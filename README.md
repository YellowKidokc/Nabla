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

Place Markdown or text inputs in nabla/_inbox. Results are written to
nabla/_outbox.

Run the local comparison lane without external calls:

    python method_comparison/scripts/run_comparison.py --source paper.md --skip-api

Run a full comparison:

    python method_comparison/scripts/run_comparison.py --source paper.md --provider deepseek

Set DEEPSEEK_API_KEY or OPENAI_API_KEY before using an external provider. The
local semantic service defaults to http://localhost:8700; when unavailable,
the receipt explicitly identifies the deterministic lexical fallback.
