import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LP Diligence Agent",
  description: "Agentic AI diligence over LP-format private-equity quarterly reports",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen">
          <header className="border-b border-[var(--border)]">
            <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
              <a href="/" className="font-semibold tracking-tight">
                LP Diligence Agent
              </a>
              <nav className="flex items-center gap-6 text-sm text-neutral-400">
                <a href="/" className="hover:text-white">Reports</a>
                <a href="/about" className="hover:text-white">About</a>
                <a
                  href="https://github.com/CZtrader299/lp-diligence-agent"
                  target="_blank"
                  rel="noreferrer"
                  className="hover:text-white"
                >
                  GitHub
                </a>
              </nav>
            </div>
          </header>
          <main className="max-w-6xl mx-auto px-6 py-10">{children}</main>
          <footer className="border-t border-[var(--border)] mt-16">
            <div className="max-w-6xl mx-auto px-6 py-6 text-xs text-neutral-500">
              Built by{" "}
              <a href="https://krawczun.com" className="hover:text-white">
                Dan Krawczun
              </a>{" "}
              as a portfolio piece. All documents in the corpus are publicly available
              regulatory or FOIA-released filings.
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
