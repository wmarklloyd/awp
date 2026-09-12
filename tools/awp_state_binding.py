"""Staged-index state bindings for AWP Handoff `git-staged-tree-v1`.

A Resume `state_binding` that names a commit cannot be produced before the
commit exists, so hosts commit and then amend, rewriting the very revision a
receiver may already have read.  Handoff 0.5.0 section 10 defines the
`git-staged-tree-v1` adapter profile instead: the binding names the tree object
recorded by the producer's staged index.

That identifier is computable before the commit and survives it unchanged --
when the index does not move between staging and committing, the resulting
commit's tree *is* that object -- so one value is verifiable on both sides of
the commit.  It names content, not history: a match establishes that the same
tree is present, never that it was committed or is reachable.

This module computes and verifies such bindings.  It does not decide whether a
binding may be published, and it never reports a working tree clean on the
producer's say-so: divergence is measured, not asserted.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

PROFILE = "git-staged-tree-v1"
REVISION_PREFIX = "git-tree:"


class StateBindingError(RuntimeError):
    """The binding could not be computed or compared."""


def _git(project: Path, *args: str, check: bool = True) -> str:
    """Run one Git command in `project` and return its stripped stdout."""
    try:
        completed = subprocess.run(
            ["git", "--no-optional-locks", *args],
            cwd=str(project),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError as error:  # Git is not installed on this host.
        raise StateBindingError("git is unavailable on this host") from error
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise StateBindingError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def _is_repository(project: Path) -> bool:
    try:
        return _git(project, "rev-parse", "--is-inside-work-tree") == "true"
    except StateBindingError:
        return False


def _normalize_scope(scope: Sequence[str] | None) -> list[str]:
    if not scope:
        return []
    normalized = []
    for entry in scope:
        if not isinstance(entry, str) or not entry.strip():
            raise StateBindingError("scope entries must be nonempty strings")
        normalized.append(entry.strip().replace("\\", "/").lstrip("./"))
    return normalized


def _in_scope(path: str, scope: Sequence[str]) -> bool:
    """Repository-relative, case-sensitive prefix match (awp-repository-path-v1)."""
    if not scope:
        return True
    for entry in scope:
        prefix = entry if entry.endswith("/") else entry + "/"
        if path == entry or path.startswith(prefix):
            return True
    return False


def _tree_difference(project: Path, left: str, right: str) -> list[str] | None:
    """Paths that differ between two tree objects, or None when uncomparable."""
    try:
        output = _git(project, "diff", "--name-only", left, right)
    except StateBindingError:
        return None
    return sorted(line for line in output.splitlines() if line)


def staged_tree(project: Path) -> str:
    """Return the tree object identifier recorded by the staged index.

    `git write-tree` reads the index, never the working tree or a branch, which
    is what AWP-HANDOFF-022 requires.  It writes the tree object so the
    identifier is resolvable; the object stays unreachable until a commit names
    it, which is the retention limitation AWP-HANDOFF-025 makes the producer
    disclose.
    """
    return _git(project, "write-tree")


def head_tree(project: Path) -> str | None:
    """Return HEAD's tree object identifier, or None on an unborn branch."""
    try:
        return _git(project, "rev-parse", "--verify", "--quiet", "HEAD^{tree}") or None
    except StateBindingError:
        return None


def _divergence(project: Path, scope: Sequence[str]) -> dict[str, list[str]]:
    """Report tracked-but-unstaged and untracked paths inside `scope`.

    A declared scope is pushed down to Git as a pathspec.  Scanning for
    untracked files costs time proportional to the working tree, which in a
    build-heavy repository is minutes rather than seconds; bounded by a
    pathspec it costs what the scope is worth.  The result is filtered again in
    Python so the answer does not depend on pathspec interpretation.
    """
    pathspec = ["--", *scope] if scope else []
    unstaged = [
        line
        for line in _git(project, "diff", "--name-only", *pathspec).splitlines()
        if line and _in_scope(line, scope)
    ]
    untracked = [
        line
        for line in _git(
            project, "ls-files", "--others", "--exclude-standard", *pathspec
        ).splitlines()
        if line and _in_scope(line, scope)
    ]
    return {"unstaged": sorted(unstaged), "untracked": sorted(untracked)}


def staged_tree_binding(
    project: Path,
    state_space: str,
    scope: Sequence[str] | None = None,
    excludes: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Build a `git-staged-tree-v1` state binding for the current index.

    The recorded identifier always covers the whole staged index; `scope`
    narrows the claims the binding carries, never what the identifier covers
    (AWP-HANDOFF-023).

    `excludes` carries the paths whose content depends on the identifier itself
    -- above all the Capsule that will hold the binding, which cannot be inside
    the tree it names.  A receiver treats a commit that differs only at those
    paths as current (AWP-HANDOFF-030).  It is not a way to leave a work product
    out of the binding.
    """
    if not isinstance(state_space, str) or not state_space.strip():
        raise StateBindingError("state_space must be a nonempty string")
    if not _is_repository(project):
        raise StateBindingError("project is not inside a Git work tree")
    normalized = _normalize_scope(scope)
    excluded = _normalize_scope(excludes)
    divergence = _divergence(project, normalized)
    unstaged = [path for path in divergence["unstaged"] if path not in excluded]
    untracked = [path for path in divergence["untracked"] if path not in excluded]
    binding: dict[str, Any] = {
        "state_space": state_space.strip(),
        "revision": REVISION_PREFIX + staged_tree(project),
        "profile": PROFILE,
        "covers": "staged-index",
        "working_tree": "clean" if not unstaged else "modified",
        "retention": "pre-commit: the staged tree is unreachable until a commit names it",
    }
    if normalized:
        binding["scope"] = normalized
    if excluded:
        binding["excludes"] = excluded
    if unstaged or untracked:
        binding["divergence"] = {
            key: value
            for key, value in (("unstaged", unstaged), ("untracked", untracked))
            if value
        }
    return binding


def verify_binding(project: Path, binding: dict[str, Any]) -> dict[str, Any]:
    """Compare a recorded staged-tree binding with this repository.

    A receiver accepts either an identical recomputed staged tree or a commit
    whose tree equals the recorded identifier (AWP-HANDOFF-024), so a checkpoint
    written before its commit does not read as stale afterwards.
    """
    if not isinstance(binding, dict):
        raise StateBindingError("binding must be an object")
    if binding.get("profile") != PROFILE:
        return {"profile": PROFILE, "state": "unavailable", "reason": "binding declares another adapter profile"}
    revision = binding.get("revision")
    if not isinstance(revision, str) or not revision.startswith(REVISION_PREFIX):
        return {"profile": PROFILE, "state": "unavailable", "reason": "revision is not a git-tree identifier"}
    recorded = revision[len(REVISION_PREFIX):]
    if not _is_repository(project):
        return {"profile": PROFILE, "state": "unverifiable", "reason": "project is not inside a Git work tree"}
    try:
        current_staged = staged_tree(project)
    except StateBindingError as error:
        return {"profile": PROFILE, "state": "unverifiable", "reason": str(error)}
    current_head = head_tree(project)
    present = _git(project, "cat-file", "-e", recorded + "^{tree}", check=False) == ""
    result: dict[str, Any] = {
        "profile": PROFILE,
        "recorded_tree": recorded,
        "staged_tree": current_staged,
        "head_tree": current_head,
        "object_present": present,
    }
    excluded = _normalize_scope(binding.get("excludes"))
    if recorded == current_staged:
        result["state"] = "current"
        result["matched"] = "staged-index"
    elif current_head is not None and recorded == current_head:
        result["state"] = "current"
        result["matched"] = "commit-tree"
    else:
        differing = _tree_difference(project, recorded, current_head) if present and current_head else None
        if differing is not None and differing and all(path in excluded for path in differing):
            # The commit differs only where the Capsule recorded its own binding.
            result["state"] = "current"
            result["matched"] = "commit-tree-modulo-excludes"
            result["excluded_differences"] = differing
        else:
            result["state"] = "stale"
            result["matched"] = None
            if differing:
                result["differing_paths"] = differing[:50]
    scope = _normalize_scope(binding.get("scope"))
    divergence = _divergence(project, scope)
    if divergence["unstaged"] or divergence["untracked"]:
        result["divergence"] = {
            key: value for key, value in divergence.items() if value
        }
    return result


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--project", type=Path, default=Path.cwd())
    commands = root.add_subparsers(dest="command", required=True)
    stage_command = commands.add_parser("stage", help="compute a binding for the staged index")
    stage_command.add_argument("--state-space", required=True)
    stage_command.add_argument("--scope", action="append", default=[])
    stage_command.add_argument(
        "--exclude",
        action="append",
        default=[],
        help="path whose content depends on the identifier itself, such as the capsule holding the binding",
    )
    verify_command = commands.add_parser("verify", help="compare a recorded binding with this repository")
    verify_command.add_argument("--binding", type=Path, help="file holding the binding JSON; omit to read stdin")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        project = args.project.resolve()
        if args.command == "stage":
            result = staged_tree_binding(project, args.state_space, args.scope, args.exclude)
        else:
            raw = args.binding.read_text(encoding="utf-8") if args.binding else sys.stdin.read()
            result = verify_binding(project, json.loads(raw))
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("state") not in {"stale", "unverifiable"} else 2
    except (StateBindingError, OSError, ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"profile": PROFILE, "state": "rejected", "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
