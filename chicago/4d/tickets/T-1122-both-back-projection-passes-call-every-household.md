---
id: T-1122
title: Both back-projection passes call every householder 'this man' in generated prose, and one of the 57 is Rebecca Sherman
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-14
pr: 1336
claimed_by: run 9/14/2026, 11:57:10 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T17:39:00.521Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34871047337
---

Both back-projection passes call every householder 'this man' in generated prose, and one of the 57 is Rebecca Sherman.

**Found by T-1050, 2026-09-14**, while re-deriving the residence ledger.

`tools/back_project_residences.py` and `tools/back_project_addresses.py` write the prose a
reader sees on a household card, and every template says **"this man"**: "the entry prints
it as this man's home", "Norris's Chicago directory of 1844 prints where this man lived in
1844". Twenty-eight of the 57 residence rulings carry that phrase in their `reason`, and
the notes carry it again. One of the 57 is **Rebecca Sherman** (`hh_sherman_rebecca`), so
the record as published tells a reader that Norris printed where *this man* lived.

It is one word in a template and it is the only word on that card a reader did not ask for.
Nothing about the reading is wrong; the prose is asserting a fact about a person that the
source does not support and that happens to be false.

**Acceptance:** neither pass's generated prose assumes the householder's sex — "this
person", "the householder", or the name itself, whichever reads best in each template; the
two passes stay word-for-word consistent with each other, because their shared tables are
already held to that (`--self-test` asserts the two never disagree about a street, and this
is the same class of fault); the ledgers and every `back_projection` /
`residence_back_projection` block re-derive; and the check is a `--self-test` assertion that
no generated string contains the phrase, not a one-time sweep. Small: one run, no bake.
