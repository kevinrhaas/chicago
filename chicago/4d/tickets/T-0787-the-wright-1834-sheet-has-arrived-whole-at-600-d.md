---
id: T-0787
title: The Wright 1834 sheet has arrived whole at 600 dpi and nothing can cite it yet: register the National Archives reproduction beside the BPL master, in its own pixel space, with the scale bar as the check
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 956
claimed_by: run 9/5/2026, 9:44:39 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T03:42:13.250Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34006978138
---

**The source, 2026-09-05.** The owner added a second copy of J. S. Wright's manuscript survey of
1834 at `chicago/pre_fire_v1/maps/images/1834-wright-map.jpg` — the Historic Urban Plans (Ithaca) reproduction of the
**National Archives original**, 5050 × 6628 px at 600 dpi, with its own caption: *"Two portions are
missing, the larger being near the lower center … the manuscript was mounted on cloth to repair this
tear."* It is a different scan of the same drawing this project already traces as `wright_1834`
(the BPL/Leventhal copy, 4204 × 5166 px, IIIF `commonwealth:js957744g`). The owner's instruction:
*"review this and create tickets to update and enhance the map … several items from this map should
be incorporated including the streets, there are streets documented here that are missing, including
the blocks, where the public square is, where the various sloughs are, things like 'the kinzie block'
… look at all of the streets and block numbers … the lakeshore edge and that whole area … the whole
path of the river going south … note the sections as labeled in the legend."*

## Why this is first

Every trace this project holds off Wright is keyed to the **BPL pixel space** and its sha256:
`data/traces/gcp/wright_1834_gcps.json` picks its control in `commonwealth:js957744g` coordinates,
`tools/trace_river.py` / `tools/trace_shoreline.py` cite IIIF regions of it, and
`data/traces/thompson_block_numbering.json` grades a numeral by whether it was *read* off that sheet.
The new file is a different raster of the same drawing. **Nothing can cite it until it is registered**
— and every ticket filed beside this one (T-0788 to T-0795) wants to cite regions of it, because at
600 dpi the block numerals are legible where the BPL scan's are not.

## The ask

1. **A source record** — `data/sources/wright_1834_nara_hup.json` (or a sibling id the source
   schema allows): repository (National Archives, via Historic Urban Plans, Ithaca), the sheet's
   own caption verbatim, the checksum, the pixel size, and its relation to `wright_1834` stated in
   terms: *same drawing, different scan, different pixel space*. Add its row to
   `chicago/pre_fire_v1/maps/image_checksums.csv` and `map_references.csv` beside the other maps.
2. **Its own control.** Either pick GCPs in the NEW scan's pixel space by the same rule the BPL set
   used (the same six to eight street crossings, so the two sets can be compared), or fit a
   pixel-to-pixel homography onto the BPL frame from shared features and record its residuals.
   Say which, and why. The two scans will not agree to the pixel — paper stretch differs by
   mounting — so the residual IS the finding.
3. **The scale bar as the check.** Wright draws *Scale of feet* — 1200 / 600 / 300 / 50 — at the
   foot of the sheet. Measure it in both scans and state metres per pixel from the bar alone, then
   against the affine the GCPs give (BPL: 0.7115 m/px, RMS 17.5 m). A bar that disagrees with the
   GCP fit by more than the fit's own RMS is a finding about the sheet, not a rounding.
4. **The two missing portions, located.** The caption says two pieces of the manuscript are gone,
   the larger near the lower centre. Box them in pixel space so that every later reading knows
   which numerals and lines it cannot have read — on the crops made for this review the tear sits
   on the South Branch beside the *Reserved* blocks 87/88 (T-0791, T-0794).

**Done when** the new scan has a source id, a checksum row, registered control with residuals
against the BPL fit, a scale-bar figure, and boxed lacunae — and a tracing tool can be pointed at a
region of it and cite that region.
