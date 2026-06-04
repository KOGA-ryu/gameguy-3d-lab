# ASCII Blender Dry-Run v0

This project lets you test a Blender-style architectural build plan in ASCII first.

The core idea is simple:

`Recipe is truth. ASCII preview is proof. Blender script is execution.`

Do not make Blender infer meaning from pixels. Write or compile a recipe, run it through the ASCII backend, validate it, then emit a Blender Python script.

## What this zip contains

- `ascii_blender_dryrun/ops.py`  
  Typed build operations such as `AddBox`, `AddCylinder`, `AddRing`, and `CutFlutes`.

- `ascii_blender_dryrun/recipes.py`  
  A deterministic Doric column recipe.

- `ascii_blender_dryrun/ascii_backend.py`  
  A dry-run backend that renders front, side, and top ASCII projections.

- `ascii_blender_dryrun/validators.py`  
  Boring but useful checks for names, dimensions, shaft/base/capital sanity, and flute configuration.

- `ascii_blender_dryrun/blender_backend.py`  
  Emits a Blender Python script from the same operation stream.

- `examples/doric_column_recipe_v0.json`  
  Example recipe JSON.

- `tests/test_dryrun.py`  
  Minimal tests for the recipe, ASCII backend, validation, and Blender emitter.

## Quick start

From the project folder:

```bash
python -m ascii_blender_dryrun.cli --demo --out out
```

This writes:

```text
out/compiled_recipe.json
out/validation_report.json
out/doric_front_preview.txt
out/doric_side_preview.txt
out/doric_top_preview.txt
out/build_doric_column_v0.py
```

Open the `.txt` previews first. If they look wrong, fix the recipe. Do not open Blender yet. Blender is not where bad plans go to become good plans. That is how one summons the time goblin.

## Run tests

```bash
pip install -r requirements.txt
pytest
```

## Current limitations

This is v0. It intentionally stabilizes the recipe/backend contract before fancy geometry.

The Blender script currently emits primitive boxes, cylinders, and rings. It marks flute cutting, taper, and entasis as TODO comments in the emitted script. That is deliberate. The ASCII dry-run needs to catch plan problems first.

## Next slices

1. Implement real shaft taper and entasis in Blender backend.
2. Implement radial flute boolean cutters.
3. Add OBJ dry-run mesh output outside Blender.
4. Add ASCII/image reference parser that compiles into this same recipe format.
5. Add material passes for marble, limestone, sandstone, and aged stone.
