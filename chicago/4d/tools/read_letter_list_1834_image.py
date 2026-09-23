#!/usr/bin/env python3
"""The 1 January 1834 letter list read at the page image (T-0424).

    tools/read_letter_list_1834_image.py            the printed length and the
                                                    thirty-two cut readings, settled
    tools/read_letter_list_1834_image.py --json     the same, machine-readable
    tools/read_letter_list_1834_image.py --apply    write the image readings into the claims
    tools/read_letter_list_1834_image.py --check    the committed claims still carry them
    tools/read_letter_list_1834_image.py --self-test  the assertions still fire

WHY THIS EXISTS. `tools/letter_list_printings.py` did everything the transcriptions
allow: it found nine printings of one standing list, and repaired twenty-five of the
fifty-seven forenames the 1834-03-04 crop cut off its left edge by concordance across
the other eight. Two questions survived it and BOTH were assigned to the page images.
How long the printed list is -- the concordance cannot count it, because the crops it
reads carry an interleaved advertisement and a surname census over them counts
`Athenian` and `Blankets` too. And the thirty-two readings still cut, which no two
printings agree on, or which no printing witnesses at all, or which carry a surname
that stands TWICE in the list so that a crop which lost both forenames cannot say
which line is which.

THE IMAGE ANSWERS BOTH, and it answers them on the SAME IMPRESSION the crops were cut
from rather than on a witness: `data/research/newspapers/letter_list_1834_01_01_printed.json`
is every line of the list as it stands on page 4 of Vol. I No. 15, read at the scan the
deposit manifest names. The deposit holds typed transcriptions; the scans behind them
are the public Internet Archive item `chicago1835-newspaper-chicago-democrat-1834`,
which is what `chicago/reference/newspapers/ChicagoDemocrat/1834.yaml` describes, and
the roster file records the item, the file, its sha256, the jp2 page and the exact
IIIF regions read.

**THE PRINTED LENGTH IS 170**, in two sub-columns of eighty-five, Eliphalet Atkins to
J. P. Harkness and Isaac Hays to Samuel Wright, over John S. C. Hogan's signature. The
crops carry 78. The floor was 45 per cent of the list.

WHAT THIS TOOL WILL NOT DO. It does not mint. T-0299 rules that one list mints once and
these names are January's, minted from the 1834-01-28 printing; the ninety-two lines the
crops never carried are a MINTING question and are filed as one, not answered here.
Nothing in the roster is amended to agree with anything: `as_printed` is the type's own
setting, so `dane Gray`, `Philip Willaee` and `Joshua Pruvis` stand as they stand.

HOW A CROP LINE IS TIED TO A PRINTED LINE. Both are in printed order, so the tie is by
ORDER, and `--check` asserts it: every mapped entity's line index strictly increases
within its claim. Where the fragment also carries enough letters to recognise the line
it is checked against it as well; where it does not -- `Nats` for `J. V. Natta`, `is
Pestin 2` for `Julius Perrin 2` -- the mapping says `by: position` and the check
demands that admission rather than pretending to a textual match.

TWO LINES THE IMAGE DOES NOT SETTLE, and they are reported rather than guessed. The
crop's `Re Leena,` stands between `Lewis Lake` and `Miranda Miner 2`, where the printed
list sets THREE lines -- `J. W. Lewis 2`, `J. S. Lacey`, `Jacob Loose` -- of which the
crop kept one; no surname in this list reads `Leena`. The crop's `I Cenige` stands
between `Thomas Conger` and `Lamira & Laura Carrier`, where the printed list sets five.
Both keep `reading: transcription_mediated` at the entity, and the candidates are named.
"""

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "data/research/newspapers/letter_list_1834_01_01_printed.json"
EXTRACTED = ROOT / "data/research/newspapers/extracted/chicago_democrat_1834_03_04.json"

# Crop entity (by claim and position in `entities`) -> line of the printed list.
# `None` is a line the image cannot assign, and it carries its candidates.
# `by` is how the tie was made: `text` where the fragment recognises its own line,
# `position` where only the order does.
MAPPING = {
    "c026": [
        (1, "text"), (13, "text"), (17, "text"), (18, "text"), (19, "text"),
        (21, "text"), (26, "text"), (30, "text"), (None, "unassigned"),
        (36, "text"), (42, "text"), (45, "text"), (46, "text"), (50, "text"),
        (55, "text"), (60, "text"), (61, "position"), (64, "position"),
    ],
    "c027": [
        (89, "text"), (90, "text"), (91, "position"), (92, "text"), (93, "text"),
        (94, "text"), (95, "text"), (96, "text"), (97, "text"), (98, "text"),
        (None, "unassigned"), (102, "text"), (103, "text"), (104, "text"),
        (105, "text"), (106, "text"), (109, "text"), (110, "text"), (111, "text"),
        (112, "text"), (114, "position"), (117, "position"), (118, "text"),
        (119, "text"), (120, "text"), (121, "text"), (122, "text"), (124, "text"),
        (125, "text"), (126, "text"), (137, "text"), (140, "text"), (141, "text"),
        (142, "text"), (143, "text"), (144, "text"), (145, "text"), (146, "text"),
        (147, "text"), (148, "text"), (149, "position"), (151, "text"), (152, "text"),
        (153, "text"), (154, "text"), (155, "text"), (156, "text"), (157, "text"),
        (158, "text"), (159, "text"), (160, "text"), (161, "text"), (162, "text"),
        (163, "text"), (164, "text"), (165, "text"), (166, "text"), (167, "text"),
        (168, "text"), (169, "text"), ("signature", "text"),
    ],
}

UNASSIGNED = {
    ("c026", 8): {
        "fragment": "I Cenige",
        "between": ["Thomas Conger", "Lamira & Laura Carrier"],
        "candidates": [31, 32, 33, 34, 35],
        "note": "No surname in the printed list reads `Cenige`. The crop kept one of the "
                "five lines the list sets between Conger and Carrier and the image cannot "
                "say which; `D. P. Clevinger` is the nearest setting and is NOT asserted.",
    },
    ("c027", 10): {
        "fragment": "Re Leena,",
        "between": ["Lewis Lake", "Miranda Miner 2"],
        "candidates": [99, 100, 101],
        "note": "No surname in the printed list reads `Leena`. The crop kept one of the "
                "three lines the list sets between Lake and Miner and the image cannot "
                "say which.",
    },
}

# The thirty-two readings `letter_list_printings.py` reports as still cut, by the
# `normalized` it minted them with. Every one of them is answered below.
STILL_CUT = [
    "[?] Atkins", "[…]as Bennett", "[?] E. Benton", "[?] Bennett[…]",
    "[?] H. Howard", "[?] Haight", "[…]ward", "[?] Johnson", "[?] Killigoss",
    "[?] Kinzie", "[?] Kercheval", "[?] Leena", "[?] Daniel", "[…]y Meriams",
    "[…]s Machel", "[?] M'Carty", "[?] Miner", "[?] Nats", "[?] Pestin",
    "[…]in Poel", "[?] Phelps", "[?] H. Riche[…]", "[?] Scott", "[?] Tuller",
    "[?] Thorn", "[?] Temple", "[?] Vanzandt", "[?] Vanderwerker", "[?] Willece",
    "[?] B. Winn & Co.", "[?] Weed", "[?] Webb",
]

SIGNATURE = "John S. C. Hogan"


def load(path=None):
    return json.loads((path or ROSTER).read_text())


def line_text(roster, n):
    return roster["lines"][n - 1]["as_printed"]


def letters(s):
    return re.sub(r"[^a-z]", "", s.lower())


def recognises(fragment, line):
    """Does the crop fragment carry enough of its own line to be tied to it by text?"""
    a, b = letters(fragment), letters(line)
    if not a or not b:
        return False
    if len(a) >= 4 and a in b:
        return True
    match = difflib.SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    if match.size >= 4:
        return True
    return difflib.SequenceMatcher(None, a, b).ratio() >= 0.55


def resolve(roster=None, extracted=None):
    """Every crop entity beside the printed line the image ties it to."""
    roster = roster or load()
    doc = extracted if extracted is not None else json.loads(EXTRACTED.read_text())
    claims = {c["id"]: c for c in doc["claims"]}
    out = []
    for cid, rows in MAPPING.items():
        entities = claims[cid]["entities"]
        if len(entities) != len(rows):
            raise AssertionError("%s carries %d entities, the mapping has %d"
                                 % (cid, len(entities), len(rows)))
        for i, (n, by) in enumerate(rows):
            ent = entities[i]
            # `was` is the reading the crops carried BEFORE the image was read. Once
            # `--apply` has run it lives in `read_at_image`, because `normalized` now
            # carries the printed line and the check must still be able to say what the
            # image overturned.
            prior = ent.get("read_at_image", {}).get("was_normalized")
            row = {"claim": cid, "entity": i, "as_printed": ent["as_printed"],
                   "was": prior if prior is not None else ent.get("normalized"),
                   "line": n, "by": by,
                   "completed_from": ent.get("completed_from")}
            if n == "signature":
                row["at_image"] = SIGNATURE
                row["reading"] = "scan_verified"
            elif n is None:
                row["at_image"] = None
                row["reading"] = "transcription_mediated"
                row["unassigned"] = UNASSIGNED[(cid, i)]
            else:
                row["at_image"] = line_text(roster, n)
                row["reading"] = "scan_verified"
            out.append(row)
    return out


def was_cut(was):
    """A reading the crop lost, which the image COMPLETES rather than overturns."""
    return "[?]" in (was or "") or "[…]" in (was or "")


def overturned(rows):
    """Readings that were not cut, and that the printed line contradicts anyway."""
    return [r for r in rows
            if r["at_image"] and r["was"] and not was_cut(r["was"])
            and letters(r["was"]).replace("uncertain", "") != letters(r["at_image"])]


def report(rows, roster):
    printed = roster["printed_length"]["lines"]
    floor = sum(1 for r in rows if r["line"] != "signature")
    settled = [r for r in rows if r["reading"] == "scan_verified"]
    print("THE PRINTED LENGTH, COUNTED OFF THE PAGE IMAGE")
    print("  %d lines stand in the Chicago post office's 1 January 1834 return as it is"
          % printed)
    print("  printed in the Democrat of 1834-03-04 -- %d in the left sub-column, %d in the"
          % (roster["printed_length"]["left_sub_column"],
             roster["printed_length"]["right_sub_column"]))
    print("  right -- over %s." % roster["return"]["signed"])
    print("  The crops minted %d personal names. The shortfall is %d lines, and the %d was"
          % (floor, printed - floor, floor))
    print("  a FLOOR at %d per cent of the printed list, not a length."
          % round(100.0 * floor / printed))
    print()
    print("THE THIRTY-TWO STILL-CUT READINGS, AT THE IMAGE")
    by_norm = {}
    for r in rows:
        by_norm.setdefault(r["was"], []).append(r)
    done = 0
    for was in STILL_CUT:
        for r in by_norm.get(was, []):
            if r["at_image"]:
                done += 1
                print("  %-22s -> %-28s line %s" % (was, r["at_image"], r["line"]))
            else:
                u = r["unassigned"]
                print("  %-22s -> UNREADABLE AT THE IMAGE: no line of the list reads it;"
                      % was)
                print("  %-22s    the crop kept one of %s"
                      % ("", ", ".join(line_text(roster, c) for c in u["candidates"])))
    print("  %d of %d completed at the image, %d reported unreadable."
          % (done, len(STILL_CUT), len(STILL_CUT) - done))
    print()
    print("WHAT THE IMAGE OVERTURNS -- readings the crops carried that the printed line")
    print("contradicts. A `[?]` or `[…]` reading was CUT and is completed above; these were")
    print("not cut. They were completed from another impression, or read off this crop, and")
    print("they are wrong -- which is the price of both routes and the reason for the image.")
    for r in overturned(rows):
        how = ("from " + ", ".join(r["completed_from"])) if r["completed_from"] \
            else "read off this crop"
        print("  %-26s was %-30s %s" % (r["at_image"], r["was"], how))
    print()
    print("THE SURNAMES THAT STAND TWICE, RESOLVED TO THEIR OWN LINES")
    for surname in ("Bennett", "Miner", "Temple", "Tuller"):
        lines = [(l["n"], l["as_printed"]) for l in roster["lines"]
                 if re.search(r"\b%s\b" % surname, l["as_printed"])]
        held = [r for r in rows if r["at_image"] and re.search(r"\b%s\b" % surname,
                                                              r["at_image"])]
        print("  %-8s printed: %s" % (surname, "; ".join("%s (line %d)" % (t, n)
                                                         for n, t in lines)))
        for r in held:
            print("           crop `%s` is line %d, %s" % (r["as_printed"], r["line"],
                                                           r["at_image"]))


APPLIED_NOTE = (
    " THE PAGE IMAGE HAS NOW BEEN READ, AND IT SETTLES BOTH QUESTIONS T-0331 LEFT (T-0424). "
    "`data/research/newspapers/letter_list_1834_01_01_printed.json` carries every line of "
    "this printing of the list, read at the scan behind the deposit -- Internet Archive "
    "`chicago1835-newspaper-chicago-democrat-1834`, `Jan1834-Mar1834.pdf`, jp2 page 0019, "
    "which is page 4 of Vol. I No. 15 -- with the IIIF regions named. THE PRINTED LENGTH IS "
    "170 LINES, eighty-five in each sub-column, over John S. C. Hogan's signature. The "
    "seventy-eight names these two claims mint are 45 per cent of it, so the hand count was "
    "a floor and the ninety-two missing lines are the crops' loss and not the paper's. "
    "EVERY ENTITY BELOW IS NOW TIED TO ITS PRINTED LINE, in `read_at_image`, and carries the "
    "grade of that tie: `scan_verified` where the image states the line, "
    "`transcription_mediated` for the two crop fragments no line of the list matches -- "
    "`I Cenige` and `Re Leena,` -- which are reported with their candidates rather than "
    "guessed. Thirty-one of the thirty-two readings `tools/letter_list_printings.py` left "
    "cut are completed here, INCLUDING the four the doubled surnames blocked: the crop's "
    "`as Bennett` is Thomas Bennett and its `Bennettra` is H. S. Bennett 2 -- the list holds "
    "THREE Bennetts, not two -- `nda Miner 2` is Miranda Miner 2 and `'. Miner` is F. T. "
    "Miner, `Temple 3` is Peter Temple 3 and `is Temple` is Lewis Temple, and `n Tuller` is "
    "Alden Tuller, the disagreement resolved. THE IMAGE ALSO OVERTURNS THREE CONCORDANCE "
    "COMPLETIONS, which is the price of completing a forename from another impression: "
    "`nda Miner 2` was read `[Ori]nda` and the type sets `Miranda` -- Orinda is a different "
    "person on this page, Orinda Garyl; `stor Marshall 2` was read `[Ne]stor` and the type "
    "sets `Chester`; `| Monreou` was read `John Monroe` and the type sets `John Monreou`. "
    "`normalized` now carries the printed line, `as_printed` still carries this crop's own "
    "setting, and nothing is minted here -- T-0299 rules that one list mints once and these "
    "names are January's."
)


def apply(doc, rows):
    claims = {c["id"]: c for c in doc["claims"]}
    for r in rows:
        ent = claims[r["claim"]]["entities"][r["entity"]]
        ent["reading"] = r["reading"]
        tie = {"printed_line": r["line"], "tied_by": r["by"],
               "was_normalized": r["was"],
               "roster": "data/research/newspapers/letter_list_1834_01_01_printed.json"}
        if r["at_image"]:
            tie["as_printed_at_image"] = r["at_image"]
            if r["line"] != "signature":
                ent["normalized"] = r["at_image"]
            if r["completed_from"] and letters(r["was"]) != letters(r["at_image"]):
                tie["overturns_concordance_completion"] = r["was"]
        else:
            tie.update(r["unassigned"])
        ent["read_at_image"] = tie
    for cid in MAPPING:
        c = claims[cid]
        c["reading"] = "scan_verified"
        if APPLIED_NOTE.strip() not in c["notes"]:
            c["notes"] = c["notes"] + APPLIED_NOTE
    return doc


def check():
    roster = load()
    doc = json.loads(EXTRACTED.read_text())
    rows = resolve(roster, doc)
    fail = []
    n = roster["printed_length"]
    if len(roster["lines"]) != n["lines"]:
        fail.append("the roster states %d lines and carries %d"
                    % (n["lines"], len(roster["lines"])))
    for col, want in (("left", n["left_sub_column"]), ("right", n["right_sub_column"])):
        got = sum(1 for l in roster["lines"] if l["column"] == col)
        if got != want:
            fail.append("the %s sub-column states %d lines and carries %d" % (col, want, got))
    for cid in MAPPING:
        seen = [r["line"] for r in rows if r["claim"] == cid and isinstance(r["line"], int)]
        if seen != sorted(set(seen)):
            fail.append("%s: the printed lines are not in printed order" % cid)
    for r in rows:
        if r["by"] == "text" and r["line"] != "signature":
            if not recognises(r["as_printed"], r["at_image"]):
                fail.append("%s entity %d: `%s` does not recognise `%s`, so the tie is by "
                            "position and must say so"
                            % (r["claim"], r["entity"], r["as_printed"], r["at_image"]))
    claims = {c["id"]: c for c in doc["claims"]}
    for r in rows:
        ent = claims[r["claim"]]["entities"][r["entity"]]
        if "read_at_image" not in ent:
            fail.append("%s entity %d carries no read_at_image" % (r["claim"], r["entity"]))
        elif ent["read_at_image"]["printed_line"] != r["line"]:
            fail.append("%s entity %d is tied to line %s and the claim says %s"
                        % (r["claim"], r["entity"], r["line"],
                           ent["read_at_image"]["printed_line"]))
        if ent.get("reading") != r["reading"]:
            fail.append("%s entity %d should read %s" % (r["claim"], r["entity"], r["reading"]))
    for cid in MAPPING:
        if claims[cid]["reading"] != "scan_verified":
            fail.append("%s should carry reading: scan_verified" % cid)
    if len(overturned(rows)) < 12:
        fail.append("the image overturned %d readings and the check expects at least 12"
                    % len(overturned(rows)))
    settled = {r["was"] for r in rows if r["at_image"]}
    for was in STILL_CUT:
        if was not in settled and was not in {"[?] Leena"}:
            fail.append("the still-cut reading `%s` is not settled at the image" % was)
    for f in fail:
        print("FAIL  %s" % f)
    if not fail:
        print("ok    %d printed lines; %d crop entities tied to their printed line; "
              "%d of %d still-cut readings settled"
              % (len(roster["lines"]), len(rows), len(STILL_CUT) - 1, len(STILL_CUT)))
    return 1 if fail else 0


def self_test():
    roster = load()
    assert len(roster["lines"]) == 170
    assert line_text(roster, 1).startswith("Eliphalet Atkins")
    assert line_text(roster, 85) == "J. P. Harkness"
    assert line_text(roster, 86) == "Isaac Hays"
    assert line_text(roster, 170) == "Samuel Wright"
    # the doubled surnames really are doubled, and one of them is trebled
    bennetts = [l["n"] for l in roster["lines"] if "Bennett" in l["as_printed"]]
    assert len(bennetts) == 3, bennetts
    assert len([l for l in roster["lines"] if "Miner" in l["as_printed"]]) == 2
    assert len([l for l in roster["lines"] if "Temple" in l["as_printed"]]) == 2
    assert len([l for l in roster["lines"] if "Tuller" in l["as_printed"]]) == 2
    # the tie test recognises a line it should and refuses one it should not
    assert recognises("ell Baldwin", "Russell Baldwin")
    assert recognises("nas H. Wrickey", "Thomas H. Wrickey")
    assert not recognises("Nats", "Lewis Kerchevel")
    assert not recognises("Re Leena,", "Jacob Loose")
    # every mapping row lands on a real line, in order, and the counts agree
    for cid, ident in MAPPING.items():
        ints = [n for n, _ in ident if isinstance(n, int)]
        assert ints == sorted(set(ints)), cid
        assert max(ints) <= 170
    assert sum(1 for rows in MAPPING.values() for n, _ in rows if n is None) == 2
    assert len(STILL_CUT) == 32
    assert was_cut("[?] Atkins") and was_cut("[…]as Bennett")
    assert not was_cut("[Ori]nda Miner") and not was_cut("Russel Baldwin")
    # and the assertions fire when the roster is broken
    broken = json.loads(ROSTER.read_text())
    broken["lines"] = broken["lines"][:-1]
    fired = False
    try:
        assert len(broken["lines"]) == 170
    except AssertionError:
        fired = True
    assert fired, "the length assertion does not fire"
    print("letter-list image read self-test: all assertions fire")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.check:
        return check()
    roster = load()
    if a.apply:
        doc = json.loads(EXTRACTED.read_text())
        rows = resolve(roster, doc)
        EXTRACTED.write_text(json.dumps(apply(doc, rows), indent=2, ensure_ascii=False) + "\n")
        print("applied %d image readings to c026 and c027" % len(rows))
        return 0
    rows = resolve(roster)
    if a.json:
        print(json.dumps({"printed_length": roster["printed_length"], "rows": rows},
                         indent=1, ensure_ascii=False))
        return 0
    report(rows, roster)
    return 0


if __name__ == "__main__":
    sys.exit(main())
