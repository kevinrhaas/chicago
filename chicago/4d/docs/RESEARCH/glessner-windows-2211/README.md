# T-2211 — Glessner street and stable window profiles

Glessner exterior audit GA-11A. The audit found the street windows drawn as repetitive dark fields
in simplified frames: one pane behind one flat frame with a bar across its middle, every window the
same, and the 18th Street gable's high light a black arched slot.

## What changed (generator: `generators/archetypes/masonry_house_v4_sash.py`)

- **Double-hung sash in two planes.** Every street and stable window is a one-over-one double-hung:
  the upper sash outside the lower (205-245 and 250-290 mm behind the wall face), each with its own
  stiles, rails and glass, the blind stop and head proud of both. The two panes now sit at different
  depths, so a window reads as two sashes and catches light differently top and bottom.
- **Sills that shed water.** An oak sub-sill weathered outward under the lower sash, and the granite
  sill weathered toward the street with a drip nib under its nose, where it was a flat slab.
- **Narrow lights are sash, not voids.** The ten north lights under 0.45 m wide went down the
  basement-grille path and rendered as recessed black glass. They are now single sashes with
  horizontal bars, as HABS sheet 5 draws the corridor slits beside the 18th Street entrance.
- **The gable light.** HABS photograph 14 (1965) shows the east-wing gable's high light as a glazed
  round head in its own arched frame, a stone transom, and a one-over-one sash. It is built that
  way (record: `v4_detail.supplemental_openings`, the `transom` field). The c. 1923 HABS photograph 4
  (`a18-glessner-habs-photo-04`, the audit's #117) agrees; its rights are unknown, so it is a
  cross-check only and nothing is derived from it.

The courtyard sash is part B (T-2212) and is unchanged. The light (mobile) tier keeps the single
pane everywhere but the gable light: it had 2,696 triangles of its 200,000 left.
`docs/LIBERTIES.md` → `L-glessner-sash-2211` records what is read and what is reconstructed.

## The opening schedule

`opening-schedule.md` (and `.json`) lists all 62 street and stable openings, including the four-light
central group on the Prairie front's second floor. It gives each opening's position, height, light
count, the sash the generator draws, and the record entry's sources and confidence. It is generated:
`python3 tools/glessner_opening_schedule.py` writes it, `--check` fails when it is stale.

## Measured

- Master: 1,246,933 → 1,251,519 triangles. Light tier: 197,304 → 197,582 (limit 200,000).
  K01 contract re-measured: scale drift, origin, coincident faces and metric UV all ok
  (`data/components/prairie_1904/glessner_baseline.json`).

## Captures

Actual published `/1904/` app, desktop (full) and mobile (light), zero page errors;
`before-` captures are desktop on dev before this change. The stands are the gable from 18th Street
and close to; the Prairie first floor; the Prairie group of four; the east wing's north pair with the
narrow lights below; and the stable's north face.
`node tools/qa_glessner_t2211.mjs` (or `QA_TAG=before- QA_VIEWPORT=desktop …`) re-runs them.
