# Glessner's Prairie second-floor sills and the carved band (T-2985)

T-2974 found that sheet 6 draws the second-floor colonnettes' bases on a line at about
19.2-19.4 ft and the lower sashes' glass stopping at about 19.97, where the record built every
second-floor sill at 19.8. This reads the sill, the base blocks and the carved band under the
group of four on sheet 6 and HABS photograph 16, and builds them.

`read_sills.py` re-derives the sheet numbers below from the committed scan.

## 1. The sills: 19.2, from 19.8

Each light on sheet 6 runs from a heavy head line (the soffit) to a heavy sill line, and every
colonnette's splayed base stands on the sill line. The scan is turned slightly, so both lines
read higher toward the south end by the same amount. The light's height does not move with the
turn, so the sill is read under the printed 24.30 head.

| group | lights | height (head to sill) | sill under 24.30 |
|---|---|---|---|
| single | 1 | 5.11 | 19.19 |
| three, north | 3 | 5.19 | 19.11 |
| four | 4 | 5.05-5.07 | 19.23-19.25 |
| three, south | 3 | 5.09-5.11 | 19.19-19.21 |

HABS photograph 16 (frontal and level), scaled on its printed 0.00 (row 783) and 24.30
(row 366), gives the same answer. The soffit's shadow starts at row 364-365. The painted
sub-sill ends and the stone sill begins at rows 452-455. That makes the lights 5.1-5.2 ft.

**Built: every second-floor sill at 19.2, so each light is the sheet's 5.1 ft (it was 4.5).**
The colonnettes take their heights as shares of the opening (T-2965). They now stand on the
drawn sill, with a base about 0.66 ft high (the sheet draws 0.63) and a capital about 1.5 ft
(the sheet draws about 1.53).

The 19.97 is the glass, not the stone. On the sheet the lower sashes' glass stops about 0.65 ft
above the sill line, and on the photograph about 0.4-0.6 ft. That is the frame's sub-sill and
bottom rail, which the build draws 0.48 ft deep.

## 2. The carved band under the group of four

Sheet 6 draws one granite course whose top line is the sill line. It is 1.02-1.08 ft deep
(18.15-19.2 on the built sill). The egg run reaches S 24.95-40.4. A foliate end block closes
each end: S 23.21-24.90 at the south and S 40.42-42.34 at the north, about 1.8 ft wide.
Photograph 16 shows the course under the group's sill, about 1 ft deep.

It had been built 0.4 ft deep at 19.2-19.6 on S 26.2-40.0, with end blocks 1.44 ft wide
(0.44 m, fixed in the generator).

**Built:** the course at z 18.23-19.05, so its end blocks run 18.15-19.2, under the sill.
The egg run is S 24.95-40.4 and each end block is 1.8 ft wide. The record's new `terminal_ft`
sets the block width; where a record names none, the generator keeps the 0.44 m it drew
before. The carving in the blocks is unchanged and still reconstructed.

## 3. Not changed

- **The heads (24.30).** These are the sheet's printed level.
- **The string above bed 8.** Whether the printed course string holds on the Prairie front
  above the door head is T-2986. Neither the sill nor the band is set on a bed of it.
- **The north gable pair's colonnettes.**

## Gate

Rebaked `glessner_house`: full and web tiers 1,389,531 triangles (+3,536), light 198,397.
The full and light tiers have 0 coincident faces; the web tier has 4, which the K01 contract
passes. Re-derived: web and light tiers, recovery pack, sidecar, K01 baseline and both
opening schedules.
