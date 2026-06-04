# Chess Engine Source Index V0

This source index supports the chess-engine-to-3D-generation analogy. These
sources are used for engine vocabulary and architecture, not for copying chess
engine code into the repo.

## Primary Engine Sources

1. Stockfish

   Source: <https://github.com/official-stockfish/Stockfish>

   Use in this repo: reference for a mature deterministic chess engine with a
   clean engine/program boundary, UCI support, search/evaluation orientation,
   and repeatable command-line behavior.

2. Stockfish official documentation

   Source: <https://official-stockfish.github.io/docs/stockfish-wiki/Home.html>

   Use in this repo: reference for how a serious engine documents search,
   evaluation, options, testing, and engine use without making the interface
   depend on a graphical board.

3. python-chess

   Source: <https://python-chess.readthedocs.io/en/latest/>

   Use in this repo: reference for programmatic board state, legal move
   generation, move application, PGN/FEN/UCI helpers, and testing utilities in a
   Python-accessible form.

4. Leela Chess Zero

   Source: <https://lczero.org/dev/wiki/>

   Use in this repo: reference for a neural-network/MCTS engine family. This is
   future-facing only; the first useful generation engine in this repo should be
   deterministic and source-rule based.

5. AlphaZero paper

   Source: <https://arxiv.org/abs/1712.01815>

   Use in this repo: reference for policy/value search language and self-play
   framing. This is not a first implementation target.

## Protocol And Taxonomy Sources

1. Universal Chess Interface

   Source: <https://backscattering.de/chess/uci/>

   Use in this repo: reference for separating an engine from the thing that
   shows the game. The 3D version should separate the generation engine from
   Blender, a drawing UI, and any game-engine import step.

2. Chess Programming Wiki

   Source: <https://www.chessprogramming.org/Main_Page>

   Use in this repo: secondary taxonomy for common engine terms such as
   alpha-beta, transposition tables, quiescence search, perft, move ordering,
   iterative deepening, and evaluation.

3. Alpha-beta pruning

   Source: <https://www.chessprogramming.org/Alpha-Beta>

   Use in this repo: vocabulary for pruning large search trees. The direct
   algorithm is adversarial, so it does not map one-to-one to asset generation.

4. Transposition table

   Source: <https://www.chessprogramming.org/Transposition_Table>

   Use in this repo: vocabulary for caching canonical states so the generator
   does not repeat equivalent operation paths.

5. Quiescence search

   Source: <https://www.chessprogramming.org/Quiescence_Search>

   Use in this repo: vocabulary for continuing search when a state is visibly
   unstable. In 3D, this means not stopping while a candidate still has obvious
   defects such as floating parts, unclosed sockets, unresolved bevels, or bad
   silhouette breaks.

6. Perft

   Source: <https://www.chessprogramming.org/Perft>

   Use in this repo: vocabulary for counting legal operation branches as a
   debug tool. This maps strongly to validating a legal operation generator.

## Source Use Notes

- Stockfish and python-chess support the deterministic state/legal-move/search
  framing.
- UCI supports the engine-adapter boundary.
- Chess Programming Wiki supports shared vocabulary and debugging patterns.
- Leela Chess Zero and AlphaZero support future policy/value search thinking,
  but should not be the first implementation because the current repo needs
  repeatable source-owned geometry, not opaque generation.
