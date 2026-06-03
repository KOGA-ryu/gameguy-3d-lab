# 3D-LAB-0048 Sacred Graph v0

## Result

Added the first source-owned sacred-geometry construction graph compiler.

```text
sacred graph recipe
-> radial rings and star-step edges
-> named selections
-> selected 22-star column outline profile
-> deterministic graph JSON
-> SVG construction preview
-> existing star_column_22_v0 remains the first 3D consumer
```

## Source Decisions

- `sacred_graph_v0` is a source layer, not an asset and not a Blender script.
- The graph compiler writes JSON and SVG previews under `/tmp`; it writes no repo-local generated media or mesh outputs.
- Version 0 uses deterministic Python math only: radial divisions, rings, radial edges, star-step edges, and a derived `star_polygon` profile.
- The first graph uses `22` radial divisions and four rings: `boss`, `inner_cell`, `shaft_valley`, and `outer_tip`.
- The first named selections are `center_boss_node`, `primary_radial_ribs`, `outer_star_step_5_trace`, and `column_star_outline`.
- `column_star_outline` matches the current section-stack star-column intent with `66` profile vertices.

## Compiled Graph

- Bundle: `data/architecture/sacred_geometry/sacred_graph_recipes_v0.json`
- Compiler: `scripts/compile_sacred_graph_v0.py`
- Operation term: `geometry_dictionary/operations/sacred_graph.json`
- Output graph: `/tmp/gameguy_sacred_graph_v0_0048/graphs/sacred_22_star_construction_graph_v0.json`
- SVG preview: `/tmp/gameguy_sacred_graph_v0_0048/svg/sacred_22_star_construction_graph_v0.svg`
- PNG preview: `/tmp/gameguy_sacred_graph_v0_0048_preview/sacred_22_star_construction_graph_v0.svg.png`
- Points: `89`
- Edges: `220`
- Selections: `4`
- Derived profiles: `1`

## Validation

```text
python3 scripts/compile_sacred_graph_v0.py --validate-only
compiled sacred graphs=1 out=<validate-only>

python3 scripts/compile_sacred_graph_v0.py --clean --out /tmp/gameguy_sacred_graph_v0_0048
compiled sacred graphs=1 points=89 edges=220 out=/tmp/gameguy_sacred_graph_v0_0048

python3 -m unittest discover -s tests
OK, 134 tests

python3 scripts/validate_asset_generation_registry_v0.py
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 source_graphs=1 reference_only=3

python3 scripts/validate_generation_pipeline_v0.py --json-report /tmp/gameguy_pipeline_0048_final.json
PASS generation pipeline validation: commands=35 json=245 include_blender=false

python3 scripts/validate_generation_pipeline_v0.py --include-blender --json-report /tmp/gameguy_pipeline_blender_0048_final.json
PASS generation pipeline validation: commands=49 json=245 include_blender=true
```

## Next

The next slice should add v0 cell selection from the graph: select closed wedges between rings, classify them as `vault_web_cell` candidates, and preview the cascade order before any Blender execution.
