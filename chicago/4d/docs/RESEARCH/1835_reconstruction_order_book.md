# The 1835 reconstruction order book

> DERIVED from `data/reconstruction/1835_reconstruction_order_book.json`. Regenerate with
> `tools/build_order_book_1835.py --build`; `tools/check.sh` re-derives both. Do not hand-edit.

**T-1166.** Known minus model, per bucket, with the ticket that owns filling it. The town converges to **2,543 people** in **644 households**, working **109 enumerated businesses**, under **668 roofs**.

| | target | known | to reconstruct |
|---|---:|---:|---:|
| Persons | 2,543 | 1,402 | 1,542 |
| Households | 644 | 82 | 564 |
| Businesses (enumerated classes) | 109 | 130 | 7 |
| Roofs | 668 | 419 | 262 |

**2,381 people stand in the layer today** and **299** are still owed after the counters, so the town this book converges to is **2,680** — inside the model's 2,362-3,265. `--build` and `--check` both refuse a remainder that lands outside it.

## What the re-cut found

> T-1463 summed T-1386's presence rulings into `known`, and T-1525 read the parish register into it. These are the things that made measurable, carried in the book so they cannot go stale in a report.


### t 1171 adjudicated

*T-1171 closed 2026-09-18 (PR #1476) having drawn 124 of 556, and the presence rulings landed 2026-09-19 — the day after. Was its 432 real, or an artifact of a quota cut against a town that did not yet hold the 827 ruled-in people?*

Of the 432, the household leg is DISCHARGED: T-1171's household quota was 182 against 124 drawn and the re-cut takes it to its own drawn figure, so it owes 372. The person leg is PART artifact: 374 before, 208 now. The remainder is owed and is not a counting error, so T-1171 REOPENS for it.

**Verdict:** reopen T-1171 for the persons; the households are discharged

### the remainder said out loud

*What does the town converge to if every remaining order is filled?*

2,381 standing plus 299 still owed is 2,680, inside the model's 2,362-3,265. Before the re-cut the same sum was 2,381 + 843 = 3,224, and the book was ordering a replacement for 826 people already in the layer. It is 137 above the model's 2,543 point, and that surplus is the 395 people drawn into 44 buckets past what the re-cut would now order — named in `recut_refusals`, held rather than clamped, and retired or re-familied by T-1196, T-1197 and T-1179 rather than by this book.

### households are counted in two different units

*The model wants 643 households and the layer holds 1,510 records. Are those the same thing?*

Of the 1,375 records the layer holds present, 82 carry a reading about a dwelling and 1,293 do not. The quota is taken against the 82, so it stops reading 0 owed — which was never true and was the symptom that raised this — and starts reading what the town still owes in houses.

### a documented reading shrank an order the town had drawn

*The parish register's 120 documented residents (T-0841) land in buckets the town had already reconstructed strangers into. Where did reading a person the town can name put a bucket's order UNDER what was drawn against it, and by how many people?*

`persons/male/10_19/west/lodging/trade` holds 1 drawn against an order of 0 — over-supplied by 1. That is 1 reconstructed people standing where the sources now name someone else, and it is a different fault from the rest of `recut_refusals`: those are quotas drifting under a draw, this is the town learning it invented a person it did not need. Nothing here is clamped and nothing already drawn moves — T-1459 — so the book keeps ordering the larger figure and names the surplus instead.

**Declined:** RETIRING a reconstructed card is the bucket owner's work and not this book's: a book that deleted people to make its own arithmetic close would be reconstructing backwards. T-1347, which drew the trade band, has closed, so T-1530 is filed for the south-side 20-29 surplus and T-1506 owns the surplus lawyer.

## Where the re-cut was refused

44 buckets would have had their order cut below the people already drawn against them. The owner's ruling of 2026-09-20 refuses that by name rather than clamping it: each is held at what was drawn. The three tickets this paragraph used to hand the surplus to — T-1196, T-1197 and T-1179 — are all closed; the owner's ruling of 2026-09-24 (T-1556) hands it to the re-family programme below, where the held heads move into the buckets the re-cut grew instead of being un-written.

| bucket | ticket | cause | quota it was drawn against | the re-cut would order | drawn | re-familied out | still held |
|---|---|---|---:|---:|---:|---:|---:|
| `persons/female/10_19/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 26 | 15 | 24 | 2 | 9 |
| `persons/female/10_19/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 61 | 33 | 55 | 6 | 22 |
| `persons/female/10_19/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 24 | 13 | 21 | 3 | 8 |
| `persons/female/20_29/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 15 | 8 | 15 | 0 | 7 |
| `persons/female/20_29/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 28 | 16 | 26 | 2 | 10 |
| `persons/female/20_29/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 35 | 19 | 30 | 5 | 11 |
| `persons/female/20_29/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 67 | 36 | 64 | 2 | 28 |
| `persons/female/20_29/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 13 | 7 | 9 | 4 | 2 |
| `persons/female/20_29/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 25 | 14 | 20 | 5 | 6 |
| `persons/female/30_39/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 6 | 4 | 6 | 0 | 2 |
| `persons/female/30_39/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 13 | 7 | 11 | 2 | 4 |
| `persons/female/30_39/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 16 | 9 | 16 | 0 | 7 |
| `persons/female/30_39/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 31 | 16 | 27 | 4 | 11 |
| `persons/female/30_39/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 7 | 4 | 5 | 1 | 1 |
| `persons/female/30_39/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 12 | 6 | 9 | 3 | 3 |
| `persons/female/40_49/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 3 | 1 | 3 | 0 | 2 |
| `persons/female/40_49/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 5 | 3 | 4 | 1 | 1 |
| `persons/female/40_49/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 6 | 3 | 5 | 1 | 2 |
| `persons/female/40_49/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 11 | 6 | 9 | 2 | 3 |
| `persons/female/40_49/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 3 | 1 | 2 | 1 | 1 |
| `persons/female/50_plus/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 | 0 | 1 |
| `persons/female/50_plus/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 8 | 4 | 6 | 2 | 2 |
| `persons/female/50_plus/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 | 0 | 1 |
| `persons/female/under_10/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 46 | 26 | 41 | 4 | 15 |
| `persons/female/under_10/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 107 | 57 | 100 | 7 | 43 |
| `persons/female/under_10/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 40 | 23 | 34 | 6 | 11 |
| `persons/male/10_19/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 30 | 17 | 28 | 2 | 11 |
| `persons/male/10_19/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 71 | 39 | 65 | 6 | 26 |
| `persons/male/10_19/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 27 | 15 | 23 | 3 | 8 |
| `persons/male/10_19/west/lodging/trade` | T-1532 | a_documented_reading_shrank_the_order | 1 | 0 | 1 | 0 | 1 |
| `persons/male/20_29/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 25 | 14 | 22 | 3 | 8 |
| `persons/male/20_29/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 59 | 32 | 52 | 8 | 20 |
| `persons/male/20_29/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 23 | 13 | 20 | 3 | 7 |
| `persons/male/30_39/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 15 | 8 | 15 | 0 | 7 |
| `persons/male/30_39/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 35 | 19 | 32 | 3 | 13 |
| `persons/male/30_39/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 13 | 7 | 11 | 2 | 4 |
| `persons/male/40_49/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 4 | 2 | 3 | 1 | 1 |
| `persons/male/40_49/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 10 | 5 | 9 | 1 | 4 |
| `persons/male/40_49/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 3 | 2 | 3 | 0 | 1 |
| `persons/male/50_plus/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 5 | 2 | 3 | 2 | 1 |
| `persons/male/50_plus/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 | 0 | 1 |
| `persons/male/under_10/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 51 | 28 | 44 | 7 | 16 |
| `persons/male/under_10/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 120 | 64 | 109 | 10 | 45 |
| `persons/male/under_10/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 46 | 26 | 34 | 9 | 8 |

## The re-family ledger

the owner's ruling of 2026-09-24 on T-1530, carried in T-1556: the surplus the re-cut holds is RE-FAMILIED rather than retired — the heads move into the buckets the re-cut grew instead of being un-written.

**A move is** one reconstructed person counted in a different cell of the same ladder. His card, his id, his residence_grade and every citation on him are untouched; his sex and age band may not change; the bucket he left keeps its `drawn_here` and names him in `refamilied_out`, and the bucket he entered fills one of its orders with a person the town already holds.

**A move is not** a retirement (nobody is un-written, which is T-1459's ruling of 2026-09-20) and a draw (no stranger enters the town, so the population does not move — only what is still OWED does).

395 held head(s) stand across 44 refused bucket(s), and 299 slot(s) of order stand open elsewhere in the persons ladder. A held head moved into an open order fills that order without drawing a stranger, so each move takes one person off what is still owed rather than out of the town.

**129 move(s) have been made**, carrying 0 adoption(s) out of 39 bucket(s) and into 41. The book is owed 299 people now, and would be owed 0 if every held head moved. The model's point is what decides HOW MANY move, and that number is T-1559's to spend; this book states the two ends of the range.

Which heads move is T-1558's (settled): T-1558 modelled it against the adoption layers and published the cost ladder there, with the tier of every held person and the ceilings the axes impose. `refamily_shape` above refuses a move whose `rule` is not one of the movable rungs, so the naming T-1557 required is now checked rather than trusted. The moves themselves are T-1559's.

| person | out of | into | order filled | rule | ticket | adoptions |
|---|---|---|---|---|---|---:|
| `rc_newell_seth` | `persons/male/50_plus/south/family/trade` | `persons/male/50_plus/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_leland_harvey` | `persons/male/50_plus/south/family/trade` | `persons/male/50_plus/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_bertrand_pierre` | `persons/male/50_plus/north/family/trade` | `persons/male/50_plus/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_newell_hiram` | `persons/male/40_49/south/family/trade` | `persons/male/40_49/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_nash_eli` | `persons/male/40_49/north/family/trade` | `persons/male/40_49/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_sheldon_willard` | `persons/male/30_39/west/family/trade` | `persons/male/30_39/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_thayer_harvey` | `persons/male/30_39/west/family/trade` | `persons/male/30_39/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_stiles_nathaniel` | `persons/male/30_39/south/family/trade` | `persons/male/30_39/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_stiles_alvah` | `persons/male/30_39/south/family/trade` | `persons/male/30_39/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_robillard_michel` | `persons/male/30_39/south/family/trade` | `persons/male/30_39/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_gallagher_catherine` | `persons/female/50_plus/west/family/trade` | `persons/female/50_plus/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_eastman_clarissa` | `persons/female/50_plus/south/family/trade` | `persons/female/50_plus/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_duffy_bridget` | `persons/female/50_plus/south/family/trade` | `persons/female/50_plus/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_reilly_johanna` | `persons/female/40_49/west/family/trade` | `persons/female/40_49/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_kelly_catherine` | `persons/female/40_49/south/family/trade` | `persons/female/40_49/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_sullivan_johanna` | `persons/female/30_39/west/family/trade` | `persons/female/30_39/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_newell_amanda` | `persons/female/20_29/west/family/trade` | `persons/female/20_29/north/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_eastman_lucy` | `persons/female/20_29/west/family/trade` | `persons/female/20_29/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_shea_alice` | `persons/female/20_29/west/family/trade` | `persons/female/20_29/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth` | `persons/female/30_39/west/family/none` | `persons/female/30_39/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_1` | `persons/male/under_10/west/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_2` | `persons/male/10_19/west/family/none` | `persons/male/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_3` | `persons/male/under_10/west/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_4` | `persons/male/10_19/west/family/none` | `persons/male/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_5` | `persons/male/under_10/west/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_6` | `persons/male/under_10/west/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_ruth_7` | `persons/female/10_19/west/family/none` | `persons/female/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_lucy` | `persons/female/20_29/south/family/none` | `persons/female/20_29/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_lucy_1` | `persons/male/under_10/south/family/none` | `persons/male/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_lucy_2` | `persons/male/10_19/south/family/none` | `persons/male/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_lucy_3` | `persons/male/under_10/south/family/none` | `persons/male/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_lucy_4` | `persons/male/under_10/south/family/none` | `persons/male/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_lucy_5` | `persons/female/10_19/south/family/none` | `persons/female/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_emily` | `persons/female/30_39/west/family/none` | `persons/female/30_39/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_eliza` | `persons/female/30_39/north/family/none` | `persons/female/30_39/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_eliza_1` | `persons/male/under_10/north/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_eliza_2` | `persons/male/under_10/north/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_eliza_3` | `persons/female/under_10/north/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_eliza_4` | `persons/female/10_19/north/family/none` | `persons/female/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_woodruff_eliza_5` | `persons/male/under_10/north/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_sophronia` | `persons/female/20_29/west/family/none` | `persons/female/20_29/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_sophronia_1` | `persons/male/under_10/west/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_sophronia_2` | `persons/female/10_19/west/family/none` | `persons/female/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_sophronia_3` | `persons/female/under_10/west/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_sophronia_4` | `persons/female/under_10/west/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_sophronia_5` | `persons/male/under_10/west/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_harriet` | `persons/female/20_29/north/family/none` | `persons/female/20_29/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_harriet_1` | `persons/female/under_10/north/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_harriet_2` | `persons/female/10_19/north/family/none` | `persons/female/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_whitcomb_sarah` | `persons/female/40_49/south/family/none` | `persons/female/40_49/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_whitcomb_sarah_1` | `persons/male/under_10/south/family/none` | `persons/male/under_10/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_whitcomb_sarah_2` | `persons/male/10_19/south/family/none` | `persons/male/10_19/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_thayer_sarah` | `persons/female/30_39/south/family/none` | `persons/female/30_39/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_thayer_sarah_1` | `persons/male/under_10/south/family/none` | `persons/male/under_10/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_thayer_sarah_2` | `persons/male/10_19/south/family/none` | `persons/male/10_19/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_stebbins_clarissa` | `persons/female/30_39/south/family/none` | `persons/female/30_39/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_stebbins_clarissa_1` | `persons/female/under_10/south/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_stebbins_clarissa_2` | `persons/female/under_10/south/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_stebbins_clarissa_3` | `persons/male/under_10/south/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_pothier_victoire` | `persons/female/20_29/west/family/none` | `persons/female/20_29/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_pothier_victoire_1` | `persons/male/under_10/west/family/none` | `persons/male/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_pothier_victoire_2` | `persons/male/under_10/west/family/none` | `persons/male/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_pothier_victoire_3` | `persons/male/under_10/west/family/none` | `persons/male/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_pothier_victoire_4` | `persons/male/10_19/west/family/none` | `persons/male/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_pothier_victoire_5` | `persons/female/under_10/west/family/none` | `persons/female/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_newell_hannah` | `persons/female/20_29/west/family/none` | `persons/female/20_29/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_nash_martha` | `persons/female/20_29/north/family/none` | `persons/female/20_29/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_nash_martha_1` | `persons/female/under_10/north/family/none` | `persons/female/under_10/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_nash_martha_2` | `persons/male/under_10/north/family/none` | `persons/male/under_10/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_mahoney_catherine` | `persons/female/40_49/west/family/none` | `persons/female/40_49/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_mahoney_catherine_1` | `persons/female/under_10/west/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_mahoney_catherine_2` | `persons/female/under_10/west/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_kelly_honora` | `persons/female/40_49/north/family/none` | `persons/female/40_49/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_kelly_honora_1` | `persons/male/under_10/north/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_kelly_honora_2` | `persons/male/under_10/north/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_fisk_esther` | `persons/female/20_29/west/family/none` | `persons/female/20_29/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_fisk_esther_1` | `persons/female/under_10/west/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_fairbanks_amanda` | `persons/female/40_49/south/family/none` | `persons/female/40_49/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_fairbanks_amanda_1` | `persons/male/under_10/south/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_fairbanks_amanda_2` | `persons/male/under_10/south/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_fairbanks_amanda_3` | `persons/male/under_10/south/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_dufresne_therese` | `persons/female/30_39/north/family/none` | `persons/female/30_39/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_dufresne_therese_1` | `persons/male/under_10/north/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_barnes_nancy` | `persons/female/50_plus/south/family/none` | `persons/female/50_plus/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_barnes_nancy_1` | `persons/female/under_10/south/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_barnes_nancy_2` | `persons/male/under_10/south/family/none` | `persons/male/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_barnes_clarissa` | `persons/female/20_29/west/family/none` | `persons/female/20_29/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_nichols_eli` | `persons/male/20_29/west/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_thayer_james` | `persons/male/20_29/west/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_nichols_samuel` | `persons/male/20_29/west/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_gallagher_martin` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_tuttle_rufus` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_doyle_alice` | `persons/female/20_29/west/family/trade` | `persons/female/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_quinn_margaret` | `persons/female/20_29/south/family/trade` | `persons/female/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_walsh_johanna` | `persons/female/30_39/south/family/none` | `persons/female/30_39/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_walsh_johanna_1` | `persons/female/10_19/south/family/none` | `persons/female/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_walsh_johanna_2` | `persons/female/10_19/south/family/none` | `persons/female/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_walsh_johanna_3` | `persons/male/10_19/south/family/none` | `persons/male/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_walsh_johanna_4` | `persons/female/under_10/south/family/none` | `persons/female/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_walsh_johanna_5` | `persons/female/under_10/south/family/none` | `persons/female/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_shea_bridget` | `persons/female/30_39/west/family/none` | `persons/female/30_39/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_shea_bridget_1` | `persons/female/10_19/west/family/none` | `persons/female/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_ryan_ellen` | `persons/female/50_plus/south/family/none` | `persons/female/50_plus/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_ryan_ellen_1` | `persons/female/under_10/south/family/none` | `persons/female/under_10/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_ryan_ellen_2` | `persons/male/10_19/south/family/none` | `persons/male/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_ryan_ellen_3` | `persons/male/10_19/south/family/none` | `persons/male/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_duffy_margaret` | `persons/female/30_39/south/family/none` | `persons/female/30_39/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_duffy_margaret_1` | `persons/female/10_19/south/family/none` | `persons/female/10_19/west/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_parmelee_silas` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_tuttle_benjamin` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_chapin_ezra` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_bourassa_hyacinthe` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_nichols_willard` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_parmelee_alvah` | `persons/male/20_29/south/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_vieau_louis` | `persons/male/20_29/north/family/trade` | `persons/male/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_walsh_edward` | `persons/male/20_29/north/family/trade` | `persons/male/20_29/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_nichols_rufus` | `persons/male/20_29/north/family/trade` | `persons/male/20_29/west/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_lynch_catherine` | `persons/female/20_29/south/family/trade` | `persons/female/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_parmelee_sarah` | `persons/female/20_29/south/family/trade` | `persons/female/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_mccarthy_margaret` | `persons/female/20_29/south/family/trade` | `persons/female/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_hastings_amanda` | `persons/female/20_29/south/family/trade` | `persons/female/20_29/south/lodging/trade` |  | C1 | T-1556 | 0 |
| `rc_wilcox_martha` | `persons/female/20_29/south/family/none` | `persons/female/20_29/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_martha_1` | `persons/female/10_19/south/family/none` | `persons/female/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_martha_2` | `persons/female/10_19/south/family/none` | `persons/female/10_19/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_wilcox_martha_3` | `persons/female/under_10/south/family/none` | `persons/female/under_10/south/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_gilbert_abigail` | `persons/female/50_plus/north/family/none` | `persons/female/50_plus/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_gilbert_abigail_1` | `persons/male/10_19/north/family/none` | `persons/male/10_19/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_gilbert_abigail_2` | `persons/male/10_19/north/family/none` | `persons/male/10_19/north/lodging/none` |  | C1 | T-1556 | 0 |
| `rc_gilbert_abigail_3` | `persons/female/under_10/north/family/none` | `persons/female/under_10/north/lodging/none` |  | C1 | T-1556 | 0 |

## The trade cut, re-cut on its remainder

> **T-1459**, on the owner's ruling of 2026-09-20: take option 1 — re-cut the book — and re-cut **just the remainder**.

### The age of a working person is read, not assumed

137 people in the resident layer carry an occupation a source records. 10 of them are in the book's 10_19 band — and every one of those is labelled 15-19 by the layer, so the record reaches below twenty and stops at fifteen. Per unit of the 1840 pyramid's population that is 0.2919 of the adult rate, which is the weight the band enters the cut at. The band under ten has no worker in the record at all and is left shut.

| band | workers the sources record | share of the 1840 pyramid | weight in the trade cut |
|---|---:|---:|---:|
| `under_10` | 0 | 0.2662 | 0.0000 |
| `10_19` | 10 | 0.1559 | 0.2919 |
| `20_29` | 61 | 0.3202 | 1.0000 |
| `30_39` | 50 | 0.1737 | 1.0000 |
| `40_49` | 10 | 0.0547 | 1.0000 |
| `50_plus` | 6 | 0.0292 | 1.0000 |

Read from data/residents/households/*.json — every person whose occupation is attested or inferred, which is to say read from a source. 0 person(s) the layer grades `reconstructed` were skipped: a stage's own draw is not evidence for the cut that produced it.

### The sex of the remainder is NOT re-cut

130 of the 137 are men. That is not a licence to cut the trade remainder male: the sources that print an occupation — notices, poll lists, the trade census, the directories — print PROPRIETORS and heads of household, and a record of who advertised is not a record of who worked. The town model's own occupations section says the same thing from the other side: the 1840 schedule's seven columns have no row for domestic service, 'which a port with this adult sex ratio certainly had', and the trade split understates household labour 'by an amount this model cannot bound'. Both arguments point one way and neither bounds a number, so the SEX of the trade remainder is NOT re-cut. The book keeps the population's own split, and the hands a shop wants that only a man can fill stand short with the reason said out loud.

### What moved

The re-cut wanted **36** trade slots in the bands it reopened. The younger bands held **20** undrawn and the adult cells it would draw from held **9**, so **9** moved and the book's employed total did not change. Every cell below is a `lodging` cell on both sides, because every `family` cell of the reopened band is drawn out: the working youths this book still orders are BOARDERS — an apprentice or a shop hand sleeping where he works — which is a consequence of what is already drawn and not a claim about 1835.

| into | slots |
|---|---:|
| `persons/female/10_19/north/lodging` | 1 |
| `persons/female/10_19/south/lodging` | 3 |
| `persons/male/10_19/north/lodging` | 1 |
| `persons/male/10_19/south/lodging` | 4 |

| out of | slots |
|---|---:|
| `persons/female/30_39/south/lodging` | 3 |
| `persons/female/30_39/west/lodging` | 1 |
| `persons/female/40_49/south/lodging` | 1 |
| `persons/male/20_29/north/lodging` | 4 |

**27 cell(s) could not take or give their share**, because the people who would have filled them are already drawn. Each is named with both numbers; none was clamped in silence, and no person already drawn moved.

| cell | the re-cut wanted | the remainder could pay | already drawn | by |
|---|---:|---:|---:|---|
| `persons/female/10_19/north/family` (into) | 3 | 0 | 24 | T-1174 |
| `persons/female/10_19/south/family` (into) | 7 | 0 | 55 | T-1174 |
| `persons/female/10_19/west/family` (into) | 3 | 0 | 21 | T-1174 |
| `persons/female/10_19/west/lodging` (into) | 1 | 0 | 5 | T-1536 |
| `persons/male/10_19/north/family` (into) | 3 | 0 | 28 | T-1174 |
| `persons/male/10_19/south/family` (into) | 8 | 0 | 65 | T-1174 |
| `persons/male/10_19/west/family` (into) | 3 | 0 | 23 | T-1174 |
| `persons/male/10_19/west/lodging` (into) | 1 | 0 | 5 | T-1536 |
| `persons/female/20_29/north/family` (out of) | 1 | 0 | 15 | T-1347 |
| `persons/female/20_29/south/family` (out of) | 3 | 0 | 30 | T-1347 |
| `persons/female/20_29/south/lodging` (out of) | 1 | 0 | 6 | T-1532 |
| `persons/female/20_29/west/family` (out of) | 1 | 0 | 9 | T-1347 |
| `persons/female/30_39/south/family` (out of) | 2 | 0 | 16 | T-1347 |
| `persons/female/30_39/west/family` (out of) | 1 | 0 | 5 | T-1347 |
| `persons/female/40_49/west/family` (out of) | 1 | 0 | 2 | T-1347 |
| `persons/female/50_plus/south/family` (out of) | 1 | 0 | 2 | T-1347 |
| `persons/male/20_29/north/family` (out of) | 3 | 0 | 22 | T-1347 |
| `persons/male/20_29/south/family` (out of) | 5 | 0 | 52 | T-1347 |
| `persons/male/20_29/south/lodging` (out of) | 2 | 0 | 11 | T-1532 |
| `persons/male/20_29/west/family` (out of) | 2 | 0 | 20 | T-1347 |
| `persons/male/20_29/west/lodging` (out of) | 1 | 0 | 3 | T-1532 |
| `persons/male/30_39/north/family` (out of) | 1 | 0 | 15 | T-1347 |
| `persons/male/30_39/south/family` (out of) | 3 | 0 | 32 | T-1347 |
| `persons/male/30_39/south/lodging` (out of) | 1 | 0 | 1 | T-1532 |
| `persons/male/30_39/west/family` (out of) | 1 | 0 | 11 | T-1347 |
| `persons/male/40_49/south/family` (out of) | 1 | 0 | 9 | T-1347 |
| `persons/male/50_plus/south/family` (out of) | 1 | 0 | 3 | T-1347 |

### Who has already spent against this book

The re-cut's one forbidden move is to pull a quota out from under a stage that has already drawn on it. These are the stages that have, so a reader can tell the settled parts of the book from the open ones:

| ticket | persons drawn | buckets |
|---|---:|---:|
| T-1174 | 680 | 27 |
| T-1347 | 308 | 24 |
| T-1171 | 295 | 19 |
| T-1371 | 85 | 29 |
| T-1533 | 15 | 3 |
| T-1184 | 2 | 1 |
| T-1185 | 2 | 2 |
| T-1531 | 2 | 2 |
| T-1418 | 1 | 1 |


## The rules this book adds

- **point from range** — Where the town model gives a point the book takes it; where it gives only a range the book takes the MIDPOINT, rounded half up, and carries the range beside it. A quota cannot be a range.
- **unresolved known** — A named person or household the layer cannot place on an axis is subtracted PRO RATA across that axis's cells, so the book never orders a replacement for somebody already standing in the town.
- **presence is the test** — A household is known when the index records it `present` on the scene date, or when T-1386's presence rulings rule it present. The 820 `uncertain` households hold 827 people who stand in the layer, so counting them unknown ordered a replacement for each of them (T-1463). The two evidenced absences stay out; the roster stays a licence, not a quota, so counting these once orders nobody twice.
- **the re cut does not reach work already done** — Summing the rulings into `known` shrinks quotas people have already been drawn against. No bucket's order falls below its own `filled`: the re-cut is REFUSED there by name, with both numbers, in `recut_refusals` — never clamped in silence (the owner's ruling of 2026-09-20).
- **the fort is read not apportioned** — The garrison and its households carry a null target; T-1176 reads the return and the civilian quota is re-cut at the next --build.
- **rounding** — Largest remainder throughout, ties broken on the bucket key, so two builds on one set of inputs are byte-identical.
- **real names first** — The roster (T-1159) offers every name the corpus printed and withheld. It is a licence on WHICH name a filler uses and never a quota, so it is counted against its ticket rather than smeared across cells that cannot hold it.

## Real names before invented ones

The roster offers 1,787 names the corpus printed and this project withheld. Each class is a licence, not a quota:

| class | offered | ticket |
|---|---:|---|
| `R1_in_window_uncertain` | 902 | T-1172 |
| `R2_in_window_single_source` | 207 | T-1172 |
| `R3_1834_return_or_muster` | 28 | T-1172 |
| `R4_surname_only_census` | 436 | T-1170 |
| `R5_later_only_backprojectable` | 53 | T-1172 |
| `R6_native_metis_black` | 161 | T-1177 |

## Where the ordered households are standing

Two committed passes have offered every banded household ground: the plat first, then the ground the plat does not draw. This is what they seated, against the roofs the town already has. A seat is an ADOPTION — a household put under a roof that already stands — or a SLOT, a request the build tickets fulfil. Neither pass raises a roof, and nothing here is a claim about 1835: it is the reconstruction's own progress, read off two derived files and joined.

- offered ground: 1,480
- seated: 178 — 172 by adopting a roof that already stands, 6 by asking for one
- still on no ground at all: 1,302
- of the 419 roofs the town already has, 172 now carry a reconstructed household

| pass | ticket | offered | seated | adopted | slots | handed on |
|---|---|---:|---:|---:|---:|---:|
| The committed plat | T-1613 | 1,480 | 106 | 100 | 6 | 1,374 |
| The ground the plat does not draw | T-1614 | 1,374 | 72 | 72 | 0 | 1,302 |

6 slot(s) on 3 block(s) — blk_south_water_dearborn, blk_south_water_franklin, blk_south_water_wells. A slot is headroom the block's own committed plan still holds, so the recipe that deals that block is where it is spent.

| household | block | lot | family | clause |
|---|---|---|---|---|
| `hh_ashbaugh_fre` | `blk_south_water_dearborn` | `blk_south_water_dearborn#07` | D7 | `merchant_and_professional_dwellings` |
| `hh_aspam_antoine` | `blk_south_water_dearborn` | `blk_south_water_dearborn#07` | H1 | `merchant_and_professional_dwellings` |
| `hh_brown_lemuel` | `blk_south_water_franklin` | `blk_south_water_franklin#04` | D3 | `tradesman_dwellings` |
| `hh_bryant_j_r_m` | `blk_south_water_franklin` | `blk_south_water_franklin#04` | D4 | `tradesman_dwellings` |
| `hh_burbee_jonathan` | `blk_south_water_wells` | `blk_south_water_wells#01` | D5 | `tradesman_dwellings` |
| `hh_burk_james` | `blk_south_water_wells` | `blk_south_water_wells#01` | D6 | `tradesman_dwellings` |

1,302 of the 1,480 banded households are still on no ground at all. The reasons are written row by row in both files' `owed`, and the clause each one waits on is carried there rather than summarised away.

## Persons

Who the town still has to be given, by sex, age, division, household and trade.

- `town_target`: 2,543
- `town_target_basis`: the model's own point within 2,362-3,265
- `town_target_range`: 2362, 3265
- `employed_target`: 507
- `employed_basis`: the midpoint of the model's 425-588, rounded half up
- `lodging_share`: 0.26
- `lodging_share_range`: 0.143, 0.377

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `persons/female/10_19/north/family/none` | 32 | 17 | 24 | 24 | T-1174 |
| `persons/female/10_19/north/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/female/10_19/north/lodging/none` | 10 | 6 | 4 | 1 | T-1536 |
| `persons/female/10_19/south/family/none` | 76 | 43 | 55 | 55 | T-1174 |
| `persons/female/10_19/south/lodging/trade` | 3 | 0 | 3 | 0 | T-1532 |
| `persons/female/10_19/south/lodging/none` | 24 | 15 | 9 | 7 | T-1536 |
| `persons/female/10_19/west/family/none` | 28 | 15 | 21 | 21 | T-1174 |
| `persons/female/10_19/west/lodging/none` | 10 | 5 | 5 | 5 | T-1536 |
| `persons/female/20_29/north/family/trade` | 18 | 10 | 15 | 15 | T-1347 |
| `persons/female/20_29/north/family/none` | 34 | 18 | 26 | 26 | T-1174 |
| `persons/female/20_29/north/lodging/trade` | 6 | 3 | 3 | 3 | T-1532 |
| `persons/female/20_29/north/lodging/none` | 12 | 7 | 5 | 5 | T-1538 |
| `persons/female/20_29/south/family/trade` | 43 | 24 | 30 | 30 | T-1347 |
| `persons/female/20_29/south/family/none` | 82 | 46 | 64 | 64 | T-1174 |
| `persons/female/20_29/south/lodging/trade` | 15 | 9 | 6 | 6 | T-1532 |
| `persons/female/20_29/south/lodging/none` | 29 | 16 | 13 | 13 | T-1538 |
| `persons/female/20_29/west/family/trade` | 16 | 9 | 9 | 9 | T-1347 |
| `persons/female/20_29/west/family/none` | 30 | 16 | 20 | 20 | T-1174 |
| `persons/female/20_29/west/lodging/trade` | 5 | 2 | 3 | 3 | T-1532 |
| `persons/female/20_29/west/lodging/none` | 11 | 6 | 5 | 5 | T-1538 |
| `persons/female/30_39/north/family/trade` | 8 | 4 | 6 | 6 | T-1347 |
| `persons/female/30_39/north/family/none` | 16 | 9 | 11 | 11 | T-1174 |
| `persons/female/30_39/north/lodging/trade` | 3 | 2 | 1 | 1 | T-1532 |
| `persons/female/30_39/north/lodging/none` | 5 | 2 | 3 | 3 | T-1538 |
| `persons/female/30_39/south/family/trade` | 20 | 11 | 16 | 16 | T-1347 |
| `persons/female/30_39/south/family/none` | 38 | 22 | 27 | 27 | T-1174 |
| `persons/female/30_39/south/lodging/trade` | 4 | 4 | 0 | 0 | T-1532 |
| `persons/female/30_39/south/lodging/none` | 16 | 7 | 9 | 9 | T-1538 |
| `persons/female/30_39/west/family/trade` | 8 | 4 | 5 | 5 | T-1347 |
| `persons/female/30_39/west/family/none` | 14 | 8 | 9 | 9 | T-1174 |
| `persons/female/30_39/west/lodging/trade` | 2 | 2 | 0 | 0 | T-1532 |
| `persons/female/30_39/west/lodging/none` | 6 | 2 | 4 | 4 | T-1538 |
| `persons/female/40_49/north/family/trade` | 3 | 2 | 3 | 3 | T-1347 |
| `persons/female/40_49/north/family/none` | 6 | 3 | 4 | 4 | T-1174 |
| `persons/female/40_49/north/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/female/40_49/north/lodging/none` | 2 | 1 | 1 | 1 | T-1538 |
| `persons/female/40_49/south/family/trade` | 7 | 4 | 5 | 5 | T-1347 |
| `persons/female/40_49/south/family/none` | 14 | 8 | 9 | 9 | T-1174 |
| `persons/female/40_49/south/lodging/trade` | 2 | 2 | 0 | 0 | T-1532 |
| `persons/female/40_49/south/lodging/none` | 6 | 2 | 4 | 4 | T-1538 |
| `persons/female/40_49/west/family/trade` | 3 | 2 | 2 | 2 | T-1347 |
| `persons/female/40_49/west/family/none` | 5 | 2 | 3 | 3 | T-1174 |
| `persons/female/40_49/west/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/female/40_49/west/lodging/none` | 2 | 1 | 1 | 0 | T-1538 |
| `persons/female/50_plus/north/family/trade` | 2 | 1 | 2 | 2 | T-1347 |
| `persons/female/50_plus/north/family/none` | 4 | 2 | 2 | 2 | T-1174 |
| `persons/female/50_plus/north/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/female/50_plus/north/lodging/none` | 1 | 0 | 1 | 1 | T-1538 |
| `persons/female/50_plus/south/family/trade` | 5 | 3 | 2 | 2 | T-1347 |
| `persons/female/50_plus/south/family/none` | 9 | 5 | 6 | 6 | T-1174 |
| `persons/female/50_plus/south/lodging/trade` | 2 | 1 | 1 | 1 | T-1532 |
| `persons/female/50_plus/south/lodging/none` | 3 | 2 | 1 | 1 | T-1538 |
| `persons/female/50_plus/west/family/trade` | 2 | 1 | 1 | 1 | T-1347 |
| `persons/female/50_plus/west/family/none` | 3 | 2 | 2 | 2 | T-1174 |
| `persons/female/50_plus/west/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/female/50_plus/west/lodging/none` | 1 | 0 | 1 | 1 | T-1538 |
| `persons/female/under_10/north/family/none` | 55 | 29 | 41 | 41 | T-1174 |
| `persons/female/under_10/north/lodging/none` | 19 | 11 | 8 | 7 | T-1536 |
| `persons/female/under_10/south/family/none` | 132 | 75 | 100 | 100 | T-1174 |
| `persons/female/under_10/south/lodging/none` | 46 | 26 | 20 | 11 | T-1536 |
| `persons/female/under_10/west/family/none` | 49 | 26 | 34 | 34 | T-1174 |
| `persons/female/under_10/west/lodging/none` | 17 | 9 | 8 | 4 | T-1536 |
| `persons/male/10_19/north/family/none` | 37 | 20 | 28 | 28 | T-1174 |
| `persons/male/10_19/north/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/male/10_19/north/lodging/none` | 12 | 7 | 5 | 5 | T-1536 |
| `persons/male/10_19/south/family/none` | 88 | 49 | 65 | 65 | T-1174 |
| `persons/male/10_19/south/lodging/trade` | 4 | 0 | 4 | 0 | T-1532 |
| `persons/male/10_19/south/lodging/none` | 27 | 18 | 9 | 3 | T-1536 |
| `persons/male/10_19/west/family/none` | 33 | 18 | 23 | 23 | T-1174 |
| `persons/male/10_19/west/lodging/trade` | 0 | 0 | 1 | 1 | T-1532 |
| `persons/male/10_19/west/lodging/none` | 11 | 6 | 5 | 5 | T-1536 |
| `persons/male/20_29/north/family/trade` | 31 | 17 | 22 | 22 | T-1347 |
| `persons/male/20_29/north/family/none` | 58 | 31 | 27 | 0 | T-1171 |
| `persons/male/20_29/north/lodging/trade` | 7 | 6 | 1 | 1 | T-1532 |
| `persons/male/20_29/north/lodging/none` | 24 | 11 | 13 | 6 | T-1538 |
| `persons/male/20_29/south/family/trade` | 73 | 41 | 52 | 52 | T-1347 |
| `persons/male/20_29/south/family/none` | 140 | 79 | 61 | 0 | T-1171 |
| `persons/male/20_29/south/lodging/trade` | 26 | 15 | 11 | 11 | T-1532 |
| `persons/male/20_29/south/lodging/none` | 49 | 27 | 22 | 14 | T-1538 |
| `persons/male/20_29/west/family/trade` | 27 | 14 | 20 | 20 | T-1347 |
| `persons/male/20_29/west/family/none` | 52 | 27 | 25 | 0 | T-1171 |
| `persons/male/20_29/west/lodging/trade` | 10 | 5 | 5 | 3 | T-1532 |
| `persons/male/20_29/west/lodging/none` | 18 | 10 | 8 | 3 | T-1538 |
| `persons/male/30_39/north/family/trade` | 18 | 10 | 15 | 15 | T-1347 |
| `persons/male/30_39/north/family/none` | 34 | 18 | 16 | 0 | T-1171 |
| `persons/male/30_39/north/lodging/trade` | 6 | 3 | 3 | 3 | T-1532 |
| `persons/male/30_39/north/lodging/none` | 12 | 6 | 6 | 4 | T-1538 |
| `persons/male/30_39/south/family/trade` | 43 | 24 | 32 | 32 | T-1347 |
| `persons/male/30_39/south/family/none` | 82 | 46 | 36 | 0 | T-1171 |
| `persons/male/30_39/south/lodging/trade` | 15 | 9 | 6 | 1 | T-1532 |
| `persons/male/30_39/south/lodging/none` | 29 | 16 | 13 | 7 | T-1538 |
| `persons/male/30_39/west/family/trade` | 16 | 9 | 11 | 11 | T-1347 |
| `persons/male/30_39/west/family/none` | 30 | 16 | 14 | 0 | T-1171 |
| `persons/male/30_39/west/lodging/trade` | 5 | 2 | 3 | 1 | T-1532 |
| `persons/male/30_39/west/lodging/none` | 11 | 6 | 5 | 2 | T-1538 |
| `persons/male/40_49/north/family/trade` | 5 | 3 | 3 | 3 | T-1347 |
| `persons/male/40_49/north/family/none` | 10 | 5 | 5 | 0 | T-1171 |
| `persons/male/40_49/north/lodging/trade` | 2 | 1 | 1 | 1 | T-1532 |
| `persons/male/40_49/north/lodging/none` | 3 | 1 | 2 | 0 | T-1538 |
| `persons/male/40_49/south/family/trade` | 12 | 7 | 9 | 9 | T-1347 |
| `persons/male/40_49/south/family/none` | 24 | 13 | 11 | 0 | T-1171 |
| `persons/male/40_49/south/lodging/trade` | 4 | 2 | 2 | 1 | T-1532 |
| `persons/male/40_49/south/lodging/none` | 9 | 6 | 3 | 0 | T-1538 |
| `persons/male/40_49/west/family/trade` | 4 | 2 | 3 | 3 | T-1347 |
| `persons/male/40_49/west/family/none` | 9 | 5 | 4 | 0 | T-1171 |
| `persons/male/40_49/west/lodging/trade` | 2 | 1 | 1 | 0 | T-1532 |
| `persons/male/40_49/west/lodging/none` | 3 | 1 | 2 | 0 | T-1538 |
| `persons/male/50_plus/north/family/trade` | 2 | 1 | 1 | 1 | T-1347 |
| `persons/male/50_plus/north/family/none` | 5 | 3 | 2 | 0 | T-1171 |
| `persons/male/50_plus/north/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/male/50_plus/north/lodging/none` | 1 | 0 | 1 | 0 | T-1538 |
| `persons/male/50_plus/south/family/trade` | 6 | 4 | 3 | 3 | T-1347 |
| `persons/male/50_plus/south/family/none` | 11 | 6 | 5 | 0 | T-1171 |
| `persons/male/50_plus/south/lodging/trade` | 2 | 1 | 1 | 1 | T-1532 |
| `persons/male/50_plus/south/lodging/none` | 4 | 2 | 2 | 0 | T-1538 |
| `persons/male/50_plus/west/family/trade` | 2 | 1 | 2 | 2 | T-1347 |
| `persons/male/50_plus/west/family/none` | 4 | 2 | 2 | 0 | T-1171 |
| `persons/male/50_plus/west/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/male/50_plus/west/lodging/none` | 1 | 0 | 1 | 0 | T-1538 |
| `persons/male/under_10/north/family/none` | 62 | 34 | 44 | 44 | T-1174 |
| `persons/male/under_10/north/lodging/none` | 22 | 12 | 10 | 10 | T-1536 |
| `persons/male/under_10/south/family/none` | 148 | 84 | 109 | 109 | T-1174 |
| `persons/male/under_10/south/lodging/none` | 52 | 30 | 22 | 17 | T-1536 |
| `persons/male/under_10/west/family/none` | 55 | 29 | 34 | 34 | T-1174 |
| `persons/male/under_10/west/lodging/none` | 19 | 10 | 9 | 9 | T-1536 |
| `persons/garrison/fort` | — | 2 | — | 0 | T-1176 |
| `persons/transient/town` | — | 0 | — | 0 | T-1178 |

## Households

The households the model wants, by kind and division.

- `households_target`: 644
- `households_target_basis`: the midpoint of the model's 471-816, rounded half up
- `households_target_range`: 471, 816
- `known_present`: 82
- `known_present_records`: 1,375
- `known_present_awaiting_a_household`: 1,293
- `known_uncertain_in_the_index_ruled_in_by_T-1386`: 936

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `households/boarding_house/north` | 12 | 1 | 11 | 5 | T-1538 |
| `households/boarding_house/south` | 41 | 7 | 34 | 1 | T-1538 |
| `households/boarding_house/west` | 9 | 1 | 8 | 2 | T-1538 |
| `households/family_dwelling/north` | 123 | 12 | 111 | 26 | T-1171 |
| `households/family_dwelling/south` | 257 | 41 | 216 | 65 | T-1171 |
| `households/family_dwelling/west` | 110 | 7 | 103 | 33 | T-1171 |
| `households/inn_tavern/north` | 3 | 0 | 3 | 1 | T-1538 |
| `households/inn_tavern/south` | 7 | 1 | 6 | 6 | T-1538 |
| `households/inn_tavern/west` | 4 | 0 | 4 | 1 | T-1538 |
| `households/institutional/north` | 1 | 0 | 1 | 1 | T-1531 |
| `households/institutional/south` | 1 | 0 | 1 | 1 | T-1531 |
| `households/store_residence/north` | 6 | 0 | 6 | 0 | T-1171 |
| `households/store_residence/south` | 61 | 10 | 51 | 0 | T-1171 |
| `households/store_residence/west` | 9 | 0 | 9 | 0 | T-1171 |
| `households/garrison/fort` | — | 2 | — | 0 | T-1176 |

## Businesses

The December 1835 State census set against the register the town already holds.

- `register_total`: 196
- `at_scene_date`: 210
- `census_enumerated_total`: 118
- `register_businesses_read`: 196
- `division_note`: EVERY BUSINESS BUCKET IS `unassigned` BY DIVISION TODAY, and that is a reading rather than a hole: the register carries a street where the paper printed one and no division at all, and assigning premises to a division is T-1182's audit and T-1198's seating. The key carries the axis so those tickets fill it rather than re-cut the book.
- `staffing_note`: The STAFF each business implies is T-1183's model and is not guessed at here; T-1189 staffs them from it.

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `businesses/bank` | 0 | 0 | 0 | 0 | T-1182 |
| `businesses/book_store` | 2 | 2 | 0 | 0 | T-1184 |
| `businesses/brewery` | 2 | 1 | 1 | 1 | T-1185 |
| `businesses/church` | 5 | 4 | 0 | 0 | T-1215 |
| `businesses/druggist` | 4 | 2 | 2 | 2 | T-1184 |
| `businesses/iron_foundry` | 1 | 2 | 0 | 0 | T-1185 |
| `businesses/lawyer` | 15 | 14 | 1 | 1 | T-1418 |
| `businesses/lottery_office` | 0 | 0 | 0 | 0 | T-1182 |
| `businesses/lyceum_and_reading_room` | 0 | 0 | 0 | 0 | T-1182 |
| `businesses/physician` | 10 | 8 | 2 | 0 | T-1529 |
| `businesses/printing_office` | 2 | 2 | 0 | 0 | T-1215 |
| `businesses/school` | 7 | 5 | 0 | 0 | T-1215 |
| `businesses/silversmith_jeweller` | 2 | 1 | 1 | 1 | T-1185 |
| `businesses/steam_saw_mill` | 1 | 2 | 0 | 0 | T-1187 |
| `businesses/storage_and_forwarding` | 4 | 7 | 0 | 0 | T-1187 |
| `businesses/store` | 44 | 65 | 0 | 0 | T-1184 |
| `businesses/tavern` | 8 | 11 | 0 | 0 | T-1187 |
| `businesses/tin_and_copper_manufactory` | 2 | 4 | 0 | 0 | T-1185 |

## Structures

The roofs the 668-roof programme still owes, by archetype group and division.

- `roof_target`: 668
- `standing_records`: 419
- `standing_with_an_occupant`: 123
- `standing_without_an_occupant`: 296
- `to_build_total`: 262
- `redeal_note`: A roof standing where the order book has nobody to put in it is a SUBSTITUTION for T-1197, never a demolition: 296 of the 419 standing records carry no occupants block today, and T-1197 re-audits them against this book.

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `structures/barns_stables/south` | 35 | 20 | 15 | 0 | T-1212 |
| `structures/barns_stables/west` | 20 | 12 | 8 | 0 | T-1212 |
| `structures/barns_stables/north` | 17 | 8 | 9 | 0 | T-1212 |
| `structures/barns_stables/fort` | 1 | 1 | 0 | 0 | T-1204 |
| `structures/fort_principal/fort` | 10 | 10 | 0 | 0 | T-1204 |
| `structures/inns_taverns/south` | 5 | 5 | 0 | 0 | T-1201 |
| `structures/inns_taverns/west` | 3 | 3 | 0 | 0 | T-1207 |
| `structures/inns_taverns/north` | 2 | 1 | 1 | 0 | T-1205 |
| `structures/institutional_public/south` | 5 | 5 | 0 | 0 | T-1202 |
| `structures/institutional_public/west` | 1 | 1 | 0 | 0 | T-1208 |
| `structures/institutional_public/north` | 3 | 3 | 0 | 0 | T-1205 |
| `structures/larger_boarding_houses/south` | 28 | 9 | 19 | 0 | T-1209 |
| `structures/larger_boarding_houses/west` | 6 | 2 | 4 | 0 | T-1209 |
| `structures/larger_boarding_houses/north` | 8 | 6 | 2 | 0 | T-1209 |
| `structures/ordinary_dwellings/south` | 176 | 118 | 58 | 0 | T-1203 |
| `structures/ordinary_dwellings/west` | 75 | 51 | 24 | 0 | T-1208 |
| `structures/ordinary_dwellings/north` | 84 | 46 | 38 | 0 | T-1206 |
| `structures/small_outbuildings/south` | 48 | 25 | 23 | 0 | T-1212 |
| `structures/small_outbuildings/west` | 14 | 4 | 10 | 0 | T-1212 |
| `structures/small_outbuildings/north` | 20 | 9 | 11 | 0 | T-1212 |
| `structures/small_outbuildings/fort` | 3 | 3 | 0 | 0 | T-1204 |
| `structures/stores_mixed_use/south` | 42 | 26 | 16 | 0 | T-1201 |
| `structures/stores_mixed_use/west` | 6 | 4 | 2 | 0 | T-1207 |
| `structures/stores_mixed_use/north` | 4 | 1 | 3 | 0 | T-1205 |
| `structures/stores_mixed_use/fort` | 1 | 1 | 0 | 0 | T-1204 |
| `structures/warehouses_freight/south` | 11 | 4 | 7 | 0 | T-1200 |
| `structures/warehouses_freight/west` | 2 | 1 | 1 | 0 | T-1207 |
| `structures/warehouses_freight/north` | 7 | 6 | 1 | 0 | T-1205 |
| `structures/workshops/south` | 15 | 10 | 5 | 0 | T-1201 |
| `structures/workshops/west` | 8 | 5 | 3 | 0 | T-1207 |
| `structures/workshops/north` | 7 | 5 | 2 | 0 | T-1205 |
| `structures/workshops/fort` | 1 | 1 | 0 | 0 | T-1204 |

## Ground first

The streets, terrain and lots a structure bucket waits on.

- `roofs_on_committed_ground`: 12
- `roofs_gated_on_coverage`: 250
- `statement`: 12 of the 262 remaining roofs stand on ground this project has already surveyed, platted and modelled. The other 250 have nowhere to go until street control, terrain and hydrology reach them. The binding constraint on the 668-roof programme is coverage, not recipes.

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `ground/blk_west_fulton_des_plaines` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_fulton_jefferson` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_fulton_clinton` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_lake_des_plaines` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_lake_jefferson` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_lake_canal` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_randolph_des_plaines` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_randolph_jefferson` | 0 | — | — | 0 | T-1414 |
| `ground/blk_west_randolph_canal` | 0 | — | — | 0 | T-1414 |
| `ground/blk_michigan_st_tract_west_north` | 0 | — | — | 0 |  |
| `ground/blk_michigan_st_tract_west_south` | 0 | — | — | 0 |  |
| `ground/blk_michigan_st_tract_east_north` | 0 | — | — | 0 |  |
| `ground/blk_michigan_st_tract_east_south` | 0 | — | — | 0 |  |
| `ground/blk_wabansia_b_t1` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_c_t1` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_b_t2` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_c_t2` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_b_t3` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_c_t3` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_b_t4` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_b_t5` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_c_t5` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_b_t6` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_c_t6` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_b_t7` | 0 | — | — | 0 | T-1414 |
| `ground/blk_wabansia_c_t7` | 0 | — | — | 0 | T-1414 |
| `ground/blk_south_water_market` | 27 | — | — | 0 |  |
| `ground/south_plat_beyond_committed_control` | 104 | — | — | 0 |  |
| `ground/west_division_beyond_committed_control` | 52 | — | — | 0 | T-1414 |
| `ground/north_division_beyond_modelled_ground` | 67 | — | — | 0 |  |

## Where the model and the roof programme disagree

The book carries THE MODEL. Every difference is listed here for T-1196, which re-cuts the 668-roof schedule against it. `programme groups` names the `district_group_matrix` groups summed on the programme side; a row marked NOT A CHECK reads its model figure off those same groups and therefore cannot disagree (2 of 5 do).

| | model | programme | delta | programme groups |
|---|---:|---:|---:|---|
| **households_against_dwellings** — The household model wants 644 households and the programme schedules 335 ordinary dwellings (335-377 in the model's own reading). More than one household to a roof is the resolution the census's own 8.204 people per dwelling implies; T-1196 re-cuts the schedule to say how many. | 644 | 335 | +309 | `ordinary_dwellings` |
| **boarding_houses** — NOT A CHECK: the model's 42 larger boarding houses ARE district_group_matrix.larger_boarding_houses — model_town_1835.build_lodging reads the figure straight off the roof programme — so this row cannot disagree, and its zero says nothing about whether 42 is the right number of boarding roofs. An independent count is owed to T-1196 with the re-cut. | 42 | 42 | +0 | `larger_boarding_houses` |
| **inns_and_taverns** — The model reads 11-11 inns and taverns; the programme schedules 10. This one is a real disagreement: the model's ceiling is the business layer's count at the scene date, not a figure read back off the programme. | 11 | 10 | +1 | `inns_taverns` |
| **institutional_and_public** — NOT A CHECK: the model reads 9-19 institutional and public roofs — 9 outside the fort and 10 principal roofs inside it — and the programme schedules those same two groups, institutional_public (9) and fort_principal (10), for 19. Both ends of the model are read off that matrix, so the row cannot disagree. Until T-1439 it reported a delta of ten by taking the fort's roofs on the model's side and not on the programme's, which is the schedule charged for ten roofs it already had. | 19 | 19 | +0 | `institutional_public`, `fort_principal` |
| **people_per_roof** — 2,543 people under 668 roofs is the ratio the completed town must meet; the census's own reading for November 1835 is 8.204 people per dwelling over 398 dwellings. | 2,543 | 668 | +0 | — |

## The invariants the convergence tickets assert

- **every_person_housed** (T-1215) — Every person in the layer — attested, inferred or reconstructed — is a member of a household or a lodging place that is seated on a roof. *Now:* 20 of 1375 present households name a lives_at.
- **every_working_person_has_a_workplace** (T-1189) — Every person carrying a trade, profession or employment has a workplace, or a stated `no fixed workplace`. *Now:* 49 of 1375 present households name a works_at.
- **every_business_has_staff** (T-1189) — Every business — attested, inferred or reconstructed — carries the staff T-1183's model implies for its kind. *Now:* not yet measurable: the authored business layer is T-1180.
- **every_structure_occupied_or_its_use_stated** (T-1197) — Every standing roof carries an occupant or a stated use. *Now:* 296 of 419 standing records carry no occupants block.
- **dwellings_ratio_within_its_bracket** (T-1215) — The town census's people-per-dwelling ratio is met within the model's bracket. *Now:* the book orders 2,543 people into 644 households.
- **an_uncompared_class_orders_nothing** (T-1442) — A trade-census class the crosswalk rules `compared: false` carries its figures but orders no reconstruction: the difference between a census line and the register is only a shortfall where the crosswalk has ruled the two comparable. *Now:* carried uncompared: 1 of 18 enumerated business classes, each ordering nought.
- **no_bucket_overfilled** (T-1166) — No bucket's `filled` exceeds its `to_reconstruct`; a filler that bypasses the book is red in check.sh. *Now:* enforced by --check on every gate run.
