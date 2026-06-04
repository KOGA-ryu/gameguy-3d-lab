# Furniture Style And Caste System V0

Furniture needs two separate labels:

```text
what it is -> family
who it belongs to / how it reads socially -> caste tier
how it is shaped and decorated -> style
```

That means the same base asset can be reused:

```text
chest
-> common household boarded chest
-> merchant locked coffer
-> noble carved coffer
-> ruin-salvage broken coffer
```

## Caste Tiers

| Tier | Read | Asset signals |
| --- | --- | --- |
| rough utility | camp, servant, dungeon, workshop | plank parts, patch boards, rough edges, visible pegs |
| common household | modest home, tavern, kitchen, barracks | stable form, simple hardware, repair marks |
| monastic/guild | disciplined shared work or refectory use | long repeatable forms, plain bevels, ordered wear |
| merchant/bourgeois | trade, display, household wealth | locks, shelves, raised panels, regular fronts |
| noble household | rank and comfort | high backs, cushions, canopies, carved trim |
| royal/ritual | authority or sacred use | central axis, crest, symbol panel, dais relation |
| scholarly/arcane | study, maps, alchemy, puzzle rooms | sloped tops, drawers, sockets, stains, compartments |
| ruin/salvage | broken, reused, abandoned | missing boards, broken legs, patches, burn/water marks |

## Style Sheets

`rough_plank_vernacular_v0`

- fast blockout
- flat planks, square supports, visible fasteners
- useful for low-cost clutter and breakable objects

`joined_oak_frame_v0`

- stiles, rails, stretchers, mortise/tenon hints
- useful for benches, chairs, cupboards, chests, tables

`gothic_panelled_v0`

- pointed arches, tracery panels, foils, moulded rails
- useful for cupboards, chairs, chests, lecterns, thrones

`monastic_plain_v0`

- simple ordered long furniture
- useful for benches, trestle tables, lecterns, workrooms

`merchant_display_v0`

- locks, shelves, ledges, front-facing panels, hardware
- useful for cupboards, counters, display cases, storage furniture

`noble_carved_textile_v0`

- cushions, curtains, high backs, carved arms, cloth panels
- useful for chairs, beds, chambers, noble halls

`royal_ritual_axis_v0`

- central axis, crest, dais relation, authority silhouette
- useful for thrones, altars, lecterns, ceremonial furniture

`ruin_repaired_v0`

- missing parts, patches, split boards, broken supports
- useful for dungeon and ruin variants without designing new forms

## Promotion Rule

Do not put style decisions inside Blender scripts. The recipe or workcard should
declare family, caste tier, and style first; Blender only executes the resulting
tool plan.
