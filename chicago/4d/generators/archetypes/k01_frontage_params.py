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

import copy
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
K10_KIT = ROOT / "data" / "components" / "prairie_1904" / "k10_cornices.json"
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
    stone_finish: dict = field(default_factory=dict)  # T-1883: pierced stone facade
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
    # T-2350: "hip" (k01.roof.hip) or "flat" (k01.roof.flat, K05's stone-front rowhouse deck
    # behind coped party-wall parapets and a blocking course); `flat` holds the deck's
    # resolved numbers — fascia, parapet thickness, coping, upstand, high line, parapet top
    roof_form: str = "hip"
    flat: dict = field(default_factory=dict)
    # T-2369: the floor the door opens on, when it is not the principal floor (1612's door
    # stands at the head of a short stoop under its portico, a vestibule's height below the
    # hall); 0.0 is the principal floor, every other house's
    entrance_floor_m: float = 0.0
    # T-2370: "mansard" (k01.roof.mansard, K05's mansard ring stack laid on this house);
    # `mansard` holds its resolved numbers — variant, profile, pitches, rise, curb, ridge
    mansard: dict = field(default_factory=dict)
    # T-2476: a brick house painted over its brick (1620, 'olive green in color' in 1887):
    # the paint's linear colour, laid over the K03 brick's own map as its factor, so the
    # courses still read through it; empty for the unpainted brick of every other house
    wall_paint: tuple = ()
    # T-2459: "gable" (k01.roof.gable): a ridge parallel to the street front, a steep street
    # slope and a rear slope down to the same wall head, each side wall carried up as a
    # parapet (1619's crow-stepped south wall, its drawing); `gable` holds its resolved numbers
    gable: dict = field(default_factory=dict)
    # T-2543: the street front carried up as a SHAPED (Flemish) gable over a hip (1812's, its
    # photograph): its outline, slab, lights, kneelers and finial (k01_shaped_gable)
    shaped_gable: dict = field(default_factory=dict)
    # T-2410: a brick street front's round-headed windows — {"storeys", "key"}: the storeys
    # whose street windows are ROUND_HOODED, and the key block over each hood's crown
    round_heads: dict = field(default_factory=dict)
    # T-2753: a front whose windows `street_front_windows` names: its own belts, the dressed
    # quoined surrounds of its lower windows ({"belts", "surrounds"}), and its proud quoined
    # frontispiece with the door's surround, the carved panel over it and the hood mould
    # (`street_front_frontispiece`, resolved by _street_frontispiece) — empty for every other house
    street_dress: dict = field(default_factory=dict)
    frontispiece: dict = field(default_factory=dict)
    # T-2820: a rear section stepping out past a side wall beside the main body's rear part,
    # under its own slated attic (1625's, its sheet and photograph; k01_rear_section) — empty
    # for every other house
    rear_section: dict = field(default_factory=dict)
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def on_frontispiece(self, op) -> bool:
        """T-2753: does this street opening stand on the proud frontispiece (laid on its face)?"""
        fp = self.frontispiece
        return bool(fp) and op.wall == "k01.wall.street_front" and \
            op.s_m - op.width_m / 2 >= fp["s_m"] - 1e-6 and op.head_m <= fp["hood"]["bed_m"] + 1e-6

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

    def stoop_s_m(self, door_s: float) -> float:
        """The stoop's axis along the street front: its door's, unless the entrance kit
        stands it off the door (T-2463). The gate and the front walk line up on it."""
        return self.entrance_kit.get("stoop_v_m", door_s)

    @property
    def door_floor_m(self) -> float:
        """The floor the door opens on and the stoop climbs to."""
        return self.entrance_floor_m or self.principal_floor_m

    @property
    def eave_m(self) -> float:
        return round(self.principal_floor_m + sum(self.storey_heights_m), 4)

    @property
    def ridge_m(self) -> float:
        if self.roof_form == "flat":     # T-2350: the deck's high line, behind the blocking course
            return self.flat["deck_high_m"]
        if self.roof_form == "mansard":  # T-2370: the upper hip's ridge, over the curb
            return self.mansard["ridge_m"]
        if self.roof_form == "gable":    # T-2459: the ridge parallel to the front
            return self.gable["ridge_m"]
        return round(self.eave_m + self.width_m / 2 * math.tan(math.radians(self.roof_pitch_deg)), 4)


CONSUMED = frozenset({
    "stories", "construction", "principal_floor_m", "storey_heights_m",
    "wall_thickness_front_m", "wall_thickness_side_m", "roof_form", "roof_pitch_deg",
    "eave_overhang_m", "stair_tread_m", "stair_landing_depth_m", "stoop_width_m",
    "entrance_bay", "front_bays", "side_bays", "rear_bays", "sash_by_storey",
    "basement_lights", "roof_covering", "dormer", "rainwater", "window_kit", "service_wall_brick",
    "entrance_kit", "street_front_trim", "wall_head", "bays", "chimneys", "chimney_positions",
    "stone_front", "boundary", "north_bays", "mansard", "rear_wings", "rear_section", "yard", "condition",
    "street_front_openings", "street_front_dress", "entrance_floor_m", "street_front_round_heads",
    "front_bays_by_storey", "gable_roof", "wall_finish", "stone_finish", "shaped_gable",
    "street_front_windows", "street_front_frontispiece",
})

#: T-2451: a bay's corner strip -> K01 slot: dressed stone, or painted timber on a frame bay
STRIP_FABRICS = {"stone": "dress_stone", "painted_timber": "bay_strip_paint"}

#: T-2410: the component a brick street front's round-headed window is cut as — K06's round
#: sash in a round hole through the K03 wall, under the kit's own arch band as its hood
ROUND_HOODED = "k01.opening.sash_round_hooded"
#: T-2752: the street windows a stone front read off a photograph names one by one
#: (`street_front_windows`), each a component the record's window_kit glazes
STREET_WINDOW = "k01.opening.street_"

#: T-2358: the one condition kit a record may name (K14, T-2324)
CONDITION_KIT = "data/components/prairie_1904/k14_condition.json"

WALLS = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.rear_service", "k01.wall.side.south")


def _k04(covering: dict, rain: dict, pitch: float, flat: bool = False,
         lower_pitch: float | None = None, gable: bool = False) -> tuple[dict, dict]:
    """The K04 roof and rainwater parameters (T-2293): the record names fabrics and
    kinds; k04_roofs.json says what each is and what it may cover. A flat deck (T-2350)
    has no hip or ridge to cap, and its one eave, the rear fascia, hangs no gutter yet."""
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
    # T-2406: a mansard's steep lower faces in their own fabric (1620's engraving slates
    # them over a tin upper hip); K04's slate rule is read at the lower faces' own pitch
    lower = covering.get("lower_faces")
    if lower is not None:
        if lower_pitch is None:
            raise ParamError("roof_covering.lower_faces covers a mansard's lower faces; this roof is no mansard")
        if lower not in lib["slots"]["covering"] or fabrics[lower]["kind"] != "slate":
            raise ParamError(f"roof_covering.lower_faces {lower!r} is not a K04 slate covering fabric")
        if fabrics[lower]["module"]["headlap_m"] < prof["slate_exposure"]["headlap_m"][
                "pitch_45_up" if lower_pitch >= 45 else "pitch_25_to_45"] - 1e-9 or lower_pitch < 25:
            raise ParamError(f"{lower} is not cut for a {lower_pitch} deg mansard face (k04 slate_exposure)")
    # T-2476: the covering's paint, when a house's own evidence picks one of the fabric's
    # paint_alternatives over the paint its map is drawn in (k04_roofs.json)
    paint = covering.get("paint")
    if paint is not None and paint not in fabrics[cov].get("paint_alternatives", ()):
        raise ParamError(f"roof_covering.paint {paint!r}: {cov} is painted one of "
                         f"{', '.join(fabrics[cov].get('paint_alternatives', ())) or 'nothing'}")
    if flat and covering.get("caps") is not None:
        raise ParamError("a flat K01 roof has no hip or ridge: roof_covering names no caps")
    if flat and fabrics[cov]["kind"] == "slate":
        raise ParamError(f"a {pitch} deg deck is not slated: a flat K01 roof is covered in sheet metal")
    if flat and rain:
        raise ParamError("a flat K01 roof hangs no gutter yet: its one eave is the rear fascia, and "
                         "k01_frontage runs its half-round gutter round a hip's eaves (rainwater is empty)")
    if not flat and covering.get("caps") != "copper_ridge_roll":
        raise ParamError("k01_frontage caps its hips and ridge with k04 hip_ridge_caps.copper_ridge_roll; "
                         "a slate saddle is another cap")
    caps = prof["hip_ridge_caps"]["copper_ridge_roll"]   # the hip's; a flat deck lays none
    roof = {
        "covering": cov, "flashing": flash, **({"lower_covering": lower} if lower else {}),
        **({"paint": paint} if paint and paint != fabrics[cov].get("paint") else {}),
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
    if flat or gable:     # T-2459: a gable roof hangs no gutter yet (from_phase refuses one)
        return roof, {}
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
        if x["wall"] not in WALLS:
            raise ParamError(f"a downpipe on {x['wall']!r}: not a K01 wall")
        # the K01 measure's north wall is the open SOUTH side of a house across the avenue (v
        # runs south there): 1625's photograph hangs its pipe on it, by the front corner
        # (T-2753). On the east side it is 1808's, closing the Glessner court 0.02 m off its
        # face, where nothing may stand: a pipe there stands within 0.5 m of the front
        if x["wall"] == "k01.wall.side.north" and float(x["s_m"]) > 0.5:
            raise ParamError(f"a downpipe on the north wall at s {x['s_m']}: only by the front corner (s <= 0.5 m)")
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
# stands on grade against one wall under its own roof; a tower's cap meets the main
# eave and roof, which this assembly does not cut. T-2369: an oriel stands on its corbel
# courses and stops under the main eave, its own roof leaning on the wall below the
# cornice (1612's south wall), so it is carried too.
BAY_KINDS = ("bay", "projection", "oriel")

#: T-2350: the K05 variant a flat K01 roof is built from (k05_roofs.json)
FLAT_ROOF = "k05.roof.flat_parapet"


def _flat_roof(depth: float, eave: float, pitch: float, overhang: float) -> dict:
    """The numbers a flat K01 roof is built to (T-2350), from K05's stone-front rowhouse deck:
    the deck's rear fascia stands on the walls' top (the eave datum), so the deck's soffit IS
    the wall head; it falls `pitch` from behind the blocking course to that fascia, and the
    side parapets and the blocking course stand level, clearing the deck's high line by the
    variant's upstand. The street cornice projects `overhang` (eave_overhang_m) under them."""
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    v = next(x for x in k5["variants"] if x["id"] == FLAT_ROOF)
    lo, hi = k5["ranges"]["pitch_deg"][v["pitch_range"]]
    _within(pitch, (lo, hi), f"roof_pitch_deg ({FLAT_ROOF}'s fall)")
    p = k5["parts"]
    f, tw = p["eave"]["fascia_depth_m"], p["parapet"]["thickness_m"]
    if not 0.3 <= overhang <= 1.0:
        raise ParamError(f"eave_overhang_m {overhang}: a flat roof's street cornice projects 0.3-1.0 m")
    t = math.tan(math.radians(pitch))
    er = eave + f
    high = er + (depth - tw) * t
    return {"variant": FLAT_ROOF, "fascia_m": f, "parapet_m": tw, "coping_m": p["coping"]["thickness_m"],
            "drip_m": p["coping"]["drip_m"], "upstand_m": float(v["upstand_m"]), "deck_eave_m": round(er, 4),
            "deck_high_m": round(high, 4), "parapet_top_m": round(high + float(v["upstand_m"]), 4)}
#: T-2459: the parapet lines a K01 gable roof's side walls are carried up in
GABLE_PARAPETS = ("stepped", "coped")


def _gable_roof(g: dict, depth: float, width: float, eave: float, pitch: float, side_wall: float) -> dict:
    """The numbers a K01 gable roof is built to (T-2459): the ridge runs along the street
    front `ridge_back_m` behind the front wall's plane, the street slope rises to it at
    roof_pitch_deg from the front eave, and the rear slope falls from it to the rear wall's
    head at whatever pitch that leaves, so both eaves stand on the one wall head. Each side
    wall is carried up as a parapet the wall's own thickness (`ends`: K01's `north` is the
    high-v wall, `south` the low-v one), either `stepped` (crow steps, `steps` a slope, each
    clearing the covering behind it by K05's upstand and carrying its own coping) or `coped`
    (one coping following the slopes at that clearance); both stand `top_above_ridge_m` over
    the ridge at their head."""
    if not g:
        raise ParamError("a gable K01 roof names its gable_roof: ridge_back_m and the two ends")
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    pp, cp = k5["parts"]["parapet"], k5["parts"]["coping"]
    tf = math.tan(math.radians(pitch))
    r = float(g["ridge_back_m"])
    if not 1.0 <= r <= depth / 2:
        raise ParamError(f"gable_roof.ridge_back_m {r}: the ridge stands 1 m to half the depth behind the front")
    rise = r * tf
    back_deg = math.degrees(math.atan(rise / (depth - r)))
    if back_deg < 15.0:
        raise ParamError(f"gable_roof: the rear slope falls at {back_deg:.1f} deg; under 15 a slate roof sheds no water")
    ends = g.get("ends") or {}
    if set(ends) != {"north", "south"}:
        raise ParamError("gable_roof.ends names the parapet on both side walls, north and south")
    out = {}
    for side, e in sorted(ends.items()):
        style = e.get("style")
        if style not in GABLE_PARAPETS:
            raise ParamError(f"gable_roof.ends.{side}.style is one of {GABLE_PARAPETS}")
        row = {"style": style}
        if style == "stepped":
            n = int(e["steps"])
            if not 2 <= n <= 8:
                raise ParamError(f"gable_roof.ends.{side}.steps: 2-8 crow steps a slope")
            row["steps"] = n
        out[side] = row
    top = float(g.get("top_above_ridge_m", pp["top_above_ridge_m"]))
    if not pp["upstand_min_m"] <= top <= 1.5:
        raise ParamError(f"gable_roof.top_above_ridge_m: {pp['upstand_min_m']}-1.5 m")
    return {"ridge_back_m": r, "ridge_m": round(eave + rise, 4), "back_pitch_deg": round(back_deg, 4),
            "ends": out, "parapet_m": side_wall, "upstand_m": float(pp["upstand_min_m"]),
            "top_above_ridge_m": top, "coping_m": float(cp["thickness_m"]), "drip_m": float(cp["drip_m"])}


#: T-2370: the K05 mansard variants a K01 roof may be built from (k05_roofs.json)
MANSARD_ROOFS = ("k05.roof.mansard_convex", "k05.roof.mansard_concave")


def _mansard_roof(m: dict, depth: float, width: float, eave: float, pitch: float, overhang: float) -> dict:
    """The numbers a K01 mansard is built to (T-2370), from K05's mansard (T-2304): the
    record names the variant, which gives the lower face's profile, curve and chord pitch,
    and the lower face's rise to the curb, the attic storey's height; the upper hip is the
    record's roof_pitch_deg. The fascia's top stands on the walls' top (the eave datum), so
    the soffit is the cornice's, and the curb and ridge follow."""
    if not m:
        raise ParamError("a mansard K01 roof names its K05 variant and lower_rise_m (`mansard`)")
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    vid = m.get("variant")
    if vid not in MANSARD_ROOFS:
        raise ParamError(f"mansard.variant {vid!r}: one of {', '.join(MANSARD_ROOFS)}")
    v = next(x for x in k5["variants"] if x["id"] == vid)
    lower = float(m.get("lower_pitch_deg", v["lower_pitch_deg"]))
    _within(lower, k5["ranges"]["mansard_lower_deg"], "mansard.lower_pitch_deg")
    _within(pitch, k5["ranges"]["mansard_upper_deg"], "roof_pitch_deg (a mansard's upper hip)")
    rise = float(m["lower_rise_m"])
    if not 2.0 <= rise <= 4.5:
        raise ParamError(f"mansard.lower_rise_m {rise}: an attic storey's face rises 2.0-4.5 m")
    if not 0.3 <= overhang <= 1.0:
        raise ParamError(f"eave_overhang_m {overhang}: a mansard's cornice projects 0.3-1.0 m")
    f = k5["parts"]["eave"]["fascia_depth_m"]
    run = rise / math.tan(math.radians(lower))
    half = min(depth, width) / 2 + overhang
    if run >= half - 0.5:
        raise ParamError(f"mansard.lower_rise_m {rise}: the curb leaves no upper roof")
    ridge = eave + rise + (half - run) * math.tan(math.radians(pitch))
    # T-2452: a house's own lower faces may bow less than the variant's, down to none — the
    # straight steep faces 1637's engraving draws — on the variant's ring stack, in one ring
    # when the face is a plane (five coplanar rings would only part one face into five)
    bulge = float(m.get("bulge", v["bulge"]))
    if not 0.0 <= bulge <= 0.2:
        raise ParamError(f"mansard.bulge {bulge}: 0 (a straight face) to 0.2 of the chord")
    return {"variant": vid, "profile": v["profile"], "lower_pitch_deg": lower, "bulge": bulge,
            "segments": int(v["segments"]) if bulge > 0 else 1, "lower_rise_m": rise, "fascia_m": f,
            "curb_m": round(eave + rise, 4), "ridge_m": round(ridge, 4)}


def _mansard_crown(c: dict, m: dict, bays: tuple, depth: float, width: float, eave: float, pitch: float,
                   overhang: float) -> dict:
    """T-2404: a taller mansard over a street-front pavilion — the 1874 engraving's crown
    on 1620 — as the main mansard's own profile with a higher curb and a fuller bow. It
    stands on the K08 projection it names, its front on that pavilion's face and its sides
    on the pavilion's junctions, and runs `depth_m` back into the main roof, which the
    union swallows it into. Its cornice projects `overhang_m` past the pavilion's face."""
    bay = next((b for b in bays if b["id"] == c.get("over_bay")), None)
    if bay is None or bay["variant"]["kind"] != "projection" or bay["wall"] != "k01.wall.street_front":
        raise ParamError(f"mansard.crown.over_bay {c.get('over_bay')!r}: a K08 projection on the street front")
    pts = bay["variant"]["plan"]["points"]
    proud = max(float(q[1]) for q in pts)
    a, b = bay["span_m"]
    cd = float(c["depth_m"])
    if not 1.5 <= cd <= depth / 2:
        raise ParamError(f"mansard.crown.depth_m {cd}: 1.5 m to half the house's depth")
    up = float(c.get("rise_above_curb_m", 0.0))
    if c.get("form", "mansard") == "mansard" and not 0.3 <= up <= 2.0:
        raise ParamError(f"mansard.crown.rise_above_curb_m {up}: a crown stands 0.3-2.0 m over the main curb")
    co = float(c.get("overhang_m", overhang))
    if not overhang < co <= overhang + 0.5:
        raise ParamError(f"mansard.crown.overhang_m {co}: past the main cornice's {overhang} m, by at most 0.5 m "
                         f"(an equal one would lay the two fascias in one plane on the corner)")
    if c.get("form", "mansard") == "hip":
        return _hip_crown(c, m, bay, proud, a, b, cd, co, depth, eave, overhang)
    if c.get("form", "mansard") != "mansard":
        raise ParamError(f"mansard.crown.form {c.get('form')!r}: mansard or hip")
    bulge = float(c.get("bulge", m["bulge"]))
    if not 0.0 <= bulge <= 0.2:
        raise ParamError(f"mansard.crown.bulge {bulge}: 0-0.2 of the chord")
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    lower = float(c.get("lower_pitch_deg", m["lower_pitch_deg"]))
    _within(lower, k5["ranges"]["mansard_lower_deg"], "mansard.crown.lower_pitch_deg")
    rise = m["lower_rise_m"] + up
    run = rise / math.tan(math.radians(lower))
    half = min(cd, b - a) / 2 + co
    if run >= half - 0.3:
        raise ParamError(f"mansard.crown: its curb at {rise} m leaves no upper roof over {b - a} m")
    out = {"over_bay": bay["id"], "x0": round(depth + proud - cd, 4), "x1": round(depth + proud, 4),
           "z0": round(-b, 4), "z1": round(-a, 4), "lower_pitch_deg": lower, "lower_rise_m": round(rise, 4),
           "bulge": bulge, "overhang_m": co, "curb_m": round(eave + rise, 4),
           "ridge_m": round(eave + rise + (half - run) * math.tan(math.radians(pitch)), 4)}
    d = c.get("dormer")
    if d:
        # one round-headed dormer on the crown's street face, centred on it: a K06 opening
        # in a stone face whose head follows the sash's own arch
        out["dormer"] = _round_dormer(d, "mansard.crown.dormer", run + co)
        if out["dormer"]["width_m"] > (b - a) - 0.6:
            raise ParamError(f"mansard.crown.dormer: {out['dormer']['width_m']:.2f} m wide on a {b - a} m crown")
    return out


def _hip_crown(c: dict, m: dict, bay: dict, proud: float, a: float, b: float, cd: float, co: float,
               depth: float, eave: float, overhang: float) -> dict:
    """T-2465: a crown that is a steep hip and not a mansard — 1637's wing in its engraving,
    under its own hipped roof as high as the main one, a stack at its ridge. Its plan is the
    mansard crown's (the pavilion's face and junctions, `depth_m` back into the main roof,
    its cornice `overhang_m` past the face, its fascia's top on the main eave datum), hipped
    at `pitch_deg` on its sides and back and at `end_pitch_deg` on its street end, so the
    ridge runs back from the end's apex at the height the sides give it. Both pitches are in
    K05's steep range and over 45 degrees, so K04 slates them as it slates a lower face.
    The ridge stands at least 0.3 m over the main curb, and the end stays in front of the main
    lower faces up to that curb: an end that met them lower would be cut off by the main roof,
    and the picture draws it whole."""
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    if c.get("dormer"):
        raise ParamError("mansard.crown.dormer: a hipped crown carries none")
    lo, hi = k5["ranges"]["pitch_deg"]["steep"]
    side, end = float(c["pitch_deg"]), float(c["end_pitch_deg"])
    for what, x in (("pitch_deg", side), ("end_pitch_deg", end)):
        if not (lo < x <= hi):
            raise ParamError(f"mansard.crown.{what} {x}: a hipped crown is slated, over {lo} and up to {hi} degrees")
    w = b - a
    if cd <= w:
        raise ParamError(f"mansard.crown.depth_m {cd}: a hipped crown runs its ridge back, deeper than its {w} m")
    # the pavilion is carried up to the crown's soffit, its own eaves and deck inside the crown
    soffit = eave - float(k5["parts"]["eave"]["fascia_depth_m"])
    top = sum(float(st["height_m"]) for st in bay["variant"]["storeys"])
    if not soffit <= top <= soffit + 0.1:
        raise ParamError(f"mansard.crown: {bay['id']} stops at {top:.3f} m; under a hipped crown it rises "
                         f"to the crown's soffit at {soffit:.3f} m, and at most 0.1 m into it")
    half = w / 2 + co
    rise = half * math.tan(math.radians(side))
    x1 = depth + proud
    apex = x1 + co - rise / math.tan(math.radians(end))
    if rise < m["lower_rise_m"] + 0.3:
        raise ParamError(f"mansard.crown: its ridge {rise:.2f} m over the eave is not 0.3 m over the main "
                         f"curb's {m['lower_rise_m']} m")
    # where the end reaches the main curb's height it stands in front of that curb
    curb = depth + overhang - m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
    at_curb = x1 + co - m["lower_rise_m"] / math.tan(math.radians(end))
    if at_curb < curb + 0.2:
        raise ParamError(f"mansard.crown: its end meets the main curb's height at x {at_curb:.2f}, not 0.2 m "
                         f"in front of the curb at {curb:.2f}; steepen end_pitch_deg")
    back = x1 - cd - co + rise / math.tan(math.radians(side))
    if back > apex - 0.5:
        raise ParamError(f"mansard.crown.depth_m {cd}: its ridge would run {apex - back:.2f} m, under 0.5")
    return {"over_bay": bay["id"], "form": "hip", "x0": round(x1 - cd, 4), "x1": round(x1, 4),
            "z0": round(-b, 4), "z1": round(-a, 4), "pitch_deg": side, "end_pitch_deg": end,
            "overhang_m": co, "ridge_m": round(eave + rise, 4),
            "ridge_x_m": (round(back, 4), round(apex, 4))}


def mansard_cover(m: dict, depth: float, width: float, eave: float, pitch: float, overhang: float):
    """T-2466: a K01 mansard's covering over a plan point (u, v), as K15 reads a roof: the
    lower faces from the fascia's top up K05's profile to the curb, the upper hip on at
    `pitch`, and a hipped crown (T-2465) over its pavilion, whichever stands higher."""
    rise, lower = m["lower_rise_m"], m["lower_pitch_deg"]
    run, tu = rise / math.tan(math.radians(lower)), math.tan(math.radians(pitch))
    cr = m.get("crown") or {}
    if cr and cr.get("form") != "hip":
        raise ParamError("chimneys.k15 reads a mansard and a hipped crown; a mansard crown's covering is not read")

    def cover(u: float, v: float) -> float:
        s = min(u + overhang, depth + overhang - u, v + overhang, width + overhang - v)
        y = eave + (mansard_face_height(max(s, 0.0), rise, lower, m["bulge"], m["profile"]) if s <= run
                    else rise + (s - run) * tu)
        if cr:
            co, z = cr["overhang_m"], -v
            X0, X1, Z0, Z1 = cr["x0"] - co, cr["x1"] + co, cr["z0"] - co, cr["z1"] + co
            if X0 <= u <= X1 and Z0 <= z <= Z1:
                ts, te = math.tan(math.radians(cr["pitch_deg"])), math.tan(math.radians(cr["end_pitch_deg"]))
                y = max(y, eave + min((u - X0) * ts, (X1 - u) * te, (z - Z0) * ts, (Z1 - z) * ts))
        return y
    return cover


def _k15_heads(k: dict, stacks: list, chimneys: list, cover) -> None:
    """T-2466: each plain stack's K15 spec (k15_chimneys.stack_solids, built with its flashing
    off), from the kit variant `from` less the parts `omit` names: its corbel courses and cap
    as the variant's, `flues` flues across it, and, unless the stack says `panelled: false`,
    `panels` sunk panels on its street and rear faces, each run from `above_roof_m` over the
    highest covering under the stack to `under_head_m` below its corbelled head. The stack
    keeps its record's plan and top; it is turned so its panelled faces face the street."""
    from . import k15_chimneys as k15
    kit = k15.load()
    var = next((x for x in kit["variants"] if x["id"] == k.get("from")), None)
    if var is None or len(var["stacks"]) != 1:
        raise ParamError(f"chimneys.k15.from {k.get('from')!r} is not a one-stack K15 variant")
    omit = set(k.get("omit", []))
    if omit - {"bands", "dentils", "panels"}:
        raise ParamError(f"chimneys.k15.omit {sorted(omit)}: bands, dentils or panels")
    base, so, fl = var["stacks"][0], kit["soot"], kit["parts"]["flashing"]
    nfl, fo = int(k.get("flues", len(base["flues"]))), kit["parts"]["flue"]["opening_m"]
    pn = k.get("panels")
    for st_, c in zip(stacks, chimneys):
        sx, sz = c["plan_m"]
        u, v, top = c["u_m"], c["v_m"], c["top_m"]
        if sz / max(nfl, 1) < fo + 0.1:
            raise ParamError(f"chimney at ({u}, {v}): {nfl} flues of {fo} m do not fit its {sz} m face")
        spec = {key: copy.deepcopy(x) for key, x in base.items()
                if key not in ("x", "z", "width_m", "depth_m", "top_m", "flues", "panels") and key not in omit}
        spec.update(width_m=sz, depth_m=sx, across="z", top_m=top,
                    flues=[{"at": round((i + 0.5) * sz / nfl - sz / 2, 4)} for i in range(nfl)])
        hi = max(cover(u + a * sx / 2, v + b * sz / 2) for a in (-1, 0, 1) for b in (-1, 0, 1))
        y_head = top - spec["cap"]["thickness_m"] - sum(h for h, _ in spec["corbels"])
        if max(y_head - so["band_m"], hi + fl["upstand_m"] + 0.2) > y_head - 0.05:
            raise ParamError(f"chimney at ({u}, {v}): its shaft stands {y_head - hi:.2f} m over its roof under "
                             f"K15's head, too little for the head's courses and its sooted band")
        if pn and "panels" not in omit and st_.get("panelled", True):
            ph = round(y_head - pn["under_head_m"] - hi - pn["above_roof_m"], 4)
            if ph < pn["min_height_m"]:
                raise ParamError(f"chimney at ({u}, {v}): room for a {ph} m panel, under the {pn['min_height_m']} m "
                                 f"chimneys.k15.panels asks; mark the stack panelled: false")
            if not 0.1 <= int(pn["count"]) * pn["width_m"] <= sz - 0.2:
                raise ParamError(f"chimneys.k15.panels.width_m {pn['width_m']}: 0.1 m inside each edge of {sz} m")
            spec["panels"] = [int(pn["count"]), pn["width_m"], ph, pn["depth_m"], pn["above_roof_m"]]
        c["k15_head"] = spec
        c["cover_high_m"] = round(hi, 4)


def mansard_face_height(setback: float, rise: float, lower_pitch_deg: float, bulge: float, profile: str) -> float:
    """How high a mansard's lower face stands over its eave `setback` in from the fascia's
    face: K05's quadratic (k05_roofs.mansard_element), the chord from the fascia's top to
    the curb bowed `bulge` of its length along the chord's normal."""
    run = rise / math.tan(math.radians(lower_pitch_deg))
    sgn = 1.0 if profile == "convex" else -1.0
    P1 = (run / 2 - sgn * bulge * rise, rise / 2 + sgn * bulge * run)
    bez = lambda u, i: 2 * (1 - u) * u * P1[i] + u * u * (run, rise)[i]
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if bez(mid, 0) < setback else (lo, mid)
    return bez(lo, 1)


# T-2411: the main mansard's four lower faces. `along` is the face's own coordinate for a
# dormer's centre — u (rear wall 0, street front D) on the side faces, v (south wall 0) on
# the street and rear — and `out` the face's outward direction in the K01 frame (x = u, z = -v)
MANSARD_FACES = {"street": "v", "rear": "v", "north": "u", "south": "u"}


#: T-2452: a lower-face dormer's head — the sash's own arch carried out by the surround
#: (T-2404, T-2411), or a pitched gable over a square-headed sash — and the K06 head each takes
DORMER_HEADS = {"round": "round", "gable": "flat"}


def _round_dormer(d: dict, what: str, room: float) -> dict:
    """A lower-face dormer's numbers (T-2404's crown dormer, T-2411's lower-face ones,
    T-2452's gabled ones): a K06 sash in a stone face `surround_m` round it, its face
    `face_setback_m` in from the fascia's face. `head` is `round` (the default: the sash's
    own arch, the surround carried round it) or `gable` (a square-headed sash under a
    pediment pitched `gable_pitch_deg` from the surround's head, the face's two slopes
    slated as its cheeks are). `room` is how far the lower face runs in to its curb.
    `head_m` is how far the face's top stands over its sill."""
    kit = {v["id"]: v for v in json.loads(WINDOW_KIT.read_text())["variants"]}
    sh = d["sash"]
    head = d.get("head", "round")
    if head not in DORMER_HEADS:
        raise ParamError(f"{what}.head {head!r}: one of {', '.join(DORMER_HEADS)}")
    if kit.get(sh.get("variant"), {}).get("head") != DORMER_HEADS[head]:
        raise ParamError(f"{what}.sash.variant: a {DORMER_HEADS[head]}-headed K06 variant under a {head} head")
    sw, sht, sill = float(sh["width_m"]), float(sh["height_m"]), float(sh["sill_m"])
    ring, sb = float(d["surround_m"]), float(d["face_setback_m"])
    if not 0.1 <= ring <= 0.4 or not 0.0 < sb < room:
        raise ParamError(f"{what}: a 0.1-0.4 m surround, its face on the lower face")
    if not 0.5 <= sw <= 1.2 or not 1.0 <= sht <= 2.4 or not 0.1 <= sill <= 0.6:
        raise ParamError(f"{what}.sash: 0.5-1.2 m wide, 1.0-2.4 m high, on a 0.1-0.6 m sill")
    out = {"variant": sh["variant"], "head": head, "sash_width_m": sw, "sash_height_m": sht, "sill_m": sill,
           "surround_m": ring, "face_setback_m": sb, "width_m": round(sw + 2 * ring, 4),
           "head_m": round(sht + ring, 4)}
    if head == "gable":
        gp = float(d["gable_pitch_deg"])
        if not 30.0 <= gp <= 60.0:
            raise ParamError(f"{what}.gable_pitch_deg {gp}: a dormer's pediment is pitched 30-60 deg")
        out["gable_pitch_deg"] = gp
        out["head_m"] = round(sht + ring + (sw / 2 + ring) * math.tan(math.radians(gp)), 4)
    return out


def _wall_gable(d: dict, wg: dict, dormer: dict, width: float) -> dict:
    """T-2428: the street dormer built as a WALL GABLE — 1619 Prairie's roof storey, which its
    drawing raises from the wall over the bow rather than setting on the hip: the face on the
    street wall's plane (no setback), centred at `v_m` along the front, a row of K06 lights
    `sash.at_m` either side of its centre each under a block of radiating voussoirs, a
    recessed panel in the pediment, a finial at the apex and a pinnacle shaft either side
    at the face's foot. The pediment's cornices are K10's dormer face, as on any dormer."""
    kit = {v["id"]: v for v in json.loads(WINDOW_KIT.read_text())["variants"]}
    sh = d["sash"]
    vid = sh.get("variant")
    if kit.get(vid, {}).get("head") not in ("flat", "segmental"):
        raise ParamError("dormer.sash.variant: a wall gable's lights are a flat- or segment-headed K06 variant")
    if float(d["face_setback_m"]) != 0.0:
        raise ParamError("dormer.wall_gable: a wall gable's face is the street wall's plane (face_setback_m 0)")
    wd, sw = dormer["width_m"], dormer["sash"]["width_m"]
    vm = float(d.get("v_m", width / 2))
    if not wd / 2 + 0.3 <= vm <= width - wd / 2 - 0.3:
        raise ParamError("dormer.v_m: the wall gable stands 0.3 m inside both ends of the front")
    at = sorted(float(x) for x in sh.get("at_m", [0.0]))
    vs = wg["voussoirs"]
    ring, proud = float(vs["ring_m"]), float(vs["proud_m"])
    if not 0.1 <= ring <= 0.4 or not 0.0 < proud <= 0.08:
        raise ParamError("dormer.wall_gable.voussoirs: a 0.1-0.4 m ring, 0-0.08 m proud")
    side = min(0.6 * ring, *((b - a - sw) / 2 - 0.01 for a, b in zip(at, at[1:])))
    if side < 0.05:
        raise ParamError("dormer.sash.at_m: the wall gable's lights stand too close for their voussoirs")
    if at[-1] + sw / 2 + side > wd / 2 - 0.05 or at[0] - sw / 2 - side < -wd / 2 + 0.05:
        raise ParamError("dormer.sash.at_m: a light's voussoirs run off the wall gable's face")
    pn, fn, pa = wg["pinnacles"], wg["finial"], wg["panel"]
    pin = {k: float(pn[k]) for k in ("at_m", "shaft_m", "foot_m", "top_m", "cap_m", "spire_m")}
    if pin["at_m"] - pin["shaft_m"] / 2 < wd / 2 + 0.13 + 0.02:
        raise ParamError("dormer.wall_gable.pinnacles: a shaft stands in the face's cornice return")
    if not pin["foot_m"] < 0.0 < dormer["face_height_m"] < pin["top_m"]:
        raise ParamError("dormer.wall_gable.pinnacles: a shaft rises from under the wall head past the face's eave")
    if vm - pin["at_m"] - pin["shaft_m"] / 2 < 0.0 or vm + pin["at_m"] + pin["shaft_m"] / 2 > width:
        raise ParamError("dormer.wall_gable.pinnacles: both shafts stand on the front")
    panel = {"inset_m": float(pa["inset_m"]), "depth_m": float(pa["depth_m"])}
    if not 0.1 <= panel["inset_m"] <= 0.5 or not 0.02 <= panel["depth_m"] <= dormer["face_thickness_m"] / 2:
        raise ParamError("dormer.wall_gable.panel: a 0.1-0.5 m margin, recessed no deeper than half the face")
    finial = {"height_m": float(fn["height_m"]), "radius_m": float(fn["radius_m"])}
    if not 0.2 <= finial["height_m"] <= 1.0 or not 0.04 <= finial["radius_m"] <= 0.2:
        raise ParamError("dormer.wall_gable.finial: 0.2-1.0 m high, 0.04-0.2 m in radius")
    return {"v_m": vm, "sash": dict(dormer["sash"], variant=vid, at_m=at),
            "wall_gable": {"voussoirs": {"ring_m": ring, "proud_m": proud, "side_m": round(side, 4)},
                           "pinnacles": pin, "finial": finial, "panel": panel}}


def _shaped_gable(sg: dict, roof_form: str, dormer: dict, width: float, eave: float, pitch: float,
                  overhang: float) -> dict:
    """T-2543: the street front's shaped gable — 1812 Prairie's, which its photograph shows
    standing over the whole front: `profile_m`, the outline's half-width over grade from its
    foot to its apex ([half-width, height] pairs, rising, the last on the centre line); the
    slab's `foot_m` under the wall head, `thickness_m`, and `proud_m` in front of the street
    eave's fascia; a row of K06 `lights` (`variant`, `sill_m` over grade, `width_m`,
    `height_m`, `at_m` from the centre); the `coping` band on the face; a pinnacle
    `kneelers` each side on the ledge where the outline leaves the eave; a `finial`.
    T-2730: 1625 Prairie's plain coped WALL GABLE is the same slab with a straight outline:
    its `kneelers` and `finial` may be left out (the ledge alone is the kneeler stone), its
    lights may be segment-headed and stand below the ledge, on the slab under the eave, an
    `oculus` (`centre_m` over grade, `width_m`, `height_m`, a stone `ring_m` `proud_m` and
    its glazing `bars_m`) may light its apex, and `fabric: "front"` dresses the slab in the
    front's stone where 1812's wears the side walls' brick."""
    if not sg:
        return {}
    if roof_form != "hip":
        raise ParamError("shaped_gable: a shaped gable stands in front of a hip's street slope (T-2543)")
    if dormer:
        raise ParamError("shaped_gable: a front carried up as a shaped gable carries no street dormer")
    pr = [(float(w), float(y)) for w, y in sg["profile_m"]]
    if len(pr) < 3 or pr[-1][0] != 0.0:
        raise ParamError("shaped_gable.profile_m: at least three points, the last on the centre line (0)")
    if any(y1 <= y0 for (_, y0), (_, y1) in zip(pr, pr[1:])):
        raise ParamError("shaped_gable.profile_m: the outline rises point by point")
    if pr[0][0] > width / 2 or min(w for w, _ in pr) < 0.0:
        raise ParamError("shaped_gable.profile_m: the outline stands inside the front")
    ye = eave - overhang * math.tan(math.radians(pitch))
    ridge = eave + width / 2 * math.tan(math.radians(pitch))
    if pr[-1][1] < ridge + 0.3:
        raise ParamError(f"shaped_gable: its apex ({pr[-1][1]} m) stands at least 0.3 m over the hip's ridge ({ridge:.2f} m)")
    foot, t, proud = float(sg["foot_m"]), float(sg["thickness_m"]), float(sg["proud_m"])
    if not eave - 2.0 <= foot < ye - 0.3:
        raise ParamError("shaped_gable.foot_m: the slab starts under the street fascia, within 2.0 m of the wall head")
    if not 0.02 <= proud <= 0.2 or not overhang + proud + 0.1 <= t <= 1.0:
        raise ParamError("shaped_gable: its face 0.02-0.2 m proud of the fascia, its back over the wall")
    li = sg["lights"]
    kit = {v["id"]: v for v in json.loads(WINDOW_KIT.read_text())["variants"]}
    if kit.get(li["variant"], {}).get("head") not in ("flat", "segmental"):
        raise ParamError("shaped_gable.lights.variant: a flat- or segment-headed K06 variant")
    lw, lh, sill = float(li["width_m"]), float(li["height_m"]), float(li["sill_m"])
    at = sorted(float(x) for x in li["at_m"])
    ledge = ye + 0.12
    if sg.get("kneelers") and sill < ledge + 0.3:
        raise ParamError("shaped_gable.lights: a light's sill stands 0.3 m over the kneelers' ledge")
    if sill < foot + 0.3:   # T-2730: without kneelers a light may stand on the slab under the eave
        raise ParamError("shaped_gable.lights: a light's sill stands 0.3 m over the slab's foot")
    from archetypes import k01_shaped_gable as ksg
    q = {"profile_m": pr}
    for x in at:
        need = abs(x) + lw / 2 + 0.15
        if need > ksg.half_width(q, sill + lh + 0.15) or need > ksg.half_width(q, sill):
            raise ParamError("shaped_gable.lights: every light stands 0.15 m inside the outline")
    cp, kn, fn = sg["coping"], sg.get("kneelers"), sg.get("finial")
    coping = {"width_m": float(cp["width_m"]), "proud_m": float(cp["proud_m"])}
    if not 0.1 <= coping["width_m"] <= 0.5 or not 0.0 < coping["proud_m"] <= 0.08:
        raise ParamError("shaped_gable.coping: a 0.1-0.5 m band, 0-0.08 m proud")
    kne = {}
    if kn:
        kne = {k_: float(kn[k_]) for k_ in ("at_m", "shaft_m", "top_m", "cap_m", "spire_m")}
        hb, hl = width / 2 + overhang + 0.02, ksg.half_width(q, ledge)
        if not hl + kne["shaft_m"] / 2 <= kne["at_m"] <= hb - kne["shaft_m"] / 2 or kne["top_m"] <= ledge + 0.2:
            raise ParamError("shaped_gable.kneelers: each pinnacle stands on its ledge and rises from it")
    fin = {}
    if fn:
        fin = {"height_m": float(fn["height_m"]), "radius_m": float(fn["radius_m"])}
        if not 0.2 <= fin["height_m"] <= 1.2 or not 0.04 <= fin["radius_m"] <= 0.3:
            raise ParamError("shaped_gable.finial: 0.2-1.2 m high, 0.04-0.3 m in radius")
    fabric = sg.get("fabric", "brick")
    if fabric not in ("brick", "front"):
        raise ParamError(f"shaped_gable.fabric {fabric!r}: brick (the side walls') or front (the front's stone)")
    oc = {}
    if sg.get("oculus"):   # T-2730: an oval light near the apex, in a stone ring
        o_ = sg["oculus"]
        oc = {k_: float(o_[k_]) for k_ in ("centre_m", "width_m", "height_m", "ring_m", "proud_m", "bars_m")}
        if not 0.3 <= oc["width_m"] <= 1.5 or not 0.3 <= oc["height_m"] <= 1.5:
            raise ParamError("shaped_gable.oculus: 0.3-1.5 m across and high")
        if not 0.05 <= oc["ring_m"] <= 0.3 or not 0.0 < oc["proud_m"] <= 0.08 or not 0.0 <= oc["bars_m"] <= 0.08:
            raise ParamError("shaped_gable.oculus: a 0.05-0.3 m ring 0-0.08 m proud, bars 0-0.08 m")
        top, low = oc["centre_m"] + oc["height_m"] / 2 + oc["ring_m"], oc["centre_m"] - oc["height_m"] / 2 - oc["ring_m"]
        if oc["width_m"] / 2 + oc["ring_m"] + 0.15 > ksg.half_width(q, top) or low < sill + lh + 0.3:
            raise ParamError("shaped_gable.oculus: its ring stands 0.15 m inside the outline and 0.3 m over the lights")
    return {"profile_m": pr, "foot_m": foot, "thickness_m": t, "proud_m": proud,
            "lights": {"variant": li["variant"], "sill_m": sill, "width_m": lw, "height_m": lh, "at_m": at},
            "coping": coping, "kneelers": kne, "finial": fin, "fabric": fabric, "oculus": oc}


def _mansard_dormers(entries, m: dict, depth: float, width: float, eave: float, overhang: float,
                     chimneys) -> list:
    """T-2411: round-headed dormers in the main mansard's lower faces — the 1874 engraving's
    two on 1620's north face — each the crown dormer's construction (`_round_dormer`) on a
    face the record names, at a centre along it. Each stands clear of the face's hips, of
    the crown and its cornice, of the stacks and of its neighbours, and its head stays under
    the curb so the body it runs back into the roof is swallowed by the upper hip."""
    run = m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
    lengths = {"u": depth, "v": width}
    out, rects = [], []
    for i, e in enumerate(entries):
        what = f"mansard.dormers[{i}]"
        face = e.get("face")
        if face not in MANSARD_FACES:
            raise ParamError(f"{what}.face {face!r}: one of {', '.join(MANSARD_FACES)}")
        d = _round_dormer(e, what, run)
        ax = MANSARD_FACES[face]
        c, r = float(e["along_m"]), d["width_m"] / 2
        lo, hi = -overhang + run + 0.3 + r, lengths[ax] + overhang - run - 0.3 - r
        if not lo <= c <= hi:
            raise ParamError(f"{what}.along_m {c}: its face stands clear of the hips only for {lo:.2f}-{hi:.2f} m")
        foot = mansard_face_height(d["face_setback_m"], m["lower_rise_m"], m["lower_pitch_deg"], m["bulge"],
                                   m["profile"])
        top = foot + d["sill_m"] + d["head_m"]
        if top > m["lower_rise_m"] - 0.1:
            raise ParamError(f"{what}: its head at {top:.2f} m over the eave meets the curb at {m['lower_rise_m']} m")
        # its plan, face to back, in (u, v): the body runs `run + 0.3` in from the fascia
        fa, ba = {"street": (depth + overhang, depth + overhang - run - 0.3),
                  "rear": (-overhang, -overhang + run + 0.3),
                  "north": (width + overhang, width + overhang - run - 0.3),
                  "south": (-overhang, -overhang + run + 0.3)}[face]
        n0, n1 = sorted((fa, ba))
        rect = ((c - r, c + r, n0, n1) if ax == "u" else (n0, n1, c - r, c + r))   # (u0, u1, v0, v1)
        cr = m.get("crown")
        if cr:   # the crown's plan with its cornice, in (u, v)
            co = cr["overhang_m"]
            keep = (cr["x0"] - co - 0.1, cr["x1"] + co + 0.1, -cr["z1"] - co - 0.1, -cr["z0"] + co + 0.1)
            if rect[0] < keep[1] and keep[0] < rect[1] and rect[2] < keep[3] and keep[2] < rect[3]:
                raise ParamError(f"{what}: it stands in the crown or under its cornice")
        for ch in chimneys:
            sx, sz = ch["plan_m"]
            if rect[0] < ch["u_m"] + sx / 2 and ch["u_m"] - sx / 2 < rect[1] and \
                    rect[2] < ch["v_m"] + sz / 2 and ch["v_m"] - sz / 2 < rect[3]:
                raise ParamError(f"{what}: a chimney stands in its body")
        for j, q in enumerate(rects):
            if rect[0] < q[1] + 0.3 and q[0] - 0.3 < rect[1] and rect[2] < q[3] + 0.3 and q[2] - 0.3 < rect[3]:
                raise ParamError(f"{what}: within 0.3 m of mansard.dormers[{j}]")
        rects.append(rect)
        out.append(dict(d, face=face, along_m=c, foot_m=round(eave + foot, 4)))
    return out


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
    # T-2581: a front read off its photographs may turn the corner as a straight strip of
    # its own stone, every course returned the same length onto the south wall, where a
    # quoined corner bonds long and short in turn into the brick
    south_return = front.get("south_return_m")
    if south_return is not None:
        if "south" not in corners:
            raise ParamError("stone_front.south_return_m returns the south corner: corner_bond must name it")
        south_return = float(south_return)
        if not float(f["corner_bond"]["return_m"][1]) < south_return <= 4.0:
            raise ParamError(f"stone_front.south_return_m = {south_return} must be longer than {fab}'s "
                             f"longest quoin ({f['corner_bond']['return_m'][1]} m) and at most 4 m")
    if t["coping"] is None:
        raise ParamError("dressed_trim declares no coping")
    coping_h = float(front.get("coping_height_m", 0.0))
    _within(coping_h, t["course_height_m"], "stone_front.coping_height_m (dressed_trim course_height_m)")
    # T-2566: a front read off its photograph may lay its walling high and low in turn
    # (the profile's course_rule) up to a line, and evenly above it with a shallower face;
    # every course and rock face it lays stays inside the profile's own ranges
    coursing = front.get("coursing")
    if coursing is not None:
        lo_c, hi_c = (float(x) for x in f["course_height_m"])
        req = {"rhythm", "low_ratio", "even_above_m", "even_rock_share"}
        if not req <= set(coursing) <= req | {"even_below_m", "deep_max_m"} or coursing["rhythm"] != "alternating":
            raise ParamError("stone_front.coursing takes rhythm 'alternating', low_ratio, even_above_m "
                             "and even_rock_share, and may take even_below_m and deep_max_m")
        if "deep_max_m" in coursing and not lo_c < float(coursing["deep_max_m"]) <= hi_c:
            raise ParamError(f"stone_front.coursing.deep_max_m must stand inside {fab}'s "
                             f"course_height_m ({lo_c}, {hi_c}]")
        # T-2773: under even_below_m (a front's principal sill) the walling is laid even too
        if "even_below_m" in coursing and not (
                0.0 < float(coursing["even_below_m"]) < float(coursing["even_above_m"])):
            raise ParamError("stone_front.coursing.even_below_m stands above grade and under even_above_m")
        if not (lo_c / hi_c <= float(coursing["low_ratio"]) < 1.0):
            raise ParamError(f"stone_front.coursing.low_ratio must let a low course stand inside "
                             f"{fab}'s course_height_m [{lo_c}, {hi_c}]")
        if not (0.0 < float(coursing["even_rock_share"]) <= 1.0 and float(coursing["even_above_m"]) > 0.0):
            raise ParamError("stone_front.coursing: even_rock_share in (0, 1], even_above_m above grade")
        if f["course_rule"].find("alternating") < 0:
            raise ParamError(f"{fab}'s profile does not allow alternating courses")

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
        **({"south_return_m": south_return} if south_return is not None else {}),
        "base_courses": base, "channel_m": f["rusticated_base"]["channel_width_m"],
        "channel_depth_m": f["rusticated_base"]["channel_depth_m"],
        **({"coursing": dict(coursing)} if coursing else {}),
        "coping_height_m": coping_h, "coping_fall": t["coping"]["fall"],
        "coping_overhang_m": t["coping"]["overhang_m"], "drip_groove_m": t["coping"]["drip_groove_m"],
        "fabric_roughness": lib[fab]["mean_roughness"], "trim_roughness": lib[trim]["mean_roughness"],
    }


BAY_FABRICS = ("stone", "brick", "front_stone", "frame")   # T-2350: front_stone, the K02 front's own fabric; T-2356: frame, a painted timber bay
BAY_PIER_M = 0.30          # masonry left between a bay's junction and its wall's corner
EAVE_FASCIA_M = 0.20       # the K05 eave's fascia on a K01 house: its soffit stands this far under the eaves line
BRACKETED_CORNICE = "k10.cornice.bracketed_timber"


def _bay_span(plan: dict) -> tuple:
    """Where a bay's plan meets its host wall: (left, right) metres about its centre."""
    if plan["kind"] == "polyline":
        return float(plan["points"][0][0]), float(plan["points"][-1][0])
    if plan["kind"] == "bow":
        return -float(plan["chord_m"]) / 2, float(plan["chord_m"]) / 2
    raise ParamError(f"a K01 bay's plan is a polyline or a bow, not a {plan['kind']}")


def bracketed_section(k10: dict, overhang: float) -> list:
    """T-2472: the bracketed timber cornice's section as a bay carries it round its plan,
    [n out, u up] from the bay's wall top: the kit's bed moulding, then the house's eave
    over it, a soffit out to `overhang` and a fascia EAVE_FASCIA_M deep whose top is the
    eaves line. Its brackets are not in it: a bay's own eaves are a band."""
    bed = [list(q) for q in k10["parts"]["profiles"]["bed_mould"]["points"]]
    n, u = bed[-1]
    if overhang < n + 0.1:
        raise ParamError(f"eave_overhang_m {overhang} leaves the bay's soffit no width past its bed moulding")
    return bed + [[overhang, u], [overhang, u + EAVE_FASCIA_M], [0.0, u + EAVE_FASCIA_M]]


def _bays(entries, wall_len: dict, openings: list, structure_id: str, front_stone: bool = False,
          floors: tuple = (), eave: float = 0.0, overhang: float = 0.0, front_coursed: bool = False):
    """Resolve the record's `bays` against the K08 kit; drop the host openings each covers.

    A bay stands in front of its wall from grade to its own wall top, so every host
    opening in that span below the top is behind it and is not cut; one that straddles a
    junction is refused, since half a window behind a bay's cheek is no window at all.
    An oriel (T-2369) stands from its lowest corbel course to its wall top: its floor is
    one of the house's floors (`base_m`), the record may set its corbel courses and size
    its canted plan, and its wall top stays a metre under the main eave — unless the
    record carries it `through_eave` (T-2778), under a spire, its back closed over the
    wall head.
    """
    import copy as _copy
    kit = {v["id"]: v for v in json.loads(BAY_KIT.read_text())["variants"]}
    out = []
    for e in entries or ():
        if e["variant"] not in kit:
            raise ParamError(f"bays: {e['variant']} is not a K08 variant (k08_bays.json)")
        v = _copy.deepcopy(kit[e["variant"]])
        oriel = v["kind"] == "oriel"
        if v["kind"] not in BAY_KINDS or (v["base"] != "grade") != oriel:
            raise ParamError(f"bays: {v['id']} is a {v['kind']} off {v['base']}; a K01 frontage carries "
                             f"a bay or a projection on grade, or an oriel on its corbels")
        if oriel:
            base = float(e.get("base_m", -1.0))
            if not any(abs(base - y) < 1e-6 for y in floors[1:]):
                raise ParamError(f"bays: {e['id']} is an oriel; its base_m stands on one of the upper floors {floors[1:]}")
            v["base"] = base
            if "corbel" in e:
                v["corbel"] = {"courses": int(e["corbel"]["courses"])}
            q = e.get("plan")
            if q is not None:
                pts = [[float(x), float(z)] for x, z in q.get("points", ())]
                if q.get("kind") != "polyline" or len(pts) != len(v["plan"]["points"]) \
                        or any(abs(a[0] + b[0]) > 1e-9 or abs(a[1] - b[1]) > 1e-9 for a, b in zip(pts, pts[::-1])) \
                        or abs(pts[0][1]) > 1e-9 or not all(0.0 < z <= 1.2 for _, z in pts[1:-1]):
                    raise ParamError(f"bays: {e['id']} sizes its oriel's plan as the kit's canted polyline, "
                                     f"symmetric, its ends on the wall and its front at most 1.2 m out")
                v["plan"] = {"kind": "polyline", "points": pts}
        if e["wall"] not in wall_len:
            raise ParamError(f"bays: {e['wall']} is not one of this assembly's walls")
        if e.get("fabric", "stone") not in BAY_FABRICS:
            raise ParamError(f"bays: fabric {e.get('fabric')!r} is not one of {BAY_FABRICS}")
        v["id"] = f"{structure_id}|{e['id']}"
        if e.get("masonry"):
            m = e["masonry"]
            if set(m) - {"coursing"} != {"course_m", "block_m", "joint_m", "relief_m"} or not (.2 <= m["course_m"] <= .6 and .4 <= m["block_m"] <= 1.5 and .004 <= m["joint_m"] <= .02 and .008 <= m["relief_m"] <= .06):
                raise ParamError("bays.masonry: bounded coursed rock-faced ashlar")
            # T-2584: a bay read off its photograph may lay its courses deep and thin in turn,
            # as the street front's T-2566 coursing does; course_m is then the deep course's
            # most, and the thin one stays at least the K02 profiles' least course (0.19 m)
            c = m.get("coursing")
            # T-2773: or on the street front's own beds, as the 1888 plate lays Keith's bow
            if c == {"rhythm": "street_front"}:
                if e["wall"] != "k01.wall.street_front" or not front_coursed:
                    raise ParamError("bays.masonry.coursing 'street_front' lays a bay on a coursed stone "
                                     "street front's beds: the bay stands on k01.wall.street_front, whose "
                                     "stone_front names a coursing")
            elif c is not None and (set(c) != {"rhythm", "low_ratio"} or c["rhythm"] != "alternating"
                                  or not (.25 <= float(c["low_ratio"]) < 1.0)
                                  or float(c["low_ratio"]) * m["course_m"] < .15):
                raise ParamError("bays.masonry.coursing takes rhythm 'alternating' and a low_ratio in "
                                 "[0.25, 1) whose thin course is at least 0.15 m")
            v["masonry"] = m
        if "plan" in e and v["kind"] == "projection":
            # T-2404: a full-height projection read off a picture keeps the picture's width
            # and how far it stands proud; the kit's projection is the shape (a square-cornered
            # pavilion), never the size
            q = e["plan"]
            w, d = float(q["width_m"]), float(q["proud_m"])
            if not (1.5 <= w <= 6.0 and 0.1 <= d <= 1.2):
                raise ParamError(f"bays: {e['id']}'s projection is {w} m wide and {d} m proud; a pavilion "
                                 f"is 1.5-6.0 m wide and stands 0.1-1.2 m proud")
            v["plan"] = {"kind": "polyline", "points": [[-w / 2, 0.0], [-w / 2, d], [w / 2, d], [w / 2, 0.0]]}
        elif "plan" in e and not oriel:
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
        # T-2525: a window's iron grille in its reveal (1621's basement lights, from its drawing)
        for st in v["storeys"]:
            for w in st["windows"]:
                # T-2537: a grouped window's mullion read off a picture (1637's wing, from its
                # engraving): only on a K06 variant of more than one light, and every light kept
                # inside the ordinary sash width
                if "mullion_m" in w:
                    k06 = json.loads(WINDOW_KIT.read_text())
                    v6 = next((x for x in k06["variants"] if x["id"] == w["opening"]), {})
                    mu, n = float(w["mullion_m"]), int(v6.get("bays", 1))
                    cw = float(w.get("clear_width_m", v6.get("clear_width_m", 0.0)))
                    bw = (cw - mu * (n - 1)) / n
                    lo, hi = k06["ranges"]["ordinary_clear_width_m"]
                    if n < 2 or not 0.02 <= mu <= 0.3 or not lo <= bw <= hi:
                        raise ParamError(f"bays: {e['id']}'s mullion_m {mu} needs a grouped K06 opening "
                                         f"(not {w['opening']}), 0.02-0.3 m, and lights {lo}-{hi} m wide "
                                         f"(these are {round(bw, 3)} m)")
                    w["mullion_m"] = mu
                g = w.get("grille")
                if g is None:
                    continue
                if set(g) != {"bars", "set_back_m", "ring_radius_m"} or not 2 <= int(g["bars"]) <= 16 \
                        or not 0.0 < float(g["set_back_m"]) <= 0.08:
                    raise ParamError(f"bays: {e['id']}'s grille takes bars (2-16), set_back_m (at most "
                                     f"0.08 m) and ring_radius_m, not {g}")
                w["grille"] = {"bars": int(g["bars"]), "set_back_m": float(g["set_back_m"]),
                               "ring_radius_m": float(g["ring_radius_m"])}
        # T-2531: a light's dressed head of splayed voussoirs, up to the string course over it
        for st in v["storeys"]:
            for w in st["windows"]:
                h = w.get("voussoirs")
                if h is None:
                    continue
                if set(h) != {"stones", "splay_m", "proud_m", "joint_m", "bevel_m"} \
                        or not 3 <= int(h["stones"]) <= 11 or not 0.0 <= float(h["splay_m"]) <= 0.3 \
                        or not 0.0 < float(h["proud_m"]) <= 0.06 or not 0.0 < float(h["joint_m"]) <= 0.02 \
                        or not 0.0 < float(h["bevel_m"]) < min(float(h["proud_m"]), 0.03):
                    raise ParamError(f"bays: {e['id']}'s voussoirs take stones (3-11), splay_m (0-0.3 m), "
                                     f"proud_m (at most 0.06 m), joint_m (at most 0.02 m) and bevel_m "
                                     f"(under the proud and 0.03 m), not {h}")
                w["voussoirs"] = {k: (int(h[k]) if k == "stones" else float(h[k])) for k in sorted(h)}
        # T-2525: a plinth read off a picture: its height only, the kit's proud and stone kept
        if "plinth_m" in e:
            ph = float(e["plinth_m"])
            if v["base"] != "grade" or not 0.1 <= ph <= 0.6:
                raise ParamError(f"bays: {e['id']}'s plinth_m {ph} is a grade bay's, 0.1-0.6 m")
            v.setdefault("overrides", {}).setdefault("plinth", {})["height_m"] = ph
        if "eaves" in e:
            # T-2369: a hood read off a picture sizes the kit's soffit and fascia, never its shape
            ev = e["eaves"]
            for k, (lo, hi) in (("overhang_m", (0.1, 0.6)), ("fascia_m", (0.1, 0.6))):
                if not lo <= float(ev.get(k, lo)) <= hi:
                    raise ParamError(f"bays: {e['id']}'s eaves {k} {ev.get(k)} is outside [{lo}, {hi}]")
            v.setdefault("overrides", {}).setdefault("eaves", {}).update(
                {k: float(ev[k]) for k in ("overhang_m", "fascia_m") if k in ev})
            # T-2460: a bay rising to the wall's moulded stone cornice carries that cornice's
            # own section round its plan, read from the K10 kit, so the two are one moulding
            if "cornice" in ev:
                k10 = json.loads(K10_KIT.read_text())
                cv = next((x for x in k10["variants"] if x["id"] == ev["cornice"]), None)
                if cv is not None and cv["id"] == BRACKETED_CORNICE and not set(ev) - {"cornice"}:
                    # T-2472: a bay rising to the bracketed timber cornice carries what of it
                    # a bow can: its bed moulding, and the house's eave over that (the K05
                    # soffit out `eave_overhang_m` to a fascia), in the eave's painted timber
                    v["overrides"]["eaves"]["profile"] = bracketed_section(k10, overhang)
                    v["overrides"]["eaves"]["role"] = "fascia"
                elif cv is None or cv["kind"] != "moulded" or set(ev) - {"cornice"}:
                    raise ParamError(f"bays: {e['id']}'s eaves name a K10 moulded cornice, or "
                                     f"{BRACKETED_CORNICE}, and nothing else, not {ev}")
                else:
                    v["overrides"]["eaves"]["profile"] = k10["parts"]["profiles"][cv["profile"]]["points"]
        # T-2525: an iron balcony rail on a bow's eaves, round its plan from wall to wall
        if "balcony" in e:
            bl = e["balcony"]
            need = {"height_m", "inset_m", "post_m", "bar_m", "pitch_m", "rail_m", "foot_rail_m"}
            if v["plan"]["kind"] != "bow" or set(bl) != need:
                raise ParamError(f"bays: {e['id']}'s balcony stands on a bow and takes {sorted(need)}")
            bal = {k: ([float(x) for x in bl[k]] if k == "rail_m" else float(bl[k])) for k in need}
            if not 0.5 <= bal["height_m"] <= 1.2 or not 0.06 <= bal["pitch_m"] <= 0.3 \
                    or not 0.0 < bal["bar_m"] < bal["pitch_m"] / 2 or not 0.0 <= bal["inset_m"] <= 0.3 \
                    or not 0.0 < bal["foot_rail_m"] < bal["height_m"] / 2:
                raise ParamError(f"bays: {e['id']}'s balcony {bal} is not a railing (0.5-1.2 m high, "
                                 f"bars 0.06-0.3 m apart and thinner than half that, 0-0.3 m in from the eaves)")
            v["balcony"] = bal
        # T-2534: a balcony on a projection's floor, bowed out from its front under the window
        # it serves (1637 Prairie's wing, from its engraving): a stone slab and its balustrade
        if "floor_balcony" in e:
            fb = e["floor_balcony"]
            need = {"floor_m", "at", "chord_m", "rise_m", "slab_m", "height_m", "inset_m", "post_m", "bar_m",
                    "pitch_m", "rail_m"}
            if v["kind"] != "projection" or set(fb) != need:
                raise ParamError(f"bays: {e['id']}'s floor_balcony stands on a projection and takes {sorted(need)}")
            bal = {k: ([float(x) for x in fb[k]] if k == "rail_m" else float(fb[k])) for k in need}
            # the projection's plan is cheek, front, cheek; `at` is a fraction of all three, as a
            # window's is, and the bow stands on the front with 0.1 m of wall either side
            (x0, _), (_, proud_m), (x1, _) = v["plan"]["points"][:3]
            front = x1 - x0
            s_c = bal["at"] * (front + 2 * proud_m) - proud_m
            if not bal["chord_m"] / 2 + 0.1 <= s_c <= front - bal["chord_m"] / 2 - 0.1 \
                    or not 0.5 <= bal["chord_m"] <= front - 0.2 \
                    or not 0.1 <= bal["rise_m"] <= min(bal["chord_m"] / 2, 1.2) \
                    or not 0.1 <= bal["slab_m"] <= 0.3 or not 0.5 <= bal["height_m"] <= 1.2 \
                    or not 0.0 <= bal["inset_m"] < bal["rise_m"] / 2 or not 0.06 <= bal["pitch_m"] <= 0.3 \
                    or not 0.0 < bal["bar_m"] < bal["pitch_m"] / 2 or not bal["bar_m"] <= bal["post_m"] <= 0.2:
                raise ParamError(f"bays: {e['id']}'s floor_balcony {bal} is not a balcony on its front: centred "
                                 f"on the front run, a chord 0.5 m to its width less 0.2 m, rising 0.1-1.2 m and at "
                                 f"most half its chord, a 0.1-0.3 m slab, a 0.5-1.2 m rail, bars 0.06-0.3 m apart")
            if not bal["slab_m"] <= bal["floor_m"] < sum(float(st["height_m"]) for st in v["storeys"]):
                raise ParamError(f"bays: {e['id']}'s floor_balcony floor {bal['floor_m']} m is not inside its walls")
            v["floor_balcony"] = bal
        s = float(e["s_m"])
        lo, hi = _bay_span(v["plan"])
        a, b = s + lo, s + hi
        # T-2404: a pavilion may stand flush with its wall's corner — its cheek then runs on in
        # the side wall's own plane, as 1620's north pavilion does in its 1874 engraving. Only
        # a projection, only at the corner it names, and then exactly at it
        flush = e.get("flush_corner")
        if flush is not None:
            if v["kind"] != "projection" or flush not in ("left", "right"):
                raise ParamError(f"bays: {e['id']}: flush_corner is 'left' or 'right', on a projection only")
            at = a if flush == "left" else wall_len[e["wall"]] - b
            if abs(at) > 1e-6:
                raise ParamError(f"bays: {e['id']} is flush with its {flush} corner, and its junction stands "
                                 f"{at:.3f} m from it")
        if (a < BAY_PIER_M - 1e-9 and flush != "left") or \
                (b > wall_len[e["wall"]] - BAY_PIER_M + 1e-9 and flush != "right"):
            raise ParamError(f"bays: {e['id']} meets {e['wall']} at s {a:.3f}..{b:.3f}, closer than "
                             f"{BAY_PIER_M} m to a corner of its {wall_len[e['wall']]} m wall")
        top = sum(float(st["height_m"]) for st in v["storeys"])
        bottom = 0.0
        if oriel:
            kit_all = json.loads(BAY_KIT.read_text())
            bottom = v["base"] - v["corbel"]["courses"] * float(kit_all["parts"]["corbel"]["course_height_m"])
            top += v["base"]
            spire = v["roof"].get("kind") == "spire"
            if e.get("through_eave"):
                # T-2778: an oriel carried up through the eave (1623's, from its drawing): its
                # upper stage stands clear over the main roof under a spire, the house's eave,
                # gutter and bed moulding die into its cants (so its front stands past them),
                # and its back is closed over the wall head, where no wall stands behind it
                front = max(z for _, z in v["plan"]["points"])
                if not spire or top < eave + 0.3 or front < overhang + 0.15:
                    raise ParamError(f"bays: {e['id']} is carried through the eave: under a spire, its wall top "
                                     f"at least 0.3 m over the eave ({eave:.2f} m; has {top:.2f}) and its front "
                                     f"0.15 m past the eave's {overhang} m (has {front})")
                v["back_from_m"] = eave
            elif spire or top > eave - 1.0:
                raise ParamError(f"bays: {e['id']}'s wall top {top:.2f} m is not a metre under the eave "
                                 f"({eave:.2f} m), or it stands under a spire without being carried through it")
        for o in list(openings):
            if o.wall != e["wall"]:
                continue
            o0, o1 = o.s_m - o.width_m / 2 - 0.12, o.s_m + o.width_m / 2 + 0.12   # the lintel's horns
            if o1 <= a or o0 >= b or o.sill_m >= top or o.head_m + 0.30 <= bottom:
                continue
            if o.component == "k01.opening.door_leaf":
                raise ParamError(f"bays: {e['id']} stands in front of the entrance")
            if o0 < a or o1 > b:
                raise ParamError(f"bays: {e['id']}'s junction at s {a:.3f}..{b:.3f} cuts the opening at "
                                 f"s {o.s_m} on {o.wall}")
            openings.remove(o)
        # T-2451: light strips down a bay's corners — 1620's stone strip at its pavilion's north
        # corner, the painted pilasters at its bay window's front corners. Each stands on one run
        # of the plan (point i to i + 1), at its start, its end or both, from `from_m` to `to_m`
        # over grade, inside the bay's own wall
        strips = []
        for j, q in enumerate(e.get("strips") or ()):
            pts = v["plan"]["points"] if v["plan"]["kind"] == "polyline" else None
            run, at = int(q["run"]), q["at"]
            w, d = float(q["width_m"]), float(q["proud_m"])
            y0, y1 = float(q["from_m"]), float(q["to_m"])
            if pts is None or not 0 <= run < len(pts) - 1:
                raise ParamError(f"bays: {e['id']}.strips[{j}] stands on run {run}, which its plan has not")
            length = math.dist(pts[run], pts[run + 1])
            if at not in ("start", "end", "both") or not 0.05 <= w <= (length / 2 if at == "both" else length):
                raise ParamError(f"bays: {e['id']}.strips[{j}] is {w} m wide at {at!r} of a {length:.3f} m run")
            if not 0.01 <= d <= 0.15 or not 0.0 <= y0 < y1 <= top + 1e-9:
                raise ParamError(f"bays: {e['id']}.strips[{j}] stands {d} m proud from {y0} to {y1} m; a strip is "
                                 f"0.01-0.15 m proud, inside the bay's wall (top {top:.2f} m)")
            if q.get("fabric") not in STRIP_FABRICS:
                raise ParamError(f"bays: {e['id']}.strips[{j}] fabric {q.get('fabric')!r} is not one of {tuple(STRIP_FABRICS)}")
            strips.append({"run": run, "at": at, "width_m": w, "proud_m": d, "from_m": y0, "to_m": y1,
                           "fabric": q["fabric"]})
        if e.get("fabric") == "front_stone" and not front_stone:
            raise ParamError(f"bays: {e['id']} is laid in the front's stone, and the record names no K02 stone_front")
        out.append({"id": e["id"], "wall": e["wall"], "s_m": s, "span_m": (round(a, 4), round(b, 4)),
                    "fabric": e.get("fabric", "stone"), "variant": v,
                    **({"flush_corner": flush} if flush else {}),
                    **({"through_eave": True} if e.get("through_eave") else {}),
                    **({"strips": tuple(strips)} if strips else {})})
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
            # T-2526: the door is K07's one round-headed hole, its spring a half span under its crown
            v = {"bays": 1} if o.component == "k01.opening.door_leaf" else variants[kit[o.component]["variant"]]
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
                                 "top_m": g["keystone_top_m"], "width_m": g["keystone_m"]},
                    **({"extrados": g["extrados"], "ring_proud_m": g["ring_proud_m"]} if "extrados" in g else {})})
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
    if po and po.get("archivolt_m") and any(k in po for k in ("top_m", "cornice_m")):
        raise ParamError("a portico's archivolt stands alone on its imposts: it takes no arch block or cornice")
    rails = dress.get("stoop_rails") or {}
    if rails and rails.get("kit") != "k11.rail.stoop_rail":
        raise ParamError("street_front_dress.stoop_rails are the K11 kit's k11.rail.stoop_rail")
    return {"groups": tuple(out), "belts": tuple(belts), "stone_top_m": stone_top, "frieze": fr or {},
            "frontispiece": dress.get("frontispiece") or {}, "portico": po or {},
            "balconettes": dress.get("balconettes") or {}, "grilles": dress.get("grilles") or {},
            "stoop_rails": rails,
            "banded": dress.get("banded") or {}}


def _street_dress(sfw, openings, floors, width) -> dict:
    """T-2753: a named-window front's own belts, which replace K01's two (1625's photograph runs
    one string course, under the first floor's windows), and the dressed quoined surrounds of
    the windows on `surrounds.storeys`: each jamb a dressed stone `returns_m` short and long in
    turn up the courses, and a dressed course `lintel_m` deep over the head, the short return
    past each jamb."""
    out = {}
    if "belts" in sfw:
        belts = [tuple(float(y) for y in b) for b in sfw["belts"]]
        for b0, b1 in belts:
            if not floors[0] < b0 < b1 <= b0 + 0.40:
                raise ParamError(f"street_front_windows.belts {[b0, b1]}: a course at most 0.40 m deep over the ground floor")
            for o in openings:
                if o.wall == "k01.wall.street_front" and o.sill_m < b1 - 1e-6 and o.head_m > b0 + 1e-6:
                    raise ParamError(f"street_front_windows.belts {[b0, b1]} runs through {o.component} at s {o.s_m}")
        out["belts"] = tuple(belts)
    su = sfw.get("surrounds")
    if su:
        if set(su) != {"storeys", "returns_m", "lintel_m"}:
            raise ParamError("street_front_windows.surrounds takes storeys, returns_m [short, long] and lintel_m")
        lo, hi = (float(x) for x in su["returns_m"])
        if not 0.15 <= lo < hi <= 0.6 or not 0.15 <= float(su["lintel_m"]) <= 0.6:
            raise ParamError("street_front_windows.surrounds: returns of 0.15-0.6 m, short then long, and a "
                             "0.15-0.6 m lintel")
        storeys = tuple(sorted(int(k) for k in su["storeys"]))
        if not storeys or not all(0 <= k < len(floors) for k in storeys):
            raise ParamError(f"street_front_windows.surrounds.storeys {list(storeys)} are not this front's storeys")
        out["surrounds"] = {"storeys": storeys, "returns_m": (lo, hi), "lintel_m": float(su["lintel_m"])}
    return out


def _street_frontispiece(fp, openings, dress, floors, width) -> dict:
    """T-2753: the frontispiece of a named-window front (1625's, its photograph): the front from
    `s_m` to its south end and from grade to the hood mould's bed stands `proud_m` out, its
    coursing and the openings in it laid on that face; both its arrises quoined `quoins_m`
    short and long in turn; the door in a dressed surround `band_m` wide, its lintel up to
    `top_m`; over that a carved panel; and capping it all the hood mould over its window,
    `overhang_m` past its face and north arris. Every street opening stands wholly on it or
    wholly off it."""
    keys = {"s_m", "proud_m", "quoins_m", "hood", "door_surround", "panel"}
    if set(fp) != keys:
        raise ParamError(f"street_front_frontispiece takes {sorted(keys)}")
    s0, pr = float(fp["s_m"]), float(fp["proud_m"])
    if not 0.5 <= s0 <= width - 1.0 or not 0.03 <= pr <= 0.30:
        raise ParamError("street_front_frontispiece: its north edge 0.5 m inside the front and 1 m short of its "
                         "south end, and 0.03-0.30 m proud")
    q = tuple(float(x) for x in fp["quoins_m"])
    if len(q) != 2 or not 0.15 <= q[0] < q[1] <= 0.6:
        raise ParamError("street_front_frontispiece.quoins_m: [short, long], 0.15-0.6 m")
    h = fp["hood"]
    if set(h) != {"bed_m", "top_m", "overhang_m"}:
        raise ParamError("street_front_frontispiece.hood takes bed_m, top_m and overhang_m")
    bed, top, ov = float(h["bed_m"]), float(h["top_m"]), float(h["overhang_m"])
    if not floors[1] < bed < top <= bed + 0.40 or not 0.03 <= ov <= 0.20:
        raise ParamError("street_front_frontispiece.hood: a mould at most 0.40 m deep over the first floor, "
                         "0.03-0.20 m past the frontispiece")
    front = [o for o in openings if o.wall == "k01.wall.street_front"]
    on = []
    for o in front:
        a, b = o.s_m - o.width_m / 2, o.s_m + o.width_m / 2
        inside, outside = a >= s0 + q[1] - 1e-6 and o.head_m <= bed - 0.15 + 1e-6, b <= s0 - 0.1 + 1e-6 or o.sill_m >= top + 0.3 - 1e-6
        if not inside and not outside:
            raise ParamError(f"{o.component} at s {o.s_m} stands neither on the frontispiece (clear of its long quoin "
                             f"and 0.15 m under its hood) nor off it")
        if inside:
            on.append(o)
    door = next((o for o in on if o.component == "k01.opening.door_leaf"), None)
    ds = fp["door_surround"]
    if door is None or set(ds) != {"band_m", "top_m"}:
        raise ParamError("street_front_frontispiece.door_surround (band_m, top_m) dresses the door, which stands on it")
    band, stop = float(ds["band_m"]), float(ds["top_m"])
    if not 0.15 <= band <= 0.6 or not door.head_m + 0.15 <= stop <= door.head_m + 0.6:
        raise ParamError("street_front_frontispiece.door_surround: a 0.15-0.6 m band, its lintel 0.15-0.6 m deep")
    if door.s_m - door.width_m / 2 - band < s0 + q[1] - 1e-6 or door.s_m + door.width_m / 2 + band > width - q[1] + 1e-6:
        raise ParamError("street_front_frontispiece.door_surround runs into a quoin")
    pa = fp["panel"]
    if set(pa) != {"s_m", "width_m", "bed_m", "height_m", "proud_m"}:
        raise ParamError("street_front_frontispiece.panel takes s_m, width_m, bed_m, height_m and proud_m")
    pa = {k: float(v) for k, v in pa.items()}
    p0, p1, py0, py1 = pa["s_m"] - pa["width_m"] / 2, pa["s_m"] + pa["width_m"] / 2, pa["bed_m"], pa["bed_m"] + pa["height_m"]
    if p0 < s0 + q[1] - 1e-6 or p1 > width - q[1] + 1e-6 or py0 < stop - 1e-6 or not 0.02 <= pa["proud_m"] <= 0.1 \
            or pa["width_m"] < 0.3 or pa["height_m"] < 0.3:
        raise ParamError("street_front_frontispiece.panel: at least 0.3 m square, 0.02-0.1 m proud, between the "
                         "quoins and over the door's lintel")
    for o in on:
        if o is not door and o.sill_m < py1 - 1e-6 and o.head_m > py0 + 1e-6 and o.s_m - o.width_m / 2 < p1 and o.s_m + o.width_m / 2 > p0:
            raise ParamError(f"street_front_frontispiece.panel meets {o.component} at s {o.s_m}")
    for b0, b1 in dress.get("belts", ()):
        if py0 < b1 - 1e-6 and py1 > b0 + 1e-6:
            raise ParamError("street_front_frontispiece.panel runs into a belt")
    return {"s_m": s0, "proud_m": pr, "quoins_m": q, "hood": {"bed_m": bed, "top_m": top, "overhang_m": ov},
            "door_surround": {"band_m": band, "top_m": stop}, "panel": pa}


def door_arch_of(entrance_kit) -> dict:
    """T-2526: the record's voussoir block round a round-headed door, or {}."""
    return dict(((entrance_kit or {}).get("k01.opening.door_leaf") or {}).get("arch") or {})


WING_SIDES = ("south", "north", "rear")
#: T-2417: what a wing's walls are made of — the K03 brick, or a frame wall in painted timber
WING_FABRICS = ("brick", "frame")
#: T-2417: a frame wing's wall, studs and boards, for its windows' reveals (a brick wing takes the side walls')
FRAME_WALL_M = 0.15


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
        # T-2417: a wing is laid in the K03 brick, or framed in painted timber (`frame`) as a
        # K08 frame bay is (T-2356) — the one-storey frame porch a sheet draws in yellow
        # behind a brick house (1613's)
        fabric = e.get("fabric", "brick")
        if fabric not in WING_FABRICS:
            raise ParamError(f"rear_wings: {wid} is {fabric!r}; a K01 wing is laid in the K03 brick "
                             f"or framed in painted timber ({', '.join(WING_FABRICS)})")
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
        out.append({"id": wid, "fabric": fabric, "rect": (u0, u1, v0, v1), "host_wall": hwall, "host_span_m": (round(a, 4), round(b, 4)),
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

    roof_form = val("roof_form")
    if roof_form not in ("hip", "flat", "mansard", "gable"):
        raise ParamError("k01_frontage builds the contract's k01.roof.hip, k01.roof.flat, "
                         "k01.roof.mansard and k01.roof.gable only")
    flat = roof_form == "flat"
    mansard = roof_form == "mansard"
    gable = roof_form == "gable"
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

    # T-2476: paint over the brick walls, the colour a source names for the house
    wf = val("wall_finish", {}) or {}
    paint = ()
    if wf:
        if construction != "brick":
            raise ParamError("wall_finish paints a brick house's walls; a stone front is not painted here")
        if set(wf) != {"paint"} or set(wf["paint"]) != {"color"}:
            raise ParamError("wall_finish is {\"paint\": {\"color\": [r, g, b]}}")
        paint = tuple(float(x) for x in wf["paint"]["color"])
        if len(paint) != 3 or not all(0.05 <= x <= 1.0 for x in paint):
            raise ParamError(f"wall_finish.paint.color {wf['paint']['color']}: three factors in [0.05, 1]")

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
    band = "flat" if flat else "mansard_upper" if mansard else "ordinary"
    _within(pitch, roof["parameters"]["pitch_deg"]["ranges"][band], "roof_pitch_deg")
    # T-2541: a gable's ridge runs along the street front (T-2459), so its length is the
    # front's and a front block wider than it is deep (1811's) has one; only a hip's runs
    # front to back and needs the side walls longer than the front
    if not flat and not mansard and not gable and depth <= width:
        raise ParamError("a hip roof over this plan needs the side walls longer than the "
                         "front, or its ridge has no length")

    # T-2369: a door below the principal floor opens on a vestibule whose own flight climbs
    # the rest indoors: the record reads that floor off a source, between grade and the hall
    ef = float(val("entrance_floor_m", 0.0) or 0.0)
    if ef:
        efa = form["entrance_floor_m"]
        if not 1.0 <= ef <= pf - 0.5:
            raise ParamError(f"entrance_floor_m {ef} is not a vestibule's floor: at least 1.0 m up and "
                             f"0.5 m under the principal floor ({pf} m)")
        if efa.get("confidence", "reconstructed") == "reconstructed" or not efa.get("sources"):
            raise ParamError("entrance_floor_m puts the door below the principal floor; only a source can")
    door_floor = ef or pf
    # The stair solves to the door's floor in WHOLE risers (datums: principal_floor).
    tread = float(val("stair_tread_m"))
    _within(tread, stair["parameters"]["tread_m"]["range"], "stair_tread_m")
    rng = stair["parameters"]["riser_m"]["range"]
    risers = max(1, round(door_floor / ((rng[0] + rng[1]) / 2)))
    riser = door_floor / risers
    _within(riser, rng, "riser_m (the door's floor / whole risers)")

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
    # T-2408: a three-bay front entered in its middle bay, the door between the bays either
    # side (1620's, beside the bay window its pictures put on the south part)
    if entrance == "middle":
        if len(front_bays) != 3:
            raise ParamError("entrance_bay 'middle' needs a three-bay front")
        door_s = front_bays[1]
    # T-2366: a street front read off a photograph names its own openings, row by row
    sfo = val("street_front_openings")
    if sfo:
        if entrance != "middle" or len(front_bays) != 3:
            raise ParamError("street_front_openings builds a three-bay front entered in its middle bay")
        door_s = front_bays[1]
    # T-2752: a stone front whose windows its photograph puts off the bays' columns, each
    # storey its own (1625's): every street window named with its centre, width, sill and head
    sfw = val("street_front_windows") or {}
    if sfw:
        if not val("stone_front") or sfo or val("front_bays_by_storey") or val("street_front_round_heads"):
            raise ParamError("street_front_windows names every window of a K02 stone front, and takes "
                             "no street_front_openings, front_bays_by_storey or street_front_round_heads")
        if not {"windows", "base_top_m", "belts", "surrounds"} >= set(sfw) >= {"windows", "base_top_m"} \
                or not sfw["windows"]:
            raise ParamError("street_front_windows takes windows: [{component, storey, s_m, width_m, sill_m, "
                             "height_m}, ...] and base_top_m, the plain plinth's top where no area light sets it "
                             "(and, T-2753, belts and surrounds)")
    # T-2410: a brick front's storeys whose street windows are round-headed under hoods
    rh = val("street_front_round_heads") or {}
    if rh:
        if set(rh) != {"storeys", "key"} or set(rh["key"]) != {"width_m", "height_m", "proud_m"}:
            raise ParamError("street_front_round_heads takes storeys [k, ...] and key {width_m, height_m, proud_m}")
        if val("stone_front") or sfo:
            raise ParamError("street_front_round_heads cuts round holes in a brick front; a stone front "
                             "lays its arches with street_front_openings")
        if any(not 0 <= int(k) < stories for k in rh["storeys"]):
            raise ParamError(f"street_front_round_heads.storeys names a storey this {stories}-storey house has not")
        rh = {"storeys": tuple(sorted({int(k) for k in rh["storeys"]})),
              "key": {k: float(x) for k, x in rh["key"].items()}}
    # T-2437: as T-2366 rules for the principal floor, the contract's starting range binds a
    # sash height the record reconstructs; one read off a source stands on that source
    sba = form.get("sash_by_storey") or {}
    sash_read = sba.get("confidence", "reconstructed") != "reconstructed"
    if sash_read and not sba.get("sources"):
        raise ParamError(f"sash_by_storey is {sba.get('confidence')} and names no source: "
                         "outside the contract's starting range only a source can place it")
    # T-2451: an upper storey whose street windows its picture draws off the bays below (1620's
    # window over the door, south of the door's own centre): that storey's own centres, one a
    # bay, in order. Never the principal storey's, whose middle bay is the door
    fbs = {}
    for key, xs in (val("front_bays_by_storey") or {}).items():
        k = int(key)
        xs = tuple(float(x) for x in xs)
        if sfo or not 1 <= k < stories:
            raise ParamError(f"front_bays_by_storey names storey {key}: only an upper storey of a front "
                             f"that does not name its own openings")
        if not xs or list(xs) != sorted(xs) or xs[0] < 0.6 or xs[-1] > width - 0.6:
            raise ParamError(f"front_bays_by_storey[{key}] is one centre a bay, south to north, inside the front")
        # T-2499: an upper storey may light its own number of bays — 1808's third storey runs six
        # sashes across a front its lower storeys open in three — so long as no two of its sashes,
        # with their lintels' horns, meet
        sw = float(sash[k]["width_m"])
        if len(xs) != len(front_bays) and any(b - a < sw + 2 * 0.12 + 0.02 for a, b in zip(xs, xs[1:])):
            raise ParamError(f"front_bays_by_storey[{key}] sets its centres closer than a {sw} m sash and its "
                             f"lintels' horns")
        fbs[k] = xs
    for k, row in enumerate(sash):
        sill = floors[k] + float(row["sill_above_floor_m"])
        w, h = float(row["width_m"]), float(row["height_m"])
        _within(w, cw, f"sash_by_storey[{k}].width_m")
        if not sash_read:
            _within(h, ch, f"sash_by_storey[{k}].height_m")
        head = sill + h
        if k + 1 < stories and head + 0.30 > floors[k + 1] + float(sash[k + 1]["sill_above_floor_m"]) - 0.10:
            raise ParamError(f"storey {k}'s heads run into storey {k + 1}'s sills")
        # a hip's soffit drops by the overhang's run down its slope; a mansard's stands on
        # the wall head (T-2370)
        drop = 0.0 if mansard else float(val("eave_overhang_m")) * math.tan(math.radians(pitch))
        if k + 1 == stories and head + 0.30 > eave - drop - 0.25:
            raise ParamError("the top storey's lintels run into the soffit")
        for s in (() if sfo or sfw else fbs.get(k, front_bays)):
            if k == 0 and s == door_s:
                continue
            comp = ROUND_HOODED if rh and k in rh["storeys"] else "k01.opening.sash_flat"
            openings.append(Opening(comp, "k01.wall.street_front", s, round(sill, 4), w, h))
        for s in val("side_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.south", float(s), round(sill, 4), w, h))
        for s in val("rear_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.rear_service", float(s), round(sill, 4), w, h))
        for s in val("north_bays") or ():
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.north", float(s), round(sill, 4), w, h))
    openings.append(Opening("k01.opening.door_leaf", "k01.wall.street_front", door_s, round(door_floor, 4), 1.20, 2.70, False))
    if sfw:
        kit_ids = {v["id"]: v for v in json.loads(WINDOW_KIT.read_text())["variants"]}
        door = (door_s - 0.60 - 0.30, door_s + 0.60 + 0.30, door_floor + 2.70 + 0.30)
        laid = []
        for k, w in enumerate(sfw["windows"]):
            if set(w) != {"component", "storey", "s_m", "width_m", "sill_m", "height_m"}:
                raise ParamError(f"street_front_windows.windows[{k}] takes component, storey, s_m, width_m, sill_m and height_m")
            comp, st = w["component"], int(w["storey"])
            s, wd, sill, h = (float(w[x]) for x in ("s_m", "width_m", "sill_m", "height_m"))
            entry = (val("window_kit") or {}).get(comp)
            vid = entry if isinstance(entry, str) else (entry or {}).get("variant")
            if not comp.startswith(STREET_WINDOW) or vid not in kit_ids:
                raise ParamError(f"street_front_windows.windows[{k}]: {comp!r} is not a {STREET_WINDOW}* "
                                 f"component the window_kit glazes")
            if not 0 <= st < stories or not floors[st] < sill or sill + h + 0.30 > (
                    floors[st + 1] if st + 1 < stories else eave - 0.25):
                raise ParamError(f"street_front_windows.windows[{k}] does not stand in storey {st} under "
                                 f"its flat arch's 0.30 m")
            s0, s1 = s - wd / 2, s + wd / 2
            if s0 < 0.30 or s1 > width - 0.30:
                raise ParamError(f"street_front_windows.windows[{k}] runs within 0.30 m of the front's end")
            if s0 < door[1] and s1 > door[0] and sill < door[2]:
                raise ParamError(f"street_front_windows.windows[{k}] stands over the door below its head")
            for j, (a0, a1, b0, b1) in enumerate(laid):
                if s0 < a1 + 0.24 and s1 > a0 - 0.24 and sill < b1 + 0.30 and sill + h > b0 - 0.30:
                    raise ParamError(f"street_front_windows.windows[{k}] meets windows[{j}] or its flat arch")
            laid.append((s0, s1, sill, sill + h))
            dh = kit_ids[vid]["operation"].startswith("double_hung")
            openings.append(Opening(comp, "k01.wall.street_front", round(s, 4), round(sill, 4), wd, h, dh))
    street_dress, frontispiece = {}, {}
    if sfw:
        street_dress = _street_dress(sfw, openings, floors, width)
    if val("street_front_frontispiece"):
        if not sfw:
            raise ParamError("street_front_frontispiece dresses a front laid by street_front_windows")
        frontispiece = _street_frontispiece(val("street_front_frontispiece"), openings, street_dress, floors, width)
    # T-2366: a front that names its own openings names its basement lights among them
    bl = val("basement_lights") or {}
    if sfw and bl:
        # T-2752: a front that names its windows one by one names them all; 1625's plinth is plain
        raise ParamError("street_front_windows names every street window; it takes no basement_lights")
    if not sfw and bool(bl) == bool(sfo):
        raise ParamError("basement_lights names the area lights of a front without street_front_openings, "
                         "and only of one")
    bsill = float(bl.get("sill_m", 0.0))
    for s in (() if sfo or sfw else front_bays):
        if s != door_s:
            openings.append(Opening("k01.opening.area_light", "k01.wall.street_front", s, bsill,
                                    float(bl["width_m"]), float(bl["height_m"]), False))
    if not sfo and not sfw and bsill + float(bl["height_m"]) + 0.30 > pf + float(sash[0]["sill_above_floor_m"]) - 0.10:
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

    flat_roof = _flat_roof(depth, eave, pitch, float(val("eave_overhang_m"))) if flat else {}
    mansard_roof = _mansard_roof(val("mansard"), depth, width, eave, pitch,
                                 float(val("eave_overhang_m"))) if mansard else {}
    gable_roof = _gable_roof(val("gable_roof"), depth, width, eave, pitch, st) if gable else {}
    # T-2820: the rear section, resolved before the stacks, one of which may stand on its attic
    from .k01_rear_section import resolve as resolve_rear_section
    rear_section = resolve_rear_section(val("rear_section") or {}, depth=depth, width=width, eave=eave,
                                        side_wall=float(val("wall_thickness_side_m")),
                                        overhang=float(val("eave_overhang_m")), cw=cw,
                                        openings=openings)
    if rear_section and (flat or mansard or gable):
        raise ParamError("rear_section stands beside a hipped K01 roof (the one built)")
    if val("gable_roof") and not gable:
        raise ParamError(f"a {roof_form} roof names no gable_roof")
    if gable and val("rainwater"):
        raise ParamError("a gable K01 roof hangs no gutter yet: k01_frontage runs its half-round gutter "
                         "round a hip's eaves, and a gable's side walls are parapets (rainwater is empty)")
    k04, rainwater = _k04(val("roof_covering") or {}, val("rainwater") or {}, pitch, flat,
                          mansard_roof.get("lower_pitch_deg"), gable)
    if val("mansard") and not mansard:
        raise ParamError(f"a {roof_form} roof names no mansard")
    dormer = {}
    d = val("dormer")
    if d and flat:
        raise ParamError("a flat K01 roof carries no dormer: the K05 dormer is cut into a hip's street plane")
    if d and mansard:
        raise ParamError("a K01 mansard carries no dormer yet: the K05 dormer is cut into a hip's "
                         "street plane, and a mansard's lower face is another surface (T-2370)")
    if d:
        dw, dh = float(d["sash"]["width_m"]), float(d["sash"]["height_m"])
        wg = d.get("wall_gable")
        if wg:
            # T-2428: a wall gable's roof-storey lights are K06 variants of their own (1619's
            # three short segment-headed lights), not the principal sash the contract sizes
            if not 0.5 <= dw <= 1.2 or not 0.6 <= dh <= 2.4:
                raise ParamError("dormer.sash: a wall gable's lights are 0.5-1.2 m wide and 0.6-2.4 m high")
        else:
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
        if wg:
            dormer.update(_wall_gable(d, wg, dormer, width))

    shaped = _shaped_gable(val("shaped_gable") or {}, roof_form, dormer, width, eave, pitch,
                           float(val("eave_overhang_m")))

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
        if comp == ROUND_HOODED:
            # T-2410: the K01 wall cuts this one's round hole (k01_frontage.wall), so its
            # variant is a single round-headed sash, and its hood and key must clear K10's
            # bed moulding as any K01 head does (HEAD_RISE_M, 0.30 m over the crown)
            if v["head"] != "round" or v.get("bays", 1) != 1:
                raise ParamError(f"window_kit: {comp} is cut as one round hole, and {vid} is not a single round-headed sash")
            band = json.loads(WINDOW_KIT.read_text())["parts"]["head_band"]
            key = rh["key"]
            if not band["width_m"] < key["height_m"] <= 0.30 or key["proud_m"] <= band["proud_m"] or \
                    key["width_m"] > min(o.width_m for o in openings if o.component == comp) / 2:
                raise ParamError(f"street_front_round_heads.key: {key['width_m']} x {key['height_m']} m, "
                                 f"{key['proud_m']} m proud, does not stand on the hood's crown (over its "
                                 f"{band['width_m']} m band and {band['proud_m']} m proud, inside 0.30 m and half the sash)")
        elif v["head"] != "flat" and not (comp in arched_rows and val("stone_front")) and not (
                comp.startswith(STREET_WINDOW) and v["head"] == "segmental"):
            # T-2752: the coursed stone front fills a named street window's segmental head
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
    da = door_arch_of(val("entrance_kit"))
    if da:
        # T-2526: the door's round head under its own voussoir block, as an arched group
        if not val("stone_front"):
            raise ParamError("entrance_kit.arch: a door's voussoirs are laid in a K02 stone front's courses")
        need = {"ring_m", "keystone_top_m", "keystone_m"}
        # T-2531: optionally the ring's curved extrados (`extrados`, the ring `ring_proud_m`
        # before the wall) and a band over its crown (`band_m`, a belt course [foot, top])
        if not need <= set(da) <= need | {"extrados", "ring_proud_m", "band_m"}:
            raise ParamError(f"entrance_kit.arch takes {sorted(need)}, and extrados, ring_proud_m and band_m")
        if not 0.15 <= float(da["ring_m"]) <= 0.6:
            raise ParamError("entrance_kit.arch.ring_m: a voussoir block 0.15-0.6 m outside the arch")
        if da.get("extrados", "curved") != "curved" or ("ring_proud_m" in da) != ("extrados" in da) \
                or not 0.0 <= float(da.get("ring_proud_m", 0.0)) <= 0.06:
            raise ParamError("entrance_kit.arch.extrados is 'curved', with ring_proud_m 0-0.06 m beside it")
        di = next(i for i, o in enumerate(openings) if o.component == "k01.opening.door_leaf")
        arched_groups.append({"component": "k01.opening.door_leaf", "bay": front_bays.index(door_s), "ops": [di],
                              "ring_m": float(da["ring_m"]), "keystone_top_m": float(da["keystone_top_m"]),
                              "keystone_m": tuple(float(x) for x in da["keystone_m"]),
                              **({"extrados": "curved", "ring_proud_m": float(da["ring_proud_m"])}
                                 if "extrados" in da else {})})
    arched = _arched_front(arched_groups, openings, variants, kit, val("street_front_dress") or {},
                           pf, floors, width, door_s,
                           # T-2528: the soffit the roof builds; a mansard's stands on the wall head
                           eave - (0.0 if mansard else float(val("eave_overhang_m")) * math.tan(math.radians(pitch)))
                           - EAVE_FASCIA_M) \
        if sfo or da else {}
    if da and not sfo:
        arched["belts"] = None    # a door's arch alone keeps K01's own belts (k01_frontage.stone_front)
        if "band_m" in da:
            # T-2531: K01's own belts, and a band laid on the arch's crown as one more
            b0, b1 = (float(y) for y in da["band_m"])
            top = max(g["top_m"] for g in arched["groups"] if g["component"] == "k01.opening.door_leaf")
            if not (abs(b0 - top) < 1e-6 and 0.08 <= b1 - b0 <= 0.3 and b1 < floors[1] - 0.2 - 0.3):
                raise ParamError(f"entrance_kit.arch.band_m {da['band_m']}: a band 0.08-0.3 m deep on the "
                                 f"voussoirs' top ({top} m), a course clear of the second floor's belt")
            arched["belts"] = ((floors[1] - 0.20, floors[1]), *([(floors[2] - 0.15, floors[2])] if len(floors) > 2 else []),
                               (b0, b1))
    if val("street_front_dress") and not sfo:
        raise ParamError("street_front_dress dresses a street front laid by street_front_openings")
    # T-2304: the door and its stoop are a K07 entrance. The K01 wall cuts a rectangular
    # hole at the principal floor, so only a flat-headed principal entrance on a straight
    # stoop fits it; the stair is solved from this record's own floor, tread, landing and
    # width, and it must agree with the K01 stair's whole risers and stay in the front yard.
    ek = val("entrance_kit") or {}
    door_kit = dict(ek.get("k01.opening.door_leaf") or {})
    door_kit_in = dict(door_kit)
    ekit = json.loads(ENTRANCE_KIT.read_text())
    evs = {v["id"]: v for v in ekit["variants"]}
    ev = evs.get(door_kit.get("variant"))
    if ev is None:
        raise ParamError("entrance_kit names no K07 variant for k01.opening.door_leaf (k07_entrances.json)")
    # T-2526: a stone front may lay its door's round head as an arched group (`arch`): the
    # courses go round the jambs to the spring and a voussoir block over it, so the hole is
    # K07's own round one and the door stands round-headed in its reveal
    door_arch = door_arch_of(val("entrance_kit"))
    if (ev["head"] != ("round" if door_arch else "flat") or ev["use"] != "principal"
            or ev["stair"]["kind"] != "straight"):
        raise ParamError(f"entrance_kit: {ev['id']} is a {ev['head']}-headed {ev['use']} entrance on a "
                         f"{ev['stair']['kind']} stair; a K01 front cuts a rectangular hole at the "
                         f"principal floor over a straight stoop, or (`arch`) a round one in a stone front")
    yard = float(door_kit.get("front_yard_m", 0.0))
    reach = float(val("stair_landing_depth_m")) + (risers - 1) * tread
    if not reach < yard:
        raise ParamError(f"entrance_kit: the stoop reaches {reach:.2f} m from the front, and the public "
                         f"walk's inner edge is {yard:.2f} m (front_yard_m)")
    k07_risers = max(1, round(door_floor / ekit["parts"]["stair"]["riser_target_m"]))
    if k07_risers != risers:
        raise ParamError(f"entrance_kit: K07 solves {door_floor} m in {k07_risers} risers and the K01 stair in "
                         f"{risers}; one stoop cannot be both")
    terrace, balustrade = door_kit.get("terrace"), door_kit.get("balustrade")
    door_kit = {"variant": ev["id"], "front_yard_m": yard}
    # T-2409: a terrace at the landing's height running from the stoop along the front to
    # `to_v_m` (the front's own s), its back stepped out where the front stands proud, and
    # a turned balustrade on it and on the stoop's cheeks
    # T-2450: or one a side, as a list — a left one's to_v_m and back run south of the stoop,
    # and its to_v_m may pass the front's south corner (v < 0)
    if terrace is not None:
        terraces = []
        for t in (terrace if isinstance(terrace, list) else [terrace]):
            if set(t) - {"side", "to_v_m", "back", "out_m", "loggia"} or t.get("side", "right") not in ("right", "left"):
                raise ParamError("entrance_kit.terrace takes side 'right' or 'left', to_v_m, "
                                 "back [[v, out], ...], out_m and loggia alone, or a list of one a side")
            terraces.append({"side": t.get("side", "right"), "to_v_m": float(t["to_v_m"]),
                             "back": [[float(v), float(o)] for v, o in t.get("back", [])]})
            # T-2500: a terrace deeper than the landing (1808's loggia deck), and the loggia on
            # it (k07_entrances.Entrance._loggia): its deck clear of the walk, and its parts
            # named in full so a record cannot half-specify one
            if "out_m" in t:
                out = float(t["out_m"])
                if not float(val("stair_landing_depth_m")) < out < yard:
                    raise ParamError(f"entrance_kit.terrace.out_m: {out} m is not deeper than the landing "
                                     f"and short of the walk at {yard} m")
                terraces[-1]["out_m"] = out
            if "loggia" in t:
                lg = t["loggia"]
                need = {"pedestal": {"width_m", "depth_m", "height_m"},
                        "columns": {"height_m", "segments", "profile"},
                        "entablature": {"height_m"}, "balcony": {"thickness_m", "height_m"},
                        "parapet": {"thickness_m", "height_m"}, "arch": {"span_m", "spring_m", "depth_m"}}
                if set(lg) - {"finish"} != set(need) or any(set(lg[k]) != v for k, v in need.items()):
                    raise ParamError(f"entrance_kit.terrace.loggia takes {sorted(need)}, each with "
                                     + "; ".join(f"{k}: {sorted(v)}" for k, v in need.items()))
                if "out_m" not in t:
                    raise ParamError("entrance_kit.terrace.loggia stands on a terrace with its own out_m")
                if lg.get("finish") not in (None, "ionic_carved"):
                    raise ParamError("loggia.finish is ionic_carved")
                prof = lg["columns"]["profile"]
                if prof[0][1] != 0.0 or prof[-1][1] != 1.0 or any(b[1] <= a[1] for a, b in zip(prof, prof[1:])):
                    raise ParamError("entrance_kit.terrace.loggia.columns.profile runs [r, fraction of height] from 0 to 1")
                if 2 * max(r for r, _ in prof) > float(lg["pedestal"]["width_m"]) / 2:
                    raise ParamError("entrance_kit.terrace.loggia: two columns do not stand side by side on a pedestal")
                terraces[-1]["loggia"] = lg
        if len({t["side"] for t in terraces}) != len(terraces):
            raise ParamError("entrance_kit.terrace: one terrace a side")
        door_kit["terrace"] = terraces[0] if len(terraces) == 1 else terraces
    if balustrade is not None:
        need = {"height_m", "pitch_m", "newel_m", "newel_cap_m", "rail_m", "segments", "profile"}
        if set(balustrade) != need:
            raise ParamError(f"entrance_kit.balustrade takes {sorted(need)}")
        prof = balustrade["profile"]
        if prof[0][1] != 0.0 or prof[-1][1] != 1.0 or any(b[1] <= a[1] for a, b in zip(prof, prof[1:])):
            raise ParamError("entrance_kit.balustrade.profile runs [r, fraction of height] from 0 to 1")
        door_kit["balustrade"] = dict(balustrade)
    if door_arch:
        door_kit["arch"] = dict(door_arch)
    # T-2369: a stoop between iron rails has no stone cheeks, and a door in a vestibule's
    # mouth stands deeper in its wall than the kit's outer leaf
    if "cheeks" in door_kit_in:
        door_kit["cheeks"] = bool(door_kit_in["cheeks"])
    if "reveal_depth_m" in door_kit_in:
        rev = float(door_kit_in["reveal_depth_m"])
        fd = ekit["parts"]["frame"]["depth_m"]
        # T-2531: a variant with a vestibule sets its door at the back of a recess deeper than
        # the wall, as deep as the kit's own reveal for it
        deepest = max(ft - fd, float(ev["reveal_depth_m"]) if ev.get("vestibule_m") else 0.0)
        if not ekit["parts"]["reveal_depth_m"]["range"][0] <= rev <= deepest:
            raise ParamError(f"entrance_kit: the door's reveal {rev} m and its {fd} m frame do not fit "
                             f"the {ft} m front wall" + (f", or the kit's {deepest} m vestibule" if deepest > ft - fd else ""))
        door_kit["reveal_depth_m"] = rev
    # T-2480: a bracketed timber hood over the door, in a K08 bay hood's joinery (its consoles
    # and modillions), its flat top railed as a small balcony; k01_frontage.door_hood builds it
    if "hood" in door_kit_in:
        hd = door_kit_in["hood"]
        need = {"soffit_m", "width_m", "out_m", "fascia_m", "cornice", "brackets", "railing"}
        if set(hd) != need or set(hd["cornice"]) != {"height_m", "proud_m"} or \
                set(hd["railing"]) != {"height_m", "post_m", "baluster_m", "pitch_m", "rail_m"}:
            raise ParamError(f"entrance_kit.hood takes {sorted(need)}, its cornice height_m and proud_m, "
                             f"its railing height_m, post_m, baluster_m, pitch_m and rail_m [width, depth]")
        bay = {v["id"]: v for v in json.loads(BAY_KIT.read_text())["variants"]}.get(hd["brackets"])
        if not bay or not bay.get("brackets"):
            raise ParamError(f"entrance_kit.hood.brackets: {hd['brackets']!r} is not a bracketed K08 variant")
        con, mod = bay["brackets"]["consoles"], bay["brackets"]["modillions"]
        if con["reach_m"] > hd["out_m"]:
            raise ParamError(f"entrance_kit.hood: {hd['brackets']}'s consoles reach {con['reach_m']} m, "
                             f"past the hood's {hd['out_m']} m")
        if mod["drop_m"] >= hd["fascia_m"]:
            raise ParamError("entrance_kit.hood: the modillions hang deeper than the fascia they stand on")
        if (val("street_front_trim") or {}).get("entrance"):
            raise ParamError("entrance_kit.hood: the door takes the hood or a K09 entrance, not both")
        door_kit["hood"] = {**{k: float(hd[k]) for k in ("soffit_m", "width_m", "out_m", "fascia_m")},
                            "cornice": {k: float(v) for k, v in hd["cornice"].items()},
                            "railing": {k: ([float(x) for x in v] if isinstance(v, list) else float(v))
                                        for k, v in hd["railing"].items()},
                            "brackets": hd["brackets"], "consoles": dict(con), "modillions": dict(mod)}
    # T-2463: a stoop whose axis is not its door's (1620's, the door at the south end of a
    # landing that runs on north into the porch): the stoop's centre along the front, in the
    # front's own s. The door has to stand on the landing or on a terrace beside it
    if "stoop_v_m" in door_kit_in:
        sv = float(door_kit_in["stoop_v_m"])
        half, dh = float(val("stoop_width_m")) / 2, 1.20 / 2
        sides = {t["side"] for t in (door_kit.get("terrace") or [])} if isinstance(door_kit.get("terrace"), list) \
            else ({door_kit["terrace"]["side"]} if door_kit.get("terrace") else set())
        if not 0 <= sv - half or not sv + half <= width:
            raise ParamError(f"entrance_kit.stoop_v_m: a {2 * half} m stoop on v {sv} leaves the front")
        if (door_s - dh < sv - half - 1e-9 and "left" not in sides) or \
                (door_s + dh > sv + half + 1e-9 and "right" not in sides):
            raise ParamError(f"entrance_kit.stoop_v_m: the door at v {door_s} hangs off the stoop's landing "
                             f"(v {sv - half:.3f}-{sv + half:.3f}) where no terrace carries it on")
        door_kit["stoop_v_m"] = sv
    # T-2530: a side stoop (1621's, from the Building Budget drawing): the landing runs along
    # the front over `landing_v_m` (the front's own s), and the flight leaves its `run` end
    # parallel to the front, `out_m` clear of the face so that it passes in front of a bay,
    # behind a cheek on its street side (k07_entrances.Entrance._side_stoop)
    if "side_stoop" in door_kit_in:
        ss = door_kit_in["side_stoop"]
        if not {"run", "landing_v_m", "out_m"} <= set(ss) <= {"run", "landing_v_m", "out_m", "cheek_above_nosing_m"} \
                or ss["run"] not in ("right", "left"):
            raise ParamError("entrance_kit.side_stoop takes run ('right' or 'left'), landing_v_m [from, to], "
                             "out_m and optionally cheek_above_nosing_m")
        if {"terrace", "balustrade", "stoop_v_m", "cheeks"} & set(door_kit_in):
            raise ParamError("entrance_kit.side_stoop is its own stair: no terrace, balustrade, stoop_v_m or cheeks")
        a, b = sorted(float(x) for x in ss["landing_v_m"])
        o0, k = float(ss["out_m"]), 1.0 if ss["run"] == "right" else -1.0
        cheek_t = float(ekit["parts"]["cheek"]["thickness_m"])
        run = (risers - 1) * tread
        far, near = (a, b) if k > 0 else (b, a)
        foot = near + k * run
        if not a < door_s < b:
            raise ParamError(f"entrance_kit.side_stoop: the door at v {door_s} is not on its landing (v {a}-{b})")
        if not 0 <= min(far - k * cheek_t, foot) or not max(far - k * cheek_t, foot) <= width:
            raise ParamError(f"entrance_kit.side_stoop: the landing's cheek or the flight's foot (v {foot:.3f}) "
                             f"leaves the {width} m front")
        reach = o0 + float(val("stoop_width_m")) + cheek_t
        if not reach < yard:
            raise ParamError(f"entrance_kit.side_stoop: the cheek reaches {reach:.2f} m from the front, and the "
                             f"public walk's inner edge is {yard:.2f} m (front_yard_m)")
        for bay in (val("bays") or []):
            if bay.get("wall", "k01.wall.street_front") != "k01.wall.street_front":
                continue
            half = float(bay["plan"]["chord_m"]) / 2
            b0, b1 = float(bay["s_m"]) - half, float(bay["s_m"]) + half
            if b0 < b - 1e-9 and a + 1e-9 < b1:
                raise ParamError(f"entrance_kit.side_stoop: the landing (v {a}-{b}) stands on the {bay['id']} bay")
            lo, hi = sorted((near, foot))
            if b0 < hi and lo < b1 and not float(bay["plan"]["rise_m"]) < o0:
                raise ParamError(f"entrance_kit.side_stoop: the flight {o0} m out runs into the {bay['id']} bay, "
                                 f"which stands {bay['plan']['rise_m']} m proud")
        door_kit["side_stoop"] = {"run": ss["run"], "landing_v_m": [a, b], "out_m": o0,
                                  **({"cheek_above_nosing_m": float(ss["cheek_above_nosing_m"])}
                                     if "cheek_above_nosing_m" in ss else {})}
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
        ridge = (flat_roof["deck_high_m"] if flat else mansard_roof["ridge_m"] if mansard
                 else gable_roof["ridge_m"] if gable
                 else (round(pf + sum(heights), 4) + width / 2 * tp))
        for st_ in ch["stacks"]:
            u, v = float(st_["u_m"]), float(st_["v_m"])
            sx, sz = (float(x) for x in st_.get("plan_m", ch["plan_m"]))
            base = None
            if st_.get("on_cornice"):
                # T-2406: a stack standing on a mansard's cornice over a side wall (1620's
                # front stack, its 1874 engraving): it straddles the wall line, its outer
                # face no further out than the cornice's edge, and rises from the wall head
                o = float(val("eave_overhang_m"))
                if not mansard:
                    raise ParamError(f"chimney at ({u}, {v}): only a mansard's cornice carries a stack")
                if not (sx / 2 + 0.3 <= u <= depth - sx / 2 - 0.3):
                    raise ParamError(f"chimney at ({u}, {v}) does not stand along the side wall")
                if not (min(v - sz / 2, width - v - sz / 2) < 0.0
                        and max(sz / 2 - v, v + sz / 2 - width) <= o + 1e-9):
                    raise ParamError(f"chimney at ({u}, {v}) does not straddle a side wall inside its {o} m cornice")
                base = round(pf + sum(heights), 4)
            elif st_.get("in_parapet"):
                # T-2459: a stack carried up in a gable roof's side-wall parapet (1619's south
                # stack at the head of its crow steps, its drawing): its outer face is the
                # wall's, and it rises from the wall head as the parapet does
                if not gable:
                    raise ParamError(f"chimney at ({u}, {v}): only a gable roof's parapet carries a stack")
                if not (sx / 2 + 0.3 <= u <= depth - sx / 2 - 0.3):
                    raise ParamError(f"chimney at ({u}, {v}) does not stand along the side wall")
                if not (abs(v - sz / 2) < 1e-6 or abs(v + sz / 2 - width) < 1e-6):
                    raise ParamError(f"chimney at ({u}, {v}): a parapet stack's outer face is the side wall's")
                if sz < st:
                    raise ParamError(f"chimney at ({u}, {v}) is thinner than the parapet it stands in")
                base = round(pf + sum(heights), 4)
            elif st_.get("in_rear_section"):
                # T-2820: a stack carried up in the rear section's end parapet (1625's rear stack,
                # its photograph): its outer face is the step-out's outer wall, and it rises from
                # the wall head as the parapet does, clearing the attic's ridge
                if not rear_section:
                    raise ParamError(f"chimney at ({u}, {v}): this house has no rear section")
                u0r, u1r, _v0r, v1r = rear_section["rect"]
                if not (u0r + sx / 2 + 0.3 <= u <= u1r - sx / 2 - 0.3):
                    raise ParamError(f"chimney at ({u}, {v}) does not stand along the rear section's end wall")
                if abs(v + sz / 2 - v1r) > 1e-6 or sz < rear_section["attic"]["parapet_m"]:
                    raise ParamError(f"chimney at ({u}, {v}): an end-parapet stack's outer face is the "
                                     f"step-out's, and it is no thinner than the parapet")
                base = round(pf + sum(heights), 4)
            elif not (sx / 2 + 0.3 <= u <= depth - sx / 2 - 0.3 and sz / 2 + 0.3 <= v <= width - sz / 2 - 0.3):
                raise ParamError(f"chimney at ({u}, {v}) does not stand inside the footprint")
            if above < 0.6:
                raise ParamError("a chimney stops less than 0.6 m above the ridge")
            top = round((rear_section["attic"]["ridge_m"] if st_.get("in_rear_section") else ridge) + above, 4)
            # T-2406: a stack read off a picture stands at its own top. On a mansard it may
            # stop under the ridge, beside the upper hip it cannot see over (1620's front
            # stack, at the north wall's front corner): it clears the curb by the same 0.6 m
            # a ridge stack clears its ridge, and the crown's curb where one stands
            if "top_m" in st_:
                top = float(st_["top_m"])
                if st_.get("in_rear_section"):
                    if top < rear_section["attic"]["ridge_m"] + 0.6 - 1e-9:
                        raise ParamError(f"chimney at ({u}, {v}) tops at {top} m, under the rear section's "
                                         f"ridge + 0.6")
                elif flat:
                    # T-2712: a flat-roof stack read off a picture may stop under the parapet
                    # that hides it (1808's hall stack, under the north return's coping, its
                    # flue carried on by the cowl pipe every 1887-89 view shows). It clears
                    # the deck it stands on by the same 0.6 m, the stone finish's drop taken
                    deck = flat_roof["deck_high_m"] - float((val("stone_finish") or {}).get("deck_drop_m", 0.0))
                    if top < deck + 0.6 - 1e-9:
                        raise ParamError(f"chimney at ({u}, {v}) tops at {top} m, under the deck's "
                                         f"{deck:.3f} m + 0.6")
                elif not mansard:
                    raise ParamError(f"chimney at ({u}, {v}): a top_m of its own is a mansard or a flat "
                                     "roof's stack")
                else:
                    crown = (val("mansard") or {}).get("crown") or {}
                    curb = mansard_roof["curb_m"] + float(crown.get("rise_above_curb_m", 0.0))
                    if top < curb + 0.6 - 1e-9:
                        raise ParamError(f"chimney at ({u}, {v}) tops at {top} m, under the curb's {curb} m + 0.6")
            chimneys.append({"u_m": u, "v_m": v, "plan_m": (sx, sz), "top_m": top, "base_m": base,
                             "cap_proud_m": cap_p, "cap_depth_m": cap_d})
    elif ch and (flat or mansard or gable):
        raise ParamError(f"a {roof_form} K01 roof takes T-2302's plain stacks: K15's draught rule "
                         "reads a hip's covering")
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
            if abs(c["v_m"] - dormer.get("v_m", width / 2)) < dormer["width_m"] / 2 + 0.5 + sz / 2 \
                    and c["u_m"] + sx / 2 > back - 0.3:
                raise ParamError("a chimney stands in the dormer's body")

    # T-2291: the brick walls wear a K03 panel the record names; k03_brick lays one
    from . import k03_brick
    panel = val("service_wall_brick", k03_brick.PANEL)
    if panel != k03_brick.PANEL:
        raise ParamError(f"service_wall_brick = {panel!r}: k03_brick lays {k03_brick.PANEL!r} alone; "
                         f"another K03 panel is a new slot in generators/archetypes/k03_brick.py")

    # a bay drops the openings behind it, so an arched group finds its own again by identity
    grouped = [[openings[i] for i in g["ops"]] for g in (arched or {}).get("groups", ())]
    bays = _bays(val("bays"), {"k01.wall.street_front": width, "k01.wall.rear_service": width,
                               "k01.wall.side.south": depth, "k01.wall.side.north": depth},
                 openings, (record or {}).get("id", ""), bool(val("stone_front")), tuple(floors), eave,
                 float(val("eave_overhang_m")), bool((val("stone_front") or {}).get("coursing")))
    for g, ops in zip((arched or {}).get("groups", ()), grouped):
        at = [j for o in ops for j, x in enumerate(openings) if x is o]
        if len(at) != len(ops):
            raise ParamError(f"bays: a bay stands in front of the arched group in bay {g['bay']}")
        g["ops"] = tuple(at)
    if (val("mansard") or {}).get("crown"):
        mansard_roof["crown"] = _mansard_crown(val("mansard")["crown"], mansard_roof, bays, depth, width, eave,
                                               pitch, float(val("eave_overhang_m")))
        cr = mansard_roof["crown"]
        if cr.get("form") == "hip":
            # T-2465: a stack through a hipped crown clears its ridge as a ridge stack does
            co = cr["overhang_m"]
            for c in chimneys:
                if cr["x0"] - co < c["u_m"] < cr["x1"] + co and cr["z0"] - co < -c["v_m"] < cr["z1"] + co \
                        and c["top_m"] < cr["ridge_m"] + 0.6 - 1e-9:
                    raise ParamError(f"chimney at ({c['u_m']}, {c['v_m']}) tops at {c['top_m']} m, under the "
                                     f"hipped crown's ridge {cr['ridge_m']} m + 0.6")
    if ch and ch.get("k15"):
        # T-2466: the K15 kit's head (its sunk panels, corbelled courses and cap) on T-2302's
        # plain stacks, read against the mansard's own covering
        if not mansard or "plan_m" not in ch:
            raise ParamError("chimneys.k15 dresses a mansard's plain stacks (plan_m); a hip's stacks "
                             "name their K15 variant in chimney_positions")
        _k15_heads(ch["k15"], ch["stacks"], chimneys,
                   mansard_cover(mansard_roof, depth, width, eave, pitch, float(val("eave_overhang_m"))))
    if (val("mansard") or {}).get("dormers"):
        mansard_roof["dormers"] = _mansard_dormers(val("mansard")["dormers"], mansard_roof, depth, width, eave,
                                                   float(val("eave_overhang_m")), chimneys)

    wings = _rear_wings(val("rear_wings"), depth, width, openings, cw,
                        opening["parameters"]["clear_height_m"]["range"], (record or {}).get("id", ""))

    stone = _k02(val("stone_front") or {})
    if stone:
        # the rusticated base and its coping run up to the area lights' heads, so the
        # coping's top is the line the lights' flat arches spring from (T-2289)
        top = bsill + float(bl["height_m"]) if bl else float((val("street_front_dress") or sfw or {}).get("base_top_m", 0.0))
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

    # T-2358: the K14 condition kit. Its water trails hang from the K06 sills; a stone front
    # seats them before it cuts its walls, and a brick house reads them off a kit-less build
    # of itself first (T-2364), so either construction may name it
    condition = {}
    cond = val("condition")
    if cond:
        if cond.get("kit") != CONDITION_KIT:
            raise ParamError(f"condition.kit names {cond.get('kit')!r}; the K14 kit is {CONDITION_KIT}")
        built = cond.get("built")
        if not isinstance(built, int) or not 1830 <= built <= 1904:
            raise ParamError(f"condition.built {built!r} is not a completion year standing by 1904")
        # T-2359: the chimney plume lies on a compass bearing, so the kit is read in the
        # house's own frame turned by the placement's rotation (+ clockwise, as buildings.js)
        rotation = float(((phase.get("position") or {}).get("rotation_deg")) or 0.0)
        condition = {"kit": CONDITION_KIT, "built": built, "rotation_deg": rotation}

    from .k01_stone_finish import validate as validate_stone_finish
    stone_finish = validate_stone_finish(dict(val("stone_finish", {}) or {}), width)
    if stone_finish and (roof_form != "flat" or not stone):
        raise ParamError("stone_finish requires a flat roof and a stone front")
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
        yard=yard, stone_finish=stone_finish,
        stone=stone, rear_wings=wings, condition=condition, arched_front=arched,
        roof_form=roof_form, flat=flat_roof, mansard=mansard_roof, gable=gable_roof, shaped_gable=shaped, entrance_floor_m=ef, round_heads=rh,
        wall_paint=paint, street_dress=street_dress, frontispiece=frontispiece, rear_section=rear_section,
        confidence={n: form[n].get("confidence", "reconstructed") for n in names if n in form}
                   | {"footprint": (phase.get("footprint") or {}).get("confidence", "reconstructed")},
    )
    return params
