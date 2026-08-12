# Full Atlas Intake API

`method_comparison/scripts/run_atlas_full_intake.py` is the one-call DeepSeek
intake for a frozen document. It is an integration rail, not a new truth or
classification system.

It retains one candidate object graph and projects it through the existing
`AtlasRecord v1` envelope. The contract explicitly includes Nabla routing,
Periodic-15, Atom Stack, H/P/A/N lane states, Dynamics-7,
Ascent/Translation/Descent, bridge manifests, Resonance versus Phi, and
Reality Mirror.

The call never admits a claim. Lean, human audit, independent NLP, and external
anchors remain `not_run` unless a separate receipt is attached.

```text
python method_comparison/scripts/run_atlas_full_intake.py \
  --source path/to/source.md \
  --output output/atlas-record.json \
  --receipt output/full-intake-receipt.json \
  --raw-output output/full-intake.raw.txt
```

The API records normalized claims, source assertions, and kill conditions in
the existing SQLite claim ledger. Its retained receipt is the canonical source
for future deterministic projections.
