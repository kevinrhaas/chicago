---
id: T-1482
title: Migrate the three platted blocks' six refamilied roofs, whose ancillary slots cross the principal/ancillary line: generate_block_infill's claimed principal/ancillary mix re-dealt rather than field-edited, the ids carried across the reference list, rebaked and published — with the screenshot from Lake and Clark
state: blocked-owner
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1452
opened: 2026-09-20
closed: null
pr: null
claimed_by: run 9/21/2026, 10:58:15 AM CT
blocked_on: A yard building refamilied to a dwelling becomes a second principal roof on a lot that already carries one, which multi_building_lot admits only in a principal-street party-line run: clause a rear cottage as ancillary, move the six onto ground that is not there, or withdraw the verdicts — noting that the term that refused them refuses 3 of the 4 evidence records of the clause it was scored against
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35621907359
---

Migrate the three platted blocks' six refamilied roofs, whose ancillary slots cross the principal/ancillary line: generate_block_infill's claimed principal/ancillary mix re-dealt rather than field-edited, the ids carried across the reference list, rebaked and published — with the screenshot from Lake and Clark.

Piece 3 of 3 of **T-1452 — Migrate the 26 refamilied roofs whose id moves — the phase-one South parcel, the North Division parcel and the three platted blocks — against the measured reference list: sidecars, enclosures, liberties, signage, yard, frontage, lodgers, seating and business files all name these ids, and blk ancillary slots cross the principal/ancillary line; with the screenshot from Lake and Clark**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance, stated before working.** The six outstanding platted-block verdicts are
carried out — the recipe re-dealt rather than field-edited, the ids carried across the
reference list, rebaked and published — or the reason they cannot be is derived from
committed files, gated, and handed to the owner as one question with its remedies
costed.

## WHAT IT DEMONSTRATED, 2026-09-21 — and why the re-deal did not run

The rename is the easy half and it is not what stops them. All six are A-family yard
buildings standing at a `yard` setback off their block alley, **behind the principal roof
on their own lot**, and the adjudication moves every one into an `ordinary_dwellings`
family. `generate_block_infill` reads a roof's inventory class from its group, so a
dwelling family is `principal_functional` — and the parcel gate refuses a second
principal roof on a lot that already carries one. The committed `multi_building_lot` rule
admits a second principal roof **only** on a principal-street lot in a party-line run of
shared side walls (its evidence is Wright's pair of buildings-to-let on the Randolph
line); a cottage in the back yard is not that, and `back_street_lot` says one roof.

Measured, and re-derived on every run by
`tools/measure_block_redeal_remedies.py --check` in `tools/check.sh`:

- **6 of 6** refused by the parcel gate, each against the roof already on its lot. The
  second deal on `blk_randolph_market` is refused the same way: its A1 stands on lot 1,
  which is the lot its own frontage run was dealt.
- **0 of 36** families the adjudication offers across the six would leave the inventory
  class alone. Every offer is an ordinary dwelling, so there is no re-deal *inside* the
  verdict.
- **2 open lots** across the three blocks against **6** roofs needing ground — and both
  are declared open in the recipe with a stated reason, the programme's own
  alternating-vacancy assumption. Taking one overrules that assumption; it does not find
  space.

**And the refusal that produced these six refuses its own evidence.** They were refamilied
for standing nearest a principal street, which is the one term
`ancillary_behind_its_own_roof` scores. Re-read against the same term, **3 of the 4**
documented buildings that clause cites as evidence stand nearest a principal street:
`wolf_point_tavern_stable` is an A1 at 36.70 m, where
`recon_1835_blk_randolph_market_a1_07` is an A1 at 29.28 m. The test that refamilies the
second refamilies the first.

**The three remedies, each costed in the report** (`data/reconstruction/1835_block_redeal_remedies.json`,
read by `docs/RESEARCH/1835_block_redeal_remedies.md`):

1. **Clause a dwelling in the yard** — admit a rear cottage as ANCILLARY and write the
   clause. `ancillary_behind_its_own_roof` applies to A1–A5 only, so a D-family roof in a
   yard is covered by no clause today and `refusals_of` returns that as its own refusal;
   the adoption gate would also have to rule whether such a roof may house anybody.
2. **Move them onto open ground** — the verdict's own "the slot is wanted and the position
   stands" no longer holds, and 4 of the 6 have nowhere to go even after both open lots
   are spent.
3. **Leave them where they are** — withdraw the block verdicts and re-read the clause.
   That is a decision about T-1445's scoring, which this ticket may not make.

Nothing was adjudicated, nothing moved, no confidence changed and no record was written
to. **Blocked on the owner.**
