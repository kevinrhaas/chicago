---
id: T-0421
title: Canal Street's three control points spread 2.33 m, so its corridor cannot be centred on any of them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-13
pr: 1233
claimed_by: run 9/13/2026, 12:54:37 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T06:33:50.255Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34741297404
---

Canal Street's three control points spread 2.33 m, so its corridor cannot be centred on any of them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by **T-0009** on 2026-08-29 while deriving every street's corridor from its committed
control. Canal is the one street with more than one control point that does not agree with itself:

| control point | offset from canal's drawn centreline |
|---|---|
| `lake_canal` | +0.00 m |
| `randolph_canal` | +0.09 m |
| `kinzie_canal` | **−2.24 m** |

A spread of **2.33 m**, so no rigid translation puts the corridor on all three, and re-DRAWING the
line is what the ruling forbids. `plat_corridors.control_offsets()` therefore returns `disagree`
for canal and leaves its corridor on the drawn line, which is the honest answer and not a repair.

**The disagreement is probably not an error, which is why it is a ticket and not a fix.**
`data/streets/1835.json` says of canal: *"The line uses the road-only Kinzie control already
adopted by the North Branch bridge rather than the queued five-node bikeway-inclusive GCP."* So
the street was drawn on a DIFFERENT reading of the Kinzie junction from the one
`data/traces/street_control.json` commits under `kinzie_canal`, and 2.24 m is the size of that
disagreement rather than a drift. The bridge deck sits on the street's reading.

**Acceptance:** the two readings of the Kinzie junction are named side by side with what each was
derived from; whichever is the control is said so in one place rather than two; if both stand for
stated reasons, the street record and the control file each say that the other exists and why.
Nothing moves without that being written down first — the North Branch bridge stands on this.

**Links:** T-0009 · K30(e) in `docs/ROADMAP.md` · `data/traces/street_control.json` ·
`data/streets/1835.json` · `tools/refetch_control.py`.
