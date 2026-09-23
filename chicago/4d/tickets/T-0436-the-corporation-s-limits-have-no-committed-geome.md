---
id: T-0436
title: The corporation's limits have no committed geometry, and the fire ordinance binds only inside them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-30
closed: 2026-09-13
pr: 1238
claimed_by: run 9/13/2026, 2:13:16 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T07:51:41.116Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34744481248
---

The corporation's limits have no committed geometry, and the fire ordinance binds only
inside them.

**Raised by T-0333.** Section 18 of the Trustees' ordinance of 5 August 1835
(`chicago_democrat_1835_08_19` c005) requires eighteen inches of stack above a roof "within
the limits of the Corporation". T-0333 gated that constraint over the WHOLE drawn town, and
it was able to do so only because it measured the town's extent and found every chimneyed
building whole platted tiers inside any reading of the boundary — not because the boundary
exists in this repository. It does not.

**What is actually held.** One prose note, on `chicagology_prefire278`: limits fixed
6 November 1833 at Jackson south, Jefferson and Cook west, Ohio north, "barely
seven-eighths of a square mile", extended 11 February 1835 east to the lake shore and out
to Chicago Avenue and Twelfth Street. That record's own note grades the incorporation half
of the page **rung 3, not 2**, and says in terms that no value in the dataset rests on it —
so it cannot carry a committed boundary on its own.

**Why it will matter.** Two ordinances in this corpus are bounded by a line and neither can
be tested without one: section 18's eighteen inches, and section 22's hay-stacking
boundary, which is a DIFFERENT and narrower line ([[T-0334]]) — a point worth stating
plainly, because section 22 is sometimes read as describing the corporation limits and it
does not. And the moment the reconstruction reaches a building outside the limits, T-0333's
gate silently starts conforming a farmhouse to a by-law that never bound it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Either the limits are committed as geometry, sourced at the tier the evidence actually
  carries — which means finding the incorporation record or the 11 February 1835 act in
  something better than a compilation page, since `chicagology_prefire278` cannot carry it
  — or the search is recorded as a negative finding with what was looked for and where.
- If committed, `tools/measure_stack_projection.py` reads it instead of arguing from
  extent, and reports the inside/outside split for real.
- No confidence anywhere is graded off the compilation page.

Links: [[T-0333]] (the gate that needs it), [[T-0334]] (the hay line, which is not this).
