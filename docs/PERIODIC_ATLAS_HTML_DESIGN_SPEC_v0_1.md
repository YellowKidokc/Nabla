# Periodic Atlas HTML Design Spec v0.1

## Governing Rule

**Same core markers, richer aggregation.** One visual grammar serves Local Atom,
Paper, Series, Cross-Series Phi, and Global. Cross-Series Phi is an operation,
not a storage resolution. Templates render canonical records and deterministic
projections; they do not classify, grade, or create bridges.

## Identity And Orientation

Every displayed object shows a permanent opaque UUID, registry-backed semantic
code, and editable human label. The Nabla address is a compact routing and
orientation band, never proof or standing. Show source hash, current Atlas
state, publication state, version, and last-computed time.

## Periodic-15

1. Identity
2. Home Domain
3. Native Domains
4. Bridged Domains (admitted only)
5. Object Type
6. Claim Family
7. Function Kind
8. Source
9. Commitment
10. Standing
11. Dispute
12. Evidence Grade (computed)
13. Usage / Runs (computed)
14. Graph Degree (computed)
15. Alert State (computed)

Markers 12-15 must visibly read as computed/registry-backed. Candidate states
use a distinct treatment from registered/admitted states. Open Items and
Anomalies remain distinct: an open item is known unresolved work; an anomaly is
not yet classifiable.

### Implementation Status

This is the intended UI contract. The current `atlas_record.schema.json` still
uses earlier names for markers 9-15 (`standing`, `native_grade`, `modality`,
`evidence_grade`, `dispute`, publication/component state). That contract drift
needs an explicit schema ruling before the production UI treats this version as
fully frozen. Do not silently map or rename values in the renderer.

## Workbench Shell

One workbench shell provides resolution and view selectors:

```text
Resolution: Local | Paper | Series | Global | Resonance
View: Periodic | Dependency | Warrant | Dynamics | Orientation |
      Bridges | Reality Mirror | Evolution | Blast | Topology | Phi
```

The selected object remains fixed while the view changes. The default detailed
view is dependency-first: `Upstream -> Selected Object -> Downstream`. A side
rail provides receipts, open items, alerts, and computed graph signature.

## Atom Stack

The tile is a front door, not the data. Pills are compressed addresses to the
same canonical object at every map entry point. Hover gives orientation; click
opens the atom dossier with claim, source spans, scope, assumptions, evidence,
proof/tests, counterevidence, kill conditions, dependencies, warrant,
Dynamics-7, bridge/anchor state, and H/P/A/N receipts.

Warrant must separately display evidence strength, evidence coverage,
independence, native grade, normalized grade, dispute, and open items.

## Dynamics And Orientation

Dynamics shows seven questions: coherence, degradation, measurement, threshold,
asymmetry, restoration, counterexample. Restoration presents `self` and
`external` subrows.

Orientation is three independently auditable lanes:

```text
Ascent | Translation | Descent
```

Translation exposes `PRESERVED`, `LOST`, `INTRODUCED`, and `FORBIDDEN`.
Meeting state is `CONVERGED`, `PRESSURE`, `PREDICTED_NOT_OBSERVED`,
`UNRESOLVED`, or `CONTRADICTED`. Only preserved structure may carry
argumentative load. Never draw one uninterrupted arrow from evidence to
framework.

## Bridges And Reality Mirror

Bridge panels disclose direction, lifecycle, preserved/lost/introduced/forbidden
manifest, independence, negative controls, and ablation. Candidate bridges stay
out of Marker 04.

Reality Mirror is top-level, not Marker 16. Display class `N`, `F`, `H`, `T`,
or `None`; anchor status; provenance; externality; native-domain warrant;
load-bearing path; closed-loop warning; and identification state. Internal
coherence is not external constraint, and external requirement is not a specific
theological identification.

## Resolution Rules

Paper aggregates atoms, Series aggregates papers, and Global aggregates series
and admitted cross-series structure. Higher levels retain identities, source
spans, unresolved component details, publication snapshot, and living Atlas
projection. Aggregation may not hide unsupported components or silently change
marker meaning.

Phi comparison begins with candidate discovery, then blind native manifests,
bridge manifests, directionality, controls, ablation, independence, and a
bridge-lifecycle verdict. Resonance is discovery; Phi adjudicates. A score is
never a truth label.

## Visual And Machine Boundary

Candidate and Admitted graphs must be visibly switchable and never silently
merged. Publication snapshot and Current Atlas are separate modes. Templates may
change appearance, layout, density, animation, and graph implementation, but may
not change identity semantics, Periodic-15 meaning/order, candidate/admitted
semantics, evidence ownership, bridge lifecycle, Reality Mirror classes, or
provenance visibility.

Rendered elements should carry stable attributes such as `data-object-id`,
`data-uuid`, `data-semantic-code`, `data-resolution`, `data-marker`,
`data-origin`, `data-admission-state`, `data-source-span-id`,
`data-computed-by`, and `data-run-id`. Canonical JSON and ledger objects remain
the source of truth.
