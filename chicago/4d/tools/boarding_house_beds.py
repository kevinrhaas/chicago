#!/usr/bin/env python3
"""The medium boarding house sized from its beds (T-1806).

T-1778 sized the town's first H3 boarding house from the lodging model's beds: one
chamber per three lodgers on a crowded night gives its upper-storey windows, one box
stove per three sleepers on an ordinary night gives its stovepipes. The five H2 houses
the North and West parcels raised are boarding houses in the same model
(`medium_boarding_house`, apportioned beds of their own), but stood with the tavern's
five-bay upper storey and no stove pipe at all — the beds were counted and nothing on
the house said so. This module carries the SAME two ratios to them, so the town has one
rule for what a boarding house's beds look like from the street.

What differs from the H3 is only the window band, because the H2 crosswalk entry (a
"merchant or professional house") states none:

* the FLOOR is five, the five-bay elevation every one of these houses has stood with —
  a house sized from its beds never shows fewer chambers than it already did;
* the CEILING is ten, the H3 crosswalk's own top — a medium house does not out-window
  the large one;
* and then, exactly as for the H3, the sashes the front can carry with a pier between
  them (`frame_tavern_params.UPPER_BAY_MIN_M`), because the archetype refuses past it.

Neither ratio is read off any source; docs/LIBERTIES.md (L324) owns them, beside L318
which owns them for the H3. Both generators call `size_from_beds` and nothing else, so
`--check` re-derives the counts from the committed lodging model.

T-1807 carries the stove half of the rule to the two SMALL boarding houses (H1), which
stand on `frame_dwelling`. `stovepipes_from_beds` is that half alone: the H1 crosswalk
entry states its front outright ("5 bays; center hall"), and a half-storey house lights
its chambers from the gable ends rather than from a row of upper sashes, so the beds
size no window there. docs/LIBERTIES.md (L325) owns the carry.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import frame_tavern_params as tavern  # noqa: E402

LODGING_MODEL = ROOT / "data" / "reconstruction" / "1835_lodging_model.json"
H2_UPPER_WINDOWS = (5, 10)        # the house's own five bays .. the H3 crosswalk's top
STOVEPIPES = (2, 6)               # "multiple", and no more than the archetype carries
LODGERS_PER_CHAMBER = 3           # the crowded night: two to a bed and one on the floor
SLEEPERS_PER_STOVE = 3            # the ordinary night: a stove to a chamber in use

CAPACITY_WHY = (
    "SIZED FROM THE HOUSE'S MODELLED BEDS rather than chosen, and still not a reading "
    "of any source about this house: the count is re-derivable from this record's "
    "`reconstruction.capacity` block, which names the lodging-model row it read and the "
    "rule that turned beds into this number. It is the H3 boarding house's rule (L318) "
    "carried to the medium house the lodging model also counts as a boarding house; "
    "the count indicates capacity and is not a recovered interior plan, and "
    "docs/LIBERTIES.md (L324) owns the ratios.")

CAPACITY_WHY_H1 = (
    "SIZED FROM THE HOUSE'S MODELLED BEDS rather than chosen, and still not a reading "
    "of any source about this house: the count is re-derivable from this record's "
    "`reconstruction.capacity` block, which names the lodging-model row it read and the "
    "rule that turned beds into this number. It is the H3 boarding house's stove ratio "
    "(L318) carried to the small house the lodging model also counts as a boarding "
    "house; the count indicates capacity and is not a recovered interior plan, and "
    "docs/LIBERTIES.md (L325) owns the carry.")

_MODEL: dict | None = None


def _model() -> dict:
    global _MODEL
    if _MODEL is None:
        _MODEL = json.loads(LODGING_MODEL.read_text(encoding="utf-8"))
    return _MODEL


def lodging_capacity(sid: str) -> dict:
    """The beds the lodging model gives this house, or its class's per-place figure."""
    for row in _model()["places"]:
        if row["id"] == sid:
            return {"beds_ordinary": int(row["beds_ordinary"]),
                    "beds_crowded": int(row["beds_crowded"]),
                    "from": "data/reconstruction/1835_lodging_model.json",
                    "row": f"places[id={sid}]"}
    cls = next(c for c in _model()["classes"] if c["class"] == "boarding_house")
    return {"beds_ordinary": int(cls["ordinary_per_place"]),
            "beds_crowded": int(cls["crowded_per_place"]),
            "from": "data/reconstruction/1835_lodging_model.json",
            "row": "classes[class=boarding_house] per-place figure: the house is not yet "
                   "a place in the model, which apportions only buildings that stand"}


def size_from_beds(sid: str, width: float) -> tuple[dict, int, int]:
    """(capacity block, upper windows, stovepipes) for one H2 boarding house."""
    cap = lodging_capacity(sid)
    lo, hi = H2_UPPER_WINDOWS
    chambers = -(-cap["beds_crowded"] // LODGERS_PER_CHAMBER)
    want = max(lo, min(hi, chambers))
    fits = int(width / tavern.UPPER_BAY_MIN_M)
    windows = min(want, fits)
    plo, phi = STOVEPIPES
    stoves = -(-cap["beds_ordinary"] // SLEEPERS_PER_STOVE)
    pipes = max(plo, min(phi, stoves))
    cap["sizes"] = {
        "upper_windows": (
            f"ceil({cap['beds_crowded']} crowded beds / {LODGERS_PER_CHAMBER} to a "
            f"chamber) = {chambers}, held to {lo}-{hi} (the house's own five bays to the "
            f"H3 crosswalk's top) = {want}"
            + (f", then to the {fits} sashes a front of {width:.2f} m carries at "
               f"{tavern.UPPER_BAY_MIN_M} m a bay" if fits < want else "")
            + f": {windows} across the upper storey of the front and of the rear"),
        "stovepipes": (
            f"ceil({cap['beds_ordinary']} ordinary beds / {SLEEPERS_PER_STOVE} to a "
            f"stove) = {stoves}, held to {plo}-{phi}: {pipes}"),
        "chimneys": ("not sized by the beds: the two brick stacks are the household's "
                     "kitchen and common-room hearths, and the stoves the beds add go "
                     "out through the roof as stovepipes"),
    }
    return cap, windows, pipes


def stovepipes_from_beds(sid: str) -> tuple[dict, int]:
    """(capacity block, stovepipes) for one H1 small boarding house (T-1807)."""
    cap = lodging_capacity(sid)
    plo, phi = STOVEPIPES
    stoves = -(-cap["beds_ordinary"] // SLEEPERS_PER_STOVE)
    pipes = max(plo, min(phi, stoves))
    cap["sizes"] = {
        "stovepipes": (
            f"ceil({cap['beds_ordinary']} ordinary beds / {SLEEPERS_PER_STOVE} to a "
            f"stove) = {stoves}, held to {plo}-{phi}: {pipes}"),
        "upper_windows": ("not sized by the beds: the H1 crosswalk states the front "
                          "(5 bays, centre hall), and the half storey's chambers are lit "
                          "from its gable ends rather than by a row of upper sashes"),
        "chimneys": ("not sized by the beds: the two brick stacks are the household's "
                     "kitchen and common-room hearths, and the stoves the beds add go "
                     "out through the roof as stovepipes"),
    }
    return cap, pipes
