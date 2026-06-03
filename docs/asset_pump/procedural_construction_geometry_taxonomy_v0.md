# Procedural Construction Geometry Taxonomy v0

## Purpose
Give the repo the words needed to describe what the user is asking for:

```text
dense 2D construction field
-> select or omit nodes, edges, and cells
-> promote selected pieces into architectural roles
-> lift, fold, sweep, thicken, chamfer, bevel
-> deterministic asset geometry or tool-plan JSON
-> Blender adapter preview/export
```

This is not a game app, render gallery, or Blender-first modeling lane. The construction geometry remains source language. Blender consumes compiled decisions.

Machine-readable taxonomy:

```text
data/architecture/taxonomy/construction_geometry/construction_geometry_taxonomy_v0.json
```

Validator:

```bash
python3 scripts/validate_construction_geometry_taxonomy_v0.py
```

## Working Sentence
The repo is building procedural construction geometry: a dense construction field whose selected nodes, edges, and cells are promoted into architectural form.

## Core Terms

| Plain phrase | Repo term | Meaning |
| --- | --- | --- |
| master pattern | `construction_field` | Full hidden guide network: rings, points, edges, star traces, chords, diagonals, cells. |
| chosen lines | `selected_subgraph` | Named subset of nodes, edges, or cells chosen from the field. |
| left-out lines | `selective_omission` | Guides that remain invisible so the final model does not become every line in the drawing. |
| make this line real | `line_promotion` | Turn a guide edge into a rib, rail, mullion, trim strip, flute, bead, or fold seam. |
| make this point real | `node_promotion` | Turn a point into a boss, socket, column placement, capital center, or anchor. |
| make this region real | `cell_promotion` | Turn a closed cell into a panel, recess, web surface, cutout, muqarnas cell, or lifted patch. |
| repeated local pattern | `motif_module` | One reusable motif extracted from the construction field. |
| repeated around a center | `motif_orbit` | Rotated, mirrored, or translated motif instances. |
| dome/ceiling cell map | `muqarnas_cell_plan` | 2D cells assigned to tiers and lifted into a 3D vault or dome-like form. |
| give it depth | `lift_operation` | Assign height/depth to a 2D selection. |
| bend the pieces | `fold_operation` | Angle selected cells around fold lines. |
| run a profile along it | `sweep_operation` | Push a 2D profile along a selected curve or line. |
| make it physical | `thicken_operation` | Give selected lines or surfaces material thickness. |
| soften/cut the edge | `chamfer_bevel_operation` | Add lips, edge highlights, and stone-like transitions without bloating the source outline. |
| tier by tier | `cascade_order` | Declared order for lifting, folding, repeating, or suppressing selections. |

## Source Support

The user claim is defensible, with careful wording.

- Islamic geometric design and museum references support the idea that patterns arise from circles, grids, divisions, intersections, repeated polygons, and deliberate visible-line choices: [ArchNet](https://www.archnet.org/collections/864?media_content_id=7657), [Met Museum](https://www.metmuseum.org/essays/geometric-patterns-in-islamic-art).
- Girih and strapwork support the idea that larger ornamental fields can be generated from formal motif/tile relationships: [Tilings Encyclopedia](https://tilings.math.uni-bielefeld.de/glossary/girih/), [Lu and Steinhardt record](https://colab.ws/articles/10.1126/science.1135491).
- Gothic analysis and medieval drawing practice support treating cathedral details as geometric procedures rather than only hand-sculpted decoration: [Robert Bork record](https://iro.uiowa.edu/esploro/outputs/journalArticle/Dynamic-Unfolding-and-the-Conventions-of/9984398190202771?institution=01IOWA_INST&recordUsage=false&skipUsageReporting=true), [Columbia Amiens](https://projects.mcah.columbia.edu/amiens-arthum/dynamic-geometry), [Drawing Matter](https://drawingmatter.org/medieval-masons-and-tracing-floors/).
- Muqarnas and geometric pattern drawing references support the 2D-cell-plan-to-3D-vault direction: [Getty Topkapi Scroll](https://www.getty.edu/publications/virtuallibrary/9780892363353.html), [Nexus Network Journal](https://link.springer.com/article/10.1007/s00004-026-00878-8).

## Repo Consequence

The current sacred graph should not directly become a column, railing, window, or dome. It should feed selectors.

The intended source chain is:

```text
sacred_graph_recipes_v0.json
-> construction graph JSON
-> named selected_subgraph records
-> role_promotion records
-> operation stack records
-> gameguy_asset_v0 or gameguy_tool_plan_v0
```

For the railing, this means:

```text
construction_field
-> select cells for base face panels
-> promote edges to raised lips and bead strips
-> promote cells to recessed fields
-> thicken and bevel
-> wrap on four sides
-> compiled tool plan
-> Blender preview
```

For the dome/vault idea, this means:

```text
construction_field
-> select closed cells
-> assign cascade_order
-> lift/fold cells by tier
-> sweep ribs along promoted edges
-> thicken/bevel ribs and panels
-> deterministic vaulted asset JSON
```

## Guardrails

- Do not hide selection decisions in Blender.
- Do not turn every guide line into mesh.
- Do not call a construction field historical proof.
- Do not claim structural safety, fabrication readiness, or building-code compliance.
- Do not generate final meshes until source selection, promotion, and operation order are explicit.

## Current Compiler Slice

`3D-LAB-0050 construction_cell_selection_v0` adds the first cell-selection compiler:

```bash
python3 scripts/compile_construction_cell_selection_v0.py \
  --clean \
  --graph-manifest /tmp/gameguy_sacred_graph_v0/manifest.json \
  --out /tmp/gameguy_construction_cell_selection_v0
```

It reads the existing sacred graph output, derives simple closed cells between adjacent radial divisions and rings, selects cells by ring band and radial orbit, labels them with roles such as `vault_web_cell`, `tracery_opening_cell`, and `railing_panel_face`, previews selected cells in SVG, and emits JSON only.

`3D-LAB-0051 pattern_field_v0` adds the first multi-center rosette field compiler:

```bash
python3 scripts/compile_pattern_field_v0.py \
  --clean \
  --out /tmp/gameguy_pattern_field_v0
```

It creates a construction drawing closer to the user's paper reference: repeated large rosettes, smaller bridge rosettes, guide circles, radial rays, ring segments, selected star traces, selected connector traces, JSON output, and SVG preview.

`3D-LAB-0052 pattern_segment_split_v0` adds the first intersection splitter:

```bash
python3 scripts/compile_pattern_segments_v0.py \
  --clean \
  --pattern-field-manifest /tmp/gameguy_pattern_field_v0/manifest.json \
  --out /tmp/gameguy_pattern_segments_v0
```

It computes line intersections in the multi-center pattern field, splits source edges into candidate segments, preserves selected source-trace tags, and previews the intersection points. The next compiler should either omit guide segments and extract closed motif loops, or promote selected cells/edges into operation stacks:

```text
selected construction cells/edges
-> role promotion records
-> lift/fold/sweep/thicken/chamfer operations
-> railing panel or vault-web prototype
```
