# Asset Family Template V0

Use this structure for every new asset family page.

## Purpose

One or two paragraphs describing what this family does in the world and why it
matters for gameplay or map construction.

## Component Breakdown

List the named pieces. These should match or eventually feed
`data/architecture/taxonomy/component_domains/component_domain_taxonomy_v0.json`.

## Style Directions

List the style families that can change the look without changing the component
contract.

Examples:

- Gothic
- Romanesque
- Renaissance
- Baroque
- Victorian
- Art Nouveau
- Arts and Crafts
- Islamic geometric
- Modern
- Rustic

## Geometric Shaping Ledger

For each important component, write:

```text
component
-> source shapes
-> operations
-> edit knobs
-> visible result
```

## Blender Tool Groups

Name tool groups instead of one-off scripts:

- mesh primitives
- profile mesh from points
- curve/path sweep
- section stack or radial stack
- boolean cuts
- array or radial repeat
- bevel and weighted normals
- solidify or wireframe
- UV and material assignment
- validation/export

## First Build Targets

Pick small targets that prove the family without pretending to finish every
variant.

## Boundaries

Say what this page does not claim: code compliance, fabrication readiness,
historical accuracy, final materials, or game-engine integration.
