---
id: T-1233
title: Render the asserted person facts and every withheld candidate's reason on the resident card, and rule on the 83 unread resident field paths — wired, refused in writing, or removed
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1146
opened: 2026-09-17
closed: 2026-09-17
pr: 1394
claimed_by: run 9/17/2026, 6:46:07 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T12:56:31.486Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35217105791
---

Render the asserted person facts and every withheld candidate's reason on the resident card, and rule on the 83 unread resident field paths — wired, refused in writing, or removed.

Piece 2 of 2 of **T-1146 — Spend matched household and person-profile research into structured relationships, names, sex, dates and life events, with every withheld fact legible**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. T-1232 shipped the first half of this: the card's "Spent from the matched research" row
   renders every asserted fact with its confidence swatch, the date it describes, its source,
   its record id and the sentence it was read from. What is left here is the WITHHELD half.
2. The card states, in readable text, the reason every withheld candidate was withheld:
   later-only, out of town, contradicted, insufficient identity or referred to another ticket.
3. All 83 unread resident field paths in `tools/layer_reads_baseline.json` are reviewed. Each is
   either wired to a visitor-facing reader and un-banked in the same commit, retained with a
   written `refused_because`, or removed as genuine duplicate machinery. A path left unread with
   no stated refusal is a fail.
4. `tools/measure_layer_reads.py` is green and the bank carries no entry that is not either a
   deliberate refusal or a figure the tree still holds.

**Links:** T-1146 (parent) · T-1232 · T-0021 · T-1029.
