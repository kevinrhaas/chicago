#!/usr/bin/env python3
"""No committed file carries a git conflict marker.

WHY THIS EXISTS. On 2026-08-24 `docs/LIBERTIES.md` reached **production** with
three literal conflict-marker lines in it, and every gate in this repository
passed it. A visitor opening L180 or L181 in the Evidence panel was shown

    Recorded: 2026-08-23. <<<<<<< HEAD
    Recorded: 2026-08-24. ======= >>>>>>> origin/dev

because the markers rode the compile into `data/liberties.json` and out to the
published mirror.

Nothing caught it, and the reason is worth stating plainly: the liberties gate
compares the markdown against the compiled JSON, and `compile_liberties.py`
recognises `### L<n> — title` headings and `**Label:** text` fields. A marker
line is neither, so it was carried along as body text on the entry above it. The
markdown and the JSON agreed *perfectly* — both contained the same garbage — and
a gate that asks "do these two derivations match?" cannot see a fault that is
faithfully reproduced by both.

Two other things had to be true, and both were:

  * `git add -A` stages a file that still contains markers without complaint,
    and `git diff --diff-filter=U` then reports nothing unresolved. The index
    calls it resolved because you told it to.
  * The merge that did it conflicted on a hunk whose *other* side was empty — a
    positional conflict over an entry both branches already had — so there was
    no visible disagreement to prompt a careful read.

So the check is a TEXT scan, deliberately dumb, over what is actually committed.
It asks nothing about structure, because structure is what missed it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # chicago/4d
REPO = ROOT.parent.parent                              # repo root
SCAN = ("chicago/4d", "site/chicago/4d")

# Built rather than written, so this file does not trip its own scan.
OPEN = "<" * 7 + " "
MID = "=" * 7
CLOSE = ">" * 7 + " "


def is_marker(line: str) -> bool:
    """A conflict marker at the start of a line.

    `=======` is only a marker when it is the WHOLE line: a row of equals signs
    is also how markdown underlines a heading and how this project rules off a
    table, and refusing those would make the gate a nuisance rather than a
    guard. The open and close forms carry a trailing space and a label, so they
    are unambiguous.

    Trailing whitespace is stripped before the comparison — git does not emit
    any, but an editor that has been through the file may leave some, and a
    marker with a space after it is still a marker. Leading whitespace is NOT
    stripped, so an indented rule stays legal.
    """
    return line.startswith(OPEN) or line.startswith(CLOSE) or line.rstrip() == MID


def tracked_text_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z", *SCAN],
                         cwd=REPO, capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f]


def scan() -> list[tuple[str, int, str]]:
    hits = []
    for rel in tracked_text_files():
        p = REPO / rel
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue                                   # binary, or a broken link
        if len(text) > 40_000_000:
            continue
        for n, line in enumerate(text.split("\n"), 1):
            if is_marker(line):
                hits.append((rel, n, line[:90]))
    return hits


def self_test() -> bool:
    """Every assertion fires when broken."""
    ok = True

    def check(label, got, want=True):
        nonlocal ok
        if got != want:
            ok = False
        print(f"  {'ok  ' if got == want else 'FAIL'}  {label}")

    check("an opening marker is caught", is_marker(OPEN + "HEAD"))
    check("a closing marker is caught", is_marker(CLOSE + "origin/dev"))
    check("a bare divider is caught", is_marker(MID))
    check("a divider with trailing whitespace is still caught", is_marker(MID + "  "))
    # The three the scan must NOT refuse, or it becomes a nuisance:
    check("a markdown heading underline is NOT a marker", is_marker(MID + "=="), want=False)
    check("a table rule is NOT a marker", is_marker("|" + MID + "|"), want=False)
    check("an indented divider is NOT a marker", is_marker("  " + MID), want=False)
    check("prose mentioning a marker mid-line is NOT caught",
          is_marker("the line " + OPEN + "HEAD appears"), want=False)
    check("this file does not trip its own scan",
          not any(is_marker(l) for l in Path(__file__).read_text(encoding="utf-8").split("\n")))
    return ok


def main() -> int:
    if "--self-test" in sys.argv:
        print("\n\033[1m== …and its own assertions still fire when broken\033[0m")
        good = self_test()
        print("\nSELF-TEST " + ("PASS" if good else "FAIL"))
        return 0 if good else 1

    files = tracked_text_files()
    hits = scan()
    if not hits:
        print(f"  ok    no conflict marker in any of {len(files)} tracked file(s) "
              f"under {' and '.join(SCAN)}")
        return 0

    print(f"  FAIL  {len(hits)} conflict marker(s) survive in committed files:")
    for rel, n, line in hits[:40]:
        print(f"          {rel}:{n}: {line}")
    if len(hits) > 40:
        print(f"          … and {len(hits) - 40} more")
    print("\n        A merge was committed unresolved. `git add -A` stages a file")
    print("        with markers in it and reports nothing unresolved, so this is")
    print("        the only thing that will tell you. Resolve the hunk properly,")
    print("        re-run any compile the file feeds, and commit again.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
