---
id: T-0703
title: Every Go to row says how far and which way; arrow keys walk the list
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
closed_at: 2026-09-05T01:52:45.935Z
claimed_run: null
---

The owner asked for a menu that is "easy to use"; a list of two hundred places is only usable if each row says where it is from where you stand, and if the keyboard can walk it.

**Decision.** Every Go-to row gets `.jump-name` · `.jump-sub` (kind or street) · `.jump-dist` — "240 m NE ↗", a 16-point compass with the arrow rotated by bearing − visitor bearing, distance in the visitor's units — refreshed every 500 ms while the pane is visible. Rows sort by distance when the query is empty, by name when searching, under sticky `.jump-group` headings. ArrowUp/Down/Home/End move `is-active` / `aria-activedescendant`; Enter goes (first row when none is active, as today); typing resets.

**Acceptance:** smoke PART 12 — every row shows a distance and a compass point; after a 100 m teleport the distance on a fixed row changes by ≈100 m; ArrowDown three times then Enter arrives at the third row's target; the old `.jump-result span` read is restated as `.jump-result .jump-name` (same meaning). Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
