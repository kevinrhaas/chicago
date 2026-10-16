#!/usr/bin/env python3
"""Gate the arrival's time-stream decks (T-2611).

    python3 tools/check_timestream.py --check       gate every deck in data/timestream/
    python3 tools/check_timestream.py --self-test   plant each fault and require the gate to refuse it

Design doc "Field Navigator Mk II", section 05 "Time-stream captions": as the arrival's
ticker rolls down from the present year to the destination, a one-line caption shows for
about two seconds as it passes a landmark year. Each destination (1812, 1835, 1904) has
its own deck, data/timestream/<scene>.json, of 8 to 12 captions; js/time-stream.js shows
at most 3 of them on a fast load (by `importance`) and up to 8 on a slow one. The page
shows the strings exactly as written, so this gate sits between the author and the
visitor, and refuses:

  - a deck with fewer than 8 or more than 12 captions, or for a destination with no scene;
  - a caption with no grade, or a grade off the data's own ladder (attested, inferred,
    reconstructed);
  - a caption with no source, or a source id that does not resolve in data/sources/
    (AGENTS.md hard rule 1 — never invented), or no `note` saying what the source says
    (hard rule 2, and the reconstructed tier's "record what bounded the invention");
  - a year the ticker never passes (at or before the destination, or after this year),
    two captions on one year, or two at one importance (the fast-load pick must not
    depend on file order);
  - a caption over 70 characters or 20 words (section 03), or carrying an id, snake_case
    word, file path, link or ticket number — T-2635's string lint, reused from
    tools/compile_summaries.py so the two gates cannot drift apart — or a retired term
    ("documented", "conjectural") where the locked terms belong;
  - a caption that touches Native history or the removal without `review_required` and
    `touches_removal` and a `review_note` saying why (AGENTS.md, the standing constraint
    and the owner's ruling of 2026-09-17), and a caption on a year the deck holds back.
    `held_back` names years left out of the deck on purpose and says why; the 1812 deck,
    the one whose ticker passes them, holds back the years of the 1833 treaty and the
    removal rather than caption them.

These are facts about the years BETWEEN the present and the destination, shown in
transit; they put nothing in any scene, so hard rule 3 (the scene date) does not bind
them. Reading level is a separate gate (T-2669).
"""

import argparse
import copy
import datetime
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from compile_summaries import GRADES, lint_string, words  # noqa: E402  (T-2635's lint)

ROOT = HERE.parent
DATA = ROOT / "data"
DECKS = DATA / "timestream"

DESTINATIONS = ("1812", "1835", "1904")
MIN_CAPTIONS, MAX_CAPTIONS = 8, 12
MAX_CHARS, MAX_WORDS = 70, 20
CAPTION_KEYS = {"year", "text", "grade", "importance", "sources", "note",
                "review_required", "touches_removal", "review_note"}
DECK_KEYS = {"scene", "about", "captions", "held_back", "held_back_note"}
RETIRED = re.compile(r"\b(documented|conjectural)\b", re.IGNORECASE)
# A caption on this subject is held to the standing constraint. The list is the subjects
# the constraint names and the words a caption about them would use; a match is not a
# judgement that the caption is wrong, only that it must carry the flags and its reason.
NATIVE = re.compile(
    r"\b(potawatomi\w*|pottawatomie\w*|native|indian\w*|indigenous|tribe\w*|treat(y|ies)|"
    r"removal|removed|ojibwe?|chippewa|odawa|m[ée]tis|sauk|black\s+hawk|winnebago|ho-chunk|"
    r"kickapoo|miami|massacre|battle)\b", re.IGNORECASE)
REVIEW_SUBJECT = re.compile(r"removal|native|indigenous|potawatomi", re.IGNORECASE)


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_world(root=ROOT):
    data = Path(root) / "data"
    return {
        "sources": {p.stem for p in (data / "sources").glob("*.json")},
        "scenes": {p.stem for p in (data / "scenes").glob("*.json")},
        "present": datetime.date.today().year,
    }


def gate(stem, deck, world):
    """Every reason this deck may not reach a visitor, as strings."""
    errs = []
    if not isinstance(deck, dict):
        return [f"{stem}: not an object"]
    for k in sorted(set(deck) - DECK_KEYS):
        errs.append(f"{stem}: unknown field `{k}`")
    scene = deck.get("scene")
    if scene != stem:
        errs.append(f"{stem}: `scene` is {scene!r}, not the file's own name")
    if stem not in world["scenes"]:
        errs.append(f"{stem}: no data/scenes/{stem}.json — a deck for a destination with no scene")
    try:
        target = int(stem)
    except ValueError:
        return errs + [f"{stem}: the file is not named for a year"]

    held = set()
    for i, h in enumerate(deck.get("held_back") or []):
        years = h.get("years") if isinstance(h, dict) else None
        if not years or not all(isinstance(y, int) for y in years):
            errs.append(f"{stem}: held_back[{i}] names no years")
        else:
            held.update(years)
        why = h.get("why") if isinstance(h, dict) else None
        if not isinstance(why, str) or len(words(why)) < 8:
            errs.append(f"{stem}: held_back[{i}] does not say why")

    caps = deck.get("captions")
    if not isinstance(caps, list):
        return errs + [f"{stem}: no captions list"]
    if not MIN_CAPTIONS <= len(caps) <= MAX_CAPTIONS:
        errs.append(f"{stem}: {len(caps)} captions; a deck holds {MIN_CAPTIONS} to {MAX_CAPTIONS}")
    seen_years, seen_rank = {}, {}
    for i, cap in enumerate(caps):
        where = f"{stem} captions[{i}]"
        if not isinstance(cap, dict):
            errs.append(f"{where}: not an object")
            continue
        for k in sorted(set(cap) - CAPTION_KEYS):
            errs.append(f"{where}: unknown field `{k}`")
        year = cap.get("year")
        if not isinstance(year, int) or isinstance(year, bool):
            errs.append(f"{where}: no year")
        else:
            where = f"{stem} {year}"
            if not target < year <= world["present"]:
                errs.append(f"{where}: the ticker never passes {year} on the way from "
                            f"{world['present']} to {target}")
            if year in seen_years:
                errs.append(f"{where}: two captions on one year")
            seen_years[year] = i
            if year in held:
                errs.append(f"{where}: the deck holds this year back, and it is captioned")
        rank = cap.get("importance")
        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            errs.append(f"{where}: no importance (a whole number from 1)")
        elif rank in seen_rank:
            errs.append(f"{where}: shares importance {rank} with another caption, so the "
                        "fast-load pick would depend on file order")
        else:
            seen_rank[rank] = i
        grade = cap.get("grade")
        if grade is None:
            errs.append(f"{where}: no grade")
        elif grade not in GRADES:
            errs.append(f"{where}: grade {grade!r} is not one of {', '.join(GRADES)}")
        srcs = cap.get("sources")
        if not isinstance(srcs, list) or not srcs:
            errs.append(f"{where}: no source")
        else:
            for s in srcs:
                if s not in world["sources"]:
                    errs.append(f"{where}: source `{s}` does not resolve in data/sources/")
        note = cap.get("note")
        if not isinstance(note, str) or len(words(note)) < 4:
            errs.append(f"{where}: no note saying what the source says"
                        + ("" if grade == "attested" else " or what bounded the reading"))
        text = cap.get("text")
        if not isinstance(text, str) or not text.strip():
            errs.append(f"{where}: no text")
            continue
        if len(text) > MAX_CHARS:
            errs.append(f"{where}: {len(text)} characters; a caption is at most {MAX_CHARS}")
        if len(words(text)) > MAX_WORDS:
            errs.append(f"{where}: {len(words(text))} words; a caption is at most {MAX_WORDS}")
        for found in lint_string(text):
            errs.append(f"{where}: the text carries {found}")
        m = RETIRED.search(text)
        if m:
            errs.append(f"{where}: `{m.group(0)}` is retired; the locked terms are Attested, "
                        "Inferred and Reconstructed")
        m = NATIVE.search(text)
        flagged = cap.get("review_required") is True and cap.get("touches_removal") is True
        if cap.get("touches_removal") is True and cap.get("review_required") is not True:
            errs.append(f"{where}: touches_removal without review_required")
        if m and not flagged:
            errs.append(f"{where}: `{m.group(0)}` touches Native history; the caption needs "
                        "review_required and touches_removal with its reason (AGENTS.md)")
        if flagged or m:
            rn = cap.get("review_note")
            if not isinstance(rn, str) or "review" not in rn.lower() or not REVIEW_SUBJECT.search(rn):
                errs.append(f"{where}: review_note must say why it is held for review and name "
                            "the subject (the removal or Native history)")
    return errs


def read_decks(decks=DECKS):
    return {p.stem: load_json(p) for p in sorted(Path(decks).glob("*.json"))}


def run(decks=DECKS, root=ROOT, world=None, quiet=False):
    world = world or load_world(root)
    found = read_decks(decks)
    errs = []
    for dest in DESTINATIONS:
        if dest in world["scenes"] and dest not in found:
            errs.append(f"{dest}: no deck — every destination has one (data/timestream/{dest}.json)")
    for stem, deck in found.items():
        errs.extend(gate(stem, deck, world))
    if not quiet:
        for stem, deck in found.items():
            caps = deck.get("captions") or []
            grades = {}
            for c in caps:
                grades[c.get("grade")] = grades.get(c.get("grade"), 0) + 1
            top = sorted(caps, key=lambda c: -(c.get("importance") or 0))[:3]
            print(f"  {stem}: {len(caps)} captions ({', '.join(f'{n} {g}' for g, n in sorted(grades.items(), key=str))}); "
                  f"fast-load three: {', '.join(str(c.get('year')) for c in top)}; "
                  f"held back: {sorted({y for h in deck.get('held_back') or [] for y in h.get('years', [])}) or 'none'}")
        for e in errs:
            print(f"FAIL {e}")
    return errs


def fixture_world():
    return {"sources": {"real_source"}, "scenes": {"1904"}, "present": 2026}


def fixture_deck():
    caps = []
    for i, year in enumerate((1990, 1980, 1970, 1960, 1950, 1940, 1930, 1920)):
        caps.append({"year": year, "text": f"Something plain and true happens in {year}.",
                     "grade": "attested", "importance": i + 1, "sources": ["real_source"],
                     "note": "The fixture source says so, in so many words."})
    return {"scene": "1904", "about": "a fixture", "captions": caps,
            "held_back": [{"years": [1935], "why": "A fixture year held back to test that a held year stays uncaptioned."}]}


def self_test():
    failures = []

    def expect(cond, what):
        print(f"   self-test | {'ok  ' if cond else 'FAIL'} {what}")
        if not cond:
            failures.append(what)

    world = fixture_world()
    clean = gate("1904", fixture_deck(), world)
    expect(not clean, f"a clean fixture deck passes ({clean[:2]})")

    def plant(label, needle, mutate):
        deck = copy.deepcopy(fixture_deck())
        mutate(deck)
        errs = gate("1904", deck, world)
        expect(any(needle in e for e in errs), f"{label} is refused ({needle!r})")

    def cap(d):
        return d["captions"][0]
    plant("a caption with no grade", "no grade", lambda d: cap(d).pop("grade"))
    plant("a retired grade", "is not one of", lambda d: cap(d).update(grade="documented"))
    plant("a caption with no source", "no source", lambda d: cap(d).update(sources=[]))
    plant("an invented source", "does not resolve", lambda d: cap(d).update(sources=["no_such_source_planted"]))
    plant("a caption with no note", "no note", lambda d: cap(d).pop("note"))
    plant("a caption over 70 characters", "characters; a caption", lambda d: cap(d).update(text="x" * 71))
    plant("a caption over 20 words", "words; a caption", lambda d: cap(d).update(text=" ".join(["a"] * 21)))
    plant("a snake_case id in the text", "snake_case", lambda d: cap(d).update(text="The glessner_house is saved."))
    plant("a file path in the text", "file path", lambda d: cap(d).update(text="See data/timestream/1904.json now."))
    plant("a ticket number in the text", "ticket number", lambda d: cap(d).update(text="Fixed under T-2611."))
    plant("a retired term in the text", "is retired", lambda d: cap(d).update(text="A documented fire."))
    plant("a year the ticker never passes", "never passes", lambda d: cap(d).update(year=1904))
    plant("a year after the present", "never passes", lambda d: cap(d).update(year=2031))
    plant("two captions on one year", "two captions on one year", lambda d: d["captions"][1].update(year=1990))
    plant("two captions at one importance", "shares importance", lambda d: d["captions"][1].update(importance=1))
    plant("a deck of seven", "7 captions", lambda d: d["captions"].pop())
    plant("a deck of thirteen", "13 captions", lambda d: d["captions"].extend(
        [dict(cap(d), year=1906 + k, importance=50 + k) for k in range(5)]))
    plant("Native history with no flags", "touches Native history",
          lambda d: cap(d).update(text="The Potawatomi leave Chicago."))
    plant("flags with no reason", "review_note must say", lambda d: cap(d).update(
        text="The Potawatomi leave Chicago.", review_required=True, touches_removal=True))
    plant("touches_removal without review_required", "without review_required",
          lambda d: cap(d).update(touches_removal=True))
    plant("a held-back year captioned", "holds this year back", lambda d: cap(d).update(year=1935))
    plant("a hold with no reason", "does not say why", lambda d: d["held_back"][0].update(why="because"))
    errs = gate("1866", dict(fixture_deck(), scene="1866"), world)
    expect(any("no data/scenes" in e for e in errs), "a deck for a destination with no scene is refused")
    errs = run(decks=Path("/nonexistent-timestream"), world=world, quiet=True)
    expect(any("no deck" in e for e in errs), "a destination with no deck is refused")
    flagged = copy.deepcopy(fixture_deck())
    cap(flagged).update(text="The Potawatomi leave Chicago.", review_required=True, touches_removal=True,
                        review_note="Held for review by Native scholars: it touches the removal.")
    expect(not gate("1904", flagged, world), "a flagged caption with its reason passes the gate")
    print(f"   self-test | {len(failures)} of the planted faults got through" if failures
          else "   self-test | every planted fault refused")
    return 1 if failures else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    errs = run()
    if errs:
        print(f"TIMESTREAM FAIL — {len(errs)} problem(s)")
        return 1
    print("TIMESTREAM PASS — every deck graded, sourced, within its lengths and free of ids")
    return 0


if __name__ == "__main__":
    sys.exit(main())
