# The 1835 reconstruction order book

> DERIVED from `data/reconstruction/1835_reconstruction_order_book.json`. Regenerate with
> `tools/build_order_book_1835.py --build`; `tools/check.sh` re-derives both. Do not hand-edit.

**T-1166.** Known minus model, per bucket, with the ticket that owns filling it. The town converges to **2,543 people** in **644 households**, working **109 enumerated businesses**, under **668 roofs**.

| | target | known | to reconstruct |
|---|---:|---:|---:|
| Persons | 2,543 | 1,402 | 1,671 |
| Households | 644 | 82 | 564 |
| Businesses (enumerated classes) | 109 | 130 | 7 |
| Roofs | 668 | 417 | 264 |

**2,381 people stand in the layer today** and **431** are still owed after the counters, so the town this book converges to is **2,812** — inside the model's 2,362-3,265. `--build` and `--check` both refuse a remainder that lands outside it.

## What the re-cut found

> T-1463 summed T-1386's presence rulings into `known`, and T-1525 read the parish register into it. These are the things that made measurable, carried in the book so they cannot go stale in a report.


### t 1171 adjudicated

*T-1171 closed 2026-09-18 (PR #1476) having drawn 124 of 556, and the presence rulings landed 2026-09-19 — the day after. Was its 432 real, or an artifact of a quota cut against a town that did not yet hold the 827 ruled-in people?*

Of the 432, the household leg is DISCHARGED: T-1171's household quota was 182 against 124 drawn and the re-cut takes it to its own drawn figure, so it owes 372. The person leg is PART artifact: 374 before, 208 now. The remainder is owed and is not a counting error, so T-1171 REOPENS for it.

**Verdict:** reopen T-1171 for the persons; the households are discharged

### the remainder said out loud

*What does the town converge to if every remaining order is filled?*

2,381 standing plus 431 still owed is 2,812, inside the model's 2,362-3,265. Before the re-cut the same sum was 2,381 + 843 = 3,224, and the book was ordering a replacement for 826 people already in the layer. It is 269 above the model's 2,543 point, and that surplus is the 524 people drawn into 49 buckets past what the re-cut would now order — named in `recut_refusals`, held rather than clamped, and retired or re-familied by T-1196, T-1197 and T-1179 rather than by this book.

### households are counted in two different units

*The model wants 643 households and the layer holds 1,510 records. Are those the same thing?*

Of the 1,375 records the layer holds present, 82 carry a reading about a dwelling and 1,293 do not. The quota is taken against the 82, so it stops reading 0 owed — which was never true and was the symptom that raised this — and starts reading what the town still owes in houses.

### a documented reading shrank an order the town had drawn

*The parish register's 120 documented residents (T-0841) land in buckets the town had already reconstructed strangers into. Where did reading a person the town can name put a bucket's order UNDER what was drawn against it, and by how many people?*

`persons/male/20_29/south/family/trade` holds 60 drawn against an order of 32 — over-supplied by 28. That is 28 reconstructed people standing where the sources now name someone else, and it is a different fault from the rest of `recut_refusals`: those are quotas drifting under a draw, this is the town learning it invented a person it did not need. Nothing here is clamped and nothing already drawn moves — T-1459 — so the book keeps ordering the larger figure and names the surplus instead.

**Declined:** RETIRING a reconstructed card is the bucket owner's work and not this book's: a book that deleted people to make its own arithmetic close would be reconstructing backwards. T-1347, which drew the trade band, has closed, so T-1530 is filed for the south-side 20-29 surplus and T-1506 owns the surplus lawyer.

## Where the re-cut was refused

49 buckets would have had their order cut below the people already drawn against them. The owner's ruling of 2026-09-20 refuses that by name rather than clamping it: each is held at what was drawn, and the surplus is retired or re-familied by T-1196, T-1197 and T-1179.

| bucket | ticket | cause | quota it was drawn against | the re-cut would order | drawn |
|---|---|---|---:|---:|---:|
| `persons/female/10_19/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 26 | 15 | 26 |
| `persons/female/10_19/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 61 | 33 | 61 |
| `persons/female/10_19/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 24 | 13 | 24 |
| `persons/female/20_29/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 15 | 8 | 15 |
| `persons/female/20_29/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 28 | 16 | 28 |
| `persons/female/20_29/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 35 | 19 | 35 |
| `persons/female/20_29/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 67 | 36 | 66 |
| `persons/female/20_29/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 13 | 7 | 13 |
| `persons/female/20_29/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 25 | 14 | 25 |
| `persons/female/30_39/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 6 | 4 | 6 |
| `persons/female/30_39/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 13 | 7 | 13 |
| `persons/female/30_39/north/lodging/trade` | T-1532 | the_re_cut_reached_work_already_drawn | 3 | 1 | 2 |
| `persons/female/30_39/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 16 | 9 | 16 |
| `persons/female/30_39/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 31 | 16 | 31 |
| `persons/female/30_39/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 7 | 4 | 6 |
| `persons/female/30_39/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 12 | 6 | 12 |
| `persons/female/40_49/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 3 | 1 | 3 |
| `persons/female/40_49/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 5 | 3 | 5 |
| `persons/female/40_49/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 6 | 3 | 6 |
| `persons/female/40_49/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 11 | 6 | 11 |
| `persons/female/40_49/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 3 | 1 | 3 |
| `persons/female/40_49/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 4 | 3 | 4 |
| `persons/female/50_plus/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 |
| `persons/female/50_plus/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 3 | 2 | 3 |
| `persons/female/50_plus/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 4 | 2 | 4 |
| `persons/female/50_plus/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 8 | 4 | 8 |
| `persons/female/50_plus/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 |
| `persons/female/50_plus/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 |
| `persons/female/under_10/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 46 | 26 | 45 |
| `persons/female/under_10/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 107 | 57 | 107 |
| `persons/female/under_10/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 40 | 23 | 40 |
| `persons/male/10_19/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 30 | 17 | 30 |
| `persons/male/10_19/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 71 | 39 | 71 |
| `persons/male/10_19/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 27 | 15 | 26 |
| `persons/male/20_29/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 25 | 14 | 25 |
| `persons/male/20_29/south/family/trade` | T-1347 | a_documented_reading_shrank_the_order | 60 | 32 | 60 |
| `persons/male/20_29/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 23 | 13 | 23 |
| `persons/male/30_39/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 15 | 8 | 15 |
| `persons/male/30_39/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 35 | 19 | 35 |
| `persons/male/30_39/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 13 | 7 | 13 |
| `persons/male/40_49/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 4 | 2 | 4 |
| `persons/male/40_49/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 10 | 5 | 10 |
| `persons/male/40_49/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 3 | 2 | 3 |
| `persons/male/50_plus/north/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 |
| `persons/male/50_plus/south/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 5 | 2 | 5 |
| `persons/male/50_plus/west/family/trade` | T-1347 | the_re_cut_reached_work_already_drawn | 2 | 1 | 2 |
| `persons/male/under_10/north/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 51 | 28 | 51 |
| `persons/male/under_10/south/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 120 | 64 | 119 |
| `persons/male/under_10/west/family/none` | T-1174 | the_re_cut_reached_work_already_drawn | 46 | 26 | 43 |

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

The re-cut wanted **36** trade slots in the bands it reopened. The younger bands held **31** undrawn and the adult cells it would draw from held **35**, so **31** moved and the book's employed total did not change. Every cell below is a `lodging` cell on both sides, because every `family` cell of the reopened band is drawn out: the working youths this book still orders are BOARDERS — an apprentice or a shop hand sleeping where he works — which is a consequence of what is already drawn and not a claim about 1835.

| into | slots |
|---|---:|
| `persons/female/10_19/north/lodging` | 3 |
| `persons/female/10_19/south/lodging` | 8 |
| `persons/female/10_19/west/lodging` | 4 |
| `persons/male/10_19/north/lodging` | 3 |
| `persons/male/10_19/south/lodging` | 9 |
| `persons/male/10_19/west/lodging` | 4 |

| out of | slots |
|---|---:|
| `persons/female/20_29/south/lodging` | 5 |
| `persons/female/30_39/south/lodging` | 3 |
| `persons/female/30_39/west/lodging` | 1 |
| `persons/female/40_49/south/lodging` | 1 |
| `persons/male/20_29/north/lodging` | 3 |
| `persons/male/20_29/south/lodging` | 10 |
| `persons/male/20_29/west/lodging` | 4 |
| `persons/male/30_39/south/lodging` | 4 |

**21 cell(s) could not take or give their share**, because the people who would have filled them are already drawn. Each is named with both numbers; none was clamped in silence, and no person already drawn moved.

| cell | the re-cut wanted | the remainder could pay | already drawn | by |
|---|---:|---:|---:|---|
| `persons/female/10_19/north/family` (into) | 3 | 0 | 26 | T-1174 |
| `persons/female/10_19/south/family` (into) | 7 | 0 | 61 | T-1174 |
| `persons/female/10_19/west/family` (into) | 3 | 0 | 24 | T-1174 |
| `persons/male/10_19/north/family` (into) | 3 | 0 | 30 | T-1174 |
| `persons/male/10_19/south/family` (into) | 8 | 0 | 71 | T-1174 |
| `persons/male/10_19/west/family` (into) | 3 | 0 | 26 | T-1174 |
| `persons/female/20_29/north/family` (out of) | 1 | 0 | 15 | T-1347 |
| `persons/female/20_29/south/family` (out of) | 3 | 0 | 35 | T-1347 |
| `persons/female/20_29/west/family` (out of) | 1 | 0 | 13 | T-1347 |
| `persons/female/30_39/south/family` (out of) | 2 | 0 | 16 | T-1347 |
| `persons/female/30_39/west/family` (out of) | 1 | 0 | 6 | T-1347 |
| `persons/female/40_49/west/family` (out of) | 1 | 0 | 3 | T-1347 |
| `persons/female/50_plus/south/family` (out of) | 1 | 0 | 4 | T-1347 |
| `persons/male/20_29/north/family` (out of) | 3 | 0 | 25 | T-1347 |
| `persons/male/20_29/south/family` (out of) | 5 | 0 | 60 | T-1347 |
| `persons/male/20_29/west/family` (out of) | 2 | 0 | 23 | T-1347 |
| `persons/male/30_39/north/family` (out of) | 1 | 0 | 15 | T-1347 |
| `persons/male/30_39/south/family` (out of) | 3 | 0 | 35 | T-1347 |
| `persons/male/30_39/west/family` (out of) | 1 | 0 | 13 | T-1347 |
| `persons/male/40_49/south/family` (out of) | 1 | 0 | 10 | T-1347 |
| `persons/male/50_plus/south/family` (out of) | 1 | 0 | 5 | T-1347 |

### Who has already spent against this book

The re-cut's one forbidden move is to pull a quota out from under a stage that has already drawn on it. These are the stages that have, so a reader can tell the settled parts of the book from the open ones:

| ticket | persons drawn | buckets |
|---|---:|---:|
| T-1174 | 680 | 27 |
| T-1347 | 308 | 24 |
| T-1171 | 295 | 19 |
| T-1371 | 85 | 29 |
| T-1533 | 12 | 3 |
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

The roster offers 1,786 names the corpus printed and this project withheld. Each class is a licence, not a quota:

| class | offered | ticket |
|---|---:|---|
| `R1_in_window_uncertain` | 901 | T-1172 |
| `R2_in_window_single_source` | 207 | T-1172 |
| `R3_1834_return_or_muster` | 28 | T-1172 |
| `R4_surname_only_census` | 436 | T-1170 |
| `R5_later_only_backprojectable` | 53 | T-1172 |
| `R6_native_metis_black` | 161 | T-1177 |

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
| `persons/female/10_19/north/family/none` | 32 | 17 | 26 | 26 | T-1174 |
| `persons/female/10_19/north/lodging/trade` | 3 | 0 | 3 | 0 | T-1532 |
| `persons/female/10_19/north/lodging/none` | 8 | 6 | 2 | 2 | T-1536 |
| `persons/female/10_19/south/family/none` | 76 | 43 | 61 | 61 | T-1174 |
| `persons/female/10_19/south/lodging/trade` | 8 | 0 | 8 | 0 | T-1532 |
| `persons/female/10_19/south/lodging/none` | 19 | 15 | 4 | 4 | T-1536 |
| `persons/female/10_19/west/family/none` | 28 | 15 | 24 | 24 | T-1174 |
| `persons/female/10_19/west/lodging/trade` | 4 | 0 | 4 | 0 | T-1532 |
| `persons/female/10_19/west/lodging/none` | 6 | 5 | 1 | 1 | T-1536 |
| `persons/female/20_29/north/family/trade` | 18 | 10 | 15 | 15 | T-1347 |
| `persons/female/20_29/north/family/none` | 34 | 18 | 28 | 28 | T-1174 |
| `persons/female/20_29/north/lodging/trade` | 6 | 3 | 3 | 1 | T-1532 |
| `persons/female/20_29/north/lodging/none` | 12 | 7 | 5 | 2 | T-1538 |
| `persons/female/20_29/south/family/trade` | 43 | 24 | 35 | 35 | T-1347 |
| `persons/female/20_29/south/family/none` | 82 | 46 | 66 | 66 | T-1174 |
| `persons/female/20_29/south/lodging/trade` | 10 | 9 | 1 | 0 | T-1532 |
| `persons/female/20_29/south/lodging/none` | 34 | 16 | 18 | 7 | T-1538 |
| `persons/female/20_29/west/family/trade` | 16 | 9 | 13 | 13 | T-1347 |
| `persons/female/20_29/west/family/none` | 30 | 16 | 25 | 25 | T-1174 |
| `persons/female/20_29/west/lodging/trade` | 5 | 2 | 3 | 0 | T-1532 |
| `persons/female/20_29/west/lodging/none` | 11 | 6 | 5 | 2 | T-1538 |
| `persons/female/30_39/north/family/trade` | 8 | 4 | 6 | 6 | T-1347 |
| `persons/female/30_39/north/family/none` | 16 | 9 | 13 | 13 | T-1174 |
| `persons/female/30_39/north/lodging/trade` | 3 | 2 | 2 | 2 | T-1532 |
| `persons/female/30_39/north/lodging/none` | 5 | 2 | 3 | 0 | T-1538 |
| `persons/female/30_39/south/family/trade` | 20 | 11 | 16 | 16 | T-1347 |
| `persons/female/30_39/south/family/none` | 38 | 22 | 31 | 31 | T-1174 |
| `persons/female/30_39/south/lodging/trade` | 4 | 4 | 0 | 0 | T-1532 |
| `persons/female/30_39/south/lodging/none` | 16 | 7 | 9 | 4 | T-1538 |
| `persons/female/30_39/west/family/trade` | 8 | 4 | 6 | 6 | T-1347 |
| `persons/female/30_39/west/family/none` | 14 | 8 | 12 | 12 | T-1174 |
| `persons/female/30_39/west/lodging/trade` | 2 | 2 | 0 | 0 | T-1532 |
| `persons/female/30_39/west/lodging/none` | 6 | 2 | 4 | 0 | T-1538 |
| `persons/female/40_49/north/family/trade` | 3 | 2 | 3 | 3 | T-1347 |
| `persons/female/40_49/north/family/none` | 6 | 3 | 5 | 5 | T-1174 |
| `persons/female/40_49/north/lodging/trade` | 1 | 0 | 1 | 0 | T-1532 |
| `persons/female/40_49/north/lodging/none` | 2 | 1 | 1 | 0 | T-1538 |
| `persons/female/40_49/south/family/trade` | 7 | 4 | 6 | 6 | T-1347 |
| `persons/female/40_49/south/family/none` | 14 | 8 | 11 | 11 | T-1174 |
| `persons/female/40_49/south/lodging/trade` | 2 | 2 | 0 | 0 | T-1532 |
| `persons/female/40_49/south/lodging/none` | 6 | 2 | 4 | 1 | T-1538 |
| `persons/female/40_49/west/family/trade` | 3 | 2 | 3 | 3 | T-1347 |
| `persons/female/40_49/west/family/none` | 5 | 2 | 4 | 4 | T-1174 |
| `persons/female/40_49/west/lodging/trade` | 1 | 0 | 1 | 0 | T-1532 |
| `persons/female/40_49/west/lodging/none` | 2 | 1 | 1 | 0 | T-1538 |
| `persons/female/50_plus/north/family/trade` | 2 | 1 | 2 | 2 | T-1347 |
| `persons/female/50_plus/north/family/none` | 4 | 2 | 3 | 3 | T-1174 |
| `persons/female/50_plus/north/lodging/trade` | 1 | 0 | 1 | 0 | T-1532 |
| `persons/female/50_plus/north/lodging/none` | 1 | 0 | 1 | 0 | T-1538 |
| `persons/female/50_plus/south/family/trade` | 5 | 3 | 4 | 4 | T-1347 |
| `persons/female/50_plus/south/family/none` | 9 | 5 | 8 | 8 | T-1174 |
| `persons/female/50_plus/south/lodging/trade` | 2 | 1 | 1 | 0 | T-1532 |
| `persons/female/50_plus/south/lodging/none` | 3 | 2 | 1 | 0 | T-1538 |
| `persons/female/50_plus/west/family/trade` | 2 | 1 | 2 | 2 | T-1347 |
| `persons/female/50_plus/west/family/none` | 3 | 2 | 2 | 2 | T-1174 |
| `persons/female/50_plus/west/lodging/trade` | 1 | 0 | 1 | 1 | T-1532 |
| `persons/female/50_plus/west/lodging/none` | 1 | 0 | 1 | 0 | T-1538 |
| `persons/female/under_10/north/family/none` | 55 | 29 | 45 | 45 | T-1174 |
| `persons/female/under_10/north/lodging/none` | 19 | 11 | 8 | 5 | T-1536 |
| `persons/female/under_10/south/family/none` | 132 | 75 | 107 | 107 | T-1174 |
| `persons/female/under_10/south/lodging/none` | 46 | 26 | 20 | 0 | T-1536 |
| `persons/female/under_10/west/family/none` | 49 | 26 | 40 | 40 | T-1174 |
| `persons/female/under_10/west/lodging/none` | 17 | 9 | 8 | 0 | T-1536 |
| `persons/male/10_19/north/family/none` | 37 | 20 | 30 | 30 | T-1174 |
| `persons/male/10_19/north/lodging/trade` | 3 | 0 | 3 | 0 | T-1532 |
| `persons/male/10_19/north/lodging/none` | 10 | 7 | 3 | 3 | T-1536 |
| `persons/male/10_19/south/family/none` | 88 | 49 | 71 | 71 | T-1174 |
| `persons/male/10_19/south/lodging/trade` | 9 | 0 | 9 | 0 | T-1532 |
| `persons/male/10_19/south/lodging/none` | 22 | 18 | 4 | 4 | T-1536 |
| `persons/male/10_19/west/family/none` | 33 | 18 | 26 | 26 | T-1174 |
| `persons/male/10_19/west/lodging/trade` | 4 | 0 | 4 | 0 | T-1532 |
| `persons/male/10_19/west/lodging/none` | 7 | 6 | 1 | 1 | T-1536 |
| `persons/male/20_29/north/family/trade` | 31 | 17 | 25 | 25 | T-1347 |
| `persons/male/20_29/north/family/none` | 58 | 31 | 27 | 0 | T-1171 |
| `persons/male/20_29/north/lodging/trade` | 8 | 6 | 2 | 2 | T-1532 |
| `persons/male/20_29/north/lodging/none` | 23 | 11 | 12 | 6 | T-1538 |
| `persons/male/20_29/south/family/trade` | 73 | 41 | 60 | 60 | T-1347 |
| `persons/male/20_29/south/family/none` | 140 | 79 | 61 | 0 | T-1171 |
| `persons/male/20_29/south/lodging/trade` | 16 | 15 | 1 | 0 | T-1532 |
| `persons/male/20_29/south/lodging/none` | 59 | 27 | 32 | 10 | T-1538 |
| `persons/male/20_29/west/family/trade` | 27 | 14 | 23 | 23 | T-1347 |
| `persons/male/20_29/west/family/none` | 52 | 27 | 25 | 0 | T-1171 |
| `persons/male/20_29/west/lodging/trade` | 6 | 5 | 1 | 1 | T-1532 |
| `persons/male/20_29/west/lodging/none` | 22 | 10 | 12 | 3 | T-1538 |
| `persons/male/30_39/north/family/trade` | 18 | 10 | 15 | 15 | T-1347 |
| `persons/male/30_39/north/family/none` | 34 | 18 | 16 | 0 | T-1171 |
| `persons/male/30_39/north/lodging/trade` | 6 | 3 | 3 | 0 | T-1532 |
| `persons/male/30_39/north/lodging/none` | 12 | 6 | 6 | 3 | T-1538 |
| `persons/male/30_39/south/family/trade` | 43 | 24 | 35 | 35 | T-1347 |
| `persons/male/30_39/south/family/none` | 82 | 46 | 36 | 0 | T-1171 |
| `persons/male/30_39/south/lodging/trade` | 11 | 9 | 2 | 0 | T-1532 |
| `persons/male/30_39/south/lodging/none` | 33 | 16 | 17 | 6 | T-1538 |
| `persons/male/30_39/west/family/trade` | 16 | 9 | 13 | 13 | T-1347 |
| `persons/male/30_39/west/family/none` | 30 | 16 | 14 | 0 | T-1171 |
| `persons/male/30_39/west/lodging/trade` | 5 | 2 | 3 | 0 | T-1532 |
| `persons/male/30_39/west/lodging/none` | 11 | 6 | 5 | 2 | T-1538 |
| `persons/male/40_49/north/family/trade` | 5 | 3 | 4 | 4 | T-1347 |
| `persons/male/40_49/north/family/none` | 10 | 5 | 5 | 0 | T-1171 |
| `persons/male/40_49/north/lodging/trade` | 2 | 1 | 1 | 0 | T-1532 |
| `persons/male/40_49/north/lodging/none` | 3 | 1 | 2 | 0 | T-1538 |
| `persons/male/40_49/south/family/trade` | 12 | 7 | 10 | 10 | T-1347 |
| `persons/male/40_49/south/family/none` | 24 | 13 | 11 | 0 | T-1171 |
| `persons/male/40_49/south/lodging/trade` | 4 | 2 | 2 | 0 | T-1532 |
| `persons/male/40_49/south/lodging/none` | 9 | 6 | 3 | 1 | T-1538 |
| `persons/male/40_49/west/family/trade` | 4 | 2 | 3 | 3 | T-1347 |
| `persons/male/40_49/west/family/none` | 9 | 5 | 4 | 0 | T-1171 |
| `persons/male/40_49/west/lodging/trade` | 2 | 1 | 1 | 0 | T-1532 |
| `persons/male/40_49/west/lodging/none` | 3 | 1 | 2 | 0 | T-1538 |
| `persons/male/50_plus/north/family/trade` | 2 | 1 | 2 | 2 | T-1347 |
| `persons/male/50_plus/north/family/none` | 5 | 3 | 2 | 0 | T-1171 |
| `persons/male/50_plus/north/lodging/trade` | 1 | 0 | 1 | 0 | T-1532 |
| `persons/male/50_plus/north/lodging/none` | 1 | 0 | 1 | 0 | T-1538 |
| `persons/male/50_plus/south/family/trade` | 6 | 4 | 5 | 5 | T-1347 |
| `persons/male/50_plus/south/family/none` | 11 | 6 | 5 | 0 | T-1171 |
| `persons/male/50_plus/south/lodging/trade` | 2 | 1 | 1 | 0 | T-1532 |
| `persons/male/50_plus/south/lodging/none` | 4 | 2 | 2 | 0 | T-1538 |
| `persons/male/50_plus/west/family/trade` | 2 | 1 | 2 | 2 | T-1347 |
| `persons/male/50_plus/west/family/none` | 4 | 2 | 2 | 0 | T-1171 |
| `persons/male/50_plus/west/lodging/trade` | 1 | 0 | 1 | 0 | T-1532 |
| `persons/male/50_plus/west/lodging/none` | 1 | 0 | 1 | 0 | T-1538 |
| `persons/male/under_10/north/family/none` | 62 | 34 | 51 | 51 | T-1174 |
| `persons/male/under_10/north/lodging/none` | 22 | 12 | 10 | 5 | T-1536 |
| `persons/male/under_10/south/family/none` | 148 | 84 | 119 | 119 | T-1174 |
| `persons/male/under_10/south/lodging/none` | 52 | 30 | 22 | 0 | T-1536 |
| `persons/male/under_10/west/family/none` | 55 | 29 | 43 | 43 | T-1174 |
| `persons/male/under_10/west/lodging/none` | 19 | 10 | 9 | 2 | T-1536 |
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
- `standing_records`: 417
- `standing_with_an_occupant`: 124
- `standing_without_an_occupant`: 293
- `to_build_total`: 264
- `redeal_note`: A roof standing where the order book has nobody to put in it is a SUBSTITUTION for T-1197, never a demolition: 293 of the 417 standing records carry no occupants block today, and T-1197 re-audits them against this book.

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `structures/barns_stables/south` | 35 | 20 | 15 | 0 | T-1212 |
| `structures/barns_stables/west` | 20 | 11 | 9 | 0 | T-1212 |
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
| `structures/ordinary_dwellings/west` | 75 | 50 | 25 | 0 | T-1208 |
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
- `roofs_gated_on_coverage`: 252
- `statement`: 12 of the 264 remaining roofs stand on ground this project has already surveyed, platted and modelled. The other 252 have nowhere to go until street control, terrain and hydrology reach them. The binding constraint on the 668-roof programme is coverage, not recipes.

| bucket | target | known | to do | filled | ticket |
|---|---:|---:|---:|---:|---|
| `ground/blk_west_fulton_des_plaines` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_fulton_jefferson` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_fulton_clinton` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_lake_des_plaines` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_lake_jefferson` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_lake_canal` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_randolph_des_plaines` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_randolph_jefferson` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_west_randolph_canal` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_michigan_st_tract_west_north` | 0 | — | — | 0 |  |
| `ground/blk_michigan_st_tract_west_south` | 0 | — | — | 0 |  |
| `ground/blk_michigan_st_tract_east_north` | 0 | — | — | 0 |  |
| `ground/blk_michigan_st_tract_east_south` | 0 | — | — | 0 |  |
| `ground/blk_wabansia_b_t1` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_c_t1` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_b_t2` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_c_t2` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_b_t3` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_c_t3` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_b_t4` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_b_t5` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_c_t5` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_b_t6` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_c_t6` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_b_t7` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_wabansia_c_t7` | 0 | — | — | 0 | T-1414, T-1444 |
| `ground/blk_south_water_market` | 27 | — | — | 0 |  |
| `ground/west_wolf_point_outer` | 2 | — | — | 0 | T-1414, T-1444 |
| `ground/south_plat_beyond_committed_control` | 104 | — | — | 0 |  |
| `ground/west_division_beyond_committed_control` | 52 | — | — | 0 | T-1414, T-1444 |
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
- **every_structure_occupied_or_its_use_stated** (T-1197) — Every standing roof carries an occupant or a stated use. *Now:* 293 of 417 standing records carry no occupants block.
- **dwellings_ratio_within_its_bracket** (T-1215) — The town census's people-per-dwelling ratio is met within the model's bracket. *Now:* the book orders 2,543 people into 644 households.
- **an_uncompared_class_orders_nothing** (T-1442) — A trade-census class the crosswalk rules `compared: false` carries its figures but orders no reconstruction: the difference between a census line and the register is only a shortfall where the crosswalk has ruled the two comparable. *Now:* carried uncompared: 1 of 18 enumerated business classes, each ordering nought.
- **no_bucket_overfilled** (T-1166) — No bucket's `filled` exceeds its `to_reconstruct`; a filler that bypasses the book is red in check.sh. *Now:* enforced by --check on every gate run.
