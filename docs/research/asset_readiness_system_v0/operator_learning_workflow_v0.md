# Operator Learning Workflow V0

The fastest useful workflow is not "learn all of Blender first." The fastest
workflow is to learn the exact Blender terms needed for the asset in front of
you, then write those terms back into the repo.

## Roles

Codex prepares:

- reference packets
- vocabulary
- drawing guides
- component breakdowns
- Blender tool cards
- source recipes and style sheets
- validation checklists

The operator decides:

- whether the silhouette feels right
- which detail is worth keeping
- which reference detail matters most
- when a bevel, cut, lip, taper, or material reads correctly
- when the asset is ready to archive or promote

## The Learning Loop

Use this loop for each asset:

```text
look at reference
-> name anatomy
-> draw construction
-> choose Blender tools
-> model one pass
-> name what is wrong
-> adjust
-> record the correction
```

Every correction should become one of these:

- a new anatomy term
- a better drawing-guide rule
- a better Blender tool-card note
- a recipe edit knob
- a style-sheet ledger entry
- a validation rule

## Useful Question Format

When something looks wrong, describe it in this order:

```text
part -> visual problem -> desired correction -> strength
```

Examples:

```text
shaft -> too straight -> add entasis belly near lower third -> subtle
cap lip -> too thin -> increase lower bead projection -> medium
panel recess -> too flat -> deepen shadow cut -> strong
rail grip -> too square -> round top arrises -> subtle
```

## What Codex Should Hand Over

Before the operator starts, Codex should provide:

- the exact asset ID
- the primary reference
- a compact anatomy list
- a drawing guide
- the Blender tool sequence
- scale/origin/socket notes
- material and UV notes
- a QA checklist
- a list of details intentionally deferred

## What The Operator Should Give Back

After the Blender pass, the operator should give back:

- screenshots from front, side, top, and gameplay angle
- what feels wrong
- which parts should be thicker, thinner, deeper, smoother, sharper, or simpler
- any new terms learned
- whether the asset should be archived, refined, or promoted

