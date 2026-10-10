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
# T-2293: the K04 roof library — fabrics, and the profiles its caps, valleys, apron,
# gutters and pipes are built to. Read here, not in the builder, so every number the
# roof is built from is a resolved parameter and is in the mesh's input hash.
K04 = ROOT / "data" / "components" / "prairie_1904" / "k04_roofs.json"
WINDOW_KIT = ROOT / "data" / "components" / "prairie_1904" / "k06_windows.json"
BAY_KIT = ROOT / "data" / "components" / "prairie_1904" / "k08_bays.json"
ENTRANCE_KIT = ROOT / "data" / "components" / "prairie_1904" / "k07_entrances.json"

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
    roof: dict = field(default_factory=dict)       # T-2293: covering, caps, flashing (K04)
    dormer: dict = field(default_factory=dict)     # T-2293: the front dormer, if any
    rainwater: dict = field(default_factory=dict)  # T-2293: gutters, outlets, pipes (K04)
    # T-2298: the K06 variant each K01 opening kind is glazed with (k06_windows.json)
    window_kit: dict = field(default_factory=dict)
    # T-2304: the K07 variant the door and its stoop are built from (k07_entrances.json),
    # and the front yard its stair may not reach past: {"variant", "front_yard_m"}
    entrance_kit: dict = field(default_factory=dict)
    service_wall_brick: str = ""      # the K03 panel the brick walls wear (T-2291)
    # T-2308: K08 bays keyed to a wall — each a resolved kit variant with its wall, its
    # centre along that wall, its span there and the fabric its masonry is laid in
    bays: tuple = ()
    street_front_trim: dict = field(default_factory=dict)   # K09 heads, entrance, aprons (T-2310)
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
    "basement_lights", "roof_covering", "dormer", "rainwater", "window_kit", "service_wall_brick",
    "entrance_kit", "street_front_trim", "bays",
})

WALLS = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.rear_service", "k01.wall.side.south")


def _k04(covering: dict, rain: dict, pitch: float) -> tuple[dict, dict]:
    """The K04 roof and rainwater parameters (T-2293): the record names fabrics and
    kinds; k04_roofs.json says what each is and what it may cover."""
    lib = json.loads(K04.read_text())
    fabrics = {f["id"]: f for f in lib["fabrics"]}
    prof = lib["profiles"]
    cov, flash = covering.get("fabric"), covering.get("flashing")
    if cov not in lib["slots"]["covering"]:
        raise ParamError(f"roof_covering.fabric {cov!r} is not a K04 covering fabric")
    if flash not in lib["slots"]["flashing"]:
        raise ParamError(f"roof_covering.flashing {flash!r} is not a K04 flashing fabric")
    for r in lib["restrictions"]:
        if r["fabric"] == cov:  # a restricted fabric is never a main roof without its own evidence
            raise ParamError(f"{cov} is restricted ({r['rule']}) as a main roof covering: {r['why']}")
    module = fabrics[cov]["module"]
    if fabrics[cov]["kind"] == "slate":
        lap = prof["slate_exposure"]["headlap_m"]
        if pitch < 25:
            raise ParamError(f"a {pitch} deg roof is not slated (k04 slate_exposure: {lap['below_25']})")
        want = lap["pitch_45_up"] if pitch >= 45 else lap["pitch_25_to_45"]
        if module["headlap_m"] < want - 1e-9:
            raise ParamError(f"{cov} is cut for a {module['headlap_m']} m headlap and a {pitch} deg "
                             f"roof needs {want} m (k04 slate_exposure.headlap_m); steepen the roof "
                             f"or choose a slate cut for it — never stretch the courses to fit")
    if covering.get("caps") != "copper_ridge_roll":
        raise ParamError("k01_frontage caps its hips and ridge with k04 hip_ridge_caps.copper_ridge_roll; "
                         "a slate saddle is another cap")
    caps = prof["hip_ridge_caps"]["copper_ridge_roll"]
    roof = {
        "covering": cov, "flashing": flash,
        "tile_m": list(fabrics[cov]["tile_m"]),
        "slate_thickness_m": module.get("thickness_m", 0.0064),
        "eave_overhang_m": prof["cut_edges"]["eave"]["overhang_m"],
        "cap_roll_diameter_m": caps["roll_diameter_m"],
        "cap_flange_m": caps["flange_width_m"],
        "valley_exposed_at_top_m": prof["valley_flashing"]["exposed_width_at_ridge_m"],
        "valley_widening_per_m": prof["valley_flashing"]["exposed_width_widening_per_m"],
        "valley_crimp_m": prof["valley_flashing"]["standing_crimp_m"],
        "apron_lap_m": prof["dormer_apron"]["apron_lap_over_covering_m"],
        "apron_upstand_m": prof["dormer_apron"]["upstand_m"],
        "step_leg_m": prof["dormer_apron"]["step_flashing_m"]["leg"],
        "step_upstand_m": prof["dormer_apron"]["step_flashing_m"]["upstand"],
    }
    gk, pk = rain.get("gutter"), rain.get("downpipe")
    g, d = prof["gutter"], prof["downpipe"]
    if gk != "half_round":
        raise ParamError("k01_frontage hangs a half_round gutter on brackets; a built-in box is another eave")
    if rain.get("fabric") not in g["kinds"][gk]["fabrics"]:
        raise ParamError(f"rainwater.fabric {rain.get('fabric')!r} is not a K04 {gk} gutter fabric")
    if pk not in d["kinds"] or rain.get("ends_at") not in d["ends_at"]:
        raise ParamError("rainwater.downpipe / ends_at are not K04 downpipe kinds")
    pipes = []
    for x in rain.get("downpipes", []):
        if x["wall"] not in WALLS or x["wall"] == "k01.wall.side.north":
            raise ParamError(f"a downpipe on {x['wall']!r}: the north wall closes the Glessner "
                             f"court 0.02 m off its face, so no pipe stands there")
        pipes.append({"wall": x["wall"], "s_m": float(x["s_m"])})
    if not pipes:
        raise ParamError("every gutter outlet leads to a pipe: rainwater.downpipes is empty")
    rainwater = {
        "fabric": rain["fabric"], "ends_at": rain["ends_at"],
        "gutter_diameter_m": g["kinds"][gk]["diameter_m"], "fall": g["fall"],
        "bracket_spacing_m": g["bracket"]["spacing_m"], "bracket_section_m": list(g["bracket"]["section_m"]),
        "outlet_spacing_max_m": g["outlet"]["spacing_max_m"],
        "pipe_diameter_m": d["kinds"][pk]["diameter_m"], "strap_spacing_m": d["strap_spacing_m"],
        "pipe_offset_from_wall_m": d["offset_from_wall_m"],
        "shoe_kick_deg": d["shoe"]["kick_deg"], "shoe_length_m": d["shoe"]["length_m"],
        "shoe_end_above_grade_m": d["shoe"]["end_above_grade_m"],
        "downpipes": pipes,
    }
    return roof, rainwater

# T-2308: the K08 kinds a K01 frontage can carry. A bay or a full-height projection
# stands on grade against one wall under its own roof; an oriel's corbels and a
# tower's cap meet the main eave and roof, which this assembly does not cut.
BAY_KINDS = ("bay", "projection")
BAY_FABRICS = ("stone", "brick")
BAY_PIER_M = 0.30          # masonry left between a bay's junction and its wall's corner


def _bay_span(plan: dict) -> tuple:
    """Where a bay's plan meets its host wall: (left, right) metres about its centre."""
    if plan["kind"] == "polyline":
        return float(plan["points"][0][0]), float(plan["points"][-1][0])
    if plan["kind"] == "bow":
        return -float(plan["chord_m"]) / 2, float(plan["chord_m"]) / 2
    raise ParamError(f"a K01 bay's plan is a polyline or a bow, not a {plan['kind']}")


def _bays(entries, wall_len: dict, openings: list, structure_id: str):
    """Resolve the record's `bays` against the K08 kit; drop the host openings each covers.

    A bay stands in front of its wall from grade to its own wall top, so every host
    opening in that span below the top is behind it and is not cut; one that straddles a
    junction is refused, since half a window behind a bay's cheek is no window at all.
    """
    import copy as _copy
    kit = {v["id"]: v for v in json.loads(BAY_KIT.read_text())["variants"]}
    out = []
    for e in entries or ():
        if e["variant"] not in kit:
            raise ParamError(f"bays: {e['variant']} is not a K08 variant (k08_bays.json)")
        v = _copy.deepcopy(kit[e["variant"]])
        if v["kind"] not in BAY_KINDS or v["base"] != "grade":
            raise ParamError(f"bays: {v['id']} is a {v['kind']} off {v['base']}; a K01 frontage carries "
                             f"{' and '.join(BAY_KINDS)} on grade only")
        if e["wall"] not in wall_len:
            raise ParamError(f"bays: {e['wall']} is not one of this assembly's walls")
        if e.get("fabric", "stone") not in BAY_FABRICS:
            raise ParamError(f"bays: fabric {e.get('fabric')!r} is not one of {BAY_FABRICS}")
        v["id"] = f"{structure_id}|{e['id']}"
        for k in ("storeys", "roof"):
            if k in e:
                v[k] = _copy.deepcopy(e[k])
        s = float(e["s_m"])
        lo, hi = _bay_span(v["plan"])
        a, b = s + lo, s + hi
        if a < BAY_PIER_M - 1e-9 or b > wall_len[e["wall"]] - BAY_PIER_M + 1e-9:
            raise ParamError(f"bays: {e['id']} meets {e['wall']} at s {a:.3f}..{b:.3f}, closer than "
                             f"{BAY_PIER_M} m to a corner of its {wall_len[e['wall']]} m wall")
        top = sum(float(st["height_m"]) for st in v["storeys"])
        for o in list(openings):
            if o.wall != e["wall"]:
                continue
            o0, o1 = o.s_m - o.width_m / 2 - 0.12, o.s_m + o.width_m / 2 + 0.12   # the lintel's horns
            if o1 <= a or o0 >= b or o.sill_m >= top:
                continue
            if o.component == "k01.opening.door_leaf":
                raise ParamError(f"bays: {e['id']} stands in front of the entrance")
            if o0 < a or o1 > b:
                raise ParamError(f"bays: {e['id']}'s junction at s {a:.3f}..{b:.3f} cuts the opening at "
                                 f"s {o.s_m} on {o.wall}")
            openings.remove(o)
        out.append({"id": e["id"], "wall": e["wall"], "s_m": s, "span_m": (round(a, 4), round(b, 4)),
                    "fabric": e.get("fabric", "stone"), "variant": v})
    return tuple(out)


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

    k04, rainwater = _k04(val("roof_covering") or {}, val("rainwater") or {}, pitch)
    dormer = {}
    d = val("dormer")
    if d:
        dw, dh = float(d["sash"]["width_m"]), float(d["sash"]["height_m"])
        _within(dw, cw, "dormer.sash.width_m")
        _within(dh, ch, "dormer.sash.height_m")
        dpitch = float(d["pitch_deg"])
        pr = roof["parameters"]["pitch_deg"]["ranges"]
        _within(dpitch, (pr["ordinary"][0], pr["steep"][1]), "dormer.pitch_deg")
        dormer = {"width_m": float(d["width_m"]), "face_setback_m": float(d["face_setback_m"]),
                  "face_height_m": float(d["face_height_m"]), "pitch_deg": dpitch,
                  "verge_m": float(d["verge_m"]), "face_thickness_m": float(d["face_thickness_m"]),
                  "sash": {"sill_m": float(d["sash"]["sill_m"]), "width_m": dw, "height_m": dh}}
        if dormer["sash"]["sill_m"] + dh + 0.30 > dormer["face_height_m"] - 0.05:
            raise ParamError("the dormer sash's lintel runs into its eave")
        if dormer["sash"]["sill_m"] - 0.10 < k04["apron_upstand_m"]:
            raise ParamError("the dormer sash's sill sits on its apron's upstand")

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
    # T-2304: the door and its stoop are a K07 entrance. The K01 wall cuts a rectangular
    # hole at the principal floor, so only a flat-headed principal entrance on a straight
    # stoop fits it; the stair is solved from this record's own floor, tread, landing and
    # width, and it must agree with the K01 stair's whole risers and stay in the front yard.
    ek = val("entrance_kit") or {}
    door_kit = dict(ek.get("k01.opening.door_leaf") or {})
    ekit = json.loads(ENTRANCE_KIT.read_text())
    evs = {v["id"]: v for v in ekit["variants"]}
    ev = evs.get(door_kit.get("variant"))
    if ev is None:
        raise ParamError("entrance_kit names no K07 variant for k01.opening.door_leaf (k07_entrances.json)")
    if ev["head"] != "flat" or ev["use"] != "principal" or ev["stair"]["kind"] != "straight":
        raise ParamError(f"entrance_kit: {ev['id']} is a {ev['head']}-headed {ev['use']} entrance on a "
                         f"{ev['stair']['kind']} stair; a K01 front cuts a rectangular hole at the "
                         f"principal floor over a straight stoop")
    yard = float(door_kit.get("front_yard_m", 0.0))
    reach = float(val("stair_landing_depth_m")) + (risers - 1) * tread
    if not reach < yard:
        raise ParamError(f"entrance_kit: the stoop reaches {reach:.2f} m from the front, and the public "
                         f"walk's inner edge is {yard:.2f} m (front_yard_m)")
    k07_risers = max(1, round(pf / ekit["parts"]["stair"]["riser_target_m"]))
    if k07_risers != risers:
        raise ParamError(f"entrance_kit: K07 solves {pf} m in {k07_risers} risers and the K01 stair in "
                         f"{risers}; one stoop cannot be both")
    door_kit = {"variant": ev["id"], "front_yard_m": yard}
    # T-2291: the brick walls wear a K03 panel the record names; k03_brick lays one
    from . import k03_brick
    panel = val("service_wall_brick", k03_brick.PANEL)
    if panel != k03_brick.PANEL:
        raise ParamError(f"service_wall_brick = {panel!r}: k03_brick lays {k03_brick.PANEL!r} alone; "
                         f"another K03 panel is a new slot in generators/archetypes/k03_brick.py")

    bays = _bays(val("bays"), {"k01.wall.street_front": width, "k01.wall.rear_service": width,
                               "k01.wall.side.south": depth, "k01.wall.side.north": depth},
                 openings, (record or {}).get("id", ""))

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
        roof=k04, dormer=dormer, rainwater=rainwater,
        window_kit={k: kit[k] for k in sorted(kit)}, entrance_kit=door_kit, bays=bays,
        street_front_trim=dict(val("street_front_trim", {}) or {}),
        confidence={n: form[n].get("confidence", "reconstructed") for n in names if n in form}
                   | {"footprint": (phase.get("footprint") or {}).get("confidence", "reconstructed")},
    )
    return params
