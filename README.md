<div align="center">

# Blabberer

**AI-powered lip sync sprite generator**

Turn any face photo into 9 production-ready mouth shape sprites — and animate them in real time.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab.svg?logo=python&logoColor=white)](https://pypi.org/project/blabberer)
[![TypeScript](https://img.shields.io/badge/TypeScript-demo-3178c6.svg?logo=typescript&logoColor=white)](#interactive-demo)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-plugin-ff6b35.svg)](#claude-code-plugin)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/historacle-ai/blabberer/pulls)

<br>

https://github.com/user-attachments/assets/REPLACE_WITH_VIDEO_ID

<!-- To embed the video above:
     1. Go to https://github.com/historacle-ai/blabberer/issues/new
     2. Drag & drop demo/public/sample/demo_video.mp4 into the comment box
     3. GitHub will generate a URL like: https://github.com/user-attachments/assets/<UUID>
     4. Replace the placeholder URL above with that generated URL
     5. Close the issue without submitting -->

</div>

---

## Highlights

- **One command, nine sprites** — feed in a portrait, get back 9 mouth shapes based on the [Preston Blair phoneme system](https://en.wikipedia.org/wiki/Preston_Blair)
- **Auto face detection** — MediaPipe finds the face automatically; no manual cropping needed
- **AI-generated** — Gemini (via OpenRouter) generates each mouth shape from reference artwork
- **Production-ready output** — transparent backgrounds, soft-edge feathering, WebP format
- **Real-time lip sync engine** — vanilla TypeScript engine syncs audio energy + text phonemes to shapes at 60fps
- **Claude Code plugin** — install the skill and let Claude run the full pipeline for you
- **Zero frameworks** — Python stdlib for HTTP, vanilla TS for the demo — minimal dependencies

## How It Works

```
Portrait → Face Detection → Gemini AI → 9 Mouth Shapes → Post-Processing → Sprites
 (photo)    (MediaPipe)     (OpenRouter)  (Preston Blair)   (rembg + soft edges)   (WebP)
```

### The 9 Shapes

| Shape | Phonemes | Visual |
|:-----:|----------|--------|
| **A** | M, B, P | Lips pressed together |
| **B** | S, T, D, K, N | Teeth visible, slightly open |
| **C** | A, I | Open mouth (speaking vowels) |
| **D** | E | Wide horizontal stretch |
| **E** | O | Rounded mouth |
| **F** | U, W, Q | Puckered lips |
| **G** | F, V | Upper teeth on lower lip |
| **H** | L, T, D | Barely parted lips |
| **X** | *(idle)* | Resting / closed mouth |

---

## Quick Start

### Install

```bash
# Clone
git clone https://github.com/historacle-ai/blabberer.git
cd blabberer

# Install (pick one)
uv pip install -e .
# or: pip install -e .
```

### Generate sprites

```bash
export OPENROUTER_API_KEY=sk-or-...   # https://openrouter.ai/keys

blabberer generate photo.jpg --output-dir ./sprites --verbose
```

**Output:**
```
sprites/
├── soft/              # Production-ready (transparent bg + soft edges)
│   ├── shape_A.webp
│   ├── shape_B.webp
│   ├── ...
│   └── shape_X.webp
├── shape_A.webp       # Transparent background (no soft edges)
├── ...
└── shape_X.webp
```

---

## CLI Reference

```
blabberer generate <image> [options]

Options:
  --api-key KEY          OpenRouter API key (or set OPENROUTER_API_KEY env var)
  --output-dir, -o DIR   Output directory (default: ./sprites)
  --crop-box L,T,R,B     Manual face crop box (auto-detects if omitted)
  --model MODEL          Gemini model (default: google/gemini-3.1-flash-image-preview)
  --workers N            Concurrent API calls (default: 3)
  --skip-postprocess     Skip background removal and soft edges
  --verbose, -v          Detailed output
```

## Python API

```python
from blabberer import generate_sprites, full_postprocess

# Generate sprites
results = generate_sprites(
    image_path="photo.jpg",
    output_dir="./sprites",
    api_key="sk-or-...",
)

# Post-process (background removal + soft edges)
final = full_postprocess("./sprites")
```

### Face Detection

```python
from blabberer import detect_face_crop
from PIL import Image

image = Image.open("photo.jpg")
crop_box = detect_face_crop(image)  # → (left, top, right, bottom)

# Custom expansion ratios
crop_box = detect_face_crop(
    image,
    expand_top=0.3,      # 30% above face
    expand_bottom=0.5,   # 50% below face
    expand_sides=0.25,   # 25% each side
)
```

---

## Interactive Demo

A browser demo lets you see lip sync in action — audio analysis drives mouth shapes in real time.

```bash
cd demo && npm install && npm run dev
# → http://localhost:5173
```

**Two modes:**

| Mode | Entry | What it does |
|------|-------|-------------|
| **Canvas** (default) | `simple.html` | Draws shapes on a `<canvas>` overlay — no sprites needed |
| **Sprite** | `index.html` | Dual-layer crossfade with generated sprite images |

### Lip Sync Algorithm

The `LipSyncEngine` uses a 3-tier energy model with text-informed shape selection:

1. **Audio analysis** — Web Audio `AnalyserNode` extracts frequency data (first 30 bins)
2. **Energy smoothing** — exponential moving average (rise=0.28, decay=0.18)
3. **Hysteresis state machine** — LOW / MID / HIGH with asymmetric thresholds to prevent flicker
4. **Text-to-shape mapping** — 28 letter + 12 digraph preferences per energy level
5. **Min hold time** — 100ms per shape prevents "chewing" artifacts
6. **Crossfade rendering** — two stacked `<img>` elements with 60ms CSS transitions

### Use the Engine in Your Project

The demo's `src/` files are standalone vanilla TypeScript — zero framework dependencies. Copy them into any project:

```typescript
import { AudioAnalyser } from './audioAnalyser';
import { LipSyncEngine } from './lipSync';

const audio = document.querySelector('audio')!;
const analyser = new AudioAnalyser();
const node = analyser.connect(audio);
const engine = new LipSyncEngine(node!);

engine.loadText('Hello world');
audio.play();

function animate() {
  requestAnimationFrame(animate);
  const shape = engine.update(performance.now());
  // shape: 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'X'
}
requestAnimationFrame(animate);
```

---

## Claude Code Plugin

Blabberer ships as a **Claude Code plugin** with a `/lip-sync-pipeline` skill that automates the entire workflow.

### Install

```
/plugin install historacle-ai/blabberer
```

### Run

```
/blabberer:lip-sync-pipeline photo.jpg
```

Claude handles face detection, sprite generation, post-processing, demo setup, and troubleshooting — end to end.

---

## Requirements

| Component | Requirement |
|-----------|-------------|
| Python | >= 3.10 |
| API key | [OpenRouter](https://openrouter.ai/keys) with Gemini model access |
| Disk | ~170 MB for rembg U2Net model (downloaded on first run) |
| Node.js | >= 18 (demo only) |

## Project Structure

```
blabberer/
├── blabberer/                # Python package
│   ├── cli.py                # CLI entry point
│   ├── generator.py          # Face detect → Gemini → sprites
│   ├── face_detect.py        # MediaPipe face detection
│   ├── shapes.py             # 9 Preston Blair shape definitions
│   ├── postprocess.py        # Background removal + soft edges
│   └── reference/            # 12 bundled reference images
├── demo/                     # Browser lip sync demo
│   ├── simple.html           # Canvas mode (default)
│   ├── index.html            # Sprite mode
│   └── src/                  # Vanilla TypeScript
│       ├── lipSync.ts        # Audio + text → shape engine
│       ├── audioAnalyser.ts  # Web Audio API bridge
│       ├── mouthRenderer.ts  # Dual-layer crossfade
│       ├── simple.ts         # Canvas demo
│       └── main.ts           # Sprite demo
├── skills/                   # Claude Code plugin
│   └── lip-sync-pipeline/
├── .claude-plugin/           # Plugin manifest
└── pyproject.toml
```

---

## Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## About HistOracle

<a href="https://historacle.ai">
  <img src="https://img.shields.io/badge/HistOracle-historacle.ai-ff6b35?style=for-the-badge" alt="HistOracle">
</a>

**Blabberer** was extracted from the production lip sync pipeline at [HistOracle](https://historacle.ai) — an AI platform that brings historical figures to life through interactive conversations. HistOracle uses AI-generated visemes, real-time audio analysis, and natural language understanding to create lifelike talking portraits of figures from history.

We open-sourced the lip sync sprite generation and animation engine so developers, educators, and creators can build their own talking-face experiences.

## License

MIT License — see [LICENSE](LICENSE).

Copyright (c) 2026 [Editlingo Solutions LLC](https://historacle.ai)
