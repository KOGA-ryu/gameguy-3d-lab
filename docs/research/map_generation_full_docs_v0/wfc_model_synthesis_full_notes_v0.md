# WFC / Model Synthesis Full Notes v0

## 1. Source URLs

- https://github.com/Henauxg/ghx_proc_gen
- https://docs.rs/ghx_proc_gen/latest/ghx_proc_gen/
- https://github.com/mxgmn/WaveFunctionCollapse

## 2. What Documentation Was Read

- `ghx_proc_gen` README and docs.rs crate page.
- `WaveFunctionCollapse` README sections on tile constraints, symmetries, higher dimensions, constrained synthesis, and algorithm lineage.

## 3. Relevant Technical Concepts

- Wave Function Collapse and model synthesis solve grid assignment problems from local constraints.
- A node/cell holds a set of possible states/models until observation/collapse chooses one.
- Constraints propagate to neighboring cells. If a state is impossible, it is removed from the neighbor domain.
- Contradiction occurs when a cell has zero possible states.
- `ghx_proc_gen` focuses on grid-based 2D and 3D generation, not only bitmap texture synthesis.
- `ghx_proc_gen` uses `Models`, `SocketCollection`, socket connections, `RulesBuilder`, `GridDefinition`, and `GeneratorBuilder`.
- WFC can work in higher dimensions, but performance and failure rates become more important.
- Symmetry/rotation systems reduce manual adjacency definitions.
- WFC can be constrained by initial values or manual edits.

## 4. Relevant Data Fields / API Fields / Formulas

### ghx_proc_gen Concepts

```text
Model:
  abstract state assigned to a grid node
  interpreted by caller as terrain tile, building module, facade bay, asset, etc.

Socket:
  edge/side compatibility label
  connections define which socket labels can face each other

SocketCollection:
  creates sockets
  add_connection(socket, compatible_sockets)
  add_constrained_rotated_connection(socket, allowed_relative_rotations, compatible_sockets)

ModelCollection<Cartesian2D | Cartesian3D>:
  creates model templates
  supports sockets per side

RulesBuilder:
  builds rules from model collection and sockets
  has Cartesian2D and Cartesian3D modes

CartesianGrid:
  2D/3D grid definition
  dimensions
  optional looping per axis

GeneratorBuilder:
  with_rules(rules)
  with_grid(grid)
  with_initial_nodes(position -> model)
  with_initial_grid(...)
  build()

Generator:
  generate_collected()
  select_and_propagate()
  set_and_propagate()
```

### 2D vs 3D

- Cartesian2D: grid has x/y neighbors; rotations around `Z+`.
- Cartesian3D: grid has x/y/z neighbors; default rotation axis `Y+` but can be customized.
- For our engine, 2D WFC can place terrain/building/facade patterns on a surface; 3D WFC can stack volumetric modules, but should be deferred.

### WFC / Simple Tiled Model Terms

```text
tile/state/model: possible value for a cell
domain/wave: set of possible states per cell
adjacency constraint: allowed pair of states in a direction
observation: pick one low-entropy cell and one state
propagation: remove incompatible states from neighbors
contradiction: any cell domain becomes empty
entropy heuristic: choose a cell with low uncertainty
backtracking/restart: recovery strategy after contradiction
symmetry: generate rotated/reflected variants and adjacency rules
```

### Socket / Edge Compatibility Logic

For our module recipes:

```json
{
  "model_id": "stone_wall_straight_v0",
  "weight": 1.0,
  "sockets": {
    "north": "wall_continue",
    "east": "wall_end",
    "south": "wall_continue",
    "west": "wall_end",
    "upper": "empty",
    "lower": "foundation"
  },
  "semantic_tags": ["wall", "blocking", "cover"]
}
```

Compatibility table:

```json
{
  "wall_continue": ["wall_continue", "wall_corner"],
  "wall_end": ["empty", "doorway"],
  "foundation": ["ground", "foundation"],
  "empty": ["empty", "wall_end"]
}
```

Hex adaptation: use six side names/direction indexes instead of Cartesian four sides. If adopting a WFC crate that assumes Cartesian grids, either use a wrapper graph solver or encode hex as a custom adjacency graph.

## 5. Minimal v0 Subset For Our Engine

Do not implement full WFC in v0. Implement the data shape for later:

```text
module_id
domain_tags
weight
sockets: direction -> socket_id
allowed_neighbors: socket_id -> socket_id[]
rotation_policy
initial_constraints
failure_policy
```

Use deterministic local compatibility checks first:

- Terrain edge compatibility.
- Building module connector compatibility.
- Facade bay left/right/top/bottom compatibility.
- Asset socket placement constraints.

## 6. Direct Project Mapping

- `32x32x8 map cube`: WFC domain can be cells in the cube, but full 3D assignment is deferred.
- `hex/elevation cells`: each hex cell can have candidate terrain states; constraints come from edge profiles.
- `terrain mesh compiler`: consumes resolved terrain states, not the WFC wave.
- `visible face meshing`: can use state labels for cliff/ledge/ramp visibility.
- `seam/fold grammar`: socket compatibility maps directly to edge profiles.
- `road/path layer`: initial constraints can force road cells before solving surrounding decoration.
- `building plot layer`: WFC can fill room/module grids inside plots later.
- `asset placement layer`: choose compatible assets for sockets after terrain/building base exists.
- `Blender proof renderer`: proof only final resolved module placements.
- `future AI affordance graph`: WFC state tags can seed affordance facts.

## 7. Deferred Parts

- Full entropy-based solver.
- Backtracking or modifying-in-blocks.
- 3D WFC for volumetric buildings.
- Non-Wang adjacency sets for complex global correlations.
- Learning constraints from examples.
- Integrating `ghx_proc_gen` directly; Rust dependency decision is separate.

## 8. Risks / Ambiguity

- Restart-on-contradiction can be expensive for large maps.
- Hex grids are not Cartesian; many WFC libraries assume square/voxel neighborhoods.
- Socket labels alone cannot enforce long-range structure such as rivers, roads, stairs, and loops.
- Too many states and rotations can make rules hard to debug.
- WFC output is only as good as rule coverage; missing constraints can produce legal but bad maps.

## 9. Build Dex Implementation Notes

- Start with a simple socket validator, not a generator.
- For each module candidate, validate six hex edge sockets plus optional `upper/lower` sockets.
- Add a deterministic repair pass before stochastic solving.
- Keep WFC data separate from terrain recipes so non-WFC generation remains possible.
- If later adopting `ghx_proc_gen`, model our module ids as `Models`, connector labels as `Socket`s, and use initial nodes for roads/plots.

