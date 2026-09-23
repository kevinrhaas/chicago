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
OUT = ROOT / "data" / "reconstruction" / "1835_population_profile.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_population_profile.md"

SCENE_DATE = "1835-07-01"
AS_OF = "2026-09-18"


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
]

# Ordered: the FIRST pattern that matches the stated reason names it. Specific
# before general, because "trade and tavern keeping" is a tavern and "a law
# practice" beside a county office is the office.
REASON_RULES = [
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
]

FEMALE_TITLES = ("mrs", "miss", "madam", "madame", "widow")
MALE_TITLES = ("mr", "master")

SEX_RULES = [
    {"rule": "recorded", "means": "a source records the sex on the card"},
    {"rule": "inferred_title", "means": "the read name carries a gendered title (Mrs, Miss, Widow, Mr)"},
    {"rule": "inferred_forename",
     "means": "the forename stands in exactly one sex's period pool and in no other"},
    {"rule": "unknown", "means": "the name is an initial, a surname alone, or carries neither signal"},
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
    """(sex or None, the rule that says so)."""
    recorded = person.get("sex")
    if recorded:
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


LODGING_FUNCTIONS = {"hotel", "tavern", "boarding_house", "inn", "coffee_house"}


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
            {"title": "Attribute values already standing at the reconstructed tier",
             **plain_table(["household", "field", "value", "why it is at that tier"],
                           already, "llll")},
        ],
        "notes": ["No PERSON carries the `reconstructed` grade (%d) and this ticket does "
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
        "lead": ("%d of %d persons (%s) can be sexed at all — %d because a source records "
                 "it, %d from a gendered title, %d from a forename that stands in exactly "
                 "one sex's period pool. The rest are an initial, a surname alone, or a "
                 "forename both sexes used."
                 % (known, total, pct(known, total), by_rule["recorded"],
                    by_rule["inferred_title"], by_rule["inferred_forename"])),
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
    return {
        "id": "age",
        "title": "Age",
        "lead": ("%d of %d persons carry a year or an age; %d more are placed in an adult "
                 "band by what they are recorded DOING — a poll, a tax list, a muster, a "
                 "trade, an office, a marriage. %d persons carry nothing that bears on age. "
                 "THERE IS NO AGE PYRAMID HERE: %d dated ages cannot make one, which is "
                 "T-1174's brief."
                 % (dated, total, adults, bands["unknown"], dated)),
        "tables": [
            {"title": "Age bands", **plain_table(
                ["band", "persons", "share", "what it means"], rows, "lrrl")},
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
                  "are all at zero — the whole of T-1171, T-1173 and T-1175."
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
        rows.append([h["name"], sid, fn, kind, tier_of(h["lives_at"])])
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
        "notes": ["No household in the known layer lodges on a vessel. The crews ashore on "
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
        ["servants, apprentices, journeymen and clerks", "T-1171, T-1173, T-1189"],
        ["the labouring trades: labourers, carpenters, teamsters, sawyers, boatmen",
         "T-1173"],
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
SECTION_IDS = ["headcount", "sex", "age", "origin_and_arrival", "roles", "households",
               "lodging", "buildings", "community", "should_have_held"]

SECTIONS = [
    ("headcount", sec_headcount),
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
            "persons_with_a_sex": sexed,
            "persons_with_a_dated_age": aged,
            "persons_with_a_role": sum(1 for _, p in layer.people if p.get("roles")),
            "households_naming_an_origin": sum(
                1 for h in layer.records if value(h.get("origin"))),
            "households_naming_a_reason": sum(
                1 for h in layer.records if value(h.get("reason_for_coming"))),
            "households_naming_a_lives_at": sum(
                1 for h in layer.records if value(h.get("lives_at"))),
        },
        "vocabulary": {"age_bands": AGE_BANDS, "reasons_for_coming": REASONS_FOR_COMING,
                       "sex_rules": SEX_RULES},
        "sections": sections,
    }


def assertions(doc: dict) -> None:
    ids = [s["id"] for s in doc["sections"]]
    if ids != SECTION_IDS:
        raise Refused("the profile does not hold every section, in order: %s" % ids)
    counts = doc["counts"]
    if counts["by_grade"].get("reconstructed", 0) != 0:
        raise Refused("the `reconstructed` grade is not zero — reconstruction begins at "
                      "T-1167 under its own programme, never inside a profile")
    if counts["persons_with_a_sex"] > counts["persons"]:
        raise Refused("more persons carry a sex than there are persons")
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

    def fires(name, mutate):
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

    fires("a reconstructed person appears in a profile",
          lambda d: d["counts"]["by_grade"].__setitem__("reconstructed", 1))
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

    # The two judgements, exercised against the rules rather than the document.
    try:
        reason_term("a reason no rule in this tool has ever seen")
    except Refused:
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
    print("all 7 assertions fire when broken, and the sex rule holds on 6 probes")
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
