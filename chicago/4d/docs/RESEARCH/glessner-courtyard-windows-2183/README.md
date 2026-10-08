# T-2183 — courtyard windows and continuous eave

## Evidence reread

The research repository is part of `kevinrhaas/chicago`, under
`chicago/prairie_1904_v1/research/public/`. Reviewed the index of all 17 HABS
photographs, all six HABS sheets and 10 Houghton design drawings. HABS photo 05 is the relevant
courtyard evidence; photos 01, 04 and 14 concern street elevations and do not
supply a courtyard-window height. Sheet 4 supplies the section and floor levels.
The Houghton drawings are design intent, not as-built evidence.

The owner's five attachments (8 October 2026) contain two model views, two
courtyard photographs, and the service-entry detail. They were visually read,
not redistributed or used as textures. Modern replacement upper tower panes
are not copied: the circa-1923 HABS photograph supports the divided sash.
Carrying the surviving exterior to 1904 remains an inference, not direct
photographic attestation of that year.

## Source-use record

Photo 05 retains `rights_status: check_required` and `asset_use: cross_check`.
This change does not claim that the HABS photocopy is automatically cleared,
redistribute a new copy, or derive a texture from it. The owner requested a
comparison of architectural facts; HABS measured sections and the owner
reconstruction brief also support the edited attributes. The rights-derivation
baseline explicitly records the new `opening_heights` and `ridge_north_range`
photo citations, both with other support, and the reconstructed confidence.
This is a recorded use decision under the existing cross-check route, not a
rights clearance or a removal of the unresolved-source warning.

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

Source checkpoint: `c497167b`. Pinned Blender rebuilt the canonical master
and unchanged comparison versions. First desktop app review caught a slit
beneath the rising copper return: the wall now follows the actual roof
underside and a gutter joins the return to the bow. Final derivatives are rebuilt
and the recovery archive is repacked from these exact bytes. Actual published
1904 app review passes at 1280×800 Full and 390×780 Light: three fixed views each,
zero page/HTTP/loader errors, dark glass active, all views within render budgets.
The six PNGs and two browser-validation JSON reports beside this note record it.
Animation is paused for repeatable images, so these are not FPS measurements.
Published stage-13 smoke passes both viewports: **250 passed, 0 failed**, zero
page errors; 124 mobile and 126 desktop checks. It took 40 minutes with software
rendering. This is stage 13 of 14, not a full unfiltered smoke. The log is saved
beside this note. The mirror was built from checkpoint 72b0cd61; dev integration
began while the lengthy run continued, so the standing ledger explicitly claims
no exact tree digest for that reading. Glessner geometry and renderer code did
not change. The PR CI gate supplies the final clean-clone repository verdict.

Rebuild from `chicago/4d` with pinned Blender 4.5.3:
`generators/build.py --only glessner_house`, then
`tools/web_derivatives.sh --only glessner_house__as_built_1887.glb`.
Rebuild any comparison derivatives named by the bake; compile scenes,
compile liberties/source-use, publish, and run `tools/qa_glessner_t2183.mjs`.
The canonical derivative producer repacks the three GLBs for GitHub recovery.
Never repack stale materialized assets over a new bake.

## Integration repairs

Dev advanced through `a8ac1213` and `2649aaf0` to `525abdee` during review. The final integration
preserves dev's T-2187 adult-men ruling, the live work-order owner repair, its
matching derived reports, and its smoke arrival wait. Shared generated source-use
records are rebuilt from the combined inputs. This PR adds no population or quota
change beyond the incorporated dev baseline.

The previous worktree backing metadata became unavailable during integration.
It was recovered from GitHub checkpoint `72b0cd61`; the existing working files
and the completed merge of dev `a8ac1213` were preserved. Repository metadata
now lives in this checkout rather than depending on the earlier scratch tree.

Local preflight completed all 790 steps: 787 passed and three reported errors.
The re-familying report is now taken with its corrected writer and inputs from
current dev. Two local publish readbacks saw stale duplicate cohort files; they
now pass after serial mirror recovery (1,403 loose resident files and 773
packed records). All three failing steps pass individually; the full local run
is still reported as 787/790. PR CI will verify the unmodified publisher on a
clean checkout. Changelog-entry and ticket-collision preflight checks passed.
