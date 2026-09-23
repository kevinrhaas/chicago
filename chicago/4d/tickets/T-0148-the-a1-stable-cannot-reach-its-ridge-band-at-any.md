---
id: T-0148
title: The A1 stable cannot reach its ridge band at any pitch its family allows
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-22
closed: 2026-08-24
pr: 355
claimed_by: run 8/24/2026, 3:11:57 AM CT
blocked_on: null
needs_bake: false
---

The A1 stable cannot reach its ridge band at any pitch its family allows.

Found by T-0145's new instrument, `tools/measure_ridge_band.py`. It models every reconstructed
roof's ridge from the archetype's own roof arithmetic and reads back the ridge the committed GLB
carries; the two agree on all 257 records, and **104 of those roofs stand outside the `ridge_ft`
band their family authors** — banked in `tools/ridge_band_baseline.json`.

Most of that is not a sampling error and cannot be repaired by moving a pitch. Three committed
claims disagree, and the disagreement is structural:

- the crosswalk's **footprint band** (how wide and deep the family is),
- the crosswalk's **pitch band** (`roof`, e.g. A1's `7:12-10:12`),
- the crosswalk's **ridge band** (`ridge_ft`, e.g. A1's `17-24`),

plus a fourth thing the crosswalk does not author at all: **which way the archetype points the
ridge.** `outbuilding` runs a gable down the LONG axis, so the roof climbs half the SHORT one, and
an A1 stable drawn inside its own footprint band tops out around 15-17 ft at the steepest pitch A1
allows. Thirteen A1 roofs are banked low for exactly that reason; the D3/D4/D5/D6 groups are banked
HIGH for the mirror of it.

**This is an owner-facing question, not an agent repair.** Satisfying the ridge band means giving up
one of the other three — widening the pitch band, widening the footprint band, or turning the
archetype's ridge — and each is a change to the specification or to a shared generator, not to a
parcel. T-0145 deliberately declined to leave the pitch band to reach the ridge band, on the ground
that satisfying a gate by disobeying the other committed claim is not a repair.

**Acceptance:** for each family group in `tools/ridge_band_baseline.json`, a stated decision about
which of the four claims gives way, carried out and the baseline shrunk accordingly — or, where the
answer is that the specification's ridge column simply does not describe how this project's
archetypes set a roof out, that recorded in `docs/LIBERTIES.md` and the affected families exempted
by name rather than by silence. Gates green, and the baseline smaller than 104 or explicitly
argued to be the wrong instrument.

**Links:** T-0145 (opened this) · T-0144 · L166 · `tools/measure_ridge_band.py` ·
`tools/ridge_model.py` · `tools/ridge_band_baseline.json` ·
`data/reconstruction/1835_family_archetype_crosswalk.json`.

---

## THE ANSWER (2026-08-24)

**None of the four claims gives way, because they were never in conflict.**
`tools/measure_ridge_reach.py` sweeps every family's whole authored footprint band and asks
whether ANY eave inside its eave band and ANY pitch inside its pitch band lands the ridge inside
its ridge band. At every footprint of every family that authors a pitch band, the answer is yes.
The specification is internally consistent and nothing in the crosswalk is edited, nothing is
exempted by name, and no liberty of the "the ridge column does not describe this project"
shape was needed.

What was wrong was the reading, not the specification. T-0145's instrument holds the eave at
whatever the record happens to carry and asks the pitch alone to reach the ridge band — but the
eave is the SECOND of two values the crosswalk authors as a band and the samplers draw from, so
a ridge band is reachable from a (footprint, eave) pair. Constraining one free claim and leaving
the other free made the second carry the first one's choice. The A1 stable this ticket is named
after reaches its 17-24 ft ridge band comfortably at an eave in the top half of the 9-12 ft its
own family authors.

**Carried out**, per family group in the baseline:

| group | the decision | done |
|---|---|---|
| A1, A4 in `north_infill` and `block_infill` | the SAMPLER gives way: draw the eave under the ridge band the way the pitch is already drawn | `family_bands.eave_for_ridge`; 6 records re-derived and re-baked |
| every group in `west_infill`, `inferred_infill`, `inferred_households` | the RECORD's retyped eave gives way — it is not one of the four claims, it is a constant that predates them | T-0172, which named these three parcels before this ran |
| A4, W4, W5 | the family authors NO pitch band, so the specification claims nothing here and the generator's own type default is what misses | folded into T-0172's sweep; reported as `no-pitch-band` |
| C1, F1, F4 as SHEDS | the crosswalk offers a roof form its ridge band cannot carry, latent because no generator deals it | T-0179 |

Baseline 64 -> 58, and the residual is now entirely records in the three parcels that never
sampled: `tools/measure_ridge_reach.py` prints the split by parcel so it cannot be mistaken for
a specification fault again. The sweep is a gate in `tools/check.sh`, so a future crosswalk edit
that authors an unbuildable family fails at the specification. Recorded as **L176**.
