# Generation Registry v0

This slice adds a single source registry for the deterministic generation surface.

## Registry

```text
data/architecture/asset_mill/asset_generation_registry_v0.json
```

The registry declares:

- canonical geometry recipe bundles consumed by `scripts/asset_pump_v0.py`
- the canonical tool-plan recipe bundle consumed by `scripts/compile_blender_tool_plan_v0.py`
- validators and Blender adapters that prove each generated JSON lane
- reference-only recipe bundles that are intentionally not pipeline inputs
- quality gates for pipeline validation, script orbit audit, and no repo-local generated outputs

## Added Gate

```bash
python3 scripts/validate_asset_generation_registry_v0.py
```

This validator checks registry paths, schemas, asset counts, expected tool count, compiler/validator boundaries, pipeline-label coverage, and reference-only recipe boundaries. It does not run the pump, run the tool-plan compiler, run Blender, or write generated media/mesh outputs.

## Current Evidence

```text
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 reference_only=3
PASS generation pipeline validation: commands=24 json=219 include_blender=false
PASS generation pipeline validation: commands=30 json=219 include_blender=true
PASS script orbit audit: scripts=73 KEEP_CANONICAL=15, CONVERT_TO_ADAPTER=0, REPLACE_BY_PUMP=0, REFERENCE_ONLY=58, DELETE_LATER=0
```

The registry records:

| Category | Count |
| --- | ---: |
| canonical geometry bundles | 5 |
| canonical geometry assets | 40 |
| canonical tool-plan bundle | 1 |
| asset-family sequence policies | 5 |
| default compiled tool plans | 3 |
| reference-only recipe bundles | 3 |

## Boundary

This registry is not a generator and not a Blender adapter. It is source-side proof that the repo has one declared canonical generation surface, plus explicit reference-only exclusions for older recipe shapes.
