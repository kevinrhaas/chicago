#!/usr/bin/env python3
"""Printed pages 47-50 of Fergus 1839: the Fort Dearborn Addition sale, and the
population table (T-0666).

`read_fergus_1839.py` read the alphabetical directory (printed 5-36) and the churches
and hotels (printed 37); `read_fergus_1839_election.py` read the charter election of
2 May 1837 (printed 40-46). These are the last four pages of the appendices, and they
are two different objects on the same sheets:

  printed 47-49 (leaves 59-61)  LOTS SOLD IN FT. DEARBORN ADDITION TO THE TOWN OF
                                CHICAGO, from the 10th to the 24th June, 1839 — the
                                Beaubien, or Reservation, lands. Block, lot, bidder
                                and amount, in four columns twice over per page.
  printed 50   (leaf 62)        POPULATION OF CHICAGO — the volume's own year-by-year
                                table, 1835 to 1876, plus two projections.

  tools/read_fergus_1839_lots.py --map      RE-DERIVE the row map from the scan (NETWORK)
  tools/read_fergus_1839_lots.py --build    write the two claims files
  tools/read_fergus_1839_lots.py --check    rebuild in memory and diff (the gate)
  tools/read_fergus_1839_lots.py --report    the reading counted, and what it could not read
  tools/read_fergus_1839_lots.py --self-test  the three judging rules, fired against breakage

WHY THERE IS A ROW MAP. Both objects are set in columns, and archive.org's OCR reads a
columned page in the order the scanner met the ink, not the order the printer set it.
The flat text of leaf 60 runs the whole left column, then the right column's numbers,
then the right column's names — so a bidder read off the committed text lands beside
somebody else's lot, and the population table's flat text puts 1863 under 1849. The
parent ticket said so and said not to read it off the flat text.

The fix is the one thing the flat text threw away: the word COORDINATES the OCR
carries. `--map` fetches `fergusdirectoryo00ferg_djvu.xml`, splits each page at its
gutter, groups words into printed ROWS by their vertical centre and into CELLS by the
column bands written out below, and commits what it found as
`data/research/directories/fergus_1839_lots_rowmap.json` — for every cell, the exact
[line, from, to] spans of the committed page text it is made of. That is the same
standing as the committed page text itself: derived from the scan by a re-runnable
rule, over the network, and therefore not in `check.sh`. What IS in `check.sh` is
`--check`, which rebuilds the claims offline out of the committed text plus the map,
and `research_domains.py --check`, which rebuilds every quote out of the committed
text through those same spans — so a span that points at the wrong ink fails the gate.

THE COLUMN BANDS ARE WRITTEN OUT, NOT SNIFFED. Six half-pages, six lines of table.
The three sheets are set at three different offsets across the page and a rule that
found the columns for one found the running head for another; T-0664 wrote its line
map out by eye for the same reason, and this is that map one step less by eye.

WHAT DATE THIS IS. The sale ran 10-24 June 1839, so every lot claim carries
`describes_date: "1839-06"` and NOT 1835. These are the Fort Dearborn reservation
lands, which in 1835 were the garrison's and were not lots at all: the ground is south
and east of the river mouth and the plat is four years after the scene date. A bidder
here is a name that MAY corroborate a man in the town and never mints one, and nothing
in this file mints or regrades anybody. The population table's rows each carry the
year the FIGURE describes, which for the first row is 1835.

THE COMPILER'S WARNING BINDS THESE PAGES TOO. Printed page 3: the volume is Fergus's
1876 completion, out of Old Settlers' recollections, of a list he set up from memory
in 1839. The sale list reads like a clerk's abstract and may well be one, but this
reading cannot show that it is, so it is graded as everything else in the volume is.

WHAT IT REFUSES TO READ. A great many of the numerals in this table are destroyed in
the scan — lot 33 prints as `'l ">` over two lines, $303 as `3°3` and `jjj`, $511 as
`51 1`, and printed page 49's left-hand lot column collapses after two lines into a
smear of rotated type (`<J\\Ui`, `00^1`, `In)`). Every such cell is committed with its value NULL and
its ink kept verbatim in `as_printed`, never guessed from the run it sits in. The
sequence would usually give it away, and a number recovered from its neighbours is an
inference wearing a reading's clothes.

WHERE THEY ARE READ INSTEAD (T-0679). The page images are the same scan the OCR is of,
at the same 2238 x 3640 the row map's coordinates are written in, so every cell the row
map places can be cropped off the image and read by eye. That reading is committed as
`data/research/directories/fergus_1839_lots_corrections.json` — the ONE hand-authored
file in this pass — and `--build` applies it. Two rules keep it from becoming a place to
put guesses:

  * EVERY ENTRY ASSERTS THE INK IT CORRECTS. A correction names the `as_printed` string
    the generated cell carries today, and a mismatch is a hard failure rather than a
    silent write. A re-map that moves a row cannot slide somebody else's lot number
    under a correction.
  * A CORRECTED ROW IS REGRADED `scan_verified`, and since T-0779 that grade covers the
    WHOLE row — block, lot, amount, whether the lot was withheld, AND the bidder. T-0679
    deliberately left the bidder column alone and said so; T-0779 read all six half-page
    bidder columns off the same images and corrected the thirteen names the scan mangled
    and the three ditto marks it mapped no ink to. T-0910 added the third bidder repair,
    `bidder_brace`: the one lot on these pages that a printer's BRACE gathers under a
    name rather than under *Reserved.* A row that carries no correction is still
    `transcription_mediated`, which is what its numerals are.

What the image settles is the ink, not the sequence: where the page prints nothing —
a braced run of reserved lots sharing one price, the blank line between two blocks —
the correction fills nothing and says why. A brace that gathers a lot under a NAME is
the one place that rule is not enough, because the lot is sold and reaches the reading
with no bidder at all; see `bidder_brace` in the row loop, which gives it the name its
brace carries and still refuses to divide the one price printed over the pair.

AND THE ROW THE SCAN HAS NO INK FOR AT ALL (T-0778). A correction reaches a cell the row
map gathered; it cannot mint a row, and printed page 47 needs one. That half ends on
block 5, whose lots 1 to 5 are braced against a single *Reserved.*, and the OCR mapped
words to four of the five — so the reading held 267 rows where the page prints 268 and
block 5 jumped from lot 4 to lot 6. `--map` cannot gather ink that is not in the scan, so
the corrections file gains an `added_rows` section instead, and `added_row()` below states
the three assertions that keep it from becoming a place to put rows that were never
printed. The added row is numbered AFTER the last mapped row rather than in its printed
position, because fourteen household cards and four sidecars cite `f1839_lot` ids and a
positional insert would move every one of them after this page onto ink it was not
written against.
"""
import json, os, re, statistics, sys, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = os.path.join(ROOT, "data/research/directories")
TEXT = os.path.join(DOMAIN, "text")
MAP = os.path.join(DOMAIN, "fergus_1839_lots_rowmap.json")
LOTS_OUT = os.path.join(DOMAIN, "claims/fergus_1839_ft_dearborn_lots.json")
POP_OUT = os.path.join(DOMAIN, "claims/fergus_1839_population.json")
CORRECTIONS = os.path.join(DOMAIN, "fergus_1839_lots_corrections.json")
COVERAGE = os.path.join(DOMAIN, "coverage.json")

ITEM = "fergusdirectoryo00ferg"
URL = "https://archive.org/download/%s/%s_djvu.xml" % (ITEM, ITEM)
LEAF_TO_PRINTED = -12
SOURCE_ID = "fergus_chicago_directory_1839"

# THE COLUMN BANDS, by leaf and half. `gutter` is the x that divides the page's two
# halves; within a half, a word's LEFT EDGE decides its cell: below `block` it is the
# block number, below `lot` the lot number, below `bidder` the bidder, and anything
# further right is the amount. Read off the word coordinates of these three pages and
# written out here because the three sheets do not share an offset.
BANDS = {
    #  leaf  gutter  half   block   lot   bidder(→amount beyond)
    (59, "L"): dict(lo=0,    hi=1040, block=320,  lot=390,  bidder=860),
    (59, "R"): dict(lo=1040, hi=9999, block=1075, lot=1145, bidder=1600),
    (60, "L"): dict(lo=0,    hi=1230, block=530,  lot=600,  bidder=1100),
    (60, "R"): dict(lo=1230, hi=9999, block=1275, lot=1350, bidder=1850),
    (61, "L"): dict(lo=0,    hi=1030, block=375,  lot=420,  bidder=900),
    (61, "R"): dict(lo=1030, hi=9999, block=1100, lot=1160, bidder=1700),
}
# The population table, printed page 50, is TWO pairs of columns per half.
POP_BANDS = [
    dict(lo=430,  hi=900,  year=600,  first=1835),   # 1835-1848
    dict(lo=1000, hi=1500, year=1200, first=1849),   # 1849-1862
    dict(lo=1550, hi=1990, year=1700, first=1863),   # 1863-1876
]
POP_LEAF = 62
LOT_LEAVES = (59, 60, 61)
# Rows on a page are set about 55 px apart and a cell stands about 40 px tall, so two
# words belong to the same printed row when their vertical centres are within this.
ROW_PX = 34
# The tight first pass. No printed row on these pages sets two of its own cells more
# than this far apart vertically; every gathering past it has to earn its way back.
TIGHT_PX = 12
# The header band of each page: the running head, the title block and the column
# heads. Everything above this y on a lot page is not a row of the table.
TABLE_TOP = {59: 1340, 60: 380, 61: 370, 62: 400}

RESERVED = re.compile(r"reserved|forfeited", re.I)
# A bidder cell is a NAME when it carries a word of three or more letters — every
# surname on these three pages does, and no ditto mark does. Everything else in the
# bidder column is the printer's ditto (`II`, `11`, `It`, `»`, `„`, `"`, `-`) or the
# scan's ruin of one, and it means the name above it.
NAME = re.compile(r"[A-Za-z]{3}")
INT = re.compile(r"^\$?([0-9][0-9,]*)$")


# ---------------------------------------------------------------- the scan (network)

def header_like(line: str) -> bool:
    """fetch_fergus_1839_pages.py's running-head test, verbatim — one definition."""
    s = line.strip()
    if not s or len(s) > 45:
        return False
    if len(s) <= 3:
        return True
    letters = [c for c in s if c.isalpha()]
    return not letters or sum(c.isupper() for c in letters) / len(letters) > 0.7


def page_words(page):
    """Every word of a page as (x0, ycentre, text, line_index, char_from, char_to).

    The line index and the character offsets are into the COMMITTED page text, and
    they are computed by replaying `fetch_fergus_1839_pages.py`'s renderer rather
    than by searching the text for the word — a page with `II` on forty lines cannot
    be searched, only replayed.
    """
    raw = []
    for line in page.iter("LINE"):
        ws = line.findall("WORD")
        if ws:
            raw.append(ws)
    lefts = [int(ws[0].get("coords").split(",")[0]) for ws in raw]
    if not lefts:
        return []
    median = statistics.median(lefts)
    out, head = [], True
    for idx, ws in enumerate(raw):
        text = " ".join((w.text or "") for w in ws)
        prefix = 0
        if head and header_like(text):
            pass
        else:
            head = False
            if lefts[idx] - median > 25:
                prefix = 2
        at = prefix
        for w in ws:
            body = w.text or ""
            x0, y1, x1, y0 = [int(v) for v in w.get("coords").split(",")]
            if body.strip():
                out.append((x0, (y0 + y1) // 2, body, idx + 1, at, at + len(body)))
            at += len(body) + 1
    return out


def rows_of(words, band, names, top):
    """The words of one column-half, gathered into the rows the printer set.

    Grouping by vertical centre alone does not work on printed page 49, whose lines
    are set tight enough that two of them fall inside one row's tolerance: the OCR
    boxes of `S. N. Dexter  305` and `B. McDonald  331` overlap, and a single pass
    welds them into one row bidding $305331. So the gathering is done twice. First a
    TIGHT pass, at a threshold no printed row can straddle, which over-splits every
    row into its cells; then adjacent groups are merged back while they can be — and
    two groups can be merged only when they COLLIDE IN NO COLUMN. Two printed rows
    both carry a bidder and both carry an amount, so they collide and stay apart; the
    three fragments of one printed row land in three different columns and rejoin.
    """
    sel = sorted([w for w in words if band["lo"] <= w[0] < band["hi"] and w[1] >= top],
                 key=lambda w: (w[1], w[0]))
    tight = []
    for w in sel:
        if tight and w[1] - tight[-1][-1][1] <= TIGHT_PX:
            tight[-1].append(w)
        else:
            tight.append([w])

    def columns(group):
        return {c for c, ws in cells_of(group, band, names).items() if ws}

    rows = []
    for group in tight:
        cols = columns(group)
        if rows and group[0][1] - rows[-1][0][-1][1] <= ROW_PX and not (cols & rows[-1][1]):
            rows[-1][0].extend(group)
            rows[-1][1] |= cols
        else:
            rows.append([list(group), cols])
    return [sorted(r[0], key=lambda w: w[0]) for r in rows]


def cells_of(row, band, names):
    """Split one row into its named cells on the band's left-edge thresholds."""
    out = {n: [] for n in names}
    out[names[-1] + "_beyond"] = []
    for w in row:
        for n in names:
            if w[0] < band[n]:
                out[n].append(w)
                break
        else:
            out[names[-1] + "_beyond"].append(w)
    return out


def spans_of(ws):
    """The committed-text spans a cell's words occupy, merged where they adjoin."""
    out = []
    for x0, y, body, line, a, b in sorted(ws, key=lambda w: (w[3], w[4])):
        if out and out[-1]["line"] == line and out[-1]["to"] + 1 == a:
            out[-1]["to"] = b
        else:
            out.append({"line": line, "from": a, "to": b})
    return out


def build_map(xml_path=None):
    data = open(xml_path, "rb").read() if xml_path else \
        urllib.request.urlopen(URL, timeout=240).read()
    pages = ET.fromstring(data).findall(".//OBJECT")
    doc = {"schema": 1,
           "_doc": "GENERATED by tools/read_fergus_1839_lots.py --map, over the network, "
                   "out of the word coordinates of %s_djvu.xml. Every cell names the "
                   "[line, from, to] spans of the committed page text it is made of, so "
                   "the reading built from it is rebuilt and checked OFFLINE. Hand-edit "
                   "and --check says so." % ITEM,
           "generated_by": "tools/read_fergus_1839_lots.py --map",
           "item": ITEM, "lots": [], "population": []}
    for leaf in LOT_LEAVES:
        words = page_words(pages[leaf - 1])
        for half in ("L", "R"):
            band = BANDS[(leaf, half)]
            for row in rows_of(words, band, ["block", "lot", "bidder"], TABLE_TOP[leaf]):
                cells = cells_of(row, band, ["block", "lot", "bidder"])
                amount = cells.pop("bidder_beyond", [])
                doc["lots"].append({
                    "leaf": leaf, "half": half, "y": row[0][1],
                    "block": spans_of(cells["block"]), "lot": spans_of(cells["lot"]),
                    "bidder": spans_of(cells["bidder"]), "amount": spans_of(amount)})
    words = page_words(pages[POP_LEAF - 1])
    for band in POP_BANDS:
        for row in rows_of(words, band, ["year"], TABLE_TOP[POP_LEAF]):
            cells = cells_of(row, band, ["year"])
            figure = cells.pop("year_beyond", [])
            doc["population"].append({
                "leaf": POP_LEAF, "y": row[0][1], "column_first_year": band["first"],
                "year": spans_of(cells["year"]), "figure": spans_of(figure)})
    return doc


# ------------------------------------------------------------------ the reading

def leaf_text(leaf):
    with open(os.path.join(TEXT, "fergus_1839_leaf_%03d.txt" % leaf), encoding="utf-8") as fh:
        return fh.read().splitlines()


def ink(lines, spans):
    """The verbatim ink of a cell, out of the committed text, exactly as its spans cut it."""
    return "\n".join(lines[s["line"] - 1][s["from"]:s["to"]] for s in spans)


def flat(text):
    return re.sub(r"\s+", " ", text).strip()


def as_int(text):
    m = INT.match(flat(text).replace(" ", ""))
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except ValueError:
        return None


def reads_as_ditto(bidder_ink: str, amount_ink: str) -> bool:
    """A MARK IN THE BIDDER COLUMN IS A DITTO ONLY WHERE A PRICE IS PRINTED.

    The printer's brace, which gathers the reserved lots of a block, breaks into the
    same one- and two-character wreckage the ditto does — a paren, a semicolon, a
    `J`, a backslash, a `1`, an `II` — and reading a brace as a ditto hands the man
    above somebody else's lot. A
    lot that sold has an amount printed against it and a lot held back has none, so
    INK in the amount column is what separates them. Ink, not a readable number:
    twenty-two of these prices are wreckage too, and `45o` is still a price.
    """
    if not bidder_ink.strip() or RESERVED.search(bidder_ink) or NAME.search(bidder_ink):
        return False
    return bool(amount_ink.strip())


def carry_block(block, lot, last_block, last_lot):
    """THE BLOCK IS CARRIED, AND SAYS SO. Returns (block, carried, last_block, last_lot).

    A block number is printed once, against the first lot of its run, and governs
    until the next one. Carrying it is an inference and it is flagged on every row
    that takes it. It is carried only while the lot numbers keep RISING: a lot that
    restarts is a new block whose number the scan lost, and the run stops there
    rather than lending block 10 to blocks 11 and 12 the way printed page 49's ruined
    lot column would invite.
    """
    if block is not None:
        return block, False, block, lot if lot is not None else 0
    if last_block is not None and (lot is None or lot > last_lot):
        return last_block, True, last_block, lot if lot is not None else last_lot
    if lot is not None:
        return None, False, None, None
    return None, False, last_block, last_lot


def corrections():
    """The hand-authored page-image reading, keyed the way each half is applied.

    Lot rows are keyed by claim id, population rows by the row map's own
    (column_first_year, y) — the population correction has to reach a row the reading
    DROPS, the 1840 line, which never gets an id at all."""
    doc = json.loads(open(CORRECTIONS, encoding="utf-8").read())
    pop = {(r["column_first_year"], r["y"]):
           {k: v for k, v in r.items() if k in ("year", "figure")}
           for r in doc["population"]}
    return doc["lots"], pop, doc.get("added_rows", [])


def added_row(spec, lots, rowmap, lines, seq):
    """One printed row the OCR mapped NO ink to, put back off the page image (T-0778).

    A CORRECTION AND AN ADDITION ARE NOT THE SAME THING. A correction reaches a cell the
    row map already gathered and replaces the number the scan ruined; the assertion that
    makes it safe is the ink it was written against. An added row has no ink and therefore
    no cell: printed page 47's right half ends on block 5, whose lots 1 to 5 are braced
    against a single *Reserved.*, and the scan carries words for four of the five. A layer
    that fills cells cannot mint a row, so the row is minted here — under three assertions
    that fail LOUDLY rather than duplicate a lot or hang a reading on the wrong page:

      1. THE ROW IT FOLLOWS still reads the block and lot it was written against. A re-map
         that moves the page cannot slide this row in behind somebody else.
      2. THE ROW MAP STILL GATHERS NOTHING in the y band this row occupies. If a later
         --map DOES find the ink — a better scan, a wider window — the addition stops being
         an addition and this raises instead of shipping block 5's lot 5 twice.
      3. THE INK THAT GOVERNS THE ROW is quoted verbatim out of the committed page text.
         The lot NUMERAL is not in the scan and the claim says so — `as_printed` is null on
         every one of its four cells — but the brace's own *Reserved.* is, and that word is
         what the page prints against this lot. The claim quotes it, so the verbatim gate
         in research_domains.py rebuilds this row's quote like every other row's.

    THE ID IS THE NEXT FREE ONE, NOT A POSITIONAL ONE. `f1839_lot%04d` is assigned by
    position, and fourteen household cards and four sidecars cite those ids. Inserting a
    row in the middle of printed page 47 with a positional id would move every id after it
    onto ink it was not written against — silently, on a card a visitor opens. So the row
    is inserted where it was printed and numbered after the last mapped row, and the
    reading order it belongs to is carried by its locator and its block and lot, which is
    where a reader looks for it anyway.
    """
    after = spec["after"]
    prev = next((c for c in lots if c["id"] == after["id"]), None)
    if prev is None:
        raise SystemExit("fergus 1839 lots: added row follows %s, which the reading does "
                         "not hold" % after["id"])
    if (prev["normalized"]["block"], prev["normalized"]["lot"]) != (after["block"], after["lot"]):
        raise SystemExit(
            "fergus 1839 lots: added row follows %s asserting block %s lot %s, and that "
            "claim now reads block %s lot %s — re-read the page image rather than editing "
            "the assertion" % (after["id"], after["block"], after["lot"],
                               prev["normalized"]["block"], prev["normalized"]["lot"]))
    lo, hi = spec["no_row_gathered_between"]
    clash = [r for r in rowmap["lots"] if r["leaf"] == spec["leaf"]
             and r["half"] == spec["half"] and lo <= r["y"] <= hi]
    if clash:
        raise SystemExit(
            "fergus 1839 lots: added row at y %d asserts the row map gathers nothing "
            "between %d and %d on leaf %d %s, and it now gathers %d row(s) there — the ink "
            "is in the scan after all, so gather it rather than adding it"
            % (spec["y"], lo, hi, spec["leaf"], spec["half"], len(clash)))
    span = spec["governing_ink"]
    quote = lines[span["line"] - 1][span["from"]:span["to"]]
    read = spec["read"]
    return {
        "id": "f1839_lot%04d" % seq,
        "kind": "civic",
        "reading": "scan_verified",
        "quote": quote,
        "normalized": {
            "as_printed": {"block": None, "lot": None, "bidder": None, "amount": None},
            "bidder": None,
            "bidder_ditto": False,
            "bidder_braced": False,
            "bidder_wrapped": False,
            "block": prev["normalized"]["block"],
            "block_carried": True,
            "lot": read["lot"],
            "amount_usd": read["amount"],
            "withheld_from_sale": read["withheld"],
            "addition": "Fort Dearborn Addition to the Town of Chicago",
            "row_added_off_the_page_image": True,
        },
        "locator": {
            "text_file": "fergus_1839_leaf_%03d.txt" % spec["leaf"],
            "spans": [span],
            "lines": [span["line"], span["line"]],
            "page": "fergus_1839_leaf_%03d" % spec["leaf"],
            "printed_page": spec["leaf"] + LEAF_TO_PRINTED,
            "column": spec["half"],
        },
        "describes_date": "1839-06",
        "entities": [],
        "town_finding": False,
        "notes": spec["why"],
    }


def apply_fix(fix, field, ink_now, value):
    """One corrected cell: assert the ink it was written against, then return the reading.

    THE ASSERTION IS THE WHOLE SAFETY OF THIS LAYER. The corrections file is hand-authored
    against the file --build produced on the day it was read; if a re-map or a re-fetch
    moves a row, the ink under a correction changes and this raises rather than writing a
    number onto the wrong lot."""
    want = fix.get(field)
    if want is None:
        return value, False
    now = flat(ink_now) or None
    if now != want["was"]:
        raise SystemExit(
            "fergus 1839 lots: correction for %s asserts as_printed %r, the reading now "
            "has %r — re-read the page image rather than editing the assertion"
            % (field, want["was"], now))
    return want["read"], True


def build():
    texts = {leaf: leaf_text(leaf) for leaf in LOT_LEAVES + (POP_LEAF,)}
    rowmap = json.loads(open(MAP, encoding="utf-8").read())
    lot_fixes, pop_fixes, additions = corrections()

    # PASS 1 — the ink of every mapped row, and the WRAPPED NAMES folded back into the
    # row above. A bidder too long for the column is set on a second line, and the OCR
    # gives that line a row of its own: `T. Church and H.` on one, `O. Stone` and the
    # price on the next. A row whose block AND lot cells are empty — not destroyed,
    # EMPTY — carrying a name under a row that has a lot and no price is that second
    # line, and it is folded back rather than shipped as a bidder of its own.
    raw = []
    for row in rowmap["lots"]:
        lines = texts[row["leaf"]]
        cell = {k: ink(lines, row[k]) for k in ("block", "lot", "bidder", "amount")}
        if not any(v.strip() for v in cell.values()):
            continue
        cell["_spans"] = row["block"] + row["lot"] + row["bidder"] + row["amount"]
        cell["_leaf"], cell["_half"] = row["leaf"], row["half"]
        wrapped = (raw and not cell["block"].strip() and not cell["lot"].strip()
                   and NAME.search(cell["bidder"]) and not RESERVED.search(cell["bidder"])
                   and raw[-1]["_leaf"] == row["leaf"] and raw[-1]["_half"] == row["half"]
                   and raw[-1]["lot"].strip() and not raw[-1]["amount"].strip())
        if wrapped:
            prev = raw[-1]
            prev["bidder"] = (prev["bidder"] + "\n" + cell["bidder"]).strip("\n")
            prev["amount"] = (prev["amount"] + "\n" + cell["amount"]).strip("\n")
            prev["_spans"] = prev["_spans"] + cell["_spans"]
            prev["_wrapped"] = True
            continue
        raw.append(cell)

    lots, n, last_bidder, last_block, last_lot = [], 0, None, None, None
    illegible = {"lot": 0, "amount": 0, "block": 0}
    settled = {"lot": 0, "amount": 0, "block": 0, "withheld_from_sale": 0,
               "bidder": 0, "bidder_ditto": 0, "bidder_brace": 0, "rows": 0}
    for cell in raw:
        quote = "\n".join(v for v in (cell["block"], cell["lot"], cell["bidder"],
                                      cell["amount"]) if v)
        spans = cell["_spans"]
        n += 1
        block, lot = as_int(cell["block"]), as_int(cell["lot"])
        if lot == 0:
            lot = None
        amount = as_int(cell["amount"])
        withheld = RESERVED.search(cell["bidder"])
        withheld_word = withheld.group(0).lower() if withheld else None
        named = bool(NAME.search(cell["bidder"])) and not withheld
        ditto = reads_as_ditto(cell["bidder"], cell["amount"])
        # THE BIDDER COLUMN, off the page image (T-0779). Applied HERE and not beside the
        # numeral fixes below, because a bidder is the one cell the rows under it read:
        # `last_bidder` is what every ditto inherits, so a name corrected after it was
        # carried would leave the mangle standing on the ditto rows and only mend the
        # named one. Two kinds, and they are different repairs:
        #   `bidder`       the page prints a name the scan destroyed — `O. II. Thompson`
        #                  for O. H. Thompson. The read name replaces the ink and becomes
        #                  the carry, so the dittos below it inherit the repair.
        #   `bidder_ditto` the page prints a DITTO MARK the OCR mapped no ink to at all,
        #                  so `reads_as_ditto` never saw it and the row lost its bidder.
        #                  Its `read` is the name the mark carries, and it is checked
        #                  against the carry rather than trusted: a ditto that disagrees
        #                  with the name standing above it is a row map that moved, not a
        #                  correction, and it raises like every other broken assertion.
        #   `bidder_brace` the page gathers this lot with the row above it inside a
        #                  printer's BRACE, and sets ONE name and ONE price against the
        #                  pair (T-0910). A brace is not a ditto and is deliberately not
        #                  read as one — `reads_as_ditto` refuses a mark with no price
        #                  beside it precisely so that a brace leg cannot hand the man
        #                  above somebody else's lot — so the braced lot reached the
        #                  reading with no bidder at all. This kind gives it the name its
        #                  brace carries and says HOW it carries it: `bidder_braced` on
        #                  the claim, never `bidder_ditto`, because the page prints no
        #                  mark on this row and a card that said it did would be wrong
        #                  about the ink. The PRICE is not touched: the brace prints one
        #                  amount over several lots and this layer does not divide it.
        fix = lot_fixes.get("f1839_lot%04d" % n, {})
        read_name, fixed_bidder = apply_fix(fix, "bidder", cell["bidder"], None)
        carried_name, fixed_ditto = apply_fix(fix, "bidder_ditto", cell["bidder"], None)
        braced_name, fixed_brace = apply_fix(fix, "bidder_brace", cell["bidder"], None)
        if fixed_bidder:
            named, ditto, last_bidder = True, False, read_name
        elif named:
            last_bidder = re.sub(r"\s+[.,]$", "",
                                 flat(cell["bidder"].replace("\n", " "))).rstrip(",")
        if fixed_ditto:
            if carried_name != last_bidder:
                raise SystemExit(
                    "fergus 1839 lots: the ditto correction for f1839_lot%04d reads %r, "
                    "but the name standing above it is %r — re-read the page image rather "
                    "than editing the assertion" % (n, carried_name, last_bidder))
            ditto = True
        braced = False
        if fixed_brace:
            if braced_name != last_bidder:
                raise SystemExit(
                    "fergus 1839 lots: the brace correction for f1839_lot%04d reads %r, "
                    "but the name standing above it is %r — re-read the page image rather "
                    "than editing the assertion" % (n, braced_name, last_bidder))
            if named or ditto or withheld_word:
                raise SystemExit(
                    "fergus 1839 lots: the brace correction for f1839_lot%04d sits on a "
                    "row that already carries a bidder of its own — a braced lot is one "
                    "the printer left blank, so this is a row map that moved" % n)
            if cell["amount"].strip():
                raise SystemExit(
                    "fergus 1839 lots: the brace correction for f1839_lot%04d sits on a "
                    "row with ink in the amount column — the brace prints ONE price over "
                    "the lots it gathers and this layer does not divide it" % n)
            braced = True
        # WHAT THE SCAN DESTROYED is counted on the OCR's reading, before the page image
        # is allowed to speak: the count describes the scan, not what was rescued from it.
        if cell["block"].strip() and block is None:
            illegible["block"] += 1
        if cell["lot"].strip() and lot is None:
            illegible["lot"] += 1
        if cell["amount"].strip() and amount is None:
            illegible["amount"] += 1

        # THE PAGE IMAGE, where it was read. Applied BEFORE the block is carried, so the
        # carrying re-derives off the settled lot numbers rather than off the ruin —
        # which is the whole reason printed page 49 lost blocks 11 and 12.
        block, fixed_block = apply_fix(fix, "block", cell["block"], block)
        lot, fixed_lot = apply_fix(fix, "lot", cell["lot"], lot)
        amount, fixed_amount = apply_fix(fix, "amount", cell["amount"], amount)
        withheld_word, fixed_withheld = apply_fix(fix, "withheld", cell["bidder"],
                                                  withheld_word)
        if fixed_withheld and withheld_word:
            named, ditto, braced = False, False, False
        for what, did in (("block", fixed_block), ("lot", fixed_lot),
                          ("amount", fixed_amount),
                          ("withheld_from_sale", fixed_withheld),
                          ("bidder", fixed_bidder), ("bidder_ditto", fixed_ditto),
                          ("bidder_brace", fixed_brace)):
            settled[what] += 1 if did else 0
        settled["rows"] += 1 if fix else 0

        block, carried, last_block, last_lot = carry_block(block, lot, last_block, last_lot)
        bidder = last_bidder if (named or ditto or braced) else None
        lots.append({
            "id": "f1839_lot%04d" % n,
            "kind": "person" if bidder else "civic",
            "reading": "scan_verified" if fix else "transcription_mediated",
            "quote": quote,
            "normalized": {
                "as_printed": {k: flat(v) or None for k, v in cell.items()
                               if not k.startswith("_")},
                "bidder": bidder,
                "bidder_ditto": ditto,
                "bidder_braced": braced,
                "bidder_wrapped": bool(cell.get("_wrapped")),
                "block": block,
                "block_carried": carried,
                "lot": lot,
                "amount_usd": amount,
                "withheld_from_sale": withheld_word,
                "addition": "Fort Dearborn Addition to the Town of Chicago",
            },
            "locator": {
                "text_file": "fergus_1839_leaf_%03d.txt" % cell["_leaf"],
                "spans": spans,
                "lines": [min(s["line"] for s in spans), max(s["line"] for s in spans)],
                "page": "fergus_1839_leaf_%03d" % cell["_leaf"],
                "printed_page": cell["_leaf"] + LEAF_TO_PRINTED,
                "column": cell["_half"],
            },
            "describes_date": "1839-06",
            "entities": [bidder] if bidder else [],
            "town_finding": False,
            "notes": "; ".join(v["why"] for v in fix.values() if v.get("why")) or None,
        })

    # THE ROWS THE OCR MAPPED NO INK TO, put back off the page image. Applied after the
    # loop above and never inside it, so that neither the ids nor the carried block move:
    # an added row is numbered after the last mapped row and inserted where it was
    # printed. See added_row() for the three assertions that hold it in place.
    added = 0
    for spec in additions:
        row = added_row(spec, lots, rowmap, texts[spec["leaf"]], n + added + 1)
        lots.insert(1 + next(i for i, c in enumerate(lots) if c["id"] == spec["after"]["id"]), row)
        added += 1

    pop, m, unread, pop_settled = [], 0, [], {"year": 0, "figure": 0}
    for row in rowmap["population"]:
        lines = texts[POP_LEAF]
        year_ink, figure_ink = ink(lines, row["year"]), ink(lines, row["figure"])
        year = as_int(re.sub(r"[.\s]+$", "", flat(year_ink)))
        fix = pop_fixes.get((row["column_first_year"], row["y"]), {})
        # The year is settled FIRST, because a row whose year will not parse is dropped
        # here and the 1840 line is exactly that row.
        year, fixed_year = apply_fix(fix, "year", year_ink, year)
        if year is None or not (1835 <= year <= 1876):
            if year_ink.strip() and figure_ink.strip():
                unread.append(flat(year_ink + " " + figure_ink))
            continue
        m += 1
        figure = as_int(figure_ink.replace(".", ""))
        figure, fixed_figure = apply_fix(fix, "figure", figure_ink, figure)
        pop_settled["year"] += 1 if fixed_year else 0
        pop_settled["figure"] += 1 if fixed_figure else 0
        spans = row["year"] + row["figure"]
        pop.append({
            "id": "f1839_pop%02d" % m,
            "kind": "civic",
            "reading": "scan_verified" if fix else "transcription_mediated",
            "quote": "\n".join(v for v in (year_ink, figure_ink) if v),
            "normalized": {
                "as_printed": {"year": flat(year_ink) or None,
                               "figure": flat(figure_ink) or None},
                "year": year,
                "population": figure,
                "of": "Chicago",
                "column_reconstructed": True,
            },
            "locator": {
                "text_file": "fergus_1839_leaf_%03d.txt" % POP_LEAF,
                "spans": spans,
                "lines": [min(s["line"] for s in spans), max(s["line"] for s in spans)],
                "page": "fergus_1839_leaf_%03d" % POP_LEAF,
                "printed_page": POP_LEAF + LEAF_TO_PRINTED,
            },
            "describes_date": "%d" % year,
            "entities": [],
            "town_finding": True,
            "notes": "; ".join(v["why"] for v in fix.values() if v.get("why")) or
                     (None if figure is not None else
                      "the figure is destroyed in the scan and is left null rather than "
                      "recovered from the run it sits in"),
        })

    corpus = {
        "item": ITEM,
        "url": "https://archive.org/details/%s" % ITEM,
        "what": "Allen County Public Library Genealogy Center scan of Robert Fergus, "
                "Fergus' Directory of the City of Chicago, 1839 (Chicago: Fergus Printing "
                "Company, 1876). 86 leaves. Printed pages 47-50 are leaves 59-62.",
        "committed": True,
        "how": "tools/fetch_fergus_1839_pages.py commits the page text; "
               "tools/read_fergus_1839_lots.py --map commits the row map that puts the "
               "columns back in printed order, out of the same scan's word coordinates; "
               "fergus_1839_lots_corrections.json holds the numerals that were read off "
               "the page images themselves, because the OCR destroyed them.",
    }
    lots_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_fergus_1839_lots.py --build out of the committed "
                "page text in data/research/directories/text/ and the committed row map "
                "beside it. Hand-edit and --check says so. Fergus' Directory of the City of "
                "Chicago, 1839, printed pages 47-49: LOTS SOLD IN FT. DEARBORN ADDITION TO "
                "THE TOWN OF CHICAGO, from the 10th to the 24th June, 1839, inclusive — "
                "known as the Beaubien, or Reservation, lands. One claim per printed row: "
                "block, lot, bidder and amount.",
        "generated_by": "tools/read_fergus_1839_lots.py --build",
        "source_id": SOURCE_ID,
        "corpus": corpus,
        "reading_note": "TWO GRADES, ROW BY ROW. A row graded transcription_mediated is "
                        "archive.org's OCR of the printed page, machine-read and not "
                        "checked against the image by eye. A row graded scan_verified had "
                        "its NUMERAL columns — block, lot, amount, and whether the lot was "
                        "withheld — read off the page image by T-0679, and the reading it "
                        "was made against is committed as "
                        "fergus_1839_lots_corrections.json. Since T-0779 that grade covers "
                        "the bidder column too: all six half-page bidder columns were read "
                        "off the same images, and the names the scan mangled, the ditto "
                        "marks it mapped no ink to and — since T-0910 — the one braced lot "
                        "it left bidderless are corrected there and nowhere else. The "
                        "damage is left in every cell on purpose — the "
                        "ink stays in as_printed beside the number the image settled, "
                        "because a tidied cell cannot be found again on the page. The "
                        "columns are the hazard here rather than the spelling: the OCR "
                        "reads a four-column table in the order the scanner met the ink, "
                        "so the printed rows are put back from the word coordinates by "
                        "--map and every cell carries the spans of the committed text it "
                        "is made of. A numeral is still never recovered from the RUN it "
                        "sits in: what the image does not print, no row here invents.",
        "date_note": "1839, NOT 1835. The sale ran 10-24 June 1839 and every claim carries "
                     "describes_date 1839-06. This ground is the Fort Dearborn reservation, "
                     "which in July 1835 was the garrison's and was not lots at all, so no "
                     "row here places anybody in the scene. A bidder is a name that MAY "
                     "corroborate a man in the town; under the ratified grading ladder a "
                     "later appearance alone never makes an 1835 resident, and nothing in "
                     "this file mints or regrades anybody.",
        "compiler_note": "Printed page 3, already recorded in data/sources/%s.json: the "
                         "volume is Fergus's 1876 completion, out of Old Settlers' "
                         "recollections, of a list he set up from memory in 1839. This list "
                         "reads like a clerk's abstract of the sale and may well be one; "
                         "this reading cannot show that it is, so it is graded as the rest "
                         "of the volume is." % SOURCE_ID,
        "ditto_note": "The printer sets a repeated bidder as a ditto mark, and the scan "
                      "ruins it into II, 11, It, », „ and a dozen more. A bidder cell with "
                      "no word of three or more letters is read as a ditto and carries the "
                      "name above it with bidder_ditto true — the mark IS the printer "
                      "saying the same name, so the name is not an inference, but which "
                      "mark it was is not recoverable and the ink is kept in as_printed.",
        "brace_note": "A BRACE IS NOT A DITTO, and one lot on these pages turns on the "
                      "difference (T-0910). The printer gathers a run of lots with a "
                      "brace and sets ONE entry against the whole run: on block 2's lots "
                      "8-10, block 4's lots 1-6 and block 5's lots 1-5 that entry is "
                      "Reserved. and there is no bidder to lose, but on block 4's lots 39 "
                      "and 40 it is `C. Walker,` and $408 the pair. The brace leg breaks "
                      "into the same wreckage a ruined ditto does, so reads_as_ditto "
                      "refuses any mark with no price beside it rather than hand the man "
                      "above somebody else's lot — which left lot 40 with no bidder at "
                      "all. Such a row now carries bidder_braced true and bidder_ditto "
                      "FALSE: the name is the brace's, the page prints no mark on the row "
                      "itself, and the amount stays null because the one price is printed "
                      "over the pair and this reading does not divide it.",
        "counts": {
            "claims": len(lots),
            "rows": len(lots),
            "rows_the_row_map_gathered": n,
            "rows_added_off_the_page_image": added,
            "bidders_named": len({c["normalized"]["bidder"] for c in lots
                                  if c["normalized"]["bidder"]}),
            "rows_with_a_lot_number": sum(1 for c in lots if c["normalized"]["lot"] is not None),
            "rows_with_an_amount": sum(1 for c in lots
                                       if c["normalized"]["amount_usd"] is not None),
            "cells_the_scan_destroyed": illegible,
            "cells_settled_off_the_page_image": settled,
            "rows_scan_verified": sum(1 for c in lots if c["reading"] == "scan_verified"),
            "aggregate_printed_usd": 100000,
        },
        "claims": lots,
    }
    pop_doc = {
        "schema": 1,
        "_doc": "GENERATED by tools/read_fergus_1839_lots.py --build. Hand-edit and --check "
                "says so. Fergus' Directory of the City of Chicago, 1839, printed page 50: "
                "POPULATION OF CHICAGO, the volume's own year-by-year table.",
        "generated_by": "tools/read_fergus_1839_lots.py --build",
        "source_id": SOURCE_ID,
        "corpus": corpus,
        "reading_note": "transcription_mediated. THE PAIRING IS RECONSTRUCTED AND SAYS SO. "
                        "The table is set as three pairs of year-and-figure columns and the "
                        "OCR interleaves them — its flat text puts 1863 under 1849 and "
                        "strands the last column's figures — so no row here is read off the "
                        "committed text in reading order. Each row is put back from the word "
                        "coordinates: a year and a figure are one row when their vertical "
                        "centres agree inside 28 px within one pair of columns, and every "
                        "claim carries column_reconstructed true. THE 1840 LINE WAS MISSING "
                        "ENTIRELY and is not any more: the scan prints it `1 S40 .... "
                        "4,47!*`, neither half of which parses, so the reading dropped the "
                        "row — T-0679 read the page image, where it prints 1840 .... 4,479, "
                        "and that row is now here and graded scan_verified. Five more "
                        "figures the leader dots had swallowed were read the same way. The "
                        "census of 1840 is held elsewhere in this repo and was not borrowed "
                        "for any of it.",
        "date_note": "Each claim's describes_date is the year the FIGURE describes, not the "
                     "year of the volume. The first row is the one this project wants: "
                     "Fergus prints Chicago's 1835 population as 3,265.",
        "projection_note": "The table's last two lines are not counts and are not read here: "
                           "1885 estimated by Jno S. Wright at 1,000,000 and 1911 estimated "
                           "by J. X. Balestier at 2,000,000. They are projections printed in "
                           "1876 and belong with the volume's rhetoric, which follows them on "
                           "the same page.",
        "counts": {"claims": len(pop),
                   "years": [c["normalized"]["year"] for c in pop],
                   "cells_settled_off_the_page_image": pop_settled,
                   "figures_read": sum(1 for c in pop if c["normalized"]["population"] is not None),
                   "figures_the_scan_destroyed": sum(1 for c in pop
                                                     if c["normalized"]["population"] is None),
                   "rows_whose_year_the_scan_destroyed": unread},
        "claims": pop,
    }
    return lots_doc, pop_doc


def write(path, doc):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def self_test() -> int:
    """The three rules that do this reading's judging, fired against cases that break them.

    Every one of them is a rule about what NOT to write down, which is the kind that
    fails silently: a brace read as a ditto, a block lent to its neighbour and a
    numeral recovered from its run all produce a fuller-looking file, and nothing else
    in check.sh would notice.
    """
    bad = []

    def want(got, expect, what):
        if got != expect:
            bad.append("%s: expected %r, got %r" % (what, expect, got))

    # 1. the ditto, and the brace that looks exactly like one
    want(reads_as_ditto("II", "211"), True, "a ditto with a price is a ditto")
    want(reads_as_ditto("II", "45o"), True, "a ditto with a RUINED price is still a ditto")
    want(reads_as_ditto(")", ""), False, "a brace with no price is not a ditto")
    want(reads_as_ditto("J", ""), False, "a brace leg with no price is not a ditto")
    want(reads_as_ditto("A. Bronson,", "303"), False, "a name is not a ditto")
    want(reads_as_ditto("' Reserved.", ""), False, "a withheld lot is not a ditto")
    want(reads_as_ditto("", "211"), False, "a price with no mark at all invents no bidder")

    # 2. the block, carried only while the lots rise
    want(carry_block(4, 1, None, None), (4, False, 4, 1), "a printed block is not carried")
    want(carry_block(None, 2, 4, 1), (4, True, 4, 2), "a rising lot carries its block")
    want(carry_block(None, 1, 4, 22), (None, False, None, None),
         "a lot that restarts ends the run rather than lending block 4 to block 5")
    want(carry_block(None, None, 4, 3), (4, True, 4, 3),
         "a row whose lot the scan destroyed stays inside the run it sits in")
    want(carry_block(None, 3, None, None), (None, False, None, None),
         "no run, no block")

    # 3. the numerals, refused rather than repaired
    want(as_int("3\u00b03"), None, "$303 printed as 3\u00b03 is not read as 33")
    want(as_int("jjj"), None, "a destroyed price is not read")
    want(as_int("51 1"), 511, "a price the OCR broke into two words rejoins — the "
         "CELL is the unit of a reading here, and both halves are its own ink")
    want(as_int("$2657"), 2657, "a clean price is read")
    want(as_int("1,557"), 1557, "a clean price with a comma is read")

    # 4. and the three of them, on the committed reading itself
    lots, pop = build()
    by_id = {c["id"]: c for c in lots["claims"]}
    block4 = [c for c in lots["claims"] if c["normalized"]["block"] == 4
              and c["locator"]["printed_page"] == 47]
    braced = [c for c in block4 if (c["normalized"]["lot"] or 99) <= 6]
    want(bool(braced), True, "printed page 47 still has block 4's braced lots")
    want([c["normalized"]["bidder"] for c in braced], [None] * len(braced),
         "the brace over block 4's first six lots gives nobody a lot")

    # 5. and the ONE brace on these pages that gathers a lot under a NAME (T-0910)
    by_brace = [c for c in lots["claims"] if c["normalized"]["bidder_braced"]]
    want([c["id"] for c in by_brace], ["f1839_lot0060"],
         "block 4's lot 40 is the only lot on printed pages 47-49 a brace carries under a "
         "bidder's name — every other braced run reads Reserved.")
    lot40 = by_id["f1839_lot0060"]
    want(lot40["normalized"]["bidder"], "C. Walker",
         "and it carries the name its brace carries")
    want(lot40["normalized"]["bidder_ditto"], False,
         "without claiming the page printed a ditto mark on it, because it printed none")
    want(lot40["normalized"]["amount_usd"], None,
         "and with no price of its own: $408 is printed over the pair and is not divided")
    want(by_id["f1839_lot0059"]["normalized"]["amount_usd"], 408,
         "the price stays where the printer set it, on lot 39")
    bidderless = [c["id"] for c in lots["claims"]
                  if c["normalized"]["bidder"] is None
                  and not c["normalized"]["withheld_from_sale"]]
    want(bidderless, ["f1839_lot0005", "f1839_lot0173"],
         "and the only rows left with neither a bidder nor a withholding are the two that "
         "carry no lot number either — a speck and the rule between two blocks")
    p49 = [c for c in lots["claims"] if c["locator"]["printed_page"] == 49
           and c["locator"]["column"] == "L"]
    want(bool(p49), True, "printed page 49's left half is still read")
    smeared = [c for c in p49 if (c["normalized"]["as_printed"]["lot"] or "") in
               ("<J\\Ui", "00^1", "'O", "In)", "Oo", "4-", "Qn^i")]
    want(len(smeared) >= 6, True,
         "printed page 49's rotated lot column is still in the reading, as ink")
    want({c["normalized"]["lot"] for c in smeared}, {5, 7, 9, 12, 13, 14, 15, 17},
         "and those eight are settled off the page image, in printed order")
    want({c["reading"] for c in smeared}, {"scan_verified"},
         "which is the grade a cell read off the image carries")
    want({c["normalized"]["block"] for c in smeared}, {10},
         "and the block they belong to is carried again, now that their lots rise")
    want(sorted({c["normalized"]["block"] for c in p49}), [10, 11, 12],
         "printed page 49's left half is blocks 10, 11 and 12, whose headings "
         "the ruined column had swallowed")
    unfixed = [c for c in lots["claims"] if c["reading"] == "transcription_mediated"]
    want(all(c["normalized"]["as_printed"]["lot"] != "70" for c in unfixed), True,
         "the one numeral the scan handed over CLEAN AND WRONG — block 9's lot 30, "
         "scanned as 70 — is not left standing as a reading of its own")
    want([c["normalized"]["lot"] for c in lots["claims"]
          if c["normalized"]["as_printed"]["lot"] == "70"], [30],
         "it is 30, off the page image, with the ruin kept in as_printed")
    want(any(c["normalized"]["bidder_ditto"] for c in lots["claims"]), True,
         "the dittoed rows are still read")
    want(1835 in [c["normalized"]["year"] for c in pop["claims"]], True,
         "the population table still opens on 1835")
    want([c["normalized"]["population"] for c in pop["claims"]
          if c["normalized"]["year"] == 1835], [3265],
         "and Fergus still prints 3,265 against it")
    want([c["normalized"]["population"] for c in pop["claims"]
          if c["normalized"]["year"] == 1840], [4479],
         "the 1840 line, which neither half of the OCR would parse, is read off the "
         "page image rather than left as a silent gap")
    want([c["reading"] for c in pop["claims"] if c["normalized"]["year"] == 1840],
         ["scan_verified"], "and it says so in its grade")
    want([c["normalized"]["year"] for c in pop["claims"]],
         list(range(1835, 1877)), "so the table runs 1835 to 1876 with no year missing")

    # 4b. THE ADDED ROW (T-0778). Block 5's lot 5 is printed inside the same brace as
    #     lots 1 to 4 and the OCR mapped it no ink at all, so the row map gathers four
    #     rows where the page prints five.
    b5 = [c for c in lots["claims"] if c["normalized"]["block"] == 5
          and c["locator"]["printed_page"] == 47]
    want([c["normalized"]["lot"] for c in b5], [1, 2, 3, 4, 5],
         "printed page 47's block 5 runs 1 to 5 with no gap — the brace covers five lots")
    want([c["normalized"]["withheld_from_sale"] for c in b5], ["reserved"] * 5,
         "and the one Reserved. over the brace withholds all five")
    want([c["normalized"]["bidder"] for c in b5], [None] * 5,
         "so the brace still gives nobody a lot")
    lot5 = b5[-1]
    want(lot5["normalized"]["as_printed"], {"block": None, "lot": None, "bidder": None,
                                            "amount": None},
         "the added row's own cells are EMPTY in the scan and say so — the numeral was "
         "read off the page image, not recovered from the run it sits in")
    want(lot5["quote"], "Reserved.",
         "and it quotes the ink that governs it, verbatim out of the committed text, so "
         "the verbatim gate rebuilds it like every other row")
    want(lot5["reading"], "scan_verified", "which is the grade a row read off the image carries")
    want(lot5["normalized"]["amount_usd"], None,
         "the brace prints one word and no price, and no price is invented for it")
    # THE IDS DID NOT MOVE. Fourteen household cards and four sidecars cite f1839_lot ids.
    want([by_id["f1839_lot0068"]["normalized"]["lot"],
          by_id["f1839_lot0069"]["normalized"]["lot"]], [4, 6],
         "the added row is numbered after the last mapped row, so inserting it in the "
         "middle of printed page 47 renumbers nothing")
    want(lot5["id"], "f1839_lot%04d" % len(lots["claims"]),
         "and it takes the next free id")
    want(by_id["f1839_lot0069"]["normalized"]["block"], 5,
         "block 5's lot 6 still carries block 5 across the leaf")

    # 4c. and the two assertions that hold it there, fired against breakage
    rowmap = json.loads(open(MAP, encoding="utf-8").read())
    lines = leaf_text(59)
    spec = json.loads(open(CORRECTIONS, encoding="utf-8").read())["added_rows"][0]
    moved = [dict(c) for c in lots["claims"]]
    for c in moved:
        if c["id"] == "f1839_lot0068":
            c["normalized"] = dict(c["normalized"], lot=9)
    try:
        added_row(spec, moved, rowmap, lines, 999)
        bad.append("an added row was applied behind a claim that no longer reads what it "
                   "was written against")
    except SystemExit:
        pass
    gathered = dict(rowmap, lots=rowmap["lots"] + [{"leaf": 59, "half": "R", "y": 3275,
                                                    "block": [], "lot": [], "bidder": [],
                                                    "amount": []}])
    try:
        added_row(spec, lots["claims"], gathered, lines, 999)
        bad.append("an added row was applied although the row map now gathers the ink "
                   "itself, which would ship block 5's lot 5 twice")
    except SystemExit:
        pass

    # 5. the corrections layer's own guard: a correction written against ink that is no
    #    longer there must RAISE, not write its number onto whatever row moved under it.
    try:
        apply_fix({"lot": {"was": "In)", "read": 12}}, "lot", "somebody else's ink", None)
        bad.append("a correction whose as_printed no longer matches was applied anyway")
    except SystemExit:
        pass
    want(apply_fix({"lot": {"was": "In)", "read": 12}}, "lot", "In)", None), (12, True),
         "and a correction whose ink DOES match is applied, and says it was")
    want(apply_fix({}, "lot", "In)", None), (None, False),
         "a cell with no correction is left exactly as the OCR read it")

    if bad:
        print("fergus 1839 lots self-test: " + "; ".join(bad), file=sys.stderr)
        return 1
    print("fergus 1839 lots: the ditto, the carried block, the refused numeral and the "
          "page-image correction all fire")
    return 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if "--map" in sys.argv:
        local = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--from=")), None)
        doc = build_map(local)
        write(MAP, doc)
        print("row map: %d lot rows, %d population rows" % (len(doc["lots"]), len(doc["population"])))
        return 0
    lots_doc, pop_doc = build()
    if "--build" in sys.argv:
        write(LOTS_OUT, lots_doc)
        write(POP_OUT, pop_doc)
        print("  wrote %d lot claims and %d population claims"
              % (len(lots_doc["claims"]), len(pop_doc["claims"])))
        return 0
    if "--report" in sys.argv:
        c = lots_doc["counts"]
        print("FT. DEARBORN ADDITION, 10-24 June 1839 — printed pages 47-49")
        print("  %d printed rows, %d named bidders" % (c["rows"], c["bidders_named"]))
        print("  lot number read on %d rows, amount read on %d" %
              (c["rows_with_a_lot_number"], c["rows_with_an_amount"]))
        print("  cells the scan destroyed: %s" % c["cells_the_scan_destroyed"])
        for claim in lots_doc["claims"]:
            nz = claim["normalized"]
            print("   bk %-4s lot %-4s %-28s %s" % (
                nz["block"] if nz["block"] is not None else "?",
                nz["lot"] if nz["lot"] is not None else "?",
                (nz["bidder"] or nz["withheld_from_sale"] or "?")[:28],
                "$%s" % nz["amount_usd"] if nz["amount_usd"] is not None
                else "(%s)" % (nz["as_printed"]["amount"] or "-")))
        print("POPULATION OF CHICAGO — printed page 50")
        for claim in pop_doc["claims"]:
            nz = claim["normalized"]
            print("   %d  %s" % (nz["year"], nz["population"] if nz["population"] is not None
                                 else "(%s)" % nz["as_printed"]["figure"]))
        return 0
    bad = []
    for path, doc in ((LOTS_OUT, lots_doc), (POP_OUT, pop_doc)):
        if not os.path.exists(path):
            bad.append("%s is not committed" % os.path.basename(path))
        elif json.loads(open(path, encoding="utf-8").read()) != doc:
            bad.append("%s no longer rebuilds out of the committed text and row map"
                       % os.path.basename(path))
    if bad:
        print("fergus 1839 lots: " + "; ".join(bad), file=sys.stderr)
        return 1
    print("fergus 1839 printed 47-50: %d lot claims and %d population claims rebuild"
          % (len(lots_doc["claims"]), len(pop_doc["claims"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
