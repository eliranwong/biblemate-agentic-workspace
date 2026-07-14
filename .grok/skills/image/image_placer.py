#!/usr/bin/env python3
"""Place a Grok Build–generated image into the repo images/ directory.

Usage:
  python3 image_placer.py <source_image_path> [prompt_or_title]

Copies (and converts to PNG when possible) the source file into:

  images/YYYY-MM-DD-HH-MM-SS_<slug>.png

No network calls. No Antigravity / external image APIs — generation is done by
Grok Build's image_gen / image_edit tools; this script only renames and stores.
"""
from __future__ import annotations

import datetime
import logging
import os
import re
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
IMAGES_DIR = os.path.join(REPO_ROOT, "images")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("image_placer")


def slugify(text: str) -> str:
    text = re.sub(r"^/[a-zA-Z0-9_-]+\s*", "", text)
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = text.strip("_")
    words = text.split("_")[:4]
    slug = "_".join(words)[:35]
    return slug if slug else "bible_image"


def place_image(src_path: str, prompt_text: str) -> str:
    src_path = os.path.abspath(os.path.expanduser(src_path))
    if not os.path.isfile(src_path):
        logger.error("Source image not found: %s", src_path)
        sys.exit(1)

    image_title = slugify(prompt_text or os.path.splitext(os.path.basename(src_path))[0])
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    target_filename = f"{timestamp}_{image_title}.png"
    target_path = os.path.join(IMAGES_DIR, target_filename)

    logger.info("Source: %s", src_path)
    logger.info("Refined image title: '%s'", image_title)
    logger.info("Target destination: '%s'", target_path)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    try:
        if src_path.lower().endswith(".png"):
            shutil.copy2(src_path, target_path)
            logger.info("Image was already PNG. Copied directly.")
        else:
            try:
                from PIL import Image  # optional; fall back to raw copy
            except ImportError:
                ext = os.path.splitext(src_path)[1].lower() or ".img"
                target_filename = f"{timestamp}_{image_title}{ext}"
                target_path = os.path.join(IMAGES_DIR, target_filename)
                shutil.copy2(src_path, target_path)
                logger.info("Pillow not installed; copied with original extension.")
            else:
                logger.info("Converting image to PNG format...")
                with Image.open(src_path) as img:
                    img.save(target_path, "PNG")
                logger.info("Successfully converted and saved image.")

        rel = os.path.relpath(target_path, REPO_ROOT)
        print(f"\nSUCCESS: Generated image saved at {rel}")
        return target_path
    except Exception as e:
        logger.error("Error copying/converting image: %s", e)
        sys.exit(1)


def main() -> None:
    args = [a for a in sys.argv[1:] if a.strip() and not (a.startswith("$") or a == '""')]
    if not args:
        logger.error("No source image path provided.")
        print("Usage: python3 image_placer.py <source_image_path> [prompt_or_title]")
        sys.exit(1)

    src = args[0]
    prompt = " ".join(args[1:]) if len(args) > 1 else ""
    place_image(src, prompt)


if __name__ == "__main__":
    main()
