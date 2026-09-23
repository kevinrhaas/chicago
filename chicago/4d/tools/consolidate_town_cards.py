#!/usr/bin/env python3
"""One person, several cards: the merge of the town's duplicate resident records.

WHY THIS EXISTS, in the owner's words (2026-09-05, reading data/residents/households
on dev): "do a review and consolidate of the residents, like James Allen is almost
certainly one record and he is spread across several, don't lose any data, but
consolidation is needed across the residents" — and, when the first draft of the ticket
stopped at a report, "make the ticket merge those records — research without
consolidation is useless".

WHAT WAS WRONG. Each source pass minted the name the way its source printed it and no
pass asked whether the town already had the man. `tools/consolidate_resident_evidence.py`
clusters SOURCE APPEARANCES into identities and marks which town cards each identity
absorbs, but its canonical card is town[0] and the merge is never proposed back onto the
cards — so a person the consolidation already knows is one identity stays several cards
for ever, and every pass that spends onto cards spends onto the wrong one or onto all of
them. Lieut. James Allen stood on four cards and only the one the ladder never reached
knew he was an army officer.

WHAT THIS TOOL DOES.
  1. DERIVES the candidate clusters: every group of town cards a surname-plus-compatible-
     forename test joins. Compatible means a full forename against the same word, an
     initial that the word begins with, or a card that prints a title and no forename at
     all — nothing looser. The candidate list is a WORKLIST, never a merge list: some of
     these are brothers, spouses, or a father and a son.
  2. Reads the WRITTEN RULING for every one of them from
     `data/residents/card_merge_rulings.json`, and refuses to pass its own gate while any
     card in a candidate cluster carries no ruling. That is the half that stops this
     recurring: a mint that re-splits an identity puts an unruled card in a cluster and
     `--check` goes red.
  3. LANDS the merges. A merge loses nothing:
       * the folded record is copied WHOLE to `data/residents/merged/<id>.json` with a
         `merged_into` block, so every byte of it is still in the tree and readable;
       * `index.json` grows a `merged` redirect table, so every `person_id` any file
         cites — the crosswalks, identity_master.json, the smoke cohorts, the placed-
         resident parcels — still resolves to a person;
       * `data/research/residents/card_merge_crosswalk.json` is the LANDED ADJUDICATION.
         `consolidate_resident_evidence.py`'s `declared_anchors()` reads every
         `*crosswalk*.json` under data/research/ and moves the anchored appearances onto
         the identity that holds the named person. So the folded cards' sources arrive on
         the survivor through the project's own machinery, the ladder regrades the joined
         identity, and `mint_civic_residents.py` refuses to re-mint the folded card
         because its identity now has a canonical person the pass does not own. Nothing
         here is a special case bolted beside the derivation; it is a ruling the
         derivation reads.
       * where the survivor is a HAND-AUTHORED card — the Andreas-derived records that no
         mint pass owns and no derivation will therefore spend onto — the union is written
         here: the folded cards' sources and evidence blocks, and a `merged_from` block
         naming what came from where.
  4. Writes the DISTINCT and UNDECIDED rulings onto the cards themselves, as a
     `merge_ruling` block, so the next pass reads the answer instead of re-asking.

    tools/consolidate_town_cards.py --report       the clusters and their rulings
    tools/consolidate_town_cards.py --candidates   write the ledger only
    tools/consolidate_town_cards.py --apply        land the rulings
    tools/consolidate_town_cards.py --check        the gate
    tools/consolidate_town_cards.py --self-test    the assertions still fire when broken
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESIDENTS = ROOT / "data" / "residents"
HOUSEHOLDS = RESIDENTS / "households"
MERGED = RESIDENTS / "merged"
INDEX = RESIDENTS / "index.json"
RULINGS = RESIDENTS / "card_merge_rulings.json"
LEDGER = ROOT / "data" / "research" / "residents" / "town_card_candidates.json"
CROSSWALK = ROOT / "data" / "research" / "residents" / "card_merge_crosswalk.json"
IDENTITY_MASTER = ROOT / "data" / "research" / "residents" / "identity_master.json"

GENERATED_BY = "tools/consolidate_town_cards.py --apply"
TICKET = "T-0839"
RULED_ON = "2026-09-05"

sys.path.insert(0, str(ROOT / "tools"))
from reconstructed_person import is_reconstructed  # noqa: E402
from consolidate_resident_evidence import split_name_or_reason  # noqa: E402

# A rank is not a forename. `consolidate_resident_evidence.HONORIFICS` already drops the
# short forms the sources print most; these are the long ones the town cards carry, and
# they are stripped HERE rather than there because the identity master's own rules are
# ratified and this pass may not move them.
RANKS = {"lieut", "lieutt", "lieutenant", "captain", "colonel", "major", "general",
         "doctor", "reverend", "sergeant", "judge", "deacon", "elder"}

# block key -> the identity master's domain(s) that write it. `book_evidence` is written
# by two domains and the inversion is therefore one-to-many; an anchor row for a domain
# that never held the record simply never matches, so naming both is safe and honest.
BLOCK_DOMAINS = {
    "civic_evidence": ("civic",),
    "church_evidence": ("church",),
    "press_evidence": ("newspapers",),
    "book_evidence": ("directories", "old_settlers"),
    "census_evidence": ("census_1840",),
}
BLOCK_KEYS = tuple(BLOCK_DOMAINS)


# ---------------------------------------------------------------------------
# the candidate test

def forename_tokens(name: str):
    """(surname, forename tokens with ranks stripped), or None if it names nobody."""
    parsed, _ = split_name_or_reason(name or "")
    if not parsed:
        return None
    surname, given = parsed
    return surname, [t for t in given if t not in RANKS]


def compatible(a, b) -> bool:
    """A full forename against the same word, an initial, or a title. Nothing looser."""
    ga, gb = a[1], b[1]
    if not ga or not gb:
        return True                      # a card that prints a title and no forename
    x, y = ga[0], gb[0]
    if x == y:
        return True
    return (len(x) == 1 and y.startswith(x)) or (len(y) == 1 and x.startswith(y))


def bracket_conflict(as_read: str, survivor_id: str) -> str | None:
    """The forename a transcriber BRACKETED, when the survivor is not that man.

    T-0855. A reading like "Hubbard, [Henry] G." carries an editorial expansion:
    somebody read the page and said who this is. That is evidence about IDENTITY,
    where an initial is only evidence about spelling — so a fold that contradicts
    it has put one man's record on another man. Returns the forename when it
    conflicts, else None.

    A bracketed RANK is not a forename and never conflicts. "Allen, [Lieut] James"
    folded onto `allen_james` would otherwise read as a contradiction, and it is
    only a title the transcriber supplied — which is the false positive this check
    would have shipped without the guard.
    """
    hit = re.search(r"\[([A-Za-z]+)\]", str(as_read or ""))
    if not hit:
        return None
    word = hit.group(1)
    if word.lower().rstrip(".") in RANKS:
        return None
    return None if word.lower() in survivor_id.lower() else word


def read_town(root: Path | None = None) -> list:
    """One row per person on a card in the index, with the household it stands on."""
    root = root or RESIDENTS
    index = json.loads((root / "index.json").read_text(encoding="utf-8"))
    rows = []
    for entry in index.get("households", []):
        path = root / entry["file"]
        doc = json.loads(path.read_text(encoding="utf-8"))
        for person in doc.get("persons") or []:
            # T-1171. A person a stage of the reconstruction programme wrote is not a card
            # claiming an identity: no source names them and their forename came out of a
            # name pool. Clustering one against a real card would ask a reader to rule on
            # whether this dataset's own invention is the man it was drawn beside.
            if is_reconstructed(person):
                continue
            rows.append({"household": doc["id"], "person": person["id"],
                         "name": person.get("name") or "", "doc": doc, "record": person})
    return rows


def clusters(rows: list) -> list:
    """Every group of two or more cards the candidate test joins, in a stable order."""
    by_surname = defaultdict(list)
    for row in rows:
        parsed = forename_tokens(row["name"])
        if parsed:
            row["parsed"] = parsed
            by_surname[parsed[0]].append(row)
    out = []
    for surname, group in sorted(by_surname.items()):
        if len(group) < 2:
            continue
        parent = list(range(len(group)))

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                if compatible(group[i]["parsed"], group[j]["parsed"]):
                    a, b = find(i), find(j)
                    if a != b:
                        parent[a] = b
        buckets = defaultdict(list)
        for i, row in enumerate(group):
            buckets[find(i)].append(row)
        for _, members in sorted(buckets.items(),
                                 key=lambda kv: sorted(r["person"] for r in kv[1])):
            if len(members) > 1:
                out.append({"surname": surname,
                            "cards": sorted(members, key=lambda r: r["person"])})
    return out


# ---------------------------------------------------------------------------
# the evidence a pair is weighed on

def anchored(person: dict, doc: dict) -> bool:
    """Does this card DOCUMENT the person, or only list them?

    An anchor is a card no mint pass derived — the hand-authored records read out of
    Andreas and the research passes — carrying a trade, a dwelling or a premises. It is
    what a bare forename or a contradicted middle initial is allowed to attach to.
    """
    if doc.get("source_pass"):
        return False
    occupation = (person.get("occupation") or {}).get("value")
    return bool(person.get("resident_research")
                or (occupation and occupation != "none_recorded")
                or (doc.get("lives_at") or {}).get("value")
                or (doc.get("works_at") or {}).get("value"))


def pair_evidence(a: dict, b: dict) -> dict:
    """The evidence FOR and AGAINST one pair of cards, read off the records."""
    pa, pb = a["record"], b["record"]
    sa, sb = set(pa.get("sources") or []), set(pb.get("sources") or [])
    oa = (pa.get("occupation") or {}).get("value")
    ob = (pb.get("occupation") or {}).get("value")
    ta = [t for t in a["parsed"][1]]
    tb = [t for t in b["parsed"][1]]
    for_, against = [], []
    shared = sorted(sa & sb)
    if shared:
        for_.append(f"share {len(shared)} source(s): {', '.join(shared)}")
    if ta and tb and ta[0] == tb[0]:
        for_.append(f"the same forename, '{ta[0]}'")
    elif ta and tb and (len(ta[0]) == 1 or len(tb[0]) == 1):
        for_.append(f"an initial against its forename, '{ta[0]}' and '{tb[0]}'")
    elif not ta or not tb:
        for_.append("one card prints a title and no forename at all")
    if oa and ob and oa == ob and oa != "none_recorded":
        for_.append(f"the same trade, {oa}")
    if anchored(pa, a["doc"]):
        for_.append(f"{a['person']} is an anchor — the town documents this person")
    if anchored(pb, b["doc"]):
        for_.append(f"{b['person']} is an anchor — the town documents this person")
    mid_a = [t for t in ta[1:] if len(t) == 1]
    mid_b = [t for t in tb[1:] if len(t) == 1]
    if mid_a and mid_b and mid_a[0] != mid_b[0]:
        against.append(f"the middle initial contradicts: '{mid_a[0]}' against '{mid_b[0]}'")
    if ta and tb and len(ta[0]) > 1 and len(tb[0]) > 1 and ta[0] != tb[0]:
        against.append(f"two full forenames that are different words: "
                       f"'{ta[0]}' and '{tb[0]}'")
    if oa and ob and "none_recorded" not in (oa, ob) and oa != ob:
        against.append(f"two trades that disagree: {oa} and {ob}")
    if a["household"] == b["household"]:
        against.append(f"both stand on one household record, {a['household']} — "
                       f"the sources name them together, not twice")
    if not (anchored(pa, a["doc"]) or anchored(pb, b["doc"])):
        against.append("neither card is an anchor: nothing here documents the person "
                       "beyond a list")
    return {"a": a["person"], "b": b["person"], "for": for_, "against": against}


# ---------------------------------------------------------------------------
# the rulings

def load_rulings() -> dict:
    """The rulings, each stamped with the ticket that MADE it and the day it was made.

    T-0839 wrote this file and is the default, but a ruling a later ticket rewrote is
    that ticket's claim and not T-0839's — T-0844 re-ruled the six clusters T-0839
    referred to the owner. Stamping here means the stub, the redirect table, the
    crosswalk and the on-card block all name the pass to argue with, without every
    writer below having to know about the ledger. In memory only: nothing writes this
    file back.
    """
    doc = json.loads(RULINGS.read_text(encoding="utf-8"))
    when = {row.get("ticket"): row.get("on")
            for row in doc.get("also_ruled_on") or [] if row.get("ticket")}
    for cluster in doc.get("clusters", []):
        for ruling in cluster.get("rulings", []):
            ticket = ruling.get("ticket") or TICKET
            ruling["ticket"] = ticket
            ruling["on"] = (ruling.get("on")
                            or (doc.get("ruled_on") if ticket == TICKET else None)
                            or when.get(ticket) or RULED_ON)
    return doc


def ruled_cards(rulings: dict) -> dict:
    """person_id -> the ruling that covers it. A card may be named by more than one
    ruling in its cluster (a survivor is also weighed against the people it is NOT);
    the merge ruling wins, because it is the one that moves a card."""
    out = {}
    for row in rulings.get("deferred", []):
        for pid in row.get("cards", []):
            out.setdefault(pid, {"state": "deferred", "cluster": row["cluster"],
                                 "to": row.get("to"), "why": row.get("why")})
    for cluster in rulings.get("clusters", []):
        for ruling in cluster.get("rulings", []):
            members = ([ruling["survivor"]] + list(ruling.get("folded") or [])
                       if ruling["state"] == "merge" else list(ruling.get("members") or []))
            for pid in members:
                if ruling["state"] == "merge" or pid not in out:
                    out[pid] = dict(ruling, cluster=cluster["id"], surname=cluster["surname"])
    return out


def merges(rulings: dict) -> list:
    out = []
    for cluster in rulings.get("clusters", []):
        for ruling in cluster.get("rulings", []):
            if ruling["state"] == "merge":
                out.append(dict(ruling, cluster=cluster["id"], surname=cluster["surname"]))
    return sorted(out, key=lambda r: r["survivor"])


def coverage_problems(town: list, rulings: dict) -> list:
    """Every card in a candidate cluster owes a written ruling. This is the gate that
    makes a re-split visible: a new card lands in a cluster, carries no ruling, red."""
    known = ruled_cards(rulings)
    problems = []
    for cluster in clusters(town):
        for card in cluster["cards"]:
            if card["person"] not in known:
                problems.append(
                    f"'{card['person']}' ({card['name']!r}, on {card['household']}) stands "
                    f"in a candidate cluster with "
                    f"{', '.join(c['person'] for c in cluster['cards'] if c is not card)} "
                    f"and carries no ruling in data/residents/card_merge_rulings.json. "
                    f"{TICKET}: rule it MERGE, DISTINCT or UNDECIDED before it ships — a "
                    f"card that nobody has weighed is how one man came to stand on six.")
    return problems


# ---------------------------------------------------------------------------
# the ledger

def dump(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def ledger_doc(town: list, rulings: dict) -> dict:
    known = ruled_cards(rulings)
    by_person = {r["person"]: r for r in town}
    rows = []
    for cluster in clusters(town):
        cards = cluster["cards"]
        pairs = [pair_evidence(cards[i], cards[j])
                 for i in range(len(cards)) for j in range(i + 1, len(cards))]
        rows.append({
            "surname": cluster["surname"],
            "cards": [{"person": c["person"], "household": c["household"],
                       "name": c["name"],
                       "anchor": anchored(c["record"], c["doc"]),
                       "sources": sorted(c["record"].get("sources") or []),
                       "ruling": (known.get(c["person"]) or {}).get("state"),
                       "ruled_in": (known.get(c["person"]) or {}).get("cluster")}
                      for c in cards],
            "pairs": pairs,
        })
    landed = []
    for ruling in merges(rulings):
        survivor = by_person.get(ruling["survivor"])
        landed.append({
            "cluster": ruling["cluster"],
            "survivor": ruling["survivor"],
            "survivor_household": survivor["household"] if survivor else None,
            "survivor_on_the_cards": survivor is not None,
            "folded": list(ruling["folded"]),
            "rule": ruling["rule"],
        })
    states = defaultdict(int)
    for cluster in rulings.get("clusters", []):
        for ruling in cluster.get("rulings", []):
            key = ruling["state"]
            if key == "undecided":
                key = f"undecided_{ruling.get('referred_to', 'owner')}"
            states[key] += 1
    return {
        "schema": "town-card-candidates/1",
        "_doc": "T-0839. Every cluster of town cards that a surname-plus-compatible-"
                "forename test joins, with the evidence each pair is weighed on and the "
                "written ruling that covers it. DERIVED — regenerate with "
                "tools/consolidate_town_cards.py --apply; the rulings themselves are "
                "hand-authored in data/residents/card_merge_rulings.json. A cluster that "
                "survives here is one whose cards were ruled DISTINCT or UNDECIDED: the "
                "merges are gone from this list because their cards are gone from the "
                "town.",
        "generated_by": GENERATED_BY,
        "ticket": TICKET,
        "counts": {
            "town_people": len(town),
            "open_clusters": len(rows),
            "cards_in_open_clusters": sum(len(r["cards"]) for r in rows),
            "rulings": dict(sorted(states.items())),
            "landed_merges": len(landed),
            "cards_folded": sum(len(m["folded"]) for m in landed),
        },
        "landed": landed,
        "clusters": rows,
    }


def landed_record_ids(folded: str) -> list:
    """What a PREVIOUS write of this crosswalk already declared for a folded card.

    THE FIXED POINT, and without it this pass oscillates. `appearances_of` finds a
    letter-list card's appearance on the ORPHAN identity the fold leaves behind — and the
    moment `consolidate_resident_evidence.py` reads this crosswalk and honours it, that
    appearance MOVES onto the survivor's identity and the orphan is gone. The next write
    would then find nothing, empty the row, and the appearance would move back: the two
    passes would trade the same fact back and forth for ever and `--check` would never be
    green twice running. Measured on T-1134, which is where it was found.

    So a declaration is KEPT. That is not a cache and it is not a hand edit — it is what a
    LANDED adjudication means here: this pass has already said, in a committed file, which
    records the folded card brought to the merge, and the evidence for that statement is
    consumed by the act of honouring it. The row is still fully derived in the sense that
    matters: it exists only while `merges()` holds the ruling, so withdrawing a ruling
    still deletes the row outright, and nothing stale can outlive its merge.
    """
    if not CROSSWALK.exists():
        return []
    try:
        doc = json.loads(CROSSWALK.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    for row in doc.get("merges") or []:
        if row.get("folded_person_id") != folded:
            continue
        domains = [d for d in (row.get("domains") or []) if isinstance(d, str)]
        return [{"domain": domain, "record_id": rid}
                for rid in (row.get("record_ids") or []) if isinstance(rid, str)
                for domain in domains]
    return []


def appearances_of(person_id: str, name: str) -> list:
    """The identity master's own (domain, record_id) rows for a card this pass folded away.

    THE HOLE THIS CLOSES, and the gate has only ever seen it once (T-1134). A LETTER-LIST
    card carries no evidence block at all: `mint_letter_list_residents.py` writes
    `letter_list_returns` — bare dates — where every other pass writes `press_evidence`
    rows with a `record_id`. So the loop in `crosswalk_doc` gathers NOTHING from one,
    `declared_anchors()` has no (domain, record_id) to key on, the folded appearance never
    moves onto the survivor's identity, and a CIVIC survivor — which `apply()` deliberately
    does not hand-write the union onto, because the next mint would revert it — never
    learns the source. Four of the 63 landed folds are letter-list cards and three of them
    hid it: `norton_n_r`, `vanderbogart_h` and `scarritt_isaac` fold onto survivors that
    already cite the same paper for reasons of their own, so 'a merge loses nothing' held
    by luck. `anight_clark` onto `knight_clark` is the first whose survivor cites no paper
    at all, and --check said so.

    HOW A FOLDED CARD IS FOUND IN THE MASTER, and why it is a match and not a guess. The
    fold removes the card, so the identity it was minted from is left with NO
    `canonical_person_id` — an orphan, one of several thousand. The name is what joins
    them, and it is an EXACT join: the master keys an identity on the surname and the
    forename tokens `split_name_or_reason` reads, this pass parses the folded card's own
    name with the same function, and the match must be on both AND be UNIQUE among the
    orphans. Anything else — no orphan of that name, or two — returns nothing and the
    behaviour is exactly what it was, which is what `norton_n_r` and `vanderbogart_h` do
    today: their printed names ('N. R. Norton', 'H. Vanderbogart') parse to forenames the
    master does not carry, and neither needs this, because neither's survivor lost a source.

    The master is written at step 20 of `tools/rederive.mjs --run` and this pass is step
    23, so a chain run has it on disk before this reads it; a NEW fold reaches the
    crosswalk on the second pass, which is what 'iterated to a fixed point' has always
    meant here. Missing or unreadable, this returns nothing.
    """
    if not IDENTITY_MASTER.exists():
        return []
    try:
        doc = json.loads(IDENTITY_MASTER.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return []
    rows = [r for r in (doc if isinstance(doc, list) else doc.get("identities") or [])
            if isinstance(r, dict)]
    held = [r for r in rows
            if r.get("canonical_person_id") == person_id
            or person_id in (r.get("town_person_ids") or [])]
    if held:
        found = held
    else:
        parsed, _ = split_name_or_reason(name or "")
        if not parsed:
            return []
        surname, given = parsed
        key = (surname, " ".join(given))
        found = [r for r in rows
                 if not r.get("canonical_person_id")
                 and (r.get("surname"), r.get("forename")) == key]
        if len(found) != 1:
            return []
    out = []
    for row in found:
        for appearance in row.get("appearances") or []:
            domain = appearance.get("domain")
            rid = appearance.get("record_id")
            if not domain or not rid or domain == "residents" or rid == person_id:
                continue
            out.append({"domain": domain, "record_id": rid})
    return out


def crosswalk_doc(rulings: dict) -> dict:
    """THE LANDED ADJUDICATION, in the shape consolidate_resident_evidence.py reads.

    One row per folded card, naming the survivor and every source record the folded card
    cited. `declared_anchors()` keys on (domain, record_id) and moves the appearance onto
    the identity that holds `person_id`, which is what joins the identities, regrades the
    man and stops the mint re-writing the card it just lost.
    """
    rows = []
    for ruling in merges(rulings):
        for folded in sorted(ruling["folded"]):
            stub = MERGED / f"{household_of_stub(folded)}.json"
            record_ids, sources = [], set()
            if stub.exists():
                doc = json.loads(stub.read_text(encoding="utf-8"))
                record = doc.get("superseded_record") or doc
                person = next((p for p in record.get("persons") or []
                               if p.get("id") == folded), None) or {}
                sources = set(person.get("sources") or [])
                for key in BLOCK_KEYS:
                    for entry in person.get(key) or []:
                        rid = entry.get("record_id")
                        if not rid:
                            continue
                        for domain in BLOCK_DOMAINS[key]:
                            record_ids.append({"domain": domain, "record_id": rid})
                if not record_ids:
                    record_ids += (appearances_of(folded, person.get("name") or "")
                                   or landed_record_ids(folded))
            rows.append({
                "outcome": "merged",
                "person_id": ruling["survivor"],
                "folded_person_id": folded,
                "rule": ruling["rule"],
                "cluster": ruling["cluster"],
                "record_ids": sorted({r["record_id"] for r in record_ids}),
                "domains": sorted({r["domain"] for r in record_ids}),
                "sources": sorted(sources),
                "evidence": f"{ruling.get('ticket') or TICKET}: '{folded}' and "
                            f"'{ruling['survivor']}' are one "
                            f"person under rule {ruling['rule']}; the ruling and its "
                            f"reasoning are in data/residents/card_merge_rulings.json "
                            f"under cluster '{ruling['cluster']}'.",
            })
    return {
        "schema": "card-merge-crosswalk/1",
        "_doc": "T-0839. The town cards ruled to be one person, as a LANDED ADJUDICATION "
                "the consolidation reads. consolidate_resident_evidence.py's "
                "declared_anchors() walks every *crosswalk*.json under data/research/ and "
                "moves each anchored appearance onto the identity that holds `person_id`, "
                "so the folded card's sources reach the survivor, the ladder regrades the "
                "joined identity, and mint_civic_residents.py refuses to re-mint a card "
                "whose identity now has a canonical person it does not own. DERIVED from "
                "the rulings and the redirect stubs — do not hand-edit.",
        "generated_by": GENERATED_BY,
        "ticket": TICKET,
        "merges": rows,
    }


def household_of_stub(person_id: str) -> str:
    """The household a folded person stood on, asked of the redirect table."""
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    for row in index.get("merged", []):
        if row["person"] == person_id:
            return row["household"]
    return ""


# ---------------------------------------------------------------------------
# landing it

def stub_doc(doc: dict, person_id: str, ruling: dict, survivor_household: str) -> dict:
    """The folded record, WHOLE, with the redirect written on the front of it."""
    out = {
        "id": doc["id"],
        "merged_into": {
            "person": ruling["survivor"],
            "household": survivor_household,
            "person_merged": person_id,
            "rule": ruling["rule"],
            "cluster": ruling["cluster"],
            "ticket": ruling.get("ticket") or TICKET,
            "on": ruling.get("on") or RULED_ON,
            "note": "THIS RECORD IS NOT DELETED AND NOTHING ON IT IS LOST. The card below "
                    "is the record exactly as it stood when the merge landed; the person "
                    "it names is now carried by the household above, and "
                    "data/residents/index.json's `merged` table redirects the id. "
                    "The reasoning is in data/residents/card_merge_rulings.json.",
        },
        "superseded_record": doc,
    }
    return out


def merge_ruling_block(ruling: dict, this: str, others: list) -> dict:
    state = ruling["state"]
    block = {
        "ticket": ruling.get("ticket") or TICKET,
        # `verdict`, not `state`: tools/measure_layer_reads.py matches a figure's leaf
        # name against the renderer's property accesses, and `.state` is a word the
        # walk uses everywhere, so a key called `state` reads as shipped-and-drawn
        # when nothing draws it.
        "verdict": state,
        "rule": ruling["rule"],
        "cluster": ruling["cluster"],
        "weighed_against": sorted(p for p in others if p != this),
    }
    if state == "undecided":
        block["referred_to"] = ruling.get("referred_to", "owner")
    block["for_merge"] = ruling.get("for_merge", "")
    block["against_merge"] = ruling.get("against_merge", "")
    return block


def apply(write: bool = True) -> dict:
    """Land every ruling. Returns {path: text} of everything it would write."""
    rulings = load_rulings()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    docs = {p.stem: json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(HOUSEHOLDS.glob("*.json"))}
    home = {person["id"]: hid for hid, doc in docs.items()
            for person in doc.get("persons") or []}
    stub_home = {row["person"]: row["household"] for row in index.get("merged", [])}

    files: dict = {}
    folded_households: set = set()

    for ruling in merges(rulings):
        survivor_home = home.get(ruling["survivor"])
        if survivor_home is None:
            continue                     # already landed on an earlier run
        survivor_doc = docs[survivor_home]
        survivor = next(p for p in survivor_doc["persons"]
                        if p["id"] == ruling["survivor"])
        gained_sources, gained_blocks = set(), defaultdict(list)
        for folded in sorted(ruling["folded"]):
            hid = home.get(folded)
            if hid is None:
                # ALREADY FOLDED ON AN EARLIER RUN. The union is still read, out of the
                # stub, so --apply is idempotent and can repair a survivor a later
                # derivation stripped rather than only ever landing a merge once.
                hid = stub_home.get(folded)
                if hid is None:
                    continue
                stub = json.loads((MERGED / f"{hid}.json").read_text(encoding="utf-8"))
                person = next(p for p in (stub.get("superseded_record") or {}
                                          ).get("persons") or [] if p["id"] == folded)
                # …AND A RULING THAT CHANGED ITS MIND IS FOLLOWED (T-0855).
                #
                # Reading the stub was all this branch used to do, so a card folded onto
                # the WRONG survivor could not be corrected: rewrite the ruling, re-run
                # --apply, and the stub and the redirect table went on naming the old
                # survivor. The ruling said one thing and the data said another, which is
                # this project's oldest failure shape, and --check could not see it
                # because it never compared the two.
                #
                # That is not hypothetical. T-0839 folded `hubbard_g` onto Gurdon
                # Saltonstall Hubbard when that card's own and only press evidence reads
                # "Hubbard, [Henry] G." and cites person_hubbard_henry_g — a different,
                # attested man on the same tree. Correcting it is what found this.
                landed = stub.get("merged_into") or {}
                if landed.get("person") != ruling["survivor"]:
                    stub["merged_into"] = dict(landed, person=ruling["survivor"],
                                               household=survivor_home,
                                               rule=ruling["rule"],
                                               cluster=ruling["cluster"],
                                               ticket=ruling.get("ticket") or TICKET,
                                               repointed_from=landed.get("person"))
                    files[MERGED / f"{hid}.json"] = dump(stub)
            else:
                doc = docs[hid]
                person = next(p for p in doc["persons"] if p["id"] == folded)
                files[MERGED / f"{hid}.json"] = dump(
                    stub_doc(doc, folded, ruling, survivor_home))
                folded_households.add(hid)
            gained_sources |= set(person.get("sources") or [])
            for key in BLOCK_KEYS:
                for entry in person.get(key) or []:
                    gained_blocks[key].append(entry)
        # THE UNION, but only where nothing else will write it. `mint_civic_residents.py`
        # derives its whole card from the identity master, and the crosswalk above has
        # already put the folded appearances INTO that identity — so a civic survivor
        # carries the union without being touched here, and writing it here as well would
        # be a hand-edit the next --build reverts and --check calls stale. Every other
        # card — hand-authored, or minted by a pass that reads its own pool rather than
        # the master — gains nothing unless this pass writes it, so it is written.
        if survivor_doc.get("source_pass") == "civic":
            continue
        if gained_sources or gained_blocks:
            survivor["sources"] = sorted(set(survivor.get("sources") or [])
                                         | gained_sources)
            for key in BLOCK_KEYS:
                if not gained_blocks[key]:
                    continue
                have = {json.dumps(e, sort_keys=True) for e in survivor.get(key) or []}
                add = [e for e in gained_blocks[key]
                       if json.dumps(e, sort_keys=True) not in have]
                survivor[key] = (survivor.get(key) or []) + sorted(
                    add, key=lambda e: (str(e.get("describes_date") or ""),
                                        str(e.get("record_id") or "")))
            # ONE SURVIVOR, MORE THAN ONE FOLD — a LIST, keyed by cluster (T-1026).
            #
            # This was a dict, written straight over whatever stood there, and it held
            # for as long as no card was the survivor of two rulings. `beaubien_madore`
            # is the first: T-1002 folded `beaubien_medore_b` onto it from the
            # `beaubien-madore` cluster under C11, and T-1026 folds `beaubien_medard`
            # onto it from `beaubien-medard` under C12. The second --apply erased the
            # first ruling's row, so the card carried the T-1026 fold and no trace of
            # the T-1002 one — the sources and evidence blocks of a merge the project
            # had made and argued, with nothing on the card to say where they came
            # from. A survivor may be the answer to any number of clusters and the card
            # has to say so once per cluster, which is exactly what `merge_ruling`
            # below has always done for the DISTINCT and UNDECIDED rows.
            #
            # Re-running a cluster REPLACES that cluster's row and leaves the others, so
            # --apply stays idempotent and a re-ruled cluster is followed rather than
            # doubled.
            block = {
                "ticket": ruling.get("ticket") or TICKET,
                "rule": ruling["rule"],
                "cluster": ruling["cluster"],
                "cards": sorted(ruling["folded"]),
                "note": "THE UNION OF THE CARDS THIS PERSON WAS SPLIT ACROSS. The sources "
                        "and evidence blocks above include everything the folded cards "
                        "cited; each folded record is kept whole under "
                        "data/residents/merged/ and is redirected by index.json's "
                        "`merged` table. The reasoning for the merge is in "
                        "data/residents/card_merge_rulings.json.",
            }
            was = survivor.get("merged_from")
            rows = [b for b in (was if isinstance(was, list) else [was] if was else [])
                    if b.get("cluster") != ruling["cluster"]]
            survivor["merged_from"] = sorted(rows + [block],
                                             key=lambda b: b["cluster"])
            files[HOUSEHOLDS / f"{survivor_home}.json"] = dump(survivor_doc)

    # the written DISTINCT and UNDECIDED rulings, onto the cards themselves
    for cluster in rulings.get("clusters", []):
        for ruling in cluster.get("rulings", []):
            if ruling["state"] not in ("distinct", "undecided"):
                continue
            members = list(ruling.get("members") or [])
            for pid in members:
                hid = home.get(pid)
                if hid is None or hid in folded_households:
                    continue
                doc = docs[hid]
                person = next(p for p in doc["persons"] if p["id"] == pid)
                block = merge_ruling_block(dict(ruling, cluster=cluster["id"]),
                                           pid, members)
                existing = person.get("merge_ruling")
                rows = [b for b in (existing if isinstance(existing, list) else
                                    [existing] if existing else [])
                        if b.get("cluster") != cluster["id"]]
                person["merge_ruling"] = sorted(rows + [block],
                                                key=lambda b: b["cluster"])
                files[HOUSEHOLDS / f"{hid}.json"] = dump(doc)

    # the index: the folded rows out, the redirect table left to its owner
    index["households"] = [r for r in index["households"]
                           if r["id"] not in folded_households]
    index["_merged_doc"] = (
        "T-0839. THE REDIRECT TABLE. One row per town card folded onto another "
        "because the two named one person. The record is not deleted: it is kept "
        "whole at the `record` path with a `merged_into` block, and this table is "
        "what lets every consumer that cites the folded `person` — the crosswalks, "
        "identity_master.json, the smoke cohorts, the placed-resident parcels — "
        "still resolve it to somebody. The ruling and its reasoning are in "
        "data/residents/card_merge_rulings.json. T-1144 acceptance 6: THIS TABLE IS "
        "DERIVED, from the `merged_into` block of each record under "
        "data/residents/merged/ and from nothing else — tools/"
        "rebuild_resident_index.py writes it and tools/check.sh re-derives it, the "
        "same rule T-0715 put on `households` and `counts`. It is not a place to "
        "patch a redirect: the record is. The gate also refuses a redirect that does "
        "not ARRIVE — a `merged_into_household` or `merged_into_person` that is in no "
        "household card, a redirect onto another retired card, or a retired id that "
        "is also a live one.")
    # THE MANIFEST HAS AN OWNER (T-0715) and this pass is not it. Every row and every
    # derived count comes back from the cards through that tool, over the whole layer as
    # this pass will leave it.
    #
    # THAT NOW INCLUDES THE REDIRECT TABLE (T-1144 acceptance 6). This pass used to
    # write `merged` itself, by carrying the manifest's own previous rows forward and
    # laying this run's redirects on top:
    #
    #     prior = {row["person"]: row for row in index.get("merged", [])}
    #
    # A row that was never right was therefore right for ever, and a record retired by
    # any other route got no row at all — which is exactly what `dev` was carrying:
    # `hh_blanchard_gantry` under the rule letter T-0993 superseded in the same ticket,
    # and `hh_vanderbogart_h` with no row, resolving to nothing. The table is derived
    # from the retired records now, so the map below hands the owner BOTH halves of the
    # layer as this pass will leave it: the households it keeps, and the retired
    # records — the ones already committed, plus the ones this run is about to write,
    # which are not on disk yet and would otherwise be missing from their own table.
    import rebuild_resident_index
    after = {HOUSEHOLDS / f"{hid}.json": doc for hid, doc in docs.items()
             if hid not in folded_households}
    after.update(rebuild_resident_index.load_retired())
    after.update({path: doc for path, doc in files.items()
                  if path.parent.name == "merged"})
    files[INDEX] = dump(rebuild_resident_index.rebuild(index, after))

    if write:
        MERGED.mkdir(parents=True, exist_ok=True)
        for path, text in sorted(files.items()):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        for hid in sorted(folded_households):
            (HOUSEHOLDS / f"{hid}.json").unlink(missing_ok=True)
        # the ledger and the crosswalk are derived from the LANDED tree
        town = read_town()
        LEDGER.write_text(dump(ledger_doc(town, rulings)), encoding="utf-8")
        CROSSWALK.write_text(dump(crosswalk_doc(rulings)), encoding="utf-8")
        files[LEDGER] = LEDGER.read_text(encoding="utf-8")
        files[CROSSWALK] = CROSSWALK.read_text(encoding="utf-8")
    return files


# ---------------------------------------------------------------------------
# the gate

def check() -> int:
    problems = []
    rulings = load_rulings()
    town = read_town()
    problems += coverage_problems(town, rulings)

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    people = {r["person"] for r in town}
    for row in index.get("merged", []):
        if row["merged_into_person"] not in people:
            problems.append(f"the redirect for '{row['person']}' points at "
                            f"'{row['merged_into_person']}', who is on no card — a "
                            f"person_id a crosswalk cites would stop resolving")
        path = RESIDENTS / row["record_file"]
        if not path.exists():
            problems.append(f"'{row['person']}' redirects to {row['record_file']}, which is "
                            f"not in the tree — the folded record has been LOST, and "
                            f"'a merge loses nothing' is the one promise this pass made")
        if row["person"] in people:
            problems.append(f"'{row['person']}' is both folded away and back on a card: "
                            f"the identity has been re-split")

    for ruling in merges(rulings):
        for folded in ruling["folded"]:
            if folded in people:
                problems.append(f"'{folded}' is ruled merged onto '{ruling['survivor']}' "
                                f"and is still a person on the cards; run --apply")
        if ruling["survivor"] not in people:
            problems.append(f"the survivor '{ruling['survivor']}' of cluster "
                            f"'{ruling['cluster']}' is on no card")

    # T-0855, AND IT IS TWO COPIES OF ONE FACT DISAGREEING, WHICH IS THIS PROJECT'S
    # OLDEST FAILURE SHAPE. The ruling names a survivor and so does the landed redirect,
    # and nothing compared them. So a CORRECTED ruling did not land: --apply's
    # already-folded branch only read the stub, the redirect table kept its old row, and
    # --check passed while card_merge_rulings.json said Henry and the data said Gurdon.
    # A ruling nobody can act on is not a ruling.
    landed_target = {row["person"]: row["merged_into_person"]
                     for row in index.get("merged", [])}
    for ruling in merges(rulings):
        for folded in ruling["folded"]:
            landed = landed_target.get(folded)
            if landed is not None and landed != ruling["survivor"]:
                problems.append(
                    f"'{folded}' is RULED onto '{ruling['survivor']}' but the redirect "
                    f"table lands it on '{landed}'. The ruling and the data disagree; "
                    f"run --apply, which now re-points a corrected fold")
        for row in index.get("merged", []):
            if row["person"] not in ruling["folded"]:
                continue
            stub_file = RESIDENTS / row["record_file"]
            if not stub_file.exists():
                continue
            got = (json.loads(stub_file.read_text(encoding="utf-8")
                              ).get("merged_into") or {}).get("person")
            if got != ruling["survivor"]:
                problems.append(
                    f"{row['record_file']} says it was merged into '{got}', but the "
                    f"ruling for '{row['person']}' says '{ruling['survivor']}'")

    # …AND THE RULING MUST AGREE WITH THE CARD'S OWN TRANSCRIPTION (T-0855).
    #
    # A reading like "Hubbard, [Henry] G." carries a BRACKETED forename: somebody looked
    # at the page and said who this is. That is evidence about identity, not spelling, and
    # a fold that contradicts it is putting one man's record on another man. Exactly that
    # happened — hubbard_g, whose only press evidence reads "[Henry]" and cites
    # person_hubbard_henry_g, was folded onto hubbard_gurdon while Henry stood attested on
    # his own card two files away.
    #
    # Measured over the 42 folded records the day this was written: ONE tripped it, the
    # one above. So this is a narrow check with a real catch, not a net cast at a guess.
    for row in index.get("merged", []):
        stub_file = RESIDENTS / row["record_file"]
        if not stub_file.exists():
            continue
        stub = json.loads(stub_file.read_text(encoding="utf-8"))
        survivor_id = row["merged_into_person"]
        for person in (stub.get("superseded_record") or {}).get("persons") or []:
            for key in BLOCK_KEYS:
                for entry in person.get(key) or []:
                    named = bracket_conflict(entry.get("as_read"), survivor_id)
                    if named:
                        problems.append(
                            f"'{row['person']}' is folded onto '{survivor_id}', but its "
                            f"{key} reads {entry.get('as_read')!r} — the transcriber "
                            f"bracketed the forename '{named}', which names "
                            f"somebody else. A bracket is a reading of the page and "
                            f"outranks an inference from the initial (rule C5)")

    # THE UNION IS STILL ON THE SURVIVOR. Where the survivor is a card no derivation
    # spends onto, --apply wrote the folded cards' sources by hand; a later --build of the
    # pass that owns it would re-derive them away silently, and this is what says so.
    by_person = {r["person"]: r["record"] for r in town}
    for row in index.get("merged", []):
        survivor = by_person.get(row["merged_into_person"])
        if survivor is None:
            continue
        stub = RESIDENTS / row["record_file"]
        if not stub.exists():
            continue
        record = json.loads(stub.read_text(encoding="utf-8")).get("superseded_record") or {}
        folded = next((p for p in record.get("persons") or []
                       if p["id"] == row["person"]), {})
        lost = sorted(set(folded.get("sources") or []) - set(survivor.get("sources") or []))
        if lost:
            problems.append(
                f"'{row['merged_into_person']}' no longer cites "
                f"{', '.join(lost)}, which '{row['person']}' brought to the merge. A "
                f"merge loses nothing: run --apply to write the union back")

    want = {LEDGER: dump(ledger_doc(town, rulings)),
            CROSSWALK: dump(crosswalk_doc(rulings))}
    for path, text in want.items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            problems.append(f"{path.relative_to(ROOT)} does not re-derive; run --apply")

    for problem in problems:
        print(f"   {problem}")
    if problems:
        print(f"   {len(problems)} problem(s)")
        return 1
    landed = sum(len(m["folded"]) for m in merges(rulings))
    print(f"   OK: {len(town)} person(s) on the cards, {landed} card(s) folded and "
          f"redirected, every card in a candidate cluster carries a written ruling")
    return 0


def report() -> None:
    rulings, town = load_rulings(), read_town()
    doc = ledger_doc(town, rulings)
    print(json.dumps(doc["counts"], indent=1))
    for cluster in doc["clusters"]:
        print(f"\n{cluster['surname']}  ({len(cluster['cards'])} cards)")
        for card in cluster["cards"]:
            print(f"   {card['ruling'] or 'UNRULED':<10} {card['person']:<38} "
                  f"{card['name']}")


# ---------------------------------------------------------------------------

def self_test() -> int:
    fails = []

    def ok(cond, why):
        if not cond:
            fails.append(why)

    ok(compatible(("allen", ["james"]), ("allen", ["j"])),
       "an initial must attach to the forename it begins")
    ok(compatible(("allen", ["james"]), ("allen", [])),
       "a title-only card must be compatible with every card of its surname")
    ok(not compatible(("cook", ["john"]), ("cook", ["josiah"])),
       "two different full forenames are never compatible")
    ok(forename_tokens("Lieut. James Allen") == ("allen", ["james"]),
       "a rank must be stripped from the forename tokens")
    ok(forename_tokens("Dr Edmund Stoughton Kimberly") == ("kimberly",
                                                           ["edmund", "stoughton"]),
       "an honorific must be stripped from the forename tokens")

    rows = [
        {"household": "hh_a", "person": "a_james", "name": "James Allen",
         "doc": {"id": "hh_a"}, "record": {"id": "a_james"}},
        {"household": "hh_b", "person": "a_j", "name": "J Allen",
         "doc": {"id": "hh_b"}, "record": {"id": "a_j"}},
        {"household": "hh_c", "person": "b_mary", "name": "Mary Brown",
         "doc": {"id": "hh_c"}, "record": {"id": "b_mary"}},
    ]
    found = clusters(rows)
    ok(len(found) == 1 and len(found[0]["cards"]) == 2,
       "the candidate test must join the two Allens and leave the Brown alone")

    ok(coverage_problems(rows, {"clusters": []}),
       "a cluster with no ruling must be a problem — this is the gate that catches a "
       "re-split, and it has to fire")
    ok(not coverage_problems(rows, {"clusters": [
        {"id": "allen", "surname": "allen", "rulings": [
            {"state": "merge", "rule": "C1", "survivor": "a_james", "folded": ["a_j"]}]}]}),
       "a cluster whose cards are all ruled must not be a problem")

    pair = pair_evidence(
        {"person": "x", "household": "h", "parsed": ("hunt", ["c", "s"]),
         "record": {"sources": ["s1"]}, "doc": {}},
        {"person": "y", "household": "h2", "parsed": ("hunt", ["charles", "c"]),
         "record": {"sources": ["s1"]}, "doc": {}})
    ok(any("middle initial contradicts" in a for a in pair["against"]),
       "a contradicted middle initial must be read as evidence AGAINST")
    ok(any("share 1 source" in f for f in pair["for"]),
       "a shared source must be read as evidence FOR")

    # T-0855 — the transcriber's bracket. This is the rule that would have caught
    # hubbard_g being folded onto Gurdon, so it is the one that must not rot.
    ok(bracket_conflict("Hubbard, [Henry] G.", "hubbard_gurdon") == "Henry",
       "a bracketed forename that is not the survivor's must be a conflict — this is "
       "the real case: hubbard_g read '[Henry]' and was folded onto Gurdon")
    ok(bracket_conflict("Hubbard, [Henry] G.", "hubbard_henry_g") is None,
       "…and the same reading onto the man it names must be silent, or the check "
       "fires for ever and gets switched off")
    ok(bracket_conflict("G. S. Hubbard", "hubbard_gurdon") is None,
       "a reading with no bracket says nothing about identity and must not be judged")
    ok(bracket_conflict("Allen, [Lieut] James", "allen_james") is None,
       "a bracketed RANK is not a forename — this is the false positive the check "
       "would have shipped without its guard")
    ok(bracket_conflict("", "anybody") is None and bracket_conflict(None, "x") is None,
       "an absent reading must not raise")

    for fail in fails:
        print(f"   {fail}")
    print(f"   {'OK: every assertion holds' if not fails else f'{len(fails)} failed'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--candidates", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.report:
        report()
        return 0
    if args.check:
        return check()
    if args.candidates:
        LEDGER.parent.mkdir(parents=True, exist_ok=True)
        LEDGER.write_text(dump(ledger_doc(read_town(), load_rulings())), encoding="utf-8")
        print(f"wrote {LEDGER.relative_to(ROOT)}")
        return 0
    if args.apply:
        files = apply(write=True)
        print(f"wrote {len(files)} file(s)")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
