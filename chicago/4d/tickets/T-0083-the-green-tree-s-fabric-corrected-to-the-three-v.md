---
id: T-0083
title: The Green Tree's fabric corrected to the three views: bays, chimneys and the low left wing
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: K2
parent: T-0042
opened: 2026-08-18
closed: 2026-08-20
pr: 274
claimed_by: run 8/20/2026, 6:52:38 AM CT
blocked_on: null
needs_bake: true
---

The Green Tree's fabric corrected to the three views: bays, chimneys and the low left wing.

Piece 4 of 4 of **T-0042 — Image-accuracy pass: the Green Tree Tavern**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

The building itself, against all three views: two full storeys of pale clapboard, **even
6-over-6 bays**, **end chimneys at both gables**, and the **lower gabled wing at the left with a
wide carriage door** that `data/structures/green_tree_tavern.json` deliberately excludes from
its footprint today. Image 6 also puts **ship masts directly behind the roofline** — check what
the model puts behind the inn.

**NEEDS THE BAKE.** Every item here moves `green_tree_tavern__frame_1833.glb`'s inputs, and the
improve runner has no Blender; this closes on the nightly `chicago-4d-bake.yml` or on a runner
that has one.

**Acceptance:** a before/after pair from a stand matching the engraving's quarter, the fabric
corrected to the views, every claim carded at its honest tier.

**Links:** owner_brief_2026_08_18 README (images 6, 7) · prefire_views_kevin_2026_08 (plate
"11") · T-0042 (parent) · T-0075.
