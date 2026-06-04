# Asset Readiness TODO List V0

This is the repeatable TODO list for preparing one asset before the operator
does the Blender pass.

## Phase 1: Pick The Exact Asset

- Choose one asset family: railing, stair, window, door, trim, ceiling, wall,
  floor, column, arch, roof, terrain, light, gate, ruin kit, prop, or mechanism.
- Choose one exact component, not a full scene.
- Name the asset with a stable ID.
- Decide whether the asset is structural, decorative, interactive, or a kit part.
- Decide the first build goal: blockout, polished prototype, game-ready asset, or
  style-sheet proof.

## Phase 2: Build The Reference Packet

- Collect 3 to 8 reference images for the exact component.
- Mark which reference is the primary target.
- List visible anatomy terms from the reference.
- List what must be copied as shape language, not texture.
- List what is ignored for the first pass.
- Record license/provenance if the image will be used beyond morphology study.

## Phase 3: Create The Drawing Guide

- Draw or generate the construction grid.
- Mark primary centers, axes, circles, arcs, polygons, and tangent points.
- Mark selected visible lines.
- Mark construction lines that should be hidden or omitted.
- Split the drawing into buildable pieces: solids, cutters, trims, ribs, panels,
  sockets, and ornaments.
- Add a side profile or cross-section when the shape needs thickness.

## Phase 4: Define The Component Style Ledger

- Map every visible part to a taxonomy name.
- Map every part to simple source shapes.
- Map every part to operations: extrude, bevel, boolean cut, sweep, array,
  mirror, radial stack, section stack, relief stack, or profile stack.
- Define edit knobs: width, height, depth, radius, taper, count, spacing, bevel,
  cut depth, lip thickness, and material role.
- Define what the asset should still look like if detail is reduced.

## Phase 5: Define Game-Asset Requirements

- Choose unit scale in meters.
- Set origin and pivot behavior.
- Set grid snapping size.
- Define sockets/connectors.
- Define collision proxy.
- Define LOD tiers.
- Define material slots and UV strategy.
- Define hardware-tier behavior, including whether decals are allowed.
- Define export format and preview requirements.

## Phase 6: Fill The Blender Tool Workcard

- Choose a base-form tool.
- Choose assembly tools.
- Choose shape-refinement tools.
- Choose detail/sculpt tools if needed.
- Choose retopo/cleanup tools.
- Choose UV/material tools.
- Choose validation/export tools.
- Write the exact tool order.
- Write what each tool is supposed to accomplish visually.

## Phase 7: Prepare The Operator Pass

- Provide the reference packet.
- Provide the drawing guide.
- Provide the tool workcard.
- Provide the scale, origin, socket, and material rules.
- Provide a short "do not worry about this yet" list.
- Provide the expected final visual read from three distances:
  close, gameplay, and silhouette.

## Phase 8: Capture Corrections

- Record what looked wrong.
- Record which Blender tool changed it.
- Record which term the operator used to describe the correction.
- Convert repeated corrections into edit knobs.
- Promote stable corrections into source recipes or component style sheets.
- Leave one-off visual experiments out of source until they repeat.

## Phase 9: Promote To Data

Promote only after the hand workflow is clear:

```text
reference packet
-> drawing guide
-> component style sheet
-> source recipe
-> deterministic tool plan
-> Blender adapter preview/export
```

If Blender had to invent the design, the source layer is still missing data.

