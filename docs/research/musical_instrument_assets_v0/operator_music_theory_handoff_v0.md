# Operator Music Theory Handoff V0

This handoff defines what future UI/manual workcards should capture when an
instrument prop, readable music page, sound cue, or performance animation needs
music-theory context.

## Required Fields

```text
music_asset_id
reference_packet_id
instrument_id_optional
world_style_id
music_role
theory_terms
playing_method
visible_sound_source
performer_pose
notation_type_optional
rhythm_pattern_optional
mode_or_scale_optional
animation_cues
audio_hook_optional
operator_checks
```

## Music Role Labels

Use these labels before inventing new ones:

- `ritual_chant`
- `procession_signal`
- `dance_tune`
- `tavern_song`
- `court_piece`
- `work_rhythm`
- `warning_signal`
- `mourning_toll`
- `market_call`
- `teaching_page`
- `repair_note`
- `ambient_set_dressing`

## Theory Fields

| Field | Purpose |
| --- | --- |
| `mode_or_scale_label` | Gives the music its tonal color or lore name. |
| `drone_pitch` | Supports chant, hurdy-gurdy, organ, and ritual ambience. |
| `meter_label` | Ties motion/animation to pulse. |
| `accent_pattern` | Helps drums, bells, steps, and dances feel intentional. |
| `phrase_count` | Lets a loop have musical structure instead of random motion. |
| `texture_label` | Separates solo, drone, chordal, and polyphonic contexts. |
| `notation_type` | Staff, chant-like page, tablature, rhythm grid, bell schedule, or fingering chart. |
| `ensemble_parts` | Defines how many visible performers or prop parts are needed. |

## Playing Fields

| Field | Purpose |
| --- | --- |
| `sound_action` | Pluck, bow, blow, strike, ring, crank, key press, or sing. |
| `hand_pose_map` | Where each hand goes and what it controls. |
| `mouth_contact_optional` | For winds and voice-like cues. |
| `moving_parts` | Strings, keys, bellows, wheel, crank, clapper, beater, or fingers. |
| `sound_source_part` | The part that visibly produces the sound. |
| `anchor_points` | String, pipe, hole, bell, membrane, or key anchors. |
| `performance_loop_beats` | Keeps animation and audio aligned. |
| `low_compute_fallback` | What visual fact remains if detailed motion/audio is disabled. |

## Common Workcard Sentences

```text
This lute prop uses court_piece role, tablature notation, six courses, right-hand
finger plucking, left-hand fretting, and a two-phrase loop.
```

```text
This bell uses warning_signal role, toll pattern 3+1, visible clapper, rope
pull, and a slow loop tied to the gatehouse watch schedule.
```

```text
This recorder page is a teaching_page role with fingering chart notation,
front-hole map, thumbhole note, and a small consort-size diagram.
```

```text
This hurdy-gurdy animation uses dance_tune role, drone texture, crank loop,
key presses, visible wheel contact zone, and melody/drone string separation.
```

## Operator Checks

- Does the visible motion match the instrument's sound action?
- Are hands, mouth, beater, crank, keys, or clapper placed on real functional
  parts?
- Does notation match the prop type instead of being generic sheet decoration?
- Does the instrument have enough anchors to explain strings, holes, pipes,
  membranes, or bells?
- Can the player learn a world clue from the musical detail?
- Is there a low-compute version that keeps the important read?

## Avoid

- random finger motion unrelated to holes, strings, keys, or frets
- music pages that do not match the instrument
- treating every instrument as a generic held prop
- adding audio complexity before the visible sound source is readable
- using theory terms as decoration without a world role
