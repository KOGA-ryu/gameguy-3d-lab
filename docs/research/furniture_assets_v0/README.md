# Furniture Assets V0

This folder starts the furniture prop, style, and status-tier lane.

The machine-readable source is:

```text
data/asset_taxonomy/furniture_v0/furniture_asset_taxonomy_v0.json
```

Validate it with:

```bash
python3 scripts/validate_furniture_asset_taxonomy_v0.py
```

## What This Lane Does

- names furniture families such as seating, storage, tables, beds, reading
  desks, and workshop utility
- defines furniture caste/status tiers such as rough utility, common household,
  monastic/guild, merchant, noble, royal/ritual, scholarly/arcane, and
  ruin/salvage
- defines style sheets such as rough plank, joined oak frame, Gothic panelled,
  monastic plain, merchant display, noble textile, royal axis, and ruin repaired
- breaks starter furniture into visible anatomy
- maps parts to geometry dictionary terms and legal Blender tool IDs
- captures source fields and operator checks for future drawing/manual tools
- records lore book hooks so furniture can teach room hierarchy and craft terms

## Starter Furniture

- rough plank stool
- joined bench
- boarded chest or coffer
- trestle table
- panelled cupboard
- high-back chair
- canopy bed
- lectern or reading desk
- workbench and tool rack
- throne or court chair

## Documents

- `furniture_source_index_v0.md` lists source links and their repo use.
- `furniture_style_caste_system_v0.md` explains the status-tier/style model.
- `furniture_family_build_plans_v0.md` maps starter assets to build sequences.
- `furniture_lore_book_hooks_v0.md` captures player-facing book/detail hooks.
- `operator_furniture_handoff_v0.md` defines future UI/manual workcard fields.

## Boundary

This is game-asset planning only. It is not fabrication guidance, ergonomic
safety guidance, conservation guidance, historical authenticity proof, or active
generated-asset input.
