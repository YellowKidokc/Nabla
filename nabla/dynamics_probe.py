"""
dynamics_probe.py - nabla-chi-classifier.station
DG7 / DynamicsGate7 - cross-domain dynamics extraction
Theophysics Research Initiative | POF 2828

NAMING
------
PROBE_ID = "DG7". Namespaced away from the canonical 7Q epistemological engine
(Q0-Q12, W7.8-the-7q-universal-classifier.canonical.md), from
_DORMANT/7q-classifier.station, and from 04_OPENAI_7Q in the paper-intelligence
suite. Flip PROBE_ID and PROBE_NAME below if CDR_DYNAMICS_7 is preferred;
nothing else references the string.

SEVEN VISIBLE QUESTIONS, EIGHT STORED FIELDS
--------------------------------------------
The human interface stays seven. Restoration stores two:

    restoration.self      = W grad(chi)   -- will, on an EXISTING slope
    restoration.external  = eta           -- source term, at ZERO slope

That is not a stylistic split. Two of the three machine-verified theorems in
the canon exist to separate them, from the same premise:

    stationary_without_source     grad(chi)=0, source=0    => velocity 0
    source_makes_velocity_nonzero grad(chi)=0, source!=0   => velocity nonzero

Collapsing them into one RESTORATION field erases BC2 - named in the 7Q as the
exact seam where physics and theology separate.

PROVENANCE, KEPT PRECISE
------------------------
Six slots anchor to the differential stack (Level 0 -> Level 2). COUNTEREXAMPLE
does NOT; it anchors to the verification/falsification architecture. Do not
describe all seven as a read-off of the equations.

STATUS VOCABULARY - DELIBERATELY TWO-VALUED
-------------------------------------------
Emits PRESENT / PARTIAL / ABSENT only. A regex cannot distinguish "this
document has no threshold" from "this document has a threshold and did not say
so." NOT_APPLICABLE and UNRESOLVED are semantic rulings and belong to the
reader, not to this lane.
"""
from __future__ import annotations

import re
from typing import Dict, List

PROBE_ID = "DG7"
PROBE_NAME = "DynamicsGate7"
PROBE_VERSION = "0.1.0"

# Public interface: seven questions, in order.
VISIBLE_QUESTIONS = [
    ("coherence", "What counts as coherence?"),
    ("degradation", "What counts as degradation?"),
    ("measure", "How is it measured?"),
    ("threshold", "Is there a threshold?"),
    ("asymmetry", "Is the transition asymmetric?"),
    ("restoration", "What restores it?"),
    ("counterexample", "Is there a counterexample?"),
]

# Storage schema: restoration expands to two fields. Everything else is 1:1.
STORED_FIELDS = [
    "coherence", "degradation", "measure", "threshold", "asymmetry",
    "restoration_self", "restoration_external", "counterexample",
]

SLOTS: Dict[str, dict] = {
    "coherence": {
        "anchor": "chi = C_W[prod X_i] - the alignment scalar",
        "anchor_layer": "differential stack (Level 1)",
        "families": {
            "chi": [r"\bchi\b", r"χ", r"\balign(?:ed|ment)\b"],
            "coherence": [r"\bcoheren\w+", r"\bin phase\b", r"\bintegrat\w+"],
            "wholeness": [r"\bwhole\w*\b", r"\bunity\b", r"\bintact\b"],
        },
    },
    "degradation": {
        "anchor": "D (drift) in Lambda_i = A_i log2(1 + T_i/D_i)",
        "anchor_layer": "differential stack (Level 0)",
        "families": {
            "drift": [r"\bdrift\w*", r"\bdecay\w*", r"\bdegrad\w+", r"\berod\w+"],
            "entropy": [r"\bentrop\w+", r"\bdisorder\b", r"\bnoise\b", r"\bsecond law\b"],
            "fragmentation": [r"\bfragment\w+", r"\bdecoher\w+", r"\bfractur\w+"],
        },
    },
    "measure": {
        "anchor": "Lambda_i = A_i log2(1 + T_i/D_i) -> X_i = Lambda_i / Lambda_i_ref",
        "anchor_layer": "differential stack (Level 0 -> boundary)",
        "families": {
            "quantity": [r"\bmeasur\w+", r"\bmetric\b", r"\bobservable\b", r"\bquantif\w+"],
            "formalism": [r"\bbits?/s\b", r"\blog_?2\b", r"\bcapacity\b", r"\bbandwidth\b",
                          r"\bnormaliz\w+", r"\bdimensionless\b"],
            "instrument": [r"\bsigma\b", r"σ", r"\bcorrelat\w+", r"\bexperiment\w*"],
        },
    },
    "threshold": {
        "anchor": "chi_c in Phi_L(chi) = tanh(beta_L(chi - chi_c))",
        "anchor_layer": "differential stack (phase form)",
        "families": {
            "critical": [r"\bthreshold\b", r"\bcritical\b", r"\bchi_?c\b", r"χ_?c"],
            "regime": [r"\bregime\b", r"\bphase (?:change|transition)\b", r"\btipping\b",
                       r"\btanh\b"],
            "boundary": [r"\bboundary condition\b", r"\bfloor\b", r"\bcutoff\b"],
        },
    },
    "asymmetry": {
        "anchor": "Law 9 - directional, parity-breaking, time-translation preserved",
        "anchor_layer": "differential stack (Law 9)",
        "families": {
            "direction": [r"\basymmetr\w+", r"\bdirectional\b", r"\birreversib\w+"],
            "parity": [r"\bparity\b", r"\bCP violation\b", r"\bbreaks? (?:parity|symmetry)\b"],
            "arrow": [r"\barrow of time\b", r"\bcannot be undone\b", r"\bnon-?reversib\w+"],
        },
    },
    "restoration_self": {
        "anchor": "W in Xdot = W grad(chi) + eta - will, acts ONLY through an existing slope",
        "anchor_layer": "differential stack (Level 2); Lean: stationary_without_source",
        "families": {
            "will": [r"\bfree will\b", r"\bwill\b", r"\bchoice\b", r"\bchoos\w+", r"\bvolition\w*"],
            "gradient": [r"\bgradient\b", r"\bgrad\b", r"\bslope\b", r"\bnabla\b", r"∇"],
            "effort": [r"\brepent\w+", r"\bpractice\b", r"\bdiscipline\b", r"\bascent\b"],
        },
    },
    "restoration_external": {
        "anchor": "eta in Xdot = W grad(chi) + eta - source term, acts AT ZERO slope",
        "anchor_layer": "differential stack (Level 2); Lean: source_makes_velocity_nonzero",
        "families": {
            "grace": [r"\bgrace\b", r"\bcharis\b", r"\beta\b", r"η", r"\bunmerited\b"],
            "external": [r"\bexternal source\b", r"\bsource term\b", r"\boutside the system\b",
                         r"\bflat spot\b", r"\bzero gradient\b"],
            "negentropy": [r"\bnegentrop\w+", r"\batonement\b", r"\bredempt\w+", r"\bW_?grace\b"],
        },
    },
    "counterexample": {
        "anchor": "kill conditions / falsification ledger",
        "anchor_layer": "VERIFICATION architecture - NOT the differential stack",
        "families": {
            "kill": [r"\bkill (?:condition|test|gate)\w*", r"\bfalsif\w+", r"\bwould refute\b",
                     r"\block gate\b"],
            "counter": [r"\bcounterexample\b", r"\bcounter-?evidence\b", r"\bhostile question\b"],
            "ledger": [r"\bobjection ledger\b", r"\bretired claim\w*", r"\bopen (?:issue|problem|gate)s?\b"],
        },
    },
}


def _scan(text: str, patterns: List[str], cap: int, ctx: int) -> List[dict]:
    hits: List[dict] = []
    for pat in patterns:
        for m in re.compile(pat, re.IGNORECASE).finditer(text):
            if len(hits) >= cap:
                break
            a = max(0, m.start() - ctx // 2)
            b = min(len(text), m.end() + ctx // 2)
            hits.append({
                "match": m.group(0),
                "line": text.count("\n", 0, m.start()) + 1,
                "context": " ".join(text[a:b].split()),
            })
    return hits


def probe(text: str, evidence_per_family: int = 2, context_chars: int = 160) -> dict:
    """Run DG7 over a document. Returns eight stored fields plus a seven-question
    public view."""
    stored: Dict[str, dict] = {}

    for slot in STORED_FIELDS:
        spec = SLOTS[slot]
        families: Dict[str, List[dict]] = {}
        for fam, pats in spec["families"].items():
            hits = _scan(text, pats, evidence_per_family, context_chars)
            if hits:
                families[fam] = hits
        n = len(families)
        status = "PRESENT" if n >= 2 else ("PARTIAL" if n == 1 else "ABSENT")
        stored[slot] = {
            "status": status,
            "canonical_anchor": spec["anchor"],
            "anchor_layer": spec["anchor_layer"],
            "families_matched": n,
            "evidence": families,
            "semantic_lane_may_upgrade_to": ["NOT_APPLICABLE", "UNRESOLVED"]
            if status == "ABSENT" else [],
        }

    # Seven-question public view. Restoration folds for display only.
    def _fold(a: str, b: str) -> str:
        order = {"PRESENT": 2, "PARTIAL": 1, "ABSENT": 0}
        return max((stored[a]["status"], stored[b]["status"]), key=lambda s: order[s])

    visible = {}
    for key, question in VISIBLE_QUESTIONS:
        if key == "restoration":
            visible[key] = {
                "question": question,
                "status": _fold("restoration_self", "restoration_external"),
                "self": stored["restoration_self"]["status"],
                "external": stored["restoration_external"]["status"],
            }
        else:
            visible[key] = {"question": question, "status": stored[key]["status"]}

    return {
        "probe": {"id": PROBE_ID, "name": PROBE_NAME, "version": PROBE_VERSION},
        "visible_questions": visible,
        "stored_fields": stored,
        "note": "ABSENT = no qualifying lexical evidence in this lane. It does not "
                "establish that the slot does not apply.",
    }
