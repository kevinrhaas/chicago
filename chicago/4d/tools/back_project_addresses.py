#!/usr/bin/env python3
"""Position an 1835 business from an address printed after 1835 — T-0633.

THE FOURTH GRAMMAR. `docs/STREET-FACE-ADOPTION.md` (L212), `docs/CORNER-ORDINAL.md`
(L215) and `docs/LOT-ADDRESS.md` (L216) each answer a way a Chicago paper of 1834-5
places a building: a street is a FACE, a count of doors off a corner is a POSITION
ALONG a face, a lot-and-block is the PLAT'S OWN UNIT. All three read a source written
inside the target year. This tool answers a fourth, and the whole of its difficulty is
that the source is written AFTER it: T-0632 wrote 87 addresses onto the people of 1835
out of Fergus's directories of 1839 and 1843 and Norris's of 1844, and an address
printed four, eight or nine years later is not an address in 1835. `docs/ADDRESS-BACK-
PROJECTION.md` is the policy and **L218** is the liberty; this file is the only thing
that writes a back-projected position, and it writes nothing the policy does not allow.

WHAT IT ADJUDICATES. Every `directories.people[].address_later` on
`data/residents/households/*.json` — all of them, so that a refusal is RECORDED rather
than dropped. Each gets exactly one outcome:

  placed                 the four clauses hold; a face, or a corner where the cross
                         street is 1835's too, graded `reconstructed`
  already_better_placed  the household already carries a real `works_at`; clause 2
                         says an 1835 placement always wins, and this pass stands off
  refused                a clause fails, and the clause that failed is named

THE FOUR CLAUSES, and the record says which one decided it:

  1. The 1835 record has to attest a business to position. A person the 1835 corpus
     gives no trade has no business for a later door to place, and minting one out of
     an 1844 directory is the one thing the ticket forbids outright.
  2. Nothing better places it. A real `works_at` wins; so does a residence address,
     which is not this pass's claim at all and is left to T-0669.
  3. The address has to resolve onto the 1835 street grid — the street existed under
     that name, in that place, on the scene date. `data/streets/1835.json` is that
     record and this tool holds to it: `North Dearborn street` is a north-side street
     the 1835 layer does not carry under that name, `Michigan ave` is not `Michigan
     Street`, and a qualifier reading `cor. Monroe` places a shop three blocks south
     of the platted town. Each is refused, by name.
  4. The placement is graded `reconstructed` at best, and its note says in plain words
     that it is a later address read backwards and by how many years.

WHAT IT DOES NOT DO. It deals no roof. `docs/STREET-FACE-ADOPTION.md` limit 3 says the
allocation of a business to one roof on a face "is an allocation, not a reading", and
stacking that allocation on top of an address already read back four to nine years
would produce a building attachment a reader would badly over-read. So the unit here is
the FACE — the same unit the owner's ruling of 2026-08-29 says a street name constrains
— and `lives_at` and `works_at` are not touched by this pass at all.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
STREETS = DATA / "streets" / "1835.json"
LEDGER = DATA / "research" / "directories" / "address_back_projection.json"

SCENE_YEAR = 1835

# The volumes T-0632 read, the year each describes, and the name a card calls it.
VOLUME_YEAR = {
    "fergus_chicago_directory_1839": 1839,
    "fergus_chicago_directory_1843": 1843,
    "norris_directory_1844": 1844,
}
VOLUME_TITLE = {
    "fergus_chicago_directory_1839": "Fergus's Chicago directory of 1839",
    "fergus_chicago_directory_1843": "Fergus's Chicago directory of 1843",
    "norris_directory_1844": "Norris's Chicago directory of 1844",
}

# ---------------------------------------------------------------------------
# The street table. Authored, not derived, and deliberately in two halves: a
# name this pass accepts and a name it refuses are both statements about 1835,
# and a table with only the first half would refuse by silence.
# ---------------------------------------------------------------------------

# Printed form (folded) -> the street id in data/streets/1835.json.
STREET_1835 = {
    "south water": "south_water", "so water": "south_water", "s water": "south_water",
    "lake": "lake",
    "randolph": "randolph", "west randolph": "randolph", "w randolph": "randolph",
    "washington": "washington",
    "market": "market",
    "franklin": "franklin",
    "wells": "wells",
    "lasalle": "lasalle", "la salle": "lasalle",
    "clark": "clark", "clarke": "clark",
    "dearborn": "dearborn", "dearb": "dearborn",
    "state": "state",
    "canal": "canal", "north canal": "canal", "n canal": "canal",
    "clinton": "clinton",
    "kinzie": "kinzie",
    "north water": "north_water", "n water": "north_water",
    "wolcott": "wolcott",
    "michigan street": "michigan_north",
}

# Printed form (folded) -> why 1835 does not hold it. Clause 3's refusals, by name.
NOT_1835 = {
    "madison": "Madison Street bounds the 1830 plat on the south and the modelled town "
               "stops at it; the 1835 street layer carries no Madison.",
    "monroe": "Monroe Street is south of Madison, outside the platted town of 1835.",
    "adams": "Adams Street is south of Madison, outside the platted town of 1835.",
    "jackson": "Jackson Street is south of Madison, outside the platted town of 1835.",
    "illinois": "Illinois Street is a Kinzie's Addition name the 1835 street layer does "
                "not carry.",
    "indiana": "Indiana Street is a north-side name the 1835 street layer does not carry.",
    "ohio": "Ohio Street is a north-side name the 1835 street layer does not carry.",
    "superior": "Superior Street is a north-side name the 1835 street layer does not carry.",
    "erie": "Erie Street is a north-side name the 1835 street layer does not carry.",
    "pine": "Pine Street is a north-side name the 1835 street layer does not carry.",
    "st clair": "St Clair Street is a north-side name the 1835 street layer does not carry.",
    "cass": "Cass Street is a north-side name the 1835 street layer does not carry.",
    "rush": "Rush Street is a north-side name the 1835 street layer does not carry.",
    "wabash ave": "Wabash Avenue is a lakefront street south of the 1830 plat and later "
                  "than this scene.",
    "michigan ave": "Michigan Avenue is the lakefront street south of the river and is "
                    "NOT the 1835 layer's Michigan Street, which runs east from La Salle "
                    "on the north side. Two streets, one word, and the 1839 directory "
                    "prints both.",
    "jefferson": "Jefferson Street is a west-division name the 1835 street layer does not "
                 "carry.",
    "west water": "West Water Street is the west-bank riverfront street; the 1835 layer "
                  "carries Market as the west-division street nearest the South Branch "
                  "and no West Water.",
    "north dearborn": "Dearborn Street in the 1835 layer runs from Madison to the south "
                      "bank and stops there. A north-side street of that name is later; "
                      "the north-side street on that meridian in 1835 is Wolcott.",
    "n dearborn": "Dearborn Street in the 1835 layer runs from Madison to the south "
                  "bank and stops there. A north-side street of that name is later; the "
                  "north-side street on that meridian in 1835 is Wolcott.",
    "grand ave": "Grand Avenue is a later name and lies outside the modelled town.",
    "milwaukee ave": "Milwaukee Avenue is the plank road out of the north-west and is "
                     "outside the modelled town.",
    "dearborn pl": "Dearborn Place is a later platting and is not Dearborn Street.",
    "north branch": "The North Branch is the river, not a platted street.",
    "wabash": "Wabash Avenue is a lakefront street south of the 1830 plat and later than "
              "this scene.",
}

# A word that introduces a residence rather than a place of business. `res` and
# `bds` are the Fergus volumes' own abbreviations for residence and boards-at.
#
# NORRIS SETS THE SAME THING IN HIS OWN SHORTHAND, and until T-0987 stretch 6 this
# pattern had never been asked about it: that volume's parse was refused entire, so no
# `h` or `house` address ever reached clause 2 to be tested. The moment the refusal
# became per-entry, `house N Water st (See card` — Silvester Marsh's HOME, printed
# `house` in Norris's preface's own abbreviation for it — was placed as a business face
# on North Water Street by the very clause written to refuse it. So the four words the
# four volumes actually print are all here: `res`/`bds` (Fergus), `residence`/`house`
# spelled out (Fergus 1843), and `h`/`r` (Norris, declared in his preface). The single
# letters require a following space, so no street name beginning with one can match.
#
# `hou\S{0,2}e` is the archive.org reading of `house` with a mis-set character inside
# it — `hou.«e` is in the corpus — and is the same word.
RESIDENCE_PREFIX = re.compile(
    r"^\s*(residence|res\.?|boards|bds\.?|house|hou\S{0,2}e|[hr](?=\s))\b", re.I)

# THE FIELD CAN CARRY BOTH CLAIMS (T-0987 stretch 7). The residence word usually
# opens the field; it does not always. The crosswalks split a printed line on its
# punctuation, and where the trade's own trailing corner falls into the address the
# field opens with the SHOP and goes on to the HOME: `cor Clark, res Dearborn, bet
# Washington and Madison` is Charles Loomis Harmon's shop corner and then his
# house. Clause 2 asks whether the volume prints an address as a residence, and
# that word answers it wherever in the field it stands — so the field is CUT at it,
# and each pass reads its own half. Stretch 6 fixed this fault at the head of the
# field, where `house N Water st` had been placed as a shop face; this is the same
# fault one clause in.
_HOME_CLAUSE = re.compile(
    r"[,;]\s*((?:residence|res\.?|boards|bds\.?|house|hou\S{0,2}e|[hr](?=\s))\b.*)$",
    re.I | re.S)


def split_home(printed: str):
    """(the shop half, the home half) of one printed address field.

    Either half may be empty: a field that OPENS with the residence word is all
    home, and a field with no residence word in it at all is all shop. Nothing is
    invented and nothing is dropped — the full field stays the quote on the record.
    """
    text = str(printed or "")
    if RESIDENCE_PREFIX.match(text):
        return "", text.strip()
    m = _HOME_CLAUSE.search(text)
    if not m:
        return text.strip(), ""
    return text[:m.start()].strip(" .,"), m.group(1).strip()


# The qualifiers that set a door against a second street, in two kinds. A
# CORNER word claims the corner itself; an ANCHOR word ("near Dearborn", "north
# of Lake street") sets the door somewhere off a crossing and says nothing about
# how far. Both resolve to the same point and they are NOT the same claim, so
# the record carries which word it read and calls the weaker one `anchored`.
CORNER_WORD = re.compile(r"\b(cor\.?|corner)\b", re.I)
ANCHOR_WORD = re.compile(
    r"\b(near|next|opposite|north\s+of|south\s+of|east\s+of|west\s+of|"
    r"bet\.?|between)\b", re.I)

_STREET_WORD = re.compile(
    r"\b(south\s+water|so\.?\s+water|s\.?\s+water|north\s+water|n\.?\s+water|"
    r"west\s+water|north\s+canal|n\.?\s+canal|west\s+randolph|w\.?\s+randolph|"
    r"north\s+dearborn|n\.?\s+dearborn|michigan\s+ave(?:nue)?|michigan\s+st(?:reet)?|"
    r"wabash\s+ave(?:nue)?|dearborn\s+pl(?:ace)?|grand\s+ave(?:nue)?|"
    r"milwaukee\s+ave(?:nue)?|north\s+branch|st\.?\s+clair|la\s*salle|"
    r"lake|randolph|washington|market|franklin|wells|clark[e]?|dearb(?:orn)?|state|"
    r"canal|clinton|kinzie|wolcott|madison|monroe|adams|jackson|illinois|indiana|"
    r"ohio|superior|erie|pine|cass|rush|jefferson|wabash|michigan|"
    # ...and the volumes' own contractions of those names (T-1050), LAST in the
    # alternation so a spelled-out name is always tried first: at the start of
    # `Randolph` the engine reaches `randolph` before it reaches `rand`.
    r"wash|rand|ran|dear|wol|frank|kin|clin|mich|mad|mon|jack|ind|wab|ad)\b", re.I)


# The names whose type word is part of the NAME and must survive the fold.
# `Michigan street` and `Michigan ave` are two different streets; `Dearborn pl`
# is a later platting and not Dearborn Street; and the `St` in `St Clair` is
# Saint, not Street. Every other name in the tables is bare, so the type word is
# dropped once these are settled. Without this set the strip below reduced
# `dearborn pl` to `dearborn` and `st clair` to `clair`, which made the two
# NOT_1835 keys of those names unreachable — a latent refusal no address had yet
# exercised, found by T-0669 when a residence printed `res 5 Dearborn pl`.
KEEPS_ITS_TYPE_WORD = ("michigan street", "michigan ave", "dearborn pl", "st clair")


# THE VOLUMES' OWN CONTRACTIONS OF A STREET NAME — T-1050. Norris's REMARKS page
# declares that he uses them and names three: "Abbreviations, which occur only in a
# very few words, will readily be understood; b stands for between; Rand for Randolph;
# Mad for Madison; Wash for Washinglon, &c."
# (`data/research/directories/text/norris_1844_leaf_031.txt` lines 9-11, printed page
# 21). His `&c.` is the whole difficulty: he sets eleven more the page never lists, and
# a table that knows only the spelled-out name can see none of them.
#
# That is not a cosmetic miss, because of what this table is FOR. It decides whether a
# printed name is a street the town of 1835 has, and a contraction hides the names it
# does NOT have exactly as well as the ones it does. Norris prints Rebecca Sherman's
# house at `h Clark st. b Mad. & Mon`; read as naming Clark alone, that is Clark Street
# placed on a qualifier the pass never saw — while `h Clark, b Madison and Monroe`, the
# same address spelled out one line further down the same column, is refused. One
# address, two spellings, two verdicts, and the one that said MORE was the one the pass
# could not read.
#
# The expansion happens ONCE, in `street_words`, rather than as aliases in STREET_1835
# and NOT_1835: those two tables carry the argument about the ground, a contraction is
# a fact about the type, and keeping them apart means each refusal is still written out
# exactly once.
#
# Every expansion is unique on the 1844 street list — no other Chicago street of the
# period begins Wol, Frank, Kin, Clin, Mon, Jack or Wab — and every occurrence of every
# one of these tokens, across all 4,235 addresses the four volumes print, is that
# street. Three are `documented` by the preface above; the rest are `inferred` from
# that sentence's `&c.` plus the uniqueness of the expansion, which is the reasoning
# note the confidence model requires.
PRINTED_ABBREVIATION = {
    # named by Norris's preface
    "rand": "randolph",
    "mad": "madison",
    "wash": "washington",
    # his `&c.`, one entry per token the pages actually set
    "ran": "randolph",
    "dear": "dearborn",
    "wol": "wolcott",
    "frank": "franklin",
    "kin": "kinzie",
    "clin": "clinton",
    "mich": "michigan",
    "mon": "monroe",
    "jack": "jackson",
    "ind": "indiana",
    "wab": "wabash",
    "ad": "adams",
}

# NOT in the table, and left unread on purpose. `h Lake st. b Frank <t Wat` (Norris,
# the one occurrence in 4,235 addresses) contracts either North Water Street or South
# Water Street, both of which the 1835 layer carries, and the token cannot decide
# which. T-0397's rule is that a name the page does not let you read stays unread, so
# this one is declared here instead of guessed at. Nothing turns on it either way:
# both candidates are 1835 streets, so the qualifier would be permitted under either
# reading, and `--self-test` asserts the token stays invisible.
UNREADABLE_ABBREVIATION = {
    "wat": "North Water Street or South Water Street — the contraction cannot "
           "decide which, and the 1835 layer carries both.",
}


def fold(token: str) -> str:
    """A printed street word as the table spells it: lower case, no points."""
    t = token.lower().replace(".", " ").replace(",", " ")
    t = re.sub(r"\bavenue\b", "ave", t)
    t = re.sub(r"\bstreet\b", "street", t)
    t = re.sub(r"\bplace\b", "pl", t)
    t = re.sub(r"\s+", " ", t).strip()
    if t not in KEEPS_ITS_TYPE_WORD:
        t = re.sub(r"\b(street|st|ave|pl)\b", "", t)
    return re.sub(r"\s+", " ", t).strip()


def street_words(address: str) -> list[str]:
    """Every street name the printed address contains, in the order printed."""
    out, seen = [], set()
    for m in _STREET_WORD.finditer(address):
        raw = m.group(0)
        # A CONTRACTION IS READ ONLY WHERE THE PAGE SETS IT AS A WORD OF ITS OWN
        # (T-1050). The one measured reason: the scanner sets `and` as `;ind` in
        # `res nenr Clark ;ind N. Water sts. 5th ward`, and a damaged conjunction
        # glued to a semicolon must not read as Indiana Street. Three other `Ind`
        # in the corpus all stand free and all are Indiana. No volume sets a street
        # contraction with punctuation shoved against its front, so requiring
        # whitespace in front of one costs the table nothing and closes that.
        abbrev = PRINTED_ABBREVIATION.get(raw.lower().strip(" .,"))
        if abbrev:
            if not (m.start() == 0 or address[m.start() - 1].isspace()):
                continue
            raw = abbrev
        # `michigan` alone is ambiguous; look at the word after it. The point and the
        # comma have to be stepped over, because `Mich. av.` and `Mich Av` are how
        # Norris sets the avenue and a bare `\s*ave` reads both as the north-side
        # street — which is the NOT_1835 name being hidden a second way (T-1050).
        tail = address[m.end():m.end() + 12].lower()
        if raw.lower().strip() == "michigan":
            raw = "michigan ave" if re.match(r"[\s.,]*av", tail) else "michigan street"
        elif re.match(r"^michigan\s+st", raw.lower()):
            raw = "michigan street"
        elif re.match(r"^michigan\s+ave", raw.lower()):
            raw = "michigan ave"
        f = fold(raw)
        if f and f not in seen:
            seen.add(f)
            out.append(f)
    return out


# ---------------------------------------------------------------------------
# Geometry. A face is a centreline; a corner is where two of them meet.
# ---------------------------------------------------------------------------

def _seg_intersect(a, b, c, d):
    """The point where segment ab crosses cd, or None."""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    denom = r[0] * s[1] - r[1] * s[0]
    if abs(denom) < 1e-9:
        return None
    t = ((c[0] - a[0]) * s[1] - (c[1] - a[1]) * s[0]) / denom
    u = ((c[0] - a[0]) * r[1] - (c[1] - a[1]) * r[0]) / denom
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return (a[0] + t * r[0], a[1] + t * r[1])
    return None


def crossing(path_a, path_b):
    """Where two street centrelines cross, or None if they never do.

    A crossing and a near miss are different claims: two 1835 streets that do
    not meet cannot be a corner, however the directory phrased it, and this
    returns None rather than the nearest approach so the caller has to say so.
    """
    for i in range(len(path_a) - 1):
        for j in range(len(path_b) - 1):
            p = _seg_intersect(path_a[i], path_a[i + 1], path_b[j], path_b[j + 1])
            if p is not None:
                return [round(p[0], 1), round(p[1], 1)]
    return None


# ---------------------------------------------------------------------------
# The adjudication
# ---------------------------------------------------------------------------

def load_streets() -> dict:
    doc = json.loads(STREETS.read_text())
    return {s["id"]: s for s in doc["streets"]}


def households() -> list[tuple[Path, dict]]:
    return [(p, json.loads(p.read_text())) for p in sorted(HOUSEHOLDS.glob("*.json"))]


def adjudicate(streets: dict, records: list[tuple[Path, dict]]) -> list[dict]:
    """Every `address_later` in the layer, through the four clauses, in order."""
    rows: list[dict] = []
    for path, hh in records:
        block = hh.get("directories")
        if not block:
            continue
        persons = {p["id"]: p for p in hh.get("persons", [])}
        for person in block.get("people", []):
            claim = person.get("address_later")
            if not (claim and claim.get("value")):
                continue
            rows.append(adjudicate_one(streets, hh, persons, person, claim))
    rows.sort(key=lambda r: (r["household_id"], r["person_id"]))
    return rows


def adjudicate_one(streets, hh, persons, person, claim) -> dict:
    printed = str(claim["value"])
    year = int(claim.get("describes_date") or 0)
    pid = person["person_id"]
    trade = ((persons.get(pid) or {}).get("occupation") or {}).get("value")
    works_at = (hh.get("works_at") or {}).get("value")
    row = {
        "household_id": hh["id"],
        "person_id": pid,
        "person": (persons.get(pid) or {}).get("name") or pid,
        "address_as_printed": printed,
        "describes_date": year,
        "read_back_years": year - SCENE_YEAR if year else None,
        "sources": list(claim.get("sources") or []),
        "occupation_1835": trade,
        "works_at_1835": works_at,
        "outcome": None,
        "clause": None,
        "reason": None,
        "street_id": None,
        "face": None,
        "placement": None,
        "qualifier_as_printed": None,
        "position_local_enu_m": None,
    }

    # Clause 2, first half — an 1835 placement always wins, so a household that
    # already has one is not touched and is not counted as a refusal either.
    if works_at:
        row.update(outcome="already_better_placed", clause="2",
                   reason=f"An 1835 placement already stands: this household works at "
                          f"`{works_at}`, and clause 2 says an attested 1835 placement "
                          f"always beats a door printed {row['read_back_years']} years "
                          f"later.")
        return row

    # Clause 1 — there has to be a business in 1835 to position.
    if not trade or trade == "none_recorded":
        row.update(outcome="refused", clause="1",
                   reason="The 1835 record prints no trade for this person, so there is "
                          "no 1835 business for a later door to position. Minting one out "
                          "of a directory printed after the scene date is the one thing "
                          "this pass may never do.")
        return row

    # Clause 2, second half — a residence address is a different claim.
    if RESIDENCE_PREFIX.match(printed):
        row.update(outcome="refused", clause="2",
                   reason="The directory prints this as a RESIDENCE — its own `res`, "
                          "`bds`, `house` or Norris's `h` — and this pass positions "
                          "businesses. Reading a home "
                          "address as a shop door would be the pass answering a question "
                          "nobody asked it. The residence half is T-0669.")
        return row

    names = street_words(split_home(printed)[0])
    if not names:
        row.update(outcome="refused", clause="3",
                   reason="The address names no street at all — it names a house or a "
                          "person to board with — so there is nothing to resolve onto the "
                          "1835 grid.")
        return row

    head, rest = names[0], names[1:]
    if head in NOT_1835:
        row.update(outcome="refused", clause="3", reason=NOT_1835[head])
        return row
    if head not in STREET_1835:
        row.update(outcome="refused", clause="3",
                   reason=f"'{head}' is not a street this pass's 1835 table knows, and a "
                          f"name it cannot rule on is refused rather than guessed.")
        return row

    sid = STREET_1835[head]
    street = streets[sid]
    row.update(street_id=sid, face=street["name_1835"])

    # Clause 3's second half — a qualifier that names a second street has to
    # land on the 1835 grid too, or the address is placing the shop somewhere
    # the town does not reach and the face alone would be a false reading.
    cross_ids = []
    for other in rest:
        if other in NOT_1835:
            row.update(outcome="refused", clause="3",
                       reason=f"The face resolves — {street['name_1835']} is 1835's — but "
                              f"the address places the door against a second street the "
                              f"town does not have: {NOT_1835[other]} Taking the face and "
                              f"dropping the qualifier would put the shop somewhere the "
                              f"address does not say it was.")
            return row
        if other in STREET_1835 and STREET_1835[other] != sid:
            cross_ids.append(STREET_1835[other])

    point = None
    kind = None
    if cross_ids:
        if CORNER_WORD.search(printed):
            kind = "corner"
        elif ANCHOR_WORD.search(printed):
            kind = "anchored"
        if kind:
            point = crossing(street["path_local_enu_m"],
                             streets[cross_ids[0]]["path_local_enu_m"])
    row["qualifier_as_printed"] = None
    if kind:
        m = (CORNER_WORD if kind == "corner" else ANCHOR_WORD).search(printed)
        row["qualifier_as_printed"] = m.group(0)

    if kind and point is None:
        row.update(outcome="refused", clause="3",
                   reason=f"The address sets the door against a second 1835 street that "
                          f"{street['name_1835']} never meets — the two committed "
                          f"centrelines do not cross anywhere in the modelled town — so "
                          f"the qualifier does not resolve and the face alone would be "
                          f"reading past what the directory said.")
        return row

    if point is not None:
        cross_name = streets[cross_ids[0]]["name_1835"]
        if kind == "corner":
            why = (f"and the directory sets the door AT their corner, which is the point "
                   f"where the two committed centrelines cross.")
        else:
            why = (f"and the directory sets the door against that crossing without "
                   f"claiming the corner — it prints "
                   f"'{row['qualifier_as_printed']}' — so the point is the crossing and "
                   f"the distance from it is not a claim this pass makes.")
        row.update(outcome="placed", clause="3 and 4", placement=kind,
                   position_local_enu_m=point,
                   reason=f"{street['name_1835']} and {cross_name} both stand in 1835 "
                          f"under those names, {why}")
    else:
        row.update(outcome="placed", clause="3 and 4", placement="face",
                   reason=f"{street['name_1835']} stands in 1835 under that name and in "
                          f"that place. The directory gives a street and nothing this pass "
                          f"can resolve narrower, so the placement is the FACE — the unit "
                          f"the owner's ruling of 2026-08-29 says a street name "
                          f"constrains — and no roof is dealt.")
    return row


# T-1122 — THE HOUSEHOLDER'S SEX IS NOT A READING, AND BOTH PASSES USED TO ASSERT IT.
# These two passes write the prose a reader sees on a household card, and every one of
# the residence pass's templates said "this man": 28 of its 57 rulings carried the
# phrase in their `reason` and the notes carried it again. One of the 57 is Rebecca
# Sherman, so the record as published told a reader that Norris printed where *this man*
# lived. Nothing about the reading was wrong — the prose was asserting a fact about a
# person that the source does not give and that happens to be false, which is the one
# word on that card a reader did not ask for.
#
# So the templates say "this person", "the householder", or the name; and this is what
# holds them there. It is an assertion over the strings the passes actually GENERATE —
# every static reason template, plus the `reason` and the note written for every row
# adjudicated — and not a one-time sweep of the source, because the fault is a template
# being reached for and not a line of code being present. Whole words, so `this house`
# is not read as `his house`; and the printed address and the person's own name are not
# scanned, because those are what the volume set and not what this pass says.
SEXED_OF_THE_SUBJECT = (
    "this man", "this woman", "this gentleman", "this lady",
    "his house", "her house", "his home", "her home", "his lodging", "her lodging",
    "he lived", "she lived", "he boarded", "she boarded",
    "himself", "herself", "his host", "her host",
)

_SEXED = re.compile(r"\b(?:" + "|".join(re.escape(w) for w in SEXED_OF_THE_SUBJECT)
                    + r")\b", re.I)


def generated_prose(rows, note_of, tables=()) -> list[tuple[str, str]]:
    """Every string a pass generates: its static templates, and what it wrote per row."""
    pairs = list(tables)
    for row in rows:
        pairs.append((f"{row['person_id']} reason", row.get("reason") or ""))
        pairs.append((f"{row['person_id']} note", note_of(row) or ""))
    return pairs


def sexed_prose(label: str, pairs) -> list[str]:
    """T-1122's assertion: no generated string assumes the householder's sex."""
    out = []
    for where, text in pairs:
        for hit in dict.fromkeys(m.group(0) for m in _SEXED.finditer(text or "")):
            out.append(f"{label}: {where} says {hit!r} of a person the source does "
                       f"not sex")
    return out


def note_for(row: dict) -> str:
    """The plain words clause 4 requires, on the record itself."""
    back = row["read_back_years"]
    volume = ", ".join(VOLUME_TITLE.get(s, s) for s in row["sources"])
    if row["outcome"] == "placed":
        where = {"corner": "the corner where the two streets cross",
                 "anchored": "a point on the street face, anchored on a crossing the "
                             "directory names but at a distance from it this pass does "
                             "not claim",
                 }.get(row["placement"], "the street face")
        return (
            f"A LATER ADDRESS, READ BACKWARDS {back} YEARS. The door is not an 1835 "
            f"reading: {volume} printed it in {row['describes_date']}, and this pass "
            f"carries it back to the scene date because the 1835 record attests a trade "
            f"for this person and nothing in the corpus places it better. What is claimed "
            f"is {where} and nothing narrower — no lot, no roof, no door count — and the "
            f"grade is `reconstructed`, which is this dataset's word for a figure the "
            f"reconstruction supplies rather than a source. {row['reason']} The rule this "
            f"stands on is docs/ADDRESS-BACK-PROJECTION.md and the liberty is L218; a "
            f"reader who thinks {back} years is too far to carry a shop should read the "
            f"grade as the disagreement being invited.")
    if row["outcome"] == "already_better_placed":
        return (
            f"NOT READ BACK, BECAUSE SOMETHING BETTER ALREADY STANDS. {volume} prints an "
            f"address against this name in {row['describes_date']}, and it is left where "
            f"it is. {row['reason']} The later address stays on the record as "
            f"{row['describes_date']}'s evidence and moves nothing.")
    return (
        f"REFUSED, AND THE REFUSAL IS THE RECORD. {volume} prints an address against this "
        f"name in {row['describes_date']} and this pass will not carry it back to 1835. "
        f"{row['reason']} A refusal is written here rather than dropped so that a later "
        f"run can see the address was read and ruled on, not missed "
        f"(docs/ADDRESS-BACK-PROJECTION.md, clause {row['clause']}).")


def block_for(row: dict) -> dict:
    """The `back_projection` block as the household record carries it.

    `street_id` stays in the ledger and off the record on purpose. It is the join
    to `data/streets/1835.json` that the pass resolves ON, and the record already
    carries the same fact in the words the volume used — the street's 1835 NAME,
    which is what the card prints. A key on a record that nothing reads is what
    `tools/measure_layer_reads.py` exists to find, and not writing it is a better
    answer than declaring it unread.
    """
    out = {
        "outcome": row["outcome"],
        "clause": row["clause"],
        "value": row["face"] if row["outcome"] == "placed" else None,
        # A CONFIDENCE ONLY ON A PLACEMENT. A refusal is not a figure held at low
        # confidence, it is the absence of a figure, and writing `reconstructed`
        # over it — or writing the key at all with nothing in it — would put a
        # grade on a claim nobody made. `tools/validate.py` reads a `confidence`
        # anywhere in this layer against the closed vocabulary, and it is right to.
        **({"confidence": "reconstructed"} if row["outcome"] == "placed" else {}),
        "describes_date": row["describes_date"],
        "read_back_years": row["read_back_years"],
        "placement": row["placement"],
        "position_local_enu_m": row["position_local_enu_m"],
        "sources": list(row["sources"]),
        "note": note_for(row),
    }
    return out


def counts(rows: list[dict]) -> dict:
    placed = [r for r in rows if r["outcome"] == "placed"]
    return {
        "addresses_adjudicated": len(rows),
        "placed": len(placed),
        "placed_as_a_face": len([r for r in placed if r["placement"] == "face"]),
        "placed_as_a_corner": len([r for r in placed if r["placement"] == "corner"]),
        "placed_anchored_on_a_crossing": len(
            [r for r in placed if r["placement"] == "anchored"]),
        "already_better_placed": len([r for r in rows
                                      if r["outcome"] == "already_better_placed"]),
        "refused": len([r for r in rows if r["outcome"] == "refused"]),
        "refused_clause_1_no_1835_business": len(
            [r for r in rows if r["outcome"] == "refused" and r["clause"] == "1"]),
        "refused_clause_2_a_residence_not_a_shop": len(
            [r for r in rows if r["outcome"] == "refused" and r["clause"] == "2"]),
        "refused_clause_3_not_on_the_1835_grid": len(
            [r for r in rows if r["outcome"] == "refused" and r["clause"] == "3"]),
        "faces_reached": sorted({r["face"] for r in rows if r["outcome"] == "placed"}),
        "lives_at_real_values": None,
        "works_at_real_values": None,
    }


def link_counts(records) -> tuple[int, int]:
    lives = sum(1 for _, h in records if (h.get("lives_at") or {}).get("value"))
    works = sum(1 for _, h in records if (h.get("works_at") or {}).get("value"))
    return lives, works


def build(records=None) -> tuple[dict, dict[str, dict]]:
    """The ledger, and the `back_projection` block each person's record gets."""
    streets = load_streets()
    records = records if records is not None else households()
    rows = adjudicate(streets, records)
    c = counts(rows)
    lives, works = link_counts(records)
    c["lives_at_real_values"] = lives
    c["works_at_real_values"] = works
    ledger = {
        "schema": 1,
        "_doc": "GENERATED by tools/back_project_addresses.py (T-0633). Every address a "
                "Chicago directory of 1839, 1843 or 1844 prints against a person of "
                "1835, put through the four clauses of docs/ADDRESS-BACK-PROJECTION.md. "
                "The policy is L218 and the unit of a placement is a STREET FACE, never "
                "a lot and never a roof. Refusals are here in full: an address this pass "
                "declines is a reading it made, not one it missed.",
        "generated_by": "tools/back_project_addresses.py",
        "policy": "docs/ADDRESS-BACK-PROJECTION.md",
        "liberty": "L218",
        "scene_year": SCENE_YEAR,
        "street_layer": "data/streets/1835.json",
        "counts": c,
        "rows": rows,
    }
    blocks = {f"{r['household_id']}::{r['person_id']}": block_for(r) for r in rows}
    return ledger, blocks


def write() -> dict:
    records = households()
    ledger, blocks = build(records)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    # `indent=1, ensure_ascii=False` and a trailing newline: the households are
    # written by tools/spend_directories.py in exactly that shape and both passes
    # compare their files byte for byte, so a second writer with its own dialect
    # would put the two gates permanently at war.
    LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")
    for path, hh in records:
        block = hh.get("directories")
        if not block:
            continue
        touched = False
        for person in block.get("people", []):
            key = f"{hh['id']}::{person['person_id']}"
            if key in blocks:
                if person.get("back_projection") != blocks[key]:
                    person["back_projection"] = blocks[key]
                    touched = True
            elif "back_projection" in person:
                del person["back_projection"]
                touched = True
        if touched:
            path.write_text(json.dumps(hh, indent=1, ensure_ascii=False) + "\n")
    return ledger["counts"]


def check() -> int:
    records = households()
    ledger, blocks = build(records)
    problems = []
    if not LEDGER.exists():
        problems.append(f"{LEDGER.relative_to(ROOT)} is missing")
    else:
        on_disk = json.loads(LEDGER.read_text())
        if on_disk != ledger:
            problems.append(f"{LEDGER.relative_to(ROOT)} disagrees with a re-derivation "
                            f"— run tools/back_project_addresses.py --write")
    for path, hh in records:
        for person in (hh.get("directories") or {}).get("people", []):
            key = f"{hh['id']}::{person['person_id']}"
            want = blocks.get(key)
            if person.get("back_projection") != want:
                problems.append(f"{path.name}: {person['person_id']} carries a "
                                f"back_projection block that is not the one this pass "
                                f"derives")
    for p in problems[:20]:
        print(f"   {p}")
    if problems:
        print(f"back_project_addresses: {len(problems)} problem(s)")
        return 1
    print(f"back_project_addresses: ok — {ledger['counts']['addresses_adjudicated']} "
          f"addresses adjudicated, {ledger['counts']['placed']} placed, "
          f"{ledger['counts']['already_better_placed']} already better placed, "
          f"{ledger['counts']['refused']} refused")
    return 0


# ---------------------------------------------------------------------------

def self_test() -> int:
    """The clauses, on cases the corpus actually contains."""
    streets = load_streets()
    fails = []

    def one(printed, trade, works, year=1839):
        hh = {"id": "hh_t", "works_at": {"value": works},
              "persons": [{"id": "p", "name": "T", "occupation": {"value": trade}}]}
        persons = {"p": hh["persons"][0]}
        person = {"person_id": "p"}
        claim = {"value": printed, "describes_date": year, "sources": ["fergus_chicago_directory_1839"]}
        return adjudicate_one(streets, hh, persons, person, claim)

    def want(label, row, outcome, clause, placement=None):
        if row["outcome"] != outcome or row["clause"] != clause or (
                placement is not None and row["placement"] != placement):
            fails.append(f"{label}: got {row['outcome']}/{row['clause']}/"
                         f"{row['placement']}, wanted {outcome}/{clause}/{placement}")

    # Clause 2 beats clause 1 and clause 3 both: an 1835 placement always wins.
    want("an 1835 works_at wins", one("Clark st", "grocer", "peck_store"),
         "already_better_placed", "2")
    # Clause 1: no trade in 1835, nothing to position.
    want("no 1835 trade", one("Clark street", "none_recorded", None), "refused", "1")
    want("no occupation block", one("Clark street", None, None), "refused", "1")
    # Clause 2: a residence is not a shop.
    want("res is a residence", one("res 15 Lake", "attorney", None), "refused", "2")
    want("bds is a residence", one("bds Tremont House", "merchant", None), "refused", "2")
    # ...and Norris's own shorthand for the same word, which until T-0987 stretch 6 this
    # clause had never been shown, because that volume's parse never reached it. The
    # instance: `house N Water st` was PLACED as a business face on the one street in
    # the town no other rule can seat a shop on.
    want("house is a residence", one("house N Water st", "merchant", None), "refused", "2")
    want("Norris's h is a residence", one("h Clark st. b Mad. & Mon", "attorney", None),
         "refused", "2")
    want("Norris's r is a residence", one("r Ind, b Cass & Rush", "grocer", None),
         "refused", "2")
    want("a mis-set house is still a house",
         one("hou.\u00abe Randolph st. 1st ward", "carpenter", None), "refused", "2")
    # And the letters are not street names: a street beginning with one still places.
    want("Randolph is not Norris's r", one("Randolph st", "grocer", None),
         "placed", "3 and 4", "face")
    want("Lake is not Norris's h", one("Lake st", "grocer", None),
         "placed", "3 and 4", "face")
    # Clause 3: the street has to be 1835's, under that name, in that place.
    want("Michigan ave is not Michigan Street",
         one("Michigan ave", "brickmaker", None), "refused", "3")
    want("North Dearborn is later",
         one("North Dearborn street", "speculator", None), "refused", "3")
    want("West Water is not in the layer",
         one("West Water street near Lake st", "insurance_agent", None), "refused", "3")
    want("a house is not a street", one("bds Mrs. Post", "sub_agent", None), "refused", "2")
    want("no street named at all", one("hi", "merchant", None), "refused", "3")
    # Clause 3's second half: the qualifier has to land on the grid too.
    want("cor. Monroe is off the 1835 grid",
         one("Clark st cor. Monroe", "grocer", None), "refused", "3")
    # Placement: a face, and a corner where both streets are 1835's.
    want("a bare street is a face",
         one("South Water street", "shoemaker", None), "placed", "3 and 4", "face")
    want("'near' anchors, it does not claim a corner",
         one("Randolph street near Dearborn", "blacksmith", None),
         "placed", "3 and 4", "anchored")
    want("'cor' does claim the corner",
         one("Lake st cor. Clark", "grocer", None), "placed", "3 and 4", "corner")
    want("two 1835 streets that never meet are not a corner",
         one("Clark st cor. Dearborn", "grocer", None), "refused", "3")
    want("a corner word with no second street is still a face",
         one("159 Lake st, corner", "merchant", None), "placed", "3 and 4", "face")
    want("an 1844 landmark leaves a face",
         one("office Clark street, opposite City Saloon", "hardware_merchant", None,
             year=1844), "placed", "3 and 4", "face")

    # T-1050 — THE VOLUMES' OWN CONTRACTIONS, one case per entry in the table, each
    # quoted off a page. The table is shared with the residence pass, so this is where
    # it is held: a contraction that stops resolving silently un-refuses every address
    # whose qualifier it hides, which is the fault that ticket was filed for.
    for printed, expect in [
            ("h Wells st. b Rand and Wash sis", ["wells", "randolph", "washington"]),
            ("h Wells st. b Wash & Mad", ["wells", "washington", "madison"]),
            ("house State st. b Ran dolph and Washington streets",
             ["state", "randolph", "washington"]),
            ("h Rand st. b Dear and Lake sts", ["randolph", "dearborn", "lake"]),
            ("h Mich st. b Dear & Wol", ["michigan street", "dearborn", "wolcott"]),
            ("b Wells & Frank", ["wells", "franklin"]),
            ("b Kin and Dear", ["kinzie", "dearborn"]),
            ("h Washington, b Canal & Clin", ["washington", "canal", "clinton"]),
            ("h Clark st. b Mad. & Mon", ["clark", "madison", "monroe"]),
            ("b Jack. & Fifth", ["jackson"]),
            ("r Ind, b Cass & Rush", ["indiana", "cass", "rush"]),
            ("res Wab. av. b Mon. and Ad", ["wabash", "monroe", "adams"]),
            # The point and the comma between `Mich` and `av` are Norris's, and the
            # avenue is the NOT_1835 name, so stepping over them is load-bearing.
            ("house cor Mich. av. and Randolph", ["michigan ave", "randolph"]),
            ("h c Mich Av & Mad st", ["michigan ave", "madison"]),
            ("h c Mich dc Cass", ["michigan street", "cass"]),
            # The scanner's word-splits fall out of the same table: a contraction is
            # what the first half of a broken name looks like.
            ("house Dear-. born street, bet Randolph and Washington",
             ["dearborn", "randolph", "washington"]),
            ("house State street, bet Wash ington and Madison",
             ["state", "washington", "madison"]),
            # A contraction is read only where the page sets it as a word of its own:
            # `;ind` here is the scanner's `and`, not Indiana Street.
            ("res nenr Clark ;ind N. Water sts. 5th ward", ["clark", "n water"]),
            # And the one contraction left unread, because it cannot be decided.
            ("h Lake st. b Frank <t Wat", ["lake", "franklin"]),
    ]:
        got = street_words(printed)
        if got != expect:
            fails.append(f"contraction: {printed!r} read as {got}, wanted {expect}")
    for token in UNREADABLE_ABBREVIATION:
        if token in PRINTED_ABBREVIATION:
            fails.append(f"'{token}' is declared unreadable and also expanded")
        if street_words(f"h Lake st. b {token.title()}") != ["lake"]:
            fails.append(f"'{token}' is declared unreadable and still read as a street")
    # Every expansion has to be a name one of the two tables rules on, or the
    # contraction buys a refusal reading `'x' is not a street this pass's table knows`
    # — a right answer for a wrong reason, which is worse than not reading it. The one
    # exception is `michigan`, which is deliberately NOT in either table: it is
    # ambiguous between the north-side street and the lakefront avenue, and the
    # disambiguation above splits it before the tables are consulted.
    for token, full in PRINTED_ABBREVIATION.items():
        if full == "michigan":
            continue
        if full not in STREET_1835 and full not in NOT_1835:
            fails.append(f"'{token}' expands to '{full}', which neither table rules on")
    for reading in ("michigan street", "michigan ave"):
        if reading not in STREET_1835 and reading not in NOT_1835:
            fails.append(f"'{reading}' is a reading of `Mich` neither table rules on")

    # Michigan Street, the north-side one, does resolve.
    r = one("Michigan st", "forwarding_and_commission", None)
    if r["street_id"] != "michigan_north":
        fails.append(f"Michigan st should reach michigan_north, got {r['street_id']}")

    # The corner point is a real crossing of two committed centrelines.
    r = one("Randolph street near Dearborn", "blacksmith", None)
    x, y = r["position_local_enu_m"]
    if not (690 < x < 705 and -262 < y < -248):
        fails.append(f"Randolph/Dearborn crossing is at {r['position_local_enu_m']}, "
                     f"which is not where those two centrelines meet")

    # Two parallel streets never make a corner, however the directory phrased it.
    if crossing(streets["lake"]["path_local_enu_m"],
                streets["randolph"]["path_local_enu_m"]) is not None:
        fails.append("Lake and Randolph are parallel and must not cross")

    # Clause 4 is not optional: every placement is `reconstructed` and says so.
    ledger, blocks = build()
    for row in ledger["rows"]:
        b = block_for(row)
        if row["outcome"] == "placed":
            if b["confidence"] != "reconstructed":
                fails.append(f"{row['person_id']}: a placement graded {b['confidence']}")
            if "read backwards" not in b["note"].lower():
                fails.append(f"{row['person_id']}: the note does not say it is read back")
        if b["note"] is None or not b["note"].strip():
            fails.append(f"{row['person_id']}: no note")

    # Acceptance clause 4: nothing this pass writes touches an 1835 link.
    for _, hh in households():
        for person in (hh.get("directories") or {}).get("people", []):
            bp = person.get("back_projection")
            if bp and set(bp) & {"lives_at", "works_at"}:
                fails.append(f"{hh['id']}: a back_projection block writing an 1835 link")

    # T-1122: nothing this pass generates assumes the householder's sex — the static
    # refusal templates keyed on a street the town does not carry, and the `reason` and
    # note written for every row actually adjudicated.
    fails.extend(sexed_prose("back_project_addresses", generated_prose(
        ledger["rows"], note_for,
        [(f"NOT_1835[{k}]", v) for k, v in NOT_1835.items()])))

    for f in fails:
        print(f"   {f}")
    print(f"back_project_addresses --self-test: "
          f"{'FAIL' if fails else 'ok'} ({len(fails)} problem(s))")
    return 1 if fails else 0


def report() -> int:
    ledger, _ = build()
    c = ledger["counts"]
    for k, v in c.items():
        print(f"  {k}: {v}")
    print()
    for row in ledger["rows"]:
        if row["outcome"] == "placed":
            print(f"  PLACED   {row['person']:28s} {row['describes_date']} "
                  f"{row['placement']:9s} {row['face']}  <- {row['address_as_printed']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.write:
        c = write()
        print(f"back_project_addresses: {c['addresses_adjudicated']} adjudicated, "
              f"{c['placed']} placed ({c['placed_as_a_face']} faces, "
              f"{c['placed_as_a_corner']} corners), "
              f"{c['already_better_placed']} already better placed, {c['refused']} refused")
        return 0
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    return check()


if __name__ == "__main__":
    sys.exit(main())
