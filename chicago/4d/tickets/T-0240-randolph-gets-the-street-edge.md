---
id: T-0240
title: Randolph gets the street edge
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-0191
opened: 2026-08-27
closed: 2026-08-27
pr: 416
claimed_by: run 8/27/2026, 4:36:58 PM CT
blocked_on: null
needs_bake: false
---

Randolph gets the street edge.

Piece 1 of 2 of **T-0191 — Randolph and Washington get the street edge**, split because
the parent turned out to need more than one run's demonstration. The parent keeps the
full ask and its links; this ticket owns one slice of it.

**Why the parent split, measured rather than guessed.** T-0191 was taken as one unit and
built as one: `EDGE_STREETS` extended to carry both streets, 36 block faces, 3,129.1 m of
walk. Read on the published mirror with `tools/measure_detail_ceilings.mjs`, desktop
1280x800, worst of T-0135's five stands:

| tier | ceiling | both streets | Randolph alone |
|---|---:|---:|---:|
| `full` | 1,425,000 | 1,385,207 | 1,369,835 |
| `balanced` | 1,260,000 | **1,260,174 — OVER by 174** | 1,201,248 |
| `light` | 1,050,000 | 761,404 | 745,904 |

**Washington is what breaches `balanced`, and by 174 triangles on 1.26 million.** The two
honest routes past that are a sixth ceiling raise or a trim, and a sixth raise is the
thing T-0223, T-0229, T-0237 and the count written into `main.js` all exist to make
harder — T-0237's acceptance says it in as many words: *"Not by raising a ceiling."* So
Washington becomes T-0241 with the number attached, and Randolph — which fits under the
raised ceilings AND under the ORIGINAL ones T-0229 will restore — ships here.

**Acceptance:** Randolph Street's platted block faces carry the street edge by the same
rule Lake and South Water already do — laid from the plat grid, not hand-placed — and a
visitor walking Randolph finds plank walk under foot with board crossings at the corners.
`full`, `balanced` and `light` are each inside their ceiling at all five stands, at BOTH
viewports, measured on the published mirror. Gates green.

**Links:** T-0191 (parent) · T-0241 (Washington) · T-0069 · T-0127 · T-0188 (the earlier
Randolph build that was taken back out) · docs/LIBERTIES.md L160.
