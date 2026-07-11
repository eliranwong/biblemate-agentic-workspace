#!/usr/bin/env python3
"""
build_grok.py — Port the Claude Code `.claude` BibleMate ecosystem into a
self-contained, portable Grok Build `.grok` ecosystem.

Primary source of truth for content: `.claude/` (the Claude Code port).
Produces (all relative; no absolute paths):

  .grok/skills/<name>/...          <- from .claude/skills/<name>/...
  .grok/commands/<name>.md         <- from .claude/commands/<name>.md
  .grok/agents/<slug>.md           <- Grok agent definitions (spawn_subagent types)
  .grok/personas/<slug>.toml       <- Grok persona overlays
  .grok/agents.md                  <- combined persona reference (paths ported)
  .grok/preferences/...            <- from .claude/preferences/...

Text transforms applied so the Grok Build copies work independently of
`.claude/` and `.agents/`:
  * `.claude/skills/`            -> `.grok/skills/`
  * `.claude/agents.md`          -> `.grok/agents.md`
  * `.claude/` directory tokens  -> `.grok/`
  * Claude tool names            -> Grok tool names
  * persona-adoption lines point to `.grok/agents.md`
  * orchestrator discovery paths use `.grok/skills`
  * zip packages `.grok` + preferences
  * data dir resolution keeps BIBLEMATE_DATA / ~/biblemate portability

This script is idempotent. It only rewrites the skills/commands/agents/
personas/preferences subtrees and agents.md under `.grok/`. It never
touches build_grok.py, AGENTS.md, or anything outside `.grok/` except
reading from `.claude/`.
"""
from __future__ import annotations

import os
import re
import shutil
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_CLAUDE = os.path.join(REPO_ROOT, ".claude")
SRC_SKILLS = os.path.join(SRC_CLAUDE, "skills")
SRC_COMMANDS = os.path.join(SRC_CLAUDE, "commands")
SRC_AGENTS_MD = os.path.join(SRC_CLAUDE, "agents.md")
SRC_PREFERENCES = os.path.join(SRC_CLAUDE, "preferences")

DST_GROK = os.path.join(REPO_ROOT, ".grok")
DST_SKILLS = os.path.join(DST_GROK, "skills")
DST_COMMANDS = os.path.join(DST_GROK, "commands")
DST_AGENTS_DIR = os.path.join(DST_GROK, "agents")
DST_PERSONAS_DIR = os.path.join(DST_GROK, "personas")
DST_AGENTS_MD = os.path.join(DST_GROK, "agents.md")
DST_PREFERENCES = os.path.join(DST_GROK, "preferences")

SKIP_NAMES = {"__pycache__", ".DS_Store", "Thumbs.db"}

PERSONA_SLUGS = {
    "Passionate Evangelist": "passionate-evangelist",
    "Context Analyst David": "context-analyst-david",
    "Biblical Content Interpreter": "biblical-content-interpreter",
    "Compassionate Pastor": "compassionate-pastor",
    "Verse Scripter": "verse-scripter",
    "OT Bible Scholar": "ot-bible-scholar",
    "NT Bible Scholar": "nt-bible-scholar",
    "Biblical Theologian": "biblical-theologian",
    "Systematic Theologian": "systematic-theologian",
    "Biblical Translator": "biblical-translator",
    "Biblical Linguistic Analyst": "biblical-linguistic-analyst",
    "Bible Textual Critic": "bible-textual-critic",
    "Master Biblical Writer": "master-biblical-writer",
    "AI Agent Creator": "ai-agent-creator",
    "Study Plan & Phase Quality Auditor": "study-quality-auditor",
}

# Claude Code tool names -> Grok Build tool names (order matters for partials).
TOOL_REPLACEMENTS = [
    # Longer / more specific first
    ("the `Write` tool", "the `write` tool"),
    ("the `Read` tool", "the `read_file` tool"),
    ("the `Edit` tool", "the `search_replace` tool"),
    ("the `Bash` tool", "the `run_terminal_command` tool"),
    ("the `Grep` tool", "the `grep` tool"),
    ("the `Glob` tool", "the `list_dir` tool"),
    ("the `Task` tool", "the `spawn_subagent` tool"),
    ("`Write`", "`write`"),
    ("`Read`", "`read_file`"),
    ("`Edit`", "`search_replace`"),
    ("`Bash`", "`run_terminal_command`"),
    ("`Grep`", "`grep`"),
    ("`Glob`", "`list_dir`"),
    ("`Task`", "`spawn_subagent`"),
    # Frontmatter tools lists (Claude-style)
    (
        "tools: Read, Write, Edit, Bash, Grep, Glob",
        "tools: read_file, write, search_replace, run_terminal_command, grep, list_dir",
    ),
    (
        "tools: Read, Write, Edit, Bash, Grep, Glob, Task",
        "tools: read_file, write, search_replace, run_terminal_command, grep, list_dir, spawn_subagent",
    ),
]


def log(msg: str) -> None:
    print(msg, flush=True)


def reset_dir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# Text transforms
# ---------------------------------------------------------------------------

def rewrite_paths(text: str) -> str:
    """Rewrite `.claude/...` references to `.grok/...` equivalents."""
    text = text.replace(".claude/skills/", ".grok/skills/")
    text = text.replace(".claude/agents.md", ".grok/agents.md")
    text = text.replace(".claude/commands/", ".grok/commands/")
    text = text.replace(".claude/agents/", ".grok/agents/")
    text = text.replace(".claude/preferences/", ".grok/preferences/")
    text = text.replace(".claude/build_claude.py", ".grok/build_grok.py")
    # Orchestrator discovery: os.path.join(workspace_root, ".claude", "skills")
    text = text.replace('".claude", "skills"', '".grok", "skills"')
    text = text.replace("'.claude', 'skills'", "'.grok', 'skills'")
    text = text.replace("/.claude/skills/", "/.grok/skills/")
    # zip packages
    text = text.replace("to zip the `.claude/`, `preferences/`, and `.grok/` folders, and the `AGENTS.md` and `CLAUDE.md` files", "to zip the `.grok/`, `preferences/` folders, and the `AGENTS.md` and `CLAUDE.md` files")
    text = text.replace("['.claude', 'preferences']", "['.grok', 'preferences']")
    text = text.replace("'.claude/' and 'preferences/'", "'.grok/' and 'preferences/'")
    text = text.replace("'.claude/'", "'.grok/'")
    # Remaining bare directory tokens
    text = text.replace(".claude/", ".grok/")
    text = text.replace("`.claude`", "`.grok`")
    # Prose about Claude Code -> Grok Build
    text = text.replace("Claude Code", "Grok Build")
    text = text.replace("for Claude Code", "for Grok Build")
    return text


def rewrite_tools(text: str) -> str:
    for old, new in TOOL_REPLACEMENTS:
        text = text.replace(old, new)
    # schedule tool (Antigravity/Claude dispatch hint) -> Grok background/subagent guidance
    text = text.replace(
        'use the `schedule` tool (with `DurationSeconds="1"`) to dispatch the retrieval skills',
        "use `spawn_subagent` (or background `run_terminal_command`) to dispatch the retrieval skills",
    )
    text = text.replace("`schedule` tool", "`spawn_subagent` tool")
    return text


def enhance_skill_description(text: str, skill_name: str) -> str:
    """Ensure Grok-friendly description with slash-command trigger."""
    m = re.match(r"^---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not m:
        return text
    fm = m.group(1)
    body = text[m.end() :]

    # Normalize name to directory/skill name if missing
    if not re.search(r"(?m)^name:\s*", fm):
        fm = f"name: {skill_name}\n" + fm

    desc_m = re.search(r"(?m)^description:\s*(.+)$", fm)
    if desc_m:
        desc = desc_m.group(1).strip()
        # Unwrap folded multi-line descriptions already present as single line
        slash = f"/{skill_name}"
        if slash not in desc and "Use when" not in desc:
            if not desc.endswith("."):
                desc += "."
            desc = f"{desc} Use when the user runs {slash} or requests this BibleMate workflow."
            fm = re.sub(
                r"(?m)^description:\s*.+$",
                f"description: {desc}",
                fm,
                count=1,
            )
    return f"---\n{fm}\n---\n{body}"


def transform_python(text: str) -> str:
    text = rewrite_paths(text)
    # Preferences already resolve via script_dir/../.. which works for .grok/skills/<name>/
    return text


def transform_skill_md(text: str, skill_name: str) -> str:
    text = rewrite_paths(text)
    text = rewrite_tools(text)
    text = enhance_skill_description(text, skill_name)
    return text


def transform_command_md(text: str) -> str:
    text = rewrite_paths(text)
    text = rewrite_tools(text)
    # Claude already uses $ARGUMENTS; keep it (Grok passes args after the slash command).
    return text


def transform_agents_md(text: str) -> str:
    text = rewrite_paths(text)
    text = rewrite_tools(text)
    return text


# ---------------------------------------------------------------------------
# Copy helpers
# ---------------------------------------------------------------------------

def copy_tree_transformed(src: str, dst: str, file_transform) -> None:
    """Copy a directory tree, applying file_transform(content, name, spath)."""
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if name in SKIP_NAMES:
            continue
        spath = os.path.join(src, name)
        dpath = os.path.join(dst, name)
        if os.path.isdir(spath):
            copy_tree_transformed(spath, dpath, file_transform)
        else:
            # Binary-safe: only transform known text extensions
            if name.endswith((".py", ".md", ".txt", ".json", ".toml", ".yml", ".yaml")):
                with open(spath, "r", encoding="utf-8") as f:
                    content = f.read()
                content = file_transform(content, name, spath)
                with open(dpath, "w", encoding="utf-8") as f:
                    f.write(content)
            else:
                shutil.copy2(spath, dpath)


def copy_skill(src_skill: str, dst_skill: str, skill_name: str) -> None:
    def file_tf(content, name, spath):
        if name == "SKILL.md":
            return transform_skill_md(content, skill_name)
        if name.endswith(".py"):
            return transform_python(content)
        if name.endswith(".md"):
            return rewrite_paths(rewrite_tools(content))
        return content

    copy_tree_transformed(src_skill, dst_skill, file_tf)


# ---------------------------------------------------------------------------
# Persona / agent / persona.toml generation
# ---------------------------------------------------------------------------

def parse_agents_md(text: str):
    """Return (universal_header, [(persona_name, body), ...])."""
    first = text.find("\n## ")
    if first == -1:
        return text, []
    universal = text[:first].rstrip()
    rest = text[first + 1 :]

    parts = re.split(r"\n(?=## )", rest)
    personas = []
    for part in parts:
        part = part.strip()
        if not part.startswith("## "):
            continue
        name = part[3:].splitlines()[0].strip()
        personas.append((name, part))
    return universal, personas


def first_sentence(body: str) -> str:
    lines = body.splitlines()
    for ln in lines[1:]:
        ln = ln.strip()
        if ln and not ln.startswith("#") and not ln.startswith("---"):
            return ln
    return ""


def slug_for(name: str) -> str:
    slug = PERSONA_SLUGS.get(name)
    if slug:
        return slug
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "persona"


def toml_escape(s: str) -> str:
    """Escape a string for TOML multi-line basic string body (triple quotes)."""
    return s.replace("\\", "\\\\").replace('"""', '\\"""')


def build_agent_md(name: str, body: str, universal: str) -> str:
    """Grok agent definition for .grok/agents/<slug>.md (spawn_subagent type)."""
    slug = slug_for(name)
    desc = first_sentence(body) or f"{name} persona."
    # Collapse multi-line desc to one line for frontmatter
    desc = " ".join(desc.split())
    prompt_body = rewrite_tools(rewrite_paths(body))
    universal_t = rewrite_tools(rewrite_paths(universal)).strip()

    out = []
    out.append("---")
    out.append(f"name: {slug}")
    out.append(f"description: {desc}")
    out.append(
        "tools: read_file, write, search_replace, run_terminal_command, grep, list_dir"
    )
    out.append("prompt_mode: full")
    out.append("agents_md: true")
    out.append("---")
    out.append("")
    out.append("You are operating inside the BibleMate workspace for Grok Build.")
    out.append("Two universal rules apply to every BibleMate study task:")
    out.append("")
    out.append(universal_t)
    out.append("")
    out.append("Persona definition:")
    out.append("")
    out.append(prompt_body.strip())
    out.append("")
    out.append(
        "When scripture must be quoted, run the `bible` skill "
        '(`python3 .grok/skills/bible/bible_retriever.py "<query>"`). '
        "Save study outputs to the `biblemate/` directory with a "
        "`YYYY-MM-DD-HH-MM-SS_desc.md` timestamp prefix and confirm the path. "
        "Use the `write` tool for file creation. Delegate peer personas with "
        "`spawn_subagent` and `subagent_type` set to the persona slug when useful."
    )
    out.append("")
    return "\n".join(out)


def build_persona_toml(name: str, body: str, universal: str) -> str:
    """Grok persona overlay for .grok/personas/<slug>.toml."""
    slug = slug_for(name)
    desc = first_sentence(body) or f"{name} persona."
    desc = " ".join(desc.split())
    prompt_body = rewrite_tools(rewrite_paths(body)).strip()
    universal_t = rewrite_tools(rewrite_paths(universal)).strip()

    instructions = "\n".join(
        [
            f"You are the BibleMate **{name}** persona for Grok Build.",
            "",
            "Universal BibleMate rules:",
            universal_t,
            "",
            "Persona definition:",
            prompt_body,
            "",
            "When scripture must be quoted, run:",
            '  python3 .grok/skills/bible/bible_retriever.py "<query>"',
            "Save study outputs under biblemate/ with a YYYY-MM-DD-HH-MM-SS_ prefix "
            "using the write tool, and confirm the path.",
        ]
    )

    # Prefer instructions_file for long bodies to keep TOML readable, but
    # inline is more portable (no extra path resolution). Use multi-line string.
    return (
        f'# BibleMate persona: {name}\n'
        f'description = "{toml_escape(desc).replace(chr(34), chr(92) + chr(34))}"\n'
        f'instructions = """\n'
        f"{toml_escape(instructions)}\n"
        f'"""\n'
    )


def _write_grok_update_skill() -> None:
    """Overwrite .grok/skills/update/SKILL.md with a Grok-tailored flow."""
    skill_dir = os.path.join(DST_SKILLS, "update")
    os.makedirs(skill_dir, exist_ok=True)
    skill_md = """---
name: update
description: Refresh the BibleMate Grok Build ecosystem by re-running the local generator against the latest Claude Code (or antigravity) source. Use when the user runs /update or asks to regenerate the .grok ecosystem.
---

# Update Skill (Grok Build)

## Overview
This skill refreshes the self-contained `.grok` BibleMate ecosystem for Grok
Build. Preferred path when `.claude/` is already present: regenerate directly
from Claude Code sources. Optional path: download the remote `manual_setup.zip`
bundle first (ships `.agents/` + `preferences/`), rebuild Claude via
`python3 .claude/build_claude.py` if available, then rebuild Grok.

Everything this skill needs for the Grok rebuild lives inside `.grok/` (this
generator) plus the `.claude/` tree as source.

## Guidelines & Objectives
1. **Verify Operating System**: Only supported on macOS or Linux.
2. **Verify Workspace Folder**: Prefer not to run destructive updates inside a
   workspace named `antigravity-biblemate-workspace` (the source repository)
   unless you intentionally maintain this repo. Confirm with the user first.
3. **Optional download & extract** (if `.claude/` is missing or stale and the
   user wants a remote refresh):
   ```bash
   python3 .grok/skills/update/updater.py
   ```
   If the Claude updater exists, you may also run:
   ```bash
   python3 .claude/skills/update/updater.py
   python3 .claude/build_claude.py
   ```
4. **Regenerate `.grok`**: Rebuild the Grok Build ecosystem from `.claude/`:
   ```bash
   python3 .grok/build_grok.py
   ```
5. **Report Status**: Summarise whether regeneration succeeded, and list the
   number of skills/commands/agents/personas regenerated.
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)


def _write_grok_zip_skill_overlay() -> None:
    """Tailor zip skill to package .grok, preferences, and AGENTS.md."""
    zip_dir = os.path.join(DST_SKILLS, "zip")
    os.makedirs(zip_dir, exist_ok=True)

    skill_md = """---
name: zip
description: Create manual_setup.zip containing .grok/, preferences/, and AGENTS.md for manual Grok Build repository setup. Use when the user runs /zip or requests this BibleMate workflow.
---

# Zip Archive Skill (Grok Build)

## Overview
This skill packages the `.grok/` configuration, root `preferences/`, and root
`AGENTS.md` into a single `manual_setup.zip` at the repository root. That
archive lets users manually import the Grok Build BibleMate personas, skills,
slash commands, and database preferences into a new repository.

## Guidelines & Objectives
When executing this skill:
1. **Remove Existing Archive**: Before creating a new zip file, always check for
   the existence of `manual_setup.zip` in the root of the repository. If it
   exists, delete it first to ensure the archive is built fresh.
2. **Execute Python Helper**: Run the zip creator script:
   ```bash
   python3 .grok/skills/zip/zip_creator.py
   ```
3. **Git Integration**: The script will automatically detect if the repository
   is a Git repository. If it is, and `manual_setup.zip` has modifications, it
   will stage, commit, and push it to the remote repository.
4. **Report Status**: Once the ZIP archive is successfully created and Git
   integration has run, output a clear summary confirming the creation of
   `manual_setup.zip` and the Git synchronization status.
"""
    with open(os.path.join(zip_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)

    # Patch zip_creator.py if present: include AGENTS.md as a root file.
    creator = os.path.join(zip_dir, "zip_creator.py")
    if not os.path.isfile(creator):
        return
    with open(creator, "r", encoding="utf-8") as f:
        src = f.read()
    if "Grok Build ecosystem" in src:
        return
    # Inject root-file packaging after the folders loop setup.
    old = """    # Folders to zip
    folders_to_zip = ['.claude', 'preferences', '.grok']
    files_to_zip = ['AGENTS.md', 'CLAUDE.md']
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in folders_to_zip:
                folder_path = os.path.join(REPO_ROOT, folder)
                if not os.path.exists(folder_path):
                    print(f"Warning: Folder '{folder}' does not exist, skipping.")
                    continue
                # Walk through the folder
                for root, dirs, files in os.walk(folder_path):
                    # Sort dirs and files to ensure deterministic zip order
                    dirs.sort()
                    files.sort()
                    for file in files:
                        file_path = os.path.join(root, file)
                        # The relative path within the zip archive
                        arcname = os.path.relpath(file_path, REPO_ROOT)
                        zipf.write(file_path, arcname)
            for rel in files_to_zip:
                file_path = os.path.join(REPO_ROOT, rel)
                if not os.path.isfile(file_path):
                    print(f"Warning: File '{rel}' does not exist, skipping.")
                    continue
                zipf.write(file_path, rel)
                        
        print(f"Successfully created manual_setup.zip at: {zip_path}")
        print("This zip file includes the '.grok/', 'preferences/', and '.grok/' folders, and the 'AGENTS.md' and 'CLAUDE.md' files, offering users an easy way to set up manually.")
"""
    new = """    # Folders and root files to zip (Grok Build ecosystem)
    folders_to_zip = ['.grok', 'preferences']
    files_to_zip = ['AGENTS.md', 'CLAUDE.md']
    
    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder in folders_to_zip:
                folder_path = os.path.join(REPO_ROOT, folder)
                if not os.path.exists(folder_path):
                    print(f"Warning: Folder '{folder}' does not exist, skipping.")
                    continue
                # Walk through the folder
                for root, dirs, files in os.walk(folder_path):
                    # Sort dirs and files to ensure deterministic zip order
                    dirs.sort()
                    files.sort()
                    for file in files:
                        file_path = os.path.join(root, file)
                        # The relative path within the zip archive
                        arcname = os.path.relpath(file_path, REPO_ROOT)
                        zipf.write(file_path, arcname)
            for rel in files_to_zip:
                file_path = os.path.join(REPO_ROOT, rel)
                if not os.path.isfile(file_path):
                    print(f"Warning: File '{rel}' does not exist, skipping.")
                    continue
                zipf.write(file_path, rel)
                        
        print(f"Successfully created manual_setup.zip at: {zip_path}")
        print("This zip file includes the '.grok/' folder, 'preferences/', and the 'AGENTS.md' and 'CLAUDE.md' files for Grok Build setup.")
"""
    if old in src:
        src = src.replace(old, new)
        with open(creator, "w", encoding="utf-8") as f:
            f.write(src)
    else:
        log("WARNING: zip_creator.py layout unexpected; left path-rewritten copy as-is")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    for required in (SRC_SKILLS, SRC_COMMANDS, SRC_AGENTS_MD, SRC_PREFERENCES):
        if not os.path.exists(required):
            log(f"ERROR: source not found: {required}")
            log("       Build the Claude ecosystem first: python3 .claude/build_claude.py")
            sys.exit(1)

    os.makedirs(DST_GROK, exist_ok=True)

    # 1. Skills
    log("Building .grok/skills ...")
    reset_dir(DST_SKILLS)
    n_skills = 0
    for name in sorted(os.listdir(SRC_SKILLS)):
        if name in SKIP_NAMES:
            continue
        s = os.path.join(SRC_SKILLS, name)
        if not os.path.isdir(s):
            continue
        n_skills += 1
        copy_skill(s, os.path.join(DST_SKILLS, name), name)
    log(f"  {n_skills} skills")

    _write_grok_update_skill()
    _write_grok_zip_skill_overlay()

    # 2. Commands (slash workflows)
    log("Building .grok/commands ...")
    reset_dir(DST_COMMANDS)
    n_cmds = 0
    for name in sorted(os.listdir(SRC_COMMANDS)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(SRC_COMMANDS, name), "r", encoding="utf-8") as f:
            content = f.read()
        content = transform_command_md(content)
        with open(os.path.join(DST_COMMANDS, name), "w", encoding="utf-8") as f:
            f.write(content)
        n_cmds += 1
    log(f"  {n_cmds} commands")

    # 3. Preferences
    log("Building .grok/preferences ...")
    reset_dir(DST_PREFERENCES)
    n_prefs = 0
    for name in sorted(os.listdir(SRC_PREFERENCES)):
        s = os.path.join(SRC_PREFERENCES, name)
        if os.path.isdir(s):
            continue
        shutil.copy2(s, os.path.join(DST_PREFERENCES, name))
        n_prefs += 1
    log(f"  {n_prefs} preference files")

    # 4. agents.md + agents + personas
    log("Building .grok/agents.md, .grok/agents/*, .grok/personas/* ...")
    with open(SRC_AGENTS_MD, "r", encoding="utf-8") as f:
        agents_text = f.read()
    # Parse from Claude-path version before rewrite so headings stay stable
    universal, personas = parse_agents_md(agents_text)
    if len(personas) != len(PERSONA_SLUGS):
        log(
            f"WARNING: found {len(personas)} personas, expected {len(PERSONA_SLUGS)}; "
            "unknown personas will get a generated slug."
        )

    combined = transform_agents_md(agents_text)
    with open(DST_AGENTS_MD, "w", encoding="utf-8") as f:
        f.write(combined)

    reset_dir(DST_AGENTS_DIR)
    reset_dir(DST_PERSONAS_DIR)
    n_agents = 0
    for name, body in personas:
        slug = slug_for(name)
        agent_md = build_agent_md(name, body, universal)
        with open(os.path.join(DST_AGENTS_DIR, f"{slug}.md"), "w", encoding="utf-8") as f:
            f.write(agent_md)
        persona_toml = build_persona_toml(name, body, universal)
        with open(
            os.path.join(DST_PERSONAS_DIR, f"{slug}.toml"), "w", encoding="utf-8"
        ) as f:
            f.write(persona_toml)
        n_agents += 1
    log(f"  {n_agents} agents + {n_agents} personas")

    log("Done.")
    log(
        f"Summary: {n_skills} skills, {n_cmds} commands, "
        f"{n_agents} agents, {n_agents} personas, {n_prefs} preferences"
    )


if __name__ == "__main__":
    main()
