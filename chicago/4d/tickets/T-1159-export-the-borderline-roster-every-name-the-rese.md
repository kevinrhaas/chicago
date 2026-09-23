---
id: T-1159
title: Export the borderline roster: every name the research read and withheld from 1835 — single-source, refused, surname-only, uncertain presence, letter-list-only — with its source, reason and re-admission class, so reconstruction can name real people before it invents any
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-17
pr: 1428
claimed_by: run 9/17/2026, 8:09:29 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T01:52:39.579Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35293945922
---

The owner, 2026-09-17: *"You may use research that was borderline in naming and give them a real
human name … like there was research that you had that may have only been one source not a few
so you marked them out, but now is the time to dip back into that and fill out the population."*

The research spend was, correctly, conservative: the T-1143 ledger holds 7,329 `refused`,
11,880 `later_only`, 63 `outside_chicago` and 32 `aggregate_only` units, and the resident layer
carries 893 households `uncertain` on 1 July 1835 and 736 `letter_list_only`. Those refusals are
NOT overturned here — a refusal was a ruling about EVIDENCE, and it stands. What changes is that
a name the corpus printed is a better reconstructed resident than a name drawn from a pool, so
the reconstruction band must be offered the corpus's own names first, with each one's evidence
limit stated. This ticket builds that offer as a generated roster; it mints nobody.

**The roster** — `data/reconstruction/1835_borderline_roster.json`, built by
`tools/export_borderline_roster.py --build|--check`, one row per candidate, fields: `name_as_read`,
`normalised`, `source_id`, `claim_or_record_id`, `describes_date`, `domain`, `ledger_disposition`,
`ledger_reason`, `existing_household_id` (if a card exists), `presence_today`, and the
**re-admission class**:

| class | who | what reconstruction may do |
|---|---|---|
| `R1_in_window_uncertain` | a card exists, in-window source, presence `uncertain` (the 893) | fix presence `present` at tier `reconstructed`, basis = the dated appearance + the model's persistence rate |
| `R2_in_window_single_source` | one 1833–35 appearance, no card, ledger `refused: single source` / `insufficient_identity` | mint a reconstructed resident under the read name |
| `R3_1834_return_or_muster` | the 1 April 1834 return (T-1153) / 1832 muster names with no 1835 corroboration | mint reconstructed, presence bounded by the persistence rate |
| `R4_surname_only_census` | 1830 census surname-only refusals (25) and 1840 heads whose surname matches an 1835 household | may supply a FAMILY (spouse/child bands) to an existing head at `reconstructed`, never a new head |
| `R5_later_only_backprojectable` | 1839 directory / 1840 census / Fergus 1843 names whose own biography or a second source puts arrival before 1835-07-01 | mint reconstructed with arrival at the biography's date; else NOT eligible |
| `R6_native_metis_black` | a Native, Métis or free Black person any source names in or near the town in window (the treaty schedules, the registers, the traders' lists, the 1833 freedom certificates) — whatever its ledger disposition | mint at the ladder's grade where the evidence allows, else `reconstructed`; always `review_required` for Native/Métis; `community` set; owned by T-1177 |
| `R0_ineligible` | outside Chicago, Bear Creek couples (T-1129), explicit `researched_not_resident`, post-scene arrivals | never |

Every row states which rule put it in its class and the ledger row it came from. The roster is
sized against the ledger: every `refused`/`unresolved`/`later_only` unit that names a person is
either in a class or listed under `not_a_person_unit` with the reason — no unit is silently
dropped.

**Acceptance:**

- The roster builds, re-derives byte-for-byte under `--check` in `check.sh`, and prints counts
  per class per domain; a `docs/RESEARCH/borderline-roster-2026-09.md` review page shows the
  counts and twenty worked examples (five per class R1–R4, with the reason each was withheld).
- No card, grade, presence or ledger row changes in this ticket.
- The 10 `researched_not_resident` names are R0 and the tool proves it with a self-test; every
  `review_required` / `touches_removal` household's named-but-uncarded kin are R6.
- The 1840 IPUMS household extract is used for R4 only as a SHAPE (age bands) attached to a
  head that 1835 evidence already carries — the T-0507 line stands: *1840 household members
  are never minted into 1835 solely from census counts.*

**Stop condition:** reconstruction can read one file to learn every real name the sources offer
below the inferred bar, and what each name licenses.

**Links:** T-1143 · T-1146 · T-1153 · T-1129 · T-0507 · T-1027 (the one-letter pairs stay its own
question — rows it owns are `unresolved:T-1027`, class R0 until it rules) ·
`docs/RESEARCH/resident-grading-policy.md`.

## WHAT SHIPPED (PR #1428)

`tools/export_borderline_roster.py` builds `data/reconstruction/1835_borderline_roster.json`
and `docs/RESEARCH/borderline-roster-2026-09.md`; `--check` and a self-test are wired into
`tools/check.sh`. 1,634 offered rows — R1 814, R4 424, R2 182, R6 129, R5 55, R3 30 — plus
13,564 named refusals and 9,239 units naming no person, so the accounting rule ("no unit
silently dropped") is a checked identity rather than a claim. No card, grade, presence or
ledger disposition changed.

**THE HAND-OFF MOVED, AND THAT IS THE ONLY LEDGER EDIT.** 40 Cook-residence land-sale
purchaser units were deferred to THIS ticket to be CARRIED. They are carried (class R2), so
`tools/spend_land_sales_rulings.py` now names **T-1172** — the ticket that re-admits the
roster's single-source names. This is what that register's own doc asks for: a hand-off names
the OPEN ticket whose field owns the finding, and that ticket closing turns the file red.
Without it, closing this ticket would have stranded all 40 behind finished work, which is
exactly the refusal T-1144 and T-1241 recorded when somebody tried to fold them away.

**TWO JUDGEMENTS THE NEXT READER SHOULD KNOW.** R6 is a RECALL rule, not a verdict — a
declared term list over the reading's own words, so thin evidence never becomes the reason a
community goes unbuilt; its first version read `Indian agent` as a description of the man
holding the office and put Jouett, Forsyth and Irwin through as Native people, so the office
phrases are struck out before the terms are read and every row names its matched term. And a
`touches_removal` flag is a REVIEW REQUIREMENT, not an ineligibility: the eight flagged
households stay on the roster carrying `review_required`.

**ACCEPTANCE 3, HONESTLY.** The rule for kin a flagged household names and no card carries is
implemented and checked; it finds 0 today because every structured `kin` row on those eight
resolves to a held household. It cannot reach a person named only in prose —
Mah-naw-bun-no-quah is the case the tree states in as many words — and the review page names
that gap rather than pretending at it.
