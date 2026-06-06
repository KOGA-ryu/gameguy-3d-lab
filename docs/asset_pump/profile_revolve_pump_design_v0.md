# Profile Revolve Pump Design V0

## Purpose

`profile_revolve` is the source vocabulary for lathed architectural shapes.

It represents the idea:

```text
2D side profile
-> rotate around an axis
-> deterministic mesh vertices and faces
```

The Blender adapter should consume the generated mesh. It should not decide the
profile, taper, collar placement, or silhouette.

## Source Shape

The source recipe uses named side-profile points:

```json
{
  "point_id": "belly_max",
  "at": 0.9,
  "radius_m": 0.275
}
```

`at` is the position along the revolve axis. `radius_m` is the distance from the
axis. The points must be ordered and increasing.

## Mesh Generation

For each side-profile point, the pump creates a ring:

```text
x = radius * cos(angle)
y = radius * sin(angle)
z = at
```

Then it bridges consecutive rings with quad faces and caps the bottom and top
with center-fan triangles.

## First Asset

The first source asset is:

```text
data/architecture/asset_mill/recipes/profile_revolve_assets_v0.json
-> gothic_calibration_revolved_shaft_v0
```

It is a narrow proof asset: a spun shaft with lower lip, necking, entasis belly,
upper collar, and top neck. Square plinth and cap pieces should be composed later
as separate parts around this shaft.

## Commands

```bash
python3 scripts/asset_pump_v0.py \
  --bundle data/architecture/asset_mill/recipes/profile_revolve_assets_v0.json \
  --clean \
  --out /tmp/gameguy_profile_revolve_asset_pump_v0

python3 scripts/validate_gameguy_asset_v0.py \
  --manifest /tmp/gameguy_profile_revolve_asset_pump_v0/manifest.json

python3 scripts/export_blender_asset_preview_v0.py \
  --manifest /tmp/gameguy_profile_revolve_asset_pump_v0/manifest.json \
  --validate-only
```
