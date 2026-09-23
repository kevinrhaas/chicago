---
id: T-0231
title: T-0229's expiry was blocked on a flora ticket, so the raised ceilings would never have come down
state: open
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-27
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

T-0229 is the receipt for the owner's decision to raise the `full` and `balanced`
scene-detail ceilings. Its entire purpose is to bring them back down. It was
filed `blocked_on: T-0209` — and **T-0209 is a FLORA ticket about how far the
sward's bloom reaches across the ground it covers.** It has nothing to do with
timber, with the sun's shadow box, or with the triangle budget.

The measurement, the per-layer table and the costed cull are **T-0223**, and
always were.

## Where the wrong number reached

| file | what it said |
|---|---|
| `tickets/T-0229-*.md` | `parent: T-0209`, `blocked_on: T-0209`, the title, and 4 body references |
| `renderers/web/js/main.js` | **7** references in the `DETAIL` expiry block — lines 291, 295, 323, 331, 382, 390, 394 |
| `tickets/QUEUE.md` | the label, which is regenerated from the title, so it inherited it |

Eleven references, one wrong number, zero disagreement between them — which is
why nothing caught it.

## Why this one is not a citation typo

A stale citation in a research note costs a reader one lookup. **This ticket IS
its pointer.** `blocked_on` is machine-read: the loop skips a blocked ticket, and
`ticket.mjs` unblocks it when the named ticket closes. So the failure mode is
not "a reader is confused", it is:

- T-0209 (bloom) closes on its own unrelated schedule — it is an open M-effort
  FLORA ticket sitting in the queue's *WHAT GROWS* band, so this was going to
  happen;
- T-0229 unblocks and reads to an agent as **"the cull has landed, put the
  ceilings back"**;
- no cull has landed. The 180,100 triangles of pure-loss shadow work are still
  in every frame. Either the agent lowers the ceilings and re-opens a breach it
  cannot explain, or it reads the acceptance criteria, finds nothing to measure,
  and closes T-0229 keeping the raised numbers — **which is precisely the
  outcome the ticket was written to prevent.**

Meanwhile T-0223, which is the ticket that actually has to be worked, is blocked
by nothing and pointed at by nothing.

The ceilings themselves are correct and are not touched here. Nothing about the
owner's decision changes: it was a bounded raise, bounded by the cull, and it
still is. **Only the pointer was wrong.**

## How it got in

It was written by the same run that filed T-0229 and raised the ceilings, and
that run had T-0223's measurements in front of it — the 1,412,120, the 180,100,
the 14.4 %, the `measure_stand_budget.mjs` invocation. Every *number* in T-0229
is T-0223's and every number is right. Only the label attached to them is wrong.

That is the same failure this project has now recorded four times in one day, in
four different disguises: a real measurement attached to the wrong subject. The
desktop stage-8 red that was read as a What's-new defect and was machine load.
The triangle overage charged to #372's branch, which predated it. The wharf merge
pushed at `steward/t-0058-walk-the-wharf` when the PR's head was
`steward/t-0058-wharf-walk`. And this. **The measuring is not what keeps
failing. The attribution is.**

## What would have caught it, and what to do about it

Nothing in `check.sh` reads `blocked_on` at all, so an id that names a real
ticket is accepted whatever that ticket is about. Two cheap checks, in order of
value:

1. **`blocked_on` must name a ticket that is OPEN.** A ticket blocked on a
   *closed* ticket is either stale or wrong, and today it would have flagged
   nothing — T-0209 is open — so this is the weaker check. Worth having; not the
   fix.
2. **A `blocked_on` across epics is worth a WARNING.** T-0229 is `RENDERING`
   blocked on `FLORA`. That is not illegal — a real dependency can cross epics —
   but it is unusual enough to be worth a line of output, and it would have
   caught this one. It is a heuristic and should be a warning, never an error.

Neither is a real answer, and this ticket should not pretend otherwise: **the
honest reading is that an eleven-reference number with no disagreement between
its copies cannot be caught by a consistency check.** That is the same lesson
T-0207 wrote down when three conflict markers reached production through every
gate — *a consistency check cannot see a fault that both sides reproduce
faithfully.* The check that would have caught this is a human or an agent asking
"what is T-0209 actually about?" before writing it down eleven times.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `tools/check.sh` warns when a ticket's `blocked_on` names a ticket in a
  different epic, naming both epics, and errors when it names a ticket that is
  already closed.
- The warning fires on a synthetic fixture, not just on a clean tree — a check
  that has never been seen to fail has not been tested.
- Every existing cross-epic `blocked_on` in `tickets/` is listed in the PR body
  and stated to be either correct or wrong. If the warning is noisy on the
  current ledger, that is a finding about the ledger and it goes in the body;
  **it is not a reason to weaken the check.**

**Links:** T-0229 (the receipt, corrected) · T-0223 (the measurement and the
costed cull — the ticket that should have been named) · T-0209 (the flora ticket
that should never have been in this chain) · T-0207 (a consistency check cannot
see a fault both sides reproduce) · T-0217 (`ticket.mjs restamp` damaging a queue
line — the other id-handling defect open right now).
