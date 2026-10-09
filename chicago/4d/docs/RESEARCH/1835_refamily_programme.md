# The re-familying programme, reported — what the ruling asked and what it reaches (T-1560)

DERIVED — regenerate with `python3 tools/report_refamily_programme.py --build`.
Piece 4 of 4 of T-1556. **This report moves nobody and writes no card.**

## The ruling

> the owner's ruling of 2026-09-24 on T-1530, carried in T-1556: the surplus the re-cut holds is RE-FAMILIED rather than retired — the heads move into the buckets the re-cut grew instead of being un-written

**A move is** one reconstructed person counted in a different cell of the same ladder. His card, his id, his residence_grade and every citation on him are untouched; his sex and age band may not change; the bucket he left keeps its `drawn_here` and names him in `refamilied_out`, and the bucket he entered fills one of its orders with a person the town already holds.

**A move is not** a retirement (nobody is un-written, which is T-1459's ruling of 2026-09-20) and a draw (no stranger enters the town, so the population does not move — only what is still OWED does).

## The programme in four numbers

| | |
|---|---:|
| held when the ruling was made | 539 |
| moves T-1556 § 3 named | 265 |
| moves the rule yields | **142** |
| people still held when it is spent | **397** |

The remedy reaches 26% of what it was asked to remedy. The other 74% is not owed to a ticket and is not waiting on a run.

## The four pieces

| piece | owns | settled |
|---|---|---|
| `T-1557` | the ledger and the order book's accounting of a move, with zero moves made | yes |
| `T-1558` | the rule that chooses WHICH held heads move, modelled against the adoption layers | yes |
| `T-1559` | the moves themselves, in bucket-family stages | yes |
| `T-1560` | this report: the counts, the rule, and the owner's ruling behind them | not yet |

## Where it stands

142 move(s) made, 0 outstanding, 397 people held today.

## What it is left holding

397 people stand in 51 of the 51 refused buckets once every move the rule yields has been made. 0 bucket(s) clear completely.

T-1558 measured the ceilings, each loosening one more axis than the one above it: 0 if only the division changed, 15 if the household kind changed too, 15 if the trade could change as well, and 142 under the rule as written. The remainder is not waiting on a run; it is waiting on an order book that wants women and children somewhere else.

| sex | age band | still held |
|---|---|---:|
| female | `under_10` | 70 |
| male | `under_10` | 69 |
| female | `20_29` | 65 |
| male | `10_19` | 50 |
| female | `10_19` | 39 |
| male | `20_29` | 35 |
| female | `30_39` | 29 |
| male | `30_39` | 18 |
| female | `40_49` | 10 |
| male | `40_49` | 6 |
| female | `50_plus` | 4 |
| male | `50_plus` | 2 |

## Where the programme finishes, and what the residue is

The programme is **settled**, and its finish line is the rule's own fixpoint: the programme is settled when T-1558's rule yields no further move, and not when nobody is held. `settled` is arithmetic either way — what the ruling changed is which arithmetic.

> owner, 2026-09-25, answering T-1597 with option (a): "They remain held, recorded as held, and the programme is settled at its fixpoint rather than at zero — the refusals stand as written and the book says so." It is the ruling of 2026-09-24 asked again of the residue that rule could not reach.

**397 people remain held**, in 51 refused bucket(s). What becomes of them is nothing, and that is the ruling: each keeps the card, the id, the seed and the confidence the stage that drew him wrote, counted in a cell the sources have since shown the town did not need that many of. Every one of the buckets goes on naming both its figures (T-1459), docs/LIBERTIES.md L268 is the admission, and docs/RESEARCH/1835_refamily_programme.md is the arithmetic.

| the refusal that holds them | people |
|---|---:|
| `a_documented_reading_shrank_the_order` | 10 |
| `the_re_cut_reached_work_already_drawn` | 387 |

**What would reopen it:** a wider rule. Option (b) — loosening whole-house, sex or age band — was not taken; if it ever is, the rule yields more moves than are spent, this step goes unsettled, and the work-order gate asks for a live owner again.

Read from `data/reconstruction/1835_reconstruction_order_book.json § re_family_ledger.the_programme`.

## What the town converges to

- standing in the layer: 2,865
- still owed now: 15
- still owed when the programme is spent: 15
- converges to now: 2,880
- converges to when the programme is spent: 2,880
- 2,880 is inside the model's 2,371-3,265 and 330 above its 2,550 point, against 330 above it today.

The rule's own projection of 2,738 is NOT used here, and the rule subtracts every move it yields from a standing-and-owed pair that is ALREADY post-move, so once the moves are spent it counts them twice — the T-1563 double count, one file over. Both ends here are computed from the layer's standing persons and what the book still owes; `model_refamily_rule.py` owns the projection and the fix.

## What would move the remainder

- **more_orders_in_the_women_and_children_cells** (T-1532, T-1536, T-1538 (the lodging band) and the book itself) — The binding constraint is room, not willingness: the surplus is 228 people under twenty and 108 adult women, and their cells hold 15 and 0 open slots between them. An order book re-cut that grew those cells — or a lodging ticket that ordered more children into boarding houses — would raise this directly.
- **a_ruling_that_an_adoption_may_be_RE_SEATED** (the business staffing band (T-1189 and its successors)) — 202 of the people in the refused buckets carry an employment seat, a business card or a lodging roll that names a house in their division, and 113 more are refused with a house one of those people is in. If the staffing layer may re-seat an adopted head at an equivalent house in the destination division, the adoption travels and T-1556 § 8 is satisfied by carrying rather than by refusing. That is a change to the staffing model and not to this rule.
- **the_22_seated_households** (T-1199) — 66 people are refused because their roof is already placed. A re-family that also re-seats the roof is a placement act, and the placement policy owns it.
- **and_the_honest_alternative** (T-1560, the programme's report) — What is left standing after the rule is spent is a remainder that NOTHING can move, and T-1459's ruling says it is held rather than clamped. The book will go on naming both numbers per bucket, which is the state the owner's ruling improved on rather than abolished.

## Every refused bucket, and what it is left holding

Each of the buckets below keeps its `held_at` and its `the_re_cut_would_have_ordered` side by side, which is T-1459's ruling of 2026-09-20 and is the state the 2026-09-24 ruling IMPROVED on rather than abolished. docs/LIBERTIES.md L268 is the admission.

| bucket | ticket | held at | the re-cut would have ordered | surplus today | moves outstanding | left holding |
|---|---|---:|---:|---:|---:|---:|
| `persons/male/under_10/south/family/none` | T-1174 | 109 | 64 | 45 | 0 | 45 |
| `persons/female/under_10/south/family/none` | T-1174 | 100 | 57 | 43 | 0 | 43 |
| `persons/female/20_29/south/family/none` | T-1174 | 64 | 35 | 29 | 0 | 29 |
| `persons/male/10_19/south/family/none` | T-1174 | 65 | 39 | 26 | 0 | 26 |
| `persons/female/10_19/south/family/none` | T-1174 | 54 | 33 | 21 | 0 | 21 |
| `persons/male/20_29/south/family/trade` | T-2187 | 52 | 32 | 20 | 0 | 20 |
| `persons/female/under_10/north/family/none` | T-1174 | 41 | 25 | 16 | 0 | 16 |
| `persons/male/under_10/north/family/none` | T-1174 | 44 | 28 | 16 | 0 | 16 |
| `persons/female/20_29/south/family/trade` | T-2187 | 30 | 19 | 11 | 0 | 11 |
| `persons/female/30_39/south/family/none` | T-1174 | 27 | 16 | 11 | 0 | 11 |
| `persons/female/under_10/west/family/none` | T-1174 | 34 | 23 | 11 | 0 | 11 |
| `persons/male/10_19/north/family/none` | T-1174 | 28 | 17 | 11 | 0 | 11 |
| `persons/female/10_19/north/family/none` | T-1174 | 24 | 14 | 10 | 0 | 10 |
| `persons/female/20_29/north/family/none` | T-1174 | 26 | 16 | 10 | 0 | 10 |
| `persons/female/10_19/west/family/none` | T-1174 | 21 | 13 | 8 | 0 | 8 |
| `persons/male/10_19/west/family/none` | T-1174 | 23 | 15 | 8 | 0 | 8 |
| `persons/male/20_29/north/family/trade` | T-2187 | 22 | 14 | 8 | 0 | 8 |
| `persons/male/30_39/south/family/trade` | T-2187 | 27 | 19 | 8 | 0 | 8 |
| `persons/male/under_10/west/family/none` | T-1174 | 34 | 26 | 8 | 0 | 8 |
| `persons/female/20_29/north/family/trade` | T-2187 | 15 | 8 | 7 | 0 | 7 |
| `persons/female/20_29/west/family/none` | T-1174 | 20 | 14 | 6 | 0 | 6 |
| `persons/female/30_39/south/family/trade` | T-2187 | 15 | 9 | 6 | 0 | 6 |
| `persons/male/20_29/west/family/trade` | T-2187 | 18 | 12 | 6 | 0 | 6 |
| `persons/male/30_39/north/family/trade` | T-2187 | 14 | 8 | 6 | 0 | 6 |
| `persons/female/30_39/north/family/none` | T-1174 | 11 | 7 | 4 | 0 | 4 |
| `persons/female/30_39/south/lodging/none` | T-2023 | 9 | 6 | 3 | 0 | 3 |
| `persons/female/30_39/west/family/none` | T-1174 | 9 | 6 | 3 | 0 | 3 |
| `persons/female/40_49/south/family/none` | T-1174 | 9 | 6 | 3 | 0 | 3 |
| `persons/male/10_19/south/lodging/trade` | T-2023 | 7 | 4 | 3 | 0 | 3 |
| `persons/male/30_39/west/family/trade` | T-2187 | 10 | 7 | 3 | 0 | 3 |
| `persons/male/40_49/south/family/trade` | T-2187 | 8 | 5 | 3 | 0 | 3 |
| `persons/female/20_29/west/family/trade` | T-2187 | 9 | 7 | 2 | 0 | 2 |
| `persons/female/30_39/north/family/trade` | T-2187 | 6 | 4 | 2 | 0 | 2 |
| `persons/female/40_49/north/family/trade` | T-2187 | 3 | 1 | 2 | 0 | 2 |
| `persons/female/50_plus/south/family/none` | T-1174 | 6 | 4 | 2 | 0 | 2 |
| `persons/female/40_49/north/family/none` | T-1174 | 4 | 3 | 1 | 0 | 1 |
| `persons/female/40_49/north/lodging/trade` | T-2023 | 1 | 0 | 1 | 0 | 1 |
| `persons/female/40_49/south/family/trade` | T-2187 | 5 | 4 | 1 | 0 | 1 |
| `persons/female/40_49/west/family/trade` | T-2187 | 2 | 1 | 1 | 0 | 1 |
| `persons/female/40_49/west/lodging/trade` | T-2023 | 1 | 0 | 1 | 0 | 1 |
| `persons/female/50_plus/north/family/trade` | T-2187 | 2 | 1 | 1 | 0 | 1 |
| `persons/female/50_plus/west/family/none` | T-1174 | 2 | 1 | 1 | 0 | 1 |
| `persons/male/10_19/north/lodging/trade` | T-2023 | 1 | 0 | 1 | 0 | 1 |
| `persons/male/10_19/west/lodging/trade` | T-2023 | 1 | 0 | 1 | 0 | 1 |
| `persons/male/20_29/south/lodging/none` | T-2023 | 22 | 21 | 1 | 0 | 1 |
| `persons/male/30_39/north/lodging/none` | T-2023 | 6 | 5 | 1 | 0 | 1 |
| `persons/male/40_49/north/family/trade` | T-2187 | 3 | 2 | 1 | 0 | 1 |
| `persons/male/40_49/north/lodging/none` | T-2023 | 2 | 1 | 1 | 0 | 1 |
| `persons/male/40_49/west/family/trade` | T-2187 | 3 | 2 | 1 | 0 | 1 |
| `persons/male/50_plus/south/family/trade` | T-2187 | 3 | 2 | 1 | 0 | 1 |
| `persons/male/50_plus/west/family/trade` | T-2187 | 2 | 1 | 1 | 0 | 1 |
