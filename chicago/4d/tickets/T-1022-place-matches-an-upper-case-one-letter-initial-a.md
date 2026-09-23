---
id: T-1022
title: PLACE matches an upper-case one-letter initial as the 'h' of 'house', so 'at H. Norton & Co.' reads as an address in 294 entries
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-13
pr: 1272
claimed_by: run 9/13/2026, 3:03:53 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T20:29:19.179Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34779431849
---

PLACE matches an upper-case one-letter initial as the 'h' of 'house', so 'at H. Norton & Co.' reads as an address in 294 entries.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1018, which exposed it on one entry and did not widen its scope to fix it.

`PLACE` in `tools/read_norris_1844.py` is the regex that splits a trade from a street:

    PLACE = re.compile(r"\b(?:h|house|res|residence|r|boards|bds|b)\.?\s", re.I)

`re.I` makes the one-letter forms `h`, `r` and `b` case-blind, and Norris sets them
LOWER CASE for house/residence/between while a forename initial is upper case. So
`H.` in `at H. Norton & Co.'s` reads as "house", and the address begins at the
employer's initial:

    n1844_e1936  AVorcester, D. L. at H. Norton & Co.'s, h Wabash st
                 occupation 'at'  ·  address "H. Norton & Co.'s, h Wabash st"

**MEASURED ON DEV:** 294 entries carry at least one upper-case one-letter PLACE
match. Most are not the FIRST match and so do not move the split — the count that
matters is how many entries' occupation/address actually change, and that is what
this ticket must measure before it changes anything.

Requiring lower case for the one-letter forms only (`house`, `res`, `residence`,
`boards`, `bds` keep `re.I`) is the obvious shape, but it is a change to all 2,073
readings and every crosswalk below them, which is why T-1018 refused to make it in
passing.

**Acceptance:**

- Every entry whose `occupation` or `address` moves is enumerated before and after,
  and each is a repair or is named as a loss.
- `crosswalk_norris_1844.py` counts before and after; `could_carry_address` is the
  number to watch, and any match LOST is named.
- n1844_e1936 reads occupation `at H. Norton & Co.'s`, address `h Wabash st`.
- A self-test case holds the lower-case rule against a re-read.
- `bash tools/check.sh` green, derived layer re-run in the same commit. No bake.
