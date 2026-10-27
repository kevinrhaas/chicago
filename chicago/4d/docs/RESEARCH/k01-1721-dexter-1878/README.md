# T-1878 (package N18A of T-1837) — 1721 Prairie onto K01

It refines the district draft (T-2335) in place under `dexter_house_1721_prairie`. T-1879 owns the
detail and the image gate.

## The house

Wirt Dexter's house of 1863 (the marker), given a new front in 1889 by Arthur Little of Boston.
The 1911 sheet prints it "3B" brick with two curved bays on the Prairie face and a long "2B" rear
wing with one-storey frame pieces at both ends; the T-1840 census rules the sheet's 1721 and the
register's 1719 one property.

## The picture read

**The 1891 Inland Architect plate** (`inland_architect_1891_06_dexter_plate`, public domain; library
`a16-inland-1891-dexter-residence`), from across Prairie Avenue to the north-west. Read off it:

- the north part of the front stands back, and the entrance porch stands in that recess on two
  round columns, its flat roof railed as a balcony at the second floor; the door is in the
  recessed wall;
- the rest of the front steps forward as one block. Its north return is a narrow face in shade
  (it faces the camera, so the block stands forward, not back), and a tall plain stack rises from
  it past the parapet;
- on the block's face, two bows rise through the ground and second storeys, each roofed at the
  third floor as a balcony behind a balustrade, the third storey flat behind them;
- three storeys over a low basement, a deep moulded cornice under a balustraded parapet, no roof
  seen over it;
- a light, smooth wall with no coursing, on a print sharp enough to show the shutters' slats.

The four other pictures on the ticket are T-1879's: the two c. 1888 photographs show the house
before Little's front (a different phase), the Detroit print sees it only at its edge, and the
c. 1905 Clark negative is online only as a contact thumbnail.

## The plan, from the 1911 sheet (trace s20fp-1721-b1, in the house's frame: u toward the street, v south from the north wall)

| part | u (m) | v (m) | built as |
|---|---|---|---|
| main block | 0 – 7.75 | 0 – 17.6 | K01's main body; the street front is the recessed wall |
| forward block | 7.75 – 10.65 | 3.55 – 17.6 | K08 full-height projection marked `block`, flush with the south wall |
| north bow | to 11.85 | 4.8 – 9.4 | K08 bow, 4.6 m chord, 1.2 m out, `on_front` |
| south bow | to 11.75 | 12.6 – 17.0 | K08 bow, 4.4 m chord, 1.1 m out, `on_front` |
| porch (p2, frame) | 7.75 – 10.65 | 0.25 – 3.35 | K01's door hood on two columns, 2.9 m out, 3.1 m wide, railed |
| rear wing ('rear2B') | -19.9 – 0 | 0 – 6.2 | K01 rear wing, two storeys, decked flat |
| frame pieces (p3, p4) | -22.4 – -19.9 | 0 – 6.0 | one frame room, one storey |

The trace puts the recessed wall at u 7.7-7.75, the forward block's straight face at u 10.5-10.6,
the bows to 11.6-11.8, the north wall at draft v -3.75 to -3.9 and the south wall at 13.6-14.0;
the record's origin is carried 3.8 m north of the draft's to stand on the north wall.

## The kit change

K01 has no way to step its own front: a rear wing stands behind the main body, a rear section
steps out of a side wall under a mansard, and a projection is at most 1.2 m proud and 6 m wide.
So two additive options, which no other record names (every other house's bytes unchanged):

- `bays[].plan.block` — a K08 full-height projection 6-16 m wide and 1.2-3.5 m proud, square,
  flush with one corner: a whole forward block of the front;
- `bays[].on_front` — a bay on grade standing on such a block's face, framed exactly as T-3108
  frames a bow on a chamfer (the face is the wall, `s_m` along it), held 0.3 m inside its ends.

## Seen from the plate's camera

A rough camera (not solved, not committed — that is T-1879's image gate) shows the recess and the
porch in it, the forward block and its stack, both bows and the three storeys where the plate has
them. What differs is what T-1879 builds: the parapet's balustrade, the bows' balconies,
shutters, balconettes and carved tablets.
