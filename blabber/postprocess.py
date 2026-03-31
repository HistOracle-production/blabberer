"""
Post-processing for generated sprites.

1. Background removal using rembg (U2Net AI model)
2. Soft-edge feathering for seamless compositing
"""

import os
import time
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


# Feathering parameters
DEFAULT_ERODE_KERNEL = 7   # MinFilter size — shrinks opaque area by ~3px per side
DEFAULT_BLUR_RADIUS = 10   # GaussianBlur radius for the falloff gradient


def _feather_alpha(
    img: Image.Image,
    erode_kernel: int = DEFAULT_ERODE_KERNEL,
    blur_radius: int = DEFAULT_BLUR_RADIUS,
) -> Image.Image:
    """Apply a soft feathered edge to an RGBA image's alpha channel."""
    img = img.convert("RGBA")
    r, g, b, a = img.split()

    # Erode the alpha mask (shrink opaque region inward)
    eroded = a.filter(ImageFilter.MinFilter(erode_kernel))

    # Blur the eroded mask to create a smooth gradient at edges
    blurred = eroded.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Pixel-wise minimum: min(original_alpha, feathered_alpha)
    # Preserves internal transparency while softening outer edges
    result_alpha = ImageChops.darker(a, blurred)

    img.putalpha(result_alpha)
    return img


def remove_backgrounds(
    input_dir: str,
    output_format: str = "webp",
    quality: int = 90,
) -> list[Path]:
    """
    Remove backgrounds from all shape PNG sprites using rembg.

    Args:
        input_dir: Directory containing shape_*.png files.
        output_format: Output format (webp or png).
        quality: Output quality for webp (1-100).

    Returns:
        List of output file paths.
    """
    from rembg import remove

    input_path = Path(input_dir)
    png_files = sorted(input_path.glob("shape_*.png"))

    if not png_files:
        print(f"No shape_*.png files found in {input_dir}")
        return []

    print(f"Removing backgrounds from {len(png_files)} sprites...")
    outputs = []

    for png_file in png_files:
        out_name = png_file.stem + f".{output_format}"
        out_path = input_path / out_name

        img = Image.open(png_file)
        result = remove(img)

        if output_format == "webp":
            result.save(out_path, "WEBP", quality=quality)
        else:
            result.save(out_path, "PNG")

        outputs.append(out_path)
        print(f"  {out_name}: {out_path.stat().st_size:,} bytes")

    print(f"Background removal complete: {len(outputs)} files")
    return outputs


def apply_soft_edges(
    input_dir: str,
    output_dir: str | None = None,
    erode_kernel: int = DEFAULT_ERODE_KERNEL,
    blur_radius: int = DEFAULT_BLUR_RADIUS,
    quality: int = 90,
) -> list[Path]:
    """
    Apply feathered alpha edges to sprite images for seamless compositing.

    Args:
        input_dir: Directory containing shape_*.webp files.
        output_dir: Output directory (default: input_dir/soft/).
        erode_kernel: MinFilter kernel size for edge erosion.
        blur_radius: GaussianBlur radius for edge gradient.
        quality: Output webp quality.

    Returns:
        List of output file paths.
    """
    input_path = Path(input_dir)
    out_path = Path(output_dir) if output_dir else input_path / "soft"
    out_path.mkdir(parents=True, exist_ok=True)

    sprite_files = sorted(input_path.glob("shape_*.webp"))
    if not sprite_files:
        print(f"No shape_*.webp files found in {input_dir}")
        return []

    print(f"Applying soft edges (erode={erode_kernel}, blur={blur_radius})...")
    outputs = []
    start = time.time()

    for sprite_file in sprite_files:
        out_file = out_path / sprite_file.name

        img = Image.open(sprite_file).convert("RGBA")
        result = _feather_alpha(img, erode_kernel, blur_radius)
        result.save(out_file, "WEBP", quality=quality, method=6)

        size_in = sprite_file.stat().st_size
        size_out = out_file.stat().st_size
        outputs.append(out_file)
        print(f"  {sprite_file.name:30s}  {img.size[0]}x{img.size[1]}  "
              f"{size_in // 1024:>4d}KB -> {size_out // 1024:>4d}KB")

    elapsed = time.time() - start
    print(f"Soft edges complete: {len(outputs)} sprites in {elapsed:.1f}s")
    print(f"Output: {out_path}")
    return outputs


def full_postprocess(
    input_dir: str,
    output_dir: str | None = None,
    erode_kernel: int = DEFAULT_ERODE_KERNEL,
    blur_radius: int = DEFAULT_BLUR_RADIUS,
) -> list[Path]:
    """
    Run full post-processing pipeline: background removal → soft edges.

    Args:
        input_dir: Directory containing shape_*.png files from generation.
        output_dir: Final output directory (default: input_dir/soft/).

    Returns:
        List of final soft-edge sprite file paths.
    """
    print("\n--- Post-processing ---\n")

    # Step 1: Remove backgrounds (PNG → WebP with transparent bg)
    remove_backgrounds(input_dir, output_format="webp")

    # Step 2: Apply soft edges (WebP → soft/WebP with feathered alpha)
    return apply_soft_edges(
        input_dir,
        output_dir=output_dir,
        erode_kernel=erode_kernel,
        blur_radius=blur_radius,
    )
