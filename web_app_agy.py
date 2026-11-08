#!/usr/bin/env python3
"""BibleMate web app backed by the signed-in Antigravity CLI (`agy`).

Sibling of web_app_gemini_api_key.py, web_app_claude.py, and web_app_grok.py. The layout and workspace
tools are the same. The agent backend is `agy -p` headless mode, which reuses the
credentials from the user's existing Google subscription sign-in in Antigravity CLI.
No separate Gemini API key is required.
"""
import os
import sys
import re
import json
import asyncio
import shutil
import signal
import sqlite3
import subprocess
from nicegui import ui, app

# Reuse the Antigravity CLI install the user is already signed into.
AGY_BIN = shutil.which("agy") or os.path.expanduser("~/.local/bin/agy")
AGY_DATA_DIRS = (
    os.path.expanduser("~/.gemini/antigravity-cli"),
    os.path.expanduser("~/.gemini/antigravity"),
)
# Antigravity stream-json writes each tool result as one line. A file read can
# exceed asyncio's default 64 KiB StreamReader limit and abort the turn.
AGY_STREAM_LIMIT = 8 * 1024 * 1024
if not AGY_BIN or not os.path.isfile(AGY_BIN) or not os.access(AGY_BIN, os.X_OK):
    print("Error: the agy CLI was not found.")
    print("Install Antigravity CLI, sign in with your Google subscription, then re-run this app.")
    print("Expected the `agy` executable on PATH or at ~/.local/bin/agy.")
    sys.exit(1)

# Ensure working directory is workspace root to auto-discover .agents/
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if WORKSPACE_DIR:
    os.chdir(WORKSPACE_DIR)
else:
    WORKSPACE_DIR = os.getcwd()

# Ensure images directory exists and serve statically
os.makedirs(os.path.join(WORKSPACE_DIR, 'images'), exist_ok=True)
app.add_static_files('/images', os.path.join(WORKSPACE_DIR, 'images'))

# ---------------------------------------------------------
# Dynamic Discovery Helpers
# ---------------------------------------------------------

def parse_personas():
    """Parses .agents/agents.md to extract all available personas and descriptions."""
    path = '.agents/agents.md'
    personas = {'Auto': 'Perform the task by dynamically rotating or choosing the best persona.'}
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Split sections by heading level 2
            sections = re.split(r'\n##\s+', '\n' + content)
            for sec in sections:
                if not sec.strip() or sec.strip().startswith('# AI Team'):
                    continue
                lines = sec.strip().split('\n')
                if not lines:
                    continue
                title = lines[0].strip().split('---')[0].strip()
                desc_lines = []
                for l in lines[1:]:
                    if l.startswith('###') or l.strip() == '---':
                        break
                    desc_lines.append(l)
                personas[title] = '\n'.join(desc_lines).strip()
        except Exception as e:
            print(f"Error parsing agents.md: {e}")
    return personas

def get_skills():
    """Dynamically lists the available exegesis skills from .agents/skills/."""
    skills = ['Auto']
    skills_dir = '.agents/skills'
    if os.path.exists(skills_dir):
        try:
            for d in os.listdir(skills_dir):
                if os.path.isdir(os.path.join(skills_dir, d)):
                    skills.append(d)
        except Exception:
            pass
    return sorted(skills)

# Parse configurations at startup
PERSONAS_MAP = parse_personas()
SKILLS_LIST = get_skills()

# Dropdown labels to `agy --model` values. None means "use whatever model the
# CLI session default is configured with" (no --model flag is passed).
FALLBACK_MODELS_MAP = {
    'Default (session default)': None,
    'Gemini 3.8 Flash (Medium)': 'gemini-3.8-flash-medium',
    'Gemini 3.8 Flash (High)': 'gemini-3.8-flash-high',
    'Gemini 3.8 Flash (Low)': 'gemini-3.8-flash-low',
    'Gemini 4 Argon (Medium)': 'gemini-4-argon-medium',
    'Gemini 4 Argon (High)': 'gemini-4-argon-high',
    'Gemini 4 Argon (Low)': 'gemini-4-argon-low',
    'Claude Opus 5.5 (Medium)': 'claude-opus-5-5-medium',
    'Claude Opus 5.5 (High)': 'claude-opus-5-5-high',
    'Claude Opus 5.5 (Low)': 'claude-opus-5-5-low',
    'Claude Sonnet 5.5 (Medium)': 'claude-sonnet-5-5-medium',
    'Claude Sonnet 5.5 (High)': 'claude-sonnet-5-5-high',
    'Claude Sonnet 5.5 (Low)': 'claude-sonnet-5-5-low',
    'GPT-OSS 120B (Medium)': 'gpt-oss-120b-medium',
}

def discover_agy_models(fallback_map: dict) -> dict:
    """Queries `agy models` to dynamically populate available CLI models, falling back to fallback_map."""
    try:
        res = subprocess.run(
            [AGY_BIN, 'models'],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=WORKSPACE_DIR,
        )
        if res.returncode == 0 and res.stdout:
            discovered = {'Default (session default)': None}
            for raw_line in res.stdout.splitlines():
                clean_line = raw_line.rsplit('\r', 1)[-1].strip()
                if not clean_line or 'Fetching available models' in clean_line:
                    continue
                parts = re.split(r'\t|\s{2,}', clean_line, maxsplit=1)
                if len(parts) == 2:
                    model_id, label = parts[0].strip(), parts[1].strip()
                    if model_id and label:
                        discovered[label] = model_id
            if len(discovered) > 1:
                return discovered
    except Exception:
        pass
    return dict(fallback_map)

MODELS_MAP = discover_agy_models(FALLBACK_MODELS_MAP)
DEFAULT_MODEL = (
    'Gemini 3.8 Flash (Medium)'
    if 'Gemini 3.8 Flash (Medium)' in MODELS_MAP
    else next(iter(MODELS_MAP))
)

async def run_local_retriever(skill_name: str, query: str, on_process=None) -> str:
    """Runs a Python database retriever script under .agents/skills directly and returns output."""
    script_path = f".agents/skills/{skill_name}/{skill_name}_retriever.py"
    if not os.path.exists(script_path):
        return f"Error: Local retriever script not found at {script_path}"

    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path, query,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE_DIR,
            start_new_session=True,
        )
        if on_process is not None:
            on_process(process)
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return stdout.decode('utf-8').strip()
        else:
            return f"Error executing retriever: {stderr.decode('utf-8').strip()}"
    except Exception as e:
        return f"Error executing retriever script: {e}"

def parse_direct_command(query: str):
    """Parses a query to check if it's a direct slash command (e.g. /bible, /commentary)."""
    clean_query = query.strip()
    tokens = clean_query.split(None, 1)
    if tokens:
        cmd = tokens[0].lower()
        args = tokens[1] if len(tokens) > 1 else ""
        # These run the local SQLite retrievers directly without calling Antigravity.
        # /image and other skills are handled by the agent itself.
        cmd_mapping = {
            '/bible': 'bible',
            '/commentary': 'commentary',
            '/xrefs': 'xrefs',
            '/lexicon': 'lexicon',
            '/morphology': 'morphology',
            '/interlinear': 'interlinear',
            '/original': 'original',
        }
        if cmd in cmd_mapping:
            return cmd_mapping[cmd], args
    return None, None

# ---------------------------------------------------------
# Antigravity stream helpers
# ---------------------------------------------------------

def parse_agy_stream_line(line: str):
    """Parse one stdout line from `agy -p --output-format stream-json`."""
    text = line.strip()
    if not text:
        return None
    try:
        event = json.loads(text)
    except json.JSONDecodeError:
        return {"type": "_nonjson", "data": text[:500]}
    if isinstance(event, dict):
        return event
    return {"type": "_nonjson", "data": text[:500]}

def summarize_tool_input(raw_input) -> str:
    """Pick the most useful field from an Antigravity tool-call payload."""
    if isinstance(raw_input, str):
        try:
            parsed = json.loads(raw_input)
        except json.JSONDecodeError:
            return raw_input
        if not isinstance(parsed, dict):
            return raw_input
        raw_input = parsed
    if not isinstance(raw_input, dict):
        return ""
    for key in (
        "CommandLine", "command", "cmd",
        "Path", "TargetFile", "AbsolutePath", "file_path", "path",
        "Query", "query", "Queries", "queries", "pattern",
        "DirectoryPath", "Url", "url",
        "Prompt", "prompt", "Role", "TypeName", "description", "script_path",
        "toolSummary",
    ):
        value = raw_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, list) and value and all(isinstance(part, str) for part in value):
            return ", ".join(value)
    try:
        return json.dumps(raw_input, ensure_ascii=False)
    except Exception:
        return str(raw_input)


def summarize_tool_intent(tool_name: str, raw_input) -> str:
    """Build a concise human-readable reasoning/intent line for a tool step."""
    if isinstance(raw_input, str):
        try:
            parsed = json.loads(raw_input)
            if isinstance(parsed, dict):
                raw_input = parsed
        except json.JSONDecodeError:
            pass
    if isinstance(raw_input, dict):
        summary = raw_input.get("toolSummary")
        if isinstance(summary, str) and summary.strip():
            return summary.strip()
        if tool_name == "search_web":
            q = raw_input.get("query") or raw_input.get("Query")
            if isinstance(q, str) and q.strip():
                return f"Searching web: {q.strip()}"
        if tool_name in ("read_file", "view_file"):
            p = raw_input.get("Path") or raw_input.get("path") or raw_input.get("file_path")
            if isinstance(p, str) and p.strip():
                rel = os.path.relpath(p.strip(), WORKSPACE_DIR) if p.strip().startswith("/") else p.strip()
                return f"Reading {rel}"
        if tool_name in ("write_file", "create_file"):
            p = raw_input.get("Path") or raw_input.get("path") or raw_input.get("file_path")
            if isinstance(p, str) and p.strip():
                rel = os.path.relpath(p.strip(), WORKSPACE_DIR) if p.strip().startswith("/") else p.strip()
                return f"Writing {rel}"
        if tool_name == "edit_file":
            p = raw_input.get("Path") or raw_input.get("path") or raw_input.get("file_path")
            if isinstance(p, str) and p.strip():
                rel = os.path.relpath(p.strip(), WORKSPACE_DIR) if p.strip().startswith("/") else p.strip()
                return f"Editing {rel}"
        if tool_name == "invoke_subagent":
            role = raw_input.get("Role") or raw_input.get("TypeName") or "subagent"
            prompt = raw_input.get("Prompt") or ""
            if isinstance(prompt, str) and prompt.strip():
                return f"Delegating to {role}: {clip_text(prompt.strip().splitlines()[0], 100)}"
            return f"Delegating to {role}"
    detail = summarize_tool_input(raw_input)
    if detail:
        return f"{tool_name}: {clip_text(detail.splitlines()[0], 120)}"
    return f"Running {tool_name}"


def _read_proto_varint(buf: bytes, pos: int):
    val = 0
    shift = 0
    n = len(buf)
    while pos < n:
        b = buf[pos]
        pos += 1
        val |= (b & 0x7F) << shift
        if not (b & 0x80):
            return val, pos
        shift += 7
        if shift > 63:
            break
    return val, pos


def _iter_proto_fields(buf: bytes):
    pos = 0
    n = len(buf)
    while pos < n:
        tag, pos = _read_proto_varint(buf, pos)
        field_num = tag >> 3
        wire_type = tag & 7
        if field_num <= 0:
            break
        if wire_type == 0:
            val, pos = _read_proto_varint(buf, pos)
            yield field_num, wire_type, val
        elif wire_type == 2:
            length, pos = _read_proto_varint(buf, pos)
            if length < 0 or pos + length > n:
                break
            yield field_num, wire_type, buf[pos:pos + length]
            pos += length
        elif wire_type == 1:
            if pos + 8 > n:
                break
            yield field_num, wire_type, buf[pos:pos + 8]
            pos += 8
        elif wire_type == 5:
            if pos + 4 > n:
                break
            yield field_num, wire_type, buf[pos:pos + 4]
            pos += 4
        else:
            break


def parse_planner_step_payload(blob: bytes):
    """Extract (thinking, response, tool_calls) from a CortexStep PLANNER_RESPONSE protobuf blob."""
    thinking_parts = []
    response_parts = []
    tool_calls = []
    if not isinstance(blob, (bytes, bytearray)):
        return "", "", []
    for fnum, wtype, val in _iter_proto_fields(blob):
        if fnum == 20 and wtype == 2:
            for pfnum, pwtype, pval in _iter_proto_fields(val):
                if pfnum == 3 and pwtype == 2:
                    text = pval.decode("utf-8", errors="replace").strip()
                    if text:
                        thinking_parts.append(text)
                elif pfnum == 1 and pwtype == 2:
                    text = pval.decode("utf-8", errors="replace").strip()
                    if text:
                        response_parts.append(text)
                elif pfnum == 7 and pwtype == 2:
                    tname = ""
                    targs = ""
                    for tfnum, twtype, tval in _iter_proto_fields(pval):
                        if tfnum == 2 and twtype == 2:
                            tname = tval.decode("utf-8", errors="replace").strip()
                        elif tfnum == 3 and twtype == 2:
                            targs = tval.decode("utf-8", errors="replace").strip()
                    if tname:
                        tool_calls.append((tname, targs))
    return "\n\n".join(thinking_parts), "\n\n".join(response_parts), tool_calls


def find_agy_conversation_db(conversation_id: str, data_dirs=AGY_DATA_DIRS):
    """Locate the SQLite conversation store `<conversation_id>.db` written by `agy`."""
    if not conversation_id or "/" in conversation_id or "\\" in conversation_id:
        return None
    candidates = []
    for base in data_dirs:
        path = os.path.join(base, "conversations", f"{conversation_id}.db")
        if os.path.isfile(path):
            try:
                candidates.append((os.path.getmtime(path), path))
            except OSError:
                candidates.append((0.0, path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def find_agy_transcript_jsonl(conversation_id: str, log_uri: str = "", data_dirs=AGY_DATA_DIRS):
    """Locate `transcript_full.jsonl` or `transcript.jsonl` for an `agy` conversation."""
    if log_uri:
        clean_uri = log_uri[7:] if log_uri.startswith("file://") else log_uri
        if os.path.isfile(clean_uri):
            full_sibling = os.path.join(os.path.dirname(clean_uri), "transcript_full.jsonl")
            if os.path.isfile(full_sibling):
                return full_sibling
            return clean_uri
    if not conversation_id or "/" in conversation_id or "\\" in conversation_id:
        return None
    for base in data_dirs:
        logs_dir = os.path.join(base, "brain", conversation_id, ".system_generated", "logs")
        for filename in ("transcript_full.jsonl", "transcript.jsonl"):
            path = os.path.join(logs_dir, filename)
            if os.path.isfile(path):
                return path
    return None


def read_agy_db_planner_steps(conversation_id: str, min_step_index: int = 0, data_dirs=AGY_DATA_DIRS) -> list:
    """Read live PLANNER_RESPONSE steps from the `agy` SQLite conversation database."""
    db_path = find_agy_conversation_db(conversation_id, data_dirs=data_dirs)
    if not db_path:
        return []
    steps = []
    conn = None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.2)
        cur = conn.cursor()
        cur.execute(
            "SELECT idx, status, step_payload FROM steps WHERE step_type = 15 AND idx >= ? ORDER BY idx",
            (int(min_step_index),),
        )
        for idx, status, blob in cur.fetchall():
            thinking, response, tool_calls = parse_planner_step_payload(blob)
            steps.append({
                "step_index": int(idx),
                "status": status,
                "thinking": thinking,
                "content": response,
                "tool_calls": tool_calls,
            })
    except Exception:
        pass
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
    return steps


def read_agy_transcript_planner_steps(
    conversation_id: str,
    min_step_index: int = 0,
    log_uri: str = "",
    data_dirs=AGY_DATA_DIRS,
) -> list:
    """Read PLANNER_RESPONSE steps from `transcript_full.jsonl` / `transcript.jsonl`."""
    jsonl_path = find_agy_transcript_jsonl(conversation_id, log_uri=log_uri, data_dirs=data_dirs)
    if not jsonl_path:
        return []
    steps = []
    try:
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                text = line.strip()
                if not text:
                    continue
                try:
                    obj = json.loads(text)
                except json.JSONDecodeError:
                    continue
                if not isinstance(obj, dict) or obj.get("type") != "PLANNER_RESPONSE":
                    continue
                idx = obj.get("step_index")
                if not isinstance(idx, int) or idx < min_step_index:
                    continue
                thinking = (obj.get("thinking") or obj.get("thought") or "").strip()
                content = (obj.get("content") or "").strip()
                tool_calls = []
                for tc in obj.get("tool_calls") or []:
                    if isinstance(tc, dict):
                        tname = tc.get("name") or tc.get("tool_name") or ""
                        targs = tc.get("args") or tc.get("arguments") or tc.get("input") or {}
                        if tname:
                            tool_calls.append((tname, targs))
                steps.append({
                    "step_index": idx,
                    "status": obj.get("status"),
                    "thinking": thinking,
                    "content": content,
                    "tool_calls": tool_calls,
                })
    except Exception:
        pass
    return steps


def get_agy_max_step_index(conversation_id: str, data_dirs=AGY_DATA_DIRS) -> int:
    """Return the highest recorded step index for a conversation before starting a resumed turn."""
    if not conversation_id:
        return -1
    max_idx = -1
    db_path = find_agy_conversation_db(conversation_id, data_dirs=data_dirs)
    if db_path:
        conn = None
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=0.2)
            cur = conn.cursor()
            cur.execute("SELECT MAX(idx) FROM steps")
            row = cur.fetchone()
            if row and isinstance(row[0], int):
                max_idx = max(max_idx, row[0])
        except Exception:
            pass
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
    jsonl_path = find_agy_transcript_jsonl(conversation_id, data_dirs=data_dirs)
    if jsonl_path:
        try:
            with open(jsonl_path, "r", encoding="utf-8", errors="replace") as handle:
                for line in handle:
                    text = line.strip()
                    if not text:
                        continue
                    try:
                        obj = json.loads(text)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(obj, dict) and isinstance(obj.get("step_index"), int):
                        max_idx = max(max_idx, obj["step_index"])
        except Exception:
            pass
    return max_idx

def clip_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n… (truncated)"

def markdown_fence(text: str) -> str:
    """Wrap text in a fence that the payload cannot close early."""
    safe = text.replace("```", "'''")
    return f"```\n{safe}\n```"

def flatten_tool_result(raw) -> str:
    """Normalize a tool output to readable text."""
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = []
        for block in raw:
            if isinstance(block, dict):
                if block.get("type") == "text" and block.get("text"):
                    parts.append(block["text"])
                elif block.get("type") == "image":
                    parts.append("(image output)")
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    try:
        return json.dumps(raw, ensure_ascii=False, indent=2)
    except Exception:
        return str(raw)

# ---------------------------------------------------------
# NiceGUI Web Application State & Layout
# ---------------------------------------------------------

class BibleMateApp:
    def __init__(self):
        # Settings state
        self.selected_model = DEFAULT_MODEL
        self.selected_persona = 'Auto'
        self.selected_skill = 'Auto'
        # Headless Antigravity session for this conversation. Empty means a new session.
        self.agy_conversation_id = None
        self.agy_last_rules_key = None
        self.agy_proc = None

        # UI Toggles and References
        self.left_drawer = None
        self.right_drawer = None
        self.chat_container = None
        self.progress_container = None
        self.thinking_display = None
        self.tool_display = None
        self.tool_output_display = None
        self.terminal_display = None
        self.delete_button = None
        self.export_button = None
        self.edit_button = None
        self.add_file_button = None
        self.add_folder_button = None
        self.selected_node_id = None
        self.action_button = None
        self.action_button_tooltip = None
        self.header = None
        self.footer = None
        self.page_column = None
        self.focus_button = None
        self.focus_button_tooltip = None
        self.reading_focus = False
        self._drawer_open_before_focus = False

        # State tracking
        self.active_agent_running = False
        self.running_chat_task = None
        self.terminal_logs = []
        self.slash_commands = self.get_slash_commands()

        # Log Hook Registration
        self.setup_logging_interceptor()

    def get_slash_commands(self) -> list:
        """Lists slash commands from .agents/workflows and .agents/skills."""
        commands = set()
        workflows_dir = '.agents/workflows'
        if os.path.isdir(workflows_dir):
            try:
                for name in os.listdir(workflows_dir):
                    if name.endswith('.md'):
                        commands.add('/' + name[:-3])
            except Exception:
                pass
        skills_dir = '.agents/skills'
        if os.path.isdir(skills_dir):
            try:
                for name in os.listdir(skills_dir):
                    if os.path.isdir(os.path.join(skills_dir, name)):
                        commands.add('/' + name)
            except Exception:
                pass
        return sorted(commands, key=str.lower)

    def setup_logging_interceptor(self):
        """Remember the server loop. Antigravity progress is read from the CLI stream."""
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            self.loop = None

    def append_runtime_log(self, log_line: str):
        """Append one line to the on-screen system log."""
        if not log_line:
            return
        self.terminal_logs.append(log_line)
        if len(self.terminal_logs) > 500:
            self.terminal_logs.pop(0)
        display = getattr(self, 'terminal_display', None)
        if display is None:
            return
        try:
            display.set_content(markdown_fence("\n".join(self.terminal_logs[-30:])))
        except Exception:
            pass

    def _notify_progress(self, message: str):
        try:
            ui.notify(message, group='agent_progress', type='ongoing', timeout=0)
        except RuntimeError:
            pass

    def _set_markdown(self, widget, text: str):
        if widget is None:
            return
        try:
            widget.set_content(text)
        except Exception:
            pass

    def resolve_skill_name(self, token: str):
        """Match a slash-command token to an .agents skill directory name."""
        if not token:
            return None
        wanted = token.lower()
        for skill in SKILLS_LIST:
            if skill.lower() == wanted:
                return skill
        return None

    def build_system_rules(self, active_skill: str) -> str:
        """Rules passed to Antigravity CLI."""
        rules = (
            "You are BibleMate AI running inside the local BibleMate web app, "
            "backed by the signed-in Antigravity CLI. Follow AGENTS.md and the skills under .agents/skills/. "
            "Do not quote scripture from memory; retrieve verses with the local bible skill or python3 .agents/skills/bible/bible_retriever.py."
        )
        if self.selected_persona != 'Auto':
            persona = PERSONAS_MAP.get(self.selected_persona, '')
            if persona:
                rules += f"\n\nAdopt the following persona instructions:\n{persona}"
        else:
            rules += (
                "\nYou have access to specialized personas listed in .agents/agents.md. "
                "Rotate them dynamically depending on the research phase."
            )

        if active_skill != 'Auto':
            rules += (
                f"\n\nCRITICAL TASK REQUIREMENT: You MUST use the local BibleMate skill "
                f"'{active_skill}'. Read `.agents/skills/{active_skill}/SKILL.md` and follow it "
                "before you answer. Do not answer scripture from memory. Retrieve verses with "
                "`python3 .agents/skills/bible/bible_retriever.py`."
            )

        rules += (
            "\n\n## WORKSPACE FILE RULES (MANDATORY)"
            "\nThe current working directory IS the repository root. All file output MUST be saved"
            " into this workspace using RELATIVE paths only — never absolute paths."
            "\n- Save ALL study outputs (outlines, sermons, devotionals, analyses, etc.) to the"
            " `biblemate/` subdirectory."
            "\n- Every output filename MUST be prefixed with a timestamp in the format"
            " `YYYY-MM-DD-HH-MM-SS_` followed by a short descriptive name ending in `.md`."
            " To get the current timestamp, run this command first:"
            " `python3 -c \"import datetime; print(datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))\"`"
            " then use the printed value as the prefix."
            " Example filename: `biblemate/2026-06-21-22-09-00_hope_theological_study.md`."
            "\n- Save generated images to `images/`."
            "\n- NEVER tell the user a file has been saved unless you have actually written it to"
            " one of these workspace directories in this session."
            "\n- Do NOT write files to any artifact, brain, or temporary directory outside the workspace."
        )
        return rules

    def _refresh_thinking(self, state: dict):
        """Render the accumulated thinking monologue (or live step intents) into thinking_display."""
        thoughts = state.get("thoughts") or {}
        step_intents = state.get("step_intents") or {}

        blocks = [text.strip() for text in thoughts.values() if isinstance(text, str) and text.strip()]
        if blocks:
            max_thought_step_by_conv = {}
            for (cid, sidx), text in thoughts.items():
                if isinstance(text, str) and text.strip() and isinstance(sidx, int):
                    prev_max = max_thought_step_by_conv.get(cid, -1)
                    if sidx > prev_max:
                        max_thought_step_by_conv[cid] = sidx

            trailing_intents = []
            for (cid, sidx), intent in step_intents.items():
                if not isinstance(intent, str) or not intent.strip():
                    continue
                if isinstance(sidx, int) and sidx > max_thought_step_by_conv.get(cid, -1):
                    line = f"*→ {intent.strip()}*"
                    if line not in trailing_intents:
                        trailing_intents.append(line)

            body = "\n\n".join(blocks)
            if trailing_intents:
                body = body + "\n\n" + "\n".join(trailing_intents[-3:])
            rendered = clip_text(body, 8000)

            latest_key = next(reversed(thoughts))
            if state.get("last_notified_thought_key") != latest_key:
                state["last_notified_thought_key"] = latest_key
                state["notified_think"] = True
                latest_text = blocks[-1]
                snippet = latest_text.splitlines()[0].strip("*# ") if latest_text else "reasoning"
                if len(snippet) > 50:
                    snippet = snippet[:50] + "..."
                self._notify_progress(f"Antigravity thinking: {snippet}")
        elif step_intents:
            intent_lines = []
            for intent in step_intents.values():
                if isinstance(intent, str) and intent.strip():
                    item = f"*• {intent.strip()}*"
                    if item not in intent_lines:
                        intent_lines.append(item)
            rendered = clip_text("\n".join(intent_lines), 8000) if intent_lines else "*Analyzing query...*"
        elif state.get("streamed"):
            rendered = "*Synthesizing response...*"
        else:
            rendered = "*Analyzing query...*"

        state["thinking"] = rendered
        if state.get("_last_rendered_thinking") != rendered:
            state["_last_rendered_thinking"] = rendered
            self._set_markdown(self.thinking_display, rendered)

    def _sync_agy_thinking(self, state: dict):
        """Pull live PLANNER_RESPONSE thinking blocks from SQLite and transcript JSONL."""
        root_conv_id = state.get("conversation_id") or self.agy_conversation_id
        targets = []
        if root_conv_id:
            targets.append((root_conv_id, "", state.get("min_step_index", 0), ""))
        for sub_id, sub_meta in list((state.get("subagents") or {}).items()):
            if isinstance(sub_meta, dict):
                targets.append((
                    sub_id,
                    sub_meta.get("label") or "subagent",
                    0,
                    sub_meta.get("log_uri") or "",
                ))

        for cid, label, min_idx, log_uri in targets:
            prefix = f"**[{label}]**\n" if label else ""
            combined_steps = {}
            for item in read_agy_db_planner_steps(cid, min_step_index=min_idx):
                combined_steps[item["step_index"]] = item
            for item in read_agy_transcript_planner_steps(cid, min_step_index=min_idx, log_uri=log_uri):
                sidx = item["step_index"]
                if sidx not in combined_steps:
                    combined_steps[sidx] = item
                else:
                    existing = combined_steps[sidx]
                    if item.get("thinking") and len(item["thinking"]) > len(existing.get("thinking") or ""):
                        existing["thinking"] = item["thinking"]
                    if item.get("content") and not existing.get("content"):
                        existing["content"] = item["content"]
                    if item.get("tool_calls") and not existing.get("tool_calls"):
                        existing["tool_calls"] = item["tool_calls"]

            for sidx in sorted(combined_steps):
                item = combined_steps[sidx]
                key = (cid, sidx)
                thinking = (item.get("thinking") or "").strip()
                content = (item.get("content") or "").strip()
                tool_calls = item.get("tool_calls") or []
                if thinking:
                    state.setdefault("thoughts", {})[key] = prefix + thinking
                elif content and tool_calls:
                    state.setdefault("thoughts", {})[key] = prefix + content

                if tool_calls:
                    intents = [
                        summarize_tool_intent(tname, targs)
                        for tname, targs in tool_calls[:3]
                        if tname
                    ]
                    if intents:
                        intent_prefix = f"[{label}] " if label else ""
                        state.setdefault("step_intents", {})[key] = intent_prefix + "; ".join(intents)

        self._refresh_thinking(state)

    async def _poll_agy_thinking(self, state: dict):
        """Continuously poll the live conversation store while `agy -p` is executing."""
        try:
            while True:
                self._sync_agy_thinking(state)
                await asyncio.sleep(0.25)
        except asyncio.CancelledError:
            return

    def apply_agy_event(self, event: dict, state: dict, response_card):
        """Update the chat bubble and the live progress panels from one Antigravity stream event."""
        etype = event.get("event") or event.get("type")

        if etype == "init":
            conv_id = event.get("conversation_id")
            if conv_id:
                self.agy_conversation_id = conv_id
                state["conversation_id"] = conv_id
                self.append_runtime_log(f"init session={conv_id}")
                self._sync_agy_thinking(state)
            return

        if etype == "step_update":
            step = event.get("step_update") or {}
            step_type = step.get("step_type")
            step_state = step.get("state")
            conv_id = step.get("conversation_id") or state.get("conversation_id") or self.agy_conversation_id or "default"
            if step.get("conversation_id") and not state.get("conversation_id"):
                state["conversation_id"] = step["conversation_id"]
                self.agy_conversation_id = step["conversation_id"]

            step_index = step.get("step_index")
            idx_key = step_index if isinstance(step_index, int) else 0

            if step_type == "user_input" and isinstance(step_index, int):
                state["min_step_index"] = max(state.get("min_step_index", 0), step_index + 1)

            subagent_info = step.get("subagent_info")
            if isinstance(subagent_info, dict) and subagent_info.get("conversation_id"):
                sub_id = subagent_info["conversation_id"]
                sub_label = subagent_info.get("role") or subagent_info.get("type_name") or "subagent"
                state.setdefault("subagents", {})[sub_id] = {
                    "label": sub_label,
                    "log_uri": subagent_info.get("log_uri") or "",
                }

            if step_type == "agent_response":
                delta = step.get("text_delta") or ""
                if delta:
                    if state.get("needs_paragraph_break") and state["text"] and not state["text"].endswith("\n\n"):
                        state["text"] = state["text"].rstrip("\n") + "\n\n"
                    state["needs_paragraph_break"] = False
                    state["text"] += delta
                    state["streamed"] = True
                    step_texts = state.setdefault("step_texts", {})
                    step_texts[(conv_id, idx_key)] = step_texts.get((conv_id, idx_key), "") + delta
                    self._render_response(response_card, state["text"])

                thinking_delta = step.get("thinking_delta") or ""
                thinking = step.get("thinking") or step.get("thought") or ""
                if thinking_delta:
                    stream_thoughts = state.setdefault("stream_thoughts", {})
                    combined = stream_thoughts.get((conv_id, idx_key), "") + thinking_delta
                    stream_thoughts[(conv_id, idx_key)] = combined
                    if combined.strip():
                        state.setdefault("thoughts", {})[(conv_id, idx_key)] = combined.strip()
                elif thinking and thinking.strip():
                    state.setdefault("thoughts", {})[(conv_id, idx_key)] = thinking.strip()

            elif step_type == "tool":
                state["needs_paragraph_break"] = True
                state["needs_think_break"] = True
                state["notified_think"] = False

                # If an earlier agent_response step streamed pre-tool commentary without a separate
                # thinking block, promote that commentary into the thinking monologue.
                for (tcid, tsidx), stext in list((state.get("step_texts") or {}).items()):
                    if tcid == conv_id and tsidx < idx_key and stext.strip():
                        state.setdefault("thoughts", {}).setdefault((tcid, tsidx), stext.strip())

                tool_name = step.get("tool_name") or "tool"
                tool_info = step.get("tool_info") or {}
                params = tool_info.get("parameters") or {}
                output = tool_info.get("output")

                intent = summarize_tool_intent(tool_name, params)
                if intent:
                    state.setdefault("step_intents", {})[(conv_id, idx_key)] = intent

                detail = summarize_tool_input(params)
                shown = detail or tool_name

                if step_state == "ACTIVE":
                    self._set_markdown(
                        self.tool_display,
                        f"**Executing:** `{tool_name}`" + (f"\n\n`{clip_text(shown, 500)}`" if detail else ""),
                    )
                    display_cmd = shown.replace('python3 .agents/skills/', '')
                    if len(display_cmd) > 50:
                        display_cmd = display_cmd[:50] + "..."
                    self._notify_progress(f"Antigravity executing: {display_cmd}")
                    self.append_runtime_log(f"tool {tool_name}: {clip_text(shown, 300)}")

                elif step_state == "DONE":
                    self.append_runtime_log(f"tool {tool_name} completed")
                    if output is not None and str(output).strip():
                        raw_output = flatten_tool_result(output)
                        self._set_markdown(self.tool_output_display, markdown_fence(clip_text(raw_output, 4000)))

            self._sync_agy_thinking(state)
            return

        if etype == "result":
            res = event.get("result") or {}
            conv_id = res.get("conversation_id")
            if conv_id:
                self.agy_conversation_id = conv_id
                state["conversation_id"] = conv_id

            self._sync_agy_thinking(state)

            status = res.get("status")
            duration = res.get("duration_seconds")
            turns = res.get("num_turns")
            usage = res.get("usage") or {}

            bits = [f"antigravity finished status={status}"]
            if duration is not None:
                bits.append(f"duration={duration:.1f}s")
            if turns is not None:
                bits.append(f"turns={turns}")
            if usage.get("total_tokens"):
                bits.append(f"tokens={usage['total_tokens']}")
            self.append_runtime_log(" ".join(bits))

            final_resp = res.get("response") or ""
            if status != "SUCCESS" and not state["text"]:
                state["error"] = res.get("error") or f"Execution ended with status: {status}"
            elif final_resp and not state["text"]:
                state["text"] = final_resp
                self._render_response(response_card, state["text"])
            return

        if etype == "_nonjson":
            self.append_runtime_log(event.get("data") or "")

    def _render_response(self, response_card, text: str):
        if response_card is None:
            return
        try:
            response_card.clear()
            with response_card:
                ui.markdown(text).classes('text-current')
        except RuntimeError:
            pass

    async def _drain_stderr(self, process):
        if process.stderr is None:
            return
        try:
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                text = line.decode('utf-8', errors='replace').rstrip()
                if text:
                    self.append_runtime_log(text)
        except asyncio.CancelledError:
            return

    async def _stop_agy_proc(self, proc=None):
        """Stop the headless agy process group started for the current turn."""
        if proc is None:
            proc = self.agy_proc
        if proc is None or proc.returncode is not None:
            return
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except Exception:
            try:
                proc.terminate()
            except Exception:
                return
        try:
            await asyncio.wait_for(proc.wait(), timeout=3)
        except asyncio.TimeoutError:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass

    def build_file_tree_nodes(self):
        """Recursively builds the dictionary hierarchy for ui.tree representing files and directories."""
        def build_node(rel_path):
            full_path = os.path.join(WORKSPACE_DIR, rel_path)
            basename = os.path.basename(rel_path)
            if os.path.isdir(full_path):
                children = []
                try:
                    for entry in os.listdir(full_path):
                        if entry.startswith('.'):
                            continue
                        child_rel = os.path.join(rel_path, entry)
                        child_node = build_node(child_rel)
                        if child_node:
                            children.append(child_node)
                except Exception:
                    pass
                return {
                    'id': rel_path.replace('\\', '/'),
                    'label': basename if basename else rel_path,
                    'children': children
                }
            else:
                normalized = rel_path.replace('\\', '/')
                parts = normalized.split('/')
                top_folder = parts[0]
                is_valid = False
                if top_folder == 'images':
                    is_valid = basename.lower().endswith(('.png', '.jpg', '.jpeg', '.md'))
                elif top_folder == 'export':
                    is_valid = basename.lower().endswith(('.md', '.docx'))
                elif top_folder in ('docs', 'biblemate', 'notes'):
                    is_valid = basename.endswith('.md')

                if is_valid:
                    return {
                        'id': rel_path.replace('\\', '/'),
                        'label': basename
                    }
                return None

        nodes = []
        for folder in ['biblemate', 'images', 'export', 'docs', 'notes']:
            if os.path.exists(folder):
                node = build_node(folder)
                if node:
                    nodes.append(node)

        def sort_nodes(nodes_list, reverse=False):
            nodes_list.sort(key=lambda x: x['label'], reverse=reverse)
            for node in nodes_list:
                if 'children' in node:
                    child_reverse = node['id'].startswith('biblemate')
                    sort_nodes(node['children'], reverse=child_reverse)

        sort_nodes(nodes, reverse=False)
        return nodes

    def handle_file_select(self, node_id: str):
        if not node_id:
            return

        is_markdown = node_id.endswith('.md')
        is_image = node_id.lower().endswith(('.png', '.jpg', '.jpeg'))
        is_docx = node_id.lower().endswith('.docx')

        if not (is_markdown or is_image or is_docx):
            return

        file_path = os.path.join(WORKSPACE_DIR, node_id)
        if os.path.exists(file_path):
            try:
                if is_docx:
                    ui.download(file_path)
                    ui.notify(f"Downloading: {os.path.basename(node_id)}", type='info')
                    return

                # Switch tab to reader
                self.main_tabs.set_value('reader')
                # Render content
                self.reader_title.set_text(os.path.basename(node_id))
                self.reader_container.clear()
                with self.reader_container:
                    if is_markdown:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        ui.markdown(content).classes('theme-text')
                    elif is_image:
                        web_path = f"/{node_id}"
                        ui.image(web_path).classes('w-full max-w-2xl mx-auto rounded-lg shadow-lg border theme-border')

                ui.notify(f"Loaded: {os.path.basename(node_id)}", type='positive')
            except Exception as e:
                ui.notify(f"Error loading file: {e}", type='negative')

    def is_deletable(self, path: str) -> bool:
        """Checks if a given path is allowed to be deleted by the user."""
        if not path:
            return False
        clean_path = os.path.normpath(path).replace('\\', '/')

        # Protect any README.md files
        if os.path.basename(clean_path).lower() == 'readme.md':
            return False

        # Protect the docs folder and any files in it
        if clean_path.lower() == 'docs' or clean_path.lower().startswith('docs/'):
            return False

        # Protect images/Timelines folder and its contents
        if clean_path.lower() == 'images/timelines' or clean_path.lower().startswith('images/timelines/'):
            return False

        # Explicitly protect root and direct parent folders
        protected = {
            '.', '', 'biblemate', 'export', 'export/md', 'export/docx', 'images',
            'images/readme.md', 'images/readme', 'notes'
        }
        if clean_path.lower() in protected or clean_path.startswith(('.', '..')):
            return False

        # Must be strictly nested inside allowed directories
        allowed_roots = ('biblemate/', 'export/', 'images/', 'notes/')
        return any(clean_path.startswith(root) for root in allowed_roots)

    def confirm_delete(self):
        """Displays a confirmation dialog to delete the selected tree item."""
        node_id = getattr(self, 'selected_node_id', None)
        if not node_id or not self.is_deletable(node_id):
            ui.notify("This item cannot be deleted.", type='warning')
            return

        is_dir = os.path.isdir(os.path.join(WORKSPACE_DIR, node_id))
        item_type = "folder" if is_dir else "file"

        with ui.dialog() as dialog, ui.card().classes('p-6 max-w-sm'):
            ui.label('Confirm Deletion').classes('text-lg font-bold theme-text mb-2')
            ui.label(f'Are you sure you want to permanently delete the {item_type} "{os.path.basename(node_id)}"? This action cannot be undone.').classes('text-sm theme-muted mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Delete', color='negative', on_click=lambda: self.perform_delete(node_id, dialog)).props('elevated')
        dialog.open()

    def perform_delete(self, node_id: str, dialog):
        """Executes deletion of the verified file or folder."""
        dialog.close()
        full_path = os.path.join(WORKSPACE_DIR, node_id)
        if not os.path.exists(full_path):
            ui.notify("Item not found.", type='warning')
            return

        try:
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
                ui.notify(f"Deleted folder: {os.path.basename(node_id)}", type='positive')
            else:
                os.remove(full_path)
                ui.notify(f"Deleted file: {os.path.basename(node_id)}", type='positive')

            self.selected_node_id = None
            if self.delete_button:
                self.delete_button.set_visibility(False)
            if self.export_button:
                self.export_button.set_visibility(False)
            if self.edit_button:
                self.edit_button.set_visibility(False)
            if self.add_file_button:
                self.add_file_button.set_visibility(False)
            if self.add_folder_button:
                self.add_folder_button.set_visibility(False)

            # Clear reader view if deleted file was open
            if self.reader_title.text == os.path.basename(node_id):
                self.reader_title.set_text("No File Selected")
                self.reader_container.clear()
                with self.reader_container:
                    ui.markdown('Select a file from the left sidebar tree to view it. New exegesis results are written directly to `biblemate/` and `export/`, and images to `images/`.').classes('theme-text')

            self.refresh_file_tree()
        except Exception as e:
            ui.notify(f"Error during deletion: {e}", type='negative')

    async def export_to_docx(self):
        """Converts the selected markdown file to docx using pandoc."""
        node_id = getattr(self, 'selected_node_id', None)
        if not node_id or not node_id.lower().endswith('.md'):
            ui.notify("No markdown file selected for export.", type='warning')
            return

        full_path = os.path.join(WORKSPACE_DIR, node_id)
        if not os.path.exists(full_path):
            ui.notify("File not found.", type='warning')
            return

        import datetime
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        original_basename = os.path.basename(node_id)
        if original_basename.lower().endswith('.md'):
            original_name_without_ext = original_basename[:-3]
        else:
            original_name_without_ext = original_basename

        output_filename = f"{timestamp}_{original_name_without_ext}.docx"
        output_dir = os.path.join(WORKSPACE_DIR, 'export', 'docx')
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, output_filename)

        try:
            process = await asyncio.create_subprocess_exec(
                'pandoc', '-s', '-o', output_path, full_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                ui.notify(f"Successfully exported to DOCX: {output_filename}", type='positive')
                self.refresh_file_tree()
            else:
                err_msg = stderr.decode('utf-8').strip()
                ui.notify(f"Pandoc error: {err_msg}", type='negative')
        except Exception as e:
            ui.notify(f"Error during export: {e}", type='negative')

    def start_edit(self):
        node_id = getattr(self, 'selected_node_id', None)
        if not node_id or not node_id.lower().endswith('.md'):
            ui.notify("No markdown file selected for editing.", type='warning')
            return

        file_path = os.path.join(WORKSPACE_DIR, node_id)
        if not os.path.exists(file_path):
            ui.notify("File not found.", type='warning')
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.main_tabs.set_value('reader')
            self.reader_title.set_text(f"Editing: {os.path.basename(node_id)}")
            self.reader_container.clear()

            with self.reader_container:
                # Textarea for editing the markdown content
                editor = ui.textarea(
                    value=content,
                    label='Edit Content (Markdown)'
                ).props('outlined autogrow input-class="font-mono theme-text"').classes('w-full min-h-[400px] mb-4 theme-text')

                with ui.row().classes('w-full gap-4'):
                    ui.button('Save', icon='save', color='positive', on_click=lambda: self.save_edit(node_id, editor.value)).props('elevated')
                    ui.button('Cancel', icon='cancel', color='grey', on_click=lambda: self.handle_file_select(node_id)).props('flat')

            ui.notify("Editor opened", type='info')
        except Exception as e:
            ui.notify(f"Error opening editor: {e}", type='negative')

    def save_edit(self, node_id: str, new_content: str):
        file_path = os.path.join(WORKSPACE_DIR, node_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            ui.notify(f"Successfully saved {os.path.basename(node_id)}", type='positive')
            self.handle_file_select(node_id)
        except Exception as e:
            ui.notify(f"Error saving file: {e}", type='negative')

    def prompt_create_item(self, is_folder: bool):
        parent_dir = getattr(self, 'selected_node_id', 'notes')
        if not parent_dir:
            parent_dir = 'notes'

        full_parent_path = os.path.join(WORKSPACE_DIR, parent_dir)
        if not os.path.isdir(full_parent_path):
            parent_dir = os.path.dirname(parent_dir)
            full_parent_path = os.path.join(WORKSPACE_DIR, parent_dir)

        item_type = "Folder" if is_folder else "File"

        with ui.dialog() as dialog, ui.card().classes('p-6 w-80'):
            ui.label(f'Add New {item_type}').classes('text-lg font-bold mb-2')
            ui.label(f'Inside: {parent_dir}').classes('text-xs theme-muted mb-4')
            name_input = ui.input(f'{item_type} Name').classes('w-full mb-6')

            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Create', on_click=lambda: self.create_item(parent_dir, name_input.value, is_folder, dialog)).props('elevated')
        dialog.open()

    def create_item(self, parent_dir: str, name: str, is_folder: bool, dialog):
        dialog.close()
        name = name.strip()
        if not name:
            ui.notify("Name cannot be empty.", type='warning')
            return

        if not is_folder and not name.lower().endswith('.md'):
            name += '.md'

        target_path = os.path.join(WORKSPACE_DIR, parent_dir, name)

        # Verify path security
        normalized_target = os.path.normpath(target_path).replace('\\', '/')
        notes_root = os.path.normpath(os.path.join(WORKSPACE_DIR, 'notes')).replace('\\', '/')
        if not normalized_target.startswith(notes_root):
            ui.notify("Invalid path target.", type='negative')
            return

        if os.path.exists(target_path):
            ui.notify(f"Item '{name}' already exists.", type='warning')
            return

        try:
            if is_folder:
                os.makedirs(target_path, exist_ok=True)
                ui.notify(f"Folder '{name}' created successfully.", type='positive')
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {name[:-3]}\n\n")
                ui.notify(f"File '{name}' created successfully.", type='positive')

            self.refresh_file_tree()
        except Exception as e:
            ui.notify(f"Error creating item: {e}", type='negative')

    def handle_tree_select(self, node_id: str):
        self.selected_node_id = node_id
        if node_id:
            deletable = self.is_deletable(node_id)
            if self.delete_button:
                self.delete_button.set_visibility(deletable)

            is_file = os.path.isfile(os.path.join(WORKSPACE_DIR, node_id))
            is_md = is_file and node_id.lower().endswith('.md')
            if self.export_button:
                self.export_button.set_visibility(is_md)

            if self.edit_button:
                self.edit_button.set_visibility(is_md and deletable)

            is_dir = os.path.isdir(os.path.join(WORKSPACE_DIR, node_id))
            is_notes = (node_id == 'notes' or node_id.startswith('notes/'))
            if self.add_file_button:
                self.add_file_button.set_visibility(is_dir and is_notes)
            if self.add_folder_button:
                self.add_folder_button.set_visibility(is_dir and is_notes)

            # Open files in the Document Reader automatically
            if is_file:
                self.handle_file_select(node_id)
        else:
            if self.delete_button:
                self.delete_button.set_visibility(False)
            if self.export_button:
                self.export_button.set_visibility(False)
            if self.edit_button:
                self.edit_button.set_visibility(False)
            if self.add_file_button:
                self.add_file_button.set_visibility(False)
            if self.add_folder_button:
                self.add_folder_button.set_visibility(False)

    def refresh_file_tree(self):
        nodes = self.build_file_tree_nodes()
        self.file_tree.clear()
        with self.file_tree:
            ui.tree(nodes=nodes, label_key='label', on_select=lambda e: self.handle_tree_select(e.value))
        ui.notify("File tree refreshed!", type='info')

    def update_action_button(self, to_stop: bool):
        try:
            if to_stop:
                self.action_button.props('icon=stop color=negative', remove='icon=send')
                self.action_button_tooltip.set_text('Stop Execution')
            else:
                self.action_button.props('icon=send', remove='icon=stop color=negative')
                self.action_button_tooltip.set_text('Send Request')
            self.action_button.update()
        except Exception:
            pass

    async def handle_stop(self):
        if self.running_chat_task and not self.running_chat_task.done():
            self.running_chat_task.cancel()
            ui.notify("Stopping agent execution...", type='warning')

    def active_skill_for_query(self, user_query: str) -> str:
        """Honor the settings dropdown, or a leading slash command when it is Auto."""
        active_skill = self.selected_skill
        if active_skill == 'Auto' and user_query.strip().startswith('/'):
            tokens = user_query.strip().split(None, 1)
            if tokens:
                resolved = self.resolve_skill_name(tokens[0][1:])
                if resolved and resolved != 'Auto':
                    active_skill = resolved
        return active_skill

    async def run_direct_retriever(self, skill_name: str, args: str, response_card):
        """Answer lookup commands from the local SQLite retrievers, without calling Antigravity."""
        self._notify_progress(f"Local retriever: {skill_name}")
        self._set_markdown(
            self.thinking_display,
            f"Running the local `{skill_name}` database. This request does not call the agent.",
        )
        script = f"python3 .agents/skills/{skill_name}/{skill_name}_retriever.py"
        self._set_markdown(self.tool_display, f"**Executing:** `{script}`")
        if not args.strip():
            text = f"Add a query after `/{skill_name}`."
        else:
            text = await run_local_retriever(
                skill_name,
                args.strip(),
                on_process=lambda process: setattr(self, 'agy_proc', process),
            )
        self._set_markdown(self.tool_output_display, markdown_fence(clip_text(text or "(no output)", 4000)))
        self._render_response(response_card, text or "(no output)")

    async def run_agy_turn(self, user_query: str, response_card):
        """Run one headless `agy -p` turn on the signed-in Google subscription and stream it into the UI."""
        active_skill = self.active_skill_for_query(user_query)
        sdk_model = MODELS_MAP.get(self.selected_model, MODELS_MAP[DEFAULT_MODEL])

        rules_key = (self.selected_persona, active_skill)
        if not self.agy_conversation_id or self.agy_last_rules_key != rules_key:
            system_rules = self.build_system_rules(active_skill)
            full_prompt = (
                f"[System Instructions]\n{system_rules}\n\n"
                f"[User Request]\n{user_query}"
            )
            self.agy_last_rules_key = rules_key
        else:
            full_prompt = user_query

        stderr_task = None
        thinking_task = None
        min_step_index = 0
        if self.agy_conversation_id:
            prev_max = get_agy_max_step_index(self.agy_conversation_id)
            if prev_max >= 0:
                min_step_index = prev_max + 1
        state = {
            "text": "",
            "thinking": "",
            "thoughts": {},
            "step_intents": {},
            "step_texts": {},
            "stream_thoughts": {},
            "subagents": {},
            "conversation_id": self.agy_conversation_id or "",
            "min_step_index": min_step_index,
            "notified_think": False,
            "last_notified_thought_key": None,
            "error": "",
            "streamed": False,
            "needs_paragraph_break": False,
            "needs_think_break": False,
        }
        try:
            cmd = [
                AGY_BIN,
                '-p', full_prompt,
                '--output-format', 'stream-json',
                '--dangerously-skip-permissions',
                '--disable-slash-commands',
            ]
            if sdk_model:
                cmd.extend(['--model', sdk_model])
            if self.agy_conversation_id:
                cmd.extend(['--conversation', self.agy_conversation_id])

            env = os.environ.copy()
            # Do not inject an API key. The CLI reuses whatever Google subscription
            # session it is signed in with, so this app needs no Gemini API key.

            self.append_runtime_log(
                f"starting agy model={sdk_model or 'default'} skill={active_skill} resume={bool(self.agy_conversation_id)}"
            )
            self._notify_progress("Antigravity: Planning study...")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=WORKSPACE_DIR,
                env=env,
                start_new_session=True,
                limit=AGY_STREAM_LIMIT,
            )
            self.agy_proc = process
            stderr_task = asyncio.create_task(self._drain_stderr(process))
            thinking_task = asyncio.create_task(self._poll_agy_thinking(state))

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                event = parse_agy_stream_line(line.decode("utf-8", errors="replace"))
                if event:
                    self.apply_agy_event(event, state, response_card)

            returncode = await process.wait()
            if thinking_task is not None and not thinking_task.done():
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass
                thinking_task = None
            self._sync_agy_thinking(state)
            if stderr_task is not None:
                await stderr_task
                stderr_task = None

            if state["error"] and not state["text"]:
                self._render_response(response_card, f"**Antigravity error:** {state['error']}")
            elif returncode not in (0, None) and not state["text"]:
                self._render_response(
                    response_card,
                    f"**Antigravity exited with code {returncode}.** See System Logs for details.",
                )
            elif not state["text"]:
                self._render_response(response_card, "Antigravity finished without a text reply. See System Logs.")
        finally:
            if thinking_task is not None and not thinking_task.done():
                thinking_task.cancel()
                try:
                    await thinking_task
                except asyncio.CancelledError:
                    pass
            if stderr_task is not None and not stderr_task.done():
                stderr_task.cancel()
                try:
                    await stderr_task
                except asyncio.CancelledError:
                    pass
            proc = self.agy_proc
            if proc is not None and proc.returncode is None:
                try:
                    await asyncio.shield(self._stop_agy_proc(proc))
                except Exception:
                    pass
            self.agy_proc = None

    async def execute_agent_chat(self, user_query: str):
        try:
            self.running_chat_task = asyncio.current_task()
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        if self.active_agent_running:
            ui.notify("An agent is already running. Please wait...", type='warning')
            return

        self.active_agent_running = True
        self.terminal_logs.clear()
        self.update_action_button(to_stop=True)

        response_card = None
        try:
            self.add_chat_bubble(user_query, sent=True)
            self._notify_progress("Antigravity: Initializing workspace...")
            self.progress_container.set_visibility(True)
            self.thinking_display.set_content("*Analyzing query...*")
            self.tool_display.set_content("**Awaiting agent action...**")
            self.tool_output_display.set_content("")
            response_card = self.add_chat_bubble("Preparing Antigravity and BibleMate skills...", sent=False, italic=True)

            direct_skill, direct_args = parse_direct_command(user_query)
            if direct_skill:
                await self.run_direct_retriever(direct_skill, direct_args or "", response_card)
            else:
                await self.run_agy_turn(user_query, response_card)
        except asyncio.CancelledError:
            proc = self.agy_proc
            try:
                await asyncio.shield(self._stop_agy_proc(proc))
            except Exception:
                pass
            try:
                self.add_chat_bubble("Agent execution stopped by user.", sent=False, italic=True)
            except RuntimeError:
                pass
        except Exception as e:
            try:
                if response_card:
                    response_card.clear()
                    with response_card:
                        ui.label(f"Execution Error: {str(e)}").classes('text-negative font-semibold')
                else:
                    self.add_chat_bubble(f"Execution Error: {str(e)}", sent=False)
            except RuntimeError:
                pass
        finally:
            self.active_agent_running = False
            self.agy_proc = None
            self.update_action_button(to_stop=False)
            try:
                self.progress_container.set_visibility(False)
                ui.notify("System Ready", group='agent_progress', type='positive', timeout=2000)
                self.refresh_file_tree()
            except RuntimeError:
                pass

    def add_chat_bubble(self, text: str, sent: bool, italic: bool = False):
        align_class = "justify-end" if sent else "justify-start"
        bubble_bg = "theme-inset theme-text border theme-border" if sent else "theme-panel theme-text border theme-border"
        border_radius = "rounded-l-2xl rounded-tr-2xl" if sent else "rounded-r-2xl rounded-tl-2xl"
        card_width = "max-w-[85%] md:max-w-[75%]" if sent else "w-full"

        with self.chat_container:
            with ui.row().classes(f'w-full {align_class} mb-4 items-end animate-fade-in'):
                with ui.card().classes(f'{card_width} p-4 shadow-md backdrop-blur-sm {bubble_bg} {border_radius}') as card:
                    if italic:
                        ui.label(text).classes('italic theme-muted')
                    else:
                        ui.markdown(text) if not sent else ui.label(text)

        # Scroll to bottom using the specific client context to prevent RuntimeError in background tasks
        self.chat_container.client.run_javascript('window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });')
        return card

    def clear_conversation(self):
        try:
            self.chat_container.clear()
            self.terminal_logs.clear()
            # Next message starts a fresh Antigravity session instead of resuming this one.
            self.agy_conversation_id = None
            self.agy_last_rules_key = None
            # Hide the progress console on a new conversation
            self.progress_container.set_visibility(False)
            if hasattr(self, 'main_tabs') and self.main_tabs:
                self.main_tabs.set_value('chat')
            ui.notify("Conversation cleared. Starting afresh!", type='info')
        except Exception as e:
            ui.notify(f"Error clearing conversation: {e}", type='warning')

    def toggle_reading_focus(self):
        """Hide or restore the header, footer, and studies drawer for reading."""
        self.reading_focus = not self.reading_focus
        if self.reading_focus:
            self._drawer_open_before_focus = bool(self.left_drawer.value)
            self.header.hide()
            self.footer.hide()
            self.left_drawer.hide()
            self.page_column.classes(add="reading-focus")
            self.focus_button.set_icon("fullscreen_exit")
            self.focus_button_tooltip.set_text("Show header, footer, and studies")
            self.focus_button.props["aria-label"] = "Show header, footer, and studies"
            return
        self.header.show()
        self.footer.show()
        if self._drawer_open_before_focus:
            self.left_drawer.show()
        self.page_column.classes(remove="reading-focus")
        self.focus_button.set_icon("fullscreen")
        self.focus_button_tooltip.set_text("Maximise reading view")
        self.focus_button.props["aria-label"] = "Maximise reading view"

    def _install_theme(self):
        """GitHub-style charcoal surfaces and quiet, accessible controls."""
        ui.colors(
            primary="#57606a", secondary="#57606a", accent="#57606a",
            dark="#161b22", dark_page="#0d1117",
            positive="#1a7f37", negative="#cf222e", info="#57606a", warning="#9a6700",
        )
        ui.add_css(
            """
            body {
                --theme-bg: #ffffff;
                --theme-panel: #f6f8fa;
                --theme-inset: #eff2f5;
                --theme-text: #24292f;
                --theme-muted: #57606a;
                --theme-border: #d0d7de;
                --theme-link: #0969da;
                --theme-selection: #ddf4ff;
                background: var(--theme-bg);
                color: var(--theme-text);
            }
            body.body--dark {
                color-scheme: dark;
                --theme-bg: #0d1117;
                --theme-panel: #161b22;
                --theme-inset: #21262d;
                --theme-text: #c9d1d9;
                --theme-muted: #8b949e;
                --theme-border: #30363d;
                --theme-link: #9ecbff;
                --theme-selection: #30363d;
                /* NiceGUI sets these inline; keep them in sync with dark mode. */
                --q-primary: #8b949e !important;
                --q-secondary: #8b949e !important;
                --q-accent: #8b949e !important;
                --q-positive: #3fb950 !important;
                --q-negative: #f85149 !important;
                --q-info: #57606a !important;
                --q-warning: #d29922 !important;
            }
            .q-card, .q-menu, .q-dialog__inner > div, .q-tooltip {
                background: var(--theme-panel);
                color: var(--theme-text);
            }
            .q-header, .q-footer, .q-tab-panel { color: var(--theme-text); }
            .theme-bg { background: var(--theme-bg); }
            .theme-panel { background: var(--theme-panel); }
            .theme-inset { background: var(--theme-inset); }
            .theme-text { color: var(--theme-text); }
            .theme-muted { color: var(--theme-muted); }
            .theme-border { border-color: var(--theme-border); }
            .q-btn.send-button:not(.bg-negative) {
                background: var(--theme-inset);
                color: var(--theme-text);
                border: 1px solid var(--theme-border);
            }
            .q-field__native, .q-field__input, .q-field__prefix, .q-field__suffix {
                color: var(--theme-text);
                caret-color: var(--theme-text);
            }
            .q-field__label, .q-field__marginal { color: var(--theme-muted); }
            .q-field--outlined .q-field__control:before { border-color: var(--theme-border); }
            .q-tree__node-header, .q-tree__node-header .q-tree__node-header-content {
                color: var(--theme-text);
            }
            .q-tree__node--selected > .q-tree__node-header,
            .q-item.q-item--active { background: var(--theme-inset); }
            .q-separator { background: var(--theme-border); }
            ::selection { background: var(--theme-selection); color: var(--theme-text); }
            .nicegui-markdown { color: var(--theme-text); }
            .nicegui-markdown a, .nicegui-markdown a:visited { color: var(--theme-link); }
            .nicegui-markdown h1, .nicegui-markdown h2, .nicegui-markdown hr,
            .nicegui-markdown th, .nicegui-markdown td {
                border-color: var(--theme-border);
            }
            .nicegui-markdown th { background: var(--theme-panel); }
            .nicegui-markdown hr { background: var(--theme-border); }
            .nicegui-markdown tr:nth-child(even) { background: var(--theme-panel); }
            .nicegui-markdown blockquote {
                color: var(--theme-muted);
                border-left: 3px solid var(--theme-border);
            }
            .nicegui-markdown :not(pre) > code {
                background: var(--theme-inset);
                color: inherit;
                border-radius: 4px;
                padding: 0.15em 0.35em;
            }
            .nicegui-markdown pre {
                background: var(--theme-panel);
                color: var(--theme-text);
                border: 1px solid var(--theme-border);
                border-radius: 6px;
                padding: 12px;
                overflow-x: auto;
            }
            """
        )


    def _install_reading_focus_control(self):
        """Floating button: drag to move, click to maximise the reader. Position stays in localStorage."""
        ui.add_css(
            """
            button.reading-focus-btn.q-btn {
                position: fixed;
                z-index: 4500;
                width: 36px;
                height: 36px;
                min-width: 36px;
                min-height: 36px;
                padding: 0;
                right: 28px;
                bottom: 118px;
                border-radius: 9999px;
                background: var(--theme-panel) !important;
                color: var(--theme-text) !important;
                border: 1px solid var(--theme-border);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.35);
                touch-action: none;
                cursor: grab;
                user-select: none;
            }
            button.reading-focus-btn.q-btn .q-icon {
                font-size: 18px;
            }
            button.reading-focus-btn.reading-focus-dragging {
                cursor: grabbing;
            }
            /* Remove both NiceGUI's page gutter and the workspace gutter. */
            .nicegui-content:has(.document-reader),
            .nicegui-content:has(.reading-focus) {
                padding: 0;
                gap: 0;
            }
            .workspace-page:has(.document-reader),
            .reading-focus {
                padding: 0 !important;
                margin: 0;
                gap: 0;
                box-sizing: border-box;
            }
            .workspace-page:has(.document-reader) .q-tab-panels,
            .workspace-page:has(.document-reader) .q-panel,
            .workspace-page:has(.document-reader) .q-tab-panel,
            .reading-focus .q-tab-panels,
            .reading-focus .q-panel,
            .reading-focus .q-tab-panel {
                min-height: inherit;
                box-sizing: border-box;
            }
            .document-reader {
                padding: 8px;
                gap: 8px;
                border: 0;
                border-radius: 0;
                box-shadow: none;
            }
            .document-reader > *,
            .document-reader .nicegui-markdown {
                min-width: 0;
                max-width: 100%;
                overflow-wrap: anywhere;
            }
            .document-reader .nicegui-markdown {
                width: 100%;
                overflow-x: auto;
            }
            """
        )
        ui.add_body_html(
            """
            <script>
            (function () {
                if (window.__tradingGrokReadingFocusBound) return;
                window.__tradingGrokReadingFocusBound = true;
                var STORAGE_KEY = "tradingGrok.readingFocusButton";
                var DRAG_THRESHOLD = 5;

                function clamp(value, min, max) {
                    return Math.max(min, Math.min(max, value));
                }

                function readSaved() {
                    try {
                        var parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null");
                        if (!parsed || !Number.isFinite(parsed.left) || !Number.isFinite(parsed.top)) return null;
                        return parsed;
                    } catch (err) {
                        return null;
                    }
                }

                function save(pos) {
                    try {
                        localStorage.setItem(STORAGE_KEY, JSON.stringify({
                            left: Math.round(pos.left),
                            top: Math.round(pos.top)
                        }));
                    } catch (err) {}
                }

                function place(btn, left, top) {
                    var maxLeft = Math.max(8, window.innerWidth - btn.offsetWidth - 8);
                    var maxTop = Math.max(8, window.innerHeight - btn.offsetHeight - 8);
                    left = clamp(left, 8, maxLeft);
                    top = clamp(top, 8, maxTop);
                    btn.style.left = left + "px";
                    btn.style.top = top + "px";
                    btn.style.right = "auto";
                    btn.style.bottom = "auto";
                    return {left: left, top: top};
                }

                function defaultPosition(btn) {
                    var footer = document.querySelector(".q-footer");
                    var footerTop = window.innerHeight - 96;
                    if (footer) {
                        var rect = footer.getBoundingClientRect();
                        if (rect.height > 8 && rect.top > 0) footerTop = rect.top;
                    }
                    return {
                        left: window.innerWidth - btn.offsetWidth - 28,
                        top: footerTop - btn.offsetHeight - 16
                    };
                }

                function init(btn) {
                    if (btn.dataset.dragBound === "1") return;
                    if (!btn.offsetWidth) {
                        var tries = Number(btn.dataset.dragTries || "0") + 1;
                        btn.dataset.dragTries = String(tries);
                        if (tries < 40) requestAnimationFrame(function () { init(btn); });
                        return;
                    }
                    btn.dataset.dragBound = "1";
                    var saved = readSaved();
                    var initial = saved || defaultPosition(btn);
                    place(btn, initial.left, initial.top);
                    var userPlaced = !!saved;
                    var dragging = false;
                    var moved = false;
                    var offsetX = 0;
                    var offsetY = 0;
                    var startLeft = 0;
                    var startTop = 0;

                    btn.addEventListener("pointerdown", function (event) {
                        if (event.button !== undefined && event.button !== 0) return;
                        dragging = true;
                        moved = false;
                        var rect = btn.getBoundingClientRect();
                        offsetX = event.clientX - rect.left;
                        offsetY = event.clientY - rect.top;
                        startLeft = rect.left;
                        startTop = rect.top;
                        btn.classList.add("reading-focus-dragging");
                        if (btn.setPointerCapture) btn.setPointerCapture(event.pointerId);
                    });

                    btn.addEventListener("pointermove", function (event) {
                        if (!dragging) return;
                        var left = event.clientX - offsetX;
                        var top = event.clientY - offsetY;
                        if (Math.abs(left - startLeft) > DRAG_THRESHOLD || Math.abs(top - startTop) > DRAG_THRESHOLD) {
                            moved = true;
                        }
                        if (moved) place(btn, left, top);
                    });

                    function endDrag(event) {
                        if (!dragging) return;
                        dragging = false;
                        btn.classList.remove("reading-focus-dragging");
                        var rect = btn.getBoundingClientRect();
                        var pos = place(btn, rect.left, rect.top);
                        if (moved) {
                            userPlaced = true;
                            save(pos);
                            btn.dataset.suppressClick = "1";
                        }
                        if (event && btn.releasePointerCapture) {
                            try { btn.releasePointerCapture(event.pointerId); } catch (err) {}
                        }
                    }

                    btn.addEventListener("pointerup", endDrag);
                    btn.addEventListener("pointercancel", endDrag);
                    btn.addEventListener("click", function (event) {
                        if (btn.dataset.suppressClick !== "1") return;
                        btn.dataset.suppressClick = "0";
                        event.preventDefault();
                        event.stopPropagation();
                        event.stopImmediatePropagation();
                    }, true);
                    window.addEventListener("resize", function () {
                        var rect = btn.getBoundingClientRect();
                        var pos = place(btn, rect.left, rect.top);
                        if (userPlaced) save(pos);
                    });
                    if (!saved) {
                        setTimeout(function () {
                            if (userPlaced || dragging) return;
                            var again = defaultPosition(btn);
                            place(btn, again.left, again.top);
                        }, 400);
                    }
                }

                function scan() {
                    var buttons = document.querySelectorAll(".reading-focus-btn");
                    for (var i = 0; i < buttons.length; i++) init(buttons[i]);
                }

                var observer = new MutationObserver(scan);
                function boot() {
                    if (!document.body) return;
                    observer.observe(document.body, {childList: true, subtree: true});
                    scan();
                }
                if (document.body) boot();
                else document.addEventListener("DOMContentLoaded", boot);
            })();
            </script>
            """
        )

    def build_ui(self):
        # Premium dark mode configuration (Default to Dark)
        dark = ui.dark_mode(value=True)
        self._install_theme()
        self._install_reading_focus_control()

        # ---------------------------------------------------------
        # Header Area
        # ---------------------------------------------------------
        with ui.header().classes('theme-panel border-b theme-border p-4 justify-between items-center fixed top-0 left-0 right-0 z-10 backdrop-blur-md') as self.header:
            with ui.row().classes('items-center gap-3'):
                ui.button(icon='menu', on_click=lambda: self.left_drawer.toggle()).props('flat round').classes('theme-text')
                ui.icon('menu_book', size='md').classes('theme-muted')
                ui.label('BibleMate Antigravity').classes('max-sm:hidden text-lg font-bold tracking-wide theme-text')

            with ui.row().classes('items-center gap-4'):
                # New Conversation button
                with ui.button(icon='add', on_click=self.clear_conversation).props('flat round').classes('theme-text'):
                    ui.tooltip('New Conversation')

                # Tabs Menu inside header to maximize content space
                with ui.tabs().props('dense shrink active-color=primary indicator-color=primary').classes('theme-text') as self.main_tabs:
                    with ui.tab('chat', label='', icon='chat'):
                        ui.tooltip('Chat Workspace')
                    with ui.tab('reader', label='', icon='menu_book'):
                        ui.tooltip('Document Reader')

                # Settings toggle button
                ui.button(icon='settings', on_click=lambda: self.right_drawer.toggle()).props('flat round').classes('theme-text')

        # ---------------------------------------------------------
        # Left Drawer (Collapsible File Tree)
        # ---------------------------------------------------------
        with ui.left_drawer(value=False).classes('theme-bg border-r theme-border p-4') as self.left_drawer:
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('Saved Studies').classes('text-md font-bold theme-text')
                with ui.row().classes('items-center gap-1'):
                    self.delete_button = ui.button(icon='delete', on_click=self.confirm_delete).props('flat round size=sm color=negative').classes('text-negative')
                    self.delete_button.set_visibility(False)
                    with self.delete_button:
                        ui.tooltip('Delete Item')

                    self.export_button = ui.button(icon='file_download', on_click=self.export_to_docx).props('flat round size=sm color=primary').classes('theme-muted')
                    self.export_button.set_visibility(False)
                    with self.export_button:
                        ui.tooltip('Export to DOCX')

                    self.edit_button = ui.button(icon='edit', on_click=self.start_edit).props('flat round size=sm color=positive').classes('text-positive')
                    self.edit_button.set_visibility(False)
                    with self.edit_button:
                        ui.tooltip('Edit Markdown File')

                    self.add_file_button = ui.button(icon='note_add', on_click=lambda: self.prompt_create_item(is_folder=False)).props('flat round size=sm color=primary').classes('theme-muted')
                    self.add_file_button.set_visibility(False)
                    with self.add_file_button:
                        ui.tooltip('Add File')

                    self.add_folder_button = ui.button(icon='create_new_folder', on_click=lambda: self.prompt_create_item(is_folder=True)).props('flat round size=sm color=primary').classes('theme-muted')
                    self.add_folder_button.set_visibility(False)
                    with self.add_folder_button:
                        ui.tooltip('Add Folder')

                    ui.button(icon='refresh', on_click=self.refresh_file_tree).props('flat round size=sm').classes('theme-muted')

            # Dynamic Container
            self.file_tree = ui.column().classes('w-full')
            self.refresh_file_tree()

        # ---------------------------------------------------------
        # Right Drawer (Settings Panel)
        # ---------------------------------------------------------
        with ui.right_drawer(value=False).classes('theme-bg border-l theme-border p-6') as self.right_drawer:
            ui.label('Agent Options').classes('text-lg font-bold theme-text mb-6')

            # Dark/Light Mode switch
            ui.label('Appearance').classes('text-xs font-semibold theme-muted uppercase tracking-wider mb-2')
            ui.switch('Dark Mode').bind_value(dark).classes('mb-6')

            # Model Selection
            ui.label('AI Model').classes('text-xs font-semibold theme-muted uppercase tracking-wider')
            model_drop = ui.select(list(MODELS_MAP.keys()), value=self.selected_model).classes('w-full mb-6')
            model_drop.bind_value_to(self, 'selected_model')

            # Persona Selection
            ui.label('Active Persona').classes('text-xs font-semibold theme-muted uppercase tracking-wider')
            persona_drop = ui.select(list(PERSONAS_MAP.keys()), value=self.selected_persona).classes('w-full mb-6')
            persona_drop.bind_value_to(self, 'selected_persona')

            # Skill Selection
            ui.label('Enforced Skill').classes('text-xs font-semibold theme-muted uppercase tracking-wider')
            skill_drop = ui.select(SKILLS_LIST, value=self.selected_skill).classes('w-full mb-6')
            skill_drop.bind_value_to(self, 'selected_skill')

            ui.markdown('---').classes('my-4')
            ui.label('Backend: Antigravity CLI (`agy`)').classes('text-xs font-bold text-positive tracking-wide uppercase')
            ui.label('Uses your signed-in Google subscription. No Gemini API key required.').classes('text-xs theme-muted mt-1')
            ui.label('Auto-Approval: ENABLED').classes('text-xs font-bold text-positive tracking-wide uppercase mt-3')

        # ---------------------------------------------------------
        # Main Layout Structure
        # ---------------------------------------------------------
        # Quasar accounts for the actual header/footer heights, including mobile wrapping.
        with ui.element("q-page").props(
            ':style-fn="offset => ({ minHeight: \'calc(100dvh - \' + offset + \'px)\' })"'
        ).classes("workspace-page w-full flex flex-col gap-4 pt-4 pb-32 px-4 md:px-6") as self.page_column:
            # Tab Content
            with ui.tab_panels(self.main_tabs, value='chat').classes('w-full bg-transparent flex-grow'):

                # Chat tab
                with ui.tab_panel('chat').classes('w-full p-0 bg-transparent flex flex-col'):
                    self.chat_container = ui.column().classes('w-full flex-grow mb-6')

                    # Collapsible agent execution logger console (hidden by default, shown only when agent is active)
                    with ui.column().classes('w-full mb-6 transition-all duration-300') as self.progress_container:
                        self.progress_container.set_visibility(False)
                        with ui.card().classes('w-full border theme-border theme-panel p-4 rounded-xl shadow-inner'):
                            with ui.row().classes('w-full items-center gap-2 mb-2'):
                                ui.spinner(size='sm', color='primary')
                                ui.label('Antigravity Running - Live Execution Pipeline').classes('text-xs font-bold theme-muted tracking-wide uppercase')

                            # Thinking monologue
                            with ui.expansion('Agent Thinking Monologue', icon='psychology').classes('w-full border theme-border rounded-lg mb-2 theme-bg'):
                                self.thinking_display = ui.markdown().classes('text-xs theme-text p-2 font-mono overflow-auto max-h-60')

                            # Running Tool
                            with ui.expansion('Currently Executed Tool/Skill', icon='construction').classes('w-full border theme-border rounded-lg mb-2 theme-bg'):
                                self.tool_display = ui.markdown().classes('text-xs theme-text p-2 font-mono')
                                self.tool_output_display = ui.markdown().classes('text-xs theme-muted p-2 theme-panel rounded font-mono overflow-auto max-h-48')

                            # Raw standard logger updates
                            with ui.expansion('System Logs (Stdout/Logger)', icon='terminal').classes('w-full border theme-border rounded-lg theme-bg'):
                                self.terminal_display = ui.markdown().classes('text-xs theme-text p-2 theme-bg rounded font-mono overflow-auto max-h-48')

                # Reader tab
                with ui.tab_panel('reader').classes('document-reader w-full theme-bg'):
                    self.reader_title = ui.label('No File Selected').classes('text-xl font-bold theme-text border-b theme-border pb-2 mb-4')
                    self.reader_container = ui.column().classes('w-full')
                    with self.reader_container:
                        self.reader_content = ui.markdown('Select a file from the left sidebar tree to view it. New exegesis results are written directly to `biblemate/` and `export/`, and images to `images/`.').classes('theme-text')

        # ---------------------------------------------------------
        # Footer Area (Multiline Input Chat Bar)
        # ---------------------------------------------------------
        with ui.footer().classes('theme-panel border-t theme-border p-4 fixed bottom-0 left-0 right-0 z-10 backdrop-blur-md') as self.footer:
            with ui.column().classes('w-full gap-1'):
                with ui.row().classes('w-full items-end gap-3'):
                    # Wrapper column for message input & autocomplete menu
                    with ui.column().classes('flex-grow relative'):
                        autocomplete_menu = None

                        def select_command(cmd: str):
                            message_input.value = cmd + ' '
                            if autocomplete_menu:
                                autocomplete_menu.close()
                            message_input.run_method('focus')

                        def handle_input_change(e):
                            val = e.value or ""
                            if self.selected_skill == 'Auto' and val.startswith('/') and ' ' not in val:
                                matches = [cmd for cmd in self.slash_commands if cmd.lower().startswith(val.lower())]
                                if matches and autocomplete_menu:
                                    autocomplete_menu.clear()
                                    with autocomplete_menu:
                                        for cmd in matches:
                                            ui.menu_item(cmd, on_click=lambda c=cmd: select_command(c)).classes('text-xs font-mono py-1 px-3')
                                    autocomplete_menu.open()
                                elif autocomplete_menu:
                                    autocomplete_menu.close()
                            elif autocomplete_menu:
                                autocomplete_menu.close()

                        # Multi-line textarea for entry requests
                        message_input = ui.textarea(
                            label='Ask BibleMate Antigravity',
                            placeholder='Enter your study request (e.g., Write a devotion on Romans 8:28)...',
                            on_change=handle_input_change
                        ).props('outlined autogrow rows=2 input-class="theme-text"').classes('w-full rounded-xl theme-text')

                        autocomplete_menu = ui.menu().props('fit no-parent-event no-focus no-refocus anchor="top left" self="bottom left"').classes('max-h-60 overflow-y-auto')

                    # Inline async sender bound to Client context to avoid RuntimeError
                    async def on_send_click():
                        await self.handle_send(message_input)

                    # Bind Control+S and Command+S keyboard shortcuts to send the request
                    message_input.on('keydown.ctrl.s.prevent', on_send_click)
                    message_input.on('keydown.meta.s.prevent', on_send_click)

                    # Send Button
                    with ui.button(icon='send', color=None, on_click=on_send_click).props('round size=lg').classes('send-button shadow-md hover:scale-105 transition-transform mb-1') as self.action_button:
                        self.action_button_tooltip = ui.tooltip('Send Request')

        self.focus_button = ui.button(
            icon="fullscreen",
            color=None,
            on_click=self.toggle_reading_focus,
        ).props(
            'round dense :ripple=false type=button aria-label="Maximise reading view"'
        ).classes("reading-focus-btn")
        with self.focus_button:
            self.focus_button_tooltip = ui.tooltip("Maximise reading view")

    async def handle_send(self, message_input):
        if self.active_agent_running:
            await self.handle_stop()
            return

        query = message_input.value.strip()
        if not query:
            return
        # Clear text entry field
        message_input.value = ''
        if hasattr(self, 'main_tabs') and self.main_tabs:
            self.main_tabs.set_value('chat')
        await self.execute_agent_chat(query)

if __name__ == '__main__':
    # Initialize application UI
    app_instance = BibleMateApp()
    app_instance.build_ui()

    # Setup logging interceptor after uvicorn initializes on server startup to capture the active event loop
    app.on_startup(lambda: app_instance.setup_logging_interceptor())

    # 33381 keeps this app from colliding with web_app_gemini_api_key.py (33380), web_app_claude.py (33382), and web_app_codex.py (33383), and web_app_grok.py (33384).
    port = int(os.environ.get('BIBLEMATE_AGY_PORT', '33381'))
    print(f"BibleMate Antigravity uses your signed-in Google subscription via Antigravity CLI (no API key required).")
    print(f"Open http://localhost:{port}")
    ui.run(
        title='BibleMate Antigravity',
        port=port,
        reload=False,  # Disable reload for background execution safety
        show=False     # Do not open a browser window automatically on server start
    )
