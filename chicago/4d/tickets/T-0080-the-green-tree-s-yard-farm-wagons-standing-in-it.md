---
id: T-0080
title: The Green Tree's yard: farm wagons standing in it, and the bench at its front wall
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: K2
parent: T-0042
opened: 2026-08-18
closed: 2026-08-18
pr: 244
claimed_by: run 8/18/2026, 9:52:48 AM CT
blocked_on: null
needs_bake: false
---

The Green Tree's yard: farm wagons standing in it, and the bench at its front wall.

Piece 1 of 4 of **T-0042 — Image-accuracy pass: the Green Tree Tavern**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

The Trowbridge view (owner brief 2026-08-18, image 7) shows **farm wagons standing in the
yard** of this inn and a **bench against the front wall** — the sitters on it are L1 reference
only and are never drawn; the bench is the buildable fact.

**Acceptance:** walk to the Green Tree and there are wagons standing in its yard and a bench
against its front wall; every stand is DERIVED from the committed footprint and the ground
rather than placed by eye, the rule that chose them re-derives byte for byte under
`tools/check.sh`, and both are graded `reconstructed` with the liberty recorded. Gates green,
published in the same commit.

**Links:** owner_brief_2026_08_18 README (image 7) · T-0042 (parent) · T-0064 · L131 ·
`tools/generate_yard_goods.py` · `renderers/web/js/yard.js`.
