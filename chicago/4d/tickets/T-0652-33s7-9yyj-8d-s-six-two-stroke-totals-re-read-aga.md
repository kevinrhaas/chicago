---
id: T-0652
title: 33S7-9YYJ-8D's six two-stroke totals, re-read against 6H's footing: its column over-runs its printed 106 by 15
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 866
claimed_by: run 9/5/2026, 4:24:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T10:10:07.190Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33957727181
---

33S7-9YYJ-8D's six two-stroke totals, re-read against 6H's footing: its column over-runs its printed 106 by 15.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0645**, which read the footing of `33S7-9YYJ-6H`'s TOTAL column and settled that
sheet's ten two-stroke figures at 4. 8D is the sibling sheet and it fails the same way, and this
ticket exists so the finding is not quietly generalised to it without a reading.

**The state.** T-0643 read `33S7-9YYJ-8D` line by line and met the identical two-stroke figure on
six lines. It read them **11**, on a stroke-pitch test measured on that leaf: about 30 px between
the strokes, against that sheet's own two-digit `17` at 32 px and its three-digit `106` at 36 px.
Read that way its TOTAL column sums to **121** against a printed footing of **106** — a residual
of +15 that T-0643 recorded and did not explain. Six figures moved from 11 to 4 is −42, which
over-shoots the other way to 79.

**What T-0645 found on 6H, and what it does and does not carry.** 6H's own footing carries the
two-stroke figure twice, in the second and third places of a three-glyph number beginning with a
plain slash. `1 4 11` is not a number, so on THAT leaf the figure is a single numeral. That is an
argument about 6H's footing and about nothing else: 8D's `106` is legible, its stroke-pitch test
separates the forms where 6H's does not, and the two sheets may not be the same hand. **Do not
apply 6H's answer to 8D without reading 8D.**

**The ask.** Re-read the six on 8D at magnification against that sheet's own confirmed digits —
the `17` and the `106` at its foot, and every single `1` in its industry columns — and say which
of the six, if any, are 4s. The +15 is the measurement to explain: state what each of the six
reads and what the column then sums to, and if it still does not close, say so and leave it open
rather than choosing whichever reading closes it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Each of the six named with its line, its stroke geometry, its reading and its confidence.
- The column's sum stated under the reading reached, against the printed 106, with the residual.
- If the residual survives, it is localised to named lines and published, not spread.
- No line reading adjusted to make the total come out; `tools/check.sh` green.

**Links:** T-0643 (the 8D reading) · T-0645 (the 6H footing) · T-0628 (the 6H line index) ·
`data/research/census_1840/pages/33S7-9YYJ-8D.json`

**T-0653 (33S7-9YYJ-B1, 2026-09-04) is a second, independent confirmation, and it is the
stronger one.** B1 carries five matched pairs. Read as 11 its family totals come to 149
against a printed 165; read as 4, on 33S7-9YYJ-6Q's labelled key, they come to 164 — one
person short of the enumerator's own footing, the tightest close in the deposit. Its
line 27 settles the form again from the other side: a 5 and a matched pair standing
together in the tens-and-units band read 54, and 54 is what the page needs. So the pair
is a 4 in this hand on at least two sheets besides 6Q's exemplar, and 8D's six of them
are almost certainly the same. B1's `digit_key_used` block records the check.
