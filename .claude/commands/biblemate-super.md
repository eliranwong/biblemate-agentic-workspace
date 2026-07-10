---
description: Run a dynamically planned, multi-phase BibleMate-Super study, orchestrating specialized skills and personas with dynamic audit checkpoints.
---

Adopt the **Study Plan & Phase Quality Auditor** persona from `.claude/agents.md`.

Use the **biblemate-super** skill to orchestrate and execute the study. Read the full SKILL.md file at `.claude/skills/biblemate-super/SKILL.md` before beginning — it contains the dynamic workflow phases, persona rotation guide, dynamic validation rules, quality gates, phase audits, and the iterative writing process for the final response.

Before beginning the study:
1. Run the orchestrator script `.claude/skills/biblemate-super/biblemate_super_orchestrator.py` with `--list-skills` to discover all currently available skills.
2. Read each relevant skill's SKILL.md to understand its parameters and output format.
3. Run the `data` skill to check which bible versions, commentaries, and lexicons are available locally.
4. **Read Request File (If Applicable)**: If the User Request below specifies a file path (e.g. `biblemate/my_request.txt`), use the `Read` tool to read the contents of that file and use those contents as the actual raw user request for all subsequent planning, refinement, and execution.

Then orchestrate a complete, dynamically planned BibleMate-Super study:
- **Phase 0**: Request Assessment & Dynamic Planning (IMPORTANT: Write the user's raw, detailed request exactly as-is to a temporary file in the `scratch/` directory, and pass that file path to `--init` to preserve all requirements and avoid command-line truncation/quoting errors.)
- **Phase K (1 to N)**: Step Execution & Auditor Checkpoints (Update the plan and run extra steps if phase goals are not fully met.)
- **Phase N+1**: Pre-Final Overview (save `NNN-pre_final_overview.md`)
- **Phase N+2**: Final Response — Iterative Draft→Integrate→Audit→Revise writing loop (save `NNN-final_response.md` using the **Master Biblical Writer** persona)
- **Phase N+3**: Git Sync

The final response is the primary deliverable. It must be a comprehensive, standalone, publication-quality document that directly and thoroughly answers the original request — produced through the iterative writing and refinement loop.

# User Request

$ARGUMENTS
