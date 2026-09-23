#!/usr/bin/env python3
"""The six enrichments that name a DEPARTURE from Chicago, ruled one at a time (T-1354).

    python3 tools/spend_departure_rulings.py             what each of the six rules
    python3 tools/spend_departure_rulings.py --write     write the derived register
    python3 tools/spend_departure_rulings.py --check     it re-derives; nothing drifted
    python3 tools/spend_departure_rulings.py --self-test the rules below, over the rows

WHY THIS EXISTS. T-1330 read all thirty `corroborated_enrichment` arrival-and-origin
units one at a time. Six of them name a GOING rather than a coming -- a removal, a
migration to another town, a prospecting journey that ended somewhere else -- for six men
this town holds cards for. No field on a resident card carries a departure. The only
thing a removal bears on is `present_on_scene_date`, so all six were handed to the ticket
whose acceptance owns that field, and a hand-off is not a spend: they were handed to
T-1144, then, when T-1144 split, to whichever child happened to be open (#1471, #1489),
and neither child's acceptance owned spending a departure onto a presence. T-1354 owns
it. This is the spend.

WHAT A RULING IS HERE, and it has exactly two shapes.

  1. THE REMOVAL REACHES THE SCENE DATE, and the presence carries it. One of the six:
     Joseph Porthier left Chicago with Horace Chase on 27 February 1835 and reached
     Milwaukee on 23 March, and T-0478 had already read that chronology and moved his
     `present_on_scene_date` to `absent` at `attested`, citing the volume the finding
     names. The ruling re-reads it beside the card's other sources, finds nothing further
     to move, and asserts nothing over it.

  2. THE REMOVAL DOES NOT REACH THE SCENE DATE, and saying so is a ruling rather than a
     skip. Five of the six, and they miss in three different ways: a removal dated AFTER
     1 July 1835 (Caldwell's, Jones's), a removal dated only to the YEAR the scene falls
     in and therefore standing on both sides of the day (Sweet's), and a going with no
     date on it at all (Pugsley's, Cleland's).

  3. NOTHING ELSE. `--self-test` refuses a third outcome.

THE RULE THAT ORDERS ALL SIX: A REMOVAL IS READ BESIDE THE OTHER SOURCES ON THE CARD,
never out of the one volume it came in. A departure read alone is how a layer loses a
resident it had evidence for -- it is the one direction in which this dataset can delete
a documented person on a single late compiler's say-so, and five of these six volumes are
retrospective county, city or family histories. So every row below names what it was read
against, and `--check` re-reads the card each ruling stands on: a presence that moves
under one of these rulings turns this gate red, which is the point of writing them down.

WHAT THIS PASS MAY NOT DO.

  * IT MOVES NO PRESENCE TODAY AND WRITES ONTO NO CARD. All six presences stand where
    the readings already put them. The moving case is still a rule -- a ruling whose
    `presence_after` differs from its `presence_before` must name the prior value, the
    tier and the reason -- and `--self-test` holds that rule over a fixture rather than
    over the tree, because no row fires it.
  * IT MOVES NO GRADE AND RETIRES NO CARD. A departure is evidence about a DATE, not
    about whether the man existed. `--self-test` asserts that every row's `presence_after`
    is the value the committed card carries.
  * IT DOES NOT RESOLVE A CONFLICT THE CARD RETAINS. Caldwell's 1835-against-1836 removal
    year is a dated conflict the card holds in terms; this ruling says only that both
    datings fall after the scene date, which is the one thing the conflict does not touch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
REGISTER = ROOT / "data" / "research" / "residents" / "spend_rulings.json"
OUT = ROOT / "data" / "research" / "residents" / "departure_rulings.json"

TICKET = "T-1354"
GENERATOR = "tools/spend_departure_rulings.py"
# The rule in the remainder register whose six units this pass rules. The register is the
# corpus: this file may not invent a seventh departure and may not quietly drop one.
REGISTER_RULE = "the_enrichment_names_a_departure_from_chicago_no_field_carries"
OUTCOMES = ("already_written_onto_the_presence", "does_not_reach_the_scene_date")
SCENE_DATE = "1835-07-01"

# THE SIX, each read beside the card rather than out of its own volume.
RULINGS = {
    "caldwell_billy": {
        "household": "hh_caldwell_billy.json",
        "finding": "data/research/residents/pass_02_75_cohort.json#people/caldwell_billy",
        "sources": ["encyclopedia_chicago_potawatomis"],
        "removal": (
            "Institutional histories corroborate Billy Caldwell's Chicago leadership and "
            "place the westward removal in 1835, against the 1836 migration Andreas and "
            "this project's own language carry."),
        "read_beside": [
            "hh_caldwell_billy.json#present_on_scene_date — Andreas has him leading the "
            "assembly and the march to the Missouri in 1836",
            "chicagology_lastwardance, cited in the same block — the last war dance at "
            "Chicago on 18 August 1835",
            "AGENTS.md's standing constraint — the final removal of the Potawatomi from "
            "Chicago was August 1835, six weeks after the scene date",
        ],
        "outcome": "does_not_reach_the_scene_date",
        "presence_before": "present",
        "presence_after": "present",
        "ruling": (
            "THREE DATINGS ARE NOW HELD AND EVERY ONE OF THEM FALLS AFTER 1 JULY 1835: "
            "Andreas's march to the Missouri in 1836, the last war dance at Chicago on 18 "
            "August 1835, and this volume's bare year. Read beside the other two rather "
            "than off its own page, the bare 1835 IS the August removal they date — there "
            "is no second removal in that year for it to be. The card already says so in "
            "terms, so the removal moves nothing. The conflict between 1835 and 1836 is a "
            "conflict about which summer he left, not about whether he was at Chicago in "
            "July, and it is retained where the card retains it rather than resolved here."),
    },
    "jones_benjamin": {
        "household": "hh_jones_benjamin.json",
        "finding": "data/research/residents/pass_03_75_cohort.json#people/jones_benjamin",
        "sources": ["loc_mantowoc_benjamin_jones"],
        "removal": (
            "A Library of Congress engineering history identifies Benjamin Jones as a "
            "Chicago merchant and land speculator who bought at the Manitowoc River mouth "
            "in 1835 and settled there in 1836."),
        "read_beside": [
            "hh_jones_benjamin.json#present_on_scene_date.last_dated_appearance — the "
            "corpus holds no sighting, only chicago_democrat_1833_11_26's span reaching "
            "1833-11-30, 578 days short of the scene date",
            "hh_jones_benjamin.json#arrival — 1833-11-07 attested, the day the trustees "
            "appointed him street commissioner",
            "the finding's own words: 'This supplies a dated migration lead, not a 1 July "
            "address.'",
        ],
        "outcome": "does_not_reach_the_scene_date",
        "presence_before": "uncertain",
        "presence_after": "uncertain",
        "ruling": (
            "A PURCHASE AT ANOTHER RIVER MOUTH IS NOT A DEPARTURE FROM THIS TOWN, and the "
            "settlement it led to is dated 1836 — after the scene date, so it moves "
            "nothing. It does not move the presence the other way either: the volume calls "
            "him a Chicago merchant, which is an epithet and not a dated sighting, and the "
            "card's last dated appearance is still a source's span ending in November "
            "1833. `uncertain` is what the evidence pays for and it stands."),
    },
    "porthier_joseph": {
        "household": "hh_porthier_joseph.json",
        "finding": "data/research/residents/pass_04_75_cohort.json#people/porthier_joseph",
        "sources": ["buck_pioneer_milwaukee_porthier_1835"],
        "removal": (
            "Pioneer History of Milwaukee dates Joseph Porthier leaving Chicago with "
            "Horace Chase on 27 February 1835; after a brief return to Chicago for means "
            "he left again on 21 March and reached Milwaukee on 23 March."),
        "read_beside": [
            "hh_porthier_joseph.json#present_on_scene_date — already `absent` at "
            "`attested`, citing this same volume beside andreas_1884_v1, moved by T-0478",
            "hh_porthier_joseph.json#research_note — the agency payroll that documents him "
            "at all, and the same February–March chronology",
            "no committed source places him back at Chicago between 23 March and 1 July 1835",
        ],
        "outcome": "already_written_onto_the_presence",
        "presence_before": "absent",
        "presence_after": "absent",
        "ruling": (
            "THIS IS THE ONE DEPARTURE OF THE SIX THAT REACHES THE SCENE DATE, AND IT WAS "
            "SPENT BEFORE THIS TICKET EXISTED. T-0478 read the same chronology and moved "
            "the presence to `absent` at `attested`, citing this volume. Re-read beside "
            "the card's other sources there is nothing further to move: the brief return "
            "for means is the source's own and sits inside the same February–March "
            "sequence, the last leg reaches Milwaukee on 23 March, and nothing committed "
            "puts him back here before 1 July. `absent` stands and this ticket asserts "
            "nothing over it. The row is kept because a spend that is invisible to the "
            "register reads as an unspent unit to the next pass, which is how this one "
            "was handed on three times."),
    },
    "sweet_alanson": {
        "household": "hh_sweet_alanson.json",
        "finding": "data/research/residents/pass_04_75_cohort.json#people/sweet_alanson",
        "sources": ["buck_pioneer_milwaukee_alanson_sweet"],
        "removal": (
            "Milwaukee histories identify Alanson Sweet as an early Chicago stone mason "
            "who moved to Milwaukee in 1835; the reviewed passage supplies no sufficiently "
            "safe departure day."),
        "read_beside": [
            "hh_sweet_alanson.json#present_on_scene_date.last_dated_appearance — a "
            "source's span of 1673/1857 that COVERS the scene date and pins no sighting "
            "before it",
            "hh_sweet_alanson.json#arrival — 1832, attested, and corroborated at year "
            "precision by an 1895 compiler",
            "hh_sweet_alanson.json#research_note — 'What Sweet was doing on 1 July 1835 is "
            "not stated anywhere reached.'",
        ],
        "outcome": "does_not_reach_the_scene_date",
        "presence_before": "uncertain",
        "presence_after": "uncertain",
        "ruling": (
            "A REMOVAL DATED TO THE YEAR THE SCENE FALLS IN CANNOT BE PLACED AGAINST A DAY "
            "INSIDE IT. 1835 lies on both sides of 1 July and the passage refuses to "
            "choose — its own reviewer says so. So this cannot carry the presence to "
            "`absent`, and reading it as though it could is exactly how a layer loses a "
            "resident it had evidence for. Nor does it argue the other way: the card holds "
            "no sighting at all, only a source's span. `uncertain` stands, and it is now "
            "uncertain for a stated reason rather than for want of a reading."),
    },
    "pugsley_john_k": {
        "household": "hh_pugsley_john_k.json",
        "finding": "data/research/residents/pass_09_75_cohort.json#people/pugsley_john_k",
        "sources": ["resident_research_pugsley_barrien_vanburen"],
        "removal": (
            "An 1880 Van Buren County history says John K. Pugsley left near Utica, New "
            "York in June 1835, travelled to Chicago, prospected there, then returned to "
            "Paw Paw Township, Michigan, and entered land."),
        "read_beside": [
            "hh_pugsley_john_k.json#present_on_scene_date — `present` at `inferred`, off a "
            "letter still waiting for the name at the Democrat's return of 1 July 1835",
            "hh_pugsley_john_k.json#arrival — 1835-06-30, a bound from that return and not "
            "an arrival (T-0425)",
            "hh_pugsley_john_k.json#origin — 'Near Utica, New York', already spent out of "
            "this same volume by T-1232",
            "the finding's own evidence_against: 'he may have left Chicago before July 1, "
            "so the source does not prove scene-date bodily presence.'",
        ],
        "outcome": "does_not_reach_the_scene_date",
        "presence_before": "present",
        "presence_after": "present",
        "ruling": (
            "THE GOING HERE CARRIES NO DATE. The history dates the setting out — June 1835 "
            "— and not the return to Paw Paw, and an undated departure cannot be placed "
            "before a day. The one dated thing the passage supplies is a journey TO "
            "Chicago in the very month the card's own bound falls in, which corroborates "
            "the postal identity and argues for the presence rather than against it. So "
            "the presence stands where the return put it — at `present`, at `inferred`, "
            "and not a rung above: the finding's own note that he may have left before 1 "
            "July is why this reading does not promote the grade, and the letter list was "
            "never a sighting of a body in the first place. It says somebody was writing "
            "to this name at this town."),
    },
    "cleland_martin": {
        "household": "hh_cleland_martin.json",
        "finding": "data/research/residents/pass_10_75_cohort.json#people/cleland_martin",
        "sources": ["chicago_democrat_1833_1835", "marsh_genealogy_martin_cleland_1886"],
        "removal": (
            "An 1886 family genealogy has Martin Cleland travelling from Chautauqua, New "
            "York to Chicago on a prospecting tour in 1834 and selecting a future home "
            "near Niles, Michigan; the family moved west in 1835."),
        "read_beside": [
            "hh_cleland_martin.json#present_on_scene_date.last_dated_appearance — "
            "1834-07-09, a dated reading of this person and the last the corpus holds, 357 "
            "days short of the scene date",
            "hh_cleland_martin.json#arrival — 1834-07-01, the letter-list return the "
            "sighting belongs to, a bound and not an arrival",
            "hh_cleland_martin.json#origin — 'Chautauqua, New York', already spent out of "
            "this same genealogy by T-1232",
            "the finding's own words: 'the Niles destination prevents a July 1835 "
            "Chicago-residence inference.'",
        ],
        "outcome": "does_not_reach_the_scene_date",
        "presence_before": "uncertain",
        "presence_after": "uncertain",
        "ruling": (
            "BOTH LEGS FALL OUTSIDE THE QUESTION. The tour is dated 1834, a year before "
            "the scene, and the move it led to is dated only to 1835 and is a move to "
            "MICHIGAN — neither places him at Chicago, or away from it, on 1 July 1835. "
            "What the volume does change is what the card's one dated leg MEANS: the "
            "return of 1 July 1834 is the tail of a prospecting visit that chose somewhere "
            "else, not the tail of a residence. That is recorded here rather than written "
            "over a verdict the leg already carries, because the leg is the evidence under "
            "the verdict and not a new claim. `uncertain` stands."),
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def register_units(register: Path = REGISTER) -> list[str]:
    """The person ids the remainder register hands this ticket, from the register itself."""
    doc = read_json(register)
    return sorted(row["unit"].split("#people/")[1]
                  for row in doc.get("rulings") or [] if row.get("rule") == REGISTER_RULE)


def presence_now(person_id: str, households: Path = HOUSEHOLDS) -> dict:
    """The verdict the committed card carries, which is what each ruling stands on."""
    path = households / RULINGS[person_id]["household"]
    block = read_json(path).get("present_on_scene_date") or {}
    return {"value": block.get("value"), "confidence": block.get("confidence"),
            "sources": sorted(block.get("sources") or [])}


def moved(row: dict) -> bool:
    return row["presence_before"] != row["presence_after"]


def build_document(households: Path = HOUSEHOLDS) -> dict:
    rulings = []
    for person_id in sorted(RULINGS):
        row = RULINGS[person_id]
        rulings.append({
            "person": person_id,
            "household": row["household"],
            "unit": f"residents:{row['finding']}",
            "sources": sorted(row["sources"]),
            "removal": row["removal"],
            "read_beside": list(row["read_beside"]),
            "outcome": row["outcome"],
            "presence_before": row["presence_before"],
            "presence_after": row["presence_after"],
            "presence_on_the_card": presence_now(person_id, households),
            "ruling": row["ruling"],
        })
    counts = {name: sum(1 for r in rulings if r["outcome"] == name) for name in OUTCOMES}
    return {
        "schema": "resident-departure-rulings-v1",
        "_doc": (
            f"DERIVED, {TICKET}, by {GENERATOR} from the six `corroborated_enrichment` units "
            "the remainder register hands this ticket and the resident cards they name -- run "
            "--check to re-derive it. Each of the six names a DEPARTURE from Chicago, which "
            "no field on a resident card carries: the only thing a removal bears on is "
            "`present_on_scene_date`. Every row is ruled ONE AT A TIME with the removal read "
            "BESIDE the other sources on the card rather than out of the single volume it "
            "came in, because a departure read alone is how a layer loses a resident it had "
            "evidence for. NOTHING HERE MINTS A PERSON, MOVES A GRADE, RETIRES A CARD OR "
            "INVENTS A CITATION, and today nothing here moves a presence either: five of the "
            "removals do not reach the scene date and the sixth was already written onto its "
            "card by T-0478. `presence_on_the_card` is re-read from the card on every "
            "derivation, so a presence that moves under one of these rulings turns this "
            "register's gate red."),
        "ticket": TICKET,
        "generated_by": GENERATOR,
        "scene_date": SCENE_DATE,
        "counts": counts,
        "rulings": rulings,
    }


def write(doc: dict) -> None:
    OUT.write_text(dumps(doc), encoding="utf-8")


def report() -> int:
    doc = build_document()
    for row in doc["rulings"]:
        mark = "→" if row["presence_before"] != row["presence_after"] else "·"
        print(f"  {row['person']:<18} {row['outcome']:<34} "
              f"{row['presence_before']} {mark} {row['presence_after']}")
    print(f"\n{len(doc['rulings'])} ruling(s): "
          + ", ".join(f"{k} {v}" for k, v in doc["counts"].items()))
    if OUT.exists() and read_json(OUT) == doc:
        print(f"{OUT.relative_to(ROOT)} is current")
    else:
        print(f"{OUT.relative_to(ROOT)} would change — run --write")
    return 0


def check(quiet: bool = False) -> int:
    doc = build_document()
    if not OUT.exists():
        print(f"FAIL {OUT.relative_to(ROOT)} is missing — run {GENERATOR} --write")
        return 1
    if read_json(OUT) != doc:
        print(f"FAIL {OUT.relative_to(ROOT)} is stale — run {GENERATOR} --write")
        return 1
    faults = []
    # THE RULING STANDS ON THE CARD, so the card is re-read rather than remembered.
    for row in doc["rulings"]:
        on_card = row["presence_on_the_card"]["value"]
        if on_card != row["presence_after"]:
            faults.append(f"{row['person']}: the ruling leaves the presence "
                          f"{row['presence_after']!r} and the card carries {on_card!r}")
    # AND THE CORPUS IS THE REGISTER'S, not this file's. A seventh departure arriving, or
    # one of the six leaving, is a change of subject and must be ruled rather than ignored.
    known = set(register_units())
    for person_id in sorted(known - set(RULINGS)):
        faults.append(f"{person_id}: a departure unit this pass never ruled")
    for person_id in sorted(set(RULINGS) - known):
        faults.append(f"{person_id}: ruled here and not among the units this ticket owns")
    for line in faults:
        print(f"FAIL {line}")
    if faults:
        return 1
    if not quiet:
        print(f"OK departure rulings re-derive: {len(doc['rulings'])} units, "
              + ", ".join(f"{k} {v}" for k, v in doc["counts"].items()))
    return 0


def self_test() -> int:
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append(f"{label}: got {got!r}, wanted {want!r}")

    doc = build_document()

    # 1. THE CORPUS IS THE REGISTER'S, in both directions.
    holds("the six units are the register's six",
          sorted(RULINGS), register_units())

    # 2. NO THIRD OUTCOME. There are two shapes of ruling and a row may not invent one.
    holds("every row reaches a stated outcome",
          sorted({r["outcome"] for r in doc["rulings"]} - set(OUTCOMES)), [])
    holds("both stated outcomes fire over the committed corpus",
          sorted(k for k, v in doc["counts"].items() if v == 0), [])

    # 3. EVERY ROW SAYS WHAT IT WAS READ AGAINST. A removal read out of one volume, with
    #    nothing beside it, is the failure this whole ticket exists to refuse — so a row
    #    that names fewer than two other legs is not a ruling, it is a transcription.
    holds("every ruling names at least two things it was read beside",
          sorted(p for p, r in RULINGS.items() if len(r["read_beside"]) < 2), [])
    holds("every ruling states itself at length",
          sorted(p for p, r in RULINGS.items() if len(r["ruling"].strip()) < 120), [])

    # 4. NO SILENT PASS. Six rulings for six units, one each.
    holds("one ruling per unit", len({r["unit"] for r in doc["rulings"]}), 6)

    # 5. EVERY ROW CITES THE FINDING'S OWN VOLUME and nothing it made up.
    register = read_json(REGISTER)
    noted = {row["unit"].split("#people/")[1]: row["note"]
             for row in register.get("rulings") or [] if row.get("rule") == REGISTER_RULE}
    holds("every citation appears in the finding it rules",
          sorted(f"{p}:{s}" for p, r in RULINGS.items() for s in r["sources"]
                 if p in noted and s not in noted[p]), [])

    # 6. THE PRESENCE A RULING LEAVES IS THE PRESENCE THE CARD CARRIES. This is the one
    #    that goes red if a later pass moves one of these six.
    holds("every ruling stands on the committed card",
          sorted(p for p in RULINGS if presence_now(p)["value"] != RULINGS[p]["presence_after"]),
          [])

    # 7. THE MOVING CASE IS STILL A RULE, held over a fixture because no row fires it:
    #    a ruling that moves a presence has to name the prior value, and one that does not
    #    move it may not pretend to.
    holds("a row that moves is detected",
          moved({"presence_before": "uncertain", "presence_after": "absent"}), True)
    holds("a row that stands is not",
          moved({"presence_before": "uncertain", "presence_after": "uncertain"}), False)
    holds("no row moves a presence today",
          sorted(p for p, r in RULINGS.items() if moved(r)), [])

    for line in failures:
        print(f"FAIL {line}")
    print(f"DEPARTURE RULING SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), {len(RULINGS)} unit(s), {len(OUTCOMES)} outcome(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write the derived register")
    parser.add_argument("--check", action="store_true", help="re-derive and prove nothing drifted")
    parser.add_argument("--self-test", action="store_true", help="hold the rules over the rows")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check(args.quiet)
    if args.write:
        doc = build_document()
        write(doc)
        print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['rulings'])} rulings")
        for name, n in doc["counts"].items():
            print(f"  {n:5d}  {name}")
        return 0
    return report()


if __name__ == "__main__":
    sys.exit(main())
