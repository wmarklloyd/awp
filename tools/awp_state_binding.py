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
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

PROFILE = "git-staged-tree-v1"
REVISION_PREFIX = "git-tree:"

# A project whose .gitignore has a gap around build/dependency caches can leave
# hundreds of thousands of paths untracked.  Recording all of them in a Capsule
# turned one real project's `.awp.md` into ~40MB (github issue: capsule bloat
# from un-gitignored Gradle/Go build-cache directories, Sept 2026) -- the tree
# identifier itself was still correct, but the *divergence report* embedded
# next to it was not bounded, so a project's own ignore-pattern gap became a
# capsule-processing cost paid by every later reader.  `_divergence` below caps
# each category and reports the true count instead of embedding it in full, so
# a gap like that fails loud (a small list plus an honest total) rather than
# quietly producing an unusably large capsule.
DEFAULT_DIVERGENCE_LIMIT = 2000
DIVERGENCE_LIMIT_ENV = "AWP_DIVERGENCE_LIMIT"


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


def _resolve_divergence_limit(explicit: int | None) -> int:
    """Resolve the per-category divergence cap.

    Precedence: an explicit argument, then the AWP_DIVERGENCE_LIMIT
    environment variable, then DEFAULT_DIVERGENCE_LIMIT.  An override that
    fails to parse or is not positive is ignored rather than disabling the
    cap silently -- a typo in the environment should not reopen the failure
    mode this guards against.
    """
    if explicit is not None:
        return explicit
    raw = os.environ.get(DIVERGENCE_LIMIT_ENV)
    if raw:
        try:
            value = int(raw)
        except ValueError:
            value = 0
        if value > 0:
            return value
    return DEFAULT_DIVERGENCE_LIMIT


def _divergence(
    project: Path,
    scope: Sequence[str],
    excluded: Sequence[str] = (),
    limit: int | None = None,
) -> dict[str, Any]:
    """Report tracked-but-unstaged and untracked paths inside `scope`.

    A declared scope is pushed down to Git as a pathspec.  Scanning for
    untracked files costs time proportional to the working tree, which in a
    build-heavy repository is minutes rather than seconds; bounded by a
    pathspec it costs what the scope is worth.  The result is filtered again in
    Python so the answer does not depend on pathspec interpretation.

    Each category (`unstaged`, `untracked`) is capped at `limit` paths (see
    DEFAULT_DIVERGENCE_LIMIT).  Beyond the cap, the list is truncated but the
    true count is still reported as `<category>_total`, with
    `<category>_truncated: True` -- so a project whose ignore rules have a gap
    (an un-gitignored build cache, a vendored dependency tree) produces a
    small, bounded report with an honest count attached, instead of a
    divergence list sized to its whole working tree.
    """
    pathspec = ["--", *scope] if scope else []
    cap = _resolve_divergence_limit(limit)
    result: dict[str, Any] = {}
    for key, args in (
        ("unstaged", ("diff", "--name-only", *pathspec)),
        ("untracked", ("ls-files", "--others", "--exclude-standard", *pathspec)),
    ):
        values = sorted(
            line
            for line in _git(project, *args).splitlines()
            if line and _in_scope(line, scope) and line not in excluded
        )
        total = len(values)
        if total > cap:
            result[key] = values[:cap]
            result[f"{key}_total"] = total
            result[f"{key}_truncated"] = True
        else:
            result[key] = values
    return result


def staged_tree_binding(
    project: Path,
    state_space: str,
    scope: Sequence[str] | None = None,
    excludes: Sequence[str] | None = None,
    divergence_limit: int | None = None,
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

    `divergence_limit` bounds how many unstaged/untracked paths per category
    the `divergence` block records (default DEFAULT_DIVERGENCE_LIMIT, override
    via AWP_DIVERGENCE_LIMIT).  It bounds the report, never the identifier: a
    project with an ignore-pattern gap that leaves huge numbers of files
    untracked still gets a correct tree object, just not a Capsule sized to
    its whole working tree.
    """
    if not isinstance(state_space, str) or not state_space.strip():
        raise StateBindingError("state_space must be a nonempty string")
    if not _is_repository(project):
        raise StateBindingError("project is not inside a Git work tree")
    normalized = _normalize_scope(scope)
    excluded = _normalize_scope(excludes)
    divergence = _divergence(project, normalized, excluded, divergence_limit)
    unstaged = divergence["unstaged"]
    untracked = divergence["untracked"]
    unstaged_present = bool(unstaged) or bool(divergence.get("unstaged_total"))
    binding: dict[str, Any] = {
        "state_space": state_space.strip(),
        "revision": REVISION_PREFIX + staged_tree(project),
        "profile": PROFILE,
        "covers": "staged-index",
        "working_tree": "clean" if not unstaged_present else "modified",
        "retention": "pre-commit: the staged tree is unreachable until a commit names it",
    }
    if normalized:
        binding["scope"] = normalized
    if excluded:
        binding["excludes"] = excluded
    truncated = divergence.get("unstaged_truncated") or divergence.get("untracked_truncated")
    if unstaged_present or untracked or divergence.get("untracked_total"):
        binding["divergence"] = {key: value for key, value in divergence.items() if value}
        if truncated:
            print(
                "awp_state_binding: divergence truncated for state_space "
                f"{state_space.strip()!r} "
                f"(unstaged {len(unstaged)}/{divergence.get('unstaged_total', len(unstaged))}, "
                f"untracked {len(untracked)}/{divergence.get('untracked_total', len(untracked))}); "
                "the recorded tree is still correct, but this project has an "
                "ignore-pattern gap worth fixing -- see divergence.*_total in "
                "the binding, or override with AWP_DIVERGENCE_LIMIT.",
                file=sys.stderr,
            )
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
    if any(
        divergence.get(key)
        for key in ("unstaged", "untracked", "unstaged_truncated", "untracked_truncated")
    ):
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
    stage_command.add_argument(
        "--divergence-limit",
        type=int,
        default=None,
        help=(
            "cap on unstaged/untracked paths recorded per category "
            f"(default {DEFAULT_DIVERGENCE_LIMIT}, or ${DIVERGENCE_LIMIT_ENV})"
        ),
    )
    verify_command = commands.add_parser("verify", help="compare a recorded binding with this repository")
    verify_command.add_argument("--binding", type=Path, help="file holding the binding JSON; omit to read stdin")
    return root


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        project = args.project.resolve()
        if args.command == "stage":
            result = staged_tree_binding(
                project,
                args.state_space,
                args.scope,
                args.exclude,
                args.divergence_limit,
            )
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
