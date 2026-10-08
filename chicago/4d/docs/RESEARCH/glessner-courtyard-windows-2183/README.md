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

Pending: pinned Blender bake, web derivatives and package, published desktop
and mobile captures, full repository gate, PR and dev merge. This checkpoint
is not a claim of completed visual validation.

Rebuild from `chicago/4d` with pinned Blender 4.5.3:
`generators/build.py --only glessner_house`, then
`tools/web_derivatives.sh --only glessner_house__as_built_1887.glb`.
Rebuild any comparison derivatives named by the bake; compile scenes,
compile liberties/source-use, publish, and run `tools/qa_glessner_t2183.mjs`.
The canonical derivative producer repacks the three GLBs for GitHub recovery.
Never repack stale materialized assets over a new bake.
