---
id: T-0702
title: Go to hides reconstructed roofs by default and filters by kind: taverns, stores, trades, homes, fort, waterfront
state: done
epic: RENDERING
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 829
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:52:45.789Z
claimed_run: null
---

The owner, 2026-09-04: Go to should be "a complete list of viewpoints and intersections"; structures with **reconstructed roofs hidden by default** — attested and inferred shown, "reconstructed available as an option" — with **filters** "like taverns, shops, etc."

**Decision.** Presence grade rule: `documented_range.confidence || placement.position_confidence || 'reconstructed'` (`presenceGrade()` in `js/place-kinds.js`); `#jump-reconstructed` "include reconstructed roofs (276)" is persisted as `settings.gotoReconstructed=false`. The row chip becomes the *presence* grade and `data-jump-position` carries the position grade. Single-select pills (`button.jump-pill[data-kind][aria-pressed]`): All · Viewpoints · Corners · People · Taverns & hotels · Stores · Trades · Homes & yards · Public & fort · Waterfront. `placeKind()` reads `attributes.function.value` → `archetype`/`reconstruction.family` → display-name noun → homes; privies, stables and sheds sit under Homes & yards.

**Acceptance:** default Go to lists exactly the structures whose presence grade is not `reconstructed` (82 of 358 today, asserted as `count(presenceGrade ≠ reconstructed) > 70`) and the include-reconstructed toggle lists all 358 (`=== registry.size`); the Taverns pill lists only records whose function matches `tavern|inn|hotel|boarding|lodging` and includes the Sauganash; every structure row has a known group; each row's chip `=== presenceGrade(record)` and its `data-jump-position` `===` the position grade (toggle on, all 358); the attested/inferred/reconstructed chip colours are pairwise distinct and none equals the `.jump-name` colour; `#jump-note`'s shown/hidden/attested/inferred/reconstructed counts equal the registry tally. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
