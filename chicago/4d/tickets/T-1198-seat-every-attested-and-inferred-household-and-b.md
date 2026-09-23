---
id: T-1198
title: Seat every attested and inferred household and business on the ground its evidence allows: a structure where one is named, a lot on the right face where an address, corner or later directory narrows it, a division band where only that is known — plural, dated, no fabricated coordinates
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
needs_bake: false
closed_at: null
claimed_run: null
---

1,243 of 1,263 households have no `lives_at`; 1,213 no `works_at`; 1,191 are `unplaced`. T-1147
spends every LOCATION FACT the research holds and preserves the 123 business location limits;
this ticket takes the households and firms T-1147 leaves placed-to-a-street or unplaced and seats
them AS FAR AS THE EVIDENCE GOES plus one honest reconstructed step, through the placement policy
— never past it. It writes the **address book**: `data/reconstruction/1835_address_book.json`,
one row per household and per business, built by `tools/seat_known_1835.py --build|--check`.

**The seating ladder** (the first rung that fires; the row names it):

1. `structure` — a named roof (the 20 + the T-1147 spend): unchanged, tier as spent.
2. `lot` — an address, a corner ordinal, a lot-and-block line, a back-projected face (L218/L223)
   that narrows to a lot or two: the lot id(s) on the extended lot grid (T-1194),
   tier `inferred`, the policy from `docs/LOT-ADDRESS.md`/`CORNER-ORDINAL.md`/`ADDRESS-BACK-PROJECTION.md`.
3. `face` — a street only (the 61 street-only firms; a directory street): the block face(s)
   the policy prefers for that trade/household on that street, tier `inferred` for the street,
   `reconstructed` for the face choice, seeded.
4. `division_band` — a division from the evidence (a north-side baptism, a Wolf Point tavern
   keeper's household): the policy's band for that household class in that division, tier
   `reconstructed`.
5. `policy_only` — nothing in the evidence: the policy's band by trade/wealth class alone,
   tier `reconstructed`, and the row says so in words ("no source places this household; seated
   by the policy's rule <id>").
6. `unplaceable` — the evidence CONTRADICTS every band (T-0305's four American addresses, T-0251,
   T-0386 until ruled): stays unplaced with the ticket that owns it.

A household follows its head's workplace where the policy says trades lived at their shop
(store-residences, shop-houses, the keeper of an inn), and the row records which.

**Acceptance:**

- Every attested/inferred household and business has an address-book row at some rung; counts
  per rung printed; rungs 1–2 never move on a rung 3–5 rule; the 62 unplaceable firms remain
  unplaceable unless a rung ≤ 3 fact is cited.
- `division` on every household re-derived from the row (no household reads `unplaced` that
  has a rung ≤ 5 seat); the People view's division filter fills.
- `--check` in `check.sh`; the row's `replaceable_by` = a stronger rung.
- **Visible:** the household card's "Lived at / Worked at" show the seat and its rung in words;
  "Go to" takes the visitor to the face or lot; nothing is drawn — the roofs come in the build
  tickets.

**Stop condition:** every known person has a place on the map at the honest rung, and the build
tickets know which lot to raise a roof on for whom.

**Links:** T-1147 · T-1195 · T-1194 · T-0251 · T-0305 · T-0386 · T-1087 ·
`docs/STREET-FACE-ADOPTION.md` · `docs/ADDRESS-BACK-PROJECTION.md` · `docs/RESIDENCE-BACK-PROJECTION.md`.
