"""
semantic_proposer.py - nabla-chi-classifier.station
Theophysics Research Initiative | POF 2828

THE MISSING LAYER
-----------------
nabla_engine.py says of itself: "74 independent classification factors. No
lexicon. Pure structure." It has the address, the vector, the hash and the
confidence container - and nothing that reads text. This module is that
lexicon. It PROPOSES; nabla_engine files; a reader rules.

TRUST BOUNDARY
--------------
Output is a proposal, never a classification. Concretely:

  factor_mentions     PRESENT / PARTIAL / ABSENT per canonical factor
  possible_veto_flags factors whose lexical evidence was ABSENT
  veto_status         always "NOT_ADJUDICATED"

A lexical miss is not evidence that X_i = 0. Regex ABSENT never enforces the
veto; it only nominates a factor for semantic review. The veto itself is a
machine-verified theorem (veto_collapse, Lean v4.21.0, zero sorry, Scalar=Int
with the Mathlib/R port pending) - which makes it exactly the kind of result a
regex must not be allowed to trigger.

C IS KEPT
---------
Nabla's semantic C (Coherence/Unity) remains one of the ten address dimensions
and is proposed here alongside the rest. It is emitted in `semantic_vector`.
It is NOT emitted in `factor_mentions`, which covers the canonical nine only.
See master_equation_types.py for why those are different types.
"""
from __future__ import annotations

import re
from typing import Dict, List

from master_equation_types import CANONICAL_FACTORS, FACTOR_NAMES

PROPOSER_VERSION = "0.1.0"

# Nabla address order is independent of the Master Equation's canonical order.
SEMANTIC_DIMENSIONS = ["G", "M", "E", "S", "T", "K", "R", "Q", "F", "C"]

LEXICON: Dict[str, List[str]] = {
    "G": [r"\bground\w*", r"\bauthority\b", r"\baxiom\w*", r"\bfoundation\w*",
          r"\bsource\b", r"\bGod\b", r"\bFather\b", r"\bfirst principle\w*"],
    "M": [r"\bmechanis\w+", r"\boperat\w+", r"\bprocess\w*", r"\bforce\b",
          r"\baction\b", r"\bfunction\b", r"\bequation\w*"],
    "E": [r"\bentrop\w+", r"\bdisorder\b", r"\bdecay\w*", r"\bnoise\b",
          r"\bsin\b", r"\bdrift\w*", r"\bdegrad\w+"],
    "S": [r"\bidentity\b", r"\bself\b", r"\bperson\w*", r"\bI AM\b", r"\bbeing\b",
          r"\bwho (?:he|she|it|we|you) (?:is|are)\b"],
    "T": [r"\btime\b", r"\btemporal\b", r"\bsequence\b", r"\bhistory\b",
          r"\bbefore\b", r"\bafter\b", r"\beternal\b"],
    "K": [r"\binformation\b", r"\bknowledge\b", r"\bbits?\b", r"\bShannon\b",
          r"\bsignal\b", r"\bdata\b", r"\bchannel\b"],
    "Q": [r"\bexperienc\w+", r"\bqualia\b", r"\bconscious\w*", r"\bfelt\b",
          r"\bawareness\b", r"\bobserver\b", r"\bphi\b", r"Φ"],
    "R": [r"\brelation\w*", r"\bbond\b", r"\bbetween\b", r"\bcoupl\w+",
          r"\bcovenant\b", r"\blove\b", r"\bagape\b"],
    "F": [r"\bfaith\b", r"\btrust\b", r"\bbelief\b", r"\bpistis\b", r"\bsurrender\b"],
    "C": [r"\bcoheren\w+", r"\bChrist\b", r"\bLogos\b", r"\bC_?W\b", r"\bwrapper\b",
          r"\bunity\b", r"\bunif\w+"],
}

# These detect references to the canonical equation factors. They do not turn
# semantic density into X_i values and cannot adjudicate the veto.
FACTOR_LEXICON: Dict[str, List[str]] = {
    "G": [r"\bgravit\w+", r"\bgrace\b", r"\bNewton\b"],
    "M": [r"\bmass(?:-energy)?\b", r"\benergy\b", r"\bmeaning\b", r"\bEinstein[- ]Meaning\b"],
    "E": [r"\belectromagnet\w*", r"\btruth\b", r"\bMaxwell\b"],
    "S": [r"\bstrong (?:nuclear )?force\b", r"\bagape\b", r"\bYukawa\b"],
    "T": [r"\bthermodynamic\w*", r"\bjudg(?:e|ment)\w*", r"\bClausius\b"],
    "K": [r"\binformation\b", r"\bLogos\b", r"\bShannon\b"],
    "Q": [r"\bquantum\b", r"\bfaith\b", r"\bHeisenberg\b"],
    "R": [r"\brelativit\w*", r"\bgrace[- ]frame\b", r"\bEinstein[- ]Frame\b"],
    "F": [r"\bweak (?:nuclear )?force\b", r"\bmoral conservation\b", r"\bFermi\b"],
}

DEFAULT_BANDS = {"1": 0.4, "2": 1.2, "3": 3.0}
DEFAULT_MENTION_MIN = {"PARTIAL": 1, "PRESENT": 3}  # raw hit counts


def _band(density: float, bands: Dict[str, float]) -> int:
    if density >= bands["3"]:
        return 3
    if density >= bands["2"]:
        return 2
    if density >= bands["1"]:
        return 1
    return 0


def propose(text: str, bands: Dict[str, float] | None = None,
            mention_min: Dict[str, int] | None = None) -> dict:
    """Propose a ten-dimension semantic vector and nine-factor mention report."""
    bands = bands or DEFAULT_BANDS
    mention_min = mention_min or DEFAULT_MENTION_MIN

    words = max(len(re.findall(r"\b\w+\b", text)), 1)
    per_k = words / 1000.0

    counts: Dict[str, int] = {}
    density: Dict[str, float] = {}
    vector: Dict[str, int] = {}
    evidence: Dict[str, List[str]] = {}

    for dim in SEMANTIC_DIMENSIONS:
        found: List[str] = []
        for pat in LEXICON[dim]:
            found.extend(m.group(0) for m in re.finditer(pat, text, re.IGNORECASE))
        counts[dim] = len(found)
        density[dim] = round(len(found) / per_k, 3)
        vector[dim] = _band(density[dim], bands)
        evidence[dim] = sorted(set(t.lower() for t in found))[:8]

    # Factor mentions use the canonical physical/spiritual translations.
    factor_mentions: Dict[str, str] = {}
    for key in CANONICAL_FACTORS:
        n = sum(
            len(list(re.finditer(pattern, text, re.IGNORECASE)))
            for pattern in FACTOR_LEXICON[key]
        )
        factor_mentions[key] = (
            "PRESENT" if n >= mention_min["PRESENT"]
            else "PARTIAL" if n >= mention_min["PARTIAL"]
            else "ABSENT"
        )

    possible_veto = [k for k, v in factor_mentions.items() if v == "ABSENT"]

    return {
        "proposer": {"version": PROPOSER_VERSION, "tier": "lexical (tier 1)"},
        "words": words,
        "semantic_vector": vector,                       # ten dims, C included
        "semantic_vector_string": "".join(f"{k}{vector[k]}" for k in SEMANTIC_DIMENSIONS),
        "density_per_1k_words": density,
        "evidence_terms": evidence,
        "factor_mentions": factor_mentions,              # canonical nine only
        "factor_names": FACTOR_NAMES,
        "possible_veto_flags": possible_veto,
        "veto_status": "NOT_ADJUDICATED",
        "note": "ABSENT means no qualifying lexical evidence in this lane; it does "
                "not establish Xi = 0. Veto adjudication requires the semantic lane.",
        "confidence": "LOW - term density only. Proposal, not classification.",
    }


def to_nabla_semantic_vector(proposal: dict):
    """Hand the proposal to the existing engine. Import is local so this module
    stays usable standalone."""
    from nabla_engine import SemanticVector  # existing deterministic core
    return SemanticVector(**proposal["semantic_vector"])
