---
id: T-0712
title: The card's evidence, liberties and record move under three tabs at its foot
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
closed_at: 2026-09-05T01:52:47.250Z
claimed_run: null
---

The owner, 2026-09-04: provenance goes to the bottom under tabs — "that list is getting very long".

**Decision.** Below the residents block, a sticky `.pop-tabs` of three `[data-pop-tab]` buttons — Evidence · What we made up · Record — and three `.pop-pane[data-pop-pane]`, all in the DOM, hidden via `[hidden]`. Evidence holds the basis, a new "Where did it stand?" `claimRow` (so the position `.conf` chip stays inside `table.attrs`), presence minus the account, shape, Attributes and evidence, Citations; What we made up holds `libertySection` + `openQuestionSection`; Record holds `researchSection`, `.pop-spec`, `.pop-foot`. The last tab is remembered in module scope.

**Acceptance:** smoke PART 3 — three tabs and three panes exist; every `checkVisibility` read inside a card pane first activates that pane's `[data-pop-tab]` (a collapsed read passing would be dishonest, so the smoke says which tab it opened); the `#popup .pop-sec h3` texts and the chip-coverage selector keep their meaning; the `.pop-flag` spans are still in the head. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
