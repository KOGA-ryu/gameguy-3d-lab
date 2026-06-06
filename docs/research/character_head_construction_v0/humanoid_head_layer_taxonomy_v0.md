# Humanoid Head Layer Taxonomy v0

This note turns the head discussion into a source-side build language. The goal is not a finished face sculpt yet. The goal is a stable vocabulary for describing a mannequin head as ordered contours, planes, ridges, sockets, wedges, valleys, bevels, and chamfers before a Blender adapter ever runs.

Machine-readable source:

`data/characters/head_construction/humanoid_head_layer_taxonomy_v0.json`

Validation:

```bash
python3 scripts/validate_humanoid_head_layer_taxonomy_v0.py
```

## Core Rule

Build largest forms first, then defining forms, then detail:

```text
skull envelope
-> face mask planes
-> brow / eye socket band
-> nose wedge
-> cheek / midface planes
-> mouth / lip relief
-> chin / jaw mass
-> optional ear side anchors
-> final bevel/chamfer/normal pass
```

The script should not try to "make a face" directly. It should apply named operations to named contours.

## Measurement Anchors

The v0 source profile uses NIOSH/Anthrotech head-and-face survey values as a measured seed. These are not artistic rules. They are proportional anchors.

| Field | Use | v0 value |
|---|---|---:|
| `head_length` | skull front/back depth | `0.1973 m` |
| `head_breadth` | skull side width | `0.1530 m` |
| `bizygomatic_breadth` | cheekbone width | `0.1435 m` |
| `bigonial_breadth` | jaw width | `0.1204 m` |
| `minimum_frontal_breadth` | forehead width | `0.1059 m` |
| `interpupillary_distance` | eye socket centers | `0.0647 m` |
| `menton_sellion_length` | face height frame | `0.1227 m` |
| `subnasale_sellion_length` | nose vertical frame | `0.0520 m` |
| `nose_breadth` | nose base width | `0.0364 m` |
| `nose_protrusion` | nose forward depth | `0.0211 m` |
| `lip_length` | mouth crease width | `0.0514 m` |

These fields define where the head features start. Style knobs decide how faceted, soft, severe, cute, old, noble, monstrous, or mannequin-like the final result becomes.

## Shape Terms

`envelope`

The biggest readable volume. For the head this is the cranium plus back skull. Blender mapping: `mesh_from_pydata`, `bridge_edge_loops`, `modifier_bevel`, `modifier_weighted_normal`.

`plane`

A broad directed surface. Forehead, central face, lower face, cheek, jaw side, and skull side are planes. Blender mapping: `extrude_faces`, `shade_flat`, `modifier_weighted_normal`.

`plane_break`

A controlled angle change between planes. This is how low-poly anatomy reads without many vertices. Blender mapping: `loopcut_slide`, `mark_sharp`, `modifier_bevel`.

`ridge`

A raised band or line. Brow ridge, cheekbone, lip hint, and chin relief can all be ridges. Blender mapping: `relief_stack`, `extrude_faces`, `modifier_bevel`.

`socket`

A recessed enclosed area with a rim. Eye sockets are the first important use. Blender mapping: `inset_faces`, inward `extrude_faces`, optional `modifier_boolean`, rim bevel.

`wedge`

A protruding tapered form. The nose is the important first wedge. Blender mapping: `extrude_faces`, `scale_profile`, `modifier_bevel`.

`valley`

A narrow recessed line. Mouth crease and under-lip shadow are valleys. Blender mapping: `knife_project`, `inset_faces`, inward `extrude_faces`, `sculpt_crease`.

`relief`

Small raised surface detail. Lip hints, ear shell hints, and stylized cheek/lower-face marks are relief. Blender mapping: `mesh_from_pydata`, `extrude_faces`, `modifier_bevel`.

`chamfer`

A straight angled edge transition. This is the right word for many low-poly face cuts. Blender mapping: bevel with one segment.

`bevel`

A softened edge transition. Use it lightly on socket rims, nose tip, skull envelope, lips, and cheek planes.

## Layer Detail

### 1. Skull Envelope

Use `head_length`, `head_breadth`, and head silhouette/profile contours. This layer produces the head shell and neck socket. It should still read as a head even if all facial features are hidden.

Main operations: `loft_sections`, `scale_profile`, `bevel_edges`.

### 2. Face Mask Planes

Place the forehead, central face, and lower-face planes onto the skull envelope. This is where the head stops being a ball and starts becoming a face.

Main operations: `extrude`, `profile_operation_stack`, `bevel_edges`.

### 3. Brow / Eye Band

Raise the brow ridge and recess the eye sockets. This is the first defining facial layer. If this layer works, the face reads before the nose or mouth exists.

Main operations: `relief_stack`, `offset_profile`, `boolean_cut`, `bevel_edges`.

### 4. Nose Wedge

Extrude a central wedge from sellion to subnasale. Tie nose width and protrusion to measured fields, then let style knobs exaggerate or soften.

Main operations: `extrude`, `scale_profile`, `bevel_edges`.

### 5. Cheek / Midface Planes

Raise cheekbone planes from the measured cheek width and slope them toward the mouth and side face. This stops the head from becoming a flat mask with a nose glued on.

Main operations: `relief_stack`, `profile_operation_stack`, `bevel_edges`.

### 6. Mouth / Lip Zone

Keep this subtle for v0. The mouth is a valley crease plus tiny upper/lower lip relief, not a full expression rig.

Main operations: `boolean_cut`, `offset_profile`, `relief_stack`, `bevel_edges`.

### 7. Chin / Jaw Mass

Push the chin and chamfer the jaw into the side face. This anchors the lower profile and makes the head connect believably to the neck socket.

Main operations: `extrude`, `profile_operation_stack`, `bevel_edges`.

### 8. Ear Side Anchors

Optional for low-detail heads. These can be shallow sockets or small raised shells. They mainly provide future attachment references for hair, helmets, masks, and earrings.

Main operations: `offset_profile`, `relief_stack`, `bevel_edges`, `mirror_axis`.

### 9. Final Edge Language

Apply bevels, chamfers, hard edges, soft edges, and weighted normals after the forms are placed. This pass decides the surface language.

Harder edges:

- brow underside
- jawline plane break
- nose side chamfers
- cheek to side-face transition

Softer edges:

- skull envelope
- socket rims
- lip relief
- nose tip
- chin transition

## Useful Correction Language

The operator should be able to say:

```text
make the brow heavier
deepen the eye sockets
push the nose tip forward
soften the cheek bevel
widen the jaw
round the back skull
make the mouth crease shallower
make the face less flat from side view
```

Each correction maps to a source field, not a vague Blender edit.

## Compiler Direction

The future compiler should consume:

```text
head measurement profile
front silhouette contour
side profile contour
feature contours
construction layer stack
style knobs
```

And emit:

```text
deterministic humanoid_head_geometry_v0 JSON
```

The Blender script should only consume that JSON and execute the tool plan. If the Blender adapter has facial design decisions inside it, those decisions belong in this taxonomy or in a future source recipe.
