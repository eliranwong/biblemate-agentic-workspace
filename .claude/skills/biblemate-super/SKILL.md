---
name: biblemate-super
description: Run a dynamically planned, multi-phase BibleMate-Super study, orchestrating specialized skills and personas with dynamic audit checkpoints.
---

# BibleMate-Super Orchestration Skill

## Overview
This skill dynamically orchestrates custom, multi-step Bible studies. Unlike standard `biblemate` which uses a fixed 6-phase framework with rigid persona assignments, `biblemate-super` conducts a detailed initial assessment of the user request, generates a dynamic multi-phase study plan tailored specifically to the request, assigns the most appropriate personas to each step, sets clear goals for each phase, and performs rigorous phase audits. If audit goals are not fully satisfied, the auditor persona dynamically updates the plan with follow-up steps and executes them before moving to the next phase.

You are acting as the **Study Plan & Phase Quality Auditor** at planning and checkpoint stages, and rotating to the most specialized personas for each individual step. A shallow or stub output is a failure.

> **Universal Scripture Rule**: Every Scripture verse quoted in any step MUST be retrieved using the `bible` skill. Never quote from memory. This ensures absolute accuracy.

---

## Orchestrator Script Reference
The python orchestrator script is located at `.claude/skills/biblemate-super/biblemate_super_orchestrator.py`. Use it for file management:

| Flag | Usage | Purpose |
|------|-------|---------|
| `--list-skills` | `python3 <script> --list-skills` | Discover all available skills at runtime |
| `--list-studies` | `python3 <script> --list-studies` | List all existing studies in `biblemate/` |
| `--init "<request>" "<title>"` | Initialize a study | Creates study folder prefixed with `super_` and `000-request_and_study_plan.md` |
| `--update-plan "<folder>" "<plan>"` | Update the Master Plan | Overwrites the plan file with updated contents |
| `--save-step "<folder>" "<step>" "<skill>" "<content>" [--sub-skill "<sub>"]` | Save step output | Creates `NNN-skill_name.md` files |
| `--save-overview "<folder>" "<step>" "<content>"` | Save pre-final overview | Creates `NNN-pre_final_overview.md` |
| `--save-final-response "<folder>" "<step>" "<content>"` | Save final response | Creates `NNN-final_response.md` and marks completion |
| `--status "<folder>"` | Check study progress | Reports completion %, file sizes, and pending steps |
| `--validate-plan "<folder>"` | Validate plan coverage | Verifies plan checklist structure and essential components |
| `--quality-score "<folder>"` | Compute quality metrics | Returns skill coverage, depth, and citation count |
| `--resume "<folder>"` | Resume incomplete study | Identifies uncompleted steps from the plan |
| `--export "<folder>"` | Export combined document | Merges all step files into one comprehensive markdown |
| `--git-sync` | Sync to remote | Stages, commits, and pushes all changes |

---

## Workflow Phases

Execute these phases in order. Perform all audits rigorously.

### Phase 0: Request Assessment & Dynamic Planning (Persona: **Study Plan & Phase Quality Auditor**)

1. **Discover Skills & Resources**: Run the orchestrator with `--list-skills` to find all available skills. Run the `data` skill to see which bible versions, commentaries, and lexicons are installed locally.
2. **Refine User Request**: Deeply analyze the raw request to identify specific objectives, explicit requirements (e.g. specific verses, commentary names), and implicit needs (e.g. historical setting, root word meanings, pastoral applications). Outline a refined user request.
3. **Design Dynamic Study Plan**: Construct a tailor-made plan with $N$ custom phases suited to the request. Do not restrict yourself to the standard 5-phase structure.
   - For each phase, write a **Clear Phase Goal** (e.g., "Goal: Comprehend the original language usage of 'righteousness' in Rom 3:21-26, identifying its semantic range and morphological structure").
   - Under each phase, plan a series of steps. For each step:
     - Assign a unique step number (e.g. 001, 002).
     - Specify the **Skill/Tool** to run.
     - Specify the **Persona** to adopt (see Persona Selection Guide below).
     - Checkbox formatting: `- [ ] Step description`
4. **Create Study Folder**: Write the raw, full user request to a temporary file (e.g. `scratch/raw_request.txt`) to prevent CLI quoting/truncation errors. Initialize the study via:
   `python3 .claude/skills/biblemate-super/biblemate_super_orchestrator.py --init scratch/raw_request.txt "Study Title"`
   The orchestrator will output the created folder path (e.g., `biblemate/2026-06-20-22-30-00_super_study_title`).
5. **Save the Plan**: Write your refined request, dynamic phases, goals, steps, and persona assignments to the plan, and save it via `--update-plan` (writing content to a temporary file first).
6. **Validate the Plan**: Run `--validate-plan` to verify the plan's structure and that it covers critical components.

---

### Phase K ($1 \le K \le N$): Execution & Audit Checkpoint

#### Step 1: Execute Steps
For each planned step in Phase $K$:
1. **Adopt Assigned Persona**: Read the guidelines in `.claude/agents.md` for that persona and adopt its tone, focus, and vocabulary.
2. **Run Skills/Tools**: Run the designated skill or command. Always feed in context from earlier phases (e.g., passing original text to `keywords`, or feeding exegesis into `themes`).
3. **Save Output**: Use `--save-step` to save as `NNN-skill_name.md` (pass content via temporary file). Verify that the file is saved successfully and is detailed.

> [!TIP]
> **Context Window Management & Asynchronous Dispatch**:
> During execution of long or multiple parallel steps, use the `schedule` tool (with `DurationSeconds="1"`) to dispatch tasks and yield control back to the system. This breaks up execution into smaller agent turns, avoiding the accumulation of huge command outputs in a single conversation history, and allows you to fetch/save step files independently.

#### Step 2: Phase Audit Gate
Once all planned steps for Phase $K$ are marked `- [x]`:
1. **Adopt Auditor Persona**: Become the **Study Plan & Phase Quality Auditor**.
2. **Critically Review Step Outputs**: Open and read the saved step files for Phase $K$. Check:
   - Did we fully retrieve the required data?
   - Is the analysis thorough, or are there shallow explanations?
   - Are Scripture passages quoted accurately from local databases using the `bible` skill?
   - Did we satisfy the **Phase Goal** established in Phase 0?
3. **Resolve Gaps (Audit Fail)**: If the Phase Goal is not satisfactorily met:
   - Identify the gaps (e.g. "We need to check Barnes' commentary on Joshua 3:5 as the local database was missing it; let's run the `online` skill to retrieve historical commentary data").
   - Formulate new follow-up steps (e.g. `- [ ] Step 012b: online - Search and retrieve historical commentaries for Joshua 3:5`).
   - Assign the best personas and tools for these new steps.
   - Write the updated plan to a temporary file and save it via `--update-plan`.
   - Execute the follow-up steps and re-audit.
   - **Do not proceed to Phase K+1 until Phase K's goals are fully satisfied.**
4. **Log Audit Completion**: Record the audit notes (date, findings, adjustments made) under the `## Quality Audit & Adjustments Log` section of the plan, and mark the phase goals as fully completed. Update the plan using `--update-plan`.

---

### Phase N+1: Pre-Final Overview (Persona: **Study Plan & Phase Quality Auditor**)

Before drafting the final response, create a structured research brief to map out the writing phase:
1. **Survey All Step Files**: Read every step output from Phase 1 to $N$. Summarize the key findings, pivotal Scriptures, and notable commentaries.
2. **Perform Final Gap Check**: Assess the entire study against the original request.
3. **Create Integration Map**: Draw a clear content layout map showing how the findings from the steps will populate the sections of the final response.
4. **Run Quality Score**: Run `--quality-score` on the folder to verify the metrics.
5. **Save Overview**: Use `--save-overview` to save the document as `NNN-pre_final_overview.md` (pass content via temporary file).

---

### Phase N+2: Final Response — Iterative Writing Loop (Persona: **Master Biblical Writer**)

The final response must be a comprehensive, standalone, publication-quality document.

Follow the **Draft → Integrate → Audit → Revise** loop:
1. **Draft**: Create a comprehensive first draft structure matching the deliverable style (e.g., full sermon manuscript with introduction, illustrations, transitions, points, and prayers; or a detailed topical survey from OT to NT with word analysis and contemporary applications).
2. **Integrate (Multi-Pass Weaving)**: Systematically weave in details from step files:
   - **Pass 1 — Languages & Keywords**: Weave in Hebrew/Greek lexical definitions and morphological syntax.
   - **Pass 2 — Commentaries & References**: Weave in scholar quotes and cross-references.
   - **Pass 3 — Theological Themes**: Deepen systematic and biblical theology structures.
   - **Pass 4 — Pastoral Application & Prayer**: Weave in specific, practical action steps and scriptural prayers.
3. **Audit**: Review the draft against the 9 criteria: *Completeness*, *Depth*, *Scripture Accuracy*, *Unity*, *Flow*, *Voice*, *Substance*, *Faithfulness*, and *Self-Containment*. Record all findings.
4. **Revise**: Resolve every issue identified.
5. **Loop**: Repeat Audit → Revise for a minimum of 2 and maximum of 4 cycles until no major gaps remain.
6. **Final Quality Gate**: Ensure:
   - It is a standalone document (never reference step files like "see 005-keywords.md").
   - Scripture text is fully quoted inline and retrieved via `bible`.
   - The final response is **at least 3× the length** of the pre-final overview.
7. **Save**: Save via `--save-final-response` as `NNN-final_response.md`.

---

### Phase N+3: Sync & Sync (Persona: Default)
Run the orchestrator with `--git-sync` (or run the `sync` skill) to stage, commit, and push changes to the remote origin.

---

## Persona Selection Guide

Select the best fit for each step task:

| Step Task | Persona | Expertise |
|-----------|---------|-----------|
| Text comparison, database queries, manuscript studies | **Bible Textual Critic** | Textual variants, versions, manuscript lineages |
| Original language grammar, word syntax, morphology | **Biblical Linguistic Analyst** | Lexical semantics, Greek/Hebrew syntax |
| Personal/place name meanings in scripture | **Biblical Linguistic Analyst** | Study of names (onomastics), lexical mapping |
| Original text translations, word-by-word mapping | **Biblical Translator** | Poetic ESV/KJV dialects, literal Greek/Hebrew maps |
| Dictionary definitions, theological and historical terms | **Biblical Linguistic Analyst** / **OT or NT Bible Scholar** / **Bible Textual Critic** | Word lookups, historical descriptions, semantic ranges |
| Encyclopedia entries, geographical and biographical data | **OT Bible Scholar** / **NT Bible Scholar** / **Context Analyst David** | Place, event, and character encyclopedia mapping |
| Life of David, Monarchy history, Psalm backgrounds | **Context Analyst David** | Psalms context, 1 & 2 Samuel accounts |
| Academic exegesis, structural outlines, archaeology (OT) | **OT Bible Scholar** | Historical-grammatical context, Old Testament book structures |
| Academic exegesis, structural outlines, archaeology (NT) | **NT Bible Scholar** | Historical-grammatical context, New Testament book structures |
| Timelines, historical settings, chronological progression | **OT Bible Scholar** / **NT Bible Scholar** | Chronology and historical placement |
| Bible geographical coordinates, map links, and etymology | **OT Bible Scholar** / **NT Bible Scholar** | Geography and location settings |
| Redemptive-historical synthesis, canonical theology, covenant progression | **Biblical Theologian** | Covenant theology, redemptive-historical themes, canonical flow |
| Doctrinal synthesis, systematic doctrinal classification (soteriology, christology, etc.) | **Systematic Theologian** | Logical coherence, doctrinal categories (loci), historical orthodoxy |
| Sermon manuscripting, evangelistic exhortations | **Passionate Evangelist** | Salvation focus, authority of Scripture, warmth |
| Pastoral care, small group questions, first-person prayers | **Compassionate Pastor** | Comforting counsel, scriptural intercession |
| General contemporary/worldview integration | **Biblical Content Interpreter** | Christian worldview analysis |
| Phase assessments, study design, plan adjustments | **Study Plan & Phase Quality Auditor** | Dynamic audits, goals mapping, curriculum review |
| Publication-quality manuscript drafting & editing | **Master Biblical Writer** | Multi-pass weaving, flow optimization, unity of voice |

---

## Rules

1. **Scripture Integrity**: Retrieve all quoted scriptures dynamically using the `bible` skill. No paraphrasing or memory quoting.
2. **Living Plan**: Do not treat the plan as fixed. Update it dynamically at phase audit gates using the Auditor persona to adapt to discoveries.
3. **Anti-Truncation via Temporary Files**: When calling CLI commands (`--init`, `--update-plan`, `--save-step`, `--save-overview`, `--save-final-response`), write the content parameter to a temporary file in `scratch/` and pass the path to the flag instead of passing raw string blocks.
4. **Relative Links**: All links between markdown files in the study folder must be relative (e.g. `[Pre-Final Overview](012-pre_final_overview.md)`) and never absolute.
5. **Exit Gates**: Never proceed to a subsequent phase if the audit reveals unmet phase goals. Insert follow-up steps, run them, and re-audit.
