# 3D-LAB-0008: Asset Mill Solids Replacement Decision

## Decision

`scripts/compile_asset_mill_solids_v0.py` is demoted from `REPLACE_BY_PUMP` to `REFERENCE_ONLY`.

It is not deletion-ready yet. Keep it only as historical comparison until a separate deletion task removes it.

## Replacement

Canonical replacement:

```text
scripts/asset_pump_v0.py
```

Stable generated schema:

```text
contracts/gameguy_asset_v0.json
```

## Evidence

No-write comparison between the old compiler path and the pump:

| Check | Result |
| --- | --- |
| Old asset count | 14 |
| New asset count | 14 |
| Asset IDs match | yes |
| Dimension mismatches | 0 |
| Old schema | `compiled_asset_mill_solid_v0` |
| New schema | `gameguy_asset_v0` |
| `child_slots` preserved | yes |

The pump now preserves the old compiler's useful `child_slots` value in generated asset JSON.

## Preserved Value

- Same source recipe bundle.
- Same core operations: `extrude`, `loft_sections`, and `compound_asset`.
- Same source asset IDs.
- Same generated dimensions.
- Semantic tags and no-claims data.
- Connector anchor intent, with connector directions added by the pump.
- Child attachment/decorative slot metadata through `child_slots`.

## Not Preserved

- Wall-clock `created_at_utc` fields, because pump output must stay deterministic.
- Repo-local `goal/architecture/asset_mill_v0` writes, because the pump writes to an explicit output root.
- Generated receipts and Markdown reports, because workflow evidence belongs in workflow packets.
- `profile_points_2d` / section-only output, because `gameguy_asset_v0` emits adapter-facing mesh JSON.
- `approx_volume`, because it is a derived metric outside the first stable generated asset schema.

## Follow-Up

Use `asset_pump_v0.py` for future simple solid generation. Do not run `compile_asset_mill_solids_v0.py` as active source logic.
