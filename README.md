# Blabber

Generate lip sync mouth shape sprites from any face image using AI.

Feed in a portrait photo, get back 9 production-ready mouth shape sprites based on the [Preston Blair phoneme system](https://en.wikipedia.org/wiki/Preston_Blair) — ready for real-time lip sync animation.

## How It Works

```
Input Image → Face Detection → Gemini AI → 9 Mouth Shapes → Post-Processing → Sprites
  (any face)   (MediaPipe)    (OpenRouter)  (Preston Blair)   (rembg + soft edges)
```

**The 9 shapes:**

| Shape | Phonemes | Description |
|-------|----------|-------------|
| A | M, B, P | Lips pressed together |
| B | S, T, D, K, N | Teeth visible, slightly open |
| C | A, I | Open mouth (speaking vowels) |
| D | E | Wide horizontal stretch |
| E | O | Rounded mouth |
| F | U, W, Q | Puckered lips |
| G | F, V | Upper teeth on lower lip |
| H | L, T, D | Barely parted lips |
| X | (idle) | Resting/closed mouth |

## Quick Start

### Option 1: Clone and run

```bash
git clone https://github.com/historacle-ai/blabber.git
cd blabber

# Install the Python package
pip install -e .
# OR
uv pip install -e .

# Set your API key
export OPENROUTER_API_KEY=sk-or-...   # Get one at https://openrouter.ai/keys

# Generate sprites from any face image
blabber generate photo.jpg --output-dir ./sprites --verbose
```

### Option 2: Install from PyPI

```bash
pip install blabber
# OR
uv pip install blabber

export OPENROUTER_API_KEY=sk-or-...
blabber generate photo.jpg
```

**Output:**
```
sprites/
├── soft/              # Production-ready (transparent bg + soft edges)
│   ├── shape_A.webp
│   ├── shape_B.webp
│   ├── ...
│   ├── shape_H.webp
│   └── shape_X.webp
├── shape_A.webp       # Transparent background (no soft edges)
├── ...
└── shape_X.webp
```

## Claude Code Skill (Plugin)

Blabber ships as a **Claude Code plugin** with a `/lip-sync-pipeline` skill that guides you through the entire sprite generation workflow.

### Install the skill

In any Claude Code session:

```
/plugin install historacle-ai/blabber
```

### Use the skill

```
/blabber:lip-sync-pipeline photo.jpg
```

This gives Claude the full pipeline context — face detection, sprite generation, post-processing, demo setup, troubleshooting — so it can walk you through the process or run it autonomously.

### What the skill covers

- Auto face detection (MediaPipe) or manual crop box
- 9 mouth shape generation via Gemini (OpenRouter)
- Background removal (rembg/U2Net) + soft-edge feathering
- Browser demo setup with real-time audio-driven lip sync
- Placement config for overlaying sprites on any image
- Troubleshooting common issues

## Interactive Demo

A browser-based demo lets you see lip sync in action:

```bash
cd demo
npm install
npm run dev
```

Opens http://localhost:5173 with two demo modes:

### Canvas mode (default — `simple.html`)

Draws mouth shapes directly on a canvas overlay. Works immediately — no generated sprites needed. Great for testing.

### Sprite mode (`index.html`)

Uses actual generated sprite images with smooth crossfade animation. Load your sprites + audio file via file inputs for production-quality results.

The demo uses the Web Audio API to analyze audio energy in real-time and maps it to mouth shapes using a hybrid approach:
- **Audio energy** drives mouth openness (rhythm)
- **Text phonemes** drive shape selection (variety)
- **Hysteresis** prevents flickering at energy boundaries
- **60ms crossfade** between shapes for smooth animation

## CLI Reference

```
blabber generate <image> [options]

Options:
  --api-key KEY          OpenRouter API key (or OPENROUTER_API_KEY env var)
  --output-dir, -o DIR   Output directory (default: ./sprites)
  --crop-box L,T,R,B    Manual face crop (auto-detects if omitted)
  --model MODEL          Gemini model (default: google/gemini-3.1-flash-image-preview)
  --workers N            Concurrent API calls (default: 3)
  --skip-postprocess     Skip background removal and soft edges
  --verbose, -v          Detailed output
```

## Python API

```python
from blabber import generate_sprites, full_postprocess

# Generate sprites
results = generate_sprites(
    image_path="photo.jpg",
    output_dir="./sprites",
    api_key="sk-or-...",
)

# Post-process (background removal + soft edges)
final = full_postprocess("./sprites")
```

### Auto Face Detection

```python
from blabber import detect_face_crop
from PIL import Image

image = Image.open("photo.jpg")
crop_box = detect_face_crop(image)  # (left, top, right, bottom)

# With custom expansion ratios
crop_box = detect_face_crop(
    image,
    expand_top=0.3,      # 30% above face
    expand_bottom=0.5,   # 50% below face
    expand_sides=0.25,   # 25% each side
)
```

## Using the JS/TS Lip Sync Engine in Your Project

The demo's `src/` files are standalone vanilla TypeScript with zero framework dependencies. Copy them into any project:

- **`lipSync.ts`** — `LipSyncEngine` class: text + audio → mouth shape selection
- **`audioAnalyser.ts`** — `AudioAnalyser` class: Web Audio API bridge
- **`mouthRenderer.ts`** — `MouthRenderer` class: dual-layer image crossfade

### Minimal integration

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
  // shape is 'A' | 'B' | 'C' | 'D' | 'E' | 'F' | 'G' | 'H' | 'X'
  // Use it to swap images, draw on canvas, or drive any animation
}
requestAnimationFrame(animate);
```

## How the Lip Sync Algorithm Works

The `LipSyncEngine` uses a 3-tier energy model with text-informed shape selection:

1. **Audio Analysis**: Web Audio API `AnalyserNode` extracts frequency data (first 30 bins)
2. **Energy Smoothing**: Exponential moving average (rise=0.28, decay=0.18) prevents jitter
3. **Hysteresis State Machine**: Three levels (LOW/MID/HIGH) with asymmetric thresholds prevent flickering
4. **Text-to-Shape Mapping**: 28 letter preferences + 12 digraph preferences map text to shape preferences per energy level
5. **Min Hold Time**: 100ms minimum per shape prevents "chewing" artifacts
6. **Crossfade Rendering**: Two stacked images alternate opacity with 60ms CSS transitions

## Requirements

- Python >= 3.10
- An [OpenRouter API key](https://openrouter.ai/keys) with access to Gemini models
- ~170MB disk space for the rembg U2Net model (downloaded on first run)
- Node.js >= 18 (for the demo only)

## Project Structure

```
blabber/
├── blabber/                  # Python package
│   ├── cli.py                # CLI: blabber generate <image>
│   ├── generator.py          # Core: face detect → Gemini → sprites
│   ├── face_detect.py        # MediaPipe auto face detection
│   ├── shapes.py             # 9 Preston Blair shape definitions
│   ├── postprocess.py        # Background removal + soft edges
│   └── reference/            # 12 bundled cartoon reference images
├── demo/                     # Browser-based lip sync demo
│   ├── simple.html           # Canvas-drawn mouth shapes (default)
│   ├── index.html            # Sprite-based with file inputs
│   └── src/                  # Vanilla TypeScript
│       ├── lipSync.ts        # LipSyncEngine (audio+text → shape)
│       ├── audioAnalyser.ts  # Web Audio API bridge
│       ├── mouthRenderer.ts  # Dual-layer crossfade renderer
│       ├── simple.ts         # Canvas demo logic
│       └── main.ts           # Sprite demo logic
├── skills/                   # Claude Code plugin skills
│   └── lip-sync-pipeline/    # /blabber:lip-sync-pipeline
├── .claude-plugin/           # Plugin manifest
│   └── plugin.json
├── pyproject.toml            # pip/uv installable
└── README.md
```

## License

MIT License — see [LICENSE](LICENSE).

Built with care by the [HistOracle](https://historacle.ai) team.
