---
id: T-0605
title: The 1830 schedule's district runs on past leaf n584 and those leaves are unread: finish Peoria & Putnam & territory attached
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 853
claimed_by: run 9/4/2026, 11:59:47 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T05:29:19.564Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33945835931
---

The 1830 schedule's district runs on past leaf n584 and those leaves are unread: finish Peoria & Putnam & territory attached.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Where T-0498 stopped.** It read leaves n580 and n582 of NARA M19 reel 24 as the Internet
Archive republishes it (`populationsc18300024unit`, 620 leaves, no text layer) — 67 heads of
family in the enumeration district headed *Peoria & Putnam Counties & Territory attached*, which
is where Chicago was enumerated in 1830. See `data/research/census_1830/` and the source record
`data/sources/census_1830_peoria_county_chicago_precinct.json`.

**What is left.** The district continues on leaf n584 with the county cell left empty — Reuben
Flagg, John Cooper, Timothy B Clark, Pierce Hawley, Bailey Hobson, Jacob Kite, the Groves,
Matthias Trumbo, James McCarty — which is the Du Page and Fox River settlement rather than the
mouth of the river. Its county column was looked at only far enough to establish that the
district had not ended; nothing on it was read. Read on until the heading changes, and declare
each leaf in `coverage.json` as it is read.

**How.** Fetch the leaf as `https://archive.org/download/populationsc18300024unit/page/n<N>_w2400.jpg`,
crop the names column and read it. Append to `text/peoria_putnam_1830_leaves_580_582.txt` (or a
sibling file per range) and re-run `tools/read_census_1830.py --build`, which regenerates the
records and the resident crosswalk. The per-household age-band cells are still unread for
n580/n582 as well and are a separate pass, not this one.

**Acceptance.** Every remaining leaf of the district read head by head, coverage declared leaf by
leaf, the crosswalk regenerated, and the point where the district ends stated with the leaf number
that proves it. `tools/research_domains.py --check` and `tools/read_census_1830.py --check` green.
Nothing minted — the ladder is T-0513's.
