"""Parameters for the masonry_house archetype — pure Python, NO bpy import.

Same split, and for the same reason, as every other `*_params` module: tools/check.sh
imports this on every commit to prove that each scene-included record still resolves
into buildable parameters, in a bare Python with no Blender in the sandbox.

## What this archetype is for

A load-bearing masonry house of the 1880s city — the stone and brick mansions of the
1904 Prairie Avenue scene — whose form is not a box with a roof but a COMPOSITION:
gabled ranges meeting at right angles, round towers with conical roofs, bays, dormers,
parapet gables and stacks, each of which a measured drawing or a dated photograph
states separately and at a different grade. The first record is the John J. Glessner
House at 1800 Prairie (T-1732), built from the T-1731 specification
(`docs/RESEARCH/glessner_house_1904.md`).

The frame archetypes of the 1835 town take a handful of scalars (a width, a pitch, a
paint) and decide the rest themselves. That is the wrong shape here: the Glessner
House's HABS survey prints or measures almost every one of those decisions, and a
generator that "decided" a ridge the drawings already place would be inventing over
evidence. So this archetype decides nothing about form. Every mass, tower, bay,
opening and stack is a FORM ATTRIBUTE of the record, carrying its own confidence and
its own sources, and this module only converts them — from the sources' own units and
frame into metres in the footprint's frame — and hands the builder a list of parts,
each tagged with the confidence of the attributes that drove it.

## The two frames, and why the record keeps the sources' one

The record states geometry the way HABS prints it: in FEET, in the **building frame**
of the plans — `W` feet west of the Prairie Avenue (east) face, `S` feet south of the
18th Street (north) face — and heights in feet above one of two stated datums (`door`,
HABS sheet 6's front-door sill; `ng`, the grade sheet 4 draws at the 18th Street
wall). Keeping the sources' own numbers in the record is what lets a reader check a
value against the sheet it cites without re-deriving a conversion; the conversion is
done once, here:

    x_m = (length_ft - W) * 0.3048      (x east, from the building's west face)
    y_m = (depth_ft  - S) * 0.3048      (y north, from its south face)
    z_m = (h + datum_offset_ft) * 0.3048

so the footprint polygon's origin — docs/GLB-CONTRACT.md's mesh origin — is the SW
corner of the building's bounding box, and every point of the house has x, y >= 0.

## What it deliberately does not do

Full interiors remain out of scope. Legacy profiles represent openings as surface
panels; the explicitly selected glessner_v4 profile clips real wall apertures, adds
recessed glazing and shallow dark room backing, and preserves the open underpass.
Neighbouring buildings are their own records — the Glessner courtyard's south side
is the north wall of 1808 Prairie, which belongs to that house (T-0475).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md. Duplicated from the other params modules rather than
# imported, so that neither can break the other's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

FT = 0.3048

# The form attributes whose VALUE this archetype reads. An attribute outside this set
# cannot move a vertex, so tools/validate.py makes the record declare what the mesh
# does with it instead (`geometry: absent | simplified | record_only`).
#
# Most of the vocabulary is FAMILIES of per-part attributes — `range_<part>`,
# `ridge_<part>`, `gable_<part>_<face>`, `tower_<part>` (+ `_plan`), `bay_<part>`
# (+ `_elevation`), `turret_<part>`, `chimney_<part>`, `openings_<group>` — because
# the evidence arrives per part and at a different grade for each: the Glessner
# House's east-wing ridge line is inferred where its north-range ridge is printed, and
# one attribute over both would have to carry the weaker grade for the stronger value.
# `validate.py` asks this set by NAME, so it lists every part name a committed record
# uses; `from_phase` refuses a family attribute that is not listed here, so a new part
# cannot be read by the builder while the gate believes nothing reads it.
FAMILIES = ("range_", "ridge_", "gable_", "tower_", "bay_", "turret_", "chimney_",
            "openings_")
CONSUMED = frozenset({
    "frame_ft", "grade_datum", "detail_profile", "v4_detail",
    "construction", "paint", "roof_covering",
    "granite_tint", "brick_tint", "trim_tint", "roof_tint", "copper_tint", "wood_tint",
    # 1800 Prairie Avenue (glessner_house)
    "range_east_wing", "range_north_range", "range_west_wing",
    "ridge_east_wing", "ridge_north_range", "ridge_west_wing",
    "gable_east_wing_north", "gable_east_wing_south",
    "gable_west_wing_north", "gable_west_wing_south",
    "tower_stair", "tower_north", "tower_north_plan",
    "hall_bow", "hall_bow_height", "hall_bow_roof",
    "bay_dining", "bay_dining_elevation",
    "dormers", "dormer_depth",
    "turret_stable",
    "chimneys", "chimney_plans", "chimney_dining_room",
    "openings_prairie", "openings_18th", "openings_18th_stable", "openings_18th_photo",
    "openings_stable_doors", "openings_alley", "openings_court", "openings_court_north",
    "opening_heights",
    "eave_cornice",
    "courtyard_gate", "courtyard_gate_heights",
    "courtyard_ground",
})

# Where this archetype touches the ground: the whole footprint outline, at the base
# of the walls — "y = 0 at the base of the walls" in docs/GLB-CONTRACT.md.
GROUND_CONTACT = "perimeter"

WALL_KINDS = ("granite", "brick", "trim", "wood", "none")
FACES = ("north", "south", "east", "west")
OPENING_KINDS = ("window", "door", "doors", "arch", "dark", "fan", "band")


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


def _hex_or_rgb(v) -> list[float]:
    if isinstance(v, (list, tuple)) and len(v) in (3, 4):
        rgb = [float(c) for c in v[:3]]
        if not all(0.0 <= c <= 1.0 for c in rgb):
            raise ParamError(f"colour {v!r} is not a linear rgb triple in 0..1")
        return rgb + [1.0]
    raise ParamError(f"colour {v!r} is not a linear [r, g, b]")


@dataclass
class MasonryHouseParams:
    """One masonry house as a list of parts in the footprint's metric frame.

    Every part is a plain dict so that the staleness hash (generators/mesh_inputs.py)
    sees exactly the numbers the builder reads, and every part carries `conf`, the
    _CONFIDENCE float of the attributes that drove it — least-confident wins.
    """

    width_m: float
    depth_m: float
    colours: dict = field(default_factory=dict)
    ranges: list = field(default_factory=list)
    towers: list = field(default_factory=list)
    bows: list = field(default_factory=list)
    bays: list = field(default_factory=list)
    dormers: list = field(default_factory=list)
    turrets: list = field(default_factory=list)
    chimneys: list = field(default_factory=list)
    openings: list = field(default_factory=list)
    bands: list = field(default_factory=list)
    walls: list = field(default_factory=list)
    ground: list = field(default_factory=list)
    confidence: dict = field(default_factory=dict)
    detail_profile: str = ""
    detail: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def validate(self) -> None:
        if self.detail_profile not in ("", "glessner_v4"):
            raise ParamError(f"unknown masonry detail profile {self.detail_profile!r}")
        if not 3.0 <= self.width_m <= 120.0 or not 3.0 <= self.depth_m <= 120.0:
            raise ParamError(f"footprint {self.width_m} x {self.depth_m} m is outside "
                             f"3-120 m — not a house")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")
        if not self.ranges:
            raise ParamError("a masonry house needs at least one gabled range")
        for r in self.ranges:
            if r["ridge_z"] <= max(r["eave_lo_z"], r["eave_hi_z"]):
                raise ParamError(f"range '{r['name']}': ridge {r['ridge_z']:.2f} m is not "
                                 f"above its eaves")
            lo, hi = (r["x0"], r["x1"]) if r["axis"] == "y" else (r["y0"], r["y1"])
            if not lo < r["ridge_at"] < hi:
                raise ParamError(f"range '{r['name']}': ridge line {r['ridge_at']:.2f} m is "
                                 f"outside its own walls ({lo:.2f}-{hi:.2f})")
        for t in self.towers:
            if t["apex_z"] <= t["wall_top_z"]:
                raise ParamError(f"tower '{t['name']}': cone apex below its wall top")
        for o in self.openings:
            if o["kind"] not in OPENING_KINDS:
                raise ParamError(f"opening kind '{o['kind']}' not in {OPENING_KINDS}")
            if o["z1"] <= o["z0"] and o["kind"] != "fan":
                raise ParamError(f"opening on {o['face']} at u {o['u0']:.2f}: head "
                                 f"{o['z1']:.2f} not above sill {o['z0']:.2f}")


# ------------------------------------------------------------------ conversion


class _Frame:
    """The record's building frame (feet, W west / S south, two height datums)."""

    def __init__(self, length_ft: float, depth_ft: float, datums: dict):
        self.L = float(length_ft)
        self.D = float(depth_ft)
        self.datums = {k: float(v) for k, v in datums.items()}

    def x(self, w: float) -> float:
        return round((self.L - float(w)) * FT, 4)

    def y(self, s: float) -> float:
        return round((self.D - float(s)) * FT, 4)

    def z(self, h: float, datum: str = "ng") -> float:
        if datum not in self.datums:
            raise ParamError(f"height datum '{datum}' is not declared in frame_ft / "
                             f"grade_datum (known: {sorted(self.datums)})")
        return round((float(h) + self.datums[datum]) * FT, 4)

    def zval(self, spec) -> float:
        """A height written `[h, "datum"]` or as a bare number above grade."""
        if isinstance(spec, (list, tuple)):
            return self.z(spec[0], spec[1])
        return self.z(spec, "ng")

    def xy(self, pt) -> list[float]:
        return [self.x(pt[0]), self.y(pt[1])]


# The four faces of the building frame, and which way each looks in the metric frame.
# `axis` is the coordinate that is constant on the face; `sign` is its outward normal.
_FACE_AXIS = {"east": ("x", +1), "west": ("x", -1), "north": ("y", +1), "south": ("y", -1)}


def _face(fr: _Frame, face: str, at: float) -> dict:
    """A wall plane: `face` names its outward direction, `at` its W (east/west faces)
    or S (north/south faces) in the building frame."""
    if face not in _FACE_AXIS:
        raise ParamError(f"face '{face}' not in {FACES}")
    axis, sign = _FACE_AXIS[face]
    coord = fr.x(at) if axis == "x" else fr.y(at)
    return {"face": face, "axis": axis, "sign": sign, "at": coord}


def _u(fr: _Frame, face: str, v: float) -> float:
    """Position along a face: east/west faces run along S, north/south along W."""
    axis, _ = _FACE_AXIS[face]
    return fr.y(v) if axis == "x" else fr.x(v)


def _urange(fr: _Frame, face: str, a: float, b: float) -> tuple[float, float]:
    u0, u1 = _u(fr, face, a), _u(fr, face, b)
    return (min(u0, u1), max(u0, u1))


def from_phase(phase: dict, record: dict | None = None) -> MasonryHouseParams:
    """Resolve one structure phase into generator parameters.

    Reads only each form attribute's `value` and its confidence. The footprint polygon
    must start at the origin (docs/GLB-CONTRACT.md); its bounding box is checked
    against the `frame_ft` the attributes are written in, so the two cannot drift.
    """
    form = phase.get("form", {})

    def val(attr, default=None):
        a = form.get(attr)
        return default if a is None else a.get("value", default)

    def cf(*attrs) -> float:
        """Least-confident wins over the attributes that drive one part."""
        vals = []
        for a in attrs:
            blk = form.get(a)
            vals.append(CONFIDENCE_VALUE[(blk or {}).get("confidence", "reconstructed")])
        return max(vals) if vals else 1.0

    poly = phase.get("footprint", {}).get("polygon") or []
    if len(poly) < 3:
        raise ParamError("footprint polygon needs at least 3 points")
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    if abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise ParamError(
            f"footprint polygon starts at ({min(xs)}, {min(ys)}), not the origin. "
            f"docs/GLB-CONTRACT.md pins the mesh origin to polygon coordinate (0, 0).")

    frame = val("frame_ft")
    if not isinstance(frame, dict):
        raise ParamError("frame_ft is required: the building frame the record's feet "
                         "are written in")
    datums = {"ng": 0.0}
    datums["door"] = float(frame.get("door_datum_above_grade_ft", 0.0))
    gd = val("grade_datum") or {}
    datums["ng"] = float(gd.get("north_grade_above_grade_ft", 0.0))
    fr = _Frame(frame["length_ft"], frame["depth_ft"], datums)

    width, depth = max(xs) - min(xs), max(ys) - min(ys)
    if abs(width - fr.L * FT) > 0.05 or abs(depth - fr.D * FT) > 0.05:
        raise ParamError(f"footprint bounding box {width:.3f} x {depth:.3f} m disagrees "
                         f"with frame_ft {fr.L} x {fr.D} ft ({fr.L * FT:.3f} x "
                         f"{fr.D * FT:.3f} m) — the polygon and the attributes are in "
                         f"two different frames")

    if val("construction") not in ("stone", "brick"):
        raise ParamError(f"construction {val('construction')!r}: this archetype builds "
                         f"load-bearing masonry, stone or brick")
    if val("paint") not in ("stone", "brick"):
        raise ParamError(f"paint {val('paint')!r}: a masonry_house's walls are bare "
                         f"masonry ('stone' or 'brick'); a painted wall is another claim")
    if val("roof_covering") != "terracotta_tile":
        raise ParamError(f"roof_covering {val('roof_covering')!r}: the only covering this "
                         f"archetype colours is 'terracotta_tile'")

    colours = {
        "granite": _hex_or_rgb(val("granite_tint")),
        "brick": _hex_or_rgb(val("brick_tint")),
        "trim": _hex_or_rgb(val("trim_tint")),
        "roof": _hex_or_rgb(val("roof_tint")),
        "copper": _hex_or_rgb(val("copper_tint")),
        "wood": _hex_or_rgb(val("wood_tint")),
    }

    unknown = sorted(a for a in form if a.startswith(FAMILIES) and a not in CONSUMED)
    if unknown:
        raise ParamError(f"form attribute(s) {unknown} belong to a part family this "
                         f"archetype reads, but CONSUMED does not list them — add them "
                         f"there, or tools/validate.py will believe nothing reads them")

    p = MasonryHouseParams(width_m=round(width, 3), depth_m=round(depth, 3),
                           colours=colours, detail_profile=val("detail_profile", ""))
    p.confidence = {a: (form[a] or {}).get("confidence", "reconstructed") for a in form}
    p.confidence["footprint"] = phase.get("footprint", {}).get("confidence",
                                                               "reconstructed")

    def family(prefix: str, *, exclude_suffix: tuple = ()) -> list[str]:
        return sorted(a for a in form if a.startswith(prefix)
                      and not any(a.endswith(s) for s in exclude_suffix))

    # ---------------------------------------------------------------- ranges
    for attr in family("range_"):
        name = attr[len("range_"):]
        r = form[attr]["value"]
        rid_attr = f"ridge_{name}"
        rid = val(rid_attr)
        if rid is None:
            raise ParamError(f"range '{name}' has no {rid_attr}")
        axis = r["ridge_axis"]            # 'ns' or 'ew' in the building frame
        if axis not in ("ns", "ew"):
            raise ParamError(f"range '{name}': ridge_axis {axis!r} is not 'ns' or 'ew'")
        x0, x1 = sorted((fr.x(r["W"][0]), fr.x(r["W"][1])))
        y0, y1 = sorted((fr.y(r["S"][0]), fr.y(r["S"][1])))
        # eave_lo is the eave on the low-coordinate side of the ridge in METRES (west
        # for a N-S ridge, south for an E-W one); the record names them by face.
        if axis == "ns":
            ridge_at = fr.x(rid["W"])
            eave_lo, eave_hi = fr.zval(rid["eave_west"]), fr.zval(rid["eave_east"])
        else:
            ridge_at = fr.y(rid["S"])
            eave_lo, eave_hi = fr.zval(rid["eave_south"]), fr.zval(rid["eave_north"])
        kick = None
        if rid.get("kick"):
            k = rid["kick"]
            kick = {"side": k["side"], "run_m": round(float(k["run_ft"]) * FT, 4),
                    "pitch_deg": float(k["pitch_deg"])}
        extend = {}
        for side, v in (r.get("roof_extends_to") or {}).items():
            # an E-W range is carried along x (a W value), a N-S one along y (an S value)
            extend[side] = fr.x(v) if axis == "ew" else fr.y(v)
        ends, parapet, end_conf = {}, {}, {}
        for face in FACES:
            g_attr = f"gable_{name}_{face}"
            g = val(g_attr)
            if g is None:
                ends[face] = "none"
                end_conf[face] = cf(attr)
                continue
            ends[face] = g["end"]
            parapet[face] = round(float(g.get("parapet_ft", 1.0)) * FT, 4)
            end_conf[face] = cf(attr, rid_attr, g_attr)
        rng = {
            "name": name,
            "axis": "y" if axis == "ns" else "x",
            "x0": x0, "x1": x1, "y0": y0, "y1": y1,
            "ridge_at": ridge_at,
            "ridge_z": fr.zval(rid["ridge"]),
            "eave_lo_z": eave_lo,
            "eave_hi_z": eave_hi,
            "kick": kick,
            "roof_extend": extend,
            "walls": {f: r["walls"].get(f, "none") for f in FACES},
            "wall_skip": {f: [list(_urange(fr, f, *span)) for span in spans]
                          for f, spans in (r.get("wall_skip") or {}).items()},
            "gable_ends": ends,
            "parapet_m": parapet,
            "conf_plan": cf(attr, rid_attr),
            "conf_roof": cf(attr, rid_attr),
            "conf_ends": end_conf,
        }
        for f in FACES:
            if rng["walls"][f] not in WALL_KINDS:
                raise ParamError(f"range '{name}': wall {f} is {rng['walls'][f]!r}, not one "
                                 f"of {WALL_KINDS}")
            if rng["gable_ends"][f] not in ("parapet", "plain", "none"):
                raise ParamError(f"range '{name}': gable end {f} is "
                                 f"{rng['gable_ends'][f]!r}")
        p.ranges.append(rng)

    # ---------------------------------------------------------------- towers
    for attr in family("tower_", exclude_suffix=("_plan",)):
        name = attr[len("tower_"):]
        t = form[attr]["value"]
        plan_attr = f"{attr}_plan"
        pl = val(plan_attr) or {}
        cw = pl.get("centre_W", t.get("centre_W"))
        cs = pl.get("centre_S", t.get("centre_S"))
        r_drum = pl.get("r_ft", t.get("r_ft"))
        if cw is None or cs is None or r_drum is None:
            raise ParamError(f"tower '{name}' has no centre or radius in {attr} or "
                             f"{plan_attr}")
        eave_r = pl.get("eave_r_ft", t.get("eave_r_ft", float(r_drum) + 0.5))
        conf = cf(attr, plan_attr) if plan_attr in form else cf(attr)
        p.towers.append({
            "name": name,
            "cx": fr.x(cw), "cy": fr.y(cs),
            "r": round(float(r_drum) * FT, 4),
            "eave_r": round(float(eave_r) * FT, 4),
            "z0": fr.zval(t.get("base", 0.0)),
            "wall_top_z": fr.zval(t["wall_top"]),
            "apex_z": fr.zval(t["apex"]),
            "finial_m": round(float(t.get("finial_ft", 0.0)) * FT, 4),
            "wall": t.get("wall", "brick"),
            "segments": int(t.get("segments", 16)),
            "conf_wall": conf,
            "conf_roof": conf,
        })

    # --------------------------------------------------------------- hall bow
    bow = val("hall_bow")
    if bow:
        cx, cy = fr.x(bow["centre_W"]), fr.y(bow["centre_S"])
        a0 = math.atan2(fr.y(bow["from"][1]) - cy, fr.x(bow["from"][0]) - cx)
        a1 = math.atan2(fr.y(bow["to"][1]) - cy, fr.x(bow["to"][0]) - cx)
        hb = val("hall_bow_height") or {}
        roof = val("hall_bow_roof") or {}
        p.bows.append({
            "name": "hall_bow", "cx": cx, "cy": cy,
            "r": round(float(bow["r_ft"]) * FT, 4),
            "a0": round(a0, 5), "a1": round(a1, 5),
            "wall_top_z": fr.zval(hb.get("wall_top", 0.0)),
            "light_rows": [[fr.zval(r[0]), fr.zval(r[1])] for r in hb.get("light_rows", [])],
            "lights_per_row": int(hb.get("lights_per_row", 0)),
            "roof_rise_m": round(float(roof.get("rise_ft", 4.0)) * FT, 4),
            "roof_colour": roof.get("colour", "copper"),
            "conf_wall": cf("hall_bow", "hall_bow_height"),
            "conf_roof": cf("hall_bow_roof"),
        })

    # ------------------------------------------------------------------- bays
    for attr in family("bay_", exclude_suffix=("_elevation",)):
        name = attr[len("bay_"):]
        el_attr = f"{attr}_elevation"
        el = val(el_attr)
        if el is None:
            raise ParamError(f"bay '{name}' has no {el_attr}")
        apex = el["roof_apex"]
        p.bays.append({
            "name": name,
            "pts": [fr.xy(pt) for pt in form[attr]["value"]["outline"]],
            "wall_top_z": fr.zval(el["wall_top"]),
            "band_top_z": fr.zval(el.get("glazed_band_top", el["wall_top"])),
            "apex": [fr.x(apex[0]), fr.y(apex[1]), fr.zval(apex[2])],
            "light_row": ([fr.zval(el["light_row"][0]), fr.zval(el["light_row"][1])]
                          if el.get("light_row") else []),
            "conf_wall": cf(attr, el_attr),
            "conf_roof": cf(el_attr),
        })

    # ---------------------------------------------------------------- dormers
    dm = val("dormers")
    if dm:
        dd = val("dormer_depth") or {}
        half = float(dm["width_ft"]) / 2.0
        for c in dm["centres_S"]:
            p.dormers.append({
                "front": fr.x(dd["front_W"]), "back": fr.x(dd["back_W"]),
                "u0": fr.y(c + half), "u1": fr.y(c - half),
                "z0": fr.zval(dd["bottom"]),
                "eave_z": fr.zval(dm["eave"]),
                "apex_z": fr.zval(dm["apex"]),
                "light": [fr.zval(dm["light"][0]), fr.zval(dm["light"][1])],
                "conf": cf("dormers", "dormer_depth"),
            })

    # --------------------------------------------------------------- turrets
    for attr in family("turret_"):
        t = form[attr]["value"]
        half = float(t["plan_ft"]) / 2.0
        p.turrets.append({
            "name": attr[len("turret_"):],
            "x0": fr.x(t["centre_W"] + half), "x1": fr.x(t["centre_W"] - half),
            "y0": fr.y(t["centre_S"] + half), "y1": fr.y(t["centre_S"] - half),
            "z0": fr.zval(t["base"]),
            "top_z": fr.zval(t["body_top"]),
            "louvre": [fr.zval(t["louvre"][0]), fr.zval(t["louvre"][1])],
            "apex_z": fr.zval(t["apex"]),
            "finial_m": round(float(t.get("finial_ft", 0.0)) * FT, 4),
            "conf": cf(attr),
        })

    # --------------------------------------------------------------- chimneys
    def chimney(name, ws, ss, base, top, conf):
        p.chimneys.append({
            "name": name,
            "x0": min(fr.x(ws[0]), fr.x(ws[1])), "x1": max(fr.x(ws[0]), fr.x(ws[1])),
            "y0": min(fr.y(ss[0]), fr.y(ss[1])), "y1": max(fr.y(ss[0]), fr.y(ss[1])),
            "z0": fr.zval(base), "z1": fr.zval(top), "conf": conf,
        })

    cplans = val("chimney_plans") or {}
    for name, c in sorted((val("chimneys") or {}).items()):
        pl = cplans.get(name)
        if pl is None:
            raise ParamError(f"chimney '{name}' has no entry in chimney_plans")
        chimney(name, pl["W"], c["S"], pl["base"], c["top"], cf("chimneys", "chimney_plans"))
    for attr in family("chimney_", exclude_suffix=("_plans",)):
        c = form[attr]["value"]
        chimney(attr[len("chimney_"):], c["W"], c["S"], c["base"], c["top"], cf(attr))

    # --------------------------------------------------------------- openings
    heights = val("opening_heights") or {}
    opening_groups = [(a, form[a]["value"]) for a in family("openings_")]
    if p.detail_profile:
        opening_groups += [("v4_detail", g) for g in
                           (val("v4_detail", {}).get("supplemental_openings", []))]
    for attr, grp in opening_groups:
        face = grp["face"]
        plane = _face(fr, face, grp["at"])
        rows = heights.get(attr, {})
        grp_conf = cf(attr)
        row_conf = cf(attr, "opening_heights")
        for it in grp["items"]:
            kind = it.get("kind", "window")
            if "z" in it:
                z, conf = it["z"], grp_conf
            else:
                z, conf = rows.get(it.get("row", "")), row_conf
            if z is None:
                raise ParamError(f"{attr}: an item at {it.get('at')} has no height, and "
                                 f"opening_heights gives none for row {it.get('row')!r}")
            datum = it.get("datum", grp.get("datum", "ng"))
            z0 = max(0.0, fr.z(z[0], datum))
            z1 = fr.z(z[1], datum)
            spans = it["at"]
            if spans and not isinstance(spans[0], (list, tuple)):
                spans = [spans]
            lights = int(it.get("lights", 1))
            gap = float(it.get("mullion_ft", 0.6)) * FT
            for a, b in spans:
                u0, u1 = _urange(fr, face, a, b)
                if kind == "window" and it.get("grid"):
                    gc, gr = it["grid"]
                    gw = ((u1 - u0) - gap * (gc - 1)) / gc
                    gh = ((z1 - z0) - gap * (gr - 1)) / gr
                    for i in range(gc):
                        for j in range(gr):
                            lu, lz = u0 + i * (gw + gap), z0 + j * (gh + gap)
                            p.openings.append({**plane, "kind": "window",
                                               "u0": round(lu, 4), "u1": round(lu + gw, 4),
                                               "z0": round(lz, 4), "z1": round(lz + gh, 4),
                                               "conf": conf})
                    continue
                if kind == "window" and lights > 1:
                    wl = ((u1 - u0) - gap * (lights - 1)) / lights
                    for i in range(lights):
                        lu = u0 + i * (wl + gap)
                        p.openings.append({**plane, "kind": "window", "u0": round(lu, 4),
                                           "u1": round(lu + wl, 4), "z0": z0, "z1": z1,
                                           "conf": conf})
                    continue
                op = {**plane, "kind": kind, "u0": u0, "u1": u1, "z0": z0, "z1": z1,
                      "conf": conf}
                if it.get("style"):
                    op["style"] = it["style"]
                if kind in ("arch", "fan"):
                    op["spring_z"] = fr.z(it["spring"], datum)
                    op["r_out"] = round(float(it.get("ring_ft", 0.0)) * FT, 4)
                    op["r_in"] = round(float(it.get("inner_ft", 0.0)) * FT, 4)
                    op["voussoirs"] = int(it.get("voussoirs", 0))
                p.openings.append(op)

    # ------------------------------------------------------------ cornices
    corn = val("eave_cornice")
    if corn:
        for b in corn["bands"]:
            face = b["face"]
            u0, u1 = _urange(fr, face, *b["span"])
            p.bands.append({**_face(fr, face, b["at"]), "u0": u0, "u1": u1,
                            "z0": fr.zval(b["z"][0]), "z1": fr.zval(b["z"][1]),
                            "proj_m": round(float(b.get("proj_ft", 0.5)) * FT, 4),
                            "colour": b.get("colour", "granite"),
                            "conf": cf("eave_cornice")})

    # ------------------------------------------------------- courtyard gate
    gate = val("courtyard_gate")
    if gate:
        gh = val("courtyard_gate_heights") or {}
        face = gate["face"]
        for piece in gate["pieces"]:
            u0, u1 = _urange(fr, face, *piece["S"])
            kind = piece["kind"]
            if kind not in gh:
                raise ParamError(f"courtyard_gate piece '{kind}' has no height in "
                                 f"courtyard_gate_heights")
            p.walls.append({**_face(fr, face, gate["at"]), "kind": kind,
                            "u0": u0, "u1": u1,
                            "thick_m": round(float(gate.get("thick_ft", 1.5)) * FT, 4),
                            "z1": fr.zval(gh[kind]),
                            "conf": cf("courtyard_gate", "courtyard_gate_heights")})

    # ---------------------------------------------------------------- ground
    cg = val("courtyard_ground")
    if cg:
        for g in cg["surfaces"]:
            p.ground.append({"kind": g["kind"],
                             "rgba": _hex_or_rgb(g["tint"]),
                             "pts": [fr.xy(pt) for pt in g["outline"]],
                             "lift_m": round(float(g.get("lift_ft", 0.05)) * FT, 4),
                             "conf": cf("courtyard_ground")})

    if p.detail_profile:
        raw = val("v4_detail", {})
        p.detail["ashlar_courses_m"] = [round(float(h) * 0.0254, 6)
                                          for h in raw.get("ashlar_courses_in", [])]
        p.detail["ashlar_relief_m"] = [float(v) * FT for v in
                                        raw.get("ashlar_relief_ft", [0.025,0.15])]
        p.detail["conf"] = cf("v4_detail")
        cg = raw.get("west_cross_gable")
        if cg:
            a, b = sorted((fr.y(cg["S"][0]), fr.y(cg["S"][1])))
            p.detail["west_cross_gable"] = {"axis": "x", "sign": -1,
                "at": fr.x(cg["W"]), "u0": a, "u1": b,
                "ridge_at": fr.y(cg["ridge_S"]), "ridge_z": fr.zval(cg["ridge"]),
                "eave_lo_z": fr.zval(cg["eaves"][1]),
                "eave_hi_z": fr.zval(cg["eaves"][0]), "conf": cf("v4_detail")}
        ng = raw.get("stable_north_gable")
        if ng:
            west = next(r for r in p.ranges if r["name"] == "west_wing")
            north = next(r for r in p.ranges if r["name"] == "north_range")
            west["north_cross_gable"] = {
                "x0": min(fr.x(w) for w in ng["W"]),
                "x1": max(fr.x(w) for w in ng["W"]),
                "eave_z": fr.zval(ng["eave"]),
                "cross_y0": north["y0"], "cross_y1": north["y1"],
                "cross_ridge_at": north["ridge_at"], "cross_ridge_z": north["ridge_z"],
                "cross_eave_lo_z": north["eave_lo_z"],
                "cross_eave_hi_z": north["eave_hi_z"], "cross_kick": north["kick"],
            }
            # The west wing emits the joined roof here, once. In particular the
            # north roof must never continue through the north gable's openings.
            north["roof_min"] = west["x1"]
        wd = raw.get("west_dormer")
        if wd:
            half = float(wd["width_ft"]) / 2
            p.detail["west_dormer"] = {"front": fr.x(wd["front_W"]),
                "back": fr.x(wd["back_W"]), "u0": fr.y(wd["centre_S"] + half),
                "u1": fr.y(wd["centre_S"] - half), "z0": fr.zval(wd["base"]),
                "eave_z": fr.zval(wd["eave"]), "apex_z": fr.zval(wd["apex"]),
                "conf": cf("v4_detail")}
        rework = raw.get("stable_roof_rework")
        if rework:
            west = next(r for r in p.ranges if r["name"] == "west_wing")
            north = next(r for r in p.ranges if r["name"] == "north_range")
            ng = raw["stable_north_gable"]
            west["stable_roof"] = {
                "front_x0": min(fr.x(w) for w in ng["W"]),
                "front_x1": max(fr.x(w) for w in ng["W"]),
                "north_eave": fr.zval(ng["eave"]),
                "cross_y": fr.y(rework["cross_ridge_S"]),
                "cross_z": fr.zval(rework["cross_ridge"]),
                "south_foot_y": fr.y(rework["south_gable_foot_S"]),
                "rear_x": fr.x(rework["rear_ridge_W"]),
                "rear_z": fr.zval(rework["rear_ridge"]),
                "rear_west_eave": fr.zval(rework["rear_eave_west"]),
                "rear_east_eave": fr.zval(rework["rear_eave_east"]),
                "south_eave": fr.zval(rework["south_eave"]),
                "hip_y": fr.y(rework["south_hip_S"]),
                "front_hip_y": fr.y(rework["front_hip_S"]),
                "north_range": dict(north)}
            dormer = p.detail.get("west_dormer")
            if dormer:
                dormer["style"] = wd.get("style")
                dormer["crest_x"] = fr.x(wd["crest_W"])
                dormer["hood_front"] = fr.x(wd["hood_front_W"])
                west["stable_roof"]["dormer"] = dormer
        alcove = raw.get("north_entry_alcove")
        if alcove:
            p.detail["north_entry_alcove"] = {
                "x": sorted(fr.x(v) for v in alcove["opening_W"]),
                "front_y": fr.y(0), "back_y": fr.y(alcove["back_S"]),
                "east_x": fr.x(alcove["inner_east_W"]),
                "landing_z": fr.zval(alcove["landing_z"]),
                "threshold_z": fr.zval(alcove["threshold_z"]),
                "front_steps": alcove["front_steps"],
                "front_run": alcove["front_run_ft"]*FT,
                "stair_steps": alcove["stair_steps"],
                "stair_x": sorted(fr.x(v) for v in alcove["stair_W"]),
                "stair_y": sorted(fr.y(v) for v in alcove["stair_S"]),
                "door_y": sorted(fr.y(v) for v in alcove["door_S"]),
                "door_top": fr.zval(alcove["door_top"]),
                "window_x": sorted(fr.x(v) for v in alcove["window_W"]),
                "window_z": [fr.z(v) for v in alcove["window_z"]],
                "cheek_x": sorted(fr.x(v) for v in alcove["cheek_W"]),
                "cheek_top": fr.zval(alcove["cheek_top"])}
            for o in p.openings:
                if o["face"] == "north" and o["kind"] == "arch" and o["u1"]-o["u0"] > 3:
                    o["style"] = "north_entry_alcove"
        cr = raw.get("copper_return")
        if cr:
            p.detail["copper_return"] = {"x0": min(fr.x(w) for w in cr["W"]),
                "x1": max(fr.x(w) for w in cr["W"]),
                "y0": min(fr.y(s) for s in cr["S"]),
                "y1": max(fr.y(s) for s in cr["S"]),
                "wall_top_z": fr.zval(cr["wall_top"]),
                "rise_m": float(cr["rise_ft"]) * FT, "conf": cf("v4_detail")}
        p.detail["bow_garden_windows"] = int(raw.get("bow_garden_windows", 2))
        p.detail["dining_garden_window_facets"] = list(raw.get("dining_garden_window_facets", [0,2,4]))
        if raw.get("dining_garden_window_z"):
            p.detail["dining_garden_window_z"] = [fr.z(v) for v in raw["dining_garden_window_z"]]
        if raw.get("chimney_details"):
            p.detail["chimney_details"] = raw["chimney_details"]
        if raw.get("tower_stair_windows"):
            tw = raw["tower_stair_windows"]
            p.detail["tower_stair_windows"] = {"lantern_panes": tw.get("lantern_panes", [2,3]), "openings": [
                {"angle": math.radians(w["azimuth_deg"]), "width_m": w["width_ft"] * FT,
                 "z0": fr.z(w["z"][0]), "z1": fr.z(w["z"][1])}
                for w in tw.get("slits", []) + tw.get("lantern", [])],
                "bands": [[fr.z(v) for v in tw[key]] for key in
                          ("lantern_sill_band_z", "lantern_lintel_band_z") if key in tw]}
        bt = raw.get("bow_terrace")
        if bt:
            p.detail["bow_terrace"] = {"cx": fr.x(bt["centre_W"]), "cy": fr.y(bt["centre_S"]),
                "r": bt["outer_r_ft"] * FT, "z1": fr.zval(bt["top_z"]),
                "coping_m": bt["coping_ft"] * FT, "thick_m": bt["wall_thickness_ft"] * FT,
                "window_count": bt["window_count"], "window_z": [fr.z(v) for v in bt["window_z"]],
                "parapet_m": float(bt.get("parapet_height_ft", 2.2)) * FT,
                "stair_steps": int(bt.get("stair_steps", 9))}
        p.detail["bow_first_floor_central_door"] = bool(raw.get("bow_first_floor_central_door"))
        service_stair = raw.get("north_court_service_stair")
        if service_stair:
            p.detail["north_court_service_stair"] = {
                "landing_x": sorted(fr.x(v) for v in service_stair["landing_W"]),
                "landing_y": sorted(fr.y(v) for v in service_stair["landing_S"]),
                "flight_x": sorted(fr.x(v) for v in service_stair["flight_W"]),
                "flight_y": sorted(fr.y(v) for v in service_stair["flight_S"]),
                "landing_z": fr.zval(service_stair["landing_z"]),
                "steps": int(service_stair["steps"]),
                "rail_height_m": float(service_stair["rail_height_ft"]) * FT}
        un = raw.get("underpass")
        if un:
            p.detail["underpass"] = {"pts": [fr.xy(v) for v in un["plan_WS"]],
                "ceiling_prairie_z": fr.zval(un["ceiling_prairie"]),
                "ceiling_court_z": fr.zval(un["ceiling_court"]), "floor_z": fr.zval(un["floor"])}
        p.detail["porte_cochere_open_deg"] = raw.get("porte_cochere_open_deg", 82)
        gd = raw.get("gable_details", {})
        en = gd.get("east_north")
        if en:
            a,b = sorted(fr.x(v) for v in en["date_stone_W"])
            p.detail["date_stones"] = [{"axis": "y", "sign": 1, "at": fr.y(0),
                "u0": a, "u1": b, "z0": fr.z(en[key][0]), "z1": fr.z(en[key][1]),
                "text": en[textkey]} for key,textkey in [("date_stone_z","date_text"),("ad_stone_z","ad_text")]]
        sn = gd.get("stable_north")
        if sn:
            a,b = sorted(fr.x(v) for v in sn["pigeon_ledge_W"])
            p.detail["pigeon_ledge"] = {"axis": "y", "sign": 1, "at": fr.y(0),
                "u0": a, "u1": b, "z0": fr.z(sn["pigeon_ledge_z"][0]),
                "z1": fr.z(sn["pigeon_ledge_z"][1]), "projection_m": sn["projection_ft"] * FT}
        p.detail["joinery"] = {k: (float(v)*FT if k.endswith("_ft") else v)
                               for k,v in raw.get("joinery", {}).items()}
        if raw.get("bow_garden_window_z") and not bt:
            for bow in p.bows:
                bow["light_rows"].insert(0, [fr.z(v) for v in raw["bow_garden_window_z"]])
    p.validate()
    return p
