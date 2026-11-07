"""T-3301: a street dormer's STONE-COPED GABLE — 1919 Prairie's, off its pictures.

TICKET T-3301 (piece 1 of T-1907). Both Gatlin Institute plates (1913, 1919) and the 2004
photograph of 1919 Prairie draw the broad street dormer's gable not with the kit's slated
verges but carried up in a pale stone coping along each rake, a kneeler block at each foot
where the coping springs, and a finial at the apex; the smaller one-light dormer beside it
is coped the same way. The record names it as its dormer's `coping` (resolved and bounded by
k01_frontage_params._dormer_coping) and every dormer in `dormer.also` inherits it.

The K05 dormer k01_frontage.roof raises is left as it is (its covering, verges and soffits
are the union's); this module dresses it after the union, in the dormer face's own frame —
s across the face (toward -z), y up, d out of it (+x, the street) — with:

  the coping   along each rake, a stone `thickness_m` deep over the covering's top line,
               from `depth_m` behind the face to `PROUD_M` before the verge's face, the two
               rakes mitred at the apex
  kneelers     a block `kneeler_m` square at each foot, from under the eave's edge to over
               the coping's foot, its sides flush with the coping's
  the finial   a turned stone `finial_m` high on the coping's apex (none at 0)

Every number is the record's or is named here; docs/LIBERTIES.md L-k01-1919-coped-dormers-3301
says what is read and what is reconstructed.
"""

from __future__ import annotations

import math

PROUD_M = 0.04          # the coping and kneelers before the verge's front edge
SEAT_M = 0.02           # the coping let down into the covering, so no light shows under it
KNEELER_DROP_M = 0.25   # a kneeler's foot under the eave's edge at the face's corner
FINIAL_RADIUS = 0.11    # the finial's widest turned ring, of its 0.4-0.9 m height


def _k01():
    from . import k01_frontage
    return k01_frontage


def _af():
    from . import k01_arched_front
    return k01_arched_front


def dress(a, d, g, roof_seed):
    """One dormer's coping, kneelers and finial: `d` its resolved record, `g` its geometry."""
    k, af = _k01(), _af()
    cp = d["coping"]
    conf = a.p.worst_conf("dormer")
    zc = (g["zs"] + g["zn"]) / 2
    R = (0.0, 0.0, -1.0)
    N = k._cross(R, k.Y)
    frame = ((g["xf"], 0.0, zc), R, N)
    half, dt, o = d["width_m"] / 2, g["dt"], g["overhang"]
    yde = g["yde"]
    S = half + o                                    # the eave's edge, each side of the centre
    cover = lambda s: yde + (half - abs(s)) * dt     # the covering's top line in the face's plane
    tv = cp["thickness_m"] * math.sqrt(1 + dt * dt)  # the coping's depth, measured plumb
    d0, d1 = -cp["depth_m"], d["verge_m"] + PROUD_M
    kw = cp["kneeler_m"]
    seed = a.instance("k01.roof.dormer_coping", "roof",
                      {"face_width_m": d["width_m"], "thickness_m": cp["thickness_m"], "depth_m": cp["depth_m"],
                       "kneeler_m": kw, "finial_m": cp["finial_m"], "pitch_deg": d["pitch_deg"]},
                      {"apex": (g["xf"], round(cover(0.0) + tv, 4), zc)})
    mat = "limestone_trim"
    for sg in (-1.0, 1.0):
        s0, s1 = sg * (S - kw), 0.0                  # from the kneeler's inner face to the apex
        lo0, lo1 = cover(s0) - SEAT_M, cover(s1) - SEAT_M
        hi0, hi1 = cover(s0) + tv, cover(s1) + tv
        quad = [(s0, lo0), (s1, lo1), (s1, hi1), (s0, hi0)]
        for dd, hint in ((d1, (0, 0, 1)), (d0, (0, 0, -1))):
            af._face(a, mat, frame, [(s, y, dd) for s, y in quad], hint, seed, conf)
        # its top and underside along the rake, the underside seen past the verge's edge
        for (sa, ya), (sb, yb), up in (((s0, hi0), (s1, hi1), 1), ((s0, lo0), (s1, lo1), -1)):
            af._face(a, mat, frame, [(sa, ya, d0), (sb, yb, d0), (sb, yb, d1), (sa, ya, d1)],
                     (sg * dt * up, up, 0), seed, conf)
        # the kneeler: a block from under the eave's edge to over the coping's foot
        ks0, ks1 = sorted((sg * S, s0))
        ky0 = cover(sg * S) - KNEELER_DROP_M
        ky1 = cover(s0) + tv + 0.02
        af._box(a, mat, frame, ks0, ks1, ky0, ky1, d0, d1, seed, conf)
    # the finial: a turned stone on the coping's apex
    fh = cp["finial_m"]
    if fh > 0:
        ya = cover(0.0) + tv
        dc = (d0 + d1) / 2
        r = FINIAL_RADIUS
        af._box(a, mat, frame, -r, r, ya - 0.01, ya + 0.12 * fh, dc - r, dc + r, seed, conf, skip=("bottom",))
        y1 = ya + 0.12 * fh
        af._frustum(a, mat, frame, 0.0, dc, y1, y1 + 0.38 * fh, r * 0.55, r * 0.8, seed, conf)
        af._frustum(a, mat, frame, 0.0, dc, y1 + 0.38 * fh, y1 + 0.5 * fh, r * 0.8, r * 0.4, seed, conf)
        af._frustum(a, mat, frame, 0.0, dc, y1 + 0.5 * fh, ya + fh, r * 0.4, 0.004, seed, conf)
