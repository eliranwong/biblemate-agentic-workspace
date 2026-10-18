---
name: image
description: Generate bible-related images with Cursor's GenerateImage tool and place them in the images/ directory. Use when the user runs /image or asks for a bible-related image.
---

# Image Generation Skill (Cursor)

## Overview
Generate bible-related images with Cursor's **GenerateImage** tool, then place
a durable copy in the repository's `images/` directory with a timestamped,
slugified filename.

This skill is self-contained for Cursor. It does not use Google Antigravity,
the `google-antigravity` SDK, or any `.agents/` image script.

## Tools

| Situation | Tool |
|-----------|------|
| New image from a text prompt (default) | `GenerateImage` |
| Restyle or vary an existing image | `GenerateImage` with `reference_image_paths` |
| Place the result under `images/` with BibleMate naming | `image_placer.py` (below) |

`GenerateImage` arguments:

- `description` (required): concrete scene, at least 6 words
- `aspect_ratio` (optional): `16:9`, `1:1`, `9:16`, `4:3`, or `3:4`
- `filename` (optional): file name only, no directory
- `reference_image_paths` (optional): source images for a variation

## Workflow

1. **Craft the description.** Prefer a concrete biblical scene, subject, setting,
   style, lighting, and mood in natural prose (about 2–5 sentences). If the user
   supplies a detailed prompt, use it (refined only if needed for clarity).
2. **Choose aspect ratio** when helpful:
   - `16:9` — landscape scenes, banners
   - `1:1` — icons, social thumbnails
   - `9:16` — phone / story format
   - `4:3` / `3:4` — classic illustration framing
   - omit it when the user does not specify
3. **Generate** with `GenerateImage`. Do not call any Antigravity API or script.
   For a variation, pass the source file in `reference_image_paths`.
4. **Place** the returned file into the repo `images/` directory:
   ```bash
   python3 .cursor/skills/image/image_placer.py "<absolute-or-relative-source-path>" "<original user prompt or title>"
   ```
   The helper prints a line like:
   `SUCCESS: Generated image saved at images/YYYY-MM-DD-HH-MM-SS_<slug>.png`
5. **Report** the saved `images/...` path and briefly describe what was generated.
   Do not repeat the image as Markdown; Cursor displays the tool image itself.

## Prompt craft (bible scenes)

- Lead with the subject (who / what), then action, place, era cues, style, and mood.
- Prefer historically and textually respectful depictions; avoid sensational or
  anachronistic detail unless the user asks for a specific artistic style.
- State what to include; avoid long negative-prompt lists.
- For labeled diagrams, charts, or exact scripture text on the image, prefer
  building the asset with code (HTML/CSS) rather than pure image generation —
  image models often garble precise text.

## Failures

- On a moderation or safety block: stop; do not rephrase to evade filters. Tell
  the user and offer a different creative direction.
- If generation succeeds but placement fails, report both the tool output path
  and the placer error so the user can still find the raw file.

## Do not

- Run `.agents/skills/image/image_generator.py` or any `google.antigravity` code.
- Invent image-tool parameters beyond `description`, `aspect_ratio`, `filename`,
  and `reference_image_paths`.
- Quote or invent Bible verse text on the image unless the user explicitly wants
  on-image text (and even then, verify accuracy if text must be exact).
