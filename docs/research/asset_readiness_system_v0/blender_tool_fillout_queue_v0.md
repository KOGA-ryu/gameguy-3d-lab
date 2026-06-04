# Blender Tool Fillout Queue V0

The repo already has a machine-readable Blender tool dictionary:

```text
data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json
```

This page is the human tool-card queue. Each tool card should eventually explain
what the tool does, when to use it, how to use it effectively, common mistakes,
and which asset families need it.

## Tool Card Template

```text
tool_id:
plain English:
best used for:
avoid when:
key settings:
visual result:
asset families:
common mistakes:
operator notes:
source fields needed:
```

## Stage 1: Base Form

Use these to create the first physical mass.

| Tool IDs | Use Effectively |
| --- | --- |
| `primitive_cube_add`, `primitive_cylinder_add`, `primitive_cone_add`, `primitive_torus_add` | Fast blockouts, posts, collars, caps, rings, sockets, and simple rails. Keep dimensions explicit and apply transforms before later edits. |
| `mesh_from_pydata`, `bmesh_create` | Custom low-poly shapes, sacred-geometry contours, compound pier profiles, tracery cutters, and deterministic geometry from source coordinates. Prefer this when the shape must match a recipe exactly. |
| `curve_bezier_add`, `curve_polyline_add` | Rails, ribs, arches, scrolls, vine-like ornament, and paths that need a profile swept along a curve. |
| `extrude_region`, `extrude_faces`, `extrude_edges`, `extrude_vertices` | Turn a 2D drawing or face into thickness. Good for panels, trim, ribs, and negative-space cutters. |
| `modifier_screw` | Turn a side profile into a radial object: balusters, posts, finials, beads, rings, and lathe-like forms. |

## Stage 2: Assembly

Use these to repeat, mirror, combine, and cut parts.

| Tool IDs | Use Effectively |
| --- | --- |
| `modifier_array` | Repeated balusters, ribs, beads, blocks, steps, crenellations, and tileable modules. Define count and spacing from source, not by eye. |
| `modifier_mirror` | Symmetric rail panels, window tracery, door frames, gothic arches, and post faces. Model one side cleanly, mirror across the true centerline. |
| `object_duplicate_radial` | Rosettes, radial spokes, circular windows, finials around a post, and repeated ornament around a column. |
| `modifier_boolean`, `gn_mesh_boolean` | Sockets, recesses, cutouts, tracery voids, mortises, panel reveals, and negative-space ornament. Keep cutters named and record cut depth. |
| `bridge_edge_loops`, `join_objects`, `split_separate` | Join sections, separate details for materials, and keep complex assets editable before final export. |
| `gn_instance_on_points`, `gn_join_geometry`, `gn_realize_instances` | High-repeat detail like bolts, beads, crockets, leaves, spokes, and modular ornament. Use when manual duplication would be fragile. |

## Stage 3: Shape Refinement

Use these to make hard forms read as intentional sculpture.

| Tool IDs | Use Effectively |
| --- | --- |
| `inset_faces` | Raised panels, inner fields, lips, borders, and recessed faces. Use measured inset widths so panels stay consistent. |
| `bevel_mesh_edges`, `modifier_bevel` | Chamfers, softened arrises, readable stone edges, rail grips, base lips, and worn corners. Small bevels often matter more than extra geometry. |
| `modifier_weighted_normal`, `mark_sharp`, `shade_flat`, `shade_smooth` | Control how low-poly geometry catches light. Weighted normals can make simple meshes read more finished. |
| `modifier_solidify` | Give flat tracery, panels, ribs, and plates usable thickness. |
| `knife_project`, `bisect_mesh`, `loopcut_slide` | Project 2D pattern lines onto geometry, slice panels, and create controlled edge loops for later bevels or cuts. |
| `modifier_simple_deform`, `modifier_lattice`, `gn_set_position` | Bend rails, taper shafts, bow ribs, create entasis, and turn flat construction patterns into curved forms. |

## Stage 4: Sculpt And Surface Detail

Use these only when shape grammar and base modeling are already correct.

| Tool IDs | Use Effectively |
| --- | --- |
| `modifier_displace` | Stone roughness, hammered metal, carved wear, chipped edges, and terrain-like surface breakup. Keep it subtle for low-compute targets. |
| `sculpt_draw`, `sculpt_crease`, `sculpt_scrape`, `sculpt_smooth` | Manual polish for hero assets or reference-study passes. Record useful sculpt decisions so they can become procedural later. |

## Stage 5: Retopo And Cleanup

Use these to make the asset usable after detail work.

| Tool IDs | Use Effectively |
| --- | --- |
| `merge_vertices`, `remove_doubles`, `modifier_weld` | Clean duplicate vertices after booleans, arrays, or mirrored pieces. |
| `recalc_normals`, `flip_normals`, `validate_non_manifold` | Make faces point correctly and catch mesh problems before export. |
| `grid_fill`, `fill_holes`, `bridge_edge_loops` | Close openings created during cuts and section transitions. |
| `modifier_decimate`, `modifier_triangulate`, `modifier_remesh`, `modifier_shrinkwrap` | Build lower-detail versions, game collision helpers, or cleaner topology after heavy operations. |

## Stage 6: UV And Materials

Use these to make the same geometry support multiple dungeon styles.

| Tool IDs | Use Effectively |
| --- | --- |
| `material_slot_add`, `material_assign_by_part`, `gn_set_material` | Assign semantic material roles: stone_core, edge_wear, shadow_recess, metal_socket, moss_zone, waterline, scorch, and trim. |
| `mark_seam`, `uv_unwrap`, `uv_smart_project`, `uv_cube_project`, `uv_pack_islands` | Prepare UVs for trim sheets, tileable materials, and packed low-compute assets. Boxy assets often start with cube projection. |
| `material_principled_shader`, `procedural_noise_texture`, `procedural_bump_map` | Preview material direction before dedicated texture work. Base materials must carry the asset when decals are disabled. |

## Stage 7: Validation And Export

Use these before considering an asset ready.

| Tool IDs | Use Effectively |
| --- | --- |
| `origin_set`, `calculate_bounds` | Confirm pivot, local origin, and scale. Bad origins make modular placement painful. |
| `create_collision_proxy`, `create_lod_variant` | Create gameplay helpers and lower-detail versions early, not after the asset is already too complex. |
| `render_workbench_preview` | Produce quick evidence from multiple angles without pretending it is a final render. |
| `export_gltf`, `export_fbx`, `export_obj`, `save_blend_file` | Export only after origin, sockets, collision, LOD, material slots, and naming are settled. |

## First Tool Cards To Fill

Priority for practical writeups:

1. `mesh_from_pydata`
2. `modifier_bevel`
3. `modifier_weighted_normal`
4. `modifier_boolean`
5. `inset_faces`
6. `extrude_faces`
7. `modifier_array`
8. `modifier_mirror`
9. `modifier_screw`
10. `curve_bevel_profile`
11. `curve_to_mesh`
12. `uv_cube_project`
13. `material_assign_by_part`
14. `create_collision_proxy`
15. `create_lod_variant`

These first cards now live in:

```text
docs/research/asset_readiness_system_v0/blender_tool_cards/
```

Use the cards as the first operator-facing notes before turning them into
machine-readable tool-plan requirements.
