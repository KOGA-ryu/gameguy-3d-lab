# Trim And Moulding V0

## Purpose

Trim and moulding are the detail language that makes simple geometry feel
intentional. This family should become a reusable profile library that can be
swept, extruded, wrapped around posts, applied to panels, or stacked into caps
and bases.

## Component Breakdown

Primary components:

- `fillet`
- `torus`
- `bead`
- `cove`
- `ovolo`
- `ogee`
- `cyma_recta`
- `cyma_reversa`
- `dentil`
- `cornice`

Useful anatomy:

- profile control points
- flat band
- convex roll
- concave hollow
- shadow groove
- lip
- drip
- projection
- return
- end cap

## Style Directions

Gothic:

- slender beads
- deep coves
- repeated small rolls
- pointed or chamfered edges

Classical/Renaissance:

- ordered base/cornice stacks
- cyma profiles
- dentil courses
- clean repeated proportions

Victorian:

- layered profiles
- heavy ogees
- bead-and-reel-like rhythms

Modern:

- simple reveals
- square shadow gaps
- minimal bevels

Rustic:

- thick boards
- rough chamfers
- uneven displacement

## Geometric Shaping Ledger

`fillet`

```text
source shapes: rectangle
operations: extrude, sweep, bevel_edges
edit knobs: width, height, run length, bevel width
visible result: small flat separator band
```

`torus` and `bead`

```text
source shapes: circle, capsule
operations: radial_stack, sweep, modifier_screw, array_linear
edit knobs: radius, segment count, spacing, projection
visible result: rounded convex molding or repeated small bead
```

`cove`

```text
source shapes: arch_profile, circle segment, custom profile
operations: profile_operation_stack, sweep, bevel_edges
edit knobs: hollow radius, depth, height, end return
visible result: concave shadow profile
```

`ogee`, `cyma_recta`, `cyma_reversa`

```text
source shapes: custom profile, arch_profile
operations: profile_operation_stack, sweep, section_stack, bevel_edges
edit knobs: upper radius, lower radius, inflection point, projection
visible result: S-shaped molding, cap lip, or base transition
```

`dentil`

```text
source shapes: square, rectangle
operations: extrude, array_linear, bevel_edges
edit knobs: block width, gap width, block depth, course length
visible result: repeated small block course
```

## Blender Tool Groups

- `mesh_from_pydata` for profile curves and wrapped control points
- `modifier_screw` for lathed caps, bases, and torus stacks
- curve/path sweep for rail and frame runs
- array for bead strips and dentils
- bevel/weighted normals for profile readability
- material assignment by named profile band
- validation for profile bounds and nonzero thickness

## First Build Targets

1. `simple_bead_strip_v0`
2. `ogee_cap_lip_profile_v0`
3. `cove_shadow_groove_v0`
4. `dentil_course_v0`
5. `profile_stack_cap_and_base_v0`

## Boundary

This page does not decide where trim is placed on a building. Placement belongs
to the parent asset recipe or map module.
