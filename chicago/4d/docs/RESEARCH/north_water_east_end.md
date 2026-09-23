# North Water Street's east end, and the two excursions the owner marked

Sequel to [north_water_street_and_the_bank.md](north_water_street_and_the_bank.md)
(T-0226), which re-derived every other vertex of this street.

T-0447, 2026-09-04. Answers the owner's fault report of 2026-08-31, which marked up the
dev preview against the Thompson plat and said the whole course of North Water Street is
wrong, naming a dip to local N +2.2 at E +5 and a climb to N +270 at E +970.

**The short answer: the middle of the street is right, the two ends are not the same
kind of thing, and only one of them was ever a line anybody drew.** The dip is the
committed bank, read at half a platted street's distance, and it stays. The climb was
the last surviving fragment of the hand-drawn schematic that T-0226 replaced everywhere
else, and it is now derived under the same rule as the rest of the street — which ends
it at Kinzie Street rather than 17.2 m past it.

Everything below is re-derivable from committed files with
`python3 tools/derive_north_water.py` and gated by `--gate` and `--self-test`, both of
which `tools/check.sh` runs.

## Is the whole course wrong? No — measured against the plat's own arithmetic

The report's strongest claim is that the street is not where the plat puts it. The one
committed line that can test that is Kinzie Street, the next east–west street north.
Measured between the two committed centrelines over the open reach, E +255 .. +830:

| | spacing |
|---|---|
| minimum (E +255) | 130.23 m |
| maximum (E +645) | 148.92 m |
| mean | 142.51 m |
| 458 ft block-and-street module (T-0444) | 139.60 m |

The measured spacing **brackets** the module, with a spread well inside the ±20 m the
bank trace itself carries. This is a **consistency check, not a derivation**: T-0444
measured that module in the West Division, Kinzie's Addition is a different plat, and
this project holds no module for it. Nothing is claimed from the agreement except that
the middle of this street is not where a wrong course would be.

## The dip to N +2.2 at E +5 — the bank's, and committed

It is the west reach's offset curve coming round Wolf Point into the forks. The traced
bank falls 45 m of northing in 35 m of easting there; the street follows it half a
platted module off (12.192 m, `thompson_module_1830`) and ends **at** the fork, which is
where the street ended. T-0372 already ruled on that terminus — it is one of the two
places on this street exempt from the setback because the street meets the water there
on purpose — and refused the two alternatives with numbers. Nothing here moves.

It is worth saying plainly why the dip looks wrong on a table of vertices and is right on
the ground: a street laid on a bank inherits the bank's shape, and the bank at Wolf Point
is a right-angle turn into the forks. The number the report read as a fault is the number
that says the street follows the water.

## The climb to N +270 at E +970 — the draughtsman's, and gone

Before this ticket, `tools/derive_north_water.py` derived the street east only as far as
E +830 and then appended two constants:

```python
E_EAST = 830.0              # where the street leaves the bank and climbs to Kinzie
TAIL = [[920.0, 190.0], [970.0, 270.0]]   # unchanged: dry, drawn, and not in question
```

Those two vertices are `[920, 190]` and `[970, 270]` **verbatim** off the pre-T-0226
hand-drawn line, whose own note read: *"A schematic bank-following path used for
orientation and readout … the committed street module does not yet carry enough control
to claim this curve as a trace."* T-0226 replaced every other vertex of that schematic
because it ran 477 m of its length through the river. These two survived only because
they were dry — which is not a derivation, and the comment claiming they were "not in
question" was the whole of their defence.

Measured, they were wrong twice:

- **21.1 m north** of what this street's own setback rule asks at E +970 (the offset
  curve there reads N +248.9), and 6.7 m north of it at E +920;
- **17.2 m north of Kinzie Street's committed line** at the terminus, so North Water
  Street ended in the block beyond the street it runs to.

### What replaces it

The same climb, derived. East of E +830 the main stem swings north-east into the mouth
and its north bank climbs from N +92 to N +236 in 145 m of easting, so a street laid half
a module off it climbs too — the shape was never in doubt. The east reach is simply
continued under the rule that already governs the rest of the street, and **cut where the
bank's offset curve crosses `kinzie`'s committed line**: local **E +973.6, N +252.9**.

East of that crossing the requirement stands *north* of Kinzie Street, and the plat draws
no pair of east–west streets that swap sides. So the east end is the intersection of two
committed records — the bank and Kinzie — and a Kinzie that moves moves it. It is not a
number this tool chose: `--self-test` case 6 holds it to being a genuine crossing, with
the offset curve 3.96 m south of Kinzie one station before and 5.47 m north two stations
after.

| | before | after |
|---|---|---|
| the climb, E +830 → the end | 165.8 m of drawn line | 148.1 m of derived line |
| street length | 1175.8 m | 1165.3 m |
| authored bends | 24 | 26 |
| verge over that reach (nearest water, any direction) | 12.00 – 27.00 m | 12.00 – 18.00 m |
| east terminus | [970, 270] | [973.6, 252.9] |

**Nothing west of E +830 moved.** The west reach, the crossing and the open reach east of
the slough are vertex-for-vertex what they were, so this is the east end and not a
re-derivation of the street.

## The corroboration, on a record that reads none of this

`data/structures/steamboat_hotel.json`'s placement note, written 2026-08-11 off the
Wright 1834 sheet at this project's fitted affine, says North Water Street *"east of
Wolcott Street, swings north-east with the river"*, that *"the two converge about 165 m
east of State Street, at roughly local E +990"*, and that modern OpenStreetMap agrees —
E North Water Street's west end joins E Kinzie Street about 70 m east of State today.

This derivation reads neither that note nor that sheet, and puts the convergence at
**E +973.6 — 16.4 m west of a reading whose own stated georeference uncertainty is about
20 m.** The swing north-east and the meeting with Kinzie are therefore corroborated
independently. What the authored tail got wrong was not the shape but the line: it drew
the swing as two straight guesses and then overran both the setback and the street.

## What this turned up, and did not settle

The same note puts the Kinzie alignment at **local N +276**, where the committed `kinzie`
record is at **N +252.8** — a 23.2 m disagreement between a structure's prose and a
street's geometry, and the Steamboat Hotel at `[968, 291]` stands 38.2 m north of the
committed line. Filed as **T-0684**; T-0451 owns Kinzie's geometry and this street's east
end is where the *committed* Kinzie is. It is not settled here.

## The records that moved with the line

Five derived files read this centreline; all five were re-derived in the same commit, and
**12 records changed** across them:

| file | change |
|---|---|
| `data/flora/plantings/town_planted_rows.json` | **1 row gained**: the Indian Agency House (`cobweb_castle`) gets its 4 Lombardy poplars — refused before because no line across its green cleared the old street's kink at E +830. 2 rows / 8 stems → **3 rows / 12 stems**. |
| `data/flora/plantings/town_dooryard_plantings.json` | 128 stems, unchanged in count; **5 moved** (`cobweb_castle_tree_1` and four North Division stems). |
| `data/signage/town_business_signboards.json` | 34 signs, unchanged in count; **1 changed** — `steamboat_hotel`'s post board becomes an awning board, the rule stating "no street lies in front of this wall within 22 m — a post here would stand in a yard". That refusal is true about the committed records and is the T-0684 disagreement showing. |
| `data/yard/town_trade_goods.json` | 66 wagons → **65**: `town_wagon_north_water_8` refused, `town_wagon_north_water_7` moved. |
| `data/sidecars/1835/index.json` | recompiled. |

No baked geometry changes: streets, plantings, signboards and yard goods are drawn by the
renderer from these records, and `validate.py --stale` reports 372 assets matching their
inputs and 0 stale.

## Acceptance, against the ticket

1. **Re-derived from the plat and the committed bank** — the open reach measured against
   Kinzie and the platted module above; the east reach re-derived under the offset-curve
   rule and cut at the crossing with Kinzie.
2. **The dip and the climb each committed with a source, or removed with the reason
   recorded** — the dip is the committed bank under T-0372's ruling and stays; the climb's
   two authored vertices are removed, the reason recorded here and in the record's own
   note, and the climb itself re-derived.
3. **Records re-derived and the count reported** — 5 files, 12 records, above.
4. **`tools/check.sh` green.**
