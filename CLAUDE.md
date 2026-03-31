# CLAUDE.md — Blabber

## What This Project Is

**Blabber** is an open-source lip sync sprite generator. It takes a face image as input and outputs 9 mouth shape sprites (Preston Blair phoneme system) using Gemini AI via OpenRouter. It also includes a browser demo that plays audio with real-time lip sync animation using those sprites.

**Origin:** Extracted from the [HistOracle](https://historacle.ai) production platform's lip sync pipeline.
**GitHub org:** `historacle-ai` | **Owner:** Arun Kashyap (`kashyaparun25`)

## Claude Code Plugin

This repo is a **Claude Code plugin**. Users install it via:
```
/plugin install historacle-ai/blabber
```

Then use the skill:
```
/blabber:lip-sync-pipeline photo.jpg
```

### Plugin structure
- `.claude-plugin/plugin.json` — Plugin manifest (name, version, metadata)
- `skills/lip-sync-pipeline/SKILL.md` — The pipeline skill

### Skills
- **`/blabber:lip-sync-pipeline`** — End-to-end sprite generation pipeline. Covers face detection, Gemini generation, post-processing, placement config, and demo integration.

## Architecture

Two independent parts sharing no code:

```
blabber/              Python package — image in, 9 mouth sprites out
demo/                 Vanilla TS + Vite — sprites + audio in, lip sync animation out
```

## Python Package (`blabber/`)

| File | Purpose | Source |
|------|---------|--------|
| `shapes.py` | 9 Preston Blair shape definitions + Gemini prompt template | Extracted from Historacle `scripts/generate_lip_sync_sprites.py` |
| `face_detect.py` | Auto face detection via MediaPipe (NEW — not in Historacle) | Written fresh |
| `generator.py` | Core: face detect → crop → Gemini API → 9 sprites | Extracted + refactored from `scripts/generate_lip_sync_sprites.py` |
| `postprocess.py` | rembg background removal + soft-edge feathering | Extracted from `scripts/generate_soft_edge_sprites.py` |
| `cli.py` | CLI entry point: `blabber generate <image>` | Written fresh |
| `reference/` | 12 Preston Blair cartoon reference JPGs (bundled) | Copied from Historacle `frontend/public/lip-sync/reference/` with commas removed from filenames |

### CLI Usage
```bash
export OPENROUTER_API_KEY=sk-or-...
blabber generate photo.jpg --output-dir ./sprites --verbose
```

### Dependencies
- `Pillow>=10.0` — image manipulation
- `rembg>=2.0` — AI background removal (downloads U2Net ~170MB on first run)
- `mediapipe>=0.10` — face detection
- API: OpenRouter (`urllib.request`, no `requests` dep)

## JS Demo (`demo/`)

| File | Purpose | Source |
|------|---------|--------|
| `src/audioAnalyser.ts` | Web Audio API bridge (AnalyserNode) | Ported from Historacle `frontend/lib/hooks/useAudioAnalyser.ts` |
| `src/lipSync.ts` | Hybrid audio+text lip sync engine | Ported from Historacle `frontend/lib/hooks/useTextLipSync.ts` |
| `src/mouthRenderer.ts` | Dual-layer crossfade sprite renderer | Ported from Historacle `frontend/app/_components/chat/MouthOverlay.tsx` |
| `src/main.ts` | UI wiring, file inputs, playback | Written fresh |
| `index.html` | Single-page dark-themed demo UI | Written fresh |

### Demo Usage
```bash
cd demo && npm install && npm run dev
# Open http://localhost:5173
# Load sprites + audio + optional transcript → Play
```

### Key Algorithms (in lipSync.ts)
- 28 letter preferences + 12 digraph preferences → shape selection per energy level
- 3-tier hysteresis (LOW/MID/HIGH) with asymmetric thresholds
- Exponential moving average smoothing (rise=0.28, decay=0.18)
- 100ms min shape hold, 180ms text cursor advance, 200ms silence grace
- 60ms CSS crossfade between shapes

## Current Status

### Done
- Full Python package with CLI, auto face detection, generation, post-processing
- Full JS demo with lip sync engine, audio analysis, crossfade renderer
- Canvas-based simple demo (`simple.html` + `simple.ts`) — draws mouth shapes on canvas overlay
- Sprite-based full demo (`index.html` + `main.ts` + `mouthRenderer.ts`) — file input + crossfade
- README, LICENSE (MIT), pyproject.toml, .gitignore
- 12 reference images bundled and renamed (commas removed from filenames)
- Git repo initialized (no commits yet)
- Sample image (`demo/public/sample/sample.png`) and audio (`demo/public/sample/sample_audio.mp3`) placed
- `/blabber:lip-sync-pipeline` skill created as Claude Code plugin (`.claude-plugin/` + `skills/`)
- Vite config routes to `simple.html` by default, supports both demo entry points

### TODO
1. **Create GitHub repo + push** — `gh repo create historacle-ai/blabber --public --source . --push`
2. **Generate sample sprites** — `blabber generate demo/public/sample/sample.png --output-dir demo/public/sample/sprites -v`
3. **Test `pip install -e .`** — verify package installs and `blabber --help` works
4. **Test plugin install** — from another project: `/plugin install historacle-ai/blabber`
5. **Test full pipeline end-to-end** — generate sprites → copy to demo → verify in browser
6. **Publish to PyPI** (later)
7. **Submit to Anthropic plugin marketplace** (later) — https://platform.claude.com/plugins/submit

## Commands

```bash
# Install package in dev mode
pip install -e .
# or
uv pip install -e .

# Run CLI
blabber --help
blabber generate photo.jpg --api-key sk-or-... --output-dir ./sprites -v

# Run demo
cd demo && npm install && npm run dev

# Build demo
cd demo && npm run build
```

## Demo Modes

### Canvas-based (simple.html — default)
Draws mouth shapes directly on a `<canvas>` overlay on top of the portrait image. No generated sprite files needed. Good for testing and quick demos.
- Entry: `demo/simple.html`
- Logic: `demo/src/simple.ts`
- Config: `MOUTH_CENTER_X`, `MOUTH_CENTER_Y`, `MOUTH_WIDTH`, `MOUTH_HEIGHT` constants
- Vite opens this by default (`server.open: '/simple.html'`)

### Sprite-based (index.html)
Uses actual generated sprite images with dual-layer crossfade animation. Production quality.
- Entry: `demo/index.html`
- Logic: `demo/src/main.ts` + `demo/src/mouthRenderer.ts`
- Requires generated sprites (shape_A.webp through shape_X.webp)

## Sample Assets
- `demo/public/sample/sample.png` — Henry George portrait (3001x1988ish scene at desk)
- `demo/public/sample/sample_audio.mp3` — Speech audio clip for demo

## Key Design Decisions
- **No `requests` dependency** — uses stdlib `urllib.request` for OpenRouter API calls
- **MediaPipe for face detection** — lightweight, no GPU required, model_selection=1 for full-range
- **Face crop expansion** — top 30%, bottom 50%, sides 25% beyond MediaPipe bbox (head+neck)
- **Reference images renamed** — `B,M,P.jpg` → `BMP.jpg` to avoid filesystem issues
- **Vanilla TS demo** — no React/framework dependency, maximum accessibility
- **Dual-layer crossfade** — two stacked `<img>` elements with CSS opacity transitions
