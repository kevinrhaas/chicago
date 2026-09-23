---
id: T-1084
title: The walkthrough presents walking speed in miles per hour and the smoke has called it red on dev since at least 2026-09-12 08:51, on both viewports
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T16:51:39.090Z
claimed_run: null
---

The walkthrough presents walking speed in miles per hour and the smoke has called it red on dev since at least 2026-09-12 08:51, on both viewports.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

FOUND BY T-1070, 2026-09-12, running the smoke legs that cover a street diff. It is not
that ticket's doing and it is not new: `tools/dev-smoke-state.json` already carries the
same red on dev at **2026-09-12T08:51:52.866Z**, mobile stage 2-3,7-8, on a tree that
predates any of today's branches. T-1070 reproduced it on its own tree at both sizes:

    mobile 390x780:   FAIL  walking speed is presented in miles per hour — speed label walk · 3.2 mph
    desktop 1280x800: FAIL  walking speed is presented in miles per hour — speed label walk · 3.2 mph

Every other check in every leg run passed, so this is one assertion and not a broken part.

**Why it matters more than a units preference.** It is a STANDING dev red on part 7 of the
smoke, which is one of the parts that covers any change to `data/streets/1835.json`. Every
run that touches a street line therefore gets a red leg it has to read, attribute and
argue past before it can merge — T-1070 spent a leg doing exactly that. A gate that is red
for a reason unrelated to the diff in front of it stops being a gate.

**Acceptance:**

1. The assertion and the label agreed, whichever way the argument goes — either the
   walkthrough presents the speed in the unit the assertion expects, or the assertion is
   changed with the reasoning written down. Do not silence it.
2. Both viewports green on part 7 afterwards, filed with `dev-smoke-state.mjs record`.
3. If the unit is a deliberate choice rather than a slip, say so where a reader will find
   it: a walker's speed in a reconstruction of 1835 is a presentation decision, and mph
   against m/s against "a brisk walk" is exactly the kind of thing this project argues in
   writing rather than leaves as a number in a file.
