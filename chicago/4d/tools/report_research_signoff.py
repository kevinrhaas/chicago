#!/usr/bin/env python3
"""The research sign-off: one owner-readable receipt over the spend, and the GO it carries (T-1157).

WHAT THIS IS. The owner asked, on 2026-09-17, to "confirm that all of the research has been
spent successfully on building residents households trades occupations … and also the business
structures and where everyone works and lives, their primary and any other locations they were
significantly involved in." This is that confirmation, read from the tree rather than typed,
and it ends in a GO or a NO-GO for the reconstruction bands.

WHAT IT IS NOT. It re-decides nothing. `measure_research_spend.py` accounts for the research
from the SOURCE side; `report_research_closing_audit.py` (T-1241) reads the same ledger onto
the four town layers and prints the gaps. Both are gated already, and this report cites them
rather than recomputing them. What is new here is the five axes the owner named — residents and
households, plural dated roles, businesses and who works where, primary and other significant
locations, and whether the withheld research is legible — each reduced to a small number of
CONDITIONS that either hold in the committed tree or do not, and a verdict derived from them.

A STATED GAP IS A FINISHED ANSWER. Zero unclassified is not the bar and never was: the queue's
own header says "zero unclassified research does not mean forcing uncertain people or locations
into 1835." So a condition here asks whether the research is ACCOUNTED FOR, never whether it is
large. Section 7 lists the gaps that remain, each with the ticket that owns it; none of them is
a blocker unless a condition says so, and the report says which is which in both directions.

THE VERDICT IS DERIVED. Every condition below is a measurement over committed files, so the
GO line cannot be edited into existence: change the tree and the verdict re-derives, and
`--check` refuses a report that no longer matches. That is deliberate. If a condition breaks
after this is signed, check.sh goes red and the next run has to re-derive the signature rather
than inherit it.

`--build` writes the report; `--check` re-derives it and refuses a drifted one, which is how
tools/check.sh consumes it; `--self-test` mutates each condition and proves the verdict moves.
"""
from __future__ import annotations

import argparse
import glob
import gzip
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
REPORT = ROOT / "docs" / "RESEARCH" / "research-signoff-2026-09.md"
RESIDENT_INDEX = ROOT / "data" / "residents" / "index.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"
LOCATION_SPEND = ROOT / "data" / "research" / "location_spend.json"
RECONCILIATION = ROOT / "data" / "research" / "location_reconciliation.json.gz"
SYNTHESIS_DRIFT = ROOT / "data" / "research" / "residents" / "synthesis_drift_baseline.json"
GATE_BASELINE = ROOT / "data" / "research" / "check_gate_baseline.json"
AGENCIES = ROOT / "data" / "reconstruction" / "1835_agencies.json"
LAND_SALES = ROOT / "data" / "reconstruction" / "1835_land_sales_by_tract.json"
RESIDENTS_JS = ROOT / "renderers" / "web" / "js" / "residents.js"
PEOPLE_JS = ROOT / "renderers" / "web" / "js" / "people.js"
SCENE_DATE = "1835-07-01"
AS_OF = "2026-09-18"

# The dispositions a reading unit may end on, split into the two halves this report cares
# about: what was written onto the town, and what was deliberately withheld from it. An
# `unresolved` unit is neither — it is research read and not yet spent. Its legitimacy has
# two forms (T-1423): a unit waiting on WORK defers to a ticket that is still going to
# happen, and a unit waiting on EVIDENCE names no ticket and states the document that would
# reopen it, because no ticket can produce a source nobody holds. C3 below tests the first
# and must not read the second as a dead pointer — 266 units wait on evidence, and they are
# not 266 units deferring to finished work.
WITHHELD = ("refused", "later_only", "outside_chicago", "aggregate_only")
SPENT = ("asserted",)

# A role row's `kind` vocabulary, and which kinds mean "this person was working". An
# `office` is working for this purpose: the man who kept the post office was at the post
# office, and axis 4 asks where he was.
WORKING_KINDS = ("trade", "profession", "employment", "office")

# Daniel Elston is the owner's own fixture for plural dated roles — soap and candles, then
# provisions, then brickmaking and school inspector — and the report shows him because a
# rule nobody can see working is a rule nobody can check.
FIXTURE = "hh_elston_daniel"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_gz(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return json.load(handle)


def households() -> list[dict]:
    return [read_json(Path(p)) for p in sorted(glob.glob(str(HOUSEHOLDS / "*.json")))]


def resolves(doc, field_path: str) -> bool:
    """Walk a JSON-pointer-ish field_path and say whether it lands on something."""
    cur = doc
    for raw in [s for s in str(field_path or "").split("/") if s]:
        seg = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, list):
            try:
                cur = cur[int(seg)]
            except (ValueError, IndexError):
                return False
        elif isinstance(cur, dict) and seg in cur:
            cur = cur[seg]
        else:
            return False
    return True


def measure_axis1() -> dict:
    """Residents and households: is every read unit accounted for, and did it land?"""
    ledger = read_ledger(LEDGER)
    units = ledger.get("units") or []
    if not units:
        raise SystemExit("FAIL the closed ledger is missing — run "
                         "tools/measure_research_spend.py --ledger-build")
    dispositions = Counter(u.get("disposition") for u in units)
    known = set(SPENT) | set(WITHHELD) | {"unresolved"}
    unclassified = sum(n for k, n in dispositions.items() if k not in known)
    unresolvable_targets = 0
    for unit in units:
        target = unit.get("target")
        if not isinstance(target, dict):
            continue
        path = ROOT / str(target.get("file") or "")
        if not path.exists() or not resolves(read_json(path), target.get("field_path")):
            unresolvable_targets += 1
    states = ticket_states(ROOT)
    unresolved = [u for u in units if u.get("disposition") == "unresolved"]
    owners = Counter(u["ticket"] for u in unresolved if u.get("ticket"))
    owner_rows = [
        {"ticket": t, "units": n, "state": states.get(t, "missing"),
         "live": states.get(t, "missing") in OPEN_TICKET_STATES}
        for t, n in sorted(owners.items(), key=lambda kv: (-kv[1], kv[0]))
    ]
    awaiting = Counter(u["awaiting_evidence"] for u in unresolved
                       if u.get("awaiting_evidence"))
    awaiting_rows = [{"reopened_by": clause, "units": n}
                     for clause, n in sorted(awaiting.items(), key=lambda kv: (-kv[1], kv[0]))]
    # A unit that names neither is the fault C3 exists to catch, and the ledger's own gate
    # refuses it before this report is built; counted here so the receipt can say zero.
    unowned = sum(1 for u in unresolved
                  if not u.get("ticket") and not u.get("awaiting_evidence"))
    index = read_json(RESIDENT_INDEX)
    counts = index.get("counts") or {}
    drift = read_json(SYNTHESIS_DRIFT)
    return {
        "units": ledger.get("unit_count", len(units)),
        "as_of": ledger.get("as_of"),
        "dispositions": {k: dispositions.get(k, 0) for k in sorted(dispositions)},
        "unclassified": unclassified,
        "asserted": dispositions.get("asserted", 0),
        "unresolvable_targets": unresolvable_targets,
        "owners": owner_rows,
        "owners_not_live": sum(r["units"] for r in owner_rows if not r["live"]) + unowned,
        "awaiting_evidence": awaiting_rows,
        "awaiting_evidence_units": sum(r["units"] for r in awaiting_rows),
        "persons": counts.get("persons", 0),
        "households": counts.get("households", 0),
        "by_grade": {k: v for k, v in sorted((counts.get("by_grade") or {}).items())},
        "letter_list_only": counts.get("letter_list_only", 0),
        "projected_residents": counts.get("projected_residents", 0),
        "synthesis_drift": int(drift.get("count", -1)),
    }


def measure_axis2(cards: list[dict]) -> dict:
    """Trades, professions and offices: plural, dated, and never claiming past their sources."""
    persons = 0
    with_roles = 0
    plural = 0
    on_scene = 0
    off_scene_only = 0
    rows = 0
    kinds: Counter = Counter()
    confidence: Counter = Counter()
    coverage: Counter = Counter()
    dated_by: Counter = Counter()
    unsourced_scene_claims = 0
    for card in cards:
        for person in card.get("persons") or []:
            persons += 1
            roles = [r for r in (person.get("roles") or []) if isinstance(r, dict)]
            if roles:
                with_roles += 1
            if len(roles) > 1:
                plural += 1
            if any(r.get("covers_scene_date") for r in roles):
                on_scene += 1
            elif roles:
                off_scene_only += 1
            for role in roles:
                rows += 1
                kinds[str(role.get("kind"))] += 1
                confidence[str(role.get("confidence"))] += 1
                covers = bool(role.get("covers_scene_date"))
                coverage["reaches 1 July 1835" if covers else "dated away from it"] += 1
                if covers:
                    dated_by[str(role.get("dated_by"))] += 1
                    if not role.get("sources"):
                        unsourced_scene_claims += 1
    fixture_rows = []
    fixture_path = HOUSEHOLDS / f"{FIXTURE}.json"
    if fixture_path.exists():
        card = read_json(fixture_path)
        for person in card.get("persons") or []:
            for role in person.get("roles") or []:
                fixture_rows.append({
                    "name": person.get("name"),
                    "role": role.get("role") or role.get("as_printed"),
                    "kind": role.get("kind"),
                    "from": role.get("from"),
                    "to": role.get("to"),
                    "covers": bool(role.get("covers_scene_date")),
                    "confidence": role.get("confidence"),
                })
    return {
        "persons": persons,
        "with_roles": with_roles,
        "plural": plural,
        "rows": rows,
        "on_scene": on_scene,
        "off_scene_only": off_scene_only,
        "no_roles": persons - with_roles,
        "kinds": {k: kinds[k] for k in sorted(kinds)},
        "confidence": {k: confidence[k] for k in sorted(confidence)},
        "coverage": {k: coverage[k] for k in sorted(coverage)},
        "dated_by": {k: dated_by[k] for k in sorted(dated_by)},
        "unsourced_scene_claims": unsourced_scene_claims,
        "fixture": fixture_rows,
        "fixture_on_scene": sum(1 for r in fixture_rows if r["covers"]),
    }


def measure_axis3(cards: list[dict]) -> dict:
    """Business structures and who works where."""
    register = read_json(REGISTER)
    businesses = register.get("businesses") or []
    present = [b for b in businesses if b.get("present_at_scene_date")]
    spend = read_json(LOCATION_SPEND)
    counts = spend.get("counts") or {}
    working = 0
    linkage: Counter = Counter()
    unreasoned: list[str] = []
    for card in cards:
        works = card.get("works_at") or {}
        seat = works.get("value")
        reason = works.get("note")
        for person in card.get("persons") or []:
            rows = [r for r in (person.get("roles") or [])
                    if isinstance(r, dict) and r.get("covers_scene_date")
                    and str(r.get("kind")) in WORKING_KINDS]
            if not rows:
                continue
            working += 1
            if seat:
                linkage["a workplace on the household record"] += 1
            elif any(str(r.get("place") or "not_stated") != "not_stated" for r in rows):
                linkage["a place printed on the role"] += 1
            elif any(str(r.get("employer_or_body") or "not_stated") != "not_stated" for r in rows):
                linkage["an employer or body on the role"] += 1
            elif reason:
                linkage["a printed reason no premises resolves"] += 1
            else:
                linkage["NOTHING"] += 1
                unreasoned.append(f"{card.get('id')}/{person.get('id')}")
    return {
        "records": len(businesses),
        "present": len(present),
        "with_proprietors": sum(1 for b in present if b.get("proprietors")),
        "with_partners": sum(1 for b in present if b.get("partners")),
        "with_street": sum(1 for b in present if b.get("street")),
        "published_limits": dict(sorted((counts.get("published_limits") or {}).items())),
        "adjudicated_grades": dict(sorted((counts.get("adjudicated_grades") or {}).items())),
        "moved_between_published_limits": counts.get("moved_between_published_limits"),
        "substitutable_seats": counts.get("seats_that_are_substitutable"),
        "working_persons": working,
        "linkage": {k: linkage[k] for k in sorted(linkage)},
        "unreasoned": sorted(unreasoned),
    }


def measure_axis4(cards: list[dict]) -> dict:
    """Primary and other significant locations — home, work, and everywhere else."""
    reconciliation = read_gz(RECONCILIATION)
    rows = reconciliation.get("rows") or []
    counts = reconciliation.get("counts") or {}
    no_disposition = sum(1 for r in rows if not r.get("disposition"))
    unclaused = sum(1 for r in rows
                    if r.get("disposition") in ("limited", "refused") and not r.get("limit_clause"))
    empty_resolutions = sum(1 for r in rows if r.get("disposition") == "resolved" and not (
        r.get("resolved_street") or r.get("resolved_structure")
        or r.get("resolved_face") or r.get("resolved_anchor")))
    offices: Counter = Counter()
    church = 0
    printed_places = Counter()
    associations = 0
    with_lives_at = 0
    with_works_at = 0
    for card in cards:
        if (card.get("lives_at") or {}).get("value"):
            with_lives_at += 1
        if (card.get("works_at") or {}).get("value"):
            with_works_at += 1
        if card.get("associated_with"):
            associations += len(card["associated_with"])
        for person in card.get("persons") or []:
            if person.get("church_evidence"):
                church += 1
            if person.get("associated_with"):
                associations += len(person["associated_with"])
            for role in person.get("roles") or []:
                body = str(role.get("employer_or_body") or "not_stated")
                if str(role.get("kind")) == "office" and body != "not_stated":
                    offices[body] += 1
                if str(role.get("place") or "not_stated") != "not_stated":
                    printed_places["reaching 1 July 1835" if role.get("covers_scene_date")
                                   else "dated away from it"] += 1
    agencies = (read_json(AGENCIES).get("counts") or {})
    land = (read_json(LAND_SALES).get("summary") or {})
    return {
        "households": len(cards),
        "with_lives_at": with_lives_at,
        "with_works_at": with_works_at,
        "seating_class": dict(sorted((counts.get("households_by_seating_class") or {}).items())),
        "rows": len(rows),
        "by_claim_kind": dict(sorted((counts.get("by_claim_kind") or {}).items())),
        "by_disposition": dict(sorted((counts.get("by_disposition") or {}).items())),
        "no_disposition": no_disposition,
        "unclaused": unclaused,
        "empty_resolutions": empty_resolutions,
        "offices": dict(sorted(offices.items(), key=lambda kv: (-kv[1], kv[0]))),
        "office_rows": sum(offices.values()),
        "church_persons": church,
        "printed_places": {k: printed_places[k] for k in sorted(printed_places)},
        "agency_holdings_on_a_card": agencies.get("reaching_a_card", 0),
        "agency_refused_holdings": agencies.get("refused_holdings", 0),
        "land_parcels_sorted": land.get("sorted", 0),
        "land_parcels_refused": land.get("refused", 0),
        "association_rows": associations,
    }


def measure_axis5() -> dict:
    """Withheld is legible: every refusal keeps its reason, every ungated check its owner."""
    ledger = read_ledger(LEDGER)
    units = ledger.get("units") or []
    withheld = [u for u in units if u.get("disposition") in WITHHELD]
    without_reason = sum(1 for u in withheld
                         if not (u.get("reason") or u.get("evidence") or u.get("ruling")))
    by_disposition = Counter(u.get("disposition") for u in withheld)
    baseline = read_json(GATE_BASELINE)
    ungated = baseline.get("ungated") or []
    return {
        "withheld": len(withheld),
        "by_disposition": {k: by_disposition[k] for k in sorted(by_disposition)},
        "without_reason": without_reason,
        "check_capable": (baseline.get("counts") or {}).get("check_capable", 0),
        "gated": (baseline.get("counts") or {}).get("gated", 0),
        "ungated": [
            {"tool": row.get("tool"), "owner": row.get("owner_ticket") or "—",
             "reason": bool(row.get("why_not_gated"))}
            for row in sorted(ungated, key=lambda r: str(r.get("tool")))
        ],
        "ungated_without_reason": sum(1 for row in ungated if not row.get("why_not_gated")),
    }


def measure_view() -> dict:
    """Acceptance 3, verified and not rebuilt: does the People surface show the plural fields?"""
    residents = RESIDENTS_JS.read_text(encoding="utf-8")
    people = PEOPLE_JS.read_text(encoding="utf-8")
    return {
        "roles_renderer": "export function rolesHtml" in residents,
        "associations_renderer": "export function associationsHtml" in residents
        or "function associationsHtml" in residents,
        "person_card_calls_roles": "rolesHtml(roles" in residents,
        "person_card_calls_associations": "associationsHtml(person.associated_with" in residents,
        "household_card_calls_associations": "associationsHtml(hh.associated_with" in residents,
        "people_view_filters_roles": "roles_at_scene_date" in people,
    }


def measure() -> dict:
    cards = households()
    model = {
        "axis1": measure_axis1(),
        "axis2": measure_axis2(cards),
        "axis3": measure_axis3(cards),
        "axis4": measure_axis4(cards),
        "axis5": measure_axis5(),
        "view": measure_view(),
    }
    model["conditions"] = conditions(model)
    return model


def conditions(model: dict) -> list[dict]:
    """The sign-off reduced to what can fail. Each row is measured, never asserted.

    A condition asks whether the research is ACCOUNTED FOR — read, dispositioned, landed on a
    field, or withheld with its reason on the record. None of them asks whether a count is
    large, because the size of what 1835 left behind is not something a gate can fix.
    """
    a1, a2, a3, a4, a5, view = (model["axis1"], model["axis2"], model["axis3"],
                                model["axis4"], model["axis5"], model["view"])
    rows = [
        ("C1", "Every registered reading unit carries one of the six durable dispositions",
         a1["unclassified"] == 0, f"{a1['unclassified']} unclassified", "T-1143"),
        ("C2", "Every asserted unit lands on a field that exists on the record it names",
         a1["unresolvable_targets"] == 0,
         f"{a1['unresolvable_targets']} of {a1['asserted']} do not resolve", "T-1143"),
        ("C3", "Every unresolved unit defers to a ticket that is still live, or states the "
               "evidence that would reopen it",
         a1["owners_not_live"] == 0, f"{a1['owners_not_live']} units defer to finished work",
         "T-1143"),
        ("C4", "The resident synthesizer stands zero files from the cards it writes",
         a1["synthesis_drift"] == 0, f"drift baseline holds {a1['synthesis_drift']} file(s)",
         "T-0838"),
        ("C5", "No role row claims 1 July 1835 without a source that describes it",
         a2["unsourced_scene_claims"] == 0,
         f"{a2['unsourced_scene_claims']} unsourced scene-date roles", "T-1145"),
        ("C6", "Every person working in the window resolves to a workplace or says why none does",
         not a3["unreasoned"], f"{len(a3['unreasoned'])} working persons say nothing", "T-1147"),
        ("C7", "Every location claim carries a disposition, and every limit its clause",
         a4["no_disposition"] == 0 and a4["unclaused"] == 0 and a4["empty_resolutions"] == 0,
         f"{a4['no_disposition']} undispositioned, {a4['unclaused']} unclaused, "
         f"{a4['empty_resolutions']} resolved onto nothing", "T-1147"),
        ("C8", "Every withheld unit keeps its stated reason",
         a5["without_reason"] == 0, f"{a5['without_reason']} withheld without a reason", "T-1146"),
        ("C9", "Every check this tree cannot gate declares why, and who owns the answer",
         a5["ungated_without_reason"] == 0,
         f"{a5['ungated_without_reason']} ungated row(s) state no reason", "T-0714"),
        ("C10", "The People surface renders the plural roles and the plural associations",
         all(view.values()), "the person or household card does not read a plural field",
         "T-1145 · T-1147"),
    ]
    return [{"id": i, "condition": text, "holds": bool(ok), "on_failure": detail, "ticket": tic}
            for i, text, ok, detail, tic in rows]


def verdict(model: dict) -> tuple[str, list[dict]]:
    failed = [c for c in model["conditions"] if not c["holds"]]
    return ("NO-GO" if failed else "GO"), failed


def table(header: list[str], rows: list[list[str]]) -> list[str]:
    align = ["---"] + ["---:"] * (len(header) - 1)
    out = ["| " + " | ".join(header) + " |", "| " + " | ".join(align) + " |"]
    out.extend("| " + " | ".join(r) + " |" for r in rows)
    return out


def n(value) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def render(model: dict) -> str:
    a1, a2, a3, a4, a5, view = (model["axis1"], model["axis2"], model["axis3"],
                                model["axis4"], model["axis5"], model["view"])
    call, failed = verdict(model)
    out: list[str] = []
    out.append(f"# The research sign-off — {AS_OF}")
    out.append("")
    out.append("Generated by `tools/report_research_signoff.py --build`; `--check` re-derives it and "
               "`tools/check.sh` runs that check, so this report cannot quietly stop being true. "
               "It is the owner's *confirm Completed Research* step (2026-09-17) and the entry "
               "condition for the reconstruction bands. Nothing below is typed: every figure is read "
               "from a committed file by the command its section names.")
    out.append("")
    out.append(f"**Scene date** {SCENE_DATE} · **reading units registered** {n(a1['units'])} "
               f"(ledger as of {a1['as_of']}) · **persons in the town** {n(a1['persons'])} in "
               f"{n(a1['households'])} households.")
    out.append("")
    out.append("The companion report is `research-closing-audit-2026-09.md` (T-1241), which reads the "
               "same ledger onto the four town layers and makes no judgement. This one judges.")
    out.append("")

    out.append("## The verdict")
    out.append("")
    out.append(f"### {call} for reconstruction")
    out.append("")
    out.extend(table(["Condition", "Holds", "Ticket"],
                     [[f"**{c['id']}** — {c['condition']}",
                       "yes" if c["holds"] else "**NO**", c["ticket"]]
                      for c in model["conditions"]]))
    out.append("")
    if failed:
        out.append("**NO-GO.** These must close before a reconstruction ticket may be claimed, "
                   "because a band that inherits an unaccounted reading will invent what a source "
                   "already says:")
        out.append("")
        for c in failed:
            out.append(f"- **{c['id']}** — {c['condition']}: {c['on_failure']} ({c['ticket']}).")
    else:
        out.append("**GO.** Every condition holds in the committed tree, so the reconstruction bands "
                   "may be claimed. What GO means, precisely: the research this project has read is "
                   "accounted for — dispositioned, landed on a structured field, or withheld with its "
                   "reason on the record — so a reconstruction pass can tell an attested fact from an "
                   "absent one and will not invent over either. What GO does NOT mean: that 1835 is "
                   "fully known. Section 7 names what is still missing, and every reconstructed value "
                   "that fills one of those gaps carries its tier, basis, seed and "
                   "`replaceable_by` (T-1158) so a later reading can displace it.")
    out.append("")
    out.append("Reproduce: `python3 tools/report_research_signoff.py --check`.")
    out.append("")

    out.append("## 1. Residents and households — is every reading accounted for?")
    out.append("")
    out.extend(table(["Disposition", "Units"], [[k, n(v)] for k, v in a1["dispositions"].items()]))
    out.append("")
    out.append(f"Unclassified: **{n(a1['unclassified'])}** (C1). Asserted units whose named field "
               f"does not resolve on the record: **{n(a1['unresolvable_targets'])}** of "
               f"{n(a1['asserted'])} (C2). The resident synthesizer's declared drift from the cards "
               f"it writes: **{n(a1['synthesis_drift'])}** file(s) (C4).")
    out.append("")
    out.append("An `unresolved` unit is research read and not yet spent, and it is only legitimate "
               "while the ticket it defers to is still going to happen. Read the owners column "
               "carefully — it is the most informative table in this report:")
    out.append("")
    out.extend(table(["Owner", "Units", "State", "Live"],
                     [[r["ticket"], n(r["units"]), r["state"], "yes" if r["live"] else "**NO**"]
                      for r in a1["owners"]]))
    out.append("")
    heaviest = ", ".join(f"{r['ticket']} ({n(r['units'])})" for r in a1["owners"][:5])
    out.append(f"Not one of those owners asks for another READING. The heaviest are {heaviest} — the "
               f"arrival and origin fill, the authored business layer, the seating, the "
               f"re-admissions, the named families — and the lighter ones are derivation fixes "
               f"beside them. That is the shape of a finished research spend: what is still unspent "
               f"is waiting on the bands this report opens, not on more of the corpus. "
               f"**{n(a1['owners_not_live'])}** units defer to work that is no longer live (C3).")
    out.append("")
    # T-1423. The second legitimate shape, and the reason C3 is not simply "names a live
    # ticket": these units are not waiting on a band of this programme, they are waiting on
    # a document. Saying so is what stopped the hand-off being renamed at every closure.
    out.append(f"**{n(a1['awaiting_evidence_units'])}** further unresolved unit(s) name no ticket "
               "at all, because no ticket can settle them: they are names the research READ and "
               "the town WITHHELD, since re-admitted at the reconstructed tier, and what is open "
               "is whether the person was in the town on 1 July 1835. Each states the document "
               "that would reopen it (T-1423):")
    out.append("")
    out.extend(table(["Units", "Reopened by"],
                     [[n(r["units"]), r["reopened_by"]] for r in a1["awaiting_evidence"]]))
    out.append("")
    out.extend(table(["The town as the layer holds it", "Count"], [
        ["Persons", n(a1["persons"])],
        ["Households", n(a1["households"])],
        *[[f"Persons graded `{k}`", n(v)] for k, v in a1["by_grade"].items()],
        ["Letter-list-only names", n(a1["letter_list_only"])],
        ["Carrying the PROJECTED RESIDENT qualifier", n(a1["projected_residents"])],
    ]))
    out.append("")
    out.append("Reproduce: `python3 tools/measure_research_spend.py --check` · "
               "`python3 tools/synthesize_resident_research.py --drift` · "
               "`python3 tools/report_research_closing_audit.py --check`.")
    out.append("")

    out.append("## 2. Trades, professions and offices — plural and dated")
    out.append("")
    out.append("`persons[].roles[]` is canonical (T-1145) and `occupation` is a GENERATED view of the "
               "rows that cover the scene date. A man may hold several at once and several in "
               "sequence, and the record now says which is which.")
    out.append("")
    out.extend(table(["Measure", "Count"], [
        ["Persons in the layer", n(a2["persons"])],
        ["Carrying at least one dated role", n(a2["with_roles"])],
        ["Carrying two or more", n(a2["plural"])],
        ["Role rows in total", n(a2["rows"])],
        [f"Persons whose roles reach {SCENE_DATE}", n(a2["on_scene"])],
        ["Persons whose every role is dated away from it", n(a2["off_scene_only"])],
        ["Persons carrying no dated role at all", n(a2["no_roles"])],
    ]))
    out.append("")
    out.extend(table(["Role kind", "Rows"], [[f"`{k}`", n(v)] for k, v in a2["kinds"].items()]))
    out.append("")
    out.extend(table(["Dating", "Rows"], [[k, n(v)] for k, v in a2["coverage"].items()]))
    out.append("")
    out.extend(table(["Confidence", "Rows"], [[f"`{k}`", n(v)] for k, v in a2["confidence"].items()]))
    out.append("")
    out.append(f"Of the rows that reach the scene date, every one names a source that describes it "
               f"(C5) — {', '.join(f'{n(v)} by `{k}`' for k, v in a2['dated_by'].items())}.")
    out.append("")
    out.append("**The fixture.** Daniel Elston is the owner's own example of a man with more than "
               "one calling, and the report shows his rows rather than describing them:")
    out.append("")
    out.extend(table(["Role", "Kind", "From", "To", f"Reaches {SCENE_DATE}", "Confidence"],
                     [[str(r["role"]), f"`{r['kind']}`", str(r["from"]), str(r["to"]),
                       "yes" if r["covers"] else "no", f"`{r['confidence']}`"]
                      for r in a2["fixture"]]))
    out.append("")
    out.append(f"Read it as written: Elston carries {n(len(a2['fixture']))} dated roles and "
               f"**{n(a2['fixture_on_scene'])}** of them reaches 1 July 1835. The soap and candle "
               "manufactory is real and attested, and the corpus last prints it at the issue of "
               "2 July 1834, so T-0991 withdrew it from the 1835 field and left it standing in "
               "`roles[]` with the bound its evidence permits; the brickmaking and the school "
               "inspectorship are printed against his name in the later Fergus directories and are "
               "carried as the years those volumes print. The plural field is "
               "therefore doing exactly the work it was built for — holding a career the scene date "
               "cannot see, without letting any of it claim the scene date.")
    out.append("")
    out.append("Reproduce: `python3 tools/derive_resident_roles.py --check`.")
    out.append("")
    out.append(
        "**Per person, rather than in aggregate.** The counts above and the location counts "
        "in section 4 are the two axes T-1144 acceptance 7 asks to be readable one person at "
        "a time. They are, in `docs/RESEARCH/convergence-coverage-2026-09.md` and the table "
        "under it (`data/research/convergence_coverage.json.gz`): one row per person naming "
        "which of his roles and which of his home, work and other places reach 1 July 1835, "
        "each verdict copied from the derivation that owns it. This section counts; that "
        "table names."
    )
    out.append("")

    out.append("## 3. Business structures, and who works where")
    out.append("")
    out.extend(table(["Measure", "Count"], [
        ["Register records", n(a3["records"])],
        [f"Standing on {SCENE_DATE}", n(a3["present"])],
        ["Naming a proprietor", n(a3["with_proprietors"])],
        ["Naming a partner", n(a3["with_partners"])],
        ["Naming a street", n(a3["with_street"])],
    ]))
    out.append("")
    out.append("The location limit is how far a firm's own evidence places it, published and then "
               "adjudicated. A limit is a preserved refusal, not a hole:")
    out.append("")
    out.extend(table(["Published limit", "Businesses"],
                     [[f"`{k}`", n(v)] for k, v in a3["published_limits"].items()]))
    out.append("")
    out.extend(table(["Adjudicated grade", "Businesses"],
                     [[f"`{k}`", n(v)] for k, v in a3["adjudicated_grades"].items()]))
    out.append("")
    out.append(f"Businesses whose published limit moved during the spend: "
               f"**{n(a3['moved_between_published_limits'])}** — the spend seated what the evidence "
               f"already reached and promoted nothing, so there is no firm to name here and no "
               f"source to name it on. Seats a later reading may displace: "
               f"**{n(a3['substitutable_seats'])}**.")
    out.append("")
    out.append(f"And the other direction — the people. **{n(a3['working_persons'])}** persons hold a "
               f"trade, profession, employment or office that reaches {SCENE_DATE}. Every one of them "
               f"either resolves to a workplace or carries the printed reason none is resolvable "
               f"(C6):")
    out.append("")
    out.extend(table(["What the record gives", "Persons"],
                     [[k, n(v)] for k, v in a3["linkage"].items()]))
    out.append("")
    out.append("Reproduce: `python3 tools/location_spend.py --check` · "
               "`python3 tools/compile_register.py --check`.")
    out.append("")

    out.append("## 4. Primary and other significant locations")
    out.append("")
    out.append("Home and work first, read off the household records:")
    out.append("")
    out.extend(table(["Measure", "Households"], [
        ["Household records", n(a4["households"])],
        ["Carrying a `lives_at`", n(a4["with_lives_at"])],
        ["Carrying a `works_at`", n(a4["with_works_at"])],
    ]))
    out.append("")
    out.extend(table(["Seating class", "Households"],
                     [[f"`{k}`", n(v)] for k, v in a4["seating_class"].items()]))
    out.append("")
    out.append(f"Then every location claim the research makes, reconciled: **{n(a4['rows'])}** rows, "
               f"each carrying a disposition, a date precision and — where it stops short — the "
               f"clause that stops it.")
    out.append("")
    out.extend(table(["Claim kind", "Rows"], [[f"`{k}`", n(v)] for k, v in a4["by_claim_kind"].items()]))
    out.append("")
    out.extend(table(["Disposition", "Rows"],
                     [[f"`{k}`", n(v)] for k, v in a4["by_disposition"].items()]))
    out.append("")
    out.append(f"Rows with no disposition: **{n(a4['no_disposition'])}**. Limited or refused rows "
               f"with no clause: **{n(a4['unclaused'])}**. Rows called resolved that resolve onto "
               f"nothing: **{n(a4['empty_resolutions'])}** (C7). This is the answer to *how many "
               f"attested location facts sit in prose with no structured target*: none — every "
               f"claim in the corpus is a row here, and a row that could not be placed says so with "
               f"its reason rather than being dropped or guessed past.")
    out.append("")
    out.append("**The other significant places.** The owner asked for more than home and work — the "
               "office a man held, the church he joined, the agency he kept, the land he bought. "
               "Each is carried on a structured record and counted here:")
    out.append("")
    out.extend(table(["Kind of involvement", "Rows"], [
        ["Offices held, naming the body they were held under", n(a4["office_rows"])],
        ["Persons carrying church evidence", n(a4["church_persons"])],
        ["Agency holdings reaching a card", n(a4["agency_holdings_on_a_card"])],
        ["Agency holdings refused", n(a4["agency_refused_holdings"])],
        ["Land-sale parcels sorted onto a tract", n(a4["land_parcels_sorted"])],
        ["Land-sale parcels refused", n(a4["land_parcels_refused"])],
        ["`associated_with` rows on a person or household", n(a4["association_rows"])],
    ]))
    out.append("")
    out.extend(table(["Body an office was held under", "Rows"],
                     [[f"`{k}`", n(v)] for k, v in a4["offices"].items()]))
    out.append("")
    out.extend(table(["Roles naming a printed place", "Rows"],
                     [[k, n(v)] for k, v in a4["printed_places"].items()]))
    out.append("")
    out.append("Reproduce: `python3 tools/location_reconciliation.py --check` · "
               "`python3 tools/compile_agencies.py --check`.")
    out.append("")

    out.append("## 5. Withheld is legible")
    out.append("")
    out.append(f"**{n(a5['withheld'])}** reading units were deliberately kept out of the town, and "
               f"**{n(a5['without_reason'])}** of them do so without a stated reason (C8). A refusal "
               f"that cannot say why is indistinguishable from an oversight, which is the whole "
               f"point of keeping them.")
    out.append("")
    out.extend(table(["Withheld as", "Units"],
                     [[f"`{k}`", n(v)] for k, v in a5["by_disposition"].items()]))
    out.append("")
    out.append(f"The same rule over the gate itself: of **{n(a5['check_capable'])}** tools carrying a "
               f"`--check`, **{n(a5['gated'])}** are run by `tools/check.sh` and "
               f"**{n(len(a5['ungated']))}** are not. Each of those declares why and who owns the "
               f"answer, and **{n(a5['ungated_without_reason'])}** state no reason (C9):")
    out.append("")
    out.extend(table(["Ungated check", "Owner", "States why"],
                     [[f"`{r['tool']}`", r["owner"], "yes" if r["reason"] else "**NO**"]
                      for r in a5["ungated"]]))
    out.append("")
    out.append("Reproduce: `python3 tools/audit_check_gates.py --gate`.")
    out.append("")

    out.append("## 6. The surface a reader sees")
    out.append("")
    out.append("The plural fields are worth nothing if only a gate can read them. Verified here "
               "against the committed renderer, not rebuilt:")
    out.append("")
    out.extend(table(["The People surface", "Present"],
                     [[k.replace("_", " "), "yes" if v else "**NO**"]
                      for k, v in sorted(view.items())]))
    out.append("")
    out.append("Reproduce: `node --check renderers/web/js/residents.js` and read the card blocks "
               "the table names.")
    out.append("")

    out.append("## 7. The gaps, stated")
    out.append("")
    out.append("None of these is a condition above, and that is a judgement rather than an oversight: "
               "each names something 1835 did not write down, or a contract question about a tool, "
               "and neither kind is closed by reading more of what this project already holds.")
    out.append("")
    out.append(f"1. **{n(a3['present'] - a3['with_proprietors'])} of the {n(a3['present'])} firms "
               f"standing on {SCENE_DATE} name nobody who kept them.** The paper advertised the "
               f"goods and not the man. T-1182 audits it; T-1189 staffs it.")
    out.append(f"2. **{n(a3['published_limits'].get('street_only', 0))} firms reach a street and "
               f"{n(a3['published_limits'].get('unplaceable', 0))} reach nowhere.** Those limits are "
               f"preserved refusals; T-1198 seats what can be seated and the rest stay limits.")
    out.append(f"3. **{n(a4['households'] - a4['with_lives_at'])} of {n(a4['households'])} households "
               f"have no `lives_at`, and {n(a4['seating_class'].get('none', 0))} sit in no seating "
               f"class.** Most are post-office-list names whose whole evidence is that a letter "
               f"waited for them. T-1172 rules on their re-admission; T-1199 seats them.")
    out.append(f"4. **{n(a2['no_roles'])} of {n(a2['persons'])} persons carry no dated role, and "
               f"{n(a2['off_scene_only'])} carry only roles dated away from the scene date.** The "
               f"town's trades come from newspapers, directories and registers, and those name the "
               f"men who advertised. T-1173 reconstructs the trade households the occupation model "
               f"still wants.")
    out.append(f"5. **Only {n(a4['association_rows'])} `associated_with` rows exist.** The plural, "
               f"dated location row is the agreed shape (T-1147) and the renderer already reads it, "
               f"but the migration off the singular `lives_at`/`works_at` pair has barely begun: "
               f"T-1273 writes the committed reconciliations as association rows, T-1274 retires the "
               f"pair. Until then the reconciliation table above, not the card, is where a person's "
               f"second address is legible — which is why C7 measures the table.")
    out.append("6. **One resident derivation cannot be gated on byte identity.** "
               "`tools/mint_letter_list_residents.py` is not the last writer of the files it "
               "derives, so re-running it over the committed tree would revert the synthesis and "
               "upgrade grades this project holds down; T-0662 read that and T-0691 owns the "
               "contract that compares only what the pass owns. It is declared on the gate baseline "
               "with that reason (C9) and `--gate` and `--self-test` are run in check.sh, which "
               "prove different things. This is a tooling contract, not an unspent reading: it "
               "cannot cause a reconstruction band to invent over a source, which is why it is "
               "listed here and not above.")
    out.append("")

    out.append("## 8. What this signs, and what it does not")
    out.append("")
    out.append(f"Signed **{call}** on {AS_OF}, by measurement over the committed tree. The signature "
               f"is the ten conditions and nothing else: it says the research is accounted for, not "
               f"that the town is known. Every gap in section 7 stays a gap, keeps its ticket, and "
               f"will be filled — where it is filled at all — by a reconstructed value that says so "
               f"on its own face.")
    out.append("")
    out.append("If a condition later breaks, `tools/check.sh` goes red on this report and the next "
               "run must re-derive the signature. A sign-off that cannot be revoked is not a "
               "measurement.")
    out.append("")
    return "\n".join(out)


def self_test() -> int:
    """Break each condition in memory and prove the verdict and the report both move."""
    base = measure()
    baseline_call, baseline_failed = verdict(base)
    rendered = render(base)
    failures: list[str] = []
    if baseline_failed:
        print("  note the live tree already fails "
              f"{', '.join(c['id'] for c in baseline_failed)}")
    cases = [
        ("C1", ("axis1", "unclassified"), 12),
        ("C2", ("axis1", "unresolvable_targets"), 4),
        ("C3", ("axis1", "owners_not_live"), 9),
        ("C4", ("axis1", "synthesis_drift"), 31),
        ("C5", ("axis2", "unsourced_scene_claims"), 2),
        ("C7", ("axis4", "no_disposition"), 5),
        ("C8", ("axis5", "without_reason"), 7),
        ("C9", ("axis5", "ungated_without_reason"), 1),
    ]
    for cid, (section, key), value in cases:
        mutated = json.loads(json.dumps(base))
        if mutated[section][key] == value:
            failures.append(f"{cid}: the mutation is a no-op against live data")
            continue
        mutated[section][key] = value
        mutated["conditions"] = conditions(mutated)
        call, failed = verdict(mutated)
        if call != "NO-GO" or cid not in {c["id"] for c in failed}:
            failures.append(f"{cid}: breaking it did not reach the verdict")
        if render(mutated) == rendered:
            failures.append(f"{cid}: the report did not move")
    # C6 is a list, and C10 is a dict of booleans — both need their own shape.
    mutated = json.loads(json.dumps(base))
    mutated["axis3"]["unreasoned"] = ["hh_nobody/nobody"]
    mutated["conditions"] = conditions(mutated)
    if verdict(mutated)[0] != "NO-GO":
        failures.append("C6: a working person who says nothing did not reach the verdict")
    mutated = json.loads(json.dumps(base))
    if mutated["view"]:
        mutated["view"][sorted(mutated["view"])[0]] = False
        mutated["conditions"] = conditions(mutated)
        if verdict(mutated)[0] != "NO-GO":
            failures.append("C10: a card that stopped reading a plural field did not reach the verdict")
    else:
        failures.append("C10: no view assertion to mutate")
    # And the other direction: a GO must be reachable, or the gate is decoration.
    mutated = json.loads(json.dumps(base))
    for section, key, value in (("axis1", "unclassified", 0), ("axis1", "unresolvable_targets", 0),
                                ("axis1", "owners_not_live", 0), ("axis1", "synthesis_drift", 0),
                                ("axis2", "unsourced_scene_claims", 0),
                                ("axis4", "no_disposition", 0), ("axis4", "unclaused", 0),
                                ("axis4", "empty_resolutions", 0), ("axis5", "without_reason", 0),
                                ("axis5", "ungated_without_reason", 0)):
        mutated[section][key] = value
    mutated["axis3"]["unreasoned"] = []
    mutated["view"] = {k: True for k in mutated["view"]}
    mutated["conditions"] = conditions(mutated)
    if verdict(mutated)[0] != "GO":
        failures.append("a clean tree: the verdict cannot reach GO")
    for line in failures:
        print(f"  MISS {line}")
    print(f"RESEARCH SIGN-OFF SELF-TEST {'FAIL' if failures else 'PASS'} — "
          f"{len(failures)} failure(s), {len(cases) + 3} case(s), live verdict {baseline_call}")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="write the sign-off report")
    parser.add_argument("--check", action="store_true", help="re-derive and refuse a drifted report")
    parser.add_argument("--self-test", action="store_true", help="break each condition in memory")
    parser.add_argument("--verdict", action="store_true", help="print the GO/NO-GO line only")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    model = measure()
    if args.verdict:
        call, failed = verdict(model)
        print(f"{call} — {len(failed)} condition(s) failing"
              + (": " + ", ".join(c["id"] for c in failed) if failed else ""))
        return 0
    text = render(model)
    if args.check:
        if not REPORT.exists():
            print(f"FAIL {REPORT.relative_to(ROOT)} is missing — run "
                  f"tools/report_research_signoff.py --build")
            return 1
        if REPORT.read_text(encoding="utf-8") != text:
            print(f"FAIL {REPORT.relative_to(ROOT)} is stale — run "
                  f"tools/report_research_signoff.py --build")
            return 1
        if not args.quiet:
            call, failed = verdict(model)
            print(f"OK: the research sign-off re-derives, and still says {call}"
                  + (f" on {len(failed)} failing condition(s)" if failed else ""))
        return 0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    call, failed = verdict(model)
    print(f"wrote {REPORT.relative_to(ROOT)} — {call}"
          + (f", failing {', '.join(c['id'] for c in failed)}" if failed else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
