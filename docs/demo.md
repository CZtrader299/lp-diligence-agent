# Running the demo (local + public tunnel)

The LP Diligence Agent demo has two processes: a Python FastAPI backend and a Next.js frontend. The frontend proxies API calls to the backend via Next's `rewrites()`, so a single Cloudflare tunnel pointed at the frontend exposes both surfaces under one public URL.

## Local-only

You need three terminals (backend, frontend, optional tunnel).

**Terminal 1 — backend:**
```powershell
cd backend
.venv\Scripts\Activate.ps1
uvicorn lp_diligence.api:app --port 8000
```

**Terminal 2 — frontend:**
```powershell
cd frontend
npm install        # one time
npm run dev
# http://localhost:3003
```

The frontend forwards `/api/*` to the backend on `:8000`. Override with `NEXT_PUBLIC_BACKEND_URL` in `frontend/.env.local` if you need a different backend address.

## Public URL via Cloudflare Tunnel

Free, no Cloudflare account needed. Gives you a `*.trycloudflare.com` URL that stays live as long as your laptop is on.

### One-time setup

```powershell
winget install --id Cloudflare.cloudflared
cloudflared --version
```

### Each session

With the backend and frontend already running in their own terminals (see above), open a third terminal:

```powershell
cd frontend
npm run tunnel
```

`cloudflared` prints a URL like `https://random-words-1234.trycloudflare.com`. Share that link; it works from anywhere as long as both dev servers and `cloudflared` are running.

## Tradeoffs of this setup

This is a laptop-hosted demo, not a hosted service:

- **Free**, no monthly cost, no signup needed for the quick tunnel
- **Demo is offline when your laptop is off, asleep, or off your network**
- **The URL rotates** each time you restart the tunnel; keep the tunnel running for the duration of a single review window
- **No autoscale, no observability** — this is intentional for a portfolio demo, not a real product

For a persistent always-on URL, switch to a named Cloudflare tunnel with a `lp-diligence.krawczun.com` DNS record, or host the backend on Railway/Render/HF Spaces.
