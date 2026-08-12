#!/usr/bin/env python3
"""Shared contracts and adapters for independent NLP and API comparison."""

from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SYSTEM_PROMPT = """You are one independent analysis lane in the Consilience Atlas.
Follow the supplied stage contract exactly. Be conservative. Preserve source
quotations. Keep physics, mathematics, empirical evidence, bridge language, and
theological interpretation distinctly labeled. UNKNOWN and UNRESOLVED are valid.
Do not promote Candidate material or infer evidence from repetition.
Return one valid JSON object only."""

MODES = [
    "AXIOM", "PRE_ASSUMPTION", "EMPIRICAL_EVENT", "HISTORICAL_RECORD",
    "MATHEMATICAL_PROOF", "FORMAL_DERIVATION", "CLASSIFICATION",
    "INTERPRETATION", "SYMBOLIC_TRUTH", "MORAL_CLAIM",
    "THEOLOGICAL_CLAIM", "EXPERIENTIAL_REPORT", "PREDICTION", "UNKNOWN",
]
DOMAINS = [
    "physics", "mathematics", "theology", "information_theory",
    "consciousness", "ethics", "history", "narrative", "unknown",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_id(prefix: str, text: str) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]
    return f"{prefix}:{digest}"


def tokens(text: str) -> set[str]:
    stop = {"the", "and", "that", "this", "with", "from", "into", "then",
            "when", "where", "which", "have", "does", "not", "are", "for"}
    return {word for word in re.findall(r"[a-z0-9]+", text.lower())
            if len(word) > 2 and word not in stop}


def jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left or right else 1.0


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n"))
    pieces = re.split(r"(?<=[.!?])\s+|\n{2,}", normalized)
    return [piece.strip() for piece in pieces if piece.strip()]


def likely_claim(value: str) -> bool:
    lower_raw = value.lower().strip()
    if (
        lower_raw.startswith(("# ", "## ", "### ", "[home]", "[previous", "[next"))
        or re.search(r"\bsheet\s+\d+\s+of\s+\d+\b", lower_raw)
        or lower_raw.count("](") >= 2
    ):
        return False
    plain = re.sub(r"[#*|>-]", " ", value)
    words = re.findall(r"\b\w+\b", plain)
    if len(words) < 6:
        return "=" in value and len(words) >= 2
    return not plain.lower().strip().startswith(
        ("table of contents", "copyright", "click here", "next:", "previous:")
    )


def normalize_api_stage(stage_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Normalize provider naming drift into the shared stage contract."""
    if stage_id == "01_claims":
        rows = []
        for item in data.get("claims", []):
            if not isinstance(item, dict):
                continue
            text = str(item.get("text") or item.get("claim") or "").strip()
            if not text:
                continue
            rows.append({
                "claim_id": stable_id("claim", text),
                "text": text,
                "source_quote": str(item.get("source_quote") or item.get("quote") or text),
                "extraction_status": "candidate",
            })
        return {"claims": rows}
    if stage_id == "02_classification":
        mode_aliases = {
            "formal": "FORMAL_DERIVATION",
            "formal_model": "FORMAL_DERIVATION",
            "normative": "MORAL_CLAIM",
            "theological": "THEOLOGICAL_CLAIM",
            "bridge": "INTERPRETATION",
            "empirical": "EMPIRICAL_EVENT",
            "historical": "HISTORICAL_RECORD",
            "prediction": "PREDICTION",
        }
        rows = []
        for item in data.get("claim_assessments", []):
            if not isinstance(item, dict):
                continue
            raw_mode = str(item.get("mode") or item.get("epistemic_mode") or "UNKNOWN")
            mode = mode_aliases.get(raw_mode.lower(), raw_mode.upper())
            if mode not in MODES:
                mode = "UNKNOWN"
            rows.append({
                "claim_id": str(item.get("claim_id") or item.get("id") or ""),
                "mode": mode,
                "domain": str(item.get("domain") or item.get("native_domain") or "unknown"),
                "standing": str(item.get("standing") or "active_candidate"),
                "confidence": float(item.get("confidence", 0.0) or 0.0),
            })
        return {"claim_assessments": rows}
    if stage_id == "03_dependencies":
        edges = []
        for item in data.get("dependencies", []):
            if isinstance(item, list) and len(item) >= 2:
                item = {"from": item[1], "to": item[0]}
            if not isinstance(item, dict):
                continue
            edges.append({
                "from": str(item.get("from") or item.get("source") or ""),
                "relation": str(item.get("relation") or "depends_on_candidate"),
                "to": str(item.get("to") or item.get("target") or ""),
                "basis": str(item.get("basis") or item.get("reason") or "api_proposal"),
                "score": float(item.get("score", 0.0) or 0.0),
            })
        load = data.get("load_bearing_claim_ids", data.get("load_bearing", []))
        return {"dependencies": edges, "load_bearing_claim_ids": load if isinstance(load, list) else []}
    if stage_id == "04_falsification":
        rows = []
        for item in data.get("tests", []):
            if not isinstance(item, dict):
                continue
            rows.append({
                "claim_id": str(item.get("claim_id") or item.get("id") or ""),
                "type": str(item.get("type") or "defeat_condition"),
                "condition": str(item.get("condition") or item.get("kill_condition") or item.get("test") or ""),
                "status": str(item.get("status") or "candidate_untested"),
            })
        return {"tests": rows}
    if stage_id == "05_evidence":
        support = []
        for item in data.get("source_support", []):
            if not isinstance(item, dict):
                continue
            support.append({
                "claim_id": str(item.get("claim_id") or ""),
                "source_quote": str(item.get("source_quote") or item.get("support") or ""),
                "relation": str(item.get("relation") or "source_asserts"),
                "independent": bool(item.get("independent", False)),
            })
        requirements = data.get("evidence_requirements", [])
        return {
            "source_support": support,
            "evidence_requirements": requirements if isinstance(requirements, list) else [],
        }
    if stage_id == "06_contradictions":
        def relation_rows(key: str) -> list[dict[str, Any]]:
            rows = []
            for item in data.get(key, []):
                if not isinstance(item, dict):
                    continue
                ids = item.get("claim_ids", [])
                rows.append({
                    "claim_a": str(item.get("claim_a") or (ids[0] if len(ids) > 0 else "")),
                    "claim_b": str(item.get("claim_b") or (ids[1] if len(ids) > 1 else "")),
                    "reason": str(item.get("reason") or item.get("description") or ""),
                    "status": str(item.get("status") or "candidate"),
                })
            return rows
        return {"contradictions": relation_rows("contradictions"), "tensions": relation_rows("tensions")}
    if stage_id == "07_dynamics":
        vector = data.get("semantic_vector", {})
        dimensions = ("G", "M", "E", "S", "T", "K", "R", "Q", "F", "C")
        if not isinstance(vector, dict) or not all(key in vector for key in dimensions):
            vector = {key: 0 for key in dimensions}
        vector = {
            key: max(0, min(3, int(vector.get(key, 0) or 0)))
            for key in dimensions
        }
        raw_dg7 = data.get("dg7", {})
        if isinstance(raw_dg7, dict) and isinstance(raw_dg7.get("visible_questions"), dict):
            raw_dg7 = {
                key: value.get("status", "UNRESOLVED")
                for key, value in raw_dg7["visible_questions"].items()
                if isinstance(value, dict)
            }
        dg7_keys = (
            "coherence", "degradation", "measure", "threshold",
            "asymmetry", "restoration", "counterexample",
        )
        dg7 = {
            key: str(raw_dg7.get(key, "UNRESOLVED")).upper()
            if isinstance(raw_dg7, dict) else "UNRESOLVED"
            for key in dg7_keys
        }
        return {
            "semantic_vector": vector,
            "dg7": dg7,
            "veto_status": "NOT_ADJUDICATED",
        }
    if stage_id == "08_natural_process_mirror":
        rows = []
        for item in data.get("natural_process_mirrors", []):
            if not isinstance(item, dict):
                continue
            stage_map = item.get("ordered_stage_map", [])
            if not isinstance(stage_map, list):
                stage_map = []
            rows.append({
                "claim_id": str(item.get("claim_id") or ""),
                "source_process": str(item.get("source_process") or ""),
                "natural_domain": str(item.get("natural_domain") or "unknown"),
                "natural_process": str(item.get("natural_process") or ""),
                "part_count_source": int(item.get("part_count_source", 0) or 0),
                "part_count_mirror": int(item.get("part_count_mirror", 0) or 0),
                "ordered_stage_map": [
                    {
                        "source_stage": str(row.get("source_stage") or ""),
                        "natural_stage": str(row.get("natural_stage") or ""),
                        "same_direction": bool(row.get("same_direction", False)),
                        "same_function": bool(row.get("same_function", False)),
                        "notes": str(row.get("notes") or ""),
                    }
                    for row in stage_map if isinstance(row, dict)
                ],
                "directionality": str(item.get("directionality") or "unknown"),
                "functionality_match": str(item.get("functionality_match") or "unknown"),
                "mapping_type": str(item.get("mapping_type") or "none"),
                "constraints_preserved": item.get("constraints_preserved", [])
                if isinstance(item.get("constraints_preserved", []), list) else [],
                "failure_modes_preserved": item.get("failure_modes_preserved", [])
                if isinstance(item.get("failure_modes_preserved", []), list) else [],
                "lost": item.get("lost", []) if isinstance(item.get("lost", []), list) else [],
                "introduced": item.get("introduced", []) if isinstance(item.get("introduced", []), list) else [],
                "test_needed": item.get("test_needed", [])
                if isinstance(item.get("test_needed", []), list) else [],
                "status": str(item.get("status") or "unresolved"),
            })
        questions = data.get("unresolved_natural_process_questions", [])
        if not isinstance(questions, list):
            questions = [str(questions)]
        status = str(data.get("mirror_gate_status") or "UNRESOLVED").upper()
        allowed = {"PASSED_CANDIDATE", "PARTIAL", "NEEDS_NATURAL_ANCHOR", "FAILED", "UNRESOLVED"}
        return {
            "natural_process_mirrors": rows,
            "unresolved_natural_process_questions": questions,
            "mirror_gate_status": status if status in allowed else "UNRESOLVED",
        }
    return data


def build_packet(source: Path, contract: dict[str, Any]) -> dict[str, Any]:
    raw = source.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    packet = {
        "schema_version": "atlas-method-packet/v1",
        "packet_id": f"method-packet:{sha256_bytes(raw)[:16]}",
        "created_at": now(),
        "source": {
            "path": str(source.resolve()),
            "filename": source.name,
            "sha256": sha256_bytes(raw),
            "bytes": len(raw),
            "text": text,
        },
        "contract": {
            "schema_version": contract["schema_version"],
            "sha256": sha256_bytes(canonical_bytes(contract)),
            "stage_ids": [stage["id"] for stage in contract["stages"]],
        },
        "rules": contract["rules"],
    }
    packet["packet_sha256"] = sha256_bytes(canonical_bytes(packet))
    return packet


def validate_packet(packet: dict[str, Any], contract: dict[str, Any]) -> None:
    expected = sha256_bytes(canonical_bytes(contract))
    if packet.get("contract", {}).get("sha256") != expected:
        raise ValueError("Packet contract hash does not match the active contract")
    source = packet.get("source", {})
    if sha256_bytes(source.get("text", "").encode("utf-8")) != source.get("sha256"):
        raise ValueError("Packet source text does not match its SHA-256")


def empty_for(stage_id: str) -> dict[str, Any]:
    defaults = {
        "01_claims": {"claims": []},
        "02_classification": {"claim_assessments": []},
        "03_dependencies": {"dependencies": [], "load_bearing_claim_ids": []},
        "04_falsification": {"tests": []},
        "05_evidence": {"source_support": [], "evidence_requirements": []},
        "06_contradictions": {"contradictions": [], "tensions": []},
        "07_dynamics": {"semantic_vector": {}, "dg7": {}, "veto_status": "UNRESOLVED"},
        "08_natural_process_mirror": {
            "natural_process_mirrors": [],
            "unresolved_natural_process_questions": [],
            "mirror_gate_status": "UNRESOLVED",
        },
        "09_synthesis": {
            "summary": "", "strongest_points": [], "weakest_points": [],
            "unresolved": [], "recommended_next_actions": [],
        },
    }
    return defaults[stage_id]


def validate_stage(stage: dict[str, Any], data: Any) -> list[str]:
    if not isinstance(data, dict):
        return ["stage output is not an object"]
    return [f"missing required key: {key}" for key in stage["required_keys"] if key not in data]


def service_available(url: str, timeout: int) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300
    except Exception:
        return False


def local_classify(text: str, labels: list[str], runtime: dict[str, Any]) -> tuple[str, float]:
    cfg = runtime["local_nlp"]
    payload = json.dumps({"text": text, "labels": labels}).encode("utf-8")
    request = urllib.request.Request(
        cfg["classify_url"], data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=cfg["timeout_seconds"]) as response:
            value = json.loads(response.read().decode("utf-8"))
        labels_out = value.get("labels", [])
        scores = value.get("scores", [])
        if labels_out and scores:
            return str(labels_out[0]), float(scores[0])
        return str(value.get("label", labels[-1])), float(value.get("score", 0.0))
    except Exception:
        return labels[-1], 0.0


def lexical_mode(text: str) -> str:
    lower = text.lower()
    rules = [
        ("MATHEMATICAL_PROOF", ("theorem", "proof", "qed", "lemma")),
        ("FORMAL_DERIVATION", ("equation", "therefore", "implies", "gradient", "chi", "=")),
        ("EMPIRICAL_EVENT", ("observed", "measured", "experiment", "dataset")),
        ("PREDICTION", ("predict", "will produce", "would result")),
        ("THEOLOGICAL_CLAIM", ("god", "christ", "trinity", "grace", "theological")),
        ("MORAL_CLAIM", ("moral", "ought", "good", "evil", "sin")),
        ("INTERPRETATION", ("suggests", "means", "read as", "interpreted")),
    ]
    for mode, terms in rules:
        if any(term in lower for term in terms):
            return mode
    return "UNKNOWN"


def lexical_domain(text: str) -> str:
    lower = text.lower()
    scores = {
        "physics": sum(term in lower for term in ("physics", "force", "energy", "thermodynamic", "quantum", "relativity")),
        "mathematics": sum(term in lower for term in ("equation", "theorem", "proof", "gradient", "product", "zero")),
        "theology": sum(term in lower for term in ("god", "christ", "trinity", "grace", "faith", "theology")),
        "information_theory": sum(term in lower for term in ("information", "shannon", "entropy", "signal")),
        "consciousness": sum(term in lower for term in ("conscious", "qualia", "experience", "observer")),
        "ethics": sum(term in lower for term in ("moral", "good", "evil", "ought")),
        "history": sum(term in lower for term in ("history", "historical", "century", "dated")),
        "narrative": sum(term in lower for term in ("story", "character", "narrative")),
    }
    top = max(scores, key=scores.get)
    return top if scores[top] else "unknown"


def local_stage(stage_id: str, text: str, prior: dict[str, Any],
                runtime: dict[str, Any], semantic_service: bool) -> dict[str, Any]:
    claims = prior.get("01_claims", {}).get("claims", [])
    assessments = prior.get("02_classification", {}).get("claim_assessments", [])
    assessment_by_id = {row.get("claim_id"): row for row in assessments}

    if stage_id == "01_claims":
        rows = []
        seen = set()
        for sentence in split_sentences(text):
            clean = re.sub(r"\s+", " ", sentence).strip()
            if not likely_claim(clean) or clean.lower() in seen:
                continue
            seen.add(clean.lower())
            rows.append({
                "claim_id": stable_id("claim", clean),
                "text": clean,
                "source_quote": clean,
                "extraction_status": "candidate",
            })
            if len(rows) >= 30:
                break
        return {"claims": rows}

    if stage_id == "02_classification":
        rows = []
        for claim in claims:
            if semantic_service:
                mode, mode_score = local_classify(claim["text"], MODES, runtime)
                domain, domain_score = local_classify(claim["text"], DOMAINS, runtime)
            else:
                mode, mode_score = lexical_mode(claim["text"]), 0.35
                domain, domain_score = lexical_domain(claim["text"]), 0.35
            rows.append({
                "claim_id": claim["claim_id"], "mode": mode, "domain": domain,
                "standing": "active_candidate",
                "confidence": round(min(mode_score, domain_score), 4),
            })
        return {"claim_assessments": rows}

    if stage_id == "03_dependencies":
        edges = []
        for left_index, left in enumerate(claims):
            left_terms = tokens(left["text"])
            for right in claims[left_index + 1:]:
                overlap = jaccard(left_terms, tokens(right["text"]))
                if overlap >= 0.30:
                    edges.append({
                        "from": right["claim_id"], "relation": "depends_on_candidate",
                        "to": left["claim_id"], "basis": "lexical_overlap",
                        "score": round(overlap, 4),
                    })
        load_bearing = [
            claim["claim_id"] for claim in claims
            if any(term in claim["text"].lower()
                   for term in ("equation", "therefore", "if ", "axiom", "depends", "requires"))
        ][:12]
        return {"dependencies": edges, "load_bearing_claim_ids": load_bearing}

    if stage_id == "04_falsification":
        tests = []
        for claim in claims:
            mode = assessment_by_id.get(claim["claim_id"], {}).get("mode", "UNKNOWN")
            if mode in {"THEOLOGICAL_CLAIM", "MORAL_CLAIM", "SYMBOLIC_TRUTH"}:
                condition = (
                    "State a countermodel or interpretive alternative that explains the same "
                    "material with fewer unsupported bridge assumptions."
                )
                test_type = "defeat_condition"
            else:
                condition = f"Produce a scoped counterexample or failed prediction for: {claim['text']}"
                test_type = "counterexample_test"
            tests.append({
                "claim_id": claim["claim_id"], "type": test_type,
                "condition": condition, "status": "candidate_untested",
            })
        return {"tests": tests}

    if stage_id == "05_evidence":
        support = [{
            "claim_id": claim["claim_id"], "source_quote": claim["source_quote"],
            "relation": "source_asserts", "independent": False,
        } for claim in claims]
        requirements = []
        for claim in claims:
            mode = assessment_by_id.get(claim["claim_id"], {}).get("mode", "UNKNOWN")
            needed = {
                "MATHEMATICAL_PROOF": ["formal proof artifact", "axiom audit"],
                "FORMAL_DERIVATION": ["derivation", "domain and units check", "countermodel"],
                "EMPIRICAL_EVENT": ["dataset or instrument receipt", "independent replication"],
                "HISTORICAL_RECORD": ["primary source", "independent corroboration"],
                "THEOLOGICAL_CLAIM": ["scriptural or doctrinal warrant", "interpretive alternatives"],
            }.get(mode, ["independent source", "rival explanation"])
            requirements.append({
                "claim_id": claim["claim_id"], "required": needed, "status": "unresolved"
            })
        return {"source_support": support, "evidence_requirements": requirements}

    if stage_id == "06_contradictions":
        tensions = []
        for index, left in enumerate(claims):
            left_terms = tokens(left["text"])
            left_neg = bool(re.search(r"\b(no|not|never|cannot|without)\b", left["text"].lower()))
            for right in claims[index + 1:]:
                overlap = jaccard(left_terms, tokens(right["text"]))
                right_neg = bool(re.search(r"\b(no|not|never|cannot|without)\b", right["text"].lower()))
                if overlap >= 0.35 and left_neg != right_neg:
                    tensions.append({
                        "claim_a": left["claim_id"], "claim_b": right["claim_id"],
                        "reason": "high lexical overlap with opposing negation",
                        "status": "candidate_needs_semantic_review",
                    })
        return {"contradictions": [], "tensions": tensions}

    if stage_id == "07_dynamics":
        station = Path(__file__).resolve().parents[2] / "nabla"
        try:
            import sys
            sys.path.insert(0, str(station))
            import dynamics_probe
            import semantic_proposer
            proposal = semantic_proposer.propose(text)
            return {
                "semantic_vector": proposal["semantic_vector"],
                "semantic_vector_string": proposal["semantic_vector_string"],
                "factor_mentions": proposal["factor_mentions"],
                "dg7": dynamics_probe.probe(text),
                "veto_status": proposal["veto_status"],
                "possible_veto_flags": proposal["possible_veto_flags"],
            }
        except Exception as exc:
            return {
                "semantic_vector": {}, "dg7": {}, "veto_status": "UNRESOLVED",
                "error": str(exc),
            }

    if stage_id == "08_natural_process_mirror":
        process_terms = (
            "process", "sequence", "stage", "derivation", "restoration",
            "collapse", "decay", "growth", "transition", "cycle",
            "mapping", "isomorphism", "bridge", "coherence",
        )
        natural_terms = (
            "physics", "biology", "chemistry", "cosmology", "thermodynamic",
            "entropy", "cell", "evolution", "population", "information",
            "channel", "phase transition", "decoherence",
        )
        rows = []
        questions = []
        for claim in claims:
            lower = claim["text"].lower()
            if not any(term in lower for term in process_terms):
                continue
            has_natural_hint = any(term in lower for term in natural_terms)
            if has_natural_hint:
                natural_domain = lexical_domain(claim["text"])
                rows.append({
                    "claim_id": claim["claim_id"],
                    "source_process": claim["text"],
                    "natural_domain": natural_domain if natural_domain != "unknown" else "unknown",
                    "natural_process": "Natural anchor mentioned by source; stage map not adjudicated.",
                    "part_count_source": 0,
                    "part_count_mirror": 0,
                    "ordered_stage_map": [],
                    "directionality": "unknown",
                    "functionality_match": "unknown",
                    "mapping_type": "partial",
                    "constraints_preserved": [],
                    "failure_modes_preserved": [],
                    "lost": [],
                    "introduced": [],
                    "test_needed": [
                        "Decompose source process into ordered stages.",
                        "Decompose natural candidate into ordered stages.",
                        "Check same direction and same function for each stage.",
                    ],
                    "status": "needs_receipt",
                })
            else:
                questions.append(
                    f"Find an endogenous natural process mirror for claim {claim['claim_id']}: {claim['text']}"
                )
        if rows:
            gate = "PARTIAL"
        elif questions:
            gate = "NEEDS_NATURAL_ANCHOR"
        else:
            gate = "UNRESOLVED"
            questions.append("No load-bearing process mirror candidate was found by the lexical fallback.")
        return {
            "natural_process_mirrors": rows[:12],
            "unresolved_natural_process_questions": questions[:12],
            "mirror_gate_status": gate,
        }

    if stage_id == "09_synthesis":
        unresolved = []
        requirements = prior.get("05_evidence", {}).get("evidence_requirements", [])
        if requirements:
            unresolved.append(f"{len(requirements)} claim-level evidence requirement sets remain unresolved.")
        if prior.get("07_dynamics", {}).get("veto_status") != "ADJUDICATED":
            unresolved.append("Nabla veto is not semantically adjudicated.")
        mirror_gate = prior.get("08_natural_process_mirror", {}).get("mirror_gate_status")
        if mirror_gate and mirror_gate != "PASSED_CANDIDATE":
            unresolved.append(f"Natural process mirror gate remains {mirror_gate}.")
        return {
            "summary": (
                f"The local lane extracted {len(claims)} Candidate claims and applied all "
                "nine stages. Its outputs nominate review targets; they do not establish truth."
            ),
            "strongest_points": [
                "Exact source quotations are retained.",
                "Claims, evidence requirements, tests, dynamics, and natural mirrors remain separate.",
            ],
            "weakest_points": [
                "Lexical inference may miss paraphrase, scope, and implied dependencies.",
                "No independent external evidence was gathered in this pass.",
            ],
            "unresolved": unresolved,
            "recommended_next_actions": [
                "Compare field-level output with the independent API lane.",
                "Human-review material disagreements and all load-bearing claims.",
            ],
        }
    raise KeyError(stage_id)


def extract_json(text: str) -> dict[str, Any]:
    clean = text.strip()
    fence = chr(96) * 3
    if clean.startswith(fence):
        clean = re.sub(r"^" + fence + r"(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*" + fence + r"$", "", clean)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        start, end = clean.find("{"), clean.rfind("}")
        if start >= 0 and end > start:
            return json.loads(clean[start:end + 1])
        raise


def call_api(provider: str, prompt: str,
             runtime: dict[str, Any]) -> tuple[str, str]:
    cfg = runtime["api"]
    if provider == "deepseek":
        key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
        if not key:
            raise RuntimeError("DEEPSEEK_API_KEY is not set")
        model = cfg["deepseek_model"]
        url = "https://api.deepseek.com/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": cfg["temperature"],
            "max_tokens": cfg["max_tokens_per_stage"],
            "response_format": {"type": "json_object"},
        }
    elif provider == "openai":
        key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        model = cfg["openai_model"]
        url = "https://api.openai.com/v1/responses"
        payload = {
            "model": model,
            "input": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_output_tokens": cfg["max_tokens_per_stage"],
        }
    else:
        raise ValueError(f"Unsupported API provider: {provider}")

    request = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=240) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{provider} HTTP {exc.code}: {detail}") from exc
    if provider == "deepseek":
        return body["choices"][0]["message"]["content"], model
    if body.get("output_text"):
        return body["output_text"], model
    parts = []
    for item in body.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    return "\n".join(parts), model


def api_prompt(packet: dict[str, Any], stage: dict[str, Any],
               prior: dict[str, Any], runtime: dict[str, Any]) -> str:
    source = packet["source"]["text"]
    limit = runtime["api"]["max_source_chars"]
    if len(source) > limit:
        half = limit // 2
        source = source[:half] + "\n[TRUNCATED WITH RECEIPT]\n" + source[-half:]
    shape = empty_for(stage["id"])
    return f"""Run exactly one stage of the shared Atlas comparison process.

Stage id: {stage['id']}
Stage title: {stage['title']}
Instruction: {stage['instruction']}
Required top-level keys in data: {json.dumps(stage['required_keys'])}
Item-level contract: {json.dumps(stage.get('item_contract', {}), ensure_ascii=False)}

Return this envelope:
{{
  "data": {json.dumps(shape, ensure_ascii=False)},
  "refusals": [string],
  "limits": [string]
}}

Earlier outputs from this lane only:
{json.dumps(prior, ensure_ascii=False)}

Immutable source:
filename: {packet['source']['filename']}
sha256: {packet['source']['sha256']}
---
{source}
---"""


def run_lane(packet: dict[str, Any], contract: dict[str, Any],
             runtime: dict[str, Any], lane: str,
             provider: str | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    validate_packet(packet, contract)
    raw_responses: dict[str, str] = {}
    prior: dict[str, Any] = {}
    semantic_service = False
    if lane == "local_nlp":
        semantic_service = service_available(
            runtime["local_nlp"]["health_url"],
            runtime["local_nlp"]["timeout_seconds"],
        )
        backend = "local_nlp_service" if semantic_service else "deterministic_lexical_fallback"
    elif lane == "external_api":
        provider = provider or runtime["api"]["default_provider"]
        backend = provider
    else:
        raise ValueError(f"Unknown lane: {lane}")

    run = {
        "schema_version": "atlas-method-run/v1",
        "run_id": f"{lane}:{packet['packet_id']}:{now()}",
        "created_at": now(),
        "lane": lane,
        "backend": backend,
        "provider": provider if lane == "external_api" else None,
        "packet_id": packet["packet_id"],
        "packet_sha256": packet["packet_sha256"],
        "source_sha256": packet["source"]["sha256"],
        "contract_sha256": packet["contract"]["sha256"],
        "independent_input_rule": "No output from the other lane was available during this run.",
        "stages": [],
        "status": "running",
    }

    for stage in contract["stages"]:
        started = now()
        refusals: list[str] = []
        limits: list[str] = []
        try:
            if lane == "local_nlp":
                data = local_stage(
                    stage["id"], packet["source"]["text"], prior,
                    runtime, semantic_service,
                )
                data = normalize_api_stage(stage["id"], data)
                if not semantic_service:
                    limits.append(
                        "Local semantic service unavailable; deterministic lexical fallback used."
                    )
            else:
                prompt = api_prompt(packet, stage, prior, runtime)
                raw, model = call_api(str(provider), prompt, runtime)
                raw_responses[stage["id"]] = raw
                parsed = extract_json(raw)
                data = normalize_api_stage(stage["id"], parsed.get("data", parsed))
                refusals = parsed.get("refusals", [])
                limits = parsed.get("limits", [])
                if not isinstance(refusals, list):
                    refusals = [str(refusals)]
                if not isinstance(limits, list):
                    limits = [str(limits)]
                backend = f"{provider}:{model}"
            errors = validate_stage(stage, data)
            stage_status = "complete" if not errors else "invalid"
        except Exception as exc:
            data = empty_for(stage["id"])
            errors = [str(exc)]
            stage_status = "failed"
            refusals.append("Stage failed; empty contract-compliant object emitted.")
        prior[stage["id"]] = data
        run["stages"].append({
            "stage_id": stage["id"],
            "title": stage["title"],
            "status": stage_status,
            "started_at": started,
            "finished_at": now(),
            "data": data,
            "refusals": refusals,
            "limits": limits,
            "errors": errors,
            "data_sha256": sha256_bytes(canonical_bytes(data)),
        })

    run["backend"] = backend
    failed = [stage for stage in run["stages"] if stage["status"] != "complete"]
    run["status"] = "complete" if not failed else "complete_with_stage_failures"
    run["finished_at"] = now()
    run["run_sha256"] = sha256_bytes(canonical_bytes(run))
    return run, raw_responses


def flatten_scalars(value: Any, prefix: str = "") -> dict[str, str]:
    rows: dict[str, str] = {}
    if isinstance(value, dict):
        for key in sorted(value):
            child = f"{prefix}.{key}" if prefix else str(key)
            rows.update(flatten_scalars(value[key], child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            rows.update(flatten_scalars(item, f"{prefix}[{index}]"))
        if not value:
            rows[prefix] = "[]"
    else:
        rows[prefix] = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return rows


def key_paths(value: Any, prefix: str = "") -> set[str]:
    paths = set()
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{prefix}.{key}" if prefix else str(key)
            paths.add(child)
            paths |= key_paths(item, child)
    elif isinstance(value, list):
        paths.add(prefix + "[]")
        for item in value:
            paths |= key_paths(item, prefix + "[]")
    return paths


def claim_alignment(left: dict[str, Any], right: dict[str, Any]) -> tuple[dict[str, str], dict[str, str], dict[str, Any]]:
    left_rows = left.get("claims", [])
    right_rows = right.get("claims", [])
    candidates = []
    for li, lrow in enumerate(left_rows):
        for ri, rrow in enumerate(right_rows):
            score = jaccard(tokens(str(lrow.get("text", ""))), tokens(str(rrow.get("text", ""))))
            if score >= 0.35:
                candidates.append((score, li, ri))
    used_left, used_right, matches = set(), set(), []
    for score, li, ri in sorted(candidates, reverse=True):
        if li in used_left or ri in used_right:
            continue
        used_left.add(li)
        used_right.add(ri)
        matches.append((score, li, ri))
    left_map, right_map = {}, {}
    for index, (score, li, ri) in enumerate(matches, 1):
        label = f"aligned_claim:{index:03d}"
        left_map[str(left_rows[li].get("claim_id", ""))] = label
        right_map[str(right_rows[ri].get("claim_id", ""))] = label
    for index, row in enumerate(left_rows):
        claim_id = str(row.get("claim_id", ""))
        left_map.setdefault(claim_id, f"local_only_claim:{index:03d}")
    for index, row in enumerate(right_rows):
        claim_id = str(row.get("claim_id", ""))
        right_map.setdefault(claim_id, f"api_only_claim:{index:03d}")
    denominator = max(len(left_rows), len(right_rows), 1)
    coverage = len(matches) / denominator
    mean_similarity = sum(row[0] for row in matches) / len(matches) if matches else 0.0
    return left_map, right_map, {
        "local_claim_count": len(left_rows),
        "api_claim_count": len(right_rows),
        "matched_claim_count": len(matches),
        "matched_coverage": round(coverage, 4),
        "mean_matched_similarity": round(mean_similarity, 4),
        "alignment_score": round((coverage + mean_similarity) / 2, 4),
    }


def canonicalize_for_comparison(value: Any, id_map: dict[str, str]) -> Any:
    if isinstance(value, str):
        return id_map.get(value, value)
    if isinstance(value, dict):
        return {
            key: canonicalize_for_comparison(item, id_map)
            for key, item in sorted(value.items())
        }
    if isinstance(value, list):
        items = [canonicalize_for_comparison(item, id_map) for item in value]
        return sorted(items, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=False))
    return value


def compare_runs(left: dict[str, Any], right: dict[str, Any],
                 contract: dict[str, Any],
                 runtime: dict[str, Any]) -> dict[str, Any]:
    identity_fields = ("packet_sha256", "source_sha256", "contract_sha256")
    mismatched = [
        field for field in identity_fields if left.get(field) != right.get(field)
    ]
    if mismatched:
        raise ValueError(f"Runs are not comparable; identity mismatch: {mismatched}")

    left_stages = {stage["stage_id"]: stage for stage in left["stages"]}
    right_stages = {stage["stage_id"]: stage for stage in right["stages"]}
    left_map, right_map, claims_metric = claim_alignment(
        left_stages["01_claims"]["data"], right_stages["01_claims"]["data"]
    )
    cfg = runtime["comparison"]
    rows = []
    for stage in contract["stages"]:
        stage_id = stage["id"]
        a = canonicalize_for_comparison(left_stages[stage_id]["data"], left_map)
        b = canonicalize_for_comparison(right_stages[stage_id]["data"], right_map)
        a_keys, b_keys = key_paths(a), key_paths(b)
        structural = jaccard(a_keys, b_keys)
        af, bf = flatten_scalars(a), flatten_scalars(b)
        common = sorted(set(af) & set(bf))
        exact = (
            sum(af[key] == bf[key] for key in common) / len(common)
            if common else 1.0
        )
        content = jaccard(
            tokens(json.dumps(a, ensure_ascii=False)),
            tokens(json.dumps(b, ensure_ascii=False)),
        )
        score = (
            cfg["structural_weight"] * structural
            + cfg["field_weight"] * exact
            + cfg["content_weight"] * content
        )
        if stage_id == "01_claims":
            score = 0.70 * score + 0.30 * claims_metric["alignment_score"]
        divergences = [
            {"path": key, "local_nlp": af[key], "external_api": bf[key]}
            for key in common if af[key] != bf[key]
        ][:30]
        rows.append({
            "stage_id": stage_id,
            "structural_agreement": round(structural, 4),
            "exact_field_agreement": round(exact, 4),
            "content_token_agreement": round(content, 4),
            "weighted_agreement": round(score, 4),
            "claim_alignment": claims_metric if stage_id == "01_claims" else None,
            "divergences": divergences,
            "local_only_paths": sorted(set(af) - set(bf))[:30],
            "api_only_paths": sorted(set(bf) - set(af))[:30],
        })

    overall = sum(row["weighted_agreement"] for row in rows) / len(rows)
    if overall >= cfg["high_agreement"]:
        band = "HIGH_PROCESS_AGREEMENT"
    elif overall >= cfg["moderate_agreement"]:
        band = "MODERATE_PROCESS_AGREEMENT"
    else:
        band = "LOW_PROCESS_AGREEMENT"
    material = [
        row["stage_id"] for row in rows
        if row["weighted_agreement"] < cfg["moderate_agreement"]
    ]
    report = {
        "schema_version": "atlas-method-comparison/v1",
        "comparison_id": f"comparison:{left['source_sha256'][:16]}:{now()}",
        "created_at": now(),
        "source_sha256": left["source_sha256"],
        "packet_sha256": left["packet_sha256"],
        "contract_sha256": left["contract_sha256"],
        "lanes": {
            "local_nlp": {
                "run_id": left["run_id"],
                "backend": left["backend"],
                "status": left["status"],
            },
            "external_api": {
                "run_id": right["run_id"],
                "backend": right["backend"],
                "status": right["status"],
            },
        },
        "overall_agreement": round(overall, 4),
        "agreement_band": band,
        "material_divergence_stages": material,
        "claim_alignment": claims_metric,
        "stages": rows,
        "boundary": [
            "Agreement measures process-output similarity, not truth.",
            "Independent evidence and human or formal audit are still required for promotion.",
            "A lexical fallback is not equivalent to a semantic NLP model even when fields match.",
        ],
    }
    report["comparison_sha256"] = sha256_bytes(canonical_bytes(report))
    return report
