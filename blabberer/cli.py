"""
Command-line interface for Blabberer.

Usage:
    blabberer generate <image_path> [options]
"""

import argparse
import sys

from dotenv import load_dotenv

from blabberer import __version__

load_dotenv()


def parse_crop_box(value: str) -> tuple[int, int, int, int]:
    """Parse 'left,top,right,bottom' string into a tuple."""
    try:
        parts = [int(x.strip()) for x in value.split(",")]
        if len(parts) != 4:
            raise ValueError
        return tuple(parts)  # type: ignore
    except (ValueError, TypeError):
        raise argparse.ArgumentTypeError(
            f"Invalid crop box: '{value}'. Expected format: left,top,right,bottom (e.g., 100,50,400,350)"
        )


def cmd_generate(args: argparse.Namespace) -> None:
    """Run the sprite generation pipeline."""
    from blabberer.generator import generate_sprites
    from blabberer.postprocess import full_postprocess

    results = generate_sprites(
        image_path=args.image,
        output_dir=args.output_dir,
        api_key=args.api_key,
        crop_box=args.crop_box,
        model=args.model,
        max_workers=args.workers,
        verbose=args.verbose,
    )

    if not args.skip_postprocess:
        final_sprites = full_postprocess(args.output_dir)
        if final_sprites:
            print(f"\nDone! {len(final_sprites)} production-ready sprites generated.")
            print(f"Use the sprites in {args.output_dir}/soft/ for your project.")
    else:
        print(f"\nDone! {len(results)} raw sprites saved to {args.output_dir}/")
        print("Run post-processing separately or use --skip-postprocess=false")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="blabberer",
        description="Generate lip sync mouth shape sprites from any face image using AI",
    )
    parser.add_argument(
        "--version", action="version", version=f"blabberer {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate command
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate mouth shape sprites from a face image",
    )
    gen_parser.add_argument(
        "image",
        help="Path to input image containing a face",
    )
    gen_parser.add_argument(
        "--api-key",
        default=None,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)",
    )
    gen_parser.add_argument(
        "--output-dir", "-o",
        default="./sprites",
        help="Output directory for sprites (default: ./sprites)",
    )
    gen_parser.add_argument(
        "--crop-box",
        type=parse_crop_box,
        default=None,
        help="Manual face crop: left,top,right,bottom (auto-detects if omitted)",
    )
    gen_parser.add_argument(
        "--model",
        default="google/gemini-3.1-flash-image-preview",
        help="Gemini model to use via OpenRouter",
    )
    gen_parser.add_argument(
        "--workers",
        type=int,
        default=3,
        help="Number of concurrent API calls (default: 3)",
    )
    gen_parser.add_argument(
        "--skip-postprocess",
        action="store_true",
        help="Skip background removal and soft-edge processing",
    )
    gen_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print detailed progress",
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    if args.command == "generate":
        cmd_generate(args)


if __name__ == "__main__":
    main()
