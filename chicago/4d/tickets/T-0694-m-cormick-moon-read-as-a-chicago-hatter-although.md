---
id: T-0694
title: M'Cormick & Moon read as a Chicago hatter although their own notice gives No. 109 Jefferson Avenue, Detroit
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 973
claimed_by: run 9/6/2026, 3:02:50 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T08:41:37.567Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34020625245
---

M'Cormick & Moon read as a Chicago hatter although their own notice gives No. 109 Jefferson Avenue, Detroit.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)
T-0661 gave the residents vocabulary the word `hatter` and the needle that reaches it.
The FIRM record for M'Cormick & Moon is refused on its own printed phrase — "hat
manufacturers and wholesale dealers, Detroit" is in `T0661_NOT_IN_VOCABULARY` — but the
gazetteer also holds them as a PERSON whose occupation is printed plainly as "hatter",
and the person tables give them the word. Their notice of 2 July 1834 gives their house
as No. 109 Jefferson Avenue, Detroit.

Nothing moved when T-0661 landed: their register action is `new_resident` and was
`new_resident` before it, because Ruling 1 turns on the town not holding the name, not
on the trade. The risk is downstream — a mint pass reading occupations alone could raise
a hatter's shop on the plat for a Detroit house.

**Acceptance:** either the person record carries the Detroit place the firm record
carries, so the mint's placement refusal reaches it, or the phrase is refused at the
person level with the reason written into
`docs/RESEARCH/occupation_vocabulary_1835.md`; and a re-derived `register_1835.json`
shows the outcome. Check the same shape for every other out-of-town house the papers
advertise for.
