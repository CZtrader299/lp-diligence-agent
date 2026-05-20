"""Deterministic sentence-aware text chunker.

Ported from filings-analyst-mcp. Splits text into overlapping windows of
roughly N tokens, preferring sentence boundaries. Token counts approximated
at 4 chars/token (standard GPT-family BPE heuristic).
"""

from __future__ import annotations

import re
from typing import Iterable

CHARS_PER_TOKEN = 4

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])[ \t]+(?=[A-Z\(])|\n\n+")


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text)
    out: list[str] = []
    for part in parts:
        if part is None:
            continue
        cleaned = part.strip()
        if cleaned:
            out.append(cleaned)
    return out


def _char_chunks(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    step = max(1, max_chars - overlap_chars)
    out: list[str] = []
    for start in range(0, len(text), step):
        chunk = text[start : start + max_chars]
        if chunk:
            out.append(chunk)
        if start + max_chars >= len(text):
            break
    return out


def chunk_text(
    text: str,
    *,
    target_tokens: int = 500,
    overlap_tokens: int = 60,
) -> list[str]:
    if not text or not text.strip():
        return []
    if target_tokens <= 0:
        raise ValueError("target_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= target_tokens:
        raise ValueError("overlap_tokens must be in [0, target_tokens)")

    max_chars = target_tokens * CHARS_PER_TOKEN
    overlap_chars = overlap_tokens * CHARS_PER_TOKEN

    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    def flush() -> str:
        return " ".join(current).strip()

    def tail_for_overlap(chunk_text_: str) -> tuple[list[str], int]:
        if overlap_chars <= 0 or not chunk_text_:
            return [], 0
        tail = chunk_text_[-overlap_chars:]
        tail_sents = _split_sentences(tail)
        if not tail_sents:
            return [tail], len(tail)
        if tail_sents and tail_sents[0] and not tail_sents[0][0].isupper():
            tail_sents = tail_sents[1:]
        if not tail_sents:
            return [], 0
        joined = " ".join(tail_sents)
        return tail_sents, len(joined)

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                emitted = flush()
                if emitted:
                    chunks.append(emitted)
                current, current_len = [], 0
            for piece in _char_chunks(sentence, max_chars, overlap_chars):
                chunks.append(piece)
            if chunks:
                seed, seed_len = tail_for_overlap(chunks[-1])
                current = list(seed)
                current_len = seed_len
            continue

        prospective_len = current_len + (1 if current else 0) + len(sentence)
        if current and prospective_len > max_chars:
            emitted = flush()
            if emitted:
                chunks.append(emitted)
            seed, seed_len = tail_for_overlap(emitted)
            current = list(seed)
            current_len = seed_len
            current.append(sentence)
            current_len += (1 if seed_len else 0) + len(sentence)
        else:
            current.append(sentence)
            current_len = prospective_len

    if current:
        emitted = flush()
        if emitted:
            chunks.append(emitted)

    return chunks


__all__: Iterable[str] = ("chunk_text", "CHARS_PER_TOKEN")
