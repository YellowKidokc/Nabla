#!/usr/bin/env python3
"""Human-guided Natural Process Mirror worksheet and deterministic gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


QUESTIONS = [
    "What is the source process, stated without its desired conclusion?",
    "What are its ordered stages or indispensable parts?",
    "What endogenous natural process is proposed, and in what domain?",
    "For every source stage, what natural stage corresponds in the same order?",
    "Does each paired stage preserve direction?",
    "Does each paired stage preserve function?",
    "What constraints and failure modes are preserved?",
    "What is lost, introduced, or forbidden by the translation?",
    "What natural evidence anchors the proposed process outside this framework?",
    "What counterexample, ablation, or rival process would defeat the mapping?",
    "Was the proposed natural process selected before the conclusion it is asked to support?",
]


def make_walk(source_process: str, source_stages: list[str]) -> dict[str, Any]:
    return {
        "schema_version": "atlas-natural-process-walk/v1",
        "state": "in_progress",
        "source_process": source_process,
        "questions": [{"number": i + 1, "question": question, "answer": None} for i, question in enumerate(QUESTIONS)],
        "source_stages": source_stages,
        "natural_domain": "unknown",
        "natural_process": "",
        "stage_map": [
            {"source_stage": stage, "natural_stage": "", "same_order": False,
             "same_direction": False, "same_function": False, "notes": ""}
            for stage in source_stages
        ],
        "constraints_preserved": [], "failure_modes_preserved": [],
        "lost": [], "introduced": [], "forbidden": [], "external_anchors": [],
        "negative_controls": [], "ablation": [], "rival_explanations": [],
        "descent_created_after_ascent_observed": "unknown",
        "mirror_gate_status": "UNRESOLVED",
        "next_question": 1,
    }


def evaluate_walk(walk: dict[str, Any]) -> dict[str, Any]:
    rows = walk.get("stage_map", [])
    source_count = len(walk.get("source_stages", []))
    complete = source_count > 0 and len(rows) == source_count and all(
        row.get("natural_stage") and row.get("same_order") and row.get("same_direction") and row.get("same_function")
        for row in rows
    )
    anchored = bool(walk.get("external_anchors"))
    challenged = bool(walk.get("negative_controls") or walk.get("ablation") or walk.get("rival_explanations"))
    post_hoc = walk.get("descent_created_after_ascent_observed") is True
    if complete and anchored and challenged and not post_hoc:
        status = "PASSED_CANDIDATE"
    elif walk.get("natural_process"):
        status = "PARTIAL"
    else:
        status = "NEEDS_NATURAL_ANCHOR"
    result = dict(walk)
    result["mirror_gate_status"] = status
    result["state"] = "ready_for_review" if status == "PASSED_CANDIDATE" else "in_progress"
    result["computed"] = {
        "part_count_source": source_count, "part_count_mirror": len(rows),
        "same_order_count": sum(bool(row.get("same_order")) for row in rows),
        "same_direction_count": sum(bool(row.get("same_direction")) for row in rows),
        "same_function_count": sum(bool(row.get("same_function")) for row in rows),
        "externally_anchored": anchored, "challenged_by_control": challenged, "post_hoc_warning": post_hoc,
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or evaluate a guided Natural Process Mirror walk.")
    parser.add_argument("--source-process"); parser.add_argument("--source-stages", type=Path)
    parser.add_argument("--input", type=Path); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input:
        walk = json.loads(args.input.read_text(encoding="utf-8"))
        result = evaluate_walk(walk)
    else:
        if not args.source_process or not args.source_stages:
            raise SystemExit("--source-process and --source-stages are required when creating a walk")
        stages = [line.strip() for line in args.source_stages.read_text(encoding="utf-8").splitlines() if line.strip()]
        result = make_walk(args.source_process, stages)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{args.output}\nstatus={result['mirror_gate_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
