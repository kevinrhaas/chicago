---
id: T-0223
title: The 'full' and 'balanced' ceilings are both breached on dev, with no parcel in flight that spends them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 411
claimed_by: run 8/27/2026, 1:54:47 PM CT
blocked_on: null
needs_bake: false
---

The `full` and `balanced` scene-detail ceilings are both breached at T-0135's worst stand, and
no branch in flight is spending them.

## 1. Measured 2026-08-27, published mirror, desktop 1280 x 800, Lake Street at Canal, east

`tools/measure_detail_ceilings.mjs`, which runs T-0135's five-stand sweep on its own and
reproduces bake run 32761900576's figures to the triangle.

| tier | ceiling | dev @ `e2056e97` (T-0117) | dev @ `29eebdef` | verdict today |
|---|---:|---:|---:|---|
| `full` | 1,400,000 | 1,390,060 @ 203c | **1,412,120 @ 204c** | **12,120 OVER** |
| `balanced` | 1,210,000 | **1,244,766 @ 201c** | **1,252,802 @ 202c** | **42,802 OVER** |
| `light` | 1,050,000 | 803,316 @ 70c | 838,742 @ 71c | passes, 20 % under |

Draw calls are inside the 215 budget at every tier and every stand. This is a triangle
problem alone.

## 2. WHAT ACTUALLY OCCUPIES THE BUDGET AT THAT STAND — the table nobody had

`tools/measure_stand_budget.mjs`, same tree, same stand. Each layer is hidden, two frames are
allowed to pass, `renderer.info.render` is read, and the layer is restored — so a layer's cost
is its colour pass AND whatever it adds to the sun's. The sun column is CONTROLLED: the whole
frame is re-read with `shadowMap.enabled = false`, and the per-layer column sums to that total
**exactly** at both tiers. The baseline re-read against itself is **0 triangles, 0 calls**.

**`balanced` — 1,252,802 of 1,210,000, 202 calls**

| layer | drawn | % of frame | calls | of which the sun | meshes |
|---|---:|---:|---:|---:|---:|
| **trees** | **360,926** | **28.8** | 9 | **180,100** | 5 |
| terrain | 249,185 | 19.9 | 22 | 0 | 31 |
| structures | 240,734 | 19.2 | 2 | 40,060 | 1 |
| frontage | 154,932 | 12.4 | 40 | 8,680 | 39 |
| enclosures | 105,888 | 8.5 | 48 | 6,892 | 48 |
| yard | 65,480 | 5.2 | 54 | 15,768 | 50 |
| streets | 45,192 | 3.6 | 6 | 0 | 3 |
| yard-ground | 12,892 | 1.0 | 4 | 0 | 4 |
| flora | 9,389 | 0.7 | 10 | 0 | 15 |
| boats | 3,200 | 0.3 | 2 | 1,600 | 1 |
| wharves | 2,760 | 0.2 | 2 | 1,380 | 1 |
| signage | 2,212 | 0.2 | 2 | 1,106 | 1 |
| **the sun's own pass** | **255,586** | **20.4** | 25 | — | — |

**`full` — 1,412,120 of 1,400,000, 204 calls.** Same order, two differences worth naming:
`trees` reads **442,110 (31.3 %), 220,692 of it the sun**, and `enclosures` reads **173,838
against `balanced`'s 105,888** — which is T-0068's zero-thickness pale doing exactly what it
was built to do, worth **67,950** at this stand. The sun's whole pass is **296,178 (21.0 %)**.

### Four things fall out of it, and none was known before

1. **The single largest consumer of the frame is not the town — it is the TIMBER, and half of
   it is a shadow.** `trees` holds 181,900 triangles in its buffers and draws **360,926**:
   essentially the whole layer, twice, once for the camera and once for the sun. Nothing is
   culled from it. `trees.js` builds the near timber as **four quadrant meshes**
   (`timber__q0…q3`) plus the horizon — five objects spanning kilometres — and the sun's box is
   **±240 m** (`DETAIL.shadowReachM`). A mesh whose bounding sphere touches that box is
   submitted whole, so the great majority of those 180,100 triangles are timber standing
   **outside the shadow box, casting nothing that any pixel of the shadow map can hold.**
   The comment at `trees.js` `mesh.castShadow = true` still reads *"the sun's shadow camera is
   only ±60 m around the walker … so this costs a shadow pass on the few stands actually near
   the visitor."* The reach has been ±240 m since T-0115, and the cost is not a few stands: it
   is **14.4 % of every frame at the worst one.**
2. **The sun costs a fifth of the frame** — 255,586 triangles at `balanced`, 296,178 at `full`,
   in 25 draw calls, and **86 %** of it is two layers (`trees` and `structures`), both of which
   are single objects too large for the shadow camera to cull.
3. **The derived furniture is a DRAW-CALL story, not a triangle story.** `frontage` 40 calls +
   `enclosures` 48 + `yard` 54 = **142 of the 202 calls for 26 % of the triangles.** That is
   T-0146's target and the table says it is aimed correctly — but it is not where the overage
   is.
4. **`flora` is not the problem and should stop being suspected.** 9,389 triangles, 0.7 %,
   instanced off 447 held. The sward has been the first suspect in three separate budget
   arguments; at the stand that actually fails it is the ninth-largest layer.

## 3. So: are the ceilings wrong, or is the content?

**Neither, yet — and that is the finding.** There are on the order of **180,000 triangles of
pure-loss shadow work** in the frame at `balanced`, spent on timber outside the box it could
cast into. Nothing is claimed by it: not a source, not a form, not a pixel. Removing it costs
the picture nothing that can be measured, which is the same test the sward LOD, the shadow
reach and T-0188's boards all passed. Re-basing a ceiling while that is in the frame would be
budgeting for work the renderer should not be doing, and it would be the fifth raise.

T-0149's own order says the same thing — *"only THEN consider lowering the ceilings back,
which is the point of the exercise: a ceiling that comes back DOWN after a trim is the
strongest evidence the trim worked."*

## 4. The plan, costed, in order — and it is more than one run

1. **Let the sun's camera cull the timber** (biggest lever, ~180,100 at `balanced` / ~220,692
   at `full`, upper bound). Chunk `timber__q0…q3` finely enough that the shadow camera can
   reject what lies outside its ±240 m box, or decide `castShadow` per chunk per frame from the
   box the rig already tracks. **Watch the draw calls**: the colour pass must NOT gain 40 calls
   to save the shadow pass, and 202 of 215 is what there is to spend — so the chunking wants to
   be shadow-only, or paired with T-0146. Frame-signature cost must be measured, not assumed.
2. **The same question for `structures`** (40,060). R-W5a2 requires the untextured town to stay
   ONE batch in the COLOUR pass and that is not up for revision; a shadow-only split is a
   different object and does not reopen it.
3. **`yard` (15,768 of sun on 54 calls)** — the wagons and barrels. T-0188's ledger already
   argued the standing/ground-hugging split for `frontage`; `yard` has never been asked.
4. **T-0146**, on the call count, which this table says is aimed at the right layers.
5. **Only then T-0147**, and a ceiling that comes back DOWN.

**This is more than one run** — item 1 alone is a renderer change with its own smoke, its own
frame-signature control and its own draw-call trade. Split it rather than half-doing it.

## Acceptance

(state it before working — the definition of done, never weakened to pass)

`full` and `balanced` are inside their ceilings at the WORST of T-0135's five stands on the
published mirror, at both release viewports, read by `tools/measure_detail_ceilings.mjs`, with
the per-layer reading above re-taken by `tools/measure_stand_budget.mjs` so the saving is shown
where it came from. Either

1. **a trim**, with the frame-signature cost measured the way T-0150 measured its own and the
   draw-call count held inside 215; or
2. **a conscious re-budget**, argued at `DETAIL` in `renderers/web/js/main.js` — where the old
   figure came from, what supports the new one, `light` untouched as the floor, and a stated
   answer to *"what stops this being the sixth raise"*.

Say which one it is. **Never weaken the assertion in `tools/smoke_renderer.mjs` to make the red
go away** — the gate is not the problem.

## 5. Nothing in flight caused this

T-0126's branch was swept against its own base: **all fifteen readings — five stands x three
tiers — identical to the triangle and to the draw call**, 487,837 triangles in `assets/web/` on
both trees. #376, which adds no geometry either, reports the same figures. The spend is merged
content:

- **T-0098's branch read `balanced` at 1,209,926 of 1,210,000** — seventy-four triangles of
  headroom — at this stand, on dev @ `059aaf26`.
- **T-0095, T-0109, T-0106 and T-0117** merged next and cost **34,840** there.
- **T-0188** added six re-placed South Water buildings, +66.8 m of plank walk and three street
  fence meshes, and took the ground-hugging boards out of the shadow map. Net at `balanced`:
  **+8,036**. At `light`, where that lever does not reach, the content alone reads **+35,426**.
- `full` had **never been over before today**.

Every PR's `smoke (desktop, 3-4)` leg fails until this is fixed, on branches that did not cause
it. That is the cost of leaving it.

**Links:** T-0135 (the five stands and the instrument) - T-0190 (the street tier the ceiling
refuses) - T-0147 and T-0149 (win the axial frame back, then let the ceilings follow) - T-0089
(the same shape at `light`, 2026-08-18, and the first branch charged for a breach it did not
open) - T-0056 - T-0115's ledger - `renderers/web/js/main.js` `DETAIL` -
`renderers/web/js/trees.js` (the stale +/-60 m comment at `mesh.castShadow`).

---

## WHAT WAS DONE — step 1, and it is A TRIM, not a re-budget

The plan's item 1. `renderers/web/js/trees.js` builds the near timber on a **120 m
lattice** — 71 cells carry timber — instead of four world quadrants, and submits the whole
lattice as **one `THREE.BatchedMesh`**. That is what makes fine chunks affordable: three
culls per chunk against the view frustum in `onBeforeRender` AND against the shadow camera
in `onBeforeShadow`, and issues the survivors as a single `WEBGL_multi_draw`. The ticket's
own warning — *"the colour pass must NOT gain 40 calls to save the shadow pass"* — is
answered by the draw calls going DOWN.

Items 2-5 (`structures`' shadow split, `yard`, T-0146, T-0147) are untouched and stay open.

### The reading, same instrument, same runner, both trees

`tools/measure_stand_budget.mjs`' method — hide the layer, let two frames pass, read
`renderer.info.render`, restore; then clear `castShadow` on it and read again — at
`balanced`, **Lake Street at Canal, east down the axis**, desktop 1280x800, published
mirror. `dev` here is `d9b437dd`, re-read on this runner rather than quoted from the table
above (which was `29eebdef`).

| | dev @ `d9b437dd` | this branch | delta |
|---|---:|---:|---:|
| the whole frame | 1,239,486 / 199 calls | **1,073,218 / 193 calls** | **-166,268 / -6** |
| `trees`, whole cost | 337,692 / 9 calls | **171,424 / 3 calls** | -166,268 / -6 |
| ...of which the sun's pass | **168,464 / 4 calls** | **46,464 / 1 call** | **-122,000 / -3** |
| everything else (`trees` hidden) | 901,794 / 190 calls | **901,794 / 190 calls** | **0 / 0** |
| baseline re-read against itself | 0 tris, 0 calls | 0 tris, 0 calls | — |

The fourth row is the control that matters: with the layer hidden the two trees agree **to
the triangle and to the draw call**, so the whole delta is the timber and nothing else moved.
The layer still OWNS 169,228 triangles on both trees — no geometry was removed, thinned or
retyped. 53 of the 71 cells are drawn at that stand.

### Acceptance, read by `tools/measure_detail_ceilings.mjs` on the published mirror

Worst of T-0135's five stands, **both release viewports**:

| tier | ceiling | desktop 1280x800 | mobile 390x780 | the ORIGINAL ceiling |
|---|---:|---:|---:|---:|
| `full` | 1,425,000 | **1,252,519** | **1,145,025** | 1,400,000 — inside it |
| `balanced` | 1,260,000 | **1,083,932** | **1,020,396** | 1,210,000 — inside it |
| `light` | 1,050,000 | **702,212** | **649,224** | 1,050,000 — inside it |

`every tier inside its ceiling`, at both viewports, and inside the ceilings that stood
BEFORE T-0229's raise as well. Worst draw-call count 195 of 215 (desktop) and 186 (mobile),
against dev's 204. **T-0229's expiry condition is met** — putting the two numbers back is
that ticket's own change, and `DETAIL` in `main.js` now records the reading it needs.

### Where the estimate landed

The plan's upper bound was ~180,100 at `balanced`. The sun's pass over the timber fell by
**122,000** of it; the remaining ~46,000 is timber genuinely inside the +/-240 m box plus one
chunk-radius of lattice margin. The colour pass gave back another ~55,900 that was not
budgeted for at all — the quadrants were never culled from the camera either. The `DETAIL`
block predicted "roughly 1,232,000 (full) and 1,072,000 (balanced)"; measured 1,252,519 and
1,083,932, within 2 %.

### What is NOT claimed

`renderer.info` counts a multi-draw as one call because it is one GL call, but the driver
still issues a sub-draw per surviving chunk. The lattice is 120 m rather than 40 for exactly
that reason: the shadow saving is nearly all won by the first halving and the sub-draw count
is what pays for the rest. The frame-signature control is structural rather than
photographic — three's per-chunk cull is conservative (bounding sphere against the frustum),
so it can only drop chunks that contributed no pixel, and the shadow camera clipped the same
timber at +/-240 m before this change anyway. `tools/measure_stand_budget.mjs`' own full
thirteen-layer sweep was NOT re-run: it does not finish inside this runner's per-command
ceiling. The three-reading probe above uses its method on the one layer that changed.
