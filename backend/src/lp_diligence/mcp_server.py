"""MCP server exposing the LP diligence tools.

Tools:
  list_documents     -> list available LP reports
  checklist_items    -> show the 9-item diligence checklist
  run_checklist      -> run the full checklist against one document
  ask_document       -> ad-hoc RAG Q&A over one document

Usable from Claude Desktop by adding to ``claude_desktop_config.json``:

    "lp-diligence": {
        "command": "python",
        "args": ["-m", "lp_diligence.mcp_server"],
        "env": { "ANTHROPIC_API_KEY": "..." }
    }
"""

from __future__ import annotations

import json
from dataclasses import asdict

from mcp.server.fastmcp import FastMCP

from . import config
from .checklist import CHECKLIST_ITEMS, answer_item, run_checklist, _build_client
from .documents import list_documents as _list_documents
from .embeddings import Embedder
from .vectorstore import VectorStore


mcp = FastMCP("lp-diligence")


@mcp.tool()
def list_documents() -> str:
    """List the available LP-format diligence documents in the corpus."""
    return json.dumps(_list_documents(), indent=2)


@mcp.tool()
def checklist_items() -> str:
    """Return the 9 diligence checklist items as JSON."""
    return json.dumps([{"id": i, "question": q} for i, q in CHECKLIST_ITEMS], indent=2)


@mcp.tool()
def run_diligence_checklist(doc_id: str, k: int = 8) -> str:
    """Run the full 9-item diligence checklist against one document.

    Args:
      doc_id: e.g. "PSERS_HL_2Q17" or "Blackstone_PES_Q1_2025"
      k: number of chunks to retrieve per item
    """
    answers = run_checklist(doc_id, k=k)
    return json.dumps([asdict(a) for a in answers], indent=2)


@mcp.tool()
def ask_document(doc_id: str, question: str, k: int = 8) -> str:
    """Ask a single diligence question of one document, with citations."""
    client = _build_client()
    embedder = Embedder()
    store = VectorStore(config.VECTOR_DB_PATH, dim=embedder.dim)
    try:
        ans = answer_item("adhoc", question, doc_id=doc_id, client=client, embedder=embedder, store=store, k=k)
    finally:
        store.close()
    return json.dumps(asdict(ans), indent=2)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
