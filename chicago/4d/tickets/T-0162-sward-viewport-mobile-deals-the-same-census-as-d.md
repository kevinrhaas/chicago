---
id: T-0162
title: SWARD_VIEWPORT=mobile deals the same census as desktop: the viewport does not reach the ring sizes
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-28
pr: 435
claimed_by: run 8/28/2026, 12:04:03 AM CT
blocked_on: null
needs_bake: false
---

SWARD_VIEWPORT=mobile deals the same census as desktop: the viewport does not reach the ring sizes.

**Acceptance, chosen before working (2026-08-28):** the FIRST limb of the clause below — the tool drives the thing that actually changes the ring sizes, and the two runs are shown to differ. The second limb (delete the flag) was refused because the census IS answerable at both stands once the device guess is driven, and deleting the flag would have thrown away a reading nobody had ever taken. Done means: `SWARD_VIEWPORT=mobile` reaches the `light` tune through `prefersTouch()` rather than through the window alone; the run PRINTS the stand it reached before its first figure and REFUSES to print a census under a stand it did not reach; and the desktop and mobile censuses are published side by side as different numbers.

Found by T-0018 while measuring the sward census at both viewports. `tools/measure_sward_draw.mjs`
opens the page at 390x780 when `SWARD_VIEWPORT=mobile` is set, and its own header says *"the
viewport decides the ring sizes and therefore how many slots a station deals, so the census has to
be answerable at both"*. It is not answerable at both: the two runs deal **identical** censuses,
row for row, 7,844 slots either way.

The reason is that `flora.js` sizes its rings off `tune`, which comes from `mergeTune(lowSpec &&
detail === 'full' ? 'light' : detail)` — and `lowSpec` is the DEVICE guess, not the page size, so a
desktop Chromium at a phone's viewport is still `full`. The phone's ring sizes are reached by the
device guess or by an explicit `detail`, and the env var reaches neither.

**Acceptance:** either the tool drives the thing that actually changes the ring sizes and the two
runs are shown to differ, or the flag and its header claim are removed so nothing reads a mobile
figure that is a desktop one. Whichever is chosen, no measurement is left claiming a viewport it
did not stand at.

**Links:** `tools/measure_sward_draw.mjs` (the `VIEWPORT` const and its comment) ·
`renderers/web/js/flora.js` (`mergeTune`, `lowSpec`) · T-0018.
