from __future__ import annotations

from typing import Any


REQUIRED_BLOCKS = (
    "schema_version", "id", "source", "nabla", "periodic15", "epistemic",
    "atom_stack", "evidence_receipts", "edges", "bridges", "anchors",
    "reality_mirror", "reference_interface", "ascent_interface",
    "meta_argument", "computed", "audit", "unresolved",
)


def validate_record(record: dict[str, Any]) -> list[str]:
    errors = [f"missing required block: {key}" for key in REQUIRED_BLOCKS if key not in record]
    if record.get("schema_version") != "atlas-record/v1":
        errors.append("schema_version must be atlas-record/v1")
    if "reality_mirror" in record.get("periodic15", {}):
        errors.append("reality_mirror is top-level, not periodic marker 16")
    state = record.get("audit", {}).get("candidate_or_admitted")
    if state not in {"Candidate", "Admitted", "Blocked", "Unknown"}:
        errors.append("audit.candidate_or_admitted has an invalid state")
    return errors
