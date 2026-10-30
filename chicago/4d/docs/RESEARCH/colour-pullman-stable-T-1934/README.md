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
mansard slate 141 and the house's wall 129 (sky 206, print black about 30). Through the tone curve
(gamma 1.8-2.2), the stable's wall reflects **1.37-1.47 times the house's wall** and 1.0-1.1 times
its slate roof. The palm house range beside it prints 126-143 in the same print: the same stone
family as the stable, not lighter.

## Which comparison to trust

Two walls in one soft light are the safer pair. A roof faces the sky and takes more of an overcast
sky's light than a wall does, so a wall-to-slate ratio in this print reads walls darker than they
are. The house shows how much: here its wall prints a little under its own mansard (0.9 times), but
in the Detroit print and Taylor's 1445 its walls print 1.7-3.3 times its slate
(`docs/RESEARCH/pullman-stone-1881/`, T-1881). So the stable is set against the house's wall, which
T-1881 laid in K02's `sandstone_fawn` from those two prints.

This replaces a first reading made against the slate alone, which set the stable at the draft's
stone x 0.58 (about the fawn's own value). After T-1881 that reading would have put the stable as
dark as the house, where the print has it clearly lighter.

| hypothesis | to the house's fawn wall, blue plate | ortho plate |
|---|---|---|
| the light stone the palm house range was built in | 3.22 | 2.99 |
| the draft's stone, as the stable was built | 1.77 | 1.68 |
| first reading: the draft's stone x 0.58 | 1.02 | 0.98 |
| **chosen: the draft's stone x 0.83** | **1.47** | **1.40** |

The print wants 1.37-1.47.

## What was changed

- **The stable** (`pullman_house_1729_prairie_ranges`): its walls take the draft's stone at 0.83
  of its value, linear (0.332, 0.299, 0.241), its hue kept, and its dressed trim (sills,
  surrounds, belts) a shade lighter, (0.372, 0.335, 0.27). The prints show the trim in the walls'
  own stone. This is set in the record's `draft_elevation.tint`, so no other draft changes.
- **The palm house range** (`pullman_house_1729_prairie_conservatory`, its `host_wall.color`):
  the same stone as the stable, from (0.66, 0.62, 0.54). The range's rusticated face, its
  pilasters and its cornice go with it. The K13 kit had drawn them in its own light `stone`
  (0.74, 0.70, 0.62) over the wall; they are the wall's stone now (`host_stone`). The drum's
  columns and the conservatory's dressed stone are left in the kit's lighter stone: in both lit
  prints the columns print lighter than the walls behind them (the plate 166-188 against 130,
  Taylor's 16555 113 against 93).
- The slate roofs are left as they were: neutral, as slate is.

## What it does not settle

The hue. A grey level fixes a surface's value in the plate's band, not its colour. A warm grey-buff
sandstone and a light brown sandstone of the same value print alike. The draft's warm grey-tan hue
is kept because nothing here argues for another; a written specification of Beman's 1892 work or
a colour view would settle it. The value also leans on T-1881's reading of the house; if that
changes, this follows it.
