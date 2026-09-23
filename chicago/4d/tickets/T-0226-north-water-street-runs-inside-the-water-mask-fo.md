---
id: T-0226
title: North Water Street runs inside the water mask for 477 m and draws no ribbon at all
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 430
claimed_by: run 8/27/2026, 10:13:16 PM CT
blocked_on: null
needs_bake: false
---

North Water Street runs inside the water mask for 477 m and draws no ribbon at all.

Found working T-0184, by its joint probe's first reading. Three of North Water Street's six
authored bends — **[330, 66], [452, 75], [576, 86]** — stand on centreline the terrain's water mask
calls river. `renderers/web/js/streets.js` drops any panel whose centreline endpoint is wet, under
R-BUG4's own rule that a crossing is a bridge's job and a ford is not something a ribbon may paint,
so **no roadway is drawn on that street across the whole reach**. Measured with a half-metre walk
along the committed line (`terrain.isWater` at every step): **477.4 m of North Water Street's 843.3 m
is inside the mask, in ONE unbroken run from [200.2, 55] to [675.4, 95.7]** — 57 % of the street,
and it swallows three of its six bends. Nothing else in the street layer comes close: the fort road
has a 2.0 m nub of wet centreline at [809, 4] where it leaves the bank, and no other street has any.

It has presumably been like this since the water mask and the street record last moved
independently, and nothing had reason to look: the panel-accounting gate asks whether every panel
with a DRY centreline reached the ribbon, and every one of them did. A street whose centreline is
wet is invisible to that question by construction.

**Two readings, and this is research rather than a nudge.** Either the traced north bank runs too
far south along that reach — the bank there comes from the 1834 survey windows L-something records
under T-0106 — or North Water Street's own line, which grades its geometry `inferred`, is drawn too
far north. Both are recorded claims with sources behind them, so one of them has to be shown wrong
rather than moved to make the picture work — and 477 m is far too much to be a tracing wobble.

**Acceptance:** state which record is wrong WITH the evidence that says so — the bank tracing or the
street line — correct that one, and leave the other alone; a visitor can then walk North Water
Street from Wolf Point to the fort road on drawn roadway, with `tools/measure_road_joints.mjs`
reporting 0 bends refused for water where it reports 3 today; and if neither record can be shown
wrong, say so in `docs/RESEARCH/` and record the gap rather than nudging a line to close it.

**Links:** T-0184 (which found it) · T-0106 (the two 1834 survey windows the bank is traced from) ·
`tools/road_joint_probe.mjs` · `renderers/web/js/streets.js` (the centreline water test) · ROADMAP
**B-BUG4**.
