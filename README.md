# gameguy-3d-lab

`gameguy-3d-lab` is a clean standalone lab for the 3D architecture, terrain, map graph, connector asset, and Blender proof-script lanes from the Mac prototype repo.

This repo is not the 2D Pattern Lab, not an ornament-generation repo, not a production asset pack, and not a game-engine integration layer. It keeps source-like 3D/shared data and prototype Python tooling in one smaller workspace so future 3D work does not have to carry the full historical prototype shape.

## Origin

Source origin:

- `/Users/kogaryu/game`
- `/Users/kogaryu/game/mosaic_dungeon_floor_v0`

The source repo remains the historical prototype/reference. This repo is a flattened working lane for continuing 3D architecture/map/building work.

## Current Scope

- 3D architecture source data under `data/architecture/`
- Geometry dictionary terms and validation inputs under `geometry_dictionary/`
- Shared contracts under `contracts/`
- Architectural measurement, map-generation, and terrain research notes under `docs/research/`
- 3D/map/building compiler, validator, and Blender proof scripts under `scripts/`
- Workflow packets and cleanup decisions under `workflow/`

2D Pattern Lab, ornament generation, 2D contact sheets, 2D media outputs, and proof render/mesh artifacts are intentionally excluded.

## Core Rebuild Direction

The durable core of this repo is:

```text
construction geometry taxonomy -> sacred construction graph -> selected subgraph/profile -> source asset recipe -> profile/operation compiler -> deterministic asset geometry JSON
```

The taxonomy layer gives the repo names for the user's core demand:

```text
dense construction field -> selection/omission -> role promotion -> lift/fold/sweep/thicken/bevel
```

The machine-readable taxonomy is `data/architecture/taxonomy/construction_geometry/construction_geometry_taxonomy_v0.json`; the design note is `docs/asset_pump/procedural_construction_geometry_taxonomy_v0.md`.

Validate it with:

```bash
python3 scripts/validate_construction_geometry_taxonomy_v0.py
```

The graph layer is source-only. It creates named 2D points, edges, rings, star traces, and profile selections before any asset pump or Blender adapter sees the shape:

```bash
python3 scripts/compile_sacred_graph_v0.py \
  --clean \
  --out /tmp/gameguy_sacred_graph_v0
```

The first graph bundle is `data/architecture/sacred_geometry/sacred_graph_recipes_v0.json`. It compiles `sacred_22_star_construction_graph_v0` into `89` named points, `220` named edges, an SVG construction preview, and named selections for the center boss, radial ribs, and primary star-step trace. It deliberately does not emit a derived column profile; this layer is now a clean construction field for later cell, rib, and vault selection.

Cell selection is now the next source layer. It consumes the compiled sacred graph, derives closed adjacent ring-band cells, and names selected cell groups before any 3D lifting or Blender execution:

```bash
python3 scripts/compile_construction_cell_selection_v0.py \
  --clean \
  --graph-manifest /tmp/gameguy_sacred_graph_v0/manifest.json \
  --out /tmp/gameguy_construction_cell_selection_v0
```

The first cell-selection bundle is `data/architecture/sacred_geometry/construction_cell_selection_recipes_v0.json`. It compiles `sacred_22_star_radial_cell_selection_v0` into `66` closed cells across `3` adjacent ring bands, with named selections for vault web cells, outer tracery opening cells, and railing recess panel cells.

Multi-center pattern fields are the source layer for hand-drawn rosette sheets like the user references:

```bash
python3 scripts/compile_pattern_field_v0.py \
  --clean \
  --out /tmp/gameguy_pattern_field_v0
```

The first pattern-field bundle is `data/architecture/sacred_geometry/pattern_field_recipes_v0.json`. It compiles `multi_rosette_pattern_field_v0` into repeated large and small rosette modules, guide circles, radial rays, ring segments, star traces, connector lines, and named selected edge groups. It is a construction drawing source, not a final ornament or mesh.

Pattern segment splitting turns the field into smaller selectable pieces by cutting linework at intersections:

```bash
python3 scripts/compile_pattern_segments_v0.py \
  --clean \
  --pattern-field-manifest /tmp/gameguy_pattern_field_v0/manifest.json \
  --out /tmp/gameguy_pattern_segments_v0
```

The first segment bundle is `data/architecture/sacred_geometry/pattern_segment_recipes_v0.json`. It splits `multi_rosette_pattern_field_v0` into candidate segments, preserves selected source-trace tags, and previews intersection points before omission rules or closed-loop extraction.

The first lean command is:

```bash
python3 scripts/asset_pump_v0.py --clean --out /tmp/gameguy_asset_pump_v0
```

It reads `data/architecture/asset_mill/recipes/simple_solids_v0.json` and writes a compact asset manifest plus per-asset geometry JSON. It does not write workflow reports, receipts, Blender files, renders, exported mesh files, or repo-local generated folders.

Measured components use the same pump contract:

```bash
python3 scripts/asset_pump_v0.py \
  --bundle data/architecture/asset_mill/recipes/measured_components_v0.json \
  --clean \
  --out /tmp/gameguy_measured_asset_pump_v0
```

Section-stack assets are also pumped to deterministic JSON first. The current column source uses a `star_polygon` profile so each ring declares radii and star-tip count instead of baked point arrays:

```bash
python3 scripts/asset_pump_v0.py \
  --bundle data/architecture/asset_mill/recipes/section_stack_assets_v0.json \
  --clean \
  --out /tmp/gameguy_section_stack_asset_pump_v0
```

Blocky compound columns keep the source simple while generating shape-rich assets from named simple parts:

```bash
python3 scripts/asset_pump_v0.py \
  --bundle data/architecture/asset_mill/recipes/blocky_column_assets_v0.json \
  --clean \
  --out /tmp/gameguy_blocky_column_asset_pump_v0
```

The reusable blocky shape grammar generalizes that idea for columns, banister posts, fence posts, frame parts, sockets, and other adjustable architectural blockouts:

```bash
python3 scripts/asset_pump_v0.py \
  --bundle data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json \
  --clean \
  --out /tmp/gameguy_blocky_shape_grammar_asset_pump_v0
```

The pump rejects recipe operations, profile types, connector IDs, and semantic tags that are not present in `geometry_dictionary/`.

The first stable generated asset schema is:

```text
contracts/gameguy_asset_v0.json
```

The canonical generation surface is declared in:

```text
data/architecture/asset_mill/asset_generation_registry_v0.json
```

Validate that registry with:

```bash
python3 scripts/validate_asset_generation_registry_v0.py
```

It names the canonical geometry recipe bundles, canonical tool-plan recipe bundle, validators, adapters, and reference-only recipe bundles that are deliberately not pipeline inputs.

Reference-led asset work now starts with a source-side dissection packet before geometry changes:

```bash
python3 scripts/validate_reference_dissection_packet_v0.py
```

The current packet is `data/architecture/asset_mill/reference_packets/gothic_panel_guard_reference_v0.json`. It records the Pexels gothic stone balcony reference, visible components, geometry dictionary terms, and candidate Blender tools for each part. The packet is morphology-reference-only: it does not download images, copy textures, claim historical accuracy, or claim building-code compliance.

Measured molding and compound-pier profile sources now have their own source-only lane:

```bash
python3 scripts/validate_measured_molding_profiles_v0.py
```

The current bundle is `data/architecture/asset_mill/profile_sources/measured_molding_profiles_v0.json`. It records the user-supplied column molding and compound-pier references as cap/base side profiles, fluted shaft channel profiles, plinth profiles, and a lobed compound-pier cross-section. These records declare measurements, geometry dictionary terms, and candidate Blender tools, but do not generate asset JSON, compile tool plans, or execute Blender.

Railing detail profiles extend that same 2D source idea into post, rail, and guard-panel decoration:

```bash
python3 scripts/validate_railing_detail_profiles_v0.py
```

The current bundle is `data/architecture/asset_mill/profile_sources/railing_detail_profiles_v0.json`. It declares square frame blocks, pointed-arch and round-arch recesses, capsule vertical slots, circular bead strips, ogee side moldings, trapezoid transition collars, profiled plinth bases, rounded-rectangle handrail grips, triangular chamfers, octagonal baluster cross-sections, star rosettes, quatrefoil cutouts, and lobed post cross-sections. Each profile must say where it is used, what detail role it has, how it is applied, and which staged Blender tools may execute it later.

The gothic guard-panel tool-plan recipe now selects six of those profiles as a source-owned `railing_detail_profile_stack`. The compiler expands them into a 57-step guard-panel plan with pointed-arch and capsule cutters, shadow recess plates, mirrored side details, a linearly arrayed bead strip, ogee trim, tapered socket collars, and the normal shared finish stack. Blender remains an adapter: it consumes the compiled `gameguy_tool_plan_v0` JSON and executes `mesh_from_pydata`, `modifier_boolean`, `modifier_mirror`, and `modifier_array` steps rather than deciding those details itself.

The profiled plinth base is now the first standalone `profile_detail` prototype. Its source recipe uses `railing_plinth_ogee_base_side_profile_v0` to compile one 14-control-point side profile into fifteen chamfered-square footprint rings with a foot, shadow groove, bead projection, cove slope, neck, and top landing, producing a four-sided wrapped `mesh_from_pydata` detail plan before the shared finish stack is applied. Separate `context_prototype` plans reuse that wrapped plinth mesh with a centered square post core: one verifies the plain top-landing fit, and one adds a four-sided `relief_stack` with recessed fields, raised outer lips, and higher inner bead lips.

The repo now also has a tool-planning layer for near-finished Blender-capable asset construction:

```text
asset intent recipe + family sequence policy -> staged Blender tool-plan compiler -> deterministic gameguy_tool_plan_v0 JSON
```

The first tool dictionary and plan compiler are:

```bash
python3 scripts/compile_blender_tool_plan_v0.py \
  --clean \
  --out /tmp/gameguy_blender_tool_plan_v0
```

This reads `data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json`, `data/architecture/asset_mill/blender_tools/asset_family_tool_sequence_policy_v0.json`, and `data/architecture/asset_mill/tool_plan_recipes/architectural_tool_plan_recipes_v0.json`. It currently compiles separate staged plans for a banister post, fence post, rail segment, gothic panel guard, column, window frame, door frame, profiled plinth base detail, profiled plinth/post context prototype, and profiled plinth/lipped-post context prototype, while the policy defines legal tool sequences for columns, banister posts, fence posts, rail segments, guard panels, window frames, door frames, profile details, and context prototypes. It does not execute Blender, write media, write mesh exports, or make render artifacts. The Blender execution adapter consumes `gameguy_tool_plan_v0` and executes the staged operations.

The column source now uses `profile_operation_stack` to declare a square-to-circle-to-fluted-to-circle-to-square profile sequence from legal `geometry_dictionary/` terms. The compiler preserves those terms in `source_terms`, and the tool-plan validator rejects unknown profile or operator terms before Blender sees the plan.

The default architectural tool-plan bundle also uses `finish_tool_stack` to share a source-owned finishing sequence across the banister post, fence post, rail segment, guard panel, column, window frame, door frame, profile-detail prototype, and context prototypes. That stack declares bevels, weighted normals, procedural stone material/detail, UV projection/packing, cleanup, collision/LOD, final-only preview visibility, and export as source recipe intent; the compiler expands it into deterministic Blender tool steps.

Validate compiled tool-plan JSON before adapter execution with:

```bash
python3 scripts/validate_gameguy_tool_plan_v0.py \
  --manifest /tmp/gameguy_blender_tool_plan_v0/manifest.json
```

The first execution adapter consumes the compiled tool plan and runs supported deterministic steps in Blender:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_tool_plan_execution_v0 \
  --render \
  --export
```

This writes its report, preview, `.blend`, and optional `.glb` under `/tmp`, not the repo. The preview render hides validation helper objects such as collision proxies and LOD variants when the source finish stack requests `final_asset_only` visibility; those helpers still exist in the execution report and exported scene evidence.

The execution report includes `material_regions`, `socket_pass`, `topology_cleanup`, and `quality_pass` evidence. The current banister-post run preserves role material regions, applies two explicit socket booleans with cutter cleanup, creates two socket shadow panels, and reports `0` non-manifold edges after validation.

After a Blender execution run, validate that report with:

```bash
python3 scripts/validate_blender_tool_plan_execution_report_v0.py \
  --report /tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json
```

Blender scripts should be adapters for viewing or exporting deterministic asset JSON. If a Blender script contains source design decisions, move those decisions into source recipes or the asset pump.

The first adapter is:

```bash
python3 scripts/export_blender_asset_preview_v0.py --manifest /tmp/gameguy_asset_pump_v0/manifest.json --validate-only
```

The measured component adapter also consumes generated asset JSON:

```bash
python3 scripts/export_blender_measured_components_preview_v0.py \
  --manifest /tmp/gameguy_measured_asset_pump_v0/manifest.json \
  --validate-only
```

Measurement-source registries and research notes are reference material until they feed concrete asset dissection records or recipe inputs.

Measured component field mapping into `gameguy_asset_v0` is defined at:

```text
docs/asset_pump/measured_component_pump_design_v0.md
```

## Current Language

The current implementation language is Python prototype scripts. A future C++ port is planned, but this repo does not claim a completed C++ implementation.

## Validation

Run from the repo root:

```bash
python3 scripts/validate_generation_pipeline_v0.py
```

For the full Blender execution and quality report gate:

```bash
python3 scripts/validate_generation_pipeline_v0.py --include-blender
```

The expanded validation sequence is:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests
python3 scripts/validate_asset_generation_registry_v0.py
python3 scripts/validate_reference_dissection_packet_v0.py
python3 scripts/validate_measured_molding_profiles_v0.py
python3 scripts/validate_railing_detail_profiles_v0.py
python3 scripts/validate_construction_geometry_taxonomy_v0.py
python3 scripts/compile_sacred_graph_v0.py --clean --out /tmp/gameguy_sacred_graph_v0
python3 scripts/compile_construction_cell_selection_v0.py --clean --graph-manifest /tmp/gameguy_sacred_graph_v0/manifest.json --out /tmp/gameguy_construction_cell_selection_v0
python3 scripts/compile_pattern_field_v0.py --clean --out /tmp/gameguy_pattern_field_v0
python3 scripts/compile_pattern_segments_v0.py --clean --pattern-field-manifest /tmp/gameguy_pattern_field_v0/manifest.json --out /tmp/gameguy_pattern_segments_v0
python3 scripts/compile_blender_tool_plan_v0.py --validate-only
python3 scripts/compile_blender_tool_plan_v0.py --clean --out /tmp/gameguy_blender_tool_plan_v0
python3 scripts/validate_gameguy_tool_plan_v0.py --manifest /tmp/gameguy_blender_tool_plan_v0/manifest.json
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_fence_post_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_rail_segment_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_panel_guard_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_column_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_window_frame_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_door_frame_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/profiled_plinth_base_detail_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/profiled_plinth_post_context_tool_plan_v0_compiled.json --validate-only
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/profiled_plinth_lipped_post_context_tool_plan_v0_compiled.json --validate-only
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_fence_post_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_fence_post_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_fence_post_tool_plan_execution_v0/tool_plan_execution_v0_report.json
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_rail_segment_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_rail_segment_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_rail_segment_tool_plan_execution_v0/tool_plan_execution_v0_report.json
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_column_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_column_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_column_tool_plan_execution_v0/tool_plan_execution_v0_report.json
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_window_frame_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_window_frame_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_window_frame_tool_plan_execution_v0/tool_plan_execution_v0_report.json
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_door_frame_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_door_frame_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_door_frame_tool_plan_execution_v0/tool_plan_execution_v0_report.json
python3 scripts/validate_tiny_fixture_v0.py
python3 scripts/validate_measured_component_source_v0.py
python3 scripts/asset_pump_v0.py --clean --out /tmp/gameguy_asset_pump_v0
python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_asset_pump_v0/manifest.json
python3 scripts/export_blender_asset_preview_v0.py --manifest /tmp/gameguy_asset_pump_v0/manifest.json --validate-only
python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/measured_components_v0.json --clean --out /tmp/gameguy_measured_asset_pump_v0
python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_measured_asset_pump_v0/manifest.json
python3 scripts/export_blender_measured_components_preview_v0.py --manifest /tmp/gameguy_measured_asset_pump_v0/manifest.json --validate-only
python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/section_stack_assets_v0.json --clean --out /tmp/gameguy_section_stack_asset_pump_v0
python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_section_stack_asset_pump_v0/manifest.json
python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/blocky_column_assets_v0.json --clean --out /tmp/gameguy_blocky_column_asset_pump_v0
python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_blocky_column_asset_pump_v0/manifest.json
python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/blocky_shape_grammar_assets_v0.json --clean --out /tmp/gameguy_blocky_shape_grammar_asset_pump_v0
python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_blocky_shape_grammar_asset_pump_v0/manifest.json
python3 scripts/audit_script_orbit_v0.py
test ! -d pattern_lab_2d
find . -path '*pattern_lab_2d*' -print
find . -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
```

Expected current checks:

- Generation pipeline validation passes as the canonical orchestration gate.
- Asset generation registry validation proves the canonical recipe/tool-plan surface and reference-only recipe boundaries.
- Reference dissection packet validation proves visible shapes, geometry terms, and candidate Blender tools before the next geometry pass.
- Measured molding profile validation proves user-supplied cap/base/flute/plinth/compound-pier profile sources before the next geometry pass.
- Railing detail profile validation proves 2D detail shape placement, detail roles, application methods, and Blender tool stage order before the next geometry pass.
- Construction geometry taxonomy validation proves the source-language terms for construction fields, selection/omission, role promotion, motif orbits, tracery, muqarnas cell plans, and lift/fold/sweep/thicken/bevel operations.
- Sacred graph compilation proves a source-owned 22-division construction graph with named point, edge, and star-trace selections before 3D lifting/folding.
- Construction cell selection compilation proves `66` closed ring-band cells and named cell selections for vault webs, tracery openings, and railing recess panels before 3D lifting/folding/sweeping.
- Pattern field compilation proves a source-owned multi-center rosette construction field with faint guide layers and named selected trace groups before intersections, omission rules, or 3D promotion.
- Pattern segment splitting proves the multi-center field can be cut at intersections into smaller candidate segments before guide omission, closed-loop extraction, or 3D role promotion.
- JSON parses.
- Python scripts compile.
- Asset pump tests pass.
- Blender tool-plan compiler validates a `97`-tool dictionary, a `9`-family sequence policy, and compiles ten default plans: a `32`-step banister post, a `32`-step fence post, a `28`-step rail segment, a `57`-step gothic panel guard, a `31`-step column, a `25`-step window frame, a `25`-step door frame, a `22`-step profiled plinth base detail, a `23`-step profiled plinth/post context prototype, and a `59`-step profiled plinth/lipped-post context prototype.
- `gameguy_tool_plan_v0` validation proves manifest shape, known tool IDs, stable step order, stage order, asset-family sequence policy, deterministic steps, false claims, and no compiler media/mesh output.
- Blender tool-plan execution adapter validation consumes the compiled `32`-step banister plan, the compiled `32`-step fence-post plan, the compiled `28`-step rail-segment plan, the compiled `57`-step guard-panel plan, the compiled `31`-step column plan, the compiled `25`-step window-frame plan, the compiled `25`-step door-frame plan, the compiled `22`-step profile-detail plan, the compiled `23`-step post-context plan, and the compiled `59`-step lipped-post context plan.
- Blender tool-plan execution report validation proves adapter boundary rules, material-region preservation, topology count, and no repo-local generated outputs for the seven full-executed family plans. The profile-detail, post-context, and lipped-post context plans are adapter-validated by default and can be manually executed for preview. The banister and fence-post profiles also prove socket boolean evidence, the rail-segment profile proves connector-tab material regions, the guard-panel profile proves reference-led panel/pier/collar/recess material regions plus decorative detail boolean evidence, and the column profile proves square/circular transition and fluted-shaft material regions.
- Blender tool-plan execution quality evidence is recorded in `workflow/reports/3D-LAB-0021-execution-quality-pass-v0/`.
- Tiny source fixture validation passes.
- Measured component source validation passes.
- Generated `gameguy_asset_v0` validation passes for simple, measured, section-stack, blocky-column, and blocky-shape grammar pump output.
- Blender adapter validation consumes generated asset JSON.
- Measured component Blender adapter validation consumes generated measured asset JSON.
- Script orbit audit runs without deleting or moving files.
- No `pattern_lab_2d` paths.
- No media, render, mesh, or Blender proof output files.

## Claims

This repo makes no production, structural, fabrication, historical accuracy, gym/museum approval, or game-engine integration claims. Assets and scripts are prototype inputs and proof tooling only.
