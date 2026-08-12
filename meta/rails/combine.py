from __future__ import annotations

from typing import Any


def combine(base: dict[str, Any], lane_outputs: list[dict[str, Any]]) -> dict[str, Any]:
    """Attach independent lane receipts without allowing lanes to overwrite native fields."""
    record = dict(base)
    audit = dict(record.get("audit", {}))
    receipts = list(audit.get("subsystem_receipts", []))
    for lane in lane_outputs:
        receipts.append({"system": lane.get("lane", "unknown"), "status": lane.get("status", "candidate"),
                         "owned_fields": lane.get("owned_fields", []),
                         "notes": lane.get("notes", "Independent lane output attached; no native promotion.")})
    audit["subsystem_receipts"] = receipts
    record["audit"] = audit
    return record
