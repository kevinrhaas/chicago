#!/usr/bin/env python3
"""The documented people the papers NAME but give no trade, and the town does not hold (T-0373).

    python3 tools/mint_placed_residents.py           write
    python3 tools/mint_placed_residents.py --check   re-derive and diff
    python3 tools/mint_placed_residents.py --report  the mint and every refusal

WHAT THIS IS FOR, AND WHY IT IS A DIFFERENT PASS FROM T-0376's.

`tools/mint_documented_residents.py` takes the register's `new_resident` people who
carry a TRADE: the paper prints what they did, and the trade is the anchor that puts
them in the town. This pass takes the rest of the non-letter-list half — 392 people
today whom the corpus names in a proceedings column, a public card, a shipping notice
or an advertisement and for whom `data/research/newspapers/register_1835.json` reads
no occupation at all. (The 1,536 known only from the post office's letter lists are
T-0374's, and are excluded here by the register's own `letter_list_only` flag.)

THE HARD PART IS NOT THE MINTING, IT IS THE RESIDENCY TEST, so it is stated first.

A name printed in a Chicago paper is not a Chicago resident. T-0376's refusals already
showed what this pool is full of: 'A. A. Barber' is one of sixty-three signatures on a
card thanking a steamboat captain for a trip from Buffalo, and the only place the
corpus gives him is Green Bay. With no trade to argue from, the test has to be built
out of what the corpus itself says about PLACE and about COMPANY, and it has to be
derived rather than judged — a hand-picked list of the people who "look like"
residents is exactly the invention this project exists not to make.

  A NOTE ON THE WORD "PLACED", because it reads as a lot/plat position and is not
  one. Every household this pass mints carries `"division": "unplaced"` — nobody
  here has been placed on a parcel. "Placed" names PART ONE below: a residency
  EVIDENCE test (does the corpus put this person inside the town, as opposed to
  outside it), not a location. Before T-0599 that test's name doubled as this
  pass's filename prefix (`hh_placed_`); a household minted from here on gets a
  plain `hh_<surname>_<given>` id instead, with `source_pass: "placed"` recording
  which test it passed — see `household_id()` / `minted_by()` below.

  PART ONE — PLACEMENT. The corpus must put the person inside the town and nowhere
  outside it. `associated_places` is resolved against the committed dataset:
  `in_town_places()` (shared with T-0376's pass) is the bare town, every committed
  1835 street name, and every committed structure's name and aka, so a street record
  renamed or a building added moves the test with it.
    · any place outside that set REFUSES — 'Green Bay', 'Detroit', 'Cook county',
      'Naper's Settlement'. This is how the corpus names somebody who was somewhere
      else, and it outranks any placement in the town: a man the paper puts in two
      places has not told us where he lived.
    · NO place at all REFUSES. The corpus is silent about where he was, there is no
      trade to anchor him, and a printed name on its own is not evidence of residence.
      37 of the pool are refused here and they are refused honestly rather than swept
      in on the strength of having appeared in a Chicago newspaper.

  PART TWO — CORROBORATION, because a bare 'Chicago' is weak. The gazetteer records
  'Chicago' when the corpus says a person did something AT Chicago, which is a
  different claim from living there — a bride married at Chicago, a Secretary of War
  received at Chicago. So a bare-town placement needs a SECOND witness, and the corpus
  offers exactly three that can be derived:
    (a) a placement at street or structure level — the corpus gives an address inside
        the modelled town, which no visitor passing through acquires;
    (b) print in two or more separate ISSUES — a transient is printed once and is gone;
        the town's own people recur across the run;
    (c) print in the same claim as TWO OR MORE people this reconstruction already
        holds. The register says who those are: its `enrich` action is the finding
        that a person in the papers is a person already in `data/residents/`. A man
        named on a committee beside three committed residents is placed by the company
        the corpus prints him in.
  ONE witness is enough. None is a refusal, and 12 of the pool are refused there.

THE STRUCTURAL REFUSALS — a name that cannot head a household at all. Six are T-0376's
and are kept word for word, because they are the same facts about the same corpus:
`garbled`, `a firm, not a person`, `first evidence after the scene date` (AGENTS.md
rule 3), `no surname the corpus prints`, `a surname and nothing else`, and the two
duplicate guards (`the town already names a <Surname>`, `surname already minted`).
Three more are new, and each was found by reading this pass's own output:

  · `the corpus carries this name as a business, and not among its proprietors` —
    'Eagle Hotel' is in the register's persons and is a BUILDING. The gazetteer's
    business records are the derived test: a name that is a business and is NOT listed
    among that business's own proprietors is the business, not a man. A tradesman
    whose shop the papers advertise under his own name IS among the proprietors, so
    this refuses the hotel without refusing the hatter. It reads the record's
    `partners` and not its `proprietors` (T-0398): a notice signed only by the firm
    puts the FIRM in the proprietor list, and 28 houses would otherwise vouch for
    themselves against a test written to catch precisely that.
  · `an article and a common noun, not a person` — 'the Baptist meeting house'. A
    grammatical fact about the printed name, not a list.
  · `the name is not printed clear of the transcription's uncertainty marks` — 180
    people, the largest refusal in the pass and the one that came from reading its own
    first output. See `printed_clear()` below: the register's normalized name hides
    damage the corpus records, and a household may not be named after a word the
    source does not contain. It is tested second, immediately after `garbled`, because
    both are facts about whether there is a legible name at all — everything below
    them is a fact about the person.
  · `the corpus prints a trade the residents vocabulary has no word for` — 36 people.
    `compile_register.py`'s TRADE_TO_OCCUPATION is a closed table by design, so a
    printed 'tinsmith', 'provision dealer' or 'house and land agent' arrives here with
    `occupation: null` NOT because the papers are silent about the trade but because
    the vocabulary cannot say it. Those people are documented TRADESPEOPLE and this
    pass will not mint them as trade-less: minting them would lose the trade the
    corpus prints, and the parent's rule is that an occupation is absent rather than
    invented — it does not license absent rather than RECORDED. They are refused here
    and carried by their own ticket, which this run opened.

WHAT THIS FILE WILL NOT DO. It will not invent an occupation, a dwelling, a division,
a sex or a family; the minted person's occupation reads `none_recorded`, the
residents vocabulary's own word for an absent record, because the corpus gives none. The PERSON is `attested` — the papers print the name. Everything
the household says around them is written as unattested, because it is.

A LIMIT, STATED RATHER THAN PAPERED OVER. The duplicate guards compare surnames
EXACTLY, so 'Blanshard' and 'Blanchard', or 'Eldredge' and 'Eldridge', pass each other
untouched and may be one man under two printed spellings. A fuzzy surname match was
considered and rejected for the reason `compile_register.py` gives for refusing a
fuzzy trade match: it would silently refuse a real family on a spelling that happened
to collide, and a wrongly refused resident is invisible where a wrongly accepted one
is at least a record somebody can read. `data/research/newspapers/identity.json` is
where a decided identity belongs.

THE POOL READS `enrich` BACK, for the reason T-0376's pass does: the register is
compiled FROM the committed town, so the moment this pass mints a man the compiler
stops calling him `new_resident`. An `enrich` whose target is one of THIS pass's own
person ids is read back in as this pass's previous answer.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
EXTRACTED = DATA / "research" / "newspapers" / "extracted"

sys.path.insert(0, str(ROOT / "tools"))
from rebuild_resident_index import rebuild  # noqa: E402  (the manifest's one owner)
from resident_mint_carry import carry_resident_mint  # noqa: E402  (T-1137)
from mint_documented_residents import (  # noqa: E402  (shared, deliberately)
    BARE_TOWN, FEMALE_TITLES, FIRM, MALE_TITLES, PAPERS, SCENE_DATE, UNCERTAIN,
    cited, display, dumps, household_id, in_town_places, issue_of, load,
    minted_by, paper_for, plain_fragment, slug, surname, titles_in,
    town_family_names, words,
)
from identity_master_guard import (  # noqa: E402  (T-0843)
    IdentityGuard, blind_person_ids, refusal as guard_refusal,
)

PREFIX = "hh_placed_"
LETTER_LIST_PREFIX = "hh_ll_"   # tools/mint_letter_list_residents.py; see the mint
CIVIC_PREFIX = "hh_civic_"      # tools/mint_civic_residents.py (T-0514); beside, not above
# T-0599: the pass-name/legacy-prefix pairs `town_family_names` skips for THIS
# pass — itself and the letter-list pass below it, never the documented pass
# above it. Kept as pairs (not the bare prefixes `_ORDER_SKIP` used to be) so a
# household minted plain, after T-0599, by either pass is still recognized.
# ("civic", "hh_civic_") joins them for the reason MINTED_PASSES states: the civic
# pass (T-0514) is beside the letter-list pass on a disjoint pool, not above this one.
_ORDER_SKIP = (("placed", PREFIX), ("letter_list", LETTER_LIST_PREFIX),
               ("civic", CIVIC_PREFIX))
PERSON_PREFIX = "placed_"
DIVISION = "unplaced"
ARTICLE = re.compile(r"^the\b", re.I)


def norm_place(s: str) -> str:
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()


# ---------------------------------------------------------------------------
# is the reading actually printed, or is it inside the transcriber's brackets
# ---------------------------------------------------------------------------

def project(text: str):
    """The letters of `text`, each flagged with whether it sits inside a [...] span.

    The transcription methodology brackets everything it is not sure of, so the
    brackets are DATA and not noise: '[uncertain: G. BLANSHARD]' is the transcriber
    saying they cannot read that name, and 'JOHN DAVE[S?]' is them saying they cannot
    read the end of it.
    """
    letters, flags, depth = [], [], 0
    for ch in text or "":
        if ch == "[":
            depth += 1
            continue
        if ch == "]":
            depth = max(0, depth - 1)
            continue
        if ch.isalnum():
            letters.append(ch.lower())
            flags.append(depth > 0)
    return "".join(letters), flags


def printed_clear(name: str, texts) -> bool:
    """Does one of these claims print this name whole and outside every bracket?

    THIS IS THE REPRODUCIBILITY TEST FOR A NAME, and it is the one refusal in this
    file that was added by reading the pass's own output rather than by reasoning
    ahead. Two of the first five people it minted came out of damaged type: the
    Democrat of 8 October 1834 prints 'fG. BL NSHARD' and the transcriber bracketed
    the whole reading as uncertain, and the American of 13 June 1835 prints
    'JOHN DAVE[S?]', where the bracket says the surname may be Daves. The gazetteer
    keeps both facts — the raw form in `variants[].as_printed` and the brackets in the
    claim's own `normalized` text — but the register's normalized NAME hides them, and
    a pass that reads only the name mints 'The Blanshard household' from a word the
    source does not contain. So the name has to be found letter for letter in a claim
    that carries it, with no bracketed letter inside the match AND none immediately
    after it, which is what catches a surname the transcriber left half-read.
    """
    # The papers print both orders and the gazetteer keeps whichever it read, so
    # 'Hinton, Isaac T.' has to be looked for as 'ISAAC T. HINTON' too — the same
    # reason `display()` exists. Without this the rule refuses a name the source
    # prints perfectly plainly, which is a wrongly refused resident.
    needles = {"".join(c.lower() for c in form if c.isalnum())
               for form in (name, display(name))}
    needles.discard("")
    if not needles:
        return False
    for text in texts:
        letters, flags = project(text)
        for needle in needles:
            i = letters.find(needle)
            while i >= 0:
                end = i + len(needle)
                after = flags[end] if end < len(flags) else False
                if not any(flags[i:end]) and not after:
                    return True
                i = letters.find(needle, i + 1)
    return False


def claim_text(extracted=EXTRACTED) -> dict:
    """claim id → the transcription's own normalized reading of it."""
    out = {}
    for path in sorted(extracted.glob("*.json")):
        doc = load(path)
        for c in doc["claims"]:
            out[f"{doc['issue_id']}#{c['id']}"] = c.get("normalized") or ""
    return out


# ---------------------------------------------------------------------------
# the corpus, read for the two things the test needs
# ---------------------------------------------------------------------------

def business_proprietors(gazetteer: dict) -> dict:
    """Every business name the corpus prints → the PEOPLE it prints under it.

    `partners` and not `proprietors` (T-0398). The test below asks whether a printed
    name is a house or a man, and answers it by looking for the name among the house's
    own proprietors — a hatter who advertises under his own name is there, a hotel is
    not. But a notice signed only by the firm puts the FIRM in that list, so 28 of the
    199 houses vouch for themselves: `business_russell_clift` carries 'Russell & Clift'
    among its proprietors because the Democrat of 1835-08-19 printed nothing else, and
    the house would then pass a test written to catch exactly that. The gazetteer already
    derives which entries are people, so this reads that instead.
    """
    out: dict = {}
    for biz in gazetteer["businesses"]:
        key = (biz.get("name") or "").strip().lower()
        if not key:
            continue
        out.setdefault(key, set()).update(
            (p or "").strip().lower() for p in (biz.get("partners") or []))
    return out


def already_held(register: dict, is_prior_mint_answer) -> set:
    """The register's own finding of who the committed town already holds.

    `enrich` is 'this printed person IS a person in data/residents/'. A target that
    is a mint's own previous answer is excluded — `is_prior_mint_answer` says which:
    the legacy `doc_`/`placed_` prefix still does, for any household not yet
    migrated to a plain id (T-0599); a migrated one only says so in its own
    source_pass field, which the caller has already read.
    """
    return {p["id"] for p in register["persons"]
            if p.get("action") == "enrich"
            and not is_prior_mint_answer(str(p.get("action_target") or ""))}


def claim_company(gazetteer: dict) -> dict:
    """claim id → the person ids the corpus prints in it."""
    company: dict = collections.defaultdict(set)
    for person in gazetteer["persons"]:
        for mention in person["mentions"]:
            company[mention].add(person["id"])
    return company


# ---------------------------------------------------------------------------
# the mint
# ---------------------------------------------------------------------------

def mint(docs: dict, index: dict):
    """Choose who joins the town. Returns (accepted, refusals)."""
    register = load(REGISTER)
    gazetteer = load(GAZETTEER)
    gaz = {p["id"]: p for p in gazetteer["persons"]}
    proprietors = business_proprietors(gazetteer)
    # T-0599: a plain id no longer says whose previous answer it is on its own —
    # the legacy `doc_`/`placed_` prefix still does, for any household not yet
    # migrated, but a migrated one only says so in its own source_pass field.
    own_placed = {doc["head"] for doc in docs.values() if doc.get("source_pass") == "placed"}
    prior_mint_answer = {doc["head"] for doc in docs.values()
                         if doc.get("source_pass") in ("documented", "placed")}

    def is_own_prior_answer(target: str) -> bool:
        return target.startswith(PERSON_PREFIX) or target in own_placed

    def is_prior_mint_answer(target: str) -> bool:
        return target.startswith(("doc_", PERSON_PREFIX)) or target in prior_mint_answer

    held = already_held(register, is_prior_mint_answer)
    company = claim_company(gazetteer)
    texts = claim_text()
    # The three-way precedence documented in mint_documented_residents.MINTED_PREFIXES:
    # this pass SEES `hh_doc_` and gives way to it, and does not see its own output
    # or the letter-list pass below it, which gives way to this one in turn.
    known = town_family_names(docs, index, skip=_ORDER_SKIP)
    # T-0843. The surname test above is blind to the households `_ORDER_SKIP` names —
    # this pass's own, the letter-list pass's and the civic pass's. The identity master
    # resolves on surname AND forename signature, so it can see into that blind spot
    # without the bluntness that made the proxy partial in the first place. Consulted
    # with the SAME precedence, so nothing here reads back this pass's own answer.
    guard = IdentityGuard.load()
    blind = blind_person_ids(docs, lambda path, doc: any(
        minted_by(path, doc, pass_name, prefix) for pass_name, prefix in _ORDER_SKIP))
    in_town = in_town_places()

    candidates = [p for p in register["persons"]
                  if not p.get("occupation") and not p.get("letter_list_only")
                  and (p.get("action") == "new_resident"
                       or (p.get("action") == "enrich"
                           and is_own_prior_answer(str(p.get("action_target") or ""))))]
    candidates.sort(key=lambda p: (-len(gaz[p["id"]]["mentions"]),
                                   p["first_seen"], p["id"]))

    taken: set = set()
    accepted, refusals = [], []
    for cand in candidates:
        g = gaz[cand["id"]]
        name = cand["name"]
        fam = surname(name)
        printed = name.strip().lower()
        places = g.get("associated_places") or []
        inside = [p for p in places if norm_place(p) in in_town]
        outside = [p for p in places if norm_place(p) not in in_town]
        addressed = [p for p in inside if norm_place(p) not in BARE_TOWN]
        issues = {m.split("#")[0] for m in g["mentions"]}
        neighbours = set()
        for mention in g["mentions"]:
            neighbours |= company.get(mention, set()) & held

        reason = None
        if UNCERTAIN.search(name):
            reason = "garbled"
        elif not printed_clear(name, [texts.get(m, "") for m in g["mentions"]]):
            reason = ("the name is not printed clear of the transcription's "
                      "uncertainty marks")
        elif FIRM.search(name):
            reason = "a firm, not a person"
        elif printed in proprietors and printed not in proprietors[printed]:
            reason = ("the corpus carries this name as a business, and not among "
                      "its proprietors")
        elif ARTICLE.match(name.strip()):
            reason = "an article and a common noun, not a person"
        elif cand["first_seen"] > SCENE_DATE:
            reason = "first evidence after the scene date"
        elif not fam:
            reason = "no surname the corpus prints"
        elif len(words(name)) < 2:
            reason = "a surname and nothing else"
        elif g.get("occupations"):
            reason = ("the corpus prints a trade the residents vocabulary has no "
                      "word for (" + ", ".join(g["occupations"]) + ")")
        elif outside:
            reason = ("placed where this project cannot put them in the town ("
                      + "; ".join(outside) + ")")
        elif not inside:
            reason = "the corpus places them nowhere"
        elif not addressed and len(issues) < 2 and len(neighbours) < 2:
            reason = ("at Chicago once and uncorroborated — no address in the town, "
                      "one issue, and fewer than two committed residents beside them")
        elif fam in known:
            reason = f"the town already names a {fam.title()}"
        elif (hit := guard.holder(name, blind_to=blind)) is not None:
            reason = guard_refusal(hit)
        elif fam in taken:
            reason = "surname already minted"
        if reason:
            refusals.append((cand["id"], name, reason))
            continue
        taken.add(fam)
        accepted.append((cand, g, inside, addressed, sorted(issues),
                         sorted(neighbours)))
    return accepted, refusals


# ---------------------------------------------------------------------------
# the records
# ---------------------------------------------------------------------------

def witness(addressed, issues, neighbours) -> str:
    """The sentence naming which of the three corroborations carried this person."""
    if addressed:
        return (f"THE CORPUS GIVES AN ADDRESS IN THE TOWN — {', '.join(addressed)} — "
                f"which is a placement no visitor passing through acquires.")
    if len(issues) > 1:
        return (f"THE CORPUS PRINTS THIS PERSON IN {len(issues)} SEPARATE ISSUES. A "
                f"transient is printed once and is gone; recurrence across the run is "
                f"the paper's own evidence that the town kept dealing with them.")
    return (f"THE CORPUS PRINTS THIS PERSON IN THE COMPANY THE TOWN ALREADY HOLDS: "
            f"{len(neighbours)} people this reconstruction already carries are named "
            f"in the same claim, which the register records as its `enrich` finding.")


def record(cand: dict, gaz: dict, inside, addressed, issues, neighbours,
          docs: dict, taken_ids: set[str]) -> dict:
    name = display(cand["name"])
    fam = surname(cand["name"]).title()
    sources = paper_for(gaz["mentions"])
    where = cited(gaz["mentions"])
    printed = sorted({v["as_printed"] for v in gaz.get("variants") or []})
    titles = titles_in(cand["name"])

    legacy_id = PREFIX + slug(cand["name"])
    hid = household_id(cand["name"], PREFIX, "placed", docs, taken_ids)
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
        "value": "none_recorded",
        "confidence": "reconstructed",
        "note": ("No source records an occupation for this person. This is the "
                 "ABSENCE of a record rather than a claim that they did no work: the "
                 "papers name them in a proceedings column, a public card or an "
                 "advertisement and simply do not say what they did for a living, and "
                 "`data/research/newspapers/register_1835.json` reads no trade for "
                 "them. Reasoning a trade out of the company they keep would be "
                 "inventing one, so the vocabulary's own word for an absent record is "
                 "what stands here."),
    }
    person["sources"] = list(sources)
    person["note"] = (
        "A DOCUMENTED PERSON, AND NO TRADE IS CLAIMED BECAUSE THE PAPERS GIVE NONE. "
        "The corpus prints "
        + " and ".join(f"'{p}'" for p in printed)
        + f" and places them at {', '.join(inside)}; it does not say what they did "
        f"for a living, where this household lived, who else was in it, or when it "
        f"came. The occupation therefore reads `none_recorded`, this dataset's own "
        f"word for an absent record, rather than a trade reasoned from the company "
        f"they keep — the absence is the finding. Cited at {where}. " + witness(addressed, issues, neighbours)
        + " A place the corpus associates with a person is where the paper does "
        "business with them and not a statement about where they slept. No figure is "
        "drawn (docs/LIBERTIES.md L1). READ THROUGH A TRANSCRIPTION, not a scan: the "
        "owner's ruling of 2026-08-28 grades a transcription-mediated reading as "
        "documented, and the source record for the run states that standard and its "
        "limits. A scan read that confirms or corrects the name upgrades this entry."
    )

    present = "present" if cand["last_seen"] >= SCENE_DATE else "uncertain"
    doc = {
        "id": hid,
        "name": f"The {fam} household — documented at Chicago, no trade printed, "
                f"unplaced in the town",
        "division": DIVISION,
        "head": pid,
    }
    if hid != legacy_id:
        # A genuinely new mint (T-0599): see mint_documented_residents.record()'s
        # matching comment — a household reusing its legacy id is unchanged.
        doc["source_pass"] = "placed"
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
            "note": ("Not attested, and no trade is recorded either — the papers name "
                     "this person without saying what they did."),
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
            f"MINTED FROM THE NEWSPAPER REGISTER (T-0373) BY A RESIDENCY TEST, NOT BY "
            f"A TRADE. T-0376's pass mints the register's `new_resident` people whose "
            f"trade the papers print; this one takes the rest, where there is no trade "
            f"to anchor anybody and a printed name on its own proves only that a "
            f"Chicago paper set the type. The test asks the corpus two questions "
            f"instead: does it place this person inside the town and NOWHERE outside "
            f"it, and does a second independent witness corroborate a bare 'Chicago' — "
            f"an address at street level, print in two or more issues, or print beside "
            f"two or more people this reconstruction already holds. "
            f"{witness(addressed, issues, neighbours)} The household around them is a "
            f"CONTAINER and not an argument: one member, no dwelling, no division, no "
            f"family, no recorded trade, and every one of those absences written as "
            f"unattested rather than filled in from the shape of the rest of the town. "
            f"That the person is a HOUSEHOLD is the one invention here and it is "
            f"recorded as docs/LIBERTIES.md L213. "
            f"tools/mint_placed_residents.py derives the whole minted set and prints "
            f"every candidate it refused, with the reason."
        ),
    })
    return doc


# T-0634. The civic writer's self-test pins these literals here, while T-1137's shared
# contract discovers the writer-owned marker without importing the pass as executable
# code. A drift in either still shows up in the writer's own assertion.
CIVIC_ROLLS_SOURCE = "chicago_voter_lists_1833_1835_irad"
CIVIC_ROLLS_MARKER = "THE TOWN'S OWN ROLLS, 1833-1835 — CORROBORATION, NOT A GRADE."

# T-0635, consolidation pass 2.  This writer's self-test pins the source and marker
# literals here; the shared carry contract discovers that marker from the writer itself.
FERGUS_1839_SOURCE = "fergus_chicago_directory_1839"
FERGUS_1839_MARKER = "FERGUS 1839'S LATER LISTS — 1837 AND 1839 EVIDENCE, NEVER AN 1835 FACT."

# T-0697. The land-sales crosswalk stopped counting namesakes and started putting the
# reading to every person of the surname.  The writer's self-test holds both constants
# against this file while the shared contract preserves the resulting finding.
LAND_SALES_SOURCE = "isa_public_domain_land_tract_sales"
LAND_SALES_MARKER = "THE FEDERAL LAND TRACT SALES — A PURCHASE, AND NEVER A RESIDENCE."

def carry_over(doc: dict, existing: dict) -> dict:
    """Keep every sibling pass's finding through the shared marker contract (T-1137)."""
    # ``sex`` is the one optional person field this mint derives from a printed title.
    # Its absence is therefore a new answer, not a foreign field to restore.
    return carry_resident_mint(doc, existing, owned_person_keys=("sex",))


def build(preload: dict | None = None):
    docs = ({p: json.loads(t) for p, t in preload.items() if p != INDEX}
            if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    index = (json.loads(preload[INDEX]) if preload is not None and INDEX in preload
             else load(INDEX))

    mine_paths = {p for p, doc in docs.items() if minted_by(p, doc, "placed", PREFIX)}
    accepted, refusals = mint(docs, index)

    files = {}
    seen: set = set()
    for cand, gaz, inside, addressed, issues, neighbours in accepted:
        doc = record(cand, gaz, inside, addressed, issues, neighbours, docs, seen)
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
    print(f"MINTED — {len(accepted)} documented resident(s), no trade printed")
    shown: set[str] = set()
    for cand, gaz, inside, addressed, issues, neighbours in accepted:
        hid = household_id(cand["name"], PREFIX, "placed", docs, shown)
        shown.add(hid)
        carried = ("an address in the town" if addressed
                   else f"{len(issues)} issues" if len(issues) > 1
                   else f"{len(neighbours)} committed residents beside them")
        print(f"  {hid:30s} {display(cand['name'])[:24]:26s} "
              f"({len(gaz['mentions'])} mention(s), {cand['first_seen']}.."
              f"{cand['last_seen']}; placed at {', '.join(inside)}; carried by "
              f"{carried})")
    print(f"\nREFUSED — {len(refusals)} candidate(s), with the reason")
    tally: dict = collections.Counter()
    for _, _, reason in refusals:
        tally[reason.split(" (")[0]] += 1
    for cid, name, reason in refusals:
        print(f"  {name[:34]:36s} {reason}")
    print("\nREFUSALS BY REASON")
    for reason, n in tally.most_common():
        print(f"  {n:4d}  {reason}")


# ---------------------------------------------------------------------------
# the assertions, so a refusal that stopped firing is a failure and not a discovery
# ---------------------------------------------------------------------------

def self_test() -> int:
    """Every rule in the residency test, fired against a case it must refuse.

    `--check` proves the pass re-derives what is committed; it cannot prove a RULE
    still works, because a rule that quietly stopped firing simply mints more people
    and the committed set moves with it. These are the cases each rule exists for,
    taken from the corpus where the corpus has one.
    """
    fails = []

    def want(label, got, expected):
        if got != expected:
            fails.append(f"{label}: got {got!r}, wanted {expected!r}")

    # printed_clear — the refusal that came from reading this pass's own output.
    want("a name whole and outside the brackets is printed clear",
         printed_clear("J. K. Boyer", ["Messrs. John H. Kinzie, J. K. Boyer, were "
                                       "elected T[rustees of this] Town"]), True)
    want("a name the transcriber bracketed entire is not",
         printed_clear("G. Blanshard",
                       ["enquire of [uncertain: G. BLANSHARD], Lake-st."]), False)
    want("a surname the transcriber left half-read is not",
         printed_clear("John Dave", ["JOHN DAVE[S?] NORTH WATER STREET"]), False)
    want("the other printed order is still the same name",
         printed_clear("Hinton, Isaac T.", ["ISAAC T. HINTON, Chicago;"]), True)
    want("a name the claim never prints is not printed clear",
         printed_clear("N. G. Sanford",
                       ["A CARD. [and the sixty-three signatures that follow]"]),
         False)
    want("a bracket elsewhere in the line does not refuse the name",
         printed_clear("B. S. Morris",
                       ["called to order by C[ol]. Hubbard, B. S. Morris addressed"]),
         True)

    # the business/person confusion, from the two records that caused it.
    props = business_proprietors({"businesses": [
        {"name": "Eagle Hotel", "partners": ["John Murphy"]},
        {"name": "W. G. Blanchard", "partners": ["W. G. Blanchard"]},
        # T-0398: a house that signed its own notice does not vouch for itself.
        {"name": "Russell & Clift", "proprietors": ["Aaron Russell", "Russell & Clift"],
         "partners": ["Aaron Russell"], "firm_styles": ["Russell & Clift"]}]})
    want("a hotel is not among its own proprietors",
         "eagle hotel" in props and "eagle hotel" not in props["eagle hotel"], True)
    want("a shop advertised under its keeper's name is",
         "w. g. blanchard" in props["w. g. blanchard"], True)
    want("a partnership does not stand among its own partners",
         "russell & clift" in props["russell & clift"], False)

    # the article rule, and the two duplicate guards' shape.
    want("a common noun behind an article is refused",
         bool(ARTICLE.match("the Baptist meeting house")), True)
    want("a person whose name begins with a word that merely starts 'the' is not",
         bool(ARTICLE.match("Theodore Rumsey")), False)

    # placement — the set the test resolves against is derived from the committed town.
    in_town = in_town_places()
    want("the bare town resolves inside", "chicago" in in_town, True)
    want("Green Bay does not", norm_place("Green Bay") in in_town, False)

    # the ordering between the three minting passes: this one must SEE T-0376's
    # households and NOT T-0378's; T-0376's must see neither.
    from mint_documented_residents import MINTED_PASSES, MINTED_PREFIXES, minted_by
    want("T-0376 skips all three minted prefixes",
         set(MINTED_PREFIXES) == {"hh_doc_", PREFIX, LETTER_LIST_PREFIX}, True)
    # T-0514 added a FOURTH pass, tools/mint_civic_residents.py. It is not a fourth
    # rung of this precedence: it sits BESIDE the letter-list pass on a pool its own
    # refusal 5 makes disjoint, and the three passes here skip it so that a civic
    # household never reads as "the town already names a <Surname>". Its own docstring
    # argues why, and MINTED_PASSES carries the same note.
    want("T-0599's pairs name the three passes and the civic pass beside them",
         {prefix for _, prefix in MINTED_PASSES}
         == {"hh_doc_", PREFIX, LETTER_LIST_PREFIX, CIVIC_PREFIX}, True)
    want("this pass skips its own, the letter-list pass's and the civic pass's, "
         "and not T-0376's",
         {prefix for _, prefix in _ORDER_SKIP}
         == {PREFIX, LETTER_LIST_PREFIX, CIVIC_PREFIX}, True)
    # minted_by recognizes a household by either shape — the legacy prefix every
    # household minted before T-0599 still carries, or the field a fresh mint
    # carries instead. A household with neither is nobody's.
    want("a legacy-prefixed household is recognized by its filename alone",
         minted_by(pathlib.Path(f"{PREFIX}smith_john.json"), {}, "placed", PREFIX), True)
    want("a plain household is recognized by source_pass alone",
         minted_by(pathlib.Path("hh_smith_john.json"), {"source_pass": "placed"},
                   "placed", PREFIX), True)
    want("a plain household with no source_pass belongs to nobody",
         minted_by(pathlib.Path("hh_smith_john.json"), {}, "placed", PREFIX), False)

    for line in fails:
        print(f"   FAIL {line}")
    if fails:
        print(f"   {len(fails)} assertion(s) no longer fire")
        return 1
    print("   OK: every refusal in the residency test still fires")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and report any drift without writing")
    ap.add_argument("--report", action="store_true",
                    help="print the mint and every refusal")
    ap.add_argument("--self-test", action="store_true",
                    help="fire every refusal against the case it exists for")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

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
        print(f"   OK: {len(accepted)} resident(s) minted by the residency test, "
              f"{len(refusals)} candidate(s) refused")
        return 0

    for p in sorted(mine_paths):
        if p not in files:
            p.unlink()
    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"minted {len(accepted)} resident(s); refused {len(refusals)} candidate(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
