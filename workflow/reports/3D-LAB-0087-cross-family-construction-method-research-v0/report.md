# 3D-LAB-0087 Cross-Family Construction Method Research V0

## Goal

Research construction and craft methods across buildings, furniture, musical
instruments, metalwork, ceramics, textiles, leather-like accessories, and woven
natural forms, then map those methods into future source fields and Blender
planning language.

## Added

- `docs/research/craft_fabrication_methods_v0/construction_method_source_index_v0.md`
- `docs/research/craft_fabrication_methods_v0/cross_family_construction_method_research_v0.md`

## Updated

- `docs/research/craft_fabrication_methods_v0/README.md`

## Coverage

- masonry walls and lime mortar/repointing
- timber-framed buildings
- thatch, slate, tile, and metal roof details
- plaster/stucco/render
- frame-and-panel furniture
- carved furniture and sculpture-like woodwork
- bentwood furniture
- veneer, marquetry, inlay, and upholstery
- lute/oud/guitar-like instruments
- harp/lyre-like instruments
- drums, wind instruments, and cast bells
- forged/cast/chased/engraved/soldered metalwork
- ceramic vessels and molded/pierced ceramics
- woven cloth, tapestry, embroidery, and leather-like accessory construction
- wattle, basketry, rope, and woven natural forms

## Boundary

This is source research for game-asset planning only. It is not structural
guidance, code compliance advice, conservation treatment instruction, animal
care guidance, or fabrication-ready shop drawings.

## Validation

```text
python3 -m json.tool workflow/reports/3D-LAB-0087-cross-family-construction-method-research-v0/receipt.json
PASS

python3 scripts/validate_craft_fabrication_methods_v0.py
PASS craft fabrication method validation: methods=10 geometry_terms=75 tools=97

git diff --check
PASS
```

## Recommended Next Goal

Promote the highest-value method records into machine-readable data only when a
specific asset family needs them. Good first candidates are
`frame_panel_furniture_joinery_v0`, `lute_ribbed_bowl_soundboard_v0`,
`drum_shell_membrane_tension_v0`, and `traditional_roof_layering_v0`.
