---
id: T-1024
title: Two faults in the volume 2 folio derivation leave twelve claims with no printed page: the verso-head regex matches 'history of Chicago' in running prose, and the recto folios the volume prints are never read at all
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: 1110
claimed_by: run 9/11/2026, 1:17:52 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T06:46:14.916Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34562840711
---

Two faults in the volume 2 folio derivation leave twelve claims with no printed page: the verso-head regex matches 'history of Chicago' in running prose, and the recto folios the volume prints are never read at all.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found while re-reading volume 2 for T-0826, on a branch that lost the ticket to PR #1106 by
twenty-six minutes.** The reading that landed is good; its folio derivation has two faults and
`tools/derive_book_folios.py --audit` reports the second one as a property of the book.

**Fault 1 — the verso head matches running prose.** `VERSO_HEAD` is searched with `re.search`
against every line, so any line CONTAINING the phrase is a head. Line 9941 is
`To  return  to  the  history  of  Chicago `, a sentence. The detector took it for a verso head,
looked six lines back for a numeral, and found `79` at line 9937 — which is the numeral of the
RECTO head at 9934 (`EDUCATIONAL.`). It then reported that numeral as "79, which is odd on a verso
and refused by the parity check", and carried the page. The head count is inflated the same way:
319 loose matches against 295 whole-line ones.

**Fault 2 — the recto folios are never read.** The docstring states the rule correctly — the
number stands alone above `HISTORY OF CHICAGO.` on a verso and after the chapter title on a recto
— but `verso_heads()` only finds the verso side, and `at()` uses a recto numeral only as a
tie-breaker when the verso folio is already known. The volume prints **336 recto folios**, 320 of
them odd, and not one is used as a head in its own right. So where a verso numeral did not survive
— 48 of the 319 — the page is carried and reported as unreadable, when a recto head two lines away
carries it.

**The cost, on committed data:** twelve of T-0826's twenty claims carry `"page": null`.
`bk_mose2_004`, the first term of court in the Mansion House loft, is the clearest: its locator
says the two heads between read folios 150 and 156 "lost their numerals to the OCR", and the recto
head at lines 18524-18527 prints `THE BENCH AND BAR.` and then `153`. The page is on the leaf.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)
- The verso head is matched on the WHOLE line, and the audit's head count is the whole-line count.
- Recto heads are first-class: title line, numeral within six lines AFTER it, folio odd, and the
  same step rule the verso side is held to. Both sides are interleaved into one sequence in
  document order and `--at` reads a page off the nearest preceding head of either side.
- Every one of the twenty claims is re-derived and each locator rewritten to what the fixed
  derivation says. A claim whose page is still not readable KEEPS `null` and says why — the point
  is that the carried ones are carried honestly, not that the nulls all disappear.
- NO CLAIM'S `quote`, `normalized`, `entities` OR LINE RANGE CHANGES. This moves folios and the
  prose that justifies them, nothing else, and the research spend does not move at all.
- The source record and the corpus `page_index.why` stop asserting the counts the faulty audit
  produced.
