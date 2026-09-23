---
id: T-1379
title: The borderline roster keys the resident layer by the name a source prints, so a read name a crosswalk merged into a differently-spelt card is offered for re-admission beside the card that already holds the person
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-21
pr: 1613
claimed_by: run 9/21/2026, 1:46:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T07:36:05.962Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35569613071
---

The borderline roster keys the resident layer by the name a source prints, so a read name a crosswalk merged into a differently-spelt card is offered for re-admission beside the card that already holds the person.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1367**, which put asserted ledger units on the roster and so had to say, in a
rule statement, what an offered name off a spent claim means.

`tools/export_borderline_roster.py` builds `layer["by_name"]` from the cards' own names and
classifies a read name R0 only when that index hits. `data/research/books/crosswalk.json`
holds merges that join a read name to a card spelt otherwise, and the roster does not
consult them. So the Baptist catalogue's **Martin D. Harmon** is offered as an R2 name to
re-admit while `hh_harmon_m_d` — the card the crosswalk committed him to, and the card
T-1367 just wrote his 1833-10-19 arrival onto — already holds him. Re-admitting him would
mint a second copy of a person this layer carries, which is the exact thing rule 1 of
`classify` exists to prevent.

The same gap applies to every committed merge whose `into` and `from` differ. Willard Jones
and Nathaniel Carpenter are printed whole on both sides and so are caught by the name index;
M D Harmon is not, and nothing but the crosswalk says he is the same man.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. A read name a crosswalk merged into a card is R0, under a rule that names the merge and
   the card, not R2. Measured: how many offered rows leave the roster, listed by name.
2. A refusal in the crosswalk is NOT a merge and must not make a name R0 — the catalogue's
   Peter Moore was refused against Henry Moore and stays offered.
3. `--check` and `--self-test` green; the accounting identity still holds.
