---
id: T-0407
title: The same blacksmith notice is read as 'Matthias Nason & Co.' in one impression, and the partner-surname guard can never merge it
state: done
epic: PAPERS
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-12
pr: 1171
claimed_by: run 9/11/2026, 11:12:19 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T05:07:45.429Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34672201367
---

Matthias Mason & Co.'s blacksmithing notice runs eleven times in the *Chicago Democrat*
under one copy date of 26 November 1833. T-0345 joined four of the five styles the reading
passes minted for it into one house, `business_matthias_mason_co`. The fifth cannot be
joined and this ticket is why.

The impression of 1834-02-18 (c010) sets the heading so badly that the reading pass
recorded the firm as **`Matthias Nason & Co.`** — the transcription's own quote is
`MATTHIAS MASON & CO.` misread from `MATTHIAS [N]ASON & CO.`, on lines interleaved with a
neighbouring column, and its own claim note says so: *"The firm's name is printed 'NASON'
here and 'MASON' at 1834-02-25; neither is preferred and both stand in their own quotes."*
Every other field is the house's: trade blacksmiths, goods horse shoes and chains, anchor
Graves' Tavern, and the sentence resumes `[at Gra]ves' Tavern, where they in[tend to]`.

`firm_merges` cannot take it. The guard is deliberate and has no escape: *"the two styles
must carry the same set of PARTNER SURNAMES, with or without a rule, because a partnership
IS its partners and a changed one is a different house."* `Nason` is not `Mason`, so the
rule refuses — correctly, on the policy as written. The result is that one printing of a
notice this project has otherwise fully reconciled stands as a separate business in the
gazetteer and a separate row in the register, and T-0345's anchor history does not carry
it.

The question is whether the surname guard needs a stated exception for a surname the
transcription itself brackets as unread, or whether a claim-level correction is the right
place — the reading pass could record `Matthias Mason & Co.` as the `normalized` name with
`Nason` standing in the quote, which is what this corpus does everywhere else with a
letter it cannot read. The second is probably right and does not touch the policy.

**Acceptance:**

- One of the two routes is taken, with the reasoning written down, and the 1834-02-18
  printing joins the other ten in `business_matthias_mason_co`.
- The partner-surname guard is not weakened by resemblance. If an exception is made it
  names the exact condition (a surname the transcription brackets as unread) and a case
  asserts that an ordinary surname difference is still refused.
- T-0345's `anchor_changes` declaration for this house still accounts for every reading,
  which it will have to be re-checked against: the 1834-02-18 anchor is `Graves' Tavern`
  and falls inside the earlier window.
