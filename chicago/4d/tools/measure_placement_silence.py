#!/usr/bin/env python3
"""A house's live placement against everything its own printings said (T-0440).

    python3 tools/measure_placement_silence.py            the report
    python3 tools/measure_placement_silence.py --check    the invariant, as a gate

WHAT THIS COUNTS, AND WHY IT IS COUNTED RATHER THAN ARGUED.

`compile_gazetteer.py` mints a house's dict from WHICHEVER CLAIM MINTS THE KEY — the
earliest printing the corpus carries — and takes `placement` and `street` from it.
Every later printing's placement is kept as a READING with its own dates (T-0345), but
until T-0440 nothing downstream of the mint ever revised the live one. So a standing
advertisement that ran without an address in its first week and with one afterwards
stood at `{"class": "none"}` for good, `compile_register.resolve_anchor` was handed no
anchor, and the row read `unplaceable` — while three of the house's own printings said
otherwise a few lines below in the same file.

Clark, Filer & Co. is the house it was found on: silent on 1834-05-28, then *"their ware
house on South water St. five [doors east] of the corner [of Randolph st.]"* on
1834-06-11, 1834-06-18 and 1834-07-02, and `unplaceable` in the register throughout.
T-0440 asked for the count of others before it asked for a repair, because a defect one
house shows is a bug and a defect fourteen show is a rule choosing wrongly.

THE TWO POPULATIONS, AND ONLY ONE OF THEM IS THIS PASS'S TO FIX.

  * **SILENT, THEN PLACED** — the live placement places nothing and some printing of the
    same house does. A printing that omits the address does not contradict one that gives
    it; it simply did not repeat it, which is what a standing advertisement does every
    other week. There is no judgement about a house that MOVED to be made here, so
    `compile_gazetteer` takes the earliest placing reading and this report expects the
    count to be ZERO on a compiled tree. `--check` asserts exactly that.

  * **PLACED, THEN PLACED BETTER** — the live placement already puts the house somewhere
    and a later printing puts it somewhere narrower, or somewhere else. Preferring one
    printed address to another is a statement about the house or about the advertisement,
    and the only thing in this project that may make it is the authored `anchor_changes`
    rule, which has to name the anchors verbatim and say what the corpus leaves open.
    **Nothing here repairs these and nothing should**: they are REPORTED, with the class
    they hold and the class they were outranked by, so the queue can see how many are
    waiting on a judgement.

    T-0773 counted that population and found that only part of it is waiting on anything,
    so it is reported in three lines rather than one. A house whose `anchor_changes` rule
    has been WRITTEN has had the judgement made and is not waiting for it — the class rank
    still calls it outranked, because a ruling that a house moved will routinely leave the
    live anchor coarser than a sharper reading of where it used to be, and the rank cannot
    see the ruling. G. Spring is that case: ruled onto Dearborn Street beside the Tremont
    House, and still nominally outranked by a `corner` reading of the Franklin and South
    Water office he left. And a house outranked only by a printing AFTER the scene date is
    the same bound as the line below it working, not a judgement anyone may make: no rule
    could prefer that address without placing the house on the strength of an
    advertisement that had not run yet.

    AND A HOUSE MAY BE DECLARED REFUSED A RULE, which T-0949 landed off T-0773's reading
    and is what closes the report's last hole. Until then the only record of "this house
    is never getting an `anchor_changes` rule" was the ABSENCE of one, which is the same
    number as "nobody has opened this house yet" — so the sweep that read this report
    could not tell a judgement from a silence, and read the same houses again. A refusal
    is now declared in `identity.json` § `refused_anchor_changes` with its KIND, and
    `compile_gazetteer.py` checks the kind against the readings rather than taking the
    author's word, so a refusal counted on that line has been argued and machine-checked.
    Two houses hold one: J. K. Botsford, whose two anchors ran in the same issue, and
    Samuel Lewis, whose only sharper address was printed six weeks after the scene date.
    The refusal line sits ABOVE the scene-date one because a reader who has stated the
    bound in writing may not have that statement quietly outlive it — the compiler fails
    the refusal the moment such a printing turns up inside the scene, where the computed
    bucket would simply have reclassified the house and said nothing.

AND A THIRD, SINCE T-0948, WHICH IS NEITHER OF THOSE: **A STREET NAMED, NARROWED BY
AN ANCHOR ON THAT SAME STREET.** A house printing "South Water street" one week and
"on South Water street, at the stand formerly occupied by Clark & Co." the next has
not contradicted itself and was never silent; it said less and then said more about
one frontage. `compile_gazetteer` takes the narrower reading, bounded to the SAME
street and to the scene date, and this report prints those houses in their own
section rather than under "silent when minted" — which the counts above exist to
state exactly. An anchor on ANOTHER street stays `anchor_changes`' to declare and is
counted in the second population, where it belongs.

The rank is `compile_gazetteer.placement_rank`, read from that module rather than
retyped, so this report and the compiler cannot disagree about what outranks what.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from compile_gazetteer import (SCENE_DATE, placement_rank,  # noqa: E402
                               places_nothing)

GAZETTEER = ROOT / "data" / "research" / "newspapers" / "gazetteer.json"
REGISTER = ROOT / "data" / "research" / "newspapers" / "register_1835.json"


def survey():
    """Every house whose live placement is outranked by one of its own readings."""
    gaz = json.loads(GAZETTEER.read_text(encoding="utf-8"))
    reg = {b["id"]: b for b in json.loads(REGISTER.read_text(encoding="utf-8"))["businesses"]}
    scene_iso = SCENE_DATE.isoformat()
    silent, outranked, after_scene, ruled, out_of_scene = [], [], [], [], []
    refused, groundless = [], []
    for biz in gaz["businesses"]:
        # T-0859. "Places nothing" is a question about the PLACEMENT, not about its
        # class: a `street_only` carrying neither a street nor an anchor names no
        # street, and puts a shop on no more ground than `{"class": "none"}` does.
        # Read from `compile_gazetteer` rather than retyped, for the same reason
        # `placement_rank` already is — this report and the compiler may not disagree
        # about what puts a storefront on the ground.
        live = 0 if places_nothing(biz.get("placement")) else placement_rank(
            biz.get("placement"))
        readings = biz.get("placement_readings") or []
        placing = [r for r in readings if not places_nothing(r.get("placement"))]
        if not placing:
            # The population this line exists for is the one that PRINTED a placing
            # class and named no ground with it. A house whose every reading is
            # `{"class": "none"}` is the ordinary silent advertisement, counted nowhere
            # and rightly so.
            if any(placement_rank(r.get("placement")) > 0 for r in readings):
                groundless.append({
                    "id": biz["id"],
                    "live_class": (biz.get("placement") or {}).get("class") or "none",
                    "groundless_class": next(
                        r.get("class") for r in readings
                        if placement_rank(r.get("placement")) > 0),
                    "readings": len(readings),
                    "action": (reg.get(biz["id"]) or {}).get("action")})
            continue
        best = max(placement_rank(r.get("placement")) for r in placing)
        if best <= live:
            continue
        # An address first printed after 1 July 1835 was not up on 1 July 1835, so a
        # house whose only placing printings run after the scene date is not a defect —
        # it is the bound working. Reported on its own line, never counted as silence.
        in_scene = [r for r in placing if r["first_issue"] <= scene_iso]
        anchors = sorted({(r.get("class"), r.get("anchor") or "",
                           (r.get("placement") or {}).get("street") or "")
                          for r in placing})
        row = {
            "id": biz["id"], "name": biz.get("name"),
            "live_class": (biz.get("placement") or {}).get("class") or "none",
            "best_class": next(r.get("class") for r in placing
                               if placement_rank(r.get("placement")) == best),
            "readings": len(readings), "distinct_placing_anchors": len(anchors),
            "action": (reg.get(biz["id"]) or {}).get("action"),
            "took_a_later_printing": bool(biz.get("placement_from")),
            "ruled": bool(biz.get("anchor_change")),
            "refused": bool(biz.get("anchor_refusal")),
            "refusal_kind": (biz.get("anchor_refusal") or {}).get("kind"),
            "live_anchor": (biz.get("anchor_change") or {}).get("live_anchor"),
            "outranked_in_scene": any(
                placement_rank(r.get("placement")) > live for r in in_scene),
        }
        if live == 0 and not in_scene:
            after_scene.append(row)
        elif live == 0:
            silent.append(row)
        elif row["ruled"]:
            # The judgement this report exists to count has been made for this house.
            ruled.append(row)
        elif row["refused"]:
            # …and so has the judgement that NO rule may be written (T-0773, landed by
            # T-0949). This is the other half of `ruled`, and it has to be its own line:
            # before it existed, a declared refusal and a house nobody had opened were
            # the same number, and the sweep that read this report could not tell them
            # apart. `identity.json` § `refused_anchor_changes` carries the argument and
            # `compile_gazetteer.py` checks the kind against the readings, so a refusal
            # counted here has been argued and machine-checked, not merely asserted. The
            # check is placed ABOVE the scene-date bound on purpose: a refusal of kind
            # `after_the_scene_date` is a reader saying in writing what the bound says by
            # computation, and it may not outlive the bound silently — the compiler fails
            # it the moment an outranking printing turns up inside the scene.
            refused.append(row)
        elif not row["outranked_in_scene"]:
            # Outranked only by an address first printed after the scene date.
            out_of_scene.append(row)
        else:
            outranked.append(row)
    return (silent, outranked, after_scene, ruled, refused, out_of_scene,
            groundless)


def report() -> int:
    (silent, outranked, after_scene, ruled, refused, out_of_scene,
     groundless) = survey()
    gaz = json.loads(GAZETTEER.read_text(encoding="utf-8"))
    print("A HOUSE'S LIVE PLACEMENT AGAINST ITS OWN PRINTINGS — T-0440\n")
    took = [b for b in gaz["businesses"] if b.get("placement_from")]
    print("  house(s) compiled                                          %4d"
          % len(gaz["businesses"]))
    print("  — placed by a printing later than the one that minted them %4d"
          % len(took))
    print("  — live placement places NOTHING while a printing does      %4d  "
          "(this is the defect; it must be 0)" % len(silent))
    print("  — outranked, and waiting on an `anchor_changes` judgement  %4d  "
          "(a judgement, and `anchor_changes` owns it)" % len(outranked))
    print("  — outranked, and the judgement has been WRITTEN            %4d  "
          "(an authored `anchor_changes` rule)" % len(ruled))
    print("  — outranked, and DECLARED REFUSED a change                 %4d  "
          "(`refused_anchor_changes`, kind checked)" % len(refused))
    print("  — outranked only by a printing after %s        %4d  "
          "(the scene-date bound, working)"
          % (SCENE_DATE.isoformat(), len(out_of_scene)))
    print("  — placed by no printing on or before %s          %4d  "
          "(the scene-date bound, working)" % (SCENE_DATE.isoformat(), len(after_scene)))
    print("  — no printing of theirs ever named any ground              %4d  "
          "(T-0859: nothing to place them by, and none is invented)" % len(groundless))
    # TWO REPAIRS, REPORTED APART (T-0948). Both write `placement_from`, and folding
    # them together would file a house that named its street under "silent when
    # minted" — which is the one thing this report exists to count exactly.
    narrowed = [b for b in took
                if (b["placement_from"].get("rule") or "").startswith("T-0948")]
    silent_then = [b for b in took if b not in narrowed]
    if silent_then:
        print("\nSILENT WHEN MINTED, PLACED BY A LATER PRINTING — repaired here")
        for b in sorted(silent_then, key=lambda b: b["id"]):
            frm = b["placement_from"]
            street = frm.get("street_from_reading")
            print("  %-52s %-11s %s%s"
                  % (b["id"], (b.get("placement") or {}).get("class"),
                     frm["first_issue"], "  street: %s" % street if street else ""))
    if narrowed:
        print("\nA STREET NAMED, NARROWED BY AN ANCHOR ON THAT SAME STREET (T-0948) —\n"
              "not silence repaired: the coarse printing said less, and the anchored one "
              "said more\nabout the same frontage. An anchor on ANOTHER street is a move "
              "and `anchor_changes`' alone")
        for b in sorted(narrowed, key=lambda b: b["id"]):
            frm = b["placement_from"]
            print("  %-52s %-11s %s  street: %s  bound: %s"
                  % (b["id"], (b.get("placement") or {}).get("class"),
                     frm["first_issue"], frm.get("street"), frm.get("bound")))
    if groundless:
        print("\nNO PRINTING OF THEIRS EVER NAMED ANY GROUND (T-0859) — a `street_only`\n"
              "carrying neither a street nor an anchor is not an address, so these are "
              "not placed\nand nothing is invented for them")
        for r in sorted(groundless, key=lambda r: r["id"]):
            print("  %-52s printed %-11s live %-11s register: %s"
                  % (r["id"], r["groundless_class"], r["live_class"], r["action"]))
    if silent:
        print("\nSTILL SILENT WHILE A PRINTING PLACES THEM — the defect, unrepaired")
        for r in sorted(silent, key=lambda r: r["id"]):
            print("  %-52s %s -> %s" % (r["id"], r["live_class"], r["best_class"]))
    if after_scene:
        print("\nPLACED ONLY BY A PRINTING AFTER THE SCENE DATE — left silent on "
              "purpose (AGENTS.md rule 3)")
        for r in sorted(after_scene, key=lambda r: r["id"]):
            print("  %-52s would have been %-11s register: %s"
                  % (r["id"], r["best_class"], r["action"]))
    if outranked:
        print("\nA PRINTED ADDRESS OUTRANKED BY A LATER PRINTED ADDRESS — left alone on "
              "purpose;\nreordering two printed addresses is a judgement and "
              "`anchor_changes` is where it is written")
        for r in sorted(outranked, key=lambda r: r["id"]):
            print("  %-52s %-11s outranked by %-11s %d distinct anchor(s), register: %s"
                  % (r["id"], r["live_class"], r["best_class"],
                     r["distinct_placing_anchors"], r["action"]))
    if ruled:
        print("\nOUTRANKED BY THE CLASS RANK, AND RULED ON ANYWAY — an `anchor_changes` "
              "rule\nnames the anchors and says what the corpus leaves open; the rank "
              "cannot see it")
        for r in sorted(ruled, key=lambda r: r["id"]):
            print("  %-52s %-11s live anchor: %s"
                  % (r["id"], r["live_class"], r["live_anchor"]))
    if refused:
        print("\nOUTRANKED, AND DECLARED REFUSED A CHANGE (T-0773) — the judgement was "
              "made\nand it was that no rule may be written; each names an anchor it "
              "will not be\nreordered by, and the compiler checks the kind against the "
              "readings")
        for r in sorted(refused, key=lambda r: r["id"]):
            print("  %-52s %-11s outranked by %-11s %s"
                  % (r["id"], r["live_class"], r["best_class"], r["refusal_kind"]))
    if out_of_scene:
        print("\nOUTRANKED ONLY BY A PRINTING AFTER THE SCENE DATE — no judgement is "
              "owed;\nan address that had not run yet may not place a house on %s"
              % SCENE_DATE.isoformat())
        for r in sorted(out_of_scene, key=lambda r: r["id"]):
            print("  %-52s %-11s outranked by %-11s register: %s"
                  % (r["id"], r["live_class"], r["best_class"], r["action"]))
    return 0


def check() -> int:
    (silent, outranked, after_scene, ruled, refused, out_of_scene,
     groundless) = survey()
    if silent:
        print("PLACEMENT SILENCE FAIL — %d house(s) hold a live placement that places "
              "nothing while one of their own printings places them:" % len(silent))
        for r in sorted(silent, key=lambda r: r["id"]):
            print("  - %s (%s, outranked by %s). compile_gazetteer.py takes the earliest "
                  "placing reading; re-run `tools/compile_gazetteer.py --build`."
                  % (r["id"], r["live_class"], r["best_class"]))
        return 1
    took = len([1 for b in json.loads(GAZETTEER.read_text(encoding="utf-8"))["businesses"]
                if b.get("placement_from")])
    print("  ok    no house is placed by a printing that gave no address; %d house(s) "
          "take a later printing's, %d WAIT on a judgement nobody has made, %d have an "
          "`anchor_changes` rule written, %d are declared REFUSED one with the kind "
          "checked, %d are outranked only by a printing after the scene date, %d are "
          "placed by nothing printed on or before it, and %d were never given any ground "
          "by any printing of their own"
          % (took, len(outranked), len(ruled), len(refused), len(out_of_scene),
             len(after_scene), len(groundless)))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="fail if any house is left placed by a silent printing")
    args = ap.parse_args()
    raise SystemExit(check() if args.check else report())
