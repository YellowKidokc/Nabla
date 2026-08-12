MARKERS = (
    "marker_1_scope", "marker_2_home_domain", "marker_3_native_domains",
    "marker_4_bridged_domains", "marker_5_object_type", "marker_6_claim_family",
    "marker_7_function_kind", "marker_8_source_kind", "marker_9_standing",
    "marker_10_native_grade", "marker_11_modality", "marker_12_evidence_grade",
    "marker_13_dispute", "marker_14_publication_state", "marker_15_component_state",
)


def missing_markers(value: dict) -> list[str]:
    return [marker for marker in MARKERS if marker not in value]
