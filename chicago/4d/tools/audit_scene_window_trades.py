#!/usr/bin/env python3
"""Every 1835 trade STANDING on a card whose own sources describe another year (T-0872).

    python3 tools/audit_scene_window_trades.py            the population, read out
    python3 tools/audit_scene_window_trades.py --write    regenerate the adjudication
    python3 tools/audit_scene_window_trades.py --check    it re-derives, and it has not grown
    python3 tools/audit_scene_window_trades.py --self-test the rules below, held over data

WHY THIS EXISTS, AND WHY T-0837's GATE IS NOT IT. T-0837 gated the SYNTHESIZER: a trade
may only be written into the 1835 `occupation` field out of a source whose own
`describes_date` covers 1835. That is a WRITE gate, and it has two blind spots this one
covers.

  1. IT CANNOT SEE WHAT WAS ALREADY COMMITTED. It stops the next promotion and leaves
     standing what earlier passes landed. Nine people are standing on one right now.

  2. ITS REFUSAL IS SUPPRESSED ON EXACTLY THOSE NINE. The synthesizer declines to
     overwrite a filled field before it ever reaches the date test, so the refusal branch
     that would name them never fires. The defect is invisible from inside the tool whose
     rule it breaks — which is why it went a month unmeasured and why the count in
     T-0872's table (eight, on 2026-09-06) was already wrong four days later.

WHAT IT ASSERTS, and it is one sentence: a person's 1835 `occupation` may carry a trade at
`attested`, `documented` or `inferred` only if at least one of the sources cited on that
occupation block has a `describes_date` whose span contains 1835. It asserts NOTHING about
what the right repair is — see the ledger's `verdict` field, and T-0991.

THE DIRECTION IS NOT THE POINT, and the ticket's title reads as though it were. A trade
printed in Fergus' directory of 1839 and a trade printed in the Chicago Democrat of 26
November 1833 fail this for the same reason: neither volume is about July 1835. They are
not the same REPAIR — T-0693's `later_occupation` pointer holds a directory of 1839 and
cannot hold an issue of 1833, which is what a run reading only the title would try — but
they are the same MEASUREMENT, and this tool makes it.

THE BASELINE MAY ONLY FALL. `--check` re-derives the population and compares it to the
committed ledger. A row that disappears is a repair and the ledger is regenerated with it;
a row that appears is a regression and fails the gate, which is the half T-0837 cannot do
from the write side.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
SOURCES = DATA / "sources"
LEDGER = DATA / "research" / "residents" / "scene_window_trade_audit.json"

SCENE_YEAR = 1835
SCENE_DATE = "1835-07-01"
GENERATOR = "tools/audit_scene_window_trades.py"
TICKET = "T-0872"
ABSENT = "none_recorded"

# The grades that make the field a CLAIM. `reconstructed` is this dataset's word for a
# figure the reconstruction supplies rather than a source, and the synthesizer's own
# overwrite guard already treats it as an empty field, so a trade held at that grade is
# not asserting a documented 1835 fact and is not in this population.
CLAIMING = ("attested", "documented", "inferred")

_YEARS = re.compile(r"1[6-9]\d{2}")


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


def covers_scene(spanned: str) -> bool:
    """Does this `describes_date` name a span the scene year falls inside?

    A source with no `describes_date`, or one as vague as "nineteenth century", names no
    year at all and cannot carry the claim.  Same reading as
    `synthesize_resident_research.describes_scene`, deliberately duplicated rather than
    imported: that module runs a whole synthesis on import cost, and the two must be able
    to disagree loudly rather than quietly share a bug.
    """
    years = [int(y) for y in _YEARS.findall(spanned)]
    return bool(years) and min(years) <= SCENE_YEAR <= max(years)


def offenders(households: Path = HOUSEHOLDS) -> list[dict]:
    """Every claiming 1835 trade with no cited source about 1835, in file order."""
    out = []
    for path in sorted(households.glob("*.json")):
        doc = read_json(path)
        for person in doc.get("persons") or []:
            occ = person.get("occupation")
            if not isinstance(occ, dict):
                continue
            trade = occ.get("value")
            if not trade or trade == ABSENT:
                continue
            if occ.get("confidence") not in CLAIMING:
                continue
            cited = [s for s in (occ.get("sources") or []) if s]
            if any(covers_scene(describes_date(s)) for s in cited):
                continue
            out.append({
                "household": path.stem,
                "person_id": person.get("id"),
                "name": person.get("name"),
                "trade": trade,
                "confidence": occ.get("confidence"),
                "cited": [{"source_id": s, "describes_date": describes_date(s) or None}
                          for s in cited] or None,
            })
    return out


# The adjudication a run has already made on a row, keyed by person.  It is carried
# forward by `--write` so a repair's reasoning is not lost when the ledger regenerates,
# and it is the only hand-written thing in the file.
VERDICTS = {
    "elston_daniel": ("pre_scene_printing", 
        "Soap and candle manufactory, Chicago Democrat, 26 November 1833. The corpus last "
        "prints the manufactory at the issue of 2 July 1834 (business_daniel_elston_co, "
        "business_chicago_soap_and_candle_manufactory); nothing inside the scene window "
        "prints the trade."),
    "goss_o": ("dissolved_before_the_scene",
        "'Goss & Cobb, saddle and harness makers', Chicago Democrat, 26 November 1833 — and "
        "the Chicago American of 8 June 1835 prints the firm's DISSOLUTION, over copy dated "
        "18 February 1835, four months before the scene date. The newspaper register reads "
        "business_goss_cobb as `present_at_scene_date: false` on that notice while the card "
        "goes on asserting the trade at `attested`. The sharpest row in the population."),
    "harmon_charles_l": ("firm_in_window_trade_not_printed",
        "'C. & I. HARMON', dry goods, crockery, hardware and groceries, Chicago Democrat, 26 "
        "November 1833. A Harmon dry-goods firm does stand inside the window — the Democrat "
        "of 17 June 1835 prints 'Messrs. Harmon, Loomis & Co.' — but that notice prints no "
        "trade, and tying the 1833 brothers to the 1835 firm is reasoning rather than a "
        "printing. Both halves would have to be written down before the citation could move."),
    "harmon_isaac_d": ("firm_in_window_trade_not_printed",
        "The other half of C. & I. Harmon, and the same reading. The Democrat of 5 August "
        "1835 prints 'Isaac Harmon, esq.' winding up Bristol, Vale & Hogue — the man inside "
        "the window, without his trade."),
    "hathaway_joshua": ("trade_read_from_a_map",
        "Cited to `hathaway_1834`, which is a MAP of 1834 — the extent envelope Kinzie "
        "commissioned — carrying his authorship. A surveyor's name in a cartouche is "
        "evidence that he drew the map; `forwarding_and_commission` is not read off it at "
        "all. The one row in this population whose defect is the READING and not the date."),
    "jones_benjamin": ("pre_scene_printing",
        "A grocery and provision store, Chicago Democrat, 26 November 1833. The register's "
        "later readings of this man print `forwarding_and_commission` (21 January to 16 July "
        "1834), not `grocer`, and neither reaches the scene window."),
    "kimball_walter": ("pre_scene_printing",
        "His own signed 'New Store' advertisement, Chicago Democrat, 26 November 1833. The "
        "corpus last prints the store at the issue of 4 June 1834 (business_w_kimball); the "
        "paper's later readings of the man give `grocer`, to 3 December 1834. Nothing inside "
        "the window."),
    "mason_matthias": ("pre_scene_printing",
        "'Matthias Mason & Co., blacksmiths', Chicago Democrat, 26 November 1833. The MAN is "
        "printed in the paper to 20 May 1835, inside the window; the FIRM is last printed 10 "
        "December 1834, outside it. A card may not read the second off the first."),
}

DOC = (
    "THE STANDING POPULATION T-0837's WRITE GATE CANNOT SEE. Each row is a person whose "
    "1835 `occupation` carries a trade at a claiming grade while no source cited on that "
    "block has a `describes_date` covering 1835. Derived by `" + GENERATOR + "`; do not "
    "hand-edit anything but the verdicts, which live in the generator beside the rule they "
    "adjudicate. A row leaving this file is a repair. A row arriving is a regression, and "
    "`--check` refuses it."
)


def ledger(rows: list[dict]) -> dict:
    for row in rows:
        verdict, note = VERDICTS.get(row["person_id"], ("unadjudicated", None))
        row["verdict"] = verdict
        row["note"] = note
    return {
        "schema": "scene_window_trade_audit/1",
        "generated_by": GENERATOR,
        "ticket": TICKET,
        "scene_date": SCENE_DATE,
        "_doc": DOC,
        "rule": ("persons[].occupation.value at a grade in " + "/".join(CLAIMING) +
                 " requires at least one cited source whose describes_date spans "
                 f"{SCENE_YEAR}"),
        "count": len(rows),
        "rows": rows,
    }


def report() -> int:
    rows = offenders()
    if not rows:
        print("no standing 1835 trade is cited to a source about another year")
        return 0
    print(f"{len(rows)} standing 1835 trade(s) cited to no source about {SCENE_YEAR}:\n")
    for row in rows:
        cited = ", ".join(f"{c['source_id']} ({c['describes_date'] or 'no describes_date'})"
                          for c in row["cited"] or []) or "no sources at all"
        verdict = VERDICTS.get(row["person_id"], ("unadjudicated", None))[0]
        print(f"  {row['person_id']:<20} {row['trade']:<26} {row['confidence']:<10} {verdict}")
        print(f"  {'':<20} {cited}")
    return 0


def write() -> int:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(dumps(ledger(offenders())), encoding="utf-8")
    print(f"wrote {LEDGER.relative_to(ROOT)}")
    return 0


def check() -> int:
    if not LEDGER.exists():
        print(f"MISSING {LEDGER.relative_to(ROOT)} — run --write", file=sys.stderr)
        return 1
    held = read_json(LEDGER)
    live = ledger(offenders())
    was = {r["person_id"] for r in held.get("rows") or []}
    now = {r["person_id"] for r in live["rows"]}
    grew = sorted(now - was)
    if grew:
        print("A TRADE CITED TO NO 1835 SOURCE HAS APPEARED ON A CARD, and T-0837's write "
              "gate did not stop it:", file=sys.stderr)
        for pid in grew:
            row = next(r for r in live["rows"] if r["person_id"] == pid)
            print(f"  {pid}: {row['trade']} at {row['confidence']}, cited "
                  f"{[c['source_id'] for c in row['cited'] or []]}", file=sys.stderr)
        return 1
    if dumps(live) != LEDGER.read_text(encoding="utf-8"):
        shrank = sorted(was - now)
        print(f"{LEDGER.relative_to(ROOT)} does not re-derive — run --write and commit it.",
              file=sys.stderr)
        if shrank:
            print(f"  repaired since it was written: {', '.join(shrank)}", file=sys.stderr)
        return 1
    print(f"{live['count']} standing row(s), and the ledger re-derives")
    return 0


def self_test() -> int:
    """The rules above, held over synthetic cards rather than over the tree."""
    import tempfile
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append(f"{label}: got {got!r}, wanted {want!r}")

    # THE DATE TEST, in both directions and on the vague case.
    holds("1839 does not cover the scene", covers_scene("1839"), False)
    holds("1833-11 does not cover the scene", covers_scene("1833-11"), False)
    holds("the run of the paper covers it", covers_scene("1833-11/1835-08"), True)
    holds("a bare 1835 covers it", covers_scene("1835"), True)
    holds("'nineteenth century' names no year", covers_scene("nineteenth century"), False)
    holds("an absent describes_date names no year", covers_scene(""), False)

    with tempfile.TemporaryDirectory() as tmp:
        hh = Path(tmp) / "households"
        hh.mkdir()

        def card(name, person_id, occ):
            (hh / f"{name}.json").write_text(json.dumps(
                {"id": name, "persons": [{"id": person_id, "name": person_id,
                                          "occupation": occ}]}), encoding="utf-8")

        # Real source ids, so the test reads the committed describes_date rather than a
        # fixture that could drift away from it.
        card("hh_late", "late", {"value": "attorney", "confidence": "attested",
                                 "sources": ["fergus_chicago_directory_1839"]})
        card("hh_early", "early", {"value": "blacksmith", "confidence": "attested",
                                   "sources": ["chicago_democrat_1833_11_26"]})
        card("hh_window", "window", {"value": "clothier", "confidence": "attested",
                                     "sources": ["chicago_democrat_1833_1835"]})
        card("hh_mixed", "mixed", {"value": "grocer", "confidence": "attested",
                                   "sources": ["chicago_democrat_1833_11_26",
                                               "chicago_democrat_1833_1835"]})
        card("hh_absent", "absent", {"value": ABSENT, "confidence": "reconstructed",
                                     "sources": []})
        card("hh_reconstructed", "recon", {"value": "cooper", "confidence": "reconstructed",
                                           "sources": ["fergus_chicago_directory_1839"]})
        card("hh_unsourced", "unsourced", {"value": "cooper", "confidence": "attested",
                                           "sources": []})
        card("hh_noblock", "noblock", {})
        found = {r["person_id"] for r in offenders(hh)}

    holds("a 1839 directory is refused", "late" in found, True)
    holds("an 1833 issue is refused too", "early" in found, True)
    holds("the run of the paper passes", "window" in found, False)
    holds("one in-window source among several is enough", "mixed" in found, False)
    holds("none_recorded is not a claim", "absent" in found, False)
    holds("a reconstructed trade is not a claim", "recon" in found, False)
    holds("a claim with no sources at all is refused", "unsourced" in found, True)
    holds("an occupation block that is not a dict is skipped", "noblock" in found, False)

    for line in failures:
        print(f"FAIL {line}", file=sys.stderr)
    print(f"self-test: {14 - len(failures)}/14 assertions hold")
    return 1 if failures else 0


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "--report"
    sys.exit({"--report": report, "--write": write, "--check": check,
              "--self-test": self_test}.get(arg, report)())
