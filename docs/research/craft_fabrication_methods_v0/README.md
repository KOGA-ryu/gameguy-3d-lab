# Craft Fabrication Methods V0

This folder adds a fabrication-informed detail pass to the asset docs.

The goal is not to produce real shop drawings. The goal is to understand how
craftspeople make related real objects so the repo can choose better source
fields, drawing tags, Blender tools, and operator checks.

The source data is:

```text
data/architecture/taxonomy/craft_methods/craft_fabrication_methods_v0.json
```

Validate it with:

```bash
python3 scripts/validate_craft_fabrication_methods_v0.py
```

## Documents

- `craft_source_index_v0.md` records the reference sources used in this pass.
- `asset_family_fabrication_build_plans_v0.md` maps asset families to
  fabrication-informed modeling sequences.
- `operator_fabrication_handoff_v0.md` defines what the future UI/workcard
  should hand to the operator.
- `construction_method_source_index_v0.md` records broader source anchors for
  buildings, furniture, instruments, metalwork, ceramics, textiles, and related
  craft families.
- `cross_family_construction_method_research_v0.md` maps those construction
  methods into visible asset cues, source fields, Blender direction, and
  operator checks.

## Boundary

These notes are for prototype asset generation and Blender operator planning.
They are not structural advice, code compliance advice, museum conservation
instructions, shop drawings, or fabrication-ready dimensions.
