---
id: T-1197
title: Re-audit the 285 anonymous roofs against the re-derived programme: keep the ones the order book can occupy, re-family the ones of the wrong kind, retire the ones that no longer fit — 214 stand empty today — and record every change as a substitution, not a demolition
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

The owner: *"review and replace any previous reconstructed buildings that do not fit your current
understanding of the population now that the significant research has been applied, many of
which are unoccupied."* 285 records carry a `reconstruction` block, all `inferred_anonymous`:
214 with no occupant, 31 "anonymous stock" from the retired programme (`resident_assignment:
unassigned`), 40 seated with a documented business (L212/L218). They were dealt to the 2026-08
schedule by block recipes (`1835_platted_block_parcels.json`, the north and west parcels).

**Acceptance:**

- `tools/redeal_anonymous_roofs.py --build|--check`: for every anonymous roof, against the
  re-derived programme (T-1196) and the placement policy (T-1195): `keep` (its
  family and position are wanted here — the order book has an occupant class for it), `refamily`
  (the slot is wanted but as another family — e.g. a D4 cottage on a South Water party line
  should be a C2 store-residence; the record's family, form and footprint band change, the
  position stays), `retire` (nothing in the order book wants a roof of this kind here — the
  record moves to `data/exclusions.json` under a `retired_reconstruction` guard with the reason,
  its GLB deleted from the manifest by the bake, its liberty `Covers:` tokens moved to Resolved).
  The 40 business-seated roofs are `keep` unless the business's audited location (T-1182)
  moved. The 31 stock roofs are dealt first to the trades they were raised for (their
  `reconstruction.occupation`) where T-1185 wrote that firm.
- The recipe files are updated by the tool so the three infill generators re-derive byte for
  byte (`--check` green); `reconcile_665.py` and the town census re-derive; `measure_massing_variety.py`
  and the band gates green after refamilying.
- Every change is a row in `data/reconstruction/1835_roof_redeal.json` with before/after family,
  reason and the order-book bucket it now serves; LIBERTIES entry with scope; the counts
  keep / refamily / retire printed.
- Bake (`needs_bake: true`): refamilied and retired records rebuilt; a screenshot from Lake and
  Clark shows the difference.

**Stop condition:** no anonymous roof stands that the order book cannot give an occupant, and no
wanted slot is held by a roof of the wrong kind.

**Links:** T-1196 · T-1195 · T-0489 · T-0516 · T-0167 (the vacant/to-let rule, L167)
· `data/reconstruction/1835_platted_block_parcels.json`.
