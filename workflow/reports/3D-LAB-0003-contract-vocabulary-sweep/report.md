# 3D-LAB-0003: Contract Vocabulary Sweep

## Result

Reviewed the primary contract set and scanned remaining active root contracts, excluding `contracts/quarantine_2d_mosaic_v0/`.

Edited three active contracts:

- `contracts/cube_math_shape_recipe_v0.json`
- `contracts/plot_shape_taxonomy_v0.json`
- `contracts/map_authoring_contract_v0.json`

No contracts were quarantined.

## Terms Renamed

`cube_math_shape_recipe_v0.json`:

- `ornament_generation_uses` -> `architectural_detail_generation_uses`
- `ornament_anchors` -> `facade_detail_anchors`
- `ornamental_panel` -> `architectural_detail_panel`
- `ornament_object_cube` -> `detail_object_cube`
- `ornament_panel_generation` -> `architectural_detail_panel_generation`
- `*_debug_png` slice outputs -> `*_diagnostic`
- `slice_contact_sheet_png` -> `slice_diagnostic_summary`
- `cube zoo specimen` -> `cube-volume recipe`

`plot_shape_taxonomy_v0.json`:

- `tileability` -> `repeatability`
- `ornament_anchors` -> `facade_detail_anchors`
- `ornament_generation_uses` -> `architectural_detail_generation_uses`
- `animation_relevance` -> `deformation_relevance`
- `animation_or_motion_uses` -> `deformation_uses`

`map_authoring_contract_v0.json`:

- `map_authoring_contract_v0_to_tiled_style_template_v0` -> `map_authoring_contract_v0_to_grid_style_template_v0`

## Terms Kept

Kept `2D profiles` / `profile_points_2d` in `asset_mill_solid_recipe_v0.json` because they describe 2D cross-section profiles used to create 3D solids, not the 2D Pattern Lab.

Kept `pattern_lab_2d` and `mosaic_tile_outputs` where they appear only as explicit exclusion/boundary rules in the narrowed workflow contracts.

Kept the quarantine README wording that says 2D/mosaic contracts are excluded from active contracts.

## Deferred Terms

No active contract terms were deferred in this pass.

## Validation

Commands run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
python3 -m json.tool workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/vocabulary_decision_matrix.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0003-contract-vocabulary-sweep/receipt.json >/dev/null
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

Result: PASS for JSON validation, report JSON validation, and Python compile. The path/media scans printed no matching files.

## Non-Goals Respected

- Did not touch the old Mac prototype repo.
- Did not edit quarantined 2D/mosaic contracts.
- Did not run Blender.
- Did not generate assets, maps, renders, meshes, screenshots, or proof outputs.
- Did not stage, commit, or push.

## Next Recommended Task

Proceed to `3D-LAB-0004`: add a source-only connector validator that checks the connector manifest, connector recipes, and placement policy without generating outputs.
