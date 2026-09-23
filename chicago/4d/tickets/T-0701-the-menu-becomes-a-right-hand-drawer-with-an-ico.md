---
id: T-0701
title: The menu becomes a right-hand drawer with an icon rail, a bottom sheet on a phone
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
closed_at: 2026-09-05T01:52:45.639Z
claimed_run: null
---

The owner, 2026-09-04: the pop-out menu "is so small" — a sixth tab literally did not fit its 380 px row (STATUS § 2026-08-13) — and the redesign should take its cues from polecat-platform's left rail: "world class elegant and easy to use", "delightful and fun". He also ruled that the menu and the building card **share one right-hand slot**.

**Decision.** `#panel` becomes a right-hand drawer `min(440px, 100vw)` wide: a 66 px vertical icon rail (`nav.panel-tabs` — Go to, Travel, People, Evidence, Settings, Controls, What's new; inline SVG, `currentColor`, active = 16 % accent wash + 3 px gradient bar), a head (`h2#panel-title` + one `#panel-close`, a back button for sub-views) and a scroll column; under 560 px it is a bottom sheet. Opening the drawer *tucks* the card (`#popup[data-tucked]`, never `hidden`); closing untucks it; a Go-to arrival closes the drawer and opens the card.

**Acceptance:** smoke PART 12 — rail order is exactly `goto,travel,people,evidence,settings,controls,whatsnew`; every rail item is fully visible and unsqueezed (desktop: one column, one distinct `offsetLeft`; mobile: one row; no rail overflow; no item with `scrollWidth/Height > client + 1`); menu open ⇒ `#popup` is tucked and the drawer's and card's rects do not intersect, close ⇒ untucked. PART 13 "card is not collateral when the panel opens" holds unchanged (`hidden` stays off `#popup`). Both viewports, zero pageerrors.

Claimed together; ships in one PR into dev on the owner's instruction.
