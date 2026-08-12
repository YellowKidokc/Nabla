"""
pipeline.py - nabla-chi-classifier.station
Theophysics Research Initiative | POF 2828 | SSS_v1

Thin wiring only. The work lives in:
    nabla_engine.py            existing deterministic core (UNCHANGED)
    semantic_proposer.py       NEW - reads text, proposes semantics
    dynamics_probe.py          NEW - DG7 seven-question dynamics extraction
    master_equation_types.py   NEW - canonical nine/wrapper type separation

This station proposes. It does not rule, and it does not compute chi.
"""
# ============================================================
# 00 IMPORTS
# ============================================================
from __future__ import annotations

import hashlib
import json
import logging
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))

import dynamics_probe
import nabla_engine
import semantic_proposer

# ============================================================
# 01 CONSTANTS
# ============================================================
STATION_ID = "nabla-chi-classifier"
STATION_NAME = "Nabla-Chi Classifier"
STATION_DESC = "Semantic proposer + DG7 dynamics probe over the Nabla deterministic core."
STATION_VERSION = "1.1.0"

HERE = Path(__file__).resolve().parent
STATIONS = HERE.parent
BRAIN = STATIONS.parent


def _resolve(numbered: str, flat: str) -> Path:
    p = BRAIN / numbered
    return p if p.is_dir() else BRAIN / flat


MODELS = _resolve("05_MODELS", "models")
TEMPLATES = _resolve("15_TEMPLATES", "templates")

INBOX, OUTBOX = HERE / "_inbox", HERE / "_outbox"
PROCESSED, LOGS, STATE = HERE / "_processed", HERE / "_logs", HERE / "_state"

# ============================================================
# 02 CONFIG
# ============================================================
DEFAULTS = {
    "extensions": [".md", ".markdown", ".txt"],
    "source_globs": [],
    "min_words": 40,
    "density_bands": {"1": 0.4, "2": 1.2, "3": 3.0},
    "evidence_per_family": 2,
    "context_chars": 160,
    "archive_inputs": False,
}


def load_config() -> dict:
    cfg = dict(DEFAULTS)
    p = HERE / "config.json"
    if p.exists():
        try:
            cfg.update(json.loads(p.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"[warn] config.json unreadable ({exc}); using defaults")
    return cfg


# ============================================================
# 03 LOGGING
# ============================================================
def setup_logging() -> logging.Logger:
    LOGS.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger(STATION_ID)
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")
    fh = logging.FileHandler(LOGS / f"{STATION_ID}_{datetime.now():%Y%m%d}.log", encoding="utf-8")
    ch = logging.StreamHandler(sys.stdout)
    fh.setFormatter(fmt)
    ch.setFormatter(fmt)
    log.addHandler(fh)
    log.addHandler(ch)
    return log


# ============================================================
# 04 INGEST
# ============================================================
def ingest(cfg: dict, log: logging.Logger) -> List[Path]:
    files: List[Path] = []
    exts = {e.lower() for e in cfg["extensions"]}
    for pattern in cfg.get("source_globs", []):
        pat = Path(pattern)
        root, glob = (pat.parent, pat.name) if pat.name else (pat, "*")
        if root.is_dir():
            files.extend(f for f in root.glob(glob) if f.is_file())
        else:
            log.warning("source_glob root missing: %s", root)
    if INBOX.is_dir():
        files.extend(f for f in INBOX.rglob("*") if f.is_file())
    seen, out = set(), []
    for f in files:
        if f.suffix.lower() not in exts:
            continue
        k = str(f.resolve()).lower()
        if k not in seen:
            seen.add(k)
            out.append(f)
    log.info("ingest: %d file(s)", len(out))
    return sorted(out)


# ============================================================
# 05 VALIDATE
# ============================================================
def validate(path: Path, cfg: dict, log: logging.Logger) -> Optional[dict]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8", errors="replace")
    except Exception as exc:
        log.error("unreadable: %s (%s)", path.name, exc)
        return None
    words = len(re.findall(r"\b\w+\b", text))
    if words < cfg["min_words"]:
        log.warning("skip (%d words): %s", words, path.name)
        return None
    title = path.stem
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
            break
    return {"path": path, "text": text, "words": words, "title": title,
            "sha256": hashlib.sha256(raw).hexdigest()}


# ============================================================
# 06 NLP_ROUTE
# ============================================================
def route_nlp(cfg: dict, log: logging.Logger):
    """Tier 1 (lexical) is always on, stdlib only. Tier 2 (M02_embedder) would
    rerank evidence spans; not wired yet - absence degrades precision only."""
    return None


# ============================================================
# 07 PROCESS
# ============================================================
def process(doc: dict, cfg: dict, log: logging.Logger) -> dict:
    log.info("probe: %s (%d words)", doc["path"].name, doc["words"])
    proposal = semantic_proposer.propose(doc["text"], bands=cfg["density_bands"])
    dg7 = dynamics_probe.probe(doc["text"],
                               evidence_per_family=cfg["evidence_per_family"],
                               context_chars=cfg["context_chars"])
    vector = semantic_proposer.to_nabla_semantic_vector(proposal)
    vector_string = vector.to_string()
    pairing_hash = nabla_engine.build_hash(vector)
    semantic_address = (
        f"UNKNOWN/{doc['path'].stem}/U/UNKNOWN/I/R0 :: "
        f"{vector_string} :: {pairing_hash}"
    )
    routing_hints = [
        f"semantic_review:possible_veto:{key}"
        for key in proposal["possible_veto_flags"]
    ]
    routing_hints.extend(
        f"semantic_review:dg7_absent:{key}"
        for key, value in dg7["stored_fields"].items()
        if value["status"] == "ABSENT"
    )
    return {
        "schema": "nabla-chi/1.1",
        "station": {"id": STATION_ID, "version": STATION_VERSION},
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "identity": {"path": str(doc["path"]), "filename": doc["path"].name,
                     "title": doc["title"], "sha256": doc["sha256"], "words": doc["words"]},
        "nabla_proposal": proposal,
        "dg7": dg7,
        "classification": "NABLA_SEMANTIC_PROPOSAL",
        "semantic_address": semantic_address,
        "semantic_vector": proposal["semantic_vector"],
        "pairing_hash": pairing_hash,
        "routing_hints": routing_hints,
        "lane": {
            "is": "deterministic proposal",
            "is_not": "a ruling on truth, standing, applicability, or chi",
            "chi_computed": False,
            "chi_note": "This station never computes chi. See master_equation_types.py.",
        },
    }


# ============================================================
# 08 ARTIFACTS
# ============================================================
def write_artifact(record: dict, log: logging.Logger) -> Path:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(record["identity"]["filename"]).stem)
    out = OUTBOX / f"{stem}.nabla-dg7.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("artifact: %s", out.name)
    return out


def write_summary(records: List[dict], log: logging.Logger) -> Path:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    rows = [{
        "file": r["identity"]["filename"],
        "title": r["identity"]["title"],
        "semantic_vector": r["nabla_proposal"]["semantic_vector_string"],
        "possible_veto_flags": r["nabla_proposal"]["possible_veto_flags"],
        "veto_status": r["nabla_proposal"]["veto_status"],
        "dg7": {k: v["status"] for k, v in r["dg7"]["visible_questions"].items()},
        "restoration_split": {
            "self": r["dg7"]["stored_fields"]["restoration_self"]["status"],
            "external": r["dg7"]["stored_fields"]["restoration_external"]["status"],
        },
    } for r in records]
    out = OUTBOX / f"_SUMMARY_{datetime.now():%Y%m%d_%H%M%S}.json"
    out.write_text(json.dumps({"station": STATION_ID, "count": len(rows), "rows": rows},
                              indent=2, ensure_ascii=False), encoding="utf-8")
    log.info("summary: %s", out.name)
    return out


# ============================================================
# 09 WORKFLOW
# ============================================================
def update_workflow(records: List[dict], log: logging.Logger) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    (STATE / "last_run.json").write_text(json.dumps({
        "station": STATION_ID,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "processed": [r["identity"]["filename"] for r in records],
    }, indent=2), encoding="utf-8")


# ============================================================
# 10 HANDOFF
# ============================================================
def handoff(records: List[dict], log: logging.Logger) -> None:
    queue = []
    for r in records:
        f = r["identity"]["filename"]
        for slot, v in r["dg7"]["stored_fields"].items():
            if v["status"] == "ABSENT":
                queue.append({"file": f, "kind": "dg7_slot", "item": slot})
        for k in r["nabla_proposal"]["possible_veto_flags"]:
            queue.append({"file": f, "kind": "possible_veto", "item": k})
    if queue:
        OUTBOX.mkdir(parents=True, exist_ok=True)
        (OUTBOX / "_NEEDS_RULING.json").write_text(json.dumps(queue, indent=2), encoding="utf-8")
        log.info("handoff: %d item(s) need a semantic ruling", len(queue))


# ============================================================
# 11 ARCHIVE
# ============================================================
def archive(path: Path, cfg: dict, log: logging.Logger) -> None:
    if not cfg.get("archive_inputs"):
        return
    try:
        path.relative_to(INBOX)
    except ValueError:
        return  # never move files that live outside our inbox
    PROCESSED.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(PROCESSED / path.name))
    log.info("archived: %s", path.name)


# ============================================================
# 12 MAIN
# ============================================================
def main() -> int:
    cfg = load_config()
    log = setup_logging()
    log.info("=== %s v%s ===", STATION_NAME, STATION_VERSION)
    files = ingest(cfg, log)
    if not files:
        log.warning("nothing to do")
        return 0
    route_nlp(cfg, log)
    records = []
    for path in files:
        doc = validate(path, cfg, log)
        if doc is None:
            continue
        rec = process(doc, cfg, log)
        write_artifact(rec, log)
        records.append(rec)
        archive(path, cfg, log)
    if records:
        write_summary(records, log)
        update_workflow(records, log)
        handoff(records, log)
    log.info("done: %d/%d", len(records), len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
