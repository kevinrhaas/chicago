---
id: T-0336
title: The 31 July 1835 letter list, standing in all four August Democrats
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0297
opened: 2026-08-28
closed: 2026-08-29
pr: 532
claimed_by: run 8/29/2026, 7:12:54 AM CT
blocked_on: null
needs_bake: false
---

ONE list, four printings. Letters remaining in the Post Office at Chicago, Cook County,
Illinois, on the **31st day of July 1835**, over **JOHN S. C. HOGAN, P. M.**, set once and
printed unchanged in `chicago_democrat_1835_08_05` (page 3, columns 2-3),
`_08_12` (page 4, columns 2-3), `_08_19` (page 3, column 6 into page 4) and `_08_26`
(page 4, columns 2-3). Roughly six hundred names. Piece 2 of 2 of **T-0297**.

This is the census proxy ruling 1 turns on: a listed name mints a resident candidate, and
the flag `letter_list_only` is what keeps the weaker evidence distinguishable forever.

## What the run that takes this has to get right

- **Mint the names ONCE.** [[T-0299]] measured what happens when a standing list is minted
  from every printing: 298 names became 638 persons off three printings of the 1834 list,
  because the identity policy — correctly — keys on the whole normalized name and the
  segmenter cut each printing differently. Read the list from the printing whose type is
  most legible, say in the claim's note which printing that is and why, and claim the other
  three printings as printings: heading, signature, and no entities.
- **Two witnesses, and say so.** The four printings are four OCR readings of one standing
  forme, so a name unreadable in one is often clean in another. Using a second printing to
  resolve a letter is legitimate and must be stated; it is NOT licence to smooth a `quote`,
  which stays verbatim and is machine-checked line by line.
- **`[…]` is absence, `[word]` is a supply**, and a name read with a query keeps the query.
- Nothing here may be merged in `identity.json` without a `merge_rule` naming both
  spellings; same surname with different initials never merges.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The list is extracted in full at name level from one named printing, and the PR states a
  sampled hand count against the column.
- Every minted person carries `letter_list_only: true` unless another claim in the corpus
  names them; the compiler sets that field and nothing hand-writes it.
- The other three printings carry a claim naming the list and minting no names.
- The gate is green and every quote is reassembled from the transcription.
