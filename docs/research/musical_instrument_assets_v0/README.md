# Musical Instrument Assets V0

This folder starts the musical-instrument prop and lore lane.

The machine-readable source is:

```text
data/asset_taxonomy/musical_instruments_v0/musical_instrument_asset_taxonomy_v0.json
```

Validate it with:

```bash
python3 scripts/validate_musical_instrument_taxonomy_v0.py
```

## What This Lane Does

- names instrument families and starter instruments
- breaks each instrument into visible anatomy
- records source links and what each source supports
- maps anatomy to geometry dictionary terms
- maps likely build steps to legal Blender tool IDs
- defines drawing UI tags and source fields needed later
- adds in-game book hooks so readable objects can teach craft vocabulary

## Starter Instruments

- lute
- Gothic harp
- recorder
- shawm
- frame drum
- cast bell
- portative organ
- hurdy-gurdy

These were chosen because they cover reusable modeling mechanics: hollow bodies,
ribbed shells, string arrays, tapered bores, tone-hole booleans, membrane hoops,
revolved metal shells, bellows, keys, crank/wheel assemblies, and repeated small
hardware.

## Documents

- `instrument_source_index_v0.md` lists source links and what they are used for.
- `instrument_family_build_plans_v0.md` maps instruments to modeling sequences.
- `instrument_lore_book_hooks_v0.md` captures player-facing book/detail hooks.
- `operator_instrument_handoff_v0.md` defines what the future drafting/manual UI
  should collect before Blender work.
- `music_theory_and_playing_source_index_v0.md` records theory and playing
  method source anchors.
- `music_theory_and_playing_method_research_v0.md` maps mode, rhythm, melody,
  harmony, notation, and playing actions into game-asset, animation, sound, and
  lore planning.
- `operator_music_theory_handoff_v0.md` defines future fields for playable
  motion, notation pages, sound hooks, and music-readable world details.

## Boundary

This is game-asset planning and lore documentation only. It is not acoustic
engineering, instrument-making instruction, formal music instruction,
performance coaching, conservation guidance, historical authenticity proof, or
playable-audio implementation.
