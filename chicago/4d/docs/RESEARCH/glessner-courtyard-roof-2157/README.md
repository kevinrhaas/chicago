# T-2157 courtyard dining-tower roof

Owner request: correct the copper cap and tiled connector, preserving the main
roof line and carrying its terracotta crest onto the connector. The supplied
current-model views show a long copper wedge and two sunken tile returns.
The supplied aerial and Tommy Henry courtyard detail (March 2023) show a
forward copper hip with a short ridge returning to the main roof.

The canonical 1904 Glessner record selects the repair. Older comparison versions
retain their original geometry. The new junction is a roof union: the host loses
only the triangular area above which the tiled connector stands. The original
wall-top/eave profile is continuous. Shared apron edges use the same coordinates
on copper and tile; the two sides meet a level ridge with the main roof's crests.

Dimensions remain a declared reconstruction bounded by the existing HABS plan
and north-wing roof heights. The owner brief records the supplied references;
no third-party photographic assets are added to the repository.

Validation:

- `python3 tools/test_glessner_roof_envelope.py`: 1,800 stable-roof samples plus
  1,200 courtyard samples. Every sampled courtyard point has exactly one roof
  surface, and the replacement never lies below the original host plane.
- Pinned Blender 4.5.3 bake, canonical web compression and package round-trip.
  The light model has 196,335 triangles, below its 200,000-triangle cap.
- `dining-roof-*.png`: three fixed cameras from `render_structure_review.py`.
- `desktop-*.png` / `mobile-*.png`: the actual published 1904 renderer at
  1280×800/full and 390×780/light. Both boot normally; no page errors, failed
  resource requests or loader problems. Three cameras per viewport, with
  draw/triangle counts within the existing renderer budgets. Camera positions
  and complete results are in `browser-validation.json`.

The renderer images retain the scene's existing lighting and materials. The
animation loop is paused after normal boot only to make the review cameras
repeatable; these captures do not measure interactive frame rate.

Integration: after merging the current dev changes, the order-book gate found
T-2168 had also been split. The West residual rows now follow T-2169, and the
North barn row follows T-2170. The reports are rebuilt from the owner table;
this bookkeeping update changes no counts, budgets or geometry.

The browser gate also retained the pre-lot-remnant flora totals (10 communities,
155 species). The committed catalog independently sums to 11 communities and
166 species. Its three exact count assertions now reflect that catalog; the
clamped-layer, worst-case, source and overflow assertions retain their bounds.

Broader published browser coverage also reports existing 1835 bridge-pile,
frontage-count and scene-detail-budget failures. The desktop 1–6 leg reached
265 passes and ten assertion failures before its browser target crashed; part
14 passes on both viewports (46 checks). These runs are recorded honestly in
`tools/dev-smoke-state.json`; they are not a claim of a green whole-site smoke.
The roof patch changes no 1835 renderer or model geometry.

After integration with dev `f5a99ae5`, the published 1904 app was checked again:
desktop/full and mobile/light each passed three roof views, with zero page,
resource or loader errors and every draw/triangle budget satisfied. The full
readings are in `integration-validation.json`.
