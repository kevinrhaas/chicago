---
id: T-1166
title: The reconstruction order book: known minus model, per bucket and per division — exactly how many persons, households, businesses and structures of each kind to reconstruct, in the order the bands below will build them, published as a card
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

This closes the 1835 TOWN ANALYSIS band. Every model above (T-1161, T-1162,
T-1163, T-1164, T-1165) states a target; the profile (T-1160)
states the known; the roster (T-1159) states the real names on offer. The order book is the
subtraction, resolved into work: one file the reconstruction tickets read to know their quota
and write to as they fill it, so the town converges on a number instead of on a feeling.

**Deliverable** — `data/reconstruction/1835_reconstruction_order_book.json`, built by
`tools/build_order_book_1835.py --build|--check|--self-test`:

1. **Person buckets**: sex × age band × division × household type × (trade | none), each with
   `target`, `known_attested`, `known_inferred`, `roster_offered` (by class), `to_reconstruct`,
   and the ticket that owns filling it (T-1168 … T-1178).
2. **Household buckets**: type × division, same columns.
3. **Business buckets**: trade/type × division, `target`, `known`, `to_reconstruct`, owning
   ticket (T-1184 … T-1188), and the STAFF each implies.
4. **Structure buckets**: archetype family × division, `target` (from the roof programme as
   corrected by the occupation and lodging models), `standing`, `standing_unoccupied`,
   `to_build`, `to_retire_or_redeal`, owning ticket (T-1200 … T-1214).
5. **Ground buckets**: which blocks/streets must exist first (T-1191,
   T-1192, T-1193) for each structure bucket.
6. **Invariants** the convergence tickets assert: every person housed; every working person
   with a workplace or a stated "no fixed workplace"; every business with staff; every structure
   with an occupant or a stated use; the town census's dwellings ratio within its bracket.
7. `filled` counters per bucket that the reconstruction tools increment through their own
   `--build`, so `--check` fails if a bucket is overfilled or a filler bypasses the book.

**Acceptance:**

- Builds, re-derives, `--check` in `check.sh`; `docs/RESEARCH/1835_reconstruction_order_book.md`
  prints every bucket and the total the town converges to (persons, households, businesses,
  roofs), each against its model bracket.
- **Visible:** a "Reconstructing the town" card in the Evidence hub reads the JSON and shows the
  buckets with filled / to-do bars (this card becomes the progress view of the next three
  bands and is updated by their builds, not by hand).
- The QUEUE band headers for RECONSTRUCT RESIDENTS, BUSINESSES and STRUCTURES gain one comment
  line each naming this file as the quota (the only queue edit).
- Where a model target and the roof programme disagree the order book carries the model and
  lists the programme delta for T-1196.

**Stop condition:** a reconstruction ticket reads its quota from one file, fills it through a
tool that records the fill, and the card shows the town filling up.

**Links:** every ticket in this band · `data/reconstruction/1835_665_roof_programme.json` ·
`data/town_census.json`.
