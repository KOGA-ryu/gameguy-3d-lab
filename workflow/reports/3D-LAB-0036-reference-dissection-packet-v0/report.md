# Reference Dissection Packet v0

This slice adds the first reference-led asset dissection packet for the gothic panel guard direction.

## Source Path

```text
external morphology reference
-> data/architecture/asset_mill/reference_packets/gothic_panel_guard_reference_v0.json
-> scripts/validate_reference_dissection_packet_v0.py
-> future source recipe / tool plan
```

## Reference

The packet uses the Pexels reference:

```text
Historic Gothic Architectural Stone Balcony
https://www.pexels.com/photo/historic-gothic-architectural-stone-balcony-31473119/
```

The packet stores the page URL, image URL, author name, access date, and use policy. It is morphology-reference-only and does not copy image pixels, texture data, or mesh geometry.

## Dissection

The packet breaks the reference into nine source components:

```text
left_square_pier
right_square_pier
pier_pointed_arch_recess
slab_cap_and_base_stack
small_top_finial
center_solid_guard_panel
top_coping_rail
lower_molding_stack
repeated_side_ornament_strips
```

Each component declares visible shape notes, generation role, geometry dictionary terms, and candidate Blender tools. V0 tool choices must be deterministic; nondeterministic sculpt/paint tools are allowed only in `future_reference_only_tools`.

## Current Evidence

```text
PASS reference dissection packet validation: components=9 tools=12 terms=9
PASS generation pipeline validation: commands=28 json=228 include_blender=false
PASS generation pipeline validation: commands=40 json=228 include_blender=true
```

## Boundary

This is not a generated asset and not a code-compliant railing claim. It is a shared reference contract for discussion, Blender vocabulary, and the next generated asset slice.
