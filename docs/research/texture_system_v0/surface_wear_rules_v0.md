# Surface Wear Rules V0

## Purpose

Texture should react to surface role. The same material should look different
on a top face, exposed bevel, socket recess, waterline, handrail, or ceiling
underside.

## General Rules

Top surfaces collect:

- dust
- ash
- moss on outdoor/wet styles
- worn spots where walked on

Bottom surfaces collect:

- darkness
- dampness
- soot under fire-lit caps
- less direct edge wear

Outer edges collect:

- pale stone wear
- chipped corners
- scratched metal
- polished wood on hand-contact surfaces

Inner recesses collect:

- dark grime
- ambient occlusion
- dampness
- moss/slime if near wet zones
- less direct edge wear

Vertical faces collect:

- water streaks
- rust streaks below metal
- soot above candles/torches
- wall marks if decals are available

Walkable floors collect:

- worn high-traffic paths
- dirt in cracks
- dust in low-traffic corners
- wetness near water or sewer zones

Hand-contact surfaces collect:

- polish
- reduced dust
- smooth roughness
- edge darkening from use

Ceiling undersides collect:

- soot
- dark rib shadows
- less dust
- water stains if leaking

Waterlines collect:

- algae
- mineral deposits
- dark damp bands
- slime in sewer/aqueduct styles

## Component Examples

Railing plinth:

```text
bottom grime
edge wear on chamfers
moss near base for wet/overgrown styles
no decals on low hardware tier
```

Pointed arch recess:

```text
dark interior groove
subtle worn rim
optional crack/smoke decals on high tier
```

Stair tread:

```text
worn nosing
dirt in back corners
top dust or wetness depending on dungeon
```

Window sill:

```text
dust on top
water streaks below
edge wear on front lip
```

Door hinge strap:

```text
scratched metal
rust near rivets
optional rust streak decals on high tier
```

Vault rib:

```text
edge highlights
dark underside
soot or water staining depending on room
```

Wall bay:

```text
base grime
opening reveal shadows
vertical streaks
optional cracks/marks on high tier
```

## Hardware Fallback Rule

Low-compute hardware must still receive:

- base color
- roughness variation
- normal/bump if affordable
- material-role slots
- vertex color or baked masks
- recess shadow materials

Low-compute hardware must not require:

- decals
- multiple overlapping transparent layers
- dense unique texture sets
- high-frequency material blends on every asset
