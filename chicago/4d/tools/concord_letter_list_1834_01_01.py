"""What each of the 170 printed lines of the 1 January 1834 return reaches (T-1010, out of T-1008).

    python3 tools/concord_letter_list_1834_01_01.py            write
    python3 tools/concord_letter_list_1834_01_01.py --check    re-derive and diff
    python3 tools/concord_letter_list_1834_01_01.py --report   the ledger, read out
    python3 tools/concord_letter_list_1834_01_01.py --self-test the assertions, broken

WHAT THIS IS FOR.

T-0424 read the ninth printing of the Chicago post office's 1 January 1834 return at
the page image and counted it: 170 printed lines, set down in printed order in
`data/research/newspapers/letter_list_1834_01_01_printed.json`. T-0310 minted a cohort
of residents out of the SAME return, a year of loop-runs earlier, from the
transcriptions of two of its nine impressions. Nobody had ever put the two beside each
other, so the project could say how long the list is and it could say who it minted,
and it could not say WHICH LINES THOSE PEOPLE ARE — nor, therefore, how many of the
170 reach no card at all.

That is the measurement this pass makes, and it makes it as a ledger with one row per
printed line. It MINTS NOBODY. Minting is a different decision from reading (T-0424's
own words) and a different decision again from counting, and the ticket that owns the
mint is the one this file's counts are for.

HOW A PRINTED LINE IS TIED TO A NAME THE PROJECT EXTRACTED, in four rules, strongest
first, each recorded on the row as `tied_by` so that a tie can be argued with:

  `image`     the extraction's own entity carries `read_at_image.printed_line`. That
              tie was made at the scan by T-0424 and is simply read back here.
  `text`      the entity's normalized name and the printed line agree exactly, once
              both are folded (case, punctuation, the trailing letter-count digit and
              any [bracketed] illegible glyph dropped). Unique matches only.
  `spelling`  the two surnames are within one edit of each other and the forenames do
              not contradict — one initial against the same initial, or a forename
              against nothing. Two settings of ONE return differ by exactly this much
              (`Hutchins`/`Huchins`, `Forster`/`Forrister`), and a rule narrower than
              this leaves those lines looking unread when they are merely respelt.
  untied      everything else, INCLUDING every ambiguity. A line two entities could
              equally be, or an entity two lines could equally be, is left untied and
              listed, because a concordance that guesses is worse than one that counts
              its own gaps.

WHAT A ROW SAYS THE LINE REACHES. The four outcomes are the four things that can have
happened to a name on this list, and the pass derives all four rather than asserting
any of them — `minted` and `refused` come out of `mint_letter_list_residents.py`'s own
`mint()`, through the refusals as that pass applies them, so this ledger cannot drift
from the pass it describes:

  `minted`        the letter-list pass minted a household for it, named here.
  `held_already`  the register ties the name to somebody the town ALREADY holds on
                  other evidence, so the line reaches a card that is not this cohort's.
                  A line that reaches Lewis Kercheval reaches Lewis Kercheval.
  `refused`       the name was in the mint's pool and a named refusal turned it away.
                  Not a gap: a ruling.
  `unread`        nothing the project has extracted from any of the nine impressions
                  carries this line. THIS is the gap the cohort's floor is made of.

THE THREE LINES THAT ARE NOT A PERSON are marked as what they are, from the roster's
own reading rather than from a rule here: `Axtel & Steele` and `Jesse B. Winn & Co.`
are firms, and `Lamira & Laura Carrier` names two people on one line. The printed
length is 170 LINES either way; what they are worth in PEOPLE is a different number,
and `counts.people_named` states it.

WHERE THE TWO READINGS OF A NAME DISAGREE, the row carries both (`printed_as` against
`extracted_as`) under `name_differs`, and where the line reached a card the card's own
spelling stands beside them. A corrected claim over an uncorrected card is worse than
neither (T-1008), and this is the list of the places where that could be true.

AND SINCE T-1139 EVERY ONE OF THOSE ROWS IS RULED ON.
`letter_list_1834_01_01_name_rulings.json` adjudicates each disagreement — the card takes
the image's reading, or it keeps its own and that file names the source outside this
return which outranks the image there — and this pass reads the rulings back onto the
rows. A row ruled ONTO THE IMAGE moves out of `name_differs` and into `name_ruled`: it is
a settled question and no longer one of the places a card may be wrong. The rows that
remain under `name_differs` are the ones where a card deliberately spells something the
ninth impression does not, which is exactly what a reader must go on seeing. An UNRULED
disagreement fails `--check`, so a row cannot appear here and go unweighed again.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import mint_letter_list_residents as mint_pass  # noqa: E402

DATA = ROOT / "data"
ROSTER = DATA / "research" / "newspapers" / "letter_list_1834_01_01_printed.json"
EXTRACTED = DATA / "research" / "newspapers" / "extracted"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
IDENTITY = DATA / "research" / "newspapers" / "identity.json"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
HOUSEHOLDS = DATA / "residents" / "households"
OUT = DATA / "research" / "newspapers" / "letter_list_1834_01_01_concordance.json"
NAME_RULINGS = DATA / "research" / "newspapers" / "letter_list_1834_01_01_name_rulings.json"

# The claims this project has extracted from the nine impressions of this one return.
# Two of the nine were extracted as name lists; the other seven were recorded as
# printings and carry no entities, which is why the return's names come from these.
CLAIMS = (
    ("chicago_democrat_1834_01_14", "c004"),
    ("chicago_democrat_1834_01_28", "c001"),
    ("chicago_democrat_1834_02_04", "c016"),
    ("chicago_democrat_1834_03_04", "c026"),
    ("chicago_democrat_1834_03_04", "c027"),
    # T-1011. The 54 lines the two crops lost to the advertisement set down the middle
    # of the column, lifted from T-0424's roster into the extraction of the impression
    # they were printed in. It is the SAME impression as c026 and c027 and a DIFFERENT
    # reading of it — the whole column at the scan, where those two are segmenter crops
    # — so it is tied as its own printing, which is what lets its entities take the
    # lines the crops could not offer a reading for.
    ("chicago_democrat_1834_03_04", "c033"),
)

# A bracket in either reading is the READER speaking, not the type. The two
# transcriptions and the image read use three of them and they do not mean the same
# thing: `[uncertain: Dagenet]` is a reading the transcriber would not vouch for,
# `Willi[a]m` is a letter supplied inside a word the type broke, and `[?]` / `[…]` is
# a glyph or a run nobody could carry at all. Folding all three to nothing — which is
# what a single blanket [^\]]* rule does — loses two names in three: `[uncertain:
# Dagenet]` folds to the empty string and line 47 then looks unread when the project
# has in fact read it. So the bracket is OPENED: its mark is dropped and whatever
# letters it holds are kept, without a space, so a letter supplied mid-word rejoins
# its word.
BRACKET = re.compile(r"\[(?:uncertain:\s*)?([^\]]*)\]")
UNREADABLE = str.maketrans("", "", "?…")


def load(path):
    return json.loads(pathlib.Path(path).read_text())


def dumps(doc, indent=1):
    return json.dumps(doc, indent=indent, ensure_ascii=False) + "\n"


def fold(name: str) -> str:
    """A printed name reduced to what two settings of it can be compared on.

    The trailing digit is the count of letters waiting and not part of the name; a
    bracket is opened rather than dropped (see BRACKET above); accents, case and
    punctuation go. `Rob't. Fisher` and `Robt Fisher` fold together, which is the
    point, and so do `[uncertain: Samuel] Stout` and `Samuel Stout`.
    """
    s = unicodedata.normalize("NFKD", name or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = BRACKET.sub(lambda m: m.group(1).translate(UNREADABLE).replace("...", ""), s)
    s = s.replace("‘", "").replace("’", "").replace("'", "")
    s = s.lower()
    s = re.sub(r"\d+", " ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(s.split())


def parts(name: str) -> tuple[str, list[str]]:
    """(surname, forename tokens) off a folded name, surname last as this list sets it."""
    toks = fold(name).split()
    if not toks:
        return "", []
    return toks[-1], toks[:-1]


def edits(a: str, b: str, ceiling: int = 1) -> int:
    """Levenshtein distance, stopped at `ceiling` + 1 because nothing here needs more."""
    if abs(len(a) - len(b)) > ceiling:
        return ceiling + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > ceiling:
            return ceiling + 1
        prev = cur
    return prev[-1]


def is_run_of(needle: list[str], hay: list[str]) -> bool:
    """Are `needle`'s words a contiguous run of `hay`'s, and more than a lone surname?

    Two words at least, so that a bare `Steele` does not tie itself to `Axtel &
    Steele` on the strength of the surname alone — that is refusal 5's distinction
    and it holds here too.
    """
    if len(needle) < 2 or len(needle) > len(hay):
        return False
    return any(hay[i:i + len(needle)] == needle
               for i in range(len(hay) - len(needle) + 1))


def forenames_agree(a: list[str], b: list[str]) -> bool:
    """Do two forename readings of one name fail to contradict each other?

    An initial matches the same initial and the forename it could abbreviate; a
    reading that prints no forename at all contradicts nothing. Anything else — two
    different initials, two different names — is a contradiction and refuses the tie.
    """
    if not a or not b:
        return True
    for x, y in zip(a, b):
        if x == y:
            continue
        if (len(x) == 1 or len(y) == 1) and x[0] == y[0]:
            continue
        return False
    return True


# ---------------------------------------------------------------------------
# the two sides of the concordance
# ---------------------------------------------------------------------------

def roster_lines(roster: dict) -> list[dict]:
    firms = set(roster["printed_length"]["addressee_lines_that_are_firms"])
    pairs = set(roster["printed_length"]["addressee_lines_naming_two_people"])
    rows = []
    for line in roster["lines"]:
        printed = line["as_printed"]
        kind = ("a firm, not a person" if printed in firms
                else "one line, two people" if printed in pairs
                else "a person")
        rows.append({"n": line["n"], "column": line["column"],
                     "as_printed": printed, "addressee": kind})
    return rows


def return_entities() -> list[dict]:
    """Every name this project has extracted from any impression of this return."""
    out = []
    for issue_id, claim_id in CLAIMS:
        path = EXTRACTED / f"{issue_id}.json"
        if not path.exists():
            continue
        doc = load(path)
        for claim in doc.get("claims", []):
            if claim.get("id") != claim_id:
                continue
            for ent in claim.get("entities", []):
                out.append({
                    "claim": f"{issue_id}#{claim_id}",
                    "as_printed": ent.get("as_printed"),
                    "normalized": ent.get("normalized") or ent.get("as_printed"),
                    "printed_line": (ent.get("read_at_image") or {}).get("printed_line"),
                })
    return out


def tie_one_printing(rows: list[dict], ents: list[dict], tied: dict[int, list[dict]],
                     ambiguities: list[dict]) -> list[dict]:
    """Tie ONE printing's entities to the printed lines, and return what stayed untied.

    A printing is a setting of the WHOLE return, so it offers at most one reading per
    line and the rules below may take each line once. They are run per printing rather
    than over the pooled names for exactly that reason: the ninth impression's
    `Kerchevel` and the fourth's `Kercheval` are two readings of line 96, and a pass
    that let the first take the line would then have to call the second a name no line
    carries.
    """
    by_n = {r["n"]: r for r in rows}
    taken: dict[int, dict] = {}
    noted: set[int] = set()

    # 1. the image's own ties (T-0424)
    rest = []
    for ent in ents:
        n = ent.get("printed_line")
        if n and n in by_n and n not in taken:
            taken[n] = dict(ent, tied_by="image")
        elif n and n in taken:
            ambiguities.append({"why": "two entities of one printing carry the same "
                                       "image tie", "line": n,
                                "entity": ent["normalized"]})
        else:
            rest.append(ent)

    def free():
        return [n for n in by_n if n not in taken]

    # 2. exact fold
    left = []
    for ent in rest:
        key = fold(ent["normalized"])
        hits = [n for n in free() if fold(by_n[n]["as_printed"]) == key] if key else []
        if len(hits) == 1:
            taken[hits[0]] = dict(ent, tied_by="text")
        else:
            if len(hits) > 1:
                noted.add(id(ent))
                ambiguities.append({"why": "one reading, more than one printed line",
                                    "entity": ent["normalized"],
                                    "lines": [by_n[n]["as_printed"] for n in hits]})
            left.append(ent)

    # 2b. a line that is not one person: one of its names, whole
    #
    # `Jesse B. Winn & Co.` and `Lamira & Laura Carrier` are ONE printed line each and
    # two of the readings name a part of one — `Jesse B. Winn`, with no `& Co.`. The
    # surname rule below cannot see it, because the last word of that line is `Co.`
    # and the last word of this one is `Winn`. So a line the roster says is not a
    # single person may also be tied by carrying a reading's words, in order, entire.
    left2 = []
    for ent in left:
        toks = fold(ent["normalized"]).split()
        hits = [n for n in free()
                if by_n[n]["addressee"] != "a person" and toks
                and is_run_of(toks, fold(by_n[n]["as_printed"]).split())]
        if len(hits) == 1:
            taken[hits[0]] = dict(ent, tied_by="part_of_a_line")
        else:
            if len(hits) > 1:
                noted.add(id(ent))
                ambiguities.append({"why": "one reading, more than one line it could "
                                           "be a part of", "entity": ent["normalized"],
                                    "lines": [by_n[n]["as_printed"] for n in hits]})
            left2.append(ent)
    left = left2

    # 3. one edit on the surname, forenames not contradicting
    untied = []
    for ent in left:
        fam, fore = parts(ent["normalized"])
        if not fam:
            untied.append(ent)
            continue
        hits = []
        for n in free():
            rfam, rfore = parts(by_n[n]["as_printed"])
            if rfam and edits(fam, rfam) <= 1 and forenames_agree(fore, rfore):
                hits.append(n)
        if len(hits) == 1:
            taken[hits[0]] = dict(ent, tied_by="spelling")
        else:
            if len(hits) > 1 and id(ent) not in noted:
                ambiguities.append({"why": "one reading, more than one printed line "
                                           "within a letter",
                                    "entity": ent["normalized"],
                                    "lines": [by_n[n]["as_printed"] for n in hits]})
            untied.append(ent)

    for n, ent in sorted(taken.items()):
        tied.setdefault(n, []).append(ent)
    return untied


def tie(rows: list[dict], ents: list[dict]) -> tuple[dict, list[dict], list[dict]]:
    """Tie every printing's entities to the printed lines, printing by printing.

    Returns (line n -> the readings tied to it, the entities no line carries, the
    ambiguities this pass declined to decide). Each rule refuses every ambiguity it
    meets rather than breaking it, because a concordance that guesses is worse than
    one that counts its own gaps.
    """
    tied: dict[int, list[dict]] = {}
    untied: list[dict] = []
    ambiguities: list[dict] = []
    seen_claims = []
    for claim in [e["claim"] for e in ents]:
        if claim not in seen_claims:
            seen_claims.append(claim)
    for claim in seen_claims:
        untied += tie_one_printing(
            rows, [e for e in ents if e["claim"] == claim], tied, ambiguities)
    return tied, untied, ambiguities


# ---------------------------------------------------------------------------
# what a tied line reaches
# ---------------------------------------------------------------------------

def mint_outcomes():
    """(person id -> minted household id, person id -> refusal), from the mint itself.

    Derived by calling `mint_letter_list_residents.mint()` rather than by reading its
    printed report, so the two cannot disagree. The household id is computed exactly
    as that pass's own `report` computes it, in the same order, because refusal 8 and
    the id allocator are both order-dependent.
    """
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    index = load(mint_pass.INDEX)
    accepted, refusals = mint_pass.mint(docs, index)
    minted, shown = {}, set()
    for cand, _gaz in accepted:
        hid = mint_pass.household_id(cand["name"], mint_pass.PREFIX, "letter_list",
                                     docs, shown)
        shown.add(hid)
        minted[cand["id"]] = hid
    refused = {cid: reason for cid, _name, _n, reason in refusals}
    return minted, refused


def variant_owner(gaz: dict) -> dict:
    """(claim, folded as_printed) -> gazetteer person id, over every variant it holds."""
    owner = {}
    for person in gaz["persons"]:
        for var in person.get("variants", []):
            owner[(var.get("claim"), fold(var.get("as_printed")))] = person["id"]
        for claim in person.get("mentions", []):
            owner.setdefault((claim, fold(person["name"])), person["id"])
    return owner


def identity_rulings(rows: list[dict]) -> dict[str, dict]:
    """Reading -> the ruling `identity.json` makes about it, for the untied readings.

    T-1011. The 1834-01-28 transcription carries readings no line of the ninth
    impression's 170 carries, and the tie rules above refuse every one of them: a
    concordance that guesses is worse than one that counts its gaps. But two
    impressions of ONE return print the same names, and once the whole printed column
    has been read at the image the only place left for such a reading to be is on one
    of those lines, set differently. That is an IDENTITY question, and `identity.json`
    is the only place it may be answered. This reads the answers back onto the rows so
    the ledger says which of its own gaps have since been ruled on, and which were
    ruled UNCLOSEABLE — a refusal is an answer and the more useful half of this map.
    """
    doc = load(IDENTITY)
    printed = {r["as_printed"] for r in rows}
    by_line = {r["as_printed"]: r["n"] for r in rows}
    out: dict[str, dict] = {}
    for rule in doc.get("merges", []):
        into, frm = rule.get("into"), rule.get("from")
        for reading, other in ((frm, into), (into, frm)):
            if reading and other and (other in printed) and (reading not in printed):
                out[reading] = {"ruling": "one person with printed line %d" % by_line[other],
                                "line": by_line[other], "held_as": into,
                                "ticket": rule.get("ticket")}
    for rule in doc.get("refused_merges", []):
        into, frm = rule.get("into"), rule.get("from")
        for reading, other in ((frm, into), (into, frm)):
            if reading and other and (other in printed) and (reading not in printed):
                out.setdefault(reading, {
                    "ruling": "refused: not joined to printed line %d" % by_line[other],
                    "line": by_line[other],
                    "refused_because": rule.get("refused_because"),
                })
    return out


def classify_untied(ent: dict, rows: list[dict], signed: str,
                    ruled: dict[str, dict] | None = None) -> dict:
    """An extracted name no printed line carries — and, where the pass can say so, why.

    Three of the four kinds are not gaps at all. The postmaster signed the return and
    the roster counts his name separately, so his line is not one of the 170. A
    reading whose surname IS on the list but whose forename contradicts every line
    carrying it is a name the concordance declined to tie rather than one it failed to
    find, and naming the lines it stood between is the whole use of the row: that is
    where a second reading of the scan would be worth making.
    """
    out = {"claim": ent["claim"], "as_printed": ent["as_printed"],
           "extracted_as": ent["normalized"]}
    ruling = (ruled or {}).get(ent["normalized"])
    if ruling:
        out["ruled_by_identity"] = ruling
    if signed and fold(ent["normalized"]) == fold(signed):
        out["why"] = ("the postmaster's signature under the list, which the roster "
                      "counts separately from its 170 addressee lines")
        return out
    fam, fore = parts(ent["normalized"])
    near = [r["as_printed"] for r in rows
            if fam and parts(r["as_printed"])[0]
            and edits(fam, parts(r["as_printed"])[0]) <= 1]
    if near:
        out["why"] = ("the list carries this surname and no line's forename agrees "
                      "with this reading of it")
        out["lines_carrying_the_surname"] = near
        if not fore:
            out["why"] = ("the list carries this surname on more than one line and "
                          "this reading has no forename to choose between them"
                          if len(near) > 1 else out["why"])
    else:
        out["why"] = ("no line of the printed list carries this surname at all, so "
                      "either the transcription read a name the ninth impression does "
                      "not set or the image read lost it")
    return out


def build() -> dict:
    roster = load(ROSTER)
    rows = roster_lines(roster)
    signed = re.sub(r",.*$", "", roster["return"].get("signed", "")).strip()
    ents = return_entities()
    tied, untied, ambiguities = tie(rows, ents)

    gaz = load(GAZETTEER)
    owner = variant_owner(gaz)
    by_person = {p["id"]: p for p in load(REGISTER)["persons"]}
    minted, refused = mint_outcomes()

    card_names, card_by_household = {}, {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = load(path)
        for person in doc.get("persons", []):
            card_names[person["id"]] = (doc["id"], person["name"])
            if person.get("relationship") == "head":
                card_by_household[doc["id"]] = person["name"]

    RANK = {"minted": 0, "held_already": 1, "refused": 2, "unresolved": 3}

    def outcome_for(ent: dict) -> dict:
        pid = owner.get((ent["claim"], fold(ent["as_printed"])))
        if pid is None:
            pid = owner.get((ent["claim"], fold(ent["normalized"])))
        reg = by_person.get(pid) if pid else None
        if pid and pid in minted:
            hid = minted[pid]
            return {"kind": "minted", "person": pid, "household": hid,
                    "card_name": card_by_household.get(hid),
                    "by": "tools/mint_letter_list_residents.py"}
        if pid and pid in refused:
            return {"kind": "refused", "person": pid, "reason": refused[pid],
                    "by": "tools/mint_letter_list_residents.py"}
        if reg and reg.get("action") in ("enrich", "replace_invented"):
            target = reg.get("action_target")
            hid, held = card_names.get(target, (None, None))
            return {"kind": "held_already", "person": pid, "resident": target,
                    "household": hid, "card_name": held, "action": reg["action"]}
        return {"kind": "unresolved", "person": pid,
                "why": "the extraction carries this line but the compiled register "
                       "does not resolve the reading to a person, so nothing "
                       "downstream of it reaches a card either"}

    ruling_by_line = {}
    if NAME_RULINGS.exists():
        for r in load(NAME_RULINGS)["rulings"]:
            ruling_by_line[r["n"]] = r

    def rule_for(differ: dict) -> dict:
        """The T-1139 adjudication of this line, read back onto the row."""
        r = ruling_by_line.get(differ["n"])
        if not r:
            return differ
        differ["ruled"] = {"ticket": "T-1139", "rule": r["rule"], "takes": r["takes"],
                           "because": r["because"]}
        if r.get("card"):
            differ["ruled"]["card"] = r["card"]
        return differ

    lines, name_differs, name_ruled = [], [], []
    for row in rows:
        readings = tied.get(row["n"]) or []
        out = dict(row)
        if not readings:
            out["tie"] = None
            out["reaches"] = {
                "kind": "unread",
                "why": "no claim this project has extracted from any of the nine "
                       "impressions of this return carries this line",
            }
            lines.append(out)
            continue

        out["tie"] = [{"tied_by": e["tied_by"], "claim": e["claim"],
                       "as_printed_in_that_printing": e["as_printed"],
                       "extracted_as": e["normalized"]} for e in readings]
        outcomes = [outcome_for(e) for e in readings]
        best = min(outcomes, key=lambda o: RANK[o["kind"]])
        out["reaches"] = best
        others = [o for o in outcomes
                  if o.get("person") and o["person"] != best.get("person")]
        if others:
            # Two impressions of one line resolving to two people is a finding, not a
            # tidy-up: the compiler made two persons out of one addressee.
            out["reaches"] = dict(best, also_resolved_to=sorted(
                {o["person"] for o in others}))

        printed_fold = fold(row["as_printed"])
        disagree = [e for e in readings if fold(e["normalized"]) != printed_fold]
        bracketed = [e for e in readings
                     if fold(e["normalized"]) == printed_fold
                     and BRACKET.search(e["normalized"] or "")
                     and not BRACKET.search(row["as_printed"])]
        def follows(card: str | None, others: list[dict]) -> str:
            """Which of the two readings of this line the committed card spells."""
            if fold(card or "") == printed_fold:
                return "the page image"
            if fold(card or "") in {fold(e["normalized"]) for e in others}:
                return "the transcription"
            return "neither"

        if bracketed and not disagree:
            card = out["reaches"].get("card_name")
            differ = {
                "n": row["n"], "printed_as": row["as_printed"],
                "extracted_as": [e["normalized"] for e in bracketed],
                "tied_by": [e["tied_by"] for e in bracketed],
                "reaches": out["reaches"]["kind"],
                "kind": "the transcription bracketed what the image reads",
            }
            if card:
                differ["card_name"] = card
                differ["card_follows"] = follows(card, bracketed)
            out["name_differs"] = True
            (name_ruled if rule_for(differ).get("ruled", {}).get("takes")
             == "the page image" else name_differs).append(differ)
        if disagree:
            card = out["reaches"].get("card_name")
            differ = {"n": row["n"], "printed_as": row["as_printed"],
                      "extracted_as": [e["normalized"] for e in disagree],
                      "tied_by": [e["tied_by"] for e in disagree],
                      "reaches": out["reaches"]["kind"],
                      "kind": "the two readings disagree in their letters"}
            if card:
                differ["card_name"] = card
                differ["card_follows"] = follows(card, disagree)
            out["name_differs"] = True
            (name_ruled if rule_for(differ).get("ruled", {}).get("takes")
             == "the page image" else name_differs).append(differ)
        lines.append(out)

    tally: dict[str, int] = {}
    for line in lines:
        tally[line["reaches"]["kind"]] = tally.get(line["reaches"]["kind"], 0) + 1
    refusal_tally: dict[str, int] = {}
    for line in lines:
        if line["reaches"]["kind"] == "refused":
            key = mint_pass.reason_key(line["reaches"]["reason"])
            refusal_tally[key] = refusal_tally.get(key, 0) + 1

    ruled = identity_rulings(rows)
    untied_rows = [classify_untied(e, rows, signed, ruled) for e in untied]
    untied_tally: dict[str, int] = {}
    for u in untied_rows:
        untied_tally[u["why"]] = untied_tally.get(u["why"], 0) + 1

    firms = sum(1 for r in lines if r["addressee"] == "a firm, not a person")
    pairs = sum(1 for r in lines if r["addressee"] == "one line, two people")

    return {
        "schema": 1,
        "generated_by": "tools/concord_letter_list_1834_01_01.py",
        "_doc": __doc__.strip(),
        "return": {"office": roster["return"]["office"],
                   "remaining_as_of": roster["return"]["remaining_as_of"],
                   "printings": 9,
                   "roster": "data/research/newspapers/letter_list_1834_01_01_printed.json",
                   "roster_read_by": "T-0424, at the page image of the ninth printing"},
        "claims_read": [f"{i}#{c}" for i, c in CLAIMS],
        "counts": {
            "printed_lines": roster["printed_length"]["lines"],
            "people_named": roster["printed_length"]["lines"] - firms + pairs,
            "firm_lines": firms,
            "lines_naming_two_people": pairs,
            "tied_to_an_extracted_name": sum(1 for r in lines if r["tie"]),
            "readings_tied": sum(len(r["tie"]) for r in lines if r["tie"]),
            "tied_by": {
                rule: sum(1 for r in lines if r["tie"]
                          for t in r["tie"] if t["tied_by"] == rule)
                for rule in ("image", "text", "part_of_a_line", "spelling")
            },
            "reaches": tally,
            "reaches_a_card": tally.get("minted", 0) + tally.get("held_already", 0),
            "refused_by_reason": refusal_tally,
            "readings_that_disagree": len(name_differs),
            "readings_ruled_onto_the_page_image": len(name_ruled),
            "readings_unruled": sum(
                1 for d in name_differs + name_ruled if "ruled" not in d),
            "extracted_names_no_line_carries": len(untied),
            "extracted_names_no_line_carries_by_why": untied_tally,
            "extracted_names_ruled_on_in_identity_json": sum(
                1 for u in untied_rows if u.get("ruled_by_identity")),
        },
        "lines": lines,
        "name_differs": name_differs,
        "name_ruled": name_ruled,
        "extracted_names_no_line_carries": [
            classify_untied(e, rows, signed, ruled)
            for e in sorted(untied, key=lambda e: (e["claim"], e["normalized"] or ""))
        ],
        "ambiguities_this_pass_declined_to_decide": ambiguities,
    }


# ---------------------------------------------------------------------------
# the modes
# ---------------------------------------------------------------------------

def report(doc: dict) -> None:
    c = doc["counts"]
    print(f"THE 1 JANUARY 1834 RETURN — {c['printed_lines']} printed lines, "
          f"{c['people_named']} people named")
    print(f"  tied to an extracted name   {c['tied_to_an_extracted_name']:4d}  "
          f"({', '.join(f'{k} {v}' for k, v in c['tied_by'].items())})")
    for kind, n in sorted(c["reaches"].items(), key=lambda kv: -kv[1]):
        print(f"  {kind:26s}  {n:4d}")
    print(f"  REACHES A CARD              {c['reaches_a_card']:4d}")
    if c["refused_by_reason"]:
        print("\n  the refusals, as the mint applies them")
        for reason, n in sorted(c["refused_by_reason"].items(), key=lambda kv: -kv[1]):
            print(f"    {n:4d}  {reason}")
    print(f"\n  readings ruled onto the image {c.get('readings_ruled_onto_the_page_image', 0):3d}"
          f"  (T-1139)")
    for d in doc.get("name_ruled", []):
        r = d.get("ruled", {})
        card = (f"  card: {r['card']['displayed_name_was']} -> "
                f"{r['card']['displayed_name_is']}"
                if (r.get("card") or {}).get("displayed_name_is") else "")
        print(f"    line {d['n']:3d}  {r.get('rule')}  {d['printed_as']!r}"
              f"  over {', '.join(repr(x) for x in d['extracted_as'])}{card}")
    print(f"\n  readings that disagree      {c['readings_that_disagree']:4d}"
          f"  (still, after the rulings)")
    for d in doc["name_differs"]:
        card = f"  card: {d['card_name']} ({d['card_follows']})" if d.get("card_name") else ""
        print(f"    line {d['n']:3d}  printed {d['printed_as']!r}  "
              f"extracted {', '.join(repr(x) for x in d['extracted_as'])}{card}"
              f"\n              {d['kind']}")
    print(f"\n  extracted names no line carries "
          f"{c['extracted_names_no_line_carries']:4d}"
          f"  ({c.get('extracted_names_ruled_on_in_identity_json', 0)} since ruled on "
          f"in identity.json)")
    for e in doc["extracted_names_no_line_carries"]:
        print(f"    {e['extracted_as']!r}  ({e['claim']})\n        {e['why']}")
        if e.get("ruled_by_identity"):
            print(f"        RULED: {e['ruled_by_identity']['ruling']}")
    print("\n  UNREAD — the lines that reach nothing")
    for line in doc["lines"]:
        if line["reaches"]["kind"] == "unread":
            print(f"    line {line['n']:3d}  {line['as_printed']}")


def self_test() -> int:
    """The assertions this pass rests on, each broken on purpose."""
    bad = 0

    def want(label, got, expect):
        nonlocal bad
        if got != expect:
            print(f"  FAIL {label}: {got!r} != {expect!r}")
            bad += 1

    want("fold drops the letter count", fold("Eliphalet Atkins 2"), "eliphalet atkins")
    want("fold drops an illegible glyph", fold("[?] Blodget"), "blodget")
    want("fold opens an uncertain reading", fold("[uncertain: Dagenet]"), "dagenet")
    want("fold rejoins a letter supplied mid-word", fold("Willi[a]m Crisey"),
         "william crisey")
    want("fold drops a run nobody could carry", fold("Benj. Cl[…]"), "benj cl")
    want("fold joins an apostrophe", fold("Rob't. Fisher"), "robt fisher")
    want("one edit", edits("hutchins", "huchins"), 1)
    want("two edits are refused at the ceiling", edits("forster", "forrister") <= 1, False)
    want("an initial does not contradict its forename",
         forenames_agree(["w"], ["william"]), True)
    want("two different initials contradict", forenames_agree(["w"], ["j"]), False)
    want("no forename contradicts nothing", forenames_agree([], ["william"]), True)
    want("surname last", parts("Wm. G. Austin"), ("austin", ["wm", "g"]))

    # the tie rules, on a made-up roster, each rule reached in turn
    rows = [{"n": 1, "column": "left", "as_printed": "Wm. G. Austin", "addressee": "a person"},
            {"n": 2, "column": "left", "as_printed": "Nathan Huchins", "addressee": "a person"},
            {"n": 3, "column": "left", "as_printed": "Levi Hills 2", "addressee": "a person"},
            {"n": 4, "column": "left", "as_printed": "Aaron Friend", "addressee": "a person"}]
    ents = [{"claim": "x#c1", "as_printed": "Austin", "normalized": "Wm. G. Austin",
             "printed_line": 1},
            {"claim": "x#c1", "as_printed": "Levi Hills", "normalized": "Levi Hills",
             "printed_line": None},
            {"claim": "x#c1", "as_printed": "Nathan Hutchins",
             "normalized": "Nathan Hutchins", "printed_line": None},
            {"claim": "x#c1", "as_printed": "Zoroaster Quill",
             "normalized": "Zoroaster Quill", "printed_line": None}]
    tied, untied, _amb = tie(rows, ents)
    want("the image tie wins", tied[1][0]["tied_by"], "image")
    want("the text tie folds the count", tied[3][0]["tied_by"], "text")
    want("the spelling tie crosses one letter", tied[2][0]["tied_by"], "spelling")
    want("a name no line carries stays untied", [e["normalized"] for e in untied],
         ["Zoroaster Quill"])
    want("…and is classified as a surname the list does not carry",
         classify_untied(untied[0], rows, "JOHN S. C. HOGAN, P. M.")["why"][:11],
         "no line of ")
    want("the postmaster is not a gap",
         classify_untied({"claim": "x#c1", "as_printed": "J. S. C. Hogan",
                          "normalized": "John S. C. Hogan"}, rows,
                         "JOHN S. C. HOGAN")["why"][:16],
         "the postmaster's")
    want("a contradicted forename names the lines it stood between",
         classify_untied({"claim": "x#c1", "as_printed": "Zeb Austin",
                          "normalized": "Zeb Austin"}, rows,
                         "")["lines_carrying_the_surname"],
         ["Wm. G. Austin"])
    want("a line no name reaches stays untied", 4 in tied, False)
    want("a bare surname is not a run of a firm line",
         is_run_of(["steele"], ["axtel", "steele"]), False)
    want("a whole name is", is_run_of(["jesse", "b", "winn"],
                                      ["jesse", "b", "winn", "co"]), True)

    # a firm line is tied by the reading that names the person inside it
    rows_firm = [{"n": 1, "column": "right", "as_printed": "Jesse B. Winn & Co.",
                  "addressee": "a firm, not a person"}]
    tied_firm, untied_firm, _af = tie(
        rows_firm, [{"claim": "x#c1", "as_printed": "Jesse B. Winn",
                     "normalized": "Jesse B. Winn", "printed_line": None}])
    want("the firm line is tied by its own name",
         tied_firm[1][0]["tied_by"], "part_of_a_line")
    want("…and nothing is left over", untied_firm, [])

    # two printings of one return each offer a reading of the same line, and both are
    # tied to it — the rule that makes the concordance many-to-one
    ents_two = ents + [{"claim": "x#c2", "as_printed": "Wm G Austin",
                        "normalized": "Wm. G. Austin", "printed_line": None},
                       {"claim": "x#c2", "as_printed": "Nathan Huchins",
                        "normalized": "Nathan Huchins", "printed_line": None}]
    tied3, untied3, _a3 = tie(rows, ents_two)
    want("the second printing joins the same line", len(tied3[1]), 2)
    want("…by text where the image tied the first",
         [t["tied_by"] for t in tied3[1]], ["image", "text"])
    want("…and is not counted as a name no line carries",
         sorted(e["normalized"] for e in untied3), ["Zoroaster Quill"])

    # an ambiguity is refused rather than broken
    rows2 = [{"n": 1, "column": "left", "as_printed": "H. S. Steele 2",
              "addressee": "a person"},
             {"n": 2, "column": "left", "as_printed": "H. S. Steele",
              "addressee": "a person"}]
    ents2 = [{"claim": "x#c1", "as_printed": "H. S. Steele",
              "normalized": "H. S. Steele", "printed_line": None}]
    tied2, untied2, amb2 = tie(rows2, ents2)
    want("two lines one reading ties neither", tied2, {})
    want("…and the reading is listed as untied", len(untied2), 1)
    want("…and the ambiguity is written down", len(amb2), 1)

    # T-1139. The rulings are read back onto the rows, and the partition they drive is
    # the whole use of them: a row ruled onto the image is settled and leaves
    # `name_differs`, a row whose card keeps its own spelling stays there to be seen.
    # Broken here by withholding a ruling, which is the shape a new roster line would
    # arrive in.
    doc = build()
    ruled, differs = doc["name_ruled"], doc["name_differs"]
    want("every disagreement carries a ruling",
         [d["n"] for d in ruled + differs if "ruled" not in d], [])
    want("…and the unruled count says so", doc["counts"]["readings_unruled"], 0)
    want("a row ruled onto the image leaves name_differs",
         sorted({d.get("ruled", {}).get("takes") for d in ruled}), ["the page image"])
    want("…and the rows that stay are the ones ruled otherwise",
         sorted(d.get("ruled", {}).get("takes") or "UNRULED" for d in differs),
         ["neither — the line names a firm and the card names the man in it",
          "the card's held spelling", "the card's held spelling"])
    want("a rename carries the id unchanged",
         sorted(d["ruled"]["card"]["person"] for d in ruled
                if (d.get("ruled", {}).get("card") or {}).get("id_unchanged")),
         ["fraser_wm_h", "provis_joshua", "vandino_john"])

    print("FAIL" if bad else "OK — the concordance's own assertions hold")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff against the committed ledger")
    ap.add_argument("--report", action="store_true", help="read the ledger out")
    ap.add_argument("--self-test", action="store_true",
                    help="the tie rules, broken on purpose")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    doc = build()
    if args.report:
        report(doc)
        return 0
    if args.check:
        if not OUT.exists():
            print(f"FAIL {OUT.relative_to(ROOT)} is not committed")
            return 1
        if OUT.read_text() != dumps(doc):
            print(f"FAIL {OUT.relative_to(ROOT)} no longer re-derives from the roster, "
                  f"the extractions and the mint — re-run "
                  f"`python3 tools/concord_letter_list_1834_01_01.py`")
            return 1
        c = doc["counts"]
        # T-1139. A disagreement that nothing has weighed is the defect this ledger was
        # built to make visible, so it may not sit here silently once the rulings exist.
        if c.get("readings_unruled"):
            unruled = [d["n"] for d in doc["name_differs"] + doc.get("name_ruled", [])
                       if "ruled" not in d]
            print(f"FAIL {c['readings_unruled']} reading(s) disagree and are not ruled on "
                  f"in {NAME_RULINGS.relative_to(ROOT)} — line(s) "
                  f"{', '.join(str(n) for n in unruled)}. T-1139's acceptance is that "
                  f"none is left silent")
            return 1
        print(f"OK  {c['printed_lines']} printed lines, {c['reaches_a_card']} reaching "
              f"a card, {c['reaches'].get('unread', 0)} unread, "
              f"{c.get('readings_ruled_onto_the_page_image', 0)} readings ruled onto the "
              f"image and {c['readings_that_disagree']} still disagreeing")
        return 0

    OUT.write_text(dumps(doc))
    print(f"wrote {OUT.relative_to(ROOT)}")
    report(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
