"""Parameters for the pier_crib archetype — pure Python, NO bpy import.

Same split, same reason, as `bridge_timber_params`: `tools/check.sh` imports this on
every commit and must not need Blender.

## What this archetype is for

The two harbour piers at the mouth of the Chicago River — the north (weather) pier
and the south pier — begun under the 1833 appropriation and extended every open
season afterwards. They are the first structures in this dataset that are neither a
building nor a crossing: a line of timber cribs, sunk on the lake bed and filled with
stone, standing in open water with a working deck a few feet above it.

`docs/EPOCHS.md` and `docs/ROADMAP.md` both make the point this module depends on:
**piers are STRUCTURES WITH PHASES, not terrain.** A pier that is 700 ft long at the
end of 1834 and 1,260 ft at the end of 1835 is one identity in two states, and the
state is what a phase carries.

## What is actually documented, and what this module therefore refuses to default

Very little, and the little there is comes apart under examination:

- **Length.** Andreas gives the north pier at 1,260 ft "to twelve feet of water" at
  the close of the 1835 season, and the south pier "extended 500 ft in 1835, total
  700 ft"; Wikipedia's *Chicago River* summary gives 200 ft (south) and 700 ft
  (north) at the end of 1834. **No source reached gives a length for any date inside
  the 1835 season.** So a length for 1835-07-01 is an INTERPOLATION between two
  year-end figures, it is `inferred` on the record with the arithmetic written out,
  and there is deliberately no default for it here. A parameter module that
  defaulted a pier's length would be inventing the one number this archetype exists
  to be honest about.
- **Deck height.** `docs/research/01-terrain-hydrology.md` zone 24 gives "deck ~+4
  to +6" ft above the water and cites nothing for it. `DEFAULT_DECK_HEIGHT_M` below
  is the middle of that band and the records tag it `inferred` for exactly that
  reason.
- **Width.** Nothing. Not one source reached states how wide either pier was, and
  **the master survey cannot supply it either**: at Wright 1834's ~1:7,200 a 25-ft
  crib is a fifth of a pen width, so the red pier lines on that sheet carry a
  direction and a position and no thickness at all. `DEFAULT_WIDTH_M` is this
  archetype's own number, records state it `conjectural`, and it owes
  `docs/LIBERTIES.md` an entry.
- **Crib module.** How long each individual crib box was is a builder's convenience
  that no witness would record, so — following the repair `bridge_timber` made when
  `pier_spacing_m` put fifteen supports under a bridge that had two — it is NOT a
  record attribute. It is `CRIB_MODULE_FALLBACK_M`, an archetype constant, and every
  pier built through it inherits an invention that owes the liberties document an
  entry rather than a confidence chip.

## The one thing that IS measured: the line

The alignment is not a guess. Wright 1834 draws the harbour as two red lines with
HARBOR lettered between them, and both lines can be read through the same fitted
affine that `tools/rederive_datum.py` checks the datum against. Read that way the two
drafted pier faces run at **103.4 degrees** and stand **64.2 m** apart — against a
documented entrance width of 200 ft (61.0 m), which is a four-per-cent agreement from
a completely independent direction and is the check that says the right two lines were
read.

What the same sheet does NOT supply is a length: both drafted lines run about 1,165 ft,
which is longer than the north pier was at the end of 1834 (700 ft) and far longer
than the south pier ever was before 1837. Wright drew the harbour as authorised, not
as built. That is recorded on both records and it is why the drafted line is used for
bearing and root and never for extent.

## GROUND_CONTACT is `ends`, and the declaration is half right on purpose

`tools/validate.py` asks every archetype that declares `GROUND_CONTACT` whether its
structures reach the ground under them, and offers two modes: `perimeter` for a
building that meets the terrain all the way round its outline, and `ends` for a
crossing that lands at both ends of its span. **A pier is neither.** It lands at ONE
end — the root, where it leaves the shore — and its other end is open water by
definition. There is no one-ended mode, and inventing one means editing a shared gate
to suit a single archetype.

`ends` is declared anyway, and here is exactly what that buys and costs today. Both
piers in this dataset sit between local E +1216 and E +1589, against a heightfield
that stops at E +320, so `unlanded_values` short-circuits on its `field.covers`
test before it measures anything: the finding is `outside_modelled_ground`, which is
true of both ends and is the honest answer. The declaration therefore makes the piers
VISIBLE to the gate — which declaring nothing would not — and the seaward end costs
nothing while there is no ground anywhere near it.

**It will cost something when `docs/ROADMAP.md` S2e lands** and the terrain box
reaches the harbour. At that point the root will be measured against real ground,
correctly, and the seaward end will be measured against whatever the extended field
puts under open lake — and the gate will ask for `approach_not_modelled` on a pier
head standing in twelve feet of water, which is not a finding about anything. The
right repair then is a `root` mode in the checker, taking only the minimum-u edge.
Written down here rather than left for someone to rediscover.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CONFIDENCE_VALUE = {"attested": 0.0, "inferred": 0.5, "reconstructed": 1.0}

# What a pier of this decade was made of. One value, and the shortness of the list is
# deliberate: `timber_crib` is a log box sunk on the bed and filled with stone, which
# is what this generator builds. A driven-pile trestle is a lighter and quite
# different structure, and adding the word here without the geometry behind it would
# let a record state a construction the mesh silently ignores — the exact fault the
# `geometry:` declarations exist to catch one level up.
CONSTRUCTIONS = ("timber_crib",)

# The middle of docs/research/01-terrain-hydrology.md zone 24's "deck ~+4 to +6" ft.
# Five feet. The dossier cites nothing for the band, so a record taking this value
# records it `inferred` and says where it came from.
DEFAULT_DECK_HEIGHT_M = 1.524

# Twenty-five feet, and it is this module's invention rather than anybody's
# measurement. A gravity crib standing in up to twelve feet of water and carrying a
# working deck has to be wide enough not to be rolled by a lake sea, which is an
# argument for "not narrow" and not an argument for a number. Kept as one constant so
# that every pier in the dataset inherits the SAME invention and a reader can find it
# in one place; records state it `conjectural` and it owes docs/LIBERTIES.md an entry.
DEFAULT_WIDTH_M = 7.62

# How long one crib box is along the pier. Thirty feet. Deliberately NOT a record
# attribute: see the module docstring, and see bridge_timber_params on why
# `pier_spacing_m` had to stop being one. A pier built through this constant is
# inventing every seam it shows.
CRIB_MODULE_FALLBACK_M = 9.144

# The seam between adjacent crib boxes. Cribs were built and sunk one at a time and
# they did not close perfectly; the gap is what makes a pier read as a row of boxes
# rather than as one extruded wall, which is the whole visual difference between a
# timber crib pier and a quay.
CRIB_GAP_M = 0.30

# Where a structure of this archetype is anchored vertically — read by
# tools/compile_scene.py and written into the sidecar. The same reasoning
# bridge_timber gives: the one dimensional statement anybody makes about a pier is a
# height above the WATER, and its cribs run down to a bed this project does not model.
VERTICAL_ANCHOR = "water"

# Where this archetype touches the ground, read by tools/validate.py. `ends` is the
# nearest available reading and it is half right: a pier lands at its root and never
# at its head. See the module docstring for what that costs and when.
GROUND_CONTACT = "ends"


def ground_contact_z(params: "PierCribParams") -> float:
    """Local z at which a pier could meet the ground: the deck.

    A module-level function rather than a `@property`, for the reason
    `bridge_timber_params.ground_contact_z` gives: `generators/mesh_inputs.py`
    hashes every property the parameter class derives, and this one reaches no
    vertex, so making it a property would re-stale a pier for a number no builder
    reads.
    """
    return float(params.deck_height_m or 0.0)


class ParamError(ValueError):
    """A structure record cannot be resolved into valid archetype parameters."""


@dataclass
class PierCribParams:
    """A timber crib pier standing in open water.

    **Local origin.** x runs along the pier away from the land, y across it, and
    **z = 0 is the design water surface**, exactly as for `bridge_timber` and for the
    same reason.

    **Bearing, and why `v0_m` exists.** The thing that is measured off Wright 1834 is
    the pier's INNER (channel) face — the line the draughtsman drew with the harbour
    lettered against it. So that is the line a record's `position` names, and the crib
    is built to one side of it: north of it for the north pier, south of it for the
    south pier. Rather than move the recorded position by a width nobody measured,
    the footprint polygon simply runs from `v0_m` to `v0_m + width_m`, which is
    negative for a pier whose body lies on the far side of its measured face. The
    generator honours that offset, so the mesh's local origin is still the polygon's
    own (0, 0), as docs/GLB-CONTRACT.md requires.

    At `rotation_deg` 0 the pier would run due east with its measured face on the
    south; a record sets `rotation_deg` to its axis bearing minus 90.
    """

    length_m: float
    width_m: float = DEFAULT_WIDTH_M
    deck_height_m: float = DEFAULT_DECK_HEIGHT_M
    construction: str = "timber_crib"

    # The footprint polygon's minimum v. Zero for a pier built on the +v side of its
    # measured face, -width for one built on the -v side. Derived from the polygon by
    # `from_phase`; never stated on a record.
    v0_m: float = 0.0

    confidence: dict = field(default_factory=dict)

    def conf(self, attr: str, default: str = "reconstructed") -> float:
        return CONFIDENCE_VALUE[self.confidence.get(attr, default)]

    def worst_conf(self, *attrs: str) -> float:
        """Least-confident wins — the rule from docs/GLB-CONTRACT.md."""
        return max((self.conf(a) for a in attrs), default=1.0)

    @property
    def cribs(self) -> int:
        """How many crib boxes the run is divided into. At least one."""
        return max(1, round(self.length_m / CRIB_MODULE_FALLBACK_M))

    @property
    def crib_x(self) -> list:
        """`(x0, x1)` for each crib box, with the seam between them.

        Evenly divided, which is the archetype's and not anybody's record: the modules
        are equal because nothing says they were not, and a pier built out over
        several seasons in fact ends where a season ended.
        """
        n = self.cribs
        pitch = self.length_m / n
        half = CRIB_GAP_M / 2.0
        out = []
        for i in range(n):
            x0 = i * pitch + (half if i else 0.0)
            x1 = (i + 1) * pitch - (half if i < n - 1 else 0.0)
            out.append((round(x0, 4), round(x1, 4)))
        return out

    def validate(self) -> None:
        # 2,000 m is past anything the harbour reached before 1840 and well past the
        # traced window; a bigger number is a unit error, not a longer pier.
        if not 10.0 <= self.length_m <= 2000.0:
            raise ParamError(f"length_m {self.length_m} outside 10-2000 m. The north "
                             f"pier stood at about 700 ft at the end of 1834 and "
                             f"1,260 ft at the end of 1835; anything past 2 km is a "
                             f"feet-for-metres slip")
        if not 2.0 <= self.width_m <= 40.0:
            raise ParamError(f"width_m {self.width_m} outside 2-40 m")
        if self.length_m <= self.width_m:
            raise ParamError(
                f"length_m {self.length_m} is not longer than width_m {self.width_m}. "
                f"The footprint polygon's u axis runs ALONG the pier and its v axis "
                f"across it; a polygon the other way round means the record's "
                f"footprint is rotated 90 degrees, which would lay the pier across "
                f"the harbour entrance instead of along it")
        if not 0.3 <= self.deck_height_m <= 6.0:
            raise ParamError(f"deck_height_m {self.deck_height_m} outside 0.3-6 m")
        if self.construction not in CONSTRUCTIONS:
            raise ParamError(f"construction '{self.construction}' not in {CONSTRUCTIONS}")
        for k, v in self.confidence.items():
            if v not in CONFIDENCE_VALUE:
                raise ParamError(f"confidence['{k}'] = '{v}' is not a confidence level")


# The form attributes whose VALUE this archetype reads. `length_m` is in the set even
# though the polygon already carries the length, and that redundancy is the point: the
# length is the interpolated number this record exists to be honest about, it has to
# be visible as its own attribute with its own confidence chip, and `from_phase`
# refuses a record whose stated length and drawn polygon disagree.
CONSUMED = frozenset({"length_m", "width_m", "deck_height_m", "construction"})

# How far the stated length may sit from the drawn polygon before the record is
# rejected. Ten centimetres: the two are meant to be the same number written twice.
LENGTH_AGREEMENT_TOL_M = 0.1


def from_phase(phase: dict, record: dict | None = None) -> PierCribParams:
    """Resolve one structure phase into generator parameters.

    The footprint polygon is the pier's plan: its u extent is the length along the
    pier and its v extent is the width across it.
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
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    length, width = max(us) - min(us), max(vs) - min(vs)

    confidences = {a: conf(a) for a in form}
    confidences["footprint"] = phase.get("footprint", {}).get("confidence", "reconstructed")
    # A record that draws a width but never grades it is graded by the polygon it drew.
    confidences.setdefault("width_m", confidences["footprint"])
    confidences.setdefault("length_m", confidences["footprint"])

    stated_length = val("length_m")
    if stated_length is not None and abs(float(stated_length) - length) > LENGTH_AGREEMENT_TOL_M:
        raise ParamError(
            f"form.length_m is {stated_length} but the footprint polygon is "
            f"{length:.3f} m long. Those are the same claim written twice and they "
            f"disagree; fix the record rather than picking one")

    p = PierCribParams(
        length_m=round(length, 3),
        width_m=round(float(val("width_m", width)), 3),
        deck_height_m=float(val("deck_height_m", DEFAULT_DECK_HEIGHT_M)),
        construction=str(val("construction", "timber_crib")),
        v0_m=round(min(vs), 3),
        confidence=confidences,
    )
    p.validate()
    return p
