"""Build the T-1801 proof assembly: one clapboard bay, one hewn-log pen, a recessed sash,
a painted signboard and a plank walk, through the town's own glTF path.

Run with the project's pinned Blender (tools/fabric_proof_1835.sh does this for you)::

    blender -b -noaudio --factory-startup --python tools/build_fabric_proof_1835.py -- \
      --out /tmp/fabric-proof-1835/fabric_proof_1835.glb

**It is a proof, not a building.** Nothing here is a record, nothing is placed in the
town, and nothing is read by `generators/build.py`, `mesh_inputs.py` or the staleness
gate. It exists so T-1210-T-1213 can start from an inspected surface rather than a memo
(T-1769's stop condition). Every dimension is the town's own where the town has one:

* the clapboard lap is `frame_dwelling._clapboard`'s profile -- `CLAPBOARD_LIP_M` proud,
  dropping 0.02 m, a course every `siding_exposure_m` -- and its butt joints come off
  `frame_dwelling._joint_positions` on the 16 in balloon-frame stud module;
* the log pen IS `logwork.hewn_log_wall`, called as `log_dwelling` calls it;
* the sash is `frame_dwelling.WIN_W_M` x `WIN_H_M`, six-over-six, and the glass is
  `common.materials.GLASS` for colour -- what is NEW is that it is recessed 0.10 m into
  the wall and enclosed by a dark room 0.60 m deep (Glessner v4's method, scaled to
  1835 sash), rather than a dark panel standing proud of a trim board;
* the signboard is `log_dwelling`/`frame_storefront`'s `SIGN_RGBA` board, framed;
* the walk boards are 0.25 m with a 12 mm gap, laid across the walk as frontage.js
  lays them.

The materials name their substrate (`wall_clapboard`, not `wall`) -- the proof is free
to, because it is not a town asset. Route 1 of the preparation map's section 5
proposes the same for the town as a docs/GLB-CONTRACT.md change; this file does not
make it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

import bpy  # noqa: E402

import emit  # noqa: E402
from archetypes import frame_dwelling as fd  # noqa: E402
from archetypes import log_dwelling as ld  # noqa: E402
from common import logwork, materials  # noqa: E402
from common.mesh import MeshBuilder, reset_scene, simple_material  # noqa: E402

CONF = 0.25          # reconstructed: a proof surface, not a claim about a building
(M_CLAP, M_LOG, M_CHINK, M_TRIM, M_SASH, M_GLASS, M_DARK, M_SIGN,
 M_DECK) = range(9)

BAY_X0, BAY_X1 = 0.0, 4.80   # wider than CLAPBOARD_RUN_M, so a course has a butt joint
WALL_T = 0.15
Z_LO, Z_HI = 0.30, 3.10
WIN_W, WIN_H = fd.WIN_W_M, fd.WIN_H_M
WIN_SILL = 1.00
RECESS = 0.10        # wall face to the glass
ROOM = 0.60          # the enclosed dark room behind the glass
SASH_BAR = 0.05
MUNTIN = 0.022


def rect_y(b, y, x0, x1, z0, z1, mat, outward=-1):
    """A rectangle in the plane y=const facing `outward` (-1 = towards the street)."""
    fd._panel(b, "y", y, x0, x1, z0, z1, outward, CONF, mat)


def rect_x(b, x, y0, y1, z0, z1, mat, outward):
    fd._panel(b, "x", x, y0, y1, z0, z1, outward, CONF, mat)


def rect_z(b, z, x0, x1, y0, y1, mat, up):
    pts = [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)]
    if not up:
        pts.reverse()
    b.add_poly(pts, CONF, mat)


def clapboard_bay(b):
    """The wall, its lap courses and joints, with a real hole for the sash."""
    u0 = (BAY_X0 + BAY_X1) / 2 - WIN_W / 2
    u1 = u0 + WIN_W
    zs, zh = WIN_SILL, WIN_SILL + WIN_H
    # front face in four pieces round the opening
    rect_y(b, 0.0, BAY_X0, u0, Z_LO, Z_HI, M_CLAP)
    rect_y(b, 0.0, u1, BAY_X1, Z_LO, Z_HI, M_CLAP)
    rect_y(b, 0.0, u0, u1, Z_LO, zs, M_CLAP)
    rect_y(b, 0.0, u0, u1, zh, Z_HI, M_CLAP)
    # the rest of the block: ends, top, back
    b.add_box(BAY_X0, 0.0, Z_LO, BAY_X1, WALL_T, Z_HI, CONF, M_CLAP, skip=("front", "bottom"))
    # lap courses, as _clapboard draws them, broken where the opening is
    lip = fd.CLAPBOARD_LIP_M
    p = SimpleNamespace(stud_spacing_m=0.406, siding_exposure_m=0.14)
    n = int((Z_HI - Z_LO) / p.siding_exposure_m)
    for i in range(1, n):
        z = Z_LO + i * p.siding_exposure_m
        if z > Z_HI - 0.02:
            break
        spans = [(BAY_X0, BAY_X1)]
        if zs - 0.02 < z < zh + 0.02:
            spans = [(BAY_X0, u0 - 0.09), (u1 + 0.09, BAY_X1)]
        for a, c in spans:
            b.add_poly([(a, 0.0, z), (c, 0.0, z), (c, -lip, z - 0.02), (a, -lip, z - 0.02)],
                       CONF, M_CLAP)
        for jx in fd._joint_positions(BAY_X0, BAY_X1, p.stud_spacing_m, i):
            if any(a + 0.05 < jx < c - 0.05 for a, c in spans):
                rect_y(b, -(lip + 0.006), jx - 0.015, jx + 0.015,
                       z - p.siding_exposure_m, z, M_CLAP)
    return u0, u1, zs, zh


def sash(b, u0, u1, zs, zh):
    """Casing, sill, reveal, a six-over-six sash at the back of it, glass, a dark room."""
    cas = 0.09
    yc = -fd.TRIM_RELIEF_M
    # casing: four boards standing off the siding, with their outer returns
    for (a, c, z0, z1) in ((u0 - cas, u0, zs, zh + cas), (u1, u1 + cas, zs, zh + cas),
                           (u0, u1, zh, zh + cas)):
        rect_y(b, yc, a, c, z0, z1, M_TRIM)
        rect_x(b, a, yc, 0.0, z0, z1, M_TRIM, -1)
        rect_x(b, c, yc, 0.0, z0, z1, M_TRIM, 1)
        rect_z(b, z1, a, c, yc, 0.0, M_TRIM, True)
    # sill: projects and drips
    b.add_box(u0 - cas - 0.03, -0.07, zs - 0.045, u1 + cas + 0.03, 0.0, zs,
              CONF, M_TRIM, skip=("back",))
    # reveal: the four jambs of the hole, wall face back to the glass plane
    rect_x(b, u0, 0.0, RECESS, zs, zh, M_TRIM, 1)
    rect_x(b, u1, 0.0, RECESS, zs, zh, M_TRIM, -1)
    rect_z(b, zs, u0, u1, 0.0, RECESS, M_TRIM, True)
    rect_z(b, zh, u0, u1, 0.0, RECESS, M_TRIM, False)
    # glass, one plane behind the bars
    yg = RECESS + 0.012
    rect_y(b, yg, u0, u1, zs, zh, M_GLASS)
    # sash bars: stiles, rails, the meeting rail and the muntins, as thin boxes
    yb0, yb1 = RECESS - 0.010, RECESS + 0.010
    mid = (zs + zh) / 2

    def bar(x0, x1, z0, z1):
        b.add_box(x0, yb0, z0, x1, yb1, z1, CONF, M_SASH, skip=("back",))
    bar(u0, u0 + SASH_BAR, zs, zh)
    bar(u1 - SASH_BAR, u1, zs, zh)
    bar(u0 + SASH_BAR, u1 - SASH_BAR, zs, zs + SASH_BAR)
    bar(u0 + SASH_BAR, u1 - SASH_BAR, zh - SASH_BAR, zh)
    bar(u0 + SASH_BAR, u1 - SASH_BAR, mid - 0.025, mid + 0.025)
    for k in (1, 2):
        x = u0 + SASH_BAR + k * (WIN_W - 2 * SASH_BAR) / 3
        bar(x - MUNTIN / 2, x + MUNTIN / 2, zs + SASH_BAR, mid - 0.025)
        bar(x - MUNTIN / 2, x + MUNTIN / 2, mid + 0.025, zh - SASH_BAR)
    for zc in ((zs + SASH_BAR + mid - 0.025) / 2, (mid + 0.025 + zh - SASH_BAR) / 2):
        bar(u0 + SASH_BAR, u1 - SASH_BAR, zc - MUNTIN / 2, zc + MUNTIN / 2)
    # the enclosed room: five inward faces, so the glass shows depth and never the sky
    y0, y1 = WALL_T, WALL_T + ROOM
    rect_y(b, y1, u0 - 0.4, u1 + 0.4, zs - 0.3, zh + 0.3, M_DARK, -1)
    rect_x(b, u0 - 0.4, y0, y1, zs - 0.3, zh + 0.3, M_DARK, 1)
    rect_x(b, u1 + 0.4, y0, y1, zs - 0.3, zh + 0.3, M_DARK, -1)
    rect_z(b, zs - 0.3, u0 - 0.4, u1 + 0.4, y0, y1, M_DARK, True)
    rect_z(b, zh + 0.3, u0 - 0.4, u1 + 0.4, y0, y1, M_DARK, False)
    # the hole through the wall's own thickness between the glass and the room
    rect_x(b, u0, RECESS, WALL_T, zs, zh, M_DARK, 1)
    rect_x(b, u1, RECESS, WALL_T, zs, zh, M_DARK, -1)


def signboard(b):
    """A framed board on the siding above the sash: SIGN_RGBA's board, painted by the page."""
    x0, x1, z0, z1 = 1.20, 3.60, 2.52, 2.92
    y_face = -0.055
    b.add_box(x0, y_face, z0, x1, -0.02, z1, CONF, M_SIGN, skip=("back",))
    m = 0.035
    for (a, c, za, zb) in ((x0 - m, x1 + m, z1, z1 + m), (x0 - m, x1 + m, z0 - m, z0),
                           (x0 - m, x0, z0, z1), (x1, x1 + m, z0, z1)):
        b.add_box(a, y_face - 0.012, za, c, -0.02, zb, CONF, M_TRIM, skip=("back",))


def plank_walk(b):
    """Boards laid across the walk in front of the bay, on two stringers."""
    w, gap, top = 0.25, 0.012, Z_LO - 0.02
    x = BAY_X0
    while x + w <= BAY_X1 + 1e-6:
        b.add_box(x, -1.45, top - 0.05, x + w, -0.04, top, CONF, M_DECK, skip=("bottom",))
        x += w + gap
    for y in (-1.30, -0.25):
        b.add_box(BAY_X0, y - 0.075, 0.0, BAY_X1, y + 0.075, top - 0.05, CONF, M_DECK,
                  skip=("bottom", "top"))


def flat_opening(b, u0, u1, zs, zh):
    """The town's opening today, for the comparison: `frame_dwelling._opening`, a dark
    panel standing just proud of a trim surround, over a wall that is closed behind it."""
    rect_y(b, 0.0, u0, u1, zs, zh, M_CLAP)
    off = fd.TRIM_RELIEF_M + 0.010
    m = 0.075
    rect_y(b, -off, u0 - m, u1 + m, zs - m, zh + m, M_TRIM)
    rect_y(b, -(off + 0.006), u0, u1, zs, zh, M_DARK)


def build(out: Path, opening: str = "recessed") -> dict:
    reset_scene()
    b = MeshBuilder("fabric_proof_1835")
    u0, u1, zs, zh = clapboard_bay(b)
    if opening == "flat":
        flat_opening(b, u0, u1, zs, zh)
    else:
        sash(b, u0, u1, zs, zh)
    signboard(b)
    plank_walk(b)
    # the pen, eight courses, called the way log_dwelling calls it
    logwork.hewn_log_wall(b, 5.90, 0.0, 8.90, 2.20, 0.0, 8 * logwork.COURSE_M, CONF,
                          M_LOG, M_CHINK)

    unpainted = materials.FINISHES["unpainted"]
    glass = simple_material("glass", materials.GLASS.rgba, roughness=0.05)
    bsdf = glass.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs["Transmission Weight"].default_value = 0.94
    bsdf.inputs["IOR"].default_value = 1.52
    mats = [
        simple_material("wall_clapboard", unpainted.rgba, roughness=0.86),
        simple_material("log", ld.HEWN_RGBA, roughness=materials.SUBSTRATES["hewn_log"].roughness),
        simple_material("chinking", ld.CHINK_RGBA, roughness=materials.SUBSTRATES["chinking"].roughness),
        simple_material("trim", materials.FINISHES["white_paint"].rgba, roughness=0.60),
        simple_material("sash", materials.FINISHES["white_paint"].rgba, roughness=0.60),
        glass,
        simple_material("dark", materials.DARK.rgba, roughness=materials.DARK.roughness),
        simple_material("sign", ld.SIGN_RGBA, roughness=0.85),
        simple_material("deck", materials.FINISHES["weathered_board"].rgba, roughness=0.94),
    ]
    ob = b.to_object(mats)
    emit.unwrap(ob)
    emit.export_glb(ob, "fabric_proof_1835", "proof", out)
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    per = {}
    for p in ob.data.polygons:
        k = mats[p.material_index].name
        per[k] = per.get(k, 0) + len(p.vertices) - 2
    return {"glb": str(out), "opening": opening, "triangles": tris,
            "triangles_by_material": per}


def main() -> int:
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--opening", choices=("recessed", "flat"), default="recessed",
                    help="flat = the town's current opening, for the comparison")
    a = ap.parse_args(argv)
    info = build(a.out, a.opening)
    a.out.with_suffix(".build.json").write_text(json.dumps(info, indent=2) + "\n")
    print("PROOF", json.dumps(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
