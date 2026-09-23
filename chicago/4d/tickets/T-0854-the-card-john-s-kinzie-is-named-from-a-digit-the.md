---
id: T-0854
title: The card John S. Kinzie is named from a digit: the Democrat prints 'JOHN 8. KINZIE' beside John Harris Kinzie's own trade, and the owner's R3 referral was argued on an initial the source never printed
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0844: the Kinzie digit is the premise inside T-0844's John S. Kinzie row and must be ruled before or with it
needs_bake: false
closed_at: 2026-09-10T04:20:05.919Z
claimed_run: null
---

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
