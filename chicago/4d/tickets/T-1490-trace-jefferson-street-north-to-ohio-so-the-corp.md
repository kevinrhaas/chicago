---
id: T-1490
title: Trace Jefferson Street north to Ohio so the corporate boundary's west leg stops being a 1,188 m extrapolation, and seat the five West Division roofs held on it
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Trace Jefferson Street north to Ohio so the corporate boundary's west leg stops being a 1,188 m extrapolation, and seat the five West Division roofs held on it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on 2026-09-20 while T-1444 released the West Division parcel's held slots.

`tools/measure_corporation_limits.py` resolves the corporate boundary of 7 November 1833
on committed geometry. Its west leg is Jefferson Street, whose committed centreline ends
far south of the West Division approaches, so the tool carries it **1 188.8 m** past that
end to reach Ohio Street. A leg extended that far is uncertain by 20 m plus the surveys'
own bearing spread — **22.0 m of drift** at the point in question.

Five of the parcel's released slots stand inside that band:

| slot | clearance from the leg | drift at that point |
|---|---|---|
| west_rec_035 |  6.9 m | 22.0 m |
| west_rec_037 |  7.4 m | 22.4 m |
| west_rec_027 | 12.9 m | 23.8 m |
| west_rec_029 | 19.2 m | 23.2 m |
| west_rec_032 | 22.6 m | 22.7 m |

The next roof out, recon_1835_west_033, clears at 24.8 m against 22.7 m and is decided.

The gate names the two remedies and refuses a third: *trace the street, or leave the
structure's side unstated — do not widen the tolerance.* T-1444 took the second, in the
only way a reconstruction can: `BOUNDARY_HOLDS` in `tools/generate_west_infill.py` keeps
those five slots unbuilt, with their ids, families and dealt sequence numbers intact.
Moving them was refused for the same reason the west-prairie swales did not move seven
reviewed roofs (T-1460): a conjectural building shifted 15 m to make a model assert a
side it does not know is a worse record, not a better one.

**What closes this:** Jefferson Street traced north to Ohio from a committed source, at
which point the leg is no longer an extrapolation, the drift falls to the trace tolerance
and the five slots instantiate unchanged — delete `BOUNDARY_HOLDS`, regenerate, bake.
