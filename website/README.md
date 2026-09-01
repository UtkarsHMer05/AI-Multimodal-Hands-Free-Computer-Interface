# Voice Cursor — Project Website + Live Dashboard

A Next.js + TypeScript + Tailwind site with two surfaces:

1. **Landing page (`/`)** — public showcase: hero, modalities, command
   grammar, architecture diagrams, safety, evaluation, FAQ. Deployable as a
   plain static site (Vercel / Netlify / GitHub Pages); viewable by anyone.
   The interface mock is deliberately non-interactive: it points visitors to
   the dashboard.

2. **Live dashboard (`/dashboard`)** — the actual control surface. It connects
   over WebSocket to the local Python engine
   ([`voice_cursor/web_server.py`](../voice_cursor/web_server.py)) and drives
   the **real system**: continuous voice recognition (Parakeet/Vosk), head
   tracking and eye-gaze pointer control, tongue & blink click calibration,
   enable/pause safety state, transcript/feedback/log telemetry, and click-ring
   notifications. Commands execute on the Mac through the same guarded
   `ActionExecutor` used by the Tk application — the real pointer moves.

## Quick start (full system)

Double-click `run_website.command` in the repo root, or:

```bash
source .venv/bin/activate
python -m voice_cursor.web_server --open
```

This starts the engine at `http://localhost:8757` (serving the site and the
`ws://localhost:8757/bridge` WebSocket) and opens the dashboard. Grant
Microphone, Camera, Accessibility, and Screen Recording permission to your
terminal app (same one-time setup as the Tk application).

## Why a local server is required for live control

Browsers sandbox pages away from the OS: no web page can move a real pointer.
The dashboard therefore talks to the engine on your Mac, which already has
that capability — this is the same pattern as Jupyter or Ollama web UIs. The
public landing page deploys statically; the dashboard works when the engine
is running locally.

## Website development

```bash
cd website
npm install
npm run dev        # http://localhost:3000 (landing page only)
npm run build      # static export to out/ (served by the Python engine)
```

The `/dashboard` page is included in the static export; when no engine is
running it shows an "Engine offline" banner with restart instructions and
keeps retrying.

## Command parity

- `src/lib/commands.ts` — exact TypeScript port of `voice_cursor/commands.py`
  and `text_matching.py` (same grammar, normalization, difflib fuzzy fallback,
  refusal rules).
- `scripts/verify_port_parity.py` (repo root) asserts parity between the two
  implementations on a shared battery: 161/161 cases match.

## Deploy the landing page

**Vercel** — import the repo, root directory `website`.
**Netlify** — root `website`, build `npm run build`, publish `out`.
**GitHub Pages** — push `out/` to `gh-pages` (`trailingSlash: true` is set).

The deployed landing page is fully functional for visitors; the dashboard
shows its offline banner unless run against a local engine.
