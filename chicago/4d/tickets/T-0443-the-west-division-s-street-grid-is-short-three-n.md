---
id: T-0443
title: The West Division's street grid is short three north-south streets and two east-west, and what is drawn as Canal may be Clinton
state: split
epic: GROUND
requested_by: owner
seen: true
effort: L
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-08-31
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

Reported by the owner on 2026-08-31, from the dev preview against the Thompson
plat sheet: *"you have the whole west of the river section off … where you have
what you say is canal, is where I am fairly sure where Clinton should be, the
Canal street is missing and all of the buildings would be positioned further
east along Canal correctly … I think you have Clinton where maybe Des Plaines is
from the Thompson plat."*

Three findings below are **measured from the committed files** and are not in
doubt. The fourth — the shift the owner reports — is stated as a question with
the measurement that would settle it, because this project does not move a
street on a reading of a screenshot.

## 1. Three north-south streets of the West Division are absent — measured

`data/streets/1835.json` holds **19 streets, of which exactly two lie west of
the South Branch**:

| id | `name_1835` | centreline, local ENU east (m) |
|---|---|---|
| `canal` | Canal Street | −189.0 … −150.8 (mid **−170.1**) |
| `clinton` | Clinton Street | −288.0 … −276.5 (mid **−282.2**) |

The Thompson plat's West Division carries **five** north-south streets between
the South Branch and the town's west line. Reading the sheet east to west:
**West Water, Canal, Clinton, Jefferson, Des Plaines**. So **West Water,
Jefferson and Des Plaines are held by nothing at all** — not as a refusal, not
as a queued node, not as a low-confidence line. They are simply not in the file.

## 2. Two east-west streets of the West Division are absent — measured

Four east-west streets reach west of the river, each stopping at east −320 m:
`kinzie`, `lake`, `randolph`, `washington`. The plat's West Division tiers run,
north to south: **Kinzie, Carroll, Fulton, Lake, Randolph, Washington**.

**`carroll` and `fulton` are in no committed file.** Two whole tiers of the West
Division have no street between them, which is why the preview shows unbroken
ground where the plat shows two rows of blocks.

## 3. The one west-side spacing this project does hold is short of the plat's
own arithmetic by 90 feet — measured

Adjacent north-south centreline spacings, from the committed paths:

| pair | spacing (m) |
|---|---|
| market → franklin | 119.2 |
| franklin → wells | 122.0 |
| wells → lasalle | 122.0 |
| lasalle → clark | 123.4 |
| clark → dearborn | 123.0 |
| **clinton → canal** | **112.1** |

Every South Division pair sits in a 119.2–123.4 m band. The single West Division
pair is **112.1 m — 7 to 11 m short of every one of them**. The plat's own
legend reads *"The Streets are all 80 feet wide and the alleys 18 feet wide"*
and *"a scale of 160 feet to an inch"*, so the module is a stated quantity and
not a matter of taste. A West Division laid to the same plat should not be
narrower than the South Division by most of a lot width.

## 4. THE PLAT SETTLES THE SPACING, AND THE SPACING IS WRONG

The plat's legend gives streets 80 ft and alleys 18 ft. The committed east-west
streets give the lot depth: 184.1 and 174.9 ft, so **80 x 180 ft**. Those figures
reproduce the South Division exactly — 4x80 + 80 = **400 ft = 121.92 m** against
a committed mean of **121.92 m, delta 0 mm**.

The West Division's blocks are two lots across by five down, so its module is a
block depth plus a street: **2x180 + 18 + 80 = 458 ft = 139.60 m**. The committed
`clinton -> canal` is **112.1 m**, short by **27.5 m (90.2 ft)**.

A spacing is independent of the anchor, so this holds whatever the answer to the
owner's shift report. What still needs one number is where the West Division sits
relative to the South, because the river breaks the module between Market Street
and West Water Street. **T-0444 owns that.**

## 5. North Water Street crosses ground the plat does not give it

`north_water` runs from east **−30.0** to 970.0. That west end carries it across
the point of land at the river forks. On the plat, North Water Street is a
**north-bank street east of the North Branch**; nothing on the sheet runs it
over Wolf Point. Reported by the owner in the same pass. Whether the west end is
a stray vertex or a deliberate approach is not established here.

## What this ticket is NOT

It does not authorise moving a committed street line. `docs/LIBERTIES.md` L211
and the South Water re-centring of 2026-08-29 are the precedent: a corridor moves
when surveyed control says so, is re-derived from committed points, and the
before and after are both reproducible behind a flag. The same standard applies
here and is not relaxed because the error is large.

**Acceptance:**

1. The west bank of the South Branch is measured at each West Division tier and
   committed, and the plat sequence is stepped from it at the module the South
   Division demonstrates. The answer to §4 is **written down with its numbers**
   before any line moves — including if the answer is that the present Canal is
   correct.
2. `west_water`, `jefferson` and `des_plaines` either exist in
   `data/streets/1835.json` with a stated `geometry_confidence` and sources, or
   each is refused in writing with the reading that refuses it. Absent is not an
   answer.
3. `carroll` and `fulton` likewise.
4. The `clinton → canal` spacing is either brought inside the South Division's
   119.2–123.4 m band, or the reason it is legitimately narrower is committed
   with its source.
5. If any line moves, every building, lot, frontage and street-face adoption
   derived from it is re-derived rather than nudged, and the count of records
   that changed is reported. `tools/check.sh` green.
6. North Water Street's west end (§5) is resolved or split into its own ticket
   with the reason.

**Splitting is expected.** This is filed as one ticket because it is one fault
report, and the owner asked for it to be traceable as one. §4 is a measurement
and should probably be its own child ticket, taken first — nothing else here can
be done honestly until it is answered.
