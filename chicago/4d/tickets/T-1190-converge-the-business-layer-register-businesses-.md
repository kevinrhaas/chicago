---
id: T-1190
title: Converge the business layer: register, businesses, persons and structures agree by id; every reconstructed firm carries its substitution rule and liberty; the trade-census crosswalk, the order book and the Businesses view print the finished count
state: split
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-20
pr: null
claimed_by: run 9/20/2026, 6:04:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T11:28:18.516Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35506620874
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

**A FINDING FOR CLAUSE 1, HANDED OVER BY T-1432 (2026-09-20).** The staffing join put every
card's own name beside every name the register printed for it — the first time the two have
stood in one place — and three cards disagree mechanically. They are counted in
`data/reconstruction/1835_staffing_join.json` under `questions_for_the_convergence`, and the
join carries `printed_as` on every row so a reader can check the match rather than take it:

- `kinzie_james` — the card reads **James Kinzie** and holds three houses printed *J. H.
  Kinzie*, *John H. Kinzie* and *John S. Kinzie*. The printings disagree with each other about
  the middle initial AND with the card about the forename. James Kinzie and John H. Kinzie were
  two men; if these rows are John's, one card is carrying another man's trade.
- `hogan_john` — the card reads **John Hogan**, every printing *John S. C. Hogan*.
- `bradley_joseph` — the card reads **Joseph Bradley**, every printing *J. C. Bradley*.

T-1432 raised these and did not touch them: it carries rows across at the identity the business
layer already asserted and re-matches nobody. Re-matching is this ticket's clause 1.

**AND ONE ROW LEFT OVER BY T-1428 (2026-09-20).** The crosswalk, the order book and the
1835 town model all say, per class, how much of a shortfall is houses the register names
with an opening dated after the scene date — `school` is 7 against 5 with 2 explained, and
orders nothing. `data/research/residents/inwindow_trade_workplaces.json` was rebuilt with
the corrected figures but its row still reads `still_short: 2` with `owed_to: null`: right
arithmetic, and it hands the two to nobody, but the row does not say they are accounted
for. When this ticket makes the finished counts print, make that row say it too.

**Stop condition:** the business layer is complete to the order book, reproducible, and every
invented firm says how it will be replaced.

**Links:** every ticket in this band · T-1144 · T-1147 · T-1166.
