from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "nabla"))

import dynamics_probe
import master_equation_types as met
import semantic_proposer

SPECIMEN = """
Coherence is measured over nine normalized factors. The equation is a product,
and a zero factor collapses the product. Information, relation, faith, time,
identity, mechanism, entropy, experience, authority, and Christ are discussed.
The system degrades under disorder. A threshold is proposed. An external source
restores motion when self-driven motion is stationary. A counterexample defeats
the claim.
"""


class NablaTests(unittest.TestCase):
    def test_semantic_and_equation_types_remain_separate(self) -> None:
        proposal = semantic_proposer.propose(SPECIMEN)
        self.assertEqual(
            list(proposal["semantic_vector"]),
            ["G", "M", "E", "S", "T", "K", "R", "Q", "F", "C"],
        )
        self.assertEqual(list(proposal["factor_mentions"]), met.CANONICAL_FACTORS)
        self.assertEqual(proposal["veto_status"], "NOT_ADJUDICATED")
        with self.assertRaises(met.CanonViolation):
            met.MasterEquationFactors.from_semantic_vector(proposal["semantic_vector"])

    def test_nine_factor_wrapper(self) -> None:
        values = {key: 1.0 for key in met.CANONICAL_FACTORS}
        factors = met.MasterEquationFactors.from_factor_values(values)
        self.assertEqual(met.MasterEquationState(factors).chi(), 1.0)
        with self.assertRaises(met.CanonViolation):
            met.forbid_ten_field_product({**values, "C": 1.0})

    def test_dg7_restoration_split(self) -> None:
        result = dynamics_probe.probe(SPECIMEN)
        self.assertIn("restoration_self", result["stored_fields"])
        self.assertIn("restoration_external", result["stored_fields"])


if __name__ == "__main__":
    unittest.main()
