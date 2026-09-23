---
id: T-0035
title: Flowers grow up out of the ground as you approach instead of fading in
state: done
epic: FLORA
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-17
closed: 2026-08-18
pr: 242
claimed_by: run 8/18/2026, 8:34:20 AM CT
blocked_on: null
needs_bake: false
---

**The owner's report, 2026-08-17:** "the flowers still seem like they grow out of the
ground as you approach them, they do not fade in as you walk towards, they grow up."

The mechanism to check first: the ring fade deliberately scales plants and heads down to
the ground at the lattice edge (`chiFade` — a head "slides down its own stalk as its plant
shrinks", R-BUG7's design), so a plant entering the near ring rises from the soil instead
of appearing at full height. The ask is a different transition: **opacity or scale-in-place
fade, not vertical growth** — or a ring far enough out that the transition happens beyond
notice. Mind the R-BUG7 invariant: any change must keep `foot ≤ plantH` at every fade so
heads never detach again; that gate is in the smoke and must stay green.

**Acceptance:** walking toward a meadow at eye height, new plants appear without visible
vertical growth (owner-checkable from spawn); the flower-head attachment gate stays green;
frame cost within budgets.
