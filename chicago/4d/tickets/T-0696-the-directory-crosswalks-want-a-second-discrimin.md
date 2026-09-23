---
id: T-0696
title: The directory crosswalks want a second discriminator: a trade separates 6 of the 33 contested groups and an 1835 premises 8, and the rule has none
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 969
claimed_by: run 9/6/2026, 12:56:31 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T06:17:49.633Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34015075391
---

The directory crosswalks want a second discriminator: a trade separates 6 of the 33 contested groups and an 1835 premises 8, and the rule has none.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Measured on dev after T-0670 (2026-09-04).** The crosswalks match on surname plus first initial
and now refuse a full-forename disagreement, and what is left over is the case the rule genuinely
cannot decide: one printed line that two people of 1835 both meet (CONTESTED), and one person of
1835 who meets several printed lines (AMBIGUOUS). Counting them:

| | Fergus 1843 | Norris 1844 |
|---|---|---|
| contested groups (residents) | 18 (43) | 15 (39) |
| …a trade printed in 1835 names exactly one of the rivals | 4 | 2 |
| …an 1835 premises names exactly one of the rivals | 4 | 4 |
| ambiguous residents | 51 | 28 |
| …an 1835 trade picks exactly one of the printed entries | 2 | 4 |

So a second discriminator is worth having and is not a landslide: on the coarse test above it
settles 6 of the 33 contested groups on the trade, 8 on an 1835 premises, and 6 of the 79 ambiguous
residents. The test is coarse on purpose — it is a substring of the 1835 occupation against the
printed one, and the residents vocabulary and the directories' trade words are not the same
vocabulary (T-0661 is the ticket for the words themselves).

**The ask.** Decide whether a trade, an address or a year may BREAK a tie, and on what terms — a
tie broken on a trade is a stronger claim than a tie left standing, and this reconstruction's rule
has been that an undecided reading is filed rather than resolved. If the answer is yes, the
discriminator has to be graded and cited like everything else, and the loser of the tie has to be
recorded as refused with the discriminator named. If the answer is no, write that down: it is a
standing question and it will be asked again.

**Links:** T-0670 (the rule this extends) · T-0661 (the trade vocabulary the test needs) ·
`tools/name_agreement.py` · `tools/crosswalk_fergus_1843.py` · `tools/crosswalk_norris_1844.py`.
