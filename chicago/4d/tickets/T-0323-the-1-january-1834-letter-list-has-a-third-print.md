---
id: T-0323
title: The 1 January 1834 letter list has a third printing that T-0318 did not know about, and it repairs the A-H half without page images
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 507
claimed_by: run 8/28/2026, 10:15:43 PM CT
blocked_on: null
needs_bake: false
---
T-0318 says of the January 1834 letter list that the two January printings "do not repair
each other and the images are the only route". **There is a third printing and it was not
known when that ticket was written.** T-0311 found it while reading February 1834:
`chicago_democrat_1834_02_04`, page 4 column 2, lines 2857-2943 — the same 1 January 1834
Chicago list, reprinted a third time over John S. C. Hogan's signature.

It is a far better witness than either January one, for a structural reason rather than a
lucky one: **it is in the ruled dialect and sets one name per line.** The January printings
came out of `.docx` and the extraction crushed the printed list's two alphabetical columns
into eight paragraph lines. Here the first alphabetical column survives at name level all
the way from Atkins to Harkness.

## What it already gives

- **71 names read at name level**, A to H, transcribed in full in the claim's `normalized`
  field at `extracted/chicago_democrat_1834_02_04.json` c016. Four further lines of the
  same column are debris, so the printed first column was about 75 names.
- **That measures T-0310's floor.** T-0310 minted 97 from the whole list and its coverage
  note called 97 "a FLOOR and not the printed length". About 75 in the A-H half alone
  settles it: the printed list was very substantially longer than 97.
- **One of T-0318's four cut surnames is closed.** `William Cr[…]` is **William Criss**.
- The SECOND alphabetical column is cut by the segmenter's right edge to first names and
  initials here (`Isanc K…`, `Lewis …`, `Mirand…`, `A. M'L…`), so the H-Z half still wants
  either the page images or a better segmentation of this same column.

## Why T-0311 did not do the repair

The names were deliberately **not minted**. T-0292's rule is that a list printed more than
once is minted ONCE and the other printings recorded as reprints; T-0299 is the open ticket
about what happens when that rule is broken, and minting these 71 would add 71 more
same-list-different-OCR people to a gazetteer that already has that problem. Repairing the
January entries means declaring merges in `identity.json` with a `merge_rule` for each —
`Anthony Becra` here against `Anthony Heere` there — and that is T-0318's and T-0299's
work, not a reading pass's.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- T-0318's plan is rewritten to start from this printing rather than from the page images,
  and its acceptance says which of its four cut surnames and seven bare ones this witness
  closes and which still need the images.
- Every merge that closes one is declared in `identity.json` with a `merge_rule` naming
  both spellings verbatim, and the gazetteer recompiles green.
- The claims themselves are not edited to agree (T-0299's rule).

**Links:** T-0318 (the gap this narrows) · T-0299 (the merge policy and the 298-people
problem) · T-0292 (mint once, record the reprints) · T-0310 (the 97) · T-0311 (the read
that found it) · `data/research/newspapers/README.md` § Nor does the Democrat's own first
issue
