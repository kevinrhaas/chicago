---
id: T-0249
title: The light tier's 80-call floor is breached on dev at 83 calls, the day after T-0147 restored it
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: null
claimed_by: null
blocked_on: Duplicate of T-0247, filed by a sibling slice against the same dev red hours earlier. Same measurement, same 83-of-80 at Lake and Market; T-0247 is the one to work. Withdrawn on the merge that discovered the collision rather than left in the owner's queue twice.
needs_bake: false
---

The light tier's 80-call floor is breached on dev at 83 calls, the day after T-0147 restored it.

Measured 2026-08-27 on clean `origin/dev` @ `2ab3065a` (`steward-runner`, 4 cpu), while
gating T-0183. `SMOKE_VIEWPORT=desktop SMOKE_STAGE=4 node tools/smoke_renderer.mjs --published`:

    FAIL  desktop 1280x800: the light tier draws inside its 80-call floor at the worst
          stand — 83 calls at light, worst stand Lake and Market, the corner itself —
          floor 80, the count this project chose before the 2026-08 content landed,
          restored by T-0147 once T-0150, T-0146 and T-0223 had trimmed the axial view

Triangles are comfortable at every tier in the same reading — `light` 746,060 of 785,000,
`balanced` 1,201,344 of 1,210,000, `full` 1,369,931 of 1,400,000. **This is a draw-call
breach alone, and it is three calls.**

The sequence is worth stating because it is nobody's mistake. T-0147 (PR #413) restored the
80-call floor on the day the trims paid for it, having measured 75 calls at `light`. T-0240
then landed Randolph Street's edge, and the walks, crossings and fences of a fourteen-face
street are what the other three calls are. Each step was measured and green on its own
branch; the floor went over at the join.

**IT IS RED FOR EVERY BRANCH.** Desktop part 4 is the leg that reads it, so every PR into
`dev` inherits this until it is answered — which is the thing T-0223 named as the reason a
gate that is red for everyone reports nothing about anybody.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`light` is back inside 80 calls at the worst of the five stands, at both release viewports,
measured with `tools/measure_detail_ceilings.mjs` — **or** the floor is re-argued at `DETAIL`
in `renderers/web/js/main.js` with what it now buys and what stops the next street breaching
it, which is the harder answer and needs the owner. Do **not** weaken the assertion in
`tools/smoke_renderer.mjs`: T-0147 restored that number precisely because it had been
weakened once already.

**Links:** T-0147 (restored the floor, and measured 75) · T-0240 (Randolph's street edge) ·
T-0146 · T-0223 · T-0190 (the second street tier the ceiling refuses).
