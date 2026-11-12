#!/usr/bin/env python3
"""Privacy-preserving visual activity metrics for private BO3 Wine screenshots.

We never upload the screenshot, infer a menu from a process being alive, or
claim that a nonblack frame is gameplay. Produces numeric metrics only.
"""
import argparse
import json
from pathlib import Path

def analyze(folder):
    try:
        from PIL import Image
    except ImportError as e:
        raise RuntimeError("Pillow is required for screenshot metrics") from e
    root = Path(folder)
    results = []
    for filename in sorted(root.glob("shot-*.png"))[:16]:
        if not filename.is_file() or filename.is_symlink():
            continue
        with Image.open(filename) as im:
            original = im.size
            pixels = list(im.convert("RGB").resize((96, 54)).getdata())
        brightness = [(r * 299 + g * 587 + b * 114) // 1000 for r,g,b in pixels]
        visible = sum(1 for b in brightness if b > 24)
        results.append({
            "image": filename.name,
            "resolution": list(original),
            "nonblack_fraction": round(visible / len(pixels), 5),
            "average_luma": round(sum(brightness) / len(pixels), 2),
            "sampled_unique_colors": len(set(pixels)),
        })
    return {
        "screenshots_observed": len(results),
        "frames": results,
        "menu_render_verified": False,
        "note": "A nonblack screen could be a splash, dialog, loading screen, or error; no automatic menu claim.",
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(args.run_dir)
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        args.out.write_text(text)
    else:
        print(text, end="")

if __name__ == "__main__":
    main()
