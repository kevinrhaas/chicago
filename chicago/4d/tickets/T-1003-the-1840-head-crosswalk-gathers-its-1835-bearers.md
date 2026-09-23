---
id: T-1003
title: The 1840 head crosswalk gathers its 1835 bearers by surname and folds it exactly, so a ruled card merge is invisible to it: Ed. Kimberley fell to L2 when T-1001 landed
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-13
pr: 1291
claimed_by: run 9/13/2026, 6:15:22 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-14T00:10:58.654Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34788900596
---

The 1840 head crosswalk gathers its 1835 bearers by surname and folds it exactly, so a ruled card merge is invisible to it: Ed. Kimberley fell to L2 when T-1001 landed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1001, which folded `kimberley_ed` onto `kimberly_edmund_s` and watched the cost.

**What happened.** `tools/crosswalk_census_1840_heads.py` builds `residents_by_surname` off the
live cards and folds the surname exactly — the same fault T-1001 found in the land register's
crosswalk and fixed there with `merged_card_surnames()`. So when the town's only Kimberley card
folded onto Dr Edmund Stoughton Kimberly, the 1840 head `Ed. Kimberley` (33S7-9YYJ-99F, printed
page 234, line 3) stopped reaching anybody and fell from **L7 candidate** to **L2
no_surname_in_the_1835_pools** — whose standing text reads "a surname absent from 1835 is
evidence of that, not a gap in the reading", which is now the wrong reading of this row.

**Why T-1001 did not just fix it, and this is the whole question.** The ladder's L6 promotes a
head to `matched` when the full name agrees, is unique on both sides, the read is `medium` or
better, and an INDEPENDENT discriminator holds — an adjudicated Fergus 1843 or Norris 1844 entry
for that person. The survivor has one: Fergus 1843 prints `Kimberly, Edmund Stoughten, physician,
101 Lake`. So simply gathering the folded surname would not restore the candidate; it would
promote the head to a **matched identity**, on evidence the merge supplied rather than on a
reading of the page. A merge must not promote an identity as a side effect, and T-1001's ruling
says in as many words that nothing was promoted to make it tidy.

**The question to settle, and it is general, not about one head.** When a card-merge ruling joins
two spellings, does the surviving person inherit the folded card's PRINTED NAME for the purposes
of a name-matching crosswalk — and if he does, may the discriminators the merge handed him count
towards L6, or is a head reached through a merge capped at `candidate` until somebody re-reads the
line? Answer it once, in the domain's own README, then apply it. The land crosswalk's answer is
already on the record and is the narrower one: it gathers under the folded surname and weighs the
person by his LIVE card's name, and the match carries `via_card_merge` so a reader can see how it
was reached.

**Acceptance:** the rule is written down in `data/research/census_1840/`'s own documentation
before it is coded; `crosswalk_census_1840_heads.py --check` and `spend_census_1840_heads.py
--check` green; the Kimberley head's outcome is whatever the written rule says it is, with the
reasoning on the row; and `bash tools/check.sh` green.
