#!/usr/bin/env python3
"""BibleMate web app backed by the google-antigravity Python SDK.

Requires a Gemini API key exported in the environment:
    export GEMINI_API_KEY="your-gemini-api-key"

If you are signed into Antigravity CLI with a Google subscription without an
API key, use `web_app_agy.py` instead.
"""
import os
import sys
import re
import json
import asyncio
import logging
import shutil
import signal
import tempfile
from nicegui import ui, app

# Check for GEMINI_API_KEY
if not os.environ.get("GEMINI_API_KEY"):
    print("Warning: GEMINI_API_KEY environment variable is not set.")
    print("Please export it before executing queries: export GEMINI_API_KEY=\"your-api-key\"")
    print("Or use `web_app_agy.py` to use your signed-in Google subscription with no API key.")

# Try to import Antigravity SDK
try:
    from google.antigravity import Agent, LocalAgentConfig, types
    from google.antigravity.hooks import policy
except ImportError:
    print("Error: google-antigravity is not installed. Please run: pip install -U google-antigravity")
    sys.exit(1)

DEFAULT_READER_FONT_SIZE = 14
READER_FONT_SIZES = tuple(range(12, 33, 2))
DEFAULT_CHAT_FONT_SIZE = 14
CHAT_FONT_SIZES = READER_FONT_SIZES

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

# AI Models Map (Dropdown Labels to SDK Strings; None uses SDK DEFAULT_MODEL)
MODELS_MAP = {
    'Default (SDK default)': None,
    'Gemini 3.8 Flash': 'gemini-3.8-flash',
    'Gemini 3.5 Flash': 'gemini-3.5-flash',
    'Gemini 3.5 Pro': 'gemini-3.5-pro',
    'Gemini 2.5 Pro': 'gemini-2.5-pro',
    'Gemini 2.5 Flash': 'gemini-2.5-flash',
    'Gemini 2.0 Flash': 'gemini-2.0-flash',
}
DEFAULT_MODEL = 'Gemini 3.8 Flash'

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
        # These run the local SQLite retrievers directly without calling the SDK agent.
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

def summarize_tool_input(raw_input) -> str:
    """Pick the most useful field from an Antigravity tool-call payload."""
    if isinstance(raw_input, str):
        return raw_input
    if not isinstance(raw_input, dict):
        return ""
    for key in (
        "CommandLine", "command", "cmd",
        "Path", "TargetFile", "AbsolutePath", "file_path", "path",
        "Query", "query", "Queries", "pattern",
        "DirectoryPath", "Url", "url",
        "Prompt", "prompt", "Role", "TypeName", "description",
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
# Dynamic Logging Interceptor
# ---------------------------------------------------------

class WebAppLogHandler(logging.Handler):
    """Intercepts python logs from google.antigravity to stream to UI."""
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        try:
            normalized_path = record.pathname.replace('\\', '/')
            msg_str = record.getMessage()
            is_sdk_log = (
                'google/antigravity' in normalized_path or
                record.name.startswith('google.antigravity') or
                'RAW WS MSG:' in msg_str
            )
            if is_sdk_log:
                log_line = self.format(record)
                self.callback(log_line)
        except Exception:
            pass


# ---------------------------------------------------------
# NiceGUI Web Application State & Layout
# ---------------------------------------------------------

class BibleMateApp:
    def __init__(self):
        # Settings state
        self.selected_model = DEFAULT_MODEL
        self.selected_persona = 'Auto'
        self.selected_skill = 'Auto'

        # Multi-turn session state for google-antigravity SDK
        self.conversation_id = None
        self.session_save_dir = None
        self.active_response = None
        self.retriever_proc = None

        # UI Toggles and References
        self.left_drawer = None
        self.right_drawer = None
        self.chat_container = None
        self.message_input = None
        self.chat_font_size = DEFAULT_CHAT_FONT_SIZE
        self.chat_font_size_select = None
        self.reader_container = None
        self.reader_font_size = DEFAULT_READER_FONT_SIZE
        self.reader_font_size_select = None
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
        self.terminal_logs = []
        self.active_agent_running = False
        self.running_chat_task = None

        # Slash commands auto-discovery
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
        # Store active event loop
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = None

        # Clean up any existing WebAppLogHandler to avoid duplicates
        root_logger = logging.getLogger()
        for h in list(root_logger.handlers):
            if isinstance(h, WebAppLogHandler):
                root_logger.removeHandler(h)

        handler = WebAppLogHandler(self.handle_incoming_log)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(handler)

        # Ensure root and SDK loggers capture DEBUG (needed for RAW WS MSG tool output updates)
        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)
        logging.getLogger("google.antigravity").setLevel(logging.DEBUG)

    def append_runtime_log(self, log_line: str):
        """Append one human-readable line to the on-screen system log."""
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

    def _render_response(self, response_card, text: str):
        if response_card is None:
            return
        try:
            response_card.clear()
            with response_card:
                ui.markdown(text).classes('text-current')
        except RuntimeError:
            pass

    def handle_incoming_log(self, log_line: str):
        try:
            is_raw_ws = "RAW WS MSG:" in log_line
            if not is_raw_ws:
                self.terminal_logs.append(log_line)
                if len(self.terminal_logs) > 500:
                    self.terminal_logs.pop(0)

            loop = getattr(self, 'loop', None)
            if not loop or not loop.is_running():
                try:
                    loop = asyncio.get_event_loop()
                    self.loop = loop
                except RuntimeError:
                    pass

            async def refresh_ui():
                try:
                    if not is_raw_ws and self.terminal_display is not None:
                        logs_text = "\n".join(self.terminal_logs[-30:])
                        self.terminal_display.set_content(markdown_fence(logs_text))

                    parsed = self.parse_raw_log(log_line)
                    if parsed and parsed.get('cmd_output'):
                        self._set_markdown(
                            self.tool_output_display,
                            markdown_fence(clip_text(parsed['cmd_output'], 4000)),
                        )
                except Exception:
                    pass

            if loop and loop.is_running():
                try:
                    asyncio.run_coroutine_threadsafe(refresh_ui(), loop)
                except Exception:
                    pass
        except Exception:
            pass

    def parse_raw_log(self, log_line: str):
        if "RAW WS MSG:" in log_line:
            try:
                json_str = log_line.split("RAW WS MSG:", 1)[1].strip()
                data = json.loads(json_str)
                step_update = data.get('stepUpdate', {})
                trajectory_update = data.get('trajectoryStateUpdate', {})

                result = {}
                if step_update:
                    result['thinking'] = step_update.get('thinking', '')
                    result['text'] = step_update.get('text', '')
                    result['state'] = step_update.get('state', '')
                    run_cmd = step_update.get('runCommand', {})
                    if run_cmd:
                        result['command'] = run_cmd.get('commandLine', '')
                        result['cmd_output'] = run_cmd.get('combinedOutput', '')
                        result['exit_code'] = run_cmd.get('exitCode', None)
                elif trajectory_update:
                    result['trajectory_state'] = trajectory_update.get('state', '')
                return result
            except Exception:
                pass
        return None

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

    async def _stop_retriever_proc(self, proc=None):
        """Stop the local retriever subprocess group started for the current turn."""
        if proc is None:
            proc = self.retriever_proc
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

    async def handle_stop(self):
        if self.active_response is not None:
            try:
                await self.active_response.cancel()
            except Exception:
                pass
        if self.retriever_proc is not None:
            try:
                await self._stop_retriever_proc(self.retriever_proc)
            except Exception:
                pass
        if self.running_chat_task and not self.running_chat_task.done():
            self.running_chat_task.cancel()
            ui.notify("Stopping agent execution...", type='warning')

    def resolve_skill_name(self, token: str):
        """Match a slash-command token to an .agents skill directory name."""
        if not token:
            return None
        wanted = token.lower()
        for skill in SKILLS_LIST:
            if skill.lower() == wanted:
                return skill
        return None

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

    def build_system_rules(self, active_skill: str) -> str:
        """Rules passed to the Antigravity SDK agent."""
        rules = (
            "You are BibleMate AI running inside the local BibleMate web app, "
            "backed by the google-antigravity Python SDK. Follow AGENTS.md and the skills under .agents/skills/. "
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
            "\n- Save generated images to the `images/` subdirectory (images already use timestamped filenames)."
            "\n- NEVER tell the user a file has been saved unless you have actually written it to"
            " one of these workspace directories in this session."
            "\n- Do NOT write files to any artifact, brain, or temporary directory outside the workspace."
        )
        return rules

    async def run_direct_retriever(self, skill_name: str, args: str, response_card):
        """Answer lookup commands from the local SQLite retrievers directly."""
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
                on_process=lambda process: setattr(self, 'retriever_proc', process),
            )
        self._set_markdown(self.tool_output_display, markdown_fence(clip_text(text or "(no output)", 4000)))
        self._render_response(response_card, text or "(no output)")

    async def run_sdk_turn(self, user_query: str, response_card):
        """Run one turn using the google-antigravity SDK and stream chunks into the UI."""
        active_skill = self.active_skill_for_query(user_query)
        system_rules = self.build_system_rules(active_skill)
        sdk_model = MODELS_MAP.get(self.selected_model, MODELS_MAP[DEFAULT_MODEL])

        if self.session_save_dir is None:
            self.session_save_dir = tempfile.mkdtemp(prefix="biblemate_sdk_")

        config = LocalAgentConfig(
            system_instructions=system_rules,
            model=sdk_model,
            policies=[policy.allow_all()],  # AUTO-APPROVE POLICY
            conversation_id=self.conversation_id,
            session_continuation_mode=(
                types.SessionContinuationMode.CREATE_OR_RESUME
                if self.conversation_id
                else None
            ),
            save_dir=self.session_save_dir,
            debug_config=True,
        )

        async with Agent(config) as agent:
            self._notify_progress("Agent: Planning study...")
            response = await agent.chat(user_query)
            self.active_response = response

            response_text = ""
            thinking_text = ""
            notified_think = False
            needs_paragraph_break = False
            needs_think_break = False

            async for chunk in response.chunks:
                if isinstance(chunk, types.Text):
                    if chunk.text:
                        if needs_paragraph_break and response_text and not response_text.endswith("\n\n"):
                            response_text = response_text.rstrip("\n") + "\n\n"
                        needs_paragraph_break = False
                        response_text += chunk.text
                        try:
                            response_card.clear()
                            with response_card:
                                ui.markdown(response_text).classes('text-current')
                        except RuntimeError:
                            # Client disconnected or page reloaded, stop streaming
                            break
                elif isinstance(chunk, types.Thought):
                    if chunk.text:
                        if needs_think_break and thinking_text and not thinking_text.endswith("\n\n"):
                            thinking_text = thinking_text.rstrip("\n") + "\n\n"
                        needs_think_break = False
                        thinking_text = clip_text(thinking_text + chunk.text, 8000)
                        self._set_markdown(self.thinking_display, thinking_text)
                        if not notified_think:
                            notified_think = True
                            lines = [l.strip('* ') for l in chunk.text.splitlines() if l.strip()]
                            snippet = lines[0] if lines else "reasoning"
                            if len(snippet) > 50:
                                snippet = snippet[:50] + "..."
                            self._notify_progress(f"Agent thinking: {snippet}")
                elif isinstance(chunk, types.ToolCall):
                    needs_paragraph_break = True
                    needs_think_break = True
                    notified_think = False
                    tool_name = str(chunk.name) if chunk.name else "tool"
                    detail = summarize_tool_input(chunk.args)
                    shown = detail or tool_name
                    self._set_markdown(
                        self.tool_display,
                        f"**Executing:** `{tool_name}`" + (f"\n\n`{clip_text(shown, 500)}`" if detail else ""),
                    )
                    display_cmd = shown.replace('python3 .agents/skills/', '')
                    if len(display_cmd) > 50:
                        display_cmd = display_cmd[:50] + "..."
                    self._notify_progress(f"Agent executing: {display_cmd}")
                    self.append_runtime_log(f"tool {tool_name}: {clip_text(shown, 300)}")

            # Double check final text
            try:
                final_text = await response.text()
                if final_text and len(final_text) > len(response_text):
                    self._render_response(response_card, final_text)
            except RuntimeError:
                pass

            if agent.conversation_id:
                self.conversation_id = agent.conversation_id

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
            self._notify_progress("Agent: Initializing workspace...")
            # Clear and expand progress indicators
            self.progress_container.set_visibility(True)
            self.thinking_display.set_content("*Analyzing query...*")
            self.tool_display.set_content("**Awaiting agent action...**")
            self.tool_output_display.set_content("")
            response_card = self.add_chat_bubble("Preparing agents and skills...", sent=False, italic=True)

            direct_skill, direct_args = parse_direct_command(user_query)
            if direct_skill:
                await self.run_direct_retriever(direct_skill, direct_args or "", response_card)
            else:
                await self.run_sdk_turn(user_query, response_card)
        except asyncio.CancelledError:
            proc = self.retriever_proc
            try:
                await asyncio.shield(self._stop_retriever_proc(proc))
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
            self.active_response = None
            self.retriever_proc = None
            self.update_action_button(to_stop=False)
            try:
                # Hide the progress console now that the agent is done
                self.progress_container.set_visibility(False)
                ui.notify("System Ready", group='agent_progress', type='positive', timeout=2000)
                # Refresh file tree to show newly created output files
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
            self.conversation_id = None
            if self.session_save_dir and os.path.isdir(self.session_save_dir):
                shutil.rmtree(self.session_save_dir, ignore_errors=True)
            self.session_save_dir = None
            # Hide the progress console on a new conversation
            self.progress_container.set_visibility(False)
            if hasattr(self, 'main_tabs') and self.main_tabs:
                self.main_tabs.set_value('chat')
            ui.notify("Conversation cleared. Starting afresh!", type='info')
        except Exception as e:
            ui.notify(f"Error clearing conversation: {e}", type='warning')

    def set_chat_font_size(self, font_size):
        """Resize chat messages and input, and remember this browser's choice."""
        if font_size not in CHAT_FONT_SIZES:
            return
        self.chat_font_size = font_size
        for element in (self.chat_container, self.message_input):
            if element is not None:
                element.style(f"--chat-font-size: {font_size}px")
        ui.run_javascript(
            'try { localStorage.setItem("biblemateGemini.chatFontSize", '
            f'{json.dumps(font_size)}); }} catch (err) {{}}'
        )

    async def restore_chat_font_size(self):
        """Restore a saved chat size after the browser connects."""
        await ui.context.client.connected()
        font_size = await ui.run_javascript(
            '''return (() => {
                try {
                    return JSON.parse(localStorage.getItem("biblemateGemini.chatFontSize") || "null");
                } catch (err) {
                    return null;
                }
            })();'''
        )
        if font_size in CHAT_FONT_SIZES:
            self.chat_font_size_select.set_value(font_size)

    def set_reader_font_size(self, font_size):
        """Resize reader content and remember the choice in this browser."""
        if font_size not in READER_FONT_SIZES:
            return
        self.reader_font_size = font_size
        if self.reader_container is not None:
            self.reader_container.style(f"--reader-font-size: {font_size}px")
        ui.run_javascript(
            'try { localStorage.setItem("biblemateGemini.readerFontSize", '
            f'{json.dumps(font_size)}); }} catch (err) {{}}'
        )

    async def restore_reader_font_size(self):
        """Restore a saved size after the browser connects; ignore invalid storage."""
        await ui.context.client.connected()
        font_size = await ui.run_javascript(
            '''return (() => {
                try {
                    return JSON.parse(localStorage.getItem("biblemateGemini.readerFontSize") || "null");
                } catch (err) {
                    return null;
                }
            })();'''
        )
        if font_size in READER_FONT_SIZES:
            self.reader_font_size_select.set_value(font_size)

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
            .chat-content .q-card,
            .chat-content .nicegui-markdown,
            .chat-input .q-field__native {
                font-size: var(--chat-font-size, 14px);
            }
            .chat-input .q-field__native { line-height: 1.5; }
            .chat-content .nicegui-markdown {
                --markdown-font-size: var(--chat-font-size, 14px);
                overflow-wrap: anywhere;
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
                --markdown-font-size: var(--reader-font-size, 14px);
                font-size: var(--reader-font-size, 14px);
            }
            /* Scale NiceGUI's fixed headings with each display's text size. */
            :is(.document-reader, .chat-content) .nicegui-markdown h1 {
                font-size: calc(var(--markdown-font-size, 14px) * 48 / 14);
            }
            :is(.document-reader, .chat-content) .nicegui-markdown h2 {
                font-size: calc(var(--markdown-font-size, 14px) * 36 / 14);
                line-height: calc(var(--markdown-font-size, 14px) * 40 / 14);
            }
            :is(.document-reader, .chat-content) .nicegui-markdown h3 {
                font-size: calc(var(--markdown-font-size, 14px) * 30 / 14);
                line-height: calc(var(--markdown-font-size, 14px) * 36 / 14);
            }
            :is(.document-reader, .chat-content) .nicegui-markdown h4 {
                font-size: calc(var(--markdown-font-size, 14px) * 24 / 14);
                line-height: calc(var(--markdown-font-size, 14px) * 32 / 14);
            }
            :is(.document-reader, .chat-content) .nicegui-markdown h5 {
                font-size: calc(var(--markdown-font-size, 14px) * 20 / 14);
                line-height: calc(var(--markdown-font-size, 14px) * 28 / 14);
            }
            :is(.document-reader, .chat-content) .nicegui-markdown h6 {
                font-size: calc(var(--markdown-font-size, 14px) * 18 / 14);
                line-height: calc(var(--markdown-font-size, 14px) * 28 / 14);
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
                ui.label('BibleMate AI').classes('max-sm:hidden text-lg font-bold tracking-wide theme-text')

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
            self.reader_font_size_select = ui.select(
                {size: f"{size} px" for size in READER_FONT_SIZES},
                value=self.reader_font_size,
                label="Reader font size",
                on_change=lambda event: self.set_reader_font_size(event.value),
            ).classes("w-full mb-6")
            self.chat_font_size_select = ui.select(
                {size: f"{size} px" for size in CHAT_FONT_SIZES},
                value=self.chat_font_size,
                label="Chat font size",
                on_change=lambda event: self.set_chat_font_size(event.value),
            ).classes("w-full mb-6")

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
            ui.label('Backend: Antigravity Python SDK').classes('text-xs font-bold text-positive tracking-wide uppercase')
            ui.label('Requires GEMINI_API_KEY in environment.').classes('text-xs theme-muted mt-1')
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
                    self.chat_container = ui.column().classes("chat-content w-full flex-grow mb-6").style(
                        f"--chat-font-size: {self.chat_font_size}px"
                    )

                    # Collapsible agent execution logger console (hidden by default, shown only when agent is active)
                    with ui.column().classes('w-full mb-6 transition-all duration-300') as self.progress_container:
                        self.progress_container.set_visibility(False)
                        with ui.card().classes('w-full border theme-border theme-panel p-4 rounded-xl shadow-inner'):
                            with ui.row().classes('w-full items-center gap-2 mb-2'):
                                ui.spinner(size='sm', color='primary')
                                ui.label('Agent Running - Live Execution Pipeline').classes('text-xs font-bold theme-muted tracking-wide uppercase')

                            # Thinking monologue
                            with ui.expansion('Agent Thinking Monologue', icon='psychology').classes('w-full border theme-border rounded-lg mb-2 theme-bg'):
                                self.thinking_display = ui.markdown().classes('text-xs theme-text p-2 font-mono')

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
                    self.reader_container = ui.column().classes("w-full").style(
                        f"--reader-font-size: {self.reader_font_size}px"
                    )
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
                        self.message_input = message_input = ui.textarea(
                            label='Ask BibleMate AI',
                            placeholder='Enter your study request (e.g., Write a devotion on Romans 8:28)...',
                            on_change=handle_input_change
                        ).props('outlined autogrow rows=2 input-class="theme-text"').classes("chat-input w-full rounded-xl theme-text").style(
                            f"--chat-font-size: {self.chat_font_size}px"
                        )

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
        ui.timer(0.1, self.restore_reader_font_size, once=True)
        ui.timer(0.1, self.restore_chat_font_size, once=True)

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

    # Start server on default port 33380
    port = int(os.environ.get('BIBLEMATE_GEMINI_PORT', '33380'))
    print(f"Open http://localhost:{port}")
    ui.run(
        title='BibleMate App',
        port=port,
        reload=False,  # Disable reload for background execution safety
        show=False     # Do not open a browser window automatically on server start
    )
