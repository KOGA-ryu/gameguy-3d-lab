# 3D-LAB-0005: No-Dirty Compiler Audit

## Result

Audited `39` matching scripts by static source inspection only. No output-writing compiler, create script, audit script, or validator was executed for this audit.

Reviewed patterns:

- `scripts/compile_*.py`
- `scripts/create_*.py`
- `scripts/audit_*.py`
- `scripts/validate_*.py`

Matrix:

- `workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/compiler_output_matrix.json`

## Summary

- Safe / keep: `4`
- Need `--output-root`: `29`
- Need read-only mode: `6`

Safe scripts:

- `scripts/compile_connector_asset_placement_v0.py`
- `scripts/validate_connector_source_v0.py`
- `scripts/validate_contract.py`
- `scripts/validate_dex_agent_profiles.py`

Scripts needing `--output-root`:

- `scripts/compile_architectural_modules_v0.py`
- `scripts/compile_architectural_proportion_ranges_v0.py`
- `scripts/compile_asset_mill_measured_components_v1.py`
- `scripts/compile_asset_mill_measured_components_v2.py`
- `scripts/compile_asset_mill_solids_v0.py`
- `scripts/compile_building_entrance_road_join_v0.py`
- `scripts/compile_building_graph_attachment_v0.py`
- `scripts/compile_building_graph_kit_expansion_v0.py`
- `scripts/compile_building_graph_variation_rules_v0.py`
- `scripts/compile_floor_plans_to_assemblies_v0.py`
- `scripts/compile_hex_plot_vertex_graph_v0.py`
- `scripts/compile_hex_terrain_fold_site_v0.py`
- `scripts/compile_hex_topology_site_v0.py`
- `scripts/compile_integrated_map_scene_v0.py`
- `scripts/compile_map_gameplay_surface_semantics_v0.py`
- `scripts/compile_map_template_profile_application_v0.py`
- `scripts/compile_map_template_shared_terrain_adapter_v0.py`
- `scripts/compile_map_template_v2_building_variant_placement.py`
- `scripts/compile_measured_asset_placement_v1.py`
- `scripts/compile_pathway_engine_v0.py`
- `scripts/compile_plug_based_connection_graph_v0.py`
- `scripts/compile_profile_aware_road_plot_refinement_v0.py`
- `scripts/compile_terrain_profile_bending_v0.py`
- `scripts/compile_tiled_map_template_v0.py`
- `scripts/compile_topology_sites_v0.py`
- `scripts/create_integrated_map_scene_v0.py`
- `scripts/create_measured_asset_aware_map_template_v1.py`
- `scripts/create_tiled_map_template_fixture_v0.py`
- `scripts/audit_hex_terrain_deformation_v0.py`

Scripts needing read-only mode:

- `scripts/validate_architectural_measurements_v0.py`
- `scripts/validate_floor_plans_v0.py`
- `scripts/validate_geometry_dictionary.py`
- `scripts/validate_map_authoring_contract_v0.py`
- `scripts/validate_measurement_fetch_packet_v1.py`
- `scripts/validate_topology_dictionary_v0.py`

## Top 5 Refactor Targets

1. `scripts/compile_integrated_map_scene_v0.py` - orchestration compiler imports and can trigger many downstream generated-output writes.
2. `scripts/create_measured_asset_aware_map_template_v1.py` - writes both source template data and generated goal outputs while importing multiple compilers.
3. `scripts/compile_tiled_map_template_v0.py` - early map compiler feeding several downstream generated fixtures.
4. `scripts/compile_hex_plot_vertex_graph_v0.py` - writes graph JSON, reports, and multiple receipts from generated folded-site inputs.
5. `scripts/compile_asset_mill_measured_components_v2.py` - current measured asset catalog compiler writes recipes, index, report, and receipt into fixed paths.

`compile_connector_asset_placement_v0.py` already supports `--output-root`, plus `--integrated-graph-path` and `--no-regenerate-integrated`, so it is classified as `KEEP_SAFE` when invoked with those options even though default invocation still writes canonical outputs.

## Validation

Commands run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
python3 -m json.tool workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/compiler_output_matrix.json >/dev/null
python3 -m json.tool workflow/reports/3D-LAB-0005-no-dirty-compiler-audit/receipt.json >/dev/null
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
find . -path './.git' -prune -o -path '*pattern_lab_2d*' -print
find . -path './.git' -prune -o -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
git status --short
```

Result: PASS for matrix JSON, receipt JSON, repo JSON, and Python compile. The path/media scans printed no matching files.

## Non-Goals Respected

- Did not edit compiler behavior.
- Did not run output-writing compilers.
- Did not run Blender.
- Did not generate assets, maps, renders, meshes, screenshots, or proof outputs.
- Did not touch the old Mac prototype repo.
- Did not stage, commit, or push.

## Next Recommended Task

Proceed to `3D-LAB-0006` and create the tiny canonical source fixture. After that, start output-root refactors with `compile_integrated_map_scene_v0.py` or the earlier map/terrain compilers it orchestrates.
