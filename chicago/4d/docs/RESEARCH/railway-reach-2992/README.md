# T-2992 — the 1904 `light` tier from the air over the district

**The finding (lapping #1180).** `tools/qa_draft_t2982.mjs`'s `air` stand (eye 1360,-3620 at
110 m, looking at 1300,-3480) read **1,323,370** triangles at 390x780 `light` on dev 7a4c01da4,
against the 1,270,000 ceiling (`GLESSNER_V4_LIGHT_TRIANGLES`, main.js). It is a breach on dev, not
a breach T-2982 caused: that ticket's eight drafts carry 16,980 of the triangles.

**Whose triangles, read by hiding each group of the scene in turn at the stand:** structures
829,287 · **railway 247,401** · context 82,204 · the sun's pass 61,768 · street trees 57,042 ·
terrain 55,243 · street grid 52,181. Inside the railway: the four ground decals (beds, cinders,
made ground, verges) 175,120, cut into 40 m cells already and drawn because they are in view; the
**far rails 61,416**, 25 zones' strips in view out to 3.3 km; and the **lake-edge cap 9,120**, 4,560 in the
colour pass and the same again in the sun's.

**Two trims; no ceiling moved.** `light` is the floor (AGENTS.md § the frame budget), so the
ceiling stays where it is and the railway gives the triangles back:

1. **The far rails stop at the tie reach**, which is what `railway.js`'s header has always said
   ("past the tie reach a zone draws only the ground") and what its update never did: since
   T-2478 the three-face strips drew to the end of the yard at every tier. Past `REACH[level].ties`
   (220 m at `light`, 480 `balanced`, 650 `full`) a rail is under a fifth of a pixel at 390x780
   and the ties beside it have already gone. This one changes pixels, and they are counted below.
2. **The cap is cut into the ground's 40 m cells** (`spatialBatchAsync`, as the decals are). One
   mesh three kilometres long was never outside the sun's ±120 m box, so it drew into the shadow
   map from anywhere; cut, three's own shadow-camera and view culls take each cell. The same
   triangles, so the same picture.

## Readings (published mirror, software GL on the runner)

| stand, 390x780 `light` | dev | this branch | ceiling |
|---|---:|---:|---:|
| `qa_draft_t2982` air (hand-set camera) | 1,323,370 | **1,252,942** | 1,270,000 |
| `measure_detail_ceilings --district` (walker pose) | 1,266,335 | **1,195,907** | 1,270,000 |
| trackside, looking north up the yard | 1,274,635 | **1,209,703** | 1,270,000 |
| trackside, looking south | 884,064 | 810,540 | 1,270,000 |

The trackside stand looking north was over on dev as well; nobody had stood there.
`measure_detail_ceilings.mjs --district` (new) reads the same air stand through a walker pose,
which puts the eye a little differently and so reads lower; both are kept. The `qa_draft_t2982`
row's "dev" figure includes the cap; `qa_railway_reach_t2992.mjs`'s own dev emulation re-shows
only the rails and reads 1,314,358 there, so the cap's share at that stand is 9,012.

**What changes in the picture** (`tools/qa_railway_reach_t2992.mjs`, the same held frame with
the far rails as dev drew them and as shipped, every pixel compared; the control hides every
rail):

| stand | pixels differing | max channel delta | control (no rails) |
|---|---:|---:|---:|
| air | 122 of 304,200 | 29 | 122 |
| yard looking north | 130 | 29 | 19,633 |
| yard looking south | 68 | 29 | 18,409 |
| Prairie looking east | 0 | 0 | 0 (no rail in view) |

From the air every rail on screen was a far rail: the 122 pixels are the whole railway's steel at
that distance, sub-pixel glints on the cinders. From the yard the trim removes under 1 % of what
the rails draw (130 of 19,633 pixels), all of it at the far end.

`qa_draft_t2982.mjs` re-run on the branch, both viewports, every stand inside budget with no page
error or failed request (`qa-draft-t2982-browser-validation-*.json`; desktop `full` air
3,078,015 against 4,600,000).

## Files

- `browser-validation-mobile.json`, `after-mobile-*.jpg` — `node tools/qa_railway_reach_t2992.mjs`
- `detail-ceilings-mobile-light.json` — `node tools/measure_detail_ceilings.mjs --district --only mobile --levels light --stepped --against <dev mirror>`
- `qa-draft-t2982-*` — `QA_TAG=t2992 node tools/qa_draft_t2982.mjs`, per viewport
