# Measured Molding Profile v0

This slice promotes the user's column and compound-pier reference images into a source-profile layer.

## Source Path

```text
user-supplied reference images
-> measured molding / compound pier source profiles
-> source profile validator
-> registry + pipeline validation
-> future profile-driven tool plan
```

## Change

Added `measured_molding_profiles_v0.json` as source-only data for:

```text
column_cap_cyma_profile_v0
fluted_shaft_channel_cross_section_v0
column_base_torus_side_profile_v0
plinth_ogee_side_profile_v0
compound_pier_lobed_cross_section_v0
```

Each profile records reference ownership, local coordinate space, measured centimeter or normalized hints, geometry dictionary terms, operations, candidate Blender tools, and false claim flags.

## Validation

The new validator checks:

```text
profile_count matches profiles length
reference IDs resolve
profile family matches coordinate space
measurement hints are positive finite numbers
profile and operation terms exist in geometry_dictionary
candidate Blender tools exist in blender_tool_dictionary_v0
source-only and no-claims boundaries are preserved
```

Current evidence:

```text
PASS measured molding profile validation: profiles=5 references=2 tools=11
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=5 reference_only=3
PASS generation pipeline validation: commands=30 json=232 include_blender=false
PASS generation pipeline validation: commands=44 json=232 include_blender=true
```

## Boundary

This does not generate a column, post, rail, or pier yet. The next useful slice is to let the tool-plan compiler consume these source profiles so the Blender adapter can build a square plinth, molded base, fluted shaft, molded cap, and compound-pier/lobed cross-section from source-owned profile data.
