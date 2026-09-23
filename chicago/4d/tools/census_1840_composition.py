#!/usr/bin/env python3
"""T-0507: what a Chicago household looked like in 1840, in counts and nothing else.

    python3 tools/census_1840_composition.py --build
    python3 tools/census_1840_composition.py --check
    python3 tools/census_1840_composition.py --self-test

WHY THIS EXISTS. The retired reconstructed-household programme
(`data/reconstruction/1835_inferred_household_programme.json`) was calibrated on five
in-dataset figures, because — as STATUS.md said at the time — "no period trade table
for a comparable western town exists in `data/sources/`". One does now, and it is not
a comparable town: it is THIS town, counted by the United States five years after the
scene. 964 households, every one of them a column of tally marks in thirteen male and
thirteen female age bands, with the industry columns beside them. That is a
composition model for a frontier lake port, and this file is the arithmetic of it.

WHAT IT IS NOT, and the line is the ticket's own. A count is not a person. Nothing
here mints, names, ages or houses anybody: the output carries no name, no serial
attached to a 1835 identity and no household record, and `--self-test` refuses the
build if a name ever reaches it. 1840 Chicago had roughly doubled since 1 July 1835,
so every figure below is a SHAPE that 1835 may be tested against, never a population
it may be filled from.

WHAT IT READS, and why that file and not the other one. The IPUMS USA extract itself
(`chicago/reference/ipums/H_1840_chicago.csv`) is not in git: IPUMS Conditions of Use
forbid redistribution, and the directory's README records the owner's decision to
publish it to the Internet Archive instead. But a copy of the same 964 rows, with
eleven reading columns added by the T-0504 name work, IS committed at
`chicago/reference/census1840/validation/H_1840_chicago_with_names_partial.csv`, and
on 2026-09-04 all 964 x 134 IPUMS cells of the two were compared and found identical.
So this tool reads the committed copy, re-derives inside `check.sh` with no network
and no restricted file, and records the identity of the original it stands for.

The band labels are NOT authored here either. They are read out of T-0504's own
`column_map` in `data/research/census_1840/serial_crosswalk.json`, which is the
committed statement of which IPUMS variable is which column of the 1840 schedule. If
that mapping is ever corrected, this file moves with it.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import pathlib
import statistics

ROOT = pathlib.Path(__file__).resolve().parents[1]
REFERENCE = ROOT.parent / "reference"
EXTRACT = REFERENCE / "census1840" / "validation" / "H_1840_chicago_with_names_partial.csv"
CROSSWALK = ROOT / "data" / "research" / "census_1840" / "serial_crosswalk.json"
TOWN_CENSUS = ROOT / "data" / "town_census.json"
OUT = ROOT / "data" / "research" / "census_1840" / "composition_1840.json"

# The restricted original this stands for. Fetched 2026-09-04 from the Internet Archive
# item named in chicago/reference/ipums/ipums-usa.yaml, compared cell by cell against the
# committed copy above (964 rows x 134 IPUMS columns, zero differences) and then deleted.
# Recorded so a later reader can re-fetch the same bytes and repeat that comparison; the
# bytes themselves are not redistributed here.
IPUMS_ORIGINAL = {
    "file": "H_1840_chicago.csv",
    "bytes": 279062,
    "sha256": "e37d9761b0d0cab183c0aef61e32477edbf7aabd2c190184c2120779ae56d240",
    "fetched": "2026-09-04",
    "url": "https://archive.org/download/chicago1835-ipums-usa-1790-1840-household-extracts/H_1840_chicago.csv",
    "compared_against_the_committed_copy": {
        "rows": 964,
        "ipums_columns": 134,
        "cell_differences": 0,
    },
}

# The 1830 county total, quoted rather than committed for the same licence reason.
# IPUMS NHGIS ds5 (1830 county population) prints FORTY-NINE Illinois counties and
# Peoria is not among them, though Peoria County had existed since 1825. The district
# the Chicago settlement was enumerated in is headed, in the enumerator's own hand,
# "Peoria & Putnam Counties & Territory attached" (source
# census_1830_peoria_county_chicago_precinct), and its published total stands in NHGIS
# under Putnam. Whether NHGIS merged the two or the return itself was credited to
# Putnam is NOT settled here and must not be asserted from this file.
NHGIS_1830 = {
    "file": "nhgis0001_ds5_1830_county.csv",
    "bytes": 4013,
    "sha256": "0e17819c66c7685e53e0b7f9a0a0e54aeb2d78e8eea23da80202af67e501c7af",
    "fetched": "2026-09-04",
    "url": "https://archive.org/download/chicago1835-ipums-nhgis-1830-illinois-counties/nhgis0001_ds5_1830_county.csv",
    "illinois_counties_printed": 49,
    "illinois_total": 157445,
    "peoria_county_has_a_row": False,
    "putnam_county_total": 1310,
}

# The 1840 industry columns, in the order the schedule prints them. The label is the
# schedule's own wording; the gloss says what the column counts and what it does not.
INDUSTRY = (
    ("nindagr", "Agriculture"),
    ("nindcom", "Commerce"),
    ("nindmfg", "Manufactures and trades"),
    ("nindocn", "Navigation of the ocean"),
    ("nindriv", "Navigation of canals, lakes and rivers"),
    ("nindeng", "Learned professions and engineers"),
    ("nindmin", "Mining"),
)

# Columns the 1840 schedule has and this extract carries as zero in every one of its 964
# rows. Zero in 964 of 964 is not a count of none — it is a column that was not coded into
# the extract — and the difference matters enough to be a named section of the output
# rather than a silently absent one.
UNCARRIED = (
    ("nforeign", "Foreigners not naturalised"),
    ("nwforeign", "Foreigners not naturalised, white"),
    ("nlit", "White persons over 20 who cannot read and write"),
    ("nslave", "Slaves"),
    ("nothfree", "Free coloured persons, other"),
)

# Free-coloured age bands. The 1840 schedule counts these in six bands, not thirteen, and
# the variable names are shared across census years, so only the ones this extract
# actually uses are named. The band wording is the schedule's.
COLOURED_BANDS = (
    ("nbmlt10", "free coloured males under 10"),
    ("nbm10", "free coloured males 10 under 24"),
    ("nbm24", "free coloured males 24 under 36"),
    ("nbm36", "free coloured males 36 under 55"),
    ("nbm55", "free coloured males 55 under 100"),
    ("nbm100", "free coloured males 100 and over"),
    ("nbflt10", "free coloured females under 10"),
    ("nbf10", "free coloured females 10 under 24"),
    ("nbf24", "free coloured females 24 under 36"),
    ("nbf36", "free coloured females 36 under 55"),
    ("nbf55", "free coloured females 55 under 100"),
    ("nbf100", "free coloured females 100 and over"),
)

# Bands whose lower edge is 20 or more, for the adult sex ratio. Read off the column_map's
# own wording rather than hard-coded, via ADULT_FROM below.
ADULT_FROM = 20


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rounded(x: float, places: int = 4) -> float:
    """One rounding rule, so --check compares bytes and not floating point."""
    return round(x + 0.0, places)


def share(n: int, of: int) -> float | None:
    return rounded(n / of) if of else None


def read_extract() -> list[dict]:
    with EXTRACT.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 964:
        raise SystemExit(f"   REFUSED: {EXTRACT.name} holds {len(rows)} rows, not the 964 "
                         f"households the extract is")
    return rows


def column_map() -> list[dict]:
    doc = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    cmap = doc["column_map"]
    if len(cmap) != 26:
        raise SystemExit(f"   REFUSED: T-0504's column_map holds {len(cmap)} bands, not 26")
    return cmap


def band_low_edge(band: str) -> int:
    """`free white males 20 under 30` -> 20; `... Under 5` -> 0; `... 100 and over` -> 100."""
    words = band.split()
    for i, w in enumerate(words):
        if w.isdigit():
            return 0 if i and words[i - 1].lower() == "under" else int(w)
    return 0


def total(rows: list[dict], col: str) -> int:
    return sum(int(r[col]) for r in rows)


def percentiles(sizes: list[int]) -> dict:
    """Nearest-rank percentiles on the sorted sizes. Integer in, integer out: a household
    of 4.7 people is not a thing, and interpolating one would invent a household."""
    s = sorted(sizes)
    out = {}
    for p in (10, 25, 50, 75, 90, 95, 99):
        rank = max(1, -(-p * len(s) // 100))
        out[f"p{p}"] = s[rank - 1]
    return out


def build() -> dict:
    rows = read_extract()
    cmap = column_map()
    sizes = [int(r["numperhh"]) for r in rows]
    households = len(rows)
    persons = sum(sizes)

    if persons != total(rows, "ntotal"):
        raise SystemExit("   REFUSED: numperhh and ntotal disagree on the person total")

    males, females = total(rows, "nmale"), total(rows, "nfemale")
    children = total(rows, "nchild")

    bands = []
    for entry in cmap:
        col, band = entry["ipums_variable"], entry["band"]
        n = total(rows, col)
        bands.append({
            "column": entry["column"],
            "band": band,
            "ipums_variable": col,
            "sex": "male" if " males " in band or band.endswith(" males") else "female",
            "low_edge": band_low_edge(band),
            "persons": n,
            "households_with_at_least_one": sum(1 for r in rows if int(r[col])),
        })
    free_white = sum(b["persons"] for b in bands)
    for b in bands:
        b["share_of_free_white"] = share(b["persons"], free_white)

    coloured = []
    for col, band in COLOURED_BANDS:
        n = total(rows, col)
        coloured.append({"band": band, "ipums_variable": col, "persons": n})
    free_coloured = sum(c["persons"] for c in coloured)

    adult_m = sum(b["persons"] for b in bands
                  if b["sex"] == "male" and b["low_edge"] >= ADULT_FROM)
    adult_f = sum(b["persons"] for b in bands
                  if b["sex"] == "female" and b["low_edge"] >= ADULT_FROM)

    industry = []
    for col, label in INDUSTRY:
        industry.append({"column": label, "ipums_variable": col, "persons": total(rows, col)})
    employed = sum(i["persons"] for i in industry)
    for i in industry:
        i["share_of_employed"] = share(i["persons"], employed)

    uncarried = []
    for col, label in UNCARRIED:
        values = {r[col] for r in rows}
        uncarried.append({
            "column": label,
            "ipums_variable": col,
            "distinct_values_in_964_rows": sorted(values),
            "read_as": "not carried by this extract",
        })

    histogram = collections.Counter(sizes)
    town = json.loads(TOWN_CENSUS.read_text(encoding="utf-8"))
    town_people = town["people"]["town_total"]
    town_dwellings = town["people"]["town_total_dwellings"]
    citypop = sorted({int(r["citypop"]) for r in rows})

    by_page = page_breakdown(rows)

    return {
        "schema": "census-1840-composition-v1",
        "_doc": (
            "DERIVED — rebuild with tools/census_1840_composition.py --build; check.sh "
            "re-derives it. What a Chicago household looked like in 1840, in counts. "
            "NOTHING HERE IS A PERSON: no name, no age, no residence and no 1835 "
            "identity appears in this file or may be read out of it. 1840 Chicago had "
            "roughly doubled since the 1 July 1835 scene, so these are shapes the "
            "reconstruction may be TESTED against, never a population it may be filled "
            "from. The owner's synthesis rule stands: 1840 household members are never "
            "minted into 1835 solely from census counts."
        ),
        "generated_by": "tools/census_1840_composition.py",
        "ticket": "T-0507",
        "inputs": {
            "committed_extract": {
                "path": str(EXTRACT.relative_to(ROOT.parent.parent)),
                "sha256": sha256(EXTRACT),
                "bytes": EXTRACT.stat().st_size,
                "source": "census_1840_chicago_name_crosswalk",
            },
            "band_labels": {
                "path": str(CROSSWALK.relative_to(ROOT.parent.parent)),
                "from": "T-0504's column_map — the committed statement of which IPUMS "
                        "variable is which column of the 1840 schedule",
            },
            "town_census_1835": str(TOWN_CENSUS.relative_to(ROOT.parent.parent)),
            "ipums_original_not_redistributed": IPUMS_ORIGINAL,
            "nhgis_1830_quoted_not_redistributed": NHGIS_1830,
            "sources": [
                "ipums_1840_chicago_households",
                "ipums_nhgis_1830_illinois_counties",
                "census_1840_chicago_name_crosswalk",
            ],
        },
        "totals": {
            "households": households,
            "persons": persons,
            "males": males,
            "females": females,
            "children_under_10": children,
            "free_white_persons": free_white,
            "free_coloured_persons": free_coloured,
            "slaves": total(rows, "nslave"),
            "child_share": share(children, persons),
            "free_coloured_share": share(free_coloured, persons),
            "males_per_100_females": rounded(100 * males / females, 1),
            "males_per_100_females_aged_20_and_over": rounded(100 * adult_m / adult_f, 1),
            "adults_20_and_over": adult_m + adult_f,
            "adult_share": share(adult_m + adult_f, persons),
            "citypop_variable": citypop,
            "citypop_note": (
                f"Every row carries citypop = {citypop[0]}, the published 1840 population "
                f"of the city of Chicago. The 964 households enumerated in this extract "
                f"sum to {persons} — {persons - citypop[0]} more, "
                f"{rounded(100 * (persons - citypop[0]) / citypop[0], 1)}%. The gap is "
                "recorded, not resolved: it may be the boundary IPUMS assigns households "
                "to the city, or the published figure, or both, and this file settles "
                "neither. Cite whichever you mean and say which."
            ),
        },
        "household_size": {
            "households": households,
            "persons": persons,
            "mean": rounded(persons / households, 3),
            "median": rounded(statistics.median(sizes), 1),
            "min": min(sizes),
            "max": max(sizes),
            "percentiles": percentiles(sizes),
            "empty_households": histogram[0],
            "empty_note": (
                f"{histogram[0]} of the 964 households return a total of zero people. A "
                "dwelling enumerated with nobody in it is what the schedule looks like "
                "when a family is counted elsewhere or a line is struck; they are kept in "
                "every denominator here because removing them would be a reading."
            ),
            "histogram": [{"size": k, "households": histogram[k]}
                          for k in sorted(histogram)],
        },
        "age_bands": {
            "free_white": bands,
            "free_white_persons": free_white,
            "free_coloured": coloured,
            "free_coloured_persons": free_coloured,
            "note": (
                "Thirteen male and thirteen female bands are printed; the extract uses "
                "ten of each, the bands from 80 upward standing empty but for one woman "
                "in her nineties. Band labels come from T-0504's column_map."
            ),
        },
        "industry": {
            "columns": industry,
            "employed_persons": employed,
            "employed_per_household": rounded(employed / households, 3),
            "employed_share_of_persons": share(employed, persons),
            "note": (
                "The 1840 schedule asks for the number of persons in each family employed "
                "in each of seven pursuits, so these are PERSONS in households, not "
                "occupations of named men, and a household may appear in more than one "
                "column. Manufactures and trades is the largest single column, which is "
                "what a lake port with a building boom should look like — and it is the "
                "one figure here that speaks directly to the trades the 1835 town needs."
            ),
        },
        "columns_the_extract_does_not_carry": uncarried,
        "by_page": by_page,
        "beside_the_town": {
            "1830_district": {
                "total": NHGIS_1830["putnam_county_total"],
                "what_it_counts": (
                    "The published 1830 county total for Putnam, which is where NHGIS "
                    "ds5 prints the return for the district headed 'Peoria & Putnam "
                    "Counties & Territory attached' — the district the Chicago "
                    "settlement was enumerated in. It is a district of northern "
                    "Illinois, not Chicago: the schedule never writes the word."
                ),
                "source": "ipums_nhgis_1830_illinois_counties",
            },
            "1835_town": {
                "people": town_people,
                "dwellings": town_dwellings,
                "people_per_dwelling": rounded(town_people / town_dwellings, 3),
                "what_it_counts": (
                    "The town census of November 1835 — four months after the scene "
                    "date — as Andreas prints it. The town's recorded size, never the "
                    "scene's population on 1 July."
                ),
                "source": town["people"]["town_total_source"],
            },
            "1840_city": {
                "households_enumerated": households,
                "persons_enumerated": persons,
                "published_citypop": citypop[0],
            },
            "growth": {
                "1835_over_1830_district": rounded(town_people / NHGIS_1830["putnam_county_total"], 3),
                "1840_enumerated_over_1835_town": rounded(persons / town_people, 3),
                "1840_published_over_1835_town": rounded(citypop[0] / town_people, 3),
                "note": (
                    "Two of these three figures count different things — a northern "
                    "Illinois district in 1830, a town in 1835, a city in 1840 — so the "
                    "ratios are the arithmetic between them and NOT a growth rate for a "
                    "single place. They are printed because the ticket asks for them "
                    "placed beside each other, and because the size of the step from "
                    "1835 to 1840 is the reason every figure in this file is a shape and "
                    "not a population."
                ),
            },
        },
        "what_this_may_calibrate": [
            "household size: the mean, median and the whole histogram, as the distribution "
            "a 1835 roof programme's occupancy should be tested against",
            "the sex ratio, overall and among adults, as the shape of a frontier port",
            "the child share, as a check on how many under-tens a reconstructed household may carry",
            "the trade split across the seven industry columns, as the relative weight of "
            "manufactures, commerce, agriculture and river navigation in the same town",
        ],
        "what_this_may_not_do": [
            "name anybody, or supply a person to any 1835 household",
            "supply the members of any specific 1835 household, however well the sizes match",
            "date a residence: a household counted in 1840 says nothing about 1 July 1835",
            "stand as evidence for a trade attached to a named man — the columns count "
            "persons in families, not occupations of individuals",
            "be read as a growth rate for one place; see beside_the_town.growth.note",
        ],
    }


def page_breakdown(rows: list[dict]) -> dict:
    """The ticket asks for the same figures by ward where T-0504 attached one.

    It attached PAGES, not wards — nothing in the 1840 material read so far divides
    Chicago into wards — so pages are what this reports, and it says so rather than
    quietly substituting one for the other.
    """
    doc = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    by_serial = {r["serial"]: r for r in rows}
    pages = []
    for page in doc["pages"]:
        serials = sorted({line["serial"] for line in page.get("lines", [])
                          if line.get("serial") and line["serial"] in by_serial})
        if not serials:
            continue
        sizes = [int(by_serial[s]["numperhh"]) for s in serials]
        pages.append({
            "familysearch_id": page["familysearch_id"],
            "printed_page": page.get("printed_page"),
            "households_attached": len(serials),
            "persons": sum(sizes),
            "mean_household_size": rounded(sum(sizes) / len(sizes), 3),
        })
    def page_order(p: dict) -> tuple:
        """`printed_page` is an integer where the page prints one, and null or the string
        'unknown' where the corner is torn or was not read. Both sort last, together."""
        n = p["printed_page"]
        return (0, int(n), p["familysearch_id"]) if str(n).isdigit() \
            else (1, 0, p["familysearch_id"])

    pages.sort(key=page_order)
    return {
        "unit": "page",
        "why_not_ward": (
            "The ticket asks for these figures by ward where T-0504 attached one. It "
            "attached pages: no 1840 material read by this project divides Chicago into "
            "wards, and inventing a ward boundary to report against would be worse than "
            "reporting the unit that exists."
        ),
        "pages_with_attached_households": len(pages),
        "households_attached": sum(p["households_attached"] for p in pages),
        "coverage_note": (
            "T-0504's fingerprint join is unique for a minority of households and "
            "ambiguous for the rest — 531 of 964 can EVER be resolved by age-band pattern "
            "alone. So this section describes the households that happen to be attached "
            "and is NOT a sample of the town; do not compare page means as if it were."
        ),
        "pages": pages,
    }


def self_test() -> int:
    """The invariants: the arithmetic closes, and nothing here is a person."""
    doc = build()
    rows = read_extract()
    failed = 0

    def bad(msg: str) -> None:
        nonlocal failed
        failed += 1
        print(f"   FAIL {msg}")

    t = doc["totals"]
    if t["males"] + t["females"] != t["persons"]:
        bad("males + females do not sum to the person total")
    if t["free_white_persons"] + t["free_coloured_persons"] != t["persons"]:
        bad("free white + free coloured do not sum to the person total")
    if sum(h["households"] for h in doc["household_size"]["histogram"]) != t["households"]:
        bad("the size histogram does not sum to 964 households")
    if sum(h["size"] * h["households"] for h in doc["household_size"]["histogram"]) != t["persons"]:
        bad("the size histogram does not sum to the person total")
    if t["households"] != 964:
        bad(f"households is {t['households']}, not the 964 the extract is")

    pcts = doc["household_size"]["percentiles"]
    ordered = [pcts[k] for k in ("p10", "p25", "p50", "p75", "p90", "p95", "p99")]
    if ordered != sorted(ordered):
        bad(f"percentiles are not monotone: {ordered}")

    ind = doc["industry"]
    if sum(c["persons"] for c in ind["columns"]) != ind["employed_persons"]:
        bad("the industry columns do not sum to the employed total")
    shares = sum(c["share_of_employed"] for c in ind["columns"])
    if abs(shares - 1.0) > 0.001:
        bad(f"the industry shares sum to {shares}, not 1")

    for u in doc["columns_the_extract_does_not_carry"]:
        if u["distinct_values_in_964_rows"] != ["0"]:
            bad(f"{u['ipums_variable']} is reported as uncarried but is not all zero")

    # Nothing minted. The extract this reads carries 55 transcribed head names; not one
    # of them, nor any serial, may reach the output.
    blob = dumps(doc)
    names = [r["head_name_transcribed"].strip() for r in rows
             if r["head_name_transcribed"].strip()]
    for name in names:
        if name in blob:
            bad(f"a head-of-household name reached the output: {name!r}")
            break
    for serial in {r["serial"] for r in rows}:
        if f'"{serial}"' in blob:
            bad(f"a household serial reached the output: {serial}")
            break

    if failed:
        print(f"   {failed} assertion(s) failed")
        return 1
    print(f"   OK: 964 households and {t['persons']} persons close on every total, the "
          f"histogram and the industry columns; no name and no serial reaches the output")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    doc = build()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != dumps(doc):
            print(f"   FAIL {OUT.relative_to(ROOT)} is stale or hand-edited; rebuild it "
                  f"with tools/census_1840_composition.py --build")
            return 1
        print(f"   ok    {OUT.relative_to(ROOT)} re-derives — "
              f"{doc['totals']['households']} households, "
              f"{doc['totals']['persons']} persons, nobody minted")
        return 0
    OUT.write_text(dumps(doc), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['totals']['households']} households, "
          f"{doc['totals']['persons']} persons, mean household "
          f"{doc['household_size']['mean']}, {doc['industry']['employed_persons']} "
          f"persons in the seven industry columns")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
