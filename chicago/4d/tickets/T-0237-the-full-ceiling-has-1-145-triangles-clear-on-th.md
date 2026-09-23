---
id: T-0237
title: The full ceiling has 1,145 triangles clear on the published mirror, twelve hours after T-0229 raised it
state: open
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

The full ceiling has 1,145 triangles clear on the published mirror, twelve hours after T-0229 raised it.

Measured 2026-08-27 on the T-0208 branch — a change that adds no geometry at all, nine words
of card prose — with `tools/measure_stand_budget.mjs` on the published mirror, desktop
1280 x 800, at T-0135's worst stand (Lake Street at Canal, east down the axis). The gate's own
five-stand sweep, run the same afternoon in `smoke_renderer.mjs` stage 4, reads the same
figure to the triangle.

| tier | ceiling | measured worst stand | clear |
|---|---:|---:|---:|
| `full` | 1,425,000 | **1,423,855** | **1,145** |
| `balanced` | 1,260,000 | 1,239,486 | 20,514 |
| `light` | 1,050,000 | 858,200 (at the forks) | 191,800 |

**T-0229 sized its raise at "measured worst stand plus about 0.6 %" — the smallest step that
clears the breach "and leaves an ordinary parcel room".** It was measured at 1,412,120 and set
at 1,425,000, so it bought 12,880 triangles of room. Read the same afternoon on the published
mirror, **11,735 of those 12,880 are already spent** and the tier stands 0.08 % under its
ceiling. Nothing was raised for the second time; content merged between the two readings.
`flora` alone accounts for most of it — T-0223's table read it at 9,389 and it reads **21,337**
here — and T-0223 filed that layer as "the ninth-largest and not the problem", which it still
is by share and is not by delta.

## Why this matters more than the number

**Every geometry-adding ticket in the queue's visible bands is blocked by it today.** T-0028,
T-0191, T-0192, T-0193 and T-0194 all add triangles at a stand that has 1,145 to give — so a
run that takes any of them cannot land a green `full` ceiling row, and would either park on
`hold` or reach for the sixth raise. That is exactly the state the queue's own
TRIANGLE BUDGET band header describes, and it is now measured rather than inferred.

**It also changes T-0229's expiry story.** That ticket's escape clause reads: *"If the cull
recovers materially less than 180,100, this ticket does NOT close by quietly keeping the raised
numbers."* The mirror image is now true as well — the raise it granted is 91 % consumed before
the cull has started, so T-0223's cull has to pay for the breach it was scoped against **and**
for what has landed since.

## Acceptance

`full`'s headroom at the worst of T-0135's five stands is stated as a policy rather than
discovered by the next parcel that breaches it: either T-0223's cull lands and the measured
headroom is re-read against it, or the +11,952 that arrived after T-0229's reading is
attributed layer by layer with `tools/measure_stand_budget.mjs` and the queue says which
tickets that leaves runnable. **Not by raising a ceiling** — a sixth raise is what T-0223,
T-0229 and the count written into `main.js` all exist to make harder.

**Links:** T-0223 (the layer table and the costed cull) · T-0229 (the raise, and its expiry) ·
T-0147 · T-0135 (the five stands and the instrument) · `tools/measure_stand_budget.mjs` ·
`renderers/web/js/main.js` `DETAIL`.
