# Component Style System V0

## Problem

The repo needs to support many asset domains: railings, stairs, windows, doors,
trim, moulding, ceilings, and walls. A single script per object will not scale.
The missing layer is a stable contract that connects architectural names to
geometric construction choices.

## Source Contract

Each buildable style follows this chain:

```text
domain taxonomy
-> component
-> component style sheet
-> geometric shaping ledger
-> Blender tool sequence
-> recipe/compiler target
```

Example:

```text
railings
-> newel_post
-> gothic_railing_post.clustered_shaft_newel_v0
-> clustered shaft + collars + cap
-> radial stack, section stack, bevels, weighted normals
-> gameguy_asset_v0 or gameguy_tool_plan_v0 later
```

## Folder Ownership

```text
docs/research/component_style_system_v0/
```

Human-readable research, taxonomy explanation, build-plan notes, source links,
and design tradeoffs.

```text
data/architecture/taxonomy/component_domains/
```

Source taxonomy for domains and reusable components. It names what exists, but
does not decide geometry.

```text
data/architecture/component_style_sheets/
```

Source-owned style sheets. These bind a taxonomy component to shape terms,
operation terms, construction rules, edit knobs, and Blender tool IDs.

```text
data/architecture/asset_mill/recipes/
```

Actual pump recipes after a style sheet is selected and promoted into a
specific asset.

## Domain Taxonomy

The first domain taxonomy names seven domains and seventy components:

- `railings`
- `stairs`
- `windows`
- `doors`
- `trim_moulding`
- `ceilings`
- `walls`

The point is not to finish all of them now. The point is to make room for them
without polluting Blender scripts or asset recipes.

The human-facing handbook for these domains lives in:

```text
docs/research/component_style_system_v0/asset_families/
```

Those pages are intentionally organized by asset family. They are where a
person can read the component breakdown, style directions, geometric shaping
ledger, Blender tool groups, and first build targets before anything is
promoted into machine-readable style sheets.

## Component Style Sheet Shape

A component style sheet must answer these questions:

- Which domain and component does this style apply to?
- What style family is it in?
- What anatomical parts does the component have?
- Which 2D/profile/measurement terms shape each part?
- Which operations build the part?
- Which edit knobs should a user tune later?
- Which Blender tools can execute the look, in what stage order?
- Which compile targets can consume the result later?

That turns vague prompts like "make the post Gothic" into a source-owned
ledger:

```text
post style -> plinth/base/shaft/collar/cap/finial -> shapes -> operations -> tools
```

## Validator

`scripts/validate_component_style_sheets_v0.py` checks:

- domain and component IDs exist in the taxonomy
- style families exist in the taxonomy
- source shape terms exist in `geometry_dictionary/`
- operations exist in `geometry_dictionary/`
- Blender tool IDs exist in `blender_tool_dictionary_v0.json`
- Blender stage order is valid
- no source sheet executes Blender or generates assets

## Promotion Path

The next compiler should not read free-form prose. It should consume the style
sheet JSON and promote one selected style into either:

```text
component style sheet -> source recipe -> asset_pump_v0 -> gameguy_asset_v0
```

or:

```text
component style sheet -> tool-plan recipe -> compile_blender_tool_plan_v0 -> gameguy_tool_plan_v0
```

Blender remains an adapter in both cases.
