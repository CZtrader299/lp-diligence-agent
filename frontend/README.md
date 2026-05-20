# LP Diligence Agent — Frontend

Next.js 16 (App Router) + Tailwind v4 demo UI for the diligence agent.

## Local dev

```powershell
cd frontend
npm install
copy .env.example .env.local
npm run dev
# http://localhost:3003
```

Assumes the backend FastAPI server is running on http://localhost:8000. Adjust `NEXT_PUBLIC_BACKEND_URL` in `.env.local` if hosting it elsewhere.

## Deployment

Vercel: import the repo, set the project root to `frontend/`, set `NEXT_PUBLIC_BACKEND_URL` to the deployed backend URL. Build command and output are default.

## Pages

- `/` — list of available LP reports
- `/reports/[docId]` — run the 9-item checklist against one document
- `/about` — project context
