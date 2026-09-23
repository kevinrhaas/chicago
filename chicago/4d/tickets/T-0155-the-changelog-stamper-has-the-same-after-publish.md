---
id: T-0155
title: The changelog stamper has the same after-publish trap the ticket tool just lost
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-28
pr: 496
claimed_by: run 8/28/2026, 8:41:41 PM CT
blocked_on: null
needs_bake: false
---

`renderers/web/js/changelog.js` is published to TWO mirrored paths — `js/changelog.js`
(the URL Manager and the launcher parse) and `walk/js/changelog.js` (inside the copied
renderer tree) — and `check_published.mjs` compares both byte for byte.
`tools/stamp-changelog.mjs` rewrites the source. So a run that stamps AFTER
`tools/publish.sh` lands in exactly the state T-0154 fixed for `tickets.json`: the gate
is red and the only remedy is a remembered second publish.

Nothing in AGENTS.md forces that order, which is why it has not bitten yet — the close
step is the one that CANNOT be ordered correctly, and that is why T-0154 was the ticket.
This is the latent sibling: a run that stamps last is following the documented rules and
gets a red gate for it.

Found while fixing T-0154; filed rather than folded into it, because a PR is one
revertible unit.

**Acceptance:** stamping the changelog after `publish.sh` cannot leave either mirrored
copy stale — by the same shape as T-0154's fix (the writer carries the file, only on a
real rewrite, with the copy pinned) or by a better one. `tools/test_ticket_mirror.mjs`
is the pattern for the demonstration, and the second half of it is not optional: a
mirror somebody else made stale must still fail the gate.
