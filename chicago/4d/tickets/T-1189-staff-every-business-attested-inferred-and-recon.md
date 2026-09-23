---
id: T-1189
title: Staff every business — attested, inferred and reconstructed — with real persons: attested partners and clerks first, then the reconstructed residents, then new reconstructed staff to the staffing model, so every working person has a workplace and every workplace its people
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

The owner: *"reconstructing the staff of the store … as part of their resident profile. Do this for
all of the attested inferred and reconstructed businesses."* This ticket runs after the five
reconstruction groups and after the resident band's trade households (T-1173), and it is the
join: it writes `staff[]` on every business and `works_at[]`/`roles[]` on every person, through
one tool, to the staffing model's ratios, recording the fill in the order book.

**Order of preference, enforced by the tool** (`tools/staff_businesses_1835.py --build|--check`):

1. **Attested/inferred staff** — every partner, clerk, apprentice, journeyman or servant a source
   names with an employer (the identity master's directory ties, Andreas's "clerk for …", the
   register's partners) — written at their tier with the source. Zero of these may be
   reconstructed over.
2. **Reconstructed residents with a matching trade and no workplace** (T-1173,
   T-1172) — seated at a business of their trade in their division, nearest first, seeded.
3. **New reconstructed staff** — only where a business is still short of its model's `typical`
   count: young men as clerks/apprentices (age band from the model), women as chambermaids/
   cooks at the hotels, hands at the packing houses — each a new reconstructed person in the
   proprietor's household (`relationship: clerk|apprentice|journeyman|servant`, the shop-household
   rule) or in a boarding house (T-1175), counted in the order book.
4. **No-premises trades** — labourers, teamsters, boatmen, sawyers: `works_at[]` entry of kind
   `no_fixed_premises` with the employer business where one is implied (the pier works, a packing
   house, a lumber yard) or `casual` with the reason.

**Acceptance:**

- Every business record's `staff[]` is within its model band, every person of working age
  (model band) has a `works_at[]` entry or an explicit `not_employed: <reason>` (keeps house,
  child, aged, gentleman of property, soldier — the garrison is T-1176's), and both are
  asserted by `--check` in `check.sh`; a mutation self-test breaks each.
- The Elston fixture: Daniel Elston's card shows his manufactory with its hands and his school
  inspectorship at its seat, dated, at their tiers.
- Report: staff written by tier and role; persons employed / not employed by reason; the
  order book's employment buckets read filled.
- Visible: every business card lists its people; every person card its workplace(s).

**Stop condition:** the join is total — no business without people, no working person without a
place or a reason.

**Links:** T-1183 · T-1184 … T-1188 · T-1173 · T-1175 ·
T-1166 · T-1145.
