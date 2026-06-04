# ASCII Blender Dry-Run Zip Audit V0

## Source

Local incoming archive:

```text
ascii_blender_dryrun_v0.zip
```

Audit hash:

```text
cfc6466196a1b43cbb8c0009be742596d7b71438f6a3040a5b5d3b7192e1e589
```

The archive was first inspected as local reference material. It was then
implemented directly after the user explicitly requested the zip code be used
exactly instead of being reinterpreted.

Implemented package path:

```text
ascii_blender_dryrun_v0/
```

## Contents

The useful source files are:

- `ascii_blender_dryrun/ops.py`
- `ascii_blender_dryrun/recipes.py`
- `ascii_blender_dryrun/ascii_backend.py`
- `ascii_blender_dryrun/validators.py`
- `ascii_blender_dryrun/blender_backend.py`
- `ascii_blender_dryrun/cli.py`
- `examples/doric_column_recipe_v0.json`
- `tests/test_dryrun.py`

The archive also contains `out/` previews, a generated Blender script, and
`__pycache__/` files. Those are build artifacts, not source.

## What It Gets Right

The archive has the correct high-level split:

```text
typed recipe operations
-> ASCII dry-run projection
-> validation report
-> Blender script emitter
```

This is aligned with the repo direction because Blender is treated as an
execution target instead of the place where source design decisions are made.

The useful ideas to keep are:

- a typed operation stream that multiple backends can consume
- front, side, and top cheap previews before Blender
- a blunt validation pass before execution
- a script emitter that does not import `bpy` during source planning

## What It Does Not Solve Yet

The prototype does not satisfy `gameguy_ascii_plan_v0` by itself.

Missing pieces:

- ASCII cells do not carry stable cell IDs.
- Glyphs do not own source-pixel bounding boxes.
- Glyphs do not own model-space X/Z bounding boxes.
- Regions are not first-class source objects.
- Blender tool hints are not attached at the cell or region level.
- The ASCII previews are visual-only text, not selectable measurement ledgers.
- The Blender backend still leaves taper, entasis, and flute cutting as
  placeholders.

The top projection also shows a structural limitation: later broad square
objects can overwrite the readable footprint of circular and fluted parts. A
future dry-run renderer needs a layer stack, region ownership, and optional
per-region projections instead of one flattened character canvas.

## Integration Decision

The package is implemented exactly as a standalone dry-run prototype. Its code
is not rewritten into repo-native operation names or compiler methods.

The package can be run from its own folder:

```bash
python3 -m ascii_blender_dryrun.cli --demo --out out
```

The measured ASCII plan remains the source-planning contract for future repo
work. The direct package implementation should be treated as an executable
prototype beside that contract, not as a replacement for cell-level measurement
metadata.

Future integration boundary:

```text
gameguy_ascii_plan_v0
-> ascii_region_compile_v0
-> dryrun_operation_stream_v0
-> ASCII projection plus QC report
-> gameguy_tool_plan_v0
-> Blender adapter
```

## Operation Crosswalk

| Prototype op | Repo interpretation | Blender role |
| --- | --- | --- |
| `AddBox` | block mass, plinth, slab, cap, rail socket blockout | cube primitive or mesh profile extrusion |
| `AddCylinder` | shaft, round post, column core | cylinder primitive, spin/revolve, or mesh section stack |
| `AddRing` | torus-like collar, necking ring, lip, bead | cylinder band, bevelled ring, or lathed profile |
| `CutFlutes` | repeated recessed shaft channels | cutter profile plus radial array plus boolean difference |
| `AddLabel` | QC annotation only | non-geometry note or hidden label object |

## Rules For The Real Version

1. ASCII source plans must stay measurement-backed.
2. A glyph cannot become geometry unless its region is accepted for generation.
3. Visual preview text is proof, not source.
4. Dry-run operation streams must be deterministic JSON.
5. Blender emitters can consume approved tool plans only.
6. Broad mass layers must not destroy detail evidence; projections need region
   IDs and layer ordering.
7. Render contracts stay blocked until ASCII/source QC passes.

## Next Slice

Build a small compiler from the existing tiny fixture:

```text
single_post_ascii_plan_fixture_v0.json
-> dryrun_operation_stream_v0.json
-> front/side/top ASCII previews
-> dryrun QC report
```

That compiler should use measured regions from `gameguy_ascii_plan_v0` and emit
only deterministic JSON and text previews. Blender remains downstream.
