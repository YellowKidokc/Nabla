from __future__ import annotations

from typing import Any


def score(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    left_domains = set(left.get("periodic15", {}).get("m03_native_domains", []))
    right_domains = set(right.get("periodic15", {}).get("m03_native_domains", []))
    union = left_domains | right_domains
    return {"domain_overlap": len(left_domains & right_domains) / len(union) if union else 1.0,
            "status": "comparison_only", "promotes_grade": False}
