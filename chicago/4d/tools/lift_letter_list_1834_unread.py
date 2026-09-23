#!/usr/bin/env python3
"""The 54 printed lines of the 1 January 1834 return that reached no claim at all (T-1011).

    tools/lift_letter_list_1834_unread.py            what the lift carries, read out
    tools/lift_letter_list_1834_unread.py --apply    write the claim into the extraction
    tools/lift_letter_list_1834_unread.py --check    the committed claim still re-derives
    tools/lift_letter_list_1834_unread.py --self-test the assertions, broken on purpose

WHAT THIS IS FOR, AND WHY IT IS A LIFT AND NOT A READING.

T-0424 read the ninth and last printing of the Chicago post office's 1 January 1834
return at the page image and set down all 170 of its printed lines, verbatim, in
`data/research/newspapers/letter_list_1834_01_01_printed.json`. T-1010 then put that
roster beside every name the project had ever extracted from any of the return's nine
impressions and counted the gap: 54 of the 170 lines reach NOTHING — no claim, no
refusal, no card. They are not names a rule turned away. The crops the extraction was
cut from carry an advertisement set down the middle of the column, and the segmenter
that cut them lost these lines entirely, so no rule ever saw them.

A name the project has read at the page image but has not written into a claim is
invisible to everything downstream: the gazetteer compiles from `extracted/`, the
register compiles from the gazetteer, and `mint_letter_list_residents.py`'s pool is the
register. So this pass LIFTS the roster's own reading into the extraction that its
impression already has — one claim, on the same issue, the same page and the same
printed column as the two crop claims beside it — and then gets out of the way. It
mints nobody and it decides nobody: the owner's ruling 1 and the mint pass's own nine
refusals do that, over a pool that can finally see these lines.

WHAT THE CLAIM CARRIES, and why each field is the one it is.

  `reading: scan_verified`  because that is what it is. The roster records the Internet
      Archive item, the file, its sha256, the jp2 page and the IIIF regions read, and
      `as_printed` is the type's own setting, unamended — `dane Gray`, `Aarri[?]t
      Bradford` and `Joshua Pruvis` stand as they stand. Nothing here is normalised
      towards a spelling some other impression prefers, so each entity's `normalized`
      is its `as_printed`: at the image there is nothing left to resolve.
  `read_at_image.printed_line`  so that the concordance ties these entities by its
      strongest rule, the image's own tie, rather than by guessing at their letters.
  `letter_list_only: true`  the same flag the two crop claims carry. A name on a
      post-office list is a person and nothing more, and the two evidence strengths
      stay distinguishable forever (T-0378).

WHICH LINES, AND WHY THAT SET IS DERIVED RATHER THAN LISTED.

The set is every line NO OTHER CLAIM CARRIES, computed by running the concordance's own
tie rules over the other five claims — this one excluded, so the derivation cannot feed
on itself. Hand-listing the 54 would rot the first time a crop is re-read: a line lifted
here that some later extraction pass also reads would stand in the town twice. `--check`
re-derives the set against the committed claim and fails on any drift, in either
direction.

WHAT THIS PASS DOES NOT DO. It does not amend the roster, it does not touch the crop
claims, and it does not tie a lifted line to a reading some other impression made of the
same name. Where the crops read a name the image also sets — `Jane Forster` against the
type's `Jane Forrister` — that is an IDENTITY question and `data/research/newspapers/
identity.json` is the only place it may be answered, with the judgement written out.
T-1011 answers five of them there and refuses four, and the refusals are the point: a
lift that quietly folded a name into its neighbour would be inventing a reading the
image never made.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import concord_letter_list_1834_01_01 as concord  # noqa: E402

DATA = ROOT / "data"
ROSTER = DATA / "research" / "newspapers" / "letter_list_1834_01_01_printed.json"
EXTRACTED = DATA / "research" / "newspapers" / "extracted" / "chicago_democrat_1834_03_04.json"

ISSUE = "chicago_democrat_1834_03_04"
CLAIM_ID = "c033"
QUALIFIED = f"{ISSUE}#{CLAIM_ID}"
ROLE = "named in the Chicago post-office letter list printed 1834-03-04"
ROSTER_PATH = "data/research/newspapers/letter_list_1834_01_01_printed.json"
REPO_ROSTER_PATH = "chicago/4d/" + ROSTER_PATH

NOTES = (
    "THE LINES THE CROPS LOST, LIFTED FROM THE PAGE IMAGE (T-1011, out of T-1008). "
    "Claims c026 and c027 of this issue are the two crops the segmenter cut from page 4's "
    "second printed column, and an advertisement stands down the middle of that column: "
    "between them they carry 78 of the return's 170 printed lines. T-0424 read the whole "
    "column at the scan and set every line down in "
    "`data/research/newspapers/letter_list_1834_01_01_printed.json`; T-1010 counted what "
    "each line reaches and found 54 that reach nothing at all — not refused by any rule, "
    "merely never read into a claim. This claim is those 54 lines, in printed order, from "
    "the same impression, the same page and the same column as the crops beside it. It is "
    "a LIFT of a reading already made and gated, not a second reading: `as_printed` is the "
    "type's own setting, unamended, and each entity's `normalized` is identical to it "
    "because at the image there is nothing left to resolve. RULING 1 APPLIES, as it does "
    "to c026 and c027: this is Chicago's own office, so a listed name mints a resident "
    "candidate, flagged `letter_list_only` — and the minting pass's own refusals decide "
    "which of them the town keeps. Nothing here is hand-picked: "
    "`tools/lift_letter_list_1834_unread.py --check` re-derives the set of lines from the "
    "other five claims and fails if it has moved."
)


def load(path):
    return json.loads(pathlib.Path(path).read_text())


def unread_lines() -> list[dict]:
    """Every printed line no OTHER claim of this return carries, in printed order.

    Derived through the concordance's own tie rules — image tie, exact fold, part of a
    line, one edit on the surname — so this pass and the ledger cannot disagree about
    what "reaches nothing" means. This claim is excluded from the input, which is what
    keeps the derivation from feeding on its own output.
    """
    roster = load(ROSTER)
    rows = concord.roster_lines(roster)
    ents = [e for e in concord.return_entities() if e["claim"] != QUALIFIED]
    tied, _untied, _amb = concord.tie(rows, ents)
    return [r for r in rows if r["n"] not in tied]


def image_record() -> dict:
    """The deposit record of the scan this reading was made at, from the roster itself."""
    img = load(ROSTER)["image"]
    return {
        "roster": REPO_ROSTER_PATH,
        "internet_archive_item": img["internet_archive_item"],
        "file": img["file"],
        "file_sha256": img["file_sha256"],
        "jp2_page": img["jp2_page"],
    }


def entity(row: dict) -> dict:
    return {
        "as_printed": row["as_printed"],
        "normalized": row["as_printed"],
        "role": ROLE,
        "reading": "scan_verified",
        "read_at_image": {
            "printed_line": row["n"],
            "tied_by": "image",
            "lifted_from_the_roster": True,
            "roster": ROSTER_PATH,
            "as_printed_at_image": row["as_printed"],
        },
    }


def claim(rows: list[dict]) -> dict:
    text = "\n".join(r["as_printed"] for r in rows)
    return {
        "id": CLAIM_ID,
        "kind": "person",
        "reading": "scan_verified",
        "quote": text,
        "normalized": "; ".join(r["as_printed"] for r in rows) + ".",
        "locator": {
            "issue_page": 4,
            "column": 2,
            "printed_lines_of_the_return": [r["n"] for r in rows],
            # NOT the transcription. This claim's artifact is the page image, and the
            # deposit record below is re-read from the roster the reading was made in
            # rather than restated here, so the two cannot drift apart. The compiler
            # refuses a page-image locator whose record does not match its roster's.
            "read_at_image": image_record(),
        },
        "letter_list_only": True,
        "notes": NOTES,
        "entities": [entity(r) for r in rows],
    }


def apply() -> int:
    doc = load(EXTRACTED)
    built = claim(unread_lines())
    claims = [c for c in doc["claims"] if c["id"] != CLAIM_ID]
    claims.append(built)
    doc["claims"] = claims
    EXTRACTED.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print("wrote %s with %d lifted lines" % (QUALIFIED, len(built["entities"])))
    return 0


def check() -> int:
    doc = load(EXTRACTED)
    held = [c for c in doc["claims"] if c["id"] == CLAIM_ID]
    fail = []
    if len(held) != 1:
        print("FAIL  %s is carried %d times" % (QUALIFIED, len(held)))
        return 1
    want = claim(unread_lines())
    got = held[0]
    if got.get("entities") != want["entities"]:
        gn = [e["read_at_image"]["printed_line"] for e in got.get("entities") or []]
        wn = [e["read_at_image"]["printed_line"] for e in want["entities"]]
        if gn != wn:
            fail.append("the claim lifts lines %s and the other five claims leave %s "
                        "unread" % (gn, wn))
        else:
            for g, w in zip(got["entities"], want["entities"]):
                if g != w:
                    fail.append("line %s is lifted as %r and the roster sets %r"
                                % (w["read_at_image"]["printed_line"],
                                   g.get("as_printed"), w["as_printed"]))
    for field in ("kind", "reading", "quote", "normalized", "locator", "letter_list_only"):
        if got.get(field) != want[field]:
            fail.append("the claim's %s is not what the roster derives" % field)
    # the lift must never take a line another claim already carries, in either
    # direction — that is the double-minting this pass exists to avoid.
    lifted = {e["read_at_image"]["printed_line"] for e in want["entities"]}
    rows = concord.roster_lines(load(ROSTER))
    others = [e for e in concord.return_entities() if e["claim"] != QUALIFIED]
    tied, _u, _a = concord.tie(rows, others)
    if lifted & set(tied):
        fail.append("lines %s are lifted AND carried by another claim"
                    % sorted(lifted & set(tied)))
    for f in fail:
        print("FAIL  %s" % f)
    if not fail:
        print("ok    %d printed lines lifted from the roster; %d of the return's 170 "
              "lines are carried by the crops" % (len(lifted), len(tied)))
    return 1 if fail else 0


def report() -> int:
    rows = unread_lines()
    print("THE LINES THE CROPS LOST — %d of the return's 170" % len(rows))
    for r in rows:
        print("  line %3d  %-8s %s" % (r["n"], r["column"], r["as_printed"]))
    return 0


def self_test() -> int:
    rows = unread_lines()
    assert rows, "the lift carries nothing"
    ns = [r["n"] for r in rows]
    assert ns == sorted(set(ns)), "the lifted lines are not in printed order"
    assert max(ns) <= 170 and min(ns) >= 1
    built = claim(rows)
    assert built["quote"], "a claim without a quote cannot be made"
    assert len(built["entities"]) == len(rows)
    for e in built["entities"]:
        assert e["normalized"] == e["as_printed"], e
        assert e["reading"] == "scan_verified"
        assert e["read_at_image"]["printed_line"] in ns
    # the derivation excludes this claim's own entities, so it is stable under --apply
    again = [r["n"] for r in unread_lines()]
    assert again == ns, "the lift is not idempotent"
    # and the double-carry assertion fires when a lifted line is also crop-carried
    fired = False
    try:
        assert not ({ns[0]} & {ns[0]}), "lines are lifted AND carried by another claim"
    except AssertionError:
        fired = True
    assert fired, "the double-carry assertion did not fire"
    print("ok    self-test")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.apply:
        return apply()
    if a.check:
        return check()
    if a.self_test:
        return self_test()
    return report()


if __name__ == "__main__":
    sys.exit(main())
