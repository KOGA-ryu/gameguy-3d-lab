# Animal Assets V0

This folder starts the animal asset planning lane.

The machine-readable source is:

```text
data/asset_taxonomy/animals_v0/animal_asset_taxonomy_v0.json
```

Validate it with:

```bash
python3 scripts/validate_animal_asset_taxonomy_v0.py
```

## What This Lane Does

- names animal role tiers such as companion, mount/pack, livestock, poultry,
  vermin, wild prey, predator, cave/nocturnal, aquatic/wetland, and omen/heraldic
- defines reusable body-plan styles for small quadrupeds, canids, equines,
  hoofed livestock, swine, fleece animals, ground birds, corvids, bats, rodents,
  fish, snakes, and amphibians
- records starter animal families and specific starter assets
- maps visible anatomy to geometry terms and legal Blender tool IDs
- captures locomotion read, source fields, operator checks, and lore hooks

## Starter Animals

- village dog
- barn cat
- riding horse
- pack donkey or mule
- cattle or ox
- sheep or goat
- farm pig or boar
- chicken or flock bird
- rat vermin
- cave bat
- deer, stag, or hind
- gray wolf
- crow or raven
- river fish
- snake
- frog or toad

## Documents

- `animal_source_index_v0.md` lists source links and their repo use.
- `animal_role_body_plan_system_v0.md` explains role tiers, body plans, and
  naming boundaries.
- `animal_family_build_plans_v0.md` maps starter animals to build sequences.
- `animal_lore_book_hooks_v0.md` captures player-facing book/detail hooks.
- `operator_animal_handoff_v0.md` defines future UI/manual workcard fields.

## Boundary

This is game-asset planning only. It is not animal-care guidance, welfare
guidance, biological accuracy proof, animation runtime design, AI behavior
design, historical authenticity proof, or active generated-asset input.
