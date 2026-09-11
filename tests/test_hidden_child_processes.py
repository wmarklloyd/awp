"""Guard: every child process an AWP tool starts must be hidden on Windows.

Background AWP processes (the supervisor, watchers, hooks) run without a
console. On Windows any console program they start (git, codex, python) then
gets its own visible window, which flashes on the user's desktop. The
Codex-specific watcher solved this; the generic supervisor later dropped the
fix and the windows came back. This test fails on any new subprocess call in
tools/ that does not pass creationflags or a ``hidden_process_options()``
expansion, so the lesson cannot be lost again silently.
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
SPAWN = {"run", "Popen", "check_output", "check_call", "call"}


def _spawns(call: ast.Call) -> bool:
    func = call.func
    if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and func.value.id == "subprocess":
        return func.attr in SPAWN
    if isinstance(func, ast.Name):
        return func.id == "runner"
    return isinstance(func, ast.Attribute) and func.attr == "runner"


def _hidden(call: ast.Call) -> bool:
    for keyword in call.keywords:
        if keyword.arg == "creationflags":
            return True
        if keyword.arg is None and "hidden_process_options" in ast.unparse(keyword.value):
            return True
    return False


class HiddenChildProcessGuard(unittest.TestCase):
    def test_every_tool_subprocess_is_started_hidden(self) -> None:
        unhidden = []
        for path in sorted(TOOLS.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and _spawns(node) and not _hidden(node):
                    unhidden.append(f"{path.name}:{node.lineno}")
        self.assertEqual(unhidden, [], "start these child processes with **hidden_process_options()")


if __name__ == "__main__":
    unittest.main()
