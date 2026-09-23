#!/usr/bin/env python3
"""Page boundaries for a committed book text that has none.

    tools/build_book_page_index.py --build   re-derive the index (needs pdftotext)
    tools/build_book_page_index.py --check   the gate (committed files only)
    tools/build_book_page_index.py --self-test

WHY THIS FILE EXISTS. `data/research/books/` commits the TEXT it quotes from, and
the gate in `tools/research_domains.py` rebuilds every quote out of that text by
line number. For Hubbard's autobiography the text this project was told to commit
is the Internet Archive's own OCR output,
`https://archive.org/download/autobiographyofg00hubb/autobiographyofg00hubb_djvu.txt`
— and that file carries NO page breaks at all. Zero form feeds, no folios of its
own, nothing that says where leaf 65 stops and leaf 66 starts.

That is a problem, because a book's locator is a PAGE. `coverage.json` already
records the shape of this fault once: Hurlbut's chapter is declared as one `list`
item and not as nine `page` items, because "declaring nine pages would mean
assigning each claim to a page nobody has seen, which is an invention, and the
gate would then be checking a fiction rather than a reading."

The deposited scan, `chicago/reference/swift-walker-autobiography/
autobiographyofg00hubb.pdf`, carries the SAME OCR in a text layer that DOES have
all 226 leaf breaks. So the page boundaries are not invented here — they are
transferred, mechanically, from the one artifact that holds them onto the one this
repo quotes from, and this file is that transfer written down so it can be redone
and disputed.

HOW. `pdftotext -layout` splits the deposit into 226 leaves. Both texts are
whitespace-normalised; a single `difflib.SequenceMatcher` pass over the two
normalised strings gives the correspondence (they agree to better than 0.9999,
their OCR being the same OCR); each leaf's normalised start is carried across and
mapped back to a raw offset, and thence to a 1-based line number in the committed
text. Where a leaf's opening words cannot be located the entry is written with
`aligned: false` and no claim may cite it.

WHAT IS DERIVED AND WHAT IS READ. The leaf number is mechanical. The PRINTED folio
is not: it is read off the foot of the leaf where the OCR gives it, and where the
OCR does not, it is carried by the constant offset that the read folios establish
— which is recorded per entry as `folio_source`: `read` or `offset`. Nothing here
authors a claim.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # chicago/4d
BOOKS = ROOT / "data" / "research" / "books"
REPO = ROOT.parent.parent                              # the custom repo root

BOOKS_INDEXED = {
    "hubbard_autobiography_1911": {
        "title": 'The Autobiography of Gurdon Saltonstall Hubbard, Pa-pa-ma-ta-be, '
                 '"The Swift Walker" (Chicago: Lakeside Press, 1911)',
        "archive_item": "autobiographyofg00hubb",
        "deposit_pdf": "chicago/reference/swift-walker-autobiography/autobiographyofg00hubb.pdf",
        "leaves": 226,
        # The two folio runs the book prints, each as (first_leaf, last_leaf,
        # first_folio). Roman for the front matter, arabic for the body. Both are
        # CHECKED against the folios the OCR actually gives, and a disagreement is
        # an error and not a silent correction.
        # THE SCAN IS OUT OF ORDER AND THIS IS WHERE THAT IS WRITTEN DOWN. Leaves 11
        # and 12 carry pages xv and xvi of the Introduction, and they were
        # photographed at the FRONT of the item, ahead of the title page. The text
        # proves it and the folios confirm it: leaf 26 ends "Quoting Mr. Gale's
        # characteristic manner of narration:", leaf 11 opens the Gale quotation,
        # leaf 12 ends "his engine was soon put to", and leaf 27 opens "use as
        # 'Fire King Engine No. I,'". Six folios READ off the page (xviii, xix, xxi,
        # xxiv, xxv at leaves 28-35) fix the run above the displacement, and the
        # Contents' own "Introduction ix" fixes the run below it. A single run
        # across leaves 21-37 would put two whole pages between xvi and xvii, which
        # is why this is three runs and not one.
        "folio_runs": [
            {"first_leaf": 11, "last_leaf": 12, "first_folio": 15, "numeral": "roman"},
            {"first_leaf": 21, "last_leaf": 26, "first_folio": 9, "numeral": "roman"},
            {"first_leaf": 27, "last_leaf": 37, "first_folio": 17, "numeral": "roman"},
            {"first_leaf": 39, "last_leaf": 220, "first_folio": 1, "numeral": "arabic"},
        ],
        # Reading order, where it is not leaf order. Stated so a coverage
        # declaration can say what it swept without the reader rediscovering it.
        "reading_order_note": "Leaves 11-12 (pages xv-xvi) belong between leaves 26 "
                              "and 27; everything else reads in leaf order.",
    },
    "fergus_26_29": {
        "title": "Fergus' Historical Series, Nos. 26-29, bound in one volume "
                 "(Chicago: Fergus Printing Company, 1883-1888)",
        "archive_item": "fergushistorical2629unse",
        # DERIVED A DIFFERENT WAY, AND THAT IS THE POINT OF THIS ENTRY. Hubbard's
        # boundaries had to be ALIGNED, because the text this project commits and
        # the artifact that knows where the leaves break are two different files.
        # Here they are one file's two halves: the deposit carries the Internet
        # Archive's hOCR search text AND the hOCR page index that was emitted with
        # it, and the index gives every leaf's exact character range in that very
        # text. Nothing is searched for, nothing is backed off, no leaf is
        # unaligned. `--build` checks the ranges tile the text end to end with no
        # gap and no overlap, and refuses to write an index if they do not.
        "derivation": "hocr_page_index",
        "deposit_text": "chicago/reference/fergus/fergushistorical2629unse_hocr_searchtext",
        "deposit_page_index": "chicago/reference/fergus/fergushistorical2629unse_hocr_pageindex.json",
        "leaves": 858,
        # NO `folio_runs`, ON PURPOSE. The volume binds four separately printed
        # pamphlets, each starting its own arabic run at 1, with plates, covers and
        # eight pages of Fergus Printing Company advertisements between them. A
        # constant offset would be an invention on every leaf it touched, and the
        # gate would then be checking the invention. So a folio here is READ off the
        # running head of the leaf or it is null, and `folio_source` is never
        # "offset" in this book.
        "folios": "read_only",
        "reading_order_note": "Leaf order throughout. The four numbers run 26 "
                              "(leaves 15-206), 27 (207-396), 28 (399-656) and 29 "
                              "(657-858); each restarts its own folio at 1, so a "
                              "printed page number is only unique within its number.",
    },
    # The third, added by T-0502 for H. H. Porter's Short Autobiography (1915). It
    # takes the Fergus route and not Hubbard's, for the same reason and one more.
    # The reason: the Internet Archive emitted this item's hOCR search text AND the
    # hOCR page index beside it, and the index gives every leaf's exact character
    # range in that very text, so nothing is aligned and nothing is searched for.
    # The one more: THE DEPOSIT PDF IS NOT IN THIS CHECKOUT. The 66 MB scan is
    # offloaded (chicago/reference/hh-porter-a-short-autobiography.yaml names a
    # local_archive_path outside the repository), so Hubbard's pdftotext transfer
    # cannot be run here at all, by anybody, ever. The two OCR artifacts are
    # derived text, they are small, and committing them beside the pointer is what
    # makes this index re-derivable by someone who does not hold the scan.
    "porter_hh_short_autobiography_1915": {
        "title": "H. H. Porter, A Short Autobiography, Written for His Children and "
                 "Grandchildren (Chicago: privately printed, 1915)",
        "archive_item": "chicago1835-hh-porter-autobiography",
        "derivation": "hocr_page_index",
        "deposit_text": "chicago/reference/hh-porter-a-short-autobiography/4582673_hocr_searchtext",
        "deposit_page_index": "chicago/reference/hh-porter-a-short-autobiography/4582673_hocr_pageindex.json",
        "leaves": 70,
        # NO `folio_runs`, and here the reason is smaller than Fergus's. The book
        # prints one arabic run over its narrative and nothing at all over its front
        # matter or its twenty-five leaves of plates; a run carried across the plates
        # would be inventing folios for pages that print none. A folio is READ off
        # the running head or it is null.
        "folios": "read_only",
        "reading_order_note": "Leaf order throughout. Leaves 1-10 are the covers, "
                              "the reference-use notice, the frontispiece, the two "
                              "title pages and the Introduction; leaves 11-45 are the "
                              "narrative, whose printed folios run 9 to 43; leaves "
                              "46-70 are the plates, their captions and the endpapers.",
    },
}

ROMAN = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
         (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]


def roman(n: int) -> str:
    out = []
    for value, sign in ROMAN:
        while n >= value:
            out.append(sign)
            n -= value
    return "".join(out)


def folio_for(spec: dict, leaf: int):
    for run in spec.get("folio_runs") or []:
        if run["first_leaf"] <= leaf <= run["last_leaf"]:
            n = run["first_folio"] + leaf - run["first_leaf"]
            return roman(n) if run["numeral"] == "roman" else str(n)
    return None


def normalise(s: str):
    """Collapse whitespace, keeping a map back to the raw offsets."""
    out, back = [], []
    prev_space = True
    for i, ch in enumerate(s):
        if ch.isspace():
            if prev_space:
                continue
            out.append(" ")
            back.append(i)
            prev_space = True
        else:
            out.append(ch)
            back.append(i)
            prev_space = False
    while out and out[-1] == " ":
        out.pop()
        back.pop()
    return "".join(out), back


def line_starts(text: str):
    starts = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            starts.append(i + 1)
    return starts


def line_of(starts, offset: int) -> int:
    lo, hi = 0, len(starts) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if starts[mid] <= offset:
            lo = mid
        else:
            hi = mid - 1
    return lo + 1                                       # 1-based


def read_folio(leaf_text: str):
    """The folio printed in a leaf's running head, or None.

    READ OR NOTHING. The head is set with the page number outside the title —
    "4 HARRISONS HISTORICAL DISCOURSE." on a verso, "CHICAGO DIRECTORY, 1843. 19"
    on a recto — so the folio is the first token or the last token of the leaf's
    running head, and only when the rest of that head still carries letters. The
    OCR frequently breaks the head across two lines and leaves the folio alone on
    the first, so a first line that is NOTHING BUT a one-to-three digit number is
    read as the folio when the next line carries the head; a bare number with no
    head under it is refused, because a plate caption, a table cell and a plate
    number all look like that. Four digits are refused everywhere, because this
    volume's heads print years ("CHICAGO DIRECTORY, 1843") and a year that passed
    for a folio would be a fiction the gate then checked. `I`, `l` and `O` are
    folded to `1`, `1` and `0` in a token that is otherwise digits — the same fold
    the folio check above applies for the same reason, this OCR reading 19 as "I9"
    about as often as not.
    """
    lines = [l.strip() for l in leaf_text.split("\n")]
    lines = [l for l in lines if l]
    if not lines:
        return None
    head = lines[0]
    if re.fullmatch(r"\d{1,3}", head):
        nxt = lines[1] if len(lines) > 1 else ""
        return head if re.search(r"[A-Za-z]{3}", nxt) else None
    if not re.search(r"[A-Za-z]{3}", head):
        return None
    m = re.match(r"^(\d{1,3})\s+(?=\S*[A-Za-z])", head)
    if m:
        return m.group(1)
    m = re.search(r"(?<=[A-Za-z.,;:'\u2019])[\s.,]+([0-9IlOo]{1,3})\s*[.,]?$", head)
    if m:
        folded = m.group(1).translate(str.maketrans("IlOo", "1100"))
        if any(ch.isdigit() for ch in m.group(1)) and folded.isdigit():
            return str(int(folded))
    return None


def build_one_hocr(key: str, spec: dict) -> dict:
    """Leaf boundaries taken straight from the deposit's own hOCR page index.

    No alignment: the index and the text were emitted by the same OCR pass over the
    same scan, so leaf i IS text[start:end]. What this function still has to prove
    is that the ranges tile the committed text end to end — one gap and a claim's
    line number would name the wrong leaf — and it refuses to write an index if
    they do not.
    """
    text_path = BOOKS / "text" / (key + ".txt")
    text = text_path.read_text(encoding="utf-8")
    deposit_text = REPO / spec["deposit_text"]
    deposit_index = REPO / spec["deposit_page_index"]
    for path in (deposit_text, deposit_index):
        if not path.exists():
            raise SystemExit("the deposit is not here: %s" % path)
    if deposit_text.read_bytes() != text_path.read_bytes():
        raise SystemExit("%s is not byte-identical to the deposit OCR it is copied from" % text_path)
    ranges = json.loads(deposit_index.read_text(encoding="utf-8"))
    if len(ranges) != spec["leaves"]:
        raise SystemExit("the page index holds %d leaves, not %d" % (len(ranges), spec["leaves"]))
    prev_end = 0
    for i, row in enumerate(ranges):
        start, end = int(row[0]), int(row[1])
        if start != prev_end:
            raise SystemExit("leaf %d starts at %d, leaf %d ended at %d — the ranges do "
                             "not tile the text" % (i + 1, start, i, prev_end))
        if end < start:
            raise SystemExit("leaf %d ends before it starts" % (i + 1))
        prev_end = end
    if prev_end != len(text):
        raise SystemExit("the ranges cover %d characters, the text has %d" % (prev_end, len(text)))

    starts = line_starts(text)
    entries = []
    for i, row in enumerate(ranges):
        char_start, char_end = int(row[0]), int(row[1])
        body = text[char_start:char_end]
        blank = not body.strip()
        entry = {
            "leaf": i + 1,
            "printed_page": None if blank else read_folio(body),
            "folio_source": None,
            "blank": blank,
            "aligned": not blank,
            "align_method": None if blank else "hocr_page_index",
            "char_start": char_start,
            "char_end": max(char_start, char_end - 1),
            "line_start": line_of(starts, char_start),
            "line_end": line_of(starts, max(char_start, char_end - 1)),
            "opens": " ".join(body.split()[:8]),
        }
        if entry["printed_page"] is not None:
            entry["folio_source"] = "read"
        entries.append(entry)
    read = sum(1 for e in entries if e["folio_source"] == "read")
    return {
        "schema": 1,
        "id": key,
        "title": spec["title"],
        "archive_item": spec["archive_item"],
        "generated_by": "tools/build_book_page_index.py --build",
        "_doc": "Leaf boundaries taken from the deposit's own hOCR page index, which "
                "indexes the very characters of the committed text — so these are not "
                "aligned boundaries but exact ones, and --build refuses to write this "
                "file unless the ranges tile the text with no gap and no overlap. "
                "`printed_page` is the folio READ off the leaf's running head and is "
                "null where the head prints none; `folio_source` is never \"offset\" in "
                "this book, because it binds four pamphlets that each restart at 1 and "
                "a carried offset would be an invention. `line_start`/`line_end` are "
                "inclusive 1-based line numbers into text/%s.txt, which is what a "
                "claim's locator cites." % key,
        "text_file": key + ".txt",
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_lines": len(starts),
        "deposit_text": spec["deposit_text"],
        "deposit_page_index": spec["deposit_page_index"],
        "deposit_sha256": hashlib.sha256(deposit_text.read_bytes()).hexdigest(),
        "reading_order_note": spec["reading_order_note"],
        "leaves": len(entries),
        "leaves_aligned": sum(1 for e in entries if e["aligned"]),
        "leaves_blank": sum(1 for e in entries if e["blank"]),
        "folios_read": read,
        "leaves_aligned_exactly": sum(1 for e in entries if e["aligned"]),
        "pages": entries,
    }


def build_one(key: str, spec: dict) -> dict:
    text_path = BOOKS / "text" / (key + ".txt")
    text = text_path.read_text(encoding="utf-8")
    pdf = REPO / spec["deposit_pdf"]
    if not pdf.exists():
        raise SystemExit("the deposit is not here: %s" % pdf)
    raw = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         check=True, capture_output=True).stdout.decode("utf-8", "replace")
    leaves = raw.split("\f")
    if leaves and not leaves[-1].strip():
        leaves.pop()
    if len(leaves) != spec["leaves"]:
        raise SystemExit("the deposit split into %d leaves, not %d" % (len(leaves), spec["leaves"]))

    ntext, back = normalise(text)
    nleaf_texts = [normalise(t)[0] for t in leaves]

    # A whole-document difflib pass over 285 000 characters does not finish, so the
    # alignment is done leaf by leaf and forwards only: each leaf's opening words are
    # searched for in the committed text from where the previous leaf ended. The two
    # OCRs are the same OCR, so the opening usually matches EXACTLY; where it does
    # not — poppler occasionally welds an italic word to its neighbour, which the
    # djvu text spaces — the probe is retried from the second word, the third and so
    # on, and the leaf's start is then backed off by the length of the words skipped.
    # Which of the two happened is recorded per leaf as `align_method`, because a
    # backed-off boundary is good to a few characters and an exact one is not.
    PROBE_WORDS = 9
    MAX_SKIP = 24
    positions, methods = [], []
    cursor = 0
    for t in nleaf_texts:
        if not t:
            positions.append(None)
            methods.append(None)
            continue
        words = t.split(" ")
        found, method = None, None
        for skip in range(0, MAX_SKIP + 1):
            probe = " ".join(words[skip:skip + PROBE_WORDS])
            if len(probe) < 12:
                break
            at = ntext.find(probe, cursor)
            if at < 0:
                continue
            prefix = " ".join(words[:skip])
            found = at - (len(prefix) + 1 if prefix else 0)
            if found < 0:
                found = at
            method = "exact" if skip == 0 else "skipped_%d_words" % skip
            break
        positions.append(found)
        methods.append(method)
        if found is not None:
            cursor = max(cursor, found + max(0, len(t) - 400))

    starts = line_starts(text)
    entries = []
    disagreements = []
    for i, t in enumerate(nleaf_texts):
        leaf = i + 1
        entry = {"leaf": leaf, "printed_page": None, "folio_source": None,
                 "blank": not t, "aligned": False, "char_start": None, "line_start": None,
                 "opens": ""}
        printed = folio_for(spec, leaf)
        if printed is not None:
            entry["printed_page"] = printed
            entry["folio_source"] = "offset"
            # Confirm against the folio the OCR prints at the foot of the leaf. A
            # folio that is well formed, the right LENGTH, and says something other
            # than the run says is a hard error and not a note: it is the fault that
            # hid the displaced leaves 11-12 behind a tidy constant offset until the
            # text itself gave them away.
            tail = [l.strip() for l in leaves[i].split("\n") if l.strip()]
            got = re.sub(r"[^0-9A-Za-z]", "", tail[-1]).lower() if tail else ""
            # The OCR reads an arabic folio's 1 as an i or an l about as often as
            # not — page 11 comes back "ii" and page 111 "iii" — so on an arabic
            # leaf those glyphs are folded before the comparison. Doing it the other
            # way round would let a roman folio pass as an arabic one, so it is not
            # done the other way round.
            if printed.isdigit():
                got = got.translate(str.maketrans("ilo", "110"))
            well_formed = bool(re.fullmatch(r"[ivxlcdm]+|[0-9]+", got))
            if got == printed.lower():
                entry["folio_source"] = "read"
            elif well_formed and len(got) == len(printed):
                disagreements.append("leaf %d: the page prints folio %r, the runs say %r"
                                     % (leaf, got, printed))
        if t:
            pos = positions[i]
            if pos is not None and pos < len(back):
                entry["aligned"] = True
                entry["align_method"] = methods[i]
                entry["char_start"] = back[pos]
                entry["line_start"] = line_of(starts, back[pos])
                entry["opens"] = " ".join(t.split()[:8])
        entries.append(entry)

    # A leaf ends where the next aligned leaf begins.
    for i, entry in enumerate(entries):
        nxt = None
        for j in range(i + 1, len(entries)):
            if entries[j]["aligned"]:
                nxt = entries[j]
                break
        if entry["aligned"]:
            entry["line_end"] = (nxt["line_start"] - 1) if nxt else len(starts)
            entry["char_end"] = (nxt["char_start"] - 1) if nxt else len(text)
            # A leaf that could not be aligned is swallowed by its predecessor's
            # range, and a claim citing those lines would name the wrong leaf. Say
            # so on the leaf that swallows it rather than leaving the range to look
            # clean: `runs_into` is the list of leaves whose text is inside this
            # entry's line span, and no claim may cite a leaf that has one.
            swallowed = [e["leaf"] for e in entries[i + 1:(nxt["leaf"] - 1) if nxt else len(entries)]
                         if not e["aligned"] and not e["blank"]]
            if swallowed:
                entry["runs_into"] = swallowed

    if disagreements:
        raise SystemExit("the folio runs contradict the page:\n  " + "\n  ".join(disagreements))
    read = sum(1 for e in entries if e["folio_source"] == "read")
    return {
        "schema": 1,
        "id": key,
        "title": spec["title"],
        "archive_item": spec["archive_item"],
        "generated_by": "tools/build_book_page_index.py --build",
        "_doc": "Leaf boundaries carried onto the committed text from the deposited "
                "scan's own text layer, because the committed text (the Internet "
                "Archive djvu OCR) has none. `leaf` is the scan's sheet number, 1-based "
                "and mechanical; `printed_page` is the folio the book itself prints, "
                "and `folio_source` says whether it was READ off the foot of that leaf "
                "or carried by the constant offset the read folios establish. "
                "`line_start`/`line_end` are inclusive 1-based line numbers into "
                "text/%s.txt, which is what a claim's locator cites." % key,
        "text_file": key + ".txt",
        "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "text_lines": len(starts),
        "deposit_pdf": spec["deposit_pdf"],
        "deposit_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "reading_order_note": spec["reading_order_note"],
        "leaves": len(entries),
        "leaves_aligned": sum(1 for e in entries if e["aligned"]),
        "leaves_blank": sum(1 for e in entries if e["blank"]),
        "folios_read": read,
        "leaves_aligned_exactly": sum(1 for e in entries if e.get("align_method") == "exact"),
        "pages": entries,
    }


def check(quiet: bool = False) -> int:
    bad = []
    for key, spec in BOOKS_INDEXED.items():
        path = BOOKS / "page_index" / (key + ".json")
        if not path.exists():
            bad.append("%s: no page index committed" % key)
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        text_path = BOOKS / "text" / doc.get("text_file", "")
        if not text_path.exists():
            bad.append("%s: names text_file %r, which is not committed" % (key, doc.get("text_file")))
            continue
        text = text_path.read_text(encoding="utf-8")
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if sha != doc.get("text_sha256"):
            bad.append("%s: the index was built against a different text (sha256 %s, "
                       "committed text is %s)" % (key, doc.get("text_sha256"), sha))
        n_lines = len(line_starts(text))
        if n_lines != doc.get("text_lines"):
            bad.append("%s: the index counts %s lines, the text has %d"
                       % (key, doc.get("text_lines"), n_lines))
        pages = doc.get("pages") or []
        if len(pages) != spec["leaves"]:
            bad.append("%s: %d leaves indexed, the scan has %d" % (key, len(pages), spec["leaves"]))
        prev_line, prev_leaf = 0, 0
        for entry in pages:
            leaf = entry.get("leaf")
            if leaf != prev_leaf + 1:
                bad.append("%s: leaf numbers are not consecutive at %r" % (key, leaf))
            prev_leaf = leaf
            if spec.get("folios") == "read_only":
                # No folio runs to check against, so the assertion is the one that
                # matters here instead: a folio in this book is READ or it is null,
                # and a carried one would be the invention the spec refuses.
                if entry.get("printed_page") is not None and entry.get("folio_source") != "read":
                    bad.append("%s leaf %s: printed_page %r with folio_source %r — this "
                               "book carries no folio it did not read"
                               % (key, leaf, entry.get("printed_page"), entry.get("folio_source")))
                if entry.get("printed_page") is None and entry.get("folio_source") is not None:
                    bad.append("%s leaf %s: folio_source %r on a leaf with no printed_page"
                               % (key, leaf, entry.get("folio_source")))
            else:
                expected = folio_for(spec, leaf)
                if entry.get("printed_page") != expected:
                    bad.append("%s leaf %s: printed_page %r, the folio runs say %r"
                               % (key, leaf, entry.get("printed_page"), expected))
            if not entry.get("aligned"):
                continue
            if entry.get("line_start", 0) < prev_line:
                bad.append("%s leaf %s: line_start %r runs backwards from leaf %s"
                           % (key, leaf, entry.get("line_start"), leaf - 1))
            prev_line = entry.get("line_start", 0)
            if entry.get("line_end") is not None and entry["line_end"] < entry["line_start"]:
                bad.append("%s leaf %s: ends before it starts" % (key, leaf))
            if entry["line_start"] > n_lines:
                bad.append("%s leaf %s: line_start %d is past the end of the text"
                           % (key, leaf, entry["line_start"]))
        aligned = sum(1 for e in pages if e.get("aligned"))
        if aligned != doc.get("leaves_aligned"):
            bad.append("%s: the header counts %s aligned leaves, the entries show %d"
                       % (key, doc.get("leaves_aligned"), aligned))
        if not quiet:
            print("  %s — %d leaves, %d aligned, %d folios read off the page"
                  % (key, len(pages), aligned, sum(1 for e in pages if e.get("folio_source") == "read")))
    if bad:
        for line in bad:
            print("  FAIL %s" % line)
        return 1
    if not quiet:
        print("  page index: OK")
    return 0


def self_test() -> int:
    """The gate's own assertions still fire when the index is broken.

    Both derivations are exercised, because they are checked by different branches:
    the aligned book is held to its folio RUNS, and the hOCR-indexed book is held to
    the rule that it carries no folio it did not read.
    """
    cases = [
        ("hubbard_autobiography_1911", "a text that is not the one indexed",
         lambda d: d.update(text_sha256="0" * 64), "built against a different text"),
        ("hubbard_autobiography_1911", "a leaf whose folio contradicts the printed run",
         lambda d: d["pages"][100].update(printed_page="999"), "the folio runs say"),
        ("hubbard_autobiography_1911", "line numbers that run backwards",
         lambda d: d["pages"][100].update(line_start=1), "runs backwards"),
        ("fergus_26_29", "a folio carried onto a leaf that never printed one",
         lambda d: _first_folio_leaf(d).update(folio_source="offset"),
         "no folio it did not read"),
        ("fergus_26_29", "a folio source on a leaf with no folio",
         lambda d: _first_folioless_leaf(d).update(folio_source="read"),
         "on a leaf with no printed_page"),
    ]
    failures = 0
    originals = {key: (BOOKS / "page_index" / (key + ".json")).read_text(encoding="utf-8")
                 for key in {c[0] for c in cases}}
    try:
        for key, label, break_it, wanted in cases:
            path = BOOKS / "page_index" / (key + ".json")
            broken = json.loads(originals[key])
            break_it(broken)
            path.write_text(json.dumps(broken, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            import io
            import contextlib
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = check(quiet=True)
            path.write_text(originals[key], encoding="utf-8")
            if rc == 0 or wanted not in buf.getvalue():
                print("  FAIL the gate does not catch %s" % label)
                failures += 1
            else:
                print("  caught: %s" % label)
    finally:
        for key, original in originals.items():
            (BOOKS / "page_index" / (key + ".json")).write_text(original, encoding="utf-8")
    if failures:
        return 1
    print("  self-test: OK")
    return 0


def _first_folio_leaf(doc: dict) -> dict:
    for entry in doc["pages"]:
        if entry.get("printed_page") is not None:
            return entry
    raise SystemExit("the self-test needs a leaf with a folio and the index has none")


def _first_folioless_leaf(doc: dict) -> dict:
    for entry in doc["pages"]:
        if entry.get("printed_page") is None and entry.get("aligned"):
            return entry
    raise SystemExit("the self-test needs a leaf with no folio and the index has none")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.build:
        for key, spec in BOOKS_INDEXED.items():
            doc = (build_one_hocr(key, spec) if spec.get("derivation") == "hocr_page_index"
                   else build_one(key, spec))
            out = BOOKS / "page_index" / (key + ".json")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            print("  %s — %d leaves, %d aligned (%d exactly), %d folios read"
                  % (key, doc["leaves"], doc["leaves_aligned"],
                     doc["leaves_aligned_exactly"], doc["folios_read"]))
        return 0
    if args.self_test:
        return self_test()
    return check()


if __name__ == "__main__":
    sys.exit(main())
