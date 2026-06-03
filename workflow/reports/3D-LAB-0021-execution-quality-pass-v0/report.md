# Blender Tool Plan Execution Quality Pass v0

This slice improves the first `gameguy_tool_plan_v0` Blender execution adapter without moving source design decisions into Blender.

The path remains:

```text
source intent recipe
-> deterministic gameguy_tool_plan_v0 JSON
-> Blender execution adapter
-> report / preview / export under /tmp
```

## Changes

- The compiler now emits explicit socket boolean settings: `targets`, `solver`, cutter cleanup, and socket shadow-panel parameters.
- The join step now includes generated `socket_shadows` from the plan.
- The material assignment step preserves existing polygon material indexes and remaps role slots to named gothic-stone variants.
- The executor report now includes `material_regions`, `socket_pass`, `topology_cleanup`, and `quality_pass` evidence.
- The current blocky post plan uses a zero-distance weld pass so loose block parts are not accidentally merged into non-manifold internal faces before a source-planned union cleanup exists.

## Execution Evidence

Execution report:

```text
/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json
```

Current measured result:

- Plan: `gothic_stone_banister_post_tool_plan_v0_compiled`
- Steps executed: `32`
- Unique tools used: `24`
- Skipped steps: `0`
- Mesh objects: `3`
- Final object vertices: `1225`
- Final object faces: `1158`
- Final object material slots: `6`
- Socket boolean modifiers applied: `2`
- Socket boolean failures: `0`
- Socket shadow panels created: `2`
- Socket cutters removed: `true`
- Non-manifold edge count before cleanup: `0`
- Non-manifold edge count after cleanup: `0`

Material face counts by role:

```text
base: 158
cap: 106
rib: 626
shaft: 115
socket_shadow: 153
```

Generated outputs remain outside the repo:

- Preview: `/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_workbench.png`
- Blend: `/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0.blend`
- GLB: `/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0.glb`

## Boundary

The Blender adapter still consumes compiled deterministic JSON. It does not read the source intent recipe, run the compiler, import the asset pump, or choose source design steps.

This does not make production, fabrication, structural, historical accuracy, approval, or game-engine integration claims.
