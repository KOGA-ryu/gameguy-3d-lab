# Operator Animal Handoff V0

This handoff defines what the future drawing UI or manual Blender workcard must
capture before an animal asset is modeled.

## Required Fields

```text
animal_id
reference_packet_id
role_tier_ids
body_plan_style_ids
pose_type
scale_reference
side_silhouette
front_silhouette
top_silhouette_optional
anatomy_parts
material_slots
socket_plan
collision_plan
lod_plan
operator_checks
```

## Drawing UI Fields

| Field | Purpose |
| --- | --- |
| `side_silhouette` | Main animal read; most animal identity comes from side view. |
| `front_silhouette` | Prevents paper-thin or confusing forms. |
| `spine_line` | Needed for quadrupeds, fish, snakes, and crouching amphibians. |
| `limb_anchor_points` | Keeps legs, wings, fins, and feet attached to source locations. |
| `head_direction` | Prevents animals from reading as generic blobs. |
| `tail_or_wing_path` | Captures the largest expressive secondary shape. |
| `body_section_profiles` | Lets the asset pump loft simple sections into a readable body. |
| `material_breaks` | Tells Blender where fur, feather, horn, hoof, scale, membrane, or wet skin begins. |
| `socket_locations` | Supports saddle, bridle, yoke, collar, perch, cage, cargo, trophy, or emblem conversion. |

## Blender Tool Sequence Pattern

Most starter animals should follow this order:

```text
block major masses
-> mirror paired anatomy
-> loft or curve body details
-> add species marker pieces
-> assign materials by part
-> bevel/weighted-normal finish
-> create collision proxy
-> create LOD variants
```

## Avoid

- starting with fur, feathers, scales, or noise before the silhouette works
- mixing animation behavior into taxonomy records
- adding high-density surface detail before LOD and lower-compute policies exist
- treating symbolic/statue animal variants as if they need living anatomy

## First Promotion Candidates

Good first generated assets:

1. `river_fish_v0`: simple lens body, tail fork, fins, and wet material.
2. `chicken_flock_bird_v0`: small bird body with beak, comb, legs, and flock LOD.
3. `snake_v0`: curve-driven body, head wedge, and belly strip.
4. `riding_horse_v0`: larger and harder, but valuable for stables, roads, and tack sockets.
