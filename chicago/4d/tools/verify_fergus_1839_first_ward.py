#!/usr/bin/env python3
"""Fergus's first-ward total against the names he printed, settled off the pixels (T-0667).

    tools/verify_fergus_1839_first_ward.py --build     fetch the leaves, measure, write the record
    tools/verify_fergus_1839_first_ward.py --check     re-fetch and assert the record re-derives
    tools/verify_fergus_1839_first_ward.py --offline   the record still agrees with the claims file

THE QUESTION. `claims/fergus_1839_election_1837.json` reads 167 names in the first ward of
the poll of 2 May 1837 and commits, beside them, Fergus's own table on printed page 46, which
says 170. Five wards agree exactly and this one does not. The claims file said only that
"the page images can say whether the printer dropped names, the OCR did, or the total was
recalled wrong in 1876." This tool is that sentence carried out.

WHAT IT MEASURES, and why it is measured rather than read. A name lost by archive.org's OCR
leaves NO trace in the text — the line is simply not there — so counting the committed text
can never find one. It leaves a very loud trace in the pixels: a printed list is set on a
constant leading, so a dropped line is a DOUBLE GAP in the row grid. So the derivation goes
to the ink:

  1. the ward's block on each leaf is bounded, and the three column bands inside it are found
     as runs of columns carrying ink over the WHOLE block. The gutters on these leaves are
     narrow — 11 px and 22 px on printed page 41 — so the test is not gutter width but the
     fact of a gutter: a column of ink-free scanlines running the full height of a block of
     34 names is a column break and cannot be a word space;
  2. inside each band the text rows are found as runs of scanlines whose ink exceeds 3% of the
     band's width — a threshold above the scanner speck in the margins and below the lightest
     row of small caps on these two leaves;
  3. the row starts are fitted to a grid, and the tool FAILS if any adjacent pair is more than
     1.4x the median leading apart. That is the dropped-line test, and it is the whole point;
  4. nothing may stand outside the block: the scanlines between the last row of the ward and
     the next heading, and between the block and the foot of the page, must carry no row of
     ink at all. That is the test for a name set below the columns.

WHAT IT CANNOT SETTLE, said here because the record says it too. The pixels can say how many
names the printer set and that none was lost between the page and this project. They cannot
say why Fergus's table says three more. Both remain committed, neither is corrected to the
other, and no name is invented to close the gap.

DEPENDENCIES AND NETWORK. Pillow, and archive.org. It is therefore NOT in `check.sh`, which
runs offline in seconds with no third-party imports — the same rule `fetch_fergus_1839_pages.py`
follows for the same reason. `--offline` is the part that needs neither, and it is what a run
with no network can still assert: that the committed record and the committed claims file have
not drifted apart.
"""
import hashlib
import json
import os
import statistics
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data/research/directories/fergus_1839_first_ward_scan.json")
CLAIMS = os.path.join(ROOT, "data/research/directories/claims/fergus_1839_election_1837.json")

ITEM = "fergusdirectoryo00ferg"
# archive.org's leaf index is 0-based; this project's leaf numbering is 1-based, the same
# offset `fetch_fergus_1839_pages.py` uses when it takes OBJECT `leaf - 1` out of the djvu.
IMAGE_URL = "https://archive.org/download/%s/page/n{n}_w2400.jpg" % ITEM
LEAF_TO_PRINTED = -12

# The blocks to measure. `block` is the scanline range the object occupies; `after` is the
# range below it that must carry no row of ink, which is what catches a name set under the
# columns or between the ward and the next heading.
BLOCKS = [
    {"leaf": 53, "what": "the first ward, FOR WILLIAM B. OGDEN",
     "block": [1540, 3420], "after": [3420, 3640], "expect_columns": 3},
    {"leaf": 54, "what": "the first ward, FOR JOHN H. KINZIE",
     "block": [470, 1690], "after": [1690, 1770], "expect_columns": 3},
]

INK = 140            # a scanline pixel darker than this is ink on this scan
ROW_FRACTION = 0.03  # of the band's width, before a scanline counts as a text row
MIN_ROW_PX = 10      # a run shorter than this is speck, not a line of type
MIN_BAND_PX = 40     # a run of inked columns narrower than this is speck, not a column
GAP_RATIO = 1.4      # a leading this much over the median is a dropped line

# Read BY EYE off the crops named here, which is a different act from the measurement above
# and is labelled as one. The box is given so the same pixels can be reopened.
EYE = [
    {"leaf": 58, "printed_page": 46, "box": [300, 1600, 2100, 2450],
     "read": "Total votes in Chicago in 1837 by wards: First 170, Second 238, Third 38, "
             "Fourth 59, Fifth 60, Sixth 144, rule, 709.",
     "note": "The figures are old-style. The first ward's is unambiguously 1-7-0: the tool "
             "exists because 167 and 170 are three apart, and the first thing to rule out "
             "was archive.org's OCR misreading the numeral. It did not."},
    {"leaf": 53, "printed_page": 41, "box": [0, 0, 2238, 3640],
     "read": "Three full columns of 34 names under FIRST WARD. / FOR WILLIAM B. OGDEN:, "
             "Sidney Abel to Colon Ware. No cell holds two names and no name is repeated.",
     "note": "The page carries the ward heading and the candidate heading and nothing else "
             "above the columns; below the last row there is no ink at all."},
    {"leaf": 54, "printed_page": 42, "box": [0, 0, 2238, 3640],
     "read": "Under FOR JOHN H. KINZIE:, columns of 22, 22 and 21 names, L. C. P. Freer to "
             "Edward Colvin. SECOND WARD. follows, about two and a half lines of leading "
             "below the last of them.",
     "note": "Room for one more row in each column was left standing, so the shape of the "
             "block is not evidence that three names were squeezed out for want of space."},
]


def fetch(n: int) -> bytes:
    with urllib.request.urlopen(IMAGE_URL.format(n=n), timeout=180) as fh:
        return fh.read()


def bands(px, w, y0, y1):
    """The column bands: runs of x carrying ink over the full height of the block."""
    on = []
    for x in range(w):
        ink = 0
        for y in range(y0, y1):
            if px[x, y] < INK:
                ink += 1
                if ink > 2:
                    break
        on.append(ink > 2)
    out, s = [], None
    for x, v in enumerate(on):
        if v and s is None:
            s = x
        if not v and s is not None:
            if x - s > MIN_BAND_PX:
                out.append([s, x])
            s = None
    if s is not None and w - s > MIN_BAND_PX:
        out.append([s, w])
    return out


def rows(px, x0, x1, y0, y1):
    """The text rows in one band: runs of scanlines whose ink clears ROW_FRACTION."""
    thr = max(4, int(ROW_FRACTION * (x1 - x0)))
    out, s = [], None
    for y in range(y0, y1):
        ink = 0
        for x in range(x0, x1):
            if px[x, y] < INK:
                ink += 1
                if ink > thr:
                    break
        v = ink > thr
        if v and s is None:
            s = y
        if not v and s is not None:
            if y - s >= MIN_ROW_PX:
                out.append([s, y])
            s = None
    if s is not None and y1 - s >= MIN_ROW_PX:
        out.append([s, y1])
    return out


def measure(spec, raw):
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(raw)).convert("L")
    px = im.load()
    w, h = im.size
    y0, y1 = spec["block"]
    cols = []
    faults = []
    for x0, x1 in bands(px, w, y0, y1):
        rs = rows(px, x0, x1, y0, y1)
        starts = [r[0] for r in rs]
        leads = [starts[i + 1] - starts[i] for i in range(len(starts) - 1)]
        med = statistics.median(leads) if leads else 0
        gaps = [i for i, g in enumerate(leads) if med and g > GAP_RATIO * med]
        if gaps:
            faults.append("leaf %d, band %d-%d: %d gap(s) over %.1fx the leading — a dropped "
                          "line" % (spec["leaf"], x0, x1, len(gaps), GAP_RATIO))
        cols.append({"band": [x0, x1], "rows": len(rs), "first_row_top": starts[0],
                     "last_row_top": starts[-1], "median_leading": med,
                     "leading_min": min(leads) if leads else 0,
                     "leading_max": max(leads) if leads else 0})
    if len(cols) != spec["expect_columns"]:
        faults.append("leaf %d: %d column band(s), expected %d"
                      % (spec["leaf"], len(cols), spec["expect_columns"]))
    a0, a1 = spec["after"]
    stray = rows(px, 200, min(2050, w), a0, min(a1, h))
    if stray:
        faults.append("leaf %d: %d row(s) of ink between %d and %d, below the block"
                      % (spec["leaf"], len(stray), a0, a1))
    return {"leaf": spec["leaf"], "printed_page": spec["leaf"] + LEAF_TO_PRINTED,
            "what": spec["what"], "image": {"url": IMAGE_URL.format(n=spec["leaf"] - 1),
                                            "sha256": hashlib.sha256(raw).hexdigest(),
                                            "size": [w, h]},
            "block": spec["block"], "columns": cols,
            "names": sum(c["rows"] for c in cols)}, faults


def read_claims():
    doc = json.load(open(CLAIMS, encoding="utf-8"))
    per = {}
    for c in doc["claims"]:
        n = c.get("normalized") or {}
        if n.get("role") == "voter" and n.get("ward") == 1:
            per[c["locator"]["text_file"]] = per.get(c["locator"]["text_file"], 0) + 1
    return doc, per


def payload(leaves, faults):
    doc, per = read_claims()
    read = doc["counts"]["counts_read"]["first"]
    printed = doc["counts"]["counts_printed"]["first"]
    measured = sum(l["names"] for l in leaves)
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/verify_fergus_1839_first_ward.py --build. The first ward "
                "of the poll of 2 May 1837, counted off the page images rather than off "
                "anybody's transcription of them, because Fergus's own table says three more "
                "than the names he printed.",
        "generated_by": "tools/verify_fergus_1839_first_ward.py --build",
        "ticket": "T-0667",
        "source_id": doc["source_id"],
        "corpus": {"item": ITEM, "url": "https://archive.org/details/%s" % ITEM,
                   "how": "page/n<leaf-1>_w2400.jpg, the same leaves fetch_fergus_1839_pages.py "
                          "takes the text from, at the scan's own 2238 px width"},
        "method": "Column bands are unbroken runs of x carrying ink over the full height of "
                  "the block, wider than %d px; text rows are runs of scanlines whose ink "
                  "clears %.0f%% of the band's width; a dropped line is an adjacent leading "
                  "over %.1fx the median. Nothing here reads a letter — it counts lines of type."
                  % (MIN_BAND_PX, ROW_FRACTION * 100, GAP_RATIO),
        "measured": {"names_set_by_the_printer": measured, "per_leaf": leaves,
                     "dropped_line_faults": faults},
        "committed_reading": {"claims_file": "claims/fergus_1839_election_1837.json",
                              "first_ward_read": read, "per_leaf": per},
        "fergus_own_table": {"leaf": 58, "printed_page": 46, "first_ward_printed": printed},
        "eye_readings": EYE,
        "settlement": SETTLEMENT,
        "what_this_cannot_settle": CANNOT,
    }

SETTLEMENT = (
    "THE PRINTER SET 167 NAMES AND FERGUS'S TABLE SAYS 170, and the three are missing from the "
    "LIST, not from this project's reading of it. Printed page 41 carries three columns of 34 "
    "under FOR WILLIAM B. OGDEN and printed page 42 carries 22, 22 and 21 under FOR JOHN H. "
    "KINZIE — 167 lines of type, on a leading of 54 px that never once doubles, with no ink "
    "below either block and no cell holding two names. The committed reading has 167, one "
    "claim per line, so archive.org's OCR lost nothing here and neither did the segmenter. "
    "The numeral in the table was reopened for the same reason and it is 170, not a misread "
    "167. Both numbers stand as read; neither is corrected to the other.")

CANNOT = (
    "WHY the table says three more. Two accounts survive the measurement and the pixels choose "
    "between neither. (a) The 1876 compositor dropped three lines while setting a list of 167 "
    "— nothing on the page shows it, but nothing on the page would. (b) The total is the one "
    "number that survived from 1837 and the NAMES are the reconstruction: Fergus's own warning "
    "on printed page 3 says the volume completes, from Old Settlers' recollections, a list set "
    "up from memory in 1839, and the first ward's list reads like one — an alphabetised run of "
    "51 names from Abel to Worthingham, then 51 more in no order at all, which is what a list "
    "looks like when later recollections are appended rather than merged. On (b) the three are "
    "men nobody remembered, and no page image can name them. What the images DO settle is that "
    "they were never in this book to lose.")


def build(check=False):
    leaves, faults = [], []
    for spec in BLOCKS:
        m, f = measure(spec, fetch(spec["leaf"] - 1))
        leaves.append(m)
        faults.extend(f)
    doc = payload(leaves, faults)
    if faults:
        print("\n".join("  " + f for f in faults), file=sys.stderr)
        print("the row grid is not clean — the settlement below is NOT supported", file=sys.stderr)
        return 1
    if check:
        have = json.load(open(OUT, encoding="utf-8"))
        if have != doc:
            print("%s no longer re-derives from the scan — rebuild with --build"
                  % os.path.relpath(OUT, ROOT), file=sys.stderr)
            return 1
        print("fergus 1839 first ward: %d names of type re-derive from %s"
              % (doc["measured"]["names_set_by_the_printer"], ITEM))
        return 0
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print("wrote %s: %d names set, %d read, %d in Fergus's table"
          % (os.path.relpath(OUT, ROOT), doc["measured"]["names_set_by_the_printer"],
             doc["committed_reading"]["first_ward_read"],
             doc["fergus_own_table"]["first_ward_printed"]))
    return 0


def offline():
    doc = json.load(open(OUT, encoding="utf-8"))
    _, per = read_claims()
    bad = []
    if doc["measured"]["names_set_by_the_printer"] != doc["committed_reading"]["first_ward_read"]:
        bad.append("the measured count and the committed reading have drifted apart: %d set, "
                   "%d read" % (doc["measured"]["names_set_by_the_printer"],
                                doc["committed_reading"]["first_ward_read"]))
    if per != doc["committed_reading"]["per_leaf"]:
        bad.append("the claims file's first ward moved: %r, recorded %r"
                   % (per, doc["committed_reading"]["per_leaf"]))
    for leaf in doc["measured"]["per_leaf"]:
        want = doc["committed_reading"]["per_leaf"].get("fergus_1839_leaf_%03d.txt" % leaf["leaf"])
        if want != leaf["names"]:
            bad.append("leaf %d: %d lines of type, %s claims" % (leaf["leaf"], leaf["names"], want))
    if bad:
        print("\n".join("  " + b for b in bad), file=sys.stderr)
        return 1
    print("fergus 1839 first ward: the scan record and the claims file agree, %d names"
          % doc["measured"]["names_set_by_the_printer"])
    return 0


def main():
    if "--offline" in sys.argv:
        return offline()
    if "--build" in sys.argv:
        return build()
    if "--check" in sys.argv:
        return build(check=True)
    print(__doc__.strip().split("\n\n")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
