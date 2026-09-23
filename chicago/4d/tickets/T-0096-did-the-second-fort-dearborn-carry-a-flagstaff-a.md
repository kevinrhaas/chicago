---
id: T-0096
title: Did the second Fort Dearborn carry a flagstaff, and can anything but a retrospective plate say so
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-18
closed: 2026-08-28
pr: 447
claimed_by: run 8/28/2026, 2:47:39 AM CT
blocked_on: null
needs_bake: false
---

Did the second Fort Dearborn carry a flagstaff, and can anything but a retrospective plate say so.

Raised and deliberately REFUSED by T-0044's image-accuracy pass, which is why it is a ticket rather
than a building. `p4_0` draws a flagstaff with the flag flying over the fort, and it is the most
conspicuous single feature of that plate. But `data/exclusions.json` already excludes a flagstaff:
the one in the parade belongs to Captain Whistler's 1808 FIRST fort, in the passage that ends *"Such
was the old Fort previous to 1812"*, and the entry closes *"none of it may be borrowed for the second
fort's records"*. Retrospective plates conflate the two forts — the courthouse plate in the same
directory is filed as a negative reference for exactly this reason — so a tier-5 view cannot settle
it, and raising it on that plate alone would be the commonest error in the popular literature
committed on purpose.

What could settle it: a garrison return or quartermaster's account of the 1816 post; Andreas on the
rebuilt fort specifically; the 1830 Harrison plan re-read for a staff; or an identification of this
plate against chicagology's numbering that dates what it claims to show.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Either evidence that reaches the second fort is found and cited, and the staff is built at the tier
that evidence earns — or the search is recorded as a negative finding in
`docs/RESEARCH/fort_dearborn.md` with what was looked at, the way `quaife_1913` records its own.

**The plate half is now measured (T-0197, 2026-08-28), and it does not answer this ticket —
it sharpens it.** `tools/measure_fort_ways_plate.py` puts `p4_0`'s staff at **0.495 of the
drawn wall run**, truck at row 158, rising 15.2–18.8 m over the picket head, with the flag
at rows 195–220 — that is **over the GATE**, between the two roofed lanterned works T-0095
measured at 0.435 and 0.521. `data/exclusions.json` locates the flagstaff it excludes **in
the parade**. So the two are not in the same place, and "the exclusion already covers it"
is not a way to close this. Either the staff, the two towers and the gate work are one
first-fort composition or none of them is, and the sheet cannot say which. The acceptance
below is unchanged: a source that reaches the 1816 post, or a recorded negative finding.
Working in `docs/RESEARCH/fort_dearborn_image_accuracy.md` § "Rows 1, 2 and 6 measured".
