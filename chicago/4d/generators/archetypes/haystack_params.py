"""Parameters for the haystack archetype — pure Python, NO bpy import.

Same split, same reason, as `camp_params`: `tools/check.sh` imports this on every
commit and must not need Blender.

## What a haystack is here, and why it is not a building

Wau-Bun, ch. XVIII, of Lee's Place on the South Branch in April 1812: the discharged
soldier "pointed to the cattle which were standing among the haystacks on the opposite
bank", crossed, "pulled some hay for the cattle", and he and the boy "made a circuit, so
that their movements were concealed by the haystacks" (kinzie_waubun_1856). That is the
first stack yard this project builds (T-2510), and it says what the stacks were: hay
stacked in the open where the stock was fed, big enough to hide a man walking round
them, with the cattle loose among them. So a stack is not one of the roofs, it has no
door and no wall, and it answers no household.

## What it builds

One stack per record: a round stack drawn in to a peak, the kind pitched by hand round a
stack pole in a meadow, which is the only kind a farm worked from a frontier post had the
hands for. From the ground up:

- the **bottom**, narrower than the stack, because a stack is built out as it rises so
  the rain runs off its belly and drips clear of its foot;
- the **body**, its widest girth a little above half its height;
- the **top**, drawn in from the shoulder to the peak and raked down to shed the rain,
  which is the part that weathers first and is drawn a shade darker for it;
- the **stack pole** standing a little clear of the peak.

`condition` is the hay's age: `new` is this season's cut, still pale and gold-green;
`weathered` is a stack that has stood through a winter, greyed and settled, and a stack
cattle have been fed from is lower than it was pitched (`height_m` says by how much).

**No figure is drawn, and no animal** (docs/LIBERTIES.md L1 binds figures; the cattle
Wau-Bun puts among the stacks are not built either, and the record says so).

## Local origin and frame

The footprint is the square the stack stands in: (0, 0) is its corner, as
docs/GLB-CONTRACT.md requires, and the stack is centred in it. z = 0 is the ground at the
origin. A round stack has no front; `rotation_deg` only turns the pole's lean and the
small irregularities of the girth.

## Every dimension here is the archetype's, and owes the liberties document an entry

No source sizes a stack at Chicago. The defaults below are a hand-pitched round stack of
two to three tons, and each record that uses them says so and carries the liberty.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

CONDITIONS = ("new", "weathered")

# A round stack of about twelve feet across and fourteen to the peak. Its volume, about
# 30 cubic metres, is two to three tons of loose hay settled in the stack: what two or
# three men pitch in a day off a meadow, and the scale a single farm stacks at.
DEFAULT_DIAMETER_M = 3.7
DEFAULT_HEIGHT_M = 4.3
# The shoulder, where the top is begun, as a fraction of the height to the peak.
SHOULDER_FRACTION = 0.56
# The bottom's girth as a fraction of the widest: a stack is built out as it rises.
FOOT_FRACTION = 0.86
# How far the stack pole stands clear of the peak, and how thick it is.
POLE_ABOVE_M = 0.45
POLE_SIDE_M = 0.09
# Room between the stack's widest girth and the square it stands in.
MARGIN_M = 0.15

VERTICAL_ANCHOR = "ground"
# A stack stands on the ground over its whole foot: the gate asks the terrain under the
# square's perimeter to lie within the walker's tolerance of the ground at the origin,
# which is the claim that the stack was pitched on level meadow.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class HaystackParams:
    """One round stack, centred in its footprint square."""

    side_m: float
    diameter_m: float = DEFAULT_DIAMETER_M
    height_m: float = DEFAULT_HEIGHT_M
    condition: str = "new"
    stack_pole: bool = True
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def radius_m(self) -> float:
        return self.diameter_m / 2.0

    @property
    def shoulder_z_m(self) -> float:
        return self.height_m * SHOULDER_FRACTION

    def profile(self) -> list:
        """The stack's half-section from the foot to the peak, as `(r, z)` pairs.

        The foot, the belly a little above the middle of the body, the shoulder where
        the top is begun, then the top drawn in on a curve that steepens to the peak.
        The last pair is the peak itself, on the axis.
        """
        r, s, h = self.radius_m, self.shoulder_z_m, self.height_m
        top = h - s
        return [
            (FOOT_FRACTION * r, 0.0),
            (0.96 * r, 0.30 * s),
            (r, 0.62 * s),
            (0.97 * r, s),
            (0.84 * r, s + 0.22 * top),
            (0.62 * r, s + 0.48 * top),
            (0.34 * r, s + 0.76 * top),
            (0.10 * r, s + 0.95 * top),
            (0.0, h),
        ]

    def validate(self) -> None:
        if self.condition not in CONDITIONS:
            raise ParamError(f"condition '{self.condition}' not in {CONDITIONS}")
        if not 2.0 <= self.diameter_m <= 7.0:
            raise ParamError(f"diameter_m {self.diameter_m} outside 2-7 m: a round stack "
                             f"pitched by hand off a wagon or a sled")
        if not 2.0 <= self.height_m <= 7.0:
            raise ParamError(f"height_m {self.height_m} outside 2-7 m")
        if self.height_m < 0.8 * self.diameter_m:
            raise ParamError(
                f"a stack {self.height_m} m high and {self.diameter_m} m across is a heap, "
                f"not a stack: it would not shed rain. A stack fed down that far is "
                f"recorded as gone")
        need = self.diameter_m + 2.0 * MARGIN_M
        if self.side_m + 1e-6 < need:
            raise ParamError(
                f"the footprint square is {self.side_m} m and a {self.diameter_m} m stack "
                f"needs {need:.2f} m")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")


CONSUMED = frozenset({"diameter_m", "height_m", "condition", "stack_pole"})


def from_phase(phase: dict, record: dict | None = None) -> HaystackParams:
    """Resolve one structure phase into generator parameters.

    The footprint polygon is the square the stack stands in, from its own (0, 0).
    """
    form = phase.get("form", {})

    def val(attr, default=None):
        a = form.get(attr)
        return default if a is None else a.get("value", default)

    def conf(attr, default="reconstructed"):
        a = form.get(attr)
        return default if a is None else a.get("confidence", default)

    poly = (phase.get("footprint") or {}).get("polygon") or []
    if len(poly) < 3:
        raise ParamError("a haystack needs a footprint square to stand in")
    us = [float(p[0]) for p in poly]
    vs = [float(p[1]) for p in poly]
    if min(us) != 0.0 or min(vs) != 0.0:
        raise ParamError("a haystack's footprint must start at its own (0, 0): the "
                         "generator centres the stack in it from the origin")
    if not math.isclose(max(us), max(vs), abs_tol=0.01):
        raise ParamError("a haystack's footprint is the square it stands in; this one is "
                         f"{max(us)} x {max(vs)} m")
    names = sorted(CONSUMED)
    params = HaystackParams(
        side_m=max(us),
        diameter_m=float(val("diameter_m", DEFAULT_DIAMETER_M)),
        height_m=float(val("height_m", DEFAULT_HEIGHT_M)),
        condition=val("condition", "new"),
        stack_pole=bool(val("stack_pole", True)),
        confidence={n: conf(n) for n in names if n in form},
    )
    params.validate()
    return params
