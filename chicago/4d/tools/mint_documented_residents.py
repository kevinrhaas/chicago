#!/usr/bin/env python3
"""The documented tradespeople the town never invented a roof for become residents (T-0376).

    python3 tools/mint_documented_residents.py           write
    python3 tools/mint_documented_residents.py --check   re-derive and diff
    python3 tools/mint_documented_residents.py --report  the mint and every refusal

WHAT THIS IS FOR.

`data/research/newspapers/register_1835.json` reads 2,201 people out of the Democrat
and the American and says, for each, what the committed town would have to do about
them. `replace_invented` is the finding that a trade the town INVENTED a household for
has a documented practitioner — T-0366 and T-0367 spend those. `new_resident` is the
rest: 1,967 documented people this reconstruction does not hold at all.

THIS PASS TAKES ONE SLICE OF THAT, AND THE SLICE IS DEFINED BY THE COMPILER RATHER
THAN BY TASTE. `tools/compile_register.py` gives a person `replace_invented` only when
the trade it reads for him is one the occupation census invented a household for, and
`new_resident` otherwise. So a `new_resident` WITH a trade is, by construction, a
tradesman the town has no roof to offer and never did: an attorney, an auctioneer, a
schoolteacher, a milliner, a hardware merchant. Nobody else's pass can reach him, and
this one cannot reach into theirs. The people with no trade at all are T-0373's; the
1,536 known only from the post office's letter lists are T-0374's.

THEY ARRIVE WITHOUT A ROOF, AND THAT IS THE HONEST ANSWER RATHER THAN A GAP.

Nothing reached says where any of these people slept. `data/town_census.json` already
counts 52 households whose `lives_at` names nothing, so this dataset has always been
able to hold a person the sources put in the town and nowhere in it. A household here
is a CONTAINER and not a claim: one person, no dwelling, no division, no family, and
every one of those absences written as `reconstructed` with "Not attested" in its own
note. The division vocabulary gains `unplaced` for exactly this, because writing
`south` because most of the town was south is the kind of quiet invention this project
exists not to make.

THE NINE REFUSALS, AND WHY EACH ONE IS THERE.

  1. `garbled`                — the transcription bracketed the name as uncertain.
  2. `a firm, not a person`   — 'Hamilton & Sons'. A firm cannot head a household; it
                                is a BUSINESS, and the businesses are T-0263's.
  3. `first evidence after the scene date` — AGENTS.md rule 3.
  4. `no surname the corpus prints`.
  5. `a surname, a trade, and nothing else` — data/residents/index.json already
                                records this decision, under `darwin_of_canada`: a
                                real Chicago resident the project declined to write
                                because "a person record whose only content is one
                                clause of somebody else's sentence inflates the
                                documented count without adding evidence". A printed
                                name with no forename and no initial is that case.
  6. `placed where this project cannot put him in the town` — the gazetteer gives him
                                a place, and the place is not the town, one of the
                                committed streets, or a committed structure. 'Mouth of
                                the St. Joseph' and 'Green Bay' are how the corpus
                                names people who were somewhere else; 'Cook county' is
                                how it names people who may never have been in the
                                town at all. A Chicago street does NOT refuse — this
                                pass claims no location, so a street in a man's own
                                record is not contradicted by a household that says
                                nothing about where he lived. T-0662 made it the
                                test the place vocabulary says it is: it is a test on
                                a READING, and a reading that names the town as well
                                as the other place is a Chicago appearance. So a
                                reading refuses only when NOTHING in it resolves
                                inside the town, and where the register folds several
                                printings onto one person, one printing that places
                                him here answers for all of them.
  7. `the town already names a <Surname>` — a committed resident, or one of the
                                index's researched-not-resident findings, carries that
                                family name. Deliberately blunt: a wrongly refused
                                candidate costs the town one documented resident, a
                                wrongly accepted one mints a second copy of a real man
                                or answers a question the project has already opened.
  9. `the identity master already holds this person on a committed card` — refusal 7
                                is a surname proxy and it is deliberately PARTIAL: it
                                skips the households minted by this pass and by every
                                pass below it, so a card one of those wrote is invisible
                                to it. `tools/identity_master_guard.py` asks the
                                cross-domain identity master instead, which resolves on
                                surname AND forename signature and can therefore look
                                into that blind spot without the bluntness. It refuses
                                only where the master's own M1/M2/M3 merge this name
                                onto a card; where the master refuses to choose between
                                rivals (R2/R3/R4) so does this, and the candidate is
                                minted. T-0843, the half of T-0839 that stops the next
                                duplicate rather than folding the last one.
  8. `surname already minted`  — one surname, one household, across the whole pass. A
                                shared surname reads as kinship and this pass claims
                                none; it is also how the same man under two printed
                                forms ('J. Bates' and 'Bates, J.') would take two.

WHY THE POOL READS `enrich` BACK.

The register is compiled FROM the committed town, so the moment this pass mints a man
the compiler stops calling him `new_resident` and starts calling him `enrich` — he is
in the town now, and it is right about that. Reading only `new_resident` would make
the pass unre-derivable the run after it lands. So an `enrich` whose target is one of
THIS pass's own person ids is read back into the pool as what it is: this pass's
previous answer.

WHAT THIS FILE WILL NOT DO. It will not invent an occupation, a dwelling, a division,
a sex or a family; it will not cite a claim the gazetteer does not carry; and it will
not upgrade a grade to make a record look better. The PERSON is `attested` — a source
names him and gives him his trade. Everything the household says about him beyond that
is written as unattested, because it is.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from rebuild_resident_index import rebuild  # noqa: E402  (the manifest's one owner)
from resident_mint_carry import carry_resident_mint  # noqa: E402  (T-1137)
from identity_master_guard import (  # noqa: E402  (T-0843; refusal 9)
    IdentityGuard, blind_person_ids, refusal as guard_refusal,
)

DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
STREETS = DATA / "streets" / "1835.json"
STRUCTURES = DATA / "structures"

SCENE_DATE = "1835-07-01"
PREFIX = "hh_doc_"
LETTER_LIST_PREFIX = "hh_ll_"   # tools/mint_letter_list_residents.py; see town_family_names
PERSON_PREFIX = "doc_"
DIVISION = "unplaced"

PAPERS = (("chicago_democrat_", "chicago_democrat_1833_1835"),
          ("chicago_american_", "chicago_american_1835"))

TITLES = {"dr", "mr", "mrs", "miss", "jr", "sr", "esq", "capt", "col", "maj",
          "rev", "messrs"}
FEMALE_TITLES = {"mrs", "miss"}
MALE_TITLES = {"mr"}
FIRM = re.compile(r"&| and |\bco\b|\bcompany\b", re.I)
UNCERTAIN = re.compile(r"\[|uncertain", re.I)
BARE_TOWN = {"chicago", "the town of chicago"}

MONTHS = ("January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc, indent=1):
    return json.dumps(doc, indent=indent, ensure_ascii=False) + "\n"


def words(name: str) -> list[str]:
    name = re.sub(r"\[[^\]]*\]", "", name or "").replace(".", " ").replace(",", " ")
    return [w for w in re.split(r"\s+", name.strip())
            if w and w.lower().strip("'") not in TITLES]


def titles_in(name: str) -> set[str]:
    raw = re.sub(r"\[[^\]]*\]", "", name or "").replace(".", " ").replace(",", " ")
    return {w.lower().strip("'") for w in re.split(r"\s+", raw.strip())} & TITLES


def surname(name: str) -> str:
    """The family name, lowercased, from either order the papers print it in."""
    parts = words(name)
    if not parts:
        return ""
    if "," in name:
        head = words(name.partition(",")[0])
        return (head[-1] if head else parts[0]).lower().strip("'")
    return parts[-1].lower().strip("'")


def display(name: str) -> str:
    """'Foot, S.' → 'S. Foot'. The papers print both orders; a card shows one.

    T-1121. A second comma inside the forename side — `Hugunin, Leonard, C.` —
    must not survive the reordering where it would LIE. Given-first is the one
    order a card shows and it says so by its order; a comma left standing in what
    the reordering made is read straight back as a surname-first mark, which is
    how the letter-list pass came to store `Leonard, C. Hugunin` and answer
    `leonard` for the family name. So the ordered string is compared with and
    without its commas, and they are dropped exactly where the answer moves. The
    same rule, and the same wording, as `display()` in
    mint_letter_list_residents.py — duplicated rather than imported, for the
    reason this file's own note gives for the other duplications.
    """
    if "," not in name:
        return name.strip()
    head, _, tail = name.partition(",")
    tail = tail.strip()
    shown = f"{tail} {head.strip()}".strip() if tail else head.strip()
    plain = re.sub(r"\s+", " ", shown.replace(",", " ")).strip()
    return plain if surname(shown) != surname(plain) else shown


def slug(name: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_",
                                     " ".join(words(name)).lower())).strip("_")


def plain_fragment(name: str) -> str:
    """surname_given..., the shape the hand-authored households already use.

    The naive `slug()` above just joins `words(name)` in whatever order the raw
    printed name happens to be in — surname-first for 'Hail, Aifred' but
    given-first for 'B. S. Morris', because that is the order the papers print
    them in. This is the shape a NEW household's id and person id take (T-0599):
    `surname()` already finds the family name from either printed order, so this
    drops that one token from `words(name)` wherever it fell and puts it first —
    `plain_fragment("B. S. Morris")` → `morris_b_s`.
    """
    fam = surname(name)
    given: list[str] = []
    dropped = False
    for w in words(name):
        if not dropped and w.lower().strip("'") == fam:
            dropped = True
            continue
        given.append(w)
    return slug(fam + " " + " ".join(given)) if given else slug(fam)


def issue_of(claim_id: str) -> str:
    """'chicago_democrat_1834_06_11#c003' → 'the Democrat of 11 June 1834, column 3'."""
    stem = claim_id.split("#")[0]
    col = claim_id.split("#")[1] if "#" in claim_id else ""
    m = re.search(r"(\d{4})_(\d{2})_(\d{2})$", stem)
    if not m:
        return claim_id
    y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
    paper = "the American" if "american" in stem else "the Democrat"
    tail = f", column {int(col[1:])}" if col.startswith("c") and col[1:].isdigit() else ""
    return f"{paper} of {d} {MONTHS[mo - 1]} {y}{tail}"


def paper_for(claim_ids) -> list[str]:
    out = []
    for cid in claim_ids:
        for prefix, sid in PAPERS:
            if cid.startswith(prefix) and sid not in out:
                out.append(sid)
    return out


def cited(mentions) -> str:
    head = "; ".join(issue_of(c) for c in mentions[:6])
    if len(mentions) <= 6:
        return head
    return f"{head}, and {len(mentions) - 6} further mention(s)"


# ---------------------------------------------------------------------------
# what the town already holds
# ---------------------------------------------------------------------------

def in_town_places() -> set[str]:
    """Every place name this project can resolve INSIDE the town it models.

    The committed streets under their 1835 names, every committed structure's own
    name, and the bare town. Derived, so a street record renamed or a building
    added moves this set with it rather than leaving a hand-typed list behind.
    """
    def norm(s):
        return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()

    places = set(BARE_TOWN)
    for street in load(STREETS)["streets"]:
        name = norm(street.get("name_1835"))
        if name:
            places.add(name)
            places.add(name.replace(" street", "").strip())
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load(path)
        for key in ("name",):
            if isinstance(doc.get(key), str) and norm(doc[key]):
                places.add(norm(doc[key]))
        for aka in doc.get("aka") or []:
            if isinstance(aka, str) and norm(aka):
                places.add(norm(aka))
    return places


# The minting passes run in a fixed ORDER, and `skip` below is what encodes it.
# Each pass must not read its OWN output back as "the town already names a
# <Surname>" — it would refuse on the second run every man it seated on the first
# and make `--check` pass against any tree at all. But it must not read a LATER
# pass's output either, and THAT is a precedence rule rather than the same rule
# twice: where two passes reach for one family name, the better-evidenced pass
# keeps it and the later one gives way.
#
# The order is documented (a trade the papers print) ▸ placed (a residency test
# over the corpus, T-0373) ▸ letter-list-only (a name on a list of uncalled-for
# letters, T-0378), best-evidenced first:
#
#   mint_documented_residents   skips hh_doc_, hh_placed_, hh_ll_ — sees none
#   mint_placed_residents       skips hh_placed_, hh_ll_         — sees hh_doc_
#   mint_letter_list_residents  skips hh_ll_                     — sees both
#
# So this derivation is unchanged by anything any of the three mints, which is
# what keeps all three re-derivable beside each other in any order.
MINTED_PREFIXES = ("hh_doc_", "hh_placed_", "hh_ll_")

# T-0599: a household minted from here on gets a PLAIN id (`plain_fragment`
# above), the shape the 73 hand-authored households already use, instead of one
# of the three prefixes above — the prefix read as a household's STATUS ("placed"
# sounds like a lot position; it names a residency test) when it was only ever
# meant to say which pass minted the record. `source_pass` carries that instead.
# The ~747 households already minted under a legacy prefix are UNCHANGED by this
# — see `household_id()` — and stay that way until a dedicated migration renames
# them (tracked separately; this file does not do it).
#
# `MINTED_PASSES` pairs each pass's own name (the `source_pass` value it writes
# on a freshly minted household) with the legacy prefix that marks a household
# minted by that pass BEFORE this field existed, in the same precedence order as
# `MINTED_PREFIXES` above. `minted_by()` is the union test — a household counts
# as this pass's whether it still carries the legacy prefix or the field.
# `("civic", "hh_civic_")` is the fourth pass (T-0514,
# tools/mint_civic_residents.py) and it is here for a reason its own docstring
# argues at length: it sits BESIDE the letter-list pass on a pool its refusal 5
# makes disjoint, not above it, so none of the three passes here should read its
# households as "the town already names a <Surname>". That test is a proxy for
# identity resolution over evidence that is a bare name, and the civic pass does
# not need the proxy — its identities come from the consolidation, which resolves
# on surname AND forename signature. Letting these three see it would retire
# hundreds of committed letter-list records on a surname collision alone, which is
# the opposite of the ruling of 2026-08-30.
MINTED_PASSES = (("documented", "hh_doc_"), ("placed", "hh_placed_"),
                 ("letter_list", "hh_ll_"), ("civic", "hh_civic_"))


def minted_by(path, doc: dict, pass_name: str, legacy_prefix: str) -> bool:
    """Was this household minted by the named pass — recognized either way."""
    return path.name.startswith(legacy_prefix) or doc.get("source_pass") == pass_name


def household_id(cand_name: str, prefix: str, pass_name: str, docs: dict,
                 taken_ids: set[str]) -> str:
    """The household id for a candidate: reuse whatever already exists for them —
    their legacy-prefixed id if this pass already minted them under one, or a
    plain id if a run after T-0599 already minted them under that — and mint a
    fresh plain one otherwise, disambiguated against every id already on disk or
    claimed earlier in this same run. This is what makes `record()` reproduce an
    EXISTING candidate's id byte-for-byte (so `--check` stays green on the ~747
    legacy households this pass has already minted) while a genuinely new
    candidate gets the new plain shape.
    """
    legacy_id = prefix + slug(cand_name)
    base_id = "hh_" + plain_fragment(cand_name)
    for hid in (legacy_id, base_id):
        path = HOUSEHOLDS / f"{hid}.json"
        if path in docs and minted_by(path, docs[path], pass_name, prefix):
            return hid
    candidate_id, n = base_id, 2
    while (HOUSEHOLDS / f"{candidate_id}.json") in docs or candidate_id in taken_ids:
        candidate_id = f"{base_id}_{n}"
        n += 1
    return candidate_id


def town_family_names(docs: dict, index: dict, skip=MINTED_PASSES) -> set[str]:
    """The family names the committed dataset already has something to say about.

    Read from the household records' own person names and from the index's
    researched-not-resident findings — minus the minted households named by
    `skip`, tested with `minted_by()` so a plain-named household minted after
    T-0599 is recognized the same as a legacy-prefixed one. See MINTED_PASSES
    above for why `skip` is an order and not a set.
    """
    known: set[str] = set()
    for path, doc in docs.items():
        if any(minted_by(path, doc, pass_name, prefix) for pass_name, prefix in skip):
            continue
        for person in doc.get("persons") or []:
            fam = surname(person.get("name") or "")
            if fam:
                known.add(fam)
    for entry in index.get("researched_not_resident") or []:
        fam = surname(entry.get("name") or "")
        if fam:
            known.add(fam)
    return known


# ---------------------------------------------------------------------------
# the mint
# ---------------------------------------------------------------------------

def fold_adjudicated(candidates: list[dict], gazetteer: dict) -> list[dict]:
    """One adjudicated person, one candidate — T-0662.

    The register does not only read names; it ADJUDICATES them. Two printings it has
    resolved onto the same person carry the same `action_target`, which is that
    person's committed id. This pass used to iterate the printings instead of the
    people, so `Grant, J., Jr.` (militia officer, 3 September 1834) and `James Grant`
    (attorney, La Salle Street, 10 June 1835) — one man by the register's own ruling —
    arrived as RIVALS for one surname, and refusal 8 threw the loser out as a duplicate
    of himself. Whichever printing sorted first took the household; the other's name
    and trade were lost. `hh_grant_james` became `hh_grant_j` and the town's attorney
    became a militia officer.

    So the group is folded before the refusals are applied: the evidence is the union
    of every printing's mentions, variants, trades and places, and the representative
    is the printing whose name the committed id is built from — the register's answer
    about who this is, not an artefact of the sort. Fifteen people in the pool are read
    from more than one printing; every one of them now carries all of it.

    The two transcription refusals are NOT folded past: a name the transcription
    bracketed as uncertain, or a firm, stays its own candidate and is refused as one.
    Folding it would launder an uncertain reading into a clean man's evidence.
    """
    groups: dict[str, list[dict]] = {}
    order: list = []
    for cand in candidates:
        target = str(cand.get("action_target") or "")
        if (cand.get("action") != "enrich" or not target
                or UNCERTAIN.search(cand["name"]) or FIRM.search(cand["name"])):
            order.append(cand)
            continue
        groups.setdefault(target, []).append(cand)
        if len(groups[target]) == 1:
            order.append(target)

    folded: list[dict] = []
    for item in order:
        if isinstance(item, dict):
            folded.append(item)
            continue
        rows = groups[item]
        if len(rows) == 1:
            folded.append(rows[0])
            continue
        # The register's own id for this person is what the card is filed under, so the
        # printing that re-derives it leads. Where several do (the papers print the same
        # name in both orders), the best-evidenced of them does, on the pass's own sort.
        named = [r for r in rows if plain_fragment(display(r["name"])) == item]
        rep = sorted(named or rows,
                     key=lambda r: (-len(gazetteer[r["id"]]["mentions"]),
                                    r["first_seen"], r["id"]))[0]
        merged = dict(rep)
        merged["first_seen"] = min(r["first_seen"] for r in rows)
        merged["last_seen"] = max(r["last_seen"] for r in rows)
        merged["folded_from"] = sorted(r["id"] for r in rows)
        gaz = dict(gazetteer[rep["id"]])
        for key in ("mentions", "occupations", "associated_places"):
            seen, out = set(), []
            for r in rows:
                for v in gazetteer[r["id"]].get(key) or []:
                    if v not in seen:
                        seen.add(v)
                        out.append(v)
            gaz[key] = out
        seen, variants = set(), []
        for r in rows:
            for v in gazetteer[r["id"]].get("variants") or []:
                mark = (v.get("as_printed"), v.get("claim"))
                if mark not in seen:
                    seen.add(mark)
                    variants.append(v)
        gaz["variants"] = variants
        # Refusal 6 is a test on a READING — "a reading that names only such places is
        # not a Chicago appearance" — so the union must not be allowed to make it
        # stricter than it was on the printings it folded. The postmaster Levi F.
        # Arnold, the sheriff Stephen Forbes and the justice Stephen M. Salisbury are
        # each printed once beside somewhere else (Plainfield, Cook County, the Dupage)
        # and elsewhere plainly in the town; folding their places into one list would
        # have withdrawn all three. The readings travel separately and the refusal
        # reads them one at a time.
        merged["place_readings"] = [list(gazetteer[r["id"]].get("associated_places") or [])
                                    for r in rows]
        gaz["first_seen"] = merged["first_seen"]
        gaz["last_seen"] = merged["last_seen"]
        gazetteer[rep["id"]] = gaz
        folded.append(merged)
    return folded


def mint(docs: dict, index: dict):
    """Choose who joins the town. Returns (accepted, refusals)."""
    register = load(REGISTER)
    gazetteer = {p["id"]: p for p in load(GAZETTEER)["persons"]}
    known = town_family_names(docs, index)
    in_town = in_town_places()
    # T-0843. The identity master, consulted with the same precedence this pass's
    # surname test already obeys: blind to its own output and to every pass below it.
    guard = IdentityGuard.load()
    blind = blind_person_ids(docs, lambda path, doc: any(
        minted_by(path, doc, pass_name, prefix) for pass_name, prefix in MINTED_PASSES))

    def norm(s):
        return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()

    # T-0599: a plain id no longer says whose previous answer it is on its own —
    # the legacy `doc_` prefix still does, for any household not yet migrated, but
    # a migrated one only says so in its own source_pass field.
    own_pass = {doc["head"] for doc in docs.values() if doc.get("source_pass") == "documented"}

    def is_own_prior_answer(target: str) -> bool:
        return target.startswith(PERSON_PREFIX) or target in own_pass

    # The pool, and its own previous answer read back (see the module docstring).
    candidates = [p for p in register["persons"]
                  if p.get("occupation") and not p.get("letter_list_only")
                  and (p.get("action") == "new_resident"
                       or (p.get("action") == "enrich"
                           and is_own_prior_answer(str(p.get("action_target") or ""))))]
    candidates = fold_adjudicated(candidates, gazetteer)
    candidates.sort(key=lambda p: (-len(gazetteer[p["id"]]["mentions"]),
                                   p["first_seen"], p["id"]))

    taken: set[str] = set()
    accepted, refusals = [], []
    for cand in candidates:
        gaz = gazetteer[cand["id"]]
        name = cand["name"]
        fam = surname(name)
        # T-0662, and the rule is the place vocabulary's own (T-1048 B2): "a reading
        # that names only such places is not a Chicago appearance". So a READING is
        # refused when NOTHING in it resolves inside the town, and a reading that
        # names the town, one of its streets or one of its structures answers for the
        # premises printed beside them — 'P. Cohen's store' on South Water Street in
        # Chicago is not evidence that L. W. Montgomery was somewhere else, and
        # refusing the shoemaker the papers print seven times against it was the whole
        # of why he left the town. And the reading is the unit: where the register
        # folds several printings onto one person, one printing that puts him in the
        # town answers for him, or the postmaster Levi F. Arnold (printed once beside
        # Plainfield), the sheriff Stephen Forbes (Cook County) and the justice
        # Stephen M. Salisbury (the Dupage) would each have gone with him.
        readings = cand.get("place_readings") or [gaz.get("associated_places") or []]
        beyond = [[p for p in reading if norm(p) not in in_town] for reading in readings
                  if reading and not any(norm(p) in in_town for p in reading)]
        outside = (sorted({p for b in beyond for p in b})
                   if beyond and len(beyond) == len(readings) else [])
        reason = None
        if UNCERTAIN.search(name):
            reason = "garbled"
        elif FIRM.search(name):
            reason = "a firm, not a person"
        elif cand["first_seen"] > SCENE_DATE:
            reason = "first evidence after the scene date"
        elif not fam:
            reason = "no surname the corpus prints"
        elif len(words(name)) < 2:
            reason = "a surname, a trade, and nothing else"
        elif outside:
            reason = ("placed where this project cannot put him in the town ("
                      + "; ".join(outside) + ")")
        elif fam in known:
            reason = f"the town already names a {fam.title()}"
        elif (hit := guard.holder(name, blind_to=blind)) is not None:
            reason = guard_refusal(hit)
        elif fam in taken:
            reason = "surname already minted"
        if reason:
            refusals.append((cand["occupation"], cand["id"], name, reason))
            continue
        taken.add(fam)
        accepted.append((cand, gaz))
    return accepted, refusals


# ---------------------------------------------------------------------------
# the records
# ---------------------------------------------------------------------------

def record(cand: dict, gaz: dict, docs: dict, taken_ids: set[str]) -> dict:
    name = display(cand["name"])
    fam = surname(cand["name"]).title()
    trade = cand["occupation"]
    trade_words = trade.replace("_", " ")
    sources = paper_for(gaz["mentions"])
    where = cited(gaz["mentions"])
    printed = sorted({v["as_printed"] for v in gaz.get("variants") or []})
    reads = ", ".join(gaz.get("occupations") or [trade_words])
    places = list(gaz.get("associated_places") or [])
    titles = titles_in(cand["name"])

    legacy_id = PREFIX + slug(cand["name"])
    hid = household_id(cand["name"], PREFIX, "documented", docs, taken_ids)
    pid = (PERSON_PREFIX + slug(cand["name"])) if hid == legacy_id else hid.removeprefix("hh_")

    person = {
        "id": pid,
        "name": name,
        "relationship": "head",
        "grade": "attested",
    }
    if titles & FEMALE_TITLES:
        person["sex"] = "female"
    elif titles & MALE_TITLES:
        person["sex"] = "male"
    person["occupation"] = {
        "value": trade,
        "confidence": "attested",
        "sources": list(sources),
        "note": (f"THE TRADE IS THE PAPER'S. The corpus reads it as {reads}, at "
                 f"{where}. The residents vocabulary's nearest period-correct word "
                 f"for it is `{trade}`, and where the corpus prints more than one "
                 f"trade they are all named here rather than reduced to the one the "
                 f"vocabulary could take."),
    }
    person["sources"] = list(sources)
    person["note"] = (
        f"A DOCUMENTED PERSON, AND NOTHING ELSE IS CLAIMED. The papers name "
        + " and ".join(f"'{p}'" for p in printed)
        + f" and give the trade; they do not say where this household lived, who "
        f"else was in it, or when it came. So the record around this person carries "
        f"nothing but the person: no dwelling, no division, no family, each written "
        f"as unattested in its own block rather than filled in from the shape of the "
        f"rest of the town. Cited at {where}. "
        + (f"The corpus associates the name with {', '.join(places)}; that is where "
           f"the paper does business with this person and not a statement about "
           f"where they slept, and the storefront tickets are the ones that may "
           f"stand a shop there. " if places else "")
        + f"THE TOWN NEVER INVENTED A ROOF FOR THIS TRADE. The occupation census "
        f"raised reconstructed households for the trades a town of 3,265 people "
        f"needed and could not document; `{trade}` was not one of them, which is "
        f"why this person could only ever be ADDED and never seated on an existing "
        f"record — data/research/newspapers/register_1835.json calls it "
        f"`new_resident` for exactly that reason. No figure is drawn "
        f"(docs/LIBERTIES.md L1). READ THROUGH A TRANSCRIPTION, not a scan: the "
        f"owner's ruling of 2026-08-28 grades a transcription-mediated reading as "
        f"documented, and the source record for the run states that standard and "
        f"its limits. A scan read that confirms or corrects the name upgrades this "
        f"entry."
    )

    present = "present" if cand["last_seen"] >= SCENE_DATE else "uncertain"
    doc = {
        "id": hid,
        "name": f"The {fam} household — a documented {trade_words}, unplaced in the town",
        "division": DIVISION,
        "head": pid,
    }
    if hid != legacy_id:
        # A genuinely new mint (T-0599): the plain id carries no pass of its own,
        # so the pass is recorded here instead. A household reusing its legacy id
        # does NOT gain this field retroactively — see household_id()'s docstring.
        doc["source_pass"] = "documented"
    doc.update({
        "arrival": {
            "value": cand["first_seen"],
            "confidence": "inferred",
            "sources": list(sources),
            "note": (f"A BOUND FROM THE PAPER, NOT AN ARRIVAL. The corpus first "
                     f"prints this person at {issue_of(gaz['mentions'][0])}, so they "
                     f"are in the town's paper by {cand['first_seen']} and at no "
                     f"stated time before it; nothing reached says when they came. "
                     f"Last printed {cand['last_seen']}."),
            "precision": "not_later_than",
        },
        "party_size_on_arrival": {
            "value": None, "confidence": "reconstructed", "note": "Not attested.",
        },
        "origin": {
            "value": None, "confidence": "reconstructed", "note": "Not attested.",
        },
        "reason_for_coming": {
            "value": None, "confidence": "reconstructed", "note": "Not attested.",
        },
        "lives_at": {
            "value": None, "confidence": "reconstructed",
            "note": ("Not attested. NOTHING IS BEING WITHHELD HERE: no source reached "
                     "says where this person lived, and 52 households in this dataset "
                     "were already in that position before this one was written."),
        },
        "works_at": {
            "value": None, "confidence": "reconstructed",
            "note": ("Not attested as a structure this project models. The trade is "
                     "documented; the premises are not one of the committed records."),
        },
        "present_on_scene_date": {
            "value": present,
            "confidence": "inferred",
            "sources": list(sources),
            "note": ((f"Printed on or after the scene date — last at "
                      f"{issue_of(gaz['mentions'][-1])} — so the corpus itself puts "
                      f"this person in the town's paper at {cand['last_seen']}.")
                     if present == "present" else
                     (f"THE CORPUS STOPS BEFORE THE SCENE DATE. Last printed "
                      f"{cand['last_seen']}, at {issue_of(gaz['mentions'][-1])}, and "
                      f"nothing reached either follows this person to 1 July 1835 or "
                      f"says they left. A documented resident whose whereabouts on "
                      f"one day are unknown is `uncertain` here rather than dropped: "
                      f"that is the same distinction index.json draws for Jeremiah "
                      f"Porter, and it is a finding rather than a gap.")),
        },
        "persons": [person],
        "touches_removal": False,
        "review_required": False,
        "research_note": (
            f"MINTED FROM THE NEWSPAPER REGISTER (T-0376), AND THE HOUSEHOLD IS A "
            f"CONTAINER RATHER THAN AN ARGUMENT. Every other record in this dataset "
            f"argues for a household — a family the sources count, or a trade the "
            f"town demonstrably needed. This one argues for a PERSON: the Democrat "
            f"and the American name {name} as a {trade_words} at Chicago "
            f"{len(gaz['mentions'])} time(s), and this reconstruction did not hold "
            f"them. `data/residents/` has no way to carry a person except inside a "
            f"household, so one was written around them and told to claim nothing: "
            f"one member, no dwelling, no division, no origin, no arrival beyond the "
            f"bound the paper sets. Reading a family, a house or a quarter of town "
            f"into this record would be reading something the papers do not say. "
            f"tools/mint_documented_residents.py derives the whole minted set and "
            f"prints every candidate it refused, with the reason."
        ),
    })
    return doc


def carry_over(doc: dict, existing: dict) -> dict:
    """Keep later passes' findings when this newspaper mint rebuilds its card."""
    # A title is this pass's evidence for ``sex``.  If the reading changes and the
    # title vanishes, an old derivation may not silently put that optional field back.
    return carry_resident_mint(doc, existing, owned_person_keys=("sex",))


def build(preload: dict | None = None):
    docs = ({p: json.loads(t) for p, t in preload.items() if p != INDEX}
            if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    index = (json.loads(preload[INDEX]) if preload is not None and INDEX in preload
             else load(INDEX))

    mine_paths = {p for p, doc in docs.items() if minted_by(p, doc, "documented", PREFIX)}
    accepted, refusals = mint(docs, index)

    files = {}
    seen: set[str] = set()
    for cand, gaz in accepted:
        doc = record(cand, gaz, docs, seen)
        existing = docs.get(HOUSEHOLDS / f"{doc['id']}.json") or {}
        carry_over(doc, existing)
        if doc["id"] in seen:
            raise SystemExit(f"two candidates mint the same household id {doc['id']}")
        seen.add(doc["id"])
        files[HOUSEHOLDS / f"{doc['id']}.json"] = dumps(doc, 1)

    # ONE OWNER FOR THE MANIFEST (T-0715). This pass used to mint its own rows and
    # keep every other row verbatim, so a household no pass owned could be regraded
    # elsewhere and go on carrying a stale row for ever. `final` is the whole layer
    # as this pass leaves it, and the derivation reads all of it.
    final = {path: doc for path, doc in docs.items() if path not in mine_paths}
    final.update({path: json.loads(text) for path, text in files.items()
                  if path != INDEX})
    rebuild(index, final)
    files[INDEX] = dumps(index, 1)
    return files, accepted, refusals, mine_paths


def report(accepted, refusals, docs: dict) -> None:
    print(f"MINTED — {len(accepted)} documented resident(s)")
    shown: set[str] = set()
    for cand, gaz in accepted:
        hid = household_id(cand["name"], PREFIX, "documented", docs, shown)
        shown.add(hid)
        print(f"  {hid:34s} {cand['occupation']:26s} "
              f"{display(cand['name'])[:24]:26s} ({len(gaz['mentions'])} mention(s), "
              f"{cand['first_seen']}..{cand['last_seen']})")
    print(f"\nREFUSED — {len(refusals)} candidate(s), with the reason")
    for trade, cid, name, reason in refusals:
        print(f"  {trade:26s} {name[:30]:32s} {reason}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and report any drift without writing")
    ap.add_argument("--report", action="store_true",
                    help="print the mint and every refusal")
    args = ap.parse_args()

    files, accepted, refusals, mine_paths = build()
    if args.report:
        docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
        report(accepted, refusals, docs)
        return 0
    if args.check:
        drift = [p for p, text in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        stale = [p for p in sorted(mine_paths) if p not in files]
        for p in drift + stale:
            print(f"   DRIFT: {p.relative_to(ROOT)}")
        if drift or stale:
            print(f"   {len(drift) + len(stale)} file(s) differ from what this pass "
                  f"derives")
            return 1
        print(f"   OK: {len(accepted)} documented resident(s) minted from the "
              f"register, {len(refusals)} candidate(s) refused")
        return 0

    for p in sorted(mine_paths):
        if p not in files:
            p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"minted {len(accepted)} documented resident(s); refused "
          f"{len(refusals)} candidate(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
