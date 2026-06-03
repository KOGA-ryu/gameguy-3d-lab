# 3D-LAB-0009: Measured Components Source Promotion

## Decision

`scripts/compile_asset_mill_measured_components_v1.py` and `scripts/compile_asset_mill_measured_components_v2.py` are demoted from `REPLACE_BY_PUMP` to `REFERENCE_ONLY`.

Their stable value is now source data:

```text
data/architecture/asset_mill/recipes/measured_components_v0.json
```

Validator:

```text
scripts/validate_measured_component_source_v0.py
```

## Evidence

| Check | Result |
| --- | --- |
| v1 assets promoted | 12 |
| v2 assets promoted | 10 |
| total promoted assets | 22 |
| generated `goal/` refs retained | no |
| wall-clock fields retained | no |
| source validator added | yes |
| `REPLACE_BY_PUMP` scripts remaining | 0 |

## Preserved Value

- Asset IDs, dimensions, bounds, ratio basis, uncertainty, sockets, semantic roles, validation expectations, and proof primitives.
- Local measurement and research refs that exist in the source repo.
- Version provenance via `source_version` and `source_script`.
- Explicit no-claims posture.

## Not Preserved

- Generated `goal/architecture/asset_mill_measured_v1` index references.
- Missing generated v2 orientation report references.
- `created_at_utc` fields.
- Compiler-side writes to generated recipe/index/report/receipt lanes.

## Follow-Up

Measured components are now source catalog entries, not active compiler scripts. Pump support should be added only after a stable operator mapping exists from measured component proof primitives and sockets into `gameguy_asset_v0`.
