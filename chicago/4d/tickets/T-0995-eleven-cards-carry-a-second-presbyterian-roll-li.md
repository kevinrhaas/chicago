---
id: T-0995
title: Eleven cards carry a Second Presbyterian roll line that is matched to two or three townspeople each, and not one of them says so
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-13
pr: 1281
claimed_by: run 9/13/2026, 5:02:42 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T22:34:01.338Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34785405985
---

Eleven cards carry a Second Presbyterian roll line that is matched to two or three townspeople each, and not one of them says so.

**Acceptance:** every card whose Second Presbyterian roll line is matched to another townsperson
names those others in the paragraph on the card, and `spend_second_presbyterian_roll.py --check`
refuses a card that omits them. `effort: S` — one measured pass over an existing tool, no new
reading and no bake.

**What is on the cards, and what is not.** T-0992 (PR #1063) spent the crosswalk's 83 `matched`
rulings onto the 83 cards they name, and it did that well: every paragraph quotes the crosswalk's
own limit unparaphrased, states the Mrs rule where the line is a married woman's entry, and moves
no grade. What no paragraph states is that **a roll line can be met by more than one townsperson.**

`matched` means this RESIDENT met exactly one line — a resident meeting several is `ambiguous`. It
does NOT mean the line met exactly one resident, and five of the 83 lines are matched to two or
three cards apiece:

| roll line | as read | cards it reaches |
|---|---|---|
| `second_presb_0519` | "Cook, Mrs. J. L. \| Dismissed." | `cook_j_b`, `cook_john`, `cook_josiah_p` |
| `second_presb_0301` | — | two cards |
| `second_presb_0309` | — | two cards |
| `second_presb_0323` | — | two cards |
| `second_presb_0870` | "Taylor, Mrs. Charle's …" | two cards |

Eleven cards in total. Each of the three Cooks now carries a paragraph reading “carries 1 line
whose surname and given initial agree with this person's”, which is true of each of them and reads
as though the line were about the one card the reader is looking at. It singles nobody out, and a
card that does not say so is the failure T-0700 named: a paragraph that is not false and is not the
whole ruling either.

**The fix is small and local.** The generator already has every row in hand: group the matched rows
by `roll_lines[].record`, and where a record carries more than one person, name the others in that
card's paragraph — "the same roll line is matched under the same rule to X and Y, so it is met by
three townspeople of this name and says which of them it was about no more than it says it was
about this one." Then gate it: `--check` asks whether the paragraph is RIGHT and not merely
present, so the assertion belongs beside the ones already there, and `--self-test` should hold that
a shared line names its rivals and an unshared one does not.

**Found by** the duplicate run of T-0992 on 2026-09-10 (slice 1 of 2 fell to T-0992 after its own
row was held, and PR #1063 landed from the other slice while it worked). Its independent
implementation wrote this clause and its gate; the ledger there carried a
`shares_its_line_with` column. Nothing of that is in the tree — only this reading of the gap.

**Links:** T-0992 / `tools/spend_second_presbyterian_roll.py` (the pass to amend) · T-0700 (a
paragraph present and no longer the whole truth) · T-0846 (the sibling fault: one paragraph written
twice) · `data/research/church/second_presbyterian_crosswalk.json` § `matched`.
