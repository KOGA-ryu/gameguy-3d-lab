# 3D-LAB-0012: Legacy Blender Proof Policy

## Decision

All remaining legacy `blender_*.py` proof scripts are `REFERENCE_ONLY`.

Canonical Blender adapters now use the `export_blender_*` prefix:

```text
scripts/export_blender_asset_preview_v0.py
scripts/export_blender_measured_components_preview_v0.py
```

## Why

The repo center is:

```text
source asset recipe -> profile/operation compiler -> deterministic asset geometry JSON
```

Legacy Blender scripts often carry proof-scene construction logic, generated-output assumptions, or compiler imports. They should not be treated as engine/source logic.

## Result

Script orbit after this decision:

```text
CONVERT_TO_ADAPTER=0
REPLACE_BY_PUMP=0
```

The scripts were not deleted or moved. They remain historical reference until a separate explicit deletion task.

## Follow-Up

When a Blender preview is needed, build or extend an `export_blender_*` adapter that consumes source JSON or deterministic generated JSON.
