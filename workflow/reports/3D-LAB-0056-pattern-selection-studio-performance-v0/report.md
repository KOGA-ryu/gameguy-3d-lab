# 3D-LAB-0056 Pattern Selection Studio Performance v0

## Result

Reduced the default browser load for the manual pattern selection studio.

```text
dense segment graph
-> prioritized light render subset
-> manual selection/coloring
-> deterministic selection recipe JSON
```

## Source Decisions

- The source segment graph still contains all `14,324` segments.
- The studio now opens at `light` detail and renders `1,200` prioritized lines by default.
- Normal, dense, and full detail remain available from the Detail selector.
- Segment interaction now uses delegated events on the SVG layer instead of per-line listeners.
- Intersections are rendered lazily only when the Intersections toggle is enabled.
- Select/clear operations apply to the currently rendered subset.
- No Blender, mesh, material, or generation-pipeline behavior is touched.

## Validation

```text
python3 -m py_compile scripts/serve_pattern_selection_studio_v0.py
PASS

python3 -m unittest tests/test_pattern_selection_studio_v0.py
OK, 4 tests

python3 scripts/serve_pattern_selection_studio_v0.py --validate-only
PASS pattern selection studio validation: segment_set=hex_rosette_pattern_segments_v0 segments=14324 default_selection=hex_rosette_user_selection_v0

Browser smoke:
detail=1200
renderedLines=1200
matching=14324
intersectionsRendered=0
click selection readout selected=1
reset readout selected=0
```

## Next

Use the lighter studio to select the first motif safely, then compile a kept/omitted line preview from the saved recipe.
