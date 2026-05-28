# Contracts Ownership

Active contracts in this folder should support the 3D lab lanes:

- map and pathway authoring
- terrain and seam topology
- building and floor-plan assembly
- connector asset placement
- architecture measurements and shape dictionaries
- geometry or cube-volume recipe metadata
- workflow/factory records that are not tied to 2D-only output

Obvious 2D/mosaic-only contracts are quarantined under `quarantine_2d_mosaic_v0/`. They are kept for reference during the bootstrap cleanup, but they are not active contracts for this repo.

When adding a contract, keep it source-like, JSON-parseable, and explicit about non-claims. Do not add contracts for generated render, mesh, screenshot, or 2D Pattern Lab outputs.
