"""Genera representaciones vectoriales de las páginas y crea una base de datos SQLite para búsquedas."""
import argparse
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite_vec
from app import retrieval as r


def embedding_text(page: dict) -> str:
    """Añade la sesión, el capítulo y el título al texto de la página para indexarlo."""
    return (f"第{page['lecture']}回 {page['document_title']}\n{page['section']}\n"
            f"{page['title']}\n{page['content']}")


def build_index(source: Path = r.RAG_SOURCE, destination: Path = r.RAG_DB,
                *, rebuild: bool = False, embedder=None) -> dict:
    """Guarda una fila por página. Para reconstruir una base existente, hay que indicar --rebuild."""
    if destination.exists() and not rebuild:
        raise FileExistsError("La base de datos de búsqueda ya existe. Indica --rebuild para reconstruirla.")
    pages = r.load_pages(source)
    if not pages:
        raise ValueError("No hay páginas de los materiales seleccionados.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".rag-build-", suffix=".sqlite3", dir=destination.parent)
    os.close(fd)
    temporary = Path(name)
    embedder = embedder or r.embed_text
    try:
        db = sqlite3.connect(temporary)
        try:
            db.execute("""CREATE TABLE chunks (
                page_id TEXT PRIMARY KEY, document_id TEXT, lecture INTEGER,
                document_title TEXT, section TEXT, title TEXT,
                page INTEGER, content TEXT, embedding BLOB, citation TEXT)""")
            for page in pages:
                print(f"[embedding] {page['page_id']}", flush=True)
                vector = embedder(embedding_text(page), "RETRIEVAL_DOCUMENT")
                values = [page[key] for key in ["page_id", "document_id", "lecture", "document_title",
                                                "section", "title", "page", "content"]]
                db.execute("INSERT INTO chunks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           values + [sqlite_vec.serialize_float32(vector), page.get("citation")])
            db.commit()
        finally:
            db.close()
        if temporary.stat().st_size > 10_000_000:
            raise ValueError("La base de datos de búsqueda supera el límite de almacenamiento de 10MB.")
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {"pages": len(pages), "model": r.EMBEDDING_MODEL, "dimensions": r.EMBEDDING_DIMENSIONS,
            "bytes": destination.stat().st_size, "database": str(destination)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=r.RAG_SOURCE)
    parser.add_argument("--db", type=Path, default=r.RAG_DB)
    parser.add_argument("--rebuild", action="store_true", help="Volver a vectorizar todas las páginas y reconstruir la base de datos")
    args = parser.parse_args()
    print(json.dumps(build_index(args.source, args.db, rebuild=args.rebuild), ensure_ascii=False, indent=2))
