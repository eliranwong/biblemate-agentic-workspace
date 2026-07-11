# Grok Build Ecosystem Guide

This guide explains how to use the **BibleMate** study suite on **Grok Build** (xAI Grok). The Grok port is a full parallel ecosystem of skills, slash commands, agents, and personas—equivalent to the Antigravity (`.agents/`) and Claude Code (`.claude/`) ports—and is self-contained under `.grok/`.

It does **not** replace the other platforms. You can use Antigravity, Claude Code, and Grok Build against the same workspace and the same local Bible databases.

---

## Prerequisites

1. **Grok Build** installed and signed in ([xAI Build docs](https://docs.x.ai/build/overview)).
2. **This repository** opened as the workspace root (so Grok discovers `.grok/` and `AGENTS.md`).
3. **Local Bible data** (not bundled in the repo—files are large):

   ```bash
   pip install --upgrade biblematedata
   ```

   Data lands under `~/biblemate/data` by default. To point elsewhere:

   ```bash
   export BIBLEMATE_DATA="/path/to/your/biblemate"
   ```

4. **Python 3** on your `PATH` (retrievers and orchestrators are Python scripts).

---

## What gets loaded

When you open this repo in Grok Build:

| Asset | Location | How Grok uses it |
| :--- | :--- | :--- |
| Project rules | `AGENTS.md` | Loaded into session context (scripture integrity, save rules, tool map) |
| Skills | `.grok/skills/<name>/SKILL.md` | Auto-invoked by intent **and** available as slash commands (`/bible`, `/sermon`, …) |
| Slash workflows | `.grok/commands/<name>.md` | Legacy-style custom slash commands (persona + workflow wrappers) |
| Agents | `.grok/agents/<slug>.md` | Custom `spawn_subagent` types (e.g. `verse-scripter`) |
| Personas | `.grok/personas/<slug>.toml` | Behavioral overlays (`/personas`) |
| Combined persona reference | `.grok/agents.md` | Source of truth for persona adoption in workflows |
| Preferences | `.grok/preferences/` | Default bible / commentary / lexicon versions for retrievers |

Browse loaded skills in the TUI with `/skills`. Manage agents and personas with `/config-agents` (alias `/agents`) and `/personas`.

> **Note:** Grok may also discover `.claude/` and `.agents/` if those trees are present. Project `.grok/` skills take priority when names collide and the working directory is the repo root.

---

## Layout (portable paths only)

```
.grok/
  build_grok.py              # regenerate ecosystem from .claude/
  agents.md                  # 15 personas (combined reference)
  preferences/               # bible.md, commentary.md, lexicon.md
  skills/<name>/SKILL.md     # ~125 skills (+ scripts where needed)
  commands/<name>.md         # ~125 slash command workflows
  agents/<slug>.md           # 15 agent definitions
  personas/<slug>.toml       # 15 persona overlays

AGENTS.md                    # Grok project rules (repo root)
```

All skill and command instructions use **relative** paths such as `.grok/skills/bible/bible_retriever.py`. Do not hardcode machine-specific absolute paths in study outputs or cross-file links.

---

## Universal rules

These apply to every BibleMate study on Grok Build (also stated in `AGENTS.md` and `.grok/agents.md`):

### 1. Scripture integrity

Never quote Bible text from memory. Fetch verses via the `bible` skill:

```bash
python3 .grok/skills/bible/bible_retriever.py "NET John 3:16"
```

Or invoke the slash command:

```text
/bible NET John 3:16
```

### 2. Save study output

For bible-related skills/commands **except** `biblemate`, `biblemate-super`, `image`, `data`, `sync`, `md`, `docx`, and `zip`, save the full study output under `biblemate/` with a timestamp prefix:

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

Use the Grok `write` tool to create the file, and always confirm the saved path in the final reply.

---

## Everyday usage

### Slash commands

Type `/` in the Grok prompt to open autocomplete, then pick a skill or command. Arguments go after the name:

```text
/bible NET John 3:16
/devotion Romans 8:28
/sermon Psalm 23
/keywords Ephesians 2:1-10
/commentary BNC John 3:16
/lexicon G26
/Gen "In the beginning" NET
/biblemate Write an expository study on Ezra 5
/biblemate-super Sermon series seed: standing firm in Ezra
```

Full command catalog (shared names across platforms): [slash_commands.md](slash_commands.md).

### Automatic skill invocation

Grok can load a skill without a slash when your request matches its description—for example, “retrieve John 3:16 in the NET” may trigger the `bible` skill. Prefer an explicit `/name` when you want a specific workflow.

### Orchestrated deep studies

| Command | Purpose |
| :--- | :--- |
| **`/biblemate`** | Multi-phase orchestrated study: plan → local data retrieval → exegesis → theology → application → pre-final overview → iterative final manuscript |
| **`/biblemate-super`** | Dynamically planned multi-phase study with quality-audit checkpoints and persona rotation |

Both write step files under `biblemate/` (timestamped study folders). They enforce local `bible` retrieval and do not quote Scripture from memory.

### Book search skills

Each Protestant canon book has a search skill/command (e.g. `/Gen`, `/John`, `/Rom`). Example:

```text
/Ps "The Lord is my shepherd"
/John love + world NET
```

Wildcards (`*`, `?`) and logical combinations (`+`, `|`) follow the shared search skill conventions.

### Utility commands

| Command | Purpose |
| :--- | :--- |
| `/data` | List installed bible / commentary / lexicon versions |
| `/sync` | Git add, commit, and push workspace changes |
| `/md` / `/docx` | Export content to `export/md` or `export/docx` |
| `/image` | Generate bible-related images into `images/` |
| `/zip` | Build `manual_setup.zip` with `.grok/`, `preferences/`, and `AGENTS.md` |
| `/update` | Refresh sources and regenerate the `.grok` ecosystem |

---

## Personas and agents

There are **15** study personas. Profiles: [ai_team_personas.md](ai_team_personas.md). Combined Grok reference: `.grok/agents.md`.

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

### How to use them on Grok

1. **Slash workflows** already adopt personas (e.g. `/devotion` → Compassionate Pastor via `.grok/agents.md`).
2. **`spawn_subagent`** — set `subagent_type` to a persona slug (agent definitions live in `.grok/agents/`).
3. **Personas tab** — open `/personas` to inspect or apply file-based overlays from `.grok/personas/*.toml`.

---

## Grok tool mapping

Skills and personas refer to these Grok tools:

| Need | Tool |
| :--- | :--- |
| Read a file | `read_file` |
| Create or overwrite a file | `write` |
| Edit a file in place | `search_replace` |
| Run Python retrievers / shell | `run_terminal_command` |
| Search the repo | `grep` |
| List a directory | `list_dir` |
| Delegate a persona task | `spawn_subagent` |

Example retriever invocations:

```bash
python3 .grok/skills/bible/bible_retriever.py "NET John 3:16"
python3 .grok/skills/commentary/commentary_retriever.py "BNC Romans 8:28"
python3 .grok/skills/lexicon/lexicon_retriever.py "G26"
python3 .grok/skills/original/original_retriever.py "John 1:1"
python3 .grok/skills/data/data_lister.py bible
```

---

## Runtime data and preferences

| Resource | Default install location |
| :--- | :--- |
| Bibles | `~/biblemate/data/bibles` (and optional `data_custom/bibles`) |
| Commentaries | `~/biblemate/data/commentaries` |
| Lexicons | under the biblemate data tree |
| Morphology / xrefs / etc. | under the biblemate data tree |

Default versions for queries without an explicit version are read from:

- `.grok/preferences/bible.md`
- `.grok/preferences/commentary.md`
- `.grok/preferences/lexicon.md`

Resolution order for the data root:

1. `BIBLEMATE_DATA` environment variable  
2. `~/biblemate`

---

## Where outputs go

See also [study_outputs.md](study_outputs.md).

| Output type | Location |
| :--- | :--- |
| Standard study files | `biblemate/YYYY-MM-DD-HH-MM-SS_*.md` |
| Orchestrated multi-step studies | `biblemate/<timestamp>_<title>/` with `NNN-skill.md` steps |
| Images | `images/` |
| Markdown / Word exports | `export/md/`, `export/docx/` |
| Manual setup archive | `manual_setup.zip` (repo root, via `/zip`) |

Use **relative** links between study files (e.g. `[005-keywords.md](005-keywords.md)`), never `file:///Users/...` absolute URLs.

---

## Regenerating the Grok ecosystem

Content is generated from the Claude Code tree (which itself is generated from `.agents/`):

```bash
# Optional: refresh Claude from Antigravity sources
python3 .claude/build_claude.py

# Rebuild Grok from .claude
python3 .grok/build_grok.py
```

The generator is **idempotent**. It rewrites only under `.grok/`:

- `skills/`, `commands/`, `agents/`, `personas/`, `preferences/`, `agents.md`

It does **not** modify `.agents/`, `.claude/`, or root `AGENTS.md`.

After editing shared Antigravity sources, refresh Claude first, then Grok, so all three ecosystems stay aligned.

---

## Quick start checklist

1. Open this repository as the Grok Build workspace.  
2. Confirm `AGENTS.md` and `.grok/skills/` are present.  
3. Install data: `pip install --upgrade biblematedata`.  
4. Smoke-test: `/bible NET John 3:16`.  
5. Run a small study: `/devotion Romans 8:28` and confirm a file under `biblemate/`.  
6. For a deep dive: `/biblemate` with a clear passage or topic request.

---

## Platform coexistence

| Platform | Config tree | Project rules |
| :--- | :--- | :--- |
| Google Antigravity | `.agents/` | (Antigravity conventions) |
| Claude Code | `.claude/` | `CLAUDE.md` / `Claude.md` |
| Grok Build | `.grok/` | `AGENTS.md` |

Shared across platforms:

- Local Bible / commentary / lexicon databases (`BIBLEMATE_DATA` or `~/biblemate`)
- Study outputs in `biblemate/`, `images/`, `export/`
- Command and skill **names** (same `/bible`, `/sermon`, `/biblemate`, book skills, etc.)

When regenerating one platform’s tree, leave the others untouched unless you intend to update them.

---

## Troubleshooting

| Symptom | What to try |
| :--- | :--- |
| Empty or missing verse text | Run `/data` (or `data_lister.py bible`); install/upgrade `biblematedata`; check `BIBLEMATE_DATA` |
| Skill not in `/` menu | Confirm you are in the repo root; wait for skill reload; run `python3 .grok/build_grok.py` |
| Wrong tool paths in old notes | Re-run `python3 .grok/build_grok.py` so instructions point at `.grok/skills/...` |
| Persona not available to subagents | Check `.grok/agents/<slug>.md` and `.grok/personas/<slug>.toml`; open `/config-agents` |
| Preference version ignored | Edit `.grok/preferences/*.md` (not only root `preferences/` unless you re-copy/regenerate) |
| Paths break on another machine | Avoid absolute paths; keep everything relative to the repo and `BIBLEMATE_DATA` |

---

## Related docs

- [slash_commands.md](slash_commands.md) — full command reference (shared names)
- [ai_team_personas.md](ai_team_personas.md) — persona profiles
- [study_outputs.md](study_outputs.md) — where studies and exports are saved
- Root [AGENTS.md](../AGENTS.md) — Grok session rules
- [`.grok/agents.md`](../.grok/agents.md) — combined persona definitions for Grok
