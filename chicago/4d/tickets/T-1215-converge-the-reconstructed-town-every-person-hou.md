---
id: T-1215
title: Converge the reconstructed town: every person housed, every business roofed, every roof occupied or its use stated, the census's dwellings ratio met, the programme reconciled, the budgets re-measured and set — the completion report a visitor can open
state: open
epic: TOWN
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
needs_bake: true
closed_at: null
claimed_run: null
---

The closeout of the whole reconstruction. The owner's stop condition, verbatim: *"you must
complete all businesses and all structures, and all residences so that every person in Chicago
has a place to live and a place to work … your goal here is to complete the entire city with
reconstruction based on evidence."*

**Acceptance:**

1. **The join is total.** `tools/audit_town_completion_1835.py --check` (in `check.sh`): every
   person's `lives_at[]` resolves to a standing structure, a vessel or a camp; every working
   person's `works_at[]` to a standing structure, a vessel, a camp or a stated `no_fixed_premises`;
   every business's primary location to a standing structure or a stated street-only/unplaceable
   limit (the T-1147 limits preserved and printed); every structure carries `occupants` or a
   stated use (`vacant_to_let` per L167, `outbuilding_of: <id>`, `civic`); zero dangling ids.
2. **The numbers.** The town census screen shows: roofs standing = programme target (or the
   headroom and why); dwellings vs the census's 398 within the bracket; residents / transients /
   garrison; households housed = households; the order book reads filled in every bucket; the
   roof programme reconciles; `docs/RESEARCH/1835_town_completion.md` prints every table by tier
   (attested / inferred / reconstructed) for persons, households, businesses, structures, streets.
3. **Fixed point.** Every generator and derived layer re-derives drift-zero; every LIBERTIES
   entry's `Scope:` agrees with the compiler; `substitute_reconstruction.py` covers structures
   (a new attested roof retires the reconstructed one on its lot).
4. **The budgets, honestly.** `measure_detail_ceilings.mjs` on the published tree at every stand;
   the ceilings and draw-call budget set consciously where they are defined, with the reasoning,
   `light` inside its floor; T-1154's finding reconciled (its trim landed, or the re-budget
   stated in its ticket); `smoke_renderer.mjs` green at both viewports on the published tree;
   the boot payload within `measure_boot_payload.mjs`'s budget or re-set with the reason.
5. **Visible.** The "Reconstructing the town" card reads complete; a walk from the fort to Wolf
   Point along South Water, Lake and Canal Street with a screenshot at each stand, committed under
   `docs/RESEARCH/shots/`; `docs/STATUS.md` states what remains unverified.
6. **The gate screen** says the town is complete to the reconstruction of 2026-09 and names the
   three tiers' shares.

**Stop condition:** a visitor can walk the whole town and open any door, and every door has a
name, a trade, a family and a reason behind it — or an honest empty.

**Links:** every ticket in this band · T-1179 · T-1190 · T-1154 · T-1156 ·
`data/town_census.json`.
