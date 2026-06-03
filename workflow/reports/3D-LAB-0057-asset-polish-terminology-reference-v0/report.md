# 3D-LAB-0057 Asset Polish Terminology Reference v0

## Result

Added a reference doc for the terminology needed to discuss asset polish and Blender tool-plan work.

```text
architectural part terms
-> geometric construction terms
-> Blender/tool-plan terms
-> recipe target names
```

## Added

```text
docs/asset_pump/asset_polish_terminology_reference_v0.md
```

The doc covers:

- railing and balustrade vocabulary
- posts, plinths, shafts, caps, piers, and compound supports
- panels, frames, windows, mullions, tracery, foils, and openings
- arches, vaults, ribs, bosses, springlines, intrados, extrados, and archivolts
- molding/profile terms such as bead, torus, cavetto, scotia, cyma, ogee, arris, reveal, and fielded panel
- construction geometry terms for source patterns, selected subgraphs, cells, rosettes, orbits, girih, strapwork, and muqarnas cell plans
- Blender/tool-plan operation words such as inset faces, bevel, chamfer, solidify, curve bevel, weighted normals, UV unwrap, material slots, and proxy meshes
- phrasebook examples for telling Dex exactly what to change
- target naming convention for future recipes

## Source Boundary

This slice does not alter generators, Blender adapters, mesh outputs, or validation rules. It gives the repo a shared vocabulary for the next asset-polish schema/tool-plan work.

## Validation

```text
python3 -m json.tool workflow/reports/3D-LAB-0057-asset-polish-terminology-reference-v0/receipt.json
PASS

rg "Source References|Phrasebook|Target Naming Convention" docs/asset_pump/asset_polish_terminology_reference_v0.md
PASS

git diff --check
PASS
```

## Next

Use the reference doc to define the first `asset_polish_tool_plan_v0` schema:

```text
gameguy_asset_v0 geometry
-> named polish targets
-> ordered operation stack
-> Blender adapter executes, not decides
```
