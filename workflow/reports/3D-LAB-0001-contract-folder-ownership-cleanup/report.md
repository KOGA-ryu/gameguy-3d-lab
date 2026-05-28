# 3D-LAB-0001: Contract And Folder Ownership Cleanup

## Result

Reviewed `contracts/` and quarantined the obvious 2D/mosaic-only contracts under:

```text
contracts/quarantine_2d_mosaic_v0/
```

Kept active map, terrain, building, connector, geometry, measurement, and workflow-adjacent contracts in the root of `contracts/`.

Added ownership docs:

- `FOLDER_OWNERSHIP.md`
- `contracts/README.md`
- `contracts/quarantine_2d_mosaic_v0/README.md`

## Quarantined Contracts

- `example_border_corner_32x32.contract.json`
- `example_center_medallion_64x64.contract.json`
- `example_floor_fill_16x16.contract.json`
- `example_verified_floor_fill_16x16.contract.json`
- `met_mosaic_floor_panel_family_v0.contract.json`
- `met_mosaic_floor_panel_floor_fill_16x16.contract.json`
- `mosaic_dungeon_tile_contract_v0.json`
- `mosaic_tile_family_contract_v0.json`

These records describe 2D mosaic tiles, Met mosaic panel tile families, example floor-fill/medallion/border output records, or 2D export metadata.

## Kept In Active Contract Root

Kept contracts that remain relevant to the 3D lab:

- architecture measurements and shape dictionaries
- asset mill solid recipes
- floor plans and building/topology recipes
- terrain fold, seam, hex topology, and plot vertex graph contracts
- map authoring, map cube, and pathway connection contracts
- geometry/cube recipe metadata
- workflow/factory records that are not clearly 2D-only

## Validation

Commands run from `/Users/kogaryu/gameguy-3d-lab`:

```bash
find data contracts docs geometry_dictionary workflow -name '*.json' -print0 | xargs -0 -n 1 python3 -m json.tool >/dev/null
python3 -m py_compile scripts/*.py
```

Result: PASS.

## Non-Goals Respected

- Did not touch the old Mac prototype repo.
- Did not generate assets, renders, meshes, screenshots, or Blender outputs.
- Did not run Blender.

## Next Recommended Task

Review `contracts/lane_registry_v0.json`, `contracts/factory_manifest_v0.json`, and `contracts/job_contract_v0.json` for whether the new repo should keep generic workflow/factory contracts as-is or narrow them to 3D-lab lanes only.
