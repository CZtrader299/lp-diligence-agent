export default function AboutPage() {
  return (
    <div className="prose prose-invert max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">About</h1>
      <p className="text-neutral-300">
        The LP Diligence Agent is a portfolio prototype demonstrating an agentic-AI workflow
        applied to private-markets diligence. Given a private equity fund quarterly report, the
        agent runs a nine-item diligence checklist and returns citation-backed structured answers
        with explicit confidence tags.
      </p>
      <h2 className="text-lg font-semibold">Why this exists</h2>
      <p className="text-neutral-300">
        Built as a portfolio piece demonstrating an agentic-AI workflow over LP-format
        private-equity quarterly reports. The corpus uses publicly available materials:
        PSERS FOIA-released quarterly reports from 2017 plus SEC 10-Q filings from
        Blackstone Private Equity Strategies Fund (2025).
      </p>
      <h2 className="text-lg font-semibold">Architecture</h2>
      <ul className="text-neutral-300 list-disc ml-5 space-y-1">
        <li>Python backend: FastAPI + sqlite-vec + sentence-transformers</li>
        <li>Multi-step agent: one retrieval + one Anthropic Claude call per checklist item</li>
        <li>MCP server: same tools exposed for Claude Desktop</li>
        <li>Eval harness: 20-question golden set scored by an LLM judge</li>
        <li>Guardrails: citation-required answers, refusal-by-default on missing data</li>
      </ul>
      <p>
        <a
          href="https://github.com/CZtrader299/lp-diligence-agent"
          className="text-[var(--accent)] hover:underline"
        >
          Source on GitHub →
        </a>
      </p>
    </div>
  );
}
