---
id: T-1164
title: The 1835 lodging and institutional model: every hotel, tavern, boarding house, the fort, the vessels in port and the camps — who slept where, at what capacity, from the named records and the season's evidence
state: withdrawn
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1293
needs_bake: false
closed_at: 2026-09-17T20:06:19.211Z
claimed_run: null
---

The owner, 2026-09-17: *"there are other things like hotels and boarding houses that would have
residents and if you don't have them you should reconstruct also."* The town census's 8.2 people
per dwelling is the boarding town speaking: in July 1835 the hotels "were always full; and full
meant three in a bed sometimes, with the floor covered besides". The project already holds the
named lodging records — Sauganash, Green Tree, Mansion House, Tremont, New York House, Exchange
Coffee House, Steamboat Hotel, Western Hotel, Travellers' Home, Wolf Point tavern, Lake House
(under construction — check its date), Brown's boarding house, the Eagle/others the register
prints — each with a `docs/RESEARCH/<id>.md` dossier, and the roof programme's 42 boarding-house
and 10 inn slots. Nobody has said how many people each held.

**Deliverable** — `data/reconstruction/1835_lodging_model.json`, built by
`tools/build_lodging_model_1835.py --build|--check|--self-test`, one row per lodging PLACE:

1. **Named hotels, taverns, boarding houses** (attested/inferred structures): keeper household
   (from the layer), storeys/footprint (from the record), **capacity** derived from the record's
   own dimensions and the period rule (rooms × beds × the "full" multiplier), staff (bar-keeper,
   hostler, cook, chambermaid — per the staffing model), and the resident mix the sources show
   (lawyers and land agents at the Tremont/Sauganash, mechanics at the smaller houses).
2. **Anonymous boarding-house and inn slots** in the roof programme: same fields at
   `reconstructed`, sized from the family's dimensional band.
3. **Private houses taking boarders** — a share from the household model.
4. **Fort Dearborn** — officers' quarters, barracks, laundresses' quarters, the sutler's, the
   Agency house: who the sources put there in July 1835 (`fort_dearborn_*.md`), capacity from
   the compound's roofs.
5. **Vessels in port and the harbour works** — crews sleeping aboard, the pier-works gang; the
   lighthouse keeper.
6. **Camps** — the land-sale crowd of June 1835 and immigrants awaiting lots: what Andreas and
   the newspapers say about tents and wagons; a bounded bracket and WHERE (the lake shore south
   of the fort, the prairie edge west, Wolf Point) as candidate ground for T-1214.
7. Sum of capacities against the transient + lodger brackets of T-1161; the slack stated.

**Acceptance:**

- Builds, re-derives, `--check` in `check.sh`; `docs/RESEARCH/1835_lodging_model.md` prints the
  table with each capacity's derivation and the dossier quotes behind it.
- Every named lodging structure gains a `capacity` block at the tier the derivation supports,
  through the generator that owns the record, not by hand.
- No person is minted; T-1175 fills the beds.
- Visible: the business/structure card of each hotel and boarding house shows its capacity and
  the derivation.

**Stop condition:** every bed in the town is accounted for as a number with a reason, and the
transients have candidate ground.

**Links:** T-1161 · T-1163 · `docs/RESEARCH/sauganash_hotel.md` ·
`docs/RESEARCH/green_tree_tavern.md` · `docs/RESEARCH/tremont_house_1.md` ·
`docs/RESEARCH/fort_dearborn_barracks.md` · `docs/RESEARCH/residents_1835_inferred.md` § 3.
