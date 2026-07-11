# BibleMate Agentic Workspace

> [!IMPORTANT]
> **News — multi-platform support.** This workspace now runs on **three** agentic
> platforms, not only Google Antigravity:
>
> | Platform | Config | Status |
> | :-- | :-- | :-- |
> | **[Google Antigravity](https://antigravity.google/download)** | `.agents/` | Original ecosystem |
> | **[Claude Code](https://claude.com/claude-code)** | `.claude/` | Full parallel port (same 15 personas, 125 skills, 125 slash commands) |
> | **[Grok Build](https://docs.x.ai/build/overview)** (xAI) | `.grok/` + `AGENTS.md` | Full parallel port (same personas, skills, and commands) |
>
> Use **any one** or **any combination** against a single shared workspace and the
> same local Bible databases. Details:
> [Claude Code](#-claude-code-equivalent-ecosystem-optional-bonus) ·
> [Grok Build](#-grok-build-equivalent-ecosystem-optional-bonus) ·
> [docs/grok_build_ecosystem.md](docs/grok_build_ecosystem.md)

*An integrated local workspace combining robust scripture databases, modular study skills, and specialized AI personas to streamline biblical research and writing across Google Antigravity, Claude Code, and Grok Build.*

> [!NOTE]
> **Where Rigorous Scholarship Meets Agentic Power:** This repository unites advanced agentic workflow capability (originally built for the **Google Antigravity Platform**, now also available for **Claude Code** and **Grok Build**) with the reliable, time-tested databases of the **[UniqueBible Project](https://github.com/eliranwong/UniqueBible)** and the modular AI exegesis tools of **[BibleMate AI](https://github.com/eliranwong/biblemate)**.

Welcome to the **BibleMate Agentic Workspace**, a state-of-the-art local agentic study suite. It began as an extension for the **Google Antigravity** development platform (CLI, IDE, and platform) and now ships equivalent, self-contained ecosystems for **Claude Code** and **Grok Build** as well. It features an integrated team of 15 customized study personas, 125 standalone exegesis and theology skills, and 125 custom slash commands—shared names and study outputs across platforms.

> [!TIP]
> **Optional multi-platform add-ons.** Beyond the original Google Antigravity
> experience under `.agents/`, this workspace ships parallel, self-contained
> ecosystems for **[Claude Code](https://claude.com/claude-code)** (`.claude/`) and
> **[Grok Build](https://docs.x.ai/build/overview)** (`.grok/`) — each with the
> same 15 personas, 125 skills, and 125 slash commands. Both are **optional**:
> ignore them and use Antigravity alone, or use **any combination** of the three
> platforms interchangeably against a single shared workspace and shared local
> Bible databases. See
> [Claude Code Equivalent Ecosystem](#-claude-code-equivalent-ecosystem-optional-bonus)
> and
> [Grok Build Equivalent Ecosystem](#-grok-build-equivalent-ecosystem-optional-bonus)
> below.

Whether you are a **pastor preparing a sermon**, a **bible content writer drafting articles**, a **theology student researching ancient manuscripts**, or a **believer deepening your study of the scriptures**, this workspace provides a unified, local-first environment where writing, AI agent assistance, and scholarly databases reside side-by-side in your IDE.

Official Antigravity downloads at: https://antigravity.google/download

---

## 🌟 Key Selling Points & Synergy

This project is the intersection of three powerful domains:

### 1. Reliable Databases (UniqueBible)
Unlike standard AI workflows that suffer from hallucinations when quoting, translating, or parsing scripture, this workspace relies directly on the SQLite database files developed and refined for over a decade in the **[UniqueBible project](https://github.com/eliranwong/UniqueBible)**. Bibles, commentaries, lexicons, morphology codes, and cross-references are queried locally at runtime, providing an unwavering, solid foundation of truth.

### 2. Intelligent Exegesis (BibleMate AI)
By integrating the tools and retrievers of **[BibleMate AI](https://github.com/eliranwong/biblemate)**, the agent team can dynamically locate words, compare translations, analyze Greek and Hebrew root words, extract commentaries, and track down cross-references instantly.

### 3. Multi-Platform Agentic Environments
Tools are exposed natively in your agentic environment of choice. The original
integration targets **Google Antigravity**; equivalent ecosystems ship for
**Claude Code** and **Grok Build**:
* **Automatic Workspace Loading**: Open this workspace in Antigravity, Claude Code, or Grok Build, and the matching tree (`.agents/`, `.claude/`, or `.grok/`) loads personas, skills, and slash commands.
* **Inline Composition**: Write your study guides, sermons, or articles in the IDE while conversing with specialized agents in the side panel.
* **Slash Commands**: Execute complex workflows (e.g. `/sermon Romans 8:28` or `/translate-greek John 1:1`) with simple, parameterized commands—**same command names** across platforms.

---

## 🚀 The `/biblemate` Signature Command: Orchestrated Bible Study

The `/biblemate` command (backed by the [.agents/skills/biblemate](.agents/skills/biblemate) orchestration suite) is the **signature command** of this project. While individual slash commands perform specific exegesis tasks (like outline lookups or keyword analyses), `/biblemate` acts as a first-class Biblical scholar and orchestrator, running a fully automated, multi-phase research pipeline to produce publication-quality, deep-dive manuscripts.

### Why it is so powerful for Bible Study:
* **Phased Workflow**: It guides the AI assistant through 5 rigorous research phases—Planning, local database Data Retrieval, Analysis, Theological Synthesis, and pastoral/evangelistic Application.
* **Persona Rotation**: It automatically rotates AI personas based on the study phase (e.g., using the *OT Bible Scholar* / *NT Bible Scholar* for exegesis, *Biblical Theologian* / *Systematic Theologian* for theology, *Passionate Evangelist* for devotions, and *Compassionate Pastor* for first-person prayers) to ensure academic rigor and spiritual depth.
* **100% Scripture Integrity**: It strictly enforces the local `bible` query skill to fetch all scriptures directly from SQLite databases, completely eliminating AI scripture hallucinations.
* **Quality Gate Auditing**: It validates the Master Plan against minimum skill requirements for the study type (passage, book, topical, or sermon) and computes a 0–100 quality score, ensuring no thin or shallow outputs are ever accepted.
* **Iterative Final Response**: After producing a pre-final overview that surveys all study outputs, it adopts the *Master Biblical Writer* persona and runs an iterative Draft→Integrate→Audit→Revise writing loop (minimum 2 cycles) to produce a comprehensive, standalone, publication-quality final response that directly answers the original request.

### `/biblemate` Workflow Architecture

```mermaid
graph TD
    User(["User Request"]) --> Refine["Refine & Classify Request"]
    Refine --> Phase0["Phase 0: Planning & Init"]
    Phase0 --> Plan["Master Study Plan Generated & Validated"]

    Plan --> Phase1["Phase 1: Local Data Retrieval"]
    subgraph Phase1_Sub ["Phase 1: Data (Bible Textual Critic & Linguistic Analyst)"]
        Phase1 --> Db1[("Bible Texts")]
        Phase1 --> Db2[("Greek/Hebrew Original")]
        Phase1 --> Db3[("Commentaries")]
        Phase1 --> Db4[("Lexicons & Morphology")]
        Phase1 --> Db5[("Cross-References")]
        Phase1 --> Db6[("Bible Dictionaries")]
        Phase1 --> Db7[("Encyclopedias")]
    end

    Db1 & Db2 & Db3 & Db4 & Db5 & Db6 & Db7 --> Phase2["Phase 2: Analysis & Exegesis"]
    subgraph Phase2_Sub ["Phase 2: Exegesis (OT & NT Bible Scholar)"]
        Phase2 --> Outline["Structural Outline"]
        Phase2 --> Keywords["Word Study"]
        Phase2 --> Context["Historical/Cultural Context"]
        Phase2 --> Flow["Thought Flow Progression"]
    end

    Outline & Keywords & Context & Flow --> Phase3["Phase 3: Theological Synthesis"]
    subgraph Phase3_Sub ["Phase 3: Theology (Biblical & Systematic Theologian)"]
        Phase3 --> Themes["Doctrinal Mapping"]
        Phase3 --> Systematic["Systematic Soteriology"]
        Phase3 --> Canon["Canonical Narrative Fit"]
    end

    Themes & Systematic & Canon --> Phase4["Phase 4: Devotion & Application"]
    subgraph Phase4_Sub ["Phase 4: Heart (Passionate Evangelist & Compassionate Pastor)"]
        Phase4 --> Devotion["Devotional Reflection"]
        Phase4 --> Application["Practical Action Steps"]
        Phase4 --> Prayer["Heartfelt Scriptural Prayer"]
    end

    Devotion & Application & Prayer --> Phase5["Phase 5: Pre-Final Overview"]
    subgraph Phase5_Sub ["Phase 5: Overview (Biblical Content Interpreter)"]
        Phase5 --> Survey["Survey All Study Outputs"]
        Phase5 --> GapCheck["Gap Analysis & Content Mapping"]
        Phase5 --> QualScore["Quality Score Check"]
    end

    Survey & GapCheck & QualScore --> Phase6["Phase 6: Final Response"]
    subgraph Phase6_Sub ["Phase 6: Writing (Master Biblical Writer)"]
        Phase6 --> Draft["Step 1: Comprehensive Draft"]
        Draft --> Integrate["Step 2: Multi-Pass Integration"]
        Integrate --> Audit["Step 3: Audit Against 9 Criteria"]
        Audit --> Revise["Step 4: Revise & Strengthen"]
        Revise -->|"Loop min 2x"| Audit
        Revise --> FinalGate["Step 6: Final Quality Gate"]
    end

    FinalGate --> Phase7["Phase 7: Sync"]
    subgraph Phase7_Sub ["Phase 7: Sync"]
        Phase7 --> GitSync["Git Commit & Push"]
    end

    FinalGate --> FinalUser(["Publication-Quality Final Response"])
```

---

## ⚡ The `/biblemate-super` Ultimate Command: Dynamic & Goal-Oriented Research & Orchestration

The `/biblemate-super` command (backed by the [.agents/skills/biblemate-super](.agents/skills/biblemate-super) orchestration suite) is the **advanced, adaptive counterpart** to the standard `/biblemate` command. 

While `/biblemate` follows a preset, structured 6-phase framework, `/biblemate-super` is designed for complex, non-standard, or highly specific research tasks that require dynamic planning, custom tools, and strict validation checks.

### Key Differences & Enhancements:
* 🗺️ **Dynamic Phased Planning**: It does not force a generic template. The agent assesses the request and designs a custom-tailored multi-phase master plan containing custom phases specifically aligned to your objectives.
* 🎭 **Dynamic Persona Rotation**: Personas are matched to steps based on the specific task (e.g. using `Context Analyst David` for historical Psalms exegesis, `Linguistic Analyst` for original syntax, or `Bible Textual Critic` for translation variants), rather than following a rigid phase-locked rotation.
* 🎯 **Goal-Oriented Phase Audits**: Every custom phase is initialized with **Clear Phase Goals**. Upon completion of a phase, the **Study Plan & Phase Quality Auditor** persona runs a strict checkpoint review. If goals are not met, the auditor:
  1. Identifies textual, theological, or practical gaps.
  2. Prescribes and inserts new follow-up steps (e.g. running the `online` skill to fetch commentary, or doing extra lexically parsed lookups).
  3. Updates the plan and runs those steps, re-auditing until goals are satisfied before advancing.
* 🔍 **Flexible Plan Validation**: Validation checks verify that the dynamic plan contains a structured checklist with essential categories covered (Scripture Retrieval, Exegesis, Theology, and Application) rather than enforcing rigid tool inventories.

---

## Directory Structure

All agentic configurations are self-contained under the `.agents/` folder (for the Antigravity platform), with **optional, parallel** ecosystems for **Claude Code** under `.claude/` and **Grok Build** under `.grok/` (see [Claude Code](#-claude-code-equivalent-ecosystem-optional-bonus) and [Grok Build](#-grok-build-equivalent-ecosystem-optional-bonus) below). Generated study outputs are written to your shared workspace:

```
├── .agents/              # Antigravity agentic config (personas, skills, workflows)
│   ├── agents.md         # Custom AI team personas and guidelines
│   ├── skills/           # Standalone, modular exegesis and study skills
│   └── workflows/        # Parameterized slash command workflows
├── .claude/              # Claude Code equivalent ecosystem (self-contained, portable)
│   ├── build_claude.py   # Regenerates .claude/ from .agents/ + preferences/
│   ├── settings.json     # Permissions + env (BIBLEMATE_DATA) for Claude Code
│   ├── agents.md         # Combined persona reference (paths ported to .claude)
│   ├── preferences/      # Default bible/commentary/lexicon version files
│   ├── skills/           # 125 Claude Code Agent Skills (one per .agents/skills/)
│   ├── commands/         # 125 slash commands (one per .agents/workflows/)
│   └── agents/           # 15 subagents (one per persona in agents.md)
├── .grok/                # Grok Build equivalent ecosystem (self-contained, portable)
│   ├── build_grok.py     # Regenerates .grok/ from .claude/ (Claude paths → Grok)
│   ├── agents.md         # Combined persona reference (paths ported to .grok)
│   ├── preferences/      # Default bible/commentary/lexicon version files
│   ├── skills/           # 125 Grok skills + scripts (slash commands + auto-invoke)
│   ├── commands/         # 125 slash command workflows
│   ├── agents/           # 15 agent definitions (spawn_subagent types)
│   └── personas/         # 15 persona overlays (.toml) for Grok subagents
├── AGENTS.md             # Grok Build project rules (scripture integrity, save rules)
├── preferences/          # Shared default version preferences (bible/commentary/lexicon)
├── biblemate/            # Saved study outputs, sermons, outlines, and devotions
├── images/               # Generated biblical illustrations and visual aids
├── notes/                # User-created notes, subfolders, and documents
└── export/               # Exported Word documents (.docx) and bundles
```

For in-depth details on file management and study output locations, see the **[Study Outputs Reference Guide](docs/study_outputs.md)**.


---

## 🤖 Claude Code Equivalent Ecosystem (Optional Bonus)

> [!NOTE]
> This section is **entirely optional**. The Google Antigravity integration under
> `.agents/` is the primary experience and requires nothing from `.claude/`. The
> Claude Code ecosystem below is an **additional choice** provided as a bonus for
> users who prefer to run BibleMate through [Claude Code](https://claude.com/claude-code)
> instead of — or alongside — Antigravity (and optionally Grok Build). If you do
> not use Claude Code, you can safely ignore everything in `.claude/`.

In addition to the native Google Antigravity integration, this workspace ships an
**optional, parallel, self-contained BibleMate ecosystem for [Claude Code](https://claude.com/claude-code)**
under `.claude/`. It is generated directly from `.agents/` + `preferences/`, so
it mirrors the Antigravity ecosystem one-to-one: the same **15 personas**, the same
**125 skills**, and the same **125 slash commands**, all using **relative paths**
only (no hardcoded absolute paths), so the workspace stays portable.

### One workspace, three ecosystems

The Antigravity (`.agents/`), Claude Code (`.claude/`), and Grok Build (`.grok/`)
ecosystems **coexist** in a single repository and share the same local Bible
databases, the same root `preferences/` defaults (each port also keeps a copy
under its own tree), and the same `biblemate/` study output directory. You can
use **any one platform or any combination** interchangeably:

| | Antigravity | Claude Code | Grok Build |
| :-- | :-- | :-- | :-- |
| Config dir | `.agents/` | `.claude/` | `.grok/` |
| Project rules | (Antigravity conventions) | `CLAUDE.md` / `Claude.md` | `AGENTS.md` |
| Personas | `agents.md` (single file) | `.claude/agents/<slug>.md` + `.claude/agents.md` | `.grok/agents/<slug>.md` + `.grok/personas/<slug>.toml` + `.grok/agents.md` |
| Skills | `.agents/skills/<name>/SKILL.md` | `.claude/skills/<name>/SKILL.md` | `.grok/skills/<name>/SKILL.md` |
| Slash commands | `.agents/workflows/<name>.md` | `.claude/commands/<name>.md` | `.grok/commands/<name>.md` (+ skills as `/name`) |
| Runtime data | `~/biblemate/data` (or `BIBLEMATE_DATA`) | same | same |
| Study outputs | `biblemate/` | `biblemate/` | `biblemate/` |

Because all three read from the same SQLite databases and write to the same
`biblemate/` folder, a study started on one platform can be continued or
re-opened on another.

### Using BibleMate with Claude Code

1. **Install Claude Code** if you have not already (CLI, desktop app, or IDE
   extension). The `.claude/` ecosystem is auto-discovered when you open this
   workspace as your project root.
2. **Install the shared database** (one-off, same as Antigravity / Grok Build):
   ```bash
   pip install --upgrade biblematedata
   biblematedata
   ```
3. **Run any slash command** exactly as you would on Antigravity — Claude Code
   registers the same names: `/bible`, `/sermon`, `/devotion`, `/biblemate`,
   `/biblemate-super`, `/translate-greek`, `/Gen` (book search), `/data`,
   `/sync`, etc. For example:
   ```
   /bible NET John 3:16
   /sermon Romans 8:28
   /translate-greek John 1:1
   ```
4. **Scripture integrity & output saving** are enforced the same way as on
   Antigravity: skills fetch every verse from the local SQLite databases via
   `python3 .claude/skills/bible/bible_retriever.py "..."` (never from memory),
   and study outputs are saved to `biblemate/` with a `YYYY-MM-DD-HH-MM-SS_`
   timestamp prefix.

### Portability (no absolute paths)

The `.claude/` ecosystem is fully self-contained and portable:

- All skill scripts and their bundled data files are **copied inside
  `.claude/skills/`** — the skills and commands do not depend on any files
  outside the `.claude/` directory.
- Runtime Bible data resolves in this order:
  1. the `BIBLEMATE_DATA` environment variable (point it anywhere), else
  2. `~/biblemate` (the standard install location).
  Override it in [`.claude/settings.json`](.claude/settings.json) (`env.BIBLEMATE_DATA`)
  if your data lives elsewhere.
- Default bible/commentary/lexicon versions are read from
  [`.claude/preferences/`](.claude/preferences), a copy of the shared
  [`preferences/`](preferences) folder.

### Regenerating or refreshing `.claude/`

The Claude Code ecosystem is produced by a generator script. Re-run it after
editing `.agents/` or `preferences/` to keep `.claude/` in sync (idempotent;
only rewrites `skills/`, `commands/`, `agents/`, `preferences/`, and `agents.md`
under `.claude/`):

```bash
python3 .claude/build_claude.py
```

From within Claude Code you can also run the tailored `/update` command, which
refreshes the bundled `.agents/` + `preferences/` source from the remote
`manual_setup.zip` and then regenerates `.claude/`.


---

## ⚡ Grok Build Equivalent Ecosystem (Optional Bonus)

> [!NOTE]
> This section is **entirely optional**. The Google Antigravity integration under
> `.agents/` is the primary experience and requires nothing from `.grok/`. The
> Grok Build ecosystem below is an **additional choice** for users who prefer to
> run BibleMate through [Grok Build](https://docs.x.ai/build/overview) (xAI)
> instead of — or alongside — Antigravity and/or Claude Code. If you do not use
> Grok Build, you can safely ignore everything in `.grok/` and root `AGENTS.md`.

This workspace also ships an **optional, parallel, self-contained BibleMate
ecosystem for [Grok Build](https://docs.x.ai/build/overview)** under `.grok/`.
It is generated from the Claude Code tree (`.claude/`) by
[`python3 .grok/build_grok.py`](.grok/build_grok.py), with paths and tool names
adapted to Grok standards. It mirrors the other platforms one-to-one: the same
**15 personas**, the same **125 skills**, and the same **125 slash commands**,
using **relative paths** only so the workspace stays portable.

Full usage guide: **[docs/grok_build_ecosystem.md](docs/grok_build_ecosystem.md)**.

### Using BibleMate with Grok Build

1. **Install and sign in to Grok Build**, then open this repository as the
   workspace root so Grok discovers `.grok/` skills/commands and root
   [`AGENTS.md`](AGENTS.md).
2. **Install the shared database** (one-off, same as Antigravity / Claude Code):
   ```bash
   pip install --upgrade biblematedata
   biblematedata
   ```
3. **Run any slash command** with the same names as on the other platforms:
   ```
   /bible NET John 3:16
   /devotion Romans 8:28
   /sermon Psalm 23
   /biblemate Study grace in Ephesians 2
   ```
   Skills also appear under `/skills` and can auto-invoke from natural language
   when their descriptions match the request.
4. **Scripture integrity & output saving** match the other ports: fetch verses
   with `python3 .grok/skills/bible/bible_retriever.py "..."` (never from
   memory), and save study outputs under `biblemate/` with a
   `YYYY-MM-DD-HH-MM-SS_` timestamp prefix (via the Grok `write` tool).
5. **Personas / agents**: Grok exposes personas both as
   [`.grok/agents/<slug>.md`](.grok/agents) definitions (for `spawn_subagent`
   `subagent_type`) and as [`.grok/personas/<slug>.toml`](.grok/personas)
   overlays (`/personas`). Combined reference: [`.grok/agents.md`](.grok/agents.md).

### Portability (no absolute paths)

The `.grok/` ecosystem is fully self-contained and portable:

- Skill scripts and bundled data live under **`.grok/skills/`**; instructions
  use relative paths such as `.grok/skills/bible/bible_retriever.py`.
- Runtime Bible data resolves in this order:
  1. the `BIBLEMATE_DATA` environment variable, else
  2. `~/biblemate` (the standard install location).
- Default versions are read from [`.grok/preferences/`](.grok/preferences)
  (a copy of the shared [`preferences/`](preferences) folder).

### Regenerating or refreshing `.grok/`

Generate or refresh Grok from the Claude Code tree (refresh Claude first if you
changed `.agents/` or root `preferences/`):

```bash
python3 .claude/build_claude.py   # optional: sync Claude from Antigravity sources
python3 .grok/build_grok.py       # rebuild Grok from .claude/
```

The Grok generator is idempotent and only rewrites `skills/`, `commands/`,
`agents/`, `personas/`, `preferences/`, and `agents.md` under `.grok/`. It does
not modify `.agents/`, `.claude/`, or root `AGENTS.md`.

From within Grok Build you can also run the tailored `/update` skill to
regenerate the ecosystem after refreshing sources.


---

## 🌐 Standalone Web Application

In addition to the native Antigravity IDE integration, this workspace ships with a **self-contained browser-based web application** ([`web_app.py`](web_app.py)) built with [NiceGUI](https://nicegui.io). It lets you run the full suite of BibleMate AI agents, monitor live execution, browse generated study reports, and view AI-generated biblical images — all from any modern web browser on your local machine.

<img width="1511" height="860" alt="Image" src="https://github.com/user-attachments/assets/c76d8e4b-5188-4f02-92aa-79d985f68523" />

### Key Features

- **Chat Workspace** — submit study requests and receive beautifully rendered Markdown responses streamed in real time
- **Live Agent Console** — watch the agent's thinking monologue, active tool calls, and system logs as they happen
- **Stop Button** — cancel any running agent mid-execution with one click
- **File Tree & Document Reader** — browse and open saved Markdown study outputs, notes, and AI-generated images directly in the browser
- **Inline Markdown Editor** — edit any deletable markdown study outputs or notes right from the web browser with Save/Cancel capability
- **Notes Management** — select the `notes` directory to add files and subfolders on demand, with empty folders displaying instantly in the tree
- **Image Generation (`/image`)** — generate Bible-related images on demand; files are saved to `images/` with a timestamped filename
- **Settings Drawer** — switch AI models (Gemini 3.5 Flash/Pro, 2.0 Flash, 1.5 Pro/Flash), select a persona, or enforce a specific skill
- **Dark / Light Mode** — fully themeable UI


### Quick Launch

```bash
pip install biblematedata google-antigravity nicegui Pillow
biblematedata
python3 web_app.py
```

Then open **[http://localhost:33377](http://localhost:33377)** in your browser.

> **Full setup guide:** [`docs/standalone_web_app.md`](docs/standalone_web_app.md)

---

## Quick Start for a Local Workspace

Prerequisites: Install the database (one-off operation):

```bash
pip install biblematedata
biblematedata
```

Download the agents and setup the workspace folder:

```bash
# Navigate to your workspace directory
cd <workspace_directory_name>
# Download and import into your workspace directory
curl -L -O https://github.com/eliranwong/antigravity-biblemate-workspace/raw/main/manual_setup.zip && tar -xf manual_setup.zip && rm manual_setup.zip && mkdir -p biblemate notes images export
```

Launch your platform of choice, for example:

```bash
# Google Antigravity (primary)
antigravity-ide # or 'antigravity' (GUI without text editor) or agy (Antigravity CLI)

# Optional: Claude Code or Grok Build — open this folder as the project/workspace root
# so `.claude/` or `.grok/` (+ AGENTS.md) are discovered automatically.
```

## Auto-Discovery

Because this repository is already configured with standard multi-platform workspace schemas, the custom personas, skills, and workflows are **automatically discovered and registered** when you open this project folder in your tool of choice.

### Antigravity (primary)

1. **Open Workspace**: Open the workspace root directory in your Antigravity-integrated IDE (such as Cursor or VS Code configured with the Antigravity extension) or run the CLI inside this directory:
   ```bash
   agy
   ```
2. **Auto-Discovery**: Antigravity automatically detects the `.agents/` directory at the project root. It will:
   - Load the 15 custom personas from `agents.md` into the agent selection registry.
   - Register the skills in `.agents/skills/` for progressive disclosure.
   - Expose the workflow files in `.agents/workflows/` as native slash commands.

3. **Meet Prerequisites**: Ensure you meet all system and platform prerequisites listed in [System Prerequisites](#system-prerequisites)

4. **Running Slash Commands**: In the Antigravity chat input, type `/` to bring up the commands menu, followed by arguments (e.g. references, topics, or words):
   - `/outline Ephesians 1`
   - `/sermon Romans 8:28`
   - `/translate-greek John 1:1`

### Claude Code & Grok Build (optional)

- **Claude Code**: open this repo as the project root; `.claude/skills/` and `.claude/commands/` are auto-discovered. See [Claude Code Equivalent Ecosystem](#-claude-code-equivalent-ecosystem-optional-bonus).
- **Grok Build**: open this repo as the workspace root; `.grok/skills/`, `.grok/commands/`, and root `AGENTS.md` are auto-discovered. See [Grok Build Equivalent Ecosystem](#-grok-build-equivalent-ecosystem-optional-bonus) and **[docs/grok_build_ecosystem.md](docs/grok_build_ecosystem.md)**.

Slash command **names** are the same across platforms (e.g. `/bible`, `/sermon`, `/biblemate`).

For a full reference of all available slash commands and usage examples, see the [Slash Commands Reference Guide](docs/slash_commands.md).

---

## System Prerequisites

To utilize the core capabilities of the local Bible study tools (such as database lookups and document exports), you must ensure the following dependencies are configured on your system:

1. **Local Bible Databases (`biblematedata`)**:  
   To enable local Scripture database lookups, you need to install the `biblematedata` package and initialize it:
   ```bash
   pip install --upgrade biblematedata
   biblematedata
   ```
   *Note: For more details on configuring database files, refer to the official [biblemate repository](https://github.com/eliranwong/biblemate).*

2. **Document Converter (`pandoc`)**:  
   To convert your study guides, outlines, and sermons into formats like Microsoft Word (`.docx`), ensure `pandoc` is installed on your system:
   - **macOS**: `brew install pandoc`
   - **Windows**: `winget install JohnMacFarlane.Pandoc` (or download the setup installer)
   - **Linux**: `sudo apt install pandoc` (or equivalent package manager command)

3. **AI platform subscription (at least one)**:  
   To run model inference for the agents and exegesis workflows, set up the
   platform(s) you intend to use:
   - **Google Antigravity** — primary experience; see the
     [Google Antigravity Documentation](https://antigravity.google/docs).
   - **Claude Code** (optional) — [Claude Code](https://claude.com/claude-code);
     uses the `.claude/` ecosystem. You can run Claude Code against a local or
     cloud [Ollama](https://ollama.com) backend, **GLM-5.2** is recommended for
     BibleMate study workflows.
   - **Grok Build** (optional) — [Grok Build / xAI](https://docs.x.ai/build/overview);
     uses the `.grok/` ecosystem and root `AGENTS.md`.


---

## Setting Up a New Repository

If you wish to bring these custom Bible study agents and tools into a **different, brand-new repository** of your own, follow these steps:

1. **Copy Configuration & Preferences (Choose one method)**:
   - **Method A - Git users (Recommended for developers)**: **Fork** this repository on GitHub and `git clone` it. This is highly recommended because when you write your own studies, generate exports, and run the `/sync` command, all changes will be synchronized cleanly to your own personal remote repository.
   - **Method B - Download (Zip File)**: Download [manual_setup.zip](https://github.com/eliranwong/antigravity-biblemate-workspace/raw/main/manual_setup.zip) into the root of your new project and extract it:
      * **Via Terminal (Recommended)**: Run the command for your operating system in your project root to download, extract, and clean up:
        * **macOS / Linux**:
          ```bash
          curl -L -O https://github.com/eliranwong/antigravity-biblemate-workspace/raw/main/manual_setup.zip && tar -xf manual_setup.zip && rm manual_setup.zip && mkdir -p biblemate notes images export
          ```
        * **Windows (PowerShell)**:
          ```powershell
          Invoke-WebRequest -Uri "https://github.com/eliranwong/antigravity-biblemate-workspace/raw/main/manual_setup.zip" -OutFile "manual_setup.zip"; Expand-Archive -Path "manual_setup.zip" -DestinationPath "." -Force; Remove-Item -Path "manual_setup.zip"; New-Item -ItemType Directory -Path "biblemate","notes","images","export" -Force
          ```
        * **Windows (Command Prompt)**:
          ```cmd
          curl.exe -L -O https://github.com/eliranwong/antigravity-biblemate-workspace/raw/main/manual_setup.zip && tar -xf manual_setup.zip && del manual_setup.zip && md biblemate notes images export
          ```
      * **Via GUI (Double-Click)**: If you extract using double-click on macOS, the OS will wrap the contents in a `manual_setup` folder. Simply move the configuration folders (e.g. `.agents/`, `preferences/`, `.claude/`, `.grok/`) and any root project-rules files (e.g. `AGENTS.md`) out of it and into your project root.
      *(You can generate or regenerate this zip file at any time by running the `/zip` command on the platform you use. Contents can vary by platform: Antigravity/Claude zip flows traditionally ship `.agents/` + `preferences/` + `.claude/`; the Grok `/zip` skill packages `.grok/`, `preferences/`, and `AGENTS.md`.)*
   - **Method C - Manual Copy (Folders)**: Manually copy the platform trees you need from this repository into the root of your new project:
      * **Antigravity**: `.agents/` + `preferences/`
      * **Claude Code**: `.claude/` (+ optionally root `CLAUDE.md` / `Claude.md`)
      * **Grok Build**: `.grok/` + root `AGENTS.md` (+ `preferences/` for shared defaults)

      Antigravity discovers `.agents/`; Claude Code discovers `.claude/`; Grok Build discovers `.grok/` and `AGENTS.md`. Shared `preferences/` preserves default database versions.

2. **Install System Prerequisites**: Ensure you have configured the [System Prerequisites](#system-prerequisites) on your system.

### How to Update
To update your workspace with the latest agent configurations, skills, and command definitions:
* **For Git users (Method A)**: Simply run `git pull` in your terminal to fetch and merge the latest updates from the upstream repository.
* **For Manual users (Method B or C)**:
  * **Via Slash Command (macOS/Linux only)**: Run the `/update` command in the chat interface on your platform. This refreshes sources and regenerates that platform's ecosystem where applicable.
  * **Via Terminal**: Redo the manual download or re-copy the trees you use (`.agents/`, `preferences/`, `.claude/`, `.grok/`, and for Grok also `AGENTS.md`) into your repository root, overwriting the existing directories. To rebuild generated trees without re-downloading:
    ```bash
    python3 .claude/build_claude.py   # Claude from .agents/ + preferences/
    python3 .grok/build_grok.py       # Grok from .claude/
    ```

---

## Preferences & Customization

You can easily configure your preferred default versions for Bible translation, commentary, and lexicon lookups without modifying any code. To do this, edit the plain text files under the `preferences/` folder at the root of the repository:

- **Bible Default Version**: Set your preference (e.g. `NET`, `KJV`, `BSB`) in [preferences/bible.md](preferences/bible.md).
- **Commentary Default Version**: Set your preference (e.g. `AIC`, `BI`, `BARNES`) in [preferences/commentary.md](preferences/commentary.md).
- **Lexicon Default Version**: Set your preference (e.g. `SECE`, `BDB`, `Thayer`) in [preferences/lexicon.md](preferences/lexicon.md).

These files are dynamically read by the respective retrievers on every execution.

---

## Documentation

For in-depth details about the web app, workflows, slash commands, and team structure, please refer to the files under the [docs/](docs) directory:

- **[claude_code_ecosystem.md](docs/claude_code_ecosystem.md)**: How to use the Claude Code (Anthropic) BibleMate ecosystem under `.claude/`—setup, slash commands, subagents/personas, scripture rules, regeneration, and troubleshooting.
- **[grok_build_ecosystem.md](docs/grok_build_ecosystem.md)**: How to use the Grok Build (xAI) BibleMate ecosystem under `.grok/`—setup, slash commands, personas/agents, regeneration, and troubleshooting.
- **[standalone_web_app.md](docs/standalone_web_app.md)**: Complete setup and usage guide for the standalone NiceGUI web application (`web_app.py`), including installation, slash commands, image generation, settings, and troubleshooting.
- **[ai_team_personas.md](docs/ai_team_personas.md)**: Detailed profiles, guidelines, and expertise profiles for each of the 15 custom AI study personas.
- **[slash_commands.md](docs/slash_commands.md)**: A complete reference guide for all 120 custom slash commands (workflows), organized by study category with syntax examples.
- **[study_outputs.md](docs/study_outputs.md)**: A guide explaining where and how study outputs, images, and Word exports are saved within your workspace.
- **[README.md (Documentation Index)](docs/README.md)**: Index and overview of repository documentation.

