#!/usr/bin/env python3
"""Can a parcel generator build every family it is allowed to deal? (T-0142, T-0172)

WHY THIS EXISTS. A parcel generator does not choose its families: the 665-roof
schedule and the parcel recipes do, and an entry names one. So a family is either
buildable at EVERY size its band lets it be dealt at, or the schedule is holding a card
that kills the run whenever it comes up — and it comes up rarely enough that the
standing records look fine. That is exactly what happened to H2. `blk_randolph_dearborn`'s
second deal asked for a merchant house, the family's authored eave band runs 18-21 ft,
`frame_dwelling` refuses a two-storey wall over 6.2 m because the one attested ceiling in
this dataset is the Green Tree's seven and a half feet, and the sample landed at 6.234 m.
Two H2s were already standing, both under the limit by luck, so nothing in the repo said
the family was broken.

Standing records cannot answer that question — there are two H1s and two H2s in the
whole platted-block parcel. So this deals each family several hundred synthetic
instances through the generator's OWN sampling and form rules, and asks two things of
each:

  1. the archetype the family resolves through will BUILD it — `from_phase` is the same
     call the generator makes before it writes a record; and
  2. every value that cites the family's band is INSIDE that band — the same reading
     `tools/measure_band_claims.py` takes of the records that landed, taken here of the
     records that could.

It builds no geometry and needs no Blender: `from_phase` validates, which is the step
that refuses. Roughly a few seconds for the whole table.

## FOUR PARCELS, NOT ONE (T-0172)

T-0142 built this against `generate_block_infill.py` alone and said so; the other three
anonymous parcels deal the same families through the same archetypes and were never
asked the question. They are here now. What they do NOT share is an interface — each
generator authors its form through a differently-shaped call, and the parcel adapters
below are that difference and nothing else. Each adapter answers three things: which
(family, archetype) pairs the parcel may deal, how it sizes a deal, and how it authors
the form.

Where a parcel authors its footprint in a hand-written recipe rather than sampling
(`west`, `household`), the sweep sizes deals from the family band anyway, because that
is the bound the parcel's OWN footprint note claims — *"a rectangle assigned by the
reconstruction recipe within the {family} family band"*. Sweeping only the sizes the
recipe happens to hold today would re-measure what already stands, which
`tools/measure_band_claims.py` does; the question here is what the recipe may deal.

## WHAT IS GATED, AND WHAT IS ONLY REPORTED

`check.sh` runs `--gate`, which is a **ratchet** against `tools/family_deal_baseline.json`:
a new refusal, or a new off-band family, is a failure; the committed ones are named
there with the reason each stands. The block parcel is green and gated absolutely — no
baseline entry may ever be added for it. The three parcels T-0172 brought in are not,
and the baseline says per family why not; the fault may shrink and may not grow.

    tools/measure_family_deal.py                the report, all four parcels
    tools/measure_family_deal.py --parcel west  one parcel
    tools/measure_family_deal.py --gate         exit 1 on a deal outside the baseline
    tools/measure_family_deal.py --strict       exit 1 on ANY refusal, baseline ignored
    tools/measure_family_deal.py --write-baseline   re-cut the census (shrink only)
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.path.insert(0, str(ROOT / "tools"))

from family_bands import dimensions_m, families, pitch_band_deg  # noqa: E402
# The SAME edge epsilons the landed-record gate reads its bands with, imported rather
# than retyped: a value is either inside its band or not, and two gates disagreeing
# about the last millimetre would be a third opinion nobody asked for.
from measure_band_claims import EPS_DEG, EPS_FT  # noqa: E402
from band_notes import split_notes  # noqa: E402
from roof_form import note_refusal  # noqa: E402
import generate_block_infill as blk  # noqa: E402
import generate_inferred_households as hh  # noqa: E402
import generate_inferred_infill as inf  # noqa: E402
import generate_west_infill as west  # noqa: E402

# How many instances of each family. The failure this exists to catch is a band whose
# TAIL is unbuildable, so the sweep has to be dense enough to reach a tail that is a few
# per cent of the band: 400 deals put about a dozen samples in the top three per cent.
DEALS = 400

BASELINE_PATH = ROOT / "tools" / "family_deal_baseline.json"
DATA = ROOT / "data"

# The band a value cites, and how to read the value out of the form. `levels` is not
# tested here — the crosswalk authors it as a value for every family the block generator
# deals, so `family_bands.storeys` cannot put it outside anything.
FT_M = 0.3048


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def eave_band_m(spec: dict) -> tuple[float, float] | None:
    from family_bands import RANGE_RE
    m = RANGE_RE.match(str(spec.get("eave_ft") or ""))
    return (float(m.group(1)) * FT_M, float(m.group(2)) * FT_M) if m else None


# --------------------------------------------------------------------------- parcels
# One adapter per generator. `pairs()` names the (family, archetype) the parcel may
# deal — the archetype is the parcel's OWN resolution, not the crosswalk's, because
# that is what will be asked to build. `form()` calls the generator exactly as the
# generator calls itself, including the K33 note split and T-0179's refusal note, so a
# fault in either lands here rather than only in the committed records.


class Parcel:
    key = ""
    label = ""

    def pairs(self) -> list[tuple[str, str]]:
        raise NotImplementedError

    def size(self, family: str, spec: dict, i: int) -> tuple[float, float]:
        return dimensions_m(family, spec["band_ft"], f"deal_{family}_{i:04d}")

    def form(self, family: str, spec: dict, i: int, width: float, depth: float) -> dict:
        raise NotImplementedError


class BlockParcel(Parcel):
    key, label = "block", "platted blocks"

    def pairs(self):
        table = families()
        return [(f, (table.get(f) or {}).get("archetype")) for f in sorted(blk.FUNCTIONS)]

    def form(self, family, spec, i, width, depth):
        key = f"deal_{family}_{i:04d}"
        _finish, paint = blk.finish_for(key)
        return blk.form_for(family, spec, key, width, depth, paint)


class WestParcel(Parcel):
    key, label = "west", "West Division approaches"

    def pairs(self):
        return [(f, west.archetype_for(f)) for f in sorted(west.FUNCTIONS)]

    def form(self, family, spec, i, width, depth):
        _finish, paint = west.finish_for(i)
        return west.form_for(family, i, paint, width, depth)


class InfillParcel(Parcel):
    key, label = "infill", "South Division mixed blocks"

    def __init__(self):
        self.bands = load(DATA / "reconstruction" / "1835_building_inventory.json")[
            "family_bands_ft"]

    def pairs(self):
        return [(f, inf.archetype_for(f)) for f in sorted(self.bands)]

    def size(self, family, spec, i):
        # This parcel samples its own footprint, so it is asked its own rule rather
        # than the shared one — the sizes it may deal are the ones it deals itself.
        return inf.dimensions(family, i, self.bands)

    def form(self, family, spec, i, width, depth):
        # `finish_for` is keyed on the record id the generator would write, and its
        # SECOND return is what `form_for` takes — the parameter is named `finish`
        # there and carries the paint. Called the way the generator calls it.
        _finish_key, paint = inf.finish_for(f"{inf.PREFIX}{family.lower()}_{i:03d}")
        return inf.form_for(family, i, paint, width, depth)


class HouseholdParcel(Parcel):
    key, label = "household", "inferred households"

    def __init__(self):
        prog = load(DATA / "reconstruction" / "1835_inferred_household_programme.json")
        # The programme pairs family with archetype by hand, building by building, so
        # the pairs it holds are the parcel's vocabulary — a family here can reach an
        # archetype the crosswalk never names for it (H1 through `log_dwelling`).
        self._pairs = sorted({(b["family"], b["archetype"]) for b in prog["buildings"]})

    def pairs(self):
        return self._pairs

    def form(self, family, spec, i, width, depth):
        note = (f"Type-level choice within the {family} band in the reconstruction "
                f"specification; it is not evidence for this building.")
        archetype = dict(self._pairs).get(family) or spec.get("archetype")
        # Dealt on the same synthetic key every other parcel's adapter deals on, and
        # the generator's own key is the STRUCTURE ID (T-0274) — a string either way,
        # so the sampler sees the shape it sees in production.
        return note_refusal(
            split_notes(hh.inferred_form(archetype, family, note,
                                         f"deal_{family}_{i:04d}", width, depth,
                                         building_documented=False), family, note),
            family, width, depth)


def parcels() -> dict[str, Parcel]:
    return {p.key: p for p in (BlockParcel(), WestParcel(), InfillParcel(),
                               HouseholdParcel())}


# ---------------------------------------------------------------------------- sweep


def sweep(parcel: Parcel, family: str, archetype: str, spec: dict) -> dict:
    """Deal one family `DEALS` times through one parcel; count what will not build.

    A refusal is per DEAL — it depends on the size drawn, which is the whole reason the
    sweep is dense. An off-band value is per CLAIM: three of the four parcels author a
    per-family CONSTANT, so the same claim comes back on all 400 deals and counting the
    deals would report a magnitude the fault does not have. Claims are collapsed by
    (field, value, band) and carry the share of deals that made them, which is 100 per
    cent for a constant and less for anything sampled.
    """
    refused: list[str] = []
    claims: dict[tuple, dict] = {}
    module = importlib.import_module(f"archetypes.{archetype}_params")
    eband = eave_band_m(spec)
    pband = pitch_band_deg(spec.get("roof"))
    eps_m = EPS_FT * FT_M

    def claim(field: str, value, lo: float, hi: float, unit: str) -> None:
        row = claims.setdefault((field, value, round(lo, 3), round(hi, 3)),
                                {"field": field, "value": value, "band": [round(lo, 3),
                                                                          round(hi, 3)],
                                 "unit": unit, "deals": 0})
        row["deals"] += 1

    for i in range(DEALS):
        key = f"deal_{family}_{i:04d}"
        width, depth = parcel.size(family, spec, i)
        form = parcel.form(family, spec, i, width, depth)
        phase = {
            "id": "inferred_1835",
            "footprint": {"polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                          "confidence": "reconstructed"},
            "form": form,
        }
        try:
            module.from_phase(phase)
        except Exception as exc:                                  # noqa: BLE001
            refused.append(f"{key} {width:.2f}x{depth:.2f} m: {exc}")

        def value(attr):
            entry = form.get(attr)
            return entry.get("value") if entry else None

        pitch, eave = value("roof_pitch_deg"), value("wall_height_m")
        if pband and pitch is not None and not (pband[0] - EPS_DEG <= pitch
                                                <= pband[1] + EPS_DEG):
            claim("pitch", pitch, pband[0], pband[1], "deg")
        if eband and eave is not None and not (eband[0] - eps_m <= eave
                                               <= eband[1] + eps_m):
            claim("eave", eave, eband[0], eband[1], "m")
    return {"refused": refused,
            "claims": sorted(claims.values(), key=lambda c: (c["field"], c["value"]))}


def run(only_parcel: str | None, only_family: str | None) -> dict:
    """The whole census: {parcel: {family: {refused, outside, archetype}}}."""
    table = families()
    out: dict[str, dict] = {}
    for key, parcel in parcels().items():
        if only_parcel and key != only_parcel:
            continue
        rows: dict[str, dict] = {}
        for family, archetype in parcel.pairs():
            if only_family and family != only_family:
                continue
            spec = table.get(family)
            if not spec or not spec.get("band_ft") or not archetype:
                rows[family] = {"skipped": "no footprint band in the crosswalk"}
                continue
            result = sweep(parcel, family, archetype, spec)
            result["archetype"] = archetype
            rows[family] = result
        out[key] = rows
    return out


# -------------------------------------------------------------------------- reporting


def claim_id(claim: dict) -> str:
    """The identity a baseline entry is matched on: the claim, not its count."""
    lo, hi = claim["band"]
    return f"{claim['field']} {claim['value']} outside {lo:g}-{hi:g} {claim['unit']}"


def describe(claim: dict) -> str:
    return f"{claim_id(claim)}  ({claim['deals']} of {DEALS} deals)"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 on a refusal, or a claim the baseline does not name")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 on ANY refusal or off-band claim, baseline ignored")
    ap.add_argument("--parcel", choices=sorted(parcels()), help="one parcel")
    ap.add_argument("--only", help="one family id")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    report = run(args.parcel, args.only)
    baseline = load(BASELINE_PATH) if BASELINE_PATH.exists() else {"parcels": {}}
    known = baseline.get("parcels", {})

    print(f"   {DEALS} synthetic deals per family, through each parcel's own sampling "
          f"and form rules")
    refusals = off_band = unnamed = 0
    for pkey, rows in report.items():
        parcel = parcels()[pkey]
        named_here = (known.get(pkey) or {}).get("families") or {}
        print(f"\n   {pkey} — {parcel.label}")
        print(f"   {'family':7s} {'archetype':17s} {'refused':>8s} {'off band':>9s}")
        for family, result in rows.items():
            if result.get("skipped"):
                print(f"   {family:7s} {result['skipped']} — not dealt")
                continue
            n_ref, n_claim = len(result["refused"]), len(result["claims"])
            refusals += n_ref
            off_band += n_claim
            allowed = {c["claim"] for c in (named_here.get(family) or {}).get("claims", [])}
            new_here = [c for c in result["claims"] if claim_id(c) not in allowed]
            unnamed += n_ref + len(new_here)
            flag = ""
            if n_ref:
                flag = "  <- REFUSED"
            elif new_here:
                flag = "  <- UNNAMED"
            elif n_claim:
                flag = "  <- named"
            print(f"   {family:7s} {result['archetype']:17s} {n_ref:8d} {n_claim:9d}"
                  f"{flag}")
            for line in result["refused"][:2]:
                print(f"           {line}")
            for c in result["claims"]:
                mark = " " if claim_id(c) in allowed else "!"
                print(f"          {mark}{describe(c)}")

    if args.write_baseline:
        keep = baseline.setdefault("parcels", {})
        for pkey, rows in report.items():
            entry = keep.setdefault(pkey, {"why": "", "families": {}})
            fams = entry.setdefault("families", {})
            prior = {f: {c["claim"]: c.get("why", "") for c in row.get("claims", [])}
                     for f, row in fams.items()}
            for family, result in rows.items():
                if result.get("skipped") or not result["claims"]:
                    fams.pop(family, None)
                    continue
                fams[family] = {
                    "archetype": result["archetype"],
                    "claims": [{"claim": claim_id(c), "deals": c["deals"],
                                "why": prior.get(family, {}).get(claim_id(c), "")}
                               for c in result["claims"]],
                }
            for family in list(fams):
                if family not in rows or not rows[family].get("claims"):
                    del fams[family]
        # `ensure_ascii=False`, because every `why` in this file is prose a person
        # reads and it is written with em dashes. Escaping them to \\u2014 rewrote
        # all eleven surviving reasons as noise the first time a repair shrank the
        # ratchet (T-0273), which is a diff nobody can review.
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False)
                                 + "\n", encoding="utf-8")
        print(f"\n   baseline written to {BASELINE_PATH.relative_to(ROOT)}")
        return 0

    print()
    if args.strict:
        if refusals or off_band:
            print(f"   --strict: {refusals} refusal(s) and {off_band} off-band claim(s) "
                  f"across four parcels.")
            return 1
        print("   --strict: every family every parcel may deal builds at every size "
              "its own band allows,\n   and every value that cites a band is inside it.")
        return 0
    if unnamed:
        print(f"   {unnamed} refusal(s) or claim(s) the committed baseline does not "
              f"name. A family a parcel\n   may deal and the generator cannot build is "
              f"a run that dies on the day the card comes\n   up; a value outside the "
              f"band its own note cites is wrong about its source. Repair it,\n   or "
              f"name it in tools/family_deal_baseline.json with the reason it stands.")
        return 1 if args.gate else 0
    if off_band:
        print(f"   0 refusals: every archetype builds every size all four parcels may "
              f"deal it.\n   {off_band} off-band claim(s), every one named in "
              f"tools/family_deal_baseline.json with the\n   reason it stands. Nothing "
              f"new, nothing grown.")
        return 0
    print("   every family every parcel may deal builds at every size its own band "
          "allows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
