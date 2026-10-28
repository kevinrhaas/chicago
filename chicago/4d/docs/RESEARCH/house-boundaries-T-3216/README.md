# T-3216 — walks and front boundaries of the ten unpictured worked 1600-block Prairie houses

Piece 3 of T-3204 (the owner, 2026-10-27: every worked house's walk to its door, its gates and
its boundaries to its pictures; where no picture shows them, a stated reconstruction consistent
with the block).

No picture of any of these ten fronts is held, so each one follows its own side of the block.

| side | houses | built | why |
|---|---|---|---|
| west | 1600, 1604, 1608, 1626, 1628, 1634, 1636 | K11 spear fence on its curb along the parcel's street line, a pair of entrance leaves on stone piers standing open (70°), and a flagged walk through them | every pictured west front closes its street line and gates its walk: 1612 (photograph, iron spear fence), 1620 (1874 engraving and 1898 sketch, iron lattice), 1616 (1874, boards) and 1638 (photograph, iron bars on a stone base) |
| east | 1613, 1615, 1619 | `layout: open` and a 1.2 m flagged walk straight out to the public walk | 1621's and 1623's 1886 drawings and 1625's 1890 photograph draw open fronts (T-3221) |

The lot and street lines come from the 1904 parcels (`data/street_grid/1904.json`), carried into each
house's frame. The same transform reproduces the recorded lot lines of 1612, 1616, 1621, 1623 and
1625 to the centimetre. The exceptions:

- 1634 and 1636: the fence is held 0.3 m inside the public walk, because their parcels' street
  line falls on the walk's edge.
- 1626: the south lot line is put on the house's wall, 0.21 m from where the parcel was fitted.
- 1600: its 3.6 m south passage has a shut 1.6 m side gate, as 1612's photograph shows.

**Code.** Six of the seven west houses stand within 0.5 m of their south lot line, which leaves no
passage that the kit's 0.9 m gate could fit. So K11 now lets an iron front run unbroken from the lot
line when the passage is narrower than a gate (`_side_passage_m`), and K14 lays such a yard with no
service walk. A passage wide enough to gate is still refused without one. The other 28 K01 houses
rebuild byte-identical; only their manifest input hashes move.

**Walked.** `tools/qa_house_walks_t3216.mjs` ran on the published `/1904/` app at 1280×800 (full)
and 390×780 (light). From the public walk, the walker reaches every stoop's foot (closest 0.04 to
0.30 m) with 0 blocked frames and no page errors (`stills/walks-after.json`, with a front still
and a gate still per house). No "before" stills were taken: before this change none of the ten had
a walk, and the walk gate (`tools/check_house_walks.py`) listed every one of them as PENDING.

**Not done here.** These need K16 walk support, which is on #1401 (T-3222) and not yet on dev:

- the four timber houses, 1601, 1609, 1611 and 1630;
- 1612 and 1620 (T-3214, #1395).

1635 Forsyth is not a worked 1904 house.

Liberties: `L-k11-fences-1600-block-3216`, `L-k14-walks-1600-block-3216`.
