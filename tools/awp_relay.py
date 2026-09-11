"""AWP relay: turn Git ledger events into wake attempts for every bound participant.

One relay runs per clone (or, later, per always-on LAN host).  It serves every
wake binding that names it (``tools/awp_wake.py``), whatever agent the binding
belongs to, and runs the delivery ladder of Cooperation Contracts section 12:

1. A ledger ref change (the Git event) or the safety replay wakes the relay.
2. For each addressed event it tries the recipient's bindings in declared
   order, recording a transport receipt as ``actor:awp-relay`` for each try.
3. It waits for a *recipient* receipt within the binding's acknowledgement
   window; if none arrives it records ``coop2.wake.escalated`` and moves on.
4. After the last binding it notifies the principal (a W5 binding) or records
   a disclosed ``entry-only`` outcome.  Nothing is ever silent, and entry
   recovery stays authoritative underneath every rung.

Bindings have budgets and a circuit breaker; a suspended binding is skipped
with the reason recorded until a probe through it succeeds again.  Every new
declaration is probed once, so reach is measured, not assumed.

The relay never records a recipient receipt itself.  Receipts arrive from the
recipient's session (ingress or a host prompt hook) or from a headless runner
(``host-launch``), through the request spool this relay serves.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid
from typing import Any, Callable, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from tools import awp_wake as wake
    from tools.awp_coop2 import Rendezvous
    from tools.awp_coordination import CoordinationError
    from tools.awp_request_spool import RequestSpool
    from tools.awp_runtime import atomic_json, control_is_current
    from tools.awp_supervisor import SignalWatch
else:
    from . import awp_wake as wake
    from .awp_coop2 import Rendezvous
    from .awp_coordination import CoordinationError
    from .awp_request_spool import RequestSpool
    from .awp_runtime import atomic_json, control_is_current
    from .awp_supervisor import SignalWatch


PROFILE = "awp-relay-v1"
RELAY_ACTOR = wake.RELAY_ACTOR
BREAKER_THRESHOLD = 3
PROBE_BACKOFF_SECONDS = 1800
COALESCE_SECONDS = 5
HISTORY_SECONDS = 3600
DONE_RETENTION_SECONDS = 7 * 86400
RECEIPT_VIA = {"agent-ingress", "host-prompt-hook", "host-launch"}
RECIPIENT_RECEIPTS = {"coop2.interaction.observed", "coop2.interaction.accepted", "coop2.interaction.refused",
                      "coop2.interaction.responded"}
FINAL = {"received", "closed", "expired", "failed", "principal-notified", "done"}


def runtime(project: Path) -> Path:
    return project / ".awp-runtime"


def control_path(project: Path) -> Path:
    return runtime(project) / "awp-relay.json"


def state_path(project: Path) -> Path:
    return runtime(project) / "awp-relay-state.json"


def status_path(project: Path) -> Path:
    return runtime(project) / "awp-relay-status.json"


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def legacy_handled(project: Path) -> list[str]:
    """Events a per-actor supervisor already delivered; the relay does not repeat them."""
    handled: set[str] = set()
    for path in runtime(project).glob("awp-supervisor-*.json"):
        handled.update(_read(path).get("jobs", {}).keys())
    return sorted(handled)


class _Index:
    """Receipts and closures derived from the authoritative ledger."""

    def __init__(self, events: list[dict[str, Any]]) -> None:
        self.acked: dict[str, dict[str, Any]] = {}
        self.received: dict[str, dict[str, Any]] = {}
        self.withdrawn: set[str] = set()
        self.outcomes: set[str] = set()
        for event in events:
            payload = event.get("payload", {})
            kind = event["kind"]
            if kind == "coop2.tickle.acked":
                self.acked.setdefault(payload.get("tickle_id"), event)
            elif kind in RECIPIENT_RECEIPTS:
                self.received.setdefault(f"{payload.get('interaction_id')}\0{event.get('actor')}", event)
            elif kind == "coop2.interaction.withdrawn":
                self.withdrawn.add(payload.get("interaction_id"))
            elif kind == wake.OUTCOME:
                self.outcomes.add(payload.get("event_id"))

    def receipt(self, job: dict[str, Any]) -> dict[str, Any] | None:
        if job["event_kind"] == "coop2.tickle.sent":
            return self.acked.get(job["subject"])
        return self.received.get(f"{job['subject']}\0{job['recipient']}")


class Relay:
    def __init__(self, rendezvous: Any, relay: str, path: Path, *, generation: str = "manual",
                 adapter_factory: Callable[[dict[str, Any]], Any] | None = None,
                 clock: Callable[[], datetime] | None = None) -> None:
        self.rendezvous = rendezvous
        self.relay = relay
        self.state_path = path
        self.generation = generation
        self.project = Path(getattr(rendezvous, "project", path.parent))
        self.spool = RequestSpool(self.project)
        self.adapter_factory = adapter_factory or (lambda binding: wake.adapter_for(binding, self.project))
        self.clock = clock or wake.utc_now
        self._frontier: list[str] | None = None
        self.notes: list[str] = []

    # -- state --------------------------------------------------------------
    def state(self) -> dict[str, Any]:
        value = _read(self.state_path)
        if value.get("profile") != PROFILE or value.get("relay") != self.relay:
            value = {"profile": PROFILE, "relay": self.relay, "cursor": None, "jobs": {}, "bindings": {},
                     "handled": legacy_handled(self.project)}
        value.setdefault("jobs", {}); value.setdefault("bindings", {}); value.setdefault("handled", [])
        return value

    def _binding_state(self, state: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
        entry = state["bindings"].get(binding["binding_id"])
        if entry is None or entry.get("declaration") != binding["event_id"]:
            # A new declaration (for example a new live session) starts clean.
            prior = entry or {}
            entry = {"declaration": binding["event_id"], "failures": 0, "suspended": None, "runs": prior.get("runs", []),
                     "probed_declaration": prior.get("probed_declaration"), "last_probe_at": prior.get("last_probe_at")}
            state["bindings"][binding["binding_id"]] = entry
        return entry

    # -- ledger writes (always as the relay) -----------------------------------
    def _record(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self.rendezvous._append(RELAY_ACTOR, kind, payload | {"relay": self.relay})

    def _frontier_now(self) -> list[str]:
        if self._frontier is None:
            self._frontier = self.rendezvous.ledger.refresh(self.rendezvous.workstate_id)["frontier"]
        return self._frontier

    def _envelope(self, job: dict[str, Any], binding: dict[str, Any]) -> dict[str, Any]:
        return {
            "type": "cooperation_activation_envelope", "module": "urn:awp:cooperation",
            "profile": "awp-host-activation-v1",
            "operation_id": f"deliver:{binding['binding_id']}:{job['event_id']}",
            "binding_id": self.rendezvous.ledger.binding_id(), "project_id": self.rendezvous.project_id,
            "workstate_id": self.rendezvous.workstate_id, "recipient_actor": job["recipient"],
            "route_id": binding["binding_id"], "route_generation": binding["event_id"],
            "event_id": job["event_id"], "event_kind": job["event_kind"], "interaction_id": job["subject"],
            "ledger_frontier": self._frontier_now(),
        }

    def _transport(self, job: dict[str, Any], binding: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
        if job["event_kind"] == "coop2.tickle.sent":
            base = "coop2.tickle"
        elif job["event_kind"] == "coop2.tickle.acked":
            base = "coop2.tickle.ack"
        else:
            base = "coop2.interaction"
        suffix = "queued" if result["state"] == "accepted" else result["state"]
        return self._record(f"{base}.transport_{suffix}", {
            "event_id": job["event_id"], "interaction_id": job["subject"], "recipient": job["recipient"],
            "route_id": binding["binding_id"], "route_generation": binding["event_id"],
            "binding_id": binding["binding_id"], "wake_class": binding["class"],
            "transport_state": result["state"], "endpoint_receipt": result.get("endpoint_receipt"),
            "reason": result.get("reason"),
        })

    # -- one pass -------------------------------------------------------------
    def step(self, limit: int = 256) -> dict[str, Any]:
        now = self.clock()
        self._frontier = None
        self.notes = []
        state = self.state()
        ingress = self.spool.process(self._handle_request, limit=limit,
                                     accept=lambda envelope: envelope.get("client_id") == envelope.get("request", {}).get("actor"))
        events = self.rendezvous._events()
        index = _Index(events)
        bindings = wake.active_bindings(events)
        mine = {key: value for key, value in bindings.items() if value["relay"] == self.relay}
        self._elsewhere = {value["actor"] for value in bindings.values() if value["relay"] != self.relay}

        ledger = self.rendezvous.ledger
        profile = getattr(ledger, "profile", "sqlite")
        cursor = state.get("cursor")
        if state.get("ledger_profile", profile) != profile:
            cursor = None
        fresh = not cursor
        if fresh:
            state["informational_floor"] = wake.iso(now)
        if profile == "git-ledger-v1":
            cursor = cursor if isinstance(cursor, dict) else {}
        else:
            cursor = int(cursor) if isinstance(cursor, (int, str)) and str(cursor).isdigit() else 0
        state["ledger_profile"] = profile
        page = ledger.events_after(self.rendezvous.workstate_id, cursor, limit)
        admitted = []
        handled = set(state["handled"])
        for event in page["events"]:
            sequence = event.pop("_ledger_sequence", None)
            if self._admit(state, event, index, now, fresh, handled):
                admitted.append(event["event_id"])
            if sequence is not None:
                state["cursor"] = sequence
        if not page["events"] and fresh:
            state["cursor"] = page.get("next_cursor") or cursor or None

        # Liveness first: a slow wake adapter below must not make the relay look dead.
        heartbeats = []
        for actor in sorted({item["actor"] for item in mine.values() if item["class"] == "W1"}):
            try:
                self.rendezvous.heartbeat(actor, PROFILE)
                heartbeats.append(actor)
            except Exception as error:  # a heartbeat is evidence, never a reason to stop relaying
                self.notes.append(f"heartbeat {actor}: {str(error)[:120]}")
        self._write_status(state, mine, now, {"notes": self.notes})
        probes = self._probe_bindings(state, mine, now)
        activity = self._advance(state, mine, index, now)
        self._prune(state, now)
        atomic_json(self.state_path, state)
        summary = {"profile": PROFILE, "relay": self.relay, "admitted": admitted, "probes": probes,
                   "ingress_processed": len(ingress), "heartbeats": heartbeats, "notes": self.notes, **activity}
        self._write_status(state, mine, now, summary)
        return summary

    def _admit(self, state: dict[str, Any], event: dict[str, Any], index: _Index, now: datetime, fresh: bool,
               handled: set[str]) -> bool:
        event_id, kind, payload = event["event_id"], event["kind"], event.get("payload", {})
        recipient = payload.get("recipient")
        if not recipient or recipient == RELAY_ACTOR or event_id in state["jobs"] or event_id in handled:
            return False
        subject = payload.get("tickle_id") or payload.get("interaction_id")
        job = {"event_id": event_id, "event_kind": kind, "recipient": recipient, "subject": subject,
               "occurred_at": event.get("occurred_at"), "created_at": wake.iso(now), "tried": [], "current": None,
               "state": "open"}
        if kind == "coop2.tickle.sent":
            sent = wake.parse_time(event.get("occurred_at"))
            try:
                expires = sent + timedelta(seconds=int(payload["ttl_seconds"])) if sent else None
            except (KeyError, TypeError, ValueError):
                expires = None
            if (expires and now > expires) or index.acked.get(subject):
                return False
            job["expires_at"] = wake.iso(expires) if expires else None
            if payload.get("probe_binding"):
                job["probe_binding"] = payload["probe_binding"]
        elif kind == "coop2.interaction.requested":
            if subject in index.withdrawn or index.receipt(job):
                return False
        elif kind in {"coop2.tickle.acked", "coop2.interaction.responded"}:
            floor = state.get("informational_floor")
            if floor and str(event.get("occurred_at", "")) < floor:
                return False
            job["state"] = "info"
        else:
            return False
        occurred = wake.parse_time(event.get("occurred_at"))
        if fresh and occurred and (now - occurred).total_seconds() > HISTORY_SECONDS and job["state"] == "open":
            # First start over an old ledger: long-open items are not re-woken
            # (their recipients see them on entry); only recent ones ladder.
            job.update({"state": "parked", "historical": True})
        state["jobs"][event_id] = job
        return True

    # -- probes ---------------------------------------------------------------
    def _probe_bindings(self, state: dict[str, Any], mine: dict[str, dict[str, Any]], now: datetime) -> list[str]:
        sent = []
        for binding in mine.values():
            if binding["class"] == "W5":
                continue  # a notification has no recipient receipt to verify
            entry = self._binding_state(state, binding)
            key = None
            if entry.get("probed_declaration") != binding["event_id"]:
                key = f"probe:{binding['event_id']}"
            elif entry.get("suspended"):
                last = wake.parse_time(entry.get("last_probe_at"))
                if last is None or (now - last).total_seconds() >= PROBE_BACKOFF_SECONDS:
                    key = f"probe:{binding['event_id']}:{int(now.timestamp())}"
            if key is None:
                continue
            try:
                result = wake.probe(self.rendezvous, binding["binding_id"], key=key)
                sent.append(result["tickle_id"])
            except (CoordinationError, wake.WakeError) as error:
                self.notes.append(f"probe {binding['binding_id']}: {str(error)[:160]}")
            entry["probed_declaration"] = binding["event_id"]
            entry["last_probe_at"] = wake.iso(now)
        return sent

    # -- ladder ---------------------------------------------------------------
    def _skip_reason(self, state: dict[str, Any], binding: dict[str, Any], job: dict[str, Any], now: datetime) -> str | None:
        entry = self._binding_state(state, binding)
        if entry.get("suspended") and job.get("probe_binding") != binding["binding_id"]:
            return f"binding suspended: {entry['suspended']}"
        budget = binding["budget"]
        window = now - timedelta(seconds=int(budget["per_seconds"]))
        recent = [stamp for stamp in entry.get("runs", []) if (wake.parse_time(stamp) or now) > window]
        entry["runs"] = recent
        if len(recent) >= int(budget["runs"]):
            return f"budget exhausted ({budget['runs']} runs per {budget['per_seconds']}s)"
        return None

    def _fail(self, state: dict[str, Any], binding: dict[str, Any], reason: str) -> None:
        entry = self._binding_state(state, binding)
        entry["failures"] = int(entry.get("failures", 0)) + 1
        entry["last_failure"] = reason[:200]
        if entry["failures"] >= BREAKER_THRESHOLD and not entry.get("suspended"):
            entry["suspended"] = f"{entry['failures']} consecutive failures; last: {reason[:160]}"
            self._record(wake.SUSPENDED, {"binding_id": binding["binding_id"], "actor": binding["actor"],
                                          "wake_class": binding["class"], "reason": entry["suspended"]})

    def _succeed(self, state: dict[str, Any], binding: dict[str, Any]) -> None:
        entry = self._binding_state(state, binding)
        entry["failures"] = 0
        if entry.get("suspended"):
            entry["suspended"] = None
            self._record(wake.RESUMED, {"binding_id": binding["binding_id"], "actor": binding["actor"],
                                        "wake_class": binding["class"], "reason": "recipient receipt through this binding"})

    def _escalate(self, job: dict[str, Any], binding: dict[str, Any], reason: str) -> None:
        self._record(wake.ESCALATED, {"event_id": job["event_id"], "interaction_id": job["subject"],
                                      "recipient": job["recipient"], "binding_id": binding["binding_id"],
                                      "wake_class": binding["class"], "reason": reason[:200]})

    def _finish(self, job: dict[str, Any], outcome: str, reason: str, index: _Index) -> None:
        if job["event_id"] not in index.outcomes:
            self._record(wake.OUTCOME, {"event_id": job["event_id"], "interaction_id": job["subject"],
                                        "recipient": job["recipient"], "outcome": outcome, "reason": reason[:200],
                                        "tried": [item.split("@")[0] for item in job["tried"]]})
            index.outcomes.add(job["event_id"])

    @staticmethod
    def _key(binding: dict[str, Any]) -> str:
        return f"{binding['binding_id']}@{binding['event_id']}"

    def _candidates(self, job: dict[str, Any], mine: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
        rungs = [item for item in wake.ladder(mine, job["recipient"]) if item["class"] != "W5"]
        if job.get("probe_binding"):
            rungs = [item for item in rungs if item["binding_id"] == job["probe_binding"]]
        return [item for item in rungs if self._key(item) not in job["tried"]]

    def _deliver(self, binding: dict[str, Any], jobs: list[dict[str, Any]]) -> dict[str, Any]:
        envelopes = [self._envelope(job, binding) for job in jobs]
        try:
            adapter = self.adapter_factory(binding)
        except wake.WakeError as error:
            return {"state": "unavailable", "reason": str(error)}
        try:
            if hasattr(adapter, "deliver_many"):
                return adapter.deliver_many(envelopes)
            return adapter.deliver(envelopes[0])
        except Exception as error:  # an adapter fault is a failed rung, never a relay crash
            return {"state": "unavailable", "reason": f"adapter error: {str(error)[:200]}"}

    def _advance(self, state: dict[str, Any], mine: dict[str, dict[str, Any]], index: _Index, now: datetime) -> dict[str, Any]:
        delivered, escalated, finished = [], [], []
        jobs = sorted(state["jobs"].values(), key=lambda item: (item.get("created_at", ""), item["event_id"]))
        by_id = {item["binding_id"]: item for item in mine.values()}
        for job in jobs:
            if job["state"] in FINAL:
                continue
            receipt = index.receipt(job) if job["state"] != "info" else None
            current = job.get("current")
            if receipt:
                binding = by_id.get(current["binding_id"]) if current else None
                if binding is None and job.get("probe_binding"):
                    binding = by_id.get(job["probe_binding"])
                if binding is not None and (current or job.get("probe_binding")):
                    self._succeed(state, binding)
                job.update({"state": "received", "current": None, "received_at": receipt.get("occurred_at"),
                            "via": (receipt.get("payload") or {}).get("acknowledged_via") or (receipt.get("payload") or {}).get("observed_via")})
                finished.append(job["event_id"])
                continue
            if job["event_kind"] == "coop2.interaction.requested" and job["subject"] in index.withdrawn:
                job.update({"state": "closed", "current": None})
                continue
            expires = wake.parse_time(job.get("expires_at"))
            if expires and now > expires:
                if current and current["binding_id"] in by_id:
                    self._fail(state, by_id[current["binding_id"]], "no recipient receipt before the probe expired")
                if job["state"] in {"open", "awaiting-expiry"}:
                    self._finish(job, "failed" if job.get("probe_binding") else "expired",
                                 "no recipient receipt before the probe expired", index)
                job.update({"state": "failed" if job.get("probe_binding") else "expired", "current": None})
                finished.append(job["event_id"])
                continue
            if job["state"] == "info":
                self._deliver_info(job, mine)
                continue
            if job.get("historical"):
                continue
            if current:
                if now < (wake.parse_time(current["deadline"]) or now):
                    continue
                binding = by_id.get(current["binding_id"])
                if binding is not None:
                    self._fail(state, binding, "no recipient receipt within the acknowledgement window")
                    self._escalate(job, binding, "no recipient receipt within the acknowledgement window")
                    escalated.append(job["event_id"])
                job["current"] = None
            waiting = False
            while True:
                candidates = self._candidates(job, mine)
                if not candidates:
                    break
                binding = candidates[0]
                reason = self._skip_reason(state, binding, job, now)
                if reason:
                    job["tried"].append(self._key(binding))
                    self._escalate(job, binding, f"skipped: {reason}")
                    escalated.append(job["event_id"])
                    continue
                if binding["class"] in {"W2", "W3", "W4"} and not job.get("probe_binding"):
                    created = wake.parse_time(job.get("created_at")) or now
                    if (now - created).total_seconds() < COALESCE_SECONDS:
                        waiting = True  # events arriving together share one run
                        break
                group = [job]
                if binding["class"] in {"W2", "W3", "W4"} and not job.get("probe_binding"):
                    for other in jobs:
                        if (other is not job and other["state"] in {"open", "parked"} and not other.get("historical")
                                and not other.get("current") and other["recipient"] == job["recipient"]
                                and not other.get("probe_binding") and other["event_kind"] != "coop2.tickle.acked"
                                and not index.receipt(other)
                                and self._candidates(other, mine)[:1] and self._candidates(other, mine)[0]["binding_id"] == binding["binding_id"]):
                            group.append(other)
                result = self._deliver(binding, group)
                self._binding_state(state, binding).setdefault("runs", []).append(wake.iso(now))
                window = int(binding["ack_window_seconds"])
                for member in group:
                    self._transport(member, binding, result)
                    member["tried"].append(self._key(binding))
                    delivered.append(member["event_id"])
                if result.get("state") == "accepted":
                    for member in group:
                        deadline = now + timedelta(seconds=window)
                        member_expiry = wake.parse_time(member.get("expires_at"))
                        if member_expiry and member_expiry < deadline:
                            deadline = member_expiry
                        member.update({"state": "open", "current": {"binding_id": binding["binding_id"],
                                                                    "at": wake.iso(now), "deadline": wake.iso(deadline)}})
                    break
                self._fail(state, binding, result.get("reason") or f"transport {result.get('state')}")
                for member in group[1:]:
                    self._escalate(member, binding, f"transport {result.get('state')}: {result.get('reason') or ''}")
                self._escalate(job, binding, f"transport {result.get('state')}: {result.get('reason') or ''}")
                escalated.append(job["event_id"])
            if job.get("current") or waiting:
                continue
            if job.get("probe_binding"):
                if job["state"] == "open":
                    job["state"] = "awaiting-expiry"
                continue
            self._end_of_ladder(state, job, mine, index, now)
            if job["state"] in FINAL:
                finished.append(job["event_id"])
        return {"delivered": delivered, "escalated": escalated, "finished": finished}

    def _end_of_ladder(self, state: dict[str, Any], job: dict[str, Any], mine: dict[str, dict[str, Any]],
                       index: _Index, now: datetime) -> None:
        if job["state"] == "parked":
            return
        if not job["tried"] and job["recipient"] in getattr(self, "_elsewhere", set()) and not wake.ladder(mine, job["recipient"]):
            job["state"] = "parked"  # another relay serves this recipient; it owns the outcome
            return
        notify = [item for item in wake.ladder(mine, job["recipient"]) if item["class"] == "W5"]
        if job["event_kind"] == "coop2.interaction.requested" and notify and not job.get("notified"):
            binding = notify[0]
            reason = self._skip_reason(state, binding, job, now)
            if reason is None:
                result = self._deliver(binding, [job])
                self._binding_state(state, binding).setdefault("runs", []).append(wake.iso(now))
                self._record(wake.PRINCIPAL_NOTIFIED, {"event_id": job["event_id"], "interaction_id": job["subject"],
                                                       "recipient": job["recipient"], "binding_id": binding["binding_id"],
                                                       "channel": result.get("endpoint_receipt"), "outcome": "principal-notified",
                                                       "tried": [item.split("@")[0] for item in job["tried"]]})
                job.update({"state": "principal-notified", "notified": True})
                return
            self._escalate(job, binding, f"skipped: {reason}")
        if job["tried"]:
            reason = "no wake binding produced a recipient receipt"
        elif notify and job["event_kind"] == "coop2.tickle.sent":
            reason = "recipient can only be reached by principal notification, which probes do not use"
        else:
            reason = "recipient has no wake binding on this relay"
        self._finish(job, "entry-only", reason, index)
        # Parked, not closed: a later declaration (a new live session) resumes it.
        job["state"] = "parked"

    def _deliver_info(self, job: dict[str, Any], mine: dict[str, dict[str, Any]]) -> None:
        live = [item for item in wake.ladder(mine, job["recipient"]) if item["class"] == "W1"]
        if live:
            result = self._deliver(live[0], [job])
            self._transport(job, live[0], result)
        job["state"] = "done"

    def _prune(self, state: dict[str, Any], now: datetime) -> None:
        for key, job in list(state["jobs"].items()):
            stamp = wake.parse_time(job.get("created_at"))
            if stamp and (now - stamp).total_seconds() > DONE_RETENTION_SECONDS and (
                    job["state"] in FINAL or job.get("historical")):
                state["jobs"].pop(key)
                state["handled"].append(key)
        state["handled"] = state["handled"][-5000:]

    def _write_status(self, state: dict[str, Any], mine: dict[str, dict[str, Any]], now: datetime,
                      summary: dict[str, Any]) -> None:
        open_jobs = [job for job in state["jobs"].values() if job["state"] not in FINAL and not job.get("historical")]
        atomic_json(status_path(self.project), {
            "profile": PROFILE, "relay": self.relay, "generation": self.generation, "pid": os.getpid(),
            "last_seen": wake.iso(now),
            "served": sorted({item["actor"] for item in mine.values()}),
            "bindings": {key: {"actor": item["actor"], "class": item["class"], "adapter": item["adapter"],
                               "failures": state["bindings"].get(key, {}).get("failures", 0),
                               "suspended": state["bindings"].get(key, {}).get("suspended")}
                         for key, item in mine.items()},
            "open_jobs": len(open_jobs), "notes": summary.get("notes", []),
        })

    # -- ingress --------------------------------------------------------------
    def _handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        actor = request.get("actor")
        event_id = request.get("event_id")
        event = next((item for item in self.rendezvous._events() if item["event_id"] == event_id), None)
        if event is None or event.get("payload", {}).get("recipient") != actor:
            raise ValueError("unknown or misaddressed ingress event")
        payload = event["payload"]
        via = request.get("via") if request.get("via") in RECEIPT_VIA else "agent-ingress"
        evidence = request.get("evidence") if isinstance(request.get("evidence"), dict) else None
        if event["kind"] == "coop2.tickle.sent":
            return self.rendezvous.tickle_ack(actor, payload["tickle_id"], via=via, evidence=evidence)
        if event["kind"] == "coop2.interaction.requested":
            return self.rendezvous.observe(actor, payload["interaction_id"], via=via, evidence=evidence)
        return {"publication": "not-required", "event_id": event_id}


# -- process management ---------------------------------------------------------

def relay_status(project: Path, interval_seconds: float = 5.0) -> dict[str, Any]:
    """Liveness from the relay's own status heartbeat (works across machines and VMs)."""
    status = _read(status_path(project))
    control = _read(control_path(project))
    last = wake.parse_time(status.get("last_seen"))
    age = (wake.utc_now() - last).total_seconds() if last else None
    live = (age is not None and age <= max(3 * interval_seconds, 30)
            and control.get("desired_state") == "running" and control.get("generation") == status.get("generation"))
    return {"live": live, "age_seconds": round(age, 1) if age is not None else None, "status": status, "control": control}


def relay_command(project: Path, generation: str, interval_seconds: float) -> list[str]:
    return [sys.executable, "-m", "tools.awp_relay", "--project", str(project), "--control", str(control_path(project)),
            "--generation", generation, "--interval-seconds", str(interval_seconds)]


def spawn(project: Path, interval_seconds: float = 5.0, started_by: str = "session") -> dict[str, Any]:
    generation = uuid.uuid4().hex
    control = {"profile": PROFILE, "generation": generation, "desired_state": "running", "state": "starting",
               "started_at": wake.iso(wake.utc_now()), "started_by": started_by}
    atomic_json(control_path(project), control)
    flags = 0
    if os.name == "nt":
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
                 | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    runtime(project).mkdir(parents=True, exist_ok=True)
    with (runtime(project) / "awp-relay.out.log").open("ab") as output, (runtime(project) / "awp-relay.err.log").open("ab") as error:
        process = subprocess.Popen(relay_command(project, generation, interval_seconds), cwd=Path(__file__).resolve().parent.parent,
                                   stdin=subprocess.DEVNULL, stdout=output, stderr=error, close_fds=True,
                                   creationflags=flags, start_new_session=os.name != "nt")
    control.update({"pid": process.pid, "state": "waiting_for_status"})
    atomic_json(control_path(project), control)
    return control


def ensure(project: Path, interval_seconds: float = 5.0, timeout_seconds: float = 12.0,
           started_by: str = "session") -> dict[str, Any]:
    """Attach to this clone's live relay, or start one and wait for its first pass."""
    current = relay_status(project, interval_seconds)
    if current["live"]:
        return {"state": "attached", **current}
    control = spawn(project, interval_seconds, started_by)
    deadline = time.monotonic() + max(timeout_seconds, 0.1)
    while time.monotonic() < deadline:
        current = relay_status(project, interval_seconds)
        if current["live"] and current["status"].get("generation") == control["generation"]:
            return {"state": "started", **current}
        time.sleep(0.25)
    return {"state": "unavailable", "diagnostic": "AWP-RELAY-UNVERIFIED", **relay_status(project, interval_seconds)}


def stop(project: Path) -> dict[str, Any]:
    control = _read(control_path(project))
    control.update({"profile": PROFILE, "desired_state": "stopped", "generation": uuid.uuid4().hex,
                    "stopped_at": wake.iso(wake.utc_now())})
    atomic_json(control_path(project), control)
    return {"state": "stopping", "control": control}


def _code_fingerprint() -> tuple:
    tools = Path(__file__).resolve().parent
    return tuple(sorted((item.name, item.stat().st_mtime_ns) for item in tools.glob("awp_*.py")))


def _relaunch(argv: Sequence[str], project: Path) -> None:
    """Replace this process with one running the current code, same generation."""
    flags = 0
    if os.name == "nt":
        flags = (getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
                 | getattr(subprocess, "CREATE_NO_WINDOW", 0))
    with (runtime(project) / "awp-relay.out.log").open("ab") as output, (runtime(project) / "awp-relay.err.log").open("ab") as error:
        subprocess.Popen([sys.executable, "-m", "tools.awp_relay", *argv], cwd=Path(__file__).resolve().parent.parent,
                         stdin=subprocess.DEVNULL, stdout=output, stderr=error, close_fds=True, creationflags=flags,
                         start_new_session=os.name != "nt")


def _claim(control: Path, generation: str) -> None:
    value = _read(control)
    if value.get("generation") == generation and value.get("pid") != os.getpid():
        value.update({"pid": os.getpid(), "state": "running"})
        atomic_json(control, value)


def run_loop(relay: Relay, control: Path, generation: str, argv: Sequence[str], *, interval_seconds: float = 5.0,
             signal_poll_seconds: float = 0.25, once: bool = False) -> int:
    watch = SignalWatch(relay.project, RELAY_ACTOR)
    watch.paths[-1] = runtime(relay.project) / "requests"  # every served actor's ingress spool
    code = _code_fingerprint()
    _claim(control, generation)
    trigger = "start"
    while True:
        if not control_is_current(control, generation):
            return 0
        seen = watch.fingerprint()
        try:
            output = relay.step()
        except Exception as error:  # keep relaying; the next pass replays from the cursor
            output = {"error": str(error)[:500], "delivered": [], "escalated": []}
        output["trigger"] = trigger
        if once or output.get("delivered") or output.get("escalated") or output.get("error"):
            print(json.dumps(output, sort_keys=True), flush=True)
        if once:
            return 0
        deadline = time.monotonic() + max(interval_seconds, 0.1)
        trigger = "replay"
        while time.monotonic() < deadline:
            if not control_is_current(control, generation):
                return 0
            if watch.fingerprint() != seen:
                trigger = "git-signal"
                break
            time.sleep(max(signal_poll_seconds, 0.05))
        if _code_fingerprint() != code:
            _relaunch(argv, relay.project)
            return 0


LIVE_SESSION_PROFILES = {"codex": "codex-queue"}


def declare_live_session(rendezvous: Any, actor: str, host: str, session_ref: str,
                         adapter_command: Sequence[str] | None = None) -> dict[str, Any] | None:
    """Declare the W1 binding for an agent's open session (called on activation).

    A trusted local adapter command is kept in relay-local configuration and
    only its profile name enters the ledger.
    """
    project = Path(rendezvous.project)
    if adapter_command:
        name = "local:" + wake.binding_id(actor, "W1", host).split(":")[1]
        wake.register_local_command(project, name, "W1", adapter_command)
        return wake.declare(rendezvous, actor, "W1", name, params={"session_ref": session_ref})
    profile = LIVE_SESSION_PROFILES.get(host)
    if profile is None:
        return None
    return wake.declare(rendezvous, actor, "W1", profile, params={"session_ref": session_ref})


def adopt_legacy(args: argparse.Namespace) -> int:
    """Run in place of a per-actor supervisor started by older activation code.

    A supervisor process that relaunches itself after a code change arrives
    here: it declares its session as a W1 binding, then either leaves the work
    to this clone's live relay or becomes that relay.
    """
    project = args.project.resolve()
    rendezvous = Rendezvous(project, args.ledger)
    try:
        declare_live_session(rendezvous, args.actor, args.host, args.session_ref)
    except (CoordinationError, wake.WakeError) as error:
        print(json.dumps({"adopt_legacy": "declaration failed", "reason": str(error)[:300]}), flush=True)
    if relay_status(project, args.interval_seconds)["live"]:
        return 0
    generation = uuid.uuid4().hex
    atomic_json(control_path(project), {"profile": PROFILE, "generation": generation, "desired_state": "running",
                                        "state": "running", "pid": os.getpid(), "started_at": wake.iso(wake.utc_now()),
                                        "started_by": "legacy-supervisor"})
    relay = Relay(rendezvous, wake.relay_id(project), state_path(project), generation=generation)
    argv = ["--project", str(project), "--control", str(control_path(project)), "--generation", generation,
            "--interval-seconds", str(args.interval_seconds)]
    return run_loop(relay, control_path(project), generation, argv, interval_seconds=args.interval_seconds,
                    signal_poll_seconds=args.signal_poll_seconds)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument("command", nargs="?", default="run", choices=["run", "status", "ensure", "stop"])
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--relay-id")
    result.add_argument("--control", type=Path)
    result.add_argument("--generation")
    result.add_argument("--state", type=Path)
    result.add_argument("--interval-seconds", type=float, default=5.0)
    result.add_argument("--signal-poll-seconds", type=float, default=0.25)
    result.add_argument("--once", action="store_true")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    args = parser().parse_args(argv)
    project = args.project.resolve()
    if args.command == "status":
        print(json.dumps(relay_status(project, args.interval_seconds), indent=2, sort_keys=True))
        return 0
    if args.command == "ensure":
        result = ensure(project, args.interval_seconds, started_by="cli")
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result["state"] in {"attached", "started"} else 2
    if args.command == "stop":
        print(json.dumps(stop(project), indent=2, sort_keys=True))
        return 0
    rendezvous = Rendezvous(project)
    control = args.control or control_path(project)
    generation = args.generation
    if not generation:
        generation = uuid.uuid4().hex
        atomic_json(control, {"profile": PROFILE, "generation": generation, "desired_state": "running",
                              "state": "running", "pid": os.getpid(), "started_at": wake.iso(wake.utc_now()),
                              "started_by": "manual"})
        argv = [*argv, "--generation", generation]
    relay = Relay(rendezvous, args.relay_id or wake.relay_id(project), args.state or state_path(project),
                  generation=generation)
    return run_loop(relay, control, generation, argv, interval_seconds=args.interval_seconds,
                    signal_poll_seconds=args.signal_poll_seconds, once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
