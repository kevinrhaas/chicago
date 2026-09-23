---
id: T-0567
title: Norris's 1844 directory: the Description and Historical Sketch and the Statistical Account read as dated town findings
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0555
opened: 2026-09-03
closed: 2026-09-03
pr: 710
claimed_by: run 9/3/2026, 12:39:13 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T17:39:13.123Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33783212867
---

Norris's 1844 directory: the Description and Historical Sketch and the Statistical Account read as dated town findings.

Piece 2 of 4 of **T-0555 — Norris's General Directory and Business Advertiser of Chicago for 1844 (HathiTrust chi.56111136): parse residents, businesses and occupations, date-flag them as later evidence, and use them to validate and enrich the 1835 residences and businesses**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every leaf of the **Description and Historical Sketch** (scan leaves 15-30 = printed pages 5-20) and of the
  **Statistical Account** (leaves 76-88 = printed 66-78) read out, and every one of those 29 leaves DECLARED in
  `data/research/directories/coverage.json` and REACHED by at least one claim — no declared page a claim never
  touches, which is what that file calls a hole.
- A claims file `data/research/directories/claims/norris_1844_town_findings.json` under the T-0492 shape, in which
  every claim carries `town_finding: true`, a **verbatim** quote that `tools/research_domains.py --check` rebuilds
  character-for-character out of the committed page text, a `normalized` reading, a `locator` naming the text file,
  the lines and the printed page, and `entities`.
- `describes_date` is the year the STATEMENT describes, not the year the book was printed. A sentence about 1832 is
  filed as 1832; a sentence about the town as it stood when Norris wrote is filed as 1843 or 1844. The scene-year
  statements — Norris on 1835 — are separable from the rest by that field alone.
- **Nothing here is written into a resident, household, business or structure record.** This ticket reads a source;
  T-0569 is the ticket that spends it on the layers, and under the ratified ladder an 1844 book never on its own
  makes an 1835 fact.
- The counts in the PR, and the README saying what the sketch does and does not settle for 1 July 1835.
