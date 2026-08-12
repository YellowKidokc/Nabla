from __future__ import annotations

from typing import Any


def evaluate(record: dict[str, Any]) -> dict[str, Any]:
    tests = record.get("atom_stack", {}).get("tests", [])
    unresolved = record.get("unresolved", [])
    return {
        "class": record.get("reality_mirror", {}).get("class", "UNKNOWN"),
        "kill_conditions_declared": sum(row.get("type") == "kill_condition" for row in tests),
        "unresolved_count": len(unresolved),
        "admission_effect": "constraint_only",
    }
