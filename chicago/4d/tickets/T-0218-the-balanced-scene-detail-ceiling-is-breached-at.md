---
id: T-0218
title: The 'balanced' scene-detail ceiling is breached at Lake and Canal, at both viewports
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded by #765, which raised all three scene-detail ceilings on the owner's ruling; every tier is inside its ceiling on dev
needs_bake: false
closed_at: 2026-09-10T04:20:10.244Z
claimed_run: null
---

The 'balanced' scene-detail ceiling is breached at Lake and Canal, at both viewports.

`tools/smoke_renderer.mjs` stage 4 holds each scene-detail tier to its own triangle ceiling at
the WORST of five named stands. **`balanced` fails at both viewports, and `full` fails at
desktop**, at the same stand — *Lake Street at Canal, east down the axis*, the long axial view
T-0135 added the stand set for.

**Measured 2026-08-27 on the published mirror**, and measured as an A/B rather than asserted: the
same tree was read twice, once with `dev`'s `data/frontage/town_street_edge.json` in the mirror
and once with T-0199's, so the delta is the street edge and nothing else.

| tier · viewport | ceiling | with dev's street edge | with T-0199's | delta |
|---|---:|---:|---:|---:|
| `balanced` · mobile 390×780 | 1,210,000 | **1,208,033** — 1,967 to spare, 0.16 % | **1,213,383** OVER | +5,350 |
| `balanced` · desktop 1280×800 | 1,210,000 | **1,253,630** — already over by 43,630 | **1,258,980** | +5,350 |
| `full` · desktop 1280×800 | 1,400,000 | **1,413,266** — already over by 13,266 | **1,418,616** | +5,350 |
| `full` · mobile 390×780 | 1,400,000 | 1,366,289 | **1,371,639** — 28,361 to spare | +5,350 |
| `light` · mobile / desktop | 1,050,000 | passes | **807,943 / 859,229** | +~840 |

**The layer costs 5,350 triangles at that stand, to the triangle, at every tier and both
viewports** — which is what an A/B is for. `light` is the exception, because it distance-culls
the derived furniture (T-0150) and most of the new walk is beyond its reach.

**RE-MEASURED 2026-08-27 AFTER MERGING dev's #384, #387 and #394**, because the town shrank
under them: `balanced` at mobile now reads **1,210,762 of 1,210,000 — over by 762 triangles,
0.06 %**. T-0179's roof forms and T-0022's log walls between them gave back most of the
5,350 the street edge costs. The breach is real and it is small, and small is the whole
problem: this tier has been inside its ceiling by a rounding error for a week.


**Read the first row before anything else.** On desktop BOTH failures are `dev`'s and predate any
of this: 43,630 and 13,266 triangles over, with T-0199's street edge not in the tree. On mobile
`dev` stood **1,967 triangles — 0.16 % — inside** the `balanced` ceiling, and T-0199's 82.8 m of
extra plank sidewalk (the South Water repair the owner's density ruling unblocked) costs 5,350
triangles at that stand and takes it over. **A tier with 0.16 % of headroom is not a budget, it
is a coincidence**, and this is the third time the same thing has happened: T-0135 set these
ceilings on 2026-08-22 with *"about 6 % of headroom over the measured worst"* and the town has
eaten all of it in five days.

**`light` is fine and that matters**, because it is the one promise in the table made to a person
rather than to a number: 807,943 of 1,050,000 at mobile, 858,389 at desktop — 18–23 % under. The
objection T-0135 raised to raising `full` and `balanced` — that `light` was 65 % over at the time,
so moving the tiers above it would be *"a ceiling moved to fit the camera that flatters it"* — no
longer holds. T-0150's furniture distance-cull paid that debt.

**The two honest routes are the ones T-0135 named, and choosing is not the loop's.** Either a
conscious re-budget of `full` and `balanced`, argued at the definition site in
`renderers/web/js/main.js` `DETAIL` with the reasoning written there (AGENTS.md's 2026-08-21
ruling: *"or just raise the budget?"*, with `light` staying the floor), or the trim T-0149 and
T-0146 are open for — distance-culling or an LOD down a long street, which is what makes the
axial stand expensive in the first place. T-0135's own text says it: *"choosing between them is
the owner's… This is the measure. The move is his."* **T-0199 did not move it**, deliberately:
raising a ceiling to make a red go away inside a ticket about a sidewalk is exactly the defect
T-0135 was opened to end.

**Acceptance:** `scene detail 'full'` and `scene detail 'balanced'` are green at the worst stand
at BOTH viewports on the published mirror, by a re-budget argued at the definition site with the
measurement above beside it OR by a trim measured against these figures — never by moving a
ceiling to fit one camera, and never by thinning what a layer claims to be (T-0056's rule).
`light` stays inside its own ceiling either way, and whatever headroom the answer leaves is
stated as a percentage so the next parcel knows what it is spending.

**Links:** T-0135 (the stand set and the last re-argument) · T-0147 (re-lower once the trims
land) · T-0149 (win the floor back by trimming the axial view) · T-0146 (merge far chunks) ·
T-0115 (the tier ledger) · T-0089 · T-0199 (where this was measured).

---
## 2026-08-28 — RE-READ on `dev`, and both the size of the breach and the stand have moved

`tools/measure_detail_ceilings.mjs --only desktop`, published mirror, `origin/dev` at
`a9a3a2f9`. Taken while working T-0214, beside a branch that changes no geometry a gate
stand can see — the two trees agree to the triangle at four of the five stands, which is
what makes this `dev`'s reading rather than a branch's:

| tier | ceiling | worst | stand |
|---|---:|---:|---|
| `full` | 1,400,000 | 1,376,419 PASS by 23,581 | the forks, from Wolf Point |
| `balanced` | 1,210,000 | **1,213,481 — OVER by 3,481** | the forks, from Wolf Point |
| `light` | 785,000 | 755,194 PASS by 29,806 | Lake at Canal, east |

(Read twice, four hours apart, either side of T-0209: at `a9a3a2f9` the breach was 5,290
at the same stand, at `c39167b4` it is 3,481. The stand does not move between them.)

**Two things have changed since this ticket's own table.** The breach is **3,481**, not
43,630 — the town has shrunk under it. And **the worst stand is no longer the axial
view**: Lake at Canal now reads 1,197,353, inside the ceiling by 12,647, while *the forks,
from Wolf Point* has become the binding frame at both `full` and `balanced`. A run that
goes looking for these triangles down the Lake Street axis will not find them. Mobile
390x780 passes all three tiers by 75,190–113,179.

`light`'s draw-call floor (T-0247) is a separate red and is untouched by this reading.
