"""Resolve a k16_timber structure record into what the K16 builder reads (T-2323).

A record of this archetype names the timber street front of ONE house, built from the K16
kit (data/components/prairie_1904/k16_timber.json), and the plain body it stands against.
Its phase's `form` carries each as an attested-shaped entry:

    layout       which street the front faces, and the gap left between abutting parts
    gable        a kit `gable` variant in full: the front gable, its shingle bands, its sash
    wing_wall    a kit `clapboard_wall` variant in full: the wall beside it, with its corner
    porch        a kit `porch` variant in full, built as two halves mirrored about its middle
    body         the envelope behind the front: depths, roof pitch, colour; with
                 `timber_walls` (T-2395) closed in kit clapboard and roofed, else a stand-in
    canted_bay   optional: a plain bay standing on the gable front's ground storey; with
                 `lights` (T-2424) built in kit timber, a pointed light in each face
    roof_covering optional: the roof's colour
    basement     optional (T-2523): `height_m`, the basement storey the whole house stands
                 on; every other height in the record is over its top, the porch floor and
                 stoop come down to grade, and the foundations run on down to grade

OR, since T-2357, a WHOLE small frame house closed on every face from the kit:

    frame_house  blocks in the lot plan frame (u toward the street, v along it), each a
                 closed run of `clapboard_wall`s with its cased sash and doors under a
                 boxed, bracketed eave and a hip or flat roof; the kit porch on the street
                 wall with its steps; one brick stack
    roof_covering optional: the roof's colour

Nothing here imports Blender; `generators/mesh_inputs.py` hashes the dataclass this
returns, so every field the builder reads is in it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from archetypes.k01_frontage_params import CONFIDENCE_VALUE

REQUIRED = ("layout", "gable", "wing_wall", "porch", "body")
OPTIONAL = ("canted_bay", "roof_covering", "tower", "boundary", "basement", "yard")
#: The form attributes that reach the mesh. `stories` and `construction` are stated on a
#: record for the card and declare `geometry: simplified`.
# T-2357: the whole-house layout, read instead of the front's five
HOUSE_REQUIRED = ("frame_house",)
HOUSE_OPTIONAL = ("roof_covering",)
CONSUMED = frozenset(REQUIRED + OPTIONAL + HOUSE_REQUIRED)
SIDES = ("east", "north", "west", "south")   # counter-clockwise from above, the walls' order
ROOFS = ("hip", "flat", "gable")   # T-2398: a gable, its ridge along u or v
KINDS = {"gable": "gable", "wing_wall": "clapboard_wall", "porch": "porch"}
BODY_KEYS = ("gable_depth_m", "wing_depth_m", "wing_roof_pitch_deg", "roof_under_m")
#: T-2395: the faces of a timber body — the gable range's flanks and rear gable, the wing's
#: north side and back wall
TIMBER_WALLS = ("south", "north", "rear", "wing_north", "wing_rear")


class ParamError(ValueError):
    pass


@dataclass
class K16TimberParams:
    layout: dict | None = None
    gable: dict | None = None
    wing_wall: dict | None = None
    porch: dict | None = None
    body: dict | None = None
    canted_bay: dict | None = None
    roof_covering: dict | None = None
    tower: dict | None = None
    boundary: dict | None = None
    basement: dict | None = None
    yard: dict | None = None
    frame_house: dict | None = None
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]


def from_phase(phase: dict, record: dict | None = None) -> K16TimberParams:
    rid = f"{(record or {}).get('id')}/{phase.get('id')}"
    form = phase.get("form") or {}
    if "frame_house" in form:
        bad = frame_house_errors(form["frame_house"]["value"])
        if bad:
            raise ParamError(f"{rid}: frame_house: {'; '.join(bad)}")
        return K16TimberParams(
            frame_house=dict(form["frame_house"]["value"]),
            **{k: dict(form[k]["value"]) for k in HOUSE_OPTIONAL if k in form},
            confidence={k: form[k]["confidence"] for k in HOUSE_REQUIRED + HOUSE_OPTIONAL if k in form},
        )
    missing = [k for k in REQUIRED if k not in form]
    if missing:
        raise ParamError(f"{rid}: form lacks {', '.join(missing)}")
    for k, kind in KINDS.items():
        if form[k]["value"].get("kind") != kind:
            raise ParamError(f"{rid}: {k} must be a kit {kind!r} variant, not {form[k]['value'].get('kind')!r}")
    if form["layout"]["value"].get("faces") not in ("east", "south"):
        raise ParamError(f"{rid}: layout.faces must be east or south")
    body = form["body"]["value"]
    bad = [k for k in BODY_KEYS if not isinstance(body.get(k), (int, float)) or body[k] < 0]
    if bad:
        raise ParamError(f"{rid}: body needs non-negative {', '.join(bad)}")
    tw = body.get("timber_walls")
    if tw is not None:     # T-2395: the body closed in kit timber instead of a stand-in
        missing = [k for k in TIMBER_WALLS if not isinstance(tw.get(k), dict)]
        if missing:
            raise ParamError(f"{rid}: body.timber_walls lacks {', '.join(missing)}")
        for k in TIMBER_WALLS:
            for w in tw[k].get("windows", []):
                if not all(_num(w.get(x)) for x in ("clear_height_m", "sill_m", "centre_m")):
                    raise ParamError(f"{rid}: body.timber_walls.{k}: a window needs clear_height_m, sill_m, centre_m")
        errs = annex_errors(body, form["gable"]["value"]["width_m"])
        if errs:
            raise ParamError(f"{rid}: body: " + "; ".join(errs))
    bad = gable_errors(form["gable"]["value"])
    if bad:
        raise ParamError(f"{rid}: gable: {'; '.join(bad)}")
    if "tower" in form:     # T-2396: the corner tower over the porch
        bad = tower_errors(form["tower"]["value"])
        if bad:
            raise ParamError(f"{rid}: tower: {'; '.join(bad)}")
    if "boundary" in form:     # T-2456: the street fence and its gate piers
        bad = boundary_errors(form["boundary"]["value"])
        if bad:
            raise ParamError(f"{rid}: boundary: {'; '.join(bad)}")
    if "yard" in form:     # T-3222: a K14 front walk through the boundary's gateway
        bad = yard_errors(form["yard"]["value"], "boundary" in form)
        if bad:
            raise ParamError(f"{rid}: yard: {'; '.join(bad)}")
    if "basement" in form:     # T-2523
        bad = basement_errors(form["basement"]["value"])
        if bad:
            raise ParamError(f"{rid}: basement: {'; '.join(bad)}")
    if "canted_bay" in form and "lights" in form["canted_bay"]["value"]:     # T-2424
        bad = bay_errors(form["canted_bay"]["value"])
        if bad:
            raise ParamError(f"{rid}: canted_bay: {'; '.join(bad)}")
    for k, fv in form.items():     # T-2520: a door's transom light
        doors = fv["value"].get("doors") if isinstance(fv, dict) and isinstance(fv.get("value"), dict) else None
        for d in doors or []:
            bad = transom_errors(d)
            if bad:
                raise ParamError(f"{rid}: {k}: door transom: {'; '.join(bad)}")
    if not isinstance(form["porch"]["value"].get("half_width_m"), (int, float)):
        raise ParamError(f"{rid}: porch needs half_width_m")
    bad = porch_errors(form["porch"]["value"])
    if bad:
        raise ParamError(f"{rid}: porch: {'; '.join(bad)}")
    return K16TimberParams(
        **{k: dict(form[k]["value"]) for k in REQUIRED},
        **{k: dict(form[k]["value"]) for k in OPTIONAL if k in form},
        confidence={k: form[k]["confidence"] for k in REQUIRED + OPTIONAL if k in form},
    )


def yard_errors(yv: dict, has_boundary: bool) -> list[str]:
    """T-3222: a K16 yard is a K14 front walk alone — no lawn or service walk is laid — from the
    porch stair's foot in through the boundary's gateway (k16_timber.yard_walk)."""
    out = [] if has_boundary else ["a yard's walk comes in through the boundary's gateway, and the form names none"]
    if yv.get("kit") != "k14_condition" or not _num(yv.get("built")):
        out.append("names kit 'k14_condition' and the year its ground is worn from ('built')")
    if set(yv) - {"kit", "built", "front_walk", "grade_m"}:
        out.append(f"takes kit, built, front_walk and grade_m alone; {sorted(set(yv))}")
    fw = yv.get("front_walk") or {}
    if fw.get("surface") != "stone_flags":
        out.append("front_walk is laid in 'stone_flags'")
    if not (_num(fw.get("width_m")) and 0.9 <= fw["width_m"] <= 3.0):
        out.append("front_walk.width_m is 0.9-3.0 m")
    if not (_num(fw.get("flag_m")) and 0.3 <= fw["flag_m"] <= 1.8):
        out.append("front_walk.flag_m is a flag's length, 0.3-1.8 m")
    if not (_num(fw.get("top_m")) and 0.035 < fw["top_m"] <= 0.1):
        out.append("front_walk.top_m stands a flag over the ground, and no more than 0.1 m")
    if not (_num(fw.get("wear_tone")) and 0.62 <= fw["wear_tone"] <= 1.0):
        out.append("front_walk.wear_tone is 0.62-1.0, the kit's floor up")
    return out


#: T-2456: what a street fence and its gate piers need
BOUNDARY_NUMS = ("street_line_m", "end_clear_m")
PIER_NUMS = ("plinth_m", "plinth_top_m", "section_m", "shaft_top_m")


def boundary_errors(bv: dict) -> list[str]:
    out = [f"needs a positive {k}" for k in BOUNDARY_NUMS if not (_num(bv.get(k)) and bv[k] > 0)]
    lot = bv.get("lot_s_m")
    if not (isinstance(lot, list) and len(lot) == 2 and all(_num(x) for x in lot) and lot[0] < 0 < lot[1]):
        return out + ["lot_s_m must be [south line, north line] about the front's south end"]
    b, f, pv = bv.get("base") or {}, bv.get("bars") or {}, bv.get("pier") or {}
    if not (_num(b.get("height_m")) and 0.05 <= b["height_m"] <= 0.6 and _num(b.get("width_m")) and b["width_m"] > 0):
        out.append("base needs height_m (0.05-0.6) and width_m")
    if not (_num(f.get("pitch_m")) and 0.08 <= f["pitch_m"] <= 0.4):
        out.append("bars.pitch_m must be 0.08-0.4 m")
    if not (_num(f.get("bar_m")) and 0.01 <= f["bar_m"] <= 0.05 and _num(f.get("rail_m")) and f["rail_m"] > 0):
        out.append("bars need bar_m (0.01-0.05) and rail_m")
    elif not (_num(f.get("height_m")) and _num(b.get("height_m")) and f["height_m"] - f["rail_m"] > b["height_m"]):
        out.append("bars.height_m must stand a rail over the base")
    if "first_m" in f and not (_num(f["first_m"]) and _num(f.get("bar_m")) and _num(f.get("pitch_m"))
                               and f["bar_m"] / 2 <= f["first_m"] <= f["pitch_m"]):
        out.append("bars.first_m (T-2524) puts the first bar off its pier's plinth: half a bar to one pitch")
    out += [f"pier needs a positive {k}" for k in PIER_NUMS if not (_num(pv.get(k)) and pv[k] > 0)]
    if out:
        return out
    if not pv["plinth_top_m"] < pv["shaft_top_m"] < pv["cap"]["top_m"] < pv["finial"]["top_m"]:
        out.append("pier: plinth, shaft, cap and finial must rise in that order")
    if pv["section_m"] > pv["plinth_m"] or pv["cap"]["half_m"] * 2 < pv["section_m"]:
        out.append("pier: the plinth and the cap are at least as broad as the shaft")
    cp, hv = pv["cap"], pv["cap"]["heart"]
    if cp.get("flare") is not None:      # T-2521: the cap's lower corners flared out under it
        fl, h0 = cp["flare"], cp.get("top_half_m")
        if not (_num(h0) and pv["section_m"] / 2 <= h0 < cp["half_m"]):
            out.append("pier: a flared cap needs top_half_m, at least the shaft's half and under half_m")
        elif not all(_num(fl.get(k)) for k in ("foot_m", "widest_m", "from_m")) or not (
                pv["shaft_top_m"] < fl["foot_m"] < fl["widest_m"] < fl["from_m"] < cp["top_m"]):
            out.append("pier: the cap's flare needs shaft top < foot_m < widest_m < from_m < the cap's top")
        if out:
            return out
    board_half = cp.get("top_half_m", cp["half_m"])
    if not (pv["shaft_top_m"] < hv["lobe_y_m"] - hv["lobe_r_m"] and hv["apex_y_m"] < cp["top_m"]
            and hv["lobe_off_m"] + hv["lobe_r_m"] < board_half - cp["board_m"]):
        out.append("pier: the cap's heart must stand inside its board")
    ps = sorted(q.get("centre_m", 0) for q in bv.get("piers") or [])
    if len(ps) != 2:
        out.append("piers: a gateway stands between two piers")
    elif not (lot[0] < ps[0] - pv["plinth_m"] and ps[1] + pv["plinth_m"] < lot[1] and ps[1] - ps[0] > pv["plinth_m"] + 0.6):
        out.append("piers: both inside the lot, a gateway of at least 0.6 m between their plinths")
    return out


#: T-2425: what a porch's arched head, broader post and stoop need
PORCH_ARCH = ("spring_below_plate_m", "rise_m", "lower_radius_ratio", "lower_sweep_deg", "lobe_m")
PORCH_STOOP = ("max_riser_m", "going_m", "cheek_above_m")
#: T-2519: what a cusped trefoil head needs in place of the pointed arch's rise and arcs
PORCH_TREFOIL = ("spring_below_plate_m", "foil_radius_m", "head_radius_m", "head_over_spring_m", "lobe_m")
#: T-2533: an open-fretwork spandrel, what stands of its board: the bands round the head and side
#: foils, the ring round the quatrefoil (from its middle), the tie from it to the cusp and the eye
#: through that (its breadth, its distance from the quatrefoil's middle), the frame on the post
#: and plate, and the least opening cut.
PORCH_FRET = ("head_band_m", "side_band_m", "ring_m", "tie_m", "eye_m", "eye_at_m", "rim_m", "min_opening_m")


def basement_errors(bv: dict) -> list[str]:
    """T-2523: the basement a house stands on is one height, a storey's worth at most."""
    if set(bv) != {"height_m"}:
        return ["sets height_m and nothing else"]
    if not (_num(bv["height_m"]) and 0 < bv["height_m"] <= 2.5):
        return ["height_m must lie in 0-2.5 m"]
    return []


def transom_errors(door: dict) -> list[str]:
    """T-2520: a transom is a bar on the leaves' head and one light under a low gable, its
    sides at the jambs no higher than its apex at the middle."""
    tm = door.get("transom")
    if tm is None:
        return []
    if not all(_num(tm.get(k)) and tm[k] > 0 for k in ("bar_m", "side_m", "apex_m")):
        return ["needs positive bar_m, side_m and apex_m"]
    if tm["side_m"] > tm["apex_m"]:
        return ["side_m (at the jambs) cannot stand over apex_m (the middle)"]
    return []


def porch_errors(pv: dict) -> list[str]:
    out = []
    if "post_m" in pv and not (_num(pv["post_m"]) and 0.08 <= pv["post_m"] <= 0.4):
        out.append("post_m must be a post section of 0.08-0.4 m")
    if "post_inset_m" in pv and not (_num(pv["post_inset_m"]) and 0.0 <= pv["post_inset_m"] <= 0.3):
        out.append("post_inset_m (the post's outer face in from the floor's end) must lie in 0-0.3 m")
    pl = pv.get("plate")
    if pl is not None:      # T-2519: a house's own plate
        if not isinstance(pl, dict) or not pl or set(pl) - {"clear_m", "height_m"}:
            out.append("plate may set only clear_m and height_m")
        elif not all(_num(x) and x > 0 for x in pl.values()):
            out.append("plate's clear_m and height_m must be positive")
    if "roof_m" in pv and not (_num(pv["roof_m"]) and 0.05 <= pv["roof_m"] <= 0.5):
        out.append("roof_m (T-2533: the porch's fascia) must lie in 0.05-0.5 m")
    ar = pv.get("arch")
    fr = (ar or {}).get("fret")
    if fr is not None and (ar or {}).get("kind") != "trefoil":
        out.append("arch.fret (T-2533) is tied to a trefoil's cusp, so it needs kind: trefoil")
    elif fr is not None and not (isinstance(fr, dict) and set(fr) == set(PORCH_FRET)
                               and all(_num(fr[k]) and 0 < fr[k] <= 0.5 for k in PORCH_FRET)):
        out.append(f"arch.fret (T-2533) needs exactly {', '.join(PORCH_FRET)}, each 0-0.5 m")
    if ar is not None and ar.get("kind") == "trefoil":     # T-2519: a cusped trefoil head
        out += [f"arch needs a positive {k}" for k in PORCH_TREFOIL if not (_num(ar.get(k)) and ar[k] > 0)]
        qi = ar.get("quatrefoil_inset_m")
        if not (isinstance(qi, list) and len(qi) == 2 and all(_num(x) and x > 0 for x in qi)):
            out.append("arch needs quatrefoil_inset_m [in from the post, down from the plate]")
    elif ar is not None:
        out += [f"arch needs a positive {k}" for k in PORCH_ARCH if not (_num(ar.get(k)) and ar[k] > 0)]
        qi = ar.get("quatrefoil_inset_m")
        if not (isinstance(qi, list) and len(qi) == 2 and all(_num(x) and x > 0 for x in qi)):
            out.append("arch needs quatrefoil_inset_m [in from the post, down from the plate]")
        if _num(ar.get("lower_radius_ratio")) and not 0 < ar["lower_radius_ratio"] < 1:
            out.append("arch.lower_radius_ratio must lie between 0 and 1")
        if _num(ar.get("lower_sweep_deg")) and not 0 < ar["lower_sweep_deg"] < 90:
            out.append("arch.lower_sweep_deg must lie between 0 and 90")
    so = pv.get("stoop")
    if so is not None:
        out += [f"stoop needs a positive {k}" for k in PORCH_STOOP if not (_num(so.get(k)) and so[k] > 0)]
    return out


#: T-2397: the roofs an annex may take — a deck, or a lean-to up into the main roof; T-2522 a
#: gable whose ridge runs north into it
ANNEX_ROOFS = ("flat", "lean_to", "gable")


def annex_errors(body: dict, gable_width: float) -> list[str]:
    """What the timber body's widened rear range and its annexes need (T-2397). An annex is a
    block in the lot plan (u east, v north), standing `against` one side of the body and
    walled on the others it names, in the walls' counter-clockwise order; a side it joins to
    another annex is `open`, walled by neither."""
    out = []
    wr = body.get("rear_width_m")
    if wr is not None and (not _num(wr) or wr < gable_width):
        out.append("rear_width_m must be a number no narrower than the gable's range")
    annexes = body.get("annexes")
    if annexes is None:
        return out
    if not _num(body.get("annex_return_m")) or not 0.2 <= body["annex_return_m"] <= 1.0:
        out.append("annex_return_m (each annex corner's return) must lie in 0.2-1.0 m")
    ids = [b.get("id") for b in annexes]
    if len(set(ids)) != len(ids) or not all(isinstance(i, str) and i for i in ids):
        out.append("every annex needs its own id")
    for b in annexes:
        bid = b.get("id", "?")
        r = b.get("rect_uv")
        if not (isinstance(r, list) and len(r) == 4 and all(_num(x) for x in r) and r[0] < r[2] and r[1] < r[3]):
            out.append(f"{bid}: rect_uv must be [u0, v0, u1, v1] with u0 < u1 and v0 < v1")
        if not (b.get("wall_top_m") == "flank" or (_num(b.get("wall_top_m")) and b["wall_top_m"] > 2.0)):
            out.append(f"{bid}: wall_top_m is the flanks' ('flank') or a height above a storey")
        kind = (b.get("roof") or {}).get("kind")
        if kind not in ANNEX_ROOFS:
            out.append(f"{bid}: roof.kind must be one of {', '.join(ANNEX_ROOFS)}")
        if kind == "lean_to" and b.get("against") != "north":
            out.append(f"{bid}: a lean-to rises against the body's south flank, so stands against north")
        if kind == "gable":     # T-2522: a gable whose ridge runs north into the main roof
            rf = b["roof"]
            if b.get("against") != "north" or rf.get("ridge") != "v":
                out.append(f"{bid}: a gabled annex stands against north with its ridge along v")
            if not (_num(rf.get("pitch_deg")) and 20 <= rf["pitch_deg"] <= 65):
                out.append(f"{bid}: a gabled annex's roof.pitch_deg must lie in 20-65")
            if b.get("wall_top_m") == "flank":
                out.append(f"{bid}: a gabled annex's eave stands under the flanks', so its wall_top_m is a number")
        against = b.get("against")
        if against not in SIDES:
            out.append(f"{bid}: an annex names the side it stands against")
            continue
        sides = [w.get("side") for w in b.get("walls") or []]
        order = [SIDES[(SIDES.index(against) + k) % 4] for k in (1, 2, 3)]
        want = [x for x in order if x not in (b.get("open") or [])]
        if sides != want:
            out.append(f"{bid}: walls must run {', '.join(want)} in that order, not {', '.join(map(str, sides))}")
        for w in b.get("walls") or []:
            for x in w.get("windows", []):
                if not all(_num(x.get(k)) for k in ("clear_height_m", "sill_m", "centre_m")):
                    out.append(f"{bid}.{w.get('side')}: a window needs clear_height_m, sill_m, centre_m")
    return out


def _num(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


#: T-3181: a porch's paired posts, arcade, balustrade, cresting and stair cheeks — each key the
#: builder reads, and the range a timber porch's part may take
PORCH_DETAIL = {
    "arcade": {"spring_below_plate_m": (0.1, 1.0), "rise_m": (0.02, 1.0), "middle_rise_m": (0.02, 1.0)},
    "balustrade": {"height_m": (0.4, 1.2), "pitch_m": (0.08, 0.4), "baluster_m": (0.03, 0.2)},
    "cresting": {"height_m": (0.15, 1.0), "inset_m": (0.0, 0.3), "return_to_m": (0.0, 2.0), "base_bar_m": (0.01, 0.1),
                 "top_bar_m": (0.01, 0.1), "bar_m": (0.005, 0.05), "bar_pitch_m": (0.05, 0.4), "post_m": (0.01, 0.1),
                 "post_pitch_m": (0.2, 2.0), "post_above_m": (0.0, 0.3), "knob_m": (0.0, 0.3)},
    "cheek": {"width_m": (0.05, 0.4), "string_above_m": (0.0, 0.4), "height_m": (0.4, 1.2), "rail_m": (0.03, 0.2),
              "rail_width_m": (0.03, 0.3), "baluster_m": (0.03, 0.2), "pitch_m": (0.08, 0.4), "newel_m": (0.08, 0.4),
              "newel_above_m": (0.0, 0.5)},
}


def _porch_detail_errors(po: dict) -> list[str]:
    out = []
    pr = po.get("pair_m")
    if pr is not None and not (_num(pr) and 0.15 <= pr <= 0.6):
        out.append("porch.pair_m (a paired post's centres apart) must lie in 0.15-0.6 m")
    for key, spec in PORCH_DETAIL.items():
        v = (po.get("steps") or {}).get(key) if key == "cheek" else po.get(key)
        if v is None:
            continue
        for k, (lo, hi) in spec.items():
            if not (_num(v.get(k)) and lo <= v[k] <= hi):
                out.append(f"porch.{'steps.' if key == 'cheek' else ''}{key}.{k} must lie in {lo}-{hi}")
    bl = po.get("balustrade")
    if bl is not None:
        for k in ("bottom_rail_m", "top_rail_m"):
            r = bl.get(k)
            if not (isinstance(r, list) and len(r) == 2 and all(_num(x) and 0.02 <= x <= 0.2 for x in r)):
                out.append(f"porch.balustrade.{k} must be [height, width], each 0.02-0.2 m")
    return out


def frame_house_errors(fh: dict) -> list[str]:
    """What the whole-house builder cannot read (T-2357). The first block stands free and
    is walled on all four sides; every later block stands `against` one side of it and is
    walled on its other three, the last of them ending on that wall without a corner. A
    house of a pair (T-1867) names its `party_wall` (the side, and the house `with` it): its
    first block stands `against` that side, so the pair's shared wall is built by neither half
    and the eave, the deck and the front and rear walls run on to the partner's."""
    out = []
    if not _num(fh.get("foundation_m")) or fh["foundation_m"] <= 0:
        out.append("foundation_m must be a positive number")
    if not _num(fh.get("return_m")) or not 0.2 <= fh["return_m"] <= 1.0:
        out.append("return_m (each corner's return) must lie in 0.2-1.0 m")
    blocks = fh.get("blocks") or []
    if not blocks:
        out.append("no blocks")
    pw = fh.get("party_wall")
    if pw is not None and (pw.get("side") not in SIDES or not isinstance(pw.get("with"), str) or not pw["with"]
                           or not blocks or blocks[0].get("against") != pw.get("side")):
        out.append("party_wall names a side and the house `with` it, and the first block stands against that side")
    for i, b in enumerate(blocks):
        bid = b.get("id", f"#{i}")
        r = b.get("rect_uv")
        if not (isinstance(r, list) and len(r) == 4 and all(_num(x) for x in r) and r[0] < r[2] and r[1] < r[3]):
            out.append(f"{bid}: rect_uv must be [u0, v0, u1, v1] with u0 < u1 and v0 < v1")
            continue
        if not _num(b.get("wall_top_m")) or b["wall_top_m"] <= fh.get("foundation_m", 0) + 1.0:
            out.append(f"{bid}: wall_top_m must stand a storey above the foundation")
        if (b.get("roof") or {}).get("kind") not in ROOFS:
            out.append(f"{bid}: roof.kind must be one of {', '.join(ROOFS)}")
        if (b.get("roof") or {}).get("kind") == "gable" and (b["roof"].get("ridge", "u") not in ("u", "v")
                                                           or not _num(b["roof"].get("pitch_deg"))):
            out.append(f"{bid}: a gable roof needs pitch_deg and a ridge along u or v")
        against = b.get("against")
        if i == 0 and against and against != (pw or {}).get("side"):
            out.append(f"{bid}: the first block stands free, or against the party wall the record names")
        if i > 0 and against not in SIDES:
            out.append(f"{bid}: a later block names the side it stands against")
        sides = [w.get("side") for w in b.get("walls") or []]
        want = list(SIDES) if not against else [SIDES[(SIDES.index(against) + k) % 4] for k in (1, 2, 3)]
        if sides != want:
            out.append(f"{bid}: walls must run {', '.join(want)} in that order, not {', '.join(map(str, sides))}")
    po = fh.get("porch")
    if po is not None and (po.get("kind") != "porch" or not _num(po.get("half_width_m"))
                           or not _num(po.get("centre_m"))):
        out.append("porch must be a kit 'porch' variant with half_width_m and centre_m")
    elif po is not None:
        ip = po.get("inner_posts_m")     # T-3180: posts between a long porch's ends, each half's
        if ip is not None and not (isinstance(ip, list) and all(_num(x) and 0.3 <= x <= po["half_width_m"] - 0.6 for x in ip)):
            out.append("porch.inner_posts_m must list posts 0.3 m out from the porch's middle to 0.6 m short of its end")
        bm = po.get("basement_m")
        if bm is not None and not (_num(bm) and 0.0 <= bm <= 2.5):
            out.append("porch.basement_m (the floor raised over the kit's) must lie in 0-2.5 m")
        out += _porch_detail_errors(po)
    ch = fh.get("chimney")
    if ch is not None and not all(_num(ch.get(k)) for k in ("u_m", "v_m", "width_m", "depth_m", "above_ridge_m")):
        out.append("chimney needs u_m, v_m, width_m, depth_m and above_ridge_m")
    out += _frame_upper_errors(fh)
    return out


def _frame_upper_errors(fh: dict) -> list[str]:
    """T-3182: what a whole frame house's upper storey parts need: a block's own eave, its
    paired brackets and frieze lights, a front gable on a hipped block, and a bay on the porch
    deck whose plan is three faces from the wall out and back, each face naming its windows."""
    out = []
    for b in fh.get("blocks") or []:
        bid = b.get("id", "?")
        ev = b.get("eave")
        if ev is not None and not (_num(ev.get("projection_m")) and 0.2 <= ev["projection_m"] <= 1.2):
            out.append(f"{bid}: eave.projection_m must lie in 0.2-1.2 m")
        fg = b.get("front_gable")
        if fg is not None:
            if (b.get("roof") or {}).get("kind") != "hip":
                out.append(f"{bid}: a front gable stands on a hipped block")
            if not all(_num(fg.get(k)) and fg[k] > 0 for k in ("centre_m", "width_m", "pitch_deg", "overhang_m", "rake_m")):
                out.append(f"{bid}: front_gable needs positive centre_m, width_m, pitch_deg, overhang_m and rake_m")
        for w in b.get("walls") or []:
            if "bracket_pairs_m" in w and not ((b.get("bracket") or {}).get("pair_m")
                                               and all(_num(x) for x in w["bracket_pairs_m"])):
                out.append(f"{bid}.{w.get('side')}: bracket_pairs_m needs the block's bracket.pair_m")
            for fl in w.get("frieze_lights") or []:
                if fl.get("kind") not in ("oval", "round") or not all(
                        _num(fl.get(k)) and fl[k] > 0 for k in ("centre_m", "centre_y_m", "width_m", "height_m", "frame_m")):
                    out.append(f"{bid}.{w.get('side')}: a frieze light is an oval or round one with positive "
                               "centre_m, centre_y_m, width_m, height_m and frame_m")
    for i, bay in enumerate(fh.get("bays") or []):
        plan = bay.get("plan") or []
        if len(plan) != 4 or plan[0][1] != 0 or plan[-1][1] != 0 or min(plan[1][1], plan[2][1]) <= 0:
            out.append(f"bay {i}: plan must be four (s, z) points from the wall out and back to it")
        if len(bay.get("faces") or []) != 3:
            out.append(f"bay {i}: faces must name each of the plan's three faces")
        if not all(_num(bay.get(k)) and bay[k] > 0 for k in ("floor_m", "base_m", "wall_top_m", "frieze_m", "post_m",
                                                               "cap_rise_m")) \
                or not bay["floor_m"] < bay["base_m"] < bay["wall_top_m"]:
            out.append(f"bay {i}: floor_m, base_m and wall_top_m must rise in that order, with frieze_m, post_m "
                       "and cap_rise_m positive")
    return out


def gable_errors(gv: dict) -> list[str]:
    """What a gable front's T-2423 parts need: a field the builder knows, a pointed surround
    only on a pointed sash, a hood's four control points and sizes, an oval's middle and sizes
    with its ring standing proud of its field."""
    out = []
    if gv.get("field", "shingle") not in ("shingle", "clapboard"):
        out.append("field must be shingle or clapboard")
    for w in gv.get("windows", []):
        if w.get("surround", "flat") not in ("flat", "pointed"):
            out.append("a window's surround must be flat or pointed")
        elif w.get("surround") == "pointed" and w.get("k06_variant") != "k06.opening.sash_pointed":
            out.append("a pointed surround needs the k06.opening.sash_pointed sash")
    hv = gv.get("hood")
    if hv is not None:
        c = hv.get("curve")
        if not (isinstance(c, list) and len(c) == 4 and all(isinstance(q, list) and len(q) == 2 and all(_num(x) for x in q) for q in c)):
            out.append("hood.curve must be four [s, y] control points")
        if not all(_num(hv.get(k)) and hv[k] > 0 for k in ("centre_m", "width_m", "projection_m", "finial_m")):
            out.append("hood needs positive centre_m, width_m, projection_m and finial_m")
        st = hv.get("stop") or {}
        if not all(_num(st.get(k)) and st[k] > 0 for k in ("width_m", "height_m")):
            out.append("hood.stop needs positive width_m and height_m")
    ov = gv.get("oculus")
    if ov is not None:
        if not all(_num(ov.get(k)) and ov[k] > 0 for k in ("centre_m", "centre_y_m", "width_m", "height_m", "ring_m",
                                                         "field_z_m", "ring_z_m")):
            out.append("oculus needs positive centre_m, centre_y_m, width_m, height_m, ring_m, field_z_m and ring_z_m")
        elif ov["ring_z_m"] <= ov["field_z_m"] or 2 * ov["ring_m"] >= min(ov["width_m"], ov["height_m"]):
            out.append("oculus: the ring must stand proud of its field and leave a field inside it")
    # T-2457: a plain verge board, a cluster of pinnacles, the hood's volute stops and tracery
    vg = gv.get("verge")
    if vg is not None:
        if not all(_num(vg.get(k)) and vg[k] > 0 for k in ("depth_m", "thickness_m", "bead_m", "bead_proud_m")):
            out.append("verge needs positive depth_m, thickness_m, bead_m and bead_proud_m")
        elif vg["bead_m"] >= vg["depth_m"]:
            out.append("verge: the bead must be shallower than the board")
    pn = gv.get("pinnacles")
    if pn is not None:
        if not isinstance(pn, list) or not pn:
            out.append("pinnacles must be a list of pinnacles")
        else:
            for q in pn:
                if not all(_num(q.get(k)) for k in ("offset_m", "section_m", "shaft_top_m", "top_m")) \
                        or q["offset_m"] < 0 or q["section_m"] <= 0 or q["top_m"] <= q["shaft_top_m"]:
                    out.append("a pinnacle needs offset_m >= 0, a positive section_m, and top_m over shaft_top_m")
    if hv is not None:
        st = hv.get("stop") or {}
        if st.get("kind", "block") not in ("block", "volute"):
            out.append("hood.stop.kind must be block or volute")
        elif st.get("kind") == "volute" and not (_num(st.get("radius_m")) and _num(st.get("eye_m"))
                                                 and 0 < st["eye_m"] < st["radius_m"]):
            out.append("a volute stop needs radius_m and a smaller positive eye_m")
        tr = hv.get("tracery")
        if tr is not None and not (all(_num(tr.get(k)) and tr[k] > 0 for k in
                                       ("centre_y_m", "lobe_r_m", "lobe_off_m", "ring_m", "projection_m"))
                                   and tr["ring_m"] < tr["lobe_r_m"]):
            out.append("hood.tracery needs positive centre_y_m, lobe_r_m, lobe_off_m, projection_m and a ring_m under lobe_r_m")
    return out


TOWER_FACES = ("e", "ne", "n", "nw", "w", "sw", "s", "se")


def tower_errors(tv: dict) -> list[str]:
    """What the corner-tower builder cannot read (T-2396): an octagon's size, its stage's wall
    top and spire apex in metres over grade (the stage's foot is the porch roof it stands on),
    the cornice's projection and kick, the finial's height, and each sash's faces."""
    out = []
    for k in ("across_flats_m", "wall_top_m", "spire_apex_m", "eave_projection_m", "kick_m", "finial_m"):
        if not _num(tv.get(k)) or tv[k] <= 0:
            out.append(f"{k} must be a positive number")
    if not out and tv["spire_apex_m"] <= tv["wall_top_m"] + 1.0:
        out.append("spire_apex_m must stand at least 1 m over wall_top_m")
    sg = tv.get("stage")
    if sg is not None:     # T-2521: a smooth stage under a shallower frieze, a trefoil incised over each light
        if not (_num(sg.get("frieze_m")) and 0.05 <= sg["frieze_m"] <= 0.5):
            out.append("stage.frieze_m must be 0.05-0.5 m")
        inc = sg.get("incised")
        if inc is not None and not (all(_num(inc.get(k)) and inc[k] > 0 for k in
                                        ("centre_y_m", "lobe_r_m", "lobe_off_m", "groove_m", "depth_m"))
                                    and inc["lobe_r_m"] - inc["groove_m"] > inc["lobe_off_m"] * math.sqrt(3) / 2
                                    and inc["depth_m"] < 0.015):
            out.append("stage.incised needs positive centre_y_m, lobe_r_m, lobe_off_m, groove_m and depth_m "
                       "(under 0.015 m), the lobes inside the groove overlapping")
    seen = set()
    for w in tv.get("windows", []):
        faces = w.get("faces") or []
        if not faces or any(f not in TOWER_FACES or f in seen for f in faces):
            out.append(f"a window's faces must be distinct, from {', '.join(TOWER_FACES)}")
        seen.update(faces)
        if not all(_num(w.get(x)) for x in ("clear_width_m", "clear_height_m", "sill_m")) or not w.get("k06_variant"):
            out.append("a window needs k06_variant, clear_width_m, clear_height_m and sill_m")
    return out


def bay_errors(bv: dict) -> list[str]:
    """What the timber bay builder cannot read (T-2424): a plan of three faces from the wall
    (z 0) out and back to it, its base, wall top and frieze under the cornice, the least post,
    the deck's rise to the wall, and the one light every face carries."""
    out = []
    plan = bv.get("plan") or []
    if len(plan) != 4 or not all(isinstance(q, list) and len(q) == 2 and all(_num(x) for x in q) for q in plan):
        out.append("plan must be four (s, z) points: three faces")
    elif plan[0][1] != 0 or plan[-1][1] != 0 or min(plan[1][1], plan[2][1]) <= 0:
        out.append("plan must start and end on the wall (z 0) and stand out from it between")
    for k in ("base_m", "wall_top_m", "frieze_m", "post_m", "roof_m"):
        if not _num(bv.get(k)) or bv[k] <= 0:
            out.append(f"{k} must be a positive number")
    lt = bv.get("lights") or {}
    if not all(_num(lt.get(x)) for x in ("clear_width_m", "clear_height_m", "sill_m")) or not lt.get("k06_variant"):
        out.append("lights needs k06_variant, clear_width_m, clear_height_m and sill_m")
    elif "head_radius_ratio" in lt and not (_num(lt["head_radius_ratio"]) and 0.5 < lt["head_radius_ratio"] <= 1.0):
        out.append("lights.head_radius_ratio must lie over 0.5 and at most 1 (T-2457: a drop head)")
    elif lt.get("stops") is not None and not all(_num(lt["stops"].get(k)) and lt["stops"][k] > 0
                                                 for k in ("width_m", "height_m", "projection_m")):
        out.append("lights.stops needs positive width_m, height_m and projection_m")
    elif not out and lt["sill_m"] + lt["clear_height_m"] >= bv["wall_top_m"] - bv["frieze_m"]:
        out.append("the lights must stand under the frieze")
    return out
