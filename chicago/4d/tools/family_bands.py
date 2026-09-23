#!/usr/bin/env python3
"""The one sampling rule: a family's authored band, and how an instance is drawn from it.

`data/reconstruction/1835_family_archetype_crosswalk.json` authors, per family, the
footprint band, the storey count, the eave band and the placeholder archetype. This
module is the single place that reads them and the single place that turns a band into
an instance's dimensions.

It exists because the same arithmetic was in two files and only one of them ran it.
`tools/generate_block_infill.py` samples inside the band, so its twelve blocks carry a
size distribution; `tools/generate_north_infill.py` retyped one value per family into
Python, so its sixty roofs were the same building sixty times (ROADMAP T-V1). Uniformity
is itself a claim and no source makes it, so the rule moved here and both parcels import
it rather than one of them owning it.

**Sampling adds variety, not knowledge.** Every value it returns is an invention bounded
by the family band; it grades at the bottom tier wherever it lands, exactly as the
constant it replaced did. What changes is that the band is now used as the range it was
authored as instead of being collapsed to a point.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
CROSSWALK_PATH = ROOT / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json"

FOOTPRINT_RE = re.compile(r"^\s*(\d+)x(\d+)\s*-\s*(\d+)x(\d+)")
RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$")
# The rise:run pair a family's roof line names — "side or front gable, 7:12-10:12".
# Same expression `tools/band_notes.py` and `tools/measure_band_claims.py` already use
# to decide whether a pitch may cite the band at all; kept identical on purpose, so a
# family this module samples for is exactly a family the gate tests.
PITCH_RE = re.compile(r"(\d+):12\s*-\s*(\d+):12")


def stable_fraction(key: str, slot: int) -> float:
    raw = hashlib.sha256(f"{key}:{slot}".encode()).digest()
    return int.from_bytes(raw[:4], "big") / 0xFFFFFFFF


def families() -> dict[str, dict]:
    """Per-family geometry and archetype, as the crosswalk authors them."""
    table: dict[str, dict] = {}
    for fam in json.loads(CROSSWALK_PATH.read_text(encoding="utf-8"))["families"]:
        geom = fam.get("key_geometry_parameters") or {}
        entry = {
            "label": fam.get("label"),
            "archetype": fam.get("current_placeholder_archetype"),
            "levels": geom.get("levels"),
            "eave_ft": geom.get("eave_ft"),
            "roof": geom.get("roof"),
            "ridge_ft": geom.get("ridge_ft"),
            "band_ft": None,
        }
        m = FOOTPRINT_RE.match(str(geom.get("footprint_ft") or ""))
        if m:
            entry["band_ft"] = [int(m.group(1)), int(m.group(2)),
                                int(m.group(3)), int(m.group(4))]
        table[fam["id"]] = entry
    return table


def dimensions_m(family: str, band_ft: list[int], key: str) -> tuple[float, float]:
    """A rectangle sampled deterministically inside the family's authored band.

    The sampling is the phase-one parcel's, unchanged, so the same family reads the
    same size distribution wherever it stands.
    """
    lo_w, lo_d, hi_w, hi_d = band_ft
    width_ft = lo_w + (hi_w - lo_w) * (.18 + .70 * stable_fraction(key, 1))
    depth_ft = lo_d + (hi_d - lo_d) * (.15 + .72 * stable_fraction(key, 2))
    width, depth = width_ft * .3048, depth_ft * .3048
    # The implemented frame dwelling is eaves-front. Families whose band reaches a
    # gable-front proportion are held inside the archetype that exists rather than
    # being drawn as something the generator cannot build.
    if family.startswith(("D", "H")) and family not in ("D1", "D2") and depth > width * 1.46:
        width = min(hi_w * .3048, depth / 1.46)
    return round(width, 3), round(depth, 3)


def storeys(levels: str, key: str | None = None) -> tuple[float, bool]:
    """(storeys, has a loft) from the crosswalk's `levels` string.

    Three of the crosswalk's families author `levels` as a BAND rather than a value —
    T1 is `1.5-2`, W2 is `1-1.5` — for the same reason the footprint and eave columns
    are bands: the typology covers a range and no source narrows it. Those are sampled
    on the half-storey step the vocabulary uses, from the same stable key as every
    other dimension, so a family that stands more than once does not stand at one
    height. A band asked for without a key still fails loudly: collapsing it to its
    low end silently is the retyping this module exists to stop.
    """
    text = str(levels or "1").strip()
    loft = "loft" in text
    head = text.split("+")[0].strip()
    band = RANGE_RE.match(head)
    if band:
        lo, hi = float(band.group(1)), float(band.group(2))
        if key is None:
            raise SystemExit(f"levels '{levels}' is a band, not a value; pass a key to "
                             f"sample it rather than collapsing it")
        steps = [lo + .5 * i for i in range(int(round((hi - lo) / .5)) + 1)]
        return steps[min(int(stable_fraction(key, 9) * len(steps)), len(steps) - 1)], loft
    try:
        return float(head), loft
    except ValueError:
        raise SystemExit(f"cannot read a storey count from levels '{levels}'")


# A door has to fit under a wall, and two of the small ancillary families are authored
# with an eave band whose bottom is below the height the implemented outbuilding needs
# to carry its own man door plus a header — A3 runs 6-7 ft, and a sample at 1.891 m is
# refused by name. The band is not wrong: the phase-one parcel's privies stand at
# 2.05 m, which is 6.73 ft and inside it. Uniform sampling across the band is what is
# wrong. So the sample is taken from the part of the authored band the archetype can
# actually build, and a family whose whole band is below that floor fails loudly rather
# than being quietly raised out of its own typology.
DOOR_HEADROOM_M = 2.05


def wall_height_m(family: str, eave_ft: str, key: str, floor: float = 0.0,
                  ceiling: float | None = None) -> float:
    m = RANGE_RE.match(str(eave_ft or ""))
    if not m:
        raise SystemExit(f"{family}: eave height '{eave_ft}' is not a numeric band")
    lo, hi = float(m.group(1)) * .3048, float(m.group(2)) * .3048
    if floor > hi:
        raise SystemExit(f"{family}: the authored eave band {eave_ft} ft tops out at "
                         f"{hi:.2f} m, below the {floor:.2f} m its archetype needs to "
                         f"carry a door")
    lo = max(lo, floor)
    if ceiling is not None:
        if ceiling < lo:
            raise SystemExit(f"{family}: the authored eave band {eave_ft} ft starts at "
                             f"{lo:.2f} m, above the {ceiling:.2f} m its archetype will "
                             f"carry at this storey count — no part of the band is "
                             f"buildable, so the band and the archetype disagree about "
                             f"the family and one of them has to be settled")
        hi = min(hi, ceiling)
    return round(lo + (hi - lo) * stable_fraction(key, 8), 3)


# Which families take a headroom floor at all. Only the door-carrying outbuilding
# families do; a house's eave band is far above it and clamping there would be
# inventing a storey height.
#
# HOW HIGH the floor is depends on WHICH DOOR, and that is not a constant. 2.05 m is
# the phase-one privies' height and carries a man door, but a wagon door is 3.00 m in
# the clear and the outbuilding archetype refuses a wall that cannot header it — which
# is how the North parcel's blacksmith shop failed the moment it started sampling its
# own band instead of standing at a retyped 3.42 m. So the floor is asked of the
# archetype's own door table rather than retyped here: retyping it is the fault this
# module exists to fix.
def eave_floor(family: str, door: str = "man") -> float:
    if not (family.startswith(("A", "W")) or family in ("D2", "F1")):
        return 0.0
    from archetypes.outbuilding_params import DOOR_SIZE_M  # noqa: PLC0415
    head = DOOR_SIZE_M.get(door, DOOR_SIZE_M["man"])[1]
    return max(DOOR_HEADROOM_M, round(head + DOOR_HEADER_M, 3))


# The stock over a door's clear opening, as the outbuilding archetype's own validator
# measures it: a wall must stand more than this above the door head.
DOOR_HEADER_M = 0.08


# THE OTHER END OF THE SAME BAND (T-0142). `eave_floor` exists because part of a
# family's authored eave band is below what its archetype can build; H2 is the mirror
# image — the merchant house's band runs 18-21 ft, and `frame_dwelling` refuses a
# two-storey wall over 6.2 m because the one attested ceiling height in this dataset is
# the Green Tree's seven and a half feet and a house was not built taller than the
# hotel. So roughly the top third of H2's band cannot be built at all, and a uniform
# sample lands in it about a third of the time: the schedule dealt `blk_randolph_dearborn`
# an H2 at 6.234 m and the generator refused to build it.
#
# The band is not wrong and the archetype is not wrong. Uniform sampling across the
# whole of the band is what is wrong, which is exactly the reading `eave_floor` already
# took at the bottom: the sample is drawn from the part of the authored band the
# archetype can actually build, and a family NONE of whose band is buildable fails
# loudly rather than being quietly shortened out of its own typology. A clamped value is
# still inside the band it cites, so the note it carries stays true and
# `tools/measure_band_claims.py` keeps passing it.
#
# The limit is ASKED OF THE ARCHETYPE, never retyped here — an archetype that publishes
# no `WALL_HEIGHT_M` table names no storey-dependent limit and gets no ceiling. Only
# frame_dwelling publishes one today; frame_tavern, log_dwelling, frame_storefront and
# outbuilding carry flat limits far above any eave band the crosswalk authors.
def eave_limits(archetype: str | None,
                stories: float | None) -> tuple[float, float | None]:
    """(floor, ceiling) the archetype will carry at this storey count.

    `(0.0, None)` for an archetype that publishes no `wall_height_band_m` — it names no
    storey-dependent limit and gets none imposed. Only frame_dwelling publishes one
    today; frame_tavern, log_dwelling, frame_storefront and outbuilding carry flat
    limits far outside any eave band the crosswalk authors.
    """
    if not archetype or stories is None:
        return 0.0, None
    try:
        module = importlib.import_module(f"archetypes.{archetype}_params")
    except ModuleNotFoundError:
        return 0.0, None
    band_of = getattr(module, "wall_height_band_m", None)
    if band_of is None:
        return 0.0, None
    try:
        lo, hi = band_of(float(stories))
    except (KeyError, ValueError):
        return 0.0, None
    return lo, hi


# ---------------------------------------------------------------------------
# THE ROOF: a pitch sampled from the family's own band, and gated on the ridge
# it produces (T-0145).
#
# T-0144 moved footprint, storeys and eave off retyped constants and onto the
# authored bands. Pitch was deliberately left alone, and the ticket said why:
# sampling a pitch without looking at what it does to the RIDGE moves the fault
# one field over. The crosswalk authors both — `roof` carries a rise:run band and
# `ridge_ft` carries the height the ridge is supposed to reach — and the two are
# not independent, because the ridge is what the pitch and the footprint make
# together. So the sampler here is CONSTRAINED: it samples inside the pitch band,
# but where part of that band would put the ridge outside the family's own
# `ridge_ft`, it samples from the part that does not.
#
# WHAT IT WILL NOT DO. It will not leave the pitch band to reach a ridge band, in
# either direction. The pitch band is a claim about the roofs of a building type
# and the ridge band is another; where the archetype's own geometry cannot satisfy
# both — a narrow-fronted outbuilding whose ridge runs across its short axis
# cannot reach a ridge band written for a house's span at ANY pitch the family
# allows — the sampler stays inside the pitch band and the residual is reported by
# `tools/measure_ridge_band.py` rather than hidden by a pitch nobody claims. A
# gate that can be satisfied by disobeying the other band is not a gate.
# ---------------------------------------------------------------------------

def pitch_band_deg(roof: str | None) -> tuple[float, float] | None:
    """The family's authored pitch band in degrees, or None if it authors none.

    Eight of the thirty-five families write a roof line with no pitch in it at all
    ("gable or shed", "gabled composite"). Those return None and keep whatever type
    default the generator holds — which is what `tools/band_notes.py` already makes
    their note say, and the two agree by construction because they read the same
    expression off the same string.
    """
    m = PITCH_RE.search(str(roof or ""))
    if not m:
        return None
    return (math.degrees(math.atan(int(m.group(1)) / 12)),
            math.degrees(math.atan(int(m.group(2)) / 12)))


def ridge_band_m(ridge_ft: str | None) -> tuple[float, float] | None:
    """The family's authored ridge band in metres, or None ('custom' on T3 and M1)."""
    m = RANGE_RE.match(str(ridge_ft or ""))
    if not m:
        return None
    return (float(m.group(1)) * .3048, float(m.group(2)) * .3048)


def eave_band_m(eave_ft: str | None) -> tuple[float, float] | None:
    """The family's authored eave band in metres, or None where it is not numeric.

    The third of the three band readers, and it lives here for the same reason as the
    other two: `wall_height_m` above already parses this column with this expression, and
    a second copy in a measuring tool is how a gate ends up testing a different band from
    the one the sampler drew from (T-0179).
    """
    m = RANGE_RE.match(str(eave_ft or ""))
    if not m:
        return None
    return (float(m.group(1)) * .3048, float(m.group(2)) * .3048)


def ridge_m(eave_m: float, run_m: float, pitch_deg_value: float) -> float:
    """The ridge a pitch reaches over a given run, from the eave it springs from.

    One line, and it is the line every roof builder in `generators/archetypes/`
    computes: the rise is the run times the tangent. What differs between archetypes
    is WHICH horizontal distance the run is — half the span for a gable, the whole
    span for a shed, and which of width and depth the span is — and that belongs to
    the archetype, so it is asked of `tools/ridge_model.py` and passed in here.
    """
    return eave_m + run_m * math.tan(math.radians(pitch_deg_value))


def pitch_deg(family: str, roof: str | None, key: str, default: float,
              eave_m: float | None = None, run_m: float | None = None,
              ridge_ft: str | None = None) -> float:
    """A pitch sampled inside the family's band, constrained by its ridge band.

    `default` is the generator's own type value and is returned unchanged for a
    family whose roof line names no pitch — the sampler adds variety inside a claim
    the specification makes and invents no claim where it makes none.

    The constraint is applied by SHRINKING the sampling interval, not by rejecting
    a sample: the reachable sub-band is computed in closed form from the ridge band
    (the ridge rises monotonically with the pitch over a fixed run, so the sub-band
    is an interval), and the same stable fraction is then taken across whatever
    interval survives. That keeps the sample deterministic and re-derivable without
    a search, which is what `tools/check.sh` needs — it re-derives these records
    byte for byte on a runner with no Blender on it.
    """
    band = pitch_band_deg(roof)
    if band is None:
        return default
    lo, hi = band
    ridge = ridge_band_m(ridge_ft)
    if ridge is not None and eave_m is not None and run_m and run_m > 1e-6:
        r_lo, r_hi = ridge
        # tan is increasing on (0, 90), so the pitches that land the ridge inside
        # the band are themselves an interval, and it is this one.
        def pitch_for(target: float) -> float:
            return math.degrees(math.atan(max(0.0, target - eave_m) / run_m))
        want_lo, want_hi = pitch_for(r_lo), pitch_for(r_hi)
        sub_lo, sub_hi = max(lo, want_lo), min(hi, want_hi)
        if sub_hi - sub_lo > 1e-9:
            lo, hi = sub_lo, sub_hi
        # else: the two bands do not overlap for this instance's own run. The pitch
        # band wins (see the module note above) and the residual is the gate's to
        # report.
    value = round(lo + (hi - lo) * stable_fraction(key, 7), 1)
    # ROUNDING MUST NOT LEAVE THE BAND (T-0142). Pitches are authored to a tenth of a
    # degree, and a family's band edge is a rise:run pair that almost never lands on
    # one: 9:12 is 36.87 deg, so a sample in the top three hundredths of C1, C3, F1 or
    # H2's band rounds UP to 36.9 and the record ships citing a band it sits outside.
    # Found by `tools/measure_family_deal.py` — ten deals in four thousand, which is
    # exactly the rate that never shows up in the handful of records standing. So the
    # rounded value is held inside the band at the same tenth-degree resolution it is
    # written at.
    return min(max(value, math.ceil(band[0] * 10) / 10),
               math.floor(band[1] * 10) / 10)


# ---------------------------------------------------------------------------
# THE OTHER HALF OF THE SAME COUPLING: the EAVE a ridge band can be reached from
# (T-0148).
#
# `pitch_deg` above constrains the pitch by the ridge band, given the eave and the
# run it is handed. That is one of the two free claims, and constraining only one of
# them is why the ridge gate still had a residual on the parcels that DO sample:
# `wall_height_m` draws the eave first and draws it free, and once a low eave is
# drawn there may be no pitch inside the family's band that reaches the family's
# ridge band at all. The gate then reports a roof outside its ridge band and the
# fault reads as a conflict between two committed claims, when what actually
# happened is that the sampler asked the second claim to carry the first one's
# choice.
#
# It is not a conflict. `tools/measure_ridge_reach.py` sweeps every family's
# authored footprint band and asks whether ANY (eave in band, pitch in band) reaches
# the ridge band: for every family the crosswalk authors a pitch band for, at every
# footprint in its band, the answer is yes. The four claims — footprint, eave, pitch,
# ridge — are jointly satisfiable everywhere, so nothing in the specification has to
# give way. What gives way is the sampler's ORDER, and only where it has to.
#
# WHAT THIS DOES, and what it deliberately does not do. The eave is sampled exactly
# as before, from the part of the authored band the archetype can build. Where the
# value drawn cannot reach the ridge band at any pitch the family allows, it is HELD
# at the nearest eave inside its own authored band that can — the same reading
# `eave_floor` and `eave_limits` already take at the two ends of the band, and the
# same discipline `pitch_deg` takes on the pitch: shrink to the part of the band that
# satisfies the other committed claim, never leave the band to satisfy it. A held
# value is still inside the band its note cites, so the note stays true and
# `tools/measure_band_claims.py` keeps passing it. Where no eave in the band can
# reach the ridge band either, nothing is held and the residual is the gate's to
# report, exactly as `pitch_deg` leaves it.
#
# A sample that already reaches its ridge band is returned untouched, to the bit.
# That is what keeps this a repair of the roofs that are wrong rather than a reshuffle
# of every roof that is right.
# ---------------------------------------------------------------------------

def eave_window_for_ridge(run_m: float, pitch_lo_deg: float, pitch_hi_deg: float,
                          ridge_band: tuple[float, float]) -> tuple[float, float]:
    """The eaves from which the ridge band is reachable at some pitch in the band.

    `ridge = eave + run x tan(pitch)` rises with both, so the ridge band is reachable
    from an eave exactly when the steepest allowed pitch clears the band's floor and
    the shallowest does not overshoot its ceiling. Closed form, no search — which is
    what `tools/check.sh` needs, because it re-derives these records byte for byte.
    """
    r_lo, r_hi = ridge_band
    return (r_lo - run_m * math.tan(math.radians(pitch_hi_deg)),
            r_hi - run_m * math.tan(math.radians(pitch_lo_deg)))


def eave_for_ridge(eave_m: float, family: str, eave_ft: str | None, roof: str | None,
                   ridge_ft: str | None, run_m: float | None, default_pitch_deg: float,
                   key: str, floor: float = 0.0, ceiling: float | None = None) -> float:
    """A sampled eave redrawn inside the part of its own band the ridge band can be met from.

    `default_pitch_deg` is the generator's own type value and is what a family whose
    roof line names no pitch actually gets — A4 authors "shed or gable" and no rise:run
    at all, so its ridge is a function of the eave and that default alone. Passing it
    means the hold works for those families too, instead of only for the families that
    happen to author a pitch band.

    A value already inside the window is returned UNTOUCHED, to the bit; only a value
    outside it is redrawn, and it is redrawn by taking the SAME stable fraction across
    the surviving interval that `wall_height_m` took across the whole band. That is the
    shape `pitch_deg` already uses — shrink the interval, do not reject the sample — and
    it matters here for a reason beyond consistency: the nearest EDGE of the window is
    the eave at which exactly one pitch works, so an eave held there leaves `pitch_deg`
    a degenerate interval and it falls back to the whole pitch band. Inside the window,
    both samplers have room.
    """
    ridge = ridge_band_m(ridge_ft)
    if ridge is None or not run_m or run_m <= 1e-6:
        return eave_m
    band = RANGE_RE.match(str(eave_ft or ""))
    if not band:
        return eave_m
    lo, hi = float(band.group(1)) * .3048, float(band.group(2)) * .3048
    lo = max(lo, floor)
    if ceiling is not None:
        hi = min(hi, ceiling)
    if hi < lo:
        return eave_m
    pitch = pitch_band_deg(roof) or (default_pitch_deg, default_pitch_deg)
    want_lo, want_hi = eave_window_for_ridge(run_m, pitch[0], pitch[1], ridge)
    sub_lo, sub_hi = max(lo, want_lo), min(hi, want_hi)
    if sub_hi - sub_lo < 1e-9:
        # No eave in the authored band reaches the ridge band at this run. The eave
        # band wins, same as the pitch band does above, and the gate reports it.
        return eave_m
    if sub_lo - 1e-9 <= eave_m <= sub_hi + 1e-9:
        return eave_m
    return round(sub_lo + (sub_hi - sub_lo) * stable_fraction(key, 8), 3)
