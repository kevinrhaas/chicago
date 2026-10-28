# T-3230 (piece 2 of T-3216) — walks and front boundaries of the four unpictured K16 frame houses of the 1600 block

The owner asked (2026-10-27) that every worked house have a walk to its door and correct front
boundaries, matched to its pictures, and where no picture shows them, a stated reconstruction
consistent with the block. T-3229 (#1408) did the ten K01 brick houses of the 1600 block; this is
the four K16 timber houses. No picture of any of their fronts is held, so each follows its side of
the block, as T-3229's did.

| house | side | built | why |
|---|---|---|---|
| 1601, 1609, 1611 | east | `layout: open` and a 1.2 m flagged walk straight out to the street line | 1621's and 1623's 1886 drawings and 1625's 1890 photograph draw the east side open (T-3221); 1613, 1615 and 1619 were laid open on that reading (T-3229) |
| 1630 | west | a squared stone kerb (0.35 m through, 0.32 m high) with an iron railing to 0.83 m along the street line, an opening 1.5 m clear on the stair's axis between two 1.2 m stone posts, and a flagged walk through it | every pictured west front closes its street line and opens it only at the walk: 1612, 1616, 1620 and 1638, the block's other timber house (its photograph: iron bars on a 0.32 m stone base to 0.83 m, an open gateway with no leaf); the kerb, railing and posts are the K16 kit's (1720's, T-3205) |

**Lot and street lines.** The 1904 parcels' (`data/street_grid/1904.json`), carried into each
house's plan frame by the placement its sidecar holds — the same transform puts 1720's recorded
street line (u 31.2) and lot lines back on its parcel to the centimetre.

| house | parcel | street line u (at the walk) | lot s |
|---|---|---|---|
| 1601 | prairie_1601 | 18.09 (18.12-18.04 along the front) | -1.70 .. 13.20 |
| 1609 | prairie_1607 (shared with 1611) | 14.51 | -5.56 .. 4.775 (the party wall) |
| 1611 | prairie_1607 (shared with 1609) | 14.47 | -0.025 (the party wall) .. 5.25 (its own south wall, 0.44 m past the parcel's line) |
| 1630 | prairie_1630 | 21.37 | -2.535 .. 6.035 |

**Code.** `generators/archetypes/k16_yard.py` lays a frame house's yard. It only knew a
`stone_coping_wall` boundary; it now also takes `layout: open` (street line and lot lines, nothing
else), which lays nothing on the line and writes the same `k11.boundary.open` instance a K01 open
front writes, so the walk runs straight out from the stair's foot. 1638 and 1720, the two other K16
houses with a yard, rebuild byte-identical; only their manifest input hashes move. The four houses
are out of `tools/check_house_walks.py`'s PENDING list: 33 worked houses walked into, 11 pending on
their own lanes.

**Walked.** `tools/qa_house_walks_t3230.mjs`, on the published `/1904/` app at 1280×800 (full) and
390×780 (light): from the public walk the walker reaches every stair's foot (closest 0.01-0.34 m)
with 0 blocked frames and no page errors (`stills/walks-after-*.json`, a front still and a gate
still per house at desktop). The app's ground rises 0-18 mm over each house's base under its walk,
less than the flags' 0.06 m, so no `grade_m` lift is laid. No "before" stills: before this none of
the four had a walk, and the walk gate listed each as PENDING.

Liberty: `L-k16-walks-1600-block-3230`.
