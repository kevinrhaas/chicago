---
id: T-1343
title: Spend the 128 press notices onto the cards they name, on identifications a committed newspapers-to-residents crosswalk makes, and refuse in writing the ones it cannot make
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1338
opened: 2026-09-18
closed: 2026-09-18
pr: 1499
claimed_by: run 9/18/2026, 9:54:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T04:27:28.774Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35416872113
---

Spend the 128 press notices onto the cards they name, on identifications a committed newspapers-to-residents crosswalk makes, and refuse in writing the ones it cannot make.

Piece 2 of 2 of **T-1338 — Spend the 128 press notices onto the cards they name, once a newspaper claim unit carries a file-qualified ledger id: the 22 raw claim ids these units share would close 937 other units as asserted**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**T-1342 unblocked this and enlarged it (2026-09-18).** A press claim can now be named
by a bound: the ledger key is the issue file's stem and the claim id joined by `#`. Two
things arrived with that.

* **148 units, not 128.** Repairing the bare-id collision unmade 142 assertions the
  ledger had been making off three resident cards, and 20 of those had nothing in them
  to route on: 19 newspaper notices, persons, events, shipping and price rows, and one
  civic claim — Andreas on how the town got its water by cart from the foot of Randolph
  Street, read as an assertion about George W. Dole's reason for coming because its id
  is `c013` and so is the Democrat claim that card cites. They are claim units of the
  same corpus and are spent with the press notices.
* **`EPIC_PIECES["civic"]` points here** rather than at the closed T-1297, so closing
  this ticket means finding an owner for what is left of the civic claims — the
  `spend_remainder_rulings.py` register rules four domains and refuses civic by name.

**Acceptance:** to be stated by the run that takes it, before working.
