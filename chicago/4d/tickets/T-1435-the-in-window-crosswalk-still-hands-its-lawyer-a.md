---
id: T-1435
title: The in-window crosswalk still hands its lawyer and physician shortfall to T-1186, whose two children are both closed: re-point owed_to at the ticket that actually reconciles the crosswalk
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: null
claimed_by: null
blocked_on: Already inside T-1420's scope. T-1420 asks for the order book's dead owner ids to be re-pointed AND for 'the same sweep for any other ticket id the order book names that has since closed or split'. T-1435's finding is exactly that: the in-window crosswalk hands its lawyer and physician shortfall to T-1186, which is now split. Verified both today — T-1192 (named at build_order_book_1835.py:272) and T-1186 (named in compile_businesses.py and complete_inwindow_trades.py) are both in state split. One sweep, one ticket.
needs_bake: false
closed_at: 2026-09-20T23:17:06.248Z
claimed_run: null
---

The in-window crosswalk still hands its lawyer and physician shortfall to T-1186, whose two children are both closed: re-point owed_to at the ticket that actually reconciles the crosswalk.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-1419, whose closure is what exposed it.** `tools/ticket.mjs done T-1419` warned
that something hands units to **T-1186** and that T-1186 needs a live owner before the merge.
It does: `tools/complete_inwindow_trades.py:525` writes `"owed_to": "T-1186"` onto two rows of
the in-window crosswalk re-run — **lawyer, still short 4** and **physician, still short 6** —
and T-1186 is a `split` parent whose only two children, T-1418 and T-1419, are now both
closed. Nothing is lost yet, because the shortfall is a *documented* reading rather than an
orphan (T-1418's own worked section says why there are three law offices and not fifteen: the
census lines behind the group count MEN, and the count was read down to the population the
scene date actually had). But the string now names an epic nobody is working, which is the
exact shape of the defect T-1423 records.

**Acceptance:** `owed_to` on those two rows names a ticket that is OPEN — **T-1190** reads
like the right one, since its clause 4 re-runs this very crosswalk per class — or states in
the row itself that the shortfall is a closed reading and owes nobody anything. Re-derive
`data/research/residents/inwindow_trade_workplaces.json` in the same commit; `check.sh` runs
`complete_inwindow_trades.py --check` and will catch a hand edit.

**Links:** T-1419 · T-1418 · T-1186 (the parent) · T-1404 · T-1190 · T-1423.
