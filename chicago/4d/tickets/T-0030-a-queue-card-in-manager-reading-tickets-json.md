---
id: T-0030
title: A queue card in Manager reading tickets.json
state: open
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
opened: 2026-08-17
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

Manager (manager.polecat.live) already parses this project's changelog live. This repo now
publishes tickets/tickets.json into the site mirror — add a Manager card/section that fetches
it and renders the queue (owner-first, states, blocked-on-owner questions), so the owner can
see the board without opening the repo. Scope: the manager repo, its own conventions.

**Acceptance:** the queue visible in Manager against the published URL; read-only is fine.
