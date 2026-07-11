# Claude Code Ecosystem Guide

This guide explains how to use the **BibleMate** study suite on **Claude Code** (Anthropic). The Claude Code port is a full parallel ecosystem of skills, slash commands, subagents, and personas—equivalent to the Antigravity (`.agents/`) and Grok Build (`.grok/`) ports—and is self-contained under `.claude/`.

It does **not** replace the other platforms. You can use Antigravity, Claude Code, and Grok Build against the same workspace and the same local Bible databases.

---

## Prerequisites

1. **Claude Code** installed and signed in ([Claude Code docs](https://docs.claude.com/en/docs/claude-code/overview)).

   > [!TIP]
   > **Ollama backend (optional, open source).** You can run Claude Code against a
   > local or cloud [Ollama](https://ollama.com) backend instead of the hosted
   > Anthropic API — useful for fully local, open-source setups. Setup details:
   > [docs.ollama.com/integrations/claude-code](https://docs.ollama.com/integrations/claude-code).
   > For BibleMate study workflows, the open-source **GLM-5.2** model is
   > recommended.
2. **This repository** opened as the workspace root (so Claude Code discovers `.claude/` and `CLAUDE.md`).
3. **Local Bible data** (not bundled in the repo—files are large):

   ```bash
   pip install --upgrade biblematedata
   ```

   Data lands under `~/biblemate/data` by default. To point elsewhere:

   ```bash
   export BIBLEMATE_DATA="/path/to/your/biblemate"
   ```

   You can also set it permanently via `env.BIBLEMATE_DATA` in `.claude/settings.json`.
4. **Python 3** on your `PATH` (retrievers and orchestrators are Python scripts).

---

## What gets loaded

When you open this repo in Claude Code:

| Asset | Location | How Claude Code uses it |
| :--- | :--- | :--- |
| Project rules | `CLAUDE.md` | Loaded into session context (scripture integrity, save rules, tool map) |
| Permissions / env | `.claude/settings.json` | Allowed tools, environment variables (`BIBLEMATE_DATA`, …) |
| Skills | `.claude/skills/<name>/SKILL.md` | Auto-invoked by intent **and** available as slash commands (`/bible`, `/sermon`, …) |
| Slash workflows | `.claude/commands/<name>.md` | Custom slash commands (persona + workflow wrappers) |
| Subagents | `.claude/agents/<slug>.md` | Persona subagents delegable via the Task tool (e.g. `verse-scripter`) |
| Combined persona reference | `.claude/agents.md` | Source of truth for persona adoption in workflows |
| Preferences | `.claude/preferences/` | Default bible / commentary / lexicon versions for retrievers |

Browse loaded skills and commands by typing `/` in the prompt. Subagents are surfaced in the Task tool's `subagent_type` list.

> **Note:** Claude Code may also discover `.agents/` if that tree is present. Project `.claude/` skills take priority when names collide and the working directory is the repo root.

---

## Layout (portable paths only)

```
.claude/
  build_claude.py            # regenerate ecosystem from .agents/ + preferences/
  settings.json              # permissions + env for the workspace
  agents.md                  # 15 personas (combined reference)
  preferences/               # bible.md, commentary.md, lexicon.md
  skills/<name>/SKILL.md     # ~125 skills (+ scripts where needed)
  commands/<name>.md         # ~125 slash command workflows
  agents/<slug>.md           # 15 subagent definitions

CLAUDE.md                    # Claude Code project rules (repo root)
```

All skill and command instructions use **relative** paths such as `.claude/skills/bible/bible_retriever.py`. Do not hardcode machine-specific absolute paths in study outputs or cross-file links.

---

## Universal rules

These apply to every BibleMate study on Claude Code (also stated in `CLAUDE.md` and `.claude/agents.md`):

### 1. Scripture integrity

Never quote Bible text from memory. Fetch verses via the `bible` skill:

```bash
python3 .claude/skills/bible/bible_retriever.py "NET John 3:16"
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

Use the Claude Code `Write` tool to create the file, and always confirm the saved path in the final reply.

---

## Everyday usage

### Slash commands

Type `/` in the Claude Code prompt to open autocomplete, then pick a skill or command. Arguments go after the name:

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

Claude Code can load a skill without a slash when your request matches its description—for example, “retrieve John 3:16 in the NET” may trigger the `bible` skill. Prefer an explicit `/name` when you want a specific workflow.

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
| `/zip` | Build `manual_setup.zip` with `.claude/`, `preferences/`, and `CLAUDE.md` |
| `/update` | Refresh sources and regenerate the `.claude` ecosystem |

---

## Personas and subagents

There are **15** study personas, each exposed as a Claude Code subagent. Profiles: [ai_team_personas.md](ai_team_personas.md). Combined Claude reference: `.claude/agents.md`.

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

### How to use them on Claude Code

1. **Slash workflows** already adopt personas (e.g. `/devotion` → Compassionate Pastor via `.claude/agents.md`).
2. **Task tool** — delegate to a persona subagent by setting `subagent_type` to a slug above (definitions live in `.claude/agents/`).
3. **Direct delegation** — when a study needs a specialist lens (e.g. Greek grammar), the main agent can hand off to `biblical-linguistic-analyst` and continue from its result.

---

## Claude Code tool mapping

Skills and personas refer to these Claude Code tools:

| Need | Tool |
| :--- | :--- |
| Read a file | `Read` |
| Create or overwrite a file | `Write` |
| Edit a file in place | `Edit` |
| Run Python retrievers / shell | `Bash` |
| Search the repo | `Grep` |
| List / find files | `Glob` |
| Delegate a persona task | `Task` (with `subagent_type`) |

Example retriever invocations:

```bash
python3 .claude/skills/bible/bible_retriever.py "NET John 3:16"
python3 .claude/skills/commentary/commentary_retriever.py "BNC Romans 8:28"
python3 .claude/skills/lexicon/lexicon_retriever.py "G26"
python3 .claude/skills/original/original_retriever.py "John 1:1"
python3 .claude/skills/data/data_lister.py bible
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

- `.claude/preferences/bible.md`
- `.claude/preferences/commentary.md`
- `.claude/preferences/lexicon.md`

Resolution order for the data root:

1. `BIBLEMATE_DATA` environment variable (also settable in `.claude/settings.json`)
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

## Regenerating the Claude Code ecosystem

Content is generated from the Antigravity tree (`.agents/`) plus shared `preferences/`:

```bash
# Rebuild .claude from .agents/ + preferences/
python3 .claude/build_claude.py
```

The generator is **idempotent**. It rewrites only under `.claude/`:

- `skills/`, `commands/`, `agents/`, `preferences/`, `agents.md`

It does **not** modify `.agents/`, `.grok/`, or root `CLAUDE.md` / `AGENTS.md`.

After editing shared Antigravity sources, refresh Claude first, then Grok (`.grok/build_grok.py` derives from `.claude/`), so all three ecosystems stay aligned.

---

## Quick start checklist

1. Open this repository as the Claude Code workspace.  
2. Confirm `CLAUDE.md` and `.claude/skills/` are present.  
3. Install data: `pip install --upgrade biblematedata`.  
4. Smoke-test: `/bible NET John 3:16`.  
5. Run a small study: `/devotion Romans 8:28` and confirm a file under `biblemate/`.  
6. For a deep dive: `/biblemate` with a clear passage or topic request.

---

## Platform coexistence

| Platform | Config tree | Project rules |
| :--- | :--- | :--- |
| Google Antigravity | `.agents/` | (Antigravity conventions) |
| Claude Code | `.claude/` | `CLAUDE.md` |
| Grok Build | `.grok/` | `AGENTS.md` |

Shared across platforms:

- Local Bible / commentary / lexicon databases (`BIBLEMATE_DATA` or `~/biblemate`)
- Study outputs in `biblemate/`, `images/`, `export/`
- Command and skill **names** (same `/bible`, `/sermon`, `/biblemate`, book skills, etc.)

When regenerating one platform's tree, leave the others untouched unless you intend to update them.

---

## Troubleshooting

| Symptom | What to try |
| :--- | :--- |
| Empty or missing verse text | Run `/data` (or `data_lister.py bible`); install/upgrade `biblematedata`; check `BIBLEMATE_DATA` in `.claude/settings.json` |
| Skill not in `/` menu | Confirm you are in the repo root; restart Claude Code so skills reload; run `python3 .claude/build_claude.py` |
| Wrong tool paths in old notes | Re-run `python3 .claude/build_claude.py` so instructions point at `.claude/skills/...` |
| Persona subagent not available | Check `.claude/agents/<slug>.md` exists; restart the session to refresh the Task tool's subagent list |
| Permission prompt on retriever | Add the command to `permissions.allow` in `.claude/settings.json` (or accept once with "always allow") |
| Preference version ignored | Edit `.claude/preferences/*.md` (not only root `preferences/` unless you re-copy/regenerate) |
| Paths break on another machine | Avoid absolute paths; keep everything relative to the repo and `BIBLEMATE_DATA` |

---

## Related docs

- [grok_build_ecosystem.md](grok_build_ecosystem.md) — the Grok Build equivalent of this guide
- [slash_commands.md](slash_commands.md) — full command reference (shared names)
- [ai_team_personas.md](ai_team_personas.md) — persona profiles
- [study_outputs.md](study_outputs.md) — where studies and exports are saved
- Root [CLAUDE.md](../CLAUDE.md) — Claude Code session rules
- [`.claude/agents.md`](../.claude/agents.md) — combined persona definitions for Claude Code