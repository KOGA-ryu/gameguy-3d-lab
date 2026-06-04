# Gothic Railing Post Build Plans V0

## Machine-Readable Source

The first Gothic railing post style sheets live here:

```text
data/architecture/component_style_sheets/railings/gothic_railing_post_style_sheets_v0.json
```

They are registered by:

```text
data/architecture/component_style_sheets/component_style_sheet_registry_v0.json
```

Validate with:

```bash
python3 scripts/validate_component_style_sheets_v0.py
```

## First Style Sheets

### `gothic_railing_post.buttress_newel_v0`

Purpose:

```text
square post -> chamfered plinth -> buttress-like face strips -> rail sockets -> blind pointed arch panel -> stepped cap
```

Geometric priorities:

- square and octagon footprints
- raised rectangular/trapezoid strips on four sides
- shallow pointed-arch face recesses
- bevels that keep the low-poly mass readable

Likely Blender tools:

- `primitive_cube_add`
- `mesh_from_pydata`
- `object_duplicate_radial`
- `modifier_boolean`
- `modifier_mirror`
- `modifier_bevel`
- `modifier_weighted_normal`

### `gothic_railing_post.clustered_shaft_newel_v0`

Purpose:

```text
compound-pier idea -> center shaft -> attached radial ribs -> collar rings -> square-to-round-to-square transition
```

Geometric priorities:

- low-segment round or lobed shaft
- radial rib count as a knob
- entasis/taper as a section-stack option
- collars at base and below cap

Likely Blender tools:

- `primitive_cylinder_add`
- `mesh_from_pydata`
- `object_duplicate_radial`
- `primitive_torus_add`
- `modifier_screw`
- `shade_smooth`
- `modifier_weighted_normal`

### `gothic_railing_post.blind_tracery_box_newel_v0`

Purpose:

```text
simple box post -> recessed face fields -> selectable quatrefoil/rosette/pointed linework
```

Geometric priorities:

- keep the box core clean
- apply tracery as shallow relief first
- make foil count and motif depth editable
- repeat or omit faces by side mask

Likely Blender tools:

- `primitive_cube_add`
- `mesh_from_pydata`
- `modifier_boolean`
- `object_duplicate_radial`
- `modifier_solidify`
- `modifier_bevel`

### `gothic_railing_post.pinnacle_newel_v0`

Purpose:

```text
named rail sockets -> stepped cap -> octagon transition -> small spire finial
```

Geometric priorities:

- sockets are explicit connector contracts
- finial is optional and detachable
- spire stays faceted, not over-smoothed

Likely Blender tools:

- `mesh_from_pydata`
- `modifier_boolean`
- `modifier_mirror`
- `primitive_cone_add`
- `primitive_cube_add`
- `shade_flat`
- `modifier_bevel`

### `gothic_railing_post.crocketed_finial_newel_v0`

Purpose:

```text
simple post core -> cap/finial -> repeated low-poly crockets -> validation/export readiness
```

Geometric priorities:

- crockets start as separate named ornaments
- array count, spacing, projection, and side mask are knobs
- ornament must not alter rail socket placement

Likely Blender tools:

- `mesh_from_pydata`
- `modifier_array`
- `object_duplicate_radial`
- `modifier_bevel`
- `modifier_weighted_normal`
- `uv_smart_project`
- `material_principled_shader`
- `calculate_bounds`
- `validate_non_manifold`

## Next Compiler Slice

The next practical code slice should be:

```text
3D-LAB-0072 component_style_sheet_to_post_recipe_v0
```

Goal:

```text
select one style sheet
-> emit a small source recipe
-> compile deterministic gameguy_asset_v0 JSON
-> validate
-> preview in Blender later
```

Recommended first target:

```text
gothic_railing_post.blind_tracery_box_newel_v0
```

Reason:

It keeps the post body simple while proving the core demand: taxonomy part,
source shapes, selectable relief, tool sequence, and named geometry can all
come from a reusable style sheet.
