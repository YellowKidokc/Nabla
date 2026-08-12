from __future__ import annotations

from typing import Any


def ascent(records: list[dict[str, Any]], aggregate_id: str) -> dict[str, Any]:
    return {"aggregate_id": aggregate_id, "level": "paper", "atom_record_ids":
            [row.get("id", {}).get("record_id") for row in records], "reinterpreted": False}


def descent(aggregate: dict[str, Any]) -> list[str]:
    return list(aggregate.get("atom_record_ids", []))
