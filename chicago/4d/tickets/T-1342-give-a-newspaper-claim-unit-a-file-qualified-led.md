---
id: T-1342
title: Give a newspaper claim unit a file-qualified ledger id, so a bound naming one claim closes that claim and not the 55 issues that share its number: the declaration, the gate that refuses an undeclared repeat, and the 142 assertions the bare id was making
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1338
opened: 2026-09-18
closed: 2026-09-18
pr: 1483
claimed_by: run 9/18/2026, 5:59:52 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T23:50:54.928Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35403118586
---

Give a newspaper claim unit a file-qualified ledger id, so a bound naming one claim closes that claim and not the 55 issues that share its number: the declaration, the gate that refuses an undeclared repeat, and the 142 assertions the bare id was making.

Piece 1 of 2 of **T-1338 — Spend the 128 press notices onto the cards they name, once a newspaper claim unit carries a file-qualified ledger id: the 22 raw claim ids these units share would close 937 other units as asserted**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. A ledger unit's key in `tools/research_spend_ledger.py` is UNIQUE ACROSS THE CORPUS.
   Where a container's row ids are only unique within their own file, the key is the
   source file's stem and the id joined by `#` — `chicago_democrat_1835_08_19#c007`,
   which is the form the resident cards' own notes were already writing. A card must
   name that whole form to spend such a unit, and a bare `c007` names nothing.
2. WHICH CONTAINERS NEED IT IS DECLARED, NOT GUESSED. Two corpora reuse a row id across
   their own files and mean opposite things by it — a `residents` pass cohort names the
   same man in four passes, a newspaper issue numbers its claims from `c001` with no
   reference to any other issue — and nothing in the id tells them apart. Each is
   declared on its own pattern in `data/research/domains.json`, which is GENERATED, so
   the declaration is authored in `tools/research_domains.py` and the manifest rebuilt
   from it.
3. AN UNDECLARED REPEAT IS A FAULT. `record_id_scope_faults` refuses a container whose
   ids repeat across files and which declares neither scope, and refuses a `global`
   declaration whose ids no longer repeat — the same discipline this project already
   holds a refusal to, so a judgement nobody recorded cannot read as one nobody needs.
4. THE 142 ASSERTIONS THE BARE ID WAS MAKING ARE UNMADE, and the three that were real
   survive UNTOUCHED. No resident card is edited, no confidence moves, no identity is
   reopened and no person is minted: the cards were right and the ledger was reading
   them wrong.
5. The units the repair frees reach a terminal disposition or an OPEN owner — not the
   done ticket the domain defaults had been pointing at — and
   `tools/measure_research_spend.py --check` is green.
6. `--ledger-self-test` proves the rule over the shape that caused it: two issue files
   each carrying a claim `c007`, one card citing one of them. The card closes that claim
   ALONE; the same card citing a bare `c007` closes nothing.

**Outcome, 2026-09-18.** asserted 824 → 682. `newspapers` asserted 144 → 3, and the
three are `chicago_democrat_1834_04_01#c013`, `chicago_democrat_1835_07_01#c015` and
`chicago_democrat_1835_08_19#c007` — the three the cards actually name. Of the 142
unmade: 69 are enterprise claims and route themselves to T-1182, 28 are place claims and
route to T-1198, 18 reach a terminal disposition in the remainder register, 7 join the
family and re-admission passes (T-1172, T-1335), and 20 — 19 press rows and the one
civic claim that shared their numbering — go to T-1343 with the corpus, which now owns
148. `EPIC_PIECES` had pointed `civic` at the closed T-1297 and nothing had noticed,
because until this repair nothing reached it.

**Not this ticket:** the identification. T-1343 owns spending the 128 press notices onto
the cards they name; this one only makes a press claim NAMEABLE.
