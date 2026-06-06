# Settings Page Design V0

## Purpose

The settings page controls the generation workbench around this pipeline:

```text
source recipe or blank tool plan
-> validation
-> cheap ASCII/dry-run preview
-> deterministic asset JSON or tool-plan JSON
-> optional Blender preview/export
```

It should not become a recipe editor by another name. The main editor owns
objects, steps, and source geometry. Settings only control environment,
preview/detail quality, validation strictness, output locations, and hardware
policy.

## Page Layout

Use a compact two-column settings page:

```text
left rail: setting groups
right pane: dense controls for selected group
footer: reset, validate settings, save, close
```

Do not use nested cards, oversized pills, or marketing-style panels. Use rows,
small labels, compact inputs, segmented controls, toggles, sliders, and file
pickers. Keep destructive choices behind explicit confirmation.

## Setting Groups

### 1. Workspace

Purpose: choose what the workbench is operating on.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `active_lane` | segmented control | `tool_plan` | `tool_plan`, `asset_pump`, `profile_revolve`, `ascii_preview`, `blender_preview` |
| `working_plan_path` | file picker | empty | Points at a `gameguy_tool_plan_v0` draft. |
| `source_bundle_path` | file picker | empty | Points at a source recipe bundle such as `profile_revolve_assets_v0.json`. |
| `selected_asset_id` | dropdown | first asset | Loaded from current manifest or bundle. |
| `autosave_drafts` | toggle | on | Saves JSON drafts after valid edits. |
| `show_raw_json` | toggle | off | Opens a raw JSON pane for inspection. |

Required behavior:

- Startup can be blank.
- No sample asset should be injected by default.
- The UI should show current schema and validation state near the path.

### 2. Source Pump

Purpose: configure source-to-geometry generation.

Controls:

| Setting | Control | Default | Applies To |
| --- | --- | --- | --- |
| `bundle_schema` | read-only label | from JSON | All source bundles |
| `output_root` | folder picker | `/tmp/gameguy_asset_workbench_v0` | All pump output |
| `clean_tmp_output` | toggle | on | Only allowed under `/tmp` |
| `write_repo_outputs` | disabled toggle | off | Must stay off in v0 |
| `validate_asset_json_after_pump` | toggle | on | Runs `validate_gameguy_asset_v0.py` |
| `adapter_validate_only_after_pump` | toggle | on | Runs Blender adapter in validate-only mode |

Mapped commands:

```bash
python3 scripts/asset_pump_v0.py --bundle <bundle> --clean --out <tmp_out>
python3 scripts/validate_gameguy_asset_v0.py --manifest <tmp_out>/manifest.json
python3 scripts/export_blender_asset_preview_v0.py --manifest <tmp_out>/manifest.json --validate-only
```

### 3. Profile Revolve

Purpose: tune the side-profile spin operation without making the object a stack
of rectangular blocks.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `axis` | segmented control | `z` | `x`, `y`, `z` |
| `segments` | stepper/slider | `24` | Minimum `8`; low hardware can use `12` or `16`. |
| `material_role` | dropdown | `stone_shaft` | Assigned to the generated body part. |
| `side_profile_points` | editable table | recipe values | Rows contain `point_id`, `at`, `radius_m`, `material_role`. |
| `add_profile_point` | button | n/a | Inserts a point after current row. |
| `delete_profile_point` | button | n/a | Refuse if fewer than two points would remain. |
| `normalize_profile_order` | button | n/a | Sorts by `at`; warn if it changes row order. |
| `show_profile_graph` | toggle | on | Shows 2D height/radius curve. |
| `show_ring_preview` | toggle | on | Shows ring count and vertex count before Blender. |

Validation:

- `segments >= 8`
- at least two side-profile points
- `at` values strictly increase
- `radius_m > 0`
- unique `point_id`

Current source anchor:

```text
data/architecture/asset_mill/recipes/profile_revolve_assets_v0.json
```

Current proof asset:

```text
gothic_calibration_revolved_shaft_v0
```

### 4. Tool Plan

Purpose: control the blank Blender tool-plan workbench.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `tool_filter` | segmented/filter chips | `exec` | `exec`, `catalog`, `future-gn`, `reference`, `export` |
| `stage_lock` | toggle | on | Keeps stage-canonical ordering. |
| `auto_renumber_steps` | toggle | on | Writes `10, 20, 30...` order values. |
| `show_dependency_warnings` | toggle | on | Shows missing final object, bounds, export requirements. |
| `allow_raw_param_edit` | toggle | off | Expert mode only. |
| `validate_on_change` | toggle | on | Runs UI template validation after edits. |

Mapped commands:

```bash
python3 scripts/create_blank_tool_plan_v0.py --out <plan>
python3 scripts/add_tool_plan_step_v0.py --plan <plan> --tool-id <tool_id>
python3 scripts/validate_tool_plan_against_ui_templates_v0.py --plan <plan>
python3 scripts/render_tool_plan_ascii_dryrun_v0.py --plan <plan> --out <tmp_out>
python3 scripts/execute_blender_tool_plan_v0.py --plan <plan> --validate-only
```

Source of controls:

```text
data/architecture/asset_mill/blender_tools/blender_tool_ui_templates_v0.json
```

The settings page should not invent tool params. Add missing controls to the
template file first, validate the template, then expose them.

### 5. ASCII Preview

Purpose: provide low-compute inspection before Blender.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `ascii_backend` | dropdown | `tool_plan_dryrun` | `tool_plan_dryrun`, `external_image_to_ascii` |
| `width` | number/stepper | `80` | Used by `render_tool_plan_ascii_dryrun_v0.py`. |
| `height` | number/stepper | `50` | Used by `render_tool_plan_ascii_dryrun_v0.py`. |
| `projection` | segmented control | `front_side_top` | Front, side, top, or all. |
| `custom_palette` | text input | empty | Use `--custom-palette=...` when forwarding to external ASCII tools. |
| `edge_mode` | dropdown | `none` | External image-to-ASCII only. |
| `save_txt` | toggle | on | Human-readable ASCII. |
| `save_png` | toggle | off | Higher cost; optional. |

Hardware note:

- Low-compute mode should prefer text output and skip PNG conversion.
- `* DECALS`: lower compute hardware does not get decals. Mark decal options
  with a large warning in any future texture/detail page.

### 6. Blender Preview

Purpose: control optional Blender adapter runs after JSON validation passes.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `blender_path` | file picker | `/Applications/Blender.app/Contents/MacOS/Blender` | Must be validated before run. |
| `preview_output_root` | folder picker | `/tmp/gameguy_blender_preview_v0` | Must not write into repo. |
| `render_png` | toggle | off | Writes Workbench PNG. |
| `save_blend` | toggle | on | Current adapter saves `.blend`. |
| `hide_connectors` | toggle | on | Keeps first visual clean. |
| `render_resolution` | dropdown | `1600x1100` | Future adapter knob; currently hardcoded in adapter. |
| `material_preview_mode` | dropdown | `material_role` | Future adapter knob. |

Mapped command:

```bash
/Applications/Blender.app/Contents/MacOS/Blender --background \
  --python scripts/export_blender_asset_preview_v0.py -- \
  --manifest <manifest> \
  --out <tmp_out> \
  --render \
  --hide-connectors
```

### 7. Validation

Purpose: centralize checks and make failure states obvious.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `json_parse_check` | toggle | on | Parse touched JSON files. |
| `template_contract_check` | toggle | on | Runs `validate_blender_tool_ui_templates_v0.py`. |
| `tool_plan_ui_check` | toggle | on | Runs `validate_tool_plan_against_ui_templates_v0.py`. |
| `asset_schema_check` | toggle | on | Runs `validate_gameguy_asset_v0.py`. |
| `adapter_validate_only` | toggle | on | Runs adapter without Blender output. |
| `full_pipeline_gate` | toggle | off | Expensive and may fail if repo output folders contain media. |

The error panel should show:

```text
failing command
stderr
affected file
suggested next fix
```

Do not hide failures behind green UI state. If validation fails, preview/export
buttons should be disabled except for raw draft save.

### 8. Output Safety

Purpose: prevent generated media and mesh exports from polluting the repo.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `tmp_only_outputs` | locked toggle | on | All generated outputs go under `/tmp`. |
| `clean_before_run` | toggle | on | Only for `/tmp` paths. |
| `repo_output_guard` | toggle | on | Warns if `.blend`, `.glb`, `.png`, etc. exist in repo output folders. |
| `open_output_folder` | button | n/a | Opens tmp folder after run. |
| `copy_output_path` | button | n/a | Copies current generated file path. |

The settings page must make it clear:

```text
source files live in repo
generated outputs live under /tmp
```

### 9. Hardware Profile

Purpose: make the same workflow usable on lower compute hardware.

Profiles:

| Profile | Geometry | ASCII | Blender | Texture/Decals |
| --- | --- | --- | --- | --- |
| `low` | fewer segments, no helpers | text only | validate-only by default | no decals |
| `mid` | normal segments | text plus optional PNG | Workbench render allowed | no heavy decals |
| `high` | full segments | all previews | render/export allowed | decals allowed only if explicitly enabled |

Default for this repo should be `mid`, but a visible low-compute toggle should
exist near preview buttons.

### 10. Review And Correction Capture

Purpose: turn visual feedback into source changes.

Controls:

| Setting | Control | Default | Notes |
| --- | --- | --- | --- |
| `capture_rejected_preview` | toggle | on | Stores notes, not generated media. |
| `correction_note_path` | file path | docs scratch note | Human-readable correction queue. |
| `source_change_target` | dropdown | current bundle | Tells the next edit where to land. |
| `mark_blender_decision_as_source_gap` | button | n/a | Records that Blender had to invent something. |

The key rule:

```text
If Blender had to decide the shape, the source recipe is missing a setting.
```

## Minimal Settings JSON Shape

The UI can persist settings as a small JSON object:

```json
{
  "schema": "gameguy_workbench_settings_v0",
  "active_lane": "profile_revolve",
  "hardware_profile": "mid",
  "source_bundle_path": "data/architecture/asset_mill/recipes/profile_revolve_assets_v0.json",
  "working_plan_path": "",
  "output_root": "/tmp/gameguy_asset_workbench_v0",
  "ascii": {
    "backend": "tool_plan_dryrun",
    "width": 80,
    "height": 50,
    "save_txt": true,
    "save_png": false
  },
  "blender": {
    "path": "/Applications/Blender.app/Contents/MacOS/Blender",
    "render_png": false,
    "hide_connectors": true,
    "output_root": "/tmp/gameguy_blender_preview_v0"
  },
  "validation": {
    "validate_on_change": true,
    "adapter_validate_only": true,
    "full_pipeline_gate": false
  }
}
```

## First Settings Page Build Target

For the first UI implementation, build only these sections:

```text
Workspace
Profile Revolve
ASCII Preview
Blender Preview
Validation
Output Safety
```

Skip advanced texture, decal, and full pipeline controls until the basic
profile-revolve shaft can be tuned, validated, previewed, and rendered from the
same screen.
