"""Deterministic Atlas view memberships derived from one canonical record."""
from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


VIEW_RELATIONS = {
    "dependency": {"dependsOn", "depends_on", "derives_from"},
    "proof": {"supports", "establishes", "partially_supports", "derives_from"},
    "dispute": {"contradicts", "contradicted_by", "qualifies"},
    "bridge": {"bridgesTo", "bridges_to"},
    "reality_mirror": {"anchors", "external_support"},
    "evolution": {"resolves", "resolved_by", "supersedes", "qualifies"},
}


def view_memberships(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Select canonical edges and objects; never reclassify them for a view."""
    edges = list(record.get("edges", []))
    result: dict[str, dict[str, Any]] = {}
    for view, relations in VIEW_RELATIONS.items():
        selected = [edge for edge in edges if edge.get("relation") in relations]
        object_ids = sorted({edge.get("from", "") for edge in selected} | {edge.get("to", "") for edge in selected} - {""})
        result[view] = {"edge_ids": [edge.get("edge_id", "") for edge in selected], "object_ids": object_ids}
    result["evidence_landscape"] = {
        "evidence_ids": [row.get("evidence_id", "") for row in record.get("evidence_receipts", [])],
        "anchor_ids": [row.get("anchor_id", "") for row in record.get("anchors", [])],
    }
    return result


def blast_radius(record: dict[str, Any], origin_id: str) -> dict[str, Any]:
    """Compute dependent descendants from canonical dependency edges only."""
    relations = VIEW_RELATIONS["dependency"]
    reverse: dict[str, list[str]] = defaultdict(list)
    for edge in record.get("edges", []):
        if edge.get("relation") in relations:
            reverse[str(edge.get("to", ""))].append(str(edge.get("from", "")))
    seen, queue = {origin_id}, deque([origin_id])
    while queue:
        current = queue.popleft()
        for child in reverse.get(current, []):
            if child and child not in seen:
                seen.add(child); queue.append(child)
    return {"origin_id": origin_id, "affected_object_ids": sorted(seen - {origin_id}), "count": len(seen) - 1}
