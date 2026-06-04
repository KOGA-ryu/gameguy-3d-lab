# 3D-LAB-0068 Mace Baluster Radial Post v0

## Result

Added a second radial-stack post asset that uses entasis and a mace-like lower belly instead of a straight cylindrical shaft.

```text
radial_stack_assets_v0
-> mace_baluster_reference_post_v0
-> height/radius entasis profile
-> tapered rib arrays
-> compact top cap
-> embedded rail-socket plates
-> gameguy_asset_v0 JSON
```

## Changed

```text
data/architecture/asset_mill/recipes/radial_stack_assets_v0.json
data/architecture/asset_mill/asset_generation_registry_v0.json
tests/test_asset_pump_v0.py
tests/test_validate_asset_generation_registry_v0.py
README.md
workflow/reports/3D-LAB-0068-mace-baluster-radial-post-v0/report.md
workflow/reports/3D-LAB-0068-mace-baluster-radial-post-v0/receipt.json
```

## Generated Asset Evidence

```text
asset_id=mace_baluster_reference_post_v0
source_schema=asset_mill_radial_stack_bundle_v0
source_operation=radial_stack
segments=16
ring_count=17
radial_detail_count=3
rib_count=24
attachment_count=2
side_socket_count=2
vertex_count=482
face_count=444
part_count=27
dimensions_m=0.88 x 0.88 x 1.48
```

The tapered rib effect is source-authored as three radial rib arrays:

```text
lower_tapered_rib: rib_depth_m=0.055
middle_tapered_rib: rib_depth_m=0.04
upper_tapered_rib: rib_depth_m=0.025
```

This keeps the ribs visually heavier near the mace belly and lighter near the neck/cap without adding Blender-side shape decisions.

## Preview

The Blender preview adapter consumed generated `gameguy_asset_v0` JSON and rendered:

```text
/tmp/gameguy_radial_stack_mace_preview_v0/mace_baluster_reference_post_v0_preview.png
```

Generated preview outputs stayed under `/tmp`.

## Boundary

This slice still does not:

```text
boolean-cut recessed sockets
bevel or weighted-normal polish the asset
join/export final GLB
claim production, structural, fabrication, or code compliance
write generated mesh/media into the repo
```

Those are polish/export steps after the source silhouette is accepted.

## Validation

```text
python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/radial_stack_assets_v0.json --clean --out /tmp/gameguy_radial_stack_asset_pump_v0
pumped assets=2 vertices=788 faces=744 out=/tmp/gameguy_radial_stack_asset_pump_v0

python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json
PASS gameguy_asset_v0 validation: 2 assets, 788 vertices, 744 faces

python3 scripts/export_blender_asset_preview_v0.py --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json --validate-only
PASS Blender asset adapter validation: 2 assets, 788 vertices, 744 faces

python3 -m unittest tests.test_asset_pump_v0 tests.test_validate_asset_generation_registry_v0 tests.test_validate_generation_pipeline_v0
OK, 32 tests

python3 -m unittest discover -s tests
OK, 178 tests

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_mace_baluster_v0_final.json
PASS generation pipeline validation: commands=46 json=276 include_blender=false

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/export_blender_asset_preview_v0.py -- --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json --out /tmp/gameguy_radial_stack_mace_preview_v0 --render --hide-connectors
PASS Blender asset preview export: assets=2 out=/tmp/gameguy_radial_stack_mace_preview_v0
```

## Next

If the silhouette is accepted, the next useful step is a Blender polish plan for this asset: bevel the annular molding stack, weighted normals, and boolean-recess the side sockets so they stop reading as external plates.
