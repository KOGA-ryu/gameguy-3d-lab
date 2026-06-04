# Measurement-Backed ASCII Grid V0

## Core Idea

Every character is a measurable cell.

```text
glyph + row/col + source pixel bbox + model-space bbox + role tags
```

This makes ASCII useful for 3D planning because a character is no longer just a
visual mark. It can say:

```text
I am the left edge of a cap.
I came from this source-pixel area.
I occupy this X/Z area in abstract meters.
I should become a bevel, cutter, raised strip, socket hint, or panel later.
```

## Minimum Source Resolution

Use `960 px` minimum source dimension for serious planning.

Suggested packet:

```text
master source: 960 px minimum
overview ASCII: 160-240 columns
detail crop ASCII: 240-480 columns
micro crop ASCII: up to 960 columns
metadata JSON: cells, regions, measurements, operations
```

One giant sheet is not the goal. The useful output is a packet:

```text
post_overview.txt
post_edges.txt
post_cap_crop.txt
post_shaft_crop.txt
post_base_crop.txt
post_ascii_plan.json
```

## Cell Data

Each annotated cell should include:

```json
{
  "cell_id": "socket_left_r8_c7",
  "row": 8,
  "col": 7,
  "glyph": "[",
  "source_px_bbox": [395, 452, 452, 508],
  "local_xz_bbox_m": [-0.075, 0.4, -0.025, 0.45],
  "brightness": 0.55,
  "edge_strength": 0.86,
  "edge_direction": "corner",
  "geometry_role": "rail_socket_hint_left",
  "region_id": "rail_socket_hint",
  "measurement_refs": ["cell_width_m", "cell_height_m"],
  "operation_hints": ["boolean_cut", "relief_stack", "bevel_edges"],
  "blender_tool_hints": ["mesh_from_pydata", "modifier_boolean", "modifier_bevel"],
  "depth_intent": "recessed"
}
```

## Region Data

Cells group into regions:

- finial
- cap
- collar
- shaft
- face panel
- socket hint
- base
- plinth
- damage
- ornament

Each region should declare whether it is accepted for generation.

This matters because rejected generated art, guide grids, and visual noise can
stay in the plan without becoming source geometry.

## Blender Tooling Bridge

ASCII cells should never execute Blender directly.

They can hint:

- `primitive_cube_add` for block masses
- `mesh_from_pydata` for traced profiles and cutters
- `modifier_boolean` for recesses and sockets
- `modifier_bevel` for readable edge catch lights
- `modifier_solidify` for linework thickness
- `modifier_weighted_normal` for clean low-poly faces
- `uv_smart_project` for simple UVs
- `material_principled_shader` for named material regions

The later compiler decides whether those hints become an actual tool plan.

## QC Questions

Before Blender:

- Does the ASCII silhouette read?
- Are cap, shaft, base, and socket regions named?
- Are raised and recessed details distinguishable?
- Are measurement cells attached to the important marks?
- Are operation hints legal repo terms?
- Are Blender tool hints known tool IDs?
- Is the generated concept image accepted or rejected as source?
- Is render still blocked until promotion?
