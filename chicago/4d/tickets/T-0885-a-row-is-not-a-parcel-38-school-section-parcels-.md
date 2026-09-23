---
id: T-0885
title: A row is not a parcel: 38 school-section parcels are entered twice, 26 of them every parcel Ebenezer Hale buys and John Hale buys too
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-06
pr: 981
claimed_by: run 9/6/2026, 6:51:47 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T12:12:15.959Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34029206125
---

A row is not a parcel: 38 school-section parcels are entered twice, 26 of them every parcel Ebenezer Hale buys and John Hale buys too.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY THIS RUN, and worked immediately rather than from the top of the queue because it
is a correction to a table merged forty minutes earlier by PR #979 (T-0798) and the
evidence was already in hand. The queue's own rule asks for that reason to be stated in
the PR, and it is.

Of the 335 live School Section rows, **297 are distinct block-and-lot parcels**. 38 parcels
carry more than one row. All 38 agree on the day and on the page of volume 818; 37 agree on
the price; each row has its own purchase number. Six of the 38 carry the register's `AS`
suffix on one row, which reads as an assignment — the one shape of duplicate the source
explains itself.

**Twenty-six of the 38 are one pair of names:** every parcel Ebenezer Hale enters, John
Hale enters as well. That is why the keenest-purchaser table reads two Hales at its head.
The 38th disagreement is block 72 lot 2, entered at **$8.00** and **$80.00** on the same
day and page — a slip of the pen or of the transcription, and this project does not know
which.

**Acceptance:** the difference between rows and parcels is DERIVED and printed wherever the
sale is counted, so a row count can never be read as a parcel count by accident; no name is
merged and no row dropped to get there; and the Hale pair is left as an open question with
its evidence written down, because ruling on it is an identity ruling and
`resident_crosswalk.json` is where this domain makes those.
