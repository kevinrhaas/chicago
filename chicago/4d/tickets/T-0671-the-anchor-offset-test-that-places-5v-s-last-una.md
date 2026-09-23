---
id: T-0671
title: The anchor-offset test that places 5V's last unassigned_ink stroke, salvaged from the closed PR #746
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-05
pr: 861
claimed_by: run 9/5/2026, 1:50:50 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T13:05:44.759Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33950203006
---

The anchor-offset test that places 5V's last `unassigned_ink` stroke, salvaged from the
closed PR #746.

**Filed 2026-09-04 when PR #746 was closed**, so the one thing that branch held which `dev`
does not is not lost with it.

## What happened

Two runs claimed **T-0565** sixty-five seconds apart. **#747 merged** (2026-09-04T02:06Z)
and is on `dev`; **#746** rewrote the same page file from its pre-#747 state, so merging it
would have reverted #747's reading. #746 said so itself — *"Do not merge as-is … Nothing
here should be merged over #747"* — and asked for this one piece to be carried across as a
small follow-up ticket rather than by merging the branch. This is that ticket.

Nothing is lost on the substance: #747 reaches the same line grid independently, and with
stronger evidence — an rms sweep over line counts 27 to 38, plus a jackknife.

## What is actually wanted

`33S7-9YYJ-5V`'s TOTAL column, as read on `dev`, leaves **one stroke marked
`unassigned_ink`** — ink the reader is confident about but could not attribute to a line.
#746 had an **anchor-offset test** that places it, and the band-D assignment that follows.

The test is in the closed branch `steward/t-0565-total-column-line-index`, which is not
deleted — read it there rather than re-deriving from nothing.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The anchor-offset test is lifted onto **`dev`'s** version of the page file — #747's — and
   never by restoring #746's copy of it.
2. The stroke is either assigned to a line, with the offset that places it stated as a
   number, or it stays `unassigned_ink` and the ticket records why the test does not settle
   it. Both are acceptable outcomes; a silent drop is not.
3. If it is assigned, the column's total is re-closed against the sheet's own printed
   figure, and the before/after is stated.
4. `bash tools/check.sh` green.
