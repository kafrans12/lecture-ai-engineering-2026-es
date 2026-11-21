"""Lecture 05: benchmark incremental de recuperación vectorial.

Ejecutar desde la raíz del repositorio:
    python benchmarks/lecture05/run_benchmark.py --case 1

Cada variante se guarda inmediatamente en results/<slug>_<variant>.json.
Las páginas candidatas NO constituyen ground truth validado.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.retrieval import search

ROOT = Path(__file__).resolve().parent
CASES_FILE = ROOT / "cases.json"
RESULTS_DIR = ROOT / "results"


def save_json_atomic(path: Path, data: dict) -> None:
    """Escribe a un archivo temporal y reemplaza el destino al terminar."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    try:
        with temp.open("w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark incremental de Neighbor Expansion")
    parser.add_argument("--case", type=int, required=True, help="ID de caso (1 a 6)")
    parser.add_argument("--force", action="store_true", help="Repetir y sobrescribir resultados guardados")
    args = parser.parse_args()

    data = json.loads(CASES_FILE.read_text(encoding="utf-8"))
    case = next((item for item in data["cases"] if item["id"] == args.case), None)
    if case is None:
        parser.error(f"No existe el caso {args.case}")

    print(f"Caso {case['id']}: {case['slug']}")
    print(f"Pregunta: {case['question']}")

    for variant, expand in (("baseline", False), ("neighbors", True)):
        destination = RESULTS_DIR / f"{case['slug']}_{variant}.json"
        if destination.exists() and not args.force:
            print(f"[{variant}] YA GUARDADO: {destination}")
            continue

        print(f"[{variant}] Consultando embeddings y recuperando páginas...", flush=True)
        pages = search(case["question"], expand_neighbors=expand)
        ids = [page["page_id"] for page in pages]
        candidates = set(case["candidate_page_ids"])
        found = sorted(candidates.intersection(ids))
        payload = {
            "case_id": case["id"],
            "slug": case["slug"],
            "question": case["question"],
            "variant": variant,
            "expand_neighbors": expand,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "reference_status": "candidate_unverified_relevance",
            "candidate_page_ids": case["candidate_page_ids"],
            "candidate_pages_found": found,
            "candidate_coverage": len(found) / len(candidates) if candidates else None,
            "total_pages": len(pages),
            "unique_pages": len(set(ids)),
            "context_characters": sum(len(str(page.get("content", ""))) for page in pages),
            "page_ids": ids,
            "results": pages,
        }
        save_json_atomic(destination, payload)
        print(
            f"[{variant}] GUARDADO: {destination} | "
            f"páginas={len(pages)} | candidatas={len(found)}/{len(candidates)} | "
            f"caracteres={payload['context_characters']}",
            flush=True,
        )

    print("Caso terminado. Los archivos guardados se pueden reutilizar sin repetir consultas.")


if __name__ == "__main__":
    main()
