# Chess Engine Concepts V0

This document explains the chess-engine ideas that are useful for 3D generation.

## Board State

A chess engine starts from a complete position: pieces, side to move, castling
rights, en-passant state, clocks or counters, and enough history to judge
legality.

For this repo, a generation engine needs the same kind of complete state:

- selected asset family
- source recipe
- construction graph or profile inputs
- current parts
- current sockets
- current material slots
- current constraints
- budget and low-compute policy
- operation history

## Legal Move Generation

An engine does not try every imaginable action. It generates only legal moves
from the current position.

For 3D generation, this becomes a legal operation generator. It should only emit
operations allowed by the current component, source terms, operation dictionary,
asset family policy, and budget.

Examples:

- select a construction segment
- promote a closed cell to panel, opening, rib, boss, socket, or ornament
- extrude a selected face/profile
- sweep a molding profile along a rail
- revolve a radial profile into a post
- bevel an exposed arris
- array a bead or spindle
- mirror a side detail
- boolean-cut a recess
- assign a material region
- create a collision proxy or LOD proxy

## Make And Unmake

Chess search repeatedly applies and reverts moves. This lets the engine explore
many futures without corrupting the original state.

For this repo, each operation should be reversible at the source-JSON level:

```text
state + operation -> next state
next state - operation -> previous state
```

That does not mean Blender must undo every edit. It means the source compiler
must be able to replay or discard candidate operation sequences deterministically.

## Search Tree

Chess engines build a tree of possible move sequences. Every branch is one
possible future.

For assets, each branch is one possible build plan:

```text
choose base footprint
-> choose shaft style
-> add rail socket
-> add trim stack
-> add ornament
-> add finish stack
```

The generator should search operation sequences, not random mesh edits.

## Evaluation

Chess engines score positions so the search can choose good branches.

For 3D generation, evaluation should score candidate assets. A first evaluator
can be deterministic and weighted:

- silhouette match
- style fit
- component completeness
- source-reference provenance
- geometry validity
- socket and attachment completeness
- material and wear readiness
- low-compute compatibility
- expected operator edit distance

## Pruning

Search trees explode. Chess engines prune branches that cannot matter.

For 3D assets, pruning should reject candidates early when they violate hard
rules:

- unknown geometry term
- forbidden Blender tool for the family
- missing required socket
- impossible bounds
- too much detail for the target budget
- decorative operation before the base structure exists
- material/detail operation applied to a non-existent part
- non-deterministic operation

## Move Ordering

Chess engines search promising moves first. That makes pruning and search
quality much better.

For 3D assets, operation ordering should prefer moves that satisfy the user's
current goal:

- structural moves before ornament
- silhouette moves before surface polish
- sockets before fine decoration
- source-reference-selected details before generic details
- low-risk legal operations before experimental operations

## Transposition Table

Different chess move orders can reach the same position. Engines cache those
states so they do not re-search identical work.

For 3D generation, equivalent operation sequences can also lead to the same
candidate state. A future generator should hash canonical JSON state and cache:

- score
- validation result
- rejected reason
- best next operations
- preview metadata

## Iterative Deepening

Chess engines often search shallow first, then deeper as time allows.

For assets, this maps to candidate refinement:

```text
depth 1: base silhouette
depth 2: major component layout
depth 3: sockets and trim
depth 4: ornament groups
depth 5: finish, UV, LOD, collision
```

This is a good fit for the user's workflow because a useful rough candidate can
appear before a full near-finished candidate exists.

## Quiescence

Chess engines avoid stopping evaluation in obviously unstable tactical moments.

For 3D assets, the generator should avoid stopping while a candidate still has
obvious unresolved defects:

- open sockets
- floating ornaments
- mismatched caps
- bevels missing on exposed low-poly corners
- rail/post intersections without collars
- unsupported decoration
- missing material regions

The 3D version is a "polish until stable" pass.

## Perft

Perft counts legal move branches from a chess position. It is a debugging tool
for move generation correctness.

For this repo, a perft-like command should count legal generation branches:

```text
given state X:
depth 1 -> 24 legal operations
depth 2 -> 318 legal operation sequences
depth 3 -> 4,921 legal operation sequences
```

If the count changes unexpectedly, the legal operation generator changed.

## Opening Books And Tablebases

Chess engines can use known solved or precomputed knowledge.

For this repo:

- opening book = known style templates, starting recipes, and family policies
- tablebase = tiny solved components, such as standard hinges, sockets, bead
  strips, rail collars, plinth layers, and simple ornament modules

This is how the repo gets faster without guessing.

## UCI Boundary

Chess engines commonly talk to graphical interfaces through a protocol. The GUI
shows the game; the engine decides moves.

The repo needs the same boundary:

```text
generation engine -> deterministic JSON/protocol -> Blender or drawing UI
```

Blender should be the viewer/exporter and tool executor, not the source of
design decisions.

## Neural And MCTS Engines

Neural/MCTS engines such as Leela Chess Zero and AlphaZero-style systems use
policy/value guidance and search rather than only handcrafted evaluation.

That is interesting later. It is not the right first target. The current repo
needs:

- deterministic legal operations
- reproducible candidate states
- readable score reasons
- source-owned recipes
- operator correction capture

Opaque learned scoring can come later only after the source-rule system is
solid enough to generate training examples or preference data.
