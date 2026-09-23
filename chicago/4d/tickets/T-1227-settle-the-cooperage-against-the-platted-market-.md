---
id: T-1227
title: Settle the cooperage against the platted Market Street corridor in the recipe that places it, so no hand-typed coordinate stands in for the ruling
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1108
opened: 2026-09-17
closed: 2026-09-17
pr: 1385
claimed_by: run 9/17/2026, 4:19:35 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T10:00:49.217Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35203627603
---

Settle the cooperage against the platted Market Street corridor in the recipe that places it, so no hand-typed coordinate stands in for the ruling.

Piece 1 of 2 of **T-1108 — Three generators refuse together and none is gated: inf_cooperage_south_branch stands 2.1 m inside the platted Market Street corridor**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What was wrong.** The refusal was real and the ruling behind it was already right. T-0827
re-fitted Market Street on 2026-09-12 off the plat's own 400 ft module, instead of off the
modern junction on N Wacker Drive it had been hung from — Wacker stands on ground made in
1926 when the river was walled — and the platted corridor came 3.0 m west onto this
building. A band assignment has no evidence in it, so it has nothing to encroach with: the
roadway moved and the building follows. T-0827 settled exactly that.

What it then did was write the answer into `data/structures/inf_cooperage_south_branch.json`
BY HAND, as a coordinate and a paragraph, and leave `center_local_enu_m` in
`data/reconstruction/1835_inferred_household_programme.json` at E 72 N -235. That file is
the recipe and `tools/generate_inferred_households.py` owns the record. So the two
disagreed from that day, and the generator went on re-deriving the building into the road.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The corridor refusal is gone because the RECIPE moved the building, not because a record
  was edited: no hand-typed coordinate is left standing in for the ruling, and re-fitting
  Market Street again moves this building again instead of leaving it to disagree in silence.
- The margin is T-0827's own 0.5 m, and the distance is measured against
  `tools/plat_corridors.py` — the same geometry the gate refuses on.
- Nothing is upgraded. The position stays `reconstructed`, the derivation block stays
  `not_derivable`, and the record says on itself what moved it and why.
- What this piece does NOT claim: that the three `--check` modes can be gated. They cannot —
  see T-1228, which is what the parent's second half turned out to be.

