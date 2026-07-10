---
description: Run a fully automated BibleMate AI study, orchestrating multiple study skills and tools to complete a detailed theological or exegetical request.
---

Adopt the **Biblical Content Interpreter** persona from `.claude/agents.md`.

Use the **biblemate** skill to orchestrate and execute the study. Read the full SKILL.md file at `.claude/skills/biblemate/SKILL.md` before beginning — it contains the complete workflow phases, skill taxonomy, minimum coverage requirements, quality gates, persona rotation guidance, and the iterative writing process for the final response.

Before beginning the study:
1. Run the orchestrator with `--list-skills` to discover all currently available skills.
2. Read each relevant skill's SKILL.md to understand its parameters and output format.
3. Run the `data` skill to check which bible versions, commentaries, and lexicons are available locally.
4. **Read Request File (If Applicable)**: If the User Request below specifies a file path (e.g. `biblemate/my_request.txt`), use the `Read` tool to read the contents of that file and use those contents as the actual raw user request for all subsequent planning, refinement, and execution.

Then orchestrate a complete, multi-step BibleMate study following all seven workflow phases:
- **Phase 0**: Initialization & Planning (IMPORTANT: Write the user's raw, detailed request exactly as-is to a temporary file in the `scratch/` directory, and pass that file path to `--init` to preserve all requirements and avoid command-line truncation/quoting errors.)
- **Phase 1**: Data Retrieval
- **Phase 2**: Analysis & Exegesis
- **Phase 3**: Theological Synthesis
- **Phase 4**: Application & Devotion
- **Phase 5**: Pre-Final Overview & Synthesis Audit (save `NNN-pre_final_overview.md`)
- **Phase 6**: Final Response — Iterative Draft→Integrate→Audit→Revise writing loop (save `NNN-final_response.md`)
- **Phase 7**: Sync to Git

The final response (Phase 6) is the primary deliverable. It must be a comprehensive, standalone, publication-quality document that directly answers the original request — produced through iterative writing and refinement, not a single-pass output.

# User Request

$ARGUMENTS
