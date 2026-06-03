# Asset-Family Tool Sequence Policy v0

This slice adds a source-side policy for choosing Blender tools in the right sequence by asset family.

## Source Path

```text
asset intent recipe
+ blender_tool_dictionary_v0
+ asset_family_tool_sequence_policy_v0
-> scripts/compile_blender_tool_plan_v0.py
-> deterministic gameguy_tool_plan_v0 JSON
-> scripts/validate_gameguy_tool_plan_v0.py
-> Blender adapter
```

## Added Policy

```text
data/architecture/asset_mill/blender_tools/asset_family_tool_sequence_policy_v0.json
```

The policy covers five target asset families:

| Asset family | Role |
| --- | --- |
| `column` | Sectioned posts, fluted/star/ribbed shafts, square/circular transitions |
| `banister_post` | Socketed rail posts and sculpted stone posts |
| `fence_post` | Rail-bearing exterior posts |
| `window_frame` | Rectangular or arched frame assemblies |
| `door_frame` | Threshold/header/jamb frame assemblies |

Each family declares dictionary family tags, allowed features, required stage coverage, legal tools by stage, required tools, forbidden tools, and before/after ordering constraints.

## Enforcement

The compiler now loads the sequence policy by default and rejects source recipes that would compile into illegal family sequences.

The `gameguy_tool_plan_v0` validator now loads the same policy and rejects hand-edited compiled plans that violate family tool legality or order constraints before Blender can execute them.

The generation registry now declares the sequence policy as part of the canonical tool-plan bundle.

## Current Evidence

```text
compiled tool plans=2 steps=57 tools=97 out=<validate-only>
PASS gameguy_tool_plan_v0 validation: 2 plans, 57 steps, 24 tools
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 reference_only=3
PASS generation pipeline validation: commands=23 json=218 include_blender=false
PASS generation pipeline validation: commands=27 json=218 include_blender=true
```

Focused tests prove:

- `5` asset-family policies are present.
- Current banister and window-frame plans declare `asset_family_tool_sequence_policy_v0`.
- A window-frame recipe cannot add the banister-only `east_west_rail_sockets` feature.
- A hand-edited window-frame plan cannot use `primitive_cylinder_add`.
- A hand-edited banister plan cannot move socket booleans before radial rib duplication.

## Boundary

This policy does not execute Blender, does not generate media or mesh files, and does not move source design decisions into the Blender adapter. It constrains source-to-tool-plan compilation and compiled-plan validation.
