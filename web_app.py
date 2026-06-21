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
    'Gemini 3.5 Flash (High)': 'gemini-3.5-flash',
    'Gemini 3.5 Pro': 'gemini-3.5-pro',
    'Gemini 2.0 Flash': 'gemini-2.0-flash',
    'Gemini 1.5 Pro': 'gemini-1.5-pro',
    'Gemini 1.5 Flash': 'gemini-1.5-flash'
}

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
        self.selected_model = 'Gemini 3.5 Flash (High)'
        self.selected_persona = 'Auto'
        self.selected_skill = 'Auto'
        
        # UI Toggles and References
        self.left_drawer = None
        self.right_drawer = None
        self.chat_container = None
        self.terminal_logs = []
        self.active_agent_running = False
        
        # Log Hook Registration
        self.setup_logging_interceptor()

    def setup_logging_interceptor(self):
        handler = WebAppLogHandler(self.handle_incoming_log)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.getLogger('google.antigravity').addHandler(handler)
        logging.getLogger('google.antigravity').setLevel(logging.INFO)

    def handle_incoming_log(self, log_line: str):
        # Append to raw terminal logs
        self.terminal_logs.append(log_line)
        if len(self.terminal_logs) > 500:
            self.terminal_logs.pop(0)

        # Parse real-time progress update if available
        parsed = self.parse_raw_log(log_line)
        if parsed:
            # Update status widgets if UI is built
            asyncio.run_coroutine_threadsafe(self.update_progress_ui(parsed), asyncio.get_event_loop())

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

    async def update_progress_ui(self, parsed: dict):
        # Update progress updates on active widgets
        if 'thinking' in parsed and parsed['thinking']:
            self.thinking_display.set_content(parsed['thinking'])
        if 'command' in parsed and parsed['command']:
            self.tool_display.set_content(f"**Executing:** `{parsed['command']}`")
        if 'cmd_output' in parsed and parsed['cmd_output']:
            self.tool_output_display.set_content(f"```\n{parsed['cmd_output']}\n```")
        
        # Update terminal console
        logs_text = "\n".join(self.terminal_logs[-30:])
        self.terminal_display.set_content(f"```\n{logs_text}\n```")

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
        for folder in ['biblemate', 'export']:
            if os.path.exists(folder):
                folder_node = {'id': folder, 'label': folder, 'children': []}
                nodes.append(folder_node)
                for root, dirs, files in os.walk(folder):
                    for file in files:
                        if file.endswith('.md'):
                            full_file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(full_file_path, start=WORKSPACE_DIR)
                            parts = rel_path.split(os.sep)
                            add_to_tree(parts[1:], folder_node['children'], rel_path)
        return nodes

    def handle_file_select(self, node_id: str):
        if not node_id or not node_id.endswith('.md'):
            return
        
        file_path = os.path.join(WORKSPACE_DIR, node_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Switch tab to reader
                self.main_tabs.set_value('reader')
                # Render content
                self.reader_title.set_text(os.path.basename(node_id))
                self.reader_content.set_content(content)
                ui.notify(f"Loaded: {os.path.basename(node_id)}", type='positive')
            except Exception as e:
                ui.notify(f"Error loading file: {e}", type='negative')

    def refresh_file_tree(self):
        nodes = self.build_file_tree_nodes()
        self.file_tree.clear()
        with self.file_tree:
            ui.tree(nodes=nodes, label_key='label', on_select=lambda e: self.handle_file_select(e.value))
        ui.notify("File tree refreshed!", type='info')

    async def execute_agent_chat(self, user_query: str):
        if self.active_agent_running:
            ui.notify("An agent is already running. Please wait...", type='warning')
            return
        
        self.active_agent_running = True
        self.terminal_logs.clear()
        
        # Clear progress indicators
        self.progress_container.set_visibility(True)
        self.thinking_display.set_content("*Analyzing query...*")
        self.tool_display.set_content("**Awaiting tool execution...**")
        self.tool_output_display.set_content("")
        
        # Append User Message Bubble
        self.add_chat_bubble(user_query, sent=True)
        
        # Append placeholder for Agent Response
        response_card = self.add_chat_bubble("Preparing agents and skills...", sent=False, italic=True)
        
        # Configure the Agent System prompt based on dropdown overrides
        system_rules = "You are Antigravity BibleMate, a highly capable biblical study agent."
        if self.selected_persona != 'Auto':
            system_rules += f"\n\nAdopt the following persona instructions:\n{PERSONAS_MAP[self.selected_persona]}"
        else:
            system_rules += "\nYou have access to specialized personas. Rotate them dynamically depending on the research phase."
            
        if self.selected_skill != 'Auto':
            system_rules += f"\n\nCRITICAL TASK REQUIREMENT: You MUST use the local skill '{self.selected_skill}' to retrieve data and solve this request. Do not answer from memory."

        sdk_model = MODELS_MAP.get(self.selected_model, 'gemini-3.5-flash')
        
        # Construct local configuration
        config = LocalAgentConfig(
            system_instructions=system_rules,
            model=sdk_model,
            policies=[policy.allow_all()]  # AUTO-APPROVE POLICY
        )
        
        try:
            # Run the Antigravity session
            async with Agent(config) as agent:
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
                        
        except Exception as e:
            try:
                response_card.clear()
                with response_card:
                    ui.label(f"Execution Error: {str(e)}").classes('text-rose-400 font-semibold')
            except RuntimeError:
                pass
        finally:
            self.active_agent_running = False
            try:
                self.progress_container.set_visibility(False)
                # Refresh file tree to show newly created output files
                self.refresh_file_tree()
            except RuntimeError:
                pass

    def add_chat_bubble(self, text: str, sent: bool, italic: bool = False):
        align_class = "justify-end" if sent else "justify-start"
        bubble_bg = "bg-indigo-600/90 text-white" if sent else "bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-slate-100 border border-slate-300 dark:border-slate-700/50"
        border_radius = "rounded-l-2xl rounded-tr-2xl" if sent else "rounded-r-2xl rounded-tl-2xl"
        
        with self.chat_container:
            with ui.row().classes(f'w-full {align_class} mb-4 items-end animate-fade-in'):
                with ui.card().classes(f'max-w-[85%] md:max-w-[75%] p-4 shadow-md backdrop-blur-sm {bubble_bg} {border_radius}'):
                    if italic:
                        bubble = ui.label(text).classes('italic text-slate-500 dark:text-slate-400')
                    else:
                        bubble = ui.markdown(text) if not sent else ui.label(text)
        
        # Scroll to bottom using the specific client context to prevent RuntimeError in background tasks
        self.chat_container.client.run_javascript('window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });')
        return bubble

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
                ui.label('Antigravity BibleMate').classes('text-lg font-bold tracking-wide text-slate-900 dark:text-white')
            
            with ui.row().classes('items-center gap-3'):
                # Theme toggle button
                ui.button(
                    icon='dark_mode',
                    on_click=lambda: dark.toggle()
                ).props('flat round').classes('text-slate-700 dark:text-slate-200')
                
                # Settings toggle button
                ui.button(icon='settings', on_click=lambda: self.right_drawer.toggle()).props('flat round').classes('text-slate-700 dark:text-slate-200')

        # ---------------------------------------------------------
        # Left Drawer (Collapsible File Tree)
        # ---------------------------------------------------------
        with ui.left_drawer(value=True).classes('bg-slate-50 dark:bg-slate-950 border-r border-slate-200 dark:border-slate-900 p-4') as self.left_drawer:
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label('Saved Studies').classes('text-md font-bold text-slate-800 dark:text-slate-200')
                ui.button(icon='refresh', on_click=self.refresh_file_tree).props('flat round size=sm').classes('text-slate-600 dark:text-slate-400')
            
            # Dynamic Container
            self.file_tree = ui.column().classes('w-full')
            self.refresh_file_tree()

        # ---------------------------------------------------------
        # Right Drawer (Settings Panel)
        # ---------------------------------------------------------
        with ui.right_drawer(value=False).classes('bg-slate-50 dark:bg-slate-950 border-l border-slate-200 dark:border-slate-900 p-6') as self.right_drawer:
            ui.label('Agent Options').classes('text-lg font-bold text-slate-800 dark:text-slate-200 mb-6')
            
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
        with ui.column().classes('w-full min-h-screen flex flex-col justify-between pt-20 pb-36 px-4 md:px-8 max-w-5xl mx-auto'):
            
            # Tabs Menu
            with ui.tabs().classes('w-full border-b border-slate-200 dark:border-slate-800 mb-4') as self.main_tabs:
                ui.tab('chat', label='Chat Workspace', icon='chat')
                ui.tab('reader', label='Document Reader', icon='menu_book')

            # Tab Content
            with ui.tab_panels(self.main_tabs, value='chat').classes('w-full bg-transparent flex-grow'):
                
                # Chat tab
                with ui.tab_panel('chat').classes('w-full p-0 bg-transparent flex flex-col'):
                    self.chat_container = ui.column().classes('w-full flex-grow mb-6')
                    
                    # Collapsible agent execution logger console
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
                    self.reader_content = ui.markdown('Select a markdown file from the left sidebar tree to read its content. New exegesis results are written directly to `biblemate/` and `export/`.').classes('text-slate-700 dark:text-slate-300')

        # ---------------------------------------------------------
        # Footer Area (Multiline Input Chat Bar)
        # ---------------------------------------------------------
        with ui.footer().classes('bg-slate-100/90 dark:bg-slate-900/90 border-t border-slate-200 dark:border-slate-800 p-4 fixed bottom-0 left-0 right-0 z-10 backdrop-blur-md'):
            with ui.row().classes('w-full max-w-4xl mx-auto items-end gap-3'):
                # Multi-line textarea for entry requests
                # We remove the custom text and background overrides so NiceGUI/Quasar naturally styles colors according to the active dark/light mode
                message_input = ui.textarea(
                    label='Ask BibleMate',
                    placeholder='Enter your study request (e.g., Write a devotion on Romans 8:28)...'
                ).props('outlined autogrow rows=2').classes('flex-grow rounded-xl')
                
                # Inline async sender bound to Client context to avoid RuntimeError
                async def on_send_click():
                    await self.handle_send(message_input)
                
                # Send Button
                ui.button(
                    icon='send',
                    on_click=on_send_click
                ).props('round size=lg color=indigo').classes('shadow-md hover:scale-105 transition-transform mb-1')

    async def handle_send(self, message_input):
        query = message_input.value.strip()
        if not query:
            return
        # Clear text entry field
        message_input.value = ''
        await self.execute_agent_chat(query)

# Initialize application UI
app_instance = BibleMateApp()
app_instance.build_ui()

# Start server on default port 33377
ui.run(
    title='BibleMate App',
    port=33377,
    reload=False,  # Disable reload for background execution safety
    show=False     # Do not open a browser window automatically on server start
)
