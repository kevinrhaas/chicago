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
import dataclasses
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
    # T-2866: a light over a door's leaf in the top of its hole (1625's rear section door), 0 for none
    transom_m: float = 0.0
    # T-2884: a side light whose picture shows its head plain (1625's south wall): no K03 head
    # or lintel is drawn over it, and a light narrower than the ordinary sash is one light a sash
    plain: bool = False
    narrow: bool = False
    # T-2960: a ROUND_CUT hole cut segmental at this rise over its span (1736's upper lights,
    # the c. 1890 photograph), which its K06 sash is built to; 0 is the round head
    rise_over_span: float = 0.0

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
    # T-2781: stone belt courses along a side wall, read off a picture — each
    # {"wall", "from_m", "to_m", "proud_m"}, stopped against a bay and a rear wing as the
    # front's belts are; empty for every house whose side walls carry K03's brick course or none
    side_belts: tuple = ()
    # T-3184: a side wall's basement faced in the front's stone up to its water table, read
    # off a picture (1834's north flank); empty where the side walls are brick to grade
    side_base: tuple = ()
    # T-3184: a brick front's iron, read off its picture: balconettes under named street
    # windows and the stoop's rails (1834's), as k01_arched_front lays them on an arched front
    street_iron: dict = field(default_factory=dict)
    roof: dict = field(default_factory=dict)       # T-2293: covering, caps, flashing (K04)
    dormer: dict = field(default_factory=dict)     # T-2293: the front dormer, if any
    # T-2866: dormers on a hip's side and rear slopes (1625's on its open south side), each
    # `_round_dormer`'s numbers with its face, its centre along the slope and how far back
    # its body runs (`back_m`, in from the wall line) to die into the hip
    slope_dormers: tuple = ()
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
    wall_paint_opaque: bool = False
    front_brick_tone: tuple = ()   # T-3093: the street front's brick, tinted apart from the side walls
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
    # T-3006: a corner of the front block rounded from grade, in the front's stone, and
    # corbelled out to the square under the wall head ({"corner", "radius_m"}; 1811's, off
    # the 1888 plate) — empty for every other house, whose corners stand square
    round_corner: dict = field(default_factory=dict)
    # T-3186: a corner of the main body cut on a canted face from grade to the roof, its own
    # window column on it and the cornice and the mansard carried round it ({"corner",
    # "cut_m", "face_m"}; 1901's, off both Chicagology photographs) — empty for every other house
    cant_corner: dict = field(default_factory=dict)
    # T-3112: the street front's low-s end stood as a pier capped under the wall head, a slate
    # weathering over its cap and the eave brought in over it ({"to_m", "band_m", "cap_m",
    # "band_proud_m", "cap_proud_m", "weathering_pitch_deg"}; 1811's, off its three pictures)
    front_pier: dict = field(default_factory=dict)
    # T-3158: a stone street front divided into pavilions — its rusticated quoined piers, the
    # frieze's bed and panels between them, the cornice's modillions and the mansard's ribs over
    # the piers (`street_front_pavilions`, k01_pavilions; 1729's, off the Detroit print)
    pavilions: dict = field(default_factory=dict)
    # T-3160: a one-storey arcaded porte-cochere on a side wall under a balustraded deck
    # (`porte_cochere`, k01_porte_cochere; 1729's on 18th Street, off the Detroit print)
    porte_cochere: dict = field(default_factory=dict)
    # T-1879: open louvred shutters folded back beside named walls' lights, by storey
    # (`window_shutters`; 1721's, off the 1891 plate): {"width_m", "louvre_m", "lights":
    # ((wall, s0, s1, sill, head), ...)} — empty for every other house
    shutters: dict = field(default_factory=dict)
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def on_frontispiece(self, op) -> bool:
        """T-2753: does this street opening stand on the proud frontispiece (laid on its face)?"""
        fp = self.frontispiece
        return bool(fp) and op.wall == "k01.wall.street_front" and \
            op.s_m - op.width_m / 2 >= fp["s_m"] - 1e-6 and op.head_m <= fp["hood"]["bed_m"] + 1e-6

    def entrance_block(self):
        """T-1881: the forward block that carries the entrance on its face, or None."""
        return next((b for b in self.bays if b.get("entrance")), None)

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
    "front_bays_by_storey", "gable_roof", "wall_finish", "street_front_brick", "stone_finish", "shaped_gable",
    "street_front_windows", "street_front_frontispiece", "door_clear_height_m", "side_belts",
    "slope_dormers", "round_corner", "cant_corner", "front_pier", "street_front_pavilions", "porte_cochere",
    "side_base", "street_front_iron", "window_shutters", "flat_balustrade",
})

#: T-2451: a bay's corner strip -> K01 slot: dressed stone, or painted timber on a frame bay
STRIP_FABRICS = {"stone": "dress_stone", "painted_timber": "bay_strip_paint"}

#: T-2410: the component a brick street front's round-headed window is cut as — K06's round
#: sash in a round hole through the K03 wall, under the kit's own arch band as its hood
ROUND_HOODED = "k01.opening.sash_round_hooded"
#: T-2884: a side wall's round-headed light whose picture shows its head plain (1625's lower
#: lights): K06's round sash in the same round hole, under no hood and no brick arch
ROUND_PLAIN = "k01.opening.sash_round_plain"
#: the K01 components whose hole the wall cuts round over the spring
ROUND_CUT = (ROUND_HOODED, ROUND_PLAIN)
ROUND_HEAD_HOOD = "k09.trim.lintel_cornice_hood"   # T-2960: the hood street_front_round_heads may name
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
    gk, pk = rain.get("gutter"), rain.get("downpipe")
    g, d = prof["gutter"], prof["downpipe"]
    # T-2919: a gable roof hangs no gutter yet, but its front may carry pipes down from
    # rainwater heads of their own (T-2953's front_pipes; 1811's plate draws two)
    gable_pipes = gable and bool(rain)
    if gable_pipes:
        if set(rain) != {"fabric", "downpipe", "ends_at", "front_pipes"} or not rain["front_pipes"]:
            raise ParamError("a gable K01 roof's rainwater is front_pipes alone, from heads of their own: "
                             "fabric, downpipe, ends_at and front_pipes (no gutter, no downpipes)")
    elif flat or gable:     # T-2459: a gable roof hangs no gutter yet (from_phase refuses one)
        return roof, {}
    if gable_pipes:
        gk = "half_round"   # no gutter is hung; its kind only keys the K04 fabrics a pipe may be
    elif gk != "half_round":
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
    if not pipes and not gable_pipes:
        raise ParamError("every gutter outlet leads to a pipe: rainwater.downpipes is empty")
    # T-2953: a pipe down the street front from a rainwater head of its own, where no eave gutter
    # runs to it (1812's shaped gable, its pipes at both ends of the front in the Levy print):
    # `s_m` along the front from the south corner, the head's top `head_m` over grade, standing
    # `proud_m` before the main front (a projection's face), down to `foot_m` (0: grade, its shoe
    # over a splash stone; else a lower roof it discharges onto)
    # T-2997: or (`on: "return"`) down a street projection's square high-s return, its own face
    # (1811's bay on its 1888 plate): `s_m` is then the return's face, `proud_m` where along it
    # the pipe stands before the main front, and the pipe, head, straps and shoe turn to that
    # face; from_phase holds it to a projection's return
    front = []
    for x in rain.get("front_pipes", []):
        if set(x) - {"on"} != {"s_m", "head_m", "foot_m", "proud_m"} or x.get("on", "front") not in ("front", "return"):
            raise ParamError("rainwater.front_pipes take s_m, head_m, foot_m and proud_m (and on: front or return)")
        q = {k: float(x[k]) for k in ("s_m", "head_m", "foot_m", "proud_m")}
        if x.get("on") == "return":
            if not 0.15 <= q["proud_m"] <= 2.0:
                raise ParamError(f"rainwater.front_pipes {x}: a pipe on a return stands 0.15-2 m before the front")
            q["on"] = "return"
        # T-3006: a pipe on a rounded corner stands behind the front's plane, round the
        # curve; from_phase holds it clear of the round's face (_round_corner)
        if not -1.5 <= q["proud_m"] <= 2.0 or not 0.0 <= q["foot_m"] <= q["head_m"] - 0.5 or q["head_m"] > 20.0:
            raise ParamError(f"rainwater.front_pipes {x}: a head at most 20 m up, at least 0.5 m over its foot, "
                             f"standing 0-2 m before the front")
        front.append(q)
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
        **({"front_pipes": front} if front else {}),
    }
    return roof, rainwater

# T-2308: the K08 kinds a K01 frontage can carry. A bay or a full-height projection
# stands on grade against one wall under its own roof. T-2369: an oriel stands on its corbel
# courses and stops under the main eave, its own roof leaning on the wall below the
# cornice (1612's south wall), so it is carried too. T-2787: a tower stands on grade and
# rises PAST the main eave, its cap whole over the main roof; the roof is not cut for it,
# so its ring closes round the eave and its back is closed in the wall's plane above it.
BAY_KINDS = ("bay", "projection", "oriel", "tower")
#: T-2787: how far a tower's wall top stands over the main eave at the least. Under that
#: it is a bay with a cone on it, and the eave would run into its cap
TOWER_PAST_EAVE_M = 1.0
#: T-2900: how far inside its end wall's plane a corner turret's ring may stand, at the most
TURRET_CORNER_M = 0.3
SHALLOW_PROUD_M = 0.3   # T-3047: a shallow projection stands at most this far proud
CHAMFER_BEHIND_M = 0.6  # T-3048: and its chamfer runs back at most this far behind the wall's face
CHAMFER_ALONG_M = 1.0   # ...and at most this far (and a quarter of its width) along its front
# T-3108: a chamfer a round bay stands on (`on_chamfer`, 1801's south-west corner on HABS
# photograph 1 and its 1911 sheet: the corner cut back about 1.0-1.4 m over about 2 m) may run
# this far along the front (and at most half the pavilion's width) and this far behind it
ROUND_CHAMFER_ALONG_M = 2.0
ROUND_CHAMFER_BEHIND_M = 1.6

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
def _flat_balustrade(fb: dict, flat_roof: dict, width: float, eave: float) -> dict:
    """T-1879: the blocking course pierced as a balustrade over a stretch of the street front
    (1721's recessed front, the 1891 plate): from `from_s_m` to `to_s_m` along the front the
    course stops at a coped plinth `plinth_m` over the wall head, square balusters `bar_m` thick
    every `pitch_m` stand on it, and a rail `rail_m` deep runs under the course's top between
    the solid lengths either side, which stand as its pedestals."""
    if not flat_roof:
        raise ParamError("flat_balustrade pierces a flat roof's blocking course (roof_form flat)")
    need = {"from_s_m", "to_s_m", "plinth_m", "rail_m", "bar_m", "pitch_m"}
    if set(fb) != need:
        raise ParamError(f"flat_balustrade takes {sorted(need)}")
    b = {k: float(fb[k]) for k in sorted(need)}
    rise = flat_roof["parapet_top_m"] - eave
    if not 0.0 <= b["from_s_m"] < b["to_s_m"] <= width or b["to_s_m"] - b["from_s_m"] < 1.0 \
            or not 0.1 <= b["plinth_m"] <= 0.4 or not 0.1 <= b["rail_m"] <= 0.25 \
            or not 0.06 <= b["bar_m"] <= 0.15 or not 1.5 * b["bar_m"] <= b["pitch_m"] <= 0.35 \
            or rise - b["plinth_m"] - flat_roof["coping_m"] - b["rail_m"] < 0.3:
        raise ParamError(f"flat_balustrade {b}: at least 1 m of the {width} m front, a 0.1-0.4 m plinth and "
                         f"a 0.1-0.25 m rail leaving 0.3 m of balusters in the course's {rise:.2f} m, bars "
                         f"0.06-0.15 m at 1.5 bars' pitch to 0.35 m")
    return b


#: T-2459: the parapet lines a K01 gable roof's side walls are carried up in
GABLE_PARAPETS = ("stepped", "coped")


def _gable_top_half() -> float:
    """The parapet's level head either side of the ridge (k01_gable_roof.TOP_HALF_M)."""
    from . import k01_gable_roof
    return k01_gable_roof.TOP_HALF_M


def _gable_roof(g: dict, depth: float, width: float, eave: float, pitch: float, side_wall: float,
                overhang: float = 0.0) -> dict:
    """The numbers a K01 gable roof is built to (T-2459): the ridge runs along the street
    front `ridge_back_m` behind the front wall's plane, the street slope rises to it at
    roof_pitch_deg from the front eave, and the rear slope falls from it to the rear wall's
    head at whatever pitch that leaves, so both eaves stand on the one wall head. Each side
    wall is carried up as a parapet the wall's own thickness (`ends`: K01's `north` is the
    high-v wall, `south` the low-v one), either `stepped` (crow steps, `steps` a slope, each
    clearing the covering behind it by K05's upstand and carrying its own coping) or `coped`
    (one coping following the slopes at that clearance); both stand `top_above_ridge_m` over
    the ridge at their head.

    T-3050: `hip_mass` stands a steeper HIPPED MASS over the low-v end of the front block
    (1811's, its 1888 plate: a tall hipped roof over the bay, the lower gable roof running on
    to the tall stack): a K05 hip over the whole depth from v 0 to `v_m`, its street and rear
    faces at roof_pitch_deg from the same eave, so its street face is the gable's own street
    plane; `apex_v_m`, where a picture puts its apex, pitches its two end faces to it. The gable's attic
    then starts at `attic_from_m`, inside the hip's south face, and only the high-v (`north`)
    wall is carried up as a parapet: the low-v wall is under the hip's end.

    T-3063: `rear_fall` lets the rear slope fall steeply from the ridge, at its `pitch_deg`,
    to a FLAT DECK that runs to the rear wall, and the coped parapet over it fall with it to a
    LEVEL wall head, its coping's top at `wall_head_m`, the deck K05's upstand under the
    parapet's slab (1811's south
    wall behind its tall stack: both its pictures draw the coping level at about 10.95 m from
    just behind the stack to the block's rear wall, with no roof showing over it, where a rear
    slope falling to the rear eave stands it 0.5-1.4 m higher there). `head_back_m` is how far
    the parapet's level head runs on behind the ridge before it falls. Coped ends only."""
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
    hm = g.get("hip_mass")
    if hm and set(ends) != {"north"}:
        raise ParamError("gable_roof.ends: under a hip_mass only the north (high-v) wall is a parapet")
    if not hm and set(ends) != {"north", "south"}:
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
    fall = {}
    rf = g.get("rear_fall")
    if rf:
        if any(e["style"] != "coped" for e in out.values()):
            raise ParamError("gable_roof.rear_fall: only a coped parapet runs level over a deck")
        head, fp = float(rf["wall_head_m"]), float(rf["pitch_deg"])
        # how far the parapet's level head runs on behind the ridge before it falls (the
        # coped head's own half, unless a picture sees the fall start nearer the ridge)
        hb = float(rf.get("head_back_m", _gable_top_half()))
        if not 0.05 <= hb <= _gable_top_half():
            raise ParamError(f"gable_roof.rear_fall.head_back_m {hb}: 0.05-{_gable_top_half()} m")
        if not back_deg + 15.0 <= fp <= 75.0:
            raise ParamError(f"gable_roof.rear_fall.pitch_deg {fp}: from the plain rear slope's "
                             f"{back_deg:.1f} + 15 to 75 deg")
        # the wall head is the coping's top, as a picture reads it; the parapet's slab stops a
        # coping under it, and the deck K05's least upstand under that
        up, ridge = float(pp["upstand_min_m"]), eave + rise
        deck = head - float(cp["thickness_m"]) - up
        run = (ridge - deck) / math.tan(math.radians(fp))
        # the deck stands over the front eave and under the ridge, and the fall is long enough
        # that the parapet's level head over the ridge stays over the covering behind it
        if not (eave + 0.5 <= deck and run >= hb + 0.05 and run <= depth - r - 1.0):
            raise ParamError(f"gable_roof.rear_fall.wall_head_m {head}: its deck {deck:.3f} m must stand "
                             f"0.5 m over the eave {eave} and fall from the ridge {ridge:.3f} m over "
                             f"{hb + 0.05:.2f} m to 1 m short of the rear wall (it falls {run:.2f})")
        fall = {"rear_fall": {"wall_head_m": head, "pitch_deg": fp, "head_back_m": hb, "deck_m": round(deck, 4),
                              "deck_from_m": round(depth - r - run, 4)}}
    hip = {}
    if hm:
        vm, va = float(hm["v_m"]), float(hm["attic_from_m"])
        if not 2.0 <= vm <= width - 1.0:
            raise ParamError(f"gable_roof.hip_mass.v_m {vm}: 2 m to 1 m short of the width {width}")
        he = eave - overhang * tf
        rise_h = (depth / 2 + overhang) * tf      # the street and rear faces at the street's pitch
        apex = he + rise_h
        # the apex's place along the front (`apex_v_m`, read off a picture) sets the two end
        # faces' pitches; without it they take the street's, and the ridge is centred
        av = hm.get("apex_v_m")
        if av is None:
            if vm < depth:
                raise ParamError("gable_roof.hip_mass narrower than the depth names its apex_v_m")
            tn = ts = tf
        else:
            av = float(av)
            tn, ts = rise_h / (av + overhang), rise_h / (vm + overhang - av)
            for side, t_ in (("south", tn), ("north", ts)):
                if not 45.0 <= math.degrees(math.atan(t_)) <= 70.0:
                    raise ParamError(f"gable_roof.hip_mass.apex_v_m {av}: the {side} end face falls at "
                                     f"{math.degrees(math.atan(t_)):.1f} deg, outside 45-70")
        ridge = eave + rise
        # the attic's end stands inside the hip: under its south face and its north one
        if not (he + (va + overhang) * tn >= ridge + 0.05 and he + (vm + overhang - va) * ts >= ridge + 0.05):
            raise ParamError(f"gable_roof.hip_mass.attic_from_m {va}: the attic's end must stand inside "
                             f"the hip, under both its end faces, at the ridge {ridge:.3f} m")
        if apex < ridge + 0.5:
            raise ParamError(f"gable_roof.hip_mass: its apex {apex:.3f} m stands under the ridge + 0.5")
        hip = {"hip_mass": {"v_m": vm, "attic_from_m": va, "apex_m": round(apex, 4),
                            "apex_v_m": av, "end_pitch_deg": {"south": round(math.degrees(math.atan(tn)), 4),
                                                             "north": round(math.degrees(math.atan(ts)), 4)}}}
    return {"ridge_back_m": r, "ridge_m": round(eave + rise, 4), "back_pitch_deg": round(back_deg, 4),
            **hip, **fall, "ends": out, "parapet_m": side_wall, "upstand_m": float(pp["upstand_min_m"]),
            "top_above_ridge_m": top, "coping_m": float(cp["thickness_m"]), "drip_m": float(cp["drip_m"])}


#: T-2370: the K05 mansard variants a K01 roof may be built from (k05_roofs.json)
MANSARD_ROOFS = ("k05.roof.mansard_convex", "k05.roof.mansard_concave")


def _mansard_roof(m: dict, depth: float, width: float, eave: float, pitch: float, overhang: float,
                  shaped: bool = False, side_wall: float = 0.0) -> dict:
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
    # T-2843: a face may hold two storeys — the house's top storey and its attic over it, as
    # 1801's steep slate faces do in the Taylor photograph, cornice 8.1 m to deck about 17 m —
    # and says so (`storeys: 2`); it then rises 4.5-7.5 m. One storey is the default and the
    # attic storey's 2.0-4.5 m
    held = m.get("storeys", 1)
    if held not in (1, 2):
        raise ParamError(f"mansard.storeys {held!r}: a face holds 1 storey (an attic) or 2")
    lo, hi = (2.0, 4.5) if held == 1 else (4.5, 7.5)
    if not lo <= rise <= hi:
        raise ParamError(f"mansard.lower_rise_m {rise}: a face holding {held} storey(s) rises {lo}-{hi} m")
    # T-3033: behind a shaped gable the side walls run up plain under the gable's own shallow
    # eave (1812 Prairie's, 0.05 m), so the mansard's cornice may be as shallow as that eave
    lo = 0.05 if shaped else 0.3
    if not lo <= overhang <= 1.0:
        raise ParamError(f"eave_overhang_m {overhang}: a mansard's cornice projects {lo}-1.0 m"
                         + (" behind a shaped gable" if shaped else ""))
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
    out = {"variant": vid, "profile": v["profile"], "lower_pitch_deg": lower, "bulge": bulge,
           "segments": int(v["segments"]) if bulge > 0 else 1, "lower_rise_m": rise, "fascia_m": f,
           "curb_m": round(eave + rise, 4), "ridge_m": round(ridge, 4)}
    if m.get("side_parapet"):
        out["side_parapet"] = _mansard_side_parapet(m["side_parapet"], k5, out, eave, overhang, side_wall)
    # T-1881: the lower faces' dormers may be faced in the front's own stone (1729's read in the
    # walls' tone in every photograph), where K01's are a pale dressed stone
    if "dormer_fabric" in m:
        if m["dormer_fabric"] != "front_stone":
            raise ParamError(f"mansard.dormer_fabric {m['dormer_fabric']!r}: front_stone, or leave it out")
        out["dormer_fabric"] = "front_stone"
    return out


#: T-3061: the side walls a mansard's wall may be carried up past its curb from
MANSARD_PARAPET_WALLS = ("south", "north")


def _mansard_side_parapet(sp: dict, k5: dict, m: dict, eave: float, overhang: float, side_wall: float) -> dict:
    """T-3061: a side wall carried up past the mansard's curb as a coped parapet — 1812
    Prairie's south wall, Levy's print and the c. 1955 photograph: the slate face behind the
    gable's shoulder ends in the wall's end, which rises from the slate's foot to a heavy level
    cap over the curb. The parapet is the side wall's own thickness, from the rear wall's plane
    to the front's, its coping's top at `top_m` and `coping_m` deep; the lower face behind it
    is the mansard's own, dying into its inner face. Its top stands no lower than the curb, so
    nothing of the face shows over it from the street, and clears the face where the face
    meets its inner side by K05's upstand."""
    if set(sp) - {"wall", "top_m", "coping_m"} or not {"wall", "top_m"} <= set(sp):
        raise ParamError("mansard.side_parapet takes wall, top_m and optionally coping_m")
    if sp["wall"] not in MANSARD_PARAPET_WALLS:
        raise ParamError(f"mansard.side_parapet.wall {sp['wall']!r}: one of {', '.join(MANSARD_PARAPET_WALLS)}")
    pp, cp = k5["parts"]["parapet"], k5["parts"]["coping"]
    curb = m["curb_m"]
    top, cop = float(sp["top_m"]), float(sp.get("coping_m", cp["thickness_m"]))
    if not cp["thickness_m"] <= cop <= 0.3:
        raise ParamError(f"mansard.side_parapet.coping_m {cop}: {cp['thickness_m']}-0.3 m")
    if not curb - 1e-9 <= top <= curb + 1.5:
        raise ParamError(f"mansard.side_parapet.top_m {top}: from the curb's {curb} m to 1.5 m over it")
    if side_wall <= 0.0:
        raise ParamError("mansard.side_parapet: the side wall's thickness is the parapet's")
    # where the lower face crosses the parapet's inner side, the fascia's face `overhang` out
    meet = eave + mansard_face_height(overhang + side_wall, m["lower_rise_m"], m["lower_pitch_deg"], m["bulge"],
                                      m["profile"])
    if top - cop < meet + float(pp["upstand_min_m"]) - 1e-9:
        raise ParamError(f"mansard.side_parapet.top_m {top}: its slab's top clears the lower face at its "
                         f"inner side ({meet:.3f} m) by less than {pp['upstand_min_m']} m")
    return {"wall": sp["wall"], "top_m": top, "coping_m": cop, "drip_m": float(cp["drip_m"]),
            "thickness_m": side_wall}


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
    # T-3197: a hipped crown over an attic has its eave a storey over the main one, so the
    # two fascias never meet on a corner, and it stands as little past the pavilion as its
    # picture draws (1827's, about at the pavilion's sides in the Doane photograph)
    if c.get("form") == "hip" and float(c.get("attic_m", 0.0)) and 0.1 <= co <= overhang + 0.5:
        pass
    elif not overhang < co <= overhang + 0.5:
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
    # T-3156: the pavilion may be carried up an ATTIC storey past the main eave (1815's, its
    # paired lights in the wall between the main cornice and its own eave), the crown's fascia
    # then standing `attic_m` over the main eave's; the main eave box stops square at the
    # pavilion's cheeks under the crown, as at a shallow pavilion's (k01_frontage.shallow_bay_cutters)
    # T-3175: or the whole mansard storey (1827's, the Doane photograph: its attic of three
    # lights rises from the main cornice to the main curb's height, about 4.2 m)
    attic = float(c.get("attic_m", 0.0))
    if attic and not 1.0 <= attic <= 4.5:
        raise ParamError(f"mansard.crown.attic_m {attic}: 1-4.5 m")
    E = eave + attic
    # the pavilion is carried up to the crown's soffit, its own eaves and deck inside the crown
    soffit = E - float(k5["parts"]["eave"]["fascia_depth_m"])
    top = sum(float(st["height_m"]) for st in bay["variant"]["storeys"])
    if not soffit <= top <= soffit + 0.1:
        raise ParamError(f"mansard.crown: {bay['id']} stops at {top:.3f} m; under a hipped crown it rises "
                         f"to the crown's soffit at {soffit:.3f} m, and at most 0.1 m into it")
    half = w / 2 + co
    rise = half * math.tan(math.radians(side))
    x1 = depth + proud
    apex = x1 + co - rise / math.tan(math.radians(end))
    if attic + rise < m["lower_rise_m"] + 0.3:
        raise ParamError(f"mansard.crown: its ridge {attic + rise:.2f} m over the eave is not 0.3 m over the main "
                         f"curb's {m['lower_rise_m']} m")
    # where the end reaches the main curb's height it stands in front of that curb
    curb = depth + overhang - m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
    at_curb = x1 + co - max(m["lower_rise_m"] - attic, 0.0) / math.tan(math.radians(end))
    if at_curb < curb + 0.2:
        raise ParamError(f"mansard.crown: its end meets the main curb's height at x {at_curb:.2f}, not 0.2 m "
                         f"in front of the curb at {curb:.2f}; steepen end_pitch_deg")
    back = x1 - cd - co + rise / math.tan(math.radians(side))
    if back > apex - 0.5:
        raise ParamError(f"mansard.crown.depth_m {cd}: its ridge would run {apex - back:.2f} m, under 0.5")
    # T-3175: and a turned iron finial on the ridge's street end (1827's, over its pavilion in
    # the Doane photograph), the deck's turning (k01_mansard_deck) at the same bounds
    fn = c.get("finial")
    if fn is not None:
        if set(fn) != {"height_m", "radius_m"} or not 0.8 <= float(fn["height_m"]) <= 3.0 \
                or not 0.05 <= float(fn["radius_m"]) <= 0.2:
            raise ParamError("mansard.crown.finial: height_m 0.8-3.0 m and radius_m 0.05-0.2 m")
        fn = {"height_m": float(fn["height_m"]), "radius_m": float(fn["radius_m"])}
    return {"over_bay": bay["id"], "form": "hip", "x0": round(x1 - cd, 4), "x1": round(x1, 4),
            "z0": round(-b, 4), "z1": round(-a, 4), "pitch_deg": side, "end_pitch_deg": end,
            "overhang_m": co, "ridge_m": round(E + rise, 4),
            "ridge_x_m": (round(back, 4), round(apex, 4)),
            **({"attic_m": attic, "eave_m": round(E, 4)} if attic else {}),
            **({"finial": fn} if fn else {})}


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
                y = max(y, cr.get("eave_m", eave) + min((u - X0) * ts, (X1 - u) * te, (z - Z0) * ts, (Z1 - z) * ts))
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
    # T-2782: a clay pot on every flue, one of the kit's profiles, where the house's picture
    # draws a crown over each cap (1637's engraving); the record's top stays the cap's
    pot = k.get("pot")
    if pot is not None and pot not in kit["pot"]["profiles"]:
        raise ParamError(f"chimneys.k15.pot {pot!r} is not one of the kit's pot profiles "
                         f"{sorted(kit['pot']['profiles'])}")
    for st_, c in zip(stacks, chimneys):
        sx, sz = c["plan_m"]
        u, v, top = c["u_m"], c["v_m"], c["top_m"]
        if sz / max(nfl, 1) < fo + 0.1:
            raise ParamError(f"chimney at ({u}, {v}): {nfl} flues of {fo} m do not fit its {sz} m face")
        spec = {key: copy.deepcopy(x) for key, x in base.items()
                if key not in ("x", "z", "width_m", "depth_m", "top_m", "flues", "panels") and key not in omit}
        spec.update(width_m=sz, depth_m=sx, across="z", top_m=top,
                    flues=[{"at": round((i + 0.5) * sz / nfl - sz / 2, 4), **({"pot": pot} if pot else {})}
                           for i in range(nfl)])
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


#: T-1890: the sheet metals a K08 cap's finial may be laid in, each a K01 slot (the default,
#: no fabric named, is the cap's own covering)
FINIAL_FABRICS = {"zinc_sheet": "k04_zinc_sheet"}


def tympanum_spec(ty, what: str, lintel_proud: float) -> dict:
    """T-3197: a carved tympanum on a light's lintel (1827's, from the Doane photograph;
    k08_bays.tympanum builds it): a panel springing `spring_m` (0-0.6 m) over the lintel and
    rising `rise_m` (0-0.6 m, 0 a level top) at its crown, `proud_m` out, under a hood band
    `band_m` deep and `band_proud_m` out (prouder than the panel, no prouder than the lintel
    it stands on), its leaves `relief_m` proud of the panel; `span_m` (optional) names one
    arc over a group, centred on the run, whose part over each light is that light's."""
    need, opt = {"spring_m", "rise_m", "proud_m", "band_m", "band_proud_m", "relief_m"}, {"span_m"}
    if not isinstance(ty, dict) or not need <= set(ty) <= need | opt:
        raise ParamError(f"{what} takes {sorted(need)} and optionally span_m, not {ty}")
    t = {k: float(ty[k]) for k in sorted(ty)}
    if not (0.0 <= t["spring_m"] <= 0.6 and 0.0 <= t["rise_m"] <= 0.6 and 0.02 <= t["proud_m"] <= 0.1
            and 0.04 <= t["band_m"] <= 0.2 and t["proud_m"] < t["band_proud_m"] <= lintel_proud
            and 0.01 <= t["relief_m"] <= 0.05 and 0.1 <= t["spring_m"] + t["rise_m"]
            and ("span_m" not in t or 1.0 <= t["span_m"] <= 8.0)):
        raise ParamError(f"{what}: spring_m and rise_m 0-0.6 m (together at least 0.1), proud_m 0.02-0.1 m, "
                         f"band_m 0.04-0.2 m, band_proud_m prouder than the panel and at most the lintel's "
                         f"{lintel_proud} m, relief_m 0.01-0.05 m, span_m 1-8 m; not {ty}")
    return t


#: T-2452: a lower-face dormer's head — the sash's own arch carried out by the surround
#: (T-2404, T-2411), or a pitched gable over a square-headed sash — and the K06 head each takes.
#: T-2866: or a hipped roof of its own over the face's square head (1625's south dormer).
#: T-2902: or a FLAT hood — the face carried `frieze_m` over the sash's head to a projecting
#: cornice, the kit's dormer eaves, under a cap falling `hood_fall_deg` (1625's rear section)
#: T-3000: or a HOOD — a short face under a shelf, and over the shelf a tall slated hood with
#: upright cheeks, its front falling back to a level top the lower face swallows (1801's)
DORMER_HEADS = {"round": "round", "gable": "flat", "hip": "flat", "flat": "flat", "hood": "flat"}
#: the heads whose eaves are K05's hip over the face's square wall head
HIPPED_HEADS = ("hip", "flat")


def _round_dormer(d: dict, what: str, room: float, hip: bool = False, hood: bool = False) -> dict:
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
    if head in HIPPED_HEADS and not hip:
        raise ParamError(f"{what}.head {head!r}: a dormer under its own eaves stands on a hip's slope "
                         f"(slope_dormers) or a rear section's attic")
    if head == "hood" and not hood:
        raise ParamError(f"{what}.head 'hood': a hooded dormer stands on the main mansard's lower faces")
    if kit.get(sh.get("variant"), {}).get("head") != DORMER_HEADS[head]:
        raise ParamError(f"{what}.sash.variant: a {DORMER_HEADS[head]}-headed K06 variant under a {head} head")
    sw, sht, sill = float(sh["width_m"]), float(sh["height_m"]), float(sh["sill_m"])
    ring, sb = float(d["surround_m"]), float(d["face_setback_m"])
    if not 0.1 <= ring <= 0.4 or not 0.0 < sb < room:
        raise ParamError(f"{what}: a 0.1-0.4 m surround, its face on the lower face")
    # T-3000: a hood's light is the short one at its foot (1801's read about 0.9 m)
    low = 0.6 if head == "hood" else 1.0
    if not 0.5 <= sw <= 1.2 or not low <= sht <= 2.4 or not 0.1 <= sill <= 0.6:
        raise ParamError(f"{what}.sash: 0.5-1.2 m wide, {low}-2.4 m high, on a 0.1-0.6 m sill")
    out = {"variant": sh["variant"], "head": head, "sash_width_m": sw, "sash_height_m": sht, "sill_m": sill,
           "surround_m": ring, "face_setback_m": sb, "width_m": round(sw + 2 * ring, 4),
           "head_m": round(sht + ring, 4)}
    if head == "gable":
        gp = float(d["gable_pitch_deg"])
        if not 30.0 <= gp <= 60.0:
            raise ParamError(f"{what}.gable_pitch_deg {gp}: a dormer's pediment is pitched 30-60 deg")
        out["gable_pitch_deg"] = gp
        out["head_m"] = round(sht + ring + (sw / 2 + ring) * math.tan(math.radians(gp)), 4)
    if head == "hip":
        # T-2866: the face's wall head stands `surround_m` over the sash, as its jambs do; the
        # hip over it is K05's (k05_roofs.hip_element), its eaves the kit's dormer overhang
        hp = float(d["hip_pitch_deg"])
        if not 30.0 <= hp <= 60.0:
            raise ParamError(f"{what}.hip_pitch_deg {hp}: a dormer's hip is pitched 30-60 deg")
        out["hip_pitch_deg"] = hp
    if head == "hood":
        # T-3000: the face's wall head `surround_m` over the sash, then a shelf `shelf_m` deep
        # standing `shelf_proud_m` out of the face, then the hood: `rise_m` of slated front
        # whose top falls `lean_m` back toward the roof, each cheek leaning `taper_m` in
        hd = d.get("hood") or {}
        try:
            sf, sp, hr, ln, tp_ = (float(hd[k]) for k in ("shelf_m", "shelf_proud_m", "rise_m", "lean_m", "taper_m"))
        except KeyError as e:
            raise ParamError(f"{what}.hood names shelf_m, shelf_proud_m, rise_m, lean_m and taper_m ({e} missing)")
        if not 0.08 <= sf <= 0.3 or not 0.0 <= sp <= 0.2:
            raise ParamError(f"{what}.hood: a 0.08-0.3 m shelf standing 0-0.2 m out of the face")
        if not 0.5 <= hr <= 4.0 or not 0.0 <= ln <= hr / 2:
            raise ParamError(f"{what}.hood: a 0.5-4.0 m hood whose top falls back no more than half its rise")
        if not 0.0 <= tp_ <= (sw / 2 + ring) - 0.15:
            raise ParamError(f"{what}.hood.taper_m {tp_}: each cheek leans in 0 m up to 0.15 m short of the middle")
        out["hood"] = {"shelf_m": sf, "shelf_proud_m": sp, "rise_m": hr, "lean_m": ln, "taper_m": tp_}
        # T-1890: the hood's foot may FLARE, standing `flare_m` wider than the face each side and
        # as far out in front of it, the shelf under it with it, and sweeping in to the top the
        # taper and lean set (1801's, wider at their feet than the faces under them in HABS 1)
        if "flare_m" in hd:
            fl = float(hd["flare_m"])
            if not 0.05 <= fl <= 0.3:
                raise ParamError(f"{what}.hood.flare_m {fl}: a hood's foot flares 0.05-0.3 m past its face")
            out["hood"]["flare_m"] = fl
        # T-1890: the face under the shelf may be SLATED as the hood is, its light in a pale
        # stone frame `frame_m` wide inside the surround (1801's, in the Taylor print and HABS 1)
        if hd.get("face", "stone") not in ("stone", "slate"):
            raise ParamError(f"{what}.hood.face {hd['face']!r}: stone or slate")
        if hd.get("face") == "slate":
            fm = float(hd.get("frame_m", 0.0))
            if not 0.05 <= fm <= ring - 0.05:
                raise ParamError(f"{what}.hood.frame_m {fm}: a slated face's frame is 0.05 m wide up to "
                                 f"0.05 m short of its surround ({ring} m)")
            out["hood"].update(face="slate", frame_m=fm)
        elif "frame_m" in hd:
            raise ParamError(f"{what}.hood.frame_m: a frame stands in a slated face only")
        out["head_m"] = round(sht + ring + sf + hr, 4)
    if "eared_hood" in d:
        # T-1881: an eared architrave and hood round a round head's face (1729's dormers in the
        # 1890 Albertype, the Detroit print and Taylor's photograph no. 1445)
        eh = d["eared_hood"]
        if head != "round":
            raise ParamError(f"{what}.eared_hood: on a round head")
        eh = {k: float(v) for k, v in eh.items()}
        if set(d["eared_hood"]) - {"rise_m"} != {"band_m", "proud_m", "ear_m", "drop_m"}:
            raise ParamError(f"{what}.eared_hood takes band_m, proud_m, ear_m, drop_m and an optional rise_m")
        eh.setdefault("rise_m", 0.0)
        ro, ri = sw / 2 + ring + eh["band_m"], sw / 2 + ring - 0.05
        if not (0.08 <= eh["band_m"] <= 0.3 and 0.02 <= eh["proud_m"] <= 0.15 and 0.05 <= eh["ear_m"] <= 0.3
                and 0.1 <= eh["drop_m"] <= 0.5):
            raise ParamError(f"{what}.eared_hood: a 0.08-0.3 m band 0.02-0.15 m proud, its ears 0.05-0.3 m out "
                             f"and 0.1-0.5 m deep")
        # the ears stand `rise_m` over the springing, where the hood's arc is still outside the face
        if not 0.0 <= eh["rise_m"] <= math.sqrt(max(0.0, ro * ro - (ri + 0.05) ** 2)):
            raise ParamError(f"{what}.eared_hood.rise_m {eh['rise_m']}: the ears stand 0 m over the springing up "
                             f"to where the hood's arc meets the face")
        out["eared_hood"] = eh
    if head == "flat":
        # T-2902: the face's wall head `frieze_m` over the sash (a frieze under the cornice, where
        # the surround's ring is only its jambs'), the cap K05's hip at a flat's fall
        fz, fall = float(d["frieze_m"]), float(d["hood_fall_deg"])
        if not 0.1 <= fz <= 0.6:
            raise ParamError(f"{what}.frieze_m {fz}: a flat hood's frieze stands 0.1-0.6 m over the sash")
        if not 2.0 <= fall <= 15.0:
            raise ParamError(f"{what}.hood_fall_deg {fall}: a flat hood's cap falls 2-15 deg")
        out.update(frieze_m=fz, hood_fall_deg=fall, hip_pitch_deg=fall, head_m=round(sht + fz, 4))
    return out


#: T-2866: the hip's side slopes a dormer may stand on (the K01 frame's north and south walls)
SLOPE_FACES = ("north", "south")


def _slope_dormers(entries, roof_form: str, depth: float, width: float, eave: float, pitch: float,
                   overhang: float, rear_section: dict) -> tuple:
    """T-2866: dormers on a hip's side slopes — 1625's on its open south side (K01's north),
    which the McBirney photograph shows over the side wall's eave. Each is a lower-face
    dormer (`_round_dormer`) with its face `face_setback_m` in from the fascia's face, so its
    foot is where it leaves the covering; `along_m` is its centre in u (rear wall 0, street
    front `depth`). Its body runs back into the hip (`back_m`, in from the wall line) until
    its top, and a hipped head's ridge, are inside the main roof, and never so far that it
    stands out of the slope behind the ridge."""
    if not entries:
        return ()
    if roof_form != "hip":
        raise ParamError("slope_dormers stand on a hip's side slopes: a K01 hip roof only")
    dp = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())["parts"]["dormer"]
    do, df = float(dp["overhang_m"]), float(dp["fascia_depth_m"])
    tp = math.tan(math.radians(pitch))
    half = width / 2
    ridge = eave + half * tp
    out = []
    for i, e in enumerate(entries):
        what = f"slope_dormers[{i}]"
        face = e.get("face")
        if face not in SLOPE_FACES:
            raise ParamError(f"{what}.face {face!r}: one of {', '.join(SLOPE_FACES)}")
        r_ = _round_dormer(e, what, half, hip=True)
        c, r = float(e["along_m"]), r_["width_m"] / 2
        w0 = r_["face_setback_m"] - overhang          # the face, in from the wall line
        if w0 < 0.05:
            raise ParamError(f"{what}.face_setback_m: its face stands on the slope, at least 0.05 m "
                             f"inside the wall line ({overhang} m of eave)")
        foot = eave + w0 * tp
        top = foot + r_["sill_m"] + r_["head_m"]
        if r_["head"] in HIPPED_HEADS:
            reach = r + do
            high = top + df + reach * math.tan(math.radians(r_["hip_pitch_deg"]))
        else:
            reach, high = r, top
        if high > ridge - 0.1:
            raise ParamError(f"{what}: its top at {high:.2f} m stands within 0.1 m of the hip's ridge at {ridge:.2f} m")
        # back to where its top is inside the near slope; a hipped head's ridge ends `r` short of it
        back = (r if r_["head"] in HIPPED_HEADS else 0.0) + (high - eave) / tp + 0.05
        lowest = top + df if r_["head"] in HIPPED_HEADS else high
        far = eave + (width - back - (do if r_["head"] in HIPPED_HEADS else 0.0)) * tp
        if far < lowest + 0.02:
            raise ParamError(f"{what}: run back {back:.2f} m to bury its top, it stands out of the slope behind the ridge")
        if c - reach < back or c + reach > depth - back:
            raise ParamError(f"{what}.along_m {c}: it stands on the side slope only for "
                             f"{back + reach:.2f}-{depth - back - reach:.2f} m")
        if rear_section and rear_section["side"] == face:
            clear = rear_section["u_m"][1] + rear_section["attic"]["overhang_m"] + 0.3
            if c - reach < clear:
                raise ParamError(f"{what}.along_m {c}: within 0.3 m of the rear section's attic (u {clear - 0.3:.2f})")
        out.append(dict(r_, face=face, along_m=c, foot_m=round(foot, 4), back_m=round(back, 4),
                        overhang_m=do, fascia_m=df, top_m=round(high, 4)))
    return tuple(out)


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
    if "arch" in wg:     # T-2917: the arched recess stands where the voussoirs and the panel would
        if "voussoirs" in wg or "panel" in wg:
            raise ParamError("dormer.wall_gable: an arched gable carries no voussoirs or pediment panel")
        arch, side = _wall_gable_arch(wg["arch"], at, dormer), None
    else:
        arch, vs = None, wg["voussoirs"]
        ring, proud = float(vs["ring_m"]), float(vs["proud_m"])
        if not 0.1 <= ring <= 0.4 or not 0.0 < proud <= 0.08:
            raise ParamError("dormer.wall_gable.voussoirs: a 0.1-0.4 m ring, 0-0.08 m proud")
        side = min(0.6 * ring, *((b - a - sw) / 2 - 0.01 for a, b in zip(at, at[1:])))
        if side < 0.05:
            raise ParamError("dormer.sash.at_m: the wall gable's lights stand too close for their voussoirs")
    if at[-1] + sw / 2 + (side or 0.0) > wd / 2 - 0.05 or at[0] - sw / 2 - (side or 0.0) < -wd / 2 + 0.05:
        raise ParamError("dormer.sash.at_m: a light's voussoirs run off the wall gable's face")
    pn, fn = wg["pinnacles"], wg["finial"]
    pin = {k: float(pn[k]) for k in ("at_m", "shaft_m", "foot_m", "top_m", "cap_m", "spire_m")}
    if pn.get("engage"):
        # T-2937: the shafts TAKE the gable's ends, as 1811 Prairie's 1888 plate draws them: the
        # face's edge stands inside each shaft and its raking cornice, horizontal cornice and K05
        # eave (0.15 m past the face) all die into it, so the rake runs out past the shaft's inner
        # face and nothing of it shows outside the outer one
        if not pin["at_m"] - pin["shaft_m"] / 2 < wd / 2 < pin["at_m"] + pin["shaft_m"] / 2 - 0.15 - 0.02:
            raise ParamError("dormer.wall_gable.pinnacles.engage: each shaft stands across the face's edge "
                             "and 0.17 m past it, so the rake and its eave die into it")
        pin["engage"] = True
    elif pin["at_m"] - pin["shaft_m"] / 2 < wd / 2 + 0.13 + 0.02:
        raise ParamError("dormer.wall_gable.pinnacles: a shaft stands in the face's cornice return")
    if not pin["foot_m"] < 0.0 < dormer["face_height_m"] < pin["top_m"]:
        raise ParamError("dormer.wall_gable.pinnacles: a shaft rises from under the wall head past the face's eave")
    if vm - pin["at_m"] - pin["shaft_m"] / 2 < 0.0 or vm + pin["at_m"] + pin["shaft_m"] / 2 > width:
        raise ParamError("dormer.wall_gable.pinnacles: both shafts stand on the front")
    # T-3051: or each shaft its own head (`heads`, the low-s one first; 1811's 1888 plate carves
    # them apart): its own `top_m`, its spire a `pyramid` (the default, `spire_m` high) or a
    # `dome` (`spire_m` its rise), and over the low one a moulded `block` straddling the rake's
    # foot, `in_m` toward the face's centre, from `foot_m` (over the wall head) `height_m` high.
    # T-3064: a shaft under a block may stop BELOW the face's eave (the plate's north pinnacle
    # stops at a band level with the horizontal cornice), its spire a `scaled_pyramid` or a
    # pyramid rising to the block's foot, so the block takes the eave's end over it
    if "heads" in pn:
        hs = pn["heads"]
        if not isinstance(hs, list) or len(hs) != 2:
            raise ParamError("dormer.wall_gable.pinnacles.heads: one head a shaft, the low-s one first")
        heads = []
        for j, h in enumerate(hs):
            if set(h) - {"top_m", "spire", "spire_m", "block"} \
                    or h.get("spire", "pyramid") not in ("pyramid", "scaled_pyramid", "dome"):
                raise ParamError(f"dormer.wall_gable.pinnacles.heads[{j}] takes top_m, spire (pyramid, "
                                 "scaled_pyramid or dome), spire_m and block")
            hd = {"top_m": float(h.get("top_m", pin["top_m"])), "spire": h.get("spire", "pyramid"),
                  "spire_m": float(h.get("spire_m", pin["spire_m"]))}
            low = hd["top_m"] <= dormer["face_height_m"]
            if not (0.5 if low else dormer["face_height_m"]) < hd["top_m"] <= 4.0 or not 0.1 <= hd["spire_m"] <= 1.2:
                raise ParamError(f"dormer.wall_gable.pinnacles.heads[{j}]: a shaft rises past the face's eave "
                                 "(at most 4 m), or under a block at least 0.5 m over the wall head, under a "
                                 "0.1-1.2 m spire")
            if "block" in h:
                bk = h["block"]
                if set(bk) != {"in_m", "width_m", "foot_m", "height_m"}:
                    raise ParamError(f"dormer.wall_gable.pinnacles.heads[{j}].block takes in_m, width_m, foot_m "
                                     "and height_m")
                b = {k: float(bk[k]) for k in ("in_m", "width_m", "foot_m", "height_m")}
                if not 0.3 <= b["width_m"] <= 1.0 or not 0.4 <= b["height_m"] <= 2.0 \
                        or not 0.0 <= b["in_m"] - b["width_m"] / 2 <= pin["shaft_m"] / 2:
                    raise ParamError(f"dormer.wall_gable.pinnacles.heads[{j}].block: 0.3-1.0 m wide, 0.4-2.0 m "
                                     "high, its outer face over the shaft and inside its centre line")
                hd["block"] = b
            if low:
                # T-3064: the block takes the eave's end, so the shaft's spire must rise to it
                tip = hd["top_m"] + pin["cap_m"] + hd["spire_m"]
                if "block" not in hd or hd["spire"] == "dome" or abs(tip - hd["block"]["foot_m"]) > 0.05:
                    raise ParamError(f"dormer.wall_gable.pinnacles.heads[{j}]: a shaft stops below the face's eave "
                                     "only under a block, its pyramid's tip at the block's foot (within 0.05 m)")
            heads.append(hd)
        pin["heads"] = heads
    finial = {"height_m": float(fn["height_m"]), "radius_m": float(fn["radius_m"])}
    if not 0.2 <= finial["height_m"] <= 1.0 or not 0.04 <= finial["radius_m"] <= 0.2:
        raise ParamError("dormer.wall_gable.finial: 0.2-1.0 m high, 0.04-0.2 m in radius")
    face = wg.get("face_fabric", "dormer_stone")
    if face not in ("dormer_stone", "front_stone"):
        raise ParamError("dormer.wall_gable.face_fabric: dormer_stone (the default) or front_stone")
    if arch:
        out = {"pinnacles": pin, "finial": finial, "arch": arch}
    else:
        pa = wg["panel"]
        panel = {"inset_m": float(pa["inset_m"]), "depth_m": float(pa["depth_m"])}
        if not 0.1 <= panel["inset_m"] <= 0.5 or not 0.02 <= panel["depth_m"] <= dormer["face_thickness_m"] / 2:
            raise ParamError("dormer.wall_gable.panel: a 0.1-0.5 m margin, recessed no deeper than half the face")
        out = {"voussoirs": {"ring_m": ring, "proud_m": proud, "side_m": round(side, 4)},
               "pinnacles": pin, "finial": finial, "panel": panel}
    if face != "dormer_stone":
        out["face_fabric"] = face
    return {"v_m": vm, "sash": dict(dormer["sash"], variant=vid, at_m=at), "wall_gable": out}


def _wall_gable_arch(ar: dict, at: list, dormer: dict) -> dict:
    """T-2917: 1811 Prairie's wall gable, which its 1888 plate draws as ONE GREAT ARCH: a
    round arch whose centre stands `drop_m` under the pediment's foot (the horizontal
    cornice's top, which reads as the lintel over the lights below it), so its ring rises
    from the cornice; its tympanum recessed `depth_m`, holding a row of small round-headed
    lights; and colonnettes standing between and beside the flat-headed lights under the
    cornice, which carry no voussoirs. Every figure here is in the face's own frame: across
    it from its centre, and up from the pediment's foot; that the ring clears the raking
    cornice is the generator's to check, as it knows the cornice."""
    wd, sw = dormer["width_m"], dormer["sash"]["width_m"]
    R, drop, ring = float(ar["radius_m"]), float(ar["drop_m"]), float(ar["ring_m"])
    proud, depth, stones = float(ar["proud_m"]), float(ar["depth_m"]), int(ar["stones"])
    if not 0.5 <= R <= wd / 2 - 0.1 or not 0.0 <= drop < R / 2:
        raise ParamError("dormer.wall_gable.arch: a radius of 0.5 m up to 0.1 m inside the face's half-width, "
                         "its centre under the foot by less than half of it")
    if not 0.08 <= ring <= 0.4 or not 0.0 < proud <= 0.08 or not 0.02 <= depth <= dormer["face_thickness_m"] / 2:
        raise ParamError("dormer.wall_gable.arch: a 0.08-0.4 m ring 0-0.08 m proud, its tympanum recessed "
                         "no deeper than half the face")
    if stones < 5 or stones % 2 == 0:
        raise ParamError("dormer.wall_gable.arch.stones: an odd number, at least five, so one is the crown's")
    lights = []
    for i, q in enumerate(ar["lights"]):
        lt = {k: float(q[k]) for k in ("at_m", "sill_m", "width_m", "height_m")}
        r = lt["width_m"] / 2
        if not 0.15 <= lt["width_m"] <= 0.8 or lt["height_m"] < r + 0.05 or lt["sill_m"] < 0.03:
            raise ParamError(f"dormer.wall_gable.arch.lights[{i}]: 0.15-0.8 m wide, its jambs standing "
                             "0.05 m under its round head, its sill clear of the cornice")
        spring = lt["sill_m"] + lt["height_m"] - r
        edge = [(lt["at_m"] + sg * r, y) for sg in (-1, 1) for y in (lt["sill_m"], spring)]
        edge += [(lt["at_m"] + r * math.cos(math.pi * k / 8), spring + r * math.sin(math.pi * k / 8)) for k in range(9)]
        if any(math.hypot(x, y + drop) > R - 0.05 for x, y in edge):
            raise ParamError(f"dormer.wall_gable.arch.lights[{i}]: stands 0.05 m inside the arch's intrados")
        lights.append(lt)
    lights.sort(key=lambda q: q["at_m"])
    for a, b in zip(lights, lights[1:]):
        if b["at_m"] - b["width_m"] / 2 - a["at_m"] - a["width_m"] / 2 < 0.08:
            raise ParamError("dormer.wall_gable.arch.lights: the tympanum's lights stand 0.08 m apart")
    co = ar["colonnettes"]
    cr = float(co["radius_m"])
    block = cr + 0.03                       # the half-width of a colonnette's base and capital
    cat = sorted(float(x) for x in co["at_m"])
    if not 0.04 <= cr <= 0.12:
        raise ParamError("dormer.wall_gable.arch.colonnettes: 0.04-0.12 m in radius")
    for c in cat:
        if abs(c) + block > wd / 2 - 0.02:
            raise ParamError("dormer.wall_gable.arch.colonnettes: a colonnette stands off the face")
        if any(abs(c - x) < sw / 2 + block for x in at):
            raise ParamError("dormer.wall_gable.arch.colonnettes: a colonnette stands in a light")
    out = {"radius_m": R, "drop_m": drop, "ring_m": ring, "proud_m": proud, "depth_m": depth, "stones": stones,
           "lights": lights, "colonnettes": {"at_m": cat, "radius_m": cr, "block_m": round(block, 4)}}
    if "hood" in ar:   # T-2937: the archivolt's moulded outer order, round the voussoirs' extrados
        hd = {k: float(ar["hood"][k]) for k in ("ring_m", "proud_m")}
        if not 0.05 <= hd["ring_m"] <= 0.25 or not proud < hd["proud_m"] <= 0.15:
            raise ParamError("dormer.wall_gable.arch.hood: a 0.05-0.25 m order standing prouder than the "
                             "voussoirs, at most 0.15 m")
        out["hood"] = hd
    if "crown_light" in ar:   # a round-headed light in the pediment over the arch, on the face's centre
        cl = {k: float(ar["crown_light"][k]) for k in ("sill_m", "width_m", "height_m")}
        if not 0.15 <= cl["width_m"] <= 0.6 or cl["height_m"] < cl["width_m"] / 2 + 0.05:
            raise ParamError("dormer.wall_gable.arch.crown_light: 0.15-0.6 m wide, its jambs standing "
                             "0.05 m under its round head")
        out["crown_light"] = cl
    return out


def _shaped_gable(sg: dict, roof_form: str, dormer: dict, width: float, eave: float, pitch: float,
                  overhang: float, mansard: dict | None = None) -> dict:
    """T-2543: the street front's shaped gable — 1812 Prairie's, which its photograph shows
    standing over the whole front: `profile_m`, the outline's half-width over grade from its
    foot to its apex ([half-width, height] pairs, rising, the last on the centre line); the
    slab's `foot_m` under the wall head, `thickness_m`, and `proud_m` in front of the street
    eave's fascia; a row of K06 `lights` (`variant`, `sill_m` over grade, `width_m`,
    `height_m`, `at_m` from the centre); the `coping` band on the face; a pinnacle
    `kneelers` each side on the ledge where the outline leaves the eave; a `finial`.
    T-2865: an optional `ledge_m` (over grade) stands that ledge higher than the eave, so the
    front carries its full width up past the side walls' eave — 1625 Prairie's corner pier,
    which its photograph stops at about 13 m over a side wall whose eave is 10.9 m.
    T-2730: 1625 Prairie's plain coped WALL GABLE is the same slab with a straight outline:
    its `kneelers` and `finial` may be left out (the ledge alone is the kneeler stone), its
    lights may be segment-headed and stand below the ledge, on the slab under the eave, an
    `oculus` (`centre_m` over grade, `width_m`, `height_m`, a stone `ring_m` `proud_m` and
    its glazing `bars_m`) may light its apex, and `fabric: "front"` dresses the slab in the
    front's stone where 1812's wears the side walls' brick."""
    if not sg:
        return {}
    # T-3033: or before a mansard's street face, as 1812's photographs show its slate faces
    # rising behind the shoulders to a level curb (`mansard`, the resolved roof's numbers)
    if roof_form not in ("hip", "mansard"):
        raise ParamError("shaped_gable: a shaped gable stands in front of a hip's street slope (T-2543) "
                         "or a mansard's street face (T-3033)")
    if dormer:
        raise ParamError("shaped_gable: a front carried up as a shaped gable carries no street dormer")
    pr = [(float(w), float(y)) for w, y in sg["profile_m"]]
    if len(pr) < 3 or pr[-1][0] != 0.0:
        raise ParamError("shaped_gable.profile_m: at least three points, the last on the centre line (0)")
    if any(y1 <= y0 for (_, y0), (_, y1) in zip(pr, pr[1:])):
        raise ParamError("shaped_gable.profile_m: the outline rises point by point")
    if pr[0][0] > width / 2 or min(w for w, _ in pr) < 0.0:
        raise ParamError("shaped_gable.profile_m: the outline stands inside the front")
    if roof_form == "mansard":   # a mansard's eave is its cornice, the fascia's top on the wall head
        ye, ridge = eave, mansard["ridge_m"]
    else:
        ye = eave - overhang * math.tan(math.radians(pitch))
        ridge = eave + width / 2 * math.tan(math.radians(pitch))
    if pr[-1][1] < ridge + 0.3:
        raise ParamError(f"shaped_gable: its apex ({pr[-1][1]} m) stands at least 0.3 m over the roof's ridge ({ridge:.2f} m)")
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
    # T-2951: a grid window — `rows` of the variant stacked over one another, a stone
    # `transom_m` between each row and the next, and optionally its `panes` per light
    rows, tr = int(li.get("rows", 1)), float(li.get("transom_m", 0.0))
    if not 1 <= rows <= 4 or (rows > 1 and not 0.05 <= tr <= 0.3):
        raise ParamError("shaped_gable.lights: 1-4 rows, a 0.05-0.3 m stone transom between them")
    panes = li.get("panes")
    if panes is not None and (len(panes) != 2 or not all(1 <= int(n) <= 4 for n in panes)):
        raise ParamError("shaped_gable.lights.panes: [across, up], 1-4 each")
    lh_all = rows * lh + (rows - 1) * tr
    # T-3090: the grid window's dressings, each optional — `glazing: "dark"` (the print's
    # lights read as dark openings: no K06 sash, a dark backing behind glass at the reveal's
    # back), `quoins` (its side stones, one a row each side, long and short in turn), a `hood`
    # over its head (its upper edge waved: a crown at the middle, a flick at each end) and a
    # two-step moulded `shelf` under its sill
    dressing = {}
    glz = li.get("glazing", "sash")
    if glz not in ("sash", "dark"):
        raise ParamError("shaped_gable.lights.glazing: sash (K06's) or dark (an opening read dark, T-3090)")
    if glz == "dark":
        dressing["glazing"] = "dark"
    if li.get("quoins"):
        qn = {k_: float(li["quoins"][k_]) for k_ in ("long_m", "short_m", "proud_m")}
        if not 0.1 <= qn["short_m"] <= qn["long_m"] <= 0.6 or not 0.0 < qn["proud_m"] <= 0.08:
            raise ParamError("shaped_gable.lights.quoins: short 0.1 m to long 0.6 m, 0-0.08 m proud")
        dressing["quoins"] = qn
    if li.get("hood"):
        hd = {k_: float(li["hood"][k_]) for k_ in ("over_m", "height_m", "crown_m", "flick_m", "proud_m")}
        if not 0.0 <= hd["over_m"] <= 0.5 or not 0.04 <= hd["height_m"] <= 0.3 \
                or not 0.0 <= hd["crown_m"] <= 0.2 or not 0.0 <= hd["flick_m"] <= 0.15 or not 0.0 < hd["proud_m"] <= 0.15:
            raise ParamError("shaped_gable.lights.hood: 0-0.5 m past the window, 0.04-0.3 m high, its crown "
                             "0-0.2 m and its flicks 0-0.15 m over that, 0-0.15 m proud")
        dressing["hood"] = hd
    if li.get("shelf"):
        sf = {k_: float(li["shelf"][k_]) for k_ in ("over_m", "height_m", "proud_m", "band_m", "band_proud_m")}
        if not 0.0 <= sf["over_m"] <= 0.5 or not 0.04 <= sf["height_m"] <= 0.25 or not 0.0 < sf["proud_m"] <= 0.25 \
                or not 0.0 <= sf["band_m"] <= 0.3 or not 0.0 <= sf["band_proud_m"] <= sf["proud_m"]:
            raise ParamError("shaped_gable.lights.shelf: 0-0.5 m past the window, 0.04-0.25 m high and 0-0.25 m "
                             "proud, over a band 0-0.3 m high standing no further out")
        dressing["shelf"] = sf
    ledge = ye + 0.12
    ledge_m = None
    if sg.get("ledge_m") is not None:   # T-2865: the front carried up full width past the eave
        ledge_m = float(sg["ledge_m"])
        if not ledge <= ledge_m <= pr[-1][1] - 1.0:
            raise ParamError("shaped_gable.ledge_m: the ledge stands at least 0.12 m over the street "
                             "fascia and 1.0 m under the apex")
        ledge = ledge_m
    if sg.get("kneelers") and sill < ledge + 0.3:
        raise ParamError("shaped_gable.lights: a light's sill stands 0.3 m over the kneelers' ledge")
    if sill < foot + 0.3:   # T-2730: without kneelers a light may stand on the slab under the eave
        raise ParamError("shaped_gable.lights: a light's sill stands 0.3 m over the slab's foot")
    from archetypes import k01_shaped_gable as ksg
    q = {"profile_m": pr}
    for x in at:
        need = abs(x) + lw / 2 + 0.15
        if need > ksg.half_width(q, sill + lh_all + 0.15) or need > ksg.half_width(q, sill):
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
        if kn.get("scroll"):   # T-2951: a carved scroll console under each, at the front's corner
            sc = {k_: float(kn["scroll"][k_]) for k_ in ("bed_m", "width_m", "radius_m", "proud_m")}
            if not 0.1 <= sc["radius_m"] <= sc["width_m"] / 2 + 1e-9 or not 0.2 <= sc["width_m"] <= 0.8:
                raise ParamError("shaped_gable.kneelers.scroll: 0.2-0.8 m wide, its roll 0.1 m to half that in radius")
            if not 0.05 <= sc["proud_m"] <= 0.4 or not foot - 1.5 <= sc["bed_m"] <= foot - 2 * sc["radius_m"] - 0.1:
                raise ParamError("shaped_gable.kneelers.scroll: 0.05-0.4 m proud, its roll under the slab's foot "
                                 "and its bed within 1.5 m of it")
            # T-3090: the print's scroll is carved — a rosette in the roll's eye
            if kn["scroll"].get("rosette"):
                sc["rosette"] = int(kn["scroll"]["rosette"])
                if not 5 <= sc["rosette"] <= 12:
                    raise ParamError("shaped_gable.kneelers.scroll.rosette: 5-12 petals")
            kne["scroll"] = sc
    fin = {}
    if fn:
        fin = {"height_m": float(fn["height_m"]), "radius_m": float(fn["radius_m"])}
        if not 0.2 <= fin["height_m"] <= 1.2 or not 0.04 <= fin["radius_m"] <= 0.3:
            raise ParamError("shaped_gable.finial: 0.2-1.2 m high, 0.04-0.3 m in radius")
        if fn.get("form", "spike") not in ("spike", "urn"):
            raise ParamError("shaped_gable.finial.form: spike (T-2543's) or urn (a carved ball under an urn, T-3090)")
        if fn.get("form") == "urn":
            fin["form"] = "urn"
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
    sho = {}
    if sg.get("shoulders"):   # T-2951: a square stone block on the outline each side, through the slab
        s_ = sg["shoulders"]
        sho = {k_: float(s_[k_]) for k_ in ("inner_m", "outer_m", "bed_m", "top_m", "proud_m")}
        if not 0.2 <= sho["outer_m"] - sho["inner_m"] <= 1.2 or not 0.2 <= sho["top_m"] - sho["bed_m"] <= 1.2:
            raise ParamError("shaped_gable.shoulders: a block 0.2-1.2 m across and high")
        if not 0.0 < sho["proud_m"] <= 0.15 or sho["outer_m"] > ksg.half_width(q, sho["bed_m"]) + 1e-9:
            raise ParamError("shaped_gable.shoulders: 0-0.15 m proud, its foot inside the outline")
        if sho["bed_m"] < sill + lh_all + 0.15 and sho["inner_m"] < max(abs(x) for x in at) + lw / 2 + 0.05:
            raise ParamError("shaped_gable.shoulders: clear of the lights")
        if s_.get("panel"):   # T-3090: a sunk panel in each block's face
            pn = {k_: float(s_["panel"][k_]) for k_ in ("width_m", "height_m", "drop_m", "sunk_m")}
            bw_, bh_ = sho["outer_m"] - sho["inner_m"], sho["top_m"] - sho["bed_m"]
            if not 0.05 <= pn["width_m"] <= bw_ - 0.1 or not 0.03 <= pn["height_m"] or pn["drop_m"] < 0.05 \
                    or pn["drop_m"] + pn["height_m"] > bh_ - 0.05 or not 0.0 < pn["sunk_m"] < sho["proud_m"]:
                raise ParamError("shaped_gable.shoulders.panel: inside the block's face by 0.05 m all round, "
                                 "sunk less than the block stands proud")
            sho["panel"] = pn
    tg = sg.get("takes_gutter", False)
    if not isinstance(tg, bool):
        raise ParamError("shaped_gable.takes_gutter: true or false (T-2889)")
    base_in = None
    if sg.get("base_ledge_half_m") is not None:
        # T-3090: the slab's base drawn in from its foot to the ledge, where the print's outline
        # is already drawing in past the kneelers, in place of a square run past the side walls
        base_in = float(sg["base_ledge_half_m"])
        if not kne or not ksg.half_width(q, ledge) <= base_in <= width / 2 \
                or kne["at_m"] + kne["shaft_m"] / 2 > base_in + 1e-9:
            raise ParamError("shaped_gable.base_ledge_half_m: wider than the outline at the ledge, inside the "
                             "front, and wide enough to carry the kneelers' pinnacles")
    return {"profile_m": pr, "foot_m": foot, "thickness_m": t, "proud_m": proud,
            **({"takes_gutter": True} if tg else {}),
            "lights": {"variant": li["variant"], "sill_m": sill, "width_m": lw, "height_m": lh, "at_m": at,
                       **({"rows": rows, "transom_m": tr} if rows > 1 else {}),
                       **({"panes": [int(n) for n in panes]} if panes is not None else {}),
                       **dressing},
            **({"shoulders": sho} if sho else {}),
            "coping": coping, "kneelers": kne, "finial": fin, "fabric": fabric, "oculus": oc,
            **({"ledge_m": ledge_m} if ledge_m is not None else {}),
            **({"base_ledge_half_m": base_in} if base_in is not None else {})}


def _mansard_dormers(entries, m: dict, depth: float, width: float, eave: float, overhang: float,
                     chimneys, cant=None) -> list:
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
        if face == "cant":
            # T-3186: the canted corner's own dormer (1901's, over the face's window column in both
            # photographs), centred on the face's lower slope and clear of its two hips under the
            # curb, where the face is narrowest; k01_frontage turns a street dormer onto it
            d = _round_dormer(e, what, run, hood=False)
            if not cant or float(e["along_m"]) != 0.0 or d["head"] not in ("gable", "round"):
                raise ParamError(f"{what}: a cant dormer stands on a cant_corner, centred (along_m 0), "
                                 f"under a gable or round head")
            half = float(cant["cut_m"]) * math.sqrt(0.5) + (overhang - run) * math.tan(math.pi / 8)
            if d["width_m"] / 2 + 0.15 > half:
                raise ParamError(f"{what}: {d['width_m']} m across leaves the canted face's hips no "
                                 f"0.15 m under the curb, where the face is {2 * half:.2f} m")
            foot = mansard_face_height(d["face_setback_m"], m["lower_rise_m"], m["lower_pitch_deg"], m["bulge"],
                                       m["profile"])
            if foot + d["sill_m"] + d["head_m"] > m["lower_rise_m"] - 0.1:
                raise ParamError(f"{what}: its head meets the curb at {m['lower_rise_m']} m")
            out.append(dict(d, face=face, along_m=0.0, foot_m=round(eave + foot, 4)))
            continue
        if face not in MANSARD_FACES:
            raise ParamError(f"{what}.face {face!r}: one of {', '.join(MANSARD_FACES)}")
        d = _round_dormer(e, what, run, hood=True)
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
        if d["head"] == "hood":
            # T-3000: the hood's top, fallen back by its lean, still stands 0.1 m proud of the
            # lower face behind it, so the front never sinks into the roof it projects from
            back = d["face_setback_m"] + d["hood"]["lean_m"] + 0.1
            if mansard_face_height(back, m["lower_rise_m"], m["lower_pitch_deg"], m["bulge"], m["profile"]) > top:
                raise ParamError(f"{what}.hood: its top, {d['hood']['lean_m']} m back, meets the lower face")
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
    # T-2821: none at all is a plain plinth, one dressed course from grade (the coping),
    # where a photograph draws no rusticated base under it (1625's)
    if base and not lo <= base <= hi:
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
    if coursing is not None and coursing.get("rhythm") == "even":
        # T-2819: or evenly throughout, the whole range of rock face under `even_above_m`
        # and the shallower face above it (1623's drawing: rock-faced to the arches'
        # springing, smoother coursed stone over it) — the line itself a course line
        if set(coursing) != {"rhythm", "even_above_m", "even_rock_share"}:
            raise ParamError("stone_front.coursing with rhythm 'even' takes even_above_m and even_rock_share")
        if not (0.0 < float(coursing["even_rock_share"]) <= 1.0 and float(coursing["even_above_m"]) > 0.0):
            raise ParamError("stone_front.coursing: even_rock_share in (0, 1], even_above_m above grade")
    elif coursing is not None:
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
        # T-2914: the stone stops at a storey line and the front is the K03 brick over it
        **({"brick_above_m": float(front["brick_above_m"])} if "brick_above_m" in front else {}),
        # T-3184: the stone belts a picture draws across such a front's brick, in place of K01's
        **({"belts": _brick_belts(front)} if "belts" in front else {}),
        "coping_height_m": coping_h, "coping_fall": t["coping"]["fall"],
        "coping_overhang_m": t["coping"]["overhang_m"], "drip_groove_m": t["coping"]["drip_groove_m"],
        "fabric_roughness": lib[fab]["mean_roughness"], "trim_roughness": lib[trim]["mean_roughness"],
        # T-1881: or the trim's members cut from the walling's own stone (1729's: every
        # photograph draws its sills, rings, belts and dressings in the brownstone of the walls,
        # not a paler stone), laid to dressed_trim's profile numbers in the walling's fabric
        **({"trim_face": fab} if _trim_in_walling(front) else {}),
    }


def _trim_in_walling(front: dict) -> bool:
    """T-1881: does the record cut its trim from the walling's stone (`trim_in_walling`)?"""
    t = front.get("trim_in_walling", False)
    if t not in (True, False):
        raise ParamError("stone_front.trim_in_walling is true or false")
    return t


#: T-1879: the walls `window_shutters` may name, and how long each runs (depth or width)
SHUTTER_WALLS = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.side.south", "k01.wall.rear_service")


def _window_shutters(ws: dict, openings, floors, depth: float, width: float) -> dict:
    """T-1879: open louvred shutters folded back flat beside a wall's lights, read off a
    picture (1721's, the 1891 plate: a pair at every upper light of the recessed front and
    of the north flank). `walls` names each wall and the storeys (0 the principal floor)
    whose lights take them; every light of those storeys does, a pair `width_m` wide from its
    sill to its head with `louvre_m` slats, and each pair must stand clear of the wall's ends
    and of every other light. Doors and basement lights never take them."""
    if not ws:
        return {}
    if set(ws) != {"width_m", "louvre_m", "walls"} or not isinstance(ws["walls"], dict) or not ws["walls"]:
        raise ParamError("window_shutters takes width_m, louvre_m and walls ({wall: [storey, ...]})")
    w, lv = float(ws["width_m"]), float(ws["louvre_m"])
    if not 0.2 <= w <= 0.8 or not 0.06 <= lv <= 0.2:
        raise ParamError(f"window_shutters: leaves 0.2-0.8 m wide with slats 0.06-0.2 m apart, not {w} and {lv}")
    lights = []
    for cid, storeys in sorted(ws["walls"].items()):
        if cid not in SHUTTER_WALLS or not storeys or any(not 0 <= int(k) < len(floors) for k in storeys):
            raise ParamError(f"window_shutters.walls: {cid} is one of {SHUTTER_WALLS}, naming storeys 0-{len(floors) - 1}")
        length = width if cid in ("k01.wall.street_front", "k01.wall.rear_service") else depth
        ops = [o for o in openings if o.wall == cid and o.component not in ("k01.opening.door_leaf", "k01.opening.area_light")]
        tops = list(floors[1:]) + [math.inf]
        mine = [o for o in ops if any(floors[int(k)] <= o.sill_m < tops[int(k)] for k in storeys)]
        if not mine:
            raise ParamError(f"window_shutters.walls: {cid} has no light in storeys {storeys}")
        for o in mine:
            s0, s1 = o.s_m - o.width_m / 2 - SHUTTER_GAP_M - w, o.s_m + o.width_m / 2 + SHUTTER_GAP_M + w
            if s0 < 0.1 or s1 > length - 0.1 or any(
                    q is not o and q.s_m - q.width_m / 2 < s1 and q.s_m + q.width_m / 2 > s0
                    and q.sill_m < o.head_m and q.head_m > o.sill_m for q in ops):
                raise ParamError(f"window_shutters: the pair at s {o.s_m} on {cid} ({s0:.2f}-{s1:.2f} m) "
                                 f"runs past the wall or over another light")
            lights.append((cid, round(o.s_m - o.width_m / 2, 4), round(o.s_m + o.width_m / 2, 4),
                           round(o.sill_m, 4), round(o.head_m, 4)))
    return {"width_m": w, "louvre_m": lv, "lights": tuple(lights)}


#: T-1879: the gap between a light's side and its shutter's leaf
SHUTTER_GAP_M = 0.06


def _street_iron(si: dict, openings, entrance_kit: dict) -> dict:
    """T-3184: a brick front's iron read off its picture (1834's photograph), which an arched
    stone front names in `street_front_dress` and k01_arched_front lays:

      balconettes  [{from_s_m, to_s_m, floor_m, proud_m, height_m, slab_m, consoles}, ...]: a
                   stone slab `slab_m` deep under `floor_m`, `proud_m` out from the front, on
                   `consoles` scrolled stone consoles (none where the slab sits on the stone
                   basement's top), and on it a pierced iron guard `height_m` high under the
                   street window(s) it stands before, whose sills it stays under
      stoop_rails  {kit: k11.rail.stoop_rail, scroll_m}: the K11 stoop rail each side of a
                   stoop the record builds without cheeks (entrance_kit cheeks: false)"""
    if not si:
        return {}
    if not set(si) <= {"balconettes", "stoop_rails"} or not si:
        raise ParamError("street_front_iron takes balconettes and stoop_rails")
    out = {}
    bals = []
    front = [o for o in openings if o.wall == "k01.wall.street_front" and o.component != "k01.opening.door_leaf"
             and o.component != "k01.opening.area_light"]
    for j, b in enumerate(si.get("balconettes") or ()):
        need = {"from_s_m", "to_s_m", "floor_m", "proud_m", "height_m", "slab_m", "consoles"}
        # T-3212: `before_light: true`, a guard standing before the foot of a light that runs
        # down behind it to a sill over the shelf (1700-1706 Prairie's principal windows: the
        # 1901 construction photograph's openings and Chicagology's sashes)
        if set(b) - {"before_light"} != need or b.get("before_light", True) is not True:
            raise ParamError(f"street_front_iron.balconettes[{j}] takes {sorted(need)} (and before_light: true)")
        s0, s1, fl, d, h, sl, n = (float(b["from_s_m"]), float(b["to_s_m"]), float(b["floor_m"]),
                                   float(b["proud_m"]), float(b["height_m"]), float(b["slab_m"]), b["consoles"])
        if not (0.6 <= s1 - s0 <= 3.0 and 0.15 <= d <= 0.9 and 0.6 <= h <= 1.1 and 0.08 <= sl <= 0.25
                and isinstance(n, int) and n in (0, 2, 3, 4)):
            raise ParamError(f"street_front_iron.balconettes[{j}]: 0.6-3.0 m long, 0.15-0.9 m proud, a guard "
                             f"0.6-1.1 m high on a slab 0.08-0.25 m deep, on 0 or 2-4 consoles")
        over = [o for o in front if s0 < o.s_m < s1 and o.sill_m > fl]
        if b.get("before_light"):
            low = min(over, key=lambda o: o.sill_m) if over else None
            if low is None or not fl + sl <= low.sill_m < fl + h - 0.05 \
                    or any(o.sill_m < fl + h - 0.05 for o in over if o is not low):
                raise ParamError(f"street_front_iron.balconettes[{j}] before_light: a light's sill stands over "
                                 f"the shelf ({fl + sl:.2f} m) and under the guard's top ({fl + h:.2f} m)")
        elif not over or any(o.sill_m < fl + h - 0.05 for o in over):
            raise ParamError(f"street_front_iron.balconettes[{j}] stands under a street window, its guard "
                             f"under the sill ({fl + h:.2f} m)")
        bals.append({"from_s_m": s0, "to_s_m": s1, "floor_m": fl, "proud_m": d, "height_m": h, "slab_m": sl,
                     "consoles": n})
    if bals:
        out["balconettes"] = tuple(bals)
    rails = si.get("stoop_rails")
    if rails:
        if not {"kit", "scroll_m"} <= set(rails) <= {"kit", "scroll_m", "panel_m", "guard"} or rails["kit"] != "k11.rail.stoop_rail" \
                or not 0.1 <= float(rails["scroll_m"]) <= 0.5 or not 0.2 <= float(rails.get("panel_m", 0.4)) <= 0.7:
            raise ParamError("street_front_iron.stoop_rails are the K11 kit's k11.rail.stoop_rail, scroll_m 0.1-0.5, "
                             "and may name panel_m (0.2-0.7), a scrolled panel that deep under the handrail")
        if (entrance_kit.get("k01.opening.door_leaf") or {}).get("cheeks") is not False:
            raise ParamError("street_front_iron.stoop_rails stand on a stoop without cheeks (entrance_kit cheeks: false)")
        out["stoop_rails"] = {"kit": rails["kit"], "scroll_m": float(rails["scroll_m"]),
                              **({"panel_m": float(rails["panel_m"])} if "panel_m" in rails else {})}
        # the landing's guard along a terrace to `to_v_m`, pierced its whole length (the stoop's
        # scrolled panels, so it takes panel_m) — k01_arched_front._landing_guard
        gd = rails.get("guard")
        if gd is not None:
            if set(gd) != {"to_v_m"} or "panel_m" not in rails or "terrace" not in (
                    entrance_kit.get("k01.opening.door_leaf") or {}):
                raise ParamError("street_front_iron.stoop_rails.guard takes to_v_m, along a terrace, on scrolled "
                                 "rails (panel_m)")
            out["stoop_rails"]["guard"] = {"to_v_m": float(gd["to_v_m"]), "scrolled": True}
    return out


def _brick_belts(front: dict) -> tuple:
    """T-3184: a brick front over a stone basement (`brick_above_m`) may name the stone belts
    its picture draws across the brick, [[bed, top], ...] — none at all where it draws none
    (1834's photograph: no belt at the second floor and no band at the principal heads, which
    K01's two belts lay). Named, they are the only stone in the brick: every other thin course
    the openings' lines would strike there is brick."""
    if "brick_above_m" not in front:
        raise ParamError("stone_front.belts names the belts across a brick front over a stone "
                         "basement (brick_above_m); a stone front lays its own")
    out = []
    for b in front["belts"]:
        b0, b1 = (float(y) for y in b)
        if not float(front["brick_above_m"]) < b0 < b1 <= b0 + 0.4:
            raise ParamError(f"stone_front.belts {list(b)}: a course at most 0.40 m deep over the "
                             f"stone's top ({front['brick_above_m']} m)")
        out.append((b0, b1))
    return tuple(out)


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
    if plan["kind"] == "circle":
        # T-2787: a round tower meets its wall where its circle crosses the wall's face
        r, c = float(plan["radius_m"]), float(plan["centre_proud_m"])
        h = math.sqrt(r * r - c * c)
        return -h, h
    if plan["kind"] == "polygon":
        # ...and a polygonal one where its ring does (k08_bays walks the same ring)
        from . import k08_bays as K8
        ring = K8.polygon_vertices(int(plan["sides"]), float(plan["radius_m"]), float(plan["centre_proud_m"]),
                                   float(plan.get("turned_deg", 0.0)))
        if plan.get("across_corner"):
            # T-3176: across its corner it meets its wall from its junction to the corner
            chain = K8.across_corner_chain(ring, plan["across_corner"])
            return (chain[0][0], 0.0) if plan["across_corner"] == "right" else (0.0, chain[-1][0])
        xs = [a[0] + a[1] / (a[1] - b[1]) * (b[0] - a[0])
              for a, b in zip(ring, ring[1:] + ring[:1]) if (a[1] < 0) != (b[1] < 0)]
        xs += [a[0] for a in ring if abs(a[1]) < 1e-12]
        return min(xs), max(xs)
    raise ParamError(f"a K01 bay's plan is a polyline, a bow, a circle or a polygon, not a {plan['kind']}")


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
          floors: tuple = (), eave: float = 0.0, overhang: float = 0.0, front_coursed: bool = False,
          wing_corner: bool = False, eave_front: float | None = None):
    """Resolve the record's `bays` against the K08 kit; drop the host openings each covers.

    A bay stands in front of its wall from grade to its own wall top, so every host
    opening in that span below the top is behind it and is not cut; one that straddles a
    junction is refused, since half a window behind a bay's cheek is no window at all.
    An oriel (T-2369) stands from its lowest corbel course to its wall top: its floor is
    one of the house's floors (`base_m`), the record may set its corbel courses and size
    its canted plan, and its wall top stays a metre under the main eave — unless the
    record carries it `through_eave` (T-2778), under a spire, its back closed over the
    wall head. Or it rounds a projection's corner (`over_corner`, T-1890): a bow on one of
    that projection's storey lines whose ring buries the corner, to the projection's own wall
    top over the eave, its back closed on the wall plane from the eave up (`back_over`).
    `eave_front` is the height of the house eave's front edge, its fascia's top
    (the eave datum when not given), which a through-eave oriel's walls must clear (T-2989).
    """
    import copy as _copy
    kit = {v["id"]: v for v in json.loads(BAY_KIT.read_text())["variants"]}
    out = []
    carried = {e["on_chamfer"] for e in entries or () if e.get("on_chamfer") is not None}   # T-3108
    for e in entries or ():
        if e["variant"] not in kit:
            raise ParamError(f"bays: {e['variant']} is not a K08 variant (k08_bays.json)")
        v = _copy.deepcopy(kit[e["variant"]])
        oriel = v["kind"] == "oriel"
        if v["kind"] not in BAY_KINDS or (v["base"] != "grade") != oriel:
            raise ParamError(f"bays: {v['id']} is a {v['kind']} off {v['base']}; a K01 frontage carries "
                             f"a bay, a projection or a tower on grade, or an oriel on its corbels")
        over = None
        if oriel:
            base = float(e.get("base_m", -1.0))
            # T-1890: or an oriel rounding a projection's corner (1801's 18th Street section, its
            # west corner turned round over the corbel table in the Taylor print and HABS
            # photograph 2): its base one of that projection's storey lines, not the house's
            if e.get("over_corner") is not None:
                oc = e["over_corner"]
                host = next((x for x in out if x["id"] == oc.get("of")), None) if isinstance(oc, dict) else None
                lines = ([round(sum(float(st["height_m"]) for st in host["variant"]["storeys"][:i]), 6)
                          for i in range(1, len(host["variant"]["storeys"]))] if host is not None else [])
                if host is None or set(oc) != {"of", "corner"} or oc["corner"] not in ("left", "right") \
                        or host["variant"]["kind"] != "projection" or host["wall"] != e["wall"] \
                        or not any(abs(base - y) < 1e-6 for y in lines):
                    raise ParamError(f"bays: {e['id']} rounds the corner of a projection laid before it on the "
                                     f"same wall (`over_corner`: of, corner left or right), its base_m one of "
                                     f"that projection's storey lines {lines}")
                over = (host, oc["corner"])
            elif not any(abs(base - y) < 1e-6 for y in floors[1:]):
                raise ParamError(f"bays: {e['id']} is an oriel; its base_m stands on one of the upper floors {floors[1:]}")
            v["base"] = base
            if "corbel" in e:
                v["corbel"] = {"courses": int(e["corbel"]["courses"])}
                # T-1890: a corner round's courses step back only `reach_m` from its face, onto
                # the projection's corbel table and the house's cornice under it, not to the wall
                if "reach_m" in e["corbel"]:
                    cb = json.loads(BAY_KIT.read_text())["parts"]["corbel"]
                    reach, K = float(e["corbel"]["reach_m"]), v["corbel"]["courses"]
                    if over is None or set(e["corbel"]) != {"courses", "reach_m"} or not 0.1 <= reach \
                            or reach / (K + 1) > cb["max_oversail_ratio"] * cb["course_height_m"] + 1e-9:
                        raise ParamError(f"bays: {e['id']}'s corbel reach_m is a corner round's alone, and its "
                                         f"{K} courses cannot carry {reach} m (each oversails at most "
                                         f"{cb['max_oversail_ratio']} of its {cb['course_height_m']} m)")
                    v["corbel"]["reach_m"] = reach
            # T-2883: or an apron in the corbel courses' place, a flat face down to a moulded foot
            if "apron" in e:
                ap = e["apron"]
                # T-3007: or a ROUND apron, its face turned under on a quarter round of
                # radius_m (0.1-0.5 m) to a foot 0-0.5 m under the floor, its top on or over it
                # (1811's oriel's rock-faced base on its 1888 plate, the floor its foot)
                rnd = ap.get("form") == "round"
                ok = {"foot_m", "form", "radius_m"} <= set(ap) <= {"foot_m", "fabric", "form", "radius_m"} \
                    and ap["form"] == "round" and 0.1 <= float(ap["radius_m"]) <= 0.5 \
                    and 0.0 <= base - float(ap["foot_m"]) <= min(0.5, float(ap["radius_m"])) if rnd \
                    else {"foot_m"} <= set(ap) <= {"foot_m", "fabric"} and 1.0 <= base - float(ap["foot_m"]) <= 2.5
                if "corbel" in e or not ok:
                    raise ParamError(f"bays: {e['id']}'s apron takes foot_m (and a fabric), 1.0-2.5 m under its floor "
                                     f"at {base} m, in place of its corbel courses (not beside them); a round one "
                                     f"(form 'round') a radius_m of 0.1-0.5 m and its foot under the floor by no "
                                     f"more than that")
                v["apron"] = {"foot_m": float(ap["foot_m"]),
                              **({"form": "round", "radius_m": float(ap["radius_m"])} if rnd else {})}
                v.pop("corbel", None)
                # T-2904: or in a stone of its own: the front's K02 walling, where the bay is dressed
                if "fabric" in ap and not (ap["fabric"] == "front_stone" and front_stone):
                    raise ParamError(f"bays: {e['id']}'s apron takes one fabric, front_stone (the front's "
                                     f"K02 walling), and the record must name a stone_front")
            q = e.get("plan")
            # T-1890: or ROUND, a segmental bow on its chord and rise (1801's gabled section on
            # 18th Street, its oriel bowed on its corbels in the Taylor print and HABS photograph
            # 2), its front at most 1.2 m out as a canted one's
            if q is not None and q.get("kind") == "bow":
                if set(q) != {"kind", "chord_m", "rise_m"} \
                        or not 1.0 <= float(q["chord_m"]) <= 4.0 \
                        or not 0.2 <= float(q["rise_m"]) <= min(float(q["chord_m"]) / 2, 1.2):
                    raise ParamError(f"bays: {e['id']} sizes a round oriel's plan by chord_m (1.0-4.0 m) and "
                                     f"rise_m (0.2 m to half its chord, at most 1.2 m), not {q}")
                v["plan"] = {"kind": "bow", "chord_m": float(q["chord_m"]), "rise_m": float(q["rise_m"])}
                q = None
            if q is not None:
                pts = [[float(x), float(z)] for x, z in q.get("points", ())]
                # T-3007: or, saying so (`asymmetric`), returns of their own (1811's on its 1888
                # plate: square to the north, splayed back to the rounded corner to the south),
                # each end on the wall either side of the centre, running left to right
                asym = q.get("asymmetric") is True
                if q.get("kind") != "polyline" or len(pts) != len(v["plan"]["points"]) \
                        or set(q) - {"kind", "points", "asymmetric"} \
                        or (not asym and any(abs(a[0] + b[0]) > 1e-9 or abs(a[1] - b[1]) > 1e-9
                                             for a, b in zip(pts, pts[::-1]))) \
                        or (asym and (abs(pts[-1][1]) > 1e-9 or not pts[0][0] < 0.0 < pts[-1][0]
                                      or any(b[0] < a[0] - 1e-9 for a, b in zip(pts, pts[1:])))) \
                        or abs(pts[0][1]) > 1e-9 or not all(0.0 < z <= 1.2 for _, z in pts[1:-1]):
                    raise ParamError(f"bays: {e['id']} sizes its oriel's plan as the kit's canted polyline, "
                                     f"symmetric (or `asymmetric`, running left to right about its centre), "
                                     f"its ends on the wall and its front at most 1.2 m out")
                v["plan"] = {"kind": "polyline", "points": pts}
        if e["wall"] not in wall_len:
            raise ParamError(f"bays: {e['wall']} is not one of this assembly's walls")
        if e.get("fabric", "stone") not in BAY_FABRICS:
            raise ParamError(f"bays: fabric {e.get('fabric')!r} is not one of {BAY_FABRICS}")
        v["id"] = f"{structure_id}|{e['id']}"
        if e.get("masonry"):
            m = e["masonry"]
            if set(m) - {"coursing", "to_m"} != {"course_m", "block_m", "joint_m", "relief_m"} or not (.2 <= m["course_m"] <= .6 and .4 <= m["block_m"] <= 1.5 and .004 <= m["joint_m"] <= .02 and .008 <= m["relief_m"] <= .06):
                raise ParamError("bays.masonry: bounded coursed rock-faced ashlar")
            # T-2919: or rock-faced only up to one of its storey lines, smooth ashlar over it
            # (1811's bay on its plate, rock-faced to the first floor's sill course)
            if "to_m" in m:
                sts = e.get("storeys") or v["storeys"]
                lines = [round(sum(float(st["height_m"]) for st in sts[:i]), 4) for i in range(1, len(sts))]
                if not any(abs(float(m["to_m"]) - y) < 1e-6 for y in lines):
                    raise ParamError(f"bays: {e['id']}.masonry.to_m {m['to_m']} must be one of its storey lines {lines}")
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
            # T-1878: or a whole FORWARD BLOCK of the front (`block`), standing proud of the wall
            # behind a corner recess (1721's, the 1911 sheet and the 1891 Inland plate: 14 m of the
            # front stands 2.9 m before the wall the porch is set back against), square, flush
            # with its wall's other corner, and carrying the front's bows on its face (`on_front`)
            if q.get("block") is not None:
                if q["block"] is not True or not (6.0 < w <= 16.0 and 1.2 < d <= 3.5) \
                        or e.get("variant") != "k08.projection.full_height" \
                        or set(q) - {"width_m", "proud_m", "block"}:
                    raise ParamError(f"bays: {e['id']} is a forward block: a square full-height projection "
                                     f"6-16 m wide and 1.2-3.5 m proud, flush with a corner (has {w} m and {d} m)")
            # T-3191: or a flank's STEP (`step`), the rear part of a side wall standing out from its
            # front part (1827's south flank on the 1911 sheet: u 0-14.6 stands 1.6 m out), a plain
            # full-height projection on a side wall, longer and further out than a pavilion
            elif q.get("step") is not None:
                if q["step"] is not True or not (6.0 < w <= 16.0 and 0.1 <= d <= 2.5) \
                        or e.get("variant") != "k08.projection.full_height" \
                        or e.get("wall") not in ("k01.wall.side.north", "k01.wall.side.south") \
                        or set(q) - {"width_m", "proud_m", "step"}:
                    raise ParamError(f"bays: {e['id']} is a flank's step: a full-height projection on a side "
                                     f"wall, 6-16 m wide and 0.1-2.0 m proud (has {w} m and {d} m)")
            # T-1890: or a PIER (`pier`), a plain stone strip standing out from a wall from grade to
            # under its cornice (1801's 18th Street wall where the gabled section meets the main
            # block, in the Taylor print and HABS photograph 2): narrower than a pavilion, with no
            # window in it and a flat top under the eave it dies into
            elif q.get("pier") is not None:
                if q["pier"] is not True or not (0.3 <= w < 1.5 and 0.05 <= d <= 0.3) \
                        or e.get("variant") != "k08.projection.full_height" \
                        or any(st.get("windows") for st in e.get("storeys") or v["storeys"]) \
                        or (e.get("roof") or {}).get("kind") != "hip" or float((e.get("roof") or {}).get("pitch", -1)) != 0.0 \
                        or set(q) - {"width_m", "proud_m", "pier"}:
                    raise ParamError(f"bays: {e['id']} is a pier: a windowless full-height projection under a "
                                     f"flat top, 0.3-1.5 m wide and 0.05-0.3 m proud (has {w} m and {d} m)")
                v["pier"] = True   # check_bay_kit holds it to a box's triangles, with no light tier
            elif not (1.5 <= w <= 6.0 and 0.1 <= d <= 1.2):
                raise ParamError(f"bays: {e['id']}'s projection is {w} m wide and {d} m proud; a pavilion "
                                 f"is 1.5-6.0 m wide and stands 0.1-1.2 m proud")
            # T-2988: either cheek may be CANTED, running from the wall `cant_*_m` further out
            # along it than the front's corner (1811's bay on its 1911 sheet and its 1888 plate:
            # the north cheek from the wall 1.99 m north of the front's north corner); s_m stays
            # the front's centre, and the front keeps width_m. Neither cant: the square
            # pavilion, its points as they always were
            if set(q) - {"width_m", "proud_m", "cant_left_m", "cant_right_m", "shallow", "chamfer", "block", "step",
                         "pier"}:
                raise ParamError(f"bays: {e['id']} sizes its projection by width_m, proud_m, an optional "
                                 f"cant_left_m or cant_right_m, shallow and chamfer, not {sorted(q)}")
            cl, cr = (float(q.get(k, 0.0)) for k in ("cant_left_m", "cant_right_m"))
            if not all(c == 0.0 or 0.3 <= c <= 3.0 for c in (cl, cr)):
                raise ParamError(f"bays: {e['id']}'s canted cheek runs 0.3-3.0 m along its wall, not "
                                 f"{cl if cl else cr} m")
            v["plan"] = {"kind": "polyline", "points": [[-w / 2 - cl, 0.0], [-w / 2, d], [w / 2, d], [w / 2 + cr, 0.0]]}
            # T-3047: a SHALLOW pavilion (1801's south one, 0-0.1 m proud on its 1911 sheet) is
            # too thin to hold its windows' recesses or its gable's copings: they run back
            # through the host wall's plane, and the host opens its face round each recess
            # (k08_bays.Bay.host_holes) and stops its eave box and gutter at the cheeks
            if q.get("shallow") is not None:
                if q["shallow"] is not True or e.get("variant") != "k08.projection.full_height" or cl or cr \
                        or d > SHALLOW_PROUD_M:
                    raise ParamError(f"bays: {e['id']}'s shallow is true, on a square full-height projection "
                                     f"at most {SHALLOW_PROUD_M} m proud (has {d} m)")
                v["shallow"] = True
            # T-3048: a shallow pavilion flush with its wall's corner may CHAMFER that corner (1801's
            # south one, its south-west corner cut about 0.45 m on its 1911 sheet): its front stops
            # `along_m` short of the corner and a canted face runs from there back to the side
            # wall's plane `behind_m` behind the wall's face, so the house's own corner is cut
            # under it (k01_frontage `chamfer_spans`). width_m stays the pavilion's whole width
            ch = q.get("chamfer")
            if ch is not None:
                if not isinstance(ch, dict) or set(ch) != {"corner", "along_m", "behind_m"} \
                        or ch["corner"] not in ("left", "right") or not v.get("shallow") \
                        or e.get("flush_corner") != ch["corner"]:
                    raise ParamError(f"bays: {e['id']}'s chamfer takes corner (left or right), along_m and "
                                     f"behind_m, on a shallow pavilion flush with that corner")
                ca, cb = float(ch["along_m"]), float(ch["behind_m"])
                # T-3108: further on a chamfer a round bay stands on, which closes the cut in front
                rb = e["id"] in carried
                most_a, most_b = (ROUND_CHAMFER_ALONG_M, w / 2) if rb else (CHAMFER_ALONG_M, w / 4)
                most_c = ROUND_CHAMFER_BEHIND_M if rb else CHAMFER_BEHIND_M
                if not (0.2 <= ca <= min(most_a, most_b) and 0.1 <= cb <= most_c):
                    raise ParamError(f"bays: {e['id']}'s chamfer runs 0.2-{most_a} m (and at most "
                                     f"{'half' if rb else 'a quarter'} of its width) along its front and "
                                     f"0.1-{most_c} m behind the wall, not {ca} and {cb}")
                pts = v["plan"]["points"]
                if ch["corner"] == "right":
                    pts[2], pts[3] = [w / 2 - ca, d], [w / 2, -cb]
                else:
                    pts[0], pts[1] = [-w / 2, -cb], [-w / 2 + ca, d]
                v["plan"]["side_end"] = ch["corner"]
        elif "plan" in e and v["kind"] == "tower":
            # T-2787: a tower read off a picture keeps the picture's radius and how far its
            # centre stands out of the wall; the kit's tower is the shape (its ring, its sides),
            # never the size. Its centre stands on or out of the wall's face, so at least half
            # the ring is clear of it, and the ring always crosses the face
            q = e["plan"]
            across = e.get("across_corner")
            if across is None and set(q) != {"radius_m", "centre_proud_m"}:
                raise ParamError(f"bays: {e['id']} sizes its tower by radius_m and centre_proud_m, not {sorted(q)}")
            r, c = float(q["radius_m"]), float(q["centre_proud_m"])
            # T-2900: a corner turret's centre may stand inside its wall, as 1801's does on the
            # 1911 sheet (its bump 0.6 m proud on a ring 2.6 m across)
            c_lo = -(r - 0.3) if e.get("corner") is not None or across is not None else 0.0
            if not (1.0 <= r <= 4.0 and c_lo <= c <= r - 0.3):
                raise ParamError(f"bays: {e['id']}'s tower is {r} m in radius, its centre {c} m proud; a tower "
                                 f"is 1.0-4.0 m in radius and its centre {c_lo} m to its radius less 0.3 m out")
            v["plan"] = {**v["plan"], "radius_m": r, "centre_proud_m": c}
            if across is not None:
                # T-3176: a square tower set diagonally across its wall's corner (1827's, from the
                # Doane photograph and the 1911 sheet's turned bump at the south-west corner): the
                # kit's polygon with four sides, turned 45 degrees so an angle points out of each
                # wall, its centre on the end wall's plane (s_m the wall's end) and `centre_proud_m`
                # out of (or inside) the face, so its ring crosses both walls. Its walls stand on the
                # ring outside the house; over the wall head it is closed on both planes and its
                # cap is whole (k08_bays.Bay._corner_back)
                if across not in ("left", "right") or v["plan"]["kind"] != "polygon" or e.get("corner") \
                        or e.get("flush_corner") or set(q) != {"radius_m", "centre_proud_m", "sides", "turned_deg"} \
                        or int(q["sides"]) != 4 or abs(float(q["turned_deg"]) - 45.0) > 1e-9:
                    raise ParamError(f"bays: {e['id']} across_corner is 'left' or 'right', on a polygonal tower "
                                     f"sized by radius_m, centre_proud_m, sides 4 and turned_deg 45")
                end = 0.0 if across == "left" else wall_len[e["wall"]]
                if abs(float(e["s_m"]) - end) > 1e-6:
                    raise ParamError(f"bays: {e['id']} stands across its {across} corner, so its s_m is that "
                                     f"corner's ({end} m), not {e['s_m']}")
                if not -(r - 0.3) <= c <= r / math.sqrt(2):
                    raise ParamError(f"bays: {e['id']}'s centre {c} m proud leaves its ring off one of its walls")
                v["plan"] = {**v["plan"], "sides": 4, "turned_deg": 45.0, "across_corner": across}
                v["corner_back_m"] = eave
        elif "plan" in e and not oriel and v["plan"]["kind"] == "polyline" and v["kind"] == "bay":
            # T-2780: a canted bay drawn on its sheet keeps the sheet's size (1637's south bay on
            # the 1911 sheet, 3.55 m at the wall and 0.75 m out); the kit's polyline is the shape,
            # so the record's has as many points, symmetric, its ends on the wall, as an oriel's.
            # T-2963: a bay standing on grade may come out 1.8 m, as 1816's front bay does on its
            # sheet (1.65 m); an oriel, carried on corbels off the wall, stays at 1.2 m
            q = e["plan"]
            pts = [[float(x), float(z)] for x, z in q.get("points", ())]
            if q.get("kind") != "polyline" or len(pts) != len(v["plan"]["points"]) \
                    or any(abs(a[0] + b[0]) > 1e-9 or abs(a[1] - b[1]) > 1e-9 for a, b in zip(pts, pts[::-1])) \
                    or abs(pts[0][1]) > 1e-9 or not all(0.0 < z <= 1.8 for _, z in pts[1:-1]) \
                    or any(b[0] <= a[0] for a, b in zip(pts, pts[1:])):
                raise ParamError(f"bays: {e['id']} sizes its bay's plan as the kit's polyline, symmetric, "
                                 f"its ends on the wall, running left to right and its front at most 1.8 m out")
            v["plan"] = {"kind": "polyline", "points": pts}
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
        # T-1881: a pavilion's mansard slated as the house's own lower faces (1729's: each
        # forward section carries the main roof's slate round its own curb in every photograph)
        if v["roof"].get("slated_as_house") is not None:
            if v["roof"]["slated_as_house"] is not True or not v["roof"].get("mansard"):
                raise ParamError(f"bays: {e['id']}'s roof.slated_as_house is true, on a mansard")
        # T-1890: a round tower's corbelled upper stage (1801's, in the Taylor print and HABS
        # photograph 2): from one of its storey lines its ring is wider than its shaft's, carried
        # out on stepped corbel courses, its eaves and cone the stage's (k08_bays._build_staged)
        if "stage" in e:
            sg = e["stage"]
            ok = isinstance(sg, dict) and set(sg) == {"from_storey", "radius_m", "corbel_courses"} \
                and v["kind"] == "tower" and v["plan"]["kind"] == "circle" and not e.get("corner")
            if ok:
                k, r2, kc = int(sg["from_storey"]), float(sg["radius_m"]), int(sg["corbel_courses"])
                r1 = float(v["plan"]["radius_m"])
                ok = 0 < k < len(v["storeys"]) and r1 + 0.2 <= r2 <= min(4.0, r1 + 1.0) and 2 <= kc <= 8
            if not ok:
                raise ParamError(f"bays: {e['id']}'s stage takes from_storey (one of its storey lines), radius_m "
                                 f"(0.2-1.0 m wider than its shaft, at most 4.0 m) and corbel_courses (2-8), on "
                                 f"a round tower standing on its own wall, not {sg}")
            v["stage"] = {"from_storey": k, "radius_m": r2, "corbel_courses": kc}
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
                # T-2815: a transom window's fixed lights in tiers, each on a stone bar (Keith's
                # bow, from the 1888 plate): only on a K06 transom sash, and a sash left under them
                if "tiers" in w:
                    k06 = json.loads(WINDOW_KIT.read_text())
                    v6 = next((x for x in k06["variants"] if x["id"] == w["opening"]), {})
                    t = w["tiers"]
                    ok = isinstance(t, dict) and set(t) == {"bar_m", "lights_m"} \
                        and v6.get("operation") == "double_hung_transom" and 1 <= len(t["lights_m"]) <= 3
                    if ok:
                        bar, lights = float(t["bar_m"]), [float(h) for h in t["lights_m"]]
                        ch = float(w.get("clear_height_m", v6.get("clear_height_m", 0.0)))
                        ok = 0.05 <= bar <= 0.3 and all(0.2 <= h <= 1.0 for h in lights) \
                            and ch - sum(lights) - bar * len(lights) >= 1.0
                    if not ok:
                        raise ParamError(f"bays: {e['id']}'s tiers take bar_m (0.05-0.3 m) and one to three "
                                         f"lights_m (0.2-1.0 m each) on a K06 transom sash, leaving at least "
                                         f"1.0 m of sash under them, not {t}")
                    w["tiers"] = {"bar_m": bar, "lights_m": lights}
                # T-2886: a light set between a bay's columns under a narrower band than the
                # kit's (1637's south bay's cheeks, from the Grosvenor photograph): only over an
                # arched head, never wider than the kit's own band nor thinner than a moulding
                if "head_band_m" in w:
                    k06 = json.loads(WINDOW_KIT.read_text())
                    v6 = next((x for x in k06["variants"] if x["id"] == w["opening"]), {})
                    hb, hb_kit = float(w["head_band_m"]), k06["parts"]["head_band"]["width_m"]
                    if v6.get("head", "flat") == "flat" or not 0.03 <= hb <= hb_kit:
                        raise ParamError(f"bays: {e['id']}'s head_band_m {hb} needs an arched K06 head "
                                         f"(not {w['opening']}) and a band 0.03-{hb_kit} m broad")
                    w["head_band_m"] = hb
                # T-2883: a narrow light in a shallow cheek (1625's oriel, from its print): one light
                # a sash on a double-hung K06 opening, under half a metre, and it says why
                # T-3007: or a transom sash's (1811's oriel's return, its lights transomed as its front's)
                if "narrow" in w:
                    k06 = json.loads(WINDOW_KIT.read_text())
                    v6 = next((x for x in k06["variants"] if x["id"] == w["opening"]), {})
                    if w["narrow"] is not True or v6.get("operation") not in ("double_hung", "double_hung_transom") \
                            or v6.get("bays", 1) != 1 \
                            or not 0.2 <= float(w.get("clear_width_m", 1.0)) <= 0.45 or not w.get("why_not_ordinary"):
                        raise ParamError(f"bays: {e['id']}'s narrow light is `narrow: true` on a single double-hung "
                                         f"(or transomed) K06 opening 0.2-0.45 m across that says why (why_not_ordinary)")
                # T-1879: open louvred shutters folded back beside a bay's light, and an iron
                # guard on a stone slab before its foot (1721's bows and forward block, the 1891
                # plate). In the light's own frame, so a bow bends them with it
                if "shutters" in w:
                    sh = w["shutters"]
                    if not isinstance(sh, dict) or set(sh) != {"width_m", "louvre_m"} \
                            or not 0.2 <= float(sh["width_m"]) <= 0.8 or not 0.06 <= float(sh["louvre_m"]) <= 0.2:
                        raise ParamError(f"bays: {e['id']}'s shutters take width_m (0.2-0.8 m) and louvre_m "
                                         f"(0.06-0.2 m), not {sh}")
                    w["shutters"] = {"width_m": float(sh["width_m"]), "louvre_m": float(sh["louvre_m"])}
                if "guard" in w:
                    gd = w["guard"]
                    need = {"height_m", "proud_m", "slab_m", "pitch_m", "reach_m"}
                    if not isinstance(gd, dict) or set(gd) != need:
                        raise ParamError(f"bays: {e['id']}'s guard takes {sorted(need)}")
                    gd = {k: float(gd[k]) for k in sorted(need)}
                    if not 0.5 <= gd["height_m"] <= 1.1 or not 0.15 <= gd["proud_m"] <= 0.6 \
                            or not 0.08 <= gd["slab_m"] <= 0.25 or not 0.08 <= gd["pitch_m"] <= 0.25 \
                            or not 0.0 <= gd["reach_m"] <= 1.0 or gd["height_m"] + gd["slab_m"] + 0.02 > float(w["sill_m"]):
                        raise ParamError(f"bays: {e['id']}'s guard {gd} is not a guard 0.5-1.1 m high, 0.15-0.6 m "
                                         f"proud, on a 0.08-0.25 m slab, bars 0.08-0.25 m apart, reaching 0-1.0 m past "
                                         f"the light, its slab over the storey's floor")
                    w["guard"] = gd
                g = w.get("grille")
                if g is None:
                    continue
                # T-3129: or, for `bars`, a rosette `panel` (1811's basement lights, from the
                # c. 1888 photograph): border_m, pitch_m and rosette_m, all in metres
                pn = g.get("panel")
                if pn is not None:
                    ok = set(g) == {"panel", "set_back_m", "ring_radius_m"} and isinstance(pn, dict) \
                        and set(pn) == {"border_m", "pitch_m", "rosette_m"} \
                        and 0.04 <= float(pn["border_m"]) <= 0.2 and 0.03 <= float(pn["pitch_m"]) <= 0.15 \
                        and 0.04 <= float(pn["rosette_m"]) <= 0.15
                else:
                    ok = set(g) == {"bars", "set_back_m", "ring_radius_m"} and 2 <= int(g["bars"]) <= 16
                if not ok or not 0.0 < float(g["set_back_m"]) <= 0.08:
                    raise ParamError(f"bays: {e['id']}'s grille takes bars (2-16) or a panel (border_m "
                                     f"0.04-0.2, pitch_m 0.03-0.15, rosette_m 0.04-0.15), set_back_m (at "
                                     f"most 0.08 m) and ring_radius_m, not {g}")
                if pn is not None:
                    w["grille"] = {"panel": {k: float(pn[k]) for k in ("border_m", "pitch_m", "rosette_m")},
                                   "set_back_m": float(g["set_back_m"]), "ring_radius_m": float(g["ring_radius_m"])}
                else:
                    w["grille"] = {"bars": int(g["bars"]), "set_back_m": float(g["set_back_m"]),
                                   "ring_radius_m": float(g["ring_radius_m"])}
        # T-2931: a light's moulded surround, jambs on its sill's horns under its lintel as a
        # hood (1801's bow and pavilion, from the Taylor photograph): on a flat-headed stone
        # light, never beside voussoirs, the jambs less proud than the sill and under the hood
        for st in v["storeys"]:
            for w in st["windows"]:
                su = w.get("surround")
                if su is None:
                    continue
                k06 = json.loads(WINDOW_KIT.read_text())
                v6 = next((x for x in k06["variants"] if x["id"] == w["opening"]), {})
                sill6 = k06["parts"]["sill"]["projection_m"]
                keys = {"band_m", "proud_m", "head_m", "head_proud_m"}
                if not isinstance(su, dict) or set(su) != keys or v6.get("head", "flat") != "flat" \
                        or "voussoirs" in w or w.get("narrow") or e.get("fabric", "stone") == "frame" \
                        or not 0.06 <= float(su["band_m"]) <= 0.25 or not 0.01 <= float(su["proud_m"]) < sill6 \
                        or not 0.1 <= float(su["head_m"]) <= 0.4 \
                        or not float(su["proud_m"]) < float(su["head_proud_m"]) <= 0.12:
                    raise ParamError(f"bays: {e['id']}'s surround takes band_m (0.06-0.25 m), proud_m (0.01 m, short "
                                     f"of the sill's {sill6} m), head_m (0.1-0.4 m) and head_proud_m (prouder "
                                     f"than the jambs, at most 0.12 m), on a flat-headed stone light without "
                                     f"voussoirs, not {su}")
                w["surround"] = {k: float(su[k]) for k in sorted(keys)}
                ty = w.get("tympanum")
                if ty is not None:
                    w["tympanum"] = tympanum_spec(ty, f"bays: {e['id']}'s tympanum", float(su["head_proud_m"]))
        for st in v["storeys"]:
            for w in st["windows"]:
                if "tympanum" in w and "surround" not in w:
                    raise ParamError(f"bays: {e['id']}'s tympanum stands on a moulded surround's lintel; name one")
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
        # (T-3133: down to 0.05 m, 1811's bay on the Chicagology print, its lights' sills on it)
        if "plinth_m" in e:
            ph = float(e["plinth_m"])
            if v["base"] != "grade" or not 0.05 <= ph <= 0.6:
                raise ParamError(f"bays: {e['id']}'s plinth_m {ph} is a grade bay's, 0.05-0.6 m")
            v.setdefault("overrides", {}).setdefault("plinth", {})["height_m"] = ph
        if "cap_band" in e:
            # T-2815: a carved band round the bay under its cap, read off a picture (Keith's
            # bow, the 1888 plate), carrying the frieze's guilloche (T-2778's keys)
            cb = e["cap_band"]
            g = cb.get("guilloche") if isinstance(cb, dict) else None
            gk = {"radius_m", "ring_width_m", "ring_proud_m", "margin_m", "pitch", "segments"}
            if not isinstance(g, dict) or set(cb) != {"height_m", "proud_m", "guilloche"} or set(g) != gk \
                    or not (0.1 <= float(cb["height_m"]) <= 0.8 and 0.01 <= float(cb["proud_m"]) <= 0.08) \
                    or not (6 <= int(g["segments"]) <= 24 and 1.0 <= float(g["pitch"]) <= 3.0) \
                    or not (0.0 < float(g["ring_width_m"]) < float(g["radius_m"]) <= 0.5
                            and 0.0 < float(g["ring_proud_m"]) <= 0.05 and 0.0 <= float(g["margin_m"]) <= 0.1):
                raise ParamError(f"bays: {e['id']}'s cap_band takes height_m (0.1-0.8 m), proud_m (0.01-0.08 m) "
                                 f"and a guilloche of {sorted(gk)}, not {cb}")
            v["cap_band"] = {"height_m": float(cb["height_m"]), "proud_m": float(cb["proud_m"]),
                             "guilloche": {k: (int(g[k]) if k == "segments" else float(g[k])) for k in sorted(gk)}}
        # T-3197: a storey slated at its sides (1827's pavilion attic under its crown, the Doane
        # photograph): the front run's outer width_m at each end and every other run, in slate
        for st in v["storeys"]:
            ch = st.get("cheeks")
            if ch is None:
                continue
            if not isinstance(ch, dict) or set(ch) != {"front_run", "width_m", "proud_m"} \
                    or not (0 <= int(ch["front_run"]) and 0.3 <= float(ch["width_m"]) <= 2.0
                            and 0.01 <= float(ch["proud_m"]) <= 0.06):
                raise ParamError(f"bays: {e['id']}'s cheeks take front_run, width_m (0.3-2.0 m) and proud_m "
                                 f"(0.01-0.06 m), not {ch}")
            st["cheeks"] = {"front_run": int(ch["front_run"]), "width_m": float(ch["width_m"]),
                            "proud_m": float(ch["proud_m"])}
        # T-3002: a dressed band across one run over a storey's windows, under its top, with a
        # roundel on it (1801's south pavilion under its gable's shelf, the Taylor photograph)
        for st in v["storeys"]:
            hf = st.get("head_frieze")
            if hf is None:
                continue
            keys, rk = {"run", "at", "from_m", "to_m", "border_m", "proud_m", "roundel"}, \
                {"radius_m", "ring_m", "proud_m", "segments"}
            rd = hf.get("roundel") if isinstance(hf, dict) else None
            if not isinstance(rd, dict) or set(hf) != keys or set(rd) != rk \
                    or not (0 <= int(hf["run"]) and 0.0 < float(hf["at"]) < 1.0
                            and 0.0 < float(hf["from_m"]) < float(hf["to_m"]) <= float(st["height_m"])
                            and 0.3 <= float(hf["to_m"]) - float(hf["from_m"]) <= 1.5
                            and 0.05 <= float(hf["border_m"]) <= 0.6 and 0.01 <= float(hf["proud_m"]) <= 0.06
                            and 0.05 <= float(rd["radius_m"]) <= 0.5 and 0.02 <= float(rd["ring_m"]) < float(rd["radius_m"])
                            and 0.01 <= float(rd["proud_m"]) <= 0.05 and 12 <= int(rd["segments"]) <= 48):
                raise ParamError(f"bays: {e['id']}'s head_frieze takes {sorted(keys)} (a band 0.3-1.5 m deep inside "
                                 f"its storey, 0.01-0.06 m proud) and a roundel of {sorted(rk)}, not {hf}")
            k06 = json.loads(WINDOW_KIT.read_text())
            for w in st["windows"]:
                v6 = next((x for x in k06["variants"] if x["id"] == w["opening"]), {})
                head = float(w["sill_m"]) + float(w.get("clear_height_m", v6.get("clear_height_m", 0.0))) \
                    + float((w.get("surround") or {}).get("head_m", 0.0))
                if head > float(hf["from_m"]) - 0.02:
                    raise ParamError(f"bays: {e['id']}'s head_frieze from {hf['from_m']} m stands on a head at {head:.3f} m")
            st["head_frieze"] = {"run": int(hf["run"]), "at": float(hf["at"]), "roundel": {
                "radius_m": float(rd["radius_m"]), "ring_m": float(rd["ring_m"]), "proud_m": float(rd["proud_m"]),
                "segments": int(rd["segments"])}, **{k: float(hf[k]) for k in ("from_m", "to_m", "border_m", "proud_m")}}
        # T-1890: a corbel table carrying a storey in place of its floor band (1801's 18th Street
        # section, the Taylor print and HABS photograph 2): a stone course on a row of corbels
        for k, st in enumerate(v["storeys"]):
            ct = st.get("corbel_table")
            if ct is None:
                continue
            keys = {"height_m", "course_m", "proud_m", "block_m", "pitch_m", "margin_m"}
            if k == 0 or not isinstance(ct, dict) or set(ct) != keys \
                    or not (0.1 <= float(ct["course_m"]) <= 0.4 and float(ct["course_m"]) + 0.2 <= float(ct["height_m"]) <= 1.5
                            and 0.05 <= float(ct["proud_m"]) <= 0.5 and 0.1 <= float(ct["block_m"]) <= 0.6
                            and float(ct["block_m"]) + 0.05 <= float(ct["pitch_m"]) <= 1.5
                            and 0.0 <= float(ct["margin_m"]) <= 0.5):
                raise ParamError(f"bays: {e['id']}'s corbel_table takes {sorted(keys)} (on a storey over another: a "
                                 f"0.1-0.4 m course 0.05-0.5 m proud, corbels 0.1-0.6 m wide, 0.05 m apart at "
                                 f"least, down to 1.5 m under the line), not {ct}")
            st["corbel_table"] = {k_: float(ct[k_]) for k_ in sorted(keys)}
        if "light_tier" in e:
            # T-1890: a bay holding an OPEN opening (1801's gabled section's loggia) has no sash,
            # blind or curtain there for its light tier to drop, so it may state its own light-tier
            # triangle ratio, with its reason; check_bay_kit holds it to 0.65 and to such a bay
            lt = e["light_tier"]
            if not isinstance(lt, dict) or set(lt) != {"max_triangle_ratio", "why"} or not str(lt["why"]).strip() \
                    or not 0.55 < float(lt["max_triangle_ratio"]) <= 0.65:
                raise ParamError(f"bays: {e['id']}'s light_tier takes max_triangle_ratio (over 0.55, at most 0.65) "
                                 f"and why, not {lt}")
            v["light_tier"] = {"max_triangle_ratio": float(lt["max_triangle_ratio"]), "why": str(lt["why"])}
        if "pilasters" in e:
            # T-2931: carved pilasters at the ends of a stone bay's runs (1801's bow and its south
            # pavilion, from the Taylor photograph), one a storey on a base, under a capital
            pl = e["pilasters"]
            keys = {"at", "width_m", "proud_m", "base_m", "capital_m"}
            lk = {"pitch_m", "gap_m", "margin_m", "relief_m"}
            runs_n = len(v["plan"]["points"]) - 1 if v["plan"]["kind"] == "polyline" else 1
            ok = isinstance(pl, dict) and set(pl) - {"lozenges", "foot_m", "corbel_m", "bands"} == keys and e.get("fabric", "stone") != "frame" \
                and v["base"] == "grade" and isinstance(pl["at"], list) and pl["at"] \
                and all(set(q) == {"run", "at"} and 0 <= int(q["run"]) < runs_n
                        and q["at"] in ("start", "end", "both") for q in pl["at"])
            if ok:
                w, d, hb, hc = (float(pl[k]) for k in ("width_m", "proud_m", "base_m", "capital_m"))
                ok = 0.1 <= w <= (1.2 if "bands" in pl else 0.6) and 0.02 <= d <= 0.15 and 0.05 <= hb <= 0.4 \
                    and 0.1 <= hc <= 0.6
            bd = pl.get("bands") if ok else None
            if bd is not None:
                # T-1881: a banded pier's courses and the channels between them (1729's)
                ok = isinstance(bd, dict) and set(bd) == {"course_m", "channel_m"} and "lozenges" not in pl \
                    and 0.2 <= float(bd["course_m"]) <= 0.8 and 0.02 <= float(bd["channel_m"]) <= float(bd["course_m"]) / 3
            lz = pl.get("lozenges") if ok else None
            if lz is not None:
                ok = isinstance(lz, dict) and set(lz) == lk and 0.1 <= float(lz["pitch_m"]) <= 1.0 \
                    and 0.0 <= float(lz["gap_m"]) < float(lz["pitch_m"]) / 2 \
                    and 0.01 <= float(lz["margin_m"]) < w / 2 - 0.02 and 0.005 <= float(lz["relief_m"]) <= 0.04
            if not ok:
                raise ParamError(f"bays: {e['id']}'s pilasters take at (runs of its plan and start, end or "
                                 f"both), width_m (0.1-0.6 m), proud_m (0.02-0.15 m), base_m (0.05-0.4 m), "
                                 f"capital_m (0.1-0.6 m) and optional lozenges ({sorted(lk)}) or bands (course_m "
                                 f"0.2-0.8 m, channel_m 0.02 m to a third of it; then up to 1.2 m wide), on a stone "
                                 f"bay on grade")
            ft, cm = pl.get("foot_m"), pl.get("corbel_m")
            if ok and ft is not None:
                ft = float(ft)
                ok = 0.0 < ft <= v["storeys"][0]["height_m"] - hb - hc - 0.5
            if ok and cm is not None:
                cm = float(cm)
                ok = ft is not None and 0.1 <= cm <= min(0.6, ft - 0.1)
            if not ok:
                raise ParamError(f"bays: {e['id']}'s pilasters' foot_m stands the lowest base over grade, half "
                                 f"a metre of shaft under its first storey's top, and corbel_m (0.1-0.6 m, under "
                                 f"a foot_m) hangs a corbel under it")
            for st in v["storeys"]:
                if st["height_m"] < hb + hc + 0.5:
                    raise ParamError(f"bays: {e['id']}'s pilasters need half a metre of shaft in every storey "
                                     f"over their base and capital, not {st['height_m']} m")
            v["pilasters"] = {"at": [{"run": int(q["run"]), "at": q["at"]} for q in pl["at"]],
                              "width_m": w, "proud_m": d, "base_m": hb, "capital_m": hc,
                              **({"foot_m": ft} if ft is not None else {}),
                              **({"corbel_m": cm} if cm is not None else {}),
                              **({"lozenges": {k: float(lz[k]) for k in sorted(lk)}} if lz else {}),
                              **({"bands": {k: float(bd[k]) for k in ("channel_m", "course_m")}} if bd else {})}
        if "finial" in e:
            # T-1890: a cap's finial read off a picture sizes the kit's spike, never adds one
            # (1801's tower's, about 2.7 m over its cone's apex in the Taylor print)
            fn = e["finial"]
            if not v["roof"].get("finial") or not isinstance(fn, dict) or not {"height_m", "radius_m"} <= set(fn) \
                    or not set(fn) <= {"height_m", "radius_m", "form", "collar_m", "fabric"} \
                    or not 0.3 <= float(fn["height_m"]) <= 3.5 or not 0.03 <= float(fn["radius_m"]) <= 0.3:
                raise ParamError(f"bays: {e['id']}'s finial sizes its cap's own finial by height_m (0.3-3.5 m) "
                                 f"and radius_m (0.03-0.3 m), not {fn}")
            v.setdefault("overrides", {})["finial"] = {k: float(fn[k]) for k in ("height_m", "radius_m")}
            # T-1890: or TURNS it — knobs stacked on a waisted shaft over a crocketed collar
            # `collar_m` out on the cone (1801's tower in the Taylor print) — and may lay it in a
            # sheet metal of its own (FINIAL_FABRICS), where a picture reads it pale on the slate
            form = fn.get("form", "spike")
            if form not in ("spike", "turned"):
                raise ParamError(f"bays: {e['id']}'s finial.form {form!r}: spike or turned")
            if "collar_m" in fn:
                cm = float(fn["collar_m"])
                if form != "turned" or v["roof"].get("kind") != "cone" or not 0.2 <= cm <= 0.8:
                    raise ParamError(f"bays: {e['id']}'s finial.collar_m {cm}: a turned finial's collar, "
                                     f"0.2-0.8 m out on a cone")
                v["overrides"]["finial"]["collar_m"] = cm
            if form == "turned":
                v["overrides"]["finial"]["form"] = form
            if "fabric" in fn and fn["fabric"] not in FINIAL_FABRICS:
                raise ParamError(f"bays: {e['id']}'s finial.fabric {fn['fabric']!r}: one of {', '.join(FINIAL_FABRICS)}")
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
        # T-2408's consoles and modillions read off a picture (1637's south bay, T-2780): the
        # record sizes the variant's own brackets, never adds them to a variant without
        if "brackets" in e:
            br, kb = e["brackets"], v.get("brackets")
            if kb is None or set(br) - set(kb) or any(set(br[k]) != set(kb[k]) for k in br):
                raise ParamError(f"bays: {e['id']}'s brackets size {v['id']}'s own consoles and modillions, "
                                 f"with their keys, not {br}")
            for k, part_ in br.items():
                for kk, x in part_.items():
                    lo, hi = (2, 16) if kk == "segments" else (0.02, 1.2)
                    if not lo <= float(x) <= hi:
                        raise ParamError(f"bays: {e['id']}'s brackets.{k}.{kk} {x} is outside [{lo}, {hi}]")
                    kb[k][kk] = int(x) if kk == "segments" else float(x)
        # T-3195: a row of plain stone blocks under a moulded eave (1827's tower, from the Doane
        # photograph), on every run: only under a K10 moulded cornice, never beside the brackets
        if "corbel_table" in e:
            ct = e["corbel_table"]
            need = {"spacing_m", "width_m", "drop_m", "out_m", "margin_m"}
            ok = isinstance(ct, dict) and set(ct) == need and not v.get("brackets") \
                and bool(v["overrides"].get("eaves", {}).get("profile"))
            if ok:
                ct = {k: float(ct[k]) for k in sorted(need)}
                ok = 0.05 <= ct["width_m"] < ct["spacing_m"] <= 1.5 and 0.05 <= ct["drop_m"] <= 0.6 \
                    and 0.05 <= ct["out_m"] <= 0.5 and 0.0 <= ct["margin_m"] <= 0.5
            if not ok:
                raise ParamError(f"bays: {e['id']}'s corbel_table stands under eaves naming a K10 moulded "
                                 f"cornice, with no brackets, and takes width_m (at least 0.05) under spacing_m "
                                 f"(at most 1.5), drop_m (0.05-0.6), out_m (0.05-0.5) and margin_m (0-0.5), "
                                 f"not {e['corbel_table']}")
            v["corbel_table"] = ct
        # T-2525: an iron balcony rail on a bow's eaves, round its plan from wall to wall;
        # T-2780: or a stone balustrade round a flat-topped canted bay's (1637's south bay);
        # T-2888: or an iron rail round a flat-topped projection's front and cheeks (1812's)
        if "balcony" in e:
            bl = dict(e["balcony"])
            fabric = bl.pop("fabric", "iron")
            # T-2930: or a stone balustrade's pierced panels in place of its bars (1801's bow)
            panels = bl.pop("panels", None)
            # T-3092: or a stone panel in one run's middle rising to a pedestal, iron scrolls
            # over its sweeps, and a roundel on every bar (1812's, the Levy print)
            spanel, roundel = bl.pop("panel", None), bl.pop("roundel", None)
            need = {"height_m", "inset_m", "post_m", "bar_m", "pitch_m", "rail_m", "foot_rail_m"}
            flat_top = v["plan"]["kind"] == "polyline" and v["kind"] in ("bay", "projection") \
                and float(e.get("roof", v["roof"]).get("pitch", 1.0)) == 0.0
            if not (v["plan"]["kind"] == "bow" or flat_top) or set(bl) != need or fabric not in ("iron", "stone"):
                raise ParamError(f"bays: {e['id']}'s balcony stands on a bow, or on a canted bay's or a "
                                 f"projection's flat top, in iron or stone, and takes {sorted(need)}")
            bal = {k: ([float(x) for x in bl[k]] if k == "rail_m" else float(bl[k])) for k in need}
            if fabric == "stone":   # an iron rail's resolved entry stays as it was, byte for byte
                bal["fabric"] = fabric
            if panels is not None:
                if fabric != "stone" or not isinstance(panels, dict) or set(panels) != {"count", "rows"} \
                        or not 1 <= int(panels["count"]) <= 6 or not 1 <= int(panels["rows"]) <= 3:
                    raise ParamError(f"bays: {e['id']}'s balcony panels are a stone balustrade's, and take "
                                     f"count (1-6 panels between posts) and rows (1-3 diamonds to a panel's height)")
                bal["panels"] = {"count": int(panels["count"]), "rows": int(panels["rows"])}
            if not 0.5 <= bal["height_m"] <= 1.2 or not 0.06 <= bal["pitch_m"] <= 0.3 \
                    or not 0.0 < bal["bar_m"] < bal["pitch_m"] / 2 or not 0.0 <= bal["inset_m"] <= 0.3 \
                    or not 0.0 < bal["foot_rail_m"] < bal["height_m"] / 2:
                raise ParamError(f"bays: {e['id']}'s balcony {bal} is not a railing (0.5-1.2 m high, "
                                 f"bars 0.06-0.3 m apart and thinner than half that, 0-0.3 m in from the eaves)")
            # T-2888: on a projection the rails stop inside the corner posts, so they are thinner
            if v["kind"] == "projection" and not bal["rail_m"][0] < bal["post_m"]:
                raise ParamError(f"bays: {e['id']}'s balcony rail {bal['rail_m'][0]} m is no thinner than its "
                                 f"{bal['post_m']} m posts, so it cannot stop inside the projection's corner posts")
            if spanel is not None:
                pk = {"run", "width_m", "end_m", "sweep_m", "shoulder_m", "thickness_m", "pedestal_m", "scroll_m", "boss_m"}
                if fabric != "iron" or panels is not None or not isinstance(spanel, dict) or set(spanel) != pk:
                    raise ParamError(f"bays: {e['id']}'s balcony panel is stone in an iron rail and takes {sorted(pk)}")
                sp = {k: (int(x) if k == "run" else [float(y) for y in x] if k == "pedestal_m" else float(x))
                      for k, x in spanel.items()}
                pw, ph = sp["pedestal_m"]
                if not 0 <= sp["run"] < len(v["plan"]["points"]) - 1 or not 0.5 <= sp["width_m"] <= 5.0 \
                        or not 0.0 < sp["end_m"] < sp["shoulder_m"] < bal["height_m"] - bal["rail_m"][1] \
                        or not 0.1 <= sp["sweep_m"] < (sp["width_m"] - pw) / 2 or not 0.06 <= sp["thickness_m"] <= 0.3 \
                        or not 0.15 <= pw <= 0.8 or not sp["shoulder_m"] < ph <= bal["height_m"] + 0.3 \
                        or not 0.03 <= sp["scroll_m"] <= 0.25 or not 0.02 <= sp["boss_m"] <= 0.12:
                    raise ParamError(f"bays: {e['id']}'s balcony panel {sp} is not a panel under its rail: its "
                                     f"ends under its shoulders under the rail, its sweeps clear of its pedestal")
                bal["panel"] = sp
            if roundel is not None:
                rk = {"radius_m", "width_m", "drop_m"}
                if fabric != "iron" or not isinstance(roundel, dict) or set(roundel) != rk:
                    raise ParamError(f"bays: {e['id']}'s balcony roundel is an iron ring on each bar, and takes {sorted(rk)}")
                rd_ = {k: float(x) for k, x in roundel.items()}
                if not bal["bar_m"] / 2 < rd_["radius_m"] - rd_["width_m"] or not 0.005 <= rd_["width_m"] <= 0.03 \
                        or not 2 * rd_["radius_m"] < bal["pitch_m"] or not 0.0 <= rd_["drop_m"] <= 0.2:
                    raise ParamError(f"bays: {e['id']}'s balcony roundel {rd_} does not ring its bar inside its pitch")
                bal["roundel"] = rd_
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
        # T-3108: a bow standing on a chamfered pavilion's canted face (1801's south-west corner,
        # HABS photograph 1: a two-storey round bay between the gabled face and the south wall,
        # where the 1911 sheet cuts the corner back): its wall is the cant, s_m measured along it
        # from its left end, and on its host wall it stands over the cant's own span
        cant = None
        if e.get("on_chamfer") is not None:
            host = next((x for x in out if x["id"] == e["on_chamfer"]), None)
            ch = chamfer_of(host) if host is not None else None
            if ch is None or host["wall"] != e["wall"] or v["kind"] != "bay" or v["plan"]["kind"] != "bow" \
                    or oriel or e.get("flush_corner") or e.get("corner") or e.get("window_over") \
                    or e.get("strips") or e.get("columns") or e.get("dress"):
                raise ParamError(f"bays: {e['id']} stands on_chamfer: a bow on grade, on the chamfer of a "
                                 f"projection laid before it on the same wall")
            hp = host["variant"]["plan"]["points"]
            (ax, az), (bx, bz) = (hp[2], hp[3]) if ch[0] == "right" else (hp[0], hp[1])
            L = math.hypot(bx - ax, bz - az)
            ex, ez = (bx - ax) / L, (bz - az) / L
            if not (BAY_PIER_M / 2 - 1e-9 <= a and b <= L - BAY_PIER_M / 2 + 1e-9):
                raise ParamError(f"bays: {e['id']} meets its chamfer at s {a:.3f}..{b:.3f}, closer than "
                                 f"{BAY_PIER_M / 2} m to an end of its {L:.3f} m face")
            cant = {"host": host["id"], "origin": (round(host["s_m"] + ax, 6), round(az, 6)),
                    "along": (round(ex, 6), round(ez, 6)), "out": (round(-ez, 6), round(ex, 6)),
                    "length_m": round(L, 4), "s_m": s}
            a, b = host["s_m"] + min(ax, bx), host["s_m"] + max(ax, bx)
        # T-1878: a bay standing on a forward block's FRONT (1721's two bows, the 1911 sheet and
        # the 1891 Inland plate): its wall is the block's face, s_m measured along it from its
        # left end, and on its host wall it stands over the block's own span. The same frame
        # as a chamfer's, with no cant
        face = None
        if e.get("on_front") is not None:
            host = next((x for x in out if x["id"] == e["on_front"]), None)
            if host is None or not host.get("block") or host["wall"] != e["wall"] or v["kind"] != "bay" \
                    or oriel or cant is not None or e.get("flush_corner") or e.get("corner") \
                    or e.get("window_over") or e.get("strips") or e.get("columns") or e.get("dress"):
                raise ParamError(f"bays: {e['id']} stands on_front: a bay on grade, on the face of a forward "
                                 f"block laid before it on the same wall")
            (ax, az), (bx, _bz) = host["variant"]["plan"]["points"][1:3]
            L = bx - ax
            if not (BAY_PIER_M - 1e-9 <= a and b <= L - BAY_PIER_M + 1e-9):
                raise ParamError(f"bays: {e['id']} meets its block's face at s {a:.3f}..{b:.3f}, closer than "
                                 f"{BAY_PIER_M} m to an end of its {L:.3f} m face")
            face = {"host": host["id"], "origin": (round(host["s_m"] + ax, 6), round(az, 6)),
                    "along": (1.0, 0.0), "out": (0.0, 1.0), "length_m": round(L, 4), "s_m": s}
            a, b = host["s_m"] + ax, host["s_m"] + bx
        # T-2404: a pavilion may stand flush with its wall's corner — its cheek then runs on in
        # the side wall's own plane, as 1620's north pavilion does in its 1874 engraving. Only
        # a projection, only at the corner it names, and then exactly at it
        flush = e.get("flush_corner")
        if flush is not None and cant is None:
            if v["kind"] != "projection" or flush not in ("left", "right"):
                raise ParamError(f"bays: {e['id']}: flush_corner is 'left' or 'right', on a projection only")
            at = a if flush == "left" else wall_len[e["wall"]] - b
            if abs(at) > 1e-6:
                raise ParamError(f"bays: {e['id']} is flush with its {flush} corner, and its junction stands "
                                 f"{at:.3f} m from it")
        # T-2900: a corner turret: a round tower on a rear wing's wall at one of its ends, its
        # ring standing within TURRET_CORNER_M of the end wall's plane and never past it, its
        # eaves at the wing's own wall top (1801's east range, the Taylor photograph), and its
        # cone whole over the wing's roof. Its junction may then fall inside the pier
        corner = e.get("corner")
        if corner is not None:
            if not wing_corner:
                raise ParamError(f"bays: {e['id']} is a corner turret, and a corner turret stands on a rear wing's wall")
            if v["kind"] != "tower" or v["plan"]["kind"] != "circle" or corner not in ("left", "right") or flush:
                raise ParamError(f"bays: {e['id']}: corner is 'left' or 'right', on a round tower only")
            r = float(v["plan"]["radius_m"])
            gap = s - r if corner == "left" else wall_len[e["wall"]] - (s + r)
            if not -1e-9 <= gap <= TURRET_CORNER_M + 1e-9:
                raise ParamError(f"bays: {e['id']}'s ring stands {gap:.3f} m inside its {corner} end; a corner turret's "
                                 f"stands 0-{TURRET_CORNER_M} m inside it, never past the end wall's plane")
            v["cap_whole"] = True
        across = e.get("across_corner")   # T-3176
        if cant is None and face is None and ((a < BAY_PIER_M - 1e-9 and flush != "left" and corner != "left"
                                               and across != "left") or
                                              (b > wall_len[e["wall"]] - BAY_PIER_M + 1e-9 and flush != "right"
                                               and corner != "right" and across != "right")):
            raise ParamError(f"bays: {e['id']} meets {e['wall']} at s {a:.3f}..{b:.3f}, closer than "
                             f"{BAY_PIER_M} m to a corner of its {wall_len[e['wall']]} m wall")
        top = sum(float(st["height_m"]) for st in v["storeys"])
        bottom = 0.0
        if oriel:
            from . import k08_bays as K8
            bottom = K8.support_bottom(v)
            top += v["base"]
            spire = v["roof"].get("kind") == "spire"
            if over is not None:
                # T-1890: a corner round: a bow whose ring buries its host's corner (at least
                # 0.15 m of its walling round it), its wall top the host's own, standing over the
                # house's eave; its back is closed on the wall plane from that eave to its wall
                # top, over the stretch of its plan the host does not stand in front of
                host, side = over
                q = v["plan"]
                hp = host["variant"]["plan"]["points"]
                proud_h = max(z for _, z in hp)
                edge = host["span_m"][0] if side == "left" else host["span_m"][1]
                htop = sum(float(st["height_m"]) for st in host["variant"]["storeys"])
                if q["kind"] != "bow" or e.get("through_eave") or spire:
                    raise ParamError(f"bays: {e['id']} rounds a corner as a bow (chord_m, rise_m) under its own "
                                     f"cap, not through the eave")
                h_, rise = q["chord_m"] / 2, q["rise_m"]
                R = (h_ * h_ + rise * rise) / (2 * rise)
                if math.hypot(edge - s, proud_h - (rise - R)) > R - 0.15 + 1e-9 or abs(top - htop) > 1e-6 \
                        or not v["base"] > eave + 0.3:
                    raise ParamError(f"bays: {e['id']} rounds {host['id']}'s {side} corner: its ring must bury the "
                                     f"corner under 0.15 m of walling, its wall top must be {htop:.2f} m (has "
                                     f"{top:.2f}), and its base 0.3 m over the eave ({eave:.2f} m)")
                x0, x1 = (-h_, edge - s) if side == "left" else (edge - s, h_)
                v["back_over"] = {"x": [round(x0, 6), round(x1, 6)], "y": [eave, top]}
            elif e.get("through_eave"):
                # T-2778: an oriel carried up through the eave (1623's, from its drawing): its
                # upper stage stands clear over the main roof under a spire, the house's eave,
                # gutter and bed moulding die into its cants (so its front stands past them),
                # and its back is closed over the wall head, where no wall stands behind it
                # T-2989: or its wall top may stand UNDER the eave datum, as 1811's plate draws its
                # oriel's cornice (its top 9.06 m, under the 9.14 m datum), so long as its walls
                # rise 0.3 m over the eave's front edge (the fascia's top), so the eave still dies
                # into them; its back is then closed from the datum up, over its eaves and spire
                # only (k08_bays._back)
                front = max(z for _, z in v["plan"]["points"])
                edge = eave if eave_front is None else eave_front
                if not spire or not (top >= eave + 0.3 or edge + 0.3 - 1e-9 <= top < eave) or front < overhang + 0.15:
                    raise ParamError(f"bays: {e['id']} is carried through the eave: under a spire, its wall top "
                                     f"at least 0.3 m over the eave ({eave:.2f} m; has {top:.2f}), or under it and "
                                     f"0.3 m over the eave's front edge ({edge:.2f} m), and its front 0.15 m past "
                                     f"the eave's {overhang} m (has {front})")
                v["back_from_m"] = eave
            elif spire or top > eave - 1.0:
                raise ParamError(f"bays: {e['id']}'s wall top {top:.2f} m is not a metre under the eave "
                                 f"({eave:.2f} m), or it stands under a spire without being carried through it")
        if corner is not None:
            if abs(top - eave) > 1e-6:
                raise ParamError(f"bays: {e['id']} is a corner turret whose wall top {top:.2f} m is not its wing's "
                                 f"({eave:.2f} m); its eaves are the wing's own")
        elif v["kind"] == "tower" and top < eave + TOWER_PAST_EAVE_M - 1e-9:
            raise ParamError(f"bays: {e['id']} is a tower whose wall top {top:.2f} m is not {TOWER_PAST_EAVE_M} m "
                             f"over the eave ({eave:.2f} m); a shorter one is a bay with its cap in the eave")
        for o in list(openings):
            if o.wall != e["wall"] or cant is not None:   # T-3108: its host stood over them
                continue
            o0, o1 = o.s_m - o.width_m / 2 - 0.12, o.s_m + o.width_m / 2 + 0.12   # the lintel's horns
            if o1 <= a or o0 >= b or o.sill_m >= top or o.head_m + 0.30 <= bottom:
                continue
            if o.component == "k01.opening.door_leaf":
                # T-3135: a projection the porch arch is cut into at its corner (1812's: the Levy
                # print and the c. 1955 photograph draw the arch's south jamb and its moulding on
                # the projection's own face, south of its corner): the mouth's one jamb inside the
                # projection, at most half a metre in, its axis clear of it; the rest stands
                j0, j1 = o.s_m - o.width_m / 2, o.s_m + o.width_m / 2
                if e.get("cut_by_entrance") is True and v["kind"] == "projection" and (
                        (a < j0 < b < o.s_m and b - j0 <= 0.5) or (o.s_m < a < j1 < b and j1 - a <= 0.5)):
                    continue
                # T-1881: or a forward block that CARRIES the entrance on its face (1729's: the
                # 1911 sheet draws the Prairie front's north part 2.95 m before the rest, its stoop
                # before it, and the photographs put the door behind the portico on that part):
                # the door is cut in the block's face, the door, stoop and porch laid out from
                # it, and the host wall's door stands inside the block
                if e.get("entrance") is True and v["kind"] == "projection" and (e.get("plan") or {}).get("block") \
                        and e["wall"] == "k01.wall.street_front" and a + BAY_PIER_M <= j0 and j1 <= b - BAY_PIER_M:
                    v["door_hole"] = {"x_m": (round(j0 - (a + b) / 2, 4), round(j1 - (a + b) / 2, 4)),
                                      "y_m": (round(o.sill_m, 4), round(o.head_m, 4))}
                    continue
                raise ParamError(f"bays: {e['id']} stands in front of the entrance"
                                 + ("" if not e.get("cut_by_entrance") else
                                    " (cut_by_entrance: true cuts a projection's corner for one jamb, "
                                    "at most 0.5 m in, the mouth's axis clear of it)"))
            if o0 < a or o1 > b:
                raise ParamError(f"bays: {e['id']}'s junction at s {a:.3f}..{b:.3f} cuts the opening at "
                                 f"s {o.s_m} on {o.wall}")
            openings.remove(o)
        # T-2780: the host wall's window over a one-storey bay, centred on it, its sill on or
        # over the bay's top (1637's south bay: the round-headed light over its balustrade, which
        # the house's sash_by_storey would have put behind the bay and so never cut)
        wo = e.get("window_over")
        if wo is not None:
            if set(wo) - {"offset_m"} != {"sill_m", "width_m", "height_m", "head"} \
                    or wo["head"] not in ("flat", "round") or oriel or v["kind"] != "bay":
                raise ParamError(f"bays: {e['id']}'s window_over takes sill_m, width_m, height_m, head "
                                 f"(flat or round) and an optional offset_m, over a bay on grade")
            ws, ww, wh = float(wo["sill_m"]), float(wo["width_m"]), float(wo["height_m"])
            # T-2909: off the bay's centre line along its wall, where a picture puts it (1637's
            # light over its south bay stands 0.55 m east of the bay's centre in the Grosvenor
            # photograph), inside the bay's span with 0.3 m to spare
            wc = float(wo.get("offset_m", 0.0))
            if not top <= ws or not 0.6 <= ww <= min(1.5, b - a - 0.6) or not 1.0 <= wh <= 3.0 \
                    or ws + wh + 0.30 > eave - 0.25 or (wo["head"] == "round" and wh < ww / 2 + 0.3) \
                    or abs(wc) > (b - a - ww) / 2 - 0.3:
                raise ParamError(f"bays: {e['id']}'s window_over {wo} does not stand on the bay's top "
                                 f"({top:.2f} m), 0.6-1.5 m wide inside its span and under the eave ({eave:.2f} m)")
            for o in openings:
                if o.wall == e["wall"] and abs(o.s_m - (s + wc)) < (o.width_m + ww) / 2 + 0.24 \
                        and o.sill_m < ws + wh + 0.3 and ws < o.head_m + 0.3:
                    raise ParamError(f"bays: {e['id']}'s window_over meets the opening at s {o.s_m} on {o.wall}")
            openings.append(Opening(ROUND_HOODED if wo["head"] == "round" else "k01.opening.sash_flat",
                                    e["wall"], round(s + wc, 4), round(ws, 4), ww, wh))
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
        # T-2781: engaged stone columns on a canted bay's faces (1637's south bay, the Grosvenor
        # photograph's columns at its angles and beside its lights): one shaft size for all,
        # each at `s_m` along one run of the plan (a run's end stands it on the corner's
        # bisector), from `from_m` to `to_m` over grade, a square base and capital at its ends
        columns = None
        if e.get("columns") is not None:
            cl = e["columns"]
            pts = v["plan"]["points"] if v["plan"]["kind"] == "polyline" else None
            need = {"diameter_m", "from_m", "to_m", "base_m", "capital_m", "at"}
            if pts is None or set(cl) != need or e.get("fabric", "stone") != "stone" or not cl["at"]:
                raise ParamError(f"bays: {e['id']}'s columns take {sorted(need)}, on a stone bay's polyline plan")
            d, y0, y1 = float(cl["diameter_m"]), float(cl["from_m"]), float(cl["to_m"])
            hb, hc = float(cl["base_m"]), float(cl["capital_m"])
            if not 0.1 <= d <= 0.5 or not 0.0 <= y0 < y1 <= top + 1e-9 \
                    or not (0.05 <= hb <= 0.5 and 0.05 <= hc <= 0.5) or y1 - y0 - hb - hc < 4 * d:
                raise ParamError(f"bays: {e['id']}'s columns are {d} m across (0.1-0.5) from {y0} to {y1} m "
                                 f"inside the bay's wall (top {top:.2f} m), a shaft at least four diameters "
                                 f"between a base and a capital of 0.05-0.5 m each")
            at = []
            for j, q in enumerate(cl["at"]):
                run, s_ = int(q["run"]), float(q["s_m"])
                if set(q) != {"run", "s_m"} or not 0 <= run < len(pts) - 1 \
                        or not 0.0 <= s_ <= math.dist(pts[run], pts[run + 1]) + 1e-3:
                    raise ParamError(f"bays: {e['id']}.columns.at[{j}] {q} is not a run of its plan and a "
                                     f"distance along it")
                at.append({"run": run, "s_m": s_})
            columns = {"diameter_m": d, "from_m": y0, "to_m": y1, "base_m": hb, "capital_m": hc,
                       "at": tuple(at)}
        dress = _bay_dress(e, v, top, columns) if e.get("dress") is not None else None
        if e.get("fabric") == "front_stone" and not front_stone:
            raise ParamError(f"bays: {e['id']} is laid in the front's stone, and the record names no K02 stone_front")
        brick_above = None
        if "brick_above_m" in e:
            # T-2914: a stone bay whose wall is brick over one of its storey lines (1812's
            # projection: rock-faced basement, brick over it); its plinth, bands, sills,
            # heads and reveals stay stone, its dressings
            brick_above = float(e["brick_above_m"])
            lines = [round(sum(float(st["height_m"]) for st in v["storeys"][:i]), 4) for i in range(1, len(v["storeys"]))]
            if e.get("fabric", "stone") not in ("stone", "front_stone") or not any(abs(brick_above - y) < 1e-6 for y in lines):
                raise ParamError(f"bays: {e['id']}.brick_above_m {brick_above} must be one of a stone bay's "
                                 f"storey lines {lines}")
        out.append({"id": e["id"], "wall": e["wall"], "s_m": s if cant is None and face is None else round(a, 4),
                    "span_m": (round(a, 4), round(b, 4)),
                    **({"on_chamfer": cant} if cant else {}),
                    **({"on_face": face} if face else {}),
                    **({"block": True} if (e.get("plan") or {}).get("block") is True else {}),
                    "fabric": e.get("fabric", "stone"), "variant": v,
                    **({"apron_fabric": e["apron"]["fabric"]} if "fabric" in (e.get("apron") or {}) else {}),
                    **({"finial_fabric": e["finial"]["fabric"]} if "fabric" in (e.get("finial") or {}) else {}),
                    **({"flush_corner": flush} if flush else {}),
                    **({"corner": corner} if corner else {}),
                    **({"across_corner": across} if across else {}),
                    **({"through_eave": True} if e.get("through_eave") else {}),
                    **({"cut_by_entrance": True} if e.get("cut_by_entrance") is True else {}),
                    # T-3236: or a bay whose cornice overhangs a porch arch's pier (1812's)
                    **({"seat_walls": True} if e.get("seat_walls") is True else {}),
                    **({"entrance": True} if "door_hole" in v else {}),
                    # T-3101: a canted cheek seats the bay part by part on its wall
                    **({"canted": True} if any(float((e.get("plan") or {}).get(k, 0.0))
                                               for k in ("cant_left_m", "cant_right_m")) else {}),
                    **({"strips": tuple(strips)} if strips else {}),
                    **({"columns": columns} if columns else {}),
                    **({"dress": dress} if dress else {}),
                    **({"brick_above_m": brick_above} if brick_above is not None else {})})
    return tuple(out)


def _bay_dress(e: dict, v: dict, top: float, columns: dict | None) -> dict:
    """T-2887: a stone bay's carved dress, read off a picture (1637's south bay, the Grosvenor
    photograph): its columns' capitals carved as a bell of leaves under an abacus, mitred bands
    round its faces (the architrave over the capitals, the bed mouldings under the soffit and
    the corona's cymatium), oval panels in its frieze, a roll at each end of its consoles (the
    scroll) and open louvred shutters at the window over it. Every part is optional.
    T-2915: a bay in the front's stone takes it too (1812's projection, the Levy photograph),
    with its windows' quoined jambs, a band along one run broken at its window, and an oval
    whose field is a raised boss."""
    ds, bid = e["dress"], e["id"]
    pts = v["plan"]["points"] if v["plan"]["kind"] == "polyline" else None
    known = {"capitals", "bands", "ovals", "volutes_m", "shutters", "quoins", "run_bands", "blocks"}
    if pts is None or e.get("fabric", "stone") not in ("stone", "front_stone") or not ds or set(ds) - known:
        raise ParamError(f"bays: {bid}'s dress takes {sorted(known)}, on a stone bay's polyline plan")
    out = {"soffit_m": round(top, 4)}
    if "capitals" in ds:
        cp = ds["capitals"]
        if columns is None or set(cp) != {"tiers", "abacus_m"} or cp["tiers"] not in (1, 2) \
                or not 0.03 <= float(cp["abacus_m"]) <= columns["capital_m"] - 0.08:
            raise ParamError(f"bays: {bid}'s dress.capitals take tiers (1 or 2) and abacus_m, 0.03 m up to "
                             f"0.08 m short of its columns' capital, and carve the columns it has")
        out["capitals"] = {"tiers": int(cp["tiers"]), "abacus_m": float(cp["abacus_m"])}
    bands = []
    for j, q in enumerate(ds.get("bands") or ()):
        if set(q) - {"in_m"} != {"from_m", "to_m", "proud_m"}:
            raise ParamError(f"bays: {bid}.dress.bands[{j}] takes from_m, to_m, proud_m and an optional in_m")
        y0, y1, d, d0 = float(q["from_m"]), float(q["to_m"]), float(q["proud_m"]), float(q.get("in_m", 0.0))
        if not 0.0 < y0 < y1 <= top + 0.5 or y1 - y0 > 0.5 or not 0.0 <= d0 < d <= 0.6:
            raise ParamError(f"bays: {bid}.dress.bands[{j}] {q} is a band up to 0.5 m tall, inside the bay and "
                             f"its eaves (top {top:.2f} m), from in_m out to 0.6 m proud")
        bands.append({"from_m": y0, "to_m": y1, "proud_m": d, "in_m": d0})
    if bands:
        out["bands"] = tuple(bands)
    ovals = []
    for j, q in enumerate(ds.get("ovals") or ()):
        need = {"run", "s_m", "y_m", "width_m", "height_m", "proud_m"}
        # T-3093: an optional `shape`, `shield` for a carved shield's outline (1812's bosses under
        # the projection's jambs, Levy's print): square-shouldered and drawn to a point below
        if set(q) - {"field", "shape"} != need or q.get("field", "dark") not in ("dark", "stone", "boss") \
                or q.get("shape", "oval") not in ("oval", "shield") or not 0 <= int(q["run"]) < len(pts) - 1:
            raise ParamError(f"bays: {bid}.dress.ovals[{j}] takes {sorted(need)}, an optional field "
                             f"(dark, stone or boss) and an optional shape (oval or shield), on a run of its plan")
        run, s_, y_ = int(q["run"]), float(q["s_m"]), float(q["y_m"])
        w, h, d = float(q["width_m"]), float(q["height_m"]), float(q["proud_m"])
        # T-2909: up to 1.6 m across, for the broad sunk roundel in 1637's bay's base
        if not (0.1 <= w <= 1.6 and 0.1 <= h <= 1.0 and 0.01 <= d <= 0.1) \
                or not w / 2 <= s_ <= math.dist(pts[run], pts[run + 1]) - w / 2 or not h / 2 < y_ < top - h / 2:
            raise ParamError(f"bays: {bid}.dress.ovals[{j}] {q} is 0.1-1.6 m across, 0.1-1.0 m tall and "
                             f"0.01-0.1 m proud, inside its run and the bay's wall (top {top:.2f} m)")
        ovals.append({"run": run, "s_m": s_, "y_m": y_, "width_m": w, "height_m": h, "proud_m": d,
                      **({"field": q["field"]} if q.get("field") in ("stone", "boss") else {}),
                      **({"shape": "shield"} if q.get("shape") == "shield" else {})})
    if ovals:
        out["ovals"] = tuple(ovals)
    run_len = lambda r: math.dist(pts[r], pts[r + 1])
    quoins = []
    for j, q in enumerate(ds.get("quoins") or ()):
        # T-2915: a window's quoined jambs on one run of the plan: from `from_m` to `to_m` over
        # grade, `courses` dressed stones a side, each `returns_m` [short, long] out from the
        # jamb in turn from the foot, standing `proud_m` before the wall
        need = {"run", "jambs_m", "from_m", "to_m", "returns_m", "courses", "proud_m"}
        if set(q) != need or not 0 <= int(q["run"]) < len(pts) - 1:
            raise ParamError(f"bays: {bid}.dress.quoins[{j}] takes {sorted(need)}, on a run of its plan")
        run = int(q["run"])
        a, b = sorted(float(x) for x in q["jambs_m"])
        lo, hi = (float(x) for x in q["returns_m"])
        y0, y1, n, d = float(q["from_m"]), float(q["to_m"]), int(q["courses"]), float(q["proud_m"])
        if not 0.1 <= lo < hi <= 0.8 or a - hi < 0.05 or b + hi > run_len(run) - 0.05 or b - a < 0.3:
            raise ParamError(f"bays: {bid}.dress.quoins[{j}]: returns 0.1-0.8 m, short then long, that stop "
                             f"0.05 m short of the run's ends (0-{run_len(run):.3f} m) from jambs {a}-{b}")
        if not 0.0 < y0 < y1 <= top or not 0.12 <= (y1 - y0) / max(n, 1) <= 0.6 or not 0.01 <= d <= 0.05:
            raise ParamError(f"bays: {bid}.dress.quoins[{j}]: {n} courses of 0.12-0.6 m from {y0} to {y1} m "
                             f"inside the bay's wall (top {top:.2f} m), 0.01-0.05 m proud")
        quoins.append({"run": run, "jambs_m": (a, b), "from_m": y0, "to_m": y1, "returns_m": (lo, hi),
                       "courses": n, "proud_m": d})
    if quoins:
        out["quoins"] = tuple(quoins)
    rbs = []
    for j, q in enumerate(ds.get("run_bands") or ()):
        # T-2915: a band along one run of the plan, broken where `gaps_m` [from, to] stand (a
        # window and its arch's ring), so it stops against them as an impost course does
        need = {"run", "from_m", "to_m", "proud_m", "gaps_m"}
        if set(q) != need or not 0 <= int(q["run"]) < len(pts) - 1:
            raise ParamError(f"bays: {bid}.dress.run_bands[{j}] takes {sorted(need)}, on a run of its plan")
        run = int(q["run"])
        y0, y1, d = float(q["from_m"]), float(q["to_m"]), float(q["proud_m"])
        gaps = sorted(tuple(sorted(float(x) for x in g)) for g in q["gaps_m"])
        if not 0.0 < y0 < y1 <= top or y1 - y0 > 0.6 or not 0.01 <= d <= 0.1 \
                or any(not 0.0 < g0 < g1 <= run_len(run) + 1e-9 for g0, g1 in gaps) \
                or any(p_[1] >= n_[0] for p_, n_ in zip(gaps, gaps[1:])):
            raise ParamError(f"bays: {bid}.dress.run_bands[{j}] {q} is a band up to 0.6 m tall inside the bay's "
                             f"wall (top {top:.2f} m), 0.01-0.1 m proud, its gaps inside the run and apart")
        rbs.append({"run": run, "from_m": y0, "to_m": y1, "proud_m": d, "gaps_m": tuple(gaps)})
    if rbs:
        out["run_bands"] = tuple(rbs)
    blocks, bosses = [], []
    for j, q in enumerate(ds.get("blocks") or ()):
        # T-3091: a dressed block on one run of the plan, `s_m` [from, to] along it and `from_m`
        # to `to_m` over grade, `proud_m` before the wall (1812's projection, the Levy print: its
        # paired window's mullion carried up as a pier, the moulded hood over its sashes and the
        # carved caps its jambs rise to); `boss` raises an oval boss on its face, standing for
        # carving the build does not model, as the shields' (T-2915)
        need = {"run", "s_m", "from_m", "to_m", "proud_m"}
        if set(q) - {"boss"} != need or not 0 <= int(q["run"]) < len(pts) - 1:
            raise ParamError(f"bays: {bid}.dress.blocks[{j}] takes {sorted(need)} and an optional boss, on a "
                             f"run of its plan")
        run = int(q["run"])
        a, b = sorted(float(x) for x in q["s_m"])
        y0, y1, d = float(q["from_m"]), float(q["to_m"]), float(q["proud_m"])
        if not 0.0 <= a < b <= run_len(run) or b - a > 3.0 or not 0.0 < y0 < y1 <= top or y1 - y0 > 3.0 \
                or not 0.01 <= d <= 0.1:
            raise ParamError(f"bays: {bid}.dress.blocks[{j}] {q} is a block up to 3 m each way inside its run "
                             f"(0-{run_len(run):.3f} m) and the bay's wall (top {top:.2f} m), 0.01-0.1 m proud")
        blocks.append({"run": run, "s_m": (a, b), "from_m": y0, "to_m": y1, "proud_m": d})
        if q.get("boss"):
            bosses.append({"run": run, "s_m": (a + b) / 2, "y_m": (y0 + y1) / 2, "width_m": round(0.6 * (b - a), 4),
                           "height_m": round(0.6 * (y1 - y0), 4), "proud_m": round(d + 0.015, 4), "field": "boss"})
    if blocks:
        out["blocks"] = tuple(blocks)
    if bosses:
        out["ovals"] = tuple(out.get("ovals", ())) + tuple(bosses)
    if "volutes_m" in ds:
        rv, con = float(ds["volutes_m"]), (v.get("brackets") or {}).get("consoles")
        if con is None or not 0.02 <= rv <= min(0.15, con["drop_m"] / 4, con["reach_m"] / 3):
            raise ParamError(f"bays: {bid}'s dress.volutes_m {rv} rolls its consoles' ends, 0.02 m up to a "
                             f"quarter of their drop and a third of their reach")
        out["volutes"] = {"radius_m": rv, "reach_m": float(con["reach_m"]), "drop_m": float(con["drop_m"]),
                          "thickness_m": float(con["thickness_m"])}
    if "shutters" in ds:
        sh, wo = ds["shutters"], e.get("window_over")
        if wo is None or set(sh) != {"width_m", "to_m", "louvre_m"}:
            raise ParamError(f"bays: {bid}'s dress.shutters take width_m, to_m and louvre_m, at its window_over")
        ws, wh = float(wo["sill_m"]), float(wo["height_m"])
        w, y1, lv = float(sh["width_m"]), float(sh["to_m"]), float(sh["louvre_m"])
        if not 0.2 <= w <= float(wo["width_m"]) or not ws + 0.5 <= y1 <= ws + wh or not 0.03 <= lv <= 0.15:
            raise ParamError(f"bays: {bid}'s dress.shutters {sh}: each leaf 0.2 m up to the window's width, "
                             f"from its sill ({ws} m) to at most its crown, louvres 0.03-0.15 m")
        out["shutters"] = {"half_m": float(wo["width_m"]) / 2, "from_m": ws, "to_m": y1, "width_m": w,
                           "louvre_m": lv, **({"centre_m": float(wo["offset_m"])} if wo.get("offset_m") else {})}
    return out


def _rise_over_span(v) -> float:
    """T-2818: a K06 segmental head's rise over its span (k06_windows.rise_over_span)."""
    return float(v.get("rise_over_span", json.loads(WINDOW_KIT.read_text())["arch"]["segmental"]["working_rise_over_span"]))


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
        seg = ell = None
        for i in g["ops"]:
            o = openings[i]
            # T-2526: the door is K07's one round-headed hole, its spring a half span under its crown
            v = ({"bays": 1, **({"head": g.get("head", "segmental"), "rise_over_span": g["rise_over_span"]}
                                if g.get("rise_over_span") else {})}
                 if o.component == "k01.opening.door_leaf" else variants[kit[o.component]["variant"]])
            n, mull = int(v.get("bays", 1)), float(v.get("mullion_m", 0.0))
            bw = (o.width_m - mull * (n - 1)) / n
            # T-2818: a segmental head springs its rise under the crown, and each light's last
            # field is that rise (the crown over the spring, as a round head's radius is)
            rise = bw / 2
            if v.get("head") == "segmental":
                rise = bw * _rise_over_span(v)
                seg = {"radius_m": round((bw * bw / 4 + rise * rise) / (2 * rise), 5), "rise_m": round(rise, 5)}
            elif v.get("head") == "elliptical":   # T-3134: a half ellipse, its rise the upright semi-axis
                rise = bw * _rise_over_span(v)
                ell = {"rise_m": round(rise, 5)}
            for k in range(n):
                s0 = o.s_m - o.width_m / 2 + k * (bw + mull)
                lights.append((round(s0, 5), round(s0 + bw, 5), round(o.head_m - rise, 5), round(rise, 5), round(o.sill_m, 5)))
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
                    **({"extrados": g["extrados"], "ring_proud_m": g["ring_proud_m"]} if "extrados" in g else {}),
                    **({"segmental": seg} if seg else {}),
                    **({"elliptical": ell} if ell else {}),
                    **({"moulding": g["moulding"]} if g.get("moulding") else {})})
    blocks = sorted((g["cuts"][0], g["cuts"][-1], g["sill_m"], g["top_m"]) for g in out)
    for a, b in zip(blocks, blocks[1:]):
        if a[1] > b[0] and a[3] > b[2] and b[3] > a[2]:
            raise ParamError(f"two arched groups' blocks overlap at s {b[0]:.3f}")
    if blocks and (blocks[0][0] < 0.25 or blocks[-1][1] > width - 0.25):
        raise ParamError("an arched group's voussoir block runs within 0.25 m of a corner")
    belts = [tuple(float(y) for y in b) for b in dress.get("belts", [])]
    cb = dress.get("carved_band")
    if cb is not None:
        # T-2819: a carved band across the front at the arches' springing (1623's drawing):
        # a belt course from `bed_m` to `top_m`, cut by every light it crosses, the
        # oriel's guilloche (k08_bays._guilloche) carved along each run of it between them
        if set(cb) != {"bed_m", "top_m", "guilloche"} or \
                set(cb["guilloche"]) != {"radius_m", "ring_width_m", "ring_proud_m", "margin_m", "pitch", "segments"}:
            raise ParamError("street_front_dress.carved_band takes bed_m, top_m and a guilloche (radius_m, "
                             "ring_width_m, ring_proud_m, margin_m, pitch, segments)")
        b0, b1 = float(cb["bed_m"]), float(cb["top_m"])
        if not (pf < b0 and 0.15 <= b1 - b0 <= 0.6 and b1 <= floors[1] - 0.3):
            raise ParamError(f"street_front_dress.carved_band [{b0}, {b1}]: a band 0.15-0.6 m deep over the "
                             f"principal floor ({pf} m), 0.3 m clear of the second ({floors[1]} m)")
        if any(g["spring_m"] < b1 - 1e-6 < g["top_m"] for g in out):
            raise ParamError(f"street_front_dress.carved_band's top ({b1} m) runs into a voussoir block: "
                             f"the arches spring from the band, not under it")
        g_ = cb["guilloche"]
        if not 0.05 <= float(g_["radius_m"]) <= (b1 - b0) / 2 or not 0.0 < float(g_["ring_proud_m"]) <= 0.05:
            raise ParamError("street_front_dress.carved_band.guilloche: a ring at most half the band "
                             "high, standing at most 0.05 m")
        belts.append((b0, b1))
        cb = {"bed_m": b0, "top_m": b1, "guilloche": {k: float(v) for k, v in g_.items()}}
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
    gr = dress.get("grilles") or {}
    if gr.get("scrolls"):
        # T-2818: a band of scrolls over the uprights, from its foot bar to the lights' spring
        sc = gr["scrolls"]
        if set(sc) != {"count", "foot_m"} or not 2 <= int(sc["count"]) <= 12:
            raise ParamError("street_front_dress.grilles.scrolls takes count (2-12) and foot_m")
        for g in out:
            if g["component"] == gr["component"] and not (
                    g["sill_m"] + 0.3 <= float(sc["foot_m"]) <= g["spring_m"] - 0.15):
                raise ParamError(f"street_front_dress.grilles.scrolls.foot_m {sc['foot_m']} does not leave "
                                 f"0.3 m of uprights over the sill ({g['sill_m']}) and a 0.15 m band under the "
                                 f"spring ({g['spring_m']})")
    rails = dress.get("stoop_rails") or {}
    if rails and rails.get("kit") != "k11.rail.stoop_rail":
        raise ParamError("street_front_dress.stoop_rails are the K11 kit's k11.rail.stoop_rail")
    gd = rails.get("guard")
    if gd is not None:
        # T-2817: the landing's guard runs from the stoop's head along the landing to `to_v_m`,
        # an ornamental panel inside it (k01_arched_front._landing_guard)
        if set(gd) != {"to_v_m", "panel_v_m"} or len(gd["panel_v_m"]) != 2:
            raise ParamError("street_front_dress.stoop_rails.guard takes to_v_m and panel_v_m [from, to]")
        pa, pb = sorted(float(x) for x in gd["panel_v_m"])
        to = float(gd["to_v_m"])
        if not 0.1 <= to <= width - 0.05 or not 0.3 <= pb - pa <= 1.2:
            raise ParamError(f"street_front_dress.stoop_rails.guard: its end (v {to}) stands inside the front, "
                             f"its panel 0.3-1.2 m long")
        rails = {**rails, "guard": {"to_v_m": to, "panel_v_m": [pa, pb]}}
    return {"groups": tuple(out), "belts": tuple(belts), "stone_top_m": stone_top, "frieze": fr or {},
            "frontispiece": dress.get("frontispiece") or {}, "portico": po or {},
            "balconettes": dress.get("balconettes") or {}, "grilles": dress.get("grilles") or {},
            "stoop_rails": rails, "carved_band": cb or {},
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
    cbs = []
    for j, cb in enumerate(sfw.get("carved_bands") or ()):
        # T-2915: a carved belt on a named-window front (1812's photograph: a carved interlace
        # over the second storey's north window and a band of sunk panels over that): a belt
        # course from `bed_m` to `top_m`, carved from `s_m` [from, to] along the front (the
        # whole front unless named) with T-2819's guilloche, or with `panels`, rows of sunk
        # panels between raised ribs, each row's joints halfway along the row under it
        what = f"street_front_windows.carved_bands[{j}]"
        # T-3093: or with `interlace`, two straps crossing as a plait (1812's frieze, read at 3x:
        # crossing straps, where the guilloche's rings had stood for them)
        carving = set(cb) & {"guilloche", "panels", "interlace"}
        if len(carving) != 1 or set(cb) - {"s_m"} != {"bed_m", "top_m", *carving}:
            raise ParamError(f"{what} takes bed_m, top_m, an optional s_m [from, to] and one of guilloche, "
                             f"panels or interlace")
        if "belts" not in sfw:
            raise ParamError(f"{what}: a front with carved bands names its belts too, since they replace K01's two")
        b0, b1 = float(cb["bed_m"]), float(cb["top_m"])
        if not (floors[0] < b0 and 0.15 <= b1 - b0 <= 0.6):
            raise ParamError(f"{what} [{b0}, {b1}]: a band 0.15-0.6 m deep over the ground floor")
        for o in openings:
            if o.wall == "k01.wall.street_front" and o.sill_m < b1 - 1e-6 and o.head_m > b0 + 1e-6:
                raise ParamError(f"{what} [{b0}, {b1}] runs through {o.component} at s {o.s_m}")
        s0, s1 = (float(x) for x in cb.get("s_m", (0.0, width)))
        if not 0.0 <= s0 < s1 - 0.5 or s1 > width + 1e-6:
            raise ParamError(f"{what}.s_m [{s0}, {s1}] is not a run of at least 0.5 m along the {width} m front")
        band = {"bed_m": b0, "top_m": b1, "s_m": (s0, s1)}
        if "guilloche" in cb:
            g_ = cb["guilloche"]
            if set(g_) != {"radius_m", "ring_width_m", "ring_proud_m", "margin_m", "pitch", "segments"} \
                    or not 0.05 <= float(g_["radius_m"]) <= (b1 - b0) / 2 or not 0.0 < float(g_["ring_proud_m"]) <= 0.05:
                raise ParamError(f"{what}.guilloche takes radius_m (at most half the band), ring_width_m, "
                                 f"ring_proud_m (at most 0.05 m), margin_m, pitch and segments")
            band["guilloche"] = {k: float(v) for k, v in g_.items()}
        elif "interlace" in cb:
            il = cb["interlace"]
            if set(il) != {"strap_m", "proud_m", "margin_m", "wavelength_m", "segments"}:
                raise ParamError(f"{what}.interlace takes strap_m, proud_m, margin_m, wavelength_m and segments")
            st, pr, mg, wl, sg = (float(il["strap_m"]), float(il["proud_m"]), float(il["margin_m"]),
                                  float(il["wavelength_m"]), int(il["segments"]))
            if not 0.02 <= st <= (b1 - b0) / 4 or not 0.005 <= pr <= 0.05 or not 0.0 <= mg <= (b1 - b0) / 4 \
                    or not 0.2 <= wl <= s1 - s0 or not 4 <= sg <= 32:
                raise ParamError(f"{what}.interlace: straps 0.02 m up to a quarter of the band, 0.005-0.05 m proud, "
                                 f"a margin up to a quarter of the band, a wavelength 0.2 m up to the run and "
                                 f"4-32 segments a half wave")
            band["interlace"] = {"strap_m": st, "proud_m": pr, "margin_m": mg, "wavelength_m": wl, "segments": sg}
        else:
            pa = cb["panels"]
            if set(pa) != {"rows", "length_m", "rib_m", "proud_m"}:
                raise ParamError(f"{what}.panels takes rows, length_m, rib_m and proud_m")
            rows, ln, rib, pr = int(pa["rows"]), float(pa["length_m"]), float(pa["rib_m"]), float(pa["proud_m"])
            if not 1 <= rows <= 4 or not 0.15 <= ln <= 1.0 or not 0.015 <= rib <= (b1 - b0) / (3 * rows) \
                    or not 0.005 <= pr <= 0.04:
                raise ParamError(f"{what}.panels: 1-4 rows of panels 0.15-1.0 m long, ribs 0.015 m up to a third "
                                 f"of a row and 0.005-0.04 m proud")
            band["panels"] = {"rows": rows, "length_m": ln, "rib_m": rib, "proud_m": pr}
        cbs.append(band)
    if cbs:
        spans = sorted((b["bed_m"], b["top_m"]) for b in cbs)
        if any(a[1] > b[0] + 1e-6 for a, b in zip(spans, spans[1:])):
            raise ParamError("street_front_windows.carved_bands overlap")
        if any(b0 < c1 - 1e-6 and c0 < b1 - 1e-6 for b0, b1 in out.get("belts", ()) for c0, c1 in spans):
            raise ParamError("street_front_windows.carved_bands overlap its belts")
        out["carved_bands"] = tuple(cbs)
        # each is a belt course of the front's, laid with the rest
        out["belts"] = tuple(sorted(out.get("belts", ()) + tuple(spans)))
    return out


def _voussoirs(vs, k, variant, s, sill, h, sgr, overhang, eave) -> dict:
    """T-2889: a named street window's arch turned in voussoirs (1812 Prairie's photograph: a
    ring of dressed stones round each third-storey arch, a keystone at the crown): `ring_m`
    deep from the head's curve, `stones` of them (odd, the middle one the keystone), standing
    `proud_m` before the wall, the keystone `key_m` [width at its top, height over the crown].
    Where the ring rises past a shaped gable's foot it stands before the gable's face too."""
    what = f"street_front_windows.windows[{k}].voussoirs"
    if set(vs) - {"short_m"} != {"ring_m", "stones", "proud_m", "key_m"}:
        raise ParamError(f"{what} takes ring_m, stones, proud_m and key_m [width, height], and an optional "
                         f"short_m")
    if variant["head"] not in ("round", "segmental"):
        raise ParamError(f"{what}: a ring is turned over a round or segmental head, not a {variant['head']} one")
    ring, n, proud = float(vs["ring_m"]), int(vs["stones"]), float(vs["proud_m"])
    kw, kh = (float(x) for x in vs["key_m"])
    if not 0.15 <= ring <= 0.6 or n % 2 == 0 or not 5 <= n <= 25 or not 0.02 <= proud <= 0.15:
        raise ParamError(f"{what}: a 0.15-0.6 m ring of 5-25 stones (odd, the keystone in the middle), "
                         f"0.02-0.15 m proud")
    if not 0.15 <= kw <= 0.6 or not ring <= kh <= ring + 0.6:
        raise ParamError(f"{what}.key_m: a keystone 0.15-0.6 m across its top, rising at least the ring's depth "
                         f"and at most 0.6 m past it")
    # T-3091: long and short in turn into the walling (1812's, the Levy print): every other
    # stone, from the keystone's neighbours out, `short_m` deep where the rest are `ring_m`
    short = float(vs["short_m"]) if "short_m" in vs else None
    if short is not None and not 0.1 <= short <= ring - 0.05:
        raise ParamError(f"{what}.short_m: the short stones 0.1 m deep up to 0.05 m short of the ring ({ring} m)")
    top = sill + h + kh
    if sgr and top > float(sgr["foot_m"]):
        face = overhang + float(sgr["proud_m"])
        if proud < face + 0.02:
            raise ParamError(f"{what}: the ring rises past the gable's foot, so it stands at least 0.02 m "
                             f"before the gable's face ({face + 0.02:.2f} m proud)")
    elif top > eave - 0.05:
        raise ParamError(f"{what}: the keystone runs into the wall head")
    return {"s_m": round(s, 4), "sill_m": round(sill, 4), "ring_m": ring, "stones": n, "proud_m": proud,
            "key_m": (kw, kh), **({"short_m": short} if short is not None else {})}


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


def _loggia_carving(cv, w, h, floor) -> dict:
    """T-2923: the carving on both of a loggia's arches (1801's, the Taylor photograph), laid
    by k01_arched_front._loggia_carving: the archivolt's two stepped faces, `steps_m` broad
    and `proud_m` before the wall from the intrados out; a carved pier each side `off_m`
    outside the intrados and `width_m` broad, from the floor on a `base_m` base to a
    `capital_m` capital under `top_m`, a chain of `lozenge_m` [width, height] lozenges down
    its shaft; a `rosette_m` rosette in each spandrel; the stair's foot blocks carved
    (`foot_blocks`, panels `proud_m` before their faces) and the side arch's balcony face in
    `balcony_panels` panels."""
    need = {"archivolt", "piers", "rosette_m", "foot_blocks", "balcony_panels"}
    if not isinstance(cv, dict) or not need <= set(cv) <= need | {"frieze", "cartouche_band"} \
            or ("frieze" in cv) != ("cartouche_band" in cv):
        raise ParamError(f"entrance_kit.loggia.carving takes {sorted(need)}, and frieze with cartouche_band")
    av, pi = cv["archivolt"], cv["piers"]
    if set(av) != {"steps_m", "proud_m"} or len(av["steps_m"]) != 2 or len(av["proud_m"]) != 2:
        raise ParamError("entrance_kit.loggia.carving.archivolt takes steps_m [inner, outer] and proud_m [inner, outer]")
    (w1, w2), (p1, p2) = ((float(x) for x in av[k]) for k in ("steps_m", "proud_m"))
    if not (0.03 <= w1 <= 0.2 and 0.03 <= w2 <= 0.2 and 0.01 <= p1 < p2 <= 0.12):
        raise ParamError("entrance_kit.loggia.carving.archivolt: steps 0.03-0.2 m broad, the outer prouder, "
                         "at most 0.12 m")
    pneed = {"off_m", "width_m", "proud_m", "base_m", "capital_m", "top_m", "lozenge_m"}
    if set(pi) != pneed:
        raise ParamError(f"entrance_kit.loggia.carving.piers takes {sorted(pneed)}")
    off, pw, pp, bh, ch, top = (float(pi[k]) for k in ("off_m", "width_m", "proud_m", "base_m", "capital_m", "top_m"))
    wl, hl = (float(x) for x in pi["lozenge_m"])
    if not w1 + w2 + 0.02 <= off <= 0.6 or not 0.15 <= pw <= 0.5 or not 0.02 <= pp <= 0.1:
        raise ParamError("entrance_kit.loggia.carving.piers: clear of the archivolt and at most 0.6 m off the "
                         "intrados, 0.15-0.5 m broad, 0.02-0.1 m proud")
    if not floor + h + w1 + w2 + 0.05 <= top or not 0.1 <= bh <= 0.5 or not 0.08 <= ch <= 0.4 \
            or top - ch - (floor + bh) < 2 * hl or not 0.05 <= wl <= pw - 0.06 or not 0.08 <= hl <= 0.5:
        raise ParamError("entrance_kit.loggia.carving.piers: the capitals' top over the archivolt's crown, a "
                         "0.1-0.5 m base and 0.08-0.4 m capital, and lozenges narrower than the shaft, two "
                         "at least to it")
    rr = float(cv["rosette_m"])
    if not 0.04 <= rr <= 0.25:
        raise ParamError("entrance_kit.loggia.carving.rosette_m: a spandrel's rosette 0.04-0.25 m in radius")
    rho = w / 2 + w1 + w2 + rr + 0.05
    if rho * math.sqrt(0.5) + rr > w / 2 + off - 0.02 or floor + h - w / 2 + rho * math.sqrt(0.5) + rr > top - 0.02:
        raise ParamError("entrance_kit.loggia.carving.rosette_m: the spandrel's rosette runs into its pier or "
                         "the capitals' line")
    fb = cv["foot_blocks"]
    if not isinstance(fb, dict) or set(fb) != {"proud_m"} or not 0.005 <= float(fb["proud_m"]) <= 0.04:
        raise ParamError("entrance_kit.loggia.carving.foot_blocks takes proud_m, 0.005-0.04 m")
    nb = int(cv["balcony_panels"])
    if not 1 <= nb <= 8:
        raise ParamError("entrance_kit.loggia.carving.balcony_panels: 1-8 panels")
    out = {}
    if "frieze" in cv:
        # T-2932: the relief frieze on the capitals' line under a moulded course, and the
        # cartouche band from that course to `top_m`, under the second storey's sill
        fr, cb = cv["frieze"], cv["cartouche_band"]
        fneed = {"top_m", "proud_m", "course_m", "course_proud_m", "guilloche"}
        if set(fr) != fneed or set(cb) != {"top_m", "proud_m", "cartouche_m", "roundel_m"}:
            raise ParamError(f"entrance_kit.loggia.carving.frieze takes {sorted(fneed)}, and cartouche_band "
                             f"top_m, proud_m, cartouche_m [width, height] and roundel_m")
        ft, fp, cm, cp = (float(fr[k]) for k in ("top_m", "proud_m", "course_m", "course_proud_m"))
        g_ = fr["guilloche"]
        if not 0.3 <= ft - top <= 0.8 or not pp < fp < cp <= 0.2 or not 0.1 <= cm <= 0.3 or fp <= p2 \
                or set(g_) != {"radius_m", "ring_width_m", "ring_proud_m", "margin_m", "pitch", "segments"} \
                or not 0.05 <= float(g_["radius_m"]) <= (ft - top) / 2 or not 0.0 < float(g_["ring_proud_m"]) <= 0.05:
            raise ParamError("entrance_kit.loggia.carving.frieze: 0.3-0.8 m deep over the capitals, prouder than "
                             "the piers and the archivolt and under its 0.1-0.3 m course, and T-2819's guilloche "
                             "(radius_m at most half the frieze)")
        ct, cpk = float(cb["top_m"]), float(cb["proud_m"])
        cw, chh = (float(x) for x in cb["cartouche_m"])
        rr_ = float(cb["roundel_m"])
        if not 0.3 <= ct - ft - cm <= 1.0 or not 0.02 <= cpk < cp or not 0.2 <= chh <= ct - ft - cm - 0.06 \
                or not 0.2 <= cw <= 1.2 or not 0.04 <= rr_ <= chh / 2:
            raise ParamError("entrance_kit.loggia.carving.cartouche_band: 0.3-1.0 m deep over the course and "
                             "less proud than it, its cartouche inside it and its roundels no taller")
        out = {"frieze": {"top_m": ft, "proud_m": fp, "course_m": cm, "course_proud_m": cp,
                          "guilloche": {k: float(v) for k, v in g_.items()}},
               "cartouche_band": {"top_m": ct, "proud_m": cpk, "cartouche_m": [cw, chh], "roundel_m": rr_}}
    return {**out, "archivolt": {"steps_m": [w1, w2], "proud_m": [p1, p2]},
            "piers": {"off_m": off, "width_m": pw, "proud_m": pp, "base_m": bh, "capital_m": ch, "top_m": top,
                      "lozenge_m": [wl, hl]},
            "rosette_m": rr, "foot_blocks": {"proud_m": float(fb["proud_m"])}, "balcony_panels": nb}


def _loggia_columns(cl, w, h) -> dict:
    """T-2918: clustered shafts in the jambs of a loggia's mouth (1811's, the Inland Architect
    plate of 1888), laid by k01_arched_front._jamb_columns: each side a cluster of round
    shafts `radius_m` thick, their axes `proud_m` before the wall and `shafts_m` [left, right]
    off the intrados outward along the face, on one plinth a side `plinth_m` over the floor,
    each on a `base_m` base, under a flared carved capital `capital_m` deep whose abacus
    carries the arch at its springing."""
    need = {"shafts_m", "radius_m", "proud_m", "plinth_m", "base_m", "capital_m"}
    if not isinstance(cl, dict) or set(cl) != need:
        raise ParamError(f"entrance_kit.loggia.columns takes {sorted(need)}")
    rs, pr, ph, bh, ch = (float(cl[k]) for k in ("radius_m", "proud_m", "plinth_m", "base_m", "capital_m"))
    sh = cl["shafts_m"]
    if not isinstance(sh, list) or len(sh) != 2 or not all(isinstance(x, list) and 1 <= len(x) <= 4 for x in sh):
        raise ParamError("entrance_kit.loggia.columns.shafts_m is [left, right], one to four offsets a side")
    sides = [sorted(float(x) for x in side) for side in sh]
    if not 0.05 <= rs <= 0.2 or not 0.0 <= pr <= rs + 0.05:
        raise ParamError("entrance_kit.loggia.columns: shafts 0.05-0.2 m in radius, their axes at most a "
                         "radius and 0.05 m before the wall")
    for side in sides:
        if not -rs <= side[0] <= 0.3 or any(b - a < 2 * rs + 0.01 for a, b in zip(side, side[1:])) or side[-1] > 1.0:
            raise ParamError("entrance_kit.loggia.columns.shafts_m: a cluster from the intrados (at most a "
                             "radius inside it) out to 1.0 m, its shafts clear of each other")
    spring = h - w / 2
    if not 0.3 <= ph <= 1.2 or not 0.02 <= bh <= 0.15 or not 0.1 <= ch <= 0.4 or ph + bh + 0.5 > spring - ch:
        raise ParamError(f"entrance_kit.loggia.columns: a 0.3-1.2 m plinth, a 0.02-0.15 m base and a 0.1-0.4 m "
                         f"capital leave a shaft at least 0.5 m under the arch's springing ({spring:.2f} m "
                         f"over the floor)")
    return {"shafts_m": sides, "radius_m": rs, "proud_m": pr, "plinth_m": ph, "base_m": bh, "capital_m": ch}


def _round_arcade(ra, floor, spring, v0, v1, plinth) -> dict:
    """T-2991: the porch's arcade round a rounded corner (1811's, the Inland Architect plate of
    1888), laid by k01_frontage.round_arcade: a colonnette at each of `angles_deg` round the
    curve from the street front's tangent, standing as the mouth's columns stand (their radius,
    plinth, base and capital), on a dressed plinth band carried round the curve; and over each
    capital a round-headed light `clear_width_m` across, its sill the capital's abacus (the
    mouth's springing) and its crown `crown_m` over it, `reveal_m` deep into the porch's shadow.
    The plinth band under the colonnettes is `band_m` deep down from the mouth's plinth top. The
    corner and the loggia's end it stands beside are checked in from_phase."""
    need = {"angles_deg", "clear_width_m", "crown_m", "reveal_m", "band_m"}
    if not isinstance(ra, dict) or set(ra) - {"drops_m"} != need:
        raise ParamError(f"entrance_kit.loggia.round_arcade takes {sorted(need)} (and drops_m)")
    ang = ra["angles_deg"]
    if not isinstance(ang, list) or not 1 <= len(ang) <= 6 or any(not isinstance(x, (int, float)) for x in ang):
        raise ParamError("entrance_kit.loggia.round_arcade.angles_deg: one to six angles round the curve")
    ang = [float(x) for x in ang]
    if any(b <= a for a, b in zip(ang, ang[1:])) or not 0.0 <= ang[0] or not ang[-1] <= 75.0:
        raise ParamError(f"entrance_kit.loggia.round_arcade.angles_deg {ang}: rising from the front's tangent "
                         f"(0) to at most 75 degrees, short of the side wall")
    w, c, r = (float(ra[k]) for k in ("clear_width_m", "crown_m", "reveal_m"))
    if not 0.1 <= w <= 0.6 or not w / 2 + 0.2 <= c <= 1.5 or not 0.1 <= r <= 0.5:
        raise ParamError(f"entrance_kit.loggia.round_arcade: a light 0.1-0.6 m across ({w}), its crown "
                         f"{w / 2 + 0.2:.2f}-1.5 m over its sill ({c}), 0.1-0.5 m deep ({r})")
    b = float(ra["band_m"])
    if not 0.1 <= b <= plinth:
        raise ParamError(f"entrance_kit.loggia.round_arcade.band_m {b}: the plinth band 0.1 m deep at least, and "
                         f"no deeper than the mouth's {plinth} m plinth over the floor")
    out = {"angles_deg": ang, "clear_width_m": w, "crown_m": c, "reveal_m": r, "band_m": b,
           "floor_m": round(floor, 5), "sill_m": round(spring, 5), "v_m": [v0, v1]}
    # T-3129: each light and its colonnette stepped down by its own drop (1811's, as the 1888 plate
    # and the Chicagology photograph step them), never rising round the curve and at most 0.4 m
    if "drops_m" in ra:
        dr = ra["drops_m"]
        if not isinstance(dr, list) or len(dr) != len(ang) or any(not isinstance(x, (int, float)) for x in dr) \
                or any(not 0.0 <= x <= 0.4 for x in dr) or any(y < x for x, y in zip(dr, dr[1:])):
            raise ParamError(f"entrance_kit.loggia.round_arcade.drops_m {dr}: one drop a light (0-0.4 m), never "
                             f"rising round the curve")
        out["drops_m"] = [float(x) for x in dr]
    return out


def round_arcade_check(ra, rc, cl, width) -> None:
    """T-2991: a round arcade stands on a rounded corner, beside the loggia's end on that side
    (within ROUND_ARCADE_REACH_M of the round's tangent), its colonnettes and lights clear of
    each other along the curve and its last light's frame short of the side wall."""
    if not ra:
        return
    if not rc:
        raise ParamError("entrance_kit.loggia.round_arcade stands on a rounded corner (round_corner)")
    r = rc["radius_m"]
    v0, v1 = ra["v_m"]
    gap = (width - r) - v1 if rc["corner"] == "north" else v0 - r
    if not -1e-6 <= gap <= ROUND_ARCADE_REACH_M:
        raise ParamError(f"entrance_kit.loggia.round_arcade: the loggia (v {v0}-{v1}) ends {gap:.3f} m short of "
                         f"the {rc['corner']} round's tangent, where the arcade lights it from (at most "
                         f"{ROUND_ARCADE_REACH_M} m)")
    s = [r * math.radians(a) for a in ra["angles_deg"]]
    w = ra["clear_width_m"]
    if s[0] < w / 2 + 0.02 or any(b - a < max(2 * cl["radius_m"] + 0.01, w + 0.06) for a, b in zip(s, s[1:])):
        raise ParamError(f"entrance_kit.loggia.round_arcade: on the {r} m round its lights ({w} m) and colonnettes "
                         f"({cl['radius_m']} m) crowd each other or the front's tangent "
                         f"(at {[round(x, 3) for x in s]} m round the curve)")
    if s[-1] + w / 2 + ROUND_ARCADE_MARGIN_M > r * math.pi / 2 - 0.1:
        raise ParamError("entrance_kit.loggia.round_arcade: the last light's frame runs onto the side wall")


#: T-2991: how far the loggia's end may stand from the round's tangent and still be lit by the
#: arcade round it; and the dressed band's margin past its last light
ROUND_ARCADE_REACH_M = 0.6
ROUND_ARCADE_MARGIN_M = 0.12


def door_arch_of(entrance_kit) -> dict:
    """T-2526: the record's voussoir block round a round-headed door, or {}."""
    return dict(((entrance_kit or {}).get("k01.opening.door_leaf") or {}).get("arch") or {})


WING_SIDES = ("south", "north", "rear")
#: T-2900: the wall a wing has only where it runs past its host wall (`past_host`)
WING_FRONT = "front"
#: T-2900: how much of its host wall a wing longer than it still stands on, at the least
WING_HOST_MIN_M = 1.0
#: T-2417: what a wing's walls are made of — the K03 brick, or a frame wall in painted timber
WING_FABRICS = ("brick", "frame")
#: T-2417: a frame wing's wall, studs and boards, for its windows' reveals (a brick wing takes the side walls')
FRAME_WALL_M = 0.15


def wing_walls(w: dict) -> dict:
    """A rear wing's three outer walls, each as (origin, along) in the assembly's frame,
    +X east (u) and -Z north (v), read left to right from outside as the main walls are:
    south from the wing's rear end, north from its front end, the rear from its north end."""
    u0, u1, v0, v1 = w["rect"]
    walls = {"south": ((u0, 0.0, -v0), (1.0, 0.0, 0.0), u1 - u0),
             "north": ((u1, 0.0, -v1), (-1.0, 0.0, 0.0), u1 - u0),
             "rear": ((u0, 0.0, -v1), (0.0, 0.0, 1.0), v1 - v0)}
    # T-2900: a wing longer than its host wall has a front of its own where it runs past
    # the host, read from its south end; the host's span on it is drawn by the host
    if w.get("past_host"):
        walls["front"] = ((u1, 0.0, -v0), (0.0, 0.0, -1.0), v1 - v0)
    return walls


#: T-2841: what a wing is roofed with — K04's tin deck (T-2343), or a slated hip or gable
WING_ROOFS = ("flat", "hip", "gable")
#: T-2841: the sides a wing's gable may face; north or south runs the ridge along the
#: wing (v), so both of its flank walls carry a gable, and rear runs it across (u) into
#: the host wall, so the rear wall carries the one gable
WING_GABLE_SIDES = ("rear", "north", "south")


def _wing_pitched(wid, roof, kind, u0, u1, v0, v1, top) -> dict:
    """T-2841: a wing's hipped or gabled roof, resolved. Slated in a K04 slate read at its
    own pitch by K04's slate_exposure rule, as the main roof's is (`_k04`); its eaves are
    the deck's overhang and fascia; its gable named by the side it faces.

    The ridge runs across the wing (along u, into the host wall) for a gable to the rear
    and for a hip on a wing deeper than it is wide; otherwise along it (v), hipped or
    gabled at both flank walls, its front slope down to the host wall at the wing's wall
    top. `cover_m` is the roof's highest point on the host wall: the ridge where the ridge
    runs into it, the wall top where a slope comes down to it."""
    pitch = float(roof["pitch_deg"])
    lib = json.loads(K04.read_text())
    fabrics = {f["id"]: f for f in lib["fabrics"]}
    cov = roof.get("covering")
    if cov not in lib["slots"]["covering"] or fabrics[cov]["kind"] != "slate":
        raise ParamError(f"rear_wings: {wid}'s {kind} is covered in {cov!r}; a pitched K01 wing is slated "
                         f"in a K04 slate covering fabric")
    if not 25.0 <= pitch <= 60.0:
        raise ParamError(f"rear_wings: {wid}'s {kind} is pitched {pitch} deg, outside 25-60 (K04 slates "
                         f"nothing under 25 deg; a steeper face is a mansard's)")
    want = lib["profiles"]["slate_exposure"]["headlap_m"]["pitch_45_up" if pitch >= 45 else "pitch_25_to_45"]
    if fabrics[cov]["module"]["headlap_m"] < want - 1e-9:
        raise ParamError(f"rear_wings: {cov} is cut for a {fabrics[cov]['module']['headlap_m']} m headlap and "
                         f"{wid}'s {pitch} deg roof needs {want} m (k04 slate_exposure.headlap_m)")
    gable_to = roof.get("gable_to")
    if kind == "gable":
        if gable_to not in WING_GABLE_SIDES:
            raise ParamError(f"rear_wings: {wid}'s gable faces {gable_to!r}; name the side it faces "
                             f"({', '.join(WING_GABLE_SIDES)})")
        axis = "u" if gable_to == "rear" else "v"
    else:
        if gable_to is not None:
            raise ParamError(f"rear_wings: {wid} is hipped and has no gable to face {gable_to!r}")
        axis = "u" if u1 - u0 > v1 - v0 else "v"
    t = math.tan(math.radians(pitch))
    ridge = round(top + ((v1 - v0) if axis == "u" else (u1 - u0)) / 2 * t, 4)
    return {"kind": kind, "pitch_deg": pitch, "covering": cov, "axis": axis,
            **({"gable_to": gable_to} if kind == "gable" else {}),
            "ridge_m": ridge, "cover_m": ridge if axis == "u" else top}


def _rear_wings(entries, depth, width, openings, cw, ch, structure_id: str):
    """Resolve the record's `rear_wings` (T-2343): the ranges a sheet draws behind the main
    body, each a rectangle in the footprint frame whose front stands on the main rear wall
    (u = 0) or on the rear wall of a wing listed before it, inside that wall's length.

    A wing covers its host wall from grade to its deck: every host opening in that span
    below the deck is behind it and is not cut, and one that straddles a junction is
    refused, as a bay's. Its own windows are cut in its south, north and rear walls.
    T-2841: a hipped or gabled wing covers it to its roof's highest point on that wall
    (`_wing_pitched`), and the wall is drawn down to the wing's own wall top."""
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
        # T-2900: a wing may run on past its host wall's ends (1801's east range, the 1911
        # sheet's v 0-18.3 behind a gabled section 6 m wide) when the record says so; it
        # still stands on WING_HOST_MIN_M of that wall, and past it the wing has a front wall
        # of its own and its roof's eaves run round it
        past = ()
        if v0 < hv0 - 1e-9 or v1 > hv1 + 1e-9:
            if not e.get("past_host"):
                raise ParamError(f"rear_wings: {wid} runs v {v0}..{v1}, past its host wall's {hv0}..{hv1} "
                                 f"(a wing longer than its host wall says past_host)")
            if min(v1, hv1) - max(v0, hv0) < WING_HOST_MIN_M - 1e-9:
                raise ParamError(f"rear_wings: {wid} stands on {max(0.0, min(v1, hv1) - max(v0, hv0)):.2f} m of "
                                 f"its host wall's {hv0}..{hv1}, under the {WING_HOST_MIN_M} m a wing stands on")
            past = tuple((round(a, 4), round(b, 4)) for a, b in ((v0, min(v1, hv0)), (max(v0, hv1), v1))
                         if b - a > 1e-9)
        elif e.get("past_host"):
            raise ParamError(f"rear_wings: {wid} says past_host and runs v {v0}..{v1}, inside its host "
                             f"wall's {hv0}..{hv1}")
        heights = tuple(float(h) for h in e["storey_heights_m"])
        floor = float(e["floor_m"])
        floors, y = [], floor
        for h in heights:
            floors.append(round(y, 4))
            y += h
        top = round(y, 4)
        roof = e["roof"]
        kind = roof.get("kind")
        if kind not in WING_ROOFS:
            raise ParamError(f"rear_wings: {wid}'s roof is a {kind}; a K01 wing is decked flat, hipped or "
                             f"gabled ({', '.join(WING_ROOFS)})")
        ov, fas = float(roof["overhang_m"]), float(roof["fascia_m"])
        if not (0.0 <= ov <= 0.6 and 0.1 <= fas <= 0.5):
            raise ParamError(f"rear_wings: {wid}'s deck overhangs {ov} m on a {fas} m fascia, outside "
                             f"0-0.6 m and 0.1-0.5 m")
        if kind == "flat":
            if roof.get("covering") != "painted_tin_sheet":
                raise ParamError(f"rear_wings: {wid}'s deck is covered in {roof.get('covering')!r}; a K01 wing "
                                 f"deck is K04's painted_tin_sheet")
            pitched = None
            deck = cover = round(top + fas, 4)
        else:
            # T-2841: a hipped or gabled wing, slated. What its plan and its gable say fixes the
            # ridge: across the wing (along u) it dies into the host wall, along it (v) the front
            # slope comes down to the host wall at the wing's own wall top
            pitched = _wing_pitched(wid, roof, kind, u0, u1, v0, v1, top)
            # the host wall is drawn down to the wing's wall top, the roof dying into it; a host
            # light is behind the wing up to the roof's highest point on that wall
            deck, cover = top, pitched["cover_m"]
        sash = e["sash_by_storey"]
        if len(sash) != len(heights):
            raise ParamError(f"rear_wings: {wid}'s sash_by_storey needs one row per storey")
        walls = wing_walls({"rect": (u0, u1, v0, v1), "past_host": past})
        ops = []
        # T-3133: the sides whose lights a picture draws round-headed (1811's south flank on the
        # c. 1888 Chicagology photograph), cut as one round hole under K06's arch band, and the
        # round-headed basement lights it draws under each of them, plain, below the first floor
        rheads = tuple(e.get("round_heads") or ())
        bls = e.get("basement_lights") or {}
        for side in (*rheads, *bls):
            if side not in (e.get("windows") or {}):
                raise ParamError(f"rear_wings: {wid}'s round_heads and basement_lights name a side whose "
                                 f"windows it lists, not {side!r}")
        for side, ss in sorted((e.get("windows") or {}).items()):
            if side not in walls:
                raise ParamError(f"rear_wings: {wid} has no {side} wall ({', '.join(walls)})")
            length = walls[side][2]
            bl = bls.get(side)
            if bl is not None:
                if set(bl) != {"sill_m", "width_m", "height_m"}:
                    raise ParamError(f"rear_wings: {wid}'s basement_lights.{side} takes sill_m, width_m and height_m")
                bs, bw, bh = (float(bl[k]) for k in ("sill_m", "width_m", "height_m"))
                first = floors[0] + float(sash[0]["sill_above_floor_m"])
                if not 0.5 <= bw <= cw[1] or bs < 0.15 or bh < bw / 2 + 0.2 or bs + bh + 0.45 > first:
                    raise ParamError(f"rear_wings: {wid}'s basement_lights.{side} stand 0.5-{cw[1]} m across, "
                                     f"their sill at least 0.15 m up, their spring 0.2 m over it and their crown "
                                     f"0.45 m under the first floor's sills at {first:.2f} m")
                for s in ss:
                    s = float(s)
                    if s - bw / 2 < 0.30 or s + bw / 2 > length - 0.30:
                        raise ParamError(f"rear_wings: {wid}'s {side} basement light at s {s} stands closer "
                                         f"than 0.30 m to a corner of its {length:.3f} m wall")
                    ops.append(Opening(ROUND_PLAIN, f"k01.wall.wing.{wid}.{side}", s, round(bs, 4), bw, bh,
                                       False, plain=True, narrow=bw < cw[0]))
            comp = ROUND_HOODED if side in rheads else "k01.opening.sash_flat"
            for k, row in enumerate(sash):
                sill = floors[k] + float(row["sill_above_floor_m"])
                w_, h_ = float(row["width_m"]), float(row["height_m"])
                _within(w_, cw, f"rear_wings.{wid}.sash_by_storey[{k}].width_m")
                _within(h_, ch, f"rear_wings.{wid}.sash_by_storey[{k}].height_m")
                if sill + h_ + 0.30 > top:
                    raise ParamError(f"rear_wings: {wid}'s storey {k} heads run into its deck")
                if comp == ROUND_HOODED and h_ < w_ / 2 + 0.3:
                    raise ParamError(f"rear_wings: {wid}'s round-headed {side} lights in storey {k} spring "
                                     f"under 0.3 m over their sills")
                for s in ss:
                    s = float(s)
                    if s - w_ / 2 < 0.30 or s + w_ / 2 > length - 0.30:
                        raise ParamError(f"rear_wings: {wid}'s {side} window at s {s} stands closer than "
                                         f"0.30 m to a corner of its {length:.3f} m wall")
                    # T-2900: a front's lights stand in the stretches past the host, clear of it
                    if side == WING_FRONT and not any(a - v0 + 0.30 <= s - w_ / 2 and s + w_ / 2 <= b - v0 - 0.30
                                                      for a, b in past):
                        raise ParamError(f"rear_wings: {wid}'s front window at s {s} is not 0.30 m clear inside "
                                         f"the stretches past its host wall {[(a - v0, b - v0) for a, b in past]}")
                    ops.append(Opening(comp, f"k01.wall.wing.{wid}.{side}", s,
                                       round(sill, 4), w_, h_, comp != ROUND_HOODED))
        # what the wing covers of its host wall: s along that wall, from its left end
        # (T-2900: of a wing longer than it, the host wall's whole length it stands on)
        a, b = hv1 - min(v1, hv1), hv1 - max(v0, hv0)
        pool = openings if host is None else list(host["openings"])
        for o in list(pool):
            if o.wall != hwall:
                continue
            o0, o1 = o.s_m - o.width_m / 2 - 0.12, o.s_m + o.width_m / 2 + 0.12   # the head's horns
            if o1 <= a or o0 >= b or o.sill_m - 0.15 >= cover:
                continue
            if o0 < a or o1 > b:
                raise ParamError(f"rear_wings: {wid}'s junction at s {a:.3f}..{b:.3f} cuts the opening at "
                                 f"s {o.s_m} on {o.wall}")
            pool.remove(o)
        if host is not None:
            host["openings"] = tuple(pool)
        out.append({"id": wid, "fabric": fabric, "rect": (u0, u1, v0, v1), "host_wall": hwall, "host_span_m": (round(a, 4), round(b, 4)),
                    "floors_m": tuple(floors), "top_m": top, "deck_m": deck, "overhang_m": ov, "fascia_m": fas,
                    "host_v_m": (hv0, hv1), "openings": tuple(ops), "roof": pitched or {"kind": "flat"},
                    **({"past_host": past} if past else {})})
    slates = {w["roof"]["covering"] for w in out if w["roof"]["kind"] != "flat"}
    if len(slates) > 1:
        raise ParamError(f"rear_wings: the wings are slated in {', '.join(sorted(slates))}; a K01 house's "
                         f"wings share one slate (the assembly's wing_slate)")
    return tuple(out)


def _gable_walls(roof) -> set:
    """T-2841's gable ends on a wing: its rear wall, or both flank walls."""
    if roof.get("kind") != "gable":
        return set()
    return {"rear"} if roof["gable_to"] == "rear" else {"north", "south"}


def _wing_towers(entries, wings, structure_id: str, front_stone: bool, overhang: float):
    """T-2842: K08 towers on a rear wing's south, north or rear wall (k01.wall.wing.<id>.<side>),
    the kit piece 1801 Prairie's north-east turret on its east range needs. Each is resolved
    by `_bays` against that wing as a main-wall tower is against the house: its wall length,
    its floors and its wall top in the main eave's place, so it rises TOWER_PAST_EAVE_M past
    the wing's own eave with its cap whole over the wing's roof, and the wing's lights behind
    it are dropped; the wing's eave is not cut for it and runs into its ring, as the main
    eave does. T-3001: a full-height projection too, standing to the wing's wall top with its
    gable over it (1801's gabled section); T-1890: an oriel too, on one of the wing's floors
    (that section's round oriel); a bay on a wing is still the main walls' kit.
    Refused where the wing's walling stands in the tower's back above its wall top (a gable
    end), and where a later wing stands on the same stretch of the wall."""
    wings = list(wings)
    at = {f"k01.wall.wing.{w['id']}.{side}": (j, side) for j, w in enumerate(wings) for side in WING_SIDES}
    kinds = {v["id"]: v["kind"] for v in json.loads(BAY_KIT.read_text())["variants"]}
    out = []
    for e in entries:
        if e["wall"] not in at:
            raise ParamError(f"bays: {e['wall']} is not a wall of one of this house's rear wings")
        # T-3001: or a full-height projection, to the wing's own wall top (1801's gabled
        # section on 18th Street, its coped gable and balcony over a shallow pavilion as the
        # front's south one is, in the Taylor photograph); a bay or an oriel still is not
        # T-1890: or an oriel on its corbels from one of the wing's floors, its wall top under the
        # wing's as a main-wall oriel's is under the main eave (1801's gabled section, its round
        # oriel on the shallow pavilion's face)
        kind = kinds.get(e["variant"])
        if kind not in ("tower", "oriel") and e["variant"] != "k08.projection.full_height":
            raise ParamError(f"bays: {e['id']} is a {kind or e['variant']} on {e['wall']}; a "
                             f"rear wing's wall carries a K08 tower, past the wing's eave, a full-height "
                             f"projection or an oriel")
        j, side = at[e["wall"]]
        w = wings[j]
        if side in _gable_walls(w["roof"]):
            raise ParamError(f"bays: {e['id']} stands on {e['wall']}, a gable end: the gable's walling rises "
                             f"where the tower's back is closed over the wing's wall top")
        ops = list(w["openings"])
        (b,) = _bays([e], {e["wall"]: wing_walls(w)[side][2]}, ops, structure_id, front_stone,
                     tuple(w["floors_m"]), w["top_m"], overhang, wing_corner=True)
        for x in wings:
            if x["host_wall"] == e["wall"] and x["host_span_m"][0] < b["span_m"][1] + BAY_PIER_M \
                    and b["span_m"][0] - BAY_PIER_M < x["host_span_m"][1]:
                raise ParamError(f"bays: {e['id']} meets {e['wall']} at s {b['span_m'][0]}..{b['span_m'][1]}, "
                                 f"within {BAY_PIER_M} m of where {x['id']} stands on it")
        wings[j] = {**w, "openings": tuple(ops)}
        out.append({**b, "wing": w["id"], "eave_m": w["top_m"]})
    return tuple(wings), tuple(out)

#: T-3006: the corners a front block may round, each named by the side wall it turns into
ROUND_CORNERS = ("north", "south")


def round_corner_spans(rc: dict, depth: float, width: float) -> dict:
    """T-3006: where a rounded corner stands: each wall's span (s0, s1) the round replaces,
    and its centre in the footprint (u, v). The round's faces are tangent to the street
    front and to the side wall it turns into, `radius_m` in from the square corner."""
    r = rc["radius_m"]
    if rc["corner"] == "north":   # the front's far end, s = width, into the north wall's start
        return {"centre": (depth - r, width - r),
                "walls": {"k01.wall.street_front": (width - r, width), "k01.wall.side.north": (0.0, r)}}
    return {"centre": (depth - r, r),   # the front's start, s = 0, into the south wall's end
            "walls": {"k01.wall.street_front": (0.0, r), "k01.wall.side.south": (depth - r, depth)}}


#: T-3186: the wall a canted corner's face is (`cant_corner`)
CANT_WALL = "k01.wall.cant"
#: ...cut this far back along each wall at the least and the most (1901's south-west corner,
#: about 1.83 m each way through the Chicagology south-west photograph's camera)
CANT_CUT_M = (1.0, 2.5)
#: ...with a window on either wall it cuts standing at least this far clear of the cut
CANT_PIER_M = 0.2


def cant_corner_plan(cc: dict, depth: float, width: float) -> dict:
    """T-3186: where a canted corner stands: each wall's span (s0, s1) it cuts away, the canted
    face's two ends in the footprint (u, v) in the order a run round the house meets them (the
    street front's end and the north wall's start, or the south wall's end and the front's
    start), and the face's outward unit normal (nu, nv)."""
    c, h = cc["cut_m"], math.sqrt(0.5)
    if cc["corner"] == "north":   # the front's far end, s = width, into the north wall's start
        return {"walls": {"k01.wall.street_front": (width - c, width), "k01.wall.side.north": (0.0, c)},
                "ends": ((depth, width - c), (depth - c, width)), "normal": (h, h)}
    return {"walls": {"k01.wall.street_front": (0.0, c), "k01.wall.side.south": (depth - c, depth)},
            "ends": ((depth - c, 0.0), (depth, c)), "normal": (h, -h)}


def cant_ring(ring, cc: dict, depth: float, width: float, out: float):
    """T-3186: a K05 ring of four (x, z) corners (k05_roofs.inset_rect's order) cut on the
    canted face's line moved `out` out from the wall plane: the corner replaced by the two
    points where that line crosses its sides, or doubled where the line misses it, so every
    ring keeps five points and a ring stack's faces stay planar."""
    (u0, v0), (u1, v1) = cant_corner_plan(cc, depth, width)["ends"]
    nu, nv = cant_corner_plan(cc, depth, width)["normal"]
    nx, nz = nu, -nv                                  # the plan's (x, z) = (u, -v)
    k = nx * u0 + nz * -v0 + out
    i = 1 if cc["corner"] == "north" else 2           # inset_rect: (xb, za) or (xb, zb)
    cx, cz = ring[i]
    if nx * cx + nz * cz <= k + 1e-9:
        return ring[:i] + [ring[i], ring[i]] + ring[i + 1:]
    a = (cx, (k - nx * cx) / nz)                      # on the side x = cx
    b = ((k - nz * cz) / nx, cz)                      # on the side z = cz
    pair = [b, a] if cc["corner"] == "north" else [a, b]
    return ring[:i] + pair + ring[i + 1:]


def _cant_corner(cc, depth, width, openings, bays, rainwater, chimneys, *, construction, roof_form,
                 mansard, wall_head, others, floors, sash, basement) -> dict:
    """T-3186: a corner of the main body cut on a canted face from grade to the roof (1901's
    south-west corner, K01's 'north', in both Chicagology photographs: the face square to the
    corner, its own window column on both storeys, the cornice and the mansard carried round
    it). The face is a wall of its own (`CANT_WALL`), laid in the front's stone on its beds
    with a window at its middle in every storey and a basement light under them; the front
    and the side wall stop where it begins; the mansard's rings, its cornice, its gutter and
    the deck's cresting are cut on its line. Nothing else may stand on the walls it cuts."""
    if not cc:
        return {}
    if not isinstance(cc, dict) or set(cc) != {"corner", "cut_m"} or cc["corner"] not in ROUND_CORNERS:
        raise ParamError(f"cant_corner takes corner ({' or '.join(ROUND_CORNERS)}) and cut_m, not {cc}")
    c = float(cc["cut_m"])
    if not CANT_CUT_M[0] <= c <= min(CANT_CUT_M[1], width / 4, depth / 4):
        raise ParamError(f"cant_corner.cut_m {c}: {CANT_CUT_M[0]}-{CANT_CUT_M[1]} m and at most a quarter "
                         f"of the main body's width and depth")
    if construction != "stone":
        raise ParamError("cant_corner is laid on the front's beds round an all-stone house (construction: stone)")
    if roof_form != "mansard" or not mansard or mansard.get("crown") or mansard.get("straight") \
            or mansard.get("side_parapet"):
        raise ParamError("cant_corner cuts a plain mansard's rings: not a hip, a gable or a flat roof, nor a "
                         "crown, a straight wall or a side parapet")
    if (mansard.get("deck") or {}).keys() & {"finials", "hoods"}:
        raise ParamError("cant_corner: the deck's finials and corner hoods stand on its square corners")
    walls = wall_head.get("walls") or []
    side = "k01.wall.side.north" if cc["corner"] == "north" else "k01.wall.side.south"
    if wall_head.get("cornice") != "k10.cornice.moulded_stone" or not {"k01.wall.street_front", side} <= set(walls):
        raise ParamError(f"cant_corner carries the moulded stone cornice round it: wall_head names "
                         f"k10.cornice.moulded_stone on the street front and {side}")
    clash = [k for k, v in others.items() if v]
    if clash:
        raise ParamError(f"cant_corner cuts the corner {', '.join(clash)} would stand on")
    out = {"corner": cc["corner"], "cut_m": c}
    plan = cant_corner_plan(out, depth, width)
    for wall, (s0, s1) in plan["walls"].items():
        lo, hi = s0 - CANT_PIER_M, s1 + CANT_PIER_M
        for o in openings:
            if o.wall == wall and o.s_m + o.width_m / 2 > lo and o.s_m - o.width_m / 2 < hi:
                raise ParamError(f"cant_corner {cc['corner']}: {o.component} at s {o.s_m} on {wall} stands "
                                 f"within {CANT_PIER_M} m of the cut")
        for b in bays:
            if b["wall"] == wall and b["span_m"][1] > s0 - 1e-6 and b["span_m"][0] < s1 + 1e-6:
                raise ParamError(f"cant_corner {cc['corner']}: the bay {b['id']} on {wall} stands on the cut")
        for x in (rainwater or {}).get("downpipes", []):
            if x["wall"] == wall and s0 - 0.3 < x["s_m"] < s1 + 0.3:
                raise ParamError(f"cant_corner {cc['corner']}: the downpipe at s {x['s_m']} on {wall} stands on the cut")
    if (rainwater or {}).get("front_pipes"):
        raise ParamError("cant_corner: a front pipe has no head on a cut corner's gutter")
    for d in mansard.get("dormers") or ():
        if d["face"] == "street" and (d["along_m"] > width - c - 0.5 if cc["corner"] == "north"
                                      else d["along_m"] < c + 0.5):
            raise ParamError(f"cant_corner: the street dormer at {d['along_m']} m stands over the cut")
    (u0, v0), _ = plan["ends"]
    nu, nv = plan["normal"]
    for ch in chimneys:
        reach = math.hypot(*ch["plan_m"]) / 2 + 0.1
        if nu * ch["u_m"] + nv * ch["v_m"] > nu * u0 + nv * v0 - reach:
            raise ParamError(f"cant_corner: the stack at ({ch['u_m']}, {ch['v_m']}) stands on the cut")
    # the face's own column: a window at its middle in every storey, the storey's sash, and the
    # basement's light under them, each with a pier either side of it
    L = c * math.sqrt(2.0)
    mid = round(L / 2, 4)
    for k, row in enumerate(sash):
        w, h = float(row["width_m"]), float(row["height_m"])
        if w + 2 * CANT_PIER_M > L:
            raise ParamError(f"cant_corner: storey {k}'s sash, {w} m, leaves no pier on a {L:.2f} m face")
        openings.append(Opening("k01.opening.sash_flat", CANT_WALL, mid,
                                round(floors[k] + float(row["sill_above_floor_m"]), 4), w, h))
    if basement:
        openings.append(Opening("k01.opening.area_light", CANT_WALL, mid, float(basement.get("sill_m", 0.0)),
                                float(basement["width_m"]), float(basement["height_m"]), False))
    out["face_m"] = round(L, 4)
    return out


def chamfer_of(b: dict):
    """T-3048: a shallow pavilion's chamfered corner, or None: (corner, along_m, behind_m,
    cross_m), cross_m how far in from the corner its canted face crosses the wall's face."""
    v = b["variant"]
    side = v["plan"].get("side_end") if v["plan"]["kind"] == "polyline" else None
    if not side:
        return None
    pts = v["plan"]["points"]
    (fx, d), (bx, zb) = (pts[2], pts[3]) if side == "right" else (pts[1], pts[0])
    along, behind = abs(bx - fx), -zb
    return side, along, behind, along * behind / (d + behind)


def chamfer_spans(bays, depth: float, width: float) -> dict:
    """T-3048: each wall's span (s0, s1) a chamfered pavilion's corner cuts from the house: the
    street front's from where the canted face crosses it to the corner, and the side wall's
    from the corner back to where the face meets it, `behind_m` behind the front."""
    out = {}
    for b in bays:
        ch = chamfer_of(b) if b["wall"] == "k01.wall.street_front" else None
        if ch is None:
            continue
        side, _, behind, cross = ch
        if side == "right":   # the front's far end, s = width, into the north wall's start
            out["k01.wall.street_front"] = (width - cross, width)
            out["k01.wall.side.north"] = (0.0, behind)
        else:
            out["k01.wall.street_front"] = (0.0, cross)
            out["k01.wall.side.south"] = (depth - behind, depth)
    return out


#: T-3007: how far an oriel's junction on the wall plane may stand off a round corner's curve
ROUND_ORIEL_GAP_M = 0.3


def round_corner_gap(rc: dict, depth: float, width: float, b: dict):
    """T-3007: an oriel on the street front reaching onto a rounded corner (1811's, its south
    return carried back to the round on the 1888 plate): (s0, s1, gap) — the stretch of the
    wall plane its back stands over the round, from the round's tangent to its junction, and
    how far that junction stands off the curve — or None where it may not: it must stand on
    the flat front as well, its junction short of the side wall's plane by BAY_PIER_M and
    within ROUND_ORIEL_GAP_M of the curve. Its back over that stretch is closed on the plane
    (k01_frontage.bay, `back_over`), since the round falls away behind it."""
    r = rc["radius_m"]
    (cu, cv), (s0, s1) = round_corner_spans(rc, depth, width)["centre"], \
        round_corner_spans(rc, depth, width)["walls"]["k01.wall.street_front"]
    a, e = b["span_m"]
    end = e if rc["corner"] == "north" else a
    if b["wall"] != "k01.wall.street_front" or (rc["corner"] == "north" and not a < s0 - 1e-6 < e) \
            or (rc["corner"] == "south" and not a < s1 + 1e-6 < e):
        return None
    d = abs(end - cv)
    if d > r - BAY_PIER_M:
        return None
    gap = depth - (cu + math.sqrt(r * r - d * d))
    if gap > ROUND_ORIEL_GAP_M + 1e-9:
        return None
    return (s0, end, round(gap, 4)) if rc["corner"] == "north" else (end, s1, round(gap, 4))


FRONT_PIER_KEYS = {"to_m", "band_m", "cap_m", "band_proud_m", "cap_proud_m", "weathering_pitch_deg"}


def _front_pier(fp, stone, openings, bays, rainwater, round_corner, roof_form, mansard, eave) -> dict:
    """T-3112: the street front's low-s end (s 0 to `to_m`) stood as a PIER of the front's
    stone, coursed from grade in its own unbroken courses (no belt across it), stopped under
    the wall head by a dressed band (`band_m`, its bed and top) and a moulded cap (`cap_m`),
    each proud of the pier's faces and returned along the side wall; over the cap a slate
    weathering rising back from the cap's front at `weathering_pitch_deg`, the street front,
    its cornice and the roof's eaves cut back over the pier to that slope. 1811 Prairie's,
    where its 1888 plate, the Chicagology photograph and the 1965 HABS photograph all cap the
    pier below the bay's cornice with sky over it. Empty for every other house."""
    if not fp:
        return {}
    if set(fp) != FRONT_PIER_KEYS:
        raise ParamError(f"front_pier takes {sorted(FRONT_PIER_KEYS)}, not {sorted(fp)}")
    if not stone:
        raise ParamError("front_pier is laid in the front's stone: it needs a stone_front")
    if mansard or roof_form not in ("hip", "gable"):
        raise ParamError("front_pier cuts a hip's or a gable's eave back over it, not a mansard's or a flat roof's")
    if round_corner and round_corner.get("corner") == "south":
        raise ParamError("front_pier stands at the front's low-s end, where round_corner south would round it")
    to = float(fp["to_m"])
    (b0, b1), (c0, c1) = (tuple(float(x) for x in fp[k]) for k in ("band_m", "cap_m"))
    bp, cp, pitch = float(fp["band_proud_m"]), float(fp["cap_proud_m"]), float(fp["weathering_pitch_deg"])
    if not 0.5 <= to <= 1.5:
        raise ParamError(f"front_pier.to_m {to}: a pier 0.5-1.5 m wide at the front's low-s end")
    if not (3.0 <= b0 and 0.08 <= b1 - b0 <= 0.3 and b1 + 0.1 <= c0 and 0.1 <= c1 - c0 <= 0.4 and c1 <= eave - 0.8):
        raise ParamError(f"front_pier: the band {b0}-{b1} m (0.08-0.3 m deep, from 3 m up) stands 0.1 m or more "
                         f"under the cap {c0}-{c1} m (0.1-0.4 m deep), its top 0.8 m or more under the eave {eave}")
    if not (0.02 <= bp <= 0.1 and bp + 0.03 <= cp <= 0.25):
        raise ParamError(f"front_pier: the band 0.02-0.1 m proud ({bp}), the cap 0.03 m prouder, at most 0.25 ({cp})")
    if not 15.0 <= pitch <= 45.0:
        raise ParamError(f"front_pier.weathering_pitch_deg {pitch}: 15-45 deg")
    for b in bays:
        if b["wall"] == "k01.wall.street_front" and b["span_m"][0] < to - 1e-6:
            raise ParamError(f"front_pier to {to} m: the bay {b['id']} stands on it from s {b['span_m'][0]}")
    for o in openings:
        if o.wall == "k01.wall.street_front" and o.s_m - o.width_m / 2 < to + 0.1:
            raise ParamError(f"front_pier to {to} m: {o.component} at s {o.s_m} is cut into it")
    for x in (rainwater or {}).get("front_pipes", []):
        if x.get("on") != "return" and x["s_m"] < to and x["head_m"] > b0 - 0.01:
            raise ParamError(f"rainwater.front_pipes {x}: a pipe down the pier has its head under the band at {b0}")
    return {"to_m": to, "band_m": (b0, b1), "cap_m": (c0, c1), "band_proud_m": bp, "cap_proud_m": cp,
            "weathering_pitch_deg": pitch}


def _round_corner(rc, depth, width, stone, openings, bays, rainwater, *, side_belts, frontispiece) -> dict:
    """T-3006: a corner of the front block rounded on a radius from grade (1811's south corner
    on the 1888 plate, K01's 'north'), laid in the front's own stone and corbelled out to the
    square under the wall head, so the cornice, the eave and the gable end stand on the square
    corner as before. Nothing else may stand on the walls it replaces."""
    if not rc:
        return {}
    if not isinstance(rc, dict) or set(rc) != {"corner", "radius_m"} or rc["corner"] not in ROUND_CORNERS:
        raise ParamError(f"round_corner takes corner ({' or '.join(ROUND_CORNERS)}) and radius_m, not {rc}")
    r = float(rc["radius_m"])
    if not stone:
        raise ParamError("round_corner is laid in the front's stone: it needs a stone_front")
    if stone.get("brick_above_m") is not None or frontispiece:
        raise ParamError("round_corner is coursed on the front's own beds: not with brick_above_m or a frontispiece")
    if rc["corner"] == "south" and (stone["corners"] or "south_return_m" in stone):
        raise ParamError("round_corner south: the south corner is quoined or returned (corner_bond, south_return_m)")
    if not 0.3 <= r <= min(1.5, width / 4, depth / 4):
        raise ParamError(f"round_corner.radius_m {r}: 0.3-1.5 m and at most a quarter of the front block's "
                         f"width and depth")
    out = {"corner": rc["corner"], "radius_m": r}
    spans = round_corner_spans(out, depth, width)["walls"]
    for wall, (s0, s1) in spans.items():
        for o in openings:
            if o.wall == wall and o.s_m + o.width_m / 2 > s0 - 0.05 and o.s_m - o.width_m / 2 < s1 + 0.05:
                raise ParamError(f"round_corner {rc['corner']}: {o.component} at s {o.s_m} on {wall} stands on the round")
        for b in bays:
            if b["wall"] == wall and b["span_m"][1] > s0 - 1e-6 and b["span_m"][0] < s1 + 1e-6:
                if b["variant"]["kind"] == "oriel" and round_corner_gap(out, depth, width, b) is not None:
                    continue   # T-3007: an oriel carried out over the round (k01_frontage.bay closes its back)
                raise ParamError(f"round_corner {rc['corner']}: the bay {b['id']} on {wall} stands on the round"
                                 f"{'' if b['variant']['kind'] != 'oriel' else f' (an oriel may reach onto it from the flat front, its junction within {ROUND_ORIEL_GAP_M} m of the curve)'}")
        if any(sb.get("wall") == wall for sb in side_belts):
            raise ParamError(f"round_corner {rc['corner']}: a side belt runs on {wall} into the round")
    # a pipe on the round stands behind the front's plane, as far off the curve as a front
    # pipe stands off the front (K04's offset and 0.05 m); one before the front's plane over
    # the round would stand off nothing
    cu, cv = round_corner_spans(out, depth, width)["centre"]
    f0, f1 = spans["k01.wall.street_front"]
    rain = rainwater or {}
    for x in rain.get("front_pipes", []):
        rp, off = rain["pipe_diameter_m"] / 2, rain["pipe_offset_from_wall_m"]
        on = f0 - 1e-6 <= x["s_m"] <= f1 + 1e-6
        if x["proud_m"] < 0.0 or on:
            lat = depth + x["proud_m"] + off + 0.05 + rp
            if not on or x["proud_m"] >= 0.0 or math.hypot(lat - cu, x["s_m"] - cv) < r + off + 0.05 + rp - 1e-6:
                raise ParamError(f"rainwater.front_pipes {x}: a pipe behind the front's plane stands on the round "
                                 f"corner, its centre at least {r + off + 0.05 + rp:.4f} m from the round's centre")
    return out


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
    # T-2788: or an all-stone house (`stone`), its K02 stone_front's fabric, dressing and
    # coursing laid round every face — flanks, rear and wings — not a stone front on a brick box
    construction = val("construction")
    if construction not in ("brick_with_stone_front", "brick", "stone"):
        raise ParamError("k01_frontage builds a stone or a brick street front on common-brick "
                         "side and rear walls, or an all-stone house; another construction is "
                         "another assembly")
    if (construction != "brick") != bool(val("stone_front")):
        raise ParamError(f"construction {construction!r}: a stone street front or an all-stone "
                         "house names its K02 stone_front and a brick one names none")

    # T-2476: paint over the brick walls, the colour a source names for the house
    wf = val("wall_finish", {}) or {}
    paint = ()
    paint_opaque = False
    if wf:
        if construction != "brick":
            raise ParamError("wall_finish paints a brick house's walls; a stone front is not painted here")
        # T-2933: `opaque` paint covers the brick's map (1736's walls, near white in its
        # photograph, which no factor over the buff brick can reach); otherwise it tints it
        if set(wf) != {"paint"} or not {"color"} <= set(wf["paint"]) <= {"color", "opaque"}:
            raise ParamError("wall_finish is {\"paint\": {\"color\": [r, g, b]}}, optionally opaque")
        paint = tuple(float(x) for x in wf["paint"]["color"])
        paint_opaque = wf["paint"].get("opaque", False)
        if not isinstance(paint_opaque, bool):
            raise ParamError("wall_finish.paint.opaque is true or false")
        if len(paint) != 3 or not all(0.05 <= x <= 1.0 for x in paint):
            raise ParamError(f"wall_finish.paint.color {wf['paint']['color']}: three factors in [0.05, 1]")

    # T-3093: the street front's brick (over a stone front's brick_above_m line, the shaped
    # gable and the front's brick bays) toned apart from the K03 common brick of the side and
    # rear walls: a factor over the same panel, where a photograph reads the front's brick
    # darker than its stone and the side wall paler than the front (1812's)
    sfb = val("street_front_brick", {}) or {}
    front_tone = ()
    if sfb:
        if set(sfb) != {"tone"} or len(sfb["tone"]) != 3 or not all(0.2 <= float(x) <= 1.0 for x in sfb["tone"]):
            raise ParamError("street_front_brick is {\"tone\": [r, g, b]}, three factors in [0.2, 1]")
        if not (val("stone_front") or {}).get("brick_above_m"):
            raise ParamError("street_front_brick tones the brick over a stone front's brick_above_m line, "
                             "and this front names none")
        front_tone = tuple(float(x) for x in sfb["tone"])

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
    prange = tuple(roof["parameters"]["pitch_deg"]["ranges"][band])
    # T-2542: a gable read off a source may stand in the contract's steep band too (1811's,
    # whose plate shows its street slope rising from about 8.4 m to about 16 m); a
    # reconstructed pitch keeps the ordinary band, as a reconstructed principal floor does
    rpa = form.get("roof_pitch_deg") or {}
    if gable and rpa.get("confidence", "reconstructed") != "reconstructed":
        if not rpa.get("sources"):
            raise ParamError(f"roof_pitch_deg is {rpa.get('confidence')} and names no source: "
                             "only a source can put a gable past the ordinary band")
        prange = (prange[0], roof["parameters"]["pitch_deg"]["ranges"]["steep"][1])
    _within(pitch, prange, "roof_pitch_deg")
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
    # T-1888: a front entered in an inner bay that is not its middle one (1834's four bays,
    # the door third from the south in its photograph): the bay's number, 1 the southmost
    if isinstance(entrance, int) and not isinstance(entrance, bool):
        if not 1 <= entrance <= len(front_bays):
            raise ParamError(f"entrance_bay {entrance} names a bay this {len(front_bays)}-bay front has not "
                             f"(1 is the southmost)")
        door_s = front_bays[entrance - 1]
    elif entrance not in ("south", "north", "middle"):
        raise ParamError(f"entrance_bay is south, north, middle or a bay's number, not {entrance!r}")
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
    # T-3135: a porch arch whose mouth stands off its bay's centre (1812's, the Levy print and
    # the c. 1955 photograph: the south jamb run down the projection's corner, the north jamb
    # where the bay's was), the bay's windows over it on their own centres: `axis_s_m` the
    # mouth's centre along the front, at most half a metre off the bay's, under a sized mouth
    door_bay = door_s
    dax = ((val("entrance_kit") or {}).get("k01.opening.door_leaf") or {}).get("axis_s_m")
    if dax is not None:
        if sfo or abs(float(dax) - door_bay) > 0.5 \
                or "opening_m" not in (val("entrance_kit") or {}).get("k01.opening.door_leaf"):
            raise ParamError(f"entrance_kit.axis_s_m {dax}: a sized mouth's (`opening_m`) centre at most 0.5 m "
                             f"off its bay's ({door_bay}), on a front laid by front_bays")
        door_s = float(dax)
    # T-2752: a stone front whose windows its photograph puts off the bays' columns, each
    # storey its own (1625's): every street window named with its centre, width, sill and head
    sfw = val("street_front_windows") or {}
    if sfw:
        if not val("stone_front") or sfo or val("front_bays_by_storey") or val("street_front_round_heads"):
            raise ParamError("street_front_windows names every window of a K02 stone front, and takes "
                             "no street_front_openings, front_bays_by_storey or street_front_round_heads")
        if not {"windows", "base_top_m", "belts", "surrounds", "carved_bands"} >= set(sfw) >= {"windows", "base_top_m"} \
                or not sfw["windows"]:
            raise ParamError("street_front_windows takes windows: [{component, storey, s_m, width_m, sill_m, "
                             "height_m}, ...] and base_top_m, the plain plinth's top where no area light sets it "
                             "(and, T-2753, belts and surrounds; T-2915, carved_bands)")
    # T-2410: a brick front's storeys whose street windows are round-headed under hoods
    # T-2960: or segmental-headed (`head`), under K09's cornice hood on its consoles (`hood`)
    # in place of the arch band and its key block
    rh = val("street_front_round_heads") or {}
    if rh:
        if not {"storeys"} <= set(rh) <= {"storeys", "key", "head", "rise_over_span", "hood"} \
                or ("key" in rh) == ("hood" in rh) \
                or ("key" in rh and set(rh["key"]) != {"width_m", "height_m", "proud_m"}):
            raise ParamError("street_front_round_heads takes storeys [k, ...] and either key {width_m, height_m, "
                             "proud_m} or hood, and may name head and rise_over_span")
        if rh.get("head", "round") not in ("round", "segmental"):
            raise ParamError("street_front_round_heads.head cuts a 'round' or a 'segmental' head")
        if "rise_over_span" in rh and (rh.get("head") != "segmental" or not 0.05 <= rh["rise_over_span"] < 0.5):
            raise ParamError("street_front_round_heads.rise_over_span sets a segmental head's rise, 0.05 to "
                             "under 0.5 of its span")
        hood = rh.get("hood")
        if hood is not None and (set(hood) != {"variant", "overhang_m"} or hood["variant"] != ROUND_HEAD_HOOD
                                 or not 0.05 <= hood["overhang_m"] <= 0.4):
            raise ParamError(f"street_front_round_heads.hood takes variant {ROUND_HEAD_HOOD!r} and overhang_m, "
                             f"its block 0.05-0.4 m past each jamb")
        # T-1888: a front whose stone stops at the principal floor (brick_above_m there) is a
        # brick front over a stone basement, and its storeys' windows are cut in the brick
        # T-3208: or a stone front laid by front_bays, each window one round hole in its courses
        # under the arch band and key (1900's, the oblique print and the c. 2014 detail); a front
        # whose arches are grouped under voussoir blocks still names them in street_front_openings
        sf_ = val("stone_front") or {}
        if (sf_ and sf_.get("brick_above_m") not in (None, val("principal_floor_m"))) or sfo:
            raise ParamError("street_front_round_heads cuts round holes in a brick front, or in a stone front "
                             "laid by front_bays; a stone front's grouped arches are street_front_openings")
        if any(not 0 <= int(k) < stories for k in rh["storeys"]):
            raise ParamError(f"street_front_round_heads.storeys names a storey this {stories}-storey house has not")
        rh = {"storeys": tuple(sorted({int(k) for k in rh["storeys"]})), "head": rh.get("head", "round"),
              **({"rise_over_span": float(rh["rise_over_span"])} if "rise_over_span" in rh else {}),
              **({"key": {k: float(x) for k, x in rh["key"].items()}} if "key" in rh else
                 {"hood": {"variant": hood["variant"], "overhang_m": float(hood["overhang_m"])}})}
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
    # T-2910: a loggia's side arch on the 18th Street (south) wall takes the principal storey's
    # window in its span, as the door takes its bay's; the storeys over it keep theirs
    lsa = (((val("entrance_kit") or {}).get("k01.opening.door_leaf") or {}).get("loggia") or {})
    lsa = lsa.get("side_arch") if abs(float(sorted(lsa.get("v_m", [-1.0]))[0]) - st) < 1e-6 else None

    def _in_side_arch(s, w):
        if not lsa:
            return False
        reach = float(lsa["clear_width_m"]) / 2 + float(lsa["ring_m"]) + w / 2
        return abs(s - (depth - float(lsa["centre_m"]))) < reach
    # T-1871: a porch on columns may stand off its door's axis (`centre_v_m`, the front's own v)
    # and name the head of the principal-storey windows behind it (`under_head_m`)
    hd_ = ((val("entrance_kit") or {}).get("k01.opening.door_leaf") or {}).get("hood") or {}
    under = None
    if "under_head_m" in hd_:
        uh = float(hd_["under_head_m"])
        if "columns" not in hd_ or not floors[0] + 1.5 <= uh <= float(hd_["soffit_m"]) - 0.3:
            raise ParamError("entrance_kit.hood.under_head_m: the head of the windows behind a porch on columns, "
                             "1.5 m over the principal floor and 0.3 m under the soffit")
        under = (float(hd_.get("centre_v_m", door_s)), float(hd_["width_m"]), uh)
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
            if k == 0 and s == door_bay:
                continue
            # T-1871: a principal-storey window behind a porch on columns (1700's and 1706's,
            # Chicagology's photograph) stands under the porch's soffit, square-headed
            if k == 0 and under and abs(s - under[0]) < under[1] / 2 + w / 2:
                openings.append(Opening("k01.opening.sash_flat", "k01.wall.street_front", s, round(sill, 4), w,
                                        round(under[2] - sill, 4)))
                continue
            comp = ROUND_HOODED if rh and k in rh["storeys"] else "k01.opening.sash_flat"
            openings.append(Opening(comp, "k01.wall.street_front", s, round(sill, 4), w, h))
        for s in val("side_bays"):
            if isinstance(s, dict):   # T-3097: a window read off a picture is laid once, below
                continue
            if k == 0 and _in_side_arch(float(s), w):   # T-2910: the loggia's arch stands there
                continue
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.south", float(s), round(sill, 4), w, h))
        for s in val("rear_bays"):
            openings.append(Opening("k01.opening.sash_flat", "k01.wall.rear_service", float(s), round(sill, 4), w, h))
        for s in val("north_bays") or ():
            if not isinstance(s, dict):   # T-2866: a window read off a picture is laid once, below
                openings.append(Opening("k01.opening.sash_flat", "k01.wall.side.north", float(s), round(sill, 4), w, h))
    # T-2866: a north-wall window read off a picture (1625's south wall on the McBirney camera:
    # its top floor's lights at their own sills, a stair light between floors, the ground
    # floor's one) is {s_m, sill_m, width_m, height_m}, laid once at its own place rather than
    # a column on every storey; the contract's single sash width, its height read (as
    # street_front_windows' and rear_section's are), its lintel clear of the soffit
    soffit = eave - (0.0 if mansard else float(val("eave_overhang_m")) * math.tan(math.radians(pitch)))
    # T-3097: and the south wall's the same way (1801's 18th Street flank on the Taylor camera:
    # the corner light over the loggia off the arch's axis, the round-headed pair past the tower)
    read = {}
    for attr, wall_id, j, e in [("north_bays", "k01.wall.side.north", j, e)
                                for j, e in enumerate(val("north_bays") or ())] + \
            [("side_bays", "k01.wall.side.south", j, e) for j, e in enumerate(val("side_bays") or ())]:
        if not isinstance(e, dict):
            continue
        what = f"{attr}[{j}]"
        if not {"s_m", "sill_m", "width_m", "height_m"} <= set(e) <= {"s_m", "sill_m", "width_m", "height_m",
                                                                     "head", "why_not_ordinary"}:
            raise ParamError(f"{what}: a window read off a picture takes s_m, sill_m, width_m and height_m, "
                             f"and may take head and why_not_ordinary")
        s, sill, wd, h = (float(e[x]) for x in ("s_m", "sill_m", "width_m", "height_m"))
        # T-2884: its head as the picture draws it — `plain`, a square hole with nothing laid
        # over it, or `round`, a round-headed hole under no hood or arch (1625's lower lights);
        # absent, K01 lays the brick wall's own head. A light narrower than the ordinary sash
        # (a basement light's, a slit's) says why, and may stand lower and shorter
        head = e.get("head")
        if head not in (None, "plain", "round"):
            raise ParamError(f"{what}.head is plain or round, not {head!r}")
        narrow = "why_not_ordinary" in e
        if narrow:
            if not e["why_not_ordinary"] or not 0.25 <= wd < cw[0] or head is None:
                raise ParamError(f"{what}: a light narrower than the ordinary sash is 0.25-{cw[0]} m across, "
                                 f"its head read (plain or round), and says why (why_not_ordinary)")
            if not 0.5 <= h <= 3.2 or sill < 0.15:
                raise ParamError(f"{what}: a narrow light read off a picture stands 0.5-3.2 m, its sill at least 0.15 m up")
        else:
            _within(wd, cw, f"{what}.width_m")
            if not 1.0 <= h <= 3.2 or sill < 0.3:
                raise ParamError(f"{what}: a sash read off a picture stands 1.0-3.2 m, its sill at least 0.3 m up")
        if head == "round" and h < wd / 2 + 0.2:
            raise ParamError(f"{what}: a round head's spring stands at least 0.2 m over its sill")
        if sill + h + 0.30 > soffit - 0.05:
            raise ParamError(f"{what}'s lintel runs into the soffit at {soffit:.2f} m")
        if s - wd / 2 < 0.45 or s + wd / 2 > depth - 0.45:
            raise ParamError(f"{what} stands within 0.45 m of the wall's ends")
        for a0, a1, b0, b1 in read.setdefault(wall_id, []):
            if s - wd / 2 < a1 + 0.3 and s + wd / 2 > a0 - 0.3 and sill < b1 + 0.45 and sill + h > b0 - 0.45:
                raise ParamError(f"{what} meets another read window, or its lintel")
        read[wall_id].append((s - wd / 2, s + wd / 2, sill, sill + h))
        openings.append(Opening(ROUND_PLAIN if head == "round" else "k01.opening.sash_flat", wall_id,
                                s, round(sill, 4), wd, h, head != "round", plain=head is not None, narrow=narrow))
    # T-2821: a door whose height its picture reads (1625's, 2.48 m clear over its one step);
    # K07 hangs its leaf in the K01 hole, so the hole is the door's. K01's 2.70 m otherwise
    door_w, door_h = 1.20, 2.70
    if form.get("door_clear_height_m"):
        dch = form["door_clear_height_m"]
        if dch.get("confidence", "reconstructed") == "reconstructed" or not dch.get("sources"):
            raise ParamError("door_clear_height_m moves the door's head off K01's 2.70 m; only a source can")
        door_h = float(dch["value"])
        if not 2.0 <= door_h <= 3.2:
            raise ParamError(f"door_clear_height_m {door_h} is not a principal door's: 2.0-3.2 m clear")
    # T-2817: a stone front's door arch may be cut broader and lower than K01's 1.2 by 2.7 m door
    # (1623's porch mouth, as broad as the window's arch beside it): `opening_m`, [width, height
    # to the crown over the door's floor], the door itself then standing at the porch's back
    om = ((val("entrance_kit") or {}).get("k01.opening.door_leaf") or {}).get("opening_m")
    if om is not None:
        if form.get("door_clear_height_m"):
            raise ParamError("entrance_kit.opening_m and door_clear_height_m both size the door's hole; give one")
        if not door_arch_of(val("entrance_kit")) or len(om) != 2:
            raise ParamError("entrance_kit.opening_m [width, height] sizes a round-arched door's hole (`arch`)")
        door_w, door_h = float(om[0]), float(om[1])
        # T-2952: under a segmental head (`arch.rise_over_span`) the mouth may be a porch's, to 3.2 m
        ros = door_arch_of(val("entrance_kit")).get("rise_over_span")
        rise, widest = (door_w * float(ros), 3.2) if ros else (door_w / 2, 2.2)
        if not 1.0 <= door_w <= widest or not rise + 1.2 <= door_h <= 3.6:
            raise ParamError(f"entrance_kit.opening_m {om}: an arch 1.0-{widest} m across whose jambs rise at least "
                             f"1.2 m to its springing, its crown at most 3.6 m over the floor")
    openings.append(Opening("k01.opening.door_leaf", "k01.wall.street_front", door_s, round(door_floor, 4),
                            door_w, door_h, False))
    if sfw:
        kit_ids = {v["id"]: v for v in json.loads(WINDOW_KIT.read_text())["variants"]}
        door = (door_s - 0.60 - 0.30, door_s + 0.60 + 0.30, door_floor + door_h + 0.30)
        laid, rings = [], []
        for k, w in enumerate(sfw["windows"]):
            if set(w) - {"voussoirs"} != {"component", "storey", "s_m", "width_m", "sill_m", "height_m"}:
                raise ParamError(f"street_front_windows.windows[{k}] takes component, storey, s_m, width_m, sill_m and height_m"
                                 f" (and, T-2889, voussoirs)")
            comp, st = w["component"], int(w["storey"])
            s, wd, sill, h = (float(w[x]) for x in ("s_m", "width_m", "sill_m", "height_m"))
            entry = (val("window_kit") or {}).get(comp)
            vid = entry if isinstance(entry, str) else (entry or {}).get("variant")
            if not comp.startswith(STREET_WINDOW) or vid not in kit_ids:
                raise ParamError(f"street_front_windows.windows[{k}]: {comp!r} is not a {STREET_WINDOW}* "
                                 f"component the window_kit glazes")
            # T-2865: a front carried up past the eave (shaped_gable.ledge_m) has no eave over
            # its top storey's lights — the gable's slab stands there, so the light stops under
            # the slab's foot and its flat arch runs on into the slab's wall
            sgr = val("shaped_gable") or {}
            top = (floors[st + 1] - 0.30 if st + 1 < stories
                   else float(sgr["foot_m"]) if sgr.get("ledge_m") is not None else eave - 0.55)
            if not 0 <= st < stories or not floors[st] < sill or sill + h > top:
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
            if w.get("voussoirs") is not None:
                rings.append(_voussoirs(w["voussoirs"], k, kit_ids[vid], s, sill, h, sgr,
                                        float(val("eave_overhang_m")), eave))
            dh = kit_ids[vid]["operation"].startswith("double_hung")
            openings.append(Opening(comp, "k01.wall.street_front", round(s, 4), round(sill, 4), wd, h, dh))
    street_dress, frontispiece = {}, {}
    if sfw:
        street_dress = _street_dress(sfw, openings, floors, width)
        if rings:   # T-2889: the named windows' voussoir rings
            street_dress["voussoirs"] = tuple(rings)
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
    # T-3184: a stone basement's lights read round-headed off a picture (1834's photograph: a
    # tall round-headed light under each window but the door's) are cut as the side walls'
    # round lights are, ROUND_PLAIN, in the coursed stone, the head at least half the width
    bhead = bl.get("head")
    if not set(bl) <= {"sill_m", "width_m", "height_m"} | ({"head", "base_top_m"} if bhead else set()):
        raise ParamError("basement_lights takes sill_m, width_m and height_m (and, round-headed, head and base_top_m)")
    if bhead is not None and (bhead != "round" or not val("stone_front")
                              or float(bl["height_m"]) < float(bl["width_m"]) / 2 + 0.2):
        raise ParamError("basement_lights.head is 'round', in a K02 stone front, its spring at least "
                         "0.2 m over the sill")
    for s in (() if sfo or sfw else front_bays):
        if s != door_bay:
            openings.append(Opening(ROUND_PLAIN if bhead else "k01.opening.area_light", "k01.wall.street_front",
                                    s, bsill, float(bl["width_m"]), float(bl["height_m"]), False, plain=bool(bhead)))
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
            # T-2818: a row's lights may stand off their bay's centre, where the picture puts
            # them (1623's basement light, drawn north of the window over it)
            off = float(row.get("offset_m", 0.0))
            if off and (pier or not abs(off) <= 0.5):
                raise ParamError(f"street_front_openings.rows[{k}].offset_m: a single light stands at most "
                                 f"0.5 m off its bay's centre (has {off}, pair_pier_m {pier})")
            for b in row["bays"]:
                c = front_bays[int(b)] + off
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
    if val("flat_balustrade"):
        flat_roof["balustrade"] = _flat_balustrade(val("flat_balustrade"), flat_roof, width, eave)
    mansard_roof = _mansard_roof(val("mansard"), depth, width, eave, pitch,
                                 float(val("eave_overhang_m")), shaped=bool(val("shaped_gable")),
                                 side_wall=float(val("wall_thickness_side_m"))) if mansard else {}
    # T-2995: a mansard on the street front and part of a side, the rest a straight brick storey
    if mansard and (val("mansard") or {}).get("straight"):
        from .k01_mansard_straight import resolve as resolve_straight
        mansard_roof["straight"] = resolve_straight(val("mansard")["straight"], depth=depth, width=width,
                                                    side_wall=float(val("wall_thickness_side_m")),
                                                    dormers=list(val("mansard").get("dormers") or []))
    gable_roof = _gable_roof(val("gable_roof"), depth, width, eave, pitch, st,
                             float(val("eave_overhang_m"))) if gable else {}
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
    if gable and val("rainwater") and "front_pipes" not in val("rainwater"):
        raise ParamError("a gable K01 roof hangs no gutter yet: k01_frontage runs its half-round gutter "
                         "round a hip's eaves, and a gable's side walls are parapets (rainwater is empty, "
                         "or front_pipes alone)")
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

    slope_dormers = _slope_dormers(val("slope_dormers"), roof_form, depth, width, eave, pitch,
                                   float(val("eave_overhang_m")), rear_section)
    shaped = _shaped_gable(val("shaped_gable") or {}, roof_form, dormer, width, eave, pitch,
                           float(val("eave_overhang_m")), mansard_roof)

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
        # T-3195: a plain front's basement lights barred as a bay's are (1827's, from the Doane
        # photograph): K08's bar grille in each light's reveal (k08_bays.grille), on the area
        # lights only, and only where no well is dug, so the bars stand in a reveal above grade
        g = entry.get("grille")
        if g is not None:
            ok = comp == "k01.opening.area_light" and not kit[comp]["well"] and isinstance(g, dict) \
                and set(g) == {"bars", "set_back_m", "ring_radius_m"} and 2 <= int(g["bars"]) <= 16 \
                and 0.0 < float(g["set_back_m"]) <= 0.08
            if not ok:
                raise ParamError(f"window_kit: {comp}'s grille is a basement light's, out of its well "
                                 f"(\"well\": false), and takes bars (2-16), set_back_m (at most 0.08 m) "
                                 f"and ring_radius_m, not {g}")
            kit[comp]["grille"] = {"bars": int(g["bars"]), "set_back_m": float(g["set_back_m"]),
                                   "ring_radius_m": float(g["ring_radius_m"])}
    for comp in sorted({o.component for o in openings} - {"k01.opening.door_leaf"}):
        vid = kit.get(comp, {}).get("variant")
        if vid not in variants:
            raise ParamError(f"window_kit names no K06 variant for {comp} (k06_windows.json)")
        v = variants[vid]
        if comp == ROUND_HOODED:
            # T-2410: the K01 wall cuts this one's round hole (k01_frontage.wall), so its
            # variant is a single round-headed sash, and its hood and key must clear K10's
            # bed moulding as any K01 head does (HEAD_RISE_M, 0.30 m over the crown)
            # T-2960: or its segmental hole, on the variant's own rise over span
            want = (rh or {}).get("head", "round")
            if v["head"] != want or v.get("bays", 1) != 1:
                raise ParamError(f"window_kit: {comp} is cut as one {want} hole, and {vid} is not a single "
                                 f"{want}-headed sash")
            if want == "segmental":
                ros = float(rh.get("rise_over_span") or v.get("rise_over_span", json.loads(
                    WINDOW_KIT.read_text())["arch"]["segmental"]["working_rise_over_span"]))
                openings = [dataclasses.replace(o, rise_over_span=ros) if o.component == comp else o
                            for o in openings]
            band = json.loads(WINDOW_KIT.read_text())["parts"]["head_band"]
            key = (rh or {}).get("key")
            if key and (not band["width_m"] < key["height_m"] <= 0.30 or key["proud_m"] <= band["proud_m"] or
                        key["width_m"] > min(o.width_m for o in openings if o.component == comp) / 2):
                raise ParamError(f"street_front_round_heads.key: {key['width_m']} x {key['height_m']} m, "
                                 f"{key['proud_m']} m proud, does not stand on the hood's crown (over its "
                                 f"{band['width_m']} m band and {band['proud_m']} m proud, inside 0.30 m and half the sash)")
        elif comp == ROUND_PLAIN:
            # T-2884: the side wall cuts this one's round hole as it cuts ROUND_HOODED's
            if v["head"] != "round" or v.get("bays", 1) != 1:
                raise ParamError(f"window_kit: {comp} is cut as one round hole, and {vid} is not a single round-headed sash")
        elif v["head"] != "flat" and not (comp in arched_rows and val("stone_front")) and not (
                comp.startswith(STREET_WINDOW) and v["head"] in ("segmental", "round")):
            # T-2752: the coursed stone front fills a named street window's segmental head
            # (T-2889: and its round one, 1812's small arched window)
            raise ParamError(f"window_kit: {vid} has a {v['head']} head, and a K01 wall cuts "
                             f"a rectangular hole")
        # T-2818: a single light may stand under a segmental arch (1623's broad basement light)
        if comp in arched_rows and v["head"] != "round" and not (v["head"] == "segmental" and v.get("bays", 1) == 1):
            raise ParamError(f"window_kit: {comp} is laid under a round arch, or a single light under a "
                             f"segmental one, and {vid} has a {v['head']} head")
        if v.get("well") and kit[comp]["well"] and comp == "k01.opening.area_light" and bsill > 0:
            raise ParamError(f"window_kit: {vid} sits in an area well, but these basement "
                             f"lights' sills stand {bsill} m above grade; set \"well\": false")
        if comp == ROUND_PLAIN and v["operation"].startswith("double_hung"):
            # T-3160: a round-headed light read off a picture, hung as a sash under its fanlight
            # (1729's 18th Street flank) where the kit names one, not a fixed basement light
            openings = [dataclasses.replace(o, meeting_rail=True) if o.component == comp else o for o in openings]
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
        if not need <= set(da) <= need | {"extrados", "ring_proud_m", "band_m", "rise_over_span", "head", "moulding"}:
            raise ParamError(f"entrance_kit.arch takes {sorted(need)}, and extrados, ring_proud_m, band_m, "
                             f"rise_over_span, head and moulding")
        # T-3134: the head a half ellipse rising `rise_over_span` of its span (1812's porch arch, the
        # Levy print: flatter at the crown than a segment), and a narrow moulded ring of light stone
        # round it and down its jambs, `steps_m` [inner, outer] broad and `proud_m` before the wall
        if "head" in da and (da["head"] != "elliptical" or "rise_over_span" not in da):
            raise ParamError("entrance_kit.arch.head is 'elliptical', rising rise_over_span of its span")
        if "moulding" in da:
            mo = da["moulding"]
            if set(mo) != {"steps_m", "proud_m"} or len(mo["steps_m"]) != 2 or len(mo["proud_m"]) != 2:
                raise ParamError("entrance_kit.arch.moulding takes steps_m and proud_m, [inner, outer] each")
            (w1, w2), (p1, p2) = (float(x) for x in mo["steps_m"]), (float(x) for x in mo["proud_m"])
            if not (0.02 <= w1 and 0.02 <= w2 and w1 + w2 <= float(da["ring_m"])) or not 0.0 < p2 < p1 <= 0.08 \
                    or "extrados" in da:
                raise ParamError(f"entrance_kit.arch.moulding {mo}: two steps at least 0.02 m broad inside the "
                                 f"{da['ring_m']} m ring, the inner the prouder, at most 0.08 m (no curved extrados)")
        # T-2952: a broad porch arch whose head is a segment, not a half circle (1812's, the Levy
        # print: about 2.7 m across, rising about 0.8 m from its spring to its crown)
        if "rise_over_span" in da and (not 0.15 <= float(da["rise_over_span"]) <= 0.45 or "extrados" in da):
            # T-3134: (a half ellipse's rise is a semi-axis, the same bounds)
            raise ParamError("entrance_kit.arch.rise_over_span: a segmental head rising 0.15-0.45 of its span, "
                             "in a voussoir block (no curved extrados)")
        if not 0.15 <= float(da["ring_m"]) <= 0.6:
            raise ParamError("entrance_kit.arch.ring_m: a voussoir block 0.15-0.6 m outside the arch")
        if da.get("extrados", "curved") != "curved" or ("ring_proud_m" in da) != ("extrados" in da) \
                or not 0.0 <= float(da.get("ring_proud_m", 0.0)) <= 0.06:
            raise ParamError("entrance_kit.arch.extrados is 'curved', with ring_proud_m 0-0.06 m beside it")
        di = next(i for i, o in enumerate(openings) if o.component == "k01.opening.door_leaf")
        arched_groups.append({"component": "k01.opening.door_leaf", "bay": front_bays.index(door_bay), "ops": [di],
                              "ring_m": float(da["ring_m"]), "keystone_top_m": float(da["keystone_top_m"]),
                              "keystone_m": tuple(float(x) for x in da["keystone_m"]),
                              **({"rise_over_span": float(da["rise_over_span"])} if "rise_over_span" in da else {}),
                              **({"head": da["head"]} if "head" in da else {}),
                              **({"moulding": {k: [float(x) for x in da["moulding"][k]] for k in ("steps_m", "proud_m")}}
                                 if "moulding" in da else {}),
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
            if set(t) - {"side", "to_v_m", "back", "out_m", "loggia", "parapet"} \
                    or t.get("side", "right") not in ("right", "left"):
                raise ParamError("entrance_kit.terrace takes side 'right' or 'left', to_v_m, "
                                 "back [[v, out], ...], out_m, loggia and parapet alone, or a list of one a side")
            terraces.append({"side": t.get("side", "right"), "to_v_m": float(t["to_v_m"]),
                             "back": [[float(v), float(o)] for v, o in t.get("back", [])]})
            # T-2952: a stone parapet along the terrace's front, pierced in rows of square holes
            # (1812's beside its stair's head, the Levy print)
            if "parapet" in t:
                pp = t["parapet"]
                if set(pp) != {"height_m", "thickness_m", "holes", "hole_m"} or len(pp["holes"]) != 2 \
                        or len(pp["hole_m"]) != 2:
                    raise ParamError("entrance_kit.terrace.parapet takes height_m, thickness_m, holes [rows, "
                                     "columns] and hole_m [width, height]")
                ph, pt = float(pp["height_m"]), float(pp["thickness_m"])
                (rows, cols), (hw, hh) = (int(x) for x in pp["holes"]), (float(x) for x in pp["hole_m"])
                if not 0.3 <= ph <= 1.1 or not 0.1 <= pt <= 0.4 or not 1 <= rows <= 4 or not 1 <= cols <= 20 \
                        or not 0.03 <= hw <= 0.3 or not 0.03 <= hh <= 0.3 or rows * hh > ph - 0.2:
                    raise ParamError(f"entrance_kit.terrace.parapet {pp}: 0.3-1.1 m high, 0.1-0.4 m thick, 1-4 rows "
                                     f"of 1-20 holes 0.03-0.3 m across, a coping and a foot left round them")
                terraces[-1]["parapet"] = {"height_m": ph, "thickness_m": pt, "holes": [rows, cols],
                                           "hole_m": [hw, hh]}
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
                # T-2845: the far pedestal's and the side parapet's inset from the terrace's end,
                # and the pair's pitch, are optional (the kit's defaults stand them at the corner
                # and the pedestal's quarters)
                opt = {"pedestal": {"far_inset_m"}, "columns": {"pitch_m"}, "parapet": {"side_inset_m"}}
                # T-2877: and a rear row, a pedestal against the wall behind each front one
                # (its depth; its width, its pair's place off the wall, pitch and radii the
                # front's unless given), carrying a pair under a paired capital; T-2882: and a
                # respond on the wall behind the pair, `respond_m` deep, from the pedestal to the ceiling
                if "rear" in lg and not ({"depth_m"} <= set(lg["rear"]) <= {"depth_m", "width_m", "axis_m",
                                                                         "pitch_m", "radius_scale", "respond_m"}):
                    raise ParamError("entrance_kit.terrace.loggia.rear takes depth_m, and optionally width_m, "
                                     "axis_m, pitch_m, radius_scale and respond_m")
                if set(lg) - {"finish", "rear"} != set(need) or any(
                        not v <= set(lg[k]) <= v | opt.get(k, set()) for k, v in need.items()):
                    raise ParamError(f"entrance_kit.terrace.loggia takes {sorted(need)}, each with "
                                     + "; ".join(f"{k}: {sorted(v)}" for k, v in need.items())
                                     + "; optionally " + "; ".join(f"{k}: {sorted(v)}" for k, v in opt.items())
                                     + "; and optionally rear")
                if "out_m" not in t:
                    raise ParamError("entrance_kit.terrace.loggia stands on a terrace with its own out_m")
                if lg.get("finish") not in (None, "ionic_carved"):
                    raise ParamError("loggia.finish is ionic_carved")
                prof = lg["columns"]["profile"]
                if prof[0][1] != 0.0 or prof[-1][1] != 1.0 or any(b[1] <= a[1] for a, b in zip(prof, prof[1:])):
                    raise ParamError("entrance_kit.terrace.loggia.columns.profile runs [r, fraction of height] from 0 to 1")
                # the pair's pitch, half the pedestal's width unless the record gives it (T-2845)
                pitch = float(lg["columns"].get("pitch_m", float(lg["pedestal"]["width_m"]) / 2))
                if 2 * max(r for r, _ in prof) > pitch:
                    raise ParamError("entrance_kit.terrace.loggia: two columns do not stand side by side on a pedestal")
                terraces[-1]["loggia"] = lg
        if len({t["side"] for t in terraces}) != len(terraces):
            raise ParamError("entrance_kit.terrace: one terrace a side")
        door_kit["terrace"] = terraces[0] if len(terraces) == 1 else terraces
    if balustrade is not None:
        need = {"height_m", "pitch_m", "newel_m", "newel_cap_m", "rail_m", "segments", "profile"}
        # T-2960: and may be painted timber (`fabric`), as a veranda's is (1736's photograph)
        if not need <= set(balustrade) <= need | {"fabric"}:
            raise ParamError(f"entrance_kit.balustrade takes {sorted(need)}, and may name fabric")
        if balustrade.get("fabric", "stone") not in ("stone", "painted_timber"):
            raise ParamError("entrance_kit.balustrade.fabric is 'stone' (the stoop's) or 'painted_timber' "
                             "(the walls' paint)")
        prof = balustrade["profile"]
        if prof[0][1] != 0.0 or prof[-1][1] != 1.0 or any(b[1] <= a[1] for a, b in zip(prof, prof[1:])):
            raise ParamError("entrance_kit.balustrade.profile runs [r, fraction of height] from 0 to 1")
        door_kit["balustrade"] = dict(balustrade)
    # T-2933: a timber veranda over the landing and its terraces (1736's, the c. 1890
    # photograph): posts at `posts_v_m` along the front, a beam over them and a hipped
    # lean-to roof from the wall; k07_entrances.Entrance._veranda builds and places it
    if "veranda" in door_kit_in:
        vr = door_kit_in["veranda"]
        need = {"posts_v_m", "post_m", "height_m", "inset_m", "beam_m", "roof"}
        if not need <= set(vr) <= need | {"open_under"} or set(vr["roof"]) != {"overhang_m", "rise_m", "thickness_m"}:
            raise ParamError(f"entrance_kit.veranda takes {sorted(need)}, its roof overhang_m, rise_m "
                             f"and thickness_m, and may name open_under")
        # T-2960: a deck open beneath, on its posts carried down to grade (1736's photograph):
        # a skirt board `skirt_m` deep over the void, which stands `recess_m` behind the front
        ou = vr.get("open_under")
        if ou is not None and (set(ou) != {"skirt_m", "recess_m"} or not 0.05 <= ou["skirt_m"] <= 0.5
                               or not 0.2 <= ou["recess_m"] <= 1.5):
            raise ParamError("entrance_kit.veranda.open_under takes skirt_m (0.05-0.5 m) and recess_m "
                             "(0.2-1.5 m)")
        if terrace is None:
            raise ParamError("entrance_kit.veranda stands on the landing and a terrace")
        if not 0.1 <= float(vr["post_m"]) <= 0.3 or not 2.0 <= float(vr["height_m"]) <= 4.5:
            raise ParamError(f"entrance_kit.veranda: {vr['post_m']} m posts {vr['height_m']} m high are "
                             f"not a veranda's (0.1-0.3 m, 2.0-4.5 m)")
        door_kit["veranda"] = {**vr, "posts_v_m": [float(x) for x in vr["posts_v_m"]],
                               "beam_m": [float(x) for x in vr["beam_m"]], "roof": dict(vr["roof"]),
                               **({"open_under": {k: float(x) for k, x in ou.items()}} if ou else {})}
    if door_arch:
        door_kit["arch"] = dict(door_arch)
    if "opening_m" in door_kit_in:
        door_kit["opening_m"] = [door_w, door_h]
    # T-2817: a porch behind the arch, its door at the back to one side (1623's drawing): the
    # door's own opening, `width_m` across and `height_m` to its flat head, its centre
    # `offset_m` along the front from the arch's axis, with its leaves, transom and glazing;
    # a wall at the reveal's depth closes the arch round it (k07_entrances, porch_back)
    if "porch_door" in door_kit_in:
        pd = door_kit_in["porch_door"]
        need = {"width_m", "offset_m", "height_m", "leaves", "panels", "transom_m"}
        if not door_arch or "reveal_depth_m" not in door_kit_in or not need <= set(pd) <= need | {"glazed_rows"}:
            raise ParamError(f"entrance_kit.porch_door takes {sorted(need)} and optionally glazed_rows, at the back "
                             f"of a round-arched door's (`arch`) deep reveal (`reveal_depth_m`)")
        wd, off, hd = float(pd["width_m"]), float(pd["offset_m"]), float(pd["height_m"])
        if "loggia" in door_kit_in:   # T-2910: the door stands in the loggia's back wall, checked there
            pass
        elif not 0.8 <= wd <= door_w - 0.3 or abs(off) + wd / 2 > door_w / 2 - 0.1 or not 2.0 <= hd < door_h:
            raise ParamError(f"entrance_kit.porch_door: a {wd} m door {off:+.2f} m off the axis, {hd} m high, does "
                             f"not stand 0.1 m inside the {door_w} m arch under its {door_h} m crown")
        door_kit["porch_door"] = {"width_m": wd, "offset_m": off, "height_m": hd, "leaves": int(pd["leaves"]),
                                  "panels": [int(x) for x in pd["panels"]], "transom_m": float(pd["transom_m"]),
                                  **({"glazed_rows": [int(x) for x in pd["glazed_rows"]]}
                                     if "glazed_rows" in pd else {})}
    # T-2952: a side light beside the door under the arch's transom (1812's, the Levy print): the
    # door's leaves take the left of the mouth, then a pier `pier_m` wide, then a glazed light
    # `width_m` across from a sill `sill_m` over the floor up to the transom, a panel under it
    if "side_light" in door_kit_in:
        sl = door_kit_in["side_light"]
        if not door_arch or "opening_m" not in door_kit_in or "porch_door" in door_kit_in \
                or set(sl) != {"width_m", "pier_m", "sill_m"}:
            raise ParamError("entrance_kit.side_light takes width_m, pier_m and sill_m, under a round- or "
                             "segmental-arched door's own mouth (`arch`, `opening_m`; no porch_door)")
        lw, pw, ls = (float(sl[k]) for k in ("width_m", "pier_m", "sill_m"))
        if not 0.5 <= lw <= 1.5 or not 0.15 <= pw <= 0.5 or not 0.3 <= ls <= 1.5 or door_w - lw - pw < 1.0:
            raise ParamError(f"entrance_kit.side_light {sl}: a light 0.5-1.5 m across beside a 0.15-0.5 m pier, "
                             f"its sill 0.3-1.5 m up, leaving the door 1.0 m of the {door_w} m mouth")
        door_kit["side_light"] = {"width_m": lw, "pier_m": pw, "sill_m": ls}
    # T-3134: under such a mouth a heavy moulded transom beam `depth_m` deep (a cap and a bead,
    # each [high, proud]), and the fanlight over it parted by two narrow columns of small panes
    # (`width_m` between their posts, `rows` panes up), over the leaves' meeting and the pier
    if "transom_beam" in door_kit_in:
        tb = door_kit_in["transom_beam"]
        if "side_light" not in door_kit or not isinstance(tb, dict) or set(tb) != {"depth_m", "cap_m", "bead_m"}:
            raise ParamError("entrance_kit.transom_beam takes depth_m, cap_m and bead_m, under a side-lit mouth")
        dp, cap, bead = float(tb["depth_m"]), [float(x) for x in tb["cap_m"]], [float(x) for x in tb["bead_m"]]
        ros = float(door_arch.get("rise_over_span", 0.5))
        if not 0.07 <= dp <= 0.4 or cap[0] + bead[0] > dp or not 0.0 < cap[1] <= 0.08 or not 0.0 < bead[1] <= 0.08 \
                or door_h - door_w * ros - dp < 2.0:
            raise ParamError(f"entrance_kit.transom_beam {tb}: a beam 0.07-0.4 m deep holding its cap and bead, "
                             f"each at most 0.08 m proud, leaving the leaves 2.0 m under it")
        door_kit["transom_beam"] = {"depth_m": dp, "cap_m": cap, "bead_m": bead}
    if "fanlight_columns" in door_kit_in:
        fc = door_kit_in["fanlight_columns"]
        if "side_light" not in door_kit or not isinstance(fc, dict) \
                or not {"width_m", "rows"} <= set(fc) <= {"width_m", "rows", "offsets_m"} \
                or not 0.1 <= float(fc["width_m"]) <= 0.5 or not 1 <= int(fc["rows"]) <= 8:
            raise ParamError("entrance_kit.fanlight_columns takes width_m (0.1-0.5 m) and rows (1-8), over a "
                             "side-lit mouth (and offsets_m)")
        door_kit["fanlight_columns"] = {"width_m": float(fc["width_m"]), "rows": int(fc["rows"])}
        # T-3236: the two columns at `offsets_m` from the mouth's axis, not over the leaves' meeting
        # and the pier (1812's, the owner's report: the fanlight set even under the arch)
        if "offsets_m" in fc:
            off = [float(x) for x in fc["offsets_m"]]
            if len(off) != 2 or not -door_w / 2 + 0.2 < off[0] < off[1] < door_w / 2 - 0.2:
                raise ParamError(f"entrance_kit.fanlight_columns.offsets_m {fc['offsets_m']}: two offsets from the "
                                 f"mouth's axis, south to north, 0.2 m inside its {door_w} m")
            door_kit["fanlight_columns"]["offsets_m"] = off
    # T-3236: the leaves' own joinery (1812's, the owner's report that the door read flat):
    # `panels` [across, up] on `rails_y_m`, the panels sunk `panel_recess_m` with a raised field
    # `margin_m` in and `proud_m` before their ground, and the joinery's `color` (linear RGB)
    if "leaf" in door_kit_in:
        lv = door_kit_in["leaf"]
        need = {"panels", "rails_y_m", "panel_recess_m", "raised_field", "color"}
        if not isinstance(lv, dict) or set(lv) != need or set(lv["raised_field"]) != {"margin_m", "proud_m"}:
            raise ParamError(f"entrance_kit.leaf takes {sorted(need)}; raised_field takes margin_m and proud_m")
        cols, rows = (int(x) for x in lv["panels"])
        ry = [float(x) for x in lv["rails_y_m"]]
        rec, mg, up = float(lv["panel_recess_m"]), float(lv["raised_field"]["margin_m"]), float(lv["raised_field"]["proud_m"])
        col = [float(x) for x in lv["color"]]
        if not 1 <= cols <= 3 or not 1 <= rows <= 5 or len(ry) != rows - 1 or ry != sorted(ry) \
                or not 0.01 <= rec <= 0.05 or not 0.02 <= mg <= 0.12 or not 0.0 < up < rec \
                or len(col) != 3 or not all(0.0 <= c <= 1.0 for c in col):
            raise ParamError(f"entrance_kit.leaf {lv}: 1-3 panels across and 1-5 up on rows-1 rising rails, sunk "
                             f"0.01-0.05 m, the field 0.02-0.12 m in and raised less than the sinking, a linear RGB")
        door_kit["leaf"] = {"panels": [cols, rows], "rails_y_m": ry, "panel_recess_m": rec,
                            "raised_field": {"margin_m": mg, "proud_m": up}, "color": col}
    # T-2910: a loggia behind the arch (1801's, the Taylor photograph): a room `v_m` [from, to]
    # along the front and `depth_m` behind its face, its floor the door's, a flat ceiling
    # `ceiling_m` over it, the porch door in its back wall; and `side_arch`, a round arch
    # through the end wall the room stands against, onto the street round the corner
    if "loggia" in door_kit_in:
        lg = door_kit_in["loggia"]
        need = {"v_m", "depth_m", "ceiling_m"}
        if not door_arch or "porch_door" not in door_kit_in \
                or not need <= set(lg) <= need | {"side_arch", "carving", "columns", "round_arcade"}:
            raise ParamError(f"entrance_kit.loggia takes {sorted(need)} and optionally side_arch, carving, "
                             f"columns and round_arcade, behind a "
                             f"round-arched door's (`arch`) mouth with its porch_door at the back")
        v0, v1 = sorted(float(x) for x in lg["v_m"])
        D, Hc = float(lg["depth_m"]), float(lg["ceiling_m"])
        pd = door_kit["porch_door"]
        if not (st - 1e-9 <= v0 < door_s - door_w / 2 - 0.1 and door_s + door_w / 2 + 0.1 < v1 <= width - st + 1e-9):
            raise ParamError(f"entrance_kit.loggia.v_m {lg['v_m']}: the room holds the {door_w} m arch at v "
                             f"{door_s} with 0.1 m each side, inside the side walls")
        if not ft + 1.0 <= D <= depth / 2 or not door_h + 0.1 <= Hc <= heights[0] - 0.3:
            raise ParamError(f"entrance_kit.loggia: {D} m deep (at least 1.0 m behind the {ft} m front wall, at "
                             f"most half the house) under a {Hc} m ceiling (over the arch's {door_h} m crown, "
                             f"0.3 m under the floor above)")
        a_, b_ = door_s + pd["offset_m"] - pd["width_m"] / 2, door_s + pd["offset_m"] + pd["width_m"] / 2
        if not (v0 + 0.15 <= a_ and b_ <= v1 - 0.15 and 0.8 <= pd["width_m"] and 2.0 <= pd["height_m"] <= Hc - 0.2):
            raise ParamError(f"entrance_kit.porch_door: a {pd['width_m']} m door {pd['height_m']} m high does not "
                             f"stand 0.15 m inside the loggia's back wall (v {v0}-{v1}) under its {Hc} m ceiling")
        loggia = {"front_wall_m": ft, "depth_m": D, "ceiling_m": Hc, "s_m": [v0 - door_s, v1 - door_s]}
        sa = lg.get("side_arch")
        if sa is not None:
            need = {"centre_m", "clear_width_m", "clear_height_m", "ring_m", "keystone_top_m", "keystone_m"}
            if not need <= set(sa) <= need | {"balcony"}:
                raise ParamError(f"entrance_kit.loggia.side_arch takes {sorted(need)} and optionally balcony")
            if abs(v0 - st) < 1e-6:
                side, wall = "left", "k01.wall.side.south"
            elif abs(v1 - (width - st)) < 1e-6:
                side, wall = "right", "k01.wall.side.north"
            else:
                raise ParamError("entrance_kit.loggia.side_arch opens an end wall: the room stands against one "
                                 "(v_m from the side wall's thickness, or to the front's width less it)")
            c, w, h = float(sa["centre_m"]), float(sa["clear_width_m"]), float(sa["clear_height_m"])
            if not 1.0 <= w <= 2.2 or not w / 2 + 1.0 <= h <= Hc - 0.1 or not ft + 0.1 <= c - w / 2 \
                    or not c + w / 2 <= D - 0.1:
                raise ParamError(f"entrance_kit.loggia.side_arch: a {w} m arch {h} m to its crown, centred {c} m "
                                 f"behind the front, does not stand in the loggia's side wall ({ft}-{D} m, "
                                 f"ceiling {Hc} m)")
            ring, ktop = float(sa["ring_m"]), float(sa["keystone_top_m"])
            if not 0.15 <= ring <= 0.6 or not ktop >= door_floor + h + ring:
                raise ParamError("entrance_kit.loggia.side_arch: a voussoir ring 0.15-0.6 m, its keystone "
                                 "above the ring's top")
            arch = {"side": side, "wall": wall, "centre_m": c, "clear_width_m": w, "clear_height_m": h,
                    "wall_m": st, "ring_m": ring, "keystone_top_m": ktop,
                    "keystone_m": [float(x) for x in sa["keystone_m"]]}
            if "balcony" in sa:
                bl = sa["balcony"]
                if set(bl) != {"span_m", "out_m", "height_m", "corbel_m"}:
                    raise ParamError("entrance_kit.loggia.side_arch.balcony takes span_m, out_m, height_m, corbel_m")
                e0, e1 = sorted(float(x) for x in bl["span_m"])
                if not 0.0 <= e0 < c - w / 2 and c + w / 2 < e1 <= depth or not 0.1 <= float(bl["out_m"]) <= 1.0 \
                        or float(bl["height_m"]) + float(bl["corbel_m"]) >= door_floor:
                    raise ParamError("entrance_kit.loggia.side_arch.balcony: under the arch along the wall, "
                                     "0.1-1.0 m out, its corbel clear of grade")
                arch["balcony"] = {"span_m": [e0, e1], "out_m": float(bl["out_m"]),
                                   "height_m": float(bl["height_m"]), "corbel_m": float(bl["corbel_m"])}
            loggia["side_arch"] = arch
        if "carving" in lg:
            loggia["carving"] = _loggia_carving(lg["carving"], door_w, door_h, door_floor)
        if "columns" in lg:
            if "carving" in lg:
                raise ParamError("entrance_kit.loggia: its carving's piers or its columns carry the arch, not both")
            loggia["columns"] = _loggia_columns(lg["columns"], door_w, door_h)
        if "round_arcade" in lg:
            if "columns" not in lg:
                raise ParamError("entrance_kit.loggia.round_arcade: its colonnettes are the mouth's columns "
                                 "carried round the corner, so it needs columns")
            loggia["round_arcade"] = _round_arcade(lg["round_arcade"], door_floor, door_floor + door_h - door_w / 2,
                                                   v0, v1, loggia["columns"]["plinth_m"])
        door_kit["loggia"] = loggia
    # T-2910: a stoop's cheeks swept down from the landing to a block at the foot
    if "cheek_form" in door_kit_in and isinstance(door_kit_in["cheek_form"], dict) \
            and door_kit_in["cheek_form"].get("kind") == "scrolled":
        # T-2918: a stoop's cheeks swept down to a rolled scroll at the foot, K07's carved cheek
        # (1808's, T-2565); 1811's plate draws its stair between them
        cf = door_kit_in["cheek_form"]
        # T-3186: or beside open terraces at the landing's depth, each cheek's head standing on
        # the landing's front edge (1901's portico, its terraces either side of the stoop)
        ters = door_kit_in.get("terrace")
        ters = ters if isinstance(ters, list) else [ters] if ters else []
        if "side_stoop" in door_kit_in or door_kit_in.get("cheeks") is False \
                or any(not isinstance(t, dict) or set(t) & {"out_m", "loggia", "parapet"} for t in ters) \
                or set(cf) - {"kind", "foot_block_m", "bow", "pierced"}:
            raise ParamError("entrance_kit.cheek_form 'scrolled' is a stoop's own two cheeks (no side stoop; "
                             "a terrace beside it only open, at the landing's depth), optionally on a foot_block_m, "
                             "with a bow and pierced")
        door_kit["cheek_form"] = {"kind": "scrolled"}
        # T-2984: the roll raised onto a plain foot block, its top `foot_block_m` over grade
        if "foot_block_m" in cf:
            fb = float(cf["foot_block_m"])
            if not 0.2 <= fb <= 1.0:
                raise ParamError("entrance_kit.cheek_form.foot_block_m: a scroll's foot block is 0.2-1.0 m tall")
            door_kit["cheek_form"]["foot_block_m"] = fb
        # T-3186: the sweep's power, 1 a straight rake onto the roll up to 2, the concave fall
        if "bow" in cf:
            bw = float(cf["bow"])
            if not 1.0 <= bw <= 2.0:
                raise ParamError("entrance_kit.cheek_form.bow: a scrolled cheek's sweep falls with a power of 1 "
                                 "(straight) to 2 (the concave default)")
            door_kit["cheek_form"]["bow"] = bw
        # T-3186: a row of openings through both cheeks under their coping (1901's, the 1893 plate)
        if "pierced" in cf:
            pc = cf["pierced"]
            if not isinstance(pc, dict) or set(pc) != {"count", "hole_m", "under_m", "span_m"} \
                    or not 1 <= int(pc["count"]) <= 12 or len(pc["hole_m"]) != 2 \
                    or not 0.05 <= float(pc["hole_m"][0]) <= 0.5 or not 0.05 <= float(pc["hole_m"][1]) <= 0.4 \
                    or not 0.05 <= float(pc["under_m"]) <= 0.3 or not 0.3 <= float(pc["span_m"]) <= 6.0:
                raise ParamError("entrance_kit.cheek_form.pierced on a scrolled cheek is {count 1-12, hole_m "
                                 "[0.05-0.5 along, 0.05-0.4 high], under_m 0.05-0.3 under its top, span_m 0.3-6 "
                                 "along the sweep from its head}")
            door_kit["cheek_form"]["pierced"] = {"count": int(pc["count"]),
                                                 "hole_m": [float(x) for x in pc["hole_m"]],
                                                 "under_m": float(pc["under_m"]), "span_m": float(pc["span_m"])}
    elif "cheek_form" in door_kit_in:
        cf = door_kit_in["cheek_form"]
        if not isinstance(cf, dict) or cf.get("kind") != "swept" \
                or not {"kind", "head_m", "foot_m", "block_m"} <= set(cf) <= {"kind", "head_m", "foot_m", "block_m",
                                                                             "flare", "newel", "pierced"} \
                or "side_stoop" in door_kit_in or door_kit_in.get("cheeks") is False \
                or any("parapet" not in t or "loggia" in t
                       for t in ([door_kit_in["terrace"]] if isinstance(door_kit_in.get("terrace"), dict)
                                 else door_kit_in.get("terrace") or [])):
            # T-2952: a terrace beside a swept stoop stands behind a parapet, not a balustrade
            raise ParamError("entrance_kit.cheek_form is {kind: 'swept', head_m, foot_m, block_m}, on a "
                             "stoop's own cheeks (no side stoop; a terrace beside it only behind its parapet)")
        if not 0.0 <= float(cf["head_m"]) <= 0.6 or not 0.3 <= float(cf["foot_m"]) <= 1.2 or not 0.2 <= float(cf["block_m"]) <= 1.0:
            raise ParamError("entrance_kit.cheek_form: head_m 0-0.6 m over the landing, foot_m 0.3-1.2 m over "
                             "grade, block_m 0.2-1.0 m")
        door_kit["cheek_form"] = {k: (v if k == "kind" else float(v)) for k, v in cf.items()
                                  if k not in ("flare", "newel", "pierced")}
        # T-3134: the right cheek flared out `out_m` toward its foot, and each foot block a newel
        # `width_m` across under a cap `cap_m` [high, overhang] and a knob `knob_m` high (1812's
        # stair, the Levy print)
        # T-3144: or one a side, as a list, and a cheek drawn in toward the axis (a negative
        # out_m, to 0.5 m: 1812's south cheek) rather than carried out
        if "flare" in cf:
            fls = cf["flare"] if isinstance(cf["flare"], list) else [cf["flare"]]
            sides = [fl.get("side") for fl in fls if isinstance(fl, dict)]
            if len(sides) != len(fls) or not fls or len(set(sides)) != len(sides) \
                    or any(set(fl) != {"side", "out_m"} or fl["side"] not in ("left", "right")
                           or not (0.1 <= float(fl["out_m"]) <= 1.2 or -0.5 <= float(fl["out_m"]) <= -0.05)
                           for fl in fls):
                raise ParamError("entrance_kit.cheek_form.flare is {side: 'left'|'right', out_m 0.1-1.2 m out "
                                 "or -0.5 to -0.05 m drawn in}, or a list of one a side")
            out = [{"side": fl["side"], "out_m": float(fl["out_m"])} for fl in fls]
            door_kit["cheek_form"]["flare"] = out if isinstance(cf["flare"], list) else out[0]
        # T-3144: a row of small openings through one cheek under its top (1812's north cheek)
        if "pierced" in cf:
            pc = cf["pierced"]
            if not isinstance(pc, dict) or set(pc) != {"side", "count", "hole_m", "under_m"} \
                    or pc["side"] not in ("left", "right") or not 1 <= int(pc["count"]) <= 24 \
                    or len(pc["hole_m"]) != 2 or not all(0.03 <= float(x) <= 0.3 for x in pc["hole_m"]) \
                    or not 0.03 <= float(pc["under_m"]) <= 0.4:
                raise ParamError("entrance_kit.cheek_form.pierced is {side, count 1-24, hole_m [0.03-0.3 along, "
                                 "0.03-0.3 high], under_m 0.03-0.4 under the cheek's top}")
            door_kit["cheek_form"]["pierced"] = {"side": pc["side"], "count": int(pc["count"]),
                                                 "hole_m": [float(x) for x in pc["hole_m"]],
                                                 "under_m": float(pc["under_m"])}
        if "newel" in cf:
            nw = cf["newel"]
            if set(nw) != {"width_m", "cap_m", "knob_m"} or not 0.3 <= float(nw["width_m"]) <= 0.8 \
                    or not 0.04 <= float(nw["cap_m"][0]) <= 0.25 or not 0.0 <= float(nw["cap_m"][1]) <= 0.1 \
                    or not 0.0 < float(nw["knob_m"]) <= 0.4:
                raise ParamError("entrance_kit.cheek_form.newel takes width_m 0.3-0.8, cap_m [0.04-0.25 high, "
                                 "0-0.1 over] and knob_m to 0.4")
            door_kit["cheek_form"]["newel"] = {"width_m": float(nw["width_m"]),
                                               "cap_m": [float(x) for x in nw["cap_m"]], "knob_m": float(nw["knob_m"])}
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
        # T-2963: a hood may stand on columns (1816's porch) and rail its top in iron
        # T-3159: or be laid, columns, balustrade and all, in the front's stone (1729's portico)
        # T-3210: and turn round arches between them (1827's porch)
        extra = {"columns", "railing_fabric", "fabric", "centre_v_m", "under_head_m", "arches"}
        if not need <= set(hd) <= need | extra or set(hd["cornice"]) != {"height_m", "proud_m"} or \
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
        # T-2963: a porch, not a hood: a turned column on a square plinth at each front corner
        # of the deck, from the landing to the soffit, under a square capital block, and a
        # flat respond against the wall behind it. The landing has to reach under them
        if "columns" in hd:
            co = hd["columns"]
            if not {"diameter_m", "plinth_m", "capital_m", "respond_m"} <= set(co) <= \
                    {"diameter_m", "plinth_m", "capital_m", "respond_m", "at_v_m", "carved"}:
                raise ParamError("entrance_kit.hood.columns takes diameter_m, plinth_m [width, height], "
                                 "capital_m and respond_m, and optionally at_v_m and carved")
            dia, (pw, ph), cap, rsp = float(co["diameter_m"]), (float(x) for x in co["plinth_m"]), \
                float(co["capital_m"]), float(co["respond_m"])
            if not (0.15 <= dia <= 0.6 and dia < pw <= 0.8 and 0.1 <= ph <= 0.8 and 0.1 <= cap <= 0.6
                    and 0.05 <= rsp <= 0.3):
                raise ParamError("entrance_kit.hood.columns: a 0.15-0.6 m shaft on a wider plinth up to 0.8 m "
                                 "square and 0.8 m high, a 0.1-0.6 m capital and a 0.05-0.3 m respond")
            if hd["out_m"] < pw + 0.3 or hd["width_m"] < 2 * pw + 0.8:
                raise ParamError("entrance_kit.hood.columns: the hood is too small to stand on two columns")
            # T-3159: or on a terrace either side of a narrower stoop, at the landing's height,
            # that carries the deck on to the hood's ends (1729's portico, its flight at the north end)
            hc = float(hd.get("centre_v_m", door_s))
            hs0, hs1 = hc - hd["width_m"] / 2, hc + hd["width_m"] / 2
            sv, sh = float(door_kit_in.get("stoop_v_m", door_s)), float(val("stoop_width_m")) / 2
            ters = door_kit.get("terrace")
            ters = ters if isinstance(ters, list) else [ters] if ters else []
            lo = min([sv - sh] + [t["to_v_m"] for t in ters if t["side"] == "left"])
            hi = max([sv + sh] + [t["to_v_m"] for t in ters if t["side"] == "right"])
            if float(val("stair_landing_depth_m")) < hd["out_m"] - 0.05 or lo > hs0 + 0.05 or hi < hs1 - 0.05:
                raise ParamError("entrance_kit.hood.columns stand on the stoop's landing, or the terraces beside "
                                 "it: they must be as deep as the hood is out and reach both its ends")
            door_kit["hood"]["columns"] = {"diameter_m": dia, "plinth_m": [pw, ph], "capital_m": cap, "respond_m": rsp}
            # T-3159: the columns' centres along the front (the front's own v), where a picture
            # puts them, in place of one at each front corner
            if "at_v_m" in co:
                at = sorted(float(x) for x in co["at_v_m"])
                if not 2 <= len(at) <= 8 or at[0] < hs0 + pw / 2 + 0.05 - 1e-6 or at[-1] > hs1 - pw / 2 - 0.05 + 1e-6 \
                        or any(b - a < pw + 0.3 for a, b in zip(at, at[1:])):
                    raise ParamError(f"entrance_kit.hood.columns.at_v_m {at}: two to eight columns under the hood "
                                     f"(v {hs0:.3f}-{hs1:.3f}), their plinths inside its ends and 0.3 m apart")
                door_kit["hood"]["columns"]["at_s_m"] = [round(a - door_s, 4) for a in at]
            # T-3186: the capitals carved as a bell of leaves in `tiers` under an abacus `abacus_m`
            # deep, the bay columns' carving (T-2887) (1901's Corinthian capitals, the 1898 photograph)
            if "carved" in co:
                cv = co["carved"]
                if not isinstance(cv, dict) or set(cv) != {"tiers", "abacus_m"} or cv["tiers"] not in (1, 2) \
                        or not 0.03 <= float(cv["abacus_m"]) <= cap - 0.08:
                    raise ParamError("entrance_kit.hood.columns.carved takes tiers (1 or 2) and abacus_m, 0.03 m "
                                     "up to 0.08 m short of the columns' capital")
                door_kit["hood"]["columns"]["carved"] = {"tiers": int(cv["tiers"]), "abacus_m": float(cv["abacus_m"])}
            # T-3210: a round-arched arcade on the columns (1827's porch, the Doane photograph):
            # on the front, an arch from capital to capital between each pair of columns; on an
            # end (`left` the low-v end, `right` the high-v), one from the respond on the wall to
            # the end column. Each a half ellipse `rise_m` high over its clear span, springing at
            # `spring_m` off the capitals, under a spandrel wall to the soffit
            if "arches" in hd:
                ar = hd["arches"]
                if not {"faces", "spring_m", "rise_m"} <= set(ar) <= {"faces", "spring_m", "rise_m"} or \
                        not ar["faces"] or not set(ar["faces"]) <= {"front", "left", "right"} or \
                        len(set(ar["faces"])) != len(ar["faces"]):
                    raise ParamError("entrance_kit.hood.arches takes faces (front, left, right), spring_m and rise_m")
                sp, ri = float(ar["spring_m"]), float(ar["rise_m"])
                floor = float(val("principal_floor_m"))
                if not 0.1 <= ri <= 1.5 or sp - cap < floor + ph + 0.5 or sp + ri > float(hd["soffit_m"]) - 0.05:
                    raise ParamError(f"entrance_kit.hood.arches: a {ri} m rise (0.1-1.5) springing at {sp} m must "
                                     f"clear the columns' plinths with a shaft and stand under the soffit "
                                     f"({hd['soffit_m']} m) by 0.05 m")
                door_kit["hood"]["arches"] = {"faces": list(ar["faces"]), "spring_m": sp, "rise_m": ri}
        if "centre_v_m" in hd:
            # T-1871: the porch's centre along the front, the door under it but off its axis
            off = float(hd["centre_v_m"]) - door_s
            if "columns" not in hd or abs(off) > hd["width_m"] / 2 - 0.9:
                raise ParamError("entrance_kit.hood.centre_v_m: a porch on columns, its door at least 0.9 m "
                                 "inside its ends")
            door_kit["hood"]["offset_m"] = round(off, 4)
        if "fabric" in hd:
            if hd["fabric"] != "stone" or "columns" not in hd:
                raise ParamError("entrance_kit.hood.fabric: stone, for a portico on columns, or leave it out "
                                 "for the painted joinery")
            door_kit["hood"]["fabric"] = "stone"
        if "railing_fabric" in hd:
            # T-3159: or a stone balustrade, its posts, balusters and rail in the hood's stone
            if hd["railing_fabric"] not in ("iron", "stone") or \
                    (hd["railing_fabric"] == "stone" and hd.get("fabric") != "stone"):
                raise ParamError("entrance_kit.hood.railing_fabric: iron, or stone on a stone hood, or leave it "
                                 "out for the painted joinery")
            door_kit["hood"]["railing_fabric"] = hd["railing_fabric"]
    # T-2463: a stoop whose axis is not its door's (1620's, the door at the south end of a
    # landing that runs on north into the porch): the stoop's centre along the front, in the
    # front's own s. The door has to stand on the landing or on a terrace beside it
    if "stoop_v_m" in door_kit_in:
        sv = float(door_kit_in["stoop_v_m"])
        half, dh = float(val("stoop_width_m")) / 2, door_w / 2
        sides = {t["side"] for t in (door_kit.get("terrace") or [])} if isinstance(door_kit.get("terrace"), list) \
            else ({door_kit["terrace"]["side"]} if door_kit.get("terrace") else set())
        if not 0 <= sv - half or not sv + half <= width:
            raise ParamError(f"entrance_kit.stoop_v_m: a {2 * half} m stoop on v {sv} leaves the front")
        # T-3135: or on the floor of a projection the arch is cut into, abutting the landing
        for q in val("bays") or ():
            if q.get("cut_by_entrance") is True and q.get("wall") == "k01.wall.street_front":
                qa = float(q["s_m"]) - float(q["plan"]["width_m"]) / 2
                qb = float(q["s_m"]) + float(q["plan"]["width_m"]) / 2
                if qa < door_s - dh < qb and 0.0 <= sv - half - qb <= 0.1:
                    sides = sides | {"left"}
                if qa < door_s + dh < qb and 0.0 <= qa - (sv + half) <= 0.1:
                    sides = sides | {"right"}
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
            # T-3163: a bow names its chord, a projection its width (1823's pavilion), a
            # polyline its ends on the wall
            pl = bay.get("plan") or {}
            half = (float(pl["chord_m"]) / 2 if "chord_m" in pl else float(pl["width_m"]) / 2 if "width_m" in pl
                    else max(abs(float(x)) for x, _ in pl["points"]))
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
            elif st_.get("outside_wall"):
                # T-3061: a stack carried up on a side wall's outer face beside the mansard's
                # side parapet (1812's south stack, in the gap to 1816, both its photographs):
                # its inner face is the wall's outer face, and it rises from the ground
                spp = (mansard_roof or {}).get("side_parapet") or {}
                if not spp:
                    raise ParamError(f"chimney at ({u}, {v}): only a wall carried up as a mansard's side "
                                     "parapet carries a stack on its outer face")
                if not (sx / 2 + 0.3 <= u <= depth - sx / 2 - 0.3):
                    raise ParamError(f"chimney at ({u}, {v}) does not stand along the side wall")
                if abs(v + sz / 2) > 1e-6 if spp["wall"] == "south" else abs(v - sz / 2 - width) > 1e-6:
                    raise ParamError(f"chimney at ({u}, {v}): an outside stack's inner face is the "
                                     f"{spp['wall']} wall's outer face")
                if "top_m" not in st_ or float(st_["top_m"]) < spp["top_m"] + 0.6 - 1e-9:
                    raise ParamError(f"chimney at ({u}, {v}): an outside stack names its top_m, 0.6 m or more "
                                     f"over the parapet's {spp['top_m']} m")
                base = 0.0
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
                elif gable and st_.get("in_parapet"):
                    # T-3050: a parapet stack read off a picture stands at its own top (1811's
                    # tall south stack, its 1888 plate), clearing the ridge by the same 0.6 m
                    if top < gable_roof["ridge_m"] + 0.6 - 1e-9:
                        raise ParamError(f"chimney at ({u}, {v}) tops at {top} m, under the ridge's "
                                         f"{gable_roof['ridge_m']} m + 0.6")
                elif not mansard:
                    raise ParamError(f"chimney at ({u}, {v}): a top_m of its own is a mansard, a flat "
                                     "roof's or a gable parapet's stack")
                else:
                    crown = (val("mansard") or {}).get("crown") or {}
                    curb = mansard_roof["curb_m"] + float(crown.get("rise_above_curb_m", 0.0))
                    if top < curb + 0.6 - 1e-9:
                        raise ParamError(f"chimney at ({u}, {v}) tops at {top} m, under the curb's {curb} m + 0.6")
            # T-3000: a stack may carry its own cap, as 1801's flank stack its heavy corbelled one
            sp_, sd_ = float(st_.get("cap_proud_m", cap_p)), float(st_.get("cap_depth_m", cap_d))
            if not 0.0 <= sp_ <= 0.4 or not 0.05 <= sd_ <= 0.8:
                raise ParamError(f"chimney at ({u}, {v}): its cap stands 0-0.4 m proud and 0.05-0.8 m deep")
            # T-3003: a stack may be laid in the house's own stone rather than brick, as 1801's
            # two tall south stacks are in HABS photograph 1 (pale ashlar to the cap, the walls' tone)
            fab = st_.get("fabric", "brick")
            if fab not in ("brick", "stone"):
                raise ParamError(f"chimney at ({u}, {v}): fabric is 'brick' or 'stone', not {fab!r}")
            if fab == "stone" and not val("stone_front"):
                raise ParamError(f"chimney at ({u}, {v}): a stone stack stands on a house with a stone front")
            # T-3109: a stone stack may carry a dressed head and base, as 1801's two south stacks
            # do in HABS photograph 1: a broader base from the cornice weathered back to the
            # shaft, a moulded collar, a stage of diamond lattice and the moulded cap over it
            head = st_.get("head")
            if head is not None:
                if fab != "stone" or not mansard or base is None:
                    raise ParamError(f"chimney at ({u}, {v}): a dressed head is a stone stack's on a mansard's cornice")
                bs, cl, sg = head["base"], head["collar"], head["stage"]
                bp, bt, bw = float(bs["proud_m"]), float(bs["top_m"]), float(bs["weathering_m"])
                cp_, cdp = float(cl["proud_m"]), float(cl["depth_m"])
                gp, gd = float(sg["proud_m"]), float(sg["depth_m"])
                lat = sg.get("lattice") or {}
                n_d, rw, rp = int(lat.get("diamonds", 0)), float(lat.get("rib_m", 0.06)), float(lat.get("proud_m", 0.03))
                if not (0.0 < bp <= 0.3 and 0.05 <= bw <= 0.6 and base + 0.5 <= bt - bw):
                    raise ParamError(f"chimney at ({u}, {v}): its base stands 0-0.3 m proud, weathered over "
                                     "0.05-0.6 m, at least 0.5 m over the cornice")
                if max(sz / 2 + bp - v, v + sz / 2 + bp - width) > float(val("eave_overhang_m")) + 1e-9:
                    raise ParamError(f"chimney at ({u}, {v}): its base runs past the cornice's edge")
                if not (0.0 < cp_ <= 0.3 and 0.1 <= cdp <= 0.6 and 0.0 < gp <= cp_ and 0.4 <= gd <= 2.0):
                    raise ParamError(f"chimney at ({u}, {v}): its collar stands 0-0.3 m proud and 0.1-0.6 m deep, "
                                     "its stage 0.4-2.0 m deep and no prouder than the collar")
                if sp_ < cp_ or bt + 0.6 > top - sd_ - gd - cdp:
                    raise ParamError(f"chimney at ({u}, {v}): its cap stands no prouder than its collar, or its "
                                     "shaft shows under 0.6 m between the base and the collar")
                if n_d and not (1 <= n_d <= 4 and 0.03 <= rw <= 0.12 and 0.01 <= rp <= gp + 0.02):
                    raise ParamError(f"chimney at ({u}, {v}): a lattice of 1-4 diamonds a face, ribs 0.03-0.12 m "
                                     "wide and no prouder than the stage's face")
                head = {"base_proud_m": bp, "base_top_m": bt, "weathering_m": bw, "collar_proud_m": cp_,
                        "collar_depth_m": cdp, "stage_proud_m": gp, "stage_depth_m": gd,
                        "diamonds": n_d, "rib_m": rw, "rib_proud_m": rp}
            chimneys.append({"u_m": u, "v_m": v, "plan_m": (sx, sz), "top_m": top, "base_m": base,
                             "cap_proud_m": sp_, "cap_depth_m": sd_, "stone": fab == "stone",
                             **({"head": head} if head else {})})
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
    # T-2842: a tower on a rear wing's wall is read against that wing, so it waits for the wings
    wing_towers = [e for e in val("bays") or () if str(e.get("wall", "")).startswith("k01.wall.wing.")]
    bays = _bays([e for e in val("bays") or () if e not in wing_towers],
                 {"k01.wall.street_front": width, "k01.wall.rear_service": width,
                               "k01.wall.side.south": depth, "k01.wall.side.north": depth},
                 openings, (record or {}).get("id", ""), bool(val("stone_front")), tuple(floors), eave,
                 float(val("eave_overhang_m")), bool((val("stone_front") or {}).get("coursing")),
                 eave_front=(eave - float(val("eave_overhang_m")) * math.tan(math.radians(pitch))
                             if roof_form in ("hip", "gable") else None))
    # T-2780: a round-headed window over a bay is cut after the kit was read, so its variant
    # is held here to what the street front's round heads are held to: one round-headed sash
    for o in openings:
        if o.component == ROUND_HOODED and o.wall != "k01.wall.street_front":
            v6 = variants.get(kit.get(ROUND_HOODED, {}).get("variant"))
            if v6 is None or v6["head"] != "round" or v6.get("bays", 1) != 1:
                raise ParamError(f"window_kit: {ROUND_HOODED} is cut as one round hole over a bay, and names "
                                 f"no single round-headed K06 sash")
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
    spp = (mansard_roof or {}).get("side_parapet")
    if spp:
        # T-3061: no eave gutter runs along a wall carried up as a parapet, so no pipe falls from one
        # there, and the lower face behind it is hidden: it takes no dormer
        wall = f"k01.wall.side.{spp['wall']}"
        if any(x["wall"] == wall for x in rainwater.get("downpipes", [])):
            raise ParamError(f"rainwater.downpipes: no eave gutter runs along the {spp['wall']} wall, which is "
                             "carried up as the mansard's side parapet")
        if any(d.get("face") == spp["wall"] for d in (val("mansard") or {}).get("dormers") or []):
            raise ParamError(f"mansard.dormers: the {spp['wall']} face stands behind the side parapet")
    if (val("mansard") or {}).get("dormers"):
        mansard_roof["dormers"] = _mansard_dormers(val("mansard")["dormers"], mansard_roof, depth, width, eave,
                                                   float(val("eave_overhang_m")), chimneys, val("cant_corner"))
    if (val("mansard") or {}).get("deck"):
        # T-3000: the deck's cresting, finials and corner hoods (1801's, Taylor's photograph)
        from .k01_mansard_deck import ParamError as DeckError, resolve as resolve_deck
        try:
            mansard_roof["deck"] = resolve_deck(val("mansard")["deck"], mansard_roof, depth, width,
                                                float(val("eave_overhang_m")), pitch, chimneys)
        except DeckError as e:
            raise ParamError(str(e)) from None

    wings = _rear_wings(val("rear_wings"), depth, width, openings, cw,
                        opening["parameters"]["clear_height_m"]["range"], (record or {}).get("id", ""))
    if wing_towers:
        wings, more = _wing_towers(wing_towers, wings, (record or {}).get("id", ""), bool(val("stone_front")),
                                   float(val("eave_overhang_m")))
        bays = bays + more

    stone = _k02(val("stone_front") or {})
    if stone:
        # the rusticated base and its coping run up to the area lights' heads, so the
        # coping's top is the line the lights' flat arches spring from (T-2289)
        top = bsill + float(bl["height_m"]) if bl else float((val("street_front_dress") or sfw or {}).get("base_top_m", 0.0))
        if bl and bhead:   # T-3184: tall round-headed lights rise through it: its top is the record's
            top = float(bl.get("base_top_m", -1.0))
            if not bsill < top < bsill + float(bl["height_m"]) - float(bl["width_m"]) / 2:
                raise ParamError("basement_lights.base_top_m: round-headed lights name the plinth's top, "
                                 "over their sills and under their spring")
        if not stone["base_courses"]:
            if bl or abs(top - stone["coping_height_m"]) > 1e-6:
                raise ParamError("stone_front: a plain plinth (no rusticated base courses) is its coping alone, "
                                 "coping_height_m to the plinth's top, under no area light")
            course = 0.0
        else:
            course = (top - stone["coping_height_m"]) / stone["base_courses"]
            _within(course, stone["course_m"], f"the rusticated base's course height ({stone['fabric']} "
                    f"course_height_m; base courses, coping and the area lights' heads must agree)")
        stone["base_course_m"] = round(course, 5)
        stone["coping_top_m"] = round(top, 5)
        if "brick_above_m" in stone:
            # T-2914: a front read off its photograph as stone below and brick above (1812's:
            # its basement and first storey stone, its upper storeys brick banded and dressed
            # in stone). The line is a storey line, so it is the top of that floor's belt and
            # the walling over it is brick; the belts, sills, arches, voussoirs and dressed
            # surrounds stay stone. A quoined corner is stone returned into brick up a
            # stone front, so it is refused here rather than half laid
            ba = stone["brick_above_m"]
            # T-1888: or the principal floor's, a stone basement under a brick front (1834's
            # photograph: the ashlar basement to the water table, every storey over it brick)
            lines = [round(pf + sum(heights[:i]), 4) for i in range(len(heights))]
            if construction == "stone" or not any(abs(ba - f) < 1e-6 for f in lines):
                raise ParamError(f"stone_front.brick_above_m {ba} must be one of the upper storeys' "
                                 f"floor lines {lines}, on a brick house with a stone front")
            if stone["corners"] or "south_return_m" in stone:
                raise ParamError("stone_front.brick_above_m: a front whose stone stops under brick "
                                 "names no corner_bond or south_return_m")
    if construction == "stone":
        # T-2788: an all-stone house's corners are its own courses turned, so it names no
        # quoin bond (a quoin is stone returned into brick), and a bay on it is stone or timber
        if stone["corners"] or "south_return_m" in stone:
            raise ParamError("construction 'stone': its courses turn every corner, so its "
                             "stone_front names no corner_bond or south_return_m")
        brick_bays = [b["id"] for b in bays if b["fabric"] == "brick"]
        if brick_bays:
            raise ParamError(f"construction 'stone': bays {brick_bays} are brick; an all-stone "
                             "house lays its bays in stone, its front's stone or frame")
        stone["all_round"] = True

    # T-1861: a brick street front may lay its windows' heads in the brick, as its side and
    # rear walls do (two rowlock rings on a segmental arch), instead of the stone lintel or
    # K09 head `by_storey` names; the hole stays the K01 rectangle, so the sash stays flat
    trim = dict(val("street_front_trim", {}) or {})
    if trim.get("brick_heads") not in (None, "segmental"):
        raise ParamError("street_front_trim.brick_heads builds 'segmental' alone")
    if trim.get("brick_heads") and construction != "brick":
        raise ParamError("street_front_trim.brick_heads arches the brick; a stone front is laid "
                         "by its K02 stone_front")
    # T-3197: a front bay's lights under a carved tympanum on a stone lintel, in place of the
    # K09 head its storey names (1827's window bay south of the pavilion, the Doane photograph)
    if "tympana" in trim:
        tys = []
        bays_v = [float(x) for x in (val("front_bays") or [])]
        for e in trim["tympana"]:
            keys = {"s_m", "storeys", "lintel_m", "lintel_proud_m", "tympanum"}
            if not isinstance(e, dict) or set(e) != keys or not 0.1 <= float(e["lintel_m"]) <= 0.4 \
                    or not 0.03 <= float(e["lintel_proud_m"]) <= 0.15:
                raise ParamError(f"street_front_trim.tympana takes {sorted(keys)} (a lintel 0.1-0.4 m deep, "
                                 f"0.03-0.15 m proud), not {e}")
            if not any(abs(float(e["s_m"]) - b) < 1e-6 for b in bays_v):
                raise ParamError(f"street_front_trim.tympana: s_m {e['s_m']} is not one of front_bays {bays_v}")
            st = sorted({int(k) for k in e["storeys"]})
            if not st or not all(0 <= k < int(val("stories")) for k in st):
                raise ParamError(f"street_front_trim.tympana: storeys {e['storeys']} are not this front's "
                                 f"storeys (0-{int(val('stories')) - 1}, as by_storey counts them)")
            tys.append({"s_m": float(e["s_m"]), "storeys": st, "lintel_m": float(e["lintel_m"]),
                        "lintel_proud_m": float(e["lintel_proud_m"]),
                        "tympanum": tympanum_spec(e["tympanum"], "street_front_trim.tympana",
                                                  float(e["lintel_proud_m"]))})
        trim["tympana"] = tys

    # T-1890: single lights named by wall, place and storey, each wearing its storey's head on
    # a side wall too (1801's light over the loggia's 18th Street arch, framed as its pair over
    # the loggia on the avenue front is in the Taylor print), and each its own transom `tiers`
    # where its picture draws the bar lower than K06's transom light
    if "lights" in trim:
        lts = []
        for e in trim["lights"]:
            keys = {"wall", "s_m", "storey"}
            ok = isinstance(e, dict) and keys <= set(e) <= keys | {"tiers", "pilasters"} \
                and e["wall"] in ("k01.wall.street_front", "k01.wall.side.south", "k01.wall.side.north") \
                and isinstance(e["storey"], int) and 0 <= e["storey"] < int(val("stories"))
            hits = [o for o in openings if ok and o.wall == e["wall"] and o.component == "k01.opening.sash_flat"
                    and abs(o.s_m - float(e["s_m"])) < 1e-6
                    and max(k for k, f in enumerate(floors) if o.sill_m >= f - 1e-6) == e["storey"]]
            if len(hits) != 1:
                raise ParamError(f"street_front_trim.lights: {e} names no one square-headed light by its wall "
                                 f"(street front or a side), s_m and storey, with an optional tiers")
            out = {"wall": e["wall"], "s_m": float(e["s_m"]), "storey": e["storey"]}
            if "tiers" in e:
                t, h = e["tiers"], hits[0].height_m
                if not isinstance(t, dict) or set(t) != {"bar_m", "lights_m"} or not 1 <= len(t["lights_m"]) <= 3 \
                        or not 0.05 <= float(t["bar_m"]) <= 0.3 \
                        or not all(0.2 <= float(x) <= 1.0 for x in t["lights_m"]) \
                        or h - sum(float(x) for x in t["lights_m"]) - float(t["bar_m"]) * len(t["lights_m"]) < 1.0:
                    raise ParamError(f"street_front_trim.lights: tiers take bar_m (0.05-0.3 m) and one to three "
                                     f"lights_m (0.2-1.0 m each), leaving at least 1.0 m of sash under them, not {t}")
                out["tiers"] = {"bar_m": float(t["bar_m"]), "lights_m": [float(x) for x in t["lights_m"]]}
            if "pilasters" in e:
                # T-1890: a carved pilaster each side of a surrounded light (1801's lights over the
                # loggia, the Taylor print), on a base from `foot_m` over grade under its sill, to a
                # capital carrying the hood's end, the shaft's face carved as K08's are (T-2931)
                pl, o = e["pilasters"], hits[0]
                pk = {"width_m", "proud_m", "base_m", "capital_m", "gap_m", "foot_m"}
                lk = {"count", "height_m", "margin_m", "relief_m"}
                ok = isinstance(pl, dict) and pk <= set(pl) <= pk | {"lozenges"} \
                    and (trim.get("by_storey") or [None] * (e["storey"] + 1))[e["storey"]] == "k09.surround.rowhouse_restrained"
                if ok:
                    w, d, hb, hc, g, ft = (float(pl[k]) for k in ("width_m", "proud_m", "base_m", "capital_m", "gap_m", "foot_m"))
                    ok = 0.1 <= w <= 0.4 and 0.02 <= d <= 0.1 and 0.05 <= hb <= 0.3 and 0.1 <= hc <= 0.5 \
                        and 0.06 <= g <= 0.3 and floors[e["storey"]] - 0.5 <= ft <= o.sill_m - 0.1 \
                        and o.head_m + 0.15 - hc - (ft + hb) >= 1.0
                lz = pl.get("lozenges") if ok else None
                if lz is not None:
                    ok = isinstance(lz, dict) and set(lz) == lk and isinstance(lz["count"], int) \
                        and 1 <= lz["count"] <= 6 and 0.1 <= float(lz["height_m"]) <= 1.0 \
                        and lz["count"] * (float(lz["height_m"]) + 0.1) <= o.head_m + 0.15 - hc - (ft + hb) \
                        and 0.01 <= float(lz["margin_m"]) < w / 2 - 0.02 and 0.005 <= float(lz["relief_m"]) <= 0.04
                if not ok:
                    raise ParamError(f"street_front_trim.lights: pilasters stand beside a light its storey's "
                                     f"k09.surround.rowhouse_restrained dresses, and take width_m (0.1-0.4 m), "
                                     f"proud_m (0.02-0.1 m), base_m (0.05-0.3 m), capital_m (0.1-0.5 m), gap_m "
                                     f"(0.06-0.3 m) clear of the architrave, foot_m (half a metre under the storey's "
                                     f"floor at most, 0.1 m under the sill at least, a metre of shaft over it) and "
                                     f"optional lozenges ({sorted(lk)}: one to six, 0.1-1.0 m tall, a tenth of a "
                                     f"metre apart at least, inside the shaft), not {pl}")
                out["pilasters"] = {"width_m": w, "proud_m": d, "base_m": hb, "capital_m": hc, "gap_m": g, "foot_m": ft,
                                    **({"lozenges": {"count": lz["count"], **{k: float(lz[k]) for k in
                                                                             ("height_m", "margin_m", "relief_m")}}} if lz else {})}
            lts.append(out)
        trim["lights"] = lts

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
    cant_corner = _cant_corner(val("cant_corner"), depth, width, openings, bays, rainwater, chimneys,
                               construction=construction, roof_form=roof_form, mansard=mansard_roof,
                               wall_head=dict(val("wall_head", {}) or {}),
                               others={"round_corner": val("round_corner"), "front_pier": val("front_pier"),
                                       "street_front_pavilions": val("street_front_pavilions"),
                                       "shaped_gable": val("shaped_gable"),
                                       "a shallow pavilion": [b for b in bays if b["variant"].get("shallow")]},
                               floors=floors, sash=sash, basement=bl)
    round_corner = _round_corner(val("round_corner"), depth, width, stone, openings, bays, rainwater,
                                 side_belts=val("side_belts") or (), frontispiece=frontispiece)
    front_pier = _front_pier(val("front_pier"), stone, openings, bays, rainwater, round_corner, roof_form,
                             mansard_roof, pf + sum(heights))
    from .k01_pavilions import ParamError as PavilionError, resolve as resolve_pavilions
    try:
        pavilions = resolve_pavilions(val("street_front_pavilions"), width=width, stone=stone, openings=openings,
                                      mansard=mansard_roof, eave=pf + sum(heights),
                                      wall_head=dict(val("wall_head", {}) or {}), depth=depth, bays=bays)
    except PavilionError as e:
        raise ParamError(str(e)) from None
    from .k01_porte_cochere import ParamError as PorteError, resolve as resolve_porte
    try:
        porte_cochere = resolve_porte(val("porte_cochere"), depth=depth, width=width, stone=stone, openings=openings)
    except PorteError as e:
        raise ParamError(str(e)) from None
    lg_ = (door_kit or {}).get("loggia") or {}
    round_arcade_check(lg_.get("round_arcade"), round_corner, lg_.get("columns"), width)
    # T-2997: a pipe on a return stands on a street projection's square high-s return, at
    # least its head's half-width (0.14 m) and 0.01 m clear of the projection's face and the
    # main front
    for x in (rainwater or {}).get("front_pipes", []):
        if x.get("on") != "return":
            continue
        rets = [b["s_m"] + pts[-1][0] for b in bays if b["wall"] == "k01.wall.street_front"
                for pts in [((b.get("variant") or {}).get("plan") or {}).get("points") or []
                            if isinstance(b.get("variant"), dict) else []]
                if len(pts) >= 2 and pts[-1][1] == 0.0 and pts[-2][0] == pts[-1][0]
                and 0.15 <= x["proud_m"] <= pts[-2][1] - 0.15]
        if not any(abs(r - x["s_m"]) < 1e-6 for r in rets):
            raise ParamError(f"rainwater.front_pipes {x}: no street projection's square high-s return stands at "
                             f"s {x['s_m']} deep enough for a pipe {x['proud_m']} m before the front")
    names = sorted(CONSUMED)
    # T-2781: a side wall's stone belt (1637's south flank, the Grosvenor photograph's pale band
    # along its foot). Never on a wall that carries K03's brick course, which is the same line
    side_belts = []
    for j, sb in enumerate(val("side_belts") or ()):
        walls_ = {"k01.wall.side.south": bool(val("side_bays")), "k01.wall.side.north": bool(val("north_bays"))}
        if set(sb) != {"wall", "from_m", "to_m", "proud_m"} or sb["wall"] not in walls_:
            raise ParamError(f"side_belts[{j}] takes wall (a side wall), from_m, to_m and proud_m, not {sb}")
        if walls_[sb["wall"]] or (stone or {}).get("all_round"):
            raise ParamError(f"side_belts[{j}]: {sb['wall']} carries K03's string course or the front's "
                             f"belts already")
        y0, y1, d = float(sb["from_m"]), float(sb["to_m"]), float(sb["proud_m"])
        if not (0.3 <= y0 and 0.08 <= y1 - y0 <= 0.4 and y1 <= pf + sum(heights) - 0.5 and 0.01 <= d <= 0.08):
            raise ParamError(f"side_belts[{j}] runs {y0}-{y1} m, {d} m proud: a course 0.08-0.4 m deep "
                             f"from 0.3 m up, under the wall head, 0.01-0.08 m proud")
        for o in openings:
            if o.wall == sb["wall"] and o.sill_m < y1 and y0 < o.head_m:
                raise ParamError(f"side_belts[{j}] runs through {o.component} at s {o.s_m} on {o.wall}")
        side_belts.append({"wall": sb["wall"], "from_m": y0, "to_m": y1, "proud_m": d})
    side_base = []
    for j, sb in enumerate(val("side_base") or ()):
        if set(sb) != {"wall", "to_m", "proud_m"} or sb["wall"] not in ("k01.wall.side.north", "k01.wall.side.south"):
            raise ParamError(f"side_base[{j}] takes wall (a side wall), to_m and proud_m, not {sb}")
        if not stone or "brick_above_m" not in stone:
            raise ParamError(f"side_base[{j}] carries a stone basement's facing round its side; this front has none")
        y1, d = float(sb["to_m"]), float(sb["proud_m"])
        if not (abs(y1 - stone["brick_above_m"]) < 1e-6 and 0.01 <= d <= 0.06):
            raise ParamError(f"side_base[{j}] runs to the front's stone top ({stone['brick_above_m']} m), "
                             f"0.01-0.06 m proud, not {y1} m and {d} m")
        for o in openings:   # a light in the basement is framed by it (1834's round-headed one)
            if o.wall == sb["wall"] and o.sill_m < y1 and (o.head_m > y1 - 0.15 or o.sill_m < 0.15):
                raise ParamError(f"side_base[{j}]: {o.component} at s {o.s_m} on {o.wall} stands across "
                                 f"its top or its foot")
        side_base.append({"wall": sb["wall"], "to_m": y1, "proud_m": d})
    street_iron = _street_iron(val("street_front_iron") or {}, openings, val("entrance_kit") or {})
    shutters = _window_shutters(val("window_shutters") or {}, openings,
                                [round(pf + sum(heights[:k]), 4) for k in range(len(heights))], depth, width)
    params = K01FrontageParams(
        depth_m=depth, width_m=width, stories=stories, principal_floor_m=pf,
        storey_heights_m=heights, front_thickness_m=ft, side_thickness_m=st,
        roof_pitch_deg=pitch, eave_overhang_m=float(val("eave_overhang_m")),
        riser_m=round(riser, 5), tread_m=tread, risers=risers,
        landing_depth_m=float(val("stair_landing_depth_m")),
        stoop_width_m=float(val("stoop_width_m")), entrance_bay=entrance,
        front_bays=front_bays,
        side_bays=tuple(float(s["s_m"] if isinstance(s, dict) else s) for s in val("side_bays")),
        rear_bays=tuple(float(s) for s in val("rear_bays")),
        north_bays=tuple(float(s["s_m"] if isinstance(s, dict) else s) for s in val("north_bays") or ()),
        side_belts=tuple(side_belts), side_base=tuple(side_base), street_iron=street_iron,
        basement_sill_m=bsill, openings=tuple(openings), service_wall_brick=panel,
        roof=k04, dormer=dormer, slope_dormers=slope_dormers, rainwater=rainwater, chimneys=tuple(chimneys),
        window_kit={k: kit[k] for k in sorted(kit)}, entrance_kit=door_kit, bays=bays,
        street_front_trim=trim,
        wall_head=dict(val("wall_head", {}) or {}),
        boundary=dict(val("boundary", {}) or {}),
        yard=yard, stone_finish=stone_finish,
        stone=stone, rear_wings=wings, condition=condition, arched_front=arched,
        roof_form=roof_form, flat=flat_roof, mansard=mansard_roof, gable=gable_roof, shaped_gable=shaped, entrance_floor_m=ef, round_heads=rh,
        wall_paint=paint, wall_paint_opaque=paint_opaque, front_brick_tone=front_tone, street_dress=street_dress, frontispiece=frontispiece, rear_section=rear_section,
        round_corner=round_corner, cant_corner=cant_corner, front_pier=front_pier, pavilions=pavilions, porte_cochere=porte_cochere,
        shutters=shutters,
        confidence={n: form[n].get("confidence", "reconstructed") for n in names if n in form}
                   | {"footprint": (phase.get("footprint") or {}).get("confidence", "reconstructed")},
    )
    return params
