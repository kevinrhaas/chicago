#!/usr/bin/env python3
"""Per person, WHICH roles and WHICH places reach 1 July 1835 (T-1144 acceptance 7).

    python3 tools/report_convergence_coverage.py            the per-axis summary, read out
    python3 tools/report_convergence_coverage.py --build    write the table and the report
    python3 tools/report_convergence_coverage.py --check    it re-derives, and nothing drifted
    python3 tools/report_convergence_coverage.py --self-test the rules below, held over fixtures

WHAT THIS IS. T-1144's seventh acceptance, added by the owner on 2026-09-17: the
convergence report must NAME, per person, which of the plural `roles[]` (T-1145) and which
home, work and other locations (T-1147) reach the scene date, "so the sign-off ticket
T-1157 can read coverage per axis off one table rather than re-deriving it". The research
sign-off already counts these axes in aggregate — 160 role rows reach the day, 20
households carry a `lives_at`, 50 a `works_at` — but an aggregate cannot answer *which
person*, and every reader who wanted that has had to walk 1,258 household files and join
1,705 reconciliation rows by hand. This is that join, committed once.

IT RE-DECIDES NOTHING, AND THAT IS THE POINT. Every "reaches 1835-07-01" here is COPIED
from the derivation that owns it, never recomputed:

  * a role reaches the day on `roles[].covers_scene_date`, which
    `tools/derive_resident_roles.py` writes from `audit_scene_window_trades.covers_scene`.
    A second opinion on that rule is exactly what the roles tool says a compatibility view
    must not have, so this table takes the flag and does no date arithmetic of its own.
  * a home or a workplace reaches the day when the reconciliation row for that household
    is `disposition: resolved` at `date_precision: scene_date` — which is the only way
    `tools/location_reconciliation.py` grades a `home` or `workplace` claim it could place.
    A `limited` or `no_claim` row is a preserved refusal and says so; it is not a miss.
  * a `later_home_address` or `later_workplace_address` NEVER reaches the day. The
    reconciliation dates every one of them `directory_year` against a volume printed after
    the scene, which is the whole reason those two kinds exist as separate kinds.
  * a business premises reaches the day on the business record's own
    `present_at_scene_date`. The premises is carried to each person the firm names as
    proprietor, partner or staff, because "where does this man work" is a question about
    him and the answer is stored on the firm.

SO A ROW HERE CAN ONLY BE WRONG IF ITS SOURCE IS WRONG, and the sources are gated above
this step in check.sh. What this file adds is the join and the per-axis verdict, not a
new claim about anybody.

WHAT "COVERED" MEANS, AND WHAT IT DOES NOT. An axis is `reaches` for a person when at
least one of that person's rows on the axis reaches the scene date; `limited` when the
person has rows on the axis but none of them reaches; and `none` when the corpus makes no
claim on that axis about this person at all. The three are kept apart deliberately: the
queue's own header holds that "zero unclassified research does not mean forcing uncertain
people or locations into 1835", so a `limited` axis is a finished answer and a `none` axis
is a stated absence. Neither is a defect, and this report never totals them as one.

THE PRESENCE COLUMN IS THE HOUSEHOLD'S, NOT A FOURTH AXIS. It is carried so the table can
be read without a second file open — a man whose household is `uncertain` on the scene
date can still hold a role that reaches it, because the role is bounded by its source and
the presence verdict is bounded by the last dated sighting (T-1144 acceptance 9).
"""
from __future__ import annotations

import argparse
import glob
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
BUSINESSES = DATA / "businesses"
RECONCILIATION = DATA / "research" / "location_reconciliation.json.gz"
OUT = DATA / "research" / "convergence_coverage.json.gz"
REPORT = ROOT / "docs" / "RESEARCH" / "convergence-coverage-2026-09.md"

SCENE_DATE = "1835-07-01"
TICKET = "T-1144"
AS_OF = "2026-09-18"

# The reconciliation's claim kinds, sorted onto the axes the owner named. `home` and
# `workplace` are the primary pair; the two `later_*` kinds and the business premises are
# the "other locations" he asked about, and they are kept as separate kinds inside that
# axis so the table never loses which kind a row was.
AXIS_OF_CLAIM_KIND = {
    "home": "home",
    "workplace": "work",
    "later_home_address": "other",
    "later_workplace_address": "other",
    "business_location": "other",
}
# The kinds that CANNOT reach the scene date, by construction rather than by measurement.
NEVER_REACHES = ("later_home_address", "later_workplace_address")

AXES = ("roles", "home", "work", "other")
VERDICTS = ("reaches", "limited", "none")


# ---------------------------------------------------------------------------
# the rules, each a pure function so --self-test can hold it over a fixture
# ---------------------------------------------------------------------------

def role_reaches(role: dict) -> bool:
    """A role reaches the scene date exactly when derive_resident_roles.py says so."""
    return role.get("covers_scene_date") is True


def location_reaches(row: dict, business_present: bool | None = None) -> bool:
    """A reconciliation row reaches the scene date.

    `home` and `workplace`: the row resolved onto a place AND the reconciliation dated it
    at the scene date. `later_*`: never. `business_location`: the firm's own
    `present_at_scene_date`, which is the business layer's verdict and not this file's.
    """
    kind = row.get("claim_kind")
    if kind in NEVER_REACHES:
        return False
    if kind == "business_location":
        return business_present is True
    return row.get("disposition") == "resolved" and row.get("date_precision") == "scene_date"


def axis_verdict(rows: list) -> str:
    """`reaches` if any claim on the axis reaches, `limited` if claims but none reach, else `none`.

    A row the reconciliation grades `no_claim` is NOT a claim — it is the reconciliation
    saying, on the record, that the corpus places this household nowhere. Every one of the
    1,258 households carries a `home` row for exactly that reason, so counting the row as a
    claim would read 1,186 stated absences as failed placements. A role row is always a
    claim: `roles[]` only holds roles a source printed.
    """
    claims = [r for r in rows if r.get("disposition") != "no_claim"]
    if not claims:
        return "none"
    return "reaches" if any(r["reaches_scene_date"] for r in claims) else "limited"


def presence_reaches(household: dict) -> bool:
    """The household's own presence verdict, unchanged — `present` and nothing else."""
    value = household.get("present_on_scene_date")
    if isinstance(value, dict):
        value = value.get("value")
    return value == "present"


# ---------------------------------------------------------------------------
# the join
# ---------------------------------------------------------------------------

def location_row(row: dict, business_present: bool | None, business_name: str | None) -> dict:
    return {
        "row_id": row["row_id"],
        "claim_kind": row["claim_kind"],
        "axis": AXIS_OF_CLAIM_KIND[row["claim_kind"]],
        "disposition": row.get("disposition"),
        "date_precision": row.get("date_precision"),
        "describes_date": row.get("describes_date"),
        "describes_date_last": row.get("describes_date_last"),
        "resolved_street": row.get("resolved_street"),
        "resolved_structure": row.get("resolved_structure"),
        "seating_class": row.get("seating_class"),
        "business_id": row.get("business_id"),
        "business_name": business_name,
        "limit_clause": row.get("limit_clause"),
        "reaches_scene_date": location_reaches(row, business_present),
    }


def person_row(household: dict, person: dict, rows: list) -> dict:
    """One person, both axes, with the rows the verdicts were read off."""
    roles = []
    for role in person.get("roles") or []:
        roles.append({
            "role": role.get("role"),
            "kind": role.get("kind"),
            "from": role.get("from"),
            "to": role.get("to"),
            "dated_by": role.get("dated_by"),
            "confidence": role.get("confidence"),
            "place": role.get("place"),
            "employer_or_body": role.get("employer_or_body"),
            "reaches_scene_date": role_reaches(role),
        })
    by_axis = {"home": [], "work": [], "other": []}
    for row in rows:
        by_axis[row["axis"]].append(row)

    presence = household.get("present_on_scene_date")
    presence_value = presence.get("value") if isinstance(presence, dict) else presence
    leg = presence.get("last_dated_appearance") if isinstance(presence, dict) else None

    verdicts = {
        "roles": axis_verdict(roles),
        "home": axis_verdict(by_axis["home"]),
        "work": axis_verdict(by_axis["work"]),
        "other": axis_verdict(by_axis["other"]),
    }
    return {
        "person_id": person.get("id"),
        "name": person.get("name"),
        "household_id": household.get("id"),
        "household_name": household.get("name"),
        "division": household.get("division"),
        "relationship": person.get("relationship"),
        "grade": person.get("grade"),
        "presence": {
            "value": presence_value,
            "reaches_scene_date": presence_reaches(household),
            "last_dated_appearance_reaches": (leg or {}).get("reaches"),
        },
        "axes": verdicts,
        "axes_reaching": [a for a in AXES if verdicts[a] == "reaches"],
        "roles": roles,
        "locations": {
            "home": by_axis["home"],
            "work": by_axis["work"],
            "other": by_axis["other"],
        },
    }


def read_businesses() -> tuple[dict, dict]:
    """(business_id -> record, person_id -> [business_id]) over the committed firms."""
    records: dict[str, dict] = {}
    by_person: dict[str, list] = {}
    for path in sorted(BUSINESSES.glob("biz_*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(record, dict) or "register_id" not in record:
            continue
        records[record["register_id"]] = record
        seen = set()
        for field in ("proprietors", "partners", "staff"):
            for member in record.get(field) or []:
                person_id = member.get("person_id") if isinstance(member, dict) else None
                if person_id and person_id not in seen:
                    seen.add(person_id)
                    by_person.setdefault(person_id, []).append(record["register_id"])
    return records, by_person


def read_reconciliation() -> list:
    return json.loads(gzip.decompress(RECONCILIATION.read_bytes()).decode("utf-8"))["rows"]


def build() -> dict:
    businesses, businesses_by_person = read_businesses()
    reconciliation = read_reconciliation()

    by_household: dict[str, list] = {}
    by_business: dict[str, list] = {}
    for row in reconciliation:
        if row["claim_kind"] not in AXIS_OF_CLAIM_KIND:
            continue
        if row["claim_kind"] == "business_location":
            by_business.setdefault(row["business_id"], []).append(row)
        elif row.get("household_id"):
            by_household.setdefault(row["household_id"], []).append(row)

    rows = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        household = json.loads(path.read_text(encoding="utf-8"))
        household_rows = [
            location_row(r, None, None)
            for r in sorted(by_household.get(household["id"], []), key=lambda r: r["row_id"])
        ]
        for person in household.get("persons") or []:
            person_rows = list(household_rows)
            for business_id in businesses_by_person.get(person.get("id"), []):
                record = businesses[business_id]
                present = record.get("present_at_scene_date") is True
                for row in sorted(by_business.get(business_id, []), key=lambda r: r["row_id"]):
                    person_rows.append(location_row(row, present, record.get("name")))
            rows.append(person_row(household, person, person_rows))

    rows.sort(key=lambda r: (r["household_id"] or "", r["person_id"] or ""))
    return {
        "schema": "convergence_coverage/1",
        "generated_by": "tools/report_convergence_coverage.py",
        "ticket": TICKET,
        "as_of": AS_OF,
        "scene_date": SCENE_DATE,
        "_doc": (
            "T-1144 acceptance 7. One row per person: which of the plural roles[] and which "
            "home, work and other locations reach the scene date. Every reach flag is copied "
            "from the derivation that owns it (derive_resident_roles.py, "
            "location_reconciliation.py, the business record's present_at_scene_date) and "
            "none is recomputed here. Derived — do not hand-edit; run "
            "tools/report_convergence_coverage.py --build."
        ),
        "compiled_from": [
            "data/residents/households/",
            "data/research/location_reconciliation.json.gz",
            "data/businesses/",
        ],
        "counts": counts_of(rows),
        "people": rows,
    }


def counts_of(rows: list) -> dict:
    axes = {
        axis: {verdict: sum(1 for r in rows if r["axes"][axis] == verdict) for verdict in VERDICTS}
        for axis in AXES
    }
    role_rows = [role for r in rows for role in r["roles"]]
    location_rows = [
        loc for r in rows for axis in ("home", "work", "other") for loc in r["locations"][axis]
    ]
    return {
        "people": len(rows),
        "households": len({r["household_id"] for r in rows}),
        "by_axis": axes,
        "people_by_axes_reaching": dict(
            sorted(Counter(str(len(r["axes_reaching"])) for r in rows).items())
        ),
        "presence": dict(sorted(Counter(str(r["presence"]["value"]) for r in rows).items())),
        "role_rows": len(role_rows),
        "role_rows_reaching": sum(1 for role in role_rows if role["reaches_scene_date"]),
        "role_rows_by_kind": dict(sorted(Counter(str(r["kind"]) for r in role_rows).items())),
        "location_rows": len(location_rows),
        "location_rows_reaching": sum(1 for loc in location_rows if loc["reaches_scene_date"]),
        "location_rows_by_kind": dict(
            sorted(Counter(loc["claim_kind"] for loc in location_rows).items())
        ),
    }


# ---------------------------------------------------------------------------
# the report
# ---------------------------------------------------------------------------

def fixture(rows: list, wanted: int) -> dict | None:
    for row in rows:
        if len(row["axes_reaching"]) == wanted:
            return row
    return None


def fmt(n: int) -> str:
    return f"{n:,}"


def report(doc: dict) -> str:
    counts = doc["counts"]
    rows = doc["people"]
    out = [
        "# Convergence coverage — which roles and which places reach 1 July 1835",
        "",
        f"Derived by `tools/report_convergence_coverage.py --build` ({doc['ticket']}, "
        f"acceptance 7) over `data/residents/households/`, the location reconciliation and "
        f"the business register. Table: `data/research/convergence_coverage.json.gz`, "
        f"{fmt(counts['people'])} rows, one per person. Do not edit either by hand.",
        "",
        "This report RE-DECIDES NOTHING. Every reach flag is copied from the derivation that "
        "owns it — `roles[].covers_scene_date` for a role, the reconciliation's "
        "`resolved`-at-`scene_date` grading for a home or a workplace, the firm's own "
        "`present_at_scene_date` for a business premises — so a row here can only be wrong if "
        "its source is wrong, and each of those sources is gated above this one.",
        "",
        "Read the three verdicts apart. **reaches** — at least one row on the axis reaches the "
        "scene date. **limited** — the corpus makes claims on the axis and not one of them "
        "reaches the day; that is a preserved refusal and a finished answer. **none** — the "
        "corpus makes no claim on the axis about this person, which is a stated absence. "
        "Adding `limited` to `none` and calling the total a gap is the error this table exists "
        "to stop.",
        "",
        "## Coverage per axis",
        "",
        "| Axis | reaches 1 Jul 1835 | limited | no claim |",
        "| --- | ---: | ---: | ---: |",
    ]
    labels = {
        "roles": "`roles[]` — trades, professions, offices",
        "home": "home (`lives_at`)",
        "work": "work (`works_at`)",
        "other": "other places — later addresses, business premises",
    }
    for axis in AXES:
        a = counts["by_axis"][axis]
        out.append(
            f"| {labels[axis]} | {fmt(a['reaches'])} | {fmt(a['limited'])} | {fmt(a['none'])} |"
        )
    out += [
        "",
        f"Of {fmt(counts['people'])} people in {fmt(counts['households'])} households.",
        "",
        "| Axes reaching the scene date | People |",
        "| --- | ---: |",
    ]
    for n, people in counts["people_by_axes_reaching"].items():
        out.append(f"| {n} | {fmt(people)} |")
    out += [
        "",
        "## The rows behind the verdicts",
        "",
        f"**Roles.** {fmt(counts['role_rows'])} dated role rows across the layer; "
        f"{fmt(counts['role_rows_reaching'])} reach 1 July 1835. By kind: "
        + ", ".join(f"`{k}` {fmt(v)}" for k, v in counts["role_rows_by_kind"].items())
        + ".",
        "",
        f"**Places.** {fmt(counts['location_rows'])} location rows reach a person; "
        f"{fmt(counts['location_rows_reaching'])} of them reach the scene date. By claim kind: "
        + ", ".join(f"`{k}` {fmt(v)}" for k, v in counts["location_rows_by_kind"].items())
        + ".",
        "",
        "A person inherits his household's `home` and `workplace` rows — the claim is made "
        "about the roof, not about the man — and inherits a `business_location` row from every "
        "firm that names him as proprietor, partner or staff. That is why the location row "
        "count above is larger than the reconciliation's own: the same roof is carried to each "
        "of the people living under it.",
        "",
        "## Presence, carried for reading",
        "",
        "| Household presence on the scene date | People |",
        "| --- | ---: |",
    ]
    for value, people in counts["presence"].items():
        out.append(f"| `{value}` | {fmt(people)} |")
    out += [
        "",
        "Presence is not a fifth axis. It is the household's verdict (T-1144 acceptance 9, with "
        "the last dated sighting under it) and it is carried here only so a row can be read "
        "without a second file open. A man whose household is `uncertain` may still hold a role "
        "that reaches the day: the role is bounded by its own source, and the two bounds are "
        "different questions.",
        "",
        "## Two rows, read out",
        "",
    ]
    for wanted, heading in ((3, "A person the corpus places on the day"),
                            (0, "A person no axis reaches")):
        row = fixture(rows, wanted)
        if row is None:
            continue
        out += [
            f"**{heading}.** {row['name']} (`{row['person_id']}`, {row['household_name']}), "
            f"presence `{row['presence']['value']}`, axes reaching: "
            + (", ".join(f"`{a}`" for a in row["axes_reaching"]) or "none")
            + ".",
            "",
            "| Axis | Verdict | Rows |",
            "| --- | --- | --- |",
            f"| `roles` | `{row['axes']['roles']}` | "
            + (" · ".join(
                f"{r['role']} ({r['kind']}, {r['from']}–{r['to']}, "
                f"{'reaches' if r['reaches_scene_date'] else 'dated away'})"
                for r in row["roles"]) or "—")
            + " |",
        ]
        for axis in ("home", "work", "other"):
            cells = " · ".join(
                f"{r['claim_kind']}: no claim" if r["disposition"] == "no_claim" else
                f"{r['claim_kind']}: {r['resolved_structure'] or r['resolved_street'] or r['disposition']}"
                f" ({'reaches' if r['reaches_scene_date'] else 'does not reach'})"
                for r in row["locations"][axis]
            ) or "—"
            out.append(f"| `{axis}` | `{row['axes'][axis]}` | {cells} |")
        out.append("")
    out += [
        "Reproduce: `python3 tools/report_convergence_coverage.py --check`.",
        "",
    ]
    return "\n".join(out)


# ---------------------------------------------------------------------------
# build / check / self-test
# ---------------------------------------------------------------------------

def write(doc: dict) -> None:
    raw = (json.dumps(doc, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report(doc), encoding="utf-8")


def read_committed():
    try:
        return json.loads(gzip.decompress(OUT.read_bytes()).decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None


def summary(doc: dict) -> str:
    counts = doc["counts"]
    parts = [
        f"{a}: {counts['by_axis'][a]['reaches']} reach / "
        f"{counts['by_axis'][a]['limited']} limited / {counts['by_axis'][a]['none']} no claim"
        for a in AXES
    ]
    return f"{counts['people']} people — " + "; ".join(parts)


def check(quiet: bool = False) -> int:
    doc = build()
    committed = read_committed()
    if committed is None:
        print(f"MISSING: {OUT.relative_to(ROOT)} — run --build", file=sys.stderr)
        return 1
    if committed != doc:
        drifted = [
            key for key in sorted(set(doc) | set(committed))
            if doc.get(key) != committed.get(key)
        ]
        print(f"DRIFT: {OUT.relative_to(ROOT)} no longer re-derives "
              f"({', '.join(drifted)}) — run --build", file=sys.stderr)
        return 1
    if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != report(doc):
        print(f"DRIFT: {REPORT.relative_to(ROOT)} no longer re-derives — run --build",
              file=sys.stderr)
        return 1
    if not quiet:
        print(summary(doc))
    return 0


def self_test() -> int:
    """Each rule, held over a fixture, and proved to move when its input moves."""
    failures = []

    def ok(label, condition):
        if condition:
            print(f"  ok   {label}")
        else:
            failures.append(label)
            print(f"  FAIL {label}")

    reaching_role = {"role": "grocer", "kind": "trade", "covers_scene_date": True}
    dated_away_role = {"role": "grocer", "kind": "trade", "covers_scene_date": False}
    ok("a role the roles tool covers reaches the day", role_reaches(reaching_role))
    ok("the same role with the flag down does not", not role_reaches(dated_away_role))
    ok("a role with no flag at all does not reach",
       not role_reaches({"role": "grocer", "kind": "trade"}))

    home = {"row_id": "hh_fixture#lives_at", "claim_kind": "home",
            "disposition": "resolved", "date_precision": "scene_date"}
    ok("a home resolved at the scene date reaches", location_reaches(home))
    ok("the same home, limited, does not",
       not location_reaches({**home, "disposition": "limited"}))
    ok("the same home, dated off the scene date, does not",
       not location_reaches({**home, "date_precision": "directory_year"}))
    ok("a later home address can never reach",
       not location_reaches({"claim_kind": "later_home_address", "disposition": "resolved",
                             "date_precision": "scene_date"}))
    ok("a later workplace address can never reach",
       not location_reaches({"claim_kind": "later_workplace_address", "disposition": "resolved",
                             "date_precision": "scene_date"}))
    premises = {"row_id": "business_fixture#location", "claim_kind": "business_location",
                "disposition": "resolved", "date_precision": "issue"}
    ok("a business premises reaches on the firm's own present_at_scene_date",
       location_reaches(premises, business_present=True))
    ok("and does not when the firm is not standing on the day",
       not location_reaches(premises, business_present=False))

    ok("an axis with a reaching row is `reaches`",
       axis_verdict([{"reaches_scene_date": True}, {"reaches_scene_date": False}]) == "reaches")
    ok("an axis with rows and no reach is `limited`",
       axis_verdict([{"reaches_scene_date": False}]) == "limited")
    ok("an axis with no rows at all is `none`", axis_verdict([]) == "none")
    ok("an axis holding only a `no_claim` row is `none`, not `limited`",
       axis_verdict([{"reaches_scene_date": False, "disposition": "no_claim"}]) == "none")
    ok("…and one live claim beside a `no_claim` row still decides the axis",
       axis_verdict([{"reaches_scene_date": False, "disposition": "no_claim"},
                     {"reaches_scene_date": True, "disposition": "resolved"}]) == "reaches")

    ok("a present household is present", presence_reaches({"present_on_scene_date":
                                                           {"value": "present"}}))
    ok("an uncertain household is not",
       not presence_reaches({"present_on_scene_date": {"value": "uncertain"}}))

    household = {
        "id": "hh_fixture", "name": "The fixture household", "division": "south",
        "present_on_scene_date": {"value": "uncertain",
                                  "last_dated_appearance": {"reaches": "1834-12-31"}},
        "persons": [{"id": "fixture_a", "name": "A Fixture", "relationship": "head",
                     "grade": "inferred", "roles": [reaching_role]}],
    }
    row = person_row(household, household["persons"][0],
                     [location_row(home, None, None)])
    ok("a person with a reaching role and a resolved home reaches both axes",
       row["axes"]["roles"] == "reaches" and row["axes"]["home"] == "reaches"
       and row["axes_reaching"] == ["roles", "home"])
    ok("…and his work and other axes stay `none`",
       row["axes"]["work"] == "none" and row["axes"]["other"] == "none")
    ok("…and his uncertain presence is carried, not converted into an axis",
       row["presence"]["value"] == "uncertain"
       and row["presence"]["reaches_scene_date"] is False
       and row["presence"]["last_dated_appearance_reaches"] == "1834-12-31")

    dated_away = person_row(
        {**household, "persons": [{**household["persons"][0], "roles": [dated_away_role]}]},
        {**household["persons"][0], "roles": [dated_away_role]},
        [location_row({**home, "disposition": "limited"}, None, None)],
    )
    ok("the same person with the flags down is `limited` on both, never `none`",
       dated_away["axes"]["roles"] == "limited" and dated_away["axes"]["home"] == "limited")

    print(f"self-test: {21 - len(failures)}/21 assertions hold")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(add_help=True, description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", dest="self_test", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        return self_test()
    if args.check:
        return check(quiet=args.quiet)
    if args.report:
        print(report(read_committed() or build()), end="")
        return 0
    if args.build:
        doc = build()
        write(doc)
        print(f"wrote {OUT.relative_to(ROOT)} ({doc['counts']['people']} people) "
              f"and {REPORT.relative_to(ROOT)}")
        return 0
    print(summary(build()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
