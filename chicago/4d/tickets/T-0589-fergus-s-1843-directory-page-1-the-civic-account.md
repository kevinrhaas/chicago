---
id: T-0589
title: Fergus's 1843 directory, page 1: the civic account — officers, courts, churches, societies, newspapers, fire and military companies, schools, the 1843 ward population count and the port's exports and imports for 1842-3
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 813
claimed_by: run 9/4/2026, 4:37:51 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T22:04:03.468Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33918604701
---

Fergus's 1843 directory, page 1: the civic account — officers, courts, churches, societies,
newspapers, fire and military companies, schools, the 1843 ward population count and the
port's exports and imports for 1842-3.

**Where it is.** `data/research/directories/text/fergus_1843_page_001.txt`, lines 37-750,
committed by T-0571 and byte-identical to the Genealogy Trails cache at
`data/research/genealogytrails/text/1843directory_1.txt`. Nothing needs fetching.

**Why T-0571 left it.** T-0571 read the DIRECTORY on that page — the 174 classified business
cards of lines 752-1204 — and the 2,521 alphabetical entries on pages 2-4. The civic account
above it is a different shape with a different kind vocabulary: `civic` for an office, a poll
or an ordinance, `price` and `shipping` for the port tables, `person` for a minister, and it
is finding-shaped rather than list-shaped. Reading it entry by entry alongside the directory
would have been two demonstrations in one run. `coverage.json` names it as not read and names
this ticket.

**What is in it, and it is worth having.** The mayor, the common council by ward and the
corporation's officers; the county, state and United-States officers and the courts; twenty-odd
churches and societies with their ministers, their streets and their memberships — the First
Presbyterian on Clark between Washington and Madison with 500 in the congregation, the Catholic
church at the north-west corner of Michigan and Madison with 2,000; the newspapers and their
publication days; the post-office and its hours; three military companies and five fire
companies with their officers; Rush Medical College's trustees and faculty; the common schools
and the Female Seminary; the population by ward, counted male and female; and the port of
Chicago's exports and imports with the articles exported in 1842 and in 1843 and the vessels
arrived and cleared.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Lines 37-750 read into `data/research/directories/`, in T-0492's shape, under the closed
  kind vocabulary, with the quote verbatim and the reading beside it.
- `describes_date: "1843"` on everything, and `town_finding` set honestly: an 1843 congregation
  count is a finding about 1843 and never an 1835 one.
- `coverage.json`'s `not_read_and_why` entry for these lines replaced by a declaration that
  names them read, with a count the reader's `--check` holds.
- No resident record changes state.

**Links:** T-0571 (the directory half, done — the file shapes and the reader to follow) ·
T-0556 (the parent sweep) · T-0492 (the shape) · T-0513 waits on the sweep.
