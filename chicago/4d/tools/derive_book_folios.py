#!/usr/bin/env python3
"""Read the printed folios off a Moses and Kirkland volume's OCR — T-0826.

THE FOLIO RULE IS RE-DERIVED HERE AND NOT ASSUMED. T-0581 established that volume 1
prints its own page numbers into the OCR and that the number is READ off the nearest
preceding running head rather than counted, with verso heads even and recto heads
odd as the check. T-0826's acceptance requires that rule re-derived for volume 2
rather than carried over, because a second volume of the same work need not be set
the same way. This script is that derivation, and it reports the evidence:

  --audit   the whole folio sequence, its parity, and every numeral the parity
            check refuses
  --at N    the printed page a given line of the committed text stands on

WHAT THE DERIVATION FOUND FOR VOLUME 2 (1895, the same UIUC copy, scanned in the
same batch): THE RULE HOLDS, and on BOTH SIDES OF THE LEAF. A head is a line of
small caps — 'HISTORY OF CHICAGO.' on a verso, the chapter's own title on a recto —
with the folio alone on a line within six lines of it, above the verso head and
below the recto one. 299 verso heads survive, 269 with their numeral, 256 of those
even; 336 recto heads survive, every one with its numeral, 320 of them odd. The
parity check refuses the wrong-parity numerals on either side and the run corrects
eleven of them — the head above line 5881 reads '43' between 40, 41 and 43, 44 —
which is the same fault, caught the same way, as the '93' volume 1's parity refused
at its line 13147. A SECOND REFUSAL is needed and is not parity's: the head above
line 34064 reads '392' where the run goes 288 .. 300, which keeps its side's parity
and is still wrong, so a folio must also STEP FORWARD by no more than forty pages
from the last one kept. Where a head's numeral did not survive (30 of 635) the page
is carried between two read folios and the locator says so on itself.

T-1024 REBUILT THIS, and what it found is why the recto side is here. Two faults in
the first derivation left it reading half the leaf:

  * the verso head was SEARCHED FOR INSIDE a line rather than matched on the whole
    of one, so any line containing the phrase was a head — line 9941 is "To  return
    to  the  history  of  Chicago ", a sentence, and it stole the '79' that belongs
    to the recto head 'EDUCATIONAL.' three lines above it, which the audit then
    reported as an odd numeral on a verso that parity must refuse;
  * the recto head was never a head. The rule always named it, and `at()` consulted
    a recto numeral only to break the tie once the verso folio was already known, so
    where a verso numeral had not survived the page was reported unreadable while a
    recto head two lines away carried it.

The cost was on committed data: twelve of T-0826's twenty claims carried no printed
page at all, among them the first term of court in the Mansion House loft, whose
page (153) stands two lines under 'THE BENCH AND BAR.' at line 18524. Reading both
sides carries the folio on 512 of 615 heads where the verso side alone carried 271
of 319, and nine of the twenty claims' folios move.

ONE HEAD IN THIS VOLUME IS STILL NOT MATCHED and the record says so rather than
widening a pattern until it is: the OCR set the running head at line 34254 as
'niSTOET OF CHICAGO.', and bk_mose2_010's page 294 is read by hand off the bare
'294' above it. This module reports that page as carried, and the disagreement is
written into the claim's locator.

usage:
  derive_book_folios.py --text <path> --audit
  derive_book_folios.py --text <path> --at <line> [--at <line> ...]
"""
import argparse, re, sys
from pathlib import Path

BARE = re.compile(r'^\s*(\d{1,3})\s*$')
VERSO_HEAD = re.compile(r'^\s*H[I1l]ST[O0]R[YT7] +[O0][FE] +CH[I1]C *A *G *[O0]\W*\s*$', re.I)
RECTO_HEAD = re.compile(r"^\s*[A-Z][A-Z'\.\,\-\u2014 ]{5,}\.?\s*$")
NEAR = 6  # the folio stands alone within this many lines of its head


def heads(lines):
    """Every running head in document order, verso and recto, with its numeral.

    Returns (head_line, numeral_line or None, numeral or None, side).

    THE VERSO HEAD IS MATCHED ON THE WHOLE LINE AND NOT SEARCHED FOR INSIDE ONE
    (T-1024). `re.search` made a head of any line CONTAINING the phrase, and this
    volume writes it in prose: line 9941 is "To  return  to  the  history  of
    Chicago ", a sentence. The detector took it for a verso head, looked six lines
    back, and took the `79` at line 9937 — which is the RECTO head 9934's numeral,
    `EDUCATIONAL.` — and then reported it as an odd numeral on a verso that the
    parity check must refuse. It was neither odd for its side nor on a head. The
    loose match also inflated the head count: 319 against 295 whole-line ones.

    THE RECTO HEAD IS A HEAD (T-1024). The rule this module derived for volume 2
    always said both sides carry a folio — alone above 'HISTORY OF CHICAGO.' on a
    verso, after the chapter's own title on a recto — but only the verso side was
    ever read, and a recto numeral was used solely to break the tie once the verso
    folio was known. The volume prints 336 recto folios and 320 of them are odd. So
    where a verso numeral did not survive, the page was reported as unreadable while
    a recto head two lines away carried it: printed page 153, the first term of
    court, sat under a locator saying its heads "lost their numerals to the OCR".
    """
    out = []
    for i, l in enumerate(lines, 1):
        if VERSO_HEAD.match(l):
            side, span = 'verso', range(i - 1, max(0, i - NEAR - 1), -1)
        elif RECTO_HEAD.match(l):
            side, span = 'recto', range(i + 1, min(len(lines), i + NEAR) + 1)
        else:
            continue
        found = (None, None)
        for j in span:
            m = BARE.match(lines[j - 1])
            if m:
                found = (j, int(m.group(1)))
                break
        if side == 'recto' and found[1] is None:
            continue  # a title with no numeral is a chapter opening, not a head
        out.append((i, found[0], found[1], side))
    return _one_head_per_numeral(out)


def _one_head_per_numeral(rows):
    """Two head lines may reach the same numeral, and only one of them is the head.

    The OCR breaks a running head into fragments — lines 53984-53988 are
    'OF  THE', 'VINUSTN  M' and 'MANUFACTURES.', all three of them lines of capitals
    above the same '453' — and each fragment claimed the folio. The second and third
    then stepped 0 from the first and were refused, which carried a page whose
    numeral is plainly printed. The head is the fragment NEAREST its numeral; the
    others are wreckage of the same head and are dropped.
    """
    best = {}
    for h, j, n, side in rows:
        if j is None:
            continue
        cur = best.get(j)
        if cur is None or abs(h - j) < abs(cur[0] - j):
            best[j] = (h, j, n, side)
    keep = set(best.values())
    return [r for r in rows if r[1] is None or r in keep]


def verso_heads(lines):
    """The verso side alone, in the shape the audit's head counts still report."""
    return [(h, j, n) for h, j, n, side in heads(lines) if side == 'verso']


def parity_corrected(rows):
    """Apply the parity check: a VERSO folio is EVEN and a RECTO folio is ODD, and a
    numeral of the wrong parity for its side is the OCR and not the page — but only
    where the run says which page it must be.

    The candidate is n-1 or n+1, and it is accepted only if exactly one of them falls
    strictly between the nearest surviving numerals either side. That refusal matters:
    the head above line 80964 reads '39' between 638 and 640, so neither 38 nor 40 can
    be the page, the numeral is a lost digit rather than a flipped one, and the honest
    answer is that this page is carried between two read folios. A rule that always
    corrected would have printed page 38 six hundred pages late.

    THE CHECK IS NOW TWO-SIDED (T-1024). It used to be 'even or refused', because only
    versos were read; a recto folio is odd BY THE SAME RULE, and 320 of this volume's
    336 recto numerals are. The sixteen that are not are refused and corrected here
    exactly as the thirteen odd versos are.
    """
    raw = list(rows)
    out = []
    for k, (h, j, n, side) in enumerate(raw):
        want = 0 if side == 'verso' else 1
        if n is None:
            out.append((h, j, None, side, 'numeral did not survive the OCR'))
            continue
        if n % 2 == want:
            out.append((h, j, n, side, 'read'))
            continue
        prev = next((x[2] for x in reversed(raw[:k]) if x[2] is not None), None)
        nxt = next((x[2] for x in raw[k + 1:] if x[2] is not None), None)
        fits = [c for c in (n - 1, n + 1)
                if c % 2 == want
                and (prev is None or c > prev)
                and (nxt is None or c < nxt)]
        if len(fits) == 1:
            out.append((h, j, fits[0], side, f"parity-corrected from the OCR's {n}"))
        else:
            out.append((h, j, None, side,
                        f"numeral {n} is {'odd' if n % 2 else 'even'} on a {side} head, "
                        f"refused by the parity check and not correctable inside the "
                        f"run ({prev} .. {nxt})"))
    return out


def plausible_step(rows, max_step=40):
    """Refuse a folio whose STEP from the last one kept cannot be a run of pages.

    Parity cannot catch a misread that keeps the side's parity, and the volume has
    them: the head above line 34064 reads '392' where the run goes 288, 290, ...,
    298, 300, and the one above 34489 reads '200' in the same stretch. Both are even,
    both pass a verso parity check, and both are wrong. What refuses them is the one
    thing the page order guarantees — HEADS RUN FORWARD, one page at a time when both
    sides survive and further when the OCR lost some — so a step that is zero,
    negative or larger than forty pages is not a page run, and the pages around it are
    carried between the two nearest folios that are.

    THE STEP IS NO LONGER REQUIRED TO BE EVEN (T-1024). It was, because consecutive
    VERSO heads are two pages apart; with both sides interleaved the normal step is
    one, and requiring an even step would refuse every recto folio in the book.
    """
    kept = []
    out = []
    for h, j, folio, side, how in rows:
        if folio is None:
            out.append((h, j, None, side, how))
            continue
        last = kept[-1] if kept else None
        if last is not None:
            step = folio - last
            if step <= 0 or step > max_step:
                out.append((h, j, None, side,
                            f'numeral {folio} refused: a step of {step} from the '
                            f'last read folio {last} is not a run of pages'))
                continue
        kept.append(folio)
        out.append((h, j, folio, side, how))
    return out


def sequence(lines):
    """The volume's folio sequence: both sides, parity-checked and step-checked."""
    return plausible_step(parity_corrected(heads(lines)))


def audit(lines):
    rows = sequence(lines)
    for side in ('verso', 'recto'):
        mine = [r for r in rows if r[3] == side]
        raw = [n for _, _, n, sd in heads(lines) if sd == side and n is not None]
        want = 0 if side == 'verso' else 1
        print(f"{side} running heads: {len(mine)}")
        print(f"  with a numeral: {len(raw)}")
        print(f"  numeral lost to the OCR: {len(mine) - len(raw)}")
        print(f"  raw numerals of the right parity for the side: "
              f"{sum(1 for n in raw if n % 2 == want)} of {len(raw)}")
    print(f"lines: {len(lines)}")
    kept = [r for r in rows if r[2] is not None]
    print(f"heads in document order: {len(rows)}; folio read or corrected on {len(kept)}")
    corrected = [r for r in rows if r[4].startswith('parity')]
    refused = [r for r in rows if r[4].startswith('numeral')]
    print(f"{len(corrected)} parity-corrected inside their run:")
    for h, j, f, side, how in corrected:
        k = [x for x, r in enumerate(rows) if r[0] == h][0]
        nb = [rows[x][2] for x in range(max(0, k - 2), min(len(rows), k + 3))]
        print(f"  line {j} ({side}): -> {f}   run {nb}   [{how}]")
    print(f"{len(refused)} refused, so those pages are carried between read folios:")
    for h, j, f, side, how in refused:
        print(f"  line {j} ({side}): {how}")
    return 0


def at(lines, line_no):
    """The printed page a line of the committed text stands on.

    A head BEGINS a page, so a line standing after one head and before the next is on
    that head's folio. Where the nearest preceding head has no folio the page is
    CARRIED between the two nearest that do, and this says so rather than asserting
    one.
    """
    rows = sequence(lines)
    before = [r for r in rows if r[0] < line_no]
    after = [r for r in rows if r[0] > line_no]
    if not before:
        n = next((r[2] for r in after if r[2] is not None), None)
        return ('on a page before the first read folio'
                + (f' ({n})' if n is not None else ''))
    h, j, folio, side, how = before[-1]
    if folio is not None:
        note = '' if how == 'read' else f' ({how})'
        return f'printed page {folio}{note}, read off the {side} head at line {h}'
    lo = next((r for r in reversed(before) if r[2] is not None), None)
    hi = next((r for r in after if r[2] is not None), None)
    lo_s = f'{lo[2]} at line {lo[0]}' if lo else 'the start of the volume'
    hi_s = f'{hi[2]} at line {hi[0]}' if hi else 'the end of the volume'
    gap = sum(1 for r in rows if (lo is None or r[0] > lo[0]) and (hi is None or r[0] < hi[0]))
    return (f'carried between read folios {lo_s} and {hi_s}: the {gap} head(s) between '
            f'them carry no numeral this derivation can keep')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text', required=True)
    ap.add_argument('--audit', action='store_true')
    ap.add_argument('--at', type=int, action='append', default=[])
    a = ap.parse_args()
    lines = Path(a.text).read_text(encoding='utf-8', errors='replace').split('\n')
    if a.audit:
        audit(lines)
    for L in a.at:
        print(f"line {L}: {at(lines, L)}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
