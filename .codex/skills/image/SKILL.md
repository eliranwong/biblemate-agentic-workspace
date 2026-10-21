---
name: image
description: Generate bible-related images with Codex image generation and place them in the images/ directory. Use when the user runs /image or asks for a bible-related image.
---

# Image Generation Skill (Codex)

## Overview
Generate bible-related bitmap images using Codex's `imagegen` skill, then place
a durable copy in the repository's `images/` directory with a timestamped,
slugified filename.

This skill is self-contained for Codex. It must not call image scripts or skill
copies from the other platform folders.

## Workflow

1. Read and follow the local Codex `imagegen` skill before generation.
2. Build a concrete, respectful biblical image prompt from the user's request:
   subject, action, setting, era cues, medium, composition, lighting, and mood.
3. Use the built-in `image_gen` path from `imagegen` unless the user explicitly
   asks for the CLI/API fallback.
4. After generation, move or copy the chosen bitmap into this repository with:
   ```bash
   python3 .codex/skills/image/image_placer.py "<absolute-or-relative-source-path>" "<original user prompt or title>"
   ```
   The helper prints a line like:
   `SUCCESS: Generated image saved at images/YYYY-MM-DD-HH-MM-SS_<slug>.png`
5. Report the saved `images/...` path, the final prompt, and whether the built-in
   image path or explicit CLI fallback was used.

## Prompt Craft

- Lead with the subject, then action, place, era cues, style, and mood.
- Prefer historically and textually respectful depictions; avoid sensational or
  anachronistic detail unless the user asks for a specific artistic style.
- Do not place exact Scripture text in the image unless the user explicitly asks
  for on-image text. If exact text is required, retrieve it with the `bible`
  skill first.
- For diagrams or assets with precise text, prefer deterministic HTML/CSS/SVG
  when that would be more reliable than a generated bitmap.

## Failure Handling

- On a moderation or safety block, stop and offer a different creative direction.
- If generation succeeds but placement fails, report the generated file location
  and the placer error.

## Codex Runtime Notes

- Use this `.codex/skills/image/` copy as the active skill.
- Run helper scripts with `exec_command` from the repository root.
- Use `apply_patch` when creating or editing repository files.
