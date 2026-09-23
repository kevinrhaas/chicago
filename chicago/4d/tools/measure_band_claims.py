#!/usr/bin/env python3
"""Is the invention actually bounded by the specification it cites?

ROADMAP K25. Every invented form value on every reconstructed building carries the
same closing sentence — *"Type-level choice within the D3 band in the reconstruction
specification"* — and that sentence is the **entire defence for the invention**: the
building is made up, but it is made up inside what the specification allows. It is a
provenance claim, so where the value is outside the band it cites, the note is not
merely imprecise. It is **wrong about its own source**.

`tools/measure_massing_variety.py` (T-V1) asked a neighbouring question of the
anonymous layer only — is the town a distribution or one building stamped out — and
counted 40 eaves outside their band on the way past. This tool asks K25's question of
**every reconstructed record in the dataset and every form value the crosswalk authors
a machine-readable band for**: footprint, eave, roof pitch, storeys-and-loft, roof
form. Both layers, 249 records.

## The root cause, and it is one line — REPAIRED IN ALL FOUR PARCELS AS OF T-0274

Read the next three paragraphs in the past tense. The fault they describe was taken
out of the platted-block parcel by T-0144 and T-0145, out of the West approaches by
T-0272, out of the South infill by T-0273, and out of the inferred-household parcel —
the one quoted below, and the last of the four — by T-0274 on 2026-08-30. All four now
draw the eave and the pitch from the family's own authored band through
`tools/family_bands.py`, bounded at both ends by limits ASKED of the archetype. The
census below is what remains after that: 5 offenders, none of them an eave or a pitch.

`inferred_form()` in `tools/generate_inferred_households.py` — and the anonymous
generators alongside it — selected every form value from the **archetype**, consulting
the family only for a handful of named special cases:

    wall = 3.42 if door == "wagon" else (2.75 if door == "stable" else 2.05)
    ...
    "roof_pitch_deg": a(18.0 if roof == "shed" else 32.0),

The note attached to that value cites the **family**. So `outbuilding` handed out a
2.05 m wall whether the family band asked for 7-8 ft (D2, a hair under) or 9-18 ft (W4,
out by a third of the band's floor), and every archetype constant landed on a dozen
families at once. That is why the offenders come in bands of identical values rather
than scattered: 6.73 ft appears on D2, A5 and W4 alike because it is 2.05 m, and
2.05 m is what the outbuilding archetype builds.

## What it gates, and what it only reports

**The gate is a ratchet against a committed census**, `tools/band_claims_baseline.json`,
which holds every offending (record, field) pair with its value and its band. The
strict assertion — no value outside the band its note cites — **fails today**, by
design and on purpose: `--strict` runs it and exits non-zero with the numbers. It is
not what `check.sh` runs, because the fault cannot be repaired on the improve runner
(see below) and a permanently red dev gate would block every unrelated parcel behind
it. What `check.sh` runs is the ratchet: a **new** value outside its band, or a
committed offender whose value moved, is a failure. The fault may shrink and may not
grow, and K25(b) shrinks it to zero and deletes the baseline.

## What it measures, today

    1135 values tested against a machine-readable band, 98 outside it,
    on 80 of the 249 records:

    field       tested  outside  near the edge
    eave           249       54             46
    pitch          207       38             38
    levels         181        4              1
    footprint      249        2              0
    roof_type      249        0              0

**Widening a band is not a repair, and the tolerance here is not a policy choice.**
The bands are the specification's, not this project's, and a band widened to admit the
value it was supposed to bound stops being evidence. The only slack allowed is
`EPS_FT` — 1.5 mm, which is the round-trip through the committed metre value and
nothing else, since every dimension in `data/` is stored in metres to the millimetre
and every band edge is a whole foot. Five footprints sat half a millimetre over an
edge at a tighter epsilon and every one of them is an exact 42 ft or 18 ft in the
source; those are not findings and are not counted.

**K25's open question — what to do about the cases within a hair of the edge — is
decided here: they are failures, counted separately and forgiven nowhere.** 46 of the
54 eaves are within a foot and 38 of 38 pitches are within one 1:12 step, and that
nearness is the *diagnosis*, not a defence. `2.78 m` is 37 mm over the top of D3's
8-9 ft band because the frame-dwelling archetype builds 2.78 m walls, not because
anybody measured a cottage; `18.0 deg` is 0.10 of a step under D2's 4:12 floor because
the generator authors whole degrees while the crosswalk authors rise:run. A tolerance
wide enough to forgive either is wide enough to forgive a third of a D3's band, and it
would forgive exactly the fault this parcel exists to name.

**The unspoken-field census was reported and not gated. K33 repaired it and it is now an
assertion.** The same sentence used to be attached to values the crosswalk authors
nothing about — `board_gap_m` on 99 records against a specification that names no board
gap anywhere, `paint` on 227 against 7 families that mention paint at all, and (found by
K33, and missed by the census above because a value with no band is never tested against
one) 42 `roof_pitch_deg` values on six families whose roof line is "gable or shed", a
form with no pitch in it. **623 values in all.** Those notes now say what the value is —
the reconstruction generator's type default — and say in their first four words that the
paragraph above them about the invention being bounded does not hold. The rule is
`tools/band_notes.py`, imported by the five generators that author the note and by this
tool that audits it, because a claim authored in one file and audited in another drifts.

`--gate` therefore carries two assertions with different shapes, and that asymmetry is
deliberate. **The K33 assertion is absolute** — a value may cite a band only where the
family authors one, and there is no baseline and no allowance, because the repair costs
prose and prose is not in the mesh hash. **The K25 assertion is a ratchet** against a
committed census, because that repair moves a dimension and a dimension needs a bake.

## Why (b) cannot follow (a) here

Every offender is on a parcel whose meshes are canonical Blender bakes. Changing a
committed dimension stales the GLB, `validate.py --all` fails a stale GLB, that
validator IS the dev gate, there is no Blender on the improve runner, and
`chicago-4d-bake.yml` bakes from `dev`. The repair cannot pass the gate it must pass
to reach the branch the bake reads. T-V1(b) hit the identical circle and wrote it up;
its three routes are K25(b)'s routes too.

    tools/measure_band_claims.py            the full census
    tools/measure_band_claims.py --gate     the ratchet (check.sh runs this)
    tools/measure_band_claims.py --strict   the assertion K25(b) has to turn green
    tools/measure_band_claims.py --write-baseline
"""

from __future__ import annotations

import argparse
import collections
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import band_notes  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STRUCTURES = ROOT / "data" / "structures"
CROSSWALK = ROOT / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json"
BASELINE = Path(__file__).resolve().parent / "band_claims_baseline.json"

FT = 0.3048
# Five thousandths of a foot — 1.5 mm. Every dimension in data/ is a metre value
# rounded to the millimetre and every band edge is a whole foot, so a value authored
# exactly ON an edge comes back through the unit round-trip up to half a millimetre
# outside it. This absorbs that and nothing else: five records sat 0.4 mm over an edge
# at a tighter epsilon and every one of them is an exact 42 ft or 18 ft in the source.
# It is NOT a tolerance for being outside a band. The sub-1-ft cases stay failures.
EPS_FT = 0.005
EPS_DEG = 0.01
EPS_LEVEL = 1e-6

FOOTPRINT_RE = re.compile(r"^\s*(\d+)x(\d+)\s*-\s*(\d+)x(\d+)")
RANGE_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$")
PITCH_RE = re.compile(r"(\d+):12\s*-\s*(\d+):12")
LEVELS_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:-\s*(\d+(?:\.\d+)?))?")
# The sentence under test. Every reconstructed form value ends with it, and it names
# the family whose band it claims to sit inside. Two wordings are in the dataset —
# "Type-level choice within the D3 band" on the form values, and "sampled
# deterministically inside the A1 family's authored footprint band" on the block
# parcels' footprints — so the family id and the word `band` are matched with the
# words between them left open.
CITES_BAND_RE = re.compile(r"\b([A-Z]\d)\b[^.;]{0,40}?\bband\b")

# Which form fields the crosswalk's key_geometry_parameters authors something for, and
# what it authors. Only the first group is machine-readable; the second is prose the
# crosswalk genuinely speaks (so the citation means something and this tool cannot
# check it); the third is what the crosswalk does not speak to at all.
BANDED_FIELDS = ("footprint", "wall_height_m", "roof_pitch_deg", "levels", "roof_type")
# Which fields the crosswalk speaks to in prose rather than in a testable band, and the
# keyword each is looked for under. Both tables live in `tools/band_notes.py` — the
# module the five generators import to decide whether a value may cite the band at all —
# so the sentence that is authored and the sentence that is audited cannot drift apart.
PROSE_FIELDS = tuple(sorted(band_notes.PROSE_KEYWORDS))


def bands() -> dict[str, dict]:
    """Per family, the bands the crosswalk authors in a form this tool can test."""
    table: dict[str, dict] = {}
    for fam in json.loads(CROSSWALK.read_text(encoding="utf-8"))["families"]:
        geom = fam.get("key_geometry_parameters") or {}
        entry: dict = {"raw": geom, "footprint_ft": None, "eave_ft": None,
                       "pitch_deg": None, "levels": None, "roof": None}
        m = FOOTPRINT_RE.match(str(geom.get("footprint_ft") or ""))
        if m:
            entry["footprint_ft"] = tuple(int(m.group(i)) for i in (1, 2, 3, 4))
        m = RANGE_RE.match(str(geom.get("eave_ft") or ""))
        if m:
            entry["eave_ft"] = (float(m.group(1)), float(m.group(2)))
        roof = str(geom.get("roof") or "")
        entry["roof"] = roof
        m = PITCH_RE.search(roof)
        if m:
            entry["pitch_deg"] = (math.degrees(math.atan(int(m.group(1)) / 12)),
                                  math.degrees(math.atan(int(m.group(2)) / 12)))
        levels = str(geom.get("levels") or "")
        m = LEVELS_RE.match(levels)
        if m:
            lo = float(m.group(1))
            hi = float(m.group(2)) if m.group(2) else lo
            # "1 + loft" authors a storey and a loft over it; a half level is what a
            # loft is worth everywhere else in this dataset, so the ceiling rises by
            # one. A band that already reaches lo + 0.5 needs no help.
            ceiling = hi + 0.5 if "loft" in levels.lower() else hi
            entry["levels"] = (lo, ceiling, levels)
        table[fam["id"]] = entry
    return table


def records() -> list[dict]:
    out = []
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if doc.get("reconstruction", {}).get("family"):
            out.append(doc)
    return out


def cited_family(note: str | None) -> str | None:
    m = CITES_BAND_RE.search(note or "")
    return m.group(1) if m else None


def measure() -> dict:
    table = bands()
    geometry = band_notes.geometry()
    findings: list[dict] = []
    false_citations: list[dict] = []
    unclassified: list[dict] = []
    checked = collections.Counter()
    uncited = collections.Counter()
    prose_silent = collections.Counter()
    prose_total = collections.Counter()
    layers = collections.Counter()
    mismatched_citation = []

    def fail(doc, field, value, band, detail, marginal=False):
        findings.append({
            "id": doc["id"],
            "layer": doc["reconstruction"].get("status", "?"),
            "family": doc["reconstruction"]["family"],
            "field": field,
            "value": value,
            "band": band,
            "detail": detail,
            "marginal": marginal,
        })

    for doc in records():
        fam = doc["reconstruction"]["family"]
        band = table.get(fam)
        layers[doc["reconstruction"].get("status", "?")] += 1
        if band is None:
            mismatched_citation.append((doc["id"], fam, "no such family in the crosswalk"))
            continue
        for phase in doc.get("phases", []):
            foot = phase.get("footprint") or {}
            poly = foot.get("polygon")
            note_fam = cited_family(foot.get("note"))
            if note_fam and note_fam != fam:
                mismatched_citation.append((doc["id"], fam, f"footprint note cites {note_fam}"))
            if poly and band["footprint_ft"]:
                checked["footprint"] += 1
                if not note_fam:
                    uncited["footprint"] += 1
                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                width_ft = (max(xs) - min(xs)) / FT
                depth_ft = (max(ys) - min(ys)) / FT
                lo_w, lo_d, hi_w, hi_d = band["footprint_ft"]
                bad = []
                over = 0.0
                if not (lo_w - EPS_FT <= width_ft <= hi_w + EPS_FT):
                    bad.append(f"{width_ft:.2f} ft wide against {lo_w}-{hi_w}")
                    over = max(over, lo_w - width_ft, width_ft - hi_w)
                if not (lo_d - EPS_FT <= depth_ft <= hi_d + EPS_FT):
                    bad.append(f"{depth_ft:.2f} ft deep against {lo_d}-{hi_d}")
                    over = max(over, lo_d - depth_ft, depth_ft - hi_d)
                if bad:
                    fail(doc, "footprint", f"{width_ft:.2f}x{depth_ft:.2f} ft",
                         f"{lo_w}x{lo_d}-{hi_w}x{hi_d} ft", "; ".join(bad),
                         marginal=over <= 1.0)

            form = phase.get("form") or {}

            wall = form.get("wall_height_m")
            if isinstance(wall, dict) and band["eave_ft"]:
                checked["eave"] += 1
                note_fam = cited_family(wall.get("note"))
                if not note_fam:
                    uncited["eave"] += 1
                elif note_fam != fam:
                    mismatched_citation.append((doc["id"], fam, f"eave note cites {note_fam}"))
                lo, hi = band["eave_ft"]
                value_ft = float(wall["value"]) / FT
                if not (lo - EPS_FT <= value_ft <= hi + EPS_FT):
                    over = max(lo - value_ft, value_ft - hi)
                    fail(doc, "eave", f"{value_ft:.2f} ft ({wall['value']} m)",
                         f"{lo:g}-{hi:g} ft",
                         f"{over:+.2f} ft outside", marginal=over <= 1.0)

            pitch = form.get("roof_pitch_deg")
            if isinstance(pitch, dict) and band["pitch_deg"]:
                checked["pitch"] += 1
                note_fam = cited_family(pitch.get("note"))
                if not note_fam:
                    uncited["pitch"] += 1
                lo, hi = band["pitch_deg"]
                value = float(pitch["value"])
                if not (lo - EPS_DEG <= value <= hi + EPS_DEG):
                    over = max(lo - value, value - hi)
                    # Measured in the band's own units, not in degrees. The crosswalk
                    # authors rise:run and the generator authors whole degrees, so
                    # "how far outside" is only meaningful as a fraction of a 1:12
                    # step — which is also the whole diagnosis for this field.
                    spec = PITCH_RE.search(band["roof"])
                    rise = math.tan(math.radians(value)) * 12
                    lo_r, hi_r = int(spec.group(1)), int(spec.group(2))
                    over_rise = max(lo_r - rise, rise - hi_r)
                    fail(doc, "pitch", f"{value:.1f} deg (= {rise:.2f}:12)",
                         f"{lo:.1f}-{hi:.1f} deg ({spec.group(0)})",
                         f"{over:+.1f} deg / {over_rise:+.2f} of a 1:12 step outside",
                         marginal=over_rise <= 1.0)

            roof_type = form.get("roof_type")
            if isinstance(roof_type, dict) and band["roof"]:
                checked["roof_type"] += 1
                value = str(roof_type["value"]).lower()
                if value and value not in band["roof"].lower():
                    fail(doc, "roof_type", value, band["roof"], "form not offered by the band")

            levels_band = band["levels"]
            storeys = form.get("stories")
            loft = form.get("loft")
            if levels_band and (isinstance(storeys, dict) or isinstance(loft, dict)):
                lo, ceiling, raw = levels_band
                has_loft = bool(loft["value"]) if isinstance(loft, dict) else False
                if isinstance(storeys, dict):
                    checked["levels"] += 1
                    effective = float(storeys["value"]) + (0.5 if has_loft else 0.0)
                    if not (lo - EPS_LEVEL <= effective <= ceiling + EPS_LEVEL):
                        over = max(lo - effective, effective - ceiling)
                        fail(doc, "levels",
                             f"{storeys['value']} storey"
                             + (" + loft" if has_loft else "") + f" = {effective:g}",
                             f"'{raw}' (=> {lo:g}-{ceiling:g})",
                             f"{over:+g} levels outside", marginal=over <= 0.5)
                elif has_loft:
                    # No storey count is authored on this archetype's records, so the
                    # only testable half is whether the band admits a loft at all.
                    checked["levels"] += 1
                    if ceiling < lo + 0.5 - EPS_LEVEL:
                        fail(doc, "levels", "loft = true", f"'{raw}' (=> {lo:g}-{ceiling:g})",
                             "the band authors no loft", marginal=False)

            # K33's assertion, asked of EVERY value that cites a band — the prose fields
            # and the banded ones alike. A banded field whose family authors no band is
            # invisible to the tests above (there is nothing to compare against), which
            # is exactly how 42 roof pitches cited a band on families whose roof line is
            # "gable or shed". Silence is the finding, so it has to be asked separately.
            geom = geometry.get(fam, {})
            for field, value in sorted(form.items()):
                if not isinstance(value, dict) or not cited_family(value.get("note")):
                    continue
                state = band_notes.classify(geom, field)
                if field in PROSE_FIELDS:
                    prose_total[field] += 1
                    if state == band_notes.SILENT:
                        prose_silent[field] += 1
                if state is None:
                    unclassified.append({"id": doc["id"], "family": fam, "field": field})
                elif state == band_notes.SILENT:
                    false_citations.append({"id": doc["id"], "family": fam,
                                            "field": field,
                                            "layer": doc["reconstruction"].get("status", "?")})

    findings.sort(key=lambda f: (f["layer"], f["field"], f["id"]))
    return {
        "records": sum(layers.values()),
        "layers": dict(layers),
        "checked": dict(checked),
        "uncited": dict(uncited),
        "findings": findings,
        "prose_total": dict(prose_total),
        "prose_silent": dict(prose_silent),
        "mismatched_citation": mismatched_citation,
        "false_citations": false_citations,
        "unclassified": unclassified,
    }


def key(f: dict) -> str:
    return f"{f['id']}:{f['field']}"


def census(result: dict, verbose: bool = True) -> None:
    checked = result["checked"]
    findings = result["findings"]
    total_checked = sum(checked.values())
    print(f"   {result['records']} reconstructed records "
          + ", ".join(f"{n} {k}" for k, n in sorted(result["layers"].items())))
    print(f"   {total_checked} value(s) tested against a machine-readable band, "
          f"{len(findings)} outside it")
    print()
    by_field = collections.Counter(f["field"] for f in findings)
    marginal = collections.Counter(f["field"] for f in findings if f["marginal"])
    print("   near = within one unit of the band's OWN edge: 1 ft for a footprint or an")
    print("   eave, one 1:12 step for a pitch, half a level for storeys. Near is not a")
    print("   pass — a note that cites a band it sits outside is wrong either way.")
    print()
    print("   field       tested  outside  of which near the edge")
    for field in ("footprint", "eave", "pitch", "levels", "roof_type"):
        n = checked.get(field, 0)
        if not n:
            continue
        print(f"   {field:<11} {n:>6}  {by_field.get(field, 0):>7}  {marginal.get(field, 0):>22}")
    print()
    by_layer = collections.Counter((f["layer"], f["field"]) for f in findings)
    for (layer, field), n in sorted(by_layer.items()):
        print(f"   {layer:<20} {field:<10} {n:>3}")
    records_hit = len({f["id"] for f in findings})
    print(f"\n   {records_hit} of {result['records']} records carry at least one")

    if verbose:
        print("\n   every finding, as (record, field, value, band):")
        for f in findings:
            print(f"     {f['id']:<44} {f['field']:<10} {f['value']:<26} "
                  f"vs {f['band']:<24} {f['detail']}")

    if result["uncited"]:
        print(f"\n   values tested whose note cites NO band: {result['uncited']}")
    if result["mismatched_citation"]:
        print("\n   notes citing a family that is not the record's own:")
        for row in result["mismatched_citation"]:
            print(f"     {row}")

    print("\n   the second fault (K33): the same sentence on values the crosswalk does")
    print("   not speak to at all. Repaired 2026-08-15 and now ASSERTED, on every field")
    print("   that cites a band rather than only the prose ones — the instrument is a")
    print("   keyword, so a silence it reports is a floor and not an estimate.")
    print("   field            citing the band  of which the family says nothing")
    for field in sorted(result["prose_total"], key=lambda k: -result["prose_silent"].get(k, 0)):
        total = result["prose_total"][field]
        silent = result["prose_silent"].get(field, 0)
        print(f"   {field:<16} {total:>15}  {silent:>32}")
    false_by_field = collections.Counter(f["field"] for f in result["false_citations"])
    if false_by_field:
        print(f"\n   {len(result['false_citations'])} value(s) cite a band their family "
              f"does not author: {dict(false_by_field)}")
    else:
        print("\n   every band citation in the dataset points at something the family "
              "authors.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true",
                    help="ratchet against the committed census; fails on a NEW offender")
    ap.add_argument("--strict", action="store_true",
                    help="assert no value is outside its band (fails today; K25(b)'s target)")
    ap.add_argument("--write-baseline", action="store_true")
    ap.add_argument("--quiet", action="store_true", help="counts only, no per-record list")
    args = ap.parse_args()

    result = measure()
    findings = result["findings"]

    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "$note": ("ROADMAP K25(a). Every form value in this project's reconstructed "
                      "buildings that sits outside the family band its own note cites. "
                      "This file is a RATCHET, not an allowance: tools/check.sh fails on "
                      "any offender that is not here and on any listed offender whose "
                      "value has moved. K25(b) empties it and deletes it. Regenerate "
                      "with tools/measure_band_claims.py --write-baseline, and only ever "
                      "to record a repair."),
            "measured": "2026-08-15",
            "counts": collections.Counter(f["field"] for f in findings),
            "offenders": {key(f): {"family": f["family"], "value": f["value"],
                                   "band": f["band"], "detail": f["detail"],
                                   "marginal": f["marginal"]}
                          for f in findings},
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"   wrote {BASELINE.relative_to(ROOT)}: {len(findings)} offender(s)")
        return 0

    # K33's assertion, and it is absolute in every mode. There is no baseline for it and
    # no allowance: unlike a value outside its band, a value citing a band that does not
    # exist is repaired by rewriting prose, prose is stripped from every mesh input hash
    # in this project, and so the repair costs no bake and nothing can be blocked behind
    # it. A new one is a regression the same day it lands.
    def k33() -> int:
        bad = result["false_citations"]
        unclassified = result["unclassified"]
        if unclassified:
            print(f"\n   UNCLASSIFIED: {len(unclassified)} value(s) cite a band on a field "
                  f"neither tools/band_notes.BANDED_FIELDS nor PROSE_KEYWORDS has heard "
                  f"of, so nothing has decided whether the citation is true. Classify the "
                  f"field there before authoring it.")
            for row in unclassified[:20]:
                print(f"     {row['id']}: {row['field']} ({row['family']})")
        if bad:
            print(f"\n   K33: {len(bad)} value(s) cite the family band on a field the "
                  f"crosswalk does not author for that family. There is no band for the "
                  f"note to be inside; say what the value is instead "
                  f"(tools/band_notes.unbounded_note).")
            for row in bad[:20]:
                print(f"     {row['id']}: {row['field']} ({row['family']})")
            if len(bad) > 20:
                print(f"     ... and {len(bad) - 20} more")
        return 1 if (bad or unclassified) else 0

    if args.strict:
        census(result, verbose=not args.quiet)
        rc = k33()
        if findings:
            print(f"\n   STRICT: {len(findings)} value(s) outside the band their note "
                  f"cites. Every one is a note that is wrong about its own source.")
            return 1
        print("\n   STRICT: every reconstructed value is inside the band it cites.")
        return rc

    if not args.gate:
        census(result, verbose=not args.quiet)
        return 0

    census(result, verbose=False)
    rc = k33()
    if not BASELINE.exists():
        print(f"\n   no committed census at {BASELINE.relative_to(ROOT)}")
        return 1
    committed = json.loads(BASELINE.read_text(encoding="utf-8"))["offenders"]
    current = {key(f): f for f in findings}
    added = sorted(set(current) - set(committed))
    moved = sorted(k for k in set(current) & set(committed)
                   if current[k]["value"] != committed[k]["value"])
    fixed = sorted(set(committed) - set(current))

    if added:
        print(f"\n   NEW: {len(added)} value(s) outside their band that the committed "
              f"census does not hold. A reconstructed value may not be authored outside "
              f"the band its own note cites.")
        for k in added:
            f = current[k]
            print(f"     {k}: {f['value']} vs {f['band']} — {f['detail']}")
    if moved:
        print(f"\n   MOVED: {len(moved)} committed offender(s) changed value without the "
              f"census being updated.")
        for k in moved:
            print(f"     {k}: {committed[k]['value']} -> {current[k]['value']}")
    if fixed:
        print(f"\n   {len(fixed)} committed offender(s) are now inside their band. "
              f"Re-run --write-baseline in the same commit as the repair:")
        for k in fixed:
            print(f"     {k}")
    if added or moved or fixed:
        return 1
    print(f"\n   ratchet holds: {len(findings)} offender(s), exactly the committed census. "
          f"This is not a pass mark — read it. K25(b) is the repair, and it needs a bake.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
