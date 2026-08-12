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
from meta.atlas.projections import blast_radius, view_memberships


class MetaPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = build_record(DEFAULT_ATOM)

    def test_master_equation_builds_valid_record(self) -> None:
        self.assertEqual(validate_record(self.record), [])
        self.assertEqual(self.record["schema_version"], "atlas-record/v1")
        self.assertTrue(self.record["source"]["content_hash"].startswith("sha256:"))

    def test_native_grade_and_meta_score_are_separate(self) -> None:
        self.assertEqual(self.record["periodic15"]["marker_10_native_grade"], "NOT_ESTABLISHED")
        self.assertEqual(self.record["periodic15"]["marker_12_evidence_grade"], "UNKNOWN")
        self.assertNotEqual(self.record["computed"].get("meta_scores"), "UNKNOWN")

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

    def test_views_are_deterministic_projections_of_canonical_edges(self) -> None:
        record = {"edges": [
            {"edge_id": "dep", "from": "CLM-2", "to": "CLM-1", "relation": "depends_on"},
            {"edge_id": "proof", "from": "EVD-1", "to": "CLM-1", "relation": "supports"},
        ], "evidence_receipts": [], "anchors": []}
        projections = view_memberships(record)
        self.assertEqual(projections["dependency"]["edge_ids"], ["dep"])
        self.assertEqual(projections["proof"]["edge_ids"], ["proof"])
        self.assertEqual(blast_radius(record, "CLM-1")["affected_object_ids"], ["CLM-2"])


if __name__ == "__main__":
    unittest.main()
