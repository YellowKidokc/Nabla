# D1 Workbench Architecture

This document defines the persistence and deployment boundary for the
Consilience Atlas Workbench. It is the plan behind `db/schema.sql`,
`meta/store/`, and `wrangler.toml`.

## Deployment shape

```text
React / Vite frontend
        v
Cloudflare Worker API
        v
choose provider  (DeepSeek / OpenAI / local)
        v
AtlasRecord adapter
        v
schema validation  (AtlasRecord v1)
        v
D1 database  (structured state)   +   R2  (originals)
        v
Workbench views  (Local / Paper / Series / Global / Resonance)
```

Cloudflare D1 is managed serverless SQLite. Because it *is* SQLite, the same
`db/schema.sql` runs locally and in D1, so the relational model is validated on
a laptop before any cloud round-trip.

## Storage boundary

Two stores, split on size and query need:

| Concern                                   | Store | Why |
| ----------------------------------------- | ----- | --- |
| Documents, spans, records, atoms, claims, components, evidence, tests, edges, bridges, anchors, runs, resolution issues, series | **D1** | Small, relational, queried by the browse views |
| Original PDFs, large HTML, exported JSON bundles | **R2** | D1 row/BLOB values cap at 2 MB; D1 databases cap at 500 MB (Free) / 10 GB (Paid) |

D1 stores only a reference to each original: `documents.r2_object_key`,
`content_hash`, `mime_type`, `title`, `ingestion_status`. Originals are never
inlined into D1.

## Record model

The canonical **AtlasRecord v1** JSON (see
`meta/schemas/atlas_record.schema.json`) is stored verbatim in
`atlas_records.record_json` and is authoritative. The child tables
(`claims`, `components`, `evidence`, `edges`, ...) are a denormalized
**projection** rebuilt from that JSON on every write, so they can never drift
from the record. Queries and browse views read the projection; anything that
needs the whole record reads the JSON.

Boundaries enforced by the schema and the store, mirroring README
"Repository Boundaries":

- **Native grade and evidence grade are separate columns**
  (`native_grade`, `evidence_grade`) — never merged into one score.
- **Candidate and Admitted are separate states** (`candidate_or_admitted`),
  persisted verbatim from the record's audit block. The store never promotes a
  Candidate; promotion stays a separate human/formal/evidential gate.
- **Reality Mirror is top-level metadata**
  (`reality_mirror_class`, `reality_mirror_status`), not a periodic marker.
- **Phi bridges** are stored with their `standing`; storage does not admit them.

## Local development

The local SQLite mirror lives at `meta/_state/workbench.db` (git-ignored) and is
created and migrated automatically by `meta.store.AtlasStore`, which executes
`db/schema.sql`. The local workbench server (`python -m gui.app`) exposes:

- `POST /api/records` — persist a Candidate AtlasRecord `{ "record": {...} }`
- `GET  /api/records` — list record summaries (`?document_id=` / `?state=`)
- `GET  /api/records/{record_id}` — fetch one full record

## Sequencing to Cloudflare

Deliberately incremental, so the ingestion logic and the cloud plumbing are
never debugged at the same time:

1. Run the local React workbench.
2. Feed it 10-15 real HTML / Markdown / TXT papers.
3. **Add D1-shaped SQLite persistence locally.** *(this change)*
4. Add a PDF extraction stage that freezes text and source positions before
   semantic analysis. (PDF is not yet treated as first-class; today the lanes
   handle Markdown / TXT / HTML / JSON.)
5. Apply `db/migrations` to a real D1 database, move originals to R2, and
   deploy the React frontend plus a thin Worker API. The Python rails remain the
   reference implementation and are ported to the Worker deliberately, reusing
   the same JSON schemas and deterministic rules.

## What does not change

The Worker port keeps the same AtlasRecord v1 contract, the same
Candidate/Admitted separation, and the same deterministic rules. Cloudflare
Workers do not run the local Python server verbatim; only the orchestration is
re-expressed in TypeScript, over identical schemas.
