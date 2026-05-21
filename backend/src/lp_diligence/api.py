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

import logging
import os
import time
import traceback
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import config
from .checklist import CHECKLIST_ITEMS, run_checklist, answer_item, _build_client
from .documents import list_documents
from .embeddings import Embedder
from .retrieval import format_context, retrieve
from .vectorstore import VectorStore

logger = logging.getLogger("lp_diligence.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


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


# Shared resources, populated at startup so first-request latency doesn't
# include the ~3-5 second sentence-transformers model load. Without this, the
# first checklist call can exceed proxy timeouts in dev.
_embedder: Optional[Embedder] = None
_anthropic_client = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _embedder, _anthropic_client
    logger.info("Pre-warming embedder...")
    t0 = time.time()
    _embedder = Embedder()
    _embedder.embed_query("warmup")
    logger.info("Embedder ready in %.1fs", time.time() - t0)
    _anthropic_client = _build_client()
    logger.info("Anthropic client ready")
    yield


def get_embedder() -> Embedder:
    if _embedder is None:
        raise RuntimeError("Embedder not initialized")
    return _embedder


def get_client():
    if _anthropic_client is None:
        raise RuntimeError("Anthropic client not initialized")
    return _anthropic_client


app = FastAPI(title="LP Diligence Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})


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
    embedder = get_embedder()
    client = get_client()
    store = VectorStore(config.VECTOR_DB_PATH, dim=embedder.dim)
    answers = []
    try:
        for item_id, question in CHECKLIST_ITEMS:
            answers.append(
                answer_item(
                    item_id,
                    question,
                    doc_id=req.doc_id,
                    client=client,
                    embedder=embedder,
                    store=store,
                    k=req.k or config.RETRIEVAL_K,
                )
            )
    finally:
        store.close()
    return {"doc_id": req.doc_id, "answers": [asdict(a) for a in answers]}


@app.post("/api/ask")
def post_ask(req: AskRequest, request: Request) -> dict:
    _check_rate_limit(request.client.host if request.client else "unknown")
    embedder = get_embedder()
    client = get_client()
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
