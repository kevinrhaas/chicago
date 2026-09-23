---
id: T-0157
title: A phone draws the town with no antialiasing, so every edge T-0013 named crawls unresolved
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-24
pr: 376
claimed_by: run 8/24/2026, 9:55:50 AM CT
blocked_on: null
needs_bake: false
---

`main.js` boots the renderer with `antialias: !coarse`, so a touch device draws with **no
multisampling at all**, and its pixel ratio is capped at 1.5 rather than 2.

T-0013 established what that costs. Every one of the 627 interior-flickering pixels at
`from_above` is an edge internal to a layer, and edges are resolved by sample density and by
nothing else: supersampling healed 83–93 % of them, while a shading change that moved 164,572
px of the picture healed none. On desktop MSAA is already absorbing most of it. On a phone
nothing is, so the same edges flip whole rather than partially — which is what crawl in motion
looks like, and mobile is a release gate here.

**Not obviously a fix**: MSAA is not free on a phone, which is why the flag was written this
way, and the scene-detail control already exists as the tier a weak machine boots into.

**Acceptance:** measure first — run the flicker instrument at 390×780 with `antialias` off (as
shipped) and on, and state what the mobile interior and silhouette counts actually are. Then
either turn it on for coarse devices with the frame cost measured at the walking stations the
release gate uses, or record the measurement that says it is not worth it. Do not ship the flag
on the strength of the desktop numbers alone.