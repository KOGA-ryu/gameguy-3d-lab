# 3D-LAB-0010: Blender Asset Mill Smoke Test Demotion

## Decision

`scripts/blender_asset_mill_smoke_test_v0.py` is demoted from `CONVERT_TO_ADAPTER` to `REFERENCE_ONLY`.

Replacement:

```text
scripts/export_blender_asset_preview_v0.py
```

## Why

The old smoke test consumes the obsolete generated Asset Mill solids lane:

```text
goal/architecture/asset_mill_v0/asset_mill_compiled_index_v0.json
```

The replacement adapter consumes deterministic `gameguy_asset_v0` JSON from the canonical pump output.

## Evidence

Validated adapter path:

```bash
python3 scripts/asset_pump_v0.py --clean --out /tmp/gameguy_asset_pump_v0
python3 scripts/export_blender_asset_preview_v0.py --manifest /tmp/gameguy_asset_pump_v0/manifest.json --validate-only
```

Result:

| Check | Result |
| --- | ---: |
| assets | 14 |
| vertices | 280 |
| faces | 186 |

## Preserved Value

- Asset Mill preview/export role.
- Semantic material grouping.
- Scene context in Blender mode.
- Asset identity and no-claim custom properties.
- Machine-readable adapter report.

## Not Preserved

- Reading obsolete `goal/architecture/asset_mill_v0` solids.
- Reconstructing meshes from profile sections instead of using `gameguy_asset_v0` mesh JSON.
- Default writes to `goal/architecture/blender_tests`.

## Follow-Up

Keep the old smoke test only as historical reference until a separate deletion task.
