# T-2203 — Glessner roof tile module and coverage

Target: 1 July 1904, exterior and courtyard. The previous full model used
8-inch-wide tiles with 4.8-inch exposure and skipped fragments below 0.08 m².
The light model had grain-only clay planes and a broad lip every second row.
This revision uses 6-inch width (0.1524 m) and 5-inch exposure (0.127 m),
individual lapped noses, and continuous mapped tile joints beneath the full
geometry and throughout the reduced roof. Dormer cheeks use the same module.

## Evidence and limits

- **HABS IL-1015 written data, printed page 21 / PDF page 22**, Part II B4:
  “terracotta, tar covered tiles, six inches wide with five inches of their
  length exposed.” The module is an observation of the later surveyed roof.
  Its survival from the original roof to 1904 is **inferred**, not a 1904
  measurement. Source: `habs_glessner_house_il_1015_data_pages`.
- **Glessner's 1923 account**, quoted on printed page 13 / PDF page 14:
  “The roofs are of red baked tiles, unglazed.” This supports the original
  material and finish. The reviewed source is the HABS quotation,
  `habs_glessner_house_il_1015_data_pages`; the separately catalogued original
  1923 source remains unresolved and is not newly cited by the model.
- **Taylor 2135, c.1887–1889**, Art Institute mqc 28805, audit image 008
  (duplicates 101/109), visually reviewed: the main roof shows fine,
  continuous courses. It checks the general early appearance, not an exact
  six-inch measurement or colour. Source:
  `taylor_2135_glessner_exterior_1887_1889`.

The HABS tar describes a later condition and is **excluded** from 1904.
The half-tile stagger, 4-mm side joints, 6-mm lap relief, exact clay colour,
weathering and the carry-back of the later measured module are reconstructed.
No total tile length or concealed headlap dimension is claimed. The texture
uses original numeric pixels; no historic or restricted image is embedded.
The held Florian/Nickel/Cornell views are not used to derive new assets.

## Construction

The record's `v4_detail.roof_tiles` drives physical geometry and the numeric
16-column × 16-course texture recipe. The repeat is 2.4384 × 2.032 m.
Grain-only terracotta remains on individual tiles and ridge ornament, so
ridge caps do not acquire a flat tile grid.

UVs come from the host roof, including its course phase, rather than from
individual raised faces. Equal-pitch cone facets share their height-based
course phase. Tile cuts follow each planar facet; the faceted turret envelope
is unchanged. Every clipped roof fragment retains its continuous bed. Narrow
returns and cone tips no longer fail an area threshold or masonry decoration
switch. The west dormer cheeks also receive complete tile coverage.

Full detail adds individual tile faces and closed lower noses. Light retains
the existing alternate-course geometric sampling, now at two five-inch
courses; its material carries **every** tile course and joint. No tier
threshold, renderer filtering or scene lighting changes. T-2204 remains held
for distance filtering and moving-view quality. Copper roofs, crest shapes,
roof envelopes, glazing, ground contact and earlier comparison versions retain
their existing construction.

## Reproduction and review

- `python3 assets/textures/glessner-v4/generate.py --only roof_tiles`
- Pinned Blender 4.5.3: `-b -t 4 -P generators/build.py -- --only glessner_house --no-bake`
- `bash tools/web_derivatives.sh --only glessner_house__as_built_1887.glb`
- `python3 tools/test_glessner_roof_tiles.py --output docs/RESEARCH/glessner-roof-tiles-2203/physical-coverage.json`
- `python3 tools/test_glessner_roof_envelope.py`
- `python3 tools/test_glessner_block_clipping.py --self-test`
- Publish, then `PW_EXECUTABLE=/usr/bin/chromium node tools/qa_glessner_t2203.mjs`

`physical-coverage.json` inventories all 244 host fragments, including the two
west-dormer cheeks, and checks 63,518 full tiles. Light has 199,656 triangles,
below the unchanged 200,000 ceiling. Independent checks cover host-bed closure,
physical tile bounds/pitch, UV phase, a translated cone, a tiny triangle,
decoration-independent coverage, copper/underside exclusion and the budget.
Existing roof-envelope and 1,108 frontage-access samples pass.

`before/` and `after/` use six fixed cameras each on the normal published 1904
app, desktop/full 1280×800 and mobile/light 390×780. Browser receipts record
asset URLs, detail, budgets, dark glazing, request failures and page errors.
These are surface-review views; T-2200's calibrated photograph cameras remain
frozen. Its candidate report assesses the new mesh without refitting them.

The frozen-camera candidate keeps the Prairie-front, north-level and
courtyard-east residuals identical to the baseline. Other nearest-vertex
associations move by up to 2.20 px in calibrated views, and 3.03 px in the
limited courtyard-west view; the roof landmarks now select the new tile
vertices. This is not a claim that the house meets the programme's 1% target.
The actual roof-envelope checks pass independently.

The desktop northeast view still shows distance aliasing/moire in the fine
physical tiles. That visible limitation belongs to held T-2204; this ticket
corrects the physical module and missing coverage, not the entire programme's
photographic-quality target.

During review the owner also identified the lifted/folded copper connector at
the inside northeast courtyard corner. Its flush-to-roof geometry repair was
added to the existing held **T-2220** copper ticket, with an independent
reproduction capture. It is not corrected by this clay-tile change.

`tile-close/` adds a supplementary close view in both detail levels, after the
change only (`QA_VIEW=tile-close`). It resolves the individual physical and
mapped tiles that become subpixel features in the mobile overview. Both views
pass the same published-app, budget, asset and page-error checks.

| Review view | Desktop / Full | Mobile / Light |
| --- | --- | --- |
| Northeast | [Before](before/desktop-northeast.png) · [After](after/desktop-northeast.png) | [Before](before/mobile-northeast.png) · [After](after/mobile-northeast.png) |
| Courtyard | [Before](before/desktop-courtyard.png) · [After](after/desktop-courtyard.png) | [Before](before/mobile-courtyard.png) · [After](after/mobile-courtyard.png) |
| West service roof | [Before](before/desktop-west.png) · [After](after/desktop-west.png) | [Before](before/mobile-west.png) · [After](after/mobile-west.png) |
| Dormers | [Before](before/desktop-dormers.png) · [After](after/desktop-dormers.png) | [Before](before/mobile-dormers.png) · [After](after/mobile-dormers.png) |
| Turret | [Before](before/desktop-turret.png) · [After](after/desktop-turret.png) | [Before](before/mobile-turret.png) · [After](after/mobile-turret.png) |
| Tile close-up | [After](tile-close/desktop-tile-close.png) | [After](tile-close/mobile-tile-close.png) |
