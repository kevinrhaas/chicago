# The 1880s scene stands on 1 July 1888

**Ticket:** T-1249, piece 1 of T-0473 (*Create an 1880s South Side terrain and urban-ground
epoch*). **Written:** 2026-09-17. **Machine copy:**
`data/terrain/1880s_scene_date_constraints.json`, re-derived on every commit by
`tools/check_1880s_scene_date.py`.

T-0473 asks for "a specific representative scene date in the 1880s **after checking landmark
construction dates**". This memo is that check, and the arithmetic that turns it into a day.

## 1. What the date had to satisfy

The date is not decorative. Four later tickets resolve against it:

| ticket | what it resolves against the date |
|---|---|
| T-1250 | which lake edge `shore_1880s_ic_edge` traces |
| T-1251 | which state of grade, fill and drainage the terrain spec describes |
| T-1252 | which heightfield is baked, and the scene file that selects the epoch |
| T-0474 – T-0477 | which Prairie Avenue street grid, mansions, residences and streetscape stand |

T-0475 is the one that binds hardest — "**Build the Prairie Avenue landmark mansion core**". A
representative date that predates the avenue's landmarks would ask that ticket to build the
avenue's best-documented house out of a scene in which it did not exist.

## 2. The landmark dates, and what was actually found

Two Historic American Buildings Survey records were retrieved at their Library of Congress item
endpoints on 2026-09-17 and read in full.

### HABS IL-1015 — John J. Glessner House, 1800 South Prairie Avenue

The record carries **two** dating statements, and they do not agree:

> Significance: **Designed and built between May 1885 and December 1887**, this house is
> considered the last of the fully personal works of the architect H.H. Richardson and one of
> his finest houses.

> Building/structure dates: **1886- 1887 Initial Construction**

They differ at the start of the work — May 1885 against 1886 — and agree at its end: **both
finish in 1887**, and the fuller one names December. The project takes from the record only what
both statements support, which is a floor and not a completion date:

> **The Glessner House was not complete before the end of 1887.**

The disagreement over the start is left in the data rather than averaged away. It bounds nothing
this ticket needs, and a midpoint would be an invention.

The record also gives NRHP reference number 70000233 and a 1958 Chicago Architectural Landmark
designation. Neither bears on the date.

### HABS IL-1077 — W. W. Kimball House, 1801 South Prairie Avenue

This record was opened **specifically because** the date usually given for the Kimball House —
1890–1892 — falls outside the decade T-0473 asks for, which would have made it the reading that
decided this ticket. It would have forced a choice between the avenue's two best-known houses.

**It does not date the house.** There is no `Building/structure dates` note and no year anywhere
in the significance statement, which says only:

> One of the few remaining residences along Chicago's earliest Gold Coast area, it was designed
> by Solon S. Beman for the founder of the Kimball Piano Company.

So the conflict does not exist in this corpus, because one side of it is not sourced here. The
1890–1892 figure is asserted **nowhere in this project**, and the record is committed in its
undated state (`habs_kimball_house_il_1077`) so that the absence is a recorded finding rather
than a gap the next run fills off the open web. A ticket that wants the Kimball House in an 1880s
scene has to date it from a source that states a date.

## 3. The derivation

Three steps, and `tools/check_1880s_scene_date.py` performs all three from the committed
readings on every commit:

1. Take the latest `not_before` over every reading of kind `lower_bound` — **1888-01-01**.
2. Carry it to the first 1 July on or after that day — **1888-07-01**.
3. Require the result inside the window T-0473 set, 1880-01-01 … 1889-12-31. It is.

**The year is evidence. The day and the month are not**, and `docs/LIBERTIES.md` § L241 says so
in those words. Nothing in this corpus mentions 1 July 1888. The day is chosen so the two scenes
this project intends to carry stand on the same ground in the same season at the same hour of
light, fifty-three years apart, and because midsummer is the only season for which any flora,
fauna or lighting behaviour has been built here at all.

## 4. What this replaced, and why it mattered

`tools/check_shoreline_states.py` has carried

```python
"1880s": date(1885, 7, 1),
```

since T-1152 (2026-09-15). Nothing documented it and nothing was meant to: T-1152 needed some day
inside the decade in order to prove that the 1880s address resolved through its own epoch to its
own shoreline state, and it wrote one in. It was scaffolding for a different assertion.

It was also **three and a half years too early**. On 1 July 1885 the Glessner House was a hole in
the ground at best — the earlier of the record's two statements has the work beginning in May of
that year. A scene on that date could not show the avenue this epoch exists to show.

A plausible-looking number sitting in a gate is read as settled by the next run that finds it,
which is why the fix is not to correct the literal but to remove it: the gate now reads the date
out of the committed readings, and the superseded date is recorded under `adopted.supersedes` so
it cannot quietly return.

## 5. What this memo does NOT settle

- **The lake edge.** `shore_1880s_ic_edge` is still `geometry: null`, still `planned`, and the
  gate fails if it acquires a line here. T-1250 owns the sourced trace.
- **The Illinois Central.** The epoch's old placeholder note asserted that "the Illinois Central
  trestle line already fixed the shore in 1852". No source in this corpus says that. The claim
  is neither repeated nor denied in the epoch record now; it is T-1250's to establish or refuse.
- **The ground.** No grade, fill, drainage or railroad earthwork is described anywhere yet
  (T-1251), and no heightfield is generated or baked (T-1252).
- **The scene file.** There is still no `data/scenes/1880s.json`. A scene must stand on a
  heightfield, so the scene file lands with T-1252 rather than here; adding one now would point
  a scene at an epoch with no ground.

## 6. Retrieval notes for the next run

- LOC **item** endpoints (`https://www.loc.gov/item/<id>/?fo=json`) answered 200 to unattended
  retrieval on 2026-09-17, though they rate-limit to 403 under a burst; a `--retry-delay 15`
  recovered every time.
- LOC **search** (`https://www.loc.gov/search/?…&fo=json`) answered 403 to the same client on the
  same day. Sibling HABS records are reachable by item id, not by search.
- `www.encyclopedia.chicagohistory.org` **did not resolve** from this runner on 2026-09-17, so the
  Encyclopedia of Chicago entries this project already cites could not be re-read. Nothing here
  depends on them.
- No period sheet for the 1880s lakefront has been identified yet. T-1250 needs one, and it will
  need georeferencing the way `rees_rucker_1849` was.
