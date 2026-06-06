# Blank Blender Tool Plan Workbench Handoff V0

## Correction

The primary UI must be a blank Blender tool-plan workbench.

It should not start from a petal, flower, scroll, railing, post, column, or any
other asset recipe. Those can become examples later. The first UI surface should
open as an empty ordered list of Blender tool steps and let the user choose
scripts, fill parameters, validate the plan, preview cheaply, and then run
Blender only when the plan is ready.

```text
blank plan
-> add tool step
-> choose tool_id
-> fill step params
-> validate gameguy_tool_plan_v0
-> optional ASCII dry run
-> optional Blender execution
-> execution report
```

## Current Repo Anchors

Use these files as the source of truth:

| Role | Path | Notes |
| --- | --- | --- |
| Tool catalog | `data/architecture/asset_mill/blender_tools/blender_tool_dictionary_v0.json` | Lists 97 Blender tools, stages, categories, lanes, inputs, outputs, APIs. |
| Generic Blender executor | `scripts/execute_blender_tool_plan_v0.py` | Executes supported `gameguy_tool_plan_v0` steps in Blender. |
| ASCII tool-plan dry run | `scripts/render_tool_plan_ascii_dryrun_v0.py` | Consumes the same compiled tool plan and renders primitive front/side/top ASCII previews. |
| Tool-plan compiler | `scripts/compile_blender_tool_plan_v0.py` | Existing asset-family compiler. Useful reference, but not the blank UI. |
| Execution report validator | `scripts/validate_blender_tool_plan_execution_report_v0.py` | Validates Blender execution reports. |
| Tool-card docs | `docs/research/asset_readiness_system_v0/blender_tool_cards/` | Human learning cards for a first subset of tools. |
| UI templates | `data/architecture/asset_mill/blender_tools/blender_tool_ui_templates_v0.json` | Machine-readable controls for the executable tool subset. |
| UI template validator | `scripts/validate_blender_tool_ui_templates_v0.py` | Verifies template coverage against dictionary and executor support. |
| Blank plan creator | `scripts/create_blank_tool_plan_v0.py` | Emits a valid empty `gameguy_tool_plan_v0` draft. |
| Step editor | `scripts/add_tool_plan_step_v0.py` | Adds one template-backed tool step, applies optional param overrides, and canonicalizes stage order. |
| UI plan validator | `scripts/validate_tool_plan_against_ui_templates_v0.py` | Validates a user-edited plan against template controls before ASCII or Blender. |

The UI should read the tool catalog and executor support list. Do not hardcode
only petal-scroll controls.

For actual control rendering, read `blender_tool_ui_templates_v0.json`. The broad
tool dictionary is not enough because some catalog input names differ from the
executor's current param names.

## Backend Calls For The UI

Create an empty workbench plan:

```bash
python3 scripts/create_blank_tool_plan_v0.py \
  --out /tmp/gameguy_tool_plan_ui_editor_v0/plan.json
```

Append a tool with defaults:

```bash
python3 scripts/add_tool_plan_step_v0.py \
  --plan /tmp/gameguy_tool_plan_ui_editor_v0/plan.json \
  --tool-id primitive_cube_add
```

Append a tool with edited params:

```bash
python3 scripts/add_tool_plan_step_v0.py \
  --plan /tmp/gameguy_tool_plan_ui_editor_v0/plan.json \
  --tool-id modifier_bevel \
  --set width_m=0.04 \
  --set segments=2
```

Validate the user-edited plan against the UI contract:

```bash
python3 scripts/validate_tool_plan_against_ui_templates_v0.py \
  --plan /tmp/gameguy_tool_plan_ui_editor_v0/plan.json \
  --json-report /tmp/gameguy_tool_plan_ui_editor_v0/ui_validation.json
```

The step editor sorts by the template stage order and rewrites step orders as
`10, 20, 30...`. This lets the user click `modifier_bevel` before `join_objects`
while still saving a valid plan order:

```text
primitive_cube_add -> join_objects -> modifier_bevel
```

## Existing Tool Coverage

The dictionary catalogs 97 tools.

The current generic executor supports 28 of them:

```text
calculate_bounds
create_collision_proxy
create_lod_variant
dissolve_limited
export_gltf
join_objects
mark_seam
mark_sharp
material_assign_by_part
material_principled_shader
mesh_from_pydata
modifier_array
modifier_bevel
modifier_boolean
modifier_displace
modifier_mirror
modifier_weighted_normal
modifier_weld
object_duplicate_radial
primitive_cube_add
primitive_cylinder_add
procedural_bump_map
procedural_noise_texture
recalc_normals
render_workbench_preview
uv_pack_islands
uv_smart_project
validate_non_manifold
```

The UI must show this difference clearly:

```text
cataloged tool != executable tool
```

Use badges, not prose:

```text
exec
catalog
future-gn
reference
export
```

## Stage Counts

| Stage | Cataloged | Executable Today |
| --- | ---: | ---: |
| `base_form` | 21 | 3 |
| `assembly` | 15 | 5 |
| `shape_refinement` | 17 | 3 |
| `sculpt_detail` | 5 | 1 |
| `retopo_cleanup` | 14 | 3 |
| `uv_mapping` | 5 | 3 |
| `material_texture` | 9 | 4 |
| `validation_export` | 11 | 6 |

## Tool Catalog By Stage

Legend:

| Mark | Meaning |
| --- | --- |
| `exec` | `scripts/execute_blender_tool_plan_v0.py` supports the tool now. |
| `catalog` | Cataloged deterministic Blender action, but no executor branch yet. |
| `future-gn` | Geometry Nodes target, not current v0 execution. |
| `reference` | Manual or non-deterministic reference only. |
| `export` | Export action in catalog. |

### `base_form`

| Tool | Status | User params |
| --- | --- | --- |
| `primitive_cube_add` | exec | `size_m`, `location_m`, optional `material_role` |
| `primitive_plane_add` | catalog | `size`, `location` |
| `primitive_grid_add` | catalog | `x_subdivisions`, `y_subdivisions`, `size` |
| `primitive_circle_add` | catalog | `vertices`, `radius`, `fill_type` |
| `primitive_cylinder_add` | exec | `vertices`, `radius_m`, `depth_m`, `location_m`, optional `material_role` |
| `primitive_cone_add` | catalog | `vertices`, `radius1`, `radius2`, `depth` |
| `primitive_uv_sphere_add` | catalog | `segments`, `ring_count`, `radius` |
| `primitive_ico_sphere_add` | catalog | `subdivisions`, `radius` |
| `primitive_torus_add` | catalog | `major_segments`, `minor_segments`, `major_radius`, `minor_radius` |
| `mesh_from_pydata` | exec | `vertices`, `faces`, optional `group`, optional `material_role` |
| `bmesh_create` | catalog | `bmesh_operations` |
| `curve_bezier_add` | catalog | `points`, `handles` |
| `curve_polyline_add` | catalog | `points` |
| `text_to_mesh` | reference | `text`, `font` |
| `extrude_region` | catalog | `selected_region`, `translation` |
| `extrude_faces` | catalog | `selected_faces`, `translation` |
| `extrude_edges` | catalog | `selected_edges`, `translation` |
| `extrude_vertices` | catalog | `selected_vertices`, `translation` |
| `modifier_screw` | catalog | `angle`, `steps`, `axis` |
| `modifier_skin` | catalog | `edge_skeleton` |
| `gn_curve_to_mesh` | future-gn | `curve`, `profile_curve` |

### `assembly`

| Tool | Status | User params |
| --- | --- | --- |
| `bridge_edge_loops` | catalog | `edge_loop_a`, `edge_loop_b` |
| `split_separate` | catalog | `selected_faces` |
| `join_objects` | exec | `objects` |
| `transform_apply` | catalog | `object`, `location_rotation_scale_flags` |
| `modifier_array` | exec | `source_object`, `count`, `offset_m`, `name_prefix`, optional `output_group` |
| `object_duplicate_radial` | exec | `source_object`, `count`, `radius_m`, `name_prefix` |
| `modifier_mirror` | exec | `axis`, `objects` |
| `modifier_boolean` | exec | `operation`, `solver`, `cutters`, `targets`, `cleanup_cutters`, optional `socket_shadow_panels` |
| `modifier_nodes` | future-gn | `node_group` |
| `gn_join_geometry` | future-gn | `geometry_streams` |
| `gn_instance_on_points` | future-gn | `points`, `instance` |
| `gn_realize_instances` | future-gn | `instances` |
| `gn_transform_geometry` | future-gn | `geometry`, `transform` |
| `gn_mesh_boolean` | future-gn | `mesh_a`, `mesh_b`, `operation` |
| `gn_distribute_points` | future-gn | `surface`, `density` |

### `shape_refinement`

| Tool | Status | User params |
| --- | --- | --- |
| `curve_bevel_profile` | catalog | `curve_object`, `bevel_depth` |
| `inset_faces` | catalog | `selected_faces`, `thickness` |
| `bevel_mesh_edges` | catalog | `edge_selection`, `width`, `segments` |
| `loopcut_slide` | catalog | `edge_ring`, `cuts` |
| `knife_project` | catalog | `cutter_shape`, `target_mesh` |
| `bisect_mesh` | catalog | `plane` |
| `shade_flat` | catalog | `face_selection` |
| `shade_smooth` | catalog | `face_selection` |
| `mark_sharp` | exec | optional `selection_policy` |
| `modifier_bevel` | exec | `width_m`, `segments`, optional `affect` |
| `modifier_solidify` | catalog | `thickness` |
| `modifier_weighted_normal` | exec | `keep_sharp` |
| `modifier_wireframe` | catalog | `thickness` |
| `modifier_subsurf` | catalog | `levels` |
| `modifier_simple_deform` | catalog | `mode`, `angle_or_factor` |
| `modifier_lattice` | catalog | `lattice_object` |
| `gn_set_position` | future-gn | `geometry`, `offset` |

### `sculpt_detail`

| Tool | Status | User params |
| --- | --- | --- |
| `modifier_displace` | exec | `strength_m`, optional `texture` |
| `sculpt_draw` | reference | `brush`, `stroke_path` |
| `sculpt_crease` | reference | `crease_brush`, `stroke_path` |
| `sculpt_scrape` | reference | `scrape_brush`, `stroke_path` |
| `sculpt_smooth` | reference | `smooth_brush`, `stroke_path` |

### `retopo_cleanup`

| Tool | Status | User params |
| --- | --- | --- |
| `curve_to_mesh` | catalog | `curve_object` |
| `fill_holes` | catalog | `open_boundaries` |
| `grid_fill` | catalog | `open_grid_boundary` |
| `merge_vertices` | catalog | `vertex_selection` |
| `remove_doubles` | catalog | `merge_distance` |
| `dissolve_limited` | exec | `angle_limit_degrees` |
| `recalc_normals` | exec | `inside` |
| `flip_normals` | catalog | `face_selection` |
| `modifier_weld` | exec | `merge_distance_m` |
| `modifier_decimate` | catalog | `ratio`, `method` |
| `modifier_triangulate` | catalog | `quad_method`, `ngon_method` |
| `modifier_remesh` | catalog | `mode`, `voxel_size` |
| `modifier_shrinkwrap` | catalog | `target_object` |
| `retopo_shrinkwrap` | catalog | `low_mesh`, `high_mesh` |

### `uv_mapping`

| Tool | Status | User params |
| --- | --- | --- |
| `mark_seam` | exec | optional `selection_policy` |
| `uv_smart_project` | exec | `angle_limit_degrees`, `island_margin` |
| `uv_unwrap` | catalog | `method`, `margin` |
| `uv_cube_project` | catalog | `cube_size` |
| `uv_pack_islands` | exec | `margin` |

### `material_texture`

| Tool | Status | User params |
| --- | --- | --- |
| `gn_store_named_attribute` | future-gn | `geometry`, `attribute_name`, `value` |
| `gn_set_material` | future-gn | `geometry`, `material` |
| `texture_paint_brush` | reference | `brush`, `stroke_path`, `image` |
| `vertex_paint_color` | catalog | `color_attribute`, `selection`, `color` |
| `material_slot_add` | catalog | `object`, `material` |
| `material_assign_by_part` | exec | `material_map` |
| `material_principled_shader` | exec | `base_color`, `roughness`, `metallic` |
| `procedural_noise_texture` | exec | `scale`, `detail`, `roughness`, `seed` |
| `procedural_bump_map` | exec | `height_source`, `strength` |

### `validation_export`

| Tool | Status | User params |
| --- | --- | --- |
| `origin_set` | catalog | `origin_policy` |
| `calculate_bounds` | exec | optional `units` |
| `validate_non_manifold` | exec | `cleanup_merge_distance_m`, `cleanup_fill_hole_sides` |
| `create_collision_proxy` | exec | `proxy_policy` |
| `create_lod_variant` | exec | `decimate_ratio` |
| `render_workbench_preview` | exec | `resolution`, `preview_visibility`, `hide_validation_helpers` |
| `export_gltf` | exec | `format`, `apply_modifiers` |
| `export_fbx` | export | `objects`, `export_path` |
| `export_obj` | export | `objects`, `export_path` |
| `save_blend_file` | export | `scene`, `path` |
| `bake_geometry_nodes` | future-gn | `nodes_modifier` |

## Blank Plan Contract

The UI opens to this kind of empty draft. It may be invalid for Blender
execution until the user adds visible geometry and a `join_objects` step, but it
should be a valid blank editor state.

```json
{
  "schema": "gameguy_tool_plan_v0",
  "plan_id": "manual_blank_tool_plan_v0",
  "source_schema": "asset_mill_tool_plan_recipe_bundle_v0",
  "asset_id": "manual_asset_v0",
  "asset_family": "manual_asset",
  "style": "manual",
  "stage_order": [
    "base_form",
    "assembly",
    "shape_refinement",
    "sculpt_detail",
    "retopo_cleanup",
    "uv_mapping",
    "material_texture",
    "validation_export"
  ],
  "rules": {
    "blender_adapter_must_consume_plan": true
  },
  "steps": [],
  "summary": {
    "step_count": 0
  }
}
```

Every added step must follow this shape:

```json
{
  "order": 10,
  "step_id": "create_block_001",
  "tool_id": "primitive_cube_add",
  "stage": "base_form",
  "deterministic": true,
  "params": {
    "size_m": [1.0, 1.0, 1.0],
    "location_m": [0.0, 0.0, 0.5],
    "material_role": "body"
  }
}
```

The UI owns `order`, `step_id`, `stage`, `deterministic`, and `summary.step_count`.
The user edits `tool_id` and `params`.

## Required UI Shape

Use a compact working surface:

```text
toolbar
tool palette | step stack | inspector
preview/status/log
```

Recommended regions:

| Region | Size | Content |
| --- | ---: | --- |
| Toolbar | 40 px high | New, open, save, validate, ASCII, Blender, export. |
| Tool palette | 260-300 px wide | Search, stage filter, status filter, tool list. |
| Step stack | flexible center | Empty ordered plan by default. |
| Inspector | 340-420 px wide | Params for selected step. |
| Bottom strip | 120-180 px high | Validation, ASCII paths, execution report, diff. |

The default screen must have no seeded sample geometry. The center stack can say
`No steps` in small muted text. That is enough.

## UI Components

Use these component names so review can cut the right layer:

```text
ToolPlanWorkbenchShell
ToolPlanToolbar
ToolPalette
ToolPaletteRow
StepStack
StepStackRow
StepInspector
ParamEditor
ParamNumberInput
ParamVectorInput
ParamBooleanToggle
ParamEnumSelect
ParamJsonEditor
PlanStatusStrip
AsciiPreviewPane
ExecutionReportPane
ToolCatalogStore
ToolPlanDraftStore
ToolPlanCommandBridge
```

Avoid names like:

```text
Hero
Gallery
MagicBuilder
RecipeWizard
FeatureCard
ExperiencePanel
PromptSurface
```

## Visual Rules

This is a drafting/control UI.

Rules:

- no landing page
- no hero section
- no nested cards
- no card inside a panel
- no decorative gradients
- no large pill buttons
- no large section titles
- no persistent tutorial text in the app
- no seeded demo plan
- no auto-render on load
- no hidden geometry state outside JSON

Defaults:

```text
font_ui: 12px or 13px
font_code: 11px monospace
toolbar_height: 40px
control_height: 28px
icon_button: 28px square
panel_padding: 8px
row_height: 30px
border_radius: 4px
divider_width: 1px
shadow: none
letter_spacing: 0
```

Cut these generated defaults:

```text
variant="pill"
radius="full"
size="lg"
size="xl"
shadow="md"
shadow="lg"
elevation > 0
bordered child panel
asCard=true
showDescription=true
showEyebrow=true
fullWidth button
autoDemo=true
emptyIllustration=true
gradientBackground=true
sectionTitleSize="h2"
```

## Tool Palette Behavior

The palette reads `blender_tool_dictionary_v0.json`.

Filters:

```text
stage
status
category
deterministic
search text
```

Row content:

```text
tool_id | stage | status
```

No descriptions in the row. Show longer notes in a tooltip or inspector detail.

Tool add rules:

1. Adding a tool creates a new step with the next `order`.
2. The step `stage` comes from the dictionary.
3. `deterministic` comes from the dictionary, but executable steps must be true.
4. Params start from per-tool templates.
5. Non-executable tools may be added as planning steps only if the UI marks the
   plan as `not executable`.
6. Blender execution is disabled until every step is executable and the plan has
   a final object.

## Step Stack Behavior

The center stack is the plan. It should feel like a script list, not a recipe.

Each row:

```text
order | status | tool_id | step_id
```

Row actions:

```text
select
duplicate
move up
move down
disable or remove
```

Keep stage order valid. The executor rejects steps that move backward through
`stage_order`, so drag/drop must either block invalid moves or show a validation
error immediately.

## Inspector Behavior

The inspector edits `steps[n].params`.

Controls:

| Param kind | UI control |
| --- | --- |
| number | compact number input, optional slider only when range is known |
| integer | compact stepper |
| boolean | toggle |
| enum/string | compact select or short text input |
| vector3 | three aligned number inputs |
| list of object aliases | token list with known aliases |
| dict/object | compact JSON editor with validation |
| vertices/faces | JSON editor plus later table editor |

Every slider must have a visible numeric value. The number is the source of
truth.

## Executable Param Templates

Use these templates for current executable steps. They are based on the current
executor, not only the broad dictionary names.

| Tool | Required params | Notes |
| --- | --- | --- |
| `primitive_cube_add` | `size_m`, `location_m` | Optional `material_role`. Creates visible object unless role is `socket`. |
| `primitive_cylinder_add` | `vertices`, `radius_m`, `depth_m`, `location_m` | `vertices` must be at least 4. Optional `material_role`. |
| `mesh_from_pydata` | `vertices`, `faces` | Optional `group`, `material_role`. Edges are not used by current executor. |
| `object_duplicate_radial` | `source_object`, `count`, `radius_m`, `name_prefix` | Source must already exist. |
| `modifier_array` | `source_object`, `count`, `offset_m`, `name_prefix` | Optional `output_group`. |
| `modifier_mirror` | `axis`, `objects` | `objects` entries need `source_object`, `mirrored_name`, optional `group`. |
| `modifier_boolean` | `operation`, `solver`, `cutters`, `targets`, `cleanup_cutters` | Optional `socket_shadow_panels`. |
| `join_objects` | `objects` | Required before final-object modifiers or execution completion. |
| `modifier_bevel` | `width_m`, `segments` | Applies to final object. |
| `mark_sharp` | optional `selection_policy` | Marks all final-object boundary edges in current executor. |
| `modifier_weighted_normal` | `keep_sharp` | Adds weighted normal modifier to final object. |
| `modifier_displace` | `strength_m` | Uses internal stone noise texture if available. |
| `modifier_weld` | `merge_distance_m` | Applies to final object. |
| `dissolve_limited` | `angle_limit_degrees` | Edit-mode cleanup on final object. |
| `recalc_normals` | `inside` | Edit-mode normal recalculation on final object. |
| `mark_seam` | optional `selection_policy` | Current executor marks back edges. |
| `uv_smart_project` | `angle_limit_degrees`, `island_margin` | Final-object UV projection. |
| `uv_pack_islands` | `margin` | Final-object UV island packing. |
| `material_principled_shader` | `base_color`, `roughness`, `metallic` | Creates `gothic_stone`. |
| `procedural_noise_texture` | `scale`, `detail`, `roughness`, `seed` | Stored in report/context. |
| `procedural_bump_map` | `height_source`, `strength` | Stored in report/context. |
| `material_assign_by_part` | `material_map` | Applies material map to final object slots. |
| `calculate_bounds` | optional `units` | Requires final object. |
| `validate_non_manifold` | `cleanup_merge_distance_m`, `cleanup_fill_hole_sides` | Attempts cleanup and reports counts. |
| `create_collision_proxy` | `proxy_policy` | Requires calculated bounds. |
| `create_lod_variant` | `decimate_ratio` | Duplicates final object as LOD1. |
| `render_workbench_preview` | `resolution`, `preview_visibility`, `hide_validation_helpers` | Only writes render when `--render` is passed. |
| `export_gltf` | `format`, `apply_modifiers` | Only writes GLB when `--export` is passed. |

## Command Bridge

Validate without Blender:

```bash
python3 scripts/execute_blender_tool_plan_v0.py \
  --plan /path/to/tool_plan.json \
  --validate-only \
  --json-report /tmp/gameguy_blank_tool_plan_workbench_v0/validation_report.json
```

ASCII dry run:

```bash
python3 scripts/render_tool_plan_ascii_dryrun_v0.py \
  --plan /path/to/tool_plan.json \
  --out /tmp/gameguy_blank_tool_plan_workbench_v0/ascii \
  --width 96 \
  --height 72
```

Run Blender from Blender Python:

```bash
blender --background --python scripts/execute_blender_tool_plan_v0.py -- \
  --plan /path/to/tool_plan.json \
  --out /tmp/gameguy_blank_tool_plan_workbench_v0/blender \
  --render \
  --export
```

The UI should not write generated `.blend`, `.png`, `.glb`, or report output
inside the repo unless the user explicitly requests that.

## Preview Rules

ASCII preview currently supports:

```text
primitive_cube_add
primitive_cylinder_add
mesh_from_pydata as bounding box
```

It records or skips modifier/export steps in the dry-run report. The UI must
show that limitation. ASCII is a cheap planning surface, not proof that all
modifiers have rendered.

## Execution Readiness

Blender execution should be disabled until:

- all steps use executable tools
- every step has valid params
- stage order is valid
- at least one visible object is created
- a `join_objects` step creates the final object
- final-object modifiers come after `join_objects`
- `calculate_bounds` comes before `create_collision_proxy`
- render/export buttons are explicit user actions

The UI should show `draft`, `valid`, `ascii-ready`, `blender-ready`, or
`blocked` in the status strip.

## Undo And Diffs

Undo snapshots should store JSON diffs, not UI-only state.

```text
before_json
after_json
changed_path
changed_step_id
timestamp
```

Useful actions:

```text
undo
redo
duplicate step
remove step
reset params
show JSON diff
show raw plan JSON
```

## Acceptance Checklist

- Opens with an empty plan, not a recipe.
- No seeded sample objects.
- Tool palette reads the 97-tool dictionary.
- Executable status comes from the current executor support list.
- User can add, remove, duplicate, reorder, and edit steps.
- Inspector edits `params` for the selected step.
- Validate-only command works from the UI.
- ASCII command works when supported primitive steps exist.
- Blender run is blocked until the plan has a final object.
- Non-executable catalog tools can be planned but cannot be rendered silently.
- Output paths are visible and outside the repo by default.
- UI stays compact: no nested cards, no giant pills, no hero copy.

## Implementation Priority

1. Blank plan store and raw JSON view.
2. Tool palette loaded from the dictionary.
3. Step stack add/remove/reorder.
4. Param inspector for the 28 executable tools.
5. Validate-only bridge.
6. ASCII dry-run bridge.
7. Blender run bridge.
8. Non-executable catalog tool planning mode.
9. Later: add executor branches for more cataloged tools.

This is the UI that matches the project direction: a deterministic manual tool
plan workbench where the user picks Blender scripts and fills in the details.
