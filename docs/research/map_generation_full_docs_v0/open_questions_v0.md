# Open Questions v0

## Hex Coordinate Policy

- Should internal maps use pointy-top or flat-top hexes?
- Should `hex_grid.layout` encode orientation as `pointy`/`flat`, `staggeraxis`, or a Red Blob layout matrix name?
- Is a 32x32 map cube a rectangular axial adapter, a radius-shaped hex map clipped to 32x32, or a square editor envelope converted into axial cells?

## Vertical Scale

- Is the `8` in `32x32x8` eight meters, eight cell layers, or eight abstract vertical steps?
- Should terrain `final_height` be continuous meters or integer vertical bands?
- Should terrace heights snap to integer `z` layers?

## Tiled Import

- Should v0 require `tilewidth=1` and `tileheight=1`, or allow pixel scaling?
- Are roads best represented as polylines, tile layers, or object rectangles?
- Should Tiled custom property `class` be used, or should all semantic tags stay in `properties`?

## LDtk Deferral

- Do we want LDtk templates later for authored room chunks?
- If adopted, should levels map to whole 32x32x8 cubes or individual floor/building templates?
- Should LDtk entities become asset sockets or building plot objects?

## WFC / Model Synthesis

- Is our first solver a simple socket validator, a deterministic grammar expansion, or actual entropy-based WFC?
- How should hex six-neighbor sockets map to Cartesian WFC libraries?
- What is the contradiction policy: restart, backtrack, local repair, or reject recipe?

## Blender Proof Rendering

- Should terrain chunks be one object per chunk, one object per material, or one object per semantic layer?
- Should proof renders triangulate all faces for consistency?
- How should receipts record `mesh.validate()` corrections?

## Future Geometry Backends

- What failure threshold would justify CadQuery or Manifold adoption?
- Should asset recipes remain backend-neutral or expose backend-specific operations?
- Do we need watertight/manifold guarantees for game proof assets, or only for future export/manufacturing-adjacent workflows?

