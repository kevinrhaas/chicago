# T-3136 — Glessner's sign-off reading

The sign-off (T-2761 → T-2854 → T-3028 → T-3117, now T-3140) asks for every match record to
read `matches` with nothing open. Before this reading, eight of the twelve read `differs`.
Four of them had nothing open, so the gate printed a verdict with no reason. One (HABS 14)
had its open work written inside an entry marked `fixed`. Two carried open text that
later tickets had already settled. And the discrepancy register still stood on a master
three generations old (`6b2cff4d…`). This piece is the reading half of the sign-off. It
builds nothing.

**Acceptance, stated before the work:** every `differs` record re-read on its current
side-by-side (GLB `6ba8c9f7…`). Each open difference is named precisely, its stale parts
struck, and its owning ticket named. Each record with nothing open is either given the
difference it still shows or ruled `matches`. The register is brought to the current master,
saying for each row what is attested and what is inferred.

## How it was read

Each side-by-side's two panels are drawn at one scale, so a column read on one panel can be
compared with the same column on the other. `ruler.py` stacks the print's strip (equalised)
over the render's for a band of rows, zoomed, with a ruler in panel pixels between them:

    python3 docs/RESEARCH/glessner-signoff-reading-T-3136/ruler.py \
      docs/RESEARCH/photo-match/glessner_house/habs-16-prairie-front-side-by-side.jpg out.jpg 545 600 895 1030 6

Jambs are read at the stone's edge on the print and at the outer frame on the render. These
are hand picks, good to about 2 px on HABS 13, 14 and 16 and about 1 px on Taylor 2135's
smaller image. Feet are scaled from the built opening widths in the same strip. The JPGs here
are the strips each reading was taken from.

## What each record now says

| view | before | now open | owner |
|---|---|---|---|
| HABS 13 | `differs`, nothing open | both gable pairs read as two about-equal lights (east wing about 3.1 + 3.1 ft against the built 3.35 + 2.85; tower shoulder about 2.9-3.0 each against 2.65 + 3.1), and the shoulder pair's jambs stand 15-27 px east of the render's | T-3142 |
| HABS 14 | `differs`, open work inside a `fixed` entry | T-3127's handover as its own entry: the transom stands about 0.3-0.5 ft under the build's, and the fan has fewer, broader stones than the 11 built | T-3137 |
| HABS 16 | `differs`, nothing open | the first-floor pair over the porte-cochère: north light 37.5 px and pier 21 px against the render's 47.5 and 14 (about 2.2 and 1.25 ft against the built 2.7 and 0.8); and the camera draws the front 7-20 px north of the print, growing away from the south corner | T-3141 |
| Taylor 2135 | `differs`, nothing open | the same pair: north light about 23 px and pier about 11 against 26 and 7.5; the pair stands about 15 px north of the print's | T-3141 |
| Cornell | `differs`, a catch-all "residuals remain" | the catch-all is resolved into what it held (all fixed elsewhere, or past the camera's reach and now `not shown`). New open entry: the north-gable pigeon holes, about a course tall in the print against the build's 0.45-0.65 ft slits | T-3143 |
| HABS 01 | `differs`, open | the cupola's corner strips are struck (T-3036 removed them, and the render shows none). The stable end's place through this camera stays open, and the pigeon holes and the ledge's height under the apex are added | T-3139, T-3143 |
| HABS 15 | `differs`, open | unchanged; owner named | T-3139 |
| HABS 17 | `differs`, open | unchanged; owner named | T-3138 |

None could honestly be ruled `matches`: every one of the four that had nothing open shows
a difference at the scale it resolves. The four HABS sheet-4 and HABS 5 records already read
`matches` and are not touched.

## The pair over the porte-cochère, read twice

S runs south from the north end, so the pair's north light is S 63.5-66.2. In HABS 16
(facing west) and in Taylor 2135 (from the north-east) it is the right-hand light.

| | south light | pier | north light |
|---|---|---|---|
| built (ft) | 2.3 | 0.8 | 2.7 |
| HABS 16, print / render (px) | 40 / 41 | 21 / 14 | 37.5 / 47.5 |
| Taylor 2135, print / render (px) | 21.7 / 21.3 | 10.8 / 7.5 | 23.3 / 25.8 |
| both prints (ft) | 2.3-2.4 | 1.1-1.25 | 2.2-2.4 |

Two prints, 78 years apart, agree, so this is attested. The record gives the front ±0.3 ft
from sheet 6, so T-3141 reads the pair on sheet 6 before anything is rebuilt.

## The register

`../glessner-final-comparison-T-2228/discrepancies.json` now stands on master `6ba8c9f7…`:

- **ruled (2):** `terrace-post-join` and `tower-plan-section`, both settled by T-2879's ruling
  that the plan governs and sheet 4 is shifted north. Both HABS 4 records read `matches`.
- **superseded (2):** `north-correspondence` and `prairie-correspondence`, two catch-alls
  replaced by the specific rows that follow.
- **open (7), each with its basis and its ticket:** north gable pairs (inferred, T-3142),
  the gable light's transom and fan (inferred, T-3137), the 18th Street stack's proportion
  (inferred, T-3138), the Prairie pair (attested, T-3141), HABS 16's camera scale (camera,
  T-3141), the stable-end cameras (camera, T-3139), and the stable's pigeon holes (attested in
  form, T-3143).

`final_acceptance` stays `false`. Writing it is T-3140's job, once these seven are fixed or
ruled.
