# Photo-face library: 256 adults and 16 children on dev

The library is enabled by default on dev in 1812, 1835, 1871 and 1904. Its 256 fictional adult sources
are generated images, not archival photographs or a dataset of living people. Each is fitted
with the existing portable-human morph kit, then its visible facial colour is mapped through
the calibrated landmarks to the hm08 face island. A small portable scalp surface carries the photographed front hair, with source-matched colour
for unseen strands and source-bounded crown height/width. It shares the existing head joint;
Light uses 440 scalp triangles and Full uses 1,216. The gallery defaults to the existing
reconstructed hair style in a source-measured colour. The Hair selector exposes the
photographed-scalp trial separately: skull placement is improved, but hairline/coverage
artifacts still need work and are not a finished replacement.

Serve `chicago/4d` with `python3 -m http.server 3000` and open:

```
http://localhost:3000/tools/photo_face_review.html
```

Choose a face, compare the source with the existing skin and the fitted result, and inspect
front, three-quarter and profile views. **Page gallery** shows sixteen actual rendered heads.
Previous/Next and the page selector cover all sixteen pages. Navigation reloads the viewer,
releasing the preceding page’s renderer, fitted bodies and textures. Only sixteen thumbnails
are requested per page. The catalog preserves the original sixteen and adds 240 new sources;
128 men and 128 women have apparent ages 18–87. These are appearance targets, not biographies.
The source, before and after are deliberately separate: a plausible result is not evidence of
an exact historical likeness. Generic residents receive stable, age-compatible assignments;
personal likenesses and visitor choices retain priority.

## Inspect the generic population on dev

Open a walk URL (for example, `walk/?year=1904`). No preview flag is needed.
The library supplies existing generic adults, fits their face
values, preserves their recorded complexion, and applies the softer source-based eyes.
Personal portrait fits and visitor-chosen faces take priority. Sixteen fictional child sources
cover apparent ages two through seventeen, using the same photographic style and eye treatment.
Children retain their existing head morphs, body proportions and native eye placement: only
texture, eye tone and resting lids are transferred. Their shared hm08 UV topology supplies
camera registration; this is not an independent child photogrammetry calibration.
Assignment is seeded by the person's id, sex,
age and recorded complexion, and remains the same across their body LODs.
Carriage drivers retain the existing face-only morph scope; body-wide head-outline
targets stay with their engineered body.

The town shares one 1024-square adult crowd atlas (5.33 MiB including mipmaps)
and one 512-square child crowd atlas (1.33 MiB).
Visible heads within six metres request sharper detail; the nearest page wins, with
hysteresis. One 1024-square page can be resident **or loading**, adding at most 5.33 MiB.
An evicted or failed page falls back to the same person’s crowd face. New requests wait
for an in-flight decode; late images are discarded, failed requests back off, and disposed
pages cannot be re-uploaded through old material bindings. The adult and child catalogs
add about 12 MiB of face textures in total. Adults and children
compete for the same single detail-page slot; they do not each retain one.
The existing hair layer, body LODs and visible-person limits stay in use, and face patches
add no render pass. The separate review compares the photographed-hair proposal.
Historical likeness textures use their existing separate cache. `&photoFaces=off` shows
the former generic appearance for comparison. Older `photoFaces=pilot` links still work.

For actual resident models, `tools/human_variation_lineup.html?asset=auto&keys=` followed
by their ids and `&view=faces&dress=1` uses the same population path.

The scene-assignment check reads both the shared population and the separate 1835 and 1871
tables, along with every inside-scene body assignment. It checks all four years, protects
personal likenesses, and compares every child's morph values, options, age and height with
the former appearance. A person drawn on several bodies keeps the same face on each.

To review the children's sixteen rendered heads, open
`tools/photo_face_review.html?library=assets/humans/web/photo_faces/children/review.json&gallery=1&quality=light`.

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

## Rebuild the 256-face library

```
python3 tools/photo_face_library.py --batch data/humans/variation/photo_face_pilot.json \
  --output assets/humans/web/photo_faces/pilot
python3 tools/photo_face_library.py --check assets/humans/web/photo_faces/pilot/review.json
python3 tools/photo_face_library.py --batch data/humans/variation/photo_face_children.json \
  --output assets/humans/web/photo_faces/children
python3 tools/photo_face_library.py --check assets/humans/web/photo_faces/children/review.json
```

The recipe pins the original sheet, crops, 478 detected landmarks per face and fit inputs.
Rebuilds need no landmark model or network. Changed fit inputs refit from the pinned landmarks;
changed source bytes are refused until explicitly registered again. Initial import needs
`--model`; the synthetic source batch also uses `--frontal`. Source and generated files carry
provenance in `assets/LICENSES.md`, `synthetic_photo_face_pilot_2026` (the original sixteen)
and `synthetic_photo_faces_256_2026` (240 additions). `--jobs 4` optionally parallelizes
offline fitting/baking; the app performs neither operation at runtime.

## Budget and hardware measurement

| Use | Shared face/hair textures loaded | Added RGBA8 memory, including mipmaps |
|---|---|---|
| Town crowd | adult 1024 × 1024 and child 512 × 512 sheets | 6.67 MiB |
| Town nearby detail | at most one additional face page at 1024 × 1024, shared across ages | 5.33 MiB; about 12 MiB town total |
| Review Light | one face page at 512 × 512; optional hair trial page | 1.33 MiB; 2.67 MiB with trial |
| Review Full | one face page at 1024 × 1024; optional hair trial page | 5.33 MiB; 10.67 MiB with trial |

The town limits apply to the whole 272-entry adult-and-child catalog. Other pages remain on disk until
needed. The review limits apply to its current sixteen-face page; navigation releases the
previous page. Light uses body LOD2, pixel ratio 1 and no shadows. Full uses LOD0 for close
inspection. Existing body/clothing textures, geometry, image decoding and driver overhead
are outside these **added face-texture** bounds. The town keeps its existing crowd limits.

Each full tile is 256 square with eight pixels of duplicated border. The compact crowd
sheet gives 64 pixels per face at 256 entries; the nearby page restores 256 pixels. If
several different pages are visible nearby, only the nearest page is sharp and the others
keep their smaller version. This is the deliberate low-memory compromise, not a change
of face identity. The shader uses the same face sampler when switching detail.

**Measure on this PC** warms up, draws the current sixteen heads for sixty measured
frames, and exports renderer, viewport, LOD, calls, triangles, median/p95 intervals,
submission time, catalog/page counts and atlas bytes. A 256-entry catalog does not mean
256 people are drawn in that measurement. Software renderers are labelled explicitly.
The measurement does not certify the complete town or replace a real weak-PC GPU test.

The importer refuses a 257th entry within one library and checks actual image dimensions and hashes. The
runtime refuses oversized crowd/detail metadata; decoded detail dimensions are checked
before upload. One resident-or-loading slot and page-failure/late-delivery behavior have
executable regression checks. The owner explicitly authorized this dev rollout. Whole-town
timing on a real low-power GPU remains unmeasured; software browser checks certify rendering
and cache behavior, not hardware frame rate.

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
