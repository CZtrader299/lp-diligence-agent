"""Retrieval helpers: query → top-k chunks formatted for the LLM prompt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from . import config
from .embeddings import Embedder
from .vectorstore import VectorStore


@dataclass
class Citation:
    chunk_id: str
    doc_id: str
    entity: str
    period: str
    section: str
    page_start: int | None
    page_end: int | None
    excerpt: str
    score: float

    def label(self) -> str:
        """Short citation label like ``[PSERS 2Q17 Performance p.12]``."""
        page_str = ""
        if self.page_start is not None:
            if self.page_end and self.page_end != self.page_start:
                page_str = f" p.{self.page_start}-{self.page_end}"
            else:
                page_str = f" p.{self.page_start}"
        return f"[{self.entity} {self.period} {self.section}{page_str}]"


def retrieve(
    query: str,
    *,
    doc_id: Optional[str] = None,
    doc_ids: Optional[list[str]] = None,
    k: Optional[int] = None,
    embedder: Optional[Embedder] = None,
    store: Optional[VectorStore] = None,
) -> list[Citation]:
    """Vector-search the corpus and return citations.

    If ``embedder``/``store`` are not provided, a default pair is constructed
    using ``config``. Callers running many queries should pass shared instances
    to avoid model-reload cost.
    """
    embedder = embedder or Embedder()
    own_store = False
    if store is None:
        store = VectorStore(config.VECTOR_DB_PATH, dim=embedder.dim)
        own_store = True

    qvec = embedder.embed_query(query)
    if qvec is None:
        if own_store:
            store.close()
        return []

    hits = store.search(
        qvec,
        k=k or config.RETRIEVAL_K,
        filter_doc_id=doc_id,
        filter_doc_ids=doc_ids,
    )

    if own_store:
        store.close()

    citations: list[Citation] = []
    for h in hits:
        citations.append(
            Citation(
                chunk_id=h["chunk_id"],
                doc_id=h["doc_id"],
                entity=h["entity"],
                period=h["period"],
                section=h["section"],
                page_start=h.get("page_start"),
                page_end=h.get("page_end"),
                excerpt=h["text"],
                score=h["score"],
            )
        )
    return citations


def format_context(citations: list[Citation], *, max_chars: int = 12000) -> str:
    """Render citations into a prompt-ready context block.

    Each chunk is prefixed with its citation label so the LLM can echo back
    the same label when synthesizing the answer.
    """
    blocks: list[str] = []
    total = 0
    for c in citations:
        block = f"{c.label()}\n{c.excerpt.strip()}\n"
        if total + len(block) > max_chars and blocks:
            break
        blocks.append(block)
        total += len(block)
    return "\n---\n".join(blocks)


__all__ = ("Citation", "retrieve", "format_context")
