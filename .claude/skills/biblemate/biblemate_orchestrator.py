#!/usr/bin/env python3
"""
BibleMate AI Orchestrator Script

Manages file operations, study lifecycle, validation, quality metrics,
and git synchronization for BibleMate AI studies.
"""
import os
import sys
import re
import json
import glob
import argparse
import datetime
import subprocess

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MINIMUM_COVERAGE = {
    "passage": {
        "required": ["bible", "original", "keywords", "commentary", "xrefs", "themes", "insights"],
        "recommended": ["lexicon", "morphology", "flow", "application", "devotion", "prayer",
                         "interlinear", "ot-context", "nt-context", "chronology", "names", "locations", "parallels"],
    },
    "book": {
        "required": ["bible", "book-analysis", "outline", "canon", "themes"],
        "recommended": ["flow", "ot-context", "nt-context", "characters", "chapter-summary", "chronology", "locations"],
    },
    "topical": {
        "required": ["topics", "quotes", "search", "themes", "bible"],
        "recommended": ["keywords", "lexicon", "promises", "perspective", "application", "parallels"],
    },
    "sermon": {
        "required": ["bible", "commentary", "keywords", "sermon", "application", "prayer"],
        "recommended": ["insights", "themes", "original", "flow", "questions", "devotion", "chronology", "names", "locations"],
    },
}

# Minimum acceptable content length (in characters) per skill type
MIN_CONTENT_LENGTH = {
    "bible": 200,
    "commentary": 300,
    "devotion": 1500,
    "sermon": 2000,
    "application": 800,
    "insights": 1000,
    "themes": 800,
    "theology": 600,
    "keywords": 600,
    "prayer": 300,
    "questions": 500,
    "chronology": 800,
    "names": 600,
    "daily-read": 500,
    "locations": 800,
    "default": 400,
}

FINAL_REPORT_TEMPLATES = {
    "passage": """# BibleMate Study: {title}

## Table of Contents
1. [Introduction & Study Context](#1-introduction--study-context)
2. [Scripture Text (Multiple Versions)](#2-scripture-text-multiple-versions)
3. [Original Language Analysis](#3-original-language-analysis)
4. [Key Word Study](#4-key-word-study)
5. [Historical & Cultural Context](#5-historical--cultural-context)
6. [Cross-References & Parallel Passages](#6-cross-references--parallel-passages)
7. [Commentary Insights](#7-commentary-insights)
8. [Theological Themes](#8-theological-themes)
9. [Exegetical Insights](#9-exegetical-insights)
10. [Practical Application](#10-practical-application)
11. [Devotional Reflection](#11-devotional-reflection)
12. [Prayer](#12-prayer)
13. [Discussion Questions](#13-discussion-questions)
14. [Conclusion & Summary](#14-conclusion--summary)
15. [Appendix: Individual Step Outputs](#15-appendix-individual-step-outputs)

---

## 1. Introduction & Study Context
*(Introduce the passage, its placement in Scripture, and the study objectives.)*

## 2. Scripture Text (Multiple Versions)
*(Present the passage in at least 2–3 translations for comparison.)*

## 3. Original Language Analysis
*(Greek or Hebrew original text, transliteration, and key grammatical observations.)*

## 4. Key Word Study
*(Detailed analysis of each key term: original language, semantic range, contextual meaning, theological significance.)*

## 5. Historical & Cultural Context
*(What was happening historically? What cultural norms inform this text?)*

## 6. Cross-References & Parallel Passages
*(Related passages and how they illuminate the main text.)*

## 7. Commentary Insights
*(Key observations from published commentators.)*

## 8. Theological Themes
*(Doctrinal mapping across systematic theology categories.)*

## 9. Exegetical Insights
*(Literary features, structural patterns, and deeper interpretive observations.)*

## 10. Practical Application
*(Specific, actionable applications for daily life and spiritual growth.)*

## 11. Devotional Reflection
*(A substantial devotional meditation grounding the passage in personal faith.)*

## 12. Prayer
*(A scriptural prayer in the first person based on the passage.)*

## 13. Discussion Questions
*(Thought-provoking questions for small group or personal study.)*

## 14. Conclusion & Summary
*(Synthesize the study's major findings and their significance.)*

## 15. Appendix: Individual Step Outputs
*(Links to each step file for detailed reference.)*
""",
    "book": """# BibleMate Study: {title}

## Table of Contents
1. [Introduction & Background](#1-introduction--background)
2. [Author, Date & Setting](#2-author-date--setting)
3. [Key Scripture Passages](#3-key-scripture-passages)
4. [Structural Outline](#4-structural-outline)
5. [Canonical Context](#5-canonical-context)
6. [Major Themes & Theology](#6-major-themes--theology)
7. [Key Characters](#7-key-characters)
8. [Significant Locations](#8-significant-locations)
9. [Chapter Summaries](#9-chapter-summaries)
10. [Practical Application](#10-practical-application)
11. [Conclusion](#11-conclusion)
12. [Appendix: Individual Step Outputs](#12-appendix-individual-step-outputs)

---

## 1. Introduction & Background
*(Overview of the book, its genre, and historical significance.)*

## 2. Author, Date & Setting
*(Authorship, date of composition, original audience, and setting.)*

## 3. Key Scripture Passages
*(Representative passages in multiple translations.)*

## 4. Structural Outline
*(Detailed outline of the book's structure and flow.)*

## 5. Canonical Context
*(How this book fits within the broader biblical narrative.)*

## 6. Major Themes & Theology
*(Key doctrinal and theological themes.)*

## 7. Key Characters
*(Biographical studies of major figures.)*

## 8. Significant Locations
*(Geographical and historical significance of key locations.)*

## 9. Chapter Summaries
*(Summaries of key chapters.)*

## 10. Practical Application
*(How the book speaks to contemporary life.)*

## 11. Conclusion
*(Summary of the book's enduring message.)*

## 12. Appendix: Individual Step Outputs
*(Links to each step file for detailed reference.)*
""",
    "topical": """# BibleMate Study: {title}

## Table of Contents
1. [Introduction & Definition](#1-introduction--definition)
2. [Key Scripture Passages](#2-key-scripture-passages)
3. [Old Testament Foundation](#3-old-testament-foundation)
4. [New Testament Development](#4-new-testament-development)
5. [Key Word Analysis](#5-key-word-analysis)
6. [Theological Themes](#6-theological-themes)
7. [Biblical Promises](#7-biblical-promises)
8. [Contemporary Perspective](#8-contemporary-perspective)
9. [Practical Application](#9-practical-application)
10. [Conclusion](#10-conclusion)
11. [Appendix: Individual Step Outputs](#11-appendix-individual-step-outputs)

---

## 1. Introduction & Definition
*(Define the topic and its significance in Scripture.)*

## 2. Key Scripture Passages
*(Central passages addressing the topic, in multiple versions.)*

## 3. Old Testament Foundation
*(How the topic appears and develops in the Old Testament.)*

## 4. New Testament Development
*(How the New Testament builds on or fulfills OT teaching.)*

## 5. Key Word Analysis
*(Greek and Hebrew terms related to the topic.)*

## 6. Theological Themes
*(Systematic and biblical theology connections.)*

## 7. Biblical Promises
*(God's promises related to the topic.)*

## 8. Contemporary Perspective
*(How biblical teaching on this topic speaks today.)*

## 9. Practical Application
*(Actionable steps for applying this teaching.)*

## 10. Conclusion
*(Synthesis of findings.)*

## 11. Appendix: Individual Step Outputs
*(Links to each step file for detailed reference.)*
""",
    "sermon": """# BibleMate Study: {title}

## Table of Contents
1. [Sermon Overview](#1-sermon-overview)
2. [Scripture Text](#2-scripture-text)
3. [Exegetical Foundation](#3-exegetical-foundation)
4. [Key Word Study](#4-key-word-study)
5. [Commentary Insights](#5-commentary-insights)
6. [Sermon Outline](#6-sermon-outline)
7. [Full Sermon Content](#7-full-sermon-content)
8. [Application Points](#8-application-points)
9. [Discussion Questions](#9-discussion-questions)
10. [Closing Prayer](#10-closing-prayer)
11. [Appendix: Individual Step Outputs](#11-appendix-individual-step-outputs)

---

## 1. Sermon Overview
*(Big Idea, target audience, and sermon objectives.)*

## 2. Scripture Text
*(The preaching passage in multiple translations.)*

## 3. Exegetical Foundation
*(Historical context, original language insights, and structural analysis.)*

## 4. Key Word Study
*(Key terms in the preaching passage.)*

## 5. Commentary Insights
*(Notable observations from published commentators.)*

## 6. Sermon Outline
*(The structured sermon outline with main points and sub-points.)*

## 7. Full Sermon Content
*(Complete sermon content with illustrations and transitions.)*

## 8. Application Points
*(Specific, grace-centered applications.)*

## 9. Discussion Questions
*(Follow-up questions for small groups or personal reflection.)*

## 10. Closing Prayer
*(A pastoral prayer in the first person.)*

## 11. Appendix: Individual Step Outputs
*(Links to each step file for detailed reference.)*
""",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_workspace_root():
    # This script is at: <root>/.claude/skills/biblemate/biblemate_orchestrator.py
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def _load_if_file(val):
    """If val is a path to an existing file, read and return its contents. Otherwise, return val."""
    if val and isinstance(val, str) and os.path.isfile(val):
        try:
            with open(val, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Failed to read from file '{val}': {e}. Using raw value instead.", file=sys.stderr)
    return val


def _clean_name(name, separator="_"):
    cleaned = re.sub(rf"[^a-zA-Z0-9{re.escape(separator)}]", separator, name).lower()
    cleaned = re.sub(rf"{re.escape(separator)}+", separator, cleaned).strip(separator)
    return cleaned


def _parse_plan_skills(plan_text):
    """Extract skill names mentioned in a study plan."""
    # Match skill names that appear as backtick-wrapped or after common patterns
    skills = set()
    # Backtick-wrapped skill names
    for m in re.finditer(r"`(\w[\w-]*)`", plan_text):
        skills.add(m.group(1).lower())
    # Also match patterns like "Step N: skill_name" or "- skill_name —"
    for m in re.finditer(r"(?:Step\s+\d+[:\.]?\s*|[-*]\s+)(\w[\w-]*)\s*(?:—|–|-|\()", plan_text):
        skills.add(m.group(1).lower())
    return skills


# ---------------------------------------------------------------------------
# Core Functions
# ---------------------------------------------------------------------------

def discover_skills():
    workspace_root = get_workspace_root()
    skills_dir = os.path.join(workspace_root, ".claude", "skills")
    if not os.path.exists(skills_dir):
        print(f"Error: Skills directory not found at {skills_dir}", file=sys.stderr)
        return []
    
    skills = []
    for name in sorted(os.listdir(skills_dir)):
        sub = os.path.join(skills_dir, name)
        if os.path.isdir(sub):
            skill_md_path = os.path.join(sub, "SKILL.md")
            if os.path.exists(skill_md_path):
                try:
                    with open(skill_md_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Extract YAML frontmatter
                    m = re.search(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL | re.MULTILINE)
                    desc = ""
                    skill_name = name
                    if m:
                        yaml_text = m.group(1)
                        for line in yaml_text.split("\n"):
                            if ":" in line:
                                k, v = line.split(":", 1)
                                k = k.strip().lower()
                                v = v.strip()
                                if k == "name":
                                    skill_name = v
                                elif k == "description":
                                    desc = v
                    skills.append({
                        "name": skill_name,
                        "description": desc,
                        "path": skill_md_path
                    })
                except Exception as e:
                    print(f"Warning: Failed to parse {skill_md_path}: {e}", file=sys.stderr)
    return skills


def init_study(request, title):
    request = _load_if_file(request)
    workspace_root = get_workspace_root()
    biblemate_dir = os.path.join(workspace_root, "biblemate")
    os.makedirs(biblemate_dir, exist_ok=True)
    
    clean_title = _clean_name(title)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    folder_name = f"{timestamp}_{clean_title}"
    study_dir = os.path.join(biblemate_dir, folder_name)
    os.makedirs(study_dir, exist_ok=True)
    
    plan_filepath = os.path.join(study_dir, "000-request_and_study_plan.md")
    
    plan_template = f"""# BibleMate Study: {title}

## Original User Request
{request}

## Refined User Request
*(To be populated by the AI assistant after prompt engineering refinement)*

## Study Type
*(passage | book | topical | sermon — to be classified by the AI assistant)*

## Master Study Plan

### Phase 1: Data Retrieval
*(Plan data retrieval steps here — these can run in parallel)*

### Phase 2: Analysis & Exegesis
*(Plan analytical steps here — may depend on Phase 1 outputs)*

### Phase 3: Theological Synthesis
*(Plan theological synthesis steps here)*

### Phase 4: Application & Devotion
*(Plan application/devotion steps here)*

### Phase 5: Final Report & Sync
*(Compile final report, run quality check, sync to git)*

## Quality Audit Log
*(Record quality observations after each phase)*
"""
    with open(plan_filepath, "w", encoding="utf-8") as f:
        f.write(plan_template)
    
    # Create study_metadata.json
    metadata = {
        "title": title,
        "created": datetime.datetime.now().isoformat(),
        "completed": None,
        "study_type": None,
        "original_request": request,
        "skills_used": [],
        "skills_skipped": [],
        "total_steps": 0,
        "total_output_bytes": 0,
        "quality_score": None,
    }
    metadata_path = os.path.join(study_dir, "study_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"SUCCESS_INIT:{study_dir}:{plan_filepath}")


def update_plan(folder_path, plan_content):
    plan_content = _load_if_file(plan_content)
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    plan_filepath = os.path.join(folder_path, "000-request_and_study_plan.md")
    with open(plan_filepath, "w", encoding="utf-8") as f:
        f.write(plan_content)
    print(f"SUCCESS_UPDATE_PLAN:{plan_filepath}")


def save_step(folder_path, step_number, skill_name, content, sub_skill=None):
    content = _load_if_file(content)
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    step_num = str(step_number).zfill(3)
    skill_clean = _clean_name(skill_name, separator="-")
    
    if sub_skill:
        sub_clean = _clean_name(sub_skill, separator="-")
        filename = f"{step_num}-{skill_clean}-{sub_clean}.md"
    else:
        filename = f"{step_num}-{skill_clean}.md"
        
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Depth warning
    content_len = len(content)
    min_len = MIN_CONTENT_LENGTH.get(skill_name.lower(), MIN_CONTENT_LENGTH["default"])
    if content_len < min_len:
        print(f"WARNING: Step output for '{skill_name}' is only {content_len} characters "
              f"(minimum recommended: {min_len}). Consider enriching this step.", file=sys.stderr)
    
    # Update metadata
    _update_metadata_step(folder_path, skill_name, content_len)
    
    print(f"SUCCESS_SAVE_STEP:{filepath}")


def _update_metadata_step(folder_path, skill_name, content_len):
    """Update study_metadata.json after a step is saved."""
    metadata_path = os.path.join(folder_path, "study_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            if skill_name not in metadata.get("skills_used", []):
                metadata.setdefault("skills_used", []).append(skill_name)
            metadata["total_steps"] = metadata.get("total_steps", 0) + 1
            metadata["total_output_bytes"] = metadata.get("total_output_bytes", 0) + content_len
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            pass  # Non-critical


def save_overview(folder_path, step_number, content):
    """Save the pre-final overview file (Phase 5 output)."""
    content = _load_if_file(content)
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)

    step_str = str(step_number).zfill(3)
    filename = f"{step_str}-pre_final_overview.md"
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    _update_metadata_step(folder_path, "pre_final_overview", len(content))
    print(f"SUCCESS_SAVE_OVERVIEW:{filepath}")


def save_final_response(folder_path, step_number, content):
    """Save the final response file (Phase 6 output) and mark study as complete."""
    content = _load_if_file(content)
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)

    step_str = str(step_number).zfill(3)
    filename = f"{step_str}-final_response.md"
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # Mark completion in metadata
    metadata_path = os.path.join(folder_path, "study_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["completed"] = datetime.datetime.now().isoformat()
            metadata["total_output_bytes"] = metadata.get("total_output_bytes", 0) + len(content)
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            pass

    print(f"SUCCESS_SAVE_FINAL_RESPONSE:{filepath}")


def save_report(folder_path, last_step_number, content):
    """DEPRECATED: Use save_overview + save_final_response instead."""
    content = _load_if_file(content)
    print("DEPRECATION WARNING: --save-report is deprecated. "
          "Use --save-overview and --save-final-response instead.", file=sys.stderr)
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    last_step_str = str(last_step_number).zfill(3)
    filename = f"{last_step_str}-final_report.md"
    filepath = os.path.join(folder_path, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    # Mark completion in metadata
    metadata_path = os.path.join(folder_path, "study_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            metadata["completed"] = datetime.datetime.now().isoformat()
            metadata["total_output_bytes"] = metadata.get("total_output_bytes", 0) + len(content)
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            pass
    
    print(f"SUCCESS_SAVE_REPORT:{filepath}")


def list_studies():
    """List all existing studies in the biblemate/ directory with completion status."""
    workspace_root = get_workspace_root()
    biblemate_dir = os.path.join(workspace_root, "biblemate")
    
    if not os.path.exists(biblemate_dir):
        print("No studies found. The biblemate/ directory does not exist.")
        return
    
    studies = []
    for name in sorted(os.listdir(biblemate_dir)):
        study_path = os.path.join(biblemate_dir, name)
        if os.path.isdir(study_path) and not name.startswith("."):
            # Check for final response (new) or final report (legacy)
            study_files = os.listdir(study_path)
            has_report = (any(f.endswith("-final_response.md") for f in study_files)
                          or any(f.endswith("-final_report.md") for f in study_files))
            # Count step files
            step_files = [f for f in os.listdir(study_path) if re.match(r"\d{3}-", f) and f != "000-request_and_study_plan.md"]
            # Total size
            total_size = sum(
                os.path.getsize(os.path.join(study_path, f))
                for f in os.listdir(study_path) if os.path.isfile(os.path.join(study_path, f))
            )
            # Check metadata
            meta_path = os.path.join(study_path, "study_metadata.json")
            study_type = "unknown"
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r") as f:
                        meta = json.load(f)
                    study_type = meta.get("study_type") or "unknown"
                except Exception:
                    pass
            
            status = "✅ Complete" if has_report else "🔄 In Progress"
            studies.append({
                "name": name,
                "status": status,
                "steps": len(step_files),
                "size_kb": round(total_size / 1024, 1),
                "type": study_type,
            })
    
    if not studies:
        print("No studies found in the biblemate/ directory.")
        return
    
    print("# BibleMate Studies\n")
    print(f"| Study | Status | Steps | Size | Type |")
    print(f"|-------|--------|-------|------|------|")
    for s in studies:
        print(f"| {s['name']} | {s['status']} | {s['steps']} | {s['size_kb']} KB | {s['type']} |")


def study_status(folder_path):
    """Report detailed progress on a specific study."""
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    files = sorted(os.listdir(folder_path))
    step_files = [f for f in files if re.match(r"\d{3}-", f) and f.endswith(".md") and f != "000-request_and_study_plan.md"]
    has_plan = "000-request_and_study_plan.md" in files
    has_overview = any(f.endswith("-pre_final_overview.md") for f in files)
    has_final_response = any(f.endswith("-final_response.md") for f in files)
    has_report = any(f.endswith("-final_report.md") for f in files)  # legacy
    is_complete = has_final_response or has_report
    has_metadata = "study_metadata.json" in files
    
    print("# Study Progress Report\n")
    print(f"**Folder**: `{folder_path}`")
    print(f"**Plan File**: {'✅ Found' if has_plan else '❌ Missing'}")
    print(f"**Pre-Final Overview**: {'✅ Found' if has_overview else '⬜ Pending'}")
    print(f"**Final Response**: {'✅ Complete' if has_final_response else ('📄 Legacy Report' if has_report else '🔄 Pending')}")
    print(f"**Metadata**: {'✅ Found' if has_metadata else '⚠️ Missing'}")
    print(f"**Step Files**: {len(step_files)}\n")
    
    if step_files:
        print("| File | Size | Depth Check |")
        print("|------|------|-------------|")
        for f in step_files:
            fpath = os.path.join(folder_path, f)
            size = os.path.getsize(fpath)
            # Extract skill name from filename
            match = re.match(r"\d{3}-(.+?)(?:-|\.md$)", f)
            skill_name = match.group(1) if match else "unknown"
            min_len = MIN_CONTENT_LENGTH.get(skill_name, MIN_CONTENT_LENGTH["default"])
            depth = "✅ OK" if size >= min_len else f"⚠️ Thin ({size} < {min_len} chars)"
            print(f"| {f} | {size} bytes | {depth} |")
    
    # Read plan to find incomplete steps
    if has_plan:
        plan_path = os.path.join(folder_path, "000-request_and_study_plan.md")
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_text = f.read()
        
        incomplete = re.findall(r"- \[ \]\s+(.*)", plan_text)
        in_progress = re.findall(r"- \[/\]\s+(.*)", plan_text)
        completed = re.findall(r"- \[x\]\s+(.*)", plan_text)
        
        total = len(incomplete) + len(in_progress) + len(completed)
        if total > 0:
            pct = round((len(completed) / total) * 100)
            print(f"\n**Progress**: {pct}% ({len(completed)}/{total} steps complete)")
        
        if in_progress:
            print(f"\n**In Progress** ({len(in_progress)}):")
            for item in in_progress:
                print(f"  - 🔄 {item}")
        
        if incomplete:
            print(f"\n**Pending** ({len(incomplete)}):")
            for item in incomplete:
                print(f"  - ⬜ {item}")


def validate_plan(folder_path, study_type):
    """Validate that a study plan covers minimum required skills."""
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    study_type = study_type.lower().strip()
    if study_type not in MINIMUM_COVERAGE:
        print(f"Error: Unknown study type '{study_type}'. "
              f"Valid types: {', '.join(MINIMUM_COVERAGE.keys())}", file=sys.stderr)
        sys.exit(1)
    
    plan_path = os.path.join(folder_path, "000-request_and_study_plan.md")
    if not os.path.exists(plan_path):
        print(f"Error: Plan file not found at {plan_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
    
    mentioned_skills = _parse_plan_skills(plan_text)
    coverage = MINIMUM_COVERAGE[study_type]
    
    required_missing = [s for s in coverage["required"] if s not in mentioned_skills]
    recommended_missing = [s for s in coverage["recommended"] if s not in mentioned_skills]
    required_present = [s for s in coverage["required"] if s in mentioned_skills]
    recommended_present = [s for s in coverage["recommended"] if s in mentioned_skills]
    
    print(f"# Plan Validation Report ({study_type.title()} Study)\n")
    
    req_total = len(coverage["required"])
    req_found = len(required_present)
    print(f"**Required Skills**: {req_found}/{req_total} covered")
    
    if required_missing:
        print(f"\n⚠️ **Missing Required Skills** ({len(required_missing)}):")
        for s in required_missing:
            print(f"  - ❌ `{s}`")
    else:
        print("\n✅ All required skills are covered!")
    
    if recommended_missing:
        print(f"\n💡 **Missing Recommended Skills** ({len(recommended_missing)}):")
        for s in recommended_missing:
            print(f"  - 💭 `{s}`")
    
    if required_present:
        print(f"\n✅ **Present Required Skills**: {', '.join(f'`{s}`' for s in required_present)}")
    if recommended_present:
        print(f"✅ **Present Recommended Skills**: {', '.join(f'`{s}`' for s in recommended_present)}")
    
    # Return exit code based on required coverage
    if required_missing:
        print(f"\n**RESULT**: INCOMPLETE — {len(required_missing)} required skill(s) missing from plan.")
        sys.exit(2)
    else:
        print(f"\n**RESULT**: PASS — All required skills are accounted for.")


def quality_score(folder_path):
    """Compute quality metrics for a completed or in-progress study."""
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    files = sorted(os.listdir(folder_path))
    step_files = [f for f in files if re.match(r"\d{3}-", f) and f.endswith(".md") and f != "000-request_and_study_plan.md"]
    
    total_bytes = 0
    skills_used = set()
    depth_warnings = 0
    scripture_citations = 0
    
    for f in step_files:
        fpath = os.path.join(folder_path, f)
        size = os.path.getsize(fpath)
        total_bytes += size
        
        match = re.match(r"\d{3}-(.+?)(?:-|\.md$)", f)
        if match:
            skill_name = match.group(1)
            skills_used.add(skill_name)
            min_len = MIN_CONTENT_LENGTH.get(skill_name, MIN_CONTENT_LENGTH["default"])
            if size < min_len:
                depth_warnings += 1
        
        # Count Scripture citations in the file
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                text = fh.read()
            # Match patterns like "John 3:16", "Genesis 1:1-3", "1 Cor. 13:4"
            refs = re.findall(
                r"\b(?:\d\s+)?(?:Gen|Exod|Lev|Num|Deut|Josh|Judg|Ruth|"
                r"Sam|Kgs|Chr|Ezra|Neh|Esth|Job|Ps|Prov|Eccl|Song|"
                r"Isa|Jer|Lam|Ezek|Dan|Hos|Joel|Amos|Obad|Jonah|Mic|"
                r"Nah|Hab|Zeph|Hag|Zech|Mal|Matt|Mark|Luke|John|Acts|"
                r"Rom|Cor|Gal|Eph|Phil|Col|Thess|Tim|Titus|Phlm|Heb|"
                r"Jas|Pet|Jude|Rev|Genesis|Exodus|Leviticus|Numbers|"
                r"Deuteronomy|Joshua|Judges|Samuel|Kings|Chronicles|"
                r"Nehemiah|Esther|Psalms?|Proverbs|Ecclesiastes|"
                r"Isaiah|Jeremiah|Lamentations|Ezekiel|Daniel|Hosea|"
                r"Amos|Obadiah|Micah|Nahum|Habakkuk|Zephaniah|Haggai|"
                r"Zechariah|Malachi|Matthew|Romans|Corinthians|"
                r"Galatians|Ephesians|Philippians|Colossians|"
                r"Thessalonians|Timothy|Philemon|Hebrews|James|Peter|"
                r"Revelation)[.\s]+\d+:\d+",
                text, re.IGNORECASE
            )
            scripture_citations += len(refs)
        except Exception:
            pass
    
    has_final_response = any(f.endswith("-final_response.md") for f in files)
    has_overview = any(f.endswith("-pre_final_overview.md") for f in files)
    has_report = any(f.endswith("-final_report.md") for f in files)  # legacy
    is_complete = has_final_response or has_report
    
    # Compute score (0-100)
    score = 0
    # Skills breadth (0-25 points)
    score += min(25, len(skills_used) * 3)
    # Content depth (0-20 points, based on total output)
    if total_bytes > 20000:
        score += 20
    elif total_bytes > 10000:
        score += 16
    elif total_bytes > 5000:
        score += 12
    elif total_bytes > 2000:
        score += 8
    else:
        score += 4
    # Scripture citations (0-15 points)
    score += min(15, scripture_citations * 2)
    # Depth quality (0-10 points, penalize for thin outputs)
    if len(step_files) > 0:
        thin_ratio = depth_warnings / len(step_files)
        score += round(10 * (1 - thin_ratio))
    # Pre-final overview (0-5 points)
    if has_overview:
        overview_file = [f for f in files if f.endswith("-pre_final_overview.md")][0]
        overview_size = os.path.getsize(os.path.join(folder_path, overview_file))
        if overview_size > 3000:
            score += 5
        elif overview_size > 1000:
            score += 3
        else:
            score += 1
    # Final response (0-25 points — the most important deliverable)
    if has_final_response:
        response_file = [f for f in files if f.endswith("-final_response.md")][0]
        response_size = os.path.getsize(os.path.join(folder_path, response_file))
        if response_size > 15000:
            score += 25
        elif response_size > 10000:
            score += 20
        elif response_size > 5000:
            score += 15
        elif response_size > 2000:
            score += 10
        else:
            score += 5
    elif has_report:  # legacy fallback
        report_file = [f for f in files if f.endswith("-final_report.md")][0]
        report_size = os.path.getsize(os.path.join(folder_path, report_file))
        if report_size > 5000:
            score += 10
        elif report_size > 2000:
            score += 7
        elif report_size > 500:
            score += 4
        else:
            score += 2
    
    # Clamp
    score = min(100, max(0, score))
    
    # Grade
    if score >= 90:
        grade = "A — Excellent"
    elif score >= 75:
        grade = "B — Good"
    elif score >= 60:
        grade = "C — Adequate"
    elif score >= 40:
        grade = "D — Needs Improvement"
    else:
        grade = "F — Insufficient"
    
    print(f"# Quality Score Report\n")
    print(f"**Score**: {score}/100 ({grade})\n")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Skills Used | {len(skills_used)} ({', '.join(sorted(skills_used))}) |")
    print(f"| Total Output | {round(total_bytes / 1024, 1)} KB |")
    print(f"| Step Files | {len(step_files)} |")
    print(f"| Scripture Citations | {scripture_citations} |")
    print(f"| Depth Warnings | {depth_warnings} |")
    print(f"| Pre-Final Overview | {'✅ Present' if has_overview else '❌ Missing'} |")
    print(f"| Final Response | {'✅ Present' if has_final_response else ('📄 Legacy Report' if has_report else '❌ Missing')} |")
    
    # Save score to metadata
    metadata_path = os.path.join(folder_path, "study_metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
            metadata["quality_score"] = score
            metadata["skills_used"] = sorted(skills_used)
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)
        except Exception:
            pass


def generate_report_template(study_type, title="[Study Title]"):
    """Output a comprehensive final report markdown template."""
    study_type = study_type.lower().strip()
    if study_type not in FINAL_REPORT_TEMPLATES:
        print(f"Error: Unknown study type '{study_type}'. "
              f"Valid types: {', '.join(FINAL_REPORT_TEMPLATES.keys())}", file=sys.stderr)
        sys.exit(1)
    
    template = FINAL_REPORT_TEMPLATES[study_type].format(title=title)
    print(template)


def resume_study(folder_path):
    """Identify uncompleted steps from an existing study plan."""
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    plan_path = os.path.join(folder_path, "000-request_and_study_plan.md")
    if not os.path.exists(plan_path):
        print(f"Error: Plan file not found at {plan_path}", file=sys.stderr)
        sys.exit(1)
    
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
    
    # Find completed and incomplete tasks
    incomplete = re.findall(r"- \[ \]\s+(.*)", plan_text)
    in_progress = re.findall(r"- \[/\]\s+(.*)", plan_text)
    completed = re.findall(r"- \[x\]\s+(.*)", plan_text)
    
    # Find existing step files
    files = sorted(os.listdir(folder_path))
    step_files = [f for f in files if re.match(r"\d{3}-", f) and f.endswith(".md") and f != "000-request_and_study_plan.md"]
    
    # Find the highest step number
    max_step = 0
    for f in step_files:
        match = re.match(r"(\d{3})-", f)
        if match:
            step_num = int(match.group(1))
            max_step = max(max_step, step_num)
    
    has_final_response = any(f.endswith("-final_response.md") for f in files)
    has_report = any(f.endswith("-final_report.md") for f in files)  # legacy
    is_complete = has_final_response or has_report
    
    print(f"# Resume Study Report\n")
    print(f"**Folder**: `{folder_path}`")
    print(f"**Completed Steps**: {len(completed)}")
    print(f"**In Progress**: {len(in_progress)}")
    print(f"**Pending**: {len(incomplete)}")
    print(f"**Last Step Number**: {max_step}")
    print(f"**Final Response**: {'✅ Done' if has_final_response else ('📄 Legacy Report' if has_report else '⬜ Not yet')}\n")
    
    if in_progress:
        print("## Resume From (In Progress):")
        for item in in_progress:
            print(f"  - 🔄 {item}")
    
    if incomplete:
        print("\n## Remaining Steps:")
        for item in incomplete:
            print(f"  - ⬜ {item}")
    
    if not incomplete and not in_progress:
        if is_complete:
            print("✅ Study appears to be fully complete!")
        else:
            print("⚠️ All plan steps are complete but no final response found. Run Phase 5 (overview) and Phase 6 (final response).")
    
    print(f"\n**Next step number to use**: {max_step + 1}")


def export_study(folder_path):
    """Combine all step files and the final report into a single markdown document."""
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
    
    files = sorted(os.listdir(folder_path))
    md_files = [f for f in files if f.endswith(".md")]
    
    combined = []
    for f in md_files:
        fpath = os.path.join(folder_path, f)
        with open(fpath, "r", encoding="utf-8") as fh:
            content = fh.read()
        combined.append(f"<!-- Source: {f} -->\n\n{content}")
    
    output = "\n\n---\n\n".join(combined)
    
    # Save the export
    study_name = os.path.basename(folder_path)
    export_dir = os.path.join(get_workspace_root(), "biblemate", "exports")
    os.makedirs(export_dir, exist_ok=True)
    export_path = os.path.join(export_dir, f"{study_name}_complete.md")
    
    with open(export_path, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"SUCCESS_EXPORT:{export_path}")
    print(f"Exported {len(md_files)} files ({round(len(output) / 1024, 1)} KB) to {export_path}")


def git_sync():
    workspace_root = get_workspace_root()
    git_dir = os.path.join(workspace_root, ".git")
    if not os.path.exists(git_dir):
        print("Note: Not a git repository. Skipping sync.")
        return
        
    try:
        # Check if remote origin is set
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], 
                             cwd=workspace_root, capture_output=True, text=True)
        if not res.stdout.strip():
            print("Note: No git remote origin configured. Skipping sync.")
            return
            
        print("Staging changes...")
        subprocess.run(["git", "add", "."], cwd=workspace_root, check=True)
        
        print("Committing changes...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "commit", "-m", f"Sync BibleMate study results ({timestamp})"], 
                       cwd=workspace_root, check=True)
        
        print("Pushing to remote...")
        subprocess.run(["git", "push"], cwd=workspace_root, check=True)
        print("SUCCESS_GIT_SYNC")
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}", file=sys.stderr)
    except Exception as e:
        print(f"Error during git sync: {e}", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Orchestrator script for the BibleMate AI workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-skills
  %(prog)s --list-studies
  %(prog)s --init "Study John 3:16 deeply" "John 3:16 Study"
  %(prog)s --status "/path/to/study/folder"
  %(prog)s --validate-plan "/path/to/study/folder" "passage"
  %(prog)s --quality-score "/path/to/study/folder"
  %(prog)s --resume "/path/to/study/folder"
  %(prog)s --generate-report-template "passage"
  %(prog)s --export "/path/to/study/folder"
  %(prog)s --git-sync
        """,
    )
    
    parser.add_argument("--list-skills", action="store_true",
                        help="List all dynamically discovered skills in the workspace.")
    parser.add_argument("--list-studies", action="store_true",
                        help="List all existing studies with completion status.")
    parser.add_argument("--init", nargs=2, metavar=("REQUEST", "TITLE"),
                        help="Initialize a new study folder and 000-request_and_study_plan.md file.")
    parser.add_argument("--update-plan", nargs=2, metavar=("FOLDER_PATH", "PLAN_CONTENT"),
                        help="Update the 000-request_and_study_plan.md file in the given study folder.")
    parser.add_argument("--save-step", nargs=4, metavar=("FOLDER_PATH", "STEP_NUM", "SKILL_NAME", "CONTENT"),
                        help="Save intermediate step output to folder.")
    parser.add_argument("--sub-skill",
                        help="Optional sub-skill name for the step file.")
    parser.add_argument("--save-overview", nargs=3, metavar=("FOLDER_PATH", "STEP_NUM", "CONTENT"),
                        help="Save the pre-final overview file (Phase 5 output).")
    parser.add_argument("--save-final-response", nargs=3, metavar=("FOLDER_PATH", "STEP_NUM", "CONTENT"),
                        help="Save the final response file (Phase 6 output) and mark study complete.")
    parser.add_argument("--save-report", nargs=3, metavar=("FOLDER_PATH", "LAST_STEP_NUM", "CONTENT"),
                        help="[DEPRECATED] Use --save-overview + --save-final-response instead.")
    parser.add_argument("--status", metavar="FOLDER_PATH",
                        help="Check study progress and report detailed status.")
    parser.add_argument("--validate-plan", nargs=2, metavar=("FOLDER_PATH", "STUDY_TYPE"),
                        help="Validate plan coverage against minimum skill requirements.")
    parser.add_argument("--quality-score", metavar="FOLDER_PATH",
                        help="Compute quality metrics for a study.")
    parser.add_argument("--generate-report-template", nargs="+", metavar="ARGS",
                        help="Generate a report template. Args: STUDY_TYPE [TITLE]")
    parser.add_argument("--resume", metavar="FOLDER_PATH",
                        help="Resume an incomplete study by identifying pending steps.")
    parser.add_argument("--export", metavar="FOLDER_PATH",
                        help="Export/combine all step files into a single markdown document.")
    parser.add_argument("--git-sync", action="store_true",
                        help="Run git sync to stage, commit, and push all modifications.")
    
    args = parser.parse_args()
    
    if args.list_skills:
        skills = discover_skills()
        print("# Discovered Study Skills\n")
        for s in skills:
            print(f"- **{s['name']}**: {s['description']}")
    elif args.list_studies:
        list_studies()
    elif args.init:
        init_study(args.init[0], args.init[1])
    elif args.update_plan:
        update_plan(args.update_plan[0], args.update_plan[1])
    elif args.save_step:
        save_step(args.save_step[0], args.save_step[1], args.save_step[2], args.save_step[3], args.sub_skill)
    elif args.save_overview:
        save_overview(args.save_overview[0], args.save_overview[1], args.save_overview[2])
    elif args.save_final_response:
        save_final_response(args.save_final_response[0], args.save_final_response[1], args.save_final_response[2])
    elif args.save_report:
        save_report(args.save_report[0], args.save_report[1], args.save_report[2])
    elif args.status:
        study_status(args.status)
    elif args.validate_plan:
        validate_plan(args.validate_plan[0], args.validate_plan[1])
    elif args.quality_score:
        quality_score(args.quality_score)
    elif args.generate_report_template:
        template_args = args.generate_report_template
        study_type = template_args[0]
        title = template_args[1] if len(template_args) > 1 else "[Study Title]"
        generate_report_template(study_type, title)
    elif args.resume:
        resume_study(args.resume)
    elif args.export:
        export_study(args.export)
    elif args.git_sync:
        git_sync()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
