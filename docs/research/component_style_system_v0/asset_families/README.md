# Asset Families Handbook V0

This folder is the human-facing handbook for the component style system. It is
organized by asset family, not by script name, because that is how a person
thinks while building an environment.

Use this order when expanding the repo:

```text
family overview
-> component breakdown
-> style directions
-> geometric shaping ledgers
-> Blender tool groups
-> first build targets
-> boundaries and non-claims
```

## Family Pages

- `railings_v0.md`
- `stairs_v0.md`
- `windows_v0.md`
- `doors_v0.md`
- `trim_moulding_v0.md`
- `ceilings_vaults_v0.md`
- `walls_vertical_bays_v0.md`
- `family_style_matrix_v0.md`
- `asset_family_doc_template_v0.md`

## Why This Exists

The repo should not become a pile of one-off scripts. Each asset family needs a
clear vocabulary and a repeatable breakdown before recipes or Blender adapters
touch the shape.

The intended chain is:

```text
asset family page
-> component domain taxonomy
-> component style sheet
-> source recipe
-> deterministic asset JSON or tool-plan JSON
-> Blender adapter preview/export
```

## How To Read A Page

`Component Breakdown` tells us what the asset is made of.

`Style Directions` tells us the major looks worth supporting.

`Geometric Shaping Ledger` tells us which simple shapes and operations should
own the look.

`Blender Tool Groups` tells us which scripted tool families should execute the
look later.

`First Build Targets` tells us what to build before trying the whole cathedral.

## Shared Rule

If a Blender script has to decide the style, the style sheet is missing data.
Blender should execute a source-owned plan, not invent design decisions.
