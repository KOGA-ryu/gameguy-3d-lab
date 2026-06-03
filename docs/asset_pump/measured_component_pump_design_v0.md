# Measured Component Pump Design v0

## Purpose
Define how measured component recipes map into `gameguy_asset_v0`.

This covers source records that contain:

```text
dimensions_m
bounds_m
sockets
semantic_roles
proof_primitives
source_measurement_refs
geometry_terms_used
profile_terms
operations
```

The pump should translate those fields into deterministic asset geometry JSON. It should not create Blender files, renders, receipts, or repo-local generated folders.

## Core Mapping
Measured component recipes are source records. `gameguy_asset_v0` is the generated asset record.

| Source Field | `gameguy_asset_v0` Field | Rule |
| --- | --- | --- |
| `asset_id` | `asset_id` | Preserve exactly. Do not rename silently. |
| `dimensions_m` | `dimensions_m` | Authoritative intended width/depth/height. |
| `bounds_m` | `bounds_m` | Authoritative local bounds when present. |
| `semantic_roles` | `semantic_tags` | Preserve as gameplay/building meaning. |
| `sockets` | `connectors` | Convert placement/attachment plugs into connector records. |
| `proof_primitives` | `mesh.parts[]`, `mesh.vertices`, `mesh.faces` | V0 blockout geometry source. |
| `source_measurement_refs` | `source_refs` | Preserve measurement/proportion provenance. |
| `geometry_terms_used` | `source_terms.geometry` | Preserve dictionary terms used by recipe. |
| `profile_terms` | `source_terms.profiles` | Preserve profile vocabulary. |
| `operations` | `source_terms.operators` | Preserve intended operator vocabulary. |
| `validation_expectations` | `validation_expectations` | Preserve source acceptance rules. |
| `no_claims` | `no_claims` | Preserve non-production/non-structural flags. |

## `dimensions_m`
`dimensions_m` controls intended footprint and placement scale.

Rules:
- `width`, `depth`, and `height` must be positive finite numbers.
- If `bounds_m` exists, bounds span must match `dimensions_m`.
- If `bounds_m` is absent, bounds are derived from proof primitive geometry.
- If generated proof primitive bounds do not match source dimensions, the pump must fail or emit an explicit validation warning.

Uses:
- asset placement footprint
- collision proxy dimensions
- connector sanity checks
- map/building fit checks
- generated manifest summaries

## `proof_primitives`
`proof_primitives` are V0 geometry instructions.

They are not final art and not historical proof. They are blockout mesh parts used when a full operator chain does not exist yet.

Supported v0 behavior:

| Primitive | Pump Behavior |
| --- | --- |
| `cube` | Emit box mesh from `location_m` and `dimensions_m`. |
| `cylinder` | Emit low-poly cylinder mesh from `location_m`, radius/diameter or dimensions, and segment count/default. |
| `curve` | Defer unless the record provides enough path/profile data to sweep a tube or strip. |

Rules:
- Every proof primitive becomes a named mesh part.
- Mesh parts are merged into final `mesh.vertices` and `mesh.faces`.
- `material_role` is preserved as metadata, not render material.
- Primitive bounds must be nonzero.
- Primitive geometry must fit inside `bounds_m` unless the recipe explicitly marks it as an exterior attachment or overhang.

Generated part shape:

```json
{
  "part_id": "pathway_slab_unit",
  "source_primitive": "cube",
  "material_role": "walkable",
  "vertex_range": [0, 7],
  "face_range": [0, 5]
}
```

## `sockets`
Sockets become connectors.

Source socket:

```json
{
  "socket_id": "start_join",
  "connector_term": "south",
  "position_m": [0.0, -0.6, 0.09],
  "direction": [0.0, -1.0, 0.0],
  "role": "connector_join"
}
```

Generated connector:

```json
{
  "connector_id": "start_join",
  "connector_term": "south",
  "position_m": [0.0, -0.6, 0.09],
  "direction": [0.0, -1.0, 0.0],
  "role": "connector_join"
}
```

Rules:
- `socket_id` is stable and preserved.
- `position_m` is local-space meters.
- `direction` must be normalized.
- `connector_term` must exist in `geometry_dictionary/connectors`.
- Socket position should be inside or on bounds unless explicitly exterior.
- The pump must not invent missing sockets for measured components.

Uses:
- building graph plugs
- map graph attachment
- pathway joins
- rail/bridge repeats
- floor/ceiling anchoring

## `semantic_roles`
`semantic_roles` maps directly to `semantic_tags`.

Rules:
- Preserve source roles.
- Resolve known roles against `geometry_dictionary/semantic`.
- Unknown roles must be rejected or recorded as unresolved.
- Do not infer AI behavior correctness from semantic names.

Examples:

```text
walkable -> route/floor/path candidate
blocked -> obstruction/collision proxy
connector -> graph/link asset
rail -> barrier/edge asset
support -> support-looking role, not structural claim
```

## Generated `gameguy_asset_v0` Shape

```json
{
  "schema": "gameguy_asset_v0",
  "asset_id": "measured_pathway_slab_unit_v1",
  "source_schema": "connector_asset_component_recipe_v0",
  "asset_kind": "measured_component",
  "dimensions_m": { "width": 1.4, "depth": 1.2, "height": 0.18 },
  "bounds_m": { "min": [-0.7, -0.6, 0.0], "max": [0.7, 0.6, 0.18] },
  "semantic_tags": ["walkable", "connector", "flat_pathway"],
  "connectors": [],
  "mesh": {
    "coordinate_space": "local_xyz_m",
    "parts": [],
    "vertices": [],
    "faces": []
  },
  "source_refs": [],
  "source_terms": {
    "geometry": [],
    "profiles": [],
    "operators": []
  },
  "validation_expectations": {},
  "no_claims": {}
}
```

## Build Readiness Gate
A measured component can be pumped when:

- `dimensions_m` has positive `width`, `depth`, and `height`.
- `bounds_m` exists or can be derived from proof primitives.
- `semantic_roles` is non-empty.
- `proof_primitives` is non-empty unless a real operator chain exists.
- Required connector assets expose sockets.
- Every connector term and semantic term is known or explicitly unresolved.
- No production, structural, fabrication, historical accuracy, or approval claims are made.

## Deferred
Do not solve these in this design note:

- final render materials
- historical ornament detail
- real Blender object creation
- glTF export
- boolean-heavy cutouts
- curve sweep for underspecified `curve` primitives
- physics/collision engine integration

V0 should produce useful blockout asset geometry first.
