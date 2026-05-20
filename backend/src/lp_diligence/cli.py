"""CLI: lp-diligence <command> ..."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from . import config
from .checklist import CHECKLIST_ITEMS, run_checklist
from .documents import list_documents
from .ingest import ingest_all
from .retrieval import retrieve


def _cmd_list(_args: argparse.Namespace) -> int:
    for meta in list_documents():
        print(f"{meta['doc_id']:30s}  {meta['entity']:20s}  {meta['period']}  ({meta['doc_type']})")
    return 0


def _cmd_ingest(_args: argparse.Namespace) -> int:
    result = ingest_all()
    print(json.dumps(result, indent=2))
    return 0


def _cmd_ask(args: argparse.Namespace) -> int:
    hits = retrieve(args.question, doc_id=args.doc, k=args.k)
    for h in hits:
        print(f"{h.label()}  score={h.score:.3f}")
        print(f"  {h.excerpt[:200].strip()}...")
        print()
    return 0


def _cmd_checklist(args: argparse.Namespace) -> int:
    answers = run_checklist(args.doc, k=args.k)
    out = [asdict(a) for a in answers]
    print(json.dumps(out, indent=2))
    return 0


def _cmd_items(_args: argparse.Namespace) -> int:
    for item_id, question in CHECKLIST_ITEMS:
        print(f"{item_id}:")
        print(f"  {question}")
        print()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lp-diligence")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="list registered documents").set_defaults(func=_cmd_list)
    sub.add_parser("ingest", help="ingest the full corpus").set_defaults(func=_cmd_ingest)
    sub.add_parser("items", help="show the diligence checklist").set_defaults(func=_cmd_items)

    p_ask = sub.add_parser("ask", help="retrieve top-k chunks for a query")
    p_ask.add_argument("question")
    p_ask.add_argument("--doc", help="restrict to a single doc_id")
    p_ask.add_argument("--k", type=int, default=config.RETRIEVAL_K)
    p_ask.set_defaults(func=_cmd_ask)

    p_chk = sub.add_parser("checklist", help="run the 9-item checklist against a document")
    p_chk.add_argument("doc", help="doc_id, e.g. PSERS_HL_2Q17")
    p_chk.add_argument("--k", type=int, default=config.RETRIEVAL_K)
    p_chk.set_defaults(func=_cmd_checklist)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
