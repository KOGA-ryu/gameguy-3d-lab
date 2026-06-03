# 3D-LAB-0042 Railing 2D Profile Library Expansion

This slice expands the source-owned 2D shape vocabulary for railing generation. It does not compile new geometry yet.

## Added Profiles

- `railing_plinth_ogee_base_side_profile_v0`: custom polygon side profile for replacing plain square bases with a profiled plinth.
- `railing_rounded_rectangle_handrail_grip_v0`: rounded-rectangle cross-section for handrails, coping rails, and soft frame members.
- `railing_round_arch_panel_recess_v0`: round arch profile for panel, post, and frame recesses.
- `railing_triangle_chamfer_cut_v0`: triangular chamfer/drip/shadow profile for rail undersides and cap blocks.
- `railing_octagon_baluster_cross_section_v0`: octagonal low-poly baluster, picket, and shaft cross-section.
- `railing_star_rosette_cutout_v0`: star-polygon rosette or repeated ornament cutout.
- `railing_quatrefoil_panel_cutout_v0`: low-vertex custom polygon for quatrefoil and lobed tracery.

These join the existing square frame, pointed arch, capsule slot, circular bead, ogee molding, trapezoid collar, and lobed post cross-section profiles.

## Why This Matters

This is the shape-library layer the repo needs before making many assets:

```text
source-owned 2D profiles
-> placement and detail roles
-> allowed operation sequence
-> deterministic compiler
-> Blender adapter execution
```

The important part is that Blender still does not invent the design. The source profile decides the shape family, placement region, detail role, application method, and candidate tools.

## Validation

```text
PASS railing detail profile validation: profiles=14 placements=42 sequence=8 tools=13
PASS asset generation registry validation: geometry_bundles=5 geometry_assets=40 source_profiles=19 reference_only=3
compiled tool plans=7 steps=230 tools=97 out=<validate-only>
PASS generation pipeline validation: commands=31 json=236 include_blender=false
PASS generation pipeline validation: commands=45 json=236 include_blender=true
```

No repo-local media, mesh, render, export, or `.blend` files were produced.

## Next Geometry Target

The next useful geometry slice is:

```text
3D-LAB-0043-profiled-plinth-base-compiler-v0
```

Use `railing_plinth_ogee_base_side_profile_v0` to replace one plain square base with a source-owned profiled plinth extrusion.
