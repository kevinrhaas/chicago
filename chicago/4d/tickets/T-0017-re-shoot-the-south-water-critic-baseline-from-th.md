---
id: T-0017
title: Re-shoot the south_water critic baseline from the new stand
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: XS
legacy_id: T-V2c
parent: null
opened: 2026-08-17
closed: 2026-08-23
pr: 334
claimed_by: run 8/23/2026, 12:17:00 PM CT
blocked_on: null
needs_bake: false
---

south_water is a critic baseline station and T-V2 moved it; rows shot before 2026-08-16
measure a different place. Re-shoot both viewports, restate the row. Deep history: § T-V2c
(~6230).

**Acceptance:** the STATUS baseline table's south_water row says which stand it measures.
---

## RE-SHOT 2026-08-23 — the row is labelled, not replaced, and the run measured why

**Done:** both 2026-08-14 baseline tables carry a **†** on the `south_water` row and a footnote
under them naming the retired stand — local `(260, -95)`, "South Water Street, looking east" — the
stand T-V2 (#135) retired on 2026-08-15 for `(329.8, 7.0)`, the Wells Street corner. That is the
acceptance clause.

**The ticket's implied remedy was wrong and the run has the numbers.** "Re-shoot and restate" reads
as though the retired row could be reproduced by returning the camera. It cannot. Shooting the
retired coordinates on today's `dev`, same harness, same frozen clock, gives a row that matches
neither the 2026-08-14 figures nor the current stand: `flower load` **0.0575 → 0.0037** with the
camera unmoved, draw calls **85 → 208**, triangles **570,718 → 1,441,196**. The dataset agrees —
**242 placed structures on the baseline commit, 343 today**, and within 200 m of that stand **39 →
64**. So there are three rows in the write-up, not two: the gap between rows one and two is nine
days of town, the gap between rows two and three is the stand.

**What the move did:** it took the station out of the shade. Darkest-decile L **8.87 → 26.15**
desktop, **7.64 → 37.14** mobile, against RENDERING § 5's floor of L ≥ 14 — the retired stand fails
it at both viewports on today's build, the current stand clears it at both. Crown G−B **28.55 →
80.74** / **23.05 → 73.11** says the same thing on crowns. Grain collapses (RMS mid/near **32.38 /
29.43 → 2.74 / 0.98** desktop) because the near field is now graded roadway rather than sward.

Full three-way tables, both viewports, and three findings the ticket did not ask for — the
`timber all` column heading predates R-W4a's split, the rig stands at thirteen stations against the
table's eleven, and the § 5 draw-call bullet is stale for every station — are in `docs/STATUS.md`
under *Re-shot 2026-08-23*. Frames: `docs/evidence/t-0017-{retired,current}-stand.png`.

`data/scenes/1835.json` was patched to the retired coordinates to take the middle row and restored
byte-for-byte in the same command. No threshold moved, no station dropped, no gate changed.
