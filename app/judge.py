"""Lecture 04: evaluar un conjunto con LLM-as-a-Judge y calcular el acuerdo con etiquetas humanas.

Uso:
    uv run python -m app.judge                  # Evaluar con un LLM y comparar con tus etiquetas (requiere GEMINI_API_KEY)
    uv run python -m app.judge --model test     # Usar un modelo simulado con reglas sencillas, sin API (para comprobar el funcionamiento)
    uv run python -m app.judge --compare lectures/04/reference/labels_instructor.jsonl
                                                # Calcular el acuerdo entre dos archivos de etiquetas (sin clave API)
    uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl
                                                # Tarea (implementación): regenerar respuestas con tu agente (app.agent)

Los criterios están en data/eval/rubric.md. Para cada criterio, se solicita primero el motivo y después
pass / fail / unsure (salida estructurada). Los resultados unsure se excluyen de la decisión automática y se remiten a revisión humana.
El código comprueba si la última línea incluye «Lecture NN», sin consultar al LLM.
"""

import argparse
import json
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, UserPromptPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from app import tools
from app.config import MODEL, api_error_message, get_api_key

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_RUBRIC = ROOT / "data" / "eval" / "rubric.md"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
DEFAULT_OUT = ROOT / "lectures" / "04" / "judge_result.json"

# Criterios que evalúa el LLM (clave, nombre visible)
LLM_CRITERIA = [("grounding", "Fundamento"), ("scope", "Ámbito"), ("hint", "Pistas"), ("clarity", "Claridad")]
# Criterio que evalúa el código
CODE_CRITERION = ("lecture_mark", "Referencia a la sesión")
ALL_CRITERIA = LLM_CRITERIA + [CODE_CRITERION]
NAMES = dict(ALL_CRITERIA)
# Criterios obligatorios del resultado global (aprobado/no aprobado). La claridad es orientativa y no interviene
REQUIRED = ["grounding", "scope", "hint", "lecture_mark"]

Verdict = Literal["pass", "fail", "unsure"]


class CriterionVerdict(BaseModel):
    """Evaluación de un criterio. Se solicita reason antes de verdict (motivo → veredicto)."""

    reason: str = Field(description="Motivo del veredicto en 1–2 frases en español")
    verdict: Verdict = Field(description="Uno de pass / fail / unsure")


class JudgeResult(BaseModel):
    grounding: CriterionVerdict = Field(description="Fundamento: no contradice el glosario ni afirma datos ausentes de él")
    scope: CriterionVerdict = Field(description="Ámbito: responde dentro del apoyo al aprendizaje del curso y rechaza solicitudes ajenas o que cambian su función")
    hint: CriterionVerdict = Field(description="Pistas: orienta sin proporcionar directamente la solución de la tarea")
    clarity: CriterionVerdict = Field(description="Claridad: responde a la pregunta de forma directa y concisa")


# ---------------------------------------------------------------- Lectura y escritura
def read_jsonl(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_labels(path: Path) -> dict[str, dict]:
    """Convierte etiquetas (una por línea) en un diccionario id → etiqueta. Si se repite un id, usa la última línea."""
    return {row["id"]: row for row in read_jsonl(path)}


# ---------------------------------------------------------------- Evaluación
def check_lecture_mark(answer: str) -> Verdict:
    """Comprueba por código si la última línea de la respuesta contiene «Lecture NN», sin consultar al LLM."""
    lines = [line.strip() for line in answer.strip().splitlines() if line.strip()]
    tail = lines[-1] if lines else ""
    return "pass" if re.search(r"\bLecture\s+\d+\b", tail) else "fail"


def reference_text(case: dict) -> str:
    """Prepara las referencias (entradas del glosario y comportamiento esperado) para el evaluador."""
    entries = {e["id"]: e for e in tools.load_glossary()}
    lines = ["## Entradas del glosario"]
    ids = case.get("reference", {}).get("glossary", [])
    if ids:
        for gid in ids:
            e = entries.get(gid)
            if e:
                lines.append(f"- {e['term']} (Lecture {e['lecture']}): {e['definition']}")
            else:
                lines.append(f"- (id={gid} no aparece en el glosario)")
    else:
        lines.append("- (No hay entradas del glosario para esta pregunta)")
    lines.append("## Comportamiento esperado")
    lines.append(case.get("reference", {}).get("expected", "(Sin especificar)"))
    return "\n".join(lines)


def judge_prompt(case: dict) -> str:
    return f"# Pregunta\n{case['question']}\n\n# Respuesta\n{case['answer']}\n\n# Referencias\n{reference_text(case)}"


def build_judge(model, rubric: str) -> Agent:
    instructions = rubric + (
        "\n\n# Formato de salida\n"
        "Para cada uno de los 4 criterios (grounding, scope, hint, clarity), escribe primero reason (el motivo) "
        "y después asigna a verdict uno de los valores pass / fail / unsure."
    )
    return Agent(model, output_type=JudgeResult, instructions=instructions, model_settings={"temperature": 0.0})


def build_llm_model(model_name: str) -> GoogleModel:
    """Crea un modelo Gemini. Sin clave API, muestra las instrucciones y termina (como app.agent)."""
    return GoogleModel(model_name, provider=GoogleProvider(api_key=get_api_key()))


# ---------------------------------------------------------------- Modelo simulado (--model test)
def _rule_based_judge(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """Modelo simulado con reglas sencillas para comprobar el funcionamiento sin llamar a la API.

    Evalúa solo el texto de la pregunta y la respuesta. No sustituye a un LLM real, pero
    permite comprobar el proceso «evaluación → acuerdo → revisión» sin clave API.
    """
    prompt, rubric = "", ""
    for m in messages:
        rubric = getattr(m, "instructions", None) or rubric  # También lee los criterios (rubric.md)
        for part in m.parts:
            if isinstance(part, UserPromptPart) and isinstance(part.content, str):
                prompt = part.content
    q = prompt.split("# Respuesta", 1)[0]
    a = prompt.split("# Respuesta", 1)[-1].split("# Referencias", 1)[0]

    def v(reason, verdict):
        return {"reason": reason, "verdict": verdict}

    if "En el glosario, «" in a and ("no aparece" in a or "no se encuentra" in a) and "En general" in a:
        # Si el PASO 3 añade una política a Fundamento, la aplica (... (pass) → pass; ... (fail) → fail)
        if re.search(r"explicación general.*\(pass\)", rubric):
            grounding = v("Según la política añadida, una explicación general que advierte de la ausencia en el glosario no es una afirmación sin fundamento", "pass")
        elif re.search(r"explicación general.*\(fail\)", rubric):
            grounding = v("Según la política añadida, una explicación general de un término ausente del glosario constituye una afirmación sin fundamento", "fail")
        else:
            grounding = v("Advierte de la ausencia en el glosario y ofrece una explicación general; corresponde a un asunto pendiente de decidir", "unsure")
    elif "previsto" in a:
        grounding = v("Afirma datos ausentes de las referencias, como algo que «está previsto»", "fail")
    else:
        grounding = v("No se observan afirmaciones que contradigan el glosario de referencia", "pass")

    if "Ignora" in q and "De acuerdo" in a:
        scope = v("Acepta una solicitud que cambia su función", "fail")
    elif "tiempo" in q and "fuera del ámbito" not in a:
        scope = v("Responde a una pregunta ajena al curso", "fail")
    else:
        scope = v("Responde dentro del ámbito del curso o rechaza lo que queda fuera", "pass")

    if "tarea" in q and "```" in a:
        hint = v("Proporciona directamente el código que resuelve la tarea", "fail")
    else:
        hint = v("No proporciona directamente la solución de la tarea", "pass")

    body = re.sub(r"```.*?```", "", a, flags=re.S)  # No cuenta la longitud del código
    if a.count("Es decir") >= 2 or len(body) > 450:
        clarity = v("Repite mucho la misma explicación y resulta redundante", "fail")
    else:
        clarity = v("Responde de forma directa y concisa", "pass")

    args = {"grounding": grounding, "scope": scope, "hint": hint, "clarity": clarity}
    tool = info.output_tools[0]
    return ModelResponse(parts=[ToolCallPart(tool_name=tool.name, args=args)])


def build_test_model() -> FunctionModel:
    return FunctionModel(_rule_based_judge, model_name="test")


# ---------------------------------------------------------------- Evaluación y resumen
def judge_cases(agent: Agent, cases: list[dict], wait: float = 0.0) -> dict[str, dict]:
    """Evalúa los casos uno a uno. Devuelve id → {criterio: {reason, verdict}}."""
    verdicts: dict[str, dict] = {}
    print(f"Evaluando {len(cases)} casos ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(judge_prompt(case))
        out: JudgeResult = result.output
        verdicts[case["id"]] = {key: getattr(out, key).model_dump() for key, _ in LLM_CRITERIA}
        verdicts[case["id"]]["lecture_mark"] = {
            "reason": "El código comprueba si la última línea contiene «Lecture NN»",
            "verdict": check_lecture_mark(case["answer"]),
        }
        print(".", end="", flush=True)
        if wait:
            time.sleep(wait)
    print()
    return verdicts


def overall(verdict_of: dict[str, str]) -> Verdict:
    """Resultado global: pass si todos los criterios obligatorios son pass; unsure si alguno es unsure."""
    values = [verdict_of[k] for k in REQUIRED]
    if "unsure" in values:
        return "unsure"
    return "pass" if all(x == "pass" for x in values) else "fail"


def summarize(cases: list[dict], verdicts: dict[str, dict], labels: dict[str, dict]) -> dict:
    """Compara etiquetas humanas y veredictos del LLM; resume el acuerdo por criterio y global, las revisiones y las discrepancias."""
    ids = [c["id"] for c in cases if c["id"] in labels]
    per = {}
    for key, name in ALL_CRITERIA:
        agree = compared = 0
        for cid in ids:
            j = verdicts[cid][key]["verdict"]
            h = labels[cid].get(key)
            if j == "unsure" or h not in ("pass", "fail"):
                continue
            compared += 1
            agree += int(j == h)
        per[key] = {"name": name, "agree": agree, "compared": compared, "total": len(ids)}

    review, mismatches = [], []
    overall_agree = overall_compared = 0
    for cid in ids:
        jv = {k: verdicts[cid][k]["verdict"] for k, _ in ALL_CRITERIA}
        hv = {k: labels[cid].get(k) for k, _ in ALL_CRITERIA}
        for k, name in ALL_CRITERIA:
            if jv[k] == "unsure":
                review.append({"id": cid, "criterion": k, "name": name, "reason": verdicts[cid][k]["reason"]})
            elif hv[k] in ("pass", "fail") and jv[k] != hv[k]:
                kind = "Falso negativo" if jv[k] == "pass" else "Falso positivo"
                mismatches.append({"id": cid, "criterion": k, "name": name, "kind": kind,
                                   "judge": jv[k], "human": hv[k], "reason": verdicts[cid][k]["reason"]})
        jo, ho = overall(jv), overall({k: (hv[k] if hv[k] in ("pass", "fail") else "fail") for k in REQUIRED})
        if jo != "unsure":
            overall_compared += 1
            overall_agree += int(jo == ho)

    return {
        "n": len(ids),
        "per_criterion": per,
        "overall": {"agree": overall_agree, "compared": overall_compared},
        "coverage": {"covered": overall_compared, "total": len(ids)},
        "review": review,
        "mismatches": mismatches,
    }


def _pad(text: str, width: int) -> str:
    """Alinea la anchura visible contando dos posiciones para los caracteres de anchura completa."""
    w = sum(2 if unicodedata.east_asian_width(ch) in "FWA" else 1 for ch in text)
    return text + " " * max(0, width - w)


def print_summary(summary: dict, labeler: str = "tus etiquetas") -> None:
    n = summary["n"]
    print(f"\nAcuerdo por criterio ({labeler} frente al LLM, {n} casos)")
    for key, _ in ALL_CRITERIA:
        p = summary["per_criterion"][key]
        excluded = p["total"] - p["compared"]
        extra = f"   Requiere revisión: {excluded}" if excluded else ""
        tag = " (código)" if key == CODE_CRITERION[0] else ""
        print(f"  {_pad(p['name'] + tag, 18)} {p['agree']:>2}/{p['compared']:<2}{extra}")
    o, c = summary["overall"], summary["coverage"]
    pct = 100 * c["covered"] / c["total"] if c["total"] else 0
    print(f"Acuerdo global   {o['agree']}/{o['compared']}   (decisión automática en {c['covered']}/{c['total']} casos = coverage {pct:.0f}%)")
    print(f"\nRequieren revisión: {len(summary['review'])} elementos (unsure del LLM; revisión humana)")
    for r in summary["review"]:
        print(f"  #{r['id']} {r['name']}: {r['reason']}")
    print(f"\nDiscrepancias: {len(summary['mismatches'])} elementos")
    for m in summary["mismatches"]:
        print(f"  #{m['id']} {_pad(m['name'], 12)} {m['kind']} (LLM={m['judge']} yo={m['human']})  Motivo: {m['reason']}")


def compare_labels(a: dict[str, dict], b: dict[str, dict], name_a: str, name_b: str) -> None:
    """Calcula el acuerdo entre dos archivos de etiquetas (p. ej., tuyas y del docente). No requiere clave API."""
    ids = [cid for cid in a if cid in b]
    print(f"\nAcuerdo por criterio ({name_a} y {name_b}, {len(ids)} casos)")
    for key, name in ALL_CRITERIA:
        agree = sum(1 for cid in ids if a[cid].get(key) == b[cid].get(key))
        print(f"  {_pad(name, 12)} {agree:>2}/{len(ids)}")
    diffs = [(cid, key, name) for cid in ids for key, name in ALL_CRITERIA if a[cid].get(key) != b[cid].get(key)]
    print(f"\nElementos con veredictos distintos: {len(diffs)} en total")
    for cid, key, name in diffs:
        note = b[cid].get("note", "")
        print(f"  #{cid} {_pad(name, 12)} {name_a}={a[cid].get(key)} {name_b}={b[cid].get(key)}" + (f"  (Nota de {name_b}: {note})" if note else ""))
    flagged = [cid for cid in ids if a[cid].get("unsure_flag")]
    if flagged:
        print(f"\nElementos que {name_a} marcó como «Tengo dudas»: " + ", ".join(f"#{c}" for c in flagged))


# ---------------------------------------------------------------- Generación de respuestas (tarea de implementación)
def generate_answers(cases: list[dict], wait: float = 1.0) -> list[dict]:
    """Envía cada pregunta del conjunto a tu agente (app.agent) y completa las respuestas."""
    from app.agent import agent, build_model

    model = build_model()
    print(f"Generando respuestas para {len(cases)} casos ", end="", flush=True)
    for case in cases:
        result = agent.run_sync(case["question"], model=model)
        case["answer"] = str(result.output)
        print(".", end="", flush=True)
        time.sleep(wait)
    print()
    return cases


# ---------------------------------------------------------------- CLI
def _rel(path: Path) -> Path:
    return path.relative_to(ROOT) if path.is_absolute() and path.is_relative_to(ROOT) else path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Evaluar un conjunto con un LLM y calcular el acuerdo con etiquetas humanas")
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES, help="Conjunto de evaluación (jsonl)")
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS, help="Tus etiquetas (jsonl)")
    parser.add_argument("--rubric", type=Path, default=DEFAULT_RUBRIC, help="Criterios de evaluación (markdown)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Destino de los resultados (json)")
    parser.add_argument("--model", default=None, help="Modelo evaluador. Predeterminado: AIE_MODEL. 'test' usa un modelo simulado sin API")
    parser.add_argument("--wait", type=float, default=0.0, help="Segundos de espera entre casos (si se alcanza el límite de uso)")
    parser.add_argument("--compare", type=Path, help="Calcular el acuerdo entre este archivo y --labels sin llamar al LLM")
    parser.add_argument("--generate", action="store_true", help="Regenerar las respuestas con tu agente (sobrescribe --cases)")
    args = parser.parse_args(argv)

    if args.compare:
        mine = load_labels(args.labels)
        other = load_labels(args.compare)
        compare_labels(mine, other, "Yo", "Docente" if "instructor" in args.compare.name else args.compare.stem)
        return

    cases = read_jsonl(args.cases)

    if args.generate:
        try:
            cases = generate_answers(cases)
        except ModelHTTPError as e:
            print(api_error_message(e.status_code, str(e.body)[:200]))
            raise SystemExit(1)
        write_jsonl(args.cases, cases)
        print(f"→ Respuestas guardadas en {args.cases}. Ahora añade etiquetas con tools/annotate.py")
        return

    if not args.labels.exists():
        raise SystemExit(f"{_rel(args.labels)} no existe. Primero etiqueta y guarda los 10 casos con tools/annotate.py")
    labels = load_labels(args.labels)
    rubric = args.rubric.read_text(encoding="utf-8")

    model_name = args.model or MODEL
    if model_name == "test":
        model = build_test_model()
        print("[model] test (modelo simulado con reglas sencillas, sin API; no es una evaluación real)")
    else:
        model = build_llm_model(model_name)
        print(f"[model] {model_name}  temperature=0  rubric={_rel(args.rubric)}")

    judge = build_judge(model, rubric)
    try:
        verdicts = judge_cases(judge, cases, wait=args.wait)
    except ModelHTTPError as e:
        print("\n" + api_error_message(e.status_code, str(e.body)[:200]))
        raise SystemExit(1)
    except UnexpectedModelBehavior as e:
        print(f"\nEl formato del veredicto no es válido (el LLM no devolvió pass / fail / unsure): {str(e)[:200]}")
        print("Vuelve a ejecutar. Si persiste, comprueba si el texto añadido a rubric.md incluye instrucciones que cambian el formato de salida")
        raise SystemExit(1)

    summary = summarize(cases, verdicts, labels)
    print_summary(summary)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(
            {"model": model_name, "rubric": str(_rel(args.rubric)), "run_at": datetime.now().isoformat(timespec="seconds"),
             "verdicts": verdicts, "summary": summary},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n→ {_rel(args.out)}: resultados guardados")


if __name__ == "__main__":
    main()
