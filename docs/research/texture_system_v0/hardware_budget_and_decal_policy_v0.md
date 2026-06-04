# Hardware Budget And Decal Policy V0

## Core Rule

```text
*** DECALS ARE HIGH-COST OPTIONAL DETAIL ***
```

Lower-compute hardware does not get decals.

That means every asset must look acceptable with:

- base materials
- material slots
- trim sheets
- simple procedural noise
- baked or vertex-color masks
- roughness variation
- normal/bump detail where affordable

Decals can improve the asset, but decals cannot carry the asset.

## Hardware Tiers

### Low

Target:

- old laptops
- integrated GPUs
- low-end handhelds
- browser or lightweight preview modes

Allowed:

- single base material per major role
- simple procedural noise
- one normal/bump layer when affordable
- vertex color dirt/wear masks
- trim sheets
- atlas motifs baked into material assignment

Forbidden or disabled:

- decals
- many transparent overlays
- dense per-asset unique textures
- high-resolution displacement
- many layered material blends

### Mid

Target:

- normal desktop/laptop preview
- comfortable Blender workbench/Cycles preview
- common indie game target

Allowed:

- base materials
- trim sheets
- atlases
- procedural masks
- limited normal/roughness maps
- small number of important decals if budget allows

Rules:

- decals are optional and count against a visible-area budget
- repeated decals should be instanced or atlased
- material count must stay controlled

### High

Target:

- final art preview
- high-end desktop
- hero shots
- high-quality exports

Allowed:

- decals
- localized cracks/stains/leaks
- higher resolution maps
- richer material layering
- stronger normal/height detail
- hero ornament atlases

Rules:

- still keep source ownership
- decals must have semantic purpose
- avoid random decal spam

## Decal Types

High-value decals:

- cracks
- leak streaks
- rust streaks
- scorch marks
- moss patches
- wall markings
- carved/painted symbols
- story-specific stains
- impact damage
- floor scratches

Low-value decals:

- random noise patches
- generic dirt spots everywhere
- detail that duplicates existing material noise
- decals on surfaces too small to notice

## Decal Fallbacks

When decals are disabled, use:

- darker material slot for recesses
- procedural dirt mask
- vertex color edge-wear mask
- trim-sheet crack/wear strips
- atlas motif baked into panel material
- low-cost roughness variation
- geometry-owned bevel and weighted normals

## Asset Authoring Rule

Every texture recipe should declare:

```text
decal_dependency: none | optional | required_for_high_tier_only
low_tier_fallback: material_mask | vertex_color | trim_sheet | atlas | none
```

No normal asset should require decals to communicate its main form.

## First Policy Test

Take one Gothic railing post and preview three material tiers:

```text
low: base limestone + recess grime + edge wear, no decals
mid: low + limited moss/water masks
high: mid + crack/smoke/moss decals
```

The low version must still read as a finished dungeon asset.
