---
id: T-0461
title: The Tremont House's goods are laid on lot 7, which its own placement point falls outside — one building's goods on another lot's frontage
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-03
pr: 677
claimed_by: run 9/2/2026, 11:52:30 PM CT
blocked_on: null
needs_bake: false
---

Exposed by the owner's 2026-08-31 ruling on **T-0426**. That ruling kept the
street-lining fence where the lot fronts, which is right — and it leaves this,
which T-0426 had already measured and could not fix without deciding it.

## The fact

`tremont_house_1`'s own placement point is **(687.8, −91.4)**, which falls
**1.5 m EAST of lot 7** — so the Tremont House improves nothing on that lot. Its
GOODS, though, are laid on ground **inside** lot 7: the longest group on the
goods layer, four casks, an empty on its side and two cases, at **y = −101.11**.

**One building's goods are standing on another lot's frontage.** Nothing in this
project says they may, and nothing says they may not; it has simply never been
asked.

## Why it surfaced now, and why it is not the clothing store's fault

PR #562 stands the New York Clothing Store on lot 7. Under T-0426's ruling the
lot is improved and takes its board fence at its Lake frontage — 24.7 m of it, on
the frontage line at y ≈ −103. The smoke stands a walker at (684.9, −104.3) to
check `the goods reach the screen from the footway`, and the fence is now between
that walker and goods that were never on this lot's business.

The reading collapses from **mean 3.01 / worst 58** on `dev` to **mean 0.19 /
worst 22** with the shop standing, and PR #562 is parked on it.

**The collision was always latent.** The pass `dev` has enjoyed is an accident of
where one origin point fell: had `tremont_house_1` been placed 1.5 m west, lot 7
would have been improved all along and the fence would have stood there before
any clothing store existed.

## Three ways out, none of them decided here

1. **The goods move to their own lot.** If a building's goods belong on the
   ground its placement point stands on, the Tremont House's belong east of lot
   7, and the rule that lays them is what changes.
2. **A lot's frontage is exclusive.** A lot that carries a fence may not also
   carry a neighbour's goods, and the goods layer refuses in writing where it
   would.
3. **The smoke's stand is wrong.** The walker at (684.9, −104.3) is reading
   across a lot boundary, and the assertion should stand where the goods'
   own building fronts.

**Acceptance:**

1. Which of the three is decided, in writing, with the count of other records
   that move under it. This is a rule over the goods layer and it will not only
   touch the Tremont House.
2. **The census is taken before and after**, the way T-0426's post fix was: the
   goods layer's own counts on `dev` and on the fix, so nothing moves silently.
3. `the goods reach the screen from the footway` reads at or above its `dev`
   figure of mean 3.01 / worst 58 with PR #562's clothing store standing —
   **without weakening the assertion or moving its stand to avoid the case**,
   unless option 3 is the one chosen and is argued on its own merits.
4. **PR #562 is re-read against the result.** It is parked on this and on
   nothing else now that T-0426's post half has landed.

---

## THE RESOLUTION — NONE OF THE THREE, BECAUSE THE PREMISE IS FALSE

The ticket offered three ways out and asked for one to be decided. Measuring it
first dissolves the question: **the goods are not on another lot's frontage.**

`tremont_house_1`'s front runs 15.24 m west from its origin. Lot 7 of
`blk_south_water_clark` spans x 661.41–686.34; the footprint spans 672.58–687.82.
**13.76 m of that front — 90% of the building — stands on lot 7.** What falls
1.48 m outside is the record's placement ORIGIN, and that origin is the
south-EAST corner of the footprint, not its middle. The goods stand 0.55 m off
the Tremont House's own south wall, on ground the Tremont House itself occupies.

So there is no goods rule to change, no exclusivity rule to write, and nothing
wrong with where the smoke stands its walker. The fault was in the question every
lot rule was asking.

### What was actually wrong

`_fence_runs` and `_edge_hitching` both read `_inside(b["at"], lot["polygon"])`.
`at` is the placement origin, and across `data/sidecars/1835/` it is **a footprint
VERTEX on 366 of the 367 placed records, and the centroid on none of them** — it
lies strictly inside its own outline on only 188. Whether a lot was improved was
therefore decided by where one CORNER landed.

`_stands_on` asks whether the committed footprint and the lot share ground. It is
monotone by construction — a point inside the lot is inside the overlap too — and
measured over all 144 platted lots it **adds 28 occupancies and removes none**;
125 improved lots become 131.

### The census, before and after (acceptance 2)

The goods layer does not move: `data/yard/town_trade_goods.json` is byte-identical.
Not one cask, crate or wagon changes, which is the strongest form the census can
take — this was never a goods fault. Everything that moves is in
`data/frontage/town_street_edge.json`:

| | dev | fix |
|---|---|---|
| street-lining fence runs | 35 (1669.03 m) | 32 (1641.85 m) |
| street-edge hitching posts | 15 | 17 |
| refusals | 75 | 77 |
| walks / crossings | 51 / 39 | 51 / 39 |

All three fences go under the clause already on the books — a wall inside the
3.0 m a street fence needs IS the street wall: lot 7 (`tremont_house_1`, 2.40 m),
`blk_lake_dearborn` lot 2 (`mason_blacksmith_shop`, 0.55 m) and
`blk_south_water_lasalle` lot 3 (`…_a1_06`, 1.61 m). Both new posts are buildings
with a trade the rule already accepts and a door on the face they stand on
(`tremont_house_1`, `exchange_coffee_house`). Six further refusals keep their
count and change their WORDING, from "no committed building stands on this
platted lot" to the building that does.

**T-0426's ruling is untouched.** A lot that fronts a street still takes its
street fence at that frontage whatever way the building faces. Only which lots
have a building standing on them changes.

### Acceptance 3 — measured, with #562's clothing store standing

`the goods reach the screen from the footway` reads **mean 3.01, worst 58** at
mobile 390×780 with PR #562's branch merged onto this fix — *exactly* its `dev`
figure. The assertion is unweakened and its walker still stands at
(684.9, −104.3). The 24.7 m fence never appears: with both buildings on lot 7 the
setback is 2.40 m and the lot is refused in writing.

### Acceptance 4 — PR #562 is re-read

**#562 is unblocked by this.** It was parked on this and nothing else. One thing
is left for it to do on its own account: it moves the frontage census to 19 posts
and 86 refusals against this branch's 20 and 85 (the clothing store adds a
refusal and, under T-0426's face rule, takes no post), so #562 must update the
two counters in `tools/smoke_renderer.mjs` with its own bookkeeping note before
it merges. That is #562's line to write, not this ticket's.

### One defect found on the way, and fixed here

`_fence_runs` took the minimum setback over every building on the lot and then
named `here[0]` in the refusal. **Ten committed refusals were already naming the
wrong building against a real distance.** Latent while a lot could only hold what
one corner landed in; under `_stands_on` it would have printed the Tremont
House's 2.40 m against the New York Clothing Store's name. The setback and the
building it came from are now taken together.
