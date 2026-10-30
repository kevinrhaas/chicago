# 1729 Prairie's stone, read off its prints (T-1881)

The owner's report of 2026-10-29, item 3: "The walls read as red brick. Up close the
brownstone renders with brick-like courses and a red tone. Every picture shows dressed
ashlar, light in the prints. Check the K02 stone's course size and tone against the
pictures." This note does that, with the method of `docs/RESEARCH/colour-1700-block-T-3244/`:
a black-and-white print cannot name a colour, but two surfaces in the same light bound
each other's value.

## Tone

`meas.py` reproduces the table (the Detroit boxes need the LoC master scan, 20 MB, not
committed; the command is in its header).

| picture | walls (lit) | slate mansard | other |
|---|---|---|---|
| Detroit print, LoC det 4a08065, master scan | 115-135 | 73-101 | sky 226 |
| Taylor no. 1445 (washed, highlights compressed) | 193-204 (one shaded run 171) | 165-175 | coping wall 197 |

Through a print's tone curve (gamma 1.8-2.2, black 7) the Detroit walls reflect
**1.7-3.3 times** the slate's light. Both pictures put the walls lighter than the slate,
and Taylor's puts them near the lot's stone coping wall.

The same ratio, measured on the photo-match render through the Detroit camera (linear,
blue / orthochromatic / eye weighting):

| build | wall / slate |
|---|---|
| K02 `sandstone_brown` (before) | 1.4-1.7 (eye 2.0-2.5) |
| first `sandstone_fawn` trial, mean sRGB 163,147,124 | 3.8-4.6 (too light) |
| **`sandstone_fawn`, mean sRGB 146,131,110 (built)** | **2.6-3.4** |

The red-brown sat under the print's range, and on any plate of the time a red-brown
stone prints darker than a neutral slate. The fawn is set in the upper half of the
range because the model's slate (linear about 0.05) is darker than most slate. Its
hue is reconstructed; only its value is bounded (`docs/LIBERTIES.md`
L-k01-1729-pullman-stone-tone-1881).

## Courses and joints

On the master scan, the second storey's plain wall beside the south pavilion shows
courses of about 0.44 m and blocks of 0.9-1.3 m. Both are inside K02's brownstone profile
(0.25-0.46 m, 0.6-1.5 m), so the course size was not what read as brick. The joints were:
hairlines barely darker than the face in the print, where the profile laid a 6 mm joint
struck 3 mm deep, drawing a dark line round every block. `sandstone_fawn`'s profile lays
3 mm, rubbed flush.

## What changed

- K02 gained `sandstone_fawn` (the generator, its maps, manifest, contact sheet,
  profile and K14 response; the six fabrics before it regenerate byte-identical).
- `pullman_house_1729_prairie` lays its walls, dressings and dormer faces in it.
- Its three match records gain the tone as a fixed difference.

The register still says brownstone and the record's material stays `inferred`. No other
house changes.
