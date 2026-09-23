---
id: T-0277
title: The mid and forb rings' outer edges are re-priced for a density handover, now the reach statistic is honest
state: done
epic: FLORA
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1241
claimed_by: run 9/13/2026, 3:22:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T09:08:10.260Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34747356985
---

The mid and forb rings' outer edges are re-priced for a density handover, now the reach statistic is
honest.

**VISIBLE.** What a walker sees change is the sward's far edge: at `full` the last few metres of
grass and flowers are drawn through a 4x4 screen door — a band of dots resolved per pixel — and a
density handover replaces it with plants drawn whole, thinning out. It is the same repair T-0093
made at the near/mid boundary and T-0086 made at the far band's, on the two edges those two left.

**Why it is only askable now.** T-0187 priced this and took a different route, and its reasoning
is written into `TUNE` in `renderers/web/js/flora.js`: a spread of the full band took the mean
drawn reach from 26.81 m to 25.42 m at `full` and from 11.89 m to 9.64 m at `light` against a bar
of 11.60 m — so the smoke's boundary check preferred the dither. **Every one of those figures was
read at `fadeAt > 0.02`**, a coverage the screen door renders as nothing whatever for two instance
phases in three, which is T-0225. The gate now reads the boundary at 1/16 and carries the inset
that costs, so the comparison a spread has to win is a real one. It is not yet known to be
winnable: what T-0225 fixed is the instrument, not the price.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The cost of spreading `mid.band` and `forb.band` is RE-MEASURED against the corrected statistic,
  slot by slot, at both viewports — `tools/measure_sward_reach.mjs` prints the boundary the gate
  now reads, and the same simulation T-0187 ran is what has to be re-run against it.
- If it clears the bars, the two edges are spread (`spreadOuter` in `TUNE`, the `slotRing`
  arithmetic T-0093 already carries) and the smoke's boundary checks are green at both viewports
  with the figures recorded — and the screen-doored area at the verge, which
  `tools/measure_near_verge.mjs` measures, does not grow.
- If it does not clear them, the ticket closes with the measurement and the reason, and the ramp
  stays. It is NOT closed by widening a bar.

**Links:** `renderers/web/js/flora.js` (`TUNE.mid`, `TUNE.forb`, `ringsFor`, `slotRing`,
`handoverRank`) · `tools/smoke_renderer.mjs` (part 7, `seam`) · `tools/measure_sward_reach.mjs` ·
T-0225 · T-0187 · T-0093 · T-0086.
