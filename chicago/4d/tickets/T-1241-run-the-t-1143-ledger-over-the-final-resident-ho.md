---
id: T-1241
title: Run the T-1143 ledger over the final resident, household, business and structure layers and publish the closing research audit at zero unclassified units
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1147
opened: 2026-09-17
closed: 2026-09-17
pr: 1434
claimed_by: run 9/17/2026, 8:59:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T02:36:39.542Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35297188435
---

Run the T-1143 ledger over the final resident, household, business and structure layers and publish the closing research audit at zero unclassified units.

Piece 5 of 5 of **T-1147 — Spend every defensible home, workplace and business-location finding, preserve the 123 location limits, and close research with zero unclassified attested or inferred fact**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance** (stated before working, PR #1434):

1. `tools/report_research_closing_audit.py --build` writes
   `docs/RESEARCH/research-closing-audit-2026-09.md`: the closed ledger read ONTO the
   resident, household, business and structure layers, then each layer read directly, with
   every figure derived and none typed. `--check` re-derives it and is wired into
   `tools/check.sh` beside the ledger steps, with a mutation self-test.
2. The report ends at zero unclassified units, zero dead asserted targets and zero units
   deferred to work that is not live — and names the gaps it does NOT close, each with the
   ticket that carries it. It makes no GO/NO-GO judgement; that is T-1157's signature and
   this is the evidence under it.
3. The deferral trap recorded below is defused, because otherwise this ticket cannot close
   at all: the place-and-enterprise remainder is repointed off the exhausted T-1147 onto the
   pieces that still have that corpus to spend — 494 enterprise units to T-1180, 269 place
   units to T-1198 — by the same routing `EPIC_PIECES` already performs. No unit was
   reclassified and no disposition moved; only the owner did.


## IT WAS FOLDED INTO T-1157 AND THE GATE REFUSED IT (2026-09-17)

The owner asked for the research spend to be tightened, and three tickets standing at the
end of the band — T-1144, T-1241 and T-1157 — looked like one act. T-1144 folded cleanly.
**This one did not, and the reason is worth keeping.**

`research_spend_ledger.py` holds a strict invariant: *a unit may only defer to work that is
still going to happen.* **748 unresolved units** across the book, directory and letter-list
claims defer to T-1147, and a `split` parent only counts as live while at least one of its
children is open. T-1237, T-1238 and T-1239 are done; folding away T-1240 and this ticket
left none open, T-1147 stopped reading `split_live`, and all 748 units were suddenly
deferred to finished work. `measure_research_spend.py --check` failed on every one.

So this stays open, and consolidating it is not a matter of a tidier queue — it would need
those 748 units repointed at whatever absorbs it, which is a bigger and riskier change than
the saving.

**What DOES carry over is the tightening.** Run this in the SAME PASS as T-1157: the ledger
over the final layers is that report's evidence section, not a separate expedition. One run
produces both, and the closing figures are published with the sign-off rather than ahead of
it. T-1240 stays folded into T-1255 — one open child is all the invariant needs, and this is
it.
