---
id: T-0539
title: The 1840 census images 1-25: the other five continuation sheets — 8D, 9WS, B1, B2 and BF — and the left-sheet population key that pairs all eleven
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0535
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T03:05:38.985Z
claimed_run: null
---

The 1840 census images 1-25: the other five continuation sheets — 8D, 9WS, B1, B2 and BF — and the left-sheet population key that pairs all eleven.

Piece 2 of 2 of **T-0535 — The 1840 census images 1-25: the eleven continuation sheets, paired to their left sheets by printed page**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

Piece 2 takes the five continuation sheets T-0538 did not, on exactly the same basis, and
then does the pairing the parent asked for — for all eleven at once, because the key is a
single reading of the OTHER set of images.

- `33S7-9YYJ-8D`, `-9WS`, `-B1`, `-B2`, `-BF` each get a `pages/<familysearch_id>.json` on
  T-0538's shape: one record per ruled line, and the sheet closed against its own printed
  footer row, with the residual recorded rather than adjusted away if it does not close.
- **The population key.** Each of the twelve filled left sheets of group 1 carries printed
  column totals at its foot: 26 free-white age bands plus the free-coloured columns. Their
  sum is that page's population, and it must equal the TOTAL footer of the continuation that
  belongs to it. Read that footer row for each of the twelve and publish the key.
- **Then pair.** For each of the eleven continuations state the printed page it continues
  and the evidence: the exact line count, the page population, and the schools figures where
  the sheet carries them. Where two candidates share both a line count and a population, say
  so and leave it unpaired — an unpaired sheet is recorded as unpaired, never guessed.
- Watch for the shape T-0529 found in group 2: a continuation sheet whose TOTAL column
  carries three-figure numbers is not a household page. T-0538 found none among its six.
- Coverage group 1's `read_state`, `page_file` and per-image `printed_page` updated.

**The rules, unchanged from the parent.** `reading: scan_verified`; enumeration order is
data; no IPUMS serial here (T-0504); nothing here mints or regrades an 1835 resident; the
deposit is read-only; town findings go to `claims.json` with `town_finding: true`.
