---
id: T-1497
title: The D5 deep-plan cottage has no archetype that can build its front gable: dwelling_frame / deep_plan_gable_front, and the 58 roofs standing on an eaves-front placeholder until it exists
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-21
pr: 1632
claimed_by: run 9/21/2026, 10:13:03 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T16:25:34.959Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35616096832
---

The crosswalk has been asking for this in writing. `D5 — Deep-plan frame cottage` carries:

```json
"current_placeholder_archetype": "frame_dwelling",
"canonical_archetype": "dwelling_frame",
"required_variant": "deep_plan_gable_front",
"evidence_note": "The current frame_dwelling is eaves-front and therefore compresses
                  the defining front-gable silhouette; canonical support is required."
```

`dwelling_frame` does not exist. There is no file for it in `generators/archetypes/`, and
before this ticket no ticket named it. **58 roofs** are targeted on D5 town-wide.

**The two documents contradict each other, and both are sourced.** The crosswalk authors
D5 as `roof: "front gable, 7:12-10:12"`, `variants: "narrow urban plan; side entry"` —
a narrow-fronted house turned end-on. `generators/archetypes/frame_dwelling_params.py`
refuses exactly that shape, and says why:

> The eaves-front house is the 1835 form; the gable-front house, turned end-on to the
> street, is the Greek Revival habit that arrives with the Clarke House in 1836 and
> dominates the 1840s. [...] Rotate the footprint or record the building as something else.

So either D5 should not be a front-gable family for a 1 July 1835 scene, or
`frame_dwelling`'s 1836 date is too hard a line for a *deep-plan* cottage whose gable end
faces the street for want of frontage rather than for fashion. **That reading is the first
half of this ticket** and it is a research question, not a modelling one: settle whether a
deep-plan gable-front cottage stood in this town in 1835 before building an archetype that
assumes it did. If it did not, the repair is to the crosswalk and this ticket closes by
restating D5 — which is the cheaper answer and must not be ruled out to justify the work.

**What it costs today.** `west_rec_033` is a 20 x 32 ft D5 slot. The recipe's rectangle is
squarely inside D5's own band (`18x28-24x34`) and is exactly the authored form, but
`frame_dwelling` refuses it (32/20 = 1.6, past its 1.5 ceiling), so
`tools/generate_west_infill.py` swaps width and depth and turns the bearing a quarter
circle to get an eaves-front house through the placeholder. The result stands as
`32.00x20.00 ft`, which reads OUT of the band it cites. On the owner's ruling of
2026-09-21 that compromise is kept rather than holding the slot, and it is banked in
`tools/band_claims_baseline.json` with `waiting_on` naming this ticket — so
`measure_band_claims.py` turns red the moment this ticket closes and the exception is
still there. The compromise cannot outlive its excuse.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The 1835 question answered first, in `docs/RESEARCH/`, with sources: did the deep-plan
   gable-front cottage stand in Chicago on 1 July 1835, or is it a form of 1836 and after?
   A negative answer closes this ticket by repairing the D5 crosswalk row instead, and
   that is a legitimate outcome.
2. If affirmative: `dwelling_frame` with the `deep_plan_gable_front` variant, ridge
   running front-to-back, built to D5's authored band, eave and ridge figures.
3. `west_rec_033` re-derived from the recipe's own `[20, 32]` with no swap, its
   `FACING_CORRECTIONS` membership removed and the setback prose with it.
4. Its row LEAVES `tools/band_claims_baseline.json` — the ratchet records the repair, which
   is the only thing it was ever meant to record.
5. `frame_dwelling_params`'s 1.5 refusal stays exactly as it is for every eaves-front
   family. This ticket adds a form; it does not relax a gate.
