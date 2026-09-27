#!/usr/bin/env python3
"""Which of the town's houses stand behind a CENTRE HALL, read off the family's own
crosswalk entry — said once, and the refusal recorded where the entry offers a front
this town cannot build. (T-1686)

## The fault this closes

`plan` is the room arrangement behind the wall and it is what actually decides where the
front door goes: `hall_parlour` puts the door off centre against the partition and spaces
the openings unevenly, `centre_passage` is the symmetrical five-bay front with the door
in the middle of it (`generators/archetypes/frame_dwelling_params`, L77-85). Which
families get which was decided FIVE times, once inside each anonymous parcel, beside the
form values — and, exactly like the shed rule `tools/roof_form.py` was written for, the
five had already drifted:

| parcel | centre passage for | five bays for | chimneys |
|---|---|---|---|
| `generate_block_infill.py` | D7, H2 | D7, H2 | 2 for D7 and H2 |
| `generate_inferred_infill.py` | D7, H2 | D7, H2 | 2 for H2 only |
| `generate_north_infill.py` | D7, H2, **H3** | D7, H2, **H3** | 2 for every H |
| `generate_west_infill.py` | D7, H2 | D7, H2 | 2 for every H |
| `generate_inferred_households.py` | **any two-storey** | any two-storey | 1 for everything |

**And all five refuse H1 the centre hall its own crosswalk entry requires.** H1's
`required_variant` is literally `center_hall_one_and_half`; its variants line reads
"5 bays; center hall; kitchen ell; small porch"; and it is the ONLY family of the
thirty-five whose entry names a centre hall or states a bare bay count rather than a
range. Seven roofs stand on the difference — three of them in the Randolph-Washington
tier, where the placement policy seats the town's merchants and professionals — and
every one of them came out of the bake as a three-bay cottage front with the door off
centre. Nothing in the repo said so, because the claim was spelled the same way in five
places and the specification was not asked in any of them.

So the reading lives here, once, and every parcel asks it.

## What this module will not do

**It will not resolve the four disagreements in the table above**, and that is deliberate
rather than unfinished. Each of them moves committed roofs that somebody adjudicated —
H3's centre passage in the North, D7's second chimney, the households parcel's
storey-keyed rule — and a redeal is not licence to move a roof nobody asked about. So the
two readers below are ADDITIVE: each takes the parcel's own default and returns it
untouched unless the family's own entry states otherwise, which exactly one family does.
The measured drift is filed rather than swept.

## The other half: what H2's entry offers that this town refuses

H2's crosswalk variants are "Greek doorway; corner boards; 1-2 chimneys" and its roof
line is "side gable or hip". Measured against what `frame_dwelling` actually builds:

* **corner boards** and **1-2 chimneys** already stand. The archetype's trim IS its
  construction argument and the corner boards follow the stud module
  (`frame_dwelling.py` L52); every H2 in this town carries two chimneys.
* **the hip is refused, and loudly.** `frame_dwelling_params.ROOF_TYPES` is gable and
  shed: "a hip, gambrel or mansard roof on a Chicago house in 1835 would be a claim
  rather than a default, so the archetype refuses it loudly instead of quietly
  substituting a gable".
* **the Greek doorway is refused BY DATE.** The earliest Greek Revival house in Chicago
  is the Clarke House of 1836 — `data/exclusions.json` § `clarke_house`, "Built 1836,
  and well outside the platted town in any case", earliest scene 1837 — so an
  entablature, a corner pilaster and a portico are one year and one scene away from
  1835-07-01, and nothing in the archetype builds them.

A refusal that lives only in a Python constant is a refusal no visitor can read, so the
sentence goes onto the record, beside the note that already says which archetype the
H family resolves through. Prose is not hashed into `generators/mesh_inputs.py`'s
staleness recipe, so recording it moves no geometry and stales no bake.
"""

from __future__ import annotations

import functools
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import family_bands  # noqa: E402

CROSSWALK_PATH = ROOT / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json"

# The phrases a crosswalk entry uses to name a centre hall. Read across the whole entry
# — the `required_variant` slug as well as the geometry strings — because H1 states it
# in both and a family that stated it in only one would still be stating it.
CENTRE_HALL_PHRASES = ("center hall", "centre hall", "center_hall", "centre_hall",
                       "center-hall", "centre-hall", "centre passage", "center passage")

# A BARE bay count, which is a statement, as against the ranges `band_notes.BAY_RANGE_RE`
# already reads, which are a band. "2/3 bays", "3/5 bays" and "2-3 shop bays" are bands
# and are NOT read here; "5 bays" is a count. The look-behind is what separates them: in
# "3/5 bays" the 5 is preceded by a separator and this pattern declines it.
BARE_BAY_RE = re.compile(r"(?<![\d/\-–])\b(\d+)\s+bays\b")

# THE MEASURED DRIFT, filed rather than swept — see the module docstring. Each entry is
# (parcel, family): what that parcel says the others do not. `tools/test_house_front.py`
# holds this table against the parcels themselves, so it cannot go stale in either
# direction: an entry that stops being true fails, and a disagreement that is not
# listed fails too.
KNOWN_DISAGREEMENTS = {
    ("generate_north_infill.py", "H3"): "centre passage and five bays; no other parcel",
    ("generate_inferred_infill.py", "D7"): "one chimney; the block parcel gives two",
    ("generate_inferred_households.py", "D7"): "one chimney, and the plan is keyed to "
                                               "the storey count rather than the family",
}


@functools.lru_cache(maxsize=1)
def _families() -> dict[str, dict]:
    return family_bands.families()


@functools.lru_cache(maxsize=1)
def _entries() -> dict[str, dict]:
    """The crosswalk's own rows, whole.

    `family_bands.families()` normalises an entry down to the bands a generator samples
    from and drops `required_variant` with the rest of the prose columns. The required
    variant is half of what this module reads — H1's is literally
    `center_hall_one_and_half` — so the file is read once more here rather than
    widening a normaliser every parcel imports.
    """
    rows = json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))["families"]
    return {row["id"]: row for row in rows}


def required_variant(family: str) -> str:
    return str((_entries().get(family) or {}).get("required_variant") or "")


def _blob(family: str) -> str:
    """Everything the family's own entry says, lower-cased, as one string."""
    spec = _families().get(family) or {}
    parts = [str(v) for v in spec.values() if isinstance(v, (str, int, float))]
    parts.append(required_variant(family))
    return " ".join(parts).lower()


def _variants(family: str) -> str:
    return str((_families().get(family) or {}).get("variants") or "")


def entry_names_centre_hall(family: str) -> bool:
    """Does the family's own crosswalk entry name a centre hall?

    True for H1 and nothing else in the committed crosswalk. A family this answers yes
    for gets the symmetrical front whatever the calling parcel's default was.
    """
    return any(p in _blob(family) for p in CENTRE_HALL_PHRASES)


def stated_bays(family: str) -> int | None:
    """The bay count the family's own variants line STATES, or None where it bands one.

    None is not a zero and not a refusal: it means the entry gives a range or says
    nothing, and the parcel's own default stands.
    """
    m = BARE_BAY_RE.search(_variants(family))
    return int(m.group(1)) if m else None


def plan_for(family: str, default: str) -> str:
    """The room plan, asked of the family's entry and falling back to the parcel's."""
    return "centre_passage" if entry_names_centre_hall(family) else default


def bays_for(family: str, default: int) -> int:
    """The bay count, asked of the family's entry and falling back to the parcel's."""
    stated = stated_bays(family)
    return default if stated is None else stated


# ------------------------------------------------------------- the recorded refusal

_HIP = ('the hip its roof line offers ("{roof}") is refused rather than quietly '
        'substituted, because a hip, gambrel or mansard roof on a Chicago house in '
        '1835 would be a claim and not a default')
_GREEK = ("the Greek doorway its variants name is refused BY DATE — the earliest Greek "
          "Revival house in Chicago is the Clarke House of 1836, which "
          "data/exclusions.json keeps out of this scene, so no entablature, corner "
          "pilaster or portico stands on a roof of 1835-07-01")
_STANDING = ("the corner boards and the one-to-two chimneys the same line names already "
             "stand: the trim follows the stud module the construction argument picks")


def mapping_note(family: str) -> str:
    """The sentence an H-family record carries about the archetype it resolves through.

    Returns "" for a family this does not speak to, so a call site can concatenate it
    unconditionally the way `generate_block_infill` already does.
    """
    if not family.startswith("H"):
        return ""
    note = (" H-family house massing currently resolves through the frame dwelling "
            "archetype; no larger house generator is implemented.")
    if entry_names_centre_hall(family):
        note += (f" THE CENTRE HALL IS THE ENTRY'S, NOT THIS PARCEL'S (T-1686). "
                 f"{family} is the only family of the thirty-five whose crosswalk entry "
                 f"names a centre hall and states a bare bay count — its required "
                 f"variant is \"{required_variant(family)}\" and "
                 f"its variants line reads \"{_variants(family)}\" — so the plan and the "
                 f"bay count below are read off that entry and not dealt by this parcel. "
                 f"The kitchen ell and the small porch the same line offers are NOT "
                 f"raised with them: both are selectable variants beside the required "
                 f"one, and an ell is a footprint fact this record's rectangle does not "
                 f"carry.")
    if family == "H2":
        roof = str((_families().get(family) or {}).get("roof") or "")
        note += (f" TWO OF THIS FAMILY'S NAMED VARIANTS ARE REFUSED AND TWO STAND "
                 f"(T-1686): {_HIP.format(roof=roof)}; {_GREEK}; and {_STANDING}.")
    return note
