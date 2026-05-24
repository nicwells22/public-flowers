#!/usr/bin/env python3
"""Convert HEIC image files to JPG files.

Usage:
    python convert_heic_to_jpg.py [path ...]

If no path is provided, the script converts all .heic/.HEIC files in the current directory.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

try:
    from PIL import Image
except ImportError as exc:
    raise ImportError(
        "Pillow is required. Install with: pip install pillow" 
        "\nFor HEIC support, also install pillow-heif or pyheif."
    ) from exc


def open_heic(path: Path) -> Image.Image:
    """Open a HEIC file and return a Pillow Image."""
    try:
        import pillow_heif

        pillow_heif.register_heif_opener()
        return Image.open(path)
    except ImportError:
        try:
            import pyheif
        except ImportError as exc:
            raise ImportError(
                "HEIC support requires pillow-heif or pyheif. "
                "Install one of them with: pip install pillow-heif or pip install pyheif"
            ) from exc

        heif_file = pyheif.read(path)
        return Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw",
            heif_file.mode,
            heif_file.stride,
        )


def convert_file(path: Path, out_dir: Path | None = None, overwrite: bool = False) -> Path:
    """Convert a single HEIC file to JPG."""
    out_dir = out_dir or path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    output_path = out_dir / f"{path.stem}.jpg"
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Output file already exists: {output_path}")

    image = open_heic(path)
    rgb_image = image.convert("RGB")
    rgb_image.save(output_path, format="JPEG", quality=95)
    return output_path


def find_heic_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_dir():
            files.extend(sorted(path.glob("*.HEIC")))
            files.extend(sorted(path.glob("*.heic")))
        elif path.is_file() and path.suffix.lower() == ".heic":
            files.append(path)
        else:
            raise FileNotFoundError(f"No HEIC file or directory found at: {path}")
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert HEIC images to JPG.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=[Path.cwd()],
        type=Path,
        help="Files or directories to convert. Defaults to current directory.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Directory to write JPG files into.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing JPG files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        heic_files = find_heic_files(args.paths)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not heic_files:
        print("No HEIC files found.")
        return 0

    converted = 0
    for heic_path in heic_files:
        try:
            output_path = convert_file(heic_path, out_dir=args.output_dir, overwrite=args.overwrite)
            print(f"Converted: {heic_path} -> {output_path}")
            converted += 1
        except Exception as exc:
            print(f"Failed: {heic_path} ({exc})", file=sys.stderr)

    print(f"Done. Converted {converted} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
