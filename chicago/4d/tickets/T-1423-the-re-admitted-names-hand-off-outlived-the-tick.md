---
id: T-1423
title: The re-admitted names' hand-off outlived the ticket that carried it: 325 unresolved research units name T-1394, whose closeout is spent, so they need a live owner for the evidence question T-1179's reconciliation never settled
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-20
pr: 1556
claimed_by: run 9/20/2026, 2:20:41 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T08:12:45.716Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35496291488
---

The re-admitted names' hand-off outlived the ticket that carried it: 325 unresolved research units name T-1394, whose closeout is spent, so they need a live owner for the evidence question T-1179's reconciliation never settled.

**What the reading found.** The hand-off did not outlive ONE ticket. It has outlived four, and
its neighbour outlived three. The roster hand-off ran **T-1159 → T-1172 → T-1179 → T-1394 →**
(this ticket), and the arrival hand-off above it in
`tools/spend_name_on_a_roll_rulings.py` ran **T-1169 → T-1318 → T-1329**. Every rename was
forced by the same invariant working exactly as designed — `research_spend_ledger.py` refuses
an `unresolved` unit whose owner is not an open ticket — and not one of them brought a source
any nearer. One of them was expensive: when T-1179 went to `split`, the gate fired inside
`rederive.mjs --run`, which `.github/steward/pr-lap.sh` runs on every lap, and *"the lap
stopped pushing and three PRs sat dirty with no gate able to run on them."*

**Why no ticket can own it.** These 266 units (the count above was 325 before T-1418 and
T-1422 spent some of the civic corpus) ask one question: was a name the research READ and
the town WITHHELD — since re-admitted at the reconstructed tier in
`data/reconstruction/1835_readmissions.json`, with its own `withdrawn_if` clause — in the town
on 1 July 1835? T-1394's three children did real work (the rebuild order a fixed point, a
liberty entry per stage, the minting stage on the People view's filter) and these units were
not one document nearer settled, because what those tickets reconciled is the LAYER and what
is open is the EVIDENCE. Only a source answers it, and none is in hand. The register already
wrote the ruling against its own practice: *"'wait for somebody to decide' is not a
disposition, it is a deferral wearing one."*

**Acceptance:** (stated before working — the definition of done, never weakened to pass)

1. An `unresolved` ruling may name a ticket **or** state `awaiting_evidence` — the document
   that would reopen the unit — and never both. `research_spend_ledger.py` gates it in one
   place (`unresolved_owner_faults`), read by the three ruling registers and by the ledger's
   own document check, so the rule cannot drift between them.
2. A wait that states no evidence is refused, at the same 40-character floor a `statement`
   already has to clear. A bare wait is the deferral this rule exists to end.
3. The five rules carrying these units name no ticket and each states what would reopen its
   own kind of unit: the COOK-residence purchasers, the letter-list names, the roll names the
   town does not hold, the surnameless 1832 enrollments, and the enrollments the rolls do not
   carry.
4. Every new assertion fires under mutation in
   `measure_research_spend.py --ledger-self-test`, and the honest shape is shown to PASS —
   a mutation test alone cannot show that.
5. The ledger's two readers print both shapes: the spend report, the closing audit and the
   sign-off each show the ticket-owned table and the reopening-condition table beside it, and
   the sign-off's **C3** reads "defers to a ticket that is still live, **or** states the
   evidence that would reopen it" so that 266 units waiting on a document are not counted as
   266 units deferring to finished work.
6. `./tools/check.sh` green, and the derived registers, ledger, roster and reports re-derive.

**What this ticket does NOT do.** It decides no residency, moves no confidence, mints and
retires nobody, and invents no citation. The units stay `unresolved`, because they are. What
goes away is the standing claim that somebody is working on them.

**Links:** T-1159 · T-1172 · T-1179 · T-1394 · T-1420 (the same defect in
`build_order_book_1835.py`, still open) · T-0660.
