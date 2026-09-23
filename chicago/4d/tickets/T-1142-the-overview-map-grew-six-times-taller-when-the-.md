---
id: T-1142
title: The overview map grew six times taller when the ground did: a fixed frame, a window that moves with you, and a pop-out for the whole field
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-15
pr: 1354
claimed_by: run 9/15/2026, 8:17:38 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T14:03:04.678Z
claimed_run: null
---

The overview map grew six times taller when the ground did: a fixed frame, a window
that moves with you, and a pop-out for the whole field.

**The owner, 2026-09-15:** "Can you add a ticket and work it now to adjust the viewport
in the navigator map, it is large now and I want it the same size as earlier just make
it a moving viewport so you can just see around you in the same size as before, but if
you want you could pop that map out and see the full map".

## Why it grew, measured

`js/navigation.js resize()` pins the inset's WIDTH and derives its HEIGHT from the
aspect ratio of the whole heightfield:

```js
logicalWidth  = window.innerWidth <= 560 ? 188 : 248;
logicalHeight = Math.max(76, Math.round(logicalWidth
  * (bounds.nMax - bounds.nMin) / (bounds.eMax - bounds.eMin)));
```

So the widget is a function of the field, and three tickets grew the field this week.
Reading `cols`/`rows`/`cell_m` out of every committed
`data/terrain/epochs/e1834_harbor_cut/heightfield.json` and carrying them through the
renderer's own `widthM`/`depthM`, which span `(cols - 1)` cells rather than `cols`:

| landed | field | inset at 248 px wide |
| --- | --- | --- |
| through 2026-09-12 | 2 020 x 800 m | 248 x **98** px |
| 2026-09-13 (T-1067) | 2 020 x 930 m | 248 x 114 px |
| 2026-09-14 (T-1123, north to +1120) | 2 020 x 1 650 m | 248 x 203 px |
| 2026-09-14 (T-0464, south to Cermak) | 2 020 x 4 920 m | 248 x **604** px |

**98 px to 604 px — 6.2x taller** in two days, and on a 780 px-tall phone the mobile
inset went 76 -> 458 px, more than half the screen. Nothing about the map changed; the
ground did, and the map was written to be its shadow.

The zoom got worse in the same move, which is the other half of what the owner is
seeing: the whole 4 920 m field squeezed into a fixed 248 px width means the town you
are standing in is a smear at the top of a long strip.

## What to build

1. **A fixed frame.** The inset returns to the footprint it had before the field grew
   — **248 x 98** on desktop, **188 x 76** on a phone — and stays there whatever the
   ground does next. These are not invented numbers: they are what the formula above
   produced on the 2026-09-12 field, so "the same size as earlier" is exact.

2. **A window that moves with you, at the scale it had before.** Rather than squeezing
   the field into the frame, the frame shows a window of ground centred on the visitor
   at the pre-growth scale of **2 020 m across 248 px** — the same metres per pixel
   the map had on 2026-09-12, so a block is the size it used to be. The window clamps
   to the field, so it never shows ground that is not there, and it letterboxes rather
   than stretching if a span ever exceeds the field. The field has only grown
   north-south, so in practice today the window sits still east-west and slides north
   and south, which is precisely the axis that broke.

3. **A pop-out for the whole field.** The frame opens to an overlay that draws the
   ENTIRE field, fitted to the screen, carrying the visitor's arrow and a rectangle
   marking where the inset's window sits inside it. Opened by clicking the inset and by
   a key; closed by Escape, by the backdrop, and by its own close button. This is where
   "renders the whole heightfield" now lives — the claim is not dropped, it moves.

4. **Both are one scale-invariant mechanism.** Neither the inset nor the pop-out may
   re-acquire a dependence on the field's aspect ratio, because South Through Time
   (T-0466) widens the field to four kilometres and would reintroduce exactly this bug.

## Acceptance: (state it before working — the definition of done, never weakened to pass)

1. The inset canvas is **248 x 98** CSS px on a desktop viewport and **188 x 76** on a
   390 px-wide one, asserted against the live element, and those numbers do NOT move
   when the heightfield's rows change. A drift guard stands on the constants so a
   future edit that re-derives the height from `bounds` fails a test rather than
   shipping.
2. The inset is a **moving window**: with the visitor teleported to two positions
   1 000 m apart in north, the canvas signature differs AND the ground under the marker
   is the ground at that position — the marker does not simply slide over a static
   image of the whole field.
3. The window **clamps**: standing at the extreme south and extreme north edges of the
   field, the inset shows no out-of-field fill beyond the letterbox case, and the
   marker moves toward the frame edge instead of the window running past the data.
4. The **pop-out** opens from the inset and from the keyboard, shows the whole field
   (its drawn extent spans the full `nMax - nMin`), carries the visitor arrow and the
   window rectangle, and closes by Escape. Focus returns to the inset on close.
5. `tools/smoke_renderer.mjs` covers 1-4 at **both** viewports with **zero
   pageerrors**, and the existing `overview map renders the whole heightfield` check is
   re-pointed at the pop-out rather than deleted.
6. The settings toggle that hides the map still hides both the inset and the pop-out,
   and the pop-out cannot be opened while the map is switched off.
7. In-app help names the new key, so the pop-out is discoverable without reading the
   source.
