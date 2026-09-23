---
id: T-1141
title: The 1 April 1834 return is unread except for three lines, and the reading of those three found a name the extraction drops entirely
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-15
pr: 1365
claimed_by: run 9/15/2026, 2:30:03 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T20:34:51.683Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35013649321
---

The 1 April 1834 return is unread except for three lines, and the reading of those three
found a name the extraction drops entirely.

**Filed by T-1138**, which read three consecutive lines of the S run at three impressions of
the page and could not avoid seeing what stood around them. It read three lines out of about
a hundred and seventy. The rest of the return has never been compared with the page.

## What the three-line read saw on its way past

All of it on the 8 April 1834 impression, which is the clean one, and each confirmed on at
least one other. None of it is acted on anywhere: `letter_list_1834_04_01_contested_lines.json`
carries it under `seen_in_passing` as OBSERVATIONS, deliberately.

- **`Mason B. Smith` is a whole line the extraction has no entity for.** It stands between
  `Robt. Stephens 2` and `Mr. Smith`, and the 16 April transcription's own raw text carries
  it. A person the town does not hold.
- **`Robt. Strong` is carried in prose and in no record.** The 1 April claim's raw text has
  `[uncertain: Robt. Strong Detroit, ?]` and the entity list goes straight from
  `Douglass Sloan` to `Samuel Shaw`.
- **Three minted names are set otherwise on the page**: `Peter Schander` is `Peter Schauder`,
  `[uncertain: Stephen M. Satsby]` is `Stephen M. Salsby`, and `Orin N. Stevens` is
  `Orin R. Stevens`.

Five findings in the twenty-odd lines one pass happened to look at, in a return the corpus
reads through TWO extractions of THREE impressions. Whatever the rate is over the other
hundred and fifty lines, it is not zero.

## Acceptance

1. The return of 1 April 1834 is concorded line by line against its page images, in T-1010's
   shape for the 1 January 1834 return: every printed line set down in printed order, tied to
   the entity that carries it or recorded as carried by none.
2. The printed length is COUNTED off the page rather than inferred from the extraction, as
   T-0424 counted January's at 170.
3. Every line the concordance finds that the extraction drops is either minted or refused by
   a named rule, and the five findings above are among them rather than beside them.
4. Every reading the image overturns is moved in the same PR, and the card it moves is
   withdrawn rather than renamed in place — the rule T-1138 applied to its three.
5. `./tools/check.sh` green, with the concordance gated the way T-1010's is.

**Links:** T-1138 (the three lines, and the roster this starts from) · T-1010 (the shape) ·
T-0424 (the January read this is the April twin of) · T-0321 (the note that first recorded
the disagreement) · `data/research/newspapers/letter_list_1834_04_01_contested_lines.json`


## What was done, against each acceptance clause (2026-09-15)

1. **DONE.** `data/research/newspapers/letter_list_1834_04_01_printed.json` — all 193
   printed lines of the return, in printed order, read at the 8 April impression (leaf
   0006, page 3, printed column 3), in T-0424's shape. The 8 April setting was chosen
   because T-1138 had already established that the 1 April one has the next column's
   auction advertisement bleeding through its S run and the 16 April one is a narrower
   reset that loses the tail of most surnames.
   `letter_list_1834_04_01_concordance.json` is the ledger: one row per printed line, tied
   to the entity that carries it or recorded as carried by none, derived by
   `tools/concord_letter_list_1834_04_01.py` and gated by its `--check`.
2. **DONE, and the page agrees with itself.** 193 lines — 97 in the left sub-column and 96
   in the right, not the 82 + 81 the 1 April transcription reads — carrying 218 letters
   once the trailing count digits are added. The office set its own total at the foot of
   the column: `21[8]`, its last digit inked thin against the column rule. The tally is
   the measurement and the printed figure agrees with it.
3. **DONE for 28 of the 30 dropped lines; the rule is named for all 30.** The 1 April
   transcription drops THIRTY printed lines. Twenty-eight are carried by another
   impression's claim and enter the mint's pool through it — the ledger names which claim
   and what each reaches. Two are carried by no claim of any impression and the rule that
   leaves them outside the pool is stated on their rows: the pool is built of ENTITIES and
   these two lines are not one. They are `P. Cook` (line 48) and `Jeter Foster` (line 68),
   and putting them INSIDE the rules needs T-1011's lift, which is on T-1153 — see below.
   The five findings T-1138 recorded in passing are rows of the ledger rather than notes
   beside it: `Mason B. Smith` (151) and `Robt. Strong` (158) are both tied to the 16
   April claim that carries them, and `Orin R. Stevens` (164), `Peter Schauder` (165) and
   `Stephen M. Salsby` (166) stand under `name_differs` with the other 25.
4. **CARRIED TO T-1153, and not silently.** 28 lines disagree between the page and an
   extraction. Moving them is T-1139's kind of work rather than T-1010's — the card takes
   the image's reading or keeps its own and the ruling names the source that outranks the
   image there — and at least one of the 28 plainly needs the second answer: line 64 sets
   `Pierce Dowaer` where the town holds `hh_downer_pierce` on evidence outside this return.
   Both that adjudication and the lift in clause 3 end in ONE run of
   `tools/mint_letter_list_residents.py`, and that writer rewrites **744 files with 25,932
   deletions on the committed tree with no edit at all** — measured this run, filed onto
   **T-1137**, which owns the question under FILING RULE (a). Neither tail can be shipped
   honestly until that is fixed, so both are on T-1153, parked under FILING RULE (d).
5. **DONE.** `./tools/check.sh` green, with the concordance gated the way T-1010's is —
   `--check` and `--self-test`, wired beside the January pair.
