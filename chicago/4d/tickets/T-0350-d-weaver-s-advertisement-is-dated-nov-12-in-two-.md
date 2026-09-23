---
id: T-0350
title: D. Weaver's advertisement is dated Nov. 12 in two printings and Nov. 19 in the one the ledger believed
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 541
claimed_by: run 8/29/2026, 9:37:59 AM CT
blocked_on: null
needs_bake: false
---

D. Weaver's advertisement is dated Nov. 12 in two printings and Nov. 19 in the one the ledger believed.

Found while T-0328 settled the LOT number in the same advertisement, and deliberately not
decided there: T-0328's question was the lot, and a second digit resolved in passing on the
same evidence would have been a second verdict nobody had stated the acceptance for.

D. Weaver's standing advertisement for the building on Lot 2, block 1, North Water street
ran five times. Its copy dateline is set differently in four of them:

| issue | claim | dateline as set | reads |
|---|---|---|---|
| 1834-11-26 | c010 | `ine. 12, 1881-50` | Nov. **12** |
| 1834-12-03 | c025 | `Chicago. Nor. 12, 1831. SO WEAVER.` | Nov. **12** |
| 1834-12-10 | c012 | `e, 1631.—00` | no legible day or month |
| 1834-12-17 | c006 | `3, Nor. 13, 131-D WEAVER.` | Nov. **13** |
| 1834-12-24 | c012 | `Chicago, Nor. 19, 1834-SD. WEAVER.` | Nov. **19** |

**Both claims that carry an `ad_copy_date` today record `iso: 1834-11-19`**, and both were
written before the three earlier printings were known. The two earliest and cleanest
settings read 12. The three new claims deliberately carry NO `ad_copy_date` rather than
mint a contradiction, so the ledger is currently silent where it is not sure — which is the
right state to leave it in and the wrong state to leave it in for long, because
`compile_gazetteer.py` feeds `ad_copy_date.iso` into each business's `evidence.copy_dates`
and a wrong date there is a wrong claim about when a house was trading.

It is not obvious which way this goes, and that is why it is a ticket. A dateline of Nov. 12
is a fortnight before the advertisement's first appearance on 1834-11-26; Nov. 19 is a week.
Neither is impossible for a weekly. Against that, `12` is what the two least-damaged settings
print, and the 1834-12-17 setting that reads `13` is the same setting T-0328 overruled on
the lot number — so the printing that is odd here is odd there too.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The copy date is decided across all five printings by the same tally-the-impressions method
  T-0328 used, or it is recorded as undecidable with the reason.
- Whatever is decided, all five claims say the same thing about it, and the ones that carry
  no `ad_copy_date` today either gain one or say in their notes why they do not.
- The verbatim quotes are not edited. Ever.
