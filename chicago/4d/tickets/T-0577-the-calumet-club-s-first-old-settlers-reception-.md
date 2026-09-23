---
id: T-0577
title: The Calumet Club's FIRST old-settlers reception, 27 May 1879: the registry of 149 settlers and their years of arrival, off the page images of Early Chicago (archive.org earlychicagorece00calu)
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 795
claimed_by: run 9/4/2026, 11:59:20 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T17:45:13.621Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33897563641
---

The Calumet Club's FIRST old-settlers reception, 27 May 1879: the registry of 149 settlers and their years of arrival, off the page images of Early Chicago (archive.org earlychicagorece00calu).

**Why this is the richest unread roster in the series.** T-0554 read the FOURTH reception
(18 May 1882) and laid the series out in `data/research/old_settlers/receptions.json`. The
1882 roster gives each guest's 1882 post-office address and **no year of arrival** — so of
128 named men, not one is dated. The first reception's printed proceedings do the opposite:
*Early Chicago: Reception to the Settlers of Chicago Prior to 1840, by the Calumet Club, of
Chicago, Tuesday Evening, May 27, 1879* records that "of the settlers of Chicago prior to
1840, one hundred and forty-nine registered their names", and prints tables of "the places
of birth, the years of arrival, and ages of those who signed the registry". A year of
arrival on a named man is exactly what this programme's grading ladder can spend.

**The catch, measured 2026-09-03.** The Internet Archive OCR
(`earlychicagorece00calu_djvu.txt`) is sound in the prose and **mangled in the tables** —
the years-of-arrival column survives as bare figures with their labels detached, e.g.
`5° 5i 52 53 … I l8l7, 16 T8 7 18^4`. The registry itself must therefore be read off the
PAGE IMAGES, not the text layer. Three copies are on archive.org
(`earlychicagorece00calu`, `cu31924028806707`, `earlychicagorecep00calu`) and a bad scan of
one page may be good in another. The source record
`data/sources/calumet_club_early_chicago_1879.json` already exists and records this.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Every name on the 1879 registry read into `data/research/old_settlers/people.json` under
  the existing shape and the existing builder (`tools/old_settlers.py`), with its year of
  arrival, place of birth and age where the tables give them, `as_read` verbatim, and the
  locator naming the printed page.
- `receptions.json` row `calumet_1879_first` flips `roster_read` to true, with the count it
  actually read stated beside the proceedings' own 149.
- The identity rules already in the builder (OS1/OS2A merge, OS2 probable, OS3/OS4/OS5
  refuse) applied unchanged; merges written onto the resident records by
  `--apply-citations`, probables left for T-0513.
- **A year of arrival is still not an 1835 residence** — it is a dated recollection of
  1879 and grades as the ladder says for that class. Nothing here mints or regrades a
  resident; T-0514/T-0515 do that.
- `tools/old_settlers.py --check` and `--self-test` green, and the aggregate tables'
  arithmetic (63 New York, 16 Connecticut, …) reconciled against the names read, with any
  gap stated.

**Effort.** M if the registry is a clean list on one or two plates; if the years of arrival
have to be read man by man off a mangled table, `split` it by page rather than shipping
half.

**Note on the queue.** Filed at the QUEUE bottom because agents only append — but this is
the continuation of the owner's own 2026-09-03 old-settlers ask, and T-0554 sits in the
resident-source band at the top. It is his call whether it belongs up there with its
parent.

**Links:** T-0554 (the parent read, and the series layout) · `data/research/old_settlers/`
· T-0499/T-0500 (the Fergus volumes, which reprinted the reception proceedings) · T-0513
(consolidation) · T-0514/T-0515 (the residents write).
