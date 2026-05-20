"""FastAPI server backing the Next.js demo UI.

Routes:
  GET  /api/documents              -> list of available documents
  GET  /api/checklist/items        -> the 9-item checklist
  POST /api/checklist/run          -> run the checklist against one document
  POST /api/ask                    -> RAG Q&A over one document

Rate limited at the route level via a simple per-IP token bucket so the public
demo doesn't get drained by a script. Tune ``RATE_LIMIT_*`` in env if needed.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import config
from .checklist import CHECKLIST_ITEMS, run_checklist, answer_item, _build_client
from .documents import list_documents
from .embeddings import Embedder
from .retrieval import format_context, retrieve
from .vectorstore import VectorStore


RATE_LIMIT_WINDOW_S = int(os.environ.get("RATE_LIMIT_WINDOW_S", "3600"))
RATE_LIMIT_MAX_RUNS = int(os.environ.get("RATE_LIMIT_MAX_RUNS", "10"))

_buckets: dict[str, deque[float]] = defaultdict(deque)


def _check_rate_limit(ip: str) -> None:
    now = time.time()
    bucket = _buckets[ip]
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_S:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX_RUNS:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: {RATE_LIMIT_MAX_RUNS} runs per {RATE_LIMIT_WINDOW_S // 60} minutes. Try again later.",
        )
    bucket.append(now)


app = FastAPI(title="LP Diligence Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class ChecklistRunRequest(BaseModel):
    doc_id: str
    k: Optional[int] = None


class AskRequest(BaseModel):
    doc_id: str
    question: str
    k: Optional[int] = None


@app.get("/api/documents")
def get_documents() -> dict:
    return {"documents": list_documents()}


@app.get("/api/checklist/items")
def get_checklist_items() -> dict:
    return {"items": [{"id": i, "question": q} for i, q in CHECKLIST_ITEMS]}


@app.post("/api/checklist/run")
def post_checklist_run(req: ChecklistRunRequest, request: Request) -> dict:
    _check_rate_limit(request.client.host if request.client else "unknown")
    answers = run_checklist(req.doc_id, k=req.k or config.RETRIEVAL_K)
    return {"doc_id": req.doc_id, "answers": [asdict(a) for a in answers]}


@app.post("/api/ask")
def post_ask(req: AskRequest, request: Request) -> dict:
    _check_rate_limit(request.client.host if request.client else "unknown")
    client = _build_client()
    embedder = Embedder()
    store = VectorStore(config.VECTOR_DB_PATH, dim=embedder.dim)
    try:
        ans = answer_item(
            "adhoc",
            req.question,
            doc_id=req.doc_id,
            client=client,
            embedder=embedder,
            store=store,
            k=req.k or config.RETRIEVAL_K,
        )
    finally:
        store.close()
    return {"doc_id": req.doc_id, "answer": asdict(ans)}


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True}
