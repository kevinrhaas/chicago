---
id: T-0707
title: Fly travel rises to a cruise height, glides, and lands in front of the building
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 829
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:52:46.510Z
claimed_run: null
---

The owner, 2026-09-04: or fly — "you go up, fly, and open the card".

**Decision.** Fly travel is the same controller with states ascending → cruising → descending → landing → arriving: cruise height `clamp(12 + 0.15·d, 20, 80)` m, `setFly(true)` through the HUD setter (never the walker directly), a glide aimed at the stand-off point, `setFly(false)` when within 2.5 m horizontally and 4 m up. Anchors with `altitude_m` fly and stay aloft; intersections and anchors open no card.

**Acceptance:** smoke PART 12 — flying to the Sauganash reaches ≥ 20 m altitude, lands (the fly button state matches the walker), stands within 14 m and opens the card. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
