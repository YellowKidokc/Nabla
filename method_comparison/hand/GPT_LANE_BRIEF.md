# GPT Hand-Classification Lane — Brief (v1, 2026-08-12)

You are one of two independent **hand-classification lanes** for the Consilience
Atlas atom corpus (Kimi is the other). The comparison contract requires that
lanes stay **blind to each other** until both runs are complete. Agreement is
measured afterward. Agreement is not truth, proof, evidence grade, or admission.

## Input

The attached file `packet-atoms-v1.json` (sha256 printed inside the file under
`packet_sha256`). It contains **505 atoms** from `atom_package/_ledger/atoms`
in YellowKidokc/Nabla. Each atom entry gives you: `atom_id`, `title`, `claim`,
`bridges`, `kill_conditions`.

**Deliberately withheld** (do not try to find them): each atom's existing
`claim_class`, `mode_classification`, `proof_label`, `domain`, and
`ontology_family`. Do not browse the Nabla repo, the atoms repo, or AI-CREW
deposits for answers. Judge the claim text itself.

## Task (per atom)

Assign:

- `mode` — exactly one of:
  AXIOM, PRE_ASSUMPTION, EMPIRICAL_EVENT, HISTORICAL_RECORD, MATHEMATICAL_PROOF,
  FORMAL_DERIVATION, CLASSIFICATION, INTERPRETATION, SYMBOLIC_TRUTH, MORAL_CLAIM,
  THEOLOGICAL_CLAIM, EXPERIENTIAL_REPORT, PREDICTION, UNKNOWN.
  **UNKNOWN is allowed and is an honest answer.** Do not force a mode.
- `domain` — the atom's native domain, lowercase-kebab (e.g. `axioms`,
  `master-equation`, `trinity`, `isomorphic-events`, `derivation-grammar`,
  `logos`, `ten-laws`, `physics`, `theology`, `christianity`, `consilience`,
  `proof-discipline`, `runtime`, `review`, `lagrangian`, `coherence-atlas`,
  `crown-canon`, `theophysics-method`). You may mint a new domain label if none
  fit — flag it in `basis`.
- `confidence` — 0..1.
- `basis` — one sentence, claim-level reason.

## Output

One JSON file, schema `atlas-method-run/v1`:

```json
{
  "schema_version": "atlas-method-run/v1",
  "run_id": "hand_gpt:hand-packet:atoms-505:<utc-timestamp>",
  "created_at": "<utc>",
  "lane": "hand_gpt",
  "backend": "<your exact model identity>",
  "packet_id": "hand-packet:atoms-505:2026-08-12",
  "packet_sha256": "<copy from packet>",
  "classifications": [
    {"atom_id": "...", "mode": "...", "domain": "...", "confidence": 0.0, "basis": "..."}
  ],
  "refusals": [],
  "notes": "anything you declined to force-classify"
}
```

Every atom_id in the packet must appear exactly once. A lane may return
UNKNOWN for mode but may not omit an atom.

## Return path

Give the finished JSON to David. Do not post it where other lanes can see it
before the comparison is run. David will hold it until Kimi's lane is complete;
then both go into the comparison together.

— Kimi (lane: hand_kimi), for the crew
