# Asset Family Animation Backlog V0

This backlog names likely animation needs by asset family. It is not an
implementation queue.

## Architecture

Doors and shutters:

- door open/close
- heavy gate open/close
- barred door rattle
- shutter swing
- hidden panel slide
- lock/latch movement

Gates and barriers:

- portcullis raise/lower
- drawbridge tilt
- chain winch loop
- gate latch drop
- sliding bolt
- rotating wall section

Ceilings and sacred geometry:

- boss reveal
- folding/lifting muqarnas demonstration preview
- rotating construction diagram for readable books
- hidden mechanism opening from selected pattern cells

Environmental architecture:

- hanging sign sway
- curtain/banner sway
- torch bracket flame support cue
- waterwheel rotation
- mill wheel and gear loop

## Dungeon And Mechanisms

Interactive:

- lever pull
- pressure plate depress/release
- trapdoor open/fall
- chest lid open/close
- winch crank loop
- pulley lift
- secret wall rotate

Hazards:

- spike raise/drop
- crusher descend/reset
- blade swing
- arrow slit trigger
- fire/steam vent timing marker
- unstable floor collapse

State transitions:

- locked/unlocked
- active/inactive
- jammed/reset
- broken/repaired
- revealed/hidden

## Furniture

Simple interaction:

- chest lid hinge
- drawer slide
- cabinet door open
- folding stool open/close
- lectern book open
- table clutter nudge

Soft/secondary:

- curtain sway
- bed canopy cloth idle
- chair cushion compression, later only
- hanging cloth/tapestry sway

Inspection:

- book page turn
- map unroll
- desk secret compartment
- jewelry box open

## Musical Instruments

Performance loops:

- lute pluck loop
- harp pluck loop
- recorder finger loop
- shawm breath/finger loop
- drum strike loop
- bell toll loop
- portative organ key/bellows loop
- hurdy-gurdy crank/key loop

Setup/repair:

- tuning peg turn
- string replacement pose
- drum tension cord adjustment
- bell rope pull
- organ bellows repair

Low-compute rule:

- if finger-level motion is too expensive, keep broad pose, sound anchor, and
  loop timing markers.

## Food, Drink, And Kitchen

Ambient:

- optional steam loop
- candle/hearth heat shimmer marker
- hanging drying rack slight sway
- liquid surface subtle movement

Interaction:

- tankard lift/place
- bottle cork pop
- jug pour
- chest/barrel lid open
- cauldron stir
- spit rotate
- bellows pump near hearth/forge

State:

- full/empty
- sealed/open
- hot/cold
- fresh/stale/spoiled
- serving/abandoned

Do not animate food before state fields and serving sockets are clear.

## Animals

Static-pose first:

- standing
- sitting/perched
- sleeping
- curled
- grazing
- alert
- statue/emblem pose

Small pose loops:

- breathing
- head turn
- tail flick
- ear flick
- perch shift
- fish idle
- bat hanging twitch

Locomotion later:

- dog/cat walk
- horse/donkey walk
- cattle/sheep/pig walk
- chicken peck/walk
- rat scurry
- bat fly
- deer bound
- wolf stalk
- fish swim
- snake slither
- frog hop

Rule:

```text
do not start with locomotion until skeleton/pose conventions and static pose
sheets exist
```

## Accessories, Clothing, Armor, And Weapons

Accessories:

- pouch flap open
- key ring jingle marker
- pendant swing
- belt strap sway
- waterskin slosh marker

Clothing:

- cloak idle sway
- hood settle
- sleeve motion
- robe hem follow-through

Armor:

- visor raise/lower
- shoulder plate articulation
- hanging fauld/tasset motion
- gauntlet/finger articulation
- shield strap/grip pose

Weapons:

- draw/sheathe
- bow draw
- crossbow crank
- spear idle
- mace/axe swing pose marker
- weapon rack pickup

These need character/rig integration later; keep them as planning records for
now.

## Textures, VFX, And Material Animation

Material/state motion:

- flame flicker
- water shimmer
- wet drip marker
- glowing ember pulse
- magic/ritual glyph pulse, if allowed later
- smoke/steam spawn marker

Policy:

- lower-compute hardware gets fewer material animations and no decal-heavy
  animated details.
- material animation must not replace readable geometry.

## Priority Order

Good first animation TODOs:

1. `door_open_close_v0`
2. `bell_toll_loop_v0`
3. `lever_pull_v0`
4. `portcullis_raise_lower_v0`
5. `chest_lid_open_v0`
6. `waterwheel_rotation_v0`
7. `drum_strike_loop_v0`
8. `cauldron_stir_or_steam_v0`
9. `lute_pluck_pose_loop_v0`
10. `animal_idle_pose_sheet_v0`

Bad first animation TODOs:

- full horse locomotion
- full humanoid combat
- full cloth simulation
- complex animal flight
- multi-character music performance
- physics destruction

Those become reasonable after pivots, rig conventions, export policy, and simple
state clips exist.
