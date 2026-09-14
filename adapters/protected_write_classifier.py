"""Detect whether a tool call is about to write into a path a project has
declared protected, shared by the claude-code-hooks and codex-hooks
bindings (and any future host binding) so classification logic lives in one
place, not duplicated per host.

Why this exists instead of a fixed tool_name -> operation_class table: the
original design (config.json's `mappings` list, still supported below as an
optional override) requires knowing, in advance, the exact tool_name a host
reports for a given kind of call -- e.g. an image-generation tool. In
deployment that name is not always confirmed (a project may never learn the
real tool_name its agent host used for a particular capability), and some
hosts report a generic tool_name for locally-executed calls regardless of
what the command actually does (see adapters/codex-hooks/README.md for a
concrete case: Codex's PreToolUse/PostToolUse are documented to report
"Bash"/"exec_command" for local tool calls irrespective of intent). A
name-keyed table is therefore fragile in general, not just for one host.
This module instead asks a more robust question: regardless of which tool
or host is calling, does this operation's target path match something this
project protects? `mappings` in a binding's config.json still works as an
optional, more precise override when a tool_name is confirmed -- both
pretooluse.py bindings try that first and fall back to this classifier.

Fail-closed default, per action-boundary.md's own principle ("ambiguous
applicability must fail closed"): a hook cannot know in advance whether a
write will *invent* content (generative:freeform, gated) or faithfully
*reproduce* an already-verified source (generative:composite, permitted
once a matching artifact-claim exists). Every match here is classified
freeform UNLESS the operation is unambiguously a plain file copy (`cp`,
`copy`, `Copy-Item`) -- everything else that touches a protected path is
gated. This hook can only *recommend* a decision to the acting participant;
the real backstop, regardless of what this classifies, is
tools/awp_ci_gate.py run in CI, which requires an actual artifact-claim
record before any protected file can land.
"""

from __future__ import annotations

import re
from typing import Any

_PATH_ARG_CANDIDATES = ("file_path", "path", "target_path", "output_path", "notebook_path")

_COPY_COMMAND = re.compile(r"\b(cp|copy|Copy-Item)\b", re.IGNORECASE)


def _glob_to_regex(glob_pattern: str) -> re.Pattern:
    """Translate a simple `*`-wildcard glob (as used in protected-paths.json)
    into a regex searched against forward-slash-normalized text. Not a full
    glob implementation -- `*` matches across path separators too, which is
    intentional here: the haystack is free text (a shell command, an
    argument value), not a single path component.
    """
    return re.compile(re.escape(glob_pattern).replace(r"\*", ".*"))


def classify(tool_name: str, tool_input: dict[str, Any], protected_paths: list[dict]) -> dict | None:
    """Return a classification dict (`operation_class`, `resource`,
    `artifact_class`, plus `matched_pattern`/`matched_tool_name` for
    diagnostics) if `tool_input` appears to target a protected path, else
    `None` (nothing protected matched -- caller should allow).

    `protected_paths` is the `protected_paths` list from a project's
    protected-paths.json: each entry has `path_globs` (a list of `*`-glob
    patterns) and `artifact_class`.
    """
    haystack_parts: list[str] = []
    for key in _PATH_ARG_CANDIDATES:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            haystack_parts.append(value)
    command = tool_input.get("command")
    if isinstance(command, str) and command:
        haystack_parts.append(command)
    if not haystack_parts:
        return None
    haystack = "\n".join(haystack_parts).replace("\\", "/")

    for entry in protected_paths:
        for pattern in entry.get("path_globs", []):
            if _glob_to_regex(pattern).search(haystack):
                operation_class = "generative:composite" if _COPY_COMMAND.search(haystack) else "generative:freeform"
                return {
                    "artifact_class": entry.get("artifact_class"),
                    "resource": pattern,
                    "operation_class": operation_class,
                    "matched_pattern": pattern,
                    "matched_tool_name": tool_name,
                }
    return None
