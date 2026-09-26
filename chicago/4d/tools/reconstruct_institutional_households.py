#!/usr/bin/env python3
"""T-1531, stage `institutional_households` — the people who slept at the town's institutions.

    python3 tools/reconstruct_institutional_households.py --build      draw them, write the cards
    python3 tools/reconstruct_institutional_households.py --check      re-derive and refuse drift
    python3 tools/reconstruct_institutional_households.py --report     what was adjudicated, and why
    python3 tools/reconstruct_institutional_households.py --self-test  the rules, each refusing its case

WHAT THIS STAGE IS, AND THE ARITHMETIC THAT MADE IT NECESSARY. The household quota
apportions the town model's 643 households across the roof groups by ROOF COUNT, and the
`institutional_public` row carries nine standing roofs — four places of worship or meeting,
two schools, three civic buildings. Weighted like that the group drew TWELVE households:
more than one per roof, in a group most of whose roofs are a church, a jail, a council
house or a light tower. Nobody had ever asked the roofs the question. T-1476 made the
quota speak (it had read `0 owed` while the count was taken against records rather than
houses) and the twelve appeared, ordered from a ticket nobody could claim.

`data/reconstruction/1835_institutional_lodging.json` is that question asked once of each
of the nine roofs, out of the committed record's own `function`, `occupants` and
`research_note` blocks. TWO of the nine hold a household:

  * `watkins_school_house` (north) — the record's own function is
    `dwelling_former_school_use_unattested`: a HOUSE a school was held in, not a
    school-house. A dwelling holds a household; who was in it in 1835 is unattested.
  * `chicago_lighthouse_1832` (south) — the keepership is recorded at "$350 a year WITH
    QUARTERS" and no keeper's dwelling is modelled, so the quarters this project can
    account for are at the light. Who kept it on 1 July 1835 is expressly not established.

The other seven are refused by name in the adjudication, each with the sentence that
refuses it. `tools/build_order_book_1835.py` weights the institutional cells on that file's
`lodging_capable_by_division`, so the book now orders TWO households where it ordered
twelve, and this stage fills both. A refusal that only lived in a ticket would have left
the book ordering ten households nobody could ever honestly write.

WHAT IS INVENTED HERE, EXACTLY. Two people, and nothing else about the two buildings. Each
is a head of their own household, carries a name from the invented pools, a `lives_at` that
is the roof the adjudication admitted, and — for the keeper alone — an occupation, which is
the appointment rather than a draw. No age is written: the household buckets carry no age
axis, so no band ordered one and this stage will not invent what nothing asked for.

NO KIN, for the reason the trade stage gives. A dwelling of this town held 4.4 people on
the 1840 histogram and the kin of a family household are `family/none` in the order book,
which is T-1171's and T-1174's quota. `household_owed` carries the drawn size, its seed and
the ticket that seats it. The keeper's quarters are the exception written rather than
taken: nothing states a family at the light and the quarters are a tower's, so no size is
drawn there and the card says why.

NO ARRIVAL, for the same circular reason every other stage of this programme gives: the
arrival model is computed over the compiled scene and the scene carries these cards.

WHERE THE CARDS LIVE. `data/residents/institutional/`, beside `readmitted/`,
`reconstructed_trades/` and `lodgers/` and for the same reason:
`data/residents/households/` is re-derived by the research mints and
`data/residents/index.json` is derived from that directory, so a reconstruction that is not
a reading lives outside both and is overlaid onto the scene by `tools/compile_scene.py`.

EVERY VALUE IS REPRODUCIBLE. Nothing is random: each value comes from `blake2s(seed)` over
a seed a reader can retype, and the seed is printed on the record that carries it.
`--check` re-derives the whole directory and refuses a single differing byte.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
MINTED = RESIDENTS / "institutional"
MODEL = DATA / "reconstruction" / "1835_town_model.json"
POOLS = DATA / "reconstruction" / "1835_invented_name_pools.json"
BOOK = DATA / "reconstruction" / "1835_reconstruction_order_book.json"
ADJUDICATION = DATA / "reconstruction" / "1835_institutional_lodging.json"
LEDGER = DATA / "reconstruction" / "1835_institutional_households.json"
STRUCTURES = DATA / "structures"

sys.path.insert(0, str(ROOT / "tools"))

STAGE = "institutional_households"
TICKET = "T-1531"
PROGRAMME_ID = "chicago_1835_resident_reconstruction"
SCENE_DATE = "1835-07-01"
RECONSTRUCTED = "reconstructed"
PREFIX = "rc_"
SOURCE_PASS = "reconstructed_institutional_household"

# What this stage writes onto each admitted roof, and NOTHING is chosen here that the
# adjudication did not already settle. `occupation` is written only where the record
# states the establishment — the keepership is an appointment, not a draw — and the sex
# rule is the roof's own evidence where it has one and the town model where it has none.
ROOFS = {
    "chicago_lighthouse_1832": {
        "household_name": "The keeper's quarters at the Chicago light",
        "occupation": "lighthouse_keeper",
        "occupation_note": (
            "THE APPOINTMENT, NOT A DEAL. The keepership of this light is recorded at "
            "$350 a year with quarters, and a light that burned every night was kept by "
            "somebody. What is reconstructed is the PERSON, not the post: the post is "
            "documented and the holder on 1 July 1835 is not. Samuel Lasby was the first "
            "keeper and Wentworth names William M. Stevens only from October 1836; no "
            "source reached covers the gap this person stands in."),
        "sex": "male",
        "sex_rule": "roof",
        "sex_note": (
            "NOT DRAWN FROM THE SEX MODEL. Every keeper of this light the sources name — "
            "Lasby, Stevens, Beaubien — is a man, and the federal appointment record this "
            "project can reach names no woman at it. That is a bound on the reconstruction "
            "rather than a reading of this person, who is not named by anything."),
        "draw_a_family": False,
        "family_note": (
            "NO SIZE IS DRAWN, AND THAT IS A REFUSAL RATHER THAN AN OVERSIGHT. The 1840 "
            "histogram is a distribution over DWELLINGS and these quarters are a light "
            "tower's; nothing states a family at the light, and drawing 4.4 people into a "
            "forty-foot tower would be the model reaching past the one thing the record "
            "gives it. A source naming the keeper's household is what fills this."),
    },
    "watkins_school_house": {
        "household_name": "The household of the Michigan Street house Watkins taught in",
        "occupation": None,
        "occupation_note": (
            "NO TRADE IS WRITTEN. The building's record says in as many words that no "
            "source reached names a householder, a tenant or a teacher in it in 1835, and "
            "the household buckets carry no trade axis to deal one from. A schoolmaster "
            "is the obvious guess and the obvious guess is exactly what this project does "
            "not write: the teaching that is attested here is Watkins's, in 1833, and he "
            "is a card of this layer already."),
        "sex": None,
        "sex_rule": "model",
        "sex_note": (
            "DRAWN, because nothing about this house says anything about who kept it. The "
            "town model's own sex ratio is the distribution and the seed below is the "
            "draw; it is a coin this project weighted, not a reading."),
        "draw_a_family": True,
        "family_note": None,
    },
}


def draw(seed: str) -> int:
    return int.from_bytes(hashlib.blake2s(seed.encode("utf-8"), digest_size=8).digest(), "big")


def unit(seed: str) -> float:
    return draw(seed) / float(1 << 64)


def pick(seed: str, weighted: list):
    total = float(sum(w for _, w in weighted))
    if total <= 0:
        raise SystemExit("a draw was asked to choose from nothing")
    at = unit(seed) * total
    run = 0.0
    for item, weight in weighted:
        run += float(weight)
        if at < run:
            return item
    return weighted[-1][0]


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ------------------------------------------------------------------ the inputs --

def adjudication() -> dict:
    return load(ADJUDICATION)


def admitted() -> list:
    """The roofs the adjudication admits, in the order it states them."""
    rows = [r for r in adjudication()["adjudication"] if r["holds_a_household"]]
    unknown = sorted(r["structure"] for r in rows if r["structure"] not in ROOFS)
    if unknown:
        raise SystemExit(
            "the adjudication admits a roof this stage has no card rule for: %s. A roof "
            "is admitted by evidence and written by a rule, and the rule is not "
            "derivable from the evidence — write it before the build runs." % unknown)
    return rows


def structure_name(sid: str) -> str:
    return load(STRUCTURES / f"{sid}.json")["name"]


def size_rows() -> list:
    for section in load(MODEL)["sections"]:
        if section["key"] == "households_and_families":
            rows = section["tables"]["size_histogram_1840"]["rows"]
            return [(int(r["size"]), int(r["households"]))
                    for r in rows if int(r["size"]) >= 1]
    raise SystemExit("the town model carries no households_and_families.size_histogram_1840")


def sex_weights() -> list:
    import build_order_book_1835 as ob  # noqa: PLC0415
    shares = ob.sex_shares(load(MODEL))
    return sorted(shares.items())


def layer() -> tuple:
    """(every name the layer bears, every person id it holds). The programme's collision
    check: an invented person may never carry an attested or inferred person's name."""
    names, ids = set(), set()
    for path in sorted(RESIDENTS.rglob("*.json")):
        if path.name == "index.json":
            continue
        # THIS STAGE'S OWN OUTPUT IS NOT PART OF THE LAYER IT CHECKS AGAINST. A draw
        # that read its own last answer as a name already borne would step past it and
        # write a different one on every build, and `--check` may not tolerate that.
        if MINTED in path.parents:
            continue
        try:
            doc = load(path)
        except json.JSONDecodeError:
            continue
        if not isinstance(doc, dict):
            continue
        for person in doc.get("persons") or []:
            if not isinstance(person, dict):
                continue
            if person.get("id"):
                ids.add(person["id"])
            if person.get("name"):
                names.add(str(person["name"]).lower())
    return names, ids


def buckets() -> dict:
    """`households/institutional/<division>` -> room left in it. THIS STAGE'S OWN FILLS
    ARE ADDED BACK, for T-1171's reason: a draw that read its own previous answer as a
    spent quota would draw fewer on the second build than on the first."""
    book = load(BOOK)
    ours = {}
    for entry in book.get("fills") or []:
        if entry.get("ticket") == TICKET:
            ours[entry.get("bucket")] = ours.get(entry.get("bucket"), 0) + int(entry.get("records") or 0)
    out = {}
    for family in book["bucket_families"]:
        if family["key"] != "households":
            continue
        for bucket in family["buckets"]:
            if bucket["axes"].get("household_type") != "institutional":
                continue
            todo = bucket.get("to_reconstruct")
            if todo is None:
                continue
            room = int(todo) - int(bucket.get("filled") or 0) + ours.get(bucket["key"], 0)
            out[bucket["key"]] = max(0, room)
    return out


# ------------------------------------------------------------------- the cards --

def card_for(row: dict, rule: dict, pool: dict, sizes: list,
             taken_names: set, taken_ids: set) -> dict:
    sid = row["structure"]
    division = row["division"]
    slot = f"{STAGE}:{sid}"
    community = {c["id"]: c for c in pool["communities"]}["yankee"]
    sex = rule["sex"] or pick(f"{slot}:sex_ratio", sex_weights())
    givens = community["given_male" if sex == "male" else "given_female"]
    surnames = community["surnames"]

    first = draw(f"{slot}:surname")
    second = draw(f"{slot}:forename")
    surname, given = surnames[first % len(surnames)], givens[second % len(givens)]
    for step_s in range(len(surnames)):
        candidate_surname = surnames[(first + step_s) % len(surnames)]
        for step_g in range(len(givens)):
            candidate_given = givens[(second + step_g) % len(givens)]
            full = f"{candidate_given} {candidate_surname}"
            pid = f"{PREFIX}{candidate_surname.lower()}_{candidate_given.lower()}"
            if full.lower() not in taken_names and pid not in taken_ids:
                surname, given = candidate_surname, candidate_given
                break
        else:
            continue
        break
    name = f"{given} {surname}"
    base = f"{PREFIX}{surname.lower()}_{given.lower()}"
    pid, suffix = base, 1
    while pid in taken_ids:
        suffix += 1
        pid = f"{base}_{suffix}"
    taken_ids.add(pid)
    taken_names.add(name.lower())

    place_name = structure_name(sid)
    bucket = f"households/institutional/{division}"
    size = pick(f"{slot}:household_size", sizes) if rule["draw_a_family"] else None

    person = {
        "id": pid,
        "name": name,
        "relationship": "head",
        "grade": RECONSTRUCTED,
        "sex": sex,
        "sex_basis": {
            "value": sex,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule" if rule["sex_rule"] == "roof" else "model",
                "id": sid if rule["sex_rule"] == "roof" else "1835_town_model",
                "note": rule["sex_note"],
            },
            "seed": None if rule["sex_rule"] == "roof" else f"{slot}:sex_ratio",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming the person who lived here on the scene date",
            },
        },
        "age_band": None,
        "occupation": {
            "value": rule["occupation"] or "none_recorded",
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED if rule["occupation"] else "unknown",
            "basis": {
                "kind": "rule",
                "id": "1835_institutional_lodging",
                "note": rule["occupation_note"],
            },
            "seed": None,
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming this establishment's holder in 1835",
            },
        },
        "name_basis": {
            "value": name,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "model",
                "id": "1835_invented_name_pools",
                "note": f"Both parts are drawn from the {community['label']} pool, which "
                        f"is seeded from the attested residents of this town. No weighting "
                        f"is applied: the adjudication says who lived under this roof and "
                        f"nothing whatever about where they came from.",
            },
            "seed": f"{slot}:forename",
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming a real person living at this building in 1835",
            },
            "note": "AN INVENTED NAME, AND IT IS NEVER EVIDENCE. No source names this "
                    "person. The name exists so a reader can tell one drawn head from "
                    "another, and it is checked against every real name in the layer.",
        },
        "basis": {
            "kind": "rule",
            "id": "1835_institutional_lodging",
            "note": f"The adjudication of the town's nine standing institutional roofs "
                    f"admits {sid} as holding a household, and the order book's bucket "
                    f"{bucket} is the one household it orders there.",
        },
        "seed": f"{slot}:forename",
        "replaceable_by": {
            "kind": "person",
            "match": "a source naming a resident of this building on the scene date, who "
                     "would stand in this slot instead",
        },
        "reconstruction": {
            "stage": STAGE,
            "programme": PROGRAMME_ID,
            "community": community["id"],
            "review_required": False,
        },
        "resident_subtype": "reconstructed_institutional_head",
        "sources": [],
        "note": f"RECONSTRUCTED, NOT FOUND. Nobody is named by any source here. This "
                f"person exists because {place_name} is one of two institutional roofs in "
                f"this town whose own committed record puts a household under it, and "
                f"because the reconstruction order book counts that household missing. "
                f"The whole of what is claimed is that somebody lived here. No figure is "
                f"drawn (L1).",
    }

    hid = f"hh_{pid}"
    return hid, {
        "id": hid,
        "name": rule["household_name"],
        "division": division,
        "head": pid,
        "source_pass": SOURCE_PASS,
        "institutional_household": {
            "ticket": TICKET,
            "stage": STAGE,
            "place": sid,
            "place_name": place_name,
            "family": row["family"],
            "bucket": bucket,
            "adjudication_tier": row["tier"],
            "stands_on": row["why"],
            "withdrawn_if": "a re-reading of this building's record that no longer puts a "
                            "household under it, or a source naming who actually lived "
                            "here; the retirement runs through --build, never by hand",
            "the_seven_refused": sorted(
                r["structure"] for r in adjudication()["adjudication"]
                if not r["holds_a_household"]),
        },
        "household_owed": {
            "size_drawn": size,
            "kin_seated": 1,
            "seed": f"{slot}:household_size" if size else None,
            "seated_by": "T-1171 (the modelled families), T-1174 (women and children), "
                         "T-1179 (converge)",
            "note": rule["family_note"] or (
                "THE FAMILY THIS HEAD IS OWED, AND NOT SEATED HERE. The 1840 size "
                "histogram drew this house at %d people. Its kin are `family/none` in the "
                "order book and that quota belongs to T-1171 and T-1174; seating them "
                "here would order the same people twice." % (size or 0)),
        },
        "arrival": {
            "value": None,
            "confidence": RECONSTRUCTED,
            "tier": "unknown",
            "note": "NOT DRAWN HERE, AND THE REASON IS A CIRCLE. The arrival model's own "
                    "distribution is computed over the compiled scene and the scene "
                    "carries these cards; an arrival written here would move the table "
                    "that drew it. The programme's arrival stage owns this block.",
            "seated_by": "T-1169 (the arrival fill), T-1179 (converge)",
        },
        "lives_at": {
            "value": sid,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "1835_institutional_lodging",
                "note": f"THE ROOF IS THE CLAIM, and it is the only part of this card that "
                        f"is not an invention. {row['why']}",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a source naming who lived at this building on the scene date",
            },
            "note": "SEATED ON A BUILDING THAT STANDS. Unlike the trade and family "
                    "reconstructions, this household is not waiting on T-1199 for a lot: "
                    "the roof it is under is a committed, placed record and is the reason "
                    "the household was ordered at all.",
        },
        "works_at": {
            "value": sid if rule["occupation"] else None,
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED if rule["occupation"] else "unknown",
            "note": ("The establishment is the building: the keepership of this light is "
                     "kept at the light." if rule["occupation"] else
                     "Not attested and not drawn. Nothing states what the people in this "
                     "house did."),
        },
        "present_on_scene_date": {
            "value": "present",
            "confidence": RECONSTRUCTED,
            "tier": RECONSTRUCTED,
            "basis": {
                "kind": "rule",
                "id": "ordered_by_the_reconstruction_order_book",
                "note": "Ordered, not argued: the book counts this household as missing "
                        "FROM the town of 1 July 1835, so presence is the order rather "
                        "than a draw made over it.",
            },
            "replaceable_by": {
                "kind": "person",
                "match": "a re-cut order book that no longer orders this bucket",
            },
        },
        "persons": [person],
        "touches_removal": False,
        "review_required": False,
        "research_note": "WRITTEN BY tools/reconstruct_institutional_households.py "
                         "(T-1531), the `institutional_households` stage of the 1835 "
                         "resident reconstruction programme. This file is NOT research "
                         "and is not a mint output: data/residents/households/ is "
                         "re-derived by the mint writers and data/residents/index.json is "
                         "derived from that directory, so a reconstruction lives here "
                         "instead and is overlaid onto the scene by "
                         "tools/compile_scene.py. docs/LIBERTIES.md carries the invention.",
    }


README = """# data/residents/institutional/

GENERATED by `tools/reconstruct_institutional_households.py --build` (T-1531), the
`institutional_households` stage of the 1835 resident reconstruction programme. Do not
hand-edit: `tools/check.sh` re-derives every card here from its seeds and fails on a
single differing byte.

One card per institutional roof whose own committed record puts a household under it.
`data/reconstruction/1835_institutional_lodging.json` is the adjudication that decides
which roofs those are — two of the town's nine — and names the seven it refuses, each
with the sentence that refuses it.

These cards live outside `data/residents/households/` for the reason `readmitted/`,
`reconstructed_trades/` and `lodgers/` do: that directory is re-derived by the research
mint writers and `data/residents/index.json` is derived from it, so a reconstruction that
is not a reading would be read back as one. `tools/compile_scene.py` overlays them.
"""


def fill() -> tuple:
    pool = load(POOLS)
    sizes = size_rows()
    taken_names, taken_ids = layer()
    room = buckets()
    cards, minted, fills = {}, [], {}
    refused_for_want_of_room = []
    for row in admitted():
        bucket = f"households/institutional/{row['division']}"
        if room.get(bucket, 0) - fills.get(bucket, 0) <= 0:
            refused_for_want_of_room.append({"structure": row["structure"], "bucket": bucket})
            continue
        hid, card = card_for(row, ROOFS[row["structure"]], pool, sizes,
                             taken_names, taken_ids)
        cards[hid] = card
        fills[bucket] = fills.get(bucket, 0) + 1
        minted.append({"id": hid, "file": f"institutional/{hid}.json",
                       "bucket": bucket, "place": row["structure"],
                       "division": row["division"]})
    adj = adjudication()
    ledger = {
        "_doc": "GENERATED by tools/reconstruct_institutional_households.py --build. Do "
                "not hand-edit; tools/check.sh re-derives it.",
        "id": "1835_institutional_households",
        "ticket": TICKET,
        "stage": STAGE,
        "target_date": SCENE_DATE,
        "generated_by": "tools/reconstruct_institutional_households.py --build",
        "not_a_reading": "A mint ledger. It reads the adjudication and the order book and "
                         "writes people; it reads no source and must not be counted as "
                         "research spend.",
        "reads": [
            "data/reconstruction/1835_institutional_lodging.json — which roofs hold a household",
            "data/reconstruction/1835_reconstruction_order_book.json — how many each division orders",
            "data/reconstruction/1835_invented_name_pools.json — the names",
            "data/reconstruction/1835_town_model.json — the sex ratio and the 1840 size histogram",
        ],
        "roofs_adjudicated": len(adj["adjudication"]),
        "roofs_holding_a_household": sorted(r["structure"] for r in admitted()),
        "roofs_refused": [
            {"structure": r["structure"], "division": r["division"], "why": r["why"]}
            for r in adj["adjudication"] if not r["holds_a_household"]],
        "what_the_book_ordered_before_the_adjudication": adj["what_the_book_ordered_before_this_file"],
        "refused_for_want_of_room": refused_for_want_of_room,
        "minted": minted,
        "fills": fills,
    }
    return cards, ledger


def measurement(cards: dict, ledger: dict) -> dict:
    room = buckets()
    short = {k: room[k] - ledger["fills"].get(k, 0)
             for k in sorted(room) if room[k] - ledger["fills"].get(k, 0)}
    return {
        "buckets_ordered": len(room),
        "households_ordered": sum(room.values()),
        "households_drawn": len(ledger["minted"]),
        "persons_drawn": sum(len(c["persons"]) for c in cards.values()),
        "every_bucket_filled": not short,
        "buckets_still_short": short,
        "kin_owed_and_not_seated": sum(
            (c["household_owed"]["size_drawn"] or 1) - 1 for c in cards.values()),
        "the_nine_roofs": {
            "adjudicated": ledger["roofs_adjudicated"],
            "hold_a_household": len(ledger["roofs_holding_a_household"]),
            "refused": len(ledger["roofs_refused"]),
        },
    }


# --------------------------------------------------------------------- modes --

def write(cards: dict) -> tuple:
    MINTED.mkdir(parents=True, exist_ok=True)
    wanted = {f"{hid}.json" for hid in cards}
    removed = 0
    for path in sorted(MINTED.glob("hh_*.json")):
        if path.name not in wanted:
            path.unlink()
            removed += 1
    written = 0
    for hid, card in sorted(cards.items()):
        path = MINTED / f"{hid}.json"
        text = dumps(card)
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            written += 1
    (MINTED / "README.md").write_text(README, encoding="utf-8")
    return written, removed


def write_fills(ledger: dict) -> None:
    """Carry this stage's fills into the order book and re-derive it. The book's own
    `--build` refuses an overfilled bucket, so the quota is enforced twice."""
    import build_order_book_1835 as ob  # noqa: PLC0415
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    kept = [f for f in book.get("fills", []) if f.get("ticket") != TICKET]
    kept += [{"bucket": key, "ticket": TICKET, "stage": STAGE, "records": n,
              "by": "tools/reconstruct_institutional_households.py --build"}
             for key, n in sorted(ledger["fills"].items())]
    book["fills"] = kept
    BOOK.write_text(json.dumps(book, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ob.cmd_build()


def build() -> int:
    cards, ledger = fill()
    written, removed = write(cards)
    ledger["measurement"] = measurement(cards, ledger)
    LEDGER.write_text(dumps(ledger), encoding="utf-8")
    write_fills(ledger)
    print("  wrote %s" % LEDGER.relative_to(ROOT))
    print("  %d household(s) drawn into %d bucket(s); %d card(s) written, %d retired"
          % (len(ledger["minted"]), len(ledger["fills"]), written, removed))
    return 0


def check() -> int:
    cards, ledger = fill()
    ledger["measurement"] = measurement(cards, ledger)
    live = {path.stem: path.read_text(encoding="utf-8")
            for path in sorted(MINTED.glob("hh_*.json"))} if MINTED.exists() else {}
    want = {hid: dumps(card) for hid, card in cards.items()}
    if set(live) != set(want):
        print("  FAIL the committed directory is not this stage's set (missing %s, extra %s)"
              % (sorted(set(want) - set(live))[:6], sorted(set(live) - set(want))[:6]))
        return 1
    bad = [hid for hid in sorted(want) if live[hid] != want[hid]]
    if bad:
        print("  FAIL %d card(s) are not what this stage derives: %s"
              % (len(bad), ", ".join(bad[:6])))
        return 1
    if not LEDGER.exists() or LEDGER.read_text(encoding="utf-8") != dumps(ledger):
        print("  FAIL %s is not what --build writes" % LEDGER.relative_to(ROOT))
        return 1
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ours = {f["bucket"]: int(f.get("records") or 0)
            for f in book.get("fills", []) if f.get("ticket") == TICKET}
    if ours != dict(ledger["fills"]):
        print("  FAIL the order book's fills for %s are not this stage's ledger" % TICKET)
        return 1
    # THE WEIGHT AND THE MINT READ ONE FILE, and this is where that is proved. The book
    # weights the institutional cells on `lodging_capable_by_division`; if it ever orders
    # more than the adjudication admits, the surplus is a household nobody could write.
    capable = adjudication()["lodging_capable_by_division"]
    for bucket, ordered in sorted(buckets().items()):
        division = bucket.rsplit("/", 1)[1]
        if ordered > int(capable.get(division) or 0):
            print("  FAIL the book orders %d institutional household(s) in the %s "
                  "division and the adjudication admits %s"
                  % (ordered, division, capable.get(division)))
            return 1
    vocabulary = set(load(RESIDENTS / "index.json")["vocabulary"]["occupations"])
    outside = sorted({
        (c["persons"][0]["occupation"] or {}).get("value") for c in cards.values()}
        - vocabulary - {"none_recorded"})
    if outside:
        print("  FAIL an occupation outside the controlled vocabulary was written: %s" % outside)
        return 1
    if not ledger["measurement"]["every_bucket_filled"]:
        print("  FAIL the institutional cells are not discharged: %s"
              % ledger["measurement"]["buckets_still_short"])
        return 1
    print("  ok    %d household(s) re-derive from their seeds; the 9 institutional roofs "
          "adjudicate to %d that hold one" % (len(cards), len(cards)))
    print("  ok    the order book carries this stage's fills and both cells are discharged")
    return 0


def report() -> int:
    cards, ledger = fill()
    stats = measurement(cards, ledger)
    print("THE TOWN'S NINE STANDING INSTITUTIONAL ROOFS, ADJUDICATED (%s)" % TICKET)
    for row in adjudication()["adjudication"]:
        mark = "HOUSEHOLD" if row["holds_a_household"] else "  refused"
        print("  %s  %-28s %-6s %s" % (mark, row["structure"], row["division"],
                                       row["why"].split(".")[0][:96]))
    print()
    print("  the book ordered %s before the adjudication; it orders %d now"
          % (ledger["what_the_book_ordered_before_the_adjudication"]["total"],
             stats["households_ordered"]))
    for hid, card in sorted(cards.items()):
        person = card["persons"][0]
        print("  %-34s %-8s %-22s %s" % (hid, card["division"],
                                         card["institutional_household"]["place"],
                                         person["name"]))
    print("  %d person(s) drawn; %d kin owed and not seated here"
          % (stats["persons_drawn"], stats["kin_owed_and_not_seated"]))
    return 0


def self_test() -> int:
    failures = []

    def case(name, ok):
        print("   self-test | %-4s %s" % ("ok" if ok else "FAIL", name))
        if not ok:
            failures.append(name)

    adj = adjudication()
    rows = adj["adjudication"]
    case("every standing institutional roof is adjudicated exactly once",
         len({r["structure"] for r in rows}) == len(rows) == 9)
    case("every refusal states a reason and cites what it read",
         all(r["why"].strip() and r["reads"] for r in rows if not r["holds_a_household"]))
    case("the capable count is the adjudication's own tally",
         all(int(adj["lodging_capable_by_division"][d]) ==
             sum(1 for r in rows if r["holds_a_household"] and r["division"] == d)
             for d in ("south", "west", "north")))
    case("the book's institutional order never exceeds the adjudication",
         all(n <= int(adj["lodging_capable_by_division"][b.rsplit("/", 1)[1]])
             for b, n in buckets().items()))

    # A ROOF ADMITTED WITH NO CARD RULE IS REFUSED, not quietly skipped: the evidence
    # says a household lived there and the rule says what to write, and the second does
    # not follow from the first.
    saved = dict(ROOFS)
    try:
        ROOFS.pop("watkins_school_house")
        try:
            admitted()
            case("fires: an admitted roof this stage has no card rule for", False)
        except SystemExit:
            case("fires: an admitted roof this stage has no card rule for", True)
    finally:
        ROOFS.clear()
        ROOFS.update(saved)

    cards, ledger = fill()
    case("no card carries an age band it was never ordered",
         all(c["persons"][0]["age_band"] is None for c in cards.values()))
    case("every card is seated on the roof that ordered it",
         all(c["lives_at"]["value"] == c["institutional_household"]["place"]
             for c in cards.values()))
    case("no invented name is a name the layer's real people bear",
         not ({c["persons"][0]["name"].lower() for c in cards.values()}
              & {n for n in layer()[0]} - {c["persons"][0]["name"].lower()
                                           for c in cards.values()}))
    case("the keeper's quarters draw no family and say so",
         all(c["household_owed"]["size_drawn"] is None
             for c in cards.values()
             if c["institutional_household"]["place"] == "chicago_lighthouse_1832"))
    print("   self-test | %d failure(s)" % len(failures))
    return 1 if failures else 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.build:
        return build()
    if args.check:
        return check()
    if args.report:
        return report()
    if getattr(args, "self_test"):
        return self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
