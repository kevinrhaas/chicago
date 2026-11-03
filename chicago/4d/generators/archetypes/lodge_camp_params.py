"""Parameters for the lodge_camp archetype — pure Python, NO bpy import (T-3342).

The working camp of the Potawatomi gathered at Chicago in August 1812, rebuilt from the
`camp` archetype's rows of identical mat domes after the owner, 2026-11-03: *"they cannot
all be identical geometric domes they must look like natural structures with correct
surfaces ... there would be I think fires and areas for cooking"*, then *"any prep areas
like where they keep horses and equipment"* and *"anything required for their
encampment to exist"*.

## What the sources give, and what each thing here rests on

That the camp stood, when and where is the records' (Wau-Bun ch. XVIII-XIX; Currey 1912
chs. II-III). What a camp of these people was made of is read from the nearest accounts
of the Potawatomi and their neighbours on the western lakes in the same years:

- **The mat lodge** (`mat_lodges`, `long_lodges`): Forsyth, agent to the Sauk and Fox,
  1827 — "Their winter lodges are made by driving long poles in the ground in two rows
  ... bending the tops so as to overlap each other, then covering them with mats made of
  what they call puc-wy a kind of rushes or flags, a Bearskin generally serves for a
  door, which is suspended at the top and hangs down, when finished it is not unlike an
  oven with the fire in the center and the smoke omits thro the top" (Blair 1912 v2 pp.
  227-28). Wau-Bun: the mats "seldom more than five or six feet in length, as a greater
  size would be inconvenient in adjusting and preparing the lodges" (ch. VII); a lodge's
  mats "very neat and new", a mat "which hung over the entrance" (ch. XVI); a Winnebago
  camp's "matted lodges, with the blue smoke curling from their tops". Hubbard 1911: the
  Potawatomi's children "lashed to bundles of Indian mats" in the canoes — a family's
  mats travelled with it, which is why a gathering camp is drawn mostly in mats.
- **The bark roof and the bark house** (`bark_roofed_lodges`, `bark_houses`): Forsyth —
  "The Indians have only one way of building their bark huts or summer residences, they
  are built in the form of an oblong, a bench on each of the long sides ... a door at
  each end"; Wau-Bun's summer villages of "neat bark wigwams" and "summer cabins" with
  "bare walls of bark". The camping place was habitual (Currey ch. II, "their favorite
  camping place"), so a few families are given the summer form.
- **The arbor** (`arbors`): Skinner 1927, a Prairie Potawatomi narrator born near Fort
  Dearborn — two brothers "prepared camps and arbors"; "they put me out under a bough
  arbor".
- **The hearth, the kettle, the spit** (`hearths`): the chief's wife who "took a kettle
  and, dipping up some water from the small creek near by" (Currey ch. III, after
  Wau-Bun ch. XIX); Forsyth's "spits to roast their meat on"; Hubbard's feast cooked in
  "the kettle in the presence of all".
- **The scaffold** (`scaffolds`): Hubbard on the Muskegon, "the poles of an Indian
  lodge, bark canoes, and a scaffold upon which was deposited matting for covering
  lodges", and the "scaffold of the lodge" a keg was hidden on.
- **The canoes** (`canoes`): Hubbard's "bark canoes" at the lodges and the Potawatomi
  crossing the lake in canoes; Wau-Bun's "canoes drawn up here and there" before the
  wigwams at Mackinac.
- **The horses** (`horse_pickets`, `pack_saddles`): the horse Mrs. Helm was "placed upon"
  at the encampment (Currey ch. III); Hubbard's Potawatomi ponies, hired to carry goods.
  The animals are not drawn (no horse model stands in 1812 yet); their ground is: the
  tether stakes, the lines, the pack saddles and loads laid by.
- **Drying racks, the hide frame, the mortar, the woodpile**: the work of a camp of
  families in late summer — meat and fish dried, hides scraped, corn pounded (Forsyth's
  Sauk and Fox raise "from seven to eight thousand bushels of corn" and carry "about five
  bushels for each family" with them). None is described at Chicago; each is
  reconstructed (L-1812-potawatomi-camp-2515).

**Nothing is staged.** No person, no ceremony, no sacred bundle or lodge of a society is
drawn, and no lodge is given to a family, band or person. A sweat lodge and a women's
lodge, both usual in a camp of families, are left out on purpose: they are not what a
visitor should be walked into on the eve of the 15th, and nothing describes them here.

## Every dimension is the archetype's

None of these numbers is attested for Chicago. A mat is 1.4-1.8 m long (Wau-Bun's five or
six feet) and a course about a metre deep; the rest are bounded by the bent-pole frame a
family can raise and cover, and stated once here so a source can replace them in one place.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

MAT_CONDITIONS = ("new", "weathered", "mixed")
EDGES = ("none", "north", "south", "east", "west")

# The three lodge sizes the layout deals, (across the door, door to back, to the crown).
LODGE_SIZES = ((3.0, 3.9, 2.15), (3.5, 4.6, 2.4), (4.0, 5.4, 2.6))
LONG_LODGE = (4.3, 8.4, 2.75)
BARK_HOUSE = (4.4, 6.8, 1.75, 3.25)   # width, length, wall height, ridge height
ARBOR = (3.6, 2.7, 2.15)              # length, depth, height to the boughs
RACK_L_M = 3.0
SCAFFOLD = (2.0, 1.4, 1.55)           # length, depth, platform height
CANOE_L_M = 5.2

# The covering's tile, the same number as each material.json's `span_m` (T-3342's
# library, assets/textures/camp_1812_pbr/): the GLB's UVs are written in tiles.
MAT_SPAN_M = 1.0
BARK_SPAN_M = 1.2
BOUGH_SPAN_M = 1.5
# A mat's length round the lodge and a course's depth up it (Wau-Bun: "seldom more than
# five or six feet in length").
MAT_LEN_M = (1.4, 1.8)
COURSE_M = 0.95

# Clear ground kept round everything, so a walker can pass between lodges.
GAP_M = 1.1
MARGIN_M = 0.6

VERTICAL_ANCHOR = "ground"
GROUND_CONTACT = "perimeter"

COUNTS = ("mat_lodges", "long_lodges", "bark_roofed_lodges", "bark_houses", "arbors",
          "hearths", "drying_racks", "scaffolds", "hide_frames", "woodpiles", "mortars",
          "canoes", "horse_pickets", "pack_saddles")


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class LodgeCampParams:
    """One group of the camp, laid out inside its footprint rectangle."""

    length_m: float
    depth_m: float
    seed_name: str = ""
    mat_lodges: int = 0
    long_lodges: int = 0
    bark_roofed_lodges: int = 0
    bark_houses: int = 0
    arbors: int = 0
    hearths: int = 0
    drying_racks: int = 0
    scaffolds: int = 0
    hide_frames: int = 0
    woodpiles: int = 0
    mortars: int = 0
    canoes: int = 0
    horse_pickets: int = 0
    pack_saddles: int = 0
    canoe_edge: str = "none"
    mat_condition: str = "mixed"
    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def seed(self) -> int:
        """A stable seed from the record's id (crc32, not Python's salted hash), so two
        bakes of one record lay the camp out the same and two groups differ."""
        return zlib.crc32(self.seed_name.encode("utf-8")) & 0xFFFFFFFF

    @property
    def dwellings(self) -> int:
        return self.mat_lodges + self.long_lodges + self.bark_roofed_lodges + self.bark_houses

    def validate(self) -> None:
        if not 6.0 <= self.length_m <= 80.0:
            raise ParamError(f"length_m {self.length_m} outside 6-80 m")
        if not 6.0 <= self.depth_m <= 60.0:
            raise ParamError(f"depth_m {self.depth_m} outside 6-60 m")
        if self.mat_condition not in MAT_CONDITIONS:
            raise ParamError(f"mat_condition '{self.mat_condition}' not in {MAT_CONDITIONS}")
        if self.canoe_edge not in EDGES:
            raise ParamError(f"canoe_edge '{self.canoe_edge}' not in {EDGES}")
        for name in COUNTS:
            v = getattr(self, name)
            if not isinstance(v, int) or not 0 <= v <= 40:
                raise ParamError(f"{name} {v!r} is not a count between 0 and 40")
        if self.canoes and self.canoe_edge == "none":
            raise ParamError("canoes are drawn up along an edge of the ground: name it")
        if not any(getattr(self, n) for n in COUNTS):
            raise ParamError("a camp ground with nothing on it is not a camp; leave the "
                             "ground empty instead")
        # The rough area test: every dwelling's plan plus its gap must fit the ground
        # with room to spare for the yards. The layout itself refuses what it cannot
        # place (lodge_camp.layout), so this only catches the absurd early.
        need = (self.mat_lodges + self.bark_roofed_lodges) * (4.6 + GAP_M) * (5.4 + GAP_M) \
            + self.long_lodges * (4.3 + GAP_M) * (8.4 + GAP_M) \
            + self.bark_houses * (4.4 + GAP_M) * (6.8 + GAP_M) \
            + self.arbors * 30.0
        if need > 0.8 * self.length_m * self.depth_m:
            raise ParamError(f"the group needs about {need:.0f} m2 and the footprint gives "
                             f"{self.length_m * self.depth_m:.0f}: fewer lodges or more ground")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")


CONSUMED = frozenset(set(COUNTS) | {"canoe_edge", "mat_condition"})


def from_phase(phase: dict, record: dict | None = None) -> LodgeCampParams:
    """Resolve one structure phase into generator parameters.

    The footprint polygon is the group's ground, from its own (0, 0): u along it, v across.
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
        raise ParamError("a camp ground needs a footprint polygon to lay itself out in")
    us = [float(p[0]) for p in poly]
    vs = [float(p[1]) for p in poly]
    if min(us) != 0.0 or min(vs) != 0.0:
        raise ParamError("a camp ground's footprint must start at its own (0, 0)")
    names = sorted(CONSUMED)
    kw = {n: int(val(n, 0)) for n in COUNTS}
    params = LodgeCampParams(
        length_m=max(us), depth_m=max(vs),
        seed_name=(record or {}).get("id", "") + "/" + phase.get("id", ""),
        canoe_edge=val("canoe_edge", "none"),
        mat_condition=val("mat_condition", "mixed"),
        confidence={n: conf(n) for n in names if n in form},
        **kw,
    )
    params.validate()
    return params
