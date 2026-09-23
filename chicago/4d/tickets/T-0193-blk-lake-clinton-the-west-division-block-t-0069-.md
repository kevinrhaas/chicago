---
id: T-0193
title: blk_lake_clinton, the West Division block T-0069 refused
state: blocked-tech
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0127
opened: 2026-08-24
closed: null
pr: 421
claimed_by: run 8/27/2026, 6:18:32 PM CT
blocked_on: T-0190 — a second street tier for the street edge. Built and measured: both faces generate cleanly (+192.2 m of walk) but desktop 'balanced' reads 1,228,110 of 1,210,000 at the lake_at_canal stand, over by 18,110, and the Lake face alone is still over by 13,890. 'balanced' had 8,656 triangles of headroom before this was tried, so no street frontage of any size fits under that rung today; T-0237 refuses buying it with a ceiling raise.
needs_bake: false
---

blk_lake_clinton, the West Division block T-0069 refused.

Piece 4 of 5 of **T-0127 — The rest of the town gets the street edge**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance (stated before working, and NOT weakened to pass):** `blk_lake_clinton`'s
platted block faces carry the street edge by the same rule the rest of the town does —
laid from the plat grid, not hand-placed — and a visitor standing in the West Division
finds plank walk under foot. `full`, `balanced` and `light` are each inside their ceiling
at all five of T-0135's stands, at BOTH viewports, measured on the published mirror.

**WHAT HAPPENED: it was built, it works, and it does not fit. BLOCKED ON T-0190.**

The rule needed no change — `blk_lake_clinton` was only ever excluded by name, in
`EDGE_SKIP_BLOCKS`. Taking the name out generates both faces cleanly and the march
refuses nothing it does not refuse everywhere else (a building standing on the frontage
line is the street wall; an unimproved lot takes no fence; a blacksmith's yard gate takes
no hitching post). The block gains **+2 block faces, +192.2 m of walk in 2 unbroken runs,
+1 board crossing over Randolph and +3 street-lining fences**. Note this is now BOTH
faces: the Lake face T-0069 named, plus a Randolph face that only became coverable when
T-0240 put Randolph in `EDGE_STREETS` the day before this ran.

Published and read with `tools/measure_detail_ceilings.mjs` at T-0135's five stands,
both viewports, against `dev`:

| tier | ceiling | desktop worst | mobile worst |
|---|---:|---:|---:|
| `full` | 1,400,000 | 1,378,391 PASS | 1,299,917 PASS |
| `balanced` | 1,210,000 | **1,228,110 — OVER by 18,110** | 1,175,288 PASS |
| `light` | 785,000 | 750,290 PASS | 699,416 PASS |

**One stand, one tier, one viewport.** The whole cost lands at `lake_at_canal`, which
stands at this block's own east end and looks east down the axis where nothing culls:
+27,932 triangles there, against a flat +8,460 at the other four stands. Mobile clears
`balanced` by 34,712.

**And half of it does not fit either, which is the finding.** The Lake face ALONE —
exactly what T-0069 refused, with the Randolph face held back — costs +23,712 at that
stand and reads 1,223,890, still **over by 13,890**. So this is not a block that is too
big. `balanced` stood **1,201,344 of 1,210,000 on `dev` before this was tried — 8,656
triangles, 0.7 % of headroom** — and no street frontage of any size fits under that rung
today. That is the same binding fact T-0240 recorded for Washington one rung earlier,
now confirmed a second time from a different direction.

The two honest routes past it are a sixth re-basing of the ceiling or a trim, and
T-0237's acceptance refuses the raise in as many words. So this waits on **T-0190 — a
second street tier for the street edge, and the ceiling that refuses it**, which is
already in the queue and is exactly this problem.

**What shipped instead (PR #421):** the refusal is no longer a promise. The record's
`refused` entry for `blk_lake_clinton` used to say only that the block "belongs with the
rest of the town in the follow-up ticket"; it now carries every number above, the way
this project requires every other refusal to. The generator carries the same table
beside `EDGE_SKIP_BLOCKS` so the next run does not re-measure it.

**Links:** T-0127 (parent) · T-0069 (the original refusal) · T-0190 (what unblocks this)
· T-0240 (Randolph, which shipped) · T-0241 (Washington, refused by the same rung) ·
T-0218 · T-0237.
