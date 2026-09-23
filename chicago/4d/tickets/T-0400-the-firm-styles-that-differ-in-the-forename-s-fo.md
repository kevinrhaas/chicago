---
id: T-0400
title: The firm styles that differ in the forename's form: whole against abbreviated against initial
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0338
opened: 2026-08-29
closed: 2026-08-29
pr: 559
claimed_by: run 8/29/2026, 2:27:06 PM CT
blocked_on: null
needs_bake: false
---

Piece 2 of 4 of **T-0338 — Thirty-one groups of firms share a partner surname and only one
of them has been judged**. The parent keeps the full ask; this ticket owns one slice of it.

The groups where the two styles carry the SAME partner surnames and differ in the form of a
forename — whole against abbreviated against bare initial. T-0304 already ruled that a
forename initial is not decisive for a firm the way it is for a person, so these are
judgeable; what they need is the printing that ties the two forms to one house.

The candidates, after T-0399 collapses the restyles:

    Collins & Caton against J. H. Collins & J. D. Caton
    Matthias Mason & Co. against Mathias Mason & Co. (one t) and bare Matthias Mason
    G. Spring against Giles Spring · J. S. C. Hogan against John S. C. Hogan
    J. Bates, Jr. against John Bates, Jr. · J. Wellmaker & Co. against John Wellmaker & Co.
    J. Wright, merchant against John Wright · D. Elston & Co. against Daniel Elston & [Co.]
    J. D. Caton, attorney… against John Dean Caton · Doty & Co. against H. Doty & Co.
    P. Pruyne against P. Pruyne & Co.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- Every group above is declared in `firm_merges` with a rule citing the printings, or
  written into `refused_firm_merges` with the reason it is two houses.
- No group is merged on the forename alone: the rule cites an issue, a copy date, a street
  or an anchor that ties the two forms together.
- The gazetteer recompiles green and the PR states the business count before and after.

Links: T-0338 (the parent), T-0399 (which ran first), T-0304.

---

**WHAT WAS DONE.** All ten workable groups judged: **8 merged, 2 refused**. The register goes
**217 businesses → 209**, and `survival_liberty_required` **109 → 103** (L211 restated).

The eleventh candidate on the list above — Matthias Mason & Co. against Mathias Mason & Co.
and bare Matthias Mason — was already closed by T-0399 and T-0345 and no `mason` group
survives. What is left of that name is `Matthias Mason & Co.` against `Matthias Nason & Co.`,
which the partner-surname guard hard-refuses because the surnames themselves differ by an
OCR reading; that is T-0407 and it is not this ticket's.

    MERGED (8)
      Collins & Caton  ← J. H. Collins & J. D. Caton   one card, copy-dated Jan. 20 1834,
        both printings next door east of Brewster, Hogan & Co. in South Water street
      G. Spring  ← Giles Spring   one card, copy-dated Dec. 3 1834, and BOTH records print
        the removal to first door north of the Tremont House
      J. S. C. Hogan  ← John S. C. Hogan   the Brewster, Hogan & Co. dissolution continues
        the business "at the old stand, by Jno. S. C. Hogan … a general assortment", and
        three weeks later J. S. C. HOGAN advertises that assortment in South Water street
      John Bates, Jr.  ← J. Bates, Jr.   the same advertisement, the same sixteen steel-
        pointed crowbars, the kegs down from twelve to seven, BOTH signed with the initial
      J. Wellmaker & Co.  ← John Wellmaker & Co.   the dissolution notice filed under the
        short style sets the firm's name as "John Wellmaker [& Co.]" in its own text
      Daniel Elston & [Co.]  ← D. Elston & Co.   printed in one issue, 1834-02-18 c002 and
        c009, one copy date, and two ends of one tallow-and-hogs stream
      H. Doty & Co.  ← Doty & Co.   one copy date, April 29 1834, and both take the store
        at the east end of South Water street lately occupied by Peter Cohen
      P. Pruyne & Co.  ← P. Pruyne   the timber notice of Ap'l. 22 signed "[P.] PRUYNE &
        CO." in one printing and "P PRUYNE" in the next, plural subscriber over a singular
        signature both times

    REFUSED (2)
      J. D. Caton, attorney and counsellor at law · different_ground — South Water Street in
        December 1833, Dearborn Street in July 1835, the Collins & Caton partnership in
        between, and no removal notice in the corpus
      John Wright · not_joined — a Democrat dry-goods house of 1833-34 against an American
        seller of leather, salt and oak scantling in July 1835; nothing printed joins them

Two directions were chosen against the "truer spelling" default and the rules say why.
`Daniel Elston & [Co.]` survives with its editorial brackets — the ink blot over the word
after the ampersand at 1833-11-26 c030 — because neither style can be placed and that record
holds six printings against two and both trades. `J. Wellmaker & Co.` survives although the
notice spells the firm out, for the same reason: it holds both March notices and both
partners, John Wellmaker and William Adams.

**T-0410** was filed on something this ticket found and could not fix inside the merge
machinery: `chicago_democrat_1834_05_21#c001` is a house Pruyne OFFERS FOR SALE, and the
extractor minted a `corner` business placement from it, so `P. Pruyne & Co.` now carries the
Lasalle-and-Lake corner among its store's placement readings. It is not the live placement,
and the reason it is not is luck — the source record's live placement was `none` — so the
merge rule states the caution verbatim and the ticket carries the machinery question.
