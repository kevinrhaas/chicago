---
id: T-1444
title: Release generate_west_infill's 35 held slots onto the extended ground: the terrain gate retired, the placements instantiated and baked
state: claimed
epic: GROUND
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1431
opened: 2026-09-20
closed: null
pr: null
claimed_by: run 9/20/2026, 2:15:04 PM CT
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35531496699
---

Release generate_west_infill's 35 held slots onto the extended ground: the terrain gate retired, the placements instantiated and baked.

Piece 2 of 2 of **T-1431 — Carry the West Division's five tier lines off their E -320 clip and release generate_west_infill's 35 held slots on the extended ground**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance.** The recipe's terrain instantiation block is retired against the committed
terrain spec (asked every run, not asserted), and 30 of the 35 held slots instantiate on
their own recipe ids, families and dealt sequence numbers. The 20 built under the hold are
byte-identical. Five slots stay held on a different question — see below — recorded in the
recipe under `terrain_and_hydrology_gate.boundary_hold` and read from there by both the
generator and `tools/reconcile_665.py`, so one hold cannot become two counts.

**The corporate boundary reading.** `tools/measure_corporation_limits.py` resolves the
1833 boundary's west leg on Jefferson Street and must carry it 1 188.8 m past the end of
its committed centreline to reach Ohio; that extension is uncertain by 22 m. Five released
slots stand 6.9–22.6 m from it, so the EXTRAPOLATION rather than the ordinance would decide
whether each roof stood inside the town limits. The gate names two remedies and refuses a
third — trace the street, or leave the side unstated, do not widen the tolerance. The side
is left unstated by not building the roof. **T-1490** owns tracing Jefferson.

**The swale reading** the recipe deferred was taken and filed as **T-1460**.

**The build.py trap, found and undone.** The earlier branch carried a convenience change to
`generators/build.py` (`--only` taking a comma-separated list). `mesh_inputs._code_shas`
hashes `build.py` into every structure's input hash, so that one edit staled 382 of 419
committed meshes — `tools/validate.py --all` is clean on `dev` and reported all 382 here.
`build.py` is restored to its committed bytes and every West mesh re-baked against it. A
multi-id `--only` is a real convenience and belongs in its own ticket with the town-wide
re-bake it costs, not folded into a release.

**WIP — PR #1576, on `hold`, 2026-09-20 (second run).** `dev` is merged in (seven conflicts
resolved; the derived ones by regeneration), `node tools/rederive.mjs --run` is green across
all 154 steps, the changelog is stamped and passes, and `tools/check.sh` is down from 20
failing steps to **one**:

* `no reconstructed value is newly outside the band its own note cites` — two NEW offenders,
  both from this release, and `tools/band_claims_baseline.json` is a ratchet that may only
  record a repair, so neither may simply be banked:
  * `recon_1835_west_033` footprint 32.00x20.00 ft against the D5 band 18x28–24x34. This is
    `FACING_CORRECTIONS`: the branch swapped width and depth so the long side is the facade,
    because 32/20 is past the 1.5 ratio at which `frame_dwelling_params` refuses an
    eaves-front house. The rectangle is right and the band is stated width-by-depth, so the
    swap reads as out of band. Either the band citation follows the rotation or the slot
    takes a footprint inside the band — the owner's call is which.
  * `recon_1835_west_036` `loft = true` where its family band authors no loft. That looks
    like a straight deal fault in the release, not a judgement call.

Everything else in the gate is green, including the boundary gate, staleness (0), the
Newberry index, the population profile, the order book, the lodging model, the hay limits
and the closing set. The `--for-diff` smoke legs have NOT been run.
