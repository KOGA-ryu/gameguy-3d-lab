# Component Style System V0

This folder documents the source layer that binds architectural taxonomy names
to geometric shaping ledgers and later Blender tool sequences.

The repo now separates the work into four lanes:

```text
docs/research/...                 human research, terminology, and build intent
data/architecture/taxonomy/...    domain/component names
data/architecture/component_style_sheets/... geometric ledgers and tool sequences
data/architecture/asset_mill/...  recipes and compilers after style selection
```

The first machine-readable files are:

```text
data/architecture/taxonomy/component_domains/component_domain_taxonomy_v0.json
data/architecture/component_style_sheets/component_style_sheet_registry_v0.json
data/architecture/component_style_sheets/railings/gothic_railing_post_style_sheets_v0.json
data/architecture/component_style_sheets/railings/single_post_style_matrix_v0.json
```

Validate them with:

```bash
python3 scripts/validate_component_style_sheets_v0.py
python3 scripts/validate_single_post_style_matrix_v0.py
```

## Documents

- `component_style_system_v0.md` explains the organization model.
- `asset_families/README.md` is the human-facing handbook for railings,
  stairs, windows, doors, trim/moulding, ceilings/vaults, and walls.
- `gothic_railing_post_research_findings_v0.md` records the first Gothic
  railing research findings and vocabulary.
- `gothic_railing_post_build_plans_v0.md` turns the research into first build
  plans.
- `railing_post_style_atlas_v0.md` narrows railing work to one reusable post
  with many style variants before full railing assemblies return.

## Boundary

These docs and JSON files do not generate mesh, execute Blender, claim
historical accuracy, or claim building-code compliance. They define source
contracts so later recipes can compile deterministic asset JSON or tool plans.
