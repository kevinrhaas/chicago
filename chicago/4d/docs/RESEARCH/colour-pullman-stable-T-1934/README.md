# The Pullman stable's stone, read from its pictures (T-1934)

The owner, 2026-10-30, on the Pullman estate (1729 Prairie): *"pay some attention to the
surfaces and color of the stable, etc and make sure it is correct"*. This note reads the stable's
wall tone the way `docs/RESEARCH/colour-1700-block-T-3244/` read the 1700 block's, and says what
was changed. `tone.py` beside it reproduces every number.

## The pictures

All three are monochrome. The plate's process, blue-sensitive or orthochromatic, is not recorded,
so both are tested.

| print | light | what it can say |
|---|---|---|
| Taylor 16554, from the south-west | winter, overcast, no cast shadows | the cleanest: stable, palm house range and house in one soft light, none of them clipped |
| Taylor 1445, from 18th and Prairie | overcast | the stable far off, its wall and its slate in one light |
| Inland Architect plate, 1894 | high sun | weak: the lit walls (201-202), the sidewalk (207) and the sky (206) all print at the paper's top, so nothing lit can be told apart |

## What they show

In the winter print the stable's south wall prints 141-148, its own slate roof 146, the house's
mansard slate 141 and the house's brownstone 129 (sky 206, print black about 30). Taken through
the tone curve (gamma 1.8-2.2), the stable's wall is 1.4-1.5 times as bright as the brownstone and
1.0-1.1 times its slate roof. A roof faces the sky and takes more of it than a wall does, so the
wall's own reflectance is somewhat over the slate's. Taylor's 1445 agrees: the wall prints 134-136
against its slate's 116.

The palm house range beside it prints 126-143 in the same print: the same stone family as the
stable, not lighter.

| hypothesis | ratio to slate, blue plate | ortho plate |
|---|---|---|
| brownstone, as the house | 0.92 | 0.99 |
| the draft's stone, as the stable was built | 2.55 | 2.72 |
| the light stone the palm house range was built in | 4.65 | 4.85 |
| **chosen: the draft's stone at 0.58 of its value** | **1.48** | **1.58** |

The draft's stone would print well over the slate (2.5-2.7 times), and the range's light stone
nearly five times over it. Either would sit near the sky's tone in the winter print, where both
print at about the slate's. The chosen tone prints a little over the slate and about 1.5 times
the brownstone, which is what the print shows.

## What was changed

- **The stable** (`pullman_house_1729_prairie_ranges`): its walls take the draft's stone at 0.58
  of its value, linear (0.232, 0.209, 0.168), its hue kept, and its dressed trim (sills, surrounds,
  belts) a shade lighter, (0.26, 0.235, 0.19). The prints show the trim in the walls' own stone.
  This is set in the record's `draft_elevation.tint`, so no other draft changes.
- **The palm house range** (`pullman_house_1729_prairie_conservatory`, its `host_wall.color`): the
  same stone as the stable, from (0.66, 0.62, 0.54), and with it the range's rusticated face, its
  pilasters and its cornice, which the K13 kit had drawn in its own light `stone` (0.74, 0.70,
  0.62) over the wall: they are the wall's stone now (`host_stone`). The drum's columns and the
  conservatory's dressed stone are the K13 kit's lighter stone and are left: in both lit prints the
  columns print lighter than the walls behind them (the plate 166-188 against 130, Taylor's 16555
  113 against 93).
- The slate roofs are left as they were: neutral, as slate is.

## What it does not settle

The hue. A grey level fixes a surface's value in the plate's band, not its colour. A warm grey-buff
sandstone and a light brown sandstone of the same value print alike. The draft's warm grey-tan hue
is kept because nothing here argues for another; a written specification of Beman's 1892 work or
a colour view would settle it.
