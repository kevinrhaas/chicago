---
id: T-0411
title: A newspaper and its own printing office are two businesses, and the partner-surname guard can never join them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-11
pr: 1159
claimed_by: run 9/11/2026, 7:10:35 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T00:45:31.450Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34660588722
---

**Found by T-0402**, which was asked to judge 'the Chicago Democrat against the Chicago
Democrat printing office' and found it cannot be judged with the machinery that exists.

The register carries the paper and the shop that prints it as two businesses:

    The Chicago Democrat             the paper, over John Calhoun's name, its imprint
                                     placing it in the building at the corner of South
                                     Water and Clark streets — 1833-11-26 c033,
                                     1834-08-27 c009, 1834-09-17 c010, 1834-12-03 c023
    Chicago Democrat printing office the shop, read out of the paper's own colophon —
                                     1834-01-07 c006 at the same South Water and Clark
                                     corner, and 1835-05-20 c007 over Jones & King's
                                     hardware store in the same street

T-0399 merged each of those into ITSELF — the article, the possessive, the extractor's
'(office)' disambiguator — and left them two, because they cannot be merged into each
other. `firm_surnames()` reads the last word of the style as the partner surname, so it
compares {democrat} against {office}, and the partner-surname guard has NO ESCAPE by
design: 'a partnership IS its partners and a changed one is a different house.' The guard
is right about partnerships and blind here, because neither style names a partner at all.

**And a refusal is not the answer either.** `refused_firm_merges` offers three kinds —
`two_houses`, `not_joined`, `different_ground` — and none of them is true. These are not
two houses; a printing DOES join them (the colophon is the paper naming its own shop); and
in 1834 they are on the same corner, so the ground is not different. Writing any of the
three down would be a false judgement filed to make a group look closed. T-0402 declined
to file one, which is why this ticket exists.

The same shape as T-0410's agency, and the reason both are filed rather than forced: the
gazetteer has exactly one relation between two businesses — 'they are the same business' —
and the corpus keeps producing pairs that are neither the same nor unrelated.

**Note what is already downstream of this.** T-0403 records that the printing office keeps
its 1834 corner through T-0399's internal merge, because `placement_rank` prefers a corner
to a relative offset regardless of date — so the office stands at the wrong end of South
Water Street on the scene date. If the paper and the office are ever joined, that placement
question is joined with them and the two tickets have to be answered together.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The gazetteer can express that one business is another's premises or department — a
  paper and its printing office, and whatever else the corpus turns out to hold in that
  shape — without merging them and without weakening the partner-surname guard.
- The Democrat pair is expressed in it, citing the imprint and colophon printings above.
- Whether the joined pair stands as one roof or two in the model is DECIDED and written
  down; it is a visible consequence and must not be left to fall out of the data.
- T-0403 is answered or is explicitly still open, with the reason.
- `check.sh` green, and the PR states the business count before and after.

Links: T-0402 (which found this and declined to file a false refusal), T-0399 (the two
self-merges), T-0403 (the corner the office keeps), T-0410 (the same shape, for an agency),
T-0304 (the firm-merge machinery).
