---
id: T-0468
title: Create an e1812 natural terrain epoch for the Fort Dearborn battle landscape
state: split
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-01
closed: 2026-09-17
pr: null
claimed_by: run 9/17/2026, 8:56:05 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-17T13:58:17.704Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35229760280
---

Create a dedicated terrain epoch for 15 August 1812 rather than reusing the post-1834 harbor-cut ground. Reconstruct the pre-cut river mouth, baymouth bar/old southward outlet, lakeshore sand ridge, prairie, wet ground and South Branch state across the expanded field.

**Unblocked 2026-09-15 by T-1152.** `shore_1812_pre_cut` is now a distinct
epoch-addressed state with deliberately null geometry. This ticket owns filling
that state; it may not fall back to `shore_1835_harbor_cut`.

Start from the project’s planned `e1830_natural` concept but resolve the 1812 differences explicitly. Use the first-fort-era maps and descriptions already cited in Fort Dearborn research, plus additional period/reliable historical mapping as needed. Any geometry not directly attested must be graded inferred or reconstructed with bounds and a LIBERTIES entry.

Acceptance: an 1812 scene can select an epoch whose shoreline and river mouth are historically plausible for 1812; the post-1834 cut and piers are absent; the Fort-to-18th-Street corridor is modeled ground; and all generated terrain passes the existing fit and provenance gates.
