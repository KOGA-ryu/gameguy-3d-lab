# 3D-LAB-0090 Animation TODO V0

## Goal

Add a documentation-only animation planning lane with TODOs, taxonomy, asset
family backlog, per-asset workcard template, and operator handoff.

## Added

- `docs/research/animation_system_v0/README.md`
- `docs/research/animation_system_v0/animation_todo_list_v0.md`
- `docs/research/animation_system_v0/animation_taxonomy_v0.md`
- `docs/research/animation_system_v0/asset_family_animation_backlog_v0.md`
- `docs/research/animation_system_v0/per_asset_animation_workcard_template_v0.md`
- `docs/research/animation_system_v0/operator_animation_handoff_v0.md`

## Updated

- `README.md`
- `docs/research/documentation_map_v0/documentation_backlog_v0.md`

## Coverage

- animation intent phases
- static asset readiness before motion
- motion models and rig levels
- timing and loop fields
- rig/source-feedback requirements
- architecture, dungeon, furniture, instruments, food/drink, animals,
  accessories, clothing, armor, weapons, textures, VFX, and material animation
  backlog
- per-asset workcard template
- Blender animation/rigging tool groups to research later
- low-compute animation policy

## Boundary

This is documentation planning only. It does not create rigs, actions,
keyframes, Blender files, generated meshes, game-engine controllers, or playable
audio.

## Validation

```text
python3 -m json.tool workflow/reports/3D-LAB-0090-animation-todo-v0/receipt.json
PASS

git diff --check
PASS
```

## Recommended Next Goal

Promote one very small animation intent only when the first implementation slice
starts. Best first candidates are `door_open_close_v0`, `bell_toll_loop_v0`, or
`lever_pull_v0`.
