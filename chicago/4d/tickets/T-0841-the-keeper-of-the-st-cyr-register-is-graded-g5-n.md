---
id: T-0841
title: The keeper of the St Cyr register is graded G5, not G2c: may the officiant of a parish register be graded on it?
state: blocked-owner
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: null
pr: null
claimed_by: run 9/10/2026, 5:38:27 PM CT
blocked_on: Does G2c's 'a party to a marriage or burial in the parish' mean the parish REGISTER of 1833-1835, baptisms included? (1) No — the baptismal pages stay out, Fr St Cyr stays a G5 conflict, and the omission is written down as a ruling. (2) Yes — the rung's text says so and 137 people take it, the priest among them, since the register names him godfather or sponsor three times at Chicago. Measured either way in docs/RESEARCH/resident-grading-policy.md; nothing in grading_proposal.json has moved.
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34538051192
---

The keeper of the St Cyr register is graded G5, not G2c: may the officiant of a parish register be graded on it?.

**Acceptance:** the owner rules on the rung; the ruling is written into `docs/RESEARCH/resident-grading-policy.md`; `grading_proposal.json` is re-derived if it moves. NOTHING here changes a rung before he rules.

**Found by T-0724, 2026-09-05.** That ticket fixed the splitter — a compound surname is now
one surname — and `st_cyr_john_mary` finally carries a ladder rung. The rung is **G5**, and
T-0724 expected **G2c**.

G5 is honest. G2c reads *"the St Cyr register 1833-1835 — a party to a marriage or burial in
the parish inside the scene window"*, and the priest is a party to neither: he is the
officiant. `read_church()` reads `st_cyr_marriages_1834_1839.json` and
`st_cyr_deaths_1834_1837.json` and yields one appearance per record — the person the record
is *about*. So the consolidation sees exactly one appearance of Fr St Cyr, his own town
card citing `andreas_1884_v1`, and G5 is the ladder declining to grade a man on a source it
has not read, and filing him as a conflict.

**The question, and it is the owner's.** The register is his handwriting. `J. M. I. St Cyr`
is printed in `st_marys_baptisms_1833_1835.json`, and the register places him in the parish
across the whole scene window as plainly as it places anybody it names. But grading the
keeper of a register on it is a change to a rung the owner ratified, and this project does
not move a rung to make a man look better.

Three ways it could go, and none of them should be taken without a ruling:
1. **Leave it.** G5 is correct under the rung as written; the priest stays a conflict for
   the owner to read, and his card keeps its Andreas grade.
2. **A new rung** — the keeper of a contemporary register, distinct from a party to it,
   graded on the register's own dates. Needs a name, a grade and a place on the ladder.
3. **Read the baptisms.** `st_marys_baptisms_1833_1835.json` is not in `read_church()` at
   all, so the whole baptismal register is invisible to the ladder — parties included. That
   is worth doing whichever way the officiant question goes, and it may be the larger find.

**Acceptance:** the owner rules, the ruling is written into
`docs/RESEARCH/resident-grading-policy.md`, and `grading_proposal.json` is re-derived if it
moves.

---

## What the run of 2026-09-10 found, and why the question is narrower than the ticket asked

Measured against dev `8c260130f` by putting the register's rows through `read_church()` four ways
and committing none of them. The full write-up, with the counts, is
`docs/RESEARCH/resident-grading-policy.md` § *The second reading put back to the owner*.

1. **The premise is wrong in the ticket's favour.** He is not only the officiant. The register names
   `Saint Cyr` as a PARTY four times in his own hand — godfather at 1834 entry 19 and 1835 entry 9,
   sponsor at 1834 entry 21, all three at Chicago, and sponsor at 1834 entry 10 in Sangamon County.
   So option 2's "a new rung for the keeper of a register, distinct from a party to it" is not the
   question. The question is whether G2c's five words mean the parish REGISTER or only its marriage
   and burial pages, and a baptism is neither of those under the rung as written.
2. **Option 3 is not a free move and it does not answer the question.** Reading the Chicago rows
   under the existing church class moves 137 people onto G2c and mints 131 identities. Reading them
   under a class no rung accepts still lifts the priest, to G4 on count alone, and moves 135 others.
   There is no read-it-and-change-nothing variant: the ladder counts appearances.
3. **A naive read plants twelve entries in the wrong place** — eleven of 1834 written in Sangamon
   County on the journey back from St Louis, and 1833 entry 7 at Ottawa. Any read filters on
   `at_chicago`.
4. **A yes needs `saint` in T-0724's particle list first.** The register spells the particle out, the
   closed list carries `St` and not `Saint`, so `Saint Cyr` keys to surname `cyr` and the party rows
   land on a NEW identity `id_cyr_john_mary_irenaeus_saint` at G2c while the town's own
   `id_stcyr_john_mary_irenaeus` stays at G5 beside it. Reading the register today would mint a
   second priest before it graded the first.
5. **The register's rulings already reach the consolidation; only its rows do not.**
   `declared_rulings()` and `person_links()` rglob every `*crosswalk*.json`, so
   `st_marys_baptisms_crosswalk.json`'s 8 merges, 18 refusals and 275 rulings are spent there today.

**What landed without a ruling**, because it needs none: every reading in
`data/research/church/records/` is now read by `read_church()` or declared unread in
`CHURCH_RECORDS_NOT_READ` with its reason, `--check` fails on a file that is neither, `--self-test`
holds that gate, and `--report` prints the declared silences under the domain table. The baptismal
register was invisible for as long as the file list was a two-name tuple, and the Second Presbyterian
roll of 1842-1892 was invisible beside it.
