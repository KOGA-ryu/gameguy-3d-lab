# Animation TODO List V0

This is the staged TODO list for preparing animation work.

## Phase 1: Name The Animation Intent

- Choose the exact animated asset.
- Decide whether motion is decorative, interactive, mechanical, creature,
  performance, environmental, UI/readable, or gameplay-critical.
- Name the animation with a stable ID.
- Define the motion role:
  - `idle_loop`
  - `activation`
  - `deactivation`
  - `open_close`
  - `cycle_loop`
  - `impact_react`
  - `use_interaction`
  - `performance_loop`
  - `ambient_loop`
  - `state_transition`
  - `inspection_pose`
- Define whether animation needs audio, VFX, collision changes, or gameplay
  state changes.

## Phase 2: Prove The Static Asset Is Ready

- Check the asset silhouette from gameplay distance.
- Confirm moving parts are separate named pieces.
- Confirm pivots/origins exist where motion should happen.
- Confirm sockets/anchors are explicit.
- Confirm material slots survive motion.
- Confirm collision proxy can either remain static or switch state.
- Confirm LOD rules exist before detail animation.

If moving parts are fused, stop and fix source geometry first.

## Phase 3: Choose The Motion Model

Pick one primary model:

- `object_transform`: move/rotate/scale whole objects.
- `hinge_or_pivot`: doors, lids, levers, bells, handles, shutters.
- `sliding_track`: drawers, bolts, portcullises, gates, latches.
- `looped_rotation`: wheels, cranks, gears, spit rods, winches.
- `curve_follow`: ropes, chains, snakes, banners, smoke trails.
- `skeletal_rig`: characters, animals, cloth-adjacent props, complex hands.
- `shape_key`: blinking, facial motion, bellows, soft deformation.
- `constraint_rig`: mechanical linkages, straps, bell clappers, pulley systems.
- `simulation_proxy`: cloth, rope, rigid-body, or fluid-like effects only when
  later systems allow it.

## Phase 4: Define Timing

- Set frame rate.
- Set loop length.
- Set beats, holds, anticipations, impacts, and recoveries.
- Mark start/end pose.
- Mark whether the loop must be seamless.
- Mark whether it can be random-offset per instance.
- Mark audio sync points.
- Mark collision on/off frames if needed.

Suggested first timing fields:

```text
frame_rate
start_frame
end_frame
loop_type
hold_frames
contact_frames
audio_event_frames
state_event_frames
random_start_offset_allowed
```

## Phase 5: Define Rig Requirements

- List moving objects.
- List pivots.
- List bones if skeletal.
- List constraints.
- List parent/child hierarchy.
- List driver relationships.
- List IK/FK needs if relevant.
- List shape keys if relevant.
- List forbidden deformation zones.

For props, prefer object transforms and constraints before skeletal rigs.

## Phase 6: Define Animation States

Minimum state fields:

```text
default_pose
animated_pose
rest_pose
active_state
inactive_state
damaged_state_optional
blocked_state_optional
inspection_state_optional
```

State examples:

- door: closed, opening, open, closing, locked, broken
- bell: idle, ringing, tolling, cracked
- animal: idle, walk, alert, flee, sleep, statue variant
- instrument: held idle, performance loop, broken/silent, display stand
- food/drink: steam loop optional, spill event, fill/empty state
- machinery: idle, crank loop, jammed, reset

## Phase 7: Define Export/Engine Needs

- Name animation clips/actions.
- Decide whether animation exports with asset or separate action data.
- Decide whether collision switches or stays separate.
- Define root motion policy.
- Define looping policy.
- Define event markers.
- Define whether motion must be deterministic.
- Define if motion is allowed on lower-compute hardware.

## Phase 8: Prepare Preview Requirements

Each animated asset needs:

- static frame screenshot
- motion preview
- one close preview
- one gameplay-distance preview
- one viewport/camera angle that shows pivots
- nonblank frame check
- loop start/end frame check
- no obvious clipping check
- no exploding transform check

## Phase 9: Capture Corrections

- Record what looked wrong.
- Record whether the fix was geometry, pivot, rig, timing, curve, or material.
- Record the Blender tool/action used.
- Convert repeated corrections into source fields.
- Move source-owned requirements back into asset recipes or tool plans.

## First Implementation Candidates

Start with assets that require almost no rigging:

1. `door_open_close_v0`: hinge/pivot rotation.
2. `bell_toll_loop_v0`: bell/clapper/rope relationship.
3. `portcullis_raise_lower_v0`: sliding track and chain/winch cue.
4. `cauldron_steam_optional_v0`: optional low-cost ambient loop.
5. `lute_performance_pose_v0`: hand-zone and string anchor planning only.
6. `snake_curve_idle_v0`: curve-follow or shape-key test after static source is
   correct.

Do not start with a full animal walk cycle. That should come after pivots,
skeleton conventions, and static pose sheets exist.
