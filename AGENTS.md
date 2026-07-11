# BibleMate for Grok Build

This repository ships a **BibleMate** study ecosystem that runs on Grok Build.
The Grok port lives in `.grok/` and is **self-contained**: its skills, slash
commands, agent definitions, personas, supporting scripts, and preference files
all live under `.grok/` and use only relative paths, so the workspace is portable.

> The original Antigravity configuration remains in `.agents/`.
> The Claude Code port remains in `.claude/`.
> `.grok/` is a parallel ecosystem generated from `.claude/` by
> `python3 .grok/build_grok.py`. Re-run that generator after refreshing
> `.claude/` (or after editing skills/commands you want mirrored) to update
> `.grok/`.

## Layout

```
.grok/
  build_grok.py            # regenerates the .grok ecosystem from .claude
  agents.md                # combined persona reference (paths ported to .grok)
  preferences/             # default bible/commentary/lexicon version files
  skills/<name>/SKILL.md   # ~125 skills (Grok Agent Skills + slash commands)
  commands/<name>.md       # ~125 slash command workflows
  agents/<slug>.md         # 15 agent definitions (spawn_subagent types)
  personas/<slug>.toml     # 15 persona overlays for subagents
```

Skills and commands share the same names as the Antigravity / Claude workflows,
so you invoke them the same way: `/bible`, `/sermon`, `/devotion`, `/biblemate`,
`/Gen` (book search), `/data`, `/sync`, etc.

## Universal rules (apply to every BibleMate study)

1. **Scripture integrity.** Never quote Bible text from memory. Run the `bible`
   skill to fetch verses from the local SQLite databases:
   ```bash
   python3 .grok/skills/bible/bible_retriever.py "NET John 3:16"
   ```
2. **Save study output.** For every bible-related skill/command except
   `biblemate`, `biblemate-super`, `image`, `data`, `sync`, `md`, `docx`, and
   `zip`, save the full study output to the `biblemate/` directory with a
   timestamp prefix using the `write` tool:
   ```bash
   python3 -c "import datetime; print(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))"
   # e.g. biblemate/2026-07-11-09-30-00_romans_8_devotion.md
   ```
   Confirm the saved path to the user.

## Runtime data

Bible/commentary/lexicon/morphology/cross-reference databases are **not** bundled
(they are large). Install them once via the `biblematedata` package so they land
in `~/biblemate/data`:

```bash
pip install --upgrade biblematedata
```

The retriever scripts resolve the data root in this order, so the workspace stays
portable (no hardcoded absolute paths):

1. the `BIBLEMATE_DATA` environment variable (set it to point anywhere), else
2. `~/biblemate` (the standard install location).

## Agents and personas

Fifteen BibleMate personas are available in two Grok-native forms:

| Form | Location | How to use |
|------|----------|------------|
| **Agents** | `.grok/agents/<slug>.md` | `spawn_subagent` with `subagent_type` set to the slug (e.g. `verse-scripter`, `ot-bible-scholar`) |
| **Personas** | `.grok/personas/<slug>.toml` | Behavioral overlays discovered by Grok Build (`/personas`) |

Slash command workflows adopt the appropriate persona via `.grok/agents.md`.
Combined reference: `.grok/agents.md`.

Example personas: `verse-scripter`, `compassionate-pastor`, `ot-bible-scholar`,
`nt-bible-scholar`, `biblical-content-interpreter`, `master-biblical-writer`,
`study-quality-auditor`.

## Grok tool mapping

When skill or persona text refers to file/shell operations, prefer these Grok tools:

| Action | Tool |
|--------|------|
| Read a file | `read_file` |
| Create/overwrite a file | `write` |
| Edit a file | `search_replace` |
| Run shell / python retrievers | `run_terminal_command` |
| Search code | `grep` |
| List directories | `list_dir` |
| Delegate a persona | `spawn_subagent` |

## Refreshing the ecosystem

```bash
# Optional: refresh Claude first from .agents + preferences
python3 .claude/build_claude.py

# Regenerate the Grok ecosystem from .claude
python3 .grok/build_grok.py
```

The Grok generator is idempotent and only rewrites `skills/`, `commands/`,
`agents/`, `personas/`, `preferences/`, and `agents.md` under `.grok/`.

## Platform coexistence

You may use Antigravity (`.agents/`), Claude Code (`.claude/`), and Grok Build
(`.grok/`) against the same workspace and the same local Bible databases. Do not
modify one platform's tree when regenerating another unless intentionally
updating that platform.
