// Server-side proxy for the ad-hoc Q&A call. Same reasoning as
// /api/checklist/run — keeps us off the dev-time rewrites() proxy timeout.

import { NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 120;

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export async function POST(request: Request) {
  const body = await request.text();
  try {
    const upstream = await fetch(`${BACKEND}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
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
