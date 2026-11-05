"""Codex protocol and subprocess integration checks without GUI dependencies."""

import asyncio
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import types
import unittest
from unittest.mock import AsyncMock, MagicMock, patch


ROOT = Path(__file__).resolve().parents[1]


def load_app():
    # The tests exercise the actual app methods; only rendering dependencies
    # are stubbed so the repository's standard-library test suite still works.
    nicegui = types.ModuleType("nicegui")
    nicegui.ui = MagicMock()
    nicegui.app = MagicMock()
    nicegui.ui.page.side_effect = lambda *args, **kwargs: lambda fn: fn
    nicegui.app.get.side_effect = lambda *args, **kwargs: lambda fn: fn
    fastapi = types.ModuleType("fastapi")
    fastapi.HTTPException = Exception
    responses = types.ModuleType("fastapi.responses")
    responses.FileResponse = MagicMock()
    spec = importlib.util.spec_from_file_location("biblemate_codex_test", ROOT / "web_app_codex.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {"nicegui": nicegui, "fastapi": fastapi, "fastapi.responses": responses}), \
            patch("shutil.which", return_value=sys.executable), patch("os.chdir"), patch("os.makedirs"):
        spec.loader.exec_module(module)
    return module


APP = load_app()


def new_app():
    instance = APP.BibleMateApp()
    for name in ("thinking_display", "tool_display", "tool_output_display", "terminal_display",
                 "chat_container", "progress_container", "main_tabs"):
        setattr(instance, name, MagicMock())
    instance._render_response = MagicMock()
    instance._notify_progress = MagicMock()
    return instance


class CodexEventsTest(unittest.TestCase):
    def setUp(self):
        self.instance = new_app()
        self.state = {"text": "", "thinking": "", "error": "", "notified_think": False}

    def event(self, etype, item):
        self.instance.apply_codex_event({"type": etype, "item": item}, self.state, None)

    def test_message_snapshots_are_not_duplicated_and_keep_paragraphs(self):
        self.event("item.updated", {"id": "a", "type": "agent_message", "phase": "final_answer", "text": "Working"})
        self.event("item.completed", {"id": "a", "type": "agent_message", "phase": "final_answer", "text": "Working on it."})
        self.event("item.completed", {"id": "b", "type": "agent_message", "phase": "final_answer", "text": "Done."})
        self.assertEqual(self.state["text"], "Working on it.\n\nDone.")

    def test_unphased_cli_commentary_updates_thinking_and_never_the_response(self):
        self.event("item.updated", {"id": "progress", "type": "agent_message", "text": "Checking"})
        self.event("item.completed", {"id": "progress", "type": "agent_message", "text": "Checking live sources."})
        self.event("item.completed", {"id": "next", "type": "agent_message", "text": "Reviewing the report."})
        self.assertEqual(self.state["thinking"], "Checking live sources.\n\nReviewing the report.")
        self.assertEqual(self.state["text"], "")
        self.instance._render_response.assert_not_called()

    def test_explicit_commentary_and_reasoning_share_the_thinking_panel(self):
        self.event("item.completed", {"id": "reason", "type": "reasoning", "text": "Reviewing evidence."})
        self.event("item.completed", {"id": "progress", "type": "agent_message", "phase": "commentary", "text": "Checking sources."})
        self.event("item.completed", {"id": "answer", "type": "agent_message", "phase": "final_answer", "text": "The final answer."})
        self.assertEqual(self.state["thinking"], "Reviewing evidence.\n\nChecking sources.")
        self.assertEqual(self.state["text"], "The final answer.")

    def test_tool_transitions_preserve_snapshots_and_restart_thinking_toasts(self):
        thought = {"id": "reason", "type": "reasoning", "text": "Checking sources."}
        self.event("item.updated", thought)
        self.event("item.completed", thought)
        self.assertEqual(self.instance._notify_progress.call_count, 1)
        self.event("item.completed", {"id": "intro", "type": "agent_message",
                                      "phase": "final_answer", "text": "Preparing the report."})
        self.event("item.started", {"id": "tool", "type": "command_execution", "command": "read sources"})
        self.event("item.completed", {"id": "tool", "type": "command_execution", "command": "read sources"})
        self.instance._notify_progress.reset_mock()
        next_thought = {"id": "next", "type": "reasoning", "text": "Writing findings."}
        self.event("item.updated", next_thought)
        self.event("item.completed", next_thought)
        self.instance._notify_progress.assert_called_once()
        self.event("item.completed", {"id": "answer", "type": "agent_message",
                                      "phase": "final_answer", "text": "# Findings"})
        self.assertEqual(self.state["text"], "Preparing the report.\n\n# Findings")
        self.assertEqual(self.state["thinking"], "Checking sources.\n\nWriting findings.")

    def test_tool_summaries_show_targets_instead_of_written_file_contents(self):
        payload = {"Path": "biblemate/report.md", "Content": "private body " * 10000}
        self.assertEqual(APP.summarize_tool_input(payload), "biblemate/report.md")
        self.assertEqual(APP.summarize_tool_input(json.dumps(payload)), "biblemate/report.md")
        self.assertEqual(APP.summarize_tool_input({"Queries": ["alpha", "beta"], "Content": "body"}), "alpha, beta")
        self.event("item.started", {"type": "mcp_tool_call", "server": "files", "tool": "write",
                                    "arguments": json.dumps(payload)})
        detail = self.instance.tool_display.set_content.call_args.args[0]
        self.assertIn("files/write", detail)
        self.assertIn("biblemate/report.md", detail)
        self.assertNotIn("private body", detail)
        self.assertNotIn("private body", self.instance.terminal_logs[-1])
        self.assertNotIn("private body", self.instance._notify_progress.call_args.args[0])

    def test_native_command_output_and_nonzero_exit_are_displayed(self):
        item = {"id": "cmd", "type": "command_execution", "command": "python3 helper.py"}
        self.event("item.started", item)
        self.event("item.updated", dict(item, aggregated_output="first line\n"))
        self.assertIn("first line", self.instance.tool_output_display.set_content.call_args.args[0])
        self.event("item.completed", dict(item, aggregated_output="first line\nfailed\n", exit_code=2, status="failed"))
        self.assertIn("failed", self.instance.tool_output_display.set_content.call_args.args[0])
        self.assertIn("exit=2", self.instance.terminal_logs[-1])

    def test_mcp_search_file_changes_and_plan_are_visible(self):
        self.event("item.completed", {"type": "mcp_tool_call", "server": "research", "tool": "search",
                                      "result": {"content": [{"type": "text", "text": "Sources found"}]}})
        self.assertIn("Sources found", self.instance.tool_output_display.set_content.call_args.args[0])
        self.event("item.started", {"type": "web_search", "query": "company filings"})
        self.assertIn("company filings", self.instance.tool_display.set_content.call_args.args[0])
        self.event("item.completed", {"type": "file_change", "changes": [{"kind": "add", "path": "notes/report.md"}]})
        self.assertIn("notes/report.md", self.instance.tool_display.set_content.call_args.args[0])
        self.event("item.updated", {"type": "todo_list", "items": [{"text": "Read sources", "completed": True}]})
        self.assertIn("[x] Read sources", self.instance.tool_display.set_content.call_args.args[0])

    def test_reasoning_snapshots_and_failure(self):
        item = {"id": "thought", "type": "reasoning", "text": "Reviewing sources"}
        self.event("item.updated", item)
        self.event("item.completed", item)
        self.assertEqual(self.state["thinking"], "Reviewing sources")
        self.instance.apply_codex_event({"type": "turn.failed", "error": {"message": "Login required"}}, self.state, None)
        self.assertEqual(self.state["error"], "Login required")

    def test_blank_malformed_and_unknown_events_do_not_abort(self):
        self.assertIsNone(APP.parse_codex_stream_line("\n"))
        for raw in ("diagnostic", "[]", "42"):
            event = APP.parse_codex_stream_line(raw)
            self.instance.apply_codex_event(event, self.state, None)
            self.assertEqual(self.instance.terminal_logs[-1], raw)
        self.instance.apply_codex_event({"type": "future.event"}, self.state, None)

    def test_direct_bible_commands_still_use_local_retrievers(self):
        for command, skill in (("/bible", "bible"), ("/commentary", "commentary"), ("/lexicon", "lexicon")):
            self.assertEqual(APP.parse_direct_command(command + " John 3:16"), (skill, "John 3:16"))
        self.assertEqual(APP.parse_direct_command("/sermon John 3:16"), (None, None))


class CodexSubprocessTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.capture = self.root / "request.json"
        self.executable = self.root / "codex"
        self.instance = new_app()
        self.card = object()

    def fixture_cli(self, events, code=0, extra="", final_text=None):
        write_final = ""
        if final_text is not None:
            write_final = f"Path(sys.argv[sys.argv.index('-o') + 1]).write_text({final_text!r})\n"
        self.executable.write_text(
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            f"Path({str(self.capture)!r}).write_text(json.dumps({{'argv': sys.argv[1:], 'prompt': sys.stdin.read(), 'cwd': os.getcwd()}}))\n"
            + extra + "\n"
            + f"events = {events!r}\n"
            "for event in events:\n"
            "    print(json.dumps(event), flush=True)\n"
            + write_final
            + f"sys.exit({code})\n"
        )
        self.executable.chmod(0o755)

    async def run_turn(self, query):
        with patch.object(APP, "CODEX_BIN", str(self.executable)):
            await asyncio.wait_for(self.instance.run_codex_turn(query, self.card), timeout=10)
        return json.loads(self.capture.read_text())

    async def test_large_stdout_stderr_stdin_and_resume(self):
        thread = "11111111-2222-3333-4444-555555555555"
        events = [
            {"type": "thread.started", "thread_id": thread},
            {"type": "item.completed", "item": {"id": "command", "type": "command_execution", "command": "read report",
                                                "aggregated_output": "x" * 120000, "exit_code": 0}},
            {"type": "item.completed", "item": {"id": "answer", "type": "agent_message", "text": "Finished."}},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}},
        ]
        self.fixture_cli(events, extra="sys.stderr.write('diagnostic ' + 'y' * 90000 + '\\n'); sys.stderr.flush()", final_text="Finished.")
        query = "--literal argument\n`whoami` $(hostname) $price NVDA"
        request = await self.run_turn(query)
        output_index = request["argv"].index("-o")
        self.assertFalse(Path(request["argv"][output_index + 1]).exists())
        del request["argv"][output_index:output_index + 2]
        self.assertEqual(request["argv"][-3:], ["exec", "--json", "-"])
        self.assertNotIn("-m", request["argv"])
        self.assertIn("--search", request["argv"])
        self.assertIn(query, request["prompt"])
        self.assertNotIn(query, request["argv"])
        self.assertEqual(request["cwd"], str(ROOT))
        self.assertEqual(self.instance.codex_session_id, thread)
        self.instance._render_response.assert_called_with(self.card, "Finished.")
        self.assertTrue(any(line.startswith("diagnostic") for line in self.instance.terminal_logs))
        self.assertIsNone(self.instance.codex_proc)

        self.instance.selected_model = "GPT-5 Codex"
        self.instance.selected_skill = "bible"
        request = await self.run_turn("Follow-up question")
        args = request["argv"]
        output_index = args.index("-o")
        del args[output_index:output_index + 2]
        self.assertEqual(args[args.index("exec"):], ["exec", "resume", "--json", "-m", "gpt-5-codex", thread, "-"])
        self.assertIn(".codex/skills/bible/SKILL.md", request["prompt"])

    async def test_failed_turn_after_partial_answer_is_explicit(self):
        self.fixture_cli([
            {"type": "item.completed", "item": {"id": "answer", "type": "agent_message", "phase": "final_answer", "text": "Partial findings."}},
            {"type": "turn.failed", "error": {"message": "Subscription session expired"}},
        ], code=1)
        await self.run_turn("Continue")
        result = self.instance._render_response.call_args.args[1]
        self.assertIn("Partial findings.", result)
        self.assertIn("Codex error:", result)
        self.assertIn("Subscription session expired", result)

    async def test_session_rules_are_deduplicated_and_resent_on_setting_or_session_changes(self):
        thread = "11111111-2222-3333-4444-555555555555"
        self.fixture_cli([{"type": "thread.started", "thread_id": thread}, {"type": "turn.completed"}],
                         final_text="Done.")
        request = await self.run_turn("First question")
        self.assertIn("## BibleMate Web App Instructions", request["prompt"])
        request = await self.run_turn("Follow-up\n`literal` $(literal) $literal")
        self.assertEqual(request["prompt"], "Follow-up\n`literal` $(literal) $literal")
        self.instance.selected_skill = "sermon"
        request = await self.run_turn("Apply the skill")
        self.assertIn(".codex/skills/sermon/SKILL.md", request["prompt"])
        self.assertEqual((await self.run_turn("Continue"))["prompt"], "Continue")
        self.instance.selected_skill = "Auto"
        request = await self.run_turn("Use Auto again")
        self.assertIn("## BibleMate Web App Instructions", request["prompt"])
        self.assertNotIn("CRITICAL TASK REQUIREMENT", request["prompt"])
        with patch.dict(APP.PERSONAS_MAP, {"Fixture Persona": "Use fixture persona instructions."}):
            self.instance.selected_persona = "Fixture Persona"
            request = await self.run_turn("Change persona")
        self.assertIn("Use fixture persona instructions.", request["prompt"])
        self.instance.codex_session_id = "another-thread"
        self.assertIn("## BibleMate Web App Instructions", (await self.run_turn("Other session"))["prompt"])
        self.instance.clear_conversation()
        self.assertIn("## BibleMate Web App Instructions", (await self.run_turn("Start again"))["prompt"])

    async def test_failed_rules_update_is_retried_on_the_next_turn(self):
        self.instance.codex_session_id = "existing-thread"
        self.instance.codex_rules_session_id = "existing-thread"
        self.instance.codex_last_rules_key = ("Auto", "Auto")
        self.instance.selected_skill = "sermon"
        self.fixture_cli([{"type": "turn.failed", "error": {"message": "Temporary failure"}}], code=1)
        await self.run_turn("Change skill")
        self.assertEqual(self.instance.codex_last_rules_key, ("Auto", "Auto"))
        self.fixture_cli([{"type": "turn.completed"}], final_text="Done.")
        request = await self.run_turn("Retry")
        self.assertIn(".codex/skills/sermon/SKILL.md", request["prompt"])
        self.assertEqual(self.instance.codex_last_rules_key, ("Auto", "sermon"))

    async def test_effort_is_model_specific_and_passed_on_new_and_resumed_turns(self):
        models = {APP.DEFAULT_MODEL: None, "Fixture Model": "fixture-model", "Limited Model": "limited-model"}
        efforts = {"fixture-model": ["low", "high"], "limited-model": ["low"]}
        with patch.object(APP, "MODELS_MAP", models), patch.object(APP, "MODEL_EFFORTS", efforts):
            self.assertEqual(self.instance.effort_options(), [APP.DEFAULT_EFFORT])
            self.instance.effort_dropdown = MagicMock()
            self.instance.update_effort_options("Fixture Model")
            self.instance.effort_dropdown.set_options.assert_called_with(
                [APP.DEFAULT_EFFORT, "low", "high"], value=APP.DEFAULT_EFFORT)
            self.instance.selected_effort = "high"
            self.fixture_cli([{"type": "thread.started", "thread_id": "fixture-thread"}], final_text="Done.")
            for _ in range(2):
                request = await self.run_turn("Question")
                argv = request["argv"]
                self.assertEqual(argv[argv.index("-c") + 1], 'model_reasoning_effort="high"')
                self.assertEqual(argv[argv.index("-m") + 1], "fixture-model")
            self.assertIn("resume", request["argv"])
            self.instance.update_effort_options("Limited Model")
            self.assertEqual(self.instance.selected_effort, APP.DEFAULT_EFFORT)
            request = await self.run_turn("Use default effort")
            self.assertNotIn("-c", request["argv"])
            self.instance.selected_effort = "unsupported"
            request = await self.run_turn("Ignore stale effort")
            self.assertNotIn("-c", request["argv"])

    async def test_nonzero_exit_and_empty_reply_are_explicit(self):
        self.fixture_cli([], code=4)
        await self.run_turn("Question")
        self.assertIn("exited with code 4", self.instance._render_response.call_args.args[1])
        self.fixture_cli([])
        await self.run_turn("Question")
        self.assertIn("without a final reply", self.instance._render_response.call_args.args[1])

    async def test_unphased_progress_stays_in_thinking_and_final_file_populates_response(self):
        self.fixture_cli([
            {"type": "item.completed", "item": {"id": "progress", "type": "agent_message", "text": "Checking sources."}},
            {"type": "item.completed", "item": {"id": "review", "type": "agent_message", "text": "Reviewing the report."}},
            {"type": "item.completed", "item": {"id": "answer", "type": "agent_message", "text": "Report saved."}},
            {"type": "turn.completed"},
        ], final_text="Report saved.\n")
        await self.run_turn("Research fixture")
        self.instance._render_response.assert_called_once_with(self.card, "Report saved.")
        self.assertEqual(self.instance.thinking_display.set_content.call_args.args[0],
                         "Checking sources.\n\nReviewing the report.")

    async def test_missing_final_file_does_not_promote_last_progress_update(self):
        self.fixture_cli([
            {"type": "item.completed", "item": {"id": "progress", "type": "agent_message", "text": "Still checking sources."}},
            {"type": "turn.completed"},
        ])
        await self.run_turn("Research fixture")
        result = self.instance._render_response.call_args.args[1]
        self.assertIn("without a final reply", result)
        self.assertNotIn("Still checking sources", result)

    async def test_failed_unphased_progress_is_not_displayed_as_an_answer(self):
        self.fixture_cli([
            {"type": "item.completed", "item": {"id": "progress", "type": "agent_message", "text": "Checking sources."}},
            {"type": "turn.failed", "error": {"message": "Session expired"}},
        ], code=1, final_text="Checking sources.")
        await self.run_turn("Research fixture")
        result = self.instance._render_response.call_args.args[1]
        self.assertIn("Session expired", result)
        self.assertNotIn("Checking sources", result)

    async def test_cancel_terminates_cli_and_its_child_command(self):
        child_pid_file = self.root / "child.pid"
        self.fixture_cli([], extra=(
            "import signal, subprocess, time\n"
            "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'])\n"
            "def stop(signum, frame):\n"
            "    child.wait(timeout=2)\n"
            "    sys.exit(0)\n"
            "signal.signal(signal.SIGTERM, stop)\n"
            f"Path({str(child_pid_file)!r}).write_text(str(child.pid))\n"
            "time.sleep(60)\n"
        ))
        with patch.object(APP, "CODEX_BIN", str(self.executable)):
            task = asyncio.create_task(self.instance.run_codex_turn("Long task", self.card))
            proc = None
            try:
                for _ in range(100):
                    if child_pid_file.exists():
                        break
                    await asyncio.sleep(0.02)
                self.assertTrue(child_pid_file.exists())
                proc = self.instance.codex_proc
                child_pid = int(child_pid_file.read_text())
                task.cancel()
                with self.assertRaises(asyncio.CancelledError):
                    await asyncio.wait_for(task, timeout=6)
                self.assertIsNotNone(proc.returncode)
                with self.assertRaises(ProcessLookupError):
                    os.kill(child_pid, 0)
                self.assertIsNone(self.instance.codex_proc)
            finally:
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                if proc and proc.returncode is None:
                    os.killpg(proc.pid, signal.SIGKILL)
                    await proc.wait()

    async def test_new_conversation_clears_session(self):
        self.instance.codex_session_id = "old-thread"
        self.instance.codex_last_rules_key = ("Auto", "Auto")
        self.instance.codex_rules_session_id = "old-thread"
        self.instance.clear_conversation()
        self.assertIsNone(self.instance.codex_session_id)
        self.assertIsNone(self.instance.codex_last_rules_key)
        self.assertIsNone(self.instance.codex_rules_session_id)
        self.instance.chat_container.clear.assert_called_once()

    async def test_direct_bible_lookup_returns_retriever_output_without_codex(self):
        self.instance.add_chat_bubble = MagicMock(return_value=self.card)
        self.instance.refresh_file_tree = MagicMock()
        self.instance.run_codex_turn = AsyncMock()
        with patch.object(APP, "run_local_retriever", new=AsyncMock(return_value="Fixture database result.")) as retriever:
            await self.instance.execute_agent_chat("/bible NET John 3:16")
        retriever.assert_awaited_once()
        self.assertEqual(retriever.call_args.args, ("bible", "NET John 3:16"))
        self.instance.run_codex_turn.assert_not_awaited()
        self.instance._render_response.assert_called_once_with(self.card, "Fixture database result.")


class CodexModelDiscoveryTest(unittest.IsolatedAsyncioTestCase):
    async def test_live_protocol_handles_initialization_pagination_and_model_efforts(self):
        pages = [
            {"data": [{"model": "model-a", "displayName": "Shared Name",
                       "supportedReasoningEfforts": [{"reasoningEffort": "low"}, {"reasoningEffort": "high"}]}],
             "nextCursor": "second-page"},
            {"data": [{"model": "model-b", "displayName": "Shared Name"},
                      {"model": "hidden-model", "hidden": True}], "nextCursor": None},
        ]
        with tempfile.TemporaryDirectory() as temp:
            executable = Path(temp) / "codex"
            capture = Path(temp) / "requests.json"
            executable.write_text(
                f"#!{sys.executable}\n"
                "import json, sys\nfrom pathlib import Path\n"
                f"pages = {pages!r}\n"
                "requests = []; initialized = False; page = 0\n"
                "for line in sys.stdin:\n"
                "    request = json.loads(line); requests.append(request)\n"
                f"    Path({str(capture)!r}).write_text(json.dumps(requests))\n"
                "    if request['method'] == 'initialize':\n"
                "        print(json.dumps({'id': request['id'], 'result': {}}), flush=True)\n"
                "        print(json.dumps({'method': 'unrelated/notification'}), flush=True)\n"
                "    elif request['method'] == 'initialized':\n"
                "        initialized = True\n"
                "    elif request['method'] == 'model/list':\n"
                "        assert initialized\n"
                "        print(json.dumps({'id': request['id'], 'result': pages[page]}), flush=True)\n"
                "        page += 1\n"
            )
            executable.chmod(0o755)
            with patch.object(APP, "CODEX_BIN", str(executable)):
                models, efforts = await APP.discover_codex_models(APP.FALLBACK_MODELS_MAP)
            self.assertEqual(models, {APP.DEFAULT_MODEL: None, "Shared Name": "model-a",
                                      "Shared Name (model-b)": "model-b"})
            self.assertEqual(efforts, {"model-a": ["low", "high"], "model-b": []})
            requests = json.loads(capture.read_text())
            self.assertEqual([request["method"] for request in requests],
                             ["initialize", "initialized", "model/list", "model/list"])
            self.assertEqual(requests[-1]["params"]["cursor"], "second-page")

    async def test_timeout_falls_back_and_reaps_discovery_process(self):
        created = []
        real_create = asyncio.create_subprocess_exec

        async def slow_cli(*args, **kwargs):
            proc = await real_create(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)
            created.append(proc)
            return proc

        with patch.object(APP.asyncio, "create_subprocess_exec", side_effect=slow_cli):
            models, efforts = await APP.discover_codex_models(APP.FALLBACK_MODELS_MAP, timeout=0.1)
        self.assertEqual(models, APP.FALLBACK_MODELS_MAP)
        self.assertEqual(efforts, {})
        self.assertIsNotNone(created[0].returncode)

    async def test_unavailable_or_malformed_catalog_keeps_fallback(self):
        with patch.object(APP.asyncio, "create_subprocess_exec", side_effect=OSError("CLI unavailable")):
            self.assertEqual(await APP.discover_codex_models(APP.FALLBACK_MODELS_MAP),
                             (APP.FALLBACK_MODELS_MAP, {}))
        proc = MagicMock()
        proc.stdin.drain = AsyncMock()
        proc.stdout.readline = AsyncMock(return_value=b'not json\n')
        proc.wait = AsyncMock(return_value=0)
        proc.returncode = 0
        with patch.object(APP.asyncio, "create_subprocess_exec", return_value=proc):
            self.assertEqual(await APP.discover_codex_models(APP.FALLBACK_MODELS_MAP),
                             (APP.FALLBACK_MODELS_MAP, {}))


if __name__ == "__main__":
    unittest.main()
