---
id: T-0727
title: Budget the walkthrough's boot payload, which is what a visitor actually downloads, rather than the whole published tree
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-16
pr: 1372
claimed_by: run 9/16/2026, 11:38:30 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T01:49:37.990Z
claimed_run: null
---

Budget the walkthrough's boot payload, which is what a visitor actually downloads, rather than the whole published tree.

**Acceptance:** a committed measurement of the bytes a first-time visitor actually
downloads to stand in the 1835 street — taken from real responses (the smoke already
drives a browser over the published tree), not from a hand-declared file list — plus a
budget on that number, and `docs/SITE-BUDGET.md` § 4 updated with what the whole-tree cap
is then for.

**Why (T-0722, 2026-09-05).** The 32 MB whole-tree budget is this project's own number;
GitHub's documented Pages limit is 1 GB. What a size budget is really for is the visitor's
download, and the tree total is a poor proxy for it in both directions:

* The 1,385 household cards are 28 % of the tree and cost a visitor nothing until they open
  that person. The record can grow ten times over without costing a byte at the door.
* A careless import into `walk/js/` costs *every* visitor immediately and moves the total
  barely at all.

So the tree total both blocks growth that is free and waves through growth that is not.
Measure the thing that is real, budget that tightly, and let the whole-tree cap relax into
the repository-hygiene guard it actually is. Until this exists, 32 MB stays — an unexamined
number is still a working brake.
