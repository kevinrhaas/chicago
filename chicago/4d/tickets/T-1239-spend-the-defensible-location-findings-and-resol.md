---
id: T-1239
title: Spend the defensible location findings and resolve or explicitly retain T-0251, T-0305, T-0386 and T-1087, keeping placement proportional to evidence
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1147
opened: 2026-09-17
closed: 2026-09-17
pr: 1400
claimed_by: run 9/17/2026, 9:09:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T14:55:54.499Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35231191680
---

Spend the defensible location findings and resolve or explicitly retain T-0251, T-0305, T-0386 and T-1087, keeping placement proportional to evidence.

Piece 3 of 5 of **T-1147 — Spend every defensible home, workplace and business-location finding, preserve the 123 location limits, and close research with zero unclassified attested or inferred fact**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working, 2026-09-17 — T-1147 clauses 3 and 4; clauses 1/8/9
belong to T-1237, clause 2/7 to T-1238, clause 5 to T-1240 and clause 6 to T-1241)

1. Every business location claim in the committed reconciliation rows is graded by what the
   EVIDENCE reached and, separately, by what the MODEL seated it on. The two are never the
   same field: a street-only business adopted onto a roof under the owner's ruling of
   2026-08-29 reaches the street and is SEATED on the roof, and the seat is marked
   substitutable. Clause 3's "claims no lot or roof" is held by that separation, not by
   overturning the owner's ruling.
2. A structure limit that stands on an anchor the model cannot resolve is reported as what
   it is. No completion metric counts a roof the town has not built as a roof it has.
3. Nothing moves between the three published location limits. Clause 4 says they fall only
   when a new source or reading names the stronger anchor; this pass reads no new source, so
   the before/after shows the counts unchanged and the gate REFUSES a move.
4. T-0251, T-0305, T-0386 and T-1087 are each explicitly retained with the owner it belongs
   to, what it costs the town today, and what would resolve it. None is resolved here: three
   are `blocked-owner` and one is `blocked-tech`, and the loop guessing any of them is the
   error the provenance rule exists to prevent.
5. Each retention is held by a GATE and not by this file — a guard measured from the
   committed data it stands on, so the day the owner rules the build says so instead of the
   retention going quietly out of date. That is T-0305's own acceptance clause 5, applied to
   all four.
6. `--check` re-derives and refuses a hand-edit; `--self-test` breaks each assertion and
   requires it to fire; both are wired into `tools/check.sh`. No confidence is upgraded, no
   anchor filled, no citation minted, no building moved.

**Stop condition:** the location axis T-1157 reads at the sign-off is honest about its own
denominator, and the four questions the research cannot answer are retained in a form that
cannot rot.

**Links:** T-1147 (parent) · T-1237 (the rows this adjudicates) · T-0251 · T-0305 · T-0386 ·
T-1087 · T-1157 · T-1198.
