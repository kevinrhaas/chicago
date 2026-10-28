# Reference views — the image gate (T-2368)

**The owner, 2026-10-11, on 1612 Prairie:** it "bears little resemblance to the photo in the
research repo"; "if you have any views of the house those should be validated against in
development"; "if you have an image you should work towards it until it's a photographic
representation of any images, even drawings are ok, but it should look exactly perfectly like
the image or drawing"; and "you don't wrap the case until it matches the photo, not that you
can't change one without a photo".

So every building that has a photograph, a print or a drawing of it is built until its render,
from that picture's own camera, matches the picture. The ticket that builds it does not close
before then.

## Layout

```
data/reference_views/<structure_id>/<view>.json        one camera per picture of the building
data/reference_views/<structure_id>/<view>.match.json  its match record (tools/photo_match.mjs writes it)
docs/RESEARCH/photo-match/<structure_id>/<view>-side-by-side.jpg   picture | render
```

**The camera** (`<view>.json`): `structure_id`; `source_id` (the picture's record in
`data/sources/`) and/or `library_image` (its id in the Prairie image library,
`chicago/prairie_1904_v1/research/images/stream-*.json`); `photo` (the picture's file, relative
to the camera); `image_px`, `principal_px`, `focal_px` (the vertical one, when `pixel_aspect` is given); `eye` `[u, v, y]` in the structure's
footprint frame (u east toward the street, v north, metres over its grade); `yaw_deg` (clockwise
from north); optional `pixel_aspect` (horizontal over vertical focal length, default 1: a copy whose width was resampled apart from its height, which the `solve` must show — T-2748 measured 0.885 on the c. 1888 SW view of 1800-1808 Prairie from two points it did not fit); optional `basis_right_up_forward` (three orthonormal vectors in the same
east/north/up frame, overriding yaw for an inclined or rolled photograph); `solve` (how the camera was fitted, in words and numbers: which lengths scaled it,
which lines and points it was fitted to, the residuals); optionally `sun_uvy`, the direction
the picture's sunlight comes from in the same frame, so the render lights the walls the picture
lights and casts its shadows the same way (T-2369); and optionally `sky`, `"sun"` (default) or `"overcast"` for a picture in which nothing casts a shadow, which renders a soft, shadowless key at `sun_uvy` (straight overhead when absent) under a brighter sky, so a face the picture shows unlit is not raked by the review sun (T-2848). Say in the `solve` what the light was read from: which walls are lit, which way shadows fall, or that none fall. A drawing is an elevation or a
perspective: an elevation is an orthographic camera far off on the face's normal, and is solved
the same way with one length.

**The match record** (`<view>.match.json`): the GLB and camera it was rendered from (sha256), the
side-by-side, a `verdict` (`unreviewed` | `differs` | `matches`) and `differences`, each
`{what, status}` with status `open` (visible in the picture, not yet built as it shows, and a
visitor on the street would notice it), `fixed`, `not shown` (the picture cannot say: colour in
a monochrome print, a face it does not see), or `within tolerance` (T-3153: under about 1 ft /
0.3 m, a pixel offset, or a gap two pictures or two camera fits disagree about; say what was
read), or `owner ruling` (T-3236: the owner, looking at the building against its picture, asked
for it built otherwise; say what the picture shows, what was built and which ticket ruled it).
Only `open` blocks `matches`. `photo_match.mjs` keeps the verdict while the GLB and camera are unchanged, and sets it
back to `unreviewed` when either changes — a building only matches a picture someone has looked
at.

## The gate

- `node tools/photo_match.mjs data/reference_views/<id>/<view>.json` renders and writes both
  files. Compare the side-by-side with the picture element by element (massing, bays, every
  opening's shape and height, ornament, cornice, porch and stoop, roof and chimneys, fence and
  ground, materials and their tone) and write what differs.
- A ticket that drafts, refines or rebuilds a building carries an `## Image gate` section that
  lists its structure ids, one bullet each. `node tools/ticket.mjs done` refuses it until every
  view of every building listed is `matches`, made from the GLB in the tree, with nothing open.
  `--anyway --why` passes a picture shown to be wrong about the building (a later alteration, a
  retouched print), with the reason written in the ticket.
- Nothing refuses an edit: `check.sh` runs `image_gate.mjs --check`, which fails only a malformed
  file and otherwise prints where each building stands.
- **Where it stops** (owner, 2026-10-25, T-3153; AGENTS.md rule 11). A difference is `open`
  only if a street visitor would notice it: over about 1 ft (0.3 m) in size or place, an
  element missing or mis-shaped, a wrong count of bays, openings or stacks, or a wrong
  material or colour. Everything else is `within tolerance`. A run that finds a gap writes it
  here and files no ticket (`ticket.mjs new` refuses one on a photo-gated house unless the
  owner asked); a house's sign-off finishes in its own run and is never split.
- What a picture does not show is still built, at the reconstructed tier, and recorded in
  `docs/LIBERTIES.md` — the gate is about what it does show.

## Where the pictures are

- Prairie Avenue 1904: the Prairie library (`chicago/prairie_1904_v1/research/images/`, viewer at
  `/prairie-1904/`), its downloaded files in the image store (`STORE.json`). Owner, 2026-10-11:
  pictures from chicagology and other sites are brought in with their attribution, not left as
  links.
- Other years: `data/sources/` (views, engravings, drawings) and `data/sources/assets/`.

Section drawings may supply optional `clip_planes`, each `{normal: [east,north,up], constant: metres}` with a unit normal. The review renderer retains points where `normal.dot(point)+constant >= 0`. State the source cut line and calibration in `solve`; this is a section through the asset, not a change to its app geometry.

Distant drawing cameras can set `near_m` (positive, below the 500 m far plane) to keep fine layers distinguishable in the depth buffer. Place it in front of the subject, state it in `solve`, and retain the same value for before/after comparisons. Ordinary photographic views default to 0.1 m.

## A picture of several structures

Use `scene: "1812"` (or another scene id) and `also_render: ["other_structure_id", ...]`
to render a compound from one camera. The camera remains in `structure_id`'s footprint
frame. Every member is loaded from that scene's compiled sidecar, including its selected
phase, position and bearing; an absent member, wrong-date sidecar or missing GLB refuses
the render rather than silently omitting part of the compound. Compile the scene first
after changing placements. `--glb` replaces only the anchor's asset for before/after work.

The reviewer places all meshes on one common grade plane. It does not reproduce the app's
terrain sampling or imply that independently sloping ground has been calibrated. Say so
in the `solve`; do not move surveyed positions to fit a retrospective drawing.

Group match records list `rendered_members` and hash every GLB and scene placement.
Changing any member invalidates the review, including a moved barracks whose GLB bytes
are unchanged. New reviews also hash the reference picture. The group is context, not
an assertion that every member is visible or attested in that picture: document hidden
and unpictured members explicitly. Existing single-building cameras retain their format.

An optional `enclosures: ["record_id", ...]` adds selected native enclosure records to
the same review. An explicit `scene` is required, even for a single anchor. Each record
must be in the actual enclosure index, name the same scene/date and belong to the anchor.
The review calls the app's `createEnclosures` renderer on those records, on the common
flat review plane, and transforms its world coordinates into the anchor frame. It does
not reproduce the app terrain or invent a second fence generator. The match binds every
selected record, native geometry dependency and anchor placement; changing one invalidates
the review. Published application grounding, clearance and walking access remain separate
checks.

Provisional compound cameras must set `diagnostic_only: true`. They remain valid review
inputs and credited picture links, but the picture compiler does not offer their invented
pose as a historical “From this spot” location. Existing cameras default to the prior behavior.
