# Accessory Assets V0

This folder starts the wearable and carried accessory prop lane.

The machine-readable source is:

```text
data/asset_taxonomy/accessories_v0/accessory_asset_taxonomy_v0.json
```

Validate it with:

```bash
python3 scripts/validate_accessory_asset_taxonomy_v0.py
```

## What This Lane Does

- names accessory families such as belts, pouches, jewelry, keys, hanging
  utility, weapon suspension, scholarly smallware, and travel containers
- defines accessory status tiers for common wear, guild trade, merchant display,
  noble court, ritual/arcane, military/guard, rogue/traveler, and ruin salvage
- defines reusable styles such as plain leather stitch, forged iron hardware,
  cast bronze fitment, precious jewel/enamel, Gothic devotional, guild marked,
  traveler patched, and ruin corroded
- maps visible anatomy to geometry terms and legal Blender tool IDs
- captures source fields, attachment mechanics, operator checks, and lore hooks

## Starter Accessories

- leather belt with buckle
- belt pouch or coin purse
- penannular brooch or cloak pin
- signet ring
- pendant or amulet
- key ring with warded keys
- chatelaine belt hook
- satchel or messenger bag
- scabbard belt hanger
- spectacles and case
- seal matrix or stamp
- waterskin or travel flask

## Documents

- `accessory_source_index_v0.md` lists source links and their repo use.
- `accessory_style_status_system_v0.md` explains status/style/family labels.
- `accessory_family_build_plans_v0.md` maps starter assets to build sequences.
- `accessory_lore_book_hooks_v0.md` captures player-facing book/detail hooks.
- `operator_accessory_handoff_v0.md` defines future UI/manual workcard fields.

## Boundary

This is game-asset planning only. It is not fabrication guidance, costume safety
guidance, historical authenticity proof, conservation guidance, or active
generated-asset input.
