#!/usr/bin/env python3
"""T-3266: read the Chicago Blue Book's Prairie Avenue 1600-2140 entries, 1890-1910.

Each edition is read TWICE, from two lists the book prints independently:

  street  the street-and-number list ("1808 Mr. & Mrs. O. R. Keith"), read from the
          PRAIRIE AVENUE pages only (the run of page headers that name the street);
  alpha   the alphabetical list of names ("Keith O. R. 1808 Prairie av."), every line
          that gives a Prairie Avenue number in the range.

Both come from the Internet Archive's OCR text of each scan (`<item>_djvu.txt`). The OCR
is not the page: a number can be misread, two columns can run together, and a line can
be lost. `tools/build_former_residents_1904.py` therefore keeps a household only where
two readings agree (see its WITNESS rule); this file keeps every candidate, so the
filter is in one place and can be re-argued.

Writes blue_book_prairie_readings.tsv beside itself. Usage:

    python3 read_blue_books.py [--cache DIR]

The 1896 and 1900 editions are not on the Internet Archive, and the 1906 item's text
returned a server error on 2026-10-30; those three are absent, not empty.
"""
import argparse
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
EDITIONS = [1890, 1891, 1892, 1893, 1894, 1895, 1897, 1898, 1899, 1901, 1902, 1903,
            1904, 1905, 1907, 1908, 1909, 1910]
LO, HI = 1600, 2140
NUM = re.compile(r'(?<!\d)(1[6-9]\d\d|20\d\d|21[0-4]\d)\s+(?=[A-Z])')
ALPHA = re.compile(r"^([A-Z][A-Za-z'\-]+\.? [^0-9]{1,60}?)[,.]? (1[6-9]\d\d|20\d\d|21[0-4]\d) Prairie av")


def item(year: int) -> str:
    return f"chicagobluebooko{year}chic"


def text_of(year: int, cache: Path) -> list[str]:
    path = cache / f"{item(year)}_djvu.txt"
    if not path.exists() or path.stat().st_size < 500_000:
        url = f"https://archive.org/download/{item(year)}/{item(year)}_djvu.txt"
        with urllib.request.urlopen(url, timeout=120) as r:
            path.write_bytes(r.read())
    raw = path.read_text(encoding="utf-8", errors="replace")
    return [re.sub(r" +", " ", l).strip() for l in raw.split("\n")]


def street_rows(lines: list[str]):
    """The PRAIRIE AVENUE pages: the first run of page headers naming the street (past
    the book's front index), from 200 lines before the first to 300 after the last."""
    heads = [i for i, l in enumerate(lines) if i > 3000 and "PRAIRIE AVENUE" in l and len(l) < 60]
    first = last = heads[0]
    for h in heads[1:]:
        if h - last >= 400:
            break
        last = h
    entries = []
    for l in lines[first - 200:last + 300]:
        if not l:
            continue
        starts = [m.start() for m in NUM.finditer(l)]
        if starts and starts[0] == 0:
            for a, b in zip(starts, starts[1:] + [len(l)]):
                m = re.match(r"(\d{4})\s+(.*)", l[a:b].strip())
                entries.append([int(m.group(1)), m.group(2).strip()])
        elif (entries and not l.startswith("Receiv") and "AVENUE" not in l and len(l) < 30
              and (l[0].islower() or l[0] == "&" or l.startswith(("jr", "dr")))):
            entries[-1][1] += " " + l       # a wrapped "& dr." or "jr."
    for n, t in entries:
        t = re.sub(r"\s*Receiv.*$", "", t).strip()
        if LO <= n <= HI and t:
            yield n, t


def alpha_rows(lines: list[str]):
    for l in lines:
        m = ALPHA.match(l)
        if m:
            yield int(m.group(2)), m.group(1).strip(" ,")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/blue-book-ocr")
    a = ap.parse_args()
    cache = Path(a.cache)
    cache.mkdir(parents=True, exist_ok=True)
    out = ["# edition\tnumber\tlist\tprinted (OCR, spaces collapsed)"]
    for y in EDITIONS:
        lines = text_of(y, cache)
        seen = set()
        for kind, rows in (("street", street_rows(lines)), ("alpha", alpha_rows(lines))):
            for n, t in rows:
                if (n, kind, t) in seen:
                    continue
                seen.add((n, kind, t))
                out.append(f"{y}\t{n}\t{kind}\t{t}")
        print(y, sum(1 for k in seen), file=sys.stderr)
    (HERE / "blue_book_prairie_readings.tsv").write_text("\n".join(out) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
