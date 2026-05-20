# Local setup guide (Windows)

Step-by-step for getting the LP Diligence Agent running on a fresh Windows machine.

## 1. Install Python 3.11+

Download from https://www.python.org/downloads/. During install, check "Add Python to PATH".

Verify:
```powershell
python --version
# Should print Python 3.11.x or higher
```

## 2. Clone the repo

```powershell
cd C:\Users\krawc\projects
git clone https://github.com/CZtrader299/lp-diligence-agent
cd lp-diligence-agent
```

## 3. Set up the Python environment

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -e ".[embeddings,dev]"
```

The `[embeddings]` extra pulls in `sentence-transformers` and `sqlite-vec`. The first import of `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~90MB). One-time cost.

## 4. Configure your API key

```powershell
cd ..
copy .env.example .env
notepad .env
```

Paste your Anthropic API key into the `ANTHROPIC_API_KEY=` line.

## 5. Ingest the corpus

This loads all 5 documents, chunks them, embeds them locally, and stores everything in `data/cache/vectors.sqlite`.

```powershell
cd backend
lp-diligence ingest
```

First run takes 1-2 minutes (mostly the local embedding pass). Re-runs are idempotent — chunks with the same ID are replaced.

## 6. Try the agent

```powershell
# List loaded documents
lp-diligence list

# Run the full 9-item checklist against one document
lp-diligence checklist PSERS_HL_2Q17

# Ask one ad-hoc question (retrieval only, no LLM call)
lp-diligence ask "What is the portfolio IRR?" --doc PSERS_HL_2Q17
```

A full checklist run consumes roughly $0.20 in Anthropic spend.

## 7. Start the API server (for the Next.js frontend)

```powershell
uvicorn lp_diligence.api:app --reload --port 8000
```

Then in another shell:
```powershell
curl http://localhost:8000/api/documents
```

## 8. Run the eval (optional)

```powershell
cd ..\eval
python run_eval.py --sample 5    # smoke test on first 5 questions (~$1)
python run_eval.py               # full 20-question run (~$3-5)
```

Reports land in `eval/reports/` as both JSON and Markdown.

## 9. MCP server (Claude Desktop)

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "lp-diligence": {
      "command": "C:\\Users\\krawc\\projects\\lp-diligence-agent\\backend\\.venv\\Scripts\\python.exe",
      "args": ["-m", "lp_diligence.mcp_server"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-..."
      }
    }
  }
}
```

Restart Claude Desktop. The four tools (`list_documents`, `checklist_items`, `run_diligence_checklist`, `ask_document`) should appear in the MCP indicator.

## Troubleshooting

**"sqlite-vec is required"** — `pip install -e ".[embeddings]"` from the `backend/` directory.

**`ANTHROPIC_API_KEY is not set`** — Verify `.env` is at the repo root (`lp-diligence-agent/.env`), not under `backend/`.

**PDF extraction looks garbled** — The PSERS reports include scanned pages in some sections; `pypdf` text extraction returns whitespace for those. Affected sections will have low chunk density but the agent will still refuse appropriately on questions targeting them.

**Rate limit error** — The API enforces 10 checklist runs per hour per IP by default. Adjust `RATE_LIMIT_MAX_RUNS` in env if needed.
