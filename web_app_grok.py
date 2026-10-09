#!/usr/bin/env python3
"""BibleMate web app backed by the signed-in Grok Build CLI.

Sibling of web_app.py. The layout and workspace tools are the same.
The agent backend is `grok` headless mode, which reuses the session in
~/.grok/auth.json from `grok login`. No separate xAI API key is required.
"""
import os
import sys
import re
import json
import asyncio
import shutil
import signal
import tempfile
from nicegui import ui, app

# Reuse the Grok Build install the user is already signed into.
GROK_BIN = shutil.which("grok") or os.path.expanduser("~/.grok/bin/grok")
if not GROK_BIN or not os.path.isfile(GROK_BIN) or not os.access(GROK_BIN, os.X_OK):
    print("Error: the grok CLI was not found.")
    print("Install Grok Build, then sign in once with: grok login")
    print("Expected the `grok` executable on PATH or at ~/.grok/bin/grok.")
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
    """Parses .grok/agents.md to extract all available personas and descriptions."""
    path = '.grok/agents.md'
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
    """Dynamically lists the available exegesis skills from .grok/skills/."""
    skills = ['Auto']
    skills_dir = '.grok/skills'
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

# Dropdown labels to Grok Build model ids (`grok models`).
# These run on the signed-in grok.com subscription, not an API key.
MODELS_MAP = {
    'Grok 4.7': 'grok-4.7',
    'Grok 4.7 Build Fast': 'grok-4.7-build-fast',
    'Grok 4.6': 'grok-4.6',
    'Grok 4.5': 'grok-4.5',
}
DEFAULT_MODEL = 'Grok 4.7'

# Regex to match scripture references (e.g. John 3:16, 1 Cor 13, Romans 8:28, 1Tim 3:16)
BIBLE_REF_PATTERN = re.compile(
    r'^\s*([1-3]\s*)?[A-Za-z\s\.\_]+?\s+\d+(\s*:\s*\d+(\s*-\s*\d+)?)?\s*$',
    re.IGNORECASE
)

async def run_local_retriever(skill_name: str, query: str, on_process=None) -> str:
    """Runs a Python database retriever script under .grok/skills directly and returns output."""
    script_path = f".grok/skills/{skill_name}/{skill_name}_retriever.py"
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
        # /image stays on Grok so it can use image_gen. There is no local retriever for it.
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
# Grok stream helpers
# ---------------------------------------------------------

def parse_grok_stream_line(line: str):
    """Parse one stdout line from `grok --output-format streaming-json`."""
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
    """Pick the most useful field from a Grok tool-call payload."""
    if isinstance(raw_input, str):
        return raw_input
    if not isinstance(raw_input, dict):
        return ""
    for key in (
        "command", "cmd", "target_file", "file_path", "path",
        "pattern", "query", "url", "prompt", "script_path",
    ):
        value = raw_input.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    try:
        return json.dumps(raw_input, ensure_ascii=False)
    except Exception:
        return str(raw_input)


def clip_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n… (truncated)"


def markdown_fence(text: str) -> str:
    """Wrap text in a fence that the payload cannot close early."""
    safe = text.replace("```", "'''")
    return f"```\n{safe}\n```"


# ---------------------------------------------------------
# NiceGUI Web Application State & Layout
# ---------------------------------------------------------

class BibleMateApp:
    def __init__(self):
        # Settings state
        self.selected_model = DEFAULT_MODEL
        self.selected_persona = 'Auto'
        self.selected_skill = 'Auto'
        # Headless Grok session for this browser conversation. Empty means a new session.
        self.grok_session_id = None
        self.grok_proc = None
        
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
        self.terminal_logs = []
        self.active_agent_running = False
        self.running_chat_task = None
        
        # Slash commands auto-discovery
        self.slash_commands = self.get_slash_commands()
        
        # Log Hook Registration
        self.setup_logging_interceptor()

    def get_slash_commands(self) -> list:
        """Lists slash commands from .grok/commands and .grok/skills."""
        commands = set()
        commands_dir = '.grok/commands'
        if os.path.isdir(commands_dir):
            try:
                for name in os.listdir(commands_dir):
                    if name.endswith('.md'):
                        commands.add('/' + name[:-3])
            except Exception:
                pass
        skills_dir = '.grok/skills'
        if os.path.isdir(skills_dir):
            try:
                for name in os.listdir(skills_dir):
                    if os.path.isdir(os.path.join(skills_dir, name)):
                        commands.add('/' + name)
            except Exception:
                pass
        return sorted(commands, key=str.lower)

    def setup_logging_interceptor(self):
        """Remember the server loop. Grok progress is read from the CLI stream."""
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
        """Match a slash-command token to a .grok skill directory name."""
        if not token:
            return None
        wanted = token.lower()
        for skill in SKILLS_LIST:
            if skill.lower() == wanted:
                return skill
        return None

    def build_system_rules(self, active_skill: str) -> str:
        """Rules passed to `grok --rules` on top of AGENTS.md."""
        rules = (
            "You are BibleMate AI running inside the local BibleMate web app, "
            "backed by Grok Build. Follow AGENTS.md and the skills under .grok/skills/. "
            "Use the signed-in Grok tools (read_file, write, run_terminal_command, image_gen, and the rest). "
            "Do not call Google Antigravity or any .agents/ script."
        )
        if self.selected_persona != 'Auto':
            persona = PERSONAS_MAP.get(self.selected_persona, '')
            if persona:
                rules += f"\n\nAdopt the following persona instructions:\n{persona}"
        else:
            rules += (
                "\nYou have access to specialized personas listed in .grok/agents.md. "
                "Rotate them dynamically depending on the research phase."
            )

        if active_skill != 'Auto':
            rules += (
                f"\n\nCRITICAL TASK REQUIREMENT: You MUST use the local BibleMate skill "
                f"'{active_skill}'. Read `.grok/skills/{active_skill}/SKILL.md` and follow it "
                "before you answer. Do not answer scripture from memory. Retrieve verses with "
                "`python3 .grok/skills/bible/bible_retriever.py`."
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
            "\n- Save generated images with `.grok/skills/image/image_placer.py` into `images/`."
            "\n- NEVER tell the user a file has been saved unless you have actually written it to"
            " one of these workspace directories in this session."
            "\n- Do NOT write files to any artifact, brain, or temporary directory outside the workspace."
        )
        return rules

    def apply_grok_event(self, event: dict, state: dict, response_card):
        """Update the chat bubble and the live progress panels from one stream event."""
        etype = event.get("type")

        if etype == "text":
            chunk = event.get("data") or ""
            if chunk:
                state["text"] += chunk
                self._render_response(response_card, state["text"])
            return

        if etype == "thought":
            chunk = event.get("data") or ""
            if not chunk:
                return
            state["thinking"] = clip_text(state["thinking"] + chunk, 8000)
            self._set_markdown(self.thinking_display, state["thinking"])
            if not state["notified_think"]:
                state["notified_think"] = True
                snippet = chunk.strip().splitlines()[0] if chunk.strip() else "reasoning"
                if len(snippet) > 50:
                    snippet = snippet[:50] + "..."
                self._notify_progress(f"Grok thinking: {snippet}")
            return

        if etype == "tool_call":
            tool_name = event.get("toolName") or event.get("title") or "tool"
            detail = summarize_tool_input(event.get("rawInput"))
            shown = detail or tool_name
            self._set_markdown(
                self.tool_display,
                f"**Executing:** `{tool_name}`" + (f"\n\n`{clip_text(shown, 500)}`" if detail else ""),
            )
            display_cmd = shown.replace('python3 .grok/skills/', '').replace('python3 .agents/skills/', '')
            if len(display_cmd) > 50:
                display_cmd = display_cmd[:50] + "..."
            self._notify_progress(f"Grok executing: {display_cmd}")
            self.append_runtime_log(f"tool {tool_name}: {clip_text(shown, 300)}")
            return

        if etype == "tool_call_update":
            raw_output = event.get("rawOutput")
            if raw_output in (None, "", [], {}):
                content = event.get("content")
                if content:
                    raw_output = content
            if raw_output in (None, "", [], {}):
                return
            if not isinstance(raw_output, str):
                try:
                    raw_output = json.dumps(raw_output, ensure_ascii=False, indent=2)
                except Exception:
                    raw_output = str(raw_output)
            self._set_markdown(self.tool_output_display, markdown_fence(clip_text(raw_output, 4000)))
            return

        if etype == "error":
            message = event.get("message") or "Grok reported an error."
            state["error"] = message
            self.append_runtime_log(f"error: {message}")
            if event.get("sessionId"):
                self.grok_session_id = event["sessionId"]
            return

        if etype == "end":
            if event.get("sessionId"):
                self.grok_session_id = event["sessionId"]
            reason = event.get("stopReason") or ""
            turns = event.get("num_turns")
            bits = ["grok finished"]
            if reason:
                bits.append(reason)
            if turns is not None:
                bits.append(f"turns={turns}")
            self.append_runtime_log(" ".join(bits))
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

    async def _stop_grok_proc(self, proc=None):
        """Stop the headless grok process group started for the current turn."""
        if proc is None:
            proc = self.grok_proc
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
                        ui.markdown(content).classes('text-slate-700 dark:text-slate-300')
                    elif is_image:
                        web_path = f"/{node_id}"
                        ui.image(web_path).classes('w-full max-w-2xl mx-auto rounded-lg shadow-lg border border-slate-200 dark:border-slate-800')
                
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
            ui.label('Confirm Deletion').classes('text-lg font-bold text-slate-900 dark:text-white mb-2')
            ui.label(f'Are you sure you want to permanently delete the {item_type} "{os.path.basename(node_id)}"? This action cannot be undone.').classes('text-sm text-slate-600 dark:text-slate-400 mb-6')
            with ui.row().classes('w-full justify-end gap-3'):
                ui.button('Cancel', on_click=dialog.close).props('flat')
                ui.button('Delete', color='red', on_click=lambda: self.perform_delete(node_id, dialog)).props('elevated')
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
                import shutil
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
                    ui.markdown('Select a file from the left sidebar tree to view it. New exegesis results are written directly to `biblemate/` and `export/`, and images to `images/`.').classes('text-slate-700 dark:text-slate-300')
            
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
                ).props('outlined autogrow input-class="font-mono text-slate-900 dark:text-slate-100"').classes('w-full min-h-[400px] mb-4 text-slate-900 dark:text-slate-100')
                
                with ui.row().classes('w-full gap-4'):
                    ui.button('Save', icon='save', color='green', on_click=lambda: self.save_edit(node_id, editor.value)).props('elevated')
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
            ui.label(f'Inside: {parent_dir}').classes('text-xs text-slate-500 mb-4')
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
                self.action_button.props('icon=stop color=red', remove='icon=send color=indigo')
                self.action_button_tooltip.set_text('Stop Execution')
            else:
                self.action_button.props('icon=send color=indigo', remove='icon=stop color=red')
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
        """Answer lookup commands from the local SQLite retrievers, without calling Grok."""
        self._notify_progress(f"Local retriever: {skill_name}")
        self._set_markdown(
            self.thinking_display,
            f"Running the local `{skill_name}` database. This request does not call Grok.",
        )
        script = f"python3 .grok/skills/{skill_name}/{skill_name}_retriever.py"
        self._set_markdown(self.tool_display, f"**Executing:** `{script}`")
        if not args.strip():
            text = f"Add a query after `/{skill_name}`."
        else:
            text = await run_local_retriever(
                skill_name,
                args.strip(),
                on_process=lambda process: setattr(self, 'grok_proc', process),
            )
        self._set_markdown(self.tool_output_display, markdown_fence(clip_text(text or "(no output)", 4000)))
        self._render_response(response_card, text or "(no output)")

    async def run_grok_turn(self, user_query: str, response_card):
        """Run one headless `grok` turn on the signed-in subscription and stream it into the UI."""
        active_skill = self.active_skill_for_query(user_query)
        system_rules = self.build_system_rules(active_skill)
        sdk_model = MODELS_MAP.get(self.selected_model, MODELS_MAP[DEFAULT_MODEL])

        prompt_path = None
        stderr_task = None
        state = {"text": "", "thinking": "", "notified_think": False, "error": ""}
        try:
            fd, prompt_path = tempfile.mkstemp(prefix="biblemate-grok-", suffix=".txt")
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(user_query)

            cmd = [
                GROK_BIN,
                "--prompt-file", prompt_path,
                "-m", sdk_model,
                "--cwd", WORKSPACE_DIR,
                "--output-format", "streaming-json",
                "--always-approve",
                "--no-auto-update",
                "--no-plan",
                "--rules", system_rules,
            ]
            if self.grok_session_id:
                cmd.extend(["--resume", self.grok_session_id])

            env = os.environ.copy()
            env["GROK_DISABLE_AUTOUPDATER"] = "1"
            # Do not inject an API key. A signed-in `grok login` session wins over
            # XAI_API_KEY when both exist, and this app is meant to use that session.

            self.append_runtime_log(f"starting grok model={sdk_model} resume={bool(self.grok_session_id)}")
            self._notify_progress("Grok: Planning study...")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=WORKSPACE_DIR,
                env=env,
                start_new_session=True,
            )
            self.grok_proc = process
            stderr_task = asyncio.create_task(self._drain_stderr(process))

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                event = parse_grok_stream_line(line.decode("utf-8", errors="replace"))
                if event:
                    self.apply_grok_event(event, state, response_card)

            returncode = await process.wait()
            if stderr_task is not None:
                await stderr_task
                stderr_task = None

            if state["error"] and not state["text"]:
                self._render_response(response_card, f"**Grok error:** {state['error']}")
            elif returncode not in (0, None) and not state["text"]:
                self._render_response(
                    response_card,
                    f"**Grok exited with code {returncode}.** See System Logs for details.",
                )
            elif not state["text"]:
                self._render_response(response_card, "Grok finished without a text reply. See System Logs.")
        finally:
            if stderr_task is not None and not stderr_task.done():
                stderr_task.cancel()
                try:
                    await stderr_task
                except asyncio.CancelledError:
                    pass
            proc = self.grok_proc
            if proc is not None and proc.returncode is None:
                try:
                    await asyncio.shield(self._stop_grok_proc(proc))
                except Exception:
                    pass
            self.grok_proc = None
            if prompt_path:
                try:
                    os.remove(prompt_path)
                except OSError:
                    pass

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
            self._notify_progress("Grok: Initializing workspace...")
            self.progress_container.set_visibility(True)
            self.thinking_display.set_content("*Analyzing query...*")
            self.tool_display.set_content("**Awaiting agent action...**")
            self.tool_output_display.set_content("")
            response_card = self.add_chat_bubble("Preparing Grok and BibleMate skills...", sent=False, italic=True)

            direct_skill, direct_args = parse_direct_command(user_query)
            if direct_skill:
                await self.run_direct_retriever(direct_skill, direct_args or "", response_card)
            else:
                await self.run_grok_turn(user_query, response_card)
        except asyncio.CancelledError:
            proc = self.grok_proc
            try:
                await asyncio.shield(self._stop_grok_proc(proc))
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
                        ui.label(f"Execution Error: {str(e)}").classes('text-rose-400 font-semibold')
                else:
                    self.add_chat_bubble(f"Execution Error: {str(e)}", sent=False)
            except RuntimeError:
                pass
        finally:
            self.active_agent_running = False
            self.grok_proc = None
            self.update_action_button(to_stop=False)
            try:
                self.progress_container.set_visibility(False)
                ui.notify("System Ready", group='agent_progress', type='positive', timeout=2000)
                self.refresh_file_tree()
            except RuntimeError:
                pass

    def add_chat_bubble(self, text: str, sent: bool, italic: bool = False):
        align_class = "justify-end" if sent else "justify-start"
        bubble_bg = "bg-indigo-600/90 text-white" if sent else "bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-slate-700/50"
        border_radius = "rounded-l-2xl rounded-tr-2xl" if sent else "rounded-r-2xl rounded-tl-2xl"
        card_width = "max-w-[85%] md:max-w-[75%]" if sent else "w-full"
        
        with self.chat_container:
            with ui.row().classes(f'w-full {align_class} mb-4 items-end animate-fade-in'):
                with ui.card().classes(f'{card_width} p-4 shadow-md backdrop-blur-sm {bubble_bg} {border_radius}') as card:
                    if italic:
                        ui.label(text).classes('italic text-slate-500 dark:text-slate-400')
                    else:
                        ui.markdown(text) if not sent else ui.label(text)
        
        # Scroll to bottom using the specific client context to prevent RuntimeError in background tasks
        self.chat_container.client.run_javascript('window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });')
        return card

    def clear_conversation(self):
        try:
            self.chat_container.clear()
            self.terminal_logs.clear()
            # Next message starts a fresh Grok session instead of resuming this one.
            self.grok_session_id = None
            # Hide the progress console on a new conversation
            self.progress_container.set_visibility(False)
            if hasattr(self, 'main_tabs') and self.main_tabs:
                self.main_tabs.set_value('chat')
            ui.notify("Conversation cleared. Starting afresh!", type='info')
        except Exception as e:
            ui.notify(f"Error clearing conversation: {e}", type='warning')

    def build_ui(self):
        # Premium dark mode configuration (Default to Dark)
        dark = ui.dark_mode(value=True)

        # ---------------------------------------------------------
        # Header Area
        # ---------------------------------------------------------
        with ui.header().classes('bg-slate-100/90 dark:bg-slate-900/90 border-b border-slate-200 dark:border-slate-800 p-4 justify-between items-center fixed top-0 left-0 right-0 z-10 backdrop-blur-md'):
            with ui.row().classes('items-center gap-3'):
                ui.button(icon='menu', on_click=lambda: self.left_drawer.toggle()).props('flat round').classes('text-slate-700 dark:text-slate-200')
                ui.icon('menu_book', size='md').classes('text-indigo-600 dark:text-indigo-400')
                ui.label('BibleMate Grok').classes('text-lg font-bold tracking-wide text-slate-900 dark:text-white')
            
            with ui.row().classes('items-center gap-4'):
                # New Conversation button
                with ui.button(icon='add', on_click=self.clear_conversation).props('flat round').classes('text-slate-700 dark:text-slate-200'):
                    ui.tooltip('New Conversation')
                
                # Tabs Menu inside header to maximize content space
                with ui.tabs().props('dense shrink active-color=indigo indicator-color=indigo').classes('text-slate-700 dark:text-slate-200') as self.main_tabs:
                    with ui.tab('chat', label='', icon='chat'):
                        ui.tooltip('Chat Workspace')
                    with ui.tab('reader', label='', icon='menu_book'):
                        ui.tooltip('Document Reader')
                
                # Settings toggle button
                ui.button(icon='settings', on_click=lambda: self.right_drawer.toggle()).props('flat round').classes('text-slate-700 dark:text-slate-200')

        # ---------------------------------------------------------
        # Left Drawer (Collapsible File Tree)
        # ---------------------------------------------------------
        with ui.left_drawer(value=False).classes('bg-slate-50 dark:bg-slate-950 border-r border-slate-200 dark:border-slate-900 p-4') as self.left_drawer:
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('Saved Studies').classes('text-md font-bold text-slate-800 dark:text-slate-200')
                with ui.row().classes('items-center gap-1'):
                    self.delete_button = ui.button(icon='delete', on_click=self.confirm_delete).props('flat round size=sm color=red').classes('text-rose-500')
                    self.delete_button.set_visibility(False)
                    with self.delete_button:
                        ui.tooltip('Delete Item')
                    
                    self.export_button = ui.button(icon='file_download', on_click=self.export_to_docx).props('flat round size=sm color=indigo').classes('text-indigo-500')
                    self.export_button.set_visibility(False)
                    with self.export_button:
                        ui.tooltip('Export to DOCX')
                        
                    self.edit_button = ui.button(icon='edit', on_click=self.start_edit).props('flat round size=sm color=green').classes('text-emerald-500')
                    self.edit_button.set_visibility(False)
                    with self.edit_button:
                        ui.tooltip('Edit Markdown File')
                        
                    self.add_file_button = ui.button(icon='note_add', on_click=lambda: self.prompt_create_item(is_folder=False)).props('flat round size=sm color=indigo').classes('text-indigo-500')
                    self.add_file_button.set_visibility(False)
                    with self.add_file_button:
                        ui.tooltip('Add File')
                        
                    self.add_folder_button = ui.button(icon='create_new_folder', on_click=lambda: self.prompt_create_item(is_folder=True)).props('flat round size=sm color=indigo').classes('text-indigo-500')
                    self.add_folder_button.set_visibility(False)
                    with self.add_folder_button:
                        ui.tooltip('Add Folder')
                        
                    ui.button(icon='refresh', on_click=self.refresh_file_tree).props('flat round size=sm').classes('text-slate-600 dark:text-slate-400')
            
            # Dynamic Container
            self.file_tree = ui.column().classes('w-full')
            self.refresh_file_tree()

        # ---------------------------------------------------------
        # Right Drawer (Settings Panel)
        # ---------------------------------------------------------
        with ui.right_drawer(value=False).classes('bg-slate-50 dark:bg-slate-950 border-l border-slate-200 dark:border-slate-900 p-6') as self.right_drawer:
            ui.label('Agent Options').classes('text-lg font-bold text-slate-800 dark:text-slate-200 mb-6')
            
            # Dark/Light Mode switch
            ui.label('Appearance').classes('text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2')
            ui.switch('Dark Mode').bind_value(dark).classes('mb-6')
            
            # Model Selection
            ui.label('AI Model').classes('text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider')
            model_drop = ui.select(list(MODELS_MAP.keys()), value=self.selected_model).classes('w-full mb-6')
            model_drop.bind_value_to(self, 'selected_model')
            
            # Persona Selection
            ui.label('Active Persona').classes('text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider')
            persona_drop = ui.select(list(PERSONAS_MAP.keys()), value=self.selected_persona).classes('w-full mb-6')
            persona_drop.bind_value_to(self, 'selected_persona')
            
            # Skill Selection
            ui.label('Enforced Skill').classes('text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider')
            skill_drop = ui.select(SKILLS_LIST, value=self.selected_skill).classes('w-full mb-6')
            skill_drop.bind_value_to(self, 'selected_skill')
            
            ui.markdown('---').classes('my-4')
            ui.label('Backend: signed-in Grok Build').classes('text-xs font-bold text-emerald-500 tracking-wide uppercase')
            ui.label('No API key. Uses `grok login`.').classes('text-xs text-slate-500 dark:text-slate-400 mt-1')
            ui.label('Auto-Approval: ENABLED').classes('text-xs font-bold text-emerald-500 tracking-wide uppercase mt-3')

        # ---------------------------------------------------------
        # Main Layout Structure
        # ---------------------------------------------------------
        with ui.column().classes('w-full flex flex-col pt-4 pb-32 px-4 md:px-6'):
            # Tab Content
            with ui.tab_panels(self.main_tabs, value='chat').classes('w-full bg-transparent flex-grow'):
                
                # Chat tab
                with ui.tab_panel('chat').classes('w-full p-0 bg-transparent flex flex-col'):
                    self.chat_container = ui.column().classes('w-full flex-grow mb-6')
                    
                    # Collapsible agent execution logger console (hidden by default, shown only when agent is active)
                    with ui.column().classes('w-full mb-6 transition-all duration-300') as self.progress_container:
                        self.progress_container.set_visibility(False)
                        with ui.card().classes('w-full border border-slate-300 dark:border-slate-800 bg-slate-100 dark:bg-slate-900 p-4 rounded-xl shadow-inner'):
                            with ui.row().classes('w-full items-center gap-2 mb-2'):
                                ui.spinner(size='sm', color='indigo')
                                ui.label('Grok Running - Live Execution Pipeline').classes('text-xs font-bold text-indigo-500 dark:text-indigo-400 tracking-wide uppercase')
                            
                            # Thinking monologue
                            with ui.expansion('Agent Thinking Monologue', icon='psychology').classes('w-full border border-slate-200 dark:border-slate-800 rounded-lg mb-2 bg-slate-50 dark:bg-slate-950'):
                                self.thinking_display = ui.markdown().classes('text-xs text-slate-700 dark:text-slate-300 p-2 font-mono')
                                
                            # Running Tool
                            with ui.expansion('Currently Executed Tool/Skill', icon='construction').classes('w-full border border-slate-200 dark:border-slate-800 rounded-lg mb-2 bg-slate-50 dark:bg-slate-950'):
                                self.tool_display = ui.markdown().classes('text-xs text-slate-700 dark:text-slate-300 p-2 font-mono')
                                self.tool_output_display = ui.markdown().classes('text-xs text-slate-600 dark:text-slate-400 p-2 bg-slate-100 dark:bg-slate-900 rounded font-mono overflow-auto max-h-48')

                            # Raw standard logger updates
                            with ui.expansion('System Logs (Stdout/Logger)', icon='terminal').classes('w-full border border-slate-200 dark:border-slate-800 rounded-lg bg-slate-50 dark:bg-slate-950'):
                                self.terminal_display = ui.markdown().classes('text-xs text-emerald-600 dark:text-emerald-500 p-2 bg-black rounded font-mono overflow-auto max-h-48')
                
                # Reader tab
                with ui.tab_panel('reader').classes('w-full p-6 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm'):
                    self.reader_title = ui.label('No File Selected').classes('text-xl font-bold text-slate-800 dark:text-slate-100 border-b border-slate-200 dark:border-slate-800 pb-2 mb-4')
                    self.reader_container = ui.column().classes('w-full')
                    with self.reader_container:
                        self.reader_content = ui.markdown('Select a file from the left sidebar tree to view it. New exegesis results are written directly to `biblemate/` and `export/`, and images to `images/`.').classes('text-slate-700 dark:text-slate-300')

        # ---------------------------------------------------------
        # Footer Area (Multiline Input Chat Bar)
        # ---------------------------------------------------------
        with ui.footer().classes('bg-slate-100/90 dark:bg-slate-900/90 border-t border-slate-200 dark:border-slate-800 p-4 fixed bottom-0 left-0 right-0 z-10 backdrop-blur-md'):
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
                            label='Ask BibleMate Grok',
                            placeholder='Enter your study request (e.g., Write a devotion on Romans 8:28)...',
                            on_change=handle_input_change
                        ).props('outlined autogrow rows=2 input-class="text-slate-900 dark:text-slate-100"').classes('w-full rounded-xl text-slate-900 dark:text-slate-100')
                        
                        autocomplete_menu = ui.menu().props('fit no-parent-event no-focus no-refocus anchor="top left" self="bottom left"').classes('max-h-60 overflow-y-auto')
                
                    # Inline async sender bound to Client context to avoid RuntimeError
                    async def on_send_click():
                        await self.handle_send(message_input)

                    # Bind Control+S and Command+S keyboard shortcuts to send the request
                    message_input.on('keydown.ctrl.s.prevent', on_send_click)
                    message_input.on('keydown.meta.s.prevent', on_send_click)
                    
                    # Send Button
                    with ui.button(icon='send', on_click=on_send_click).props('round size=lg color=indigo').classes('shadow-md hover:scale-105 transition-transform mb-1') as self.action_button:
                        self.action_button_tooltip = ui.tooltip('Send Request')

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

    # 33378 keeps this app from colliding with web_app.py on 33377.
    port = int(os.environ.get('BIBLEMATE_GROK_PORT', '33378'))
    print(f"BibleMate Grok uses your signed-in `grok login` session (no API key).")
    print(f"Open http://localhost:{port}")
    ui.run(
        title='BibleMate Grok',
        port=port,
        reload=False,  # Disable reload for background execution safety
        show=False     # Do not open a browser window automatically on server start
    )
