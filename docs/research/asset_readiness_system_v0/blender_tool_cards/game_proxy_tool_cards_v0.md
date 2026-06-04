# Game Proxy Tool Cards V0

Game proxy tools make the asset usable in a map, not just good in a preview.

## `create_collision_proxy`

Plain English:

Create a simplified helper mesh for gameplay collision.

Best used for:

- posts
- rails
- walls
- doors
- stairs
- columns
- cliffs
- interactable props

Avoid when:

- the asset is decorative-only
- ornate visual geometry is being used as collision by accident
- bounds are not settled

Key source fields:

```text
bounds_m
proxy_policy
collision_role
walkable_or_blocking
socket_clearance
```

How to use effectively:

- Match the gameplay shape, not every visual groove.
- Use boxes, cylinders, capsules, convex hulls, or compound proxies.
- Keep collision helpers hidden in final visual preview but present in reports.
- Validate that sockets and walkable spaces are not blocked by proxy mistakes.

Common mistakes:

- collision mesh too detailed
- collision mesh does not match visible silhouette enough for play
- rail or stair collision blocks intended movement
- decorative asset accidentally blocks the player

Architectural examples:

- simple box collision for a railing post
- capsule/cylinder for a column
- ramp or stair-step proxy for stairs
- wall bay blocker for line-of-sight

## `create_lod_variant`

Plain English:

Create a lower-detail version for distance or lower hardware.

Best used for:

- ornate railings
- tracery panels
- columns
- ruins
- windows
- wall modules
- repeated props

Avoid when:

- the base silhouette is not approved
- the asset is still a blockout
- small detail is doing gameplay work

Key source fields:

```text
source_object
lod_policy
target_triangle_budget
distance_m
hardware_tier
detail_removal_rules
```

How to use effectively:

- Preserve silhouette first.
- Remove tiny relief before removing structural shape.
- Disable decals and tiny cutters on low hardware.
- Use LOD1 for gameplay distance and LOD2 for far silhouette.
- Check that material roles survive simplification.

Common mistakes:

- decimating until the asset loses its identity
- keeping expensive decals on low hardware
- removing sockets or gameplay anchors
- creating LODs after the asset is already too dense to reason about

Architectural examples:

- railing panel with tracery simplified to broad arch shapes
- column that keeps the base/shaft/cap silhouette but drops tiny ribs
- window frame that keeps mullion rhythm but loses bead details
- ruin debris pile simplified to a few readable chunks

