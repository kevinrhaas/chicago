---
id: T-0086
title: The sward ends at a radius instead of receding into the distance
state: done
epic: FLORA
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-18
pr: 249
claimed_by: run 8/18/2026, 3:34:46 PM CT
blocked_on: null
needs_bake: false
---

The sward ends at a radius instead of receding into the distance.

**The owner, 2026-08-18, on the T-0035 fix: "the plant rendering is much better! but in
certain scenes it does not look right and you can see them fade in when in long distance
view like this, would be nice if you could see them in the distance blurred faintly
further out."** Three screenshots, two stands: **South Water Street approaching Wells,
heading 084°** (the sward stops a few metres out and the whole far bank across the river
is bald), and **Wells Street approaching Lake, heading 185°** (tall grass and pink forbs
in the foreground, then a hard edge, then bare green ground running all the way to the
houses and the horizon).

## What is actually happening

Two symptoms, one cause — the flora field is a set of rings about the walker and
**nothing at all is drawn past the outermost one**.

- Ring radii (`TUNE`, flora.js): HIGH near 7.6 m / mid 27.0 m / forb+shrub 26.0 m;
  MED 6.2 / 18.0 / 17.5; LOW (phone) 4.6 / 13.0 / **13.0**. On a phone the meadow is
  thirteen metres deep. Shrubs ride the forb ring (`'flora-shrub': rings.forb`), which
  is why the leafy shrubs in the first screenshot vanish at the same line as the flowers.
- The fade is a per-frame ramp evaluated in the vertex shader (`fadeOf`), resolved by an
  **ordered 4×4 Bayer screen-door dither with a per-instance phase**, discarding fragments
  (`flora.js` ≈ line 3450). At close range the dither is invisible; at the outer ring seen
  down a long shallow view it reads as a **band of dots** — the owner's "you can see them
  fade in". The second screenshot shows it clearly on the bank shrubs.
- Past the outer ring the only vegetation cue is the terrain's procedural prairie albedo
  (`uGround`, world-space, ~11 m tile). It carries **colour and no silhouette**: no
  vertical texture, no plant tops, nothing that reads as a meadow at 60 m.

## The trap — read this before proposing a sheet

**There WAS a far-field vegetation sheet, and it was removed on purpose.** The changelog
entry is in the tree: it "was a solid far-field vegetation sheet drawn at the top of the
plants. At river banks and around buildings such as the Exchange Coffee House, it hid
foundations and plant roots while the visitor correctly remained on the real heightfield
below… That sheet is gone. The rendered heightfield is now the one visible land surface."
Re-introducing a horizontal far-field mesh re-introduces a shipped, reverted bug —
a second piece of land a visitor walks underneath.

So any far-field device must: be **rooted to the heightfield** (not floating at plant-top
height), never occlude a foundation or a root, and never read as a walkable surface.

**There is already a legitimate pattern in this codebase to copy**: `trees.js` draws the
timber as a silhouette band on a ring at fixed radius — "a FAR-field device: it carries
angular size but no depth" — with the scene's fog doing the extinction. Ground-anchored
camera-facing impostor cards carrying an aggregate tuft/forb silhouette, tinted by
distance and dissolving into the fog, are the shape of the answer; so is widening the
outer band so the dither ramp is never a metre-wide dotted line seen edge-on. Which one
wins is the run's call — measure it.

**Budget is the constraint that killed the last attempt**: the far field must cost close
to nothing (a handful of instanced cards or a shader term, not another lattice), and
mobile 390×780 is a release gate.

## Acceptance

From both of the owner's stands (South Water at 084°, Wells at 185°), the meadow
**recedes** — faint, blurred vegetation continues past the detailed rings and fades into
the haze — and **no dotted stipple band is visible** at the ring edge, at HIGH and at
LOW. Foundations and plant roots stay unoccluded (the reverted-sheet check: walk to a
river bank and to the Exchange Coffee House and confirm nothing hides the ground line).
Frame budget and draw calls hold at 390×780. Before/after pairs from both stands.

**Links:** T-0035 (done, PR #242 — the fix this follows) · `renderers/web/js/flora.js`
(`TUNE`, `ringsFor`, `fadeOf`, `chiBayer4`) · `renderers/web/js/trees.js` (`RING_RADIUS`,
the far-field band pattern) · `renderers/web/js/terrain.js` (`uGround`, the prairie tile)
· the removed far-field sheet in `renderers/web/js/changelog.js`.
