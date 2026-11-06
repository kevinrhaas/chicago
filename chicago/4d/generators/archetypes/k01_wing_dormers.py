"""T-3354: a rear wing's PINNACLED DORMERS — 1919 Prairie's rear range, off the three Gatlin plates.

All three Gatlin Institute plates of 1919 Prairie (the 1912 Blue Book's, the 1913 almanac's and
the 1919 programme's) draw two small, tall dormers on the rear range's slope that faces Prairie
Avenue, just behind the flat-topped two-storey blocks along the north flank: each a narrow face
with one tall dark light, under a steep gable finialled at its peak, a pinnacle standing at each
shoulder. Through the three solved cameras both land on the same two places on that slope, in all
three within a few pixels. K01 built dormers only on the main roof's hip and front; this module
stands them on a flank-gabled wing's street slope (`rear_wings[].roof.dormers`, resolved and
bounded by k01_frontage_params._wing_dormers).

Each dormer is drawn after the wing's roof, in its face's own frame — s across the face (along v),
y up, d out of it toward the street (+u) — with the slope's top line falling `t` a metre as d
runs back into the roof:

  the face      the wing's walling, from where the slope meets it to the dormer's eave, then
                its gable; one light cut in it, `light` wide and high from its sill, in a
                stone reveal, dark behind its glass
  the cheeks    walling triangles from the face back to where the eave line meets the slope
  the roof      two slated planes from the face's rakes back to their valleys on the slope
  coping        a stone coping up both rakes, `proud_m` before the face and `back_m` over the
                slate (k01.roof.dormer_coping, as T-3293's dormers' is)
  pinnacles     a square stone shaft engaged at each edge of the face, from the slope to
                `rise_m` past the eave, under a cap and a pyramid (k01.roof.gable_pinnacle)
  the finial    a turned stone finial on the coping's apex (k01.roof.gable_finial)

The wing's slate is not cut under a dormer: the face, cheeks and roof close on the slope, and
the light's backing closes the room behind the glass. docs/LIBERTIES.md
L-k01-1919-range-dormers-3354 says what is read and what is reconstructed.
"""

from __future__ import annotations

import math

LIGHT_REVEAL_M = 0.15     # the light's stone reveal, face to backing
GLASS_BACK_M = 0.08       # the glass, this far behind the face
SILL_M = (0.07, 0.08)     # the light's stone sill: proud of the face, and its depth
COPING_SINK_M = 0.02      # as K01's dormer coping: let into the rake


def _af():
    from . import k01_arched_front
    return k01_arched_front


def dress(a, w):
    """Each dormer on wing `w`'s street slope (resolved `roof.dormers`)."""
    from .k01_wall_gable import _pyramid, PIN_CAP_PROUD_M, FINIAL_SINK_M
    af = _af()
    r = w["roof"]
    u0, u1, v0, v1 = w["rect"]
    top = w["top_m"]
    t = math.tan(math.radians(r["pitch_deg"]))
    conf = a.p.worst_conf("rear_wings", "footprint")
    walling = "brick"
    stone = "limestone_trim"
    for i, dm in enumerate(r["dormers"]):
        uf = u1 - dm["setback_m"]
        yf = top + dm["setback_m"] * t                  # the slope's top line in the face
        hw = dm["width_m"] / 2
        ye = dm["eave_m"]
        td = math.tan(math.radians(dm["pitch_deg"]))
        ya = ye + hw * td
        db, dr = -(ye - yf) / t, -(ya - yf) / t         # where the eave line and the ridge meet the slope
        R, N = (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)        # s along v, d toward the street; R x Y = N
        Fr = ((uf, 0.0, -dm["v_m"]), R, N)
        seed = a.instance(f"k01.roof.wing_dormer.{w['id']}.{i}", "roof",
                          {"width_m": dm["width_m"], "eave_m": ye, "pitch_deg": dm["pitch_deg"],
                           "setback_m": dm["setback_m"], "light_m": [dm["light"]["width_m"], dm["light"]["height_m"]],
                           "slope_pitch_deg": r["pitch_deg"]},
                          {"foot": af._P(Fr, 0.0, yf, 0.0), "apex": af._P(Fr, 0.0, ya, 0.0)})
        lt = dm["light"]
        lw, ly0 = lt["width_m"] / 2, lt["sill_m"]
        ly1 = ly0 + lt["height_m"]
        # the face round its light, and its gable
        for poly in ([(-hw, yf), (hw, yf), (hw, ly0), (-hw, ly0)],
                     [(-hw, ly0), (-lw, ly0), (-lw, ly1), (-hw, ly1)],
                     [(lw, ly0), (hw, ly0), (hw, ly1), (lw, ly1)],
                     [(-hw, ly1), (hw, ly1), (hw, ye), (0.0, ya), (-hw, ye)]):
            af._face(a, walling, Fr, [(s, y, 0.0) for s, y in poly], (0, 0, 1), seed, conf)
        # the light: its reveal, the dark room behind it, its glass and its sill
        rv = -LIGHT_REVEAL_M
        af._face(a, stone, Fr, [(-lw, ly0, 0.0), (lw, ly0, 0.0), (lw, ly0, rv), (-lw, ly0, rv)], (0, 1, 0), seed, conf)
        af._face(a, stone, Fr, [(-lw, ly1, 0.0), (lw, ly1, 0.0), (lw, ly1, rv), (-lw, ly1, rv)], (0, -1, 0), seed, conf)
        af._face(a, stone, Fr, [(-lw, ly0, 0.0), (-lw, ly1, 0.0), (-lw, ly1, rv), (-lw, ly0, rv)], (1, 0, 0), seed, conf)
        af._face(a, stone, Fr, [(lw, ly0, 0.0), (lw, ly1, 0.0), (lw, ly1, rv), (lw, ly0, rv)], (-1, 0, 0), seed, conf)
        af._face(a, "backing", Fr, [(-lw, ly0, rv), (lw, ly0, rv), (lw, ly1, rv), (-lw, ly1, rv)], (0, 0, 1), seed, conf)
        af._face(a, "glass", Fr, [(-lw, ly0, -GLASS_BACK_M), (lw, ly0, -GLASS_BACK_M), (lw, ly1, -GLASS_BACK_M),
                                  (-lw, ly1, -GLASS_BACK_M)], (0, 0, 1), seed, conf)
        sp, sd = SILL_M
        af._box(a, stone, Fr, -lw - 0.05, lw + 0.05, ly0 - sd, ly0, -0.02, sp, seed, conf, skip=("back",))
        # the cheeks, from the face back to where the eave line meets the slope
        for sg in (-1.0, 1.0):
            af._face(a, walling, Fr, [(sg * hw, yf, 0.0), (sg * hw, ye, 0.0), (sg * hw, ye, db)], (sg, 0, 0), seed, conf)
            # the dormer's slated roof, from its rake back to its valley on the slope
            af._face(a, "wing_slate", Fr, [(sg * hw, ye, 0.0), (0.0, ya, 0.0), (0.0, ya, dr), (sg * hw, ye, db)],
                     (sg * td, 1.0, 0.0), seed, conf)
        # the stone coping up both rakes, a chevron proud of the face and back over the slate
        cp = dm["coping"]
        gp = math.atan(td)
        h, k0 = cp["width_m"] / math.cos(gp), COPING_SINK_M
        d0, d1 = -cp["back_m"], cp["proud_m"]
        cseed = a.instance("k01.roof.dormer_coping", "roof",
                           {"width_m": cp["width_m"], "proud_m": d1, "back_m": cp["back_m"], "crockets": 0,
                            "wing": w["id"]},
                           {"apex": af._P(Fr, 0.0, ya, 0.0)})
        lo = [(-hw, ye - k0), (0.0, ya - k0), (hw, ye - k0)]
        hi = [(hw, ye + h - k0), (0.0, ya + h - k0), (-hw, ye + h - k0)]
        outline = lo + hi
        for half in ([lo[0], lo[1], hi[1], hi[2]], [lo[1], lo[2], hi[0], hi[1]]):
            af._face(a, stone, Fr, [(s, y, d1) for s, y in half], (0, 0, 1), cseed, conf)
            af._face(a, stone, Fr, [(s, y, d0) for s, y in half], (0, 0, -1), cseed, conf)
        n = len(outline)
        for k in range(n):
            (s0, y0), (s1, y1) = outline[k], outline[(k + 1) % n]
            af._face(a, stone, Fr, [(s0, y0, d0), (s1, y1, d0), (s1, y1, d1), (s0, y0, d1)],
                     (y1 - y0, -(s1 - s0), 0.0), cseed, conf)
        # a pinnacle at each edge of the face
        pn = dm["pinnacles"]
        q0 = pn["shaft_m"] / 2
        py0, py1 = yf - q0 * t - 0.02, ye + pn["rise_m"]   # from the slope before the face
        for s in (-hw, hw):
            pseed = a.instance("k01.roof.gable_pinnacle", "roof",
                               {"shaft_m": pn["shaft_m"], "top_m": round(py1, 4), "cap_m": pn["cap_m"],
                                "spire_m": pn["spire_m"], "dormer": True, "wing": w["id"]},
                               {"foot": af._P(Fr, s, py0, 0.0)})
            af._box(a, stone, Fr, s - q0, s + q0, py0, py1, -q0, q0, pseed, conf, skip=("top",))
            q = q0 + PIN_CAP_PROUD_M
            af._box(a, stone, Fr, s - q, s + q, py1, py1 + pn["cap_m"], -q, q, pseed, conf)
            _pyramid(a, stone, Fr, s, 0.0, py1 + pn["cap_m"], q0, py1 + pn["cap_m"] + pn["spire_m"], pseed, conf)
        # the finial on the coping's apex
        fh = dm["finial_m"]
        if fh > 0:
            yb = ya - FINIAL_SINK_M + h - k0
            dc = (d0 + d1) / 2
            rr = 0.07
            fseed = a.instance("k01.roof.gable_finial", "roof", {"height_m": fh, "radius_m": rr, "dormer": True,
                                                                  "wing": w["id"]},
                               {"foot": af._P(Fr, 0.0, yb, dc)})
            for (fa, fb, ra_, rb) in ((0.0, 0.2, 0.6, 0.6), (0.2, 0.3, 0.6, 1.0), (0.3, 0.45, 1.0, 0.45),
                                      (0.45, 0.6, 0.45, 0.8), (0.6, 0.7, 0.8, 0.3), (0.7, 1.0, 0.3, 0.03)):
                af._frustum(a, stone, Fr, 0.0, dc, yb + fa * fh, yb + fb * fh, rr * ra_, rr * rb, fseed, conf)
