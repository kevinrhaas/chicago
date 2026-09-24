#!/usr/bin/env python3
"""Documented people take the reconstructed roofs the register matched (T-0264).

    python3 tools/replace_invented_residents.py           write
    python3 tools/replace_invented_residents.py --check   re-derive and diff
    python3 tools/replace_invented_residents.py --report  the deal and every refusal

WHAT THIS IS FOR.

The town holds 113 households raised because the trade census demanded them and
no documented person was available to fill them. Every one carries an invented
name and a `name_basis` block saying so. `data/research/newspapers/
register_1835.json` now names, per trade, the documented people the papers put in
Chicago — `action: replace_invented` is exactly the register's finding that a
trade the town INVENTED a household for has a documented practitioner. This is
the pass that spends that finding: the documented man takes the roof, the
invented name is retired, and the card shows a real person with a newspaper
citation where it showed an invention.

WHAT THE ROOF KEEPS, AND WHY THE GRADE IS `inferred` AND NOT `attested`.

The PERSON becomes documented; the HOUSEHOLD does not. Nothing says where any of
these men slept, and the dwelling under them is still the reconstruction's — its
existence, its position and its footprint are unchanged and still conjectural.
`inferred` is this vocabulary's word for exactly that: a real person carrying
reconstructed details, with a note saying which details and from what. Grading
them `attested` would claim the dwelling as well as the man, which is the one
thing this pass must not do. docs/LIBERTIES.md L205 owns the placement.

THE DEAL, AND THE REFUSALS THAT SHAPE IT.

The register's candidate list is a compilation and not a nomination: it ranks by
trade and it does not ask whether a name is a man, whether he is already in this
town, or whether he was anywhere near it. Dealing it unguarded would have put a
partnership on a roof as a household head, minted a second John T. Temple, and
moved Bernardus Laughton off the Aux Plaines into the North Division. So a
candidate is REFUSED, and the refusal printed with its reason, when:

  1. `garbled`            — the transcription bracketed the name as uncertain.
                            'A CLY BOUR:' is not somebody's name.
  2. `a firm, not a person` — 'Pierce & Abbott', 'Matthias Mason & Co.',
                            'Johnson & Stevens'. A firm cannot head a household;
                            it is a BUSINESS, and the businesses are T-0263's.
  3. `first evidence after the scene date` — AGENTS.md rule 3. A man first
                            printed on 1835-08-15 is not put in the town of
                            1 July 1835 on the strength of it.
  4. `placed somewhere in particular` — the gazetteer gives him a named house or
                            a place outside the town: the Man Trap, a farm two
                            miles out, the Aux Plaines. A documented address is
                            EVIDENCE ABOUT WHERE HE WAS, and moving him onto
                            whichever reconstructed roof this deal happened to
                            reach would contradict his own record. Nothing here
                            can honour such a place, so the refusal stands.

                            T-0367 NARROWED THIS TO WHAT IT IS ACTUALLY ABOUT. It
                            used to refuse a documented STREET too, which is a
                            place this scene holds: `tools/fronting_street.py`
                            derives, from the platted lot a roof stands on, which
                            street it fronts, so the deal can now ask. A man whose
                            own record names a committed street is no longer
                            refused for being placed — he may take a roof of his
                            trade THAT STANDS ON THAT STREET, and only such a
                            roof. Where none does, refusal 8 says which street was
                            wanted and what the trade's roofs front instead.

  8. `wanted <street>, and no roof of his trade fronts it` — the street is
                            committed and the man is placeable; the town simply
                            has no invented roof of his trade on it. Six candidates
                            sit here on the tree this was written against, out of
                            the 27 the flat refusal used to hold, and the reason is
                            worth reading: every reconstructed roof
                            fronting South Water Street that carries a HOUSEHOLD is
                            a LABOURER's, so a baker, two joiners and two
                            shoemakers the papers put on South Water have no
                            dwelling on it to take. That is a fact about where the
                            occupation census placed the trades, not about the
                            evidence, and it is the finding this refusal exists to
                            surface.

                            T-0375 ASKED WHETHER THE TRADE A ROOF CARRIES COULD BE
                            RE-ARGUED AGAINST THE STREET IT FRONTS, and the answer
                            is no — but not for the reason the sentence above used
                            to imply, which is why it now says `dwelling` and
                            `carries a household` rather than `nowhere to go`.
                            `docs/STREET-FACE-ADOPTION.md`, the owner's ruling of
                            2026-08-29, already stands four of those six men on
                            South Water Street as documented STOREFRONTS —
                            D. Graves, A. Filer & Co., L. W. Montgomery and John
                            Holbrook — and that pass has taken all fourteen roofs
                            on the face it was allowed to take, leaving three more
                            businesses refused for want of one. So reseating a
                            shoemaker household onto a South Water roof of its own
                            family band would not add a man to the street; it
                            would evict a better-evidenced documented business
                            from a roof one-for-one, and it would stand
                            L. W. Montgomery or John Holbrook on that street a
                            second time. The remaining route — trading a
                            labourer's D1 log cabin for a shoemaker's D4 cottage
                            — is a claim about those men's means that no source
                            carries, and the family band IS that claim. The
                            refusal therefore stands and now names the adoption
                            when there is one, so it can never again be read as
                            saying the man is absent from the town.
  5. `already named in the town` — his surname already appears, capitalised, in a
                            committed structure record, household record or the
                            exclusions. The dataset has something to say about
                            that name already, and a pass that plants him on a
                            reconstructed roof would be answering a question that
                            is already open somewhere else. Deliberately blunt and
                            deliberately over-cautious: a wrongly refused
                            candidate costs a roof, a wrongly accepted one mints
                            a second copy of a real man.
  6. `spoken for by a placeable business` — the register carries a BUSINESS under
                            the same surname that it can put somewhere: an
                            `enrich_existing`, a `new_building` or a `street_only`
                            action. Those are the storefront tickets' to place,
                            and a man cannot be given a reconstructed dwelling in
                            one division while the same pass of work is standing
                            his shop in another. A business the register calls
                            `unplaceable` spoken for nobody and does not refuse.
                            T-0367: a dwelling on the SAME street as the shop is
                            not a fight, so where his own record and his shop both
                            name a street, that street is the only one he may take
                            a roof on. The comparison is made against the streets
                            the business record itself carries — `street_id`, a
                            corner's two sides, or the derived frontage of the
                            committed structure it is anchored to.
  7. `surname already dealt` — one surname, one roof. A shared surname reads as
                            kinship and this pass claims none; it is also how the
                            same man under two printed forms ('D. Graves' and
                            'Graves, D.') would otherwise take two roofs.

Candidates that survive are ranked by evidence — mentions first, then earliest
appearance, then id — and paired with that trade's invented roofs in id order.
Everything is deterministic: no randomness, no date, no hand-picked list.

WHAT THIS FILE WILL NOT DO. It will not upgrade a confidence to fill a roof, it
will not cite a claim the gazetteer does not carry, and it will not deal a
candidate past a refusal. A trade whose candidates are all refused keeps its
invented household, and `--report` says which refusal took each one.

THE FIFTH ROOF: ONCE DEALT, REFUSED TODAY, AND STANDING ANYWAY (T-1294).

THIS DEAL SEATS FOUR AND ONCE SEATED FIVE, and the difference is not a bug in
either number. T-0366 dealt five roofs on 2026-08-13; the fifth was
`hh_inf_joiner_north_02`, J. W. Reed, joiner. It is refused now — refusal 5,
`already named in the town` — and the household it left behind is still in the
tree, head and retired-invented-name prose and all. T-1228 found it and could
not say whose it was; this is the answer, and it is gated in
`data/reconstruction/1835_inferred_household_pass_ownership.json` under
`refused_and_standing`.

  * REFUSAL 5 IS THE ONLY BAR, and it is not this pass refusing its own output.
    `town_surnames()` deliberately does not read the hh_inf_ layer back (see
    the comment there), and the six cards that now speak the name Reed are all
    outside it. Measured 2026-09-21 by withholding them from the name pool and
    re-running the deal against the same pipeline input: with them, four seats
    and `joiner  J. W. Reed  already named in the town (reed)`; with all six
    withheld, five seats and no joiner refusal. Withholding only T-0514's three
    documented Reeds is not enough — three other cards still say it.
  * IT BEGAN FIRING UNDER A HOUSEHOLD THAT WAS ALREADY STANDING. All six cards
    entered the tree after 2026-08-13: the earliest on 2026-08-30 (T-0379's
    letter-list mint) and the three documented Reed households on 2026-09-04
    (T-0514). And it is RIGHT to fire — `hh_reid_j_chester`'s own prose reasons
    about `James W. Reed, joiner, on the 1834 and 1835 polls`, and two of the
    three documented Reeds are printed as joiners themselves. A reconstructed
    roof is exactly what refusal 5 keeps out of an open identity question.
  * THE MAN IS NOT REMOVED TO TIDY A PIPELINE. His evidence never came from
    this deal: `identity_master.json#id_reed_james_w` carries the 1834 and 1835
    poll books and the Democrat of 31 December 1833, and the grading ladder
    raised him to `attested` under G1a on that. census_1830's crosswalk has
    already ruled under D2 that J. W. Reed, S. W. Reed, Thomas Reed and William
    Reed are four cards this project will not merge. His grade is the resident
    layer's to argue and nothing here moves it.
  * SO THE HOUSEHOLD IS THE RESIDENT LAYER'S, on the same terms as the other
    four survivors: `tools/synthesize_resident_research.py`, which is what the
    settlement already said one block up about `the five that survived` and
    what it now says here too. Five hh_inf_ households survive; this is the
    fifth.
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

sys.path.insert(0, str(ROOT / "tools"))

import fronting_street  # noqa: E402  (needs the path above)

DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
INDEX = DATA / "residents" / "index.json"
REGISTER = DATA / "research" / "newspapers" / "register_1835.json"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
STRUCTURES = DATA / "structures"
EXCLUSIONS = DATA / "exclusions.json"
ADOPTIONS = DATA / "research" / "newspapers" / "street_face_adoptions.json"

SCENE_DATE = "1835-07-01"
PREFIX = "hh_inf_"

# The two runs, as they are registered in data/sources/. A claim id carries its
# issue; the SOURCE is the run, which is what every other record in this dataset
# cites and what carries the transcription-mediated standard (the owner's second
# ruling, 2026-08-28) in its own `repository` and `rights_note`.
PAPERS = (("chicago_democrat_", "chicago_democrat_1833_1835"),
          ("chicago_american_", "chicago_american_1835"))

TITLES = {"dr", "mr", "mrs", "jr", "sr", "esq", "capt", "col", "maj", "rev", "messrs"}
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


def surname(name: str) -> str:
    """The family name, lowercased, from either order the papers print.

    The corpus sets a man as 'S. Lincoln' in one column and 'Lincoln, S.' in the
    letter list two pages later, so the position of the family name is a property
    of the COLUMN and not of the name. A comma is the tell and it is the paper's
    own: reversed forms are printed reversed for alphabetising.
    """
    parts = words(name)
    if not parts:
        return ""
    if "," in name:
        head = words(name.partition(",")[0])
        return (head[-1] if head else parts[0]).lower().strip("'")
    return parts[-1].lower().strip("'")


def adoption_key(name: str) -> str:
    """This man's surname, spelled the way the adoption table spells one.

    The table's `surnames` are normalised down to letters — `M'Cormick` is `mcormick`
    there — so a lookup into it has to be normalised the same way or it silently misses.
    One key function, used to read the table and nowhere else (T-1042).
    """
    return re.sub(r"[^a-z]", "", surname(name).lower())


def display(name: str) -> str:
    """'Foot, S.' → 'S. Foot'. The papers print both orders; a card shows one."""
    if "," not in name:
        return name
    head, _, tail = name.partition(",")
    tail = tail.strip()
    return f"{tail} {head.strip()}" if tail else head.strip()


def issue_of(claim_id: str) -> str:
    """'chicago_democrat_1834_06_11#c003' → '11 June 1834, column 3'."""
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


# ---------------------------------------------------------------------------
# what the town already names
# ---------------------------------------------------------------------------

def town_surnames() -> set[str]:
    """Every capitalised word the committed dataset already uses as a name.

    Read from the structure records, the household records and the exclusions —
    prose included, because the reason to refuse a candidate is that this project
    has ALREADY said something about that name, and most of what it has said
    lives in a research note rather than in a `name` field.
    """
    known: set[str] = set()
    # NOT the reconstructed households. Their names are this layer's own
    # inventions and guard nothing, and once this pass has written a documented
    # name into one of them, reading it back would refuse that man on the next
    # run as "already named in the town" — a guard that poisons itself and makes
    # --check pass against any tree at all.
    files = (list(STRUCTURES.glob("*.json"))
             + [p for p in HOUSEHOLDS.glob("*.json") if not p.name.startswith(PREFIX)])
    if EXCLUSIONS.exists():
        files.append(EXCLUSIONS)
    for path in files:
        text = path.read_text(encoding="utf-8")
        for word in re.findall(r"\b[A-Z][a-z]{2,}\b", text):
            known.add(word.lower())
    return known


def invented_roofs(docs: dict) -> dict:
    """Trade → the households whose head carries an INVENTED name, in id order.

    `name_basis` is the marker and not the grade: a person may be graded
    `reconstructed` and still be a real person the dataset knows under a
    designation. Only a name the invented-name pools produced is this pass's to
    retire.
    """
    roofs: dict = {}
    for path in sorted(docs, key=lambda p: p.name):
        doc = docs[path]
        if not doc.get("id", "").startswith(PREFIX):
            continue
        for person in doc.get("persons", []):
            if "name_basis" not in person:
                continue
            trade = (person.get("occupation") or {}).get("value")
            if trade:
                roofs.setdefault(trade, []).append((path, doc, person))
    return roofs


def street_face_stands() -> dict[tuple[str, str], tuple[str, str]]:
    """{(proprietor surname, street_id): (business name, roof)} from T-0354's pass.

    T-0375 ASKED WHETHER THIS DEAL COULD PUT A TRADESMAN ON THE STREET HIS
    ADVERTISEMENT NAMES, and refusal 8 below used to answer for the whole town
    when it only ever spoke for the household layer. `docs/STREET-FACE-ADOPTION.md`
    landed the owner's ruling of 2026-08-29 the same day the ticket was filed: a
    business the paper puts on a street and nothing narrower adopts a reconstructed
    roof whose platted lot fronts that street. Four of the six men refusal 8 was
    written about — D. Graves, A. Filer & Co., L. W. Montgomery and John Holbrook —
    are standing on South Water Street through that pass while this one still
    reported that they had nowhere on it to go.

    So the refusal now READS the adoption table before it speaks. It is not
    softened and it seats nobody: a business adoption is a storefront and a
    household seat is a dwelling, and this deal still has no roof of the man's
    trade on his street to give him. What changes is that the refusal says which
    of the two is missing instead of implying both are.
    """
    if not ADOPTIONS.exists():
        return {}
    stands: dict[tuple[str, str], tuple[str, str]] = {}
    for row in load(ADOPTIONS).get("adoptions") or []:
        street_id = row.get("street_id")
        roof = row.get("structure_id")
        if not street_id or not roof:
            continue
        # T-1042. THE ROW CARRIES ITS OWN SURNAMES and this pass reads them instead of
        # taking the last word of each proprietor string, which invented a man out of a
        # firm suffix ('H. Doty & Co.' stood as somebody called Co) and lost one out of a
        # style ('Clark, Filer & Co.' dropped Filer, so Filer never matched here at all).
        # The reading is `compile_gazetteer.surname_words()`, through the pass that owns
        # the table; a copy of the guess here would be a third answer to one question.
        for sur in (row.get("surnames") or []):
            stands.setdefault((sur, street_id),
                              (row.get("business_name") or "", roof))
    return stands


def trade_fronts(roof_list) -> str:
    """What a trade's invented roofs front, for a refusal that must say so."""
    seen: list[str] = []
    for _path, doc, _person in roof_list:
        for street_id, _how in fronting_street.fronting(
                (doc.get("lives_at") or {}).get("value") or ""):
            name = fronting_street.street_name(street_id)
            if name not in seen:
                seen.append(name)
    return ", ".join(sorted(seen)) if seen else "no committed street"


# ---------------------------------------------------------------------------
# the deal
# ---------------------------------------------------------------------------

def deal(docs: dict):
    """Pair documented candidates with invented roofs. Returns (pairs, refusals)."""
    register = load(REGISTER)
    gazetteer = {p["id"]: p for p in load(GAZETTEER)["persons"]}
    known = town_surnames()
    roofs = invented_roofs(docs)

    adopted = street_face_stands()
    pairs, refusals = [], []
    # One surname, one roof, ACROSS the whole deal and not merely within a trade:
    # a shared surname reads as kinship and this pass claims none.
    taken: set[str] = set()
    for trade in sorted(roofs):
        # THE POOL SURVIVES ITS OWN EFFECT. The register is compiled FROM the
        # committed town, so the moment this pass seats a man on a roof the
        # register stops calling him `replace_invented` and starts calling him
        # `enrich` — he is in the town now, and the compiler is right about that.
        # Reading only `replace_invented` would therefore make the deal
        # unre-derivable the run after it lands: the candidate that won would
        # have vanished from the pool that chose him, and `--check` would report
        # drift on a tree nobody had touched. So an `enrich` whose target is a
        # person on a RECONSTRUCTED roof of this trade is read back into the pool
        # as what it is — this pass's own previous answer. The `occupation` test
        # is what keeps the sixteen name-coincidence matches out: an enrich with
        # no trade matched an INVENTED name and says nothing about a tradesman.
        candidates = [p for p in register["persons"]
                      if p.get("action") == "replace_invented"
                      and p.get("action_target") == trade]
        candidates += [p for p in register["persons"]
                       if p.get("action") == "enrich"
                       and p.get("occupation") == trade
                       and str(p.get("action_target") or "").startswith("inf_")]
        candidates.sort(key=lambda p: (-len(gazetteer[p["id"]]["mentions"]),
                                       p["first_seen"], p["id"]))
        # A MAN IS PLACED BY ANY OF HIS PRINTINGS, not only by the one this loop
        # is looking at. 'P. J. Carli' carries no place and 'P. S. Carli' is at
        # the Eagle Tavern; they are one publican, and dealing the first onto a
        # reconstructed roof in the North Division while the second stands in a
        # named house on Lake Street would be two answers to one question. So the
        # placements are collected per SURNAME first and refuse every form of it.
        spoken_for: dict[str, str] = {}
        # WHICH STREETS THE SHOP ITSELF NAMES (T-0367). The guard below refuses a
        # man whose shop the placement tickets can stand, because a dwelling in
        # one division must not fight a shop in another. Where his own record and
        # his shop name the SAME street there is no fight to have, so the streets
        # are collected and the guard is asked to compare rather than to assume.
        # A business anchored on a committed structure contributes that
        # structure's own derived frontage — the same derivation, asked twice.
        shop_streets: dict[str, set[str]] = {}
        for biz in register["businesses"]:
            if biz.get("action") not in ("enrich_existing", "new_building", "street_only"):
                continue
            anchor = biz.get("anchor") or {}
            streets = {s for s in ([biz.get("street_id")]
                                   + list(anchor.get("streets") or [])) if s}
            if anchor.get("kind") == "structure" and anchor.get("target"):
                streets |= {sid for sid, _how
                            in fronting_street.fronting(anchor["target"])}
            for word in re.findall(r"\b[A-Za-z]{3,}\b", biz.get("name") or ""):
                spoken_for.setdefault(word.lower(),
                                      f"{biz['name']}, {biz['action']}")
                shop_streets.setdefault(word.lower(), set()).update(streets)

        placed: dict[str, str] = {}
        for other in candidates:
            where = [p for p in (gazetteer[other["id"]].get("associated_places") or [])
                     if p.strip().lower() not in BARE_TOWN]
            key = surname(other["name"])
            if key and where and key not in placed:
                placed[key] = "; ".join(where)

        accepted = []
        for cand in candidates:
            name, gaz = cand["name"], gazetteer[cand["id"]]
            places = [p for p in (gaz.get("associated_places") or [])
                      if p.strip().lower() not in BARE_TOWN]
            # T-0367. A PLACE IS NOT A WALL ANY MORE. Where the line names a
            # street this scene commits, the man is not refused for being
            # placed — he is placed, and the deal may seat him on a roof of his
            # trade that FRONTS that street (tools/fronting_street.py). Where it
            # names somewhere else — a tavern, a farm, Fort Dearborn, a street
            # this scene does not plat — nothing here can honour it and the
            # refusal stands exactly as it did.
            wanted = fronting_street.streets_of(places)
            sur = surname(name)
            # Where the shop is spoken for, the man may only take a roof on a
            # street BOTH his record and his shop name — agreement, not a guess.
            agreed = ([s for s in wanted if s in shop_streets.get(sur, set())]
                      if sur in spoken_for else wanted)
            reason = None
            if UNCERTAIN.search(name):
                reason = "garbled"
            elif FIRM.search(name):
                reason = "a firm, not a person"
            elif cand["first_seen"] > SCENE_DATE:
                reason = "first evidence after the scene date"
            elif places and not wanted:
                reason = f"placed somewhere in particular ({'; '.join(places)})"
            elif not sur:
                reason = "no surname the corpus prints"
            elif sur in placed and not wanted:
                reason = (f"another printing of this surname is placed somewhere in "
                          f"particular ({placed[sur]})")
            elif sur in spoken_for and not agreed:
                reason = (f"spoken for by a placeable business "
                          f"({spoken_for[sur]})")
            elif sur in known:
                reason = f"already named in the town ({sur})"
            elif sur in taken:
                reason = "surname already dealt"
            if reason:
                refusals.append((trade, cand["id"], name, reason))
                continue
            taken.add(sur)
            accepted.append((cand, gaz, agreed))

        # THE STREET-PLACED ARE SEATED FIRST, because they are the only ones with
        # a constraint: an unplaced man may take any roof of his trade, so
        # letting him take one first could spend the single roof the placed man
        # is allowed. Within each group the order is the evidence rank the pool
        # was already sorted by, and the roofs are taken in id order, so the deal
        # stays deterministic and re-derivable.
        free = list(roofs[trade])
        for cand, gaz, want in [row for row in accepted if row[2]]:
            seat = next(
                ((roof, street_id, how)
                 for roof in free
                 for street_id in want
                 for how in [fronting_street.fronts(
                     (roof[1].get("lives_at") or {}).get("value") or "", street_id)]
                 if how), None)
            if seat is None:
                reason = (
                    f"wanted {', '.join(fronting_street.street_name(s) for s in want)}; "
                    f"no invented {trade.replace('_', ' ')} roof fronts it "
                    f"(this trade's {len(roofs[trade])} roof(s) front "
                    f"{trade_fronts(roofs[trade])})")
                # T-0375: say so when he is already standing on that street as a
                # storefront. The household seat is still refused; what the man
                # is short of is a dwelling, not a place in the town.
                key = adoption_key(cand["name"])
                already = next((adopted[(key, s)]
                                for s in want if (key, s) in adopted), None)
                if already:
                    reason += (f" — but he stands on that street already as "
                               f"'{already[0]}', a street-face adoption on "
                               f"{already[1]} (T-0354); what he is short of here "
                               f"is a dwelling, not a place in the town")
                refusals.append((trade, cand["id"], cand["name"], reason))
                continue
            roof, street_id, how = seat
            free.remove(roof)
            pairs.append((roof, cand, gaz, trade, (street_id, how)))
        for cand, gaz, _want in [row for row in accepted if not row[2]]:
            if not free:
                refusals.append((trade, cand["id"], cand["name"],
                                 "no invented roof of this trade left to take"))
                continue
            pairs.append((free.pop(0), cand, gaz, trade, None))
    return pairs, refusals


# ---------------------------------------------------------------------------
# the records
# ---------------------------------------------------------------------------

def rewrite(doc: dict, person: dict, cand: dict, gaz: dict, trade: str,
            seating=None) -> None:
    name = display(cand["name"])
    sources = paper_for(gaz["mentions"])
    cited = "; ".join(issue_of(c) for c in gaz["mentions"][:6])
    more = ("" if len(gaz["mentions"]) <= 6
            else f", and {len(gaz['mentions']) - 6} further mention(s)")
    printed = sorted({v["as_printed"] for v in gaz.get("variants") or []})
    trades = ", ".join(gaz.get("occupations") or [trade.replace("_", " ")])
    family = surname(cand["name"]).title()
    # T-0367: which clause of the placement rule this man is here under.
    if seating:
        street_id, how = seating
        street = fronting_street.street_name(street_id)
        where = (
            f"HIS OWN RECORD NAMES THIS STREET. The corpus places him on "
            f"{street}, and the roof he takes is one the plat says stands there: "
            f"tools/fronting_street.py derives the frontage of "
            f"{(doc.get('lives_at') or {}).get('value')} from the committed "
            f"geometry as {fronting_street.describe((doc.get('lives_at') or {}).get('value'))}, "
            f"and this seat is its {how}. That is the whole of the claim — the "
            f"STREET is his and the roof on it is still the reconstruction's. He "
            f"was refused by this pass until T-0367 because a placement it could "
            f"not read was safer to refuse than to honour; it can read one now, "
            f"and a man is not put on a street his record contradicts.")
        placement_note = f"placed by his own record on {street}"
    else:
        where = (
            f"He is placed nowhere in particular by his own record, which is the "
            f"condition of taking ANY roof of his trade — a man the papers put on "
            f"a named street takes only a roof the plat stands on that street "
            f"(T-0367), and one they place somewhere this scene cannot honour is "
            f"refused outright.")
        placement_note = "places nowhere in particular"

    person["name"] = name
    person["grade"] = "inferred"
    person["sources"] = list(sources)
    person.pop("name_basis", None)
    person["note"] = (
        f"A DOCUMENTED MAN ON A RECONSTRUCTED ROOF. The papers name him and this "
        f"household's dwelling does not: what is attested is the person and his "
        f"trade, and what remains the reconstruction's is everything about where "
        f"he lived. He is printed as "
        + ", ".join(f"'{p}'" for p in printed)
        + f" and the corpus reads his trade as {trades}. Cited at {cited}{more}. "
        f"THIS ROOF DID NOT COME FROM HIS RECORD. The household was raised by the "
        f"occupation census because the town of 3,265 people in 398 dwellings "
        f"needed a {trade.replace('_', ' ')} and no documented one was available; "
        f"the register (data/research/newspapers/register_1835.json, action "
        f"`replace_invented`) is what says one now is. The dwelling's existence, "
        f"position and footprint are unchanged and still conjectural, and nothing "
        f"here claims he slept in it — only that the town's need for this trade is "
        f"met by a man the papers name rather than by one this project invented. "
        f"The invented name this record used to carry, and its name_basis block, "
        f"are retired: an invented name is not kept beside a documented one. "
        f"No figure is drawn (docs/LIBERTIES.md L1); the placement is L205. "
        + where + " "
        f"READ THROUGH A TRANSCRIPTION, not a scan: the owner's ruling of "
        f"2026-08-28 grades a transcription-mediated reading as documented, and "
        f"the source record for the run states that standard and its limits. A "
        f"scan read that confirms or corrects the name upgrades this entry."
    )
    occ = person.get("occupation") or {}
    occ["confidence"] = "attested"
    occ["sources"] = list(sources)
    occ["note"] = (
        f"THE TRADE IS THE PAPER'S, NOT THE CENSUS'S. The corpus reads him as "
        f"{trades}, at {cited}{more}. This record used to carry the occupation "
        f"census's argument for the trade instead — that a town of this size "
        f"needs so many of them — which is why the household exists; it is no "
        f"longer why this man holds the trade. Where the corpus prints more than "
        f"one trade for him, they are all recorded here and the household's is "
        f"the one the register matched."
    )
    person["occupation"] = occ

    # BOTH TRUTHS IN ONE LINE, and the second one is not decoration: the card
    # prints the head's own grade chip directly under this label, so a label
    # naming a tier the chip contradicts is the K23a fault in the other
    # direction. "a documented cooper" is what changed and "inferred at this
    # roof" is what did not — he is documented as a man and inferred as this
    # household's head. tools/smoke_renderer.mjs PART 3 asserts the two agree.
    doc["name"] = (f"The {family} household — a documented "
                   f"{trade.replace('_', ' ')}, inferred at this roof "
                   f"({doc.get('division', '')} division)")

    # The arrival bound is now the paper's rather than the scene date's. The
    # household used to say `not_later_than 1835-07-01` and explain that nothing
    # dates a hypothesised household; something dates this man.
    doc["arrival"] = {
        "value": cand["first_seen"],
        "confidence": "inferred",
        "sources": list(sources),
        "note": (
            f"A BOUND FROM THE PAPER, NOT AN ARRIVAL. The corpus first prints him "
            f"at {issue_of(gaz['mentions'][0])}, so he is in the town's paper by "
            f"{cand['first_seen']} and at no stated time before it; nothing "
            f"reached says when he came. The household used to carry the scene "
            f"date as its bound, because nothing dated a hypothesised household — "
            f"this is the same claim made against evidence instead of against the "
            f"date the town is being counted on. Last printed "
            f"{cand['last_seen']}."),
        "precision": "not_later_than",
    }
    doc["research_note"] = (
        doc.get("research_note", "").rstrip()
        + f"\n\nRETIRED AN INVENTED NAME (T-0264). This household was raised by "
        f"the occupation census and named from the invented-name pools. The "
        f"newspaper register matched it to {name}, a documented "
        f"{trade.replace('_', ' ')} the corpus names {len(gaz['mentions'])} "
        f"time(s) and {placement_note}, and he now holds the roof. "
        f"What changed is WHO: the argument for the household, its dwelling and "
        f"its position are untouched and still the reconstruction's, and the "
        f"person's grade is `inferred` — a real man with reconstructed details — "
        f"rather than `attested`, which would claim the dwelling too. "
        f"tools/replace_invented_residents.py derives this deal and prints every "
        f"candidate it refused."
    )


def build(preload: dict | None = None):
    docs = ({p: json.loads(t) for p, t in preload.items()} if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    index_text = None
    if preload is not None and INDEX in preload:
        index_text = preload[INDEX]
        docs.pop(INDEX, None)
    house_docs = {p: d for p, d in docs.items() if p.name.startswith("hh_")}

    pairs, refusals = deal(house_docs)
    files = {}
    for (path, doc, person), cand, gaz, trade, seating in pairs:
        rewrite(doc, person, cand, gaz, trade, seating)
        files[path] = dumps(doc, 1)

    # The manifest's denormalised copies, which validate.py holds equal to the
    # records. Re-derived over the WHOLE layer by the manifest's one owner
    # (T-0715) rather than patched row by row: this pass moves grades, and the
    # rows it does not move can be as stale as any other pass has left them.
    index = json.loads(index_text) if index_text is not None else load(INDEX)
    final = dict(house_docs)
    final.update({path: json.loads(text) for path, text in files.items()
                  if path != INDEX})
    rebuild(index, final)
    files[INDEX] = dumps(index, 1)
    return files, pairs, refusals


def overlay(files: dict) -> dict:
    """Apply this pass to an in-memory {path: text} map and hand it back.

    The third stage of the household pipeline — build, then name, then replace —
    called by tools/generate_inferred_households.py --check for the same reason
    it calls the naming pass: a drift report that compares a midpoint against the
    tree cries wolf on every run.
    """
    out = dict(files)
    replaced, _pairs, _refusals = build(preload={p: t for p, t in files.items()})
    out.update({p: t for p, t in replaced.items() if p in files or p == INDEX})
    return out


def report(pairs, refusals) -> None:
    seated = [row for row in pairs if row[4]]
    print(f"THE DEAL — {len(pairs)} invented name(s) retired")
    for (_path, doc, person), cand, gaz, trade, seating in pairs:
        on = (f"  on {fronting_street.street_name(seating[0])} ({seating[1]})"
              if seating else "")
        print(f"  {doc['id']:34s} {trade:14s} -> {person['name']:24s} "
              f"({cand['id']}, {len(gaz['mentions'])} mention(s), "
              f"{cand['first_seen']}..{cand['last_seen']}){on}")

    # T-0367's own accounting, printed where the change is: the refusals that
    # used to read 'placed somewhere in particular' either seat now, or say
    # which street was wanted and what the trade's roofs front instead.
    print(f"\nPLACED BY THEIR OWN RECORD — {len(seated)} seated on the street "
          f"the papers name (T-0367)")
    for (_path, doc, person), cand, _gaz, trade, seating in seated:
        print(f"  {trade:14s} {person['name'][:24]:26s} "
              f"{fronting_street.street_name(seating[0]):20s} {seating[1]:15s} "
              f"{doc['id']}")
    wanted = [row for row in refusals if row[3].startswith("wanted ")]
    print(f"  {len(wanted)} more name a committed street with no roof of their "
          f"trade on it; {sum(1 for r in refusals if r[3].startswith('placed '))} "
          f"name a place this scene cannot resolve to a street.")

    print(f"\nREFUSED — {len(refusals)} candidate(s), with the reason")
    for trade, cid, name, reason in refusals:
        print(f"  {trade:14s} {name[:34]:36s} {reason}")


def pipeline_input() -> dict:
    """The households as the two passes BEFORE this one derive them.

    Not the committed tree. This pass is not idempotent against its own output —
    it retires the `name_basis` block that tells it which roofs are invented, so
    re-reading the tree after a write finds nothing to do and a --check built
    that way would pass on any tree whatever, including a hand-edited one. The
    honest input is the same one the household pipeline uses: the programme's own
    output, named, and then dealt.
    """
    import importlib.util
    def _load(name):
        spec = importlib.util.spec_from_file_location(
            name, pathlib.Path(__file__).with_name(f"{name}.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    programme = _load("generate_inferred_households")
    gen_names = _load("generate_inferred_names")
    files, _records, _households = programme.build_all()
    files = gen_names.overlay(files)
    return {p: t for p, t in files.items()
            if p.name.startswith("hh_") or p == INDEX}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and report any drift without writing")
    ap.add_argument("--report", action="store_true",
                    help="print the deal and every refusal")
    args = ap.parse_args()

    files, pairs, refusals = build(preload=pipeline_input())
    if args.report:
        report(pairs, refusals)
        return 0
    if args.check:
        # WHAT SURVIVED OF THIS PASS, AND WHAT TOOK THE REST (T-1228).
        #
        # Until 2026-09-17 this compared its whole output against the tree and
        # reported five files differing. Two things had happened underneath it. The
        # owner's T-0489 ruling of 2026-09-02 retired the reconstructed resident
        # population and left the real men this pass had seated UNPLACED, so their
        # `lives_at` and `works_at` are null in the tree while this pass still deals
        # each of them the roof the register matched. And
        # tools/synthesize_resident_research.py then took those four households into
        # the resident research layer, raising each head from `inferred` to
        # `attested` under a ladder rule and adding press, civic, book, directory
        # and old-settler evidence blocks this pass knows nothing about. Between
        # them they own division, name, research_note and the head's grade, sources
        # and note. Demanding the whole file back is demanding both be reverted.
        #
        # What is still this pass's, and only this pass's, is WHO IS ON THE ROOF:
        # the head's id and name. That is the register's finding, and if the
        # register changes under these four roofs this goes red. The withdrawal is
        # asserted rather than skipped — a man who quietly becomes placed again
        # fails here.
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import inferred_household_ownership as ownership  # noqa: PLC0415

        seated = {doc["id"]: person for (_p, doc, person), _c, _g, _t, _s in pairs}
        drift = ownership.check_replace_pass(seated)
        for item in drift:
            print(f"   DRIFT: {item}")
        if drift:
            print(f"   {len(drift)} finding(s) — see "
                  f"data/reconstruction/1835_inferred_household_pass_ownership.json")
            return 1
        print(f"   OK: {len(pairs)} documented resident(s) still head the roofs this pass "
              f"deals them, {len(refusals)} candidate(s) refused, and T-0489 still "
              f"leaves every one of them unplaced")
        return 0

    for p, text in files.items():
        p.write_text(text, encoding="utf-8")
    print(f"retired {len(pairs)} invented name(s); refused {len(refusals)} candidate(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
