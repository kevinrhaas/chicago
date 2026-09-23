---
id: T-1341
title: ticket.mjs --check REPAIRS the mirror it is checking, so on any branch that adds a ticket the gate's queue step mutates tickets.json while the pool reads it — the T-0856 check-that-repairs fault, one tool over
state: open
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-18
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

ticket.mjs --check REPAIRS the mirror it is checking, so on any branch that adds a ticket the gate's queue step mutates tickets.json while the pool reads it — the T-0856 check-that-repairs fault, one tool over.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `node tools/ticket.mjs check` writes NOTHING, on a consistent tree and on a stale one
   alike. It reports the staleness and exits non-zero; repairing is what `--write` (or
   whatever the repair mode ends up called) is for.
2. Measured the way it was found: the probe from T-1339 over a consistent tree AND over a
   deliberately stale one, with `wrote: []` on both.
3. The gate step that runs it still catches a stale mirror — the point is that it REPORTS
   it instead of quietly mending it, so the drift is visible to the person whose branch
   caused it rather than gone before anyone looks.

## HOW IT WAS FOUND, AND WHY IT MATTERS

T-1339's measurement ran twice. The first run reported `tools/ticket.mjs` writing
`chicago/4d/tickets/BOARD.md`, `chicago/4d/tickets/tickets.json` and
`site/chicago/4d/tickets.json`; the second, on an otherwise identical tree, reported
nothing. That looked like contamination from the first run being taken while the tree
moved, and it was not:

    consistent tree   node tools/ticket.mjs check  →  wrote: []
    stale mirror      node tools/ticket.mjs check  →  wrote: ['chicago/4d/tickets/tickets.json',
                                                              'site/chicago/4d/tickets.json']

It repairs when it finds drift. The first run was taken on a branch that had just added a
ticket — which is exactly when the mirror is stale — so the repair fired.

**THIS IS T-0856 ONE TOOL OVER.** `read_census_1830.py --check` used to re-derive in place:
"that reads as a check and behaves as a REPAIR, so the first run printed FAIL and mended the
file, the second printed pass, and the drift was gone before anyone could look at it." The
same sentence is true here.

**AND IT IS A LIVE RACE, not only an untidy one.** check.sh runs its steps in a job pool
over one working tree (T-1289). On any branch that adds a ticket — which is most of them —
the queue step mutates `tickets/tickets.json` while whatever the pool scheduled beside it
reads the same tree. That is the T-1336 shape, in an ordinary `step` rather than a
self-test, which is the half T-1336 never measured.

## AND WHAT IT SAYS ABOUT T-1339's GATE

The gate reads a measurement taken on ONE tree state, so a CONDITIONAL writer is invisible
to it: this tool measures clean whenever the mirror happens to be current. T-1339's audit
therefore proves "no tool wrote on the tree this was measured on", which is weaker than "no
tool writes" and is now said in those words in its own `_doc` rather than implied.
