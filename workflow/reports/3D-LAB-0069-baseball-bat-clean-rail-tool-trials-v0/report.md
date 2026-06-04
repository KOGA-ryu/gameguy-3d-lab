# 3D-LAB-0069 Baseball Bat Clean Rail Tool Trials v0

## Result

Added a clean horizontal rail source asset and used Blender only for tool trials on duplicated copies.

```text
baseball_bat_clean_rail_v0
-> radial_stack axis=x
-> one plain generated rail body
-> OG Blender copy preserved
-> adjacent Blender modifier trials
```

The clean source asset is:

```text
data/architecture/asset_mill/recipes/radial_stack_assets_v0.json
baseball_bat_clean_rail_v0
```

## Source Asset Evidence

```text
asset_id=baseball_bat_clean_rail_v0
asset_kind=radial_stack_rail
source_operation=radial_stack
axis=x
segments=16
ring_count=9
radial_detail_count=0
attachment_count=0
vertex_count=146
face_count=160
part_count=1
dimensions_m=2.4 x 0.36 x 0.36
connectors=east, west
```

This asset intentionally has no sockets, ribs, collars, or old asset pieces attached. It is the original clean copy for Blender experiments.

## Blender Tool Trials

Generated under `/tmp`:

```text
/tmp/gameguy_baseball_bat_rail_tool_trials_v0/baseball_bat_rail_tool_trials_v0.blend
/tmp/gameguy_baseball_bat_rail_tool_trials_v0/baseball_bat_rail_tool_trials_overview_v0.png
/tmp/gameguy_baseball_bat_rail_tool_trials_v0/baseball_bat_rail_tool_trials_report_v0.json
```

The trial scene consumes generated asset JSON only. It does not read source recipes.

Variants:

```text
OG_raw_clean_copy: no Blender modifiers
bevel_weighted_normal: Bevel + Weighted Normal
shade_smooth_weighted: Shade Smooth + Weighted Normal
subtle_noise_surface: Shade Smooth + Bevel + Weighted Normal + Displace noise
extra_taper_bevel: Bevel + Weighted Normal + Simple Deform Taper
```

## Changed

```text
README.md
data/architecture/asset_mill/asset_generation_registry_v0.json
data/architecture/asset_mill/recipes/radial_stack_assets_v0.json
geometry_dictionary/operations/radial_stack.json
scripts/asset_pump_v0.py
tests/test_asset_pump_v0.py
tests/test_validate_asset_generation_registry_v0.py
workflow/reports/3D-LAB-0069-baseball-bat-clean-rail-tool-trials-v0/report.md
workflow/reports/3D-LAB-0069-baseball-bat-clean-rail-tool-trials-v0/receipt.json
```

## Validation

```text
python3 scripts/asset_pump_v0.py --bundle data/architecture/asset_mill/recipes/radial_stack_assets_v0.json --clean --out /tmp/gameguy_radial_stack_asset_pump_v0
pumped assets=3 vertices=934 faces=904 out=/tmp/gameguy_radial_stack_asset_pump_v0

python3 scripts/validate_gameguy_asset_v0.py --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json
PASS gameguy_asset_v0 validation: 3 assets, 934 vertices, 904 faces

python3 scripts/export_blender_asset_preview_v0.py --manifest /tmp/gameguy_radial_stack_asset_pump_v0/manifest.json --validate-only
PASS Blender asset adapter validation: 3 assets, 934 vertices, 904 faces

python3 -m unittest tests.test_asset_pump_v0 tests.test_validate_asset_generation_registry_v0 tests.test_validate_generation_pipeline_v0
OK, 33 tests

python3 -m unittest discover -s tests
OK, 179 tests

python3 scripts/validate_generation_pipeline_v0.py --skip-unit-tests --json-report /tmp/gameguy_pipeline_baseball_bat_rail_v0_final.json
PASS generation pipeline validation: commands=46 json=277 include_blender=false

/Applications/Blender.app/Contents/MacOS/Blender --background --python-expr '<tool trial scene generation>'
BASEBALL_BAT_TOOL_TRIAL_RENDER=/tmp/gameguy_baseball_bat_rail_tool_trials_v0/baseball_bat_rail_tool_trials_v0.png
```

## Next

The most useful next step is to pick one tool direction. For a rail, the strongest candidate is `bevel_weighted_normal`: it keeps the bat silhouette readable while softening the low-poly faceting without destroying the source geometry.
