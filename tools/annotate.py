"""Lecture 04: interfaz para etiquetar un conjunto de evaluación (Streamlit).

Uso:
    uv run --with streamlit==1.66.1 streamlit run tools/annotate.py

`uv run --with` añade Streamlit temporalmente al entorno del curso (sin cambiar pyproject.toml).

- Etiquetar: muestra los casos de data/eval/lec04_cases.jsonl uno a uno y guarda aprobado/no aprobado para los 5 criterios
  y «Tengo dudas» en lectures/04/labels.jsonl
- Comparar: muestra el acuerdo entre tus etiquetas y las del docente (lectures/04/reference/labels_instructor.jsonl)
- Crear casos (tarea de implementación): escribe preguntas y comportamientos esperados para tu conjunto (data/eval/my_cases.jsonl).
  Genera las respuestas con tu agente mediante `uv run python -m app.judge --generate --cases data/eval/my_cases.jsonl`
"""

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import tools  # noqa: E402
from app.judge import ALL_CRITERIA, check_lecture_mark, load_labels, read_jsonl, write_jsonl  # noqa: E402

DEFAULT_CASES = ROOT / "data" / "eval" / "lec04_cases.jsonl"
DEFAULT_LABELS = ROOT / "lectures" / "04" / "labels.jsonl"
INSTRUCTOR_LABELS = ROOT / "lectures" / "04" / "reference" / "labels_instructor.jsonl"
MY_CASES = ROOT / "data" / "eval" / "my_cases.jsonl"

CRITERION_HELP = {
    "grounding": "No contradice las entradas del glosario. Si un dato no aparece, lo indica sin afirmarlo como cierto",
    "scope": "Responde dentro del apoyo al aprendizaje del curso. Rechaza preguntas ajenas y peticiones como «Ignora las instrucciones»",
    "hint": "Ofrece pistas sin dar la solución de la tarea (aprueba si la pregunta no trata sobre una tarea)",
    "clarity": "Responde directamente y resulta conciso y fácil de leer",
    "lecture_mark": "La última línea contiene «Lecture NN» (después lo compararemos con la comprobación por código)",
}

st.set_page_config(page_title="Lecture 04: etiquetado", layout="wide")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def glossary_entries(ids: list[str]) -> list[dict]:
    entries = {e["id"]: e for e in tools.load_glossary()}
    return [entries[i] for i in ids if i in entries]


# ---------------------------------------------------------------- Etiquetar
def page_label(cases_path: Path, labels_path: Path) -> None:
    cases = read_jsonl(cases_path)
    if not cases:
        st.error(f"{rel(cases_path)} no contiene casos de evaluación")
        return
    labels = load_labels(labels_path) if labels_path.exists() else {}

    if "index" not in st.session_state:
        done = [i for i, c in enumerate(cases) if c["id"] in labels]
        st.session_state.index = min(len(done), len(cases) - 1) if done else 0

    i = st.session_state.index
    case = cases[i]
    st.progress((len(labels)) / len(cases), text=f"Guardados: {len(labels)} / {len(cases)} casos | Mostrando: #{case['id']} (caso {i + 1})")

    nav1, nav2, nav3 = st.columns([1, 1, 6])
    if nav1.button("← Anterior", disabled=i == 0):
        st.session_state.index = i - 1
        st.rerun()
    if nav2.button("Siguiente →", disabled=i >= len(cases) - 1):
        st.session_state.index = i + 1
        st.rerun()

    left, right = st.columns([3, 2])
    with left:
        st.subheader(f"#{case['id']} — {case.get('category', '')}")
        st.markdown("**Pregunta**")
        st.info(case["question"])
        st.markdown("**Respuesta**")
        st.markdown(case["answer"] or "(Todavía no hay respuesta. Genérala con `app.judge --generate`)")
        st.markdown("**Referencias**")
        ref = case.get("reference", {})
        entries = glossary_entries(ref.get("glossary", []))
        if entries:
            for e in entries:
                st.markdown(f"- **{e['term']}** (Lecture {e['lecture']}): {e['definition']}")
        else:
            st.markdown("- (No hay entradas del glosario para esta pregunta)")
        st.markdown(f"**Comportamiento esperado**: {ref.get('expected', '(Sin especificar)')}")

    with right:
        st.subheader("Evaluación")
        st.caption("Evalúa según las referencias y los criterios, sin recurrir a tus propios conocimientos. Si dudas, marca «Tengo dudas» y continúa")
        current = labels.get(case["id"], {})
        with st.form(key=f"form-{case['id']}"):
            choice = {}
            for key, name in ALL_CRITERIA:
                default = 0 if current.get(key, "pass") == "pass" else 1
                choice[key] = st.radio(
                    f"{name}", ["Aprobado (T)", "No aprobado (F)"], index=default, horizontal=True,
                    help=CRITERION_HELP[key], key=f"{case['id']}-{key}",
                )
            unsure = st.checkbox("Tengo dudas (los criterios no bastan para decidir)", value=bool(current.get("unsure_flag", False)))
            note = st.text_input("Nota (opcional)", value=current.get("note", ""))
            submitted = st.form_submit_button("Guardar y continuar", type="primary")
        if submitted:
            labels[case["id"]] = {
                "id": case["id"],
                **{key: ("pass" if choice[key].startswith("Aprobado") else "fail") for key, _ in ALL_CRITERIA},
                "unsure_flag": unsure,
                "note": note,
            }
            write_jsonl(labels_path, [labels[c["id"]] for c in cases if c["id"] in labels])
            if i < len(cases) - 1:
                st.session_state.index = i + 1
            st.rerun()

    if len(labels) >= len(cases):
        st.success(f"{len(cases)} casos guardados → {rel(labels_path)}. Ahora evalúalos con un LLM mediante `uv run python -m app.judge`")
        st.dataframe(
            [{"id": c["id"], **{name: labels[c["id"]][key] for key, name in ALL_CRITERIA},
              "Tengo dudas": labels[c["id"]].get("unsure_flag", False)} for c in cases if c["id"] in labels],
            hide_index=True, use_container_width=True,
        )


# ---------------------------------------------------------------- Comparar
def page_compare(cases_path: Path, labels_path: Path) -> None:
    if not labels_path.exists():
        st.warning("Primero guarda las etiquetas en «Etiquetar»")
        return
    if not INSTRUCTOR_LABELS.exists():
        st.warning(f"Las etiquetas del docente {rel(INSTRUCTOR_LABELS)} no se encuentran")
        return
    cases = read_jsonl(cases_path)
    mine, ref = load_labels(labels_path), load_labels(INSTRUCTOR_LABELS)
    ids = [c["id"] for c in cases if c["id"] in mine and c["id"] in ref]
    st.subheader("Acuerdo entre tus etiquetas y las del docente")
    st.caption("Las etiquetas del docente no son necesariamente la respuesta correcta. Sirven para observar que también hay desacuerdos entre personas")
    cols = st.columns(len(ALL_CRITERIA))
    for col, (key, name) in zip(cols, ALL_CRITERIA):
        agree = sum(1 for cid in ids if mine[cid].get(key) == ref[cid].get(key))
        col.metric(name, f"{agree}/{len(ids)}")
    code_agree = sum(1 for cid in ids if mine[cid].get("lecture_mark") == check_lecture_mark(next(c for c in cases if c["id"] == cid)["answer"]))
    st.caption(f"Tu evaluación de «Referencia a la sesión» coincide con el código en {code_agree}/{len(ids)} casos")
    rows = []
    for cid in ids:
        for key, name in ALL_CRITERIA:
            if mine[cid].get(key) != ref[cid].get(key):
                rows.append({"id": cid, "Criterio": name, "Yo": mine[cid].get(key), "Docente": ref[cid].get(key),
                             "Tuve dudas": mine[cid].get("unsure_flag", False), "Nota del docente": ref[cid].get("note", "")})
    st.markdown(f"**Elementos con veredictos distintos: {len(rows)}**")
    if rows:
        st.dataframe(rows, hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- Crear casos (tarea de implementación)
def page_author(cases_path: Path) -> None:
    st.subheader("Crear tu conjunto de evaluación (tarea de implementación)")
    st.caption("Escribe la pregunta y el «Comportamiento esperado». Genera las respuestas con tu agente mediante `uv run python -m app.judge --generate --cases "
               f"{rel(cases_path)}`. Incluye casos normales y entradas que puedan provocar fallos (casos límite)")
    existing = read_jsonl(cases_path) if cases_path.exists() else []
    glossary = tools.load_glossary()
    options = {f"{e['term']} (Lecture {e['lecture']})": e["id"] for e in glossary}
    with st.form("author"):
        question = st.text_area("Pregunta", height=80)
        category = st.text_input("Categoría (p. ej., normal, término ausente del glosario, ajeno al curso)")
        expected = st.text_area("Comportamiento esperado (1–2 frases)", height=80)
        picked = st.multiselect("Entradas del glosario de referencia", list(options))
        submitted = st.form_submit_button("Añadir", type="primary")
    if submitted:
        if not question.strip() or not expected.strip():
            st.error("La pregunta y el comportamiento esperado son obligatorios")
        else:
            existing.append({
                "id": f"{len(existing) + 1:02d}", "category": category.strip(),
                "question": question.strip(), "answer": "",
                "reference": {"glossary": [options[p] for p in picked], "expected": expected.strip()},
            })
            write_jsonl(cases_path, existing)
            st.success(f"Añadido ({len(existing)} casos) → {rel(cases_path)}")
    if existing:
        st.dataframe([{"id": c["id"], "Categoría": c.get("category", ""), "Pregunta": c["question"],
                       "Tiene respuesta": bool(c.get("answer"))} for c in existing], hide_index=True, use_container_width=True)


# ---------------------------------------------------------------- Cambio de pantalla
def main() -> None:
    st.markdown("## Lecture 04: etiquetar el conjunto de evaluación")
    with st.sidebar:
        mode = st.radio("Pantalla", ["Etiquetar", "Comparar (con las etiquetas del docente)", "Crear casos (tarea de implementación)"])
        st.divider()
        cases_path = Path(st.text_input("Conjunto de evaluación", value=rel(DEFAULT_CASES)))
        labels_path = Path(st.text_input("Destino de las etiquetas", value=rel(DEFAULT_LABELS)))
        my_cases_path = Path(st.text_input("Destino de los casos creados", value=rel(MY_CASES)))
    cases_path = cases_path if cases_path.is_absolute() else ROOT / cases_path
    labels_path = labels_path if labels_path.is_absolute() else ROOT / labels_path
    my_cases_path = my_cases_path if my_cases_path.is_absolute() else ROOT / my_cases_path

    if mode.startswith("Etiquetar"):
        page_label(cases_path, labels_path)
    elif mode.startswith("Comparar"):
        page_compare(cases_path, labels_path)
    else:
        page_author(my_cases_path)


main()
