#!/usr/bin/env python3
"""The known population of 1 July 1835, profiled per attribute and per tier.

T-1160. The owner, 2026-09-17: *"do a population analysis of the known population
… analyze demographics, gender, age, occupations, arrival date and reason, all the
attributes for all members of all households and descriptions of the population
composition and types so we can make a best profile of the town."*

`tools/summarize_residents.py` (T-0517) is the older profile and this EXTENDS it
rather than forking it: the layer loader, the markdown table printer and the
percentage helper are imported from there, so a change to how a household is read
moves both. What this adds is the axes that one lacks — age, origin, arrival,
reason for coming, plural roles, lodging and community — and a TIER on every row,
because the reconstruction bands below (T-1167 onward) need to see exactly what
they are filling in and at what honesty.

    python3 tools/profile_population_1835.py              # every section
    python3 tools/profile_population_1835.py sex age      # two sections
    python3 tools/profile_population_1835.py --list       # the section names
    python3 tools/profile_population_1835.py --build      # write the report + JSON
    python3 tools/profile_population_1835.py --check      # re-derive both, byte for byte
    python3 tools/profile_population_1835.py --self-test  # break each rule, require it to fire
    python3 tools/profile_population_1835.py --write-vocabulary   # the two vocabularies

IT IS A PROFILE OF THE EVIDENCE, NOT OF THE TOWN. The town census of November 1835
counts 3,265 people; this layer holds 1,282 person entries and most of them are a
name on a post-office return and nothing else. Every table below says how thin its
own axis is, and the closing section names the buckets the MODEL tickets (T-1293)
and the reconstruction bands have to supply. Nothing here reconstructs anybody — and
the `reconstructed` tier is counted rather than assumed away, which is what puts
T-1158's forty already-reconstructed ATTRIBUTE values beside a person grade that
reads zero reconstructed. Both numbers are true and only one of them was visible.

THE TWO JUDGEMENTS, both made once and both auditable:

  * `SEX_RULES` — how a name may imply a sex. A recorded `sex` wins; then a gendered
    TITLE (Mrs/Miss/Widow/Mr); then a forename that stands in exactly one sex's pool
    of `data/reconstruction/1835_invented_name_pools.json`. Ranks and professional
    styles (Capt., Rev., Dr.) are deliberately NOT read as male: they would be an
    inference about the period rather than about the person, and the age axis already
    takes the honest half of that reading.
  * `REASON_RULES` — the phrase in a household's stated `reason_for_coming` that
    puts it under a controlled term. An unmatched reason is REFUSED rather than
    bucketed as "other", so a new reason cannot fall silently through the axis.
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from summarize_residents import load_layer, persons, pct, table  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "residents" / "index.json"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
STRUCTURES = ROOT / "data" / "structures"
TOWN_CENSUS = ROOT / "data" / "town_census.json"
ATTRIBUTE_TIERS = ROOT / "data" / "research" / "residents" / "attribute_tiers.json"
PRESENCE_RULINGS = ROOT / "data" / "reconstruction" / "1835_presence_rulings.json"
OUT = ROOT / "data" / "reconstruction" / "1835_population_profile.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_population_profile.md"

SCENE_DATE = "1835-07-01"
AS_OF = "2026-09-18"


def presence_rulings() -> dict:
    """T-1386's ruling layer, read rather than restated.

    The research left 827 people on `present_on_scene_date: uncertain` and the cards still
    say so — the ruling lives outside them, because the household directory is derived and
    a ruling is not a mint output. The profile reads it so its presence table says what the
    town's population actually is instead of stopping at the strictest reading.
    """
    if not PRESENCE_RULINGS.exists():
        return {"rulings": [], "counts": {}}
    return json.loads(PRESENCE_RULINGS.read_text(encoding="utf-8"))


def attribute_tiers() -> dict:
    """T-1158's per-attribute tier census, read rather than restated.

    That pass walks every block on every card and records the tier each one earns.
    This profile counts the same tiers along its own axes, so the VOCABULARY comes
    from there — two lists of tier names in one repository is two answers to one
    question, and the second one goes stale silently.
    """
    return json.loads(ATTRIBUTE_TIERS.read_text(encoding="utf-8"))


TIERS = attribute_tiers()["vocabulary"]["tiers"]


class Refused(Exception):
    pass


# ---------------------------------------------------------------------------
# the vocabularies this tool owns in data/residents/index.json
# ---------------------------------------------------------------------------

AGE_BANDS = [
    {"age_band": "birth_year_known",
     "rule": "the person carries a birth_year block",
     "means": "a source gives the year, however loosely"},
    {"age_band": "age_stated",
     "rule": "the person carries an age_on_scene_date block and no birth_year",
     "means": "a source gives an age at 1 July 1835"},
    {"age_band": "adult_by_civic_list",
     "rule": "the person carries civic_evidence (a poll, tax or muster list)",
     "means": "an adult: a voter, a taxpayer or a man of militia age"},
    {"age_band": "adult_by_role",
     "rule": "the person carries a role, or an occupation other than none_recorded",
     "means": "an adult: a trade, profession or office is not held by a child"},
    {"age_band": "adult_by_marriage_or_parenthood",
     "rule": "the person stands in the church register as bride, groom or parent",
     "means": "an adult on the register's own face"},
    {"age_band": "child_by_baptism",
     "rule": "the person stands in the church register as an infant or a baptised child",
     "means": "a child"},
    {"age_band": "unknown",
     "rule": "none of the above",
     "means": "nothing on the card bears on age at all"},
]

REASONS_FOR_COMING = [
    {"term": "army_posting", "means": "ordered here by the Army"},
    {"term": "indian_agency", "means": "appointed to the United States Indian agency"},
    {"term": "federal_contract", "means": "a mail or other federal contract"},
    {"term": "public_office", "means": "a county, town or court office"},
    {"term": "mission_or_church", "means": "sent by a church or missionary society"},
    {"term": "trade_or_forwarding", "means": "the fur trade, a store, forwarding and commission"},
    {"term": "house_of_entertainment", "means": "to keep a tavern, hotel or boarding house"},
    {"term": "the_press", "means": "to found, run or work a printing office"},
    {"term": "a_trade_or_manufacture", "means": "to set up a craft or works of their own"},
    {"term": "following_kin", "means": "after a father, brother or other kin already here"},
    {"term": "business_prospects", "means": "the prospects of a new western town, stated as such"},
    {"term": "canal_and_harbour_works", "means": "the harbour works or the canal"},
    {"term": "land_purchase", "means": "to buy land at the sales"},
    # T-1169's terms. The first is the biggest bucket on this axis by an order of
    # magnitude and it is deliberately the emptiest claim in the vocabulary: it means
    # the record names the season's draws and refuses to pick one, so a reader who sees
    # 1,142 households under it has learnt that the town does not know, not that 1,142
    # households came for the same thing. The rest are argued from a recorded trade and
    # say what that trade answered.
    {"term": "season_not_apportioned",
     "means": "the arrival season's draws, with no source apportioning the town between them"},
    {"term": "a_store_or_provision_trade", "means": "to keep a store or provision house"},
    {"term": "the_building_trades", "means": "the building of a town three years old"},
    {"term": "a_mechanics_trade", "means": "a mechanic's trade the town had few of"},
    {"term": "a_professional_practice", "means": "a professional practice in a new county seat"},
    {"term": "a_congregation_or_a_school", "means": "a congregation or a school"},
    {"term": "the_country_trade", "means": "the country trade at the forks"},
    {"term": "a_clerkship", "means": "a clerkship in a merchant's or a public office"},
]

# Ordered: the FIRST pattern that matches the stated reason names it. Specific
# before general, because "trade and tavern keeping" is a tavern and "a law
# practice" beside a county office is the office.
REASON_RULES = [
    # T-1169 PUT A REASON ON EVERY HOUSEHOLD, and 1,233 of them are reconstructed. Its
    # rules are read FIRST, above everything below, and the first bucket is why: a
    # reason argued from the arrival SEASON alone names the draws that were operating
    # in it — the canal land sales, the harbour works, the incorporated town — and
    # says in the same sentence that it does not know which of them applied. Read by
    # the general rules below, every one of those would have been filed under
    # `canal_and_harbour_works` or `land_purchase` on the strength of a phrase inside
    # a refusal, and this axis would have reported an apportionment of the town that
    # the town model declines to make and the value itself disclaims.
    ("season_not_apportioned",
     r"^(the trading post, the fort|the 183[345] season\b)"),
    # The trade-argued reasons, above the general rules for the same reason: each is a
    # fixed phrase this project composes, and two of them contain words — congregation,
    # land sales — that a general rule would catch at the wrong grain.
    ("a_congregation_or_a_school", r"\ba congregation or a school\b"),
    ("land_purchase", r"\bthe land sales and the canal expectation\b"),
    ("army_posting", r"\ba posting to fort dearborn\b"),
    # A missionary who travelled WITH a garrison came for the mission, and a man who
    # followed his brother to a tavern came after his brother: the specific reading
    # stands above the general one, which is the whole reason this list is ordered.
    ("mission_or_church", r"\b(missionary|bishop|congregation)\b"),
    ("following_kin", r"\b(following their|to follow a)\b"),
    ("army_posting", r"\b(by the army|ordered to command|posted to fort|transferred garrison)\b"),
    ("indian_agency", r"\bindian agency\b"),
    ("federal_contract", r"\bmail contract\b"),
    ("public_office", r"\bcounty office\b"),
    ("the_press", r"\b(newspaper|printing office)\b"),
    ("house_of_entertainment", r"\b(tavern|hotel)\b"),
    ("a_trade_or_manufacture", r"\b(brickyard|blacksmith|shop of their own)\b"),
    ("trade_or_forwarding", r"\b(fur trade|forwarding|to open a store|trade at the head)\b"),
    ("canal_and_harbour_works", r"\b(harbour works|harbor works|the canal)\b"),
    ("land_purchase", r"\bland sales?\b"),
    ("business_prospects", r"\b(confidence in the future|business interests|reverses)\b"),
    # The rest of T-1169's trade-argued phrases. These sit at the BOTTOM on purpose:
    # they are the ones no existing rule was going to catch at all, and putting them
    # here leaves every reading above them exactly as it was.
    ("a_store_or_provision_trade", r"\ba store for the traffic\b"),
    ("the_building_trades", r"\bthe building of a town three years old\b"),
    ("a_mechanics_trade", r"\ba mechanic's trade in a town\b"),
    ("house_of_entertainment", r"\blodging and victualling\b"),
    ("a_professional_practice", r"\ba professional practice in a new county seat\b"),
    ("the_country_trade", r"\bcountry trade at the forks\b"),
    ("a_clerkship", r"\ba clerkship\b"),
]

FEMALE_TITLES = ("mrs", "miss", "madam", "madame", "widow")
MALE_TITLES = ("mr", "master")

# THE THREE TIERS, AND WHY THE RULE IS READ OFF THE CARD RATHER THAN RECOMPUTED (T-1304).
# Until 2026-09-18 this report decided a sex itself, from the pools, and called anything
# already on the card `recorded`. That was right when nothing else wrote a sex; it stopped
# being right the moment T-1303 wrote 590 read sexes and T-1304 drew 587 more, because it
# read all 1,276 as a source's statement and printed `recorded 689` over a layer where 99
# people have a source. The rule now comes from the `sex_basis` block the writing pass
# leaves behind, which is the only thing that knows which rule fired.
SEX_RULES = [
    {"rule": "recorded", "tier": "attested",
     "means": "a source records the sex on the card, and no pass had to read it"},
    {"rule": "inferred_title", "tier": "inferred",
     "means": "the read name carries a gendered title (Mrs, Miss, Widow, Mr)"},
    {"rule": "inferred_contraction", "tier": "inferred",
     "means": "the name is a period contraction every attested expansion of which is one sex's"},
    {"rule": "inferred_forename", "tier": "inferred",
     "means": "the forename stands in exactly one sex's naming and in no other (T-1303's "
              "derived table, which refuses a name its own evidence splits)"},
    {"rule": "reconstructed_from_the_roll", "tier": "reconstructed",
     "means": "DRAWN at the male rate measured on the roll this person was named off, "
              "seeded by their own id (T-1304) — never evidence about this person"},
    {"rule": "unknown", "tier": "unknown",
     "means": "the name is an initial no roll rate reaches, or a collective description "
              "that names nobody"},
]


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def value(block):
    """The value of a {value, confidence, sources, note} block, or None."""
    if isinstance(block, dict):
        return block.get("value")
    return block


def tier_of(block) -> str:
    """The tier a block's own confidence puts it at; `unknown` when it says nothing."""
    if not isinstance(block, dict) or block.get("value") in (None, "", "none_recorded"):
        return "unknown"
    conf = block.get("confidence")
    return conf if conf in ("attested", "inferred", "reconstructed") else "unknown"


def tier_row(label: str, counts: Counter, total: int) -> list:
    return [label, sum(counts.values()), pct(sum(counts.values()), total)] + [
        counts[t] for t in TIERS]


def tier_table(title_col: str, rows: list, unit: str = "households",
               total_note: str = "") -> dict:
    return {"headers": [title_col, unit, "share"] + TIERS,
            "aligns": "lrr" + "r" * len(TIERS), "rows": rows, "note": total_note}


def plain_table(headers: list, rows: list, aligns: str = "", note: str = "") -> dict:
    return {"headers": headers, "aligns": aligns or "l" * len(headers),
            "rows": rows, "note": note}


def name_parts(name: str) -> tuple:
    """(title, forename) from a read name, each lowercased, either may be ''."""
    words = [w for w in re.split(r"[\s,]+", (name or "").strip()) if w]
    title = ""
    if words:
        head = words[0].rstrip(".").lower()
        if head in FEMALE_TITLES or head in MALE_TITLES:
            title = head
            words = words[1:]
    fore = ""
    for w in words:
        clean = re.sub(r"[^A-Za-z]", "", w)
        if len(clean) >= 3:
            fore = clean.lower()
            break
        # An initial ends the search: `J. W. Smith` has no forename to read.
        break
    return title, fore


def pools() -> tuple:
    """The period forename pools, as two sets and the overlap between them."""
    doc = json.loads(POOLS.read_text(encoding="utf-8"))
    male, female = set(), set()
    for community in doc["communities"]:
        male |= {n.lower() for n in community.get("given_male") or []}
        female |= {n.lower() for n in community.get("given_female") or []}
    return male, female, male & female


def sex_of(person: dict, male: set, female: set, both: set) -> tuple:
    """(sex or None, the rule that says so). The card's own `sex_basis` decides."""
    recorded = person.get("sex")
    if recorded:
        basis = person.get("sex_basis") or {}
        conf, note = basis.get("confidence"), basis.get("note") or ""
        if conf == "reconstructed":
            return recorded, "reconstructed_from_the_roll"
        if conf == "inferred":
            if "PRINTED WITH A TITLE" in note:
                return recorded, "inferred_title"
            if "PERIOD CONTRACTION" in note:
                return recorded, "inferred_contraction"
            return recorded, "inferred_forename"
        return recorded, "recorded"
    title, fore = name_parts(person.get("name") or "")
    if title in FEMALE_TITLES:
        return "female", "inferred_title"
    if title in MALE_TITLES:
        return "male", "inferred_title"
    if fore and fore not in both:
        if fore in male:
            return "male", "inferred_forename"
        if fore in female:
            return "female", "inferred_forename"
    return None, "unknown"


def age_band_of(person: dict) -> str:
    if person.get("birth_year"):
        return "birth_year_known"
    if person.get("age_on_scene_date"):
        return "age_stated"
    church = person.get("church_evidence") or []
    if any((e.get("locator") or "") in ("infant", "baptised", "child")
           for e in church):
        return "child_by_baptism"
    if person.get("civic_evidence"):
        return "adult_by_civic_list"
    occ = value(person.get("occupation"))
    if (person.get("roles") or []) or (occ and occ != "none_recorded"):
        return "adult_by_role"
    if any((e.get("locator") or "") in ("bride", "groom", "parent") for e in church):
        return "adult_by_marriage_or_parenthood"
    return "unknown"


def reason_term(text: str) -> str:
    low = (text or "").lower()
    for term, pattern in REASON_RULES:
        if re.search(pattern, low):
            return term
    raise Refused("a stated reason for coming matches no rule in REASON_RULES and "
                  "was not bucketed: %r. Add a rule rather than an `other` row." % text)


def structure_function(sid: str) -> str:
    path = STRUCTURES / (sid + ".json")
    if not path.exists():
        return "not_modelled"
    doc = json.loads(path.read_text(encoding="utf-8"))
    return value(doc.get("function")) or "unstated"


# T-1323. The lodging test, stated in terms a building can actually spell.
#
# `function` became a closed vocabulary at T-1311 and this set is a SELECTION from it,
# not a second vocabulary. Until this ticket it named `tavern`, `inn` and `coffee_house`,
# and no record ever used any of the three: the town's public houses spell `tavern_inn`
# (seven roofs, the Exchange Coffee House among them) and the reconstructed stock spells
# `small_inn_or_tavern` and the three sized boarding houses. So five households — the
# Mansion House keeper, Ingersoll, Murphy, Stow, Walters — were counted under "a dwelling
# or a place of business" and the Lodging section under-reported the houses of
# entertainment by exactly the taverns.
#
# BOTH DIRECTIONS ARE GATED, by `tools/normalise_structure_function.py --check`: a term
# here that no structure can spell is refused the way a signage trade is, and a vocabulary
# term that READS like lodging and appears in neither set below is refused too — which is
# what stops the next `inn`-shaped term from being added to the schema and silently
# missed here.
LODGING_FUNCTIONS = {
    "boarding_house",
    "hotel",
    "large_boarding_house",
    "medium_boarding_house",
    "small_boarding_house",
    "small_inn_or_tavern",
    "tavern_inn",
}

# The lodging-shaped terms that are deliberately NOT a house of entertainment, each with
# its reason. A ruling, not an oversight — the gate requires one or the other.
NOT_LODGING_FUNCTIONS = {
    # A roof still going up on 1835-07-01 lodges nobody; the Lake House opened in 1836.
    "hotel_under_construction",
    # Lodging over a professional office is a dwelling, not a house of entertainment:
    # Dr Temple's building on Lake Street housed him, it did not take the town's guests.
    "office_and_lodging",
    # Stabling is for the horses of a house of entertainment, not for its people.
    "hotel_stable",
    "tavern_stable",
}


def function_words(term: str) -> str:
    """A vocabulary term as a table cell reads it.

    `function` became a closed vocabulary at T-1311, and a term is not a phrase to
    put in a column headed "its function". The underscores come out here, where
    the value is being PRINTED, and nowhere the value is being COMPARED.
    """
    return term.replace("_", " ")


# ---------------------------------------------------------------------------
# the sections
# ---------------------------------------------------------------------------

def sec_headcount(L) -> dict:
    index, records = L.index, L.records
    total = len(L.people)
    grades = Counter(p["grade"] for _, p in L.people)
    rows = [[g, grades[g], pct(grades[g], total)] for g in index["vocabulary"]["grades"]]
    rows.append(["TOTAL", total, pct(total, total)])
    already = reconstructed_attributes(records)
    by_division = Counter(h["division"] for h in records)
    presence = Counter(value(h["present_on_scene_date"]) for h in records)
    div_rows = [[d, by_division[d], pct(by_division[d], len(records))]
                for d in index["vocabulary"]["divisions"]]
    pres_rows = [[v, presence[v], pct(presence[v], len(records))]
                 for v in index["vocabulary"]["presence"]]
    # T-1386. The cards' own `uncertain` is kept — it is what the research wrote — and the
    # ruling that puts those people in the town stands beside it, one row a tier, so the
    # table above reads as the strictest measure and this one as the population.
    ruled = presence_rulings()
    ruled_counts = ruled.get("counts") or {}
    ruled_tiers = ruled_counts.get("persons_by_tier") or {}
    ruled_total = int(ruled_counts.get("persons_ruled") or 0)
    ruled_rows = [[t, ruled_tiers[t], pct(ruled_tiers[t], ruled_total)]
                  for t in ("attested", "inferred", "reconstructed") if t in ruled_tiers]
    if ruled_rows:
        ruled_rows.append(["TOTAL", ruled_total, pct(ruled_total, ruled_total)])
    return {
        "id": "headcount",
        "title": "Headcount",
        "lead": ("%d person entries in %d households. The town census of November 1835 "
                 "counts 3,265 people in 398 dwellings, so this layer is the part of the "
                 "town the sources name and no more." % (total, len(records))),
        "tables": [
            {"title": "Persons by grade", **plain_table(
                ["grade", "persons", "share"], rows, "lrr")},
            {"title": "Households by division", **plain_table(
                ["division", "households", "share"], div_rows, "lrr")},
            {"title": "Households by presence on 1 July 1835", **plain_table(
                ["presence", "households", "share"], pres_rows, "lrr")},
        ] + ([
            {"title": "The people the research left unadjudicated, ruled into the town "
                      "(T-1386), by the tier their own dated readings reach",
             **plain_table(["presence tier", "persons", "share"], ruled_rows, "lrr")},
        ] if ruled_rows else []) + [
            {"title": "Attribute values already standing at the reconstructed tier",
             **plain_table(["household", "field", "value", "why it is at that tier"],
                           already, "llll")},
        ],
        "notes": ([
            "THE TABLE ABOVE IS THE STRICTEST READING AND IT IS NOT THE POPULATION "
            "(T-1386). %d of these households stand `uncertain` on the card because no "
            "record follows the person to 1 July 1835 — unadjudicated, never disputed. "
            "Every one of them has attested or inferred evidence of living in this town "
            "and none has evidence of being elsewhere that day, so all %d of their people "
            "are ruled into the town, each at the tier its own readings reach. Exactly %d "
            "cards are out on evidence of absence. The ruling is "
            "data/reconstruction/1835_presence_rulings.json; the cards keep the inferred "
            "`uncertain` the research wrote."
            % (int(ruled_counts.get("households_ruled") or 0), ruled_total,
               int(ruled_counts.get("evidenced_absences_left_out") or 0)),
        ] if ruled_rows else []) + [
                  "No PERSON carries the `reconstructed` grade (%d) and this ticket does "
                  "not move that: reconstruction begins at T-1167 under its own programme. "
                  "But %d ATTRIBUTE values already do, and a person-grade count hides them "
                  "— which is the whole reason T-1158 puts a tier on the field rather than "
                  "on the card." % (grades["reconstructed"], len(already))],
    }


def reconstructed_attributes(records: list) -> list:
    """Every attribute value standing at the `reconstructed` tier, from T-1158.

    Read out of that pass's census rather than re-derived here. It walks all 10,499
    blocks on all 1,258 cards — person-level and nested ones this profile's axes
    never touch — so re-deriving a subset beside it would publish a smaller number
    for the same thing, which is the failure a second implementation always ships.
    """
    rows = []
    for row in attribute_tiers()["reconstructed"]:
        note = (row.get("note") or "").split(".")[0].strip()
        rows.append([row["card"], row["attribute"], str(row.get("value")),
                     note[:96] or "(no note)"])
    rows.sort()
    return rows


def sec_sex(L) -> dict:
    total = len(L.people)
    by_rule = Counter()
    grid = defaultdict(Counter)
    for _, p in L.people:
        sex, rule = sex_of(p, *L.pools)
        by_rule[rule] += 1
        grid[sex or "unknown"][rule] += 1
    rule_rows = [[r["rule"], by_rule[r["rule"]], pct(by_rule[r["rule"]], total), r["means"]]
                 for r in SEX_RULES]
    rules = [r["rule"] for r in SEX_RULES]
    sex_rows = [[s, sum(grid[s].values()), pct(sum(grid[s].values()), total)]
                + [grid[s][r] for r in rules]
                for s in ["male", "female", "unknown"]]
    known = total - by_rule["unknown"]
    return {
        "id": "sex",
        "title": "Sex",
        "lead": ("%d of %d persons (%s) carry a sex, AT THREE DIFFERENT TIERS and the "
                 "table below is the only honest way to read them together: %d because a "
                 "source records it, %d read off a gendered title, a period contraction or "
                 "a forename that stands in one sex's naming only, and %d DRAWN at the "
                 "male rate measured on the roll the person was named off. A drawn sex is "
                 "not evidence about that person and never becomes any; the %d left are "
                 "collective descriptions that name nobody."
                 % (known, total, pct(known, total), by_rule["recorded"],
                    by_rule["inferred_title"] + by_rule["inferred_contraction"]
                    + by_rule["inferred_forename"],
                    by_rule["reconstructed_from_the_roll"], by_rule["unknown"])),
        "tables": [
            {"title": "Sex by the rule that says so", **plain_table(
                ["sex", "persons", "share"] + rules, sex_rows, "lrr" + "r" * len(rules))},
            {"title": "The rules themselves", **plain_table(
                ["rule", "persons", "share", "what it reads"], rule_rows, "lrrl")},
        ],
        "notes": ["A rank or a professional style — Capt., Rev., Dr. — is NOT read as male "
                  "here. In this town it would almost always be right and it would still be "
                  "an inference about the period rather than about the person; the age axis "
                  "takes the honest half of that reading instead."],
    }


def sec_age(L) -> dict:
    total = len(L.people)
    bands = Counter(age_band_of(p) for _, p in L.people)
    rows = [[b["age_band"], bands[b["age_band"]], pct(bands[b["age_band"]], total), b["means"]]
            for b in AGE_BANDS]
    dated = bands["birth_year_known"] + bands["age_stated"]
    adults = sum(bands[b["age_band"]] for b in AGE_BANDS if b["age_band"].startswith("adult_"))
    pyramid = []
    for h, p in L.people:
        if p.get("age_on_scene_date"):
            pyramid.append((p["name"], value(p["age_on_scene_date"]),
                            tier_of(p["age_on_scene_date"])))
        elif p.get("birth_year"):
            year = value(p["birth_year"])
            pyramid.append((p["name"], 1835 - int(year) if year else None,
                            tier_of(p["birth_year"])))
    pyramid.sort(key=lambda r: (r[1] is None, -(r[1] or 0), r[0]))
    # THE THREE TIERS OF AN AGE (T-1304). `age_band` is written for every person: at the
    # tier of their own birth year where one is on the card, and `reconstructed` where the
    # band was drawn from the 1840 schedule. The table above says what the EVIDENCE bears;
    # this one says what the layer now carries and at what tier, which are not the same
    # question and must not be printed as if they were.
    age_tiers = Counter()
    age_values = Counter()
    for _h, p in L.people:
        block = p.get("age_band") or {}
        tier = block.get("tier") or "none"
        if block.get("value") is None:
            tier = "unknown"
        age_tiers[tier] += 1
        if block.get("value"):
            age_values[(block["value"], block.get("low"))] += 1
    tier_rows = [[t, age_tiers[t], pct(age_tiers[t], total), m] for t, m in (
        ("attested", "the band this person's own recorded birth year or age puts them in"),
        ("inferred", "the band an inferred birth year or age puts them in"),
        ("reconstructed", "DRAWN from the 1840 Chicago schedule's sex × age bands, "
                          "conditioned on what the person is recorded doing, seeded by "
                          "their own id — a band, never a year"),
        ("unknown", "a collective description: a row that stands for more than one person "
                    "has no band of its own"),
    ) if age_tiers[t]]
    band_rows = [[b, n, pct(n, total)] for (b, _low), n in
                 sorted(age_values.items(), key=lambda kv: (kv[0][1] is None, kv[0][1]))]
    return {
        "id": "age",
        "title": "Age",
        "lead": ("%d of %d persons carry a year or an age off a source; %d more are placed "
                 "in an adult band by what they are recorded DOING — a poll, a tax list, a "
                 "muster, a trade, an office, a marriage — and %d carry nothing that bears "
                 "on age at all. SINCE T-1304 EVERY ONE OF THEM CARRIES AN AGE BAND, and "
                 "the tier table below says which of the three it stands on. The bands are "
                 "the 1840 Chicago schedule's and a drawn one is never turned into a year. "
                 "THIS IS STILL NOT AN AGE PYRAMID OF THE TOWN: these are the people the "
                 "rolls name, overwhelmingly adult men, and the women and children the "
                 "pyramid lacks are T-1174's brief."
                 % (dated, total, adults, bands["unknown"])),
        "tables": [
            {"title": "Age bands", **plain_table(
                ["band", "persons", "share", "what it means"], rows, "lrrl")},
            {"title": "The age band every person now carries, by tier", **plain_table(
                ["tier", "persons", "share", "what it means"], tier_rows, "lrrl")},
            {"title": "The layer by age band on 1 July 1835", **plain_table(
                ["band", "persons", "share"], band_rows, "lrr")},
            {"title": "Every dated age in the layer", **plain_table(
                ["person", "age on 1 July 1835", "tier"],
                [[n, a if a is not None else "-", t] for n, a, t in pyramid], "lrl")},
        ],
        "notes": ["`child_by_baptism` is %d. The register the layer reads gives witnesses, "
                  "brides, grooms, parents and decedents and no baptised infants, so the "
                  "known layer holds no identified child at all."
                  % bands["child_by_baptism"]],
    }


def sec_origin(L) -> dict:
    records = L.records
    n = len(records)
    origin_tiers = Counter(tier_of(h.get("origin")) for h in records)
    arrival_tiers = Counter(tier_of(h.get("arrival")) for h in records)
    reason_tiers = Counter(tier_of(h.get("reason_for_coming")) for h in records)
    precision = Counter((h.get("arrival") or {}).get("precision")
                        for h in records if value(h.get("arrival")))
    terms = Counter()
    stated = []
    for h in records:
        text = value(h.get("reason_for_coming"))
        if not text:
            continue
        term = reason_term(text)
        terms[term] += 1
        stated.append([h["name"], term, text, tier_of(h["reason_for_coming"])])
    stated.sort(key=lambda r: (r[1], r[0]))
    axis_rows = [
        tier_row("origin (state or country)", Counter(
            {t: origin_tiers[t] for t in TIERS if t != "unknown"}), n),
        tier_row("arrival date or bound", Counter(
            {t: arrival_tiers[t] for t in TIERS if t != "unknown"}), n),
        tier_row("reason for coming", Counter(
            {t: reason_tiers[t] for t in TIERS if t != "unknown"}), n),
    ]
    prec_rows = [[k or "(none)", v, pct(v, n)]
                 for k, v in sorted(precision.items(), key=lambda kv: -kv[1])]
    term_rows = [[t["term"], terms[t["term"]], t["means"]] for t in REASONS_FOR_COMING]
    bound = precision.get("not_later_than", 0)
    return {
        "id": "origin_and_arrival",
        "title": "Origin and arrival",
        "lead": ("Every household carries an arrival block and %s of them (%d) hold a "
                 "`not_later_than` BOUND rather than an arrival: somebody was writing to "
                 "that name at Chicago by a date, and nothing says when they came. Only %d "
                 "households name an origin and %d a reason for coming."
                 % (pct(bound, n), bound, sum(1 for h in records if value(h.get("origin"))),
                    len(stated))),
        "tables": [
            {"title": "The three axes, by tier", **tier_table("axis", axis_rows)},
            {"title": "What the arrival block actually is", **plain_table(
                ["arrival precision", "households", "share"], prec_rows, "lrr")},
            {"title": "Reason for coming, by controlled term", **plain_table(
                ["term", "households", "what it means"], term_rows, "lrl")},
            {"title": "Every stated reason, and the term it reads as", **plain_table(
                ["household", "term", "as the source puts it", "tier"], stated, "llll")},
        ],
        "notes": ["`canal_and_harbour_works` and `land_purchase` are both 0. The harbour "
                  "works were the largest employer in the town in 1835 and the land sales "
                  "were why much of the transient population was here; no household in the "
                  "known layer states either as its reason. That silence is T-1178's brief, "
                  "not a finding about the town."],
    }


def sec_roles(L) -> dict:
    total = len(L.people)
    counts = Counter(len(p.get("roles") or []) for _, p in L.people)
    kinds = Counter(r.get("kind") for _, p in L.people for r in (p.get("roles") or []))
    reach = Counter(bool(r.get("covers_scene_date"))
                    for _, p in L.people for r in (p.get("roles") or []))
    trade_tiers = Counter()
    trades = Counter()
    for _, p in L.people:
        occ = p.get("occupation")
        if value(occ) and value(occ) != "none_recorded":
            trades[value(occ)] += 1
            trade_tiers[tier_of(occ)] += 1
    office_holders = sorted({p["name"] for _, p in L.people
                             for r in (p.get("roles") or []) if r.get("kind") == "office"})
    keepers = sorted({p["name"] for _, p in L.people
                      if (value(p.get("occupation")) or "") in
                      ("tavern_keeper", "hotel_keeper", "boarding_house_keeper")})
    n_rows = [[str(k) if k < 2 else "%d or more" % k, v, pct(v, total)]
              for k, v in sorted(counts.items())]
    return {
        "id": "roles",
        "title": "Roles — plural and dated",
        "lead": ("%d of %d persons carry at least one role and %d carry two or more. "
                 "%d of the %d roles in the layer reach 1 July 1835; the other %d are "
                 "printed against the name in a later volume and say so."
                 % (total - counts[0], total, sum(v for k, v in counts.items() if k >= 2),
                    reach[True], sum(kinds.values()), reach[False])),
        "tables": [
            {"title": "Persons by number of roles", **plain_table(
                ["roles on the card", "persons", "share"], n_rows, "rrr")},
            {"title": "Roles by kind", **plain_table(
                ["kind", "roles"], [[k or "(none)", v] for k, v in
                                    sorted(kinds.items(), key=lambda kv: -kv[1])], "lr")},
            {"title": "Occupations reaching the scene date, by tier", **plain_table(
                ["tier", "persons"], [[t, trade_tiers[t]] for t in TIERS if trade_tiers[t]],
                "lr")},
            {"title": "The trades themselves", **plain_table(
                ["trade", "persons"],
                [[k, v] for k, v in sorted(trades.items(), key=lambda kv: (-kv[1], kv[0]))],
                "lr")},
        ],
        "notes": [
            "Offices held: %s." % (", ".join(office_holders) or "none"),
            "Houses of entertainment kept: %s." % (", ".join(keepers) or "none"),
        ],
    }


def sec_households(L) -> dict:
    records = L.records
    n = len(records)
    sizes = Counter(len(h["persons"]) for h in records)
    rel = Counter(p["relationship"] for _, p in L.people)
    female_heads = 0
    for h in records:
        head = next((p for p in h["persons"] if p["relationship"] == "head"), None)
        if head and sex_of(head, *L.pools)[0] == "female":
            female_heads += 1
    party = [(h["name"], value(h["party_size_on_arrival"]),
              tier_of(h["party_size_on_arrival"]))
             for h in records if value(h.get("party_size_on_arrival"))]
    party.sort()
    alone = sizes[1]
    size_rows = [[str(k), v, pct(v, n)] for k, v in sorted(sizes.items())]
    rel_rows = [[k, v, pct(v, len(L.people))]
                for k, v in sorted(rel.items(), key=lambda kv: -kv[1])]
    return {
        "id": "households",
        "title": "Household composition",
        "lead": ("%d of %d households (%s) are ONE PERSON — a head and nobody else. That "
                 "is a statement about the evidence: a post-office return names one man and "
                 "says nothing about a wife. %d households name a second person; %d heads "
                 "read as women."
                 % (alone, n, pct(alone, n), n - alone, female_heads)),
        "tables": [
            {"title": "Persons in the household", **plain_table(
                ["persons", "households", "share"], size_rows, "rrr")},
            {"title": "Relationships the layer actually holds", **plain_table(
                ["relationship", "persons", "share"], rel_rows, "lrr")},
            {"title": "Every stated party size on arrival", **plain_table(
                ["household", "party size", "tier"],
                [[a, b, c] for a, b, c in party], "lrl")},
        ],
        "notes": ["The index's own relationship vocabulary offers %d terms; the layer uses "
                  "%d of them. Servant, apprentice, journeyman, boarder, lodger and clerk "
                  "are all at zero — the whole of T-1171, T-1347 and T-1175."
                  % (len(L.index["vocabulary"]["relationships"]), len(rel))],
    }


def sec_lodging(L) -> dict:
    records = L.records
    n = len(records)
    classes = Counter()
    rows = []
    for h in records:
        sid = value(h.get("lives_at"))
        if not sid:
            classes["no lives_at at all"] += 1
            continue
        fn = structure_function(sid)
        kind = ("a house of entertainment" if fn in LODGING_FUNCTIONS
                else "the fort" if h["division"] == "fort"
                else "a dwelling or a place of business")
        classes[kind] += 1
        rows.append([h["name"], sid, function_words(fn), kind, tier_of(h["lives_at"])])
    rows.sort(key=lambda r: (r[3], r[0]))
    cls_rows = [[k, v, pct(v, n)] for k, v in sorted(classes.items(), key=lambda kv: -kv[1])]
    return {
        "id": "lodging",
        "title": "Lodging",
        "lead": ("%d of %d households name a place they live. The town census counts 398 "
                 "dwellings for 3,265 people — eight to a dwelling — so the beds are where "
                 "this layer is thinnest, and T-1175 is the ticket that fills them."
                 % (n - classes["no lives_at at all"], n)),
        "tables": [
            {"title": "Where a household is lodged", **plain_table(
                ["class", "households", "share"], cls_rows, "lrr")},
            {"title": "Every household with a lives_at", **plain_table(
                ["household", "structure", "its function", "class", "tier"], rows, "lllll")},
        ],
        "notes": ["A household is classed a house of entertainment when the roof it names "
                  "carries one of the %d function terms that mean lodging for pay: %s. The "
                  "test used to name `tavern`, `inn` and `coffee_house`, which the function "
                  "vocabulary cannot spell and no record ever used, so the taverns counted "
                  "as dwellings (T-1323)."
                  % (len(LODGING_FUNCTIONS),
                     ", ".join("`%s`" % t for t in sorted(LODGING_FUNCTIONS))),
                  "No household in the known layer lodges on a vessel. The crews ashore on "
                  "1 July 1835 are T-1178's cohort and none of them is named here."],
    }


def sec_buildings(L) -> dict:
    records = L.records
    town = json.loads(TOWN_CENSUS.read_text(encoding="utf-8"))
    people, buildings = town["people"], town["buildings"]
    grid = defaultdict(Counter)
    for h in records:
        d = h["division"]
        grid[d]["housed" if value(h.get("lives_at")) else "no dwelling"] += 1
        if value(h.get("works_at")):
            grid[d]["roofed workplace"] += 1
    cols = ["housed", "roofed workplace", "no dwelling"]
    rows = [[d, sum(1 for h in records if h["division"] == d)] + [grid[d][c] for c in cols]
            for d in L.index["vocabulary"]["divisions"]]
    rows.append(["TOTAL", len(records)]
                + [sum(grid[d][c] for d in grid) for c in cols])
    return {
        "id": "buildings",
        "title": "Where they meet the buildings",
        "lead": ("%d persons resolve into a dwelling that stands in the scene, in %d "
                 "households; %d households have no dwelling. %d roofs stand against a "
                 "programme of %d."
                 % (people["housed"], people["households_housed"],
                    people["households_without_a_dwelling"],
                    buildings["standing"], buildings["target"])),
        "tables": [
            {"title": "Households by division and seating", **plain_table(
                ["division", "households"] + cols, rows, "lr" + "r" * len(cols))},
            {"title": "The town census of November 1835", **plain_table(
                ["measure", "value"],
                [["people", people["town_total"]],
                 ["dwellings", people["town_total_dwellings"]],
                 ["roofs standing in the scene", buildings["standing"]],
                 ["roofs the programme targets", buildings["target"]]], "lr")},
        ],
        "notes": ["%d of %d households are `unplaced` — not in any division. A person "
                  "without a division cannot be housed, which is why the division axis and "
                  "the lodging axis fail together."
                  % (sum(1 for h in records if h["division"] == "unplaced"), len(records))],
    }


def sec_community(L) -> dict:
    """The kinds of people the SOURCES show, counted only where a source states it."""
    records = L.records
    total = len(L.people)
    signals = Counter()
    quoted = []
    for h in records:
        for p in h["persons"]:
            hit = False
            if any((e.get("list") or "").startswith("church_")
                   for e in (p.get("church_evidence") or [])):
                signals["named in the Catholic register"] += 1
                hit = True
            if h.get("touches_removal"):
                signals["named in a record that touches removal"] += 1
                hit = True
            if value(h.get("origin")):
                signals["a source states where they came from"] += 1
                quoted.append([p["name"], value(h["origin"]), tier_of(h["origin"])])
                hit = True
            if not hit:
                signals["no community signal on the card at all"] += 1
    quoted.sort()
    rows = [[k, v, pct(v, total)] for k, v in sorted(signals.items(), key=lambda kv: -kv[1])]
    return {
        "id": "community",
        "title": "Composition and types",
        "lead": ("What KINDS of people the sources show, counted only where a source says "
                 "so. %d of %d persons carry no community signal at all: the post-office "
                 "returns that mint most of this layer print a name and a town and nothing "
                 "else. Every row below is a source speaking, not a reading of a surname."
                 % (signals["no community signal on the card at all"], total)),
        "tables": [
            {"title": "Community signals on the card", **plain_table(
                ["signal", "persons", "share"], rows, "lrr")},
            {"title": "Every stated origin, quoted", **plain_table(
                ["person", "as the source puts it", "tier"], quoted, "lll")},
        ],
        "notes": [
            "NOBODY'S COMMUNITY IS READ OFF THEIR NAME HERE. A surname pool is how T-1177 "
            "will RECONSTRUCT the Irish, German, French-Canadian, Métis, Native and free "
            "Black town the register implies; it is not evidence about a person the sources "
            "merely name, and using it as evidence would manufacture exactly the "
            "attributions that ticket is required to mark as reconstructed.",
            "What the sources are silent about, in this layer: every child, every servant "
            "and apprentice, the garrison below officer rank, the harbour-works gang, the "
            "crews in port, and the women of nearly every household the returns name.",
        ],
    }


def sec_should_have_held(L) -> dict:
    """The buckets the model and reconstruction bands below must supply. NO NUMBERS."""
    buckets = [
        ["the women and children of the households the returns name", "T-1170, T-1171, T-1174"],
        ["servants, apprentices, journeymen and clerks", "T-1171, T-1183, T-1189"],
        ["the labouring trades: labourers, carpenters, teamsters, sawyers, boatmen",
         "T-1347"],
        ["boarders, lodgers and hotel guests, and the beds they filled", "T-1175"],
        ["the Fort Dearborn garrison below officer rank, and soldiers' families", "T-1176"],
        ["the Native, Métis, free Black, Irish and German town the register implies",
         "T-1177"],
        ["the transient population: land-sale visitors, the harbour gang, crews ashore",
         "T-1178"],
        ["the stores, shops, professions and lodging houses with no proprietor named",
         "T-1184 to T-1188"],
    ]
    return {
        "id": "should_have_held",
        "title": "What the town should have held",
        "lead": ("Every axis above is a count of the KNOWN layer. This is the list of what "
                 "it is missing, by bucket and by the ticket that owns it. THERE ARE NO "
                 "NUMBERS IN THIS SECTION ON PURPOSE: the quantities are T-1293's model and "
                 "T-1166's order book, and a number typed here would be a second, unsourced "
                 "answer to the same question."),
        "tables": [
            {"title": "The buckets", **plain_table(
                ["bucket", "the ticket that owns it"], buckets, "ll")},
        ],
        "notes": [],
    }


# The section ids, in the order the report reads them. The CLI names above are
# shorter on purpose (`origin` selects `origin_and_arrival`); this is the list the
# document itself must hold, and a section that goes missing fails against it.

# ---------------------------------------------------------------------------
# T-1393 — per-attribute completeness
# ---------------------------------------------------------------------------
#
# THE NINE QUESTIONS, ASKED OF EVERY PERSON. The rest of this profile reads the layer
# one axis at a time and each axis chooses its own denominator, so nowhere in it can a
# reader see whether ONE person is answered on all nine. This section asks them together.
#
# IT COUNTS THREE ANSWERS AND NOT TWO. A value at a tier; a value stated with no tier
# anywhere on the card (`division` and `relationship` are bare strings — the vocabulary
# lists their terms and nothing records a confidence); and no answer at all. Folding the
# middle column into `attested` would make an untiered string into evidence, which is the
# one thing this layer may not do, and folding it into `unknown` would say the card is
# silent where it speaks. So it is printed as what it is.
#
# A STATED ABSENCE IS AN ANSWER. "A role, or a stated reason for having none" is the
# ticket's phrasing and it is meant: an `occupation` of `none_recorded` carrying a note
# that says WHY no trade is recorded answers the question. 1,939 of the layer's people
# are answered that way and only 330 by a role, and the second table below keeps those
# two apart so the first table cannot be read as a town of tradesmen.

UNTIERED = "stated, no tier written"

COMPLETENESS_NOT_ASSERTED = (None, "", "unknown", "none_recorded", "unplaced")


def block_tier(block) -> str:
    """The tier a block carries — its own `tier` where it writes one, else `confidence`."""
    if isinstance(block, dict):
        tier = block.get("tier")
        if tier in TIERS:
            return tier
    return tier_of(block)


def _best_tier(tiers: list) -> str:
    """The strongest tier in a set of claims; UNTIERED when none of them grades itself."""
    for t in TIERS:
        if t in tiers:
            return t
    return UNTIERED


def _c_sex(h, p, pools) -> tuple:
    sex, rule = sex_of(p, *pools)
    tier = next(r["tier"] for r in SEX_RULES if r["rule"] == rule)
    if sex is None:
        return False, "unknown", ((p.get("sex_basis") or {}).get("note")
                                  or "no rule in SEX_RULES reaches this name")
    return True, tier, ""


def _c_age(h, p, pools) -> tuple:
    block = p.get("age_band")
    if value(block) in COMPLETENESS_NOT_ASSERTED:
        return False, "unknown", ((block or {}).get("note") if isinstance(block, dict)
                                  else None) or "the card carries no age band"
    return True, block_tier(block), ""


def _household_axis(field):
    def read(h, p, pools) -> tuple:
        block = h.get(field)
        if value(block) in COMPLETENESS_NOT_ASSERTED:
            return False, "unknown", "the household card asserts no %s" % field
        return True, block_tier(block), ""
    return read


def _c_role(h, p, pools) -> tuple:
    roles = p.get("roles") or []
    if roles:
        # A ROLE BLOCK IS NOT A VALUE BLOCK. It carries `role`, not `value`, so
        # `tier_of` reads it as asserting nothing; its grade is on `confidence`.
        return True, _best_tier([r.get("confidence") for r in roles]), ""
    occ = p.get("occupation")
    if value(occ) not in COMPLETENESS_NOT_ASSERTED:
        return True, block_tier(occ), ""
    # A STATED REASON FOR HAVING NONE. The note is the answer; the tier is the one the
    # block claims for itself, which for almost every row is `reconstructed` — the pass
    # declining to read a trade into a list of names rather than drawing one.
    if isinstance(occ, dict) and (occ.get("note") or "").strip():
        return True, block_tier({"value": "stated_absence",
                                 "confidence": occ.get("confidence")}), ""
    return False, "unknown", "no role, and no note saying why there is none"


def _c_division(h, p, pools) -> tuple:
    div = h.get("division")
    if div in COMPLETENESS_NOT_ASSERTED:
        return False, "unknown", ("the household stands `unplaced` — no source puts it "
                                  "on a side of the river")
    return True, UNTIERED, ""


def _c_relationship(h, p, pools) -> tuple:
    rel = p.get("relationship")
    if rel in COMPLETENESS_NOT_ASSERTED:
        return False, "unknown", "the person carries no relationship to the household"
    return True, UNTIERED, ""


COMPLETENESS_AXES = [
    ("sex", "person", "persons[].sex, ruled by sex_basis", _c_sex),
    ("age band", "person", "persons[].age_band", _c_age),
    ("arrival", "household", "arrival", _household_axis("arrival")),
    ("origin", "household", "origin", _household_axis("origin")),
    ("reason for coming", "household", "reason_for_coming",
     _household_axis("reason_for_coming")),
    ("a role, or a stated reason for having none", "person",
     "persons[].roles, else persons[].occupation", _c_role),
    ("presence on the scene date", "household", "present_on_scene_date",
     _household_axis("present_on_scene_date")),
    ("division", "household", "division", _c_division),
    ("household relationship", "person", "persons[].relationship", _c_relationship),
]

COMPLETENESS_COLUMNS = [t for t in TIERS if t != "unknown"] + [UNTIERED]

# THE ROWS WHOSE STATED REASON THEIR OWN CARD CONTRADICTS — and there are none (T-1395,
# 2026-09-21). This table existed for exactly one row. `reconstruct_sex_age.collective()`
# read a name as a group when any token of it stood in the sex pass's COLLECTIVE table, and
# `the` stood in that table because "the rest of the household, unnamed" is a count and not
# a name. "The Harmon daughter later known as Mrs A. G. Burley" begins with the same article
# and is ONE woman: Andreas names her singly, the card gives her one sex and seats her as a
# daughter. So her age band carried the collective refusal — "this row stands for more than
# one person" — over a row that stands for exactly one. The refusal's EFFECT was right (no
# band may be drawn) and its STATED REASON was wrong, which is a provenance defect and not a
# rounding error, so it was named here rather than quietly patched and the fix was left with
# the pass that writes the note. That pass has made it: a group is a group WORD and not an
# article, and her band is now refused for the reason her own card earns — a household's
# child word and a later source's married style, neither of them dated to the scene and
# neither of them an age. THE TABLE IS KEPT, EMPTY, because it is this report's standing
# question: a row whose note argues with its own card belongs here the day one appears.
CONTRADICTED_ROWS = {}


def sec_completeness(L) -> dict:
    total = len(L.people)
    grids = {name: Counter() for name, _, _, _ in COMPLETENESS_AXES}
    unanswered = defaultdict(list)
    answered_on_all = 0
    for h, p in L.people:
        every = True
        for name, _, _, read in COMPLETENESS_AXES:
            ok, tier, why = read(h, p, L.pools)
            grids[name][tier if ok else "unanswered"] += 1
            if not ok:
                every = False
                unanswered[name].append((h, p, why))
        answered_on_all += 1 if every else 0

    rows = []
    for name, carried_by, read_from, _ in COMPLETENESS_AXES:
        g = grids[name]
        ans = total - g["unanswered"]
        rows.append([name, carried_by, ans, pct(ans, total)]
                    + [g[c] for c in COMPLETENESS_COLUMNS] + [g["unanswered"]])

    role_grid = Counter()
    for h, p in L.people:
        if p.get("roles"):
            role_grid["a role, dated and sourced"] += 1
        elif value(p.get("occupation")) not in COMPLETENESS_NOT_ASSERTED:
            role_grid["an occupation, undated"] += 1
        elif isinstance(p.get("occupation"), dict) and (p["occupation"].get("note") or ""):
            role_grid["a stated reason for having none"] += 1
        else:
            role_grid["nothing"] += 1
    role_rows = [[k, role_grid[k], pct(role_grid[k], total)] for k in
                 ["a role, dated and sourced", "an occupation, undated",
                  "a stated reason for having none", "nothing"]]

    named = {}
    for name, rowlist in unanswered.items():
        for h, p, why in rowlist:
            if len(named) > 40 or (name == "division"):
                continue
            entry = named.setdefault(p["id"], {"hh": h["id"], "name": p.get("name") or "",
                                               "axes": [], "why": why})
            entry["axes"].append(name)
    silent_rows = [[pid, e["name"], e["hh"], ", ".join(e["axes"]),
                    CONTRADICTED_ROWS.get(pid, e["why"]).split(".")[0] + "."]
                   for pid, e in sorted(named.items())]

    unplaced = grids["division"]["unanswered"]
    by_roll = Counter(str(h.get("source_pass") or "unclaimed")
                      for h, p, _ in unanswered["division"])
    roll_rows = [[roll, n, pct(n, unplaced)] for roll, n in by_roll.most_common()]

    zeroed = [name for name, _, _, _ in COMPLETENESS_AXES if grids[name]["unanswered"] == 0]
    return {
        "id": "completeness",
        "title": "Per-attribute completeness",
        "lead": ("THE NINE QUESTIONS ASKED OF EVERY ONE OF THE %d PEOPLE, TOGETHER. %d of "
                 "the nine axes leave nobody unanswered. Sex leaves %d and age band %d — "
                 "the collective rows, \"the rest of the Beaubien household, unnamed\" and "
                 "their kind, which name nobody and so can carry neither, and one row that "
                 "names one woman and still earns no band; every one of them is named "
                 "below. Division leaves %d, the people of the %d households no "
                 "source puts on a side of the river, and that is the layer's largest "
                 "remaining hole: T-1198 seats the households the evidence places and "
                 "T-1199 the reconstructed ones, and until they run this column cannot "
                 "read zero without inventing ground. %d people are answered on all nine. "
                 "Two axes answer in a bare string that carries no confidence anywhere on "
                 "the card — they are counted under \"%s\" and not under a tier, because a "
                 "value with no tier is not a value at a tier."
                 % (total, len(zeroed), grids["sex"]["unanswered"],
                    grids["age band"]["unanswered"], unplaced,
                    sum(1 for h in L.records if h.get("division") == "unplaced"),
                    answered_on_all, UNTIERED)),
        "tables": [
            {"title": "Every person, every attribute", **plain_table(
                ["attribute", "carried by", "answered", "share"] + COMPLETENESS_COLUMNS
                + ["not answered"], rows,
                "llrr" + "r" * (len(COMPLETENESS_COLUMNS) + 1),
                note=("The tier columns and \"not answered\" sum to %d on every row. "
                      "\"%s\" is `division` and `relationship`, which the index's "
                      "vocabulary lists as controlled terms and no card grades."
                      % (total, UNTIERED)))},
            {"title": "A role, or a stated reason for having none", **plain_table(
                ["what the card carries", "persons", "share"], role_rows, "lrr",
                note=("A stated absence is an answer and it is not a trade. The note on "
                      "those %d cards says why the sources record no occupation — a list "
                      "of uncalled-for letters prints a name and no trade; the sources of "
                      "1835 name the occupations of heads and almost never those of wives, "
                      "children or the people counted with them."
                      % role_grid["a stated reason for having none"]))},
            {"title": "The person rows that answer nothing", **plain_table(
                ["person", "as the card names them", "household", "axes left unanswered",
                 "what the card gives as the reason"], silent_rows, "lllll",
                note=("Named rather than summed away, which is the whole of this section. "
                      "Every reason printed here is the one its own card gives, and no row "
                      "argues with itself: `harmon_daughter_burley` carried a collective "
                      "refusal over a row naming one woman until T-1395 gave her the "
                      "refusal her own evidence earns — a household's child word and a "
                      "later source's married style, neither dated to the scene and "
                      "neither an age."))},
            {"title": "The unplaced, by the roll they were minted off", **plain_table(
                ["roll", "persons", "share of the unplaced"], roll_rows, "lrr",
                note=("%d persons in households standing `unplaced`. `unplaced` is a term "
                      "in the index's own division vocabulary and it is a statement — the "
                      "sources do not place this household — but it is not a division, so "
                      "this section counts it unanswered." % unplaced))},
        ],
        "notes": ["Every count here is re-derived from the cards by "
                  "`--build`; `--check` refuses a hand-edit. The axes are the nine T-1393 "
                  "names and the tool refuses a rebuild whose answered and unanswered rows "
                  "do not sum to the layer's persons on each of them."],
    }


SECTION_IDS = ["headcount", "completeness", "sex", "age", "origin_and_arrival",
               "roles", "households", "lodging", "buildings", "community",
               "should_have_held"]

SECTIONS = [
    ("headcount", sec_headcount),
    ("completeness", sec_completeness),
    ("sex", sec_sex),
    ("age", sec_age),
    ("origin", sec_origin),
    ("roles", sec_roles),
    ("households", sec_households),
    ("lodging", sec_lodging),
    ("buildings", sec_buildings),
    ("community", sec_community),
    ("should_have_held", sec_should_have_held),
]


# ---------------------------------------------------------------------------
# the document
# ---------------------------------------------------------------------------

class Layer:
    def __init__(self):
        self.index, self.records = load_layer()
        self.people = list(persons(self.records))
        self.pools = pools()


def build() -> dict:
    layer = Layer()
    sections = [fn(layer) for _, fn in SECTIONS]
    grades = Counter(p["grade"] for _, p in layer.people)
    sexed = sum(1 for _, p in layer.people
                if sex_of(p, *layer.pools)[0] is not None)
    aged = sum(1 for _, p in layer.people
               if age_band_of(p) in ("birth_year_known", "age_stated"))
    return {
        "schema": "population_profile_1835/1",
        "generated_by": "tools/profile_population_1835.py",
        "ticket": "T-1160",
        "as_of": AS_OF,
        "scene_date": SCENE_DATE,
        "_doc": ("The known population of 1 July 1835, per attribute and per tier. "
                 "DERIVED — do not hand-edit; run tools/profile_population_1835.py "
                 "--build. The Evidence hub's 'The town's people' topic renders this."),
        "compiled_from": [
            "data/residents/index.json",
            "data/research/residents/attribute_tiers.json (T-1158's tier census)",
            "data/residents/ (the household records it manifests)",
            "data/reconstruction/1835_invented_name_pools.json",
            "data/structures/",
            "data/town_census.json",
        ],
        "counts": {
            "persons": len(layer.people),
            "households": len(layer.records),
            "by_grade": {g: grades[g] for g in layer.index["vocabulary"]["grades"]},
            # T-1314. A reconstructed person the programme cannot re-derive is the thing
            # the 2026-09-02 retirement was for, and this profile refuses to describe a
            # town that holds one. A reconstructed person that NAMES its stage is not
            # that, and the profile counts them like anybody else.
            "reconstructed_answering_no_stage": sum(
                1 for _, p in layer.people
                if p.get("grade") == "reconstructed"
                and (p.get("reconstruction") or {}).get("stage") not in _stage_keys()),
            "persons_with_a_sex": sexed,
            "persons_with_a_dated_age": aged,
            "persons_with_a_role": sum(1 for _, p in layer.people if p.get("roles")),
            "households_naming_an_origin": sum(
                1 for h in layer.records if value(h.get("origin"))),
            "households_naming_a_reason": sum(
                1 for h in layer.records if value(h.get("reason_for_coming"))),
            "households_naming_a_lives_at": sum(
                1 for h in layer.records if value(h.get("lives_at"))),
            # T-1393. The nine axes asked of every person at once: how many axes leave
            # nobody unanswered, and how many people are answered on all nine. Both are
            # in `counts` rather than only in the section so that `--check` moves on them.
            "axes_answered_by_every_person": sum(
                1 for _, _, _, read in COMPLETENESS_AXES
                if all(read(h, p, layer.pools)[0] for h, p in layer.people)),
            "persons_answering_every_axis": sum(
                1 for h, p in layer.people
                if all(read(h, p, layer.pools)[0]
                       for _, _, _, read in COMPLETENESS_AXES)),
        },
        "vocabulary": {"age_bands": AGE_BANDS, "reasons_for_coming": REASONS_FOR_COMING,
                       "sex_rules": SEX_RULES},
        "sections": sections,
    }


_STAGE_KEYS = None


def _stage_keys() -> set:
    """The stages the reconstruction programme declares; empty if it is gone."""
    global _STAGE_KEYS
    if _STAGE_KEYS is None:
        path = ROOT / "data" / "reconstruction" / "1835_resident_reconstruction_programme.json"
        try:
            _STAGE_KEYS = {row.get("key")
                           for row in json.loads(path.read_text(encoding="utf-8"))
                           .get("stages") or []}
        except (OSError, ValueError):
            _STAGE_KEYS = set()
    return _STAGE_KEYS


def assertions(doc: dict) -> None:
    ids = [s["id"] for s in doc["sections"]]
    if ids != SECTION_IDS:
        raise Refused("the profile does not hold every section, in order: %s" % ids)
    counts = doc["counts"]
    if counts.get("reconstructed_answering_no_stage", 0) != 0:
        raise Refused("a `reconstructed` person answers to no stage of the reconstruction "
                      "programme — reconstruction happens at T-1167 under that programme, "
                      "never inside a profile and never unaccountably")
    if counts["persons_with_a_sex"] > counts["persons"]:
        raise Refused("more persons carry a sex than there are persons")
    # T-1393. The completeness table's arithmetic, checked rather than trusted: an axis
    # whose columns do not sum to the layer's persons has lost somebody, and a lost row
    # is exactly the thing this section exists to refuse.
    comp = next((s for s in doc["sections"] if s["id"] == "completeness"), None)
    if comp is None:
        raise Refused("the profile carries no per-attribute completeness section")
    axes = comp["tables"][0]
    if len(axes["rows"]) != len(COMPLETENESS_AXES):
        raise Refused("completeness: %d axes against the %d T-1393 names"
                      % (len(axes["rows"]), len(COMPLETENESS_AXES)))
    for row in axes["rows"]:
        tallied = sum(row[4:])
        if tallied != counts["persons"]:
            raise Refused("completeness: the axis %r counts %d persons against the "
                          "layer's %d — a row has been lost between the tiers"
                          % (row[0], tallied, counts["persons"]))
        if row[2] != counts["persons"] - row[-1]:
            raise Refused("completeness: the axis %r says %d answered and %d unanswered, "
                          "which do not make %d" % (row[0], row[2], row[-1],
                                                    counts["persons"]))
    for section in doc["sections"]:
        if not section.get("lead"):
            raise Refused("%s: a section with no lead sentence says nothing"
                          % section["id"])
        for t in section["tables"]:
            for row in t["rows"]:
                if len(row) != len(t["headers"]):
                    raise Refused("%s/%s: a row is %d cells against %d headers"
                                  % (section["id"], t["title"], len(row),
                                     len(t["headers"])))
    should = next(s for s in doc["sections"] if s["id"] == "should_have_held")
    for t in should["tables"]:
        for row in t["rows"]:
            if any(re.search(r"\d", str(cell)) and not re.fullmatch(r"T-\d+.*", str(cell))
                   for cell in row):
                raise Refused("'What the town should have held' carries a number: %r. "
                              "The quantities are T-1293's model and T-1166's order book."
                              % row)


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def md_table(t: dict) -> list:
    aligns = t.get("aligns") or "l" * len(t["headers"])
    out = ["| " + " | ".join(str(h) for h in t["headers"]) + " |",
           "|" + "|".join("---:" if aligns[i] == "r" else "---"
                          for i in range(len(t["headers"]))) + "|"]
    for row in t["rows"]:
        out.append("| " + " | ".join(str(c).replace("|", "\\|") for c in row) + " |")
    return out


def report(doc: dict) -> str:
    out = ["# The known population of 1 July 1835", "",
           "Generated by `%s --build`. Every figure is re-derived; `--check` proves this "
           "file is what the layer says. Ticket %s, as of %s."
           % (doc["generated_by"], doc["ticket"], doc["as_of"]), "",
           "> A PROFILE OF THE EVIDENCE, NOT OF THE TOWN. %d person entries in %d "
           "households against a town census of 3,265 people. What is thin below is the "
           "record, and the tickets named against each hole are what fill it."
           % (doc["counts"]["persons"], doc["counts"]["households"]), ""]
    for section in doc["sections"]:
        out += ["## %s" % section["title"], "", section["lead"], ""]
        for t in section["tables"]:
            out += ["### %s" % t["title"], ""] + md_table(t) + [""]
            if t.get("note"):
                out += [t["note"], ""]
        for note in section["notes"]:
            out += ["*%s*" % note, ""]
    return "\n".join(out).rstrip("\n") + "\n"


def write(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report(doc), encoding="utf-8")


def read_committed():
    try:
        return json.loads(OUT.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# the vocabularies in data/residents/index.json
# ---------------------------------------------------------------------------

def cmd_write_vocabulary() -> int:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    vocab = index.setdefault("vocabulary", {})
    vocab["age_bands"] = AGE_BANDS
    vocab["reasons_for_coming"] = REASONS_FOR_COMING
    INDEX.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    print("  wrote %d age band(s) and %d reason(s) to %s vocabulary"
          % (len(AGE_BANDS), len(REASONS_FOR_COMING), INDEX.relative_to(ROOT)))
    return 0


def vocabulary_problems() -> list:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    vocab = index.get("vocabulary") or {}
    problems = []
    for key, want in (("age_bands", AGE_BANDS), ("reasons_for_coming", REASONS_FOR_COMING)):
        got = vocab.get(key)
        if got is None:
            problems.append("vocabulary.%s is missing from data/residents/index.json — the "
                            "profile prints a term and nothing under data/ says what it "
                            "means. Run --write-vocabulary." % key)
        elif got != want:
            problems.append("vocabulary.%s disagrees with the tool that owns it. Run "
                            "--write-vocabulary." % key)
    terms = {r["term"] for r in REASONS_FOR_COMING}
    unruled = [t for t, _ in REASON_RULES if t not in terms]
    if unruled:
        problems.append("REASON_RULES buckets into terms the vocabulary does not hold: %s"
                        % ", ".join(unruled))
    return problems


# ---------------------------------------------------------------------------
# check and self-test
# ---------------------------------------------------------------------------

def check() -> int:
    committed = read_committed()
    if committed is None:
        print("REFUSED: %s is missing or unreadable — run --build" % OUT.relative_to(ROOT))
        return 1
    try:
        fresh = build()
    except Refused as exc:
        print("REFUSED: %s" % exc)
        return 1
    if fresh["counts"] != committed["counts"]:
        moved = sorted(k for k in set(fresh["counts"]) | set(committed["counts"])
                       if fresh["counts"].get(k) != committed["counts"].get(k))
        print("REFUSED: a rebuild does not produce the committed counts (%s) — run --build"
              % ", ".join(moved))
        return 1
    if fresh["sections"] != committed["sections"]:
        moved = [s["id"] for s, o in zip(fresh["sections"], committed["sections"]) if s != o]
        print("REFUSED: a rebuild does not produce the committed sections (%s) — run --build"
              % ", ".join(moved or ["the section list itself"]))
        return 1
    if fresh["vocabulary"] != committed["vocabulary"]:
        print("REFUSED: the committed vocabulary is not the tool's — run --build")
        return 1
    try:
        assertions(committed)
    except Refused as exc:
        print("REFUSED: %s" % exc)
        return 1
    problems = vocabulary_problems()
    if problems:
        print("REFUSED: " + "; ".join(problems))
        return 1
    if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != report(committed):
        print("REFUSED: %s is not what the profile says — run --build"
              % REPORT.relative_to(ROOT))
        return 1
    c = committed["counts"]
    print("%d persons in %d households profiled on %d axes; %d carry a sex, %d a dated "
          "age, %d a role; reconstructed %d"
          % (c["persons"], c["households"], len(committed["sections"]),
             c["persons_with_a_sex"], c["persons_with_a_dated_age"],
             c["persons_with_a_role"], c["by_grade"]["reconstructed"]))
    return 0


def self_test() -> int:
    """Break each rule and require its assertion to fire."""
    doc = read_committed() or build()
    faults = []

    fired = []

    def fires(name, mutate):
        fired.append(name)
        broken = json.loads(json.dumps(doc))
        mutate(broken)
        try:
            assertions(broken)
        except Refused as exc:
            print("  fires: %s -> %s" % (name, str(exc)[:70]))
            return
        faults.append(name)

    def section(d, sid):
        return next(s for s in d["sections"] if s["id"] == sid)

    fires("a reconstructed person no programme stage claims appears in a profile",
          lambda d: d["counts"].__setitem__("reconstructed_answering_no_stage", 1))
    fires("more sexes than persons",
          lambda d: d["counts"].__setitem__("persons_with_a_sex",
                                            d["counts"]["persons"] + 1))
    fires("a section goes missing", lambda d: d["sections"].pop(2))
    fires("a section loses its lead sentence",
          lambda d: section(d, "sex").__setitem__("lead", ""))
    fires("a table row does not fit its headers",
          lambda d: section(d, "headcount")["tables"][0]["rows"].append(["only one cell"]))
    fires("'what the town should have held' grows a number",
          lambda d: section(d, "should_have_held")["tables"][0]["rows"]
          .append(["1,983 women and children", "T-1174"]))
    # T-1393's three: an axis that loses a person between its tiers, an axis list that
    # stops being the nine the ticket names, and the section going away altogether.
    fires("a completeness axis loses a person between its tiers",
          lambda d: section(d, "completeness")["tables"][0]["rows"][0].__setitem__(
              4, section(d, "completeness")["tables"][0]["rows"][0][4] - 1))
    fires("a completeness axis's answered and unanswered do not make the layer",
          lambda d: section(d, "completeness")["tables"][0]["rows"][0].__setitem__(
              2, 0))
    fires("the nine axes stop being nine",
          lambda d: section(d, "completeness")["tables"][0]["rows"].pop())
    fires("the per-attribute completeness section goes away",
          lambda d: d["sections"].__setitem__(
              1, dict(section(d, "completeness"), id="something_else")))

    # The two judgements, exercised against the rules rather than the document.
    try:
        reason_term("a reason no rule in this tool has ever seen")
    except Refused:
        fired.append("an unruled reason for coming")
        print("  fires: an unruled reason for coming is refused, not bucketed as other")
    else:
        faults.append("an unruled reason for coming")

    male, female, both = pools()
    probes = [
        ({"name": "Mrs. Elizabeth Forbes"}, "female", "inferred_title"),
        ({"name": "Sarah Whistler"}, "female", "inferred_forename"),
        ({"name": "Nathaniel Pope"}, "male", "inferred_forename"),
        ({"name": "J. W. Smith"}, None, "unknown"),
        ({"name": "Capt. Seagrave"}, None, "unknown"),
        ({"name": "Mary Smith", "sex": "male"}, "male", "recorded"),
    ]
    for person, want_sex, want_rule in probes:
        got = sex_of(person, male, female, both)
        if got != (want_sex, want_rule):
            faults.append("sex_of(%r) gave %r, wanted %r"
                          % (person["name"], got, (want_sex, want_rule)))
        else:
            print("  holds: %-22s -> %s by %s" % (person["name"], want_sex, want_rule))

    if faults:
        print("SELF-TEST FAILED — " + "; ".join(faults))
        return 1
    print("all %d assertions fire when broken, and the sex rule holds on %d probes"
          % (len(fired), len(probes)))
    return 0


def main(argv: list) -> int:
    if "--list" in argv:
        for name, fn in SECTIONS:
            print("%-18s %s" % (name, (fn.__doc__ or fn.__name__).splitlines()[0]))
        return 0
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    if "--write-vocabulary" in argv:
        return cmd_write_vocabulary()
    if "--build" in argv:
        doc = build()
        assertions(doc)
        write(doc)
        cmd_write_vocabulary()
        print("wrote %s and %s (%d persons, %d sections)"
              % (OUT.relative_to(ROOT), REPORT.relative_to(ROOT),
                 doc["counts"]["persons"], len(doc["sections"])))
        return 0

    wanted = [a for a in argv if not a.startswith("-")]
    known = dict(SECTIONS)
    for name in wanted:
        if name not in known:
            print("unknown section %r — try --list" % name, file=sys.stderr)
            return 2
    layer = Layer()
    for i, name in enumerate(wanted or [n for n, _ in SECTIONS]):
        section = known[name](layer)
        print(("\n" if i else "") + "## " + section["title"])
        print()
        print(section["lead"])
        for t in section["tables"]:
            print()
            print("### " + t["title"])
            print()
            table(t["headers"], t["rows"], t.get("aligns", ""))
        for note in section["notes"]:
            print()
            print(note)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
