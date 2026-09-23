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

# The form attributes whose VALUE this archetype reads. See the same set in
# frame_tavern_params for the argument; the short version is that an attribute
# outside it cannot move a vertex, so the record states something the mesh does
# not contain and tools/validate.py makes the record say which.
CONSUMED = frozenset({
    "kind", "stories", "wall_height_m", "roof_type", "roof_pitch_deg",
    "construction", "paint", "chimneys", "gallery", "loopholes", "sun_dial",
    "upper_overhang_m", "lantern",
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

    def validate(self) -> None:
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

    # The contract pins the mesh origin to polygon coordinate (0, 0); see the same
    # refusal in frame_tavern_params for the argument.
    if abs(min(xs)) > 1e-6 or abs(min(ys)) > 1e-6:
        raise ParamError(
            f"footprint polygon starts at ({min(xs)}, {min(ys)}), not the origin. "
            f"docs/GLB-CONTRACT.md pins the mesh origin to polygon coordinate (0, 0); "
            f"re-anchor the polygon and put the offset in position.")

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
        loopholes=bool(val("loopholes", False)),
        upper_overhang_m=float(val("upper_overhang_m", 0.45)),
        sun_dial=bool(val("sun_dial", False)),
        lantern=bool(val("lantern", False)),
        confidence=confidences,
    )
    p.validate()
    return p
