"""Wake bindings for the any-agent doorbell (Cooperation Contracts section 12).

A participant declares, in the COOP-2 ledger, each way it can be woken: its
class (W1 live session, W2 headless run, W3 hosted API, W4 forge mention, W5
principal notification), the adapter profile, the relay that serves it, an
acknowledgement window, a budget, non-secret parameters, and at most a secret
*reference*.  The relay (``tools/awp_relay.py``) turns those declarations into
wake attempts.

Executable commands and endpoints never come from the ledger.  A declaration
names a profile; the relay resolves that profile from its built-in table or
from relay-local configuration (``.awp-runtime/wake-adapters.json`` in the
clone, then ``~/.awp/wake-adapters.json``).  Secrets are resolved only on the
relay's machine, from ``env:NAME`` or ``file:~/.awp/secrets/NAME``.

CLI::

    python -m tools.awp_wake declare --actor actor:claude --class W3 --adapter claude-routine \
        --param routine_id=trig_... --secret-ref file:~/.awp/secrets/claude-routine
    python -m tools.awp_wake list | reach | probe --binding wake:... | retire --binding wake:...
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
from typing import Any, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools.awp_activation import (CLIResumeAdapter, CommandAdapter, HostAdapter, activation_result,
                                      delivery_message, validate_envelope)
    from tools.awp_runtime import atomic_json, hidden_process_options
else:
    from .awp_activation import (CLIResumeAdapter, CommandAdapter, HostAdapter, activation_result,
                                 delivery_message, validate_envelope)
    from .awp_runtime import atomic_json, hidden_process_options


PROFILE = "awp-wake-binding-v1"
DECLARED = "coop2.binding.declared"
RETIRED = "coop2.binding.retired"
ESCALATED = "coop2.wake.escalated"
PRINCIPAL_NOTIFIED = "coop2.wake.principal_notified"
OUTCOME = "coop2.wake.outcome"
SUSPENDED = "coop2.wake.binding_suspended"
RESUMED = "coop2.wake.binding_resumed"
RELAY_ACTOR = "actor:awp-relay"
DEFAULT_RELAY = "relay:local"

CLASSES = ("W1", "W2", "W3", "W4", "W5")
DEFAULT_ACK_WINDOW = {"W1": 120, "W2": 600, "W3": 900, "W4": 3600, "W5": 0}
# Budgets bound runaway wakes and match vendor caps: runs per period.
DEFAULT_BUDGET = {
    "W1": {"runs": 60, "per_seconds": 3600},
    "W2": {"runs": 6, "per_seconds": 3600},
    "W3": {"runs": 10, "per_seconds": 86400},
    "W4": {"runs": 10, "per_seconds": 3600},
    "W5": {"runs": 20, "per_seconds": 3600},
}

# Headless runs start with the minimum needed to read the project and record
# receipt (section 12, bounded runs).  No option that grants unrestricted tool
# use is used.  ``{prompt}`` and ``{project}`` are substituted by the relay.
CLAUDE_MINIMAL_TOOLS = ["Read", "Grep", "Glob", "Bash(python -m tools.awp_ingress:*)",
                        "Bash(python -m tools.awp_coop2 inbox:*)"]
BUILTIN_PROFILES: dict[str, dict[str, Any]] = {
    "codex-queue": {"class": "W1", "kind": "cli-resume", "host": "codex"},
    "claude-print": {"class": "W2", "kind": "headless",
                     "command": ["claude", "-p", "{prompt}", "--permission-mode", "default",
                                 "--allowedTools", *CLAUDE_MINIMAL_TOOLS]},
    "codex-exec": {"class": "W2", "kind": "headless",
                   "command": ["codex", "exec", "--sandbox", "workspace-write", "--cd", "{project}", "{prompt}"]},
    "gemini-print": {"class": "W2", "kind": "headless", "command": ["gemini", "-p", "{prompt}"]},
    "claude-routine": {"class": "W3", "kind": "claude-routine"},
    "desktop-notify": {"class": "W5", "kind": "notify"},
    # A hosted agent that cannot be woken from outside but can schedule its own
    # wake-ups (Claude in Cowork) checks the ledger itself while it is active.
    "self-poll": {"class": "W1", "kind": "self-poll"},
    # Event-driven wake for a hosted agent: the relay publishes a content-free
    # signal ref to a remote the agent's own workspace can read, and a
    # background watcher there wakes the agent when that ref changes.
    "git-signal": {"class": "W1", "kind": "git-signal"},
}
ROUTINE_ENDPOINT = "https://api.anthropic.com/v1/claude_code/routines/"
ROUTINE_BETA = "experimental-cc-routine-2026-04-01"
SECRET_REF = re.compile(r"^(env:[A-Za-z_][A-Za-z0-9_]{0,63}|file:~/\.awp/secrets/[A-Za-z0-9._-]{1,64})$")
PARAM_KEY = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
TOKEN_LIKE = re.compile(r"(sk-ant-|Bearer\s|ghp_|github_pat_|xox[abp]-)", re.IGNORECASE)


class WakeError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str | None) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _git_config(project: Path, key: str) -> str | None:
    try:
        completed = subprocess.run(["git", "config", "--get", key], cwd=project, capture_output=True, text=True,
                                   check=False, timeout=15, **hidden_process_options())
    except (OSError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


def relay_id(project: Path) -> str:
    """This clone's relay identity: AWP_RELAY_ID, git config awp.relay.id, or relay:local."""
    return os.environ.get("AWP_RELAY_ID") or _git_config(project, "awp.relay.id") or DEFAULT_RELAY


def binding_id(actor: str, wake_class: str, adapter: str) -> str:
    return "wake:" + hashlib.sha256(f"{actor}\0{wake_class}\0{adapter}".encode()).hexdigest()[:16]


# -- declarations -------------------------------------------------------------

def validate_declaration(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("class") not in CLASSES:
        raise WakeError(f"class must be one of {', '.join(CLASSES)}")
    if not re.match(r"^[A-Za-z0-9._:-]{1,64}$", str(payload.get("adapter", ""))):
        raise WakeError("adapter must name a profile (letters, digits, . _ : -)")
    params = payload.get("params") or {}
    if not isinstance(params, dict):
        raise WakeError("params must be an object")
    for key, value in params.items():
        if not PARAM_KEY.match(key) or not isinstance(value, (str, int, bool)):
            raise WakeError(f"parameter {key!r} must be a short lowercase key with a scalar value")
        if TOKEN_LIKE.search(str(value)):
            raise WakeError(f"parameter {key!r} looks like a credential; use --secret-ref")
    secret = payload.get("secret_ref")
    if secret is not None and not SECRET_REF.match(str(secret)):
        raise WakeError("secret_ref must be env:NAME or file:~/.awp/secrets/NAME (a reference, never a value)")
    for key in ("ack_window_seconds",):
        if not isinstance(payload.get(key), int) or payload[key] < 0:
            raise WakeError(f"{key} must be a non-negative integer")
    budget = payload.get("budget") or {}
    if not (isinstance(budget.get("runs"), int) and budget["runs"] >= 0
            and isinstance(budget.get("per_seconds"), int) and budget["per_seconds"] > 0):
        raise WakeError("budget must have integer runs >= 0 and per_seconds > 0")
    return payload


def _default_window(wake_class: str, adapter: str, params: dict[str, Any] | None) -> int:
    if adapter == "self-poll":
        return int((params or {}).get("interval_seconds", SELF_POLL_SECONDS)) + 120
    return DEFAULT_ACK_WINDOW.get(wake_class, 600)


def declare(rendezvous: Any, actor: str, wake_class: str, adapter: str, *, relay: str | None = None,
            params: dict[str, Any] | None = None, secret_ref: str | None = None,
            ack_window_seconds: int | None = None, budget: dict[str, int] | None = None,
            order: int | None = None) -> dict[str, Any]:
    """Publish (or confirm) one binding declaration as the participant itself."""
    wake_class = wake_class.upper()
    order = order if order is not None else CLASSES.index(wake_class) * 10 if wake_class in CLASSES else 99
    payload = validate_declaration({
        "profile": PROFILE,
        "binding_id": binding_id(actor, wake_class, adapter),
        "actor": actor,
        "class": wake_class,
        "adapter": adapter,
        "relay": relay or relay_id(rendezvous.project),
        "params": dict(params or {}),
        "secret_ref": secret_ref,
        "ack_window_seconds": _default_window(wake_class, adapter, params) if ack_window_seconds is None else ack_window_seconds,
        "budget": dict(budget or DEFAULT_BUDGET.get(wake_class, {"runs": 6, "per_seconds": 3600})),
        "order": order,
    })
    events = rendezvous._events()
    if actor not in {event["payload"].get("actor") for event in events if event["kind"] == "coop2.participant.joined"}:
        rendezvous.join(actor, ["managed-collaboration"], "on-entry-only")
    current = active_bindings(events).get(payload["binding_id"])
    if current and {k: v for k, v in current.items() if k not in {"event_id", "declared_at"}} == payload:
        return {"binding": current, "publication": "confirmed", "deduplicated": True}
    receipt = rendezvous._append(actor, DECLARED, payload)
    return {"binding": payload | {"event_id": receipt["event_id"]}, "publication": "confirmed",
            "deduplicated": False, "receipt": receipt}


# Wake paths an agent gets without anyone configuring anything: a new headless
# run when its command-line tool is installed on this machine, and a desktop
# notification to the principal as the last resort.  (A live-session binding
# is declared by session activation, which knows the session.)
SELF_POLL_SECONDS = 120
HOSTED_HOSTS = {"cowork"}
SIGNAL_REF = re.compile(r"^refs/awp/wake/[a-z0-9-]{4,64}$")
HEADLESS_BY_HOST = {"codex": ("codex-exec", "codex"), "claude": ("claude-print", "claude"),
                    "claude-code": ("claude-print", "claude"), "gemini": ("gemini-print", "gemini")}


def signal_ref(actor: str) -> str:
    return "refs/awp/wake/" + hashlib.sha256(actor.encode()).hexdigest()[:16]


def signal_remote_url(project: Path | None) -> str | None:
    """An https URL for the wake-signal remote, readable without credentials."""
    if project is None:
        return None
    url = _git_config(project, "awp.wake.url")
    if not url:
        try:
            completed = subprocess.run(["git", "remote", "get-url", "origin"], cwd=project, capture_output=True,
                                       text=True, check=False, timeout=15, **hidden_process_options())
            url = completed.stdout.strip() if completed.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            url = None
    if url and url.startswith("git@github.com:"):
        url = "https://github.com/" + url.split(":", 1)[1]
    return url if url and url.startswith("https://") else None


def automatic_bindings(host: str | None, which: Callable[[str], str | None] = shutil.which,
                       project: Path | None = None, actor: str | None = None) -> list[tuple[str, str, dict[str, Any] | None]]:
    result: list[tuple[str, str, dict[str, Any] | None]] = []
    if (host or "").lower() in HOSTED_HOSTS:
        url = signal_remote_url(project)
        if url and actor:
            result.append(("W1", "git-signal", {"signal_ref": signal_ref(actor), "remote_url": url}))
        else:
            result.append(("W1", "self-poll", {"interval_seconds": SELF_POLL_SECONDS}))
    headless = HEADLESS_BY_HOST.get((host or "").lower())
    if headless and which(headless[1]):
        result.append(("W2", headless[0], None))
    result.append(("W5", "desktop-notify", None))
    return result


def enter(rendezvous: Any, actor: str, host: str | None = None,
          which: Callable[[str], str | None] = shutil.which) -> dict[str, Any]:
    """Declare this agent's automatic wake bindings on project entry (idempotent).

    Nothing is asked of the user: whatever this environment offers is declared,
    the relay verifies it by probe, and whatever cannot wake the agent is
    disclosed in the reach report.
    """
    declared = []
    for wake_class, adapter, params in automatic_bindings(host, which, Path(rendezvous.project), actor):
        result = declare(rendezvous, actor, wake_class, adapter, params=params)
        declared.append({"class": wake_class, "adapter": adapter, "binding_id": result["binding"]["binding_id"],
                         "new": not result["deduplicated"]})
    best = reach(rendezvous._events(), actor)["participants"].get(actor, {}).get("best")
    return {"profile": PROFILE, "actor": actor, "declared": declared, "best": best}


def retire(rendezvous: Any, actor: str, binding: str, reason: str = "retired by participant") -> dict[str, Any]:
    current = active_bindings(rendezvous._events()).get(binding)
    if current is None:
        raise WakeError("unknown or already retired binding")
    if current["actor"] != actor:
        raise WakeError("only the declaring participant may retire its binding")
    receipt = rendezvous._append(actor, RETIRED, {"binding_id": binding, "actor": actor, "reason": reason[:200]})
    return {"binding_id": binding, "publication": "confirmed", "receipt": receipt}


def active_bindings(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Latest declaration per binding, minus retired ones, in ledger order."""
    result: dict[str, dict[str, Any]] = {}
    for event in events:
        payload = event.get("payload", {})
        if event["kind"] == DECLARED and payload.get("actor") == event.get("actor"):
            try:
                validate_declaration(dict(payload))
            except WakeError:
                continue
            result[payload["binding_id"]] = dict(payload) | {"event_id": event["event_id"],
                                                             "declared_at": event.get("occurred_at")}
        elif event["kind"] == RETIRED and payload.get("actor") == event.get("actor"):
            existing = result.get(payload.get("binding_id"))
            if existing and existing["actor"] == event.get("actor"):
                result.pop(payload["binding_id"], None)
    return result


def ladder(bindings: dict[str, dict[str, Any]], actor: str, relay: str | None = None) -> list[dict[str, Any]]:
    """The recipient's bindings in declared order (W5 last), optionally for one relay."""
    items = [item for item in bindings.values() if item["actor"] == actor and (relay is None or item["relay"] == relay)]
    return sorted(items, key=lambda item: (item["class"] == "W5", item["order"], item["class"], item["binding_id"]))


# -- reach --------------------------------------------------------------------

def reach(events: list[dict[str, Any]], actor: str | None = None, now: datetime | None = None) -> dict[str, Any]:
    """Measured reach per binding, and the best verified rung per participant.

    A binding counts as reach only after a probe through it (a tickle whose
    payload names ``probe_binding``) was acknowledged by its recipient.
    """
    now = now or utc_now()
    bindings = active_bindings(events)
    acks = {event["payload"].get("tickle_id"): event for event in events if event["kind"] == "coop2.tickle.acked"}
    suspended: dict[str, str | None] = {}
    for event in events:
        payload = event.get("payload", {})
        if event["kind"] == SUSPENDED:
            suspended[payload.get("binding_id")] = payload.get("reason")
        elif event["kind"] == RESUMED:
            suspended.pop(payload.get("binding_id"), None)
    rows: dict[str, dict[str, Any]] = {}
    for item in bindings.values():
        rows[item["binding_id"]] = {"binding_id": item["binding_id"], "actor": item["actor"], "class": item["class"],
                                    "adapter": item["adapter"], "relay": item["relay"], "order": item["order"],
                                    "reach": "unverified", "declared_at": item.get("declared_at")}
    for event in events:
        payload = event.get("payload", {})
        target = payload.get("probe_binding")
        if event["kind"] != "coop2.tickle.sent" or target not in rows:
            continue
        row = rows[target]
        declared = parse_time(row.get("declared_at"))
        sent = parse_time(event.get("occurred_at"))
        if declared and sent and sent < declared:
            continue  # a probe of an earlier declaration says nothing about this one
        ack = acks.get(payload.get("tickle_id"))
        if ack:
            acked = parse_time(ack.get("occurred_at"))
            row.update({"reach": "verified", "verified_at": ack.get("occurred_at"),
                        "latency_seconds": round((acked - sent).total_seconds(), 1) if acked and sent else None,
                        "acknowledged_via": ack["payload"].get("acknowledged_via")})
        elif sent and now > sent + timedelta(seconds=int(payload.get("ttl_seconds", 90))):
            row.update({"reach": "failed", "failed_at": iso(sent + timedelta(seconds=int(payload.get("ttl_seconds", 90))))})
        else:
            row.setdefault("probe_pending", event["event_id"])
    for key, reason in suspended.items():
        if key in rows:
            rows[key]["suspended"] = reason or "circuit breaker open"
    participants: dict[str, dict[str, Any]] = {}
    actors = sorted({event["payload"]["actor"] for event in events if event["kind"] == "coop2.participant.joined"})
    for name in actors:
        if actor and name != actor:
            continue
        mine = [rows[item["binding_id"]] for item in ladder(bindings, name)]
        live = [row for row in mine if row["reach"] == "verified" and not row.get("suspended") and row["class"] != "W5"]
        notify = [row for row in mine if row["class"] == "W5"]
        if live:
            best = {"rung": live[0]["class"], "binding_id": live[0]["binding_id"], "state": "wake-verified"}
        elif any(row["class"] != "W5" for row in mine):
            best = {"rung": "unverified", "state": "declared-unverified",
                    "note": "bindings are declared but none has passed a probe; delivery may still wake the recipient"}
        elif notify:
            best = {"rung": "W5", "binding_id": notify[0]["binding_id"], "state": "principal-notification"}
        else:
            best = {"rung": "W0", "state": "entry-only", "note": "no wake binding; received on the next project entry"}
        participants[name] = {"best": best, "bindings": mine}
    return {"profile": PROFILE, "participants": participants}


def outcome(events: list[dict[str, Any]], event_id: str) -> dict[str, Any]:
    """How one addressed event ended (or where its ladder is), for the sender."""
    source = next((event for event in events if event["event_id"] == event_id), None)
    if source is None:
        raise WakeError("unknown event")
    payload = source.get("payload", {})
    subject = payload.get("tickle_id") or payload.get("interaction_id")
    trail = []
    for event in events:
        item = event.get("payload", {})
        if item.get("event_id") == event_id or (event is not source and subject and
                                                  (item.get("tickle_id") == subject or item.get("interaction_id") == subject)):
            trail.append({"kind": event["kind"], "actor": event.get("actor"), "at": event.get("occurred_at"),
                          "binding_id": item.get("binding_id"), "state": item.get("transport_state") or item.get("outcome"),
                          "via": item.get("acknowledged_via") or item.get("observed_via"), "reason": item.get("reason")})
    receipt = next((row for row in trail if row["actor"] == payload.get("recipient") and row["kind"] in
                    {"coop2.tickle.acked", "coop2.interaction.observed", "coop2.interaction.accepted",
                     "coop2.interaction.refused", "coop2.interaction.responded"}), None)
    final = next((row for row in trail if row["kind"] in {OUTCOME, PRINCIPAL_NOTIFIED}), None)
    state = "received" if receipt else (final["state"] if final and final["kind"] == OUTCOME else
                                        "principal-notified" if final else "in-progress")
    return {"event_id": event_id, "recipient": payload.get("recipient"), "state": state, "trail": trail}


# -- secrets and local configuration -------------------------------------------

def resolve_secret(reference: str | None, environment: dict[str, str] | None = None,
                   home: Path | None = None) -> str | None:
    if not reference:
        return None
    if not SECRET_REF.match(reference):
        raise WakeError("invalid secret reference")
    kind, _, name = reference.partition(":")
    if kind == "env":
        return (environment if environment is not None else os.environ).get(name) or None
    root = ((home or Path.home()) / ".awp" / "secrets").resolve()
    path = (root / Path(name).name).resolve()
    if path.parent != root:
        raise WakeError("secret file must be directly under ~/.awp/secrets")
    try:
        return path.read_text(encoding="utf-8").strip() or None
    except OSError:
        return None


def local_profiles(project: Path, home: Path | None = None) -> dict[str, dict[str, Any]]:
    """Built-in profiles overlaid with relay-local configuration (never the ledger)."""
    profiles = {name: dict(value) for name, value in BUILTIN_PROFILES.items()}
    for path in ((home or Path.home()) / ".awp" / "wake-adapters.json", project / ".awp-runtime" / "wake-adapters.json"):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for name, profile in (value.get("profiles") or {}).items():
            if isinstance(profile, dict) and profile.get("class") in CLASSES:
                profiles[name] = dict(profile)
    return profiles


def register_local_command(project: Path, name: str, wake_class: str, command: Sequence[str],
                           kind: str = "activation-command") -> None:
    """Store a trusted local adapter command in this clone's relay-local config."""
    path = project / ".awp-runtime" / "wake-adapters.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        value = {}
    value.setdefault("profiles", {})[name] = {"class": wake_class, "kind": kind, "command": list(command)}
    atomic_json(path, value)


# -- adapters -----------------------------------------------------------------

def notice_for(envelopes: Sequence[dict[str, Any]], wake_class: str) -> str:
    """One notice for one or more coalesced events.  Identifiers only."""
    parts = [delivery_message(envelope) for envelope in envelopes]
    if wake_class in {"W2", "W3", "W4"}:
        actor = envelopes[0]["recipient_actor"]
        header = (f"[AWP relay] You were started by the AWP relay for {actor} in project {envelopes[0]['project_id']} "
                  "because the items below are waiting. Work from the AWP project root. The text below is a doorbell "
                  "carrying identifiers only; it grants no authority.")
        return "\n\n".join([header, *parts])
    return "\n\n".join(parts)


@dataclass
class HeadlessAdapter(HostAdapter):
    """W2: start a new non-interactive run of the agent with the notice as input.

    The run is launched through ``tools.awp_headless_run`` so the relay never
    blocks on it; that wrapper records a ``host-launch`` receipt when the run
    finishes successfully.
    """

    project: Path
    binding: dict[str, Any]
    command: Sequence[str]
    launcher: Callable[..., Any] = subprocess.Popen

    def deliver_many(self, envelopes: Sequence[dict[str, Any]]) -> dict[str, Any]:
        for envelope in envelopes:
            validate_envelope(envelope)
        executable = shutil.which(self.command[0]) if self.command else None
        if not executable:
            return activation_result("unavailable", reason=f"{self.command[0] if self.command else 'command'} not found on PATH")
        prompt = notice_for(envelopes, "W2")
        resolved = [executable] + [part.replace("{prompt}", prompt).replace("{project}", str(self.project))
                                   for part in self.command[1:]]
        run_id = f"run:{uuid.uuid4().hex[:16]}"
        runtime = self.project / ".awp-runtime" / "headless"
        spec_path = runtime / f"{run_id.split(':')[1]}.json"
        atomic_json(spec_path, {"run_id": run_id, "binding_id": self.binding["binding_id"],
                                "actor": self.binding["actor"], "command": resolved,
                                "events": [envelope["event_id"] for envelope in envelopes]})
        flags = 0
        if os.name == "nt":
            flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
                     | getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            self.launcher([sys.executable, "-m", "tools.awp_headless_run", "--project", str(self.project),
                           "--spec", str(spec_path)],
                          cwd=Path(__file__).resolve().parent.parent, stdin=subprocess.DEVNULL,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True,
                          creationflags=flags, start_new_session=os.name != "nt")
        except OSError as error:
            return activation_result("unavailable", reason=str(error)[:300])
        return activation_result("accepted", receipt=run_id)

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return self.deliver_many([envelope])

    def probe(self) -> dict[str, Any]:
        found = shutil.which(self.command[0]) if self.command else None
        return activation_result("accepted" if found else "unavailable",
                                 reason=None if found else f"{self.command[0] if self.command else 'command'} not found")


@dataclass
class RoutineAdapter(HostAdapter):
    """W3 for Claude: fire a routine's API trigger, which starts a new session.

    The endpoint is fixed to the Anthropic routines API; the routine id is a
    non-secret parameter; the bearer token is resolved from the secret
    reference on the relay's machine and never recorded.
    """

    binding: dict[str, Any]
    environment: dict[str, str] | None = None
    home: Path | None = None
    opener: Callable[..., Any] = urllib.request.urlopen

    def url(self) -> str:
        routine = str(self.binding.get("params", {}).get("routine_id", ""))
        if not re.match(r"^[A-Za-z0-9_-]{4,100}$", routine):
            raise WakeError("claude-routine binding needs params.routine_id")
        return f"{ROUTINE_ENDPOINT}{routine}/fire"

    def deliver_many(self, envelopes: Sequence[dict[str, Any]]) -> dict[str, Any]:
        for envelope in envelopes:
            validate_envelope(envelope)
        try:
            url = self.url()
            token = resolve_secret(self.binding.get("secret_ref"), self.environment, self.home)
        except WakeError as error:
            return activation_result("unavailable", reason=str(error))
        if not token:
            return activation_result("unavailable", reason=f"secret {self.binding.get('secret_ref')} is not set on the relay machine")
        body = json.dumps({"text": notice_for(envelopes, "W3")[:60000]}).encode()
        request = urllib.request.Request(url, data=body, method="POST", headers={
            "Authorization": f"Bearer {token}", "anthropic-beta": ROUTINE_BETA,
            "anthropic-version": "2023-06-01", "Content-Type": "application/json"})
        try:
            with self.opener(request, timeout=30) as response:
                value = json.loads(response.read().decode("utf-8") or "{}")
        except urllib.error.HTTPError as error:
            state = "deferred" if error.code in {429, 500, 502, 503, 529} else "unavailable"
            retry = error.headers.get("Retry-After") if error.headers else None
            return activation_result(state, reason=f"routine API returned HTTP {error.code}" + (f"; retry after {retry}s" if retry else ""))
        except (urllib.error.URLError, OSError, ValueError) as error:
            return activation_result("deferred", reason=f"routine API unreachable: {str(error)[:200]}")
        session = str(value.get("claude_code_session_id") or "")[:100]
        return activation_result("accepted", receipt=session or "routine-fired")

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return self.deliver_many([envelope])

    def probe(self) -> dict[str, Any]:
        try:
            self.url()
            token = resolve_secret(self.binding.get("secret_ref"), self.environment, self.home)
        except WakeError as error:
            return activation_result("unavailable", reason=str(error))
        return activation_result("accepted" if token else "unavailable", reason=None if token else "secret not set")


def _notification_text(envelopes: Sequence[dict[str, Any]]) -> str:
    agent = envelopes[0]["recipient_actor"].split(":", 1)[-1].capitalize()
    count = len(envelopes)
    what = "a consultation" if count == 1 else f"{count} items"
    return (f"{agent} has {what} waiting in this AWP project and could not be woken automatically. "
            f"Open {agent} in the project and say: check your AWP inbox.")


@dataclass
class NotifyAdapter(HostAdapter):
    """W5: tell the principal on the relay's machine.  Always logged."""

    project: Path
    runner: Callable[..., Any] = subprocess.run

    def deliver_many(self, envelopes: Sequence[dict[str, Any]]) -> dict[str, Any]:
        text = _notification_text(envelopes)
        log = self.project / ".awp-runtime" / "notifications.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"at": iso(utc_now()), "text": text,
                                     "events": [envelope["event_id"] for envelope in envelopes]}) + "\n")
        command = desktop_notification_command()
        shown = False
        if command:
            try:
                completed = self.runner(command, env={**os.environ, "AWP_NOTICE": text}, capture_output=True,
                                        text=True, timeout=20, check=False, **hidden_process_options())
                shown = completed.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                shown = False
        return activation_result("accepted", receipt="desktop-notification" if shown else "notifications.log")

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return self.deliver_many([envelope])

    def probe(self) -> dict[str, Any]:
        return activation_result("accepted", receipt="notifications.log")


@dataclass
class GitSignalAdapter(HostAdapter):
    """W1 for hosted agents: publish a content-free wake signal to a Git remote.

    The signal is a commit with an empty tree on ``refs/awp/wake/<actor
    token>``; its message names only the recipient and event identifiers. The
    push uses the relay machine's existing Git credentials and never prompts.
    The remote is relay-local configuration (``git config awp.wake.remote``,
    default ``origin``), never taken from the ledger.
    """

    project: Path
    binding: dict[str, Any]
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run

    def _git(self, *arguments: str, input_text: str | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never",
               "GIT_AUTHOR_NAME": "AWP relay", "GIT_AUTHOR_EMAIL": "awp-relay@localhost",
               "GIT_COMMITTER_NAME": "AWP relay", "GIT_COMMITTER_EMAIL": "awp-relay@localhost"}
        return self.runner(["git", *arguments], cwd=self.project, input=input_text, capture_output=True, text=True,
                           timeout=timeout, check=False, env=env, **hidden_process_options())

    def deliver_many(self, envelopes: Sequence[dict[str, Any]]) -> dict[str, Any]:
        for envelope in envelopes:
            validate_envelope(envelope)
        ref = str(self.binding.get("params", {}).get("signal_ref", ""))
        if not SIGNAL_REF.match(ref):
            return activation_result("unavailable", reason="git-signal binding needs params.signal_ref under refs/awp/wake/")
        remote = _git_config(self.project, "awp.wake.remote") or "origin"
        try:
            tree = self._git("mktree", input_text="").stdout.strip()
            parent = self._git("rev-parse", "--verify", "--quiet", ref)
            message = "AWP wake " + envelopes[0]["recipient_actor"] + " " + " ".join(e["event_id"] for e in envelopes)
            arguments = ["commit-tree", tree, "-m", message]
            if parent.returncode == 0 and parent.stdout.strip():
                arguments[2:2] = ["-p", parent.stdout.strip()]
            commit = self._git(*arguments)
            if commit.returncode != 0 or not tree:
                return activation_result("unavailable", reason=(commit.stderr or "could not create signal")[:300])
            sha = commit.stdout.strip()
            self._git("update-ref", ref, sha)
            pushed = self._git("push", "--quiet", remote, f"+{ref}:{ref}", timeout=60)
        except (OSError, subprocess.TimeoutExpired) as error:
            return activation_result("deferred", reason=f"signal push failed: {str(error)[:200]}")
        if pushed.returncode != 0:
            return activation_result("deferred", reason=f"signal push failed: {(pushed.stderr or '').strip()[:300]}")
        return activation_result("accepted", receipt=sha[:12])

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return self.deliver_many([envelope])

    def probe(self) -> dict[str, Any]:
        return activation_result("accepted", receipt="git-signal")


class SelfPollAdapter(HostAdapter):
    """The recipient checks the ledger itself on a timer; nothing is sent.

    The relay still records the attempt and waits the binding's window (the
    poll interval plus a margin) for the recipient's receipt, then escalates.
    """

    def deliver_many(self, envelopes: Sequence[dict[str, Any]]) -> dict[str, Any]:
        return activation_result("accepted", receipt="awaiting-recipient-poll")

    def deliver(self, envelope: dict[str, Any]) -> dict[str, Any]:
        return self.deliver_many([envelope])

    def probe(self) -> dict[str, Any]:
        return activation_result("accepted", receipt="awaiting-recipient-poll")


def pending(events: list[dict[str, Any]], actor: str, now: datetime | None = None) -> list[dict[str, Any]]:
    """Items addressed to ``actor`` that still need its receipt, oldest first."""
    now = now or utc_now()
    acked = {event["payload"].get("tickle_id") for event in events if event["kind"] == "coop2.tickle.acked"}
    closed = {event["payload"].get("interaction_id") for event in events
              if event["kind"] == "coop2.interaction.withdrawn"
              or (event["kind"] in {"coop2.interaction.observed", "coop2.interaction.accepted", "coop2.interaction.refused",
                                    "coop2.interaction.responded"} and event.get("actor") == actor)}
    result = []
    for event in events:
        payload = event.get("payload", {})
        if payload.get("recipient") != actor:
            continue
        if event["kind"] == "coop2.tickle.sent" and payload.get("tickle_id") not in acked:
            sent = parse_time(event.get("occurred_at"))
            if sent and now > sent + timedelta(seconds=int(payload.get("ttl_seconds", 90))):
                continue
            result.append({"event_id": event["event_id"], "kind": "probe", "from": payload.get("sender")})
        elif event["kind"] == "coop2.interaction.requested" and payload.get("interaction_id") not in closed:
            result.append({"event_id": event["event_id"], "kind": "consultation", "from": payload.get("sender"),
                           "interaction_id": payload.get("interaction_id"), "subject": payload.get("subject")})
    return result


def suggested_ttl(events: list[dict[str, Any]], recipient: str, minimum: int = 90) -> int:
    """A probe TTL long enough for the recipient's first wake rung to answer."""
    rungs = [item for item in ladder(active_bindings(events), recipient) if item["class"] != "W5"]
    return max(minimum, int(rungs[0]["ack_window_seconds"]) + 30) if rungs else minimum


WINDOWS_TOAST = (
    "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null;"
    "$t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);"
    "$x = $t.GetElementsByTagName('text'); $x.Item(0).AppendChild($t.CreateTextNode('AWP')) > $null;"
    "$x.Item(1).AppendChild($t.CreateTextNode($env:AWP_NOTICE)) > $null;"
    "$n = [Windows.UI.Notifications.ToastNotification]::new($t);"
    "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
    "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($n)"
)


def desktop_notification_command() -> list[str] | None:
    """The notice text travels in AWP_NOTICE, never in the command line."""
    if os.name == "nt":
        shell = shutil.which("powershell") or shutil.which("pwsh")
        return [shell, "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-Command", WINDOWS_TOAST] if shell else None
    if sys.platform == "darwin" and shutil.which("osascript"):
        return ["osascript", "-e", 'display notification (system attribute "AWP_NOTICE") with title "AWP"']
    if shutil.which("notify-send"):
        return ["sh", "-c", 'notify-send AWP "$AWP_NOTICE"']
    return None


def adapter_for(binding: dict[str, Any], project: Path, profiles: dict[str, dict[str, Any]] | None = None,
                environment: dict[str, str] | None = None) -> HostAdapter:
    profiles = profiles if profiles is not None else local_profiles(project)
    profile = profiles.get(binding["adapter"])
    if profile is None:
        raise WakeError(f"adapter profile {binding['adapter']!r} is not configured on this relay")
    if profile["class"] != binding["class"]:
        raise WakeError(f"adapter profile {binding['adapter']!r} is class {profile['class']}, not {binding['class']}")
    kind = profile.get("kind")
    params = binding.get("params") or {}
    if kind == "cli-resume":
        session = str(params.get("session_ref") or "")
        if not session:
            raise WakeError("a live-session binding needs params.session_ref")
        return CLIResumeAdapter(profile.get("host", "codex"), session, profile.get("command"))
    if kind == "activation-command":
        return CommandAdapter(list(profile["command"]))
    if kind == "headless":
        return HeadlessAdapter(project, binding, list(profile["command"]))
    if kind == "claude-routine":
        return RoutineAdapter(binding, environment)
    if kind == "notify":
        return NotifyAdapter(project)
    if kind == "self-poll":
        return SelfPollAdapter()
    if kind == "git-signal":
        return GitSignalAdapter(project, binding)
    raise WakeError(f"adapter kind {kind!r} is not supported by this relay")


# -- CLI ------------------------------------------------------------------------

def _params(values: Sequence[str]) -> dict[str, str]:
    result = {}
    for item in values:
        key, separator, value = item.partition("=")
        if not separator:
            raise WakeError(f"--param expects key=value, got {item!r}")
        result[key.strip()] = value.strip()
    return result


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument("--project", type=Path, default=Path.cwd())
    commands = result.add_subparsers(dest="command", required=True)
    item = commands.add_parser("declare", help="declare (or re-confirm) a wake binding for a participant")
    item.add_argument("--actor", required=True)
    item.add_argument("--class", dest="wake_class", required=True, choices=CLASSES)
    item.add_argument("--adapter", required=True, help="profile name: " + ", ".join(BUILTIN_PROFILES))
    item.add_argument("--relay")
    item.add_argument("--param", action="append", default=[], help="non-secret key=value")
    item.add_argument("--secret-ref", help="env:NAME or file:~/.awp/secrets/NAME")
    item.add_argument("--ack-window-seconds", type=int)
    item.add_argument("--budget-runs", type=int)
    item.add_argument("--budget-per-seconds", type=int)
    item.add_argument("--order", type=int)
    item = commands.add_parser("enter", help="declare this agent's automatic wake bindings (run on project entry)")
    item.add_argument("--actor", required=True); item.add_argument("--host")
    item = commands.add_parser("pending", help="items waiting for an agent's receipt; --ack records receipt for each")
    item.add_argument("--actor", required=True); item.add_argument("--ack", action="store_true")
    item = commands.add_parser("retire"); item.add_argument("--actor", required=True); item.add_argument("--binding", required=True)
    item.add_argument("--reason", default="retired by participant")
    item = commands.add_parser("list"); item.add_argument("--actor")
    item = commands.add_parser("reach"); item.add_argument("--actor")
    item = commands.add_parser("probe", help="send a reachability probe through one binding")
    item.add_argument("--binding", required=True); item.add_argument("--ttl-seconds", type=int)
    item = commands.add_parser("outcome", help="how one addressed event ended"); item.add_argument("--event", required=True)
    return result


def probe(rendezvous: Any, binding: str, ttl_seconds: int | None = None, key: str | None = None) -> dict[str, Any]:
    current = active_bindings(rendezvous._events()).get(binding)
    if current is None:
        raise WakeError("unknown or retired binding")
    ttl = ttl_seconds or max(int(current["ack_window_seconds"]) + 60, 90)
    return rendezvous.tickle(RELAY_ACTOR, current["actor"], ttl_seconds=ttl,
                             idempotency_key=key or f"probe:{binding}:{uuid.uuid4().hex[:8]}", probe_binding=binding)


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    from tools.awp_coop2 import Rendezvous  # deferred: keeps adapters importable without a project

    rendezvous = Rendezvous(args.project.resolve())
    try:
        if args.command == "declare":
            budget = None
            if args.budget_runs is not None or args.budget_per_seconds is not None:
                default = DEFAULT_BUDGET[args.wake_class]
                budget = {"runs": args.budget_runs if args.budget_runs is not None else default["runs"],
                          "per_seconds": args.budget_per_seconds or default["per_seconds"]}
            result = declare(rendezvous, args.actor, args.wake_class, args.adapter, relay=args.relay,
                             params=_params(args.param), secret_ref=args.secret_ref,
                             ack_window_seconds=args.ack_window_seconds, budget=budget, order=args.order)
        elif args.command == "enter":
            result = enter(rendezvous, args.actor, args.host)
        elif args.command == "pending":
            items = pending(rendezvous._events(), args.actor)
            if args.ack and items:
                from tools.awp_ingress import handle as ingress

                for item in items:
                    item["receipt"] = ingress(rendezvous.project, args.actor, item["event_id"])["state"]
            result = {"actor": args.actor, "pending": items}
        elif args.command == "retire":
            result = retire(rendezvous, args.actor, args.binding, args.reason)
        elif args.command == "list":
            result = {"bindings": [item for item in active_bindings(rendezvous._events()).values()
                                   if not args.actor or item["actor"] == args.actor]}
        elif args.command == "reach":
            result = reach(rendezvous._events(), args.actor)
        elif args.command == "probe":
            result = probe(rendezvous, args.binding, args.ttl_seconds)
        else:
            result = outcome(rendezvous._events(), args.event)
    except WakeError as error:
        print(json.dumps({"state": "refused", "reason": str(error)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
