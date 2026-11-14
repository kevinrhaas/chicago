"""monument — a bronze group on a granite pedestal, in pure Python (T-3567).

See `monument_params` for the masses and the record for every reading. Like the K12, K16
and haystack archetypes this module writes its glTF itself with no Blender, and
`generators/monument_emit.py` calls `glb()` for each record; `generators/mesh_inputs.py`
hashes this file and that one into each asset's freshness record. It is not in
`generators/emit.py` for the reason `haystack.py` gives: registering an archetype there
re-stales every Blender mesh in the town.

## The pedestal

Granite masses, read off the Barnes-Crosby view (ICHi-19208, square-on from the 18th
Street walk) and J. W. Taylor's three-quarter view of 1893: the stage base, its top
washed in; the plinth with a projecting fillet; the die, carrying a bronze panel on each
face it is asked for; the cap, a cove out to a fillet and a wash in; then the cast bronze
rock. One granite material and one bronze one, and since T-3589 a pale one for what the
c. 1900 plate shows lighter than the granite: the weathered panels and the inscription cut
under the front one (the record's `lettering`): three draw calls.

## The group (Rohl-Smith, 1893)

Five figures, built as the sculptor posed them and no more finely than a visitor on the
walk 5-15 m off can read them: since T-3583 each body is one of the people rigs, posed to
its joints and baked to bronze by `monument_figures` (the owner's suggestion); before it,
each was joined from tapered limbs and balls. The pose is taken from the two photographs (`FIGURES` below, in pose units off the rock's centre,
x along the front to the right as the street sees it, y back from the front, z up). Since
T-3582 every joint is read on ICHi-19208 through its solved camera, so the front view
holds the plate joint for joint, and put in depth by where J. W. Taylor's 1893 camera sees
it across (the two are 15 degrees apart, so a depth is good to about 0.15 m and each is
held inside its figure's band on the rock). The group is scaled as a whole to the
record's `group_h_m` less the rock. From the left: the warrior in his long lunge, the
tomahawk raised; Margaret Helm, staggering back in her long skirt, her arm across to him;
Black Partridge behind her, his open hand raised against the blow, the musket slanting
past his hip; the post surgeon fallen under them, one leg stretched to the west edge; the
child kneeling at the right front, both arms out. The feathers, the tomahawk, the musket,
the cloak and Mrs. Helm's full skirt are still the members below (`monument_figures.PROPS`).
The sculpted faces, the dress's folds, the feathers' number and the panels' reliefs are
not modelled (the record's liberty says so);
the rear, which no photograph used here shows, is the same masses seen from behind.
"""

from __future__ import annotations

import json
import math
import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archetypes import monument_figures  # noqa: E402
from archetypes.monument_params import MonumentParams  # noqa: E402

GENERATOR = "chicago-4d generators/archetypes/monument.py (T-3567, T-3582, T-3583, T-3589)"

M_GRANITE, M_BRONZE, M_PALE = 0, 1, 2
# Name, linear base colour, roughness. The granite is the photographs' mid grey (the
# 1893 print shows it pale and fresh, the c. 1900 one a little darker); the bronze a dark
# brown patina, unpolished (no metal response: nothing in this renderer reflects).
# The pale one (T-3589) is the two things ICHi-19208 (c. 1900) draws lighter than the
# granite round them: the die's bronze panels, their relief weathered pale (0.71 of white
# on the plate against 0.46 for the plinth's face and about 0.3 for the die's own; the
# render cannot reach the plate's six-to-one over the die without an albedo past one, so
# it takes three to one), and the letters cut in the die under the front one. The plate is monochrome:
# the panels' faint green-grey is reconstructed (L-fort-dearborn-monument-3567). Taylor's
# 1893 print shows the same panels fresh and dark; the scene is 1904, so the c. 1900 plate
# sets the tone. One material for both keeps the monument at three draw calls.
MATERIALS = [
    ("monument_granite", (0.205, 0.200, 0.190, 1.0), 0.78),
    ("monument_bronze", (0.080, 0.066, 0.046, 1.0), 0.55),
    ("monument_pale", (0.600, 0.630, 0.580, 1.0), 0.85),
]

#: The inscription's lines as ICHi-19208 draws them under the front panel (T-3589), read
#: on the plate's 1200 x 931 px copy against the die's front (x 406.5-782.5, y 520-700):
#: (width, baseline, cap height), the width a fraction of the die's width and the heights
#: fractions of its height from its foot. Line 1 x 479-712, y 667.5-679.5; line 2, much
#: the smallest, x 575-617, y 682-686.5; line 3 x 525-664, y 689-695.5; each centred on
#: the die (its centre x 594.5, the lines' 594.5-596). The words are the record's
#: `lettering`, one line to each `/`; a line past these three takes the third's size
#: one line-gap lower.
LETTER_LINES = [(0.620, 0.114, 0.067), (0.114, 0.075, 0.025), (0.370, 0.025, 0.036)]
#: The cutter's strokes are bolder than the town's painted boards': about 1.3 grid units
#: wide on the plate against `prairie_draft`'s 0.9.
LETTER_STROKE = 1.3

#: Block capitals on a 4 x 6 grid, each a list of strokes (x0, y0, x1, y1), and the
#: advance in grid units: `prairie_draft.GLYPHS` (T-2399), copied rather than imported so
#: a change to the Prairie drafts does not re-stale this monument, with the comma added.
GLYPHS = {
    "A": ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 0), (0, 3, 4, 3)], 5.6),
    "B": ([(0, 0, 0, 6), (0, 6, 3, 6), (3, 6, 3, 3), (0, 3, 4, 3), (4, 3, 4, 0), (4, 0, 0, 0)], 5.6),
    "C": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0)], 5.6),
    "D": ([(0, 0, 0, 6), (0, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 1), (4, 1, 3, 0), (3, 0, 0, 0)], 5.6),
    "E": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (0, 3, 3, 3)], 5.6),
    "F": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 3, 3, 3)], 5.2),
    "G": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (4, 0, 4, 3), (4, 3, 2, 3)], 5.6),
    "H": ([(0, 0, 0, 6), (4, 0, 4, 6), (0, 3, 4, 3)], 5.6),
    "I": ([(0, 0, 0, 6)], 1.6),
    "J": ([(4, 6, 4, 0), (4, 0, 0, 0), (0, 0, 0, 2)], 5.6),
    "K": ([(0, 0, 0, 6), (0, 3, 4, 6), (1, 3.75, 4, 0)], 5.6),
    "L": ([(0, 0, 0, 6), (0, 0, 4, 0)], 5.2),
    "M": ([(0, 0, 0, 6), (0, 6, 2.5, 3), (2.5, 3, 5, 6), (5, 6, 5, 0)], 6.6),
    "N": ([(0, 0, 0, 6), (0, 6, 4, 0), (4, 0, 4, 6)], 5.6),
    "O": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0)], 5.6),
    "P": ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3)], 5.6),
    "Q": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0), (2.5, 1.5, 4.5, -0.5)], 5.6),
    "R": ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3), (1.5, 3, 4, 0)], 5.6),
    "S": ([(4, 6, 0, 6), (0, 6, 0, 3), (0, 3, 4, 3), (4, 3, 4, 0), (4, 0, 0, 0)], 5.6),
    "T": ([(0, 6, 4, 6), (2, 6, 2, 0)], 5.6),
    "U": ([(0, 6, 0, 0), (0, 0, 4, 0), (4, 0, 4, 6)], 5.6),
    "V": ([(0, 6, 2, 0), (2, 0, 4, 6)], 5.6),
    "W": ([(0, 6, 1.25, 0), (1.25, 0, 2.5, 4), (2.5, 4, 3.75, 0), (3.75, 0, 5, 6)], 6.6),
    "X": ([(0, 0, 4, 6), (0, 6, 4, 0)], 5.6),
    "Y": ([(0, 6, 2, 3), (4, 6, 2, 3), (2, 3, 2, 0)], 5.6),
    "Z": ([(0, 6, 4, 6), (4, 6, 0, 0), (0, 0, 4, 0)], 5.6),
    "0": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0)], 5.6),
    "1": ([(2, 0, 2, 6), (2, 6, 0.8, 4.8), (0.8, 0, 3.2, 0)], 5.2),
    "2": ([(0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3), (0, 3, 0, 0), (0, 0, 4, 0)], 5.6),
    "3": ([(0, 6, 4, 6), (4, 6, 4, 0), (4, 0, 0, 0), (1, 3, 4, 3)], 5.6),
    "4": ([(0, 6, 0, 3), (0, 3, 4, 3), (3, 6, 3, 0)], 5.6),
    "5": ([(4, 6, 0, 6), (0, 6, 0, 3), (0, 3, 4, 3), (4, 3, 4, 0), (4, 0, 0, 0)], 5.6),
    "6": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (4, 0, 4, 3), (4, 3, 0, 3)], 5.6),
    "7": ([(0, 6, 4, 6), (4, 6, 1.5, 0)], 5.6),
    "8": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0), (0, 3, 4, 3)], 5.6),
    "9": ([(4, 3, 0, 3), (0, 3, 0, 6), (0, 6, 4, 6), (4, 6, 4, 0), (4, 0, 0, 0)], 5.6),
    ".": ([(0, 0, 0, 0.01)], 1.8),
    "&": ([(4, 0, 0, 6), (0, 6, 2.5, 6), (2.5, 6, 2.5, 4), (2.5, 4, 0, 2), (0, 2, 0, 0), (0, 0, 3, 0)], 5.6),
    ",": ([(0.4, 0.6, 0, -0.8)], 1.8),
    " ": ([], 2.8),
}

LIMB_SIDES = 8
BALL_RINGS = 5

# The poses (T-3582), in the pose frame below, each joint read on both photographs that
# see the group and put in depth between them: ICHi-19208 square-on from the 18th Street
# walk (x and z, about 140 px to a pose unit at the group) and J. W. Taylor's 1893
# three-quarter view from the south-west (depth, through the 15 degrees between the two
# cameras: about 0.15 m, so each figure's depths are evened over its own joints). Each
# part: ("limb", a, b, ra, rb) a tapered round member; ("ball", c, r); ("ell", c, (rx, ry,
# rz)); ("cone", top, bottom, r_top, r_bottom).
FIGURES = {
    # The warrior, left: crouched in a long lunge to the left, his left leg stretched back
    # to the rock's west edge and his right knee bent forward, his body twisted to the woman
    # and his head down at Black Partridge's shoulder; the tomahawk raised over his head in
    # his right hand, its head below the grip; his left arm across to her shoulder; a
    # feather in his hair and a fringed ornament hanging at his left hip.
    "warrior": [
        ("ball", (-0.36, -0.28, 1.42), 0.085),
        ("limb", (-0.36, -0.28, 1.42), (-0.27, -0.28, 1.57), 0.022, 0.006),
        ("limb", (-0.52, -0.38, 1.25), (-0.36, -0.28, 1.42), 0.055, 0.05),
        ("limb", (-0.60, -0.10, 0.93), (-0.52, -0.38, 1.25), 0.13, 0.16),
        ("ball", (-0.60, -0.10, 0.93), 0.13),
        ("ell", (-0.59, -0.10, 0.88), (0.15, 0.13, 0.10)),
        ("limb", (-0.60, -0.10, 0.93), (-0.85, -0.10, 0.92), 0.035, 0.015),
        ("ball", (-0.62, -0.25, 1.31), 0.075),
        ("limb", (-0.62, -0.25, 1.31), (-0.71, -0.34, 1.60), 0.065, 0.05),
        ("ball", (-0.71, -0.34, 1.60), 0.05),
        ("limb", (-0.71, -0.34, 1.60), (-0.50, -0.03, 1.80), 0.05, 0.04),
        ("ball", (-0.50, -0.03, 1.80), 0.045),
        ("limb", (-0.53, -0.32, 1.82), (-0.39, 0.03, 1.62), 0.018, 0.016),
        ("ell", (-0.37, 0.03, 1.71), (0.07, 0.015, 0.045)),
        ("ball", (-0.44, -0.38, 1.19), 0.06999999999999999),
        ("limb", (-0.44, -0.38, 1.19), (-0.29, -0.47, 1.11), 0.06, 0.05),
        ("ball", (-0.29, -0.47, 1.11), 0.05),
        ("limb", (-0.29, -0.47, 1.11), (-0.12, -0.60, 1.07), 0.05, 0.04),
        ("ball", (-0.12, -0.60, 1.07), 0.045),
        ("limb", (-0.66, -0.05, 0.89), (-0.73, 0.30, 0.53), 0.095, 0.065),
        ("ball", (-0.73, 0.30, 0.53), 0.065),
        ("limb", (-0.73, 0.30, 0.53), (-0.86, 0.39, 0.17), 0.065, 0.045),
        ("limb", (-0.86, 0.39, 0.17), (-0.93, 0.36, 0.10), 0.045, 0.035),
        ("limb", (-0.53, -0.15, 0.87), (-0.44, -0.60, 0.44), 0.095, 0.065),
        ("ball", (-0.44, -0.60, 0.44), 0.065),
        ("limb", (-0.44, -0.60, 0.44), (-0.43, -0.11, 0.11), 0.065, 0.045),
        ("limb", (-0.43, -0.11, 0.11), (-0.49, -0.17, 0.05), 0.045, 0.035),
    ],
    # Margaret Helm, front centre: staggering back against Black Partridge, her right arm
    # reaching across to the warrior's waist, her left hand back at his chest, her hair in
    # a knot, her long dress falling in folds to the rock and a cloak hanging loose from her
    # right arm.
    "helm": [
        ("ball", (-0.01, -0.72, 1.31), 0.08),
        ("ball", (0.05, -0.66, 1.39), 0.05),
        ("limb", (0.03, -0.72, 1.14), (-0.01, -0.72, 1.31), 0.05, 0.045),
        ("limb", (0.03, -0.72, 0.85), (0.03, -0.72, 1.14), 0.11, 0.13),
        ("cone", (0.03, -0.72, 0.85), (0.06, -0.64, 0.06), 0.13, 0.33),
        ("limb", (-0.17, -0.64, 0.96), (-0.24, -0.59, 0.60), 0.04, 0.09),
        ("ball", (-0.24, -0.59, 0.60), 0.09),
        ("ball", (-0.06, -0.72, 1.11), 0.060000000000000005),
        ("limb", (-0.06, -0.72, 1.11), (-0.21, -0.64, 1.01), 0.05, 0.042),
        ("ball", (-0.21, -0.64, 1.01), 0.042),
        ("limb", (-0.21, -0.64, 1.01), (-0.45, -0.45, 0.98), 0.042, 0.033),
        ("ball", (0.11, -0.72, 1.13), 0.060000000000000005),
        ("limb", (0.11, -0.72, 1.13), (0.16, -0.62, 1.01), 0.05, 0.042),
        ("ball", (0.16, -0.62, 1.01), 0.042),
        ("limb", (0.16, -0.62, 1.01), (0.22, -0.52, 1.14), 0.042, 0.033),
    ],
    # Black Partridge, behind her to the right: his left arm raised high and out to the
    # upper left, the palm open against the blow; a feather standing from his headband and
    # a long one streaming back; his right arm round her; the musket slanting from behind
    # his left shoulder past his right hip; his legs striding to the right.
    "black_partridge": [
        ("ball", (0.27, -0.55, 1.63), 0.09),
        ("ball", (0.35, -0.50, 1.72), 0.055),
        ("limb", (0.37, -0.55, 1.74), (0.27, -0.55, 1.91), 0.035, 0.008),
        ("limb", (0.45, -0.45, 1.68), (0.62, -0.30, 1.55), 0.03, 0.022),
        ("limb", (0.62, -0.30, 1.55), (0.74, -0.20, 1.50), 0.022, 0.01),
        ("limb", (0.32, -0.53, 1.49), (0.27, -0.55, 1.63), 0.06, 0.055),
        ("limb", (0.42, -0.62, 0.93), (0.32, -0.53, 1.49), 0.15, 0.19),
        ("ball", (0.42, -0.62, 0.93), 0.15),
        ("cone", (0.42, -0.62, 0.93), (0.48, -0.55, 0.76), 0.16, 0.20),
        ("ball", (0.16, -0.46, 1.49), 0.08),
        ("limb", (0.16, -0.46, 1.49), (-0.09, -0.63, 1.57), 0.07, 0.055),
        ("ball", (-0.09, -0.63, 1.57), 0.055),
        ("limb", (-0.09, -0.63, 1.57), (-0.31, -0.65, 1.69), 0.055, 0.042),
        ("ell", (-0.31, -0.65, 1.69), (0.045, 0.018, 0.085)),
        ("limb", (-0.31, -0.65, 1.69), (-0.29, -0.65, 1.77), 0.014, 0.01),
        ("ball", (0.56, -0.58, 1.39), 0.08),
        ("limb", (0.56, -0.58, 1.39), (0.63, -0.13, 1.26), 0.07, 0.055),
        ("ball", (0.63, -0.13, 1.26), 0.055),
        ("limb", (0.63, -0.13, 1.26), (0.27, -0.55, 1.18), 0.055, 0.045),
        ("limb", (0.21, 0.30, 1.91), (0.72, -0.61, 0.69), 0.02, 0.022),
        ("ell", (0.72, -0.61, 0.69), (0.035, 0.035, 0.09)),
        ("limb", (0.51, -0.62, 0.85), (0.58, -0.44, 0.50), 0.1, 0.07),
        ("ball", (0.58, -0.44, 0.50), 0.07),
        ("limb", (0.58, -0.44, 0.50), (0.83, 0.26, 0.12), 0.07, 0.05),
        ("limb", (0.83, 0.26, 0.12), (0.92, 0.20, 0.05), 0.05, 0.035),
        ("limb", (0.33, -0.62, 0.85), (0.30, -0.47, 0.47), 0.1, 0.07),
        ("ball", (0.30, -0.47, 0.47), 0.07),
        ("limb", (0.30, -0.47, 0.47), (0.34, -0.32, 0.05), 0.07, 0.05),
        ("limb", (0.34, -0.32, 0.05), (0.34, -0.40, 0.01), 0.05, 0.035),
    ],
    # The post surgeon, fallen under them: half-lying back across the rock under Mrs.
    # Helm's skirt, his head at the warrior's bent knee, propped on one arm, one leg
    # stretched out to the west edge.
    "surgeon": [
        ("ball", (-0.30, -0.15, 0.39), 0.075),
        ("limb", (-0.22, -0.10, 0.35), (-0.04, 0.12, 0.21), 0.13, 0.14),
        ("ball", (-0.22, -0.10, 0.35), 0.060000000000000005),
        ("limb", (-0.22, -0.10, 0.35), (-0.18, -0.35, 0.17), 0.05, 0.04),
        ("ball", (-0.18, -0.35, 0.17), 0.04),
        ("limb", (-0.18, -0.35, 0.17), (-0.22, -0.42, 0.02), 0.04, 0.03),
        ("limb", (-0.04, 0.12, 0.21), (-0.49, -0.05, 0.26), 0.09, 0.065),
        ("ball", (-0.49, -0.05, 0.26), 0.065),
        ("limb", (-0.49, -0.05, 0.26), (-0.73, -0.25, 0.08), 0.065, 0.045),
        ("limb", (-0.73, -0.25, 0.08), (-0.81, -0.28, 0.04), 0.045, 0.035),
        ("limb", (-0.04, 0.12, 0.21), (0.16, -0.10, 0.32), 0.09, 0.07),
        ("limb", (0.16, -0.10, 0.32), (0.28, -0.22, 0.05), 0.065, 0.045),
    ],
    # The child, right front: kneeling at the rock's edge, reaching out to the right with
    # both arms.
    "child": [
        ("ball", (0.55, -0.72, 0.37), 0.06),
        ("limb", (0.56, -0.72, 0.11), (0.56, -0.72, 0.31), 0.08, 0.09),
        ("cone", (0.56, -0.72, 0.23), (0.56, -0.72, 0.11), 0.09, 0.15),
        ("limb", (0.60, -0.72, 0.29), (0.79, -0.51, 0.33), 0.032, 0.027),
        ("limb", (0.79, -0.51, 0.33), (1.00, -0.30, 0.39), 0.027, 0.022),
        ("limb", (0.52, -0.72, 0.28), (0.65, -0.72, 0.34), 0.032, 0.027),
        ("limb", (0.65, -0.72, 0.34), (0.75, -0.72, 0.39), 0.027, 0.022),
        ("limb", (0.56, -0.72, 0.11), (0.64, -0.45, 0.04), 0.05, 0.04),
        ("limb", (0.64, -0.45, 0.04), (0.60, -0.52, -0.00), 0.04, 0.03),
    ],
}
#: The rock to the highest point of the poses above (the tip of Black Partridge's standing
#: feather, ICHi-19208 y 130 px), which `group_h_m` less the rock scales (T-3582).
POSE_TOP_M = 1.91


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


class _Mesh:
    """Indexed vertices per material, in the archetype's frame (x east, y north, z up)."""

    def __init__(self):
        self.parts = [{"pos": [], "nrm": [], "conf": [], "idx": []} for _ in MATERIALS]

    def vert(self, mat, p, n, conf) -> int:
        part = self.parts[mat]
        part["pos"].append(p)
        part["nrm"].append(n)
        part["conf"].append(conf)
        return len(part["pos"]) - 1

    def mesh(self, mat, pos, nrm, idx, conf) -> None:
        """A whole indexed mesh at once (a posed figure, T-3583)."""
        part = self.parts[mat]
        base = len(part["pos"])
        part["pos"] += pos
        part["nrm"] += nrm
        part["conf"] += [conf] * len(pos)
        part["idx"] += [base + i for i in idx]

    def tri(self, mat, a, b, c) -> None:
        self.parts[mat]["idx"] += [a, b, c]

    def face(self, mat, pts, conf) -> None:
        """A flat convex polygon, wound counter-clockwise seen from outside."""
        n = _norm(_cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0])))
        ix = [self.vert(mat, p, n, conf) for p in pts]
        for k in range(1, len(ix) - 1):
            self.tri(mat, ix[0], ix[k], ix[k + 1])

    @property
    def triangles(self) -> int:
        n = 0
        for p in self.parts:
            n += len(p["idx"]) // 3
        return n


def _ring(cx, cy, w, d):
    """A rectangle's corners anticlockwise from the south-west, round (cx, cy)."""
    return [(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2),
            (cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2)]


def _band(m, mat, lo, z0, hi, z1, conf, top=False):
    """The four sides between rectangle `lo` at z0 and rectangle `hi` at z1 (a box when
    they are the same, a wash or a cove when not), and its top when asked."""
    for k in range(4):
        a, b = lo[k], lo[(k + 1) % 4]
        c, d = hi[(k + 1) % 4], hi[k]
        m.face(mat, [(a[0], a[1], z0), (b[0], b[1], z0), (c[0], c[1], z1), (d[0], d[1], z1)], conf)
    if top:
        m.face(mat, [(p[0], p[1], z1) for p in hi], conf)


def _pedestal(m: _Mesh, p: MonumentParams, cx: float, cy: float) -> float:
    conf = p.worst_conf("base_w_m", "base_d_m", "base_h_m", "plinth_w_m", "die_w_m", "die_h_m")
    z = 0.0
    # the stage base, its top washed in to a ledge round the plinth
    base = _ring(cx, cy, p.base_w_m, p.base_d_m)
    ledge = _ring(cx, cy, min(p.base_w_m, p.plinth_w_m + 0.24), min(p.base_d_m, p.plinth_d_m + 0.24))
    _band(m, M_GRANITE, base, z - 0.15, base, p.base_h_m - p.base_wash_m, conf)
    _band(m, M_GRANITE, base, p.base_h_m - p.base_wash_m, ledge, p.base_h_m, conf, top=True)
    z = p.base_h_m
    # the plinth, and the fillet projecting at its top
    plinth = _ring(cx, cy, p.plinth_w_m, p.plinth_d_m)
    fil = 0.10
    _band(m, M_GRANITE, plinth, z, plinth, z + p.plinth_h_m - fil, conf)
    fillet = _ring(cx, cy, p.plinth_w_m + 0.06, p.plinth_d_m + 0.06)
    _band(m, M_GRANITE, fillet, z + p.plinth_h_m - fil, fillet, z + p.plinth_h_m - 0.04, conf)
    die = _ring(cx, cy, p.die_w_m, p.die_d_m)
    _band(m, M_GRANITE, fillet, z + p.plinth_h_m - 0.04, die, z + p.plinth_h_m, conf, top=True)
    z += p.plinth_h_m
    # the die
    _band(m, M_GRANITE, die, z, die, z + p.die_h_m, conf)
    die_z = z
    z += p.die_h_m
    # the cap: a cove out, a fillet, a wash in
    o = p.cap_overhang_m
    cove = _ring(cx, cy, p.die_w_m + 2 * o, p.die_d_m + 2 * o)
    wash = _ring(cx, cy, p.die_w_m + o * 0.6, p.die_d_m + o * 0.6)
    h = p.cap_h_m
    _band(m, M_GRANITE, die, z, cove, z + h * 0.40, conf)
    _band(m, M_GRANITE, cove, z + h * 0.40, cove, z + h * 0.75, conf)
    _band(m, M_GRANITE, cove, z + h * 0.75, wash, z + h, conf, top=True)
    z += h
    _panels(m, p, cx, cy, die_z)
    _lettering(m, p, cx, cy, die_z)
    return z


def _panels(m: _Mesh, p: MonumentParams, cx: float, cy: float, die_z: float) -> None:
    """The bronze panels, 2 cm proud of the die: 0.30-0.85 of its height, as ICHi-19208
    shows the front one (y 548-650 px on a die of 520-705), 0.82 of the face's width."""
    if not p.panels:
        return
    conf = p.worst_conf("panels")
    z0, z1 = die_z + p.die_h_m * 0.30, die_z + p.die_h_m * 0.85
    t = 0.02
    faces = ["s", "n", "e", "w"][: {1: 1, 2: 2, 4: 4}[p.panels]]
    for f in faces:
        if f in ("s", "n"):
            w = p.die_w_m * 0.82
            y = cy - p.die_d_m / 2 if f == "s" else cy + p.die_d_m / 2
            lo = _ring(cx, y + (-t / 2 if f == "s" else t / 2), w, t)
        else:
            w = p.die_d_m * 0.75
            x = cx + p.die_w_m / 2 if f == "e" else cx - p.die_w_m / 2
            lo = _ring(x + (t / 2 if f == "e" else -t / 2), cy, t, w)
        _band(m, M_PALE, lo, z0, lo, z1, conf)


def _lettering(m: _Mesh, p: MonumentParams, cx: float, cy: float, die_z: float) -> None:
    """The inscription cut in the die's front under its panel, pale on the granite as
    ICHi-19208 shows it: each line's strokes flat on the face, 3 mm proud so they never
    fight it for depth, each line squeezed or spread to the width the plate gives it."""
    lines = [ln.strip() for ln in p.lettering.split("/") if ln.strip()]
    if not lines:
        return
    conf = p.worst_conf("lettering", "die_w_m", "die_h_m")
    y = cy - p.die_d_m / 2 - 0.003
    for i, line in enumerate(lines):
        wf, bf, hf = LETTER_LINES[min(i, len(LETTER_LINES) - 1)]
        if i >= len(LETTER_LINES):
            bf -= (i - len(LETTER_LINES) + 1) * (hf + 0.012)
        h = p.die_h_m * hf
        unit = h / (6 + LETTER_STROKE)
        w = LETTER_STROKE * unit
        half = LETTER_STROKE / 2
        adv_total = 0.0
        for c in line:   # left to right, never sum() (T-2363: bytes stable across Pythons)
            adv_total += GLYPHS[c][1]
        natural = (adv_total - 1.6) * unit
        sx = p.die_w_m * wf / natural
        x = cx - p.die_w_m * wf / 2
        base = die_z + p.die_h_m * bf
        for c in line:
            strokes, adv = GLYPHS[c]
            for (a0, b0, a1, b1) in strokes:
                ax, az = x + (a0 * sx + half) * unit, base + (b0 + half) * unit
                bx, bz = x + (a1 * sx + half) * unit, base + (b1 + half) * unit
                dx, dz = bx - ax, bz - az
                ln = math.hypot(dx, dz)
                dx, dz = dx / ln, dz / ln
                ax, az, bx, bz = ax - dx * w / 2, az - dz * w / 2, bx + dx * w / 2, bz + dz * w / 2
                px, pz = -dz * w / 2, dx * w / 2
                m.face(M_PALE, [(ax - px, y, az - pz), (bx - px, y, bz - pz),
                                (bx + px, y, bz + pz), (ax + px, y, az + pz)], conf)
            x += adv * unit * sx


def _rock(m: _Mesh, p: MonumentParams, cx: float, cy: float, z0: float) -> None:
    """The cast ground the group stands on: a broken field over the cap's top, highest
    under the figures, skirted down to the granite at its edge. Both photographs show it
    rough, in ledges and clefts rising under the feet (T-3582): many small lumps over a
    few large ones, and every point of the field knocked up or down a few centimetres."""
    conf = p.worst_conf("rock_h_m")
    rng = random.Random(p.seed)
    nx, ny = 26, 18
    w, d = p.die_w_m + p.cap_overhang_m * 0.4, p.die_d_m + p.cap_overhang_m * 0.4
    lumps = [(rng.uniform(-0.45, 0.45) * w, rng.uniform(-0.4, 0.4) * d, rng.uniform(0.15, 0.35),
              rng.uniform(0.25, 1.0)) for _ in range(9)]
    lumps += [(rng.uniform(-0.48, 0.48) * w, rng.uniform(-0.45, 0.45) * d, rng.uniform(0.05, 0.12),
               rng.uniform(-0.35, 0.45)) for _ in range(40)]
    knock = {(i, j): rng.uniform(-1.0, 1.0) for j in range(ny + 1) for i in range(nx + 1)}

    def height(fx, fy):
        ex = 1.0 - (2 * abs(fx) / w) ** 4
        ey = 1.0 - (2 * abs(fy) / d) ** 4
        edge = max(0.0, min(ex, ey))
        bump = math.fsum(a * math.exp(-((fx - lx) ** 2 + (fy - ly) ** 2) / (2 * r * r)) for lx, ly, r, a in lumps)
        return p.rock_h_m * (0.25 + 0.75 * edge * (0.55 + 0.45 * max(0.0, min(1.0, bump))))

    grid = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            fx, fy = (i / nx - 0.5) * w, (j / ny - 0.5) * d
            rough = 0.0 if i in (0, nx) or j in (0, ny) else 0.035 * knock[i, j]
            grid[i, j] = (cx + fx, cy + fy, z0 + max(0.02, height(fx, fy) + rough))
    for j in range(ny):
        for i in range(nx):
            a, b, c, e = grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]
            m.face(M_BRONZE, [a, b, c], conf)
            m.face(M_BRONZE, [a, c, e], conf)
    # the skirt: the field's edge straight down to the cap
    edge = ([grid[i, 0] for i in range(nx + 1)] + [grid[nx, j] for j in range(1, ny + 1)]
            + [grid[i, ny] for i in range(nx - 1, -1, -1)] + [grid[0, j] for j in range(ny - 1, 0, -1)])
    for k in range(len(edge)):
        a, b = edge[k], edge[(k + 1) % len(edge)]
        m.face(M_BRONZE, [(a[0], a[1], z0), (b[0], b[1], z0), b, a], conf)


def _frame(axis):
    axis = _norm(axis)
    helper = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm(_cross(axis, helper))
    v = _cross(axis, u)
    return u, v


def _limb(m, a, b, ra, rb, conf, sides=LIMB_SIDES):
    axis = _sub(b, a)
    u, v = _frame(axis)
    ring_a, ring_b = [], []
    for k in range(sides):
        t = 2 * math.pi * k / sides
        n = tuple(math.cos(t) * u[i] + math.sin(t) * v[i] for i in range(3))
        ring_a.append(m.vert(M_BRONZE, tuple(a[i] + ra * n[i] for i in range(3)), n, conf))
        ring_b.append(m.vert(M_BRONZE, tuple(b[i] + rb * n[i] for i in range(3)), n, conf))
    for k in range(sides):
        k2 = (k + 1) % sides
        m.tri(M_BRONZE, ring_a[k], ring_a[k2], ring_b[k2])
        m.tri(M_BRONZE, ring_a[k], ring_b[k2], ring_b[k])
    # close the ends, so a thin member seen end-on is not hollow
    ca = m.vert(M_BRONZE, a, _norm(tuple(-x for x in axis)), conf)
    cb = m.vert(M_BRONZE, b, _norm(axis), conf)
    for k in range(sides):
        k2 = (k + 1) % sides
        m.tri(M_BRONZE, ca, ring_a[k2], ring_a[k])
        m.tri(M_BRONZE, cb, ring_b[k], ring_b[k2])


def _ell(m, c, radii, conf, sides=LIMB_SIDES, rings=BALL_RINGS):
    rx, ry, rz = radii
    rows = []
    for j in range(rings + 1):
        ph = math.pi * j / rings - math.pi / 2
        row = []
        for k in range(sides):
            t = 2 * math.pi * k / sides
            d = (math.cos(ph) * math.cos(t), math.cos(ph) * math.sin(t), math.sin(ph))
            n = _norm((d[0] / rx, d[1] / ry, d[2] / rz))
            row.append(m.vert(M_BRONZE, (c[0] + rx * d[0], c[1] + ry * d[1], c[2] + rz * d[2]), n, conf))
        rows.append(row)
    for j in range(rings):
        for k in range(sides):
            k2 = (k + 1) % sides
            a, b, cc, d = rows[j][k], rows[j][k2], rows[j + 1][k2], rows[j + 1][k]
            m.tri(M_BRONZE, a, b, cc)
            m.tri(M_BRONZE, a, cc, d)


def _cone(m, top, bottom, rt, rb, conf, sides=12):
    """A skirt: open at the top, closed at the hem."""
    _limb(m, bottom, top, rb, rt, conf, sides)


def _group(m: _Mesh, p: MonumentParams, cx: float, cy: float, z0: float) -> None:
    """The five figures: each body a people rig posed to its joints (T-3583,
    `monument_figures`), and the parts of `FIGURES` the rigs have not got (feathers,
    weapons, the cloak, the knot of hair) as they were."""
    conf = p.worst_conf("group_h_m")
    k = (p.group_h_m - p.rock_h_m) / POSE_TOP_M
    # the poses' y runs back from the front, which is the archetype's +y (north)
    place = lambda q: (cx + k * q[0], cy + k * q[1], z0 + k * q[2])  # noqa: E731
    for name in ("warrior", "helm", "black_partridge", "surgeon", "child"):
        pos, nrm, tri = monument_figures.pose(name, k)
        m.mesh(M_BRONZE, [(cx + float(v[0]), cy + float(v[1]), z0 + float(v[2])) for v in pos],
               [(float(n[0]), float(n[1]), float(n[2])) for n in nrm], tri.tolist(), conf)
        for i in monument_figures.PROPS[name]:
            part = FIGURES[name][i]
            kind = part[0]
            if kind == "limb":
                _limb(m, place(part[1]), place(part[2]), k * part[3], k * part[4], conf)
            elif kind == "ball":
                r = k * part[2]
                _ell(m, place(part[1]), (r, r, r), conf)
            elif kind == "ell":
                _ell(m, place(part[1]), tuple(k * r for r in part[2]), conf)
            elif kind == "cone":
                _cone(m, place(part[1]), place(part[2]), k * part[3], k * part[4], conf)


def mesh(params: MonumentParams) -> _Mesh:
    """The monument, its base centred in the footprint rectangle, grade at z 0."""
    params.validate()
    m = _Mesh()
    cx, cy = params.base_w_m / 2, params.base_d_m / 2
    top = _pedestal(m, params, cx, cy)
    _rock(m, params, cx, cy, top)
    _group(m, params, cx, cy, top + params.rock_h_m * 0.55)
    return m


def _pad(blob: bytes, fill: bytes = b"\x00") -> bytes:
    return blob + fill * ((4 - len(blob) % 4) % 4)


def glb(params: MonumentParams, structure_id: str, phase_id: str) -> bytes:
    """The structure's GLB. glTF is y-up: the archetype's (x, y, z) is written as
    (x, z, -y), a rotation, so no face turns inside out (docs/GLB-CONTRACT.md)."""
    m = mesh(params)
    to_gl = lambda p: (round(p[0], 4), round(p[2], 4), round(-p[1], 4))  # noqa: E731
    bin_ = bytearray()
    views, accessors, prims = [], [], []

    def view(blob: bytes, target: int) -> int:
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(blob)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(blob), "target": target})
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False) -> int:
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5123: "H", 5125: "I"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [struct.unpack("<f", struct.pack("<f", min(v[k] for v in values)))[0]
                          for k in range(comps)]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", max(v[k] for v in values)))[0]
                          for k in range(comps)]
        accessors.append(acc)
        return len(accessors) - 1

    used = []
    for mi, part in enumerate(m.parts):
        if not part["idx"]:
            continue
        pos = [to_gl(p) for p in part["pos"]]
        nrm = [(round(n[0], 4), round(n[2], 4), round(-n[1], 4)) for n in part["nrm"]]
        attrs = {"POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                 "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                 "_CONFIDENCE": accessor(part["conf"], 5126, "SCALAR", 1, 34962)}
        used.append(mi)
        idx = part["idx"]
        prims.append({"attributes": attrs,
                      "indices": accessor(idx, 5123 if len(pos) < 65536 else 5125, "SCALAR", 1, 34963),
                      "material": len(used) - 1})
    mats = []
    for mi in used:
        name, rgba, r = MATERIALS[mi]
        mats.append({"name": name, "pbrMetallicRoughness": {
            "baseColorFactor": [round(x, 4) for x in rgba], "metallicFactor": 0.0,
            "roughnessFactor": round(r, 4)}})
    name = f"{structure_id}__{phase_id}"
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0,
                   "extras": {"structure_id": structure_id, "phase_id": phase_id}}],
        "meshes": [{"name": name, "primitives": prims}],
        "materials": mats,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)
