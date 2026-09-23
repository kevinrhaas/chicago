---
id: T-1466
title: The People directory's count identity is short by 162: stated 3,228 against manifest 2,269 + readmitted 182 + trades 308 + transients 307, and the smoke has been red on dev at both viewports
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1598
claimed_by: run 9/20/2026, 7:11:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T00:32:37.342Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35546585485
---

The People directory's count identity is short by 162: stated 3,228 against manifest 2,269 + readmitted 182 + trades 308 + transients 307, and the smoke has been red on dev at both viewports.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1442's smoke legs (2026-09-20), on files byte-identical to `origin/dev`.**

`smoke_renderer.mjs` asserts an identity over the People directory's counts:

    stated == manifest + readmitted + trades + transients

Measured on dev today: `3228 != 2269 + 182 + 308 + 307` (= 3,066). **162 cards reach the
directory by a path the assertion does not know about.** The comment above it names T-1172,
T-1347 and T-1353 as the stages written outside `data/residents/households/`, and
`data/sidecars/1835/people.json` now carries several more in `by_stage` that the identity never
learned — `civic_mint: 392`, `garrison: 125`, `lodgers: 75`, `women_and_children: 556`,
`underdocumented: 87`, `modelled_families: 300`.

The companion failure is the same view: *"the Trade row offers the documented trades AND the
town's commonest"* returns 13 pills.

Both fail at **mobile 390×780 and desktop 1280×800**, parts 12 and 12-13, filed in
`tools/dev-smoke-state.json` on sha256:d9cd14b700afd11f.

**What this ticket owes:** decide which is wrong — the identity, or a stage that mints cards
without restating the manifest — and make the assertion name every path into the directory, so
it fails on a new one instead of drifting past it. Do not weaken it to the current number.
