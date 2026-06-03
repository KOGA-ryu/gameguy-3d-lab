# 3D-LAB-0044 Wrapped Profiled Plinth

## Result

Replaced the first plinth prototype's side-only extrusion with a true four-sided wrapped mesh.

The new compiler path is:

```text
railing_plinth_ogee_base_side_profile_v0
-> source profile ring stack
-> 8-point chamfered-square footprint per ring
-> ring-to-ring mesh faces
-> 1-segment bevel/chamfer finish
```

## Geometry

- Source control points: `14`
- Profile rings: `7`
- Footprint points per ring: `8`
- Initial mesh: `56` vertices, `50` faces
- Final rendered mesh after finish stack: `160` vertices, `324` edges, `166` faces
- Non-manifold edges: `0`
- Render: `/tmp/gameguy_profiled_plinth_detail_execution_v0_0044/tool_plan_execution_v0_workbench.png`

The visible corner chamfers are now source geometry from the footprint rings. The finishing bevel uses `segments: 1`, so it behaves as a small chamfer on the already-low-profile shape instead of smoothing the form into a rounded asset.

## Validation

```text
python3 -m unittest discover -s tests
124 tests passed

python3 scripts/validate_generation_pipeline_v0.py --json-report /tmp/gameguy_pipeline_0044_final.json
PASS generation pipeline validation: commands=32 json=238 include_blender=false

python3 scripts/validate_generation_pipeline_v0.py --include-blender --json-report /tmp/gameguy_pipeline_blender_0044_final.json
PASS generation pipeline validation: commands=46 json=238 include_blender=true

git diff --check
pass
```
