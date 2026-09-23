---
id: T-1291
title: Rule the remaining one-letter and disputed-name identity pairs in ONE pass and accept the residue as ambiguous
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: 1423
claimed_by: run 9/17/2026, 6:00:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T23:43:28.473Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35284430297
---

**Owner, 2026-09-17**, on the same ruling as T-1290: the research spend is a CHECK before
reconstruction, not a programme.

This folds **five** open tickets into one: T-1027 (the 68 one-letter card pairs, an EPIC),
T-1140 (C12's roll exhaustion and five one-letter SURNAME pairs), T-1153 (the 28 readings of
the 1 April 1834 return where page and extraction disagree), T-0835 and T-0958 (the Newberry
parser moving under `leads.json`, and the bleed-in test withholding 15 cards under one run and
43 under another).

**Why they are one job.** Every one asks the same question — *are these two readings the same
person?* — and every one is answered the same way: read the page, rule, and record the rule.
Splitting that into an epic plus four satellites turns one pass over a few hundred pairs into
five runs that each re-establish the same context.

**Each folded ticket's evidence is kept**, its file marked `withdrawn` and naming this one, so
the clusters already worked out are not re-derived.

**Acceptance — one run, and an explicit residue:**

1. Rule every pair in one pass, in the clusters those tickets already organise them into.
2. A pair that cannot be ruled on the evidence is recorded as **ambiguous, with both readings
   kept**, and that is a finished answer — not a deferral and not a new ticket. The project
   already prefers a refusal to an invention; an ambiguous pair is a refusal.
3. State how many pairs were merged, how many kept apart, how many left ambiguous, and what
   the ambiguous ones do to the town's count. A range is an acceptable answer.
4. **No new ticket per unresolved pair.**

**Stop condition:** identity is closed for the purposes of the 1835 reconstruction, with a
stated ambiguous residue. The 68 pairs are worth one run, not six.

---

## RULED, 2026-09-17 — 43 pairs, 0 merges, 1 ambiguous, the town's count unchanged

The closing report is `docs/RESEARCH/one_letter_card_pairs_ruled.md`. In short:

- `tools/measure_card_fuzzy_candidates.py` proposes **54** pairs beyond the exact test.
  **11** already carried a ruling naming both their cards; the other **43** are ruled in
  `data/residents/card_merge_rulings.json` under ticket `T-1291` and written onto every
  card by `consolidate_town_cards.py --apply`.
- **0 merged. 42 kept apart. 1 ambiguous** (`mcgregor_ashor` / `mgregor_a`, U2). By rule:
  D7 13 · D9 7 · R2 6 · D6 5 · R5 4 · D8 3 · D10 3 · R3 1 · U2 1.
- **The town's card count does not move**: 1,282 cards on 1,258 households before and
  after. The ambiguous pair's effect on the count is a range of one.
- **No new ticket per unresolved pair** (acceptance 4). The two pairs a page would most
  cheaply settle are named in their own rulings and in the report — `lloyd-loyd`, where
  the town is carrying its own fourth mayor twice, and `smow-snow`, whose image T-0695
  already owns.

**What the pass leaves behind.** `tools/rule_fuzzy_card_pairs.py` gathers the four facts
every landed one-letter ruling rests on, and `--check` is gated in `check.sh`. It is
stricter than the pool it replaces: T-1027 counted a pair as ruled when EITHER card stood
in some ruled cluster and said so in its own table; measured at PAIR level the pool was 43
open, not 32.

**Four rules added, none of them a merge rule.** D8 (D7's mirror on the forename), D9 (a
shared source id is not a shared printing — `chicago_voter_lists_1833_1835_irad` bundles
four closed rolls and `chicago_newspapers_1833_1835` three years of two papers), D10 (the
names disagree beyond the one letter) and U2 (ambiguous is a finished answer). D9 is the
one the pool actually needed: seven pairs fell through the gap between C9's missing
demonstration and D7's "the two bodies of evidence do not touch", which is literally false
for them.

**Stop condition met**, with the residue stated: identity is closed for the purposes of the
1835 reconstruction. The four garbled cards stay with T-0695, where they already were.
