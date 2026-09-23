---
id: T-1175
title: Fill the beds: boarders, lodgers, hotel guests, boarding-house keepers' households, the crews of the vessels in port and the hands at the works, seated in the named and reconstructed lodging places to the lodging model's capacities
state: split
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-19
pr: null
claimed_by: run 9/19/2026, 12:24:32 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T05:24:46.859Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35423674899
---

No boarder or lodger exists in the layer; the eight public houses, Brown's boarding house and the
42-roof boarding programme hold nobody but their keepers. Stage `lodgers` of T-1167,
driven by T-1164 and the businesses of T-1187.

**Rules:** for every lodging place (structure or reconstructed business) — its capacity and its
resident mix from the lodging model → (1) the single men the household model marked `boarding`
(from T-1171, T-1173, T-1186) are seated first, nearest their
workplace, by the mix (professionals and land agents at the Tremont, Sauganash and Mansion
House; mechanics at the Green Tree, the Steamboat and the smaller houses; labourers on the
floors of the boarding houses and in family houses taking boarders); (2) short beds are filled
with new reconstructed lodgers (trade from the occupation model's residual, age from the model);
(3) the keeper's own household (spouse, children, staff) per the household and staffing models;
(4) vessel crews as `lives_at: <vessel>` with the master; the pier-works gang in its camp
(T-1178). `relationship: boarder|lodger`, `lives_at[]` at tier `reconstructed`, basis =
the capacity row, seed.

**Acceptance:**

- Every lodging place's occupancy is within its capacity band and printed; the model's lodger
  bracket is met; nobody is seated twice; keepers' households complete.
- Visible: the hotel/tavern/boarding-house cards list their residents by tier ("Lived here"),
  and each lodger's card names the house.

**Stop condition:** the beds the town had are slept in, by named reconstructed people who say so.

**Links:** T-1167 · T-1164 · T-1163 · T-1187 · T-1189.
