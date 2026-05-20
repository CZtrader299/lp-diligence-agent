"""Env-driven constants for the LP Diligence Agent."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Resolve repo root: this file lives at <repo>/backend/src/lp_diligence/config.py,
# so parents[4] = <repo>. Sanity-check by looking for a known sibling and walking
# up if needed so behavior survives editable installs from odd cwds.
def _find_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "data" / "corpus").exists():
            return parent
    return here.parents[4] if len(here.parents) > 4 else here.parents[-1]


_REPO_ROOT = _find_repo_root()
load_dotenv(_REPO_ROOT / ".env", override=False)

ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

MODEL: str = os.environ.get("LP_DILIGENCE_MODEL", "claude-sonnet-4-6")
JUDGE_MODEL: str = os.environ.get("LP_DILIGENCE_JUDGE_MODEL", "claude-haiku-4-5-20251001")

EMBEDDING_PROVIDER: str = os.environ.get("LP_DILIGENCE_EMBEDDING_PROVIDER", "local")
LOCAL_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

CACHE_DIR: Path = Path(os.environ.get("LP_DILIGENCE_CACHE_DIR") or (_REPO_ROOT / "data" / "cache"))
CORPUS_DIR: Path = _REPO_ROOT / "data" / "corpus"
VECTOR_DB_PATH: Path = CACHE_DIR / "vectors.sqlite"

REQUEST_TIMEOUT: int = 60

# Chunking
TARGET_TOKENS: int = 500
OVERLAP_TOKENS: int = 60
RETRIEVAL_K: int = 8


def ensure_cache_dir() -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
