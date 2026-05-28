# Source Quality Notes v1

Research Dex should optimize for measured architectural primitives, not general architecture research.

## Priority Order

1. Measured drawings with explicit scales or dimensions.
2. Plan, elevation, and section sheets.
3. Public-domain treatises with explicit proportional rules.
4. Official building pages only when they provide concrete dimensions.
5. Academic PDFs only when they include explicit measured diagrams or tables.

## Use With Care

- Historic England archive records: rights and accessible measurement detail vary. Extract only factual measurements/ratios and record uncertainty.
- Building-specific pages: use only when a dimension is stated; do not infer from photographs.
- Treatises: use rules and vocabulary, not copied plates.

## Reject Or Mark Morphology Only

- Beautiful images with no dimensions.
- Pinterest, AI images, tourist photos, and unclear-provenance material.
- Full building histories without usable measurements.
- Sources that only support visual inspiration.

## Required Notes Per Source

Every source should include:

- `source_id`
- `source_url`
- `source_title`
- `source_type`
- `rights_note`
- `confidence`
- measurement-specific notes

If a source has no usable dimensions, record `source_type: "morphology_reference_only"` and do not create measurement rows from it.

