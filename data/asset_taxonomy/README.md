# Asset Taxonomy Data

This folder holds non-architecture asset taxonomy data that may later feed
characters, clothing, armor, props, tools, materials, and drafting workflows.

## Current Lanes

- `imported_seeds_v0/` contains raw taxonomy seed JSON copied from the user's
  local Documents folder.
- `imported_taxonomy_manifest_v0.json` records where the seeds came from, their
  counts, and how they should be treated.
- `normalized_domains_v0/shape_type_crosswalk_v0.json` maps imported shape and
  Blender-proxy phrases to repo geometry terms, Blender tool IDs, source fields,
  asset families, drafting tags, and promotion status.
- `musical_instruments_v0/musical_instrument_asset_taxonomy_v0.json` records
  starter musical-instrument prop families, visible anatomy, source support,
  geometry terms, Blender tool IDs, drawing UI tags, operator checks, and lore
  book hooks.
- `furniture_v0/furniture_asset_taxonomy_v0.json` records furniture families,
  furniture caste/status tiers, styles, visible anatomy, source support,
  geometry terms, Blender tool IDs, drawing UI tags, operator checks, and lore
  book hooks.

## Boundary

These imported seeds are not canonical architecture taxonomy and are not active
pipeline inputs. They are preserved as source/reference material until a later
slice promotes specific terms into validated repo schemas.

Musical-instrument records are source planning data only. They are not acoustic
engineering, fabrication guidance, historical-authenticity proof, playable-audio
implementation, or active generated-asset inputs.

Furniture records are source planning data only. They are not fabrication
guidance, ergonomic/safety guidance, historical-authenticity proof, conservation
guidance, or active generated-asset inputs.
