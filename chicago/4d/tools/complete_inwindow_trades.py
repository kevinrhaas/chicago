#!/usr/bin/env python3
"""A HOUSE OF TRADE FOR EVERY IN-WINDOW TRADESMAN WHO HAD NONE (T-1404, of T-1182).

    python3 tools/complete_inwindow_trades.py            the population, read out
    python3 tools/complete_inwindow_trades.py --build    raise the houses and write the ledger
    python3 tools/complete_inwindow_trades.py --check    it re-derives, and nothing has drifted
    python3 tools/complete_inwindow_trades.py --self-test the rules below, held over fixtures

THE DEFECT. `tools/derive_resident_roles.py` gives every resident their trades as DATED
ROLES, and 78 of those rows reach 1 July 1835 on a person the business layer holds no
workplace for. Lemuel Brown is a blacksmith in window and there is no smithy; five
physicians practise and the layer counts three physicians' offices. The town therefore
printed men at trades that had nowhere to be carried on, and the December 1835 State
census's shortfall was being read as a hole in the town when part of it was a hole in the
LAYER — a house the research already names and nobody had written down.

WHAT IT WRITES, AND AT WHAT GRADE. A raised house is `inferred` and never `attested`. The
source says the man followed the trade at Chicago inside the window; that a man at this
trade kept a shop of his own is an inference ABOUT THE SHOP, and the shop's own record is
where that inference is declared. Nothing here is promoted, nobody is minted, no
coordinate is invented: every raised house takes an `unplaceable` location whose
`limit_reason` says that no reading places it and hands the seating to T-1198.

THE RULE IS DATA. `data/businesses/rulings/premises_rulings.json` rules each of the resident
layer's 110 occupations into `own_premises` or `no_fixed_premises`, and the
premises-implying set is the parent's: the `public_trades` and `works_trades` of the
signage rule, plus the lawyers' and physicians' offices the census counts. An occupation
with no ruling is a FAULT here, never a silent skip — a trade nobody has ruled on is a
tradesman who would vanish out of both halves of the clause.

WHAT IT REFUSES TO DO.

  * IT WILL NOT DOUBLE A MAN THE PAPER ALREADY PRINTED. 52 keepers in the register carry
    `person_id: null`, because the register could not match the printed name to a town
    card. Where an unlinked keeper shares a candidate's surname AND the house the register
    prints names that candidate's own occupation, the candidate is HELD and reported for
    the identity ruling T-1182 clause 1 owns. A different trade under the same surname is
    a different house and is raised. A collision the surname test cannot see — the
    register prints a trade in words the card does not use — is ruled by hand in the
    rulings' `identity_holds`, and E. H. Mulford the watchmaker is the one such hold
    today: T-1007 leaves it open whether he and the register's J. H. Mulford are one man,
    and raising him a shop would answer that by building.

  * IT WILL NOT RAISE TWO HOUSES WHERE THE EVIDENCE STANDS ONE. Rufus Brown and Mrs Rufus
    Brown both keep a boarding house in window and they keep the SAME boarding house; the
    record names both as proprietors rather than standing two roofs. And a man printed at
    two trades that each imply premises kept ONE house of trade unless something says
    otherwise — John H. Kinzie is a merchant and a forwarding and commission merchant in
    the same store — so trades sharing a keeper fold into one record carrying both census
    classes. Two DIFFERENT keepers of one household at two different trades still raise
    two houses: a storekeeping father and a smith son are two houses.

  * IT WILL NOT RECONSTRUCT. What the census counts and the layer still cannot name stays
    short, and the shortfall is the order book's — `businesses/physician` and
    `businesses/lawyer` are T-1186's buckets. This tool moves the `known` figure those
    buckets are cut against and orders nothing.

WHERE A HOUSE IS SEATED, AND WHERE IT IS NOT. 22 of the 45 keepers already carry a
`works_at` structure on their card, so the premises is not unknown at all — Rufus Brown's
boarding house, McKee's smithy on State Street, the Tremont. But `works_at` also holds
BUILT-BY links, which are not workplaces: Augustine Taylor "works at" St Mary's because he
raised it, and Anson Taylor at the South Branch raft bridge for the same reason. So the
link is taken only when the STRUCTURE'S OWN committed `function` is the term the premises
ruling names — a `boarding_house` for a boarding-house keeper, a `blacksmith_shop` for a
smith — and the rest fall to `unplaceable` and to T-1198. That test is the reason the
rulings file carries `signage_function` on every own-premises row.

THE CROSSWALK HAS TO SEE THIS. `tools/trade_census_1835.py` counted the newspaper register
alone, so a house raised here was invisible to the December census comparison and to the
order book cut from it — T-1186 would have been ordered to reconstruct eleven physicians
over a layer that now names eight. The crosswalk reads the authored layer as well as of
T-1404, and its deltas are re-printed with the raised houses in them.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compile_businesses import (  # noqa: E402  — one derivation of a house's community
    RESIDENT_CARD_DIRS,
    derive_proprietor_community,
    person_communities,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESIDENTS = DATA / "residents"
BUSINESSES = DATA / "businesses"
AUTHORED = BUSINESSES / "authored"
RULINGS = BUSINESSES / "rulings" / "premises_rulings.json"
LEDGER = DATA / "research" / "residents" / "inwindow_trade_workplaces.json"

SCENE_DATE = "1835-07-01"
GENERATOR = "tools/complete_inwindow_trades.py"
TICKET = "T-1404"
OWN, NONE = "own_premises", "no_fixed_premises"
WRITTEN_BY = "raised_for_an_in_window_trade"


class Fault(Exception):
    """A defect in the rulings or the layer, phrased for the person who must fix it."""


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def identity_holds() -> dict[tuple, dict]:
    """The holds a hand ruling makes, where the surname test cannot see the collision."""
    out = {}
    for row in load_json(RULINGS).get("identity_holds") or []:
        if not str(row.get("basis") or "").strip() or not row.get("question"):
            raise Fault("an identity hold with no question or no basis: %r" % row)
        out[(row["person_id"], row["occupation"])] = row
    return out


def rulings() -> dict:
    doc = load_json(RULINGS)
    out = {}
    for row in doc["rulings"]:
        if row["occupation"] in out:
            raise Fault("two rulings for one occupation: %r" % row["occupation"])
        if row["premises"] not in (OWN, NONE):
            raise Fault("%s: a ruling off the vocabulary: %r" % (row["occupation"], row["premises"]))
        if not str(row.get("basis") or "").strip():
            raise Fault("%s: a ruling with no basis" % row["occupation"])
        if row["premises"] == OWN and not row.get("census_class"):
            raise Fault("%s: an own-premises ruling that names no census class — a house the "
                        "December census cannot be set against is a house outside the count"
                        % row["occupation"])
        out[row["occupation"]] = row
    return out


# ------------------------------------------------------------------ the layer as it stands

def business_records() -> list[dict]:
    paths = sorted(p for p in BUSINESSES.glob("*.json")
                   if p.name != "index.json")
    paths += sorted(AUTHORED.glob("*.json"))
    return [load_json(p) for p in paths]


def keepers(records: list[dict]) -> tuple[set[str], list[dict]]:
    """Who already holds a workplace, and which printed keepers the register never matched."""
    linked, unlinked = set(), []
    for rec in records:
        if rec.get("id", "").startswith("biz_") and _ours(rec):
            continue
        for field in ("proprietors", "partners", "staff"):
            for row in rec.get(field) or []:
                if row.get("person_id"):
                    linked.add(row["person_id"])
                elif field != "staff":
                    unlinked.append({"name": row.get("name") or "",
                                     "business_id": rec["id"],
                                     "occupation": rec.get("occupation"),
                                     "trade": rec.get("trade")})
    return linked, sorted(unlinked, key=lambda r: (r["business_id"], r["name"]))


def _ours(rec: dict) -> bool:
    return (rec.get("provenance") == "authored"
            and (rec.get("replaceable_by") or "").startswith(WRITTEN_BY))


def cards() -> list[tuple[str, dict]]:
    out = []
    for folder in RESIDENT_CARD_DIRS:
        for path in sorted((RESIDENTS / folder).glob("*.json")):
            out.append((folder, load_json(path)))
    return out


def _surnames(name: str) -> set[str]:
    HONORIFICS = {"dr", "mr", "mrs", "miss", "rev", "col", "capt", "maj", "major", "lieut",
                  "gen", "jr", "sr", "esq", "hon", "father", "the"}
    words = {w.strip(".,()[]'\"").lower() for w in (name or "").split()}
    return {w for w in words if len(w) > 2 and w not in HONORIFICS and w.isalpha()}


def held_by_the_register(person: dict, occupation: str, unlinked: list[dict]) -> dict | None:
    """The register may already print this man at this trade under a name it could not match."""
    mine = _surnames(person.get("name") or "")
    for row in unlinked:
        if not (mine & _surnames(row["name"])):
            continue
        printed = " ".join(str(row.get(k) or "") for k in ("occupation", "trade")).lower()
        if occupation.replace("_", " ") in printed or occupation in printed:
            return row
    return None


# ------------------------------------------------------------------------- the candidates

def candidates(ruled: dict, linked: set[str], unlinked: list[dict],
               holds: dict | None = None) -> dict:
    """Every scene-date role, sorted into what this clause does with it."""
    raise_, no_premises, held, not_ruled, already = [], [], [], [], []
    for folder, card in cards():
        for person in card.get("persons") or []:
            for role in person.get("roles") or []:
                if not isinstance(role, dict) or not role.get("covers_scene_date"):
                    continue
                row = {
                    "person_id": person["id"],
                    "name": person.get("name"),
                    "household_id": card["id"],
                    "household_head": card.get("head"),
                    "card_dir": folder,
                    "role": role.get("role"),
                    "kind": role.get("kind"),
                    "as_printed": role.get("as_printed"),
                    "confidence": role.get("confidence"),
                    "sources": sorted(role.get("sources") or []),
                    "from": role.get("from"),
                    "to": role.get("to"),
                }
                if person["id"] in linked:
                    already.append(row)
                    continue
                if not role.get("role"):
                    row["reason"] = (
                        "THE PRINTING HAS NOT BEEN RULED INTO THE CLOSED VOCABULARY. The role "
                        "keeps what the source printed and `role` is null until T-1254 rules the "
                        "controlled term; a house may not be raised on a string nobody has "
                        "adjudicated.")
                    not_ruled.append(row)
                    continue
                ruling = ruled.get(role["role"])
                if ruling is None:
                    raise Fault(
                        "%s: no ruling covers the occupation %r. Rule it in "
                        "data/businesses/rulings/premises_rulings.json — a trade with no ruling is a "
                        "tradesman who falls out of both halves of the clause."
                        % (person["id"], role["role"]))
                row["premises"] = ruling["premises"]
                row["basis"] = ruling["basis"]
                if ruling["premises"] == NONE:
                    no_premises.append(row)
                    continue
                row["census_class"] = ruling["census_class"]
                row["signage_function"] = ruling["signage_function"]
                ruled_hold = (holds or {}).get((person["id"], role["role"]))
                if ruled_hold:
                    row["held_against"] = {
                        "business_id": ruled_hold.get("where"),
                        "name": "an open identity question: %s" % ruled_hold["question"],
                        "occupation": role["role"],
                        "trade": ruled_hold["basis"],
                    }
                    row["held_by"] = "identity_holds"
                    held.append(row)
                    continue
                clash = held_by_the_register(person, role["role"], unlinked)
                if clash:
                    row["held_against"] = clash
                    held.append(row)
                    continue
                raise_.append(row)
    key = lambda r: (r["person_id"], r["role"] or "", r["kind"] or "")  # noqa: E731
    return {"raise": sorted(raise_, key=key), "no_premises": sorted(no_premises, key=key),
            "held": sorted(held, key=key), "not_ruled": sorted(not_ruled, key=key),
            "already_holds_a_workplace": sorted(already, key=key)}


def houses(to_raise: list[dict]) -> list[dict]:
    """The houses the raised roles stand for, after two kinds of folding.

    A group is one household at one trade — two keepers of one boarding house are one
    house. Groups that SHARE A KEEPER are then merged, because a man at two premises
    trades kept one house of trade: the merged record carries every trade's census class
    and takes its id from its lead keeper and its alphabetically first trade.
    """
    groups: dict[tuple, list[dict]] = {}
    for row in to_raise:
        groups.setdefault((row["household_id"], row["role"]), []).append(row)

    parent: dict[tuple, tuple] = {k: k for k in groups}

    def find(k):
        while parent[k] != k:
            parent[k] = parent[parent[k]]
            k = parent[k]
        return k

    by_person: dict[str, tuple] = {}
    for key in sorted(groups):
        for row in groups[key]:
            seen = by_person.setdefault(row["person_id"], key)
            a, b = find(seen), find(key)
            if a != b:
                parent[max(a, b)] = min(a, b)

    merged: dict[tuple, list[tuple]] = {}
    for key in sorted(groups):
        merged.setdefault(find(key), []).append(key)

    out = []
    for root, keys in sorted(merged.items()):
        occupations = sorted({k[1] for k in keys})
        rows, seen_ids = [], set()
        for key in sorted(keys):
            for row in groups[key]:
                if row["person_id"] in seen_ids:
                    continue
                seen_ids.add(row["person_id"])
                rows.append(row)
        rows.sort(key=lambda r: (r["person_id"] != r["household_head"], r["person_id"]))
        out.append({"household_id": root[0], "occupation": occupations[0],
                    "occupations": occupations, "keepers": rows})
    return out


# WHICH COMMITTED STRUCTURE FUNCTIONS SATISFY A RULING'S `signage_function`. A public
# house is recorded as `tavern_inn` or `hotel` and the two are not reliably distinguished
# in the sources; a store keeper's roof may be recorded as the store alone or as the store
# with the keeper living over it; a packer's yard and a forwarder's warehouse each carry
# two terms. Everything else is satisfied by its own term and nothing else, which is what
# keeps a built-by link out: a church does not seat a carpenter's shop.
SEATS_AT = {
    "tavern_inn": ("hotel", "tavern_inn"),
    "hotel": ("hotel", "tavern_inn"),
    "boarding_house": ("boarding_house",),
    "store": ("dwelling_and_store", "grocery_and_provision_store", "store",
              "store_and_dwelling", "store_residence"),
    "grocery_and_provision_store": ("dwelling_and_store", "grocery_and_provision_store",
                                    "store", "store_and_dwelling", "store_residence"),
    "drug_store": ("drug_store",),
    "shop": ("shop",),
    "blacksmith_shop": ("blacksmith_shop",),
    "tannery": ("tannery",),
    "brickyard": ("brickyard",),
    "soap_candle_manufactory": ("soap_candle_manufactory",),
    "packing_house": ("packing_house", "slaughterhouse_packing", "warehouse_and_slaughter_yard"),
    "slaughterhouse_packing": ("packing_house", "slaughterhouse_packing",
                               "warehouse_and_slaughter_yard"),
    "forwarding_and_commission_store": ("forwarding_and_commission_store",
                                        "forwarding_commission_warehouse",
                                        "warehouse_and_slaughter_yard"),
    "auction_room": ("auction_room",),
    "saddlery_and_harness_shop": ("saddlery_and_harness_shop",),
    "physicians_office": ("physicians_office",),
    "printing_office": ("printing_office", "printing_office_and_store"),
    "office": (),
}

STRUCTURES = DATA / "structures"


def structure_functions() -> dict[str, str]:
    out = {}
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = load_json(path)
        fn = doc.get("function")
        out[path.stem] = (fn or {}).get("value") if isinstance(fn, dict) else fn
    return out


def seat(house: dict, ruling: dict, cards_by_id: dict, functions: dict) -> dict | None:
    """The structure the lead keeper's card already puts this trade in, or nothing."""
    card = cards_by_id.get(house["keepers"][0]["household_id"]) or {}
    works = card.get("works_at") or {}
    sid = works.get("value")
    if not sid:
        return None
    allowed = SEATS_AT.get(ruling.get("signage_function") or "", ())
    if functions.get(sid) not in allowed:
        return None
    return {"structure_id": sid, "function": functions.get(sid),
            "confidence": works.get("confidence"),
            "sources": sorted(works.get("sources") or [])}


WORDS = {"forwarding_and_commission": "forwarding and commission merchant"}


def _phrase(occupation: str) -> str:
    return WORDS.get(occupation, occupation.replace("_", " "))


def _location(seated: dict | None, house: dict) -> dict:
    if not seated:
        return {
            "kind": "unplaceable",
            "structure_id": None,
            "street_id": None,
            "face": None,
            "primary": True,
            "from": None,
            "to": None,
            "tier": "inferred",
            "basis": "NO READING PLACES THIS HOUSE. The evidence is a trade on a card, not a "
                     "printed address, so the record carries its limit rather than a guess.",
            "limit_reason": "The source names the trade and not the premises. T-1198 seats every "
                            "attested and inferred house on the ground its evidence allows — a "
                            "structure where one is named, a lot where an address narrows it, a "
                            "division band where only that is known — and this house waits there.",
        }
    return {
        "kind": "premises",
        "structure_id": seated["structure_id"],
        "street_id": None,
        "face": None,
        "primary": True,
        "from": None,
        "to": None,
        "tier": "inferred",
        "basis": (
            "THE KEEPER'S CARD ALREADY PUTS THIS TRADE IN THIS ROOF. %s carries "
            "`works_at: %s` at %s on %s, and that structure's own committed `function` reads "
            "`%s` — the term this trade's premises ruling names. A `works_at` that named a "
            "roof of another function would be a BUILT-BY link rather than a workplace and is "
            "refused here. The tier is capped at `inferred` because the house itself is an "
            "inference: it is the firm, not the roof, that no source prints."
            % (house["keepers"][0]["household_id"], seated["structure_id"],
               seated["confidence"] or "an ungraded link",
               ", ".join(seated["sources"]) or "the card's own reading", seated["function"])),
    }


def record(house: dict, ruled: dict, communities: dict, seated: dict | None = None) -> dict:
    occupation = house["occupation"]
    occupations = house.get("occupations") or [occupation]
    ruling = ruled[occupation]
    classes = sorted({ruled[o]["census_class"] for o in occupations})
    lead = house["keepers"][0]
    sources = sorted({s for k in house["keepers"] for s in k["sources"]})
    names = ", ".join(k["name"] for k in house["keepers"])
    proprietors = [{
        "name": k["name"],
        "person_id": k["person_id"],
        "register_person_id": None,
        "role": "proprietor",
        "from": None,
        "to": None,
        "tier": "inferred",
        "basis": (
            "THE TRADE IS THE SOURCE'S; THE HOUSE IS THE INFERENCE. %s carries dated role(s) of "
            "`%s` that cover %s, graded %s on %s. That the trade was followed at Chicago in "
            "window is what the source says; that it was followed in a house of this keeper's "
            "own is this record's inference, and it is graded `inferred` for that reason and "
            "never promoted. The keeper held no workplace in the business layer before T-1404."
            % (k["name"], ", ".join(occupations), SCENE_DATE, k["confidence"],
               ", ".join(k["sources"]) or "the card's own reading")),
        "source_id": (k["sources"] or [None])[0],
        "claim_ids": [],
    } for k in house["keepers"]]
    doc = {
        "id": "biz_%s_%s" % (lead["person_id"], occupation),
        "register_id": None,
        "name": "%s, %s" % (names, " and ".join(_phrase(o) for o in occupations)),
        "provenance": "authored",
        "type": classes,
        "trade": " and ".join(_phrase(o) for o in occupations),
        "occupation": occupation,
        "goods": [],
        "firm_styles": [],
        "proprietors": proprietors,
        "partners": [],
        "staff": [],
        "locations": [_location(seated, house)],
        "dates": {
            "opened": None,
            "closed": None,
            "precision": "unbounded",
            "tier": "inferred",
            "basis": "The role's bound is the SOURCE's span and not the house's: nothing says "
                     "when this shop opened or closed. The record stands on the scene date "
                     "because the role covers it, and bounds neither end.",
        },
        "evidence": {"first_issue": None, "last_issue": None, "copy_dates": []},
        "present_at_scene_date": True,
        "exclusion": None,
        "exclusion_note": None,
        "proprietor_community": derive_proprietor_community(proprietors, [], communities),
        "customers": [],
        "sources": sources,
        "claim_ids": [],
        "liberties": {"survival_required": False, "backdating_required": False},
        "review_required": False,
        "replaceable_by": (
            "%s: raised by %s because the keeper's dated role covers %s and the layer held no "
            "workplace for them. Retired or rewritten by any printing that names this house — a "
            "notice, a directory line or a biography giving its style, its street or its "
            "partners — and by an identity ruling that makes this keeper one of the %d printed "
            "keepers the register could not match to a card."
            % (WRITTEN_BY, GENERATOR, SCENE_DATE, 52)),
    }
    return doc


# ------------------------------------------------------------------------------ the ledger

def shortfall(built: list[dict]) -> list[dict]:
    """Every census class this clause moved, and what is still short for the order book."""
    crosswalk = load_json(DATA / "research" / "books" / "trade_census_1835_crosswalk.json")
    raised: dict[str, int] = {}
    for doc in built:
        for cls in doc["type"]:
            raised[cls] = raised.get(cls, 0) + 1
    rows = []
    for row in sorted(crosswalk["classes"], key=lambda r: r["class"]):
        cls = row["class"]
        after = int(row["town_records_at_scene_date"])
        before = after - raised.get(cls, 0)
        census = row["census_count"]
        rows.append({
            "class": cls,
            "census_count": census,
            "town_before_T-1404": before,
            "raised_here": raised.get(cls, 0),
            "town_after_T-1404": after,
            "still_short": (max(0, census - after) if census is not None and row["compared"]
                            else None),
            "documented_zero": cls in crosswalk["classes_the_town_holds_nothing_for"],
            "owed_to": "T-1186" if cls in ("physician", "lawyer") else None,
        })
    return rows


def ledger(state: dict, built: list[dict]) -> dict:
    counts = {k: len(v) for k, v in sorted(state.items())}
    counts["houses_raised"] = len(built)
    counts["houses_seated_on_a_committed_structure"] = sum(
        1 for d in built if d["locations"][0]["kind"] == "premises")
    by_class: dict[str, int] = {}
    for doc in built:
        for cls in doc["type"]:
            by_class[cls] = by_class.get(cls, 0) + 1
    zeros = [r for r in shortfall(built) if r["documented_zero"] and r["town_after_T-1404"]]
    if zeros:
        raise Fault("a documented zero of the December census has been filled: %s"
                    % ", ".join(r["class"] for r in zeros))
    return {
        "id": "1835_inwindow_trade_workplaces",
        "ticket": TICKET,
        "parent_ticket": "T-1182",
        "generated_by": GENERATOR + " --build",
        "rulings": "data/businesses/rulings/premises_rulings.json",
        "not_a_reading": (
            "DERIVED, never hand-edited. Every row is read off a committed role on a committed "
            "card and a committed ruling. No page of any source is read here, nobody is minted, "
            "nothing is reconstructed and no confidence is promoted: a house raised from a role "
            "is `inferred` and says so on its own record."),
        "scene_date": SCENE_DATE,
        "counts": counts,
        "houses_by_census_class": dict(sorted(by_class.items())),
        "houses_raised": [{
            "business_id": doc["id"],
            "occupation": doc["trade"],
            "census_classes": doc["type"],
            "keepers": [p["person_id"] for p in doc["proprietors"]],
            "seated_at": doc["locations"][0].get("structure_id"),
            "sources": doc["sources"],
        } for doc in built],
        "no_fixed_premises": [{
            "person_id": r["person_id"], "name": r["name"], "role": r["role"],
            "kind": r["kind"], "basis": r["basis"],
        } for r in state["no_premises"]],
        "held_for_an_identity_ruling": [{
            "person_id": r["person_id"], "name": r["name"], "role": r["role"],
            "register_house": r["held_against"]["business_id"],
            "printed_as": r["held_against"]["name"],
            "held_by": r.get("held_by") or "the_surname_test",
            "owed_to": "T-1007's open question" if r.get("held_by") else "T-1182 clause 1",
        } for r in state["held"]],
        "not_ruled_into_the_vocabulary": [{
            "person_id": r["person_id"], "name": r["name"], "as_printed": r["as_printed"],
            "reason": r["reason"], "owed_to": "T-1254",
        } for r in state["not_ruled"]],
        "crosswalk_rerun": {
            "note": ("THE DECEMBER 1835 STATE CENSUS, RE-RUN OVER THE LAYER THESE HOUSES JOIN. "
                     "`town_after` is what tools/trade_census_1835.py --build now counts, which "
                     "reads the authored records as well as the register as of T-1404; "
                     "`town_before` subtracts the houses raised here. The count was taken "
                     "between 1 September and December 1835 and the scene is 1 July: a class "
                     "still short is not thereby a hole in the July town."),
            "classes": shortfall(built),
        },
    }


# --------------------------------------------------------------------------------- the run

def derive() -> tuple[dict, list[dict], dict]:
    ruled = rulings()
    records = business_records()
    linked, unlinked = keepers(records)
    state = candidates(ruled, linked, unlinked, identity_holds())
    communities = person_communities()
    cards_by_id = {card["id"]: card for _, card in cards()}
    functions = structure_functions()
    built = []
    for house in houses(state["raise"]):
        ruling = ruled[house["occupation"]]
        built.append(record(house, ruled, communities,
                            seat(house, ruling, cards_by_id, functions)))
    ids = [d["id"] for d in built]
    if len(set(ids)) != len(ids):
        raise Fault("two raised houses share an id: %s"
                    % sorted({i for i in ids if ids.count(i) > 1}))
    return state, built, ledger(state, built)


def ours_on_disk() -> list[Path]:
    return sorted(p for p in AUTHORED.glob("*.json") if _ours(load_json(p)))


def write() -> int:
    state, built, doc = derive()
    keep = {d["id"] for d in built}
    for path in ours_on_disk():
        if path.stem not in keep:
            path.unlink()
    for record_doc in built:
        (AUTHORED / (record_doc["id"] + ".json")).write_text(dumps(record_doc), encoding="utf-8")
    LEDGER.write_text(dumps(doc), encoding="utf-8")
    return report(doc)


def check() -> int:
    state, built, doc = derive()
    bad = []
    on_disk = {p.stem: load_json(p) for p in ours_on_disk()}
    for record_doc in built:
        got = on_disk.pop(record_doc["id"], None)
        if got is None:
            bad.append("%s is not committed; run --build" % record_doc["id"])
        elif got != record_doc:
            bad.append("%s on disk is not what --build writes" % record_doc["id"])
    for left in sorted(on_disk):
        bad.append("%s is committed and --build no longer writes it" % left)
    if not LEDGER.exists() or load_json(LEDGER) != doc:
        bad.append("%s is not what --build writes" % LEDGER.relative_to(ROOT))
    if bad:
        print("THE IN-WINDOW TRADE CLAUSE HAS DRIFTED:")
        for line in bad:
            print("  " + line)
        return 1
    print("%d raised houses and the ledger re-derive." % len(built))
    return 0


def report(doc: dict | None = None) -> int:
    doc = doc or derive()[2]
    c = doc["counts"]
    print("IN-WINDOW TRADES, %s" % SCENE_DATE)
    print("  roles already holding a workplace   %4d" % c["already_holds_a_workplace"])
    print("  houses raised here                  %4d (for %d role rows)"
          % (c["houses_raised"], c["raise"]))
    print("  no premises of their own            %4d" % c["no_premises"])
    print("  held for an identity ruling         %4d" % c["held"])
    print("  printing not yet ruled (T-1254)     %4d" % c["not_ruled"])
    print("  of those, seated on a committed roof %4d"
          % c["houses_seated_on_a_committed_structure"])
    print("  by census class: %s" % ", ".join(
        "%s %d" % (k, v) for k, v in doc["houses_by_census_class"].items()))
    print("  still short, owed to T-1186: %s" % ", ".join(
        "%s %d" % (r["class"], r["still_short"])
        for r in doc["crosswalk_rerun"]["classes"] if r["owed_to"] and r["still_short"]))
    return 0


def self_test() -> int:
    fired = []

    def fires(label, fn):
        try:
            fn()
        except Fault as exc:
            fired.append(label)
            print("  fired: %s — %s" % (label, str(exc).splitlines()[0][:90]))
            return
        raise SystemExit("DID NOT FIRE: " + label)

    ruled = {"blacksmith": {"occupation": "blacksmith", "premises": OWN, "census_class": "other",
                            "signage_function": "blacksmith_shop", "basis": "a smith's shop"}}
    person = {"id": "p1", "name": "Lemuel Brown",
              "roles": [{"role": "cooper", "kind": "trade", "covers_scene_date": True,
                         "confidence": "attested", "sources": ["s"]}]}
    card = {"id": "hh_1", "head": "p1", "persons": [person]}

    fires("an occupation no ruling covers", lambda: _candidates_over([card], ruled, set(), []))
    fires("an own-premises ruling naming no census class", lambda: _rulings_over(
        [{"occupation": "x", "premises": OWN, "census_class": None, "basis": "b"}]))
    fires("two rulings for one occupation", lambda: _rulings_over(
        [{"occupation": "x", "premises": NONE, "census_class": None, "basis": "b"},
         {"occupation": "x", "premises": NONE, "census_class": None, "basis": "b"}]))

    # the identity guard: same surname AND the register prints the same trade
    unlinked = [{"name": "Brown", "business_id": "biz_brown_painter", "occupation": "painter",
                 "trade": "house and sign painting"}]
    held = held_by_the_register({"name": "Lemuel Brown"}, "painter", unlinked)
    assert held and held["business_id"] == "biz_brown_painter", "the guard missed a same-trade name"
    assert held_by_the_register({"name": "Lemuel Brown"}, "blacksmith", unlinked) is None, \
        "the guard held a DIFFERENT trade under the same surname"
    assert held_by_the_register({"name": "Amos Green"}, "painter", unlinked) is None, \
        "the guard held a name the register never printed"
    print("  held: the identity guard holds a same-trade surname and releases a different trade")

    # one household at one trade is one house, and the head leads it
    wife = {"id": "p2", "name": "Mrs Rufus Brown",
            "roles": [{"role": "blacksmith", "kind": "trade", "covers_scene_date": True,
                       "confidence": "attested", "sources": ["s"]}]}
    husband = dict(person, roles=[dict(person["roles"][0], role="blacksmith")])
    state = _candidates_over([{"id": "hh_1", "head": "p1", "persons": [wife, husband]}],
                            ruled, set(), [])
    built = houses(state["raise"])
    assert len(built) == 1 and built[0]["keepers"][0]["person_id"] == "p1", \
        "two keepers of one trade in one household did not fold into one house"
    print("  held: one household at one trade raises one house, led by its head")

    # two premises trades on ONE keeper are one house, carrying both classes
    ruled2 = dict(ruled, merchant={"occupation": "merchant", "premises": OWN,
                                   "census_class": "store", "signage_function": "store",
                                   "basis": "a counter"})
    two = {"id": "p3", "name": "J. H. Kinzie", "roles": [
        {"role": "merchant", "kind": "trade", "covers_scene_date": True,
         "confidence": "inferred", "sources": ["s"]},
        {"role": "blacksmith", "kind": "trade", "covers_scene_date": True,
         "confidence": "attested", "sources": ["s"]}]}
    state = _candidates_over([{"id": "hh_2", "head": "p3", "persons": [two]}],
                            ruled2, set(), [])
    built = houses(state["raise"])
    assert len(built) == 1 and built[0]["occupations"] == ["blacksmith", "merchant"], built
    doc = record(built[0], ruled2, {})
    assert doc["type"] == ["other", "store"], doc["type"]
    print("  held: two premises trades on one keeper fold into one house, keeping both classes")

    # a scene-date role on a person who already holds a workplace raises nothing
    state = _candidates_over([{"id": "hh_1", "head": "p1", "persons": [husband]}],
                            ruled, {"p1"}, [])
    assert not state["raise"] and len(state["already_holds_a_workplace"]) == 1, \
        "a keeper who already holds a workplace was given a second one"
    print("  held: a keeper who already holds a workplace is left alone")

    # THE SEATING RULE, and the built-by link it refuses
    house = {"occupation": "carpenter",
             "keepers": [{"household_id": "hh_1", "person_id": "p1", "name": "A"}]}
    shop = {"signage_function": "shop"}
    cards_by_id = {"hh_1": {"id": "hh_1", "works_at": {"value": "st_marys_church",
                                                       "confidence": "inferred",
                                                       "sources": ["andreas_1884_v1"]}}}
    assert seat(house, shop, cards_by_id, {"st_marys_church": "church"}) is None, \
        "a built-by link seated a carpenter's shop in a church"
    cards_by_id["hh_1"]["works_at"]["value"] = "a_shop"
    got = seat(house, shop, cards_by_id, {"a_shop": "shop"})
    assert got and got["structure_id"] == "a_shop", "a real workplace link was not seated"
    inn = {"signage_function": "hotel"}
    cards_by_id["hh_1"]["works_at"]["value"] = "western_hotel"
    got = seat(house, inn, cards_by_id, {"western_hotel": "tavern_inn"})
    assert got and got["function"] == "tavern_inn", \
        "a hotel keeper was refused a roof the town records as a tavern_inn"
    assert _location(None, house)["kind"] == "unplaceable", "an unseated house was not unplaceable"
    print("  held: the seating rule takes a workplace link and refuses a built-by one")

    print("%d guards fired, 11 assertions held." % len(fired))
    return 0


def _rulings_over(rows):
    doc = {"rulings": rows}
    global RULINGS
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
        json.dump(doc, fh)
        path = Path(fh.name)
    keep, RULINGS = RULINGS, path
    try:
        return rulings()
    finally:
        RULINGS = keep
        path.unlink()


def _candidates_over(fixture_cards, ruled, linked, unlinked):
    global cards
    keep = cards
    cards = lambda: [("households", c) for c in fixture_cards]  # noqa: E731
    try:
        return candidates(ruled, linked, unlinked)
    finally:
        cards = keep


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--report"
    fn = {"--report": report, "--build": write, "--check": check, "--self-test": self_test}.get(arg)
    if fn is None:
        raise SystemExit(__doc__)
    try:
        sys.exit(fn())
    except Fault as exc:
        raise SystemExit("REFUSED: %s" % exc)
