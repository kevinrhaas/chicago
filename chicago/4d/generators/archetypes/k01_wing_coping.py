"""T-3337: a rear wing's STONE-COPED GABLES — 1919 Prairie's rear ranges, off their pictures.

TICKET T-3337 (piece 1 of T-3303, of T-1907). Both Gatlin Institute plates (the 1913 almanac's and the
1919 programme's) draw the steep gables of 1919 Prairie's rear ranges along the north flank
carried up past the slate in a pale stone coping, finialled at their peaks and springing from
kneelers at their feet, as T-3301 found the street dormer's gable is. K01's wing gables were
plain slated verges. The record names it as a flank-gabled wing's `roof.coping` (resolved and
bounded by k01_frontage_params._wing_pitched, the street dormer's bounds) on the gable ends it
lists, and this module dresses each of those ends after the wing's roof is drawn, in the gable
face's own frame — s across the face, y up, d out of it — with the parts T-3301's dormer
coping lays (k01_dormer_coping):

  the coping   along each rake, a stone `thickness_m` deep over the slate's top line, from
               `depth_m` behind the gable's face to PROUD_M before the verge's face, the two
               rakes mitred at the apex
  kneelers     a block `kneeler_m` square at each foot, from under the eave's edge to over
               the coping's foot, its sides flush with the coping's
  the finial   a turned stone `finial_m` high on the apex (none at 0)

The wing's gable is K05's (k01_frontage.wing_roof): its slate's top line in the wall's plane
runs from the wall top at the wall line to the ridge, `top + (half - |s|) tan(pitch)`, and its
verge stands the deck's overhang out of the face. In the assembly's frame z = -v, so a wing's
south end (v0, K01's naming) is its z1 face, looking +z, and its north end (v1) its z0 face.
docs/LIBERTIES.md L-k01-1919-coped-wing-gables-3303 says what is read and what is reconstructed.
"""

from __future__ import annotations

import math

from .k01_dormer_coping import FINIAL_RADIUS, KNEELER_DROP_M, PROUD_M, SEAT_M
from .k01_frontage_params import wing_gable_span as _wing_gable_span


def _af():
    from . import k01_arched_front
    return k01_arched_front


def dress(a, w):
    """Each listed gable end of wing `w` (resolved): its coping, kneelers and finial."""
    af = _af()
    r = w["roof"]
    cp = r["coping"]
    u0, u1, v0, v1 = w["rect"]
    o, top = w["overhang_m"], w["top_m"]
    t = math.tan(math.radians(r["pitch_deg"]))
    conf = a.p.worst_conf("rear_wings", "footprint")
    half, wc = (u1 - u0) / 2, (u0 + u1) / 2
    S = half + o                                     # the eave's edge, each side of the apex
    cover = lambda s: top + (half - abs(s)) * t      # the slate's top line in the face's plane
    tv = cp["thickness_m"] * math.sqrt(1 + t * t)    # the coping's depth, measured plumb
    d0, d1 = -cp["depth_m"], o + PROUD_M
    kw = cp["kneeler_m"]
    mat = "limestone_trim"
    for end in cp["ends"]:
        # T-3354: a gable standing back from a flat end stands where its span starts
        gv0, gv1 = _wing_gable_span(w)
        z, sg_end = (-gv0, 1.0) if end == "south" else (-gv1, -1.0)
        R, N = (sg_end, 0.0, 0.0), (0.0, 0.0, sg_end)   # R x Y = N, out of the gable
        frame = ((wc, 0.0, z), R, N)
        seed = a.instance(f"k01.roof.wing_coping.{w['id']}.{end}", "roof",
                          {"span_m": round(u1 - u0, 4), "thickness_m": cp["thickness_m"],
                           "depth_m": cp["depth_m"], "kneeler_m": kw, "finial_m": cp["finial_m"],
                           "pitch_deg": r["pitch_deg"]},
                          {"apex": (wc, round(cover(0.0) + tv, 4), z)})
        for sg in (-1.0, 1.0):
            s0, s1 = sg * (S - kw), 0.0              # from the kneeler's inner face to the apex
            lo0, lo1 = cover(s0) - SEAT_M, cover(s1) - SEAT_M
            hi0, hi1 = cover(s0) + tv, cover(s1) + tv
            quad = [(s0, lo0), (s1, lo1), (s1, hi1), (s0, hi0)]
            for dd, hint in ((d1, (0, 0, 1)), (d0, (0, 0, -1))):
                af._face(a, mat, frame, [(s, y, dd) for s, y in quad], hint, seed, conf)
            for (sa, ya), (sb, yb), up in (((s0, hi0), (s1, hi1), 1), ((s0, lo0), (s1, lo1), -1)):
                af._face(a, mat, frame, [(sa, ya, d0), (sb, yb, d0), (sb, yb, d1), (sa, ya, d1)],
                         (sg * t * up, up, 0), seed, conf)
            ks0, ks1 = sorted((sg * S, s0))
            af._box(a, mat, frame, ks0, ks1, cover(sg * S) - KNEELER_DROP_M, cover(s0) + tv + 0.02,
                    d0, d1, seed, conf)
        fh = cp["finial_m"]
        if fh > 0:
            ya = cover(0.0) + tv
            dc = (d0 + d1) / 2
            rr = FINIAL_RADIUS
            af._box(a, mat, frame, -rr, rr, ya - 0.01, ya + 0.12 * fh, dc - rr, dc + rr, seed, conf,
                    skip=("bottom",))
            y1 = ya + 0.12 * fh
            af._frustum(a, mat, frame, 0.0, dc, y1, y1 + 0.38 * fh, rr * 0.55, rr * 0.8, seed, conf)
            af._frustum(a, mat, frame, 0.0, dc, y1 + 0.38 * fh, y1 + 0.5 * fh, rr * 0.8, rr * 0.4, seed, conf)
            af._frustum(a, mat, frame, 0.0, dc, y1 + 0.5 * fh, ya + fh, rr * 0.4, 0.004, seed, conf)
