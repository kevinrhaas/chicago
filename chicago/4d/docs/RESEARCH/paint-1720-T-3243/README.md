# 1720 Prairie's body paint, read from the Tyrrell photograph (T-3243)

The owner, 2026-10-29: *"was it white the pictures do not appear that way to me, you need to make
sure that you picture match analysis on what the most likely color would have been according to
research and hypothesis analysis"*. The model had the body at linear (0.80, 0.77, 0.68), sRGB about
(231, 227, 215): near-white, a shade off the trim's (0.91, 0.88, 0.79).

## What the picture can say

The only photograph (`glessner_blog_1720_tyrrell_photo`, 1200 x 1119 px greyscale, camera
`data/reference_views/walker_house_1720_prairie/tyrrell_front.json`) is monochrome, so it cannot
give a hue. It can give a **tone relative to things in the same light**: the clapboard of the
upper storey, the porch's posts (trim) and the stone posts on the street line all face east and
stand in the same sun. Undated; the Prairie library brackets it 1868-1910, and its subject is the
Tyrrell house, so it is most likely a plate of the 1870s-80s, a blue-sensitive (collodion or early
dry) emulsion: orthochromatic plates were not in common use before the late 1880s.

## Measured (grey levels, 0-255, on the store's copy)

| patch (sunlit, east-facing) | px box (x0,y0,x1,y1) | mean | median |
|---|---|---|---|
| clapboard between the middle window and the pair | 680,360,740,420 | 154 | 155 |
| clapboard left of the middle window | 450,380,540,425 | 153 | 154 |
| clapboard right of the pair | 900,330,975,420 | 144 | 150 |
| porch post, north inner pair (trim) | 612,620,628,780 | 154 | 174 (p90 193) |
| porch post, south inner pair (trim) | 418,620,432,780 | 162 | 176 (p90 193) |
| stone post at x 785 | 775,905,800,1000 | 170 | 171 |
| stone post at x 955 | 945,900,970,1000 | 167 | 168 |
| window blinds (white textile) | 780,330,815,410 | 185 | 192 |
| deepest shade (balustrade rail) | 680,804,920,814 | 93 | 95 (floor about 15) |

The body prints **20-40 levels darker than the trim and 15 levels darker than the stone posts in the
same light**. A white or near-white body would print with the trim.

## Hypotheses, predicted against the measurement

Each candidate paint (linear RGB) is turned into a print tone against the trim (taken as the model's
cream-white, linear 0.91, 0.88, 0.79, printing at 185) by the plate's spectral weighting and a print
gamma of 1.8 / 2.2 over a floor of 15. Script: `tone.py` below.

| hypothesis | sRGB | blue plate | ortho | eye |
|---|---|---|---|---|
| H1 white lead | 237,236,231 | 185/185 | 183/184 | 181/181 |
| H2 the model before (near-white) | 231,227,215 | 172/174 | 172/174 | 173/175 |
| H3 the K16 kit's cream | 229,219,197 | 158/163 | 161/165 | 166/170 |
| **chosen: light stone / fawn** | **209,199,179** | **142/149** | **145/151** | **149/155** |
| H4 darker stone / fawn | 203,192,173 | 137/145 | 140/147 | 144/151 |
| H5 medium drab | 170,158,137 | 108/118 | 111/121 | 116/126 |
| H6 light neutral grey | 179,179,179 | 138/145 | 135/143 | 132/140 |
| H7 olive drab | 137,134,97 | 80/93 | 88/100 | 96/108 |
| H8 brown / red | 149,108,85 | 71/83 | 75/87 | 85/97 |
| H9 straw / yellow | 218,196,124 | 109/119 | 125/134 | 147/153 |

Measured body: **150-155**.

- **Rejected:** white and near-white (H1, H2) print 17-30 levels too light, level with the trim; the
  dark fashionable colours of the late 1870s-80s (H5 drab, H7 olive, H8 brown/red) print 30-80 levels
  too dark; a strong yellow (H9) fits only if the plate saw as the eye does, which a plate of that date
  did not.
- **Fits:** a light warm stone colour between the kit's cream (H3) and a fawn (H4): a buff/fawn
  "stone colour" whose blue reflectance is about 0.45-0.5 of white's. A light grey (H6) fits about as
  well on the tone alone.

## Research priors

- 1720 was built in 1868 (Otis L. Wheelock, architect; the register's dating). The pattern books of
  that decade that set the taste for frame villas (A. J. Downing, *Cottage Residences* and *The
  Architecture of Country Houses*, 1842/1850; Samuel Sloan, *The Model Architect*, 1852, and later
  editions) argued against white for country and suburban houses and for "neutral", "fawn", "drab"
  and "stone" colours, with the trim a few shades lighter or darker in the same family. An
  Italianate frame house of 1868 imitating a stone villa (its arched heads, quoin-like corner boards,
  heavy bracketed cornice) is the textbook case for a stone colour.
- The darker, multi-colour schemes (olive, brown, Indian red; the 1880s paint-company cards) came
  after the house was built and the tone rules them out for the photograph's date anyway.
- Warm stone colours were far more usual than cool greys on frame houses of the 1860s, so the warm
  reading is preferred to H6 on the prior, not on the tone.
- The photograph shows the trim (posts, balustrade, casings) lighter than the body: built so, the
  kit's cream-white trim kept.

## Ruling

Body paint linear (0.64, 0.57, 0.45), sRGB about (209, 199, 179): a light fawn / stone colour, the
middle of the band that fits the print, with the trim kept cream-white. Read: the body darker than
its trim and its stone posts, by the photograph (inferred). Reconstructed: the hue, from the period
taste, and its survival to the 1904 scene (repaints between the photograph and 1904 are unrecorded),
in `L-k16-1720-frame-house-3180`'s T-3243 revision.

How to resolve: a coloured view (a lithograph, a postcard), a paint-scrape finding, or a written
description of the house's colour.

## tone.py

```python
import numpy as np
trim = np.array([0.91, 0.88, 0.79])
bands = {'blue': np.array([0.05, 0.15, 0.80]), 'ortho': np.array([0.05, 0.45, 0.50]),
         'eye': np.array([0.2126, 0.7152, 0.0722])}
b, w = 15.0, 185.0
def tone(c, k, g):
    r = (np.array(c) @ k) / (trim @ k)
    return b + (w - b) * r ** (1 / g)
# tone((0.64, 0.57, 0.45), bands['blue'], 2.2) -> about 149; bands['eye'] -> about 155
```
