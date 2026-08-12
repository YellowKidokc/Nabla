from __future__ import annotations

import json
import unittest
from pathlib import Path

from meta.store import AtlasStore

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLD = REPO_ROOT / "gold" / "master-equation" / "atlas-record-v1.master-equation.trilemma.json"


def load_gold() -> dict:
    return json.loads(GOLD.read_text(encoding="utf-8-sig"))


class AtlasStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = AtlasStore(":memory:")
        self.record = load_gold()
        self.record_id = self.record["id"]["record_id"]

    def tearDown(self) -> None:
        self.store.close()

    def test_round_trip_preserves_canonical_json(self) -> None:
        self.store.save_record(self.record, timestamp="2026-08-12T00:00:00Z")
        loaded = self.store.get_record(self.record_id)
        self.assertEqual(loaded, self.record)

    def test_native_and_evidence_grades_stored_separately(self) -> None:
        self.store.save_record(self.record, timestamp="t")
        row = self.store.conn.execute(
            "SELECT native_grade, evidence_grade FROM atlas_records WHERE record_id = ?",
            (self.record_id,),
        ).fetchone()
        self.assertEqual(row["native_grade"], self.record["periodic15"]["marker_10_native_grade"])
        self.assertEqual(row["evidence_grade"], self.record["periodic15"]["marker_12_evidence_grade"])

    def test_candidate_state_is_persisted_not_promoted(self) -> None:
        self.store.save_record(self.record, timestamp="t")
        summaries = self.store.list_records()
        self.assertEqual(len(summaries), 1)
        self.assertEqual(
            summaries[0]["candidate_or_admitted"],
            self.record["audit"]["candidate_or_admitted"],
        )

    def test_projection_rebuilds_on_resave(self) -> None:
        self.store.save_record(self.record, timestamp="t")
        first = self.store.conn.execute(
            "SELECT COUNT(*) AS n FROM claims WHERE record_id = ?", (self.record_id,)
        ).fetchone()["n"]
        # Re-saving must not duplicate projected children.
        self.store.save_record(self.record, timestamp="t2")
        second = self.store.conn.execute(
            "SELECT COUNT(*) AS n FROM claims WHERE record_id = ?", (self.record_id,)
        ).fetchone()["n"]
        self.assertEqual(first, second)

    def test_document_and_run_links(self) -> None:
        self.store.save_document(
            "doc-1", title="Master Equation", kind="html",
            content_hash="sha256:abc", r2_object_key="originals/doc-1.html",
            timestamp="t",
        )
        self.store.save_run("run-1", document_id="doc-1", provider="deepseek", status="ok", timestamp="t")
        self.store.save_record(self.record, document_id="doc-1", run_id="run-1", timestamp="t")
        summaries = self.store.list_records(document_id="doc-1")
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["document_id"], "doc-1")


if __name__ == "__main__":
    unittest.main()
