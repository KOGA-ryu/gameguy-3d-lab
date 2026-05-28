# LDtk Full Notes v0

## 1. Source URLs

- https://ldtk.io/json/
- https://ldtk.io/docs/
- https://ldtk.io/docs/game-dev/json-overview/
- https://ldtk.io/docs/game-dev/json-overview/optional-separate-levels/
- https://ldtk.io/files/JSON_SCHEMA.json
- https://ldtk.io/files/MINIMAL_JSON_SCHEMA.json

## 2. What Documentation Was Read

- LDtk documentation entry points and JSON version page.
- JSON overview for root structure, `defs`, `levels`, and separate level behavior.
- Optional separate levels page for `.ldtkl` files.
- Generated JSON schema and minimal schema for field names and data structures.

## 3. Relevant Technical Concepts

- LDtk stores project data as JSON.
- Main project file extension is `.ldtk`.
- Optional separate level files use `.ldtkl`; project keeps definitions while level content is stored per level.
- The root is split into project settings, definitions (`defs`), level instances (`levels`), table-of-contents (`toc`), worlds, and editor metadata.
- `defs` contains reusable definitions: layers, entities, tilesets, enums, external enums, level fields.
- `levels` contains actual level instances, coordinates, dimensions, custom fields, and layer instances.
- Layer types include IntGrid, Entities, Tiles, and AutoLayer.
- LDtk duplicates important definition-derived data into double-underscore fields on instances, making importers easier.
- Many schema fields are editor-only; v0 should ignore them unless they carry gameplay/map content.

## 4. Relevant Data Fields / API Fields / Formulas

### Root Project Fields

Important fields:

```text
jsonVersion: string
iid: string unique project identifier
bgColor: string
defaultGridSize: int
defaultEntityWidth: int
defaultEntityHeight: int
defaultPivotX/Y: number 0..1
externalLevels: bool
simplifiedExport: bool
worldLayout: null | "Free" | "GridVania" | "LinearHorizontal" | "LinearVertical"
worldGridWidth/worldGridHeight: int|null
defs: Definitions
levels: Level[]
worlds: World[]
toc: TableOfContentEntry[]
```

Mostly editor/internal or optional for us:

```text
appBuildId
backupLimit
backupOnSave
customCommands
flags
imageExportMode
identifierStyle
minifyJson
nextUid
exportTiled
exportLevelBg
levelNamePattern
```

### Definitions

```text
defs.layers: LayerDef[]
defs.entities: EntityDef[]
defs.tilesets: TilesetDef[]
defs.enums: EnumDef[]
defs.externalEnums: EnumDef[]
defs.levelFields: FieldDef[]
```

Useful definition data:

- Layer definitions give `identifier`, `uid`, `type`, `gridSize`, opacity, offsets, required/excluded tags, int-grid values, tileset references, and auto-rule groups.
- Entity definitions give dimensions, tags, custom field definitions, color, tile rendering, and shape constraints.
- Tileset definitions give `identifier`, `uid`, `relPath`, `tileGridSize`, `pxWid`, `pxHei`, `spacing`, `padding`, enum tags, and custom tile metadata.
- Enums are useful for controlled semantic tags: terrain class, hazard type, building role, road type.

### Level Fields

Common useful fields from schema/docs:

```text
identifier: string
iid: string
uid: int
worldX: int
worldY: int
worldDepth: int
pxWid: int
pxHei: int
bgColor: string
fieldInstances: FieldInstance[]
layerInstances: LayerInstance[] | null
externalRelPath: string | null when separate levels are enabled
neighbours: NeighbourLevel[]
```

Build mapping:

- `worldX/worldY`: placement of level/map cube in a larger world.
- `pxWid/pxHei`: level pixel dimensions; convert via `gridSize` to cell dimensions.
- `fieldInstances`: level-level metadata like biome, seed, cube id, vertical levels.
- `layerInstances`: actual cell/entity/tile data unless externalized.

### Layer Instance Fields

Important fields from LDtk schema:

```text
__identifier: string
__type: "IntGrid" | "Entities" | "Tiles" | "AutoLayer"
__cWid: int grid width in cells
__cHei: int grid height in cells
__gridSize: int
__opacity: number
__pxTotalOffsetX/Y: int
defUid: int
levelId: int
iid: string
gridTiles: Tile[]
autoLayerTiles: Tile[]
entityInstances: EntityInstance[]
intGridCsv: int[]
```

### Entity Instance Fields

```text
iid: string
defUid: int
__identifier: string
__grid: [x, y] grid coordinates
px: [x, y] pixel coordinates in level space
__worldX: int|null
__worldY: int|null
__pivot: [x, y] values 0..1
width: int
height: int
fieldInstances: FieldInstance[]
__tags: string[]
```

### Field Instance Fields

```text
__identifier: string
__type: string such as Int, Float, Bool, String, Enum(name), Point, Tile, EntityRef
__value: actual typed value or array
defUid: int
realEditorValues: array editor raw values
```

Use field instances for our custom data if adopting LDtk:

- `elevation_z`
- `height_band`
- `terrain_surface`
- `road_type`
- `plot_id`
- `building_role`
- `asset_socket_type`
- `hazard_type`
- `semantic_tags`

### Tile Fields

```text
t: tile id in tileset
px: [x, y] pixel coordinates in layer
src: [x, y] pixel coordinates in tileset
f: flip bits, bit 0 X flip, bit 1 Y flip
a: alpha 0..1
d: internal data; tile layer often [coordId], auto-layer often [ruleId, coordId]
```

Coordinate ID concept: LDtk uses integer coordinate IDs in some tile data. For v0 adoption, derive explicit `(cell_x, cell_y)` from `px / gridSize` instead of depending on internal `d`.

### Separate Level Files

If `externalLevels` is true:

- The project file stores definitions and level metadata.
- Each level content is saved as a `.ldtkl` file under a subfolder named after the project.
- `.ldtkl` includes a header, level data, and all layer content.

Importer implication: load root `.ldtk`, then for each level with `externalRelPath`, load the corresponding `.ldtkl` before compiling.

## 5. Minimal v0 Subset For Our Engine

LDtk is not recommended as the v0 primary format. If adopted later, support:

```text
root:
  jsonVersion
  iid
  defaultGridSize
  externalLevels
  defs.layers
  defs.entities
  defs.enums
  levels

level:
  identifier
  iid
  worldX/worldY
  pxWid/pxHei
  fieldInstances
  layerInstances
  externalRelPath

layer instance:
  __identifier
  __type
  __cWid/__cHei
  __gridSize
  intGridCsv
  gridTiles
  entityInstances

entity:
  __identifier
  __grid
  px
  width/height
  fieldInstances
  __tags
```

Ignore for first adoption:

- AutoLayer rule definitions and rule internals.
- Editor-only fields and backup/build metadata.
- Image exports.
- Multi-world advanced mode unless our world map needs it.
- Table-of-contents export.
- Tiled export generated by LDtk.

## 6. Direct Project Mapping

- `32x32x8 map cube`: one LDtk level can represent one cube template; `pxWid/pxHei` map to 32x32 cells when `gridSize` is chosen consistently; `z_levels=8` should be a custom level field.
- `hex/elevation cells`: LDtk is fundamentally grid/tile based; store axial `q,r` as entity or int-grid metadata if needed, but Red Blob remains canonical.
- `terrain mesh compiler`: IntGrid or tile layer values can map to height/surface classes.
- `visible face meshing`: use compiled internal height deltas, not LDtk tiles directly.
- `seam/fold grammar`: represent fold sites as entities with fields or as tagged int-grid values.
- `road/path layer`: Entities or tile layers; polylines are less central in LDtk than Tiled, so roads may be entity chains or int-grid overlays.
- `building plot layer`: Entities with size, grid coordinate, tags, and fields.
- `asset placement layer`: Entities with field instances for `asset_ref`, `socket_type`, `orientation`.
- `Blender proof renderer`: consume compiled internal map only.
- `future AI affordance graph`: LDtk entity tags and enum fields are useful for affordance tags if adopted.

## 7. Deferred Parts

- LDtk importer in v0.
- AutoLayer rule system.
- Separate `.ldtkl` loading until LDtk is actually adopted.
- LDtk-to-Tiled compatibility export.
- Multi-world LDtk layout.
- Tile rendering and image export.

## 8. Risks / Ambiguity

- LDtk JSON evolves with app versions; importers should check `jsonVersion`.
- Many root fields are editor metadata and should not become engine requirements.
- LDtk separate levels add path and loading complexity.
- LDtk works well for authored templates but not necessarily for source-of-truth procedural generation.
- Hex support is not the core LDtk model; Red Blob axial/cube math remains better for our hex terrain engine.

## 9. Build Dex Implementation Notes

- Do not implement LDtk in v0 unless a map-template workflow explicitly requires it.
- If implemented later, write a converter from minimal LDtk subset to the repo’s internal map cube, terrain cells, plots, and asset sockets.
- Treat `defs` as schema metadata and `levels[].layerInstances` as actual content.
- Preserve `iid` as stable cross-reference ids; use repo ids for generated artifacts.

