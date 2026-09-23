"""pier_crib — the timber crib piers of the 1834 Chicago harbour works.

A pier of this decade is a row of log cribs: rectangular boxes of notched timber,
built on the ice or on a scow, floated into place, sunk, and filled with stone and
gravel until they sat on the bed and stayed there. The deck is the top of the box.
There is no frame, no truss and no pile bent in this archetype — a crib pier is
masonry made of trees.

## What it shares with the bridge, and why that is on purpose

The crib boxes are built by the same `hewn_log_wall` that builds the cabins and the
bridge's abutments. That is not code reuse for its own sake: a crib corner and a
cabin corner are the same joint, cut by the same men in the same decade, and they
should read as the same joint from across the water. What differs is scale and
finish — the courses are coarser, the relief is shallower, and the seam between
courses takes the grey stone-and-gravel material rather than the pale clay-and-lime
that chinks a dwelling. Nobody chinked a crib; what shows between its logs is what
was poured into it.

## The deck is the top of the box, and nothing else is built

A pier certainly carried more than its own top surface — bollards, a capstan, spiles,
lamps later on, the working clutter of a harbour under construction. None of it is
attested for July 1835 and none of it is built. The top face of the crib IS the deck
in this archetype, which is both what a crib pier actually looks like and the only
reading that invents nothing: `deck_height_m` puts the crib top at the height the
dossier gives above the water, and there is no separate plank, rail or fitting.

## Local origin: z = 0 is the water, and y may be negative

docs/GLB-CONTRACT.md pins a structure's origin to the base of its walls, which a
pier does not have; like `bridge_timber` this archetype anchors z = 0 at the design
water surface and declares `VERTICAL_ANCHOR = "water"` so the renderer places it
against the water plane instead of sampling a riverbed.

In plan the origin is the footprint polygon's own (0, 0), as the contract requires —
and for a pier that point sits on the MEASURED inner face rather than on a corner of
the mesh. The body is built from `v0_m` to `v0_m + width_m`, which is a negative
range for a pier whose crib lies on the far side of the line that was read off the
survey. See `pier_crib_params.PierCribParams`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.logwork import COURSE_M, HEWN_RGBA, hewn_log_wall  # noqa: E402
from common import materials  # noqa: E402
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.pier_crib_params import PierCribParams  # noqa: E402

M_LOG, M_FILL = 0, 1

# How far below the waterline the crib mesh runs before it stops. The cribs really
# reached the bed — twelve feet of water at the north pier's head, by Andreas — and
# there is no point modelling what the water hides, in a project that models no
# riverbed and whose renderer puts its water plane at z = 0 in this local frame.
# Deeper than the bridge's 0.55 m because a pier stands in open lake and a low sea
# would otherwise show daylight under it.
SUBMERGED_M = 0.95

# River stone and gravel packed between the crib logs, the same grey the bridge's
# crib fill takes. Defined here rather than imported from bridge_timber: an archetype
# that imported another archetype would have a mesh whose inputs hash cannot see the
# module it depends on (generators/mesh_inputs.py hashes one archetype file), so the
# duplication is load-bearing.
FILL_RGBA = (0.300, 0.295, 0.270, 1.0)


def build(params: PierCribParams, name: str):
    """Build the pier. Returns a Blender object at the local origin; z = 0 is the
    water surface, y-up is handled by the exporter."""
    params.validate()
    b = MeshBuilder(name)

    # Least-confident wins, over the attributes that say what this thing WAS. For a
    # pier that set is unusually large, and the reason is the same one
    # bridge_timber_params argues for a bridge: the whole of what anybody says about
    # a pier is dimensional. A length, a width and a height above the water ARE the
    # description, so all three sit in the character set — and since the width of
    # both piers in this dataset is conjectural, both render as massing. That is
    # correct rather than unfortunate.
    conf = params.worst_conf("construction", "length_m", "width_m", "deck_height_m")

    y0 = params.v0_m
    y1 = y0 + params.width_m
    for x0, x1 in params.crib_x:
        _crib(b, x0, y0, x1, y1, params.deck_height_m, conf)

    mats = [
        # The sheet's hewn-log roughness (0.92); see bridge_timber for the crib note.
        simple_material("log", HEWN_RGBA,
                        roughness=materials.SUBSTRATES["hewn_log"].roughness),
        simple_material("fill", FILL_RGBA, roughness=0.98),
    ]
    return b.to_object(mats)


def _crib(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
          top_z: float, conf: float) -> None:
    """One crib box: courses of logs laid up in alternating directions, notched ends
    protruding at the corners, filled to the top.

    A coarser course than a cabin's and a shallower relief, for the reason the
    bridge's cribs use the same treatment: crib timbers were heavier than wall logs
    and nothing between them was meant to be seen from a parlour.
    """
    hewn_log_wall(b, x0, y0, x1, y1, -SUBMERGED_M, top_z, conf, M_LOG, M_FILL,
                  skip=("bottom",), course=COURSE_M * 1.55, relief=0.014)
