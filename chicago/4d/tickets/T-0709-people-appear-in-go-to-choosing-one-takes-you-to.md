---
id: T-0709
title: People appear in Go to; choosing one takes you to where they lived or worked
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
closed_at: 2026-09-05T01:52:46.812Z
claimed_run: null
---

The owner, 2026-09-04: "the citizens should show there" — in Go to.

**Decision.** Go to gains targets of kind `person` for every person whose household has `lives_at` or `works_at` resolving to a loaded structure — label "Mark Beaubien · tavern keeper", sub "lived at the Sauganash". Choosing one travels to that structure at the current pace and opens the **building card** with the household highlighted (`.res-hh[data-id]` gets `is-here`). People with no known address stay in the directory only ("no known address"), with no Go-to row. `#jump-note` counts the people with an address.

**Acceptance:** smoke PART 12 — the People pill lists only people with an address; the row for Mark Beaubien names his trade and the Sauganash; choosing it lands within 14 m of `sauganash` and opens its card with his household marked `is-here`. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
