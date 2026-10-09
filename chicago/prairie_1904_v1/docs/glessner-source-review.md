# Glessner exterior source review — T-2198

Target: **1 July 1904**, exterior and courtyard only. This is a reconciliation of
the 8 October 2026 audit, not a new claim to have inspected inaccessible images.
The original 168 stable IDs and rights statements are retained. Three museum
references bring the Glessner index to 171. No building geometry changes here.

Every record carries `evidence_review` in its canonical `research/images/stream-*.json`
source. `tools/build_images.py` validates and publishes that object into the image
index. The viewer displays review state, phase, source-use limits and related
copies. `tools/test_evidence_review.py` exercises missing reviews, unsafe promotion,
family inconsistency and the rights boundary; `tools/validate.py` runs it.

## Corrected identities

The [museum's July 1948 Florian gallery](https://glessnerhouse.blogspot.com/2023/07/glessner-house-july-1948.html)
was rechecked on 9 October 2026. IDs are intentionally stable even where their old
slug describes the wrong subject. Correct the description, not a bookmarked ID.
Previous library-authored fields survive verbatim in `metadata_history` and are
expandable in the viewer; they are not endorsed as holder catalog descriptions.

| Audit | Stable ID suffix | Actual linked image |
|---|---|---|
| 024 | florian-1948-ne-exterior | GX112.10: porte-cochère doors, small Keith-house fragment at left |
| 136 | florian-1948-court-to-stable | GX112.24: roofs, dormers and stair turret |
| 137 | florian-1948-porte-cochere-doors | GX112.21: elevated courtyard looking west |
| 138 | florian-1948-roof-turret | GX112.28–29: industrial interior, excluded from exterior geometry |

The three added records are GX112.50 (entry/curb), GX112.1–3 (northeast overall)
and GX112.25 (courtyard bow/chimney). Museum attribution identifies photographer,
series and July 1948 exposure date. No permission or public-domain status was
established: all three are **copyright — link only**, with no local image copy.
The viewer uses the existing holder-hosted image mechanism. Later paving, ivy,
institutional equipment and other alterations are not silently backdated to 1904.

## Disagreement and exclusions

[Audit 112, Lowe collection mqc/75902](https://artic.contentdm.oclc.org/digital/collection/mqc/id/75902)
is cataloged as Glessner by the holder as well as our library. Its pair of brick
coach-house gables conflicts with Glessner's independently documented granite
stable. The catalog title and building association remain discoverable, explicitly
**disputed**; orientation and the former confident identification are withdrawn.
It is excluded from geometry pending reconciliation. No other identity is asserted.

[Audit 089, door sheet mqc/69279](https://artic.contentdm.oclc.org/digital/collection/mqc/id/69279)
is visibly marked **“Not Correct”**. Its floral grille is excluded as a rejected
design. Other door variants remain separate design records requiring evidence of
execution. Preliminary elevations and the courtyard watercolor are design intent,
not proof of built gables, conservatory or fountain. WPA model photos document a
secondary reconstruction; the late-1930s date belongs to the model, not necessarily
the photograph. Interior records retain the actual audit state, including the 44
that were only screened by metadata. The 17 unavailable images remain catalog-only.

A search of the 4D data and generators for the disputed/rejected stable IDs and
catalog item numbers found no geometry dependencies. The existing T-2183 courtyard
fixes and dark-glass default remain intact. This is a source-use correction, not a
claim to have independently revalidated all existing model dimensions.

## Reproductions and date limits

Explicit families link the George block view (#004/005), construction photograph
(#006/103/110), Inland Architect plate (#007/108), Taylor 2135 (#008/101/109), and
preliminary central-gable design (#035/037/047). The Taylor 9974 group
(#010/011/012/016/017/019) is marked **possible derivative family**: conflicting
publication dates do not establish independent exposures. #017 remains unavailable;
its relationship is catalog-based. Door variants #087–090 are related designs,
not duplicate photographs or independent proof of construction.

A family is counted once for corroboration. Unassigned records explicitly say
that independence is not established. “In period · to 1911,” the library's broader
search category, is separate from the 1904 review phase. A date range spanning 1904
does not prove the condition on 1 July. Drawing dates, microfilm dates and modern
photographs of old models are distinguished in each review's date basis.

## Generated locator refresh

Rebuilding the index also refreshes `site-plan.json` from the already committed
1904 street-grid dataset: it had omitted the grid's Indiana/side-street parcels.
No survey, parcel geometry, house placement or grid source was edited. The index
and locator must be regenerated together to pass the existing freshness check.

## Review boundary

The other 30 tickets T-2199–T-2228 remain on their owner's manual scheduling hold.
This ticket does not recover the 17 unavailable files or start physical completion.
