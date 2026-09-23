---
id: T-0844
title: Six duplicate-card clusters the evidence does not decide: Hunt, Kennicott, Saunders, Walker, T. Temple and John S. Kinzie
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-10
pr: 1059
claimed_by: run 9/10/2026, 2:40:33 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T08:53:09.390Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34450270341
---

Six duplicate-card clusters the evidence does not decide: Hunt, Kennicott, Saunders, Walker, T. Temple and John S. Kinzie.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Raised by T-0839**, which folded 42 duplicate town cards onto the people they name and
ruled every candidate cluster in writing. Six pairs it declined to rule, because the
evidence genuinely does not decide and a merge is not reversible by the next reader's
opinion. Each is written onto both cards as a `merge_ruling` block with
`verdict: undecided` and `referred_to: owner`, and the reasoning is in
`data/residents/card_merge_rulings.json`. Ruling one is a sentence; ruling all six is one
run, and the merges then land through `tools/consolidate_town_cards.py --apply`.

| cluster | the two cards | for the merge | against it |
|---|---|---|---|
| `hunt-c` | `hunt_c_s` (C S Hunt) · `hunt_charles_cotesworth_pinckney` | both printed in Chicago papers seventeen days apart in August 1835; the only Hunt forename beginning C | middle initial S against C, and neither card documents the man beyond a list and a death notice |
| `kennicott` | `kennicott_w_l` · `kennicott_william_h` | uncommon surname, no third bearer in the town | middle initials L and H disagree; no anchor on either side |
| `saunders` | `saunders_william_s` · `saunders_william_w` | both in the Democrat; Saunders is not common here | middle initials S and W disagree; one is letter-list only, the other a press mention |
| `walker-george` | `walker_george_e` · `walker_george_h` | both Georges in the Democrat; no third Walker | middle initials E and H disagree; no anchor |
| `temple` | `temple_t` (T Temple) · `temple_john_t` | 'T. Temple' in the Democrat of 3 Dec 1834 is most probably Dr John Taylor Temple with the first initial dropped | T matches neither Temple forename — the town's two are John and Peter — and no rule in this project attaches a card whose only forename token is a MIDDLE initial |
| `kinzie-john` | `kinzie_john_s` · `kinzie_john_h` | John Harris Kinzie is the town's only John Kinzie in 1835 | middle initial S against H, on the one surname T-0839 warns about: four Kinzie men stand on the cards and this project has mis-folded a Kinzie once already (T-0732) |

Rule C4 in the rulings file — *a contradicted middle initial, over an anchor* — would fire
on Temple and Kinzie and is withheld on both for a stated reason. Hunt, Kennicott, Saunders
and Walker fail C4 outright: there is no anchor, so nothing says which printing is the
mis-set one.

**Done when** each of the six carries a MERGE or a DISTINCT ruling in
`data/residents/card_merge_rulings.json`, the merges are landed, and the gate
`tools/consolidate_town_cards.py --check` is green with no card left undecided-to-owner.

## Folded in from T-0854 (2026-09-10) — the Kinzie digit is the premise inside T-0844's John S. Kinzie row and must be ruled before or with it

*T-0854: The card John S. Kinzie is named from a digit: the Democrat prints 'JOHN 8. KINZIE' beside John Harris Kinzie's own trade, and the owner's R3 referral was argued on an initial the source never printed*

The card John S. Kinzie is named from a digit: the Democrat prints 'JOHN 8. KINZIE' beside John Harris Kinzie's own trade, and the owner's R3 referral was argued on an initial the source never printed.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**The reading.** `data/research/newspapers/extracted/chicago_democrat_1833_12_10.json` claim
`c012` transcribes an advertisement as:

> TO LOAN, / JOHN 8. KINZIE, / [F]orwarding & Commission [MERCHANT] / CHICAGO—ILLINOIS.

The `as_printed` string the extraction records is **`JOHN 8. KINZIE`**. `John S. Kinzie` is the
extractor's NORMALISATION of that digit, and `hh_kinzie_john_s.json` is a civic mint off the
normalisation. The trade printed beside the name is *forwarding and commission merchant* — which
is John Harris Kinzie's own trade on his own card, from his own 1834 advertisement.

**Why it matters.** `data/residents/card_merge_rulings.json`, cluster `kinzie-john`, refers
`kinzie_john_s` against `kinzie_john_h` to the owner under R3, and its stated ground against the
merge is *"the middle initial S contradicts H"*. If the 8 is an OCR artefact standing where a
letter was, there is no S to contradict anything, and the referral was argued on a premise the
source does not supply. That does not decide the merge — it changes what the owner is being
asked.

**Same fault, fourth instance.** T-0721 is open on `8. G. Abbot`, `A. 8. Perry` and
`James I1. Gabbs`: a digit standing inside a printed name. This is the same defect on the surname
this project has already named as its trap, and it reached a card rather than being refused.

**Acceptance:**
- Say whether `JOHN 8. KINZIE` is a digit-for-letter artefact, on the transcription and on the
  trade beside it, and record the finding either way.
- If it is, the card's name stops asserting a middle initial the source never printed, and the
  R3 referral in `card_merge_rulings.json` is re-stated on the corrected premise. **The merge
  itself stays the owner's call** and is not made here.
- Nothing is merged on the strength of a shared surname; `data/research/books/crosswalk.json`'s
  rule governs.
- `tools/check.sh` green.

**Found by** T-0732, which read the Democrat of 10 December 1833 to corroborate the R. A. Kinzie
merge and found this two claims away. The reasoning is in
`data/research/residents/kinzie_kinship_ruling.json` § `related_finding`.

**Not a duplicate of T-0844**, which asks the owner to decide six duplicate-card clusters including
John S. Kinzie. This ticket is about the NAME the card carries: whether the source printed an S at
all. It is the premise T-0844's Kinzie cluster is argued on, and it can be settled from the
transcription without deciding the merge.

**Links:** T-0732 · T-0721 · T-0839 · T-0844 · `data/residents/card_merge_rulings.json` cluster
`kinzie-john` · `data/residents/households/hh_kinzie_john_s.json`
