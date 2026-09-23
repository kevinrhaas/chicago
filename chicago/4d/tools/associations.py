#!/usr/bin/env python3
"""`associated_with[]` — the plural, dated places a person or household was (T-1238).

    python3 tools/associations.py            the coverage table, on stdout
    python3 tools/associations.py --write    write data/research/residents/association_coverage.json
    python3 tools/associations.py --check    re-derive the coverage and refuse a hand-edit
    python3 tools/associations.py --self-test the assertions of --check, broken on purpose

WHAT THIS IS FOR.

`lives_at` and `works_at` are SINGULAR and UNDATED, and both of those are
findings the sources do not support. Jeremiah Porter's record says so in its own
note: Andreas has P. F. W. Peck invite him "to make his temporary lodging place
and study in the unfinished loft" of the store, the word *temporary* is the
source's own, the link is dated 1833 — "whether he was still in the loft in
1835 ... is unknown". A single `lives_at: peck_store` states none of that. It
reads as the household's residence on the scene date, which is the one thing the
source refuses to say. T-1237's reconciliation row inherits the flattening and
dates the same claim `1835-07-01`, because that is all a singular field can mean.

So a relationship between a person and a place becomes a LIST of rows, each
carrying its own kind, its own dates and its own tier:

    {"kind": "lodging", "place_or_structure_id": "peck_store",
     "resolves_to": "structure", "from": "1833", "to": null,
     "tier": "attested", "source_id": "andreas_1884_v1", "note": "..."}

T-1147 clause 7 names the shape — `{kind, place_or_structure_id, from, to,
tier, source_id}` — and says it is written on the person. This module adds
`resolves_to` and `note` to it, for two reasons the rest of the layer already
insists on: a place that is a street is not a place that is a roof and a
consumer may not guess which it holds, and a claim in this dataset carries the
reasoning that made it.

TWO RULES THAT ARE NOT OBVIOUS, AND ARE THE POINT.

  * `place_or_structure_id` IS NEVER NULL. An absent relationship is an absent
    row. The four resolution rungs are the four a source can actually reach —
    structure, street, face, division — and "no place at all" is not one of
    them, because a relationship with no place is not a finding about where
    somebody was. (The seating-class axis T-1237 counts is a different
    question: it is defined over the WHOLE household layer, so it needs a
    `none` class. This list is defined over CLAIMS.)
  * THE SINGULAR LINK MAY NOT DRIFT FROM THE PLURAL ONE. While both shapes
    exist, a record that carries `associated_with` rows and a non-null
    `lives_at`/`works_at` must carry that structure among its rows. Otherwise
    the migration's half-way point is a record that says two different things
    about the same man and a reader picks whichever field they happened to
    load. `validate.py` refuses it.

`from` and `to` are nullable — the sources date a relationship's start far more
often than its end, and some they do not date at all. A row that dates NEITHER
end must say `"undated": true`, so an undated relationship is an admission that
can be counted rather than a gap that cannot.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COVERAGE = DATA / "research" / "residents" / "association_coverage.json"

# The kinds a source in this corpus has actually needed. The set grows the way
# `kin_relations` grows — when a reading needs a term and not before — and every
# kind here is named by T-1147 clause 7's own list ("a civic office's seat, a
# church, an agency held, land purchased, a school taught, a tavern kept") or is
# the home/workplace pair the clause is widening.
ASSOCIATION_KINDS = (
    "agency_held",
    "business_premises",
    "church",
    "civic_seat",
    "home",
    "land_purchased",
    "lodging",
    "school",
    "workplace",
)

# The rungs a piece of evidence can reach, best first. These are T-1237's own —
# `resolved_structure`, `resolved_street`, `resolved_face` — plus the division,
# which is the coarsest thing this dataset will call a place.
ASSOCIATION_RESOLUTION = ("structure", "street", "face", "division")

# Which kinds answer "where did he live" and which answer "where did he work".
# `land_purchased` is in NEITHER: a holding is not a place a man was.
HOME_KINDS = ("home", "lodging")
WORK_KINDS = ("agency_held", "business_premises", "church", "civic_seat",
              "school", "workplace")

ASSOCIATION_ROW_KEYS = ("kind", "place_or_structure_id", "resolves_to", "from", "to",
                        "tier", "source_id", "note")
ASSOCIATION_OPTIONAL_KEYS = ("undated",)

ASSOCIATION_TIERS = ("attested", "inferred", "reconstructed")


def read_bounds(value):
    """The earliest and latest day a `from`/`to` value permits, or None.

    A year, a month or a day - the three precisions the sources give. The value
    carries its own precision in its shape, which is why there is no separate
    precision field: '1833' is a year and cannot be mistaken for one.
    """
    s = str(value or "").strip()
    try:
        if len(s) == 4:
            y = int(s)
            return dt.date(y, 1, 1), dt.date(y, 12, 31)
        if len(s) == 7:
            y, m = int(s[:4]), int(s[5:7])
            if s[4] != "-":
                return None
            last = (dt.date(y + (m == 12), 1 if m == 12 else m + 1, 1) - dt.timedelta(days=1))
            return dt.date(y, m, 1), last
        if len(s) == 10:
            d = dt.date.fromisoformat(s)
            return d, d
    except ValueError:
        return None
    return None


def check_association_rows(where: str, rows, *, error, structure_ids: set, source_ids: set,
                           divisions: set, scene: dt.date) -> None:
    """Every rule the schema above states, reported through `error(where, message)`."""
    if not isinstance(rows, list) or not rows:
        error(where, "associated_with is present and is not a non-empty list. An empty list "
                     "claims a relationship that is not there; omit the key instead")
        return
    seen: set = set()
    for i, row in enumerate(rows):
        rwhere = f"{where}/associated_with[{i}]"
        if not isinstance(row, dict):
            error(rwhere, "an association row must be an object")
            continue
        for key in ASSOCIATION_ROW_KEYS:
            if key not in row:
                error(rwhere, f"missing required key '{key}'")
        extra = set(row) - set(ASSOCIATION_ROW_KEYS) - set(ASSOCIATION_OPTIONAL_KEYS)
        if extra:
            error(rwhere, f"unknown key(s) {sorted(extra)}. This shape is a contract T-1147 "
                          f"clause 7 states and T-1182 writes against; widen it in "
                          f"tools/associations.py, not in one record")

        kind = row.get("kind")
        if kind not in ASSOCIATION_KINDS:
            error(rwhere, f"kind '{kind}' is not one of {list(ASSOCIATION_KINDS)} - the set a "
                          f"record may use is the set a reading has needed, and it grows in "
                          f"tools/associations.py with the reading that needed it")

        rung = row.get("resolves_to")
        place = row.get("place_or_structure_id")
        if rung not in ASSOCIATION_RESOLUTION:
            error(rwhere, f"resolves_to '{rung}' is not one of {list(ASSOCIATION_RESOLUTION)}")
        if not isinstance(place, str) or not place.strip():
            error(rwhere, "place_or_structure_id is empty. An absent relationship is an absent "
                          "row - this list is defined over claims, and a claim with no place "
                          "is not one")
        elif rung == "structure" and place not in structure_ids:
            error(rwhere, f"resolves_to is 'structure' and '{place}' is not a structure id in "
                          f"data/structures/")
        elif rung == "division" and place not in divisions:
            error(rwhere, f"resolves_to is 'division' and '{place}' is not a division in the "
                          f"manifest vocabulary")
        elif rung in ("street", "face") and place in structure_ids:
            error(rwhere, f"resolves_to is '{rung}' and '{place}' is a structure id. A row that "
                          f"reaches a roof says so: the rung is the evidence's own limit and "
                          f"understating it loses a finding")

        tier = row.get("tier")
        if tier not in ASSOCIATION_TIERS:
            error(rwhere, f"tier '{tier}' is not one of {list(ASSOCIATION_TIERS)}")
        sid = row.get("source_id")
        if tier in ("attested", "inferred"):
            if not sid:
                error(rwhere, f"tier '{tier}' carries no source_id. A relationship a source "
                              f"states has to name the source that states it")
            elif sid not in source_ids:
                error(rwhere, f"source_id '{sid}' does not resolve in data/sources/")
        elif tier == "reconstructed" and sid:
            error(rwhere, "a reconstructed relationship names a source_id. Reconstruction is "
                          "what the project does where the sources are silent; citing one "
                          "would overstate it")
        if not str(row.get("note") or "").strip():
            error(rwhere, "note is empty. A relationship carries the reasoning that dated it "
                          "and the clause that limited its place")

        frm, to = row.get("from"), row.get("to")
        undated = bool(row.get("undated"))
        fb = read_bounds(frm) if frm is not None else None
        tb = read_bounds(to) if to is not None else None
        if frm is not None and fb is None:
            error(rwhere, f"from {frm!r} is not a year, a month or an ISO day")
        if to is not None and tb is None:
            error(rwhere, f"to {to!r} is not a year, a month or an ISO day")
        if frm is None and to is None and not undated:
            error(rwhere, "neither end is dated and the row does not say `undated: true`. An "
                          "undated relationship is an admission this project counts, not a "
                          "gap it leaves open")
        if undated and (frm is not None or to is not None):
            error(rwhere, "undated is true and the row carries a date. One of the two is wrong")
        if fb and tb and fb[0] > tb[1]:
            error(rwhere, f"from {frm!r} begins after to {to!r} ends")
        if fb and fb[0] > scene:
            error(rwhere, f"from {frm!r} begins after the scene date {scene.isoformat()}. A "
                          f"relationship that had not started is not in this scene")

        key = (kind, place, str(frm))
        if key in seen:
            error(rwhere, f"a second row states {kind!r} at {place!r} from {frm!r}. Plural does "
                          f"not mean repeated: one relationship, one row")
        seen.add(key)


def singular_drift(record: dict, rows) -> list[str]:
    """While both shapes exist, the singular link must appear among the plural rows."""
    out = []
    if not isinstance(rows, list):
        return out
    for key, kinds in (("lives_at", HOME_KINDS), ("works_at", WORK_KINDS)):
        node = record.get(key)
        value = (node or {}).get("value") if isinstance(node, dict) else None
        if not value:
            continue
        places = {r.get("place_or_structure_id") for r in rows
                  if isinstance(r, dict) and r.get("kind") in kinds}
        if value not in places:
            out.append(f"{key} names '{value}' and no {'/'.join(kinds)} row in associated_with "
                       f"reaches it. While both shapes exist they may not drift: a reader who "
                       f"loads one field would be told a different thing about the same person")
    return out


# --------------------------------------------------------------------------
# The coverage this schema has so far, counted.

def walk_records():
    """(where, record, rows) for every household and person carrying the key."""
    root = DATA / "residents" / "households"
    for path in sorted(root.glob("*.json")):
        h = json.loads(path.read_text())
        if "associated_with" in h:
            yield h.get("id"), "household", h, h.get("associated_with")
        for p in h.get("persons") or []:
            if "associated_with" in p:
                yield p.get("id"), "person", p, p.get("associated_with")


def derive() -> dict:
    by_kind: dict = {}
    by_rung: dict = {}
    by_tier: dict = {}
    records = 0
    rows_n = 0
    undated = 0
    for _id, _scope, _rec, rows in walk_records():
        records += 1
        for r in rows or []:
            rows_n += 1
            by_kind[r.get("kind")] = by_kind.get(r.get("kind"), 0) + 1
            by_rung[r.get("resolves_to")] = by_rung.get(r.get("resolves_to"), 0) + 1
            by_tier[r.get("tier")] = by_tier.get(r.get("tier"), 0) + 1
            if r.get("undated"):
                undated += 1
    return {
        "records_with_associations": records,
        "rows": rows_n,
        "undated_rows": undated,
        "by_kind": dict(sorted(by_kind.items())),
        "by_resolves_to": dict(sorted(by_rung.items())),
        "by_tier": dict(sorted(by_tier.items())),
    }


def payload() -> dict:
    return {
        "schema": "association_coverage/1",
        "generated_by": "tools/associations.py",
        "_doc": ("T-1238. How much of the resident layer has been migrated onto the plural, "
                 "dated `associated_with[]` shape, counted so the migration's remaining "
                 "distance is a number rather than an impression. DERIVED - rebuild with "
                 "--write, and --check refuses a hand-edit."),
        "vocabulary": {
            "kinds": list(ASSOCIATION_KINDS),
            "resolves_to": list(ASSOCIATION_RESOLUTION),
            "tiers": list(ASSOCIATION_TIERS),
            "home_kinds": list(HOME_KINDS),
            "work_kinds": list(WORK_KINDS),
        },
        "counts": derive(),
    }


def render(p: dict) -> str:
    c = p["counts"]
    lines = [f"associated_with: {c['rows']} row(s) on {c['records_with_associations']} record(s), "
             f"{c['undated_rows']} undated"]
    for label, key in (("kind", "by_kind"), ("rung", "by_resolves_to"), ("tier", "by_tier")):
        for k, v in c[key].items():
            lines.append(f"  {label:5} {k:20} {v}")
    return "\n".join(lines)


def main(argv) -> int:
    write = "--write" in argv
    check = "--check" in argv
    if "--self-test" in argv:
        return self_test()
    p = payload()
    if write:
        COVERAGE.parent.mkdir(parents=True, exist_ok=True)
        COVERAGE.write_text(json.dumps(p, indent=2) + "\n")
        print(f"wrote {COVERAGE.relative_to(ROOT)}")
        return 0
    if check:
        if not COVERAGE.exists():
            print(f"FAIL {COVERAGE.relative_to(ROOT)} is missing", file=sys.stderr)
            return 1
        committed = json.loads(COVERAGE.read_text())
        bad = [k for k in ("vocabulary", "counts") if committed.get(k) != p[k]]
        if bad:
            print(f"FAIL {COVERAGE.relative_to(ROOT)} does not re-derive: {bad} differ. "
                  f"Rebuild with --write; the file is derived and a hand-edit loses.",
                  file=sys.stderr)
            return 1
        print(f"ok  {render(p)}")
        return 0
    print(render(p))
    return 0


def self_test() -> int:
    """Break each refusal on purpose; a gate that cannot fail is not a gate."""
    errs: list = []

    def err(where, msg):
        errs.append((where, msg))

    base = dict(kind="home", place_or_structure_id="peck_store", resolves_to="structure",
                **{"from": "1833", "to": None}, tier="attested", source_id="andreas_1884_v1",
                note="n")
    env = dict(structure_ids={"peck_store"}, source_ids={"andreas_1884_v1"},
               divisions={"south"}, scene=dt.date(1835, 7, 1))

    def run(row):
        errs.clear()
        check_association_rows("t", [row], error=err, **env)
        return list(errs)

    cases = [
        ("a clean row passes", base, False),
        ("an undeclared kind", {**base, "kind": "tavern"}, True),
        ("a structure rung on a name no structure carries", {**base, "place_or_structure_id": "x"}, True),
        ("an empty place", {**base, "place_or_structure_id": ""}, True),
        ("a street rung on a roof", {**base, "resolves_to": "street"}, True),
        ("a division that is not one", {**base, "resolves_to": "division",
                                        "place_or_structure_id": "peck_store"}, True),
        ("an attested row with no source", {**base, "source_id": None}, True),
        ("a reconstructed row that cites one", {**base, "tier": "reconstructed"}, True),
        ("an empty note", {**base, "note": "  "}, True),
        ("a date that is not one", {**base, "from": "eighteen thirty-three"}, True),
        ("both ends null and no admission", {**base, "from": None, "to": None}, True),
        ("an undated row that carries a date", {**base, "undated": True}, True),
        ("from after to", {**base, "from": "1836", "to": "1834"}, True),
        ("from after the scene date", {**base, "from": "1836"}, True),
        ("an unknown key", {**base, "tenure": "loft"}, True),
    ]
    failed = 0
    for label, row, want_error in cases:
        got = run(row)
        ok = bool(got) == want_error
        print(("ok   " if ok else "FAIL ") + label + ("" if ok else f"  -> {got}"))
        failed += 0 if ok else 1

    errs.clear()
    check_association_rows("t", [base, dict(base)], error=err, **env)
    ok = any("one relationship, one row" in m for _w, m in errs)
    print(("ok   " if ok else "FAIL ") + "the same relationship written twice")
    failed += 0 if ok else 1

    errs.clear()
    check_association_rows("t", [], error=err, **env)
    ok = bool(errs)
    print(("ok   " if ok else "FAIL ") + "an empty list")
    failed += 0 if ok else 1

    drift = singular_drift({"lives_at": {"value": "other_house"}}, [base])
    ok = bool(drift)
    print(("ok   " if ok else "FAIL ") + "the singular link drifting from the plural one")
    failed += 0 if ok else 1

    kept = singular_drift({"lives_at": {"value": "peck_store"}}, [base])
    ok = not kept
    print(("ok   " if ok else "FAIL ") + "…and agreeing with it")
    failed += 0 if ok else 1

    print(f"{failed} failure(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
