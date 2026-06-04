# Operator Fabrication Handoff V0

The future UI should produce two outputs at once:

```text
rough shape source
operator fabrication plan
```

This doc defines the craft-informed fields the UI/workcard should include.

## Required Workcard Fields

```text
asset_id:
asset_family:
component:
material_craft:
fabrication_method_ids:
primary_reference:
construction_drawing:
selected_visible_lines:
omitted_construction_lines:
template_profiles:
real_tool_vocabulary:
source_fields_needed:
Blender_tool_sequence:
manual_operator_checks:
deferred_details:
non_claims:
```

## Drawing Tags

The UI should support these tags because they map to real fabrication logic:

```text
construction_line
selected_line
omitted_line
center_point
arc
circle
template
profile
waste
dressed_face
arris
chamfer
groove
tool_mark
springline
intrados
extrados
voussoir
keystone
rib_path
boss
web_cell
stile
rail
mortise
tenon
groove
side_profile
bead
cove
round
bar_path
scroll
collar
rivet
join_point
relief_region
chased_line
raised_boss
```

## Tool Vocabulary The Operator Should Learn First

Stone:

- tracing floor
- template
- dressed face
- arris
- point chisel
- claw chisel
- flat chisel
- springline
- voussoir
- keystone
- rib
- web
- boss

Wood:

- stile
- rail
- mortise
- tenon
- shoulder
- groove
- rabbet/rebate
- moulding profile
- bead
- cove
- round

Iron/metal:

- bar stock
- scroll
- bend radius
- collar
- rivet
- forge weld
- punched hole
- chased line
- repoussé
- raised boss

## What The UI Should Tell The Operator

For each selected drawing piece:

```text
You drew: selected arch line
Craft meaning: tracery bar / arch template
Blender tools: mesh_from_pydata -> modifier_boolean -> modifier_bevel
Manual judgment: adjust cusp tightness and bevel width
Do not worry yet: exact stone weathering
```

For each asset:

```text
Real craft model:
  stone post dressed from block, then sockets, panels, and bevels

Blender sequence:
  block -> panel inset -> socket cutters -> bevels -> weighted normals

Manual edit focus:
  silhouette, socket fit, bevel survival, face readability
```

## Non-Claims

These fields are still for game asset planning. They do not make the output:

- structurally sound
- code compliant
- fabrication ready
- historically exact
- safe to manufacture
- conservation guidance

