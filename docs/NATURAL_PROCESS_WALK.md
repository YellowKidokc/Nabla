# Natural Process Mirror Walk

This is the hand-walked complement to Stage 08. It does not ask an AI to
declare a natural correspondence. It records the questions a reviewer must
answer, one stage at a time, and computes a conservative candidate gate.

```text
python method_comparison/scripts/natural_process_walk.py \
  --source-process "named source process" \
  --source-stages source-stages.txt \
  --output walk.json
```

Fill the generated `walk.json`, then evaluate it:

```text
python method_comparison/scripts/natural_process_walk.py \
  --input walk.json --output evaluated-walk.json
```

`PASSED_CANDIDATE` requires every source part to be mapped in the same order,
direction, and function, plus an external anchor and a negative control,
ablation, or rival explanation. It is still not an admitted bridge or an
isomorphism claim.
