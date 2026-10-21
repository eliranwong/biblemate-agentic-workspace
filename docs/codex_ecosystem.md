# Codex Ecosystem Guide

This guide explains how to use the **BibleMate** study suite in **Codex**. The Codex port is a parallel skill ecosystem—equivalent in study coverage to the Antigravity (`.agents/`), Claude Code (`.claude/`), Grok Build (`.grok/`), and Cursor (`.cursor/`) ports—and lives under `.codex/`.

It runs alongside the other platforms. You can use Antigravity, Claude Code, Codex, Grok Build, and Cursor against the same workspace and the same local Bible databases.

---

## Prerequisites

1. **Codex** installed or available in your development environment.
2. **This repository** opened as the workspace root, so Codex can use `.codex/skills/` and `.codex/AGENTS.md`.
3. **Local Bible data** (not bundled in the repo—files are large):
   Install via `biblematedata`:
   ```bash
   pip install --upgrade biblematedata
   biblematedata
   ```
   *Or use the alternate direct download of `data.zip` from [MEGA](https://mega.nz/file/SaBkhRZA#H10dm7nCbShAO1xHo2dWhOWaX3eda8Y-R83v225jBYw) (QR code: `docs/download_data_qr_code.png`) and unpack to `~/biblemate/data` via `./scripts/download_data.sh`.*

   Data lands under `~/biblemate/data` by default. To point elsewhere:

   ```bash
   export BIBLEMATE_DATA="/path/to/your/biblemate"
   ```

4. **Python 3** on your `PATH` (retrievers and orchestrators are Python scripts).
5. **Optional web app dependencies** if you want the browser UI:
   ```bash
   pip install nicegui Pillow
   ```

---

## What gets loaded

When you work in Codex:

| Asset | Location | How Codex uses it |
| :--- | :--- | :--- |
| Codex notes | `.codex/AGENTS.md` | Codex-native usage notes: scripture integrity, save rules, and tool conventions |
| Skills | `.codex/skills/<name>/SKILL.md` | 125 Codex skills. Applied when you name the workflow or when the request matches the skill description |
| Persona reference | `.codex/agents.md` | Tone and guidelines for the 15 study personas |
| Preferences | `.codex/preferences/` | Default bible / commentary / lexicon versions for retrievers |
| Generator | `.codex/build_codex.py` | Rebuilds this tree from `.agents/` + `preferences/` |

Each workflow is a skill. You can use the familiar slash-style names in prompts, such as `/bible NET John 3:16` or `/sermon Romans 8:28`; Codex reads the matching `.codex/skills/<name>/SKILL.md` before acting.

Book search skills use Codex-compatible lowercase paths such as `.codex/skills/gen/` and `.codex/skills/1cor/`, while their descriptions still recognize familiar BibleMate names such as `/Gen` and `/1Cor`.

---

## Layout (portable paths only)

```
.codex/
  build_codex.py                 # regenerate skills from .agents/ + preferences/
  AGENTS.md                      # Codex-specific usage notes
  agents.md                      # 15 personas (combined reference)
  preferences/                   # bible.md, commentary.md, lexicon.md
  skills/<name>/SKILL.md         # 125 skills (+ scripts where needed)
```

Skill instructions use **relative** paths such as `.codex/skills/bible/bible_retriever.py`. Keep study links relative to the repo as well.

---

## Universal rules

These apply to every BibleMate study in Codex (also stated in `.codex/AGENTS.md` and `.codex/agents.md`):

### 1. Scripture integrity

Never quote Bible text from memory. Fetch verses via the `bible` skill:

```bash
python3 .codex/skills/bible/bible_retriever.py "NET John 3:16"
```

Or ask Codex:

```text
/bible NET John 3:16
```

### 2. Save study output

For bible-related skills **except** `biblemate`, `biblemate-super`, `image`, `data`, `sync`, `md`, `docx`, and `zip`, save the full study output under `biblemate/` with a timestamp prefix:

```text
biblemate/YYYY-MM-DD-HH-MM-SS_short_description.md
```

Example:

```text
biblemate/2026-07-11-09-30-00_romans_8_devotion.md
```

Get a timestamp:

```bash
python3 -c "import datetime; print(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))"
```

Use Codex file-editing tools to create the file, and confirm the saved path in the final reply.

---

## Everyday usage

Ask for the workflow using the same names as the other platforms. Examples:

```text
/bible NET John 3:16
/devotion Romans 8:28
/sermon Psalm 23
/testimony George Muller provision
/keywords Ephesians 2:1-10
/commentary BNC John 3:16
/lexicon G26
/Gen "In the beginning" NET
/biblemate Write an expository study on Ezra 5
/biblemate-super Sermon series seed: standing firm in Ezra
```

The same requests work in plain language (“retrieve NET John 3:16”, “write a devotion on Romans 8:28”). The agent reads `.codex/skills/<name>/SKILL.md` and runs the Python helper that skill names.

Full command catalog: [slash_commands.md](slash_commands.md). Codex uses the same workflow names, including the refresh skill `update-biblemate`.

### Standalone Web App

Run the browser-based UI backed by your signed-in Codex CLI:

```bash
python3 web_app_codex.py
```

Then open [http://localhost:33376](http://localhost:33376). Override the port with `BIBLEMATE_CODEX_PORT=<port>`.

The app runs `codex exec --json` in headless mode, streams JSONL events into the live execution console, loads personas and skills from `.codex/`, and writes outputs to the same `biblemate/`, `images/`, and `export/` folders as the other platform apps.

### `/testimony` (real-life and missionary stories)

Ask for a **verified** real-life or missionary testimony (never a fabricated story):

```text
/testimony George Muller provision
/testimony Corrie ten Boom forgiveness
```

The skill searches a local registry first:

```bash
python3 .codex/skills/testimony/testimony_retriever.py "George Muller"
```

If there is no local match, the agent researches online and still provides biographical background plus fact-checkable sources. Outputs save under `biblemate/` as `YYYY-MM-DD-HH-MM-SS_testimony_<slug>.md`. The same skill is a recommended option inside **`biblemate`** and **`biblemate-super`**.

### Orchestrated deep studies

| Skill | Purpose |
| :--- | :--- |
| **`biblemate`** | Multi-phase orchestrated study: plan → local data retrieval → exegesis → theology → application → pre-final overview → iterative final manuscript |
| **`biblemate-super`** | Dynamically planned multi-phase study with quality-audit checkpoints and persona rotation |

Both write step files under `biblemate/` (timestamped study folders). They enforce local `bible` retrieval and do not quote Scripture from memory.

### Book search skills

Each Protestant canon book has a search skill (for example `gen`, `john`, `rom`, `ps`):

```text
/Ps "The Lord is my shepherd"
/John love + world NET
```

### Utility skills

| Skill | Purpose |
| :--- | :--- |
| `data` | List installed bible / commentary / lexicon versions |
| `sync` | Git add, commit, and push workspace changes |
| `md` / `docx` | Export content to `export/md` or `export/docx` |
| `image` | Generate bible-related images into `images/` |
| `zip` | Build `manual_setup.zip` with the shared BibleMate platform bundle |
| `update-biblemate` | Refresh sources and regenerate the `.codex` skills |

---

## Personas

There are **15** study personas. Profiles: [ai_team_personas.md](ai_team_personas.md). Combined Codex reference: `.codex/agents.md`.

| Slug | Role (short) |
| :--- | :--- |
| `verse-scripter` | Multi-verse scripture retrieval and presentation |
| `compassionate-pastor` | Pastoral tone, first-person prayers, devotion |
| `passionate-evangelist` | Gospel-centered proclamation |
| `ot-bible-scholar` | Old Testament / Hebrew Bible scholarship |
| `nt-bible-scholar` | New Testament / Koine Greek scholarship |
| `biblical-theologian` | Redemptive-historical, canonical theology |
| `systematic-theologian` | Doctrinal theme structure |
| `biblical-translator` | Translation and word mapping |
| `biblical-linguistic-analyst` | Greek/Hebrew grammar and lexicon |
| `bible-textual-critic` | Versions, manuscripts, data-driven text work |
| `biblical-content-interpreter` | Contemporary content through a biblical lens |
| `context-analyst-david` | Davidic / Psalms life-context analysis |
| `master-biblical-writer` | Publication-quality iterative final drafts |
| `study-quality-auditor` | Study plans and phase quality gates |
| `ai-agent-creator` | Designing Bible-study agent systems |

### How to use them in Codex

1. **Study skills** adopt a persona by reading `.codex/agents.md` (for example devotion follows the Compassionate Pastor).
2. **Specialist delegation** may be used when Codex subagent tools are available in the current session.
3. **`biblemate` / `biblemate-super`** rotate personas by phase and record which persona each step uses.

---

## Codex tool mapping

Skills refer to Codex-native tools and conventions:

| Need | Tool / convention |
| :--- | :--- |
| Read/search files | `rg`, `rg --files`, `sed`, `ls`, and related shell inspection commands through `exec_command` |
| Create or edit repository files | `apply_patch` |
| Run Python retrievers / shell commands | `exec_command` |
| Search the web | `web.run` when current or online sources are required |
| Delegate a persona task | Codex subagent tools, when available in the current turn |

Example retriever invocations:

```bash
python3 .codex/skills/bible/bible_retriever.py "NET John 3:16"
python3 .codex/skills/commentary/commentary_retriever.py "BNC Romans 8:28"
python3 .codex/skills/lexicon/lexicon_retriever.py "G26"
python3 .codex/skills/original/original_retriever.py "John 1:1"
python3 .codex/skills/data/data_lister.py bible
```

---

## Runtime data and preferences

| Resource | Default install location |
| :--- | :--- |
| Bibles | `~/biblemate/data/bibles` (and optional `data_custom/bibles`) |
| Commentaries | `~/biblemate/data/commentaries` |
| Lexicons | under the biblemate data tree |
| Morphology / xrefs / etc. | under the biblemate data tree |

Default versions for queries that omit an explicit version are read from:

- `.codex/preferences/bible.md`
- `.codex/preferences/commentary.md`
- `.codex/preferences/lexicon.md`

Resolution order for the data root:

1. `BIBLEMATE_DATA` environment variable
2. `~/biblemate`

The shared root [`preferences/`](../preferences) folder is the human-edited default. Regenerating `.codex/` copies those versions into `.codex/preferences/`.

---

## Where outputs go

See also [study_outputs.md](study_outputs.md).

| Output type | Location |
| :--- | :--- |
| Standard study files | `biblemate/YYYY-MM-DD-HH-MM-SS_*.md` |
| Orchestrated multi-step studies | `biblemate/<timestamp>_<title>/` with `NNN-skill.md` steps |
| Images | `images/` |
| Markdown / Word exports | `export/md/`, `export/docx/` |
| Manual setup archive | `manual_setup.zip` (repo root, via the `zip` skill) |

Use **relative** links between study files (for example `[005-keywords.md](005-keywords.md)`).

---

## Regenerating the Codex skills

Content is generated from the Antigravity tree (`.agents/`) plus shared `preferences/`:

```bash
# Rebuild Codex skills, preferences, and agents.md
python3 .codex/build_codex.py
```

The Codex generator is **idempotent**. It rewrites only:

- `.codex/skills/`
- `.codex/preferences/`
- `.codex/agents.md`

It leaves `.codex/build_codex.py`, `.codex/AGENTS.md`, `.agents/`, `.claude/`, `.grok/`, and `.cursor/` unchanged.

From Codex you can also ask the agent to run the `update-biblemate` skill, which follows the same refresh path.

---

## Quick start checklist

1. Open this repository in Codex.
2. Confirm `.codex/AGENTS.md` and `.codex/skills/` are present.
3. Install data: `pip install --upgrade biblematedata` and run `biblematedata`.
4. Smoke-test: `/bible NET John 3:16`.
5. Run a small study: `/devotion Romans 8:28` and confirm a file under `biblemate/`.
6. For a deep dive: `/biblemate` with a clear passage or topic request.

---

## Platform coexistence

| Platform | Config tree | Project rules |
| :--- | :--- | :--- |
| Google Antigravity | `.agents/` | (Antigravity conventions) |
| Claude Code | `.claude/` | `CLAUDE.md` |
| Codex | `.codex/` | `.codex/AGENTS.md` |
| Grok Build | `.grok/` | `AGENTS.md` |
| Cursor | `.cursor/` | `.cursor/rules/biblemate-skills.mdc` |

Shared across platforms:

- Local Bible / commentary / lexicon databases (`BIBLEMATE_DATA` or `~/biblemate`)
- Study outputs in `biblemate/`, `images/`, `export/`
- Skill **names** (the same `bible`, `sermon`, `biblemate`, book skills, and so on)

When regenerating one platform's tree, leave the others untouched unless you intend to update them.

---

## Troubleshooting

| Symptom | What to try |
| :--- | :--- |
| Agent quotes a verse without running a retriever | Ask it to follow `.codex/skills/bible/SKILL.md`; run `python3 .codex/skills/bible/bible_retriever.py "VERSION REF"` |
| Empty or missing verse text | Run the `data` skill, or `python3 .codex/skills/data/data_lister.py bible`; install/upgrade `biblematedata`; check `BIBLEMATE_DATA` |
| Agent follows another platform's skills | Say “follow the skill in `.codex/skills/`” and verify the repo root is the working directory |
| Wrong tool paths in a skill | Re-run `python3 .codex/build_codex.py` so instructions point at `.codex/skills/...` |
| Persona voice is generic | Point the agent at `.codex/agents.md` |
| Preference version ignored | Edit `.codex/preferences/*.md`, or edit root `preferences/` and regenerate |
| Paths break on another machine | Keep retriever paths relative and Bible data behind `BIBLEMATE_DATA` or `~/biblemate` |

---

## Related docs

- [slash_commands.md](slash_commands.md) — full command reference (refresh skill: `update-biblemate`)
- [ai_team_personas.md](ai_team_personas.md) — persona profiles
- [study_outputs.md](study_outputs.md) — where studies and exports are saved
- [claude_code_ecosystem.md](claude_code_ecosystem.md) — Claude Code port
- [grok_build_ecosystem.md](grok_build_ecosystem.md) — Grok Build port
- [cursor_ecosystem.md](cursor_ecosystem.md) — Cursor port
- [`.codex/AGENTS.md`](../.codex/AGENTS.md) — Codex usage notes
- [`.codex/agents.md`](../.codex/agents.md) — combined persona definitions for Codex
