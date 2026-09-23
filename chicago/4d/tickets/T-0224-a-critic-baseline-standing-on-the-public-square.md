---
id: T-0224
title: A critic baseline standing on the public square
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-28
pr: 464
claimed_by: null
blocked_on: null
needs_bake: false
---

T-0027 changed the sward over a whole city block — the public square now plants sedge
meadow where it planted wet prairie — and nothing in this project could show that in a
picture. `tools/critic_shots.mjs` has no stand on or facing the square, so a change to the
one block three sources describe as water is verified by a zone lookup and a
zero-pageerror pass, never by a screenshot. The same hole covers the three county
buildings on it: the estray pen, the log jail and the court-house have no baseline either,
and they are the town's only public buildings.

**Acceptance:** a critic stand on the public square, shot at both viewports, with its own
row in the baseline; the row named in `docs/STATUS.md`; and the shot re-taken against the
committed tree so the row is a reading rather than a target.
