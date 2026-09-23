#!/usr/bin/env python3
"""The three contested lines of the 1 April 1834 return, read at the page images (T-1138).

    tools/read_letter_list_1834_04_01_image.py              the three lines, and what they move
    tools/read_letter_list_1834_04_01_image.py --json       the same, machine-readable
    tools/read_letter_list_1834_04_01_image.py --apply      write the image readings into the claim
    tools/read_letter_list_1834_04_01_image.py --check      the committed tree still carries them
    tools/read_letter_list_1834_04_01_image.py --self-test  the assertions still fire

WHY THIS EXISTS. Three consecutive lines of the S run of the Chicago post office's return of
1 April 1834 stood with two readings and no arbiter. The extraction of the Democrat of
1834-04-01 reads them `Benjamin Reed, the,`, `Ira Raymore apy'` and `3. Geo. Square t 3 first
rate` -- the Public Auction advertisement of the next column bleeding through all three -- and
the extraction of the 1834-04-16 impression reads the SAME three positions `Benjarnin Smith`,
`Ira Saymoro` and `Geo. Saver`. T-0321 recorded the disagreement and refused to act on it in
the only honest terms it had: "a minted name is not rewritten on a second transcription of
equal rank -- that is what the page images are for". Two town cards were minted on the losing
side of it, and `data/residents/card_merge_rulings.json` had to leave the square-squire
cluster UNDECIDED under U1 because a merge cannot be tested against a line nobody has read.

THE RULE THIS PASS APPLIES is T-0321's own: a transcription is overturned by the PAGE, never
by another transcription. All THREE impressions the Democrat printed of this one return are
read -- 1 April (leaf 0002), 8 April (leaf 0006) and 16 April (leaf 0011) -- because the
question is what the type set, and three impressions of it either agree or they do not.

THEY AGREE, AND THEY GO AGAINST BOTH TRANSCRIPTIONS.

    Benjamin Smith   -- `Reed` is the auctioneer's name out of the next column. 16 April right.
    Ira Saymore      -- the 1 April capital is filled with ink and unreadable on that
                        impression alone; 8 April and 16 April set a clean S with none of the
                        left-hand stem their own R and B carry. `Saymoro` right in its initial
                        and wrong in its last letter, `Raymore` the other way about.
    Geo. Squar       -- no final `e` on any of the three, and `Saver` is not on the page at
                        all: the second letter is a q with its descender. NEAREST the 1 April
                        reading, identical to neither, and no `e` is supplied.

WHAT IT MOVES, AND UNDER WHAT RULE. `normalized` is what the town mints from, so the two cards
minted on a name the image does not set do not survive the reading: `mint_letter_list_residents.py`
re-derives the cohort from the register and the stale card is deleted rather than edited, which
is the withdrawal. `raymore_ira` goes and `saymore_ira` stands in its place; `square_geo` goes
and `squar_geo` stands in its place. `Benjamin Reed` never had a card -- the mint refused it
because the town already names a Reed -- and `Benjamin Smith` is refused for the same reason, so
that line moves an identity and no household.

WHAT THIS PASS WILL NOT DO. It does not read the other 167 lines of the return, and it does not
raise the CLAIM to `scan_verified`: three of c002's eighty-two entities are read at the page and
seventy-nine are not, so the claim stays `transcription_mediated` and says why. The readings the
eye could not avoid while finding these three -- a whole line the 1 April extraction skips, a
second it carries in prose and in no entity, and three names set otherwise than they were
minted -- are recorded in the roster under `seen_in_passing` as OBSERVATIONS and are applied by
nothing. The concordance of the whole return is a larger piece of work and is filed as one.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "data/research/newspapers/letter_list_1834_04_01_contested_lines.json"
EXTRACTED = ROOT / "data/research/newspapers/extracted/chicago_democrat_1834_04_01.json"
HOUSEHOLDS = ROOT / "data/residents/households"

CLAIM = "c002"

# The withdrawal each settled line makes, stated rather than left to be inferred from a
# deleted file: the card the old reading minted, and the card the image's reading mints.
# `None` on either side is a line that moves no household, and the reason is written out.
CARDS = {
    58: (None, None,
         "Neither reading mints a household: the town already names a Reed and already names "
         "a Smith, so the mint's one-surname-to-one-household refusal declines both. What "
         "moves is the identity `id_reed_benjamin`, which becomes a Smith."),
    59: ("hh_raymore_ira", "hh_saymore_ira",
         "The Raymore card is withdrawn -- no impression of this return sets Raymore -- and "
         "the person it stood for keeps their place in the town under the name the page sets."),
    60: ("hh_square_geo", "hh_squar_geo",
         "The Square card is withdrawn -- no impression of this return sets a final e -- and "
         "the person it stood for keeps their place in the town under the name the page sets."),
}

CLAIM_NOTE = (
    "\n\nTHREE OF THESE LINES ARE READ AT THE PAGE IMAGES (T-1138) and seventy-nine are not, so "
    "this claim stays `transcription_mediated`. Entities 58, 59 and 60 carry `read_at_image` and "
    "`reading: scan_verified` individually: the advertisement of the next column bleeds through "
    "them here, the 16 April impression's extraction read the same three positions differently, "
    "and all three impressions of the return were read at the scan to settle it. "
    "`data/research/newspapers/letter_list_1834_04_01_contested_lines.json` is the reading, with "
    "the IIIF regions each line was read at."
)


def load_roster(path=None):
    return json.loads((path or ROSTER).read_text(encoding="utf-8"))


def load_extracted(path=None):
    return json.loads((path or EXTRACTED).read_text(encoding="utf-8"))


def claim_of(doc, cid=CLAIM):
    for c in doc["claims"]:
        if c["id"] == cid:
            return c
    raise KeyError(cid)


def rows(roster=None, doc=None):
    """One row per line of the roster, tied to the entity it moves."""
    roster = roster if roster is not None else load_roster()
    doc = doc if doc is not None else load_extracted()
    ents = claim_of(doc)["entities"]
    out = []
    for line in roster["lines"]:
        ref = line["entity"]
        i = ref["index"]
        was, to = CARDS[i][0], CARDS[i][1]
        out.append({
            "claim": ref["claim"],
            "entity": i,
            "as_printed": ents[i]["as_printed"],
            "was": line["minted_as"],
            "at_image": line["as_printed_at_image"],
            "verdict": line["verdict"],
            "overturns": line["overturns"],
            "at_each_impression": line["at_each_impression"],
            "card_withdrawn": was,
            "card_minted": to,
            "card_note": CARDS[i][2],
        })
    return out


def apply(doc, roster, rs):
    claim = claim_of(doc)
    impressions = [im["issue_id"] for im in roster["impressions"]]
    for r in rs:
        ent = claim["entities"][r["entity"]]
        ent["normalized"] = r["at_image"]
        ent["reading"] = "scan_verified"
        ent["read_at_image"] = {
            "ticket": "T-1138",
            "roster": "data/research/newspapers/letter_list_1834_04_01_contested_lines.json",
            "impressions_read": impressions,
            "as_printed_at_image": r["at_image"],
            "at_each_impression": r["at_each_impression"],
            "was_normalized": r["was"],
            "overturns": r["overturns"],
        }
    if CLAIM_NOTE.strip() not in (claim.get("notes") or ""):
        claim["notes"] = (claim.get("notes") or "") + CLAIM_NOTE
    return doc


def check():
    roster = load_roster()
    doc = load_extracted()
    claim = claim_of(doc)
    rs = rows(roster, doc)
    fail = []

    seen_pages = {im["jp2_page"] for im in roster["impressions"]}
    if len(seen_pages) != len(roster["impressions"]):
        fail.append("two impressions name the same jp2 page")
    if len(roster["impressions"]) < 3:
        fail.append("the reading rests on %d impression(s) and the ticket read three"
                    % len(roster["impressions"]))
    for im in roster["impressions"]:
        if not im["iiif_base"].endswith(im["jp2_page"].split("/")[-1]):
            fail.append("%s: the IIIF base does not end at its own jp2 page" % im["issue_id"])
        if not any(im["regions_read"].values()):
            fail.append("%s: no region is recorded" % im["issue_id"])

    for line in roster["lines"]:
        dates = {im["date"] for im in roster["impressions"]}
        if set(line["at_each_impression"]) != dates:
            fail.append("entity %d is not read at every impression" % line["entity"]["index"])
        if line["verdict"] == "settled" and not line["as_printed_at_image"]:
            fail.append("entity %d is settled and carries no reading"
                        % line["entity"]["index"])

    for r in rs:
        ent = claim["entities"][r["entity"]]
        tie = ent.get("read_at_image")
        if not tie:
            fail.append("%s entity %d carries no read_at_image" % (r["claim"], r["entity"]))
            continue
        if ent.get("reading") != "scan_verified":
            fail.append("%s entity %d should carry reading: scan_verified"
                        % (r["claim"], r["entity"]))
        if ent.get("normalized") != r["at_image"]:
            fail.append("%s entity %d is normalized `%s` and the image sets `%s`"
                        % (r["claim"], r["entity"], ent.get("normalized"), r["at_image"]))
        if tie.get("was_normalized") != r["was"]:
            fail.append("%s entity %d does not record what it overturned"
                        % (r["claim"], r["entity"]))

    read = {r["entity"] for r in rs}
    for i, ent in enumerate(claim["entities"]):
        if i not in read and ent.get("reading") == "scan_verified":
            fail.append("%s entity %d is not one of the three and claims the scan" % (CLAIM, i))
    if claim.get("reading") == "scan_verified":
        fail.append("%s is 79/82 transcription-mediated and must not claim the scan" % CLAIM)

    for r in rs:
        gone, stands = r["card_withdrawn"], r["card_minted"]
        if gone and (HOUSEHOLDS / (gone + ".json")).exists():
            fail.append("%s was withdrawn at the image and its card is still committed" % gone)
        if stands and not (HOUSEHOLDS / (stands + ".json")).exists():
            fail.append("the image sets `%s` and %s is not committed" % (r["at_image"], stands))

    for f in fail:
        print("FAIL  %s" % f)
    if not fail:
        moved = [r for r in rs if r["card_minted"]]
        print("ok    %d contested line(s) read at %d impression(s); %d card(s) withdrawn and "
              "re-minted at the image" % (len(rs), len(roster["impressions"]), len(moved)))
    return 1 if fail else 0


def report(rs, roster):
    print("THE THREE CONTESTED LINES OF THE 1 APRIL 1834 RETURN, AT THE PAGE (T-1138)")
    print("  read at %d impressions of the return: %s"
          % (len(roster["impressions"]),
             ", ".join("%s (%s)" % (im["date"], im["jp2_page"].split("/")[-1])
                       for im in roster["impressions"])))
    for r in rs:
        print("\n  %s entity %d" % (r["claim"], r["entity"]))
        print("    minted as        %s" % r["was"])
        print("    at the image     %s   [%s, overturns %s]"
              % (r["at_image"], r["verdict"], r["overturns"]))
        for d, v in r["at_each_impression"].items():
            print("      %s       %s" % (d, v))
        if r["card_withdrawn"] or r["card_minted"]:
            print("    card             %s -> %s"
                  % (r["card_withdrawn"] or "(none)", r["card_minted"] or "(none)"))
        print("    %s" % r["card_note"])
    obs = roster["seen_in_passing"]
    print("\n  SEEN IN PASSING, applied by nothing: %d line(s) the extraction carries no entity "
          "for, %d reading(s) the image disagrees with."
          % (len(obs["lines_the_1834_04_01_extraction_carries_no_entity_for"]),
             len(obs["entities_whose_reading_the_image_disagrees_with"])))


def self_test():
    roster = load_roster()
    lines = {l["entity"]["index"]: l for l in roster["lines"]}
    assert set(lines) == {58, 59, 60}, sorted(lines)
    assert all(l["entity"]["claim"] == CLAIM for l in roster["lines"])
    assert lines[58]["as_printed_at_image"] == "Benjamin Smith"
    assert lines[59]["as_printed_at_image"] == "Ira Saymore"
    assert lines[60]["as_printed_at_image"] == "Geo. Squar"
    # the reading that matters: the page is not Saver, and it is not Square either
    assert "Saver" not in lines[60]["as_printed_at_image"]
    assert not lines[60]["as_printed_at_image"].endswith("Square")
    # three impressions, three different leaves, all of the Apr-May 1834 scan
    leaves = [im["jp2_page"] for im in roster["impressions"]]
    assert len(set(leaves)) == 3 == len(leaves), leaves
    assert all("Apr1834-May1834" in p for p in leaves)
    assert {im["date"] for im in roster["impressions"]} == {
        "1834-04-01", "1834-04-08", "1834-04-16"}
    # every settled line is settled at every impression, and none of them is left blank
    for l in roster["lines"]:
        assert l["verdict"] == "settled", l
        assert len(l["at_each_impression"]) == 3
        assert all(v for v in l["at_each_impression"].values())
    # a withdrawal is never silent: each moved line names both sides of the move
    for i, (gone, stands, why) in CARDS.items():
        assert why, i
        assert (gone is None) == (stands is None), i
    assert CARDS[59][0] == "hh_raymore_ira" and CARDS[59][1] == "hh_saymore_ira"
    assert CARDS[60][0] == "hh_square_geo" and CARDS[60][1] == "hh_squar_geo"
    # and the assertions fire when the roster is broken
    for break_it in (
        lambda r: r["lines"].pop(),
        lambda r: r["impressions"].pop(),
        lambda r: r["lines"][2].__setitem__("as_printed_at_image", "Geo. Square"),
    ):
        broken = load_roster()
        break_it(broken)
        fired = False
        try:
            b = {l["entity"]["index"]: l for l in broken["lines"]}
            assert set(b) == {58, 59, 60}
            assert len({im["jp2_page"] for im in broken["impressions"]}) == 3
            assert not b[60]["as_printed_at_image"].endswith("Square")
        except (AssertionError, KeyError):
            fired = True
        assert fired, "an assertion does not fire when the roster is broken"
    print("1 April 1834 contested-lines self-test: all assertions fire")
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
    roster = load_roster()
    if a.apply:
        doc = load_extracted()
        rs = rows(roster, doc)
        EXTRACTED.write_text(
            json.dumps(apply(doc, roster, rs), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8")
        print("applied %d image reading(s) to %s" % (len(rs), CLAIM))
        return 0
    rs = rows(roster)
    if a.json:
        print(json.dumps(rs, indent=1, ensure_ascii=False))
        return 0
    report(rs, roster)
    return 0


if __name__ == "__main__":
    sys.exit(main())
