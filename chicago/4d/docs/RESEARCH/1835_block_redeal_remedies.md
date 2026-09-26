# The platted blocks' six refamily verdicts, and the clause that frees them — July 1835

DERIVED — regenerate with `tools/measure_block_redeal_remedies.py --build`. T-1482.

T-1445 adjudicated 285 anonymous roofs and returned 32 refamily verdicts. T-1451 carried out the six whose ids do not move; T-1480 migrated the North Division's nine and T-1494 the phase-one South parcel's eleven. These six are the remainder, and the rename was never what stopped them.

Each is an A-family yard building standing at a yard setback off its block alley, behind the principal roof on its own lot, and the adjudication moves every one into an `ordinary_dwellings` family. The inventory class was read off the GROUP alone, so a dwelling family came out `principal_functional` wherever it stood — and the parcel gate refuses a second principal roof on a lot that already carries one. All six were refused, and the committed `multi_building_lot` rule admits a second principal roof only on a principal-street lot in a party-line run of shared side walls; these six stand off the alley at the back.

**The owner ruled on 2026-09-23:** (a) Treat a rear cottage as ancillary, so a lot may carry a main house plus a rear dwelling. That ruling is now `rear_dwelling_behind_its_own_roof` in the placement policy and a position in `reconcile_665.inventory_class`: off the alley, on a lot whose principal roof is already dealt, a dwelling is ANCILLARY. The same six verdicts re-derived against the same committed files are no longer refused, and because they stay ancillary the blocks' principal-roof counts do not move either.

**What is still not done:** The six are not re-dealt. The recipe stands them as A-family slots, no id has moved and no mesh has been rebaked — T-1611 does that, and this report is what says it now can be.

- outstanding verdicts: **6**
- refused by the parcel gate: **0**
- offered families that would leave the inventory class alone: **0** of 36
- open lots across the three blocks: **2**, against 6 roofs

## The six, and what refuses each one

| roof | becomes | stands | was | now | the refusal |
| --- | --- | --- | --- | --- | --- |
| `recon_1835_blk_randolph_market_a1_07` | `recon_1835_blk_randolph_market_d4_07` | lot 3, off the alley, 5.0 m | A1 (ancillary) | D4 (ancillary) | None |
| `recon_1835_blk_randolph_market_a1_12` | `recon_1835_blk_randolph_market_d4_12` | lot 1, off the alley, 5.0 m | A1 (ancillary) | D4 (ancillary) | None |
| `recon_1835_blk_randolph_market_a3_05` | `recon_1835_blk_randolph_market_d2_05` | lot 0, off the alley, 5.0 m | A3 (ancillary) | D2 (ancillary) | None |
| `recon_1835_blk_randolph_market_a4_06` | `recon_1835_blk_randolph_market_d2_06` | lot 2, off the alley, 4.5 m | A4 (ancillary) | D2 (ancillary) | None |
| `recon_1835_blk_south_water_lasalle_a1_06` | `recon_1835_blk_south_water_lasalle_d3_06` | lot 3, off the alley, 5.0 m | A1 (ancillary) | D3 (ancillary) | None |
| `recon_1835_blk_south_water_wells_a1_07` | `recon_1835_blk_south_water_wells_d1_07` | lot 3, off the alley, 5.0 m | A1 (ancillary) | D1 (ancillary) | None |

Every one of the 36 families the adjudication offers across the six is an ordinary dwelling, so no offered family avoided the promotion by its letter alone. There was no re-deal inside the verdict, which is why the question had to go to the owner rather than being solved here.

## The ground the other remedy would need

| block | roofs needing a lot | open lots |
| --- | ---: | ---: |
| `blk_randolph_market` | 4 | 1 |
| `blk_south_water_lasalle` | 1 | 0 |
| `blk_south_water_wells` | 1 | 1 |

And each of those open lots is declared open in the recipe with a stated reason — the programme's own alternating-vacancy assumption. Taking one is overruling that assumption, not finding space.

## The clause, asked its own question

1 of the 4 documented buildings this clause cites as its evidence FRONTS a principal street, which is the position the clause says it avoids and the one term the policy scores. `wolf_point_tavern_stable` is an A1 standing 36.70 m from a principal street; `recon_1835_blk_randolph_market_a1_07` is an A1 standing 29.28 m from one. The test that refamilies the second refamilies the first. That is a question about the clause, and this tool does not answer it. 2 more front no street at all, out on the reservation beyond the census's frontage reach (T-1511): the scored term has no class to read for them, and the clause's own answer is printed beside it — it refuses 2 of them on the `yard` setback it seats by, which is measured off a block alley this ground does not have.

| evidence record | family | street it fronts | class | setback m | scored term | the clause refuses it |
| --- | --- | --- | --- | ---: | --- | --- |
| `western_hotel_stable` | A1 | canal | ordinary | 0.59 | no | no |
| `wolf_point_tavern_stable` | A1 | lake | principal | 36.70 | yes | yes |
| `fort_dearborn_big_barn` | A2 | (none) | — | 270.75 | cannot speak — it fronts none | yes |
| `fort_dearborn_wash_house` | A5 | (none) | — | 420.22 | cannot speak — it fronts none | yes |

## The three remedies, and what each one changes

All three change what the town IS, so this tool costed them and asked rather than choosing. The owner answered on 2026-09-23; the one he took is marked.

### Admit a dwelling-family roof at a yard setback behind its lot's principal roof — a rear cottage — as ANCILLARY, and write the clause that covers it. — **TAKEN**

The town gains a building class it had never stated. `ancillary_behind_its_own_roof` applies to A1–A5 only, so a D-family roof in the yard was covered by no clause at all. The adoption gate had to be ruled on too: it refused an ancillary roof an occupant on the reasoning that a yard building is a shed, and a rear cottage is not one.

**Costs:** 6 roofs keep their position; one new policy clause, tier `inferred` and citing no record; one ruling on adoption. TAKEN by the owner on 2026-09-23.

### Deal the six onto free lots as principal roofs.

The verdict's own sentence — `the slot is wanted and the position stands` — no longer holds, and the ground is not there: the three blocks hold 2 open lot(s) against 6 roofs, and each of those lots is declared open in the recipe with a stated reason, carried into `ground` below. Taking one is overruling the programme's alternating-vacancy assumption, not finding space.

**Costs:** 4 roof(s) with nowhere to stand even after both open lots are spent.

### Let the six stand as the A-family yard buildings they are and record the refusal against the adjudication.

It re-opens T-1445's scoring for this clause, because the reason these six were refused refuses 1 of the clause's own 4 evidence records too. That is the owner's call and not this tool's: a scored term that its own evidence breaches is either the wrong term or the wrong evidence.

**Costs:** 0 roofs move; the adjudication's block verdicts are withdrawn and the clause is re-read.

## Where the ruling lives

- data/reconstruction/1835_placement_policy.json — the clause `rear_dwelling_behind_its_own_roof`, tier `inferred`, citing no record because the town holds none
- tools/reconcile_665.py — `inventory_class` reads the position as well as the group, and is the one derivation the generators deal by
- tools/generate_block_infill.py — the adoption gate asks the GROUP, so a rear cottage may house a household and a privy still may not

Because the six stay ancillary, the blocks' principal-roof counts are unchanged, so `lot_ceiling_principal` and `block_rooms` are untouched. A promotion to principal would have breached both.
