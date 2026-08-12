"""SQLite receipt ledger for method-comparison and foundation API runs."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "state" / "claims_ledger.sqlite"


def connect(path: Path = DEFAULT_LEDGER) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS api_runs (
          run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, provider TEXT,
          model TEXT, packet_id TEXT, source_sha256 TEXT, status TEXT NOT NULL,
          receipt_json TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS api_claims (
          run_id TEXT NOT NULL, claim_id TEXT NOT NULL, stage_id TEXT NOT NULL,
          text TEXT NOT NULL, source_quote TEXT, mode TEXT, domain TEXT,
          standing TEXT, payload_json TEXT NOT NULL,
          PRIMARY KEY (run_id, claim_id, stage_id),
          FOREIGN KEY (run_id) REFERENCES api_runs(run_id)
        );
        CREATE TABLE IF NOT EXISTS api_evidence (
          run_id TEXT NOT NULL, claim_id TEXT, stage_id TEXT NOT NULL,
          source_quote TEXT, relation TEXT, requirement_json TEXT,
          payload_json TEXT NOT NULL,
          FOREIGN KEY (run_id) REFERENCES api_runs(run_id)
        );
        CREATE TABLE IF NOT EXISTS api_tests (
          run_id TEXT NOT NULL, claim_id TEXT, stage_id TEXT NOT NULL,
          condition TEXT, status TEXT, payload_json TEXT NOT NULL,
          FOREIGN KEY (run_id) REFERENCES api_runs(run_id)
        );
    """)
    return connection


def record_method_run(run: dict[str, Any], path: Path = DEFAULT_LEDGER) -> dict[str, Any]:
    """Persist every emitted claim, evidence row, and test from one API run."""
    stages = {stage.get("stage_id"): stage.get("data", {}) for stage in run.get("stages", [])}
    classifications = {
        row.get("claim_id"): row
        for row in stages.get("02_classification", {}).get("claim_assessments", [])
    }
    connection = connect(path)
    try:
        connection.execute(
            "INSERT OR REPLACE INTO api_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run.get("run_id"), run.get("created_at"), run.get("provider"), run.get("backend"),
             run.get("packet_id"), run.get("source_sha256"), run.get("status"),
             json.dumps(run, ensure_ascii=False, sort_keys=True)),
        )
        for claim in stages.get("01_claims", {}).get("claims", []):
            claim_id = claim.get("claim_id", "UNKNOWN")
            assessment = classifications.get(claim_id, {})
            connection.execute(
                "INSERT OR REPLACE INTO api_claims VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (run.get("run_id"), claim_id, "01_claims", claim.get("text", ""),
                 claim.get("source_quote", ""), assessment.get("mode"), assessment.get("domain"),
                 assessment.get("standing", claim.get("extraction_status", "candidate")),
                 json.dumps({"claim": claim, "classification": assessment}, ensure_ascii=False, sort_keys=True)),
            )
        evidence = stages.get("05_evidence", {})
        for row in evidence.get("source_support", []):
            connection.execute(
                "INSERT INTO api_evidence VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run.get("run_id"), row.get("claim_id"), "05_evidence", row.get("source_quote", ""),
                 row.get("relation", "source_asserts"), None,
                 json.dumps(row, ensure_ascii=False, sort_keys=True)),
            )
        for row in evidence.get("evidence_requirements", []):
            connection.execute(
                "INSERT INTO api_evidence VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run.get("run_id"), row.get("claim_id"), "05_evidence", None, "requirement",
                 json.dumps(row.get("required", []), ensure_ascii=False),
                 json.dumps(row, ensure_ascii=False, sort_keys=True)),
            )
        for row in stages.get("04_falsification", {}).get("tests", []):
            connection.execute(
                "INSERT INTO api_tests VALUES (?, ?, ?, ?, ?, ?)",
                (run.get("run_id"), row.get("claim_id"), "04_falsification", row.get("condition", ""),
                 row.get("status", "candidate_untested"), json.dumps(row, ensure_ascii=False, sort_keys=True)),
            )
        connection.commit()
        counts = {
            "claims": connection.execute("SELECT COUNT(*) FROM api_claims WHERE run_id = ?", (run.get("run_id"),)).fetchone()[0],
            "evidence": connection.execute("SELECT COUNT(*) FROM api_evidence WHERE run_id = ?", (run.get("run_id"),)).fetchone()[0],
            "tests": connection.execute("SELECT COUNT(*) FROM api_tests WHERE run_id = ?", (run.get("run_id"),)).fetchone()[0],
        }
    finally:
        connection.close()
    return {"path": str(path), **counts}
