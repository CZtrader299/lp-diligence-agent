import Link from "next/link";
import { fetchDocuments } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  let docs: Awaited<ReturnType<typeof fetchDocuments>> = [];
  let error: string | null = null;
  try {
    docs = await fetchDocuments();
  } catch (e) {
    error = e instanceof Error ? e.message : "unknown error";
  }

  return (
    <div className="space-y-10">
      <section className="space-y-3">
        <h1 className="text-3xl font-semibold tracking-tight">LP Diligence Agent</h1>
        <p className="text-neutral-400 max-w-2xl">
          Pick a quarterly report. The agent runs a nine-item diligence checklist against the
          document and returns structured, citation-backed answers. Designed for sophisticated LPs
          and fund-of-fund managers who read hundreds of these per quarter.
        </p>
      </section>

      {error && (
        <div className="rounded-lg border border-red-500/40 bg-red-500/5 p-4 text-red-300 text-sm">
          Backend unreachable: {error}
        </div>
      )}

      <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {docs.map((d) => (
          <Link
            key={d.doc_id}
            href={`/reports/${d.doc_id}`}
            className="border border-[var(--border)] rounded-lg p-5 hover:border-[var(--accent)] transition-colors"
          >
            <div className="text-xs uppercase tracking-wide text-neutral-500">{d.doc_type}</div>
            <div className="mt-1 font-semibold">{d.entity}</div>
            <div className="text-sm text-neutral-400">{d.period}</div>
            <div className="mt-3 text-xs text-neutral-500 mono">{d.doc_id}</div>
          </Link>
        ))}
      </section>
    </div>
  );
}
