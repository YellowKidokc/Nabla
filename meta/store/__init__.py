"""D1-shaped local persistence for the Consilience Atlas Workbench.

The store owns durability only. It never classifies claims, promotes Candidate
to Admitted, computes a native grade, or admits bridges. It persists the
canonical AtlasRecord v1 JSON and projects a denormalized copy for browsing.
"""

from meta.store.atlas_store import AtlasStore

__all__ = ["AtlasStore"]
