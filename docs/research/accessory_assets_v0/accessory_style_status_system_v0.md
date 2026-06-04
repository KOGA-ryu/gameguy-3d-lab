# Accessory Style And Status System V0

Accessories need three labels:

```text
what it is -> family
who/what it signals -> status tier
how it is made to read visually -> style
```

That lets one base object become many usable variants:

```text
belt pouch
-> rough utility herb pouch
-> common coin purse
-> merchant locked purse
-> rogue patched hidden pouch
-> ruin-salvage torn pouch
```

## Status Tiers

| Tier | Read | Asset signals |
| --- | --- | --- |
| rough utility | camp, servant, dungeon, workshop | plain leather, cord, rough hardware, patches |
| common wear | townsfolk, market, tavern | simple closures, stitched leather, modest repair |
| guild/trade | craft identity, workshop authority | guild tags, tool sockets, measuring marks |
| merchant display | visible trade wealth | polished hardware, clean stitching, lock plates |
| noble court | rank, fashion, heraldry | fine chain, gem sockets, central motifs |
| ritual/arcane | sacred, magical, oath, seal | symbols, inscriptions, dark recesses, gem seats |
| military/guard | equipment and authority | weapon hangers, keys, rivets, thick straps |
| rogue/traveler | portable, hidden, patched | extra loops, off-axis pockets, mixed repairs |
| ruin salvage | abandoned or damaged | bent rings, torn seams, corrosion, missing parts |

## Style Sheets

`plain_leather_stitch_v0`

- straps, pouches, satchels, flasks
- stitches, seams, flaps, loops, patches

`forged_iron_hardware_v0`

- buckles, rings, hooks, rivets, key rings
- dark metal and blunt practical forms

`cast_bronze_fitment_v0`

- plates, bosses, raised rims, fittings
- useful for higher-status clasps and mounts

`precious_jewel_enamel_v0`

- rings, pendants, brooch faces
- tiny gem sockets, polished metal, colored inlay

`gothic_devotional_v0`

- amulets, brooches, pendants, seal faces
- mini arches, crosses, foils, symbolic fronts

`guild_marked_v0`

- seals, pouches, satchels, chatelaines
- stamped marks, tag plates, tool sockets

`traveler_patched_v0`

- satchels, pouches, waterskins
- extra loops, patches, cords, scuffed corners

`ruin_corroded_v0`

- keys, brooches, buckles, torn pouches
- bent metal, broken straps, missing fasteners

## Promotion Rule

Accessories must declare attachment mechanics before Blender work. If the object
hangs, pins, loops, seals, locks, or carries something, that relation belongs in
source data and sockets, not in an invented Blender detail.
