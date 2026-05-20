"""Ingest pipeline: load documents, chunk, embed, store."""

from __future__ import annotations

from pathlib import Path

from . import config
from .chunking import chunk_text
from .documents import Document, list_documents, load_document
from .embeddings import Embedder
from .vectorstore import VectorStore


def ingest_document(doc: Document, embedder: Embedder, store: VectorStore) -> int:
    """Chunk + embed + insert. Returns the number of chunks stored."""
    records: list[dict] = []
    for section in doc.sections:
        if not section.text.strip():
            continue
        pieces = chunk_text(
            section.text,
            target_tokens=config.TARGET_TOKENS,
            overlap_tokens=config.OVERLAP_TOKENS,
        )
        for idx, text in enumerate(pieces):
            records.append(
                {
                    "doc_id": doc.doc_id,
                    "entity": doc.entity,
                    "period": doc.period,
                    "section": section.name,
                    "chunk_idx": idx,
                    "page_start": section.page_start,
                    "page_end": section.page_end,
                    "text": text,
                }
            )

    if not records:
        return 0

    texts = [r["text"] for r in records]
    vectors = embedder.embed_texts(texts)
    if vectors is None or len(vectors) != len(records):
        raise RuntimeError("Embedding failed or returned wrong count")

    for rec, vec in zip(records, vectors):
        rec["embedding"] = vec

    return store.add_chunks(records)


def ingest_all(corpus_dir: Path | None = None) -> dict:
    """Ingest every registered document. Returns a summary dict."""
    corpus_dir = corpus_dir or config.CORPUS_DIR
    config.ensure_cache_dir()
    embedder = Embedder()
    store = VectorStore(config.VECTOR_DB_PATH, dim=embedder.dim)
    results: dict[str, int] = {}
    for meta in list_documents():
        doc_id = meta["doc_id"]
        try:
            doc = load_document(doc_id, corpus_dir)
            n = ingest_document(doc, embedder, store)
            results[doc_id] = n
            print(f"  Ingested {doc_id}: {n} chunks")
        except Exception as exc:
            print(f"  Failed to ingest {doc_id}: {exc}")
            results[doc_id] = -1
    store.close()
    return {"chunks_total": store.count() if False else sum(v for v in results.values() if v > 0), "per_doc": results}


__all__ = ("ingest_document", "ingest_all")
