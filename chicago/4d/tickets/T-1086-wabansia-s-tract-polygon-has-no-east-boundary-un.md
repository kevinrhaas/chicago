---
id: T-1086
title: Wabansia's tract polygon has no east boundary until the water-lot wedge is seated, and place_vocabulary still calls the tract undecided on ground the project now commits
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: 1207
claimed_by: run 9/12/2026, 1:37:48 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T19:39:34.887Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34711573150
---

Wabansia's tract polygon has no east boundary until the water-lot wedge is seated, and place_vocabulary still calls the tract undecided on ground the project now commits.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1070, 2026-09-12, seating Wabansia. Two loose ends the seating recorded rather
than closed, together because the same reading closes both.

**1. The tract has no outline.** T-1070 publishes
`data/traces/wabansia_seating.json` § `block_grid_polygon_local_enu_m` and deliberately
does NOT call it the tract's: Wabansia runs east of the block grid to the North Branch,
over the water-lot wedge — Kain's and Hight's subdivision — which T-1077 read as a lot
strip and said in its own words it did not seat. Until that wedge is on modern ground the
tract has no east boundary, and this project will not draw one it cannot derive. The same
file's `tract_polygon_local_enu_m` is `{"seated": false}` with that reason in it.

**2. `place_vocabulary.json` is now stale about this ground.** It resolves `Wabansia` as
UNDECIDED on basis **B4** — "a survey adjacent to the town that this project commits none
of (Kinzie's Addition, Wabansia — T-0789, T-0790)" — and names T-0790 as the ticket that
would settle it. That sentence is false of the ground as of this seating, and it is false
of Kinzie's Addition too: T-1060 committed its streets. A Democrat notice naming Wabansia
therefore still lands `undecided` on a rule whose stated reason has expired.

**Why it is not a one-line edit.** B4 is the owner's ruling and moving a place off it
changes what counts as a Chicago appearance, which re-scores the register's person counts.
`outside` is the likely answer for both tracts — they are adjacent to the platted town,
not in it — but "likely" is not how this file is written, and the B-rules are his.

**Acceptance:**

1. The water-lot wedge seated off the same datum, and Wabansia's tract polygon derived
   from the grid's west and north bounds, Kinzie Street, and the wedge's river edge.
2. `tract_polygon_local_enu_m` filled by the same gated tool, with the committed west bank
   cross-check stated — T-1070 measured T-1074's tier-4 block corner 66 m inside that bank
   and refused it; a tract boundary meets the same question.
3. `place_vocabulary.json` re-ruled for `Wabansia` AND `Kinzie's Addition` — by the owner,
   or blocked on him — with the register's before/after person counts in the PR.

**Links:** T-1070 · T-1077 · T-1074 · T-0790 · T-0789 · T-1060 ·
`data/research/newspapers/place_vocabulary.json` § B4

---

**WHAT LANDED** (2026-09-12). Seated by `tools/seat_wabansia_streets.py`, the tool that already
held T-1070's seating, because one edge cannot be derived by two tools:

1. **The wedge is on the ground.** `data/traces/wabansia_seating.json` §
   `water_lot_wedge_local_enu_m` — the outline (10.84 acres), the four ranks tiled rather than
   overlapped, all 26 of Wright's figures, and the north closure the bank was never measured on,
   graded for it. Every number rebuilt from `wabansia_water_lots.json`, never re-typed, so a
   changed reading fails `--check`.
2. **The tract has an outline.** § `tract_polygon_local_enu_m` — 24 vertices, 78.63 acres,
   `seated: true`. West and north from T-1074's boundary rules, south from the committed `kinzie`
   line, east from the grid's own east rule down four tiers and then the wedge's river edge.
3. **The bank cross-check, answered rather than refused.** T-1070 refused a block corner 66 m
   inside the committed water. The wedge's independent reading of that bank agrees with the
   committed trace within 1.8 m at four stations of five and 8.4 m at the fifth, and the grid's
   east rule runs 2.1-5.7 m inside it on tiers 1-3. So the disagreement is the one jog corner,
   which is carried as Wright inked it with its 18.6 m recorded beside it.
4. **A correction underneath.** The block grid polygon's south edge held Kinzie's rule flat
   across 530 px and drifted 12.4 m to 19.8 m north of the committed centreline. Carried by the
   reading's own 0.019 shear it stands 12.69 m at every column, against the 12.19 m that is half
   the platted 80 ft corridor. Two vertices move (+0.25 m N, 7.14 m S); seventeen do not.
5. **Clause 3 is blocked on the owner, with the counts.** `place_vocabulary.json`'s two notes now
   state the truth — both surveys are committed, so the stated reason for B4 has expired — and the
   RULING is left where it is, because `resolution` and `basis` are his. **T-1087** carries the
   question, `blocked-owner`, with the measurement that removes the fear T-1086 named: the
   re-ruling moves ONE person (`person_uncertain_doctor_kimberly`; Kinzie's Addition's two are
   already `inside` on `Chicago`).

Three geometric invariants are checked rather than asserted in prose: the blocks and the wedge must
lie inside the tract, the four ranks must tile the wedge, and no figure may seat outside its own
outline by more than the registration's own 16.19 m RMS. Two figures do seat outside — 13 by 6.00 m
and 14 by 0.91 m, both cells T-1077 graded thin — and both are recorded rather than moved.
