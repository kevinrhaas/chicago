#!/usr/bin/env python3
"""Sex and age, read off the evidence and spent on the cards (T-1303, from T-1168).

    python3 tools/spend_person_sex_age.py             write the table, the cards, the ledger
    python3 tools/spend_person_sex_age.py --check     everything re-derives; nothing drifted
    python3 tools/spend_person_sex_age.py --report    rule by rule, what fired and what refused
    python3 tools/spend_person_sex_age.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. The owner asked that "all people should have a best profile", and the
layer did not have one: of 1,282 people, 99 carried a sex and 10 a birth year. T-1168 set
out the three tiers a profile may stand on — attested where a source says it, inferred
where the evidence about that person allows it, reconstructed from the population model
otherwise — and was split because the third tier needs the model's writer, which is
another run's work. THIS PASS IS THE FIRST TWO TIERS AND NOTHING ELSE. Where the evidence
is silent this pass stays silent, and T-1304 fills the silence from the model.

WHAT IT WRITES, in four rules, each of which says on the card which one fired.

  1. SEX FROM A GENDERED TITLE. "Mrs Rufus Brown", "Miss Eliza Chappel", "The Widow
     Wells" — the title is a statement about the person's sex made by whoever wrote the
     name down, and it is the strongest thing a name can carry. A RANK IS NOT A TITLE
     HERE: Capt., Col., Rev. and Maj. would be right nearly every time in this town and
     would still be a guess about the period rather than a fact about the person, so this
     pass reads none of them as male. That refusal is already the profile report's
     (T-1160) and it is kept here word for word.

  2. SEX FROM A FORENAME THAT STANDS IN ONE SEX'S NAMING ONLY. The table is built here,
     from this project's own evidence and nothing else: the people whose sex a source
     already records, and the period forename pools of
     data/reconstruction/1835_invented_name_pools.json, which were themselves assembled
     out of the naming this town has attested. A name the two disagree about, or that the
     recorded people themselves split, is REFUSED rather than decided. So are Jean,
     Marion, Leslie and Francis/Frances, by name, for the reason written beside each.

  3. A BIRTH INTERVAL FROM A DEATH NOTICE. Fergus's 1843 directory (1896) prints an
     obituary list with a death date and an age at death; `tools/spend_old_settlers.py`
     already adjudicated which of its entries meet which people and wrote the arithmetic
     onto the card. This pass spends that arithmetic into a `birth_year` — and only where
     BOTH SIDES SPELL A FORENAME. The crosswalk's own thin matches, where a single
     initial is the whole of the discriminator, are refused: a birth year is exactly the
     kind of value that makes a card read better than its evidence.

  4. A BIRTH INTERVAL FROM A MAN'S OWN AGE AT THE CALUMET CLUB. The registry of 27 May
     1879 prints the age each old settler gave as he registered, and
     data/research/old_settlers/people.json carries the adjudicated merge onto this
     layer's people. An age given at a reception forty-four years after the scene date is
     a recollection about himself, which is a better thing than a recollection about
     somebody else and still not a record of a birth.

WHAT IT REFUSES, and why the refusals are the point.

  * AN INITIAL FIRES NOTHING. 223 of these people are known only as "J. W. Smith" off a
     post-office list. There is no rule that sexes an initial, and the letter lists'
     measured lean is the population model's business (T-1304, which since 2026-09-18
     draws for them at the rate measured on the letter lists themselves), not this pass's.
  * A NAME OUTSIDE THE TABLE FIRES NOTHING. 384 people bear a forename this project has
     no evidence about. Extending the table to period names at large would be invention
     wearing an inference's clothes.
  * NO AGE FROM AN ADULT STATUS. A poll list, a civic office or a trade says a person was
     an adult; it does not say when they were born. The franchise's own age rule is not
     in any source record this project holds, so no year is derived from one. That is a
     finding for T-1304, and it is written into the ticket rather than into a card.
  * AND AN ADULT STATUS THE INTERVAL CONTRADICTS REFUSES THE INTERVAL (T-1179). The rule
     above is about DERIVING a year and is unchanged; this is its converse, which is a
     different statement and was missing. An obituary matched to a name by that name
     alone put George Smith four years old on the scene date while his own advertisements
     had him keeping the Exchange Coffee House through 1834 and 1835. Where an obituary's
     interval leaves a person under the 15 that any roll naming them in their own right
     requires, the SPEND is refused: the `birth_year` block written in its place asserts
     no year at all and carries `refused_because`. The crosswalk's match is not withdrawn
     and no age is asserted instead. Where the interval clears 15 and misses only the franchise's 20 — a
     floor this project admits it invented — nothing is struck out: the year is carried
     with `contradicted_by_the_card` beside it, which is T-1146's disposition and the one
     the letter-list ruling settled on. A man's own age about himself is only ever
     flagged, never refused.
  * NO `age_on_scene_date` OVER A BAND. Every interval this pass writes spans two birth
     years, so an age on 1 July 1835 spans three. Stating one would invent a precision
     the source does not have.
  * A VALUE ALREADY ON THE CARD IS NEVER TOUCHED. The mints own `sex` and the
     biographies own the ten `birth_year` blocks; this pass only ever fills an absence.

WHERE THE VALUES GO. `sex` stays the plain string the mints and the renderer already
read, and the reasoning arrives beside it in `sex_basis` — a `{value, confidence, note}`
claim block of the ordinary shape, so the card can print the tier and the reason without
any new machinery. `birth_year` is the block the biographied ten already use, with
`band` naming the two years the arithmetic leaves open.

AND THE MINTS MUST NOT DROP IT. `sex` is an owned key of the resident mints — a mint's
silence about a person's sex is its own answer and is never resurrected — so a mint
re-running would take this pass's fill with it. `tools/resident_mint_carry.py` carries a
`sex` that arrives with a `sex_basis`, exactly as it already carries `ladder_rule` and
the roles derived after the mint. A pass that writes into a mint-owned key without
saying so is a pass whose work vanishes at the next rebuild.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
POOLS = ROOT / "data" / "reconstruction" / "1835_invented_name_pools.json"
OLD_SETTLERS = ROOT / "data" / "research" / "old_settlers" / "people.json"
TABLE = ROOT / "data" / "research" / "residents" / "forename_sex.json"
LEDGER = ROOT / "data" / "research" / "residents" / "sex_age_spend.json"

SCENE_DATE = "1835-07-01"

# HOW THIS PASS RECOGNISES ITS OWN WORK, which `--check` needs before it can take the
# committed cards back to what they were BEFORE this pass and derive them again. Without
# that step the forename table would read its own fills back in as evidence and grade its
# own homework, and every re-run would sex a few more people off the last run's guesses.
#
# A `sex_basis` block graded `inferred` is this pass's by construction — T-1304 writes
# the only other kind and grades it `reconstructed`, which is what `ours_sex` reads — and
# a `birth_year` is this pass's when it cites one of the two rolls below, which nothing
# else spends onto a person. Neither is a marker key on the card: a `derived_by` string
# repeated on 644 blocks is 24 kB of bookkeeping shipped to a browser that has no use for
# it, and `tools/measure_layer_reads.py` is right to ask what a figure nobody reads is
# doing in the payload. If another pass ever writes a person `birth_year` citing one of
# these rolls, `--check` fails loudly here rather than quietly mis-stripping — the
# self-test holds the invariant so that failure arrives with its reason attached.

# The two sources this pass cites. Both already resolve in data/sources/ and both are
# already cited by the passes that adjudicated the matches being spent here.
DEATHS_SOURCE = "fergus_1843_old_settler_death_notices"
REGISTRY_SOURCE = "calumet_club_early_chicago_1879"

# The roll that prints an age, and the day it was signed. Only one of the old-settler
# rolls carries `age_1879_as_read`, and the arithmetic below turns on its date.
REGISTRY_ROLL = "registry_1879_05_27"

# WHAT THE CARD ALREADY SAYS ABOUT THIS PERSON'S AGE, and it is a FLOOR rather than a
# year (T-1179). The refusals above say that no age may be derived from an adult status:
# a poll list does not record a birth. The converse is not the same statement and is the
# one this pass had been missing — an adult status cannot GIVE a birth year, but it can
# REFUTE one. George Smith advertised the Exchange Coffee House in the Democrat of 5
# November 1834 and again on 20 May 1835, and this pass spent an obituary onto his card
# that put him four years old on the scene date. Both readings cannot stand, and nothing
# in the tree noticed, because each pass only ever checked its own half.
#
# TWO FLOORS, AND THEY DO DIFFERENT THINGS, because the project does not hold them with
# the same conviction. Both are stated in data/reconstruction/1835_sex_age_model.json as
# conditionings on the age DRAW, and that file is candid about which is which:
#
#   * 15 at the date of any roll that names a person in their own right. The 1840
#     schedule "counts a child as a tally inside a household and never as a
#     correspondent", and the model takes 15 rather than 20 precisely so that an
#     apprentice or a journeyman on a trade roll is not excluded. This is the floor the
#     project defends in its own words, and an interval that puts a person UNDER it is
#     REFUSED: a name match cannot make a correspondent, a taxpayer or a coffee-house
#     keeper into a child of five.
#
#   * 20 on a poll, a tax list or a muster roll — the franchise's line. The model says of
#     it, in capitals, that THE FRANCHISE'S AGE RULE IS NOT IN ANY SOURCE, and carries it
#     under the liberty L-rc-age-conditioning. A floor this project admits it invented may
#     not be used to strike out evidence. So an interval that clears 15 and misses 20 is
#     not refused; it is CARRIED, with the disagreement written beside it, which is the
#     disposition T-1146 calls `contradicted` and the one the letter-list ruling settled
#     on: the pass says a collision instead of acting on it.
#
# AND A MAN'S OWN AGE ABOUT HIMSELF IS NEVER REFUSED, only ever flagged. Rule 4 above is
# a recollection by the person; rule 3 is an obituary matched to a name. Only the second
# is weak in the way a refusal answers.
#
# A refusal WRITES NOTHING ONTO THE PERSON except the refusal: the interval is not
# narrowed, no age is asserted, and the crosswalk's match is left exactly where
# tools/spend_old_settlers.py put it. What is refused is the SPEND, and the card says so
# in its own words so that a reader meets the disagreement rather than one side of it.
REFUSAL_FLOOR = 15
FRANCHISE_FLOOR = 20
CIVIC_LIST_PREFIXES = ("poll_", "tax_", "muster_")

# A roll the layer was minted off that names a person IN THEIR OWN RIGHT. A church
# register is deliberately absent: it names infants, which is the one roll whose entries
# are evidence of the opposite.
OWN_RIGHT_KEYS = ("press_evidence", "book_evidence", "letter_list_returns")
REGISTRY_DAY = "27 May 1879"

# Rule 1. A title is a statement about the person; a rank is a guess about the period.
GENDERED_TITLES = {
    "mrs": "female", "miss": "female", "madam": "female", "madame": "female",
    "widow": "female", "mr": "male", "master": "male",
}

# Tokens that stand in front of a name without being one. Ranks and honorifics are here
# so the forename behind them is the one that is read — "Lieut. James Allen" is James,
# not Lieut — and the articles are here because "The four Temple children" is a
# description of people rather than the name of one.
NOT_A_FORENAME = {
    "col": "a rank",
    "colonel": "a rank",
    "capt": "a rank",
    "captain": "a rank",
    "maj": "a rank",
    "major": "a rank",
    "lieut": "a rank",
    "lieutenant": "a rank",
    "gen": "a rank",
    "general": "a rank",
    "sergt": "a rank",
    "sergeant": "a rank",
    "corp": "a rank",
    "rev": "an honorific",
    "reverend": "an honorific",
    "dr": "an honorific",
    "doctor": "an honorific",
    "hon": "an honorific",
    "judge": "an honorific",
    "esq": "an honorific",
    "prof": "an honorific",
    "messrs": "an honorific, and a plural one",
}

# Words that say the "name" describes a GROUP rather than naming a person — "The rest of
# the Beaubien household, unnamed", "The four Temple children". A collective fires
# nothing, and it may not be read past either: walking on to the next token would sex
# four Temple children by the surname Temple, which the table holds as a man's forename.
#
# A GROUP WORD, NOT AN ARTICLE (T-1395). `the` stood in this table until 2026-09-21,
# on the reading that "the names that carry it describe people rather than name one".
# It does not: an article is how English introduces a noun and it says nothing about how
# many people the noun stands for. Every genuine collective row here carries a group WORD
# as well — rest, household, children, unnamed — and keeps its refusal unchanged with the
# article gone. What the article caught besides them was one woman, "The Harmon daughter
# later known as Mrs A. G. Burley", whom Andreas takes his particulars of Dr Harmon from:
# one sex, one seat in her father's house, and an age band refused for standing "for more
# than one person". She stands for exactly one, and a card that states a false reason for
# a true refusal is a provenance defect. The refusal she earns is written where the age is
# drawn, in tools/reconstruct_sex_age.py. The article would also have swallowed rule 1's
# own example, "The Widow Wells" — read as a group before the title it prints could sex
# her — which is the same defect one step earlier.
COLLECTIVE = {
    "rest": "'the rest of the household, unnamed' is a count, not a name",
    "four": "'the four Temple children' is a count, not a name",
    "children": "a description of a group",
    "household": "a description of a group",
    "unnamed": "the record saying in the name field that it has no name",
    "others": "a description of a group",
}

# Period contractions of a forename. Each is listed because EVERY expansion of it
# attested in this project is a man's name, so the contraction settles the sex without
# settling which name was contracted.
CONTRACTIONS = {
    "thos": "Thomas",
    "geo": "George",
    "chas": "Charles",
    "wm": "William",
    "jas": "James",
    "jno": "John",
    "benj": "Benjamin",
    "saml": "Samuel",
    "danl": "Daniel",
    "robt": "Robert",
    "richd": "Richard",
    "edwd": "Edward",
    "nathl": "Nathaniel",
    "alexr": "Alexander",
    "jos": "Joseph, Josiah or Joshua",
}

# Rule 2's named refusals. A name here fires nothing however the table's evidence falls.
AMBIGUOUS = {
    "jean": "French Jean is a man's name and English Jean a woman's, and this town holds "
            "both traditions at once — Col. Jean Baptiste Beaubien on one side of the "
            "river and New England families on the other. The pools carry it as male; "
            "that is a fact about the pool's community, not about an unplaced name on a "
            "letter list.",
    "marion": "Borne by men and by women through this whole period, and the project has "
              "no bearer of it whose sex a source records.",
    "leslie": "A surname used as a forename, and used for both sexes; a name that "
              "travels from a surname carries no sex with it.",
    "francis": "Francis and Frances are a man's name and a woman's name that a "
               "nineteenth-century page prints almost interchangeably, and the "
               "difference is one letter that OCR and a compositor both lose.",
    "frances": "Frances and Francis are a man's name and a woman's name that a "
               "nineteenth-century page prints almost interchangeably, and the "
               "difference is one letter that OCR and a compositor both lose.",
}

SPLIT_BY_THE_EVIDENCE = ("the people whose sex a source records do not agree about this "
                         "name, so the table refuses it rather than counting heads")


# --- reading a name --------------------------------------------------------------------

def tokens(name: str) -> list:
    """The alphabetic tokens of a read name, lowercased, in order."""
    out = []
    for word in re.split(r"[\s,]+", (name or "").strip()):
        clean = re.sub(r"[^A-Za-z]", "", word)
        if clean:
            out.append(clean.lower())
    return out


def read_name(name: str) -> tuple:
    """(sex_from_title, forename, why) — what a read name offers, before any table.

    `why` is one of `title`, `contraction`, `forename`, `initial`, `no_name`, and it is
    the rule that STOPPED the read rather than the rule that decided a sex.
    """
    toks = tokens(name)
    if any(tok in COLLECTIVE for tok in toks):
        return None, None, "a_group_not_a_person"
    for tok in toks:
        if tok in GENDERED_TITLES:
            return GENDERED_TITLES[tok], None, "title"
    for tok in toks:
        if tok in NOT_A_FORENAME:
            continue
        if tok in CONTRACTIONS:
            return None, tok, "contraction"
        if len(tok) < 3:
            # An initial ends the read. `J. W. Smith` has no forename to offer, and
            # walking past it to the surname would sex a man by his family's name.
            return None, None, "initial"
        return None, tok, "forename"
    return None, None, "no_name"


# --- the layer -------------------------------------------------------------------------

def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def households() -> dict:
    """household id -> the committed record, in card order."""
    return {path.stem: load(path) for path in sorted(HOUSEHOLDS.glob("hh_*.json"))}


def ours_sex(block) -> bool:
    """A `sex_basis` THIS pass wrote — one it READ, and so graded `inferred`.

    T-1304 draws a sex for the people this pass refuses and leaves a `sex_basis` of its
    own, graded `reconstructed`. That block is not this pass's to strip: stripping it
    would make `--check` re-derive a card without it, find the committed card carrying a
    sex this pass never writes, and fail every one of the 587 drawn people. The tier is
    the boundary, and each pass owns its own side of it.
    """
    return (isinstance(block, dict) and bool(block.get("note"))
            and block.get("confidence") != "reconstructed")


def ours_birth(block) -> bool:
    return isinstance(block, dict) and (block.get("sources") or []) in (
        [DEATHS_SOURCE], [REGISTRY_SOURCE])


def reconstructed(person: dict) -> bool:
    """A person a stage of the reconstruction programme wrote (T-1167).

    This pass READS a sex and a birth year off the evidence — a gendered title, a forename
    the corpus settles, an obituary. A person the household model DREW has neither: their
    sex is the model's draw and their forename came out of a name pool, so reading a sex
    back off that forename would be this layer's own invention returned to it as a finding,
    and the forename table would count an invented name as evidence. They are skipped
    everywhere here: not tabulated, not filled, not stripped.
    """
    rc = person.get("reconstruction")
    return isinstance(rc, dict) and bool(rc.get("stage"))


def without_this_pass(card: dict) -> dict:
    """The card as it stood before this pass ever ran. Pure, and the basis of `--check`."""
    out = json.loads(json.dumps(card))
    for person in out.get("persons") or []:
        if reconstructed(person):
            continue
        if ours_sex(person.get("sex_basis")):
            person.pop("sex_basis", None)
            person.pop("sex", None)
        if ours_birth(person.get("birth_year")):
            person.pop("birth_year", None)
    return out


def persons(cards: dict):
    for hid in sorted(cards):
        for person in cards[hid].get("persons") or []:
            if reconstructed(person):
                continue
            yield hid, person


# --- the forename table ----------------------------------------------------------------

# A POOL THAT ADDS NO FORENAME IS NOT NAMED IN A CARD'S PROSE (T-1377). The `free_black`
# pool contributes surnames and, by its own construction and its own note, not one
# forename the other pools do not already carry — so it can only ever appear in this
# attribution ALONGSIDE the pools that already licensed the name. Listing it would
# rewrite the sex sentence of 383 committed cards to read "it stands in the free_black
# and irish and yankee male forename pool", printing a community term onto four hundred
# people it says nothing whatever about. The sex reading does not move: `says` is a set
# and every one of this pool's forenames is already in it.
POOLS_NOT_NAMED_IN_A_SEX_SENTENCE = ("free_black",)


def pool_names() -> tuple:
    """(forename -> [community ids]) for each sex, out of the period pools."""
    male, female = {}, {}
    for community in load(POOLS)["communities"]:
        if community["id"] in POOLS_NOT_NAMED_IN_A_SEX_SENTENCE:
            continue
        for name in community.get("given_male") or []:
            male.setdefault(name.lower(), []).append(community["id"])
        for name in community.get("given_female") or []:
            female.setdefault(name.lower(), []).append(community["id"])
    return male, female


def attested_bearers(cards: dict) -> dict:
    """forename -> sex -> [person ids], out of the people whose sex a source records.

    A BEARER WHOSE NAME CARRIES A GENDERED TITLE TEACHES NOTHING. "Mrs Rufus Brown" is a
    woman because of the Mrs, and counting her forename would teach the table that Rufus
    is a woman's name — which is exactly what it did before this rule: Rufus and Nelson
    were the two names this layer's own evidence appeared to split, and both splits were
    a wife recorded under her husband's name.

    AND A BEARER WHOSE SEX WAS DRAWN TEACHES NOTHING EITHER (T-1304). That stage draws a
    sex for the 587 people this pass refuses, at a rate measured on the rolls, and grades
    it `reconstructed`. Counting those bearers would teach this table a forename off a
    coin toss and then let the table fire it as evidence on the next name — the exact
    circularity `without_this_pass` exists to stop, arriving by the other door. A draw is
    never evidence, here least of all.
    """
    table = {}
    for _hid, person in persons(cards):
        sex = person.get("sex")
        if not sex:
            continue
        # AND A RECONSTRUCTED SEX TEACHES NOTHING EITHER. T-1304 drew a sex from the
        # population model where no evidence could settle one, and T-1314 wrote whole
        # PEOPLE the sources do not name, whose forenames come out of the pools below.
        # Either one counted as a bearer would feed this table's own output back in as
        # though it were evidence about the town, and every stage that adds a person
        # would make it look better attested than the sources ever made it.
        if (person.get("grade") == "reconstructed"
                or (person.get("sex_basis") or {}).get("confidence") == "reconstructed"):
            continue
        title, fore, why = read_name(person.get("name") or "")
        if title or why not in ("forename", "contraction") or not fore:
            continue
        table.setdefault(fore, {}).setdefault(sex, []).append(person["id"])
    return table


def build_table(cards: dict) -> dict:
    pool_male, pool_female = pool_names()
    bearers = attested_bearers(cards)

    entries, refused = {}, {}
    for fore in sorted(set(bearers) | set(pool_male) | set(pool_female)):
        by_sex = bearers.get(fore) or {}
        says = set(by_sex)
        if fore in pool_male:
            says.add("male")
        if fore in pool_female:
            says.add("female")
        row = {
            "forename": fore,
            "attested_bearers": {s: sorted(ids) for s, ids in sorted(by_sex.items())},
            "in_pools": sorted(set((pool_male.get(fore) or []) + (pool_female.get(fore) or []))),
        }
        if fore in AMBIGUOUS:
            refused[fore] = dict(row, why=AMBIGUOUS[fore], refused_by="name")
        elif fore in NOT_A_FORENAME:
            continue
        elif len(says) != 1:
            refused[fore] = dict(row, why=SPLIT_BY_THE_EVIDENCE, refused_by="the evidence")
        else:
            entries[fore] = dict(row, sex=says.pop())

    for fore, why in sorted(AMBIGUOUS.items()):
        refused.setdefault(fore, {"forename": fore, "attested_bearers": {}, "in_pools": [],
                                  "why": why, "refused_by": "name"})

    male = [e for e in entries.values() if e["sex"] == "male"]
    female = [e for e in entries.values() if e["sex"] == "female"]
    return {
        "schema": "forename_sex/1",
        "domain": "residents",
        "generated_by": "tools/spend_person_sex_age.py",
        "_doc": (
            "T-1303. Which forenames this project has evidence enough to read a sex from, "
            "and which it refuses. DERIVED — rebuild with `python3 "
            "tools/spend_person_sex_age.py` and `--check` refuses a hand-edit. A name is "
            "here on one of two kinds of evidence and usually both: a person in "
            "data/residents/ whose sex a SOURCE records bears it, or it stands in one of "
            "the period forename pools of data/reconstruction/1835_invented_name_pools.json, "
            "which were assembled out of this town's own attested naming. A name the two "
            "disagree about is refused, and so are the four named below."),
        "what_this_is_not": (
            "Not a general table of nineteenth-century forenames. It says nothing about "
            "names this project holds no evidence about, and a person bearing one keeps "
            "no sex from this pass. Nor is it evidence about any individual: it licenses "
            "an INFERENCE, graded `inferred` on the card with the table named in the note."),
        "the_bearer_rule": attested_bearers.__doc__.strip().splitlines()[0]
        + " A bearer whose name carries a gendered title teaches nothing, because the "
          "title and not the forename is what sexes them.",
        "counts": {
            "male": len(male), "female": len(female), "refused": len(refused),
            "from_a_bearer_in_this_layer": sum(1 for e in entries.values()
                                               if e["attested_bearers"]),
            "from_a_pool_only": sum(1 for e in entries.values() if not e["attested_bearers"]),
            "contractions": len(CONTRACTIONS),
            "not_a_forename": len(NOT_A_FORENAME),
            "collective": len(COLLECTIVE),
        },
        "male": sorted(male, key=lambda e: e["forename"]),
        "female": sorted(female, key=lambda e: e["forename"]),
        "refused": [refused[f] for f in sorted(refused)],
        "contractions": [{"forename": f, "expands_to": CONTRACTIONS[f], "sex": "male",
                          "why": "every expansion of this contraction attested in this "
                                 "project is a man's name, so the contraction settles the "
                                 "sex without settling which name was contracted"}
                         for f in sorted(CONTRACTIONS)],
        "not_a_forename": [{"token": t, "why": NOT_A_FORENAME[t]}
                           for t in sorted(NOT_A_FORENAME)],
        "a_group_not_a_person": [{"token": t, "why": COLLECTIVE[t]}
                                 for t in sorted(COLLECTIVE)],
    }


def table_lookup(table: dict) -> dict:
    """forename -> sex, for the names the table lets fire."""
    out = {e["forename"]: e["sex"] for e in table["male"] + table["female"]}
    for row in table["refused"]:
        out.pop(row["forename"], None)
    for row in table["contractions"]:
        out.setdefault(row["forename"], row["sex"])
    return out


# --- rule 1 and 2: what a person's sex reads as -----------------------------------------

def sex_for(person: dict, table: dict, lookup: dict) -> tuple:
    """(sex, rule, note) or (None, why_not, None)."""
    if person.get("sex"):
        return None, "already_recorded", None
    name = person.get("name") or ""
    title, fore, why = read_name(name)
    if title:
        token = next(t for t in tokens(name) if t in GENDERED_TITLES)
        return title, "title", (
            "THE NAME IS PRINTED WITH A TITLE. Whoever wrote '%s' down said in the same "
            "breath that this person was %s, and a title is a statement about the person "
            "rather than a reading of their name. A RANK IS NOT READ THE SAME WAY here: "
            "Capt., Col., Rev. and Maj. would be right nearly every time in this town and "
            "would still be a guess about the period rather than a fact about the person, "
            "so none of them sexes anybody." % (token.capitalize(), title))
    if why == "initial":
        return None, "initial_only", None
    if fore is None:
        return None, "no_forename", None
    if fore in AMBIGUOUS:
        return None, "ambiguous_forename", None
    if fore in lookup and why == "contraction":
        return "male", "contraction", (
            "'%s.' IS THE PERIOD CONTRACTION OF %s, and every expansion of it attested in "
            "this project is a man's name — so the contraction settles the sex without "
            "settling which name was contracted. The table is "
            "data/research/residents/forename_sex.json."
            % (fore.capitalize(), CONTRACTIONS[fore]))
    if fore not in lookup:
        return None, "forename_not_in_table", None

    entry = next(e for e in table["male"] + table["female"] if e["forename"] == fore)
    bearers = entry["attested_bearers"].get(lookup[fore]) or []
    evidence = []
    if bearers:
        evidence.append("%d person%s in this layer whose sex a source records bear%s it (%s)"
                        % (len(bearers), "" if len(bearers) == 1 else "s",
                           "s" if len(bearers) == 1 else "", ", ".join(bearers[:6])
                           + (", and others" if len(bearers) > 6 else "")))
    if entry["in_pools"]:
        evidence.append("it stands in the %s %s forename pool of this town's own attested "
                        "naming" % (" and ".join(entry["in_pools"]), lookup[fore]))
    return lookup[fore], "forename", (
        "A FORENAME THAT STANDS IN ONE SEX'S NAMING ONLY. '%s' is read as %s because %s. "
        "Nothing about this person is recorded; the name is the whole of the reasoning, "
        "and the table that licenses it — data/research/residents/forename_sex.json — "
        "refuses a name its own evidence splits, refuses Jean, Marion, Leslie and "
        "Francis by name, and refuses an initial outright."
        % (fore.capitalize(), lookup[fore], ", and ".join(evidence)))


# --- rule 3 and 4: what a person's birth year reads as ----------------------------------

def spells_a_forename(given) -> bool:
    """True when a printed given name spells a forename out rather than initialling it."""
    for token in str(given or "").split():
        if "." not in token and len(token) >= 3 and token.replace("-", "").isalpha():
            return True
    return False


def list_year(name: str):
    """The year a civic list is OF, read off its own name. None where it does not say."""
    match = re.search(r"(18\d\d)\b", str(name or ""))
    return int(match.group(1)) if match else None


def age_floors(person: dict) -> list:
    """Every floor the card's OWN evidence puts under this person's age, with its reason.

    Each row is `(year, floor, why)`: at `year` this person was at least `floor` years
    old, because of `why`. Nothing here asserts a birth year — see the note beside
    REFUSAL_FLOOR — and nothing here reads a value this pass or any other one drew.
    """
    out = []
    for entry in person.get("civic_evidence") or []:
        name = str(entry.get("list") or "")
        year = list_year(name)
        if year and name.startswith(CIVIC_LIST_PREFIXES):
            out.append((year, FRANCHISE_FLOOR, "stands on %s" % name))
    for key in OWN_RIGHT_KEYS:
        if person.get(key):
            out.append((int(SCENE_DATE[:4]), REFUSAL_FLOOR,
                        "is named in their own right in the %s on this card"
                        % key.replace("_", " ")))
    for role in person.get("roles") or []:
        if not role.get("covers_scene_date"):
            continue
        out.append((int(SCENE_DATE[:4]), REFUSAL_FLOOR,
                    "holds the role %s over the scene date"
                    % (role.get("role") or role.get("as_printed") or "this card records")))
    return sorted(out)


def against_the_card(person: dict, row: dict) -> tuple:
    """`(refusal, contradiction)` — what the card's own evidence says about this interval.

    Both are taken at the interval's OLDEST reading, `earliest`, the year that makes the
    person as old as the arithmetic allows: a verdict here is about the whole interval and
    not merely about its unlucky end.
    """
    refusal = contradiction = None
    for year, floor, why in age_floors(person):
        age = year - row["earliest"]
        said = ("this card says the person %s, and the interval leaves them %d in %d"
                % (why, age, year))
        if age < REFUSAL_FLOOR and refusal is None:
            refusal = ("%s — under the 15 the 1840 schedule's own reading of a roll "
                       "requires, which is the floor this project holds without a liberty"
                       % said)
        elif age < floor and contradiction is None:
            contradiction = ("%s — under the %d a poll, tax or muster list is drawn at. "
                             "That floor is the franchise's line and no source states it, "
                             "so it is set beside this interval and not used to strike it "
                             "out." % (said, floor))
    return refusal, contradiction


def refusal_block(source: str, row: dict, why: str) -> dict:
    """The `birth_year` block a refused interval leaves: one that asserts NO year.

    It is the same key and the same shape as a spent interval on purpose. A refusal that
    invented a key of its own would sort differently on the card, render through nothing
    the rest of the layer already has, and — measured the hard way on T-1179 — oscillate
    against the draw stage that writes an age band into the same person. `value: null`
    under `confidence: "reconstructed"` is this layer's own idiom for a block that asserts
    nothing (T-1158), and it is what makes the card print the `not recorded` chip rather
    than the hatched one that would say this project made a birth year up.
    """
    return {
        "value": None,
        "precision": None,
        "confidence": "reconstructed",
        "sources": [DEATHS_SOURCE if source == "death_notice" else REGISTRY_SOURCE],
        "refused_interval": [row["earliest"], row["latest"]],
        "refused_because": why,
        "record_id": row.get("record_id"),
        "as_read": row.get("as_read"),
        "note": (
            "A BIRTH INTERVAL THIS CARD REFUTES, AND SO NO BIRTH YEAR AT ALL (T-1179). An "
            "obituary matched to this name puts the birth in %s, and that interval is NOT "
            "carried, because %s. The match itself is the crosswalk's and is untouched — "
            "what is refused is spending its arithmetic into an age. The two readings "
            "cannot both stand, and the weaker one is the name match: the obituary list's "
            "own header admits it names citizens who arrived after 1843 and others merely "
            "prominently connected with Illinois history, while the evidence on this side "
            "is this person's own. The floor the refusal is taken at is the one "
            "data/reconstruction/1835_sex_age_model.json defends without a liberty — a "
            "roll naming a person in their own right names somebody 15 or over — so this "
            "pass refuses nothing that pass would have drawn. NOTHING IS ASSERTED IN ITS "
            "PLACE: the person's age band is drawn for them like anybody else's, and a "
            "source that states a birth retires this refusal."
            % ("%d" % row["earliest"] if row["earliest"] == row["latest"]
               else "%d or %d" % (row["earliest"], row["latest"]), why)),
    }


def contradiction_note(why: str) -> str:
    return (
        "AND THE CARD DOES NOT AGREE WITH IT (T-1179). %s The interval is carried anyway, "
        "because the floor it misses is one this project invented and says so — the model "
        "carries it under the liberty L-rc-age-conditioning — and a floor nobody can cite "
        "may not strike out a reading. Both are printed so that a reader meets the "
        "disagreement rather than one side of it." % (why[0].upper() + why[1:]))


def death_notice_births(cards: dict) -> dict:
    """person id -> the death-notice interval this pass may spend, and why."""
    out = {}
    for hid in sorted(cards):
        for entry in (cards[hid].get("old_settler_deaths") or {}).get("people") or []:
            if not entry.get("birth_year_earliest"):
                continue
            out[entry["person_id"]] = {
                "household_id": hid,
                "earliest": entry["birth_year_earliest"],
                "latest": entry["birth_year_latest"],
                "arithmetic": entry.get("birth_year_arithmetic"),
                "as_read": entry.get("as_read"),
                "record_id": entry.get("record_id"),
                "thin": bool(entry.get("matched_on_initial_only")),
            }
    return out


def registry_births() -> dict:
    """person id -> the age a merged old settler gave at the Calumet Club, and its interval."""
    out = {}
    for row in load(OLD_SETTLERS)["people"]:
        layer = row.get("residents_layer") or {}
        age = row.get("age_1879_as_read")
        if layer.get("outcome") != "merged" or not layer.get("person_id") or not age:
            continue
        if row.get("roll") != REGISTRY_ROLL:
            continue
        years = int(str(age).strip())
        out[layer["person_id"]] = {
            "household_id": layer.get("household_id"),
            "age": years,
            # Registered on 27 May 1879 aged N completed years: the birth falls after
            # 27 May of 1879-(N+1) and on or before 27 May of 1879-N.
            "earliest": 1879 - years - 1,
            "latest": 1879 - years,
            "as_read": row.get("as_read"),
            "record_id": row.get("id"),
            "rule": layer.get("rule"),
        }
    return out


def interval(row: dict) -> dict:
    """`precision` and `band`, from how wide the arithmetic left the birth year.

    An age printed to the half-year or to the day narrows the birth to ONE year; an age
    in completed years leaves TWO, and the band names both rather than picking one.
    """
    if row["earliest"] == row["latest"]:
        return {"precision": "year"}
    return {"precision": "band", "band": [row["earliest"], row["latest"]]}


def birth_block(source: str, row: dict) -> dict:
    if source == "death_notice":
        note = (
            "A BIRTH INTERVAL OUT OF A DEATH NOTICE, NOT A RECORD OF A BIRTH. %s "
            "Fergus's 1843 directory (1896) prints the entry \"%s\", and its header admits "
            "the list also names citizens who arrived after 1843 and others merely "
            "prominently connected with Illinois history — so a match here is never "
            "evidence of residence in 1835 and never moves a grade. The match to this "
            "person was adjudicated in "
            "data/research/old_settlers/death_notices_crosswalk_1835.json and written onto "
            "this card by tools/spend_old_settlers.py; this pass only spends its arithmetic "
            "into a birth year. Both sides of the match spell a forename out — the "
            "crosswalk's thin matches, where a single initial is the whole of the "
            "discriminator, are refused rather than spent."
            % (row["arithmetic"], row["as_read"]))
        block = {"value": row["earliest"]}
        block.update(interval(row))
        block.update({"confidence": "inferred", "sources": [DEATHS_SOURCE], "note": note})
        return block
    note = (
        "A BIRTH INTERVAL OUT OF A MAN'S OWN STATEMENT OF HIS AGE. He registered at the "
        "Calumet Club's reception to the settlers of Chicago on %s and gave his age as "
        "%d: \"%s\". An age of %d completed years given on that day means the birth falls "
        "after 27 May %d and on or before 27 May %d, so the birth year is %d or %d. The "
        "subtraction is this project's; the page states no year of birth. IT IS A "
        "RECOLLECTION, forty-four years after the scene date — better than a recollection "
        "about somebody else, and still not a record. The merge onto this person is the "
        "old-settler crosswalk's own (%s), in data/research/old_settlers/people.json."
        % (REGISTRY_DAY, row["age"], row["as_read"], row["age"],
           row["earliest"], row["latest"], row["earliest"], row["latest"],
           row.get("rule") or "OS1"))
    block = {"value": row["earliest"]}
    block.update(interval(row))
    block.update({"confidence": "inferred", "sources": [REGISTRY_SOURCE], "note": note})
    return block


# --- applying ---------------------------------------------------------------------------

def apply_to(card: dict, table: dict, lookup: dict, deaths: dict, registry: dict) -> dict:
    """A fresh copy of one household with this pass's fills written in. Pure."""
    out = json.loads(json.dumps(card))
    for person in out.get("persons") or []:
        if reconstructed(person):
            continue
        pid = person.get("id")
        sex, rule, note = sex_for(person, table, lookup)
        if sex:
            person["sex"] = sex
            person["sex_basis"] = {"value": sex, "confidence": "inferred", "note": note}
        if not person.get("birth_year"):
            # Rule 4 before rule 3: a man's own age about himself outranks an obituary
            # matched to him by name. Where both stand, the note of the one written says
            # nothing about the other — the two are separate readings and the card keeps
            # the stronger.
            source, row = None, None
            if pid in registry:
                source, row = "registry", registry[pid]
            elif pid in deaths and not deaths[pid]["thin"]:
                source, row = "death_notice", deaths[pid]
            if row:
                refusal, contradiction = against_the_card(person, row)
                if refusal and source == "death_notice":
                    person["birth_year"] = refusal_block(source, row, refusal)
                else:
                    block = birth_block(source, row)
                    # A refusal that could not be taken — rule 4's own recollection — is
                    # still a disagreement, and is carried as one rather than dropped.
                    said = contradiction or refusal
                    if said:
                        # ONE HOME FOR THE SENTENCE. It is not folded into `note`: the
                        # card renders this field as a line of its own under the Born
                        # row, and a disagreement a reader only meets by opening a
                        # paragraph is one the card has not really said.
                        block["contradicted_by_the_card"] = contradiction_note(said)
                    person["birth_year"] = block
    return out


def rebuilt(cards: dict) -> tuple:
    """(table, the fresh cards, the intervals) — derived from the layer WITHOUT this pass."""
    base = {hid: without_this_pass(card) for hid, card in cards.items()}
    table = build_table(base)
    lookup = table_lookup(table)
    deaths, registry = death_notice_births(base), registry_births()
    fresh = {hid: apply_to(base[hid], table, lookup, deaths, registry) for hid in base}
    return table, fresh, deaths, registry, base


def tally(cards: dict, fresh: dict, table: dict, lookup: dict,
          deaths: dict, registry: dict) -> dict:
    sex_rules, refusals = {}, {}
    for _hid, person in persons(cards):
        _sex, rule, _note = sex_for(person, table, lookup)
        if _sex:
            sex_rules[rule] = sex_rules.get(rule, 0) + 1
        else:
            refusals[rule] = refusals.get(rule, 0) + 1
    # THIS PASS'S OWN BEFORE AND AFTER, which is the READ tier and not the layer's total.
    # T-1304 draws a sex for the people refused below and grades it `reconstructed`; those
    # draws are counted in data/reconstruction/1835_sex_age_model.json, and counting them
    # here would turn this ledger's headline — 99 -> 689 people whose sex the evidence
    # settles — into a number about a different pass's work.
    drawn = lambda p: (p.get("sex_basis") or {}).get("confidence") == "reconstructed"
    with_sex = sum(1 for _h, p in persons(fresh) if p.get("sex") and not drawn(p))
    # A REFUSAL IS NOT A BIRTH YEAR. It lives in the same key and asserts nothing, so a
    # count of `birth_year` blocks would read three people into the headline who are
    # exactly the three this pass declined to date.
    carried = lambda p: (p.get("birth_year") or {}).get("value") is not None
    with_birth = sum(1 for _h, p in persons(fresh) if carried(p))
    total = sum(1 for _ in persons(cards))
    return {
        "persons": total,
        "sex_before": sum(1 for _h, p in persons(cards) if p.get("sex") and not drawn(p)),
        "sex_after": with_sex,
        "birth_year_before": sum(1 for _h, p in persons(cards) if carried(p)),
        "birth_year_after": with_birth,
        "sex_written_by_rule": dict(sorted(sex_rules.items())),
        "sex_not_written_by_reason": dict(sorted(refusals.items())),
        "birth_year_from_the_calumet_registry": sum(
            1 for _h, p in persons(fresh)
            if carried(p) and (p.get("birth_year") or {}).get("sources") == [REGISTRY_SOURCE]),
        "birth_year_from_a_death_notice": sum(
            1 for _h, p in persons(fresh)
            if carried(p) and (p.get("birth_year") or {}).get("sources") == [DEATHS_SOURCE]),
        "death_notice_intervals_refused_as_thin": sum(1 for r in deaths.values() if r["thin"]),
        # T-1179. A match the CARD refutes, counted apart from a match that is merely
        # thin: the first is a disagreement between two readings of one person and the
        # second is a weak identification. A reader who conflates them learns nothing
        # about either.
        "intervals_refused_because_the_card_refutes_them": sum(
            1 for _h, p in persons(fresh)
            if (p.get("birth_year") or {}).get("refused_because")),
        "refused_because_the_card_refutes_them": sorted(
            p["id"] for _h, p in persons(fresh)
            if (p.get("birth_year") or {}).get("refused_because")),
        "intervals_carried_with_the_card_contradicting_them": sum(
            1 for _h, p in persons(fresh)
            if (p.get("birth_year") or {}).get("contradicted_by_the_card")),
        "carried_with_the_card_contradicting_them": sorted(
            p["id"] for _h, p in persons(fresh)
            if (p.get("birth_year") or {}).get("contradicted_by_the_card")),
        "still_without_a_sex": total - with_sex,
        "still_without_a_birth_year": total - with_birth,
    }


def ledger(counts: dict, table: dict) -> dict:
    return {
        "schema": "sex_age_spend/1",
        "domain": "residents",
        "generated_by": "tools/spend_person_sex_age.py",
        "_doc": (
            "T-1303. What the first two tiers of the profile could reach, counted before "
            "and after. DERIVED — `--check` refuses a hand-edit. The remainder is T-1304's: "
            "the population model's sex and age band, seeded by person id, for everybody "
            "the evidence here is silent about."),
        "scene_date": SCENE_DATE,
        "counts": counts,
        "the_table": {"male": table["counts"]["male"], "female": table["counts"]["female"],
                      "refused": table["counts"]["refused"]},
        "what_is_left_for_the_model": (
            "%d people without a sex and %d without a birth year. The %d known only as an "
            "initial are the letter lists' cohort and the ticket asks for them to be sexed "
            "at the model's measured adult-male rate; the rest bear a forename this "
            "project has no evidence about. Neither is this pass's to decide."
            % (counts["still_without_a_sex"], counts["still_without_a_birth_year"],
               counts["sex_not_written_by_reason"].get("initial_only", 0))),
    }


# --- commands ---------------------------------------------------------------------------

def without_this_pass_all(cards: dict) -> dict:
    return {hid: without_this_pass(card) for hid, card in cards.items()}


def build(quiet: bool = False) -> int:
    cards = households()
    table, fresh, deaths, registry, base = rebuilt(cards)
    counts = tally(base, fresh, table, table_lookup(table), deaths, registry)
    TABLE.write_text(dumps(table), encoding="utf-8")
    LEDGER.write_text(dumps(ledger(counts, table)), encoding="utf-8")
    changed = 0
    for hid, card in fresh.items():
        text = dumps(card)
        path = HOUSEHOLDS / ("%s.json" % hid)
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            changed += 1
    if not quiet:
        print("sex and age: %d card(s) rewritten; sex %d -> %d, birth year %d -> %d"
              % (changed, counts["sex_before"], counts["sex_after"],
                 counts["birth_year_before"], counts["birth_year_after"]))
    return 0


def check(quiet: bool = False) -> int:
    cards = households()
    table, fresh, deaths, registry, base = rebuilt(cards)
    counts = tally(base, fresh, table, table_lookup(table), deaths, registry)
    bad = []
    if TABLE.read_text(encoding="utf-8") != dumps(table):
        bad.append("data/research/residents/forename_sex.json does not re-derive")
    if LEDGER.read_text(encoding="utf-8") != dumps(ledger(counts, table)):
        bad.append("data/research/residents/sex_age_spend.json does not re-derive")
    for hid, card in fresh.items():
        if dumps(cards[hid]) != dumps(card):
            bad.append("%s: the committed card is not what this pass derives" % hid)
    if bad:
        print("sex and age: %d drift(s)" % len(bad))
        for line in bad[:20]:
            print("   %s" % line)
        if len(bad) > 20:
            print("   …and %d more" % (len(bad) - 20))
        return 1
    if not quiet:
        print("sex and age: %d of %d people carry a sex, %d a birth year; the forename "
              "table re-derives and %d name(s) stay refused"
              % (counts["sex_after"], counts["persons"], counts["birth_year_after"],
                 table["counts"]["refused"]))
    return 0


def report() -> int:
    cards = households()
    table, fresh, deaths, registry, base = rebuilt(cards)
    counts = tally(base, fresh, table, table_lookup(table), deaths, registry)
    print("SEX — what fired")
    for rule, n in counts["sex_written_by_rule"].items():
        print("   %-24s %4d" % (rule, n))
    print("SEX — what did not")
    for rule, n in counts["sex_not_written_by_reason"].items():
        print("   %-24s %4d" % (rule, n))
    print("BIRTH YEAR")
    print("   %-24s %4d" % ("calumet registry", counts["birth_year_from_the_calumet_registry"]))
    print("   %-24s %4d" % ("death notice", counts["birth_year_from_a_death_notice"]))
    print("   %-24s %4d" % ("refused as thin", counts["death_notice_intervals_refused_as_thin"]))
    print("-" * 46)
    print("   sex        %4d -> %4d of %d" % (counts["sex_before"], counts["sex_after"],
                                              counts["persons"]))
    print("   birth year %4d -> %4d of %d" % (counts["birth_year_before"],
                                              counts["birth_year_after"], counts["persons"]))
    return 0


def self_test() -> int:
    failures = []

    def want(label, cond):
        if not cond:
            failures.append(label)

    cards = without_this_pass_all(households())
    table, fresh, deaths, registry, _base = rebuilt(cards)
    lookup = table_lookup(table)

    # The ticket's own four: an initial and the three named ambiguities fire nothing.
    for name in ("J. W. Smith", "E. F. Adams", "A. Abbot"):
        want("an initial fires nothing (%s)" % name,
             sex_for({"name": name}, table, lookup)[0] is None)
    for fore in ("marion", "jean", "leslie", "francis", "frances"):
        want("%s fires nothing" % fore, fore not in lookup)
        want("%s fires nothing through a person" % fore,
             sex_for({"name": "%s Smith" % fore.capitalize()}, table, lookup)[0] is None)
        want("%s is refused in the table with a reason" % fore,
             any(r["forename"] == fore and r["why"] for r in table["refused"]))

    # A rank is not a title, and it is not a forename either.
    want("a rank sexes nobody", sex_for({"name": "Capt. Baxley"}, table, lookup)[0] is None)
    want("a rank is read past to the forename behind it",
         read_name("Lieut. James Allen")[1] == "james")
    want("a collective description names nobody",
         read_name("The four Temple children")[1] is None
         and read_name("The rest of the Beaubien household, unnamed")[1] is None
         and sex_for({"name": "The four Temple children"}, table, lookup)[0] is None)
    # T-1395: a group is a group WORD, not a leading article.
    want("a leading article is not a group on its own",
         read_name("The Harmon daughter later known as Mrs A. G. Burley")[2] != \
         "a_group_not_a_person")
    want("the article gone, a title behind it still fires",
         read_name("The Widow Wells")[0] == "female")
    want("every genuine collective row still names nobody",
         all(read_name(n)[2] == "a_group_not_a_person" for n in (
             "The rest of the Beaubien household, unnamed",
             "Mark Beaubien's family, unnamed",
             "Heacock's wife and children, unnamed",
             "Owen's household, unnamed",
             "The rest of the Robinson household, unnamed",
             "The four Temple children")))
    want("a title anywhere in the name fires",
         read_name("Nelson mary Miss")[0] == "female"
         and read_name("Mrs Rufus Brown")[0] == "female")

    # The bearer rule: a wife under her husband's name teaches the table nothing.
    want("Rufus is not taught by Mrs Rufus Brown", lookup.get("rufus") == "male")
    want("Nelson is not split by a trailing Miss", lookup.get("nelson") == "male")
    bearers = attested_bearers(cards)
    want("no bearer with a gendered title reached the table",
         all(not read_name(p.get("name") or "")[0]
             for _h, p in persons(cards)
             if p.get("sex") and read_name(p.get("name") or "")[1] in bearers))

    # Every fired name has evidence, and no fired name is in two places at once.
    want("every table name carries evidence",
         all(e["attested_bearers"] or e["in_pools"] for e in table["male"] + table["female"]))
    want("no name is both male and female",
         not ({e["forename"] for e in table["male"]} & {e["forename"] for e in table["female"]}))
    want("a refused name never fires",
         not ({r["forename"] for r in table["refused"]} & set(lookup)))

    # T-1179. THE CARD'S OWN EVIDENCE AGAINST THE INTERVAL, proved by breaking it: the
    # two floors do different things, and a fixture that only exercised the refusal would
    # not notice the day somebody promotes the franchise line into one.
    interval = {"earliest": 1831, "latest": 1831, "arithmetic": "a.", "as_read": "x",
                "record_id": "fdn0001", "thin": False}
    keeper = {"id": "t", "name": "Test Person",
              "roles": [{"role": "coffee_house_keeper", "covers_scene_date": True}]}
    voter = {"id": "t", "name": "Test Person",
             "civic_evidence": [{"list": "poll_1835"}]}
    infant = {"id": "t", "name": "Test Person",
              "church_evidence": [{"locator": "infant"}]}
    refusal, contra = against_the_card(keeper, interval)
    want("a trade over the scene date refuses a birth year that makes it a child of four",
         refusal and "coffee_house_keeper" in refusal and contra is None)
    refusal, contra = against_the_card(voter, {**interval, "earliest": 1820, "latest": 1820})
    want("a poll list is a CONTRADICTION and never a refusal at 15",
         refusal is None and contra and "not used to strike it out" in contra)
    refusal, _ = against_the_card(voter, {**interval, "earliest": 1825, "latest": 1825})
    want("a poll list still refuses a child of ten", refusal and "in 1835" in refusal)
    refusal, contra = against_the_card(infant, interval)
    want("a baptismal entry is never read as an adult status",
         refusal is None and contra is None)
    want("an interval is judged at its oldest reading",
         against_the_card(voter, {"earliest": 1815, "latest": 1816})[0] is None)
    want("a refusal asserts no year and says why",
         refusal_block("death_notice", interval, "because")["value"] is None
         and refusal_block("death_notice", interval, "because")["refused_because"])
    want("a man's own age about himself is never refused",
         not any((p.get("birth_year") or {}).get("refused_because")
                 for _h, p in persons(fresh)
                 if (p.get("birth_year") or {}).get("sources") == [REGISTRY_SOURCE]))
    want("the three the layer refuses today are on the card and in the ledger",
         sorted(p["id"] for _h, p in persons(fresh)
                if (p.get("birth_year") or {}).get("refused_because"))
         == ["harrison_caleb", "smith_george", "wright_amasa"])

    # Rule: this pass only ever fills an absence, and writes exactly two person keys.
    before_keys, after_keys = set(), set()
    for hid in cards:
        for old, new in zip(cards[hid].get("persons") or [], fresh[hid].get("persons") or []):
            before_keys |= set(old)
            after_keys |= set(new)
            if old.get("sex"):
                # A sex already on the card is either a mint's (no reason block) or a
                # draw of T-1304's (graded `reconstructed`). Neither is this pass's, and
                # what is asserted here is that this pass leaves both alone.
                want("a recorded sex is never changed (%s)" % old["id"],
                     new.get("sex") == old["sex"]
                     and (new.get("sex_basis") or {}).get("confidence") != "inferred")
            if old.get("birth_year"):
                want("a recorded birth year is never changed (%s)" % old["id"],
                     new["birth_year"] == old["birth_year"])
    want("this pass adds exactly `sex`, `sex_basis` and `birth_year`",
         after_keys - before_keys <= {"sex_basis"} and not before_keys - after_keys)
    want("no household key is added",
         all(set(fresh[hid]) == set(cards[hid]) for hid in cards))
    want("no grade moves",
         all([p.get("grade") for p in fresh[hid].get("persons") or []]
             == [p.get("grade") for p in cards[hid].get("persons") or []] for hid in cards))

    # Every written value is inferred, owes its reasoning, and cites a resolving source
    # only where one exists.
    for _hid, person in persons(fresh):
        basis = person.get("sex_basis")
        # T-1304's drawn blocks travel through this pass untouched and are graded
        # `reconstructed`; the assertions below are about the sexes this pass READS.
        if basis and basis.get("confidence") != "reconstructed":
            want("a written sex is inferred with a note (%s)" % person["id"],
                 basis["confidence"] == "inferred" and basis["note"].strip()
                 and basis["value"] == person["sex"])
        born = person.get("birth_year")
        if born and born.get("sources") in ([DEATHS_SOURCE], [REGISTRY_SOURCE]):
            # T-1179: a refusal lives in this key and asserts nothing, so the arithmetic
            # assertion is about the blocks that CARRY a year. The refusals have their own
            # assertion under it — narrowing one without adding the other is how a rule
            # stops being held.
            if born.get("refused_because"):
                want("a refused birth year asserts no year and says why (%s)"
                     % person["id"],
                     born["value"] is None and born["precision"] is None
                     and born["confidence"] == "reconstructed"
                     and born["note"].strip() and born["refused_because"].strip()
                     and len(born["refused_interval"]) == 2)
            else:
                want("a written birth year states how wide its arithmetic left it (%s)"
                     % person["id"],
                     born["confidence"] == "inferred" and born["note"].strip()
                     and ((born["precision"] == "band"
                           and born["band"] == [born["value"], born["value"] + 1])
                          or (born["precision"] == "year" and "band" not in born)))

    # Rule 3's refusal is real and is counted.
    thin = [pid for pid, r in deaths.items() if r["thin"]]
    want("a thin death-notice match is refused", bool(thin))
    want("no thin match reached a card",
         all(not any(p["id"] == pid and (p.get("birth_year") or {}).get("sources")
                     == [DEATHS_SOURCE] for p in fresh[deaths[pid]["household_id"]]["persons"])
             for pid in thin))

    # THE STRIPPING RULE IS ONLY SAFE WHILE IT IS TRUE. Nothing but this pass may write a
    # person `birth_year` citing either roll, and nothing but this pass may write a
    # `sex_basis` — the moment either stops holding, `--check` would strip somebody else's
    # work and re-derive a card that was never wrong.
    committed = households()
    for _hid, person in persons(committed):
        born = person.get("birth_year")
        if ours_birth(born):
            want("only this pass cites a roll for a birth year (%s)" % person["id"],
                 born.get("precision") in ("year", "band")
                 or (born.get("precision") is None and born.get("refused_because")))
    want("a biographied birth year is never mistaken for this pass's",
         all(not ours_birth(p.get("birth_year"))
             for _h, p in persons(without_this_pass_all(committed))))

    # The registry arithmetic, held against a worked example off the page.
    want("the registry arithmetic is right",
         registry.get("adams_william_h", {}).get("earliest") == 1814
         and registry["adams_william_h"]["latest"] == 1815)

    # The gate can fail: a card that loses a fill is caught.
    broken = json.loads(json.dumps(cards))
    victim = next(p for _h, p in persons(fresh) if p.get("sex_basis"))
    for hid in broken:
        for person in broken[hid].get("persons") or []:
            if person["id"] == victim["id"]:
                person["sex"] = "female" if victim["sex"] == "male" else "male"
    want("a card that disagrees with the derivation is caught",
         dumps(apply_to(broken[hid], table, lookup, deaths, registry)) != dumps(fresh[hid])
         or any(dumps(apply_to(broken[h], table, lookup, deaths, registry)) != dumps(fresh[h])
                for h in broken))

    for line in failures:
        print("   FAIL %s" % line)
    print("spend_person_sex_age self-test: %d assertion(s) failed" % len(failures))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    if args.check:
        return check(quiet=args.quiet)
    return build(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
