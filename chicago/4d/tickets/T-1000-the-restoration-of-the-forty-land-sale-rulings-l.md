---
id: T-1000
title: The restoration of the forty land-sale rulings landed with no changelog entry and no README itemisation: twelve visitor-facing cards changed and nothing says so
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-10
closed: 2026-09-10
pr: 1075
claimed_by: run 9/10/2026, 10:13:15 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-10T15:33:32.994Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34488504741
---

The restoration of the forty land-sale rulings landed with no changelog entry and no
README itemisation: twelve visitor-facing cards changed and nothing says so.

**#1073 was a good fix that told nobody.** It restored the forty rulings #1055 dropped
and re-ran the spend, which retracted a federal land purchase and a source line from
twelve resident cards — Hartzell, Vanderbogert, Wessencraft, Hale, Spence, Chandler,
Kingston, Minard, Garrett, Goodrich, Smith, Morrison. Those cards are what a visitor
reads in the inspection panel, so this is a change to what the town says about twelve of
its people. It shipped with:

- **no entry in `renderers/web/js/changelog.js`.** The fleet changelog contract asks for
  one on any user-visible change, and the What's-new tab is where this project explains
  itself. Every other pass in this domain has one — v686 for cohort A, v690 for the firm
  rule — so the record reads as though the fourteen were judged, the firms were split
  out, and nothing ever went wrong in between.
- **no itemisation in `data/research/land_sales/README.md`**, which carries a section per
  ruling pass (T-0700, T-0850, T-0851, cohort A) with what moved and by how much. The
  incident that reverted three of those passes is the one thing the file does not
  mention.

An undocumented repair is how the same fault gets rediscovered: the run that found this
one found it by reading T-0990's cohort log against the crosswalk and noticing they
disagreed. The next run to open that README would have had the same puzzle and no answer.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- a fleet-format changelog entry, authored `v: null, ts: '', date: ''` and stamped with
  `tools/stamp-changelog.mjs`, that says plainly what came off the twelve cards and that
  nothing was upgraded or minted;
- a section in `data/research/land_sales/README.md` in the shape the other passes use:
  what happened, the before/reverted/restored counts, and what it cost;
- both numbers CHECKED against the tree rather than repeated from a commit message —
  the run that filed this found two of #1055's figures misremembered on its first pass;
- the gate gap is NAMED and pointed at its own ticket rather than fixed here: a check
  that can see a ruling that is simply gone is T-0999, and it is more than this unit.

**Deliberately not in scope:** the restoration itself, which #1073 already did, and the
gate, which is T-0999.
