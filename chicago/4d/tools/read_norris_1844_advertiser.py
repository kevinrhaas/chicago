#!/usr/bin/env python3
"""The Advertising Directory of Norris's 1844 Chicago directory, card by card (T-0568).

    tools/read_norris_1844_advertiser.py --build
    tools/read_norris_1844_advertiser.py --check

WHAT THIS IS. T-0566 read the DIRECTORY PROPER of Norris's General Directory of
Chicago for 1844 — 2,073 lines, one printed line each — and committed the whole
volume as page text. The ADVERTISING DIRECTORY at the back of that volume is not a
list: it is 38 pages of display cards, each of them several lines of a firm's name,
its trade, its proprietors and its address, set in whatever type the subscriber paid
for. A line-by-line reader cannot see a card, so the card boundaries are read by eye
and committed in `norris_1844_advertiser_index.json`, and this file turns that index
into claims.

THE QUOTE IS NEVER TYPED. Every quote here is SLICED out of the committed page text
at the card's own line range, so a quote cannot drift from the page it claims to come
from, and the research gate (tools/research_domains.py) rebuilds it again from the
same text and compares. What the reading adds is beside the quote, in `normalized`,
and never inside it.

WHAT IS LEFT OUT IS DECLARED. Section headings, running heads, page numbers, printer's
ornament and the lines the scanner mangled past reading are not inside any card. This
file counts them per leaf and writes them into the output as `uncovered`, so the part
of the page no card reaches is a stated number rather than a silence.

1844 IS NINE YEARS LATE. Every claim carries describes_date 1844. A card is evidence
that a business stood in Chicago in 1844 and is never on its own an 1835 fact; the
crosswalk (tools/crosswalk_norris_1844_advertiser.py) is the only place a name here
touches a person or a trade in the scene of 1 July 1835, and it changes no record.
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = os.path.join(ROOT, "data/research/directories")
INDEX = os.path.join(DOMAIN, "norris_1844_advertiser_index.json")
TEXT = os.path.join(DOMAIN, "text")
OUT = os.path.join(DOMAIN, "claims/norris_1844_advertiser.json")

# Printed page = leaf - 10 through the advertiser, which is how T-0566 read the
# directory proper too (printed 21 is leaf 31). Norris's own card is the exception:
# it sits at the foot of printed page 65, on leaf 75, inside the directory proper.
def printed_page(leaf: int) -> int:
    return leaf - 10


def leaf_text(leaf: int):
    path = os.path.join(TEXT, "norris_1844_leaf_%03d.txt" % leaf)
    if not os.path.exists(path):
        raise SystemExit("advertiser: leaf %d is not committed at %s" % (leaf, path))
    return open(path, encoding="utf-8").read().splitlines()


def build():
    index = json.load(open(INDEX, encoding="utf-8"))
    cards = index["cards"]
    claims, problems = [], []
    covered = {}
    for n, card in enumerate(cards, 1):
        leaf = card["leaf"]
        lines = leaf_text(leaf)
        first, last = card["lines"]
        if first < 1 or last < first or last > len(lines):
            problems.append("card %d names lines %d-%d of leaf %d, which has %d"
                            % (n, first, last, leaf, len(lines)))
            continue
        seen = covered.setdefault(leaf, set())
        overlap = seen & set(range(first, last + 1))
        if overlap:
            problems.append("card %d on leaf %d re-reads line(s) %s, which another card "
                            "already covers — two cards cannot own one line"
                            % (n, leaf, sorted(overlap)))
        seen |= set(range(first, last + 1))
        quote = "\n".join(lines[first - 1:last])
        firm = card["firm"]
        entities = [firm] if firm else []
        entities += [p for p in card["proprietors"] if p not in entities]
        claims.append({
            "id": "n1844_ad%04d" % n,
            "kind": "business",
            "reading": index["reading"],
            "quote": quote,
            "normalized": {
                "firm": firm,
                "proprietors": card["proprietors"],
                "trade": card["trade"],
                "address": card["address"],
                "dated_statement": card["dated_statement"],
                "section": index["section"],
            },
            "locator": {
                "text_file": "norris_1844_leaf_%03d.txt" % leaf,
                "lines": [first, last],
                "page": "norris_1844_leaf_%03d" % leaf,
                "printed_page": printed_page(leaf),
            },
            "describes_date": "1844",
            "entities": entities,
            "town_finding": False,
            "notes": card["notes"],
        })

    # What no card reaches, per leaf, said out loud.
    uncovered = []
    for leaf in sorted(covered):
        # Leaf 75 is a directory-proper page: everything on it but Norris's own card
        # at its foot was read by T-0566, so it has no hole for this ticket to report.
        if leaf < 89:
            continue
        lines = leaf_text(leaf)
        missed = [i for i in range(1, len(lines) + 1)
                  if i not in covered[leaf] and lines[i - 1].strip()]
        if missed:
            uncovered.append({
                "page": "norris_1844_leaf_%03d" % leaf,
                "printed_page": printed_page(leaf),
                "lines": missed,
                "text": [lines[i - 1] for i in missed],
            })

    if problems:
        for p in problems:
            print("advertiser: " + p, file=sys.stderr)
        return None

    named = sum(1 for c in claims if c["normalized"]["firm"])
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_norris_1844_advertiser.py --build out of the "
                "committed page text and the hand-read card index "
                "norris_1844_advertiser_index.json. One claim per advertising card, "
                "quote sliced verbatim from the page, the reading beside it. 1844, not "
                "1835 — see norris_1844_advertiser_crosswalk_1835.json.",
        "generated_by": "tools/read_norris_1844_advertiser.py --build",
        "source_id": index["source_id"],
        "section": index["section"],
        "what": index["what"],
        "reading_note": "transcription_mediated throughout, exactly as the directory "
                        "proper is: archive.org's OCR of the printed page, not checked "
                        "against the image by eye. Display type is what OCR reads worst, "
                        "and this section is all display type — the damage is left in "
                        "every quote and the repair, where one is safe, is in normalized.",
        "counts": {
            "cards": len(claims),
            "cards_with_a_firm_name": named,
            "cards_whose_heading_the_scan_lost": len(claims) - named,
            "proprietors_named": sum(len(c["normalized"]["proprietors"]) for c in claims),
            "cards_carrying_a_date": sum(1 for c in claims
                                         if c["normalized"]["dated_statement"]),
            "leaves": len(covered),
            "advertiser_lines_no_card_reaches": sum(len(u["lines"]) for u in uncovered),
        },
        "uncovered_note": "Every advertiser line (leaves 89-126) that no card covers, "
                          "with its text, so the part of the page the reading does not "
                          "reach is a stated number and can be checked. They are running "
                          "heads, page numbers, the ornamental section headings, and two "
                          "fragments the scan tore off the cards they belonged to.",
        "uncovered": uncovered,
        "claims": claims,
    }


def main():
    doc = build()
    if doc is None:
        return 1
    if "--check" in sys.argv:
        if not os.path.exists(OUT):
            print("advertiser: %s is not committed" % OUT, file=sys.stderr)
            return 1
        if json.load(open(OUT, encoding="utf-8")) != doc:
            print("advertiser: the committed claims do not match the index and the page "
                  "text — rebuild with --build", file=sys.stderr)
            return 1
        print("advertiser: %d cards match the committed file" % doc["counts"]["cards"])
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(doc["counts"], indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
