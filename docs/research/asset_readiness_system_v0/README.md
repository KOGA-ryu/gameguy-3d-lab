# Asset Readiness System V0

This folder documents the prep layer between broad asset-family research and
hands-on Blender work.

The repo already knows the larger direction:

```text
source recipe -> compiler/pump -> deterministic JSON -> Blender adapter
```

This lane answers a more practical question:

```text
what must be prepared before the operator opens Blender?
```

## Working Model

The user is the final asset operator. Codex prepares the reference packet,
terminology, drawing guide, Blender tool notes, style ledger, and QA checklist.
The operator makes the final visual calls in Blender. Corrections from that
session are then recorded back into docs, style sheets, or source recipes.

The intended loop is:

```text
asset family
-> exact component
-> reference packet
-> drawing guide
-> component/style terminology
-> Blender tool workcard
-> source recipe or style sheet
-> operator Blender pass
-> correction log
-> better recipe/tool plan
```

## Documents

- `asset_readiness_todo_list_v0.md` is the main prep checklist.
- `operator_learning_workflow_v0.md` explains how the user learns Blender terms
  while still moving assets forward.
- `blender_tool_fillout_queue_v0.md` names the Blender tools that need practical
  tool cards.
- `blender_tool_cards/` contains the first practical cards for base-form,
  assembly, refinement, UV/material, and game-proxy tools.
- `reference_and_drawing_guide_queue_v0.md` defines how reference images and
  construction drawings should be collected and converted into build guides.
- `modular_game_asset_requirements_v0.md` lists the non-visual requirements for
  usable game assets.
- `asset_qa_checklist_v0.md` is the final asset quality checklist.
- `per_asset_workcard_template_v0.md` is the fill-in template for one asset.

## Boundaries

This lane does not create mesh, run Blender, fetch images, or claim building-code
compliance. It defines what needs to be known before those tasks are worth doing.

Reference images remain morphology references unless a later source packet states
license, provenance, and allowed use. Building-code compliance needs a separate
jurisdiction-specific reference lane.
