---
id: T-0425
title: A letter-list household's arrival bound is dated by the printing it was extracted from, not by the return, so nine printings of one list give nine different bounds
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-10
pr: 1085
claimed_by: run 9/10/2026, 3:38:02 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T21:13:25.759Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34527098866
---

`tools/mint_letter_list_residents.py` dates a minted household's `arrival` from the
issue the CLAIM sits in — "The first return holding a letter for this name is the
Democrat of 4 March 1834" on `hh_conger_thomas`, written this run. T-0331 showed
that 4 March is the NINTH printing of the Chicago post office's **1 January 1834**
return; the same list was printed in every Democrat from Vol. I No. 7 of 1834-01-07.
So the bound is true but weak, and it is weak by an accident of which impression an
extraction pass happened to reach.

The `not_later_than` precision means nothing here is false, which is why this is filed
rather than fixed inside T-0331: the fix is a change to how a household is derived, and
it moves every letter-list household this project holds, not two.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- A letter-list household's arrival bound is dated by the RETURN — the date the list
  itself states, `January 1, 1834` — or, where the return date is unreadable, by the
  EARLIEST printing that carries the name, and the note says which of the two it used.
- The nine printings T-0331 counted are the worked case: every household minted off
  `chicago_democrat_1834_03_04` moves to the January bound, and the note names the
  printing run rather than the issue.
- `mint_letter_list_residents.py --check` re-derives green, and its self-tests assert
  that two printings of one return give ONE bound.

**Links:** T-0331 (the nine printings, and the return they carry) · T-0299 (mint one
list once) · `tools/letter_list_printings.py` · `tools/mint_letter_list_residents.py`
