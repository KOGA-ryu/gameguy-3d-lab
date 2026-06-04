# Organization Plan V0

The imported taxonomy seeds should not be dumped into the architecture taxonomy.
They need their own normalized source lanes first.

## Proposed Repo Shape

```text
data/asset_taxonomy/imported_seeds_v0/        raw imported files
data/asset_taxonomy/normalized_domains_v0/    future normalized ledgers
docs/research/imported_asset_taxonomies_v0/   human triage and crosswalks
scripts/validate_asset_taxonomy_imports_v0.py future validator
```

## Promotion Order

1. Preserve raw seeds.
2. Summarize each imported domain.
3. Extract reusable shape vocabulary.
4. Map `shape_type`, `shape_vocab`, and `blender_proxy` phrases to existing
   geometry dictionary terms.
5. Map Blender proxy instructions to existing Blender tool cards.
6. Build per-domain normalized ledgers.
7. Promote only selected, stable terms into active recipe/tool-plan schemas.

## Domain Lanes

`character_body_proxy`

Use the human body seed for body landmarks, anatomy chunks, layers, render tiers,
and rig/socket vocabulary. This belongs near future character, mannequin, and
attachment workflows, not architecture assets.

`wearable_armor`

Use armor history and armor making seeds for armor families, historical shape
language, construction methods, materials, body anchors, and wearable-kit
generation.

`textile_clothing`

Use textile seed terms for stitches, seams, fabric panels, pattern pieces, cloth
shells, surface patterns, and material roles.

`workshop_props`

Use sewing equipment terms for prop assets, drafting tools, textile tools,
weaving equipment, measurement tools, and workshop dressing.

`drafting_ui_vocabulary`

Use pattern shapes, shape legends, stitching paths, seam lines, and equipment
shape types to improve the future drafting/drawing UI.

## Crosswalk Into Blender Tool Cards

| Imported Vocabulary | Likely Repo Tool Direction |
| --- | --- |
| `dome_shell`, helmet bowl, skull cap | `primitive_uv_sphere_add`, `modifier_solidify`, `modifier_bevel`, `modifier_weighted_normal` |
| `woven_sheet_grid`, cloth shell, fabric panel | `primitive_plane_add`, `mesh_from_pydata`, `uv_cube_project`, `material_assign_by_part`, procedural texture tools |
| stitch dashes, seam curves, thread, cord | `curve_bezier_add`, `curve_bevel_profile`, `modifier_array`, `material_assign_by_part` |
| blade mesh, scissor, cutter, awl point | `mesh_from_pydata`, `extrude_faces`, `modifier_bevel`, `modifier_weighted_normal` |
| ring, hoop, loop handle | `primitive_torus_add`, `curve_bevel_profile`, `modifier_screw` |
| armor plates and splints | `mesh_from_pydata`, `extrude_faces`, `modifier_array`, `modifier_boolean`, `modifier_bevel` |
| body landmark anchors | sockets/connectors, collision proxies, attachment anchors |

## First Useful Follow-Up

Build a normalized `shape_type_crosswalk_v0.json` that maps every imported
`shape_type`, `shape_vocab`, and `blender_proxy` phrase to:

```text
geometry_dictionary term
Blender tool card
source fields needed
asset families affected
promotion status
```

That crosswalk would make these imported taxonomies useful to the drafting UI
and Blender tool-plan compiler without making them active generation inputs too
early.

