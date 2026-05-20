"""Document loading + section extraction for LP-format reports and 10-Qs.

Two document families are supported:

* ``psers_quarterly`` — PSERS Hamilton Lane quarterly reports (PDF, redacted).
  Sectioning is heuristic: page-based, with a heading detector that recognizes
  the common HL report TOC labels (Executive Summary, Performance, Portfolio
  Activity, Commitments, Cash Flows, Manager Detail).
* ``sec_10q`` — SEC Form 10-Q (HTML). Uses the standard 10-Q item structure
  (Item 1 Financial Statements, Item 2 MD&A, Item 3 Quant/Qual Disclosures,
  Item 4 Controls).

For the v1 we keep this intentionally simple: each document is loaded into a
list of ``(section_name, text)`` pairs with a ``page_hint`` field so citations
can point back to a page or item. Real-world LP reports have wildly varying
structures; the agent gracefully degrades to whole-document chunking when the
heading detector misses.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup
from pypdf import PdfReader


@dataclass
class Section:
    name: str
    text: str
    page_start: int | None = None  # 1-indexed page number for PDFs
    page_end: int | None = None


@dataclass
class Document:
    doc_id: str           # stable ID, e.g. "PSERS_HL_2Q17"
    entity: str           # e.g. "PSERS" or "Blackstone PES"
    period: str           # e.g. "2Q17" or "Q1 2025"
    doc_type: str         # "psers_quarterly" | "sec_10q"
    source_path: str
    sections: list[Section]

    @property
    def full_text(self) -> str:
        return "\n\n".join(s.text for s in self.sections if s.text)


# --- PSERS quarterly report (PDF) ------------------------------------------------

# Common headings we expect in HL/PSERS quarterly reports. Order matters only
# for tie-breaking when two headings appear on the same page.
_PSERS_HEADINGS = [
    "Executive Summary",
    "Portfolio Performance",
    "Performance Summary",
    "Portfolio Activity",
    "Commitments",
    "Cash Flows",
    "Capital Calls and Distributions",
    "Strategic Plan",
    "Manager Detail",
    "Manager Profiles",
    "Investment Pacing",
    "Market Overview",
    "Appendix",
]

_PSERS_HEADING_RE = re.compile(
    r"^(?P<heading>(" + "|".join(re.escape(h) for h in _PSERS_HEADINGS) + r"))\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _load_psers_pdf(path: Path) -> list[Section]:
    """Extract text from a PSERS-style PDF, splitting on detected headings.

    Falls back to one section per page if no headings match.
    """
    reader = PdfReader(str(path))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:  # pragma: no cover - pypdf occasionally fails on odd pages
            pages.append("")

    # Find heading occurrences with their page numbers.
    occurrences: list[tuple[int, str]] = []
    for page_idx, text in enumerate(pages, start=1):
        for match in _PSERS_HEADING_RE.finditer(text):
            occurrences.append((page_idx, match.group("heading").strip().title()))

    if not occurrences:
        # No headings detected — emit one section per page so we still chunk
        # cleanly. Section name uses the page number.
        return [
            Section(name=f"Page {i}", text=t, page_start=i, page_end=i)
            for i, t in enumerate(pages, start=1)
            if t.strip()
        ]

    sections: list[Section] = []
    # Pre-text before the first heading goes into a "Cover" section if non-empty.
    first_page = occurrences[0][0]
    cover = "\n\n".join(pages[: first_page - 1]).strip()
    if cover:
        sections.append(Section(name="Cover", text=cover, page_start=1, page_end=first_page - 1))

    # Build sections page-range from each heading occurrence to the next.
    for i, (page_start, heading) in enumerate(occurrences):
        page_end = occurrences[i + 1][0] - 1 if i + 1 < len(occurrences) else len(pages)
        page_end = max(page_end, page_start)
        text = "\n\n".join(pages[page_start - 1 : page_end]).strip()
        if text:
            sections.append(
                Section(name=heading, text=text, page_start=page_start, page_end=page_end)
            )
    return sections


# --- SEC 10-Q (HTML) -------------------------------------------------------------

_TENQ_SECTIONS = [
    ("Item 1", "Financial Statements"),
    ("Item 2", "MD&A"),
    ("Item 3", "Quantitative and Qualitative Disclosures"),
    ("Item 4", "Controls and Procedures"),
]


def _load_sec_10q_html(path: Path) -> list[Section]:
    """Parse a 10-Q HTML filing into Item-keyed sections.

    We use BeautifulSoup to flatten to text first, then regex-split on Item N
    headings. 10-Q headings are surprisingly consistent across filers, so a
    permissive regex (``Item\\s+\\d+[.\\s]``) handles most cases.
    """
    raw = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(raw, "lxml")
    # Drop script/style/nav noise.
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)

    # Split into Item N regions using a permissive heading detector.
    item_re = re.compile(r"^(?:PART\s+[IVX]+\s*)?Item\s+(\d+)[.\s]", re.IGNORECASE | re.MULTILINE)
    matches = list(item_re.finditer(text))
    if not matches:
        return [Section(name="Document", text=text)]

    sections: list[Section] = []
    # Anything before the first Item is "Cover".
    if matches[0].start() > 0:
        cover = text[: matches[0].start()].strip()
        if cover:
            sections.append(Section(name="Cover", text=cover))

    for i, m in enumerate(matches):
        item_num = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        label = next((lbl for n, lbl in _TENQ_SECTIONS if n == f"Item {item_num}"), f"Item {item_num}")
        sections.append(Section(name=f"Item {item_num} — {label}", text=body))
    return sections


# --- Public API ------------------------------------------------------------------

_DOC_REGISTRY = {
    "PSERS_HL_2Q17": {
        "entity": "PSERS",
        "period": "2Q17",
        "doc_type": "psers_quarterly",
        "filename": "PSERS_HL_2Q17.pdf",
    },
    "PSERS_HL_3Q17": {
        "entity": "PSERS",
        "period": "3Q17",
        "doc_type": "psers_quarterly",
        "filename": "PSERS_HL_3Q17.pdf",
    },
    "PSERS_HL_4Q17": {
        "entity": "PSERS",
        "period": "4Q17",
        "doc_type": "psers_quarterly",
        "filename": "PSERS_HL_4Q17.pdf",
    },
    "Blackstone_PES_Q1_2025": {
        "entity": "Blackstone PES",
        "period": "Q1 2025",
        "doc_type": "sec_10q",
        "filename": "Blackstone_PES_10Q_Q1_2025.htm",
    },
    "Blackstone_PES_Q3_2025": {
        "entity": "Blackstone PES",
        "period": "Q3 2025",
        "doc_type": "sec_10q",
        "filename": "Blackstone_PES_10Q_Q3_2025.htm",
    },
}


def list_documents() -> list[dict]:
    """Return registry metadata for all known documents."""
    return [{"doc_id": did, **meta} for did, meta in _DOC_REGISTRY.items()]


def load_document(doc_id: str, corpus_dir: Path) -> Document:
    """Load and section a single document by its registered ID."""
    if doc_id not in _DOC_REGISTRY:
        raise KeyError(f"Unknown doc_id: {doc_id}")
    meta = _DOC_REGISTRY[doc_id]
    path = corpus_dir / meta["filename"]
    if not path.exists():
        raise FileNotFoundError(f"Corpus file missing: {path}")

    if meta["doc_type"] == "psers_quarterly":
        sections = _load_psers_pdf(path)
    elif meta["doc_type"] == "sec_10q":
        sections = _load_sec_10q_html(path)
    else:
        raise ValueError(f"Unsupported doc_type: {meta['doc_type']}")

    return Document(
        doc_id=doc_id,
        entity=meta["entity"],
        period=meta["period"],
        doc_type=meta["doc_type"],
        source_path=str(path),
        sections=sections,
    )


__all__: Iterable[str] = (
    "Document",
    "Section",
    "list_documents",
    "load_document",
)
