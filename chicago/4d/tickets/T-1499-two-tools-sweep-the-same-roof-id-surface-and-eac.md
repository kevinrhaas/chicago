---
id: T-1499
title: Two tools sweep the same roof-id surface and each keeps its own exemption list, so a file that is legitimately pinned must be named twice
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-21
pr: 1631
claimed_by: run 9/21/2026, 10:22:26 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T15:50:55.442Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35617821153
---

`tools/migrate_roof_ids.py` and `tools/execute_roof_redeal.py --check-migration`
both sweep the whole tree for files naming a roof id that has been migrated, and
both need a list of files that legitimately keep the old name. They keep SEPARATE
lists — `KEEPS_THE_OLD_NAME` in the first, `MIGRATION_PINNED` in the second — with
overlapping contents and the same reasoning written out twice.

**Measured on 2026-09-21.** `tools/measure_roof_id_migration.py` names an old id in
two places, both legitimate: its docstring explains the surface by naming a move
(a south id becoming its new family in place), and its self-test passes the old id
to `new_id()` as the worked example. Rewriting the fixture leaves it asserting
`new_id(<new id>, <its family>) == <the same new id>`, which is true of any already-migrated
id and therefore tests nothing.

It had to be added to `KEEPS_THE_OLD_NAME` on **#1588** and, an hour later and for
word-for-word the same reason, to `MIGRATION_PINNED` on **#1596**. Each addition was
made because a gate went red, not because anybody noticed the other list.

**Why it matters more than the duplication.** The two lists can DISAGREE, and a
disagreement is silent in the direction that hurts: a file pinned in one sweep and
not the other is red on whichever gate runs, and a file that should be stale but is
pinned in both is a dangling id nothing catches. The lists are load-bearing — a
dangling id in an enclosure or a signage run reads as a record about a building the
scene does not draw — and the only thing keeping them in agreement is that somebody
edits both.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. ONE list, in one place, with each entry carrying its reason, consumed by both
   sweeps. The categories both lists already recognise are kept and named: a dated
   receipt, an import report, a ticket's account of a day, a transcript or patch, a
   yard group named for a roof, prose about the rename itself, a self-test fixture,
   and the sweeping tool's own file.
2. A gate step asserting the two sweeps agree — same tree, same old ids, same
   verdict per file — so a future divergence is a red gate rather than a silence.
3. The re-derived files stay re-derived and are not folded into the pinned list:
   `MIGRATION_REDERIVED` is a different idea and a rewritten ledger would agree with
   the migration by construction.
4. Mutation-tested: remove one entry from the shared list and watch both sweeps
   report the same file, and pin a file that should be stale and watch the new
   agreement step refuse it.
5. `./tools/check.sh` green, and no committed file changes as a result — this is a
   consolidation, not a re-migration.

**This ticket demonstrated its own finding while being filed.** The first draft quoted the
migrated id literally, as the sibling tool's prose does. `execute_roof_redeal.py`'s
`MIGRATION_PINNED` exempts `tickets/` — "a ticket's account of what it found on a day [is]
TRUE as written" — and `migrate_roof_ids.py`'s `KEEPS_THE_OLD_NAME` does NOT. So one sweep
accepted the file and the other refused it, on the same tree, for the same text. The draft
was reworded rather than fix it here, because adding `tickets/` to the second list is a
behaviour change that belongs in this ticket's own slice and not in an unrelated PR — but
the divergence is now measured twice rather than argued once.
