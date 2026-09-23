# The calibration reference photograph — committed 2026-08-15

`dupage_tallgrass_2018-07-24.jpg` — Cassi Saari, *Restored tallgrass prairie in DuPage
County, Illinois*, 24 July 2018, **CC BY-SA 4.0**, via Wikimedia Commons. Source record:
`data/sources/saari_2018_dupage_tallgrass.json`. Licence row: `assets/LICENSES.md`.

**Why it is here.** The renderer's sky is measured against this photograph — `world.js`
derives `SKY_EXPOSURE`, the whole of `HORIZON_RESTORE` and the haze colour from readings
taken off it, and `trees.js` reasons about crown-against-sky contrast from it. Until now
the file existed only in a working directory: the numbers were quoted in the code and
nobody could check them. An uncitable calibration reference is a calibration nobody can
check, so the file is now in the repository at the exact bytes the readings came from.

## The bytes are the licensed bytes

SHA-1 `0da00f1178e7790b04c05364d78f7cb6a43992ae`, 3,251,548 bytes, 4032×3024 — identical
to the SHA-1 the Commons API reports for the file page's current version. It is
**verbatim and unmodified**, which matters twice: it is why the readings reproduce, and it
is why redistributing it here is not an adaptation under ShareAlike.

## Read this before deriving anything from it

**Do not.** This is a **measure-only** reference. Crop it, resample it, build a texture or
a colour LUT from it, and you have made an adaptation, which CC BY-SA 4.0 requires you to
release under CC BY-SA 4.0. Nothing in this project needs that: the file is read by
measurement code and never enters the scene. `tools/publish.sh` does not copy
`data/sources/`, so it is not on the published site either.

## The frame is solved

EXIF gives a 26 mm 35 mm-equivalent lens, so the 4:3 frame spans **53.1° vertically over
3024 px = 57.0 px/deg**. The sky/land step sits at **row 820**. Therefore:

    elevation(row) = (820 − row) / 57.0   degrees above the horizon

The frame reaches **14.4° above** the horizon and 38.7° below it, and the camera was
pitched **−12.1°** — a number the 2026-08-10 prairie sweep had already established
independently as "the photographer had tilted down ~12°", from a different direction
entirely.

Quote the elevation of any reading you take. Every disagreement this photograph has caused
in this project so far has come from two people measuring different parts of it.

## What reproduces, measured 2026-08-15

`python3 tools/measure_reference.py` (needs Pillow; prints and skips cleanly without it).

| reading | quoted in `world.js` | re-measured |
|---|---|---|
| band immediately above the sky/land step | (136,163,192) | (137,162,187) |
| sky at ~14.4° | (101,153,209) | (97,151,208) |
| sky at 8° | (125,165,205) | (119,163,206) |
| sky at 4° | (137,166,200) | (133,166,201) |

The residual is a few units in red and blue and is explained: the tool averages the full
frame width, the original readings were taken at the shot's own view azimuth, and the
model's horizon brightness is azimuth-dependent even where its hue is not (`world.js`,
"its one honest cost"). Nothing in the renderer was touched to make these agree.

**One quoted figure did not reproduce and is left standing as a question.** `world.js`
gives the bar's most distant land as (118,146,145), B−R +27. The 12 px immediately below
the step measure (106,130,140) here — darker, and the difference is that a naive band on
that row lands partly on the far treeline rather than on open sward. The original reading
has no stated recipe, so this is a recipe mismatch rather than a contradiction, and
whoever needs that number next should define where it is taken from before quoting it.

## What it is not evidence for

The 2026-08-10 sweep's own correction stands and is repeated on the source record: this is
a **restoration planting on a former agricultural field**, bought forb-rich, and it must
not be quoted for the flower load of unmanaged 1835 prairie. That target is 4–6 %, from
the never-plowed remnant, not the 12.91 % this frame carries. It is also a
looking-toward-the-sun frame and cannot supply an anti-sun sky.
