# Chess Engine Generation Logic V0

This lane researches chess-engine architecture as a model for deterministic
3D-generation control.

The useful idea is not to add chess to the repo. The useful idea is to borrow
the engine shape:

```text
current state -> legal moves -> apply/revert -> search -> evaluate -> choose
```

For this repo, that becomes:

```text
source asset state -> legal geometry operations -> deterministic operation
sequence search -> scored candidate asset JSON -> Blender adapter preview/export
```

## Documents

- `chess_engine_source_index_v0.md` records the sources used for chess-engine
  vocabulary and architecture.
- `chess_engine_concepts_v0.md` explains the engine concepts in plain language.
- `chess_to_3d_generation_mapping_v0.md` maps those concepts onto asset
  generation, Blender adapters, and operator review.
- `generation_engine_todo_v0.md` defines a phased build plan for a future
  deterministic generation engine.
- `operator_generation_engine_handoff_v0.md` defines how the user should drive
  and correct that engine without waiting on one tiny edit at a time.

## Boundary

This is documentation and research only. It does not implement a chess engine,
run a neural model, execute Blender, compile asset JSON, or change the existing
asset pump.

The repo should keep the same source-first rule:

```text
source recipe and legal operation sequence -> deterministic JSON -> Blender
adapter
```

If a future Blender script starts deciding the design, that logic belongs back
in a recipe, operation generator, evaluator, or search policy.
