---
id: T-0602
title: The research-spend ratchet counts a precision sample as reading, and an unanchored refusal as nothing
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 776
claimed_by: run 9/4/2026, 6:19:38 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T11:43:00.912Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33867094965
---

The research-spend ratchet counts a precision sample as reading, and an unanchored refusal as nothing.

**What the ratchet does, and it works.** `tools/measure_research_spend.py` counts, per research domain, the
named units READ and the ones RULED ON, and `check.sh` fails when a domain's unspent count passes its
ceiling in `tools/research_spend_baseline.json`. It exists because the owner asked, on 2026-09-03, "i see
lots of research being done and some apparent findings from parsing but there are not outputs or updates to
the household and resident data it seems, should i be concerned?" He was right, and T-0590 answered it for
the Newberry domain within the day — 319 leads ruled, 542 cards anchored, the ceiling down from 2,619 to
2,077. **This ticket is not an argument that the ratchet should let a domain off.** It is two counting
faults T-0578 hit while raising the ceiling for volume 2, and both make the number say the wrong thing.

**Fault one: a re-reading counts as a reading.** `count_read` walks every JSON in a domain but the
crosswalks and counts any `records` or `claims` entry carrying a name key. `precision_sample.json` holds
80 hand-adjudicated rows which are re-readings of records already counted, so the Newberry domain is
charged 80 units for MEASURING ITSELF. Sampling harder should not read the meter up.

**Fault two: a written refusal counts as nothing.** `count_spent` only sees a crosswalk ruling that carries
an id anchor, so `crosswalk.json`'s one pass and five written refusals — including the Beaubien refusal,
which is the most carefully reasoned paragraph in the domain — count as zero. A refusal IS an
adjudication; that is the whole discipline of T-0505, and `lead_crosswalk.json` only counts because
T-0590 happened to anchor its rows to card ids.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- A domain file can declare itself not-a-reading (a measurement, a sample, an index of other files), and
  `count_read` skips it. State the corrected read figure for every domain, not just Newberry.
- An unanchored crosswalk ruling counts as an adjudication of the names it does carry, or the tool says
  out loud in its output why it cannot — silently counting zero is the failure.
- Every ceiling in `research_spend_baseline.json` is restated under the corrected counts in ONE commit,
  with the deltas listed, so no domain's ceiling silently loosens.
- The self-test gains a case for each fault.

**Effort.** S — the counting is one file and the domain registry already has a place to declare this.

**Links:** T-0578 (which hit both) · T-0590 (the ruling that shows the ratchet working) · T-0603 (the
volume-2 spend) · T-0505 (the refusal discipline) · `tools/measure_research_spend.py`.
