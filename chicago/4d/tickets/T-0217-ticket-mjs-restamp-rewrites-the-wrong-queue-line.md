---
id: T-0217
title: ticket.mjs restamp rewrites the WRONG queue line when the id it is repairing is the duplicated one
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 403
claimed_by: run 8/27/2026, 10:22:34 AM CT
blocked_on: null
needs_bake: false
---

ticket.mjs restamp rewrites the WRONG queue line when the id it is repairing is the duplicated one.

**Found by using it, 2026-08-27, during T-0215's merge.** Two branches had each been given
`T-0211` — dev's *"The other nine group rows are cross-checked against nothing"* and this run's
*"Desktop smoke stage 8 …"* — which is precisely the case `restamp` exists for. It renumbered the
right FILE and rewrote the WRONG QUEUE LINE:

```
  before        T-0211 — The other nine group rows are cross-checked against nothing   <- dev's
                T-0211 — Desktop smoke stage 8 (What's-new) is red on dev …            <- mine
  after         T-0215 — Desktop smoke stage 8 (What's-new) is red on dev …            <- dev's line, CLOBBERED
                T-0211 — Desktop smoke stage 8 (What's-new) is red on dev …            <- mine, left stale
```

**The cause is one line**, `case 'restamp'` in `tools/ticket.mjs`:

```js
const line = queueIds().indexOf(old);   // FIRST line carrying that id
…
if (line >= 0) queueReplace(old, [`${t.id} — ${t.title}`]);
```

`indexOf` and `queueReplace` both key on the id, and **with a duplicate id there are two lines
carrying it**. Which one moves is whichever appears first in the owner-ordered file — a coin toss.
The comment directly above that code is the sharp part: it explains that the ticket is found by
FILE rather than by id, *"with two files sharing an id, `find` by id cannot tell them apart"* — and
then the queue edit two lines later goes back to matching on the id.

**Consequences, in order of nastiness.** A queue line the owner ordered is silently overwritten
with another ticket's title, so a real ticket vanishes from the queue while a phantom line for an
id that no longer exists stays in it. `ticket.mjs check` did NOT refuse either state; it was caught
by reading `tail QUEUE.md`. It was repaired by hand in that run.

**Acceptance:** on a queue holding the same id twice, `restamp <file>` rewrites the line belonging
to THAT file and leaves the other alone — demonstrated by a self-test that builds the duplicate
and asserts both lines afterwards. Plus: `ticket.mjs check` refuses a queue line whose id is not in
the ledger, which is the condition that survived this and would have named it.
