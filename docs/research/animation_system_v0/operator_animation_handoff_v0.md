# Operator Animation Handoff V0

This handoff defines what the future UI/manual Blender pass should capture for
animation work.

## Minimum Handoff

```text
asset_id
animation_id
static_preview
moving_part_list
pivot/anchor list
motion role
rig level
timing/loop fields
audio/collision/state markers
preview requirements
operator checks
source recipe feedback
```

## UI Fields To Support

Object motion:

- `part_id`
- `pivot_point`
- `hinge_axis`
- `slide_axis`
- `rotation_axis`
- `rest_transform`
- `active_transform`
- `motion_range`
- `hold_frames`

Rig motion:

- `bone_id`
- `parent_bone_id`
- `joint_limit`
- `ik_target_optional`
- `weight_group`
- `deformation_region`
- `forbidden_deformation_region`

Timing:

- `frame_rate`
- `start_frame`
- `end_frame`
- `loop_type`
- `contact_frames`
- `audio_event_frames`
- `state_event_frames`
- `random_offset_allowed`

Preview:

- `preview_camera`
- `show_pivots`
- `show_collision`
- `show_lod`
- `playblast_required`
- `loop_check_required`

## Blender Tool Groups To Research/Add Later

Animation authoring:

- keyframe insertion
- graph editor/f-curve edits
- action creation
- NLA strip organization
- timeline markers
- pose library

Rigging:

- armature creation
- bone parenting
- object-to-bone parenting
- vertex groups
- weight painting
- IK/FK constraints
- limit rotation/scale/location constraints
- copy/track constraints

Deformation:

- shape keys
- lattice deformation
- curve follow
- simple deform
- cloth/rope/rigid-body proxy only after pipeline policy exists

Export/validation:

- animation clip export
- action naming
- loop frame validation
- nonblank animation preview
- transform explosion check
- clipping check
- event marker export

## Source Feedback Rules

If the operator has to change any of these, update source data later:

- moving parts are fused
- pivot is wrong
- hinge axis is missing
- socket is missing
- origin is wrong
- material slot disappears during motion
- collision proxy cannot represent open/closed state
- LOD removes a moving part too early
- animation requires a hidden helper object

## Low-Compute Animation Policy

- ambient loops must be optional
- tiny repeated prop animations must allow random offset or disable
- decals are not required for motion readability
- creature locomotion should have static/pose fallback
- performance loops should keep the visible sound source even if finger detail is
  disabled
- simulation-heavy animation needs proxy or static fallback

## Review Checklist

Before accepting an animation:

- static asset reads correctly
- moving parts are named
- pivots are visible and correct
- start/end frames are defined
- loop type is correct
- no obvious clipping
- no unintentional scaling/shearing
- audio markers align with visible cause
- collision state is documented
- lower-compute fallback exists
- source recipe feedback is recorded
