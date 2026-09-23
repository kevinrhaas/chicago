---
id: T-0262
title: The July 1, 1835 register: who and what the papers put in the town
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: 512
claimed_by: run 8/29/2026, 12:49:10 AM CT
blocked_on: T-0261
needs_bake: false
---
The four reading passes (T-0258, T-0259, T-0260, T-0261 — ALL FOUR must be
closed before this is worked; `blocked_on` can only carry one id, so CHECK THE
LEDGER, and if any is open, work that instead) filled the gazetteer. This
ticket turns it into the town's scene-date register: **who and what stands in
Chicago on July 1, 1835**, and exactly what the seeding tickets build.

## The owner's three rulings, 2026-08-28 — every ticket in this epic works under them

1. **A letter-list name is enough to mint a resident.** The post-office letter
   lists name people by the hundred; the owner ruled a listed name alone makes a
   resident candidate, not merely a gazetteer entry. Record `letter_list_only:
   true` so the two evidence strengths stay distinguishable forever.
2. **Transcription-mediated readings grade `documented`, carrying a flag.** The
   corpus is read through OCR-assisted transcriptions, not the page scans. Every
   claim taken this way carries `reading: transcription_mediated` and preserves
   the transcription's own uncertainty brackets. This EXTENDS, and does not
   overturn, `data/sources/chicago_democrat_1833_11_26.json`'s standard — where
   a scan exists and is read, the scan remains the authority (it caught 'C. & I.
   HARMON' where the transcription had 'C. & L. Harmon'), and a
   transcription-mediated claim upgrades when a scan read confirms it.
3. **A documented business is BUILT at the scene date unless contradicted.** A
   dissolution, removal or replacement notice is the only thing that keeps a
   documented business out of the 1835 town. A business whose last evidence is
   1833-1834 is built WITH a survival liberty stated on the record (existence
   documented, survival to 1835-07-01 assumed) — docs/LIBERTIES.md carries it.


## The work

`tools/compile_register.py` reads the gazetteer and writes
`data/research/newspapers/register_1835.json`, deterministic, gated:

1. **Businesses.** Present at the scene date per ruling 3: everything except
   entries whose `contradicted_by` is set (dissolution/removal before Jul 1) and
   entries whose only 1835 evidence `announces_opening` AFTER Jul 1. Each
   present business carries: placement class; the anchor resolved against the
   COMMITTED town where possible (Newberry & Dole → `dole_warehouse_south`
   exists; the post office is committed; match by trade+street against
   `data/structures/`); a survival-liberty flag when the window ends before
   1835; and an `action`: `enrich_existing` (a committed building already
   carries this business), `new_building` (placeable: corner or relative with a
   committed anchor), `street_only` (documented, placeable only to a face), or
   `unplaceable`.
2. **Persons.** Every gazetteer person becomes: `replace_invented` (matched
   against the invented-resident census — same trade/street/household shape),
   `new_resident` (ruling 1: letter-list names mint candidates), or `enrich`
   (already-documented people gaining occupations/details). Matching against
   `data/residents/` is BY EVIDENCE, and a non-match is fine — the town needs
   more people regardless (the owner: "we will still need a lot more residents
   and buildings, this is all additive").
3. **Counts, stated**: businesses by action and placement class; persons by
   action; how many invented residents the register can retire. These go in the
   PR and STATUS.md — they are the epic's yield measured.
4. **File the remaining seeding tickets** with the register in hand: street/
   infrastructure enrichment onto committed records; the `street_only` and
   `unplaceable` business policy; whatever the register shows that T-0263 and
   T-0264 do not already cover. Real tickets, PAPERS epic, sized from counts.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The register compiles deterministically from the gazetteer; every business
  has a placement class and an action; every `enrich_existing`/`new_building`
  action names its committed target or anchor; every exclusion names its
  contradiction.
- Cohen and Hogan (the T-0257 fixtures) resolve to actions with committed
  anchors, or the register says precisely why not.
- Counts stated; follow-on tickets filed; check.sh green.
