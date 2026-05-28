# Tiled Full Notes v0

## 1. Source URLs

- https://doc.mapeditor.org/en/stable/reference/json-map-format/
- https://doc.mapeditor.org/en/stable/reference/tmx-map-format/
- https://doc.mapeditor.org/en/stable/manual/custom-properties/
- https://doc.mapeditor.org/en/stable/manual/objects/

## 2. What Documentation Was Read

- JSON map format reference: map, layers, chunks, objects, tilesets, properties, terrain, Wang sets.
- TMX map format reference: XML counterpart to JSON, useful for field parity and terminology.
- Custom properties manual: supported property types and typed custom metadata.
- Working with objects manual: rectangle, point, ellipse/capsule, polygon, and polyline object semantics.

## 3. Relevant Technical Concepts

- Tiled JSON is a practical interchange schema for maps composed of layers.
- Map root holds dimensions, tile size, orientation, layers, tilesets, and custom properties.
- Layers can be tile layers, object groups, image layers, or groups.
- Tile layers encode grid values as GIDs in `data`; infinite maps use `chunks`.
- Object layers encode editor-placed rectangles, points, polygons, polylines, tile objects, and text.
- Group layers nest layers and can carry shared properties/visibility/opacity/offset.
- Custom properties can attach domain metadata to maps, layers, objects, tilesets, tiles, terrain, and Wang metadata.
- Terrain and Wang metadata can represent edge/corner compatibility but should not be required in v0.

## 4. Relevant Data Fields / API Fields / Formulas

### Map Root Fields

Core fields from JSON format:

```text
type: "map"
version: string
tiledversion: string
orientation: "orthogonal" | "isometric" | "oblique" | "staggered" | "hexagonal"
renderorder: "right-down" | "right-up" | "left-down" | "left-up"
width: int
height: int
tilewidth: int
tileheight: int
hexsidelength: int, hex maps only
staggeraxis: "x" | "y", staggered/hex only
staggerindex: "odd" | "even", staggered/hex only
infinite: bool
layers: array
tilesets: array
properties: array
nextlayerid: int
nextobjectid: int
backgroundcolor: string optional
compressionlevel: int optional
```

### Layer Fields

```text
id: int
name: string
type: "tilelayer" | "objectgroup" | "imagelayer" | "group"
visible: bool
opacity: float 0..1
x: int, always 0 in fixed maps
y: int, always 0 in fixed maps
offsetx: double
offsety: double
parallaxx: double
parallaxy: double
properties: array

tilelayer-only:
  width: int
  height: int
  data: array unsigned int GIDs | base64 string
  encoding: "csv" | "base64"
  compression: "zlib" | "gzip" | "zstd" | empty
  chunks: array for infinite maps
  startx/starty: int for infinite maps

objectgroup-only:
  draworder: "topdown" | "index"
  objects: array

group-only:
  layers: array
```

### Chunk Fields

```text
x: int tile coordinate
y: int tile coordinate
width: int
height: int
data: array or encoded string
```

### Object Fields

```text
id: int
name: string
type: string / class-like object type
x: double pixels
y: double pixels
width: double pixels
height: double pixels
rotation: double degrees clockwise
visible: bool
opacity: double
properties: array

shape flags / data:
  point: bool
  ellipse: bool
  capsule: bool
  polygon: array of {x, y} points relative to object position
  polyline: array of {x, y} points relative to object position
  gid: int if object represents a tile
  text: object for text
  template: string template file
```

Tiled object coordinate rule: `x` and `y` are pixel coordinates; polygon/polyline points are relative to the object's position.

### Property Fields

```text
name: string
type: "string" | "int" | "float" | "bool" | "color" | "file" | "object" | "class"
propertytype: string optional for custom property types
value: typed value
```

Use typed properties to avoid stringly typed elevation/build tags.

### Tileset / Tile Metadata

Useful v0 fields:

```text
tilesets[]:
  firstgid: int for embedded/external tilesets in maps
  source: string for external tileset
  name: string
  tilewidth, tileheight, tilecount, columns
  tiles: array optional tile definitions
  terrains: array optional
  wangsets: array optional

tile definition:
  id: local tile id
  type/class: semantic type
  properties: array
  objectgroup: collision/socket shapes
```

Wang sets:

```text
wangsets[]:
  name: string
  type: "corner" | "edge" | "mixed"
  colors: array of wang colors
  wangtiles: array

wangtile:
  tileid: local tile id
  wangid: array[8] of color indexes
```

For v0, Wang metadata is useful conceptually for edge compatibility but not required.

## 5. Minimal v0 Subset For Our Engine

Support this first:

```json
{
  "type": "map",
  "orientation": "orthogonal",
  "width": 32,
  "height": 32,
  "tilewidth": 1,
  "tileheight": 1,
  "layers": [
    {
      "id": 1,
      "name": "terrain_height",
      "type": "tilelayer",
      "width": 32,
      "height": 32,
      "data": [],
      "properties": []
    },
    {
      "id": 2,
      "name": "semantic_objects",
      "type": "objectgroup",
      "objects": []
    }
  ],
  "properties": []
}
```

Recommended v0 layer names:

- `terrain_height`: tilelayer or custom array values for height/elevation class.
- `terrain_surface`: tilelayer for ground/stone/water/hazard classes.
- `roads_paths`: objectgroup with polylines and typed properties.
- `building_plots`: objectgroup with rectangles/polygons and plot metadata.
- `hazards`: objectgroup with polygons/rectangles and hazard tags.
- `asset_sockets`: objectgroup with points/rectangles and `asset_socket` properties.
- `semantic_tags`: objectgroup for gameplay tags not attached elsewhere.

Fields to ignore for v0:

- `imagelayer`, `image`, `transparentcolor`, `repeatx`, `repeaty`.
- Parallax fields.
- Blend mode.
- Infinite map `chunks` unless chunk streaming becomes explicit.
- Embedded tile animations.
- Text objects.
- Templates.
- Wang sets as required schema; keep optional.
- Compression/base64. Require native JSON arrays for v0 readability.

## 6. Direct Project Mapping

- `32x32x8 map cube`: Tiled `width=32`, `height=32`, custom property `z_levels=8`, `cell_size_m`.
- `hex/elevation cells`: Tiled is square/orthogonal by default; use it as an editor/interchange envelope, then convert objects/properties into axial cells if needed.
- `terrain mesh compiler`: read height/surface layers, compile final hex/square cell records, then emit mesh from internal contracts.
- `visible face meshing`: mark visible faces from layer height deltas, not from Tiled rendering.
- `road/path layer`: polylines with properties `road_type`, `width_cells`, `movement_cost`, `semantic_tags`.
- `building plot layer`: rectangles/polygons with `plot_id`, `space_role`, `floor`, `height_budget`, `asset_set`.
- `asset placement layer`: points/rectangles with `socket_id`, `socket_type`, `orientation`, `asset_ref`, `optional`.
- `Blender proof renderer`: reads internal compiled map, not Tiled directly.
- `future AI affordance graph`: convert objects/layers into graph tags: walkable, blocked, cover, hazard, entry, connector.

## 7. Deferred Parts

- Full TMX XML import/export. JSON is enough for v0.
- Infinite maps and chunks.
- Compressed/base64 tile data.
- Full Tiled tileset image handling.
- Wang sets as solver input. Use our own socket model first.
- Tiled object templates.
- Editor round-trip fidelity.

## 8. Risks / Ambiguity

- Tiled's hexagonal map model uses pixel/stagger fields, while our engine uses Red Blob axial/cube math. Avoid treating Tiled hex export as canonical until a converter is defined.
- GIDs include flip bits in Tiled global IDs. If tile graphics are ignored, strip/ignore flip flags or avoid GIDs for semantic v0.
- Object coordinates are pixel-based; repo contracts use abstract meters. Define `tilewidth=1`, `tileheight=1`, or explicit `pixels_per_meter`.
- Custom class/property types can become too editor-specific; keep v0 properties simple typed primitives.

## 9. Build Dex Implementation Notes

- Implement a minimal Tiled-style JSON importer that accepts fixed-size maps, uncompressed tile arrays, object layers, group layers, and custom properties.
- Treat Tiled JSON as input/template data, not as the internal source of truth.
- Convert layer data into repo records:
  - tile layers -> cell fields or semantic grids.
  - object rectangles/polygons -> plots/hazards/regions.
  - polylines -> roads/paths.
  - points -> asset sockets/spawn markers.
- Preserve unknown fields under `source_meta.tiled` if round-trip is useful, but do not require them.

