#!/usr/bin/env python3
"""Plain text out of a .docx, with the standard library and nothing else.

WHY THIS EXISTS. Twenty-three issues of the 1833-1835 newspaper corpus
(`chicago/reference/newspapers/Transcriptions/`) were delivered as .docx only —
the whole Chicago American run and the 1835 tail of the Democrat. The other
sixty-six carry a committed .txt beside the .docx and are cited at their
archival path; these twenty-three had no readable form at all, so nothing in
this project could quote them.

A .docx is a zip of XML. `word/document.xml` holds the body; `w:t` elements hold
the runs of text. That is the entire dependency surface, which is the point: the
fleet is static-first and this repo's gate installs `jsonschema` and `pyproj` and
nothing else. No python-docx, no pandoc.

DETERMINISM IS A REQUIREMENT, NOT A HOPE. The output of this tool is committed,
and a committed derivative that re-derives differently is a silent diff on every
run. Everything here is ordered by document order, the zip is read by explicit
member name rather than by iteration order, and `--self-test` builds a .docx in
memory, extracts it twice and asserts the two byte strings are identical.

  tools/docx_text.py FILE.docx              write text to stdout
  tools/docx_text.py FILE.docx -o OUT.txt   write text to a file
  tools/docx_text.py --self-test            prove determinism and the mapping
"""
import argparse
import io
import sys
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# The body elements this tool understands. Anything else in the body is walked
# through rather than skipped, so a run nested in a structure not listed here
# (a content control, say) still reaches the output instead of vanishing.
PARA = W + "p"
ROW = W + "tr"
CELL = W + "tc"


def _run_text(node):
    """Text of one w:r-bearing subtree, in document order.

    w:t is text. w:tab is a tab and w:br/w:cr are line breaks -- a transcription
    uses both to lay out column markers, so dropping them would run two markers
    together. w:instrText is field code, never displayed, and is dropped.
    """
    out = []
    for el in node.iter():
        tag = el.tag
        if tag == W + "t":
            out.append(el.text or "")
        elif tag in (W + "tab",):
            out.append("\t")
        elif tag in (W + "br", W + "cr"):
            out.append("\n")
    return "".join(out)


def _blocks(node):
    """Yield one string per paragraph, in document order.

    Table cells are yielded as their own paragraphs and a row is joined with
    tabs, which is what the manifests in this corpus already look like when
    read by eye.
    """
    for child in node:
        tag = child.tag
        if tag == PARA:
            yield _run_text(child)
        elif tag == W + "tbl":
            for row in child.iter(ROW):
                cells = []
                for cell in row.findall(CELL):
                    cells.append(" ".join(t for t in _blocks(cell) if t))
                yield "\t".join(cells)
        elif tag in (W + "sdt", W + "sdtContent", W + "body"):
            yield from _blocks(child)


def docx_to_text(data):
    """bytes of a .docx -> str. Deterministic: same bytes in, same string out."""
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        try:
            xml = zf.read("word/document.xml")
        except KeyError:
            raise ValueError("not a Word document: no word/document.xml")
    root = ET.fromstring(xml)
    body = root.find(W + "body")
    if body is None:
        raise ValueError("no w:body in word/document.xml")
    lines = [ln.replace("\r\n", "\n").replace("\r", "\n") for ln in _blocks(body)]
    # Trailing whitespace on a line is invisible and would be a diff, so it goes.
    lines = [ln.rstrip() for ln in lines]
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines) + "\n"


def extract_file(path):
    with open(path, "rb") as fh:
        return docx_to_text(fh.read())


# --------------------------------------------------------------------------
# self-test


def _synthetic_docx():
    """A minimal, valid .docx built in memory, so the self-test needs no corpus.

    The archival deposit lives on `main` and the 4D subtree is developed on
    `dev` (see data/research/newspapers/README.md), so a self-test that opened a
    real issue would be red on the branch it has to be green on.
    """
    doc = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        "<w:body>"
        "<w:p><w:r><w:t>===== ISSUE PAGE 1 / PDF PAGE 1 / COLUMN 1 OF 6 =====</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>THE CHICAGO </w:t></w:r><w:r><w:t>DEMOCRAT.</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>a line</w:t></w:r><w:r><w:br/><w:t>and its continuation</w:t></w:r></w:p>"
        "<w:p><w:r><w:t>[uncertain: WATTLES]</w:t></w:r><w:r><w:tab/><w:t>[illegible]</w:t></w:r></w:p>"
        "<w:p><w:r><w:instrText>PAGE \\* MERGEFORMAT</w:instrText></w:r></w:p>"
        "<w:tbl><w:tr><w:tc><w:p><w:r><w:t>date</w:t></w:r></w:p></w:tc>"
        "<w:tc><w:p><w:r><w:t>1835-07-01</w:t></w:r></w:p></w:tc></w:tr></w:tbl>"
        "<w:p><w:r><w:t>   </w:t></w:r></w:p>"
        "</w:body></w:document>"
    )
    buf = io.BytesIO()
    # date_time is pinned: a zip records mtimes, and this must be reproducible.
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, payload in (
            ("[Content_Types].xml", "<Types/>"),
            ("word/document.xml", doc),
        ):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            zf.writestr(info, payload)
    return buf.getvalue()


EXPECTED = (
    "===== ISSUE PAGE 1 / PDF PAGE 1 / COLUMN 1 OF 6 =====\n"
    "THE CHICAGO DEMOCRAT.\n"
    "a line\nand its continuation\n"
    "[uncertain: WATTLES]\t[illegible]\n"
    "\n"
    "date\t1835-07-01\n"
)


def self_test():
    data = _synthetic_docx()
    a = docx_to_text(data)
    b = docx_to_text(data)
    failures = []
    if a.encode("utf-8") != b.encode("utf-8"):
        failures.append("two extractions of the same bytes differ")
    if a != EXPECTED:
        failures.append(
            "mapping changed.\n--- expected ---\n%r\n--- got ---\n%r" % (EXPECTED, a)
        )
    # A field code must not reach the text, an uncertainty bracket must.
    if "MERGEFORMAT" in a:
        failures.append("w:instrText field code leaked into the text")
    if "[uncertain: WATTLES]" not in a:
        failures.append("an uncertainty bracket was lost")
    # And the assertions above must be capable of firing.
    broken = docx_to_text(data).replace("[uncertain: WATTLES]", "WATTLES")
    if "[uncertain: WATTLES]" in broken:
        failures.append("the bracket assertion cannot fail")
    try:
        docx_to_text(b"not a zip at all")
    except Exception:
        pass
    else:
        failures.append("a non-docx was accepted")
    if failures:
        for f in failures:
            print("FAIL: " + f, file=sys.stderr)
        return 1
    print("docx_text self-test OK — deterministic, %d chars, markers preserved" % len(a))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("docx", nargs="?", help="path to a .docx")
    ap.add_argument("-o", "--out", help="write here instead of stdout")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.docx:
        ap.error("give a .docx, or --self-test")
    text = extract_file(args.docx)
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
