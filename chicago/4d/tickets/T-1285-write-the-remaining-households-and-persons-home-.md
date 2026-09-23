---
id: T-1285
title: Write the remaining households' and persons' home and workplace claims as associated_with rows, and move every reader off the singular lives_at/works_at
state: split
epic: META
requested_by: loop
seen: false
effort: L
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T16:26:47.568Z
claimed_run: null
---

Write the remaining households' and persons' home and workplace claims as associated_with rows, and move every reader off the singular lives_at/works_at.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

T-1238 defined `associated_with[]`, gated it at both the household and the person level
and moved four records onto it. 1,253 have not moved, and nothing reads the rows yet.

**What is left.** T-1237's committed reconciliation carries the claims: 20 households name
a roof, 50 name a workplace, 52 reach a division and no further, and 28 later-directory
addresses survived the back-projection rule. Each is a row somebody can write WITHOUT
re-adjudicating any evidence, because the disposition and the limit clause are already
committed. The ones that still need adjudication are T-1239's, not this ticket's.

**And the readers.** `lives_at`/`works_at` are read by four renderer files and about
thirty tools. Until they move, both shapes stand and `singular_drift` in
`tools/associations.py` is what stops them disagreeing. Retiring the singular pair is the
second half of this ticket and is what makes the dates load-bearing rather than extra.

**Acceptance:** (state it before working - one demonstration, never weakened to pass)

1. Every committed home/workplace claim in `data/research/location_reconciliation.json.gz`
   with a `resolved` or `limited` disposition is an `associated_with` row on the record it
   belongs to, carrying the row's own date, rung, confidence and limit clause. No claim
   changes value, confidence or source in the move.
2. `tools/associations.py --check` prints the new coverage and the banked-unread entries
   for the fields are un-banked in the commit that wires a reader up, never before.
3. No confidence is upgraded and no date is borrowed: a claim T-1237 dated to the scene
   date because a singular field could mean nothing else is written `undated` unless a
   source dates it.

**Size.** This is more than one run: the row-writing generator is one demonstration and
moving four renderer files plus thirty tools off the singular pair is another. Split it
when it is reached.

**Links:** T-1238 (the schema) · T-1237 (the rows it reads) · T-1239 · T-1240 · T-1147.
