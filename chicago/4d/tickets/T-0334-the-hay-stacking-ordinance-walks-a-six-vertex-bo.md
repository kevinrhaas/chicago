---
id: T-0334
title: The hay-stacking ordinance walks a six-vertex boundary round the built town, and nothing draws or tests it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1236
claimed_by: run 9/13/2026, 1:46:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T07:30:23.175Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34743397635
---

Section 22 of the ordinance passed **5 August 1835** makes it unlawful to stack hay inside a
boundary the town walks street by street, read under [[T-0335]]
(`chicago_democrat_1835_08_19.json` c006):

> commencing on Washington street at the United States Reservation, and running thence West
> to the intersection of Canal Street, thence North to the intersection of Kinzie Street,
> thence East to the intersection of Wolcott street, thence to Illinois Street, and thence to
> Lake Michigan

Six vertices, every one of them a street this reconstruction already carries, under a penalty
of twenty-five dollars — the heaviest in the whole ordinance except gaming. It is a fire rule,
and that is exactly what makes it evidence: the Trustees drew this line round the ground they
thought was built up densely enough that a hay stack in it would take the town with it.

**This project has no other documented statement of where the BUILT town ended in the scene
year.** Every judgement about density, about which blocks get roofs and which stay open
ground, has been made from the plat, from the deal, and from measured street frontage. This
is the town's own answer, in the town's own words, six weeks after the scene date.

## What it could be worth

- A polygon in `data/`, derived from committed street control the way `datum.json` is derived,
  never hand-typed — with the ordinance claim as its source record.
- A cross-check on the block-infill programme: does the ground the schedule treats as built
  agree with the ground the Trustees fenced? Where they disagree, which is right?
- Possibly something a visitor can SEE, though what that is needs deciding: this is a legal
  boundary and not a fence, and drawing an invisible line as a visible one would be an
  invention that `docs/LIBERTIES.md` would have to carry.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- The boundary is derived from committed street geometry, not typed in, and re-derives under
  `check.sh` the way the datum does.
- The PR states, as a measured number, how many modelled structures stand inside it and how
  many outside, and names every disagreement with the block-infill programme's own idea of
  the built town.
- Nothing is drawn in the scene without a stated decision about what a legal line may look
  like; if something IS drawn, `docs/LIBERTIES.md` carries it.

---

## WHAT LANDED (2026-09-13)

**Acceptance, stated before the work and met:** the boundary is derived from committed
street geometry and re-derives under `check.sh` the way the datum does; the PR states as a
measured number how many modelled structures stand inside it and how many outside; and
nothing is drawn in the scene, so `docs/LIBERTIES.md` carries no new admission.

`tools/derive_hay_limits.py` writes `data/reconstruction/1835_hay_limits.json`. All six of
the ordinance's vertices are intersections of committed `path_local_enu_m` centrelines —
five of them true crossings, and the sixth carries the Illinois Street line 100.78 m past
its own committed east end to reach the traced 1834 shore, which is recorded and gated at
150 m. The starting point, *"on Washington street, at the United States Reservation"*, is
where Washington's committed line meets the committed reservation ring's west side, and it
lands there to the centimetre: Washington cannot run further east, which is why the
ordinance could name the spot without a cross street.

**The closure is decided, not derived, and says so.** The ordinance walks an OPEN line of
six vertices and ends at Lake Michigan. The ring closes down the traced lake shore, across
the harbour entrance in one straight segment (water between two piers — a closure, not a
claim about ground), west along the reservation's own traced waterline and south down its
west side. Every closure edge is graded `inferred` with its reasoning, and the reading it
rests on — that the walk *commencing at* the reservation means the reservation bounds the
limit, so the garrison was not subject to the town's hay rule — is stated with its
alternative and its cost.

**Measured.** 199 acres, 4,715.9 m round, 30 vertices. Of 383 committed structure
positions, **302 stand inside the limit and 81 outside** — 23 on the reservation, 36 west
of Canal Street, 20 north of the Kinzie/Illinois line, 1 south of Washington Street
(Heacock's house on Monroe) and 1 out in the harbour (the South Pier). The side each
outside structure falls on is read off the committed street itself, not asserted.

**The one disagreement with the block-infill programme, named.** Eighteen of the twenty-one
scheduled blocks sit inside the limit and the schedule places no NEW roof outside it. Three
sit outside: the Clinton–Canal tier, which the Trustees' boundary leaves out because it
turns north AT Canal. Two of the three are the programme's own `at_capacity` and hold 21
standing roofs between them (11 and 10 of a 31-roof capacity each); the third it already
calls `not_a_block`. So the reconstruction's built town reaches one tier further west than
the town's own fire line did. Either the roofs were there and the line was drawn short of
them, or the tier is a block too far west — the file states the question rather than
settling it.

**Visible half.** Nothing is drawn in the 3-D scene: a legal limit is not a fence, and
painting one across the town would put a line in front of a visitor that nobody in 1835
could see. It reaches a visitor on the CARD instead — `renderers/web/js/ordinances.js`
loads the derived ring and every building's card now carries *"Was it inside the town's
fire limit?"* with the verdict, the 199-acre boundary, the section's own nineteen words and
the citation. 383 cards gain the row.

**Gated both ways.** `check.sh` re-derives the file on every commit and refuses a hand
edit, and the tool's own refusals are self-tested — a self-crossing ring, a leg carried too
far past a committed end, a harbour closure too wide to be a river mouth, a missing street,
and two parallel lines made to meet.

**The date stands where it is.** The ordinance is 5 August 1835, thirty-five days after the
scene date. It is carried as evidence ABOUT the town of 1835 and nothing is placed, moved
or dated because of it; the file says so in `date_standing`.
