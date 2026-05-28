# Terraced Terrain Full Notes v0

## 1. Source URLs

- https://github.com/lazysquirrellabs/TTG

## 2. What Documentation Was Read

- TTG README sections for features, usage, component/API mode, parameters, deterministic seeds, custom terrace heights, planar terrain, sculpt settings, and technical limitations.

## 3. Relevant Technical Concepts

- TTG generates planar and spherical terraced terrain meshes.
- Terrain can be deterministic by seed.
- Planar terrain has configurable side count, radius, maximum height, fragmentation depth, terrace heights, sculpt settings, and height distribution.
- Terraces are defined by relative heights in `[0, 1]`, sorted ascending, then scaled by maximum height.
- Sculpting uses noise-style parameters: base frequency, octave count, persistence, lacunarity, and height distribution curve.
- Custom terrace heights allow non-uniform steps.
- Generated terrain uses one submesh/material per terrace in Unity.

## 4. Relevant Data Fields / API Fields / Formulas

### Core Parameters

```text
fragmentation_depth: detail level; more fragmentation creates more triangles/vertices
relative_terrace_heights: float[] sorted in [0, 1]
terrace_count: derived from relative heights if custom heights are used
maximum_height: terrain vertical range
height_distribution: curve from (0,0) to (1,1)
seed: int for reproducible generation
```

### Sculpt Settings

```text
base_frequency: > 0
octaves: > 0
persistence: 0 < value < 1
lacunarity: > 1
height_distribution: curve, null means linear/canonical
```

### Planar Terrain Parameters

```text
sides: int, 3..10
radius: > 0
maximum_height: > 0
relative_terrace_heights: sorted float[]
sculpt_settings
fragmentation_depth
```

### API Names From TTG

```text
PlanarTerrainGenerator(sides, radius, maximumHeight, relativeTerraceHeights, sculptSettings, depth)
SphericalTerrainGenerator(minHeight, maxHeight, relativeTerraceHeights, sculptSettings, depth)
SculptSettings(baseFrequency, octaves, persistence, lacunarity, heightDistribution)
SculptSettings(seed, baseFrequency, octaves, persistence, lacunarity, heightDistribution)
GenerateTerrain()
GenerateTerrainAsync(token)
PlanarTerrainGeneratorController
SphericalTerrainGeneratorController
```

### Terrace Formula For Our Compiler

```text
absolute_terrace_height[i] = min_z + relative_terrace_heights[i] * max_height

cell_height = nearest_or_bucketed_terrace(raw_height)
step_delta = abs(height_a - height_b)
edge_type = flat | step_up | step_down | ledge | cliff based on thresholds
```

## 5. Minimal v0 Subset For Our Engine

- Add optional `terrace_model` to terrain recipes:

```json
{
  "terrace_model": {
    "seed": 12345,
    "relative_heights": [0.0, 0.25, 0.5, 0.75, 1.0],
    "max_height_m": 8.0,
    "height_distribution": "linear",
    "classification_thresholds": {
      "flat_delta_max": 0.05,
      "step_delta_max": 1.0,
      "ledge_delta_min": 1.0,
      "cliff_delta_min": 2.0
    }
  }
}
```

- Generate height bands and edge classifications inside our own compiler.
- Use deterministic seed and parameter record.
- Treat TTG as concept reference, not a Unity dependency.

## 6. Direct Project Mapping

- `32x32x8 map cube`: `max_height_m` must fit inside `z=8` vertical budget or repo vertical step.
- `hex/elevation cells`: each cell gets `base_height`, `fold_offset`, `final_height`, and a terrace band.
- `terrain mesh compiler`: emits stepped top faces and riser side faces from terrace deltas.
- `visible face meshing`: terrace risers become visible faces where neighbor heights differ.
- `seam/fold grammar`: fold offsets can snap to terrace levels.
- `road/path layer`: roads should prefer flat/step bands and avoid cliff deltas.
- `building plot layer`: plot buildability uses terrace variance threshold.
- `asset placement layer`: ledge/cliff sockets can place stairs, ramps, walls, or railings.
- `Blender proof renderer`: render terrace bands with distinct materials only for proof; no Unity submesh dependency.
- `future AI affordance graph`: terrace deltas become movement costs/fall risks.

## 7. Deferred Parts

- Spherical terrains.
- Unity controllers and `MeshFilter`/`MeshRenderer` lifecycle.
- Async generation/cancellation.
- Native Unity collections.
- Per-terrace material submeshes as a requirement.
- TTG source code port.

## 8. Risks / Ambiguity

- TTG is Unity/C#; direct code should not be copied into the Blender/Python/Rust pipeline.
- Noise/fragmentation algorithms are not fully specified in the README; only parameters and concepts should be adopted.
- Terraces can create unwalkable discontinuities if movement thresholds are not tied to gameplay.
- Non-uniform terrace heights need clear validation: sorted, within `[0, 1]`, first/last can be 0/1.

## 9. Build Dex Implementation Notes

- Implement terrace snapping as a pure data transform over generated cell heights.
- Keep raw continuous height and final snapped height for auditability.
- Edge classification should be deterministic from neighbor final heights.
- Store seed and all parameters in receipts so terrain can be regenerated.

