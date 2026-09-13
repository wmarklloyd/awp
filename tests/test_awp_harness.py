"""Tests for the harness prototype (tools/awp_harness.py, tools/awp_ci_gate.py).

Several tests are direct implementations of the minimum conformance
fixtures listed in
research/model-assisted-reviews/codex-harness-reconciliation-evaluation.md
("Minimum conformance fixtures"), noted per-test below.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools.awp_action_boundary import RESULT_DENY, RESULT_PERMIT, RESULT_UNRESOLVED
from tools.awp_ci_gate import run_gate, verify_artifact_claim
from tools.awp_harness import (
    HarnessError,
    accept_decision,
    compute_invocation_binding,
    decision_index,
    enforce,
    gate,
    propose_decision,
    session_compliance_report,
)
from tests.test_awp_action_boundary import (
    BUDGET_EXCEEDED_ENTRY,
    COMPLETE_ENTRY,
    DECISION,
    DECISION_WITH_UNQUALIFIED_AFFECTS_ONLY,
    GUARDRAIL,
    _action,
)


class DecisionIndexTests(unittest.TestCase):
    def test_only_module_extended_decisions_are_included(self) -> None:
        projection = decision_index(
            [DECISION, DECISION_WITH_UNQUALIFIED_AFFECTS_ONLY],
            capsule_digest="sha256:" + "0" * 64,
        )
        ids = [d["id"] for d in projection["decisions"]]
        self.assertIn(DECISION["id"], ids)
        self.assertNotIn(DECISION_WITH_UNQUALIFIED_AFFECTS_ONLY["id"], ids)
        self.assertFalse(projection["truncated"])
        self.assertTrue(projection["index_digest"].startswith("sha256:"))

    def test_tight_budget_truncates_to_id_and_summary_only(self) -> None:
        projection = decision_index(
            [DECISION],
            capsule_digest="sha256:" + "0" * 64,
            budget_bytes=10,
        )
        self.assertTrue(projection["truncated"])
        entry = projection["decisions"][0]
        self.assertEqual(set(entry.keys()), {"id", "affects_summary", "status"})


class GateTests(unittest.TestCase):
    def test_incident_scenario_is_denied_through_the_harness_gate(self) -> None:
        resolution, exit_code = gate(
            _action("generative:freeform"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=BUDGET_EXCEEDED_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_DENY)
        self.assertEqual(exit_code, 1)

    def test_gate_with_tool_args_attaches_invocation_binding_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "events.jsonl"
            resolution, exit_code = gate(
                _action("generative:composite"),
                guardrails=[GUARDRAIL],
                decisions=[DECISION],
                entry_status=COMPLETE_ENTRY,
                tool_name="image-composer",
                tool_version="1.0",
                tool_arguments={"source": "website/assets/baseball-live.svg"},
                event_log_path=log_path,
            )
            self.assertEqual(exit_code, 0)
            self.assertIn("invocation_binding", resolution)
            self.assertEqual(resolution["invocation_binding"]["tool"], "image-composer")
            logged = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(logged), 1)
            self.assertEqual(logged[0]["action_digest"], resolution["action_digest"])


class EnforceTests(unittest.TestCase):
    """Fixture 4: tool arguments changed after resolution produce a mismatch and block."""

    def _permitted_resolution(self, arguments: dict) -> dict:
        resolution, _exit = gate(
            _action("generative:composite"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
            tool_name="image-composer",
            tool_version="1.0",
            tool_arguments=arguments,
        )
        assert resolution["result"] == RESULT_PERMIT
        return resolution

    def test_matching_call_stays_permitted(self) -> None:
        original_args = {"source": "website/assets/baseball-live.svg"}
        resolution = self._permitted_resolution(original_args)
        verified, exit_code = enforce(
            resolution, tool_name="image-composer", tool_version="1.0", arguments=original_args
        )
        self.assertEqual(verified["result"], RESULT_PERMIT)
        self.assertEqual(exit_code, 0)

    def test_changed_arguments_after_resolution_are_denied(self) -> None:
        resolution = self._permitted_resolution({"source": "website/assets/baseball-live.svg"})
        verified, exit_code = enforce(
            resolution,
            tool_name="image-composer",
            tool_version="1.0",
            arguments={"source": "website/assets/DIFFERENT-source.svg"},
        )
        self.assertEqual(verified["result"], RESULT_DENY)
        self.assertEqual(exit_code, 1)
        self.assertTrue(any("AWP-HARNESS-INVOCATION-MISMATCH" in d for d in verified["diagnostics"]))

    def test_a_denied_resolution_is_not_upgraded_by_a_matching_call(self) -> None:
        resolution, _exit = gate(
            _action("generative:freeform"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
            tool_name="image-generation",
            tool_arguments={},
        )
        self.assertEqual(resolution["result"], RESULT_DENY)
        verified, exit_code = enforce(resolution, tool_name="image-generation", tool_version=None, arguments={})
        self.assertEqual(verified["result"], RESULT_DENY)
        self.assertEqual(exit_code, 1)


class DecisionCaptureTests(unittest.TestCase):
    """Fixture 8: decision-capture suggestions never become binding without
    policy-owner acceptance."""

    def test_proposed_decision_is_not_accepted(self) -> None:
        decision, provenance = propose_decision(
            decision_id="decision:candidate-from-corrective-commit",
            choice="Public product imagery MUST depict only real, source-matched watch displays.",
            selectors=["artifact-class:public-promotional-watch-imagery"],
            requirements=["depicted screen pixels must derive from a verified product capture"],
            proposed_by_actor="actor:agent-session-7",
        )
        self.assertEqual(decision["status"], "proposed")
        self.assertNotIn("proposed_by_actor", decision)  # host-local provenance stays off the record
        self.assertEqual(provenance["proposed_by_actor"], "actor:agent-session-7")

    def test_proposer_cannot_accept_their_own_proposal(self) -> None:
        decision, provenance = propose_decision(
            decision_id="decision:x", choice="x", proposed_by_actor="actor:agent-session-7",
        )
        with self.assertRaises(HarnessError):
            accept_decision(
                decision,
                policy_owner="actor:project-owner",
                actor="actor:agent-session-7",
                proposed_by_actor=provenance["proposed_by_actor"],
            )

    def test_proposer_cannot_be_named_as_policy_owner_even_if_someone_else_clicks_accept(self) -> None:
        decision, provenance = propose_decision(
            decision_id="decision:x", choice="x", proposed_by_actor="actor:agent-session-7",
        )
        with self.assertRaises(HarnessError):
            accept_decision(
                decision,
                policy_owner="actor:agent-session-7",
                actor="actor:project-owner",
                proposed_by_actor=provenance["proposed_by_actor"],
            )

    def test_policy_owner_accepting_their_own_accountable_decision_is_the_ordinary_case(self) -> None:
        """policy_owner == actor is expected and fine -- the accountable
        human reviewing and accepting their own decision. Only the original
        proposer is excluded (see the two tests above)."""
        decision, provenance = propose_decision(
            decision_id="decision:x", choice="x", proposed_by_actor="actor:agent-session-7",
        )
        accepted, event = accept_decision(
            decision,
            policy_owner="actor:project-owner",
            actor="actor:project-owner",
            proposed_by_actor=provenance["proposed_by_actor"],
        )
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(event["policy_owner"], "actor:project-owner")

    def test_cannot_accept_an_already_accepted_decision(self) -> None:
        decision, provenance = propose_decision(
            decision_id="decision:x", choice="x", proposed_by_actor="actor:agent-session-7",
        )
        accepted, _event = accept_decision(
            decision,
            policy_owner="actor:project-owner",
            actor="actor:project-owner",
            proposed_by_actor=provenance["proposed_by_actor"],
        )
        with self.assertRaises(HarnessError):
            accept_decision(accepted, policy_owner="actor:someone-else", actor="actor:someone-else")


class ComplianceReportTests(unittest.TestCase):
    def test_report_is_an_execution_claim_evidence_triple(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "events.jsonl"
            gate(
                _action("generative:composite"), [GUARDRAIL], [DECISION], COMPLETE_ENTRY,
                tool_name="image-composer", tool_arguments={"source": "x"}, event_log_path=log_path,
            )
            gate(
                _action("generative:freeform"), [GUARDRAIL], [DECISION], COMPLETE_ENTRY,
                event_log_path=log_path,
            )
            report = session_compliance_report(
                log_path, session_id="sess-1", reviewer_actor="actor:agent-session-7",
                capsule_digest="sha256:" + "0" * 64,
            )
        self.assertEqual(report["execution"]["type"], "execution")
        self.assertEqual(report["claim"]["type"], "claim")
        self.assertEqual(report["evidence"]["type"], "evidence")
        self.assertIn("1 permit", report["claim"]["statement"])
        self.assertIn("1 deny", report["claim"]["statement"])
        self.assertEqual(report["evidence"]["modules"]["urn:awp:harness-runtime"]["entry_count"], 2)

    def test_empty_log_is_honestly_unverified(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "events.jsonl"
            report = session_compliance_report(log_path, session_id="sess-empty", reviewer_actor="actor:x")
        self.assertEqual(report["claim"]["epistemic_status"], "unverified")


class CiGateTests(unittest.TestCase):
    """Fixtures around the actual (agent-blind) enforcement point."""

    def _write(self, path: Path, content: bytes) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        import hashlib

        return "sha256:" + hashlib.sha256(content).hexdigest()

    def test_protected_path_without_a_claim_is_a_violation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write(repo / "play-store-assets/baseball/feature-graphic.png", b"fake-png-bytes")
            ok, violations = run_gate(
                changed_paths=["play-store-assets/baseball/feature-graphic.png"],
                protected_paths=[{
                    "artifact_class": "artifact-class:public-promotional-watch-imagery",
                    "path_globs": ["play-store-assets/**/*.png"],
                    "resource": "google-play:baseball",
                }],
                artifact_claims=[],
                guardrails=[GUARDRAIL],
                decisions=[DECISION],
                repo_root=repo,
            )
            self.assertFalse(ok)
            self.assertTrue(any("no artifact-claim record" in v for v in violations))

    def test_verified_claim_with_matching_digest_and_permitted_resolution_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write(repo / "play-store-assets/baseball/feature-graphic.png", b"fake-png-bytes")
            source_digest = self._write(repo / "website/assets/baseball-live.svg", b"real-source-svg")
            claim = {
                "artifact": "play-store-assets/baseball/feature-graphic.png",
                "claims": [{
                    "claim": "depicted-watch-interface-exists",
                    "evidence": {
                        "source_artifact": "website/assets/baseball-live.svg",
                        "source_digest": source_digest,
                        "transformation": "literal-composite",
                    },
                    "status": "verified",
                }],
            }
            ok, violations = run_gate(
                changed_paths=["play-store-assets/baseball/feature-graphic.png"],
                protected_paths=[{
                    "artifact_class": "artifact-class:public-promotional-watch-imagery",
                    "path_globs": ["play-store-assets/**/*.png"],
                    "resource": "google-play:baseball",
                }],
                artifact_claims=[claim],
                guardrails=[GUARDRAIL],
                decisions=[DECISION],
                repo_root=repo,
            )
            self.assertTrue(ok, violations)

    def test_claim_with_stale_source_digest_is_a_violation(self) -> None:
        """A claim's evidence.source_digest that no longer matches the actual
        source file on disk (the source was edited after the claim was
        written) must be caught, not trusted -- action-boundary.md section 6:
        "must be a mechanical byproduct... not a participant's self-report."
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._write(repo / "website/assets/baseball-live.svg", b"original-content")
            claim = {
                "artifact": "play-store-assets/baseball/feature-graphic.png",
                "claims": [{
                    "claim": "depicted-watch-interface-exists",
                    "evidence": {
                        "source_artifact": "website/assets/baseball-live.svg",
                        "source_digest": "sha256:" + "0" * 64,  # stale/fabricated
                        "transformation": "literal-composite",
                    },
                    "status": "verified",
                }],
            }
            problems = verify_artifact_claim(claim, repo_root=repo)
            self.assertTrue(any("does not match the current content" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
