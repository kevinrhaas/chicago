---
id: T-1232
title: Spend matched household and person-profile research into a candidate-fact table, adjudicate every candidate, and write the asserted names, sexes, dates, origins and life events as structured per-value assertions
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1146
opened: 2026-09-17
closed: 2026-09-17
pr: 1390
claimed_by: run 9/17/2026, 5:16:58 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T11:23:38.378Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35208861486
---

Spend matched household and person-profile research into a candidate-fact table, adjudicate every candidate, and write the asserted names, sexes, dates, origins and life events as structured per-value assertions.

Piece 1 of 2 of **T-1146 — Spend matched household and person-profile research into structured relationships, names, sex, dates and life events, with every withheld fact legible**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. A candidate-fact table at `data/residents/person_facts.json`, derived by one generator from
   every `resident_research` block the layer carries. Every row names the person id, household
   id, `name_as_read`, the fact class, the proposed value, the source id, the
   `claim_or_record_id`, the `describes_date` it speaks about, the confidence and the quoted
   sentence it was read from. Nothing about a matched block is left in prose alone.
2. Every row is adjudicated `asserted`, `duplicate`, `contradicted`, `insufficient_identity`,
   `later_only`, `outside_chicago` or `unresolved:<ticket>`, each with a written reason. Every
   research block the layer holds is accounted for: matched blocks by their rows, unmatched
   blocks by a disposition row carrying the T-1159 fields (`name_as_read`, `source_id`,
   `claim_or_record_id`, `describes_date`, `reason`).
3. Asserted values are written into the records as structured per-value assertions —
   `persons[].profile_facts`, each an ordinary graded claim block with its own `field`,
   `describes_date`, `confidence`, `sources`, `record_id` and note. Multiple names and multiple
   dated life events are preserved side by side. **No existing value is overwritten**: a
   household's `arrival` bound stands, and a household-level `origin` or `reason_for_coming` is
   filled only where it is null, the household holds one person, and the fact is that person's.
4. Household membership is not minted. No spouse, child, boarder or servant is created; a
   relationship fact is carried as an assertion about the named person and nothing else.
5. `--check` re-derives the table and the assertions and fails on any drift in either
   direction, so a hand-edited record or a lost row is a red gate. Mutation tests cover the
   adjudication rules: a later-only date, an out-of-town fact, a contradicted candidate and an
   asserted one each prove their own verdict.
6. The resident audit is re-run and the PR reports exact before/after counts for populated
   profile fields. No grade or presence value moves.

**Not this ticket:** the card's rendering of these facts and the ruling on the 83 unread
resident field paths — those are T-1233.

**Links:** T-1146 (parent) · T-0392 · T-0513 · T-1027 · T-1143 · T-1144 · T-1159 · T-1170.
