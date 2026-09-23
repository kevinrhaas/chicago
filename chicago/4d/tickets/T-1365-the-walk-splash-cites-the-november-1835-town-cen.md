---
id: T-1365
title: The walk splash cites the November 1835 town census as the 1 July population: 1,588 cards read against 3,265, where the source file says that number is never the scene's population and only 457 of the cards are present
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-18
closed: 2026-09-19
pr: 1510
claimed_by: run 9/19/2026, 3:50:48 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T10:15:38.160Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35432948183
---

The walk splash cites the November 1835 town census as the 1 July population: 1,588 cards read against 3,265, where the source file says that number is never the scene's population and only 457 of the cards are present.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Read T-0782 first; this is not a typo and the bar is not thoughtless.** `renderers/web/js/
census.js` says why it is built as it is: the card had three stacked figures telling three
unrelated stories, worst of all `29 people housed · of roughly 3,265`, which set a PLACEMENT
figure against the whole population and announced the town as 0.9 % peopled. T-0782 made it
"one ladder, twice" — roofs standing of roofs held, then named residents of the census total,
graded attested → inferred → reconstructed. That was right, and the ladder should survive
whatever this ticket does.

**What has drifted since.** The reconstruction programme was built after T-0782 and picked a
DIFFERENT denominator for the same quantity, so the front screen and the programme now fill
toward two different numbers:

| figure | value | what it is |
|---|---|---|
| the splash's denominator | **3,265** | Andreas's town census of NOVEMBER 1835 |
| the order book's `persons_target` | **2,535** | the programme's point figure for 1 JULY 1835 |
| the stated range for 1 July | **2,350 – 3,265** | changelog: 3,265 is the range's HIGH END |

`data/town_census.json` carries the rule in its own `town_total_note`: the November count is
"Quoted as the town's recorded size, **never as the scene's population on 1 July**." The splash
renders it as `of roughly 3,265 who lived here`, which is that use. And the changelog's own
reasoning is that 3,265 is an upper BOUND — "a town that was growing all year was no larger in
July than it was in the autumn" — while `method.point_from_range` in the order book is where the
project drew 2,535 out of that range. So the screen fills a bar toward a bound the programme has
already resolved to a point.

**And the numerator counts a different population from the denominator.** The bar reads 1,588
named residents, which is every card in `data/residents/index.json` regardless of whether the
person is established as being in Chicago on the scene date. The order book's `known_layer` says
`persons_total: 1588` but `persons_present: 457`. So 1,131 of the 1,588 are cards the project has
NOT placed in the town on 1 July, counted against a total of who was in the town. That is the
same category error T-0782 fixed one row down, arrived at from the other direction.

1. The front screen's denominator and the reconstruction programme's are the SAME number, or the
   screen says in its own words why they differ. Two figures for "how many people were in this
   town on 1 July 1835", rendered side by side in one product, is the defect — pick one, or
   label both.
2. The numerator and the denominator count the same population. Either the bar reads the 457
   established present against the model's figure, or it keeps all 1,588 cards and says that is
   what it is — a count of CARDS, not of people in the town that day. A caption that says "who
   lived here" under a number that includes people not established as living here is the thing
   to fix.
3. T-0782's ladder survives. One ladder twice, graded in three portions; `people housed` stays a
   placement note and is never quoted against the population. Undoing T-0782 to fix this is a
   fault of this ticket.
4. The rule in `town_census.json` is honoured or CHANGED IN WRITING. If 3,265 is the right
   denominator after all, the note that forbids it is what is wrong and it gets rewritten with
   the argument; what must not stand is code and data disagreeing in the tree.
5. Whatever is chosen holds on the dev preview at both viewports, and the numbers still come
   from the files — T-0036's rule, never hand-typed.

**NOT IN SCOPE: converging the layer against the model.** That is T-1179, which owns the town
census screen's final form in its acceptance 3, and it comes at the end of the resident band.
This ticket is the interim correctness fix for a screen that is live now and will keep asserting
a wrong denominator until T-1179 lands. Whoever works T-1179 should read this one and may fold
it in.
