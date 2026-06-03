# 3D-LAB-0011: Measured Components Blender Adapter

## Decision

`scripts/blender_asset_mill_measured_components_v1.py` and `scripts/blender_asset_mill_measured_components_v2.py` are demoted from `CONVERT_TO_ADAPTER` to `REFERENCE_ONLY`.

Replacement:

```text
scripts/export_blender_measured_components_preview_v0.py
```

Input:

```text
data/architecture/asset_mill/recipes/measured_components_v0.json
```

## Evidence

Validated adapter path:

```bash
python3 scripts/export_blender_measured_components_preview_v0.py --validate-only
```

Result:

| Check | Result |
| --- | ---: |
| source assets | 22 |
| v1 assets | 12 |
| v2 assets | 10 |
| proof primitives | 52 |
| sockets | 74 |

The replacement adapter does not import or run the old compiler scripts.

## Preserved Value

- Measured component preview/export role.
- Cube, cylinder, and curve proof primitive preview hints.
- Socket markers.
- Semantic material grouping.
- Machine-readable adapter report.

## Not Preserved

- Compiler imports from old measured component scripts.
- Default writes to `goal/architecture/blender_tests`.

## Follow-Up

Keep the old proof scripts only as historical reference until a separate deletion task.
