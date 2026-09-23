---
id: T-1190
title: Converge the business layer: register, businesses, persons and structures agree by id; every reconstructed firm carries its substitution rule and liberty; the trade-census crosswalk, the order book and the Businesses view print the finished count
state: open
epic: META
requested_by: owner
seen: true
effort: S
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

The closeout of the business band, the way T-1144 closes the resident spend. After it, the town
has *"a complete list of data of attested and inferred … businesses … and added to that …
reconstructed … businesses … marked and classified correctly as reconstructed so if we get new
research we can replace the reconstructed … business with an inferred or attested one later."*

**Acceptance:**

1. **Fixed point.** `compile_businesses.py`, `compile_register.py`, `staff_businesses_1835.py`,
   `reconstruct_businesses_1835.py` (all groups) and `compile_agencies.py` re-derive with zero
   drift; every `works_at[]`, `staff[]`, `proprietors[]`, `locations[]` id resolves; zero dangling
   business on a structure and zero structure named by a business that does not stand or is not
   scheduled in the structure band (the schedule is a field, not a hope).
2. **Substitution rule, tooled.** `tools/substitute_reconstruction.py --dry-run` takes a new
   attested/inferred business (or person) and prints the reconstructed record(s) its
   `replaceable_by` matches, with the retirement it would perform (redirect id, carry the roof,
   free the order-book row). A self-test proves it on a fixture; the rule is documented in
   `docs/PROVENANCE.md`.
3. **Liberties.** Every reconstructed firm is covered by a `docs/LIBERTIES.md` entry whose
   `Scope:` count the compiler agrees with; L211/L212/L218/L232 scopes re-counted.
4. **The counts.** The trade-census crosswalk (Sept–Dec 1835 State census) re-run: per class,
   attested / inferred / reconstructed / census, with the documented zeros still zero; the
   American's August counts beside it; the order book's business buckets read filled;
   `docs/RESEARCH/business-layer-final-2026-09.md` published with every table.
5. **Visible:** the Businesses view's counters and tier filter show the finished layer; the
   "Reconstructing the town" card's business bars read full.
6. Gates: everything above under `check.sh` with mutation self-tests; no gate weakened.

**Stop condition:** the business layer is complete to the order book, reproducible, and every
invented firm says how it will be replaced.

**Links:** every ticket in this band · T-1144 · T-1147 · T-1166.
