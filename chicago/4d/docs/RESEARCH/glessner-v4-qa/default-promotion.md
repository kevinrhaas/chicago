# Glessner v4 default promotion

Owner authorization: September 29, 2026, make v4 the default in dev, then
promote dev to main using the release workflow. This closes the comparison round
in T-1730; PR #201 supplied the verified model.

`node tools/promote_version.mjs glessner_house v4 --no-compile` moved the record,
master, full derivative and reduced derivative to canonical paths and retained
the former default as `pre-v4`. V2/v3 are unchanged. The archive is repacked at
the new paths; assets are materialized before validation/publishing, not committed
as a single oversized GLB. The source geometry has not changed.

The ordinary derivative producer regenerated both web assets, including a new
light recipe receipt. Canonical LOD checks cover license ownership, missing assets,
master/recipe/output freshness and the same reduced-geometry triangle ceiling.
The published default uses light geometry on both lower settings and full geometry
only on Full. The previous measured Full allowance follows the actual loaded
record, not the presence of a version query parameter.

Verification results will be recorded before release. Production is not implied
by this document; the promotion workflow and its deployment must both succeed.

## Surviving building, dated exterior phase

The owner reported that the card's “Standing: 1887–1946” looked like a demolition
date. It is not: August 1946 closes the pre-conversion exterior phase, immediately
before the alterations documented by HABS. Preserve that phase boundary rather
than asserting an unchanged 1904 exterior through today.

Canonical, pre-v4, v2 and v3 records now carry a separate sourced `present_status`:
“Still standing — Glessner House museum”, checked against the operating museum's
official history on 2026-09-30. The compiler carries that fact and its provenance;
cards with this separate status label the date range “Modeled phase” and show both.
The source is text-only with rights unresolved. No geometry was changed. The light
recipe is refreshed because it hashes the entire canonical record, including prose.
Part 13 of the published smoke asserts the rendered distinction and the unchanged
phase endpoint, not merely the existence of a source-code string.

## Owner-approved rights exception

On September 29, 2026 the owner answered: “Yes, leave them with rights unresolved.”
This approves retaining the existing courtyard-photo references in
`glessner_house/as_built_1887/form.detail_profile` and `form.v4_detail` during
promotion. The source `habs_glessner_photo_05_court_c1923` remains
`rights_status: check_required`; it is not cleared or relicensed. No photographic
pixels are used as textures. The references cross-check reconstructed forms and
are corroborated by the HABS measured sheets and owner reconstruction brief.
`measure_rights_derivation.py --update` records exactly these two added canonical
entries, with no other expansion. This is a project-policy exception, not a
copyright clearance, and the existing source-use limitations remain visible.
The regenerated register also reflects two v4 attributes already downgraded from
attested to inferred; no source is added or cleared by those confidence updates.

## Published default verification

The no-version-query default passed 30 explicit-frame view/tier checks: five
views, three detail settings, desktop and touch mobile. Both had zero unexpected
page/request errors. Light peaked at 799,079 of 825,000 rendered triangles;
Full peaked at 3,433,805 of 3,800,000. Failed-full-download rollback, repeated and
rapid switches, stable record/confidence/weathering and stable GPU resource
counts passed on both viewports (five lifecycle cases each). These are explicit
frame budget readings, not native-device frame-rate measurements.
