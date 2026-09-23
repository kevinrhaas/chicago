---
id: T-0989
title: The second hop's file-level source fallback passes 817 of 1,364 rulings on a card that cites the file's one source id for any reason at all — which is how census_1840 read 27 of 27 written with 15 cards untold
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-10
pr: 1062
claimed_by: run 9/10/2026, 4:30:08 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T09:39:59.255Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34460366591
---

The second hop's file-level source fallback passes 817 of 1,364 rulings on a card that cites the file's one source id for any reason at all — which is how census_1840 read 27 of 27 written with 15 cards untold.

**Acceptance:** a ruling whose card cites the file's source for an unrelated reason is no
longer counted written, demonstrated on a case from the 15 below; and the ceilings the change
moves are re-measured, recorded with a reason, and reported honestly rather than tuned to keep
the gate green.

**Measured on the T-0962 branch, 2026-09-10.** `rests_on(ruling) or doc_rests_on(doc)` means a
ruling that states no sources of its own is judged against the ONE source id printed at the top
of its file. **817 of the 1,364 person-reaching rulings in this repo are judged that way** —
60% of the second hop:

```
   158  directories/fergus_1839_crosswalk_1835.json
   136  land_sales/resident_crosswalk.json
   119  directories/fergus_1843_crosswalk_1835.json
    99  civic/voter_crosswalk.json
    98  directories/norris_1844_crosswalk_1835.json
    92  directories/fergus_1839_election_crosswalk_1835.json
    62  old_settlers/death_notices_crosswalk_1835.json
    17  directories/fergus_1839_lots_crosswalk_1835.json
    17  directories/fergus_1839_register_crosswalk_1835.json
    16  directories/norris_1844_advertiser_crosswalk_1835.json
     3  census_1840/resident_crosswalk.json
```

For those 817 the test collapses to *does this card cite this source id anywhere, for any
reason?* — and a card citing it from a DIFFERENT pass satisfies every ruling in the file at
once. That is not a paraphrase of the risk; it is what happened.

**The instance, reproduced rather than remembered.** T-0962 reported that on `dev` at
`577c2f6f5` census_1840 read **27 reached, 27 judgeable, 27 written** while 15 of the 27 cards
carried no mention of the 1840 census. Running that commit's own tool over that commit's own
tree reproduces `27 / 27 / 27` exactly — and it reproduces them **out of
`resident_crosswalk.json`**, whose `heads` held 12 `matched` + 15 `candidate` = the 27. So the
diagnosis T-0962 recorded — that the hop never reads `resident_crosswalk.json` and counted a
different 27 — is wrong, and is wrong in the direction that matters: the hop SAW the head
rulings and passed them. `is_crosswalk()` is a substring test and `resident_crosswalk.json` has
always satisfied it. What passed them was this fallback: those heads carried empty
`discriminators` and `same_name_support`, so all 27 were judged against
`census_1840_chicago_familysearch_images`, which the cards already cited from the earlier
bridge work.

**Why this is not a one-line fix, and why it is its own ticket.** The narrow repair — demand a
per-ruling source — makes those 817 *unjudgeable*, and `unsourced_ceiling` defaults to 0 with
no allowance, by deliberate design (T-0598). The gate would go red in seven domains at once.
So the change has to arrive with a ruling about what the honest test is for a generated
crosswalk that states its basis once at the top, and that ruling is the ticket, not a detail
of it. `spend_census_1840_heads.py` shows the shape of an answer: what a card learns from a
ruling is a NAMED paragraph, and a hop that looked for that would not be satisfied by a bare
source id at all.

**Links:** T-0962 (found the symptom, misdiagnosed the cause; corrected here) · T-0598 (made
the unsourced hop a ratchet at 0, which is what this change collides with) · T-0698 /
`tools/spend_census_1840_heads.py` (spent the 27 by hand) · T-0992 (church's 82, the debt the
container fix uncovered) · `tools/measure_research_spend.py` § `count_written`, `doc_rests_on`.
