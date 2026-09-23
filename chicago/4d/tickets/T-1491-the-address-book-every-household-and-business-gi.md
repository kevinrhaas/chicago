---
id: T-1491
title: The address book: every household and business given a row at the rung its evidence reaches — a named roof, a lot, or an honest refusal — with the reach recorded where the seat is owed to the reconstructed rungs, written and gated by tools/seat_known_1835.py, and said on the household card in words
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1198
opened: 2026-09-20
closed: 2026-09-20
pr: 1594
claimed_by: run 9/20/2026, 4:38:04 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T22:42:52.947Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35538794207
---

The address book: every household and business given a row at the rung its evidence reaches — a named roof, a lot, or an honest refusal — with the reach recorded where the seat is owed to the reconstructed rungs, written and gated by tools/seat_known_1835.py, and said on the household card in words.

Piece 1 of 3 of **T-1198 — Seat every attested and inferred household and business on the ground its evidence allows: a structure where one is named, a lot on the right face where an address, corner or later directory narrows it, a division band where only that is known — plural, dated, no fabricated coordinates**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Why the parent split here.** T-1198's ladder mixes two different kinds of work. Rungs 1,
2, 3 and 6 READ committed evidence — a roof a record names, a lot the plat's own unit, a
street a paper prints, a refusal already adjudicated. Rungs 4 and 5 RECONSTRUCT: they deal a
band to a household no source places anywhere. Doing both in one pass is exactly how a
reconstructed band comes to be read as a reading, because it arrives in the same file, on the
same day, in the same sentence as the evidence. So this piece writes the evidence rungs and
records the REACH for everything else with `seat: null`; T-1492 deals the bands; T-1493 makes
them navigable.

**Acceptance:**

- `tools/seat_known_1835.py --build|--check|--report|--self-test` writes
  `data/reconstruction/1835_address_book.json`: one row per committed household and per
  adjudicated firm, no row twice, none missing.
- Each row carries `rung`, `seat`, `reach`, `tier`, `basis`, `words`, `replaceable_by` and,
  where the seat is owed, `owed_to`.
- **No seat is invented here.** A row at the `owed` rung may not carry a seat, and every seat
  that IS carried names a committed structure. Both gated.
- The business half is a strict restatement of `data/research/location_spend.json`: a firm
  whose rung stops agreeing with its adjudicated grade fails the gate, and the 62 unplaceable
  firms remain unplaceable.
- Rung 2 stands empty by MEASUREMENT — the gate re-reads the committed lot-address ledger and
  fails the day it grows, rather than the rung quietly staying empty.
- `--check` and `--self-test` are steps in `tools/check.sh`.
- **Visible:** the household card says where its household stood and at which rung, in words,
  in place of the bare "No known address" 1,186 of the 1,393 cards carried — and says what
  would move it up the ladder.

**Deliberately NOT here:** rungs 4 and 5, the re-derivation of `division` from the row, the
People view's division filter (all T-1492), and Go-to for a lot or a face (T-1493).
