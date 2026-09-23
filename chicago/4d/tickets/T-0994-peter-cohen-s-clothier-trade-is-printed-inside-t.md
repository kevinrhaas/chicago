---
id: T-0994
title: Peter Cohen's clothier trade is printed inside the scene window at the Democrat of 8 July 1835: recite it, and gate the standing population T-0837's write gate cannot see
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0872
opened: 2026-09-10
closed: 2026-09-10
pr: 1053
claimed_by: run 9/10/2026, 1:24:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T06:48:19.040Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34444266608
---

Piece 1 of 2 of **T-0872**, and the half the corpus can settle without the owner.

T-0872's first arm says a row is kept "because a source that DOES describe the scene window
says the trade, and that source is now the one cited". Read against the corpus, exactly one
of the nine standing rows qualifies. The Chicago Democrat of 8 July 1835 prints Peter
Cohen's own signed advertisement — "[New] and cheap Goods, [AT] HIS OLD STAND … [Dry] Goods,
Groceries, [Boots, Shoes,] Clothing and Miscellaneous Arti-[cles]. […] PETER COHEN." — seven
days after the scene date, where the card cited nothing but the issue of 26 November 1833.

It answers a second question the same card recorded as open: `present_on_scene_date` read
`uncertain`, reasoning that he was "documented in the town in November 1833 and not followed
by anything reached to 1835". The window does follow him there.

The other eight are T-0991's, and the audit is why the count is knowable at all: T-0837's
write gate cannot see a standing field, and its refusal is suppressed on precisely these
cards, because the synthesizer declines to overwrite a filled field before it ever reaches
the date test.

**Acceptance:**

1. `cohen_peter`'s 1835 `occupation` cites a source whose `describes_date` covers 1835, with
   the July 1835 printing quoted and the limit of its own word stated — the copy advertises
   a general assortment, not the word "clothier".
2. `present_on_scene_date` moves off `uncertain` on that printing, at the grade the
   seven-day gap earns and no higher.
3. `tools/audit_scene_window_trades.py` measures the standing population, adjudicates every
   row, and its ledger may only fall; `check.sh` runs `--check` and `--self-test`.

**Links:** [[T-0872]] (the parent) · [[T-0991]] (the eight it could not settle) ·
[[T-0837]] (the write gate).
