# Carroll and Fulton, and the tier band the West Division actually holds

**T-0446, piece 3 of 4 of T-0443. 2026-09-04.** Every number here is recomputed
from committed files by `tools/measure_west_division_tiers.py`, which carries the
assertions as `--self-test`. Unlike T-0444's memo, this one *does* move
something: two streets are seated, and §5 says what moved with them.

## The report

T-0446, from the owner's fault report of 2026-08-31 against the Thompson plat
sheet:

> Four east-west streets reach west of the river, all stopping at east −320 m:
> `kinzie`, `lake`, `randolph`, `washington`. The plat's West Division tiers run
> north to south **Kinzie, Carroll, Fulton, Lake, Randolph, Washington**.
> `carroll` and `fulton` are in no committed file, so two platted tiers have no
> street between them and the preview shows unbroken ground where the sheet
> shows two rows of blocks.

That was exact. Between `kinzie` and `lake` west of the river lay **370.2 m** of
undivided ground — nearly three of this town's blocks — with no line drawn across
it at any point.

## Fulton is held by control, and is the easy one

West Fulton Street still crosses all four of the West Division's north-south
streets on the ground, so it is fitted the same way the rest of this file's West
Division lines are: to surviving intersection nodes, read from OpenStreetMap and
transformed to EPSG:26916 against `data/datum.json`.

| intersection | OSM node | local east (m) | local north (m) |
|---|---|---|---|
| Canal × Fulton | 258020617 | −162.00 | +12.17 |
| Clinton × Fulton | 258966840 | −282.18 | +11.83 |
| Jefferson × Fulton | 262247424 | −401.04 | +13.11 |
| Des Plaines × Fulton | 258966841 | −524.88 | +13.72 |

A least-squares line through the four has slope −0.004909 and residuals of
+0.35, −0.58, +0.12 and +0.11 m — **RMS 0.35 m**, a tighter fit than the
two-point lines several streets in this file carry. The seated path keeps the
same west clip as its four neighbours (east −320) because that clip is this
reconstruction's own extent and moving it would move five streets rather than
one.

## Carroll does not survive inside the plat, and the negative is recorded

An Overpass query for every way named Carroll between lon −87.68 and −87.632, run
2026-09-04, returned eight. **Not one of them meets Canal, Clinton, Jefferson or
Des Plaines.** The two fragments nearest the plat lie outside it in opposite
directions:

- local north +193 to +199, east −55 to +561 — the Kinzie's Addition alignment on
  the *far* side of the North Branch, some 57 m north of where the West Division
  band puts the tier;
- local north +95 to +133, more than 1,180 m west of the datum — ground the
  Thompson plat never covered.

Inside the original town, Carroll was taken by the Union Station approaches and
the Kennedy Expressway. So it is the one West Division tier that has to be
interpolated, and it is graded and noted for exactly that.

**Method, and the bracket that is its honest width.** The centreline is the
midpoint of `kinzie` and `fulton` at every easting. The two flanking tiers are
*not* evenly spaced on the surviving grid — Kinzie to Fulton measures 250.30 m
against Fulton to Lake's 119.91 m — so the two one-module steps disagree:

> stepping one Fulton-to-Lake module **south from Kinzie** puts Carroll at north
> +142.63; stepping one **north from Fulton** puts it at +132.16. The midpoint,
> +137.40, sits between them and is **±5.24 m** from either.

That ±5.24 m is this line's uncertainty and is the largest of any West Division
street's. The self-test asserts the midpoint stays inside that bracket, so if
`kinzie` or `fulton` is ever re-derived, Carroll cannot be quietly left behind.

Neither tier is given a crossing. Both paths stop 3 m short of the committed west
bank of the North Branch: no source gives Carroll or Fulton a bridge, and
Kinzie Street's is the only West Division crossing in this scene.

## The tier band, and the South Division it is measured against

Acceptance 2. At local east −250 m, inside the committed span of all six tiers:

| gap | m | ft |
|---|---|---|
| kinzie → carroll | 125.15 | 410.6 |
| carroll → fulton | 125.15 | 410.6 |
| fulton → lake | 119.91 | 393.4 |
| lake → randolph | 142.78 | 468.4 |
| randolph → washington | 135.32 | 444.0 |

The South Division's own east-west spacings, taken at east +500 m clear of the
river, are **lake → randolph 142.79 m** and **randolph → washington 135.32 m**.

> **West Division band mean 123.4 m (405 ft); South Division band mean 139.1 m
> (456 ft). The West Division's tiers are 15.7 m — just over 51 ft — tighter.**

This is not a rounding difference and it is not new to the two lines seated here:
the band is fixed at both ends by `kinzie` and `lake`, which were already
committed, and the two new tiers only divide it.

## What this does NOT settle, and it is worth stating plainly

T-0444 derived the West Division's **north-south** module as 2 × 180 ft lot depth
+ 18 ft alley + 80 ft street = **458 ft**, and found the committed `clinton →
canal` spacing of 405.3 ft "90 ft too close together". The tier band measured
here is **405 ft** — the same number, in the other direction.

So the surviving West Division grid is very nearly **square at 405 ft**, and two
readings of it are now on the table:

1. the grid is uniformly compressed, in both directions, against a 458 ft plat
   module — T-0444's reading, extended;
2. the West Division's module simply *is* about 405 ft, and the 458 ft figure —
   which rests on an inferred 180 ft lot depth and the owner's two-lots-across
   block count, neither of them read off a sheet — is the number that is wrong.

Nothing committed to this repository can choose between them: no plat survey is
held here, and this project's own rule refuses to trace the 1834 sheets in any
case. **This memo does not choose.** It records that the two derivations now
disagree by the same 53 ft in both directions, which is a sharper question than
either had on its own, and it leaves the lines where the surviving control puts
them rather than where an unread module says they should be. Both seated tiers
are graded `inferred` for that reason.

## What moved with them (§5)

Four derived files re-derive off the street set and were regenerated in the same
commit:

- `data/flora/plantings/town_dooryard_plantings.json` — three dooryard stems shift
  clear of the new corridors; the count is unchanged at 128 stems over 62 of 150
  dwellings.
- `data/yard/town_trade_goods.json` — one more wagon finds a street verge (67, of
  which 63 the town's), and the cart/farm-box mix moves with it.
- `data/research/newspapers/register_1835.json` — the street count in its header,
  19 → 21.
- `data/sidecars/1835/index.json` and the published mirror.

No structure moved and no roof was dealt: nothing in the town stands inside either
new corridor, which the corridor-intrusion ratchet confirms by staying silent.
