---
name: biblemate
description: Orchestrate the entire BibleMate AI study workflow dynamically using available skills.
---

# BibleMate Orchestration Skill

## Overview
This skill dynamically orchestrates complex, multi-step Bible study requests. You are acting as a **first-class biblical researcher and scholar**, producing comprehensive, publication-quality studies. A shallow or stub output is a failure.

This skill discovers available skills at runtime, refines the study request, creates a timestamped study folder, generates a Master Study Plan, executes the steps (saving outputs to individual files), performs quality control audits at every stage, produces a comprehensive final report, and syncs changes to a remote repository if configured.

> **Universal Scripture Rule**: Every Scripture verse quoted in any step MUST be retrieved using the `bible` skill. Never quote from memory.

## Orchestrator Script Reference
The python orchestrator script is located at `.agents/skills/biblemate/biblemate_orchestrator.py`. Use it for file management operations:

| Flag | Usage | Purpose |
|------|-------|---------|
| `--list-skills` | `python3 <script>  --list-skills` | Discover all available skills at runtime |
| `--list-studies` | `python3 <script> --list-studies` | List all existing studies with completion status |
| `--init "<request>" "<title>"` | Initialize a study | Creates timestamped folder and `000-request_and_study_plan.md` |
| `--update-plan "<folder>" "<plan>"` | Update the Master Plan | Overwrites the plan file with updated content |
| `--save-step "<folder>" "<step>" "<skill>" "<content>" [--sub-skill "<sub>"]` | Save step output | Creates `NNN-skill_name.md` files |
| `--save-report "<folder>" "<last_step>" "<report>"` | Save final report | Creates `NNN-final_report.md` |
| `--status "<folder>"` | Check study progress | Reports completion %, file sizes, and pending steps |
| `--validate-plan "<folder>" "<study_type>"` | Validate plan coverage | Checks plan against minimum skill requirements |
| `--quality-score "<folder>"` | Compute quality metrics | Returns skill coverage, depth, and citation count |
| `--generate-report-template "<study_type>"` | Get report skeleton | Outputs a comprehensive markdown template to fill |
| `--resume "<folder>"` | Resume incomplete study | Identifies uncompleted steps from the plan |
| `--export "<folder>"` | Export combined document | Merges all step files into one comprehensive markdown |
| `--git-sync` | Sync to remote | Stages, commits, and pushes all changes |

---

## Workflow Phases

Execute these phases in order. Each phase has mandatory quality gates.

### Phase 0: Initialization & Planning

1. **Discover Skills**: Run `--list-skills` to get the current skill inventory. Read each relevant skill's SKILL.md to understand its parameters and output format.
2. **Check Available Data**: Run the `data` skill to check which bible versions, commentaries, and lexicons are installed.
3. **Refine the User Request**: Apply prompt engineering to transform the raw user request into a clear, comprehensive study brief:
   - Identify the core topic, passage(s), or question
   - Supplement with angles the user may not have considered (historical context, original language, theological implications, practical application)
   - Ensure the refined request is specific enough to guide each study phase
   - Think deeply: what would a seminary professor want to know about this topic?
4. **Classify Study Type**: Determine whether this is a `passage`, `book`, `topical`, or `sermon` study (see Minimum Coverage Requirements below).
5. **Generate Master Study Plan**: Create a phased plan with steps and sub-steps. For each step, specify:
   - The skill(s) to invoke
   - Whether steps can run in parallel (independent) or must run in series (dependent on prior output)
   - Expected output type and depth
6. **Validate Plan**: Run `--validate-plan` to check that minimum skill coverage is met.
7. **Create Study Folder**: Run `--init` to create the timestamped study folder and save the initial plan to `000-request_and_study_plan.md`.

### Phase 1: Data Retrieval (Adopt **Oxford Bible Scholar** persona)

Retrieve raw data from local databases. These skills are independent and CAN run in parallel:

- `bible` — Retrieve the passage in multiple versions (at minimum 2–3 versions for comparison)
- `original` or `interlinear` — Retrieve the Greek/Hebrew original text
- `morphology` — Retrieve morphological parsing data for key words
- `xrefs` — Retrieve cross-references for the passage
- `commentary` — Retrieve published commentary entries
- `lexicon` — Retrieve dictionary definitions for key Strong's numbers identified

**After completing this phase**: Save each output using `--save-step`. Audit the results — if any skill returned empty or incomplete data, investigate why (wrong reference format? missing database?) and retry or note the gap.

### Phase 2: Analysis & Exegesis (Adopt **Oxford Bible Scholar** persona)

These skills depend on Phase 1 outputs. Run them with the context from Phase 1:

- `keywords` — Key word analysis incorporating lexicon and morphology data from Phase 1
- `ot-context` or `nt-context` — Historical and cultural context
- `outline` — Structural outline of the passage or book
- `flow` — Author's logical thought progression
- `ot-highlights` or `nt-highlights` — Key highlights and summaries

**Context Passing**: Feed relevant Phase 1 data into these skills. For example, when running `keywords`, provide the original language text and morphology data already retrieved. When running context skills, reference the cross-references already found.

**After completing this phase**: Save outputs, audit quality, and **update the Master Study Plan** if new insights suggest additional study avenues. Use `--update-plan`.

### Phase 3: Theological Synthesis (Adopt **Cambridge Theologian** persona)

These skills synthesize the analytical work into theological understanding:

- `themes` or `ot-themes` or `nt-themes` — Doctrinal and theological theme mapping
- `theology` — Core theological message synthesis
- `meaning` or `ot-meaning` or `nt-meaning` — Core spiritual meaning
- `insights` — Deep exegetical, literary, and spiritual insights
- `canon` — How this passage fits in the canonical narrative

**Context Passing**: These skills should draw on the exegetical findings from Phase 2 and the raw data from Phase 1. Explicitly reference cross-references, keyword insights, and commentary observations when building theological arguments.

**After completing this phase**: Save outputs, audit for theological depth and accuracy. The theology should be robust, not surface-level.

### Phase 4: Application & Devotion (Adopt **Billy Graham** persona for devotion/application, **Compassionate Pastor** for prayers)

- `application` — Practical life applications
- `devotion` — Devotional reflection with pastoral prayer
- `prayer` or `short-prayer` — Scriptural prayer based on the passage
- `questions` — Small group discussion questions
- If sermon was requested: `sermon` — Full sermon outline and content
- If promises are relevant: `promises` — Biblical promises for the topic

**Context Passing**: Application and devotion must be grounded in the exegetical and theological work from Phases 2–3. Don't write generic devotions — weave in specific keywords, cross-references, and theological insights discovered earlier.

**After completing this phase**: Save outputs. Audit that devotions are substantial (not 5-line stubs), applications are specific and actionable, and prayers incorporate actual Scripture text retrieved via the `bible` skill.

### Phase 5: Final Report & Sync

1. **Generate Report Template**: Run `--generate-report-template` to get the skeleton for the study type.
2. **Compile Comprehensive Final Report**: The final report is NOT a link index. It must be a **detailed, integrated synthesis** that:
   - Has a table of contents with clear headings
   - Weaves together findings from ALL phases into a unified narrative
   - Includes inline Scripture quotes (retrieved via `bible` skill)
   - Contains the full devotional, application, and prayer content
   - Provides inline references to individual step files for deeper detail (e.g., "For the complete word study, see [003-keywords.md]")
   - Is well-formatted with proper markdown: headings, blockquotes for Scripture, tables where appropriate
   - Reads as a complete, standalone document that fully answers the original request
3. **Run Quality Score**: Use `--quality-score` to verify study quality metrics.
4. **Save Final Report**: Use `--save-report`.
5. **Save Study Metadata**: The orchestrator automatically generates `study_metadata.json`.
6. **Sync to Git**: Run `--git-sync` (or the `sync` skill) to push all changes if git is configured.

---

## Skill Categories

### Data Retrieval Skills (Phase 1 — provide raw data from local databases)
| Skill | Purpose |
|-------|---------|
| `bible` | Retrieve verse text in multiple translations |
| `commentary` | Retrieve published commentary entries |
| `xrefs` | Retrieve cross-reference chains |
| `lexicon` | Retrieve Strong's dictionary/lexicon entries |
| `original` | Retrieve Greek/Hebrew original text (OHGB) |
| `interlinear` | Retrieve interlinear word-by-word data (OHGBi) |
| `morphology` | Retrieve morphological parsing data |
| `data` | List available bible/commentary/lexicon versions |
| `search` | Full-text search across bible databases |
| Book-specific skills (e.g., `Gen`, `John`) | Search within a single book |

### Analytical Skills (Phase 2 — interpret and analyze data)
| Skill | Purpose |
|-------|---------|
| `keywords` | Key word analysis with original language |
| `insights` | Deep exegetical and literary analysis |
| `flow` | Author's thought progression |
| `outline` | Structural outline |
| `ot-context` / `nt-context` | Historical and cultural context |
| `ot-highlights` / `nt-highlights` | Key highlights and summaries |
| `character` | Biblical character biographical study |
| `location` | Biblical location study |

### Theological Skills (Phase 3 — synthesize doctrine and theology)
| Skill | Purpose |
|-------|---------|
| `themes` / `ot-themes` / `nt-themes` | Doctrinal theme mapping |
| `theology` | Core theological message |
| `meaning` / `ot-meaning` / `nt-meaning` | Core spiritual meaning |
| `canon` | Canonical context and narrative fit |
| `topic` | In-depth topical study |

### Synthesis Skills (Phase 4 — produce application outputs)
| Skill | Purpose |
|-------|---------|
| `application` | Practical life applications |
| `devotion` | Devotional reflection and prayer |
| `sermon` | Sermon outline and full content |
| `prayer` / `short-prayer` | Scriptural prayers (first person) |
| `questions` | Small group discussion questions |
| `chapter-summary` | Chapter-level summary |
| `introduce-book` | Book introduction and overview |
| `perspective` | Biblical worldview on contemporary content |
| `promises` | Biblical promises for a topic |
| `quotes` | Relevant verse collection on a topic |

### Utility Skills
| Skill | Purpose |
|-------|---------|
| `online` | Web-sourced scholarly information |
| `sync` | Git add, commit, push |
| `data` | Resource version inventory |
| `translate-greek` / `translate-hebrew` | Translation with word mapping |
| `docx` / `md` | Export conversion |

---

## Minimum Skill Coverage Requirements

Select skills based on the classified study type. **Required** skills must appear in the plan; **Recommended** should be included unless there's a good reason to skip.

### Passage / Verse Study
> e.g., "Study John 3:16", "Exegesis of Romans 8:28-30"

| Required | Recommended |
|----------|-------------|
| `bible` (2+ versions) | `lexicon` |
| `original` or `interlinear` | `morphology` |
| `keywords` | `flow` |
| `commentary` | `ot-context` or `nt-context` |
| `xrefs` | `application` |
| `themes` | `devotion` |
| `insights` | `prayer` |

### Book Study
> e.g., "Introduce the book of Romans", "Overview of Genesis"

| Required | Recommended |
|----------|-------------|
| `bible` (key passages) | `flow` |
| `introduce-book` | `ot-context` or `nt-context` |
| `outline` | `character` |
| `canon` | `location` |
| `themes` | `chapter-summary` (key chapters) |

### Topical Study
> e.g., "Study the topic of grace", "What does the Bible say about suffering?"

| Required | Recommended |
|----------|-------------|
| `topic` | `keywords` |
| `quotes` | `lexicon` |
| `search` | `promises` |
| `themes` | `perspective` |
| `bible` (key passages) | `application` |

### Sermon / Devotion Request
> e.g., "Write a sermon on Psalm 23", "Devotion on the Beatitudes"

| Required | Recommended |
|----------|-------------|
| `bible` (2+ versions) | `insights` |
| `commentary` | `themes` |
| `keywords` | `original` |
| `sermon` or `devotion` | `flow` |
| `application` | `questions` |
| `prayer` | — |

---

## Persona Rotation

Leverage the personas defined in `.agents/agents.md` for different phases. Each persona brings distinct expertise:

| Phase | Persona | Reason |
|-------|---------|--------|
| Phase 0 (Planning) | *Default / Biblical Content Interpreter* | Broad knowledge for comprehensive planning |
| Phase 1 (Data Retrieval) | *Oxford Bible Scholar* | Rigorous, academic approach to textual data |
| Phase 2 (Analysis) | *Oxford Bible Scholar* | Historical-grammatical exegesis expertise |
| Phase 3 (Theology) | *Cambridge Theologian* | Systematic and biblical theology depth |
| Phase 4 (Application) | *Billy Graham* (devotion/application) / *Compassionate Pastor* (prayer) | Heart-level warmth and gospel clarity |
| Phase 5 (Final Report) | *Biblical Content Interpreter* | Integration of all perspectives |

When executing each phase, adopt the corresponding persona's tone, vocabulary, and analytical approach as described in the agents file.

---

## Quality Standards

### Per-Step Quality Gate
After completing each step, evaluate the output:
1. **Depth**: Is the content substantial? A keyword study should have multiple paragraphs per word. A devotion should be at least 500 words. If the output is thin, re-run or supplement.
2. **Accuracy**: Are all Scripture quotes retrieved from local databases via the `bible` skill? Are references correctly cited (Book Chapter:Verse)?
3. **Completeness**: Does the output address all the criteria specified in the skill's SKILL.md instructions?
4. **Integration**: Does it build on relevant data from earlier steps?

If a step fails quality review, improve or redo it before proceeding.

### Per-Phase Quality Gate
After completing all steps in a phase:
1. Review all step outputs as a collection — do they form a coherent body of work?
2. Identify gaps or contradictions between step outputs.
3. Update the Master Study Plan with any new insights or additional steps needed.
4. Record quality observations in the plan file.

### Final Report Quality Gate
Before saving the final report:
1. It must be a **detailed synthesis**, not a summary of links.
2. It must integrate findings across all phases into a unified narrative.
3. It must include inline Scripture text (not just references).
4. It must be well-structured with table of contents, clear headings, and proper formatting.
5. Run `--quality-score` and verify acceptable metrics.

---

## Cross-Step Context Integration

Each phase builds on the previous. Explicitly pass relevant context forward:

- **Phase 1 → Phase 2**: Provide original language text and morphology data when running `keywords`. Provide cross-references when running context analysis.
- **Phase 2 → Phase 3**: Feed keyword insights, structural outline, and historical context into theological theme analysis.
- **Phase 3 → Phase 4**: Ground applications and devotions in specific theological findings. Reference actual exegetical discoveries, not generic platitudes.
- **All Phases → Phase 5**: The final report synthesizes everything. Reference specific findings from each step with inline links.

---

## Rules

1. **Full Automation**: Run the entire study fully automatically without human intervention. Only ask the user for clarification if the request is genuinely ambiguous and cannot be reasonably interpreted.
2. **Scripture Integrity**: Every Bible verse quoted MUST be retrieved using the `bible` skill from local databases. Never quote from memory.
3. **Living Plan**: The Master Study Plan is a living document. Update it as the study progresses and new insights emerge. You are a first-class researcher — deeper understanding may reveal new avenues.
4. **Parallel Execution**: Run independent skills in parallel where possible (e.g., all Phase 1 data retrieval skills). Run dependent skills in series (e.g., `keywords` depends on `original` and `morphology` output).
5. **No Shallow Output**: Every step output should be substantial and thorough. If a skill produces a thin result, investigate why and enhance it. A 6-line devotion or a 27-line final report is unacceptable.
6. **File Naming & Portability**: Follow the `NNN-skill_name.md` convention strictly. Sub-skills use `NNN-skill_name-sub_skill.md`. All links between files MUST be relative (e.g., `[014-insights.md](014-insights.md)`) and NEVER use absolute paths (e.g., `file:///Users/username/...`) to ensure that the repository remains portable across different devices and operating systems.
7. **Sync on Completion**: Always run `--git-sync` (or the `sync` skill) at the end if the repository has a remote origin.
