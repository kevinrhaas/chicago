#!/usr/bin/env python3
"""A resident's trades, professions and offices as DATED PLURAL ROLES (T-1229, of T-1145).

    python3 tools/derive_resident_roles.py             what the cards would carry, read out
    python3 tools/derive_resident_roles.py --write     write roles[] and the 1835 view
    python3 tools/derive_resident_roles.py --check     it re-derives, and nothing has drifted
    python3 tools/derive_resident_roles.py --self-test the rules below, held over fixtures

WHY A SINGULAR FIELD IS THE DEFECT. `persons[].occupation` holds ONE trade and one
confidence, so a man printed as a candle manufacturer in 1833, a brickmaker in 1839 and a
school inspector in the same register can only be one of them on his own card. Daniel
Elston is the fixture the owner named: the card showed `soap_and_candle_maker` and graded
it an attested 1835 occupation, which is two errors in one field — it erased four other
roles, and it dated the surviving one to a year no source cited for it describes.

WHAT THIS TOOL ASSERTS, and it is three sentences.

  1. `roles[]` is CANONICAL. Every role the card's own evidence carries becomes a row
     naming a controlled role, the kind of role it is, the bound its evidence permits,
     how it was dated, its confidence and the sources it rests on. Two roles are two
     rows; a role whose date is unknown stays unknown and is never widened to 1835.

  2. `occupation` is a GENERATED COMPATIBILITY VIEW of the roles that actually cover
     1835-07-01 — the field the renderer, the people index and the scene compiler still
     read. Where two roles cover the day, both stand in `roles[]` and
     `occupation.roles_at_scene_date` names both, so the singular field can no longer
     decide which of a man's two trades the town is told about.

  3. A ROLE THAT DOES NOT REACH 1835 CANNOT FILL THE 1835 FIELD. That is T-0991's
     repair, and it is made here rather than by hand: the six trades
     `tools/audit_scene_window_trades.py` still reports keep their printing as a dated
     pre-scene role, the 1835 field falls to `none_recorded`, and
     `occupation.withdrawn_from_scene_date` carries the audit's own verdict and note so
     the withdrawal states its reason on the card rather than only in a ledger.

THE DATE RULE IS THE AUDIT'S, DELIBERATELY. A role derived from the 1835 block is bounded
by the `describes_date` spans of the sources that block cites, and it "covers" the scene
date on exactly `audit_scene_window_trades.covers_scene` — the span names a year range
containing 1835. That is a bound from the SOURCE and not a claim about the man, which is
why `dated_by` says which of the two a row is and why `precision` can say `source_span`.
Widening it would quietly re-assert what T-0837's write gate refuses; narrowing it would
disagree with the audit this repair is measured by, and a second opinion on that rule is
the one thing a compatibility view must not have.

WHAT THIS TICKET DOES NOT READ. The newspaper gazetteer's `persons[].occupations[]`, the
1839 directory and civic-register crosswalks and the 1843/1844 identity-master appearances
are T-1254, together with each role's stated place and employer and the migration table.
The people view's dated timeline is T-1255. This tool reads the CARD, and only the card.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
SOURCES = DATA / "sources"
INDEX = DATA / "residents" / "index.json"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_scene_window_trades import VERDICTS, covers_scene  # noqa: E402

SCENE_DATE = "1835-07-01"
ABSENT = "none_recorded"
GENERATOR = "tools/derive_resident_roles.py"
TICKET = "T-1229"

# The grades that make a role a CLAIM, and so the grades that may fill the 1835 view.
# Identical to the audit's, and for the same reason: `reconstructed` is this dataset's
# word for a figure the reconstruction supplies rather than a source.
CLAIMING = ("attested", "documented", "inferred")

ROLE_KINDS = ("trade", "profession", "office", "employment", "business_interest")
ROLE_PRECISION = ("day", "month", "year", "source_span", "unknown")
DATED_BY = ("source_describes_date", "printing_year", "stated_date", "undated")

# WHICH KIND A CONTROLLED ROLE IS. The residents vocabulary has never separated these —
# `postmaster` and `blacksmith` sit in one alphabetical list — and T-1145 needs the
# separation because an office and a trade are held on different evidence and, from
# T-1254, by different bodies. The two sets below are enumerated rather than matched:
# a fuzzy rule is how every milliner in this corpus once compiled as a grain MILLER
# (T-0376). Anything not named here is a `trade`, and `--self-test` refuses a name in
# either set that the manifest vocabulary does not carry.
OFFICES = frozenset({
    "county_clerk", "fire_warden", "indian_agent", "justice_of_the_peace",
    "land_office_receiver", "land_office_register", "lighthouse_keeper",
    "militia_officer", "postmaster", "public_administrator", "sheriff", "sub_agent",
    "town_assessor", "town_clerk", "town_president",
})
PROFESSIONS = frozenset({
    "army_officer", "army_surgeon", "attorney", "barber_surgeon", "chaplain",
    "dancing_master", "dentist", "editor", "engineer", "interpreter", "minister",
    "music_teacher", "physician", "priest", "schoolteacher", "surveyor",
})


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def describes_date(sid: str) -> str:
    path = SOURCES / f"{sid}.json"
    if not path.exists():
        return ""
    try:
        return str(read_json(path).get("describes_date") or "")
    except Exception:
        return ""


def kind_of(role: str) -> str:
    if role in OFFICES:
        return "office"
    if role in PROFESSIONS:
        return "profession"
    return "trade"


def _ends(span: str) -> tuple[str, str]:
    """The two ends of a `describes_date`, as the source writes them.

    `1833-11/1835-08` is a slashed range, `1673-1857` a hyphenated one of bare years,
    `1839` a single year and `1833-11` a single month. Anything this cannot read is an
    unknown bound and says so rather than guessing at one.
    """
    span = (span or "").strip()
    if not span:
        return "", ""
    if "/" in span:
        a, b = span.split("/", 1)
        return a.strip(), b.strip()
    parts = span.split("-")
    if len(parts) == 2 and all(p.isdigit() and len(p) == 4 for p in parts):
        return parts[0], parts[1]
    if span.replace("-", "").isdigit() and len(parts) <= 2:
        return span, span
    return "", ""


def _precision(frm: str, to: str) -> str:
    if not frm or not to:
        return "unknown"
    if frm != to:
        return "source_span"
    return {4: "year", 7: "month", 10: "day"}.get(len(frm), "source_span")


def _bound(sources: list[str]) -> tuple[str, str, str]:
    """The widest bound the cited sources permit, and how precise it is."""
    ends = [_ends(describes_date(s)) for s in sources]
    starts = sorted(a for a, _ in ends if a)
    finishes = sorted(b for _, b in ends if b)
    if not starts or not finishes:
        return "", "", "unknown"
    frm, to = starts[0], finishes[-1]
    return frm, to, _precision(frm, to)


def scene_role(occ: dict, person_id: str) -> dict | None:
    """The role the 1835 `occupation` block is standing on, whatever year it is about.

    ONCE A TRADE IS WITHDRAWN THE BLOCK NO LONGER NAMES IT, so the withdrawal is read
    first. Without that this tool is not idempotent: it would withdraw a trade on one
    run and then, finding `none_recorded`, delete the role carrying it on the next —
    losing the very evidence the withdrawal was written to preserve.
    """
    withdrawn = occ.get("withdrawn_from_scene_date")
    if isinstance(withdrawn, dict) and withdrawn.get("value"):
        role, confidence = withdrawn.get("value"), withdrawn.get("confidence")
    else:
        role, confidence = occ.get("value"), occ.get("confidence")
    if not role or role == ABSENT:
        return None
    sources = [s for s in (occ.get("sources") or []) if s]
    frm, to, precision = _bound(sources)
    covers = any(covers_scene(describes_date(s)) for s in sources)
    verdict, ledger_note = VERDICTS.get(person_id, (None, None))
    row = {
        "role": role,
        "kind": kind_of(role),
        "as_printed": None,
        "from": frm or None,
        "to": to or None,
        "precision": precision,
        "dated_by": "source_describes_date" if sources else "undated",
        "covers_scene_date": covers,
        "confidence": confidence,
        "sources": sources,
        "claim": None,
        "note": None,
    }
    if covers:
        row["note"] = (
            "THE BOUND IS THE SOURCE'S, NOT THE MAN'S. This role is carried by the card's "
            "1835 occupation block and is dated by what the cited source or sources are "
            "ABOUT, which is why `precision` can be no better than the span they cover. "
            "The span reaches 1835, so this role stands in the scene-date view. The "
            "printing the trade was read off is not on the card and is fetched by T-1254.")
    else:
        row["note"] = (
            "A DATED ROLE THAT DOES NOT REACH THE SCENE DATE (T-0991, withdrawn from the "
            "1835 field by " + GENERATOR + "). No source cited for this trade describes "
            "1835, so it is retained here with the bound its evidence permits and the "
            "1835 compatibility view reads `" + ABSENT + "` instead. "
            "tools/audit_scene_window_trades.py's verdict is `" + (verdict or "unadjudicated")
            + "`" + (": " + ledger_note if ledger_note else "."))
    return row


def later_role(occ: dict) -> dict | None:
    """T-0693's `later_occupation` pointer, as the dated role it has always been."""
    later = occ.get("later_occupation")
    if not isinstance(later, dict):
        return None
    printed = (later.get("value") or "").strip()
    year = str(later.get("describes_date") or "").strip()
    if not printed:
        return None
    return {
        "role": None,
        "kind": "trade",
        "as_printed": printed,
        "from": year or None,
        "to": year or None,
        "precision": "year" if year else "unknown",
        "dated_by": "printing_year" if year else "undated",
        "covers_scene_date": False,
        "confidence": later.get("confidence"),
        "sources": [s for s in (later.get("sources") or []) if s],
        "claim": None,
        "note": (
            "A TRADE PRINTED AGAINST THIS NAME IN A LATER VOLUME, and this row says which "
            "year rather than leaving it to a pointer (T-0693, carried here by " + GENERATOR
            + "). `role` is null because the directory's wording has not been adjudicated "
            "into the closed vocabulary — the printing is what the source gives and the "
            "printing is what is kept. T-1254 is where the controlled term is ruled on. It "
            "is not a claim about " + SCENE_DATE + " and never becomes one: the year is "
            + (year or "not stated") + "."),
    }


def roles_for(person: dict) -> list[dict]:
    occ = person.get("occupation")
    if not isinstance(occ, dict):
        return []
    rows = [r for r in (scene_role(occ, person.get("id")), later_role(occ)) if r]
    rows.sort(key=lambda r: (r["from"] or "9999", r["to"] or "9999",
                             r["role"] or r["as_printed"] or ""))
    return rows


def view(roles: list[dict]) -> tuple[str, list[str]]:
    """The 1835 compatibility view: the claiming roles that cover the scene date."""
    covering = [r for r in roles
                if r["covers_scene_date"] and r["confidence"] in CLAIMING and r["role"]]
    at = [r["role"] for r in covering]
    return (at[0] if at else ABSENT), at


def proposed(households: Path = HOUSEHOLDS) -> dict[str, dict]:
    """Every card this tool would change, keyed by path stem, with the whole new doc."""
    out: dict[str, dict] = {}
    for path in sorted(households.glob("*.json")):
        doc = read_json(path)
        before = dumps(doc)
        for person in doc.get("persons") or []:
            occ = person.get("occupation")
            if not isinstance(occ, dict):
                continue
            roles = roles_for(person)
            value, at = view(roles)
            if not roles:
                # NOTHING TO SAY, SO NOTHING IS WRITTEN. A person with no role evidence
                # carries neither `roles[]` nor the view keys, and the gate reads that
                # absence as the assertion it is: a card with no roles cannot hold a
                # trade in the 1835 field, because a trade in that field IS role
                # evidence and would have produced a row. Writing `roles: []` and an
                # empty view onto the other 1,148 cards would churn the whole residents
                # tree every run to say what their `none_recorded` already says.
                person.pop("roles", None)
                for key in ("derived_from", "roles_at_scene_date"):
                    occ.pop(key, None)
                continue
            person["roles"] = roles
            withdrawn = occ.get("withdrawn_from_scene_date")
            held = (withdrawn.get("value") if isinstance(withdrawn, dict)
                    and withdrawn.get("value") else occ.get("value"))
            if held != value:
                verdict, ledger_note = VERDICTS.get(person.get("id"), ("unadjudicated", None))
                occ["withdrawn_from_scene_date"] = {
                    "value": held,
                    # The grade the trade was held at, which after the first withdrawal
                    # is on the withdrawal and not on the field it was taken off.
                    "confidence": (withdrawn.get("confidence")
                                   if isinstance(withdrawn, dict) and withdrawn.get("value")
                                   else occ.get("confidence")),
                    "verdict": verdict,
                    "ticket": "T-0991",
                    "note": ledger_note or (
                        "No verdict is recorded for this person in "
                        "tools/audit_scene_window_trades.py's table."),
                }
                occ["value"] = value
                occ["confidence"] = "reconstructed"
                occ["note"] = (
                    "NO TRADE IS RECORDED FOR " + SCENE_DATE + ", AND ONE IS RECORDED FOR "
                    "ANOTHER YEAR. The trade this field used to carry — `" + str(held) +
                    "` — is not gone: it stands in `roles[]` with the bound its sources "
                    "permit, and `withdrawn_from_scene_date` above carries the audit's "
                    "verdict for withdrawing it. The 1835 field asserts what the sources "
                    "reach, which here is nothing, because no source cited for the trade "
                    "describes 1835 (T-0837's write rule, T-0872's measurement, T-0991's "
                    "repair, made by " + GENERATOR + ").")
            elif "withdrawn_from_scene_date" in occ:
                # The trade reaches 1835 after all — a source moved, or one was added.
                # The withdrawal is not a record, it is a refusal, and a refusal that no
                # longer fires must leave the card rather than sit on it contradicting
                # the field above.
                occ.pop("withdrawn_from_scene_date")
            occ["derived_from"] = "roles"
            occ["roles_at_scene_date"] = at
        if dumps(doc) != before:
            out[path.name] = doc
    return out


def report() -> int:
    changes = proposed()
    total = sum(len(p.get("roles") or [])
                for doc in changes.values() for p in doc.get("persons") or [])
    withdrawn = [(p.get("id"), (p.get("occupation") or {}).get("withdrawn_from_scene_date"))
                 for doc in changes.values() for p in doc.get("persons") or []
                 if (p.get("occupation") or {}).get("withdrawn_from_scene_date")]
    print(f"{len(changes)} card(s) would change, carrying {total} role(s)")
    if withdrawn:
        print(f"\n{len(withdrawn)} trade(s) withdrawn from the {SCENE_DATE} view:")
        for pid, w in withdrawn:
            print(f"  {pid:<20} {w['value']:<26} {w['verdict']}")
    return 0


def write() -> int:
    changes = proposed()
    for name, doc in changes.items():
        (HOUSEHOLDS / name).write_text(dumps(doc), encoding="utf-8")
    print(f"wrote {len(changes)} card(s) under {HOUSEHOLDS.relative_to(ROOT)}")
    return 0


def check() -> int:
    changes = proposed()
    if not changes:
        n = sum(len(p.get("roles") or []) for path in sorted(HOUSEHOLDS.glob("*.json"))
                for p in read_json(path).get("persons") or [])
        print(f"{n} role(s) stand on the cards, and every one of them re-derives")
        return 0
    print(f"{len(changes)} resident card(s) do not carry what {GENERATOR} derives — run "
          f"--write and commit them.", file=sys.stderr)
    for name in sorted(changes)[:10]:
        print(f"  {name}", file=sys.stderr)
    if len(changes) > 10:
        print(f"  …and {len(changes) - 10} more", file=sys.stderr)
    return 1


def self_test() -> int:
    """The rules above, held over fixtures rather than over the tree."""
    import tempfile
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append(f"{label}: got {got!r}, wanted {want!r}")

    vocab = set((read_json(INDEX).get("vocabulary") or {}).get("occupations") or [])
    holds("every office is in the manifest vocabulary", sorted(OFFICES - vocab), [])
    holds("every profession is in the manifest vocabulary", sorted(PROFESSIONS - vocab), [])
    holds("no role is both an office and a profession", sorted(OFFICES & PROFESSIONS), [])
    holds("an unlisted word is a trade", kind_of("blacksmith"), "trade")
    holds("an office is an office", kind_of("postmaster"), "office")
    holds("a profession is a profession", kind_of("attorney"), "profession")

    holds("a slashed run reads both ends", _ends("1833-11/1835-08"), ("1833-11", "1835-08"))
    holds("a hyphenated year range reads both ends", _ends("1673-1857"), ("1673", "1857"))
    holds("a bare year is its own bound", _ends("1839"), ("1839", "1839"))
    holds("a bare month is its own bound", _ends("1833-11"), ("1833-11", "1833-11"))
    holds("prose names no bound", _ends("nineteenth century"), ("", ""))
    holds("a span is a span", _precision("1833-11", "1835-08"), "source_span")
    holds("one year is year precision", _precision("1839", "1839"), "year")
    holds("one month is month precision", _precision("1833-11", "1833-11"), "month")
    holds("no bound is unknown precision", _precision("", ""), "unknown")

    # THE VIEW, over synthetic roles.
    def role(**kw):
        base = {"role": "cooper", "covers_scene_date": True, "confidence": "attested"}
        base.update(kw)
        return base
    holds("nothing covering leaves the field absent", view([role(covers_scene_date=False)]),
          (ABSENT, []))
    holds("one covering role fills it", view([role()]), ("cooper", ["cooper"]))
    holds("two covering roles are both named",
          view([role(), role(role="grocer")]), ("cooper", ["cooper", "grocer"]))
    holds("a reconstructed role is not a claim",
          view([role(confidence="reconstructed")]), (ABSENT, []))
    holds("a role with no controlled word cannot fill the field",
          view([role(role=None)]), (ABSENT, []))

    with tempfile.TemporaryDirectory() as tmp:
        hh = Path(tmp) / "households"
        hh.mkdir()

        def card(name, pid, occ):
            (hh / f"{name}.json").write_text(json.dumps(
                {"id": name, "persons": [{"id": pid, "name": pid, "occupation": occ}]}),
                encoding="utf-8")

        # Real source ids, so the fixtures read the committed describes_date.
        card("hh_window", "window", {"value": "clothier", "confidence": "attested",
                                     "sources": ["chicago_democrat_1833_1835"],
                                     "note": "held"})
        card("hh_early", "early", {"value": "blacksmith", "confidence": "attested",
                                   "sources": ["chicago_democrat_1833_11_26"],
                                   "note": "held"})
        card("hh_later", "later", {"value": ABSENT, "confidence": "reconstructed",
                                   "note": "held",
                                   "later_occupation": {
                                       "value": "attorney at law", "describes_date": 1843,
                                       "confidence": "attested",
                                       "sources": ["fergus_chicago_directory_1843"]}})
        card("hh_none", "none", {"value": ABSENT, "confidence": "reconstructed",
                                 "note": "held"})
        out = proposed(hh)

        w = out["hh_window.json"]["persons"][0]
        holds("an in-window trade keeps the field", w["occupation"]["value"], "clothier")
        holds("…and names itself in the scene-date list",
              w["occupation"]["roles_at_scene_date"], ["clothier"])
        holds("…and its note is not rewritten", w["occupation"]["note"], "held")
        holds("…and it carries one role", len(w["roles"]), 1)
        holds("…bounded by the run of the paper",
              (w["roles"][0]["from"], w["roles"][0]["to"]), ("1833-11", "1835-08"))

        e = out["hh_early.json"]["persons"][0]
        holds("a pre-scene trade leaves the field", e["occupation"]["value"], ABSENT)
        holds("…at reconstructed", e["occupation"]["confidence"], "reconstructed")
        holds("…and the trade is not lost", e["roles"][0]["role"], "blacksmith")
        holds("…and the withdrawal states what it withdrew",
              e["occupation"]["withdrawn_from_scene_date"]["value"], "blacksmith")
        holds("…and the role does not reach the scene",
              e["roles"][0]["covers_scene_date"], False)

        lt = out["hh_later.json"]["persons"][0]
        holds("a later trade becomes a dated role", lt["roles"][0]["as_printed"],
              "attorney at law")
        holds("…dated by the year it was printed", lt["roles"][0]["from"], "1843")
        holds("…with no controlled word yet", lt["roles"][0]["role"], None)
        holds("…and it does not reach the scene date", lt["roles"][0]["covers_scene_date"],
              False)
        holds("…and the 1835 field stays absent", lt["occupation"]["value"], ABSENT)

        holds("a card with no role evidence gains no roles[]",
              "roles" in (out.get("hh_none.json") or {"persons": [{}]})["persons"][0], False)

        # IDEMPOTENCE — the gate's whole claim. Write once, and there is nothing left.
        for name, doc in out.items():
            (hh / name).write_text(dumps(doc), encoding="utf-8")
        holds("a second derivation proposes nothing", sorted(proposed(hh)), [])

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    print(f"self-test: {35 - len(failures)}/35 assertions hold")
    return 1 if failures else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--report"
    sys.exit({"--report": report, "--write": write, "--check": check,
              "--self-test": self_test}.get(arg, report)())
