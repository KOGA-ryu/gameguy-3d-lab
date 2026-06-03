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

Measurement sources for future asset dissection live at:

```text
data/architecture/taxonomy/source_measurements/asset_dissection_measurement_sources_v0.json
```

That registry ranks source types by usefulness for extracting part measurements, curves, ratios, and operator-chain inputs.

## Current Language

The current implementation language is Python prototype scripts. A future C++ port is planned, but this repo does not claim a completed C++ implementation.

## Validation

Run from the repo root:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
test ! -d pattern_lab_2d
find . -path '*pattern_lab_2d*' -print
find . -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.gif' -o -name '*.webp' -o -name '*.blend' -o -name '*.blend1' -o -name '*.obj' -o -name '*.gltf' -o -name '*.glb' -o -name '*.fbx' \) -print
```

Expected current checks:

- JSON parses.
- Python scripts compile.
- No `pattern_lab_2d` paths.
- No media, render, mesh, or Blender proof output files.

## Claims

This repo makes no production, structural, fabrication, historical accuracy, gym/museum approval, or game-engine integration claims. Assets and scripts are prototype inputs and proof tooling only.
