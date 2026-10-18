#!/usr/bin/env python3
"""
build_cursor.py — Port the Grok Build `.grok` BibleMate skills into Cursor
project skills under `.cursor/`.

Source of truth for content: `.grok/skills/` (and `.grok/agents.md`,
`.grok/preferences/`).

Produces (all relative; no absolute paths):

  .cursor/skills/<name>/...     Cursor Agent Skills (SKILL.md + helpers)
  .cursor/preferences/...       version files the retrievers load
  .cursor/agents.md             persona reference the study skills adopt
  .cursor/rules/biblemate-skills.mdc

Text transforms so the copies run in Cursor, independent of `.grok/`:

  * `.grok/skills/` and related tokens -> `.cursor/...`
  * Grok tool names -> Cursor tool names
  * image generation uses Cursor's GenerateImage tool
  * the update-biblemate skill regenerates this tree

This script is idempotent. It rewrites `skills/`, `preferences/`, `agents.md`,
and `rules/biblemate-skills.mdc` under `.cursor/`. It does not modify
`build_cursor.py` or anything outside `.cursor/` except reading `.grok/`.
"""
from __future__ import annotations

import os
import shutil
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_GROK = os.path.join(REPO_ROOT, ".grok")
SRC_SKILLS = os.path.join(SRC_GROK, "skills")
SRC_AGENTS_MD = os.path.join(SRC_GROK, "agents.md")
SRC_PREFERENCES = os.path.join(SRC_GROK, "preferences")

DST_CURSOR = os.path.join(REPO_ROOT, ".cursor")
DST_SKILLS = os.path.join(DST_CURSOR, "skills")
DST_PREFERENCES = os.path.join(DST_CURSOR, "preferences")
DST_AGENTS_MD = os.path.join(DST_CURSOR, "agents.md")
DST_RULE = os.path.join(DST_CURSOR, "rules", "biblemate-skills.mdc")

SKIP_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}
TEXT_EXTENSIONS = (".py", ".md", ".txt", ".json", ".toml", ".yml", ".yaml")

# Longer / more specific phrases first.
TOOL_REPLACEMENTS = [
    (
        "use `spawn_subagent` (or background `run_terminal_command`) to dispatch the retrieval skills",
        "use the `Task` tool (or a background `Shell` command) to dispatch the retrieval skills",
    ),
    (
        'use the `spawn_subagent` tool (with `DurationSeconds="1"`) to dispatch tasks',
        "use the `Task` tool to dispatch tasks",
    ),
    ("`spawn_subagent`", "`Task`"),
    ("`run_terminal_command`", "`Shell`"),
    ("`read_file`", "`Read`"),
    ("`search_replace`", "`StrReplace`"),
    ("`web_fetch` / `open_page`", "`WebFetch`"),
    ("`web_search`", "`WebSearch`"),
    ("`list_dir`", "`Glob`"),
    ("`grep`", "`Grep`"),
    ("the `write` tool", "the `Write` tool"),
    ("`write` tool", "`Write` tool"),
    ("Antigravity platform", "Cursor"),
    ("capabilities of the Cursor", "capabilities of Cursor"),
    (
        "Grok Build's image_gen / image_edit tools",
        "Cursor's GenerateImage tool",
    ),
    ("Grok Build–generated", "Cursor-generated"),
    ("Grok Build", "Cursor"),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def reset_dir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def rewrite_paths(text: str) -> str:
    text = text.replace(".grok/skills/", ".cursor/skills/")
    text = text.replace(".grok/agents.md", ".cursor/agents.md")
    text = text.replace(".grok/commands/", ".cursor/commands/")
    text = text.replace(".grok/preferences/", ".cursor/preferences/")
    text = text.replace(".grok/build_grok.py", ".cursor/build_cursor.py")
    text = text.replace('".grok", "skills"', '".cursor", "skills"')
    text = text.replace("'.grok', 'skills'", "'.cursor', 'skills'")
    text = text.replace(".grok/", ".cursor/")
    text = text.replace("`.grok`", "`.cursor`")
    text = text.replace("'.grok'", "'.cursor'")
    text = text.replace('".grok"', '".cursor"')
    text = text.replace(".grok", ".cursor")
    return text


def rewrite_tools(text: str) -> str:
    for old, new in TOOL_REPLACEMENTS:
        text = text.replace(old, new)
    return text


def transform_text(text: str) -> str:
    return rewrite_tools(rewrite_paths(text))


def copy_tree_transformed(src: str, dst: str) -> None:
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if name in SKIP_NAMES:
            continue
        spath = os.path.join(src, name)
        dpath = os.path.join(dst, name)
        if os.path.isdir(spath):
            copy_tree_transformed(spath, dpath)
        elif name.endswith(TEXT_EXTENSIONS):
            with open(spath, "r", encoding="utf-8") as f:
                content = transform_text(f.read())
            with open(dpath, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            shutil.copy2(spath, dpath)


def write_image_skill() -> None:
    skill_md = """---
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
"""
    path = os.path.join(DST_SKILLS, "image", "SKILL.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(skill_md)


def write_update_skill() -> None:
    """Write the Cursor refresh skill as update-biblemate.

    Grok ships this workflow as `update-biblemate`. If an older copy still
    arrives as `update`, move its helper and drop that directory so Cursor
    exposes one skill under the new name.
    """
    skill_md = """---
name: update-biblemate
description: Refresh the BibleMate Cursor skills by regenerating .cursor from the Grok sources in this repository. Use when the user runs /update-biblemate or asks to regenerate the .cursor skills.
---

# Update BibleMate Skill (Cursor)

## Overview
This skill refreshes the Cursor BibleMate skills in `.cursor/`. Content comes
from `.grok/skills/` (itself generated from `.claude/`). The generator rewrites
paths and tool names so the copies run in Cursor.

## Guidelines & Objectives
1. **Verify Operating System**: Only supported on macOS or Linux.
2. **Verify Workspace Folder**: Confirm with the user before a refresh inside a
   workspace named `antigravity-biblemate-workspace`.
3. **Refresh upstream trees when they are missing or stale**:
   ```bash
   python3 .claude/build_claude.py
   python3 .grok/build_grok.py
   ```
   Optional remote download, only when the user wants a fresh upstream bundle:
   ```bash
   python3 .cursor/skills/update-biblemate/updater.py
   ```
4. **Regenerate `.cursor`**:
   ```bash
   python3 .cursor/build_cursor.py
   ```
5. **Report Status**: Say whether regeneration succeeded, how many skills were
   written, and confirm `.cursor/rules/biblemate-skills.mdc` is present.
"""
    legacy = os.path.join(DST_SKILLS, "update")
    skill_dir = os.path.join(DST_SKILLS, "update-biblemate")
    os.makedirs(skill_dir, exist_ok=True)
    updater_src = os.path.join(legacy, "updater.py")
    if os.path.isfile(updater_src):
        shutil.copy2(updater_src, os.path.join(skill_dir, "updater.py"))
    if os.path.isdir(legacy):
        shutil.rmtree(legacy)
    path = os.path.join(skill_dir, "SKILL.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(skill_md)


def write_rule() -> None:
    os.makedirs(os.path.dirname(DST_RULE), exist_ok=True)
    rule = """---
description: Follow the BibleMate Cursor skills in .cursor/skills for scripture study and related workflows
alwaysApply: true
---

# BibleMate skills

BibleMate workflows in this repository are Cursor project skills at `.cursor/skills/<name>/SKILL.md`. When a request matches one, read that `SKILL.md` and follow it before answering.

## When to apply

Apply the matching skill when the user:

- Invokes a BibleMate command such as `/bible`, `/sermon`, `/devotion`, `/biblemate`, `/biblemate-super`, or a book code such as `/Gen`
- Asks for scripture retrieval, a study, devotion, sermon, prayer, commentary, lexicon, search, or another workflow named by a skill in `.cursor/skills/`

Use `.cursor/skills/`. Ignore the parallel copies in `.claude/skills/` and `.grok/skills/` for the same workflow.

## How to follow a skill

1. Read `.cursor/skills/<name>/SKILL.md` and do what it says.
2. Run the Python helpers it names with the `Shell` tool, from the repository root.
3. Quote scripture only from `bible` skill output: `python3 .cursor/skills/bible/bible_retriever.py "<query>"`.
4. Save bible-related study output with the `Write` tool to `biblemate/YYYY-MM-DD-HH-MM-SS_<desc>.md`. Skip saving for `biblemate`, `biblemate-super`, `image`, `data`, `sync`, `md`, `docx`, and `zip`. Confirm the saved path.
5. For a full multi-skill study, follow `biblemate` or `biblemate-super`. Adopt personas from `.cursor/agents.md`, or delegate with the `Task` tool using the persona slug.

## Tools

These skills expect Cursor tools: `Read`, `Write`, `StrReplace`, `Shell`, `Grep`, `Glob`, `Task`, `WebSearch`, `WebFetch`, and `GenerateImage`.
"""
    with open(DST_RULE, "w", encoding="utf-8") as f:
        f.write(rule)


def audit() -> int:
    """Flag accidental Grok leftovers. Upstream refresh paths may still name `.grok`."""
    needles = (
        "spawn_subagent",
        "run_terminal_command",
        "`image_gen`",
        "web_search",
        "open_page",
        "Grok Build",
    )
    allow_grok = {
        os.path.normpath(os.path.join(DST_SKILLS, "update-biblemate", "SKILL.md")),
        os.path.normpath(DST_RULE),
    }
    bad = []
    roots = [DST_SKILLS, DST_PREFERENCES, DST_AGENTS_MD, DST_RULE]
    for root in roots:
        if os.path.isfile(root):
            files = [root]
        else:
            files = []
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
                for name in filenames:
                    if name.endswith(TEXT_EXTENSIONS):
                        files.append(os.path.join(dirpath, name))
        for path in files:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            hits = [n for n in needles if n in text]
            if ".grok" in text and os.path.normpath(path) not in allow_grok:
                hits.append(".grok")
            if hits:
                bad.append((path, hits))
    if bad:
        log("Leftover Grok-specific tokens:")
        for path, hits in bad:
            log(f"  {os.path.relpath(path, REPO_ROOT)}: {', '.join(hits)}")
        return 1
    return 0


def main() -> int:
    if not os.path.isdir(SRC_SKILLS):
        log(f"Error: missing source skills at {SRC_SKILLS}")
        return 1
    if not os.path.isfile(SRC_AGENTS_MD):
        log(f"Error: missing {SRC_AGENTS_MD}")
        return 1
    if not os.path.isdir(SRC_PREFERENCES):
        log(f"Error: missing {SRC_PREFERENCES}")
        return 1

    log("Porting .grok skills -> .cursor/skills")
    reset_dir(DST_SKILLS)
    copy_tree_transformed(SRC_SKILLS, DST_SKILLS)
    write_image_skill()
    write_update_skill()

    log("Porting preferences and persona reference")
    reset_dir(DST_PREFERENCES)
    copy_tree_transformed(SRC_PREFERENCES, DST_PREFERENCES)
    with open(SRC_AGENTS_MD, "r", encoding="utf-8") as f:
        agents = transform_text(f.read())
    with open(DST_AGENTS_MD, "w", encoding="utf-8") as f:
        f.write(agents)

    log("Writing project rule")
    write_rule()

    skill_count = sum(
        1
        for name in os.listdir(DST_SKILLS)
        if os.path.isfile(os.path.join(DST_SKILLS, name, "SKILL.md"))
    )
    log(f"Wrote {skill_count} skills to .cursor/skills/")
    log("Wrote .cursor/rules/biblemate-skills.mdc")

    status = audit()
    if status == 0:
        log("Audit clean: no leftover Grok paths or tool names.")
    return status


if __name__ == "__main__":
    sys.exit(main())
