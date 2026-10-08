# T-2183 — courtyard windows and continuous eave

## Evidence reread

The research repository is part of `kevinrhaas/chicago`, under
`chicago/prairie_1904_v1/research/public/`. Reviewed the index of all 17 HABS
photographs and 10 Houghton design drawings. HABS photo 05 is the relevant
courtyard evidence; photos 01, 04 and 14 concern street elevations and do not
supply a courtyard-window height. Sheet 4 supplies the section and floor levels.
The Houghton drawings are design intent, not as-built evidence.

The owner's five attachments (8 October 2026) contain two model views, two
courtyard photographs, and the service-entry detail. They were visually read,
not redistributed or used as textures. Modern replacement upper tower panes
are not copied: the circa-1923 HABS photograph supports the divided sash.
Carrying the surviving exterior to 1904 remains an inference, not direct
photographic attestation of that year.

## Corrections

- Principal tower openings return from 9.3–16.5 to **9.3–14.5 ft ng**, exactly
  matching the adjoining first-floor sill/head. T-2172's main-to-upper-window
  ratio was a mistaken perspective comparison and is superseded.
- The north courtyard upper row becomes **20.9–24.0 ft ng**, matching the
  existing tower band. Heads stay fixed; raising the sills produces the short
  upper openings seen in photo 05 and the service-entry detail.
- The photographed awning is treated as the projecting roof eave. It extends
  **2.36 ft (0.719 m)** beyond the north courtyard wall to the bay shoulders,
  meeting their **24-ft** roof edge. The existing 34.1-ft ridge stays fixed.
  The roof ordinate at the wall becomes **25.634 ft ng**; the prior 26.5-ft
  section extrapolation remains documented in the source note. The exact
  overhang/ordinate is reconstructed within about half a foot, not a printed
  HABS dimension. The street eave is unchanged.
- Both pitches of the copper hip/apron meet corresponding tiled connector
  faces. Each convex intersection is removed from the host individually:
  clipping their concave union as one polygon would overlap roof surfaces.
  The gutter follows the extended eave into the tower shoulders, removing
  the former diagonal drop at the junction.
- `?glass=dark` is now the default at Full, Balanced and Light. The existing
  `?glass=transmission|clear|dark` override is retained; underlying authored
  GLB materials and earlier comparison versions remain available.

## Validation / recovery

Branch: `steward/t-2183-glessner-courtyard-windows`, based on dev `3f326a6`.
Ticket T-2183 is recorded and claimed in `kevinrhaas/chicago-tickets`.

The numerical check passes 1,800 stable-roof rays and 1,200 courtyard rays,
plus explicit window-datum and eave-to-bay alignment checks. The existing
seven glass-mode checks pass with the new full-detail default.

Recovered from source checkpoint `c497167`; the original process subsequently
saved `72b0cd6`. An independent pinned Blender 4.5.3 rebuild produced the same
canonical master/full/light hashes as that later checkpoint. The derivative
producer repacked the verified recovery archive. Full is 47,959,092 bytes;
Light is 25,229,272 bytes and 197,682 triangles (below the 200,000 model cap).

The actual published `/1904/` app passes six review views: desktop 1280×800 at
Full and mobile 390×780 at Light, with zero page, HTTP or loader errors. All
views meet the existing rendering budgets. Both viewports also switch through
Balanced, Light and Full, retaining dark glass and loading both canonical
assets. `browser-validation.json` records these observations. Animation is
paused only for repeatable review cameras; these are not FPS measurements.
The normal-animation published smoke is recorded separately.

The three comparison models retain identical geometry, indices, normals,
materials and metadata. Their pinned rebuilds differ only in UV packing;
`comparison-version-check.json` records the independent buffer comparison.

The recovered working tree passes all 790 repository checks (322 negative self-tests included). Mobile published stage 13–14 passes 137 assertions with zero page errors. The first desktop attempt timed out at boot under concurrent checks; its separate rerun is in progress. Current-dev integration, final desktop smoke and PR completion remain pending.

Rebuild from `chicago/4d` with pinned Blender 4.5.3:
`generators/build.py --only glessner_house`, then
`tools/web_derivatives.sh --only glessner_house__as_built_1887.glb`.
Rebuild any comparison derivatives named by the bake; compile scenes,
compile liberties/source-use, publish, and run `tools/qa_glessner_t2183.mjs`.
The canonical derivative producer repacks the three GLBs for GitHub recovery.
Never repack stale materialized assets over a new bake.

## Source-use accounting on recovery

The checkpoint added HABS photo 05 to the opening heights and north-range eave
records without updating the geometry citation register. Recovery records those
two entries explicitly, continuing the owner-requested courtyard reconstruction
and the existing decision to retain the courtyard-photo references with rights
unresolved (see `../glessner-v4-qa/default-promotion.md`). No rights clearance is
claimed: the source remains `check_required`, the photograph is not a texture,
and no attachment is redistributed. This is a recorded project-policy decision,
not a change to the source's license.

## Integration gate repair

The first repository check passed 789 of 790 steps. Its only failure was the
shared 1835 order book still assigning work to T-2043, split earlier on
8 October. Current person rows now name T-2187 and family/store household
rows name T-2188, according to those child tickets. Regenerated book/report
differences are work-owner references only: counts, quotas and placements
are unchanged. The dependent re-familying programme report is rebuilt as well; its differences are also work-owner references only. Both strict checks and their existing negative fixtures pass.
This repair unblocks the visible Glessner parcel; it does not implement either
1835 ticket.
