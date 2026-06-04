# Per-Asset Animation Workcard Template V0

Use this template when one exact asset is ready for animation planning.

```yaml
animation_id:
asset_id:
asset_family:
reference_packet_id:
static_asset_status:
animation_role:
rig_level:
motion_source_type:
loop_type:

world_context:
  style_id:
  room_or_scene_role:
  gameplay_role:
  lore_role:

timing:
  frame_rate:
  start_frame:
  end_frame:
  loop_length_frames:
  hold_frames:
  contact_frames:
  audio_event_frames:
  collision_event_frames:
  random_start_offset_allowed:

moving_parts:
  - part_id:
    parent_part_id:
    motion_type:
    pivot_or_anchor:
    transform_axis:
    rest_pose:
    active_pose:
    forbidden_motion:

rig_or_constraint_plan:
  armature_needed:
  bones:
  constraints:
  shape_keys:
  drivers:
  curve_paths:
  simulation_proxy:

source_recipe_feedback:
  required_separate_parts:
  required_pivots:
  required_sockets:
  required_material_slots:
  collision_state_changes:
  lod_notes:

blender_workcard:
  tools_needed:
  action_names:
  marker_names:
  export_clip_names:
  preview_requirements:

operator_checks:
  - static asset reads before motion
  - moving parts do not clip
  - pivot is correct
  - loop start/end match
  - audio markers align
  - collision state is clear
  - low-compute fallback exists

do_not_do_yet:
  - 
```

## Example: Door

```yaml
animation_id: door_open_close_v0
asset_id: gothic_panel_door_v0
animation_role: interactive_state
rig_level: rig_level_1_object_transform
motion_source_type: keyframed_transform
loop_type: one_shot
moving_parts:
  - part_id: door_leaf
    motion_type: hinge_rotation
    pivot_or_anchor: left_hinge_axis
    transform_axis: z_rotation
    rest_pose: closed
    active_pose: open_92_degrees
source_recipe_feedback:
  required_separate_parts:
    - frame
    - door_leaf
    - hinge_straps
    - latch
```

## Example: Bell

```yaml
animation_id: bell_toll_loop_v0
asset_id: cast_bell_v0
animation_role: performance_loop
rig_level: rig_level_2_constraint_prop
motion_source_type: keyframed_transform
loop_type: beat_loop
moving_parts:
  - part_id: bell_body
    motion_type: swing_rotation
    pivot_or_anchor: crown_hinge_axis
  - part_id: clapper
    motion_type: delayed_swing
    pivot_or_anchor: clapper_socket
timing:
  audio_event_frames:
    - 12
    - 36
```

## Example: Drum

```yaml
animation_id: frame_drum_strike_loop_v0
asset_id: frame_drum_v0
animation_role: performance_loop
rig_level: rig_level_1_object_transform
motion_source_type: keyframed_transform
loop_type: beat_loop
moving_parts:
  - part_id: right_hand_or_beater_proxy
    motion_type: strike_arc
    pivot_or_anchor: wrist_or_beater_anchor
  - part_id: membrane
    motion_type: optional_shape_key_pulse
    pivot_or_anchor: membrane_center
```
