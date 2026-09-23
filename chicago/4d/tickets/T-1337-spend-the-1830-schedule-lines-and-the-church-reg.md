---
id: T-1337
title: Spend the 1830 schedule lines and the church register sponsorships onto the cards they name: a dated bound where the identification already stands, and a written refusal under a named rule where it does not
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1329
opened: 2026-09-18
closed: 2026-09-18
pr: 1467
claimed_by: run 9/18/2026, 12:58:42 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T19:36:02.593Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35376396531
---

Spend the 1830 schedule lines and the church register sponsorships onto the cards they name: a dated bound where the identification already stands, and a written refusal under a named rule where it does not.

Piece 1 of 2 of **T-1329 — Spend the 1830 schedule lines, the church register sponsorships and the press notices onto the cards they name, each as a dated bound on a held resident's presence and never more**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every one of the 110 units T-1329 left on these two corpora — 15 from the 1830 Peoria &
   Putnam schedule, 95 from the church registers — reaches a terminal disposition. None is
   `unresolved`, none names a further arrival ticket, and `measure_research_spend.py --check`
   is green with 0 units owned by this ticket.
2. Where an identification ALREADY STANDS in a committed crosswalk it is written onto the
   card as a structured, source-bearing field — `persons[].dated_bounds[]`'s sibling
   `persons[].appearance_bounds[]` — and `research_spend_ledger.natural_disposition` closes
   the unit `asserted` off that field. That is 27 rows on 21 cards: the 14 `matched` rows of
   `census_1830/resident_crosswalk.json` and the 13 `merged` attendance rows of
   `church/st_marys_baptisms_crosswalk.json`.
3. This pass MAKES no identification. A name the residents layer holds twice or not at all
   is refused, never chosen between, and nothing is written off St Cyr's pages, off a
   declared candidate, or off a surname-only agreement.
4. An 1830 line bounds presence in a DISTRICT and not at Chicago: `bound_kind:
   "district_presence"`, `here_by: null`. The division is headed 'Peoria & Putnam Counties &
   Territory attached', it never writes the word Chicago, and the record's own note says so
   already. Writing 14 Chicago presences off it would overturn that reading in a field
   nobody reads — the shape of T-1117's tax-roll ruling, one corpus later.
5. No row reaches `attested` and no row covers the scene date. And the ladder cuts both
   ways: the three register appearances dated after 1 July 1835 carry `here_by: null` and
   say that a later day bounds nothing at the scene.
6. A KIN role is not taken from T-1320. Eight of the crosswalk's 22 merges name a father,
   mother, spouse or subject — a tie between two cards, which is another open ticket's unit
   — and this pass writes none of them.
7. The other 83 units are REFUSED IN WRITING under a named rule with its own reopen
   condition, not deferred a fifth time: four new rules in
   `tools/spend_remainder_rulings.py` for the 82 register units (nobody this town holds, 40;
   refused in the crosswalk, 26; a candidate and not a merge, 10; a reading about the town,
   6), and `the_1830_surname_variant_is_a_candidate_and_not_a_merge` turned from a hand-off
   into a refusal for the one 1830 variant row.
8. The rules that used to hand these units on are GONE where their units are now spent —
   `the_1830_line_bounds_a_held_residents_presence` is deleted and `census_rule` returns no
   rule for a matched line — because a ruling on a unit something else closed reads as work
   done and is not. Each generator's self-test refuses a rule that never fires.
9. `a_dated_appearance_bounds_a_presence` is repointed from the split T-1329 to T-1331 and
   restated as the PRESS alone.
10. No grade moves, no identity is reopened, no person is minted, and the applier changes
    exactly one key — asserted by `tools/spend_appearance_bounds.py --self-test`.
11. A card receives a citation and not a transcription. Copying a merge rule verbatim
    imports every claim in its prose into the residents corpus, which
    `tools/survey_stated_kin.py` caught as three unruled kin statements; the row names the
    crosswalk, both spellings and the resident merged into, and the rule stays where it was
    authored.

**Verification:** `tools/spend_appearance_bounds.py --self-test` (24 checks) and `--check`;
`tools/spend_name_on_a_roll_rulings.py --self-test`; `tools/spend_remainder_rulings.py
--self-test`; `tools/measure_research_spend.py --check`; `tools/check.sh` whole; the smoke
parts `tools/smoke_budget.mjs --for-diff` names.
