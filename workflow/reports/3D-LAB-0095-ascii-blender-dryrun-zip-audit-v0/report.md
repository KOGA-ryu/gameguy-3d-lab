# 3D-LAB-0095 ASCII Blender Dry-Run Zip Audit V0

## Goal

Inspect the local `ascii_blender_dryrun_v0.zip` archive and decide whether it
belongs in the canonical ASCII-to-Blender pipeline.

## Result

The archive is useful as reference, but it should not be imported wholesale.

Accepted ideas:

- typed dry-run operation stream
- cheap front/side/top ASCII projection
- validation before Blender
- Blender script emitter as downstream adapter

Rejected as canonical source:

- visual-only ASCII previews
- generated `out/` files
- Python cache files
- a side package that bypasses `gameguy_ascii_plan_v0`

## Decision

Use the prototype as design evidence for a future compiler:

```text
gameguy_ascii_plan_v0
-> ascii_region_compile_v0
-> dryrun_operation_stream_v0
-> ASCII projection plus QC report
-> gameguy_tool_plan_v0
-> Blender adapter
```

## Validation

- Zip listing inspected.
- SHA-256 recorded.
- Demo CLI executed from a temporary extraction.
- Python source compile check passed from temporary extraction.
- Bundled pytest suite was not run because `pytest` was not installed in the
  active Python environment.
- Existing repo ASCII plan validator still expected to remain canonical.
