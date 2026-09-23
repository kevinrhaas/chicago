---
id: T-0663
title: Find the original of the Eliza Chappel shore drawing: a hand, a date and a publication, since its lighthouse cannot settle its subject
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 826
claimed_by: run 9/4/2026, 8:15:28 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T01:35:29.573Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33935461254
---

Find the original of the Eliza Chappel shore drawing: a hand, a date and a publication.

**Where this comes from.** T-0649 read the drawing's lighthouse and established that it
CANNOT settle what the picture depicts — `docs/RESEARCH/chappel_shore_lighthouse.md` and
`tools/measure_chappel_shore_lighthouse.py` are the reading. The sheet is composed rather
than constructed (three adults on one bank fall 1.523x short of the falloff a single
station demands), the tower's foot is not drawn, and Fort Dearborn is not beside the
light where the committed coordinates put it. So the internal evidence is spent. The one
route left is external: the image is plainly a published retrospective illustration, and
a published illustration has a hand, a date and a book.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Either the original is FOUND — artist or engraver, title, date, and the publication or
  holding institution — and `data/sources/eliza_chappel_school_shore_view.json` gains
  `citation`, `date`, `repository` and a real `rights_status`; or the search is
  DOCUMENTED as exhausted, naming what was searched and with what terms, so the next run
  does not repeat it.
- If a date and a hand are established, `describes_date` may finally be argued, and
  whether the picture is a fifth view of the Sauganash's log annex becomes answerable on
  the artist's own authority rather than on the sheet's geometry. That is a SUCCESSOR,
  not this ticket.
- `verified` moves only if the original is located with its terms stated. Nothing about
  an attributed plate (Braunhold, Petford, Trowbridge) moves on this image's authority,
  found or not.

**Links:** T-0649 (the reading that closed the geometric route) · T-0617 · T-0616 ·
T-0092 (how a single weak view is graded) ·
`docs/RESEARCH/chappel_shore_lighthouse.md` ·
`data/sources/eliza_chappel_school_shore_view.json`.
