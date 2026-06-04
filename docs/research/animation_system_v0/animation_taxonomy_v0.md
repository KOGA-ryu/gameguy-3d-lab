# Animation Taxonomy V0

This taxonomy gives names to animation work before implementation.

## Animation Role Families

| Role | Meaning | Examples |
| --- | --- | --- |
| `ambient_loop` | background life, not gameplay-critical | torch flicker, hanging sign sway, steam, bats in distance |
| `mechanical_cycle` | repeating machine motion | wheel, crank, winch, water wheel, bellows |
| `interactive_state` | player/system changes state | door open, chest lid, lever pull, gate raise |
| `performance_loop` | visible playing or ritual action | lute plucking, drum pattern, bell ringing, chanting posture |
| `creature_locomotion` | moving body through space | walk, trot, fly, swim, slither |
| `creature_pose_loop` | mostly stationary living motion | idle, breathing, looking, sleeping, eating |
| `physics_like_secondary` | small follow-through motion | rope, cloth, tassel, strap, hanging chain |
| `damage_react` | break, hit, collapse, or impact reaction | crate break, wall crumble, shield impact |
| `inspection_motion` | close-view rotation or reveal | book opening, object turn, secret panel reveal |
| `cinematic_or_scripted` | authored sequence | ritual scene, feast arrival, siege gate moment |

## Rig Complexity Levels

| Level | Name | Use |
| --- | --- | --- |
| `rig_level_0_static_pose` | no animation | object has source pose only |
| `rig_level_1_object_transform` | object transforms | doors, lids, levers, bells, shutters |
| `rig_level_2_constraint_prop` | linked transforms/constraints | pulleys, winches, clappers, bellows, cranks |
| `rig_level_3_shape_key_soft` | shape keys/simple deformation | bellows, cloth-like sag, face/eye hints |
| `rig_level_4_curve_motion` | curve paths/deforming curves | ropes, chains, snakes, banners, scrolls |
| `rig_level_5_skeletal_simple` | simple armature | animals, hands, character-held props |
| `rig_level_6_skeletal_complex` | IK/FK/constraints/deformation | full creature or character performance |
| `rig_level_7_simulation_proxy` | sim/cache/proxy-driven | cloth, rigid bodies, fluids, complex secondary motion |

Repo rule:

```text
prefer the lowest rig level that gives the required visual read
```

## Motion Source Types

- `keyframed_transform`
- `keyframed_shape_key`
- `bone_pose`
- `constraint_driver`
- `curve_path_motion`
- `procedural_cycle`
- `physics_cache`
- `state_event`
- `audio_synced_marker`

## Loop Types

- `one_shot`: plays once, such as lever pull.
- `ping_pong`: moves out and back, such as small sway.
- `seamless_loop`: last frame returns cleanly to first.
- `hold_loop`: loop with deliberate pauses.
- `random_offset_loop`: same loop can start at random frames per instance.
- `state_loop`: idle/open/closed/active loops depend on state.
- `beat_loop`: timing is tied to rhythm or music.
- `event_loop`: motion fires events such as sound, collision, or VFX.

## Pivot And Anchor Terms

| Term | Meaning |
| --- | --- |
| `origin` | object transform center |
| `pivot` | intentional rotation or scale center |
| `hinge_axis` | line a door/lid/shutter rotates around |
| `slide_axis` | axis a gate/drawer/bolt moves along |
| `rotation_axis` | wheel, crank, bell, or spool axis |
| `contact_point` | frame where foot, hand, beater, clapper, or tool contacts |
| `socket_anchor` | source-owned connection point |
| `grip_anchor` | hand/character holding point |
| `sound_anchor` | part that produces or explains a sound |
| `collision_state_anchor` | point/part tied to collision change |

## Source Fields

Minimum fields for a future `animation_intent_v0` record:

```json
{
  "animation_id": "",
  "asset_id": "",
  "animation_role": "",
  "rig_level": "",
  "motion_source_type": "",
  "loop_type": "",
  "frame_rate": 24,
  "start_frame": 1,
  "end_frame": 48,
  "moving_parts": [],
  "pivot_points": [],
  "anchors": [],
  "state_names": [],
  "audio_event_frames": [],
  "collision_event_frames": [],
  "operator_checks": [],
  "low_compute_policy": ""
}
```

## Blender Tooling TODO

The current Blender tool dictionary is geometry-heavy. Animation will need a
separate tool dictionary or an extension with entries such as:

- `armature_add`
- `bone_create`
- `parent_to_bone`
- `weight_paint`
- `vertex_group_assign`
- `shape_key_add`
- `shape_key_keyframe`
- `keyframe_insert`
- `fcurve_edit`
- `action_create`
- `nla_strip_create`
- `constraint_copy_transform`
- `constraint_track_to`
- `constraint_limit_rotation`
- `constraint_follow_path`
- `driver_add`
- `timeline_marker_add`
- `camera_preview_animation`
- `export_animation_clip`

Do not add these to source recipes until an animation compiler or adapter exists.
