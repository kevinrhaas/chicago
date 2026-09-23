---
id: T-0822
title: The synthesis programme demotes seventeen letter-list people the ladder graded attested, so running its own tool reverts T-0515 and T-0699
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 918
claimed_by: run 9/5/2026, 3:18:11 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T20:49:11.090Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33989566882
---

The synthesis programme demotes seventeen letter-list people the ladder graded attested, so
running its own tool reverts T-0515 and T-0699.

Found by T-0508 and again by its follow-up run, both times by running the programme's own tool.

`tools/synthesize_resident_research.py` is the programme's authority for grading a
`letter_list_only` person: with no research row the person is `inferred` and carries
`resident_subtype: projected_resident`; with a corroborated row the person is `attested`.
Seventeen people on dev today are `letter_list_only`, carry NO research row, and are graded
`attested` anyway — albert_shepherd, ambrose_joshua, barry_john_s, bradford_harriet,
brooks_gardner, chapman_chas_h, cole_parker_m, crawford_james, fitzgerald_thos, lee_george,
mack_stephen, matthews_james_g, murray_alonzo, neff_r_a, rogers_edward_a, simons_e and
winson_wm. T-0515 and T-0699's ladder put them there.

Each of them still carries the note the synthesis wrote: *"PROJECTED RESIDENT. Documented in
Chicago post-office evidence but not independently corroborated strongly enough for attested
circa-1835 residence."* The grade and the note on one card say opposite things, and a reader
gets whichever the card shows them first.

**Running the synthesizer demotes all seventeen back to `inferred` and re-flags sixty-five
people as `projected_resident`**, on fifty-nine cards that have nothing to do with whatever
cohort is being run. So every cohort ticket in this programme has to notice the reversion and
undo it by hand before it can merge, which is a trap and not a workflow: T-0508 restored the
seventeen and re-derived `data/residents/index.json` from the restored cards to get its own
PR back to no-grade-movement.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

One rule wins and the other is written down as beaten. Either the ladder's convergence rung
supersedes the synthesis programme's letter-list rule for these people — in which case
`synthesize_resident_research.py` stops demoting a person the ladder has ruled on, and says
so — or the synthesis rule stands and the seventeen go back to `inferred`. Whichever way it
goes, the note is rewritten to agree with the grade on all seventeen cards, and running
`tools/synthesize_resident_research.py` twice in a row on a clean checkout moves nothing.

**Links:** T-0515 · T-0699 · T-0508 (which hit it) · T-0509 and T-0510, the two cohorts that
will hit it next.
