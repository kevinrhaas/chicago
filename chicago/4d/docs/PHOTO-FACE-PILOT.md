# Photo-face pilot: sixteen faces to review

The review library is separate from resident assignments. Its sixteen fictional adult sources
are generated images, not archival photographs or a dataset of living people. Each is fitted
with the existing portable-human morph kit, then its visible facial colour is mapped through
the calibrated landmarks to the hm08 face island. A small portable scalp surface carries the photographed front hair, with source-matched colour
for unseen strands and source-bounded crown height/width. It shares the existing head joint;
Light uses 440 scalp triangles and Full uses 1,216.

Serve `chicago/4d` with `python3 -m http.server 3000` and open:

```
http://localhost:3000/tools/photo_face_review.html
```

Choose a face, compare the source with the existing skin and the fitted result, and inspect
front, three-quarter and profile views. **All faces** shows the sixteen actual rendered heads.
The source, before and after are deliberately separate: a plausible result is not evidence of
an exact historical likeness. No resident has been assigned one of these samples.

## Inspect the generic population before rollout

Append `&photoFaces=pilot` to a walk URL (for example, `walk/?year=1904&photoFaces=pilot`).
This opt-in preview assigns the photo library to existing generic adults, fits their face
values, preserves their recorded complexion, and applies the softer source-based eyes.
Personal portrait fits and visitor-chosen faces take priority; children retain the ordinary
library until their bodies are calibrated. Assignment is seeded by the person's id, sex,
age and recorded complexion, and remains the same across their body LODs.

The town preview shares one 512-square face atlas (1.33 MiB including mipmaps), keeps the
existing hair layer, and adds no render pass. The separate review page compares the new
photographed-hair proposal. Libraries above the town preview's 1.4 MB texture ceiling
are refused; expansion requires bounded nearby pages. No default assignment changes.

For actual resident models, `tools/human_variation_lineup.html?asset=auto&keys=` followed
by their ids and `&view=faces&dress=1&photoFaces=pilot` uses the same population path.

The scene-assignment check covers all 1,234 currently drawn people: 1,048 generic adults
receive a photo on 1,076 body assignments; 160 child and 27 personal-face assignments
remain protected. A person drawn on several bodies keeps the same face on each.

## Import one historical photograph

Use an actual photograph of the intended person where one exists. Read it, register its credit,
locator and texture rights in `data/sources/<source>.json`, and preserve the original. The
importer refuses a missing source or uncleared texture rights. With the Python dependencies and
landmarker described in [PHOTO-FACES.md](PHOTO-FACES.md), run:

```
python3 tools/photo_face_library.py --photo /path/to/portrait.jpg \
  --id HISTORICAL_PERSON_ID --source REGISTERED_SOURCE_ID --sex male --age 60 \
  --model /path/to/face_landmarker.task --output work/photo-faces/person
```

Open `tools/photo_face_review.html?library=work/photo-faces/person/review.json`. The command
creates the fitted values, source credit, source preview, shared texture and a reproducible
recipe. It writes no resident, existing portrait, existing likeness or town kit. Intended person
ids may be used as stable face ids; previewing a Glessner, Field or Pullman is not an assignment
to that person's record. Appearance ages are the ages in the picture, separate from census ages.

A source with several people needs a crop containing one face. The batch recipe's `crop_px`
is an integer rectangle on the EXIF-oriented image. A four-view head sheet and the older
`photo_face.py` path remain useful where real side views are available.

## Rebuild the sixteen-face library

```
python3 tools/photo_face_library.py --batch data/humans/variation/photo_face_pilot.json \
  --output assets/humans/web/photo_faces/pilot
python3 tools/photo_face_library.py --check assets/humans/web/photo_faces/pilot/review.json
```

The recipe pins the original sheet, crops, 478 detected landmarks per face and fit inputs.
Rebuilds need no landmark model or network. Changed fit inputs refit from the pinned landmarks;
changed source bytes are refused until explicitly registered again. Initial import needs
`--model`; the synthetic source batch also uses `--frontal`. Source and generated files carry
provenance in `assets/LICENSES.md` and `synthetic_photo_face_pilot_2026`.

## Budget and hardware measurement

| Review detail | Shared face and hair atlases | Added RGBA8 texture memory, including mipmaps | Body LOD |
|---|---|---|---|
| Light | two at 512 × 512 | 2.67 MiB total | 2 |
| Full | two at 1024 × 1024 | 10.67 MiB total | 0 |

Those are bounds for **all sixteen faces together**, excluding the existing body textures,
geometry, driver overhead and page images. There are no added render passes for a face patch;
the shared skin shader samples the face atlas and the review hair pass samples the source hair atlas with its photographed hairline mask. Eight pixels of duplicated border surround each
full-size tile. The shader excludes the border from its UV transform. Light caps pixel ratio
at 1 and leaves shadows off. Phones can additionally downsample via the existing skin loader.

**Measure on this PC** warms up, draws all faces for sixty measured frames and exports a JSON
record with viewport, LOD, renderer name, draw calls, triangles, median and p95 frame intervals,
submission time and atlas bytes. It explicitly flags software renderers. This isolates the
pilot; it does not certify the complete town or substitute for a weak-PC hardware test.

One pair of atlases supports up to 64 entries without code changes (full two at 2048²,
42.67 MiB total; light two at 1024², 10.67 MiB total). Expansion should use bounded,
nearby pages before population rollout. Unlimited
photo textures retained for the whole page's lifetime are not a solution to the memory budget.

## What still needs review

Single-photo fits cannot establish nose projection, cheek depth, the jaw from the side, hidden
ears or hair. The starter library uses the existing head-depth priors and reconstructed hair
volume, body and clothing. Only the front hair is photographed; unseen sides and back use
small procedural strands in a colour measured from the source. Sclera brightness and iris
colour are measured from each image; the iris texture is adjusted relative to its original
tone, preserving its detail. Source pupil positions and iris radii guide bounded corrections
to the existing separate eyes, the measured aperture sets the resting lids, and the corneal
glare is reduced. Recorded historical eye colours retain priority. These corrections still
need visual review and do not establish exact eye or hair correspondence. Use real side photographs and the existing
profile-trace tools to resolve a historical likeness. No invented side picture is treated as
historical evidence. Review likeness and a hardware crowd measurement before wider assignment.
