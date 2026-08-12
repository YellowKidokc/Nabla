from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "method_comparison" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from method_core import build_packet, compare_runs, read_json, run_lane
from run_foundation_synthesis import build_foundation_packet, validate_result
from claim_ledger import record_method_run
from run_atlas_full_intake import build_record, packet, prompt
from natural_process_walk import evaluate_walk, make_walk
from meta.rails.atlas_api_rails import validate


class MethodComparisonTests(unittest.TestCase):
    def test_identical_process_runs_compare_exactly(self) -> None:
        contract = read_json(ROOT / "method_comparison" / "config" / "process-contract.v1.json")
        runtime = read_json(ROOT / "method_comparison" / "config" / "runtime.json")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "specimen.md"
            source.write_text(
                "A system requires evidence. If its prediction fails, its claim "
                "must be revised. Grace is a theological interpretation.",
                encoding="utf-8",
            )
            packet = build_packet(source, contract)
            left, _ = run_lane(packet, contract, runtime, "local_nlp")
            right, _ = run_lane(packet, contract, runtime, "local_nlp")
            self.assertEqual(left["status"], "complete")
            self.assertEqual(len(left["stages"]), 9)
            report = compare_runs(left, right, contract, runtime)
            self.assertEqual(report["overall_agreement"], 1.0)
            self.assertEqual(report["agreement_band"], "HIGH_PROCESS_AGREEMENT")

    def test_foundation_packet_preserves_distinct_sources(self) -> None:
        profile = read_json(ROOT / "method_comparison" / "config" / "foundation-synthesis-profile.v1.json")
        with tempfile.TemporaryDirectory() as tmp:
            left = Path(tmp) / "axioms.md"
            right = Path(tmp) / "equation.md"
            left.write_text("Axiom source.", encoding="utf-8")
            right.write_text("Equation source.", encoding="utf-8")
            packet = build_foundation_packet([("axioms", left), ("equation", right)], profile)
            self.assertEqual(len(packet["sources"]), 2)
            self.assertIn("BEGIN SOURCE axioms", packet["material"])
            self.assertIn("BEGIN SOURCE equation", packet["material"])
            result = {key: [] if isinstance(value, list) else {} if isinstance(value, dict) else "" for key, value in profile["output_contract"].items()}
            result["foundation_summary"] = "Candidate-only summary."
            result["lens_assessments"] = [{"lens": "axiom_spine", "source_refs": [{"source_id": "axioms", "source_quote": "Axiom source."}]}]
            self.assertEqual(validate_result(result, profile, {"axioms", "equation"}), [])

    def test_api_receipt_rows_are_persisted_to_sqlite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run = {
                "run_id": "api:test", "created_at": "2026-08-12T00:00:00Z", "provider": "deepseek",
                "backend": "deepseek:test", "packet_id": "packet:test", "source_sha256": "abc", "status": "complete",
                "stages": [
                    {"stage_id": "01_claims", "data": {"claims": [{"claim_id": "C1", "text": "Claim", "source_quote": "Quote", "extraction_status": "candidate"}]}},
                    {"stage_id": "02_classification", "data": {"claim_assessments": [{"claim_id": "C1", "mode": "AXIOM", "domain": "logic", "standing": "active_candidate"}]}},
                    {"stage_id": "04_falsification", "data": {"tests": [{"claim_id": "C1", "condition": "Counterexample", "status": "candidate_untested"}]}},
                    {"stage_id": "05_evidence", "data": {"source_support": [{"claim_id": "C1", "source_quote": "Quote", "relation": "source_asserts"}], "evidence_requirements": [{"claim_id": "C1", "required": ["independent source"]}]}},
                ],
            }
            receipt = record_method_run(run, Path(tmp) / "ledger.sqlite")
            self.assertEqual(receipt["claims"], 1)
            self.assertEqual(receipt["evidence"], 2)
            self.assertEqual(receipt["tests"], 1)

    def test_full_intake_builds_candidate_record_with_architecture_contract(self) -> None:
        profile = read_json(ROOT / "method_comparison" / "config" / "atlas-full-intake-profile.v1.json")
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "specimen.md"
            source.write_text("A source claim requires a receipt.", encoding="utf-8")
            frozen = packet(source)
            result = {
                "title": "Specimen", "nabla": {"classification": "candidate", "routing_hints": []},
                "periodic15": {"native_domains": ["logic"]},
                "atom_stack": {"claims": [{"text": "A source claim requires a receipt.", "mode": "AXIOM", "domain": "logic", "source_quote": "A source claim requires a receipt.", "kill_condition": "A counterexample."}], "dependencies": [], "evidence": []},
                "lanes": {"human": "not_run", "python": "not_run", "api": "complete", "independent_nlp": "not_run"},
                "dynamics7": {}, "atd": {"translation": {}}, "bridges": [], "resonance_phi": {"phi_status": "not_run"},
                "reality_mirror": {"class": "None", "status": "Unresolved", "rule": "None", "anchors": []}, "unresolved": [],
            }
            record = build_record(frozen, result, "deepseek-test")
            self.assertEqual(record["audit"]["candidate_or_admitted"], "Candidate")
            self.assertEqual(validate(record), [])
            self.assertIn("lanes", prompt(frozen, profile))
            self.assertIn("resonance_phi", prompt(frozen, profile))

    def test_natural_process_walk_requires_complete_mapping_and_control(self) -> None:
        walk = make_walk("source sequence", ["first", "second"])
        self.assertEqual(evaluate_walk(walk)["mirror_gate_status"], "NEEDS_NATURAL_ANCHOR")
        walk["natural_process"] = "endogenous process"
        walk["external_anchors"] = ["external observation"]
        walk["negative_controls"] = ["rival process"]
        for index, row in enumerate(walk["stage_map"], 1):
            row.update({"natural_stage": f"stage {index}", "same_order": True, "same_direction": True, "same_function": True})
        self.assertEqual(evaluate_walk(walk)["mirror_gate_status"], "PASSED_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
