---
id: T-0741
title: The 1840 census images 51-74: inventory all 24 sheets — sheet side, printed page and lines with an entry
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0496
opened: 2026-09-05
closed: 2026-09-05
pr: 855
claimed_by: run 9/5/2026, 1:39:44 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T07:15:38.226Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33950186427
---

The 1840 census images 51-74: inventory all 24 sheets — sheet side, printed page and lines with an entry.

Piece 1 of 2 of **T-0496 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 51-75**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `data/research/census_1840/coverage.json` gains **group 3, images 51-74** — 24 of 24
  images declared, in the deposit's own sorted order with the duplicate copy already
  removed, each carrying `index`, `familysearch_id`, `file`, `sheet_side`,
  `printed_page` (or `null`, never guessed), `lines_with_an_entry`, `what_it_is`,
  `in_pr_670_calibration_set` and `read_state`.
- The group's `counts` block is **recomputed from the images array**, not incremented:
  images, left sheets, right sheets, left sheets with entries, blank or cancelled, the
  printed page numbers read, and how many are `inventoried_only`.
- `line_counts_are` states HOW the counts were taken and at what magnification, so the
  transcribing piece knows what standing they have. The group-1 and group-2 inventories
  read long by one to four lines; that finding is carried forward, not re-discovered.
- Which of PR #670's seven calibration pages (229-235) fall in this group is **settled by
  reading the sheets**, not assumed: the corrected coverage note expects 233 and 235 here
  and the inventory either finds them or says where they are not.
- A printed page number that the scan does not carry legibly is `null` with the reason on
  the image entry. A number recovered from the run of its neighbours is an inference
  wearing a reading's clothes and is not written.
- No names, no cells, no serials, no residents minted — those are T-0746's and T-0504's.
- `tools/check.sh` green and `research_domains.py --check` green on the domain.

**Why this piece first.** Group 3 is the only one of the three the deposit declaration
does not describe at all: `coverage.json` carries two groups and `schema_note` promises
three. Until the 24 sheets are named — which is a left sheet, which a continuation, what
printed page each carries — the transcribing work cannot be parcelled by printed page the
way T-0495's was, and a hole in the deposit cannot fail.
