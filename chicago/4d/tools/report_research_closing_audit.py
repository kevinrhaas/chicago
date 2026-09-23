#!/usr/bin/env python3
"""The closing research audit: the T-1143 ledger read over the four town layers (T-1241).

WHY THIS EXISTS AND WHAT IT IS NOT. `research_spend_ledger.py` accounts for research from
the SOURCE side: every registered reading unit gets one durable disposition, and the gate
refuses an unclassified one. That is a complete answer to "what did we read, and what did
we rule about it" and no answer at all to "what did the town end up carrying". A ledger at
zero unclassified units is compatible with a town whose businesses have no proprietors and
whose roofs have no occupants, because those are two different books.

This is the other book. It reads the ledger's asserted units onto the layers they land in,
then reads the layers themselves, and prints the two beside each other so a gap is visible
as a gap rather than as a silence. T-1157 signs the research spend off; this is the
evidence section it reads, and it makes NO GO/NO-GO judgement of its own.

A STATED GAP IS A FINISHED ANSWER. The bar here is not that every number is large. It is
that every number is DERIVED — nothing in the report below is typed — and that the
report says plainly where the research stopped. Section 7 exists to be read, not to be
driven to zero.

`--build` writes the report; `--check` re-derives it and refuses a drifted one, which is
how tools/check.sh consumes it; `--self-test` mutates the measurement and proves the check
fires.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from research_spend_ledger import (  # noqa: E402
    LEDGER,
    OPEN_TICKET_STATES,
    read_ledger,
    ticket_states,
)

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs" / "RESEARCH" / "research-closing-audit-2026-09.md"
RESIDENT_INDEX = ROOT / "data" / "residents" / "index.json"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
STRUCTURES = ROOT / "data" / "structures"
AS_OF = "2026-09-18"

# The four layers this audit is asked about, and the one rule that decides which layer an
# asserted unit landed in: the file it wrote to. A household record lives under
# data/residents/households/, so the prefix order below matters and the longest wins.
LAYER_PREFIXES = (
    ("households", "data/residents/households/"),
    ("residents", "data/residents/"),
    ("businesses", "data/research/newspapers/register_1835.json"),
    # T-1508 gave the ledger a SECOND business surface: the authored layer, one record
    # per firm, reached by a block's own `claim_ids`. Without this prefix its units land
    # in `elsewhere`, and the table below would report 0 businesses researched on the
    # same run that spent 485 units on them.
    ("businesses", "data/businesses/"),
    ("structures", "data/structures/"),
)
LAYERS = ("residents", "households", "businesses", "structures")


def prose_list(names: list[str]) -> str:
    """`a`, `a and b`, `a, b and c` — so the paragraph above reads as English."""
    if not names:
        return "none of the four layers"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def layer_of(file_path: str) -> str:
    for layer, prefix in LAYER_PREFIXES:
        if file_path.startswith(prefix):
            return layer
    return "elsewhere"


def measure_ledger() -> dict:
    ledger = read_ledger(LEDGER)
    if not isinstance(ledger, dict) or not isinstance(ledger.get("units"), list):
        raise SystemExit("FAIL the closed ledger is missing — run "
                         "tools/measure_research_spend.py --ledger-build")
    units = ledger["units"]
    dispositions = Counter(u.get("disposition") for u in units)
    landed = Counter()
    dead = Counter()
    for unit in units:
        target = unit.get("target")
        if not isinstance(target, dict):
            continue
        layer = layer_of(str(target.get("file") or ""))
        landed[layer] += 1
        if not (ROOT / str(target.get("file") or "")).exists():
            dead[layer] += 1
    unresolved = [u for u in units if u.get("disposition") == "unresolved"]
    owners = Counter(u["ticket"] for u in unresolved if u.get("ticket"))
    # T-1423. The other legitimate shape of an unresolved unit: it waits on a DOCUMENT, not
    # on a band of this programme, so it names no ticket and states what would reopen it.
    awaiting = Counter(u["awaiting_evidence"] for u in unresolved if u.get("awaiting_evidence"))
    states = ticket_states(ROOT)
    return {
        "unit_count": ledger.get("unit_count", len(units)),
        "as_of": ledger.get("as_of"),
        "dispositions": {k: dispositions.get(k, 0) for k in sorted(dispositions)},
        "unclassified": sum(n for k, n in dispositions.items() if k not in
                            {"asserted", "later_only", "outside_chicago",
                             "aggregate_only", "refused", "unresolved"}),
        "landed": {layer: landed.get(layer, 0) for layer in LAYERS},
        "landed_elsewhere": landed.get("elsewhere", 0),
        "dead_targets": sum(dead.values()),
        "owners": [
            {"ticket": t, "units": n, "state": states.get(t, "missing"),
             "live": states.get(t, "missing") in OPEN_TICKET_STATES}
            for t, n in sorted(owners.items())
        ],
        "awaiting_evidence": [
            {"reopened_by": clause, "units": n}
            for clause, n in sorted(awaiting.items(), key=lambda kv: (-kv[1], kv[0]))
        ],
    }


def measure_residents() -> dict:
    index = read_json(RESIDENT_INDEX)
    counts = index.get("counts", {})
    households = index.get("households", [])
    grades = Counter()
    for row in households:
        for grade, n in (row.get("grades") or {}).items():
            grades[grade] += n
    return {
        "persons": counts.get("persons", 0),
        "households": counts.get("households", 0),
        "by_grade": {k: v for k, v in sorted((counts.get("by_grade") or {}).items())},
        "person_grades_from_households": {k: grades[k] for k in sorted(grades)},
        "letter_list_only": counts.get("letter_list_only", 0),
        "projected_residents": counts.get("projected_residents", 0),
        "merged_away": counts.get("merged_away", 0),
    }


def measure_households() -> dict:
    index = read_json(RESIDENT_INDEX)
    households = index.get("households", [])
    presence = Counter(str(r.get("present_on_scene_date")) for r in households)
    division = Counter(str(r.get("division")) for r in households)
    return {
        "records": len(households),
        "with_lives_at": sum(1 for r in households if r.get("lives_at")),
        "with_works_at": sum(1 for r in households if r.get("works_at")),
        "review_required": sum(1 for r in households if r.get("review_required")),
        "letter_list_only": sum(1 for r in households if r.get("letter_list_only")),
        "presence": {k: presence[k] for k in sorted(presence)},
        "division": {k: division[k] for k in sorted(division)},
    }


def measure_businesses() -> dict:
    register = read_json(REGISTER)
    businesses = register.get("businesses", [])
    present = [b for b in businesses if b.get("present_at_scene_date")]
    action = Counter(str(b.get("action")) for b in present)
    return {
        "records": len(businesses),
        "present_at_scene_date": len(present),
        "location_limit": {k: action[k] for k in sorted(action)},
        "with_proprietors": sum(1 for b in present if b.get("proprietors")),
        "with_partners": sum(1 for b in present if b.get("partners")),
        "with_street": sum(1 for b in present if b.get("street")),
        "survival_liberty_required": sum(1 for b in present if b.get("survival_liberty_required")),
        "backdating_liberty_required": sum(1 for b in present if b.get("backdating_liberty_required")),
    }


def measure_structures() -> dict:
    confidence = Counter()
    review = 0
    occupied = 0
    records = 0
    for path in sorted(STRUCTURES.glob("*.json")):
        doc = read_json(path)
        records += 1
        if doc.get("review_required"):
            review += 1
        if doc.get("occupants"):
            occupied += 1
        for phase in doc.get("phases", []):
            for value in phase.values():
                if isinstance(value, dict) and "confidence" in value:
                    confidence[str(value["confidence"])] += 1
    return {
        "records": records,
        "graded_attributes": {k: confidence[k] for k in sorted(confidence)},
        "review_required": review,
        "with_occupants": occupied,
    }


def measure() -> dict:
    return {
        "ledger": measure_ledger(),
        "residents": measure_residents(),
        "households": measure_households(),
        "businesses": measure_businesses(),
        "structures": measure_structures(),
    }


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    align = ["---"] + ["---:"] * (len(header) - 1)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    out.extend("| " + " | ".join(r) + " |" for r in rows)
    return out


def n(value) -> str:
    return f"{value:,}"


def render(model: dict) -> str:
    led = model["ledger"]
    res = model["residents"]
    hh = model["households"]
    biz = model["businesses"]
    st = model["structures"]
    out: list[str] = []
    out.append(f"# Closing research audit — {AS_OF}")
    out.append("")
    out.append("Generated by `tools/report_research_closing_audit.py --build`; `--check` re-derives it. "
               "The closed unit ledger (`docs/RESEARCH/research-spend-ledger-2026-09-15.md`) accounts for "
               "research from the source side. This reads the same ledger onto the four town layers and "
               "then reads the layers themselves, so that a gap shows as a gap. It signs nothing off: "
               "T-1157 is the signature and this is its evidence section.")
    out.append("")

    out.append("## 1. The ledger, and where it lands")
    out.append("")
    out.append(f"Registered reading units: **{n(led['unit_count'])}**, as of {led['as_of']}. "
               f"Unclassified: **{n(led['unclassified'])}**. "
               f"Asserted targets whose file no longer exists: **{n(led['dead_targets'])}**.")
    out.append("")
    out.extend(table(["Disposition", "Units"],
                     [[k, n(v)] for k, v in led["dispositions"].items()]))
    out.append("")
    out.append("Every asserted unit names the record and field it wrote to. Grouped by the layer that "
               "file belongs to:")
    out.append("")
    out.extend(table(["Layer", "Asserted units landed"],
                     [[layer, n(led["landed"][layer])] for layer in LAYERS]
                     + [["outside the four layers", n(led["landed_elsewhere"])]]))
    out.append("")
    # READ FROM THE COUNTS, NOT ASSERTED BESIDE THEM. This paragraph used to state as a
    # fixed sentence that every asserted unit lands on a household record and nowhere
    # else. That was true when it was written, and T-1508 made it false in the same run
    # that added 485 business landings — with the table two lines above saying so. A
    # report that contradicts its own measurement is worse than one that omits it.
    reached = [layer for layer in LAYERS if led["landed"][layer]]
    unreached = [layer for layer in LAYERS if not led["landed"][layer]]
    said = ["**Read this honestly.** The unit-level ledger proves the second hop for "
            f"{prose_list(reached)}."]
    if unreached:
        said.append(f" It proves nothing at unit level for {prose_list(unreached)}, which is "
                    "not a claim that the layer is unresearched — the newspaper register "
                    "below is compiled from the same readings by `tools/compile_register.py`, "
                    "and the roofs carry their own graded attributes. Sections 4 and 5 read "
                    "those layers directly for that reason.")
    out.append("".join(said))
    out.append("")
    out.append("Reproduce: `python3 tools/measure_research_spend.py --ledger-build` then "
               "`python3 tools/report_research_closing_audit.py --check`.")
    out.append("")

    out.append("## 2. Layer: residents")
    out.append("")
    out.extend(table(["Measure", "Count"], [
        ["Persons", n(res["persons"])],
        ["Households", n(res["households"])],
        *[[f"Persons graded `{k}`", n(v)] for k, v in res["by_grade"].items()],
        ["Letter-list-only names", n(res["letter_list_only"])],
        ["Projected residents", n(res["projected_residents"])],
        ["Merged away", n(res["merged_away"])],
    ]))
    out.append("")
    out.append("Reproduce: `python3 -c \"import json;print(json.load(open('data/residents/index.json'))['counts'])\"`.")
    out.append("")

    out.append("## 3. Layer: households")
    out.append("")
    out.extend(table(["Measure", "Count"], [
        ["Household records", n(hh["records"])],
        ["With a `lives_at`", n(hh["with_lives_at"])],
        ["With a `works_at`", n(hh["with_works_at"])],
        ["Letter-list-only", n(hh["letter_list_only"])],
        ["Flagged `review_required`", n(hh["review_required"])],
    ]))
    out.append("")
    out.extend(table(["Presence on 1 July 1835", "Households"],
                     [[k, n(v)] for k, v in hh["presence"].items()]))
    out.append("")
    out.extend(table(["Division", "Households"],
                     [[k, n(v)] for k, v in hh["division"].items()]))
    out.append("")

    out.append("## 4. Layer: businesses")
    out.append("")
    out.append("The business layer today is the newspaper-derived register; T-1180 authors the record-per-firm "
               "layer that will stand beside it.")
    out.append("")
    out.extend(table(["Measure", "Count"], [
        ["Register records", n(biz["records"])],
        ["Present at the scene date", n(biz["present_at_scene_date"])],
        ["Naming a proprietor", n(biz["with_proprietors"])],
        ["Naming a partner", n(biz["with_partners"])],
        ["Naming a street", n(biz["with_street"])],
        ["Requiring a survival liberty", n(biz["survival_liberty_required"])],
        ["Requiring a backdating liberty", n(biz["backdating_liberty_required"])],
    ]))
    out.append("")
    out.append("The location limit of every firm present at the scene date — how far its evidence places it:")
    out.append("")
    out.extend(table(["Location limit", "Businesses"],
                     [[k, n(v)] for k, v in biz["location_limit"].items()]))
    out.append("")
    out.append("Reproduce: `python3 tools/compile_register.py --check`.")
    out.append("")

    out.append("## 5. Layer: structures")
    out.append("")
    out.extend(table(["Measure", "Count"], [
        ["Structure records", n(st["records"])],
        ["Carrying occupants", n(st["with_occupants"])],
        ["Flagged `review_required`", n(st["review_required"])],
    ]))
    out.append("")
    out.extend(table(["Graded phase attribute", "Values"],
                     [[f"`{k}`", n(v)] for k, v in st["graded_attributes"].items()]))
    out.append("")
    out.append("Reproduce: `python3 tools/audit_confidence.py --strict`.")
    out.append("")

    out.append("## 6. What is unresolved, and who owns it")
    out.append("")
    out.append("An unresolved unit is research that has been read and not yet spent. The ledger's standing "
               "invariant is that it may only defer to work that is still going to happen, so every owner "
               "below is checked against its ticket's current state.")
    out.append("")
    out.extend(table(["Owner", "Units", "State", "Live"],
                     [[o["ticket"], n(o["units"]), o["state"], "yes" if o["live"] else "**NO**"]
                      for o in led["owners"]]))
    out.append("")
    out.append("The rest defer to no ticket, and that is the second legitimate shape rather than a gap "
               "(T-1423): a name the research READ and the town WITHHELD, since re-admitted at the "
               "reconstructed tier, whose open question is whether the person was in the town on "
               "1 July 1835. No ticket can answer that — only a document can — so each states the "
               "document instead. The pointer that used to stand here was renamed four times as the "
               "ticket it named kept closing, and no source came any nearer.")
    out.append("")
    out.extend(table(["Units", "Reopened by"],
                     [[n(a["units"]), a["reopened_by"]] for a in led["awaiting_evidence"]]))
    out.append("")
    out.append("Reproduce: `python3 tools/measure_research_spend.py --check`.")
    out.append("")

    out.append("## 7. The gaps, stated")
    out.append("")
    unplaceable = biz["location_limit"].get("unplaceable", 0)
    street_only = biz["location_limit"].get("street_only", 0)
    # T-1508 CLOSED HALF OF THIS FINDING and the headline had to stop asserting the whole
    # of it: 485 units now reach the authored business layer. What is still true is the
    # structures half, so the sentence is derived from which layers are actually unreached
    # rather than fixed at the shape the finding had when it was first written.
    unreached = [layer for layer in ("businesses", "structures") if not led["landed"][layer]]
    if unreached:
        out.append(f"1. **No unit-level ledger entry reaches the "
                   f"{prose_list(unreached)} layer.** "
                   f"{n(led['landed']['residents'] + led['landed']['households'])} asserted units "
                   f"land on residents and households, {n(led['landed']['businesses'])} on "
                   f"businesses and {n(led['landed']['structures'])} on structures. Closing it "
                   f"means a seat on the ground (T-1198) for a claim to be asserted ONTO.")
    else:
        out.append(f"1. **Every layer is reached at unit level.** "
                   f"{n(led['landed']['residents'] + led['landed']['households'])} asserted units "
                   f"land on residents and households, {n(led['landed']['businesses'])} on "
                   f"businesses and {n(led['landed']['structures'])} on structures.")
    out.append(f"2. **{n(biz['present_at_scene_date'] - biz['with_proprietors'])} of the "
               f"{n(biz['present_at_scene_date'])} firms standing on 1 July 1835 name nobody who kept them.** "
               f"The paper advertised the goods and not the man. T-1182 audits this and T-1189 staffs it.")
    out.append(f"3. **{n(unplaceable)} firms are unplaceable and {n(street_only)} reach a street and no "
               f"further.** Those {n(unplaceable + street_only)} are the location limits the research "
               f"preserved rather than guessed past; T-1198 seats what can be seated and the rest stay "
               f"limits.")
    out.append(f"4. **{n(hh['records'] - hh['with_lives_at'])} of {n(hh['records'])} households have no "
               f"`lives_at`.** Most are letter-list-only names ({n(hh['letter_list_only'])}) whose whole "
               f"evidence is that a letter waited for them; where they live is T-1159's roster question, "
               f"not a hole in the reading.")
    out.append(f"5. **{n(st['graded_attributes'].get('reconstructed', 0))} structure attributes are "
               f"`reconstructed` against {n(st['graded_attributes'].get('attested', 0))} attested and "
               f"{n(st['graded_attributes'].get('inferred', 0))} inferred.** That is the honest shape of a "
               f"town of which the sources describe a few dozen buildings; the grade says so on every value.")
    out.append("")

    out.append("## 8. Closing")
    out.append("")
    out.append(f"Unclassified registered research units: **{n(led['unclassified'])}**. "
               f"Dead asserted targets: **{n(led['dead_targets'])}**. "
               f"Unresolved units deferred to work that is not live: "
               f"**{n(sum(o['units'] for o in led['owners'] if not o['live']))}**.")
    out.append("")
    out.append("The closed ledger is therefore complete in its own terms, and section 7 names the five "
               "places where the research stopped and the ticket that carries each one. This audit makes no "
               "GO/NO-GO judgement about reconstruction: that is T-1157's signature, and this is the "
               "evidence under it.")
    out.append("")
    return "\n".join(out)


def self_test() -> int:
    """Mutate the measurement and prove the rendered report changes with it."""
    base = measure()
    failures = []
    cases = [
        ("an unclassified unit appears", ("ledger", "unclassified"), 1),
        ("an asserted target dies", ("ledger", "dead_targets"), 3),
        ("a household loses its lives_at", ("households", "with_lives_at"), 0),
        ("a firm loses its proprietor", ("businesses", "with_proprietors"), 0),
        ("a structure record vanishes", ("structures", "records"), 1),
        ("the person count moves", ("residents", "persons"), 7),
    ]
    rendered = render(base)
    for label, (section, key), value in cases:
        mutated = json.loads(json.dumps(base))
        if mutated[section][key] == value:
            failures.append(f"{label}: the mutation is a no-op against live data")
            continue
        mutated[section][key] = value
        if render(mutated) == rendered:
            failures.append(f"{label}: the report did not move")
    # A dead owner must be visible as a dead owner.
    mutated = json.loads(json.dumps(base))
    if mutated["ledger"]["owners"]:
        mutated["ledger"]["owners"][0]["live"] = False
        if "**NO**" not in render(mutated):
            failures.append("a closed owner: the report did not mark it")
    else:
        failures.append("a closed owner: no owner row to mutate")
    for line in failures:
        print(f"  MISS {line}")
    print(f"CLOSING AUDIT SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), {len(cases) + 1} case(s)")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="write the closing audit")
    parser.add_argument("--check", action="store_true", help="re-derive and refuse a drifted report")
    parser.add_argument("--self-test", action="store_true", help="mutate the measurement in memory")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    text = render(measure())
    if args.check:
        if not REPORT.exists():
            print(f"FAIL {REPORT.relative_to(ROOT)} is missing — run "
                  f"tools/report_research_closing_audit.py --build")
            return 1
        if REPORT.read_text(encoding="utf-8") != text:
            print(f"FAIL {REPORT.relative_to(ROOT)} is stale — run "
                  f"tools/report_research_closing_audit.py --build")
            return 1
        if not args.quiet:
            print("OK: the closing research audit re-derives from the ledger and the four layers")
        return 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print(f"wrote {REPORT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
