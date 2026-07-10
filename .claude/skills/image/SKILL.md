---
name: image
description: Generate bible-related images and place them in the images/ directory.
---

# Image Generation Skill

## Overview
This standalone skill enables any agent to generate bible-related images based on a user's prompt using the local image generation capabilities, placing the final image in the repository's `images/` directory with a timestamped and slugified filename.

## Guidelines & Objectives
When executing this skill:
- Always run the python script located at `.claude/skills/image/image_generator.py` to generate the image.
- Execute the script using: `python3 .claude/skills/image/image_generator.py "<query>"` where `<query>` is the prompt describing the image to generate.
- Present the exact output of the script to the user, confirming the filename and status of the output.
