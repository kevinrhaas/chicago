---
id: T-1103
title: Kinzie's Addition's block numerals 1 and 2 land on no cell inside the plat, and the water lots did not take them
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-13
pr: 1232
claimed_by: run 9/13/2026, 12:28:25 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T06:23:59.485Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34740265829
---

Kinzie's Addition's block numerals 1 and 2 land on no cell inside the plat, and the water lots did not take them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Where this came from.** T-1061 read the Addition's block numerals cell by cell and found
fifty-one figures over fifty-two cells with the run's first two numbers landing on nothing:
the boustrophedon puts 1 and 2 west of block 3 on the river tier, beyond the Addition's west
boundary rule at NA x 2918, where Wright draws the Original Town's north division instead.
It refused them in writing rather than counting them onto a cell, and handed the question to
T-1063, which owned the river tier and the water lots.

**What T-1063 could answer, and what it could not.** It could rule the water lots OUT. The
strip is one continuous run of thirty-five figures along a single axis, with its terminal 1
and 35 both legible (`data/traces/kinzie_addition_water_lots.json`); that is a lot strip's
own series and it cannot be a two-block remainder. So blocks 1 and 2 were not taken by the
water lots. Where they ARE is untouched, and it is what this ticket is for.

**The two readings to test.**

1. They stand west of the Addition's boundary rule, on ground this sheet letters to another
   survey — the two eight-lot blocks carrying bold 1 and 2 across their mid-lines at NA
   x 2610-2930, y 2140-2320. If so the Addition's numbering starts at 3 by construction and
   the boundary rule at x 2918 is in the wrong place, or the legend's tract colouring is.
2. The numbering skips them, as this project's Original Town numbering skips nothing but its
   School Section run does not. A plat that reserves two numbers and plats neither is not
   unheard of on a private addition that sold ground before it was recorded.

**What would settle it:** a recorded plat of Kinzie's Addition, or a Chicago Democrat notice
selling a lot in its block 1 or 2 with a street named beside it — the newspaper corpus is
transcribed and searchable, and `data/research/newspapers/` is where to look first. Do not
adjudicate this off the raster alone: T-1061 already established the raster refuses it.
