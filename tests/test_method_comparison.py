from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "method_comparison" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from method_core import build_packet, compare_runs, read_json, run_lane


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
            self.assertEqual(len(left["stages"]), 8)
            report = compare_runs(left, right, contract, runtime)
            self.assertEqual(report["overall_agreement"], 1.0)
            self.assertEqual(report["agreement_band"], "HIGH_PROCESS_AGREEMENT")


if __name__ == "__main__":
    unittest.main()
