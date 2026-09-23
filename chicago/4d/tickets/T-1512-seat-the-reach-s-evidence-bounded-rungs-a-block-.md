---
id: T-1512
title: Seat the reach's evidence-bounded rungs: a block face for every street-only row the face adoption refused, and the placement policy's band for every household whose own record already names a division — seeded, tier-marked, and said on the card in words
state: done
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1492
opened: 2026-09-21
closed: 2026-09-21
pr: 1626
claimed_by: run 9/21/2026, 7:44:03 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T13:41:50.185Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35600413508
---

Seat the reach's evidence-bounded rungs: a block face for every street-only row the face adoption refused, and the placement policy's band for every household whose own record already names a division — seeded, tier-marked, and said on the card in words.

Piece 1 of 2 of **T-1492 — Seat the reach: the address book's reconstructed rungs — a block face for a street-only row, a division band where only the division is known, the policy's band where nothing is — seeded, tier-marked, and every household's division re-derived from its row so the People view's division filter fills**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. **The band vocabulary is an adjudication over the committed placement policy, not a
   new reading.** Every band names the clause of `1835_placement_policy.json` it rests
   on, quotes that clause's own statement, and lists the divisions the clause reaches.
   A band that cites a clause the policy does not hold fails the gate.
2. **Rung 3 — a block face for every street-only row the face adoption refused.** The
   21 firms T-1239 grades `street_only_unseated` stand on the face of the street their
   advertisement names, with `seat.kind: street_face`, no roof, no lot and no
   coordinate. The street is the evidence and carries `inferred`; standing them on the
   face without a roof is the reconstructed step and the row says so.
3. **Rung 4 — the policy's band for every household whose own record names a division.**
   A household with no `lives_at` whose card carries `south`, `west`, `north` or `fort`
   is seated at `division_band`, in that division and never another, with the band the
   policy's clause for the head's trade gives. Where no clause reaches the head's trade
   — `none_recorded`, and the trades the policy has no dwelling clause for — the band is
   the division's own ground and nothing narrower, and the row says that in words rather
   than dealing a class the record does not carry.
4. **Nothing is invented.** No coordinate, no lot, no roof and no division appears in a
   reconstructed seat that is not already in the household's own committed record. Every
   reconstructed seat carries `tier: reconstructed`, its clause as `basis`, a `seed` and
   a `replaceable_by`. No household record is written to by this piece.
5. **The rungs above do not move.** The 76 households seated at a named roof, the 40
   adopted firms, the 62 unplaceable firms and the empty rung 2 are byte-identical.
6. `--check` re-derives the book byte for byte and is in `tools/check.sh`; `--self-test`
   fires every assertion, the new ones included.
7. **Visible:** the People view's seat line labels the new rung — a household at rung 4
   reads as banded in its division rather than as "No source places this household".

**Not this piece (T-1513 owns it):** the 1,186 households no source places anywhere, the
division draw that would give them one, and the write-back that fills the People view's
division filter.
