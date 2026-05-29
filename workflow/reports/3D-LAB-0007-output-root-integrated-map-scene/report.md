# 3D-LAB-0007 Output Root Integrated Map Scene

## Summary

`scripts/compile_integrated_map_scene_v0.py` now accepts `--output-root` and redirects its integrated scene outputs under `<output-root>/goal/...`. It also accepts `--no-regenerate-downstream`, which prevents the integrated compiler from silently invoking generated dependency compilers when required generated fixtures are missing.

The temp validation run wrote the terrain-side integrated scene outputs under `/tmp/gameguy_3d_lab_0007_integrated_map_scene` and then stopped at the expected building graph variation fixture blocker.

## Source Changes

- Added CLI parsing for `--output-root` and `--no-regenerate-downstream`.
- Centralized output path configuration so compiled maps, stage directories, reports, and receipts can be recomputed from either the repo root or a temp output root.
- Redirected child terrain compiler report and receipt paths through the configured output root.
- Added fail-closed guards for missing source template and missing building graph variation fixture when downstream regeneration is disabled.
- Added temporary downstream module root overrides so child compilers can format temp output paths without crashing on `Path.relative_to(ROOT)`.
- Preserved default repo output paths when no CLI arguments are supplied.

## Validation Result

Command:

```sh
python3 scripts/compile_integrated_map_scene_v0.py --output-root /tmp/gameguy_3d_lab_0007_integrated_map_scene --no-regenerate-downstream
```

Result: `blocked_missing_downstream_fixture`

Expected blocker:

```text
goal/architecture/building_graph_variation_rules_v0/building_graph_variation_rules_v0.json
```

This is the correct behavior for this work order because the compiler must not invoke downstream generation that can dirty the repo while output-root support has not yet been added to that dependency chain.

## Temp Outputs

- Temp files written: 14
- Temp JSON files: 10
- Temp JSON validation: pass
- Repo `goal/` files written: 0
- Repo goal dirtying prevented: true

Terrain-side summary from the temp outputs:

- cell_count: 1024
- top_triangle_count: 12288
- cracked_seam_count: 0
- road_count: 2
- building_plot_count: 3
- hazard_count: 1
- asset_socket_count: 7

## Not Run

- Blender was not run.
- No renders, screenshots, meshes, or media were generated.
- No archive, staging, commit, or push was performed.
- The old Mac prototype repo was not touched.

## Next Safest Task

Add the same output-root and no-regenerate handling to the building graph dependency path used by `compile_building_graph_variation_rules_v0.py`, or add an explicit source fixture input to `compile_integrated_map_scene_v0.py` so integrated validation can complete without generating repo-local goal outputs.
