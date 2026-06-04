"""
Example parametric recipes.

This is where human-readable architectural choices become typed build ops.
For now, the Doric recipe is manual and deterministic. Later, the ASCII/image
reference parser can compile into the same ops.
"""

from __future__ import annotations

from .ops import AddBox, AddCylinder, AddRing, CutFlutes, BuildOp


def doric_column_plan(
    height: float = 72.0,
    shaft_radius: float = 5.0,
    flute_count: int = 20,
) -> list[BuildOp]:
    """
    Create a compact Doric column build plan.

    This is not trying to be a perfect historical order yet. It is a clean
    test article for the pipeline:
    recipe -> ASCII previews -> validation -> Blender script.

    Parts:
    - stepped square plinth
    - small base rings, even though strict Greek Doric often lacks a base
      in temple use. Kept here because game/fantasy columns often need a
      readable ground transition.
    - tapered/entasis shaft
    - radial flute cuts
    - necking ring
    - echinus as a broad round cushion
    - square abacus
    """
    base_z = 0.0
    plinth_lower_h = 2.0
    plinth_upper_h = 2.0
    torus_lower_h = 1.0
    shaft_h = height * 0.70
    neck_h = 1.2
    echinus_h = 4.0
    abacus_h = 3.0

    z = base_z
    ops: list[BuildOp] = []

    ops.append(AddBox("plinth.lower_step", width=18, depth=18, height=plinth_lower_h, z=z + plinth_lower_h / 2))
    z += plinth_lower_h

    ops.append(AddBox("plinth.upper_step", width=15.5, depth=15.5, height=plinth_upper_h, z=z + plinth_upper_h / 2))
    z += plinth_upper_h

    ops.append(AddRing("base.lower_round", radius=shaft_radius + 1.2, tube_height=torus_lower_h, z=z + torus_lower_h / 2, overhang=0.4))
    z += torus_lower_h

    shaft_start_z = z
    ops.append(AddCylinder(
        "shaft.tapered_fluted_core",
        radius=shaft_radius,
        taper_top_radius=shaft_radius * 0.86,
        height=shaft_h,
        z=z + shaft_h / 2,
        vertices=128,
        entasis=True,
    ))
    ops.append(CutFlutes(
        "shaft.tapered_fluted_core",
        count=flute_count,
        depth=0.45,
        width_ratio=0.34,
        start_z=shaft_start_z + 1.5,
        end_z=shaft_start_z + shaft_h - 1.5,
    ))
    z += shaft_h

    ops.append(AddRing("capital.necking_ring", radius=shaft_radius * 1.02, tube_height=neck_h, z=z + neck_h / 2, overhang=0.15))
    z += neck_h

    ops.append(AddRing("capital.echinus_cushion", radius=shaft_radius * 1.35, tube_height=echinus_h, z=z + echinus_h / 2, overhang=0.8))
    z += echinus_h

    ops.append(AddBox("capital.abacus_square_slab", width=16.5, depth=16.5, height=abacus_h, z=z + abacus_h / 2))
    z += abacus_h

    ops.append(AddBox("entablature.test_block", width=22, depth=18, height=5, z=z + 2.5, material="limestone"))
    return ops
