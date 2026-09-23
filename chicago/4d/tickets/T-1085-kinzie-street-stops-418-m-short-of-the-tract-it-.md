---
id: T-1085
title: Kinzie Street stops 418 m short of the tract it bounds: Wright draws it the length of Wabansia and the committed line is extrapolated to meet it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: 1204
claimed_by: run 9/12/2026, 12:29:28 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T18:26:15.361Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34708246430
---

Kinzie Street stops 418 m short of the tract it bounds: Wright draws it the length of Wabansia and the committed line is extrapolated to meet it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1070, 2026-09-12, seating Wabansia. `kinzie` in `data/streets/1835.json` ends
at local east **-320**, attested off the Thompson plat (T-0713), which draws the Original
Town and stops at its west boundary. Wright's 1834 survey draws the same street on west,
the whole length of Wabansia: the corridor is read and committed at
`data/traces/wabansia_streets.json` § streets `kinzie`, with Wright's own `Kinzie`
lettering at NA px 1150-1450, y 2060-2110. So the reach exists on a sheet this project
holds, and the committed line is silent about it.

T-1070's seating had to **extrapolate `kinzie` 417.9 m west of its own west end** to have
something to hang Wabansia's ladder from. That is a consistency check, not a control
point, and it is labelled as one in `data/traces/wabansia_seating.json` § datum. Six
streets are now committed north of a line that does not reach them.

**Why it is its own ticket and not a line in that one.** `data/streets/1835.json` § _doc:
"a bend added to the plat line moves platted lot lines the whole length of the street and
re-scores the corridor-intrusion count (measured on T-0111, both gates red)". Carrying an
ATTESTED street is not the same act as adding an inferred one beside it, and its blast
radius is the town, not the tract.

**Acceptance:**

1. `kinzie` carried west to Wabansia's own west boundary rule, on Wright's reading, with
   the geometry re-derivable by a gated `--check` the way the seating is.
2. The reach west of local east -320 carries its OWN grade and its own note: the Thompson
   plat does not attest it and Wright does, and the two halves of the line are not the
   same claim.
3. The corridor-intrusion count and the platted lot derivations re-scored, and the number
   before and after stated — not assumed unchanged.
4. `status_1835` for the new reach argued, not inherited: `kinzie` east of the town is a
   worn earth track with ordinary traffic; west of it, over Wabansia's prairie, that is a
   claim no source in this corpus makes.

**Links:** T-1070 · T-0713 · T-0790 · `data/traces/wabansia_seating.json` § datum ·
`data/traces/wabansia_streets.json` § streets.kinzie, § cross_check
