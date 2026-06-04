# 3D-LAB-0076 Blender Tool Cards V0

## Goal

Fill the first practical Blender tool cards for the asset readiness lane.

## Added

- Base form tool cards:
  `mesh_from_pydata`, `extrude_faces`, `modifier_screw`
- Assembly tool cards:
  `modifier_boolean`, `modifier_array`, `modifier_mirror`
- Shape refinement tool cards:
  `inset_faces`, `modifier_bevel`, `modifier_weighted_normal`,
  `curve_bevel_profile`
- Curve, UV, and material tool cards:
  `curve_to_mesh`, `uv_cube_project`, `material_assign_by_part`
- Game proxy tool cards:
  `create_collision_proxy`, `create_lod_variant`
- A small JSON index tying each card back to the repo Blender tool dictionary.

## Files

- `docs/research/asset_readiness_system_v0/blender_tool_cards/README.md`
- `docs/research/asset_readiness_system_v0/blender_tool_cards/base_form_tool_cards_v0.md`
- `docs/research/asset_readiness_system_v0/blender_tool_cards/assembly_tool_cards_v0.md`
- `docs/research/asset_readiness_system_v0/blender_tool_cards/shape_refinement_tool_cards_v0.md`
- `docs/research/asset_readiness_system_v0/blender_tool_cards/curve_uv_material_tool_cards_v0.md`
- `docs/research/asset_readiness_system_v0/blender_tool_cards/game_proxy_tool_cards_v0.md`
- `docs/research/asset_readiness_system_v0/blender_tool_cards/tool_card_index_v0.json`
- `docs/research/asset_readiness_system_v0/README.md`
- `docs/research/asset_readiness_system_v0/blender_tool_fillout_queue_v0.md`

## Boundary

This is documentation and indexing only. It does not run Blender, execute tool
plans, fetch references, or write mesh/media outputs.

## Validation

```text
python3 -m json.tool workflow/reports/3D-LAB-0076-blender-tool-cards-v0/receipt.json
PASS

python3 -m json.tool docs/research/asset_readiness_system_v0/blender_tool_cards/tool_card_index_v0.json
PASS

python3 - <<'PY' ... compare tool_card_index_v0.json to blender_tool_dictionary_v0.json
PASS tool card index crosscheck: cards=15 source_tools=97

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=7 geometry_assets=44 source_profiles=19 source_asset_polish_plans=1 source_graphs=1 source_cell_selections=1 source_pattern_fields=1 source_pattern_segments=1 source_taxonomies=23 source_component_style_sheets=5 reference_only=3
```

## Recommended Next Goal

Use the per-asset workcard template to prepare one real railing component
handoff: primary reference, drawing guide, component anatomy, selected tool
cards, material roles, sockets, collision, LOD, and operator QA.
