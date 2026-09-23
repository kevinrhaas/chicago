---
id: T-0420
title: Open the four South Water blocks T-0009 has unblocked: 20 roofs of headroom on franklin, lasalle, clark and dearborn
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

Open the four South Water blocks T-0009 has unblocked: 20 roofs of headroom on franklin, lasalle, clark and dearborn.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**T-0365's option 1, now that T-0009 has answered it.** T-0365 measured that the anonymous-block
programme had no unblocked ground left: every platted block still carrying headroom was gated on
T-0009 or on T-0183. T-0009 closed on 2026-08-29 under the owner's ruling, and the load-bearing
half of that ruling for this ticket is one sentence — **the drawn South Water line does not move.**

T-0143 and T-0188 each refused to tighten a party-line row *against a line that may move*, and
T-0317 inherited the refusal. It is discharged: the corridor was re-derived from the control and
`data/streets/1835.json` was not touched.

| block | headroom | free lots |
|---|---|---|
| `blk_south_water_lasalle` | 8 | 3 |
| `blk_south_water_franklin` | 4 | 2 |
| `blk_south_water_clark` | 4 | 2 |
| `blk_south_water_dearborn` | 4 | 2 |

**20 roofs between them**, and it is the largest visible win the programme has. `blk_south_water_market`
is NOT in this ticket: it stays gated on T-0183, which is a control point the node rule cannot make.

**Take ONE block per run** — T-0028's programme rule is one run, one demonstration, one successor,
and four blocks is four runs. **Needs the bake** for the roofs it deals.

**Acceptance:** one block opened per run against its committed lots; the row stands on the block
face rather than on a re-derived line; the census in `tools/reconcile_665.py` reconciles; a
screenshot from the same spot shows roofs that were not there.

**Links:** T-0365 · T-0009 · T-0028 · T-0143 · T-0188 · T-0317 · T-0183 · `tools/reconcile_665.py`.

---

**SPLIT ON 2026-08-30, by T-0365's close.** This ticket's own body says "Take ONE block per run …
four blocks is four runs", which is the definition of effort L, and `ticket.mjs claim` refuses an
L for the reason `tickets/README.md` records: a run that can only finish a quarter of a ticket
leaves it claimed and open, and the next run rebuilds it. The four blocks are now T-0429
(`lasalle`, 8), T-0430 (`franklin`, 4), T-0431 (`clark`, 4) and T-0432 (`dearborn`, 4). Each
carries its own re-derived headroom table and `needs_bake: true`. They hold this ticket's exact
place in QUEUE — nothing was re-ranked. This record keeps the full ask, the ruling it rests on and
the links.
