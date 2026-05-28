# Architectural Measurement Extraction Report v0

This packet is for procedural grammar and proportion reference only. It is not production approval, not a structural safety claim, not a fabrication claim, and not permission to copy artwork, plates, measured drawings, or visual assets.

## Scope

The extraction used a narrow source order: source records first, then only explicit dimensions or defensible proportional rules. When a source had useful visual material but no accessible dimensions or scalable proportions, it was recorded as no-extraction/inspiration-only.

Created files:

- `data/architecture/taxonomy/source_measurements/measurement_sources_v0.json`
- `data/architecture/taxonomy/source_measurements/extracted_measurements_v0.json`
- `docs/research/architectural_measurements/measurement_extraction_report_v0.md`
- `goal/receipts/architectural_measurement_extraction_v0.receipt.json`

## Sources Used

- `catholic_encyclopedia_arch_1907`: arch class and proportional construction rules.
- `rickman_english_architecture_7th_ed`: pointed arch class distinctions.
- `vitruvius_ten_books_gutenberg`: column proportional rules.
- `palladio_four_books_smithsonian`: column proportional rules.
- `amiens_cathedral_britannica`: Gothic nave width and vault height.
- `chartres_cathedral_dimensions`: Gothic nave width and vault height.
- `reims_cathedral_dimensions`: Gothic nave width and vault height.
- `pont_du_gard_britannica`: Roman arcade span examples.
- `ely_cathedral_octagon`: octagonal central plan and vault/lantern envelope.
- `castel_del_monte_architettura`: regular octagonal plan side and tower/courtyard dimensions.
- `pantheon_britannica`: dome and rotunda diameter relationship.
- `hagia_sophia_asce`: dome diameter and height-above-floor relationship.
- `habs_first_baptist_church_tn181`: explicit HABS imperial dimensions converted to meters.

Recorded but not extracted:

- `historic_england_kenilworth_archway`: useful measured-drawing archive record, but the accessible page did not provide usable dimensions in text.
- `loc_habs_collection`: collection-level registry source only; individual extraction requires dimensional evidence per item.

## Coverage

Enough measurement evidence for v0 grammar ranges:

- `pointed_arch_bay`: six records, combining one exact equilateral rule, two pointed class constraints, and three Gothic nave/vault span-height examples.
- `round_arch_bay`: five records, including the exact semicircular rule, one segmental constraint, and three span-only or opening-dimension examples.
- `octagonal_plan`: two records, including Ely's octagon and Castel del Monte's regular octagonal side/courtyard relationships.
- `dome_or_vault`: three records, including Pantheon, Hagia Sophia, and Ely's octagonal vault/lantern envelope.
- `column_or_pier`: three records, including Vitruvian/Palladian column proportions and one HABS splayed-opening dimensional proxy.

Weak areas:

- `wall_thickness_to_span`: no trustworthy v0 extraction. Leave null until a measured drawing or written source gives both values.
- `pier_to_span`: no full bay support-width-to-span record yet. Current support evidence is column height-to-diameter and an opening/splay proxy, not a complete bay pier ratio.
- `round_arch_bay` metric profiles: v0 has strong semicircular rule evidence and span examples, but weak rise/springline evidence for real buildings.
- `vault_rib`: v0 has envelope proportions, not rib section radii or rib thicknesses.

## Recommended Parameter Ranges

These ranges are grammar seeds only. They are not structural rules.

### pointed_arch_bay

- Intrados rise/span:
  - drop or obtuse pointed: below `0.866`
  - equilateral default: `0.866`
  - lancet: above `0.866`
- Practical v0 grammar band for pointed arch curve rise/span: `0.55-1.25`, with `0.866` as the defensible default.
- Full Gothic nave/vault height-to-span envelope from extracted examples: `2.287-2.897`.
- Confidence: medium. Treatise geometry is high confidence; building bay application is medium because nave/vault height is not identical to arch intrados rise.

### round_arch_bay

- Semicircular rise/span: `0.5`.
- Segmental circular rise/span: below `0.5`.
- Span examples:
  - Pont du Gard upper arcade: `4.6 m`.
  - Pont du Gard lower largest span: `24.0 m`.
  - HABS circular/recess dimension: `4.572 m`.
- Practical v0 grammar band for round arch curve rise/span: `0.25-0.5`, with `0.5` as the canonical round-arch default.
- Confidence: medium. The geometric rule is high confidence, but real-building metric rise data remains weak.

### octagonal_plan

- Ely octagon width: `23.0 m`; height: `43.0 m`; height/width: `1.87`.
- Castel del Monte external octagon side: `10.3 m`; tower diameter/side: `0.767`; courtyard side/external side: `0.669-0.760`.
- Regular octagon estimates from Castel del Monte side length:
  - across flats: `24.87 m`
  - across vertices: `26.92 m`
- Practical v0 grammar band:
  - tower or attached radial element diameter/external octagon side: `0.75-0.80`
  - inner court side/external side: `0.65-0.80`
- Confidence: high for stated dimensions; medium for derived regular-octagon diameters because they assume regularity from the stated side.

### column_or_pier

- Column height/diameter:
  - compact/heavy column: about `7.0`
  - slimmer classical column: about `9.0`
- Column radius/height seed range: `0.056-0.071`.
- Opening/splay proxy from HABS: visible window width/splayed opening width `0.815`.
- Practical v0 grammar band:
  - column radius/height: `0.05-0.075`
  - pier/support width to bay span remains weak and should stay null until measured bay examples are extracted.
- Confidence: high for treatise column ratios, medium/low for translating those ratios into pier support grammar.

### dome_or_vault

- Pantheon dome diameter/plan diameter: `1.0`; hemispherical rise/span grammar default: `0.5`.
- Hagia Sophia apex height/dome diameter: `1.565`.
- Ely octagonal vault/lantern height/span envelope: `1.87`.
- Practical v0 grammar band:
  - dome diameter/plan diameter: `0.9-1.0` when dome covers a central rotunda or central bay.
  - dome/vault apex height to clear span: `1.5-1.9` for tall central envelopes; use cautiously because this includes floor-to-apex height, not pure dome rise.
- Confidence: medium. Diameters and heights are explicit, but derived grammar interpretation depends on how the procedural bay defines floor, springline, and apex.

## Validation Notes

- JSON files parse.
- Every measurement references a known `source_id`.
- Every measurement has a confidence value.
- Numeric metric values are meters; unavailable values are null.
- No production approval is implied.
- No structural safety claim is made.
- No fabrication claim is made.
- No copied artwork, plate geometry, measured drawing image, or visual asset reuse is included.

