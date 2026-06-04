# 3D-LAB-0096 Implement ASCII Blender Dry-Run Zip V0

## Goal

Implement `ascii_blender_dryrun_v0.zip` directly, without rewriting the package
methods.

## Result

The archive was extracted into:

```text
ascii_blender_dryrun_v0/
```

The package code, examples, tests, and generated text/json/python examples were
preserved from the zip. No operation names, backend methods, validators, or
Blender emitter logic were rewritten.

## Verification

- Extracted files were compared byte-for-byte against `ascii_blender_dryrun_v0.zip`.
- Package source compiled with `python3 -m compileall`.
- CLI demo ran from the package folder.
- Extracted JSON files parsed.
- The bundled test assertions were run manually because `pytest` is not
  installed in the active Python environment.

## Boundary

This implements the zip package as-is. It does not yet connect the package to
`gameguy_ascii_plan_v0`, `gameguy_tool_plan_v0`, or the canonical asset pump.
