#!/usr/bin/env python3
"""
build_codex.py - Port the Cursor BibleMate skills into Codex-native project
skills under `.codex/`.

Source of truth for content: `.cursor/skills/`, `.cursor/agents.md`, and
`.cursor/preferences/`.

Produces:

  .codex/skills/<name>/...       Codex skills (SKILL.md + helpers)
  .codex/preferences/...         version files the retrievers load
  .codex/agents.md               persona reference with Codex-oriented wording

The generated tree is self-contained. Runtime instructions and helper scripts
refer to `.codex/...` paths and Codex tools, not `.agents`, `.claude`, `.grok`,
or `.cursor` skills.
"""
from __future__ import annotations

import os
import re
import shutil
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC_CURSOR = os.path.join(REPO_ROOT, ".cursor")
SRC_SKILLS = os.path.join(SRC_CURSOR, "skills")
SRC_AGENTS_MD = os.path.join(SRC_CURSOR, "agents.md")
SRC_PREFERENCES = os.path.join(SRC_CURSOR, "preferences")

DST_CODEX = os.path.join(REPO_ROOT, ".codex")
DST_SKILLS = os.path.join(DST_CODEX, "skills")
DST_PREFERENCES = os.path.join(DST_CODEX, "preferences")
DST_AGENTS_MD = os.path.join(DST_CODEX, "agents.md")

SKIP_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}
TEXT_EXTENSIONS = (".py", ".md", ".txt", ".json", ".toml", ".yml", ".yaml")

TOOL_REPLACEMENTS = [
    ("the `Write` tool", "`apply_patch`"),
    ("the `Read` tool", "Codex file-reading commands such as `sed`, `rg`, and `ls`"),
    ("the `Edit` tool", "`apply_patch`"),
    ("the `Bash` tool", "`exec_command`"),
    ("the `Grep` tool", "`rg`"),
    ("the `Glob` tool", "`rg --files`"),
    ("the `Task` tool", "available Codex subagent tools"),
    ("`GenerateImage`", "the Codex `imagegen` skill"),
    ("`WebSearch`", "`web.run` search"),
    ("`WebFetch`", "`web.run` open"),
    ("`Write` tool", "`apply_patch`"),
    ("`Read` tool", "Codex file-reading commands"),
    ("`Edit` tool", "`apply_patch`"),
    ("`Bash` tool", "`exec_command`"),
    ("`Grep` tool", "`rg`"),
    ("`Glob` tool", "`rg --files`"),
    ("`Task` tool", "available Codex subagent tools"),
    ("`Write`", "`apply_patch`"),
    ("`Read`", "`sed`/`rg`"),
    ("`Edit`", "`apply_patch`"),
    ("`Bash`", "`exec_command`"),
    ("`Grep`", "`rg`"),
    ("`Glob`", "`rg --files`"),
    ("`Task`", "Codex subagents"),
    ("`Shell`", "`exec_command`"),
    ("`StrReplace`", "`apply_patch`"),
    ("Cursor's GenerateImage tool", "the Codex `imagegen` skill"),
    ("Cursor-generated", "Codex-generated"),
    ("capabilities of Cursor", "capabilities of Codex"),
    ("Cursor project skills", "Codex project skills"),
    ("Cursor Agent Skills", "Codex skills"),
    ("Cursor", "Codex"),
]


def log(message: str) -> None:
    print(message, flush=True)


def reset_dir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def rewrite_paths(text: str) -> str:
    replacements = [
        (".cursor/skills/", ".codex/skills/"),
        (".cursor/agents.md", ".codex/agents.md"),
        (".cursor/preferences/", ".codex/preferences/"),
        (".cursor/build_cursor.py", ".codex/build_codex.py"),
        ('".cursor", "skills"', '".codex", "skills"'),
        ("'.cursor', 'skills'", "'.codex', 'skills'"),
        ("['.cursor', 'preferences']", "['.codex', 'preferences']"),
        ("'.cursor/' and 'preferences/'", "'.codex/' and 'preferences/'"),
        ("`.cursor`", "`.codex`"),
        ("'.cursor'", "'.codex'"),
        ('".cursor"', '".codex"'),
        (".cursor/", ".codex/"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def rewrite_tools(text: str) -> str:
    for old, new in TOOL_REPLACEMENTS:
        text = text.replace(old, new)
    text = text.replace(
        "use Codex subagents (or a background `exec_command` command) to dispatch the retrieval skills",
        "use available Codex subagent tools or background `exec_command` sessions to dispatch retrieval skills",
    )
    text = text.replace(
        "use the Codex subagents to dispatch tasks",
        "use available Codex subagent tools to dispatch tasks",
    )
    return text


def transform_text(text: str) -> str:
    return rewrite_tools(rewrite_paths(text))


def add_codex_skill_footer(text: str, skill_name: str) -> str:
    if "## Codex Runtime Notes" in text:
        return text
    footer = f"""

## Codex Runtime Notes

- Use this `.codex/skills/{skill_name}/` copy as the active skill. Do not invoke
  sibling skills from `.agents/`, `.claude/`, `.grok/`, or `.cursor/`.
- Run helper scripts with `exec_command` from the repository root, using the
  `.codex/skills/...` paths named above.
- Use `apply_patch` when creating or editing repository files; use shell
  commands only for execution, inspection, validation, and generated helper
  output.
"""
    return text.rstrip() + footer


def transform_skill_md(text: str, skill_name: str) -> str:
    text = transform_text(text)
    text = add_codex_skill_footer(text, skill_name)
    return text + ("\n" if not text.endswith("\n") else "")


def copy_tree_transformed(src: str, dst: str) -> None:
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if name in SKIP_NAMES:
            continue
        spath = os.path.join(src, name)
        dpath = os.path.join(dst, name)
        if os.path.isdir(spath):
            copy_tree_transformed(spath, dpath)
            continue
        if name.endswith(TEXT_EXTENSIONS):
            with open(spath, "r", encoding="utf-8") as handle:
                content = handle.read()
            if name == "SKILL.md":
                skill_name = os.path.basename(os.path.dirname(spath))
                content = transform_skill_md(content, skill_name)
            else:
                content = transform_text(content)
            with open(dpath, "w", encoding="utf-8") as handle:
                handle.write(content)
        else:
            shutil.copy2(spath, dpath)


def write_project_instructions() -> None:
    instructions = """# BibleMate Codex Skills

This folder contains the Codex-native BibleMate skill ecosystem for this
workspace. It is generated by:

```bash
python3 .codex/build_codex.py
```

Use `.codex/skills/<name>/SKILL.md` for BibleMate workflows in Codex. These
skills are self-contained and should not call sibling skill copies from
`.agents/`, `.claude/`, `.grok/`, or `.cursor/`.

## Universal Rules

1. Never quote Bible text from memory. Use the `bible` skill and its local
   retriever:
   ```bash
   python3 .codex/skills/bible/bible_retriever.py "NET John 3:16"
   ```
2. For bible-related study skills other than `biblemate`, `biblemate-super`,
   `image`, `data`, `sync`, `md`, `docx`, and `zip`, save the full study output
   under `biblemate/` with a timestamp prefix and confirm the path.
3. Use Codex tools and conventions:
   - inspect files with `rg`, `rg --files`, `sed`, `ls`, and related shell
     commands through `exec_command`
   - edit or create repository files with `apply_patch`
   - search/fetch online sources with `web.run`
   - use Codex subagent tools only when they are available in the current turn

## Refresh

Regenerating `.codex/skills` rewrites only generated Codex artifacts under
`.codex/`: `skills/`, `preferences/`, and `agents.md`. It does not modify the
parallel `.agents/`, `.claude/`, `.grok/`, or `.cursor/` folders.
"""
    with open(os.path.join(DST_CODEX, "AGENTS.md"), "w", encoding="utf-8") as handle:
        handle.write(instructions)


def write_image_skill() -> None:
    skill_dir = os.path.join(DST_SKILLS, "image")
    os.makedirs(skill_dir, exist_ok=True)
    skill_md = """---
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
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as handle:
        handle.write(skill_md)


def write_update_skill() -> None:
    skill_dir = os.path.join(DST_SKILLS, "update-biblemate")
    os.makedirs(skill_dir, exist_ok=True)
    updater = os.path.join(skill_dir, "updater.py")
    if os.path.isfile(updater):
        with open(updater, "r", encoding="utf-8") as handle:
            content = transform_text(handle.read())
        with open(updater, "w", encoding="utf-8") as handle:
            handle.write(content)
    skill_md = """---
name: update-biblemate
description: Refresh the BibleMate Codex skills by regenerating .codex from this repository's maintained skill sources. Use when the user runs /update-biblemate or asks to regenerate the .codex skills.
---

# Update BibleMate Skill (Codex)

## Overview
This skill refreshes the Codex BibleMate skills in `.codex/`. Content comes from
this repository's maintained skill source tree, then the generator rewrites
paths and tool names so the copies run in Codex.

## Guidelines & Objectives
1. Verify the workspace is this BibleMate repository.
2. Regenerate `.codex`:
   ```bash
   python3 .codex/build_codex.py
   ```
3. Report whether regeneration succeeded, how many skills were written, and
   whether the audit was clean.

## Codex Runtime Notes

- Do not modify `.agents/`, `.claude/`, `.grok/`, or `.cursor/` while refreshing
  the Codex tree.
- Use `exec_command` for the generator and validation commands.
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as handle:
        handle.write(skill_md)


def is_hyphen_case(name: str) -> bool:
    return re.fullmatch(r"[a-z0-9][a-z0-9-]*", name) is not None


def normalize_skill_names() -> None:
    """Make generated skill folder names/frontmatter valid Codex skill names."""
    for original in sorted(os.listdir(DST_SKILLS)):
        src = os.path.join(DST_SKILLS, original)
        if not os.path.isdir(src):
            continue
        normalized = original.lower()
        if is_hyphen_case(original):
            normalized = original
        if normalized == original:
            continue

        tmp = os.path.join(DST_SKILLS, f"__tmp__{normalized}")
        dst = os.path.join(DST_SKILLS, normalized)
        if os.path.exists(tmp):
            shutil.rmtree(tmp)
        os.rename(src, tmp)
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.rename(tmp, dst)

        skill_md = os.path.join(dst, "SKILL.md")
        if os.path.isfile(skill_md):
            with open(skill_md, "r", encoding="utf-8") as handle:
                content = handle.read()
            content = re.sub(
                r"(?m)^name:\s*" + re.escape(original) + r"\s*$",
                f"name: {normalized}",
                content,
                count=1,
            )
            content = content.replace(
                f".codex/skills/{original}/",
                f".codex/skills/{normalized}/",
            )
            with open(skill_md, "w", encoding="utf-8") as handle:
                handle.write(content)


def audit() -> int:
    bad = []
    forbidden_path_refs = (
        ".agents/skills/",
        ".claude/skills/",
        ".grok/skills/",
        ".cursor/skills/",
    )
    forbidden_tool_refs = (
        "`Write`",
        "`Read`",
        "`Edit`",
        "`Bash`",
        "`Grep`",
        "`Glob`",
        "`Task`",
        "`Shell`",
        "`StrReplace`",
        "`WebSearch`",
        "`WebFetch`",
        "`GenerateImage`",
        "spawn_subagent",
        "run_terminal_command",
        "search_replace",
        "read_file",
    )
    allowed = {
        os.path.normpath(os.path.join(DST_CODEX, "build_codex.py")),
        os.path.normpath(os.path.join(DST_SKILLS, "image", "SKILL.md")),
        os.path.normpath(os.path.join(DST_SKILLS, "zip", "SKILL.md")),
        os.path.normpath(os.path.join(DST_SKILLS, "update-biblemate", "SKILL.md")),
        os.path.normpath(os.path.join(DST_SKILLS, "update-biblemate", "updater.py")),
        os.path.normpath(os.path.join(DST_CODEX, "AGENTS.md")),
    }
    for dirpath, dirnames, filenames in os.walk(DST_CODEX):
        dirnames[:] = [d for d in dirnames if d not in SKIP_NAMES]
        for filename in filenames:
            if not filename.endswith(TEXT_EXTENSIONS):
                continue
            path = os.path.join(dirpath, filename)
            with open(path, "r", encoding="utf-8") as handle:
                text = handle.read()
            if os.path.normpath(path) in allowed:
                continue
            hits = [needle for needle in forbidden_path_refs if needle in text]
            hits.extend(needle for needle in forbidden_tool_refs if needle in text)
            if hits:
                bad.append((path, sorted(set(hits))))
    if bad:
        log("Codex audit found non-Codex leftovers:")
        for path, hits in bad:
            log(f"  {os.path.relpath(path, REPO_ROOT)}: {', '.join(hits)}")
        return 1
    return 0


def validate_inputs() -> int:
    required = (SRC_SKILLS, SRC_AGENTS_MD, SRC_PREFERENCES)
    missing = [path for path in required if not os.path.exists(path)]
    if missing:
        for path in missing:
            log(f"Error: missing source path {path}")
        return 1
    return 0


def main() -> int:
    if validate_inputs() != 0:
        return 1

    log("Porting .cursor skills -> .codex/skills")
    reset_dir(DST_SKILLS)
    copy_tree_transformed(SRC_SKILLS, DST_SKILLS)
    write_image_skill()
    write_update_skill()
    normalize_skill_names()

    log("Porting preferences and persona reference")
    reset_dir(DST_PREFERENCES)
    copy_tree_transformed(SRC_PREFERENCES, DST_PREFERENCES)
    with open(SRC_AGENTS_MD, "r", encoding="utf-8") as handle:
        agents = transform_text(handle.read())
    with open(DST_AGENTS_MD, "w", encoding="utf-8") as handle:
        handle.write(agents)
    write_project_instructions()

    skill_count = sum(
        1
        for name in os.listdir(DST_SKILLS)
        if os.path.isfile(os.path.join(DST_SKILLS, name, "SKILL.md"))
    )
    log(f"Wrote {skill_count} skills to .codex/skills/")

    status = audit()
    if status == 0:
        log("Audit clean: no non-Codex skill paths or tool names.")
    return status


if __name__ == "__main__":
    sys.exit(main())
