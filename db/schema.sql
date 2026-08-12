-- Consilience Atlas Workbench: canonical relational schema.
--
-- This single file is the source of truth for both lanes of persistence:
--   * Cloudflare D1 (serverless SQLite) in deployment.
--   * A local SQLite file during development.
--
-- The design boundary is deliberate and mirrors README "Repository Boundaries":
--   * D1 holds structured, queryable Atlas state only.
--   * Original artifacts (PDF, large HTML, exported bundles) live in R2. D1
--     stores only their object key, hash, and ingestion metadata. D1 row/BLOB
--     values are capped at 2 MB, so originals are never inlined here.
--   * Candidate and Admitted remain separate states (audit.candidate_or_admitted),
--     never collapsed by storage.
--   * Native grade and meta/evidence grade are stored as separate columns,
--     never reconciled into one score.
--
-- The full canonical AtlasRecord v1 JSON is stored verbatim in
-- atlas_records.record_json. The child tables below are a denormalized
-- projection for querying (browse by Local / Paper / Series / Global /
-- Resonance). The JSON blob is authoritative; the projection is rebuilt
-- from it on every save.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Originals and source freezing
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS documents (
    document_id      TEXT PRIMARY KEY,
    title            TEXT NOT NULL,
    kind             TEXT NOT NULL,              -- md | txt | html | pdf | json
    mime_type        TEXT,
    content_hash     TEXT NOT NULL,              -- sha256 of frozen source text
    r2_object_key    TEXT,                       -- key of the original in R2 (NULL if none)
    byte_size        INTEGER,
    ingestion_status TEXT NOT NULL DEFAULT 'frozen',  -- queued | extracting | frozen | failed
    created_at       TEXT NOT NULL,
    updated_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_spans (
    span_id     TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(document_id) ON DELETE CASCADE,
    record_id   TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    path        TEXT NOT NULL,
    selector    TEXT NOT NULL,
    quote       TEXT
);

-- ---------------------------------------------------------------------------
-- AtlasRecord v1 (canonical JSON + denormalized projection)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS atlas_records (
    record_id          TEXT PRIMARY KEY,
    stable_uid         TEXT,
    atom_id            TEXT,
    source_claim_id    TEXT,
    title              TEXT,
    document_id        TEXT REFERENCES documents(document_id) ON DELETE SET NULL,
    -- separate scores are stored as separate columns, never merged:
    native_grade       TEXT,                     -- periodic15.marker_10_native_grade
    evidence_grade     TEXT,                     -- periodic15.marker_12_evidence_grade
    -- Candidate vs Admitted is a first-class state, never inferred from presence:
    candidate_or_admitted TEXT NOT NULL DEFAULT 'Candidate',
    reality_mirror_class  TEXT,
    reality_mirror_status TEXT,
    schema_version     TEXT NOT NULL DEFAULT 'atlas-record/v1',
    record_json        TEXT NOT NULL,            -- full canonical AtlasRecord v1
    run_id             TEXT REFERENCES runs(run_id) ON DELETE SET NULL,
    created_at         TEXT NOT NULL,
    updated_at         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS atoms (
    atom_id      TEXT PRIMARY KEY,
    record_id    TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    title        TEXT,
    object_type  TEXT,
    standing     TEXT,
    native_grade TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id     TEXT PRIMARY KEY,
    record_id    TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    text         TEXT,
    mode         TEXT,
    mode_native  TEXT,
    standing     TEXT,
    native_grade TEXT
);

CREATE TABLE IF NOT EXISTS components (
    component_id TEXT PRIMARY KEY,
    record_id    TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    type         TEXT,
    label        TEXT,
    standing     TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id  TEXT PRIMARY KEY,
    record_id    TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    claim_id     TEXT,
    component_id TEXT,
    relation     TEXT,
    strength     TEXT,
    coverage     REAL,
    statement    TEXT,
    source       TEXT
);

CREATE TABLE IF NOT EXISTS tests (
    test_id   TEXT PRIMARY KEY,
    record_id TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    claim_id  TEXT,
    type      TEXT,
    condition TEXT,
    status    TEXT
);

CREATE TABLE IF NOT EXISTS edges (
    edge_id       TEXT PRIMARY KEY,
    record_id     TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    from_node     TEXT,
    relation      TEXT,
    to_node       TEXT,
    status        TEXT,
    source        TEXT
);

-- Phi bridges remain Candidate unless a receipt admits them; storage never
-- promotes them.
CREATE TABLE IF NOT EXISTS bridges (
    bridge_id    TEXT PRIMARY KEY,
    record_id    TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    target       TEXT,
    mapping_type TEXT,
    standing     TEXT,
    forbidden    TEXT
);

CREATE TABLE IF NOT EXISTS anchors (
    anchor_id   TEXT PRIMARY KEY,
    record_id   TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    class       TEXT,
    status      TEXT,
    target_id   TEXT,
    limitations TEXT
);

-- ---------------------------------------------------------------------------
-- Runs, resolution issues, series membership
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,
    document_id  TEXT REFERENCES documents(document_id) ON DELETE SET NULL,
    provider     TEXT,                           -- deepseek | openai | local
    local_only   INTEGER NOT NULL DEFAULT 0,
    status       TEXT,                           -- from method-comparison manifest
    source_hash  TEXT,
    contract_hash TEXT,
    manifest_json TEXT,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS resolution_issues (
    issue_id            TEXT PRIMARY KEY,
    record_id           TEXT REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    field_or_requirement TEXT NOT NULL,
    reason              TEXT,
    next_step           TEXT
);

CREATE TABLE IF NOT EXISTS series_membership (
    record_id  TEXT NOT NULL REFERENCES atlas_records(record_id) ON DELETE CASCADE,
    series_id  TEXT NOT NULL,
    position   INTEGER,
    PRIMARY KEY (record_id, series_id)
);

-- ---------------------------------------------------------------------------
-- Indexes for the browse views
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_records_document   ON atlas_records(document_id);
CREATE INDEX IF NOT EXISTS idx_records_state      ON atlas_records(candidate_or_admitted);
CREATE INDEX IF NOT EXISTS idx_records_atom       ON atlas_records(atom_id);
CREATE INDEX IF NOT EXISTS idx_claims_record      ON claims(record_id);
CREATE INDEX IF NOT EXISTS idx_components_record  ON components(record_id);
CREATE INDEX IF NOT EXISTS idx_evidence_record    ON evidence(record_id);
CREATE INDEX IF NOT EXISTS idx_edges_record       ON edges(record_id);
CREATE INDEX IF NOT EXISTS idx_bridges_record     ON bridges(record_id);
CREATE INDEX IF NOT EXISTS idx_spans_document     ON source_spans(document_id);
CREATE INDEX IF NOT EXISTS idx_series_series      ON series_membership(series_id);
