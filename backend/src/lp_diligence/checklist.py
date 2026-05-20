"""The 9-item diligence checklist + the agent that fills it in.

Each checklist item is a (name, question) pair. The agent runs one retrieval
+ one LLM call per item and emits a structured ChecklistAnswer with a
confidence tag. The LLM is instructed to return "data not available" when the
retrieved context doesn't support a citation-backed answer.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Optional

import anthropic

from . import config
from .embeddings import Embedder
from .retrieval import Citation, format_context, retrieve
from .vectorstore import VectorStore


CHECKLIST_ITEMS: list[tuple[str, str]] = [
    (
        "nav_change_drivers",
        "What was the net asset value (NAV) at period end, the change from the prior period, and the primary drivers of that change (mark-to-market changes, realizations, contributions, distributions)?",
    ),
    (
        "capital_called",
        "How much capital was called during this period? What is the cumulative called capital relative to committed capital across the portfolio?",
    ),
    (
        "distributions",
        "What distributions were received during this period? What is the DPI (distributions to paid-in capital) ratio and how has it trended?",
    ),
    (
        "irr_tvpi_dpi",
        "What are the portfolio-level or fund-level IRR, TVPI, and DPI figures reported in this filing? How do they compare to prior periods if disclosed?",
    ),
    (
        "top_holdings_movement",
        "Which underlying holdings or fund managers had the largest valuation changes (positive or negative) during this period? List specific names and dollar amounts where disclosed.",
    ),
    (
        "unfunded_commitment",
        "What is the remaining unfunded commitment? How much committed capital remains undrawn across the portfolio?",
    ),
    (
        "fee_anomalies",
        "What management fees, incentive fees, organizational expenses, or other expenses are disclosed? Are there any unusual fee items or changes in fee terms?",
    ),
    (
        "key_person_events",
        "Are any key-person events, GP-level personnel changes, leadership departures, or organizational changes flagged in this filing?",
    ),
    (
        "valuation_methodology",
        "What valuation policy or methodology is described? Are there any changes from prior periods? What share of holdings is Level 1 vs Level 2 vs Level 3 in the fair value hierarchy if disclosed?",
    ),
]


SYSTEM_PROMPT = """You are a private-markets diligence analyst working for a sophisticated LP. \
You answer specific diligence questions about a private equity fund quarterly report using ONLY \
the excerpts provided in the user message. You always cite your sources using the bracketed \
labels exactly as they appear in the context (e.g. [PSERS 2Q17 Performance p.12]).

Rules:
1. If the excerpts do not contain enough information to answer the question with a specific \
figure or fact, respond exactly with: "Data not available in the provided excerpts." Do not \
guess, infer, or fall back to general knowledge.
2. Every numeric claim must be followed by an inline citation label.
3. Be concise: 2-5 sentences total. No preamble.
4. Return your response as JSON with exactly these fields:
   - "answer": string (the actual answer text with inline citations)
   - "confidence": "high" | "medium" | "refused"
     - "high" = answer is fully supported by explicit figures in the excerpts
     - "medium" = answer is supported but partial / requires inference from disclosed items
     - "refused" = data not available
   - "citations_used": array of citation labels you actually cited

Output ONLY the JSON object. No surrounding prose, no markdown fences."""


USER_TEMPLATE = """Question: {question}

Context excerpts (one per citation label):
{context}

Answer the question using only the context above. Return the JSON object as specified."""


@dataclass
class ChecklistAnswer:
    item_id: str
    question: str
    answer: str
    confidence: str  # "high" | "medium" | "refused"
    citations_used: list[str] = field(default_factory=list)
    citations: list[dict] = field(default_factory=list)  # full Citation dicts for the retrieved chunks
    latency_ms: int = 0
    tokens_in: int = 0
    tokens_out: int = 0


def _build_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY") or config.ANTHROPIC_API_KEY
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    return anthropic.Anthropic(api_key=api_key)


def _parse_response(raw: str) -> tuple[str, str, list[str]]:
    """Extract (answer, confidence, citations_used) from the model JSON.

    Tolerates accidental code fences or surrounding whitespace.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fall back to a refused answer rather than crashing.
        return ("Data not available in the provided excerpts.", "refused", [])
    answer = str(data.get("answer", "")).strip()
    confidence = str(data.get("confidence", "medium")).strip().lower()
    if confidence not in {"high", "medium", "refused"}:
        confidence = "medium"
    citations_used = data.get("citations_used") or []
    if not isinstance(citations_used, list):
        citations_used = []
    citations_used = [str(c) for c in citations_used]
    if not answer:
        return ("Data not available in the provided excerpts.", "refused", [])
    return (answer, confidence, citations_used)


def answer_item(
    item_id: str,
    question: str,
    *,
    doc_id: str,
    client: anthropic.Anthropic,
    embedder: Embedder,
    store: VectorStore,
    k: int = 8,
) -> ChecklistAnswer:
    """Run one checklist item end-to-end: retrieve → prompt → parse."""
    citations = retrieve(question, doc_id=doc_id, k=k, embedder=embedder, store=store)

    if not citations:
        return ChecklistAnswer(
            item_id=item_id,
            question=question,
            answer="Data not available in the provided excerpts.",
            confidence="refused",
            citations=[],
        )

    context = format_context(citations)
    user_msg = USER_TEMPLATE.format(question=question, context=context)

    t0 = time.time()
    response = client.messages.create(
        model=config.MODEL,
        max_tokens=600,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_msg}],
    )
    latency_ms = int((time.time() - t0) * 1000)

    raw = "".join(block.text for block in response.content if block.type == "text")
    answer, confidence, citations_used = _parse_response(raw)

    return ChecklistAnswer(
        item_id=item_id,
        question=question,
        answer=answer,
        confidence=confidence,
        citations_used=citations_used,
        citations=[asdict(c) for c in citations],
        latency_ms=latency_ms,
        tokens_in=getattr(response.usage, "input_tokens", 0),
        tokens_out=getattr(response.usage, "output_tokens", 0),
    )


def run_checklist(
    doc_id: str,
    *,
    items: Optional[list[tuple[str, str]]] = None,
    k: int = 8,
) -> list[ChecklistAnswer]:
    """Run the full 9-item checklist against one document."""
    items = items or CHECKLIST_ITEMS
    client = _build_client()
    embedder = Embedder()
    store = VectorStore(config.VECTOR_DB_PATH, dim=embedder.dim)
    out: list[ChecklistAnswer] = []
    try:
        for item_id, question in items:
            out.append(
                answer_item(
                    item_id, question, doc_id=doc_id, client=client, embedder=embedder, store=store, k=k
                )
            )
    finally:
        store.close()
    return out


__all__ = ("CHECKLIST_ITEMS", "ChecklistAnswer", "answer_item", "run_checklist")
