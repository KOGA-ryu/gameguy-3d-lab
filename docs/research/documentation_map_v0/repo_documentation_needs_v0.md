# Repo Documentation Needs V0

The repo needs seven documentation layers for each serious asset family.

## 1. Taxonomy

Answers:

```text
what is this thing called, what family owns it, and what neighboring things can
it be confused with?
```

Needed fields:

- family name
- component names
- status/style/caste tiers
- visible anatomy
- source vocabulary
- related geometry terms

Good current examples:

- `docs/research/component_style_system_v0/asset_families/`
- `docs/research/furniture_assets_v0/`
- `docs/research/animal_assets_v0/`

## 2. Source Index

Answers:

```text
what references support the vocabulary and visible parts?
```

Needed fields:

- source URL or local reference packet
- what the source supports
- what the source does not prove
- whether it is anatomy, craft, style, measurement, or surface reference

Boundary:

- source support is not historical proof
- source support is not final concept art
- source support is not permission to copy protected art

## 3. Component Breakdown

Answers:

```text
what named parts does the object need before we can model it?
```

Needed fields:

- primary mass
- secondary masses
- trim/detail parts
- sockets and attachments
- collision/proxy parts
- LOD-critical parts
- optional detail parts

Example:

```text
railing post -> plinth, shaft, panel field, bead lip, socket reveal, cap, finial
horse -> barrel torso, neck, head, legs, hooves, mane, tail, tack sockets
door -> slab/frame, rails, stiles, hinges, latch, handle, threshold, trim
```

## 4. Geometry Shaping Ledger

Answers:

```text
what simple geometry creates the visible shape?
```

Needed fields:

- profile shapes
- construction graph or drawing guide
- operations such as extrude, loft, revolve, bevel, boolean, array, mirror
- edit knobs
- proportional constraints
- low-compute fallback

This is the layer that turns user language into source-owned geometry intent.

## 5. Blender Tool Workcard

Answers:

```text
which Blender tools execute the shape, and in what order?
```

Needed fields:

- base form tools
- curve tools
- boolean/cut tools
- bevel/weighted-normal tools
- retopo/cleanup tools
- UV/material tools
- export/proxy tools
- manual checks

This should not contain design decisions. Design decisions belong in taxonomy,
reference packets, recipes, or style sheets.

## 6. Material And Wear Sheet

Answers:

```text
what material reads make the asset belong to a dungeon, village, cathedral,
market, ruin, or workshop?
```

Needed fields:

- base material
- trim material
- surface wear
- grime/water/soot/moss rules
- optional decal policy
- lower-compute fallback
- UV and trim-sheet notes

Current anchor:

- `docs/research/texture_system_v0/`

## 7. Lore And Player-Readable Detail

Answers:

```text
why should the player care that this asset has this detail?
```

Needed fields:

- book/readable hook
- world clue
- player reward
- inspection detail
- related craft or cultural note

Good hook structure:

```text
visible shape cue -> world clue -> player reward
```

## Cross-Cutting Docs Still Needed

- global style atlas for dungeons, castles, cathedrals, villages, markets,
  caves, sewers, ruins, workshops, and wilderness
- shape-language dictionary for arches, lobes, stars, ribs, beads, curves,
  panels, bosses, spirals, and compound profiles
- drawing-guide template for side/front/top silhouettes and 2D profile source
- per-family Blender tool sequence cheat sheets
- manual-edit capture form so user corrections become future source rules
- performance budget guide for mesh density, decals, material slots, collision,
  and repeated set dressing
- asset dependency graph showing which small assets support bigger scenes
