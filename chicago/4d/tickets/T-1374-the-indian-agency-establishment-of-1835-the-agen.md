---
id: T-1374
title: The Indian Agency establishment of 1835: the agent, sub-agent, interpreter and agency blacksmith as the sources name them, and the Native and Metis employees and families the records only count, through T-1177's review rules
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-21
pr: 1627
claimed_by: run 9/21/2026, 2:42:03 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T13:53:29.959Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35573791376
---

The Indian Agency establishment of 1835: the agent, sub-agent, interpreter and agency blacksmith as the sources name them, and the Native and Metis employees and families the records only count, through T-1177's review rules.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Raised by T-1349 while closing the second half of **T-1176 — Reconstruct the Fort Dearborn
garrison of 1 July 1835**. That parent was split in two: T-1348 took the officers and
T-1349 took the companies, the laundresses, the soldiers' families and the sutler. **The
Agency is in neither**, and the parent's close would have lost it.

The parent's own words for this piece: *"the Agency establishment (the agent, sub-agent,
interpreter, blacksmith of the agency) as the sources name them, its Native and Métis
employees and their families reconstructed where only counted — through T-1177's rules,
`review_required`, `touches_removal`."*

It is filed separately rather than bolted onto the garrison stage for a reason: it is a
**reviewed-community** unit. `tools/reconstruct_residents_1835.py` refuses a Native or Métis
reconstruction written by any stage but `underdocumented`, and AGENTS.md's Indigenous-history
review is what that refusal enforces. Whoever takes this should read T-1177 first and expect
to work inside its stage rather than beside it.

`data/structures/fort_dearborn_us_factors_house.json` is in the record and the 1830 Harrison
plan names it; `docs/RESEARCH/fort_dearborn.md` is the fort dossier.

**Links:** T-1176 (parent) · T-1348 · T-1349 · T-1177 · `docs/RESEARCH/fort_dearborn.md`.

**Absorbed from T-1412 (withdrawn 2026-09-20).** That ticket asked for the
same establishment as a *civic* one and named four people to seat at the council house:
the agent, **Billy Caldwell** the interpreter, **David McKee** the blacksmith and **Joseph
Porthier** the striker. Those names are carried here so the withdrawal loses nothing — and
they are a reading to make, not a roster to write: T-1412 itself said the agency's standing
on 1 July 1835 is to be read *before anything is written*, which is this ticket's rule too.
The striker is a role T-1374's parent did not name, so it is an addition and not a repeat.
