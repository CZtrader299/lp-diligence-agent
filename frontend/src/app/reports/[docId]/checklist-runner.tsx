"use client";

import { useState } from "react";
import { runChecklist, type ChecklistAnswer } from "@/lib/api";

type Props = {
  docId: string;
  items: { id: string; question: string }[];
};

const CONFIDENCE_CLASSES: Record<string, string> = {
  high: "bg-emerald-500/10 text-emerald-400 border-emerald-500/40",
  medium: "bg-amber-500/10 text-amber-400 border-amber-500/40",
  refused: "bg-neutral-500/10 text-neutral-400 border-neutral-500/40",
};

export function ChecklistRunner({ docId, items }: Props) {
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [answers, setAnswers] = useState<ChecklistAnswer[] | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  async function onRun() {
    setRunning(true);
    setError(null);
    setAnswers(null);
    try {
      const result = await runChecklist(docId);
      setAnswers(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "unknown error");
    } finally {
      setRunning(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={onRun}
          disabled={running}
          className="px-4 py-2 rounded-md bg-[var(--accent)] text-black font-medium disabled:opacity-50"
        >
          {running ? "Running diligence checklist..." : "Run 9-item diligence checklist"}
        </button>
        {answers && (
          <span className="text-sm text-neutral-400">
            {answers.length} items · avg latency{" "}
            {Math.round(answers.reduce((s, a) => s + a.latency_ms, 0) / answers.length)} ms
          </span>
        )}
      </div>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/5 p-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {!answers && !running && (
        <div className="text-sm text-neutral-500 max-w-xl">
          Each item runs a separate retrieval + LLM call against this document. A full run takes
          roughly 25–45 seconds and consumes about $0.20 in API spend. Click any item below for the
          underlying citations.
        </div>
      )}

      {answers && (
        <ul className="space-y-3">
          {answers.map((a) => {
            const item = items.find((i) => i.id === a.item_id);
            const isExpanded = expanded === a.item_id;
            return (
              <li
                key={a.item_id}
                className="border border-[var(--border)] rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => setExpanded(isExpanded ? null : a.item_id)}
                  className="w-full px-5 py-4 text-left hover:bg-[var(--muted)] flex items-start gap-4"
                >
                  <span
                    className={`text-xs uppercase tracking-wide px-2 py-1 rounded border ${
                      CONFIDENCE_CLASSES[a.confidence] || CONFIDENCE_CLASSES.refused
                    }`}
                  >
                    {a.confidence}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-neutral-400">{item?.question}</div>
                    <div className="mt-1 text-white">{a.answer}</div>
                  </div>
                  <span className="text-xs text-neutral-500 mono shrink-0">
                    {a.latency_ms}ms
                  </span>
                </button>
                {isExpanded && (
                  <div className="border-t border-[var(--border)] px-5 py-4 space-y-3 bg-[var(--muted)]">
                    <div className="text-xs uppercase tracking-wide text-neutral-500">
                      Retrieved chunks ({a.citations.length})
                    </div>
                    {a.citations.map((c) => (
                      <div key={c.chunk_id} className="text-sm">
                        <div className="text-neutral-400 mono text-xs">
                          [{c.entity} {c.period} {c.section}
                          {c.page_start ? ` p.${c.page_start}` : ""}] · score{" "}
                          {c.score.toFixed(3)}
                        </div>
                        <div className="text-neutral-300 mt-1 line-clamp-4">{c.excerpt}</div>
                      </div>
                    ))}
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
