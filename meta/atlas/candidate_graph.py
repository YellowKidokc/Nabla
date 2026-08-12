from __future__ import annotations

from typing import Any


def build_candidate_graph(record: dict[str, Any]) -> dict[str, Any]:
    atom_id = record.get("id", {}).get("atom_id", "UNKNOWN")
    nodes = [{"id": atom_id, "kind": "atom", "standing": "Candidate"}]
    nodes.extend({"id": row.get("component_id"), "kind": row.get("type"),
                  "standing": row.get("standing", "candidate")}
                 for row in record.get("atom_stack", {}).get("components", []))
    return {"state": "Candidate", "nodes": nodes, "edges": list(record.get("edges", []))}
