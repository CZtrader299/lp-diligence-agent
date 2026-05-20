// Resolve API base URL for the calling context.
// - Browser (typeof window !== "undefined"): use relative paths so Next's
//   rewrites() proxy to the backend.
// - Server Components / Route Handlers: prefix with the backend URL directly
//   since rewrites() doesn't apply to server-side fetches.
function apiUrl(path: string): string {
  if (typeof window !== "undefined") return path;
  const base = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
  return `${base}${path}`;
}

export type DocMeta = {
  doc_id: string;
  entity: string;
  period: string;
  doc_type: string;
  filename: string;
};

export type Citation = {
  chunk_id: string;
  doc_id: string;
  entity: string;
  period: string;
  section: string;
  page_start: number | null;
  page_end: number | null;
  excerpt: string;
  score: number;
};

export type ChecklistAnswer = {
  item_id: string;
  question: string;
  answer: string;
  confidence: "high" | "medium" | "refused";
  citations_used: string[];
  citations: Citation[];
  latency_ms: number;
  tokens_in: number;
  tokens_out: number;
};

export async function fetchDocuments(): Promise<DocMeta[]> {
  const r = await fetch(apiUrl("/api/documents"), { cache: "no-store" });
  if (!r.ok) throw new Error("Failed to fetch documents");
  const data = await r.json();
  return data.documents;
}

export async function fetchChecklistItems(): Promise<{ id: string; question: string }[]> {
  const r = await fetch(apiUrl("/api/checklist/items"), { cache: "no-store" });
  if (!r.ok) throw new Error("Failed to fetch checklist items");
  const data = await r.json();
  return data.items;
}

export async function runChecklist(doc_id: string): Promise<ChecklistAnswer[]> {
  const r = await fetch(apiUrl("/api/checklist/run"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  if (!r.ok) {
    const detail = await r.text();
    throw new Error(detail || "Checklist run failed");
  }
  const data = await r.json();
  return data.answers;
}

export async function askDocument(doc_id: string, question: string): Promise<ChecklistAnswer> {
  const r = await fetch(apiUrl("/api/ask"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, question }),
  });
  if (!r.ok) {
    const detail = await r.text();
    throw new Error(detail || "Ask failed");
  }
  const data = await r.json();
  return data.answer;
}
