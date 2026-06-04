# Operator Generation Engine Handoff V0

This document defines how the user should eventually drive a search-based
generation engine without needing perfect Blender vocabulary.

## Operator Request Shape

A useful request should describe:

- `asset_family`
- `style_id`
- `source_graph_or_reference`
- `selected_regions`
- `must_have_parts`
- `forbidden_parts`
- `allowed_operations`
- `forbidden_operations`
- `budget`
- `candidate_count`
- `depth_or_pass_count`
- `scoring_weights`
- `stop_conditions`

The user should not need to name every Blender command. The repo should infer
legal tool sequences from style sheets, dictionaries, and family policies.

## Example Requests

### Railing Infill

```text
Generate 12 Gothic railing infill candidates from the selected inner rosette
linework. Keep rail sockets, avoid decals, use low-compute geometry, and prefer
clear negative-space cutouts over dense surface decoration.
```

### Door Frame

```text
Generate 8 pointed-arch door-frame candidates. Must include threshold, jambs,
archivolt, reveal, hinge-side socket hints, and stone material regions. Favor
profiles that can be edited by hand later.
```

### Vault Rib

```text
From this sacred construction graph, promote selected long curves to ribs,
selected cells to web panels, and intersections to bosses. Search 4 passes and
stop when all ribs have caps and material regions.
```

### Prop

```text
Generate 10 low-poly lute body candidates. Keep the body, neck, pegbox, bridge,
soundhole, and string anchors. Do not add fragile high-frequency ornament.
```

## Candidate Report Shape

Every candidate should report:

- candidate ID
- operation sequence
- score breakdown
- rejected warnings
- source terms used
- Blender tools needed later
- estimated manual edit areas
- low-compute notes
- preview/export status

## User Correction Shape

When the user rejects a candidate, capture the reason as a reusable rule:

```text
This used the outer guide circle as ornament. The outer circles are only
construction guides. Use the inner rosette chords for linework and the small
closed cells for cutouts.
```

That should become:

- forbidden operation: `promote_outer_guide_circle_to_ornament`
- preferred operation: `promote_inner_rosette_chord_to_rib`
- scoring change: penalize guide-line ornament use
- source tag change: mark guide circles as non-promotable by default

## Manual Editing Plan

The engine should prepare the asset so the user can make final calls in Blender.

For each accepted candidate, provide:

- where to inspect first
- which Blender tools are expected
- which parts are intentionally simple
- which details are procedural and safe to rebuild
- which details are hand-edit candidates
- which corrections should be written back to source

## Review Checklist

Before a candidate is accepted:

- source JSON can reproduce it
- operation sequence uses known terms
- candidate does not rely on Blender-only design decisions
- required components exist
- sockets exist where needed
- geometry budget is explicit
- low-compute policy is respected
- material regions are named
- manual-edit areas are listed
- rejection/correction notes can feed future rules

## Best First Operator Loop

The first practical loop should be:

```text
seed state
-> generate small candidate set
-> user picks closest candidate
-> user gives one correction
-> correction becomes rule
-> regenerate candidate set
```

This is how the repo gets out of one-off prompting and starts learning the
user's architectural language as deterministic source rules.
