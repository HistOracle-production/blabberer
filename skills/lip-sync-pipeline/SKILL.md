---
name: lip-sync-pipeline
description: Generate lip sync mouth shape sprites from any face image. Auto-detects face, generates 9 Preston Blair mouth shapes via Gemini AI, removes backgrounds, applies soft edges. Includes browser demo with real-time audio-driven animation. Use when you need lip sync sprites for a character, avatar, or any face image.
argument-hint: "[image_path]"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit, Agent
---

# Blabberer — Lip Sync Sprite Pipeline

Generate 9 mouth shape sprites from any face image using AI.

```
Input Image → Face Detection → Gemini AI → 9 Mouth Shapes → Background Removal → Soft Edges → Ready
```

## Installation

If you don't already have the blabberer Python package installed:

```bash
# Clone the repo (if not already cloned)
git clone https://github.com/HistOracle-production/blabberer.git
cd blabberer

# Install the Python package
pip install -e .
# OR
uv pip install -e .
```

Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY=sk-or-...   # Get one at https://openrouter.ai/keys
```

First run downloads the rembg U2Net model (~170MB). Subsequent runs are instant.

## Quick Pipeline

### One-command generation

```bash
blabberer generate <image_path> --output-dir ./sprites --verbose
```

This auto-detects the face, generates all 9 shapes, removes backgrounds, and applies soft edges.

**Output:**
```
sprites/
├── shape_A.png through shape_H.png, shape_X.png   # Raw PNGs
├── shape_A.webp through shape_X.webp               # Transparent background
└── soft/
    └── shape_A.webp through shape_X.webp            # Production-ready (soft edges)
```

### Manual face crop (if auto-detection fails)

```bash
blabberer generate image.png --crop-box left,top,right,bottom
```

## The 9 Preston Blair Shapes

| Shape | Phonemes | Mouth Position |
|-------|----------|----------------|
| **A** | M, B, P | Lips pressed together |
| **B** | S, T, D, K, N | Slightly parted, teeth visible |
| **C** | A, I | Open mouth (speaking vowels) |
| **D** | E | Wide horizontal stretch |
| **E** | O | Rounded oval |
| **F** | U, W, Q | Puckered lips |
| **G** | F, V | Upper teeth on lower lip |
| **H** | L, T, D, N | Barely parted |
| **X** | (idle) | Resting/closed mouth |

## Running the Demo

The repo includes a browser-based demo that plays audio with real-time lip sync:

```bash
cd demo
npm install
npm run dev
# Opens http://localhost:5173
```

### Demo modes

**Canvas mode** (`simple.html` — default): Draws mouth shapes on a canvas overlay. Works immediately, no sprites needed.

**Sprite mode** (`index.html`): Uses actual generated sprite images with crossfade animation. Load sprites + audio via file inputs.

### Configuring mouth position

In `demo/src/simple.ts`, adjust these constants to position the mouth overlay on your face image:

```typescript
const MOUTH_CENTER_X = 0.50;  // horizontal center (fraction of image width)
const MOUTH_CENTER_Y = 0.62;  // vertical position (fraction of image height)
const MOUTH_WIDTH = 0.18;     // mouth width (fraction of image width)
const MOUTH_HEIGHT = 0.08;    // mouth height (fraction of image height)
```

## How the Lip Sync Algorithm Works

The demo's `LipSyncEngine` uses a hybrid approach:

1. **Audio energy** (Web Audio API AnalyserNode) drives mouth openness — rhythm
2. **Text phonemes** (28 letter + 12 digraph mappings) drive shape selection — variety
3. **3-tier hysteresis** (LOW/MID/HIGH) prevents flickering at energy boundaries
4. **100ms min hold** prevents "chewing" artifacts
5. **60ms crossfade** between shapes for smooth animation

## Using in Your Own Project

### Python API

```python
from blabberer import generate_sprites, full_postprocess

# Generate sprites
results = generate_sprites(
    image_path="photo.jpg",
    output_dir="./sprites",
    api_key="sk-or-...",
)

# Post-process
final = full_postprocess("./sprites")
```

### JavaScript/TypeScript

The demo's `src/` files are standalone vanilla TypeScript — copy them into any project:

- `lipSync.ts` — `LipSyncEngine` class (text+audio → mouth shape)
- `audioAnalyser.ts` — `AudioAnalyser` class (Web Audio API bridge)
- `mouthRenderer.ts` — `MouthRenderer` class (dual-layer crossfade)

No React, no framework dependencies.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "No face detected" | Use `--crop-box left,top,right,bottom` manual override |
| All shapes look the same | Re-run — Gemini results vary per call |
| No sound in demo | Click the page first (browser autoplay policy) |
| Sprites have background | Check rembg version: `pip install --upgrade rembg` |
| Mouth overlay misaligned | Adjust `MOUTH_CENTER_X/Y` constants |

## CLI Reference

```
blabberer generate <image> [options]

Options:
  --api-key KEY          OpenRouter API key (or OPENROUTER_API_KEY env var)
  --output-dir, -o DIR   Output directory (default: ./sprites)
  --crop-box L,T,R,B    Manual face crop box (auto-detects if omitted)
  --model MODEL          Gemini model (default: google/gemini-3.1-flash-image-preview)
  --workers N            Concurrent API calls (default: 3)
  --skip-postprocess     Skip background removal and soft edges
  --verbose, -v          Print detailed progress
```
