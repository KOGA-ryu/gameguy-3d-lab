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

- `ascii_blender_dryrun/sweep_geometry.py`
  Deterministic helpers for twisted/tapered section stacks and swept spiral paths.

- `ascii_blender_dryrun/petal_bloom_presets.py`
  Expands named floral presets into low-level `AddPetalBloom` operations before ASCII, validation, or Blender emission.

- `presets/petal_bloom_presets_v0.json`
  Named petal-bloom presets for open bloom, rose bud, floral boss relief, leaf cluster, and flame-petal roles.

- `ascii_blender_dryrun/ascii_backend.py`  
  A dry-run backend that renders front, side, and top ASCII projections.

- `ascii_blender_dryrun/validators.py`  
  Boring but useful checks for names, dimensions, shaft/base/capital sanity, and flute configuration.

- `ascii_blender_dryrun/blender_backend.py`  
  Emits a Blender Python script from the same operation stream.

- `examples/doric_column_recipe_v0.json`  
  Example recipe JSON.

- `examples/twisted_square_bar_recipe_v0.json`
  Straight section-stack proof for hot-metal twist, taper, and bulge behavior.

- `examples/rose_scroll_sweep_recipe_v0.json`
  Curved path-sweep proof for filigree, rose, scroll, vine, and bent-glass behavior.

- `examples/layered_rose_bloom_recipe_v0.json`
  Layered petal-surface proof for rose bosses, leaves, floral caps, curled plates, and bloom-like ornament.

- `examples/spiral_rose_bud_recipe_v0.json`
  Denser petal-bloom variant with blunter petals, stronger overlap, higher inner curls, and tighter spiral-bud behavior.

- `examples/preset_spiral_rose_bud_recipe_v0.json`
  Source-side preset reference example. It names `spiral_rose_bud_v0` and applies small petal/layer overrides before compilation.

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

The Blender script currently emits primitive boxes, cylinders, revolved moulding profiles, flute cutters, taper, entasis, straight section stacks, swept spiral paths, and layered petal blooms. Mouldings are source-term driven: recipes can use `AddProfileMoulding` sequences, and the compiler expands them into low-level `AddMoulding` radius/z points.

`AddSectionStack` is for solid twisted/tapered cross-section meshes such as balusters, hot-twisted bars, square-to-round transitions, mace shafts, and ribbed posts.

`AddPathSweep` is for bent ornamental strands such as filigree, rose scrolls, vines, ironwork curls, and glass-like bends.

`AddPetalBloom` is for sheet-like ornamental surfaces such as rose petals, leaves, floral bosses, curled plates, and layered reliefs. Its recipe owns the skinny-wide-skinny petal width curve, thickness curve, bend start, layer counts, layer scale, spiral offsets, curl, and petal twist.

`AddPetalBloomPreset` is a source-side shortcut for reusable petal roles. It references one preset from `presets/petal_bloom_presets_v0.json`, then optional `petal_overrides` and indexed `layer_overrides` are applied before the compiler emits ordinary `AddPetalBloom`.

## Next slices

1. Add OBJ/GLB dry-run mesh output outside Blender.
2. Add ASCII/image reference parser that compiles into this same recipe format.
3. Add material passes for marble, limestone, sandstone, aged stone, iron, and glass.
4. Add recipe-owned export and preview directives for Blender runs.
5. Add path families beyond spiral: Bezier strokes, arches, S-scrolls, leaves, and tracery ribs.
