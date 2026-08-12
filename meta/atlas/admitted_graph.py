from __future__ import annotations

from typing import Any


ADMITTED = {"admitted", "accepted", "ratified", "canonical"}


def project_admitted(candidate: dict[str, Any]) -> dict[str, Any]:
    nodes = [row for row in candidate.get("nodes", []) if str(row.get("standing", "")).lower() in ADMITTED]
    ids = {row.get("id") for row in nodes}
    edges = [row for row in candidate.get("edges", [])
             if row.get("source") in ids and row.get("target") in ids
             and str(row.get("standing", "")).lower() in ADMITTED]
    return {"state": "Admitted", "nodes": nodes, "edges": edges}
