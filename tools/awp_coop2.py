"""Experimental project-scoped COOP-2 rendezvous over the local AWP ledger.

This is a bounded managed-collaboration pilot, not a COOP-2 conformance claim.
It gives sessions sharing one project a stable place to join, discover peers,
send a typed interaction, and receive a durable reply without exchanging paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import os
import re
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

from .awp_coordination import CoordinationError, CoordinationLedger, discover_workstate, find_project, stable_project_id


PROFILE = "local-coop2-rendezvous-v1"
DOORBELL_PROFILE = "local-filesystem-doorbell-v1"
GIT_REF_DOORBELL_PROFILE = "local-git-ref-doorbell-v1"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


class LocalDoorbell:
    """Atomic, content-free wake hint for a shared project filesystem.

    The ledger is the authoritative transport.  This file only tells a watcher
    that it should refresh that ledger; replacing it coalesces several events
    without losing them because the recorded frontier is monotonic.
    """

    def __init__(self, project: Path) -> None:
        self.path = project / ".awp-runtime" / "coop2-doorbell.json"

    def publish(
        self,
        *,
        project_id: str,
        workstate_id: str,
        binding_id: str,
        event_id: str,
        frontier: list[str],
        interaction_id: str,
        kind: str,
    ) -> dict:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        signal = {
            "profile": DOORBELL_PROFILE,
            "project_id": project_id,
            "workstate_id": workstate_id,
            "binding_id": binding_id,
            "event_id": event_id,
            "frontier": frontier,
            "interaction_id": interaction_id,
            "kind": kind,
            "signalled_at": now(),
        }
        handle, temporary_name = tempfile.mkstemp(
            prefix=".coop2-doorbell.", suffix=".tmp", dir=self.path.parent
        )
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(signal, temporary, sort_keys=True)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, self.path)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
        return signal | {"path": str(self.path)}

    def status(self, *, project_id: str, workstate_id: str, binding_id: str) -> dict:
        descriptor = {
            "profile": DOORBELL_PROFILE,
            "path": str(self.path),
            "authoritative_binding": binding_id,
            "correlation": "event_id-and-frontier",
            "content": "none; watchers refresh the authoritative ledger",
            "watcher_liveness": "not verified by this binding",
        }
        if not self.path.exists():
            return descriptor | {"state": "idle"}
        try:
            signal = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return descriptor | {"state": "unverifiable", "reason": str(error)}
        expected = {"project_id": project_id, "workstate_id": workstate_id, "binding_id": binding_id}
        if any(signal.get(key) != value for key, value in expected.items()):
            return descriptor | {"state": "unverifiable", "reason": "signal identity does not match this binding"}
        return descriptor | {"state": "current", "signal": signal}


MAX_SIGNAL_REFS = 32
STALE_LOCK_SECONDS = 30
_LOCK_PATH = re.compile(r"'([^']+\.lock)'")


class GitRefDoorbell:
    """Local Git-ref wake hint correlated to an already-published ledger event.

    Bounded: after each publication the namespace is pruned to the refs whose
    event identifiers the caller still retains (the ledger's recent frontier
    window), so it cannot grow without limit.  Lock-tolerant: a ref update that
    fails on a stale ``.lock`` older than STALE_LOCK_SECONDS removes it and
    retries once, because a doorbell that jams on a leftover lock is a doorbell
    that silently stops ringing.
    """

    prefix = "refs/awp/signal/"

    def __init__(self, project: Path) -> None:
        self.project = project

    @classmethod
    def ref_name(cls, event_id: str) -> str:
        # AWP event IDs contain ':', which Git ref components prohibit.
        return cls.prefix + event_id.replace(":", "-")

    def _git(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *arguments], cwd=self.project, check=False, capture_output=True, text=True)

    def _recover_stale_lock(self, stderr: str) -> str | None:
        match = _LOCK_PATH.search(stderr)
        if not match:
            return None
        lock = Path(match.group(1))
        if not lock.is_absolute():
            lock = self.project / lock
        try:
            age = datetime.now(timezone.utc).timestamp() - lock.stat().st_mtime
        except OSError:
            return None
        if age < STALE_LOCK_SECONDS:
            return None
        try:
            lock.unlink()
        except OSError:
            return None
        return str(lock)

    def existing(self) -> list[str]:
        result = self._git("for-each-ref", "--format=%(refname)", self.prefix)
        if result.returncode:
            return []
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]

    def prune(self, retain_event_ids: Sequence[str]) -> list[str]:
        keep = {self.ref_name(event_id) for event_id in retain_event_ids}
        pruned = []
        for ref in self.existing():
            if ref in keep:
                continue
            if self._git("update-ref", "-d", ref).returncode == 0:
                pruned.append(ref)
        return pruned

    def publish(self, event_id: str, retain_event_ids: Sequence[str] | None = None) -> dict:
        ref = self.ref_name(event_id)
        descriptor = {
            "profile": GIT_REF_DOORBELL_PROFILE,
            "ref": ref,
            "event_id": event_id,
            "content": "event identifier in ref name; ref target is current HEAD",
            "scope": "local-only; no remote push is attempted",
        }
        result = self._git("update-ref", ref, "HEAD")
        if result.returncode:
            recovered = self._recover_stale_lock(result.stderr)
            if recovered:
                descriptor["recovered_stale_lock"] = recovered
                result = self._git("update-ref", ref, "HEAD")
        if result.returncode:
            return descriptor | {"state": "unavailable", "reason": result.stderr.strip()}
        if retain_event_ids is not None:
            descriptor["pruned"] = self.prune([*retain_event_ids, event_id])
        return descriptor | {"state": "current"}

    def status(self) -> dict:
        return {
            "profile": GIT_REF_DOORBELL_PROFILE,
            "namespace": self.prefix,
            "scope": "local-only; no remote push is attempted",
            "retention": f"newest {MAX_SIGNAL_REFS} ledger events",
            "ref_count": len(self.existing()),
            "stale_lock_recovery_seconds": STALE_LOCK_SECONDS,
        }


HEARTBEAT_PROFILE = "local-filesystem-heartbeat-v1"
HEARTBEAT_TTL_SECONDS = 90
OBSERVATION_MODES = ("watcher", "on-entry-only")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _actor_slug(actor: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in actor)


class Heartbeat:
    """Per-actor watcher liveness, observed rather than asserted.

    A watcher atomically replaces its own heartbeat file on every poll.  The
    binding derives ``active`` / ``stale`` / ``none`` per actor from the file's
    ``last_seen`` and never from a participant's own claim.  Like the doorbell,
    the file serves only participants on the same filesystem; that reach is
    disclosed, not hidden.
    """

    def __init__(self, project: Path) -> None:
        self.directory = project / ".awp-runtime"

    def path(self, actor: str) -> Path:
        return self.directory / f"coop2-heartbeat-{_actor_slug(actor)}.json"

    def publish(self, *, actor: str, profile: str, project_id: str, workstate_id: str, binding_id: str, frontier: list[str]) -> dict:
        self.directory.mkdir(parents=True, exist_ok=True)
        signal = {
            "profile": HEARTBEAT_PROFILE,
            "actor": actor,
            "watcher_profile": profile,
            "project_id": project_id,
            "workstate_id": workstate_id,
            "binding_id": binding_id,
            "frontier": frontier,
            "last_seen": now(),
        }
        target = self.path(actor)
        handle, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=self.directory)
        try:
            with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as temporary:
                json.dump(signal, temporary, sort_keys=True)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_name, target)
        except Exception:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass
            raise
        return signal | {"path": str(target)}

    def read(self, actor: str, *, binding_id: str, ttl_seconds: int = HEARTBEAT_TTL_SECONDS) -> dict:
        target = self.path(actor)
        if not target.exists():
            return {"watcher_liveness": "none"}
        try:
            signal = json.loads(target.read_text(encoding="utf-8"))
            last_seen = _parse_time(signal["last_seen"])
        except (OSError, ValueError, KeyError, TypeError) as error:
            return {"watcher_liveness": "unverified", "reason": str(error)}
        if signal.get("binding_id") != binding_id:
            return {"watcher_liveness": "unverified", "reason": "heartbeat identity does not match this binding"}
        age = (datetime.now(timezone.utc) - last_seen).total_seconds()
        liveness = "active" if age <= ttl_seconds else "stale"
        return {
            "watcher_liveness": liveness,
            "profile": signal.get("watcher_profile"),
            "last_seen": signal.get("last_seen"),
            "age_seconds": int(age),
            "frontier": signal.get("frontier", []),
        }


class Rendezvous:
    def __init__(self, project: Path, ledger_path: Path | None = None) -> None:
        self.project = find_project(project)
        self.workstate_id, _ = discover_workstate(self.project)
        self.project_id = stable_project_id(self.project)
        selected_ledger = ledger_path or self.project / ".awp-runtime" / "coop2-rendezvous.sqlite3"
        try:
            self.ledger = CoordinationLedger(selected_ledger)
        except (OSError, sqlite3.Error) as error:
            # Entry recovery must still read a durable store when the host
            # cannot acquire SQLite's normal lock/journal sidecars.  The
            # fallback is deliberately read-only: writes stay fail-closed.
            self.ledger = CoordinationLedger(selected_ledger, read_only=True)
            self.ledger.fallback_reason = str(error)
        self.doorbell = LocalDoorbell(self.project)
        self.git_ref_doorbell = GitRefDoorbell(self.project)
        self.heartbeats = Heartbeat(self.project)

    def _events(self) -> list[dict]:
        return self.ledger.export_events(self.workstate_id)

    def _registrations(self) -> dict[str, dict]:
        """Return the latest durable registration for each actor."""
        registrations: dict[str, dict] = {}
        for event in self._events():
            if event["kind"] == "coop2.participant.joined":
                registrations[event["payload"]["actor"]] = event["payload"] | {"event_id": event["event_id"]}
        return registrations

    def _reach(self) -> tuple[str, dict]:
        registrations = self._registrations()
        binding_id = self.ledger.binding_id()
        matching = sorted(
            actor for actor, registration in registrations.items()
            if registration.get("project_id") == self.project_id
            and registration.get("workstate_id") == self.workstate_id
            and registration.get("binding_id") == binding_id
        )
        evidence = {"kind": "participant-binding-handshake", "binding_id": binding_id, "actors": matching, "registration_events": [registrations[actor]["event_id"] for actor in matching]}
        return ("shared" if len(matching) >= 2 else "configured-unverified", evidence)

    def _append(self, actor: str, kind: str, payload: dict) -> dict:
        with self.ledger._transaction() as connection:
            event, _ = self.ledger._append(connection, workstate_id=self.workstate_id, actor=actor, kind=kind, payload=payload, occurred_at=now())
            return {"event_id": event["event_id"], "frontier": self.ledger._frontier(connection, self.workstate_id)}

    def _signal(self, receipt: dict, interaction_id: str, kind: str) -> dict:
        filesystem = self.doorbell.publish(
            project_id=self.project_id,
            workstate_id=self.workstate_id,
            binding_id=self.ledger.binding_id(),
            event_id=receipt["event_id"],
            frontier=receipt["frontier"],
            interaction_id=interaction_id,
            kind=kind,
        )
        recent = [event["event_id"] for event in self._events()[-MAX_SIGNAL_REFS:]]
        return {
            "filesystem": filesystem,
            "git_ref": self.git_ref_doorbell.publish(receipt["event_id"], retain_event_ids=recent),
        }

    def heartbeat(self, actor: str, profile: str) -> dict:
        """Publish this actor's watcher heartbeat (called by watchers on every poll)."""
        frontier = self.ledger.refresh(self.workstate_id)["frontier"] if not getattr(self.ledger, "read_only", False) else []
        return self.heartbeats.publish(
            actor=actor,
            profile=profile,
            project_id=self.project_id,
            workstate_id=self.workstate_id,
            binding_id=self.ledger.binding_id(),
            frontier=frontier,
        )

    def participant_watchers(self) -> list[dict]:
        """Per-actor watcher liveness derived from heartbeats, never from self-report."""
        binding_id = self.ledger.binding_id()
        result = []
        for actor, registration in sorted(self._registrations().items()):
            observed = self.heartbeats.read(actor, binding_id=binding_id)
            result.append(
                {
                    "actor": actor,
                    "declared_observation": registration.get("observation", "on-entry-only"),
                    **observed,
                }
            )
        return result

    def signal_reach(self, watchers: list[dict] | None = None) -> dict:
        """Reachability per ordered pair.  Mailbox reach is shared; signal reach is not."""
        watchers = watchers if watchers is not None else self.participant_watchers()
        liveness = {item["actor"]: item["watcher_liveness"] for item in watchers}
        matrix: dict[str, dict] = {}
        for sender in liveness:
            for recipient in liveness:
                if sender == recipient:
                    continue
                state = liveness[recipient]
                if state == "active":
                    reach = "reachable"
                elif state == "stale":
                    reach = "degraded"
                else:
                    reach = "entry-recovery-only"
                matrix[f"{sender}->{recipient}"] = {
                    "signal_reach": reach,
                    "recipient_watcher": state,
                    "fallback": "entry-recovery check on the recipient's next project entry",
                }
        return matrix

    def status(self) -> dict:
        reach, evidence = self._reach()
        watchers = self.participant_watchers()
        matrix = self.signal_reach(watchers)
        active = sorted(item["actor"] for item in watchers if item["watcher_liveness"] == "active")
        liveness_summary = (
            "derived from per-actor heartbeats; active: " + (", ".join(active) if active else "none")
        )
        doorbell = self.doorbell.status(project_id=self.project_id, workstate_id=self.workstate_id, binding_id=self.ledger.binding_id())
        doorbell["watcher_liveness"] = liveness_summary
        result = {
            "profile": PROFILE,
            "project_id": self.project_id,
            "workstate_id": self.workstate_id,
            "binding_id": self.ledger.binding_id(),
            "reach": reach,
            "mailbox_reach": reach,
            "delivery_mode": "signalled-poll",
            "doorbell": doorbell,
            "git_ref_doorbell": self.git_ref_doorbell.status(),
            "heartbeat": {"profile": HEARTBEAT_PROFILE, "ttl_seconds": HEARTBEAT_TTL_SECONDS, "directory": str(self.heartbeats.directory)},
            "participant_watchers": watchers,
            "signal_reach": matrix,
            "limitations": [
                "experimental pilot",
                "a host-side shared-filesystem watcher is required to wake a session",
                "heartbeats and doorbells serve only participants on this filesystem",
                "no semantic analyzer",
                "no authentication",
                "budget declaration is recorded but not host-enforced",
            ],
        }
        if getattr(self.ledger, "read_only", False):
            result["operational_mode"] = "degraded"
            result["read_only_reason"] = getattr(self.ledger, "fallback_reason", "normal SQLite access unavailable")
            result["limitations"].append("read-only recovery fallback; publication is unavailable")
        else:
            result["operational_mode"] = "ledger_bound"
        result["shared_reach_evidence"] = evidence
        return result

    def join(self, actor: str, capabilities: list[str], observation: str = "on-entry-only") -> dict:
        if observation not in OBSERVATION_MODES:
            raise CoordinationError(f"observation must be one of {', '.join(OBSERVATION_MODES)}")
        for event in reversed(self._events()):
            if event["kind"] == "coop2.participant.joined" and event["payload"]["actor"] == actor:
                if event["payload"].get("observation", "on-entry-only") == observation:
                    return {"participant": actor, "publication": "confirmed", "deduplicated": True, "receipt": {"event_id": event["event_id"]}, "binding": self.status()}
                break
        receipt = self._append(actor, "coop2.participant.joined", {"actor": actor, "project_id": self.project_id, "workstate_id": self.workstate_id, "binding_id": self.ledger.binding_id(), "capabilities": sorted(set(capabilities)), "availability": "available", "observation": observation})
        return {"participant": actor, "publication": "confirmed", "deduplicated": False, "receipt": receipt, "binding": self.status()}

    def peers(self, actor: str | None = None) -> dict:
        latest = self._registrations()
        if actor:
            latest.pop(actor, None)
        participants = [{"actor": item["actor"], "capabilities": item["capabilities"], "availability": item["availability"], "observation": item.get("observation", "on-entry-only"), "event_id": item["event_id"]} for item in latest.values()]
        return {"binding": self.status(), "participants": sorted(participants, key=lambda item: item["actor"])}

    def _request_event(self, interaction_id: str) -> dict:
        event = next((item for item in self._events() if item["kind"] == "coop2.interaction.requested" and item["payload"]["interaction_id"] == interaction_id), None)
        if event is None:
            raise CoordinationError("unknown interaction")
        return event

    def _interaction_events(self, interaction_id: str) -> list[dict]:
        return [item for item in self._events() if item["payload"].get("interaction_id") == interaction_id]

    def send(self, actor: str, recipient: str, purpose: str, subject: str, question: str, decision_owner: str, max_rounds: int, max_tool_calls: int, max_tokens: int, delivery_window_seconds: int, response_window_seconds: int) -> dict:
        if recipient not in {item["actor"] for item in self.peers()["participants"]}:
            raise CoordinationError("recipient is not registered in this project rendezvous")
        interaction_id = "interaction:" + hashlib.sha256(canonical([self.project_id, self.workstate_id, actor, recipient, purpose, subject, question]).encode()).hexdigest()[:24]
        for event in self._events():
            if event["kind"] == "coop2.interaction.requested" and event["payload"]["interaction_id"] == interaction_id:
                return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": True, "receipt": {"event_id": event["event_id"]}}
        payload = {"interaction_id": interaction_id, "sender": actor, "recipient": recipient, "purpose": purpose, "subject": subject, "question": question, "decision_owner": decision_owner, "authorization": {"participants": sorted([actor, recipient]), "max_rounds": max_rounds, "max_tool_calls": max_tool_calls, "max_total_output_tokens": max_tokens, "delivery_window_seconds": delivery_window_seconds, "response_window_seconds": response_window_seconds, "clock_authority": self.ledger.binding_id()}, "status": "open"}
        receipt = self._append(actor, "coop2.interaction.requested", payload)
        return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": False, "receipt": receipt, "doorbell": self._signal(receipt, interaction_id, "coop2.interaction.requested")}

    def observe(self, actor: str, interaction_id: str) -> dict:
        request = self._request_event(interaction_id)["payload"]
        if request["recipient"] != actor:
            raise CoordinationError("only the named recipient may observe an interaction")
        prior = next((event for event in self._interaction_events(interaction_id) if event["kind"] == "coop2.interaction.observed" and event["actor"] == actor), None)
        if prior:
            return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": True, "receipt": {"event_id": prior["event_id"]}}
        frontier = self.ledger.refresh(self.workstate_id)["frontier"]
        receipt = self._append(actor, "coop2.interaction.observed", {"interaction_id": interaction_id, "observing_actor": actor, "observed_at": now(), "binding_frontier": frontier, "disposition": "observed"})
        return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": False, "receipt": receipt, "doorbell": self._signal(receipt, interaction_id, "coop2.interaction.observed")}

    def accept(self, actor: str, interaction_id: str, response_window_seconds: int) -> dict:
        request = self._request_event(interaction_id)["payload"]
        if request["recipient"] != actor:
            raise CoordinationError("only the named recipient may accept an interaction")
        if not any(event["kind"] == "coop2.interaction.observed" and event["actor"] == actor for event in self._interaction_events(interaction_id)):
            raise CoordinationError("observe the interaction before accepting it")
        policy = request["authorization"]
        allowed = int(policy.get("response_window_seconds", 600))
        if response_window_seconds < 1 or response_window_seconds > allowed:
            raise CoordinationError("response deadline exceeds the interaction policy")
        prior = next((event for event in self._interaction_events(interaction_id) if event["kind"] == "coop2.interaction.accepted"), None)
        if prior:
            return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": True, "receipt": {"event_id": prior["event_id"]}}
        deadline = (datetime.now(timezone.utc) + timedelta(seconds=response_window_seconds)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        receipt = self._append(actor, "coop2.interaction.accepted", {"interaction_id": interaction_id, "observing_actor": actor, "observed_at": now(), "binding_frontier": self.ledger.refresh(self.workstate_id)["frontier"], "disposition": "accepted", "response_deadline": deadline})
        return {"interaction_id": interaction_id, "publication": "confirmed", "deduplicated": False, "receipt": receipt, "doorbell": self._signal(receipt, interaction_id, "coop2.interaction.accepted")}

    def refuse(self, actor: str, interaction_id: str, reason: str) -> dict:
        request = self._request_event(interaction_id)["payload"]
        if request["recipient"] != actor:
            raise CoordinationError("only the named recipient may refuse an interaction")
        if any(event["kind"] in {"coop2.interaction.accepted", "coop2.interaction.refused"} for event in self._interaction_events(interaction_id)):
            raise CoordinationError("interaction already has a delivery disposition")
        receipt = self._append(actor, "coop2.interaction.refused", {"interaction_id": interaction_id, "observing_actor": actor, "observed_at": now(), "binding_frontier": self.ledger.refresh(self.workstate_id)["frontier"], "disposition": "refused", "reason": reason})
        return {"interaction_id": interaction_id, "publication": "confirmed", "receipt": receipt, "doorbell": self._signal(receipt, interaction_id, "coop2.interaction.refused")}

    @staticmethod
    def _lifecycle(request_event: dict, interaction_events: list[dict], delivery: str) -> dict:
        """Derive the lifecycle state on read.  Windows are declared in the policy; this
        applies them so an expired interaction is reported as such rather than 'pending'."""
        policy = request_event["payload"].get("authorization", {})
        current = datetime.now(timezone.utc)
        published_at = _parse_time(request_event["occurred_at"])
        if delivery == "refused":
            return {"lifecycle_state": "refused", "timed_out": False}
        if delivery == "accepted":
            acceptance = next((item for item in interaction_events if item["kind"] == "coop2.interaction.accepted"), None)
            deadline_text = acceptance["payload"].get("response_deadline") if acceptance else None
            deadline = _parse_time(deadline_text) if deadline_text else published_at + timedelta(seconds=int(policy.get("response_window_seconds", 600)))
            state, expired_state = "accepted", "delivered_unanswered"
        elif delivery == "observed":
            observed = next((item for item in interaction_events if item["kind"] == "coop2.interaction.observed"), None)
            observed_at = _parse_time(observed["occurred_at"]) if observed else published_at
            deadline = observed_at + timedelta(seconds=int(policy.get("response_window_seconds", 600)))
            state, expired_state = "observed", "delivered_unanswered"
        else:
            deadline = published_at + timedelta(seconds=int(policy.get("delivery_window_seconds", 600)))
            state, expired_state = "pending", "undelivered"
        remaining = int((deadline - current).total_seconds())
        if remaining < 0:
            return {"lifecycle_state": expired_state, "timed_out": True, "deadline": deadline.replace(microsecond=0).isoformat().replace("+00:00", "Z"), "overdue_seconds": -remaining}
        return {"lifecycle_state": state, "timed_out": False, "deadline": deadline.replace(microsecond=0).isoformat().replace("+00:00", "Z"), "seconds_remaining": remaining}

    def inbox(self, actor: str) -> dict:
        answered = {event["payload"]["interaction_id"] for event in self._events() if event["kind"] == "coop2.interaction.responded"}
        requests = []
        for event in self._events():
            if event["kind"] != "coop2.interaction.requested" or event["payload"]["recipient"] != actor or event["payload"]["interaction_id"] in answered:
                continue
            interaction_events = self._interaction_events(event["payload"]["interaction_id"])
            delivery = next((item["kind"].rsplit(".", 1)[-1] for item in reversed(interaction_events) if item["kind"] in {"coop2.interaction.observed", "coop2.interaction.accepted", "coop2.interaction.refused"}), "published")
            requests.append(event["payload"] | {"event_id": event["event_id"], "delivery_state": delivery, **self._lifecycle(event, interaction_events, delivery)})
        responses = [event["payload"] | {"event_id": event["event_id"]} for event in self._events() if event["kind"] == "coop2.interaction.responded" and event["payload"]["recipient"] == actor]
        return {"binding": self.status(), "inbox": requests, "responses": responses}

    def respond(self, actor: str, interaction_id: str, outcome: str, response: str) -> dict:
        request = self._request_event(interaction_id)["payload"]
        if request["recipient"] != actor:
            raise CoordinationError("only the named recipient may respond")
        acceptance = next((event for event in self._interaction_events(interaction_id) if event["kind"] == "coop2.interaction.accepted" and event["actor"] == actor), None)
        if acceptance is None:
            raise CoordinationError("accept the interaction before responding")
        deadline = datetime.fromisoformat(acceptance["payload"]["response_deadline"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > deadline:
            raise CoordinationError("response deadline has elapsed; the interaction is delivered_unanswered")
        if any(event["kind"] == "coop2.interaction.responded" and event["payload"]["interaction_id"] == interaction_id for event in self._events()):
            raise CoordinationError("interaction already has a response")
        receipt = self._append(actor, "coop2.interaction.responded", {"interaction_id": interaction_id, "sender": actor, "recipient": request["sender"], "outcome": outcome, "response": response, "status": "closed"})
        return {"interaction_id": interaction_id, "publication": "confirmed", "receipt": receipt, "doorbell": self._signal(receipt, interaction_id, "coop2.interaction.responded")}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--project", type=Path, default=Path.cwd())
    result.add_argument("--ledger", type=Path)
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("doorbell-status")
    join = commands.add_parser("join"); join.add_argument("--actor", required=True); join.add_argument("--capability", action="append", default=[]); join.add_argument("--observation", choices=list(OBSERVATION_MODES), default="on-entry-only", help="how this actor observes signals: a live watcher, or only on project entry")
    heartbeat = commands.add_parser("heartbeat"); heartbeat.add_argument("--actor", required=True); heartbeat.add_argument("--profile", default="manual-heartbeat")
    peers = commands.add_parser("peers"); peers.add_argument("--actor")
    send = commands.add_parser("send"); send.add_argument("--actor", required=True); send.add_argument("--to", required=True); send.add_argument("--purpose", choices=["review", "critique", "alternative", "delegation", "decision", "synthesis"], required=True); send.add_argument("--subject", required=True); send.add_argument("--question", required=True); send.add_argument("--decision-owner", required=True); send.add_argument("--max-rounds", type=int, default=1); send.add_argument("--max-tool-calls", type=int, default=4); send.add_argument("--max-tokens", type=int, default=1200); send.add_argument("--delivery-window-seconds", type=int, default=300); send.add_argument("--response-window-seconds", type=int, default=600)
    inbox = commands.add_parser("inbox"); inbox.add_argument("--actor", required=True)
    observe = commands.add_parser("observe"); observe.add_argument("--actor", required=True); observe.add_argument("--interaction", required=True)
    accept = commands.add_parser("accept"); accept.add_argument("--actor", required=True); accept.add_argument("--interaction", required=True); accept.add_argument("--response-window-seconds", type=int, default=600)
    refuse = commands.add_parser("refuse"); refuse.add_argument("--actor", required=True); refuse.add_argument("--interaction", required=True); refuse.add_argument("--reason", required=True)
    respond = commands.add_parser("respond"); respond.add_argument("--actor", required=True); respond.add_argument("--interaction", required=True); respond.add_argument("--outcome", choices=["accepted", "revised", "inconclusive", "declined", "timed_out", "escalated"], required=True); respond.add_argument("--response", required=True)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        rendezvous = Rendezvous(args.project, args.ledger)
        if args.command == "status": result = rendezvous.status()
        elif args.command == "doorbell-status": result = rendezvous.doorbell.status(project_id=rendezvous.project_id, workstate_id=rendezvous.workstate_id, binding_id=rendezvous.ledger.binding_id())
        elif args.command == "join": result = rendezvous.join(args.actor, args.capability, args.observation)
        elif args.command == "heartbeat": result = rendezvous.heartbeat(args.actor, args.profile)
        elif args.command == "peers": result = rendezvous.peers(args.actor)
        elif args.command == "send": result = rendezvous.send(args.actor, args.to, args.purpose, args.subject, args.question, args.decision_owner, args.max_rounds, args.max_tool_calls, args.max_tokens, args.delivery_window_seconds, args.response_window_seconds)
        elif args.command == "inbox": result = rendezvous.inbox(args.actor)
        elif args.command == "observe": result = rendezvous.observe(args.actor, args.interaction)
        elif args.command == "accept": result = rendezvous.accept(args.actor, args.interaction, args.response_window_seconds)
        elif args.command == "refuse": result = rendezvous.refuse(args.actor, args.interaction, args.reason)
        else: result = rendezvous.respond(args.actor, args.interaction, args.outcome, args.response)
        print(json.dumps(result, indent=2, sort_keys=True)); return 0
    except (CoordinationError, OSError, ValueError) as error:
        print(json.dumps({"error": str(error)}, indent=2)); return 2


if __name__ == "__main__":
    raise SystemExit(main())
