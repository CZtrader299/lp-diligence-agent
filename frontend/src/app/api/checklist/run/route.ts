// Server-side proxy for the long-running checklist call.
// Next.js' built-in rewrites() proxy has an undocumented ~30s timeout in dev
// that kills the connection before our 9-item agent can finish. This route
// handler calls the backend directly with no intermediate timeout.

import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 300; // 5 min, well above the 30-60s real runtime

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.text();
  try {
    const upstream = await fetch(`${BACKEND}/api/checklist/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      // No client-side timeout; we wait as long as the backend takes.
    });
    const text = await upstream.text();
    return new NextResponse(text, {
      status: upstream.status,
      headers: { "Content-Type": upstream.headers.get("Content-Type") || "application/json" },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : "unknown error";
    return NextResponse.json({ detail: `Backend unreachable: ${message}` }, { status: 502 });
  }
}
