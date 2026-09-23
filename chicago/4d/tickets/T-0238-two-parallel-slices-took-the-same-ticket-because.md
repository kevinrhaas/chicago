---
id: T-0238
title: Two parallel slices took the same ticket, because the rule that ranks them is evaluated per-slice
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the lane runs one slice (focus.json custom slices: 1), so the per-slice ranking fault cannot occur
needs_bake: false
closed_at: 2026-09-10T04:20:11.248Z
claimed_run: null
---

Two parallel slices took the same ticket, because the rule that ranks them is evaluated
per-slice.

**Observed 2026-08-27**, batch of five slices on this app. Slices are told `SLICE: k of N`
and take the **k-th** ticket from `ticket.mjs list --workable`, so that N runs starting from
an identical repo state land on N distinct rows. Two of them shipped T-0146 — one merged
into PR #408, the other threw its work away after finding the rival branch — and the two
runs each spent about an hour on it.

## Why the k-th rule did not separate them

Because *k-th* is applied to a list each slice filters for itself, and the filtering is the
part that moves. The workable list opened:

    1  T-0223   the ceilings are breached
    2  T-0229   the raise expires with T-0223's cull      <- blocked_on: T-0223
    3  T-0146   merge far chunks back into single draws
    4  T-0147   re-lower the ceilings once the trims land

`ticket.mjs list --workable` prints T-0229 as workable, and it is not: its acceptance
requires *"T-0223's first step has landed"*, and T-0223 was being worked by slice 1 in the
same batch. Both the improve prompt and `tickets/README.md` tell a slice to skip a ticket it
would reject anyway and take the next one below. So slice 2 skipped T-0229 and took T-0146 —
correctly — and so did whichever slice ranked it third by the same reasoning. **Two slices
applied the documented rule and collided**, because the rule is *"count only the items YOU
could run"* and different slices legitimately count differently.

`ticket.mjs claim` did not catch it either. Both runs called `inflight` before starting and
both saw nothing: the branches did not exist yet. `claim` reads `git ls-remote` at the moment
it is called, and five slices dispatched in the same tick all call it inside the same minute.
That is the window the README already admits it cannot close for id allocation, one file
over.

## The options, since the fix is a choice and not a derivation

1. **Make the list authoritative rather than advisory.** `list --workable` excludes a ticket
   whose `blocked_on` names an open ticket, so every slice filters the same list and *k-th*
   means the same row to all of them. T-0229 would not have appeared, T-0146 would have been
   row 2, and slice 3 would have had T-0147. Cheapest, and it fixes the observed case
   exactly — but it only holds while every reason to skip a ticket is machine-readable, and
   "I would reject this anyway" generally is not.
2. **Claim before working, not in the first commit.** Push an empty claim branch as the
   first action of the run. Turns a one-hour window into a one-minute one; costs a branch per
   run and needs a sweeper for the ones whose runs die.
3. **Let the dispatcher assign the row.** `steward-focus.yml` reads the queue once and passes
   each slice its ticket id, instead of five runs each deriving one. Removes the race by
   construction; moves queue knowledge into the workflow, which is outside a steward run's
   scope to edit (AGENTS.md § How work ships).

## Acceptance

(state it before working — the definition of done, never weakened to pass)

A batch of parallel slices starting from one repo state cannot land two runs on one ticket,
demonstrated rather than argued: a test that replays this batch's queue — T-0223 open,
T-0229 `blocked_on` it, T-0146 and T-0147 below — and shows five slices resolving to five
distinct ids. If the chosen route is (1), `tools/ticket.mjs` grows the filter and its
self-test covers a `blocked_on` chain; if (2) or (3), say in the PR why the cheap one was
not enough.

**Links:** `tickets/README.md` § *A claim is only real once its PR merges* (the T-0062
collision, the same shape a day earlier, before slices were parallel) · PR #408 and its
duplicate-slice comment, which has both implementations' measurements · `.github/steward/improve.md`
§ PARALLEL SLICES in `kevinrhaas/polecat-platform`.

---

## THE RATE, MEASURED — 2026-08-28, appended when T-0284 was found to be this ticket's duplicate

T-0284 was filed on 2026-08-28 for the T-0256 double-claim **without searching
the ledger first**, and this ticket already owned the defect — with the better
mechanism, since what T-0284 wrote down as an untested hypothesis (the ranking
shift) this ticket had already established from the two runs' own lists.
T-0284 is withdrawn; its one contribution that outlives it is the measurement
its acceptance demanded, which is this section.

**Counted across the merged PR ledger, #386–#497 (2026-08-27 05:36Z to
2026-08-29 02:37Z — the whole parallel-batch era on this app): 13 tickets
received two PRs each, out of roughly 90 tickets attempted. About one slice in
seven duplicates another's work.**

| ticket | PRs (merged first) |
|---|---|
| T-0096 | #447 → #466 |
| T-0137 | #438 → #440 |
| T-0211 | #458 → #459 |
| T-0221 | #425 → #427 |
| T-0224 | #464 → #465 |
| T-0225 | #450 → #452 |
| T-0229 | #397 → #414 — *possibly a legitimate two-stage ticket, not a collision* |
| T-0256 | #448 → #454 (T-0284's case) |
| T-0257 | #460 → #462 |
| T-0290 | #475 → #480 |
| T-0291 | #478 → #479 |
| T-0292 | #476 → #481 |
| T-0294 | #493 → #492 |

So 12–13 of ~90, call it **14 %**. All twelve unambiguous duplicates were
closed unmerged (eight of them by hand on the owner's instruction, 2026-08-28)
— so the *damage* rate to dev is zero so far, and the cost is pure wasted run
time: roughly one run-hour per collision, an hour in seven of the loop's whole
throughput.

**Two more findings from the same sweep, both this ticket's mechanism wearing
other clothes:**

1. **A slice can be cut from a sibling's tree, not from dev.** #492 (T-0294,
   slice 8) carried stowaway commits touching `fort_structure.py` and
   `measure_generator_half.py` — no December-1834 read touches those. Merging
   it would have landed a sibling's work twice.
2. **Ticket IDS collide by the same blindness.** #489's run filed its
   letter-list ticket as T-0321 while dev assigned T-0321 to a different
   ticket; `restamp` (T-0331) was the remedy. `new` allocates ids from the
   tree the run can see, which is the same stale view `claim` reads.

The batch width went 3 → 5 → 8 across the window, and the duplicates cluster
in the 8-slice era — consistent with exposure growing with N, still not
proof. The options in this ticket's body stand unchanged; option 2 gained raw
material on 2026-08-28 when polecat-platform's `claim-notice.sh` (#145) began
writing the claimed ticket to the journal at claim time.
