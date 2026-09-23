#!/usr/bin/env python3
"""The written ruling on all 1,572 land-sale purchaser units (T-1296).

    python3 tools/spend_land_sales_rulings.py            write the ruling register
    python3 tools/spend_land_sales_rulings.py --check    it re-derives; nothing drifted
    python3 tools/spend_land_sales_rulings.py --self-test the rules below, held over what
                                                         they derive

WHY THIS EXISTS. T-1234 gave the research-spend ledger a place to write a ruling down:
`data/research/spend_rulings.json`, consulted only where a reading's own dispositions run
out, a named rule with a stated reason and a note on every single unit it closes. That
file is HAND-AUTHORED and holds 87 rulings. This corpus is 1,572 rows of one register,
and typing 1,572 notes by hand would be a worse register, not a better one: the notes
would drift, and nobody could prove the ruling matched the row it claims to rule.

So this register is DERIVED, from the two files that already carry the judgement:

    data/research/land_sales/records/*.json          the register as read (T-0636)
    data/research/land_sales/resident_crosswalk.json the identities, ADJUDICATED under
                                                     T-0700 / T-0850

and `--check` re-derives it. Nothing here re-adjudicates an identity, moves a grade,
mints a person or writes to data/residents/. Every note is built out of the row's own
fields — its purchase number, its date, its Residence column, its tract — so a reader can
put the note beside the row and see that it says what the row says.

THE STANDING RULE THIS DOMAIN WAS READ UNDER, and the one every ruling below obeys: a
purchase is a TRANSACTION and not a RESIDENCE. The register's own Residence column is the
only thing on the page that speaks to residence at all, and it reads COOK, ILLINOIS, some
other county, or UNKNOWN — a county, a state, or nothing, and never a town. A row can
bound a presence. It can never assert one.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "data" / "research" / "land_sales" / "records"
CROSSWALK = ROOT / "data" / "research" / "land_sales" / "resident_crosswalk.json"
OUT = ROOT / "data" / "research" / "land_sales" / "spend_rulings.json"
SCENE_DATE = "1835-07-01"
TICKET = "T-1296"

# The Residence column, when it is not UNKNOWN and not Cook. Illinois is NOT in this set:
# Cook is in Illinois, so a row reading ILLINOIS states a state and excludes nothing.
OUTSIDE_COOK = {
    "MACON": "Macon County, Illinois",
    "VERMILION": "Vermilion County, Illinois",
    "MCLEAN": "McLean County, Illinois",
    "CHAMPAIGN": "Champaign County, Illinois",
    "LASALLE": "LaSalle County, Illinois",
    "IROQUOIS": "Iroquois County, Illinois",
    "VIRGINIA": "the state of Virginia",
    "ST. LOUIS": "St. Louis, Missouri",
}

RULES = {
    "the_purchaser_is_a_corporate_body": {
        "disposition": "refused",
        "statement": (
            "The register sold this tract to a BODY and not to a person: the crosswalk's "
            "declared `body_purchasers` names the purchaser a corporation, a county "
            "commission or a public fund buying on an account. A body has no residence, no "
            "arrival and no place in a population, so the row carries no 1835 person fact "
            "to assert or to refuse. What it evidences is a transfer of land, which the "
            "land layer already holds; the person ledger's answer is that there is no "
            "person here, and that is a finished answer rather than a deferral."),
    },
    "the_purchaser_is_a_firm_style": {
        "disposition": "refused",
        "statement": (
            "The purchaser is entered in a FIRM style and the crosswalk's declared "
            "`firm_purchasers` names it one. A firm name carries a partner's surname, but "
            "the register does not say which individual stood behind the entry on the day, "
            "and this domain's standing rule is that a surname-only join is always a "
            "refusal. The row evidences a firm's purchase; it does not place any named "
            "person at Chicago, and it is refused as a person unit rather than joined to a "
            "card on the strength of a trading style."),
    },
    "the_registers_date_is_unreadable": {
        "disposition": "refused",
        "statement": (
            "The register's `date_purchased` for this row does not read as a date in the "
            "nineteenth century: the transcription carries a stub, a fragment or an "
            "impossible year. So the row cannot be placed before or after the 1 July 1835 "
            "scene date, and a purchase that cannot be dated bounds nothing. This project "
            "records the unreadable reading rather than repairing it into a year nobody "
            "printed, and the refusal names the string the register actually carries."),
    },
    "the_register_places_the_purchaser_outside_cook": {
        "disposition": "outside_chicago",
        "statement": (
            "The register's own Residence column — the only column on the page that speaks "
            "to residence at all — names a county or a state that is NOT Cook. That is the "
            "source stating, in its own words, that the purchaser lived somewhere else when "
            "the tract was entered. The row is a transaction at Chicago by a person the "
            "document places away from it, and it is an outside-Chicago reading rather than "
            "a refusal because the source answers the question instead of leaving it open."),
    },
    "the_purchase_is_later_than_the_scene_date": {
        "disposition": "later_only",
        "statement": (
            "The tract was entered after 1 July 1835, so under the evidence ladder ratified "
            "in T-0513 the row may corroborate and may date, and may not assert an 1835 "
            "fact. It is written here rather than caught by the ledger's own year test "
            "because a land-sale row prints its date inside `sale.date_purchased`, which is "
            "none of the fields that test reads. A purchase is in any case a transaction "
            "and not a residence, so the later row says nothing about the scene either way."),
    },
    "the_purchase_bounds_a_held_residents_presence": {
        "disposition": "unresolved",
        "ticket": "T-1169",
        "statement": (
            "The tract was entered on or before 1 July 1835 and the crosswalk's "
            "adjudication under T-0700 / T-0850 UPHELD the join between this purchaser and "
            "a person this town holds a card for. A purchase is never a residence, but a "
            "dated entry by a named person is a dated appearance, and the earliest dated "
            "appearance is the bound T-1169 works from. This ruling hands the date on and "
            "asserts nothing: it does not move the person's grade, write an arrival, or "
            "reopen an identity the crosswalk has already ruled."),
    },
    "the_cook_residence_names_a_withheld_person": {
        "disposition": "unresolved",
        "ticket": "T-1159",
        "statement": (
            "The tract was entered on or before 1 July 1835, the register's Residence "
            "column reads COOK, and no upheld crosswalk join puts this purchaser on a card "
            "this town holds — either the identity was weighed and refused, or the layer has "
            "never seen the name. A county is not a town and this row mints nobody, but it "
            "is a dated document stating that a named person lived in Cook County inside "
            "the scene window. That is exactly the read-and-withheld name T-1159's "
            "borderline roster exists to carry, with its source and its re-admission class."),
    },
    "a_sale_is_never_a_residence": {
        "disposition": "refused",
        "statement": (
            "The tract was entered on or before 1 July 1835 by a purchaser whose Residence "
            "column the register leaves UNKNOWN, or gives only as ILLINOIS — a state, and "
            "not a place anyone lives. No upheld crosswalk join puts the name on a card this "
            "town holds. Under the standing rule this whole domain was read under — a "
            "purchase is a transaction and not a residence — the row evidences that this "
            "name entered this tract on this day and nothing further. It asserts no 1835 "
            "person, and the refusal is the finished answer rather than a deferral."),
    },
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def record_files() -> list[Path]:
    return sorted(RECORDS.glob("*.json"))


def crosswalk_index(crosswalk: dict) -> dict[str, tuple[str, dict]]:
    """record id -> (how the crosswalk disposed of the purchaser, the block that did)."""
    index: dict[str, tuple[str, dict]] = {}
    for match in crosswalk.get("matches") or []:
        ruled = (match.get("ruling") or {}).get("ruling")
        kind = "upheld" if ruled in {"upheld", "named"} else "proposed"
        for rid in match.get("record_ids") or []:
            index[rid] = (kind, match)
    for refusal in crosswalk.get("refusals") or []:
        for rid in refusal.get("record_ids") or []:
            index.setdefault(rid, ("refused", refusal))
    for firm in crosswalk.get("firm_purchasers") or []:
        for rid in firm.get("record_ids") or []:
            index[rid] = ("firm", firm)
    for body in crosswalk.get("body_purchasers") or []:
        for rid in body.get("record_ids") or []:
            index[rid] = ("body", body)
    return index


def where(row: dict) -> str:
    """The row's own locator, in one clause, so a note can be checked against the page."""
    loc = row.get("locator") or {}
    tract = row.get("tract") or {}
    if tract.get("resolves") == "town_plat_lot" and tract.get("lot"):
        place = f"lot {tract['lot']} block {tract['block']} of {tract.get('town_code') or 'the town plat'}"
    elif tract.get("section"):
        place = (f"section {tract['section']}, T{tract.get('township') or '?'} "
                 f"R{tract.get('range') or '?'}")
    else:
        place = f"the tract entered as {tract.get('part') or 'an unparsed description'}"
    return (f"purchase {loc.get('purchase_no') or '?'}, volume {loc.get('volume') or '?'} "
            f"page {loc.get('page') or '?'}, {place}")


def classify(row: dict, disposal: tuple[str, dict] | None) -> tuple[str, str]:
    """The rule this row falls under, and the note saying why THIS row fell under it."""
    sale = row.get("sale") or {}
    date = str(sale.get("date_purchased") or "")
    printed = str(sale.get("date_as_read") or date or "nothing")
    residence = str(sale.get("residence_as_read") or "").strip().upper()
    name = row.get("normalized") or row.get("as_read") or row["id"]
    as_read = row.get("as_read") or name
    kind, block = disposal if disposal else ("none", {})
    seen = f"{as_read!r} read as {name}"

    if kind == "body":
        return "the_purchaser_is_a_corporate_body", (
            f"The register enters {seen} at {where(row)} on {printed}. The crosswalk "
            f"declares this purchaser a body: {block.get('what_the_register_sold_to') or 'a public account'} "
            f"No person is named by the row.")
    if kind == "firm":
        return "the_purchaser_is_a_firm_style", (
            f"The register enters {seen} at {where(row)} on {printed}. The crosswalk "
            f"declares this a firm in the {block.get('firm_style') or 'partnership'} style, expanded as "
            f"{block.get('firm_expanded') or as_read}; which partner entered the tract is not on the page.")
    if not re.fullmatch(r"18\d\d-[01]\d-[0-3]\d", date):
        return "the_registers_date_is_unreadable", (
            f"The register enters {seen} at {where(row)} and prints its date as {printed!r}, "
            f"stored as {date!r}. That is not a nineteenth-century date, so this purchase "
            f"cannot be placed against 1 July 1835 at all.")
    if residence in OUTSIDE_COOK:
        return "the_register_places_the_purchaser_outside_cook", (
            f"The register enters {seen} at {where(row)} on {date}, and gives the residence "
            f"as {residence!r} — {OUTSIDE_COOK[residence]}, not Cook. The document places "
            f"this purchaser away from the town it bought in.")
    if date > SCENE_DATE:
        return "the_purchase_is_later_than_the_scene_date", (
            f"The register enters {seen} at {where(row)} on {date}, which is after the "
            f"1 July 1835 scene date; the residence column reads {residence or 'nothing'}. "
            f"The row may date this name later and may not put it in the 1835 town.")
    if kind == "upheld":
        return "the_purchase_bounds_a_held_residents_presence", (
            f"The register enters {seen} at {where(row)} on {date}. The crosswalk upholds "
            f"the join to {block.get('resident_name') or block.get('resident_id')} "
            f"({block.get('resident_id')}) on the ground: {block.get('match')}. The date is a "
            f"bound on that person's presence and is handed to the arrival pass unasserted.")
    if residence == "COOK":
        withheld = ("the crosswalk weighed a candidate of this name and refused it"
                    if kind == "refused" else
                    "the crosswalk proposed a candidate this town has not adjudicated"
                    if kind == "proposed" else
                    "the residents layer holds no candidate of this name at all")
        return "the_cook_residence_names_a_withheld_person", (
            f"The register enters {seen} at {where(row)} on {date} and states the residence "
            f"as COOK; {withheld}. A named person in Cook County before the scene date, read "
            f"and withheld — the borderline roster's case exactly.")
    return "a_sale_is_never_a_residence", (
        f"The register enters {seen} at {where(row)} on {date}, with the residence column "
        f"reading {residence or 'nothing'}. "
        + ("The crosswalk weighed a candidate of this name and refused it. "
           if kind == "refused" else
           "The crosswalk proposed a candidate this town has not adjudicated. "
           if kind == "proposed" else
           "The residents layer holds no candidate of this name. ")
        + "What the row documents is that this name entered this tract on this day.")


def build_document() -> dict:
    crosswalk = read_json(CROSSWALK)
    index = crosswalk_index(crosswalk)
    rulings = []
    for path in record_files():
        relative = path.relative_to(ROOT).as_posix()
        for row in read_json(path).get("records") or []:
            rule, note = classify(row, index.get(row["id"]))
            rulings.append({
                "unit": f"land_sales:{relative}#records/{row['id']}",
                "rule": rule,
                "note": note,
            })
    tally = Counter(r["rule"] for r in rulings)
    return {
        "schema": "research-spend-rulings-v1",
        "_doc": (
            "DERIVED, T-1296, by tools/spend_land_sales_rulings.py from "
            "the records/ and resident_crosswalk.json beside it — run "
            "--check to re-derive it. The written ruling on every land-sale purchaser unit "
            "the ledger leaves unresolved. tools/research_spend_ledger.py reads this file "
            "beside the hand-authored spend_rulings.json, at the point where it would "
            "otherwise leave a unit open, so a ruling here can only close a unit nothing "
            "else has closed and can never overturn an assertion, a later_only or a refusal "
            "the readings themselves carry. NOTHING HERE EDITS A RESIDENT, MINTS A PERSON, "
            "MOVES A CONFIDENCE OR REOPENS AN IDENTITY THE CROSSWALK RULED. A hand-off is "
            "not a spend: it names the open ticket whose field owns the finding, and that "
            "ticket closing turns this file red, which is the point."),
        "ticket": TICKET,
        "generated_by": "tools/spend_land_sales_rulings.py",
        "counts": {rule: tally[rule] for rule in sorted(tally)},
        "rules": RULES,
        "rulings": rulings,
    }


def write(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def self_test() -> int:
    """Hold each rule over a row built to fall under it, and over one that must not."""
    failures = []
    base = {
        "id": "ls9001", "as_read": "DOE JOHN", "normalized": "John Doe",
        "locator": {"purchase_no": "1", "volume": "L1", "page": "001"},
        "tract": {"section": "4", "township": "39N", "range": "14E", "resolves": "section"},
        "sale": {"date_purchased": "1834-05-01", "date_as_read": "05/01/1834",
                 "residence_as_read": "UNKNOWN"},
    }

    def held(label, row, disposal, want):
        rule, note = classify(row, disposal)
        if rule != want:
            failures.append(f"{label}: fell under {rule!r}, wanted {want!r}")
        elif len(note.strip()) < 20:
            failures.append(f"{label}: note is too short to say why this row fell under it")
        else:
            print(f"  rules: {label} -> {want}")

    def with_sale(**kw):
        row = json.loads(json.dumps(base))
        row["sale"].update(kw)
        return row

    held("a body purchaser", base, ("body", {"what_the_register_sold_to": "The county."}),
         "the_purchaser_is_a_corporate_body")
    held("a firm purchaser", base, ("firm", {"firm_style": "AND CO", "firm_expanded": "X & Co."}),
         "the_purchaser_is_a_firm_style")
    held("an unreadable date", with_sale(date_purchased="1000", date_as_read="1000"), None,
         "the_registers_date_is_unreadable")
    held("a residence outside Cook", with_sale(residence_as_read="MACON"), None,
         "the_register_places_the_purchaser_outside_cook")
    held("a purchase after the scene date", with_sale(date_purchased="1836-06-28"), None,
         "the_purchase_is_later_than_the_scene_date")
    held("an upheld identity before the scene date", base,
         ("upheld", {"resident_name": "John Doe", "resident_id": "doe_john", "match": "forename_agrees"}),
         "the_purchase_bounds_a_held_residents_presence")
    held("a COOK residence with no upheld identity", with_sale(residence_as_read="COOK"), None,
         "the_cook_residence_names_a_withheld_person")
    held("the standing refusal", base, ("refused", {}), "a_sale_is_never_a_residence")
    # An upheld identity AFTER the scene date is later_only and not a presence bound:
    # the ladder outranks the identity, which is the ordering T-0513 ratified.
    held("an upheld identity after the scene date", with_sale(date_purchased="1836-01-02"),
         ("upheld", {"resident_name": "John Doe", "resident_id": "doe_john", "match": "x"}),
         "the_purchase_is_later_than_the_scene_date")
    # A COOK residence for an upheld resident is a bound, not a borderline name.
    held("a COOK residence on a held resident", with_sale(residence_as_read="COOK"),
         ("upheld", {"resident_name": "John Doe", "resident_id": "doe_john", "match": "x"}),
         "the_purchase_bounds_a_held_residents_presence")

    for name, rule in sorted(RULES.items()):
        if len(rule["statement"].strip()) < 40:
            failures.append(f"rule {name}: states no rule")
        if rule["disposition"] == "unresolved" and not rule.get("ticket"):
            failures.append(f"rule {name}: hands the unit on and names no ticket")

    doc = build_document()
    if len(doc["rulings"]) != len({r["unit"] for r in doc["rulings"]}):
        failures.append("two rulings on one unit")
    unfired = sorted(set(RULES) - set(doc["counts"]))
    if unfired:
        failures.append("rules that never fire over the committed register: " + ", ".join(unfired))

    for line in failures:
        print(f"FAIL {line}")
    print(f"LAND-SALE RULING SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), {len(RULES)} rule(s), {len(doc['rulings'])} unit(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="re-derive and prove nothing drifted")
    parser.add_argument("--self-test", action="store_true", help="hold the rules over the rows")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    doc = build_document()
    if args.check:
        if not OUT.exists():
            print(f"FAIL {OUT.relative_to(ROOT)} is missing — run tools/spend_land_sales_rulings.py")
            return 1
        if read_json(OUT) != doc:
            print(f"FAIL {OUT.relative_to(ROOT)} is stale — run tools/spend_land_sales_rulings.py")
            return 1
        if not args.quiet:
            print(f"OK land-sale rulings re-derive: {len(doc['rulings'])} units, "
                  + ", ".join(f"{k} {v}" for k, v in doc["counts"].items()))
        return 0
    write(doc)
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['rulings'])} rulings")
    for rule, n in doc["counts"].items():
        print(f"  {n:5d}  {rule}  ({RULES[rule]['disposition']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
