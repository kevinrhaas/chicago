---
id: T-0768
title: West Water Street north of Lake: the 1839 directory attests the reach, and a bank offset there runs through the Wolf Point cluster
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: 1203
claimed_by: run 9/12/2026, 12:04:03 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T17:54:10.728Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34706910288
---

T-0445 seated `west_water` from the scene's south edge (local north -404) to local north **-104**,
where the committed 1834 west bank turns west into the junction pool at Wolf Point. It stopped
there deliberately: north of the turn a bank-offset line runs straight through the attested Wolf
Point cluster — `wolf_point_tavern` at (-77.3, -45.1), `robert_kinzie_store` at (-68.7, -62.8),
`james_kinzie_house` at (-46.7, -79.8), `walker_meeting_house` at (-105.0, -3.0). Those are
documented placements and the street is a reconstruction, so the reconstruction gave way.

**But the reach is attested.** Fergus 1839 prints Murphy & Titus's *"Rat's-castle Hotel, W. Water
st north of West Lake st"*, and Lake Street stands at local north -110. So the street ran north of
where this reconstruction stops it, and the town is short that frontage.

**The ask.** Find the line the street actually took past the turn — between the documented cluster
and the water, or west of the cluster — and either seat the continuation or record in writing why
no line fits between the two. A refusal that names the clearance it could not find is an answer;
silence is not.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- The clearance between the Wolf Point cluster's committed footprints and the traced bank is
  MEASURED and stated, structure by structure, before any line is proposed.
- Either `west_water`'s path is extended with the reasoning and its grade, or the refusal is
  written into `docs/RESEARCH/west_division_streets.md` § 1 with that measurement.
- `python3 tools/measure_west_division_streets.py --self-test` and
  `python3 tools/measure_corridor_intrusion.py --gate` both green; no documented structure newly
  stands in a platted street.

**Links:** T-0445 (which seated the southern reach) · `data/research/directories/fergus_1839_street_faces.json`
firm 40 · `docs/RESEARCH/west_division_streets.md` § 1.
