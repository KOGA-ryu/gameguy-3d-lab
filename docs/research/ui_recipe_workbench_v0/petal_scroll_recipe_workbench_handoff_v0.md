# Petal Scroll Recipe Workbench Handoff V0

## Purpose

Build a compact UI surface for the recipe pipeline that produced the current
petal-scroll column ornament. The UI must let a human tune script layers with
buttons, toggles, sliders, steppers, and numeric fields while the source recipe
remains the truth.

This is the center of the handoff:

```text
UI state
-> recipe JSON
-> ascii_blender_dryrun CLI
-> ASCII previews + validation report
-> optional Blender render/export
```

The UI must not contain geometry decisions that are absent from the recipe. If a
button or slider changes geometry, that value must be written back into recipe
JSON.

## First Supported Asset

Support only this recipe in v0:

```text
ascii_blender_dryrun_v0/examples/petal_scroll_column_ornament_recipe_v0.json
```

The first editable operation is:

```json
{
  "op": "AddPetalScroll",
  "name": "proof.petal_scroll_column_ornament_v0"
}
```

Do not start with generic asset families, multiple object types, or a blank
canvas. The first win is one polished operator surface that can later become the
pattern for posts, rails, trim, windows, doors, ceilings, and column ornaments.

## Data Contract

The UI should keep one in-memory recipe object and produce valid JSON that
matches:

```text
ascii_blender_dryrun_v0/schemas/recipe_v0.schema.json
```

Required file outputs:

```text
workbench_session/
  active_recipe.json
  compiled_recipe.json
  validation_report.json
  previews/
    front.txt
    side.txt
    top.txt
  renders/
    preview.png
```

The UI can choose its own session folder, but it must expose the full path to the
current recipe and proof outputs.

## Recipe Draft Model

The UI should not scatter state across controls. Keep a single draft object and
derive all controls from it.

```text
RecipeDraft
  source_path
  session_path
  recipe_json
  selected_op_index
  selected_layer_id
  dirty
  last_validated_hash
  validation_report
  preview_outputs
  undo_stack
  redo_stack
```

Every control row should be described by metadata:

```text
control_id
layer_id
json_pointer
label
control_kind
min
max
step
unit
default_value
warning_rule
```

Use JSON pointers such as:

```text
/ops/0/petal/max_width
/ops/0/scroll/turns
/ops/0/scroll/solid_fill/enabled
/ops/0/vein/raise_depth
```

The UI should write to those paths in the draft recipe, then rerun validation.
Do not maintain a second hidden geometry model.

## Command Bridge

ASCII dry run:

```bash
PYTHONPATH=ascii_blender_dryrun_v0 .venv/bin/python -m ascii_blender_dryrun.cli \
  --recipe /path/to/active_recipe.json \
  --out /tmp/gameguy_recipe_workbench_v0 \
  --width 96 \
  --height 72
```

Read these after the command:

```text
/tmp/gameguy_recipe_workbench_v0/validation_report.json
/tmp/gameguy_recipe_workbench_v0/doric_front_preview.txt
/tmp/gameguy_recipe_workbench_v0/doric_side_preview.txt
/tmp/gameguy_recipe_workbench_v0/doric_top_preview.txt
/tmp/gameguy_recipe_workbench_v0/build_doric_column_v0.py
```

The `doric_*` filenames are legacy names. The UI should relabel them as
`front`, `side`, and `top`; do not block the UI on renaming the CLI outputs.

Blender render should be manual, not automatic on every slider move. Use the
generated Python script only after validation passes.

## Layout

Use a working-tool layout, not a landing page.

```text
┌────────────────────────────────────────────────────────────────────┐
│ toolbar                                                            │
├───────────────┬──────────────────────────────────────┬─────────────┤
│ layer stack   │ preview                              │ inspector   │
│               │ ASCII front / side / top / render    │ controls    │
├───────────────┴──────────────────────────────────────┴─────────────┤
│ validation + command log + recipe diff                             │
└────────────────────────────────────────────────────────────────────┘
```

Recommended dimensions:

| Region | Width/Height | Notes |
| --- | ---: | --- |
| Toolbar | 40 px high | File, validate, ASCII, render, save. |
| Layer stack | 220-260 px wide | Plain list, no cards. |
| Preview | flexible center | ASCII first, render second. |
| Inspector | 300-360 px wide | Dense parameter controls. |
| Bottom log | 120-180 px high | Collapsible, not a modal. |

Use split panes or simple dividers. Do not put panels inside cards.

## Visual Style Rules

This UI should feel like a drafting/control surface.

Allowed:

- restrained neutral background
- one-pixel dividers
- compact toolbar
- small icon buttons with tooltips
- segmented preview tabs
- sliders paired with exact numeric inputs
- toggles for optional layers
- steppers for counts and sample values
- monospaced preview text
- monospaced JSON/diff/log text

Avoid:

- hero sections
- marketing copy
- decorative gradients
- bokeh/orb backgrounds
- nested cards
- cards inside panels
- oversized pill buttons
- large rounded controls
- big section titles
- empty-state illustrations
- floating shadows around every region
- explanatory paragraphs inside the app

## Default UI Slop To Name And Cut

When reviewing generated UI, search for these concepts and remove them unless
there is a clear working-tool reason:

```text
hero
landing
feature_card
info_card
nested_card
glass_panel
gradient_background
gradient_orb
bokeh
marketing_copy
empty_state_illustration
oversized_pill
pill_button_large
rounded_full
shadow_lg
floating_panel
card_grid
section_eyebrow
giant_title
subtitle_blurb
how_it_works_text
demo_content_seed
sample_gallery
decorative_badge
```

Preferred replacements:

| Slop default | Replace with |
| --- | --- |
| `feature_card` | plain row or table line |
| `nested_card` | divider-separated pane |
| `oversized_pill` | 28-32 px icon or text button |
| `giant_title` | 12-14 px pane label or no label |
| `subtitle_blurb` | tooltip or docs, not persistent UI |
| `sample_gallery` | saved recipe list |
| `empty_state_illustration` | blank preview with grid/placeholder text |
| `gradient_background` | flat neutral surface |

## Sizing Defaults

Use these as starting tokens:

```text
font_ui: 12px or 13px
font_preview: 11px monospace
toolbar_height: 40px
control_height: 28px
icon_button: 28px square
primary_button_height: 32px
panel_padding: 8px
control_gap: 6px
section_gap: 10px
border_radius: 4px
card_radius: 0px unless representing a repeated saved recipe item
divider_width: 1px
shadow: none
letter_spacing: 0
input_label_width: 96px
numeric_input_width: 72px
slider_min_width: 120px
row_height: 30px
pane_title_height: 24px
bottom_strip_collapsed_height: 28px
```

Do not scale font sizes with viewport width.

## Component Names To Use

Name the UI pieces plainly so review can attack the right layer:

```text
RecipeWorkbenchShell
RecipeToolbar
LayerStack
LayerStackRow
PreviewPane
PreviewTabs
AsciiPreview
RenderPreview
RecipeInspector
CompactSliderRow
UnitNumberInput
CompactStepper
CompactToggle
SegmentedControl
ValidationStrip
CommandLog
RecipeDiffPanel
JsonDraftStore
DryRunCommandBridge
BlenderRenderBridge
OutputPathBar
```

Avoid vague names like `Hero`, `FeaturePanel`, `MagicCard`, `GalleryCard`,
`PromptBox`, or `ExperienceSurface`. This is an operator workbench.

## Default UI Props To Cut

If the UI framework or generated code introduces these props, remove or override
them unless a specific control requires them.

| Prop/default name | Reject | Required replacement |
| --- | --- | --- |
| `variant="pill"` | Large rounded controls. | `variant="compact"` or plain button. |
| `radius="full"` | Pill shapes that consume space. | `radius="sm"` or `4px`. |
| `size="lg"` / `size="xl"` | Oversized toolbar and inputs. | `size="sm"` / 28-32 px controls. |
| `shadow="md"` / `shadow="lg"` | Floating card look. | `shadow="none"`. |
| `elevation > 0` | Stacked panel look. | flat pane with one-pixel divider. |
| `bordered=true` on child panels | Borders inside borders. | parent pane divider only. |
| `asCard=true` | Card layout for tool regions. | split pane region. |
| `showDescription=true` | Persistent helper prose. | tooltip or docs link. |
| `showEyebrow=true` | Marketing-style labels. | no eyebrow. |
| `fullWidth=true` on buttons | Giant command rows. | content-width buttons. |
| `minHeight="hero"` | Landing-page spacing. | fixed toolbar/workbench rows. |
| `autoDemo=true` | Seeded sample content. | load explicit recipe only. |
| `emptyIllustration=true` | Decorative blank states. | plain text: `No preview yet`. |
| `cardPadding >= 16px` | Bloated panes. | 8 px pane padding. |
| `sectionTitleSize="h2"` | Titles polluting the UI. | 12-14 px pane label or none. |
| `gradientBackground=true` | Decorative surface. | flat neutral background. |

## Layer Stack

The left pane is a plain ordered stack. It should show layer names and enabled
state, not descriptions.

Initial stack:

```text
Petal Surface
Scroll Roll
Thickness Ramp
Solid Fill
Center Vein
Finish
```

Each row:

```text
[visibility toggle] [layer name] [status dot]
```

Optional later rows:

```text
Edge Lip
Secondary Veins
Base Tuck
Material/Wear
Export
```

Selecting a row changes the inspector controls. It must not open a modal.

## Inspector Controls

Every slider must have an exact numeric input beside it. The numeric value is
the source of truth, not the slider thumb.

Use the current recipe as the reset state for v0:

| JSON pointer | Default | Control |
| --- | ---: | --- |
| `/ops/0/petal/length` | `1.35` | slider + number |
| `/ops/0/petal/base_width` | `0.16` | slider + number |
| `/ops/0/petal/max_width` | `0.36` | slider + number |
| `/ops/0/petal/tip_width` | `0.08` | slider + number |
| `/ops/0/petal/min_thickness` | `0.016` | slider + number |
| `/ops/0/petal/max_thickness` | `0.13` | slider + number |
| `/ops/0/petal/tip_thickness` | `0.12` | slider + number |
| `/ops/0/petal/width_peak_t` | `0.38` | slider + number |
| `/ops/0/petal/thickness_peak_t` | `0.92` | slider + number |
| `/ops/0/petal/bend_start_t` | `0.42` | slider + number |
| `/ops/0/petal/samples_length` | `34` | stepper |
| `/ops/0/petal/samples_width` | `7` | stepper |
| `/ops/0/scroll/type` | `volute` | locked segmented value |
| `/ops/0/scroll/turns` | `1.55` | slider + number |
| `/ops/0/scroll/radius_start` | `0.95` | slider + number |
| `/ops/0/scroll/radius_end` | `0.06` | slider + number |
| `/ops/0/scroll/vertical_lift` | `0.18` | slider + number |
| `/ops/0/scroll/start_angle_deg` | `-95` | dial + number |
| `/ops/0/scroll/direction` | `ccw` | segmented control |
| `/ops/0/scroll/relief_depth` | `0.08` | slider + number |
| `/ops/0/scroll/curl_depth` | `0.22` | slider + number |
| `/ops/0/scroll/twist_deg` | `36` | slider + number |
| `/ops/0/scroll/samples` | `54` | stepper |
| `/ops/0/scroll/samples_width` | `7` | stepper |
| `/ops/0/scroll/edge_bevel` | `0.006` | slider + number |
| `/ops/0/scroll/edge_bevel_segments` | `1` | stepper |
| `/ops/0/scroll/solid_fill/enabled` | `true` | toggle |
| `/ops/0/scroll/solid_fill/mode` | `center_fan` | locked segmented value |
| `/ops/0/scroll/solid_fill/front_depth` | `0.045` | slider + number |
| `/ops/0/scroll/solid_fill/back_depth` | `0.035` | slider + number |
| `/ops/0/scroll/solid_fill/edge_bevel` | `0.004` | slider + number |
| `/ops/0/vein/enabled` | `true` | toggle |
| `/ops/0/vein/bevel_depth` | `0.012` | slider + number |
| `/ops/0/vein/raise_depth` | `0.025` | slider + number |
| `/ops/0/vein/start_t` | `0.1` | range slider + number |
| `/ops/0/vein/end_t` | `0.9` | range slider + number |
| `/ops/0/vein/material` | `stone` | compact menu |
| `/ops/0/material` | `limestone` | compact menu |

### Petal Surface

Maps to `op.petal`.

| Field | Control | Suggested Range | Notes |
| --- | --- | ---: | --- |
| `length` | slider + number | 0.2-3.0 | Overall petal path scale. |
| `base_width` | slider + number | 0.01-1.0 | Width at start. |
| `max_width` | slider + number | 0.01-1.5 | Widest point. |
| `tip_width` | slider + number | 0.005-1.0 | Width at inner roll/tip. |
| `width_peak_t` | slider + number | 0-1 | Where max width occurs. |
| `min_thickness` | slider + number | 0.001-0.2 | Thin outside sheet edge. |
| `max_thickness` | slider + number | 0.001-0.4 | Thickest roll mass. |
| `tip_thickness` | slider + number | 0.001-0.4 | Inner curl thickness. |
| `thickness_peak_t` | slider + number | 0-1 | Push late for rolled-paper effect. |
| `bend_start_t` | slider + number | 0-1 | Where the petal starts bending into the scroll. |
| `samples_length` | stepper | 4-128 | Lengthwise surface resolution. |
| `samples_width` | stepper | 3-32 | Mesh cross-section resolution. |

### Scroll Roll

Maps to `op.scroll`.

| Field | Control | Suggested Range | Notes |
| --- | --- | ---: | --- |
| `type` | locked segmented value | `volute` | Do not expose other types in v0. |
| `turns` | slider + number | 0.25-3.0 | More turns means tighter roll. |
| `radius_start` | slider + number | 0.01-3.0 | Outer radius. |
| `radius_end` | slider + number | 0.005-1.0 | Inner curl radius. |
| `vertical_lift` | slider + number | -1.0-1.0 | Keep low for rolled-paper read. |
| `start_angle_deg` | dial/number | -180-180 | Rotates the whole scroll. |
| `direction` | segmented control | `ccw` / `cw` | No dropdown needed. |
| `relief_depth` | slider + number | 0-0.5 | Pushes scroll outward. |
| `curl_depth` | slider + number | 0-0.8 | Side curl/depth. |
| `twist_deg` | slider + number | -180-180 | Twist through the roll. |
| `samples` | stepper | 8-128 | Path smoothness. |
| `samples_width` | stepper | 3-32 | Widthwise scroll resolution. |
| `edge_bevel` | slider + number | 0-0.05 | Edge softening. |
| `edge_bevel_segments` | stepper | 1-8 | Keep `1` by default for low compute. |

### Thickness Ramp

This is not a separate JSON object yet. It is a UI grouping over:

```text
min_thickness
max_thickness
tip_thickness
thickness_peak_t
```

Expose quick presets:

| Preset | Effect |
| --- | --- |
| `sheet` | thin all the way through |
| `rolled` | thin outside, thick inner curl |
| `carved_mass` | thick body, softer ramp |

These presets must only write the four petal fields above.

### Solid Fill

Maps to `op.scroll.solid_fill`.

| Field | Control | Suggested Range | Notes |
| --- | --- | ---: | --- |
| `enabled` | toggle | on/off | No-daylight relief. |
| `mode` | segmented | `center_fan` | Only one mode in v0. |
| `front_depth` | slider + number | 0-0.3 | Front surface of fill. |
| `back_depth` | slider + number | 0-0.3 | Back surface of fill. |
| `edge_bevel` | slider + number | 0-0.05 | Softens fill edge. |

If `solid_fill.enabled` is off, preview status should show `open relief`.
If it is on, preview status should show `filled relief`.

### Center Vein

Maps to `op.vein`.

| Field | Control | Suggested Range | Notes |
| --- | --- | ---: | --- |
| `enabled` | toggle | on/off | Raised center ridge. |
| `bevel_depth` | slider + number | 0.001-0.08 | Ridge thickness. |
| `raise_depth` | slider + number | 0-0.1 | Lift above surface. |
| `start_t` | range slider + number | 0-1 | Start along scroll. |
| `end_t` | range slider + number | 0-1 | End along scroll. |
| `material` | segmented/menu | `limestone` / `stone` | Keep compact. |

### Finish

Initial controls:

| Field | Control | Notes |
| --- | --- | --- |
| ASCII width | stepper | Default 96. |
| ASCII height | stepper | Default 72. |
| Validate | icon/text button | Runs validation only. |
| ASCII preview | icon/text button | Runs dry-run CLI. |
| Blender render | icon/text button | Manual; disabled if validation fails. |
| Save recipe | icon/text button | Writes JSON. |
| Material | compact menu | Writes `/ops/0/material`. |

## Control Timing

Use this event model so the UI feels fast without hiding state:

| Interaction | Draft update | Validation | ASCII preview | Undo snapshot |
| --- | --- | --- | --- | --- |
| Slider drag | live | debounced | debounced | on drag end |
| Numeric input enter/blur | immediate | immediate | debounced | immediate |
| Toggle | immediate | immediate | debounced | immediate |
| Stepper click | immediate | immediate | debounced | immediate |
| Preset button | immediate multi-path write | immediate | debounced | one grouped snapshot |
| Save | writes session/source file | required first | no rerun required | no new snapshot |

The active preview status should show `stale` while a command is pending and
`invalid` if validation fails.

## Preview Pane

Preview tabs:

```text
Front | Side | Top | Render | JSON
```

The default tab is `Front`. ASCII should update cheaply after slider edits with a
short debounce. Blender render must be explicit.

Preview should not be wrapped in a decorative card. Use the preview pane itself.

For ASCII:

- use a monospace font
- preserve whitespace
- let the text scroll
- do not anti-alias into an image unless the user explicitly requests image view

For render:

- show the latest PNG if present
- show exact file path
- do not auto-render while dragging

## Validation And Command Log

The bottom pane should show:

```text
status: valid / invalid / stale
finding_count
first 5 validation findings
last command
last command exit code
last output paths
```

Do not show a long tutorial. Validation should be terse and operational.

Minimum warnings to surface before render:

| Warning | Trigger |
| --- | --- |
| `open_relief_daylight` | `solid_fill.enabled` is false. |
| `inner_radius_too_large` | `radius_end >= radius_start`. |
| `early_thickness_peak` | `thickness_peak_t < width_peak_t`. |
| `high_ascii_cost` | ASCII width over `160` or height over `120`. |
| `high_mesh_cost` | `scroll.samples * petal.samples_width > 1500`. |
| `hidden_numeric_value` | any slider lacks a visible number field. |
| `render_without_validation` | render clicked while status is stale/invalid. |

## Undo And Recipe Diff

Every committed UI change should create an undo snapshot of the recipe object.

Minimum undo model:

```text
before_json
after_json
changed_path
timestamp
```

Expose:

```text
Undo
Redo
Reset Layer
Show Diff
```

The diff view can live in the bottom pane. It should use compact monospace text.

## Implementation Rules

1. The UI writes recipe JSON.
2. The UI does not generate Blender geometry directly.
3. The UI does not silently mutate generated Blender scripts.
4. The UI does not store hidden geometry state outside the recipe.
5. The UI should not autosave over the source example file by default.
6. The UI should write session copies first, then explicit save back to source.
7. The UI should block Blender render when validation has errors.
8. The UI should keep render artifacts out of git unless explicitly forced.
9. Presets are only named batches of JSON writes.
10. Any new geometry layer must first exist in the schema or be blocked behind an
    explicit `future` flag in the UI.
11. The UI must show the active recipe path, output path, and validation status
    at all times.

## Suggested Implementation Phases

### Phase 1: Static Workbench Shell

- Load the petal-scroll recipe.
- Render the four panes with no decorative cards.
- Show raw JSON and static ASCII text.
- No Blender yet.

Done when the UI opens directly into the workbench with no landing screen.

### Phase 2: Recipe Inspector

- Bind controls to `op.petal`, `op.scroll`, and `op.vein`.
- Save session recipe JSON.
- Add undo/redo snapshots.

Done when moving `turns` changes JSON immediately and can be undone.

### Phase 3: ASCII Dry Run

- Run the CLI command.
- Display front/side/top previews.
- Display validation report.
- Disable render when invalid.

Done when the user can tune without opening Blender.

### Phase 4: Blender Render Button

- Run generated Blender script after validation passes.
- Save preview PNG and exports to a session output folder.
- Show render path and thumbnail.

Done when the UI can produce the same proof render as the current command-line
workflow.

### Phase 5: Detail Layers

Add UI rows for:

```text
Edge Lip
Secondary Veins
Base Tuck
```

Do this only after the core scroll workbench feels fast and non-sloppy.

## Acceptance Checklist

- Opens on the workbench, not a splash page.
- No nested cards.
- No hero/marketing layout.
- No giant pill controls.
- No unexplained geometry state outside JSON.
- One selected layer controls one parameter group.
- Every slider has an exact numeric input.
- ASCII preview works before Blender render.
- Validation failures are visible and block render.
- Save writes deterministic JSON.
- Render/export paths are visible.
- Git-ignored media stays ignored unless explicitly forced.

## Non-Goals

- Do not implement a general-purpose Blender replacement.
- Do not make a visual asset marketplace/gallery.
- Do not add collaborative cloud state.
- Do not add Figma-like freeform design tools.
- Do not build a node editor in v0.
- Do not support every asset family in the first UI.

This workbench exists to make source-owned procedural asset generation human
controllable without losing determinism.
