#!/usr/bin/env node
/**
 * Launches a one-off Cloudflare quick tunnel for the LP Diligence Agent demo.
 * Points at the Next.js frontend (default :3003); the frontend proxies
 * /api/* to the FastAPI backend (default :8000) via next.config.ts rewrites,
 * so a single tunnel covers both surfaces.
 *
 * Prints a *.trycloudflare.com URL that stays live as long as this process
 * and both dev servers are running. No Cloudflare account required.
 */
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";

const FS_CANDIDATES = [
  "C:\\Program Files (x86)\\cloudflared\\cloudflared.exe",
  "C:\\Program Files\\cloudflared\\cloudflared.exe",
];

function resolveBinary() {
  for (const c of FS_CANDIDATES) {
    if (existsSync(c)) return c;
  }
  return "cloudflared";
}

const bin = resolveBinary();
const PORT = process.env.PORT || "3003";
console.log(`Using cloudflared: ${bin}`);
console.log(`Quick tunnel → http://localhost:${PORT}\n`);

const proc = spawn(bin, ["tunnel", "--url", `http://localhost:${PORT}`], { stdio: "inherit" });

proc.on("error", (err) => {
  if (err.code === "ENOENT") {
    console.error("\ncloudflared not on PATH. Install: winget install --id Cloudflare.cloudflared");
    process.exit(1);
  }
  throw err;
});

proc.on("close", (code) => process.exit(code ?? 0));
