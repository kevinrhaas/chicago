---
id: T-1346
title: The 1839 directory's trade table: every Fergus 1839 entry's printed trade counted against the controlled vocabulary, with its refusals and the 1840 industry columns beside it — the per-trade share T-1162's withdrawal left the programme without
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1173
opened: 2026-09-18
closed: 2026-09-18
pr: 1488
claimed_by: run 9/18/2026, 6:54:10 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T01:27:22.503Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35406958128
---

The 1839 directory's trade table: every Fergus 1839 entry's printed trade counted against the controlled vocabulary, with its refusals and the 1840 industry columns beside it — the per-trade share T-1162's withdrawal left the programme without.

Piece 1 of 2 of **T-1173 — Reconstruct the trade households the occupation model still wants after the known and re-admitted people are counted: labourers, carpenters, teamsters, sawyers, masons, boatmen, clerks and the rest, by division, each head named from the pools with a family per the household model**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why the parent split here.** T-1173's own rules say a reconstructed head's trade is
drawn from "the occupation model's `gap` per trade (T-1162)". **T-1162 is withdrawn** —
its figures were folded into `1835_town_model.json`, and the fold kept the establishment
comparison and the 1840 industry columns but not the per-trade share T-1162 § 2 asked
for first. The order book buckets a person `trade` or `none` and names no trade. So the
parent was two demonstrations: derive the distribution, then draw people from it. This
is the first.

**Acceptance:**

- `tools/build_trade_table_1839.py --build|--check|--self-test` writes
  `data/research/directories/fergus_1839_trade_table.json` off the committed
  `claims/fergus_1839_directory_entries.json`, and `--check` re-derives it in `check.sh`.
- Every entry carrying a printed trade is either MAPPED or REFUSED IN WRITING:
  `mapped + refused == entries_with_a_printed_trade`, asserted by `--self-test`, with
  every refusal carrying its class, its reason and every form it caught.
- Two builds on one set of inputs are byte-identical.
- The 1839 shares are set against the 1840 schedule's seven industry columns, in the
  table and in prose, with the deltas read as shape and not as error.
- Trades the volume prints and `index.json`'s `vocabulary.occupations` has no word for
  are counted and NAMED, as the extension T-1347 owes before it may write one.
- The table states in its own first paragraph that 1839 is four years late and this
  volume is an 1876 completion — a prior for a draw, never a count of 1835 and never
  evidence about a person.
- `docs/RESEARCH/1839_trade_table.md` prints the table and the derivation of every rule.
- No person's card is touched, no confidence moves, and no `data/residents/` file changes.

**Result (2026-09-19).** 1,655 entries, 1,583 printing a trade; 1,377 mapped (87.0%)
onto 88 trades, 206 refused across six classes. Manufactures and trades reads 0.444
against the 1840 schedule's 0.466, river-and-lake navigation 0.070 against 0.071, ocean
navigation 0.010 against 0.010. Agriculture (0.039 vs 0.156) and commerce (0.340 vs
0.213) diverge for reasons about the documents, both written down. 13 trades sit outside
the 1835 vocabulary.
