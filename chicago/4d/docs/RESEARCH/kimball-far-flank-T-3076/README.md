# 1801 Prairie's far 18th Street flank: heights and ground (T-3076)

T-3074 re-solved the Taylor camera (`data/reference_views/kimball_house_1801_prairie/taylor_c1895_northwest.json`)
on the lake's horizon. Read through it, the far flank stood low. This note re-reads the far flank's rows off the
print (`taylor_c1895_kimball_1801.jpg`, 1600 x 1491 px) and asks what the ground did.

## Heights, read through T-3074's camera

z = 0.06 + (1081 - y) x d / 1521, where d is the depth along the camera's axis of the 18th Street wall
(v 0) at the row's x. That depth is about 42 m at x 385 and 49-51 m at the range and turret (0.033 m a pixel).

| row on the print | y (px) | x (px) | reads (m) | built before | built now |
|---|---|---|---|---|---|
| course along the whole flank, by the arched lights | 1045 | 385 | 1.05 | | |
| the same course at the range and turret | 1045-1048 | 185-300 | 1.1-1.2 | | |
| range: first storey's lights, sill to head | 1040 to 997 | 247-262 | 1.35-2.8 | 2.15-4.55 | 1.35-2.85 |
| range and turret: band under the upper storey | 957-958 | 185-300 | 4.15 | 5.0 | 4.15 |
| range: upper lights | about 905-950 | 240-262 | 4.45-5.9 | 5.6-7.4 | 4.45-5.95 |
| range: eaves | 893-897 | 260-300 | 6.2-6.4 | 8.1 | 6.35 |
| turret: eaves | 890-895 | 178-250 | 6.3-6.5 | 8.1 | 6.35 |
| turret: the cone's neck under the finial | 778 | 222 | 10.2 | about 12.7 | about 10.2 |
| turret: the finial's top | 702 | 222 | 12.7 | about 13.4 | about 10.9 (open) |
| wall's foot at the front's corner | 1096-1100 | 978 | -0.2 to -0.45 | 0 | 0 |
| wall's foot at u 13 | 1103 | 700 | -0.33 | 0 | 0 |
| wall's foot at the range | 1105-1108 | 200-300 | -0.75 | 0 | 0 |

The course at about 1.1 m runs level along the flank through this camera, so the camera reads the flank level and
the far heights are the building's. Foot to eaves at the range is about 7.0-7.2 m whichever horizon is held.

## The ground along 18th Street

The house still stands, so the walk along its north wall is a modern reading of its grade. The USGS 3D Elevation
Program's 1 m bare-earth model (`usgs_3dep_1m_dem`), read through its point query service
(`https://epqs.nationalmap.gov/v1/json?x=<lon>&y=<lat>&units=Feet&wkid=4326`) on 2026-10-23, in feet NAVD88, at
points in the record's frame (u west toward Prairie Avenue from the main block's rear, v south from the 18th Street
wall; turned to UTM 16N from the record's position with its 179.454-degree rotation taken as 180, under 0.3 m off at
these distances):

| line | u 22 | u 18 | u 14 | u 10 | u 6 | u 2 | u -2 | u -6 | u -10 | u -14 | u -18 | u -22 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v -1.5 | 594.05 | 593.99 | 593.92 | 593.92 | 593.94 | 593.81 | 593.76 | 593.76 | 593.57 | 592.78 | 593.02 | 592.63 |
| v -4.0 | 593.66 | 593.59 | 593.66 | 593.72 | 593.55 | 593.61 | 593.50 | 593.30 | 593.31 | 593.17 | 592.76 | 592.50 |
| v -9.0 | 593.80 | 593.80 | 593.78 | 593.78 | 593.72 | 593.72 | 593.72 | 593.65 | 593.57 | 593.43 | 593.21 | 592.95 |

From the front (u 22) to the turret (u -15.6 to -18), the ground beside the wall (v -1.5) falls about 1.0 ft
(0.31 m), the walk (v -4) about 0.9 ft (0.27 m), the roadway (v -9) about 0.6 ft (0.18 m). The print's foot
falls about 0.3-0.55 m over the same run. So 18th Street falls east about 0.3 m along the house, and the rest of the
0.8 m T-3074 found is the range standing lower than built: about 1.8 m.

## What was rebuilt

The east range (`rear_wings` r2): floor 0.75 m, storeys 3.4 and 2.2 m to eaves at 6.35 m, lights 1.5 m tall 0.6
and 0.3 m over each floor. The turret (`bays` turret): storeys 4.15 and 2.2 m, cone pitched 2.2. The floor and the
level lot are `L-kimball-1801-range-heights-3076`. The turret's shaft width and its tall finial stay open in the
match record.
