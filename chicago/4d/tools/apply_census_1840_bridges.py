#!/usr/bin/env python3
"""Apply/check recovered 1840 census household evidence and 1835 identity bridges.

Issue #669.  The 210-row census dataset is dated 1840 evidence.  The bridge CSV
is the adjudication boundary for attaching an 1840 head to an existing 1835
canonical resident.  `validated` and `provisional` are kept distinct, and no
1840 spouse/child/boarder is minted into the 1835 household from census counts.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import re
from collections import Counter
from pathlib import Path

# T-0836: rerooted with the synthesis it is re-applied by, so `--drift` can run the pair
# against a scratch copy of the tree.  Unset in every ordinary run.
ROOT = Path(os.environ["SYNTH_SCRATCH_ROOT"]) if os.environ.get("SYNTH_SCRATCH_ROOT") \
    else Path(__file__).resolve().parents[1]
import sys
# The DATA root is overridable (above); the tools directory is NOT — it is where this
# file lives. Deriving the import path from ROOT instead breaks `--drift`, whose scratch
# copy carries data and no tools: measured, ModuleNotFoundError on rebuild_resident_index.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from rebuild_resident_index import rebuild  # noqa: E402  (the manifest's one owner)

DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
RESEARCH = DATA / "research" / "residents"
BRIDGES = RESEARCH / "census_1840_identity_bridges.csv"
CENSUS_DIR = DATA / "census" / "1840"
CENSUS_INDEX = CENSUS_DIR / "index.json"
CENSUS_ROWS = CENSUS_DIR / "household_heads.csv.gz"
LEDGER = RESEARCH / "synthesis_2026_09_02.json"
SUMMARY = ROOT / "docs" / "RESEARCH" / "resident-household-synthesis-2026-09-02.md"
SOURCE_ID = "census_1840_chicago_v4_research"
ALLOWED_STATUS = {"validated", "provisional"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc, indent=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=indent, ensure_ascii=False) + "\n", encoding="utf-8")


def as_int(row, key):
    v = str(row.get(key) or "").strip()
    return int(v) if v else None


def census_rows():
    if not CENSUS_ROWS.exists():
        raise ValueError(f"missing census evidence file: {CENSUS_ROWS}")
    with gzip.open(CENSUS_ROWS, "rt", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    manifest = load(CENSUS_INDEX)
    expected = int(manifest.get("records") or 0)
    if len(rows) != expected or expected != 210:
        raise ValueError(f"census household row count drift: file={len(rows)} manifest={expected}, expected 210")
    serials = [as_int(r, "serial") for r in rows]
    if any(s is None for s in serials) or len(set(serials)) != len(serials):
        raise ValueError("1840 SERIAL values are blank or non-unique")
    pages = sorted({as_int(r, "page") for r in rows})
    if pages != [229, 230, 231, 232, 233, 234, 235]:
        raise ValueError(f"unexpected census page coverage: {pages}")
    return rows


def bridge_rows():
    with BRIDGES.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    seen_person = set(); seen_serial = set()
    for row in rows:
        pid = row["person_id"].strip(); serial = as_int(row, "serial")
        status = (row.get("bridge_status") or "").strip()
        if status not in ALLOWED_STATUS:
            raise ValueError(f"invalid bridge_status for {pid}: {status!r}")
        if not pid or pid in seen_person:
            raise ValueError(f"duplicate/blank bridge person_id: {pid!r}")
        if serial is None or serial in seen_serial:
            raise ValueError(f"duplicate/blank bridge serial: {serial!r}")
        seen_person.add(pid); seen_serial.add(serial)
    return rows


def census_lookup(rows):
    return {as_int(r, "serial"): r for r in rows}


# ---------------------------------------------------------------------------
# The scan reading of the same line, when there is one (T-0530).
#
# The 210 rows this tool applies are a RECOVERY from the owner's v4 workbook,
# which he has ruled lost, and PR #683 established that where a page has since
# been read off the deposited image the two disagree — sometimes about who the
# head of the household even is. So where the page a bridge cites has now been
# read line by line, the sheet's own figures are attached BESIDE the recovered
# ones rather than instead of them: the recovered household is the argument the
# bridge was built on, the scan is the evidence, and a card that showed only one
# of them would be hiding the disagreement rather than resolving it.
#
# This is DERIVED, not authored: it is read from data/research/census_1840/pages/
# by page and row, so it appears for a person the moment that person's page is
# read and needs no bridge row to be touched.
BANDS_WHITE = ["under 5", "5 to 9", "10 to 14", "15 to 19", "20 to 29", "30 to 39",
               "40 to 49", "50 to 59", "60 to 69", "70 to 79", "80 to 89",
               "90 to 99", "100 and over"]
BANDS_COLOURED = ["under 10", "10 to 23", "24 to 35", "36 to 54", "55 to 99", "100 and over"]
PAGES = DATA / "research" / "census_1840" / "pages"


def scan_pages():
    """(printed_page, line) -> (page doc, record), for every page read so far."""
    out = {}
    if not PAGES.is_dir():
        return out
    for path in sorted(PAGES.glob("*.json")):
        doc = load(path)
        if doc.get("cells_state") != "read":
            continue
        for rec in doc.get("records") or []:
            if rec.get("cells"):
                out[(doc.get("printed_page"), rec.get("line"))] = (doc, rec)
    return out


def _phrase(counts, bands, noun):
    parts = [f"{n} {noun} {bands[i]}" if n == 1 else f"{n} {noun}s {bands[i]}"
             for i, n in enumerate(counts) if n]
    return parts


def scan_verified(page, row, pages):
    hit = pages.get((page, row))
    if not hit:
        return None
    doc, rec = hit
    c = rec["cells"]
    males = sum(c["free_white_male"]) + sum(c["free_coloured_male"])
    females = sum(c["free_white_female"]) + sum(c["free_coloured_female"])
    under10 = (sum(c["free_white_male"][:2]) + sum(c["free_white_female"][:2])
               + c["free_coloured_male"][0] + c["free_coloured_female"][0])
    parts = (_phrase(c["free_white_male"], BANDS_WHITE, "male")
             + _phrase(c["free_white_female"], BANDS_WHITE, "female")
             + _phrase(c["free_coloured_male"], BANDS_COLOURED, "free coloured male")
             + _phrase(c["free_coloured_female"], BANDS_COLOURED, "free coloured female"))
    return {
        "read_by": "T-0530",
        "sources": ["census_1840_chicago_familysearch_images"],
        "image": doc.get("image"),
        "line": rec.get("line"),
        "head_name_as_read": rec.get("as_read"),
        "free_persons": c["free_persons"],
        "males": males,
        "females": females,
        "children_under_10": under10,
        "age_bands": "; ".join(parts) or "no person is marked on this line",
        "column_totals_check": doc.get("reconciliation_summary"),
    }


def scan_disagreement(household, scan):
    """The sentence a visitor needs, or None when the two readings agree."""
    if not scan:
        return None
    pairs = [("people", household.get("persons"), scan["free_persons"]),
             ("males", household.get("male"), scan["males"]),
             ("females", household.get("female"), scan["females"]),
             ("children under ten", household.get("children_under_10"), scan["children_under_10"])]
    diff = [f"{label} {a} against {b}" for label, a, b in pairs
            if a is not None and a != b]
    if not diff:
        return ("The page has since been read off the image and gives the same household: "
                "the recovered workbook and the sheet agree line for line here.")
    return ("The page has since been read off the image and does NOT give the same household. "
            "Recovered workbook against the sheet: " + "; ".join(diff)
            + ". Neither is deleted. The sheet is the senior reading — it is the record, and "
            "the workbook is a memory of the record — but the bridge to this person was built "
            "on the workbook's row, so the disagreement is shown rather than resolved here.")


def later_census(row, census, pages=None):
    serial = as_int(row, "serial")
    source = census[serial]
    scan = scan_verified(as_int(source, "page"), as_int(source, "row"), pages or {})
    household = {
        "persons": as_int(source, "persons"),
        "children_under_10": as_int(source, "children_lt_10"),
        "male": as_int(source, "males"),
        "female": as_int(source, "females"),
        "agriculture": as_int(source, "agriculture"),
        "commerce": as_int(source, "commerce"),
        "manufactures_trades": as_int(source, "manufactures_trades"),
        "inland_navigation": as_int(source, "inland_navigation"),
        "professions_engineering": as_int(source, "professions_engineering"),
        "foreigners_not_naturalized": as_int(source, "foreigners_not_naturalized"),
        "illiterate_over_21": as_int(source, "illiterate_gt_21"),
    }
    doc = {
        "year": 1840,
        "source_id": SOURCE_ID,
        "serial": serial,
        "head_name_transcribed": source.get("raw_scan_reading") or row["census_name"].strip(),
        "head_name_normalized": source.get("preferred_name") or row["canonical_name"].strip(),
        "name_confidence": source.get("name_confidence") or row["identity_confidence"].strip().title(),
        "identity_confidence": row["identity_confidence"].strip().title(),
        "bridge_status": row["bridge_status"].strip(),
        "serial_mapping_confidence": source.get("serial_confidence") or row["serial_mapping_confidence"].strip(),
        "census_page": as_int(source, "page"),
        "census_row": as_int(source, "row"),
        "source_image": source.get("source_image") or row["source_image"].strip() or None,
        "source_kind": source.get("source_kind") or None,
        "household": household,
        "bridge_basis": row["bridge_basis"].strip(),
        "note": "LATER EVIDENCE, NOT A BACK-PROJECTION. This is the 1840 federal census household, five years after the 1835-07-01 scene; its household composition is not asserted for 1835 without separate evidence."
    }
    # Absent until that page is read, rather than present and null: a key
    # shipped empty to a browser is a figure nobody can see and nobody can use.
    if scan:
        doc["scan_verified"] = scan
        doc["scan_disagreement"] = scan_disagreement(household, scan)
    return doc


def docs_and_people():
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    people = {}
    for path, doc in docs.items():
        for person in doc.get("persons") or []:
            pid = person.get("id")
            if pid:
                if pid in people:
                    raise ValueError(f"duplicate canonical person id: {pid}")
                people[pid] = (person, path, doc)
    return docs, people


def rebuild_index(index, docs):
    """The manifest, re-derived from the cards by its one owner (T-0715).

    This pass used to carry its own copy of the derivation. Two copies of one
    rule drift, and the rule is gated now, so there is one.
    """
    return rebuild(index, docs)


def update_ledger(rows, all_census):
    ledger = load(LEDGER)
    old = dict(ledger.get("census_1840") or {})
    linked = [{"person_id":r["person_id"].strip(), "serial":as_int(r,"serial"), "name":r["canonical_name"].strip(),
               "page":as_int(r,"census_page"), "row":as_int(r,"census_row"),
               "bridge_status":r["bridge_status"].strip(),
               "identity_confidence":r["identity_confidence"].strip(),
               "serial_mapping_confidence":r["serial_mapping_confidence"].strip()} for r in rows]
    validated = [r for r in linked if r["bridge_status"] == "validated"]
    provisional = [r for r in linked if r["bridge_status"] == "provisional"]
    ledger["census_1840"] = {
        "recovery_issue": 669,
        "named_household_heads_retained": len(all_census),
        "serial_linked_household_heads_retained": len(all_census),
        "linked": linked,
        "validated_identity_bridges": len(validated),
        "provisional_identity_bridges": len(provisional),
        "not_yet_linked_to_canonical_1835_resident": len(all_census) - len(linked),
        # Idempotence, found by running this tool twice (T-0530). The legacy
        # block is lifted out of whatever `census_1840` held BEFORE this tool
        # first owned it — so on the second run `old` is this tool's own output,
        # `eligible_named_rows` is gone and `linked` is the bridge list, and the
        # legacy result was being overwritten with a copy of the new one. Once
        # the block exists it is carried forward verbatim: it is a record of a
        # matcher that no longer runs, and nothing can re-derive it.
        "legacy_partial_matcher": old.get("legacy_partial_matcher") or {
            "eligible_named_rows": old.get("eligible_named_rows"),
            "linked": old.get("linked") or [],
            "ambiguous": old.get("ambiguous") or [],
            "unmatched_named_heads": old.get("unmatched_named_heads") or [],
            "rule": old.get("rule"),
        },
        "rule": "All 210 resolved 1840 row-to-SERIAL household records are retained as dated evidence. Canonical 1835 links require an explicit adjudicated person_id bridge and are graded validated or provisional; no fuzzy/common-name promotion."
    }
    dump(LEDGER, ledger, 2)


def update_summary(rows, all_census):
    validated = [r for r in rows if r["bridge_status"] == "validated"]
    provisional = [r for r in rows if r["bridge_status"] == "provisional"]
    nlinks = len(rows)
    text = SUMMARY.read_text(encoding="utf-8")
    text = re.sub(r"\| Linked to named 1840 census household \|\s*0\s*\|\s*\d+\s*\|",
                  f"| Linked to named 1840 census household | 0 | {nlinks} |", text)
    section = f'''## 1840 census evidence

The recovered v4 work is now retained as a complete dated census layer: **{len(all_census)} named 1840 household-head rows on printed pages 229–235, all with resolved IPUMS SERIALs and household demographic fields**. These records live under `data/census/1840/` whether or not they can yet be tied safely to a 1 July 1835 resident.

Canonical resident linkage is a separate assertion. There are currently **{len(validated)} validated High-confidence 1835↔1840 identity bridges** — John Murphy (1840 p.233 r.30, SERIAL 5102066) and William Hanford Adams (p.229 r.9, SERIAL 5101954) — plus **{len(provisional)} provisional bridge**, John Miller ↔ John J. Miller (p.232 r.3, SERIAL 5102035). Miller is independently attested as the Chicago tanner and 1833 trustee, but the 1840 middle initial is new, so the link remains Medium/provisional rather than High.

**1840 is later evidence, not the 1835 household.** Household totals, children, sex structure, industry, foreigner and literacy fields are retained under the census dataset and `later_census` links for household-reconciliation research, but are not projected backward to 1 July 1835. Murphy's 1840 household has 6 people; Adams 2; Miller 5. Those counts do not themselves mint spouses, children, partners, servants or boarders into the 1835 resident layer.

The old September 2 “0 links / 29 unmatched heads” result is preserved in the machine ledger as the **legacy partial matcher** result. It came from the older pages-234/235 partial CSV plus exact normalized-name matching and did not consume the later v4 adjudication.

'''
    text = re.sub(r"## 1840 census evidence\n.*?(?=## Placement / structures)", section, text, flags=re.S)
    SUMMARY.write_text(text, encoding="utf-8")


def apply():
    all_rows = census_rows(); lookup = census_lookup(all_rows)
    rows = bridge_rows(); docs, people = docs_and_people(); pages = scan_pages()
    for row in rows:
        pid = row["person_id"].strip(); serial = as_int(row, "serial")
        if pid not in people:
            raise SystemExit(f"bridge person_id not found in canonical residents: {pid}")
        if serial not in lookup:
            raise SystemExit(f"bridge SERIAL not found in 210-row census dataset: {serial}")
        person, _path, _doc = people[pid]
        person["later_census"] = later_census(row, lookup, pages)
    for path, doc in docs.items(): dump(path, doc, 1)
    index = rebuild_index(load(INDEX), docs); dump(INDEX, index, 1)
    update_ledger(rows, all_rows); update_summary(rows, all_rows)
    # THIS WRITER DOES NOT WRITE THE PUBLISHED MIRROR (T-0938, fixing T-0933).  It used
    # to carry the four paths it touches into `site/chicago/4d/data/residents/`
    # PRETTY-PRINTED, while `synthesize_resident_research.py` and `tools/publish.sh`
    # both wrote the same paths MINIFIED — so `bash tools/publish.sh` on an untouched
    # `dev` turned `tools/check.sh` red on four files whose parsed values were identical,
    # and whichever writer ran last decided whether the gate was green.  The mirror is
    # untracked and generated now and has exactly one writer, `tools/publish.sh`, which
    # `tools/check.sh` runs before it gates what that produced.
    return check()


def check():
    all_rows = census_rows(); lookup = census_lookup(all_rows)
    rows = bridge_rows(); docs, people = docs_and_people(); pages = scan_pages(); problems=[]
    expected = {r["person_id"].strip(): r for r in rows}
    for pid, row in expected.items():
        if pid not in people:
            problems.append(f"bridge person missing: {pid}"); continue
        serial = as_int(row,"serial")
        if serial not in lookup:
            problems.append(f"bridge serial absent from 210-row census dataset: {serial}"); continue
        got = people[pid][0].get("later_census") or {}
        if got.get("serial") != serial or got.get("census_page") != as_int(row,"census_page") or got.get("census_row") != as_int(row,"census_row"):
            problems.append(f"bridge drift for {pid}")
        if got.get("bridge_status") != row.get("bridge_status"):
            problems.append(f"bridge status drift for {pid}")
        # The scan block is DERIVED from the read census pages, so a hand-edited
        # figure on a card has to fail here rather than sit in the tree looking
        # like something that was read off a photograph (T-0530).
        want = scan_verified(as_int(lookup[serial], "page"), as_int(lookup[serial], "row"), pages)
        if got.get("scan_verified") != want:
            problems.append(f"scan reading drift for {pid}: rerun apply_census_1840_bridges.py")
        want_note = scan_disagreement(got.get("household") or {}, want) if want else None
        if got.get("scan_disagreement") != want_note:
            problems.append(f"scan disagreement drift for {pid}")
    actual_links = [p for p,_path,_doc in people.values() if p.get("later_census")]
    index = load(INDEX); counts=index.get("counts") or {}
    if int(counts.get("census_1840_linked") or 0) != len(actual_links): problems.append("index census_1840_linked disagrees with resident records")
    if int(counts.get("households") or 0) != len(docs): problems.append("index household count disagrees with records")
    people_count=sum(len(d.get("persons") or []) for d in docs.values())
    if int(counts.get("persons") or 0) != people_count: problems.append("index person count disagrees with records")
    ledger=load(LEDGER); census=ledger.get("census_1840") or {}
    validated=sum(r["bridge_status"]=="validated" for r in rows); provisional=sum(r["bridge_status"]=="provisional" for r in rows)
    if int(census.get("named_household_heads_retained") or 0) != 210: problems.append("ledger does not retain all 210 census heads")
    if int(census.get("validated_identity_bridges") or 0) != validated: problems.append("ledger validated bridge count disagrees")
    if int(census.get("provisional_identity_bridges") or 0) != provisional: problems.append("ledger provisional bridge count disagrees")
    summary=SUMMARY.read_text(encoding="utf-8")
    if "**210 named 1840 household-head rows" not in summary: problems.append("summary census coverage is stale")
    # THE MIRROR IS NOT THIS TOOL'S TO ASSERT ANY MORE (T-0938).  These four lines used
    # to check that `site/chicago/4d/data/residents/` carried the same parsed value as
    # the cards — a real claim, but one this tool could only make because it was also a
    # writer of the mirror, and being both is what made T-0933 possible.  The mirror is
    # untracked and generated now; `tools/check.sh` publishes it and then asks
    # `tools/check_published_residents.mjs`, which makes the identical claim over the
    # WHOLE layer (same value, file for file, none missing and none extra) rather than
    # over the handful of rows this bridge file happens to name.
    adams=people.get("adams_william_h")
    if adams and len(adams[2].get("persons") or []) != 1: problems.append("Adams 1840 second person was incorrectly back-projected into 1835")
    if problems:
        print("CENSUS BRIDGE FAIL")
        for p in problems: print(" -", p)
        return 1
    print(f"OK: 210 census households retained; {validated} validated + {provisional} provisional resident bridges; {len(docs)} resident households; {people_count} canonical persons")
    return 0


# ---------------------------------------------------------------------------
# T-0515 — the candidates, and why so few of them become bridges
#
# The ticket asks for the bridge CSV to be EXTENDED from the 1840 appearances
# the identity consolidation now carries, "keeping its rule — a bridge needs an
# adjudicated discriminator; composition is never back-projected". This mode
# derives every candidate that consolidation offers and rules on each one, so
# the links this project has NOT made are as legible as the three it has.
#
# The three rules, in the order they fire. A candidate must pass all three.
#
#   B1  A SERIAL. The bridge row's key is the 1840 dwelling serial, and the only
#       place a serial exists is the 210-row recovery of the owner's v4 workbook
#       (pages 229-235). An appearance citing any other page — and 33 of the 40
#       cite pages 207-228 — has been read off the deposited image, and those
#       page files carry the schedule's ruled lines and no serial at all. There
#       is nothing to key a bridge on, and one keyed on a page and a row alone
#       would not survive the duplicate-serial check this tool already enforces.
#
#   B2  THE TWO READINGS AGREE ON WHO IT IS. PR #683 established that where a
#       page in the recovery has since been read off the image the two disagree,
#       sometimes about the head's name. Six of the seven candidates that clear
#       B1 are exactly that: the consolidation reads Gurdon S. Hubbard at 232:17
#       and the recovery's own preferred name for that line is Samuel J. McCord.
#       A bridge across that disagreement would be picking a winner in the very
#       dispute the tool was built to keep visible.
#
#   B3  AN ADJUDICATED DISCRIMINATOR. The rule the three committed bridges were
#       written under: something beyond the name — an 1833/1834/1835 poll or tax
#       hit, or a directory match — that is not itself flagged as a common-name
#       caution. The last candidate standing, John Wilson at 229:2, fails on the
#       recovery's own words: "Common-name caution."
#
# So the honest count today is zero new bridges, and this ledger is the reason
# rather than a silence. It is DERIVED — re-run it when a page is read or a
# discriminator is adjudicated and the candidate moves by itself.
# ---------------------------------------------------------------------------

MASTER = RESEARCH / "identity_master.json"
CANDIDATES = RESEARCH / "census_1840_bridge_candidates_ruled.json"
COMMON_NAME = re.compile(r"common[- ]name", re.I)


def _tokens(value):
    return [t for t in re.split(r"[^A-Za-z]+", str(value or "").lower())
            if t and t not in {"mr", "mrs", "miss", "dr", "capt", "col", "jr", "sr"}]


def _agrees(identity, printed):
    """The same forename test the regrade uses, imported rather than restated."""
    import sys
    sys.path.insert(0, str(ROOT / "tools"))
    from mint_civic_residents import forename_agrees
    sur = (identity.get("surname") or "").lower()
    if sur and sur not in _tokens(printed):
        return False
    return forename_agrees(identity.get("forename") or "", sur, printed)


def candidates():
    master = load(MASTER)
    census = census_rows()
    by_pr = {(r["page"], r["row"]): r for r in census}
    have = {r["person_id"].strip() for r in bridge_rows()}
    ruled = []
    for identity in sorted(master.get("identities") or [], key=lambda i: i["id"]):
        pid = identity.get("canonical_person_id")
        if not pid:
            continue
        for app in identity.get("appearances") or []:
            if app.get("domain") != "census_1840":
                continue
            locator = str(app.get("locator") or "")
            page, _, row_no = locator.partition(":")
            entry = {"person_id": pid, "identity": identity["id"],
                     "as_read": app.get("as_read"), "locator": locator,
                     "record_id": app.get("record_id")}
            if pid in have:
                entry.update(outcome="bridged", rule=None,
                             reason="already carried as an adjudicated bridge")
                ruled.append(entry)
                continue
            found = by_pr.get((page, row_no))
            if not found:
                entry.update(outcome="refused", rule="B1",
                             reason=("no SERIAL: this appearance cites a page outside the "
                                     "210-row recovery, and the page scans carry no serial "
                                     "a bridge row could be keyed on"))
                ruled.append(entry)
                continue
            entry["serial"] = found["serial"]
            entry["recovery_name"] = found["preferred_name"]
            if not _agrees(identity, found["preferred_name"]):
                entry.update(outcome="refused", rule="B2",
                             reason=(f"the two readings of {locator} disagree about who it "
                                     f"is: the consolidation reads {app.get('as_read')!r} "
                                     f"and the recovery {found['preferred_name']!r}"))
                ruled.append(entry)
                continue
            discriminators = [found[k] for k in ("1833_poll", "1833_tax", "1834_poll",
                                                 "1835_poll", "1839_directory_match")
                              if (found.get(k) or "").strip()]
            clean = [d for d in discriminators if not COMMON_NAME.search(d)]
            if not clean:
                entry.update(outcome="refused", rule="B3",
                             reason=("no adjudicated discriminator beyond the name" +
                                     (" — the recovery's own note is a common-name caution"
                                      if discriminators else "")))
                ruled.append(entry)
                continue
            entry.update(outcome="bridgeable", rule=None,
                         reason="; ".join(clean), basis=clean)
            ruled.append(entry)
    return ruled


def candidates_report(write: bool = False) -> int:
    ruled = candidates()
    tally = Counter((r["outcome"], r.get("rule")) for r in ruled)
    print(f"1840 BRIDGE CANDIDATES — {len(ruled)} appearance(s) the consolidation offers")
    for (outcome, rule), n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:5d}  {outcome}{(' / ' + rule) if rule else ''}")
    for r in ruled:
        if r["outcome"] != "refused":
            print(f"  {r['outcome'].upper():11s} {r['person_id'][:30]:32s} {r['reason']}")
    print()
    for r in ruled:
        if r["outcome"] == "refused" and r["rule"] != "B1":
            print(f"  REFUSE {r['rule']} {r['person_id'][:30]:32s} {r['reason']}")
    doc = {
        "schema": 1,
        "_doc": ("GENERATED by tools/apply_census_1840_bridges.py --candidates (T-0515). "
                 "Every 1840 census appearance the identity consolidation carries for a "
                 "canonical resident, ruled on against the three bridge rules. A refusal "
                 "here is a link this project has NOT made and the reason it has not."),
        "generated_by": "tools/apply_census_1840_bridges.py --candidates",
        "rules": {
            "B1": "a bridge is keyed on the 1840 SERIAL, which only the 210-row recovery has",
            "B2": "the recovery's reading of the line and the consolidation's must name the same person",
            "B3": "a discriminator beyond the name, and not one the recovery itself flags as common-name",
        },
        "counts": {f"{o}{'/' + r if r else ''}": n for (o, r), n in sorted(tally.items())},
        "candidates": ruled,
    }
    if write:
        dump(CANDIDATES, doc)
        print(f"wrote {CANDIDATES.relative_to(ROOT)}")
    return 0


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--check",action="store_true")
    ap.add_argument("--candidates",action="store_true",
                    help="T-0515: rule on every 1840 appearance the consolidation offers")
    ap.add_argument("--write",action="store_true",help="with --candidates, commit the ledger")
    args=ap.parse_args()
    if args.candidates: return candidates_report(args.write)
    return check() if args.check else apply()


if __name__ == "__main__": raise SystemExit(main())
