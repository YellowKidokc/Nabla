#!/usr/bin/env python3
"""One DeepSeek call that produces a validation-gated Candidate AtlasRecord."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[0]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(REPO))

from claim_ledger import record_method_run
from method_core import call_api, extract_json, now, read_json, sha256_bytes, stable_id, write_json
from meta.rails.atlas_api_rails import validate

PROFILE = ROOT / "config" / "atlas-full-intake-profile.v1.json"
RUNTIME = ROOT / "config" / "runtime.json"
SCHEMA = REPO / "meta" / "schemas" / "atlas_record.schema.json"


def packet(source: Path) -> dict[str, Any]:
    raw = source.read_bytes()
    return {"packet_id": f"atlas-intake:{sha256_bytes(raw)[:16]}", "source": str(source),
            "sha256": sha256_bytes(raw), "text": raw.decode("utf-8", errors="replace"), "created_at": now()}


def prompt(source_packet: dict[str, Any], profile: dict[str, Any]) -> str:
    return f'''Analyze the immutable source packet as one Consilience Atlas Candidate intake. Return one JSON object only.
Required blocks: {json.dumps(profile["required_blocks"])}.
Rules: {json.dumps(profile["rules"])}.
Use this exact shape:
{{"title":"string","nabla":{{"classification":"string","routing_hints":["string"]}},"periodic15":{{"scope":"string","home_domain":"string","native_domains":["string"],"object_type":"string","claim_family":"string","function_kind":"string","source_kind":"string","standing":"Candidate","dispute":"string"}},"atom_stack":{{"claims":[{{"text":"string","mode":"string","domain":"string","source_quote":"exact quote","kill_condition":"string"}}],"dependencies":[{{"from_claim_text":"string","to_claim_text":"string","relation":"string","basis":"string"}}],"evidence":[{{"claim_text":"string","source_quote":"exact quote","relation":"source_asserts"}}]}},"lanes":{{"human":"not_run|receipt summary","python":"not_run|receipt summary","api":"complete|receipt summary","independent_nlp":"not_run|receipt summary"}},"dynamics7":{{"coherence":"string","degradation":"string","measure":"string","threshold":"string","asymmetry":"string","restoration_self":"string","restoration_external":"string","counterexample":"string"}},"atd":{{"ascent":"string","translation":{{"preserved":["string"],"lost":["string"],"introduced":["string"],"forbidden":["string"]}},"descent":"string","meeting_state":"UNRESOLVED"}},"bridges":[{{"target_domain":"string","mapping_type":"partial|analogy|none|isomorphism_candidate","preserved":["string"],"lost":["string"],"introduced":["string"],"forbidden":["string"]}}],"resonance_phi":{{"resonance_candidates":["string"],"phi_status":"not_run|candidate|rejected","notes":"string"}},"reality_mirror":{{"class":"N|F|H|T|None","status":"Candidate|Unresolved","rule":"string","anchors":["string"]}},"unresolved":["string"]}}
The `orientation` block is required even when empty. It has four typed objects:
`ascent` with `nodes`, `edges`, and `terminal_candidates`; `descent` with
`nodes`, `edges`, and `test_targets`; `translation` with `mappings`; and
`meeting` with `comparisons` and one of CONVERGED, PRESSURE,
PREDICTED_NOT_OBSERVED, UNRESOLVED, or CONTRADICTED. Each translation mapping
uses ascent_object, descent_object, preserved, lost, introduced, forbidden,
direction, status, confidence, and declared_by. Never treat a translation as an
admitted bridge merely because the two paths appear to meet.
Packet id: {source_packet["packet_id"]}; source SHA-256: {source_packet["sha256"]}
--- SOURCE ---
{source_packet["text"]}
--- END SOURCE ---'''


def build_record(source_packet: dict[str, Any], result: dict[str, Any], model: str) -> dict[str, Any]:
    claims = result.get("atom_stack", {}).get("claims", [])[:24]
    claim_rows, components, tests, evidence = [], [], [], []
    ids: dict[str, str] = {}
    for index, item in enumerate(claims, 1):
        text = str(item.get("text", "")).strip()
        if not text: continue
        cid = stable_id("claim", text); ids[text] = cid
        span = f"source-span:claim:{index:02d}"
        claim_rows.append({"claim_id": cid, "text": text, "mode": str(item.get("mode", "UNKNOWN")), "mode_native": str(item.get("mode", "UNKNOWN")), "standing": "Candidate", "native_grade": "UNKNOWN", "source_span_ids": [span], "notes": "API candidate; no native grade inferred."})
        components.append({"component_id": f"{cid}.claim", "type": "claim", "label": "Claim", "content": text, "meta_criteria_ids": ["provenance", "evidence", "falsifiability"], "standing": "Candidate", "source_span_ids": [span]})
        tests.append({"test_id": f"{cid}.kill", "claim_id": cid, "type": "kill_condition", "condition": str(item.get("kill_condition", "Human review required.")), "status": "candidate_untested"})
    for index, item in enumerate(result.get("atom_stack", {}).get("evidence", []), 1):
        cid = ids.get(str(item.get("claim_text", "")), "")
        if cid:
            evidence.append({"evidence_id": f"evidence:{index:02d}", "claim_id": cid, "component_id": f"{cid}.claim", "relation": str(item.get("relation", "source_asserts")), "strength": "SOURCE_ASSERTION", "coverage": 0.0, "statement": str(item.get("source_quote", "")), "source": source_packet["source"]})
    edges = [{"edge_id": stable_id("edge", json.dumps(item, sort_keys=True)), "from": ids.get(str(item.get("from_claim_text", "")), ""), "relation": str(item.get("relation", "depends_on_candidate")), "to": ids.get(str(item.get("to_claim_text", "")), ""), "status": "Candidate", "source": "api"} for item in result.get("atom_stack", {}).get("dependencies", [])]
    edges = [row for row in edges if row["from"] and row["to"]]
    periodic = result.get("periodic15", {})
    orientation = result.get("orientation", {
        "ascent": {"nodes": [], "edges": [], "terminal_candidates": []},
        "translation": {"mappings": []},
        "descent": {"nodes": [], "edges": [], "test_targets": []},
        "meeting": {"comparisons": [], "state": "UNRESOLVED"},
    })
    return {"schema_version":"atlas-record/v1", "id":{"record_id":stable_id("atlas-record", source_packet["sha256"]),"atom_id":stable_id("atom", source_packet["sha256"]),"source_claim_id":"","stable_uid":source_packet["sha256"],"aliases":[]}, "source":{"kind":"frozen_document","title":str(result.get("title") or Path(source_packet["source"]).stem),"content_hash":"sha256:"+source_packet["sha256"],"paths":[source_packet["source"]],"source_spans":[],"provenance":[{"timestamp":source_packet["created_at"],"event_type":"deepseek_full_atlas_intake","result":"candidate","limits":"API output is not proof","reviewer":model}]}, "nabla":{"classification":str(result.get("nabla",{}).get("classification","candidate document")),"semantic_address":f"nabla://candidate/{source_packet['sha256'][:16]}","routing_hints":result.get("nabla",{}).get("routing_hints",[]),"deterministic_status":"candidate"}, "periodic15":{"marker_1_scope":str(periodic.get("scope","paper/local")),"marker_2_home_domain":str(periodic.get("home_domain","unknown")),"marker_3_native_domains":periodic.get("native_domains",["unknown"]),"marker_4_bridged_domains":[],"marker_5_object_type":str(periodic.get("object_type","Document")),"marker_6_claim_family":str(periodic.get("claim_family","UNKNOWN")),"marker_7_function_kind":str(periodic.get("function_kind","Analysis")),"marker_8_source_kind":str(periodic.get("source_kind","frozen_document")),"marker_9_standing":"Candidate","marker_10_native_grade":"UNKNOWN","marker_11_modality":"UNKNOWN","marker_12_evidence_grade":"UNKNOWN","marker_13_dispute":str(periodic.get("dispute","unreviewed")),"marker_14_publication_state":"candidate_api_intake","marker_15_component_state":"claims,evidence,tests,dynamics"}, "atom_stack":{"atom":{"atom_id":stable_id("atom", source_packet["sha256"]),"title":str(result.get("title","Candidate intake")),"object_type":str(periodic.get("object_type","Document")),"standing":"Candidate","native_grade":"UNKNOWN"},"components":components,"claims":claim_rows,"upstream":[],"downstream":[],"dependencies":[],"arguments":[],"warrant":{"evidence_receipt_ids":[x["evidence_id"] for x in evidence],"proof_test_ids":[],"counterevidence_ids":[],"kill_condition_ids":[x["test_id"] for x in tests]},"tests":tests,"dynamics":{"ascent":result.get("atd",{}).get("ascent",""),"translation":result.get("atd",{}).get("translation",{}),"descent":result.get("atd",{}).get("descent",""),"meeting_state":result.get("atd",{}).get("meeting_state","UNRESOLVED")}}, "evidence_receipts":evidence,"edges":edges,"bridges":[{"bridge_id":stable_id("bridge",json.dumps(x,sort_keys=True)),"target":str(x.get("target_domain","unknown")),"mapping_type":str(x.get("mapping_type","none")),"standing":"Candidate","forbidden":"Only preserved structure may carry an argument."} for x in result.get("bridges",[])],"anchors":[],"reality_mirror":{"class":str(result.get("reality_mirror",{}).get("class","None")),"status":"Candidate" if result.get("reality_mirror",{}).get("status") == "Candidate" else "Unresolved","rule":str(result.get("reality_mirror",{}).get("rule","No external anchor inferred.")),"anchor_ids":[]},"meta_argument":{"status":"not_run","engine":"not_run","input_profile":"full_atlas_intake","variables":{},"refusal_states":["INSUFFICIENTLY_DEFINED"],"veto":"UNKNOWN","confidence":"UNKNOWN","dependencies":[]},"computed":{"graph_signature":{"claim_count":len(claim_rows),"edge_count":len(edges),"evidence_count":len(evidence)},"api_model":model},"audit":{"candidate_or_admitted":"Candidate","subsystem_receipts":[{"system":"DeepSeek Full Atlas Intake","status":"complete","owned_fields":["candidate classification"],"notes":"Not an admission or Lean receipt."}]},"unresolved":list(result.get("unresolved",[]))}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one DeepSeek Full Atlas Intake and write a Candidate AtlasRecord.")
    parser.add_argument("--source", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--receipt", type=Path, required=True); parser.add_argument("--raw-output", type=Path); parser.add_argument("--profile", type=Path, default=PROFILE); parser.add_argument("--runtime", type=Path, default=RUNTIME); parser.add_argument("--provider", choices=["deepseek"], default="deepseek")
    args = parser.parse_args(); source = args.source.resolve()
    if not source.is_file(): raise SystemExit(f"source not found: {source}")
    profile, runtime, source_packet = read_json(args.profile), read_json(args.runtime), packet(source)
    runtime["api"] = dict(runtime["api"]); runtime["api"]["max_tokens_per_stage"] = int(profile["max_output_tokens"])
    raw, model = call_api(args.provider, prompt(source_packet, profile), runtime)
    if args.raw_output: args.raw_output.write_text(raw, encoding="utf-8")
    result = extract_json(raw); record = build_record(source_packet, result, model)
    record["orientation"] = result.get("orientation", {
        "ascent": {"nodes": [], "edges": [], "terminal_candidates": []},
        "translation": {"mappings": []},
        "descent": {"nodes": [], "edges": [], "test_targets": []},
        "meeting": {"comparisons": [], "state": "UNRESOLVED"},
    })
    for mapping in record["orientation"].get("translation", {}).get("mappings", []):
        mapping["direction"] = str(mapping.get("direction", "A_TO_D")).upper()
        mapping["status"] = str(mapping.get("status", "Candidate")).title()
        try:
            mapping["confidence"] = float(mapping["confidence"])
        except (KeyError, TypeError, ValueError):
            mapping.pop("confidence", None)
    # The shared schema owns these computed/audit fields; API metadata belongs in receipts.
    record["computed"] = {
        "graph_signature": record["computed"]["graph_signature"],
        "grade_projection": {"native_grade": "UNKNOWN", "normalized_grade": "UNKNOWN", "status": "not_computed"},
        "load_bearing": "UNKNOWN",
        "blast_radius": [],
    }
    record["audit"].setdefault("warnings", ["API intake is Candidate-only; no admission, native grade, or external anchor is inferred."])
    for subsystem in record["audit"].get("subsystem_receipts", []):
        if subsystem.get("status") == "complete":
            subsystem["status"] = "filled"
    record["unresolved"] = [
        item if isinstance(item, dict) else {
            "field_or_requirement": "api_reported_open_item",
            "reason": str(item),
            "next_step": "Attach a human, formal, empirical, or independent-lane receipt.",
        }
        for item in record.get("unresolved", [])
    ]
    errors = validate(record, SCHEMA)
    receipt = {"schema_version":"atlas-full-intake-receipt/v1","created_at":now(),"provider":args.provider,"model":model,"packet":source_packet,"status":"complete" if not errors else "refused","validation_errors":errors,"result":result}
    write_json(args.receipt, receipt)
    if errors: print(json.dumps(receipt, indent=2)); return 2
    write_json(args.output, record)
    synthetic = {"run_id":stable_id("api-full-intake",source_packet["sha256"]),"created_at":now(),"provider":args.provider,"backend":model,"packet_id":source_packet["packet_id"],"source_sha256":source_packet["sha256"],"status":"complete","stages":[{"stage_id":"01_claims","data":{"claims":[{"claim_id":c["claim_id"],"text":c["text"],"source_quote":"","extraction_status":"candidate"} for c in record["atom_stack"]["claims"]]}},{"stage_id":"04_falsification","data":{"tests":record["atom_stack"]["tests"]}},{"stage_id":"05_evidence","data":{"source_support":[{"claim_id":e["claim_id"],"source_quote":e["statement"],"relation":e["relation"]} for e in record["evidence_receipts"]],"evidence_requirements":[]}}]}
    ledger = record_method_run(synthetic); print(json.dumps({"status":"candidate_record_written","record":str(args.output),"receipt":str(args.receipt),"ledger":ledger},indent=2)); return 0

if __name__ == "__main__": raise SystemExit(main())
