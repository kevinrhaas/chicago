---
id: T-0846
title: The four other spend passes can write the same paragraph onto a card twice, and their gates cannot see it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-11
pr: 1114
claimed_by: run 9/11/2026, 2:46:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T08:02:07.589Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34575666421
---

The four other spend passes can write the same paragraph onto a card twice, and their gates cannot see it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`tools/spend_land_sales.py` grew a `doubles()` gate under T-0677 after this run wrote every
one of its thirty-one cards twice and `tools/check.sh` stayed green. The cause was general,
not particular to the land sales: each spend pass finds its own work by a MARKER sentence,
and asks only whether that marker is PRESENT (`gaps`) and whether an unruled card carries it
(`strays`). Neither question can see a card that carries the marker twice, nor one carrying
a superseded pass's paragraph about the same source beside the current one. A pass that gets
rewritten — as this one was between T-0635 and T-0636 — leaves the older version pushed on a
branch, and running it appends rather than overwrites.

The four that carry no such rule (checked 2026-09-05: only `spend_land_sales.py` counts
marker occurrences):

  tools/spend_civic_voter_lists.py
  tools/spend_directories.py
  tools/spend_fergus_1839_later_lists.py
  tools/spend_ladder_rungs.py

**Acceptance:**

1. Each of the four holds the once-each rule in its `--check`, in the shape T-0677 used:
   a `doubles()` reading every household, faulting on a marker written more than once.
2. Each is demonstrated RED — the fault staged, the gate firing — and green on `dev`.
3. `--self-test` covers both directions in each, and no card's text changes: this is a
   gate, not a rewrite. If the sweep finds a card already doubled on `dev`, that repair is
   its own ticket and is named rather than folded in here.

Whether the four should share one implementation instead of four copies is worth a look
while doing it; T-0677 deliberately did not generalise ahead of the second case.
