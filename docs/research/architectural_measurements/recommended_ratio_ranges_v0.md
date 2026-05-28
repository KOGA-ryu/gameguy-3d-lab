# Recommended Ratio Ranges v0

These ranges are grammar/proportion hints only. They are not structural rules, fabrication dimensions, production approvals, or copied historical geometry.

## `pointed_arch_bay`

- Curve rise/span:
  - drop or obtuse pointed: below `0.866`
  - equilateral default: `0.866`
  - lancet: above `0.866`
- Practical v0 grammar band: `0.55-1.25`.
- Full Gothic nave/vault height-to-span envelope from v0 examples: `2.287-2.897`.
- Confidence: medium.

## `round_arch_bay`

- Semicircular rise/span: `0.5`.
- Segmental circular rise/span: below `0.5`.
- Practical v0 grammar band: `0.25-0.5`.
- Span examples in v0: `4.572-24.0 m`.
- Confidence: medium.

## `octagonal_plan_core`

- Ely octagon width/height: `23.0 m / 43.0 m`; height/width `1.87`.
- Castel del Monte tower diameter/external octagon side: `0.767`.
- Castel del Monte courtyard side/external side: `0.669-0.760`.
- Practical v0 grammar band:
  - radial tower or attached element diameter / external octagon side: `0.75-0.80`
  - inner court side / external side: `0.65-0.80`
- Confidence: high for stated dimensions; medium for regular-octagon derived diameters.

## `column_or_pier`

- Column height/diameter: `7.0-9.0`.
- Column radius/height seed range: `0.056-0.071`.
- Pier/support width to bay span remains weak and should stay null.
- Confidence: high for treatise column ratios, weak for pier translation.

## `dome_or_vault`

- Dome diameter/plan diameter: `0.9-1.0` for central rotunda/central bay grammar.
- Hemispherical dome rise/span default: `0.5`.
- Tall central envelope height/span examples: `1.565-1.87`.
- Confidence: medium.

## Compiler Output

The factory measurement lane can validate the source/extraction files and compile current ranges with:

```sh
python3 scripts/validate_architectural_measurements_v0.py
python3 scripts/compile_architectural_proportion_ranges_v0.py
```

Current compiled output:

- `goal/architecture/architectural_taxonomy_v0/proportion_ranges_v0.json`
- `goal/architecture/architectural_taxonomy_v0/architectural_measurement_taxonomy_report_v0.md`

