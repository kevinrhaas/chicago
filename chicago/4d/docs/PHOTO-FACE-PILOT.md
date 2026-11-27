# Photo-face library: 320 adults and 64 children on dev

The library is enabled by default on dev in 1812, 1835, 1871 and 1904. Its 320 fictional adult sources
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
Previous/Next and the page selector cover all twenty adult pages. Navigation reloads the viewer,
releasing the preceding page’s renderer, fitted bodies and textures. Only sixteen thumbnails
are requested per page. The catalog preserves the original 256 and adds 64 new references;
160 men and 160 women span young adults through old age. These are appearance targets, not biographies.
The source, before and after are deliberately separate: a plausible result is not evidence of
an exact historical likeness. Generic residents receive stable, age-compatible assignments;
personal likenesses and visitor choices retain priority.

## Inspect the generic population on dev

Open a walk URL (for example, `walk/?year=1904`). No preview flag is needed.
The library supplies existing generic adults, fits their face
values, joins photographic face and body colour, and applies softer source-based eyes.
Attested eye colours, personal portrait fits and visitor-chosen faces take priority. Sixty-four fictional child sources
cover apparent ages two through seventeen, using the same photographic style and eye treatment.
Children retain their existing head morphs, body proportions and native eye placement: only
texture, eye tone and resting lids are transferred. Their shared hm08 UV topology supplies
camera registration; this is not an independent child photogrammetry calibration.
Assignment is seeded by the person's id, sex,
age and existing community context, and remains the same across their body LODs.
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
The Grey full skin sheets retain their existing separate cache. The new named frontal-photo catalog shares the same single nearby page as generic adults and children. `&photoFaces=off` shows
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

## Rebuild the adult face library

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

The town limits apply to the whole 384-entry adult-and-child catalog. Identical crowd and Light review sheets share one file. Other pages remain on disk until
needed. The review limits apply to its current sixteen-face page; navigation releases the
previous page. Light uses body LOD2, pixel ratio 1 and no shadows. Full uses LOD0 for close
inspection. Existing body/clothing textures, geometry, image decoding and driver overhead
are outside these **added face-texture** bounds. The town keeps its existing crowd limits.

Each full tile is 256 square with eight pixels of duplicated border. The compact crowd
sheet gives about 57 pixels per face at 320 entries; the nearby page restores 256 pixels. If
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

## Forehead continuity

The photographic landmark hull ends below the hairline. The importer blends fine
facial detail near that measured boundary and spreads broad colour/lighting changes
across a wider area of the existing skin (T-3769). This removes the narrow forehead
band without blurring the face's detail. The blend is baked into the same RGB atlases;
head fits, child proportions, eye records, texture dimensions and the runtime page
budget are unchanged.

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

## Named people and existing portraits

`python3 tools/historical_photo_faces.py --all --jobs 4` registers and rebuilds all usable
retained portrait references. Open `tools/historical_photo_review.html` for the source,
previous appearance and applied face, with front/three-quarter/profile and Light/Full
controls. The page uses each actual person's assigned body, recorded age, hair and dress.
It waits for the shared nearby detail page before taking a still. Changing people unloads
both comparison frames.

The current inventory is 20 own-person archive portraits, five explicitly labelled staff
stand-ins, two existing Grey full skin sheets, and two new owner-chosen Stirling reference
models. `assets/humans/web/photo_faces/historical/coverage.json` lists all 29. The new atlas
contains 27, including the retained Kate Ryan reference which has no active cast; 26 bind to existing actors; William and Sarah retain their full skins. The archive portraits retain all 25
existing head fits. Each texture binds to its exact person, sex and scene; a photo never
creates a person or changes scene presence. These named records currently belong to 1904.
Generic adults and matching children continue in all four years.

The skin display calibration reduces the shared body maps' orange cast halfway toward
the reconstructed linear RGB white point `[0.60, 0.40, 0.30]`, at unchanged base luminance.
Existing complexion tints still apply to monochrome and non-photo reconstructions, equally
to the face and surrounding body. Colour photographs supply the whole skin colour; visitor
complexion controls apply to both together. The Grey full skin sheets retain their own colours. Sky fill on
skin and eyes, softer eye-corner shading and broader corneal highlights keep faces legible
under hats. These use existing material uniforms: no extra atlas, light or draw call.
This is display calibration, not a demographic revision or evidence of ancestry.

Dorothy and Alice have distinct fitted heads. The owner's modern uploads are not published.
Stored references are edited 1904 studio portraits, with neutral companions for resting face
textures; source records retain the original SHA-256 and disclose the edits. Their cards use
the period portraits and an explicit stand-in label. Period hair and Alice's wire spectacles
remain reconstructed. A single view cannot attest hidden profile depth or a perfect match.

To add another owner-chosen adult reference, first register its source/texture reuse basis,
prepare the approved period reference, and run one command:

```sh
python3 tools/historical_photo_faces.py --person EXISTING_PERSON_ID \
  --photo /path/to/period-reference.png --source REGISTERED_SOURCE_ID --age 25 \
  --stand-in 'STAND-IN · owner-chosen reference model' --model work/face_landmarker.task --jobs 4
```

The command validates the existing person, preserves their age/body/dress, fits the head,
pins landmarks and hashes, and rebuilds the bounded named library. It refuses to silently
replace an existing curated portrait/reference. New authentic historical portraits should be
registered as identified portrait records with their source identity and fit first, then
included by `--all`. Children use the separate texture-only path. Future photos do not imply
permission to change an unrelated identity or present a chosen model as a historical photo.

All three catalogs share **one** nearby detail cache. The historical crowd sheet has a
maximum edge of 256 pixels; its close detail is restored from the same 1024-pixel page limit
used by the generic library. Total added face textures stay under 13 MiB including mipmaps
(about 12.28 MiB for this 27-entry named atlas). This includes all three crowd sheets and the
largest single detail page, rather than one detail page per catalog. No extra face render
pass or per-person atlas is introduced. Weak-PC GPU timing remains outstanding.

Check with `python3 tools/historical_photo_faces.py --check`,
`node tools/test_historical_photo_faces.mjs` and `node tools/test_photo_face_deployment.mjs`.

## Reference appearance and historical NPC assignment (T-3762)

The owner-approved sixteen period references are included, with 48 additional fictional
references made with explicit creation briefs: 32 European, 16 Great Lakes Indigenous/Métis,
eight Black and eight East Asian references in all. They supplement the original 256
unclassified adult sources, which remain available. A reference pool describes an artistic
creation brief; it neither establishes anyone's ancestry nor claims a uniform appearance
for a community. Source `synthetic_photo_reference_pools_3762` points to all seven unchanged originals;
`data/humans/variation/photo_reference_pools.json` records their hashes and creation briefs. New heads fit the frontal outline as well as eyes, nose, mouth and jaw.

`tools/human_variation_kit.py` derives each NPC's `photo_pool` from the existing compiled
community or explicit Community/People card facts. The 1812 camps retain their Indigenous
context. Unknown town residents use the existing European-majority reconstruction, including
Prairie Avenue; this remains a reconstructed appearance choice, never a biographical fact.
Names and photographs are not classified. The policy changes no historical person counts,
community records, scene dates or household membership. Individual identified portraits win.
The existing scene populations supply the city/year/neighborhood distribution; the library's
ratio of reference sheets is never a population quota. Black residents and Native/Métis
communities keep their own recorded contexts. No Asian actors are invented to fill a quota.

The settings creator independently offers every compatible fictional photo face, across all
four new reference pools and all original choices. Complexion and NPC historical defaults
do not hide any photo choices. A selected face persists across years and overrides NPC rules;
its skin/eye controls remain available. Named archive portraits are not generic visitor faces.

A colour photograph supplies the colour of the whole exposed skin, with the reference/actual
body gain ratio keeping a coachman's seated and standing appearances consistent. NPCs do
not receive a second reconstructed complexion tint on top of the photograph. Photo lips and
pigment retain their source colour instead of the stock orange lip correction and extra
freckles. Monochrome historical sources retain their declared reconstructed colours. The
stock woman's frontal hairline follows the reference estimate by moving the existing cap
against the actual varied forehead, retaining its strand texture, crown, bun and period cut.
Curated older portrait hair and child geometry remain protected. No hair triangles, texture
or draw calls are added. A single front reference still leaves profile depth reconstructed.

The 320-entry adult catalog uses twenty detail pages on disk. Across adults, children and
named portraits, only one nearby page may be resident **or loading**; the fixed crowd-sheet
edges and 13 MiB total added face-texture ceiling are unchanged. Settings thumbnails use
the existing crowd atlas. A larger catalog is not a claim about real-GPU frame rates.

New frontal photo imports use `tools/photo_reference_fit.py`: the existing hm08 morphs,
camera, bounds and priors with a vectorized analytic derivative. Finite-difference tests
verify the derivative independently. Pinned landmarks/fit results keep subsequent offline
builds deterministic, and existing curated portrait heads are never refitted by this path.

The shared iris texture is dark brown. Reference-colour transfer now allows the per-channel
gains required to reproduce measured blue/grey irises (the former cap of three suppressed
their blue channel). Photo faces also suppress the stock painted brow shadow. New fictional
references have broad studio lighting reduced before relighting; a smooth scalar gain keeps
their chroma and fine detail, with exposure anchored at the cheeks. Source files stay intact.

The child catalog retains its original sixteen references and adds 32 companions across the
same four fictional background briefs, ages 4, 8, 12 and 16 of each sex. The child selector
uses the same existing population context as the adults, within its age-compatible choices.
Camera registration and texture transfer leave every child head/body morph and eye position
unchanged. Its crowd sheet is explicitly capped at 512 pixels even as the catalog grows;
The companion additions share the single global resident-or-loading detail slot.

Sixteen additional toddler/school-age companions cover the youngest resolved age bands: each
background has a boy and girl of two and six. The final child catalog has 64 entries and
four disk detail pages, with the same 512-pixel crowd edge and one global nearby slot.
These references close the age-band fallback gap without changing any recorded age, seeded
age, child body/head morph, stature or eye geometry.
