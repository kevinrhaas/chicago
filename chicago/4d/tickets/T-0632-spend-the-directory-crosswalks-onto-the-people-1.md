---
id: T-0632
title: Spend the directory crosswalks onto the people: 130 adjudicated matches carry a later trade or address, and 111 of 849 persons have an occupation
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 781
claimed_by: run 9/4/2026, 7:43:28 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T12:47:44.253Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33867114819
---

Spend the directory crosswalks onto the people: 130 adjudicated matches carry a later
trade or address, and 111 of 849 persons have an occupation.

**Filed on the owner's instruction of 2026-09-04**: *"do some periodic consolidations
along the way to turn the research created into actual data household et al not just
research ... there are business references that have addresses later and while we don't
have that in 1835, you might use a documented address from later to position the business
where you have limited other information or it could contribute"*.

## The gap, counted on dev at 2e1a972d

The town holds **825 households and 849 persons**. Of them:

| field | has a real value | share |
|---|---|---|
| `occupation` (person) | 111 | 13.1 % |
| `works_at` (household) | 50 | 6.1 % |
| `lives_at` (household) | 20 | 2.4 % |

788 of 849 persons rest on exactly ONE source; 3 rest on none. 731 are graded `inferred`,
118 `attested`.

Meanwhile the directory crosswalks are already adjudicated and already say what they can
carry — the counts are in the files, not estimated here:

| crosswalk | matched | could carry an occupation | could carry an address |
|---|---|---|---|
| `fergus_1843_crosswalk_1835.json` | 68 | 0 | **46** |
| `norris_1844_crosswalk_1835.json` | 48 | **21** | **39** |
| `norris_1844_advertiser_crosswalk_1835.json` | 14 | 14 (trade printed on every card) | **14** |
| `fergus_1839_crosswalk_1835.json` | 84 residents (plus 123 voters, 334 letter-list names) | — | — |

Every one of those match rows already carries `person_id`, `household_id`, the rule that
made the match, and the entry **as printed**. And every one of them carries
`occupation_1835: "none_recorded"` and `lives_at_1835: null` on the resident side. The
adjudication happened; nothing crossed into the town.

`tools/measure_research_spend.py` says the same thing from the other end: **6,684
directory claims read, 288 spent**, and **zero id pairs** for the domain.

## What this ticket does NOT do

It does not decide that a man who kept a store in 1844 kept it in 1835. That is exactly
the error the ratified ladder exists to prevent, and the crosswalks already refuse it —
`what_it_evidences` on each match says what the entry is worth. This ticket writes the
later reading onto the card **as later evidence, labelled as such**, so that:

- the card stops saying `none_recorded` when a source has been read that records it;
- the person's `sources` list gains the second source it has been entitled to since the
  crosswalk closed;
- and T-0633 has something to position a business from.

The 1835 `grade` moves only where the ladder's own clause admits it. A trade printed in
1844 against a man attested in 1835 is `inferred` for 1835 and says so in its note.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. A tool — not a hand edit — reads the four directory crosswalks and writes onto each
   matched person/household: the later `occupation`, the later address, and the source id,
   each as a graded `{value, confidence, note}` whose note names the directory, the year
   and the printed string it came from. It runs again idempotently.
2. `measure_research_spend.py` shows the `directories` spend rising by at least the
   number of matches written, and the second hop (ruled → on a card) rising with it.
   Quote the before and after table in the PR.
3. No 1835 grade is raised on a later-directory reading alone. State the count of grades
   changed and the clause each rests on; if the answer is zero, say zero.
4. Every write is reversible from the crosswalk: nothing is written that the crosswalk
   does not already hold.
5. The three counts at the top of this ticket are re-run and restated after the pass.
