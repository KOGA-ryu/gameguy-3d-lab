# Music Theory And Playing Method Research V0

This document maps music theory and playing methods into game-asset planning.

It answers:

```text
what musical idea does the player see?
what part of the instrument produces it?
what visible playing action supports it?
what source fields would a future asset, animation, lore book, or sound cue need?
```

## Boundary

This is not a music lesson, performance manual, acoustic engineering guide, or
historical authenticity proof. It is a research map for props, animations,
readable books, sound hooks, and worldbuilding.

## Theory Concepts That Matter For Assets

### Pitch, Register, And Range

Music concept:

```text
high/low pitch and the usable span of notes
```

Visible asset cues:

- longer strings or pipes imply lower pitch
- shorter strings or pipes imply higher pitch
- larger bells or drums imply lower/heavier sound
- small recorders, bells, and pipes imply higher sound
- fret, key, hole, and pin spacing suggests playable range

Source fields:

- `pitch_family`
- `lowest_note_label`
- `highest_note_label`
- `register_label`
- `string_length_series`
- `pipe_height_series`
- `hole_spacing_series`
- `bell_size_class`

Game use:

- small chime set versus tower bell
- recorder consort sizes
- organ pipe height series
- harp/lute string-length gradient
- readable music notes that explain why one object sounds high or low

### Scale, Mode, And Tonal Color

Music concept:

```text
the pitch collection that gives music its color or ritual/social identity
```

Repo use:

- `cathedral_gothic_v0`: chant/modal pages, organ drones, bell tones
- `village_vernacular_v0`: simple dance modes, pipe and drum loops
- `noble_interior_v0`: lute/harp court pieces, written notation, refined modes
- `wilderness_shrine_v0`: drone, chant, repeated small melodic cells
- `market_tavern_v0`: dance tunes, repeated phrases, drums, pipes

Source fields:

- `mode_label`
- `final_pitch`
- `reciting_tone_optional`
- `scale_degree_pattern`
- `drone_pitch`
- `cadence_pitch`
- `world_context`

Visible cues:

- mode names in readable books
- staff or tablature snippets
- drone strings on hurdy-gurdy
- organ pipe labels
- bell tone schedule

### Rhythm, Meter, Pulse, And Dance

Music concept:

```text
how time is divided, accented, repeated, or felt
```

Visible asset cues:

- drums, bells, clappers, and feet mark pulse
- dance scenes need repeated beat patterns
- work songs need steady labor rhythm
- ritual bells mark time or procession
- taverns need faster, social rhythmic loops

Source fields:

- `beat_unit`
- `meter_label`
- `accent_pattern`
- `loop_length_beats`
- `tempo_label`
- `drum_stroke_pattern`
- `bell_toll_pattern`
- `dance_step_pattern`

Game use:

- visible drum hand animation
- bell rope timing
- tavern dance loop
- marching/procession cadence
- readable rhythm notation in a music book

### Melody, Phrase, Cadence, And Form

Music concept:

```text
a tune moves through phrases and closes with recognizable arrival points
```

Visible asset cues:

- manuscript or songbook pages can show phrase marks
- players can gesture phrase starts/ends through breathing, bowing, plucking,
  drumming, or bell timing
- repeated forms explain looped tavern songs and ritual chants

Source fields:

- `melodic_contour`
- `phrase_count`
- `phrase_lengths_beats`
- `cadence_type_label`
- `repeat_scheme`
- `section_labels`
- `song_role`

Game use:

- readable books teaching "call and answer"
- bard/lute animation phrase loops
- chant diagrams
- horn call motifs
- tavern repetition maps

### Harmony, Drone, Counterpoint, And Texture

Music concept:

```text
how simultaneous sounds relate
```

Useful texture labels:

- `monophony`: one line, such as chant or solo pipe
- `drone_texture`: melody over sustained pitch
- `homophony`: melody plus chord/accompaniment
- `polyphony`: independent lines together
- `heterophony`: variants of the same line together

Visible asset cues:

- drone strings on hurdy-gurdy
- organ pipes grouped by register
- lute fingers showing multiple voices
- recorder consort sizes for polyphonic ensemble
- bells in tuned sets/chimes/carillon-like arrays

Source fields:

- `texture_label`
- `voice_count`
- `drone_pitch`
- `accompaniment_pattern`
- `independent_line_count`
- `ensemble_parts`
- `register_distribution`

Game use:

- choir/organ books
- lute tablature pages
- consort seating layouts
- bell chime diagrams
- lore explaining why instrument families come in sizes

### Notation, Tablature, And Memory

Music concept:

```text
how music is recorded, taught, remembered, or improvised
```

Useful notation families:

- staff notation
- neume/chant-like notation
- lute tablature
- drum pattern grid
- bell schedule/toll pattern
- fingering chart
- oral-memory cue list

Source fields:

- `notation_type`
- `clef_or_staff_label`
- `tablature_course_count`
- `finger_chart`
- `rhythm_grid`
- `performance_marks`
- `page_material`
- `scribe_quality`

Game use:

- readable songbooks
- choir pages
- tavern tune scraps
- bell-ringer schedules
- instrument teaching notes
- dungeon clue rhythms

## Playing Method Families

### Plucked Strings: Lute, Harp, Lyre-Like Props

Sound action:

```text
finger or plectrum plucks a string; pitch comes from string length/tension and
stopped or open string behavior
```

Visual playing cues:

- right hand plucks near soundboard or string field
- left hand stops strings/frets on neck for lute-like instruments
- harp hands hover over vertical/fan strings
- string courses or groups must remain visually aligned
- bridge, pegs, frets, and strings are all playable parts

Source fields:

- `string_count`
- `course_count`
- `open_string_pitches`
- `fret_positions`
- `plucking_hand_zone`
- `stopping_hand_zone`
- `bridge_anchor_points`
- `peg_anchor_points`
- `playing_posture`

Animation cues:

- pluck hand moves in short strokes
- fretting hand shifts along neck
- harp hands alternate or sweep small groups
- performance loop can be phrase-based rather than random finger motion

Asset checks:

- every visible string has two anchors
- fret/string spacing makes physical sense
- soundboard/rosette stays clear of the hand zone
- player pose does not clip through body or neck

Lore hooks:

- course count marks period/status
- rosette geometry can hide sacred pattern clues
- tuning pegs explain preparation before performance
- lute tab pages teach strings as lines/courses

### Bowed Strings: Future Rebec/Fiddle/Vielle Lane

Sound action:

```text
bow hair moves across strings while the other hand stops pitch
```

Visual playing cues:

- bow path crosses strings near bridge
- left hand is on neck/fingerboard
- bridge height and string arc matter
- instrument can be held at shoulder, chest, arm, or knee depending style

Source fields:

- `bow_path`
- `string_arc`
- `bridge_height_m`
- `fingerboard_length_m`
- `holding_pose`
- `bow_grip_pose`
- `left_hand_position_series`

Animation cues:

- bow has long directional strokes
- left hand shifts smaller distances
- phrase starts can align with bow direction changes

Asset checks:

- bow does not pass through body
- strings sit above bridge/fingerboard
- low-compute version keeps bow, bridge, strings, and body silhouette

Lore hooks:

- bow rosin, broken strings, and bridge setup make workshop scenes more legible
- music books can distinguish bowed dance tunes from plucked accompaniment

### Fipple And Flute-Like Winds: Recorder

Sound action:

```text
breath enters a windway/fipple; fingers open and close holes to change pitch
```

Visual playing cues:

- mouthpiece touches mouth
- hands cover front holes
- thumbhole matters as a back-side detail
- lower paired holes can signal hand orientation/size variant
- body sections/joint bands show instrument family

Source fields:

- `mouthpiece_position`
- `windway_slot`
- `labium_edge`
- `front_hole_positions`
- `thumbhole_position`
- `hand_pose_map`
- `joint_band_positions`
- `size_family`

Animation cues:

- finger lifts/closures happen on beat or phrase
- breath posture remains stable
- no huge body motion needed

Asset checks:

- holes are ordered along bore axis
- mouthpiece/window/labium remain visible
- hands align with holes, not arbitrary cylinder locations

Lore hooks:

- recorder consorts explain families of different sizes
- fingering charts can be readable wall/book details
- pastoral/tavern/noble scenes can use different recorder sizes

### Reed And Loud Outdoor Winds: Shawm

Sound action:

```text
air excites a reed; conical bore and flared bell project sound
```

Visual playing cues:

- reed/staple is distinct at mouth end
- bell flare dominates far end
- holes run along conical body
- hand pose must avoid covering the reed
- instrument reads louder/ceremonial than recorder

Source fields:

- `reed_length_m`
- `staple_length_m`
- `conical_bore_profile`
- `bell_flare_profile`
- `tone_hole_positions`
- `hand_pose_map`
- `performance_context`

Animation cues:

- breath posture is stronger than recorder
- fingers move over holes
- outdoor/processional performance can include walking stance

Asset checks:

- reed, hole order, and bell flare distinguish it from recorder
- bell is not just a cylinder cap
- hands do not hide the identifying reed

Lore hooks:

- shawm can signal procession, guards, festivals, and outdoor ceremony
- instrument manuals can warn that loud reeds belong outside halls

### Membrane Percussion: Frame Drum And Tension Drum

Sound action:

```text
hand, stick, or beater strikes a stretched membrane
```

Visual playing cues:

- membrane is separate from shell/hoop
- strike zones can be center, rim, or edge
- lacing/tacks/tension strings explain why membrane is taut
- jingles/bells add secondary sound cues if present

Source fields:

- `membrane_region`
- `rim_region`
- `strike_zone_center`
- `strike_zone_edge`
- `beater_optional`
- `tension_anchor_count`
- `lacing_paths`
- `jingle_positions`
- `rhythm_pattern`

Animation cues:

- hands or beater hit defined zones
- alternating strokes create readable rhythm
- tension drum can squeeze/pressure tension strings if needed later

Asset checks:

- membrane reads taut, not solid wood
- lacing connects real anchor points
- hand/beater impacts do not float off the surface

Lore hooks:

- drum patterns can encode warnings or dance steps
- tension strings and worn strike areas explain use
- market/tavern/procession rooms can use different drum patterns

### Struck Metal: Bells, Chimes, And Handbells

Sound action:

```text
metal vessel or bar is struck by clapper, mallet, hammer, or swinging motion
```

Visual playing cues:

- bell has mouth/lip/soundbow and hanging hardware
- clapper or striker path is clear
- ropes/levers/handles explain who rings it
- tuned sets need size/spacing order
- signal bells can be isolated; chimes appear in groups

Source fields:

- `bell_profile`
- `soundbow_region`
- `clapper_position`
- `striker_path`
- `hanging_hardware`
- `rope_or_handle`
- `bell_set_order`
- `toll_pattern`

Animation cues:

- tower bell: rope/lever moves, bell or clapper swings
- handbell: wrist/hand arc
- chime/carillon-like set: striker moves between bells

Asset checks:

- clapper or striker is visible when gameplay needs sound cause
- bell profile reads distinct from cup/vessel
- tuned sets change size logically

Lore hooks:

- bell schedules regulate daily life
- warning, worship, mourning, curfew, and market calls can be separate patterns
- bell inscriptions can name purpose, donor, or curse

### Keyboard And Wind: Portative Organ

Sound action:

```text
keys open air paths; bellows/wind supply feeds pipes
```

Visual playing cues:

- pipes are an ordered height/diameter series
- keys are a separate playable row
- bellows folds are visible and connected to wind chest
- one hand may operate keys while the other works bellows in small portable
  setups

Source fields:

- `pipe_count`
- `pipe_height_series`
- `pipe_diameter_series`
- `key_count`
- `key_positions`
- `bellows_fold_count`
- `bellows_motion_axis`
- `wind_chest_bounds`
- `playing_pose`

Animation cues:

- key press is small vertical motion
- bellows compress/expand rhythmically
- pipe sound can map to pipe groups/register labels

Asset checks:

- pipes, keys, wind chest, and bellows remain separate named parts
- bellows does not look like a plain box
- pipe rows follow pitch/register logic

Lore hooks:

- organ books can teach air, keys, and pipes as one system
- cathedral/noble scenes can use organ maintenance notes
- broken bellows are a readable quest/object clue

### Wheel-Driven Strings: Hurdy-Gurdy

Sound action:

```text
crank turns rosined wheel; wheel rubs strings; keys/tangents stop melody strings;
drone strings sound continuously
```

Visual playing cues:

- crank and wheel are the identity
- keybox and keys must be visible
- drone strings are separate from melody strings
- bridge and wheel contact zone explain sound production
- player has one hand on crank and one on keys

Source fields:

- `wheel_radius_m`
- `crank_path`
- `wheel_contact_zone`
- `melody_string_count`
- `drone_string_count`
- `key_count`
- `key_spacing_m`
- `tangent_contact_points`
- `bridge_positions`
- `playing_posture`

Animation cues:

- crank rotates continuously
- key hand presses short repeating keys
- wheel motion can drive drone/audio loop later

Asset checks:

- crank does not clip body
- wheel contact zone is visible
- drones and melody strings are distinguishable
- keybox is not swallowed by ornament

Lore hooks:

- drone strings explain continuous background tone
- crank rhythm can reveal dance or street performance
- repair notes can mention wheel rosin, loose tangents, or broken keys

### Voice, Chant, And Ensemble Context

Sound action:

```text
human voice or group performance shapes music without requiring a separate
instrument prop
```

Visible cues:

- chant books
- lecterns
- choir stalls
- conductor/leader position
- organ/choir relationship
- antiphonal seating or call-and-answer layout

Source fields:

- `voice_count`
- `chant_mode`
- `text_language`
- `book_stand_positions`
- `leader_position`
- `call_response_layout`
- `room_reverb_context`

Game use:

- cathedral ambience
- ritual rooms
- readable chant pages
- choir-stall placement
- secret melody clues in inscriptions

Asset checks:

- books and stands face performers
- space layout supports group singing
- music pages are not random decoration if they drive a clue

## Theory-To-World Style Map

| World Style | Music Theory Bias | Instrument/Playing Bias | Readable Detail |
| --- | --- | --- | --- |
| `cathedral_gothic_v0` | modes, chant, drone, organ texture, procession form | voice, portative organ, bells, recorder consort | chant book, bell schedule, pipe labels |
| `castle_fortress_v0` | signal rhythms, horn/bell calls, march pulse | bells, drums, shawms, horns later | guard call patterns, watch bells |
| `village_vernacular_v0` | simple dance meters, repeated phrases, call-and-response | frame drum, recorder, fiddle/rebec later, lute-like local variants | tavern tune scraps, dance step notes |
| `market_tavern_v0` | fast pulse, repeating sections, social forms | drums, recorders, lutes, bells | song sheets, price-board songs, drinking rounds |
| `noble_interior_v0` | refined modes, polyphony, written notation, court dances | lute, harp, organ, recorder | tablature, tuning notes, court dance books |
| `crypt_dungeon_v0` | sparse drone, bell tolls, chant fragments, ominous rhythm | bells, voice, frame drum, organ fragment | broken chant page, warning rhythm |
| `wilderness_shrine_v0` | drone, chant, small repeated motifs | voice, bell, simple pipe, drum | prayer bell note, pilgrim chant |
| `workshop_forge_v0` | work rhythm, repeated pulse, tool-sound texture | drums optional, bells, ambient work sounds | guild rhythm notes, bell work schedule |

## Future Machine-Readable Records To Promote

Good candidates:

- `modal_context_v0`
- `rhythm_pattern_v0`
- `instrument_playing_method_v0`
- `notation_page_v0`
- `instrument_animation_cue_v0`
- `sound_role_v0`
- `ensemble_layout_v0`
- `bell_signal_schedule_v0`
- `lute_tablature_prop_v0`
- `recorder_fingering_chart_prop_v0`
- `drum_pattern_prop_v0`
- `organ_pipe_register_map_v0`

Promote only when a real asset, animation, lore book, or sound feature needs the
data.
