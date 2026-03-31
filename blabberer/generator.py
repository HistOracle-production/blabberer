"""
Core sprite generation engine.

Takes a face image, auto-detects (or uses manual) crop box, and generates
9 Preston Blair mouth shape sprites via Gemini (OpenRouter API).
"""

import base64
import json
import os
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from importlib.resources import files
from io import BytesIO
from pathlib import Path

from PIL import Image

from blabberer.face_detect import detect_face_crop
from blabberer.shapes import SHAPE_DEFS, PROMPT_TEMPLATE

DEFAULT_MODEL = "google/gemini-3.1-flash-image-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _get_reference_dir() -> Path:
    """Get path to bundled reference images."""
    return Path(str(files("blabberer"))) / "reference"


def _load_reference_image(ref_dir: Path, filename: str) -> bytes | None:
    """Load a reference image from the reference directory."""
    path = ref_dir / filename
    if not path.exists():
        print(f"  WARNING: Reference image not found: {path}")
        return None
    img = Image.open(path)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _pil_to_png_bytes(img: Image.Image) -> bytes:
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _call_openrouter(
    prompt: str,
    face_bytes: bytes,
    ref_bytes: bytes | None,
    shape_name: str,
    api_key: str,
    model: str,
) -> tuple[str, bytes | None]:
    """Send face crop + reference image to Gemini via OpenRouter."""
    face_b64 = base64.b64encode(face_bytes).decode("utf-8")

    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{face_b64}"}},
    ]

    if ref_bytes:
        ref_b64 = base64.b64encode(ref_bytes).decode("utf-8")
        content.append({"type": "image_url", "image_url": {"url": f"data:image/png;base64,{ref_b64}"}})

    content.append({"type": "text", "text": prompt})

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/historacle-ai/blabberer",
        "X-Title": "Blabberer Lip-Sync Sprite Generator",
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(OPENROUTER_URL, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [{shape_name}] Request failed: {e}")
        return shape_name, None

    choices = result.get("choices", [])
    if not choices:
        print(f"  [{shape_name}] No choices in response")
        return shape_name, None

    message = choices[0].get("message", {})

    # Try images array (Gemini image generation format)
    images = message.get("images")
    if images and isinstance(images, list) and len(images) > 0:
        img = images[0]
        if isinstance(img, dict):
            image_url = img.get("image_url", {})
            if isinstance(image_url, dict):
                url = image_url.get("url", "")
                if url.startswith("data:") and "," in url:
                    return shape_name, base64.b64decode(url.split(",", 1)[1])

    # Try inline_data in content parts
    content_parts = message.get("content")
    if isinstance(content_parts, list):
        for part in content_parts:
            if isinstance(part, dict):
                inline = part.get("inline_data", {})
                if inline.get("data"):
                    return shape_name, base64.b64decode(inline["data"])

    if content_parts and isinstance(content_parts, str):
        print(f"  [{shape_name}] Text response (no image): {content_parts[:100]}")
    else:
        print(f"  [{shape_name}] No image in response")
    return shape_name, None


def generate_sprites(
    image_path: str,
    output_dir: str = "./sprites",
    api_key: str | None = None,
    crop_box: tuple[int, int, int, int] | None = None,
    model: str = DEFAULT_MODEL,
    max_workers: int = 3,
    max_retries: int = 3,
    verbose: bool = False,
) -> dict[str, Path]:
    """
    Generate 9 mouth shape sprites from a face image.

    Args:
        image_path: Path to input image containing a face.
        output_dir: Directory to save generated sprites.
        api_key: OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
        crop_box: Manual (left, top, right, bottom) crop. Auto-detects if None.
        model: Gemini model to use via OpenRouter.
        max_workers: Concurrent API calls (default 3).
        max_retries: Max retries per shape on failure.
        verbose: Print detailed progress.

    Returns:
        Dict mapping shape names to output file paths.
    """
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise ValueError(
            "API key required. Pass --api-key or set OPENROUTER_API_KEY env var. "
            "Get one at https://openrouter.ai/keys"
        )

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load image
    image = Image.open(image_path)
    img_w, img_h = image.size
    print(f"Input image: {img_w}x{img_h}")

    # Face detection or manual crop
    if crop_box is None:
        print("Detecting face...")
        crop_box = detect_face_crop(image)
        print(f"Face detected: crop box = {crop_box}")
    else:
        print(f"Using manual crop box: {crop_box}")

    face_crop = image.crop(crop_box)
    crop_w, crop_h = face_crop.size
    print(f"Face crop: {crop_w}x{crop_h}")

    # Save shape_X (idle pose — pixel-perfect from original crop)
    x_path = output_path / "shape_X.webp"
    face_crop.save(x_path, "WEBP", quality=95)
    print(f"shape_X: saved (idle pose from original crop)")

    face_crop_bytes = _pil_to_png_bytes(face_crop)

    # Load reference images
    ref_dir = _get_reference_dir()
    if verbose:
        print(f"\nReference images: {ref_dir}")

    ref_images = {}
    for name, shape_def in SHAPE_DEFS.items():
        ref_file = shape_def["reference_file"]
        ref_bytes = _load_reference_image(ref_dir, ref_file)
        ref_images[name] = ref_bytes
        if verbose:
            status = f"{len(ref_bytes):,} bytes" if ref_bytes else "NOT FOUND"
            print(f"  {name} -> {ref_file} ({status})")

    # Generate shapes concurrently
    print(f"\nGenerating {len(SHAPE_DEFS)} shapes ({max_workers} concurrent)...\n")

    results: dict[str, Path] = {"shape_X": x_path}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for name, shape_def in SHAPE_DEFS.items():
            prompt = PROMPT_TEMPLATE.format(
                phonemes=shape_def["phonemes"],
                anatomical_desc=shape_def["anatomical_desc"],
            )
            ref_bytes = ref_images.get(name)
            future = executor.submit(
                _call_openrouter, prompt, face_crop_bytes, ref_bytes, name, api_key, model
            )
            futures[future] = name

        for future in as_completed(futures):
            name, result_bytes = future.result()
            if result_bytes:
                result_img = Image.open(BytesIO(result_bytes))
                if result_img.size != (crop_w, crop_h):
                    if verbose:
                        print(f"  {name}: resize {result_img.size} -> {crop_w}x{crop_h}")
                    result_img = result_img.resize((crop_w, crop_h), Image.LANCZOS)

                filepath = output_path / f"{name}.webp"
                result_img.save(filepath, "WEBP", quality=95)
                results[name] = filepath
                print(f"  {name}: OK ({filepath.stat().st_size:,} bytes)")
            else:
                print(f"  {name}: FAILED")

    # Retry failed shapes
    expected = set(f"shape_{c}" for c in "ABCDEFGHX")
    missing = expected - set(results.keys())

    for attempt in range(1, max_retries):
        if not missing:
            break
        print(f"\nRetrying {len(missing)} failed shapes (attempt {attempt + 1}/{max_retries})...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for name in missing:
                if name == "shape_X":
                    continue
                shape_def = SHAPE_DEFS[name]
                prompt = PROMPT_TEMPLATE.format(
                    phonemes=shape_def["phonemes"],
                    anatomical_desc=shape_def["anatomical_desc"],
                )
                ref_bytes = ref_images.get(name)
                future = executor.submit(
                    _call_openrouter, prompt, face_crop_bytes, ref_bytes, name, api_key, model
                )
                futures[future] = name

            for future in as_completed(futures):
                name, result_bytes = future.result()
                if result_bytes:
                    result_img = Image.open(BytesIO(result_bytes))
                    if result_img.size != (crop_w, crop_h):
                        result_img = result_img.resize((crop_w, crop_h), Image.LANCZOS)
                    filepath = output_path / f"{name}.webp"
                    result_img.save(filepath, "WEBP", quality=95)
                    results[name] = filepath
                    print(f"  {name}: OK (retry)")

        missing = expected - set(results.keys())

    # Save config for demo overlay positioning
    config = {
        "image_path": str(image_path),
        "image_width": img_w,
        "image_height": img_h,
        "crop_box": list(crop_box),
        "face_region": {
            "x": round(crop_box[0] / img_w, 4),
            "y": round(crop_box[1] / img_h, 4),
            "width": round((crop_box[2] - crop_box[0]) / img_w, 4),
            "height": round((crop_box[3] - crop_box[1]) / img_h, 4),
        },
    }
    config_path = output_path / "blabberer_config.json"
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\nConfig saved: {config_path}")
    print(f"Face region (normalized): x={config['face_region']['x']}, y={config['face_region']['y']}, "
          f"w={config['face_region']['width']}, h={config['face_region']['height']}")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Generated {len(results)}/{len(expected)} sprites in {output_path}/")
    if missing:
        print(f"Missing: {', '.join(sorted(missing))}")
        print("Re-run to retry failed shapes.")

    return results
