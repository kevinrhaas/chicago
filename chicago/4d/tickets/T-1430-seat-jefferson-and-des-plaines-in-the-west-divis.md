---
id: T-1430
title: Seat Jefferson and Des Plaines in the West Division: the two streets the ground refused, derived from Clinton's committed line and their own surviving intersection control, now that the box reaches E -705
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1417
opened: 2026-09-20
closed: 2026-09-20
pr: 1557
claimed_by: run 9/20/2026, 2:30:23 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T08:27:58.658Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35496288002
---

Seat Jefferson and Des Plaines in the West Division: the two streets the ground refused, derived from Clinton's committed line and their own surviving intersection control, now that the box reaches E -705.

Piece 1 of 2 of **T-1417 — Put the new ground to use: flora zones, the minimap box and the walker's collision carried to the west wall, the West Division streets taken off their E -320 clip, and generate_west_infill's 35 held slots released**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

- `jefferson` and `des_plaines` are committed to `data/streets/1835.json`, each seated through
  its OWN surviving OpenStreetMap intersection — the ones `fulton`'s note already carries, read
  by T-0446 — with no new source read to place either.
- Each carries `clinton`'s bearing and `clinton`'s reach, because one intersection fixes a point
  and not a direction and a borrowed line may not claim more ground than the line it is borrowed
  from; `geometry_confidence` is `inferred` for that inheritance, and what would raise it to
  `attested` is stated on the record.
- Every line stands on dry modelled land, measured along the committed path rather than assumed,
  and the figure is on the record.
- `tools/measure_west_division_streets.py --self-test` holds every one of those clauses, so a
  re-seated, re-bent, over-stretched or quietly upgraded line fails there rather than going
  quiet; `docs/RESEARCH/west_division_streets.md` §2 keeps the refusal AND carries the seating
  that answers it.
- Nothing else moves: the eighteen West Division numeral crops still cut from `clinton` stepped
  one and two modules west, because they are citations of a reading already taken.

**Stop condition:** the West Division's five platted north-south streets are all committed, and
`measure_west_division_streets.py` says so rather than listing what is absent.
