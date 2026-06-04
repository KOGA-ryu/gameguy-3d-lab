# Animation System V0

This folder starts the animation planning lane.

It is documentation only. It does not create rigs, actions, keyframes, Blender
files, game-engine animation controllers, or generated assets.

## Documents

- `animation_todo_list_v0.md` defines the staged TODO list before any asset is
  animated.
- `animation_taxonomy_v0.md` names animation families, motion types, rig levels,
  loop types, and source fields.
- `asset_family_animation_backlog_v0.md` maps architecture, furniture,
  instruments, food/drink, animals, mechanisms, props, and environment assets to
  likely animation needs.
- `per_asset_animation_workcard_template_v0.md` defines the workcard for one
  animated asset.
- `operator_animation_handoff_v0.md` defines what a future UI/manual Blender
  pass should capture.

## Boundary

Animation is downstream from source geometry:

```text
source asset recipe
-> deterministic geometry/tool plan
-> static asset validation
-> animation intent/workcard
-> rig/action/constraint pass
-> preview/export
```

If animation requires a different pivot, socket, separation, or mesh part, that
requirement should move back into the source recipe or tool plan.

## First Principle

Do not animate a bad asset to hide a missing shape. The asset must read in a
static pose first.
