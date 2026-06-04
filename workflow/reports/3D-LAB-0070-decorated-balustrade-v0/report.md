# 3D-LAB-0070 Decorated Balustrade V0

## Goal

Promote the clean baseball-bat rail into the first source-owned decorated balustrade module without hiding ornament decisions in Blender.

## Source Shape

```text
decorated_balustrade source recipe
-> radial-stack bat handrail
-> two radial-stack posts
-> collar and bead bands
-> pointed-arch infill
-> low-poly quatrefoil/rosette ornament
-> gameguy_asset_v0 JSON
-> Blender preview adapter
```

## Files

- `data/architecture/asset_mill/recipes/decorated_balustrade_assets_v0.json`
- `geometry_dictionary/operations/decorated_balustrade.json`
- `scripts/asset_pump_v0.py`
- `data/architecture/asset_mill/asset_generation_registry_v0.json`
- `scripts/validate_generation_pipeline_v0.py`
- `tests/test_asset_pump_v0.py`

## Generated Asset

```text
asset_id=baseball_bat_gothic_balustrade_v0
source_schema=asset_mill_decorated_balustrade_bundle_v0
source_operation=decorated_balustrade
asset_kind=decorated_balustrade_module
dimensions_m=3.19 x 0.41922 x 1.385
vertices=1554
faces=1372
named_parts=26
```

Named part groups:

- rail body: 1
- posts: 2
- collars and bead bands: 4
- infill frame boxes: 5
- pointed arch pieces: 9
- quatrefoil/rosette pieces: 5

## Preview Outputs

```text
/tmp/gameguy_decorated_balustrade_preview_v0/asset_preview_v0_workbench.png
/tmp/gameguy_decorated_balustrade_preview_v0/baseball_bat_gothic_balustrade_front_v0.png
/tmp/gameguy_decorated_balustrade_preview_v0/asset_preview_v0.blend
```

## Validation

```text
python3 -m unittest discover -s tests
180 tests passed

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_decorated_balustrade_v0_final.json
PASS generation pipeline validation: commands=49 json=280 include_blender=false

/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/export_blender_asset_preview_v0.py -- --manifest /tmp/gameguy_decorated_balustrade_asset_pump_v0/manifest.json --out /tmp/gameguy_decorated_balustrade_preview_v0 --render --hide-connectors
PASS Blender asset preview export: assets=1 out=/tmp/gameguy_decorated_balustrade_preview_v0
```

## Notes

The quatrefoil is raised as named low-poly parts instead of boolean-cut in v0. That keeps the motif easy to tune or replace before we commit to cutter/boolean behavior.

The top rail intentionally remains asymmetric because it preserves the current baseball-bat grammar. A later recipe can add a mirrored-bat rail or a symmetrical baluster rail if the silhouette reads too prop-like.
