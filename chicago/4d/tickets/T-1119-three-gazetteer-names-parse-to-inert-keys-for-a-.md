---
id: T-1119
title: Three gazetteer names parse to inert keys for a reason the rank rule does not own: a surname-first entry with no comma inversion, an [uncertain: …] wrapper read as a forename, and a rank-and-regiment line that names nobody
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-13
closed: 2026-09-14
pr: 1315
claimed_by: run 9/14/2026, 1:35:56 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T07:22:08.242Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34813847248
---

Three gazetteer names parse to inert keys for a reason the rank rule does not own: a surname-first entry with no comma inversion, an [uncertain: …] wrapper read as a forename, and a rank-and-regiment line that names nobody.

**Acceptance:** the three named rows parse to what the page gives, by a rule this corpus
has already settled elsewhere rather than by a special case; `ranks_are_not_names.
still_wrong_and_not_a_rank` no longer holds them open; no 1840 head gains or loses a MATCH
(a refusal may move between refusal rules, and each move is named); the self-test asserts
each rule and each guard on a named example; `--check` and `./tools/check.sh` green.

FOUND BY T-1116, which fixed the rank and named what the rank rule does not own.

The three are all one defect wearing three hats: **this tool never read the corpus's own
name markup.** `compile_gazetteer.py` `unmarked` strips `[uncertain: …]` and joins `[x]`
into the word it supplies a letter to; its `surname`/`initials` invert on the comma;
`concord_letter_list_1834_01_01.py` `fold` folds the same wrapper; T-0299 ruled that the
markup is not a word boundary. `crosswalk_census_1840_heads.py` flattened every bracket to
a space and every comma to a space, and took the last word as the surname.

So it is not three names. It is 1,007 surname-first entries read backwards (`Aiker, Samuel`
gave the surname *Samuel*), 95 `[uncertain: …]` readings whose forename became the word
*uncertain*, 258 names whose supplied letters split into separate forenames, and two lines
that name nobody and keyed off the office beside the blank.
