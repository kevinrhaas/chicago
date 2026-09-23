---
id: T-0535
title: The 1840 census images 1-25: the eleven continuation sheets, paired to their left sheets by printed page
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0494
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: run 9/3/2026, 5:41:23 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 1-25: the eleven continuation sheets, paired to their left sheets by printed page.

Piece 5 of 5 of **T-0494 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 1-25**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**What the parent pass already did, so this ticket does not redo it.** T-0494's run declared all 25
images of group 1 in `data/research/census_1840/coverage.json` (kind, printed page, line count),
transcribed the NAMES of the three pages PR #670 also read (229, 231, 234), read printed page 206 —
the certificate and recapitulation sheet — in full, declared the blank page 238, and corrected the
deposit count to 74 distinct images in 75 files. Read that coverage group and
`data/research/census_1840/README.md` first; the inventory line counts there are stated to the
nearest line and this ticket restates its own pages exactly.

**The rules, unchanged from the parent.** `as_read` preserves position — an unread letter is `[?]`,
never an absence (T-0397). `normalized` expands the abbreviation and keeps the `[?]`.
`name_confidence` is `high | medium | low` and is about the LETTERS. `reading: scan_verified`.
Enumeration order is data: never reorder lines, and record a blank or illegible line rather than
skipping it. No IPUMS serial is attached here — T-0504 does that. Nothing here mints or regrades an
1835 resident: the 1840 census is LATER EVIDENCE and the owner's ratified ladder is explicit that
"1839/1840 alone is never a 1835 resident". Do not commit images or crops; the deposit is read-only.
Town findings — any business, street, landscape or appearance fact — go in
`data/research/census_1840/claims.json` with `town_finding: true`, verbatim quote and locator.

- The eleven continuation images of group 1 — 33S7-9YYJ-24, -5D, -5S, -5V, -6H, -6Q, -8D, -9WS, -B1,
  -B2, -BF — each get a `pages/<id>.json` with one record per ruled line: slaves, the family TOTAL,
  the six industry columns, pensioners, deaf/dumb/blind, and the schools and illiteracy columns.
- A continuation sheet carries no name and no printed page number of its own, so the PAIRING to its
  left sheet is the deliverable: state the printed page each one continues and the evidence for it
  (line count, the TOTAL column against the left sheet's age-band sums, the schools figures). An
  unpaired sheet is recorded as unpaired, never guessed.
- Watch for the shape T-0529 found in group 2: a continuation sheet whose TOTAL column carries
  three-figure numbers is not a household page. If one of these eleven is that, say so and stop.
- Coverage group 1's `read_state` and `page_file` updated for these eleven images.

**Links:** `data/research/census_1840/README.md` · `coverage.json` group `images 1-25 of 74` ·
`crosswalk_670.json` · `claims.json` · T-0492 (the shared research-domain shape) · T-0504 (serial
mapping) · T-0505 (crosswalk to 1835) · T-0507 (composition calibration) ·
`data/sources/census_1840_chicago_familysearch_images.json`
