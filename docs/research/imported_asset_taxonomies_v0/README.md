# Imported Asset Taxonomies V0

This folder organizes the asset taxonomy seed files imported from the user's
local Documents folder.

The imported JSON seeds live in:

```text
data/asset_taxonomy/imported_seeds_v0/
```

The manifest is:

```text
data/asset_taxonomy/imported_taxonomy_manifest_v0.json
```

## Imported Domains

- armor history
- armor-making materials, tools, techniques, and output families
- human body/anatomy proxy chunks
- human textile, clothing, stitching, seams, materials, and surface patterns
- sewing/textile equipment props

## Why This Matters

These documents are a second source-taxonomy lane. They are not directly about
Gothic architecture, but they are valuable for the broader asset system:

- characters and body proxies
- armor and wearable equipment
- clothing and cloth construction
- sewing/workshop props
- material, stitch, seam, and surface pattern vocabulary
- drawing/drafting UI tags that can imply Blender tools

## Crosswalk

`shape_type_crosswalk_v0.md` explains the first normalized crosswalk. The data
lives in `data/asset_taxonomy/normalized_domains_v0/shape_type_crosswalk_v0.json`
and is validated by:

```bash
python3 scripts/validate_imported_taxonomy_crosswalk_v0.py
```

## Boundary

The imported seeds are raw source material. They are not yet validated against
repo schemas, not active generator inputs, and not part of the architecture
component taxonomy.

Specific terms should be promoted only after triage.
