# CadQuery Full Notes v0

## 1. Source URLs

- https://cadquery.readthedocs.io/
- https://cadquery.readthedocs.io/en/latest/workplane.html
- https://cadquery.readthedocs.io/en/latest/sketch.html
- https://cadquery.readthedocs.io/en/latest/importexport.html
- https://cadquery.readthedocs.io/en/latest/classreference.html

## 2. What Documentation Was Read

- CadQuery documentation overview, workplane concepts, sketch concepts, import/export docs, and class reference.

## 3. Relevant Technical Concepts

- CadQuery is a Python CAD scripting library for parametric 3D models.
- Workplanes represent a plane in space with a local coordinate system and center point.
- 2D profiles are built on a workplane, then turned into solids with extrude, loft, revolve, or sweep.
- Selectors choose vertices, edges, faces, solids, and wires for later operations.
- Fluent chaining returns new workplane objects and maintains context.
- A context solid is the first/main solid that later features combine with by default.
- Construction geometry can drive placement without becoming final geometry.
- CadQuery outputs robust CAD formats such as STEP and also mesh formats such as STL/3MF.

## 4. Relevant Data Fields / API Fields / Formulas

### Workplane Concepts

```text
Workplane:
  plane origin
  local x/y/z directions
  object stack
  parent workplane
  modelling context
  pending wires
  pending edges
  tags
```

### Core Construction Pattern

```python
import cadquery as cq

solid = (
    cq.Workplane("XY")
    .rect(width, depth)
    .extrude(height)
)
```

### Profile / Sketch Operations

Common operations to model future asset recipes:

```text
circle(radius)
rect(width, height)
polyline(points)
lineTo(x, y)
threePointArc(...)
close()
offset2D(...)
```

### 3D Operations

```text
box(x, y, z)
cylinder(height, radius)
sphere(radius)
extrude(distance, combine=True|False)
loft()
sweep(path)
revolve(angleDegrees)
fillet(radius)
chamfer(distance)
shell(thickness)
```

### Boolean Operations

CadQuery supports boolean-style combination:

```text
union(other)
cut(other)
intersect(other)
combine=False to create separate solids instead of merging into context solid
```

Operators in the class reference also map:

```text
a + b -> union
a - b -> cut
a & b or a * b -> intersect
```

### Export

Export targets include:

```text
STEP
STL
AMF
3MF
SVG
DXF
glTF for assemblies
VRML
```

## 5. Minimal v0 Subset For Our Engine

CadQuery is deferred for v0. Conceptual data model to borrow:

```json
{
  "profile": {
    "plane": "XY",
    "units": "abstract_meter",
    "ops": [
      {"op": "rect", "width": 2.0, "depth": 1.0},
      {"op": "extrude", "height": 3.0}
    ]
  }
}
```

Use Blender mesh arrays now; keep CadQuery in mind for future robust asset generation where parametric solids, booleans, STEP export, and CAD-like profiles matter.

## 6. Direct Project Mapping

- `32x32x8 map cube`: CadQuery not needed.
- `hex/elevation cells`: CadQuery not needed for terrain grid.
- `terrain mesh compiler`: Blender mesh arrays are better for v0.
- `visible face meshing`: CadQuery is overkill.
- `seam/fold grammar`: no direct need.
- `road/path layer`: possible future sweeps along paths, deferred.
- `building plot layer`: future parametric buildings can use workplanes/profiles.
- `asset placement layer`: future robust asset solids can use CadQuery profiles.
- `Blender proof renderer`: v0 proof remains Blender-native.
- `future AI affordance graph`: no direct need.

## 7. Deferred Parts

- CadQuery dependency.
- STEP/3MF export.
- Boolean-heavy CAD assets.
- Loft/sweep/revolve implementation.
- CAD selector model.

## 8. Risks / Ambiguity

- CadQuery/OCC adds a heavier dependency than Blender proof scripts.
- CAD solids and Blender meshes have different topology expectations.
- Export/import into Blender may introduce scaling/material metadata issues.
- Overusing booleans for game assets can hide topology complexity.

## 9. Build Dex Implementation Notes

- Keep the existing asset recipe contract close to CadQuery concepts: profile, workplane, operation, height/depth, compound components.
- Do not adopt CadQuery until a task needs robust CAD export or Blender booleans are too fragile.
- If adopted later, write a compiler from asset recipe JSON to CadQuery scripts, then export mesh/STEP in a separate lane.

