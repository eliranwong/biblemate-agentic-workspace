#!/usr/bin/env python3
"""
build_claude.py — Port the antigravity `.agents` biblemate ecosystem into a
self-contained, portable Claude Code `.claude` ecosystem.

Produces (all relative; no absolute paths):
  .claude/skills/<name>/...        <- from .agents/skills/<name>/...
  .claude/commands/<name>.md       <- from .agents/workflows/<name>.md
  .claude/agents/<slug>.md         <- one subagent per persona in .agents/agents.md
  .claude/agents.md                <- combined persona reference (paths fixed)
  .claude/preferences/...          <- from ./preferences/...

Text transforms applied so the Claude Code copies work independently of the
`.agents` directory:
  * `.agents/skills/`            -> `.claude/skills/`
  * `.agents/agents.md`         -> `.claude/agents.md`
  * persona-adoption lines point to `.claude/agents.md`
  * workflow `$1 $2 ... $N` placeholder lines -> `$ARGUMENTS` (Claude Code
    uses 0-based `$N`; antigravity used 1-based for "all input")
  * preferences path in retrievers -> `.claude/preferences` (2 levels up)
  * data dir resolution honours `BIBLEMATE_DATA` env var (defaults to
    `~/biblemate`), so the runtime Bible data can live anywhere

This script is idempotent. It only rewrites the skills/commands/agents/
preferences subtrees and the combined agents.md; it never touches
build_claude.py, settings.json, settings.local.json, or CLAUDE.md.
"""
import os
import re
import shutil
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC_AGENTS = os.path.join(REPO_ROOT, ".agents")
SRC_SKILLS = os.path.join(SRC_AGENTS, "skills")
SRC_WORKFLOWS = os.path.join(SRC_AGENTS, "workflows")
SRC_AGENTS_MD = os.path.join(SRC_AGENTS, "agents.md")
SRC_PREFERENCES = os.path.join(REPO_ROOT, "preferences")

DST_CLAUDE = os.path.join(REPO_ROOT, ".claude")
DST_SKILLS = os.path.join(DST_CLAUDE, "skills")
DST_COMMANDS = os.path.join(DST_CLAUDE, "commands")
DST_AGENTS_DIR = os.path.join(DST_CLAUDE, "agents")
DST_AGENTS_MD = os.path.join(DST_CLAUDE, "agents.md")
DST_PREFERENCES = os.path.join(DST_CLAUDE, "preferences")

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


def log(msg):
    print(msg, flush=True)


def reset_dir(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------------------------
# Text transforms
# ---------------------------------------------------------------------------

def rewrite_paths(text):
    """Rewrite `.agents/...` references to `.claude/...` equivalents."""
    # Generic skill / agents references in prose and code strings.
    text = text.replace(".agents/skills/", ".claude/skills/")
    text = text.replace(".agents/agents.md", ".claude/agents.md")
    # Orchestrator discovery: os.path.join(workspace_root, ".agents", "skills")
    text = text.replace('".agents", "skills"', '".claude", "skills"')
    text = text.replace("'.agents', 'skills'", "'.claude', 'skills'")
    # Inline comments describing script location: <root>/.agents/skills/...
    text = text.replace("/.agents/skills/", "/.claude/skills/")
    # zip_creator bundles the ecosystem folders for manual setup.
    text = text.replace("['.agents', 'preferences']", "['.claude', 'preferences']")
    text = text.replace("'.agents/' and 'preferences/'", "'.claude/' and 'preferences/'")
    text = text.replace("'.agents/'", "'.claude/'")
    # Any remaining bare ".agents/" directory token (prose) -> ".claude/".
    text = text.replace(".agents/", ".claude/")
    # Bare backtick ".agents" config references -> ".claude".
    text = text.replace("`.agents`", "`.claude`")
    # Antigravity tool names -> Claude Code equivalents.
    text = text.replace("the `write_to_file` tool", "the `Write` tool")
    text = text.replace("`write_to_file`", "`Write`")
    text = text.replace("the `view_file` tool", "the `Read` tool")
    text = text.replace("`view_file`", "`Read`")
    return text


def rewrite_preferences_path(text):
    """Point bible/commentary/lexicon retrievers at .claude/preferences.

    Original: os.path.join(script_dir, '..', '..', '..', 'preferences', X)
    Script lives at .claude/skills/<name>/<script>.py, so two '..' reach .claude.
    """
    text = text.replace(
        "os.path.join(script_dir, '..', '..', '..', 'preferences'",
        "os.path.join(script_dir, '..', '..', 'preferences'",
    )
    text = text.replace(
        "os.path.join(SCRIPT_DIR, '..', '..', '..', 'preferences'",
        "os.path.join(SCRIPT_DIR, '..', '..', 'preferences'",
    )
    return text


def add_data_env_portability(text):
    """Let BIBLEMATE_DATA override the biblemate data root (default ~/biblemate).

    Only touches scripts that build paths via os.path.join(home, 'biblemate', ...).
    `base` = the directory that contains `data/`, `data_custom/`, etc.
    """
    if "os.path.join(home, 'biblemate'," not in text:
        return text
    if "base = os.environ.get('BIBLEMATE_DATA')" in text:
        # Already patched; still normalise the join calls below.
        pass
    else:
        # Inject `base = ...` after each `home = os.path.expanduser('~')`,
        # preserving indentation.
        text = re.sub(
            r"([ \t]*)home = os\.path\.expanduser\('~'\)",
            r"\1home = os.path.expanduser('~')\n\1base = os.environ.get('BIBLEMATE_DATA') or os.path.join(home, 'biblemate')",
            text,
        )
    text = text.replace("os.path.join(home, 'biblemate',", "os.path.join(base,")
    return text


def fix_morphology_bare_expanduser(text):
    """Handle morphology_retriever's direct expanduser('~/biblemate/data/...')."""
    text = text.replace(
        "os.path.expanduser('~/biblemate/data/morphology.sqlite')",
        "os.path.join(os.environ.get('BIBLEMATE_DATA') or os.path.join(os.path.expanduser('~'), 'biblemate'), 'data', 'morphology.sqlite')",
    )
    return text


def transform_python(text):
    text = rewrite_paths(text)
    text = rewrite_preferences_path(text)
    text = add_data_env_portability(text)
    text = fix_morphology_bare_expanduser(text)
    return text


def transform_skill_md(text):
    text = rewrite_paths(text)
    return text


def transform_command_md(text):
    text = rewrite_paths(text)
    # Convert 1-based "all input" placeholder lines ($1 $2 ... $N) to $ARGUMENTS.
    # Claude Code $N is 0-based; antigravity used $1..$10 to mean "everything".
    text = re.sub(r"^[ \t]*\$1(?:[ \t]+\$\d+)*[ \t]*$", "$ARGUMENTS", text, flags=re.MULTILINE)
    # Catch a leading lone $1 (single-token input) as well.
    text = re.sub(r"^[ \t]*\$1[ \t]*$", "$ARGUMENTS", text, flags=re.MULTILINE)
    return text


# ---------------------------------------------------------------------------
# Copy helpers
# ---------------------------------------------------------------------------

def copy_tree_transformed(src, dst, file_transform, dir_filter=None):
    """Copy a directory tree, applying file_transform to file contents."""
    os.makedirs(dst, exist_ok=True)
    for name in sorted(os.listdir(src)):
        if name in SKIP_NAMES:
            continue
        spath = os.path.join(src, name)
        dpath = os.path.join(dst, name)
        if os.path.isdir(spath):
            if dir_filter and not dir_filter(name, spath):
                continue
            copy_tree_transformed(spath, dpath, file_transform, dir_filter)
        else:
            with open(spath, "r", encoding="utf-8") as f:
                content = f.read()
            content = file_transform(content, name, spath) if file_transform.__code__.co_argcount == 3 else file_transform(content)
            with open(dpath, "w", encoding="utf-8") as f:
                f.write(content)


def copy_skill(src_skill, dst_skill):
    def file_tf(content, name, spath):
        if name == "SKILL.md":
            return transform_skill_md(content)
        if name.endswith(".py"):
            return transform_python(content)
        return content
    copy_tree_transformed(src_skill, dst_skill, file_tf)


# ---------------------------------------------------------------------------
# Persona / subagent generation
# ---------------------------------------------------------------------------

def parse_agents_md(text):
    """Return (universal_header, [(persona_name, body), ...])."""
    # Universal header = everything before the first "## " persona heading.
    first = text.find("\n## ")
    if first == -1:
        return text, []
    universal = text[:first].rstrip()
    rest = text[first + 1:]

    # Split on "\n## " headings.
    parts = re.split(r"\n(?=## )", rest)
    personas = []
    for part in parts:
        part = part.strip()
        if not part.startswith("## "):
            continue
        name = part[3:].splitlines()[0].strip()
        personas.append((name, part))
    return universal, personas


def first_sentence(body):
    """Grab the one-line description that follows the persona heading."""
    lines = body.splitlines()
    desc = ""
    for ln in lines[1:]:
        ln = ln.strip()
        if ln and not ln.startswith("#") and not ln.startswith("---"):
            desc = ln
            break
    return desc


def build_subagent_md(name, body, universal):
    slug = PERSONA_SLUGS.get(name)
    desc = first_sentence(body) or f"{name} persona."
    # Body already includes the "## Name" heading; convert to a single system prompt.
    prompt_body = body
    prompt_body = rewrite_paths(prompt_body)

    tools = "Read, Write, Edit, Bash, Grep, Glob"
    out = []
    out.append("---")
    out.append(f"name: {slug}")
    out.append(f"description: {desc}")
    out.append(f"tools: {tools}")
    out.append("---")
    out.append("")
    out.append("You are operating inside the BibleMate workspace for Claude Code.")
    out.append("Two universal rules apply to every BibleMate study task:")
    out.append("")
    out.append(rewrite_paths(universal).strip())
    out.append("")
    out.append("Persona definition:")
    out.append("")
    out.append(prompt_body.strip())
    out.append("")
    out.append(
        "When scripture must be quoted, run the `bible` skill "
        "(`python3 .claude/skills/bible/bible_retriever.py \"<query>\"`). "
        "Save study outputs to the `biblemate/` directory with a "
        "`YYYY-MM-DD-HH-MM-SS_desc.md` timestamp prefix and confirm the path."
    )
    return "\n".join(out) + "\n"


def _write_claude_update_skill():
    """Overwrite .claude/skills/update/SKILL.md with a Claude-tailored flow."""
    skill_dir = os.path.join(DST_SKILLS, "update")
    os.makedirs(skill_dir, exist_ok=True)
    skill_md = """---
name: update
description: Refresh the BibleMate Claude Code ecosystem by re-running the local generator against the latest .agents/preferences source.
---

# Update Skill (Claude Code)

## Overview
This skill refreshes the self-contained `.claude` BibleMate ecosystem for Claude
Code. It (1) downloads the latest `manual_setup.zip` bundle (which ships the
`.agents/` personas/skills/workflows and `preferences/`), (2) extracts it into
the workspace, and (3) regenerates `.claude/` by running the local generator
`python3 .claude/build_claude.py`.

Everything this skill needs lives inside `.claude/` (the generator) plus the
remote bundle; it does not depend on any other local files outside `.claude/`.

## Guidelines & Objectives
1. **Verify Operating System**: Only supported on macOS or Linux.
2. **Verify Workspace Folder**: The updater refuses to run inside a workspace
   named `antigravity-biblemate-workspace` (the source repository) to avoid
   overwriting source files. Run it in your own copy/fork instead.
3. **Download & Extract**: Run the updater helper:
   ```bash
   python3 .claude/skills/update/updater.py
   ```
   This fetches `manual_setup.zip` and extracts `.agents/` and `preferences/`
   into the workspace root.
4. **Regenerate `.claude`**: Rebuild the Claude Code ecosystem from the freshly
   extracted source:
   ```bash
   python3 .claude/build_claude.py
   ```
5. **Report Status**: Summarise whether the download, extraction, and rebuild
   succeeded, and list the number of skills/commands/agents regenerated.
"""
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(skill_md)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    for required in (SRC_SKILLS, SRC_WORKFLOWS, SRC_AGENTS_MD, SRC_PREFERENCES):
        if not os.path.exists(required):
            log(f"ERROR: source not found: {required}")
            sys.exit(1)

    os.makedirs(DST_CLAUDE, exist_ok=True)

    # 1. Skills
    log("Building .claude/skills ...")
    reset_dir(DST_SKILLS)
    n_skills = 0
    for name in sorted(os.listdir(SRC_SKILLS)):
        if name in SKIP_NAMES:
            continue
        s = os.path.join(SRC_SKILLS, name)
        if not os.path.isdir(s):
            continue
        n_skills += 1
        copy_skill(s, os.path.join(DST_SKILLS, name))
    log(f"  {n_skills} skills")

    # Tailor the `update` skill for the Claude Code ecosystem: refresh the
    # `.agents`/`preferences` source from the remote bundle, then regenerate
    # `.claude` via build_claude.py. (Original was antigravity-platform-only.)
    _write_claude_update_skill()

    # 2. Commands (workflows)
    log("Building .claude/commands ...")
    reset_dir(DST_COMMANDS)
    n_cmds = 0
    for name in sorted(os.listdir(SRC_WORKFLOWS)):
        if not name.endswith(".md"):
            continue
        with open(os.path.join(SRC_WORKFLOWS, name), "r", encoding="utf-8") as f:
            content = f.read()
        content = transform_command_md(content)
        with open(os.path.join(DST_COMMANDS, name), "w", encoding="utf-8") as f:
            f.write(content)
        n_cmds += 1
    log(f"  {n_cmds} commands")

    # 3. Preferences
    log("Building .claude/preferences ...")
    reset_dir(DST_PREFERENCES)
    for name in sorted(os.listdir(SRC_PREFERENCES)):
        s = os.path.join(SRC_PREFERENCES, name)
        if os.path.isdir(s):
            continue
        shutil.copy2(s, os.path.join(DST_PREFERENCES, name))
    log(f"  {len(os.listdir(DST_PREFERENCES))} preference files")

    # 4. agents.md + subagents
    log("Building .claude/agents.md and .claude/agents/* ...")
    with open(SRC_AGENTS_MD, "r", encoding="utf-8") as f:
        agents_text = f.read()
    universal, personas = parse_agents_md(agents_text)
    if len(personas) != len(PERSONA_SLUGS):
        log(
            f"WARNING: found {len(personas)} personas, expected {len(PERSONA_SLUGS)}; "
            "new personas will get a generated slug."
        )

    # Combined reference doc (paths fixed).
    combined = rewrite_paths(agents_text)
    with open(DST_AGENTS_MD, "w", encoding="utf-8") as f:
        f.write(combined)

    reset_dir(DST_AGENTS_DIR)
    n_agents = 0
    for name, body in personas:
        slug = PERSONA_SLUGS.get(name)
        if not slug:
            slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "persona"
        md = build_subagent_md(name, body, universal)
        with open(os.path.join(DST_AGENTS_DIR, f"{slug}.md"), "w", encoding="utf-8") as f:
            f.write(md)
        n_agents += 1
    log(f"  {n_agents} subagents")

    log("Done.")


if __name__ == "__main__":
    main()