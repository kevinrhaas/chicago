---
id: T-0467
title: Add south-scene camera anchors, navigation and map extents
state: done
epic: SOUTH_TIME
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-01
closed: 2026-09-17
pr: 1395
claimed_by: run 9/17/2026, 7:34:37 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T13:34:49.623Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35221393518
---

**Unblocked 2026-09-15.** This ticket carried `blocked_on: T-0464` from the day it was
filed. T-0464 CLOSED on 2026-09-14 as #1257 — the ground now reaches Twenty-Second
Street and the modelled field is one box 2 020 x 4 920 m — so the dependency is
SATISFIED, not dropped. The field was left stale for a day, which reads to anything
picking work off this queue as "blocked" and is the state a run steps over.

Once the land exists, make it reachable. Extend overview-map bounds, walker navigation and jump targets so a visitor can travel continuously from Fort Dearborn to the 1812 battle corridor and later Prairie Avenue landmarks without teleporting outside modeled ground.

Add evidence-aware anchors at the fort, the historic shoreline route, the approximate battle area, 16th/Prairie, 18th/Prairie and the south end near 22nd/Cermak. Anchor names must describe what the selected year actually contains; do not show an 1880s mansion label in 1812.

Acceptance: all south anchors resolve on modeled land, year switching preserves valid camera placement, overview/map bounds include the new field, and a desktop smoke path can traverse from the fort to the southern historical area.