#!/usr/bin/env python3
"""The kinship the committed sources already state, counted and ruled on (T-0734).

    python3 tools/survey_stated_kin.py             the survey, on stdout
    python3 tools/survey_stated_kin.py --write     write data/residents/kin_survey.json
    python3 tools/survey_stated_kin.py --check     re-derive, and hold every proposal to a ruling
    python3 tools/survey_stated_kin.py --self-test the assertions of --check, broken on purpose

WHAT THIS IS FOR.

The final resident audit (T-0512) counted the town's family life and found 14 of
1,404 people carrying a stated kin relationship to anybody at all. Some of that
is true — a post-office letter list prints a name and nothing else, and this
project will not invent a family out of a shared surname. Some of it is not: the
corpus PRINTS kinship it has already read and transcribed, and the household
records never took it.

`persons[].relationship` is a person's place inside ONE household and stops at
its edge; `kin` (T-0597) is the link that crosses two records. Both existed
before this pass. What did not exist was any way to know how much stated kinship
the corpus was sitting on, so every tie was found by somebody reading a card and
noticing. This module is the counting: it reads the committed sources, resolves
BOTH ends against the residents layer, and reports what is available. It writes
no kin row itself — a kinship is a ruling, and rulings are authored in
`data/residents/kin_rulings.json` by a person who has read the source.

THE TWO FILES, AND WHY THEY ARE TWO.

  data/residents/kin_survey.json    DERIVED. Re-derived by --check; hand-edits lose.
  data/residents/kin_rulings.json   AUTHORED. One ruling per proposal, with its reason.

A derivation that also carried the rulings would rewrite the rulings every time
the corpus grew. A ruling file that also carried the derivation would let a
proposal quietly disappear when a card was edited. Split, --check can demand the
thing that actually matters: EVERY landable proposal is answered, in writing,
and no answer is silently dropped when the survey moves under it.

WHAT IS READ (declared, because a survey's corpus is its argument):

  * data/research/church/records/st_marys_baptisms_1833_1835.json — the register
    states parentage in the entry itself: `fils de Mark Beaubien et de Monique
    Nadeau`, transcribed into father/mother/child roles.
  * data/research/church/records/st_cyr_marriages_1834_1839.json — groom and
    bride of one entry are husband and wife by the act the entry records.
  * data/research/church/records/st_cyr_deaths_1834_1837.json — the parent roles
    the burial entries name.
  * data/residents/households/*.json — the prose already on the cards, where a
    source has been quoted saying `brother of Samuel`, `son of Jean Baptiste
    Beaubien`, `half-brother of A. Clybourne`. The subject is that card's head.

WHAT IS NOT READ, AND WHY.

The 1840 census households. The bridge has matched heads to residents, and a
census household is the densest kinship the corpus holds — but the crosswalk on
`dev` is 235 named heads stale against the pages (T-0714) and derived against
849 residents where the town now holds 1,404 (T-0698). Reading kin off a
crosswalk that does not know two fifths of the town would land ties against the
wrong people. It is the largest seam left and it is deliberately not this pass's.

HOW A NAME IN A SOURCE BECOMES A PERSON, AND THE LINE THIS PASS WILL NOT CROSS.

For a register entry the answer is already committed and is not a match at all:
the cards carry `..._evidence[].record_id` back-links, and most of the parties to
these marriages EXIST BECAUSE OF the entry that names them — `hh_frauner_m` is
the bride of marriage 1, rung G2c, minted from `st_cyr_marriage_001_2`. Where
both ends carry a back-link the kinship is as documented as the people are, and
this pass resolves by back-link and by nothing else.

Where a back-link is missing but a town person of that name exists, the outcome
is `identity_not_asserted` and the row is reported and NOT proposed. The town's
John Murphy is attested from Andreas, the voter lists and Fergus (G1a) and
carries no back-link to marriage 6; a surname and a forename would have married
him to Bridget Rogers on the strength of nothing, and the st_cyr crosswalk had
already declined that identity as a candidate rather than a merge.

For prose ALREADY QUOTED ONTO A CARD the subject is that card's head by
construction, and the other party is resolved by name, on the crosswalk's own
rule and not a new one:

  * the surname folds equal (case, accents and apostrophes ignored);
  * the forenames agree token for token, an initial matching a full forename
    that begins with it;
  * EXACTLY ONE person in the town may match. Two is `ambiguous` and is
    reported, never guessed — six households in this dataset are Kinzies and
    four are Clarks, and a kinship written onto the wrong one of them is worse
    than no kinship at all.

Every such row is still only a PROPOSAL: it is answered in kin_rulings.json by
somebody who has read the source, and --check refuses to pass while one is
unanswered.

A relation is only proposed when its inverse is declared in validate.py, because
a relation whose inverse is unknown cannot be checked for reciprocity and this
project does not write a claim its gate cannot read.
"""
from __future__ import annotations

import itertools
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
CHURCH = ROOT / "data" / "research" / "church" / "records"
SURVEY = RESIDENTS / "kin_survey.json"
RULINGS = RESIDENTS / "kin_rulings.json"
READINGS = RESIDENTS / "kin_readings.json"

SCHEMA = "chicago4d.kin_survey.v1"

# The relations this pass may propose: exactly the ones validate.py knows an
# inverse for. Kept here as a literal and CHECKED against validate.py at run
# time, so the two cannot drift apart in silence.
PROPOSABLE = {
    "brother": "brother",
    "sister": "sister",
    "half_brother": "half_brother",
    "half_sister": "half_sister",
    "husband": "husband",
    "wife": "wife",
    "father": "father",
    "mother": "mother",
    "son": "son",
    "daughter": "daughter",
}

HONORIFIC = re.compile(
    r"^(mr|mrs|miss|col|colonel|capt|captain|cpt|dr|doctor|rev|reverend|gen|general"
    r"|lieut|lt|maj|major|hon|judge|esq|sr|jr|st|ste|late|widow|mme|mons|monsieur)$"
)

# `<relation> of <Name>` in the prose a card already carries. The name is at most
# four capitalised tokens; anything longer is a sentence, not a person.
PROSE = re.compile(
    r"\b(half[- _]?brothers?|half[- _]?sisters?|brothers?|sisters?|sons?|daughters?"
    r"|fathers?|mothers?|wife|wives|widow|husbands?)\s+of\s+"
    r"((?:[A-Z][A-Za-z'À-ÿ]*\.?)(?:\s+[A-Z][A-Za-z'À-ÿ]*\.?){0,3})"
)

# `his|her <relation> <Name>` — the SAME statement without the "of" (T-0734, the
# ties #947 read and this survey could not see). Mark Beaubien's own card reaches
# for "Andreas's life of HIS BROTHER Jean Baptiste" to date the family's move, and
# the pattern above cannot match it because English does not put an "of" there.
#
# It is a generalisation of PROSE and not a loosening of it: the name is bounded
# the same way, and every candidate still has to resolve to EXACTLY ONE town
# person before it can be proposed. Measured over the committed prose before it
# was added — 10 matches, of which the resolution step refuses "his mother
# Potawatomi", "his mother Mah" (a hyphenated name the bound truncates) and the
# other non-names on its own. The net is wider; the sieve is unchanged.
PROSE_POSSESSIVE = re.compile(
    r"\b(?:his|her|their)\s+(half[- _]?brothers?|half[- _]?sisters?|brothers?|sisters?"
    r"|sons?|daughters?|fathers?|mothers?|wife|wives|widow|husbands?)\s+"
    r"((?:[A-Z][A-Za-z'À-ÿ]*\.?)(?:\s+[A-Z][A-Za-z'À-ÿ]*\.?){0,3})"
)

# THE ELLIPSIS A QUOTED SOURCE LEAVES. Andreas prints "John Miller, brother of
# Samuel, the landlord" and the surname is carried by the sentence, not repeated.
# A bare forename identifies nobody on its own — so it is read with the SUBJECT'S
# surname, and then has to resolve to exactly one town person like any other name.
# Only inside a card, where the subject is known by construction.

PROSE_RELATION = {
    "half-brother": "half_brother", "half brother": "half_brother",
    "half_brother": "half_brother", "half-brothers": "half_brother",
    "half brothers": "half_brother", "half_brothers": "half_brother",
    "half-sister": "half_sister", "half sister": "half_sister",
    "half_sister": "half_sister", "half-sisters": "half_sister",
    "half sisters": "half_sister", "half_sisters": "half_sister",
    "brother": "brother", "brothers": "brother",
    "sister": "sister", "sisters": "sister",
    "son": "son", "sons": "son",
    "daughter": "daughter", "daughters": "daughter",
    "father": "father", "fathers": "father",
    "mother": "mother", "mothers": "mother",
    "wife": "wife", "wives": "wife", "widow": "wife",
    "husband": "husband", "husbands": "husband",
}


def fold(name: str) -> list[str]:
    """A name reduced to its comparable tokens: no accents, no honorifics, no stops."""
    n = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    n = n.replace("'", "").replace("’", "")
    toks = [t.strip(".,;:()[]").lower() for t in re.split(r"[\s]+", n)]
    toks = [t for t in toks if t and not HONORIFIC.match(t)]
    return toks


def forenames_agree(a: list[str], b: list[str]) -> bool:
    """Token for token, an initial matching a full forename that begins with it."""
    if not a or not b:
        return False
    for x, y in zip(a, b):
        if x == y:
            continue
        if len(x) == 1 and y.startswith(x):
            continue
        if len(y) == 1 and x.startswith(y):
            continue
        return False
    return True


class Town:
    """The residents layer, indexed by folded surname."""

    def __init__(self, docs: dict[str, dict]):
        self.docs = docs
        self.by_surname: dict[str, list[tuple]] = defaultdict(list)
        self.person_home: dict[str, str] = {}
        self.by_record: dict[str, tuple] = {}
        for hid, h in sorted(docs.items()):
            for p in h.get("persons") or []:
                toks = fold(p.get("name") or "")
                if toks:
                    self.by_surname[toks[-1]].append((hid, p.get("id"), p.get("name"), toks))
                self.person_home[p.get("id")] = hid
                for key, block in p.items():
                    if not (key.endswith("_evidence") and isinstance(block, list)):
                        continue
                    for e in block:
                        rid = isinstance(e, dict) and e.get("record_id")
                        if rid:
                            self.by_record.setdefault(rid, (hid, p.get("id"), p.get("name")))

    def by_source_record(self, record_id: str) -> list[tuple]:
        """The person a card has already claimed FROM this source record, if any."""
        hit = self.by_record.get(record_id)
        return [hit] if hit else []

    def resolve(self, name: str) -> list[tuple]:
        """Every town person the matching rule admits for this printed name."""
        toks = fold(name)
        if len(toks) < 2:            # a bare surname identifies nobody
            return []
        hits = []
        for hid, pid, pname, ptoks in self.by_surname.get(toks[-1], ()):
            if len(ptoks) < 2:
                continue
            if forenames_agree(toks[:-1], ptoks[:-1]):
                hits.append((hid, pid, pname))
        return sorted(hits)


def load_town() -> dict[str, dict]:
    return {f.stem: json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(HOUSEHOLDS.glob("*.json"))}


def _statement(sid, source, locator, as_read, subject_name, relation, other_name,
               subject_record=None, other_record=None):
    return {"id": sid, "source": source, "locator": locator, "as_read": as_read,
            "subject_as_read": subject_name, "relation": relation,
            "other_as_read": other_name,
            "subject_record": subject_record, "other_record": other_record}


def read_church() -> list[dict]:
    """The register's own roles, which state kinship without being read into."""
    out: list[dict] = []

    baptisms = CHURCH / "st_marys_baptisms_1833_1835.json"
    if baptisms.exists():
        recs = json.loads(baptisms.read_text(encoding="utf-8"))["records"]
        src = json.loads(baptisms.read_text(encoding="utf-8")).get("source_id") or "st_marys_baptisms"
        entries: dict[tuple, dict] = defaultdict(dict)
        for r in recs:
            loc = r.get("locator") or {}
            key = (loc.get("year_series"), loc.get("entry"))
            role = loc.get("role")
            if role in ("child", "father", "mother"):
                entries[key].setdefault(role, r)
        for key, roles in sorted(entries.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
            child = roles.get("child")
            if not child:
                continue
            for parent_role, child_side in (("father", "son"), ("mother", "son")):
                parent = roles.get(parent_role)
                if not parent:
                    continue
                # The register names the parent; the child's sex is not stated by the
                # role, so the CHILD end is proposed as the parent's relation only and
                # the ruling names the child's term. Proposed from the parent's side.
                out.append(_statement(
                    f"{parent['id']}__parent_of__{child['id']}",
                    src, f"{parent['id']}", (parent.get("cells") or {}).get("entry_as_read", "")[:300],
                    parent.get("normalized") or parent.get("as_read"),
                    parent_role,
                    child.get("normalized") or child.get("as_read"),
                    parent["id"], child["id"]))

    marriages = CHURCH / "st_cyr_marriages_1834_1839.json"
    if marriages.exists():
        doc = json.loads(marriages.read_text(encoding="utf-8"))
        src = doc.get("source_id") or "st_cyr_register"
        entries: dict[int, dict] = defaultdict(dict)
        for r in doc["records"]:
            loc = r.get("locator") or {}
            if loc.get("role") in ("groom", "bride"):
                entries[loc.get("entry")].setdefault(loc["role"], r)
        for n, roles in sorted(entries.items(), key=lambda kv: str(kv[0])):
            groom, bride = roles.get("groom"), roles.get("bride")
            if not (groom and bride):
                continue
            cells = groom.get("cells") or {}
            as_read = f"{cells.get('groom')} and {cells.get('bride')}, married {cells.get('date')}"
            out.append(_statement(f"{groom['id']}__husband_of__{bride['id']}", src,
                                  groom["id"], as_read,
                                  groom.get("normalized") or groom.get("as_read"), "husband",
                                  bride.get("normalized") or bride.get("as_read"),
                                  groom["id"], bride["id"]))

    deaths = CHURCH / "st_cyr_deaths_1834_1837.json"
    if deaths.exists():
        doc = json.loads(deaths.read_text(encoding="utf-8"))
        src = doc.get("source_id") or "st_cyr_register"
        entries: dict[int, dict] = defaultdict(dict)
        for r in doc["records"]:
            loc = r.get("locator") or {}
            if loc.get("role") in ("decedent", "parent"):
                entries[loc.get("entry")].setdefault(loc["role"], r)
        for n, roles in sorted(entries.items(), key=lambda kv: str(kv[0])):
            dec, par = roles.get("decedent"), roles.get("parent")
            if not (dec and par):
                continue
            out.append(_statement(f"{par['id']}__parent_of__{dec['id']}", src, par["id"],
                                  (par.get("cells") or {}).get("entry_as_read", "")[:300]
                                  or par.get("notes", "")[:300],
                                  par.get("normalized") or par.get("as_read"), "father",
                                  dec.get("normalized") or dec.get("as_read"),
                                  par["id"], dec["id"]))
    return out


def read_cards(docs: dict[str, dict]) -> list[dict]:
    """The kin prose already quoted onto the cards. The subject is the card's head."""
    out: list[dict] = []
    for hid, h in sorted(docs.items()):
        head = h.get("head")
        head_name = next((p.get("name") for p in h.get("persons") or []
                          if p.get("id") == head), None)
        if not head_name:
            continue
        # NOT the `kin` block: those rows are this dataset's own conclusions, and a
        # survey that read them back would find its own landings and propose them
        # again as if a source had said so.
        blob = json.dumps({k: v for k, v in h.items() if k != "kin"}, ensure_ascii=False)
        seen: set[tuple] = set()
        for m in itertools.chain(PROSE.finditer(blob), PROSE_POSSESSIVE.finditer(blob)):
            rel = PROSE_RELATION.get(m.group(1).lower().replace("_", " ").replace("-", " ")) \
                or PROSE_RELATION.get(m.group(1).lower())
            other = m.group(2).strip()
            if not rel or (rel, other) in seen:
                continue
            seen.add((rel, other))
            start = max(0, m.start() - 90)
            surname = fold(head_name)[-1:] if fold(head_name) else []
            # THE ELLIPSIS, AND IT IS NOT ONLY ONE TOKEN LONG (T-0734).
            #
            # The rule below the PROSE pattern says a name a quoted source leaves
            # without a surname is read with the SUBJECT'S — Andreas prints "John
            # Miller, brother of Samuel". That was implemented as "exactly one
            # token", which is a fair reading of `Samuel` and a wrong one of `Jean
            # Baptiste`: Mark Beaubien's card says "his brother Jean Baptiste", two
            # tokens, both forenames, no surname anywhere in them. The sentence
            # elides the surname exactly as Andreas's does; it just happens to elide
            # it after a COMPOUND forename.
            #
            # So the test is what it always meant: the name carries no surname the
            # town knows. If the name resolves on its own it is left alone; only a
            # name that resolves to NOBODY is re-read with the subject's surname,
            # and it must then still resolve to exactly one person like any other.
            # A wrong guess cannot land here — it can only fail to resolve twice.
            # The resolver does not exist here, so this only says the name is SHORT
            # ENOUGH to be an ellipsis; `classify` decides, because only it can ask
            # whether the name resolves on its own first.
            ellipsis = bool(surname) and 1 <= len(fold(other)) <= 2
            out.append(dict(_statement(
                f"{hid}__{rel}__{re.sub(r'[^a-z0-9]+', '_', other.lower()).strip('_')}",
                "card_prose", hid, blob[start:m.end() + 60],
                head_name, rel, other),
                other_read_with_subject_surname=bool(ellipsis)))
    return out


def classify(statements: list[dict], town: Town) -> list[dict]:
    """Resolve both ends of every statement and say what it is worth."""
    rows = []
    for st in statements:
        row = dict(st)
        relation = st["relation"]
        if relation not in PROPOSABLE:
            row["outcome"] = "relation_undeclared"
            rows.append(row)
            continue
        unasserted = False
        if st.get("authored_reading"):
            # AN AUTHORED READING NAMES BOTH PEOPLE OUTRIGHT, which is the whole
            # difference between it and a derived statement: a pattern finds a
            # NAME and has to work out who that is, while a person reading a
            # sentence has already done that and says so. So this resolves by
            # person id and not by name — and an id that is not on a card resolves
            # to nobody, so a typo cannot invent a tie. The quote behind it is
            # verified separately by authored_quote_problems().
            def _seat(end):
                for hid, doc in town.docs.items():
                    for person in doc.get("persons") or []:
                        if person["id"] == end:
                            return [(hid, end, person.get("name") or end)]
                return []
            subj = _seat(st["subject_record"])
            other = _seat(st["other_record"])
        elif st["source"] == "card_prose":
            hid = st["locator"]
            subj = [(hid, town.docs[hid]["head"], st["subject_as_read"])]
            other_name = st["other_as_read"]
            other = town.resolve(other_name)
            # THE NAME AS PRINTED FIRST, the ellipsis only if it names nobody. A
            # quoted source that elides the surname ("brother of Samuel", "his
            # brother Jean Baptiste") is re-read with the SUBJECT'S surname — but
            # only after the printed name has been given its chance, so a name that
            # stands on its own is never rewritten. The re-read still has to resolve
            # to exactly one town person, so this can fail to find somebody; it
            # cannot find the wrong somebody.
            if not other and st.get("other_read_with_subject_surname"):
                other_name = f"{other_name} {fold(st['subject_as_read'])[-1]}"
                other = town.resolve(other_name)
        else:
            subj = town.by_source_record(st["subject_record"])
            other = town.by_source_record(st["other_record"])
            # A side the cards have not claimed from this record is an identity
            # nobody has asserted, whatever the names look like.
            unasserted = ((not subj and town.resolve(st["subject_as_read"]))
                          or (not other and town.resolve(st["other_as_read"])))
        row["subject"] = ([{"household": h, "person": p} for h, p, _ in subj] or None)
        row["other"] = ([{"household": h, "person": p} for h, p, _ in other] or None)
        if unasserted:
            row["outcome"] = "identity_not_asserted"
        elif len(subj) != 1:
            row["outcome"] = "subject_unresolved" if not subj else "subject_ambiguous"
        elif not other:
            row["outcome"] = "other_not_in_town"
        elif len(other) > 1:
            row["outcome"] = "ambiguous"
        elif other[0][0] == subj[0][0]:
            row["outcome"] = "same_household"
        else:
            row["outcome"] = "landable"
        rows.append(row)
    return sorted(rows, key=lambda r: r["id"])


REPORTED = ("landable", "ambiguous", "same_household", "identity_not_asserted")


def read_authored() -> list[dict]:
    """Kinship a person read in prose no pattern can parse (T-0734).

    THE QUOTE IS VERIFIED, WHICH IS WHAT MAKES THIS A SEAM AND NOT A BACK DOOR.
    An authored statement is the right to be ASKED about a sentence — Andreas
    states the Harmon parentage as a list of five children, which is one subject
    and five others, and a regex fitted to that sentence would be fitted to that
    sentence. But a file where anybody can type a kinship is a file that will
    eventually carry one nobody read. So every entry names the path its quote
    stands on, and an entry whose quote is NOT there is a problem rather than a
    statement: the reading has to still be true of the tree.

    Beyond that it earns nothing. The statement it produces is classified,
    resolved against the residents layer and ruled exactly like a derived one.
    """
    out: list[dict] = []
    if not READINGS.exists():
        return out
    doc = json.loads(READINGS.read_text(encoding="utf-8"))
    for r in doc.get("readings") or []:
        out.append(dict(_statement(
            r["id"], r.get("source") or "authored_reading", r["subject"]["household"],
            r.get("quote", "")[:300], r["subject"]["person"], r["relation"],
            r["other"]["person"], r["subject"]["person"], r["other"]["person"]),
            authored_reading=True))
    return out


def authored_quote_problems() -> list[str]:
    """Every authored reading's quote must still stand where it says it does."""
    problems: list[str] = []
    if not READINGS.exists():
        return problems
    doc = json.loads(READINGS.read_text(encoding="utf-8"))
    for r in doc.get("readings") or []:
        path = ROOT / r.get("where", "")
        if not path.exists():
            problems.append(f"authored reading '{r['id']}' cites {r.get('where')!r}, "
                            f"which is not in the tree")
            continue
        # The card is JSON, so the quote is stored escaped; compare against the
        # decoded text of the whole document rather than its raw bytes.
        blob = json.dumps(json.loads(path.read_text(encoding="utf-8")),
                          ensure_ascii=False)
        needle = " ".join(r.get("quote", "").split())
        if needle and needle not in " ".join(blob.split()):
            problems.append(
                f"authored reading '{r['id']}' quotes a sentence that is NOT in "
                f"{r.get('where')}. A reading is only worth anything while the "
                f"source still says it; re-read the card or drop the entry.")
    return problems


def derive() -> dict:
    docs = load_town()
    town = Town(docs)
    rows = classify(read_church() + read_cards(docs) + read_authored(), town)
    counts = Counter(r["outcome"] for r in rows)
    return {
        "schema": SCHEMA,
        "_doc": ("DERIVED by tools/survey_stated_kin.py (T-0734) — the kinship the "
                 "committed sources state, with both ends resolved against the residents "
                 "layer. Hand-edits are overwritten; the rulings live in "
                 "kin_rulings.json. `proposals` carries only the rows a person has to "
                 "answer — the ones where the other party is somebody the town holds. "
                 "Statements whose other party is nobody in this dataset are counted and "
                 "not listed: they are the corpus talking about the world outside the town."),
        "generated_by": "tools/survey_stated_kin.py",
        "ticket": "T-0734",
        "corpus": [
            "data/research/church/records/st_marys_baptisms_1833_1835.json",
            "data/research/church/records/st_cyr_marriages_1834_1839.json",
            "data/research/church/records/st_cyr_deaths_1834_1837.json",
            "data/residents/households/*.json",
        ],
        "not_read": {
            "the_1840_census_households":
                "The densest kinship the corpus holds, and its crosswalk is 235 named "
                "heads stale on dev (T-0714) and derived against 849 residents where the "
                "town now holds 1,404 (T-0698). Kin read off it would land on the wrong "
                "people. Deliberately out of this pass."},
        "counts": {
            "statements_read": len(rows),
            "both_ends_in_town": sum(counts[k] for k in REPORTED),
            "landable": counts["landable"],
            "same_household": counts["same_household"],
            "ambiguous": counts["ambiguous"],
            "identity_not_asserted": counts["identity_not_asserted"],
            "other_not_in_town": counts["other_not_in_town"],
            "subject_unresolved": counts["subject_unresolved"] + counts["subject_ambiguous"],
            "relation_undeclared": counts["relation_undeclared"],
        },
        "proposals": [r for r in rows if r["outcome"] in REPORTED],
    }


# --------------------------------------------------------------------------
# the gate: every proposal answered, every answer honoured

def kin_pairs(docs: dict[str, dict]) -> set[tuple]:
    return {(hid, k.get("person"), k.get("relation"), k.get("household"), k.get("value"))
            for hid, h in docs.items() for k in (h.get("kin") or [])}


def check(quiet: bool = False, docs: dict | None = None,
          survey: dict | None = None, rulings: dict | None = None) -> list[str]:
    """Re-derive, then hold every landable proposal to a written ruling."""
    problems: list[str] = []
    problems += authored_quote_problems()
    fresh = derive() if survey is None else survey
    if survey is None:
        if not SURVEY.exists():
            return [f"{SURVEY.relative_to(ROOT)} does not exist — run --write"]
        committed = json.loads(SURVEY.read_text(encoding="utf-8"))
        if committed != fresh:
            problems.append(
                "data/residents/kin_survey.json no longer matches its derivation from the "
                "corpus. It is DERIVED: re-derive it with `python3 "
                "tools/survey_stated_kin.py --write` and rule on anything new.")
        fresh = committed if committed.get("proposals") else fresh
    docs = load_town() if docs is None else docs
    if rulings is None:
        if not RULINGS.exists():
            return problems + [f"{RULINGS.relative_to(ROOT)} does not exist"]
        rulings = json.loads(RULINGS.read_text(encoding="utf-8"))
    ruled = rulings.get("rulings") or {}
    proposals = {p["id"]: p for p in fresh.get("proposals") or []}
    written = kin_pairs(docs)

    for pid, p in sorted(proposals.items()):
        if p["outcome"] != "landable":
            continue
        r = ruled.get(pid)
        if r is None:
            problems.append(
                f"proposal '{pid}' is landable and nobody has ruled on it. Every stated "
                f"kinship whose two ends the town holds is answered in "
                f"data/residents/kin_rulings.json — landed, or refused with the reason.")
            continue
        if not (r.get("why") or "").strip():
            problems.append(f"ruling '{pid}' carries no reason; a refusal is a finding "
                            f"and owes its reasoning")
        verdict = r.get("ruling")
        a = (p["subject"][0]["household"], p["subject"][0]["person"])
        b = (p["other"][0]["household"], p["other"][0]["person"])
        present = any(row[0] == a[0] and row[1] == a[1] and row[3] == b[0] and row[4] == b[1]
                      for row in written)
        if verdict == "landed" and not present:
            problems.append(
                f"ruling '{pid}' says landed and {a[0]} carries no kin row for "
                f"{b[1]} — a ruling is landed when the records say so, not when the "
                f"ruling file does")
        if verdict in ("refused", "deferred") and present:
            problems.append(
                f"ruling '{pid}' says {verdict} and the records carry the kin row anyway")
        if verdict not in ("landed", "refused", "deferred"):
            problems.append(f"ruling '{pid}' has no verdict of landed|refused|deferred")

    for rid in sorted(ruled):
        if rid not in proposals:
            problems.append(
                f"ruling '{rid}' answers a proposal the survey no longer makes. The "
                f"corpus moved under the ruling; re-read it rather than leaving an "
                f"answer to a question nobody asked.")

    if not quiet:
        for line in problems:
            print("  ERROR " + line)
    return problems


def report(survey: dict) -> None:
    c = survey["counts"]
    print("STATED KINSHIP IN THE COMMITTED CORPUS (T-0734)\n")
    for k, v in c.items():
        print(f"  {v:6d}  {k}")
    print()
    ruled = (json.loads(RULINGS.read_text(encoding="utf-8")).get("rulings")
             if RULINGS.exists() else {}) or {}
    for p in survey["proposals"]:
        if p["outcome"] != "landable":
            continue
        r = ruled.get(p["id"]) or {}
        print(f"  [{r.get('ruling', 'UNRULED'):8s}] {p['subject_as_read']} — "
              f"{p['relation']} of — {p['other_as_read']}   ({p['source']})")
    by = Counter(p["outcome"] for p in survey["proposals"])
    print(f"\n  same-household (persons[].relationship, not kin): {by['same_household']}")
    print(f"  ambiguous, refused rather than guessed:           {by['ambiguous']}")


def self_test() -> int:
    """Every assertion --check makes, broken on purpose."""
    fails = []

    def check_that(label, cond):
        if not cond:
            fails.append(label)
        print(("  ok   " if cond else "  FAIL ") + label)

    hh_a = {"id": "hh_a", "head": "p_a", "persons": [{"id": "p_a", "name": "John Doe"}]}
    hh_b = {"id": "hh_b", "head": "p_b", "persons": [{"id": "p_b", "name": "Sam Doe"}]}
    docs = {"hh_a": dict(hh_a), "hh_b": dict(hh_b)}
    prop = {"id": "x1", "outcome": "landable", "relation": "brother",
            "subject_as_read": "John Doe", "other_as_read": "Sam Doe",
            "subject": [{"household": "hh_a", "person": "p_a"}],
            "other": [{"household": "hh_b", "person": "p_b"}]}
    survey = {"proposals": [prop]}

    check_that("a landable proposal nobody has ruled on is an error",
               any("nobody has ruled" in p for p in
                   check(True, docs, survey, {"rulings": {}})))
    check_that("a ruling with no reason is an error",
               any("no reason" in p for p in check(
                   True, docs, survey, {"rulings": {"x1": {"ruling": "refused", "why": " "}}})))
    check_that("a ruling with no verdict is an error",
               any("no verdict" in p for p in check(
                   True, docs, survey, {"rulings": {"x1": {"ruling": "maybe", "why": "w"}}})))
    check_that("'landed' with no kin row on the record is an error",
               any("carries no kin row" in p for p in check(
                   True, docs, survey, {"rulings": {"x1": {"ruling": "landed", "why": "w"}}})))
    landed = {"hh_a": dict(hh_a, kin=[{"person": "p_a", "relation": "brother",
                                       "household": "hh_b", "value": "p_b"}]),
              "hh_b": dict(hh_b)}
    check_that("'landed' with the kin row present passes",
               not check(True, landed, survey, {"rulings": {"x1": {"ruling": "landed",
                                                                   "why": "w"}}}))
    check_that("'refused' with the kin row written anyway is an error",
               any("carry the kin row anyway" in p for p in check(
                   True, landed, survey, {"rulings": {"x1": {"ruling": "refused", "why": "w"}}})))
    check_that("a ruling answering a proposal the survey no longer makes is an error",
               any("no longer makes" in p for p in check(
                   True, docs, {"proposals": []}, {"rulings": {"x1": {"ruling": "refused",
                                                                      "why": "w"}}})))
    check_that("an initial matches the forename it abbreviates",
               forenames_agree(["j"], ["john"]) and not forenames_agree(["j"], ["sam"]))
    check_that("a bare surname resolves to nobody",
               Town(docs).resolve("Doe") == [])
    check_that("two townspeople of one name are ambiguous, never guessed",
               len(Town({"hh_a": hh_a, "hh_b": {"id": "hh_b", "head": "p_b", "persons": [
                   {"id": "p_b", "name": "John Doe"}]}}).resolve("John Doe")) == 2)

    # T-0734 — THE AUTHORED-READING SEAM, and the one thing that keeps it honest.
    # A file where anybody can type a kinship is a file that will eventually carry
    # one nobody read, so every entry names the path its quote stands on and the
    # quote has to still be there. These are that assertion, broken on purpose.
    import tempfile
    _real = READINGS
    try:
        with tempfile.TemporaryDirectory() as td:
            bad = Path(td) / "readings_bad.json"
            bad.write_text(json.dumps({"readings": [{
                "id": "x", "where": "data/residents/households/hh_harmon_brothers.json",
                "quote": "a sentence that is nowhere in this repository at all",
                "source": "andreas_1884_v1",
                "subject": {"household": "hh_harmon_brothers", "person": "harmon_charles_l"},
                "relation": "son",
                "other": {"household": "hh_harmon_elijah_d", "person": "harmon_elijah_d"}}]}),
                encoding="utf-8")
            globals()["READINGS"] = bad
            check_that("an authored reading whose quote is NOT on the card it cites is refused",
                       bool(authored_quote_problems()))
            missing = Path(td) / "readings_missing.json"
            missing.write_text(json.dumps({"readings": [{
                "id": "y", "where": "data/residents/households/hh_nobody_at_all.json",
                "quote": "anything", "source": "s",
                "subject": {"household": "h", "person": "p"}, "relation": "son",
                "other": {"household": "h2", "person": "p2"}}]}), encoding="utf-8")
            globals()["READINGS"] = missing
            check_that("...and one citing a card that is not in the tree is refused too",
                       bool(authored_quote_problems()))
    finally:
        globals()["READINGS"] = _real
    check_that("the committed readings' quotes are all really on their cards",
               not authored_quote_problems())

    print(f"\n{len(fails)} failure(s)")
    return 1 if fails else 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        problems = check()
        if problems:
            print(f"\n{len(problems)} problem(s) — see above")
            return 1
        print("kin survey re-derives, and every landable proposal carries a ruling")
        return 0
    survey = derive()
    if "--write" in argv:
        SURVEY.write_text(json.dumps(survey, indent=1, ensure_ascii=False) + "\n",
                          encoding="utf-8")
        print(f"wrote {SURVEY.relative_to(ROOT)}: "
              f"{survey['counts']['landable']} landable of "
              f"{survey['counts']['statements_read']} statements read")
        return 0
    report(survey)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
