# BibleMate for Claude Code

This repository ships a **BibleMate** study ecosystem that runs entirely on
Claude Code. The Claude Code port lives in `.claude/` and is **self-contained**:
its skills, commands, subagents, supporting scripts, and preference files all
live under `.claude/` and use only relative paths, so the workspace is portable.

> The original antigravity-platform configuration is untouched in `.agents/`.
> `.claude/` is a parallel ecosystem generated from it by
> `python3 .claude/build_claude.py`. Re-run that generator after editing
> `.agents/` or `preferences/` to refresh `.claude/`.

## Layout

```
.claude/
  build_claude.py          # regenerates the .claude ecosystem from .agents + preferences
  settings.json            # permissions + env for the workspace
  agents.md                # combined persona reference (paths ported to .claude)
  preferences/             # default bible/commentary/lexicon version files
  skills/<name>/SKILL.md   # 124 skills (Claude Code Agent Skills)
  commands/<name>.md       # 124 slash commands (from .agents/workflows)
  agents/<slug>.md         # 15 subagents (one per persona in agents.md)
```

Skills and commands share the same names as the antigravity workflows, so you
invoke them the same way: `/bible`, `/sermon`, `/devotion`, `/biblemate`,
`/Gen` (book search), `/data`, `/sync`, etc.

## Universal rules (apply to every BibleMate study)

1. **Scripture integrity.** Never quote Bible text from memory. Run the `bible`
   skill to fetch verses from the local SQLite databases:
   ```bash
   python3 .claude/skills/bible/bible_retriever.py "NET John 3:16"
   ```
2. **Save study output.** For every bible-related skill/command except
   `biblemate`, `biblemate-super`, `image`, `data`, `sync`, `md`, `docx`, and
   `zip`, save the full study output to the `biblemate/` directory with a
   timestamp prefix:
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

Override it in `.claude/settings.json` (`env.BIBLEMATE_DATA`) if your data lives
elsewhere.

## Subagents (personas)

Fifteen personas from `.agents/agents.md` are available as Claude Code subagents
in `.claude/agents/` (e.g. `verse-scripter`, `compassionate-pastor`,
`ot-bible-scholar`, `biblical-content-interpreter`). Slash commands adopt the
appropriate persona via `.claude/agents.md`; you can also delegate to a persona
subagent directly with the Task tool.

## Refreshing the ecosystem

```bash
python3 .claude/build_claude.py   # regenerate .claude from .agents + preferences
```
The generator is idempotent and only rewrites `skills/`, `commands/`, `agents/`,
`preferences/`, and `agents.md` under `.claude/`.