#!/usr/bin/env python3
"""SQLite persistence for AtlasRecord v1, shaped for a later D1 port.

The same ``db/schema.sql`` runs here (local SQLite) and against Cloudflare D1
in deployment, so the relational shape is validated locally before any cloud
round-trip. See ``docs/d1-architecture.md`` for the storage boundary.

Design rules honored here (all mirror README "Repository Boundaries"):

* The full canonical record JSON is authoritative. Child tables are a
  rebuilt-on-write projection for querying, never a second source of truth.
* ``native_grade`` and ``evidence_grade`` are stored as separate columns.
* ``candidate_or_admitted`` is persisted verbatim from the record audit block.
  The store never promotes a Candidate.
* Originals are not stored here. ``documents.r2_object_key`` references R2.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "db" / "schema.sql"


class AtlasStore:
    """A thin, dependency-free SQLite store for AtlasRecord v1.

    Usage::

        with AtlasStore("workbench.db") as store:
            store.save_record(record, run_id=None)
            record = store.get_record(record_id)
    """

    def __init__(self, db_path: str | Path = ":memory:") -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._apply_schema()

    # -- lifecycle ---------------------------------------------------------

    def _apply_schema(self) -> None:
        self.conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "AtlasStore":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # -- documents ---------------------------------------------------------

    def save_document(
        self,
        document_id: str,
        title: str,
        kind: str,
        content_hash: str,
        *,
        mime_type: str | None = None,
        r2_object_key: str | None = None,
        byte_size: int | None = None,
        ingestion_status: str = "frozen",
        timestamp: str = "",
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO documents (document_id, title, kind, mime_type, content_hash,
                r2_object_key, byte_size, ingestion_status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                title=excluded.title, kind=excluded.kind, mime_type=excluded.mime_type,
                content_hash=excluded.content_hash, r2_object_key=excluded.r2_object_key,
                byte_size=excluded.byte_size, ingestion_status=excluded.ingestion_status,
                updated_at=excluded.updated_at
            """,
            (document_id, title, kind, mime_type, content_hash, r2_object_key,
             byte_size, ingestion_status, timestamp, timestamp),
        )
        self.conn.commit()

    # -- runs --------------------------------------------------------------

    def save_run(
        self,
        run_id: str,
        *,
        document_id: str | None = None,
        provider: str | None = None,
        local_only: bool = False,
        status: str | None = None,
        source_hash: str | None = None,
        contract_hash: str | None = None,
        manifest: dict[str, Any] | None = None,
        timestamp: str = "",
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO runs (run_id, document_id, provider, local_only, status,
                source_hash, contract_hash, manifest_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                status=excluded.status, manifest_json=excluded.manifest_json
            """,
            (run_id, document_id, provider, 1 if local_only else 0, status,
             source_hash, contract_hash,
             json.dumps(manifest, ensure_ascii=False) if manifest is not None else None,
             timestamp),
        )
        self.conn.commit()

    # -- records -----------------------------------------------------------

    def save_record(
        self,
        record: dict[str, Any],
        *,
        document_id: str | None = None,
        run_id: str | None = None,
        timestamp: str = "",
    ) -> str:
        """Persist the canonical record and rebuild its projection.

        Returns the record_id. Idempotent per record_id: an existing record and
        its projected children are replaced wholesale so the projection can
        never drift from the JSON.
        """
        record_id = record["id"]["record_id"]
        p15 = record.get("periodic15", {})
        rm = record.get("reality_mirror", {})
        audit = record.get("audit", {})

        # Clearing children first keeps the projection an exact function of the
        # current JSON (ON DELETE CASCADE handles the child rows).
        self.conn.execute("DELETE FROM atlas_records WHERE record_id = ?", (record_id,))
        self.conn.execute(
            """
            INSERT INTO atlas_records (record_id, stable_uid, atom_id, source_claim_id,
                title, document_id, native_grade, evidence_grade, candidate_or_admitted,
                reality_mirror_class, reality_mirror_status, schema_version, record_json,
                run_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record_id,
                record["id"].get("stable_uid"),
                record["id"].get("atom_id"),
                record["id"].get("source_claim_id"),
                record.get("source", {}).get("title"),
                document_id,
                p15.get("marker_10_native_grade"),
                p15.get("marker_12_evidence_grade"),
                audit.get("candidate_or_admitted", "Candidate"),
                rm.get("class"),
                rm.get("status"),
                record.get("schema_version", "atlas-record/v1"),
                json.dumps(record, ensure_ascii=False),
                run_id,
                timestamp,
                timestamp,
            ),
        )
        self._project_children(record_id, record)
        self.conn.commit()
        return record_id

    def _project_children(self, record_id: str, record: dict[str, Any]) -> None:
        stack = record.get("atom_stack", {})

        atom = stack.get("atom") or {}
        if atom.get("atom_id"):
            self.conn.execute(
                "INSERT OR REPLACE INTO atoms (atom_id, record_id, title, object_type, standing, native_grade) VALUES (?, ?, ?, ?, ?, ?)",
                (atom["atom_id"], record_id, atom.get("title"), atom.get("object_type"),
                 atom.get("standing"), atom.get("native_grade")),
            )

        self._insert_many(
            "INSERT OR REPLACE INTO claims (claim_id, record_id, text, mode, mode_native, standing, native_grade) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ((c["claim_id"], record_id, c.get("text"), c.get("mode"), c.get("mode_native"),
              c.get("standing"), c.get("native_grade")) for c in stack.get("claims", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO components (component_id, record_id, type, label, standing) VALUES (?, ?, ?, ?, ?)",
            ((c["component_id"], record_id, c.get("type"), c.get("label"), c.get("standing"))
             for c in stack.get("components", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO evidence (evidence_id, record_id, claim_id, component_id, relation, strength, coverage, statement, source) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ((e["evidence_id"], record_id, e.get("claim_id"), e.get("component_id"),
              e.get("relation"), e.get("strength"), e.get("coverage"), e.get("statement"),
              e.get("source")) for e in record.get("evidence_receipts", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO tests (test_id, record_id, claim_id, type, condition, status) VALUES (?, ?, ?, ?, ?, ?)",
            ((t["test_id"], record_id, t.get("claim_id"), t.get("type"), t.get("condition"),
              t.get("status")) for t in stack.get("tests", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO edges (edge_id, record_id, from_node, relation, to_node, status, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ((e["edge_id"], record_id, e.get("from"), e.get("relation"), e.get("to"),
              e.get("status"), e.get("source")) for e in record.get("edges", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO bridges (bridge_id, record_id, target, mapping_type, standing, forbidden) VALUES (?, ?, ?, ?, ?, ?)",
            ((b["bridge_id"], record_id, b.get("target"), b.get("mapping_type"),
              b.get("standing"), b.get("forbidden")) for b in record.get("bridges", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO anchors (anchor_id, record_id, class, status, target_id, limitations) VALUES (?, ?, ?, ?, ?, ?)",
            ((a["anchor_id"], record_id, a.get("class"), a.get("status"), a.get("target_id"),
              a.get("limitations")) for a in record.get("anchors", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO source_spans (span_id, document_id, record_id, path, selector, quote) VALUES (?, ?, ?, ?, ?, ?)",
            ((s["span_id"], None, record_id, s.get("path"), s.get("selector"), s.get("quote"))
             for s in record.get("source", {}).get("source_spans", [])),
        )
        self._insert_many(
            "INSERT OR REPLACE INTO resolution_issues (issue_id, record_id, field_or_requirement, reason, next_step) VALUES (?, ?, ?, ?, ?)",
            ((f"{record_id}:unresolved:{i}", record_id, u.get("field_or_requirement"),
              u.get("reason"), u.get("next_step")) for i, u in enumerate(record.get("unresolved", []))),
        )

    def _insert_many(self, sql: str, rows: Iterable[tuple]) -> None:
        self.conn.executemany(sql, list(rows))

    # -- read --------------------------------------------------------------

    def get_record(self, record_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT record_json FROM atlas_records WHERE record_id = ?", (record_id,)
        ).fetchone()
        return json.loads(row["record_json"]) if row else None

    def list_records(
        self,
        *,
        document_id: str | None = None,
        state: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Return lightweight record summaries for the browse views."""
        clauses, params = [], []
        if document_id is not None:
            clauses.append("document_id = ?")
            params.append(document_id)
        if state is not None:
            clauses.append("candidate_or_admitted = ?")
            params.append(state)
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        params.append(limit)
        rows = self.conn.execute(
            f"""
            SELECT record_id, title, atom_id, native_grade, evidence_grade,
                   candidate_or_admitted, reality_mirror_class, reality_mirror_status,
                   document_id, updated_at
            FROM atlas_records{where}
            ORDER BY updated_at DESC, record_id
            LIMIT ?
            """,
            params,
        ).fetchall()
        return [dict(r) for r in rows]

    def link_series(self, record_id: str, series_id: str, position: int | None = None) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO series_membership (record_id, series_id, position) VALUES (?, ?, ?)",
            (record_id, series_id, position),
        )
        self.conn.commit()
