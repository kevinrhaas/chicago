---
id: T-0992
title: Second Presbyterian's 82 adjudicated roll members reach 82 cards and not one card cites the roll: spend them, and drop church's write ceiling back to zero
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-10
pr: 1063
claimed_by: run 9/10/2026, 3:56:53 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T09:45:42.751Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34457683689
---

Second Presbyterian's 82 adjudicated roll members reach 82 cards and not one card cites the roll: spend them, and drop church's write ceiling back to zero.

**Acceptance:** every card named by a `matched` row of the Second Presbyterian crosswalk cites the roll, and the gate reports church at 0 unwritten with the ceiling tightened to 0.

**Measured on this branch, 2026-09-10, landing T-0962.** With the second hop widened to read
the `matched` container, church entered the report for the first time: **82 reached, 82
judgeable, 0 on a card, 82 unwritten**. Independently confirmed — `grep -r
second_presbyterian_chicago_1892 data/residents/` returns **nothing**. Not one resident record
in the town cites the roll, so this is the whole debt, not a sample of it.

**What the rulings are.** The crosswalk adjudicates the 1892 printed roll of the Second
Presbyterian Church against the residents layer, filing 82 as `matched`, 37 as `ambiguous` and
330 as `refused`. Only the 82 are a spend — a rival still standing is not a ruling to spend,
which is the line MATCH_CONTAINERS draws and this ticket must not cross. Each matched row
carries `person_id`, `household_id`, `grade`, its `rule` (the reasoning that got it there) and
`roll_lines[]` with the printed line as read, the admission date, how admitted and the printed
page.

**The caution this one needs, and it is the whole difficulty.** The roll is an **1892**
printing and its admission dates run decades past the scene — `second_presb_0371` is admitted
27 April **1859**. An 1859 admission is not 1835 evidence and may not move a grade or mint
anybody; the ladder T-0505 ratified binds here exactly as it binds an 1840 head.
`tools/spend_census_1840_heads.py` is the shape to copy: two fields, no grade moved, the limit
quoted in the card's own words rather than paraphrased, `--check` and `--self-test` gated in
the same commit so the pass re-derives and cannot drift.

**Links:** T-0962 (widened the hop and found this) · T-0698 / `tools/spend_census_1840_heads.py`
(the same debt paid on census_1840, and the pattern) · T-0700 (a paragraph present and no
longer true is the failure that looks like success) ·
`tools/research_spend_baseline.json` § `raised` (the entry recording the 82).

**THE COUNT IS 83, NOT 82** (2026-09-10, lapping this branch onto dev). The title and the
paragraphs above say 82 because that is what the crosswalk held when T-0962 measured it this
morning. While this branch was open dev minted **Mrs C. Taylor** (`hh_taylor_c`, T-0960,
PR #1050/#1051), the Second Presbyterian crosswalk re-derived onto her — roll line
`second_presb_0870`, *"Taylor, Mrs. Charle's | Letter. | Januarys, 1843. | Dismissed."*,
printed page 203, matched on the same surname-plus-initial rule as the other 82 — and the
`matched` rows went 82 → 83.

The debt therefore grew by one, and `research_spend_baseline.json` § `raised` carries the
reason: **not** because church read further ahead (the reading has not changed), but because
the TOWN gained a card underneath it. That is the ladder working, not a hole opening, and it
is the one reason this ceiling may move. Whoever works this ticket should expect **83**, and
should re-measure rather than trust this number either: another card minted before it is
worked moves it again, for the same good reason.

Note that `hh_taylor_anson` is named twice in the 83 and that is correct — two people of one
household, Anson H. and Charles, on two roll lines. 83 rows, 82 distinct households.
