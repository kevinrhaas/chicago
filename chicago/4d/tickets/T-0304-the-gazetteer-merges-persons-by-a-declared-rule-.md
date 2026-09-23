---
id: T-0304
title: The gazetteer merges persons by a declared rule and has no equivalent for firms, so 'L. Wilson & Co.' and 'Jno. Wilson & Co.' are two businesses
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-28
pr: 503
claimed_by: run 8/28/2026, 10:16:57 PM CT
blocked_on: null
needs_bake: false
---

The gazetteer merges persons by a declared rule and has no equivalent for firms, so 'L. Wilson & Co.' and 'Jno. Wilson & Co.' are two businesses.

`compile_gazetteer.py` keys a business on its whole normalized name and `identity.json` speaks
only of persons, so five printings of one Dearborn-street house — 'J. L. Wilson & Co.',
'Jno. L. Wilson & Co.', 'Jno. S. Wilson & Co', 'Jno. Wilson & Co.' and 'L. Wilson & Co.' —
compile to five businesses, three of which are last seen in 1834 and therefore each carry a
survival liberty that the other two disprove.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `identity.json` carries `firm_merges` and the compiler applies it, refusing — as compile
  errors, exactly as the person merges are refused — a merge with no `merge_rule`, a rule that
  does not name both spellings verbatim, a firm no claim carries, and a firm merged into itself.
- The FIRM guard is stated and is not the person one. Same-surname-different-initials cannot be
  it: a `& Co.` style elides and misprints the forename it trades under, which is the whole of
  why this ticket exists. What the two styles must share is the set of PARTNER SURNAMES, with
  or without a rule; and they may not stand in streets the papers contradict.
- Merging widens and never narrows: mentions, proprietors, goods and copy dates union, the
  issue window widens, the more specific placement wins, and every trade either side printed
  is kept in `trade_variants`.
- Ruling 3 is recomputed after the merges, so `survival_liberty_required` answers for the
  whole house rather than for one printing of it.
- The Wilson house compiles as one business, each of its four merges carrying a rule that cites
  the printings it rests on.
- `--self-test` fires on every new refusal, and asserts the union itself — green is also what a
  merge that quietly did nothing would look like.
- `check.sh` green and the mirror published.

**Done, 2026-08-29.** 201 businesses → 197. The Wilson house is documented 1834-09-17 to
1835-07-18 with the relative placement (Dearborn street, next door to the city boot, shoe and
leather store) it could only reach through the merge, and needs no survival liberty. The
self-test went 35 → 42 cases. The remaining 31 candidate groups are T-0337.
