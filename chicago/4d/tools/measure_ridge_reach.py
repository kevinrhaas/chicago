#!/usr/bin/env python3
"""Are a family's four committed claims satisfiable AT ONCE — and where one roof is
outside its ridge band, which of them is actually disobeyed? (T-0148)

`tools/measure_ridge_band.py` measures a ROOF: the ridge one record's own eave, footprint
and pitch make, against the band its family authors. It banked 104 roofs outside their
band and its own note read the residual as structural — "for several families no pitch
inside the authored pitch band reaches the authored ridge band at the footprint the family
authors". That sentence is true and it is the wrong conclusion, because it holds the eave
fixed at whatever the record happens to carry. The eave is not fixed. It is the second of
two values the crosswalk authors as a BAND and the samplers draw from, and a ridge band is
reachable or not from a (footprint, eave) PAIR.

So this asks the question one level up, of the SPECIFICATION rather than of a record:

  1. THE FAMILY SWEEP, which is the gate. For every family that authors a footprint band,
     an eave band and a ridge band, at every footprint in that band and every roof form
     its roof line names: is there ANY eave inside the eave band and ANY pitch inside the
     pitch band that lands the ridge inside the ridge band? Today the answer is yes at
     every footprint of every family, and the gate holds it there — so if the crosswalk is
     ever edited into a family whose own claims cannot all be met, that shows up here as a
     specification fault rather than four runs later as a roof nobody can build.

     Closed form, no search: `ridge = eave + run x tan(pitch)` rises with both, so the
     reachable eaves are the interval `family_bands.eave_window_for_ridge` computes and the
     question is whether it meets the authored eave band.

  2. THE SHED OFFER, which is the sweep's own residual made into a gate (T-0179). Nine
     families are offered a SHED by their roof line and three of them — C1, F1, W5 —
     cannot reach their own ridge band as one, because a shed's plane climbs the WHOLE
     span where a gable climbs half and the `ridge_ft` column was written for the gable.
     The sweep printed some as NOTE lines and nothing joined them to what the parcels
     deal, so the day
     a parcel took a permission the crosswalk plainly gives, the roof would have been
     built outside its own band. `tools/roof_form.py` now holds the deal in ONE place —
     it used to be the same literal in five parcels, and the five had already drifted —
     and this section is the join:

       * a family this town builds as a SHED whose shed the sweep cannot reach: FAIL.
       * a family offered a shed and built as a gable: its refusal must be recorded on
         every committed record of that family, in the note a visitor opens. A refusal
         that lives only in a Python tuple is one nobody outside the repo can read.
       * the open-sided table against the crosswalk's own words, the held-back parcel
         against its one named family, and the five generators against a retyped shed
         set — three ratchets, so the single home stays the single home.

  3. THE RECORD REPORT. For each roof in `tools/ridge_band_baseline.json`, which claim is
     disobeyed — stated, because the answer differs by parcel and the repairs have
     different owners:

       eave-outside-band   the record's eave is not in the band its own note cites. A
                           retyped constant from before the samplers existed; the ridge is
                           downstream of it. Owned by T-0172.
       eave-uncoupled      the eave IS in band, and no pitch in the family band reaches the
                           ridge band from it — but another eave in the same band would.
                           The sampler drew the eave free of the ridge band. Repaired for
                           the two parcels that sample by `family_bands.eave_for_ridge`.
       no-pitch-band       the family's roof line names no rise:run at all, so the pitch is
                           the generator's own type default and the specification makes no
                           claim this could be measured against.
       unreachable         no (eave in band, pitch in band) reaches it at this footprint —
                           a genuine conflict between the family's own claims. None today.

    python3 tools/measure_ridge_reach.py              the sweep, the report, and the gate
    python3 tools/measure_ridge_reach.py --quiet      the gate alone
    python3 tools/measure_ridge_reach.py --self-test  break each shed assertion in memory
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import family_bands  # noqa: E402
import ridge_model  # noqa: E402
import roof_form  # noqa: E402

FT = 0.3048
BASELINE = ROOT / "tools" / "ridge_band_baseline.json"
STRUCTURES = ROOT / "data" / "structures"
eave_band_m = family_bands.eave_band_m
roof_forms = roof_form.offered_forms

# The five parcels that deal a family a roof form, and the shape of the literal that
# used to decide it inside each of them. `roof_form.py` is the one home now; a parcel
# that grows its own copy back fails the gate rather than drifting for four months.
PARCEL_SOURCES = ("generate_north_infill.py", "generate_block_infill.py",
                  "generate_west_infill.py", "generate_inferred_infill.py",
                  "generate_inferred_households.py")
RETYPED_RE = re.compile(r"""["']shed["']\s+if\s+family\s+in""")


def reachable(run_m: float, pitch: tuple[float, float], ridge: tuple[float, float],
              eave: tuple[float, float]) -> bool:
    lo, hi = family_bands.eave_window_for_ridge(run_m, pitch[0], pitch[1], ridge)
    return min(hi, eave[1]) - max(lo, eave[0]) >= -1e-9


def sweep() -> list[dict]:
    """Per family and roof form, the footprints from which the ridge band is unreachable.

    The grid, the run and the reach test are `roof_form`'s, not a second copy: the module
    that DECIDES which form a family gets has to answer this question anyway, and a gate
    that computes reachability its own way is a gate measuring a different question from
    the one the generators answer (T-0179). What stays here is the READING — this gate
    tests the four claims the crosswalk authors, so a family with no pitch band is
    reported and not swept, because the specification claims nothing testable about its
    pitch. The shed section below takes the other reading, against the generator's own
    default, and says so.
    """
    out = []
    for fid, spec in family_bands.families().items():
        band = spec.get("band_ft")
        ridge = family_bands.ridge_band_m(spec.get("ridge_ft"))
        eave = eave_band_m(spec.get("eave_ft"))
        pitch = family_bands.pitch_band_deg(spec.get("roof"))
        if band is None or ridge is None or eave is None:
            continue
        if pitch is None:
            out.append({"family": fid, "form": None, "state": "no-pitch-band",
                        "tested": 0, "unreachable": 0})
            continue
        for form in roof_forms(fid):
            s = roof_form.sweep(fid, form)
            if s is None:
                continue
            out.append({"family": fid, "form": form, "state": "swept",
                        "tested": s["tested"], "unreachable": s["unreachable"],
                        "worst": s["worst"], "ridge_ft": spec.get("ridge_ft"),
                        "archetype": spec.get("archetype")})
    return out


# ---------------------------------------------------------------- THE SHED OFFER (T-0179)

def shed_offer() -> dict:
    """What the crosswalk offers as a shed, what this town deals, and whether they agree."""
    fams = family_bands.families()
    refusals = roof_form.refusals()
    rows = []
    for fid in sorted(fams):
        if "shed" not in roof_forms(fid):
            continue
        dealt = roof_form.roof_kind(fid)[0]
        s = roof_form.sweep(fid, "shed")
        if s is None:
            continue
        rows.append({"family": fid, "dealt": dealt, "unreachable": s["unreachable"],
                     "tested": s["tested"], "worst": s["worst"],
                     "open_sides": s["open_sides"], "ridge_ft": s["ridge_ft"],
                     "reason": (refusals.get(fid) or {}).get("reason")})

    # A family this town builds as a shed whose shed its own ridge band cannot carry.
    dealt_unbuildable = [r for r in rows if r["dealt"] == "shed" and r["unreachable"]]

    # The open-sided table against the crosswalk's own words, in both directions.
    open_drift = [f for f in fams
                  if roof_form.entry_says_open(f) != bool(roof_form.open_sides_for(f))]

    # The refusal has to reach the records. Every committed record of a family refused
    # BY THE RIDGE BAND carries the sentence its generator writes, or the refusal exists
    # only in Python and the card a visitor opens still says nothing about it.
    #
    # Asked only of INVENTED roofs, and that is the point rather than a softening: this
    # sentence defends an invention — it says which other form the typology offered and
    # why this town did not take it. A roof somebody has evidence for is not choosing
    # between the typology's forms at all, and writing the refusal onto its note would be
    # the false-provenance fault K33 spent a parcel undoing.
    refused = {f for f, e in refusals.items() if e["reason"] == "ridge_band"}
    unrecorded = []
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        fam = (doc.get("reconstruction") or {}).get("family")
        if fam not in refused:
            continue
        for phase in doc.get("phases", []):
            claim = (phase.get("form") or {}).get("roof_type") or {}
            if claim.get("confidence") != "reconstructed":
                continue
            if "THE OTHER FORM ON OFFER IS REFUSED" not in (claim.get("note") or ""):
                unrecorded.append((doc["id"], fam))

    retyped = [name for name in PARCEL_SOURCES
               if RETYPED_RE.search((ROOT / "tools" / name).read_text(encoding="utf-8"))]

    return {"rows": rows, "dealt_unbuildable": dealt_unbuildable,
            "open_drift": open_drift, "unrecorded": unrecorded, "retyped": retyped,
            "held": dict(roof_form.AWAITING_BAKE), "refused": sorted(refused)}


# The parcels held back from the shared rule, banked by name. It went to EMPTY on
# 2026-08-28, when T-0212 re-baked `recon_1835_south_a5_044` as the shed its family gets
# everywhere else and the last entry came out of `roof_form.AWAITING_BAKE`. It may shrink
# and it may not grow, so at `{}` every parcel now reads the shared rule and any parcel
# that opts a family out fails here. See `roof_form.AWAITING_BAKE` and T-0212.
HELD_BASELINE: dict[tuple[str, str], str] = {}


def report_shed_offer(offer: dict) -> list[str]:
    """The section a reader sees, and the failures it returns for the exit code."""
    fails = []
    print(f"\n   the shed offer — {len(offer['rows'])} family(ies) whose roof line names a "
          f"SHED, against what this town deals them:")
    print("     family  dealt   unreachable as a shed   why not a shed")
    for r in offer["rows"]:
        why = {"ridge_band": "its own ridge band cannot carry one",
               "choice": "buildable; this town builds the gable"}.get(r["reason"], "-")
        axis = " (open-sided, so it falls across the short span)" if r["open_sides"] else ""
        print(f"     {r['family']:6}  {r['dealt']:6}  {r['unreachable']:4} of "
              f"{r['tested']:<4} ridge {r['ridge_ft']:>6} ft   {why}{axis}")

    for r in offer["dealt_unbuildable"]:
        fails.append(f"FAIL {r['family']} is dealt a SHED and {r['unreachable']} of "
                     f"{r['tested']} footprints in its own band cannot reach ridge "
                     f"{r['ridge_ft']} ft as one (first at "
                     f"{r['worst'][0]}x{r['worst'][1]} ft) — roof_form.SHED_FAMILIES "
                     f"claims a form the specification cannot carry")
    for fam in offer["open_drift"]:
        fails.append(f"FAIL {fam}: the crosswalk entry and roof_form.OPEN_SIDED_FAMILIES "
                     f"disagree about whether this family is built open, and that decides "
                     f"which span its shed climbs")
    for sid, fam in offer["unrecorded"]:
        fails.append(f"FAIL {sid} ({fam}): its family's shed is refused by the ridge band "
                     f"and the record does not say so — the refusal has to reach the card")
    for name in offer["retyped"]:
        fails.append(f"FAIL tools/{name} has grown its own copy of the shed set; the rule "
                     f"lives in tools/roof_form.py and nowhere else")
    grown = {k: v for k, v in offer["held"].items() if HELD_BASELINE.get(k) != v}
    if grown:
        fails.append(f"FAIL roof_form.AWAITING_BAKE has grown by {grown}; a parcel may be "
                     f"held back from the shared rule only by the one entry banked in "
                     f"HELD_BASELINE, and that one may shrink and may not grow")
    if offer["held"]:
        for (parcel, fam), form in sorted(offer["held"].items()):
            print(f"     held: {parcel} still deals {fam} a {form}, awaiting a bake (T-0212)")
    print(f"     the refusal is recorded on every committed record of "
          f"{', '.join(offer['refused'])}")
    return fails


def self_test() -> int:
    """Break each of the shed-offer assertions in memory, against the real tree.

    A gate nobody has watched fail is a gate nobody knows fires. Each case below is the
    real repository state with exactly one thing wrong with it, and the assertion for
    that thing must go red while the others stay as they are.
    """
    clean = shed_offer()
    if not clean["rows"] or not clean["refused"]:
        print("SELF-TEST FAIL: nothing measured, so no assertion can be exercised")
        return 1
    base = len(report_shed_offer_quiet(clean))
    cases = []

    c1 = copy.deepcopy(clean)
    c1["dealt_unbuildable"] = [r for r in c1["rows"] if r["family"] == "F1"]
    cases.append(("a family dealt a shed its own ridge band cannot carry", c1))

    c2 = copy.deepcopy(clean)
    c2["open_drift"] = ["F4"]
    cases.append(("the open-sided table drifting from the crosswalk entry", c2))

    c3 = copy.deepcopy(clean)
    c3["unrecorded"] = [("recon_1835_north_f1_022", "F1")]
    cases.append(("a refused family's record that does not carry the refusal", c3))

    c4 = copy.deepcopy(clean)
    c4["retyped"] = ["generate_west_infill.py"]
    cases.append(("a parcel that grows its own copy of the shed set", c4))

    c5 = copy.deepcopy(clean)
    c5["held"] = dict(c5["held"])
    c5["held"][("generate_west_infill.py", "D2")] = "gable"
    cases.append(("a second parcel opting a second family out of the rule", c5))

    ok = True
    for label, state in cases:
        fired = len(report_shed_offer_quiet(state)) > base
        print(f"  {'fires' if fired else 'SILENT'}  {label}")
        ok = ok and fired

    # The two scans the assertions rest on, exercised directly: each has to be able to
    # say yes AND no, or a green gate means only that the scan found nothing.
    checks = [
        ("the retyped-set scan sees the literal it is looking for",
         bool(RETYPED_RE.search('roof = "shed" if family in ("D2", "A3")'))),
        ("...and does not see the shared call that replaced it",
         not RETYPED_RE.search("roof = roof_kind(family)[0]")),
        ("no parcel contains the literal today",
         not [n for n in PARCEL_SOURCES
              if RETYPED_RE.search((ROOT / "tools" / n).read_text(encoding="utf-8"))]),
        ("the open-side scan reads F4's entry as open",
         roof_form.entry_says_open("F4")),
        ("...and W5's 'open work bay' as not an open side",
         not roof_form.entry_says_open("W5")),
        ("a refused family's note is generated, not typed: the sentence carries its "
         "own measured count",
         "231 of" in (roof_form.refusal_note("C1", 5.49, 8.53) or "")),
        ("a family whose shed IS reachable gets no refusal sentence",
         roof_form.refusal_note("F4", 8.0, 15.0) is None),
    ]
    for label, passed in checks:
        print(f"  {'ok   ' if passed else 'FAIL '}  {label}")
        ok = ok and passed

    print("\nSELF-TEST PASS" if ok else "\nSELF-TEST FAIL")
    return 0 if ok else 1


def report_shed_offer_quiet(offer: dict) -> list[str]:
    """`report_shed_offer` without the printing, for the self-test."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return report_shed_offer(offer)


def record_report() -> list[dict]:
    """Each banked offender, and which of the family's claims its roof actually disobeys."""
    if not BASELINE.exists():
        return []
    banked = json.loads(BASELINE.read_text(encoding="utf-8")).get("offenders", {})
    fams = family_bands.families()
    out = []
    for path in sorted((ROOT / "data" / "structures").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc["id"] not in banked:
            continue
        spec = fams.get(doc.get("reconstruction", {}).get("family") or "")
        if spec is None:
            continue
        ridge = family_bands.ridge_band_m(spec.get("ridge_ft"))
        eave_band = eave_band_m(spec.get("eave_ft"))
        pitch = family_bands.pitch_band_deg(spec.get("roof"))
        for phase in doc.get("phases", []):
            poly = (phase.get("footprint") or {}).get("polygon")
            form = {k: v.get("value") for k, v in (phase.get("form") or {}).items()}
            if not poly or "roof_pitch_deg" not in form:
                continue
            width = max(p[0] for p in poly) - min(p[0] for p in poly)
            depth = max(p[1] for p in poly) - min(p[1] for p in poly)
            run = ridge_model.ridge_run_m(doc.get("archetype", ""),
                                          str(form.get("roof_type") or "gable"),
                                          width, depth, form.get("gable_front"),
                                          tuple(form.get("open_sides") or ()))
            if run is None or ridge is None or eave_band is None:
                continue
            eave = float(form.get("wall_height_m") or 0.0)
            in_band = eave_band[0] - 1e-9 <= eave <= eave_band[1] + 1e-9
            if pitch is None:
                state = "no-pitch-band"
            elif not in_band:
                state = "eave-outside-band"
            elif reachable(run, pitch, ridge, eave_band):
                state = "eave-uncoupled"
            else:
                state = "unreachable"
            tool, samples = parcel(doc["id"])
            out.append({"id": doc["id"], "family": spec_family(fams, doc),
                        "state": state, "eave_ft": round(eave / FT, 2),
                        "band": spec.get("eave_ft"), "parcel": tool,
                        "samples": samples})
    return out


def spec_family(fams: dict, doc: dict) -> str:
    return doc.get("reconstruction", {}).get("family") or "?"


# WHICH PARCEL A RECORD CAME OUT OF, because the answer to "which claim gives way" is
# the parcel's and not the family's. Two of the five anonymous parcels draw their eave
# and pitch from the family bands; the other three still carry the constants T-0144 and
# T-0145 took out of the North one, and T-0172 owns moving them.
PARCELS = [
    ("recon_1835_north_", "generate_north_infill.py", True),
    ("recon_1835_blk_", "generate_block_infill.py", True),
    ("recon_1835_south_", "generate_inferred_infill.py", False),
    ("recon_1835_west_", "generate_west_infill.py", False),
    ("inf_", "generate_inferred_households.py", False),
]


def parcel(structure_id: str) -> tuple[str, bool]:
    for prefix, tool, samples in PARCELS:
        if structure_id.startswith(prefix):
            return tool, samples
    return "?", False


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    quiet = "--quiet" in sys.argv
    rows = sweep()
    swept = [r for r in rows if r["state"] == "swept"]
    unpitched = [r for r in rows if r["state"] == "no-pitch-band"]

    # A family may name more than one roof form — C1 is "front gable or shed". The
    # claims are unsatisfiable only if NO form it names works at a given footprint;
    # a form that cannot reach the band while another can is reported and not failed,
    # because the specification still describes a buildable roof there.
    by_family: dict[str, list[dict]] = {}
    for r in swept:
        by_family.setdefault(r["family"], []).append(r)
    conflicts = [f for f, rs in by_family.items() if all(r["unreachable"] for r in rs)]
    narrowed = [r for r in swept if r["unreachable"] and r["family"] not in conflicts]

    print(f"   {len(swept)} family/roof-form combination(s) swept across the whole authored "
          f"footprint band; {len(conflicts)} family(ies) with no reachable form")
    if unpitched:
        print(f"   {len(unpitched)} family(ies) author no pitch band, so the ridge follows the "
              f"generator's own type default and the specification claims nothing testable: "
              f"{', '.join(sorted(r['family'] for r in unpitched))}")
    for n in narrowed:
        print(f"   NOTE {n['family']} as a {n['form']}: {n['unreachable']} of {n['tested']} "
              f"footprints cannot reach ridge {n['ridge_ft']} ft, so the family's other roof "
              f"form is the only one its own bands describe (first at "
              f"{n['worst'][0]}x{n['worst'][1]} ft)")

    shed_fails = report_shed_offer(shed_offer())

    if not quiet:
        report = record_report()
        by_state: dict[str, list[dict]] = {}
        for r in report:
            by_state.setdefault(r["state"], []).append(r)
        if report:
            print(f"\n   the {len(report)} banked roof(s), by the claim each one disobeys:")
        for state in ("unreachable", "eave-outside-band", "eave-uncoupled", "no-pitch-band"):
            rows_ = by_state.get(state) or []
            if not rows_:
                continue
            print(f"     {state:18} {len(rows_):3}  {', '.join(sorted({r['family'] for r in rows_}))}")
        sampled = [r for r in report if r["samples"]]
        print(f"\n   by parcel — the two that draw eave and pitch from the family bands "
              f"carry {len(sampled)} of them:")
        for tool in sorted({r["parcel"] for r in report}):
            rows_ = [r for r in report if r["parcel"] == tool]
            print(f"     {tool:34} {len(rows_):3}  "
                  f"{'samples its bands' if rows_[0]['samples'] else 'retyped constants (T-0172)'}")

    for f in conflicts:
        rs = by_family[f]
        print(f"   FAIL {f} ({rs[0]['archetype']}): no roof form it names reaches ridge "
              f"{rs[0]['ridge_ft']} ft at every footprint in its own band — "
              f"{', '.join(r['form'] for r in rs)}")
    for line in shed_fails:
        print(f"   {line}")
    return 1 if conflicts or shed_fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
