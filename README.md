# Nabla

Nabla is a source-preserving semantic proposal engine and an independent
local-NLP/API comparison workflow for the Consilience Atlas.

It separates two objects that share letters but not meanings:

- Nabla semantic address: G M E S T K R Q F C
- Master Equation factors: G M E S T K Q R F, wrapped by C_W

Semantic density is never converted into a Master Equation measurement.
Lexical absence never adjudicates a veto.

## What Is Included

The nabla folder contains the deterministic semantic core, ten-dimension
proposer, DG7 probe, nine-factor wrapper guard, and station runner.

The method_comparison folder contains the immutable packet builder, shared
eight-stage contract, isolated local and API lanes, comparator, and receipts.

The meta folder is the canonical orchestration facade. It provides typed atom
objects, independent API and local-NLP adapters, AtlasRecord v1 rails, the
Periodic 15 projection, Candidate/Admitted graph separation, and one command
entrypoint. The gold folder holds frozen comparison specimens, while templates
contains the Atlas workbench.

The atom_package folder is a provenance-preserving, squashed Git subtree of
[Faith-through-physics-atoms](https://github.com/YellowKidokc/Faith-through-physics-atoms),
imported from branch `OBS-Plugin-Final-Claude` at commit `2aa7387`. It remains
the native atom data layer; `meta/` adapts it without rewriting its meanings.

The `gui/` folder is the local React Workbench. It is a Candidate sandbox for
loading outside papers, running the existing independent semantic lanes, seeing
comparison receipts, opening Gold-001, and recording a separate human review.
The GUI renders receipts; it does not itself classify, grade, admit, or create
bridges.

## Shared Process

1. Claim extraction
2. Claim classification
3. Dependency and load-bearing analysis
4. Falsification and kill conditions
5. Evidence and warrant mapping
6. Contradiction and tension scan
7. Nabla and DG7 dynamics
8. Page-level synthesis

Both lanes receive the same source and contract hashes. Each lane sees only its
own prior stages. Comparison happens after both runs are complete.

Agreement measures process-output similarity. It is not truth, proof, native
grade, evidence grade, or admission.

## Quick Start

Run tests:

    python -m unittest discover -s tests -v

Run the Nabla station:

    python nabla/pipeline.py

Build and validate the Master Equation AtlasRecord specimen:

    python -m meta.pipeline

Place Markdown or text inputs in nabla/_inbox. Results are written to
nabla/_outbox.

Run the local comparison lane without external calls:

    python method_comparison/scripts/run_comparison.py --source paper.md --skip-api

Run a full comparison:

    python method_comparison/scripts/run_comparison.py --source paper.md --provider deepseek

Set DEEPSEEK_API_KEY or OPENAI_API_KEY before using an external provider. The
local semantic service defaults to http://localhost:8700; when unavailable,
the receipt explicitly identifies the deterministic lexical fallback.

### Local GUI

Start the Python orchestration bridge from the repository root:

    python -m meta.workbench_server

Then start the React UI:

    cd gui
    npm install
    npm run dev

Open http://localhost:5173. The Vite dev server proxies `/api` to the local
Python bridge on port 8765. See `gui/README.md` for the current capability and
trust-boundary notes.

### Persistence (D1-shaped)

Candidate AtlasRecords can be saved to a local SQLite mirror that shares its
schema (`db/schema.sql`) with the Cloudflare D1 deployment target. The bridge
exposes `POST /api/records`, `GET /api/records`, and
`GET /api/records/{record_id}`. The local database lives at
`meta/_state/workbench.db` (git-ignored) and is migrated automatically. Saving
is durability only; it never promotes a Candidate to Admitted. See
`docs/d1-architecture.md` for the storage boundary and the Cloudflare
sequencing (`wrangler.toml`).

## Repository Boundaries

- Native grade and meta score are separate values.
- Candidate and Admitted graphs are separate states.
- Reality Mirror is top-level metadata, not Periodic Marker 16.
- Paper, Series, and Global views aggregate atom stacks; they do not reinterpret
  atom claims from scratch.
- API and local-NLP lanes receive the same frozen source and are compared only
  after independent execution. Agreement is not proof or admission.
- Secrets are read only from environment variables. No `.env` file is committed.

Refresh the Atom subtree after reviewing the source branch:

    git fetch atom-source OBS-Plugin-Final-Claude
    git subtree pull --prefix=atom_package atom-source OBS-Plugin-Final-Claude --squash
