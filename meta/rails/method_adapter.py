"""Adapt a frozen method-lane run into the canonical AtlasRecord v1 contract.

The adapter is intentionally conservative: lane proposals stay Candidate, native
grades and Periodic values remain UNKNOWN, and missing ontology-owned material is
reported in ``unresolved`` rather than inferred.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _id(prefix: str, value: str) -> str:
    return f"{prefix}:{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def _stages(run: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["stage_id"]: row.get("data", {}) for row in run.get("stages", [])}


def _locate(text: str, quote: str, span_id: str, path: str) -> dict[str, str]:
    start = text.find(quote)
    if start < 0:
        return {"span_id": span_id, "path": path, "selector": "unresolved", "quote": quote}
    return {
        "span_id": span_id,
        "path": path,
        "selector": f"char={start},{start + len(quote)}",
        "quote": quote,
    }


def adapt_method_run(packet: dict[str, Any], run: dict[str, Any]) -> dict[str, Any]:
    """Return an AtlasRecord for one frozen packet and one independent lane run."""
    source = packet["source"]
    text, path = source["text"], source["path"]
    stages = _stages(run)
    claim_rows = stages.get("01_claims", {}).get("claims", [])
    assessments = {
        row.get("claim_id"): row
        for row in stages.get("02_classification", {}).get("claim_assessments", [])
    }

    spans, claims, components = [{"span_id": "source-span:document", "path": path,
                                  "selector": f"char=0,{len(text)}"}], [], []
    claim_span: dict[str, str] = {}
    for index, row in enumerate(claim_rows, 1):
        claim_id = row.get("claim_id") or _id("claim", row.get("text", ""))
        quote = str(row.get("source_quote") or row.get("text") or "")
        span_id = f"source-span:claim:{index:03d}"
        spans.append(_locate(text, quote, span_id, path))
        claim_span[claim_id] = span_id
        assessment = assessments.get(claim_id, {})
        claims.append({
            "claim_id": claim_id,
            "text": str(row.get("text", quote)),
            "mode": str(assessment.get("mode", "UNKNOWN")),
            "mode_native": str(assessment.get("mode", "UNKNOWN")),
            "standing": "Candidate",
            "native_grade": "UNKNOWN",
            "source_span_ids": [span_id],
            "notes": "Lane extraction proposal; no admission or native grade inferred.",
        })
        components.append({
            "component_id": f"component:{claim_id}", "type": "claim", "label": f"Claim {index}",
            "content": row.get("text", quote), "meta_criteria_ids": [], "standing": "Candidate",
            "source_span_ids": [span_id],
        })

    dependencies, edges = [], []
    for index, row in enumerate(stages.get("03_dependencies", {}).get("dependencies", []), 1):
        target = str(row.get("to", "")); origin = str(row.get("from", ""))
        dependencies.append(target)
        edges.append({
            "edge_id": _id("edge", f"{origin}:{target}:{index}"), "from": origin,
            "relation": str(row.get("relation", "depends_on_candidate")), "to": target,
            "status": "Candidate", "source": run.get("run_id", ""),
            "source_span_ids": [claim_span[origin]] if origin in claim_span else [],
        })

    tests = []
    for index, row in enumerate(stages.get("04_falsification", {}).get("tests", []), 1):
        cid = str(row.get("claim_id", ""))
        tests.append({
            "test_id": _id("test", f"{cid}:{index}:{row.get('condition', '')}"), "claim_id": cid,
            "type": str(row.get("type", "defeat_condition")), "condition": str(row.get("condition", "")),
            "status": str(row.get("status", "candidate_untested")),
            "source_span_ids": [claim_span[cid]] if cid in claim_span else [],
        })

    evidence = []
    for index, row in enumerate(stages.get("05_evidence", {}).get("source_support", []), 1):
        cid = str(row.get("claim_id", "")); quote = str(row.get("source_quote", ""))
        evidence.append({
            "evidence_id": _id("evidence", f"{cid}:{index}:{quote}"), "claim_id": cid,
            "component_id": f"component:{cid}", "relation": str(row.get("relation", "source_asserts")),
            "strength": "SOURCE_ASSERTION_ONLY", "coverage": 0.0, "statement": quote,
            "source": path, "does_not_show": ["independent corroboration"],
            "source_span_ids": [claim_span[cid]] if cid in claim_span else [],
        })

    dynamics = stages.get("07_dynamics", {})
    synthesis = stages.get("08_synthesis", {})
    title = Path(source["filename"]).stem
    primary = claims[0]["claim_id"] if claims else ""
    unresolved = [{
        "field_or_requirement": "Periodic 15 ontology fields and grades",
        "reason": "The semantic lane does not own Periodic classification, evidence grades, or native grades.",
        "next_step": "Run the existing ontology-owned review and grading subsystems.",
    }]
    unresolved.extend([
        {"field_or_requirement": "bridges and anchors", "reason": "The shared semantic lane does not emit canonical bridge or anchor objects.",
         "next_step": "Run bridge and Reality Mirror review without promoting the Candidate record."},
        {"field_or_requirement": "Ascent / Translation / Descent", "reason": "No explicit projection was present in the lane contract.",
         "next_step": "Attach an existing projection receipt or leave UNRESOLVED."},
    ])
    for value in synthesis.get("unresolved", []):
        unresolved.append({"field_or_requirement": str(value), "reason": "Lane reported unresolved", "next_step": "Human review"})
    for stage in run.get("stages", []):
        for refusal in stage.get("refusals", []):
            unresolved.append({"field_or_requirement": stage["stage_id"], "reason": str(refusal), "next_step": "Review provider refusal"})

    # Periodic-15 contract per Canonical Architecture v0.3 section 9.
    # The semantic lane does not own Periodic classification, so every
    # classified marker stays UNKNOWN and computed markers stay null (None);
    # only identity is known at adaptation time. Keys match
    # templates/atlas-workbench.html.
    periodic = {f"m{i:02d}_{name}": ([] if i in (3, 4) else "UNKNOWN") for i, name in enumerate((
        "identity", "home_domain", "native_domains", "bridged_domains", "object_type", "claim_family",
        "function_kind", "source", "commitment", "standing", "dispute", "evidence_grade",
        "usage_runs", "graph_degree", "alert_state"), 1)}
    periodic["m01_identity"] = _id("atom", source["sha256"])
    for computed_marker in ("m12_evidence_grade", "m13_usage_runs", "m14_graph_degree"):
        periodic[computed_marker] = None
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return {
        "schema_version": "atlas-record/v1",
        "id": {"record_id": _id("atlas-record", source["sha256"]), "atom_id": _id("atom", source["sha256"]),
               "source_claim_id": primary, "stable_uid": source["sha256"], "aliases": []},
        "source": {"kind": Path(source["filename"]).suffix.lstrip(".") or "text", "title": title,
                   "content_hash": f"sha256:{source['sha256']}", "paths": [path], "source_spans": spans,
                   "provenance": [{"timestamp": now, "event_type": "semantic_lane_adapter",
                                   "result": "Candidate AtlasRecord generated", "limits": "No admission, grades, or Periodic fields inferred."}]},
        "nabla": {"classification": "semantic_lane_candidate", "semantic_address": str(dynamics.get("semantic_vector", {})),
                  "routing_hints": [], "deterministic_status": "candidate",
                  "notes": f"backend={run.get('backend', 'UNKNOWN')}; veto={dynamics.get('veto_status', 'NOT_ADJUDICATED')}"},
        "periodic15": periodic,
        "epistemic": {
            "class": "undeclared",
            "scope_class": {"level": "undeclared", "label": "UNDECLARED"},
            "derivation_status": "UNDECLARED",
            "external_independence": "undeclared",
            "proposition": claims[0]["text"] if claims else title,
        },
        "atom_stack": {"atom": {"atom_id": _id("atom", source["sha256"]), "title": title,
                                  "object_type": "UNKNOWN", "standing": "Candidate", "native_grade": "UNKNOWN"},
                       "components": components, "claims": claims, "upstream": [], "downstream": [],
                       "dependencies": list(dict.fromkeys(dependencies)), "arguments": [],
                       "warrant": {"evidence_receipt_ids": [x["evidence_id"] for x in evidence],
                                   "proof_test_ids": [x["test_id"] for x in tests], "counterevidence_ids": [],
                                   "kill_condition_ids": [x["test_id"] for x in tests]},
                       "tests": tests, "dynamics": {"ascent": {"status": "UNRESOLVED"},
                                                     "translation": {"status": "UNRESOLVED"},
                                                     "descent": {"status": "UNRESOLVED"},
                                                     "meeting_state": "UNRESOLVED",
                                                     "dg7": {key: {"status": "not_run"} for key in (
                                                         "coherence", "degradation", "measurement", "threshold",
                                                         "transition_asymmetry", "restoration_self",
                                                         "restoration_external", "counterexample")},
                                                     "source_span_ids": ["source-span:document"]}},
        "evidence_receipts": evidence, "edges": edges, "bridges": [], "anchors": [],
        "reality_mirror": {"class": "None", "status": "Unresolved", "rule": "No external anchor inferred by semantic extraction.", "anchor_ids": []},
        "reference_interface": {"status": "not_run",
                                "note": "Gamma (Reference Interface) review not run by the semantic lane. Reference failure is not interface failure."},
        "ascent_interface": {"status": "candidate", "method": f"semantic_lane:{run.get('backend', 'UNKNOWN')}",
                             "provenance": [],
                             "note": "Cold reconstruction record. Ascent may not assume it reaches the Descent reference."},
        "meta_argument": {"status": "not_run", "engine": "", "input_profile": "", "variables": {},
                          "refusal_states": [], "veto": "NOT_ADJUDICATED", "confidence": "UNKNOWN", "dependencies": []},
        "computed": {"graph_signature": {"node_count": len(claims), "edge_count": len(edges)},
                     "grade_projection": "UNKNOWN", "load_bearing": stages.get("03_dependencies", {}).get("load_bearing_claim_ids", []),
                     "blast_radius": []},
        "audit": {"candidate_or_admitted": "Candidate", "subsystem_receipts": [{
            "system": str(run.get("backend", "semantic_lane")), "status": "filled" if run.get("status") == "complete" else "partially_filled",
            "owned_fields": ["atom_stack", "evidence_receipts", "edges", "nabla"],
            "notes": "Adapter preserves Candidate state; Φ admission and canon promotion were not run."}], "warnings": [],
            "open": unresolved},
        "unresolved": unresolved,
    }
