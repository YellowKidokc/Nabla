# Architecture

## Trust Boundaries

The local and API lanes are intentionally independent:

    source + contract
      |-- local NLP adapter chain -- local receipt
      |-- external API chain ----- API receipt
      `-- comparator, after both receipts exist

Neither method sees or repairs the other answer before comparison.

Every stage must return its required fields. UNKNOWN, UNRESOLVED, and refusal
are valid outputs. Missing output is not silently synthesized as positive.

## Nabla and the Master Equation

Nabla semantic vectors are filing and routing proposals. Master Equation
factor vectors are separate normalized mathematical objects. Shared letters do
not authorize conversion.

The equation boundary is chi(X) = C_W[product of nine independently warranted
X_i values]. C_W is a wrapper, not a tenth factor.

## Periodic-15 Contract

The fifteen-marker contract is frozen by the Consilience Atlas Canonical
Architecture v0.3, section 9: keys `m01_identity` through `m15_alert_state`,
matching templates/atlas-workbench.html. Marker semantics never change across
resolutions; m12-m14 are computed markers and stay null until the
deterministic computation layer fills them. The retired `marker_N_*` names
and their pre-freeze semantics must not be reintroduced. See
docs/migrations/2026-08-12-periodic15-v0.3-contract.md.

## Promotion Boundary

Extracted claims, vectors, edges, evidence requirements, possible veto flags,
DG7 readings, and convergence scores remain Candidate. Promotion requires the
appropriate human, formal, runtime, or independent evidential receipt.
