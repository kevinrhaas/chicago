#!/usr/bin/env python3
"""Which of the forms a family's roof line offers this town actually builds — said once,
and the refusal recorded where the family's own ridge band cannot carry the other one.
(T-0179)

## The fault this closes

Nine of the thirty-five families are offered a SHED by their crosswalk roof line —
"gable or shed", "front gable or shed", "broad gable or shed". Which of them this project
builds as a shed was decided five times, once inside each anonymous parcel, as a literal
`"shed" if family in (...)` beside the form values. **The five had already drifted.**
`generate_north_infill.py`, `generate_west_infill.py` and `generate_inferred_households.py`
name D2, A3, A4 and A5; `generate_block_infill.py` and `generate_inferred_infill.py` name
D2, A3 and A4. One roof stands on the difference — `recon_1835_south_a5_044` is a gable
where its three A5 siblings are sheds — and nothing in the repo said so, because there was
no one place for the rule to be said in.

So the rule lives here, once, and every parcel reads it.

## The other half, which is the ticket

`tools/measure_ridge_reach.py` sweeps a family's whole authored footprint band and asks
whether the ridge band is reachable from some eave in the eave band at some pitch in the
pitch band. Every family passes on its gable; some fail on the shed, because a shed's
single plane climbs the WHOLE span where a gable climbs half of it, and the `ridge_ft`
column was written for the gable. Nothing was broken, because no generator dealt any of
them a shed; but the crosswalk plainly permits it, and the day a parcel took the
permission the roof would have been built outside its own ridge band.

T-0179 named three of them — C1, F1 and F4. Measured against what the archetypes actually
build, the list is **C1, F1 and W5**, and it is worth saying which way each moved:

* **C1**, the small shop, is `frame_storefront`, and that archetype's `_shed_roof` falls
  from the back wall to the facade whatever the record says about its gable. So the run is
  the DEPTH, 20-30 ft, and no eave in C1's 9-11 ft band reaches its 15-20 ft ridge band at
  any pitch in its 5:12-9:12 over **231 of the 441 footprints** its own band allows.
  Refused, and the refusal is recorded on every C1 record.
* **F1**, the freight shed, is `outbuilding` and authors no open side, so `shed_axis`
  leaves the fall front-to-back down 32-50 ft: **399 of 441**. Refused, recorded.
* **F4**, the lumber shed, is where the ticket's own premise does not survive contact.
  Closed, it is 441 of 441 — but F4's crosswalk entry authors `levels: 1/open`,
  "open posts with slab boards" and "part-open sides", and an open LONG side turns
  `shed_axis` to 'x' (L73). Across its 24-36 ft width instead of its 45-70 ft length,
  **F4 reaches its ridge band at every footprint in its band**. F4's shed is buildable
  inside F4's own claims; nothing has to give way.
* **W5**, the sawmill or riverside shop, is the one the ticket could not see and it is a
  fault in the instrument rather than in the ticket. W5 authors no rise:run, and the sweep
  reports a family with no pitch band before it tests any FORM — so W5's shed was never
  measured at all. Against the 18 degrees a shed is actually dealt, **84 of 441** of its
  own footprints miss its 20-29 ft ridge band. Refused, recorded, and now swept.

The archetype says the same thing in its own voice, which is worth more than this module
saying it: `outbuilding_params.default_roof_type` flips from shed to gable at 5 m of
depth, "because the rise is the run times the pitch and a shallow pitch will not shed
water off riven shakes... over 5 m it rises 1.6 m, which is most of a wall again". F1's
band starts at 9.8 m of depth and F4's at 13.7 m. The ridge band and the archetype's own
default refuse the long closed shed for the same reason.

## What this module will not do

It will not widen a band to make a form fit, and it will not pick the axis that makes a
gate green. The axis a shed falls down is `outbuilding_params.shed_axis`'s answer, read
through `tools/ridge_model.py`, from the open sides the record carries — so F4's verdict
is a fact about F4's entry and not a convenience. And a family in `SHED_FAMILIES` whose
shed the sweep cannot reach FAILS the gate rather than being quietly re-roofed here: a
rule that repairs itself is a rule nobody is keeping.
"""

from __future__ import annotations

import functools
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "generators"))

import band_notes  # noqa: E402
import family_bands  # noqa: E402
import ridge_model  # noqa: E402
from archetypes.outbuilding_params import default_roof_pitch_deg  # noqa: E402

FT = 0.3048

# THE RULE. The families this town builds as sheds — the small ancillary shells whose
# depth the archetype's own `default_roof_type` would give a single slope to anyway: the
# shanty, the privy, the woodshed and the small utility. Every other family the crosswalk
# offers a shed to is built with the gable the same line offers, and `refusals()` below
# says which of those refusals the family's own ridge band forces and which is only this
# town's choice.
#
# Adding a family here is a claim that its shed is buildable inside its own bands, and
# `tools/measure_ridge_reach.py` tests exactly that claim on every commit.
SHED_FAMILIES = ("D2", "A3", "A4", "A5")

# NO PARCEL IS HELD BACK FROM THE RULE ANY MORE, and the table is kept empty rather than
# deleted because emptiness is the claim being made. One entry stood here from T-0179 to
# T-0212: `generate_inferred_infill.py` was one of the two parcels that retyped the shed
# set without A5, and one roof stood on the difference — `recon_1835_south_a5_044` was a
# gable where the other three A5s in this town are sheds. Giving it the shared answer
# CHANGED THE SHAPE OF A BUILDING, so it stale the record's GLB and could not land without
# a bake; T-0212 did that bake, in the same commit as the record, and the entry came out.
#
# The mechanism stays because the next drift will want it: a parcel may name itself here
# to hold ONE family back while its bake is owed. `tools/measure_ridge_reach.py` holds
# this table to `HELD_BASELINE`, which is now `{}` — so it may not grow at all, and a
# parcel that opts a family out fails the gate rather than waiting quietly.
AWAITING_BAKE: dict[tuple[str, str], str] = {}

# The footprint band is swept on a grid rather than at its corners — same grid as the
# family sweep, and for the same reason: the run is monotone in width and depth for every
# archetype here, so the extremes are corners, and the grid is there so an archetype whose
# run stops being monotone cannot slip past a future reader's edit.
GRID = 21

# WHICH FAMILIES THE CROSSWALK BUILDS OPEN, because that and nothing else decides which
# way a shed falls (`shed_axis`, L73) and therefore which span its ridge band is measured
# over. One open LONG side is the minimum that turns the axis; claiming more than the
# entry states would be inventing an elevation, so it is exactly one.
#
# Exactly one family qualifies, and its entry says so three times over: F4's `levels` is
# "1/open", its `construction` is "open posts with slab boards" and its `variants` are
# "part-open sides; stacked boards; rough edges". Nothing is being read between lines.
#
# W5's "open work bay" is DELIBERATELY NOT READ AS ONE, and the judgement is written down
# because it is the judgement that decides W5's verdict. A framing bay left open in a
# wall is not the archetype's `open_sides`, which is "posts and a roof" for a whole
# elevation, and the phrase sits in a variants list beside "timber piles" and "rare
# crane/derrick" — features some instances carry, not a description of the shell. Read as
# an open side it would turn W5's shed from refused to buildable, which is exactly why it
# is not decided by a keyword. If the owner reads it the other way, W5 moves here and the
# gate follows.
OPEN_SIDED_FAMILIES = {"F4": ("left",)}

# The phrases that MUST land a family in the table above. A crosswalk edit that opens a
# family's sides and does not appear here fails `tools/measure_ridge_reach.py`, so the
# table cannot go quietly stale against the specification it reads.
OPEN_SIDE_PHRASES = ("open side", "part-open", "open posts", "1/open")


# The crosswalk is re-read and re-parsed on every `families()` call, and the sweep below
# asks for a family 441 times per form. Cached here rather than in `family_bands`, which
# every generator imports and which has no business holding process state: this module is
# the only caller that asks tens of thousands of times.
@functools.lru_cache(maxsize=1)
def _families() -> dict[str, dict]:
    return family_bands.families()


@functools.lru_cache(maxsize=1)
def _geometry() -> dict[str, dict]:
    return band_notes.geometry()


def _spec(family: str) -> dict | None:
    return _families().get(family)


def offered_forms(family: str) -> list[str]:
    """The roof forms the family's own roof line names, in `ridge_model`'s vocabulary."""
    text = str((_spec(family) or {}).get("roof") or "").lower()
    forms = []
    if "gable" in text or "hip" in text or not text:
        forms.append("gable")
    if "shed" in text:
        forms.append("shed")
    return forms or ["gable"]


def open_sides_for(family: str) -> tuple:
    """The open sides the family's crosswalk entry authors, as `shed_axis` reads them."""
    return OPEN_SIDED_FAMILIES.get(family, ())


def entry_says_open(family: str) -> bool:
    """Does the family's own crosswalk entry use one of `OPEN_SIDE_PHRASES`?

    The audit half of the table above: a family this answers yes for and
    `OPEN_SIDED_FAMILIES` does not carry is a drift between the table and the
    specification, and the gate refuses it.
    """
    geom = _geometry().get(family, {})
    blob = " ".join(str(v).lower() for v in geom.values())
    return any(w in blob for w in OPEN_SIDE_PHRASES)


def roof_kind(family: str, parcel: str | None = None) -> tuple[str, bool | None]:
    """(the form this town builds for the family, whether its gable fronts the street).

    The second value is only ever read to work out which way a roof plane falls; it is
    the record's own `gable_front` for the shopfront families and nothing for the rest.

    `parcel` is the calling generator's own file name, and it is read for one purpose
    only: `AWAITING_BAKE` above. A parcel that passes nothing gets the rule.
    """
    held = AWAITING_BAKE.get((parcel, family)) if parcel else None
    form = held or ("shed" if family in SHED_FAMILIES else "gable")
    return form, (True if family.startswith("C") else None)


def pitch_band(family: str, form: str) -> tuple[float, float]:
    """The pitch band the sweep may use — the family's own, or the generator's default.

    Six of the nine shed-offering families write a roof line with no rise:run in it, so
    their pitch is the archetype's type value and the ridge band is still a testable
    claim against it. The default is asked of the archetype rather than retyped.
    """
    band = family_bands.pitch_band_deg((_spec(family) or {}).get("roof"))
    if band is not None:
        return band
    default = default_roof_pitch_deg(form)
    return (default, default)


def reach_at(family: str, form: str, width_m: float, depth_m: float,
             open_sides: tuple = ()) -> bool | None:
    """Is the family's ridge band reachable on THIS plan, from some eave and some pitch?

    None where the family authors no ridge band or no eave band, which is nothing to
    measure rather than a pass.
    """
    spec = _spec(family)
    if spec is None:
        return None
    ridge = family_bands.ridge_band_m(spec.get("ridge_ft"))
    eave = family_bands.eave_band_m(spec.get("eave_ft"))
    if ridge is None or eave is None:
        return None
    run = ridge_model.ridge_run_m(spec.get("archetype"), form, width_m, depth_m,
                                  roof_kind(family)[1], open_sides)
    if run is None:
        return None
    lo_p, hi_p = pitch_band(family, form)
    lo, hi = family_bands.eave_window_for_ridge(run, lo_p, hi_p, ridge)
    return min(hi, eave[1]) - max(lo, eave[0]) >= -1e-9


def sweep(family: str, form: str, open_sides: tuple | None = None) -> dict | None:
    """Across the whole authored footprint band: how many plans the ridge band misses."""
    spec = _spec(family)
    band = (spec or {}).get("band_ft")
    if spec is None or band is None:
        return None
    if open_sides is None:
        open_sides = open_sides_for(family) if form == "shed" else ()
    lo_w, lo_d, hi_w, hi_d = band
    tested = bad = 0
    worst = None
    for i in range(GRID):
        w = (lo_w + (hi_w - lo_w) * i / (GRID - 1)) * FT
        for j in range(GRID):
            d = (lo_d + (hi_d - lo_d) * j / (GRID - 1)) * FT
            ok = reach_at(family, form, w, d, open_sides)
            if ok is None:
                continue
            tested += 1
            if not ok:
                bad += 1
                if worst is None:
                    worst = (round(w / FT, 1), round(d / FT, 1))
    if not tested:
        return None
    return {"family": family, "form": form, "tested": tested, "unreachable": bad,
            "worst": worst, "open_sides": tuple(open_sides),
            "ridge_ft": spec.get("ridge_ft"), "archetype": spec.get("archetype")}


@functools.lru_cache(maxsize=1)
def refusals() -> dict[str, dict]:
    """Every family offered a shed and built with a gable, and WHY it is not a shed.

    `reason` is `ridge_band` where the family's own ridge band cannot carry the shed
    across its whole footprint band, and `choice` where it can and this town builds the
    gable anyway. The two are different claims and the note a visitor reads says which.
    """
    out = {}
    for family in sorted(_families()):
        if "shed" not in offered_forms(family) or family in SHED_FAMILIES:
            continue
        s = sweep(family, "shed")
        if s is None:
            continue
        out[family] = {
            "reason": "ridge_band" if s["unreachable"] else "choice",
            "unreachable": s["unreachable"], "tested": s["tested"],
            "worst": s["worst"], "ridge_ft": s["ridge_ft"],
            "open_sides": s["open_sides"], "archetype": s["archetype"],
        }
    return out


# --------------------------------------------------------------- the recorded refusal
#
# A refusal that lives only in `SHED_FAMILIES` is a refusal nobody outside this file can
# read. These records are inventions and their whole defence is that the invention is
# bounded by the specification — so where this town declines a form the specification
# offers, the record has to say so, in the same place it already says what the value is
# and what bounds it. It goes on `roof_type`, behind the same `why` a visitor opens on
# every other value, and it carries the number rather than the adjective.
#
# Prose is not hashed into `generators/mesh_inputs.py`'s staleness recipe (that module's
# docstring says why), so recording it moves no geometry and stales no bake.

def refusal_note(family: str, width_m: float, depth_m: float) -> str | None:
    """The sentence appended to a refused family's `roof_type` note, or None."""
    entry = refusals().get(family)
    if entry is None or entry["reason"] != "ridge_band":
        return None
    spec = _spec(family) or {}
    run = ridge_model.ridge_run_m(spec.get("archetype"), "shed", width_m, depth_m,
                                  roof_kind(family)[1], entry["open_sides"])
    here = reach_at(family, "shed", width_m, depth_m, entry["open_sides"])
    lo_p, hi_p = pitch_band(family, "shed")
    authored = family_bands.pitch_band_deg(spec.get("roof")) is not None
    pitches = (f"any pitch between {lo_p:.1f} and {hi_p:.1f} degrees"
               if authored else
               f"the {lo_p:g}-degree pitch a shed is given here, which is the only one "
               f"the family's roof line leaves to test")
    span = f"the whole {run:.1f} m of this plan" if run else "the whole span"
    at_this = ("This building's own plan is one of them"
               if here is False else
               f"This building's own plan is not one of them; the {family} family is "
               f"refused as a whole rather than plan by plan")
    return (f' THE OTHER FORM ON OFFER IS REFUSED, AND HERE IS THE NUMBER. The {family} '
            f'roof line offers "{spec.get("roof")}", and this town builds only the '
            f"gable. A shed is one plane over {span} where a gable climbs half of it, so "
            f"across the {entry['tested']} plans {family}'s own footprint band allows, "
            f"{entry['unreachable']} of them cannot reach the {entry['ridge_ft']} ft "
            f"ridge band the same family authors — at any eave in its "
            f"{spec.get('eave_ft')} ft band and at {pitches}. {at_this}.")


def note_refusal(form: dict, family: str, width_m: float, depth_m: float) -> dict:
    """Append the recorded refusal to `roof_type`'s note. Same shape as `split_notes`.

    Mutates and returns the form dict, for use inline at a call site. A family that is
    not refused, or a form dict with no `roof_type` note, is returned untouched — so the
    diff is exactly the records the refusal reaches.
    """
    value = form.get("roof_type")
    if not isinstance(value, dict) or not isinstance(value.get("note"), str):
        return form
    sentence = refusal_note(family, width_m, depth_m)
    if sentence:
        value["note"] = value["note"].rstrip() + sentence
    return form
