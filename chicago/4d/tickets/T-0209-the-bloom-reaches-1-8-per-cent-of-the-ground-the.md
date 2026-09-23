---
id: T-0209
title: The bloom reaches 1.8 per cent of the ground the sward covers
state: done
epic: FLORA
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-26
closed: 2026-08-28
pr: 445
claimed_by: run 8/28/2026, 2:53:59 AM CT
blocked_on: null
needs_bake: false
---

The bloom reaches 1.8 per cent of the ground the sward covers.

Measured by T-0034 (`node tools/measure_bloom_headroom.mjs`, desktop, full detail):

| ring | outer radius |
|---|---|
| forb ring | 25.40 m |
| **head ring** | **23.65 m** |
| far band | 62 m, then 175 m |

A flower head is drawn nowhere past **23.65 m**, and the sward itself is carried to **175 m** as
aggregate clump cards which carry no head at all. So the bloom covers **1.8 %** of the ground the
sward covers, and the other 98 % of a July prairie is grass-coloured whatever its records say is
flowering on it. **This is the bar that governs how much bloom a visitor sees, and it is a
distance, not a density** — T-0034 spent the whole of the lattice's remaining 24 % and the frame
past twenty-four metres did not change by a pixel.

**It is not simply a radius to raise.** Head instances cost geometry quadratically in the ring's
radius and two head sets already truncate at their cap (T-0208), so extending the head ring is
the expensive route and probably the wrong one. The route with a shape to it is the far band's
own card: a far card is an aggregate standing for several metres of matrix, and a flowering
community's card could carry its own bloom as COLOUR rather than as head geometry. What that
needs first is the plan→screen conversion R-W4c(b1) names as its second route and deliberately
skips — the flora records give bloom **in plan** (`density_per_ha` × `size_m`, 0.027–0.219 % on
the mesic prairie) and a frame reads bloom in **screen space** at an oblique pose, and nobody has
built the bridge. Without it a far card tinted by the plan figure is invisible and one tinted by
anything larger is invented.

**Acceptance:** a visitor standing at `prairie_west` sees bloom past twenty-four metres, and the
figure it is drawn at traces to committed records by a stated method — or the parcel closes with
the conversion measured and a number recorded, and says what it would take. Do not raise the head
ring's radius as the whole answer without the frame cost measured at both viewports.

Related: T-0034 (the measurement) · T-0208 (the head sets that truncate) · ROADMAP R-W4c(b1)
route 2 (derive the bar from the flora records) · T-0086 (the far band) · L137, L80.

---

## 2026-08-28 — SHIPPED. The bloom reaches 119.9 m, and the tint route is refused with a number

**Acceptance, both branches.** A visitor standing at `prairie_west` sees bloom past
twenty-four metres — the furthest drawn head goes from **26.4 m to 119.9 m** — AND the
plan→screen conversion R-W4c(b1) skipped is built, measured and recorded, which is what
says the other route may not be taken.

### What was actually wrong, and it was not the head ring's radius

The head ring hangs off the FORB ring, and the forb ring ends where the far band begins.
Past it the far band dealt **`graminoids` only** — so every flowering community past
~25 m was a hundred per cent matrix however its record read, and no card out there could
carry a flower because no card out there was a plant that has one. That is a routing
fault, not a budget one, and the whole of T-0034's "1.8 % of the ground the sward covers"
sits on it.

### The change, and it draws nothing new

`rebuildFar` deals the whole community. The split is made INSIDE the band the slot was
already occupied on — the slot is used when `u < matrixShare` exactly as before, and the
forbs take their own recorded share OF that range — so the far-card count is unchanged
(230 / 221 / 26 at the three stands, before and after) and so are the triangles those
cards cost. What changed is which plant a card stands for, and the head a flowering one
carries. Widening the occupied band instead would have bought the bloom with geometry,
which is the budget this ticket was told not to spend.

### The conversion, and why it refuses the tint route (`tools/measure_far_bloom.mjs`)

Look across a prairie from eye height: at fifty metres the sight line is 1.9° below
horizontal, so the canopy is seen edge on as a wall and every pixel is the first element
the ray meets. A flower's share of that wall is its share of the community's
**silhouette-area density**, and the depth of the wall cancels out of the ratio, so the
figure needs no constant that is not on a record:

| community | plan bloom | screen bloom | head reach min/med/max |
|---|---:|---:|---|
| `z01_wet_prairie` | 0.417 % | 0.126 % | 21.6 / 79.3 / 216.2 m |
| `z02_mesic_prairie` | 0.093 % | **0.047 %** | 19.8 / 50.5 / 72.1 m |
| `z03_sedge_meadow` | 0.064 % | 0.030 % | 50.5 / 79.3 / 115.3 m |
| `z09_sand_prairie` | 0.018 % | 0.013 % | 16.2 / 46.9 / 50.5 m |

**Five parts in ten thousand is under the eighth bit of an 8-bit channel.** A far card
tinted by that figure is invisible and one tinted by anything larger is invented, which
is exactly what the ticket said and is now a number rather than an expectation.

**A head is not an area, though — it is a saturated MARK, and a mark reads while it
covers a pixel.** The camera is 62° vertical, so the gate's viewports carry 721 (390×780)
and 739 (1280×800) pixels per radian; a head of `size_m` falls under one pixel at
`size_m × 721` m, the phone setting the bar because mobile is a release gate. That reach
is per RECORD, not per community — `silphium_laciniatum`'s 0.10 m head carries 72 m and
`dalea_purpurea`'s 0.0275 m thimble 20 m — which is why the far bloom thins by species as
it recedes instead of ending on a circle.

### The reach, drawn (`tools/measure_far_bloom.mjs`, desktop, published mirror)

| stand | heads | furthest | > 24 m | > 40 m | far cards |
|---|---:|---:|---:|---:|---:|
| `prairie_west` before | 1,968 | 26.4 m | 87 | 0 | 230 |
| `prairie_west` after | 2,441 | **119.9 m** | **528** | **174** | 230 |
| `prairie_south` before | 1,122 | 25.9 m | 104 | 0 | 221 |
| `prairie_south` after | 1,556 | **130.4 m** | **525** | **274** | 221 |

`river_bank` is unchanged at 45 heads: the marsh carries one flowering record and its
reach is 27 m.

### What it costs at the release gate's own five stands

`tools/measure_detail_ceilings.mjs`, this branch against a clean `origin/dev` worktree,
both viewports, worst stand of T-0135's five:

| viewport | tier | dev | this branch | delta |
|---|---|---:|---:|---:|
| desktop | `full` | 1,378,215 | 1,378,319 | **+104** |
| desktop | `balanced` | 1,215,290 | 1,215,381 | **+91** |
| desktop | `light` | 756,144 | 756,144 | **0** |
| mobile | `full` | 1,286,821 | 1,291,013 | +4,192 |
| mobile | `balanced` | 1,134,810 | 1,135,203 | +393 |
| mobile | `light` | 708,894 | 708,894 | **0** |

It is nearly free at the town stands because the bloom is out on the prairie, which is
where the ticket asked for it. Five of the six readings PASS with 21,681 to 113,179 of
margin.

**`balanced` on desktop is OVER — and it is over on `dev` by 5,290 without this branch.**
Measured on both trees with the same instrument in the same hour. This branch adds 91 of
that 5,381, which is 1.7 % of a breach it did not make. Filed as its own ticket rather
than fixed here, because the breach is at *the forks* and the two open tickets on the
subject (T-0203, T-0218) both name Lake and Canal.

**`light` is bit-identical at both viewports, and that is deliberate.** The phone tier
carries no far bloom at all: `light` is where the 80-call floor binds — already breached
at 83 on an unmodified `dev` (T-0248) — and a head archetype the far band lights up where
the near rings had none is a new draw call, not just more triangles. So the floor reads
85 desktop / 79 mobile on this branch, which is what `dev` reads.

### What it did not do

`flora-head-raydroop` reaches its instance cap at `prairie_west` when the far bloom is on.
The near rings are filled FIRST — `rebuildFar` runs after `rebuildGround` and
`rebuildForbs`, so near bloom can never be starved by far bloom, and the 0–20 m head count
is unmoved at 1,364 → 1,368. The truncation is the far band's own tail and it belongs to
**T-0214**, which is already open on exactly this for two other archetypes.
