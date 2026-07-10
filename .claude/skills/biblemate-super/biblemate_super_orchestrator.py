#!/usr/bin/env python3
"""
BibleMate-Super AI Orchestrator Script

Manages file operations, study lifecycle, dynamic validation, quality metrics,
and git synchronization for BibleMate-Super studies.
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_workspace_root():
    # This script is at: <root>/.claude/skills/biblemate-super/biblemate_super_orchestrator.py
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
    # Prefix folder with super_ to denote a BibleMate-Super study
    folder_name = f"{timestamp}_super_{clean_title}"
    study_dir = os.path.join(biblemate_dir, folder_name)
    os.makedirs(study_dir, exist_ok=True)
    
    plan_filepath = os.path.join(study_dir, "000-request_and_study_plan.md")
    
    plan_template = f"""# BibleMate-Super Study: {title}

## Original User Request
{request}

## Refined User Request
*(To be populated after detailed assessment and refinement by the Study Plan & Phase Quality Auditor)*

## Dynamic Master Study Plan
*(The AI assistant will outline a custom plan with dynamic phases, goals, steps, personas, and tools here)*

## Quality Audit & Adjustments Log
*(Record quality audits and adjustments at the end of each phase)*
"""
    with open(plan_filepath, "w", encoding="utf-8") as f:
        f.write(plan_template)
    
    # Create study_metadata.json
    metadata = {
        "title": title,
        "created": datetime.datetime.now().isoformat(),
        "completed": None,
        "study_type": "super",
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
    """Save the pre-final overview file."""
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
    """Save the final response file and mark study as complete."""
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
            # Check for final response or final report
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
            match = re.match(r"\d{3}-(.+?)(?:-|\.md$)", f)
            skill_name = match.group(1) if match else "unknown"
            min_len = MIN_CONTENT_LENGTH.get(skill_name, MIN_CONTENT_LENGTH["default"])
            depth = "✅ OK" if size >= min_len else f"⚠️ Thin ({size} < {min_len} chars)"
            print(f"| {f} | {size} bytes | {depth} |")
    
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


def validate_plan(folder_path, study_type=None):
    """Validate that a study plan covers essential elements and has a structured checklist."""
    if not os.path.exists(folder_path):
        print(f"Error: Study folder does not exist at {folder_path}", file=sys.stderr)
        sys.exit(1)
        
    plan_path = os.path.join(folder_path, "000-request_and_study_plan.md")
    if not os.path.exists(plan_path):
        print(f"Error: Plan file not found at {plan_path}", file=sys.stderr)
        sys.exit(1)
        
    with open(plan_path, "r", encoding="utf-8") as f:
        plan_text = f.read()
        
    mentioned_skills = _parse_plan_skills(plan_text)
    
    # If a standard study type is specified, we can fall back to standard validation
    if study_type and study_type.lower() in MINIMUM_COVERAGE:
        study_type = study_type.lower().strip()
        coverage = MINIMUM_COVERAGE[study_type]
        required_missing = [s for s in coverage["required"] if s not in mentioned_skills]
        recommended_missing = [s for s in coverage["recommended"] if s not in mentioned_skills]
        required_present = [s for s in coverage["required"] if s in mentioned_skills]
        recommended_present = [s for s in coverage["recommended"] if s in mentioned_skills]
        
        print(f"# Plan Validation Report ({study_type.title()} Study fallback)\n")
        print(f"**Required Skills**: {len(required_present)}/{len(coverage['required'])} covered")
        
        if required_missing:
            print(f"\n⚠️ **Missing Required Skills** ({len(required_missing)}):")
            for s in required_missing:
                print(f"  - ❌ `{s}`")
        else:
            print("\n✅ All required skills are covered!")
            
        if required_missing:
            print(f"\n**RESULT**: INCOMPLETE — {len(required_missing)} required skill(s) missing from plan.")
            sys.exit(2)
        else:
            print(f"\n**RESULT**: PASS — All required skills are accounted for.")
            sys.exit(0)

    # Otherwise, perform flexible, dynamic validation for super study plans
    discovered_skills = {s["name"].lower() for s in discover_skills()}
    
    print(f"# Plan Validation Report (Dynamic BibleMate-Super Plan)\n")
    
    # Check if plan contains any steps/checkboxes
    incomplete = re.findall(r"- \[ \]\s+(.*)", plan_text)
    in_progress = re.findall(r"- \[/\]\s+(.*)", plan_text)
    completed = re.findall(r"- \[x\]\s+(.*)", plan_text)
    total_steps = len(incomplete) + len(in_progress) + len(completed)
    
    print(f"**Total Planned Steps**: {total_steps}")
    if total_steps == 0:
        print("\n❌ **Validation Failed**: No checkbox steps (e.g. `- [ ] step description`) found in study plan.")
        sys.exit(2)
        
    # Check for unrecognized skills
    invalid_skills = []
    for skill in sorted(mentioned_skills):
        if skill not in discovered_skills and skill not in ["biblemate", "biblemate-super", "pre_final_overview", "final_response", "final_report", "overview"]:
            invalid_skills.append(skill)
            
    if invalid_skills:
        print(f"\n⚠️ **Unrecognized Skills/Keywords** ({len(invalid_skills)}):")
        for s in invalid_skills:
            print(f"  - `{s}` (Ensure this matches a valid skill or command prefix)")
            
    # Essential Study Component Checks
    essential_checks = {
        "Scripture Retrieval": {
            "skills": ["bible"],
            "passed": False,
            "desc": "Needs at least one scripture retrieval step using `bible` to avoid hallucinations."
        },
        "Textual & Original Language Analysis": {
            "skills": ["original", "interlinear", "keywords", "lexicon", "morphology", "commentary", "xrefs", "search", "chronology", "names", "locations"],
            "passed": False,
            "desc": "Recommended to have analytical steps like word studies, commentary checks, cross-references, original language lookups, chronology, biblical names, or locations analysis."
        },
        "Theological Synthesis": {
            "skills": ["themes", "theology", "meaning", "canon", "insights", "topics"],
            "passed": False,
            "desc": "Recommended to have synthesis steps evaluating doctrinal themes, theological messages, or exegetical insights."
        },
        "Application & Devotion": {
            "skills": ["application", "devotion", "prayer", "questions", "sermon"],
            "passed": False,
            "desc": "Recommended to have a devotional, practical application, scriptural prayer, or sermon writing step."
        }
    }
    
    for cat, info in essential_checks.items():
        for s in info["skills"]:
            if s in mentioned_skills:
                info["passed"] = True
                break
                
    print("\n## Essential Component Coverage Checklist:")
    critical_passed = True
    for cat, info in essential_checks.items():
        status_char = "✅" if info["passed"] else "⚠️"
        if not info["passed"] and cat == "Scripture Retrieval":
            status_char = "❌"
            critical_passed = False
        print(f"- {status_char} **{cat}**: {'Covered' if info['passed'] else info['desc']}")
        
    if not critical_passed:
        print("\n**RESULT**: INCOMPLETE — Missing critical Scripture retrieval (`bible` skill) in plan.")
        sys.exit(2)
    else:
        print("\n**RESULT**: PASS — Dynamic study plan contains a structured checklist with essential coverage.")
        sys.exit(0)


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
        
        try:
            with open(fpath, "r", encoding="utf-8") as fh:
                text = fh.read()
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
    score += min(25, len(skills_used) * 3.5)
    
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
        
    score += min(15, scripture_citations * 2.5)
    
    if len(step_files) > 0:
        thin_ratio = depth_warnings / len(step_files)
        score += round(10 * (1 - thin_ratio))
        
    if has_overview:
        overview_file = [f for f in files if f.endswith("-pre_final_overview.md")][0]
        overview_size = os.path.getsize(os.path.join(folder_path, overview_file))
        if overview_size > 3000:
            score += 5
        elif overview_size > 1000:
            score += 3
        else:
            score += 1
            
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
    elif has_report:
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
            
    score = min(100, max(0, score))
    
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
    
    incomplete = re.findall(r"- \[ \]\s+(.*)", plan_text)
    in_progress = re.findall(r"- \[/\]\s+(.*)", plan_text)
    completed = re.findall(r"- \[x\]\s+(.*)", plan_text)
    
    files = sorted(os.listdir(folder_path))
    step_files = [f for f in files if re.match(r"\d{3}-", f) and f.endswith(".md") and f != "000-request_and_study_plan.md"]
    
    max_step = 0
    for f in step_files:
        match = re.match(r"(\d{3})-", f)
        if match:
            step_num = int(match.group(1))
            max_step = max(max_step, step_num)
            
    has_final_response = any(f.endswith("-final_response.md") for f in files)
    has_report = any(f.endswith("-final_report.md") for f in files)
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
        res = subprocess.run(["git", "config", "--get", "remote.origin.url"], 
                             cwd=workspace_root, capture_output=True, text=True)
        if not res.stdout.strip():
            print("Note: No git remote origin configured. Skipping sync.")
            return
            
        print("Staging changes...")
        subprocess.run(["git", "add", "."], cwd=workspace_root, check=True)
        
        print("Committing changes...")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subprocess.run(["git", "commit", "-m", f"Sync BibleMate-Super study results ({timestamp})"], 
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
        description="Orchestrator script for the BibleMate-Super AI workflow.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list-skills
  %(prog)s --list-studies
  %(prog)s --init "Study Joshua 3 deeply" "Joshua 3 Study"
  %(prog)s --status "/path/to/study/folder"
  %(prog)s --validate-plan "/path/to/study/folder"
  %(prog)s --quality-score "/path/to/study/folder"
  %(prog)s --resume "/path/to/study/folder"
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
                        help="Save the pre-final overview file (Phase N+1 output).")
    parser.add_argument("--save-final-response", nargs=3, metavar=("FOLDER_PATH", "STEP_NUM", "CONTENT"),
                        help="Save the final response file (Phase N+2 output) and mark study complete.")
    parser.add_argument("--save-report", nargs=3, metavar=("FOLDER_PATH", "LAST_STEP_NUM", "CONTENT"),
                        help="[DEPRECATED] Use --save-overview + --save-final-response instead.")
    parser.add_argument("--status", metavar="FOLDER_PATH",
                        help="Check study progress and report detailed status.")
    parser.add_argument("--validate-plan", nargs="+", metavar="ARGS",
                        help="Validate plan coverage. Args: FOLDER_PATH [STUDY_TYPE]")
    parser.add_argument("--quality-score", metavar="FOLDER_PATH",
                        help="Compute quality metrics for a study.")
    parser.add_argument("--generate-report-template", nargs="+", metavar="ARGS",
                        help="[DEPRECATED/LEGACY] Generate a report template. Args: STUDY_TYPE [TITLE]")
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
        path = args.validate_plan[0]
        stype = args.validate_plan[1] if len(args.validate_plan) > 1 else None
        validate_plan(path, stype)
    elif args.quality_score:
        quality_score(args.quality_score)
    elif args.generate_report_template:
        print("Note: report template generation is legacy in super studies. Final responses are dynamically structured.", file=sys.stderr)
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
