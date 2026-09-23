#!/usr/bin/env python3
"""Look the Newberry lead surnames up in a volume of Moses and Kirkland — T-0581, T-0826.

WHY THIS EXISTS AS A COMMITTED SCRIPT. T-0581 built
`data/research/books/moses_kirkland_v1_lead_surnames.json` with "a script run by
hand" that was never committed, so its mechanics survived only as the prose of that
file's `generated_by`. T-0826 has to run the SAME search over volume 2 or the two
files cannot be read together, and a paraphrase of a search is not a search. So the
mechanics are written here once, and `--self-test` proves they are the right ones by
re-deriving every mechanical field of the committed volume 1 file and refusing to
differ from it: 49 surnames x 4 fields, all 196 equal, or the script exits non-zero.

Reproducing that file took three attempts and the two corrections are the whole
subtlety of the search, so they are recorded here rather than rediscovered:

  APOSTROPHE-TOLERANT MEANS BOTH DIRECTIONS. The volume prints both `O'Brien` and
  `Hall's`, and one normalisation cannot reach both: stripping apostrophes is what
  lets `obrien` (the index card's spelling) find `O'Brien`, and it is also what
  turns `Hall's` into `Halls` and hides it from \bhall\b. So every line is matched
  TWICE, raw and stripped, and a hit in either counts. Matching stripped-only
  silently loses 31 lines across the forty-nine surnames, six of them inside the
  pre-1836 window.

  `occurrences` COUNTS LINES, NOT MATCHES. A line naming a man twice is one
  occurrence in the committed file. Counting matches instead overstates six
  surnames by one or two each.

The verdicts are NOT produced here. This script writes the mechanical half — the
counts, the line lists, the pre-1836 window and the edit-distance-1 neighbours of a
zero result — and a reading pass authors `verdict` on top of it. That division is
T-0581's, and `mechanical_verdict` beside an authored `verdict` is how the file
keeps both.

usage:
  search_book_lead_surnames.py --self-test
  search_book_lead_surnames.py --text <path> --out <path.json>
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V1_LOOKUP = ROOT / 'data/research/books/moses_kirkland_v1_lead_surnames.json'
V1_TEXT = ROOT / 'data/research/books/text/moses_kirkland_history_of_chicago_v1.txt'

# The pre-1836 window: any line within eight lines of a line printing a year in
# this range. T-0581's `window_note` is explicit that this is a filter and not a
# judgement — it decides what a reading pass reads, nothing more.
YEAR_LO, YEAR_HI, WINDOW = 1820, 1835, 8
LIST_CAP = 8  # first_lines and pre_1836_lines are the first eight, as in v1

APOSTROPHES = re.compile(r"[’'`]")


def lead_surnames():
    """The forty-nine surnames T-0570 flagged against this work, in v1's order."""
    doc = json.loads(V1_LOOKUP.read_text())
    return [row['surname'] for row in doc['surnames']]


def read_lines(path):
    return Path(path).read_text(encoding='utf-8', errors='replace').split('\n')


def pre_1836_window(lines):
    anchored = set()
    for i, line in enumerate(lines, 1):
        for m in re.finditer(r'\b(\d{4})\b', line):
            if YEAR_LO <= int(m.group(1)) <= YEAR_HI:
                anchored.add(i)
                break
    window = set()
    for i in anchored:
        window.update(range(i - WINDOW, i + WINDOW + 1))
    return window


def search(lines, names):
    stripped = [APOSTROPHES.sub('', l) for l in lines]
    window = pre_1836_window(lines)
    rows = []
    for name in names:
        rx = re.compile(r'\b' + re.escape(name) + r'\b', re.I)
        hits = [i for i, (raw, bare) in enumerate(zip(lines, stripped), 1)
                if rx.search(raw) or rx.search(bare)]
        pre = [i for i in hits if i in window]
        rows.append({
            'surname': name,
            'occurrences': len(hits),
            'in_pre_1836_context': len(pre),
            'first_lines': hits[:LIST_CAP],
            'pre_1836_lines': pre[:LIST_CAP],
        })
    return rows


def vocabulary(lines):
    vocab = set()
    for line in lines:
        for w in re.findall(r"[A-Za-z’']+", line):
            vocab.add(APOSTROPHES.sub('', w).lower())
    vocab.discard('')
    return vocab


def edit_distance_1(word, vocab):
    """Every vocabulary word one substitution, insertion or deletion from `word`.

    A zero result is not an absence until this has run: both sides of the search
    are OCR, and a volume printing `Clvbourn` for Clybourn is not silent about the
    man. T-0581's `zero_result_note` is the rule this discharges.
    """
    letters = 'abcdefghijklmnopqrstuvwxyz'
    near = set()
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    for a, b in splits:
        if b:
            near.add(a + b[1:])
            for c in letters:
                near.add(a + c + b[1:])
        for c in letters:
            near.add(a + c + b)
    near.discard(word)
    return sorted(near & vocab)


def self_test():
    committed = {r['surname']: r for r in json.loads(V1_LOOKUP.read_text())['surnames']}
    names = list(committed)
    derived = search(read_lines(V1_TEXT), names)
    fields = ('occurrences', 'in_pre_1836_context', 'first_lines', 'pre_1836_lines')
    bad = 0
    for row in derived:
        want = committed[row['surname']]
        for f in fields:
            if row[f] != want[f]:
                bad += 1
                print(f"FAIL {row['surname']}.{f}: derived {row[f]} != committed {want[f]}")
    total = len(derived) * len(fields)
    if bad:
        print(f"self-test: {bad} of {total} mechanical fields differ from volume 1")
        return 1
    print(f"self-test ok: all {total} mechanical fields of volume 1 re-derived "
          f"({len(derived)} surnames x {len(fields)})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--text')
    ap.add_argument('--out')
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not (args.text and args.out):
        ap.error('--text and --out are both required')
    lines = read_lines(args.text)
    names = lead_surnames()
    rows = search(lines, names)
    vocab = vocabulary(lines)
    for row in rows:
        if row['occurrences'] == 0:
            row['edit_distance_1_in_the_volume'] = edit_distance_1(row['surname'], vocab)
    Path(args.out).write_text(json.dumps({
        'text_lines': len(lines),
        'surnames': rows,
    }, indent=1) + '\n')
    print(f"{args.out}: {len(rows)} surnames over {len(lines)} lines")
    return 0


if __name__ == '__main__':
    sys.exit(main())
