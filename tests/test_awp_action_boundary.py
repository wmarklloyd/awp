"""Tests for the Action Boundary reference resolver (tools/awp_action_boundary.py).

test_incident_scenario_is_now_denied reconstructs the android_sports_watches
incident this module was scoped from: a freeform image-generation call
against a protected, literal-imagery-only artifact class. Before this
module existed, nothing stopped that call. This test is the module's own
evidence that its resolver would have said "deny".
"""

from __future__ import annotations

import unittest

from tools.awp_action_boundary import (
    RESULT_DENY,
    RESULT_PERMIT,
    RESULT_UNRESOLVED,
    resolve_action,
)


GUARDRAIL = {
    "id": "constraint:no-invented-product-imagery",
    "type": "constraint",
    "status": "active",
    "effect": "deny",
    "applies_to": "all_actors",
    "operation_classes": ["generative:freeform"],
    "resources": ["artifact-class:public-promotional-watch-imagery"],
    "policy_owner": "actor:project-owner",
    "enforcement": "protected_adapter",
    "propagation": "mandatory",
}

DECISION = {
    "id": "decision:public-watch-imagery-uses-literal-product-surfaces",
    "type": "decision",
    "status": "accepted",
    "choice": "Public product imagery MUST depict only real, source-matched watch displays.",
    # Core's own `affects` names the specific artifact this decision already
    # governs, per core.md's decision-closure semantics -- it is a record/
    # artifact reference, not a selector, and the resolver does not read it.
    "affects": ["artifact:play-store-assets/baseball/feature-graphic.png"],
    # This module's own extension namespace (core.md: "modules.{module-id}"),
    # carrying the glob-matchable selector and requirements this resolver
    # actually reads -- see action-boundary.md section 3.1.
    "modules": {
        "urn:awp:action-boundary": {
            "selectors": ["artifact-class:public-promotional-watch-imagery"],
            "requirements": ["depicted screen pixels must derive from a verified product capture"],
        }
    },
}

DECISION_WITH_UNQUALIFIED_AFFECTS_ONLY = {
    "id": "decision:core-only-affects-no-module-extension",
    "type": "decision",
    "status": "accepted",
    "choice": "A decision that only sets Core's plain `affects` and never "
    "declares this module's extension.",
    "affects": ["artifact-class:public-promotional-watch-imagery"],
}

COMPLETE_ENTRY = {"selection": "complete", "decision_context": "complete"}
BUDGET_EXCEEDED_ENTRY = {"selection": "budget_exceeded", "decision_context": "absent"}


def _action(operation_class: str, actor: str = "actor:agent-session-7") -> dict:
    return {
        "operation_class": operation_class,
        "resource": "google-play:baseball",
        "artifact_class": "artifact-class:public-promotional-watch-imagery",
        "actor": actor,
    }


class ActionResolutionTests(unittest.TestCase):
    def test_incident_scenario_is_now_denied(self) -> None:
        """The exact shape of the original incident: a freeform generation
        call against a protected artifact class, with a matching guardrail
        already declared. Must resolve deny, and must do so even though the
        re-entry projection is budget_exceeded -- a known deny is not
        weakened by incomplete visibility elsewhere.
        """
        resolution = resolve_action(
            _action("generative:freeform"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=BUDGET_EXCEEDED_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_DENY)
        self.assertIn("constraint:no-invented-product-imagery", resolution["applicable_guardrails"])

    def test_composite_operation_permitted_when_context_complete(self) -> None:
        resolution = resolve_action(
            _action("generative:composite"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_PERMIT)
        self.assertIn(
            "depicted screen pixels must derive from a verified product capture",
            resolution["requirements"],
        )

    def test_composite_operation_unresolved_on_incomplete_entry(self) -> None:
        """The original bug: an incomplete/budget_exceeded re-entry result
        must never be treated as sufficient for a permit, even for an
        operation class no guardrail denies.
        """
        resolution = resolve_action(
            _action("generative:composite"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=BUDGET_EXCEEDED_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_UNRESOLVED)

    def test_unrelated_operation_class_is_not_gated_by_the_guardrail(self) -> None:
        resolution = resolve_action(
            _action("text.edit"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(resolution["applicable_guardrails"], [])
        self.assertEqual(resolution["result"], RESULT_PERMIT)

    def test_guardrail_with_policy_owner_equal_to_actor_is_unresolved(self) -> None:
        self_authored = dict(GUARDRAIL, policy_owner="actor:agent-session-7")
        resolution = resolve_action(
            _action("generative:freeform", actor="actor:agent-session-7"),
            guardrails=[self_authored],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_UNRESOLVED)
        self.assertIn("AWP-ACTION-GUARDRAIL-OWNER-INVALID", resolution["diagnostics"])

    def test_selector_matches_a_target_that_did_not_exist_at_authoring_time(self) -> None:
        """action-boundary.md section 3.1: a glob selector authored before a
        target existed must still match it once it does.
        """
        glob_guardrail = dict(GUARDRAIL, resources=["artifact-class:public-promotional-*"])
        action = _action("generative:freeform")
        action["artifact_class"] = "artifact-class:public-promotional-hiking-boot-imagery"
        resolution = resolve_action(
            action,
            guardrails=[glob_guardrail],
            decisions=[],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_DENY)

    def test_require_review_guardrail_is_unresolved_not_permitted(self) -> None:
        review_guardrail = dict(GUARDRAIL, effect="require_review")
        resolution = resolve_action(
            _action("generative:freeform"),
            guardrails=[review_guardrail],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(resolution["result"], RESULT_UNRESOLVED)

    def test_core_affects_alone_does_not_make_a_decision_apply(self) -> None:
        """core.md: an optional module MUST NOT reinterpret Core's `affects`
        field. A decision that sets plain `affects` but never declares this
        module's own `modules.urn:awp:action-boundary` extension must not be
        matched by the resolver, even though its `affects` value textually
        equals the action's artifact_class.
        """
        resolution = resolve_action(
            _action("generative:composite"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION_WITH_UNQUALIFIED_AFFECTS_ONLY],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(resolution["applicable_decisions"], [])
        self.assertEqual(resolution["requirements"], [])

    def test_resolution_is_digest_bound_and_deterministic(self) -> None:
        first = resolve_action(
            _action("generative:composite"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
        )
        second = resolve_action(
            _action("generative:composite"),
            guardrails=[GUARDRAIL],
            decisions=[DECISION],
            entry_status=COMPLETE_ENTRY,
        )
        self.assertEqual(first["action_digest"], second["action_digest"])


if __name__ == "__main__":
    unittest.main()
