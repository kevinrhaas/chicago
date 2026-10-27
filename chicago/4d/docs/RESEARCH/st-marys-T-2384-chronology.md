# T-2384: St Mary's source and chronology reassessment

The held engraving is an undated retrospective picture published in 1884. Its filename does not date the depicted building to 1843. There is no secure source for the previous checkpoint's claim that a belfry was necessarily added after 1835. A dated May 1844 diary description does support a later wooden church with a steeple, bell and cross.

This source correction preserves the existing 1835 geometry and bounds. It changes the record-only tower omission from an asserted 1835 fact to a conservative inference. No match, solved camera, new canonical phase or completed model is claimed.

## What was actually inspected

- The held picture `chicago/reference/images/chicago/chicago_st_marys_church_1843.jpg`, 2671 × 3110 pixels.
- Andreas, *History of Chicago*, vol. 1 (1884), **printed p. 290**: <https://archive.org/download/historyofchicago01andr/page/n600_large.jpg>.
- The same volume, **printed p. 291**, including the exact held engraving and its caption: <https://archive.org/download/historyofchicago01andr/page/n602_large.jpg>.
- Garraghan, *The Catholic Church in Chicago, 1673–1871* (1921), **printed p. 106 and footnote 26**: <https://archive.org/download/catholicchurchin00garr_0/page/n159_large.jpg>.
- Garraghan **printed p. 107**: <https://archive.org/download/catholicchurchin00garr_0/page/n162_large.jpg>.
- Garraghan **printed p. 112**: <https://archive.org/download/catholicchurchin00garr_0/page/n171_large.jpg>.
- Garraghan **printed p. 127**, quoting Quarter's diary: <https://archive.org/download/catholicchurchin00garr_0/page/n192_large.jpg>.
- Thompson, *Illinois Catholic Historical Review*, vol. 4, printed p. 258, via the repository's existing machine OCR. This was not a fresh scan verification.

The exact publication of the engraving is now established as 1884; its prior drawing, artist's model and depicted year remain unestablished. Its engraved signature reads Moss Engraving Co., New York. The caption is simply “ST. MARY'S CHURCH.” The drawing shows a blank near gable, **five** tall sash and a door near the far end of the visible long wall. Calling it an entrance-gable church would misread what is drawn.

## Chronology, with limits

| Evidence | Supported reading | What it cannot date |
| --- | --- | --- |
| Andreas p. 290: original church 25 × 35 ft, occupied October 1833, initially unpainted and without steeple or tower; “Some time afterwards” low open tower and bell | Initial construction state and a subsequent tower addition | The tower's installation year; neither its presence nor its absence specifically on 1 July 1835 |
| Thompson p. 258: “Having removed” the church, rear addition “about the same length as the original”; then belfry and cross | The 1921 author tells a post-removal enlargement/belfry sequence | A firm post-1837 or post-1839 tower terminus: its notes cite Andreas p. 290, which supplies no such sequence |
| Garraghan p. 106 n. 26: government lot purchased **21 June 1839** | A dated property purchase at northwest Michigan/Madison | The day the church moved or an enlargement/belfry completion day |
| Garraghan p. 106: December 1839 arrival narrative already describes O'Meara having moved the old church to north Madison west of Michigan | Retrospective support for relocation by the end of 1839, after the purchase | An exact move date or precise lot coordinate |
| Garraghan p. 107: new brick church opened Christmas Day 1843 | New church opened on 25 December 1843 | Demolition or disappearance of the old wooden church |
| Quarter diary, “1844, May”, printed by Garraghan p. 127: “The old church is a long, low, frame building, having a small steeple and bell surmounted by a cross.” | A real dated later appearance: wooden church with small steeple/bell/cross in May 1844 | Original tower installation date; exact shape of its tower; the date of the Moss engraving |
| Garraghan p. 112: College of St Mary opened 3 June 1844 in the old frame church, north side Madison between Wabash and Michigan | Old wooden church survived into June 1844 and had a different use | End of the wooden building's physical existence |

Garraghan p. 65–66 repeats the same undated Andreas wording. It supplies no independent tower date. The earlier 1836 relocation summary on Chicagology remains contradicted by the June 1837 original-site sighting and the later purchase/relocation narrative.

The May 1844 diary passage is a period witness **transmitted through a 1921 printing**. The printed page has been visually checked; the original diary manuscript has not. Its separate source record declares that chain. It does not turn every word of Garraghan's retrospective narrative into period testimony.

## Assessment of the 1835 model

A tower was physically possible by July 1835: “some time afterwards” after October 1833 includes that date. It is also possible that it arrived later. The evidence held here does not choose between those readings. Therefore neither “must add tower to 1835” nor “tower definitely postdates 1835” is justified.

Retaining `tower=false` is a conservative earliest-state inference, now disclosed as such. A reconstruction with a tower in 1835 could also be argued within the unresolved interval, but it would be a declared temporal reconstruction, not a result established by the picture. The current patch does not change the owner's 1835 view merely to make it resemble an engraving with no depicted year.

The original 25 × 35 ft footprint cannot automatically receive the enlarged later form. The current footprint's orientation and house-like facade remain disclosed liberties. This research does not resolve them.

## Bounded next model proposal

The clean dated alternative is a **May 1844 comparison form of the same old wooden structure**, using the diary for the epoch and the engraving as an explicitly reconstructed appearance reference. This is not an assertion that the engraving was drawn in, or depicts, May 1844.

A proposed phase `frame_seen_1844` may cover **1844-05-01 through 1844-05-31**, expressly the bounds of the month named in the diary, not construction, alteration, relocation or demolition days. Omit `from_is` and `to_is` so the card does not print either boundary as an event date. This preserves the existing 1833–June 1837 original-site phase, with an honest gap rather than invented continuity. The north-Madison location should initially be symbolic or null-coordinate: between Wabash and Michigan, no surveyed bearing or metre placement asserted from the engraving. A reconstructed placement may subsequently be derived from the project's streets and disclosed if that date receives a scene.

For a model comparison, build a single low clapboard range with the exact visible topology: blank near gable, five tall long-wall sash, door near that wall's far end, one far roof stack, open belfry over the near roof end, four posts, curved open braces, crossed lower rails, a curved pointed cap and cross. The engraving supplies that topology, never an exact metric or coordinate. Begin with 7.62 m across the short side and a **reconstructed** 21.336 m length (two original 35 ft lengths), using Thompson's “about the same length” addition only as a dimensional prior. It is not a measurement of the enlarged church. Keep the original phase's dimensions unchanged. Alternative lengths must be compared against the picture before any final adoption.

The existing `frame_dwelling` builder cannot produce the blank-gable/side-door arrangement and this belfry from `tower=true`; `tower` is record-only. Do not present flipping that flag as a visible correction. Add an opt-in chapel form or dedicated chapel builder, with explicit facade opening setout and belfry geometry. Defaults must preserve all existing frame dwellings. The original phase must not inherit later dimensions, windows, tower or paint. A new builder or opt-in fields need their own declared reconstruction and parameter validation.

The phase needs a build/render route for its actual date. `tools/compile_scene.py::resolve_phase` selects by scene date, and the only current dated scenes are 1812, 1835 and 1904. A committed later GLB with no selecting scene is rejected by `validate.py`'s bake-reach check. Do not select the later phase through an 1835 sidecar or reuse the original-site coordinates just to render it. A dated comparison scene or an explicit-phase bake/render route is required before committing that asset. That pipeline change should also keep function/occupant descriptions tied to the correct epoch: St Cyr is not the May 1844 occupant, and June 1844 college use is not October 1833 church use.

No canonical phase or incomplete builder is enrolled in this source-only patch. A future phase implementation can use the bounds and topology above without inventing a relocation day. No accepted reference camera is written until it renders that phase and is actually reviewed. T-2384 remains open.

## Validation and blast radius

The proposal contains three source records, the picture ledger correction, this report, and record-only disclosure corrections in `st_marys_church.json`. The phase dates, position, footprint and all consumed generator attributes retain their values. The tower confidence changes to `inferred`, so a recipe that serializes all attribute confidences may stale the St Mary's asset despite unchanged geometry; parent integration must measure freshness rather than restamp a manifest by hand. No generator, other structure, GLB, scene, camera or match record is changed. Light checks validate the JSON schemas, unchanged geometry fields and existing frame parameters. No Blender, browser, export, full gate or image-match review was run for this proposal.

## 2026-10-25: picture-bounded original-site chapel reconstruction

The original-site model now chooses the engraving's recognizable open belfry, cap,
cross and five-sash/end-door frontage for 1835. This is an explicit reconstruction
within the unresolved addition interval; the sources do not establish a dated 1835
belfry or date the engraving. The source chronology above remains valid. The earlier
no-tower choice is superseded by a different declared reconstruction, not by a newly
discovered installation date. No later enlargement, relocation or new phase is
selected through the 1835 sidecar. The original 25 by 35 ft footprint, position,
documented range, storey and body wall height remain unchanged. The gabled type is
retained, while a reconstructed 30 degree pitch replaces the earlier typological 38
degrees: the first actual private comparison showed the body ridge conspicuously too
high. The provisional camera is not a metric calibration; this is a bounded visual
shape choice. The narrower belfry and taller cap likewise address the actual visible
proportions rather than being presented as measured scantlings.

The opt-in `plan: chapel_side` has six bays: five sash followed by an end door.
Resolved stations live in a hashed property shared by the builder and native entrance
reader. Both gables are blank; the near one is pictured and the unseen far one is
reconstructed. The existing single stack moves to the far end through an explicit
reconstructed placement attribute. The open tower has a boarded plinth, four posts,
low crossed rails, curved braces, a small hanging bell, concave pointed cap and cross.
All new presence, positions, sections and profiles are reconstructed; see the liberty.

The existing 12-over-12 sash is 0.766 m wide and 1.432 m high. Its oblique projection
will be compared with the engraving before choosing any different reconstructed glass
size. No source pixel or foreshortened opening is treated as a measured pane schedule.

Every other frame dwelling retains its prior geometry by default. Actual exports and
web derivatives for all 271 phases, native derived fixed point, source/app comparison
and complete gates are still pending at the authored checkpoint. The external coarse
body-camera fit is provisional, not rendered or accepted; it does not date the picture
or move geometry/placement to fit. Acceptance will use the actual comparison and
discrepancy register under the owner's good-enough bar.

### Other held pictures checked during the frontage work

The complete `chicago_st_marys_cathedral_1848.jpg` is captioned FIRST CATHOLIC
CATHEDRAL and shows a different Greek-front building, not this small wooden range.
The complete `chicago_panorama_st_marys_college_1849.jpg` is a view *from* the college,
not an elevation of the wooden church. Neither supplies geometry for this change.

A further held file, `chicago/reference/photos/old-st-marys-church-woldstmarys_CONTRAST.jpg`,
is a 696 by 530 sepia photographic view of a similar small wooden church with a blank
gable, open belfry and end entrance. It appears to have three long-wall sash rather
than the Moss engraving's five. Its creator, holder, original date, depicted building
identity and publication provenance have not been located in the held source records;
the filename and visual resemblance do not establish them. It is an unattributed
diagnostic, not a new geometry source or a licensed comparison asset in this work.
The differing opening count is therefore recorded as an unresolved picture/state
question, without claiming a new date, identity or independent corroboration.

### Native export checkpoint, 2026-10-25

The corrected shape has now been emitted by Blender 4.5.3 LTS for all 271 frame
phases, with every genuine web derivative refreshed by the pinned 4.5.0 pipeline.
St Mary's actual canonical master is byte-identical to the corrected private
comparison: 206,184 bytes and 2,542 triangles. The same provisional camera rendered
both versions. The lower roof and narrower, taller belfry were independently viewed
and approved for the family build, which is not an image-match verdict.

All 270 other actual master exports preserve exact oriented triangle positions,
normals, confidence values and non-UV attributes, plus node, scene and material
metadata. Fifty-seven masters are byte-identical; the other 213 differ only in
unused UV or binary ordering. All 270 genuine web controls are byte-identical and
also passed an independent meshopt-decoded comparison. The selected master hashes
are current; unselected registry rows and the nine frozen authored files remained
unchanged throughout the commands.

The batch driver's final audit initially compared the wrong web-registry level
(the outer object instead of `masters`). The original failed receipt is retained.
A separate audit of the actual per-master schema passed without rerunning or
changing any export. Native derived fixed point, the official reference-view
record, published app review, complete check, PR and merge are still pending.

### Official source comparison, 2026-10-26

The single registered `moss-engraving` comparison now binds the actual canonical
master and the unchanged numerical camera. It records **differs**, with one plausible
street-noticeable remaining gap: vertical sash setout. The generic opening sill is
0.95 m and its head is 2.382 m, leaving 0.818 m below the 3.2 m plate. The engraving
shows higher window heads close beneath the eaves and higher sills. Wall-relative
proportions suggest an upward shift around 0.4–0.6 m, with substantial uncertainty;
that is not a surveyed or calibrated metric reading. No further geometry variant
was built for this bounded PR. The remaining setout belongs in original T-2384's
register, with no new follow-up ticket.

The corrected chapel topology, open belfry and lower roof are fixed differences.
Date and identity uncertainty are disclosed limits. Pixel, camera/groundline and
conflicting-picture gaps are within tolerance under T3153, rather than being
automatically classified OPEN. In particular, the unattributed three-sash diagnostic
does not establish a different 1835 count or license a new derived comparison.
Published app review and the complete code/PR gates remain separate requirements.
