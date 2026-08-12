"""Periodic-15 marker contract.

Frozen by the Consilience Atlas Canonical Architecture v0.3, section 9
(2026-08-12). Marker positions and meanings never change across Paper,
Series, Cross-Series, or Global resolutions; higher resolutions aggregate,
they do not reinterpret.

Key format `m##_name` matches `templates/atlas-workbench.html`, which was
merged against this contract. The retired `marker_N_*` names carried a
pre-freeze semantics (scope / native_grade / modality / publication_state /
component_state) and must not be reintroduced.

Contract rules:
- m04 lists admitted bridges only; candidate similarities stay in bridges[].
- m12-m14 are computed markers: null until the deterministic computation
  layer fills them, and never hand-entered or AI-fabricated.
- Source is not commitment (m08 vs m09); standing is not dispute (m10 vs m11).
- Reality Mirror is top-level metadata, never a sixteenth marker.
"""

MARKERS = (
    "m01_identity", "m02_home_domain", "m03_native_domains",
    "m04_bridged_domains", "m05_object_type", "m06_claim_family",
    "m07_function_kind", "m08_source", "m09_commitment",
    "m10_standing", "m11_dispute", "m12_evidence_grade",
    "m13_usage_runs", "m14_graph_degree", "m15_alert_state",
)

# Derived-until-computed markers (Canonical Architecture v0.3, section 18.12).
# These must be null in any record whose computation layer has not run.
COMPUTED_MARKERS = (
    "m12_evidence_grade", "m13_usage_runs", "m14_graph_degree",
)


def missing_markers(value: dict) -> list[str]:
    return [marker for marker in MARKERS if marker not in value]


def uncomputed_markers(value: dict) -> list[str]:
    """Computed markers still holding their null (not-yet-computed) state."""
    return [marker for marker in COMPUTED_MARKERS if value.get(marker) is None]
