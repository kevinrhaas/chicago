---
id: T-1325
title: Open a firm from where the visitor already is: a person's card lists every business they hold a role in, and a signboard tap and a building card's Use line open that firm's card
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1181
opened: 2026-09-18
closed: 2026-09-19
pr: 1519
claimed_by: run 9/19/2026, 7:12:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T13:28:31.301Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35442046588
---

Open a firm from where the visitor already is: a person's card lists every business they hold a role in, and a signboard tap and a building card's Use line open that firm's card.

Piece 2 of 2 of **T-1181 — A Businesses view in the app: every firm by trade, street and tier, with its proprietors, staff, dated locations and location limit on one card — the visible surface for the audit and reconstruction bands**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

A visitor standing at John Dean Caton's card reads the four houses the register
puts him in and opens one; a visitor standing at Temple's Lake Street building
reads the three houses the register puts in that roof, on the Use row, and opens
one; and a card opened by aiming at a signboard leads with the firm the board
hangs for. Every count is read off `data/businesses/index.json` at paint time and
asserted against the file by the smoke, never typed. A roof the register puts no
house in says nothing at all.

---

**DONE, 2026-09-19.** `businesses.js` now exports `firmCrosswalk(index)`, which
folds the compiled index once into `byPerson` and `byStructure`; `people.js` and
`popup.js` share it rather than each folding 196 rows, and `main.js` reads the
index before the two directories that cross-reference it.

Three things the doing of it settled:

- **One row a firm, not one row a printing.** Twelve person-firm pairs are named
  twice on the same record because the register prints the same person under two
  styles — "J. D. Caton" and "J. Dean Caton" are one partner of Collins & Caton.
  The crosswalk folds the roles onto one entry; the smoke asserts that the register
  names Caton five times and the card lists four firms, so the fold cannot be
  quietly undone. Filed on T-1182 with the eleven others.
- **The 26 anchored houses are refused, not guessed.** Their landmark lives in
  `limit_reason`'s prose and `structure_id` is null on every one of them, so the
  Sauganash still cannot say which houses stand against it. Parsing a sentence for
  an id would be the tidy-looking invention this project exists not to make; filed
  on T-1182.
- **A silent roof stays silent.** A structure the register puts no house in renders
  no firms at all on its Use row, asserted as its own term of the smoke check,
  because an empty answer there would read as a finding.

Verified: `check.sh` PASS (533 steps, none red, no skipped step reporting a missing
module) and `SMOKE_STAGE=12` green at BOTH viewports on all four new checks. The two
reds part 12 carries are dev's own and were measured on a clean `origin/dev`
worktree to prove it — T-1387 and T-1382.
