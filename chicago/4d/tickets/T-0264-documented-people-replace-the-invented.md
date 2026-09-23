---
id: T-0264
title: Documented people replace the invented
state: split
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: null
claimed_by: run 8/29/2026, 2:53:48 AM CT
blocked_on: T-0262
needs_bake: false
---
**VISIBLE.** The town's invented residents (K18 names, K20 measured) exist
because no documented person was available. Now hundreds are. This ticket
retires invented people in favour of documented ones, per the register's
`replace_invented` and `new_resident` actions.

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

- **Replacement**: where the register matched a documented person to an
  invented resident (trade, street, household shape), the documented person
  takes the roof: name, occupation, citation; `name_basis` (the invented-name
  pool citation) is REPLACED by the newspaper citation; the household keeps its
  structure. The card shows a real person with a real source where it showed an
  invention.
- **New residents** (ruling 1): letter-list persons mint residents. Prefer
  richer-evidenced people (ad, notice, proceedings) for named-trade roofs;
  letter-list-only names fill household slots as documented heads with
  `letter_list_only` carried onto the record, occupation absent rather than
  invented.
- **The K20 metric is the deliverable measured**: the invented-person count
  (last read 12 of 110-class carried-over invented persons at T-A15-era
  measurements — read the CURRENT number first) falls, and the PR states
  before → after from `tools/measure_name_churn.py` or the census's own count.
- `town_census.json` totals move additively where new residents land; no
  household loses members silently; grades and `sources` arrays per attribute,
  the household schema already carries them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The invented-person count falls, stated before → after with the instrument
  named; zero invented names remain on roofs the register matched.
- Every replaced or minted resident's card carries the newspaper citation;
  letter-list-only residents carry the flag.
- No household silently loses a member (assert set-wise, the T-0188 queue
  lesson applied to people); check.sh green; changelog entry for the visitor —
  the town's people are becoming real.
