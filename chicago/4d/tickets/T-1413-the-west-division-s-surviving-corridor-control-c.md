---
id: T-1413
title: The West Division's surviving corridor control committed: Fulton x Canal adopted where it moves nothing, and Fulton x Clinton plus the two western junctions held with the seven roofs and the ground that hold them
state: done
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1192
opened: 2026-09-19
closed: 2026-09-19
pr: 1543
claimed_by: run 9/19/2026, 7:04:59 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T00:55:16.598Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35476562284
---

The West Division's surviving corridor control committed: Fulton x Canal adopted where it moves nothing, and Fulton x Clinton plus the two western junctions held with the seven roofs and the ground that hold them.

Piece 1 of 2 of **T-1192 — Seat the West Division's and Wabansia's streets and alleys as platted corridors off Wright and Hathaway — Canal, Clinton, West Water, Carroll, Fulton, the School Section tier and the Wabansia grid north-west of the forks — with the small lots the sheets draw**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The West Division's four drawn streets that this table did not name — `west_water`,
   `clinton`, `carroll`, `fulton` — resolve in `street_control.json.streets`, each with its
   axis, its modern equivalence and the reason it has or has not got control. Two of them
   carry a recorded NEGATIVE rather than a gap: West Water's 2026-09-05 Overpass query
   returned no through street on that bank, and Carroll's 2026-09-04 query for the name
   returned nothing usable under `node_rule`.
2. `fulton`'s four surviving intersections stop being prose. They were read from
   OpenStreetMap on 2026-09-04 by T-0446 and have lived since in one sentence of one
   street record, which is the arrangement `street_control.json` exists to end.
3. **Each of the four is adopted or held ON ITS MEASURED CONSEQUENCE, not on its
   evidence** — the evidence is identical for all four. `control.fulton_canal` is adopted
   because Canal already disagreed with itself, so a fourth point changes a number and
   moves nothing: `disagree` before and after, the corridor on the drawn line, and
   `measure_corridor_intrusion.py --gate` reading the same 19 lapping phases and the same
   0 generated roofs in a corridor. The other three are HELD, in a new `held_control`
   block that states what adopting each would do:
   - `fulton_clinton` would re-centre Clinton's corridor 4.19 m east and put **seven
     generated roofs** into a platted corridor, which that gate refuses by construction.
     All seven are named with their laps. They are generated placements, not readings, so
     the release is placement work and nothing attested is in tension.
   - `jefferson_fulton` and `des_plaines_fulton` control streets the modelled ground
     refuses; the distances are derived in `measure_west_division_streets.py` and
     `docs/RESEARCH/west_division_streets.md` § 2 rather than restated.
4. `tools/measure_canal_control_spread.py` carries the fourth point in both readings and
   gates all four offsets. **Its committed constants are re-stated with the measurement,
   not relaxed to pass**, and the finding they now record is a correction: T-0421 settled
   Canal's 2.33 m as "this control entry's cycle path", and the Fulton junction is 4.61 m,
   is the largest of the four, and SURVIVES the road-only correction — so the road-only
   spread goes 0.09 m to 4.61 m and Canal's disagreement is no longer something the queued
   `kinzie_canal` correction could resolve.
5. Gates: `check.sh` green; `measure_canal_control_spread.py --check` and `--self-test`
   green; `measure_corridor_intrusion.py --gate` and `measure_corridor_strip.py --gate`
   unchanged. `needs_bake: false` — no geometry moves.

**Stop condition:** the West Division's surviving control is committed and auditable, and
every junction it holds back says in a number what adopting it would cost.

**Links:** T-1192 (parent) · T-1414 (the seating, blocked on T-1193) · T-0446 · T-0421 ·
T-0009 · `docs/RESEARCH/west_division_streets.md`.
