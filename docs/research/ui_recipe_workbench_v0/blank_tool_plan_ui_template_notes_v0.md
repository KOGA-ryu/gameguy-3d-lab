# Blank Tool Plan UI Template Notes V0

## Purpose

This note records the machine-readable contract for the blank Blender tool-plan
workbench.

The UI should no longer infer parameter controls from prose or from the broad
tool dictionary alone. It should read the UI templates, create an empty
`gameguy_tool_plan_v0`, then let the user add steps and edit params.

```text
blender_tool_dictionary_v0.json
-> blender_tool_ui_templates_v0.json
-> blank gameguy_tool_plan_v0
-> validate-only
-> ASCII dry run
-> optional Blender execution
```

## Files

| Path | Role |
| --- | --- |
| `data/architecture/asset_mill/blender_tools/blender_tool_ui_templates_v0.json` | Defines compact UI controls for every currently executable tool. |
| `scripts/validate_blender_tool_ui_templates_v0.py` | Verifies templates match the tool dictionary and executor support list. |
| `scripts/create_blank_tool_plan_v0.py` | Emits a valid empty `gameguy_tool_plan_v0`. |
| `scripts/add_tool_plan_step_v0.py` | Appends a template-backed step and rewrites stage-canonical order. |
| `scripts/validate_tool_plan_against_ui_templates_v0.py` | Validates a hand-edited plan against UI control types, ranges, enums, and dependencies. |
| `scripts/execute_blender_tool_plan_v0.py` | Existing validate-only and Blender execution adapter. |
| `scripts/render_tool_plan_ascii_dryrun_v0.py` | Existing cheap ASCII dry-run adapter. |

## UI Template Contract

The template file covers the 28 tools currently supported by
`scripts/execute_blender_tool_plan_v0.py`.

Each template defines:

```text
tool_id
stage
step_id_prefix
status
required_params
step_template
controls
dependency flags
```

The UI should use `step_template.params` as the initial params for a new step.
The inspector should render `controls` for the selected step.

The UI should own:

```text
order
step_id
stage
deterministic
summary.step_count
```

The user edits:

```text
tool_id
params
```

## Important Boundary

The broad dictionary and the executor do not use identical param names.

Example:

```text
dictionary: primitive_cube_add inputs = size, location
executor:   primitive_cube_add params = size_m, location_m
```

The UI must use `blender_tool_ui_templates_v0.json` for actual controls. The
dictionary remains useful for catalog metadata, stage, category, Blender API,
and future tool discovery.

## Commands

Validate the UI template layer:

```bash
python3 scripts/validate_blender_tool_ui_templates_v0.py \
  --json-report /tmp/gameguy_blender_tool_ui_templates_validation_v0.json
```

Create a blank plan:

```bash
python3 scripts/create_blank_tool_plan_v0.py \
  --out /tmp/gameguy_blank_tool_plan_workbench_v0/blank_tool_plan_v0.json
```

Add a tool step from the template catalog:

```bash
python3 scripts/add_tool_plan_step_v0.py \
  --plan /tmp/gameguy_blank_tool_plan_workbench_v0/blank_tool_plan_v0.json \
  --tool-id primitive_cube_add
```

Add a tool step with param overrides:

```bash
python3 scripts/add_tool_plan_step_v0.py \
  --plan /tmp/gameguy_blank_tool_plan_workbench_v0/blank_tool_plan_v0.json \
  --tool-id modifier_bevel \
  --set width_m=0.04 \
  --set segments=2
```

Validate a hand-edited plan against UI controls:

```bash
python3 scripts/validate_tool_plan_against_ui_templates_v0.py \
  --plan /tmp/gameguy_blank_tool_plan_workbench_v0/blank_tool_plan_v0.json \
  --json-report /tmp/gameguy_blank_tool_plan_workbench_v0/ui_validation_report.json
```

Validate that blank plan without Blender:

```bash
python3 scripts/execute_blender_tool_plan_v0.py \
  --plan /tmp/gameguy_blank_tool_plan_workbench_v0/blank_tool_plan_v0.json \
  --validate-only \
  --json-report /tmp/gameguy_blank_tool_plan_workbench_v0/validation_report.json
```

## UI Usage

The first screen should be empty:

```text
Tool palette | No steps | Inspector disabled
```

The UI can enable commands progressively:

| State | Condition | Enabled commands |
| --- | --- | --- |
| `draft` | no steps | save, raw JSON, validate |
| `valid-empty` | blank plan validates | save, add step |
| `ascii-ready` | primitive geometry exists | ASCII dry run |
| `blender-ready` | all steps executable and `join_objects` exists | Blender run |
| `blocked` | invalid params, invalid stage order, or missing dependency | save draft, show errors |

## Review Rule

If a UI control is not present in `blender_tool_ui_templates_v0.json`, it is not
part of the v0 UI contract. Add the control to the template file first, validate
it, then build the UI.
