# ASCII Blender Dry-Run v0

This project lets you test a Blender-style architectural build plan in ASCII first.

The core idea is simple:

`Recipe is truth. ASCII preview is proof. Blender script is execution.`

Do not make Blender infer meaning from pixels. Write or compile a recipe, run it through the ASCII backend, validate it, then emit a Blender Python script.

## What this zip contains

- `ascii_blender_dryrun/ops.py`  
  Typed build operations such as `AddBox`, `AddCylinder`, `AddMoulding`, `AddRing`, and `CutFlutes`.

- `ascii_blender_dryrun/recipes.py`  
  A deterministic Doric column source recipe and compiled backend recipe.

- `ascii_blender_dryrun/profile_mouldings.py`
  Profile helpers that compile terms such as `fillet`, `torus`, `scotia`, `cavetto`, `bead`, `cyma`, `annulet`, and `echinus` into deterministic radius/z moulding points.

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

Open the `.txt` previews first. If they look wrong, fix the recipe before running Blender.

## Run tests

```bash
pip install -r requirements.txt
pytest
```

## Current limitations

This is v0. It intentionally stabilizes the recipe/backend contract before fancy geometry.

The Blender script currently emits primitive boxes, cylinders, revolved moulding profiles, flute cutters, taper, and entasis. Mouldings are source-term driven: recipes can use `AddProfileMoulding` sequences, and the compiler expands them into low-level `AddMoulding` radius/z points.

## Next slices

1. Add OBJ dry-run mesh output outside Blender.
2. Add ASCII/image reference parser that compiles into this same recipe format.
3. Add material passes for marble, limestone, sandstone, and aged stone.
4. Add recipe-owned export and preview directives for Blender runs.
5. Add more architectural profile presets for regional styles and period-specific orders.
