# 3D-LAB-0067 Radial Stack Reference Post v0

## Result

Added a source-first radial-stack asset lane for cylindrical railing and banister posts.

```text
height/radius side profile
-> radial_stack operation
-> deterministic low-poly cylindrical body
-> named radial ribs and rail-socket parts
-> gameguy_asset_v0 JSON
-> Blender adapter preview
```

The first source asset is:

```text
data/architecture/asset_mill/recipes/radial_stack_assets_v0.json
cylindrical_reference_post_v0
```

## Changed

```text
data/architecture/asset_mill/recipes/radial_stack_assets_v0.json
data/architecture/asset_mill/asset_generation_registry_v0.json
geometry_dictionary/operations/radial_stack.json
geometry_dictionary/geometry_dictionary_v0_report.md
contracts/gameguy_asset_v0.json
scripts/asset_pump_v0.py
scripts/validate_generation_pipeline_v0.py
tests/test_asset_pump_v0.py
tests/test_validate_asset_generation_registry_v0.py
tests/test_validate_generation_pipeline_v0.py
README.md
workflow/reports/3D-LAB-0067-radial-stack-reference-post-v0/report.md
workflow/reports/3D-LAB-0067-radial-stack-reference-post-v0/receipt.json
```

## Generated Asset Evidence

```text
asset_id=cylindrical_reference_post_v0
source_schema=asset_mill_radial_stack_bundle_v0
source_operation=radial_stack
segments=16
ring_count=14
radial_detail_count=1
rib_count=8
attachment_count=2
side_socket_count=2
vertex_count=306
face_count=300
part_count=11
dimensions_m=1.04 x 0.84 x 1.54
```

The body is one revolved radial-stack mesh. The ribs and rail sockets are separate named mesh parts inside the same generated asset JSON, so later tooling can select, polish, join, or replace them deliberately.

## Preview

The Blender preview adapter consumed the generated `gameguy_asset_v0` JSON and rendered:

```text
/tmp/gameguy_radial_stack_asset_preview_v0/cylindrical_reference_post_v0_preview.png
```

Generated preview outputs stayed under `/tmp`.

## Boundary

This slice does not:

```text
add Blender source design logic
replace the asset-polish lane
join/export a final GLB for this asset
claim production, structural, fabrication, or code compliance
write generated mesh/media into the repo
```

## Validation

```text
python3 -m py_compile scripts/asset_pump_v0.py scripts/validate_generation_pipeline_v0.py
PASS

python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/radial_stack_assets_v0.json --clean --out /tmp/gameguy_radial_stack_asset_pump_v0
pumped assets=1 vertices=306 faces=300 out=/tmp/gameguy_radial_stack_asset_pump_v0

python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json
PASS gameguy_asset_v0 validation: 1 assets, 306 vertices, 300 faces

python3 scripts/export_blender_asset_preview_v0.py --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json --validate-only
PASS Blender asset adapter validation: 1 assets, 306 vertices, 300 faces

python3 -m unittest tests.test_asset_pump_v0 tests.test_validate_asset_generation_registry_v0 tests.test_validate_generation_pipeline_v0
OK, 31 tests

python3 -m unittest discover -s tests
OK, 177 tests

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_radial_stack_v0_final.json
PASS generation pipeline validation: commands=46 json=275 include_blender=false

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/export_blender_asset_preview_v0.py -- --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json --out /tmp/gameguy_radial_stack_asset_preview_v0 --render --hide-connectors
PASS Blender asset preview export: assets=1 out=/tmp/gameguy_radial_stack_asset_preview_v0
```

## Next

Refine this cylindrical post by moving from rectangular rail sockets to proper recessed sockets/collars, then add an asset-polish plan that bevels the radial stack without changing the source recipe.
