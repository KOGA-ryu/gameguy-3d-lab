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
source asset recipe -> profile/operation compiler -> deterministic asset geometry JSON
```

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

The repo now also has a tool-planning layer for near-finished Blender-capable asset construction:

```text
asset intent recipe -> staged Blender tool-plan compiler -> deterministic gameguy_tool_plan_v0 JSON
```

The first tool dictionary and plan compiler are:

```bash
python3 scripts/compile_blender_tool_plan_v0.py \
  --clean \
  --out /tmp/gameguy_blender_tool_plan_v0
```

This reads `data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json` and `data/architecture/asset_mill/tool_plan_recipes/banister_post_tool_plan_recipe_v0.json`. It does not execute Blender, write media, write mesh exports, or make render artifacts. The Blender execution adapter consumes `gameguy_tool_plan_v0` and executes the staged operations.

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

This writes its report, preview, `.blend`, and optional `.glb` under `/tmp`, not the repo.

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
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
python3 -m unittest discover -s tests
python3 scripts/compile_blender_tool_plan_v0.py --validate-only
python3 scripts/compile_blender_tool_plan_v0.py --clean --out /tmp/gameguy_blender_tool_plan_v0
python3 scripts/validate_gameguy_tool_plan_v0.py --manifest /tmp/gameguy_blender_tool_plan_v0/manifest.json
python3 scripts/execute_blender_tool_plan_v0.py --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json --validate-only
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /tmp/gameguy_blender_tool_plan_v0/plans/gothic_stone_banister_post_tool_plan_v0_compiled.json \
  --out /tmp/gameguy_blender_tool_plan_execution_v0 \
  --render \
  --export
python3 scripts/validate_blender_tool_plan_execution_report_v0.py --report /tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json
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

- JSON parses.
- Python scripts compile.
- Asset pump tests pass.
- Blender tool-plan compiler validates a `97`-tool dictionary and compiles a `32`-step banister-post plan.
- `gameguy_tool_plan_v0` validation proves manifest shape, known tool IDs, stable step order, stage order, deterministic steps, false claims, and no compiler media/mesh output.
- Blender tool-plan execution adapter validation consumes the compiled `32`-step plan.
- Blender tool-plan execution report validation proves adapter boundary rules, material-region preservation, socket boolean evidence, topology count, and no repo-local generated outputs.
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
