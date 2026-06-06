# Brow Eye Region Review v0

This is the first single-region working sheet for the humanoid head. It focuses only on the brow ridge and eye socket band.

The source is:

```text
data/characters/head_construction/humanoid_brow_eye_region_review_v0.json
```

Compile the compact review sheet:

```bash
python3 scripts/compile_humanoid_brow_eye_region_review_v0.py
```

Default outputs:

```text
/tmp/gameguy_humanoid_brow_eye_region_review_v0/humanoid_brow_eye_region_review_v0.json
/tmp/gameguy_humanoid_brow_eye_region_review_v0/humanoid_brow_eye_region_review_v0.md
```

This compiler does not read the generated full-head blockout JSON. It reads the source taxonomy and the external skull measurement stack, then summarizes only the brow-relevant slices.

## Region

```text
forehead break
-> glabella center
-> brow wings
-> upper socket rims
-> socket shadows
-> nose bridge landing
```

The goal is to make the brow and socket band read as skull structure, not loose plates. The compiler should treat this as three brow meshes: a forward `brow_glabella` and wrapped `brow_wing_L` / `brow_wing_R` pieces, with each socket rim and shadow tucked under its side wing.

## Skull Evidence

| Slice | Use |
|---|---|
| `xy_brow_band` | Main brow width/depth footprint and upper-orbit band. |
| `yz_center_profile` | Side silhouette for forehead break, brow projection, socket recess, and occiput context. |
| `xz_front_face_surface` | Front face width/height trace for socket placement and brow-to-face relation. |
| `xy_zygoma_orbit` | Lower orbit and cheekbone support; boundary only for this region. |

## Existing Controls

| Control | Use |
|---|---|
| `forehead_wrap_ratio` | Wrap brow and upper face around the skull side. |
| `brow_arc_ratio` | Shape the brow as a glabella-centered arc. |
| `eye_socket_slant_ratio` | Control socket tilt while staying mirrored. |
| `nose_bridge_blend_ratio` | Reserve the center landing for the later nose wedge. |
| `feature_embed_overlap_m` | Sink the brow/socket pieces into the face mask before any join pass. |

## Region Controls Promoted Into Taxonomy

| Control | Reason |
|---|---|
| `brow_forward_offset_m` | Push brow projection in side view without changing the arc. |
| `socket_under_brow_setback_m` | Ensure socket shadows sit behind the brow. |
| `glabella_peak_ratio` | Tune the center knot separately from the brow wings. |
| `brow_side_wrap_ratio` | Wrap brow wings independently from the full forehead. |

## Blocked Scope

- Do not tune cheeks except as the lower orbit boundary.
- Do not sculpt the nose beyond reserving the bridge landing.
- Do not inspect or edit generated full-head blockout output for this review.
- Do not join or remesh the head.
