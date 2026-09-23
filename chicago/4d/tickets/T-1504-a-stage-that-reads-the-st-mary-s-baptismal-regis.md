---
id: T-1504
title: A stage that reads the St Mary's baptismal register: the four R6 rows whose Indigenous identity the source states in its own hand are refused only because underdocumented reads the 1832 muster roll and nothing reads the register
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

A stage that reads the St Mary's baptismal register: the four R6 rows whose Indigenous identity the source states in its own hand are refused only because underdocumented reads the 1832 muster roll and nothing reads the register.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1383, 2026-09-21, which put these four rows in front of T-1177's review for
the first time.

`data/research/church/records/st_marys_baptisms_1833_1835.json` is the only source this
project holds in which a contemporary STATES an Indigenous identity for a named person at
Chicago — the priest's own parenthesis on the page, not a term in a later biography.
Since T-1383 the borderline roster reads it: four rows reach `R6_native_metis_black` on
`community_term_written_onto_the_name` (Marianne, entries 14 and 17 of 1833; Jaespquaa,
entry 18 and the town finding that quotes it).

`tools/reconstruct_underdocumented.py` then withholds all four as
`the_statement_is_not_on_the_roll_this_stage_reads`, which is the honest reason and a
dead end: that stage reads the 1832 Black Hawk muster roll and nothing else. Its own
words — "the row is owed a stage that reads the register, and until one exists the person
stays out of the town for want of a reader rather than for want of evidence."

**Acceptance:** (state it before working — never weakened to pass)

1. A stage reads the church register's R6 rows, under T-1177's review rules: every card
   `review_required`, `touches_removal` ruled in its own words, `no figures`, and no
   nation written that the source does not write.
2. A baptism is not a residence. The stage says what it takes the dated appearance to
   bound and what it does not, exactly as `underdocumented` does for the muster.
3. The mononym is carried `as_read`. No surname is invented for Marianne or Jaespquaa
   and no given/family split is imposed — the rule `underdocumented` already states.
4. Jaespquaa's origin ("de Green Bay") is the only origin the register ever gives anyone;
   it is carried or refused in writing, never dropped silently.
5. The kinship the register states on one dated line is NOT joined here — T-1335 owns
   the family pass, and every one of these rows names T-1335 in its `ledger_reason`.
   Say what is handed to it.
6. `--check` re-derives byte for byte and is in `tools/check.sh`; `--self-test` fires.
