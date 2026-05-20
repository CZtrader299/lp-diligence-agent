# Solution Design: LP Diligence Agent

## Problem

Every LP and fund-of-funds manager reads hundreds of GP quarterly reports per quarter. Each report follows a different format, runs 20-100 pages, and contains a long tail of redacted or non-load-bearing content. The 80% of the work that adds no signal is the part that consumes most of the analyst's time: locating the same nine or ten figures inside the same nine or ten differently structured documents. The 20% that matters — anomaly detection, methodology changes, key-person flags — is what gets compressed when the queue is full.

## Current state (typical LP workflow)

1. GP delivers quarterly report to LP (PDF or document portal)
2. Junior analyst opens the report and extracts a fixed set of figures into a spreadsheet
3. Findings are summarized into a portfolio-monitoring memo
4. Senior reviewer scans the memo, flags exceptions, decides whether to escalate

Time-to-memo per report: typically 45–90 minutes. Bottleneck: step 2 (extraction).

## Proposed state

An agent performs step 2 in under a minute, with three properties step 2 currently lacks:

1. **Cited extractions.** Every number traces back to a specific page and section excerpt. The analyst can audit any field in two clicks.
2. **Explicit refusal.** When the report does not disclose a figure (or it has been redacted), the agent returns "data not available" rather than fabricating a number. The analyst sees what is missing, not a confident wrong answer.
3. **Change-over-time.** When prior quarters of the same GP are ingested, the agent surfaces deltas without being asked.

The analyst now starts the workflow at step 3 with a draft memo already in hand.

## KPIs

| Metric | Target |
|---|---|
| Time-to-memo per report | < 15 min (from 45–90 min) |
| Faithfulness (judge-scored) | > 0.85 mean across golden set |
| Refusal correctness | > 0.95 (false-refusals and false-confidences both penalized) |
| Analyst override rate on cited figures | < 5% after 30 days |
| User adoption (active reviewers / month) | > 80% of investment team within 90 days |

## Guardrails

- Citation required for every numeric claim; LLM cannot answer without retrieved support
- Confidence tag per answer (`high`, `medium`, `refused`) surfaced in the UI
- Audit log of every retrieved chunk and tool call per session
- All document processing local; only synthesis calls touch a hosted LLM
- LLM provider configurable per environment (Anthropic in this prototype, swappable for Azure OpenAI in an enterprise deployment)
- Rate limiting at the API edge to control demo cost and prevent abuse

## Rollout plan (12-week pilot)

| Week | Milestone |
|---|---|
| 1-2 | Discovery: shadow 3 senior analysts through 5 GP reports each, capture current-state friction points |
| 3-4 | Pilot deployment: 5-analyst beta, 10-report scope, daily feedback session |
| 5-6 | Eval refinement: extend golden set to 100 questions across pilot reports, retrain prompts on failed cases |
| 7-8 | Expansion: 20 analysts, broaden to portfolio-monitoring memo generation (not just extraction) |
| 9-10 | Governance: legal/compliance review, audit-log retention policy, AI-usage policy update |
| 11-12 | Decision: scale firmwide, expand to capital-call notice parsing, or kill |

## Risk and mitigation

| Risk | Mitigation |
|---|---|
| Hallucinated figures slip through to investment decisions | Hard requirement for citations; refusal mode; analyst override tracked as a KPI |
| Model regression after a version upgrade | Eval harness runs on every prompt/model change; gate releases on metric thresholds |
| Sensitive data leakage via LLM API | Local-only processing for ingestion; redact PII before synthesis; vendor with zero-retention API terms |
| Analyst over-reliance erodes skill | Citations make the underlying disclosure visible; design favors "draft for analyst" over "answer for analyst" |

## What this prototype demonstrates vs. what would change in a real deployment

This prototype is a working agent over a 5-document public corpus. A production deployment at a real LP or fund-of-funds manager would differ in three ways:

1. **Data plane** — corpus would land in Snowflake or Azure Blob via existing ingestion pipelines, not be hand-downloaded; retrieval would join chunks against the firm's existing fund-master table
2. **Identity** — agent calls would be SSO-gated with per-user audit logs and document-level ACLs
3. **Provider** — synthesis would route through an enterprise Anthropic or Azure OpenAI endpoint with zero-retention terms

The shape of the agent — multi-step diligence checklist, structured outputs, citation-required answers, refusal-by-default, eval harness — is the same.
