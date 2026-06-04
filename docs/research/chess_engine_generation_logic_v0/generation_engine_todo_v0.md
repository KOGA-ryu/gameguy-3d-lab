# Generation Engine Todo V0

This TODO turns the chess-engine analogy into repo work.

## Phase 0: Research And Terms

Status: this packet.

Deliverables:

- source index
- engine concept glossary
- chess-to-3D mapping
- operator handoff language
- first implementation plan

## Phase 1: Generation State Schema

Define `gameguy_generation_state_v0`.

Required properties:

- source-side only
- JSON serializable
- canonicalized for hashing
- includes operation history
- includes validation and scoring metadata
- can point at construction graphs, profile bundles, recipes, and tool plans

Do not store Blender object state as the source of truth.

## Phase 2: Legal Operation Generator

Create a small legal operation generator over one asset family.

Recommended first family: Gothic railing infill panel.

Inputs:

- component style sheet
- construction graph or segment selection
- geometry dictionary
- Blender tool dictionary
- asset family sequence policy
- budget policy

Output:

- deterministic candidate operation records
- rejected-operation reasons

## Phase 3: Perft-Style Branch Counter

Add a debug command:

```bash
python3 scripts/count_generation_branches_v0.py \
  --state /tmp/gameguy_generation_state_v0/state.json \
  --depth 3
```

The command should count legal operation branches without scoring or rendering.

Purpose:

- prove legal operation generation is stable
- reveal branch explosion early
- make changes testable
- catch accidental loss of valid operations

## Phase 4: Deterministic Evaluator

Add a first evaluator with explicit score fields:

- silhouette
- style fit
- component completeness
- source provenance
- geometry validity
- socket completeness
- material readiness
- low-compute fit
- operator edit distance

Each score must include a short reason.

## Phase 5: Beam Search Prototype

Implement beam search before alpha-beta or neural/MCTS work.

Why:

- 3D generation is not adversarial
- the user needs ranked alternatives, not one opaque answer
- beam width gives an understandable quality/performance knob
- candidate reasons help the user teach the system

Example:

```bash
python3 scripts/search_generation_candidates_v0.py \
  --state data/.../gothic_railing_infill_seed_state_v0.json \
  --depth 5 \
  --beam-width 12 \
  --out /tmp/gameguy_generation_candidates_v0
```

## Phase 6: Canonical State Cache

Add a transposition-table-like cache:

- canonical JSON hash
- validation result
- score result
- rejected reason
- candidate preview metadata

This avoids repeating equivalent operation sequences.

## Phase 7: Generator Protocol

Define a small protocol inspired by UCI, but for generation:

```text
load_state
setoption
go
stop
bestcandidate
explain
preview
export
```

This keeps the generator separate from:

- Blender
- browser selection studio
- future drawing/drafting UI
- game-engine import/export

## Phase 8: Candidate Review Loop

Add an operator review artifact:

- candidate list
- score breakdown
- preview path if generated
- accepted candidate
- rejection reasons
- correction notes
- promoted rule changes

This is the part that reduces the user's 15-minute correction loop.

## Phase 9: Promote Corrections Back To Source

When the user says a candidate is wrong, capture the correction as one of:

- forbidden operation
- new source field
- changed operation ordering
- changed evaluator weight
- new style rule
- new geometry term
- new Blender tool card
- new asset-family policy

The final product is not just a better candidate. It is a better generator.

## Explicit Non-Goals For The First Build

- no neural model
- no self-play training
- no opaque "AI art" scoring
- no cathedral-scale global generator
- no Blender script that invents design decisions
- no render-gallery output in the repo

## First Slice Recommendation

Name:

```text
3D-LAB-0092 generation_state_schema_v0
```

Goal:

```text
Define gameguy_generation_state_v0 and one tiny Gothic railing infill seed
state. No search yet.
```

Why this is the right first move:

- the repo already has railing and pattern-field source layers
- legal operations need a state object before search exists
- validation can be tiny and deterministic
- it establishes the boundary before Blender is involved
