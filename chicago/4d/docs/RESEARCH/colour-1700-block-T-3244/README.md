# The 1700 block of Prairie Avenue: colours read from its pictures (T-3244)

The owner's report of 2026-10-29, on 1720 Prairie: "was it white the pictures do not
appear that way to me, you need to make sure that you picture match analysis on what the
most likely color would have been according to research and hypothesis analysis, this
holds for everything on the block". 1720 was settled first (T-3243,
`docs/RESEARCH/paint-1720-T-3243/`). This note does the same for every other house on
the block that has a picture, and says what was changed and what was left alone.

## Method

Every picture here is black and white. A grey level alone cannot name a colour, but the
ratio of two surfaces in the same light can rule colours out. For each pair the print
value is modelled as

    value = black + (white - black) * (R / R_white) ^ (1 / gamma)

with `gamma` 1.8 and 2.2 (the usual range of a print's tone curve), and `R` a surface's
reflectance as the plate saw it: the 1880-1905 plates were blue-sensitive (weights
0.05, 0.15, 0.80 on linear R, G, B) or orthochromatic (0.05, 0.45, 0.50); the eye's
weights (0.2126, 0.7152, 0.0722) are given for comparison. Surfaces are measured on the
source scans with `meas.py` (median grey of a box). Two references are used:

- **white paint** (linear 0.91, 0.88, 0.79): a column or a sash frame the eye agrees is
  painted white;
- **the house's own slate** (a neutral grey, linear about 0.12): a cross-check that does
  not depend on where the print's white sits, because slate is neutral and every brick
  colour sits either side of it on a blue or orthochromatic plate.

The brick hypotheses use the K03 library's own panels (mean linear base colour of each
web map): common buff (0.407, 0.256, 0.154), rough red-brown (0.197, 0.098, 0.068),
pressed red (0.177, 0.024, 0.015). `tone.py` beside this note reproduces the table.

| hypothesis, ratio to white paint | blue plate | ortho plate | eye |
|---|---|---|---|
| common buff brick | 0.22 | 0.25 | 0.32 |
| rough red-brown brick | 0.10 | 0.11 | 0.13 |
| pressed red brick | 0.03 | 0.03 | 0.06 |
| slate (neutral 0.12) | 0.15 | 0.14 | 0.14 |

Buff brick prints lighter than slate on any plate; red brick prints darker.

## 1700 and 1706 Prairie (the Glessner pair, 1901)

Three pictures: Chicagology's view of the pair (high contrast, finished houses), the
Glessner House Museum's Christmas print (low contrast, highlights compressed: its sky is
182 and its whitest column 168), and the museum's construction photograph of 1901
(small, hazy, the porches not yet built, the brick new).

| picture | brick | white paint | slate | brick / white, gamma 1.8-2.2 | brick vs slate |
|---|---|---|---|---|---|
| Chicagology | 70-76 | 235-243 (porch columns) | 106-124 | 0.05-0.08 | darker |
| Christmas print | 95-110 | 163-168 (porch column, dormer) | 150-164 | 0.30-0.38 | darker |
| 1901 construction | 153-156 | none built; stone 227-229 | 156-215 | 0.39-0.46 (to stone) | darker |

**What the pictures agree on.** Porch columns, entablatures and balcony decks, the main
cornice, the dormers' faces and pediments, and the window sash and frames all print
white, at the top of each print's range, in all three. The model had them in a beige
stone (porches, dormers), a light grey-beige paint (cornice, linear 0.72, 0.70, 0.62)
and the kit's dark green sash.

**Where they disagree: the brick.** Against white paint, Chicagology's print puts the
brick between the library's pressed red and its red-brown; the other two put it near buff.
The two light readings are the weaker ones: the Christmas print's highlights are
compressed (its white column barely clears its sky), which lifts every mid-tone, and the
1901 brick is a fresh, mortar-smeared wall under construction dust, measured against
stone because no paint was up yet. The slate cross-check does not depend on the print's
white, and in all three pictures the brick prints darker than the house's own slate,
which a buff brick cannot do on a blue or orthochromatic plate. **Ruling: a red brick.**
Of the library's two reds, the red-brown (0.10-0.13) sits nearer the three readings
than the pressed red (0.03-0.06), and Chicagology's close view of the front shows light
joints between the courses, which the pressed red's tight dark joints would hide. Laid
with the K03 `rough_red_brown_running` panel, its units cut from the same brick; the
bond is not readable at the pictures' resolution, so the library's running bond. The
style agrees: a Georgian Revival pair of 1901 with white-painted porches, cornice and
sash is the period's red-brick scheme.

**Changed (T-3244):**
- brick: the K03 red-brown panel and units, every brick wall of both houses;
- cornice: white paint (linear 0.86, 0.85, 0.80), where it was a light grey-beige;
- porches: painted timber in that white instead of the beige stone they were laid in
  (their columns print whiter than the stone sills, 235-243 against about 170-200, and
  with the cornice and sash);
- dormers: their faces and pediments painted the cornice's white, not limestone;
- sash: painted white instead of the kit's dark green.

## 1708 Prairie

Two pictures, the same Chicagology view and Christmas print, plus the 1901 construction
photograph at its south edge. Its front prints as dark as the pair's brick in the
Christmas print and the 1901 photograph (147-157 against the pair's 153-156 in the same
light, 1901), darker than its own stone basement and cornice. **Ruling: the same red-brown
brick on its street front** over its stone basement; the side walls, which no
picture shows, stay K03 common brick. Its stone trim already reads light, as the model
has it.

## 1701 Prairie (Hibbard)

One street photograph (Chicagology) and a rear view. The brick prints mid-grey and well
under its light stone dressings; in the sunlit flank it reaches 175-190 against
quoins of 199-212, which a red brick cannot reach and a buff brick can. **Kept: buff
brick, light stone**, as T-3240 built it. The roof's painted tin is the kit's default
red oxide (a reconstruction recorded on the record); the photograph's low slopes print
light, but low-pitched metal takes the sky's glare at that angle, so the picture cannot
choose a paint. Left as reconstructed.

## 1720 Prairie (Walker)

Settled by T-3243: a light fawn / stone colour body (sRGB about 209, 199, 179) with cream
trim; white and the dark 1870s colours both ruled out.

## 1736 Prairie

Its photograph prints the walls near white; the model has them painted opaque near
white (T-2933). Consistent; nothing changed.

## 1729 Prairie (Pullman)

Brownstone, consistent in its pictures with the model's K02 brownstone. Its steward work
(conservatory, ranges, wall) is the Pullman lane's; nothing changed here.

## 1709 (Kellogg) and 1721 (Dexter)

Drawings only (a Rand McNally view, an Inland Architect plate): line work carries no
colour, so their colours stay the reconstructions their records name.

## 1712, 1726, 1730

No pictures. Their colours are the draft builder's reconstructions, recorded as liberties.

## The kit change

K03 gained a second panel a record may name (`k03_brick.PANELS`): `service_wall_brick`
lays every brick slot of a house in it, and `street_front_brick.panel` lays a stone
front's brick in it alone. K01 gained `sash_paint` (the sash's colour) and
`mansard.dormer_fabric: "painted"` (dormer faces in the cornice's paint). Every other
K01, K12, K13 and K16 build was re-emitted; none changed but these three.
