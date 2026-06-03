# Blender Execution Report Validator v0

This slice adds a standalone validation gate for Blender execution quality reports.

The path is:

```text
compiled gameguy_tool_plan_v0
-> Blender execution adapter
-> blender_tool_plan_execution_report_v0
-> report validator
```

## Added Gate

The new validator is:

```bash
python3 scripts/validate_blender_tool_plan_execution_report_v0.py \
  --report /tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json
```

It validates that the execution report proves:

- The adapter consumed `gameguy_tool_plan_v0`.
- The adapter did not read source intent recipes, run the compiler, import the asset pump, or contain source design logic.
- All planned steps executed with no skipped steps.
- Material regions were preserved for base, cap, shaft, rib, and socket shadow roles.
- Socket booleans targeted `post_core`, used the exact solver, applied two modifiers, had zero failures, created two socket shadow panels, and removed cutters.
- Topology validation reports `0` non-manifold edges.
- Render, blend, and export paths do not point inside the repo.

## Current Evidence

Validated report:

```text
/tmp/gameguy_blender_tool_plan_execution_v0/tool_plan_execution_v0_report.json
```

Current measured result:

- Steps: `32`
- Non-manifold edges: `0`
- Material roles: `5`
- Socket shadow panels: `2`
- Generated outputs in repo: `false`

The validator is normal Python. It does not import Blender or create media/mesh artifacts.

## Boundary

This is a report gate, not a generator. Blender remains an adapter layer, and source design decisions remain in source recipes and deterministic compiler output.
