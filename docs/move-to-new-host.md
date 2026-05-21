# Moving the demos to a different machine

This guide walks through migrating both running demos (`lp-diligence.krawczun.com` and `aicapex.krawczun.com`) from one Windows machine to another — useful when you want the public URLs served from an always-on home server instead of a laptop you carry around.

The architecture is laptop-hosted: a local Next.js + Python stack exposed via Cloudflare named tunnels. Moving means rebuilding the same stack on the new box and copying a small set of secrets that aren't in any git repo.

## What gets moved (and what doesn't)

| Item | Where it lives | How it moves |
|---|---|---|
| Code | Public GitHub repos | `git clone` on the new box |
| Python deps | `pyproject.toml` | `pip install` on the new box |
| Node deps | `package.json` | `npm install` on the new box |
| `.env` (Anthropic key) | Not in git | Manual copy |
| Cloudflare cert (`cert.pem`) | `~/.cloudflared/` | Manual copy |
| Tunnel credentials (`<uuid>.json`) | `~/.cloudflared/` | Manual copy |
| AI Capex tunnel config (`config.yml`) | `~/.cloudflared/` | Manual copy |
| LP Diligence tunnel config | In repo at `scripts/cloudflared-config.yml` | Comes with `git clone`; path inside needs editing |
| The DNS records on Cloudflare | Cloudflare's side, not on disk | Nothing to move; already configured |

## Step 1 — Install the base toolchain (one-time)

On the new machine, in PowerShell:

```powershell
winget install --id Python.Python.3.13
winget install --id OpenJS.NodeJS.LTS
winget install --id Cloudflare.cloudflared
winget install --id Git.Git
```

Restart PowerShell, then verify:

```powershell
python --version
node --version
cloudflared --version
git --version
```

## Step 2 — Clone the repos

```powershell
mkdir C:\Users\<you>\projects
cd C:\Users\<you>\projects
git clone https://github.com/krawczun/lp-diligence-agent
git clone https://github.com/krawczun/ai-capex-flow
```

## Step 3 — Install dependencies

```powershell
# LP Diligence backend
cd C:\Users\<you>\projects\lp-diligence-agent\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[embeddings,dev]"

# LP Diligence frontend
cd ..\frontend
npm install

# AI Capex frontend
cd ..\..\ai-capex-flow
npm install
```

## Step 4 — Copy the secrets

These files are not in git (correctly — they're credentials). Copy them from the old machine to the new one at the same relative paths.

| Old machine path | New machine path |
|---|---|
| `C:\Users\krawc\projects\lp-diligence-agent\.env` | `C:\Users\<you>\projects\lp-diligence-agent\.env` |
| `C:\Users\krawc\.cloudflared\cert.pem` | `C:\Users\<you>\.cloudflared\cert.pem` |
| `C:\Users\krawc\.cloudflared\c635abcb-b7e8-444f-b374-4cc31c1b2af2.json` | `C:\Users\<you>\.cloudflared\c635abcb-b7e8-444f-b374-4cc31c1b2af2.json` |
| `C:\Users\krawc\.cloudflared\2bddbd56-ae69-4fe1-8ddd-b7bdc3189d10.json` | `C:\Users\<you>\.cloudflared\2bddbd56-ae69-4fe1-8ddd-b7bdc3189d10.json` |
| `C:\Users\krawc\.cloudflared\config.yml` (AI Capex's named tunnel config) | `C:\Users\<you>\.cloudflared\config.yml` |
| `C:\Users\krawc\projects\ai-capex-flow\.env` (if it has one) | `C:\Users\<you>\projects\ai-capex-flow\.env` |

**Move them via:** USB drive, OneDrive, or a Remote Desktop copy-paste. Don't email them — they're credentials.

You may need to create the `.cloudflared` directory first: `mkdir C:\Users\<you>\.cloudflared`.

## Step 5 — Update the LP Diligence tunnel config

The file at `lp-diligence-agent\scripts\cloudflared-config.yml` has a hardcoded credentials path that points at the old user's home directory. Edit it:

```powershell
notepad C:\Users\<you>\projects\lp-diligence-agent\scripts\cloudflared-config.yml
```

Change:
```yaml
credentials-file: C:\Users\krawc\.cloudflared\c635abcb-b7e8-444f-b374-4cc31c1b2af2.json
```
to:
```yaml
credentials-file: C:\Users\<you>\.cloudflared\c635abcb-b7e8-444f-b374-4cc31c1b2af2.json
```

The tunnel UUID itself stays the same. Don't commit this edit (path is user-specific).

## Step 6 — Optional: update the `allowedDevOrigins` LAN IP

If the new machine has a different LAN IP (find it with `ipconfig`), update:

```typescript
// frontend/next.config.ts
allowedDevOrigins: [
  "lp-diligence.krawczun.com",
  "*.trycloudflare.com",
  "192.168.1.NN",   // ← new LAN IP, or remove this line entirely
]
```

The public URL works without it; this only matters if you also want to test from another device on the local network.

## Step 7 — Confirm the launcher script paths

`scripts/start-all-demos.ps1` references `C:\Users\krawc\projects\ai-capex-flow`. If your AI Capex repo lives somewhere else on the new machine, edit the `$capexRepo` line near the top of the script.

## Step 8 — Stop the old machine's tunnels

**Before** starting the new machine's tunnels, close all five terminal windows on the old machine. If two `cloudflared` processes for the same tunnel name are running on different machines, Cloudflare round-robins requests between them, which causes intermittent failures.

## Step 9 — Start the demos on the new machine

```powershell
C:\Users\<you>\projects\lp-diligence-agent\scripts\start-all-demos.ps1
```

Wait ~30 seconds for the tunnels to register. Then check:

- `https://lp-diligence.krawczun.com` — should load
- `https://aicapex.krawczun.com` — should load

If either 1033s, look at the corresponding tunnel window for connection errors.

## Step 10 — Keep the new machine always-on

### Disable sleep on AC power

PowerShell as Administrator:

```powershell
powercfg /change standby-timeout-ac 0
powercfg /change hibernate-timeout-ac 0
powercfg /change monitor-timeout-ac 0
```

### Allow lid-closed operation (if it's a laptop)

```powershell
powercfg /setacvalueindex SCHEME_CURRENT SUB_BUTTONS LIDACTION 0
powercfg /setactive SCHEME_CURRENT
```

### Auto-start the demos at login

Create a shortcut in `C:\Users\<you>\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\` with:

```
Target: powershell.exe -ExecutionPolicy Bypass -File "C:\Users\<you>\projects\lp-diligence-agent\scripts\start-all-demos.ps1"
```

After a Windows update reboot, log back in and the demos come up automatically.

## Verifying it worked

From any other device (your phone, a different network):

1. Open `https://lp-diligence.krawczun.com`
2. Click a document, run the checklist
3. Wait for the 9-item results

If that works end-to-end, the move is done. Power down or unplug the old machine — the public URLs now route to the new one.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Cloudflare 1033 error | Tunnel process not running, or running on wrong machine | Check the tunnel window for "Registered tunnel connection" lines |
| 404 on the tunnel URL | DNS pointing at the wrong tunnel UUID | `cloudflared tunnel route dns --overwrite-dns <UUID> <HOSTNAME>` |
| Backend 500 errors | `.env` not copied or `ANTHROPIC_API_KEY` empty | Verify `.env` exists at repo root and the key is set |
| Frontend "Backend unreachable" | Backend not running on :8000 or path wrong | `curl http://localhost:8000/healthz` |
| Slow first checklist run | Sentence-transformers downloading model | Normal on first run; cached for subsequent runs |
