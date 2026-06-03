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

Section-stack assets are also pumped to deterministic JSON first:

```bash
python3 scripts/asset_pump_v0.py \
  --bundle data/architecture/asset_mill/recipes/section_stack_assets_v0.json \
  --clean \
  --out /tmp/gameguy_section_stack_asset_pump_v0
```

The pump rejects recipe operations, profile types, connector IDs, and semantic tags that are not present in `geometry_dictionary/`.

The first stable generated asset schema is:

```text
contracts/gameguy_asset_v0.json
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
python3 scripts/audit_script_orbit_v0.py
test ! -d pattern_lab_2d
find . -path '*pattern_lab_2d*' -print
find . -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
```

Expected current checks:

- JSON parses.
- Python scripts compile.
- Asset pump tests pass.
- Tiny source fixture validation passes.
- Measured component source validation passes.
- Generated `gameguy_asset_v0` validation passes for simple, measured, and section-stack pump output.
- Blender adapter validation consumes generated asset JSON.
- Measured component Blender adapter validation consumes generated measured asset JSON.
- Script orbit audit runs without deleting or moving files.
- No `pattern_lab_2d` paths.
- No media, render, mesh, or Blender proof output files.

## Claims

This repo makes no production, structural, fabrication, historical accuracy, gym/museum approval, or game-engine integration claims. Assets and scripts are prototype inputs and proof tooling only.
