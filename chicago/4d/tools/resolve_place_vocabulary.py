#!/usr/bin/env python3
"""THE NEWSPAPERS' PLACE VOCABULARY, RESOLVED AGAINST THE COMMITTED TOWN (T-1048).

`in_town_places()` (tools/mint_letter_list_residents.py, shared by the placed and
documented mints) resolves a place string against the bare town, every committed 1835
street name and every committed structure name and aka. Run the newspapers gazetteer's
`associated_places` through it and 193 of 2,665 persons carry nothing that resolves —
and the list is NOT 193 out-of-town men. It holds three different things at once:

  * places plainly INSIDE the town the function simply cannot spell — `Fort Dearborn`,
    `Water Street`, `the Mansion House`, `the Point`;
  * places that name the town and fail anyway on their own punctuation or qualifier —
    `Chicago, Illinois`, `the market square, Chicago`;
  * places genuinely OUTSIDE it — `Michigan City`, `Green Bay`, `Hennepin`, `Juliet`.

Only the third group may ever refuse anybody. This module is the resolution that tells
the three apart, one ruling per DISTINCT PRINTED STRING rather than per person, because
the printed string is what is being read: two records that print the same words are the
same reading and must not be resolved apart.

NOTHING HERE REFUSES ANYBODY. T-1048 settles the vocabulary and changes no card;
T-1049 is the ticket that spends it. `resolution_of()` is the API it will call.

WHERE THE ANSWER COMES FROM — derivation first, ruling only where derivation cannot
reach. `derive()` resolves a string against the COMMITTED DATASET by four mechanical
rules and nothing else (D1-D4 below), so a street renamed or a building added moves
those answers with it; `--check` re-derives every one of them and fails if the corpus
has drifted from what the dataset now says. What derivation cannot reach is RULED in
the corpus — `data/research/newspapers/place_vocabulary.json`, a hand-authored
adjudication carrying the boundary it falls under and the reasoning — and never in a
list inside this file. A city list hard-coded in a tool is what T-1047's acceptance
forbids, and it is also simply the wrong place for a judgement a reader must be able to
argue with.

  D1 `bare_town`      — the string IS the town: `Chicago`, `the town of Chicago`.
  D2 `street`         — `fronting_street.streets_named()` returns at least one
                        committed street of this scene. That function is already the
                        project's street resolver and its refusals are deliberate, so
                        this rule inherits them rather than re-deciding them: it reads
                        'the corner of Dearborn and Lake streets' and it refuses
                        'Kinzie's Addition'.
  D3 `structure`      — the string, or the string less a leading article, is a
                        committed structure `name` or `aka` verbatim under
                        `norm_place()`. This is what carries `the Mansion House` and
                        `the Tremont House`.
  D4 `town_qualifier` — one of the string's comma-separated segments IS the bare town,
                        so the town is the place's own locator: `Chicago, Illinois`,
                        `the market square, Chicago`. Deliberately narrow — it wants a
                        comma. 'a farm two miles from Chicago' names the town in prose
                        and is two miles outside it, and no mechanical rule should be
                        trusted to see the difference; that string is RULED.

UNDECIDED IS A REAL ANSWER AND IT IS COUNTED. A string this project cannot place —
`Main Street`, which the scene does not commit; `Cook County` and `United States`,
which CONTAIN the town and so place a man neither in it nor out of it; `Kinzie's
Addition` and `Wabansia`, adjacent surveys the town commits none of (T-0789, T-0790) —
is resolved to `undecided` and left there. It is not a silent third state and it is not
quietly folded into `outside`, which would refuse the man: 9 of the 128 strings land
here, the two spellings of `Cook County` carry 24 readings between them, and a guard
that read those as refusals would throw out residents for naming the county the town
stands in.

WHAT THE RESOLUTION MOVES, measured on dev 2026-09-12 and reproducible with `--report`.
Of the 128 distinct strings: 48 inside, 71 outside, 9 undecided; 25 of them derived and
103 ruled. Of the 193 persons the naive test refuses, this vocabulary refuses 141 — the
other 52 are 27 it places INSIDE the town and 25 it will not decide. All eight false
positives T-1047's acceptance names resolve inside, `Fort Dearborn` (13 readings) and
`Water Street` (6) among them. That 52 is the whole of this ticket's argument: a guard
built on the naive test would have thrown a fiftieth of the gazetteer's placed persons
out of the town they lived in.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from fronting_street import streets_named  # noqa: E402

DATA = ROOT / "data"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
VOCABULARY = DATA / "research" / "newspapers" / "place_vocabulary.json"
STREETS = DATA / "streets" / "1835.json"
STRUCTURES = DATA / "structures"

BARE_TOWN = {"chicago", "the town of chicago"}
BUCKETS = ("inside", "outside", "undecided")
DERIVATIONS = ("bare_town", "street", "structure", "town_qualifier")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def norm_place(s: str) -> str:
    """The mints' own normalisation, so this module resolves what they resolve."""
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


# ---------------------------------------------------------------------------
# the committed town this vocabulary is resolved against
# ---------------------------------------------------------------------------

_cache: dict = {}


def committed_structures() -> dict[str, str]:
    """Every committed structure name and aka, normalised, to its structure id."""
    if "structures" not in _cache:
        names: dict[str, str] = {}
        for path in sorted(STRUCTURES.glob("*.json")):
            doc = load(path)
            for printed in [doc.get("name")] + list(doc.get("aka") or []):
                if isinstance(printed, str) and norm_place(printed):
                    names.setdefault(norm_place(printed), doc["id"])
        _cache["structures"] = names
    return _cache["structures"]


def committed_street_ids() -> set[str]:
    if "street_ids" not in _cache:
        _cache["street_ids"] = {s["id"] for s in load(STREETS)["streets"]}
    return _cache["street_ids"]


# ---------------------------------------------------------------------------
# D1-D4: what the committed dataset can answer on its own
# ---------------------------------------------------------------------------

def derive(place: str) -> dict | None:
    """Resolve one printed place against the committed dataset, or None.

    A derivation only ever returns `inside`: the committed dataset is the town, so it
    can say that a string names something in the town and it can say nothing whatever
    about a string it does not hold. 'Detroit' is not out of town BECAUSE the dataset
    lacks it — the dataset lacks every place on earth it does not model.
    """
    flat = norm_place(place)
    bare = re.sub(r"^(the|a|an) ", "", flat).strip()

    if flat in BARE_TOWN or bare in BARE_TOWN:
        return {"how": "bare_town", "matched": []}

    for candidate in (flat, bare):
        structure_id = committed_structures().get(candidate)
        if structure_id:
            return {"how": "structure", "matched": [structure_id]}

    named = streets_named(place)
    if named:
        return {"how": "street", "matched": named}

    segments = [norm_place(part) for part in place.split(",")]
    if any(segment in BARE_TOWN for segment in segments):
        return {"how": "town_qualifier", "matched": []}

    return None


# ---------------------------------------------------------------------------
# the corpus, and the reading T-1049 will take from it
# ---------------------------------------------------------------------------

def vocabulary() -> dict[str, dict]:
    """Every distinct printed place, to its entry. The corpus is the authority."""
    if "vocabulary" not in _cache:
        _cache["vocabulary"] = {e["place"]: e for e in load(VOCABULARY)["places"]}
    return _cache["vocabulary"]


def resolution_of(place: str) -> str:
    """`inside`, `outside` or `undecided` for one printed place string.

    A string the corpus does not carry is `undecided` rather than an error, and that is
    the safe reading in both directions: a place nobody has resolved yet refuses
    nobody. `--check` is what keeps the corpus complete, in the gate, so an unresolved
    string is a failed commit rather than a silent refusal in production.
    """
    entry = vocabulary().get(place)
    return entry["resolution"] if entry else "undecided"


def places_of(gazetteer_person: dict) -> list[str]:
    return [p for p in (gazetteer_person.get("associated_places") or [])
            if isinstance(p, str) and p.strip()]


def person_resolution(gazetteer_person: dict) -> str:
    """The strongest thing the corpus says about where one person's places are.

    A person is `inside` if ANY of their places resolves inside the town — one Chicago
    address is a Chicago appearance whatever else the man's record carries — `outside`
    only if at least one place resolves outside and NONE resolves inside or undecided,
    and `undecided` otherwise. `no_places` is its own answer: 1,380 of the gazetteer's
    persons carry no place at all, and this vocabulary has nothing to say about them.
    """
    places = places_of(gazetteer_person)
    if not places:
        return "no_places"
    found = {resolution_of(p) for p in places}
    if "inside" in found:
        return "inside"
    if "undecided" in found:
        return "undecided"
    return "outside"


# ---------------------------------------------------------------------------
# the counts, restated from the corpus and the gazetteer every time
# ---------------------------------------------------------------------------

def counts() -> dict:
    persons = load(GAZETTEER)["persons"]
    strings: collections.Counter = collections.Counter()
    for person in persons:
        for place in places_of(person):
            strings[place] += 1

    by_string = collections.Counter(resolution_of(p) for p in strings)
    readings = collections.Counter()
    for place, n in strings.items():
        readings[resolution_of(place)] += n
    by_person = collections.Counter(person_resolution(p) for p in persons)
    how = collections.Counter(
        (vocabulary().get(p, {}).get("derived") or {}).get("how", "ruled")
        for p in strings)

    return {
        "persons": len(persons),
        "persons_with_a_place": sum(1 for p in persons if places_of(p)),
        "distinct_places": len(strings),
        "readings": sum(strings.values()),
        "strings": {b: by_string.get(b, 0) for b in BUCKETS},
        "readings_by_bucket": {b: readings.get(b, 0) for b in BUCKETS},
        "persons_by_bucket": {b: by_person.get(b, 0) for b in BUCKETS},
        "persons_without_a_place": by_person.get("no_places", 0),
        "strings_by_basis": {k: how.get(k, 0) for k in DERIVATIONS + ("ruled",)},
    }


def gazetteer_strings() -> set[str]:
    return {place for person in load(GAZETTEER)["persons"]
            for place in places_of(person)}


# ---------------------------------------------------------------------------
# --check: the gate
# ---------------------------------------------------------------------------

def problems(doc: dict, printed: set[str]) -> list[str]:
    """Every way `doc` fails to be a complete, honest resolution of `printed`.

    Split out from `check()` so `--self-test` can break a copy of the corpus and watch
    each assertion fire. A gate step nobody has seen fail is a gate step nobody knows
    is wired up.
    """
    entries = doc["places"]
    boundaries = doc["boundaries"]
    bad: list[str] = []

    held = [e["place"] for e in entries]
    duplicates = [p for p, n in collections.Counter(held).items() if n > 1]
    for place in duplicates:
        bad.append(f"{place!r}: resolved twice; one ruling per printed string")
    for place in sorted(printed - set(held)):
        bad.append(f"{place!r}: printed in the gazetteer and not resolved here")
    for place in sorted(set(held) - printed):
        bad.append(f"{place!r}: resolved here and no longer printed in the gazetteer")

    for entry in entries:
        place = entry["place"]
        if entry.get("resolution") not in BUCKETS:
            bad.append(f"{place!r}: resolution {entry.get('resolution')!r} "
                       f"is not one of {BUCKETS}")
            continue

        now = derive(place)
        claimed = entry.get("derived")
        if claimed:
            if not now:
                bad.append(f"{place!r}: claims derivation {claimed['how']} and the "
                           f"committed dataset no longer derives it at all")
            elif now["how"] != claimed["how"] or now["matched"] != claimed["matched"]:
                bad.append(f"{place!r}: derived as {claimed['how']} "
                           f"{claimed['matched']} and now derives as {now['how']} "
                           f"{now['matched']}")
            elif entry["resolution"] != "inside":
                bad.append(f"{place!r}: a derivation reads the committed town and can "
                           f"only say `inside`, not {entry['resolution']!r}")
        else:
            if now:
                bad.append(f"{place!r}: ruled by hand, and the committed dataset now "
                           f"derives it as {now['how']} {now['matched']} — take the "
                           f"derivation (run --write)")
            if entry.get("basis") not in boundaries:
                bad.append(f"{place!r}: basis {entry.get('basis')!r} is not a "
                           f"boundary this corpus declares")
            if not (entry.get("note") or "").strip():
                bad.append(f"{place!r}: ruled by hand and states no reasoning; a "
                           f"ruling derivation cannot reach must say why")

        for structure_id in entry.get("structures") or []:
            if not (STRUCTURES / f"{structure_id}.json").exists():
                bad.append(f"{place!r}: names structure {structure_id!r}, "
                           f"which is not committed")
        for street_id in entry.get("streets") or []:
            if street_id not in committed_street_ids():
                bad.append(f"{place!r}: names street {street_id!r}, "
                           f"which is not committed")

    stated, now = doc.get("counts"), counts()
    if stated != now:
        for key in sorted(set(stated or {}) | set(now)):
            if (stated or {}).get(key) != now.get(key):
                bad.append(f"counts.{key}: states {(stated or {}).get(key)!r}, "
                           f"measures {now.get(key)!r}")
    return bad


def check() -> int:
    bad = problems(load(VOCABULARY), gazetteer_strings())
    if bad:
        print(f"resolve_place_vocabulary: {len(bad)} problem(s)")
        for line in bad[:40]:
            print(f"  {line}")
        if len(bad) > 40:
            print(f"  ... and {len(bad) - 40} more")
        return 1

    c = counts()
    print(f"resolve_place_vocabulary: {c['distinct_places']} printed place(s) "
          f"resolved — {c['strings']['inside']} inside, "
          f"{c['strings']['outside']} outside, "
          f"{c['strings']['undecided']} undecided; "
          f"{c['strings_by_basis']['ruled']} ruled, "
          f"{c['distinct_places'] - c['strings_by_basis']['ruled']} derived")
    return 0


def write() -> int:
    """Recompute the derivations and the counts; carry every hand ruling forward."""
    doc = load(VOCABULARY)
    existing = {e["place"]: e for e in doc["places"]}
    rebuilt = []
    for place in sorted(gazetteer_strings()):
        entry = dict(existing.get(place) or {"place": place, "resolution": "undecided",
                                            "basis": "B4", "note": ""})
        entry["place"] = place
        derived = derive(place)
        if derived:
            entry["resolution"] = "inside"
            entry["derived"] = derived
            entry.pop("basis", None)
            entry.pop("note", None)
        else:
            entry.pop("derived", None)
        rebuilt.append({k: entry[k] for k in
                        ("place", "resolution", "derived", "basis", "what", "note",
                         "structures", "streets", "tickets") if k in entry})
    doc["places"] = rebuilt
    _cache.pop("vocabulary", None)
    _cache["vocabulary"] = {e["place"]: e for e in rebuilt}
    doc["counts"] = counts()
    VOCABULARY.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    print(f"resolve_place_vocabulary: wrote {len(rebuilt)} place(s) "
          f"to {VOCABULARY.relative_to(ROOT)}")
    return 0


def report() -> int:
    c = counts()
    print(f"THE NEWSPAPERS' PLACE VOCABULARY (T-1048)\n")
    print(f"  {c['persons']} gazetteer person(s), {c['persons_with_a_place']} of them "
          f"carrying at least one place")
    print(f"  {c['distinct_places']} distinct printed place string(s), "
          f"{c['readings']} reading(s) of them\n")
    print("  strings          inside {inside:4d}   outside {outside:4d}   "
          "undecided {undecided:4d}".format(**c["strings"]))
    print("  readings         inside {inside:4d}   outside {outside:4d}   "
          "undecided {undecided:4d}".format(**c["readings_by_bucket"]))
    print("  persons          inside {inside:4d}   outside {outside:4d}   "
          "undecided {undecided:4d}".format(**c["persons_by_bucket"])
          + f"   (and {c['persons_without_a_place']} carrying no place at all)\n")
    print("  by basis         " + "   ".join(
        f"{k} {v}" for k, v in c["strings_by_basis"].items()))

    for bucket in BUCKETS:
        rows = [e for e in vocabulary().values() if e["resolution"] == bucket]
        print(f"\n  --- {bucket.upper()} ({len(rows)}) ---")
        for entry in sorted(rows, key=lambda e: e["place"].lower()):
            how = (entry.get("derived") or {}).get("how") or entry.get("basis", "?")
            print(f"    {how:15s} {entry['place']}")
    return 0


def self_test() -> int:
    """Break a copy of the corpus six ways and watch `--check` catch each one.

    Every case here is a way the corpus could rot quietly in a later commit: a new notice
    extracted next week brings a place string nobody has resolved; a structure is renamed
    and a derivation stops deriving; a hand ruling is written over a string the dataset
    can now answer for itself; a count is edited by hand instead of restamped.
    """
    import copy

    good = load(VOCABULARY)
    printed = gazetteer_strings()
    assert not problems(good, printed), "the committed corpus must be clean to test against"

    cases = []

    def case(name: str, mutate, expect: str):
        doc = copy.deepcopy(good)
        mutate(doc)
        found = problems(doc, printed)
        hit = any(expect in line for line in found)
        cases.append((name, hit, found[:2]))

    def drop_an_entry(doc):
        doc["places"] = [e for e in doc["places"] if e["place"] != "Hennepin"]

    def invent_an_entry(doc):
        doc["places"].append({"place": "Timbuctoo", "resolution": "outside",
                              "basis": "B2", "note": "not printed anywhere"})

    def unreason_a_ruling(doc):
        for e in doc["places"]:
            if e["place"] == "Hennepin":
                e["note"] = "   "

    def refuse_the_fort(doc):
        for e in doc["places"]:
            if e["place"] == "Fort Dearborn":
                e["resolution"] = "outside"
                e["structures"] = ["fort_dearborn_no_such_thing"]

    def lie_about_a_derivation(doc):
        for e in doc["places"]:
            if e["place"] == "the Mansion House":
                e["derived"] = {"how": "structure", "matched": ["tremont_house_1"]}

    def rule_over_a_derivation(doc):
        for e in doc["places"]:
            if e["place"] == "the Mansion House":
                e.pop("derived")
                e["basis"], e["note"] = "B3", "ruled by hand over a live derivation"

    def edit_a_count(doc):
        doc["counts"]["distinct_places"] = 127

    def invent_a_boundary(doc):
        for e in doc["places"]:
            if e["place"] == "Hennepin":
                e["basis"] = "B9"

    case("a printed string nobody resolved", drop_an_entry, "not resolved here")
    case("a ruling on a string the papers do not print", invent_an_entry,
         "no longer printed in the gazetteer")
    case("a hand ruling with no reasoning", unreason_a_ruling, "states no reasoning")
    case("a ruling naming a structure the town does not hold", refuse_the_fort,
         "which is not committed")
    case("a derivation that no longer matches the dataset", lie_about_a_derivation,
         "and now derives as")
    case("a hand ruling written over a live derivation", rule_over_a_derivation,
         "take the derivation")
    case("a count edited by hand", edit_a_count, "counts.distinct_places")
    case("a basis this corpus does not declare", invent_a_boundary,
         "not a boundary this corpus declares")

    failed = [c for c in cases if not c[1]]
    for name, hit, found in cases:
        print(f"  {'caught' if hit else 'MISSED'}  {name}")
        if not hit:
            print(f"            saw instead: {found}")
    print(f"resolve_place_vocabulary --self-test: {len(cases) - len(failed)}"
          f"/{len(cases)} assertion(s) fire when broken")
    return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="hold the corpus to the gazetteer and the committed town")
    parser.add_argument("--self-test", action="store_true",
                        help="break a copy of the corpus and watch --check catch it")
    parser.add_argument("--write", action="store_true",
                        help="recompute derivations and counts, keeping hand rulings")
    parser.add_argument("--report", action="store_true", help="the three buckets")
    parser.add_argument("--place", action="append", default=[],
                        help="resolve one printed place and say how")
    args = parser.parse_args()

    for place in args.place:
        derived = derive(place)
        entry = vocabulary().get(place)
        how = (f"derived {derived['how']} {derived['matched']}" if derived
               else f"ruled {entry.get('basis')}: {entry.get('note')}" if entry
               else "not in the corpus")
        print(f"  {place!r} -> {resolution_of(place)} ({how})")
    if args.place:
        return 0
    if args.self_test:
        return self_test()
    if args.write:
        return write()
    if args.report:
        return report()
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
