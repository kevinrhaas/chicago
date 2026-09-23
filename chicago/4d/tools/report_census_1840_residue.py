#!/usr/bin/env python3
"""The 1840 census residue, in one table, with every figure re-derived from the tree.

WHY THIS EXISTS (T-1290). The 1840 federal census had turned into a leaf-by-leaf
programme: eight open tickets, every one of them a single page or column — a footing
that reads 198 against a column of 193, a No. of Scholars figure lost to the gutter, a
two-stroke figure on four cells that closes `m_20_30` at 41 or `m_30_40` at 13. The
scene is 1 July 1835. The 1840 census is five years after it and nothing in it seats a
person, dates an arrival or names a trade in 1835 — it BRACKETS a household other
sources already put in the town. Eight tickets of single-leaf adjudication buy a
precision the reconstruction cannot spend.

So the census is closed for the purposes of the 1835 reconstruction, and what is
written down instead is the residue: what did not close, where it is, the readings that
compete for it, and why it was not settled. A stated gap is a finished answer.

WHAT IS AUTHORED AND WHAT IS DERIVED. The classification and the prose are authored, in
`data/research/census_1840/residue_1840.json`. Not one figure is. Every number in the
published table is resolved out of the committed page files at render time, so a leaf
re-read afterwards either moves this report or turns `--check` red. The failure mode
that closes is a decision paper that quietly stops describing the tree it was measured
on — which is not hypothetical here: T-0926 rested its argument on 15 of 29 figures
reading `inferred` against a residue of 15, and the tree carries 17 today.

The effect section is derived too. The claim "the residue moves no 1835 card" is put
to the tree as an intersection: the pages the residue stands on, against the pages the
1840 -> 1835 head spend actually cites on a person.

    python3 tools/report_census_1840_residue.py            # print the report
    python3 tools/report_census_1840_residue.py --write    # write the committed copy
    python3 tools/report_census_1840_residue.py --check    # committed copy still true?
    python3 tools/report_census_1840_residue.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data/research/census_1840/residue_1840.json"
PAGES = ROOT / "data/research/census_1840/pages"
SPEND = ROOT / "data/research/census_1840/head_spend_1835.json"
TICKETS = ROOT / "tickets"
REPORT = ROOT / "docs/RESEARCH/census-1840-residue-2026-09.md"

PAGE_ID = re.compile(r"[0-9A-Za-z]{4}-[0-9A-Za-z]{4}-[0-9A-Za-z]+")


class Unresolved(Exception):
    """A figure the spec asks for that the tree does not carry."""


# ---------------------------------------------------------------------------
# resolving a figure out of the tree
# ---------------------------------------------------------------------------

def load_page(name: str) -> dict:
    path = PAGES / name
    if not path.exists():
        raise Unresolved(f"no page file {name}")
    return json.loads(path.read_text(encoding="utf-8"))


def walk(doc, path: str):
    """`a.b[2].c` against a loaded page file. Raises rather than returning None."""
    cur = doc
    for part in path.split("."):
        m = re.fullmatch(r"([^\[\]]+)((?:\[\d+\])*)", part)
        if not m:
            raise Unresolved(f"bad path {path!r}")
        key, idx = m.group(1), m.group(2)
        if not isinstance(cur, dict) or key not in cur:
            raise Unresolved(f"{path!r} is not in the page file")
        cur = cur[key]
        for i in re.findall(r"\[(\d+)\]", idx):
            i = int(i)
            if not isinstance(cur, list) or i >= len(cur):
                raise Unresolved(f"{path!r} indexes past the end")
            cur = cur[i]
    return cur


def resolve(spec: dict, default_page: str | None):
    """One figure. Every branch here reads the tree; none of them takes a literal."""
    page = spec.get("page_file", default_page)

    if "pages_absent" in spec:
        return sum(1 for p in spec["pages_absent"] if not (PAGES / f"{p}.json").exists())

    if "absent" in spec:
        doc = load_page(page)
        return "absent" if spec["absent"] not in doc else "present"

    if "difference" in spec:
        doc = load_page(page)
        a, b = (walk(doc, p) for p in spec["difference"])
        return a - b

    if "count_where" in spec:
        doc = load_page(page)
        rows = walk(doc, spec["count_where"])
        if not isinstance(rows, list):
            raise Unresolved(f"{spec['count_where']!r} is not a list")
        return sum(1 for r in rows if r.get(spec["field"]) == spec["equals"])

    if "find" in spec:
        doc = load_page(page)
        rows = walk(doc, spec["find"])
        for r in rows:
            if r.get(spec["key"]) == spec["equals"]:
                if spec["field"] not in r:
                    raise Unresolved(f"{spec['equals']} carries no {spec['field']}")
                return r[spec["field"]]
        raise Unresolved(f"no row where {spec['key']} == {spec['equals']}")

    if "path" in spec:
        doc = load_page(page)
        value = walk(doc, spec["path"])
        if value is None:
            if "null_as" not in spec:
                raise Unresolved(f"{spec['path']!r} is null and the spec gives no reading")
            return spec["null_as"]
        return value

    raise Unresolved(f"no resolver in {spec!r}")


def figures(row: dict) -> dict:
    return {name: resolve(f, row.get("page_file"))
            for name, f in (row.get("figures") or {}).items()}


def fill(text: str, values: dict) -> str:
    def sub(m):
        key = m.group(1)
        if key not in values:
            raise Unresolved(f"{{{key}}} has no figure")
        return str(values[key])
    return re.sub(r"\{([a-z0-9_]+)\}", sub, text)


# ---------------------------------------------------------------------------
# the derived effect on 1835
# ---------------------------------------------------------------------------

def residue_pages(spec: dict) -> list[str]:
    """Every page the residue stands on, taken from the rows and not listed twice."""
    seen = []
    for cls in spec["classes"]:
        for row in cls["rows"]:
            for name in [row.get("page_file")] + [
                    f.get("page_file") for f in (row.get("figures") or {}).values()]:
                if name and name[:-5] not in seen:
                    seen.append(name[:-5])
    return seen


def spend_pages() -> list[str]:
    """Every page the 1840 -> 1835 head spend cites on a person it actually wrote."""
    doc = json.loads(SPEND.read_text(encoding="utf-8"))
    seen = []
    for person in doc["people"]:
        for sheet in person.get("sheets") or []:
            m = PAGE_ID.match(sheet)
            if m and m.group(0) not in seen:
                seen.append(m.group(0))
    return sorted(seen)


def spend_counts() -> dict:
    return json.loads(SPEND.read_text(encoding="utf-8"))["counts"]


def folded_state(spec: dict) -> list[tuple[str, str, str]]:
    """Each folded ticket as the tree holds it: id, state, what it is blocked on."""
    out = []
    for tid in spec["folded_tickets"]:
        matches = sorted(TICKETS.glob(f"{tid}-*.md"))
        if not matches:
            raise Unresolved(f"{tid} has no ticket file")
        head = matches[0].read_text(encoding="utf-8").split("---")[1]
        meta = dict(
            (k.strip(), v.strip())
            for k, _, v in (line.partition(":") for line in head.splitlines() if ":" in line))
        out.append((tid, meta.get("state", "?"), meta.get("blocked_on", "")))
    return out


# ---------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------

def lines(spec: dict) -> list[str]:
    out = [
        "# The 1840 census residue",
        "",
        "*Generated by `tools/report_census_1840_residue.py --write` from",
        "`data/research/census_1840/residue_1840.json` and the committed page files.*",
        "*Do not hand-edit: `--check` compares this file against a fresh derivation, and",
        "every figure below is read out of the tree rather than typed into the source.*",
        "",
        "**What this is.** The 1840 federal census is CLOSED for the purposes of the 1835",
        "reconstruction, and this is the residue it closed with: every reading that did not",
        "settle, the leaf it is on, the readings that compete for it, and why it stayed open.",
        "A stated gap is a finished answer; a leaf-by-leaf programme of single-column",
        "adjudications is not one, and eight tickets of it were what this replaced.",
        "",
        f"**No residue row may be refiled as a ticket.** {spec['no_new_tickets_rule']}",
        "",
        "## The residue",
        "",
        "| # | class | leaf | what is open | the readings that compete | why it was not settled |",
        "|---|---|---|---|---|---|",
    ]
    n = 0
    for cls in spec["classes"]:
        for row in cls["rows"]:
            n += 1
            values = figures(row)
            tickets = " · ".join(f"`{t}`" for t in row["tickets"])
            out.append(
                f"| {n} | {cls['title']} | **{row['leaf']}** | {row['what']}<br>{tickets} | "
                f"{fill(row['readings'], values)} | {fill(row['why_not_settled'], values)} |")

    out += [
        "",
        f"{n} rows, in {len(spec['classes'])} classes.",
        "",
        "## What the residue does to the 1835 town",
        "",
        "One sentence per class, and the first four of them are the same sentence for the",
        "same reason.",
        "",
    ]
    for cls in spec["classes"]:
        out += [f"**{cls['title']}** — {cls['effect_on_1835']}", ""]

    resid = residue_pages(spec)
    spend = spend_pages()
    overlap = [p for p in resid if p in spend]
    counts = spend_counts()
    out += [
        "### The same claim, put to the tree",
        "",
        "`head_spend_1835.json` is the record of what the 1840 census actually wrote onto an",
        "1835 card. Its carry rule is LATER EVIDENCE ONLY: an 1839 or 1840 appearance alone",
        "is never an 1835 resident, and 1840 household composition is never back-projected to",
        "the 1835-07-01 scene.",
        "",
        "| | |",
        "|---|---|",
        f"| heads adjudicated in the 1840 crosswalk | {counts['heads_adjudicated']} |",
        f"| rulings that reach a person at all | {counts['rulings_that_reach_a_person']} |",
        f"| 1835 grades the whole of the 1840 census changed | **{counts['grades_changed']}** |",
        f"| distinct leaves those rulings cite | {len(spend)} |",
        f"| leaves this residue stands on | {len(resid)} |",
        f"| leaves in both sets | **{len(overlap)}** |",
        "",
    ]
    if overlap:
        out += [
            "The leaves in both sets are "
            + ", ".join(f"`{p}`" for p in overlap)
            + ". Each is named here rather than argued away: a residue row on a leaf the",
            "1835 layer cites is the one place this closure could cost something, and a later",
            "ticket that is blocked by one of them should reopen the reading it needs.",
            "",
        ]
    else:
        out += [
            "**They do not intersect.** No leaf carrying a residue row is cited by any of the",
            f"{counts['people_written']} people the 1840 census wrote to, so the residue could be",
            "settled either way tomorrow without moving a card — and the grade count says the",
            "same thing from the other side: five years after the scene, the census moved none.",
            "",
        ]

    for caveat in spec.get("caveats", []):
        if caveat["page"] not in spend:
            raise Unresolved(f"{caveat['page']} is no longer cited by the 1835 spend, "
                             "so the caveat written about it is stale")
        out += [f"**Where it very nearly does touch — `{caveat['page']}`.** "
                + caveat["text"], ""]

    out += [
        "## The tickets this closed",
        "",
        "Each keeps its file, its findings and its acceptance, marked `withdrawn` and naming",
        "T-1290. Nothing is deleted and no finding is overturned: a later run that genuinely",
        "needs one page reads what was already established and picks it up again.",
        "",
        "| ticket | state | folded into |",
        "|---|---|---|",
    ]
    for tid, state, blocked in folded_state(spec):
        out.append(f"| `{tid}` | {state} | {blocked or '—'} |")
    out += [
        "",
        "---",
        "",
        f"Stop condition (T-1290): {spec['stop_condition']}",
    ]
    return out


def render() -> str:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    return "\n".join(lines(spec)) + "\n"


# ---------------------------------------------------------------------------

def self_test() -> int:
    """The report is worth nothing unless its figures really come off the tree."""
    failures = []
    spec = json.loads(SPEC.read_text(encoding="utf-8"))

    # 1. no figure is typed into the spec: every one resolves through the tree
    for cls in spec["classes"]:
        for row in cls["rows"]:
            for name, f in (row.get("figures") or {}).items():
                if not ({"path", "difference", "count_where", "find", "absent",
                         "pages_absent"} & set(f)):
                    failures.append(f"{row['id']}.{name} carries no resolver")

    # 2. a moved page file moves the report — the drift this gate exists for
    page = json.loads((PAGES / "33SQ-GYYJ-5H.json").read_text(encoding="utf-8"))
    before = walk(page, "total_column_as_read.footed")
    page["total_column_as_read"]["footed"] = before + 1
    real, PAGES_cache = load_page, {}

    def stubbed(name, _page=page):
        return _page if name == "33SQ-GYYJ-5H.json" else real(name)

    globals()["load_page"] = stubbed
    try:
        moved = render()
    finally:
        globals()["load_page"] = real
    if moved == render():
        failures.append("the report did not move when a committed footing did")
    if f"| heads adjudicated in the 1840 crosswalk |" not in render():
        failures.append("the derived effect section is not in the report")

    # 3. a figure the tree stops carrying is a failure, never a silent blank
    try:
        resolve({"path": "total_column_as_read.no_such_key"}, "33SQ-GYYJ-5H.json")
        failures.append("a missing figure resolved instead of raising")
    except Unresolved:
        pass
    try:
        resolve({"path": "footer_as_read.mining"}, "33SQ-GYYJ-5H.json")
        failures.append("a null figure resolved without a stated reading")
    except Unresolved:
        pass

    # 4. the folded tickets are still folded, and still in the tree
    for tid, state, blocked in folded_state(spec):
        if state != "withdrawn":
            failures.append(f"{tid} is {state}, not withdrawn")
        if "T-1290" not in blocked:
            failures.append(f"{tid} does not name T-1290 as what it folded into")

    for line in failures:
        print(f"   FAIL: {line}")
    if failures:
        return 1
    rows = sum(len(c["rows"]) for c in spec["classes"])
    print(f"   OK: {rows} residue row(s) in {len(spec['classes'])} class(es), "
          f"{len(spec['folded_tickets'])} folded ticket(s), every figure off the tree")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the committed report")
    ap.add_argument("--check", action="store_true",
                    help="re-derive and fail if the committed report has drifted")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    try:
        text = render()
    except Unresolved as exc:
        print(f"   UNRESOLVED: {exc}")
        return 1
    if args.write:
        REPORT.write_text(text, encoding="utf-8")
        print(f"   wrote {REPORT.relative_to(ROOT)}")
        return 0
    if args.check:
        if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != text:
            print(f"   DRIFT: {REPORT.relative_to(ROOT)} is not what the tree derives")
            return 1
        print(f"   OK: {REPORT.relative_to(ROOT)} still describes the tree")
        return 0
    print(text, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
