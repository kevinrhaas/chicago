"""Parameters for the camp archetype — pure Python, NO bpy import.

Same split, same reason, as `pier_crib_params`: `tools/check.sh` imports this on
every commit and must not need Blender.

## What a camp is, and why it is not a building

The Chicago American of 13 June 1835: "our wharves are covered with [men], women and
children just landed from the vessels, and even some store houses have been thrown
open to receive the unsheltered emigrants, who [had else] remained under the open
[sk]y upon the wharves. Some build tents upon the spot [t]hey [we]re landed from the
b[oa]ts." That is the whole of the evidence that a camp stood in the town, and it says
what a camp was: canvas pitched where the boat put people down, by people who were not
staying. `data/reconstruction/1835_camp_grounds.json` rules that a tent is not a
building, and this archetype keeps to it — a camp is not one of the 668 roofs, it
answers no family in the roof programme, and it moves no resident count. It is ground
used by the transient crowd `data/reconstruction/1835_transient_persons.json` deals.

## What it builds

A row, a ring or a scatter of the canvas and kit the crowd slept under and cooked at:

- **tents**, of two period forms: the WALL tent (a ridge on two uprights over a short
  canvas wall — the 9 x 12 ft family tent) and the WEDGE tent (a ridge on two uprights
  with the canvas running to the ground — the 7 x 9 ft "A" tent). Both are the forms
  a quartermaster or an outfitter of the 1830s sold, which is the whole of their
  footing: no source describes the tents at Chicago. `tent_kind` `mixed` alternates
  them, wall first.
- **covered wagons**: a box bed on four wheels under canvas on hoop bows, the tongue
  down. An emigrant family that shipped its wagon by schooner unloaded it at the
  landing with everything else.
- **brush shelters**: a lean-to of poles and cut brush, the cheapest roof there is.
- **fire rings**, each with a pot crane of two forked sticks and a crossbar;
  **woodpiles**; **baggage heaps** (chests and a barrel), which is all an open-sky
  sleeper had to show for a night on the wharf.

**No figure is drawn, in any form** (docs/LIBERTIES.md L1). Smoke is not drawn either:
a column of smoke is the one thing a visitor would read as somebody at the fire.

## Local origin and frame

The footprint polygon's (0, 0) is the origin, as docs/GLB-CONTRACT.md requires; u runs
along the camp (x) and v across it (y), and z = 0 is the ground at the origin. The
FRONT of the camp is its +y edge, v = depth — north at `rotation_deg` 0, the contract's
facade convention — and every tent door, the fire rings and the baggage face it. A
record sets `rotation_deg` to the bearing the camp opened towards: the street, for a
camp on the bank.

## Every dimension here is the archetype's, and owes the liberties document an entry

None of these numbers is attested for Chicago. They are period outfitters' sizes,
stated once here so a record never has to restate them and so a source that sizes a
Chicago tent replaces them in one place.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

TENT_KINDS = ("wall", "wedge", "mixed")
ARRANGEMENTS = ("row", "ring", "scatter")
CANVAS_CONDITIONS = ("new", "weathered", "patched")

# The wall tent: 9 x 12 ft on the ground, a 4 ft wall and the ridge at 8 ft 6 in.
WALL_TENT_W_M = 2.74          # across the door (u)
WALL_TENT_D_M = 3.66          # door to back (v)
WALL_TENT_WALL_M = 1.22
WALL_TENT_RIDGE_M = 2.59

# The wedge tent: 7 x 9 ft on the ground, the ridge at 7 ft.
WEDGE_TENT_W_M = 2.13
WEDGE_TENT_D_M = 2.74
WEDGE_TENT_RIDGE_M = 2.13

# The covered wagon, laid along u: a 10 ft 6 in bed, 3 ft 8 in wide, the tongue 7 ft.
WAGON_BED_L_M = 3.20
WAGON_BED_W_M = 1.12
WAGON_TONGUE_M = 2.13
WAGON_TRACK_M = 1.52          # outside width over the wheels, the 5 ft gauge

BRUSH_SHELTER_W_M = 2.40
BRUSH_SHELTER_D_M = 2.00

# Between any two pitched things along a row, so a guy rope has somewhere to go.
PITCH_GAP_M = 1.10
# The band in front of the tents where fires, wood and baggage stand.
FRONT_BAND_M = 2.10
# Behind the last tent, so the back wall never stands on the polygon's edge.
BACK_MARGIN_M = 0.40

VERTICAL_ANCHOR = "ground"

# A camp stands on the ground over the whole of its outline: the gate asks the
# terrain under the footprint's perimeter to lie within the walker's tolerance of
# the ground at the origin, which is the claim that the camp was pitched on level
# ground and not over the edge of the bank.
GROUND_CONTACT = "perimeter"


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class CampParams:
    """A camp of the transient crowd, laid out inside its footprint rectangle."""

    length_m: float
    depth_m: float
    tents: int = 0
    tent_kind: str = "mixed"
    wagons: int = 0
    brush_shelters: int = 0
    fire_rings: int = 1
    woodpiles: int = 1
    baggage_heaps: int = 0
    arrangement: str = "row"
    canvas_condition: str = "weathered"

    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)

    def tent_kinds(self) -> list:
        """The form of each tent, in pitching order."""
        if self.tent_kind == "mixed":
            return ["wall" if i % 2 == 0 else "wedge" for i in range(self.tents)]
        return [self.tent_kind] * self.tents

    def pitches(self) -> list:
        """The pitched things, in order along the camp: `(kind, width_u, depth_v)`.

        Wagons and brush shelters are dealt in among the tents at even intervals
        rather than bunched at one end, because a camp grew one arrival at a time and
        an arrival with a wagon stood beside one without.
        """
        out = []
        for kind in self.tent_kinds():
            if kind == "wall":
                out.append(("wall_tent", WALL_TENT_W_M, WALL_TENT_D_M))
            else:
                out.append(("wedge_tent", WEDGE_TENT_W_M, WEDGE_TENT_D_M))
        extras = ([("wagon", WAGON_BED_L_M + WAGON_TONGUE_M, WAGON_TRACK_M)] * self.wagons
                  + [("brush_shelter", BRUSH_SHELTER_W_M, BRUSH_SHELTER_D_M)]
                  * self.brush_shelters)
        for i, ex in enumerate(extras):
            at = round((i + 1) * (len(out) + 1) / (len(extras) + 1))
            out.insert(min(at, len(out)), ex)
        return out

    def row_length(self) -> float:
        p = self.pitches()
        return sum(w for _, w, _ in p) + PITCH_GAP_M * (len(p) + 1)

    def deepest(self) -> float:
        return max((d for _, _, d in self.pitches()), default=0.0)

    def validate(self) -> None:
        if not 3.0 <= self.length_m <= 200.0:
            raise ParamError(f"length_m {self.length_m} outside 3-200 m")
        if not 3.0 <= self.depth_m <= 80.0:
            raise ParamError(f"depth_m {self.depth_m} outside 3-80 m")
        if self.tent_kind not in TENT_KINDS:
            raise ParamError(f"tent_kind '{self.tent_kind}' not in {TENT_KINDS}")
        if self.arrangement not in ARRANGEMENTS:
            raise ParamError(f"arrangement '{self.arrangement}' not in {ARRANGEMENTS}")
        if self.canvas_condition not in CANVAS_CONDITIONS:
            raise ParamError(f"canvas_condition '{self.canvas_condition}' not in "
                             f"{CANVAS_CONDITIONS}")
        for name in ("tents", "wagons", "brush_shelters", "fire_rings", "woodpiles",
                     "baggage_heaps"):
            v = getattr(self, name)
            if not isinstance(v, int) or not 0 <= v <= 60:
                raise ParamError(f"{name} {v!r} is not a count between 0 and 60")
        if self.tents + self.wagons + self.brush_shelters + self.fire_rings \
                + self.baggage_heaps == 0:
            raise ParamError("a camp with nothing pitched, no fire and no baggage is "
                             "not a camp; leave the ground empty instead")
        if self.arrangement == "row":
            if self.row_length() > self.length_m + 1e-6:
                raise ParamError(
                    f"the row needs {self.row_length():.2f} m along the camp and the "
                    f"footprint gives {self.length_m} m: fewer pitches, a longer "
                    f"footprint, or a scatter")
            if self.deepest() + FRONT_BAND_M + BACK_MARGIN_M > self.depth_m + 1e-6:
                raise ParamError(
                    f"the row needs {self.deepest() + FRONT_BAND_M + BACK_MARGIN_M:.2f} m "
                    f"across the camp and the footprint gives {self.depth_m} m")
        elif self.arrangement == "ring":
            if self.ring_radius() + self.deepest() + BACK_MARGIN_M \
                    > min(self.length_m, self.depth_m) / 2.0 + 1e-6:
                raise ParamError("the ring does not fit inside the footprint")
        else:
            if len(self.scatter_cells()) < len(self.pitches()):
                raise ParamError(
                    f"the scatter has room for {len(self.scatter_cells())} pitches and "
                    f"is asked for {len(self.pitches())}")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")

    def ring_radius(self) -> float:
        """Radius of the ring the tent fronts stand on: the circumference holds every
        pitch's width plus its gap, and never less than room for the fire."""
        p = self.pitches()
        circ = sum(w for _, w, _ in p) + PITCH_GAP_M * len(p)
        return max(2.5, circ / (2.0 * math.pi))

    def scatter_cells(self) -> list:
        """Cell centres of the scatter's grid, front row first. A cell is sized to
        the largest pitch plus its gap; the jitter inside it is the builder's."""
        p = self.pitches()
        if not p:
            return []
        cw = max(w for _, w, _ in p) + PITCH_GAP_M
        cd = self.deepest() + FRONT_BAND_M
        nu = max(1, int(self.length_m // cw))
        nv = max(1, int((self.depth_m - BACK_MARGIN_M) // cd))
        out = []
        for j in range(nv):
            for i in range(nu):
                out.append(((i + 0.5) * self.length_m / nu, j * cd))
        return out


CONSUMED = frozenset({
    "tents", "tent_kind", "wagons", "brush_shelters", "fire_rings", "woodpiles",
    "baggage_heaps", "arrangement", "canvas_condition",
})


def from_phase(phase: dict, record: dict | None = None) -> CampParams:
    """Resolve one structure phase into generator parameters.

    The footprint polygon is the camp's ground: its u extent is the length along the
    camp and its v extent the depth across it.
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
        raise ParamError("a camp needs a footprint polygon to lay itself out in")
    us = [float(p[0]) for p in poly]
    vs = [float(p[1]) for p in poly]
    if min(us) != 0.0 or min(vs) != 0.0:
        raise ParamError("a camp's footprint must start at its own (0, 0): the "
                         "generator lays the camp out from the origin")

    names = sorted(CONSUMED)
    params = CampParams(
        length_m=max(us),
        depth_m=max(vs),
        tents=int(val("tents", 0)),
        tent_kind=val("tent_kind", "mixed"),
        wagons=int(val("wagons", 0)),
        brush_shelters=int(val("brush_shelters", 0)),
        fire_rings=int(val("fire_rings", 1)),
        woodpiles=int(val("woodpiles", 1)),
        baggage_heaps=int(val("baggage_heaps", 0)),
        arrangement=val("arrangement", "row"),
        canvas_condition=val("canvas_condition", "weathered"),
        confidence={n: conf(n) for n in names if n in form},
    )
    params.validate()
    return params
