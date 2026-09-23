---
id: T-1179
title: Converge the reconstructed resident layer: index, sidecars, town census, People view and gates agree; every reconstructed person carries basis, seed, liberty and substitution rule; the population profile is re-run and the town reads complete against the model
state: open
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The closeout of the resident band, the way T-1144 closes the spend. After it, the owner's
sentence holds: *"All people should have a best profile … note for each attribute of the person
what is attested, inferred or reconstructed."*

**Acceptance:**

1. **Fixed point.** `reconstruct_residents_1835.py --check` (every stage), `rebuild_resident_index.py
   --check`, the three mints' `--check`, `compile_scene.py compile_people`, `town_census.py
   --check`, `export_resident_audit.py --check` all re-derive with zero drift; the audit table
   gains the reconstructed rows with their basis.
2. **Per-attribute completeness.** `profile_population_1835.py` re-run: every person has sex,
   age band, arrival, origin, reason, roles (or `not_employed` reason), presence, division,
   household relationship — each at a tier; the report's "unknown" columns read zero or list the
   attested/inferred rows where the sources conflict (T-1146's `contradicted`).
3. **The model met.** Headcount, sex ratio, age pyramid, household sizes, lodging occupancy,
   division split, trades — every table within the model's bracket; the order book's person and
   household buckets read filled; the town census screen shows residents / transients / garrison
   and the dwellings ratio.
4. **Substitution.** `substitute_reconstruction.py` (T-1190) handles persons: a new
   attested/inferred person retires the reconstructed one its `replaceable_by` matches, redirects
   the id, frees the bucket; self-test on a fixture.
5. **Liberties.** One entry per stage with `Scope:` counts the compiler agrees with; L1 restated
   (no figure drawn — a reconstructed person is a card, not a body in the scene).
6. **Visible.** People view: tier filter, transient/fort/reconstructed pills, per-attribute tier
   on the card; the "Reconstructing the town" card's person bars full; `smoke_renderer.mjs` walks
   a reconstructed card at both viewports.
7. `docs/RESEARCH/1835_resident_reconstruction.md` closes with the final tables and the exact
   counts by tier; `docs/STATUS.md` says what is unverified.

**Stop condition:** the resident layer is complete to the model, reproducible, and every invented
fact says how it will be replaced.

**Links:** every ticket in this band · T-1144 · T-1160 · T-1166 · T-1190.
