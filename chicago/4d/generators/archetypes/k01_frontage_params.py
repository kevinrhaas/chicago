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
# T-2289: the K02 stone library's joint and edge profiles — courses, joints, arrises,
# chips, rock-faced projection, corner bonds, rustication and copings, in metres.
# Read here for the same reason as K04: every number the masonry is laid to is a
# resolved parameter, so a profile edit stales the mesh it moves.
K02 = ROOT / "data" / "components" / "prairie_1904" / "k02_stone_profiles.json"
K02_LIBRARY = ROOT / "assets" / "textures" / "prairie_1904_stone" / "manifest.json"

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
    # T-2342: window centres along the north wall, east to west. None for the party wall
    # K01 was cut for (1808's, 0.02 m off the Glessner court); a corner house's street side
    north_bays: tuple = ()
    roof: dict = field(default_factory=dict)       # T-2293: covering, caps, flashing (K04)
    dormer: dict = field(default_factory=dict)     # T-2293: the front dormer, if any
    rainwater: dict = field(default_factory=dict)  # T-2293: gutters, outlets, pipes (K04)
    chimneys: tuple = ()              # T-2302: stacks joined into the K05 roof solid
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
    wall_head: dict = field(default_factory=dict)   # K10 cornice and cresting (T-2317)
    boundary: dict = field(default_factory=dict)    # K11 fence, gates, piers, wall (T-2319)
    yard: dict = field(default_factory=dict)        # K14 lawn, front walk, service walk (T-2360)
    stone: dict = field(default_factory=dict)      # T-2289: the coursed stone front (K02)
    # T-2366: a stone front read off a photograph (`street_front_openings` and
    # `street_front_dress`): its round-arched groups of lights with their voussoir blocks
    # and keystones, its belts, the stone's top and the frieze over it, the entrance's
    # frontispiece and arched portico, and the iron at its windows — empty for every other house
    arched_front: dict = field(default_factory=dict)
    # T-2343: traced ranges behind the main body, each a brick box with its own storeys,
    # windows and flat deck, standing against the main rear wall or an earlier wing's
    rear_wings: tuple = ()
    # T-2358: the K14 condition kit, opted into per record — {"kit", "built"} — so the walls
    # weather to the house's own age in 1904; empty keeps K03's fixed soot and damp mask
    condition: dict = field(default_factory=dict)
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
    "entrance_kit", "street_front_trim", "wall_head", "bays", "chimneys", "chimney_positions",
    "stone_front", "boundary", "north_bays", "rear_wings", "yard", "condition",
    "street_front_openings", "street_front_dress",
})

#: T-2358: the one condition kit a record may name (K14, T-2324)
CONDITION_KIT = "data/components/prairie_1904/k14_condition.json"

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
def _k02(front: dict) -> dict:
    """The K02 masonry parameters (T-2289): the record names the walling fabric, its
    dressing, the trim fabric, how many courses the rusticated base runs and which
    corners are bonded; everything a stone is laid to — course heights, block lengths,
    joints, arrises, chips, projection, quoin returns, channels, the coping's fall —
    is the profile's (k02_stone_profiles.json), resolved here and refused outside it."""
    if not front:
        return {}
    prof = json.loads(K02.read_text())
    fabrics = prof["fabrics"]
    lib = {m["id"]: m for m in json.loads(K02_LIBRARY.read_text())["materials"]}
    fab, trim = front.get("fabric"), front.get("trim_fabric")
    if fab not in fabrics or fab not in lib:
        raise ParamError(f"stone_front.fabric {fab!r} is not a K02 stone fabric")
    f = fabrics[fab]
    if f["laid_as"] != "coursed_ashlar" or f["pattern_in_map"]:
        raise ParamError(f"stone_front.fabric {fab!r} is laid as {f['laid_as']}: a coursed street "
                         f"front needs a coursed ashlar fabric (random rubble carries its joints in its map)")
    if trim != "dressed_trim":
        raise ParamError("stone_front.trim_fabric: sills, voussoirs, belts and the coping are K02 "
                         "dressed_trim, the one fabric the profiles lay as one piece per member")
    t = fabrics[trim]
    dressing = front.get("dressing")
    rock = tuple(float(x) for x in f["rock_face_projection_m"])
    if dressing not in ("rock_faced", "smooth"):
        raise ParamError("stone_front.dressing is rock_faced or smooth")
    if dressing == "rock_faced" and rock[1] <= 0.0:
        raise ParamError(f"{fab} has no rock-faced projection in its profile: it cannot be laid rock_faced")
    if f["corner_bond"] is None or f["rusticated_base"] is None:
        raise ParamError(f"{fab} declares no corner bond or rusticated base")
    base = int(front.get("rusticated_base_courses", 0))
    lo, hi = f["rusticated_base"]["courses"]
    if not lo <= base <= hi:
        raise ParamError(f"stone_front.rusticated_base_courses = {base} is outside {fab}'s "
                         f"profile [{lo}, {hi}] (k02_stone_profiles.json)")
    corners = tuple(front.get("corner_bond", ()))
    if not set(corners) <= {"south"}:
        # the north wall stands 0.02 m off Glessner's south face (the K01 measure's
        # clearance): a quoin proud of it by its rock face would cross into the landmark
        raise ParamError("stone_front.corner_bond: only the south corner can return; the north "
                         "corner stands 0.02 m from the Glessner house")
    if t["coping"] is None:
        raise ParamError("dressed_trim declares no coping")
    coping_h = float(front.get("coping_height_m", 0.0))
    _within(coping_h, t["course_height_m"], "stone_front.coping_height_m (dressed_trim course_height_m)")

    def edges(x):
        return {"joint_m": x["joint"]["width_m"], "recess_m": x["joint"]["recess_m"],
                "bevel_m": x["arris"]["bevel_m"], "chips_per_m": x["arris"]["chips_per_m"],
                "chip_depth_m": tuple(x["arris"]["chip_depth_m"]),
                "chip_length_m": tuple(x["arris"]["chip_length_m"])}

    return {
        "fabric": fab, "trim": trim, "dressing": dressing,
        "rock_face_m": rock if dressing == "rock_faced" else (0.0, 0.0),
        "course_m": tuple(f["course_height_m"]), "block_m": tuple(f["block_length_m"]),
        "wall": edges(f), "trim_edges": edges(t),
        "trim_course_m": tuple(t["course_height_m"]), "trim_block_m": tuple(t["block_length_m"]),
        "quoin_return_m": tuple(f["corner_bond"]["return_m"]), "corners": corners,
        "base_courses": base, "channel_m": f["rusticated_base"]["channel_width_m"],
        "channel_depth_m": f["rusticated_base"]["channel_depth_m"],
        "coping_height_m": coping_h, "coping_fall": t["coping"]["fall"],
        "coping_overhang_m": t["coping"]["overhang_m"], "drip_groove_m": t["coping"]["drip_groove_m"],
        "fabric_roughness": lib[fab]["mean_roughness"], "trim_roughness": lib[trim]["mean_roughness"],
    }


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
        if "plan" in e:
            # T-2342: a bow drawn on its sheet keeps the sheet's chord and rise; the kit's
            # bow is the shape, never the size. Only a bow, and never past its semicircle:
            # a deeper arc would swing back behind its own junctions
            q = e["plan"]
            if v["plan"]["kind"] != "bow" or q.get("kind") != "bow":
                raise ParamError(f"bays: {e['id']} sizes its plan; only a K08 bow takes the record's chord and rise")
            chord, rise = float(q["chord_m"]), float(q["rise_m"])
            if not 0.0 < rise <= chord / 2:
                raise ParamError(f"bays: {e['id']}'s bow rises {rise} m on a {chord} m chord; a segmental "
                                 f"bow rises more than nothing and at most half its chord")
            v["plan"] = {"kind": "bow", "chord_m": chord, "rise_m": rise}
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


def _arched_front(groups, openings, variants, kit, dress, pf, floors, width, door_s, soffit) -> dict:
    """T-2366: a street front's round-arched groups, as k01_arched_front lays them. Each
    group is one bay's lights in one row (one K06 opening of one or more lights, or a pair
    of them `pair_pier_m` apart): their clear holes as K06 cuts them (the jambs to the
    spring, then K06's own round head), the piers between them, and the voussoir block
    over them — the lights' span plus `arch_ring_m` each side, from the spring to the
    highest crown plus the ring — whose stones radiate from each light's centre. The
    keystone rises from the crown to `keystone_top_m`. `street_front_dress` adds the belts
    that replace K01's own, the stone's top and the frieze over it, the entrance's
    frontispiece and portico, and the iron at the windows."""
    out = []
    for g in groups:
        lights = []
        for i in g["ops"]:
            o = openings[i]
            v = variants[kit[o.component]["variant"]]
            n, mull = int(v.get("bays", 1)), float(v.get("mullion_m", 0.0))
            bw = (o.width_m - mull * (n - 1)) / n
            for k in range(n):
                s0 = o.s_m - o.width_m / 2 + k * (bw + mull)
                lights.append((round(s0, 5), round(s0 + bw, 5), round(o.head_m - bw / 2, 5), round(bw / 2, 5), round(o.sill_m, 5)))
        lights.sort()
        if len({q[2] for q in lights}) != 1 or len({q[4] for q in lights}) != 1:
            raise ParamError(f"{g['component']} in bay {g['bay']}: one voussoir block needs its lights on one sill and spring")
        spring, sill = lights[0][2], lights[0][4]
        ring = g["ring_m"]
        top = round(spring + max(q[3] for q in lights) + ring, 5)
        if g["keystone_top_m"] < top:
            raise ParamError(f"{g['component']} in bay {g['bay']}: the keystone stops at {g['keystone_top_m']} m, "
                             f"inside its voussoir block (top {top} m)")
        cuts = [lights[0][0] - ring] + [(a[1] + b[0]) / 2 for a, b in zip(lights, lights[1:])] + [lights[-1][1] + ring]
        out.append({"component": g["component"], "bay": g["bay"], "ops": tuple(g["ops"]),
                    "lights": tuple(lights), "sill_m": sill, "spring_m": spring, "top_m": top,
                    "cuts": tuple(round(x, 5) for x in cuts),
                    "piers": tuple((a[1], b[0]) for a, b in zip(lights, lights[1:])),
                    "keystone": {"s_m": round((cuts[0] + cuts[-1]) / 2, 5),
                                 "bed_m": round(spring + max(q[3] for q in lights), 5),
                                 "top_m": g["keystone_top_m"], "width_m": g["keystone_m"]}})
    blocks = sorted((g["cuts"][0], g["cuts"][-1], g["sill_m"], g["top_m"]) for g in out)
    for a, b in zip(blocks, blocks[1:]):
        if a[1] > b[0] and a[3] > b[2] and b[3] > a[2]:
            raise ParamError(f"two arched groups' blocks overlap at s {b[0]:.3f}")
    if blocks and (blocks[0][0] < 0.25 or blocks[-1][1] > width - 0.25):
        raise ParamError("an arched group's voussoir block runs within 0.25 m of a corner")
    belts = [tuple(float(y) for y in b) for b in dress.get("belts", [])]
    stone_top = float(dress.get("stone_top_m", soffit))
    if not floors[-1] < stone_top <= soffit:
        raise ParamError(f"street_front_dress.stone_top_m {stone_top} is not between the top floor and the soffit ({soffit:.3f} m)")
    if any(g["keystone"]["top_m"] > stone_top + 1e-9 for g in out):
        raise ParamError("a keystone rises past the stone's top")
    fr = dress.get("frieze")
    if fr:
        if stone_top >= soffit - 0.3:
            raise ParamError("a frieze needs at least 0.3 m between the stone's top and the soffit")
        if not stone_top + 0.05 <= fr["sill_m"] < fr["sill_m"] + fr["height_m"] <= soffit - 0.05:
            raise ParamError("the frieze's lights do not stand inside the frieze")
        hw = fr["width_m"] / 2
        xs = sorted(float(x) for x in fr["s_m"])
        if xs[0] - hw < 0.2 or xs[-1] + hw > width - 0.2 or any(b - a < fr["width_m"] + 0.2 for a, b in zip(xs, xs[1:])):
            raise ParamError("the frieze's lights overlap each other or a corner")
    po = dress.get("portico")
    if po and abs(po["centre_s_m"] - door_s) > 1e-6:
        raise ParamError("the portico stands on the door's axis")
    return {"groups": tuple(out), "belts": tuple(belts), "stone_top_m": stone_top, "frieze": fr or {},
            "frontispiece": dress.get("frontispiece") or {}, "portico": po or {},
            "balconettes": dress.get("balconettes") or {}, "grilles": dress.get("grilles") or {},
            "banded": dress.get("banded") or {}}


WING_SIDES = ("south", "north", "rear")


def wing_walls(w: dict) -> dict:
    """A rear wing's three outer walls, each as (origin, along) in the assembly's frame,
    +X east (u) and -Z north (v), read left to right from outside as the main walls are:
    south from the wing's rear end, north from its front end, the rear from its north end."""
    u0, u1, v0, v1 = w["rect"]
    return {"south": ((u0, 0.0, -v0), (1.0, 0.0, 0.0), u1 - u0),
            "north": ((u1, 0.0, -v1), (-1.0, 0.0, 0.0), u1 - u0),
            "rear": ((u0, 0.0, -v1), (0.0, 0.0, 1.0), v1 - v0)}


def _rear_wings(entries, depth, width, openings, cw, ch, structure_id: str):
    """Resolve the record's `rear_wings` (T-2343): the ranges a sheet draws behind the main
    body, each a rectangle in the footprint frame whose front stands on the main rear wall
    (u = 0) or on the rear wall of a wing listed before it, inside that wall's length.

    A wing covers its host wall from grade to its deck: every host opening in that span
    below the deck is behind it and is not cut, and one that straddles a junction is
    refused, as a bay's. Its own windows are cut in its south, north and rear walls."""
    out = []
    for e in entries or ():
        wid = e["id"]
        u0, u1, v0, v1 = (float(x) for x in e["rect"])
        if not (u0 < u1 <= 0.0 and v0 < v1):
            raise ParamError(f"rear_wings: {wid}'s rect {e['rect']} is not a rectangle behind the main body")
        if e.get("fabric", "brick") != "brick":
            raise ParamError(f"rear_wings: {wid} is {e.get('fabric')!r}; a K01 wing is laid in the K03 brick")
        if abs(u1) < 1e-9:
            host, hv0, hv1, hwall = None, 0.0, width, "k01.wall.rear_service"
        else:
            hosts = [w for w in out if abs(w["rect"][0] - u1) < 1e-9]
            if not hosts:
                raise ParamError(f"rear_wings: {wid} stands on no wall: its front u {u1} is neither the main "
                                 f"rear wall (0) nor the rear of a wing listed before it")
            host = hosts[0]
            hv0, hv1, hwall = host["rect"][2], host["rect"][3], f"k01.wall.wing.{host['id']}.rear"
        if v0 < hv0 - 1e-9 or v1 > hv1 + 1e-9:
            raise ParamError(f"rear_wings: {wid} runs v {v0}..{v1}, past its host wall's {hv0}..{hv1}")
        heights = tuple(float(h) for h in e["storey_heights_m"])
        floor = float(e["floor_m"])
        floors, y = [], floor
        for h in heights:
            floors.append(round(y, 4))
            y += h
        top = round(y, 4)
        roof = e["roof"]
        if roof.get("kind") != "flat":
            raise ParamError(f"rear_wings: {wid}'s roof is a {roof.get('kind')}; a K01 wing is decked flat")
        if roof.get("covering") != "painted_tin_sheet":
            raise ParamError(f"rear_wings: {wid}'s deck is covered in {roof.get('covering')!r}; a K01 wing "
                             f"deck is K04's painted_tin_sheet")
        ov, fas = float(roof["overhang_m"]), float(roof["fascia_m"])
        if not (0.0 <= ov <= 0.6 and 0.1 <= fas <= 0.5):
            raise ParamError(f"rear_wings: {wid}'s deck overhangs {ov} m on a {fas} m fascia, outside "
                             f"0-0.6 m and 0.1-0.5 m")
        deck = round(top + fas, 4)
        sash = e["sash_by_storey"]
        if len(sash) != len(heights):
            raise ParamError(f"rear_wings: {wid}'s sash_by_storey needs one row per storey")
        walls = wing_walls({"rect": (u0, u1, v0, v1)})
        ops = []
        for side, ss in sorted((e.get("windows") or {}).items()):
            if side not in WING_SIDES:
                raise ParamError(f"rear_wings: {wid} has no {side} wall ({', '.join(WING_SIDES)})")
            length = walls[side][2]
            for k, row in enumerate(sash):
                sill = floors[k] + float(row["sill_above_floor_m"])
                w_, h_ = float(row["width_m"]), float(row["height_m"])
                _within(w_, cw, f"rear_wings.{wid}.sash_by_storey[{k}].width_m")
                _within(h_, ch, f"rear_wings.{wid}.sash_by_storey[{k}].height_m")
                if sill + h_ + 0.30 > top:
                    raise ParamError(f"rear_wings: {wid}'s storey {k} heads run into its deck")
                for s in ss:
                    s = float(s)
                    if s - w_ / 2 < 0.30 or s + w_ / 2 > length - 0.30:
                        raise ParamError(f"rear_wings: {wid}'s {side} window at s {s} stands closer than "
                                         f"0.30 m to a corner of its {length:.3f} m wall")
                    ops.append(Opening("k01.opening.sash_flat", f"k01.wall.wing.{wid}.{side}", s,
                                       round(sill, 4), w_, h_))
        # what the wing covers of its host wall: s along that wall, from its left end
        a, b = hv1 - v1, hv1 - v0
        pool = openings if host is None else list(host["openings"])
        for o in list(pool):
            if o.wall != hwall:
                continue
            o0, o1 = o.s_m - o.width_m / 2 - 0.12, o.s_m + o.width_m / 2 + 0.12   # the head's horns
            if o1 <= a or o0 >= b or o.sill_m - 0.15 >= deck:
                continue
            if o0 < a or o1 > b:
                raise ParamError(f"rear_wings: {wid}'s junction at s {a:.3f}..{b:.3f} cuts the opening at "
                                 f"s {o.s_m} on {o.wall}")
            pool.remove(o)
        if host is not None:
            host["openings"] = tuple(pool)
        out.append({"id": wid, "rect": (u0, u1, v0, v1), "host_wall": hwall, "host_span_m": (round(a, 4), round(b, 4)),
                    "floors_m": tuple(floors), "top_m": top, "deck_m": deck, "overhang_m": ov, "fascia_m": fas,
                    "host_v_m": (hv0, hv1), "openings": tuple(ops)})
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
    # T-2341: a plain brick house is the same assembly with its street front laid in the
    # K03 brick too, its openings dressed in stone; which front it is, the record's
    # `stone_front` says — named for a stone front, absent for a brick one
    construction = val("construction")
    if construction not in ("brick_with_stone_front", "brick"):
        raise ParamError("k01_frontage builds a stone or a brick street front on common-brick "
                         "side and rear walls; another construction is another assembly")
    if (construction == "brick_with_stone_front") != bool(val("stone_front")):
        raise ParamError(f"construction {construction!r}: a stone street front names its K02 "
                         "stone_front and a brick one names none")

    stories = int(val("stories"))
    heights = tuple(float(h) for h in val("storey_heights_m"))
    if len(heights) != stories:
        raise ParamError(f"{len(heights)} storey heights for {stories} storeys")
    pf = float(val("principal_floor_m"))
    # T-2366: the contract's starting range binds a principal floor the record reconstructs;
    # one read off a source (a photograph's courses, a drawing) stands on that source
    pfa = form.get("principal_floor_m") or {}
    if pfa.get("confidence", "reconstructed") == "reconstructed":
        _within(pf, datum["principal_floor"]["range_m"], "principal_floor_m")
    elif not pfa.get("sources"):
        raise ParamError(f"principal_floor_m is {pfa.get('confidence')} and names no source: "
                         "outside the contract's starting range only a source can place it")
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
    # T-2366: a street front read off a photograph names its own openings, row by row
    sfo = val("street_front_openings")
    if sfo:
        if entrance != "middle" or len(front_bays) != 3:
            raise ParamError("street_front_openings builds a three-bay front entered in its middle bay")
        door_s = front_bays[1]
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
        for s in (() if sfo else front_bays):
            if k == 0 and s == door_s:
                continue
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.street_front", s, round(sill, 4), w, h))
        for s in val("side_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.south", float(s), round(sill, 4), w, h))
        for s in val("rear_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.rear_service", float(s), round(sill, 4), w, h))
        for s in val("north_bays") or ():
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.north", float(s), round(sill, 4), w, h))
    openings.append(Opening("k01.opening.door_leaf", "k01.wall.street_front", door_s, round(pf, 4), 1.20, 2.70, False))
    # T-2366: a front that names its own openings names its basement lights among them
    bl = val("basement_lights") or {}
    if bool(bl) == bool(sfo):
        raise ParamError("basement_lights names the area lights of a front without street_front_openings, "
                         "and only of one")
    bsill = float(bl.get("sill_m", 0.0))
    for s in (() if sfo else front_bays):
        if s != door_s:
            openings.append(Opening("k01.opening.area_light", "k01.wall.street_front", s, bsill,
                                    float(bl["width_m"]), float(bl["height_m"]), False))
    if not sfo and bsill + float(bl["height_m"]) + 0.30 > pf + float(sash[0]["sill_above_floor_m"]) - 0.10:
        raise ParamError("the basement lights' lintels run into the principal storey's sills")
    arched_rows, arched_groups = [], []
    if sfo:
        # T-2366: each row is one K06 kind at one sill in the bays it names; a basement row
        # sets its lights in pairs about the bay's centre, `pair_pier_m` apart
        for k, row in enumerate(sfo["rows"]):
            comp = row["component"]
            if not comp.startswith("k01.opening.arched_"):
                raise ParamError(f"street_front_openings.rows[{k}]: {comp!r} is not a k01.opening.arched_* kind")
            if "sill_m" in row:
                sill = float(row["sill_m"])
            else:
                sill = floors[int(row["storey"])] + float(row["sill_above_floor_m"])
            w, h = float(row["width_m"]), float(row["height_m"])
            pier = row.get("pair_pier_m")
            for b in row["bays"]:
                c = front_bays[int(b)]
                if int(b) == 1 and sill < pf + 2.7:
                    raise ParamError(f"street_front_openings.rows[{k}] puts a window over the door's bay below its head")
                centres = (c - (w + float(pier)) / 2, c + (w + float(pier)) / 2) if pier else (c,)
                group = {"component": comp, "bay": int(b), "ops": [],
                         "ring_m": float(row["arch_ring_m"]), "keystone_top_m": float(row["keystone_top_m"]),
                         "keystone_m": tuple(float(x) for x in row.get("keystone_m", (0.26, 0.5)))}
                for s in centres:
                    group["ops"].append(len(openings))
                    openings.append(Opening(comp, "k01.wall.street_front", round(s, 4), round(sill, 4), w, h,
                                            not comp.endswith("_basement")))
                arched_groups.append(group)
            arched_rows.append(comp)

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
        if v["head"] != "flat" and not (comp in arched_rows and val("stone_front")):
            raise ParamError(f"window_kit: {vid} has a {v['head']} head, and a K01 wall cuts "
                             f"a rectangular hole")
        if comp in arched_rows and v["head"] != "round":
            raise ParamError(f"window_kit: {comp} is laid under a round arch, and {vid} has a {v['head']} head")
        if v.get("well") and kit[comp]["well"] and comp == "k01.opening.area_light" and bsill > 0:
            raise ParamError(f"window_kit: {vid} sits in an area well, but these basement "
                             f"lights' sills stand {bsill} m above grade; set \"well\": false")
        if v["operation"].startswith("double_hung") != any(
                o.meeting_rail for o in openings if o.component == comp):
            raise ParamError(f"window_kit: {vid} is {v['operation']}, which {comp} is not")
    arched = _arched_front(arched_groups, openings, variants, kit, val("street_front_dress") or {},
                           pf, floors, width, door_s, eave - float(val("eave_overhang_m")) * math.tan(math.radians(pitch)) - 0.20) \
        if sfo else {}
    if val("street_front_dress") and not sfo:
        raise ParamError("street_front_dress dresses a street front laid by street_front_openings")
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
    # T-2313: chimney stacks from the K15 kit (data/components/prairie_1904/k15_chimneys.json),
    # each built by k15_chimneys.stack_solids in the house's own roof and joined into the K05
    # roof solid. The FORM (kit variant, flues, top) is `chimneys`; WHERE each stands is
    # `chimney_positions`, a separate attribute because it rests on a source (the plan's
    # fireplaces) and the form does not.
    chimneys = []
    ch = val("chimneys")
    tp = math.tan(math.radians(pitch))
    if ch and "plan_m" in ch:
        # T-2302's plain stacks, kept for a record that names no K15 variant (1612 Goodman,
        # T-2344): each a closed prism the K05 union joins into the roof, so its penetration
        # through the covering is cut where the two really meet
        sx, sz = (float(v) for v in ch["plan_m"])
        above, cap_p, cap_d = float(ch["top_above_ridge_m"]), float(ch["cap_proud_m"]), float(ch["cap_depth_m"])
        ridge = (round(pf + sum(heights), 4) + width / 2 * tp)
        for st_ in ch["stacks"]:
            u, v = float(st_["u_m"]), float(st_["v_m"])
            if not (sx / 2 + 0.3 <= u <= depth - sx / 2 - 0.3 and sz / 2 + 0.3 <= v <= width - sz / 2 - 0.3):
                raise ParamError(f"chimney at ({u}, {v}) does not stand inside the footprint")
            if above < 0.6:
                raise ParamError("a chimney stops less than 0.6 m above the ridge")
            chimneys.append({"u_m": u, "v_m": v, "plan_m": (sx, sz), "top_m": round(ridge + above, 4),
                             "cap_proud_m": cap_p, "cap_depth_m": cap_d})
    elif ch:
        from . import k15_chimneys as k15
        k15kit = k15.load()
        k15at = {c["stack"]: c for c in val("chimney_positions", [])}
        k15E = round(pf + sum(heights), 4)

        def cover(u, v):   # the hip's covering over a plan point, at the wall line E
            return k15E + tp * max(0.0, min(u, depth - u, v, width - v))
        k15dr = k15kit["draught"]
        for st_ in ch["stacks"]:
            sid = st_["id"]
            if sid not in k15at:
                raise ParamError(f"chimney {sid!r} has no entry in chimney_positions")
            u, v = float(k15at[sid]["u_m"]), float(k15at[sid]["v_m"])
            k15var = next((x for x in k15kit["variants"] if x["id"] == st_["from"]), None)
            if k15var is None or len(k15var["stacks"]) != 1:
                raise ParamError(f"chimney {sid!r}: {st_['from']!r} is not a one-stack K15 variant")
            spec = {k: v_ for k, v_ in k15var["stacks"][0].items() if k not in ("x", "z")}
            if not st_.get("pots", True):
                spec["flues"] = [{"at": fl["at"]} for fl in spec["flues"]]
            spec["top_m"] = float(st_["top_m"])
            spec["across"] = "x" if st_["width_along"] == "u" else "z"
            # plan_m is (along u, along v), whichever way the stack is turned
            sx, sz = ((spec["width_m"], spec["depth_m"]) if spec["across"] == "x"
                      else (spec["depth_m"], spec["width_m"]))
            if not (sx / 2 + 0.3 <= u <= depth - sx / 2 - 0.3 and sz / 2 + 0.3 <= v <= width - sz / 2 - 0.3):
                raise ParamError(f"chimney {sid!r} at ({u}, {v}) does not stand inside the footprint")
            # K15's draught rule, on this roof: the top clears the covering within the
            # radius by clear_m, and its own emergence by min_above_own_m
            r, k15n = k15dr["radius_m"], 24
            near = max(cover(u + r * (2 * i / k15n - 1), v + r * (2 * j / k15n - 1))
                       for i in range(k15n + 1) for j in range(k15n + 1))
            own = max(cover(u + a * sx / 2, v + b * sz / 2) for a in (-1, 1) for b in (-1, 1))
            need = max(near + k15dr["clear_m"], own + k15dr["min_above_own_m"])
            if spec["top_m"] < need - 1e-9:
                raise ParamError(f"chimney {sid!r} tops at {spec['top_m']} m; K15's draught rule asks "
                                 f"{need:.3f} m (covering {near:.3f} m within {r} m)")
            k15cap = spec["cap"]
            chimneys.append({"id": sid, "from": st_["from"], "u_m": u, "v_m": v, "plan_m": (sx, sz), "top_m": spec["top_m"],
                             "cap_proud_m": k15cap["projection_m"], "cap_depth_m": k15cap["thickness_m"],
                             "k15": spec})
    if chimneys and dormer:
        d_ridge = (dormer["face_setback_m"] * tp + dormer["face_height_m"]
                   + dormer["width_m"] / 2 * math.tan(math.radians(dormer["pitch_deg"])))
        back = depth - d_ridge / tp - 0.5   # where k01_frontage starts the dormer's body
        for c in chimneys:
            sx, sz = c["plan_m"]
            if abs(c["v_m"] - width / 2) < dormer["width_m"] / 2 + 0.5 + sz / 2 and c["u_m"] + sx / 2 > back - 0.3:
                raise ParamError("a chimney stands in the dormer's body")

    # T-2291: the brick walls wear a K03 panel the record names; k03_brick lays one
    from . import k03_brick
    panel = val("service_wall_brick", k03_brick.PANEL)
    if panel != k03_brick.PANEL:
        raise ParamError(f"service_wall_brick = {panel!r}: k03_brick lays {k03_brick.PANEL!r} alone; "
                         f"another K03 panel is a new slot in generators/archetypes/k03_brick.py")

    bays = _bays(val("bays"), {"k01.wall.street_front": width, "k01.wall.rear_service": width,
                               "k01.wall.side.south": depth, "k01.wall.side.north": depth},
                 openings, (record or {}).get("id", ""))

    wings = _rear_wings(val("rear_wings"), depth, width, openings, cw,
                        opening["parameters"]["clear_height_m"]["range"], (record or {}).get("id", ""))

    stone = _k02(val("stone_front") or {})
    if stone:
        # the rusticated base and its coping run up to the area lights' heads, so the
        # coping's top is the line the lights' flat arches spring from (T-2289)
        top = bsill + float(bl["height_m"]) if bl else float((val("street_front_dress") or {}).get("base_top_m", 0.0))
        course = (top - stone["coping_height_m"]) / stone["base_courses"]
        _within(course, stone["course_m"], f"the rusticated base's course height ({stone['fabric']} "
                f"course_height_m; base courses, coping and the area lights' heads must agree)")
        stone["base_course_m"] = round(course, 5)
        stone["coping_top_m"] = round(top, 5)

    # T-1861: a brick street front may lay its windows' heads in the brick, as its side and
    # rear walls do (two rowlock rings on a segmental arch), instead of the stone lintel or
    # K09 head `by_storey` names; the hole stays the K01 rectangle, so the sash stays flat
    trim = dict(val("street_front_trim", {}) or {})
    if trim.get("brick_heads") not in (None, "segmental"):
        raise ParamError("street_front_trim.brick_heads builds 'segmental' alone")
    if trim.get("brick_heads") and construction != "brick":
        raise ParamError("street_front_trim.brick_heads arches the brick; a stone front is laid "
                         "by its K02 stone_front")

    # T-2360: the K14 yard's age is the house's own: the year its phase was built in
    yard = dict(val("yard", {}) or {})
    if yard:
        built_from = ((phase.get("documented_range") or {}).get("from") or "")[:4]
        if str(yard.get("built")) != built_from:
            raise ParamError(f"yard.built {yard.get('built')} is not the phase's own year ({built_from or 'none'}): "
                             f"the kit ages a yard from when its house was built")

    # T-2358: the K14 condition kit. Its water trails hang from the K06 sills, so it needs
    # the sills seated before the walls are cut: a stone front lays its openings first, a
    # brick K01 house its walls, and that order is not this ticket's to change (T-2361)
    condition = {}
    cond = val("condition")
    if cond:
        if cond.get("kit") != CONDITION_KIT:
            raise ParamError(f"condition.kit names {cond.get('kit')!r}; the K14 kit is {CONDITION_KIT}")
        built = cond.get("built")
        if not isinstance(built, int) or not 1830 <= built <= 1904:
            raise ParamError(f"condition.built {built!r} is not a completion year standing by 1904")
        if not stone:
            raise ParamError("condition needs a K02 stone front: a brick K01 house cuts its walls "
                             "before its sills are seated, so no wall could carry a sill's trail")
        # T-2359: the chimney plume lies on a compass bearing, so the kit is read in the
        # house's own frame turned by the placement's rotation (+ clockwise, as buildings.js)
        rotation = float(((phase.get("position") or {}).get("rotation_deg")) or 0.0)
        condition = {"kit": CONDITION_KIT, "built": built, "rotation_deg": rotation}

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
        north_bays=tuple(float(s) for s in val("north_bays") or ()),
        basement_sill_m=bsill, openings=tuple(openings), service_wall_brick=panel,
        roof=k04, dormer=dormer, rainwater=rainwater, chimneys=tuple(chimneys),
        window_kit={k: kit[k] for k in sorted(kit)}, entrance_kit=door_kit, bays=bays,
        street_front_trim=trim,
        wall_head=dict(val("wall_head", {}) or {}),
        boundary=dict(val("boundary", {}) or {}),
        yard=yard,
        stone=stone, rear_wings=wings, condition=condition, arched_front=arched,
        confidence={n: form[n].get("confidence", "reconstructed") for n in names if n in form}
                   | {"footprint": (phase.get("footprint") or {}).get("confidence", "reconstructed")},
    )
    return params
