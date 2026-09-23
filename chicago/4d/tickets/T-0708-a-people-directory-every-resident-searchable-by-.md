---
id: T-0708
title: A people directory: every resident searchable by name, occupation, arrival, division, age and how they are known
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
closed_at: 2026-09-05T01:52:46.662Z
claimed_run: null
---

The owner, 2026-09-04: "we have people now and they should be able to be searched and found, with filters like occupation, age, arrival, etc."

**Decision.** `compile_scene.py compile_people()` emits `data/sidecars/1835/people.json`, one row per person with household, grade, occupation, sex, age, letter-list marks, division, arrival, origin, presence, `lives_at`/`works_at` — plus `vocabulary` and `counts` — added to the compiler's `keep` set and drift-checked under `--check`; `residents.js` keeps reading the manifest and household files. The People section (`js/people.js`, `#people-directory`) is a search box, pills for occupation, division, arrival year, how known, grade, presence, sex/age where recorded, a count line, and a virtualised list of `button.person-row`. A row opens the person's household record (fetched lazily, rendered by `residents.js`'s exported `householdHtml`/`personHtml`) with a **Go there** button where `lives_at`/`works_at` resolve to a loaded structure. Empty states teach ("try a surname; 727 of this town's people are only a name on a letter list"). The old `#residents` mount stays at the foot as "Browse by household".

**Acceptance:** smoke PART 12 — `people.json` row count `===` the manifest's `counts.persons` (1,404 today); searching "Beaubien" finds Mark Beaubien; the "tavern keeper" occupation pill narrows the list; the person card opens with a Go-there button that lands the visitor within 14 m of the building; `#residents details.res-hh` still renders. Both viewports green.

Claimed together; ships in one PR into dev on the owner's instruction.
