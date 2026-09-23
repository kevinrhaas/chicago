---
id: T-0453
title: The river banks are traced from Wright 1834 and the owner reads the Thompson plat differently at Wolf Point
state: split
epic: GROUND
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-04
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T19:24:25.650Z
claimed_run: null
---

**Take this before T-0447 and T-0451.** Both measure streets against the bank,
and this asks whether the bank is where the reconstruction puts it.

## The two sources disagree, and the file says which one it used

`data/terrain/epochs/e1834_harbor_cut/river.geojson` — *"Chicago River — the
forks"*:

> *"Planform traced from the **Wright 1834 survey**… Planform is as drafted on a
> **cadastral plat, not a hydrographic survey** — see `drafted_width_m`."*

The three bank features (North Division shore, **West Division shore at Wolf
Point**, South Division shore) are all the boundary of that one traced polygon.
So every bank in the model is Wright 1834, at a stated tolerance of about ±20 m.

On 2026-08-31 the owner marked the dev preview against the **1830 Thompson plat**
and reported the river borders drawn differently — the disagreement is around
**Wolf Point and the forks**, which is exactly where `north_water` also runs onto
ground the plat does not give it (T-0447).

## This is a source conflict, not obviously an error

Wright 1834 is four years later than the plat and is a survey of what was there;
the Thompson plat is the town as laid out. They can legitimately differ, and a
±20 m drafting tolerance can absorb a lot. **Nothing here says the committed bank
is wrong** — it says two committed-quality sources disagree at Wolf Point and this
project has only ever read one of them for the planform.

## A NAMED DEFECT ON THE SOUTH BRANCH — reported by the owner, 2026-08-31

The owner marked a bump on the South Branch's east bank that "sticks out" and
should not be there. It is in the committed geometry and it is measurable.

`river.geojson`, *South Division shore*, converted to local ENU against
`data/datum.json` (origin UTM 447072.7 / 4637395.8):

```
   ( 78.7,  -78.1)
   ( 78.7,  -85.3)
   ( 87.2,  -96.8)   <-- steps 8.5 m back EAST, then the bank returns west
   ( 73.5, -147.0)
```

That vertex lies **9.4 m off the straight line between its own two neighbours** —
the **largest departure of any vertex in the whole feature**. The next worst on
this reach are 8.2 m at (97.5, −70.5) and 7.0 m at (167.6, +1.3); everything else
is under 6 m.

**Read it honestly in both directions.** The file declares the planform is drafted
on a cadastral plat rather than a hydrographic survey, with a tolerance of about
±20 m — so 9.4 m is *inside* the stated tolerance and is not, by itself, proof of
an error. What is suspect is the SHAPE: a single vertex stepping out and back is
the signature of a trace artefact, not of a bank. A drafting tolerance explains a
line that is smoothly displaced; it does not explain one spike between two points
that agree with each other.

**Acceptance:**

1. The Thompson plat's bank at the forks is traced and committed **beside** the
   Wright 1834 line, not over it — both readable, each with its source.
2. The disagreement is measured in metres at named eastings, the way T-0444
   measures the West Division's spacings, and reported rather than characterised.
3. The owner rules which is the planform of record, and the ruling is written
   into the ticket with the measurement in front of it. If the answer is that
   they differ by less than the ±20 m the file already declares, that is a pass
   and the finding is that there was nothing to fix.
4. Nothing moves in this ticket. Moving the bank re-derives every waterline test
   in the project — `generate_plat_lots.py`'s headroom check, the wet-sample
   refusals, the frontage works — and that is its own unit of work with its own
   count of changed records.

5. The South Branch spike at local (87.2, −96.8) is resolved: either re-traced
   from the source and shown to be a real feature of the drawn bank, or removed
   as a trace artefact with the re-trace that says so. **A vertex is not deleted
   because it looks wrong** — the source is re-read and the reading recorded.
6. The same outlier scan is run over all four water features and any other vertex
   departing its own neighbours by more than the drafting tolerance is listed,
   so this one is not fixed while its siblings survive.

## A shore view deposited 2026-09-03 (owner)

`chicago/reference/images/chicago/eliza-chappel-school/21617595_10203558686525015_5452300313452439832_n.jpg`
— *"a great pic of the shore along there"*. Shows the bank in profile with canoes
afloat and drawn up on the beach, a white lighthouse tower on a low point in the
middle distance, and a scatter of small gabled buildings across a flat horizon.
Useful here for the BANK: how the ground meets the water, how far the beach runs
out, and where the light stands relative to it. Provenance is unestablished (a
social-media filename, no artist, title or date), so it corroborates a traced bank
rather than driving one, and needs a source record before it is cited. The building
at its right is read in T-0617, which is adjudicating whether it is the Sauganash's
log annex.
