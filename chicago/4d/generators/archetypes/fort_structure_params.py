"""Parameters for the fort_structure archetype — pure Python, NO bpy import.

Same split, and for the same reason, as frame_tavern_params: tools/check.sh imports
this module on every commit to prove that every scene-included record still resolves
into buildable parameters, and it has to do that in a bare Python 3.11 with no
Blender in the sandbox.

## What this archetype has to cover

The buildings and the furniture INSIDE and BESIDE a garrison post — the things that
are not dwellings, not taverns and not boundaries. Fort Dearborn's own inventory is
the specification, and it is unusually well described for 1835 Chicago because two
witnesses walked round the inside of it and wrote down what stood where:

- Gurdon S. Hubbard, of the fort in 1827 (Andreas I, p. 264): "the brick building,
  just within the north stockade previously occupied by the commanding officers. The
  old officers' quarters built of logs on the west, and within the pickets ... a
  number of voyageurs with their families were living in the soldiers' quarters, on
  the east side of the inclosure. The store-house and guard-house were on either side
  of the southern gate; the sutler's store was east of the north gate, and north of
  the soldiers' barracks; the block-house was located at the southwest and the bastion
  at the northwest corners of the fort, and the magazine, of brick, was situated about
  half way between the west end of the guard and block-houses."
- The key to Alexander Hesler's 1855 photograph, in Wentworth's 1881 address: the
  commandant's quarters "brick, about 25x50 ft.", the officers' quarters "wood, about
  30x60 ft."

So the archetype's `kind` is not decoration: quarters, barracks, blockhouse, magazine,
store, guard, sutler and artillery house are the words the sources use, and each one
selects a different set of decisions the archetype is allowed to make on its own.
`parade`, `root_house`, `tower` and `flagstaff` extend the same machinery to the
fort's ground furniture, to the garrison staff, and to the 1832 lighthouse, which is
a government structure on the same reservation and has no other archetype it could
belong to.

## What it deliberately does not cover

The picket line, its gates and its bastions are the `palisade` archetype's, because
a boundary is a different kind of object from a building. A blockhouse is here and
not there: it has storeys, a roof and a floor.

Interiors are out of scope everywhere in this project, so an opening is a surface
and not a hole. A loophole is a slit in a wall, which at this level of detail is the
same thing.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md. Duplicated from the other params modules rather than
# imported so that neither can break the other's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

KINDS = ("quarters", "barracks", "blockhouse", "magazine", "store", "guard",
         "sutler", "artillery", "parade", "root_house", "tower", "flagstaff")
ROOF_TYPES = ("gable", "hip", "pyramid", "shed", "flat", "none")
CONSTRUCTIONS = ("log", "hewn_log", "braced_frame", "brick", "stone", "earth")
PAINTS = ("unpainted", "whitewash", "white", "brick", "earth", "stone")
LANTERN_PROFILES = ("legacy", "birdcage_dome")

# The form attributes whose VALUE this archetype reads. See the same set in
# frame_tavern_params for the argument; the short version is that an attribute
# outside it cannot move a vertex, so the record states something the mesh does
# not contain and tools/validate.py makes the record say which.
CONSUMED = frozenset({
    "kind", "stories", "wall_height_m", "roof_type", "roof_pitch_deg",
    "construction", "paint", "chimneys", "gallery", "loopholes", "sun_dial",
    "upper_overhang_m", "lantern", "gallery_storeys", "face_openings",
    "lantern_profile", "tower_diameter_m", "tower_openings", "tower_profile",
    "tower_lantern_detail", "tower_masonry",
})

# Where this archetype touches the ground: the whole footprint outline, at the
# base of the walls, which is what "y = 0 at the base of the walls" means in
# docs/GLB-CONTRACT.md.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class FortStructureParams:
    """One building, or one piece of ground furniture, of a garrison post.

    Dimensions are metres. `width_m` runs along the facade and `depth_m` back from
    it, both derived from the footprint polygon's bounding box — the polygon is
    authoritative and these two numbers are read off it.
    """

    width_m: float
    depth_m: float
    kind: str = "quarters"

    stories: int = 1
    wall_height_m: float = 2.8
    roof_type: str = "gable"
    roof_pitch_deg: float = 34.0
    construction: str = "log"
    paint: str = "unpainted"

    # How many stacks stand on the building. The count comes from the record where
    # a record has one; where they stand is the archetype's, exactly as it is for
    # the dwellings — see docs/LIBERTIES.md.
    chimneys: int = 0

    # A covered gallery along the facade. Whistler's 1808 index says the first
    # fort's barracks had "Galliaries fronting the parade"; nothing says the 1816
    # fort's did, so this is off unless a record turns it on.
    gallery: bool = False

    # Slits for small arms. Only ever true on a blockhouse, and only when a record
    # says so: a loopholed barracks would be a claim about how the post was meant
    # to be fought, which no source here makes.
    loopholes: bool = False

    # The jetty of a blockhouse's upper storey over its lower. Nothing at Fort
    # Dearborn attests it; it is what a blockhouse of this period IS, and the
    # record carries the admission.
    upper_overhang_m: float = 0.45

    # parade furniture
    sun_dial: bool = False

    # a lighthouse lantern on a tower
    lantern: bool = False

    # per-attribute confidence, keyed by the attribute name in the record
    # Opt-in first-fort details; preserve every legacy positional argument.
    gallery_storeys: int = field(default=1, kw_only=True)
    face_openings: list | None = field(default=None, kw_only=True)

    # Lighthouse-only opt-ins. Keep all existing positional and gallery controls.
    lantern_profile: str = field(default="legacy", kw_only=True)
    tower_diameter_m: float | None = field(default=None, kw_only=True)
    footprint_min_u_m: float = field(default=0.0, kw_only=True)
    footprint_min_v_m: float = field(default=0.0, kw_only=True)
    tower_openings: list | None = field(default=None, kw_only=True)
    tower_profile: dict | None = field(default=None, kw_only=True)
    tower_lantern_detail: dict | None = field(default=None, kw_only=True)
    tower_masonry: dict | None = field(default=None, kw_only=True)

    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the contract's rule for geometry driven by
        several attributes. A wall whose height is a guess is a guessed wall,
        even if we know what it was made of."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def is_ground(self) -> bool:
        """True for the kinds that are a surface rather than a building."""
        return self.kind in ("parade", "root_house")

    @property
    def storey_height_m(self) -> float:
        return self.wall_height_m / max(self.stories, 1)

    @property
    def overhang_m(self) -> float:
        """The jetty actually built. Only a two-storey blockhouse gets one."""
        if self.kind == "blockhouse" and self.stories >= 2:
            return self.upper_overhang_m
        return 0.0

    @property
    def taper(self) -> float:
        """A tower's top radius as a fraction of its base radius.

        Fixed here rather than recorded because no source states the 1832
        lighthouse's shape at all — see docs/RESEARCH/chicago_lighthouse_1832.md.
        0.62 is what a forty-foot rubble tower of the period looks like, and the
        record carries the admission that the whole profile is ours.
        """
        return 0.62

    @property
    def mast_butt_m(self) -> float:
        """A flagstaff's diameter at the butt, as a fraction of its footprint.

        Fixed here rather than recorded because NO SOURCE REACHED gives the
        second fort's staff a thickness — Andreas gives it a height and nothing
        else. 0.60 of a half-metre square of ground is a 0.30 m butt, which is
        what a fifty-foot spar has to be to stand; the record carries the
        admission and docs/LIBERTIES.md owns it.
        """
        return self.width_m * 0.60

    @property
    def mast_truck_m(self) -> float:
        """And its diameter at the truck: a spar tapers, and this one is ours."""
        return self.mast_butt_m * 0.45

    @property
    def tower_shaft_height_m(self) -> float:
        return (self.wall_height_m*.86 if self.tower_profile is None
                else self.tower_profile["gallery_underside_m"])

    def validate(self) -> None:
        if self.tower_profile is not None:
            if self.kind != "tower" or not self.lantern or self.lantern_profile != "birdcage_dome":
                raise ParamError("tower_profile requires a lit birdcage_dome tower")
            profile = self.tower_profile
            if not isinstance(profile, dict) or set(profile) != {
                    "gallery_underside_m", "cap_base_m", "gallery_rail_height_m"}:
                raise ParamError("tower_profile needs gallery_underside_m/cap_base_m/gallery_rail_height_m")
            if any(isinstance(v, bool) or not isinstance(v, (float, int))
                   or not math.isfinite(v) for v in profile.values()):
                raise ParamError("tower_profile dimensions must be finite numbers")
            radius = (self.tower_diameter_m if self.tower_diameter_m is not None else self.width_m)/2
            maximum = self.wall_height_m+radius*self.taper*.7
            floor, cap, rail = (profile["gallery_underside_m"],profile["cap_base_m"],
                                profile["gallery_rail_height_m"])
            if not (1 <= floor < cap-.6 and .3 <= rail <= 1.4
                    and floor+.09+rail < cap and cap < maximum-.1):
                raise ParamError("tower_profile gallery/rail/cap do not fit the unchanged overall max")
        if self.tower_masonry is not None:
            if self.kind != "tower" or self.construction != "stone":
                raise ParamError("tower_masonry requires a stone tower")
            d=self.tower_masonry
            keys={"course_m","bond_m","joint_m","relief_m","reveal_m","seed"}
            if not isinstance(d,dict) or set(d)-{'character'}!=keys or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for k,v in d.items() if k!='character'):
                raise ParamError("tower_masonry needs six finite declared controls")
            if d.get('character','legacy_courses') not in {'legacy_courses','irregular_rubble'}:
                raise ParamError("tower_masonry needs six finite declared controls")
            if not (.2<=d['course_m']<=.6 and .3<=d['bond_m']<=1.2 and .01<=d['joint_m']<=.05
                    and .002<=d['relief_m']<=.025 and d['relief_m']<d['reveal_m']<=.12
                    and isinstance(d['seed'],int) and 0<=d['seed']<=100000):
                raise ParamError("tower_masonry controls out of reconstructed bounds")
        if self.tower_lantern_detail is not None:
            if (self.kind != "tower" or not self.lantern or
                    self.lantern_profile != "birdcage_dome" or self.tower_profile is None):
                raise ParamError("tower_lantern_detail requires a partitioned birdcage tower")
            d = self.tower_lantern_detail
            keys = {"pane_opacity", "sill_height_m", "dome_rise_m", "cage_uprights",
                    "cage_member_m", "gallery_posts", "gallery_member_m", "finial_radius_m"}
            if not isinstance(d, dict) or set(d) != keys:
                raise ParamError("tower_lantern_detail needs the eight declared detail controls")
            if any(isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
                   for v in d.values()):
                raise ParamError("tower_lantern_detail controls must be finite numbers")
            if any(not isinstance(d[k], int) or not 6 <= d[k] <= 32
                   for k in ("cage_uprights", "gallery_posts")):
                raise ParamError("lantern member counts must be integers in6..32")
            if not (.02 <= d["pane_opacity"] <= .65 and .04 <= d["sill_height_m"] <= .4
                    and .02 <= d["cage_member_m"] <= .1 and .02 <= d["gallery_member_m"] <= .1
                    and .01 <= d["finial_radius_m"] <= .04):
                raise ParamError("lantern detail controls out of reconstructed bounds")
            r1 = (self.tower_diameter_m if self.tower_diameter_m is not None else self.width_m)/2*self.taper
            cap_total = self.wall_height_m+r1*.7-self.tower_profile["cap_base_m"]
            if not (.3 <= d["dome_rise_m"] < cap_total-.2):
                raise ParamError("dome must leave at least0.2m finial within unchanged maximum")
        if self.tower_openings is not None:
            if self.kind != "tower":
                raise ParamError("tower_openings needs kind tower")
            if not isinstance(self.tower_openings, list) or len(self.tower_openings) > 24:
                raise ParamError("tower_openings must be a list of at most 24 windows")
            radius = (self.tower_diameter_m if self.tower_diameter_m is not None else self.width_m) / 2
            for o in self.tower_openings:
                if not isinstance(o, dict) or set(o)-{"offset_m"} != {"facet", "width_m", "z0_fraction", "z1_fraction"}:
                    raise ParamError("tower aperture needs facet/width_m/z0_fraction/z1_fraction")
                if isinstance(o["facet"], bool) or not isinstance(o["facet"], int) or not 0 <= o["facet"] < 12:
                    raise ParamError("tower aperture facet must be an integer 0..11")
                if any(isinstance(o[k], bool) or not isinstance(o[k], (int, float)) or not math.isfinite(o[k])
                       for k in ("width_m", "z0_fraction", "z1_fraction")) or ("offset_m" in o and (isinstance(o["offset_m"],bool) or not isinstance(o["offset_m"],(float,int)) or not math.isfinite(o["offset_m"]))):
                    raise ParamError("tower aperture dimensions must be finite numbers")
                if not .05 <= o["z0_fraction"] < o["z1_fraction"] <= .97 or o["width_m"] < .12:
                    raise ParamError("tower aperture fractions/width outside supported range")
                # Existing window sill horns/casings extend 0.12 m on each side.
                # Keep every emitted piece on its chosen tapered shaft facet.
                shaft = self.tower_shaft_height_m
                if ((o["z1_fraction"]-o["z0_fraction"])*shaft < .30
                        or o["z1_fraction"]*shaft+.15 >= shaft):
                    raise ParamError("tower aperture height/trim do not fit the shaft")
                top_radius = radius * (1-(1-self.taper)*(o["z1_fraction"]+.15/shaft))
                padding = .025 if self.tower_masonry is not None else .12
                if o["width_m"]+2*padding+2*abs(o.get("offset_m",0)) > 2*top_radius*math.sin(math.pi/12):
                    raise ParamError("tower aperture and trim exceed shaft facet")
            for i, a in enumerate(self.tower_openings):
                for b in self.tower_openings[i+1:]:
                    if a["facet"] == b["facet"] and not (
                            a["z1_fraction"]+.03 <= b["z0_fraction"] or
                            b["z1_fraction"]+.03 <= a["z0_fraction"]):
                        raise ParamError("tower apertures overlap on one facet")
        offsets = (self.footprint_min_u_m, self.footprint_min_v_m)
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
               not math.isfinite(v) for v in offsets):
            raise ParamError("footprint offsets must be finite numbers")
        if self.tower_diameter_m is not None:
            diameter = self.tower_diameter_m
            if (isinstance(diameter, bool) or not isinstance(diameter, (int, float))
                    or not math.isfinite(diameter) or diameter <= 0):
                raise ParamError("tower_diameter_m must be a positive finite number")
            if self.kind != "tower":
                raise ParamError("tower_diameter_m is only valid on a tower")
            if (abs(diameter - self.width_m) > 1e-6 or
                    abs(diameter - self.depth_m) > 1e-6):
                raise ParamError("tower_diameter_m must match both physical footprint spans")
        elif any(abs(v) > 1e-6 for v in offsets):
            raise ParamError("offset polygon bounds require explicit tower_diameter_m")
        if self.lantern_profile not in LANTERN_PROFILES:
            raise ParamError(
                f"lantern_profile {self.lantern_profile!r} not in {LANTERN_PROFILES}")
        if self.lantern_profile != "legacy" and (
                self.kind != "tower" or not self.lantern):
            raise ParamError("lantern_profile needs kind tower and lantern true")
        if self.face_openings is not None:
            if self.kind not in ("quarters", "barracks") or self.overhang_m:
                raise ParamError("face_openings currently supports unjettied quarters/barracks")
            if not isinstance(self.face_openings, list) or len(self.face_openings) > 128:
                raise ParamError("face_openings must be a list of at most 128 rectangles")
            for o in self.face_openings:
                if not isinstance(o, dict) or set(o) != {"face", "kind", "u0", "u1", "z0", "z1"}:
                    raise ParamError("each face_openings rectangle needs face/kind/u0/u1/z0/z1")
                if o["face"] not in ("front", "back", "left", "right"):
                    raise ParamError("face_openings face must be front/back/left/right")
                if o["kind"] not in ("window", "door"):
                    raise ParamError("face_openings kind must be window/door")
                if any(isinstance(o[k], bool) or not isinstance(o[k], (int, float))
                       or not math.isfinite(o[k]) for k in ("u0", "u1", "z0", "z1")):
                    raise ParamError("face_openings dimensions must be finite numbers")
                span = self.width_m if o["face"] in ("front", "back") else self.depth_m
                if not (0 <= o["u0"] < o["u1"] <= span
                        and 0 <= o["z0"] < o["z1"] <= self.wall_height_m):
                    raise ParamError("face_openings rectangle must lie within its wall")
            for i, a in enumerate(self.face_openings):
                for b in self.face_openings[i+1:]:
                    if a["face"] != b["face"] or a["z0"] >= b["z1"] or b["z0"] >= a["z1"]:
                        continue
                    if max(b["u0"]-a["u1"], a["u0"]-b["u1"]) < 0.15-1e-9:
                        raise ParamError("face_openings must leave at least 0.15 m between openings")
        if (not isinstance(self.gallery_storeys, int) or isinstance(self.gallery_storeys, bool)
                or self.gallery_storeys not in (1, 2)):
            raise ParamError("gallery_storeys must be the whole number 1 or 2")
        if self.gallery_storeys == 2:
            if not self.gallery or self.kind not in ("quarters", "barracks"):
                raise ParamError("a double gallery requires gallery=true on quarters or barracks")
            if self.stories != 2:
                raise ParamError("a double gallery requires a two-storey range")
        if self.kind not in KINDS:
            raise ParamError(f"kind '{self.kind}' not in {KINDS}")
        if not 0.5 <= self.width_m <= 120.0:
            raise ParamError(f"width_m {self.width_m} outside 0.5-120 m")
        if not 0.5 <= self.depth_m <= 120.0:
            raise ParamError(f"depth_m {self.depth_m} outside 0.5-120 m")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(f"construction '{self.construction}' not in {CONSTRUCTIONS}")
        if self.paint not in PAINTS:
            raise ParamError(f"paint '{self.paint}' not in {PAINTS}")
        if self.roof_type not in ROOF_TYPES:
            raise ParamError(f"roof_type '{self.roof_type}' not in {ROOF_TYPES}")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")
        if not isinstance(self.chimneys, int) or isinstance(self.chimneys, bool):
            raise ParamError(f"chimneys {self.chimneys!r} is not a whole number — a record "
                             f"states a count, not whether there was one")
        if not 0 <= self.chimneys <= 6:
            raise ParamError(f"chimneys {self.chimneys} outside 0..6")

        if self.kind == "parade":
            if self.roof_type != "none":
                raise ParamError("a parade ground has no roof; set roof_type to 'none'")
            if self.chimneys:
                raise ParamError("a parade ground has no chimney")
            return
        if self.kind == "root_house":
            if not 0.8 <= self.wall_height_m <= 3.0:
                raise ParamError(f"wall_height_m {self.wall_height_m} outside 0.8-3 m for a "
                                 f"root house — it is a banked cellar, not a shed")
            return
        if self.kind == "tower":
            if not 4.0 <= self.wall_height_m <= 40.0:
                raise ParamError(f"wall_height_m {self.wall_height_m} outside 4-40 m for a "
                                 f"tower")
            if abs(self.width_m - self.depth_m) > 0.51:
                raise ParamError(f"a round tower's footprint must be square in plan; "
                                 f"{self.width_m} x {self.depth_m} is not")
            return
        if self.kind == "flagstaff":
            # Andreas puts the staff at "some fifty feet high" — 15.24 m. The band is
            # wide enough to hold any garrison staff anyone might later attest and
            # narrow enough that a typo cannot stand a mast over the town.
            if not 6.0 <= self.wall_height_m <= 25.0:
                raise ParamError(f"wall_height_m {self.wall_height_m} outside 6-25 m for a "
                                 f"flagstaff")
            if abs(self.width_m - self.depth_m) > 0.26:
                raise ParamError(f"a flagstaff's footprint is the square of ground it "
                                 f"stands on and must be square in plan; "
                                 f"{self.width_m} x {self.depth_m} is not")
            if self.chimneys:
                raise ParamError("a flagstaff has no chimney")
            return

        if self.stories not in (1, 2, 3):
            raise ParamError(f"stories {self.stories} not in 1..3 — nothing at this post "
                             f"stood higher")
        if not 1.8 <= self.wall_height_m <= 12.0:
            raise ParamError(f"wall_height_m {self.wall_height_m} outside 1.8-12 m")
        if self.stories == 1 and self.wall_height_m > 4.2:
            raise ParamError(f"wall_height_m {self.wall_height_m} is two storeys' worth of "
                             f"wall on a one-storey record; set stories or the height")
        if self.roof_type not in ("flat", "none") and not 8.0 <= self.roof_pitch_deg <= 60.0:
            raise ParamError(f"roof_pitch_deg {self.roof_pitch_deg} outside 8-60 deg")
        if self.loopholes and self.kind != "blockhouse":
            raise ParamError(f"loopholes on a '{self.kind}' would be a claim about how this "
                             f"post was meant to be fought; no source here makes it")
        if self.kind == "blockhouse":
            if not 0.0 <= self.upper_overhang_m <= 1.2:
                raise ParamError(f"upper_overhang_m {self.upper_overhang_m} outside 0-1.2 m")
            if self.overhang_m > min(self.width_m, self.depth_m) / 4.0:
                raise ParamError(f"a {self.upper_overhang_m} m jetty on a {self.width_m} x "
                                 f"{self.depth_m} blockhouse overhangs a quarter of its plan")
        if self.gallery and self.depth_m < 3.0:
            raise ParamError(f"a gallery in front of a {self.depth_m} m deep building leaves "
                             f"no building behind it")


def from_phase(phase: dict, record: dict | None = None) -> FortStructureParams:
    """Resolve one structure phase into generator parameters.

    Reads only the attested `value` of each form attribute plus its confidence.
    Footprint dimensions come from the phase footprint polygon's bounding box —
    the polygon is authoritative, width and depth are derived.
    """
    form = phase.get("form", {})

    def val(attr, default=None):
        a = form.get(attr)
        return default if a is None else a.get("value", default)

    def conf(attr, default="reconstructed"):
        a = form.get(attr)
        return default if a is None else a.get("confidence", default)

    poly = phase.get("footprint", {}).get("polygon") or []
    if len(poly) < 3:
        raise ParamError("footprint polygon needs at least 3 points")
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    width, depth = max(xs) - min(xs), max(ys) - min(ys)

    # GLB-CONTRACT pins the coordinate origin, not necessarily the bbox corner.
    # Existing builders assume min=0; only an explicitly dimensioned tower
    # resolves polygon offsets and actually uses them to preserve its centre.
    min_u, min_v = min(xs), min(ys)
    diameter = val("tower_diameter_m", None)
    if (abs(min_u) > 1e-6 or abs(min_v) > 1e-6) and not (
            str(val("kind", "quarters")) == "tower" and diameter is not None):
        raise ParamError(
            f"footprint polygon starts at ({min_u}, {min_v}), not the origin. "
            f"Only an explicit tower_diameter_m resolves this offset; other "
            f"builders require a zero-min polygon.")

    confidences = {a: conf(a) for a in form}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")

    kind = str(val("kind", "quarters"))
    stories = int(val("stories", 2 if kind == "blockhouse" else 1))

    p = FortStructureParams(
        width_m=round(width, 3),
        depth_m=round(depth, 3),
        kind=kind,
        stories=stories,
        wall_height_m=float(val("wall_height_m", 5.0 if stories == 2 else 2.8)),
        roof_type=str(val("roof_type", "gable")),
        roof_pitch_deg=float(val("roof_pitch_deg", 34.0)),
        construction=str(val("construction", "log")),
        paint=str(val("paint", "unpainted")),
        chimneys=int(val("chimneys", 0)),
        gallery=bool(val("gallery", False)),
        gallery_storeys=val("gallery_storeys", 1),
        face_openings=val("face_openings", None),
        loopholes=bool(val("loopholes", False)),
        upper_overhang_m=float(val("upper_overhang_m", 0.45)),
        sun_dial=bool(val("sun_dial", False)),
        lantern=bool(val("lantern", False)),
        lantern_profile=str(val("lantern_profile", "legacy")),
        tower_diameter_m=diameter,
        footprint_min_u_m=min_u,
        footprint_min_v_m=min_v,
        tower_openings=val("tower_openings", None),
        tower_profile=val("tower_profile", None),
        tower_lantern_detail=val("tower_lantern_detail", None),
        tower_masonry=val("tower_masonry", None),
        confidence=confidences,
    )
    p.validate()
    return p


def wall_openings(p: FortStructureParams, face: str) -> list[dict] | None:
    """The explicit rectangles on one wall; None means this wall is unread.

    Both mesh and front-wall reader consume this exact layout. Legacy procedural
    layouts remain unread here rather than being falsely declared empty.
    """
    if p.face_openings is None:
        return None
    return [{k: o[k] for k in ("kind", "u0", "u1", "z0", "z1")}
            for o in p.face_openings if o["face"] == face]


def front_wall(p: FortStructureParams) -> dict | None:
    openings = wall_openings(p, "front")
    if openings is None:
        return None
    return {"u0": 0.0, "u1": p.width_m, "wall_height_m": p.wall_height_m,
            "openings": openings}


def tower_opening_layout(p: FortStructureParams) -> list[dict] | None:
    """The actual tower aperture rectangles, distinct from a flat front wall.

    Existing shaft height is0.86*wall_height_m. Fractions preserve source order
    and move with a future explicitly reconstructed shaft/lantern division.
    """
    if p.tower_openings is None:
        return None
    shaft = p.tower_shaft_height_m
    return [{"facet": o["facet"], "azimuth_deg": 15+30*o["facet"],
             "u0": o.get("offset_m",0)-o["width_m"]/2, "u1": o.get("offset_m",0)+o["width_m"]/2,
             "z0": shaft*o["z0_fraction"], "z1": shaft*o["z1_fraction"],
             "kind": "window"} for o in p.tower_openings]
