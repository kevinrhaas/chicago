---
id: T-0345
title: Mason's blacksmith shop is anchored on Graves' Tavern until 16 July 1834 and on the Tremont House from 10 September, and the register holds both as standing placements
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 553
claimed_by: run 8/29/2026, 12:19:29 PM CT
blocked_on: null
needs_bake: false
---

One standing advertisement, one shop, two different landmarks, and the register carries both
as if they were live at once.

From 1833-12-17 to 1834-07-16 the Chicago Democrat sets it "on Main-street, nearly opposite
Graves' Tavern" — 1833-12-24 line 131 carries the sentence unbroken in a single line. From
1834-09-10 the same advertisement, under the same 26 November 1833 copy date and with the
rest of the copy word for word unchanged, reads "on Main-street, oppo[s]ite the Tremont
House" (1834-09-10 lines 2523-2525, 1834-10-15 lines 2101-2103, 1834-11-19 lines 3661-3669,
and the December settings T-0330 resolved). The corpus holds no printing of this
advertisement between 16 July and 10 September 1834, so the change is bracketed by those
two dates and no closer.

Nothing here says WHICH changed. Either the shop moved, or the building opposite it changed
hands and name, or the compositor was handed new copy for a reason nobody printed. The
scene date is 1835-07-01, ten months after the later reading, so the reconstruction should
be standing Mason opposite the Tremont — but the register does not know that: the gazetteer
holds four separate business entries under this one firm (`business_matthias_mason`,
`business_matthias_mason_co`, `business_matthias_mason_co_blacksmiths`,
`business_mathias_mason_co`), two anchored on Graves' Tavern and two on the Tremont House,
none of them `contradicted_by` any other. A placement sweep reading that register would
find the shop in two places.

Related: T-0304 (no firm-merge rule, which is why there are four entries) and T-0324
(Graves' Tavern is itself unplaced). This ticket is the DATED anchor change; neither of
those two carries it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The register states, in one place, that this firm's printed anchor changes between
  1834-07-16 and 1834-09-10, and which anchor is the one live at the scene date.
- The superseded anchor is not silently dropped: it stays readable with its own dates, so a
  later pass can tell a moved shop from a renamed landmark.
- Nothing decides between "the shop moved" and "the landmark was renamed" on no evidence. If
  the corpus cannot say, the ticket says it cannot.
