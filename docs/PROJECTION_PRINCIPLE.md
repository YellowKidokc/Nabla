# Projection Principle

```text
Classify once -> store canonical objects and edges once -> compute -> project many ways.
```

Semantic lanes may propose primitive facts: object type, claim family, domain,
claim/evidence relation, dependency, contradiction, bridge candidate, Dynamics
interpretation, and external-anchor candidate. They do not classify whether an
object belongs in a Blast Radius, Proof, or Dispute view.

Those view memberships are deterministic projections of the canonical graph.
The same evidence edge can appear as a proof support, evidence flow, warrant
input, and blast-radius dependency without creating four edges or four copies
of its target object.

`meta/atlas/projections.py` is the first reusable implementation. It derives
view memberships and dependent blast radius from existing canonical edges.
Templates consume those projections and never create a second truth store.
