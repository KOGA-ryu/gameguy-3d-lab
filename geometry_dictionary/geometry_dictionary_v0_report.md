# Geometry Dictionary v0

Machine-readable geometry vocabulary for profile primitives, measurements, operations, connectors, semantic geometry, and validation terms.

The rule is strict: Asset Mill recipes may only use profile, operation, connector, and semantic terms that exist in this dictionary.

## Counts

| Category | Count |
| --- | ---: |
| `composition_operation` | 14 |
| `connector` | 16 |
| `measurement` | 10 |
| `mesh_operation` | 8 |
| `profile_primitive` | 12 |
| `semantic_geometry` | 12 |
| `transform` | 2 |
| `validation_term` | 6 |

Total terms: `80`

## Asset Mill Enforcement

- Checked recipe bundle: `data/architecture/asset_mill/recipes/simple_solids_v0.json`
- Validated profile primitive references.
- Validated operation references.
- Validated connector references.
- Validated semantic geometry tags.

## Purpose

- Codex cannot invent geometry words inside recipes.
- Blender scripts can look up each term and know expected params, outputs, and validation.
- Validators can reject fake geometry before it reaches generation.
