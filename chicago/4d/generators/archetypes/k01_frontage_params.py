"""Resolve a K01 frontage record into the parameters its components are built from.

TICKET T-2266, the first assembly built to the Prairie 1904 K01 metric component
contract (`data/components/prairie_1904/k01_contract.json`, T-2265). The contract
declares four families — wall, opening, roof, stair — with their parameters in
metres, their datums and their starting ranges; this module reads one structure
phase, resolves the datums (grade, walk, basement sill, principal floor, floor_2,
floor_3, eave, ridge) and REFUSES any value outside the range the contract
declares for it. A range is a prior from RECONSTRUCTION-RULES.md, so a value taken
inside it is still `reconstructed` and says so on the record; the refusal is what
stops a number drifting out of the bounds the programme agreed.

Pure Python, no Blender: `generators/archetypes/k01_frontage.py` writes the glTF
itself (see its docstring for why), and `mesh_inputs.resolve_params` imports this
module to hash what the builder sees.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data" / "components" / "prairie_1904" / "k01_contract.json"
WINDOW_KIT = ROOT / "data" / "components" / "prairie_1904" / "k06_windows.json"

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# A house stands on the ground over its whole outline, like a masonry house.
VERTICAL_ANCHOR = "ground"
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid K01 parameters."""


def _contract() -> dict:
    return json.loads(CONTRACT.read_text())


def _family(c: dict, name: str) -> dict:
    return next(f for f in c["families"] if f["family"] == name)


def _within(value: float, rng, what: str) -> None:
    lo, hi = rng
    if not (lo - 1e-9 <= value <= hi + 1e-9):
        raise ParamError(f"{what} = {value} is outside the K01 contract's range "
                         f"[{lo}, {hi}] (k01_contract.json); widen the contract or "
                         f"change the record, never the generator")


@dataclass(frozen=True)
class Opening:
    """One cut opening in one wall: its K01 component id and its four edges."""

    component: str          # k01.opening.<variant>
    wall: str               # which wall component it is cut through
    s_m: float              # centre, metres along the wall from its left end
    sill_m: float           # sill datum above grade
    width_m: float
    height_m: float
    meeting_rail: bool = True

    @property
    def head_m(self) -> float:
        return self.sill_m + self.height_m


@dataclass
class K01FrontageParams:
    depth_m: float                    # footprint u extent: the side walls' length
    width_m: float                    # footprint v extent: the street front's length
    stories: int
    principal_floor_m: float
    storey_heights_m: tuple
    front_thickness_m: float
    side_thickness_m: float
    roof_pitch_deg: float
    eave_overhang_m: float
    riser_m: float
    tread_m: float
    risers: int
    landing_depth_m: float
    stoop_width_m: float
    entrance_bay: str
    front_bays: tuple                 # bay centres along the street front, south to north
    side_bays: tuple                  # window centres along the south wall, west to east
    rear_bays: tuple                  # window centres along the rear wall, north to south
    basement_sill_m: float
    openings: tuple = ()
    # T-2298: the K06 variant each K01 opening kind is glazed with (k06_windows.json)
    window_kit: dict = field(default_factory=dict)
    service_wall_brick: str = ""      # the K03 panel the brick walls wear (T-2291)
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def floors_m(self) -> tuple:
        """Finished floor datums, principal floor first."""
        out, y = [], self.principal_floor_m
        for h in self.storey_heights_m:
            out.append(round(y, 4))
            y += h
        return tuple(out)

    @property
    def eave_m(self) -> float:
        return round(self.principal_floor_m + sum(self.storey_heights_m), 4)

    @property
    def ridge_m(self) -> float:
        return round(self.eave_m + self.width_m / 2 * math.tan(math.radians(self.roof_pitch_deg)), 4)


CONSUMED = frozenset({
    "stories", "construction", "principal_floor_m", "storey_heights_m",
    "wall_thickness_front_m", "wall_thickness_side_m", "roof_form", "roof_pitch_deg",
    "eave_overhang_m", "stair_tread_m", "stair_landing_depth_m", "stoop_width_m",
    "entrance_bay", "front_bays", "side_bays", "rear_bays", "sash_by_storey",
    "basement_lights", "window_kit", "service_wall_brick",
})


def from_phase(phase: dict, record: dict | None = None) -> K01FrontageParams:
    form = phase.get("form", {})
    unknown = sorted(set(form) - CONSUMED)
    if unknown:
        raise ParamError(f"form attribute(s) {unknown} are not read by k01_frontage — "
                         f"an attribute nothing builds from is a claim the mesh ignores")

    def val(attr, default=None):
        a = form.get(attr)
        return default if a is None else a.get("value", default)

    poly = (phase.get("footprint") or {}).get("polygon") or []
    us = sorted({round(float(p[0]), 4) for p in poly})
    vs = sorted({round(float(p[1]), 4) for p in poly})
    if len(poly) != 4 or len(us) != 2 or len(vs) != 2 or us[0] != 0.0 or vs[0] != 0.0:
        raise ParamError("a K01 frontage's footprint is a rectangle from its own (0, 0): "
                         "the plan origin rule of k01_contract.json frame.plan_origin")
    depth, width = us[1], vs[1]

    c = _contract()
    wall, opening, roof, stair = (_family(c, n) for n in ("wall", "opening", "roof", "stair"))
    datum = {d["id"]: d for d in c["datums"]}

    if val("roof_form") != "hip":
        raise ParamError("k01_frontage builds the contract's k01.roof.hip only")
    if val("construction") != "brick_with_stone_front":
        raise ParamError("k01_frontage builds a stone street front on common-brick side and "
                         "rear walls; another construction is another assembly")

    stories = int(val("stories"))
    heights = tuple(float(h) for h in val("storey_heights_m"))
    if len(heights) != stories:
        raise ParamError(f"{len(heights)} storey heights for {stories} storeys")
    pf = float(val("principal_floor_m"))
    _within(pf, datum["principal_floor"]["range_m"], "principal_floor_m")
    ft, st = float(val("wall_thickness_front_m")), float(val("wall_thickness_side_m"))
    for t, what in ((ft, "wall_thickness_front_m"), (st, "wall_thickness_side_m")):
        _within(t, wall["parameters"]["thickness_m"]["ranges"]["masonry"], what)
    pitch = float(val("roof_pitch_deg"))
    _within(pitch, roof["parameters"]["pitch_deg"]["ranges"]["ordinary"], "roof_pitch_deg")
    if depth <= width:
        raise ParamError("a hip roof over this plan needs the side walls longer than the "
                         "front, or its ridge has no length")

    # The stair solves to the principal floor in WHOLE risers (datums: principal_floor).
    tread = float(val("stair_tread_m"))
    _within(tread, stair["parameters"]["tread_m"]["range"], "stair_tread_m")
    rng = stair["parameters"]["riser_m"]["range"]
    risers = max(1, round(pf / ((rng[0] + rng[1]) / 2)))
    riser = pf / risers
    _within(riser, rng, "riser_m (principal floor / whole risers)")

    floors, y = [], pf
    for h in heights:
        floors.append(y)
        y += h
    eave = y

    openings = []
    sash = val("sash_by_storey")
    if len(sash) != stories:
        raise ParamError("sash_by_storey needs one row per storey")
    cw, ch = opening["parameters"]["clear_width_m"]["range"], opening["parameters"]["clear_height_m"]["range"]
    front_bays = tuple(float(s) for s in val("front_bays"))
    entrance = val("entrance_bay")
    door_s = front_bays[-1] if entrance == "north" else front_bays[0]
    for k, row in enumerate(sash):
        sill = floors[k] + float(row["sill_above_floor_m"])
        w, h = float(row["width_m"]), float(row["height_m"])
        _within(w, cw, f"sash_by_storey[{k}].width_m")
        _within(h, ch, f"sash_by_storey[{k}].height_m")
        head = sill + h
        if k + 1 < stories and head + 0.30 > floors[k + 1] + float(sash[k + 1]["sill_above_floor_m"]) - 0.10:
            raise ParamError(f"storey {k}'s heads run into storey {k + 1}'s sills")
        if k + 1 == stories and head + 0.30 > eave - float(val("eave_overhang_m")) * math.tan(math.radians(pitch)) - 0.25:
            raise ParamError("the top storey's lintels run into the soffit")
        for s in front_bays:
            if k == 0 and s == door_s:
                continue
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.street_front", s, round(sill, 4), w, h))
        for s in val("side_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.south", float(s), round(sill, 4), w, h))
        for s in val("rear_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.rear_service", float(s), round(sill, 4), w, h))
    openings.append(Opening("k01.opening.door_leaf", "k01.wall.street_front", door_s, round(pf, 4), 1.20, 2.70, False))
    bl = val("basement_lights")
    bsill = float(bl["sill_m"])
    for s in front_bays:
        if s != door_s:
            openings.append(Opening("k01.opening.area_light", "k01.wall.street_front", s, bsill,
                                    float(bl["width_m"]), float(bl["height_m"]), False))
    if bsill + float(bl["height_m"]) + 0.30 > pf + float(sash[0]["sill_above_floor_m"]) - 0.10:
        raise ParamError("the basement lights' lintels run into the principal storey's sills")

    # T-2298: every glazed K01 opening is built from a K06 variant. The K01 wall cuts a
    # rectangular hole, so only a flat-headed variant fits it; an arched head is a
    # different hole and a different wall, not a swap of this attribute.
    kit = {}
    variants = {v["id"]: v for v in json.loads(WINDOW_KIT.read_text())["variants"]}
    for comp, entry in sorted((val("window_kit") or {}).items()):
        # a variant id, or {"variant": id, "well": false} where the record's own datums
        # put a basement light's sill above grade and so leave its area well out
        entry = {"variant": entry} if isinstance(entry, str) else dict(entry)
        kit[comp] = {"variant": entry["variant"], "well": bool(entry.get("well", True))}
    for comp in sorted({o.component for o in openings} - {"k01.opening.door_leaf"}):
        vid = kit.get(comp, {}).get("variant")
        if vid not in variants:
            raise ParamError(f"window_kit names no K06 variant for {comp} (k06_windows.json)")
        v = variants[vid]
        if v["head"] != "flat":
            raise ParamError(f"window_kit: {vid} has a {v['head']} head, and a K01 wall cuts "
                             f"a rectangular hole")
        if v.get("well") and kit[comp]["well"] and comp == "k01.opening.area_light" and bsill > 0:
            raise ParamError(f"window_kit: {vid} sits in an area well, but these basement "
                             f"lights' sills stand {bsill} m above grade; set \"well\": false")
        if v["operation"].startswith("double_hung") != any(
                o.meeting_rail for o in openings if o.component == comp):
            raise ParamError(f"window_kit: {vid} is {v['operation']}, which {comp} is not")
    # T-2291: the brick walls wear a K03 panel the record names; k03_brick lays one
    from . import k03_brick
    panel = val("service_wall_brick", k03_brick.PANEL)
    if panel != k03_brick.PANEL:
        raise ParamError(f"service_wall_brick = {panel!r}: k03_brick lays {k03_brick.PANEL!r} alone; "
                         f"another K03 panel is a new slot in generators/archetypes/k03_brick.py")

    names = sorted(CONSUMED)
    params = K01FrontageParams(
        depth_m=depth, width_m=width, stories=stories, principal_floor_m=pf,
        storey_heights_m=heights, front_thickness_m=ft, side_thickness_m=st,
        roof_pitch_deg=pitch, eave_overhang_m=float(val("eave_overhang_m")),
        riser_m=round(riser, 5), tread_m=tread, risers=risers,
        landing_depth_m=float(val("stair_landing_depth_m")),
        stoop_width_m=float(val("stoop_width_m")), entrance_bay=entrance,
        front_bays=front_bays,
        side_bays=tuple(float(s) for s in val("side_bays")),
        rear_bays=tuple(float(s) for s in val("rear_bays")),
        basement_sill_m=bsill, openings=tuple(openings), service_wall_brick=panel,
        window_kit={k: kit[k] for k in sorted(kit)},
        confidence={n: form[n].get("confidence", "reconstructed") for n in names if n in form}
                   | {"footprint": (phase.get("footprint") or {}).get("confidence", "reconstructed")},
    )
    return params
