# Shape Type Crosswalk V0

The normalized crosswalk lives here:

```text
data/asset_taxonomy/normalized_domains_v0/shape_type_crosswalk_v0.json
```

It maps imported taxonomy phrases into repo-native build language:

```text
imported term
-> normalized intent
-> geometry dictionary terms
-> Blender tool IDs
-> tool-card docs
-> source fields needed
-> useful asset families
-> drafting UI tags
-> promotion status
```

## Why This Exists

The imported asset taxonomies contain good phrases like:

- `dome_shell`
- `lamellar_panel_array`
- `woven_sheet_grid`
- `running_stitch`
- `curve_strip`
- `ball_socket_proxy`
- `flat_spline_plate`
- `bezier_curve_strip with tick marks`

Those phrases are useful, but they are not yet repo contracts. The crosswalk
turns them into actionable recipe/tool-plan language without making them active
generation inputs too early.

## First Coverage

V0 covers these representative shape families:

- dome and cone shells
- face masks, shield boards, plates, lamellar rows, rivet grids
- quilted channels and woven sheet grids
- cloth shells, flat pattern panels, seams, stitches, binding strips
- capsules, ellipsoid pads, joint proxies, cord curves
- rings, blades, spline plates, measuring ribbons, spools, peg/bar frames,
  buckle frames, and wire spirals

## Drafting UI Connection

The `drafting_tags` field is the bridge to the future drawing tool. A user could
draw a shape and tag it as:

```text
closed_cell + plate + array
```

or:

```text
selected_line + seam + stitch
```

The crosswalk then tells the repo which geometry terms, Blender tools, and source
fields are needed before a deterministic tool plan can be compiled.

## Boundary

The crosswalk is still source triage. It does not compile assets, run Blender, or
promote imported terms into canonical recipes. Promotion should happen only after
a validator, a workcard, and at least one operator pass prove the term is useful.

