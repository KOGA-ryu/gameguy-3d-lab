# Family Style Matrix V0

This matrix is a planning aid. It does not replace style sheets. It tells us
which style directions are worth building across asset families and which first
targets would prove the family.

## Gothic

Good fit:

- railings
- stairs
- windows
- doors
- trim/moulding
- ceilings/vaults
- walls

Core shapes:

- pointed arch
- clustered shaft
- rib path
- trefoil/quatrefoil/cinquefoil
- rosette
- buttress step
- blind tracery panel

First targets:

- `gothic_railing_post.blind_tracery_box_newel_v0`
- `gothic_lancet_window_frame_v0`
- `gothic_pointed_portal_surround_v0`
- `single_bay_rib_vault_blockout_v0`
- `stepped_buttress_wall_module_v0`

## Romanesque

Good fit:

- windows
- doors
- walls
- stairs
- trim/moulding

Core shapes:

- round arch
- thick wall reveal
- heavy pier
- simple block courses
- paired openings

First targets:

- `romanesque_round_arch_window_v0`
- `romanesque_round_portal_surround_v0`
- `heavy_pier_wall_bay_v0`
- `round_arcade_wall_panel_v0`

## Renaissance

Good fit:

- windows
- doors
- trim/moulding
- walls
- ceilings

Core shapes:

- rectangular order
- pediment
- pilaster
- cornice
- coffer
- proportional grids

First targets:

- `renaissance_rectangular_window_surround_v0`
- `raised_panel_door_ordered_frame_v0`
- `dentil_cornice_course_v0`
- `coffered_ceiling_panel_v0`

## Victorian

Good fit:

- railings
- stairs
- doors
- trim/moulding

Core shapes:

- turned baluster
- heavy handrail
- bead bands
- scroll bracket
- layered ogee profiles

First targets:

- `victorian_turning_baluster_v0`
- `victorian_newel_with_bead_bands_v0`
- `victorian_scroll_bracket_v0`
- `layered_ogee_trim_stack_v0`

## Art Nouveau

Good fit:

- railings
- stairs
- doors
- windows

Core shapes:

- flowing curve
- asymmetric infill
- plant-like stem
- elongated oval
- soft transition

First targets:

- `art_nouveau_curved_railing_infill_v0`
- `art_nouveau_stair_handrail_path_v0`
- `art_nouveau_door_panel_relief_v0`
- `art_nouveau_window_lattice_v0`

## Islamic Geometric

Good fit:

- windows
- ceilings/vaults
- walls
- trim/moulding
- railings

Core shapes:

- rosette
- star polygon
- construction cell
- girih-like strap
- repeated motif orbit
- selective omission

First targets:

- `geometric_lattice_window_panel_v0`
- `selected_cell_vault_web_v0`
- `muqarnas_cell_tier_proof_v0`
- `rosette_wall_panel_relief_v0`

## Modern

Good fit:

- railings
- stairs
- windows
- doors
- walls

Core shapes:

- rectangle
- slab
- simple reveal
- clean frame
- glass panel

First targets:

- `modern_clean_railing_run_v0`
- `modern_slab_stair_v0`
- `modern_large_pane_window_v0`
- `modern_flush_door_v0`
- `modern_wall_panel_grid_v0`

## Rustic

Good fit:

- railings
- stairs
- doors
- trim/moulding
- walls

Core shapes:

- thick rectangle
- rough cylinder
- chamfer
- uneven course
- displacement detail

First targets:

- `rustic_log_railing_v0`
- `rustic_timber_stair_v0`
- `rustic_plank_door_v0`
- `rough_block_wall_course_v0`

## Build Priority

The repo should build in this order:

1. clean component blockouts
2. profile and relief details
3. repeated modules
4. style-sheet to recipe compiler
5. Blender adapter previews
6. material and UV passes
7. map assembly

That keeps every style grounded in source-owned parts instead of loose Blender
experiments.
