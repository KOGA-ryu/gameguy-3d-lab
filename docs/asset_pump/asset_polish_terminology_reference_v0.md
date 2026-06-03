# Asset Polish Terminology Reference v0

## Purpose

Give the repo and the user the proper words for the layer after raw asset geometry:

```text
source recipe
-> deterministic asset geometry JSON
-> polish/tool-plan recipe
-> Blender adapter execution
-> preview/export
```

The goal is not to make Blender invent the design. The goal is to let us say exactly which architectural part gets which modeling operation, in what order, with what parameters.

## Working Sentence

Use architectural nouns for the part, geometric terms for the source shape, and Blender/tool terms for the operation.

```text
"Give the post plinth a recessed fielded panel, bevel the arrises,
add an ogee cap lip, and run weighted normals after the bevel."
```

This should become:

```text
asset part target
-> operation
-> parameter
-> validation
```

## Three Vocabularies

### 1. Architectural Part Terms

These are the words for what the asset is.

| Term | Use in this repo |
| --- | --- |
| `assembly` | A complete grouped object, such as post + rail + post. |
| `bay` | One repeated span between supports. Good for railings, arcades, windows, and vaults. |
| `module` | Reusable unit that can be repeated, mirrored, or arrayed. |
| `motif` | A decorative pattern unit extracted from a construction field. |
| `plinth` | The square or blocky base below a post, column, pier, or pedestal. |
| `base` | Lower support member. In recipes, use when `plinth` is too specific. |
| `shaft` | Main vertical body of a column, baluster, pier, or post. |
| `capital` | Top head of a column, pier, or post. |
| `cap` | Generic top piece, especially for railing posts or plinths. |
| `finial` | Decorative terminal on top of a post, cap, spire, or newel. |
| `pier` | Heavier vertical support, often square/compound, carrying arches or vault ribs. |
| `compound_pier` | Pier made from a central core plus attached shafts/ribs. Useful for Gothic supports. |
| `engaged_shaft` | Small attached column/shaft joined to a wall or pier. |
| `clustered_column` | Group of shafts treated as one support. |
| `impost` | Block or molding at the springing of an arch. |
| `springing_point` | Where an arch or rib begins to rise from support. |
| `springline` | Horizontal level through arch springing points. |

### 2. Railing And Balustrade Terms

Use these when talking about the post + rail + post prototype.

| Term | Meaning for generation |
| --- | --- |
| `balustrade` | Whole railing assembly: posts/newels, rail, balusters, panels, and infill. |
| `handrail` / `top_rail` | Graspable or upper rail. In game assets, use `top_rail` unless it is meant to be graspable. |
| `base_rail` / `shoe_rail` | Lower horizontal rail receiving balusters or infill. |
| `baluster` | Repeating vertical support between rails. Also called spindle/picket in common usage. |
| `newel_post` | Large post at the end, corner, or turn of a railing run. |
| `infill` | Material or ornament between posts and rails: panels, bars, lattice, tracery, scrollwork. |
| `panel` | Flat or relieved infill field. Can be recessed, raised, pierced, or framed. |
| `bracket` | Secondary support under a rail or shelf-like projection. |
| `cap_block` | Blocky top piece of a post or newel. |
| `rail_socket` | Connection point where a rail enters a post. |

Good recipe target names:

```text
railing.newel.left.plinth
railing.newel.left.shaft
railing.newel.left.cap
railing.top_rail.profile
railing.base_rail.profile
railing.infill.panel_00
railing.infill.tracery_edges
```

### 3. Panel, Frame, And Window Terms

Use these for windows, door frames, railing panels, and decorative faces.

| Term | Meaning for generation |
| --- | --- |
| `frame` | Whole border around a panel, door, or window. |
| `stile` | Vertical frame member. |
| `rail` | Horizontal frame member. |
| `jamb` | Side of a door/window opening. |
| `head` | Top horizontal member of an opening. |
| `sill` | Lower horizontal member of a window/opening. |
| `mullion` | Vertical divider in a window or tracery opening. |
| `transom` | Horizontal divider across an opening. |
| `light` | One glass/open area within window tracery. |
| `tracery` | Stone or wood bar pattern dividing window/open panel openings. |
| `bar_tracery` | Tracery made from thin bars/mullions. |
| `plate_tracery` | Openings cut from a flat stone plate. |
| `blind_tracery` | Tracery pattern applied to solid backing instead of open cut-through. |
| `cusp` | Pointed projecting shape inside an arch or foil. |
| `trefoil` | Three-lobed ornamental opening/shape. |
| `quatrefoil` | Four-lobed ornamental opening/shape. |
| `cinquefoil` | Five-lobed ornamental opening/shape. |
| `mouchette` | Flame/fish-like curved tracery shape. |
| `soufflet` | Inflated/rounded flame-like tracery shape. |

Recipe distinction:

```text
bar_tracery = build bars as swept profiles
plate_tracery = boolean cut openings from a slab
blind_tracery = raised/recessed relief on a solid panel
```

### 4. Arch And Vault Terms

Use these for cathedral windows, doorways, ribs, ceiling systems, and support placement.

| Term | Meaning for generation |
| --- | --- |
| `arch` | Curved or pointed spanning shape. |
| `pointed_arch` | Two-arc Gothic arch meeting at an apex. |
| `ogive` | Pointed arch/rib form; also used for Gothic rib curves. |
| `voussoir` | Wedge-shaped arch stone. Usually simulated as block segmentation. |
| `keystone` | Top/central voussoir or boss-like cap at arch apex. |
| `springer` | Lowest voussoir at the start of an arch. |
| `intrados` | Inner underside curve/surface of an arch. |
| `extrados` | Outer curve/surface of an arch. |
| `archivolt` | Molded band following the face of an arch. |
| `spandrel` | Triangular/curved field between arch curve and rectangular frame. |
| `vault` | Curved ceiling or roof surface. |
| `rib_vault` | Vault organized by raised ribs with webbing between them. |
| `webbing` / `web_cell` | Surface panel between vault ribs. |
| `boss` | Decorative node at rib intersections. |
| `diagonal_rib` | Rib crossing a vault bay diagonally. |
| `transverse_rib` | Rib crossing bay perpendicular to the main axis. |
| `formeret` / `wall_rib` | Rib along wall side of a vault compartment. |
| `lierne` | Short secondary rib not springing from the main support. |
| `tierceron` | Secondary rib springing from support but not reaching the main keystone. |
| `fan_vault` | Vault with ribs spreading like a fan from a springing point. |

Good recipe target names:

```text
vault.bay_00.diagonal_ribs
vault.bay_00.web_cells
vault.bay_00.boss.center
arch.window_00.intrados
arch.window_00.archivolt.outer_band
```

### 5. Moldings And Edge Profile Terms

These are the words for lips, bands, raised strips, shadow lines, and carved profile changes.

| Term | Meaning for generation |
| --- | --- |
| `molding` | Continuous shaped strip used for decoration or surface transition. British spelling: moulding. |
| `profile` | 2D cross-section of a molding, rail, rib, or trim strip. |
| `fillet` | Narrow flat band separating curved moldings. |
| `fascia` | Wider flat band or face. |
| `bead` | Small rounded convex molding. |
| `astragal` | Small bead-like molding, often at a junction. |
| `torus` | Large rounded convex molding, often semicircular in section. |
| `ovolo` | Convex quarter-round molding. |
| `cavetto` | Concave quarter-round molding. |
| `scotia` | Deeper concave molding, often between fillets. |
| `cyma_recta` | S-curve molding: concave above, convex below. |
| `cyma_reversa` / `ogee` | S-curve molding: convex above, concave below. |
| `chamfer` | Flat angled cut across an edge. |
| `bevel` | General edge softening/cut; in Blender often a bevel modifier/tool. |
| `arris` | Sharp edge where two faces meet. |
| `reveal` | Recessed edge/return around a panel or opening. |
| `shadow_gap` | Small recess used to create a strong line of shadow. |
| `raised` / `proud` | Feature stands out from the base surface. |
| `recessed` / `sunk` | Feature is pushed below the base surface. |
| `fielded_panel` | Panel with a raised or sloped central field and framed border. |

Useful generation phrase:

```text
"Add a fielded panel: inset the face, sink the center,
bevel the panel rim, and add a small bead inside the frame."
```

## Geometric Construction Terms

These are the words for the source drawing before it becomes a model.

| Term | Repo meaning |
| --- | --- |
| `construction_field` | Full hidden guide network: circles, lines, intersections, rings, cells. |
| `guide_line` | Construction line that may be omitted from final output. |
| `visible_line` | Line promoted into mesh, curve, rib, rail, cut, or relief. |
| `selected_subgraph` | Chosen nodes/edges/cells from the construction field. |
| `selective_omission` | Keeping only the lines/cells that matter and suppressing the rest. |
| `node` | Point in the construction graph. |
| `edge` | Segment between two nodes. |
| `cell` | Closed 2D region bounded by edges. |
| `loop` | Closed edge path. |
| `ring` | Circular or polygonal band around a center. |
| `annulus` | Region between two rings. |
| `sector` | Pie-slice region between radii. |
| `chord` | Line connecting two points on a circle/ring. |
| `tangent` | Line touching a circle at one point. |
| `secant` | Line crossing a circle at two points. |
| `rosette` | Radial star/flower-like motif. |
| `star_polygon` | Alternating or connected radial points forming a star. |
| `repeat_unit` | Small unit repeated to make a field. |
| `tessellation` | Repetition covering a plane without gaps. |
| `symmetry_order` | Count of repeated rotations, such as 6-fold, 8-fold, 12-fold. |
| `orbit` | Repeated placements of a motif around a center or along a path. |
| `girih` | Islamic geometric strapwork pattern family. |
| `strapwork` | Interlaced band-like linework, useful for rails/tracery. |
| `jali` | Pierced screen pattern, useful for cutout panels. |
| `muqarnas_cell_plan` | 2D cell plan intended to lift/fold into tiered 3D vault cells. |
| `cascade_order` | Ordered lifting/folding/selection sequence, tier by tier. |

Working pipeline:

```text
construction_field
-> selected_subgraph
-> role_promotion
-> operation_stack
-> asset geometry or Blender tool plan
```

## Blender And Tool-Plan Terms

These are the words for what the adapter should do.

| Tool term | Meaning for generation |
| --- | --- |
| `extrude` | Pull faces/edges/profiles into depth or height. |
| `inset_faces` | Create an inner border on a face, useful for panels and recesses. |
| `extrude_along_normals` | Push selected faces outward/inward relative to face direction. |
| `solidify` | Add thickness to a surface/shell. |
| `bevel` | Add edge geometry to soften or shape hard edges. |
| `chamfer` | Bevel with one flat segment. |
| `bevel_profile` | Shape of bevel cross-section, from flat to rounded/custom. |
| `weighted_normals` | Improve hard-surface shading by weighting face normals. |
| `shade_smooth` | Smooth normal shading across faces. |
| `harden_normals` | Bevel option that preserves flat face appearance around bevels. |
| `face_strength` | Bevel/normal weighting hint for which faces dominate shading. |
| `curve_bevel_depth` | Give a curve a round tube-like thickness. |
| `bevel_object` | Use a custom curve as the cross-section of another curve. |
| `fill_caps` | Seal open ends of a beveled curve/tube. |
| `boolean_cut` | Cut openings or relief shapes from a solid. |
| `mirror` | Reflect geometry across an axis. |
| `array_linear` | Repeat along a straight path. |
| `array_radial` | Repeat around a center. |
| `uv_unwrap` | Flatten mesh faces into UV space for textures. |
| `smart_uv_project` | Automatic UV projection; useful for quick previews, not always final-quality. |
| `material_slot` | Named material assignment target. |
| `trim_sheet` | Texture layout with reusable strips for rails, lips, and moldings. |
| `normal_map` | Texture-driven surface normal detail. |
| `displacement` | Actual or shader-level surface height detail. |
| `merge_by_distance` | Cleanup duplicate vertices. |
| `recalculate_normals` | Fix face normal direction. |
| `lod_proxy` | Lower-detail mesh for distance rendering. |
| `collision_proxy` | Simplified physical/collision mesh. |

Important distinction:

```text
bevel/chamfer = edge treatment
inset/extrude = face relief
curve bevel/sweep = line becomes physical rib/rail
solidify = surface gets thickness
weighted normals = shading polish, not geometry shape
```

## Common Polish Sequences

### Railing Newel/Post

```text
block out plinth/base/shaft/cap
-> inset panel faces
-> sink or raise panel fields
-> bevel outer arrises
-> add bead/torus/ogee cap lips
-> add rail sockets
-> assign stone/wood/metal material slots
-> weighted normals
-> UV unwrap or trim-sheet hints
```

Recipe words:

```text
"square plinth with beveled arrises"
"recessed fielded panel on all four sides"
"double cap lip: bead over cavetto"
"rail sockets through left and right faces"
```

### Railing Infill Or Decorative Panel

```text
select 2D motif edges
-> omit guide lines
-> promote selected edges to tracery bars
-> curve bevel or sweep a rectangular/round profile
-> boolean-cut or leave open cells
-> bevel bar edges
-> weighted normals
```

Recipe words:

```text
"promote inner rosette strapwork to raised tracery"
"omit construction circles"
"make the panel blind tracery, not open cut-through"
"use bar tracery for thin physical ribs"
```

### Gothic Window Or Door Frame

```text
construct opening rectangle
-> add pointed arch head
-> create jambs, sill, head, mullions
-> add tracery loops
-> choose plate/bar/blind tracery mode
-> add archivolt molding
-> bevel and assign material slots
```

Recipe words:

```text
"pointed arch with archivolt band"
"two mullions dividing three lights"
"quatrefoil tracery in the arch head"
"bevel the intrados and extrados"
```

### Rib Vault Or Dome-Like Ceiling

```text
2D construction cell plan
-> select closed cells
-> assign cascade_order/tier
-> lift or fold web cells
-> sweep ribs along selected edges
-> place bosses at promoted nodes
-> solidify web surfaces
-> bevel ribs and bosses
```

Recipe words:

```text
"tiered muqarnas cell plan"
"lift each cell by cascade order"
"promote radial edges to ribs"
"place bosses at rib intersections"
"web cells should be recessed below ribs"
```

## Phrasebook For Talking To Dex

Use phrases like these when requesting changes:

```text
"Use the inner construction layer, not the outer guide layer."
"Omit the guide circles and promote only the selected strapwork."
"Make this a blind tracery panel, not a tile."
"The plinth needs a recessed fielded panel on all four sides."
"Chamfer the plinth arrises with one bevel segment."
"Give the cap a cyma reversa/ogee lip over a small bead."
"Make the ribs proud of the webbing by 0.025 m."
"Use curve bevels for thin tracery bars."
"Use plate tracery if the pattern is cut from a slab."
"Use weighted normals after beveling hard-surface stone."
"Keep the construction field as source data; do not make every guide line mesh."
```

## Target Naming Convention

Use this target pattern in recipes:

```text
asset.part.subpart.feature
```

Examples:

```text
railing.newel.left.plinth.outer_arrises
railing.newel.left.plinth.panel_faces
railing.newel.left.cap.ogee_lip
railing.top_rail.swept_profile
railing.infill.center.tracery_edges
window.arch_00.intrados
window.arch_00.archivolt.outer_band
vault.bay_00.web_cells
vault.bay_00.ribs.diagonal
```

## Repo Rule

The source recipe owns these decisions:

```text
what part exists
what source shape was selected
what role the shape plays
what operation applies
what dimensions and order are used
```

The Blender adapter owns only execution:

```text
create mesh/curve objects
apply modifiers/operators
assign materials
export/preview
validate obvious failures
```

## Source References

Blender tool terminology:

- [Blender Manual: Bevel Modifier](https://docs.blender.org/manual/en/4.0/modeling/modifiers/generate/bevel.html)
- [Blender Manual: Weighted Normal Modifier](https://docs.blender.org/manual/id/4.0/modeling/modifiers/modify/weighted_normal.html)
- [Blender Manual: Solidify Modifier](https://docs.blender.org/manual/en/latest/modeling/modifiers/generate/solidify.html)
- [Blender Manual: Curve Geometry and Bevel](https://docs.blender.org/manual/en/latest/modeling/curves/properties/geometry.html)
- [Blender Manual: UV Operators](https://docs.blender.org/manual/en/latest/modeling/meshes/editing/uv.html)

Architectural and ornamental terminology:

- [Vernacular Building Glossary: Baluster](https://www.vernacularbuildingglossary.org.uk/a-z/baluster/)
- [Looking at Buildings: Rib Vaults](https://www.lookingatbuildings.org.uk/styles/medieval/roofs-and-vaults/stone-vaulting/rib-vaults.html)
- [Visual Dictionary: Cathedral Vault](https://www.visualdictionaryonline.com/arts-architecture/architecture/cathedral/vault.php)
- [De Ferranti Glossary: Voussoir](https://deferranti.com/index.php/glossary/view/gl229220)
- [Designing Buildings: Cyma/Cornice](https://www.designingbuildings.co.uk/wiki/Cyma)
- [Designing Buildings: Scotia/Fillet](https://www.designingbuildings.co.uk/wiki/Scotia)
- [Architecture Dictionary: Cyma](https://www.archdictionary.com/cyma)

Geometric pattern references:

- [The Met: Geometric Patterns in Islamic Art](https://www.metmuseum.org/en/essays/geometric-patterns-in-islamic-art)
- [The Met: Islamic Art and Geometric Design](https://www.metmuseum.org/-/media/files/learn/for-educators/publications-for-educators/islamic_art_and_geometric_design.pdf)
- [Archnet: Drawings of Muqarnas from The Topkapi Scroll](https://www.archnet.org/publications/73)
- [Nature: Geometric decomposition and analysis of Konya Sahib Ata mosque portal muqarnas](https://www.nature.com/articles/s40494-024-01530-9)

## Guardrails

- This doc is a working vocabulary, not proof that every generated asset is historically correct.
- Do not claim building-code compliance from visual references.
- Do not claim structural safety or fabrication readiness.
- Do not turn every construction line into mesh.
- Do not hide design choices inside Blender scripts.
