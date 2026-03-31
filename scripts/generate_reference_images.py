#!/usr/bin/env python3
"""
Generate proprietary Preston Blair phoneme mouth shape reference images
using Gemini 3.1 Flash via OpenRouter.

Produces 12 webp images — one per mouth shape in the Preston Blair phoneme set.
Uses the existing reference JPGs as style/content references in each API call
so Gemini matches the exact flat cartoon illustration style.

Usage:
    python scripts/generate_reference_images.py [--output-dir blabberer/reference]

Requires:
    pip install Pillow python-dotenv
"""

import argparse
import base64
import json
import os
import sys
import time
import urllib.request
import urllib.error
from io import BytesIO
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow package required. Install with: pip install Pillow")
    sys.exit(1)

# Load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-3.1-flash-image-preview"

# Path to existing reference images (used as style reference in API calls)
REFERENCE_DIR = Path(__file__).resolve().parent.parent / "blabberer" / "reference"

# All 12 Preston Blair phoneme mouth shapes.
# Each entry has:
#   - label: the phoneme text shown on the image
#   - ref_file: the existing reference JPG to send as style context
#   - prompt: detailed description for generation
MOUTH_SHAPES = {
    "BMP": {
        "label": "B, M, P",
        "ref_file": "BMP.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'B, M, P' phoneme position: "
            "Lips gently pressed together, completely sealed — no gap, no teeth visible. "
            "The lips have a natural slight curve with soft coral/salmon pink color. "
            "Above the upper lip, a small subtle nose philtrum indent. "
            "Jaw relaxed and closed — the 'mmm' sound. "
            "Text label 'B, M, P' below in clean brown sans-serif font."
        ),
    },
    "CDGKNSTXYZ": {
        "label": "C, D, G, K, N, S, T, X, Y, Z",
        "ref_file": "CDGKNSTXYZ.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the consonant phoneme position for 'C, D, G, K, N, S, T, X, Y, Z'. "
            "Lips slightly parted with upper and lower teeth close together and visible. "
            "Jaw barely open — teeth almost touching with a thin dark gap. "
            "Lips relaxed and neutral, coral/salmon pink, pulled back to show teeth. "
            "Small nasolabial fold curves on either side. "
            "Natural talking position, not a smile. "
            "Text 'C, D, G, K, N,' on first line and 'S, T, X, Y, Z' on second line below."
        ),
    },
    "AEI": {
        "label": "A, E, I",
        "ref_file": "AEI.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'A, E, I' phoneme position: "
            "Mouth open wide in a natural speaking position. "
            "Upper teeth fully visible as a white row along top. "
            "Lower teeth partially visible at bottom. "
            "Tongue visible and relaxed inside the dark mouth cavity. "
            "Lips coral/salmon pink, relaxed and open, slightly pulled at corners. "
            "Small nasolabial fold curves on either side. "
            "Text label 'A, E, I' below in clean brown sans-serif font."
        ),
    },
    "E": {
        "label": "E",
        "ref_file": "E.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'E' phoneme position: "
            "Lips stretched slightly horizontally with wide jaw opening. "
            "Mouth corners pull gently to the sides. "
            "Upper teeth visible at top, lower teeth at bottom. "
            "Tongue tip slightly visible at center bottom. "
            "Dark mouth cavity between the teeth rows. "
            "Lips coral/salmon pink, wider opening than consonant position. "
            "Small nasolabial fold curves on either side. "
            "Text label 'E' below in clean brown sans-serif font."
        ),
    },
    "O": {
        "label": "O",
        "ref_file": "O.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'O' phoneme position: "
            "Mouth open wide in a tall oval shape, jaw drops significantly. "
            "Upper teeth visible at the very top edge. "
            "Mouth cavity dark and tall/open. "
            "Lips coral/salmon pink, forming a large open oval. "
            "Small nose philtrum indent above upper lip. "
            "Text label 'O' below in clean brown sans-serif font."
        ),
    },
    "QW": {
        "label": "Q, W",
        "ref_file": "QW.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'Q, W' phoneme position: "
            "Lips pushed forward into a small, tight, very rounded opening. "
            "Lips protrude forming a small circular/oval pursed shape. "
            "Opening is a dark circle, much smaller than other shapes. "
            "Lips coral/salmon pink, distinctly rounded/puckered forward. "
            "Upper teeth barely visible at top edge of the small opening. "
            "Small nose philtrum indent above. "
            "Text label 'Q, W' below in clean brown sans-serif font."
        ),
    },
    "FV": {
        "label": "F, V",
        "ref_file": "FV.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'F, V' phoneme position: "
            "Upper front teeth gently resting on the lower lip. "
            "Upper lip lifts slightly to expose upper teeth as a white row. "
            "Lower lip tucks naturally under the upper front teeth. "
            "Narrow horizontal opening showing teeth biting lower lip. "
            "Lips coral/salmon pink. Minimal mouth opening. "
            "Text label 'F, V' below in clean brown sans-serif font."
        ),
    },
    "L": {
        "label": "L",
        "ref_file": "L.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'L' phoneme position: "
            "Mouth open moderately with tongue clearly visible and raised, "
            "touching toward the upper teeth/palate. "
            "Tongue tip points upward, prominent in center of mouth. "
            "Upper teeth visible at top, lower teeth at bottom. "
            "Dark mouth cavity on either side of the raised tongue. "
            "Lips coral/salmon pink, moderately open. "
            "Small nasolabial fold curves on either side. "
            "Text label 'L' below in clean brown sans-serif font."
        ),
    },
    "R": {
        "label": "R",
        "ref_file": "R.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'R' phoneme position: "
            "Lips slightly parted in a moderate horizontal opening. "
            "Upper teeth visible at top, lower teeth at bottom. "
            "Tongue slightly curled/bunched visible inside mouth cavity. "
            "Mouth opening wider horizontally than vertically. "
            "Lips coral/salmon pink. "
            "Small nasolabial fold curves on either side. "
            "Text label 'R' below in clean brown sans-serif font."
        ),
    },
    "TH": {
        "label": "TH",
        "ref_file": "TH.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'TH' phoneme position: "
            "Mouth moderately open with tongue protruding slightly between teeth. "
            "Tongue tip visible between upper and lower teeth, sticking forward. "
            "Upper teeth at top edge, lower teeth at bottom. "
            "Dark mouth cavity on either side of protruding tongue. "
            "Lips coral/salmon pink. "
            "Small nasolabial fold curves on either side. "
            "Text label 'TH' below in clean brown sans-serif font."
        ),
    },
    "U": {
        "label": "U",
        "ref_file": "U.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'U' phoneme position: "
            "Lips slightly parted in a narrow horizontal opening. "
            "Upper and lower teeth visible. "
            "Narrow dark gap between the teeth rows. "
            "Mouth only slightly open, more closed than E or consonant position. "
            "Lips coral/salmon pink. "
            "Small nasolabial fold curves on either side. "
            "Text label 'U' below in clean brown sans-serif font."
        ),
    },
    "CHJCH": {
        "label": "CH, J, SH",
        "ref_file": "CHJCH.jpg",
        "prompt": (
            "Recreate this exact mouth shape illustration in the same flat cartoon style. "
            "This shows the 'CH, J, SH' phoneme position: "
            "Lips slightly pushed forward and parted in a narrow horizontal slit. "
            "Upper and lower teeth visible as thin white rows with a narrow gap. "
            "Mouth opening narrow and slightly rounded/pushed forward. "
            "Lips coral/salmon pink, slightly protruding. "
            "Small nasolabial fold curves on either side. "
            "Text label 'CH, J, SH' below in clean brown sans-serif font."
        ),
    },
}

# Shared style instructions prepended to every prompt
STYLE_PREFIX = (
    "I am showing you a reference cartoon illustration of a mouth shape. "
    "Generate a NEW illustration that matches the EXACT same mouth position, style, "
    "and layout, but is a completely original drawing — not a copy of the reference. "
    "Requirements for the new illustration:\n"
    "- Clean, flat, vector-style cartoon of ONLY a human mouth and surrounding skin area\n"
    "- Solid uniform peach/light salmon skin-toned background (hex ~#F5C5A3)\n"
    "- Show ONLY the mouth area — no eyes, no full face\n"
    "- Flat style with minimal shading, clean outlines, educational anatomy diagram look\n"
    "- Teeth: white/light blue-white. Mouth interior: dark gray/black\n"
    "- Tongue (if visible): darker pinkish-red\n"
    "- Square image, approximately 400x400 pixels\n"
    "- NO watermark, NO logo, NO copyright text\n"
    "- NOT photorealistic — clean flat cartoon illustration\n"
    "- Must include the phoneme text label below the mouth\n\n"
)


def load_reference_image(ref_file: str) -> str | None:
    """Load a reference image and return as base64 data URI."""
    ref_path = REFERENCE_DIR / ref_file
    if not ref_path.exists():
        print(f"  WARNING: Reference image not found: {ref_path}")
        return None
    with open(ref_path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def call_openrouter(
    prompt: str,
    ref_data_uri: str | None,
    api_key: str,
    shape_name: str,
) -> bytes | None:
    """Send reference image + prompt to Gemini via OpenRouter, return generated image bytes."""
    content = []

    # Include reference image first
    if ref_data_uri:
        content.append({
            "type": "image_url",
            "image_url": {"url": ref_data_uri},
        })

    content.append({"type": "text", "text": prompt})

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": content},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/historacle-ai/blabberer",
        "X-Title": "Blabberer Reference Image Generator",
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  [{shape_name}] HTTP {e.code}: {body[:300]}")
        return None
    except Exception as e:
        print(f"  [{shape_name}] Request failed: {e}")
        return None

    choices = result.get("choices", [])
    if not choices:
        print(f"  [{shape_name}] No choices in response")
        return None

    message = choices[0].get("message", {})

    # Try images array format
    images = message.get("images")
    if images and isinstance(images, list) and len(images) > 0:
        img = images[0]
        if isinstance(img, dict):
            image_url = img.get("image_url", {})
            if isinstance(image_url, dict):
                url = image_url.get("url", "")
                if url.startswith("data:") and "," in url:
                    return base64.b64decode(url.split(",", 1)[1])

    # Try inline_data in content parts
    content_parts = message.get("content")
    if isinstance(content_parts, list):
        for part in content_parts:
            if isinstance(part, dict):
                # inline_data format
                inline = part.get("inline_data", {})
                if inline.get("data"):
                    return base64.b64decode(inline["data"])
                # image_url format in content parts
                img_url = part.get("image_url", {})
                if isinstance(img_url, dict):
                    url = img_url.get("url", "")
                    if url.startswith("data:") and "," in url:
                        return base64.b64decode(url.split(",", 1)[1])

    # Log text response
    if content_parts and isinstance(content_parts, str):
        print(f"  [{shape_name}] Text only: {content_parts[:200]}")
    elif isinstance(content_parts, list):
        for part in content_parts:
            if isinstance(part, dict) and part.get("type") == "text":
                print(f"  [{shape_name}] Text: {part.get('text', '')[:200]}")
    else:
        print(f"  [{shape_name}] Unexpected response: {json.dumps(message)[:300]}")

    return None


def generate_single_shape(
    shape_name: str,
    shape_def: dict,
    output_dir: Path,
    api_key: str,
    verbose: bool = False,
    max_retries: int = 3,
) -> bool:
    """Generate a single mouth shape reference image."""
    full_prompt = STYLE_PREFIX + shape_def["prompt"]
    output_path = output_dir / f"{shape_name}.webp"

    # Load existing reference image for style context
    ref_data_uri = load_reference_image(shape_def["ref_file"])
    if not ref_data_uri and verbose:
        print(f"  [{shape_name}] No reference image — generating from description only")

    for attempt in range(1, max_retries + 1):
        if verbose:
            print(f"  [{shape_name}] Attempt {attempt}/{max_retries}...")

        image_bytes = call_openrouter(full_prompt, ref_data_uri, api_key, shape_name)

        if image_bytes:
            try:
                image = Image.open(BytesIO(image_bytes))
                if image.mode in ("RGBA", "P"):
                    image = image.convert("RGB")
                image.save(output_path, "WEBP", quality=90)
                size_kb = output_path.stat().st_size / 1024
                print(f"  {shape_name}: OK ({image.size[0]}x{image.size[1]}, {size_kb:.1f}KB)")
                return True
            except Exception as e:
                print(f"  [{shape_name}] Image decode error: {e}")

        if attempt < max_retries:
            wait = 3 * attempt
            if verbose:
                print(f"  [{shape_name}] Retrying in {wait}s...")
            time.sleep(wait)

    print(f"  {shape_name}: FAILED after {max_retries} attempts")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate Preston Blair phoneme mouth shape reference images using Gemini via OpenRouter."
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory for generated webp images (default: blabberer/reference)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var / .env file)",
    )
    parser.add_argument(
        "--shapes",
        nargs="*",
        default=None,
        help="Generate only specific shapes (e.g., --shapes BMP O QW). Default: all 12.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Max retries per shape on failure (default: 3)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    args = parser.parse_args()

    # Resolve API key
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required.")
        print("Set OPENROUTER_API_KEY env var, add to .env, or pass --api-key")
        print("Get a key at: https://openrouter.ai/keys")
        sys.exit(1)

    # Determine which shapes to generate
    if args.shapes:
        shapes_to_gen = {}
        for name in args.shapes:
            name_upper = name.upper()
            if name_upper in MOUTH_SHAPES:
                shapes_to_gen[name_upper] = MOUTH_SHAPES[name_upper]
            else:
                print(f"Warning: Unknown shape '{name}'. Available: {', '.join(MOUTH_SHAPES.keys())}")
        if not shapes_to_gen:
            print("No valid shapes specified.")
            sys.exit(1)
    else:
        shapes_to_gen = MOUTH_SHAPES

    # Output directory
    output_dir = Path(args.output_dir) if args.output_dir else REFERENCE_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {len(shapes_to_gen)} Preston Blair mouth shape reference images")
    print(f"Model: {MODEL}")
    print(f"Reference dir: {REFERENCE_DIR}")
    print(f"Output: {output_dir}/")
    print(f"Format: WebP (quality=90)")
    print()

    succeeded = 0
    failed = 0

    for shape_name, shape_def in shapes_to_gen.items():
        ok = generate_single_shape(
            shape_name=shape_name,
            shape_def=shape_def,
            output_dir=output_dir,
            api_key=api_key,
            verbose=args.verbose,
            max_retries=args.max_retries,
        )
        if ok:
            succeeded += 1
        else:
            failed += 1

        # Delay between shapes to respect rate limits
        time.sleep(1)

    # Clean up old JPG files for successfully generated shapes
    if succeeded > 0 and output_dir == REFERENCE_DIR:
        print("\nCleaning up old JPG reference files...")
        for shape_name, shape_def in shapes_to_gen.items():
            webp_path = output_dir / f"{shape_name}.webp"
            old_jpg = output_dir / shape_def["ref_file"]
            if webp_path.exists() and old_jpg.exists() and old_jpg.suffix == ".jpg":
                old_jpg.unlink()
                print(f"  Deleted {old_jpg.name}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Done: {succeeded} succeeded, {failed} failed out of {len(shapes_to_gen)}")
    if failed:
        print("Re-run with --shapes <name> to retry specific shapes.")
    print(f"Output: {output_dir}/")


if __name__ == "__main__":
    main()
