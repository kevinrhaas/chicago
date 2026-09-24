#!/usr/bin/env python3
"""T-1386 — stage `presence_rulings`: the people the project already knows, ruled into the town.

    python3 tools/rule_presence_1835.py --build      write the rulings
    python3 tools/rule_presence_1835.py --check      re-derive them byte-for-byte
    python3 tools/rule_presence_1835.py --report     the rulings, counted
    python3 tools/rule_presence_1835.py --self-test  the rules, broken on purpose

THE OWNER, 2026-09-19: *"You should not be so dogmatic about the scene date, put more of
those attested people back into the population, I want a full population of the city to
work from."* And, the same morning, the rule behind it: *"if they are attested that's ideal
if we know them already."*

WHAT WAS WRONG. Of the 2,269 people the resident layer carries, 827 sat outside the town's
population on `present_on_scene_date: uncertain` — 276 of them graded `attested`, 550
`inferred` — while 983 of the 984 the project RECONSTRUCTED were ruled `present`, because
the reconstruction stages rule a presence as they mint one. The layer believed in the people
it made up and was undecided about the people it read. That ordering is not evidentiary
caution; it is an artefact of which code path happens to write a presence. Two cards, and
only two, were out on evidence of absence.

WHAT THIS STAGE DOES. It rules all 827 `present` and says, on each one, HOW that was
reached. `uncertain` here never meant disputed — it meant unadjudicated, and every one of
these people has attested or inferred evidence of living in this town and none has evidence
of being anywhere else on 1 July 1835. T-1144's rule is "no false Chicago resident": it
refuses INVENTING a resident and does not ask the layer to forget one it has read.

THE TIER IS DERIVED FROM THE CARD'S OWN DATED READINGS, never from its class. A blanket
flip would put an undeclared claim on 276 cards, which is the fault this stage exists to
prevent, so each ruling's tier is whichever of three legs the card's own evidence reaches —
read out of `tools/derive_presence_evidence_leg.py`'s candidate extraction, the same
structured blocks the evidence leg is derived from (never prose):

  1. `attested` — `on_the_day`: the card holds a dated READING of this person whose window
     contains 1 July 1835. A record dated `1835-07`, or `1835`, is a reading of the person
     in a window that covers the day; it is an appearance and it is the strongest thing a
     card can hold about a date. 61 people.
  2. `inferred` — attested evidence places them in the town in a window that SPANS the day
     without pinning it, in one of two shapes:
       * `spans` — a role whose source-span runs through 1 July 1835. The span is the
         source's bound and not the person's, which is why it is an inference and not a
         sighting, and it is why `derive_presence_evidence_leg.py` refuses to let a span
         outrank a sighting. 55 people.
       * `bracketed` — the corpus reads this person at Chicago at or before the day AND
         again at or after it. Residence across a day the sources see both sides of is an
         inference from attested evidence, not a draw. 32 people.
  3. `reconstructed` — `carried`: the corpus stops before the day and nothing follows. What
     carries the presence here is the project's own standing rule — an attested or inferred
     resident is in the population unless there is evidence they were not — and the
     persistence model measured for T-1172 prices it, so the ruling states the lag and the
     persistence rather than implying a reading nobody made. 679 people.

WHY THE PERSISTENCE IS PRICED AND NOT DRAWN. T-1172's stage drew against `persistence(L)`
and ruled 37 cards `absent` on the losing side of the draw. This stage does not: a draw that
puts a known resident out of the town is a claim of absence with no evidence under it, and
the ticket's rule is that the two EVIDENCED absences are the shape of a correct exclusion.
The persistence figure is therefore carried as what it is — how much of this layer a later
Chicago volume still names, at this card's lag — and the ruling is `present` either way.
`basis.kind` is `rule` for that reason, and a rule owes no seed: nothing is drawn here.

AND IT IS NOT A DOWNGRADE (acceptance 3). T-1172's R1 leg re-ruled every `uncertain`
presence at tier `reconstructed`; for a person whose residence is attested and whose reading
covers the day itself, that is a downgrade dressed as progress. 142 of these 820 rulings
land above `reconstructed` on their own evidence, which is the measure of the fix. The
presence tier is a claim about ONE DAY and is a different claim from the card's residence
grade: a card graded `attested` whose last reading is a year before the scene keeps its
attested residence and takes a `reconstructed` presence, because the presence really is
carried by the rule. Saying `inferred` there would be the undeclared claim again.

WHERE THE WRITES GO, AND WHY NOT INTO THE CARDS. `data/residents/households/` is derived:
the mint writers re-derive it drift-zero and `data/residents/index.json` is a summary of
THAT directory and nothing else (T-0715). A ruling is not a mint output and must not
pretend to be one, so it lives here, in `data/reconstruction/1835_presence_rulings.json`,
and the four consumers the ticket names read it: `tools/town_census.py` (both figures),
`tools/profile_population_1835.py`, `tools/build_order_book_1835.py` and the gate screen
through the census. The inferred `uncertain` each ruling stands beside stays on the card.

NOT IN SCOPE. Nobody is invented and no refusal is overturned: this stage adds no name, and
every row names a person the layer already holds. Re-cutting the roof programme against the
bigger population is T-1196's; converging the layer is T-1179's.
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from derive_presence_evidence_leg import candidates  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
READMISSIONS = ROOT / "data" / "reconstruction" / "1835_readmissions.json"
OUT = ROOT / "data" / "reconstruction" / "1835_presence_rulings.json"
GENERATOR = "tools/rule_presence_1835.py"
SCENE_DATE = "1835-07-01"

# The three legs, strongest first. The first one the card reaches wins outright.
LEGS = ("on_the_day", "spans", "bracketed", "carried")
LEG_TIER = {"on_the_day": "attested", "spans": "inferred",
            "bracketed": "inferred", "carried": "reconstructed"}
GRADES = ("attested", "inferred", "reconstructed")


def read_json(path: pathlib.Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dumps(doc) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def persistence_model() -> dict:
    """T-1172's measured rate, read from its own output rather than restated here."""
    return read_json(READMISSIONS)["persistence_model"]


def years_before_scene(day: str) -> float:
    """Years from `day` to the scene date, by the same 365.2425-day year T-1172 used."""
    import datetime as dt
    a = dt.date.fromisoformat(day)
    b = dt.date.fromisoformat(SCENE_DATE)
    return round((b - a).days / 365.2425, 4)


def residence_grade(doc: dict) -> str:
    """The strongest grade the household's people carry for living here at all."""
    grades = {str(p.get("grade")) for p in doc.get("persons") or []}
    for grade in GRADES:
        if grade in grades:
            return grade
    return "reconstructed"


def reading_for(doc: dict) -> dict:
    """Which leg this card reaches, and the reading that put it there.

    Pure over the card: every candidate comes from a structured block, and the winner
    inside a leg is the one whose reading reaches furthest, then the narrower precision,
    then the record id — so nothing here depends on dict order.
    """
    rows = candidates(doc)
    sightings = [c for c in rows if c["tier"] == "sighting"]
    spans = [c for c in rows if c["tier"] == "source_span"]

    def best(pool):
        return sorted(pool, key=lambda c: (c["reaches"], str(c["precision"]),
                                           str(c.get("record") or ""),
                                           str(c.get("person") or "")))[-1] if pool else None

    on_the_day = best([c for c in sightings if c["earliest"] <= SCENE_DATE <= c["reaches"]])
    if on_the_day:
        return {"leg": "on_the_day", "reading": on_the_day, "second": None}
    spanning = best([c for c in spans if c["earliest"] <= SCENE_DATE <= c["reaches"]])
    if spanning:
        return {"leg": "spans", "reading": spanning, "second": None}
    before = best([c for c in sightings if c["reaches"] <= SCENE_DATE])
    after = best([c for c in sightings if c["earliest"] >= SCENE_DATE])
    if before and after:
        return {"leg": "bracketed", "reading": before, "second": after}
    # `carried`: whatever the card's furthest reading is, if it holds one at all. A card
    # whose only dated blocks fall after the day has `before` empty and no `after` pair to
    # bracket with; its reading is that later one, and the note says so.
    return {"leg": "carried", "reading": best(sightings) or best(spans), "second": None}


def _cite(reading: dict | None) -> list[str]:
    return list(reading.get("sources") or []) if reading else []


def presence_block(hid: str, doc: dict, read: dict, model: dict) -> dict:
    """The ruled presence, in the tier shape `migrate_attribute_tiers` holds every block to."""
    leg = read["leg"]
    tier = LEG_TIER[leg]
    reading = read["reading"]
    as_read = reading["as_read"] if reading else None
    grade = residence_grade(doc)

    if leg == "on_the_day":
        note = (f"READ ACROSS THE DAY. The corpus reads this person at Chicago as "
                f"{as_read}, a window that contains 1 July 1835, so the presence is the "
                f"reading's own and is carried at the attested tier. `uncertain` stood here "
                f"because nothing PINNED the day; a reading that covers it is not the "
                f"absence of one (T-1386).")
    elif leg == "spans":
        note = (f"A SOURCE'S SPAN RUNS THROUGH THE DAY. No reading pins 1 July 1835, and a "
                f"cited source covering {as_read} places this person in the town across it. "
                f"The span is the SOURCE's bound and not the person's — which is why this is "
                f"an inference and not a sighting — but attested evidence spanning the day "
                f"is what an inferred presence is made of (T-1386).")
    elif leg == "bracketed":
        second = read["second"]
        note = (f"THE CORPUS SEES BOTH SIDES OF THE DAY. This person is read at Chicago as "
                f"{as_read}, at or before 1 July 1835, and again as "
                f"{second['as_read']}, at or after it. Residence across a day the sources "
                f"read on both sides of is an inference from attested evidence and not a "
                f"draw (T-1386).")
    else:
        note = ("CARRIED BY THE RULE, NOT BY A READING. The corpus stops before 1 July 1835 "
                "and nothing follows this person past it or places them elsewhere on it. "
                "What carries the presence is the project's own standing rule — an attested "
                "or inferred resident is in the population unless there is evidence they "
                "were not — and the persistence model prices it rather than deciding it "
                "(T-1386, acceptance 1).")

    block = {
        "value": "present",
        "confidence": tier,
        "tier": tier,
        "sources": _cite(reading),
        "note": note,
    }
    if tier == "reconstructed":
        lag = years_before_scene(reading["reaches"]) if reading else None
        priced = (round(math.exp(-float(model["lambda_per_year"]) * lag), 4)
                  if lag is not None and lag > 0 else None)
        where = (f"the corpus last reads this person {as_read}"
                 + (f", {lag} year(s) before the scene date" if lag and lag > 0 else "")
                 if reading else "the card holds no dated reading at all")
        priced_says = (f" The persistence model gives {priced} for that lag — the share of "
                       f"this layer a later Chicago volume still names — which prices the "
                       f"ruling and does not decide it: a draw that put a known resident "
                       f"out of the town would be a claim of absence with nothing under it."
                       if priced is not None else
                       " No lag can be priced, so the rule carries the ruling unpriced.")
        block["basis"] = {
            "kind": "rule",
            "id": "an_attested_or_inferred_resident_is_present_unless_evidence_says_otherwise",
            "note": (f"{where[0].upper()}{where[1:]}, and nothing in the corpus follows them "
                     f"past 1 July 1835 or places them elsewhere on it.{priced_says}"),
        }
        block["replaceable_by"] = {
            "kind": "person",
            "match": ("any source that places this person outside Chicago on 1 July 1835, "
                      "or that dates their departure before it"),
        }
        block["priced_by"] = {
            "model": model["id"],
            "lambda_per_year": model["lambda_per_year"],
            "years_before_the_scene": lag,
            "persistence": priced,
        }
    else:
        # Only a reconstructed value owes basis/seed/replaceable_by, and a block that
        # carried them at a read tier is what `check_tier_block` refuses.
        block["read_from"] = {
            "as_read": as_read,
            "reaches": reading["reaches"] if reading else None,
            "family": reading["family"] if reading else None,
            "record": reading.get("record") if reading else None,
            "person": reading.get("person") if reading else None,
        }
    block["residence_grade_this_stands_beside"] = grade
    return block


def rulings() -> list[dict]:
    """One row per household the research left `uncertain`, in id order."""
    model = persistence_model()
    rows = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = read_json(path)
        presence = doc.get("present_on_scene_date") or {}
        if presence.get("value") != "uncertain":
            continue
        hid = str(doc.get("id") or path.stem)
        read = reading_for(doc)
        rows.append({
            "household_id": hid,
            "name": doc.get("name"),
            "division": doc.get("division"),
            "persons": len(doc.get("persons") or []),
            "grades": {g: sum(1 for p in doc.get("persons") or []
                              if p.get("grade") == g) for g in GRADES
                       if any(p.get("grade") == g for p in doc.get("persons") or [])},
            "leg": read["leg"],
            "present_on_scene_date": presence_block(hid, doc, read, model),
            "the_inferred_value_this_stands_beside": "uncertain",
            "what_would_retire_it": ("a source that places this person outside Chicago on "
                                     "1 July 1835, or dates a departure before it"),
        })
    return rows


def evidenced_absences() -> list[dict]:
    """The cards that stay out, and the evidence that keeps them out."""
    out = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = read_json(path)
        presence = doc.get("present_on_scene_date") or {}
        if presence.get("value") != "absent":
            continue
        out.append({
            "household_id": doc.get("id") or path.stem,
            "name": doc.get("name"),
            "note": presence.get("note"),
        })
    return out


def document() -> dict:
    rows = rulings()
    absences = evidenced_absences()
    model = persistence_model()
    by_leg = {leg: sum(1 for r in rows if r["leg"] == leg) for leg in LEGS}
    persons_by_leg = {leg: sum(r["persons"] for r in rows if r["leg"] == leg) for leg in LEGS}
    by_tier = {}
    persons_by_tier = {}
    for row in rows:
        tier = row["present_on_scene_date"]["tier"]
        by_tier[tier] = by_tier.get(tier, 0) + 1
        persons_by_tier[tier] = persons_by_tier.get(tier, 0) + row["persons"]
    persons_by_grade = {}
    for row in rows:
        for grade, n in row["grades"].items():
            persons_by_grade[grade] = persons_by_grade.get(grade, 0) + n
    above_reconstructed = sum(1 for r in rows
                              if r["present_on_scene_date"]["tier"] != "reconstructed")
    return {
        "$schema_note": f"DERIVED — regenerate with {GENERATOR}; tools/check.sh re-derives "
                        f"it and fails on drift. Do not hand-edit: every row's tier is a "
                        f"function of the dated readings its card carries.",
        "id": "chicago_july_1835_presence_rulings",
        "ticket": "T-1386",
        "stage": "presence_rulings",
        "target_date": SCENE_DATE,
        "generated_by": GENERATOR,
        "reads": [
            "data/residents/households/",
            "data/reconstruction/1835_readmissions.json#persistence_model",
        ],
        "read_by": [
            "tools/town_census.py",
            "tools/profile_population_1835.py",
            "tools/build_order_book_1835.py",
            "renderers/web/js/census.js (through data/town_census.json)",
        ],
        "the_rule": ("An attested or inferred resident is in the town's population unless "
                     "there is EVIDENCE they were not — a documented departure, a dated "
                     "appearance elsewhere, a source that places them outside. `uncertain` "
                     "with no tier and no contrary reading is not that evidence. The owner, "
                     "2026-09-19: \"if they are attested that's ideal if we know them "
                     "already\", and \"I want a full population of the city to work from\"."),
        "the_tier_is_derived": {
            "on_the_day": "attested — a dated reading of this person whose window contains "
                          "1 July 1835.",
            "spans": "inferred — a cited source's own span runs through the day.",
            "bracketed": "inferred — the corpus reads this person at Chicago on both sides "
                         "of the day.",
            "carried": "reconstructed — the corpus stops before the day; the project's "
                       "standing rule carries the presence and the persistence model "
                       "prices it.",
        },
        "the_floor": ("T-1172's R1 leg re-ruled every `uncertain` presence at tier "
                      f"`reconstructed`. {above_reconstructed} of these {len(rows)} rulings "
                      f"land ABOVE that on their own dated readings, which is what "
                      f"acceptance 3 asks for: an attested or inferred person never takes a "
                      f"presence tier below what their own evidence supports. A card graded "
                      f"`attested` whose last reading falls before the day keeps its "
                      f"attested RESIDENCE and takes a `reconstructed` PRESENCE — the two "
                      f"are different claims, and calling the presence inferred there would "
                      f"be the undeclared flip this stage refuses."),
        "nothing_is_drawn_here": ("T-1172 drew against the persistence model and ruled 37 "
                                  "cards `absent` on the losing side. This stage does not "
                                  "draw: an absence with no evidence under it is not a "
                                  "finding, and the two evidenced absences below are the "
                                  "shape of a correct exclusion. `basis.kind` is `rule` and "
                                  "a rule owes no seed."),
        "persistence_model": {
            "id": model["id"],
            "lambda_per_year": model["lambda_per_year"],
            "measured_in": "data/reconstruction/1835_readmissions.json#persistence_model",
            "used_for": "pricing a `carried` ruling, never for deciding one",
        },
        "counts": {
            "households_ruled": len(rows),
            "persons_ruled": sum(r["persons"] for r in rows),
            "households_by_leg": by_leg,
            "persons_by_leg": persons_by_leg,
            "households_by_tier": by_tier,
            "persons_by_tier": persons_by_tier,
            "persons_by_residence_grade": persons_by_grade,
            "rulings_above_t1172_blanket_reconstructed": above_reconstructed,
            "evidenced_absences_left_out": len(absences),
        },
        "evidenced_absences": absences,
        "rulings": rows,
    }


def build() -> int:
    OUT.write_text(dumps(document()), encoding="utf-8")
    doc = read_json(OUT)
    counts = doc["counts"]
    print(f"{OUT.relative_to(ROOT)}: {counts['households_ruled']} household(s), "
          f"{counts['persons_ruled']} person(s) ruled present; "
          f"{counts['persons_by_tier']}")
    return 0


def check() -> int:
    if not OUT.exists():
        print(f"{OUT.relative_to(ROOT)} is missing — run {GENERATOR} --build")
        return 1
    want = dumps(document())
    have = OUT.read_text(encoding="utf-8")
    if want == have:
        counts = json.loads(have)["counts"]
        print(f"{OUT.relative_to(ROOT)} re-derives: "
              f"{counts['households_ruled']} household(s), "
              f"{counts['persons_ruled']} person(s)")
        return 0
    print(f"{OUT.relative_to(ROOT)} is STALE — {GENERATOR} --build does not reproduce it")
    return 1


def report() -> int:
    doc = document()
    counts = doc["counts"]
    print(f"{counts['persons_ruled']} person(s) in {counts['households_ruled']} household(s) "
          f"ruled present on {SCENE_DATE}")
    for leg in LEGS:
        if counts["households_by_leg"].get(leg):
            print(f"  {counts['households_by_leg'][leg]:>5}  {leg:<11} "
                  f"→ tier {LEG_TIER[leg]:<14} "
                  f"{counts['persons_by_leg'][leg]} person(s)")
    print(f"   residence grades of the people moved: "
          f"{counts['persons_by_residence_grade']}")
    print(f"   {counts['rulings_above_t1172_blanket_reconstructed']} ruling(s) above "
          f"T-1172's blanket reconstructed tier")
    print(f"   {counts['evidenced_absences_left_out']} card(s) stay out on evidence: "
          f"{', '.join(a['household_id'] for a in doc['evidenced_absences'])}")
    return 0


# --------------------------------------------------------------------------
# the rules, broken on purpose
# --------------------------------------------------------------------------

def self_test() -> int:
    from migrate_attribute_tiers import check_tier_block

    model = persistence_model()
    failures = []

    def case(name: str, ok: bool, detail: str = "") -> None:
        if not ok:
            failures.append(f"{name}: {detail}")

    def card(**kw) -> dict:
        doc = {"id": "hh_t", "persons": [{"id": "t", "grade": "attested"}]}
        doc.update(kw)
        return doc

    # A reading whose window contains the day is a sighting across it, and the tier says so.
    doc = card(persons=[{"id": "t", "grade": "attested",
                         "press_evidence": [{"describes_date": "1835-07",
                                             "record_id": "r1", "sources": ["s"]}]}])
    read = reading_for(doc)
    case("on_the_day", read["leg"] == "on_the_day", read["leg"])
    block = presence_block("hh_t", doc, read, model)
    case("on_the_day tier", block["tier"] == "attested", block["tier"])
    case("a read tier owes no basis", "basis" not in block, sorted(block))

    # A year-precision reading of 1835 covers the day too — it is a claim about the year.
    doc = card(persons=[{"id": "t", "grade": "attested",
                         "civic_evidence": [{"describes_date": "1835", "record_id": "r2"}]}])
    case("year precision covers the day",
         reading_for(doc)["leg"] == "on_the_day", reading_for(doc)["leg"])

    # A source SPAN through the day may not be read as a sighting on it.
    doc = card(persons=[{"id": "t", "grade": "attested",
                         "roles": [{"from": "1833-11", "to": "1835-08",
                                    "claim": "c", "sources": ["s"]}]}])
    read = reading_for(doc)
    case("spans", read["leg"] == "spans", read["leg"])
    case("spans tier", presence_block("hh_t", doc, read, model)["tier"] == "inferred")

    # Read on both sides of the day: an inference, not a draw.
    doc = card(persons=[{"id": "t", "grade": "inferred",
                         "press_evidence": [{"describes_date": "1835-01-04",
                                             "record_id": "a"},
                                            {"describes_date": "1836-02-09",
                                             "record_id": "b"}]}])
    read = reading_for(doc)
    case("bracketed", read["leg"] == "bracketed", read["leg"])
    case("bracketed tier", presence_block("hh_t", doc, read, model)["tier"] == "inferred")
    case("bracketed cites both sides", read["second"]["as_read"] == "1836-02-09")

    # The corpus stops before the day: the rule carries it and the model prices it.
    doc = card(persons=[{"id": "t", "grade": "attested",
                         "press_evidence": [{"describes_date": "1834-04-01",
                                             "record_id": "a"}]}])
    read = reading_for(doc)
    case("carried", read["leg"] == "carried", read["leg"])
    block = presence_block("hh_t", doc, read, model)
    case("carried tier", block["tier"] == "reconstructed", block["tier"])
    case("carried is priced, not drawn",
         block["basis"]["kind"] == "rule" and "seed" not in block,
         json.dumps(block["basis"]))
    case("the price is recorded",
         0.0 < float(block["priced_by"]["persistence"]) < 1.0,
         str(block["priced_by"]))

    # Nobody is ever ruled absent by this stage.
    case("no absence is minted",
         all(r["present_on_scene_date"]["value"] == "present" for r in document()["rulings"]))

    # Every block passes the project's own tier contract.
    errs = []
    for row in document()["rulings"]:
        check_tier_block(row["household_id"], "present_on_scene_date",
                         row["present_on_scene_date"],
                         lambda where, msg: errs.append(f"{where}: {msg}"))
    case("every ruling passes check_tier_block", not errs, "; ".join(errs[:3]))

    # A card the research did NOT leave uncertain is not ruled here at all.
    ruled = {r["household_id"] for r in document()["rulings"]}
    absences = {a["household_id"] for a in evidenced_absences()}
    case("the evidenced absences are not ruled present", not (ruled & absences),
         str(sorted(ruled & absences)))

    # The document re-derives byte-for-byte from the same inputs.
    case("deterministic", dumps(document()) == dumps(document()))

    for line in failures:
        print(f"FAIL  {line}")
    print(f"{'FAILED' if failures else 'ok'} — {len(failures)} failure(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    parser.print_usage()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
