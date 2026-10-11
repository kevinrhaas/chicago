# T-2208 — Glessner street masonry: courses, arrises and opening returns

Glessner exterior audit GA-09A. The audit found noisy faceted stone and uniform joint
treatment; at street distance the texture overwhelmed the coursing.

## What changed (generator: `generators/archetypes/masonry_house_v4_detail.py`)

- **Jamb-bonded courses.** A course that passes wholly beside a straight opening jamb is
  cut at that jamb. The jamb is the end face of a whole stone that runs to the reveal with
  no joint, where before the opening clipped whatever stone it happened to fall in and
  left slivers (see `before-desktop-prairie-jambs.png`, beside the basement grilles).
- **Long/short ends.** Every run between corners and jambs begins and ends with one long
  and one short stone, swapped course by course, so vertical joints never stack up a
  corner or a jamb. The stones between are whole and scaled to fill the run.
- **Pitched arrises.** Each rock face falls over its outer 85 mm to a straight arris 16 mm
  proud of the bed, which is the front of an opening's reveal. The joints read as lines
  at street distance, and a jamb stone meets its return flush. Interior relief is unchanged.

Course heights are still the 24 HABS-measured courses. The rule above is reconstructed:
`docs/LIBERTIES.md` → `L-glessner-coursing-2208`.

## Measured

- Master: 1,236,675 → 1,246,933 triangles (more whole stones are laid). Light tier:
  199,116 → 197,304. K01 contract: scale drift, origin, coincident faces and metric UV all
  ok (`data/components/prairie_1904/glessner_baseline.json`, re-measured).
- `tools/test_glessner_block_clipping.py` → `check_coursing`: whole courses end flush on
  both jambs, alternating corner stones, arris on the pitch line. It also covers a run
  whose middle falls in a shorter opening. The first bake of this ticket left those runs
  as bare bed, and the test was written against that failure.

## Captures

Actual published `/1904/` app, desktop (full) and mobile (light). `before-` captures are
the desktop views on dev before this change. The views are the Prairie front from the
street and close to its basement jambs, the north-east corner, the shaded 18th Street
face from across the street and close to, and the alley face.
`node tools/qa_glessner_t2208.mjs` (or `QA_TAG=before- QA_VIEWPORT=desktop …`) re-runs them.
GA-09B (T-2209) calibrates texture, roughness and shadow. That ticket covers the shaded
north face's flat read under scene lighting.
