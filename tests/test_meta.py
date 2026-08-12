from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from meta.atlas.admitted_graph import project_admitted
from meta.atlas.atlas_record import validate_record
from meta.atlas.candidate_graph import build_candidate_graph
from meta.nlp.convergence import compare_outputs
from meta.nlp.rules_adapter import RulesAdapter
from meta.rails.ingest import DEFAULT_ATOM, build_record
from meta.rails.source_freeze import freeze
from meta.rails.method_adapter import adapt_method_run
from meta.rails.atlas_api_rails import validate
from method_comparison.scripts.method_core import build_packet, read_json, run_lane


class MetaPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_record(DEFAULT_ATOM)

    def test_master_equation_builds_valid_record(self) -> None:
        self.assertEqual(validate_record(self.record), [])
        self.assertEqual(self.record["schema_version"], "atlas-record/v1")
        self.assertTrue(self.record["source"]["content_hash"].startswith("sha256:"))

    def test_native_grade_and_meta_score_are_separate(self) -> None:
        self.assertEqual(self.record["periodic15"]["m10_standing"], "active_candidate")
        self.assertEqual(self.record["atom_stack"]["atom"]["native_grade"], "NOT_ESTABLISHED")
        self.assertIsNone(self.record["periodic15"]["m12_evidence_grade"])
        self.assertNotEqual(self.record["computed"].get("meta_scores"), "UNKNOWN")

    def test_computed_markers_are_null_until_computed(self) -> None:
        periodic = self.record["periodic15"]
        for marker in ("m12_evidence_grade", "m13_usage_runs", "m14_graph_degree"):
            self.assertIn(marker, periodic)
            self.assertIsNone(periodic[marker])

    def test_bridge_manifest_is_explicit(self) -> None:
        for bridge in self.record["bridges"]:
            self.assertIn("manifest", bridge)
            for key in ("preserved", "lost", "introduced", "forbidden"):
                self.assertIn(key, bridge["manifest"])
            self.assertIn(bridge["validation_state"],
                          {"Candidate", "Provisional", "Admitted", "Suspended", "Revoked", "Rejected"})
            self.assertIn(bridge["direction"], {"A_to_B", "B_to_A"})

    def test_epistemic_band_and_interfaces_present(self) -> None:
        self.assertIn("epistemic", self.record)
        self.assertIn("proposition", self.record["epistemic"])
        self.assertIn("reference_interface", self.record)
        self.assertIn("ascent_interface", self.record)
        dg7 = self.record["atom_stack"]["dynamics"]["dg7"]
        self.assertIn("restoration_self", dg7)
        self.assertIn("restoration_external", dg7)

    def test_reality_mirror_is_not_marker_16(self) -> None:
        self.assertIn("reality_mirror", self.record)
        self.assertNotIn("reality_mirror", self.record["periodic15"])

    def test_candidate_and_admitted_graphs_are_distinct(self) -> None:
        candidate = build_candidate_graph(self.record)
        admitted = project_admitted(candidate)
        self.assertEqual(candidate["state"], "Candidate")
        self.assertEqual(admitted["state"], "Admitted")
        self.assertLessEqual(len(admitted["nodes"]), len(candidate["nodes"]))

    def test_source_freeze_is_repeatable(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.md"
            source.write_text("A stable source packet.", encoding="utf-8")
            self.assertEqual(freeze(source)["source"]["sha256"], freeze(source)["source"]["sha256"])

    def test_rules_and_convergence_do_not_claim_truth(self) -> None:
        output = RulesAdapter().analyze("The equation implies a candidate conclusion. Evidence remains open.")
        comparison = compare_outputs(output, output)
        self.assertEqual(comparison["token_jaccard"], 1.0)
        self.assertEqual(comparison["interpretation"], "process_output_similarity_only")

    def test_gold_001_paper_lane_adapts_to_schema_valid_candidate(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract = read_json(root / "method_comparison/config/process-contract.v1.json")
        runtime = read_json(root / "method_comparison/config/runtime.json")
        source = root / "atom_package/master-equation/01_canonical/ME-01-001-trilemma-impossibility.html"
        packet = build_packet(source, contract)
        run, _ = run_lane(packet, contract, runtime, "local_nlp")
        record = adapt_method_run(packet, run)
        self.assertEqual(validate(record, root / "meta/schemas/atlas_record.schema.json"), [])
        self.assertEqual(record["audit"]["candidate_or_admitted"], "Candidate")
        self.assertEqual(record["periodic15"]["m10_standing"], "UNKNOWN")
        self.assertIsNone(record["periodic15"]["m12_evidence_grade"])
        self.assertEqual(record["periodic15"]["m01_identity"], record["id"]["atom_id"])
        self.assertTrue(record["atom_stack"]["claims"])
        self.assertTrue(all(claim["source_span_ids"] for claim in record["atom_stack"]["claims"]))


if __name__ == "__main__":
    unittest.main()
