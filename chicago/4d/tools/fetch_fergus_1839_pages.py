#!/usr/bin/env python3
"""Commit page text for *Fergus' Directory of the City of Chicago, 1839* (T-0664).

`read_fergus_1839.py` reads COMMITTED page text under
`data/research/directories/text/fergus_1839_leaf_*.txt`. Until now the derivation
of that text from the scan lived only as a sentence in that file's `CORPUS["how"]`,
so the one step nobody could re-run was the first one. This tool is that sentence
as code.

THE RULE, and it is the sentence, verbatim: the word coordinates of archive.org's
OCR (`fergusdirectoryo00ferg_djvu.xml`) give each line its left edge; a line set
more than 25 px right of the MEDIAN line start of its own page — the page is
2238 px wide and the turn measures about 50 px — is a turned line and is committed
with two leading spaces. Nothing else about the text is touched.

ONE CLAUSE THE SENTENCE LEFT OUT, and it is why this tool exists rather than a
re-derivation from memory: the RUNNING HEAD at the top of a page is centred, so it
sits far right of the median and would be committed as if it were turned. The
committed text does not indent it. The leading run of header-like lines — short,
and either shouting or scanner speck — is emitted flush, and the turn rule starts
at the first line that is neither. That clause reproduces all 33 leaves T-0506
committed, byte for byte, which is what `--check` asserts.

  tools/fetch_fergus_1839_pages.py --check              every committed leaf, network
  tools/fetch_fergus_1839_pages.py --write 50 62        commit leaves 50-62

NETWORK. This tool fetches the scan's OCR from archive.org and is therefore NOT in
`check.sh`, which runs offline in seconds. `read_fergus_1839.py --check` is the
gate; this is the step before it.
"""
import os, re, statistics, sys, urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = os.path.join(ROOT, "data/research/directories/text")
ITEM = "fergusdirectoryo00ferg"
URL = "https://archive.org/download/%s/%s_djvu.xml" % (ITEM, ITEM)
TURN_PX = 25


def header_like(line: str) -> bool:
    """A running head: short, and either shouting or mostly scanner noise.

    The same test `read_fergus_1839.py` uses on the body, kept identical on
    purpose — one definition of a running head for this volume, not two."""
    s = line.strip()
    if not s or len(s) > 45:
        return False
    if len(s) <= 3:
        return True
    letters = [c for c in s if c.isalpha()]
    return not letters or sum(c.isupper() for c in letters) / len(letters) > 0.7


def fetch(path=None) -> bytes:
    if path:
        return open(path, "rb").read()
    with urllib.request.urlopen(URL, timeout=180) as fh:
        return fh.read()


def pages(xml: bytes):
    return ET.fromstring(xml).findall(".//OBJECT")


def lines(page):
    """(left edge, text) for every line the OCR sets on this page."""
    out = []
    for line in page.iter("LINE"):
        words = line.findall("WORD")
        if not words:
            continue
        left = int(words[0].get("coords").split(",")[0])
        out.append((left, " ".join((w.text or "") for w in words)))
    return out


def render(page) -> str:
    ls = lines(page)
    if not ls:
        return ""
    median = statistics.median([left for left, _ in ls])
    out, head = [], True
    for left, text in ls:
        if head and header_like(text):
            out.append(text)
            continue
        head = False
        out.append(("  " if left - median > TURN_PX else "") + text)
    return "\n".join(out) + "\n"


def leaf_path(leaf: int) -> str:
    return os.path.join(TEXT, "fergus_1839_leaf_%03d.txt" % leaf)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    local = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--from=")), None)
    pgs = pages(fetch(local))
    if "--write" in sys.argv:
        first, last = int(args[0]), int(args[1])
        for leaf in range(first, last + 1):
            with open(leaf_path(leaf), "w", encoding="utf-8") as fh:
                fh.write(render(pgs[leaf - 1]))
            print("  wrote leaf %03d (printed %d)" % (leaf, leaf - 12))
        return 0
    bad = []
    checked = 0
    for name in sorted(os.listdir(TEXT)):
        m = re.fullmatch(r"fergus_1839_leaf_(\d{3})\.txt", name)
        if not m:
            continue
        leaf = int(m.group(1))
        checked += 1
        if open(leaf_path(leaf), encoding="utf-8").read() != render(pgs[leaf - 1]):
            bad.append(leaf)
    if bad:
        print("fergus 1839 text: %d leaf/leaves no longer re-derive from the scan: %s"
              % (len(bad), ", ".join("%03d" % b for b in bad)), file=sys.stderr)
        return 1
    print("fergus 1839 text: all %d committed leaves re-derive from %s" % (checked, ITEM))
    return 0


if __name__ == "__main__":
    sys.exit(main())
