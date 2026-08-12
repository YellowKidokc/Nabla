"""
master_equation_types.py - nabla-chi-classifier.station
Theophysics Research Initiative | POF 2828

WHY THIS FILE EXISTS
--------------------
Nabla's SemanticVector has ten dimensions (G M E S T K R Q F C). The canonical
Master Equation has NINE factors wrapped by C_W. Those are different objects
that happen to share letters. This module makes them different TYPES so the
collision cannot be made by accident.

  SemanticVector        G M E S T K R Q F C     <- filing address (nabla_engine)
  MasterEquationFactors XG..XF (nine)           <- canonical factors
  MasterEquationState   factors + wrapper       <- canonical chi

Nabla's semantic C stays exactly where it is. build_hash(), dominants() and
absents() in nabla_engine.py are doing semantic filing, not chi computation,
and need no change. What is forbidden is one line:

    chi = product(nabla_vector.values())          # <- STRUCTURAL BUG

CANON (W3-master-equation.canonical.md, 03-the-master-equation.md)
  chi(X) = C_W[ prod_{i=1..9} X_i ],  X in [0,1]^9, chi in [0,1]
  "C_W is wrapper/integrator, not a tenth product factor"  -- Locked
  C_W is CURRENTLY the identity map on [0,1]; "C_W explicitly defined beyond
  identity, or identity ratified" is still an OPEN GATE. While C_W is identity
  the conflated and correct computations return the same number. That is
  exactly why the separation is enforced by type now and not later.

LEAN STATUS (state precisely; do not round up)
  veto_collapse: any X_i = 0 => chi = 0, through both product AND wrapper.
  Machine-verified, Lean v4.21.0, lake build, zero sorry.
  QUALIFIER: Scalar = Int. The Mathlib/R port is PENDING. The canonical domain
  [0,1]^9 is real-valued, so the theorem is verified over a carrier that is not
  yet the canonical one. Cite it with that qualifier attached.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Callable, Dict, List, Optional

# Canonical order. C is deliberately absent.
CANONICAL_FACTORS: List[str] = ["G", "M", "E", "S", "T", "K", "Q", "R", "F"]

FACTOR_NAMES: Dict[str, str] = {
    "G": "Gravitation / Grace (Newton-Grace)",
    "M": "Mass-Energy / Meaning (Einstein-Meaning)",
    "E": "Electromagnetism / Truth (Maxwell-Truth)",
    "S": "Strong Force / Love (Yukawa-Agape)",
    "T": "Thermodynamics / Judgment (Clausius-Judgment)",
    "K": "Information / Logos (Shannon-Logos)",
    "Q": "Quantum Mechanics / Faith (Heisenberg-Faith)",
    "R": "Relativity / Grace-Frame (Einstein-Frame)",
    "F": "Weak Force / Moral Conservation (Fermi-Conservation)",
}


class CanonViolation(Exception):
    """Raised when a call site tries to treat the ten-field semantic vector as
    the nine-factor canonical vector."""


@dataclass(frozen=True)
class MasterEquationFactors:
    """The nine canonical X_i. Real-valued, each in [0,1]."""

    XG: float
    XM: float
    XE: float
    XS: float
    XT: float
    XK: float
    XQ: float
    XR: float
    XF: float

    def __post_init__(self) -> None:
        for key, val in asdict(self).items():
            if not (0.0 <= float(val) <= 1.0):
                raise CanonViolation(f"{key}={val} outside canonical domain [0,1]")

    @classmethod
    def from_semantic_vector(cls, vector: Dict[str, float]) -> "MasterEquationFactors":
        """Reject a tempting but invalid shared-letter conversion."""
        raise CanonViolation(
            "Nabla dimensions and Master Equation factors share letters but not "
            "measurements. Supply independently warranted normalized factor values "
            "with MasterEquationFactors.from_factor_values()."
        )

    @classmethod
    def from_factor_values(cls, values: Dict[str, float]) -> "MasterEquationFactors":
        """Build from independently established canonical values in [0,1]."""
        missing = [k for k in CANONICAL_FACTORS if k not in values]
        if missing:
            raise CanonViolation(f"factor values missing canonical factors: {missing}")
        extras = sorted(set(values) - set(CANONICAL_FACTORS))
        if extras:
            raise CanonViolation(f"unexpected canonical factor keys: {extras}")
        return cls(**{f"X{k}": float(values[k]) for k in CANONICAL_FACTORS})

    def as_list(self) -> List[float]:
        d = asdict(self)
        return [d[f"X{k}"] for k in CANONICAL_FACTORS]

    def product(self) -> float:
        p = 1.0
        for v in self.as_list():
            p *= v
        return p

    def zero_factors(self) -> List[str]:
        d = asdict(self)
        return [k for k in CANONICAL_FACTORS if d[f"X{k}"] == 0.0]


def identity_wrapper(x: float) -> float:
    """C_W as currently ruled: the identity map on [0,1].

    Open gate: 'C_W explicitly defined beyond identity, or identity ratified.'
    When that gate closes with a non-identity C_W, replace this function ONLY.
    Every call site below routes through the wrapper, so nothing else moves.
    """
    return x


@dataclass
class MasterEquationState:
    factors: MasterEquationFactors
    wrapper: Callable[[float], float] = identity_wrapper
    wrapper_name: str = "identity (current canonical ruling; ratification open)"

    def chi(self) -> float:
        """chi = C_W[ prod X_i ]. The only sanctioned way to compute chi.

        Note the wrapper is applied to the PRODUCT, not multiplied into it.
        """
        return float(self.wrapper(self.factors.product()))

    def veto(self) -> dict:
        zeros = self.factors.zero_factors()
        return {
            "triggered": bool(zeros),
            "zero_factors": zeros,
            "theorem": "veto_collapse",
            "lean_status": "machine-verified (v4.21.0, zero sorry) over Scalar=Int; "
                           "Mathlib/R port pending, canonical domain [0,1]^9 is real-valued",
        }


def forbid_ten_field_product(vector: Dict[str, float]) -> None:
    """Guard for any call site that receives a raw semantic vector and is about
    to multiply it. Import and call this at the top of such a function."""
    if "C" in vector:
        raise CanonViolation(
            "refusing to compute chi from a ten-field semantic vector. "
            "C_W is the wrapper, not a tenth factor. Use "
            "MasterEquationFactors.from_factor_values(v) then "
            "MasterEquationState(...).chi()."
        )
