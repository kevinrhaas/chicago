"""Doors, windows and the trim round them — one kit for every 1835 archetype (T-2278).

THE OWNER'S ASK, 2026-10-10: every 1835 structure gets correct door and window
openings and the trim that goes with them; where a building could reasonably have
had glass it gets the dark glass Glessner's 1904 house is drawn with; elsewhere an
opening that renders well and reads as a photograph.

WHAT THE TOWN DREW BEFORE THIS. A window was a flat near-black panel standing 4 cm
proud of the wall inside a flat trim panel, with flat sash bars in front: a plaque
with a picture of a window on it. A door was the same black panel with no door in
it, so every house, cabin and store in town stood open onto a void. The Green Tree
and the other taverns drew their panes with no sash at all.

THE GLASS, AND WHY EVERY DWELLING MAY HAVE IT. Window glass was a stock article in
Chicago in the two years before the scene. At least five merchants advertised it by
the box in the Chicago Democrat, 1833-35 — Philo Carpenter (crown glass on
consignment), John H. Kinzie, J. K. Botsford, P. F. W. Peck and Jones & King — in
8 x 10, 7 x 9 and 5 x 10 in panes, and Kinzie, Botsford and Peck sold READY-MADE
WINDOW SASH beside it (data/businesses/biz_*.json carries each advertisement with
its issue). The Green Tree's 6 x 8 in lights are the one pane size attested on a
building (chicagology_prefire127). So a frame house, a store, a tavern, a fort
building and a log cabin in this town could all have been glazed, and are. Oiled
paper and bare shutters belong to the remote frontier a decade earlier, not to a
lake port with glass on the shelf. Barns, sheds, stables and privies stay unglazed:
nothing put glass in a building nobody lived or sold in, and their openings keep the
outbuilding archetype's own board doors and vents.

THE DARK PANE IS GLESSNER'S. T-2109 / T-2183 draw Glessner's glass, at every
detail setting, as an opaque dark plate: the GLB's own near-white glass (0.945,
0.970, 0.953) at twelve per cent, roughness 0.065, metalness 0. The owner liked it,
and it is the right answer here for the reason it was there: from a street in
daylight a pane reads as a dark, glossy surface with the sky in it, not as a hole.
`materials.GLASS` now carries exactly those numbers, so the 1835 panes and the 1904
ones are the same glass. It costs nothing to draw: the town batches by material
key, colour and roughness ride the vertex stream, and an opaque pane joins the one
building batch.

THE GEOMETRY. Surfaces, not holes, as before: walls are closed boxes and interiors
are out of scope. What changes is that the opening now has DEPTH a visitor can see.
The casing stands proud of the wall's skin with real returns, the pane sits back
near the skin, so the jambs and the head show as a reveal; a sloped sill with horns
and a drip cap over the head cast the two shadow lines that make a window read as
set into a wall from across a street. A door is CLOSED: a panelled leaf on a frame
house, a store or a tavern (half-glazed on a shop, with a transom light over a door
tall enough to carry one), a board-and-batten leaf with iron strap hinges on a log
cabin. All of it is flat-faced quads in the archetypes' own idiom — a boxed bar per
muntin would treble every window in the town for a shadow nobody sees at 10 m.

EVERY NUMBER HERE IS RECONSTRUCTED. No source states the casing width of any 1835
Chicago building, the colour of any door, or how a sill was run. The dimensions are
the ordinary carpentry of the period (a 3.5 in casing, a 1 3/4 in sash, a 2 in sill
projection) and are recorded as liberty L-OPEN in docs/LIBERTIES.md.

FRAME. Every function takes a `Wall`: the axis the wall's normal lies on, the plane
of the wall's own face, which way is out, and `skin` — how far the wall's surface
stands proud of that plane (a clapboard's lip, a log wall's chinking). Offsets `n`
are metres outward from the plane; `u` runs along the wall exactly as each
archetype's `_panel` already uses it; `z` is height. Winding is computed, not hand
written: every face is turned to face the normal it is asked for.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from common import materials

# ---------------------------------------------------------------- dimensions

CASING_W_M = 0.090      # face width of a plain board casing (~3 1/2 in)
HEAD_W_M = 0.115        # the head casing, a little deeper than the legs
CASING_PROUD_M = 0.050  # how far the casing face stands in front of the wall's skin
PANE_BACK_M = 0.013     # the pane, just in front of the skin (and of a clapboard's butt joints)
SASH_PROUD_M = 0.012    # sash timber in front of its pane
SILL_OUT_M = 0.055      # the sill's nose beyond the casing face
SILL_DROP_M = 0.024     # fall of the sill's weathered top, back to front
SILL_FACE_M = 0.045     # depth of the sill's front edge
SILL_HORN_M = 0.030     # how far the sill runs past each casing leg
CAP_OUT_M = 0.025       # the drip cap's nose beyond the casing face
CAP_H_M = 0.035         # its front edge
CAP_RISE_M = 0.020      # its weathered top, rising back to the wall

DOOR_STILE_M = 0.11
DOOR_RAIL_M = 0.11
DOOR_LOCK_RAIL_M = 0.16
BATTEN_W_M = 0.13
BATTEN_PROUD_M = 0.020
TRANSOM_MIN_DOOR_M = 2.05   # an opening this tall carries a transom light over its leaf
TRANSOM_H_M = 0.34

# ---------------------------------------------------------------- the finishes

# The door's paint, DEALT, because no source gives the colour of any door in the
# town. The four are the ordinary exterior colours of a painted American front door
# in the 1830s — a bottle green, a Spanish brown, a black-green and a red-brown —
# and a weathered unpainted board for a house whose walls carry no coat either.
DOOR_PAINTS = (
    ("bottle_green", (0.050, 0.085, 0.060, 1.0), 0.55),
    ("spanish_brown", (0.170, 0.075, 0.045, 1.0), 0.60),
    ("black_green", (0.028, 0.036, 0.030, 1.0), 0.50),
    ("red_brown", (0.210, 0.060, 0.040, 1.0), 0.60),
)
WEATHERED_BOARD = ((0.300, 0.272, 0.232, 1.0), 0.86)
STRAP_IRON = ((0.055, 0.052, 0.050, 1.0), 0.55)


def deal(seed: str, n: int) -> int:
    """A stable choice among `n` from a record's identity. Not random: a rebake that
    repainted every door would make the asset hashes meaningless."""
    return int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16) % n


def door_paint(seed: str, painted: bool) -> tuple:
    """(rgba, roughness) of a door leaf: dealt from the paints when the house is
    painted, the weathered board when it is not."""
    if not painted:
        return WEATHERED_BOARD
    _name, rgba, rough = DOOR_PAINTS[deal("door|" + seed, len(DOOR_PAINTS))]
    return rgba, rough


def shade(rgba, k: float) -> tuple:
    """`rgba` with its colour scaled by `k` — a recessed panel's own shadow, carried in
    the colour because a flat panel casts none."""
    return (rgba[0] * k, rgba[1] * k, rgba[2] * k, rgba[3])


# ---------------------------------------------------------------- the frame

@dataclass(frozen=True)
class Wall:
    axis: str          # 'x' or 'y': the axis the wall's outward normal lies on
    plane: float       # coordinate of the wall's own face on that axis
    outward: int       # +1 or -1
    skin: float = 0.0  # how far the wall's surface stands proud of `plane`


@dataclass(frozen=True)
class Mats:
    """Material indices the kit draws with. `casing` and `sash` are the archetype's own
    trim; `glass`, `door`, `panel` and `iron` are usually `MeshBuilder.named_mat`s."""
    casing: int
    sash: int
    glass: int
    door: int = -1
    panel: int = -1
    iron: int = -1
    dark: int = -1


def _pt(w: Wall, u: float, n: float, z: float) -> tuple:
    off = w.plane + w.outward * n
    return (u, off, z) if w.axis == "y" else (off, u, z)


def _vec(w: Wall, du: float, dn: float, dz: float) -> tuple:
    on = w.outward * dn
    return (du, on, dz) if w.axis == "y" else (on, du, dz)


def _poly(b, w: Wall, pts_unz, facing: tuple, conf: float, mat: int) -> None:
    """Add a polygon given in (u, n, z), turned to face `facing` given in (u, n, z)."""
    pts = [_pt(w, *p) for p in pts_unz]
    nx = ny = nz = 0.0
    for i in range(len(pts)):
        x1, y1, z1 = pts[i]
        x2, y2, z2 = pts[(i + 1) % len(pts)]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    want = _vec(w, *facing)
    if nx * want[0] + ny * want[1] + nz * want[2] < 0:
        pts.reverse()
    b.add_poly(pts, conf, mat)


def face(b, w: Wall, n: float, u0: float, u1: float, z0: float, z1: float,
         conf: float, mat: int) -> None:
    """A rectangle parallel to the wall, `n` out from its plane, facing out."""
    _poly(b, w, [(u0, n, z0), (u1, n, z0), (u1, n, z1), (u0, n, z1)], (0, 1, 0), conf, mat)


def _jamb(b, w: Wall, u: float, n0: float, n1: float, z0: float, z1: float,
          side: int, conf: float, mat: int) -> None:
    """A vertical face square to the wall at `u`, facing `side` (+1 toward +u)."""
    _poly(b, w, [(u, n0, z0), (u, n1, z0), (u, n1, z1), (u, n0, z1)], (side, 0, 0), conf, mat)


def _level(b, w: Wall, u0: float, u1: float, n0: float, z0: float, n1: float, z1: float,
           up: int, conf: float, mat: int) -> None:
    """A face running out from the wall, from (n0, z0) to (n1, z1), facing up (+1)
    or down (-1). A sill's weathered top and a cap's both slope."""
    _poly(b, w, [(u0, n0, z0), (u1, n0, z0), (u1, n1, z1), (u0, n1, z1)], (0, 0, up), conf, mat)


# ---------------------------------------------------------------- the surround

def surround(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
             mats: Mats, sill: bool = True, cap: bool = True,
             casing_w: float = CASING_W_M, head_w: float = HEAD_W_M,
             proud: float = CASING_PROUD_M, back: float = PANE_BACK_M) -> None:
    """The casing round an opening `u0..u1 x z0..z1`, with its reveal, sill and cap.

    The legs and the head stand `proud` in front of the skin with their outer
    returns, and their inner returns run back to the pane at `back` — that strip is
    the reveal, and it is what turns the opening from a plaque into a hole. The sill
    (a window's) runs under the legs with horns and a weathered top; the cap is a
    drip cap on the head, the one moulding a plain 1830s frame wall carried.
    """
    s = w.skin
    nf, nb = s + proud, s + back
    cw, hw = casing_w, head_w
    zl = z0
    # faces: head, two legs
    face(b, w, nf, u0 - cw, u1 + cw, z1, z1 + hw, conf, mats.casing)
    face(b, w, nf, u0 - cw, u0, zl, z1, conf, mats.casing)
    face(b, w, nf, u1, u1 + cw, zl, z1, conf, mats.casing)
    # outer returns of the legs (the head's top is under the cap, or shown below)
    _jamb(b, w, u0 - cw, s, nf, zl, z1 + hw, -1, conf, mats.casing)
    _jamb(b, w, u1 + cw, s, nf, zl, z1 + hw, 1, conf, mats.casing)
    # the reveal: the legs' inner returns and the head's soffit, back to the pane
    _jamb(b, w, u0, nb, nf, z0, z1, 1, conf, mats.casing)
    _jamb(b, w, u1, nb, nf, z0, z1, -1, conf, mats.casing)
    _level(b, w, u0, u1, nb, z1, nf, z1, -1, conf, mats.casing)
    if sill:
        su0, su1 = u0 - cw - SILL_HORN_M, u1 + cw + SILL_HORN_M
        nose = nf + SILL_OUT_M
        top = z0
        _level(b, w, su0, su1, nb, top, nose, top - SILL_DROP_M, 1, conf, mats.casing)
        face(b, w, nose, su0, su1, top - SILL_DROP_M - SILL_FACE_M, top - SILL_DROP_M,
             conf, mats.casing)
        for u, side in ((su0, -1), (su1, 1)):
            _poly(b, w, [(u, s, top), (u, nose, top - SILL_DROP_M),
                         (u, nose, top - SILL_DROP_M - SILL_FACE_M),
                         (u, s, top - SILL_DROP_M - SILL_FACE_M)], (side, 0, 0), conf,
                  mats.casing)
    if cap:
        cu0, cu1 = u0 - cw - 0.02, u1 + cw + 0.02
        zc = z1 + hw
        nose = nf + CAP_OUT_M
        face(b, w, nose, cu0, cu1, zc, zc + CAP_H_M, conf, mats.casing)
        _level(b, w, cu0, cu1, s, zc + CAP_H_M + CAP_RISE_M, nose, zc + CAP_H_M, 1,
               conf, mats.casing)
        _level(b, w, cu0, cu1, nf, zc, nose, zc, -1, conf, mats.casing)
        for u, side in ((cu0, -1), (cu1, 1)):
            _poly(b, w, [(u, s, zc), (u, nose, zc), (u, nose, zc + CAP_H_M),
                         (u, s, zc + CAP_H_M + CAP_RISE_M)], (side, 0, 0), conf,
                  mats.casing)
    else:
        _level(b, w, u0 - cw, u1 + cw, s, z1 + hw, nf, z1 + hw, 1, conf, mats.casing)


# ---------------------------------------------------------------- glazing

def sash(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
         mat: int, across: int, rows: tuple | None, stile: float = 0.045,
         meeting: float = 0.035, muntin: float = 0.022, n: float | None = None) -> None:
    """The sash timber over a pane: stiles, rails, a meeting rail and muntins.

    `rows` is (upper, lower) for a double-hung window; None is a single fixed light
    of `across` x 1 rows... or a fixed sash whose row count is `across`'s partner,
    passed as rows=(k,) — one band of k rows with no meeting rail.
    """
    y = (w.skin + PANE_BACK_M + SASH_PROUD_M) if n is None else n
    s = stile

    def bar(a0, a1, c0, c1):
        face(b, w, y, a0, a1, c0, c1, conf, mat)

    bar(u0, u0 + s, z0, z1)
    bar(u1 - s, u1, z0, z1)
    bar(u0 + s, u1 - s, z0, z0 + s)
    bar(u0 + s, u1 - s, z1 - s, z1)
    if rows is None or len(rows) == 1:
        k = 1 if rows is None else rows[0]
        bands = [(z0 + s, z1 - s, k)]
    else:
        up, lo = rows
        pane = (z1 - z0 - 2 * s - meeting - (up + lo - 2) * muntin) / (up + lo)
        zm = z0 + s + lo * pane + (lo - 1) * muntin
        bar(u0 + s, u1 - s, zm, zm + meeting)
        bands = [(z0 + s, zm, lo), (zm + meeting, z1 - s, up)]
    lw = (u1 - u0 - 2 * s - (across - 1) * muntin) / across
    for k in range(1, across):
        u = u0 + s + k * lw + (k - 1) * muntin
        bar(u, u + muntin, z0 + s, z1 - s)
    for lo_z, hi_z, nrow in bands:
        lh = (hi_z - lo_z - (nrow - 1) * muntin) / nrow
        for k in range(1, nrow):
            z = lo_z + k * lh + (k - 1) * muntin
            bar(u0 + s, u1 - s, z, z + muntin)


def window(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
           mats: Mats, across: int, rows: tuple | None, sill: bool = True,
           cap: bool = True, casing_w: float = CASING_W_M, head_w: float = HEAD_W_M,
           proud: float = CASING_PROUD_M) -> None:
    """A glazed window: the surround, the dark pane set back in it, and the sash."""
    surround(b, w, u0, u1, z0, z1, conf, mats, sill=sill, cap=cap,
             casing_w=casing_w, head_w=head_w, proud=proud)
    face(b, w, w.skin + PANE_BACK_M, u0, u1, z0, z1, conf, mats.glass)
    sash(b, w, u0, u1, z0, z1, conf, mats.sash, across, rows)


# ---------------------------------------------------------------- doors

THRESHOLD_OUT_M = 0.06


def threshold(b, w: Wall, u0: float, u1: float, z0: float, conf: float, mat: int,
              casing_w: float = CASING_W_M, proud: float = CASING_PROUD_M) -> None:
    """The oak sill a door stands on, run out past the casing: without it a door
    raised off the ground hangs in the wall like a picture."""
    if z0 < 0.04:
        return
    s = w.skin
    a, c = u0 - casing_w, u1 + casing_w
    nose = s + proud + THRESHOLD_OUT_M
    _level(b, w, a, c, s, z0, nose, z0 - 0.008, 1, conf, mat)
    face(b, w, nose, a, c, 0.0, z0 - 0.008, conf, mat)
    for u, side in ((a, -1), (c, 1)):
        _poly(b, w, [(u, s, 0.0), (u, nose, 0.0), (u, nose, z0 - 0.008), (u, s, z0)],
              (side, 0, 0), conf, mat)


def panelled_door(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
                  mats: Mats, panels: int = 4, glazed_upper: tuple | None = None,
                  transom: bool | None = None, cap: bool = True,
                  casing_w: float = CASING_W_M, head_w: float = HEAD_W_M,
                  proud: float = CASING_PROUD_M) -> None:
    """A closed panelled door in its casing, with a transom light where it is tall.

    `panels` is 4 (two over two, the ordinary 1830s door) or 6 (three over three).
    `glazed_upper` = (across, rows) glazes the upper half instead — a shop door. The
    panels are the leaf's own colour carried darker, which is what a sunk panel
    looks like at any distance a visitor stands from a door.
    """
    surround(b, w, u0, u1, z0, z1, conf, mats, sill=False, cap=cap,
             casing_w=casing_w, head_w=head_w, proud=proud)
    threshold(b, w, u0, u1, z0, conf, mats.casing, casing_w, proud)
    if transom is None:
        transom = (z1 - z0) >= TRANSOM_MIN_DOOR_M
    leaf_top = z1
    if transom:
        leaf_top = z1 - TRANSOM_H_M
        transom_light(b, w, u0, u1, leaf_top, z1, conf, mats)
    panelled_leaf(b, w, u0, u1, z0, leaf_top, conf, mats, panels, glazed_upper)


def transom_light(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
                  mats: Mats, n: float | None = None) -> None:
    """A fixed light of three panes over a door, on its own transom bar."""
    back = w.skin + PANE_BACK_M if n is None else n
    bar = 0.06
    face(b, w, back, u0, u1, z0 + bar, z1, conf, mats.glass)
    face(b, w, back + 0.012, u0, u1, z0, z0 + bar, conf, mats.casing)
    sash(b, w, u0, u1, z0 + bar, z1, conf, mats.sash, 3, (1,), stile=0.035,
         n=back + SASH_PROUD_M)


def panelled_leaf(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
                  mats: Mats, panels: int = 4, glazed_upper: tuple | None = None,
                  n: float | None = None) -> None:
    """The leaf alone, filling `u0..u1 x z0..z1`: stiles and rails in the door's
    paint, the panels sunk (carried darker), or the upper half glazed."""
    leaf_n = (w.skin + PANE_BACK_M + 0.004) if n is None else n
    face(b, w, leaf_n, u0, u1, z0, z1, conf, mats.door)
    pn = leaf_n + 0.004
    st, rl, lock = DOOR_STILE_M, DOOR_RAIL_M, DOOR_LOCK_RAIL_M
    a0, a1 = u0 + st, u1 - st
    zmid = z0 + (z1 - z0) * 0.46
    lower = (z0 + rl + 0.10, zmid - lock / 2)
    upper = (zmid + lock / 2, z1 - rl)
    cols = 2 if (u1 - u0) > 0.62 else 1
    g = (a1 - a0 - (cols - 1) * st) / cols
    if glazed_upper is not None:
        across, rows = glazed_upper
        face(b, w, pn, a0, a1, upper[0], upper[1], conf, mats.glass)
        sash(b, w, a0, a1, upper[0], upper[1], conf, mats.door, across, (rows,),
             stile=0.012, n=pn + 0.006)
        bands = [lower]
    elif panels == 6:
        h = (upper[1] - upper[0] - rl) / 2
        bands = [lower, (upper[0], upper[0] + h * 0.55), (upper[0] + h * 0.55 + rl, upper[1])]
    else:
        bands = [lower, upper]
    for c0z, c1z in bands:
        for k in range(cols):
            c0 = a0 + k * (g + st)
            face(b, w, pn, c0, c0 + g, c0z, c1z, conf, mats.panel)


def batten_door(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
                mats: Mats, seed: str = "", boards: int | None = None,
                cap: bool = False, casing_w: float = 0.10, head_w: float = 0.12,
                proud: float = 0.035, hinge_left: bool | None = None,
                leaves: int = 1) -> None:
    """A board-and-batten door: upright boards and two ledges on the face, hung on
    iron strap hinges — the door of a log house, a shop's back, a shed. `leaves` = 2
    hangs a pair, each on its own jamb, meeting in the middle: a freight door.

    The board joints are dark lines on the leaf, because a gap between boards is
    a shadow, not a board. A single leaf is hung left or right by the record's
    identity.
    """
    surround(b, w, u0, u1, z0, z1, conf, mats, sill=False, cap=cap,
             casing_w=casing_w, head_w=head_w, proud=proud)
    threshold(b, w, u0, u1, z0, conf, mats.casing, casing_w, proud)
    if leaves == 2:
        um = (u0 + u1) / 2.0
        batten_leaf(b, w, u0, um - 0.004, z0, z1, conf, mats, True, boards)
        batten_leaf(b, w, um + 0.004, u1, z0, z1, conf, mats, False, boards)
        return
    if hinge_left is None:
        hinge_left = deal("hinge|" + seed, 2) == 0
    batten_leaf(b, w, u0, u1, z0, z1, conf, mats, hinge_left, boards, latch=True)


def batten_leaf(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
                mats: Mats, hinge_left: bool, boards: int | None = None,
                latch: bool = False) -> None:
    """One board leaf with its two ledges, strap hinges on the `hinge_left` side."""
    leaf_n = w.skin + PANE_BACK_M + 0.004
    face(b, w, leaf_n, u0, u1, z0, z1, conf, mats.door)
    if boards is None:
        boards = max(2, round((u1 - u0) / 0.24))
    bw = (u1 - u0) / boards
    joint = mats.dark if mats.dark >= 0 else mats.panel
    for k in range(1, boards):
        u = u0 + k * bw
        face(b, w, leaf_n + 0.002, u - 0.008, u + 0.008, z0, z1, conf, joint)
    lz = (z0 + min(0.22, (z1 - z0) * 0.15), z1 - min(0.22, (z1 - z0) * 0.15))
    bn = leaf_n + BATTEN_PROUD_M
    for zc in lz:
        face(b, w, bn, u0 + 0.03, u1 - 0.03, zc - BATTEN_W_M / 2, zc + BATTEN_W_M / 2,
             conf, mats.door)
        _level(b, w, u0 + 0.03, u1 - 0.03, leaf_n, zc + BATTEN_W_M / 2, bn,
               zc + BATTEN_W_M / 2, 1, conf, mats.door)
        _level(b, w, u0 + 0.03, u1 - 0.03, leaf_n, zc - BATTEN_W_M / 2, bn,
               zc - BATTEN_W_M / 2, -1, conf, mats.panel)
    if mats.iron >= 0:
        hu0, hu1 = (u0 - 0.02, u0 + (u1 - u0) * 0.62) if hinge_left else \
            (u1 - (u1 - u0) * 0.62, u1 + 0.02)
        for zc in lz:
            face(b, w, bn + 0.003, hu0, hu1, zc - 0.022, zc + 0.022, conf, mats.iron)
        if latch:
            lu = u1 - 0.12 if hinge_left else u0 + 0.05
            zl = z0 + (z1 - z0) * 0.5
            face(b, w, leaf_n + 0.004, lu, lu + 0.07, zl - 0.015, zl + 0.015, conf,
                 mats.iron)


def board_shutter(b, w: Wall, u0: float, u1: float, z0: float, z1: float, conf: float,
                  mats: Mats, boards: int = 3) -> None:
    """A closed board shutter over an opening, inside its casing — a loft door, a
    gable hatch, a store's back window at night. Boards and two ledges."""
    leaf_n = w.skin + PANE_BACK_M + 0.004
    face(b, w, leaf_n, u0, u1, z0, z1, conf, mats.door)
    bw = (u1 - u0) / boards
    joint = mats.dark if mats.dark >= 0 else mats.panel
    for k in range(1, boards):
        u = u0 + k * bw
        face(b, w, leaf_n + 0.002, u - 0.007, u + 0.007, z0, z1, conf, joint)
    for zc in (z0 + (z1 - z0) * 0.2, z1 - (z1 - z0) * 0.2):
        face(b, w, leaf_n + BATTEN_PROUD_M, u0 + 0.02, u1 - 0.02, zc - 0.05, zc + 0.05,
             conf, mats.door)


def open_shutter(b, w: Wall, u_hinge: float, width: float, z0: float, z1: float,
                 conf: float, mat: int, side: int, joint: int = -1) -> None:
    """A board shutter swung open flat against the wall beside its window, on the
    `side` (+1 toward +u) of the hinge. Two boards and a joint line."""
    n = w.skin + 0.012
    a, c = sorted((u_hinge, u_hinge + side * width))
    face(b, w, n, a, c, z0, z1, conf, mat)
    if joint >= 0:
        m = (a + c) / 2
        face(b, w, n + 0.002, m - 0.006, m + 0.006, z0, z1, conf, joint)


def glass_material_spec() -> tuple:
    """(rgba, roughness) of the town's pane: the sheet's `GLASS`, which is Glessner's."""
    return materials.GLASS.rgba, materials.GLASS.roughness
