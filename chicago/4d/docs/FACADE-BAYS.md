# Facade bays — whose count "2-3 shop bays" is

**Settled T-1665, 2026-09-27, on the specification's own words. No geometry moved.**

The 2026 reconstruction specification describes families by a bay count:
`2/3 bays` for an older log cabin, `3/5 bays; center or side door` for a two-room
frame cottage, `5 bays; center hall` for a larger house, `2-3 shop bays` for the
narrow two-storey store, `4-6 bays` for the wide one. This project's storefront
archetype also has a `shopfront_bays` parameter. **They are not the same count, and
they differ by one.**

| count | what it counts | where it lives |
|---|---|---|
| a **facade bay** | one vertical division of the elevation — a window **or the door** | `data/reconstruction/1835_family_archetype_crosswalk.json`, `key_geometry_parameters.variants` |
| `shopfront_bays` | **show windows only**; the door is added separately | `generators/archetypes/frame_storefront_params.py` |

`facade_bays(shopfront_bays) == shopfront_bays + 1` is the mapping, and
`tools/test_shopfront_bay_count.py` is the gate that keeps it.

## Why the specification's bay includes the door

Not a convention adopted for convenience, and not a question for the owner: the
crosswalk settles it, twice, by naming a door position beside an odd count.

    D4  "3/5 bays; center or side door"
    H1  "5 bays; center hall; kitchen ell; small porch"

A centre door has to be centred *in* an odd number of bays. Read the door out of
the count and "3 bays, centre door" describes four openings with a door that cannot
be in the middle of them — the sentence contradicts itself, on two families. Read
the door in and both sentences are the ordinary architectural description of a
three-bay and a five-bay front, and nothing contradicts anything. The gate
re-derives this from the crosswalk on every run rather than remembering it: if the
file ever stops carrying a witness, the argument has gone and the gate says so.

## What it makes true of C3, which is what T-1665 asked

C3's `2-3 shop bays` asks for `shopfront_bays` of **1 or 2**, not 2 or 3. Measured
on the seven committed C3 records, with the archetype's own set-out (5 ft bay,
40 in door, 0.6 m of plain wall at each end):

    2 facade bays (1 window): opening 3.251 m, needs 4.451 m of frontage
    3 facade bays (2 windows): opening 4.877 m, needs 6.077 m
    4 facade bays (3 windows): opening 6.502 m, needs 7.702 m

All seven carry **2 facade bays — inside the band, at the bottom of it.** C3's
authored footprint band is 18x36-22x50 ft and its roof is built front-gable, so its
frontage is the 5.49-6.71 m narrow end; 3 facade bays needs 6.077 m and **four of
the seven have it**, so the top of the range is reachable and was never impossible.
A fourth bay never is, and the specification does not ask for one.

The third bay is not taken because `SHOPFRONT_MAX_FRACTION` (0.45) refuses it:
4.877 m of opening on the four fronts that fit is 75.6% to 80.3% of the wall, which
is the plate-glass proportion that fraction exists to refuse.

## And the floor that was overruling the fraction in silence

`default_shopfront_bays` tries 3 windows, then 2, then returns 1. **That floor is
not checked against the 45% ceiling.** Measured over all 45 committed
`frame_storefront` phases: 26 reach the floor, and on 20 of them the remaining
window and door take **50.0% to 66.7%** of the frontage — over the stated maximum,
with nothing saying so. Those 20 are the narrow gable-front stores (C1, C2, C3),
where the front is the building's 18-22 ft end. The 0.45 fraction was argued for a
store filling a 55 ft lot frontage with its *eaves* to the street, and on a narrow
front it therefore decides nothing at all: the floor decides.

Nothing about that is fixed by changing a number, and no number was changed. What
changed is that it is now **sayable**: `shopfront_bay_verdict` returns the count,
which branch answered, and the measured fraction, and the gate holds every floor to
being one the *frontage forced* — a front wide enough to satisfy the fraction at the
next count up can never fall to the floor.

## The one family still outside its band

`recon_1835_blk_south_water_franklin_c4_01`, the town's single C4, carries 2 facade
bays against an authored 4-6. Its 9.32 m front would take 4 (7.702 m needed, 0.81 m
of plain wall left at each end), so this is the fraction rule refusing 69.8% of the
front rather than a footprint that cannot hold it. Moving it is a bake and its own
ticket, **T-1667**. `SPEC_SHORTFALL` in the gate names it, with that measurement, and the gate
refuses any *other* family that falls out of band unannounced.
