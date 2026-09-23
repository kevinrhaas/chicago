---
id: T-0051
title: The estray pen is a fence, and the model still gives it a roof
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: K5
parent: T-0038
opened: 2026-08-17
closed: 2026-08-17
pr: 235
claimed_by: run 8/17/2026, 9:40:46 PM CT
blocked_on: null
needs_bake: false
---

The estray pen is a fence, and the model still gives it a roof.

Piece 2 of 3 of **T-0038 — Fences and enclosures: the estray pen, wagon yards, garden pickets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** the estray pen on the south-west corner of the public square stands as a ROOFLESS
enclosure rather than a roofed box, drawn on the enclosure layer T-0050 shipped, with
`data/structures/estray_pen.json`'s invented roof retired rather than re-graded, and
`docs/LIBERTIES.md` L60 moved to Resolved or narrowed in writing to whatever is left.

**Why it is its own ticket.** L60: *"A pound is an enclosure; there is no reason to think this one
was roofed and nothing mentions a roof. This project has no generator that builds an enclosure …
so the choice was a roofed box or no building at all."* The record's own research note is blunter:
*"CHICAGO'S FIRST PUBLIC BUILDING, AND IT IS A FENCE."* T-0050 built the layer that makes this
possible and deliberately did not touch this record, because retiring a committed structure's GLB
is a second demonstration: the pen currently renders from `gltf/estray_pen__pen_1833.glb`, so this
ticket has to decide what the structure record becomes when its geometry moves to another layer.

**Links:** `docs/LIBERTIES.md` L60 · `data/structures/estray_pen.json` · `data/enclosures/`.
