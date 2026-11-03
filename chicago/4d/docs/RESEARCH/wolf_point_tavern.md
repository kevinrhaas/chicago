# Wolf Point Tavern — research dossier

**Record:** `data/structures/wolf_point_tavern.json` · **Scene status:** standing on 1835-07-01,
probably still in innkeeping under a changed name · **Milestone 1, west bank**

The building that named the place. Its identity is vivid and its geometry is unknown — the
painted wolf sign, the landlord succession, the 12½¢ rate and the Black Hawk War headquarters
are all attested, and not one source measures it, counts its storeys or fixes it to an
intersection. It is the least precisely placeable structure in this parcel and the record says
so in three separate places.

---

## 1. Identity and sequence

| period | landlord | note |
|---|---|---|
| 1828 (disputed — see §2) | built for **James Kinzie** | west bank at the forks |
| by 1829 | **Archibald Caldwell**, for Kinzie | liquor licence 8 December 1829 |
| from early 1830 | **Elijah "Old Geese" Wentworth** | the name most of the recollections use |
| 1831–1833 | **Charles and Mary Taylor** | |
| **1833–1836** | **William Walters** | **covers the scene date** |
| 1832 | — | Gen. Winfield Scott's Black Hawk War headquarters |

Aliases in circulation: Wolf Tavern, Wentworth's tavern, Old Geese's tavern, Rat Castle,
Taylor's tavern, Travelers' Home, Western Stage House. The last two are post-1834 renamings
and are part of the function dispute in §4.

Rates while it was a public house: 12½¢ a night, 13¢ to stable a horse.

## 2. Conflict: built 1823 or 1828?

| reading | source | what it says |
|---|---|---|
| **1828** *(adopted)* | `drloih_wolf_point` | "James Kinzie … built a tavern on the west bank of the river at Wolf Point in 1828" |
| 1823 | `drloih_hotels` | "opened in 1823 by James Kinzie, John Kinzie's son, and David Hall on Wolf Point" |

**These are the same publication contradicting itself**, which is a reason to distrust both
dates rather than to prefer one confidently. 1828 is adopted because it is the reading of the
narrative account that also carries the operator succession and the wolf sign — i.e. the page
that knows the most about the building — and because 1823 sits oddly with the licensing record,
in which Archibald Caldwell's liquor licence is dated 8 December 1829 and the settlement's first
Peoria County tavern licence went to Clybourn and Miller.

**It does not matter for the 1835 scene.** The building stood under either reading. The
`documented_range` is therefore tagged `inferred`, not `documented`, and the dispute is carried
in its note.

## 3. Conflict: what was it made of?

Not really a conflict, but a description that flattening would lose. chicagology:

> "This building was partly log and partly frame, and was situated on the ground north of Lake
> Street Bridge."

The record carries `construction: log` (documented) plus a separate `frame_addition: true`
(documented) so the mixed fabric survives into the data. **The frame element's size, position on
the building and date are all unattested** — a geometry requirement discovered from the evidence,
in the same way the Sauganash's attached log wing was.

*Updated 2026-08-10.* The attribute was written here and in the record as `frame_extension`,
which is not the name the `log_dwelling` archetype reads, so the documented frame half reached no
vertex and nothing said so; the same happened to the sign, recorded as `signage` against the
archetype's `sign`. Both are renamed and built as of 2026-08-10 — see `docs/LIBERTIES.md` L20 for
the account and L24 for the invented dimensions the build required. The frame bay is 4 m of the
12 m frontage, one storey, at the north end; those three numbers are conjectural and the record
says so on each. What would settle them is what would settle the footprint: Andreas vol. 1
pp. 626-631 at page-image level, or the Braunhold retrospective view at plate level.

## 4. Conflict: was it still an inn in July 1835?

Three readings, all from the same body of sources:

1. **William Walters was landlord 1833–1836** — ordinary innkeeping at the scene date.
2. It "ceased operations as a public house in 1834" (`drloih_hotels`).
3. After 1834 the name changed successively to the **Travelers' Home** and the **Western Stage
   House** — a change of sign, not of trade.

**Adopted: innkeeping, tagged `inferred`.** Two of the three readings are compatible with it, and
a stage house is still a public house. A landlord of a closed house is a contradiction the
sources have not resolved, which is exactly why the tag is not `documented`.

## 5. The wolf sign — the one documented visual feature

> "A painted sign of a wolf was hung outside the tavern by approximately 1833."

Hung well before the scene date, so it belongs in the 1835 model. **What it looked like is
entirely unattested** — size, board shape, how it hung, how the wolf was drawn. The archetype
should carry the sign as a distinct, separately-confidenced element rather than folding it into
the massing, so that a viewer using the confidence toggle sees "we know there was a wolf sign"
and "we invented this wolf" as two different claims.

Wau-Bun separately derives the Wolf Point name from an Indian resident called Moa-way, "the
Wolf". That is a competing etymology for the *place name*, not a competing fact about the sign.

## 6. Placement — and why it is the weakest in the parcel

**No surviving intersection locates this building**, so the Sauganash method (half an 80 ft
platted street off a documented corner) does not apply. The coordinate is derived from the datum
origin at the forks and from bank geometry.

What is attested:

- **West bank at the forks, north of the Lake Street crossing** — chicagology puts it "on the
  ground north of Lake Street Bridge".
- **James Kinzie's residence next south, Walker's meeting house north** — so it sits in the
  middle of a three-building river-front row, and the row's order constrains it.
- Wau-Bun's 1831 sequence reads "Facing down the river from the west was, first a small tavern
  kept by Mr. Wentworth", which is why the facade is put on the water.

Method: Lake Street's centreline northing at the west bank is 4637286.5, interpolated along Lake
between the two OpenStreetMap control points; its north kerb is 12.2 m beyond that at 4637298.7,
half an 80 ft platted street. The footprint's south face is set 40 m north of that kerb, leaving
room to the south for the Kinzie residence and ~50 m to the north for the meeting house, in the
documented order. Across the bank the east face sits 11–19 m back from the **modern** west-bank
line (OpenStreetMap water polygons), the setback varying because the modern bank runs north-west
across the building.

**Uncertainty: about 40 m along the bank and about 20 m across it.** The along-bank figure is
this record's own — nothing fixes how far north of the bridge the tavern stood. The across-bank
figure is the georeference's, compounded by the modern bank not being the 1835 bank: this reach
was wharfed and rebuilt, and the direction of that change is not established here.

Facade bearing 90°, due east onto the water; the bank runs north-west, so 75–105° is equally
defensible.

## 7. What is unknown

| question | where to look |
|---|---|
| Any dimension at all | Andreas vol. 1, "Wharfs, Piers and Early Hotels" pp. 626–631, at page-image level |
| Storey count | The same; or the retrospective "Wolf Point from the south as it might have appeared in 1830" reproduced in Andreas, examined at plate level — tier 5, and not yet opened for this record |
| Size and position of the frame element | Unattested in anything reached |
| What the wolf sign looked like | Unattested; probably unknowable |
| The building's fate after 1836 | No source reached gives one — which is why the phase closes at the end of Walters's tenancy rather than at a demolition |


## T-2386 — Explicit reconstructed roof tone, 2026-10-26

The current physical L, two outward-facing gables, two dark entries, one right-gable sash, roof head plus pipe, sign and georeferenced placement remain. This record supersedes the dossier's older placeholder prose about a rectangular/inline model. The earlier existing `darkened` preset was genuinely built and inspected in a normal native mobile load with shingle normal/ORM maps, live fly mode, credited source/liberty and both native door approaches. Technical checks passed but the roof still looked pale; those actual receipts remain preserved as history, with no matches claim.

Choose only explicit reconstructed `roof_colour=deep_brown`, the local FrameTavern option of one quarter of existing darkened linear RGB, with unchanged alpha/roughness and the new colour's confidence on every roof face. The optional LogDwelling parameter is keyword-only; all legacy defaults and the common material sheet remain. The genuine canonical refresh must cover all 82 LogDwelling masters and their 82 pinned WEB derivatives, controlling every unselected asset/record and actual default geometry/material/confidence before any restoration. No roof geometry or variant loop is introduced.

Source `blanchard_shober_1867_wolf_point`: Rufus Blanchard, publisher; Chas. Shober & Co., lithographer; Chicago, 1867, *Wolf's Point in 1833*, NYPL I. N. Phelps Stokes Collection, existing Commons surrogate. The actual printed year supports its existing public-domain-by-age status. The retrospective 1833 scene neither proves unchanged July 1835 appearance nor attests pigment, weather-blackening or calibrated reflectance. L-wolf-point-roof-tone-2386 declares this liberty.

All eight actual files contain nine compositions; most share motifs but are not exact camera crops. The composite has two distinct plates, Hammon changes viewpoint/crop, and Herriott's tiny birdseye lacks a confidently identified measurable Wolf target. The poster's old1892/Newberry1935 rights/date conflict remains inspection-only, without a clearance upgrade or geometry derived from it. Current per-picture camera/render coverage and T-3153 classifications are still required before original signoff; no invented cameras or matches are supplied by the tone change.

Actual deep-brown production: the strict native82 wrote guard passed. All81 unselected canonical masters and all81 WEB derivatives are byte-identical. The new Wolf master225f3e1041d02cdaa627d3d73c5f6448aff9b12c66f4a545462db45bbf8e0d59 and WEBfdc5ef22a440636e35e4cec15818661f4351f0f4d0c9e506ef36b00422a45210 preserve binary geometry, normals, confidence, counts, UVs and placement; only roof_shingle baseColorFactor differs. The actual roofconfidence remains1.0. Native invalid-stock/false-attestation checks reject unsupported declarations and the old positional API is unchanged. These are production/control facts, not an appearance or original image-match verdict.


### Poster provenance and Images credit update

The earlier inspection-only rights disposition for the colored Blanchard/Davis poster is superseded by explicit archived Newberry curatorial publication evidence: Chicago, Rufus Blanchard, ca. 1893, with the statement that the image was published in 1893. The printed credits and matching poster were reviewed on 2026-11-03; supporting publication evidence: https://github.com/kevinrhaas/chicago-evidence/blob/df1f36d070b52feec6373ad4cb7ec3c063814f97/evidence/wolf-sauganash-2026-11-03/poster-primary-publication-review/RECOVERY.md . SourceRecord blanchard_davis_c1893_wolfs_point_poster preserves the conflicting current Newberry Poole 27 date 1935 / Copyright Not Evaluated, and the unavailable archived-image payload. Do not invent a reprint chronology or unverified creator credit.

This is credited-source enrollment only. The native Images compiler can join the textual structure citation without enrolling a camera. The independently generated initial poster diagnostic remains unfitted and unreviewed outside the app; no new view/match, geometry, metrics, historical camera spot, existing-seven-view change or full-ticket acceptance is proposed here. The poster is not a duplicate of the 1867 NYPL sheet. Tiny Herriott's unmeasurable-target exclusion remains unchanged. Original T-2386 stays open.


## 2026-11-03 — Current eight-comparison reconciliation (T-2386)

This reconciles the already inventoried eight files and nine compositions; it adds no research-reading unit. The current ledger contains eight identified native asset comparisons, each reviewed `matches` under T-3153 on unchanged MASTER 225f3e1041d02cdaa627d3d73c5f6448aff9b12c66f4a545462db45bbf8e0d59. The distinct ca. 1893 poster now has its own accepted diagnostic camera and genuine canonical-layout native side-by-side. The geographic camera remains unsolved. The earlier credit-only/unfitted-poster statements above are superseded for current comparison status; the publication evidence and current Newberry catalogue conflict remain unchanged.

The later poster depicts an additional left-gable opening while the earlier governing 1867 sheet depicts one doorway and continuous logs. Keep the existing earlier-witness form and record picture disagreement under T-3153. No extra opening is hidden, called pixel-small or silently fixed, and no historical alteration date is inferred.

The Herriott panorama is contextual and individually unidentified. Its houses convey broad shape, but the checked original and caption do not key an individual Wolf house. The previous resolution-based exclusion explanation is superseded; retain the original inventory association as unverified, without a ninth camera, absence claim or new grade ruling. The native scene owner includes the poster in the existing attested-grade pictured evidence. Shape, materials, plan, placement, source records and the seven prior canonical camera/match/JPG bytes are unchanged.

Current-source gates and exact-head published app acceptance are separate release requirements, recorded with the final PR. The earlier clear-body proof is specifically 07b8 elevated flying inspection, not a surveyed/historical street pose, door traversal or view of every opening. Nothing here marks the original ticket DONE before its normal protected-dev merge. The detailed ledger is `wolf-picture-signoff-T-2386/coverage.json`; exact render recovery is https://github.com/kevinrhaas/chicago-evidence/blob/9bbce05b3f135e4cb91abb930c1750eda1cb3a43/evidence/wolf-sauganash-2026-11-03/poster-eighth-canonical-prepared-after-outage/RECOVERY.md .

### Superseded record wording, archived 2026-11-03

The following is the exact prior `research_note` from the record. Its claims that the physical L still differs, the poster is unfitted and the original request remains open describe earlier development checkpoints; they are not the current comparison verdict. Preserve this history, including the Andreas pp. 626–631/Braunhold research locator, model-origin reasoning and primary-publication citation, rather than erase it. Current uncertainty about measured dimensions, exact placement, July 1835 continuity and the geographic camera remains.

```json
{
  "research_note": "The building that named Wolf Point, and the least precisely placeable structure in this parcel. Its identity is vivid and its geometry is unknown: the painted wolf sign, the landlord succession, the 12 1/2-cent rate and the Black Hawk War headquarters are all attested, while not one source measures the building, counts its storeys or fixes it to an intersection. TWO DISPUTES ARE RECORDED RATHER THAN RESOLVED: the build date, 1823 versus 1828, where the same publication contradicts itself and 1828 is adopted for the reasons in the phase's date note; and whether it was still in innkeeping in July 1835, where the balance favours yes under a changed name. Neither dispute changes the scene — the building stood, on the west bank, north of the Lake Street crossing, with a wolf on a board outside it. What would change the record is a measured description in Andreas pp. 626-631, or the Braunhold retrospective view of Wolf Point examined at plate level for storey count and massing. See docs/RESEARCH/wolf_point_tavern.md. T-2386 L review has now inspected those retrospective pictures. The new physicalL is a bounded image-supported hypothesis, not a surveyed plan or accepted match; the original request remains open. The physicalL also rebases its local origin to preserve the old coarse world bbox centre; the retained-origin analytic trial would put part of the primary worn apron into the committed river. This is an explicit reconstructed model-coherence correction, not a picture-derived world location. T-2386 actual physical-L review found material topology/two-entry improvement but differs. This bounded continuation addresses facing horizontal wall/gable courses, roof edges, pole/sign pose and low right light, with reconstructed details and unchanged provisional camera; it does not close any image gate. T-2386 actual surface/pole comparison improved but still differs: this separate next proposal targets dark blind doorway recesses and curved course shading with narrow dark recessed joints, using the same camera and no global palette change. Full acceptance remains open. The distinct ca. 1893 Blanchard/Davis colored poster is documented by blanchard_davis_c1893_wolfs_point_poster. The archived Newberry curated exhibit explicitly identifies its Chicago publication and credits George Davis; the current Poole 27 catalog separately lists 1935/Copyright Not Evaluated. Both records remain documented without assuming a reprint chronology. Publication evidence and the 2026-11-03 review are preserved at https://github.com/kevinrhaas/chicago-evidence/blob/df1f36d070b52feec6373ad4cb7ec3c063814f97/evidence/wolf-sauganash-2026-11-03/poster-primary-publication-review/RECOVERY.md. The poster supplies no measured plan, dimensions or historical camera station, and its diagnostic camera and complete picture match remain unresolved."
}
```


### Superseded attribute-trial wording, 2026-11-03

The following exact prior notes described pre-correction trials, not current closed doors, pale chinking or a missing pipe. Their current tense is corrected without changing values, confidence, sources or any resolved mesh input. The separate pipe remains a reconstructed exterior proxy with unknown material/function.

```json
{
  "ridge_stack_head_m": "T-2386: the reconstructed head clears the ridge by 0.50 m. This is a short, visible chimney head within a period single-flue envelope, not a dimension read from the 1867 print. The pipe beside the adjacent roof is a distinct, unresolved element rather than silently folded into this shaft.",
  "compound_door_state": "T-2386 next actual-render difference: both source entry rectangles read deep/dark/open, while the current actual L has pale closed planked leaves. Cut only their stated outward wall skins and put a blind dark backing300mm behind the face with casing/reveals/threshold. This is a bounded exterior depth proxy, not a room, inferred door swing, occupant or interior passage. Whole physicalL and solid-footprint walker collision remain unchanged, and the same explicit +X access descriptor remains external-clearance metadata.",
  "compound_log_profile": "T-2386 source course faces read rounded/unevenly shaded with narrow dark recessed joints, unlike the current regular pale chink stripes. Use bounded curved face relief and inset existing-palette dark backing only on this explicit log-course compound.300mm rhythm,20mm gaps,15mm joint setback,38..48mm seeded relief and six profile panels are reconstructed rendering sections, not source-measured logs, original colour, exact weathering or a photoreal texture. Extend the same chosen profile through facing gable triangles; hidden structural fabric remains unproved and partly-frame textual evidence is retained."
}
```
