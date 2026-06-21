#!/usr/bin/env python3
import os
import sys
import re
import json
import asyncio
import logging
from nicegui import ui, app

# Try to import Antigravity SDK
try:
    from google.antigravity import Agent, LocalAgentConfig
    from google.antigravity.hooks import policy
except ImportError:
    print("Error: google-antigravity is not installed. Please run: pip install google-antigravity")
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

# AI Models Map (Dropdown Labels to SDK Strings)
MODELS_MAP = {
    'Gemini 3.5 Flash': 'gemini-3.5-flash',
    'Gemini 3.5 Pro': 'gemini-3.5-pro',
    'Gemini 2.0 Flash': 'gemini-2.0-flash',
    'Gemini 1.5 Pro': 'gemini-1.5-pro',
    'Gemini 1.5 Flash': 'gemini-1.5-flash'
}

# Regex to match scripture references (e.g. John 3:16, 1 Cor 13, Romans 8:28, 1Tim 3:16)
BIBLE_REF_PATTERN = re.compile(
    r'^\s*([1-3]\s*)?[A-Za-z\s\.\_]+?\s+\d+(\s*:\s*\d+(\s*-\s*\d+)?)?\s*$',
    re.IGNORECASE
)

async def run_local_retriever(skill_name: str, query: str) -> str:
    """Runs a Python database retriever script under .agents/skills directly and returns output."""
    script_path = f".agents/skills/{skill_name}/{skill_name}_retriever.py"
    if not os.path.exists(script_path):
        return f"Error: Local retriever script not found at {script_path}"
    
    try:
        process = await asyncio.create_subprocess_exec(
            sys.executable, script_path, query,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=WORKSPACE_DIR
        )
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
        cmd_mapping = {
            '/bible': 'bible',
            '/commentary': 'commentary',
            '/xrefs': 'xrefs',
            '/lexicon': 'lexicon',
            '/morphology': 'morphology',
            '/interlinear': 'interlinear',
            '/original': 'original',
            '/image': 'image'
        }
        if cmd in cmd_mapping:
            return cmd_mapping[cmd], args
    return None, None

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
            # Check if this log record is relevant to google.antigravity
            normalized_path = record.pathname.replace('\\', '/')
            is_sdk_log = (
                'google/antigravity' in normalized_path or 
                record.name.startswith('google.antigravity') or 
                (isinstance(record.msg, str) and 'RAW WS MSG:' in record.msg)
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
        self.selected_model = 'Gemini 3.5 Flash'
        self.selected_persona = 'Auto'
        self.selected_skill = 'Auto'
        
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
        self.selected_node_id = None
        self.terminal_logs = []
        self.active_agent_running = False
        self.running_chat_task = None
        
        # Slash commands auto-discovery
        self.slash_commands = self.get_slash_commands()
        
        # Log Hook Registration
        self.setup_logging_interceptor()

    def get_slash_commands(self) -> list:
        """Dynamically parses the .agents/workflows/ directory to retrieve available slash commands."""
        commands = []
        workflows_dir = '.agents/workflows'
        if os.path.exists(workflows_dir):
            try:
                for f in os.listdir(workflows_dir):
                    if f.endswith('.md'):
                        commands.append('/' + f[:-3])
            except Exception:
                pass
        return sorted(commands)

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
        
        # Ensure root logger is at INFO level to allow capture of SDK logs
        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)

    def handle_incoming_log(self, log_line: str):
        try:
            # Append to raw terminal logs
            self.terminal_logs.append(log_line)
            if len(self.terminal_logs) > 500:
                self.terminal_logs.pop(0)

            # Get main event loop
            loop = getattr(self, 'loop', None)
            if not loop or not loop.is_running():
                try:
                    loop = asyncio.get_event_loop()
                    self.loop = loop
                except RuntimeError:
                    pass

            # Define a coroutine to refresh the UI elements safely
            async def refresh_ui():
                try:
                    # Update terminal display
                    logs_text = "\n".join(self.terminal_logs[-30:])
                    self.terminal_display.set_content(f"```\n{logs_text}\n```")
                    
                    # Also parse and update progress if parsed
                    parsed = self.parse_raw_log(log_line)
                    if parsed:
                        if 'thinking' in parsed and parsed['thinking']:
                            self.thinking_display.set_content(parsed['thinking'])
                            lines = [l.strip('* ') for l in parsed['thinking'].split('\n') if l.strip()]
                            if lines:
                                snippet = lines[0]
                                if len(snippet) > 50:
                                    snippet = snippet[:50] + "..."
                                ui.notify(f"Agent thinking: {snippet}", group='agent_progress', type='ongoing', timeout=0)
                                
                        if 'command' in parsed and parsed['command']:
                            cmd_line = parsed['command']
                            display_cmd = cmd_line.replace('python3 .agents/skills/', '')
                            if len(display_cmd) > 50:
                                display_cmd = display_cmd[:50] + "..."
                            self.tool_display.set_content(f"**Executing:** `{cmd_line}`")
                            ui.notify(f"Agent executing: {display_cmd}", group='agent_progress', type='ongoing', timeout=0)
                            
                        if 'cmd_output' in parsed and parsed['cmd_output']:
                            self.tool_output_display.set_content(f"```\n{parsed['cmd_output']}\n```")
                except Exception:
                    pass

            # Run the coroutine safely on the event loop
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
        """Recursively builds the dictionary hierarchy for ui.tree representing markdown files."""
        def add_to_tree(path_parts, current_nodes, full_path):
            if not path_parts:
                return
            part = path_parts[0]
            found_node = None
            for node in current_nodes:
                if node['label'] == part:
                    found_node = node
                    break
            if not found_node:
                found_node = {
                    'id': full_path if len(path_parts) == 1 else full_path.split(part)[0] + part,
                    'label': part
                }
                if len(path_parts) > 1:
                    found_node['children'] = []
                current_nodes.append(found_node)
            if len(path_parts) > 1:
                add_to_tree(path_parts[1:], found_node['children'], full_path)

        nodes = []
        for folder in ['biblemate', 'export', 'images']:
            if os.path.exists(folder):
                folder_node = {'id': folder, 'label': folder, 'children': []}
                nodes.append(folder_node)
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        is_valid = False
                        normalized_root = root.replace('\\', '/')
                        if folder == 'images':
                            is_valid = file.lower().endswith(('.png', '.jpg', '.jpeg'))
                        elif folder == 'export' and 'export/docx' in normalized_root:
                            is_valid = file.lower().endswith('.docx')
                        else:
                            is_valid = file.endswith('.md')
                        if is_valid:
                            full_file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_file_path, start=WORKSPACE_DIR)
                            parts = rel_path.split(os.sep)
                            add_to_tree(parts[1:], folder_node['children'], rel_path)

        def sort_nodes(nodes_list, reverse=False):
            nodes_list.sort(key=lambda x: x['label'], reverse=reverse)
            for node in nodes_list:
                if 'children' in node:
                    child_reverse = node['id'].startswith('biblemate')
                    sort_nodes(node['children'], reverse=child_reverse)

        # Sort the folder tree: top-level is alphabetical, items under biblemate are reversed (newest first)
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
                        web_path = f"/images/{os.path.basename(node_id)}"
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
            
        # Explicitly protect root and direct parent folders
        protected = {
            '.', '', 'biblemate', 'export', 'export/md', 'export/docx', 'images',
            'images/readme.md', 'images/readme'
        }
        if clean_path.lower() in protected or clean_path.startswith(('.', '..')):
            return False
            
        # Must be strictly nested inside allowed directories
        allowed_roots = ('biblemate/', 'export/md/', 'export/docx/', 'images/')
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
            
            # Clear reader view if deleted file was open
            if self.reader_title.text == os.path.basename(node_id):
                self.reader_title.set_text("No File Selected")
                self.reader_container.clear()
                with self.reader_container:
                    ui.markdown('Select a file from the left sidebar tree to view it. New exegesis results are written directly to `biblemate/` and `export/`, and images to `images/`.').classes('text-slate-700 dark:text-slate-300')
            
            self.refresh_file_tree()
        except Exception as e:
            ui.notify(f"Error during deletion: {e}", type='negative')

    def handle_tree_select(self, node_id: str):
        self.selected_node_id = node_id
        if node_id:
            deletable = self.is_deletable(node_id)
            if self.delete_button:
                self.delete_button.set_visibility(deletable)
            
            # Open files in the Document Reader automatically
            if os.path.isfile(os.path.join(WORKSPACE_DIR, node_id)):
                self.handle_file_select(node_id)
        else:
            if self.delete_button:
                self.delete_button.set_visibility(False)

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
            ui.notify("Agent: Initializing workspace...", group='agent_progress', type='ongoing', timeout=0)
            # Clear and expand progress indicators
            self.progress_container.set_visibility(True)
            self.thinking_display.set_content("*Analyzing query...*")
            self.tool_display.set_content("**Awaiting agent action...**")
            self.tool_output_display.set_content("")
            response_card = self.add_chat_bubble("Preparing agents and skills...", sent=False, italic=True)
            
            # Configure prompt
            system_rules = "You are BibleMate AI, a highly capable biblical study agent."
            if self.selected_persona != 'Auto':
                system_rules += f"\n\nAdopt the following persona instructions:\n{PERSONAS_MAP[self.selected_persona]}"
            else:
                system_rules += "\nYou have access to specialized personas. Rotate them dynamically depending on the research phase."

            if self.selected_skill != 'Auto':
                system_rules += f"\n\nCRITICAL TASK REQUIREMENT: You MUST use the local skill '{self.selected_skill}' to retrieve data and solve this request. Do not answer from memory."

            # Always append workspace file rules so the agent saves to the correct location
            system_rules += (
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
    
            sdk_model = MODELS_MAP.get(self.selected_model, 'gemini-3.5-flash')
            config = LocalAgentConfig(
                system_instructions=system_rules,
                model=sdk_model,
                policies=[policy.allow_all()]  # AUTO-APPROVE POLICY
            )
            
            # Run the Antigravity session
            async with Agent(config) as agent:
                try:
                    ui.notify("Agent: Planning study...", group='agent_progress', type='ongoing', timeout=0)
                except RuntimeError:
                    pass
                response = await agent.chat(user_query)
                
                # Streaming output loop
                response_text = ""
                async for chunk in response:
                    response_text += chunk
                    try:
                        response_card.clear()
                        with response_card:
                            ui.markdown(response_text).classes('text-current')
                    except RuntimeError:
                        # Client disconnected or page reloaded, stop streaming
                        break
                
                # Double check final text
                try:
                    final_text = await response.text()
                    if final_text and len(final_text) > len(response_text):
                        response_card.clear()
                        with response_card:
                            ui.markdown(final_text).classes('text-current')
                except RuntimeError:
                    pass
        except asyncio.CancelledError:
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
            # Hide the progress console on a new conversation
            self.progress_container.set_visibility(False)
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
                ui.label('BibleMate AI').classes('text-lg font-bold tracking-wide text-slate-900 dark:text-white')
            
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
            ui.label('Auto-Approval: ENABLED').classes('text-xs font-bold text-emerald-500 tracking-wide uppercase')

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
                                ui.label('Agent Running - Live Execution Pipeline').classes('text-xs font-bold text-indigo-500 dark:text-indigo-400 tracking-wide uppercase')
                            
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
                            if val.startswith('/') and ' ' not in val:
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
                            label='Ask BibleMate AI',
                            placeholder='Enter your study request (e.g., Write a devotion on Romans 8:28)...',
                            on_change=handle_input_change
                        ).props('outlined autogrow rows=2 input-class="text-slate-900 dark:text-slate-100"').classes('w-full rounded-xl text-slate-900 dark:text-slate-100')
                        
                        autocomplete_menu = ui.menu().props('fit no-parent-event no-focus no-refocus anchor="top left" self="bottom left"').classes('max-h-60 overflow-y-auto')
                
                    # Inline async sender bound to Client context to avoid RuntimeError
                    async def on_send_click():
                        await self.handle_send(message_input)
                    
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
        await self.execute_agent_chat(query)

if __name__ == '__main__':
    # Initialize application UI
    app_instance = BibleMateApp()
    app_instance.build_ui()

    # Setup logging interceptor after uvicorn initializes on server startup to capture the active event loop
    app.on_startup(lambda: app_instance.setup_logging_interceptor())

    # Start server on default port 33377
    ui.run(
        title='BibleMate App',
        port=33377,
        reload=False,  # Disable reload for background execution safety
        show=False     # Do not open a browser window automatically on server start
    )
