"""Lecture 05: benchmark generativo con contextos RAG previamente guardados.

Desde la raíz del repositorio:
    python benchmarks/lecture05/run_generation_benchmark.py --case memoria
    python benchmarks/lecture05/run_generation_benchmark.py --case structured_output

Guarda cada respuesta antes de ejecutar la siguiente variante. No vuelve a buscar
embeddings ni modifica el índice. No ejecuta el Agent Loop.
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from google import genai
from app.config import MODEL, get_api_key

RESULTS_DIR = ROOT / 'results'


def atomic_save(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.tmp')
    try:
        with temp.open('w', encoding='utf-8') as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def usage_to_dict(usage):
    if usage is None:
        return None
    fields = ('prompt_token_count', 'candidates_token_count',
              'total_token_count', 'thoughts_token_count',
              'cached_content_token_count')
    return {name: getattr(usage, name, None) for name in fields}


def main():
    parser = argparse.ArgumentParser(description='Comparar generación con contextos RAG guardados')
    parser.add_argument('--case', required=True, choices=('memoria', 'structured_output'))
    parser.add_argument('--force', action='store_true', help='Sobrescribir resultados existentes')
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    print(f'Caso: {args.case} | Modelo: {MODEL}', flush=True)

    for variant in ('baseline', 'neighbors'):
        destination = RESULTS_DIR / f'{args.case}_{variant}_generation.json'
        if destination.exists() and not args.force:
            print(f'[{variant}] YA GUARDADO: {destination}', flush=True)
            continue

        source = RESULTS_DIR / f'{args.case}_{variant}.json'
        if not source.is_file():
            parser.error(f'No se encuentra el contexto guardado: {source}')
        retrieval = json.loads(source.read_text(encoding='utf-8'))
        pages = retrieval['results']
        if not pages:
            parser.error(f'El contexto está vacío: {source}')

        context = '\n\n'.join(
            f"[Página {page['page_id']}]\n{page.get('content', '')}"
            for page in pages
        )
        prompt = (
            'Responde en español a la pregunta usando únicamente el material de estudio '
            'proporcionado. Explica los conceptos con claridad y cita las páginas '
            'con sus identificadores exactos entre corchetes, por ejemplo '
            '[lec03-main-p038]. Si el material no contiene información suficiente, '
            'reconoce la limitación. No inventes citas ni datos.\n\n'
            f"PREGUNTA:\n{retrieval['question']}\n\n"
            f'MATERIAL DE ESTUDIO:\n{context}'
        )
        print(f'[{variant}] Generando respuesta con {len(pages)} páginas...', flush=True)
        response = client.models.generate_content(model=MODEL, contents=prompt)
        payload = {
            'case': args.case,
            'variant': variant,
            'model': MODEL,
            'question': retrieval['question'],
            'retrieval_source': str(source.relative_to(PROJECT_ROOT)),
            'page_ids': [page['page_id'] for page in pages],
            'context_characters': len(context),
            'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'answer': response.text or '',
            'usage': usage_to_dict(getattr(response, 'usage_metadata', None)),
            'method': 'single_generate_content_with_frozen_retrieval_context',
        }
        atomic_save(destination, payload)
        usage = payload['usage'] or {}
        print(f'[{variant}] GUARDADO: {destination}', flush=True)
        print(f"[{variant}] Tokens entrada={usage.get('prompt_token_count')} "
              f"salida={usage.get('candidates_token_count')} "
              f"total={usage.get('total_token_count')}", flush=True)
        print(f"[{variant}] Respuesta:\n{payload['answer']}\n", flush=True)

    print('Caso completado. Reanudar no repite resultados existentes.', flush=True)


if __name__ == '__main__':
    main()
