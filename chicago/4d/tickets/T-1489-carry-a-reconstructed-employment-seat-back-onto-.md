---
id: T-1489
title: Carry a reconstructed employment seat back onto the card of the person who holds it: the six mint-owned resident directories re-derive whole, so workplaces[] stops at households/ and 91 of the 124 seated people say nothing about work on their own card
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-21
pr: 1612
claimed_by: run 9/21/2026, 1:10:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T07:34:55.667Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35566824444
---

Carry a reconstructed employment seat back onto the card of the person who holds it: the six mint-owned resident directories re-derive whole, so workplaces[] stops at households/ and 91 of the 124 seated people say nothing about work on their own card.

**Acceptance:** (stated before working — the definition of done, never weakened to pass)

1. Every person `tools/seat_reconstructed_trades_1835.py` SEATS carries that seat on
   their own card, in whichever of the seven resident directories they stand in, as one
   key in a fixed slot beside the trade. Measured before: 33 of 123. Wanted: 123 of 123.
2. The other four answers — `class_held_no_house`, `keeps_their_own_house`,
   `no_employer_named`, `no_ruling` — reach NO card. They are statements about an
   absence, and a reason for having no seat where a reader looks for a seat is worse
   than a silence.
3. The key is not `workplaces`. That field means a source puts this person in this
   house and its gate asserts a business record naming them back; a drawn seat has no
   such record and the two may never be read as one.
4. The block is a POINTER, not a copy of the adjudication: no `candidates_considered`,
   no `chosen_by`, no model `basis` note, nothing that would go stale when the business
   layer moves with no gate able to tell a stale copy from a re-derivation that has not
   run.
5. Every stage that derives a resident directory WHOLE carries the key through its own
   re-derivation, on the same fixed-slot contract `tools/resident_mint_carry.py` already
   gives `workplaces`, so its byte-for-byte `--check` stays a byte comparison and the
   key is not deleted on the next `--build`.
6. The seat pass is the SOLE authority on what the block may say, asserted both ways: a
   block on a card it seats nowhere is a fossil and fails; a seated person whose card is
   silent fails. A stage carrying a block it cannot validate is safe only because of
   this.
7. `--check` is in `tools/check.sh` and the whole gate is green; `--self-test` fires
   eleven assertions.
