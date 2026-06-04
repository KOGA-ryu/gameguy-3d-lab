# Animal Lore Book Hooks V0

The animal lane should make environmental details explainable in player-facing
books. The point is not encyclopedic biology; it is readable world logic.

## Hooks By Starter Asset

| Starter Asset | Book Hook | Player Reward |
| --- | --- | --- |
| `village_dog_v0` | Kennel marks, warning posture, collar tags, guard lanes | Reads settlement safety and guard presence. |
| `barn_cat_v0` | Grain stores, rafters, warm spots, vermin-control hints | Connects barns, pantries, and household details. |
| `riding_horse_v0` | Stable measures, tack, hoof spacing, stall width | Explains roads, travel, cavalry, and status. |
| `pack_donkey_mule_v0` | Pack balance, narrow roads, rope marks, cargo frames | Explains trade routes and mining/cargo access. |
| `cattle_ox_v0` | Yokes, furrows, carts, horns, butcher-yard clues | Links farms, labor, and food systems. |
| `sheep_goat_small_ruminant_v0` | Wool before cloth, shearing, flock bells, mountain paths | Connects textiles, dye, and village economy. |
| `farm_pig_boar_v0` | Mud pens, bristle, tusks, butcher yards, forest boars | Separates farm animal from wild threat. |
| `chicken_flock_bird_v0` | Scratched yards, nests, cages, feathers, kitchen routes | Marks farm safety and food supply. |
| `rat_vermin_v0` | Gnaw marks, crumbs, cellars, pantries, sickness mood | Signals decay, stores, and hidden spaces. |
| `cave_bat_v0` | Roost stains, ceiling clusters, cave hollows, dark rafters | Rewards looking upward. |
| `deer_stag_hind_v0` | Antlers, tracks, forest edge, noble parks, hunting signs | Marks wilderness and hunting culture. |
| `gray_wolf_v0` | Pack signs, ruff silhouette, banners, grave warnings | Signals danger and faction identity. |
| `crow_raven_v0` | Black birds on battlements, grave markers, battlefield scavenging | Adds omen, death, and tower flavor. |
| `river_fish_v0` | Fishmonger clues, river health, wet markets, kitchen prep | Connects water systems to food and trade. |
| `snake_v0` | Curves in dust, staff carvings, ritual coils, warning symbols | Turns curve grammar into readable threat/emblem language. |
| `frog_toad_v0` | Rain signs, pond voices, damp stone, herbalist huts | Marks wet places and hidden water. |

## Writing Rule

Each hook should point to one visual detail the player can see in the model:

```text
shape cue -> world clue -> player reward
```

Good examples:

- antler span -> hunting ground -> noble estate nearby
- bat roost -> overhead hollow -> look up
- snout disk and tusks -> pig versus boar -> farm safety versus forest danger
- fish scale bands -> market freshness -> water source or trade route nearby
