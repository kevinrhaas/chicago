#!/usr/bin/env python3
"""What the residents and households look like — every figure, re-derived on demand.

T-0517. The owner asked for "a summary of what the residents and households look
like"; `docs/RESEARCH/residents-households-summary-2026-09.md` is that summary, and
this tool is what makes it a MEASUREMENT rather than a snapshot. Every table in the
doc names the section of this tool that prints it, so a later run can re-run the
command and see whether the number still holds.

    python3 tools/summarize_residents.py            # every section
    python3 tools/summarize_residents.py grades     # one section
    python3 tools/summarize_residents.py --list     # the section names

It READS and never writes. The inputs are the committed layer itself —
`data/residents/index.json` and the household records it manifests,
`data/town_census.json`, `data/research/residents/identity_master.json` and the
gated audit table at `chicago/reference/resident-research/final/audit/`. Nothing
here judges: the one judgement in the programme, which category a source id
belongs to, is made once in `tools/export_resident_audit.py` and read back from
its CSV.
"""

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESIDENTS = ROOT / "data" / "residents"
AUDIT = (ROOT.parent / "reference" / "resident-research" / "final" / "audit"
         / "resident_audit_master.csv")

# The #668 baseline the ticket asks every delta to be measured against — the state
# of the layer after the 2026-09-02 synthesis, as printed in
# docs/RESEARCH/resident-household-synthesis-2026-09-02.md.
BASELINE_668 = {
    "households": 824, "persons": 848,
    "attested": 117, "inferred": 731, "reconstructed": 0,
    "projected_residents": 706,
}

CATEGORIES = ["newspaper", "civic", "census", "church", "book", "directory", "secondary"]


# --- the inputs -------------------------------------------------------------

def load_layer() -> tuple[dict, list[dict]]:
    index = json.loads((RESIDENTS / "index.json").read_text())
    records = [json.loads((RESIDENTS / e["file"]).read_text())
               for e in index["households"]]
    return index, records


def load_audit() -> list[dict]:
    if not AUDIT.exists():
        return []
    with AUDIT.open(newline="") as fh:
        return list(csv.DictReader(fh))


def persons(records: list[dict]):
    for h in records:
        for p in h["persons"]:
            yield h, p


# --- rendering --------------------------------------------------------------

def table(headers: list[str], rows: list[list], aligns: str = "") -> None:
    aligns = (aligns or "l" * len(headers)).ljust(len(headers), "l")
    widths = [len(h) for h in headers]
    body = [[("%s" % c) for c in row] for row in rows]
    for row in body:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def line(cells):
        out = []
        for i, cell in enumerate(cells):
            out.append(cell.rjust(widths[i]) if aligns[i] == "r"
                       else cell.ljust(widths[i]))
        return "| " + " | ".join(out) + " |"

    print(line(headers))
    print("|" + "|".join(("-" * (w + 2)) if aligns[i] == "l"
                         else ("-" * (w + 1)) + ":"
                         for i, w in enumerate(widths)) + "|")
    for row in body:
        print(line(row))


def truthy(cell: str) -> bool:
    """The audit CSV writes Python booleans; read them back without guessing case."""
    return (cell or "").strip().lower() == "true"


def pct(n: int, total: int) -> str:
    return "%.1f%%" % (100.0 * n / total) if total else "-"


def delta(now: int, was: int) -> str:
    return "%+d" % (now - was)


# --- the sections -----------------------------------------------------------

def s_overview(index, records, audit):
    """Households, persons and how far the layer has moved since PR #668."""
    n_hh, n_p = len(records), sum(len(h["persons"]) for h in records)
    grades = Counter(p["grade"] for _, p in persons(records))
    projected = sum(1 for _, p in persons(records)
                    if p.get("resident_subtype") == "projected_resident")
    rows = [
        ["households", n_hh, BASELINE_668["households"], delta(n_hh, BASELINE_668["households"])],
        ["person entries", n_p, BASELINE_668["persons"], delta(n_p, BASELINE_668["persons"])],
    ]
    for g in index["vocabulary"]["grades"]:
        rows.append([g, grades[g], BASELINE_668[g], delta(grades[g], BASELINE_668[g])])
    rows.append(["projected_resident", projected, BASELINE_668["projected_residents"],
                 delta(projected, BASELINE_668["projected_residents"])])
    table(["measure", "now", "#668 baseline", "change"], rows, "lrrr")
    print()
    print("index.json counts block agrees: %s"
          % ("yes" if index["counts"]["households"] == n_hh
             and index["counts"]["persons"] == n_p else "NO — the manifest has drifted"))


def s_grades(index, records, audit):
    """Persons by grade and subtype, and the ladder rung that graded them."""
    rows = []
    grades = Counter(p["grade"] for _, p in persons(records))
    total = sum(grades.values())
    for g in index["vocabulary"]["grades"]:
        sub = Counter(p.get("resident_subtype") or "(none)"
                      for _, p in persons(records) if p["grade"] == g)
        rows.append([g, grades[g], pct(grades[g], total),
                     ", ".join("%s %d" % (k, v) for k, v in sorted(sub.items())) or "-"])
    table(["grade", "persons", "share", "subtype"], rows, "lrrl")
    print()
    rungs = Counter((p.get("ladder_rule") or {}).get("rung") if isinstance(p.get("ladder_rule"), dict)
                    else p.get("ladder_rule") for _, p in persons(records))
    named = sum(v for k, v in rungs.items() if k)
    rows = [[k or "(no ladder_rule)", v, pct(v, total)]
            for k, v in sorted(rungs.items(), key=lambda kv: (kv[0] is None, kv[0] or ""))]
    table(["ladder rung", "persons", "share"], rows, "lrr")
    print()
    print("%d of %d persons carry a ladder rung; %d do not."
          % (named, total, total - named))


def s_division(index, records, audit):
    """Households by division, crossed with presence on the scene date."""
    presences = index["vocabulary"]["presence"]
    grid = defaultdict(Counter)
    for h in records:
        grid[h["division"]][(h["present_on_scene_date"] or {}).get("value")] += 1
    rows = []
    for d in index["vocabulary"]["divisions"]:
        row = grid[d]
        rows.append([d, sum(row.values())] + [row[v] for v in presences])
    rows.append(["TOTAL", len(records)]
                + [sum(grid[d][v] for d in grid) for v in presences])
    table(["division", "households"] + presences, rows, "l" + "r" * (1 + len(presences)))


def s_sex(index, records, audit):
    """Sex, where a source records it at all."""
    sexes = Counter(p.get("sex") for _, p in persons(records))
    total = sum(sexes.values())
    rows = [[k or "(not recorded)", v, pct(v, total)]
            for k, v in sorted(sexes.items(), key=lambda kv: (kv[0] is None, kv[0] or ""))]
    table(["sex", "persons", "share"], rows, "lrr")


def s_occupation(index, records, audit):
    """Who carries a trade, at what confidence, and the trades themselves."""
    total = sum(len(h["persons"]) for h in records)
    trades = Counter()
    conf = Counter()
    for _, p in persons(records):
        occ = p.get("occupation") or {}
        value = occ.get("value")
        if value and value != "none_recorded":
            trades[value] += 1
            conf[occ.get("confidence")] += 1
    carried = sum(trades.values())
    print("%d of %d persons carry a trade that is not `none_recorded` (%s); "
          "%d read `none_recorded`."
          % (carried, total, pct(carried, total), total - carried))
    print()
    table(["occupation confidence", "persons"],
          [[k or "(none)", v] for k, v in sorted(conf.items(), key=lambda kv: -kv[1])], "lr")
    print()
    table(["trade", "persons"],
          [[k, v] for k, v in sorted(trades.items(), key=lambda kv: (-kv[1], kv[0]))], "lr")
    print()
    print("%d distinct trades stand in the town." % len(trades))
    print()
    print("And WHICH RECORD says so — the category of every source id cited by an")
    print("occupation block, counted once per person per category:")
    print()
    table(["the trade is printed by", "persons"],
          [[k, v] for k, v in sorted(trade_sources(records).items(), key=lambda kv: -kv[1])],
          "lr")


def trade_sources(records: list[dict]) -> Counter:
    """Which KIND of record prints each trade the layer carries.

    The category table is the audit's one judgement and is not repeated here: this
    imports it, so a source id recategorised there moves this figure too.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from export_resident_audit import category_of

    cache: dict = {}
    counted = Counter()
    for _, p in persons(records):
        occ = p.get("occupation") or {}
        if not occ.get("value") or occ["value"] == "none_recorded":
            continue
        cats = {category_of(sid, cache) for sid in (occ.get("sources") or [])}
        if not cats:
            counted["(the occupation block cites nothing)"] += 1
        for c in cats:
            counted[c] += 1
    return counted


def s_sizes(index, records, audit):
    """The household size distribution, and what it is not."""
    sizes = Counter(len(h["persons"]) for h in records)
    total = len(records)
    rows = [[str(k), v, pct(v, total)] for k, v in sorted(sizes.items())]
    table(["persons in the household", "households", "share"], rows, "rrr")
    print()
    people = sum(k * v for k, v in sizes.items())
    print("mean household size %.2f (%d persons / %d households); "
          "%d households (%s) hold more than one person."
          % (people / total, people, total, total - sizes[1], pct(total - sizes[1], total)))
    print("The 1835 town census counts 3,265 people in 398 dwellings — 8.20 to a "
          "DWELLING — and T-0507 measured a mean HOUSEHOLD of 5.02 in 1840. "
          "A mean of %.2f here is a statement about the EVIDENCE, not about the town."
          % (people / total))


def s_evidence(index, records, audit):
    """Evidence per domain and the overlap, read back from the gated audit table."""
    if not audit:
        print("the audit table is not built — run tools/export_resident_audit.py --build")
        return
    total = len(audit)
    rows = []
    for c in CATEGORIES:
        n = sum(1 for r in audit if r["src_%s" % c])
        rows.append([c, n, pct(n, total)])
    table(["domain", "persons citing at least one", "share"], rows, "lrr")
    print()
    spread = Counter(int(r["categories_covered"]) for r in audit)
    table(["domains on the card", "persons", "share"],
          [[str(k), v, pct(v, total)] for k, v in sorted(spread.items())], "rrr")
    print()
    results = Counter(r["audit_result"] for r in audit)
    table(["what the person rests on", "persons", "share"],
          [[k, v, pct(v, total)] for k, v in sorted(results.items(), key=lambda kv: -kv[1])],
          "lrr")
    print()
    ll = sum(1 for r in audit if truthy(r["letter_list_only"]))
    linked = sum(1 for r in audit if r["later_census_serial"])
    print("letter-list-only %d (%s) · bridged to a named 1840 census row %d (%s)"
          % (ll, pct(ll, total), linked, pct(linked, total)))


def s_research(index, records, audit):
    """The research programme's own adjudication, per person."""
    total = sum(len(h["persons"]) for h in records)
    outcomes = Counter()
    tickets = set()
    asserted = 0
    for _, p in persons(records):
        rr = p.get("resident_research")
        if not rr:
            outcomes["(no research row)"] += 1
            continue
        outcomes[rr.get("outcome") or "(no outcome)"] += 1
        if rr.get("ticket"):
            tickets.add(rr["ticket"])
        if rr.get("asserted_identity"):
            asserted += 1
    table(["research outcome", "persons", "share"],
          [[k, v, pct(v, total)] for k, v in sorted(outcomes.items(), key=lambda kv: -kv[1])],
          "lrr")
    print()
    print("%d research tickets are cited on a card; %d persons carry an asserted identity."
          % (len(tickets), asserted))


def s_consolidation(index, records, audit):
    """The consolidated evidence the layer is drawn from, and what is unspent."""
    path = ROOT / "data" / "research" / "residents" / "identity_master.json"
    m = json.loads(path.read_text())
    c = m["counts"]
    rows = [[k.replace("_", " "), v] for k, v in c.items()]
    table(["identity_master", "count"], rows, "lr")
    print()
    on_card = c["identities_on_a_card"]
    print("%d of %d consolidated identities are on a household card; %d are not."
          % (on_card, c["identities"], c["identities"] - on_card))
    domains = Counter()
    for ident in m["identities"]:
        for d in ident.get("domains") or []:
            domains[d] += 1
    table(["domain", "identities appearing in it"],
          [[k, v] for k, v in sorted(domains.items(), key=lambda kv: -kv[1])], "lr")


def s_town(index, records, audit):
    """Where the people meet the buildings."""
    t = json.loads((ROOT / "data" / "town_census.json").read_text())
    p, b = t["people"], t["buildings"]
    table(["measure", "value"], [
        ["persons in a household whose lives_at resolves into the scene", p["housed"]],
        ["households so housed", p["households_housed"]],
        ["households without a dwelling", p["households_without_a_dwelling"]],
        ["roofs standing in the scene", b["standing"]],
        ["roofs the programme targets", b["target"]],
        ["the town census of November 1835 — people", p["town_total"]],
        ["the town census of November 1835 — dwellings", p["town_total_dwellings"]],
    ], "lr")
    print()
    lives = sum(1 for h in records if (h["lives_at"] or {}).get("value"))
    works = sum(1 for h in records if (h["works_at"] or {}).get("value"))
    print("%d of %d households name a lives_at; %d name a works_at."
          % (lives, len(records), works))


def s_gaps(index, records, audit):
    """What is unresearched, unresolved or explicitly refused."""
    total = sum(len(h["persons"]) for h in records)
    if audit:
        flags = [
            ("flag_no_research_row", "no research row has ever looked at them"),
            ("flag_candidate_identity_open", "a candidate identity is open and unasserted"),
            ("flag_conflicting_evidence", "the evidence on the card conflicts"),
            ("flag_single_source", "one source id and no second category to check it against"),
            ("flag_no_source", "no source id at all"),
            ("flag_unplaced", "no division"),
            ("flag_no_address", "neither a lives_at nor a works_at"),
        ]
        rows = []
        for key, what in flags:
            n = sum(1 for r in audit if truthy(r[key]))
            rows.append([key.replace("flag_", ""), n, pct(n, total), what])
        table(["unresolved", "persons", "share", "what it means"], rows, "lrrl")
        print()
    review = sum(1 for h in records if h.get("review_required"))
    removal = sum(1 for h in records if h.get("touches_removal"))
    no_sex = sum(1 for _, p in persons(records) if not p.get("sex"))
    print("%d households carry review_required, %d touches_removal." % (review, removal))
    print("%d of %d persons have no recorded sex — the largest single hole in the "
          "demography." % (no_sex, total))
    print("%d names sit in researched_not_resident: researched, and deliberately NOT "
          "in the town." % len(index.get("researched_not_resident") or []))


def s_tiers(index, records, audit):
    """Which tier every ATTRIBUTE stands on, not just every person."""
    sys.path.insert(0, str(ROOT / "tools"))
    from migrate_attribute_tiers import TIERS, tier_for, walk_blocks

    by_attr: dict = {}
    totals = Counter()
    bases = Counter()
    for h in records:
        for path, block in walk_blocks(h):
            tier = tier_for(block)
            if tier is None:
                continue
            totals[tier] += 1
            by_attr.setdefault(path, Counter())[tier] += 1
            if tier == "reconstructed":
                bases[(block.get("basis") or {}).get("id") or "(none)"] += 1
    n = sum(totals.values())
    table(["tier", "attributes", "share", "what it means"],
          [[t, totals[t], pct(totals[t], n), {
              "attested": "a source says it",
              "inferred": "reasoned from evidence about this person",
              "reconstructed": "supplied by this project, with a basis and a replacement rule",
              "unknown": "nothing is asserted — no source, and nothing invented",
          }[t]] for t in TIERS], "lrrl")
    print()
    table(["attribute"] + list(TIERS),
          [[a] + [by_attr[a][t] for t in TIERS] for a in sorted(by_attr)],
          "l" + "r" * len(TIERS))
    print()
    print("%d attribute claim(s) across %d household records. The layer's HONEST "
          "headline is the fourth column: %s of every attribute this dataset could "
          "carry is not recorded, and `unknown` is the tier that says so rather than "
          "letting it read as an invention."
          % (n, len(records), pct(totals["unknown"], n)))
    print()
    print("And the %d genuinely reconstructed value(s), by the basis each rests on:"
          % totals["reconstructed"])
    print()
    table(["basis", "values"], [[k, v] for k, v in sorted(bases.items())], "lr")


SECTIONS = [
    ("overview", s_overview),
    ("grades", s_grades),
    ("tiers", s_tiers),
    ("division", s_division),
    ("sex", s_sex),
    ("occupation", s_occupation),
    ("sizes", s_sizes),
    ("evidence", s_evidence),
    ("research", s_research),
    ("consolidation", s_consolidation),
    ("town", s_town),
    ("gaps", s_gaps),
]


def main(argv: list[str]) -> int:
    wanted = [a for a in argv if not a.startswith("-")]
    if "--list" in argv:
        for name, fn in SECTIONS:
            print("%-14s %s" % (name, (fn.__doc__ or "").splitlines()[0]))
        return 0
    known = dict(SECTIONS)
    for name in wanted:
        if name not in known:
            print("unknown section %r — try --list" % name, file=sys.stderr)
            return 2
    index, records = load_layer()
    audit = load_audit()
    chosen = wanted or [name for name, _ in SECTIONS]
    for i, name in enumerate(chosen):
        if len(chosen) > 1:
            print(("\n" if i else "") + "## " + name)
            print()
        known[name](index, records, audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
