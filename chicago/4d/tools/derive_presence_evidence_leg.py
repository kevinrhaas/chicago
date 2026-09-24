#!/usr/bin/env python3
"""The dated evidence leg under every uncertain presence, as a field (T-1144, acc. 9).

    python3 tools/derive_presence_evidence_leg.py --write      write the legs
    python3 tools/derive_presence_evidence_leg.py --check      re-derive and diff
    python3 tools/derive_presence_evidence_leg.py --report     the legs, counted
    python3 tools/derive_presence_evidence_leg.py --self-test  the rules, over fixtures

WHY THE FIELD EXISTS. 820 households stand `present_on_scene_date: uncertain` — the
layer holds the person and no source follows them to 1 July 1835. That verdict is a
finding rather than a gap, and the thing that makes it a finding is a DATE: the last
day the corpus can still see this person. T-1159 classifies those presences by that
date and T-1172 re-admits them against it, so the date is load-bearing for two
tickets — and until now it lived only in the prose of the presence note, where
`tools/export_borderline_roster.py` reached for it with a regular expression. A second
representation of the same fact is the thing that drifts, and a regex over prose is
the weakest representation there is: it read `1835-05-20` out of one note and nothing
at all out of the 780 whose note names no date, falling back to the arrival bound.

So the leg is derived HERE, from the card's own structured evidence, written onto the
card, and read from there by everybody. T-1144 acceptance 9 asks for exactly that.

WHAT THE RULE IS, AND WHERE IT REFUSES TO GUESS.

Every candidate comes from a block the card already carries, never from prose:

    press_evidence · civic_evidence · book_evidence · church_evidence ·
    census_evidence · profile_facts      → `describes_date`, with `locator`,
                                           `record_id` and `source` beside it
    persons[].letter_list_returns[]      → the returns the post office printed,
                                           used only for a date no block carries
    persons[].roles[]                    → `from`/`to`, which is the SOURCE's span
    arrival.value (`not_later_than`)     → a bound on arrival, not an appearance

Those four are TIERS, in that order, and the first tier with a candidate wins outright:

  1. `sighting` — a dated reading of this person in a record. The strongest thing the
     card holds, and the only kind that is an APPEARANCE.
  2. `source_span` — a role dated by what its sources are about. The role's own note
     says the bound is the source's and not the man's, so a span may not outrank a
     sighting even when it reaches further: a printing that covers 1833-11 to 1835-08
     is not a sighting in August.
  3. `arrival_bound` — the card holds one date and it is a bound on when the person
     was already here. It is carried as the leg because it is the only date there is,
     and `leg` says which kind it is so no reader can mistake it for a sighting.

Within the winning tier the candidate with the greatest `reaches` (the latest day its
reading can mean) wins; ties go to the narrower precision, then to the family order
above, then to the record id — deterministic, and none of it depends on dict order.

A candidate whose EARLIEST possible day falls after 1 July 1835 is not admitted at
all: an 1843 directory entry is a later appearance, which is T-1159's class R5 and not
this field's business. When that is all a card holds, the leg is `null` and the note
says a later record names this person and names its date.

WHAT IS NOT WRITTEN. A household whose presence is not `uncertain` carries no leg, and
one that stops being uncertain loses it — the field is the evidence under a verdict,
so it may not outlive the verdict. `--check` holds both halves.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
GENERATOR = "tools/derive_presence_evidence_leg.py"
SCENE_DATE = "1835-07-01"
FIELD = "last_dated_appearance"

# The reading families, in the order that breaks a tie between two equal dates.
SIGHTING_FAMILIES = ("press_evidence", "civic_evidence", "book_evidence",
                     "church_evidence", "census_evidence", "profile_facts",
                     "biographical_evidence")
PRECISION_RANK = {"day": 0, "month": 1, "year": 2}
TIERS = ("sighting", "source_span", "arrival_bound")


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def bounds(value) -> tuple[str, str, str] | None:
    """(earliest day, latest day, precision) of an ISO date, or None if unreadable.

    A reading printed as a year is a claim about the year and not about 1 January:
    its bounds are the whole year, which is what lets the rule above say whether it
    can fall at or before the scene date.
    """
    if not isinstance(value, str):
        return None
    text = value.strip()
    parts = text.split("-")
    if len(parts) == 3 and all(p.isdigit() for p in parts) and len(parts[0]) == 4:
        return text, text, "day"
    if len(parts) == 2 and all(p.isdigit() for p in parts) and len(parts[0]) == 4:
        month = int(parts[1])
        if not 1 <= month <= 12:
            return None
        last = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1]
        return f"{text}-01", f"{text}-{last:02d}", "month"
    if len(parts) == 1 and text.isdigit() and len(text) == 4:
        return f"{text}-01-01", f"{text}-12-31", "year"
    return None


def _blocks(person: dict, family: str) -> list[dict]:
    """A family as a list of blocks, whichever of the two shapes the card uses."""
    value = person.get(family)
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [block for block in value if isinstance(block, dict)]
    return []


def _source_list(block: dict) -> list[str]:
    for key in ("sources", "source"):
        value = block.get(key)
        if isinstance(value, list):
            return sorted(str(item) for item in value)
        if isinstance(value, str):
            return [value]
    return []


def candidates(doc: dict) -> list[dict]:
    """Every dated leg the card offers, tier and bounds attached, unranked."""
    out = []
    for person in doc.get("persons") or []:
        pid = str(person.get("id") or "")
        for family in SIGHTING_FAMILIES:
            for block in _blocks(person, family):
                read = bounds(block.get("describes_date"))
                if not read:
                    continue
                earliest, latest, precision = read
                out.append({
                    "tier": "sighting", "family": family, "person": pid,
                    "as_read": str(block.get("describes_date")),
                    "earliest": earliest, "reaches": latest, "precision": precision,
                    "record": block.get("record_id") or block.get("locator"),
                    "sources": _source_list(block),
                })
        for value in person.get("letter_list_returns") or []:
            read = bounds(value)
            if not read:
                continue
            earliest, latest, precision = read
            out.append({
                "tier": "sighting", "family": "letter_list_returns", "person": pid,
                "as_read": str(value), "earliest": earliest, "reaches": latest,
                "precision": precision, "record": None,
                # A RETURN CARRIES NO CITATION OF ITS OWN. `letter_list_returns` is a
                # list of dates and nothing else, so there is no block to cite and the
                # person's `sources` may name several corpora of which only one printed
                # the return. Naming all of them would attribute the reading to sources
                # that did not make it, so this candidate cites none and the note says
                # where the corpus is named instead.
                "sources": [],
            })
        for role in person.get("roles") or []:
            if not isinstance(role, dict):
                continue
            first = bounds(role.get("from"))
            last = bounds(role.get("to"))
            if not (first and last):
                continue
            out.append({
                "tier": "source_span", "family": "roles", "person": pid,
                "as_read": f"{role.get('from')}/{role.get('to')}",
                "earliest": first[0], "reaches": last[1],
                "precision": str(role.get("precision") or "source_span"),
                "record": role.get("claim"),
                "sources": sorted(str(s) for s in role.get("sources") or []),
            })
    arrival = doc.get("arrival")
    if isinstance(arrival, dict):
        read = bounds(arrival.get("value"))
        if read:
            earliest, latest, precision = read
            out.append({
                "tier": "arrival_bound", "family": "arrival", "person": None,
                "as_read": str(arrival.get("value")),
                "earliest": earliest, "reaches": latest, "precision": precision,
                "record": None,
                "sources": sorted(str(s) for s in arrival.get("sources") or []),
            })
    return out


def _order(row: dict) -> tuple:
    family = row["family"] if row["family"] in SIGHTING_FAMILIES else "zz"
    return (row["reaches"], -PRECISION_RANK.get(row["precision"], 9),
            -(len(SIGHTING_FAMILIES) if family == "zz"
              else SIGHTING_FAMILIES.index(family)),
            str(row["record"] or ""), row["person"] or "")


def days_between(start: str, end: str) -> int:
    import datetime
    fmt = "%Y-%m-%d"
    return (datetime.datetime.strptime(end, fmt)
            - datetime.datetime.strptime(start, fmt)).days


LEG_WORDS = {
    "sighting": "A DATED READING OF THIS PERSON, AND THE LAST ONE THE CORPUS HOLDS.",
    "source_span": ("NO SIGHTING, SO THE LEG IS A SOURCE'S SPAN. The card holds no "
                    "dated reading of this person at or before the scene date; the "
                    "date here is the far end of what a cited source COVERS, which "
                    "the role's own note calls the source's bound and not the man's."),
    "arrival_bound": ("NO SIGHTING AND NO SPAN, SO THE LEG IS THE ARRIVAL BOUND. It "
                      "is the only date this card holds: the day by which a record "
                      "already has this person at Chicago, not a day they were seen."),
}


def leg_for(doc: dict) -> dict:
    """The one leg this card's evidence supports, written as the field it becomes."""
    rows = [row for row in candidates(doc) if row["earliest"] <= SCENE_DATE]
    later = sorted((row for row in candidates(doc) if row["earliest"] > SCENE_DATE),
                   key=lambda row: row["earliest"])
    if not rows:
        if later:
            note = ("NO DATED EVIDENCE AT OR BEFORE " + SCENE_DATE + ". The earliest "
                    "date this card carries is " + later[0]["as_read"] + ", which is "
                    "after the scene, so it is a later appearance rather than the leg "
                    "under this verdict — T-1159 class R5 is where a later record is "
                    "back-projected, and it is not done here.")
        else:
            note = ("NO DATED EVIDENCE ON THIS CARD. The sources name the person and "
                    "date nothing about them, so the presence is uncertain with no "
                    "date to be uncertain from. A reading that dates one of the "
                    "blocks above fills this in by re-running " + GENERATOR + ".")
        return {"as_read": None, "precision": None, "reaches": None,
                "includes_scene_date": False, "days_before_scene_date": None,
                "leg": "none", "person": None, "record": None, "sources": [],
                "note": note}

    for tier in TIERS:
        tiered = [row for row in rows if row["tier"] == tier]
        if tiered:
            break
    best = max(tiered, key=_order)
    # THE READING'S OWN WINDOW IS NOT SHORTENED TO THE SCENE DATE. A source that
    # describes `1835` reaches 1835-12-31, and clipping that to 1835-07-01 would make
    # the card say the person was still visible ON the scene date — a confidence
    # upgrade by arithmetic, and the exact overstatement this field exists to avoid.
    # So `reaches` is what the reading can mean, `includes_scene_date` says when that
    # window covers the day, and the gap is stated only when the window closes before
    # it. A reading whose window covers the scene date pins no last sighting before it,
    # which is one of the reasons a presence stands `uncertain`.
    reaches = best["reaches"]
    covers = reaches >= SCENE_DATE
    gap = None if covers else days_between(reaches, SCENE_DATE)
    where = (best["family"] if best["family"] != "roles"
             else "roles[] (" + best["precision"] + ")")
    uncited = ("" if best["family"] != "letter_list_returns" else
               " A RETURN IS A DATE AND NOT A CITATION: `letter_list_returns` carries no "
               "source per return, so this leg cites none and the corpus that printed it "
               "is named in the person's own `sources`.")
    note = (LEG_WORDS[best["tier"]] + " Read from `" + where + "` as `"
            + best["as_read"] + "`, which reaches " + reaches + " — "
            + (str(gap) + " day(s) short of " + SCENE_DATE if gap is not None
               else "a window that covers " + SCENE_DATE + " itself, so it pins no "
               "last sighting before the day and cannot be read as one")
            + "." + uncited + " THE FIELD IS THE "
            "EVIDENCE UNDER THE "
            "VERDICT, not a new claim: nothing here moves the presence off `uncertain`, "
            "and T-1159 and T-1172 classify this household by this date instead of "
            "reading it out of the prose (T-1144 acceptance 9).")
    return {
        # ONE DATE FIELD, NOT TWO. An earlier draft carried `date` beside `as_read` —
        # the same string for a sighting and a bound, and null for a span — which is a
        # second representation of one fact and a figure a reader has to reconcile.
        # `leg` already says which kind of date this is, so `as_read` is the date.
        "as_read": best["as_read"],
        "precision": best["precision"],
        "reaches": reaches,
        "includes_scene_date": covers,
        "days_before_scene_date": gap,
        "leg": best["tier"],
        "person": best["person"],
        "record": best["record"],
        "sources": best["sources"],
        "note": note,
    }


def _with_leg(presence: dict, leg: dict | None) -> dict:
    """The presence block with the leg in its one conventional slot, after `sources`."""
    rebuilt = {}
    for key, value in presence.items():
        if key == FIELD:
            continue
        rebuilt[key] = value
        if key == "sources" and leg is not None:
            rebuilt[FIELD] = leg
    if leg is not None and FIELD not in rebuilt:
        rebuilt[FIELD] = leg
    return rebuilt


def proposed(households: pathlib.Path = HOUSEHOLDS) -> dict[str, dict]:
    """Every card this tool would change, keyed by file name, with the whole new doc."""
    out: dict[str, dict] = {}
    for path in sorted(households.glob("*.json")):
        doc = read_json(path)
        presence = doc.get("present_on_scene_date")
        if not isinstance(presence, dict):
            continue
        before = dumps(doc)
        leg = leg_for(doc) if presence.get("value") == "uncertain" else None
        doc["present_on_scene_date"] = _with_leg(presence, leg)
        if dumps(doc) != before:
            out[path.name] = doc
    return out


def committed(households: pathlib.Path = HOUSEHOLDS) -> list[tuple[str, dict, dict]]:
    """(file, presence, leg) for every uncertain household that carries a leg."""
    rows = []
    for path in sorted(households.glob("*.json")):
        doc = read_json(path)
        presence = doc.get("present_on_scene_date")
        if isinstance(presence, dict) and presence.get("value") == "uncertain":
            rows.append((path.name, presence, presence.get(FIELD) or {}))
    return rows


def write() -> int:
    changes = proposed()
    for name, doc in changes.items():
        (HOUSEHOLDS / name).write_text(dumps(doc), encoding="utf-8")
    print(f"wrote {len(changes)} card(s) under {HOUSEHOLDS.relative_to(ROOT)}")
    return 0


def report() -> int:
    import collections
    rows = committed()
    tiers = collections.Counter(leg.get("leg") for _, _, leg in rows)
    families = collections.Counter()
    gaps = []
    covering = 0
    for _, _, leg in rows:
        if leg.get("includes_scene_date"):
            covering += 1
        elif leg.get("days_before_scene_date") is not None:
            gaps.append(leg["days_before_scene_date"])
    print(f"{len(rows)} uncertain presence(s); {sum(1 for _, _, leg in rows if leg)} "
          f"carry a dated evidence leg")
    for tier, count in tiers.most_common():
        print(f"   {count:5d}  {tier}")
    if gaps:
        gaps.sort()
        print(f"   the leg falls {gaps[0]}-{gaps[-1]} day(s) before {SCENE_DATE}; "
              f"median {gaps[len(gaps) // 2]}")
    print(f"   {covering} leg(s) read a window that covers {SCENE_DATE}, so they pin "
          f"no last sighting before it")
    del families
    return 0


def check() -> int:
    changes = proposed()
    if not changes:
        rows = committed()
        dated = sum(1 for _, _, leg in rows if leg.get("reaches"))
        print(f"   OK: {len(rows)} uncertain presence(s) carry the leg this pass "
              f"derives, {dated} of them dated")
        return 0
    print(f"   {len(changes)} household card(s) do not carry the presence leg "
          f"{GENERATOR} derives — run --write and commit them.", file=sys.stderr)
    for name in sorted(changes)[:10]:
        print(f"     {name}", file=sys.stderr)
    if len(changes) > 10:
        print(f"     …and {len(changes) - 10} more", file=sys.stderr)
    return 1


def self_test() -> int:
    """The rules above, held over fixtures rather than over the tree."""
    import tempfile
    failures = []

    def holds(label, got, want):
        if got != want:
            failures.append(f"{label}: got {got!r}, wanted {want!r}")

    holds("a year reads as the whole year", bounds("1834"),
          ("1834-01-01", "1834-12-31", "year"))
    holds("a month reads to its last day", bounds("1835-02"),
          ("1835-02-01", "1835-02-29", "month"))
    holds("a day reads as itself", bounds("1835-05-20"),
          ("1835-05-20", "1835-05-20", "day"))
    holds("prose is not a date", bounds("April 8, 1835"), None)
    holds("a role's own label is not a date", bounds("printing_year"), None)

    def card(**kw):
        doc = {"id": "hh_x", "arrival": kw.get("arrival"),
               "present_on_scene_date": {"value": kw.get("presence", "uncertain"),
                                         "confidence": "inferred",
                                         "sources": ["s1"], "note": "n"},
               "persons": [dict({"id": "p1"}, **kw.get("person", {}))]}
        if doc["arrival"] is None:
            del doc["arrival"]
        return doc

    sighting = card(person={"press_evidence": [
        {"describes_date": "1835-05-20", "record_id": "r1",
         "source": "chicago_democrat_1833_1835"}]})
    leg = leg_for(sighting)
    holds("a dated reading is a sighting", leg["leg"], "sighting")
    holds("…and it carries the date it was read as", leg["as_read"], "1835-05-20")
    holds("…and the days it falls short", leg["days_before_scene_date"], 42)
    holds("…and the record it came from", leg["record"], "r1")

    # A RETURN IS A DATE AND NOT A CITATION. The person's `sources` may name several
    # corpora of which only one printed the return, so attributing the reading to all
    # of them would cite sources that did not make it.
    returns = card(person={"letter_list_returns": ["1834-04-01"],
                           "sources": ["chicago_democrat_1833_1835",
                                       "second_presbyterian_chicago_1892"]})
    from_return = leg_for(returns)
    holds("a return cites no source of its own", from_return["sources"], [])
    holds("…and the note says where the corpus is named",
          "`sources`" in from_return["note"], True)

    # A SPAN MAY NOT OUTRANK A SIGHTING even when it reaches further. This is the
    # assertion the file's tier rule exists for: 1835-08 is later than 1835-05-20,
    # and the role's own note says that bound belongs to the source.
    both = card(person={
        "press_evidence": [{"describes_date": "1835-05-20", "record_id": "r1",
                            "source": "s"}],
        "roles": [{"from": "1833-11", "to": "1835-08", "precision": "source_span",
                   "sources": ["s"]}]})
    holds("a source span does not outrank a sighting", leg_for(both)["leg"], "sighting")
    holds("…and the sighting's date is the one written",
          leg_for(both)["reaches"], "1835-05-20")

    span_only = card(person={"roles": [
        {"from": "1833-11", "to": "1835-08", "precision": "source_span",
         "sources": ["s"]}]})
    span = leg_for(span_only)
    holds("a span alone is the leg, and reaches what the source covers",
          (span["leg"], span["reaches"]), ("source_span", "1835-08-31"))
    holds("…and a span has no field a reader could take for a sighting date",
          "date" in span, False)
    holds("…and a window over the scene date states no gap",
          (span["includes_scene_date"], span["days_before_scene_date"]), (True, None))

    # A COARSE READING IS NOT SHORTENED TO THE SCENE DATE. `1835` could be either half
    # of the year, and clipping it to 1835-07-01 would claim the later half.
    coarse = card(person={"press_evidence": [
        {"describes_date": "1835", "record_id": "r2", "source": "s"}]})
    year = leg_for(coarse)
    holds("a year that covers the scene date is not clipped to it",
          (year["as_read"], year["reaches"]), ("1835", "1835-12-31"))
    holds("…and it pins no gap", year["days_before_scene_date"], None)
    holds("…and the note says it cannot be read as a sighting on the day",
          "pins no last sighting" in year["note"], True)

    bound_only = card(arrival={"value": "1834-12-31", "precision": "not_later_than",
                               "sources": ["st_cyr_register_ichr_v4"]})
    holds("an arrival bound is the weakest leg and says so",
          leg_for(bound_only)["leg"], "arrival_bound")

    later = card(person={"press_evidence": [
        {"describes_date": "1843", "record_id": "r9", "source": "s"}]})
    after = leg_for(later)
    holds("a post-scene reading is not admitted as the leg", after["leg"], "none")
    holds("…and the note names its date", "1843" in after["note"], True)
    holds("a card with no dated block gets no date", leg_for(card())["leg"], "none")

    # THE FIELD MAY NOT OUTLIVE THE VERDICT, and the two halves of --check are what
    # prove it: a leg is written under `uncertain`, and removed when the presence moves.
    with tempfile.TemporaryDirectory() as tmp:
        hh = pathlib.Path(tmp)
        (hh / "hh_a.json").write_text(dumps(sighting), encoding="utf-8")
        moved = card(presence="present", person={"press_evidence": [
            {"describes_date": "1835-05-20", "record_id": "r1", "source": "s"}]})
        moved["present_on_scene_date"][FIELD] = leg
        (hh / "hh_b.json").write_text(dumps(moved), encoding="utf-8")
        changes = proposed(hh)
        holds("an uncertain card with no leg is proposed a leg",
              "hh_a.json" in changes, True)
        holds("…in the slot after `sources`",
              list(changes["hh_a.json"]["present_on_scene_date"]),
              ["value", "confidence", "sources", FIELD, "note"])
        holds("a card that stopped being uncertain has its leg taken away",
              FIELD in changes["hh_b.json"]["present_on_scene_date"], False)
        for name, doc in changes.items():
            (hh / name).write_text(dumps(doc), encoding="utf-8")
        holds("…and the second pass is a fixed point", proposed(hh), {})

    for line in failures:
        print(f"   FAIL {line}")
    if failures:
        print(f"   {len(failures)} assertion(s) do not hold")
        return 1
    print("   OK: every rule of the presence leg holds over its fixtures")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write the legs onto the cards")
    ap.add_argument("--check", action="store_true", help="re-derive and report drift")
    ap.add_argument("--report", action="store_true", help="the legs, counted")
    ap.add_argument("--self-test", action="store_true", help="the rules, over fixtures")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    if args.check:
        return check()
    if args.write:
        return write()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
