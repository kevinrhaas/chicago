#!/usr/bin/env python3
"""The location spend: what the evidence reached, what the town seated it on, and the
four standing questions that are RETAINED rather than answered (T-1239).

    tools/location_spend.py --build      write the adjudication and the report
    tools/location_spend.py --check      re-derive, diff, re-assert every limit
    tools/location_spend.py --self-test  break the assertions and require them to fire
    tools/location_spend.py --report     print the counts

WHAT THIS IS FOR.

T-1239 is the third piece of T-1147 and it owns two of the parent's clauses:

  * **clause 3** — keep exact placement proportional to evidence. An individual
    structure needs a resolvable anchor; a street-only business may occupy a labelled
    street face but claims no lot or roof; an unplaceable business stays visible in the
    register with its printed reason. **No completion metric rewards invented
    coordinates.**
  * **clause 4** — resolve or explicitly RETAIN T-0251, T-0305, T-0386 and T-1087. The
    61 street-only and 62 unplaceable counts may fall only when a new source or reading
    names the stronger anchor, and every move is shown in a before/after report.

T-1237 built the rows. This pass does not rebuild them and does not read the evidence
again: it reads the committed rows and adjudicates them.

THE FINDING THAT MADE THIS A TICKET AND NOT A PARAGRAPH.

T-1237's published axis says **56 businesses reach a structure**. Eleven of those
fifty-six reach a structure THE TOWN HAS NOT BUILT. The register's `new_building`
action means exactly that — the advertisement's anchor is good enough for a roof, and
the roof does not exist yet — so `action_target` is another business id or a corner
("dearborn+lake"), not a structure id, and the row resolves to no structure at all.
Read as a completion metric, 56 rewards eleven placements the model cannot make. Read
as an evidence metric it is correct: the paper did reach a roof. Both readings are
wanted and they are different numbers, so this pass publishes **both**, as a strict
refinement:

    published            adjudicated
    structure   56   ->  structure_committed    45   the anchor resolves to a roof
                         structure_pending      11   the roof is owed, not standing
    street_only 61   ->  street_only_adopted    40   seated under the 2026-08-29 ruling
                         street_only_unseated   21   the face could not be adopted
    unplaceable 62   ->  unplaceable            62   no street the model holds

**Nothing moves between the three published limits**, and that is clause 4's
requirement read literally: the limits fall only on a new source, this pass read no
new source, so the limits do not fall. What it adds is the honest denominator inside
each one.

THE OTHER HALF OF CLAUSE 3, AND THE TENSION IN IT.

Clause 3 says a street-only business "claims no lot or roof". Forty of the sixty-one
DO stand under a roof, because the owner's street-face adoption ruling of 2026-08-29
seats them there. That is not a violation to be repaired by overturning the owner; it
is two different facts wearing one field. So this pass separates them and gates the
separation:

  * `evidence_reach` is what the PAPER reached. For every adopted business it is the
    street, and it never becomes the roof.
  * `model_seat` is what the TOWN did about it, and every adopted seat is marked
    `substitutable: true` — the roof is housing, not a reading. It carries no lot, no
    anchor, and no confidence of its own.

An adopted roof that ever acquires an anchor target, or a lot, or stops matching the
committed adoption record, fails the gate. That is the line clause 3 is drawing, and
after this pass a later rung cannot cross it by accident.

THE FOUR RETENTIONS.

Clause 4 asks for a resolution or an explicit retention of T-0251, T-0305, T-0386 and
T-1087. **All four are retained, none is resolved, and not one of them is the loop's
to resolve**: three are `blocked-owner` and one is `blocked-tech` behind T-0414 and
T-0009. Writing that down in prose is what the four ticket files already do, and it is
not enough — a dossier goes quietly out of date the day its subject changes.

So each retention carries a GUARD: the committed fact it currently stands on, measured
at build time. A retention may say `retained` only while its guard holds. The day the
owner rules on Wabansia, or the saddlery leaves the watch list, or a Carver building is
committed, or the church moves, the guard stops holding and the BUILD says so instead
of this file lying. That is T-0305's own acceptance clause 5 — "the finding is held by
a gate rather than by this file" — applied to all four.

NOTHING HERE IS AUTHORED. Every placement row is derived from the committed rows, the
register's action, the adoption ledger and the structure ids the dataset holds; every
guard is re-read from the file it names. No confidence moves, no anchor is filled, no
building moves, and no count is improved.
"""
from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ROWS = ROOT / "data" / "research" / "location_reconciliation.json.gz"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
ADOPTIONS = ROOT / "data" / "research" / "newspapers" / "street_face_adoptions.json"
VOCABULARY = ROOT / "data" / "research" / "newspapers" / "place_vocabulary.json"
EXCLUSIONS = ROOT / "data" / "exclusions.json"
STRUCTURES = ROOT / "data" / "structures"
CHURCH = STRUCTURES / "first_presbyterian_church.json"

OUT = ROOT / "data" / "research" / "location_spend.json"
REPORT = ROOT / "docs" / "RESEARCH" / "location-spend.md"

SCENE_DATE = "1835-07-01"
AS_OF = "2026-09-17"

# The adjudicated classes, and the published limit each one refines.
REFINES = {
    "structure_committed": "structure",
    "structure_pending": "structure",
    "street_only_adopted": "street_only",
    "street_only_unseated": "street_only",
    "unplaceable": "unplaceable",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def committed_structures() -> set[str]:
    return {p.stem for p in sorted(STRUCTURES.glob("*.json"))}


def rows() -> list[dict]:
    doc = json.loads(gzip.decompress(ROWS.read_bytes()).decode("utf-8"))
    return doc["rows"], doc["counts"]


# ---------------------------------------------------------------------------
# the placements
# ---------------------------------------------------------------------------

def placements(business_rows, register, adoptions, known) -> list[dict]:
    actions = {b["id"]: b for b in register["businesses"]}
    adopted = {a["business_id"]: a for a in adoptions["adoptions"]}
    refused = {r["business_id"]: r for r in adoptions["refusals"]}
    out = []
    for row in sorted(business_rows, key=lambda r: r["business_id"]):
        bid = row["business_id"]
        entry = actions.get(bid, {})
        action = entry.get("action")
        target = entry.get("action_target")
        published = row["business_limit"]
        seat = row["resolved_structure"]
        if published == "structure":
            standing = target in known
            grade = "structure_committed" if standing else "structure_pending"
            reach = "structure" if standing else "structure_owed"
            why = (f"The advertisement's anchor reaches a roof and the register's "
                   f"{action} target {target!r} is a committed structure."
                   if standing else
                   f"The advertisement's anchor reaches a roof the town has not built: "
                   f"the register's {action} target is {target!r}, which is not a "
                   f"committed structure. Counted as reaching a roof by the evidence "
                   f"axis and as reaching none by the model's.")
        elif published == "street_only":
            deal = adopted.get(bid)
            grade = "street_only_adopted" if deal else "street_only_unseated"
            reach = "street"
            why = (f"The paper reaches {row['resolved_street']!r} and nothing narrower. "
                   f"The street-face adoption ruling of 2026-08-29 seated it on "
                   f"{seat!r}, which is housing and not a reading: substitutable, no "
                   f"lot, no anchor."
                   if deal else
                   "The paper reaches a platted street and nothing narrower, and the "
                   "face could not be adopted: "
                   f"{((refused.get(bid) or {}).get('refusal') or 'no adoption was recorded')}.")
        else:
            grade = "unplaceable"
            reach = "none"
            why = row["limit_clause"]
        out.append({
            "business_id": bid,
            "published_limit": published,
            "grade": grade,
            "evidence_reach": reach,
            "evidence_street": row["resolved_street"],
            "model_seat": seat,
            "seat_is_substitutable": grade == "street_only_adopted",
            "register_action": action,
            "register_action_target": target,
            "printed_place": row["printed_place"],
            "clause": why,
        })
    return out


# ---------------------------------------------------------------------------
# the four retentions
# ---------------------------------------------------------------------------

def retentions(known) -> list[dict]:
    """Each one measures the committed fact it stands on. `holds` false means the
    retention has expired and a run must re-state it — never that the gate may pass."""
    church = CHURCH.read_text(encoding="utf-8")
    vocabulary = read_json(VOCABULARY)
    places = {p["place"]: p for p in vocabulary["places"]}
    buckets = vocabulary["counts"]["persons_by_bucket"]
    watch = {w["id"] for w in read_json(EXCLUSIONS)["watch_list"]}
    register = read_json(REGISTER)
    montgomery = sorted(b["id"] for b in register["businesses"]
                        if "montgomery" in b["id"])
    montgomery_street_only = sorted(
        b["id"] for b in register["businesses"]
        if "montgomery" in b["id"] and b.get("action") == "street_only"
        and b.get("action_target") == "south_water")
    carver = sorted(s for s in known if "carver" in s)

    out = [
        {
            "ticket": "T-0251",
            "state": "blocked-owner",
            "owner": "the owner",
            "question": "Does a documented building displace an inferred unit when the "
                        "plat repair puts them on the same lot? first_presbyterian_church "
                        "needs 3.395 m to come onto the Lake Street plat and "
                        "physicians_office stands 3.15 m behind it.",
            "what_it_costs_today": "The church stands 1.90 m out in the platted roadway "
                                   "and two steps of Lake Street's plank walk stay unlaid.",
            "what_would_resolve_it": "The owner picking one of the three options the "
                                     "ticket measured, or naming a fourth. Never by "
                                     "weakening the 3.0 m separation gate.",
            "guard": {
                "reads": "data/structures/first_presbyterian_church.json",
                "expects": "the position note still carries the T-0251 refusal and its "
                           "1.90 m measurement, and physicians_office is still committed",
                "measured": {
                    "note_names_the_ticket": "T-0251" in church,
                    "note_carries_the_measurement": "1.90 m" in church,
                    "physicians_office_committed": "physicians_office" in known,
                },
            },
        },
        {
            "ticket": "T-0305",
            "state": "blocked-owner",
            "owner": "the owner — the page images are held outside this repository",
            "question": "Four readings the American contradicts itself on: the tailor's "
                        "street, which Water street two forwarding houses stood in, and "
                        "the cross street of Cobb's saddlery.",
            "what_it_costs_today": "Four business locations stay at the weaker reading; "
                                   "the saddlery's doubt is on the visitor's card.",
            "what_would_resolve_it": "Six columns of Chicago American page images — "
                                     "1835-06-13 p3 c5, 1835-07-04 p4 c4, 1835-06-27 p3 "
                                     "c5, 1835-08-15 p3 c6, 1835-06-08 p3 c5, 1835-07-11 "
                                     "p3 c6. The corpus was tested against all four and "
                                     "settles none.",
            "guard": {
                "reads": "data/exclusions.json",
                "expects": "the saddlery is still on the watch list, so its doubt still "
                           "reaches the Evidence panel",
                "measured": {
                    "saddlery_on_the_watch_list": "goss_cobb_saddlery" in watch,
                },
            },
        },
        {
            "ticket": "T-0386",
            "state": "blocked-tech",
            "owner": "T-0414, which waits on T-0009",
            "question": "W. Montgomery's auction room takes David Carver's old stand on "
                        "South Water Street — and both of the paper's anchors are "
                        "exhausted.",
            "what_it_costs_today": "The Montgomery entries stay street_only on South "
                                   "Water Street; no storefront stands.",
            "what_would_resolve_it": "T-0414's identity fix to the street-face adoption, "
                                     "which needs T-0009's roofs because South Water "
                                     "Street is out of supply — or a source that gives "
                                     "Carver's stand an address.",
            "guard": {
                "reads": "data/research/newspapers/register_1835.json and data/structures/",
                "expects": "every Montgomery entry is still street_only on south_water, "
                           "and the town still holds no Carver building",
                "measured": {
                    "montgomery_entries": montgomery,
                    "still_street_only_on_south_water": montgomery_street_only,
                    "carver_structures": carver,
                },
            },
        },
        {
            "ticket": "T-1087",
            "state": "blocked-owner",
            "owner": "the owner — resolution and basis are B-rules",
            "question": "place_vocabulary's B4 calls Wabansia and Kinzie's Addition "
                        "surveys this project commits none of, and it commits both. "
                        "Outside, inside, or B4 with a new reason?",
            "what_it_costs_today": "Exactly one person — person_uncertain_doctor_kimberly, "
                                   "the doctor in Wabansia — is scored undecided.",
            "what_would_resolve_it": "The owner writing `resolution` and `basis` for the "
                                     "two places, then "
                                     "`tools/resolve_place_vocabulary.py --write`.",
            "guard": {
                "reads": "data/research/newspapers/place_vocabulary.json",
                "expects": "both places are still undecided on B4 and the person buckets "
                           "are unmoved",
                "measured": {
                    "wabansia": [places["Wabansia"]["resolution"],
                                 places["Wabansia"]["basis"]],
                    "kinzies_addition": [places["Kinzie's Addition"]["resolution"],
                                         places["Kinzie's Addition"]["basis"]],
                    "persons_by_bucket": buckets,
                },
            },
        },
    ]
    for item in out:
        item["holds"] = _guard_holds(item)
        item["disposition"] = "retained" if item["holds"] else "expired"
    return out


EXPECTED_GUARDS = {
    "T-0251": {"note_names_the_ticket": True, "note_carries_the_measurement": True,
               "physicians_office_committed": True},
    "T-0305": {"saddlery_on_the_watch_list": True},
    "T-0386": {"montgomery_entries": ["business_l_w_montgomery_boot_and_shoe_maker",
                                      "business_montgomery_auction_and_commission_house",
                                      "business_w_montgomery",
                                      "business_w_montgomery_auction_and_commission_house"],
               "still_street_only_on_south_water":
                   ["business_l_w_montgomery_boot_and_shoe_maker",
                    "business_montgomery_auction_and_commission_house",
                    "business_w_montgomery",
                    "business_w_montgomery_auction_and_commission_house"],
               "carver_structures": []},
    "T-1087": {"wabansia": ["undecided", "B4"],
               "kinzies_addition": ["undecided", "B4"],
               "persons_by_bucket": {"inside": 1119, "outside": 141, "undecided": 25}},
}


def _guard_holds(item: dict) -> bool:
    return item["guard"]["measured"] == EXPECTED_GUARDS[item["ticket"]]


# ---------------------------------------------------------------------------
# the document
# ---------------------------------------------------------------------------

def build() -> dict:
    all_rows, published_counts = rows()
    known = committed_structures()
    register = read_json(REGISTER)
    adoptions = read_json(ADOPTIONS)
    business_rows = [r for r in all_rows if r["claim_kind"] == "business_location"]
    seats = placements(business_rows, register, adoptions, known)
    adjudicated = {grade: sum(1 for s in seats if s["grade"] == grade)
                   for grade in REFINES}
    return {
        "schema": "location_spend/1",
        "generated_by": "tools/location_spend.py",
        "ticket": "T-1239",
        "as_of": AS_OF,
        "scene_date": SCENE_DATE,
        "_doc": ("T-1147 clauses 3 and 4. What the evidence reached, what the town "
                 "seated it on, and the four standing questions retained rather than "
                 "answered. Derived from the committed reconciliation rows — do not "
                 "hand-edit; run tools/location_spend.py --build."),
        "compiled_from": [
            "data/research/location_reconciliation.json.gz",
            "data/research/newspapers/register_1835.json",
            "data/research/newspapers/street_face_adoptions.json",
            "data/research/newspapers/place_vocabulary.json",
            "data/exclusions.json",
            "data/structures/",
        ],
        "counts": {
            "businesses": len(seats),
            "published_limits": published_counts["businesses_by_location_limit"],
            "adjudicated_grades": adjudicated,
            "households_by_seating_class": published_counts[
                "households_by_seating_class"],
            "moved_between_published_limits": 0,
            "seats_that_are_substitutable": sum(
                1 for s in seats if s["seat_is_substitutable"]),
        },
        "placements": seats,
        "retentions": retentions(known),
    }


def write(doc: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                   encoding="utf-8")


def read_committed():
    try:
        return read_json(OUT)
    except (OSError, ValueError):
        return None


# ---------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------

def report(doc: dict) -> str:
    counts = doc["counts"]
    pub, adj = counts["published_limits"], counts["adjudicated_grades"]
    lines = [
        "# The location spend: evidence reach, model seat, and four retentions",
        "",
        f"Generated by `tools/location_spend.py` on {doc['as_of']}; scene date "
        f"{doc['scene_date']}. **Derived — do not hand-edit.** The adjudication lives "
        f"in `{OUT.relative_to(ROOT)}`; this is the review surface.",
        "",
        "T-1239, the third piece of T-1147, owning the parent's clause 3 (placement "
        "proportional to evidence) and clause 4 (resolve or explicitly retain T-0251, "
        "T-0305, T-0386 and T-1087). T-1237 built the rows; this pass adjudicates them "
        "and reads no evidence again.",
        "",
        "## Before and after: the business location limits",
        "",
        "Clause 4 says the 61 street-only and 62 unplaceable counts may fall only when "
        "a new source or reading names the stronger anchor. **This pass read no new "
        "source, so nothing moved between the three published limits.** What it adds "
        "is the denominator inside each one.",
        "",
        "| published limit | before | adjudicated grade | after | what the grade means |",
        "|---|---:|---|---:|---|",
        f"| structure | {pub['structure']} | `structure_committed` | "
        f"{adj['structure_committed']} | the anchor resolves to a roof the dataset holds |",
        f"| structure | {pub['structure']} | `structure_pending` | "
        f"{adj['structure_pending']} | the anchor reaches a roof the town has not built |",
        f"| street_only | {pub['street_only']} | `street_only_adopted` | "
        f"{adj['street_only_adopted']} | seated on an existing roof by the 2026-08-29 "
        "ruling; substitutable |",
        f"| street_only | {pub['street_only']} | `street_only_unseated` | "
        f"{adj['street_only_unseated']} | the face could not be adopted |",
        f"| unplaceable | {pub['unplaceable']} | `unplaceable` | {adj['unplaceable']} | "
        "no street the model holds |",
        "",
        f"**{counts['moved_between_published_limits']} businesses moved between the "
        "published limits.** The three counts T-1157 reads as the sign-off's location "
        f"axis are unchanged at {pub['structure']} / {pub['street_only']} / "
        f"{pub['unplaceable']}.",
        "",
        "### Why `structure` needed splitting",
        "",
        f"The register's `new_building` action means the advertisement's anchor is good "
        f"enough for a roof and the roof does not exist yet, so its `action_target` is "
        f"another business or a corner rather than a structure id. "
        f"{adj['structure_pending']} of the {pub['structure']} are in that state. Read "
        "as an evidence metric, 56 is right: the paper did reach a roof. Read as a "
        "completion metric it rewards eleven placements the model cannot make. Both "
        "numbers are wanted, so both are published — and no row in "
        "`structure_pending` names a structure.",
        "",
        "### Why an adopted roof is not a claim",
        "",
        "Clause 3 says a street-only business claims no lot or roof, and "
        f"{adj['street_only_adopted']} of them stand under one — because the owner's "
        "street-face adoption ruling of 2026-08-29 seats them there. Two facts were "
        "wearing one field. They are separated here: `evidence_reach` is the street the "
        "paper named and never becomes the roof, `model_seat` is what the town did "
        f"about it, and all {counts['seats_that_are_substitutable']} adopted seats are "
        "marked `seat_is_substitutable`. An adopted roof that acquires an anchor "
        "target, or a lot, or stops matching the committed adoption ledger, fails the "
        "gate.",
        "",
        "## Households, by seating class",
        "",
        "Unchanged by this pass and restated because it is the other half of the axis "
        "T-1157 reads.",
        "",
        "| class | households |",
        "|---|---:|",
    ]
    for cls, n in counts["households_by_seating_class"].items():
        lines.append(f"| {cls} | {n} |")
    lines += [
        "",
        "## The four retentions",
        "",
        "**All four are retained, none is resolved, and not one is the loop's to "
        "resolve** — three are `blocked-owner` and one is `blocked-tech` behind T-0414 "
        "and T-0009. Each retention carries a guard: the committed fact it stands on, "
        "re-measured on every build. A retention may read `retained` only while its "
        "guard holds, so the day the owner rules — or a source lands — the build says "
        "so instead of this file going quietly out of date.",
        "",
        "| ticket | state | what it costs today | what would resolve it | guard |",
        "|---|---|---|---|---|",
    ]
    for item in doc["retentions"]:
        lines.append(
            f"| {item['ticket']} | {item['disposition']} | {item['what_it_costs_today']} "
            f"| {item['what_would_resolve_it']} | {item['guard']['expects']} |")
    lines += [
        "",
        "No retention upgraded a confidence, filled an anchor, minted a citation or "
        "moved a building. Four questions were asked of the committed data and four "
        "answers came back unchanged.",
        "",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# the gate
# ---------------------------------------------------------------------------

class Refused(Exception):
    pass


def assertions(doc: dict) -> None:
    """Each one is a way this adjudication could lie."""
    seats = doc["placements"]
    if not seats:
        raise Refused("no placements: the adjudication is empty")
    ids = [s["business_id"] for s in seats]
    if len(ids) != len(set(ids)):
        raise Refused("business_id is not unique")
    known = committed_structures()
    for seat in seats:
        grade = seat["grade"]
        if grade not in REFINES:
            raise Refused(f"{seat['business_id']}: unknown grade {grade!r}")
        if REFINES[grade] != seat["published_limit"]:
            raise Refused(f"{seat['business_id']}: grade {grade!r} does not refine the "
                          f"published limit {seat['published_limit']!r} — a business "
                          "may not move between the limits without a new source")
        if not seat["clause"]:
            raise Refused(f"{seat['business_id']}: no clause")
        # NO ROW INVENTS A BUILDING.
        if seat["model_seat"] and seat["model_seat"] not in known:
            raise Refused(f"{seat['business_id']}: model_seat {seat['model_seat']!r} is "
                          "not a committed structure")
        # A ROOF THE TOWN HAS NOT BUILT IS NOT A ROOF IT HAS.
        if grade == "structure_pending" and seat["model_seat"]:
            raise Refused(f"{seat['business_id']}: structure_pending, yet it seats on "
                          f"{seat['model_seat']!r}")
        if grade == "structure_committed" and not seat["model_seat"]:
            raise Refused(f"{seat['business_id']}: structure_committed with no seat")
        # AN ADOPTED ROOF IS HOUSING, NOT A READING.
        if grade == "street_only_adopted":
            if not seat["model_seat"]:
                raise Refused(f"{seat['business_id']}: adopted with no seat")
            if not seat["seat_is_substitutable"]:
                raise Refused(f"{seat['business_id']}: an adopted seat that is not "
                              "substitutable — clause 3 says the roof is not the claim")
            if seat["evidence_reach"] != "street":
                raise Refused(f"{seat['business_id']}: an adopted business whose "
                              f"evidence reach is {seat['evidence_reach']!r}, not the "
                              "street the paper named")
        if grade == "street_only_unseated" and seat["model_seat"]:
            raise Refused(f"{seat['business_id']}: unseated, yet it seats on "
                          f"{seat['model_seat']!r}")
        # AN UNPLACEABLE BUSINESS CLAIMS NO GROUND AND KEEPS ITS PRINTED REASON.
        if grade == "unplaceable":
            if seat["model_seat"] or seat["evidence_street"]:
                raise Refused(f"{seat['business_id']}: unplaceable, yet it reaches ground")
            if not seat["printed_place"]:
                raise Refused(f"{seat['business_id']}: unplaceable with no printed reason")
        if seat["seat_is_substitutable"] and grade != "street_only_adopted":
            raise Refused(f"{seat['business_id']}: only an adopted seat is substitutable")
    counts = doc["counts"]
    if sum(counts["adjudicated_grades"].values()) != len(seats):
        raise Refused("the grades do not partition the businesses")
    for limit, published in counts["published_limits"].items():
        refined = sum(n for grade, n in counts["adjudicated_grades"].items()
                      if REFINES[grade] == limit)
        if refined != published:
            raise Refused(f"the {limit!r} grades total {refined}, not the published "
                          f"{published} — clause 4 says a limit falls only on a new source")
    if counts["moved_between_published_limits"] != 0:
        raise Refused("a business moved between the published limits; clause 4 requires "
                      "a new source or reading for that, and this pass reads none")
    # THE RETENTIONS ARE HELD BY THIS GATE AND NOT BY PROSE.
    retained = doc["retentions"]
    if {r["ticket"] for r in retained} != set(EXPECTED_GUARDS):
        raise Refused("the retentions do not name T-0251, T-0305, T-0386 and T-1087")
    for item in retained:
        if item["disposition"] == "retained" and not item["holds"]:
            raise Refused(f"{item['ticket']}: retained, yet its guard no longer holds")
        if not item["holds"]:
            raise Refused(
                f"{item['ticket']}: its guard has expired — the committed data it "
                f"stood on has changed ({item['guard']['reads']}). Re-read the ticket "
                "and re-state the retention; a gate may not count this as a pass.")
        if not item["what_would_resolve_it"]:
            raise Refused(f"{item['ticket']}: retained with no route out")


def check() -> int:
    committed = read_committed()
    if committed is None:
        print(f"REFUSED: {OUT.relative_to(ROOT)} is missing or unreadable — run --build")
        return 1
    fresh = build()
    if fresh["placements"] != committed["placements"]:
        fresh_ids = {s["business_id"]: s for s in fresh["placements"]}
        old_ids = {s["business_id"]: s for s in committed["placements"]}
        added = sorted(set(fresh_ids) - set(old_ids))
        gone = sorted(set(old_ids) - set(fresh_ids))
        changed = sorted(k for k in set(fresh_ids) & set(old_ids)
                         if fresh_ids[k] != old_ids[k])
        print("REFUSED: a rebuild would not produce the committed placements.")
        for label, items in (("added", added), ("gone", gone), ("changed", changed)):
            if items:
                print(f"  {label} ({len(items)}): {', '.join(items[:5])}"
                      + (" ..." if len(items) > 5 else ""))
        return 1
    if fresh["counts"] != committed["counts"]:
        print("REFUSED: the committed counts are not what the placements say.")
        return 1
    if fresh["retentions"] != committed["retentions"]:
        moved = sorted(f["ticket"] for f, o in zip(fresh["retentions"],
                                                   committed["retentions"]) if f != o)
        print("REFUSED: a retention no longer describes the committed data: "
              + ", ".join(moved) + ". Re-read the ticket and re-state it.")
        return 1
    try:
        assertions(committed)
    except Refused as exc:
        print(f"REFUSED: {exc}")
        return 1
    if REPORT.read_text(encoding="utf-8") != report(committed):
        print(f"REFUSED: {REPORT.relative_to(ROOT)} is not what the adjudication says — "
              "run --build")
        return 1
    counts = committed["counts"]
    print(f"{counts['businesses']} businesses adjudicated; "
          f"{counts['adjudicated_grades']}; "
          f"{len(committed['retentions'])} retentions hold")
    return 0


def self_test() -> int:
    """Break each limit and require its assertion to fire."""
    doc = read_committed() or build()
    faults = []

    def fires(name, mutate):
        broken = json.loads(json.dumps(doc))
        mutate(broken)
        try:
            assertions(broken)
        except Refused as exc:
            print(f"  fires: {name} -> {exc}")
            return
        faults.append(name)

    def pick(grade):
        return lambda d: next(s for s in d["placements"] if s["grade"] == grade)

    def duplicate(d):
        d["placements"].append(json.loads(json.dumps(d["placements"][0])))

    def pending_gains_a_roof(d):
        pick("structure_pending")(d)["model_seat"] = next(iter(committed_structures()))

    def invented_seat(d):
        pick("street_only_adopted")(d)["model_seat"] = "a_building_nobody_holds"

    def adopted_roof_hardens(d):
        pick("street_only_adopted")(d)["seat_is_substitutable"] = False

    def adopted_reach_climbs(d):
        pick("street_only_adopted")(d)["evidence_reach"] = "structure"

    def unseated_gains_a_roof(d):
        pick("street_only_unseated")(d)["model_seat"] = next(iter(committed_structures()))

    def unplaceable_gains_ground(d):
        pick("unplaceable")(d)["evidence_street"] = "Lake Street"

    def unplaceable_loses_its_reason(d):
        pick("unplaceable")(d)["printed_place"] = None

    def a_business_changes_limit(d):
        pick("unplaceable")(d)["grade"] = "street_only_unseated"

    def a_limit_falls(d):
        d["counts"]["published_limits"]["unplaceable"] -= 1

    def a_move_is_declared(d):
        d["counts"]["moved_between_published_limits"] = 1

    def a_retention_expires(d):
        d["retentions"][3]["guard"]["measured"]["wabansia"] = ["outside", "B2"]
        d["retentions"][3]["holds"] = False
        d["retentions"][3]["disposition"] = "expired"

    def a_retention_lies(d):
        d["retentions"][0]["holds"] = False

    def a_retention_goes_missing(d):
        d["retentions"].pop()

    def a_retention_has_no_route_out(d):
        d["retentions"][1]["what_would_resolve_it"] = ""

    fires("a duplicated business", duplicate)
    fires("a pending roof that acquires a seat", pending_gains_a_roof)
    fires("a seat the dataset does not hold", invented_seat)
    fires("an adopted roof that stops being substitutable", adopted_roof_hardens)
    fires("an adopted business whose evidence reach climbs to the roof", adopted_reach_climbs)
    fires("an unseated street-only business that acquires a roof", unseated_gains_a_roof)
    fires("an unplaceable business that reaches ground", unplaceable_gains_ground)
    fires("an unplaceable business with no printed reason", unplaceable_loses_its_reason)
    fires("a business that changes published limit", a_business_changes_limit)
    fires("a published limit that falls without a source", a_limit_falls)
    fires("a declared move between the limits", a_move_is_declared)
    fires("a retention whose guard has expired", a_retention_expires)
    fires("a retention that claims to hold and does not", a_retention_lies)
    fires("a retention that goes missing", a_retention_goes_missing)
    fires("a retention with no route out", a_retention_has_no_route_out)

    if faults:
        print("SELF-TEST FAILED — these assertions did not fire: " + ", ".join(faults))
        return 1
    print("all 15 assertions fire when broken")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    if "--report" in argv:
        print(report(read_committed() or build()), end="")
        return 0
    if "--build" in argv:
        doc = build()
        assertions(doc)
        write(doc)
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(report(doc), encoding="utf-8")
        counts = doc["counts"]
        print(f"wrote {OUT.relative_to(ROOT)} ({counts['businesses']} businesses) "
              f"and {REPORT.relative_to(ROOT)}")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
