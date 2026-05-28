# 3D-0008: Polish Connector Kit Source Lane

## Result

Source promotion was implemented.

The nine connector recipes under `mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0/recipes/` are useful source-like connector definitions, so they were copied into a deliberate source lane at:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0/
```

A transformed source manifest was created at:

```text
mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json
```

The old generated folder was left untouched. Generated report/index output remains in `goal/architecture/connector_asset_kit_v0/` and was not promoted as source.

## Decision Matrix

| Asset | Decision | Dimensions m | Semantic roles | Reason |
| --- | --- | --- | --- | --- |
| `measured_pathway_slab_unit_v1` | `PROMOTE_SOURCE` | 1.4 x 1.2 x 0.18 | walkable, connector, flat_pathway | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_threshold_landing_v1` | `PROMOTE_SOURCE` | 2.2 x 1.1 x 0.2 | walkable, connector, road_threshold | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_ramp_pathway_unit_v1` | `PROMOTE_SOURCE` | 1.4 x 1.2 x 0.18 | walkable, connector, ramp_pathway | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_stepped_pathway_unit_v1` | `PROMOTE_SOURCE` | 1.4 x 1.0 x 0.32 | walkable, connector, stepped_pathway | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_bridge_deck_unit_v1` | `PROMOTE_SOURCE` | 2.4 x 1.2 x 0.24 | walkable, connector, bridge_link | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_bridge_abutment_v1` | `PROMOTE_SOURCE` | 2.8 x 0.5 x 0.7 | support, connector, bridge_link | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_bridge_rail_unit_v1` | `PROMOTE_SOURCE` | 0.16 x 1.2 x 0.72 | rail, connector, bridge_link | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_retaining_wall_unit_v1` | `PROMOTE_SOURCE` | 1.2 x 0.28 x 0.75 | support, connector, retaining_edge | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |
| `measured_curb_edge_unit_v1` | `PROMOTE_SOURCE` | 0.18 x 1.2 x 0.16 | connector, curb_edge, walkable_edge | Useful deterministic connector source recipe with explicit dimensions, sockets, proof primitive, no silent scaling, and no-claim fields. |

## Source Lane Decision

- Recipes: `PROMOTE_SOURCE`
- Generated connector index: not promoted directly; transformed into `connector_asset_manifest_v0.json`
- Generated connector report: left in generated output lane
- Old generated goal folder: left untouched
- Dimensions: unchanged
- Blender renders/meshes: not created
- Engine/gameplay movement logic: unchanged

## Files Created

- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json`
- `mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0/*.json`
- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/report.md`
- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/connector_recipe_decision_matrix.json`
- `goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/receipt.json`

## Validation

Validation commands run:

```bash
cd /Users/kogaryu/game
find mosaic_dungeon_floor_v0/goal/architecture/connector_asset_kit_v0 -name '*.json' -print0 \
  | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile mosaic_dungeon_floor_v0/scripts/compile_connector_asset_placement_v0.py
python3 -m json.tool mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_manifest_v0.json >/dev/null
find mosaic_dungeon_floor_v0/data/architecture/assets/connectors/connector_asset_recipes_v0 -name '*.json' -print0 \
  | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/receipt.json >/dev/null
python3 -m json.tool goal/workflow/reports/3D-0008-polish-connector-kit-source-lane/connector_recipe_decision_matrix.json >/dev/null
```

Result: PASS.

## Remaining Risks

- The connector placement compiler still generates recipes into `goal/architecture/connector_asset_kit_v0/`; it does not yet consume the promoted source manifest.
- The promoted recipes keep their existing `local_asset_catalog` reference to the measured v1 generated index. That matches current source material, but a future source-lane pass should decide whether measured v1 recipes also need promotion.
- Some `semantic_roles` such as `connector`, `flat_pathway`, and `bridge_link` are connector-domain roles rather than geometry dictionary semantic terms. They are preserved as existing connector recipe roles, not added as geometry terms.

## Next Recommended Worker Task

Create a follow-up 3D task to refactor `scripts/compile_connector_asset_placement_v0.py` so connector recipe definitions are loaded from `data/architecture/assets/connectors/connector_asset_manifest_v0.json` instead of being embedded in `CONNECTOR_RECIPES`, while preserving current placement behavior and output paths.
