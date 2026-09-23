---
id: T-0136
title: The eight owner-brief plates T-0075 could not identify: Andreas at page-image level, and two museum objects
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-09-13
pr: 1250
claimed_by: run 9/13/2026, 7:33:25 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T13:05:07.594Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34757111135
---

The eight owner-brief plates T-0075 could not identify: Andreas at page-image level, and two museum objects.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Opened by T-0075's run (PR #304), which identified four of the twelve images in the
owner's brief of 2026-08-18 and left eight. The README's identification table is the
brief; this ticket is the chase. In priority of what the dataset leans on:

- **Images 6 and 9, the two Braunhold engravings** (Green Tree 1838, Sauganash). Both
  are stated to be Andreas 1884 plates. Neither is reproduced on any chicagology page
  this project holds a record for. **Go to Andreas volume I at page-image level** — the
  same fetch `docs/LIBERTIES.md` names as the resolution for several open liberties. A
  plate cited to a page of the volume settles the rights question at the same time.
- **Image 8, the Petford watercolour.** A Chicago History Museum object. Needs its
  accession number, which is a catalogue lookup rather than a web search;
  `chm_green_tree_1859` (ICHi-040230) is the shape of the record it should become.
- **Image 11, the CHS postcard of "South Water Street in 1834".** Carries a © line in
  the brief's own description, so `check_required` at best and possibly `restricted`.
  Read the rights line off the object before writing a record.
- **Images 1, 2, 4 and 12** (the jail engraving, the closer Dearborn drawbridge view,
  the Wolf Tavern, and the coloured view of Chicago c. 1833). Chicagology's own search
  was run for each subject and returned topic pages carrying none of them — the Cook
  County Jail page reproduces no engraving at all.

**Acceptance:** each of the eight either resolves to a source record with tier and
rights status, or its README row states a NEW search that was run and failed — repeating
the four routes above is not progress. Any attribute whose citation moves from a path to
a source_id and is read by a generator goes through the rights-derivation gate, and the
route taken is named in the commit, as T-0075's was. Gates green.
