---
id: T-0339
title: Twenty dozen cast steel axes are recorded as the booksellers' stock and Jones & King signed the advertisement
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 505
claimed_by: run 8/28/2026, 11:13:27 PM CT
blocked_on: null
needs_bake: false
---

`business_russell_clift` carries `axes` as a good, and the bookshop never sold any.

The claim is `chicago_democrat_1834_12_03#c004`, the bookseller's standing advertisement
(T-0327). Its cited range runs to line 3310, and lines 3308-3310 are a DIFFERENT
advertisement:

    G5 20%, of Silsry's gat steal “AXES, by
    lozen or singly. Bi ‘i
    [uncertain: Nor. 5 183k ee ? hee:]

In this printing the signature is crushed to `lozen or singly. Bi ‘i`, so nothing separates
the two blocks and the reading pass took them for one. **Two other printings of the same
standing pair separate them with a rule and sign the axes:**

- 1834-11-12 page 3 column 2, lines 2555-2557 — `Gg DOZ. of Silaby'e cast stool AXES, by /
  the dozen or singly. Jones § King. / Now. 5, 1834,`
- 1834-12-24 page 3 column 5, lines 3559-3561 — `the dozen or singly. donee & King.`

Jones & King are the South Water Street hardware house already in the gazetteer, and 1834-12-03
already carries one of their claims (`c007`, window glass, sash and blinds). The dateline
`Nov. 5, 1834` belongs to the axes advertisement too, not to the booksellers'.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `c004`'s cited range and quote end at line 3307, and `axes` leaves `business_russell_clift`.
- Lines 3308-3310 are extracted as their own claim keyed to `business_jones_king`, with the
  attribution marked INFERRED from the neighbouring printings, since this printing's signature
  cannot be read.
- `tools/compile_gazetteer.py --check` is green: every quote still reassembles verbatim.
