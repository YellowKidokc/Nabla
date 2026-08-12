from __future__ import annotations

import re
from typing import Any


def _tokens(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", value.lower()) if len(token) > 2}


def _claim_texts(output: dict[str, Any]) -> list[str]:
    return [str(row.get("text", "")) for row in output.get("claims", []) if isinstance(row, dict)]


def compare_outputs(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Return reproducible overlap metrics; agreement is not a truth grade."""
    left_tokens = _tokens(" ".join(_claim_texts(left)))
    right_tokens = _tokens(" ".join(_claim_texts(right)))
    union = left_tokens | right_tokens
    return {
        "left_lane": left.get("lane", "unknown"),
        "right_lane": right.get("lane", "unknown"),
        "claim_count_delta": abs(len(_claim_texts(left)) - len(_claim_texts(right))),
        "token_jaccard": round(len(left_tokens & right_tokens) / len(union), 6) if union else 1.0,
        "interpretation": "process_output_similarity_only",
    }
