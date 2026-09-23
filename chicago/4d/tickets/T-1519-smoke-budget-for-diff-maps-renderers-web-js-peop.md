---
id: T-1519
title: smoke_budget --for-diff maps renderers/web/js/people.js to part 13, but the People directory's checks are guarded by stageOn(12), so a run that trusts the mapping runs the wrong leg
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

smoke_budget --for-diff maps renderers/web/js/people.js to part 13, but the People directory's checks are guarded by stageOn(12), so a run that trusts the mapping runs the wrong leg.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)
