# Chess To 3D Generation Mapping V0

This document maps chess-engine architecture onto the repo's 3D-generation
problem.

## Core Translation

| Chess engine term | 3D generation term |
| --- | --- |
| position | generation state |
| legal move | legal geometry/material/animation operation |
| move generator | candidate operation generator |
| make move | apply operation to source state |
| unmake move | revert operation from source state |
| search depth | operation sequence length |
| evaluation | candidate asset score |
| move ordering | operation priority policy |
| pruning | early rejection rules |
| transposition table | canonical JSON state cache |
| opening book | starting style templates and source recipes |
| tablebase | solved tiny component recipes |
| quiescence | stability/polish continuation |
| perft | branch-count validation for legal operations |
| UCI | generator-to-adapter protocol |
| GUI | Blender, drawing UI, or preview studio |

## Generation State

A future `gameguy_generation_state_v0` should be a complete source-side state,
not a Blender scene.

Minimum fields:

- `state_id`
- `asset_family`
- `style_id`
- `source_recipe_id`
- `source_graph_refs`
- `selected_points`
- `selected_segments`
- `selected_cells`
- `parts`
- `sockets`
- `materials`
- `constraints`
- `budget`
- `operation_history`
- `validation_state`
- `score_state`

The state must be serializable, canonicalized, hashable, and replayable.

## Legal Operation Categories

The legal operation generator should not invent arbitrary Blender actions. It
should emit operation records from known dictionaries and family policies.

### Selection Operations

- select point
- select segment
- select closed cell
- select ring
- select profile chain
- select source-reference feature

### Role Promotion Operations

- promote segment to rib
- promote segment to mullion
- promote segment to rail
- promote segment to molding path
- promote cell to panel
- promote cell to opening
- promote cell to relief field
- promote point to boss, bead, socket, hinge, rivet, or column center

### Form Operations

- extrude
- revolve
- loft
- sweep
- taper
- bend
- fold
- thicken
- inset
- bevel/chamfer
- mirror
- radial array
- linear array
- boolean cut
- boolean union

### Detail Operations

- add bead strip
- add collar
- add reveal
- add lip
- add boss
- add tracery opening
- add rib web
- add panel inset
- add damage variant
- add trim sheet region

### Game-Readiness Operations

- add collision proxy
- add LOD proxy
- assign material slot
- assign UV region
- assign socket
- mark movable/static part
- mark animation intent
- mark low-compute fallback

## Candidate Search

The first search should be simple:

```text
generation state
-> generate legal operations
-> apply operation
-> validate hard constraints
-> score candidate
-> keep best N candidates
-> repeat until stop condition
```

This is beam search. It fits 3D generation better than direct alpha-beta
because there is no opponent. Later, adversarial scoring can be added for
tradeoffs such as detail versus performance, but the first engine should stay
deterministic and readable.

## Evaluation Vector

Each candidate should receive a score object, not a single hidden number.

Recommended first score fields:

- `silhouette_score`
- `style_fit_score`
- `component_completeness_score`
- `source_provenance_score`
- `geometry_validity_score`
- `socket_score`
- `material_readiness_score`
- `low_compute_score`
- `operator_edit_distance_score`
- `novelty_score`

The generator should explain each score in plain text so the user can correct
the rule, not only reject the result.

## Hard Rejection Rules

Reject immediately when:

- an operation uses an unknown dictionary term
- an operation violates family stage order
- a part references missing geometry
- an operation is non-deterministic
- required sockets are missing after the socket stage
- dimensions exceed bounds
- low-compute policy is violated
- a candidate cannot be replayed from source JSON
- Blender-only design logic appears in the operation record

## Quiescence For Assets

The 3D equivalent of quiescence is "do not stop while the object is visibly
unstable."

Continue polishing when any of these flags are present:

- `open_socket`
- `floating_detail`
- `uncapped_profile`
- `missing_transition_collar`
- `unbeveled_exposed_corner`
- `missing_material_region`
- `unsupported_ornament`
- `bad_panel_depth`
- `asymmetric_pair_mismatch`

This should not mean infinite polish. It means the stop condition must include a
stability check.

## Protocol Boundary

The repo should eventually have a generation protocol shaped like UCI:

```text
load_state <state_json>
setoption <budget/style/evaluator>
go candidates <n> depth <d>
bestcandidate <candidate_json>
explain <candidate_id>
preview <candidate_id>
```

The Blender adapter should consume chosen candidate JSON and report execution
evidence. It should not choose the design.

## Why This Solves The User's Friction

The current pain is waiting for one correction at a time.

The engine approach lets the user say:

```text
From this selected graph, generate 12 legal Gothic railing infill candidates.
Keep the rail sockets, use the inner linework, avoid decals, and favor low
operator edit distance.
```

The system returns a ranked candidate set with reasons. The user can reject a
candidate by correcting the rule:

```text
Do not use outer guide circles as ornament. Promote inner rosette chords to
ribs, then use the small closed cells as cutouts.
```

That correction becomes a better move-ordering, pruning, or evaluation rule.

## First Asset Fit

Good first targets:

- a Gothic railing infill panel from selected 2D graph cells
- a door-frame molding stack from profile rules
- a small chest with hinges, lid, bands, and sockets
- a bell or lantern using revolve, handles, collars, and trim

The railing panel is the best first fit because the repo already has:

- railing taxonomy
- pattern field and segment tools
- component style sheets
- Blender tool dictionary
- guard-panel tool plans
- low-compute decal policy

The first engine slice should search small legal operation sequences around
that existing lane, not start a cathedral-scale generator.
