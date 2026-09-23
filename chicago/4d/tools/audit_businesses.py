#!/usr/bin/env python3
"""Every present business record audited against the research it is compiled from (T-1402).

    python3 tools/audit_businesses.py             print the audit
    python3 tools/audit_businesses.py --write     regenerate docs/RESEARCH/business-audit-2026-09.md
    python3 tools/audit_businesses.py --check     the report re-derives (the gate)
    python3 tools/audit_businesses.py --self-test the rules below, held over fixtures

T-1402, of T-1182. THE LAYER WAS BUILT AND NEVER READ BACK. `compile_businesses.py`
turns the register's 196 rows into records with a tier on every field, and its own
`--check` asserts one thing: that a rebuild reproduces what is committed. That is a
derivation gate and it is silent on whether the derivation says what the RESEARCH says.
identity.json rules that two printed spellings are one house; trade_class_rulings.json
rules which December 1835 census class a trade belongs to; the register brackets four
houses that moved. Nothing measured whether the layer honoured any of it, and the
answer to "how well is this layer evidenced, field by field?" lived in nobody's head.

WHAT IT ASSERTS, and it is deliberately narrow: that the layer AGREES with the rulings
already made. It makes no new ruling, promotes no tier and writes no record. Where the
evidence stops, this says where it stops and hands the gap to the ticket that owns it —
goods to T-1404, staff to T-1183 and T-1189, customers to T-1189, the class counts to
the trade-census crosswalk. An audit that repaired what it measured would be measuring
its own work.

THE EMPTY COLUMN IS THE POINT. A field left empty is either a true reading of the
sources (the papers name owners and almost never a clerk) or an omission, and the two
look identical in a record. So every empty field here carries a REASON, stated once
below as this layer's policy, and the table counts empties against it. A field that
runs empty with no policy to stand on is the finding.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from compile_gazetteer import ROOT, RESEARCH  # noqa: E402

BUSINESSES = ROOT / "data" / "businesses"
AUTHORED = BUSINESSES / "authored"
IDENTITY = RESEARCH / "identity.json"
REGISTER = RESEARCH / "register_1835.json"
RULINGS = RESEARCH / "trade_class_rulings.json"
REPORT = ROOT / "docs" / "RESEARCH" / "business-audit-2026-09.md"

GRADES = ("attested", "inferred", "reconstructed")

# The fields this layer carries, in record order, each with how its grade is read and —
# where it may stand empty — the policy that lets it. `rows` grades every row by its own
# `tier`; `block` reads one `tier` off the block; `reading` is the printed notice restated,
# which is attested wherever it is filled and carries no tier of its own to read.
FIELDS = [
    ("name", "reading", None),
    ("type", "reading",
     "`not_stated` where the notice prints neither a trade nor an article to read a class off "
     "(trade_class_rulings.json's own ruling, boundary B6); never an empty list."),
    ("trade", "reading",
     "The notice prints no trade. The class ruling records the same absence as `not_stated`."),
    ("occupation", "reading",
     "No single occupation word the register will stand behind for this house."),
    ("goods", "reading",
     "The notice names no article. A lawyer, a school or a physician sells no goods; a store "
     "that names none is a gap, and T-1404 works the trades from the research."),
    ("firm_styles", "reading",
     "The house is printed under one style only, so there is no second style to keep."),
    ("proprietors", "rows",
     "The notice names no keeper — an unsigned advertisement, or one signed by a firm style "
     "alone. A null here is a finding about the paper, not a person left out."),
    ("partners", "rows",
     "A sole keeper, or no keeper named at all. `compile_businesses` files a lone name as a "
     "proprietor and only a firm of two or more as partners."),
    ("staff", "rows",
     "THE PAPERS NAME OWNERS AND ALMOST NEVER A CLERK, so empty on a record the register "
     "compiled is a true reading of the register and not an omission. What is no longer empty "
     "is the 84 houses T-1433's seating seated a reconstructed hand in: T-1462 lays those 124 "
     "seats on as `staff` rows at their own tier, each with its seed and its basis."),
    ("locations", "rows", None),
    ("dates", "block", None),
    ("proprietor_community", "block",
     "No keeper this record names has a community on their town card, so there is nothing to "
     "read a house's community off. Never inferred from a surname."),
    ("customers", "rows",
     "The register carries no customer claim at all; T-1189 is where a workplace gets its "
     "people."),
    ("sources", "reading", None),
]


def load_records():
    """The COMPILED layer, which is what this audit is about.

    `data/businesses/authored/` holds what a human or a reconstruction pass wrote — T-1184's
    druggists today — and those are deliberately NOT audited here. They are not compiled
    from the register, so identity.json's merges, the register's date fields and its anchor
    brackets say nothing about them, and every assertion below would be measuring the wrong
    thing. Their own gate is `reconstruct_businesses_1835.py --check`. What this audit owes
    them is a COUNT, printed in the report, so the scope is stated rather than assumed and a
    layer that grows past this tool cannot do it silently.
    """
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted(BUSINESSES.glob("biz_*.json"))]


def authored_records():
    return sorted(p.stem for p in AUTHORED.glob("*.json"))


# ------------------------------------------------------------------ the field table

def field_row(records, field, how):
    """`(filled_by_grade, empty, rows)` for one field over every record."""
    filled = {g: 0 for g in GRADES}
    empty = 0
    rows = 0
    for record in records:
        value = record.get(field)
        if how == "rows":
            if not value:
                empty += 1
                continue
            rows += len(value)
            for row in value:
                tier = row.get("tier")
                if tier in filled:
                    filled[tier] += 1
        elif how == "block":
            tier = (value or {}).get("tier")
            if not value or not tier:
                empty += 1
            else:
                filled[tier] = filled.get(tier, 0) + 1
                rows += 1
        else:
            # A reading off the printed notice. `not_stated` is the class ruling's own word
            # for "no class can be read off this notice", so it counts as empty here.
            if not value or value == ["not_stated"]:
                empty += 1
            else:
                filled["attested"] += 1
                rows += 1
    return filled, empty, rows


# -------------------------------------------------------------- identity adjudication

def firm_styles_of(records):
    out = set()
    for record in records:
        out.add(record["name"])
        out.update(record.get("firm_styles") or [])
    return out


def person_styles_of(record):
    """Every spelling the record carries for a person — the row's name and its folded styles."""
    people = (record.get("proprietors") or []) + (record.get("partners") or []) \
        + (record.get("staff") or [])
    names = {p["name"] for p in people}
    folded = {a for p in people for a in (p.get("also_printed_as") or [])}
    return names, folded


def identity_findings(records, identity):
    """Every merge and refusal in identity.json, measured against the layer."""
    by_id = {r["id"]: r for r in records}
    styles = firm_styles_of(records)
    out = {"firm": [], "firm_refusal": [], "proprietor": [], "distinction": []}

    for merge in identity.get("firm_merges") or []:
        # HONOURED means the merged-away spelling is not a house of its own. It may still
        # stand as a `firm_styles` entry on the record it merged INTO — the typography is
        # evidence and the layer keeps it there deliberately.
        standing = [r["id"] for r in records if r["name"] == merge["from"]]
        carried = [r["id"] for r in records if merge["from"] in (r.get("firm_styles") or [])]
        out["firm"].append({
            "from": merge["from"], "into": merge["into"],
            "verdict": "breached" if standing else "honoured",
            "where": standing or carried,
            "into_stands": merge["into"] in styles,
        })

    for refusal in identity.get("refused_firm_merges") or []:
        # A REFUSAL IS A CLAIM TOO: the two spellings must still be able to stand apart.
        # Measured as "the layer has not quietly folded one into the other" — the `from`
        # style is nowhere on the record the `into` style names.
        into_records = [r for r in records
                        if r["name"] == refusal["into"] or refusal["into"] in (r.get("firm_styles") or [])]
        folded = [r["id"] for r in into_records if refusal["from"] in (r.get("firm_styles") or [])]
        out["firm_refusal"].append({
            "from": refusal["from"], "into": refusal["into"], "kind": refusal.get("kind"),
            "verdict": "breached" if folded else "honoured", "where": folded,
        })

    for merge in identity.get("proprietor_merges") or []:
        record_id = "biz_" + merge["business"][len("business_"):]
        record = by_id.get(record_id)
        if record is None:
            out["proprietor"].append({"business": record_id, "from": merge["from"],
                                      "into": merge["into"], "verdict": "no record",
                                      "where": []})
            continue
        names, folded = person_styles_of(record)
        firm = set(record.get("firm_styles") or []) | {record["name"]}
        out["proprietor"].append({
            "business": record_id, "from": merge["from"], "into": merge["into"],
            # The merged-away spelling may survive as a folded style or as a firm style;
            # what it may not be is a second PERSON on the record.
            "verdict": "breached" if merge["from"] in names else "honoured",
            "where": sorted(n for n in (folded | firm) if n == merge["from"]),
            "into_stands": merge["into"] in names or merge["into"] in firm,
        })

    for distinction in identity.get("proprietor_distinctions") or []:
        record_id = "biz_" + distinction["business"][len("business_"):]
        record = by_id.get(record_id)
        names = person_styles_of(record)[0] if record else set()
        missing = [n for n in distinction["names"] if n not in names]
        out["distinction"].append({
            "business": record_id, "names": distinction["names"],
            "verdict": "honoured" if not missing else "breached", "where": missing,
        })
    return out


# ------------------------------------------------------------------- dates and places

def date_findings(records, register):
    by_id = {b["id"]: b for b in register["businesses"]}
    announced, dissolved, bounded, unbounded, wrong = [], [], [], [], []
    for record in records:
        entry = by_id.get(record["register_id"]) or {}
        dates = record["dates"]
        has_announced = bool([o for o in entry.get("opening_announced") or [] if o.get("iso")])
        has_dissolved = bool(entry.get("dissolved_after_scene_date") or [])
        if has_announced:
            announced.append(record["id"])
            if dates["precision"] != "exact" or dates["tier"] != "attested":
                wrong.append((record["id"], "an announced opening is not dated exact/attested"))
        elif dates["opened"]:
            bounded.append(record["id"])
            if dates["precision"] != "not_later_than" or dates["tier"] != "inferred":
                wrong.append((record["id"], "a first-printing bound is not not_later_than/inferred"))
        else:
            unbounded.append(record["id"])
        if has_dissolved:
            dissolved.append(record["id"])
            if not dates["closed"]:
                wrong.append((record["id"], "a printed dissolution leaves the house unclosed"))
        elif dates["closed"]:
            wrong.append((record["id"], "closed with no dissolution printed"))
    return {"announced": announced, "dissolved": dissolved, "bounded": bounded,
            "unbounded": unbounded, "wrong": wrong}


def relocation_findings(records, register):
    """The four houses the register brackets a move for, and how each siting is now dated."""
    by_id = {b["id"]: b for b in register["businesses"]}
    out = []
    for record in records:
        entry = by_id.get(record["register_id"]) or {}
        block = entry.get("anchor_change") or {}
        if not block.get("changes"):
            continue
        change = block["changes"][0]
        live = block.get("live_anchor")
        primary = next(l for l in record["locations"] if l.get("primary"))
        secondary = [l for l in record["locations"] if not l.get("primary")]
        out.append({
            "id": record["id"],
            "live": live,
            "side": "earlier" if live == change.get("to") else "later",
            "from_anchor": change.get("from"), "to_anchor": change.get("to"),
            "after": change.get("after"), "before": change.get("before"),
            "primary": (primary["kind"], primary["from"], primary["to"]),
            "secondary": [(l["from"], l["to"]) for l in secondary],
            "changes": len(block["changes"]),
        })
    return sorted(out, key=lambda r: r["id"])


def location_findings(records):
    kinds, limits, plural = {}, 0, []
    for record in records:
        for loc in record["locations"]:
            kinds[loc["kind"]] = kinds.get(loc["kind"], 0) + 1
            if loc.get("limit_reason"):
                limits += 1
        if len(record["locations"]) > 1:
            plural.append(record["id"])
    return kinds, limits, sorted(plural)


def class_findings(records, rulings):
    vocabulary = {v["id"]: v for v in rulings["vocabulary"]}
    counts, unknown = {}, []
    for record in records:
        for cls in record["type"]:
            counts[cls] = counts.get(cls, 0) + 1
            if cls not in vocabulary:
                unknown.append((record["id"], cls))
    return vocabulary, counts, sorted(set(unknown))


# ------------------------------------------------------------------------- the report

def render(records, identity, register, rulings):
    ident = identity_findings(records, identity)
    dates = date_findings(records, register)
    moves = relocation_findings(records, register)
    kinds, limits, plural = location_findings(records)
    vocabulary, counts, unknown = class_findings(records, rulings)
    n = len(records)

    def verdicts(rows):
        return sum(1 for r in rows if r["verdict"] == "honoured"), len(rows)

    lines = []
    w = lines.append
    w("# The business layer, audited against the research")
    w("")
    w("GENERATED by `tools/audit_businesses.py --write`; `--check` re-derives it and the gate")
    w("runs that, so a hand edit here is a red gate. T-1402, of T-1182.")
    w("")
    w("This reads the %d compiled records of `data/businesses/` back against the research they" % n)
    w("are compiled from — `identity.json`'s rulings on who is one house and one man,")
    w("`trade_class_rulings.json`'s December 1835 census classes, and the register's own dated")
    w("brackets — and states, field by field, how well each is evidenced and what stands empty.")
    w("It makes no ruling of its own: where the evidence stops, it says where, and hands the gap")
    w("to the ticket that owns it.")
    w("")
    authored = authored_records()
    w("**Scope: the compiled layer only.** `data/businesses/authored/` holds %d record(s) that"
      % len(authored))
    if authored:
        w("a human or a reconstruction pass wrote — %s — and they are not audited here."
          % ", ".join("`%s`" % a for a in authored))
    else:
        w("a human or a reconstruction pass wrote, and they would not be audited here.")
    w("They are not compiled from the register, so identity.json's merges, the register's date")
    w("fields and its anchor brackets say nothing about them and every measurement below would")
    w("be measuring the wrong thing. Their gate is `reconstruct_businesses_1835.py --check`.")
    w("The count is printed so that a layer growing past this tool cannot do it silently.")
    w("")

    w("## 1. Field × grade")
    w("")
    w("`rows` grades every row of a list by its own `tier`; `block` reads one `tier` off the")
    w("block; `reading` is the printed notice restated and is attested wherever it is filled.")
    w("`empty` counts RECORDS with nothing in the field — its reason is § 2.")
    w("")
    w("| field | read as | attested | inferred | reconstructed | rows | empty (of %d) |" % n)
    w("|---|---|---:|---:|---:|---:|---:|")
    for field, how, _ in FIELDS:
        filled, empty, rows = field_row(records, field, how)
        w("| `%s` | %s | %d | %d | %d | %d | %d |"
          % (field, how, filled["attested"], filled["inferred"], filled["reconstructed"],
             rows, empty))
    w("")
    w("## 2. Every empty field, and the policy it stands on")
    w("")
    w("A field that runs empty with no policy behind it is the finding this table is for.")
    w("Every one below has one.")
    w("")
    w("| field | empty | why a record may carry nothing here |")
    w("|---|---:|---|")
    for field, how, reason in FIELDS:
        _, empty, _ = field_row(records, field, how)
        if not empty and reason is None:
            continue
        w("| `%s` | %d | %s |" % (field, empty, reason or "— never empty."))
    w("")

    w("## 3. Identity: the layer against `identity.json`")
    w("")
    w("A merge is HONOURED when the merged-away spelling is not a second house or a second")
    w("person. It may still stand on `firm_styles[]` or `also_printed_as[]` of the record it")
    w("merged into — the typography is evidence and the layer keeps it there deliberately.")
    w("A refusal is honoured when the layer has not quietly folded the two together anyway.")
    w("")
    w("| ruling | honoured | of |")
    w("|---|---:|---:|")
    for key, label in (("firm", "firm merges"), ("proprietor", "proprietor merges"),
                       ("firm_refusal", "refused firm merges"),
                       ("distinction", "proprietor distinctions — both men stand")):
        ok, total = verdicts(ident[key])
        w("| %s | %d | %d |" % (label, ok, total))
    w("")
    breaches = [(k, r) for k in ident for r in ident[k] if r["verdict"] != "honoured"]
    if breaches:
        w("BREACHES:")
        w("")
        for key, row in breaches:
            w("- **%s** — %s" % (key, json.dumps(row, sort_keys=True)))
    else:
        w("No breaches. Every merge, refusal and distinction identity.json states is the reading")
        w("the layer carries.")
    w("")
    kept = sum(1 for r in ident["firm"] if r["verdict"] == "honoured" and r["where"])
    w("%d of the %d merged-away firm spellings are kept on the merged record's `firm_styles[]`;"
      % (kept, len(ident["firm"])))
    w("the rest were never printed as a standing house in this window and so have nothing to")
    w("stand on.")
    w("")

    w("## 4. Dates: the register's own brackets, honoured")
    w("")
    w("| reading | records | how the record is dated |")
    w("|---|---:|---|")
    w("| the paper announces the opening | %d | `exact`, `attested` |" % len(dates["announced"]))
    w("| no announcement, a first printing | %d | `not_later_than`, `inferred` — the house was "
      "trading by then |" % len(dates["bounded"]))
    w("| neither | %d | `unbounded` |" % len(dates["unbounded"]))
    w("| a dissolution printed after the scene date | %d | `closed` at the last issue that "
      "carries the house |" % len(dates["dissolved"]))
    w("")
    if dates["wrong"]:
        w("FINDINGS:")
        w("")
        for record_id, why in dates["wrong"]:
            w("- `%s` — %s" % (record_id, why))
    else:
        w("No record dates itself out of step with what the register prints for it.")
    w("")

    w("## 5. The four houses that moved")
    w("")
    w("The register brackets a change of printed anchor for four businesses: `after` is the last")
    w("issue that sets the old one, `before` the first that sets the new, and the move falls")
    w("between them. **That pair is the bracket of the MOVE and not the span of either siting**,")
    w("and it was being written onto the superseded location as `from: after, to: before` — which")
    w("dated an address to exactly the window in which it was being replaced, and carried it up")
    w("to and including the first printing of its replacement. T-1402 re-dated both rows off")
    w("their own printings; `compile_businesses.locations_for` carries the reasoning.")
    w("")
    w("| record | live anchor (register's rule) | superseded / later anchor | move bracketed | "
      "live row | other row |")
    w("|---|---|---|---|---|---|")
    for move in moves:
        other = move["from_anchor"] if move["side"] == "earlier" else move["to_anchor"]
        w("| `%s` | %s | %s (%s) | %s → %s | %s %s → %s | %s |"
          % (move["id"], move["live"], other, move["side"], move["after"], move["before"],
             move["primary"][0], move["primary"][1], move["primary"][2] or "—",
             ", ".join("%s → %s" % (f, t or "—") for f, t in move["secondary"])))
    w("")
    w("`the_chicago_democrat` is why the direction is read off `live_anchor` and never assumed:")
    w("its move to Jones & King's is first printed 1835-08-05, AFTER the scene date, so the")
    w("register keeps the corner live and the LATER siting is the second row. Read as an")
    w("“earlier” anchor like the other three, that record carried the corner twice — once live,")
    w("once as its own predecessor — and the move to Jones & King's appeared nowhere on it.")
    w("")

    w("## 6. Places, and the limit on each")
    w("")
    w("| kind | rows | what it means |")
    w("|---|---:|---|")
    meanings = {
        "premises": "matched onto a committed structure — a roof of its own",
        "anchored": "placed against a landmark the town holds; no roof of its own (T-1401)",
        "street_only": "the paper names a street and no house on it",
        "unplaceable": "no anchor the town holds, or a prose anchor never resolved to an id",
    }
    for kind in sorted(kinds, key=lambda k: -kinds[k]):
        w("| `%s` | %d | %s |" % (kind, kinds[kind], meanings.get(kind, "")))
    w("")
    w("%d of the %d location rows carry a `limit_reason`; every row that is not a `premises`"
      % (limits, sum(kinds.values())))
    w("does. %d records carry a plural `locations[]`: %s — the four of § 5."
      % (len(plural), ", ".join("`%s`" % p for p in plural)))
    w("**Every other record holds exactly one place.** The research names secondary premises for")
    w("some of these houses — a warehouse on the river, a yard, an office at a hotel, an auction")
    w("stand — and none of")
    w("them is in this layer yet, because none is in the register: the register carries ONE")
    w("anchor per business and a change of it. Raising those rows is T-1405's (for persons) and")
    w("T-1404's (for firms) with the sources in front of them; it is named here as the layer's")
    w("largest standing gap and is not fixed by an audit.")
    w("")

    w("## 7. Class: `type` against the December 1835 State census")
    w("")
    w("Every class on a record is a class `trade_class_rulings.json` enumerates; the crosswalk")
    w("against the census's own counts is `tools/trade_census_1835.py --check` and is not")
    w("repeated here. What this adds is the shape of the population.")
    w("")
    w("| class | records | the census line |")
    w("|---|---:|---|")
    for cls in sorted(counts, key=lambda c: (-counts[c], c)):
        entry = vocabulary.get(cls) or {}
        w("| `%s` | %d | %s |" % (cls, counts[cls], entry.get("census_line", "—")))
    w("")
    if unknown:
        w("FINDINGS: a class no ruling enumerates — %s"
          % ", ".join("`%s` on `%s`" % (c, r) for r, c in unknown))
    else:
        w("No record carries a class the ruling file does not enumerate.")
    w("")
    w("`other` and `not_stated` are rulings, not gaps: `other` is a trade the enumeration does")
    w("not count (tailors, bakers, smiths, auctioneers, land agents, liveries, dentists), and")
    w("`not_stated` is a notice that prints neither a trade nor an article to read a class off.")
    w("")

    w("## 8. What this audit does not settle")
    w("")
    w("- **Goods on a store that names none** — T-1404, which works the in-window trades from")
    w("  the research and raises a business for each.")
    staffed = sum(1 for r in records if r.get("staff"))
    blocks = sum(1 for r in records if r.get("staffing"))
    w("- **Staff** — a staff row on %d of %d records; a `staffing` block on %d. The"
      % (staffed, n, blocks))
    w("  papers name proprietors and almost never a hand, so an empty list is a true reading")
    w("  of the register and not an omission. T-1183 rules the staffing model; T-1422 laid it")
    w("  over the schools and the printing offices as `staffing`, which names nobody; T-1462")
    w("  lays the 124 reconstructed seats T-1433 drew onto the 84 houses that took them, each")
    w("  with the shortfall that house still stands at against the model's typical band.")
    w("- **Secondary premises** — § 6. T-1404 and T-1405.")
    w("- **Black-owned and Native or Métis-run houses** — T-1403.")
    w("- **The class counts against the census's own** — `tools/trade_census_1835.py`.")
    return "\n".join(lines) + "\n"


def build():
    records = load_records()
    return render(records,
                  json.loads(IDENTITY.read_text(encoding="utf-8")),
                  json.loads(REGISTER.read_text(encoding="utf-8")),
                  json.loads(RULINGS.read_text(encoding="utf-8")))


def report():
    sys.stdout.write(build())
    return 0


def write():
    text = build()
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text, encoding="utf-8")
    print("wrote %s (%d lines)" % (REPORT.relative_to(ROOT), text.count("\n")))
    return 0


def check():
    want = build()
    if not REPORT.exists():
        print("FAIL %s is missing; run --write" % REPORT.relative_to(ROOT), file=sys.stderr)
        return 1
    got = REPORT.read_text(encoding="utf-8")
    if got != want:
        print("FAIL %s does not re-derive — run --write and commit the result"
              % REPORT.relative_to(ROOT), file=sys.stderr)
        want_lines, got_lines = want.splitlines(), got.splitlines()
        for i in range(max(len(want_lines), len(got_lines))):
            a = got_lines[i] if i < len(got_lines) else "(end of file)"
            b = want_lines[i] if i < len(want_lines) else "(end of file)"
            if a != b:
                print("  line %d\n    committed: %s\n    derived:   %s" % (i + 1, a, b),
                      file=sys.stderr)
                break
        return 1
    records = load_records()
    ident = identity_findings(records, json.loads(IDENTITY.read_text(encoding="utf-8")))
    breached = [r for k in ident for r in ident[k] if r["verdict"] != "honoured"]
    if breached:
        print("FAIL %d identity ruling(s) breached by the business layer" % len(breached),
              file=sys.stderr)
        return 1
    print("the business audit re-derives: %d record(s), every identity ruling honoured"
          % len(records))
    return 0


# ------------------------------------------------------------------------- self-test

def self_test():
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append("%s: got %r, wanted %r" % (label, got, want))

    def rec(**kw):
        base = {"id": "biz_x", "register_id": "business_x", "name": "X", "type": ["store"],
                "trade": "dry goods", "occupation": "merchant", "goods": ["calico"],
                "firm_styles": [], "proprietors": [], "partners": [], "staff": [],
                "locations": [], "dates": {}, "proprietor_community": {}, "customers": [],
                "sources": ["s"]}
        base.update(kw)
        return base

    # THE READING COLUMN. `not_stated` is the ruling file's word for "no class can be read
    # off this notice", so it is an EMPTY class and not a filled one.
    holds("a class counts as filled", field_row([rec()], "type", "reading")[1], 0)
    holds("not_stated counts as empty",
          field_row([rec(type=["not_stated"])], "type", "reading")[1], 1)
    holds("an empty list counts as empty", field_row([rec(goods=[])], "goods", "reading")[1], 1)

    # THE ROWS COLUMN grades each row, not the record.
    two = rec(proprietors=[{"name": "A", "tier": "attested"}, {"name": "B", "tier": "inferred"}])
    filled, empty, rows = field_row([two], "proprietors", "rows")
    holds("both rows are graded", (filled["attested"], filled["inferred"], rows, empty),
          (1, 1, 2, 0))
    holds("a record with no rows is one empty",
          field_row([rec()], "proprietors", "rows")[1], 1)

    # THE BLOCK COLUMN reads one tier, and a block with no tier is empty.
    holds("a dated block is one filled row",
          field_row([rec(dates={"tier": "inferred"})], "dates", "block")[0]["inferred"], 1)
    holds("a block with no tier is empty", field_row([rec(dates={})], "dates", "block")[1], 1)

    # IDENTITY. A merged-away spelling on firm_styles is HONOURED; as a standing house it
    # is a breach. This is the distinction the whole section turns on.
    ident = {"firm_merges": [{"from": "Jno. L. Wilson & Co.", "into": "J. L. Wilson & Co."}],
             "refused_firm_merges": [], "proprietor_merges": [], "proprietor_distinctions": []}
    kept = rec(id="biz_w", name="J. L. Wilson & Co.", firm_styles=["Jno. L. Wilson & Co."])
    holds("a style kept on the merged record is honoured",
          identity_findings([kept], ident)["firm"][0]["verdict"], "honoured")
    standing = rec(id="biz_w2", name="Jno. L. Wilson & Co.")
    holds("the same spelling as a standing house is a breach",
          identity_findings([kept, standing], ident)["firm"][0]["verdict"], "breached")

    # A PROPRIETOR MERGE is about a PERSON. The spelling may survive as a firm style.
    pm = {"firm_merges": [], "refused_firm_merges": [], "proprietor_distinctions": [],
          "proprietor_merges": [{"business": "business_m", "into": "Matthias Mason",
                                 "from": "Mathias Mason & Co."}]}
    m = rec(id="biz_m", register_id="business_m", name="Matthias Mason & Co.",
            proprietors=[{"name": "Matthias Mason", "tier": "attested", "also_printed_as": []}])
    holds("a merged-away style absent from the people is honoured",
          identity_findings([m], pm)["proprietor"][0]["verdict"], "honoured")
    m2 = rec(id="biz_m", register_id="business_m", name="Matthias Mason & Co.",
             proprietors=[{"name": "Matthias Mason", "tier": "attested", "also_printed_as": []},
                          {"name": "Mathias Mason & Co.", "tier": "attested",
                           "also_printed_as": []}])
    holds("the same style as a second person is a breach",
          identity_findings([m2], pm)["proprietor"][0]["verdict"], "breached")

    # A DISTINCTION asserts two men. Losing one of them is a breach.
    dn = {"firm_merges": [], "refused_firm_merges": [], "proprietor_merges": [],
          "proprietor_distinctions": [{"business": "business_b",
                                       "names": ["William Brewster", "Franklin Brewster"]}]}
    both = rec(id="biz_b", register_id="business_b",
               partners=[{"name": "William Brewster", "tier": "attested", "also_printed_as": []},
                         {"name": "Franklin Brewster", "tier": "attested", "also_printed_as": []}])
    holds("both men standing is honoured",
          identity_findings([both], dn)["distinction"][0]["verdict"], "honoured")
    one = rec(id="biz_b", register_id="business_b",
              partners=[{"name": "William Brewster", "tier": "attested", "also_printed_as": []}])
    holds("one of the two missing is a breach",
          identity_findings([one], dn)["distinction"][0]["verdict"], "breached")

    # DATES. The register's own fields decide what the record may say.
    register = {"businesses": [
        {"id": "business_a", "opening_announced": [{"iso": "1835-04-01", "claim": "c"}],
         "dissolved_after_scene_date": []},
        {"id": "business_b", "opening_announced": [], "dissolved_after_scene_date": []},
        {"id": "business_c", "opening_announced": [], "dissolved_after_scene_date": ["c"]},
    ]}
    good = [rec(id="biz_a", register_id="business_a",
                dates={"opened": "1835-04-01", "closed": None, "precision": "exact",
                       "tier": "attested"}),
            rec(id="biz_b", register_id="business_b",
                dates={"opened": "1835-01-01", "closed": None, "precision": "not_later_than",
                       "tier": "inferred"}),
            rec(id="biz_c", register_id="business_c",
                dates={"opened": "1835-01-01", "closed": "1835-08-05",
                       "precision": "not_later_than", "tier": "inferred"})]
    holds("a layer in step with the register has no findings",
          date_findings(good, register)["wrong"], [])
    holds("the announced opening is counted", len(date_findings(good, register)["announced"]), 1)
    slack = [rec(id="biz_a", register_id="business_a",
                 dates={"opened": "1835-04-01", "closed": None, "precision": "not_later_than",
                        "tier": "inferred"})]
    holds("an announced opening dated as a bound is a finding",
          len(date_findings(slack, register)["wrong"]), 1)
    unclosed = [rec(id="biz_c", register_id="business_c",
                    dates={"opened": "1835-01-01", "closed": None,
                           "precision": "not_later_than", "tier": "inferred"})]
    holds("a printed dissolution that leaves the house open is a finding",
          len(date_findings(unclosed, register)["wrong"]), 1)
    invented = [rec(id="biz_b", register_id="business_b",
                    dates={"opened": "1835-01-01", "closed": "1835-09-09",
                           "precision": "not_later_than", "tier": "inferred"})]
    holds("a closure with no dissolution printed is a finding",
          len(date_findings(invented, register)["wrong"]), 1)

    # THE MOVE'S DIRECTION is read off live_anchor, never assumed.
    moved = {"businesses": [{"id": "business_m", "anchor_change": {
        "live_anchor": "the Tremont House",
        "changes": [{"from": "Graves' Tavern", "to": "the Tremont House",
                     "after": "1834-06-11", "before": "1834-09-10"}]}}]}
    later = {"businesses": [{"id": "business_m", "anchor_change": {
        "live_anchor": "the corner",
        "changes": [{"from": "the corner", "to": "Jones & King's",
                     "after": "1834-12-03", "before": "1835-08-05"}]}}]}
    card = rec(id="biz_m", register_id="business_m", locations=[
        {"kind": "premises", "primary": True, "from": "1833", "to": None},
        {"kind": "unplaceable", "primary": False, "from": "1833", "to": "1834-06-11"}])
    holds("the live anchor on the change's `to` reads as the earlier siting",
          relocation_findings([card], moved)[0]["side"], "earlier")
    holds("the live anchor on the change's `from` reads as the later siting",
          relocation_findings([card], later)[0]["side"], "later")

    # AND THE COMPILER ITSELF: the register's bracket may never become a siting's span.
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import compile_businesses as cb
    entry = {"id": "business_m", "action": "new_building", "action_target": "tremont_house_1",
             "street_id": "dearborn", "action_note": "",
             "evidence": {"first_issue": "1833-12-17", "last_issue": "1835-08-05"},
             "anchor_change": {"live_anchor": "the Tremont House", "changes": [
                 {"from": "the corner of Franklin and South Water streets",
                  "to": "the Tremont House", "after": "1834-11-26", "before": "1835-05-20"}]}}
    locs = cb.locations_for(entry, {})
    holds("the superseded siting runs from the first printing to its own last",
          (locs[1]["from"], locs[1]["to"]), ("1833-12-17", "1834-11-26"))
    holds("the anchored live row starts at its anchor's first printing",
          locs[0]["from"], "1835-05-20")
    entry_late = dict(entry, anchor_change={"live_anchor": "the corner", "changes": [
        {"from": "the corner", "to": "Jones & King's",
         "after": "1834-12-03", "before": "1835-08-05"}]})
    locs = cb.locations_for(entry_late, {})
    holds("a later siting starts at its own first printing and is not closed",
          (locs[1]["from"], locs[1]["to"]), ("1835-08-05", None))
    holds("...and the live row keeps the record's first issue",
          locs[0]["from"], "1833-12-17")
    # A `premises` or `street_only` live row is NOT dated by the advertisement's anchor.
    entry_premises = dict(entry, action="enrich_existing", action_target="mason_blacksmith_shop",
                          match_tier="occupants")
    holds("a premises row is left on the record's own first issue",
          cb.locations_for(entry_premises, {})[0]["from"], "1833-12-17")
    # A live anchor on neither side of its own change is a refusal, not a guess.
    entry_bad = dict(entry, anchor_change={"live_anchor": "somewhere else", "changes": [
        {"from": "a", "to": "b", "after": "1834-01-01", "before": "1835-01-01"}]})
    try:
        cb.locations_for(entry_bad, {})
        holds("an unreadable live anchor is refused", "returned", "refused")
    except SystemExit:
        holds("an unreadable live anchor is refused", "refused", "refused")

    total = 24
    for line in failures:
        print("FAIL %s" % line, file=sys.stderr)
    print("self-test: %d/%d assertions hold" % (total - len(failures), total))
    return 1 if failures else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--report"
    sys.exit({"--report": report, "--write": write, "--check": check,
              "--self-test": self_test}.get(arg, report)())
