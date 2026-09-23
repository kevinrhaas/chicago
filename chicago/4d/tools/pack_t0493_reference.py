#!/usr/bin/env python3
"""Write T-0493's durable reference package (CSV always, XLSX when openpyxl imports).

`chicago/reference/resident-research/README.md` is the contract: one folder per
cohort ticket, a machine-readable CSV, a human-reviewable workbook, and four
sheets — Residents, Candidates, Sources, Search_Log. This ticket's "cohort" is the
345 entries of the four voter lists, and its Residents sheet is one row per entry.

Everything here is a VIEW of the committed JSON. Nothing is decided in this file.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CIVIC = ROOT / "data" / "research" / "civic"
OUT = ROOT.parent / "reference" / "resident-research" / "T-0493"
TICKET = "T-0493"

HEADER = (ROOT.parent / "reference" / "resident-research" /
          "cohort_research_template.csv").read_text(encoding="utf-8").splitlines()[0].split(",")

LIST_TITLES = {
    "poll_1833": "Poll list of the first election of the Board of Trustees of the "
                 "Town of Chicago, 10 August 1833",
    "tax_1833": "Tax list of the Town of Chicago, 1833",
    "poll_1834": "Election returns — poll list of 1834, filed 11 August 1834",
    "poll_1835": "Poll list of 1835",
}


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    records = {r["id"]: r for r in load(CIVIC / "records" /
                                       "voter_lists_1833_1835.json")["records"]}
    cross = load(CIVIC / "voter_crosswalk.json")
    log = load(CIVIC / "search_log.json")
    by_record = {s["record_id"]: s for s in log["searches"]}
    OUT.mkdir(parents=True, exist_ok=True)

    residents = []
    for e in cross["entries"]:
        rec = records[e["record_id"]]
        sweep = by_record.get(e["record_id"])
        row = {k: "" for k in HEADER}
        row.update({
            "ticket": TICKET,
            "cohort": "voter_lists_1833_1835",
            "person_id": e["matched_resident"] or "",
            "household_id": e["household_id"] or "",
            "name_transcribed": e["as_read"],
            "name_normalized": e["normalized"],
            "stratum": e["list"],
            "seed_source_id": "chicago_voter_lists_1833_1835_irad",
            "seed_source_date": {"poll_1833": "1833-08-10", "tax_1833": "1833",
                                 "poll_1834": "1834-08-11",
                                 "poll_1835": "1835"}[e["list"]],
            "research_outcome": {"matched": "corroborated", "candidate": "candidate",
                                 "unmatched": "no_corroboration"}[e["outcome"]],
            "identity_confidence": ("high" if e["outcome"] == "matched"
                                    else "unresolved"),
            "candidate_ids": ", ".join(e["rivals"]) or (
                "bridge row %s" % e["candidate"]["row"] if e["candidate"] else ""),
            "proposed_civic_voter_census": "%s, entry %d" % (
                LIST_TITLES[e["list"]], rec["locator"]["entry"]),
            "evidence_for": e["discriminator"] or "",
            "evidence_against": "" if e["outcome"] == "matched" else e["rule"],
            "source_ids": "chicago_voter_lists_1833_1835_irad"
                          + (", andreas_1884_v1" if sweep and sweep["result"] == "hit"
                             else ""),
            "source_urls_locators": "%s line %d" % (e["list"], rec["locator"]["line"]),
            "source_tiers": "2",
            "queries": sweep["query"] if sweep else "",
            "access_dates": log["swept_on"] if sweep else "",
            "source_limitations": sweep["limitation"] if sweep else
                "Not swept: this entry already reaches a resident, and the sweep was "
                "run for the men on the 1835 poll who do not.",
            "recommended_data_action": (
                "no action here — T-0514 mints, T-0515 regrades"),
            "notes": ("second source in Andreas vol. 1: %s"
                      % sweep["hits"][0]["matched"]) if sweep and sweep["result"] == "hit"
                     else (sweep["result"] if sweep else ""),
        })
        residents.append(row)

    csv_path = OUT / "T-0493_resident_research.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER)
        w.writeheader()
        w.writerows(residents)

    candidates = [["record_id", "as_read", "why_it_is_only_a_candidate",
                   "rival_residents", "bridge_row", "bridge_preferred_name",
                   "bridge_tier"]]
    for e in cross["entries"]:
        if e["outcome"] != "candidate":
            continue
        c = e["candidate"] or {}
        candidates.append([e["record_id"], e["as_read"], e["rule"],
                           ", ".join(e["rivals"]), c.get("row", ""),
                           c.get("preferred_name", ""), c.get("tier", "")])

    sources = [["source_id", "tier", "verified", "what_it_supplies",
                "what_it_does_not_supply"]]
    for sid in ("chicago_voter_lists_1833_1835_irad",
                "chicago_genealogist_1993_voter_lists", "andreas_1884_v1"):
        doc = load(ROOT / "data" / "sources" / ("%s.json" % sid))
        sources.append([sid, doc.get("tier"), doc.get("verified"),
                        " | ".join(doc.get("what_it_supplies") or []),
                        " | ".join(doc.get("what_it_does_not_supply") or [])])

    search = [["record_id", "as_read", "source", "query", "searched_on", "result",
               "first_match", "limitation"]]
    for s in log["searches"]:
        search.append([s["record_id"], s["as_read"], s["source"], s["query"],
                       s["searched_on"], s["result"],
                       s["hits"][0]["matched"] if s["hits"] else "",
                       s["limitation"]])
    for p in log["probes"]:
        search.append(["", "(all 70 names)", p["source"], p["what_was_wanted"],
                       p["searched_on"], p["result"], "",
                       p.get("detail", "") or p.get("also_tried", "")])

    try:
        import openpyxl
    except ImportError:
        print("openpyxl is not importable — CSV written, workbook skipped")
        return 0
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Residents"
    ws.append(HEADER)
    for row in residents:
        ws.append([row[k] for k in HEADER])
    for title, table in (("Candidates", candidates), ("Sources", sources),
                         ("Search_Log", search)):
        sheet = wb.create_sheet(title)
        for row in table:
            sheet.append(row)
    wb.save(OUT / "T-0493_resident_research_working.xlsx")
    print("package written: %d resident rows, %d candidates, %d searches"
          % (len(residents), len(candidates) - 1, len(search) - 1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
