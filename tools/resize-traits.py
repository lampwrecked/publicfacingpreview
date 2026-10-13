#!/usr/bin/env python3
"""
Make web-sized copies of the trait PNGs for the preview page.

The preview window is at most 560px wide (~1120px on a 2x screen), so
serving the full-resolution composite layers wastes most of every byte.
This script writes a parallel folder tree of WebP files at a fixed width,
keeping transparency, ready to upload to R2 under a "web/" prefix.

Usage:
    pip install pillow
    python3 tools/resize-traits.py /path/to/traits-local /path/to/out --width 1200

Input layout (same as the bucket):   Base/<name>.png, Ghost 1/<name>.png, ...
Output layout:                       Base/<name>.webp, Ghost 1/<name>.webp, ...

Then upload the output folder to the bucket under web/ (e.g. with rclone:
    rclone copy ./out r2:<bucket>/web --header-upload "Cache-Control: public, max-age=31536000, immutable"
) and in index.html set:
    const BASE = "https://pub-....r2.dev/web/";
    const EXT  = "webp";
"""
import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow is required: pip install pillow")

LAYER_FOLDERS = ["Base", "Ghost 1", "Ghost 2", "Head", "Mouth", "Right Eye", "Nose", "Left Eye"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", type=Path, help="folder with the per-layer trait folders")
    ap.add_argument("out", type=Path, help="where to write the resized tree")
    ap.add_argument("--width", type=int, default=1200, help="output width in px (default 1200)")
    ap.add_argument("--quality", type=int, default=82, help="WebP quality 0-100 (default 82)")
    args = ap.parse_args()

    total_in = total_out = count = 0
    for folder in LAYER_FOLDERS:
        src_dir = args.src / folder
        if not src_dir.is_dir():
            print(f"skip {folder}: not found")
            continue
        out_dir = args.out / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        for png in sorted(src_dir.glob("*.png")):
            with Image.open(png) as im:
                im = im.convert("RGBA")
                if im.width > args.width:
                    h = round(im.height * args.width / im.width)
                    im = im.resize((args.width, h), Image.LANCZOS)
                dst = out_dir / (png.stem + ".webp")
                im.save(dst, "WEBP", quality=args.quality, method=6)
            total_in += png.stat().st_size
            total_out += dst.stat().st_size
            count += 1
        print(f"{folder}: done")

    if count:
        print(f"\n{count} files: {total_in/1e6:.1f} MB -> {total_out/1e6:.1f} MB "
              f"({100*(1-total_out/total_in):.0f}% smaller)")


if __name__ == "__main__":
    main()
