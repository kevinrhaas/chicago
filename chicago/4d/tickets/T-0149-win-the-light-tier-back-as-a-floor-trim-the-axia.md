---
id: T-0149
title: Win the light tier back as a floor: trim the axial view instead of carrying it
state: split
epic: RENDERING
requested_by: owner
seen: true
effort: L
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-22
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

Win the light tier back as a floor: trim the axial view instead of carrying it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Win the light tier back as a floor: trim the axial view instead of carrying it.

**Opened 2026-08-22 in the same commit that raised the ceilings**, so that what the raise
cost is a ticket rather than a regret.

## What happened

T-0135 replaced a one-camera gate with a five-stand sweep and found the town **32 % over at
`full`, 27 % at `balanced` and 65 % at `light`** — at viewpoints the Go-to menu already
offers a visitor. The owner ruled *"raise it, I think"*, and the ceilings were raised to
carry the worst stand: `full` 1,000,000 → 1,400,000, `balanced` 900,000 → 1,210,000,
`light` 600,000 → **1,050,000**, draw calls 140 → 215.

**`light` at 1,050,000 is heavier than `full` was the day before.** The bottom rung of the
ladder now costs more than the old top rung, which means the tier a weak machine boots into
is no longer a floor anyone can be promised — it is just the cheapest of three expensive
settings. The scene-detail control still works (about 25 % from `full` to `light` down Lake
Street) but it no longer reaches down to a machine that needs it to.

That is the debt this ticket exists to pay. Nothing is wrong with the raise: it made a
dishonest number honest. What it did not do is make the frame cheaper.

## Why the axial view is the target

The worst stands are **Lake Street at Canal looking east** (1,320,377 tris, 200 calls at
`full`) and **the forks from Wolf Point** (1,318,202). Both are long open sightlines where
nothing occludes anything: the whole town is in frustum and every chunk becomes its own draw
call. The dense corner at Lake and Market is 200,000 triangles cheaper, and the reference
stand cheaper still.

**The chunking work of 2026-08-21 is implicated and should not be reverted.** Splitting the
frontage, enclosure and yard layers so the frustum can skip what is behind you is a large win
at an ordinary stand — it is what took `light` from 584,715 to 557,859 while ADDING ground.
It is a loss only where nothing can be skipped. So the answer is not fewer chunks; it is
something that reduces what a long sightline has to draw at all.

## What to try, roughly in order of value

1. **Distance culling / an LOD for the furniture layers down a long street.** Fences, plank
   walks, yard goods and signboards at 300 m are a few pixels each and cost full geometry.
   A distance threshold at `light` — or a cheap far form, as the pale already has (4 triangles
   instead of 10) — is the obvious first cut.
2. **Merge small far chunks back together.** Chunking pays only while things are being culled;
   beyond some distance the frustum is skipping nothing and the calls are pure loss. A
   distance-aware chunker could draw far runs as one call and near runs as many.
3. **Re-examine the shadow pass at `light`.** It is already off for furniture (T-0115), but
   buildings and timber still cast at 120 m; the wagons ledger notes the shadow pass is ~28 of
   the enclosure layer's 45 calls.
4. **Only then consider lowering the ceilings back**, which is the point of the exercise: a
   ceiling that comes back DOWN after a trim is the strongest evidence the trim worked.

## Acceptance

`light` draws inside a ceiling that is once again lower than `full`'s, at the worst of
T-0135's named stands, with the tier's promise restated where `DETAIL` is defined; the
chunking wins of 2026-08-21 are kept; and whatever the ceilings finish at, they are the
worst-stand numbers rather than the reference stand's. Effort is **L** — this is a rendering
programme, not a run, and it should be split when it is picked up.

**Links:** T-0135 (the instrument and the five stands, with every reading) · T-0115 (the
detail tiers and the shadow trim) · T-0121 (the desktop stage now over its command ceiling
partly because of the sweep) · `renderers/web/js/main.js` `DETAIL` / `BUDGET` · the
2026-08-21 chunking parcels T-0067, T-0069, T-0064.
