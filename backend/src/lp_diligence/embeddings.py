"""Pluggable embedding provider (local sentence-transformers or OpenAI)."""

from __future__ import annotations

import os
from typing import Optional

import httpx

from . import config


_OPENAI_BATCH_SIZE = 96

_KNOWN_DIMS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "sentence-transformers/all-MiniLM-L12-v2": 384,
    "sentence-transformers/all-mpnet-base-v2": 768,
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
}

PROVIDERS = {"local", "openai"}


class Embedder:
    def __init__(self, provider: Optional[str] = None):
        requested = (provider or config.EMBEDDING_PROVIDER or "local").strip().lower()
        if requested not in PROVIDERS:
            print(f"  Warning: unknown embedding provider {requested!r}, falling back to 'local'")
            requested = "local"
        self.provider = requested
        self._local_model = None

    def embed_texts(self, texts: list[str]) -> Optional[list[list[float]]]:
        if not texts:
            return []
        if self.provider == "local":
            return self._embed_local(texts)
        if self.provider == "openai":
            return self._embed_openai(texts)
        return None

    def embed_query(self, text: str) -> Optional[list[float]]:
        vectors = self.embed_texts([text])
        if not vectors:
            return None
        return vectors[0]

    @property
    def model_name(self) -> str:
        if self.provider == "local":
            return config.LOCAL_EMBEDDING_MODEL
        if self.provider == "openai":
            return config.OPENAI_EMBEDDING_MODEL
        return ""

    @property
    def dim(self) -> int:
        override = os.environ.get("EMBEDDER_DIM", "").strip()
        if override.isdigit():
            return int(override)
        return _KNOWN_DIMS.get(self.model_name, 384)

    def _embed_local(self, texts: list[str]) -> Optional[list[list[float]]]:
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                print('  Warning: sentence-transformers not installed. Run `pip install -e ".[embeddings]"`.')
                print(f"  Detail: {exc}")
                return None
            try:
                self._local_model = SentenceTransformer(config.LOCAL_EMBEDDING_MODEL)
            except Exception as exc:  # noqa: BLE001
                print(f"  Warning: failed to load local embedding model: {exc}")
                return None
        try:
            vectors = self._local_model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
        except Exception as exc:  # noqa: BLE001
            print(f"  Warning: local embedding failed: {exc}")
            return None
        return [list(map(float, v)) for v in vectors]

    def _embed_openai(self, texts: list[str]) -> Optional[list[list[float]]]:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("  Warning: OPENAI_API_KEY not set; cannot use openai embeddings")
            return None
        model = os.environ.get("OPENAI_EMBEDDING_MODEL", config.OPENAI_EMBEDDING_MODEL)
        out: list[list[float]] = []
        for start in range(0, len(texts), _OPENAI_BATCH_SIZE):
            batch = texts[start : start + _OPENAI_BATCH_SIZE]
            try:
                response = httpx.post(
                    "https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"model": model, "input": batch},
                    timeout=config.REQUEST_TIMEOUT,
                )
            except httpx.HTTPError as exc:
                print(f"  Warning: OpenAI embeddings request failed: {exc}")
                return None
            if response.status_code >= 400:
                print(f"  Warning: OpenAI embeddings HTTP {response.status_code}: {response.text[:200]}")
                return None
            try:
                payload = response.json()
                items = sorted(payload["data"], key=lambda d: d.get("index", 0))
                out.extend([list(map(float, item["embedding"])) for item in items])
            except (KeyError, TypeError, ValueError) as exc:
                print(f"  Warning: malformed OpenAI embeddings response: {exc}")
                return None
        return out


__all__ = ("Embedder", "PROVIDERS")
