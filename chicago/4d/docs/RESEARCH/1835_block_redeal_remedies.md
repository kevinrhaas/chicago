# The platted blocks' six refamily verdicts, and why none of them can be carried out — July 1835

DERIVED — regenerate with `tools/measure_block_redeal_remedies.py --build`. T-1482.

T-1445 adjudicated 285 anonymous roofs and returned 32 refamily verdicts. T-1451 carried out the six whose ids do not move; T-1480 migrated the North Division's nine and T-1494 the phase-one South parcel's eleven. These six are the remainder, and the rename is the easy half of them — it is not what stops them.

Each is an A-family yard building standing at a yard setback off its block alley, behind the principal roof on its own lot, and the adjudication moves every one into an `ordinary_dwellings` family. `generate_block_infill` reads a roof's inventory class from its group, so a dwelling family is `principal_functional` — and the parcel gate refuses a second principal roof on a lot that already carries one. The committed `multi_building_lot` rule admits a second principal roof only on a principal-street lot in a party-line run of shared side walls; these six stand off the alley at the back.

- outstanding verdicts: **6**
- refused by the parcel gate: **6**
- offered families that would leave the inventory class alone: **0** of 36
- open lots across the three blocks: **2**, against 6 roofs

## The six, and what refuses each one

| roof | becomes | stands | was | now | the refusal |
| --- | --- | --- | --- | --- | --- |
| `recon_1835_blk_randolph_market_a1_07` | `recon_1835_blk_randolph_market_d4_07` | lot 3, off the alley, 5.0 m | A1 (ancillary) | D4 (principal_functional) | blk_randolph_market: two principal roofs on one lot — lot 3 already carries recon_1835_blk_randolph_market_d4_03 |
| `recon_1835_blk_randolph_market_a1_12` | `recon_1835_blk_randolph_market_d4_12` | lot 1, off the alley, 5.0 m | A1 (ancillary) | D4 (principal_functional) | blk_randolph_market: two principal roofs on one lot — lot 1 already carries the frontage run phase3_platted_block_randolph_market_second_deal was dealt |
| `recon_1835_blk_randolph_market_a3_05` | `recon_1835_blk_randolph_market_d2_05` | lot 0, off the alley, 5.0 m | A3 (ancillary) | D2 (principal_functional) | blk_randolph_market: two principal roofs on one lot — lot 0 already carries recon_1835_blk_randolph_market_d5_01 |
| `recon_1835_blk_randolph_market_a4_06` | `recon_1835_blk_randolph_market_d2_06` | lot 2, off the alley, 4.5 m | A4 (ancillary) | D2 (principal_functional) | blk_randolph_market: two principal roofs on one lot — lot 2 already carries recon_1835_blk_randolph_market_d6_02 |
| `recon_1835_blk_south_water_lasalle_a1_06` | `recon_1835_blk_south_water_lasalle_d3_06` | lot 3, off the alley, 5.0 m | A1 (ancillary) | D3 (principal_functional) | blk_south_water_lasalle: two principal roofs on one lot — lot 3 already carries recon_1835_blk_south_water_lasalle_d2_05 |
| `recon_1835_blk_south_water_wells_a1_07` | `recon_1835_blk_south_water_wells_d1_07` | lot 3, off the alley, 5.0 m | A1 (ancillary) | D1 (principal_functional) | blk_south_water_wells: two principal roofs on one lot — lot 3 already carries recon_1835_blk_south_water_wells_d2_06 |

Every one of the 36 families the adjudication offers across the six is an ordinary dwelling, so no offered family avoids the promotion. There is no re-deal inside the verdict.

## The ground the other remedy would need

| block | roofs needing a lot | open lots |
| --- | ---: | ---: |
| `blk_randolph_market` | 4 | 1 |
| `blk_south_water_lasalle` | 1 | 0 |
| `blk_south_water_wells` | 1 | 1 |

And each of those open lots is declared open in the recipe with a stated reason — the programme's own alternating-vacancy assumption. Taking one is overruling that assumption, not finding space.

## The clause, asked its own question

3 of the 4 documented buildings this clause cites as its evidence stand nearest a principal street, which is the position the clause says it avoids and the one term the policy scores. `wolf_point_tavern_stable` is an A1 standing 36.70 m from a principal street; `recon_1835_blk_randolph_market_a1_07` is an A1 standing 29.28 m from one. The test that refamilies the second refamilies the first. That is a question about the clause, and this tool does not answer it.

| evidence record | family | nearest street | class | setback m | breaches its own clause |
| --- | --- | --- | --- | ---: | --- |
| `western_hotel_stable` | A1 | canal | ordinary | 0.59 | no |
| `wolf_point_tavern_stable` | A1 | lake | principal | 36.70 | yes |
| `fort_dearborn_big_barn` | A2 | lake | principal | 270.75 | yes |
| `fort_dearborn_wash_house` | A5 | lake | principal | 420.22 | yes |

## The three remedies, and what each one changes

### Admit a dwelling-family roof at a yard setback behind its lot's principal roof — a rear cottage — as ANCILLARY, and write the clause that covers it.

The town gains a building class it has never stated. `ancillary_behind_its_own_roof` applies to A1–A5 only, so a D-family roof in the yard is covered by no clause, and `refusals_of` returns a family with no clause as its own refusal. The adoption gate would also have to rule on whether such a roof may house anybody: it refuses an ancillary roof today on the reasoning that a yard building is a shed.

**Costs:** 6 roofs keep their position; one new policy clause; one ruling on adoption.

### Deal the six onto free lots as principal roofs.

The verdict's own sentence — `the slot is wanted and the position stands` — no longer holds, and the ground is not there: the three blocks hold 2 open lot(s) against 6 roofs, and each of those lots is declared open in the recipe with a stated reason, carried into `ground` below. Taking one is overruling the programme's alternating-vacancy assumption, not finding space.

**Costs:** 4 roof(s) with nowhere to stand even after both open lots are spent.

### Let the six stand as the A-family yard buildings they are and record the refusal against the adjudication.

It re-opens T-1445's scoring for this clause, because the reason these six were refused refuses 3 of the clause's own 4 evidence records too. That is the owner's call and not this tool's: a scored term that its own evidence breaches is either the wrong term or the wrong evidence.

**Costs:** 0 roofs move; the adjudication's block verdicts are withdrawn and the clause is re-read.

Blocked on the owner. All three change what the town IS, and this tool adjudicates nothing.
