---
id: T-0711
title: The building card opens on a narrative lead and a key-facts grid with quiet grade dots
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
closed_at: 2026-09-05T01:52:47.105Z
claimed_run: null
---

The owner, 2026-09-04: the card should not lead with "what we made up / what was reconstructed" — lead with a narrative of what the building is and its key facts; and this session he ruled the top half uses **quiet coloured grade dots**.

**Decision.** `popup.js show()` reorders the card: `.pop-head` (title, aka, `.pop-kind`, `.pop-where-line` with a position `.fact-dot`, the `.pop-flag` spans — including a new line for the nine `review_required` records, "held pending consultation — see the standing constraint", which also advances T-0268) → `p.pop-lead.pop-account` (`change_note`, else a lead composed strictly from record fields: title, function, location, head of household) → `dl.pop-facts` (Standing from–to · Use · Built · Roof · Who was here · Keepers, each value with `<i class="fact-dot fact-<grade>">`, never a `.conf` chip) → residents. Styled in the drawer's language.

**Acceptance:** smoke PART 3 — `#popup .pop-lead.pop-account` is read directly (no longer inside "Was it here"); a record without `change_note` gets a composed lead containing its function and location; on the Sauganash `.fact-dot` count ≥ 3 and `.pop-facts .conf === 0`; `#popup .pop-where [data-note]` restates the old `.pop-meta [data-note]` read; the nine `review_required` records carry the new `.pop-flag`. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
