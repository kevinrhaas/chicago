#!/usr/bin/env python3
"""Read the Newberry Library's Genealogical Index for its Chicago, Cook County and
Illinois cards, and turn them into leads and a reading order (T-0562).

    tools/read_newberry_index.py --extract --volume 1 --pdf <path>
    tools/read_newberry_index.py --parse   --volume 1
    tools/read_newberry_index.py --check
    tools/read_newberry_index.py --self-test

WHAT THE SOURCE IS, AND WHAT IT IS NOT. *The Genealogical Index of the Newberry
Library, Chicago* (G. K. Hall, 1960) is a four-volume photostat of the Newberry's
genealogical card index: hundreds of thousands of cards, each a family surname over
one line naming a locality, the work that treats the family there, its author, its
date and the pages, then the Newberry call number. It is a FINDING AID. A card never
places a person in Chicago in 1835 — it says WHERE A BOOK IS that might. So nothing
here grades a resident, a household or a business, and nothing here is payload; the
product of this file is a ranked list of books to open, and the surnames each one
may bear on.

The owner has put all four volumes on the Internet Archive under the identifier
`chicago1835-newberry-genealogical-index`, and that identifier is the canonical
locator: he is moving the research corpus there item by item, and a source record
that names the IA identifier survives the move where one naming a local path does
not.

HOW THE CARDS ARE READ, AND WHY IT IS DONE THIS WAY. The volumes carry a text
layer, and it is a poor one — the photostat is of typed and hand-corrected cards,
and the OCR of it drops letters, splits words and mangles diacritics ('Aldrich
family.' comes back as 'Aldrod foully.', 'Aldre,1 f a m i l y .' and worse). Worse
for a parser, `pdftotext -layout` reads the whole page as one text block and weaves
FOUR columns of cards into single lines, so a heading and the citation under it end
up in different lines with two other cards' text between them.

The repair is to read the page one column at a time. `pdftotext -x/-W` crops the
page before it lays anything out, so a single column comes back in card order:
heading, then the lines of that card, then the next heading. That is what --extract
does — four cropped passes over the whole volume, each card assembled from the
heading that opens it, and only the cards whose body names Chicago, Cook County or
Illinois are kept and committed.

WHAT IS COMMITTED, AND WHAT IS NOT. The four PDFs are ~200 MB each and are NOT
committed; `text/MANIFEST.json` carries each one's size and sha256, the exact crop
boxes, and the sha256 of every intermediate, so --extract can be re-run and shown to
produce the same file. What IS committed is `text/vol_NN_locality_cards.txt`: the
kept cards, verbatim as the text layer gives them, one card per stanza, with the
page and column they were cropped from. Every record's locator names its lines
there, and --check rebuilds every `as_read` out of it and fails on a one-character
difference — the newspapers' rule, and the reason a tidied reading cannot hide here.

THE GRADE. Every record is `transcription_mediated`. A machine's reading of a
photostat of a card is a transcription, and it is a bad one; calling it
`scan_verified` because the machine looked at an image would be exactly the upgrade
the provenance rule forbids. A sample is checked against the rendered page image by
hand and the check is recorded in the README, which is what the grade is worth.

A SHARED SURNAME IS A LEAD, NOT A MATCH — T-0505's discipline, and it binds harder
here than anywhere else in the project, because the index is nothing but surnames.
`leads.json` says which of this project's people COULD be the family a card points
at; it never says one is, and `crosswalk.json` holds no merges at all.
"""
from __future__ import annotations

import argparse
import difflib
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # chicago/4d
DOMAIN = ROOT / "data" / "research" / "newberry_index"
SOURCE_ID = "newberry_genealogical_index"
IA_ITEM = "chicago1835-newberry-genealogical-index"
SCHEMA = 1

# The four volumes as the owner uploaded them. The file names are the Newberry's
# scan ids and are not guessable, so they are written down here rather than derived.
VOLUMES = {
    1: {"file": "FL2091539_CP-130151_01.pdf", "covers": "A - C (as printed on the cards)"},
    2: {"file": "FL2091536_CP-130151_02.pdf", "covers": "C - H (as printed on the cards)"},
    3: {"file": "FL1982465_CP-130151_03.pdf", "covers": "H - P (as printed on the cards)"},
    4: {"file": "130151_04.pdf", "covers": "P - Z (as printed on the cards)"},
}

# The crop boxes, in PDF points, and the reason they overlap. Page widths in volume 1
# run from 689 to 733 points, so a column's left edge moves by up to 44 points across
# the volume; a 200-point window on a 173-point pitch always contains a whole column
# and usually a sliver of its neighbour. The slivers are deduplicated on (page,
# heading, body) after the passes, which is cheaper and safer than measuring every
# page.
CROPS = [(0, 200), (173, 200), (346, 200), (519, 200)]
CROP_HEIGHT = 1100

# What counts as a locality worth keeping, and the four buckets they are sorted into.
# The OCR turns 'Ill.' into '111.', 'lil.', 'IE,' and 'I I I .', and 'Chicago' into
# 'Chicagoj', 'Ciiicigo' and 'ChicagO'; the patterns are written wide on purpose and
# every match is kept verbatim so a false one can be seen and struck.
LOCALITY_BUCKETS = (
    ("chicago", re.compile(r"\bch[il1]{1,2}[ce]a?g[o0]", re.I)),
    ("cook_county", re.compile(r"\bcoo?k\s*c[o0]", re.I)),
    ("illinois_named", re.compile(r"\bill[il1]n[o0][il1]", re.I)),
    # The abbreviation, and it has to be anchored or it is not one. 'Ill.' on a card
    # is always the tail of a locality — 'Cook Co., Ill.', 'Bureau Co., Ill.' — so the
    # pattern demands the comma that precedes it, or the start of the line. Without
    # the anchor, '111' matched page numbers: 'East Haven, Ct. (Dodd, S.) 1624: 111.'
    # is an epitaph page, not Illinois, and forty-odd cards like it were being kept.
    ("illinois_abbreviated",
     re.compile(r"(?:^|[,;])\s*(?:i|1|l)\s*(?:i|1|l)\s*(?:i|1|l)\s*[,.]", re.I)),
)

# The works the Chicago cards point AT. A card's citation is a compressed author-and-
# date, and the same handful of works carry almost all of it; the patterns cluster
# them so `follow_up.json` can rank what to open first. `held` names the source record
# this project already has, when it has one — the point of the ranking is the books it
# does NOT have. An unmatched citation is kept in its own bucket and counted, never
# dropped, because a work nobody wrote a pattern for is exactly what this file is for.
def token_like(body: str, word: str, thresh: float) -> bool:
    """True when some word of the body is a plausible OCR of `word`.

    The citations are a compressed author-and-date and the OCR of them is the worst
    text in the volume: 'Andreas' comes back as 'Andrest', 'Androcs', 'Anurcii',
    'Antlrcas' and 'A.:.!.;c,'. A spelling list would never close, so the works are
    matched on similarity to one canonical spelling, with the threshold written down
    beside each work and deliberately loose — a work wrongly credited with a card
    costs a page of reading; a work that loses one is never opened.
    """
    for tok in re.split(r"[^A-Za-z]+", body):
        t = tok.lower()
        if not t or abs(len(t) - len(word)) > 2:
            continue
        if difflib.SequenceMatcher(None, t, word).ratio() >= thresh:
            return True
    return False


WORKS = [
    {
        "key": "andreas_history_of_chicago",
        "title": "History of Chicago, from the earliest period to the present time",
        "author": "A. T. Andreas",
        "date": "1884-1886",
        # The initials, not the name. 'A. T.' survives the photostat where 'Andreas'
        # does not, and on a Chicago or Cook County card in this index the man with
        # those initials is Andreas.
        "pattern": re.compile(r"\ba\s*[.,;'\u00b4]?\s*t\s*[.,;'\u00b4]", re.I),
        "fuzzy": ("andreas", 0.6),
        "held": "andreas_1884_v1",
        "reachable": "held — the project already cites Andreas from its own source record",
    },
    {
        "key": "moses_kirkland_history_of_chicago",
        "title": "History of Chicago, Illinois",
        "author": "John Moses and Joseph Kirkland",
        "date": "1895",
        "pattern": re.compile(r"k[il1]r[kh][a-z]{0,4}[a-z]?d", re.I),
        "fuzzy": ("kirkland", 0.55),
        "held": None,
        "reachable": "Internet Archive: historyofchicago01mose, historyofchicagov2mose",
    },
    {
        "key": "moses_illinois_historical_and_statistical",
        "title": "Illinois, historical and statistical",
        "author": "John Moses",
        "date": "1888-1892 (the cards' date; the Archive's copies are dated 1889)",
        "pattern": re.compile(r"18[68]8\s*[-\u2013]\s*9[23]", re.I),
        "fuzzy": ("moses", 0.6),
        "held": "moses_illinois_historical_and_statistical",
        "reachable": "held — located and opened for T-0582; Internet Archive "
                     "illinoishistoric01inmose (vol. 1) and illinoishistoricv2mose "
                     "(vol. 2). Reachable and thin: 169 Chicago or Cook cards stand on "
                     "a STATE history whose 1835 sentences are population and revenue",
    },
    {
        "key": "sons_of_the_american_revolution_illinois_1896",
        "title": "Illinois Society, Sons of the American Revolution — year book",
        "author": "Illinois Society, S.A.R.",
        "date": "1896",
        "pattern": re.compile(r"a[mn]\s*[.,]?\s*rev", re.I),
        "fuzzy": ("revolution", 0.6),
        "held": None,
        "reachable": "not yet located — search the Internet Archive and HathiTrust",
    },
    {
        "key": "reynolds_pioneer_history_of_illinois",
        "title": "The pioneer history of Illinois",
        "author": "John Reynolds",
        "date": "1887",
        "pattern": re.compile(r"p[il1][o0]n[eo]{2}r\s+h[il1]s", re.I),
        "fuzzy": ("reynolds", 0.6),
        "held": None,
        "reachable": "Internet Archive: pioneerhistoryi00reyngoog, cihm_12342",
    },
    {
        "key": "fergus_chicago_directory_1839",
        "title": "Chicago directory for 1839 (Fergus' Historical Series)",
        "author": "Robert Fergus",
        "date": "1839, reprinted 1876",
        "pattern": re.compile(r"d[il1]r[eo]ct[o0]ry", re.I),
        "fuzzy": ("directory", 0.7),
        "held": "fergus_chicago_directory_1839",
        "reachable": "held — the project already cites the 1839 directory",
    },
    {
        "key": "century_encyclopedia_of_biography",
        "title": "Encyclopedia of biography of Illinois",
        "author": "Century Publishing and Engraving Co.",
        "date": "1892-1902",
        "pattern": re.compile(r"\benc[yr]|cent[uv]ry", re.I),
        "fuzzy": ("encyclopedia", 0.6),
        "held": None,
        "reachable": "not yet located — search the Internet Archive and HathiTrust",
    },
    {
        "key": "county_histories_kett_and_co",
        "title": "County histories published by H. F. Kett & Co. and its successors",
        "author": "H. F. Kett & Co.",
        "date": "1877-1880",
        "pattern": re.compile(r"\bh[.,]\s*f[.,]?\s*[&4a\u00c4]", re.I),
        "fuzzy": ("kett", 0.6),
        "held": None,
        "reachable": "not yet located — Illinois county histories, several on the Archive",
    },
    {
        "key": "hurlbut_chicago_antiquities",
        "title": "Chicago antiquities",
        "author": "Henry H. Hurlbut",
        "date": "1881",
        "pattern": re.compile(r"h[uv]r[il1]b[uv]t", re.I),
        "fuzzy": ("antiquities", 0.55),
        "held": "hurlbut_chicago_antiquities",
        "reachable": "held — located and opened for T-0582; Internet Archive "
                     "chicagoantiquiti00hurl. TWO cards, and the densest 1830s Chicago "
                     "text of any work in this table: the index is the wrong instrument "
                     "for ranking it",
    },
    {
        "key": "la_salle_book_co_cook_county",
        "title": "The biographical and portrait volumes of Cook County published by "
                 "the La Salle Book Co.",
        "author": "La Salle Book Co.",
        # The cards print 1900 fifty-three times and 1909 once, beside a 1903 and an
        # 1854 that are as likely to be OCR of 1900. T-0582 opened the work: it is the
        # Album of Genealogy and Biography, Cook County, eleventh edition 1899 and
        # thirteenth 1900, and no 1909 Cook County volume of this publisher was found.
        "date": "1899 (11th ed.) and 1900 (13th ed.)",
        "pattern": re.compile(r"la\s*sa[il1]le", re.I),
        "fuzzy": ("salle", 0.7),
        "held": "la_salle_album_of_genealogy_cook_county",
        "reachable": "held — located and opened for T-0582; Internet Archive "
                     "albumofgenealogy1900chic and albumofgenealogy1899lasa. The "
                     "lowest-yield work in this table: about a dozen pre-1840 Chicago "
                     "arrival sentences per edition, under 91 Chicago or Cook cards",
    },
    {
        "key": "wood_1881_chicago_and_its_distinguished_citizens",
        "title": "Chicago and its distinguished citizens; or, The progress of forty "
                 "years",
        "author": "David Ward Wood",
        "date": "1881",
        # The author's surname and initials as the card prints them — 'Wood, D. W.',
        # and the OCR's 'Wood, D. V/.', 'Wood, D, W.' and 'Wood, D. W J'. The YEAR is
        # unusable as a key here: the same eight cards carry it as 1881, I88li, I88I1,
        # 1381 and loWi. Keyed on the initials for the reason Andreas is — the letters
        # survive the photostat and the spelled-out name does not — but tighter, since
        # this needs the surname AND both initials where Andreas needs two letters.
        # No `fuzzy`: 'wood' is four letters and would take Good, Hood, Ward and
        # Woods with it, and `works_of` reads `.get("fuzzy")` for exactly this case.
        "pattern": re.compile(r"w[o0]{2}d\s*[.,;:'\u00b4]?\s*[dbo]\s*[.,;:'\u00b4]?\s*[wv]",
                              re.I),
        "held": "wood_1881_chicago_and_its_distinguished_citizens",
        "reachable": "held — located and opened for T-0582; Internet Archive "
                     "chicagoitsdistin00wood. Its printed pages 23-25 are a continuous "
                     "account of the year 1835 in Chicago",
    },
]

FAMILY_WORDS = ("family", "families", "fam")


# ---------------------------------------------------------------- small helpers

def collapse(s: str) -> str:
    return " ".join(s.split())


def alpha(s: str) -> str:
    return re.sub(r"[^a-z]", "", s.lower())


# ------------------------------------------------- the column sliver (T-0601)
#
# The four crop windows are 200 points wide on a 173-point pitch (CROPS), so every
# window carries the leftmost 27 points of the NEXT column. When a card sits on that
# boundary the pass over column c reads the first few characters of a card the pass
# over column c+1 reads in full, and keeps it as a second, short card of the same
# locality. The dedup in assemble() cannot see it: that keys on (page, heading,
# body) and a truncation is equal to nothing, so the sliver survives and the domain
# counts one card twice.
#
# MEASURED on the committed reading before the rule was written. The sliver's body
# is a BYTE-EXACT prefix of the full card's body, because it is the same ink read
# twice by the same engine — the reader's own errors come through verbatim ('Pike
# Ce, III.', 'Fua Co., III.', 'Chicago, in.'). That exactness is the whole test.
# Matching on alpha() instead, which drops the digits and the stops, admits two
# DIFFERENT cards that cite the same county history: 'Sangamon Co, III. (Power, J.
# C.) 1878.' and '... (Power, J. C.) I876.' are one string under alpha() and are two
# readings on the leaf.
#
# The figure the rule was earned on: 9 pairs over the four volumes, every one of
# them at column delta +1 and NONE at any other delta — which is the crop geometry's
# own prediction, and is why the adjacency clause is in the rule rather than assumed.
# The same test run without the adjacency clause and folded through alpha() finds 17,
# of which 8 are two cards sharing a citation.
#
# A sliver is MARKED, never dropped. Three reasons, and all three are load-bearing:
# the record id is positional, so striking one renumbers every card after it and
# orphans precision_sample.json's hand-adjudications and lead_crosswalk.json's
# rulings; the sliver is real ink that was really read, and check() rebuilds every
# `as_read` out of the committed text, which still carries it; and a wrong call
# stays visible and reversible instead of silently deleting a card.
SLIVER_MIN_GAP = 8
_SLIVER_LEAD = re.compile(r"^[^0-9A-Za-z]+")


def sliver_core(body: str) -> str:
    """A body with its leading rule-dashes and specks off — collapsed, but NOT
    alpha-folded: the comparison has to keep the digits and the stops."""
    return _SLIVER_LEAD.sub("", collapse(body))


def find_slivers(cards: list) -> dict:
    """{index of a sliver: index of the card it is a truncated copy of}.

    `cards` is the committed reading of one volume, in the order the records are
    numbered — read_committed_cards() order.
    """
    bypage = {}
    for i, card in enumerate(cards):
        bypage.setdefault(card["page"], []).append(i)
    out = {}
    for idxs in bypage.values():
        for i in idxs:
            a = cards[i]
            head = sliver_core(a["body"])
            if len(head) < 4:
                continue
            for j in idxs:
                if j == i or cards[j]["column"] != a["column"] + 1:
                    continue
                full = sliver_core(cards[j]["body"])
                if len(full) >= len(head) + SLIVER_MIN_GAP and full.startswith(head):
                    out[i] = j
                    break
    return out


# ------------------------------------------- the bled-in body (T-0769)
#
# The mirror of the sliver, off the same 27-point overlap and read from the other
# end. A volume's pages are not all the same width — 689 to 733 points — and the
# crop windows are fixed, so on a WIDE page every column's ink sits further right
# than the boxes assume and the left edge of window c+1 falls INSIDE column c. The
# window then reads the right-hand part of column c's lines: not as a card of its
# own, which is what the prefix half does, but glued to the FRONT of the card it
# assembles, heading line and body line alike. The locality patterns then match on
# text that is not on that card.
#
# MEASURED before the rule, and the measurement is what fixed its two clauses.
# Asking, over the four volumes' 6,658 committed cards, whether a body OPENS with a
# byte-exact run that CLOSES another body on the same page:
#
#   run >= 15 chars | 21 pairs | 21 at column delta -1 | 0 at 0, +1, +-2, +-3
#
# against an ordered same-page pair population of 15,518 at delta 0 and 2,517 at
# delta +1. The concentration is the crop geometry's own prediction and is the
# evidence that the two readings are the same ink, exactly as in T-0601.
#
# WHY 15 AND NOT 6. The ticket's first pass asked for a run of six and found 117
# candidates, which is an upper bound and not a measurement: at six characters most
# hits are two unrelated cards that both carry `Chicago,` or `Illinois`. The floor
# is not chosen for tidiness — it is CALIBRATED on T-0601's own nine slivers, whose
# bodies are the entire yield of the 27-point overlap and run 11 to 14 characters.
# A shared run longer than 14 is therefore longer than the overlap alone has ever
# been observed to carry, and cannot be the prefix artefact wearing this shape. At
# or below 14 the two halves are indistinguishable from the string, and this rule
# says nothing about them rather than guessing.
#
# THE SECOND DISCRIMINATOR, and it is what stops the rule marking the wrong card.
# The string relation is symmetric: `A opens with B's tail` is also what the PREFIX
# bleed looks like when column c has ink on that line, and there the contaminated
# card is B, not A. The window that slices column c's body line slices its HEADING
# line at the same x, so a card carried in by this artefact opens mid-word — its
# heading is a fragment beginning in lower case (`nner` out of `Brenner`, `lus` out
# of `Broslus`, `berta` out of `Roberts`). Over all 6,658 cards 1,019 headings begin
# in lower case, a base rate of 15.3 per cent; over the 21 long-run pairs, 15 do —
# 71 per cent, an enrichment of 4.7x. The six refused by this clause are the check
# that it is the right way round: one of them, `nbi_v02_1830`, is a precision-sample
# row hand-adjudicated `locality_correct` off the leaf image, with the county and
# the state read on the card. Marking it would have contradicted a reading made by
# eye.
#
# A bled card is MARKED, never trimmed, and the reasons are T-0601's plus one more
# that is decisive here: MANIFEST.text_sha256 binds the committed text and check()
# rebuilds every `as_read` out of it, so cutting the run off a body is a gate
# failure and not an edit. The record keeps its id and its verbatim reading, gains
# `bleed_of` and `bleed_run`, and is withheld from the volume's counts, its leads
# and its reading order — because all 15 name a locality ONLY inside the run, which
# is to say they were kept for text that is not on them.
BLEED_MIN_RUN = 15
_FIRST_LETTER = re.compile(r"[A-Za-z]")


def heading_is_cut(heading: str) -> bool:
    """True when a heading opens mid-word — the window's left edge sliced it.

    An index heading is a surname and is printed capitalised. A heading whose first
    letter is lower case is a fragment of one, which is what a crop box landing
    inside the previous column leaves behind.
    """
    m = _FIRST_LETTER.search(heading or "")
    return bool(m) and m.group(0).islower()


def shared_run(a_body: str, b_body: str) -> int:
    """The longest run `a` OPENS with that `b` CLOSES with, byte-exact.

    Proper at both ends: a run that is the whole of either body is two cards reading
    the same, which is a duplicate and not a bleed — page 363 of volume 1 carries
    `Sangamon Co., III. (Power, J. C.) 1876.` twice, in two columns, and it is two
    readings of two cards citing one county history.
    """
    a, b = collapse(a_body), collapse(b_body)
    for length in range(min(len(a), len(b)) - 1, 0, -1):
        if a[:length] == b[-length:]:
            return length
    return 0


def find_bleeds(cards: list) -> dict:
    """{index of a bled card: (index of the card whose tail bled in, run length)}.

    `cards` is one volume's committed reading in record order, and each card needs
    its `heading` as well as its body: the heading is half the test.
    """
    bypage = {}
    for i, card in enumerate(cards):
        bypage.setdefault(card["page"], []).append(i)
    out = {}
    for idxs in bypage.values():
        for i in idxs:
            a = cards[i]
            if not heading_is_cut(a.get("heading") or ""):
                continue
            best = None
            for j in idxs:
                if j == i or cards[j]["column"] != a["column"] - 1:
                    continue
                length = shared_run(a["body"], cards[j]["body"])
                if length >= BLEED_MIN_RUN and (best is None or length > best[1]):
                    best = (j, length)
            if best:
                out[i] = best
    return out


# ------------------------------------------- scanning a reading for slivers (T-0810)
#
# find_slivers() tests a byte-exact prefix, and that test is right for a TEXT-LAYER
# reading and inapplicable to an OCR one. Volumes 1-3 come out of `pdftotext` on four
# crop boxes: the sliver and the full card are the same ink returned twice by the same
# extraction, so the reader's own errors come through verbatim on both and the prefix
# is exact to the byte. Volume 4 was re-read by OCR (T-0775): its two readings of the
# overlap are two tesseract runs over two separately rendered images, so a real sliver
# there would agree CLOSELY and never exactly. A zero out of the byte-exact rule
# therefore says nothing at all about an OCR volume — which is the whole of T-0810,
# because volume 4 has been sitting on `slivers: 0` since it was re-read.
#
# So the volume is scanned by a second measure that does not care which engine made the
# characters: positional agreement over the two bodies' common prefix. It separates
# cleanly on the readings this domain already holds — every one of the eight slivers in
# volumes 1-3 scores 1.000, the closest column-boundary pair that is NOT a sliver
# scores 0.921 (nbi_v02_1738 against nbi_v02_1741, two cards citing one work), and all
# 21 of volume 4's boundary pairs score 0.216 or below.
#
# The measure REPORTS, it does not mark. Nothing between 0.921 and 1.000 has ever been
# seen, so no threshold for marking an inexact sliver has been earned, and inventing
# one would strike cards on a number no reading has tested. What the scan does instead
# is put the figures in the records file, where check() re-derives them: a volume's
# zero is then a zero that was MEASURED on the text it is committed beside, and a
# re-read that starts producing slivers moves the numbers and fails the gate.


def prefix_agreement(a: str, b: str) -> float:
    """Positional character agreement over two bodies' common prefix, 0.0 - 1.0."""
    n = min(len(a), len(b))
    if not n:
        return 0.0
    return sum(1 for k in range(n) if a[k] == b[k]) / n


def boundary_pairs(cards: list) -> list:
    """Every (i, j) on one page where j sits in the column to i's right.

    The population find_slivers() draws from, minus its early `break`: the scan has to
    see all of them to report the closest, so it cannot stop at the first match.
    """
    bypage = {}
    for i, card in enumerate(cards):
        bypage.setdefault(card["page"], []).append(i)
    out = []
    for idxs in bypage.values():
        for i in idxs:
            if len(sliver_core(cards[i]["body"])) < 4:
                continue
            for j in idxs:
                if j == i or cards[j]["column"] != cards[i]["column"] + 1:
                    continue
                if len(sliver_core(cards[j]["body"])) < 4:
                    continue
                out.append((i, j))
    return out


def scan_slivers(cards: list, ids: list, read_by: str) -> dict:
    """What the sliver rule found in this reading, and how close it came otherwise."""
    pairs = boundary_pairs(cards)
    best, on = 0.0, None
    for i, j in pairs:
        r = prefix_agreement(sliver_core(cards[i]["body"]), sliver_core(cards[j]["body"]))
        if r > best:
            best, on = r, [ids[i], ids[j]]
    return {
        "_doc": "GENERATED by --parse and re-derived by --check. The column-boundary "
                "pairs this reading offers, how many are byte-exact slivers under the "
                "T-0601 rule, and the closest pair that is not one. A zero in "
                "`byte_exact` means nothing on its own for an OCR reading, where the "
                "two readings of the overlap cannot be byte-identical; "
                "`max_prefix_agreement` is what says whether there was anything to "
                "find. See the comment above scan_slivers() (T-0810).",
        "read_by": read_by,
        "boundary_pairs": len(pairs),
        "byte_exact": len(find_slivers(cards)),
        "max_prefix_agreement": round(best, 3),
        "max_prefix_agreement_on": on,
    }


def read_by_of(volume: int, domain: Path = None) -> str:
    """How this volume's committed text was made, per MANIFEST.json."""
    path = (domain or DOMAIN) / "text" / "MANIFEST.json"
    if not path.exists():
        return "unknown"
    entry = (load(path).get("volumes") or {}).get(str(volume)) or {}
    return entry.get("read_by") or "unknown"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def heading_of(line: str):
    """The surname a card heading carries, or None when the line is not a heading.

    A heading is a short line with no digits whose last word or two is some OCR of
    'family'. The word is matched by similarity rather than by a spelling list
    because there is no end to the spellings: 'faaily', 'ramlly', 'fnnl'v', 'foully',
    'f a m i l y' with a space between every letter. Everything before it is the
    surname as printed, kept verbatim.
    """
    s = collapse(line)
    if not s or len(s) > 70 or re.search(r"\d", s):
        return None
    toks = s.split()
    if not toks:
        return None
    # Largest tail first. The OCR puts a space between every letter often enough
    # that 'Abbott f a m i l y .' is eight tokens, and a short tail matches too:
    # 'm i l y .' reads as 0.8 of 'family' and would leave the surname as
    # 'Abbott f a'. The longest tail that matches is the word, and the rest is the
    # name.
    for k in range(min(8, len(toks)), 0, -1):
        tail = alpha("".join(toks[-k:]))
        if not tail:
            continue
        for word in FAMILY_WORDS:
            if abs(len(tail) - len(word)) > 2:
                continue
            if difflib.SequenceMatcher(None, tail, word).ratio() < 0.72:
                continue
            head = collapse(re.sub(r"[^A-Za-z',\- ]", " ", " ".join(toks[:-k])))
            if len(alpha(head)) < 3:
                return None
            # A heading is one family, occasionally two spellings of it ('Aldridge,
            # or Oldridge family.'). More than four words is a body line the OCR has
            # broken, not a heading.
            if len(head.split()) > 4:
                return None
            return head
    return None


# The one systematic false positive a hand-adjudicated sample of forty cards found,
# and it is worth a rule rather than a shrug. The index carries thousands of English
# cards citing the *Calendarium Inquisitionum post mortem*, whose entries are filed by
# regnal year — 'Calendarium, Hen. III. and Edw. I' — and a comma followed by 'III.'
# is exactly the shape of 'Cook Co., Ill.'. A regnal abbreviation in front of the
# stroke is what tells them apart.
REGNAL = re.compile(r"(?:hen|edw|ric|[gc]eo|jas|el[il1]z|wm|w[il1]ll|chas|vol)\s*[.,]?\s*$",
                    re.I)


# The second and third systematic false positives, both found by T-0578's forty-card
# draw on volume 2 and both absent from volume 1's draw (T-0600). They sit here, beside
# REGNAL, because they are the same kind of thing: a locality pattern matching something
# that is not a locality, and a written reason for telling them apart.

# ONE — THE STATE BANNER, AND ANY OTHER BODY THAT NAMES ONLY THE PLACE. The printed
# index divides a family's run of cards by state with a rule on its own line,
# 'ILLINOIS.'. `assemble` opens a card at a heading and hangs the lines under it on
# that card, so a banner falling directly beneath a heading becomes that card's whole
# body and the stanza is kept for a locality no card of that family claims —
# nbi_v02_1675 is the proof: its heading is 'Kinge or King family.', whose one card is
# an English parish register, and the surname run that opens under the banner is
# KINGERY. The same shape catches the wreck of the call-number column, '111. P 85132.8'.
#
# The test is not the spelling of the banner but what is missing: a card body is a
# CITATION — an author, a date, a title — and this domain's whole product is a list of
# books to open. Strip the locality the patterns matched and a real card still has
# words left; a banner has nothing. So a stanza whose body is the locality and no more
# names no work, can never become a lead, and is refused.

# TWO — THE STROKE STANDING WHERE THE CALL NUMBER STANDS. `illinois_abbreviated` is
# anchored to a comma or to the start of the line, and the start-of-line branch is
# there for a locality that wrapped: '..., Cook Co.,' on one line and 'Ill. (Andreas,
# A. T.) 1884-6' on the next. The left of a card also carries its call number, though
# ('543.7 LaSalle Co., Ill.'), and three strokes of a wrecked one read as 'III,' —
# nbi_v02_1106, whose card is 'Holden family. — Hapgood fam. (Hapgood, W.) 1898. See
# index. E. 7. H 21' and names no locality at all.
#
# What tells the two apart is what FOLLOWS. A wrapped locality is followed by its
# citation; a stroke in the call-number slot is followed by the next card's own family
# heading, because the crop has caught the head of a stanza and not the tail of one. So
# a start-of-line stroke with a family word behind it, before any citation opens, is
# refused. (The ticket proposed testing what PRECEDES the stroke instead. On the page
# there is nothing before it — the stroke IS the call number — so the test is the other
# way round; the measurement is written up in the PR.)
FAMILY_AFTER = re.compile(r"\b(?:f\s*a\s*m\s*[il1][il1]?\s*[yv]|fam|faml|famly)\b\s*[.,]?",
                          re.I)


def call_number_slot(body: str, m) -> bool:
    """True when a start-of-line stroke is a call number and not a wrapped locality."""
    if m.start() != 0:
        return False
    rest = body[m.end():]
    cut = rest.find("(")
    return bool(FAMILY_AFTER.search(rest if cut < 0 else rest[:cut]))


# THREE — THE PAGE NUMBER STANDING WHERE THE STATE STANDS (T-0765, measured by
# T-0600 and left undone there). A card's citation ends in the pages the surname is
# on, printed as a comma-separated list — '1897: 130,111,183,186,371' — and 111 is a
# page in that list, not Illinois. The anchor `illinois_abbreviated` needs is the
# comma the list itself supplies, so every page list that happens to reach page 111
# is kept as an Illinois card. So is the illustration note: '(Delano, J. A.) 1899:
# 203,ill.' is page 203, illustrated.
#
# WHAT THE RULE MAY NOT BE. T-0600 measured the obvious one — refuse when a digit
# precedes the comma — and refused to ship it, because this OCR reads a trailing 'o'
# as '0' and '««g0, III.' and '> — Chiear.0, 111.,' are both *Chicago, Ill.* Both are
# a SINGLE digit, and both sit against a letter or a stop that a real number would
# not. So the shape tested is narrower: a run of TWO OR MORE digits, ending at the
# anchor, with no letter immediately in front of it. A page list always presents that
# shape; a wrecked 'Chicago' presents one digit, because it is one letter that fell.
#
# WHAT IT STRIKES, per volume, over the committed text of 2026-09-06: 11 in volume 1,
# 9 in volume 2, 9 in volume 3 and 3 in volume 4 — 32 cards, every one of them read
# against its body and every one a page list or an illustration note. It cannot strike
# a Chicago or Cook County card by construction: it disables one bucket, so a card
# with any other locality bucket keeps it and stays. The stratum genuinely at risk is
# the wrecked 'Chicago' that reaches the file only through the abbreviation, and the
# two the ticket names are the two the digit-run test spares.
#
# WHAT IT DELIBERATELY LEAVES. 21 further candidates precede the anchor with a digit
# and are not struck: mostly page lists whose last run this OCR ran into the word in
# front of it ('1899il09,lll,113.'). Dropping the letter guard would take exactly two
# of them across all four volumes — measured, not guessed — and would spend the one
# test that tells a fallen letter from a number to do it. The trade is refused.
PAGE_LIST_BEFORE = re.compile(r"(?<![A-Za-z])\d{2,}$")


def page_number_slot(body: str, m) -> bool:
    """True when the stroke is a page in the citation's page list, not the state."""
    pre = body[:m.start() + 1]
    if not pre.endswith((",", ";")):
        return False
    return bool(PAGE_LIST_BEFORE.search(pre[:-1]))


# FOUR — THE INQUISITIONS AGAIN, WHERE THE REGNAL YEAR IS TOO WRECKED FOR REGNAL.
# T-0766. REGNAL above tells 'Calendarium, Hen. III. and Edw. I' apart from 'Cook Co.,
# Ill.' by the regnal abbreviation standing in front of the stroke, and that abbreviation
# is three or four letters of the worst text in the volume: it comes back as 'Han,',
# 'Hee,', 'Ken,', 'Ron,' and 'ben,', and the numeral comes back lowercase. So the guard
# fires on the cards whose OCR happened to survive and misses the ones whose OCR did not
# — nbi_v03_0614 is the proof, 'Calendafium, Han, iii. and i n .', volume 1's false
# positive wearing a different wreck.
#
# The discriminator is not the regnal year but the SERIES. Every one of these cards cites
# the same work, `Calendarium Inquisitionum post mortem`, and 'Calendarium' is eleven
# letters where the regnal abbreviation is three — long enough to be recognised through
# the photostat by similarity, which is how this file already matches the works a
# citation names (`token_like`). The threshold is measured, not guessed: at 0.55 it
# strikes 38 cards over the four volumes and every one of them is this series; at 0.50 it
# begins to take real Illinois cards, because 'Blanchard' and 'Cicncharu' — the publisher
# of the DuPage and Sangamon county histories — are as close to 'calendarium' as some of
# these wrecks are. The cost of the rule at 0.55 is zero cards, and the measurement is in
# the README.
CALENDARIUM = ("calendarium", 0.55)


CITATION_YEAR = re.compile(r"(?<!\d)1[5-9]\d\d(?!\d)")


def names_only_the_place(body: str, spans: list) -> bool:
    """True when nothing but the locality is left of the body — no work is cited.

    A citation is an author, a title and a date, and a stanza that has none of them
    points at no book. What survives the locality is tested for both: any word, and
    any four-digit year. The year matters because the OCR loses authors wholesale —
    'Murry f t | Chicago,\'I;....\' . .\' 1895:' is a wrecked reading of a real card,
    and the date is the part of the citation that came through.
    """
    keep, last = [], 0
    for start, end in sorted(spans):
        keep.append(body[last:start])
        last = max(last, end)
    keep.append(body[last:])
    rest = "".join(keep)
    return len(alpha(rest)) <= 1 and not CITATION_YEAR.search(rest)


def buckets_of(body: str):
    out, spans = [], []
    for name, pat in LOCALITY_BUCKETS:
        m = pat.search(body)
        if not m:
            continue
        if name == "illinois_abbreviated" and REGNAL.search(body[:m.start() + 1]):
            continue
        if name == "illinois_abbreviated" and call_number_slot(body, m):
            continue
        if name == "illinois_abbreviated" and page_number_slot(body, m):
            continue
        if name == "illinois_abbreviated" and token_like(body, *CALENDARIUM):
            continue
        out.append(name)
        spans.append((m.start(), m.end()))
    if out and names_only_the_place(body, spans):
        return []
    return out


HEADING_NOISE = ("or", "and", "of", "see", "the", "family", "fam")


def surname_key(printed: str) -> str:
    """The surname a heading is filed under, reduced for comparison only.

    Not the first word. A card heading picks up the tail of its neighbour often
    enough that 'er, E P Adams' is a real reading of an Adams card, and the first
    word of it is 'er'. The key is the LONGEST word of three letters or more that is
    not a joiner — which is 'Adams' there, 'Aldridge' in 'Aldridge, or Oldridge', and
    the whole of a one-word heading. It is a COMPARISON key and never a reading:
    every record keeps the heading verbatim in `as_read`.
    """
    words = [alpha(w) for w in re.split(r"[\s,]+", printed) if alpha(w)]
    words = [w for w in words if len(w) >= 3 and w not in HEADING_NOISE]
    if not words:
        return ""
    return max(words, key=len)



# ---------------------------------------------------------------- extraction

def assemble(columns: dict, pages: int) -> tuple:
    """Cards out of four column texts, and the locality ones kept.

    `columns` maps a crop index to that column's text for every page, in page order —
    exactly what `pdftotext`'s form-feed split gives, and exactly what the OCR path
    rebuilds. Everything downstream of this function is blind to where the characters
    came from, which is the point: the two readers differ only in the reading.
    """
    cards = []
    for pno in range(1, pages + 1):
        for col in sorted(columns):
            page = columns[col][pno - 1] if pno - 1 < len(columns[col]) else ""
            cur = None
            for ln, line in enumerate(page.split("\n"), start=1):
                head = heading_of(line)
                if head is not None:
                    cur = {"page": pno, "column": col, "line": ln,
                           "heading": head, "body": []}
                    cards.append(cur)
                elif cur is not None and collapse(line):
                    cur["body"].append(collapse(line))

    kept, seen = [], set()
    for card in cards:
        for body in card["body"]:
            names = buckets_of(body)
            if not names:
                continue
            key = (card["page"], alpha(card["heading"]), alpha(body))
            if key in seen:
                continue
            seen.add(key)
            kept.append({"page": card["page"], "column": card["column"],
                         "line": card["line"], "heading": card["heading"],
                         "body": body, "buckets": names})
    kept.sort(key=lambda c: (c["page"], c["column"], c["line"], c["body"]))
    return cards, kept


def commit_text(volume: int, kept: list, out_dir: Path) -> tuple:
    """The kept cards, two lines per card, at the locators every record will name."""
    lines = ["# The Newberry Genealogical Index, volume %d — the cards whose body names"
             % volume,
             "# Chicago, Cook County or Illinois, verbatim as the volume's text layer",
             "# gives them. GENERATED by tools/read_newberry_index.py --extract; the",
             "# crop boxes and the source pdf's sha256 are in MANIFEST.json. Two lines",
             "# per card: the heading, then the body line that matched.",
             ""]
    for card in kept:
        card["heading_line"] = len(lines) + 1
        lines.append("p%04d c%d  %s" % (card["page"], card["column"], card["heading"]))
        card["body_line"] = len(lines) + 1
        lines.append("        %s" % card["body"])
    text_name = "vol_%02d_locality_cards.txt" % volume
    text_path = out_dir / text_name
    text_path.parent.mkdir(parents=True, exist_ok=True)
    text_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return text_name, text_path


def write_manifest(volume: int, pdf: Path, out_dir: Path, pages: int, extra: dict,
                   cards: int, kept: int, text_name: str, text_path: Path) -> None:
    spec = VOLUMES[volume]
    manifest_path = out_dir / "MANIFEST.json"
    manifest = load(manifest_path) if manifest_path.exists() else {
        "schema": SCHEMA,
        "_doc": "GENERATED by tools/read_newberry_index.py --extract. The four volumes "
                "are ~200 MB each and are NOT committed; this file is what makes the "
                "committed text reproducible from them.",
        "ia_item": IA_ITEM,
        "ia_url": "https://archive.org/details/" + IA_ITEM,
        "volumes": {},
    }
    entry = {
        "file": spec["file"],
        "covers": spec["covers"],
        "download_url": "https://archive.org/download/%s/%s" % (IA_ITEM, spec["file"]),
        "bytes": pdf.stat().st_size,
        "sha256": sha256_file(pdf),
        "pdf_pages": pages,
        "crop_height": CROP_HEIGHT,
    }
    entry.update(extra)
    entry.update({
        "cards_assembled": cards,
        "locality_cards_kept": kept,
        "text_file": text_name,
        "text_sha256": sha256_file(text_path),
    })
    manifest["volumes"][str(volume)] = entry
    dump(manifest_path, manifest)


def extract(volume: int, pdf: Path, out_dir: Path = None) -> dict:
    """Crop, read, assemble the cards, keep the locality ones, commit the text."""
    out_dir = out_dir or (DOMAIN / "text")
    if not pdf.exists():
        raise SystemExit("no such pdf: %s" % pdf)
    if shutil.which("pdftotext") is None:
        raise SystemExit("pdftotext is not installed — poppler-utils")

    tmp = Path(tempfile.mkdtemp(prefix="newberry_"))
    pass_hashes = []
    columns = {}
    for i, (x, w) in enumerate(CROPS):
        dest = tmp / ("col%d.txt" % i)
        subprocess.run(["pdftotext", "-layout", "-x", str(x), "-y", "0",
                        "-W", str(w), "-H", str(CROP_HEIGHT), str(pdf), str(dest)],
                       check=True)
        text = dest.read_text(encoding="utf-8", errors="replace")
        pass_hashes.append({"column": i, "x": x, "width": w,
                            "sha256": sha256_text(text), "bytes": len(text)})
        columns[i] = text.split("\f")

    pages = max(len(v) for v in columns.values())
    cards, kept = assemble(columns, pages)
    text_name, text_path = commit_text(volume, kept, out_dir)
    write_manifest(volume, pdf, out_dir, pages,
                   {"read_by": "text_layer", "passes": pass_hashes},
                   len(cards), len(kept), text_name, text_path)
    shutil.rmtree(tmp, ignore_errors=True)
    return {"cards": len(cards), "kept": len(kept), "pages": pages}


# ------------------------------------------------------------ the OCR path
#
# WHY THERE IS A SECOND READER, AND WHICH VOLUME NEEDS IT (T-0614). Volume 4 is not the
# same scan as the other three. The Internet Archive item carries volumes 1-3 as
# `FL…_CP-130151_0N.pdf` and volume 4 as `130151_04.pdf`, and volume 4's embedded text
# layer is a much poorer OCR whose word boxes are scattered across the page instead of
# stacked in the four card columns — so cropping to a column, which is the whole trick
# above, no longer isolates one. Run over volume 4 the text-layer path assembles 6,548
# cards and keeps 308 out of 918 pages, against volume 3's 68,552 and 2,131 out of
# 1,004. The page IMAGES are perfectly legible; only the text layer is not. So the
# volume is read by re-reading the images.
#
# WHAT IT DOES NOT CHANGE. The OCR path produces the same four column texts the
# pdftotext path produces and hands them to the same `assemble`. Nothing downstream
# knows the difference, and the grade does not move: `transcription_mediated` was
# already the right grade for a machine reading a photostat, and a second machine
# reading it does not make it stronger.
#
# WHY IT IS RESUMABLE. At the measured rate the volume is about 83 minutes of compute,
# which does not fit in one run's foreground. `--pages A-B` reads a range and commits a
# shard; `--extract --ocr` with no range stitches the shards in page order. A shard
# records the settings it was made with and stitching refuses a set that disagrees,
# because two ranges read at different dpi are two different readings of one volume.

OCR_DPI = 200
OCR_PSM = "6"          # one uniform block of text: a cropped column is exactly that.
OCR_WORKERS = 4
OCR_SHARD_SCHEMA = 1


def write_gz(path: Path, text: str) -> None:
    """gzip with a zeroed header stamp, because the shard is gated on its sha256.

    `gzip.open` writes the current mtime into the header, so the same bytes compress
    to a different file every second and MANIFEST's hash of a shard would never hold.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = text.encode("utf-8")
    with open(path, "wb") as fh:
        with gzip.GzipFile(filename="", mode="wb", fileobj=fh, compresslevel=9,
                           mtime=0) as gz:
            gz.write(raw)


def ocr_engine() -> str:
    """The tesseract build, verbatim, because it is part of what made the characters."""
    if shutil.which("tesseract") is None:
        raise SystemExit("tesseract is not installed — the OCR path needs tesseract-ocr")
    out = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
    return (out.stdout or out.stderr).strip().split("\n")[0].strip()


def ocr_settings(dpi: int = OCR_DPI, psm: str = OCR_PSM) -> dict:
    return {"engine": ocr_engine(), "dpi": int(dpi), "psm": str(psm),
            "crops": [list(c) for c in CROPS], "crop_height": CROP_HEIGHT,
            "render": "pdftoppm -gray -png"}


def _ocr_one_page(job) -> tuple:
    """Render one page's four column strips and read each. Returns (page, [4 texts]).

    OMP_THREAD_LIMIT=1 is not a detail. Tesseract parallelises a single image across
    the cores by itself, so four page workers on a four-core runner oversubscribe it
    three times over and the machine thrashes: measured on this runner, four workers
    at tesseract's default threading did not finish EIGHT pages in ten minutes, and
    the same four workers with the limit set did four pages in 21.7 s — 5.4 s a page
    against 17.5 s a page sequential. Page-level parallelism only pays when the
    engine underneath it is single-threaded.
    """
    pdf, page, dpi, psm, workdir = job
    env = dict(os.environ, OMP_THREAD_LIMIT="1")
    texts = []
    for i, (x, w) in enumerate(CROPS):
        stem = str(Path(workdir) / ("p%05d_c%d" % (page, i)))
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page),
                        "-gray", "-png",
                        "-x", str(round(x * dpi / 72.0)), "-y", "0",
                        "-W", str(round(w * dpi / 72.0)),
                        "-H", str(round(CROP_HEIGHT * dpi / 72.0)),
                        str(pdf), stem], check=True, capture_output=True)
        shot = next(iter(sorted(Path(workdir).glob("p%05d_c%d-*.png" % (page, i)))), None)
        if shot is None:                      # a page the renderer declined to draw
            texts.append("")
            continue
        subprocess.run(["tesseract", str(shot), stem, "--psm", str(psm), "-l", "eng"],
                       check=True, capture_output=True, env=env)
        texts.append(Path(stem + ".txt").read_text(encoding="utf-8", errors="replace"))
        shot.unlink(missing_ok=True)
        Path(stem + ".txt").unlink(missing_ok=True)
    return page, texts


def ocr_pages(pdf: Path, wanted: list, dpi: int = OCR_DPI, psm: str = OCR_PSM,
              workers: int = OCR_WORKERS) -> dict:
    """Read these pages in one parallel batch. Returns {page: [4 column texts]}.

    The batch is the unit that matters for cost: one page handed to four workers is
    one worker's work, and timing that would tell a later run the volume costs three
    times what it does.
    """
    from concurrent.futures import ProcessPoolExecutor
    if shutil.which("pdftoppm") is None:
        raise SystemExit("pdftoppm is not installed — poppler-utils")
    ocr_engine()                      # fail here, not inside a worker, when it is absent
    tmp = Path(tempfile.mkdtemp(prefix="newberry_ocr_"))
    out = {}
    try:
        jobs = [(pdf, page, dpi, psm, str(tmp)) for page in wanted]
        with ProcessPoolExecutor(max_workers=max(1, int(workers))) as ex:
            for page, texts in ex.map(_ocr_one_page, jobs):
                out[page] = texts
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return out


def shard_path(volume: int, first: int, last: int, shard_dir: Path) -> Path:
    return shard_dir / ("vol_%02d" % volume) / ("pages_%04d-%04d.json.gz" % (first, last))


def ocr_range(volume: int, pdf: Path, first: int, last: int, dpi: int = OCR_DPI,
              psm: str = OCR_PSM, workers: int = OCR_WORKERS,
              shard_dir: Path = None) -> Path:
    """Read one page range and commit its shard. The unit a run can actually finish."""
    shard_dir = shard_dir or (DOMAIN / "text" / "ocr")
    if not pdf.exists():
        raise SystemExit("no such pdf: %s" % pdf)
    if shutil.which("pdftoppm") is None:
        raise SystemExit("pdftoppm is not installed — poppler-utils")
    if first < 1 or last < first:
        raise SystemExit("--pages wants A-B with 1 <= A <= B, got %d-%d" % (first, last))

    pages = {str(p): t for p, t in
             ocr_pages(pdf, list(range(first, last + 1)), dpi, psm, workers).items()}

    out = shard_path(volume, first, last, shard_dir)
    out.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"schema": OCR_SHARD_SCHEMA, "volume": volume,
                       "first": first, "last": last,
                       "settings": ocr_settings(dpi, psm),
                       "pdf_sha256": sha256_file(pdf),
                       "pages": pages},
                      ensure_ascii=False, sort_keys=True)
    write_gz(out, body)
    return out


def read_shards(volume: int, shard_dir: Path = None) -> tuple:
    """Every committed shard for a volume, stitched into column texts in page order.

    Returns (columns, pages, settings, shard_records). Refuses a set of shards that
    disagree about the settings or about which pdf they read, and refuses a gap: a
    volume assembled out of ranges that do not cover it is a partial read wearing a
    finished volume's file name, which is exactly what a later run would trust.
    """
    shard_dir = shard_dir or (DOMAIN / "text" / "ocr")
    found = sorted((shard_dir / ("vol_%02d" % volume)).glob("pages_*.json.gz"))
    if not found:
        raise SystemExit("no OCR shards for volume %d under %s — run --extract --ocr "
                         "--pages A-B first" % (volume, shard_dir))
    settings = None
    pdf_sha = None
    by_page = {}
    records = []
    for path in found:
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            doc = json.load(fh)
        if settings is None:
            settings, pdf_sha = doc["settings"], doc.get("pdf_sha256")
        elif doc["settings"] != settings:
            raise SystemExit("%s was read with different settings from %s — two ranges "
                             "read differently are two readings, not one"
                             % (path.name, found[0].name))
        elif doc.get("pdf_sha256") != pdf_sha:
            raise SystemExit("%s read a different pdf from %s" % (path.name, found[0].name))
        for page, texts in doc["pages"].items():
            by_page[int(page)] = texts
        records.append({"shard": path.name, "first": doc["first"], "last": doc["last"],
                        "pages": len(doc["pages"]), "sha256": sha256_file(path)})
    pages = max(by_page)
    missing = [p for p in range(1, pages + 1) if p not in by_page]
    if missing:
        raise SystemExit("pages %s have no shard — the volume is not read yet (%d of %d)"
                         % (fmt_ranges(missing), len(by_page), pages))
    columns = {i: [by_page[p][i] for p in range(1, pages + 1)] for i in range(len(CROPS))}
    records.sort(key=lambda r: r["first"])
    return columns, pages, settings, records


def fmt_ranges(nums: list) -> str:
    """1,2,3,7,8 as '1-3,7-8' — a gap report has to be readable to be acted on."""
    out, start, prev = [], None, None
    for n in sorted(nums):
        if start is None:
            start = prev = n
        elif n == prev + 1:
            prev = n
        else:
            out.append("%d" % start if start == prev else "%d-%d" % (start, prev))
            start = prev = n
    if start is not None:
        out.append("%d" % start if start == prev else "%d-%d" % (start, prev))
    return ",".join(out)


def extract_ocr(volume: int, pdf: Path, out_dir: Path = None,
                shard_dir: Path = None) -> dict:
    """Stitch the committed shards and assemble the volume out of them."""
    out_dir = out_dir or (DOMAIN / "text")
    columns, pages, settings, records = read_shards(volume, shard_dir)
    cards, kept = assemble(columns, pages)
    text_name, text_path = commit_text(volume, kept, out_dir)
    write_manifest(volume, pdf, out_dir, pages,
                   {"read_by": "ocr", "ocr": settings, "ocr_shards": records},
                   len(cards), len(kept), text_name, text_path)
    return {"cards": len(cards), "kept": len(kept), "pages": pages,
            "shards": len(records)}




# ------------------------------------------------------------- the probe (T-0614)
#
# The measurement that justified splitting T-0580, kept as a command rather than a
# paragraph so it can be re-run and disagreed with. It reads a fixed sample of pages
# BOTH ways and reports the ratio; an impression that one reader is better than the
# other is worth nothing next to a count of the cards each one finds on the same page.

PROBE_PAGES = [100, 200, 300, 400, 500, 600, 700, 800]


def text_layer_columns(pdf: Path, first: int, last: int, tmp: Path) -> dict:
    """The pdftotext path's four column texts for one page range."""
    columns = {}
    for i, (x, w) in enumerate(CROPS):
        dest = tmp / ("probe_col%d_%d.txt" % (i, first))
        subprocess.run(["pdftotext", "-layout", "-f", str(first), "-l", str(last),
                        "-x", str(x), "-y", "0", "-W", str(w), "-H", str(CROP_HEIGHT),
                        str(pdf), str(dest)], check=True)
        columns[i] = dest.read_text(encoding="utf-8", errors="replace").split("\f")
    return columns


def probe(volume: int, pdf: Path, sample: list = None, dpi: int = OCR_DPI,
          psm: str = OCR_PSM, workers: int = OCR_WORKERS, out_dir: Path = None) -> dict:
    """Read a fixed page sample both ways and write the comparison as data."""
    import time
    out_dir = out_dir or (DOMAIN / "text")
    sample = sample or PROBE_PAGES
    if not pdf.exists():
        raise SystemExit("no such pdf: %s" % pdf)

    manifest = load(out_dir / "MANIFEST.json")
    others = {v: {"file": d.get("file"), "pdf_pages": d.get("pdf_pages"),
                  "cards_assembled": d.get("cards_assembled"),
                  "locality_cards_kept": d.get("locality_cards_kept"),
                  "read_by": d.get("read_by", "text_layer"),
                  "cards_per_page": round(d["cards_assembled"] / d["pdf_pages"], 1)
                  if d.get("cards_assembled") and d.get("pdf_pages") else None}
              for v, d in sorted(manifest.get("volumes", {}).items())
              if int(v) != volume}

    tmp = Path(tempfile.mkdtemp(prefix="newberry_probe_"))
    rows = []
    try:
        # The whole volume the committed way, into a scratch directory — the figure
        # this is all about, and it has to be the real one over all 918 pages rather
        # than the sample scaled up. Nothing of it is committed.
        whole = extract(volume, pdf, out_dir=tmp / "text_layer")
        t0 = time.time()
        read = ocr_pages(pdf, sample, dpi=dpi, psm=psm, workers=workers)
        ocr_seconds = time.time() - t0
        for page in sample:
            tl = text_layer_columns(pdf, page, page, tmp)
            tl_cards, tl_kept = assemble(tl, 1)
            oc = {i: [read[page][i]] for i in range(len(CROPS))}
            ocr_cards, ocr_kept = assemble(oc, 1)
            rows.append({"page": page,
                         "text_layer": {"cards": len(tl_cards), "kept": len(tl_kept),
                                        "chars": sum(len(c[0]) for c in tl.values())},
                         "ocr": {"cards": len(ocr_cards), "kept": len(ocr_kept),
                                 "chars": sum(len(c[0]) for c in oc.values())}})
        settings = ocr_settings(dpi, psm)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tl_total = sum(r["text_layer"]["cards"] for r in rows)
    ocr_total = sum(r["ocr"]["cards"] for r in rows)
    per_page = ocr_seconds / max(1, len(sample))
    pdf_pages = int(subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                                   text=True).stdout.split("Pages:")[1].split()[0])
    doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_newberry_index.py --probe. Why volume %d is "
                "read by OCR and the other volumes are not, measured on a fixed page "
                "sample read both ways (T-0614)." % volume,
        "volume": volume,
        "file": VOLUMES[volume]["file"],
        "bytes": pdf.stat().st_size,
        "sha256": sha256_file(pdf),
        "pdf_pages": pdf_pages,
        "other_volumes": others,
        "text_layer_whole_volume": {
            "cards_assembled": whole["cards"],
            "locality_cards_kept": whole["kept"],
            "cards_per_page": round(whole["cards"] / whole["pages"], 1),
            "_doc": "What --extract (the pdftotext path every other volume was read "
                    "with) gets off this volume. Compare cards_per_page with "
                    "other_volumes: that gap is the finding. Not committed as a "
                    "reading — see the ticket.",
        },
        "sample": sample,
        "pages": rows,
        "totals": {"text_layer_cards": tl_total, "ocr_cards": ocr_total,
                   "text_layer_kept": sum(r["text_layer"]["kept"] for r in rows),
                   "ocr_kept": sum(r["ocr"]["kept"] for r in rows),
                   "ocr_over_text_layer": round(ocr_total / tl_total, 1) if tl_total
                   else None},
        "ocr_settings": settings,
        "ocr_cost": {"workers": int(workers), "seconds_per_page": round(per_page, 1),
                     "whole_volume_minutes": round(per_page * pdf_pages / 60.0),
                     "_doc": "What a page costs at these settings on the steward "
                             "runner, and what the whole volume would cost. This is "
                             "what T-0615's page ranges are sized from."},
    }
    dump(out_dir / ("vol_%02d_probe.json" % volume), doc)
    return doc


# ---------------------------------------------------------------- the layers

def layer_names() -> dict:
    """Every name this project already holds, by layer, for the lead crosswalk.

    Four layers answer to a surname: the residents (people inside the 825 household
    records), the civic lists (the poll and tax lists of 1833-1835), the 1840 census
    (the heads read off the page images), and the structures whose name carries the
    person who kept them. Nothing else in the project is name-shaped.
    """
    out = {"residents": [], "voters": [], "census_1840": [], "structures": []}

    hh_dir = ROOT / "data" / "residents" / "households"
    for path in sorted(hh_dir.glob("*.json")) if hh_dir.exists() else []:
        doc = load(path)
        for person in doc.get("persons") or []:
            if person.get("name"):
                out["residents"].append({"id": person.get("id") or doc["id"],
                                         "name": person["name"],
                                         "household": doc.get("id")})

    voters = ROOT / "data" / "research" / "civic" / "records" / "voter_lists_1833_1835.json"
    if voters.exists():
        for row in load(voters).get("records") or []:
            out["voters"].append({"id": row.get("id"), "name": row.get("normalized") or
                                  row.get("as_read")})

    pages_dir = ROOT / "data" / "research" / "census_1840" / "pages"
    for path in sorted(pages_dir.glob("*.json")) if pages_dir.exists() else []:
        doc = load(path)
        for row in doc.get("records") or []:
            name = row.get("normalized") or row.get("as_read")
            if name:
                out["census_1840"].append({
                    "id": "%s:l%s" % (doc.get("familysearch_id") or path.stem,
                                      row.get("line")),
                    "name": name})

    st_dir = ROOT / "data" / "structures"
    for path in sorted(st_dir.glob("*.json")) if st_dir.exists() else []:
        doc = load(path)
        if doc.get("name"):
            out["structures"].append({"id": doc.get("id") or path.stem, "name": doc["name"]})
    return out


# The surname of a name as this project writes it: the last word that is not a
# suffix. 'W. H. Adams' -> adams; 'John Bates Jr.' -> bates; 'Col. Jean Baptiste
# Beaubien' -> beaubien. A structure name is a phrase ('John Bates Jr.'s Auction
# Room'), so it is cut at the possessive before the rule is applied.
SUFFIXES = ("jr", "sr", "ii", "iii", "iv", "esq", "the", "of", "and")


def surname_of(name: str) -> str:
    name = re.split(r"['’]s\b", name)[0]
    words = [w for w in re.split(r"[\s.,]+", name) if w]
    words = [w for w in words if alpha(w) and alpha(w) not in SUFFIXES and len(alpha(w)) > 1]
    return alpha(words[-1]) if words else ""


def lead_rule(index_key: str, layer_key: str):
    """Whether an OCR'd index surname may be offered as a lead on a project surname.

    Exact first, because most of them are. Then a similarity window, because the OCR
    of this photostat drops and doubles letters constantly ('Bennott' for 'Bennett',
    'Beeubion' for 'Beaubien') and refusing those would throw away most of the
    Chicago cards. The window is deliberately tight — same first letter, within two
    letters of the same length, 0.86 similarity — and even a match at 1.0 is a LEAD:
    the index files thousands of unrelated families under one surname, and none of
    this says a card is about this project's man.
    """
    if not index_key or not layer_key:
        return None
    if index_key == layer_key:
        return "exact surname"
    if index_key[0] != layer_key[0] or abs(len(index_key) - len(layer_key)) > 2:
        return None
    ratio = difflib.SequenceMatcher(None, index_key, layer_key).ratio()
    if ratio >= 0.86:
        return "OCR variant (%.2f similarity to %r)" % (ratio, layer_key)
    return None


# ---------------------------------------------------------------- the parse

def read_committed_cards(volume: int):
    """Every card back out of the committed text, with the line numbers it sits on."""
    path = DOMAIN / "text" / ("vol_%02d_locality_cards.txt" % volume)
    if not path.exists():
        raise SystemExit("no committed text for volume %d — run --extract" % volume)
    lines = path.read_text(encoding="utf-8").splitlines()
    cards = []
    for i, line in enumerate(lines, start=1):
        m = re.match(r"^p(\d{4}) c(\d)  (.*)$", line)
        if not m or i >= len(lines):
            continue
        body = lines[i][8:]
        cards.append({"page": int(m.group(1)), "column": int(m.group(2)),
                      "heading": m.group(3), "heading_line": i,
                      "body": body, "body_line": i + 1,
                      "buckets": buckets_of(body)})
    return path.name, lines, cards


def works_of(body: str):
    out = []
    for w in WORKS:
        if w["pattern"].search(body):
            out.append(w["key"])
            continue
        fz = w.get("fuzzy")
        if fz and token_like(body, fz[0], fz[1]):
            out.append(w["key"])
    return out


def leads_and_follow(records, layers, lead_id):
    """The leads and the reading order over a set of records.

    Called twice: once on ONE volume's records, for that volume's own counts, and
    once on EVERY parsed volume's records, for the committed `leads.json` and
    `follow_up.json`. Before T-0578 it was inlined in parse() and ran on one volume
    only, so reading volume 2 overwrote volume 1's 319 leads with volume 2's 215
    instead of carrying both — the reading order is a fact about the whole index, not
    about whichever volume was read last. `lead_id` is passed in because a per-volume
    id would collide across volumes on a surname both of them file.
    """
    # One row per (index surname, layer), carrying every card that surname stands
    # on and every project id it could bear on.
    by_key = {}
    for rec in records:
        by_key.setdefault(rec["normalized"]["surname_key"], []).append(rec)
    leads = []
    for key in sorted(by_key):
        for layer in sorted(layers):
            hits = []
            rule = None
            for entry in layers[layer]:
                r = lead_rule(key, surname_of(entry["name"]))
                if r:
                    hits.append({"id": entry["id"], "name": entry["name"], "rule": r})
                    rule = rule or r
            if not hits:
                continue
            leads.append({
                "id": lead_id(key, layer),
                "surname_key": key,
                "spellings_as_printed": sorted({r["normalized"]["surname_as_printed"]
                                                for r in by_key[key]}),
                "layer": layer,
                "candidates": hits,
                "entries": [r["id"] for r in by_key[key]],
                "works_cited": sorted({w for r in by_key[key]
                                       for w in r["normalized"]["works_cited"]}),
                "note": "A LEAD, never a match. The index files every family of this "
                        "surname together and this project's person is one of them at "
                        "most; the card is worth following only into the work it cites.",
            })

    # The reading order. A work is worth opening in proportion to how many of this
    # project's people its Chicago cards could bear on — not to how many cards it has.
    lead_keys = {ld["surname_key"] for ld in leads}
    follow = []
    for spec in WORKS:
        cited = [r for r in records if spec["key"] in r["normalized"]["works_cited"]]
        with_leads = [r for r in cited
                      if r["normalized"]["surname_key"] in lead_keys]
        chi = [r for r in cited if r["normalized"]["chicago_or_cook"]]
        chi_leads = [r for r in with_leads if r["normalized"]["chicago_or_cook"]]
        follow.append({
            "key": spec["key"], "title": spec["title"], "author": spec["author"],
            "date": spec["date"],
            "cards": len(cited),
            "chicago_or_cook_cards": len(chi),
            "cards_on_a_lead_surname": len(with_leads),
            "chicago_or_cook_cards_on_a_lead_surname": len(chi_leads),
            "surnames_on_a_lead_in_chicago_or_cook": sorted(
                {r["normalized"]["surname_key"] for r in chi_leads}),
            "held_source_id": spec["held"],
            "reachable": spec["reachable"],
        })
    unmatched = [r for r in records if not r["normalized"]["works_cited"]]
    unmatched_chi = [r for r in unmatched if r["normalized"]["chicago_or_cook"]]
    follow.sort(key=lambda w: (-w["chicago_or_cook_cards_on_a_lead_surname"],
                               -w["chicago_or_cook_cards"], -w["cards"], w["key"]))
    return leads, follow, unmatched, unmatched_chi, by_key


# ------------------------------------------------- the re-derivation fingerprint

# T-0740. `--parse` is deterministic over TWO inputs: the committed card text, and the
# layers the leads are looked up in — the households, the 1833-1835 voter lists, the
# 1840 census pages and the named structures. The card text is gated already (its
# sha256 is in MANIFEST). The LAYERS are not, and they are the ones that move: a
# cohort lands, a census page is read, a household is renamed, and the committed
# leads quietly stop being what a fresh parse produces. Nothing was wrong in the
# files; they were just old, and the gate could not see it because it re-derived the
# crosswalk from the COMMITTED leads rather than from the inputs.
#
# Re-parsing inside the gate would cost four minutes (64 s a volume, measured), which
# is four minutes on every commit to catch a drift that happens weekly. So the gate
# hashes the inputs instead. A fingerprint that still matches means a re-parse is a
# no-op; one that does not means the leads are stale and must be regenerated AND
# re-ruled (tools/rule_newberry_leads.py --write), because new leads arrive unruled.
def parse_fingerprint(domain: Path = None, volumes: list = None) -> str:
    domain = domain or DOMAIN
    h = hashlib.sha256()
    layers = layer_names()
    h.update(json.dumps(layers, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    # The WORKS table lives in this file, not in data/, so an edit to it changes the
    # parse without changing any committed input. T-0582 added a pattern and could
    # not commit the re-parse; that is the case this line covers.
    h.update(json.dumps([[w["key"], w["pattern"].pattern, w.get("fuzzy")]
                         for w in WORKS], sort_keys=True,
                        ensure_ascii=False).encode("utf-8"))
    for vol in sorted(volumes if volumes is not None else VOLUMES):
        path = domain / "text" / ("vol_%02d_locality_cards.txt" % vol)
        h.update(("vol_%02d:" % vol).encode("utf-8"))
        h.update(sha256_file(path).encode("utf-8") if path.exists() else b"absent")
    return h.hexdigest()


def parse(volume: int) -> dict:
    text_name, _lines, cards = read_committed_cards(volume)
    layers = layer_names()

    records = []
    for n, card in enumerate(cards, start=1):
        key = surname_key(card["heading"])
        records.append({
            "id": "nbi_v%02d_%04d" % (volume, n),
            "as_read": "%s | %s" % (card["heading"], card["body"]),
            "normalized": {
                "surname_as_printed": card["heading"],
                "surname_key": key,
                "localities": card["buckets"],
                # The distinction that decides what is worth reading next. A card
                # naming Fulton or Sangamon County is Illinois and is kept; it is not
                # Chicago, and a work is ranked on the Chicago and Cook County cards
                # it carries, not on its county histories.
                "chicago_or_cook": bool({"chicago", "cook_county"} & set(card["buckets"])),
                "works_cited": works_of(card["body"]),
            },
            "locator": {
                "list": "vol_%02d" % volume,
                "text_file": text_name,
                "lines": [card["heading_line"], card["body_line"]],
                "index_page": card["page"],
                "column": card["column"],
            },
            "reading": "transcription_mediated",
            "confidence": "documented",
            "notes": "A card in the Newberry index, not a statement about a person. "
                     "What is documented is that the index files this surname with a "
                     "citation naming %s; the citation itself is unread until the work "
                     "it names is opened."
                     % (", ".join(card["buckets"]) or "a locality"),
        })

    # The crop windows overlap, so a card on a column boundary is read twice — once
    # in full and once as a truncated sliver. The sliver keeps its record, because
    # the ink is real and the ids are positional, and is marked and withheld from
    # every count below. See find_slivers().
    slivers = find_slivers(cards)
    for i, j in slivers.items():
        records[i]["normalized"]["sliver_of"] = records[j]["id"]
        records[i]["notes"] = (
            "A COLUMN SLIVER: the leftmost few points of %s, which the pass over "
            "column %d read in full, caught by the pass over column %d because the "
            "crop windows overlap by 27 points. Its body is a byte-exact prefix of "
            "that card's. It is kept because the ink is real and it was really read, "
            "and it is withheld from this volume's counts, from the leads and from "
            "the reading order, because it is not a second card."
            % (records[j]["id"], cards[j]["column"], cards[i]["column"]))
    # The same overlap read from the other end, and on a WIDE page (T-0769). The
    # left edge of a window falls inside the previous column, so the card it
    # assembles OPENS with that column's tail — heading and body both — and the
    # locality patterns match on text that is not on this card. Every one of the
    # fifteen names a locality ONLY inside the run, so every one is withheld: it was
    # kept for ink it does not carry. See find_bleeds().
    bleeds = find_bleeds(cards)
    for i, (j, length) in bleeds.items():
        run = collapse(cards[i]["body"])[:length]
        records[i]["normalized"]["bleed_of"] = records[j]["id"]
        records[i]["normalized"]["bleed_run"] = run
        records[i]["normalized"]["localities_off_own_ink"] = buckets_of(
            collapse(cards[i]["body"])[length:])
        records[i]["notes"] = (
            "A BLED-IN BODY: this page is wide enough that the crop window over "
            "column %d begins inside column %d, so the pass read the tail of %s "
            "— %r, %d characters, byte-exact — and glued it to the front of this "
            "card. The heading is cut in the same place, which is how the direction "
            "is known. The card's own ink names %s, so the locality that kept it is "
            "not on it; the record is held because the ink is real and it was really "
            "read, and it is withheld from this volume's counts, from the leads and "
            "from the reading order."
            % (cards[i]["column"], cards[j]["column"], records[j]["id"], run, length,
               ", ".join(records[i]["normalized"]["localities_off_own_ink"])
               or "no locality at all"))
    withheld = set(slivers) | set(bleeds)
    live = [r for k, r in enumerate(records) if k not in withheld]

    leads, follow, unmatched, unmatched_chi, by_key = leads_and_follow(
        live, layers, lambda key, layer: "lead_v%02d_%s_%s" % (volume, key, layer))

    counts = {
        "cards": len(live),
        "records": len(records),
        "slivers": len(slivers),
        "bled_in_bodies": len(bleeds),
        "by_locality": {name: sum(1 for r in live
                                  if name in r["normalized"]["localities"])
                        for name, _ in LOCALITY_BUCKETS},
        "distinct_surname_keys": len(by_key),
        "leads": len(leads),
        "leads_by_layer": {layer: sum(1 for ld in leads if ld["layer"] == layer)
                           for layer in sorted(layers)},
        "chicago_or_cook_cards": sum(1 for r in live
                                     if r["normalized"]["chicago_or_cook"]),
        "cards_matching_no_known_work": len(unmatched),
        "chicago_or_cook_cards_matching_no_known_work": len(unmatched_chi),
    }

    dump(DOMAIN / "records" / ("entries_vol_%02d.json" % volume), {
        "schema": SCHEMA,
        "_doc": "GENERATED by tools/read_newberry_index.py --parse. One record per "
                "Newberry index card whose body names Chicago, Cook County or "
                "Illinois. A card is a pointer to a book, never a fact about a person.",
        "generated_by": "tools/read_newberry_index.py --parse --volume %d" % volume,
        "source_id": SOURCE_ID,
        "volume": volume,
        "counts": counts,
        "sliver_scan": scan_slivers(cards, [r["id"] for r in records],
                                    read_by_of(volume)),
        "records": records,
    })
    index_path = DOMAIN / "entries.json"
    index = load(index_path) if index_path.exists() else {}
    volumes = index.get("volumes") or {}
    volumes[str(volume)] = {"file": "records/entries_vol_%02d.json" % volume,
                            "covers": VOLUMES[volume]["covers"], "counts": counts}
    dump(index_path, {
        "schema": SCHEMA,
        "_doc": "GENERATED. The index of this domain's parsed entries. The entries "
                "themselves live one file per volume under records/, where "
                "tools/research_domains.py --check reads and gates them; a second copy "
                "here would drift from the gated one within a run.",
        "generated_by": "tools/read_newberry_index.py --parse",
        "volumes_parsed": sorted(int(k) for k in volumes),
        "volumes_unread": sorted(v for v in VOLUMES if str(v) not in volumes),
        "volumes": {k: volumes[k] for k in sorted(volumes, key=int)},
    })

    # THE LEADS AND THE READING ORDER ARE FACTS ABOUT THE WHOLE INDEX, not about the
    # volume that happened to be read last, so they are rebuilt from EVERY parsed
    # volume's committed records. Until T-0578 they were written from this volume
    # alone, and reading volume 2 silently replaced volume 1's 319 leads with volume
    # 2's 215; entries.json accumulated and these two did not.
    parsed = sorted(int(k) for k in volumes)
    all_records = []
    for vol in parsed:
        path = DOMAIN / "records" / ("entries_vol_%02d.json" % vol)
        if path.exists():
            all_records.extend(
                r for r in (load(path).get("records") or [])
                if not (r.get("normalized") or {}).get("sliver_of")
                and not (r.get("normalized") or {}).get("bleed_of"))
    # THE ID KEEPS THE VOLUME, and it is the FIRST volume the surname appears in.
    # lead_crosswalk.json (T-0590) anchors 1,248 references at `lead_v01_*`, so a
    # surname filed in both volumes must keep the id its ruling was written against;
    # a surname new to volume 2 gets `lead_v02_*`. A bare `lead_<key>_<layer>` would
    # orphan every one of those rulings.
    first_volume = {}
    for rec in all_records:
        vol = int(rec["id"][5:7])
        key = rec["normalized"]["surname_key"]
        first_volume[key] = min(first_volume.get(key, vol), vol)
    leads_all, follow_all, unmatched_all, unmatched_chi_all, by_key_all = \
        leads_and_follow(all_records, layers,
                         lambda key, layer: "lead_v%02d_%s_%s"
                                            % (first_volume[key], key, layer))
    dump(DOMAIN / "leads.json", {
        "schema": SCHEMA,
        "_doc": "GENERATED. Surname -> the residents, voters, 1840 heads and structures "
                "a Newberry card COULD bear on, over every volume read so far. Never a "
                "merge: see crosswalk.json, which holds none and says why.",
        "generated_by": "tools/read_newberry_index.py --parse",
        "volumes": parsed,
        # What this file re-derives from. --check recomputes it and fails when it has
        # moved, so a stale leads.json is found by the gate rather than by the next
        # run that happens to touch the works table (T-0740).
        "derives_from": {
            "fingerprint": parse_fingerprint(volumes=parsed),
            "_doc": "sha256 over the layers the leads are looked up in, the WORKS "
                    "table, and the committed card text of every parsed volume. "
                    "Recomputed by --check; a mismatch means --parse is no longer a "
                    "no-op and the leads must be regenerated and re-ruled.",
            "layer_counts": {name: len(rows) for name, rows in sorted(layers.items())},
        },
        "counts": {
            "cards": len(all_records),
            "distinct_surname_keys": len(by_key_all),
            "leads": len(leads_all),
            "leads_by_layer": {layer: sum(1 for ld in leads_all
                                          if ld["layer"] == layer)
                               for layer in sorted(layers)},
        },
        "leads": leads_all,
    })
    dump(DOMAIN / "follow_up.json", {
        "schema": SCHEMA,
        "_doc": "GENERATED. The works the Chicago, Cook County and Illinois cards point "
                "at, over every volume read so far, ranked by how many of this "
                "project's people they could bear on. This is the reading order for "
                "the follow-up tickets.",
        "generated_by": "tools/read_newberry_index.py --parse",
        "volumes": parsed,
        "works": follow_all,
        "cards": len(all_records),
        "cards_matching_no_known_work": len(unmatched_all),
        "chicago_or_cook_cards_matching_no_known_work": len(unmatched_chi_all),
        "note": "A card whose citation matches no pattern in WORKS is counted here and "
                "kept in the records; it is the queue of works nobody has named yet. "
                "Most of them are Illinois COUNTY histories — Chapman, LeBaron, Brink, "
                "Baldwin, Murray Williamson, Power — which are Illinois and are not "
                "Chicago, and which is why the ranking is on the Chicago and Cook "
                "County cards.",
    })
    return counts


# ---------------------------------------------------------------- the gate

def check(domain: Path = None, payload_root: Path = None) -> list:
    """The assertions. Every one of them fires in --self-test.

    The gate this domain most needs is the LAST one: a finding aid published in 1960
    may not appear in a resident, household or structure record. The whole failure
    mode of an index is that a surname in it looks like evidence, and the only place
    that can be stopped is here.
    """
    domain = domain or DOMAIN
    bad = []
    if not domain.exists():
        return ["data/research/newberry_index/ does not exist"]

    manifest_path = domain / "text" / "MANIFEST.json"
    manifest = load(manifest_path) if manifest_path.exists() else None
    if manifest is None:
        bad.append("text/MANIFEST.json is missing — the committed text is not "
                   "reproducible without it")
    elif manifest.get("ia_item") != IA_ITEM:
        bad.append("MANIFEST names ia_item %r, not the identifier the owner uploaded "
                   "the volumes under" % manifest.get("ia_item"))

    # A volume read by OCR is only reproducible while the shards it was assembled out
    # of are still there and still hash the same. They are the intermediate here, the
    # way the four pdftotext passes are the intermediate for a text-layer volume, and
    # unlike those they are committed — so they can rot, and this says so when they do.
    for volume, vol in sorted((manifest or {}).get("volumes", {}).items()):
        if vol.get("read_by") != "ocr":
            continue
        shard_root = domain / "text" / "ocr" / ("vol_%02d" % int(volume))
        named = {r["shard"]: r for r in vol.get("ocr_shards") or []}
        if not named:
            bad.append("MANIFEST says volume %s was read by OCR and names no shard — "
                       "the reading is not reproducible" % volume)
        for name, rec in sorted(named.items()):
            path = shard_root / name
            if not path.exists():
                bad.append("volume %s: MANIFEST names OCR shard %s, which is not "
                           "committed" % (volume, name))
            elif sha256_file(path) != rec.get("sha256"):
                bad.append("volume %s: OCR shard %s does not hash to what MANIFEST "
                           "says it does" % (volume, name))
        for path in sorted(shard_root.glob("pages_*.json.gz")):
            if path.name not in named:
                bad.append("volume %s: OCR shard %s is committed but MANIFEST does not "
                           "name it — the committed text was assembled without it"
                           % (volume, path.name))

    for path in sorted((domain / "records").glob("entries_vol_*.json")):
        doc = load(path)
        label = "records/" + path.name
        volume = doc.get("volume")
        if doc.get("source_id") != SOURCE_ID:
            bad.append("%s: cites source_id %r, not %r" % (label, doc.get("source_id"),
                                                           SOURCE_ID))
        text_name = "vol_%02d_locality_cards.txt" % (volume or 0)
        text_path = domain / "text" / text_name
        if not text_path.exists():
            bad.append("%s: names volume %s, whose text file is not committed"
                       % (label, volume))
            continue
        lines = text_path.read_text(encoding="utf-8").splitlines()
        if manifest:
            vol = (manifest.get("volumes") or {}).get(str(volume)) or {}
            if vol.get("text_sha256") and vol["text_sha256"] != sha256_file(text_path):
                bad.append("%s: %s does not hash to what MANIFEST says it does — the "
                           "committed text has been edited by hand" % (label, text_name))
        for rec in doc.get("records") or []:
            where = "%s %s" % (label, rec.get("id"))
            loc = rec.get("locator") or {}
            if loc.get("text_file") != text_name:
                bad.append("%s: locator names text_file %r, not %r"
                           % (where, loc.get("text_file"), text_name))
                continue
            pair = loc.get("lines") or []
            if len(pair) != 2 or pair[0] < 1 or pair[1] > len(lines) or pair[1] < pair[0]:
                bad.append("%s: locator names lines %r, which %s does not have"
                           % (where, pair, text_name))
                continue
            heading = re.sub(r"^p\d{4} c\d  ", "", lines[pair[0] - 1])
            body = lines[pair[1] - 1][8:]
            if rec.get("as_read") != "%s | %s" % (heading, body):
                bad.append("%s: as_read is not what the committed text says at its "
                           "locator" % where)
            if rec.get("reading") != "transcription_mediated":
                bad.append("%s: reading is %r — a machine's reading of a photostat of "
                           "a card is a transcription, and calling it anything stronger "
                           "is the upgrade the provenance rule forbids"
                           % (where, rec.get("reading")))
            got = (rec.get("normalized") or {}).get("localities") or []
            if not got:
                bad.append("%s: a kept card naming no locality" % where)
            elif got != buckets_of(body):
                bad.append("%s: the localities do not re-derive from the committed "
                           "body line" % where)

    # THE SLIVER MARK, BOTH WAYS (T-0601). A record that calls itself a sliver has to
    # be one on the committed text, and — the half that actually earns its keep —
    # every sliver the committed text carries has to be marked. Without the second
    # clause a records file parsed before the rule existed goes on counting one card
    # twice and nothing says so; with it, the count and the text cannot drift apart.
    for path in sorted((domain / "records").glob("entries_vol_*.json")):
        doc = load(path)
        label = "records/" + path.name
        volume = doc.get("volume")
        text_path = domain / "text" / ("vol_%02d_locality_cards.txt" % (volume or 0))
        if not text_path.exists():
            continue
        tlines = text_path.read_text(encoding="utf-8").splitlines()
        recs = doc.get("records") or []
        cards, moored = [], True
        for rec in recs:
            loc = rec.get("locator") or {}
            pair = loc.get("lines") or []
            if len(pair) != 2 or not (1 <= pair[1] <= len(tlines)):
                moored = False
                break
            cards.append({"page": loc.get("index_page"), "column": loc.get("column"),
                          "heading": re.sub(r"^p\d{4} c\d  ", "",
                                            tlines[pair[0] - 1]),
                          "body": tlines[pair[1] - 1][8:]})
        if not moored:
            continue                      # the locator gate above has already said so
        found = find_slivers(cards)
        for i, rec in enumerate(recs):
            marked = (rec.get("normalized") or {}).get("sliver_of")
            truth = recs[found[i]].get("id") if i in found else None
            if truth and not marked:
                bad.append("%s %s: a column sliver of %s that the records do not mark "
                           "— the domain is counting one card twice"
                           % (label, rec.get("id"), truth))
            elif marked and not truth:
                bad.append("%s %s: marked a sliver of %s, and the committed text does "
                           "not make it one" % (label, rec.get("id"), marked))
            elif marked and marked != truth:
                bad.append("%s %s: marked a sliver of %s, and the card it truncates on "
                           "the committed text is %s"
                           % (label, rec.get("id"), marked, truth))
        # THE BLEED MARK, BOTH WAYS (T-0769), and for the same reason the sliver
        # gate runs both ways: a records file parsed before this rule existed goes
        # on counting a card that was kept for a locality printed in the column to
        # its left, and nothing says so.
        bled = find_bleeds(cards)
        for i, rec in enumerate(recs):
            marked = (rec.get("normalized") or {}).get("bleed_of")
            truth = recs[bled[i][0]].get("id") if i in bled else None
            if truth and not marked:
                bad.append("%s %s: opens with the tail of %s in the column to its "
                           "left and the records do not mark it — the domain is "
                           "counting a card kept for a locality that is not on it"
                           % (label, rec.get("id"), truth))
            elif marked and not truth:
                bad.append("%s %s: marked a bled-in body off %s, and the committed "
                           "text does not make it one"
                           % (label, rec.get("id"), marked))
            elif marked and marked != truth:
                bad.append("%s %s: marked a bled-in body off %s, and the card whose "
                           "tail it opens with on the committed text is %s"
                           % (label, rec.get("id"), marked, truth))
            elif marked:
                want = collapse(cards[i]["body"])[:bled[i][1]]
                if (rec.get("normalized") or {}).get("bleed_run") != want:
                    bad.append("%s %s: bleed_run is not the run the committed text "
                               "shares with %s" % (label, rec.get("id"), marked))
        overlap = set(found) & set(bled)
        if overlap:
            bad.append("%s: %d record(s) marked both a column sliver and a bled-in "
                       "body — the two halves of the overlap cannot both hold"
                       % (label, len(overlap)))
        net = len(recs) - len(set(found) | set(bled))
        stated = (doc.get("counts") or {}).get("cards")
        if stated is not None and stated != net:
            bad.append("%s: counts.cards says %s, and the file holds %d records of "
                       "which %d are column slivers and %d are bled-in bodies — %d "
                       "cards" % (label, stated, len(recs), len(found), len(bled), net))
        stated_bleeds = (doc.get("counts") or {}).get("bled_in_bodies")
        if stated_bleeds is not None and stated_bleeds != len(bled):
            bad.append("%s: counts.bled_in_bodies says %s and the committed text "
                       "carries %d" % (label, stated_bleeds, len(bled)))

        # THE SCAN, RE-DERIVED (T-0810). `byte_exact: 0` is what the sliver rule gives
        # for an OCR reading whether or not the volume has slivers, because its two
        # readings of the overlap come from two tesseract runs and cannot be
        # byte-identical. Volume 4 carried that zero from the day it was re-read and
        # nothing had ever looked. So every volume now states its scan, and the gate
        # rebuilds it here: a records file with no scan is a reading nobody checked,
        # and a scan whose figures have drifted from the text beside them is one the
        # counts above cannot see.
        stated_scan = doc.get("sliver_scan")
        if not stated_scan:
            bad.append("%s: no sliver_scan — this reading has never been scanned for "
                       "column slivers, and counts.slivers alone cannot say whether "
                       "that is a clean volume or an unasked question (T-0810)"
                       % label)
        else:
            ids = [r.get("id") for r in recs]
            truth_scan = scan_slivers(cards, ids, read_by_of(volume, domain))
            for key in ("read_by", "boundary_pairs", "byte_exact",
                        "max_prefix_agreement", "max_prefix_agreement_on"):
                if stated_scan.get(key) != truth_scan[key]:
                    bad.append("%s: sliver_scan.%s says %r and the committed text "
                               "gives %r" % (label, key, stated_scan.get(key),
                                             truth_scan[key]))

    cross_path = domain / "crosswalk.json"
    if cross_path.exists():
        cross = load(cross_path)
        if cross.get("merges"):
            bad.append("crosswalk.json carries a merge — an index entry is a surname "
                       "and nothing else, and a surname-only merge is always a refusal")

    leads_path = domain / "leads.json"
    if leads_path.exists():
        leads_doc = load(leads_path)
        # T-0740: the committed leads must still be what a fresh --parse produces.
        want = parse_fingerprint(domain=domain,
                                 volumes=leads_doc.get("volumes") or None)
        got = (leads_doc.get("derives_from") or {}).get("fingerprint")
        if not got:
            bad.append("leads.json carries no derives_from.fingerprint — it was "
                       "written before the re-derivation gate; re-run "
                       "tools/read_newberry_index.py --parse --volume 1..4")
        elif got != want:
            bad.append("leads.json does not re-derive from its inputs: the layers, "
                       "the WORKS table or the committed card text have moved under "
                       "it. Re-run --parse over every volume in leads.json's "
                       "`volumes`, then tools/rule_newberry_leads.py --write — new "
                       "leads arrive unruled")
        for lead in leads_doc.get("leads") or []:
            if not lead.get("candidates"):
                bad.append("leads.json %s: a lead with no candidate" % lead.get("id"))
            for cand in lead.get("candidates") or []:
                if not str(cand.get("rule") or "").strip():
                    bad.append("leads.json %s: a candidate with no rule — %r"
                               % (lead.get("id"), cand.get("name")))
            if "never a match" not in (lead.get("note") or ""):
                bad.append("leads.json %s: a lead that does not say it is a lead"
                           % lead.get("id"))

    follow_path = domain / "follow_up.json"
    if follow_path.exists():
        for work in load(follow_path).get("works") or []:
            if work.get("chicago_or_cook_cards", 0) > work.get("cards", 0):
                bad.append("follow_up.json %s: more Chicago cards than cards"
                           % work.get("key"))
            if work.get("cards_on_a_lead_surname", 0) > work.get("cards", 0):
                bad.append("follow_up.json %s: more lead cards than cards"
                           % work.get("key"))
            if not str(work.get("reachable") or "").strip():
                bad.append("follow_up.json %s: a work with nothing said about whether "
                           "it can be opened" % work.get("key"))

    # The precision figure is only worth what it still measures. Every sampled card
    # is looked up in the records by its verbatim reading, so a re-extract that moves
    # the readings under the sample fails here and the sample is re-drawn, instead of
    # a number in the README quietly going stale.
    sample_path = domain / "precision_sample.json"
    if sample_path.exists():
        sample = load(sample_path)
        read, withheld = set(), {}
        for path in sorted((domain / "records").glob("entries_vol_*.json")):
            for rec in load(path).get("records") or []:
                read.add(rec.get("as_read"))
                mark = (rec.get("normalized") or {}).get("bleed_of")
                if mark:
                    withheld[rec.get("as_read")] = (rec.get("id"), mark)
        rows = sample.get("records") or []
        for row in rows:
            if row.get("as_read") not in read:
                bad.append("precision_sample.json %s: the card it adjudicates is no "
                           "longer in the records — re-draw the sample, do not carry "
                           "its number forward" % row.get("id"))
            # T-0769. A sampled row is a verdict reached by eye on the leaf; a bleed
            # mark is a verdict reached by rule that the locality is printed in the
            # column to the left. The two cannot both stand on one card, and the
            # sample is the older and the better-evidenced of them: a row that turns
            # up marked is the RULE to re-argue, not the reading to overwrite.
            elif row.get("as_read") in withheld:
                rid, mark = withheld[row["as_read"]]
                bad.append("precision_sample.json %s: %s is marked a bled-in body off "
                           "%s and is adjudicated %r by eye — re-argue the rule or "
                           "re-draw the row, and do not carry both"
                           % (row.get("id"), rid, mark, row.get("verdict")))
            if row.get("verdict") not in ("locality_correct", "not_demonstrated"):
                bad.append("precision_sample.json %s: verdict %r is outside the two "
                           "this file may reach" % (row.get("id"), row.get("verdict")))
        counts = sample.get("counts") or {}
        good = sum(1 for r in rows if r.get("verdict") == "locality_correct")
        if counts.get("sampled") != len(rows) or counts.get("locality_correct") != good:
            bad.append("precision_sample.json: the counts do not add up to the "
                       "verdicts under them")

    root = payload_root if payload_root is not None else ROOT
    if root is not None:
        for sub in ("data/residents", "data/structures", "data/reconstruction"):
            d = root / sub
            for path in sorted(d.rglob("*.json")) if d.exists() else []:
                if SOURCE_ID in path.read_text(encoding="utf-8"):
                    bad.append("%s cites %s — the Newberry index is a finding aid "
                               "published in 1960 and may not stand behind a person, a "
                               "household or a building"
                               % (path.relative_to(root), SOURCE_ID))
    return bad


def self_test() -> int:
    """Break each assertion in a copy of the domain and prove the gate says so."""
    import copy as _copy
    fired = []

    def run(label, mutate):
        tmp = Path(tempfile.mkdtemp(prefix="nbi_selftest_"))
        dom = tmp / "newberry_index"
        shutil.copytree(DOMAIN, dom)
        mutate(dom)
        bad = check(domain=dom, payload_root=None)
        shutil.rmtree(tmp, ignore_errors=True)
        if not bad:
            print("  DID NOT FIRE: %s" % label)
            return False
        print("  fires: %s — %s" % (label, bad[0][:110]))
        fired.append(label)
        return True

    def edit_records(dom, fn):
        path = next((dom / "records").glob("entries_vol_*.json"))
        doc = load(path)
        fn(doc)
        dump(path, doc)

    ok = True
    ok &= run("a record whose as_read has been tidied",
              lambda d: edit_records(d, lambda doc: doc["records"][0]
                                     .__setitem__("as_read", "Adams family. | Chicago.")))
    ok &= run("a reading upgraded to scan_verified",
              lambda d: edit_records(d, lambda doc: doc["records"][0]
                                     .__setitem__("reading", "scan_verified")))
    ok &= run("a locator pointing past the end of the committed text",
              lambda d: edit_records(d, lambda doc: doc["records"][0]["locator"]
                                     .__setitem__("lines", [1, 10 ** 7])))
    ok &= run("a card whose localities no longer re-derive from its body",
              lambda d: edit_records(d, lambda doc: doc["records"][0]["normalized"]
                                     .__setitem__("localities", ["chicago", "cook_county",
                                                                 "illinois_named",
                                                                 "illinois_abbreviated"])))
    ok &= run("a records file citing another source",
              lambda d: edit_records(d, lambda doc: doc.__setitem__("source_id", "andreas_1884_v1")))
    ok &= run("the committed text edited by hand after extraction",
              lambda d: (d / "text" / "vol_01_locality_cards.txt").write_text(
                  (d / "text" / "vol_01_locality_cards.txt").read_text(encoding="utf-8")
                  .replace("Chicago", "Chicago!", 1), encoding="utf-8"))
    ok &= run("MANIFEST naming the wrong Internet Archive item",
              lambda d: dump(d / "text" / "MANIFEST.json",
                             dict(load(d / "text" / "MANIFEST.json"), ia_item="wrong")))
    def unmark_sliver(dom):
        for path in sorted((dom / "records").glob("entries_vol_*.json")):
            doc = load(path)
            for rec in doc.get("records") or []:
                if (rec.get("normalized") or {}).get("sliver_of"):
                    rec["normalized"].pop("sliver_of")
                    doc["counts"]["cards"] = doc["counts"]["cards"] + 1
                    dump(path, doc)
                    return
        raise AssertionError("no sliver in the committed records to unmark")
    ok &= run("a column sliver the records no longer mark", unmark_sliver)

    def invent_sliver(dom):
        path = next((dom / "records").glob("entries_vol_*.json"))
        doc = load(path)
        for rec in doc.get("records") or []:
            if not (rec.get("normalized") or {}).get("sliver_of"):
                rec["normalized"]["sliver_of"] = doc["records"][0]["id"]
                break
        dump(path, doc)
    ok &= run("a card marked a sliver of one it does not truncate", invent_sliver)

    def miscount_slivers(dom):
        # The fixture has to break a volume that HAS a sliver to deduct. It used to
        # take whichever the glob yielded first, which was safe only while every
        # volume carried one. T-0775's OCR re-read of volume 4 rewrote all its cards
        # and carries no sliver count at all (T-0810), so on a glob that lands there
        # `cards` already equals `len(records)`, the fixture changes nothing and the
        # assertion silently stops testing anything. Pick a volume that can be broken.
        path = next((p for p in sorted((dom / "records").glob("entries_vol_*.json"))
                     if (load(p).get("counts") or {}).get("slivers")), None)
        if path is None:
            raise AssertionError("no committed volume carries a sliver to miscount — "
                                 "this fixture can no longer test what it claims to")
        doc = load(path)
        doc["counts"]["cards"] = len(doc["records"])
        dump(path, doc)
    ok &= run("a volume counting its slivers as cards", miscount_slivers)

    def drop_sliver_scan(dom):
        path = next(iter(sorted((dom / "records").glob("entries_vol_*.json"))))
        doc = load(path)
        doc.pop("sliver_scan", None)
        dump(path, doc)
    ok &= run("a reading nobody scanned for column slivers", drop_sliver_scan)

    def stale_sliver_scan(dom):
        # The figure a re-read would move. It is deliberately NOT byte_exact: that one
        # is already covered by the counts, and what T-0810 is about is the half of the
        # scan the counts cannot see.
        path = next(iter(sorted((dom / "records").glob("entries_vol_*.json"))))
        doc = load(path)
        doc["sliver_scan"]["boundary_pairs"] = doc["sliver_scan"]["boundary_pairs"] + 1
        dump(path, doc)
    ok &= run("a sliver scan that no longer re-derives from the committed text",
              stale_sliver_scan)

    def unmark_bleed(dom):
        for path in sorted((dom / "records").glob("entries_vol_*.json")):
            doc = load(path)
            for rec in doc.get("records") or []:
                if (rec.get("normalized") or {}).get("bleed_of"):
                    rec["normalized"].pop("bleed_of")
                    rec["normalized"].pop("bleed_run", None)
                    doc["counts"]["cards"] = doc["counts"]["cards"] + 1
                    doc["counts"]["bled_in_bodies"] = doc["counts"]["bled_in_bodies"] - 1
                    dump(path, doc)
                    return
        raise AssertionError("no bled-in body in the committed records to unmark")
    ok &= run("a bled-in body the records no longer mark", unmark_bleed)

    def invent_bleed(dom):
        path = next((p for p in sorted((dom / "records").glob("entries_vol_*.json"))
                     if (load(p).get("counts") or {}).get("bled_in_bodies")), None)
        if path is None:
            raise AssertionError("no committed volume carries a bled-in body")
        doc = load(path)
        # Not the first record, and not off itself: the fixture has to name a real
        # OTHER card, or it tests self-reference rather than the mark.
        for rec in doc["records"][1:]:
            if not (rec.get("normalized") or {}).get("bleed_of"):
                rec["normalized"]["bleed_of"] = doc["records"][0]["id"]
                rec["normalized"]["bleed_run"] = "x" * BLEED_MIN_RUN
                break
        dump(path, doc)
    ok &= run("a card marked a bled-in body off one whose tail it does not open with",
              invent_bleed)

    def miscount_bleeds(dom):
        path = next((p for p in sorted((dom / "records").glob("entries_vol_*.json"))
                     if (load(p).get("counts") or {}).get("bled_in_bodies")), None)
        if path is None:
            raise AssertionError("no committed volume carries a bled-in body to "
                                 "miscount — this fixture can no longer test what it "
                                 "claims to")
        doc = load(path)
        doc["counts"]["cards"] = len(doc["records"]) - (doc["counts"].get("slivers") or 0)
        dump(path, doc)
    ok &= run("a volume counting its bled-in bodies as cards", miscount_bleeds)

    def restate_bleed_run(dom):
        path = next((p for p in sorted((dom / "records").glob("entries_vol_*.json"))
                     if (load(p).get("counts") or {}).get("bled_in_bodies")), None)
        if path is None:
            raise AssertionError("no committed volume carries a bled-in body")
        doc = load(path)
        for rec in doc.get("records") or []:
            if (rec.get("normalized") or {}).get("bleed_of"):
                rec["normalized"]["bleed_run"] = rec["normalized"]["bleed_run"][:-1]
                break
        dump(path, doc)
    ok &= run("a bleed_run shortened to something the two cards do not share",
              restate_bleed_run)

    ok &= run("a merge in the crosswalk",
              lambda d: dump(d / "crosswalk.json",
                             dict(load(d / "crosswalk.json"),
                                  merges=[{"into": "Adams", "from": "Adams"}])))

    def stale_fingerprint(dom):
        doc = load(dom / "leads.json")
        doc.setdefault("derives_from", {})["fingerprint"] = "0" * 64
        dump(dom / "leads.json", doc)
    ok &= run("committed leads that no longer re-derive from their inputs",
              stale_fingerprint)

    def no_fingerprint(dom):
        doc = load(dom / "leads.json")
        doc.pop("derives_from", None)
        dump(dom / "leads.json", doc)
    ok &= run("committed leads with no re-derivation fingerprint at all",
              no_fingerprint)

    def drop_rule(dom):
        doc = load(dom / "leads.json")
        doc["leads"][0]["candidates"][0]["rule"] = ""
        dump(dom / "leads.json", doc)
    ok &= run("a lead candidate with no rule", drop_rule)

    def drop_note(dom):
        doc = load(dom / "leads.json")
        doc["leads"][0]["note"] = "a match"
        dump(dom / "leads.json", doc)
    ok &= run("a lead that calls itself a match", drop_note)

    def inflate(dom):
        doc = load(dom / "follow_up.json")
        doc["works"][0]["cards_on_a_lead_surname"] = doc["works"][0]["cards"] + 1
        dump(dom / "follow_up.json", doc)
    ok &= run("more lead cards than cards on a work", inflate)

    def restate(dom):
        doc = load(dom / "precision_sample.json")
        doc["counts"]["locality_correct"] = doc["counts"]["sampled"]
        dump(dom / "precision_sample.json", doc)
    ok &= run("a precision figure restated above its own verdicts", restate)

    def unmoor(dom):
        doc = load(dom / "precision_sample.json")
        doc["records"][0]["as_read"] = "Adams family. | Chicago, Ill."
        dump(dom / "precision_sample.json", doc)
    ok &= run("a sampled card that is no longer in the records", unmoor)

    def payload(dom):
        pass
    tmp = Path(tempfile.mkdtemp(prefix="nbi_payload_"))
    (tmp / "data" / "residents").mkdir(parents=True)
    (tmp / "data" / "residents" / "hh_x.json").write_text(
        json.dumps({"sources": [SOURCE_ID]}), encoding="utf-8")
    bad = check(domain=DOMAIN, payload_root=tmp)
    shutil.rmtree(tmp, ignore_errors=True)
    if bad:
        print("  fires: a person graded off the finding aid — %s" % bad[0][:110])
        fired.append("payload")
    else:
        print("  DID NOT FIRE: a person graded off the finding aid")
        ok = False

    # ---- the OCR path (T-0614). Two shards standing in for two page ranges, and
    # every way a run could stitch them into something that is not one reading.
    def shard(dirpath, volume, first, last, pages, settings=None, pdf_sha="deadbeef"):
        out = shard_path(volume, first, last, dirpath)
        out.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps({"schema": OCR_SHARD_SCHEMA, "volume": volume,
                           "first": first, "last": last,
                           "settings": settings or {"engine": "tesseract 0.0", "dpi": 200,
                                                    "psm": "6",
                                                    "crops": [list(c) for c in CROPS],
                                                    "crop_height": CROP_HEIGHT,
                                                    "render": "pdftoppm -gray -png"},
                           "pdf_sha256": pdf_sha, "pages": pages},
                          ensure_ascii=False, sort_keys=True)
        write_gz(out, body)
        return out

    CARD = ["Abbott family.\n  Chicago, Ill. (Dodd, S.) 1624: 111.\n", "", "", ""]
    BLANK = ["", "", "", ""]

    tmp = Path(tempfile.mkdtemp(prefix="nbi_ocr_"))
    try:
        shard(tmp, 4, 1, 1, {"1": CARD})
        shard(tmp, 4, 2, 2, {"2": BLANK})
        columns, pages, settings, records = read_shards(4, tmp)
        cards, kept = assemble(columns, pages)
        if pages == 2 and len(cards) == 1 and len(kept) == 1 \
                and kept[0]["heading"] == "Abbott" and "chicago" in kept[0]["buckets"] \
                and len(records) == 2:
            print("  fires: two OCR shards stitch into one volume and assemble")
            fired.append("ocr stitch")
        else:
            print("  DID NOT FIRE: two OCR shards stitch into one volume and assemble "
                  "(pages=%r cards=%r kept=%r)" % (pages, len(cards), len(kept)))
            ok = False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    def refuses(label, build):
        good = True
        tmp = Path(tempfile.mkdtemp(prefix="nbi_ocr_"))
        try:
            build(tmp)
            read_shards(4, tmp)
            print("  DID NOT FIRE: %s" % label)
            good = False
        except SystemExit as exc:
            print("  fires: %s — %s" % (label, str(exc)[:110]))
            fired.append(label)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return good

    ok &= refuses("shards read at two different dpi stitched into one volume",
                  lambda t: (shard(t, 4, 1, 1, {"1": CARD}),
                             shard(t, 4, 2, 2, {"2": BLANK},
                                   settings={"engine": "tesseract 0.0", "dpi": 400,
                                             "psm": "6",
                                             "crops": [list(c) for c in CROPS],
                                             "crop_height": CROP_HEIGHT,
                                             "render": "pdftoppm -gray -png"})))
    ok &= refuses("shards read off two different pdfs stitched into one volume",
                  lambda t: (shard(t, 4, 1, 1, {"1": CARD}),
                             shard(t, 4, 2, 2, {"2": BLANK}, pdf_sha="cafe")))
    ok &= refuses("a volume assembled with a page range missing",
                  lambda t: (shard(t, 4, 1, 1, {"1": CARD}),
                             shard(t, 4, 3, 3, {"3": BLANK})))
    ok &= refuses("a volume assembled with no shard at all", lambda t: None)

    def ocr_manifest(dom, mutate):
        """Mark volume 1 as OCR-read off one committed shard, then break it."""
        root = dom / "text" / "ocr"
        path = shard(root, 1, 1, 1, {"1": CARD})
        doc = load(dom / "text" / "MANIFEST.json")
        doc["volumes"]["1"]["read_by"] = "ocr"
        doc["volumes"]["1"]["ocr_shards"] = [{"shard": path.name, "first": 1, "last": 1,
                                              "pages": 1, "sha256": sha256_file(path)}]
        dump(dom / "text" / "MANIFEST.json", doc)
        mutate(dom, root, path)

    ok &= run("an OCR shard MANIFEST names that is not committed",
              lambda d: ocr_manifest(d, lambda dom, root, path: path.unlink()))
    ok &= run("an OCR shard edited after the volume was assembled off it",
              lambda d: ocr_manifest(d, lambda dom, root, path: shard(
                  root, 1, 1, 1, {"1": ["Adams family.\n  Cook Co., Ill.\n", "", "", ""]})))
    ok &= run("an OCR shard committed that MANIFEST does not name",
              lambda d: ocr_manifest(d, lambda dom, root, path: shard(
                  root, 1, 9, 9, {"9": BLANK})))

    # The reading rules themselves, on the cards that bought each one (T-0600, and
    # REGNAL before it). These are not gate assertions — they are what the extractor
    # keeps and refuses — so they are asserted directly on `buckets_of` and named by
    # the record whose adjudication is the evidence.
    for label, body, want in (
        ("the state banner absorbed as a card body (nbi_v02_1675)", "Illinois.", []),
        ("the banner in the OCR's own spelling (nbi_v02_1027)", "IlllNOiS.", []),
        ("a call-number column wrecked down to the stroke", "111. P 85132.8", []),
        ("a call number standing where the locality would (nbi_v02_1106)",
         "III, Hepgoed fam. (He'agaod. W.l 1898. See lad", []),
        ("the regnal Calendarium, which REGNAL already refused",
         "England. (Roberts, C., Ed. Calendarium, Hen. III. and Edw. I. 1865.)", []),
        ("the regnal Calendarium with its regnal year wrecked (nbi_v03_0614, T-0766)",
         "\u2014 Ingland. (Hoberta, C. _ Calendafium, Han, iii. and i n . |", []),
        ("the same series where the title itself is wrecked (nbi_v01_hibald, T-0766)",
         "tnpltnd. IRc4xrlt. C., Ed. Ctllndvlum, Hex, ill. tod idw I.", []),
        ("a county history the Calendarium rule must not take (T-0766's measured cost)",
         "j* \" 6 ' Co., Ill, (Cicncharu, R.) I882l pt.2t", ["illinois_abbreviated"]),
        ("the regnal Calendarium with its regnal year wrecked (T-0766)",
         "\u2014 Ingland. (Hoberta, C. _ Calendafium, Han, iii. and i n . |", []),
        ("the same series where the title itself is wrecked (T-0766)",
         "tnpltnd. IRc4xrlt. C., Ed. Ctllndvlum, Hex, ill. tod idw I.", []),
        ("a county history the Calendarium rule must not take (T-0766's measured cost)",
         "j* \" 6 ' Co., Ill, (Cicncharu, R.) I882l pt.2t", ["illinois_abbreviated"]),
        ("a wrapped locality, which the call-number rule must not touch",
         "III. f(Moses, J, j n d Kirkland, J.) I89J,", ["illinois_abbreviated"]),
        ("a wrecked reading that still carries its date (nbi_v01_1796's class)",
         "Chicago,'I;....' . .' 1895:", ["chicago"]),
        ("an ordinary Cook County card", "Cook Co.. I l l (La Sa'le Bock Co., Pub.l I9CB,",
         ["cook_county"]),
        # T-0765 — the page list, and the two wrecked Chicagos it must not reach.
        ("a page list that reaches page 111 (nbi_v01_1054)",
         "Ura.H.D.,Ed.) v . l . 1003:145,111.", []),
        ("the illustration note, page 203 illustrated (nbi_v01_1707)",
         "\u2014Delano fam. (Delano, J, A.) 1899: 203,ill.", []),
        ("Chicago with its trailing o read as a nought (nbi_v02_0809)",
         "\u00ab\u00abg0, III. ((-'cs,'. i . \u2022 .", ["illinois_abbreviated"]),
        ("Chicago wrecked to a stop and a nought (nbi_v02_1144)",
         "> \u2014 Chiear.0, 111., Create and conte of", ["illinois_abbreviated"]),
        ("a page list the OCR ran into the word before it, kept on purpose (nbi_v03_0596)",
         "I \\ (Boogher. W.P.) 1899il09,lll,113.", ["illinois_abbreviated"]),
    ):
        got = buckets_of(body)
        if got != want:
            print("  DID NOT HOLD: %s — buckets_of(%r) = %r, wanted %r"
                  % (label, body, got, want))
            ok = False
        else:
            print("  holds: %s" % label)
            fired.append(label)

    if not ok:
        print("SELF-TEST FAIL")
        return 1
    print("SELF-TEST PASS — %d case(s)" % len(fired))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--parse", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--probe", action="store_true",
                    help="read a fixed page sample both ways and write the comparison "
                         "to text/vol_NN_probe.json")
    ap.add_argument("--self-test", action="store_true", dest="self_test")
    ap.add_argument("--volume", type=int, default=1, choices=sorted(VOLUMES))
    ap.add_argument("--pdf", type=Path)
    ap.add_argument("--ocr", action="store_true",
                    help="read the page images instead of the embedded text layer "
                         "(volume 4 — see the OCR path)")
    ap.add_argument("--pages", help="A-B: read only this page range and commit its "
                                    "shard. Without it, --extract --ocr stitches every "
                                    "committed shard and assembles the volume.")
    ap.add_argument("--dpi", type=int, default=OCR_DPI)
    ap.add_argument("--psm", default=OCR_PSM)
    ap.add_argument("--workers", type=int, default=OCR_WORKERS)
    args = ap.parse_args(argv)

    if args.extract:
        if not args.pdf:
            raise SystemExit("--extract needs --pdf: the volume is not committed, and "
                             "MANIFEST.json says where to fetch it")
        if args.pages and not args.ocr:
            raise SystemExit("--pages is the OCR path's resume switch and means nothing "
                             "without --ocr: pdftotext reads the whole volume at once")
        if args.pages:
            m = re.fullmatch(r"\s*(\d+)\s*-\s*(\d+)\s*", args.pages)
            if not m:
                raise SystemExit("--pages wants A-B, got %r" % args.pages)
            first, last = int(m.group(1)), int(m.group(2))
            shard = ocr_range(args.volume, args.pdf, first, last,
                              dpi=args.dpi, psm=args.psm, workers=args.workers)
            print("volume %d: pages %d-%d read into %s"
                  % (args.volume, first, last, shard.name))
        elif args.ocr:
            out = extract_ocr(args.volume, args.pdf)
            print("volume %d: %d cards assembled, %d kept, from %d OCR shard(s) over "
                  "%d pages" % (args.volume, out["cards"], out["kept"], out["shards"],
                                out["pages"]))
        else:
            out = extract(args.volume, args.pdf)
            print("volume %d: %d cards assembled, %d kept" % (args.volume, out["cards"],
                                                                out["kept"]))
    if args.probe:
        if not args.pdf:
            raise SystemExit("--probe needs --pdf")
        doc = probe(args.volume, args.pdf, dpi=args.dpi, psm=args.psm,
                    workers=args.workers)
        print(json.dumps({"totals": doc["totals"], "ocr_cost": doc["ocr_cost"]},
                         indent=2, ensure_ascii=False))
    if args.parse:
        counts = parse(args.volume)
        print(json.dumps(counts, indent=2, ensure_ascii=False))
    if args.self_test:
        return self_test()
    if args.check:
        bad = check()
        for line in bad:
            print("  " + line)
        print("newberry index: %s" % ("FAIL (%d)" % len(bad) if bad else "ok"))
        return 1 if bad else 0
    if not (args.extract or args.parse or args.check or args.self_test
            or args.probe):
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
