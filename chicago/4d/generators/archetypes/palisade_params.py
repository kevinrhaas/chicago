"""Parameters for the palisade archetype — pure Python, NO bpy import.

Same split, and for the same reason, as frame_tavern_params: tools/check.sh imports
this module on every commit to prove that every scene-included record still resolves
into buildable parameters, and it has to do that in a bare Python 3.11 with no
Blender in the sandbox.

## What this archetype has to cover

An enclosure made of posts standing in the ground — the class of thing that is a
BOUNDARY rather than a building, and which nothing else in this project builds.
Two members of it are in the 1835 dataset:

- **Fort Dearborn's stockade.** Juliette Kinzie, standing inside it in 1831: "The
  fort was inclosed by high pickets, with bastions at the alternate angles. Large
  gates opened to the north and south, and there were small posterns here and there
  for the accommodation of the inmates." Andreas adds that the rebuilt fort "consisted
  of a square stockade" with "two gates, one on the north and the other on the south
  side". The 1830 Harrison plan draws that square with a work at three of its four
  angles. So: a picket line on a rectangle, with named gates and named corner works.
- **The garrison garden.** The same 1830 plan draws a large diamond-shaped plot
  south-west of the fort, labelled "Garden for the Garrison", bounded on two sides by
  a drawn zigzag. A zigzag boundary is the period convention for a worm (snake) rail
  fence, so the archetype builds one — with the reading recorded on the structure and
  not asserted here.

## What it deliberately does not cover

A **blockhouse is a building, not a boundary**, and belongs to `fort_structure` even
when it stands astride the line: it has storeys, a roof and a garrison inside it. The
BASTIONS are here because a bastion of this kind is a re-entrant of the picket line
itself with nothing inside it — that is a fact about the second-system frontier
stockade and not a convenience.

Nothing here models a ditch, a berm or a banquette. None of the three are attested at
Fort Dearborn and a stockade is not automatically earthwork-and-palisade.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

# Confidence values as they are written into the _CONFIDENCE glTF attribute.
# See docs/GLB-CONTRACT.md. Duplicated from the other params modules rather than
# imported so that neither can break the other's import in the commit gate.
CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

WALL_KINDS = ("picket_stockade", "worm_fence")
CONSTRUCTIONS = ("log", "hewn_log", "split_rail")
SIDES = ("n", "s", "e", "w")
CORNERS = ("nw", "ne", "se", "sw")

# The form attributes whose VALUE this archetype reads — the ones from_phase below
# turns into a parameter, and therefore the only ones a vertex position can depend
# on. tools/validate.py holds every attribute outside this set to a `geometry:`
# declaration on the record, so adding a parameter here without adding its name is
# a gate failure rather than a silently unbuilt attribute.
CONSUMED = frozenset({
    "wall_kind", "construction", "picket_height_m", "picket_width_m",
    "picket_spacing_m", "picket_head_m", "gate_sides", "gate_width_m",
    "bastion_corners", "bastion_length_m", "bastion_projection_m",
    "rail_courses", "panel_length_m", "panel_offset_m", "fence_height_m",
})

# How short a head may get before the wall stops reading as a stockade. The same
# number, for the same reason, as `tools/measure_picket_plate.py`'s
# MIN_POINT_FRACTION, which refuses a shipped GLB whose apexes have worn below it:
# a bound the record may state and the gate would then reject is not a bound.
MIN_HEAD_FRACTION = 0.04

# And how long. Half the picket is not a sharpened head, it is a spike on a short
# post, and past that the shaft this archetype builds under it stops being the
# thing a visitor reads as a picket.
MAX_HEAD_FRACTION = 0.5

# Where this archetype touches the ground: the whole outline, at the foot of the
# posts. A picket line whose own outline does not reach the terrain is a fence
# hanging in the air, which is the one failure mode a boundary cannot survive.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


def _seq(value, vocab, name: str) -> tuple:
    """A record's list of sides or corners, normalised and checked.

    Records write these as JSON arrays of short codes. Anything outside the
    vocabulary is refused rather than dropped: a typo'd gate would otherwise
    silently produce a fort with a wall where a source says there was a gate,
    and nothing in the pipeline would ever mention it again.
    """
    if value is None:
        return ()
    if isinstance(value, str):
        value = [value]
    out = []
    for v in value:
        v = str(v).strip().lower()
        if v not in vocab:
            raise ParamError(f"{name} '{v}' is not one of {vocab}")
        if v not in out:
            out.append(v)
    return tuple(out)


@dataclass
class PalisadeParams:
    """An enclosure of posts. Dimensions are metres.

    `width_m` and `depth_m` are the enclosure, derived from the footprint polygon's
    bounding box exactly as the building archetypes derive theirs — the polygon is
    authoritative and the two numbers are read off it.
    """

    width_m: float
    depth_m: float
    wall_kind: str = "picket_stockade"
    construction: str = "log"

    # the picket line
    picket_height_m: float = 3.7
    picket_width_m: float = 0.22
    picket_spacing_m: float = 0.30

    # How much of the picket's height is the sharpened head. `None` means the
    # record does not state it and the proportion below is derived instead — see
    # `picket_point_m`, which is what the builder actually reads.
    picket_head_m: float | None = None

    # gates. Named by the side they pierce, because that is how every source
    # describes them: "large gates opened to the north and south".
    gate_sides: tuple = ()
    gate_width_m: float = 3.6

    # corner works. A bastion here is a re-entrant of the picket line: it leaves
    # the wall `bastion_length_m` from the corner on each face, projects
    # `bastion_projection_m` outward, and returns. Nothing stands inside it.
    bastion_corners: tuple = ()
    bastion_length_m: float = 7.0
    bastion_projection_m: float = 3.0

    # the worm fence, for a garden rather than a fort
    fence_height_m: float = 1.3
    rail_courses: int = 3
    panel_length_m: float = 3.0
    panel_offset_m: float = 0.9

    # per-attribute confidence, keyed by the attribute name in the record
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        """The _CONFIDENCE float for one attribute."""
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the contract's rule for geometry driven by
        several attributes."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def picket_point_m(self) -> float:
        """How much of a picket's height is the sharpened point.

        **Stated by the record when the record states it, derived when it does
        not**, and the derivation is the fallback rather than the rule because of
        what the head is: no source describes the head of a Fort Dearborn picket,
        and a flat-topped post reads as a fence rail while a pointed one reads as
        a stockade. One picket width is the proportion that a splitting axe
        produces and it is not a claim about this fort.

        It was derived-only until T-0094's second half, and that was the defect:
        an invention this conspicuous — it is the silhouette of the most
        recognisable building in the town — lived in a Python expression, where
        the confidence model cannot grade it, the popup cannot show it and
        `docs/LIBERTIES.md` could not claim it in the machine-readable field. A
        value the archetype makes up is still a value about the building, so it
        belongs on the record at the tier it earns, which is `reconstructed`.
        `fort_dearborn_palisade` now states 0.312 m — the number this expression
        already produced, to the bit — so declaring it moved no vertex.

        The fallback stays, and it is not vestigial: the garrison garden's worm
        fence resolves through this same class and states no picket anything.
        """
        if self.picket_head_m is not None:
            return float(self.picket_head_m)
        return min(self.picket_width_m * 1.3, self.picket_height_m * 0.18)

    @property
    def perimeter_m(self) -> float:
        return 2.0 * (self.width_m + self.depth_m)

    @property
    def picket_count(self) -> int:
        """Roughly how many posts the run carries. Derived because it is the
        number that decides whether this archetype is affordable, and the bake
        should be able to state it without building it first."""
        return int(math.floor(self.perimeter_m / max(self.picket_spacing_m, 1e-6)))

    def validate(self) -> None:
        if not 2.0 <= self.width_m <= 400.0:
            raise ParamError(f"width_m {self.width_m} outside 2-400 m")
        if not 2.0 <= self.depth_m <= 400.0:
            raise ParamError(f"depth_m {self.depth_m} outside 2-400 m")
        if self.wall_kind not in WALL_KINDS:
            raise ParamError(f"wall_kind '{self.wall_kind}' not in {WALL_KINDS}")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(f"construction '{self.construction}' not in {CONSTRUCTIONS}")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")
        if self.wall_kind == "picket_stockade":
            self._validate_stockade()
        else:
            self._validate_fence()

    def _validate_stockade(self) -> None:
        if not 1.5 <= self.picket_height_m <= 6.5:
            raise ParamError(f"picket_height_m {self.picket_height_m} outside 1.5-6.5 m; "
                             f"a stockade taller than that is a wall and needs a different "
                             f"kind of evidence")
        if not 0.08 <= self.picket_width_m <= 0.5:
            raise ParamError(f"picket_width_m {self.picket_width_m} outside 0.08-0.5 m")
        if self.picket_head_m is not None:
            # Bounded as a PROPORTION of the picket rather than in metres,
            # because that is what the head is: it is cut out of the height, so
            # what decides whether it reads is how much of the post it takes, not
            # how many centimetres it is. The floor is the shipped gate's own
            # (tools/measure_picket_plate.py MIN_POINT_FRACTION) so that a value
            # this module accepts is never one check.sh then refuses.
            lo = self.picket_height_m * MIN_HEAD_FRACTION
            hi = self.picket_height_m * MAX_HEAD_FRACTION
            if not lo <= self.picket_head_m <= hi:
                raise ParamError(
                    f"picket_head_m {self.picket_head_m} outside {lo:.3f}-{hi:.3f} m — "
                    f"{MIN_HEAD_FRACTION:.0%} to {MAX_HEAD_FRACTION:.0%} of the "
                    f"{self.picket_height_m} m picket. Under the floor the sawtooth "
                    f"stops reading at the wall and tools/measure_picket_plate.py "
                    f"--gate refuses the result; over the ceiling it is a spike on a "
                    f"stub, not a sharpened post")
        if self.picket_spacing_m < self.picket_width_m:
            raise ParamError(f"picket_spacing_m {self.picket_spacing_m} is closer than the "
                             f"pickets are wide ({self.picket_width_m}) — they would "
                             f"intersect each other")
        if self.picket_spacing_m > self.picket_width_m * 3.0:
            raise ParamError(f"picket_spacing_m {self.picket_spacing_m} leaves gaps wider "
                             f"than two pickets; that is a paling fence, not a stockade, "
                             f"and no source describes Fort Dearborn as one")
        for s in self.gate_sides:
            if s not in SIDES:
                raise ParamError(f"gate side '{s}' not in {SIDES}")
            run = self.width_m if s in ("n", "s") else self.depth_m
            if self.gate_width_m > run * 0.5:
                raise ParamError(f"a {self.gate_width_m} m gate takes more than half of the "
                                 f"{run} m {s} wall")
        if not 1.5 <= self.gate_width_m <= 8.0:
            raise ParamError(f"gate_width_m {self.gate_width_m} outside 1.5-8 m")
        for c in self.bastion_corners:
            if c not in CORNERS:
                raise ParamError(f"bastion corner '{c}' not in {CORNERS}")
        if self.bastion_corners:
            if not 2.0 <= self.bastion_length_m <= min(self.width_m, self.depth_m) / 2.0:
                raise ParamError(f"bastion_length_m {self.bastion_length_m} does not fit "
                                 f"between the corners of a {self.width_m} x {self.depth_m} "
                                 f"enclosure")
            if not 1.0 <= self.bastion_projection_m <= 12.0:
                raise ParamError(f"bastion_projection_m {self.bastion_projection_m} "
                                 f"outside 1-12 m")

    def _validate_fence(self) -> None:
        if self.picket_head_m is not None:
            raise ParamError(f"picket_head_m {self.picket_head_m} is stated on a worm "
                             f"fence, which has no pickets to head — a worm fence is "
                             f"stacked split rails and nothing is set in the ground. "
                             f"The value would be read by nothing and shown by the popup "
                             f"anyway, which is the state `geometry:` declarations exist "
                             f"to make impossible")
        if not 0.6 <= self.fence_height_m <= 2.5:
            raise ParamError(f"fence_height_m {self.fence_height_m} outside 0.6-2.5 m")
        if self.rail_courses not in (2, 3, 4, 5, 6, 7, 8):
            raise ParamError(f"rail_courses {self.rail_courses} outside 2..8")
        if not 1.2 <= self.panel_length_m <= 5.0:
            raise ParamError(f"panel_length_m {self.panel_length_m} outside 1.2-5 m — a worm "
                             f"fence panel is one rail long and rails were split, not sawn")
        if not 0.2 <= self.panel_offset_m <= self.panel_length_m * 0.6:
            raise ParamError(f"panel_offset_m {self.panel_offset_m} does not make a zigzag "
                             f"against a {self.panel_length_m} m panel")


def from_phase(phase: dict, record: dict | None = None) -> PalisadeParams:
    """Resolve one structure phase into generator parameters.

    Reads only the attested `value` of each form attribute plus its confidence.
    Enclosure dimensions come from the phase footprint polygon's bounding box —
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

    p = PalisadeParams(
        width_m=round(width, 3),
        depth_m=round(depth, 3),
        wall_kind=str(val("wall_kind", "picket_stockade")),
        construction=str(val("construction", "log")),
        picket_height_m=float(val("picket_height_m", 3.7)),
        picket_width_m=float(val("picket_width_m", 0.22)),
        picket_spacing_m=float(val("picket_spacing_m", 0.30)),
        # No default number, deliberately: absence means "the record does not
        # state the head", which `picket_point_m` answers by deriving one. A
        # default here would put a second, silent number in the same place.
        picket_head_m=(None if val("picket_head_m") is None
                       else float(val("picket_head_m"))),
        gate_sides=_seq(val("gate_sides"), SIDES, "gate side"),
        gate_width_m=float(val("gate_width_m", 3.6)),
        bastion_corners=_seq(val("bastion_corners"), CORNERS, "bastion corner"),
        bastion_length_m=float(val("bastion_length_m", 7.0)),
        bastion_projection_m=float(val("bastion_projection_m", 3.0)),
        fence_height_m=float(val("fence_height_m", 1.3)),
        rail_courses=int(val("rail_courses", 3)),
        panel_length_m=float(val("panel_length_m", 3.0)),
        panel_offset_m=float(val("panel_offset_m", 0.9)),
        confidence=confidences,
    )
    p.validate()
    return p
