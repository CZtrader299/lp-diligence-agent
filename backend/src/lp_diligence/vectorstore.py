"""Sqlite-vec wrapper for chunk storage and similarity search.

Schema:
    chunk_meta(chunk_id PK, doc_id, entity, period, section, chunk_idx,
               page_start, page_end, text)
    chunk_vec(chunk_id PK, embedding FLOAT[<dim>])  -- vec0 virtual table

chunk_id is "{doc_id}:{section}:{chunk_idx}" so re-ingest is idempotent.
"""

from __future__ import annotations

import sqlite3
import struct
from pathlib import Path
from typing import Any, Optional


def _check_sqlite_vec_importable() -> None:
    try:
        import sqlite_vec  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            'sqlite-vec is required. Install with `pip install -e ".[embeddings]"`.'
        ) from exc


def _vec_to_blob(vec: list[float]) -> bytes:
    return struct.pack(f"<{len(vec)}f", *vec)


class VectorStore:
    def __init__(self, db_path: str | Path, dim: int):
        if dim <= 0:
            raise ValueError(f"dim must be positive, got {dim}")
        _check_sqlite_vec_importable()
        import sqlite_vec

        self.db_path = str(db_path)
        self.dim = dim

        path = Path(self.db_path)
        if path.name != ":memory:" and not path.parent.exists():
            path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS chunk_meta (
                chunk_id    TEXT PRIMARY KEY,
                doc_id      TEXT NOT NULL,
                entity      TEXT NOT NULL,
                period      TEXT NOT NULL,
                section     TEXT NOT NULL,
                chunk_idx   INTEGER NOT NULL,
                page_start  INTEGER,
                page_end    INTEGER,
                text        TEXT NOT NULL
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_meta_doc ON chunk_meta(doc_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_chunk_meta_entity ON chunk_meta(entity)")
        cur.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS chunk_vec USING vec0(
                chunk_id TEXT PRIMARY KEY,
                embedding FLOAT[{self.dim}]
            )
            """
        )
        self.conn.commit()

    def add_chunks(self, records: list[dict[str, Any]]) -> int:
        if not records:
            return 0
        cur = self.conn.cursor()
        inserted = 0
        for rec in records:
            chunk_id = f"{rec['doc_id']}:{rec['section']}:{rec['chunk_idx']}"
            embedding = rec["embedding"]
            if len(embedding) != self.dim:
                raise ValueError(
                    f"Embedding dim {len(embedding)} != store dim {self.dim} (chunk_id={chunk_id})"
                )
            cur.execute("DELETE FROM chunk_meta WHERE chunk_id = ?", (chunk_id,))
            cur.execute("DELETE FROM chunk_vec WHERE chunk_id = ?", (chunk_id,))
            cur.execute(
                "INSERT INTO chunk_meta(chunk_id, doc_id, entity, period, section, "
                "chunk_idx, page_start, page_end, text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    chunk_id,
                    rec["doc_id"],
                    rec["entity"],
                    rec["period"],
                    rec["section"],
                    int(rec["chunk_idx"]),
                    rec.get("page_start"),
                    rec.get("page_end"),
                    rec["text"],
                ),
            )
            cur.execute(
                "INSERT INTO chunk_vec(chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, _vec_to_blob(embedding)),
            )
            inserted += 1
        self.conn.commit()
        return inserted

    def delete_doc(self, doc_id: str) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT chunk_id FROM chunk_meta WHERE doc_id = ?", (doc_id,))
        ids = [row[0] for row in cur.fetchall()]
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        cur.execute(f"DELETE FROM chunk_meta WHERE chunk_id IN ({placeholders})", ids)
        cur.execute(f"DELETE FROM chunk_vec WHERE chunk_id IN ({placeholders})", ids)
        self.conn.commit()
        return len(ids)

    def count(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM chunk_meta")
        return int(cur.fetchone()[0])

    def search(
        self,
        query_embedding: list[float],
        k: int = 8,
        filter_doc_id: Optional[str] = None,
        filter_doc_ids: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        if len(query_embedding) != self.dim:
            raise ValueError(f"Query embedding dim {len(query_embedding)} != store dim {self.dim}")
        cur = self.conn.cursor()
        blob = _vec_to_blob(query_embedding)

        doc_set: Optional[set[str]] = None
        if filter_doc_ids:
            doc_set = {d for d in filter_doc_ids if d} or None

        any_filter = bool(filter_doc_id or doc_set)
        if any_filter:
            over_k = max(k * 8, 64)
            cur.execute(
                "SELECT v.chunk_id, v.distance FROM chunk_vec v "
                "WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance",
                (blob, over_k),
            )
            raw_hits = cur.fetchall()
            filtered: list[tuple[str, float]] = []
            for chunk_id, distance in raw_hits:
                cur.execute("SELECT doc_id FROM chunk_meta WHERE chunk_id = ?", (chunk_id,))
                row = cur.fetchone()
                if not row:
                    continue
                doc_id = row[0]
                if filter_doc_id and doc_id != filter_doc_id:
                    continue
                if doc_set is not None and doc_id not in doc_set:
                    continue
                filtered.append((chunk_id, distance))
                if len(filtered) >= k:
                    break
            hits = filtered
        else:
            cur.execute(
                "SELECT v.chunk_id, v.distance FROM chunk_vec v "
                "WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance",
                (blob, k),
            )
            hits = cur.fetchall()

        out: list[dict[str, Any]] = []
        for chunk_id, distance in hits:
            cur.execute(
                "SELECT doc_id, entity, period, section, chunk_idx, page_start, "
                "page_end, text FROM chunk_meta WHERE chunk_id = ?",
                (chunk_id,),
            )
            row = cur.fetchone()
            if not row:
                continue
            out.append(
                {
                    "chunk_id": chunk_id,
                    "doc_id": row[0],
                    "entity": row[1],
                    "period": row[2],
                    "section": row[3],
                    "chunk_idx": int(row[4]),
                    "page_start": row[5],
                    "page_end": row[6],
                    "text": row[7],
                    "score": float(distance),
                }
            )
        return out

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:  # pragma: no cover
            pass

    def __enter__(self) -> "VectorStore":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()


__all__ = ("VectorStore",)
