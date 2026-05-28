# Architectural Measurement Fetch Packet v1

This is the next Research Dex fetch packet. It is a measurement/source-lane request only. It is not Pattern Lab work, not Blender work, not asset generation, and not visual inspiration collection.

## Landing Path

Research Dex should write v1 source-backed results under:

- `data/architecture/taxonomy/source_measurements/measurement_sources_v1.json`
- `data/architecture/taxonomy/source_measurements/extracted_measurements_v1.json`
- `data/architecture/taxonomy/source_measurements/measurement_parts_taxonomy_v1.json`
- `data/architecture/taxonomy/source_measurements/measurement_geometry_term_links_v1.json`
- `data/architecture/taxonomy/source_measurements/measurement_semantic_role_links_v1.json`

Proof and report files belong under:

- `docs/research/architectural_measurements/measurement_extraction_report_v1.md`
- `docs/research/architectural_measurements/source_quality_notes_v1.md`
- `docs/research/architectural_measurements/recommended_ratio_ranges_v1.md`
- `goal/receipts/architectural_measurement_extraction_v1.receipt.json`

Do not put raw research into `pattern_lab/`, `pattern_lab_3d/`, `factory/artifacts/`, or `zoo/`.

## Primary Sources

| Source | Use For | Note |
| --- | --- | --- |
| LOC HABS/HAER/HALS | measured drawings, plans, elevations, sections, historic structures | Best source. Prefer measured drawings and scale-backed sheets. |
| Historic England Archive | measured drawings, historic plans, architectural details | Good for UK/gothic/medieval references. Rights vary, so extract measurements only and record uncertainty. |
| Vitruvius, Project Gutenberg | classical proportions, terms, orders, principles | Public-domain text. Use for proportion vocabulary, not visual copying. |
| Palladio, Smithsonian | classical plans, elevations, column/order proportions | Use for measured classical grammar and plan/section ratios. |
| Ely Cathedral Octagon | octagonal tower/dome/lantern reference | Strong target for octagon width and internal height. |
| Castel del Monte | octagonal fortress plan, towers, radial symmetry | Use for octagonal plan grammar. If dimensions are missing, mark morphology reference only. |

## First Fetch Batch

Fetch exactly:

- 10 arch bay records.
- 5 octagonal/dome plan records.
- 5 column/pier records.
- 5 vault/rib cell records.
- 5 portal/window frame records.

The goal is broad coverage for `architectural_proportion_ranges_v1`, then downstream 2D arch/octagon manifests, 3D bay/portal/dome proof recipes, and factory jobs.

## Required Record Shape

```json
{
  "measurement_id": "pointed_arch_bay_springline_ratio_v1",
  "source_id": "loc_habs_example_v1",
  "object_class": "pointed_arch_bay",
  "part": "springline",
  "measurement_name": "springline_height_ratio",
  "value": 0.58,
  "unit": "normalized_ratio",
  "basis": "springline_height / overall_height",
  "confidence": "medium",
  "uncertainty": "estimated from measured drawing scale",
  "geometry_terms": ["arch_profile", "rectangle_profile", "extrude"],
  "semantic_roles": ["opening", "support", "panel_socket"],
  "ready_for_recipe": true
}
```

## Quality Rules

- Prefer measured drawings over photos.
- Prefer plan/elevation/section drawings over prose.
- Use normalized ratios first.
- Use absolute dimensions only when the source gives them.
- If a source gives no dimensions, mark `morphology_reference_only`.
- Do not claim structural safety.
- Do not claim cultural authenticity.
- Do not download or reuse protected images.
- Extract ratios and taxonomy, not art.

