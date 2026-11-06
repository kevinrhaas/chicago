# Prairie Avenue's face brick, house by house (T-3385)

The owner, 2026-11-05, on a 1600-block view in 1904: the brick "looks excellent with nice
variations", but "it might be more like a chicago common ... maybe it would be on sides, but
this is prairie avenue and they would have nice face brick and it would be different for
houses ... use that base model and probably add more versions with tuned color and material
based on the correct time period"; and "look at the photos of the building and do your best
to infer what the color and type of brick would have been".

Until this ticket every K01 brick wall on the street, front and flank, wore the one K03
common-buff panel at the one colour (1700-1708, 1918, 1919, 2009, 1812 and 1834 excepted,
whose fronts earlier tickets had already read off their photographs).

## What the period did

- **Common brick on the sides and rear.** Chicago's own brick, made from the lake-bed clay,
  is high in lime and fired in scove kilns "shades of salmon or buff rather than the reds,
  creams, and browns seen in other regions"; it was the brick of "places generally obscured
  from street traffic": side and back walls, flues, the backing behind a front
  ([Chicago Reader](https://chicagoreader.com/blogs/everything-you-ever-needed-to-know-about-the-chicago-common-brick/);
  [Brick of Chicago](https://www.brickofchicago.com/chicagocommon): commons "buff yellow,
  salmon pink, or deep red", with kiln flash spots; [Wikipedia](https://en.wikipedia.org/wiki/Chicago_common_brick):
  commons went into the inner wythes of a multi-wythe wall, a facing brick outside).
- **Pressed face brick on the front.** The street elevation took a dearer, dry- or
  hydraulic-pressed face brick with sharp arrises, laid in thin joints: "generally used for the
  most important elevation of a home", the commons on the party and exposed side walls
  ([House History Man](https://househistoryman.blogspot.com/2012/02/pressed-brick-or-not-pressed-brick-that.html)).
  Chicago's fronts were brought in from cleaner clays: "the smoother, cleaner clays from areas
  like Pennsylvania and St. Louis" (Brick of Chicago).
- **The colours by decade.** Before the pressed reds arrived in number, Milwaukee's cream lake
  brick was exported to Chicago ([Cream City brick](https://en.wikipedia.org/wiki/Cream_City_brick):
  "widely exported ... to American cities such as Chicago"); it is porous and darkens with the
  city's dirt. The 1870s and 1880s front is the red pressed brick (the Field house, 1873:
  "red brick with stone trim", [Dr. Loihl's Journal](https://drloihjournal.blogspot.com/2021/08/history-of-the-marshall-field-mansion-and-family.html));
  darker reds and browns follow in the 1880s, and golden buffs about 1890.

## What the pictures say

`idpass.mjs` renders, from each reference view's own fitted camera
(`data/reference_views/`), which material of the build covers each pixel and which way its face
looks; `tone_read.py` takes the picture's median grey inside the build's own front brick, side
brick, light dressings and slate, each mask eroded so a camera fit's few pixels of error stay
off the edges; `classify.py` turns two medians into a reflectance ratio with T-3244's print
model (`value = black + (white - black) * (R / R_white) ^ (1 / gamma)`, gamma 1.8-2.2) and
tests the palette against it on a blue-sensitive and an orthochromatic plate. Drawings and
engravings are left out (their tones are hatching, not reflectance), as are crushed halftones.
77 views were measured; the readings that decide something:

| house | picture | reading | ruling |
|---|---|---|---|
| 1905 (Field) | Daily News print | front brick 0.39-0.46 of its slate (red; a buff reads ~1.5) | pressed red front |
| 1905 (Field) | 1893 Rand McNally plate | front level with its slate, well under its stone | (agrees: not buff) |
| 1816 (Henderson) | Chicagology | front 0.65-0.70 of its slate, flank ~0.95 | pressed red front, common sides |
| 1637 (Spalding) | Grosvenor as-built | front under 0.1 of its slate; flank 0.50-0.57 of its dressings (common buff's 0.50-0.55) | deep red pressed front, common buff sides |
| 1834 (Jones) | Chicagology, GHM | front 0.08-0.14 of its dressings (deep red); flank 0.54-0.70 (common buff) | front kept (T-3093's tone); sides common buff |
| 1812 (Wheeler) | Levy | front 0.41-0.48 of its slate; flank 1.2 | front kept (T-3093) |
| 1625, 1828, 1900, 1612 | flanks | 1.1-1.2 of slate, or near their dressings | common buff sides, unchanged |
| 1945 (Armour) | 1928 Tribune halftone | crushed to black, no tone | period pick |

Every photographed brick front on the street reads RED, and every photographed side wall reads
a pale common: the pattern the owner described. A plate cannot tell a buff from a salmon or a
yellow common (all three sit near 0.5 of a limestone dressing on either plate), so which kiln
run a house's commons came from is a reconstruction; that they are commons is read.

Unclear and left alone: 1811's flank reads light in one print and dark in two; 1815's flank is
in shade in its only oblique view; 1824's front strip is a shaded porch.

## The palette

`data/components/prairie_1904/k03_face_brick.json`. Every recipe is one of the two K03 panels
1904 already loads (`common_buff_common_6`, `rough_red_brown_running`), unchanged, under a colour
factor (the recipe's linear mean over the panel's, each channel in [0, 1]) and a roughness shift
(a pressed face is smoother). No map is added: 1904's phone build sits at its memory ceiling.
The renderer's per-brick shuffle (T-3295) runs on every one of them, so the "nice variations"
the owner liked are kept.

| recipe | role | panel | linear mean | roughness | period |
|---|---|---|---|---|---|
| pressed_red | face | common | 0.300, 0.075, 0.048 | -0.10 | 1865-1890 |
| pressed_red_deep | face | red-brown | 0.197, 0.050, 0.035 | -0.08 | 1875-1895 |
| red_brown | face | red-brown | as the panel | 0 | 1885-1910 |
| pressed_brown | face | red-brown | 0.140, 0.075, 0.050 | -0.06 | 1880-1895 |
| pressed_buff | face | common | 0.391, 0.251, 0.115 | -0.08 | 1885-1905 |
| cream_sooted | face | common | 0.375, 0.251, 0.154 | -0.04 | 1850-1875 |
| common_buff | common | common | as the panel | 0 | |
| common_salmon | common | common | 0.407, 0.220, 0.139 | +0.02 | |
| common_yellow | common | common | 0.399, 0.256, 0.128 | 0 | |
| common_dun | common | common | 0.338, 0.218, 0.135 | +0.02 | |

A pressed red laid over the common panel stains its lime joints red with the brick: pressed
fronts were laid in thin joints of mortar coloured to the brick, so the front read as one
colour field. A fresh cream is not laid: the library has no paler panel than the common buff,
and a factor may not brighten one; by 1904 a cream front of the 1860s was smoke-dulled anyway.

## Who wears what

A record names its pick as `face_brick` (`front`, `sides`); `k01_frontage_params.py` reads it.

- **Read off photographs:** 1905 and 1816 pressed red, 1637 deep red, sides common buff.
- **Kept, already read:** 1700, 1706, 1708, 1918, 1919, 2009 (red-brown), 1812 and 1834 (toned
  fronts), 1701 (buff, T-3244), 1620 (painted olive), 1736 (painted), and the houses other
  threads hold (1729, 1801, 1808).
- **By decade, no picture of the brick:** 1600, 1616, 1730, 1923, 1945 pressed red; 1608, 1709
  deep red; 1604, 2003, 2005 brown; 1726 (c. 1890) buff; 1613/1615 and 1626/1628 (the 1860s
  pairs) smoke-dulled cream; 1721 (Arthur Little's 1889 front) red-brown.
- **Stone fronts, their commons:** 1619, 1621, 1623, 1634, 1636, 1712, 1823, 1906, 2001 a
  salmon, yellow or dun run each, so the street's flanks are not one colour.

Every pick without a reading is liberty L-k03-face-brick-3385.

## First Presbyterian Church, 2029 Indiana (T-3386)

A district draft, so until T-3386 its walls were the draft's flat brick colour with no texture.
The 1911 sheet colours it brick; through T-3066's camera the Otis 1887 plate reads its wall brick
at 0.53-0.60 of its slate spire, and the 1912 plate its flank at 0.51-0.57: red on either plate.
(Against its light dressings the 1887 wall reads 0.79-0.82, which fits neither a red nor a buff
well; slate is the reference this method reads every house against, so that reading is kept.)
A draft record may now name `face_brick` `{front}`; `prairie_draft.to_glb` then lays that recipe's
K03 panel on every brick face (the same maps a K01 wall embeds, so the shuffle finds it and the
phone decodes the picture once) with K01's metre UVs. The church wears pressed red.

## The 1812 and 1835 brick (T-3387)

Two hand-made period recipes join the palette: `soft_mud_red_garrison` (the forts' brick: a soft,
sand-struck, clamp-burnt red, its colour the sheet's brick row a shade darker) and
`soft_mud_salmon_lake` (Blodgett's North Side yard of 1833, Chicago's first; the lime-rich lake
clay burns salmon to buff). A `fort_structure` record names them as `period_brick` (`walls`,
`stacks`). The archetype gives the mesh a first UV layer registered in metres on the brick faces
(the exporter's TEXCOORD_0, the one the renderer keeps; emit.py's smart projection writes the
second) and wires the K03 common panel's two maps under the recipe's factor. Worn by: the 1803 and
1816 magazines and the 1816 commandant's quarters (walls), the Lake House (walls, lake-clay), and
the stacks of all ten fort buildings that have them. Liberty L-k03-period-brick-3387.

Where it stops: the 1835 Cook County courthouse (`outbuilding`, 245 records on that builder), the
Sauganash's brick stacks (`frame_tavern`) and the brick chimney heads of the town's framed houses
(`frame_dwelling`, 272 records) still wear the flat sheet colour; each needs the same hook in its
own builder and a rebake of every record on it.
