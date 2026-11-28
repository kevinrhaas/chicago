"""T-3730: a light in a K01 gable roof's end parapet — 2130 Prairie's south gable.

The Chicagology print of 2140 Prairie (`chicagology_2140_photo_a`) shows 2130's south flank
carried up as a stone gable under the side-gabled front, and in it, just in front of the
ridge, one tall attic light: two sashes under a flat stone lintel on a stone sill, its sill
about the front's eave. K01's gable roof (`k01_gable_roof`, T-2459) carries each side wall up
as a K05 parapet joined into the roof's one solid, and until this module nothing could stand a
light in it (docs/LIBERTIES.md L-k01-2130-murdoch-3730).

A record names them on the end that carries them, `gable_roof.ends.<side>.lights`, each

  back_m          the light's centre, metres behind the street front's plane
  sill_m          its sill over grade
  clear_width_m   the clear hole
  clear_height_m

and each is built as the street dormers' lights are: the roof's union cut to K06's reveal depth
behind the parapet's face (the cut's back is the `window` role, which the K06 opening set in it
closes), then K06 sets its frame, two sashes, glass, blind and dark room and its stone sill in
the recess, and K01 lays its flat stone lintel over the head. The parapet stands on its wall
from the soffit up, so every light stands wholly in it: its sill 0.15 m over the soffit and its
lintel 0.1 m under the parapet's top line at both of its ends. `resolve` checks a record's lights
against the gable it names; `cutters` returns the recesses; `dress` sets the sashes.
"""

from __future__ import annotations

from types import SimpleNamespace

LIGHT_KEYS = {"back_m", "sill_m", "clear_width_m", "clear_height_m"}
LINTEL_M = 0.30          # K01's flat lintel over a light (k01_frontage.opening: proud_box y1 .. y1 + 0.30)
LINTEL_EAR_M = 0.12      # and its ears past either jamb
SILL_CLEAR_M = 0.15      # the light's sill over the soffit the parapet stands on
TOP_CLEAR_M = 0.10       # the lintel's top under the parapet's top line
CORNER_CLEAR_M = 0.30    # the lintel's ears clear of the wall's front and rear corners
PIER_M = 0.30            # between two lights' lintels on one gable


def line_y(ln, x: float) -> float:
    """The parapet's top line (k01_gable_roof.line, [(u, y), ...] rear to front) at u `x`: the
    lowest y it stands at there (a crow step's riser is two points at one u)."""
    ys = []
    for (a, ya), (b, yb) in zip(ln, ln[1:]):
        if b - a > 1e-9 and a - 1e-9 <= x <= b + 1e-9:
            ys.append(ya + (yb - ya) * (x - a) / (b - a))
        elif abs(b - a) <= 1e-9 and abs(x - a) <= 1e-9:
            ys += [ya, yb]
    if not ys:
        raise ValueError(f"u {x} is off the parapet's line")
    return min(ys)


def resolve(side: str, spec, *, depth: float, soffit: float, ln) -> list:
    """The record's `gable_roof.ends.<side>.lights`, checked against the parapet they stand in:
    `ln` is that parapet's top line, `soffit` the height it stands on its wall from. Returns
    [{"s_m", "sill_m", "width_m", "height_m"}], s along the wall from its own left end as the
    opening sees it (the south wall's s runs from the rear wall to the front, the north wall's
    from the front to the rear)."""
    from .k01_frontage_params import ParamError
    if not spec:
        return []
    if not isinstance(spec, list):
        raise ParamError(f"gable_roof.ends.{side}.lights is a list of lights")
    out = []
    for j, lt in enumerate(spec):
        what = f"gable_roof.ends.{side}.lights[{j}]"
        if not isinstance(lt, dict) or set(lt) != LIGHT_KEYS:
            raise ParamError(f"{what} takes {sorted(LIGHT_KEYS)}")
        b, sill = float(lt["back_m"]), float(lt["sill_m"])
        w, h = float(lt["clear_width_m"]), float(lt["clear_height_m"])
        if not 0.4 <= w <= 1.5 or not 0.6 <= h <= 2.5:
            raise ParamError(f"{what}: a light 0.4-1.5 m wide and 0.6-2.5 m high ({w} x {h})")
        u = depth - b
        u0, u1 = u - w / 2 - LINTEL_EAR_M, u + w / 2 + LINTEL_EAR_M
        if u0 < CORNER_CLEAR_M or u1 > depth - CORNER_CLEAR_M:
            raise ParamError(f"{what}: its lintel (u {u0:.2f}-{u1:.2f}) stands within {CORNER_CLEAR_M} m of "
                             f"the wall's corners (u 0-{depth})")
        if sill < soffit + SILL_CLEAR_M:
            raise ParamError(f"{what}: its sill at {sill} m stands under the parapet, which rises from the "
                             f"soffit at {soffit:.2f} m (it needs {SILL_CLEAR_M} m over it)")
        top = sill + h + LINTEL_M
        room = min(line_y(ln, u0), line_y(ln, u1)) - TOP_CLEAR_M
        if top > room + 1e-9:
            raise ParamError(f"{what}: its lintel's top at {top:.2f} m runs past the gable's top line "
                             f"({room + TOP_CLEAR_M:.2f} m at its ends, less {TOP_CLEAR_M} m)")
        for o in out:
            if abs(o["u_m"] - u) < (o["width_m"] + w) / 2 + 2 * LINTEL_EAR_M + PIER_M - 1e-9:
                raise ParamError(f"{what}: it leaves no {PIER_M} m between its lintel and the light at "
                                 f"{depth - o['u_m']:.2f} m behind the front")
        out.append({"u_m": round(u, 4), "sill_m": sill, "width_m": w, "height_m": h,
                    "s_m": round(u if side == "south" else depth - u, 4)})
    return sorted(out, key=lambda o: o["u_m"])


def frame_of(side: str, D: float, W: float):
    """The end wall's opening frame (origin, run, outward normal), as k01_frontage.build frames
    the side walls: the south from the rear corner along +u, the north from the front back."""
    if side == "south":
        return (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    return (D, 0.0, -W), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)


def _reveal(a, lt) -> float:
    return a.kit_reveal(SimpleNamespace(component="k01.opening.sash_flat", width_m=lt["width_m"],
                                        height_m=lt["height_m"]))


def cutters(a, k5) -> list:
    """The recesses the roof's union cuts: each light's hole, K06's reveal deep behind its
    parapet's face and 0.05 m out past it, its back the `window` the K06 opening closes."""
    p = a.p
    g = p.gable or {}
    P = k5.frame("z")
    W = p.width_m
    out = []
    for side, e in (g.get("ends") or {}).items():
        for lt in e.get("lights", ()):
            rev = _reveal(a, lt)
            x0, x1 = lt["u_m"] - lt["width_m"] / 2, lt["u_m"] + lt["width_m"] / 2
            y0, y1 = lt["sill_m"], lt["sill_m"] + lt["height_m"]
            rect = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            if side == "south":     # the face at z 0, outward +z: the back is the low end
                out.append(k5.extrude(rect, -rev, 0.05, P, "reveal", "window", "reveal"))
            else:                   # the face at z -W, outward -z: the back is the high end
                out.append(k5.extrude(rect, -W - 0.05, -W + rev, P, "reveal", "reveal", "window"))
    return out


def dress(a):
    """Each light's K06 window in its recess and its stone lintel: an opening in the gable's
    own face (`k01.wall.gable_end.<side>`), laid in the parapet's fabric — the front's stone on a
    flank the record lays in it (`stone_front.flanks`), the side walls' brick elsewhere."""
    from archetypes.k01_frontage_params import Opening
    p = a.p
    g = p.gable or {}
    D, W = p.depth_m, p.width_m
    flanks = (p.stone or {}).get("flanks") or ()
    for side, e in sorted((g.get("ends") or {}).items()):
        lights = e.get("lights") or ()
        if not lights:
            continue
        cid = f"k01.wall.gable_end.{side}"
        O, R, N = frame_of(side, D, W)
        a.instance(cid, "wall", {"length_m": D, "thickness_m": g["parapet_m"], "openings": len(lights),
                                 "side": side},
                   {"base": O, "top": (O[0], max(lt["sill_m"] + lt["height_m"] for lt in lights), O[2])})
        body = "rough_stone_trim" if side in flanks else "brick"
        for lt in lights:
            a.opening(Opening("k01.opening.sash_flat", cid, lt["s_m"], lt["sill_m"], lt["width_m"], lt["height_m"]),
                      (O, R, N), g["parapet_m"], body, "limestone_trim", cut=True)
