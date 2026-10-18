# Cursor Ecosystem Guide

This guide explains how to use the **BibleMate** study suite in **Cursor**. The Cursor port is a parallel set of project skills and a project rule—equivalent in study coverage to the Antigravity (`.agents/`), Claude Code (`.claude/`), and Grok Build (`.grok/`) ports—and lives under `.cursor/`.

It runs alongside the other platforms. You can use Antigravity, Claude Code, Grok Build, and Cursor against the same workspace and the same local Bible databases.

---

## Prerequisites

1. **Cursor** installed and signed in ([Cursor](https://cursor.com)).
2. **This repository** opened as the project root, so Cursor loads `.cursor/rules/` and `.cursor/skills/`.
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

---

## What gets loaded

When you open this repo in Cursor:

| Asset | Location | How Cursor uses it |
| :--- | :--- | :--- |
| Project rule | `.cursor/rules/biblemate-skills.mdc` | Always applied. Tells the agent to read and follow the matching skill before answering |
| Skills | `.cursor/skills/<name>/SKILL.md` | 125 Cursor Agent Skills. Applied when you name the workflow or when the request matches the skill description |
| Persona reference | `.cursor/agents.md` | Tone and guidelines for the 15 study personas |
| Preferences | `.cursor/preferences/` | Default bible / commentary / lexicon versions for retrievers |
| Generator | `.cursor/build_cursor.py` | Rebuilds this tree from `.grok/` |

Each workflow is a skill. The project rule treats both a natural-language request (“write a devotion on Romans 8”) and a slash-style request (`/devotion Romans 8`) as a cue to follow that skill.

> **Note:** Cursor may also discover `.claude/skills/` if that tree is present. The always-on rule tells the agent to follow `.cursor/skills/` for BibleMate work.

---

## Layout (portable paths only)

```
.cursor/
  build_cursor.py                 # regenerate skills from .grok/
  rules/biblemate-skills.mdc      # always-on project rule
  agents.md                       # 15 personas (combined reference)
  preferences/                    # bible.md, commentary.md, lexicon.md
  skills/<name>/SKILL.md          # 125 skills (+ scripts where needed)
```

Skill instructions use **relative** paths such as `.cursor/skills/bible/bible_retriever.py`. Keep study links relative to the repo as well.

---

## Universal rules

These apply to every BibleMate study in Cursor (also stated in `.cursor/rules/biblemate-skills.mdc` and `.cursor/agents.md`):

### 1. Scripture integrity

Never quote Bible text from memory. Fetch verses via the `bible` skill:

```bash
python3 .cursor/skills/bible/bible_retriever.py "NET John 3:16"
```

Or ask Cursor:

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

Use Cursor’s `Write` tool to create the file, and confirm the saved path in the final reply.

---

## Everyday usage

Open the Agent chat in this project and ask for the workflow. Examples:

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

The same requests work in plain language (“retrieve NET John 3:16”, “write a devotion on Romans 8:28”). The agent reads `.cursor/skills/<name>/SKILL.md` and runs the Python helper that skill names.

Full command catalog: [slash_commands.md](slash_commands.md). Cursor uses the same names, including the refresh skill `update-biblemate`.

### `/testimony` (real-life and missionary stories)

Ask for a **verified** real-life or missionary testimony (never a fabricated story):

```text
/testimony George Muller provision
/testimony Corrie ten Boom forgiveness
```

The skill searches a local registry first:

```bash
python3 .cursor/skills/testimony/testimony_retriever.py "George Muller"
```

If there is no local match, the agent researches with Cursor’s `WebSearch` and `WebFetch` tools and still provides biographical background plus fact-checkable sources. Outputs save under `biblemate/` as `YYYY-MM-DD-HH-MM-SS_testimony_<slug>.md`. The same skill is a recommended option inside **`biblemate`** and **`biblemate-super`**.

### Orchestrated deep studies

| Skill | Purpose |
| :--- | :--- |
| **`biblemate`** | Multi-phase orchestrated study: plan → local data retrieval → exegesis → theology → application → pre-final overview → iterative final manuscript |
| **`biblemate-super`** | Dynamically planned multi-phase study with quality-audit checkpoints and persona rotation |

Both write step files under `biblemate/` (timestamped study folders). They enforce local `bible` retrieval. Long retrieval steps can be delegated with the `Task` tool so raw database dumps stay out of the main chat.

### Book search skills

Each Protestant canon book has a search skill (for example `Gen`, `John`, `Rom`, `Ps`):

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
| `image` | Generate bible-related images into `images/` with `GenerateImage` |
| `zip` | Build `manual_setup.zip` with `.agents/`, `.claude/`, `.cursor/`, `.grok/`, and `preferences/`, plus root `AGENTS.md`, `CLAUDE.md`, and the web app scripts |
| `update-biblemate` | Regenerate the `.cursor` skills from the current `.grok/` tree |

---

## Personas

There are **15** study personas. Profiles: [ai_team_personas.md](ai_team_personas.md). Combined Cursor reference: `.cursor/agents.md`.

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

### How to use them in Cursor

1. **Study skills** adopt a persona by reading `.cursor/agents.md` (for example devotion follows the Compassionate Pastor).
2. **`Task` tool** — delegate a step with `subagent_type` set to a persona slug such as `ot-bible-scholar` or `master-biblical-writer`.
3. **`biblemate` / `biblemate-super`** rotate personas by phase and record which persona each step uses.

---

## Cursor tool mapping

Skills refer to these Cursor tools:

| Need | Tool |
| :--- | :--- |
| Read a file | `Read` |
| Create or overwrite a file | `Write` |
| Edit a file in place | `StrReplace` |
| Run Python retrievers / shell | `Shell` |
| Search the repo | `Grep` |
| Find files | `Glob` |
| Delegate a persona task | `Task` |
| Search the web | `WebSearch` |
| Open a web page | `WebFetch` |
| Generate an image | `GenerateImage` |

Example retriever invocations:

```bash
python3 .cursor/skills/bible/bible_retriever.py "NET John 3:16"
python3 .cursor/skills/commentary/commentary_retriever.py "BNC Romans 8:28"
python3 .cursor/skills/lexicon/lexicon_retriever.py "G26"
python3 .cursor/skills/original/original_retriever.py "John 1:1"
python3 .cursor/skills/data/data_lister.py bible
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

- `.cursor/preferences/bible.md`
- `.cursor/preferences/commentary.md`
- `.cursor/preferences/lexicon.md`

Resolution order for the data root:

1. `BIBLEMATE_DATA` environment variable
2. `~/biblemate`

The shared root [`preferences/`](../preferences) folder is the human-edited default. Regenerating `.cursor/` copies those versions from `.grok/preferences/` into `.cursor/preferences/`. After you change a default, refresh Grok (if needed) and then run `python3 .cursor/build_cursor.py`, or edit `.cursor/preferences/` directly.

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

## Images

The `image` skill uses Cursor’s `GenerateImage` tool (`description`, optional `aspect_ratio`, optional `filename`, optional `reference_image_paths`), then places a timestamped copy with:

```bash
python3 .cursor/skills/image/image_placer.py "<source-path>" "<prompt or title>"
```

---

## Regenerating the Cursor skills

Content is generated from the Grok tree (which itself is generated from `.claude/`, which is generated from `.agents/`):

```bash
# Optional: refresh Claude from Antigravity sources
python3 .claude/build_claude.py

# Optional: refresh Grok from .claude
python3 .grok/build_grok.py

# Rebuild Cursor skills, preferences, agents.md, and the project rule
python3 .cursor/build_cursor.py
```

The Cursor generator is **idempotent**. It rewrites only:

- `.cursor/skills/`
- `.cursor/preferences/`
- `.cursor/agents.md`
- `.cursor/rules/biblemate-skills.mdc`

It leaves `.cursor/build_cursor.py`, `.agents/`, `.claude/`, and `.grok/` unchanged.

From the Cursor agent you can also ask it to run the `update-biblemate` skill, which follows the same refresh path.

---

## Quick start checklist

1. Open this repository in Cursor.
2. Confirm `.cursor/rules/biblemate-skills.mdc` and `.cursor/skills/` are present.
3. Install data: `pip install --upgrade biblematedata` and run `biblematedata`.
4. Smoke-test in Agent chat: `/bible NET John 3:16`.
5. Run a small study: `/devotion Romans 8:28` and confirm a file under `biblemate/`.
6. For a deep dive: `/biblemate` with a clear passage or topic request.

---

## Platform coexistence

| Platform | Config tree | Project rules |
| :--- | :--- | :--- |
| Google Antigravity | `.agents/` | (Antigravity conventions) |
| Claude Code | `.claude/` | `CLAUDE.md` |
| Grok Build | `.grok/` | `AGENTS.md` |
| Cursor | `.cursor/` | `.cursor/rules/biblemate-skills.mdc` |

Shared across platforms:

- Local Bible / commentary / lexicon databases (`BIBLEMATE_DATA` or `~/biblemate`)
- Study outputs in `biblemate/`, `images/`, `export/`
- Skill **names** (the same `bible`, `sermon`, `biblemate`, book skills, and so on)

When regenerating one platform’s tree, leave the others untouched unless you intend to update them. Refresh Cursor last, because `.cursor/build_cursor.py` reads `.grok/`.

---

## Troubleshooting

| Symptom | What to try |
| :--- | :--- |
| Agent quotes a verse without running a retriever | Confirm `.cursor/rules/biblemate-skills.mdc` is enabled (always apply). Ask again and name the `bible` skill |
| Empty or missing verse text | Run the `data` skill, or `python3 .cursor/skills/data/data_lister.py bible`; install/upgrade `biblematedata`; check `BIBLEMATE_DATA` |
| Agent follows `.claude/skills/` | The project rule prefers `.cursor/skills/`. Say “follow the skill in `.cursor/skills/`” |
| Wrong tool paths in a skill | Re-run `python3 .cursor/build_cursor.py` so instructions point at `.cursor/skills/...` |
| Persona voice is generic | Point the agent at `.cursor/agents.md`, or delegate with `Task` and the persona slug |
| Preference version ignored | Edit `.cursor/preferences/*.md`, or edit root `preferences/`, refresh `.grok/preferences/`, and regenerate |
| Paths break on another machine | Keep retriever paths relative and Bible data behind `BIBLEMATE_DATA` or `~/biblemate` |

---

## Related docs

- [slash_commands.md](slash_commands.md) — full command reference (refresh skill: `update-biblemate`)
- [ai_team_personas.md](ai_team_personas.md) — persona profiles
- [study_outputs.md](study_outputs.md) — where studies and exports are saved
- [claude_code_ecosystem.md](claude_code_ecosystem.md) — Claude Code port
- [grok_build_ecosystem.md](grok_build_ecosystem.md) — Grok Build port
- [`.cursor/rules/biblemate-skills.mdc`](../.cursor/rules/biblemate-skills.mdc) — the always-on Cursor rule
- [`.cursor/agents.md`](../.cursor/agents.md) — combined persona definitions for Cursor
