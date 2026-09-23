---
id: T-0248
title: The light tier's 80-call floor was breached the run after it was restored, and dev has been red on it since
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

**WITHDRAWN THE MOMENT IT WAS FILED — duplicate of T-0247.** A parallel slice filed the
same defect against the same measurement minutes earlier; T-0247 is the live ticket and this
one carries no queue line. What is kept below is the one thing this filing adds and T-0247
does not have: the measurement showing why the obvious lever does not reach `light`.

The light tier's 80-call floor was breached the run after it was restored, and dev has been red on it since.

**Acceptance:** `light` draws inside 80 draw calls at the worst of T-0135's five stands at
BOTH release viewports, by a trim rather than by moving the bar — or, if the count is
argued up instead, the argument is made where `tools/smoke_renderer.mjs` sets it and it is
the owner's, not a run's. Either way the desktop stage-4 check stops being red on `dev`.

## The bar was restored on 2026-08-27 and breached the same evening

T-0147 put the floor back at 80 — *"the count this project chose before any of the 2026-08
content landed, not one fitted around today's reading of seventy-five"* — measured on dev
at `f7aca445`, where `light` read **76** calls at the worst stand (Lake and Market, the
corner itself). Its own entry named how thin that was: 75 before T-0194's hitching posts
merged, 76 after, *"one ordinary visible parcel spent a quarter of the margin"*.

**The next visible parcel spent the rest of it and then some.** T-0240 laid Randolph
Street, and `light`'s worst-stand call count went from 76 to **83**. Nothing recorded that,
because the dev gate is `check.sh` and the desktop smoke's stage 4 — where the assertion
lives — is a ten-minute Playwright leg that no PR runs by default (docs/PIPELINE.md § dev's
standing smoke result).

Measured on this run, `tools/measure_detail_ceilings.mjs` on the published mirror, the tool
whose whole warrant is that it reproduces the gate's own sweep to the call:

| tree | `light`, worst calls, desktop 1280x800 | floor |
|---|---:|---:|
| dev @ `2ab3065a`, clean | **83** at Lake and Market | 80 |
| T-0241 (Washington laid) | **86** at Lake and Market | 80 |

Mobile 390x780 is INSIDE it at both: 79 with Washington laid, which is why this is a
desktop-only red and why it is thin rather than structural.

## What T-0241 did about it, and deliberately did not

T-0241 took Washington's triangle cost off the `balanced` tier with an 800 m furniture
reach and left this bar alone, for two reasons. **It is not that branch's red** — dev was
already three over — and **the obvious lever does not reach it**: `far-merge.js` is what
gives calls back, and its floor is `FAR_M` = 340 m, derived as 240·√2 from the `full` and
`balanced` shadow box. Deriving it per tier instead (`light`'s box is ±120 m, so 170 m)
looks like the fix and is not: `CLUSTER_M` is 200 m and the two constants were chosen
TOGETHER, so a cluster that near subtends more than the 62° field and can never satisfy the
merge's whole-cluster-in-frustum condition. The band it would actually open at `light` is
about 311–350 m, where the T-0150 reach is already culling. That is worth writing down so
the next run does not spend an hour rediscovering it.

**The routes that might reach it**, none costed here: the street edge is chunked one mesh
per RUN of walk (`tools/generate_frontage_works.py`, and the coarser alternatives were
measured and refused on triangles at `light`); `light` could chunk that layer differently
from the tiers above it, which nothing does today; or the 80 is re-argued from the fact
that four streets of plank walk exist now and did not when it was chosen.

**Links:** T-0147 (restored the floor) · T-0240 (breached it) · T-0241 (measured it, and
why it left it) · T-0146 / `renderers/web/js/far-merge.js` · T-0150 · `tools/smoke_renderer.mjs`
§ "the light tier draws inside its 80-call floor".
