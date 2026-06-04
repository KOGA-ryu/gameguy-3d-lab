# Shape Language Dictionary V0

This dictionary gives practical words for describing asset details. Use it when
the user points at a reference and wants to say what should change.

The useful sentence pattern is:

```text
part name -> shape term -> operation -> amount -> check
```

Example:

```text
post plinth -> fielded panel -> inset and bevel -> shallow recess with raised
inner bead -> check that the panel reads on all four sides
```

## Mass And Body Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `blockout` | simple first shape | roughing the object before detail | primitives, `mesh_from_pydata`, bevel later |
| `mass` | main readable volume | describing body, post, wall, or furniture weight | cube/cylinder/sphere primitives, lofts |
| `core` | central body other parts attach to | columns, posts, animals, furniture | base mesh plus sockets |
| `shell` | outside skin around a core | fleece, domes, helmets, bowls, shields | solidify, shrinkwrap, offset profile |
| `section` | one cross-section slice | columns, rails, fish bodies, vases | section stack, loft sections |
| `profile` | 2D cross-section shape | moulding, rail, rib, trim, handle | curve bevel object, mesh from profile |
| `footprint` | top-down base shape | base, plinth, column, room module | square/circle/custom polygon profile |
| `silhouette` | outside outline | judging if the thing reads from distance | side/front drawing, low-poly preview |
| `stance` | support posture | animals, chairs, tables, posts | anchor points and collision proxy |
| `entasis` | slight swelling/taper in a shaft | columns, balusters, bat-like rails | radial stack with radius changes |

## Edge And Profile Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `arris` | sharp edge where faces meet | talking about crisp stone or wood corners | bevel or leave sharp with weighted normals |
| `bevel` | softened edge | reducing harsh computer edges | bevel modifier/tool |
| `chamfer` | flat angled bevel | low-poly beveled corners | bevel with one segment |
| `roundover` | rounded edge | soft wood, worn stone, handles | bevel with multiple segments |
| `fillet` | narrow flat band | separating two curves or profiles | small extruded strip or profile segment |
| `fascia` | broad flat face/band | wide trim, sign face, wall band | rectangle strip, inset/extrude |
| `bead` | small rounded raised strip | lips, rails, frames, decorative borders | curve bevel, torus/ring, profile stack |
| `torus` | large rounded convex band | column bases, collars, ring stacks | torus, radial stack ring |
| `cavetto` | concave quarter-round | shadowed cove under lips/caps | profile stack, bevel profile |
| `scotia` | deeper concave groove | base profiles and dark shadow bands | profile stack with inward curve |
| `ovolo` | convex quarter-round | raised cap lip or soft molding | profile stack, bevel profile |
| `ogee` | S-curve molding | fancy cap/base lips | custom side profile, curve bevel |
| `cove` | concave curved transition | underside of trim, ceiling edge | profile, bevel, solidify |
| `shadow_gap` | deliberate dark recess line | separating parts visually | inset, boolean cut, thin recessed strip |

## Panel And Frame Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `panel` | flat or shaped field inside a frame | doors, walls, railings, furniture | inset, extrude, bevel |
| `field` | central face of a panel | saying what gets raised/sunk | selected face or inset region |
| `fielded_panel` | panel with framed/sloped center | ornamental bases, doors, cabinets | inset face, bevel rim, center recess/raise |
| `reveal` | recessed return around opening | doors, windows, rail sockets | inset/extrude inward, bevel edges |
| `rabbet` | step cut for a fitted part | frame channels, window glass seats | boolean/inset stepped cut |
| `stile` | vertical frame member | doors, windows, cabinets | rectangular profile piece |
| `rail` | horizontal frame member | doors, windows, furniture | rectangular profile piece |
| `jamb` | side of an opening | doors/windows/portals | vertical opening side geometry |
| `sill` | lower opening member | windows, thresholds | horizontal ledge profile |
| `lintel` | top spanning member | doors, windows, simple portals | beam block or arch substitute |
| `socket` | part connection recess | rails entering posts, handles, tack | boolean cut, named connector |
| `collar` | band wrapped around a shaft | posts, pipes, handles, animals with harness | torus/radial band/profile strip |

## Arch And Opening Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `round_arch` | semicircular arch | Romanesque, sewers, simple openings | curve/profile extrude or boolean cut |
| `pointed_arch` | two arcs meeting at a point | Gothic doors/windows/panels | pointed arch profile, curve bars |
| `lancet` | tall narrow pointed opening | Gothic window bays | pointed arch plus vertical sides |
| `archivolt` | molded band following an arch | fancy portals and windows | swept profile along arch curve |
| `intrados` | underside/inside arch curve | describing the inner opening surface | inner arch loop surface |
| `extrados` | outer arch curve | describing the outside arch band | outer arch loop or frame |
| `spandrel` | area beside/above arch in a rectangle | panels between arch and frame | filled face, relief, ornament |
| `keystone` | top center arch block/detail | arch focal point | small block/boss at apex |
| `voussoir` | wedge arch stone | segmented arch stones | radial array wedges or face cuts |
| `springline` | level where arch starts | aligning arches to supports | guide line/source connector |
| `tracery` | decorative bar network in openings | windows, screens, panels | curve-to-mesh bars or boolean cut plate |
| `mullion` | vertical divider in window | multi-light windows | thin vertical bar/profile |
| `transom` | horizontal divider in opening | windows/doors | thin horizontal bar/profile |

## Foil, Lobe, And Gothic Ornament Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `foil` | lobe-based ornamental shape | trefoil/quatrefoil/cinquefoil families | circle arcs, boolean cuts, curve bars |
| `trefoil` | three-lobed shape | Gothic windows, panels, crests | radial three-circle construction |
| `quatrefoil` | four-lobed shape | railing panels, windows, bosses | radial four-circle construction |
| `cinquefoil` | five-lobed shape | richer Gothic openings | radial five-lobe construction |
| `cusp` | small pointed projection inside a foil/arch | making lobes Gothic instead of round | triangular/arc insert in profile |
| `lobe` | rounded petal-like part | describing scalloped/foil shapes | circle arcs, radial repetition |
| `scallop` | repeated small rounded bites | borders, shells, edge ornament | arrayed circles/boolean cuts |
| `mouchette` | flame/fish-like curved tracery shape | flowing Gothic tracery | bezier curve loop |
| `soufflet` | rounded flame-like tracery shape | rich window tracery | bezier curve loop |
| `crocket` | small leaf-like bump on edges | pinnacles, spires, finials | repeated small leaf meshes/curves |
| `finial` | terminal ornament at top | posts, spires, caps | cone/sphere/profile stack |
| `boss` | raised node at intersections | vault ribs, panels, ceilings | sphere/rosette/relief stack |

## Sacred Geometry And Pattern Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `construction_field` | full guide network | drawing complex line systems | SVG/canvas/source graph |
| `guide_line` | line used to find geometry, not final art | explaining visible vs hidden lines | source-only line |
| `selected_line` | guide line promoted to visible shape | choosing final ornament | segment selection recipe |
| `omission` | deliberately leaving lines out | making windows/screens from dense geometry | selection filters |
| `cell` | closed region in a pattern | lifting muqarnas/vault/panel pieces | cell extraction, face creation |
| `ring` | circular/polygonal band around center | rosettes, bosses, columns | radial stack or annulus |
| `sector` | pie-slice region | radial patterns, vault webs | radial cells/faces |
| `rosette` | radial flower/star pattern | windows, bosses, panels | radial arrays, curve bars |
| `star_polygon` | star made from connected radial points | sacred geometry, bosses, profiles | point generation, custom polygon |
| `radial_array` | repeated around a center | petals, ribs, spokes, bolts | array radial/object duplicate radial |
| `tessellation` | repeating pattern covering a plane | floors, screens, tiles | instance grid, pattern field |
| `orbit` | repeated placements around another shape | surrounding rosettes/medallions | radial/hex placement |
| `subgraph` | chosen nodes and edges from a graph | selecting a motif from construction field | graph selection |
| `cascade` | ordered lift/fold sequence | muqarnas or dome cells | tiered cell operations |

## Organic And Scroll Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `scroll` | curling decorative curve | ironwork, vines, carvings | bezier curve with bevel depth |
| `volute` | spiral-like scroll end | capitals, brackets, railings | spiral curve/profile |
| `tendril` | thin curling plant line | foliage ornament, ironwork | curve bevel, array/mirror |
| `vine` | branching organic line | panels, columns, borders | curves with leaves as instances |
| `leaf` | simple organic blade | crockets, capitals, relief | custom polygon or sculpted mesh |
| `fluting` | vertical grooves | columns, shafts, vessels | repeated cuts or radial ribs |
| `reeded` | repeated convex ribs | columns, handles, metalwork | radial array raised strips |
| `braid` | interlaced strands | ropes, trim, hair, straps | curves, array, twist/simple deform |
| `knotwork` | interwoven line pattern | borders and panels | curve paths with over/under breaks |
| `pierced` | cut-through ornament | screens, jali, tracery | boolean cuts or curve bars |

## Surface And Wear Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `patina` | aged surface color | bronze, brass, old metal | material mask/noise |
| `oxidation` | metal chemical aging | iron rust, copper green | procedural color mask |
| `soot` | black smoke residue | torches, hearths, candles | vertical/directional mask |
| `waterline` | stain where water sits/reaches | sewers, cisterns, bottles, walls | horizontal material band |
| `efflorescence` | pale mineral bloom on masonry | damp stone/brick | light noise/streak material |
| `edge_wear` | lighter/worn exposed edges | stone, wood, metal | bevel plus mask |
| `chips` | missing small edge pieces | damaged stone/wood | boolean nicks or normal detail |
| `cracks` | long fracture lines | stone, plaster, ceramic | curve cuts, material lines |
| `grime` | general dirt buildup | floors, corners, lower walls | ambient occlusion style mask |
| `moss` | green growth | damp outdoor stone/wood | material mask, scatter optional |
| `lichen` | spotty growth | old stone, roof, shrine | spot mask, low-cost material |
| `polished_path` | worn clean route through dirt | floors, thresholds, stairs | material contrast strip |

## Repetition And Assembly Terms

| Term | Plain Meaning | Use It When | Common Blender Method |
| --- | --- | --- | --- |
| `module` | reusable unit | dungeon bays, rails, windows, walls | source recipe asset |
| `bay` | one repeated span | arcades, railings, windows, vaults | array linear/module placement |
| `span` | distance between supports | rails, arches, bridges | bounds and sockets |
| `rhythm` | repeating visual spacing | columns, mullions, ribs | arrays and proportional guides |
| `alternation` | A/B repeating pattern | stone courses, panels, tiles | array with variant list |
| `register` | horizontal band/layer | walls, towers, muqarnas tiers | stacked sections |
| `tier` | vertical or cascade level | ceilings, towers, ornament | section stack/cascade |
| `cluster` | grouped small parts | props, animals, rubble, offerings | instancing/set dressing |
| `kitbash` | combining existing parts | rough prototype assembly | duplicate/place existing assets |
| `variant` | controlled alternate version | style/status/damage changes | source knobs/material swaps |

## How To Tell Dex What To Change

Use one of these sentence shapes:

```text
Make the [part] more [term], using [operation], but keep [constraint].
```

Examples:

- Make the base more fielded, using a recessed center and raised bead, but keep
  the square footprint.
- Make the shaft more reeded, using shallow vertical ribs, but keep it low-poly.
- Make the arch more Gothic, using a pointed arch profile and small cusps, but
  keep the opening clear.
- Make the rail look worn, using edge wear and polished hand-contact paths, but
  do not add decals.
- Make the ceiling more muqarnas-like, using selected cells lifted in cascade
  tiers, but keep the construction field visible in the source preview.

## Common Translation Problems

| User Phrase | Better Term | Why |
| --- | --- | --- |
| "that lip thing" | bead, torus, ovolo, cap lip, shadow gap | separates raised strip from recessed shadow |
| "make it fancy" | add tracery, foils, fielded panels, crockets, bosses | names the actual ornament |
| "make it less square" | chamfer, bevel, roundover, profile stack | controls edge treatment |
| "make it cathedral" | pointed arches, mullions, tracery, ribs, vertical rhythm | changes shape language, not just material |
| "make it old" | chips, grime, waterline, soot, moss, edge wear | gives specific wear rules |
| "more line work" | selected lines, tracery bars, relief grooves, construction graph | distinguishes visible geometry from guides |
| "complex but simple mesh" | strong silhouette, low-poly facets, material detail, LOD | keeps shape readable without high density |
| "select pieces and raise them" | cell selection, role promotion, lift/extrude, cascade order | maps sacred geometry to 3D operations |
