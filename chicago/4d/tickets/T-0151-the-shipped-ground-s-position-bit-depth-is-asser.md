---
id: T-0151
title: The shipped ground's POSITION bit depth is asserted, not assumed
state: done
epic: RENDERING
requested_by: loop
seen: true
effort: S
legacy_id: R-W6(b)
parent: T-0012
opened: 2026-08-22
closed: 2026-08-22
pr: 317
claimed_by: run 8/22/2026, 10:27:07 PM CT
blocked_on: null
needs_bake: false
---

The shipped ground's POSITION bit depth is asserted, not assumed.

Piece 1 of 2 of **T-0012 — Ship the 16-bit ground the script already computes**, split
because the parent needed more than one run's demonstration to be done. The parent keeps
the full ask and its links; this ticket owns one slice of it.

**The parent's headline turned out to be already true, and nothing in the repository could
say so.** Measured 2026-08-23 with the control R-W6 itself used: regenerating
`terrain__e1834_harbor_cut.glb` from the committed master at 16 bits reproduces the
committed derivative **md5 for md5** (`5b8446876a425fceace5c7dd7c59688a`, 704,004 bytes),
and at 14 bits it does not (`4b9fb0765a9b5669dd547b32ef156825`, 702,896). So the 16-bit
ground has been on the site since a nightly bake rebuilt the terrain, and R-W6(b)'s
finding — written when it was still 14-bit — outlived the state it described, at number
two in the queue, waiting for a bake that had already happened.

The water mesh reproduces at BOTH depths (`61b38d4bc36964db450b59ac7b646b77`), which is
R-W6's own recorded prediction: four vertices at exactly y = 0 land on the lattice at
every bit depth.

**Why nothing caught either direction.** R-W6(b) diagnosed it and the diagnosis still
stands: the derivative gate compares master to derivative on material identity, triangle
count, node identity and a bounding box within four rungs, and a bit-depth change moves
none of them. `tools/measure_terrain_fit.mjs` printed the lattice and asserted nothing.

**Acceptance:** the shipped ground's POSITION bit depth is recovered from its own bytes,
compared against the depth `tools/web_derivatives.sh` asks for, and FAILS when it is
coarser; the gate is demonstrated firing on the 14-bit file this ticket's parent was
written about; `tools/check_published.mjs`'s derivative entry names the assertion instead
of saying the derivative is only reported.

**Links:** T-0012 (parent) · ROADMAP R-W6, R-W6(b) · T-0152 (the other piece).
