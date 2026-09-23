---
id: T-0257
title: An extraction schema, and the gazetteer the papers compile into
state: done
epic: PAPERS
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 460
claimed_by: run 8/28/2026, 6:48:23 AM CT
blocked_on: T-0256
needs_bake: false
---
T-0256 made the corpus citable. This ticket builds the two structures every
extraction pass writes into, and the gate that keeps them honest. No mass
extraction happens here — the deliverable is the schema, the compiler, and a
worked fixture from ONE issue.

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


## The shape

1. **Per-issue extraction files** — `data/research/newspapers/extracted/
   <issue_id>.json`, one per issue, holding `claims[]`. A claim:
   - `kind`: `person | business | building | street | infrastructure | event |
     shipping | price | notice`
   - `quote`: verbatim text INCLUDING the transcription's uncertainty brackets —
     never silently smoothed
   - `normalized`: the reading after OCR judgment (interleaved columns
     unshuffled, `rn/m`-class confusions corrected), ALWAYS beside the quote,
     never replacing it
   - `locator`: issue page, column, text-file line range — per T-0256's
     convention
   - `entities[]`: names as printed plus a normalization guess
   - `ad_copy_date`: the ad's own dateline where present (e.g. `Chicago, Nov. 3,
     1834.-49`) — the date the copy was placed, NOT the issue date; this is what
     evidence windows are built from
   - `reading: transcription_mediated` (ruling 2), carried structurally so no
     claim can omit it
2. **The gazetteer** — `data/research/newspapers/gazetteer.json`, compiled by
   `tools/compile_gazetteer.py` from `extracted/*`, never hand-edited:
   - `persons`: id, name variants with the claim each came from, mentions[],
     first/last seen, `letter_list_only` (ruling 1), occupations, associated
     places
   - `businesses`: id, proprietors, trade, goods, street, `placement` —
     `class: corner | relative | street_only | none` with the anchor's name and
     the offset text verbatim ("a few doors below Messrs. Newberry and Dole's"),
     evidence window (first/last ad), `contradicted_by` (dissolution/removal
     notices — ruling 3's only veto)
3. **Identity policy**, enforced by the compiler: same surname + different
   initials NEVER merge silently; an OCR-variant merge (Hogan/Hoga, Cohen/Cohn)
   requires a stated `merge_rule` on the entry naming both spellings and the
   judgment. An unexplained merge is a compile error.
4. **The gate**, in check.sh: every claim's locator resolves against
   `corpus.json`; every gazetteer entry has ≥1 mention; the compile is
   deterministic; a claim without `quote`, `locator` or `reading` is refused.

## The fixture that proves it

Hand-extract from **Chicago_Democrat_1835-07-01** (the scene-date issue): Peter
Cohen (dry goods, groceries, clothing, liquors, "a few doors below Messrs.
Newberry and Dole's ... on south water street", ad dated Nov 3 1834 —
placement class `relative`, anchor Newberry & Dole), J. S. C. Hogan ("in South
Water Street, one [door from] the Post Office" — `relative`, anchor the post
office), and at least one letter-list person marked `letter_list_only`. These
three exercise every field including the uncertainty and interleave judgments.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The fixture compiles into a gazetteer whose Cohen entry carries the verbatim
  offset text and the Newberry & Dole anchor.
- Negative fixtures FAIL, demonstrated: a claim with no locator; a silent
  cross-initial merge; a hand-edit to gazetteer.json (the compiler's output
  hash, or regeneration diff, catches it).
- The compile is deterministic — run twice, byte-identical.
- check.sh green with the gate wired.
