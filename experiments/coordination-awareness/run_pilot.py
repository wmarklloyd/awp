"""Run the deterministic coordination-awareness instrumentation pilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CASES = ROOT / "cases.json"
RESULT_JSON = ROOT / "results" / "pilot-results.json"
RESULT_MD = ROOT / "results" / "pilot-report.md"
WRITE_ACCESSES = {"write", "create", "delete", "propose_change", "integrate"}


def chat_warning(case: dict) -> bool:
    return bool(case["chat"]["explicit_conflict_warning"])


def git_warning(case: dict) -> bool:
    left, right = case["participants"]
    return bool(set(left["changed_paths"]) & set(right["changed_paths"]))


def awp_warning(case: dict) -> bool:
    left, right = case["participants"]
    for left_scope in left["scopes"]:
        for right_scope in right["scopes"]:
            if (
                left_scope["kind"] == right_scope["kind"]
                and left_scope["target"] == right_scope["target"]
                and (
                    left_scope["access"] in WRITE_ACCESSES
                    or right_scope["access"] in WRITE_ACCESSES
                )
            ):
                return True
    return False


def metrics(cases: list[dict], detector) -> dict:
    counts = {"true_positive": 0, "true_negative": 0, "false_positive": 0, "false_negative": 0}
    classifications = []
    for case in cases:
        predicted = detector(case)
        actual = case["ground_truth_conflict"]
        key = (
            "true_positive" if predicted and actual else
            "false_positive" if predicted else
            "false_negative" if actual else
            "true_negative"
        )
        counts[key] += 1
        classifications.append({"case": case["id"], "predicted_conflict": predicted, "outcome": key})
    positives = counts["true_positive"] + counts["false_positive"]
    actual_positives = counts["true_positive"] + counts["false_negative"]
    return {
        **counts,
        "precision": counts["true_positive"] / positives if positives else None,
        "recall": counts["true_positive"] / actual_positives if actual_positives else None,
        "classifications": classifications,
    }


def run() -> dict:
    fixture = json.loads(CASES.read_text(encoding="utf-8"))
    cases = fixture["cases"]
    return {
        "study": "coordination-awareness synthetic instrumentation pilot",
        "fixture_version": fixture["fixture_version"],
        "case_count": len(cases),
        "conditions": {
            "chat_only_proxy": {**metrics(cases, chat_warning), "warning_phase": "message-time-if-explicit"},
            "git_only_proxy": {**metrics(cases, git_warning), "warning_phase": "post-change"},
            "awp_assisted_proxy": {**metrics(cases, awp_warning), "warning_phase": "pre-implementation-declaration"},
        },
        "unmeasured": ["agent_behavior", "authoring_time", "coordination_delay", "token_cost", "integration_success"],
        "interpretation_limit": "These results verify fixture instrumentation only and do not estimate real-world AWP effectiveness.",
    }


def render_markdown(result: dict) -> str:
    lines = [
        "# Synthetic pilot report",
        "",
        "**Status:** Instrumentation check; not an independent-agent experiment",
        "",
        f"The pilot evaluated {result['case_count']} fixed cases. The ground truth and detection rules are encoded in the repository, so the results establish only that the measurement implementation behaves as specified.",
        "",
        "| Condition | TP | TN | FP | FN | Recall | Warning phase |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for name, values in result["conditions"].items():
        recall = "n/a" if values["recall"] is None else f"{values['recall']:.2f}"
        lines.append(
            f"| `{name}` | {values['true_positive']} | {values['true_negative']} | "
            f"{values['false_positive']} | {values['false_negative']} | {recall} | "
            f"{values['warning_phase']} |"
        )
    lines.extend(
        [
            "",
            "The AWP-assisted proxy recognizes all encoded physical and semantic overlaps; the Git-only proxy recognizes only the same-file case; and the chat-only proxy recognizes none because the fixtures contain no explicit chat warning. This is an expected consequence of the fixture definitions, not a measured treatment effect.",
            "",
            "Agent behavior, authoring time, coordination delay, token cost, and integration success were not measured. The preregistered independent-agent protocol must be run before making effectiveness claims.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="write deterministic result artifacts")
    mode.add_argument("--check", action="store_true", help="verify checked-in result artifacts")
    args = parser.parse_args()
    result = run()
    json_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    markdown_text = render_markdown(result)
    if args.write:
        RESULT_JSON.parent.mkdir(parents=True, exist_ok=True)
        RESULT_JSON.write_text(json_text, encoding="utf-8", newline="\n")
        RESULT_MD.write_text(markdown_text, encoding="utf-8", newline="\n")
        print(f"Wrote {RESULT_JSON.relative_to(ROOT)} and {RESULT_MD.relative_to(ROOT)}")
        return 0
    failures = []
    if not RESULT_JSON.exists() or RESULT_JSON.read_text(encoding="utf-8") != json_text:
        failures.append(str(RESULT_JSON.relative_to(ROOT)))
    if not RESULT_MD.exists() or RESULT_MD.read_text(encoding="utf-8") != markdown_text:
        failures.append(str(RESULT_MD.relative_to(ROOT)))
    if failures:
        print("Stale or missing result artifacts: " + ", ".join(failures))
        return 1
    print("OK: synthetic pilot results are reproducible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
