# Global Style Atlas V0

This atlas gives future asset work a shared visual language. It is not final art
direction. It is a planning map for references, source packets, material sheets,
and Blender workcards.

Each style should eventually get:

```text
reference packet -> component list -> shape language -> material palette
-> wear rules -> Blender tool sequences -> low-compute fallback
```

## Style Sheet Fields

Use these fields when expanding a style:

- `style_id`
- `plain_name`
- `world_use`
- `silhouette_rules`
- `geometry_language`
- `material_palette`
- `surface_wear`
- `decoration_density`
- `lighting_mood`
- `asset_families`
- `readable_lore_hooks`
- `low_compute_fallback`
- `avoid`

## Cathedral Gothic

Style ID: `cathedral_gothic_v0`

World use:

- cathedrals
- chapels
- abbeys
- cloisters
- sacred ruins
- noble burial spaces

Silhouette rules:

- tall vertical rhythm
- pointed arches
- clustered supports
- ribbed ceilings
- narrow repeated window bays
- finials and pinnacles above strong vertical supports

Geometry language:

- pointed arches
- lancets
- tracery
- trefoils
- quatrefoils
- rib vaults
- bosses
- clustered shafts
- blind arcades
- crockets
- thin mullions
- deep reveals

Material palette:

- pale limestone
- gray stone
- stained glass
- dark iron
- carved wood
- aged brass
- candle soot

Surface wear:

- soot above candles and lamps
- dust in high ribs
- polished thresholds
- water streaks below windows
- chipped arrises on steps
- moss at exterior bases

Decoration density:

- high at windows, portals, capitals, bosses, screens, and railings
- medium on wall bays and columns
- low on floor walking surfaces

Lighting mood:

- high contrast shafts of colored light
- deep shadow under arches and vault ribs
- warm candle points against cool stone

Asset families:

- rose windows
- lancet windows
- tracery screens
- railings
- columns
- clustered piers
- rib vaults
- bosses
- altars
- pews
- lecterns
- reliquary cases
- stone tombs

Readable lore hooks:

- tracing-floor geometry
- guild marks
- mason repair notes
- saint calendars
- burial inscriptions
- window donor plaques

Low-compute fallback:

- keep pointed arch silhouettes
- use normal maps or material masks for small tracery
- reduce repeated ribs to fewer clean bands
- replace deep carved ornament with raised panels and shadow gaps

Avoid:

- random decoration that ignores bay rhythm
- thick mullions that make windows read like cages
- uniform beige stone without shadow gaps or wear variation

## Castle Fortress

Style ID: `castle_fortress_v0`

World use:

- keeps
- towers
- walls
- gatehouses
- battlements
- guard rooms
- armories

Silhouette rules:

- heavy mass
- blocky walls
- crenellated rooflines
- narrow defensive openings
- thick doors and gates
- repeated vertical wall breaks

Geometry language:

- ashlar blocks
- machicolations
- crenels
- merlons
- arrow slits
- portcullis tracks
- heavy hinges
- drawbar sockets
- round or square towers
- battered wall bases

Material palette:

- rough gray stone
- dark timber
- blackened iron
- leather straps
- packed earth
- straw

Surface wear:

- chipped corners
- rust below iron hardware
- soot near torches
- mud at lower walls
- water marks below battlements
- scraped thresholds

Decoration density:

- low on defensive mass
- medium on gates, banners, shields, and noble rooms
- high only on heraldry and chapel spaces

Lighting mood:

- torch pools
- cold daylight through slits
- deep interior shadow

Asset families:

- gates
- doors
- portcullises
- murder holes
- arrow slits
- wall walks
- stairs
- ladders
- weapon racks
- banners
- guard furniture

Readable lore hooks:

- guard logs
- siege repair notes
- armory tallies
- gatehouse warnings
- heraldic plaques

Low-compute fallback:

- prioritize wall mass, battlement silhouette, and door hardware
- use block textures for stone courses
- collapse repeated stones into trim-sheet bands

Avoid:

- delicate cathedral tracery on military walls unless it is a chapel or noble
  addition
- overdecorated defensive surfaces
- flat walls with no base, slit, or course rhythm

## Village Vernacular

Style ID: `village_vernacular_v0`

World use:

- cottages
- farm buildings
- barns
- wells
- fences
- stables
- workshops

Silhouette rules:

- human scale
- uneven rooflines
- visible timber and plank logic
- simple doors and small windows
- practical attachments

Geometry language:

- timber frames
- plank walls
- wattle panels
- stone footings
- thatch roofs
- simple lintels
- rough thresholds
- pegs
- braces
- small fences

Material palette:

- warm wood
- weathered plaster
- thatch
- field stone
- rope
- clay tile
- dull iron

Surface wear:

- mud at base
- smoke at chimneys
- worn door handles
- warped planks
- moss on thatch
- animal wear near stables

Decoration density:

- low to medium
- decoration appears on signs, shutters, door trim, carved posts, and market
  objects

Lighting mood:

- warm interior windows
- smoke and hearth glow
- soft outdoor light

Asset families:

- fences
- gates
- wells
- carts
- stools
- benches
- tables
- storage chests
- animal pens
- food props
- tools

Readable lore hooks:

- harvest marks
- stable records
- kitchen notes
- trade signs
- family ownership marks

Low-compute fallback:

- use strong roof/wall silhouettes and material contrast
- represent plank detail with material masks and simple grooves
- reduce clutter to clusters with readable silhouettes

Avoid:

- perfect symmetry on poor structures
- polished stone where rough wood or plaster should dominate
- noble-level ornament on common buildings

## Market And Tavern

Style ID: `market_tavern_v0`

World use:

- taverns
- inns
- market stalls
- kitchens
- cellars
- guild counters
- trade streets

Silhouette rules:

- dense but readable clutter
- many containers
- hanging objects
- repeated table/counter lines
- signs and readable labels

Geometry language:

- trestle tables
- barrels
- crates
- sacks
- hanging hooks
- racks
- shelves
- tankards
- jugs
- baskets
- folded cloth
- signage boards

Material palette:

- dark wood
- stained cloth
- ceramic
- glass
- iron hooks
- food materials
- straw
- spilled liquid

Surface wear:

- scratches on tables
- spilled drink rings
- grease near kitchens
- soot near hearths
- worn thresholds
- grime under counters

Decoration density:

- medium
- detail comes from object variety and arrangement rather than carved ornament

Lighting mood:

- warm hearths
- lamp pools
- busy shadows under shelves and counters

Asset families:

- tables
- benches
- barrels
- crates
- sacks
- plates
- bowls
- tankards
- bottles
- food
- signs
- shelves
- lanterns

Readable lore hooks:

- tavern ledgers
- price boards
- cellar inventory
- cook notes
- guild notices
- missing cargo tags

Low-compute fallback:

- group clutter into trays, shelves, and table sets
- use material slots instead of individual tiny decals
- keep large silhouettes: barrel, sack, basket, sign, table

Avoid:

- random scattered props with no service path
- too many unique tiny meshes in one view
- unreadable food piles with no container logic

## Crypt Dungeon

Style ID: `crypt_dungeon_v0`

World use:

- underground rooms
- burial chambers
- prisons
- old corridors
- locked chambers
- dungeon hubs

Silhouette rules:

- low ceilings
- repeated corridor bays
- heavy doors
- barred openings
- thick thresholds
- tomb and slab shapes

Geometry language:

- block stone
- iron bars
- grates
- slab tombs
- wall niches
- alcoves
- heavy arches
- drain channels
- chain anchors
- pressure plates

Material palette:

- cold stone
- rusted iron
- old wood
- bone
- dry dust
- damp moss
- candle wax

Surface wear:

- water stains
- rust streaks
- dust on unused ledges
- chipped slab edges
- grime near doors
- polished high-traffic floor paths

Decoration density:

- low in utility corridors
- medium in burial rooms
- high only at ritual/tomb focal points

Lighting mood:

- low light
- torch or candle islands
- deep corners
- wet highlights

Asset families:

- tombs
- doors
- bars
- grates
- chains
- locks
- altars
- urns
- bones
- plaques
- traps
- drain covers

Readable lore hooks:

- burial records
- warning inscriptions
- prisoner marks
- trap maintenance notes
- ritual fragments

Low-compute fallback:

- use repeated bay modules and strong door/grate silhouettes
- represent wall grime with material masks
- keep tombs and plaques as simple blocks with bevels

Avoid:

- bright, clean surfaces
- too much decorative density in every corridor
- thin props that vanish in low light

## Cave And Cavern

Style ID: `cave_cavern_v0`

World use:

- natural caves
- wet caverns
- underground rivers
- monster dens
- hidden passages

Silhouette rules:

- irregular outlines
- layered rock shelves
- stalactites and stalagmites
- uneven floors
- narrow squeezes opening into chambers

Geometry language:

- rock chunks
- sloped planes
- rounded erosion
- crack lines
- sediment bands
- water pools
- ledges
- root intrusions
- cave mouth arches

Material palette:

- wet stone
- mineral stains
- mud
- moss
- lichen
- root wood
- dark water

Surface wear:

- glossy wet lower surfaces
- mineral streaks
- mud splatter
- broken rock edges
- moss near light and water

Decoration density:

- low for manmade ornament
- high natural variation in silhouette and surface masks

Lighting mood:

- cold darkness
- reflected water light
- occasional torch or shaft of daylight

Asset families:

- rocks
- cliffs
- ledges
- pools
- roots
- bones
- nests
- bats
- simple bridges
- rope anchors

Readable lore hooks:

- cave maps
- miner marks
- waterline clues
- animal signs
- collapsed passage warnings

Low-compute fallback:

- use modular rock silhouettes and material variation
- reduce small stones to scatter decals only if hardware allows
- keep ledges and paths readable

Avoid:

- regular grid-like architecture unless a manmade section is present
- perfectly smooth gray blobs
- clutter that hides walkable paths

## Sewer And Cistern

Style ID: `sewer_cistern_v0`

World use:

- drains
- water channels
- cistern rooms
- old aqueducts
- sluice gates
- damp service tunnels

Silhouette rules:

- repeated arches
- horizontal water channels
- pipe openings
- grates
- valve/sluice silhouettes
- slick walkways

Geometry language:

- barrel vaults
- brick arches
- stone channels
- grates
- pipes
- sluice gates
- steps into water
- drain covers
- maintenance ledges

Material palette:

- wet stone
- brick
- rusted iron
- dark water
- algae
- green-black grime

Surface wear:

- waterline stains
- mineral rings
- algae near water
- rust below metal
- slime on lower walls
- cracked brick courses

Decoration density:

- low
- detail comes from function, water flow, and repeated service geometry

Lighting mood:

- dim greenish or blue reflected light
- harsh torch highlights on wet stone

Asset families:

- channels
- bridges
- grates
- valves
- pipes
- ladders
- sluice doors
- water wheels
- maintenance doors

Readable lore hooks:

- maintenance logs
- flood marks
- water-right inscriptions
- city service plaques
- hidden route maps

Low-compute fallback:

- use strong channel geometry and wet material masks
- keep waterline stains as material bands
- simplify pipe networks into repeated modules

Avoid:

- dry-looking materials
- decorative Gothic detail everywhere
- water paths with no visible source or exit

## Ruin And Abandoned Site

Style ID: `ruin_abandoned_v0`

World use:

- broken castles
- ruined chapels
- burned villages
- abandoned towers
- collapsed dungeons
- overgrown roads

Silhouette rules:

- broken skyline
- missing modules
- exposed interiors
- fallen stones
- tilted supports
- overgrowth interrupting hard geometry

Geometry language:

- fractured walls
- broken arches
- fallen beams
- cracked slabs
- rubble piles
- missing roof spans
- patched surfaces
- open doorframes

Material palette:

- weathered stone
- rotten wood
- rust
- moss
- lichen
- ash
- exposed earth

Surface wear:

- chipped edges
- dark cracks
- moss at joints
- soot on burned sites
- dirt on lower surfaces
- sun-bleached upper surfaces

Decoration density:

- depends on original style
- broken detail should reveal former structure, not random noise

Lighting mood:

- open sky in broken interiors
- strong shadow inside collapsed sections
- vegetation color contrast

Asset families:

- rubble
- cracked walls
- broken columns
- fallen arches
- roof debris
- burned furniture
- overgrowth
- broken signs
- blocked paths

Readable lore hooks:

- repair records
- battle marks
- collapse warnings
- abandoned inventories
- weathered inscriptions

Low-compute fallback:

- create a few strong broken silhouettes
- use material masks for cracks and moss
- reduce rubble into clustered piles

Avoid:

- evenly distributing damage everywhere
- rubble that blocks gameplay reads
- broken pieces with no relation to nearby intact structure

## Workshop And Forge

Style ID: `workshop_forge_v0`

World use:

- smithies
- carpentry rooms
- mason yards
- textile rooms
- alchemy rooms
- repair spaces

Silhouette rules:

- tool racks
- benches
- work surfaces
- repeated storage bins
- process stations
- visible raw material piles

Geometry language:

- benches
- anvils
- clamps
- racks
- shelves
- molds
- tubs
- wheels
- frames
- jigs
- hanging tools

Material palette:

- wood
- iron
- bronze
- stone
- coal
- ash
- cloth
- leather
- clay
- glass

Surface wear:

- scratches on worktops
- burns near forge
- dust near stonework
- sawdust near woodwork
- dye stains near textile work
- chemical stains near alchemy

Decoration density:

- medium
- detail is functional: tools, process marks, material piles, labels

Lighting mood:

- hot forge glow
- task lamps
- dusty shafts of light
- high contrast work areas

Asset families:

- tools
- benches
- storage racks
- molds
- barrels
- raw materials
- carts
- measuring tools
- pattern boards
- repair objects

Readable lore hooks:

- craft manuals
- job orders
- pattern boards
- guild marks
- repair tags
- warning notes

Low-compute fallback:

- make workstations as grouped sets
- use wall racks to organize many small tools
- use material stains instead of separate tiny spills

Avoid:

- random tools with no process flow
- clean benches
- unclear difference between craft types

## Noble Interior

Style ID: `noble_interior_v0`

World use:

- halls
- private chambers
- libraries
- council rooms
- galleries
- high-status bedrooms

Silhouette rules:

- ordered symmetry
- large furniture anchors
- rich trim
- framed walls
- curtains and banners
- polished surfaces

Geometry language:

- panelled walls
- carved chairs
- high tables
- shelves
- tapestries
- canopy beds
- fireplaces
- columns or pilasters
- decorative screens
- display cases

Material palette:

- polished wood
- stone
- brass
- gold accents
- cloth
- leather
- parchment
- glass

Surface wear:

- polished handles
- worn chair arms
- soot above fireplaces
- dust on shelves
- faded textiles
- scraped floor paths

Decoration density:

- medium to high
- more framed and symmetrical than market clutter

Lighting mood:

- warm hearth light
- candles
- controlled window light
- reflective metal accents

Asset families:

- thrones
- high-back chairs
- tables
- shelves
- books
- lecterns
- beds
- chests
- tapestries
- banners
- mirrors
- fireplaces

Readable lore hooks:

- lineage records
- contracts
- maps
- seals
- library marginalia
- political letters

Low-compute fallback:

- prioritize wall panels, large furniture, and cloth blocks
- reduce carving to trim profiles and normal maps
- use repeated decorative modules

Avoid:

- tavern-style clutter density
- cheap rough materials unless in storage rooms
- asymmetry without a reason

## Wilderness Shrine

Style ID: `wilderness_shrine_v0`

World use:

- roadside shrines
- forest altars
- standing stones
- small chapels
- ruined holy sites
- pilgrimage markers

Silhouette rules:

- small focal object in natural setting
- vertical marker
- offering surface
- path or threshold cue
- natural growth around manmade geometry

Geometry language:

- standing stones
- small altars
- carved plaques
- votive shelves
- steps
- low walls
- tree roots
- simple arches
- hanging charms
- offering bowls

Material palette:

- weathered stone
- wood
- cloth scraps
- wax
- flowers
- moss
- dirt
- water

Surface wear:

- moss on stone
- wax drips
- faded cloth
- water streaks
- chipped carvings
- foot-worn ground

Decoration density:

- low to medium
- detail is concentrated around offerings and inscriptions

Lighting mood:

- daylight through trees
- candle glow
- moonlit stone
- fog or mist optional

Asset families:

- altars
- bowls
- candles
- plaques
- charms
- trees
- roots
- stones
- benches
- small fences

Readable lore hooks:

- pilgrim notes
- prayer inscriptions
- offering records
- saint or local spirit markers
- trail warnings

Low-compute fallback:

- keep shrine silhouette and offering cluster
- use material masks for moss/wax
- group small offerings into tray-like clusters

Avoid:

- making every shrine ornate
- unclear path relationship
- props that look randomly dropped

## Mine And Quarry

Style ID: `mine_quarry_v0`

World use:

- mines
- quarries
- stone yards
- extraction tunnels
- collapsed shafts
- ore storage

Silhouette rules:

- cut rock faces
- timber supports
- carts and rails
- stacked raw material
- rope and pulley systems
- rough industrial rhythm

Geometry language:

- tunnel arches
- timber shoring
- planks
- rails
- carts
- buckets
- pulleys
- rock strata
- cut blocks
- slag/ore piles

Material palette:

- raw stone
- ore
- timber
- iron
- rope
- mud
- dust
- lamp soot

Surface wear:

- scrape marks on carts
- dust on everything
- soot around lamps
- water seep marks
- chipped rock edges
- worn rail paths

Decoration density:

- low
- detail is process-driven: supports, marks, carts, raw material, warning signs

Lighting mood:

- lamp pools
- deep black tunnels
- dusty beams
- occasional daylight at quarry edge

Asset families:

- carts
- rails
- tools
- supports
- ladders
- buckets
- ore piles
- rope systems
- warning signs
- cut stone blocks

Readable lore hooks:

- tally marks
- shift notes
- collapse warnings
- ore quality marks
- quarry cut diagrams

Low-compute fallback:

- reuse support modules and cart sets
- use material bands for rock strata
- keep tunnel openings and rails readable

Avoid:

- polished architectural stone inside raw extraction areas
- confusing walk paths with ore piles
- decorative details unrelated to labor/process

## Style Mixing Rules

Use style mixing when the world demands it:

- `cathedral_gothic_v0 + ruin_abandoned_v0`: broken chapel or sacred ruin
- `castle_fortress_v0 + noble_interior_v0`: lord's hall inside a keep
- `village_vernacular_v0 + market_tavern_v0`: village square or inn yard
- `crypt_dungeon_v0 + sewer_cistern_v0`: old drain under a burial site
- `cave_cavern_v0 + mine_quarry_v0`: worked mine breaking into natural cave
- `workshop_forge_v0 + castle_fortress_v0`: military armory or repair yard

Mixing rule:

```text
one dominant style controls mass and silhouette
one secondary style contributes props, materials, or damage
one rare accent style can create story contrast
```

Do not mix every style at once. The player should be able to name where they
are from the major shapes before noticing small props.
