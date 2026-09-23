#!/usr/bin/env python3
"""The corpus's LOT-AND-BLOCK addresses, resolved onto the roofs that stand at them.

    python3 tools/lot_addresses.py --check      re-resolve, and assert the committed
                                                records carry what the ledger seats
    python3 tools/lot_addresses.py --report     every address, its resolution, its refusals
    python3 tools/lot_addresses.py --self-test  the refusals fire

WHAT THIS IS FOR.

A newspaper can place a building three ways in this corpus, and they are not the same
claim. It can name a STREET and nothing narrower — `tools/adopt_street_faces.py` seats
those, and an adoption there claims a face and never a lot (L212). It can count doors
off a corner — `docs/CORNER-ORDINAL.md`, and such a record declares `lot_claim` to say it
claims NO lot (T-0384). Or it can print a lot and a block, which is the plat's own
language and the strongest placement statement the corpus makes. There is exactly one of
those: G. Spring's For-Sale notice, six printings between 1834-06-18 and 1834-11-19,
'LOT No. 7, in block No. 16, one lot east of Haddock's Tavern, on Lake street'.

T-0358 committed the block numbering so that address could resolve. It resolved to a
POLYGON and stopped: the roof standing on that polygon went on carding as a vacant
one-room frame cottage, and the most precisely placed building in the whole corpus
reached no visitor. This module is where the address is spent.

THE RESOLUTION IS DERIVED AND THE ADDRESS IS AUTHORED, which is the split that matters.
`data/research/newspapers/lot_addresses.json` carries the printed words, the printings
they are read from, and what the notice says stood on the lot. Nothing in it names a
structure. Every step from there is computed here:

  * block number -> block_id, through `data/traces/thompson_block_numbering.json`. The
    ledger states the block it believes it resolves to and the resolution REFUSES a
    ledger that disagrees with the committed numbering, so the two can never drift into
    quietly saying different things.
  * lot number   -> lot polygon, through `data/traces/vectors/thompson_lots.json`, whose
    lots carry `plat_lot_number` from the same committed numbering.
  * lot polygon  -> the roof standing on it, by footprint centroid. EXACTLY ONE, or the
    address is refused: an address that lands on two roofs has not placed anything, and
    one that lands on none has nothing to say.

THE GRADE DOES NOT RISE. The words are read; the block number is `inferred`; the lot
lines and their numbering are `conjectural`, drawn from no sheet. So the seating is
graded at the bottom tier — exactly where the roof already stood — and the ledger's
`confidence_note` states the chain. What the address buys is a NAME and a citation on a
card that said "vacant", not a promotion of the fabric under it.

WHAT IT MAY NOT DO, and each of these is an assertion below rather than a promise:

  1. **It may not move, resize or re-form the roof.** The seating writes ONE block and
     nothing else: it touches no coordinate, no footprint, no form value, and not even
     the record's `function`, which goes on reading as the anonymous family the recipe
     dealt. That restraint is not fussiness — `function.value` is what the dooryard,
     fence, planting and signboard generators read to decide what stands in a yard, so a
     documented address rewriting it would have moved fabric all over the lot to say a
     name. The house the notice calls LARGE is not made large: the fabric is the 665-roof
     programme's D3 count-unit and the ledger says so in as many words.
  2. **It may not promote the roof.** The structure's own phase stays `reconstructed`
     and `--check` re-reads it and fails if it has stopped saying so.
  3. **It may not seat a person.** The advertiser is the man to apply to for terms and
     nothing else; `is_the_occupant` and `is_the_owner` are false in the ledger and
     refused here if they are not. Who lived in this house is not in the corpus.
  4. **It may not seat two addresses on one roof, or one address on two roofs.**
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LEDGER = DATA / "research" / "newspapers" / "lot_addresses.json"
NUMBERING = DATA / "traces" / "thompson_block_numbering.json"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
STRUCTURES = DATA / "structures"

sys.path.insert(0, str(ROOT / "tools"))

# A claim id is `<issue_id>#<claim>`; the structure schema wants the SOURCE record rather
# than the issue. The same two the street-face adoptions read, and for the same reason.
CORPUS_SOURCE = (
    ("chicago_american_", "chicago_american_1835"),
    ("chicago_democrat_", "chicago_democrat_1833_1835"),
)


class AddressError(RuntimeError):
    """An address that resolves to nothing, to too much, or that claims what it may not."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sources(cites: list[str]) -> list[str]:
    out = set()
    for cite in cites:
        for prefix, source_id in CORPUS_SOURCE:
            if cite.startswith(prefix):
                out.add(source_id)
                break
        else:
            raise AddressError("the address cites %r, which names no corpus source" % cite)
    return sorted(out)


def _centroid(polygon: list[tuple[float, float]]) -> tuple[float, float]:
    """The footprint's area centroid, which is what "stands on this lot" is asked of.

    Not the record's position: a record's origin is a corner of its own footprint frame,
    and on a 26 m lot the difference between a corner and a centre is enough to answer
    the question wrong at a lot line.
    """
    twice_area = 0.0
    cx = cy = 0.0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        cross = x1 * y2 - x2 * y1
        twice_area += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(twice_area) < 1e-9:
        raise AddressError("a footprint with no area cannot stand on a lot")
    return cx / (3 * twice_area), cy / (3 * twice_area)


def _inside(point: tuple[float, float], ring: list[tuple[float, float]]) -> bool:
    x, y = point
    inside = False
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i - 1) % len(ring)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def lot_polygon(address: dict) -> list[tuple[float, float]]:
    """The committed lot polygon this address names, with the block number cross-read.

    The ledger names the block it believes it resolves to; this refuses to take its word
    for it. `thompson_block_numbering.json` is the committed answer to which block carries
    which number, and an address that disagrees with it is a stale copy of a reading that
    moved, not a second opinion.
    """
    numbering = load(NUMBERING)
    numbered = {int(b["number"]): b["block_id"] for b in numbering["blocks"]}
    number = int(address["block_number"])
    if number not in numbered:
        raise AddressError(
            "block %d carries no committed number — data/traces/thompson_block_numbering.json "
            "numbers %s, and an address on an unnumbered block resolves to nothing"
            % (number, ", ".join(str(n) for n in sorted(numbered))))
    if numbered[number] != address["block_id"]:
        raise AddressError(
            "the address puts block %d on %s and the committed numbering puts it on %s"
            % (number, address["block_id"], numbered[number]))
    blocks = {b["id"]: b for b in load(LOTS)["blocks"]}
    grid = blocks.get(address["block_id"])
    if grid is None:
        raise AddressError("%s is not a block of the committed plat grid"
                           % address["block_id"])
    wanted = int(address["lot_number"])
    lots = [lot for lot in grid["lots"] if lot.get("plat_lot_number") == wanted]
    if len(lots) != 1:
        raise AddressError("%s has %d lot(s) numbered %d"
                           % (address["block_id"], len(lots), wanted))
    return [(float(x), float(y)) for x, y in lots[0]["polygon"]]


def _limits(address: dict) -> None:
    who = address.get("id", "?")
    if not address.get("cites"):
        raise AddressError("%s cites no printing of its address" % who)
    advertiser = address.get("advertiser") or {}
    if advertiser.get("is_the_occupant") is not False:
        raise AddressError(
            "%s reads its advertiser as the occupant — the notice says whom to apply to "
            "for terms and nothing about who lived there" % who)
    if advertiser.get("is_the_owner") is not False:
        raise AddressError(
            "%s reads its advertiser as the owner, which no printing of it states" % who)
    if address.get("confidence") != "reconstructed":
        raise AddressError(
            "%s grades its seating `%s` — the lot lines it lands on are conjectural, so "
            "the bottom tier is the only grade the chain supports"
            % (who, address.get("confidence")))


def seat(placed: list[tuple[str, list[tuple[float, float]]]]) -> dict[str, dict]:
    """structure_id -> the blocks a lot address gives that roof.

    `placed` is (structure_id, footprint in the local ENU frame) for every roof that could
    stand at an address — the committed structures for the gate, the freshly built records
    for the generator. Passing them in is what lets the generator seat an address on a
    record it has not written yet, instead of reading back the file it is about to
    overwrite.
    """
    doc = load(LEDGER) if LEDGER.exists() else {}
    out: dict[str, dict] = {}
    for address in doc.get("addresses", []):
        _limits(address)
        ring = lot_polygon(address)
        standing = sorted({sid for sid, poly in placed if _inside(_centroid(poly), ring)})
        if not standing:
            raise AddressError(
                "%s resolves to lot %d of %s and no roof stands on it — the address has "
                "nothing to name" % (address["id"], address["lot_number"],
                                     address["block_id"]))
        if len(standing) > 1:
            raise AddressError(
                "%s resolves to lot %d of %s and %d roofs stand on it (%s) — an address "
                "that names more than one building has placed none of them"
                % (address["id"], address["lot_number"], address["block_id"],
                   len(standing), ", ".join(standing)))
        sid = standing[0]
        if sid in out:
            raise AddressError("%s is the second address on %s — one roof, one address"
                               % (address["id"], sid))
        out[sid] = blocks_for(address)
    return out


def blocks_for(address: dict) -> dict:
    """The `lot_address` and `function` blocks a seated roof carries, composed from the
    ledger's own words so that the card and the record cannot disagree."""
    cites = list(address["cites"])
    sources = _sources(cites)
    drawn = [item for item in address["stood_on_the_lot"] if item.get("drawn")]
    absent = [item for item in address["stood_on_the_lot"] if not item.get("drawn")]
    printed = ("%d printing%s, %s to %s, %d of them cited here as legible"
               % (address["printings"], "" if address["printings"] == 1 else "s",
                  address["first_issue"], address["last_issue"], len(cites)))
    lot_address = {
        "claims_lot": True,
        "block_number": int(address["block_number"]),
        "lot_number": int(address["lot_number"]),
        "block_id": address["block_id"],
        "address_text": address["address_text"],
        "title": address["title"],
        "confidence": address["confidence"],
        "sources": sources,
        "cites": cites,
        "note": ("SEATED BY THE LOT-ADDRESS POLICY (docs/LOT-ADDRESS.md; liberty L216). "
                 "The " + address["street_name"] + " notice prints a LOT AND A BLOCK — "
                 + address["address_text"] + " — which is the plat's own language and the "
                 "strongest placement statement in the corpus; " + printed + ", claims "
                 + ", ".join(cites) + ". THE ADDRESS IS WHAT THIS ROOF GAINS AND THE ONLY "
                 "THING IT GAINS: its existence, its position, its footprint and every "
                 "form value are the 665-roof programme's and are unchanged, its "
                 "`function` still reads as the anonymous family the recipe dealt it, and "
                 "no coordinate moved to seat this. THE NOTICE SAYS OF THIS LOT: "
                 + "; ".join(item["what"] for item in address["stood_on_the_lot"]) + ". "
                 + " ".join(item["note"] for item in drawn)
                 + (" " + " ".join(item["note"] for item in absent) if absent else "")
                 + " " + (address.get("advertiser") or {}).get("note", "")
                 + " " + address["confidence_note"]),
    }
    return {"lot_address": lot_address}


# The record's own key order, so that seating an address does not shuffle a generated
# file. `lot_address` follows `reconstruction` for the same reason `lot_claim` does: both
# are statements about the plat, and they read as a pair.
KEY_ORDER = ("id", "name", "aka", "archetype", "phases", "function", "occupants",
             "reconstruction", "lot_claim", "lot_address", "xref", "_frontage",
             "research_note", "review_required", "resident_assignment")


def apply(records: list[dict], placed: list[tuple[str, list[tuple[float, float]]]]
          ) -> int:
    """Seat every address that lands on one of `records`, in place. Returns the count."""
    seated = seat(placed)
    by_id = {r["id"]: r for r in records}
    for sid in sorted(seated):
        record = by_id.get(sid)
        if record is None:
            continue
        record["lot_address"] = seated[sid]["lot_address"]
        ordered = {k: record[k] for k in KEY_ORDER if k in record}
        leftover = {k: v for k, v in record.items() if k not in ordered}
        if leftover:
            raise AddressError("a seated record carries %s, which the key order does not "
                               "name" % ", ".join(sorted(leftover)))
        record.clear()
        record.update(ordered)
    return sum(1 for sid in seated if sid in by_id)


def committed() -> list[tuple[str, list[tuple[float, float]]]]:
    from plat_occupancy import footprints  # noqa: E402  (imported late: it reads data/)
    return footprints(load(DATA / "datum.json"))


def check() -> int:
    """Re-resolve every address against the committed town and assert what it seats."""
    seated = seat(committed())
    bad = 0
    for sid, blocks in sorted(seated.items()):
        path = STRUCTURES / f"{sid}.json"
        if not path.exists():
            print("  MISSING %s, which an address seats" % sid)
            bad = 1
            continue
        record = load(path)
        if record.get("lot_address") != blocks["lot_address"]:
            print("  %s does not carry the lot_address the ledger seats on it" % sid)
            bad = 1
        # Limit 2, re-read where it is SPENT rather than only where it is produced.
        for phase in record.get("phases") or []:
            grade = (phase.get("position") or {}).get("confidence")
            if grade != "reconstructed":
                print("  %s has been promoted to `%s` — a documented address does not "
                      "make a reconstructed roof evidence" % (sid, grade))
                bad = 1
    # An address the ledger carries and no record wears is an address that stopped being
    # spent — the exact failure mode the street-face table had for a day.
    for path in sorted(STRUCTURES.glob("*.json")):
        record = load(path)
        if "lot_address" in record and record["id"] not in seated:
            print("  %s carries a lot_address no committed address resolves to"
                  % record["id"])
            bad = 1
    if bad:
        return 1
    print("lot addresses: %d seated, %d in the ledger"
          % (len(seated), len(load(LEDGER).get("addresses", []))))
    return 0


def report() -> int:
    doc = load(LEDGER)
    placed = committed()
    for address in doc["addresses"]:
        ring = lot_polygon(address)
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        standing = sorted({sid for sid, poly in placed if _inside(_centroid(poly), ring)})
        print("%s — lot %d of block %d (%s)"
              % (address["id"], address["lot_number"], address["block_number"],
                 address["block_id"]))
        print("  the lot     E %+.1f … %+.1f, N %+.1f … %+.1f"
              % (min(xs), max(xs), min(ys), max(ys)))
        print("  seats       %s" % (", ".join(standing) or "nothing"))
        print("  printings   %d, %d cited (%s)"
              % (address["printings"], len(address["cites"]), address["first_issue"]
                 + " to " + address["last_issue"]))
        for item in address["stood_on_the_lot"]:
            print("  %-11s %s" % ("drawn" if item["drawn"] else "NOT drawn", item["what"]))
    return 0


def self_test() -> int:
    """Every refusal fires. A gate nobody has watched fail is decoration."""
    import copy
    doc = load(LEDGER)
    placed = committed()
    failed = 0

    def case(label: str, mutate) -> None:
        nonlocal failed
        broken = copy.deepcopy(doc)
        mutate(broken)
        try:
            _spend(broken, placed)
        except AddressError as exc:
            print("  fires: %s — %s" % (label, str(exc)[:72]))
            return
        failed = 1
        print("  FAIL  %s did not fire" % label)

    case("an address whose block number contradicts the committed numbering",
         lambda b: b["addresses"][0].update(block_id="blk_south_water_clark"))
    case("an address on a block the plat has not numbered",
         lambda b: b["addresses"][0].update(block_number=99))
    case("an address on a lot the block does not have",
         lambda b: b["addresses"][0].update(lot_number=9))
    case("an address citing no printing",
         lambda b: b["addresses"][0].update(cites=[]))
    case("a claim id that names no corpus source",
         lambda b: b["addresses"][0].update(cites=["the_tribune_1871#c1"]))
    case("an address that reads its advertiser as the occupant",
         lambda b: b["addresses"][0]["advertiser"].update(is_the_occupant=True))
    case("an address that reads its advertiser as the owner",
         lambda b: b["addresses"][0]["advertiser"].update(is_the_owner=True))
    case("an address graded above the tier its lot lines support",
         lambda b: b["addresses"][0].update(confidence="inferred"))
    case("two addresses on one roof",
         lambda b: b["addresses"].append(dict(b["addresses"][0], id="lot_address_twin")))

    seated = seat(placed)
    if not seated:
        print("  FAIL  nothing is seated, so nothing can be broken")
        return 1
    print("  ok:    %d address(es) seated on %d roof(s)"
          % (len(load(LEDGER)["addresses"]), len(seated)))
    return failed


def _spend(doc: dict, placed) -> None:
    """Seat a ledger held in memory. The self-test never writes to `data/`: a gate that
    edits the tree it is gating can leave it broken."""
    global LEDGER
    original = LEDGER
    try:
        LEDGER = _Memo(doc)
        seat(placed)
    finally:
        LEDGER = original


class _Memo:
    """A Path stand-in that reads back an in-memory ledger."""

    def __init__(self, doc: dict) -> None:
        self._text = json.dumps(doc)

    def exists(self) -> bool:
        return True

    def read_text(self, encoding: str = "utf-8") -> str:
        return self._text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.report:
            return report()
        if args.self_test:
            return self_test()
        return check()
    except AddressError as exc:
        print("LOT ADDRESS REFUSED: %s" % exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
