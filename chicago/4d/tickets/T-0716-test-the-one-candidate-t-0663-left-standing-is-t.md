---
id: T-0716
title: Test the one candidate T-0663 left standing: is the Eliza Chappel shore drawing William Mark Young's 'Chicago's First School House' of about 1925
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 1005
claimed_by: run 9/6/2026, 4:03:51 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T21:29:33.258Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34059671448
---

Test the one candidate T-0663 left standing: is the Eliza Chappel shore drawing William Mark Young's 'Chicago's First School House' of about 1925.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The candidate is SETTLED one way or the other. Either Young's plate is the sheet — in
  which case `data/sources/eliza_chappel_school_shore_view.json` gains `author`, `date`,
  `citation` and `repository`, and `rights_status` is re-argued from a 1920s commercial
  print rather than from age — or it is NOT, and this ticket writes that into
  `docs/RESEARCH/chappel_shore_origin_search.md` § 3 and closes the candidate.
- **The test is a picture, not a title.** Compare four things against the deposited
  sheet: the log building at the right, the woman in the doorway, the conical light on a
  low point at the left, the three canoes. A matching TITLE settles nothing — "Chicago's
  first school house" is also used for the 1844 Rumsey school at Madison and Dearborn.
- `verified` moves only if the original is located with its terms stated. Young's name
  may not appear in any citation in this project until the comparison is made.
- If the picture cannot be obtained at all, say so with the routes tried, and do not
  leave the candidate half-alive.

**Where this comes from.** T-0663 ran the external search, did not find the original, and
eliminated Andreas 1884, the Porter memoir 1892, Kirkland 1892 and Quaife 1933 by reading
their lists of illustrations. It left exactly one live lead, resting on two
secondary-market listing titles: **William Mark Young** (1881–1946), *Chicago's First
School House*, ca. 1925, an etching made for the Chicago studio **Koopman, Robinson &
Neumer**, alongside *First Draw Bridge Over Chicago River* and *La Salle Street 1889*.

**What blocked T-0663, so this run does not repeat it.** The listing pages that carry the
picture (eBay `175745610373`, `155150616147`, `155150616225`) return 403 to the runner
directly, under a desktop user-agent, and through the `r.jina.ai` reader; WorthPoint 403s;
HathiTrust full-text search is behind a Cloudflare interstitial; the Google Books API is
out of daily quota on the shared runner IP. The Art Institute's public API holds no Young.
**The productive routes are the catalogues under the NAMES** — *Young, William Mark* and
*Koopman, Robinson & Neumer* — at the Chicago History Museum, the Newberry and the Chicago
Public Library, and **asking the depositor where the scan came from**, which is the
cheapest question on the list and may settle it in a sentence.

**Links:** T-0663 (the search) · T-0649 (the reading that closed the geometric route) ·
T-0617 · `docs/RESEARCH/chappel_shore_origin_search.md` ·
`docs/RESEARCH/chappel_shore_lighthouse.md` ·
`data/sources/eliza_chappel_school_shore_view.json`.
