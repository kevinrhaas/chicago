---
id: T-0710
title: The Evidence panel becomes a hub of browsable topics with search, instead of one scroll
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
closed_at: 2026-09-05T01:52:46.960Z
claimed_run: null
---

The owner, 2026-09-04: the Evidence panel "is entirely unwieldy — nice info but unconsumable in its current form."

**Decision.** `js/evidence.js` turns the section into a hub of seven topic tiles (icon, title, count, one-line gloss): How we grade · What we made up · The ground · What was living here · What grows here · What is not here · Open questions. A tile opens its topic view (title in `#panel-title`, back arrow) with a search box filtering entries by text and, where the data has a scope, pills (liberties by scope; exclusions not-until vs came-down; fauna see/hear/sign). The existing mounts — `#liberties`, `#ground`, `#fauna`, `#plants`, `#exclusions`, `#uncertain` and their `-note` ids — move unchanged into the topic views so `liberties.js`, `exclusions.js`, `fauna.js`, `plants.js` and ground keep rendering into them. Long explanatory paragraphs collapse behind "About this list". `.lib-body`'s max-content overflow (T-0302) is fixed in `css/evidence.css` if it is fixed. People leaves Evidence for its own section (T-0708).

**Acceptance:** smoke PART 12 — seven tiles whose counts equal their mounts' entry counts; a topic search narrows the `#liberties` rows; back returns to the hub; every mount id above still exists and is populated. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
