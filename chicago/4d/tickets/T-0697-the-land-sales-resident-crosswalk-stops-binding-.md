---
id: T-0697
title: The land-sales resident crosswalk stops binding when a surname stops being unique: 531 new people cost it three rulings with nothing new read
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 994
claimed_by: run 9/6/2026, 11:15:00 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T17:00:16.434Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34044526103
---

The land-sales resident crosswalk stops binding when a surname stops being unique: 531 new people cost it three rulings with nothing new read.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Reported inside T-0670 and split out of it because it is the opposite failure and a separate fix.
`tools/read_land_sales.py`'s resident crosswalk matches a purchaser only where the residents layer
holds EXACTLY ONE person of the surname and the forename agrees. A bigger town makes that rule fire
LESS: seating 531 people (T-0514) turned nine of its matches ambiguous — Carpenter, Dole,
Fullerton, Haddock twice, Heacock, Sweet, Burdick, Wooley — and made six possible for the first
time — Bronson, Hale, Hartzell, Ludby, Price, Wolcott. A net loss of three rulings with nothing new
read, which is why `land_sales`'s spend ceiling was raised by two in that commit.

**The ask.** The two crosswalk families fail in opposite directions off the same assumption: the
directories bind too readily on an initial (T-0670, fixed) and the land sales stop binding at all
when a surname stops being unique. Both want a second discriminator rather than a count of
namesakes. Decide what the land sales' discriminator is — a purchase date inside the person's own
bounds, a trade, a lot the person is otherwise placed on — and hold it to the same standard T-0696
sets for the directories, so the two rules can be read side by side.

**Links:** T-0670 (where this was found) · T-0696 (the same question on the directory side) ·
T-0514 (the mint) · `tools/read_land_sales.py`.
