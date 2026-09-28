YªçŠx-®éÜj×¢ëiºÚ+Š§j[h‘éÜ¢éíãŽwÛ®÷Û½¼o+^²‰¢¶×## T-1256 â€” bounded jaunt choices and alternate endings (2026-09-28)

Jaunts can declare bounded integer resources and inventory without imposing them
on plain outings. Effects clamp defensively, purchases and awards commit once per
event id, Previous/Next never replay them, and Revise choice truncates the later
route before deterministically rebuilding the earlier decisions. The first matching
conditional ending wins; inconsistent content reaches a visible, non-awarding fallback.

The panel shows only declared resources. Each choice carries a plain-language
consequence; unaffordable or basket-filling choices remain visible but disabled with
their reason. Session state stays in local browser storage as content version, jaunt
id and events; corrupt or version-mismatched saves are discarded safely, and storage
failure falls back to memory. Shopping, tavern and plain fixtures share the engine.
`test_jaunt_mechanics.mjs` and the exhaustive `play_jaunt.mjs --all-paths` walker hold
the mechanics contract; published mobile/desktop validation is recorded with the PR.

## T-1280 â€” session travel modes and route estimates (2026-09-27)

Jaunt cards and the persistent controls offer Walk, Wagon, Horse, Fly and Instantly.
Changing mode during a leg cancels and replans from the current location to the
same stop. Manual movement pauses with Resume ride; Go straight to next stop
remains available during a moving or paused leg. Choices and inventory survive
replanning, and mode selection does not write the visitor's saved settings.

The pure estimator shares the controller's pace, altitude gain and arrival-settle
constants. Ground estimates price the router's length, flight includes ascent,
cruise and descent, and an unroutable pair is labelled approximate. Missing
positions produce no estimate. Reading/action inputs are added and the displayed
duration rounds to half-minutes. Fly is labelled a viewing convenience.

The estimator fixture and nine reducer tests pass. Published browser acceptance
passes at 390Ã—780 and 1280Ã—800, with zero page errors and unchanged saved settings.
The pilot now recommends Horse: declared reading plus measured travel took 243.3 s
against 236.5 s estimated on mobile, and 230.6 s against 227.8 s on desktop (2.9%
and 1.2% differences). Its formerly recommended walk estimates 9.5â€“10.5 minutes.
Full preflight passes all 681 steps; scoped shared smoke remains pending. Receipts and the
measurement definition are in `performance/jaunt-travel/`. This work depends on
T-1279; PR #137 remains owned by its other session.


## T-1279 â€” playable jaunt and persistent navigation (2026-09-27)

The welcome starts the five-stop pilot, with Previous/Next and End/Menu controls
outside the scrolling stop text. Cards and the drawer leave navigation clear.
Menu pauses at the current location with Resume/Restart; End cancels immediately;
Explore clears a paused session. Completion shows an outcome and route note.
No daybook persistence, ETA or mode selector is included in this ticket.

The lazy, content-neutral controller rejects stale session/leg callbacks and
applies revisited effects once. Eight reducer cases and published mobile/desktop
pilot and fixture play pass with zero page errors. The initial 680-step preflight
passed; the integrated-tree preflight also passes all 680 steps. Boot payload is 9.815 MB / 12 MB.
A focused End repeat exposed an unnecessary intermediate heading focus; removing
it brought End to 1.1 ms mobile / 0.8 ms desktop, with identical near/far framing.
All thirteen mobile and desktop shared parts pass across the recorded checkpoints.
Desktop 11 passed an unchanged isolated retry after a click timeout. Desktop 12
passed 95 assertions with zero page errors in 7m26s after its two reload waits were
aligned with the harness's existing 90-second default. All readiness and behavior
assertions remain unchanged; the original 30-second timeout readings are retained. Receipts and conditions
are in `performance/jaunts-play/`. Dev through d1024c1 is integrated; PR #137 was
completed by its other session.

## T-1253 â€” validated jaunt content and a real welcome preview (2026-09-27)

New in Chicago is now authored JSON: five short exterior stops, an optional
rest/explore preference, explicit historical claims, a continuity inference and
the reconstructed Finding Your Feet route note. Hoganâ€™s corner is the former
post office; the Democratâ€™s named building is also a former office by May 1835.
The welcome lists the lazy catalog and opens a lazy, read-only route preview with
per-stop evidence. No guided travel, ETA, reward storage or per-jaunt code ships.

The Draft 2020-12 schema and compiler validate typed destinations, date eligibility,
registered sources/locators, bounded integers and inventory, all reachable forward
states, ending reachability and cycle refusals. Review-held content is unavailable
with a reason. T-1248â€™s source index registers the pilotâ€™s claims directly. The
under-200-line authoring guide is linked from the architecture and execution plan.
Fixtures prove data-only expansion and isolate malformed content; a 27-entry
catalog is 22,322 bytes / 30,000, the real catalog 869 bytes. Twenty-five semantic
tests pass. Published browser and full gate receipts are recorded with the PR;
see docs/performance/jaunts/README.md. Playback remains T-1279â€™s work.

## T-1278 - mobile welcome (2026-09-27)

Arrival settles into Jaunts, Explore on my own and Enter Chicago. The inline picker uses T-1277 safe destinations. Start / Jaunts pauses the world and returns focus on close; help waits for first entry. Settings persist. Jaunts are explicitly forthcoming.

Shared destinations recovered from draft chicago PR #129. No separate destination model. See performance/welcome/README.md for validation and integration status.

# STATUS

## The South Division's outer books, closed â€” T-1713, 2026-09-28

Piece 2 of 2 of T-1710, which is piece 4 of 4 of T-1203. T-1712 raised the Beaubien
homestead's other two buildings; this one answers the four questions the parent asks before
this district's outer ground is done with, and **changes nothing in the town** â€” no roof, no
card, no confidence, no bake. The reading is committed at
`data/render/south_outer_close_out.json`, in deliberately the same shape as
`south_water_close_out.json`, `lake_close_out.json` and `randolph_close_out.json` so the
districts compare. Every number is read at load time off committed data or resolved by a
committed tool; none is typed. **Three of the four books close NIL, and a nil answered on
evidence is a result rather than a gap.**

**Which line the tier reading stands on.** The file declares `CORRIDOR_LINE: drawn`, because
the strip it measures runs between a block grid and a survey line and the block grid is cut
on the drawn line (T-0419). The disagreement between the two lines matters to this answer, so
both are reported rather than only the one used.

**Book one â€” the country seats, and the one that is not where its note says.** The Beaubien
places close: four records (`jb_beaubien_homestead`, `beaubien_barn`,
`beaubien_new_residence`, `beaubien_trading_post`), all on the United States Reservation, all
inside the modelled box, all on the reservation's own permitted list, all with 4 of 4
footprint corners inside the derived polygon. Harmon's does not. `harmon_log_cabin` stands on
`blk_randolph_franklin#02` â€” **plat lot 3 of the Original Town, fronting Randolph, barring
another roof on that lot** â€” while its own `position_note` says it "sits in the South Division
outer band". And the note's negative fact is stale: it says Harmon's pre-empted hundred and
forty acres, whose north boundary his record puts near Sixteenth Street, is "two kilometres
south of the modelled ground", but Sixteenth Street at Prairie stands at local **N -2949.59**
and the box's south wall at **N -3800.0**, so that line has been **850.4 m inside** the
modelled ground since T-0464 carried the wall to Twenty-Second Street. The cabin stands
**2 677.6 m north** of it. **The record was deliberately not moved.** Nothing in this corpus
states land south of Twelfth Street â€” `evidence_limit` writes every vertex below N -2149.40
conjectural and the terrain spec calls the 1650 m below it frame, not reconstruction â€” so
re-seating him there would trade an invention on modelled ground for an invention on
conjectural ground, which is not a reading. The discrepancy is written onto **T-1215**, the
convergence closeout, with its measurements.

**Book two â€” the Fort Dearborn Addition, refused, and four years late.** T-1710 asks for "the
Fort Dearborn Addition dwellings the no-build ground allows" and the answer is **none**. The
ground is the United States Reservation, refused `documented` in
`1835_no_build_ground.json` on three sources: 75.69 documented acres (65.70 derived,
a 13.2 % shortfall the file records rather than tunes away), unplatted, crossed by no street,
and under Jean Baptiste Beaubien's pre-emption certificate of 1835-05-28 â€” recorded
1835-06-26, five weeks old on the scene date, voided in *Wilcox v. Jackson* four years later.
`measure_no_build_ground.py` finds **26** records standing there, **0** of them unpermitted,
and **0** cells of under-coverage. And the Addition itself is not 1835 ground at all: Fergus'
Directory of 1839, printed pages 47â€“49, prints *"LOTS SOLD IN FT. DEARBORN ADDITION TO THE
TOWN OF CHICAGO, from the 10th to the 24th June, 1839, inclusive â€” known as the Beaubien, or
Reservation, lands"* â€” **268 rows, 96 bidders named, $100,000 printed in aggregate**, a sale
that opened three years and eleven months after 1835-07-01. In July 1835 there is no lot to
build on, so the ask is answered nil on a page this project has read rather than on an
absence.

**Book three â€” the lakefront tier is zero-width, and it is struck.** T-1203 names "the
lakefront tier between the fort reservation and the plat" as one of this district's four
grounds. There is no tier. G1 of `wright_1834_gcps.json` is the PLSS corner of sections
9/10/15/16 â€” State at Madison â€” and the file already records that it is the plat's SE corner
and that Madison's line continues east as the reservation's south boundary, so the plat's
south-east corner and the reservation's south-west corner are **one committed point**.
Measured between the plat's east block-grid boundary and the reservation's west survey line:
**2.054 m at local N -400 and 2.762 m at N +20**. A lot here is 24.4 m of frontage; the
narrowest thing the plat cuts anywhere is an 18 ft (5.49 m) alley. The strip is **6.3 times
narrower than the georeference's own RMS (17.5 m) and 11.8 times narrower than its worst
residual (32.7 m)** â€” narrower than the error bar on either line that bounds it, which is the
honest reason to call it zero rather than to call it two metres. The same abutment shows on
Madison's axis with the same small disagreement: Madison's drawn record is a ruled horizontal
line at N -519.05 and the reservation's south line passes State Street at N -525.27, **6.22 m
apart**, inside the datum's 17.5 m. Neither line is re-cut onto the other here â€” T-0419 ruled
that the block grid is not re-cut onto survey control, and this reading takes no step toward
it.

**Book four â€” the headroom, stated, and it is nil of its own.** `reconcile_665.py --check` is
green on this tree: 431 standing records, 418 physical roofs, **250 remaining of 668**, of
which the South owes **134**. All 134 are inside the Original Town â€” **8** on two platted
blocks with coverage (`blk_south_water_wells`, `blk_south_water_dearborn`) and **126** gated
on street control the plat has not been given (`blk_south_water_market` 27,
`south_plat_beyond_committed_control` 99). **Not one is dealt to the reservation, the tier,
the Addition or a country seat**, and the reason is structural rather than an oversight:
`1835_off_plat_ledger.json` draws 177 parcels of off-plat ground and **every** tier lot, tier
block and addition block in it belongs to the school-section tier, the north-division tier or
Kinzie's Addition. The South Division's outer ground appears only as survey tracts â€” the
coarsest granularity that file has â€” so `may_raise_a_slot` is **0** across all 177 rows and
150 of them carry no row in the roof programme at all. This district's outer books therefore
close **on a nil balance rather than on a remainder**, and the thing that moves the South's
number next is the street carry (T-1707), not this ground.

**What this does not close, said plainly.** T-1203's stop condition is "the district's slot
list reads built, every roof occupied". This closes the first half for the outer ground and
makes no claim about the second; occupancy of the outer records is the parent's own remaining
business. **One ground of T-1203 is carried by no piece of it:** its body lists "the Michigan
Street tract's five seated blocks" first among the four grounds of this band, the other three
are the titles of its four pieces, and `docs/RESEARCH/michigan_st_tract.md` is titled "The
Michigan St tract north of Kinzie Street" and reads it off Wright's 1834 survey in the
**North** Division. Either the parent's ground list names a tract that is not in its district
or a ground of this one has fallen between two tickets; this run recorded it and adjudicated
neither. Both findings are on **T-1215**, not filed as new lines â€” the queue stands at its
ceiling and its own header asks for the finding on an existing ticket first, and T-1203 and
T-1710 are both closed, so a paragraph on either would be unread.

## The Randolph tier's books, closed â€” T-1688, 2026-09-27

Piece 4 of 4 of T-1202, and the last of them: T-1685 named this tier's keepers, T-1687 settled
the civic band beside the square, and T-1686 gave its larger houses their centre halls. This
piece answers the four questions the parent asks before the district is done with, on the
published tree, and **changes nothing in the town**.
The reading is committed at `data/render/randolph_close_out.json`, deliberately the same four
books as `data/render/lake_close_out.json` and `data/render/south_water_close_out.json` so
the three districts compare. Every number in it is derived by a tool the file names; none is
typed.

**The tier** is the six subdivided units bounded north by Randolph and south by Washington:
`blk_randolph_{market,franklin,wells,clark,dearborn}` in the South Division and
`blk_randolph_clinton` in the West. The seventh cell of the row, `blk_randolph_lasalle`, is
the Public Square â€” reserved, not subdivided, holding the log jail at its north-west corner â€”
and it is out of the count by the reservation record rather than by omission.

**T-1686 landed while this was being read, and it moved nothing in these books.** It is a
re-derivation on the tree that carries it, not a forecast of it. The reason it moved nothing is
worth recording: it gave seven already-standing H1/H2 houses the centre hall their crosswalk
entry requires, which is a change of *variant* and not of family or footprint. Every figure
below is identical to the one this reading derived one commit earlier, save the frame budget,
where seven centre halls cost 48 triangles.

**Book one â€” the refusals: one deferral, and closing it empties the whole tree's log.**
Exactly one entry in the tier: `blk_randolph_dearborn` defers an I3, and the refusal was about
an archetype rather than about the block. I3 resolves through the `fort_structure`
placeholder, whose entire vocabulary is garrison words, so massing an anonymous town civic
roof through it would have stood a garrison building three quarters of a kilometre from the
fort. **It is resolved, upstream and on evidence, and the answer is that the family has no
anonymous slot left to build.** `tools/measure_institutional_claims.py --gate` reads the I3
target of 3 exhausted by three *named* records with a roof on the scene date â€” the log jail,
the council house and the 1832 lighthouse â€” and asserts in its own words that "no anonymous
roof carries I1 or I3". T-1687 closed the same question from the other side for this tier: the
three civic roofs stand and no fourth is invented. The schedule agrees, all six units reading
`roofs 0` and `families {}`. With this one discharged the committed tree has no live deferral
left; the log held two, and T-1683 resolved `blk_lake_franklin`'s F3 the same day.

**A unit can carry more than one parcel recipe, and reading one per block hides a refusal.**
Three of the six units here carry more than one â€” `blk_randolph_dearborn` three and
`blk_randolph_market` two, one per programme phase that dealt them â€” and only the FIRST of
dearborn's three holds the deferral. Indexing `1835_platted_block_parcels.json` by
`block_id` collapses them and reports this tier clean. It is not clean, and this reading found
that out by doing it wrong first.

**Book two â€” the headroom: zero, and the tier is at capacity.** All six subdivided units read
`at_capacity` with headroom 0 on a `tools/reconcile_665.py --check` that is green here, so the
parent's "or its headroom stated" clause resolves to zero and the answer is the stronger of
the two the ticket allows. Six free lots remain across the tier and not one can carry a roof:
capacity is reckoned on roofs and not on lots, and the roof count is met. That is the same
finding T-1683 reached on the Lake district, T-1682 on the Lake frontage and T-1647 on the
South Water row, and it is what makes the rest of this tier's work a question of what its
standing roofs ARE and never of adding one.

**Book three â€” the dwellings falling southward. Two of the clause's three halves hold, and
the third names a term the programme does not have.** Measured across the three committed rows
of the South Division's plat, north to south:

| row | roofs/block | homes | D1â€“D3 /block | D4â€“D7 /block | D4â€“D7 mean | H /block |
|---|---|---|---|---|---|---|
| South Water â†’ Lake | 14.8 | 37.8 % | 4.0 | 1.2 | 53.0 mÂ² | 0.4 |
| Lake â†’ Randolph | 13.5 | 55.6 % | 3.17 | 4.0 | 55.0 mÂ² | 0.33 |
| Randolph â†’ Washington | 11.8 | 72.9 % | 4.6 | 3.0 | 59.0 mÂ² | 1.0 |

Density falls southward monotonically â€” 14.8, 13.5, 11.8 roofs per block â€” which is precisely
what the authored policy claims in its own words ("mixed blocks with density falling rapidly
southward", `1835_building_inventory.json` `districts.south.character`). The mix falls with
it: D4â€“D7 thins from 4.0 roofs per block to 3.0 while D1â€“D3 thickens from 3.17 to 4.6, and D7,
the largest dwelling family the programme has, puts one roof on the Lake row and none on this
one. The South Water row is not in that line â€” it is the commercial core the policy's own
sentence sets apart with "then", and its dwellings are few because its frontage is trade.

**What does not fall is SIZE, and it must not be made to.** A D4â€“D7 roof gets *larger* going
south: 53.0, 55.0, 59.0 mÂ². The reason is in the generator and not in the town â€” a footprint
is sampled deterministically inside the family's authored band, so a D5 here and a D5 on Lake
Street are drawn from one band and the difference between them is sampling. There is no
size-by-latitude term anywhere in the programme, and inventing one to satisfy a sentence would
be tuning the data to the wording. The mean over *all* homes rises too (42.7, 48.0, 49.1 mÂ²),
and that is the H band doing it: 1.0 H1/H2 house per block here against 0.33 on the Lake row,
at a mean of 88.8 mÂ² â€” the merchant and professional seats T-1199 put in this tier and
T-1202's own acceptance asks for in the same sentence as the clause above. So the rise is the
parent's requirement being met, not the policy being broken. **T-1695** carries the wording.

**And the modelled edge is no longer at Washington, which changes what the clause is about.**
T-0026's blocker was terrain and is not any more: T-0219 carried the heightfield to local
N âˆ’3800 m, 3274.8 m past Madison Street's line at State, and the plat's last tier â€” six blocks
and 48 lots between Market and State, 6.31 ha â€” now stands on modelled ground at all 24 of its
block-boundary points, with `tools/measure_southern_ground.py --gate` reading SOUTHERN GROUND
PASS and no committed platted block off the field. What still ends at Washington is the
committed **street control**: the plat's seven northâ€“south columns all end at local N âˆ’400,
cut where the ground used to stop, and `thompson_lots.json` holds no `blk_washington_*` block
at all â€” the last tier is a projection of the plat frame, not committed geometry. So the
ground south of Washington holds no roof because it has no block, not because the terrain
refuses it. **T-1696** carries the columns.

**Book four â€” the frame budget: PASS at both viewports, on the published mirror.** The
tightest margin in the town is desktop, the balanced tier, from the forks at Wolf Point â€”
1,256,544 triangles of 1,280,000 on 145 draw calls, 23,456 clear,
1.83 % of the ceiling. Mobile's tightest is balanced at Lake
Street and Canal, 1,106,903 of 1,280,000,
13.52 % clear.

**It has drifted 828 triangles since T-1683 read it two commits back, and this diff is none of
it.** Because this reading measured the sweep at all three heads, the drift can be attributed
rather than merely noticed: T-1683 priced the stand at 24,284 clear (1.90 %), it was 23,504
(1.84 %) after T-1681, and it is 23,456 (1.83 %) after T-1686
here. 780 of the 828 are T-1681's three Lake Street cottages becoming store-residences â€” a
shopfront carries more geometry than a cottage â€” and 48 are T-1686's seven centre halls. That
is the point of recording the figure at each head rather than once: a reading that raises no
roof must be able to show that the movement was somebody else's. Worth watching, not yet worth
acting on â€” the town spent 828 of its remaining 23,456 on ten buildings â€” and the
binding stand has not changed.

**What the books leave open â€” three roofs, and the reason is a selector.** Sixty-nine roofs
stand in the tier's six units: 49 carry a keeper, 17 are ancillary by rule (a stable, a barn,
a privy, a woodshed has no keeper of its own and never wanted one), and **3 are neither** â€”
66 of 69 accounted, 95.7 %, against the Lake district's 48 of 92 when T-1683 read it. So the
parent's stop condition, *every roof occupied*, is three roofs short in this tier, and the
three are named: `recon_1835_west_018` (D5), `_019` (D7) and `_021` (D6), all in
`blk_randolph_clinton`, all raised by the west phase under its own ids.
`1835_roof_keepers.json` declares its scope as `block_prefixes: ['blk_south_water_',
'blk_randolph_']`, so the pass selects roofs by **id prefix** â€” but which block a roof stands
in is a matter of **position**, read off the record's position point against the committed
block boundary, which is the T-A7 finding. A roof standing on a scoped block under an unscoped
id is therefore invisible to the pass by construction. T-1685 wrote 23 keepers and refused 63
on that scope and these three were never offered to it. That is a fault in how the layer
selects and not a missing household, and it will recur in every district where a block's
ground and a roof's id disagree. **T-1697** carries it.

## H1's centre hall, and H2's two refused variants â€” T-1686, 2026-09-27

Piece 2 of 4 of T-1202. The Randolphâ€“Washington tier's merchant and professional seats
stand as H1/H2 houses and not cottages.

**What was wrong.** `plan` is the room arrangement behind the wall and it is what decides
where the front door goes: `hall_parlour` puts it off centre against the partition and
spaces the openings unevenly; `centre_passage` is the symmetrical five-bay front with the
door in the middle. Which families get which was decided **five times**, once inside each
anonymous parcel, beside the form values â€” and, exactly like the shed rule
`tools/roof_form.py` was written for, the five had already drifted from one another:

| parcel | centre passage for | five bays for | chimneys |
|---|---|---|---|
| `generate_block_infill.py` | D7, H2 | D7, H2 | 2 for D7 and H2 |
| `generate_inferred_infill.py` | D7, H2 | D7, H2 | 2 for H2 only |
| `generate_north_infill.py` | D7, H2, **H3** | D7, H2, **H3** | 2 for every H |
| `generate_west_infill.py` | D7, H2 | D7, H2 | 2 for every H |
| `generate_inferred_households.py` | **any two-storey** | any two-storey | 1 for everything |

**And all five refused H1 the centre hall its own crosswalk entry requires.** H1's
`required_variant` is literally `center_hall_one_and_half`; its variants line reads
"5 bays; center hall; kitchen ell; small porch"; and it is the only family of the
thirty-five whose entry names a centre hall, and the only one that states a BARE bay
count rather than a range. Nothing failed: `validate()` was satisfied, every band the
crosswalk authors was met, and `band_notes` correctly reported H1's `plan` as a value the
specification speaks to â€” while the value was the opposite of what it says. **Seven roofs
stood on it**, three of them in the Randolph-Washington tier, where the placement policy's
`merchant_and_professional_dwellings` clause seats the town's merchants and professional
men, one of them (`blk_randolph_wells_h1_02`) on the same block as the tier's only seated
merchant household.

**The repair, and what it deliberately does not repair.** The reading lives once, in
`tools/house_front.py`, and all five parcels ask it. The two readers are **additive**:
each takes the parcel's own default and returns it untouched unless the family's own entry
states otherwise, which exactly one family does. So the four disagreements in the table
above are **filed, in `house_front.KNOWN_DISAGREEMENTS`, and not swept** â€” each of them
moves committed roofs that somebody adjudicated (H3's centre passage in the North, D7's
second chimney, the households parcel's storey-keyed rule), and a redeal is not licence to
move a roof nobody asked about. The seven H1 roofs are re-baked in the same commit.

**The other half â€” what H2's entry offers that this town refuses.** H2's variants are
"Greek doorway; corner boards; 1-2 chimneys" and its roof line is "side gable or hip".
Measured against what `frame_dwelling` builds:

* **corner boards and the one-to-two chimneys already stand.** The trim IS the
  construction argument and the corner boards follow the stud module
  (`frame_dwelling.py` L52); both committed H2s carry two chimneys.
* **the hip is refused, loudly.** `frame_dwelling_params.ROOF_TYPES` is gable and shed:
  "a hip, gambrel or mansard roof on a Chicago house in 1835 would be a claim rather than
  a default, so the archetype refuses it loudly instead of quietly substituting a gable".
  Until now it *was* substituted quietly, because nothing on the record said the offer had
  been declined.
* **the Greek doorway is refused BY DATE**, and the date stands on a committed record
  rather than on a comment: `data/exclusions.json` Â§ `clarke_house` â€” the earliest Greek
  Revival house in Chicago, "Built 1836, and well outside the platted town in any case",
  earliest scene 1837. So no entablature, corner pilaster or portico stands on a roof of
  1835-07-01.

Both refusals are now written onto the record a visitor opens, beside the sentence that
already says which archetype the H family resolves through. Prose is not hashed into
`generators/mesh_inputs.py`'s staleness recipe, so recording them moved no geometry.

**What is NOT raised, and why.** The kitchen ell and the small porch H1's line also names
are selectable variants beside the required one, and an ell is a footprint fact â€” the
archetype refuses a record whose `ell` and whose polygon disagree â€” so raising one is a
question about the ground a house stands on, not about the face it shows the street. Left
for the tier's remaining pieces and said on the record rather than done quietly.

**Held by** `tools/test_house_front.py` (+ `--self-test`), in `tools/check.sh` beside the
store-variant gate.
## Lake Street's Clark corner stands as shops â€” T-1681, 2026-09-27

Piece 2 of 4 of T-1201, and the same shape as T-1647 one street north. **There is no
ground to raise a store on.** Both blocks this piece owns read `at_capacity` in the
665-roof programme â€” `blk_lake_clark` 16 standing roofs, `blk_lake_dearborn` 13, headroom
0 on each â€” and `blk_lake_clark`'s one remaining free lot is lot 5, on Randolph, which
its own end rule keeps open. So what the Lake business front is made of can only change
by saying what the roofs standing on it **are**.

**What is wrong, measured on the committed tree.** The Lake faces of the two blocks â€”
lots 0, 2, 4 and 6 of each, every one fronting a street this project grades `principal` â€”
carried **15 principal roofs, 4 of them store or workshop families**, against the
**0.6818** documented trade share T-0213 reads off a principal street. `blk_lake_clark`'s
own Lake face carried nine principal roofs and three stores, and the three units of the
party-line run on lot 0 â€” a D1 log cabin and two frame cottages â€” each had a documented
Lake Street trade seated in it by the street-face register.

**What this piece did.** Those three slots are re-familied in
`1835_platted_block_parcels.json` (`refamilied`, T-1681) and their ids move with the
family: `_d1_01` â†’ `_c1_01`, `_d3_02` â†’ `_c2_02`, `_d5_03` â†’ `_c3_03`. C1, C2 and C3 are
the three store families the programme still has headroom for in the south division (17
of 18 standing, 11 of 13, 12 of 17), so the face gains three stores and no family passes
its target. **C4 is refused and the refusal is the ground's**: a wide mixed block bands at
28â€“36 ft of frontage and no unit of this run has more than 22 ft of it.

**Which stands where is the block's own end rule, not an allocation.** T-0079 seated this
run under the rule that the better roof stands at the town-centre end â€” east, toward
Dearborn and the only crossing of the main stem in July 1835 â€” so the row now ascends
along the face: C1 at 5.34 m wide and one storey on the Clark corner, C2 at 6.18 m and a
storey and a half in the middle, C3 at 6.53 m and two full storeys closing the run,
18.05 m of the lot's 21.75 m of buildable frontage. Same lots, same 0.80 m street line
(L177), same party walls, same bottom tier; nothing is promoted and no occupant is
invented.

**The business allocation re-paired itself, and that is the policy working.** Street-face
adoption ranks a face's documented businesses by evidence and pairs them with its free
roofs **in id order**, writing `order_is_a_claim: false` on every row. Three ids moved, so
the Lake face's trades re-paired: W. G. Blanchard and G. Blanshard take the first two
units, Dr. W. G. Austin's botanic practice the third, and Sarah D. Howe's dress and cloak
making moved along the same street to `recon_1835_blk_lake_franklin_c2_01` â€” one of the
two store-residences T-1682 raised on the Franklin block hours before this landed, which
is the same policy re-pairing across the whole of Lake Street rather than within one
block. None of those pairings is evidence, and none of them chose a family.

**The re-cut on `dev` moved that last pairing and nothing else.** This piece was measured
and baked against a tree that predated T-1682 (#131), T-1675 (#126), T-1624 (#127),
T-1685 (#134) and T-1687 (#136), and the merge was re-derived rather than resolved:
every layer that names a roof id was rebuilt by its own tool on the merged tree â€”
`adopt_street_faces`, `location_reconciliation`, `location_spend`, `seat_platted_ground`,
`seat_known`, the manifest tail from `location_spend` down, `redeal_anonymous_roofs`,
`build_order_book_1835`, `compile_source_use` and `compile_scene` â€” and the Newberry
index re-parsed over all four volumes, because the STRUCTURE name layer is one of its
inputs. `validate.py --stale` reads 423 of 423 assets matching their inputs, so no mesh
was re-baked for the re-cut: the three masters this piece raised still answer for the
records that stand on them.

**And the order book's stores row has now been swept three times in one afternoon, which is
this entry's own finding.** T-1680 sent it to T-1682; T-1682 measured its own second half,
could not spend it, and sent it to T-1681 "and the row moves to T-1682 when it closes with
the cell still owing" â€” overtaken within the hour, because T-1682 merged the same afternoon
and was `done` by the time T-1681 came to close. T-1683 was then the last live child of
T-1201, and it merged too (#138) while this piece was being re-cut. **T-1681 closes with
this pull request, so all four children of T-1201 are now closed and the split parent has
no live descendant either** â€” there is no ticket left in that family to name. Naming one
anyway lands `ticket_liveness.py`'s own failure shape: the gate reads `review`, which is
live, and the `done` that takes `dev` red arrives after the gate has passed, when the
settle workflow runs.

So the cell gets a ticket of its own, filed the way T-1684 was filed for the workshops row
beside it â€” by the run that found the hole, carrying the measurement. **T-1694**: on the
merged tree the cell reads **41 standing of 42, one owed** (the three roofs this piece
re-familied plus T-1682's two), and every block of the Lakeâ€“Randolph tier reads
`at_capacity`, so the last south store has no ground in the platted core to stand on. That
is a question about where it goes, and it is not this piece's to answer â€” re-familying a
fourth roof to close the cell would be inventing a trade, which is the refusal
`blk_lake_dearborn` is already recorded under below. The workshops row stays on T-1684 at
10 of 15.

**`blk_lake_dearborn` moves nothing, and that is a measurement.** Its Lake face already
carries the two trade roofs the evidence gives it â€” `dole_warehouse_south` and
`mason_blacksmith_shop` â€” with St Mary's church on the lot 6 corner. The four anonymous
roofs left on it (`recon_1835_south_d3_017`, `_d1_018`, `_d4_019`, `_d6_020`) carry **no
occupant at all**, so the test that moved the three above does not reach one of them; and
none is this recipe's to move in any case, because all four belong to
`phase1_south_mixed_blocks`, whose re-family route is the adjudicated ledger at
`data/reconstruction/1835_roof_redeal.json`. Re-familying a roof that carries no trade
would be inventing the trade.

**The order book's dead rows, swept, because they were the gate in the way.** T-1201 was
split on 2026-09-27 without its `STRUCTURE_TICKETS` rows moving with it, so
`structures/stores_mixed_use/south` (6 owed) and `structures/workshops/south` (5 owed)
have been ordering work from a ticket nobody can claim and
`build_order_book_1835.py --build` has refused to re-derive for **every** child of T-1201
since. Both rows go to **T-1682**, the only child that still owes both kinds of roof in
its own words and that outlives the two pieces above it; `inns_taverns/south` stays on
T-1201 by the `lawyer` rule, because it orders 0 against 5 standing and the id there is
the record of who filled it. The reasoning is written into the table so the next sweep
does not flip it.

**Left as written, deliberately.** `docs/unreal/prototype/import_report.json.txt` and
`renderers/unreal/receipts/mac-253f02657.json` still name the old ids. They are dated
import receipts and rewriting one falsifies it. Every other file naming them is renamed
or re-derived, including L144's `**Covers:**` list, L177's decision and L266, whose
population drops to 73 â€” 59 log dwellings and 14 fort structures â€” because the Clark
corner's log cabin left it for the framed one, the second time that has happened and the
second time for the same reason.

**Verification.** `tools/check.sh` â€” 675 steps, none red; baked `--only` the three records plus
`..._south_water_clark_d4_02` and `..._south_water_lasalle_d3_03`, whose siding stock
re-dealt when the id set moved.

## The Lake district's books, closed â€” T-1683, 2026-09-27

Piece 4 of 4 of T-1201. The three build pieces raised and re-familied this district's
roofs; this one answers the four questions the parent asks before the district is done
with, on the published tree, and **changes nothing in the town**. The reading is committed
at `data/render/lake_close_out.json` â€” every number in it is read off the committed data or
off `tools/measure_detail_ceilings.mjs`, none is typed â€” and it is deliberately the same
four books as `data/render/south_water_close_out.json`, so the two districts compare.

**The district** is the seven Lakeâ€“Randolph blocks: `blk_lake_{market,franklin,wells,`
`lasalle,clark,dearborn}` in the South Division and `blk_lake_clinton` in the West.

**Book one â€” the refusals: one deferral, and it is the deferral this project learned the
rule from.** `generate_block_infill.py` refuses four families by name (I1, I2, I3, F3) and
a slot dealt to one may only be left unbuilt by naming it in its block recipe's `deferred`
list with its reason; the generator raises `SystemExit` on a shortfall it cannot read back,
on a deferral of a family it does not refuse, and on a family both built and deferred.
Across the district there is exactly **one** entry â€” `blk_lake_franklin` defers an F3, the
large river warehouse the schedule dealt it â€” and it is one of only two in the whole
committed tree (the other is `blk_randolph_dearborn`'s I3). T-0028 found it on 2026-08-28
by opening this very block and being unable to build the F3, 134 m from the nearest water,
the farthest of any platted block in the town but one.

**It is resolved, upstream and on evidence.** The stopgap was to put F3 in the generator's
`REFUSED_FAMILIES`, which treated a fault in the DEAL as a fault at the block and let
deferrals accumulate. T-0316 moved the repair to the deal, and on this tree
`tools/reconcile_665.py --check` prints `waterside (T-0316): F3, W5 require water â€” no
platted block was dealt one`. So the deferral cannot recur. **The roof is not dropped**: it
is still owed, the schedule still counts it, and it belongs to the wharf and landing ground
beyond South Water and Market that `generate_river_wharves.py` places against the committed
bank. That the deal ever sent an F3 inland is T-0275's, against the deal and not this block.

**And four of the seven units have no log at all, which is a different fact from an empty
one.** `blk_lake_wells`, `blk_lake_lasalle`, `blk_lake_dearborn` and `blk_lake_clinton`
were never dealt by `generate_block_infill.py`; their roofs came from the earlier
`phase1_south_mixed_blocks` and West parcels and from documented and inferred-household
records. An absent log and an empty log are not merged here.

**Book two â€” the headroom: the district IS at capacity, which is the stronger of the two
answers the parent allows.** `reconcile_665.py --check` green; programme at 410 standing,
258 remaining of 668.

| unit | district | lots | capacity | standing | free lots | headroom | state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `blk_lake_market` | south | 8 | 31 | 10 | 1 | 0 | at capacity |
| `blk_lake_franklin` | south | 8 | 31 | 14 | 1 | 0 | at capacity |
| `blk_lake_wells` | south | 8 | 31 | 14 | 0 | 0 | at capacity |
| `blk_lake_lasalle` | south | 8 | 31 | 14 | 0 | 0 | at capacity |
| `blk_lake_clark` | south | 8 | 31 | 16 | 1 | 0 | at capacity |
| `blk_lake_dearborn` | south | 8 | 31 | 13 | 1 | 0 | at capacity |
| `blk_lake_clinton` | west | 8 | 31 | 11 | 1 | 0 | at capacity |

All seven read `at_capacity` with headroom 0, so the "or its headroom stated" clause
resolves to zero. The five free lots the units still show cannot carry a roof: capacity
here is reckoned on roofs, not on lots, and the roof count is already met. This is the same
finding T-1682 reached on the Lake frontage and T-1647 on the South Water row, and it is
what makes the district's remaining work a question of what the standing roofs ARE.

**Book three â€” the cottages and yard buildings behind: built, and the count is the
answer.** Measured with `reconcile_665.py`'s own `standing_roofs()`, the function the deal
counts with, grouped by the block each roof's position point falls in.

| unit | roofs | D3â€“D6 cottages | D1â€“D2 cabins/shanties | D7+H houses | A yard buildings | business/civic |
| --- | --- | --- | --- | --- | --- | --- |
| `blk_lake_market` | 10 | 3 | 2 | 0 | 2 | 2 |
| `blk_lake_franklin` | 14 | 6 | 3 | 0 | 3 | 2 |
| `blk_lake_wells` | 14 | 7 | 2 | 0 | 2 | 3 |
| `blk_lake_lasalle` | 14 | 6 | 1 | 1 | 2 | 4 |
| `blk_lake_clark` | 16 | 7 | 2 | 1 | 2 | 4 |
| `blk_lake_dearborn` | 13 | 4 | 2 | 2 | 2 | 3 |
| `blk_lake_clinton` | 11 | 4 | 2 | 0 | 3 | 2 |
| **district** | **92** | **37** | **14** | **4** | **16** | **20** |

Every one of the seven units carries cottages behind its frontage and at least two yard
buildings, so T-1201's "D3â€“D6 cottages behind on the alleys, A-family yard buildings per
household" is met in KIND on every block. It is **not** met in the ratio the second half
implies: 16 yard buildings stand behind 55 dwellings, roughly one in four. **That gap
cannot be closed on this ground, and saying so is the point** â€” the district is at capacity
at headroom 0, so a privy or stable added here would have to come out of another district's
remainder, and the programme's whole discipline is that a family cap is never quietly
exceeded to make a block look complete. The A-family targets are the town's, not this
district's (42 stables, 31 barns, 40 privies, 28 woodsheds, 17 small utility roofs across
668 roofs), and what stands here is this district's share of them. A yard "per household"
is a claim about the TARGET, and it is filed against the deal as **T-1692** rather than built past the cap.

**Book four â€” the frame budget, on the PUBLISHED mirror: PASS at both viewports, and there
is MORE room than when the warning was written.**

| tier | ceiling | worst desktop | margin | worst mobile | margin |
| --- | --- | --- | --- | --- | --- |
| `full` | 1,460,000 | 1,408,278 (the forks) | 51,722 | 1,253,491 (Lake at Canal) | 206,509 |
| `balanced` | 1,280,000 | 1,255,716 (the forks) | **24,284** | 1,106,067 (Lake at Canal) | 173,933 |
| `light` | 825,000 | 772,454 (the open aerial) | 52,546 | 698,441 (the open aerial) | 126,559 |

Desktop `balanced` at the forks is the binding constraint at every reading, and it clears
by **1.90 per cent** of its own ceiling. T-1674 read the same sweep on dev at `c164f8ae`
and priced it at 22,880 â€” 1.79 per cent â€” and warned that T-1201 raises a block core into
the same frusta with about fifteen freight sheds of room left. **Measured after T-1201's
three build pieces: the margin went UP by 1,404 triangles.** The Lake core did not spend
the headroom T-1674 was worried about, so the Randolphâ€“Washington tier (T-1686, T-1688)
still has that room to deal into. This reading does **not** claim to know which of the
eleven commits between the two trees moved the number â€” T-1680's forge chimneys and
T-1624's plat-level placements both add, while T-1677 closed a hole in the far ground the
forks stand looks straight across, and only a per-commit sweep could apportion it. What it
establishes is the direction, which is the question the next parcel asks. No re-budget is
proposed.

**What this does NOT close.** T-1201's stop condition is "the district's slot list reads
built, every roof occupied". The first half is met; the second is not. Of the district's 92
roofs, **59 carry neither `occupants` nor a `resident_assignment`** â€” 15 of them ancillary,
where a yard building with no household of its own is the model working, and **44 raised as
dwellings, businesses or civic buildings that stand empty**. Ids are named in the reading.
The reason the count is so much larger than South Water's eleven is that
`data/reconstruction/1835_roof_keepers.json` declares its scope as `south_water` and has
never been run on this district: there the keeper layer had spent what it could and T-1675
holds the residue, here nothing has been spent at all. T-1685 is extending the same layer
to the Randolph tier; the Lake district needed the same pass and had no ticket, and this
run files **T-1691**.

**Verification:** `./tools/publish.sh`, then `./tools/check.sh`, then the smoke legs
`tools/smoke_budget.mjs --for-diff` names for this diff.

## The civic band beside the public square â€” T-1687, 2026-09-27

Piece 3 of 4 of T-1202, and the district's civic band turns out to be a closed book with one
debt left inside it. The reading is written up as Â§8 of
`docs/RESEARCH/civic_public_buildings_1835.md`; the short of it:

| the question | the answer, and what says so |
| --- | --- |
| I1 worship slots dealt to this district | **none**, across all nine deals its six blocks carry |
| I2 school slots dealt to this district | **none** |
| I3 civic slots dealt to this district | **one**, deferred on `blk_randolph_dearborn`, and T-0032 settled the family's live remainder at zero |
| the roofs the dossier does allow | 4 I1, 2 I2, 3 I3 â€” all named records, none of them in this tier |
| what the square carries on 1835-07-01 | the log jail, standing; the estray pen, roofless; nothing else |
| no fourth civic roof | `measure_institutional_claims.py --gate` at 4/4, 2/2, 3/3, zero anonymous |

**The debt was in the court-house record, and it had been unblocked for five weeks.** The
dossier's Â§7 has said since 16 August that two Andreas readings were owed to
`cook_county_courthouse_1835` â€” the **north-east corner** and **brick** fabric, both in the one
sentence that dates the building out of this scene â€” and that applying them "needs a bake,
because a changed form value stales the mesh". T-0139 retired that mesh on 23 August, for the
unrelated reason that the bake cannot reach a phase no scene resolves, and wrote into the record
that the two amendments were thereby unblocked: *"There is no mesh to stale."* Nobody came back
for them, because the page that tracked the debt still priced it as geometry. Both are applied
now. `position` goes to `inferred` â€” documented corner, derived coordinate, the same rule the
jail and the pen stand under on this block â€” and `form.construction` to `brick` at `attested`.
No coordinate moved.

**Two of the seven things this project had made up about the court-house are withdrawn**, and
one of them is an admission retired: L61's "sting in the tail" recorded the risk that the
north-east corner was an 1837 description leaking backwards into an 1835 record, and the passage
that dates the building gives that corner to THIS court-house. L264's brick population is
restated from three records to four, with the fourth taking no course â€” it draws nothing.

**What is owed after this is an archetype, not a citation.** `outbuilding` cannot build brick,
so the first scene to cover the fall of 1835 will refuse this phase rather than build a plank
court-house. That is the wanted failure in the wanted place, and it belongs to whichever parcel
builds that scene, together with the placement `measure_reserved_ground.py` already prints: the
building's corner is set on the block's corner, so it reads 1 of 4 corners in and overhangs
Randolph Street as the plat module draws it.

**What a visitor sees.** The jail's card and the pen's card now say what the square held on the
day â€” the two later county buildings named and dated out, the east half of the block open
prairie â€” and the register of liberties drops two claims about the first court-house. Nothing in
the town moved: no roof was raised, removed or re-familied, and this district's books are
T-1688's to close.
## The Lake frontage of the Franklin and Market blocks stands as stores â€” T-1682, 2026-09-27

Piece 3 of 4 of T-1201, and the same finding T-1647 reached on the South Water row: the
composition of a business front that is already full can only change by saying what the
roofs standing on it ARE.

**The ground, measured on the committed tree.** All seven Lakeâ€“Randolph blocks read
`at_capacity` with headroom 0 in the 665-roof programme â€” clinton 11 standing of 31,
market 10, franklin 14, wells 14, lasalle 14, clark 16, dearborn 13 â€” so no roof can be
raised on any of them. And only two of the five blocks T-1682 names hold a roof this
programme may speak for at all: `blk_lake_wells`, `blk_lake_lasalle` and
`blk_lake_clinton` carry NO record this parcel authored, so their 14, 14 and 11 standing
roofs belong to the research layer and the phase-one South parcel, and a documented
building is not this programme's to re-family. That is a refusal on the committed tree,
not an omission.

**What changed: two of the five Lake-fronting authored roofs.** Both carried a documented
trade and stood in a cottage's silhouette on the town's Lake Street face:

| roof | was | now | the card that asked |
|---|---|---|---|
| `blk_lake_franklin` seq 01 | D5 deep-plan frame cottage | C2 store-residence | William Clay â€” hat manufacturing and dealing |
| `blk_lake_market` seq 01 | D5 deep-plan frame cottage | C2 store-residence | a boot, shoe and leather store on Lake street, proprietor not recovered |

C3 and C4 are refused on EVIDENCE rather than on metres: nothing on either card is
evidence of a second storey or of the capital one implies, and dealing one to make the
frontage read richer is the confidence upgrade AGENTS.md rule 2 forbids. C2's
18x30â€“22x40 ft band overlaps D5's 18x28â€“24x34, so neither roof grows past the ground
its slot already stood on.

**What is left as it stands, with the reason.** `blk_lake_franklin` seq 02 is the
uncertain dentist lodging near Lake Street â€” dentistry is a profession practised in
lodgings, not a shop with a counter, which is the ground T-1648 refused a workshop and a
school on. `blk_lake_market` seq 02 and seq 03 carry no `occupants` block at all, so no
trade asks them to be stores; seq 04 and seq 05 front Randolph and are off this ticket's
ground.

**The one thing that MOVED, and the rule that moved it.** The Market slot stood 7.0 m back
at a dwelling's typology setback, and `generate_block_infill.check_non_dwelling_slot`
refuses a C roof there â€” thirteen of the fourteen documented stores in this town stand on
the street line, so a store's claim on frontage is functional (T-0024). The roof comes
forward 5.5 m onto the same 1.5 m line every party-line run in this town already stands
on. Authored at 1.505 m rather than 1.5 m, and that is the derivation noise the generator
documents twice rather than a relaxation: at 1.500 m the footprint's corner reads 1.49 m
from the lot ring against a 1.495 m floor, because this lot's side lines are not square to
its Lake face. 1.505 m is the largest setback T-0024's own gate admits.

**What the adoption machinery then did, unprompted and worth recording.** Two shopfronts
appeared on the Lake face, so `tools/adopt_street_faces.py` re-dealt the street â€” and
which trade sits behind which counter is explicitly an allocation and not a reading of any
source. Businesses adopted into a house of trade went 21 â†’ 23 and those adopted into a
roof of no trade 18 â†’ 16. Two more of the town's documented traders now stand behind a
counter instead of in somebody's parlour, which is the business layer and the
reconstruction agreeing for the first time on this face.

**The W2â€“W4 mechanics' shops: refused, and filed as T-1684.** T-1682 also asked for the
W2â€“W4 shops to take their State and Dearborn faces. They cannot, and the obstacle is the
instrument rather than the evidence: the whole `fronts` vocabulary the 22-block recipe
uses is `lake`, `randolph`, `south_water`, `washington` â€” the four LONG faces â€” and not
one slot in this programme's history has been dealt onto a cross-street face. Every block
on those faces reads `at_capacity` or deals no W head (`blk_south_water_dearborn`'s 4 of
headroom is dealt A3, D6, D7, H1), and the only W-family roof this town holds anywhere is
`recon_1835_north_w5_040` in the North Division. So there is neither a slot to deal nor a
shop to re-family, and a short-face placement term is more than a field edit.

**The order book, swept in the same PR because it was blocking every branch.** T-1201 went
to state `split` at 17:37Z, and `STRUCTURE_TICKETS` still named it for
`stores_mixed_use/south` (6 left), `inns_taverns/south` and `workshops/south` (5 left) â€”
so `build_order_book_1835.py --check` refused the book for ordering work nobody can claim,
on dev and therefore on EVERY branch cut from it. Two finished units (PR #126, PR #127)
had already been handed on as `resume` PRs for this step, neither of which touched it. All
three rows go to T-1683, the one child of T-1201 whose own acceptance IS these cells'
question, so the row does not move again when T-1680, T-1681 or T-1682 closes â€” which is
the churn the T-1640 paragraph in that file was written to stop.

**Derived layers carried with the ids.** `_d5_01` â†’ `_c2_01` on both blocks, and every
layer that named them re-derived by its own tool: fences, dooryard plantings, planted
rows, frontage works, signboards, yard goods, the lot ledger and platted seats, the
665-roof programme, the anonymous re-audit, the street-face adoptions, liberties, the
sidecars, source use, the land tracts, the location reconciliation and spend, the address
book, the convergence reading, and the Newberry index's parse fingerprint â€” which covers
the STRUCTURE name layer, so renaming two roofs moved it and the leads were re-parsed and
re-ruled (no lead changed its ruling). The two dated Unreal import receipts are NOT
rewritten, because rewriting a dated receipt falsifies it â€” T-1483's taxonomy, the same
refusal T-1647 recorded. The clapboard-stock deal re-dealt two named frame buildings as a
consequence, so `exchange_coffee_house__frame_1834` and `sauganash_hotel__frame_1831` were
re-baked alongside the two new store-residences and `blk_lake_market_d4_02`.

**Verification:** `tools/check.sh` â€” 672 steps; and the smoke legs
`tools/smoke_budget.mjs --for-diff` names for this diff.

## South Water's books, closed â€” T-1641, 2026-09-27

Piece 4 of 4 of T-1200. The three build pieces raised and re-familied the district's
roofs; this one answers the three questions the parent asks before the district is done
with, on the published tree, and changes nothing in the town. The reading is committed at
`data/render/south_water_close_out.json` â€” every number in it is read off the committed
data or off `tools/measure_detail_ceilings.mjs`, none is typed. It was taken twice: once
on `1adfa5d2`, and again after T-1640's freight shed merged underneath it, because a
budget read on a tree that no longer exists is not a reading.

**Book one â€” the refusals: empty, and the one the district met was resolved at the deal.**
`generate_block_infill.py` refuses four families by name (I1, I2, I3, F3) and a slot dealt
to one of them may only be left unbuilt by naming it in its block recipe's `deferred` list
with forty words of reasoning; the generator raises `SystemExit` on a deferral it cannot
read back. Across the district's six units â€” the five platted blocks and the Market wedge
â€” **the deferred list is empty**. The two deferrals that do stand in the tree are
elsewhere: `blk_randolph_dearborn` defers an I3, `blk_lake_franklin` an F3. The district
did meet an F3 refusal and it was settled one level up, at the deal: `reconcile_665.py`'s
waterside rule (T-0316) reroutes an F3 off `blk_south_water_market` â€” the family's
crosswalk entry makes water access a precondition of the form and the wedge's lots do not
reach the bank â€” to `south_plat_beyond_committed_control`, and deals the wedge a C2 in its
place. A refusal resolved at the deal is why the block log reads empty, and the two facts
are worth stating together so the empty log is not mistaken for a district nothing refused.

**Book two â€” the headroom: the district is NOT at capacity, and here is what is left.**
`reconcile_665.py --check` is green on this tree and reads the 668-roof programme at 410
standing, 258 remaining.

| unit | lots | capacity | standing | free lots | headroom | state |
| --- | --- | --- | --- | --- | --- | --- |
| `blk_south_water_franklin` | 8 | 31 | 17 | 1 | 0 | at capacity |
| `blk_south_water_wells` | 8 | 31 | 12 | 2 | 4 | open |
| `blk_south_water_lasalle` | 8 | 31 | 18 | 0 | 0 | at capacity |
| `blk_south_water_clark` | 8 | 31 | 12 | 1 | 0 | at capacity |
| `blk_south_water_dearborn` | 8 | 31 | 15 | 2 | 4 | open |
| `blk_south_water_market` | 8 | 31 | 0 | 8 | 27 | gated |

Three blocks are at capacity. Two carry **8 roofs of headroom between them** â€” and that 8
is the whole programme's `schedulable_on_committed_ground`, so every roof in the 668 that
has surveyed ground under it today is on these two South Water blocks. The Market wedge is
**gated, not open**: its 27 roofs wait on street control the plat module has never reached.
The one free lot each of franklin and clark still shows is the lot T-0834 makes every block
keep open, which is why their headroom is 0 and not 1.

**Book three â€” the frame budget, on the published mirror: PASS, with the margin stated.**
T-1154's trim landed (T-1244 and T-1245, both merged 2026-09-17) and the town is back
inside all three ceilings at both viewports. `node tools/measure_detail_ceilings.mjs --only
both` on the mirror `tools/publish.sh` built from this branch over dev at `c164f8ae`:

| tier | ceiling | worst desktop | margin | worst mobile | margin |
| --- | --- | --- | --- | --- | --- |
| `full` | 1,460,000 | 1,410,306 (the forks) | 49,694 | 1,254,799 (Lake at Canal) | 205,201 |
| `balanced` | 1,280,000 | 1,257,120 (the forks) | **22,880** | 1,106,631 (Lake at Canal) | 173,369 |
| `light` | 825,000 | 773,206 (the open aerial) | 51,794 | 699,187 (the open aerial) | 125,813 |

So the build takes the margin and not the re-budget, and says so. But the margin is thin
where it is thinnest: desktop `balanced` clears by 22,880 triangles, **1.79 per cent of its
own ceiling**, at the forks. The re-read is what makes that concrete rather than rhetorical.
The first reading, before T-1640 merged, cleared by 24,420; ONE freight shed on the south
bank took 1,540 of it. At that price the margin is about fifteen sheds wide. The next build
parcel in the queue, T-1201 â€” the Lake Street and Dearbornâ€“Clarkâ€“LaSalle core â€” raises roofs
inside the same downtown frusta. Filed as T-1674 rather than left in a table: a parcel that
will breach a ceiling should find out before it bakes, not after.

**What these books do NOT close.** T-1200's stop condition is "every roof occupied", and
the district does not meet it. Of the 52 structure records on the five blocks, 22 carry
neither `occupants` nor a `resident_assignment`; 11 of those are ancillary (A1 stable, A2
barn or carriage shed, A3 privy) and an outbuilding having no household is the model
working. The other **11 are dwellings and lodging** â€” four D1 log cabins, two D2 plank
dwellings, two D3 and two D4 frame cottages and the one H1 house â€” and they stand empty.
The ids are listed in the reading. Filed as T-1675. Separately, the freight roofs the
south-bank ground rule has run out of room for are T-1672's and are not touched here.

**Why an invisible run.** Nothing in the town changed and no card moved. This is AGENTS.md
Â§ the visible-progress rule's third exemption â€” a gate blocking a visible parcel â€” and the
parcel is named: T-1200 makes "`measure_detail_ceilings.mjs` on the published tree before
pushing" a precondition of the district, and T-1201 is the successor that cannot honestly
be dealt until somebody says how much of the frame budget is left. The answer is 1.79 per
cent, and a shed costs 1,540.

## The Dearborn block's business front stands as shops â€” T-1647, 2026-09-27

Piece 1 of 3 of T-1639, and the split is the first thing this run has to report. The
parent asked for C2â€“C4 store fronts and F1â€“F3 warehouses to be **raised** on the South
Water party lines. **There is no ground to raise one on.** The owner ruled on 2026-09-26
(T-1623, option a) that the single genuinely vacant lot each of `blk_south_water_dearborn`
and `blk_south_water_wells` still holds stays open, and the other three South Water blocks
read `at_capacity` in the 668-roof programme. So the business front's composition can only
change by saying what the roofs standing on it **are**.

**What is wrong, measured on the committed tree.** The South Water frontage run â€” the
party-line row on the only street this project's own hierarchy grades `principal` â€” carries
**28 roofs: 23 cottage families, 5 stores, no warehouse**, against the **0.6667** documented
trade share T-0213 reads off a principal street. Two of those cottages carried a documented
trade on their own card: `recon_1835_blk_south_water_dearborn_d5_07`, a D5 deep-plan frame
cottage, and `..._d3_08`, a D3 one-room frame cottage.

**What this piece did.** Those two slots are re-familied in
`1835_platted_block_parcels.json` (`refamilied`, T-1647) and their ids move with the family
â€” `_d5_07` â†’ `_c2_07`, `_d3_08` â†’ `_c1_08`. Nothing else about either roof moves: same lot,
same setback, same anchor, same party line, same bottom tier. No confidence is upgraded and
no occupant is invented; the footprint is not authored here either, because
`generate_block_infill` samples a slot inside its family's own band on a stable key.

**The family is the ground's choice and the refusals are measured.** Seq 07, east of
Frederick Thomas's shop, takes **C2** (store-residence, 18Ã—30â€“22Ã—40 ft). Seq 08 stands in
the gap between that shop and `john_holbrook_store` and takes **C1**, the largest store
family that gap admits: dealt C2 the generator reports `stands 2.78 m from
john_holbrook_store` against the three-metre separation gate, and dealt C3 it `reaches past
the end of its own frontage â€¦ inside the 1.5 m margin of a side line the run does not stand
across`. T-0432's own arithmetic agrees â€” it recorded the west gap as 5.932 m.

**The business allocation re-paired itself, and that is the policy working.** Street-face
adoption ranks businesses by evidence and pairs them with a face's free roofs **in id
order**, and `order_is_a_claim: false` is written on every row. Two ids changed, so the four
documented trades on this block's run re-paired across it. The block's business front now
carries **four store roofs, every one of them occupied**, where it carried two stores and
three cottages.

**Left as written, deliberately.** The `Shipped 2026-09-11 â€” T-0432` entry below still names
`_d3_08` and `_d5_07`. It is an accurate record of what shipped that day and rewriting it
would falsify the log; the same refusal covers `renderers/unreal/receipts/` and
`docs/unreal/prototype/import_report.json.txt`, which are dated import receipts. Every other
file naming the two ids is derived and was re-derived in this commit.

**Left owed.** T-1648 asks the same question of the Franklin, La Salle, Clark and Wells runs
â€” 21 cottages â€” and T-1649 owns the crosswalk's `required_variant` silhouettes, which no
generator implements today.

## Sources browser â€” T-1276, 2026-09-27

Evidence â†’ Sources lazily loads the public catalog, with scene/all selection, citation search, type/tier/use filters and claims/entities/date/title sorting. Forty rows render initially; scrolling or Show more extends the list. The compiler adds compact confidence vectors (claims, entities; attested, inferred, reconstructed), independently checked against every edge file. A mixed-confidence entity counts once at its strongest confidence. Detail files load only on demand, with source limits, safe original/archive links, collapsed newspaper issues and typed used-for groups. No research files or derived source assets are fetched. Existing structure and person cards restore the Sources context on close; other Evidence entries have stable navigation anchors. Missing catalog data remains an explicit unavailable state. Published mobile/desktop acceptance passes: 293 registered, 223 scene-used, 40 initial rows, preserved search/filter/scroll, unavailable-catalog recovery, zero page errors. First open is 31,776 gzip bytes; the index is 108,135 raw bytes; total boot is 9.683 MB / 12 MB with no Sources module/index request before opening. Receipts are in `docs/performance/sources-browser/`; published Evidence/drawer parts 12â€“13 pass on mobile (196 checks) and desktop (198 including vendor checks), with zero failures and page errors. The combined attempt timed out during desktop; its incomplete reading is retained beside the passing standalone rerun. This staged coverage is not a full renderer verdict.

## The south bank below the bend is recut to Hathaway â€” T-1630, 2026-09-26

The owner's answer to T-1630's own question, option (b). The reading that asked it
(PR #88, `docs/RESEARCH/south_bank_swell_1834.md` Â§Â§ 1â€“5) established that the
committed bank IS Wright's ink â€” median 1.87 m, p90 3.96 m over 103 stations â€” and
that **Wright himself draws the swell** while Hathaway does not. So there was
nothing to correct on the trace's own terms, and the choice of sheet was his.

He chose Hathaway here. The bank between local E +228.91 and the La Salle mouth is
now Wright's traced line displaced **south by the two sheets' own disagreement** â€”
5.6 m at block 20, 10.8 m at block 19, zero at both ends â€” measured inside each
sheet so neither registration enters it. `tools/read_south_bank_swell_1834.py`
keeps Wright's ink vertex for vertex as the set-aside reading and its `--check`
re-derives the displacement from it on every commit, so the departure is gated
rather than asserted. **The waterline on this reach is `reconstructed`, not a
trace** (`docs/LIBERTIES.md` L275) â€” the only place in the scene where the ground's
edge is not the survey the datum, the plat and all 41 blocks are fitted to.

What it buys, measured: the bank's step across the La Salle mouth falls 9.62 â†’ 1.18 m,
and its p90 departure from a straight fit over E +300â€¦+456 â€” the stretch where the
plank walk curved round the point â€” falls 1.53 â†’ 0.65 m. The walk is one straight
run where it was two, four landings re-seat 4.6â€“10.8 m south, and 299 planting nodes
that would have stood in water are not planted.

**Two things are NOT taken, and both are refusals with numbers.** Block 18's 7.5 m,
because the bank there stands 5.4 m north of South Water Street's platted corridor
edge and 7.5 m would put the river 2.1 m into the roadway. And the west end stops at
the committed bend vertex rather than the foot of the turn, because west of E +222 the
traced bank already stands south of that edge and starting further west drowned another
32 m of roadway for no reading. The block grid is not re-cut; T-0419 stands.

`tools/check.sh`: 649 steps, the eight that went red on the moved ground re-derived and
green, nothing skipped for a missing module. Smoke verdicts are in the PR.

## Source and reconstruction loading cards â€” T-1275, 2026-09-26

The arrival draws from 160 authored entries: 20 source, 32 build, 50 fact,
56 operational and 2 humor cards. Phase counts: assess 30, collect 35,
prepare 42, resolve 25, land 28. Facts link specific compiled building attributes
to their registered sources without promoting confidence. The source compiler
exports decision/loading_fact backlinks. Land candidates remain authored context;
readiness selects one canonical arrival line and never rotates.

Twenty-four checked early entries precede the optional 41 KB library fetch.
Phase bags preserve spent IDs when the library arrives. Ready/error stop timers;
arrival is painted with 1835 by the existing settle controller. Successful
same-build visits in this tab limit repeat boots to one loading card plus arrival;
storage denial falls back to dwell-based rotation. The library describes previously
researched evidence, not live archival research. Seeded simulation records humor
in 52 of 10,000 sessions, at most once per session. Published Chromium checks passed at 390Ã—780 and 1280Ã—780: 37 and 6 cold
cards, exactly 2 on each repeat visit, no page errors, and the final card once
at 1835. All 160 cards fit two lines at 320 px without clipping.
Receipts and stills: `docs/performance/loading-content/`. The PR records the
full repository gate, smoke and payload results.
The one red this branch carried was never its own: a river-walk obstruction
reproduced on unmodified dev `b6c56c8` (mobile stage 2: 87 passed, 1 failed),
where the south-bank shed overlapped the walking path. T-1643 repaired that
placement and landed on dev on 2026-09-27, so the branch was merged onto it and
re-read rather than argued with. On the merge `604b8aa` the gate is `CHECK PASS`
at 657 steps and four published legs are green â€” mobile 1-2 (158/0, the part that
was red), mobile 3-4 (115/0, the source cards this compiler rewrites), mobile
11-12 (107/0, the release-notes reader) and desktop 1 (80/0). The baseline receipt
is preserved beside the loading evidence. No smoke assertion was weakened.

## Source-use backlinks compiled â€” T-1248, 2026-09-26

The deterministic compiler reads the authored reconstruction and records typed
source-to-claim edges, including newspaper issue locators. All 293 registered
sources remain represented, including 33 with no mapped use. The compact index
is 100,053 bytes; full public citations and edges are separate lazy files.
No visitor-facing surface or boot fetch is added. This unblocks T-1275 and T-1276
(visible-progress exemption 3). The generated [coverage report](measurements/source_use_coverage.md)
names the unsupported narrative/decision families; it does not claim exhaustive
parsing of research prose. Validation receipts are recorded in the PR.

## Arrival rolls the year back to summer 1835 â€” T-1247, 2026-09-26

The loading gate now presents a restrained split-flap year, driven by the measured
boot controller. It stays above 1835 until readiness, then lands with its arrival
message and entry button. Reduced motion is stepped; fast loads add no wait;
failed essential work stops and offers Retry. The neutral source card remains for
T-1275 to populate. No town data or geometry changes.

[Acceptance, captures, failure cases and reproduction](performance/ARRIVAL.md).
Full renderer smoke verdicts are recorded in the PR and smoke ledger; the controlled
fast fixture does not claim a sub-1.5-second full-town load on this software renderer.

## The ground off the plat is enumerated, and it holds 72 more â€” T-1614, 2026-09-26

The second piece of T-1199, and it answers the 1,374 households the first piece handed on.
`data/reconstruction/1835_off_plat_ledger.json` enumerates the ground the committed plat's
own lot ledger does not draw: 136 tier lots (the North Division tier under Kinzie, the
School Section tier between Madison and Monroe â€” both files written after the Thompson lot
grid was closed), 2 School Section blocks left whole, Kinzie's Addition's 27 blocks, the 7
placed chips of the 1834 survey colour key, and the 5 camp grounds. 177 parcels.

**It is carried at the granularity the records actually hold.** Kinzie's Addition is a
BLOCK and not a lot, because its own grid withholds the subdivision in as many words: no
lot rule has been read for that plat, and carrying the Original Town's four-to-a-face
module across the river would be a guess dressed as arithmetic. The camp grounds are a
NAME and not a polygon, because T-1214's file authors no vertex and this one may not author
one for it.

**The unflattering number is 72 of 1,374, and every one of the 72 is an adoption.** Not one
slot is raised, and that is the finding rather than an omission: 150 of the 177 parcels have
no row in the 665-roof programme's schedule at all â€” committed, surveyed, drawn ground the
building programme does not carry â€” and the 27 it does carry are Kinzie's Addition, marked
`unsubdivided` with no headroom. So a household with no standing roof free in its own
division has nowhere at all to be put, and 1,302 rows say which of the two gates stopped
them.

**The sharpest reading is the South Division: it has no free off-plat roof at all.** Every
South Division roof this project raised stands on a lot of the committed plat, and T-1613
dealt what was free of them. All 762 South Division rows handed on here are owed for a
shortage of roofs, not a shortage of clauses. The 204 farms-and-country-seats rows are the
other case â€” the D1 cabins their clause admits were taken by `labourer_dwellings`, which the
placement policy's own order ranks above it, and whose documented witness is Clybourn's
cabins and Robinson and Caldwell's, both well outside the plat.

**What this pass spends that its predecessor could not.** T-1613 scored a clause's
`class:`, `street:` and `lot:` preferences and said plainly that the policy vocabulary's
`ground:` terms "are about unplatted ground and are the successor ticket's". They are scored
now â€” `outside_plat`, `unplatted` and `wet`, each off a committed field. Two of the five,
`branch` and `river_frontage`, are NOT scored, because no committed off-plat parcel record
answers them; the ledger's `unscored_ground_terms` says so rather than guessing.

**What this does not do.** It writes no structure record, raises no roof and bakes nothing.
The People and Businesses views still do not read either seating file and the infill recipes
are still not regenerated from them â€” both are T-1615. So today 178 households have an
address that nothing in the walkthrough will show you.

Gated by `tools/seat_off_plat_ground_1835.py --check` and its seven-refusal `--self-test` in
`check.sh`; the invention is `docs/LIBERTIES.md` L271, counted by the register's own scope
gate.

## The scene-detail ladder is sealed, and every rung says what it protects â€” T-0135, 2026-09-26

**What a visitor sees:** nothing. No geometry, no reach, no cull and no ceiling value moves.
`full` still carries 1,460,000 triangles, `balanced` 1,280,000, `light` 825,000, and the
draw-call budget is still 215.

**What closes T-0135.** The ticket's first three items shipped on 2026-08-22 â€” the budget is
read at five named stands and gated on the WORST of them, each stand's reason is written where
the set is defined, and the run prints the spread. What kept the ticket open is the owner's
ruling of 2026-09-21, which asked for something the re-basing did not do:

> the whole ladder is re-derived from the measured worst stand, **monotonic by construction**,
> with each rung stating what it is FOR â€¦ and what measurement set it. A rung that cannot say
> what it protects is the next version of this ticket.

**The defect is real, and the loose version of it is wrong â€” so say the precise one.** `DETAIL`
in `renderers/web/js/main.js` was three independent literals with nothing between them. The
three have always descended at any one instant, theÛ]µçkh‘éì¶»§q«^uÌ‰äÁÕÑÑ¥¹œ½¹”É•½É‰…¬Ý¡•É”¥ÐÝ…Ìè¥Ð™…¥±Ì)Ý¥Ñ Ñ¡”É•½É¹…µ•…¹Ñ¡”‘•ÁÑ µ•…ÍÕÉ•¸((¨©Q¡”™½ÕÈÝ•É”½¹”É½ÜÌÍÁ…¥¹œ¸¨¨Q¡”Á…É•°Ì•¥¡Ð…¹¥±±…Éä‰Õ¥±‘¥¹Ì¡…±½…°Ù…±Õ•Ì½˜(ÌÄÐ°€ÐÌà°€ÔØÀ°€ØàÜ°€àÄÀ…¹€ÌÄÔ°€ÔÔä°€àÀäƒŠP„€¨¨ÄÈÌ´Á¥Ñ °Ý¡¥ ¥ÌÑ¡”‰±½¬Á¥Ñ ¨¨ƒŠPÍ¼½¹”)å…É‰Õ¥±‘¥¹œÍÑ½½…ÐÑ¡”•…ÍÑ•É¸•‘”½˜•Ù•Éä‰±½¬°„‰Õ¥±‘¥¹œÌÝ¥‘Ñ ™É½´Ñ¡”¹•áÐÍÑÉ••Ð°)•¥¡ÐÑ¥µ•Ì½Ù•È¸Q¡”•¹•É…Ñ½ÈÑ¡…ÐÝÉ½Ñ”Ñ¡•´Ñ•ÍÑ•¹½Ñ¡¥¹œè¹½Ð½Ù•É±…À°¹½ÐÝ…Ñ•È°¹½Ð)É½Õ¹°¹½ÐÑ¡”ÍÑÉ••Ð¸((¨©!…±˜½˜Ñ¡•´Á…ÍÍ•°…¹Ý¡äÑ¡•äÁ…ÍÍ•¥ÌÑ¡”Á…ÉÐÝ½ÉÑ ­••Á¥¹œ¸¨¨Q¡”™½ÕÈÑ¡…Ð¥¹ÑÉÕ‘•(£Š"HÄ¸ÀÌÑ¼ƒŠ"HÐ¸ÌÈ´¥¹Í¥‘”Ñ¡”É½…‘Ý…ä¤…É”Ñ¡”™½ÕÈ±…É•ÍÐ…¹¥±±…Éä™½½ÑÁÉ¥¹ÑÌ¥¸Ñ¡”Á…É•°ìÑ¡”)™½ÕÈÑ¡…Ð±•…É•¥Ð…É”Ñ¡É•”ÁÉ¥Ù¥•Ì…¹„Íµ…±°Í¡•°±•…È‰ä€¨¨Ä¸ÓŠLÈ¸Ä´……¥¹ÍÐÑ¡¥Ì)‘…Ñ…Í•ÐÌ½Ý¸ƒ
ÄÈÀ´•½É•™•É•¹”¨¨¸Q¡•äÝ•É”¹½ÐÁ±…•±•…È½˜Ñ¡”ÍÑÉ••Ð°Ñ¡•äÝ•É”Ñ½¼Íµ…±°)Ñ¼É•… ¥ÐƒŠPÍ¼„™¥à…¥µ•½¹±ä…ÐÑ¡”™½ÕÈ™…¥±ÕÉ•ÌÝ½Õ±¡…Ù”½ÉÉ•Ñ•™½ÕÈ¹Õµ‰•ÉÌ…¹±•™Ð)Ñ¡”ÉÕ±”Ñ¡…ÐÁÉ½‘Õ•Ñ¡•´¸±°•¥¡Ðµ½Ù•¥¹ÍÑ•…°‰ä½¹”…ÉÕµ•¹Ðè•… ¹½ÜÍÑ…¹‘Ì‘¥É•Ñ±ä)‰•¡¥¹Ñ¡”•…ÍÑ•É¹µ½ÍÐÁÉ¥¹¥Á…°É½½˜½˜¥ÑÌ½Ý¸‰±½¬°€ÈÐ´‰…¬™½ÈÑ¡”É•…Èå…É‘Ì…¹€ÈÄ´™½È)Ñ¡”Í•ÉÙ¥”å…É‘Ì°‰•…ÕÍ”„É•…Èå…É‰•±½¹ÌÑ¼„±½Ð…¹„±½Ð‰•±½¹ÌÑ¼„¡½ÕÍ”¸€ÄßŠLÌÈ´½˜)µ½Ù•µ•¹Ð¸((¨©9½Ñ¡¥¹œÝ…ÌÉ•É…‘•…¹¹½Ñ¡¥¹œÝ…Ì…‘½ÁÑ•¸¨¨Q¡•Í”Á½Í¥Ñ¥½¹ÌÝ•É”½¹©•ÑÕÉ…±€‰•™½É”…¹)…É”½¹©•ÑÕÉ…±€…™Ñ•Èì±•…É¥¹œÑ¡”É½…‘Ý…ä¥Ì¹½ÐÍÑ…¹‘¥¹œ½¸„É•½Ù•É•±½Ð°…¹ÍÑ…¹‘¥¹œ)‰•¡¥¹…¸…¹½¹åµ½ÕÌÉ½½˜¥Ì¹½Ð•Ù¥‘•¹”½˜Í•ÉÙ¥¹œ¥Ð¸Q¡”¡½ÕÍ•¡½±±•‘•È­•åÌ½¸ÍÑÉÕÑÕÉ”¥)É…Ñ¡•ÈÑ¡…¸½¸Á½Í¥Ñ¥½¸°Í¼Ñ¡”€àÌ…‘½ÁÑ•É½½™Ì­•ÁÐÑ¡•¥È¡½ÕÍ•¡½±‘Ì…É½ÍÌÑ¡”µ½Ù”ƒŠPÝ¡¥ ¥Ì)Ý¡…Ðµ…‘”Ñ¡”½ÕÁ±¥¹œÑ¡”ÁÉ•Ù¥½ÕÌÍ±¥”¥Ñ•„É”µ‘•É¥Ù…Ñ¥½¸É…Ñ¡•ÈÑ¡…¸„É”µ…ÉÕµ•¹Ð¸Q¡”)9½ÉÑ Á…É•°…ÉÉ¥•ÌÑ¡”Í…µ”…Ñ”…¹¥Ð‰¥¹‘Ì¹½Ñ¡¥¹œÑ½‘…äèÑ¡”É¥½Ù•ÉÌ¹¼9½ÉÑ ¥Ù¥Í¥½¸)‰±½¬°‰•…ÕÍ”Ñ¡…ÐÍÑÉ••Ð½¹ÑÉ½°¥ÌÝ¡…Ðƒ
œLäÍÑ¥±°É•½É‘Ì…Ì½Ý•¸•Ñ…¥°è)‘½Ì½IMI ½Ñ¡½µÁÍ½¹}Á±…Ñ}É¥¹µ‘€ƒ
œ€Ýˆ¸((ŒŒ9•Ü€ÈÀÈØ´Àà´ÄÌƒŠP½¹”Ý…äÑ¼¼Í½µ•Ý¡•É”°É…‘•ì…¹Ñ¡”¡…±˜½˜Ñ¡”…Ñ”Ñ¡…ÐÝ…Ì¹½ÐÉÕ¹¹¥¹œ((¨©,ä¸¨¨Y¥•ÝÁ½¥¹ÑÌ…¹Ñ¡”Á±…”Í•…É Ý•É”ÑÝ¼±¥ÍÑÌ½˜Ñ¡”Í…µ”É½Õ¹¥¹Í¥‘”M•ÑÑ¥¹Ì¸)Q¡•ä…É”¹½Ü½¹”¼Ñ½€Ñ…ˆ°Í•½¹¥¸Ñ¡”ÍÑÉ¥À…™Ñ•È½¹ÑÉ½±Ì°½Á•¹•‰ä€ñ­‰ùð½­‰øè€à)…ÕÑ¡½É•Ù¥•ÝÁ½¥¹ÑÌ°€ÐÙ•É¥™¥•©Õ¹Ñ¥½¹Ì°€ÈÈÈÍÑÉÕÑÕÉ•Ì°‰Õ¥±Ð™É½´Ñ¡”Í•¹”°Ñ¡”¥¹‘•à…¹)Ñ¡”É•¥ÍÑÉäÉ…Ñ¡•ÈÑ¡…¸™É½´„µ•¹ÔÍ½µ•‰½‘äµ…¥¹Ñ…¥¹Ì¸€‰Ñ¸µ¡•±Á€¥Ì„¡…µ‰ÕÉ•È¸((¨©Q¡”Á…É•°…Í­•™½È‘½Õµ•¹Ñ••¹ÑÉ¥•Ì½¹±ä°…¹Ñ¡…ÐÑÕÉ¹•½ÕÐÑ¼‰”Ñ¡”ÝÉ½¹œ±¥ÍÐ¸¨¨)9¼ÍÑÉÕÑÕÉ”Á½Í¥Ñ¥½¸¥¸Ñ¡¥Ì‘…Ñ…Í•Ð¥ÌÉ…‘•‘½Õµ•¹Ñ•‘€ƒŠP€¨¨ÔÐ…É”¥¹™•ÉÉ•‘€…¹€ÄØà)½¹©•ÑÕÉ…±€¨¨ƒŠPÍ¼‘½Õµ•¹Ñ•µ½¹±äÝ½Õ±¡…Ù”Í¡¥ÁÁ•™½ÕÈ©Õ¹Ñ¥½¹Ì¸Ù•ÉäÍÑÉÕÑÕÉ”É•ÍÕ±Ð)¥¹ÍÑ•……ÉÉ¥•Ì¥ÑÌ½Ý¸Á±…•µ•¹Ð¹Á½Í¥Ñ¥½¹}½¹™¥‘•¹•€°¥¸Ñ¡”Í…µ”Ñ¡É•”Ý½É‘Ì…¹Ñ¡É•”)½±½ÕÉÌÑ¡”‰Õ¥±‘¥¹œ…ÉÕÍ•Ì°…¹Ñ¡”Ñ…ˆÌÍÕµµ…Éä±¥¹”½Õ¹ÑÌÑ¡”É…‘•Ì™É½´Ñ¡”±¥ÍÐ¥Ð)Á…¥¹ÑÌ¸]¡…ÐÍÕÉÙ¥Ù•Ì…‰½ÕÐ„‰Õ¥±‘¥¹œ¥ÌÕÍÕ…±±ä„ÍÑÉ••Ð…¹„Í¥‘”½˜¥Ð°Í¼„Ý•±°µ‘½Õµ•¹Ñ•)Ñ…Ù•É¸Ý¥Ñ „½¹©•ÑÕÉ…°Á½Í¥Ñ¥½¸¥ÌÑ¡”¹½Éµ…°…Í”¡•É”É…Ñ¡•ÈÑ¡…¸„™…¥±ÕÉ”ƒŠP…¹Ñ¡”µ•¹Ô)¹½ÜÍ…åÌÝ¡¥ ¥ÌÝ¡¥ …ÐÑ¡”µ½µ•¹ÐÑ¡”Ù¥Í¥Ñ½È¡½½Í•ÌÝ¡•É”Ñ¼¼¸Q¡”…Ñ”½µÁ…É•Ì•Ù•Éä)¡¥À……¥¹ÍÐÑ¡”É•½É¥Ð©ÕµÁÌÑ¼ì„µ•¹ÔÑ¡…ÐÉ…‘•„Á½Í¥Ñ¥½¸µ½É”­¥¹‘±äÑ¡…¸Ñ¡”É•½É)‘½•ÌÝ½Õ±‰”Ñ¡¥ÌÁÉ½©•ÐÌÝ½ÉÍÐ­¥¹½˜‰Õœ¸((¨©QÝ¼‘•™•ÑÌÑ¡”¹•Ü…ÍÍ•ÉÑ¥½¹Ì…Õ¡Ð¥¸Ñ¡•¥È½Ý¸Í±¥”¸¨¨Q¡”™¥Ù”µÑ…ˆÍÑÉ¥À™¥ÑÑ•€ÌØÀÁà)½¹±ä‰ä™±•àµÍ¡É¥¹­¥¹œ±…‰•±Ì½ÕÐÁ…ÍÐÑ¡•¥È½Ý¸‰ÕÑÑ½¹ÌƒŠP½¹”Ñ¥‘äÉ½Ü°µ•…ÍÕÉ•°…¹„µ•ÍÌÑ¼)±½½¬…ÐìÑ¡”‘•Í­Ñ½ÀÁ…¹•°¥Ì€ÌàÀÁà¹½Ü°Ñ…ˆÁ…‘‘¥¹œ¥Ì€ØÁà…¹µ½‰¥±”ÑåÁ”€ÄÄ¸ÔÁà°±•…Ù¥¹œ)…‰½ÕÐ€ÈÀÁà½˜Í±…¬…Ð‰½Ñ Ù¥•ÝÁ½ÉÑÌ°…¹Ñ¡”…Ñ”µ•…ÍÕÉ•ÌÉ½ÝÌ°½Ù•É™±½Ü…¹ÍÅÕ••é”…Ð‰½Ñ ¸)Í¥áÑ Ñ…ˆ‘½•Ì¹½Ð™¥Ð…¹Ý¥±°™…¥°Ñ¡•É”¸Q¡”½¹™¥‘•¹”¡¥ÁÌ…±Í¼É•¹‘•É•¥‘•¹Ñ¥…±±ä)É•ä°‰•…ÕÍ”„Á±…¥¸€¹©ÕµÀµÉ•ÍÕ±ÐÍµ…±±€ÉÕ±”½ÕÑÉ…¹­Ì€¹½¹˜µ¥¹™•ÉÉ•‘€½¸ÍÁ•¥™¥¥ÑäìÑ¡”)…Ñ”¹½ÜÉ•ÅÕ¥É•ÌÑ¡”É…‘•ÌÑ¼‘¥™™•È‰ä½±½ÕÈ…ÌÝ•±°…Ì‰äÝ½É¸((¨©Q¡”‘•Í­Ñ½À¡…±˜½˜Ñ½½±Ì½Íµ½­•}É•¹‘•É•È¹µ©Í€¡…¹½Ð‰••¸ÉÕ¹¹¥¹œ°…¹¥Ð¥Ì¹½Ð±•…È™½È)¡½Ü±½¹œ¸¨¨%Ð…‰½ÉÑ••Ù•ÉäÉÕ¸…ÐÑ¡”™¥ÉÍÐ±¥¬½¸Ñ¡”µ•¹Ô‰ÕÑÑ½¸ƒŠP½¸µ…¥¹€…ÌÝ•±°…Ì½¸)Ñ¡¥Ì‰É…¹ °É•ÁÉ½‘Õ¥‰±äƒŠP…¹•Ù•Éä‘•Í­Ñ½À…ÍÍ•ÉÑ¥½¸…™Ñ•ÈÑ¡…ÐÁ½¥¹Ð°É½Õ¡±ä„Ñ¡¥É½˜Ñ¡”)ÍÕ¥Ñ”°Í¥µÁ±ä¹•Ù•È•á•ÕÑ•Ý¡¥±”Ñ¡”ÉÕ¸É•Á½ÉÑ•„™…¥±ÕÉ”Ñ¡…ÐÉ•…±¥­”„‰É½­•¸½¹ÑÉ½°¸)9½Ñ¡¥¹œÝ…Ì½Ù•É¥¹œÑ¡”‰ÕÑÑ½¸è•±•µ•¹ÑÉ½µA½¥¹Ñ€É•ÑÕÉ¹•Ñ¡”‰ÕÑÑ½¸¥ÑÍ•±˜…Ð¥ÑÌ½Ý¸•¹ÑÉ”°)Ý¥Ñ ¹¼Á½¥¹Ñ•È±½¬°Ñ¡”Á…”Ù¥Í¥‰±”…¹™½ÕÍ•¸Q¡”…ÕÍ”¥ÌÑ¡”Í•¹”Ì½Ý¸Ý•¥¡Ð¸Ð(ÔÌÌ€ÀÀÀÑÉ¥…¹±•Ì½¸„Í½™ÑÝ…É”É•¹‘•É•È½¹”…¹¥µ…Ñ¥½¸™É…µ”Ñ…­•Ì€¨¨À¸ÐÛŠLÄ¸ÄÀÌ€¡µ•…ÍÕÉ•¤¨¨°)…¹A±…åÝÉ¥¡ÐÌ±¥¬Ý…¥ÑÌ™½ÈÑ¡”•±•µ•¹ÐÑ¼¡½±ÍÑ¥±°…É½ÍÌ™É…µ•Ì‰•™½É”¥ÐÝ¥±°¡¥ÐµÑ•ÍÐ)¥Ð°Í¼€ÌÀÌ½˜‘•™…Õ±Ð…Ñ¥½¸‰Õ‘•ÐÝ…Ì‰•¥¹œÍÁ•¹Ð½¸™É…µ•ÌÉ…Ñ¡•ÈÑ¡…¸½¸Ñ¡”Á…”¸Q¡”)‰Õ‘•Ð¥Ì¹½Ü€äÀÌƒŠPÉ½½´™½È„Í±½Üµ…¡¥¹”°¹½ÐÁ•Éµ¥ÍÍ¥½¸™½È„‰É½­•¸½¹ÑÉ½°°Í¥¹”„±¥¬)Ñ¡…Ð¹•Ù•È±…¹‘ÌÍÑ¥±°™…¥±Ì¸€¨©Q¡¥Ì¥Ì„ÍÑ…¹‘¥¹œ¡…é…É°¹½Ð„™¥á•½¹”¨¨èÑ¡”Í…µ”ÍÑ…ÉÙ…Ñ¥½¸)Ý¥±°É•ÑÕÉ¸…ÌÑ¡”Ñ½Ý¸É½ÝÌ€¡I=5@,ÄÐ…±É•…‘äÉ•½É‘Ì€Ø€”½˜ÑÉ¥…¹±”¡•…‘É½½´¤°…¹Ñ¡”)¹•áÐÍåµÁÑ½´Ý¥±°……¥¸±½½¬±¥­”„U$‰ÕœÉ…Ñ¡•ÈÑ¡…¸„‰Õ‘•Ð¸™Õ±°ÑÝ¼µÙ¥•ÝÁ½ÉÐÁ…ÍÌ¹½Ü)Ñ…­•ÌÕÁÝ…É‘Ì½˜Ñ•¸µ¥¹ÕÑ•Ì¡•É”ìM5=-}Y%]A=IPõµ½‰¥±•ñ‘•Í­Ñ½Á€ÉÕ¹Ì½¹”¡…±˜Ý¡¥±”)¥Ñ•É…Ñ¥¹œ…¹ÁÉ¥¹ÑÌÑ¡…Ð¥Ð¥Ì¹½ÐÑ¡”…Ñ”¸((ŒŒ9•Ü€ÈÀÈØ´Àà´ÄÌƒŠP„¹Õµ‰•ÈÑ¡…ÐÝ…ÌÝÉ¥ÑÑ•¸°Ù…±¥‘…Ñ•°Í¡¥ÁÁ•…¹¹•Ù•ÈÉ•…((¨©,Ì°½Ù•É…”¸¨¨Ù•Éä™±½É„é½¹”É•½É…ÕÑ¡½ÉÌ½Ù•È¹µ…ÑÉ¥á}™É…Ñ¥½¹€ƒŠP¡½ÜµÕ ½˜Ñ¡”)É½Õ¹Ñ¡…Ð½µµÕ¹¥ÑäÌµ…ÑÉ¥à½Ù•ÉÌƒŠPÝ¥Ñ „‰…É•}Í½¥±}™É…Ñ¥½¹€‰•Í¥‘”¥Ð¸Ñ½½±Ì½Ù…±¥‘…Ñ”¹Áå€)¡…Ì…Ñ•‰½Ñ Í¥¹”Ñ¡”É•½É‘ÌÝ•É”ÝÉ¥ÑÑ•¸°…¹¥¹‘•à¹©Í½¹€‘•¹½Éµ…±¥Í•ÌÑ¡”‰…É”µÍ½¥°™¥ÕÉ”)ÍÁ•¥™¥…±±äÍ¼Ñ¡”É½Õ¹Í¡…‘•È…¸™•Ñ ¥Ð½¹”¸€¨©É•¹‘•É•ÉÌ½Ý•ˆ½©Ì½™±½É„¹©Í€¡…¹•Ù•È…Í­•)™½È•¥Ñ¡•È¸¨¨±°Ñ•¸½µµÕ¹¥Ñ¥•ÌÝ•É”Á±…¹Ñ•…ÐÑ¡”Í¥¹±”±…ÑÑ¥”‘•¹Í¥Ñä0ÌÈÑÕ¹•½¸±½Í•)Ý•ÐÁÉ…¥É¥”°Í¼„Í•ÑÑ±•Ñ½Ý¸Ý¡½Í”½Ý¸É•½ÉÍ…åÌ€¨¨ÐÔ€”½˜¥ÑÌÉ½Õ¹¥Ì‰…É”¨¨Ý…Ì‘É…Ý¸Ý¥Ñ )Ñ¡”É½Õ¹±½Í•°…¹Í¼Ý•É”Ñ¡”Í¡…‘•É¥Ù•É‰…¹¬Õ¹‘•ÉÍÑ½Éä€ À¸ÐÔ¤°Ñ¡”™½É•ÍÐ™±½½È€ À¸ÌÔ¤…¹)Ñ¡”±…­•Í¡½É”Í…¹€ À¸ÌÔ¤¸()Q¡”™É…Ñ¥½¸¥Ì¹½ÜÑ¡”ÁÉ½‰…‰¥±¥ÑäÑ¡…Ð„µ…ÑÉ¥à±…ÑÑ¥”Í±½Ð…ÉÉ¥•Ì„Á±…¹ÐƒŠP¹•…ÈÑÕ™ÑÌ…¹)µ¥…É‘Ì…±¥­”°‰•…ÕÍ”Ñ¡¥¹¹¥¹œ½¹”…¹¹½ÐÑ¡”½Ñ¡•ÈÝ½Õ±ÁÕÐ„Í•…´•á…Ñ±ä…ÐÑ¡”É½ÍÍ½Ù•È)Ý¡•É”Ñ¡”¡…¹”½˜É•ÁÉ•Í•¹Ñ…Ñ¥½¸¥Ìµ•…¹ÐÑ¼‰”¥¹Ù¥Í¥‰±”¸%Ð¥ÌÑ¡”Í…µ”ÉÕ±”Ñ¡”™½Éˆ±…å•È)¡…Ì…±Ý…åÌ…ÁÁ±¥•Ñ¼¥ÑÌ½Ý¸É•½É‘•‘•¹Í¥Ñ¥•Ì°½¸Ñ¡”™¥•±Ñ¡”µ…ÑÉ¥à±…å•È¥¹½É•¸((´€¨©]•ÐÁÉ…¥É¥”¥ÌÕ¹Ñ½Õ¡•¨¨°‰•…ÕÍ”¥ÐÉ•½É‘Ì€Ä¸ÀÀ…¹€Ä¸ÀÀ¥ÌÑ¡”…¹¡½È¸9½Ñ¡¥¹œÑ¡”(€Ñ¡É•”µÉ¥Ñ¥ŒÁÉ…¥É¥”ÍÝ••ÀÑÕ¹•¡…Ìµ½Ù•°…¹Ñ¡”¡…¹”…¸½¹±ä•Ù•È€©É•µ½Ù”¨¥¹ÍÑ…¹•Ì¸(€5•…ÍÕÉ•…Ð€ÄÈàÃ\àÀÀ……¥¹ÍÐµ…¥¹€…ÐÑ¡É•”™¥á•ÍÑ…Ñ¥½¹ÌèÝ•ÐÁÉ…¥É¥”€¨¨ÌØÀ€äÜäÑÉ¥Ì……¥¹ÍÐ(€€ÌØÀ€àØÌ¨¨€ ¬À¸ÀÌ€”°Ý¡¥ ¥ÌÑ¡”É•Í¡Õ™™±•É…¹‘½´‘É…Ü°¹½Ð¹•Ü•½µ•ÑÉä¤°Í•ÑÑ±•Ñ½Ý¸(€€¨¨ÐÈä€ÈàÄ……¥¹ÍÐ€ÐÐÄ€ØàÌ¨¨€£Š"HÈ¸à€”°€Ì€ÈÜà™±½É„¥¹ÍÑ…¹•Ì……¥¹ÍÐ€Ì€àÐÈ¤°µ…ÉÍ •‘”(€€¨¨Èää€ÄØÄ……¥¹ÍÐ€ÌÀà€ÈÌÔ¨¨€£Š"HÈ¸ä€”¤¸Q¡”Í•¹”•ÑÌ±¥¡Ñ•È•á…Ñ±äÝ¡•É”„É•½ÉÍ…åÌÑ¡”(€É½Õ¹¥Ì‰…É”¸(´€¨©5•…ÍÕÉ•°…É½ÍÌÑ¡”•¥¡Ð½µµÕ¹¥Ñ¥•ÌÑ¡…Ð¡…Ù”„±•…¸Í…µÁ±¥¹œÍÑ…Ñ¥½¸¨¨èÁ±…¹Ñ•‘•¹Í¥Ñä(€¹½ÜÍÁ…¹Ì€¨¨È¸ÈÇŠLØ¸äÀÑÕ™ÑÌÁ•È·
È¨¨Ý¡•É”¥ÐÝ…Ì½¹”™¥ÕÉ”•Ù•ÉåÝ¡•É”°…¹Ñ¡”¥µÁ±¥•(€™Õ±°µ½Ù•È‘•¹Í¥Ñä…É••Ì…Ð€¨¨Ø¸ÌÇŠLà¸ÄÔ¨¨……¥¹ÍÐ„±…ÑÑ¥”…ÉÉå¥¹œ€Ü¸ÌÀ¸(´€¨©Q¡”…Ñ”…Í­Ì‰½Ñ ¡…±Ù•Ì¨¨°‰•…ÕÍ”…¹ÍÝ•É¥¹œ½¹±äÑ¡”™¥ÉÍÐ¥Ì¡½ÜÑ¡¥ÌÝ•¹ÐÕ¹¹½Ñ¥•è(€Ñ¡…Ð•… ½µµÕ¹¥ÑäÌ…ÕÑ¡½É•¹Õµ‰•ÈÉ•…¡•ÌÑ¡”É•¹‘•É•È€¡É”µ™•Ñ¡•™É½´Ñ¡”É•½É‘Ì°¹½Ð(€½µÁ…É•……¥¹ÍÐ„½Áä½˜Ñ¡”É•¹‘•É•È¤°…¹Ñ¡…ÐÑ¡”ÍÝ…É½¸Ñ¡”É½Õ¹™½±±½ÝÌ¥Ð¸Q¡”(€Í•½¹…ÍÍ•ÉÑ¥½¸™…¥±Ì¥¸Ñ¡”½Ñ¡•È‘¥É•Ñ¥½¸Ñ½¼ƒŠP¥˜•Ù•Éä½µµÕ¹¥ÑäÝ•¹Ð‰…¬Ñ¼½¹”(€‘•¹Í¥Ñä°Ñ¡”Á•Èµ·
ÈÍÁÉ•…Ý½Õ±½±±…ÁÍ”Ñ½Ý…É€Ä…¹Ñ¡”¥µÁ±¥•™¥ÕÉ•ÌÝ½Õ±™…¸½ÕÐ(€…É½ÍÌÑ¡”€À¸Ì×ŠLÄ¸ÀÀÑ¡”É•½É‘Ì¥Ù”¸(´€¨©=¹”…¹Ñ¤µÙ…Õ¥ÑäÕ…Éµ½Ù•…¹Ñ¡”Ñ½±•É…¹”‘¥¹½Ð¸¨¨€¨‰‘•Ñ…¥±•™±½É„É½½ÑÌÍ¡…É”Ñ¡”(€Ñ•ÉÉ…¥¸…¹Ý…Ñ•ÈÍÕÉ™…•Ìˆ¨É•ÅÕ¥É•Ì„µ¥¹¥µÕ´Í…µÁ±”Í¼Ñ¡…ÐÁ±…¹Ñ¥¹œ¹½Ñ¡¥¹œ…¹¹½ÐÉ•Á½ÉÐ„(€Á•É™•ÐÝ½ÉÍÐ•ÉÉ½Èì¥ÑÌÍÑ…Ñ¥½¸ÍÑ…¹‘Ì¥¸Ñ¡”Í•ÑÑ±•Ñ½Ý¸°…¹Ñ¡”µ½‰¥±”½¹”Ñ¡•É”¹½Ü¡½±‘Ì(€€ØÜÉ½½Ñ•Á±…¹ÑÌ……¥¹ÍÐ…‰½ÕÐ€ÄÔÀ‰•™½É”¸Q¡”Õ…É¥Ì€ÔÀìÑ¡”€Å”´Ô´É½½ÐÑ½±•É…¹”¥Ì(€Õ¹Ñ½Õ¡•¸Q¡…Ð¹Õµ‰•È¥Ì„ÁÉ½Á•ÉÑä½˜Ñ¡”‘…Ñ…Í•Ð¹½ÜÉ…Ñ¡•ÈÑ¡…¸½˜Ñ¡”É•¹‘•É•È¸((¨©QÝ¼™¥¹‘¥¹Ìµ•…ÍÕÉ•½¸Ñ¡”Ý…ä°…¹¹½Ð™¥á•Ñ¡•¸¸	½Ñ ™¥á•€ÈÀÈØ´Àà´ÄÌƒŠPÍ•”‰•±½Ü¸¨¨LÙ„)¥Ñ•´€äÉ•…‘ÌÑ¡”É¥Ù•É}‰…¹­€Í¡½Ð……¥¹ÍÐé½¹”€ÄÌ½É‘É…ÍÌƒŠP‰ÕÐÉ½Õ¹Ý¥Ñ¡¥¸•¥¡Ðµ•ÑÉ•Ì½˜)Ý…Ñ•È¥ÌÑ¡”5IM é½¹”‰ä•áÑ•¹Ð°…¹Ñ¡”Í¡½ÐÌÍÝ…É¥Ì•¹Ñ¥É•±äèÀÑ€½èÄÁ€Ý¥Ñ ¹¼èÀÅ€¥¸)¥Ð…Ð…±°¸¹Ñ¡”€‰øÈÔ´ÍÁÉ¥Ìˆ…É”‰•ÑÑ•È•áÁ±…¥¹•‰äÍÁ•¥•ÌÑ¡…¸‰ä‘•¹Í¥Ñäè)¹ÕÁ¡…É}…‘Ù•¹…€…¹¹åµÁ¡…•…}½‘½É…Ñ…€…É”™±½…Ñ¥¹œµ±•…Ù•…ÅÕ…Ñ¥ÌÉ•½É‘•…Ð€À¸ÀÇŠLÀ¸ÄÀ´Ý¡½Í”)½Ý¸…ÁÁ•…É…¹•€Ñ•áÐÍ…åÌÑ¡•ä™±½…Ð¥¸½Á•¸Ý…Ñ•È°…¹Ñ¡•äÝ•É”€¨¨Ø¸Ô€”½˜Ñ¡”ÑÕ™ÑÌÍÑ…¹‘¥¹œ)½¸Ñ¡…Ð‘Éä‰…¹¬¨¨°‰•…ÕÍ”É½±”è•µ•É•¹Ñ€Ý…Ì…±°Ñ¡”É•¹‘•É•È½Õ±Í•”¸¥á¥¹œÑ¡…Ð¥Ì„‘…Ñ„)™¥•±¥¸Ñ¡”ÁÕ‰±¥Í¡•Ù½…‰Õ±…Éä‰•™½É”¥Ð¥Ì„±¥¹”¥¸Ñ¡”É•¹‘•É•ÈƒŠP„É•¹‘•É•ÈÑ¡…Ð‘•¥‘•)Ý¡¥ Á±…¹ÑÌ™±½…Ð‰äÉ•…‘¥¹œÑ¡•¥È¡•¥¡ÑÌÝ½Õ±‰”Õ•ÍÍ¥¹œ…Ð•á…Ñ±äÑ¡”Á½¥¹ÐÑ¡¥ÌÁÉ½©•Ð)É•™ÕÍ•ÌÑ¼¸((ŒŒ9•Ü€ÈÀÈØ´Àà´ÄÌƒŠPÑ¡”Á…‘ÌÝ•É”ÍÑ…¹‘¥¹œ½¸Í½¥°°…¹ÁÉ½Í”Ý…ÌÑ¡”½¹±äÑ¡¥¹œÑ¡…ÐÍ…¥Í¼((¨©,Ì°Ñ¡”Í•½¹™¥¹‘¥¹œ¸¨¨Ý…Ñ•È±¥±ä…¹„…ÑÑ…¥°Ý•É”Ñ¡”Í…µ”É•½ÉÑ¼Ñ¡”Á±…•Èè‰½Ñ )É½±”è•µ•É•¹Ñ€°…¹Ñ¡”É½±”¥ÌÝ¡…ÐÍÑ…Ñ¥½¸ ¥€É•…¸M¼Ñ¡”µ…ÉÍ ½µµÕ¹¥ÑäÝ…ÌÁ±…¹Ñ•)¥‘•¹Ñ¥…±±ä½¸‰½Ñ Í¥‘•Ì½˜¥ÑÌ½Ý¸Ý…Ñ•É±¥¹”°…¹¹ÕÁ¡…É}…‘Ù•¹…€…¹¹åµÁ¡…•…}½‘½É…Ñ…€ƒŠP(À¸ÀÇŠLÀ¸ÄÀ´°™½É´èµ…Ñ}ÁÉ½ÍÑÉ…Ñ•€°…ÁÁ•…É…¹•€€‰™±½…Ñ¥¹œÁ…‘Ì¥¸½Á•¸Ý…Ñ•ÈˆƒŠPÍÑ½½…Ì…¹­±”´)¡¥ µ…ÑÌÉ½½Ñ•¥¸Ñ¡”Í½¥°½˜Ñ¡”‘Éä‰…¹¬¸€¨©Q¡”•Ù¥‘•¹”Ý…Ì¥¸Ñ¡”É•½É…¹Õ¹É•…‘…‰±”‰ä)…¹åÑ¡¥¹œ‰ÕÐ„Á•ÉÍ½¸¸¨¨()‘…Ñ„½™±½É„½¥¹‘•à¹©Í½¹€¹½ÜÁÕ‰±¥Í¡•Ì„ÍÕ‰ÍÑÉ…Ñ•Í€Ù½…‰Õ±…Éä…¹•Ù•ÉäÉ½±”è•µ•É•¹Ñ€É•½É)ÍÑ…Ñ•Ì½¹”è()ðÙ…±Õ”ð¡…‰¥Ððµ…ä‰”Á±…¹Ñ•ð)ð´´µð´´µð´´µð)ðÍ½¥±€ðÉ½½Ñ•É½Õ¹…‰½Ù”Ñ¡”Ý…Ñ•ÈìÑ¡”‘•™…Õ±ÐÝ¡•¸Ñ¡”™¥•±¥Ì…‰Í•¹Ðð‘ÉäÉ½Õ¹½¹±äð)ðÍ…ÑÕÉ…Ñ•‘}Í½¥±€ðÑ¡”•µ•É•¹Ð¡…‰¥ÐƒŠPÝ•ÐÉ½Õ¹=HÍÑ…¹‘¥¹œÝ…Ñ•È°™½±¥…”…‰½Ù”Ñ¡”ÍÕÉ™…”ð‰½Ñ Í¥‘•Ìð)ð½Á•¹}Ý…Ñ•É€ðÉ½½Ñ•‰•±½ÜÑ¡”ÍÕÉ™…”°±•…Ù•Ì™±½…Ñ¥¹œ=8¥Ðð½Ù•ÈÝ…Ñ•È½¹±äð((´€¨©Q¡”Ù…±¥‘…Ñ½ÈÉ•™ÕÍ•ÌÑ¡”Õ¹Á±…¹Ñ…‰±”É•½É¨¨°¹½Ð©ÕÍÐÑ¡”Õ¹­¹½Ý¸Ý½Éè…¸½Á•¹}Ý…Ñ•É€(€ÍÁ•¥•Ì¥¸„é½¹”Ý¡½Í”•áÑ•¹Ð¹•Ù•ÈÉ•…¡•ÌÝ…Ñ•ÈƒŠP½È„‰Õ™™•ÈÑ¡…ÐÍÑ…ÉÑÌ…ÐÑ¡”‰…¹¬É…Ñ¡•È(€Ñ¡…¸…ÐÑ¡”Ý…Ñ•É±¥¹”ƒŠP¥Ì…¸•ÉÉ½È°‰•…ÕÍ”„É•½ÉÑ¡…Ð…¸¹•Ù•È‰”‘É…Ý¸¥Ì„±…¥´Ñ¡”(€Ý…±­Ñ¡É½Õ ‘½•Ì¹½Ðµ…­”¸M¥à¹•ÜÍ•±˜µÑ•ÍÑÌ¥¸Ñ½½±Ì½Ñ•ÍÑ}Ù…±¥‘…Ñ”¹Áå€¸(´€¨©Q¡”½µµÕ¹¥Ñä¥ÌÍÁ±¥Ð°¹½ÐÑ¡”Í±½Ð‘É½ÁÁ•¸¨¨™±½É„¹©Í€Á¥­Ì™É½´Ñ¡”ÍÕ‰Í•Ð±•…°½¸Ñ¡”(€Í¥‘”½˜Ñ¡”Ý…Ñ•É±¥¹”¥Ð¥ÌÁ±…¹Ñ¥¹œ°Ý¥Ñ Ñ¡”Ý•¥¡ÑÌÉ•¹½Éµ…±¥Í•½Ù•ÈÑ¡…ÐÍÕ‰Í•Ð¸I•™ÕÍ¥¹œ(€Ñ¡”Í±½Ð…™Ñ•ÈÑ¡”Á¥¬Ý½Õ±¡…Ù”‰••¸½¹”±¥¹”Í¡½ÉÑ•È…¹Ý½Õ±¡…Ù”Ñ¡¥¹¹•Ñ¡”‘Éäµ…ÉÍ (€•‘”‰äÑ¡”±¥±¥•Ìœ€Ø¸Ô€”Í¡…É”ìµ…ÑÉ¥á}™É…Ñ¥½¹€€À¸ÜÔ‘½•Ì¹½ÐÍÑ½Àµ•…¹¥¹œ€À¸ÜÔ‰•…ÕÍ”ÑÝ¼(€½˜Ñ¡…Ð½µµÕ¹¥ÑäÌÍÁ•¥•Ì™±½…Ð¸(´€¨©5•…ÍÕÉ•°…Ð€ÄÈàÃ\àÀÀ¸¨¨¸€à´ÍÝ••À½˜Ñ¡”µ½‘•±±•‰½àè€¨¨Èää‘Éäµ…ÉÍ µ•‘”ÍÑ…Ñ¥½¹Ì¨¨(€€ ÈàäÁ±…¹Ñ…‰±”…Ð…±°¤…¹€¨¨ÈàØ½Ù•ÈÝ…Ñ•È¨¨¸	½Ñ ±¥±¥•ÌÝ•É”±•…°…Ð…±°€Èàä‘ÉäÍÑ…Ñ¥½¹Ì(€…¹…É”¹½Ü±•…°…Ð¹½¹”ìÑ¡”…ÑÑ…¥°¥ÌÕ¹¡…¹•…Ð€Èàä‘Éä€¼€ÈÜÌÝ•Ð¸ÐÑ¡”µ…ÉÍ µ•‘”(€ÍÑ…Ñ¥½¸¹•…É•ÍÐÑ¡”™½É­ÌÑ¡”ÍÝ…É¡½±‘Ì¥ÑÌ‘•¹Í¥ÑäƒŠP€¨¨È€ÐàÌƒŠH€È€ÐàÄÉ½½Ñ•¥¹ÍÑ…¹•Ì°(€€ÐÜ€ÔÔÄƒŠH€ÐÜ€ÐÌÔÑÉ¥…¹±•Ì¨¨ƒŠP…¹Ñ¡”ÑÝ¼¡•…‘}É…å€¡•…‘ÌÑ¡…ÐÍÑ½½½¸Ñ¡…Ð‘Éä‰…¹¬°Ý¡¥ (€…É”Ñ¡”±¥±ä‰±½½µÌ°…É”½¹”¸Ý•ÐµÁÉ…¥É¥”½¹ÑÉ½°ÍÑ…Ñ¥½¸¥Ì¥‘•¹Ñ¥…°¸(´€¨©Q¡”…Ñ”…Í­ÌÑ¡”Á±…•È°¹½Ð„½Áä½˜¥ÑÌÉÕ±•Ì¸¨¨™±½É„¹ÍÑ…Ñ¥½¹=˜¡”°¸°ÍÁ•¥•Í%¥€ÉÕ¹Ì(€Ñ¡”Í…µ”ÍÑ…Ñ¥½¸ ¥€Ñ¡”Í…ÑÑ•ÈÉÕ¹ÌìÑ¡”Íµ½­”ÍÝ••ÁÌÑ¡”‰½àÝ¥Ñ ¥Ð…Ð‰½Ñ Ù¥•ÝÁ½ÉÑÌ…¹(€…ÍÍ•ÉÑÌ¹¼™±½…Ñ¥¹œµ±•…Ù•…ÅÕ…Ñ¥Œ¡…Ì„‘ÉäÍÑ…Ñ¥½¸°Ñ¡…ÐÑ¡”±¥±¥•ÌÍÑ¥±°¡…Ù”Ý•Ð½¹•Ì°…¹(€Ñ¡…ÐÑ¡”…ÑÑ…¥°ÍÑ¥±°ÍÑ…¹‘Ì½¸‰½Ñ Í¥‘•ÌƒŠPÑ¡…Ð±…ÍÐ½¹”‰•…ÕÍ”„Á±…•ÈÑ¡…Ð¡…É•™ÕÍ•(€€©•Ù•ÉåÑ¡¥¹œ¨½¸Ñ¡…Ð‰…¹¬Ý½Õ±½Ñ¡•ÉÝ¥Í”É•……Ì„Á…ÍÌ¸(´€¨©]¡…ÐÑ¡¥Ì‘½•Ì¹½Ð±…¥´¸¨¨Q¡…ÐÑ¡”±¥±¥•Ì…É”…ÐÑ¡”™½É­Ì…Ð…±°¥ÌÍÑ¥±°¥¹™•ÉÉ•‘€™É½´„(€É•¥½¹…°™±½É„€¡ÍÝ¥¹­}Ý¥±¡•±µ|ÄääÑ€¤°…Ð„Ñ½­•¸‘•¹Í¥Ñä°…¹Ý¡•É”Ñ¡”Á…‘ÌÍ¥ÐÝ¥Ñ¡¥¸Ñ¡”(€•¥¡Ðµµ•ÑÉ”µ…ÉÍ •‘”¥ÌÑ¡”Í…ÑÑ•ÈÌ°¹½Ð„Í½ÕÉ”Ì¸Q¡”¡…¹”µ½Ù•Ì„ÍÁ•¥•Ì™É½´É½Õ¹(€¥Ð…¹¹½Ð½ÕÁäÑ¼É½Õ¹¥Ð…¸ì¥Ð¥Ì¹½Ð¹•Ü•Ù¥‘•¹”Ñ¡…Ð¥ÐÝ…ÌÑ¡•É”¸((ŒŒ-¹½Ý¸Ý•…­¹•ÍÍ•Ì°ÍÑ…Ñ•Á±…¥¹±ä((Á„¸€¨©Q¡”…Ñ”Ñ¡…Ð•á¥ÍÑÌÑ¼…Ñ „‰Õ¥±‘¥¹œÍÑ…¹‘¥¹œ½¸¹½Ñ¡¥¹œÉ•Á½ÉÑ•„Á•É™•Ð(€€€±…¹‘¥¹œ™½È„™½ÉÐ€àÌÈ´Á…ÍÐÑ¡”•‘”½˜Ñ¡”Ý½É±¸¨¨½ÕÉÑ••¸ÍÑÉÕÑÕÉ•ÌÝ•¹Ð¥¸½¸€ÈÀÈØ´Àà´ÄÄ…Ð(€€€±½…°€¬ÄÄÌÃŠ˜¬ÄÄàÀìÑ¡””ÄàÌÑ}¡…É‰½É}ÕÑ€¡•¥¡Ñ™¥•±ÍÑ½ÁÌ…Ð€¬ÌÈÀ¸Q¡…ÐµÕ ¥Ì0ÐÀÌ(€€€ÁÉ½‰±•´…Ð™½ÕÈÑ¥µ•ÌÑ¡”‘¥ÍÑ…¹”…¹¥Ð¥Ì¡½¹•ÍÑ±ä‘•±…É•½¸•Ù•ÉäÉ•½É¸€¨©Q¡”Á…ÉÐ(€€€Ñ¡…Ð¥Ì„‘•™•Ð¥¸Ñ¡”µ…¡¥¹•ÉäÉ…Ñ¡•ÈÑ¡…¸¥¸Ñ¡”‘…Ñ„¨¨èÑ½½±Ì½¡•¥¡Ñ™¥•±¹Áå€±…µÁÌ(€€€½ÕÑÍ¥‘”Ñ¡”‰½à°Í¼Ñ¡”É½Õ¹µ½¹Ñ…Ð¡•¬Í…µÁ±•Ñ¡”±…µÁ••‘”™½ÈÑ¡”ÍÑÉÕÑÕÉ”Ì(€€€‰…Í”9™½È•Ù•ÉäÁ½¥¹Ð½˜¥ÑÌ½ÕÑ±¥¹”°½ÐÑ¡”Í…µ”¹Õµ‰•ÈÑÝ¥”°…¹½¹±Õ‘•Ñ¡…ÐÑ¡”(€€€™½ÉÐµ••ÑÌÑ¡”É½Õ¹¸Ù•ÉäÍÑÉÕÑÕÉ”0ÐÀ½Ù•ÉÌÝ…Ì…Õ¡Ð½¹±ä‰•…ÕÍ”Ñ¡”±…µÁ••‘”(€€€Ù…É¥•Ì…±½¹œ„Ý…±°…¹ÁÉ½‘Õ•„…ÀìÑ¡”™½ÉÐÝ…Ì™…È•¹½Õ ½ÕÐ…¹ÍÅÕ…É”•¹½Õ ½¸Ñ¼(€€€ÁÉ½‘Õ”¹½¹”¸Q¡”…Ñ”½Õ±Í•”‰Õ¥±‘¥¹ÌÑ¡…ÐÝ•É”¹•…É±äÉ¥¡Ð…¹Ý…Ì‰±¥¹Ñ¼½¹”Ñ¡…Ð(€€€Ý…Ì½µÁ±•Ñ•±äÝÉ½¹œ¸!•¥¡Ñ™¥•±¹½Ù•ÉÌ ¥€¹½Ü…Í­ÌÝ¡•Ñ¡•ÈÑ¡•É”¥Ì…¹äÉ½Õ¹Ñ¡•É”…Ð(€€€…±°‰•™½É”…Í­¥¹œ¡½Ü¡¥ ¥Ð¥Ì°Ñ¡”Í¡•µ„…ÉÉ¥•Ì…¸½ÕÑÍ¥‘•}µ½‘•±±•‘}É½Õ¹‘€ÍÑ…Ñ”(€€€‰•Í¥‘”…ÁÁÉ½…¡}¹½Ñ}µ½‘•±±•‘€°…¹Ñ¡”‘•±…É…Ñ¥½¸¥Ì¡•­•……¥¹ÍÐÑ¡”µ•…ÍÕÉ•µ•¹Ð¥¸(€€€‰½Ñ ‘¥É•Ñ¥½¹Ì¸QÕÉ¹¥¹œ¥Ð½¸¥µµ•‘¥…Ñ•±ä™±…•ÑÝ¼ÍÑÉÕÑÕÉ•Ì¥¸½Ñ¡•ÈÁ…É•±ÌÑ¡…Ð(€€€¹½Ñ¡¥¹œ¡……Õ¡Ð¸€¨©LÉ”Á…É•°€¡ˆ¤Ñ¡•¸±…¹‘•Ñ¡”Í…µ”‘…ä¨¨…¹Ñ¡”™¥•±¹½ÜÉ•…¡•Ì€¬ÄÜÀÀ°Í¼ÑÝ•±Ù”½˜(€€€Ñ¡”™½ÕÉÑ••¸™½ÉÐÍÑÉÕÑÕÉ•Ì±…¹…¹Ñ¡•¥È‘•±…É…Ñ¥½¹Ì…É”½¹”¸QÝ¼‘¼¹½Ð°™½È„(€€€‘¥™™•É•¹Ð…¹‰•ÑÑ•ÈÉ•…Í½¸èÑ¡”™½ÉÐÍ¥ÑÌ½¸„Á±…Ñ•…ÔÑ¡…Ð™…±±ÌÑ¼Ñ¡”É¥Ù•È‰•ÑÝ••¸(€€€8€¬ÈÐÔ…¹8€¬ÈÜÀ°…¹Ñ¡”ÍÑ½­…‘”Ì¹½ÉÑ Ý…±°…¹Ñ¡”½µµ…¹‘…¹ÐÌÅÕ…ÉÑ•ÉÌÉ½ÍÌÑ¡”(€€€Ñ½À½˜Ñ¡…Ð™…±°‰ä€Ä¸ÐÀ´…¹€À¸ÐØ´¸€¨©9¼ÕÐ°™¥±°°É•Ù•Ñµ•¹Ð½È™½Õ¹‘…Ñ¥½¸¥Ìµ½‘•±±•(€€€…¹åÝ¡•É”¥¸Ñ¡¥ÌÁÉ½©•Ð¨¨°…¹Ñ¡”É•…°Ý½É¬Á±…¥¹±ä¡…½¹”¸0ÐØÝ…ÌÉ•ÝÉ¥ÑÑ•¸Ñ¡”Í…µ”(€€€‘…äÑ¼Í…äÍ¼¸Q¡”‰±¥¹‘¹•ÍÌÑ¡”™½ÉÐ•áÁ½Í•¥Ì™¥á•É•…É‘±•ÍÌ½˜Ý¡•Ñ¡•È…¹åÑ¡¥¹œ(€€€ÕÉÉ•¹Ñ±ä¹••‘ÌÑ¡”¹•ÜÍÑ…Ñ”¸((ÀÀ¸€¨©Q¡”ÁÉ…¥É¥”±½Í•Ì„‰±¥¹Í¥‘”µ‰äµÍ¥‘”……¥¹ÍÐ„)Õ±äÁ¡½Ñ½É…Á °¥¸Õ¹‘•È„Í•½¹°(€€€…¹Ý”¹½Ü­¹½Ü•á…Ñ±äÝ¡ä¸¨¨™½ÕÈµÁ…É•°ÍÝ••À½¸€ÈÀÈØ´Àà´ÄÀÁÕÐ•… Á¥•”½˜Ñ¡”(€€€Ù••Ñ…Ñ¥½¸Ñ¡É½Õ ¥ÑÌ½Ý¸‰Õ¥±‘•Èµ…¹µÉ¥Ñ¥Œ±½½À……¥¹ÍÐÙ•É¥™¥•Á¡½Ñ½É…Á¡Ì½˜(€€€ÍÕÉÙ¥Ù¥¹œ%±±¥¹½¥ÌÑ…±±É…ÍÌ°Ý¥Ñ „‰±¥¹½…ÌÑ¡”©Õ‘•µ•¹Ð¸Q¡É•”É¥Ñ¥ÌÉ…¸½¸½¹”(€€€¥‘•¹Ñ¥…°Í¡½ÐÍ•Ð¸±°Ñ¡É•”±½ÍÐ¸QÝ¼½˜Ñ¡•´°½¸‘¥™™•É•¹ÐÉ•™•É•¹•Ì…¹‘¥™™•É•¹Ð(€€€™É…µ¥¹Ì°±½ÍÐ½¸Ñ¡”€¨©Í…µ”¨¨™•…ÑÕÉ”¸]¡…Ð™½±±½ÝÌ¥ÌÑ¡”µ•…ÍÕÉ•ÍÑ…Ñ”°É•½É‘•(€€€‰•…ÕÍ”¥Ð¥Ìµ½É”ÕÍ•™Õ°Ñ¡…¸Ñ¡”ÍÕµµ…Éä€‰¹••‘ÌÝ½É¬ˆè((€€€€´€¨©Q¡”µ¥µ™¥•±Í¡••Ð¥Ì‘¥Í…É‘•…ÐøÐÔÔ´¸¨¨…¹½ÁäÉ¥¹Ì™É½´€È¸Ô´Ñ¼€ÐÔÌ´Í¥Ð…Ð(€€€€€Ñ¡”ÍÝ…ÉÑ½Àì™É½´€ÔÄÄ¸à´½ÕÑÝ…É•Ù•ÉäÉ¥¹œ‘É½ÁÌÑ¼ä€ô€À¸ÀÕ€Ý¥Ñ …5…Í¬€ô€Á€…¹(€€€€€Ñ¡”Í¡…‘•È‘¥Í…É‘Ì¥Ð¸Q¡”Ù••Ñ…Ñ•ÍÕÉ™…”Ñ¡•É•™½É”•¹‘ÌÝ¡•É”Ñ¡”™½œ¥Ì½¹±ä(€€€€€€ÈÜ€”°…¹Ñ¡”€äÌ€”¡…é”Ý½É±¹©Í€‘•Í¥¹Ì™½È…Ð€ÄÈäÀ´¥Ì¹•Ù•ÈÉ•¹‘•É•½¹Ñ¼…¹ä(€€€€€Ù••Ñ…Ñ•Á¥á•°¸€¨©±°Ñ¡É•”Á…É•±Ì¡…Ù”‰••¸½¹Ù•É¥¹œ½¸„½±½ÕÈ¹¼Ù¥Í¥‰±”(€€€€€ÍÕÉ™…”¥¸Ñ¡”Í•¹”É•…¡•Ì¸¨¨Q¡¥Ì½¹”™…ÐÁÉ½‘Õ•ÌÑ¡”‰±¥¹Ñ•±°¥¸‰½Ñ Á…¥ÉÌ°(€€€€€Ñ¡”µ¥ÍÍ¥¹œ…•É¥…°É••ÍÍ¥½¸°Ñ¡”½±±…ÁÍ•É…¥¸…¹Ñ¡”É¥¹œÍ•…´‰•±½Ü¸(€€€€´€¨©Q¡•É”¥Ì¹¼…•É¥…°É••ÍÍ¥½¸½¸™±…ÐÉ½Õ¹…¹Ñ¡•É”ÍÑÉÕÑÕÉ…±±ä…¹¹½Ð‰”¸¨¨Ð„(€€€€€€Ä¸Øà´•å”Ý¥Ñ „€Ô×
ÀÙ•ÉÑ¥…°™¥•±½Ù•È€àÀÀÉ½ÝÌ°„É½Õ¹Á½¥¹Ð…Ð‘¥ÍÑ…¹”€©¨(€€€€€±…¹‘Ì€ÄÈäÀ¸ä½‘€Áà‰•±½ÜÑ¡”¡½É¥é½¸ƒŠPÍ¼Ñ¡”•¹Ñ¥É”™½œÉ…µÀ™É½´€ÄÀ€”Ñ¼€äÌ€”±¥Ù•Ì(€€€€€‰•ÑÝ••¸É½ÝÌ€ÐÀÈ…¹€ÐÀØ¸M¥àÁ¥á•±Ì½˜…Ñµ½ÍÁ¡•É”¥¸…¸€àÀÀµÁ¥á•°™É…µ”¸=¹±äÙ•ÉÑ¥…°(€€€€€ÍÑÉÕÑÕÉ”…ÉÉ¥•¥¹Ñ¼Ñ¡”‘¥ÍÑ…¹”…¸‰ÕäÉ••ÍÍ¥½¸¡•É”ì•áÁ½¹•¹Ñ¥…°‘¥ÍÑ…¹”™½œ(€€€€€…¹¹½Ð¸(€€€€´€¨©É¥¹œÍ•…´‘É…ÝÌ„ÍÑÉ…¥¡Ð±¥¹”…É½ÍÌÑ¡”™É…µ”¸¨¨QU9¹µ¥¹É…‘¥ÕÌ€ô€ÈÜ¸Àµ€°…¹(€€€€€½¸™±…ÐÉ½Õ¹„½¹ÍÑ…¹ÐÉ…‘¥ÕÌµ…ÁÌÑ¼„½¹ÍÑ…¹ÐÍÉ••¸É½ÜƒŠPÁÉ•‘¥Ñ•€ÐÐà¸à°(€€€€€µ•…ÍÕÉ•…ÐÉ½Ü€ÐÔÀ¥¸ÁÉ…¥É¥•}Í½ÕÑ¡€°É…é½ÈµÍÑÉ…¥¡Ð…É½ÍÌ…±°€ÄÈàÀ½±Õµ¹Ì¸(€€€€´€¨©É…¥¸½±±…ÁÍ•ÌÝ¥Ñ ‘•ÁÑ Ý¡•É”Ñ¡”Á¡½Ñ½É…Á¡Ìœ¥Ì™±…Ð¸¨¨€×\Ô¡¥ µÁ…ÍÌI5L¥¸(€€€€€‰…¹‘Ì‘½Ý¸™É½´Ñ¡”±…¹½Í­ä‰½Õ¹‘…Éäè½ÕÉÌ€ÄÌ¸à€¼€ÄÐ¸Ø€¼€ÈÄ¸È°‰½Ñ É•™•É•¹•Ì(€€€€€€Äà¸à€¼€ÌÄ¸Ð€¼€Ìä¸Ì…¹€Ìä¸Ì€¼€ÐÄ¸Ü€¼€ÐÄ¸Ì¸(€€€€´€¨©Q¡”¡½É¥é½¸Ñ¥µ‰•È¥Ì¹•…É±ä…‰Í•¹Ð¸¨¨Q¥µ‰•È¥Ì‘•Ñ•Ñ•¥¸€¨¨ÌÄ€”¨¨½˜¡½É¥é½¸(€€€€€½±Õµ¹Ì½Ù•É…±°…¹€Ì¸Ø€”…É½ÍÌÑ¡”•¹ÑÉ…°ÑÝ¼µÑ¡¥É‘Ì°……¥¹ÍÐ€¨¨ÄÀÀ€”¨¨½˜½±Õµ¹Ì¥¸(€€€€€•Ù•Éä‰…¹½˜Ñ¡”É•™•É•¹”¥¹±Õ‘¥¹œ¥ÑÌ™…¥¹Ñ•ÍÐ¸Q¡”€ËŠLÐÁà‰…¹€©¡•¥¡Ð¨¥Ì¡½¹•ÍÐ(€€€€€…É¥Ñ¡µ•Ñ¥ŒìÑ¡”•µÁÑ¥¹•ÍÌ¥Ì¹½Ð¸É½Õ¹Ñ¡…ÐÉ•Á½ÉÑ•É”µÑ½¹¥¹œÑ¡¥Ì‰…¹¡…¥¸™…Ð(€€€€€É•‘Õ•¥ÑÌ‘•Ñ•Ñ¥½¸½Ù•È™É½´€ÈÄ¸Ä€”Ñ¼€À¸ä€”°…¹Ñ¡”Ñ…É•Ð¥ÐÝ…Ì¥Ù•¸(€€€€€€¡]•‰•È€À¸ÀÌÛŠLÀ¸ÀØÜ¤‘½•Ì¹½Ð•á¥ÍÐ¥¸Ñ¡”É•™•É•¹”…Ð…¹äÑ¡É•Í¡½±ƒŠPÑ¡…Ð•ÉÉ½ÈÝ…Ì(€€€€€Ñ¡”‰É¥•˜Ì°¹½ÐÑ¡”‰Õ¥±‘•ÈÌ¸(€€€€´€¨©É½Ý¹ÌÉ•……Ì‰½Õ±‘•ÉÌ¸¨¨¥¹”µ‘•Ñ…¥°É…Ñ¥¼€À¸ÈÏŠLÀ¸ÌÐ……¥¹ÍÐÑ¡”Á¡½Ñ½É…Á Ì(€€€€€€À¸ØÇŠLÀ¸ØÐƒŠP½ÕÈÉ½Ý¹Ì…Ð€ÈÃŠLØÀ´…ÉÉäÑ¡”™¥¹”µÍ…±”Ñ•áÑÕÉ”½˜„Á¡½Ñ½É…Á Ì(€€€€€­¥±½µ•ÑÉ”µ‘¥ÍÑ…¹ÐÑÉ••±¥¹”¸M¡…‘½ÝÌ±¥ÀÑ¼±¥Ñ•É…°€ À°À°À¥€Ý¡•É”Ñ¡”Á¡½Ñ½É…Á Ì(€€€€€‘…É­•ÍÐ‘•¥±”¥Ì0€ÄÓŠLÈÜ°…¹ÍÕ¹±¥ÐÉ½Ý¸Ñ½ÁÌ…É”€¨©‰±Õ”¨¨€¡Š"IƒŠ"HÄäÑ¼ƒŠ"HÈØ¤Ý¡•É”(€€€€€Ñ¡”Á¡½Ñ½É…Á Ì…É”Ý…É´É••¸€ ¬ÄÌÑ¼€¬ÈÐ¤¸(€€€€´€¨©Q¡”Í¡½ÐÍ•Ð¡…Ì½¹±ä½¹”½Á•¸µÁÉ…¥É¥”Ù¥•Ü¸¨¨ÁÉ…¥É¥•}Í½ÕÑ¡€ÍÑ…¹‘Ì€Ì¸ÐØ´™É½´„(€€€€€ÑÉÕ¹¬Ý¥Ñ €ÈÌ¸Ð€”½Á•¸Í­ä……¥¹ÍÐÁÉ…¥É¥•}Ý•ÍÑ€Ì€äÔ¸Ð€”¸Q¡…ÐÍ•½¹…¹±”•á¥ÍÑÌ(€€€€€ÁÉ•¥Í•±ä…ÌÑ¡”½¹ÑÉ½°Ñ¡…ÐÍ•Á…É…Ñ•Ì„ÑÕ¹•Ù¥•Ü™É½´„™¥á•½¹”°Í¼(€€€€€ÁÉ…¥É¥•}Ý•ÍÑ€¡…Ì‰••¸ÑÕ¹•……¥¹ÍÐ¥ÑÍ•±˜Ý¥Ñ ¹¼½¹ÑÉ½°¸(€€€€´€¨©É¥Ù•É}‰…¹­€™…¥±Ì¥ÑÌ½Ý¸‰É¥•˜…¹Ñ¡”™…Õ±Ð¥ÌÑ¡”É•¹‘•É•È°¹½ÐÑ¡”‘…Ñ„¸¨¨i½¹”€Ä(€€€€€ÍÁ•¥™¥•Ì½É‘É…ÍÌ…Ð€Ä¸ËŠLÈ¸À´…¹€ÐÃŠLÔÔ€”½Ù•ÈÝ¥Ñ ‰…É•}Í½¥±}™É…Ñ¥½¸è€À¸Á€ìÑ¡”(€€€€€™É…µ”Í¡½ÝÌøÈÔ´ÍÁÉ¥Ì½¸Ù¥Í¥‰±”‰…É”Í½¥°¥¸¹•…ÈµÉ½ÝÌ¸((€€€QÝ¼Ñ¡¥¹Ì…µ”½ÕÐ½˜Ñ¡”ÍÝ••À±•…¸…¹Í¡½Õ±‰”Í…¥…ÌÁ±…¥¹±ä…ÌÑ¡”™…¥±ÕÉ•Ì¸Q¡”(€€€€¨©)Õ±äÁ¡•¹½±½ä¥Ì½ÉÉ•Ð…ÐÍ½ÕÉ”¨¨ƒŠP•Ù•ÉäÝ…É´µÍ•…Í½¸É…ÍÌÙ••Ñ…Ñ¥Ù”Ý¥Ñ „¹Õ±°(€€€¥¹™±½É•Í•¹”°…ÑÑ…¥°™ÉÕ¥Ñ¥¹œ…¹‰É½Ý¸°É…µÀ±•…™±•ÍÌ°…¹„±¥Ù”Õ…ÉÑ¡…ÐÍÕÁÁÉ•ÍÍ•Ì(€€€…¹É•Á½ÉÑÌ…¹äÉ•½ÉÑ¡…Ð½¹ÑÉ…‘¥ÑÌ¥ÑÍ•±˜¸¹Ñ¡”€¨©™±½É„‘…Ñ…Í•Ð¥ÌÑ¡”½¹”Á…É•°(€€€„É¥Ñ¥ŒÁ…ÍÍ•Ý¥Ñ¡½ÕÐÉ•Í•ÉÙ…Ñ¥½¸¨¨¸Q¡”É•¹‘•É•È¥ÌÝ¡…Ð¥Ì™…¥±¥¹œ¥Ð¸((€€€QÝ¼µ•Ñ¡½‘½±½¥…°½ÉÉ•Ñ¥½¹ÌÝ½ÉÑ ­••Á¥¹œ°‰½Ñ ½˜Ý¡¥ ¥¹Ù…±¥‘…Ñ”¹Õµ‰•ÉÌÑ¡¥Ì(€€€ÁÉ½©•Ð¡…ÌÅÕ½Ñ•è((€€€€´€¨©Q¡”ÁÉ¥µ…ÉäÉ•™•É•¹”Ý…ÌÑ¡”ÝÉ½¹œÁ¡½Ñ½É…Á ¸¨¨‘ÕÁ…•}Ñ…±±É…ÍÍ|ÈÀÄà´ÀÜ´ÈÐ¹©Á€¥Ì(€€€€€Ñ¥Ñ±•€ˆ©I•ÍÑ½É•¨Ñ…±±É…ÍÌÁÉ…¥É¥”ˆ…¹‘•ÍÉ¥‰•…Ì„€‰AÉ…¥É¥”Á±…¹Ñ¥¹œˆ½¸„™½Éµ•È(€€€€€…É¥Õ±ÑÕÉ…°™¥•±ƒŠP„Í••µ¥à½¸Á±½Ý•É½Õ¹°…¹É•ÍÑ½É…Ñ¥½¹Ì…É”‰½Õ¡Ð™½È‰•¥¹œ(€€€€€™½ÉˆµÉ¥ ¸Q¡”¹•Ù•ÈµÁ±½Ý•]½½‘Ý½ÉÑ ÍÑ…¹¥ÌÑ¡”‰•ÑÑ•È…¹…±½Õ”™½ÈÕ¹µ…¹…•€ÄàÌÔ(€€€€€ÁÉ…¥É¥”¸ùù5•…ÍÕÉ•™±½Ý•È±½…èÁ±…¹Ñ¥¹œ€ÄÈ¸äÄ€”°Ù¥É¥¸É•µ¹…¹Ð€Ä¸ÜçŠLÔ¸ÔÐ€”¸Q¡”¡½¹•ÍÐ(€€€€€Ñ…É•Ð¥Ì€¨¨ÓŠLØ€”°¹½Ð€ÄÌ¸àä€”¨¨¹ùø€¨©Q!=IIQ%=8]LI%!P9%QL9U5	ILI(€€€€€]%Q!I]8°€ÈÀÈØ´Àà´ÄÔ‰äHµ\ÑŒ¡ˆÄ¤¸¨¨9•¥Ñ¡•È±…ÕÍ”ÍÕÉÙ¥Ù•Ì¡•­¥¹œ¸€¨©9¼¹•Ù•ÈµÁ±½Ý•(€€€€€É•µ¹…¹ÐÁ¡½Ñ½É…Á ¥Ì½µµ¥ÑÑ•Ñ¼Ñ¡¥ÌÉ•Á½Í¥Ñ½Éä…¹¹¼Í½ÕÉ”É•½É‘•ÍÉ¥‰•Ì½¹”¨¨ƒŠP(€€€€€Ñ¡”Á¡É…Í”½ÕÉÌ½¹”¥¸‘…Ñ„½Í½ÕÉ•Ì½€°¥¹Í¥‘”Ñ¡”É•½É½˜Ñ¡”Á±…¹Ñ¥¹œ°¥Ñ¥¹œ(€€€€€¹½Ñ¡¥¹œƒŠPÍ¼Ñ¡”€Ä¸ÜçŠLÔ¸ÔÐ€”¡…±˜¥ÌÕ¹Í½ÕÉ•¸¹€ÄÈ¸äÄ€”‘½•Ì¹½ÐÉ•ÁÉ½‘Õ”èÑ¡”(€€€€€½µµ¥ÑÑ•É•¥Á”É•…‘Ì€¨¨Ô¸ÔÐ€”¨¨½¸Ñ¡…Ð™É…µ”°€Ü¸ÀÈ€”½¸¥ÑÌ¹•…É•ÍÐÅÕ…ÉÑ•È…¹€ÈÔ¸àÈ€”(€€€€€Ý¥Ñ ¥ÑÌÑÝ¼Ñ•ÍÑÌÉ•½É‘•É•¸€¨©Q¡•É”¥ÌÑ¡•É•™½É”¹¼€ÓŠLØ€”Ñ…É•Ð¨¨°…¹Ñ¡¥Ì™¥±”µÕÍÐ(€€€€€¹½Ð‰”É•……ÌÍ•ÑÑ¥¹œ½¹”¸¹½‘”Ñ½½±Ì½µ•…ÍÕÉ•}‰±½½µ}Ñ…É•Ð¹µ©Í€ÁÉ¥¹ÑÌ…±°½˜¥Ðì(€€€€€I=5@ƒ
œHµ\ÑŒ¡ˆÄ¤…ÉÉ¥•ÌÑ¡”É•…Í½¹¥¹œ…¹Ñ¡”Ñ¡É•”É½ÕÑ•Ì½ÕÐ¸(€€€€´€¨©QÝ¼É½Õ¹‘ÌÝ•É”©Õ‘•…ÐÑ¡”ÝÉ½¹œ±½½¬µ…¹±”¸¨¨Q¡”Í¡½Ð¡…É¹•ÍÌÍ•Ð¹¼Á¥Ñ Ý¡¥±”(€€€€€Ñ¡”É•™•É•¹”Á¡½Ñ½É…Á¡•È¡…Ñ¥±Ñ•‘½Ý¸øÄË
À°Í¼•Ù•Éä€‰¹•…É•ÍÐÅÕ…ÉÑ•Èˆ¹Õµ‰•È(€€€€€½µÁ…É•Ñ¡”Á¡½Ñ½É…Á …Ð€È´……¥¹ÍÐ½ÕÈÉ•¹‘•È…Ð€Ð´ƒŠP…¹¹•…Èµ™¥•±Ù••Ñ…Ñ¥½¸Ý…Ì(€€€€€•á…Ñ±äÝ¡…ÐÑ¡½Í”É½Õ¹‘ÌÝ•É”ÑÕ¹¥¹œ¸Q¡”¡…É¹•ÍÌ¥Ì¹½ÜÁ¥Ñ µµ…Ñ¡•…¹ÁÉ¥¹ÑÌ¥ÑÌ(€€€€€Á¥Ñ ¸½ÉÉ•Ñ¥¹œ¥Ðµ…­•ÌÑ¡”…À€©Ý½ÉÍ”¨è€À¸ÀÜ€”……¥¹ÍÐ„Ù¥É¥¸É•µ¹…¹ÐÌ€È¸äÜ€”¸(€€€€´¡Õ”½Í…ÑÕÉ…Ñ¥½¸Ñ•ÍÐ…¹¹½ÐÍ•Á…É…Ñ”)Õ±ä™É½´=Ñ½‰•È¡•É”ƒŠPÑ¡”=Ñ½‰•È¹•…Ñ¥Ù”(€€€€€½¹ÑÉ½°±…¹‘Ì€©‰•ÑÝ••¸¨Ñ¡”ÑÝ¼)Õ±äÁ¡½Ñ½É…Á¡Ì¸Q¡…Ðµ•ÑÉ¥ŒÍ¡½Õ±¹½Ð‰”ÅÕ½Ñ•‰ä(€€€€€…¹å½¹”°¥¹±Õ‘¥¹œÑ¡¥Ì™¥±”¸((À¸€¨©Q¡”™½Éµ•ÈÍ±½ÜµÉ•¹‘•É•ÈÝ…±­¥¹œ™…¥±ÕÉ”¥ÌÉ•Í½±Ù•Ý¥Ñ¡½ÕÐÝ•…­•¹¥¹œ¥ÑÌ‘¥ÍÑ…¹”‰…È¸¨¨(€€5½Ù•µ•¹Ð¹½Ü½¹ÍÕµ•ÌÕÀÑ¼„ÅÕ…ÉÑ•ÈµÍ•½¹½˜É•…°™É…µ”Ñ¥µ”¥¸Ñ•ÉÉ…¥¸µ…¹µ½±±¥Í¥½¸(€€ÍÕ‰ÍÑ•ÁÌ¹¼±…É•ÈÑ¡…¸€À¸ÀÔÌ¸Í½™ÑÝ…É”É•¹‘•É•È‘É…Ý¥¹œ½¹±äÑÝ¼™É…µ•ÌÁ•ÈÍ•½¹¹¼(€€±½¹•ÈÑÕÉ¹Ì„€Ä¸ÐÔ´½ÌÝ…±¬¥¹Ñ¼„É…Ý°°Ý¡¥±”Ñ¡”Í¡½ÉÐÍÕ‰ÍÑ•ÁÌÉ•Ñ…¥¸‰…¹¬…¹‰Õ¥±‘¥¹œ(€€½±±¥Í¥½¸…ÕÉ…ä¸Q¡”™½É•É½Õ¹Íµ½­”ÉÕ¸Á…ÍÍ•ÌÑ¡”Í…µ”Ý…±¬µ‘¥ÍÑ…¹”…ÍÍ•ÉÑ¥½¸…Ð(€€‰½Ñ €ÌäÃ\ÜàÀ…¹€ÄÈàÃ\àÀÀ¸ÕÉÉ•¹Ð™Õ±°µÍ•¹”‰Õ‘•ÑÌ…É”€Ðä€¼€ÔÌ‘É…Ü…±±Ì…¹€ÌÜà°ØÐÜ€¼(€€€Ðää°ÌÐÌÑÉ¥…¹±•ÌÉ•ÍÁ•Ñ¥Ù•±äìÑ¡”‘•Í­Ñ½ÀÉ•¹‘•É•ÈÉ•µ…¥¹ÌÍ±½Ü…Ð€È™ÁÌÕ¹‘•ÈMÝ¥™ÑM¡…‘•È°(€€‰ÕÐ•±…ÁÍ•µÑ¥µ”Ý…±­¥¹œ¥Ì¹¼±½¹•È½ÕÁ±•Ñ¼Ñ¡…Ð™É…µ”½Õ¹Ð¸((Ä¸€¨©=¹”ÍÑÉÕÑÕÉ”É•½É‘½•Ì¹½ÐÁÉ½Ù”Ñ¡”Í¡•µ„¸¨¨Q¡”M…Õ…¹…Í •á•É¥Í•ÌÁ¡…Í•Ì°„(€€‰Õ¥±‘¥¹œµ½Ù”°…¹Ñ¡”™Õ±°½¹™¥‘•¹”É…¹”°‰ÕÐÑ¡”µ½‘•°¡…Ì¹½Ðµ•Ð„™½ÉÐ°„‰É¥‘”°½È(€€„É½Ü½˜ÍÑ½É•™É½¹ÑÌå•Ð¸áÁ•ÐÍ¡•µ„ÁÉ•ÍÍÕÉ”…Ð5¥±•ÍÑ½¹”€Ä¸(È¸€¨©½¹ÍÑÉÕÑ¥½¸è‰…±±½½¹}™É…µ•€½¸Ñ¡”M…Õ…¹…Í ¥ÌÁÉ½‰…‰±äÝÉ½¹œ¨¨…¹¥Ì™±…•…ÌÍÕ (€€¥¸Ñ¡”É•½É¸	…±±½½¸™É…µ¥¹œÁ½ÍÑ‘…Ñ•ÌÑ¡”€ÄàÌÄ‰Õ¥±‘¥¹œ‰ä„å•…È¸1•™ÐÙ¥Í¥‰±”É…Ñ¡•È(€€Ñ¡…¸Í¥±•¹Ñ±äÍÝ…ÁÁ•°‰•…ÕÍ”ÍÕ‰ÍÑ¥ÑÕÑ¥¹œ½¹”Õ•ÍÌ™½È…¹½Ñ¡•È¥Ì¹½Ð„™¥à¸(Ì¸€¨©Q¡”M…Õ…¹…Í …±±•ÉäÉ•…‘¥¹œÝ…ÌÉ•Ù¥Í•½¸‘…ä½¹”¨¨°™É½´€‰…±±•Éä°½¹©•ÑÕÉ…°ˆÑ¼(€€€‰¹¼…±±•Éä°¥¹™•ÉÉ•ˆ°…™Ñ•È½Á•¹¥¹œÑ¡”ÑÝ¼É•ÑÉ½ÍÁ•Ñ¥Ù”¥µ…•ÌÑ¡”É•Á¼…±É•…‘ä¡•±¸(€€	½Ñ Í¡½Ü¹¼Ù•É…¹‘„…¹‰½Ñ Í¡½ÜÑ¡”€ÄàÈä±½œ…‰¥¸ÍÕÉÙ¥Ù¥¹œ…Ì…¸…ÑÑ…¡•Ý¥¹œ¸Q¡”(€€¥µ…•Ì…É”¹½Ð¥¹‘•Á•¹‘•¹Ð½˜•… ½Ñ¡•È°Í¼Ñ¡¥Ì¥Ì¥¹™•É•¹”°¹½Ð‘½Õµ•¹Ñ…Ñ¥½¸ƒŠP…¹Ñ¡”(€€™É…µ•}Ñ…Ù•É¹€…É¡•ÑåÁ”¹½Ü¡…ÌÑ¼ÍÕÁÁ½ÉÐ…¸…ÑÑ…¡•±½œÝ¥¹œ¸(Ð¸€¨©QÝ¼Í½ÕÉ•Ì¡…Ù”¹¼Ý•ˆ…É¡¥Ù”¸¨¨‘É±½¥¡}¡½Ñ•±Í€¡…Ì¹¼]…å‰…¬Í¹…ÁÍ¡½Ð…¹Ñ¡”(€€Ù…±¥‘…Ñ½ÈÝ…É¹Ì…‰½ÕÐ¥Ð½¸•Ù•ÉäÉÕ¸ìÑ¡”Ý…É¹¥¹œ¥Ì½ÉÉ•Ð…¹ÍÑ…¹‘ÌÕ¹Ñ¥°Í½µ•½¹”(€€…É¡¥Ù•ÌÑ¡”Á…”¸]…Ôµ	Õ¸Ì…É¡¥Ù•‘}ÕÉ°Á½¥¹ÑÌ…Ð„Í…¹¹••‘¥Ñ¥½¸½˜Ñ¡”‰½½¬É…Ñ¡•È(€€Ñ¡…¸Ñ¡”ÑÉ…¹ÍÉ¥ÁÑ¥½¸…ÑÕ…±±äÉ•…‘ÕÉ¥¹œÉ•Í•…É ƒŠP¹½Ñ•¥¸Ñ¡”Í½ÕÉ”É•½É¸(Ô¸€¨©M•Ù•É…°É•Í•…É ±…¥µÌ…É”Í¹¥ÁÁ•Ðµ‘•É¥Ù•¸¨¨•¹å±½Á•‘¥„¹¡¥…½¡¥ÍÑ½Éä¹½É€É•ÑÕÉ¹•(€€€ÔÀÌÑ¡É½Õ¡½ÕÐÑ¡”É•Í•…É Í•ÍÍ¥½¸°…¹„™•Ü¥Ñ…Ñ¥½¹Ì¥¸Ñ¡”‘½ÍÍ¥•ÉÌÉ•ÍÐ½¸Í•…É µ¥¹‘•à(€€Í¹¥ÁÁ•ÑÌÉ…Ñ¡•ÈÑ¡…¸É•ÑÉ¥•Ù•Á…•Ì¸Q¡•äµÕÍÐ‰”É”µ™•Ñ¡•‰•™½É”…¹ä½˜Ñ¡•´¥ÌÁÉ½µ½Ñ•(€€Ñ¼‘½Õµ•¹Ñ•‘€¸(Ø¸€¨©Q¡”½¹±•ä½MÑ•±é•ÈÉ¥¡ÑÌÅÕ•ÍÑ¥½¸¥Ì½Á•¸¸¨¨5…É­•¡•­}É•ÅÕ¥É•‘€ì¹¼…ÍÍ•Ðµ…ä‰”(€€‘•É¥Ù•™É½´¥ÐÕ¹Ñ¥°„MÑ…¹™½É½ÁåÉ¥¡ÐI•¹•Ý…°…Ñ…‰…Í”¡•¬¥ÌÉ•½É‘•¸(Ü¸€¨©Q¡”€ÄàÌÔ±…­”ÍÑ…”¥Ì„Õ•ÍÌ¸¨¨€ÔàÀƒ
Ä€Ä¸Ô™ÐM0°Ñ…•½¹©•ÑÕÉ…°°…¹Ñ¡”•¹Ñ¥É”(€€Ù•ÉÑ¥…°‘…ÑÕ´¡…¹Ì½™˜¥Ð¸(à¸€¨©%aƒŠPÑ¡”Ý¡¥Ñ”Á…¥¹Ð¹½ÜÉ•…‘Ì…ÌÝ¡¥Ñ”¸¨¨Q¡”•…É±¥•È‘¥…¹½Í¥Ì¥¸Ñ¡¥Ì™¥±”€¡„Ý•…¬(€€Í­ä½¹ÑÉ¥‰ÕÑ¥½¸…Ð„É…é¥¹œÍÕ¸…¹±”¤Ý…ÌÝÉ½¹œ°…¹ÝÉ½¹œ¥¸„Ý…äÝ½ÉÑ É•½É‘¥¹œèÑ¡”(€€Ñ…¸Ý…±°Ý…Ì„MQ1AU	1%M!MMP°…¸½±‘•È‰…­”Ñ¡…ÐÍÑ¥±°…ÉÉ¥•Ñ¡”½Ù•Èµ‘…É¬<(€€Ñ•áÑÕÉ”¸QÝ¼Í•Á…É…Ñ”…ÕÍ•ÌÑ¡•¸ÑÕÉ¹•ÕÀ‰•¡¥¹¥Ð¸ÁÕ‰±¥Í ¹Í¡€Í¡¥ÁÁ•™É½´(€€…ÍÍ•ÑÌ½Ý•ˆ½€°Ý¡¥ ½¹±ä‰…­”¹Í¡€É•™É•Í¡•Ì°Í¼ÉÕ¹¹¥¹œÑ¡”•¹•É…Ñ½È‘¥É•Ñ±äÉ•ÁÕ‰±¥Í¡•(€€Ñ¡”ÁÉ•Ù¥½ÕÌµ•Í Í¥±•¹Ñ±äƒŠP¹½ÜÕ…É‘•°…¹¥ÐÍ…åÌÍ¼Ý¡•¸¥Ð½Á¥•Ì„µ…ÍÑ•ÈÑ¡É½Õ ¸(€€¹Ñ¡”Í­äµ‘•É¥Ù•A5I4•¹Ù¥É½¹µ•¹ÐÝ…Ì½Ù•ÉÉ¥‘¥¹œ…±‰•‘¼½ÕÑÉ¥¡Ðèµ•…ÍÕÉ•°„‰É½Ý¸±½œ(€€Ý…±°É•¹‘•É•…Ð…¸H½É…Ñ¥¼½˜€Ä¸Àà……¥¹ÍÐÑ¡”€Ä¸ÜÔ¥ÑÌ½Ý¸‰…Í”½±½ÕÈÍÁ•¥™¥•Ì°Ý¥Ñ (€€•Ù•ÉäÍÕÉ™…”½¹Ù•É¥¹œ½¸Ñ¡”Í­ä½±½ÕÈÝ¡…Ñ•Ù•È¥ÐÝ…Ìµ…‘”½˜¸½È„ÁÉ½©•ÐÝ¡½Í”(€€±…¥´¥ÌÑ¡…Ð„‘½Õµ•¹Ñ•Ý¡¥Ñ”Ý…±°É•…‘Ì…ÌÝ¡¥Ñ”°Ñ¡…Ð¥Ì„‘…Ñ„µ¥¹Ñ•É¥Ñä‰ÕœÝ•…É¥¹œ(€€…¸…•ÍÑ¡•Ñ¥Ì½ÍÑÕµ”¸Q¡”•¹Ù¥É½¹µ•¹Ð¥Ì½¹”ì„¡•µ¥ÍÁ¡•É”™¥±°Ý¥Ñ „Ý…É´É½Õ¹‰½Õ¹”(€€Á±ÕÌÑ¡”ÍÕ¸¹½Ü…ÉÉäÑ¡”±¥¡Ñ¥¹œ°…¹¡Õ”¥ÌÁÉ•Í•ÉÙ•€¡±½œH½€Ä¸ÌÀ¤¸I•Ù¥Í¥ÐÝ¥Ñ „(€€ÁÉ½Á•É±ä•áÁ½Í•!I$É…Ñ¡•ÈÑ¡…¸„A5I4½˜…¸…¹…±åÑ¥ŒÍ­ä¸(ä¸€¨©<¥Ì‰…­•‰ÕÐÍÝ¥Ñ¡•½™˜°‘•±¥‰•É…Ñ•±ä¸¨¨Q¡”‰…­”Á…Ñ Ý½É­Ì•¹Ñ¼•¹…¹¥ÌÝ¥É•(€€…Ì„É•…°±Q½±ÕÍ¥½¸Ñ•áÑÕÉ”°‰ÕÐÑ¡”…É¡•ÑåÁ”Ì±…Á‰½…É½ÕÉÍ•Ì…¹Ý¥¹‘½ÜÉ•Ù•…±Ì(€€Í¥Ð„•¹Ñ¥µ•ÑÉ”½™˜Ñ¡”Ý…±°…¹½±Õ‘”•… ½Ñ¡•Èè„µ•…ÍÕÉ•‰…­”½µ•Ì½ÕÐ…Ðµ•…¸€À¸ÈØÔ(€€Ý¥Ñ €Øä”½˜Ñ•á•±Ì‰•±½Ü¡…±˜°…¹Ñ¡”‰Õ¥±‘¥¹œÉ•¹‘•ÉÌ‰É½Ý¸¸M¡½ÉÑ•¹¥¹œÑ¡”<‘¥ÍÑ…¹”(€€½¹±äÉ•…¡•Ì€À¸Ìà¸%Ð¹••‘Ì„±½ÜµÁ½±ä<…”°¹½Ð„ÑÕ¹¥¹œÑÝ•…¬¸€¨©m	½Ñ ™¥ÕÉ•ÌY=%ƒŠP(€€P´ÀÄÔà°€ÈÀÈØ´Àà´ÈÜì…¹Ñ¡”•áÁ½ÉÐÝ…ÌÍ¡¥ÁÁ¥¹œ„‰±…¬Ñ•áÑÕÉ”Ý¡•¸Ñ¡¥ÌÝ…ÌÝÉ¥ÑÑ•¸°Í¼(€€€‰É•¹‘•ÉÌ‰É½Ý¸ˆÝ…Ì¹½Ð„É•…‘¥¹œ½˜<¸Q¡”½¹±ÕÍ¥½¸ÍÕÉÙ¥Ù•Ì½¸„É•¹‘•É•™É…µ”è(€€P´ÀÈÈÜ°€ÈÀÈØ´Àà´Èà°…ÐÑ¡”Ñ½À½˜Ñ¡¥Ì™¥±”¹t¨¨€´µ…½€­••ÁÌÑ¡”Á…Ñ (€€•á•É¥Í•…¹…ÍÍ•ÑÌ½µ…¹¥™•ÍÐ¹©Í½¹€É•½É‘Ì¡½¹•ÍÑ±äÑ¡…ÐÑ¡”Í¡¥ÁÁ•…ÍÍ•Ð¡…Ì¹½¹”¸(ÄÀ¸€¨©±Ñ˜µÑÉ…¹Í™½Éµ€‘¥¹½ÐÉÕ¸¨¨°Í¼…ÍÍ•ÑÌ½Ý•ˆ½€ÕÉÉ•¹Ñ±ä¡½±‘Ì½Á¥•Ì½˜Ñ¡”(€€€Õ¹½µÁÉ•ÍÍ•µ…ÍÑ•ÉÌÉ…Ñ¡•ÈÑ¡…¸µ•Í¡½ÁÐ½-Q`È‘•É¥Ù…Ñ¥Ù•Ì¸!…Éµ±•ÍÌ…Ð€ÐÐ-ì¥ÐµÕÍÐÝ½É¬(€€€‰•™½É”Ñ¡”Ñ½Ý¸Í…±•Ì¸(ÄÄ¸€¨©%aƒŠPÑ¡”±¥‰•ÉÑ¥•Ì…É”¹½Ü…ÑÑ…¡•Ñ¼Ñ¡•¥È‰Õ¥±‘¥¹Ì¸¨¨Q¡”ÁÉ½Ù•¹…¹”Á½ÁÕÀÉ•…‘Ì(€€€ÍÕ‰©•ÑÍ€…¹Í¡½ÝÌÑ¡”±¥‰•ÉÑ¥•ÌÑ…­•¸Ý¥Ñ Ñ¡”‰Õ¥±‘¥¹œ‰•¥¹œ¥¹ÍÁ•Ñ•èÑ¡”M…Õ…¹…Í Ì(€€€™½ÕÈ°0ä½¸Ñ¡”É••¸QÉ•”°0Ü½0à½¸Ñ¡”Ñ¡É•”]½±˜A½¥¹ÐÁ±…•µ•¹ÑÌ¸	½Ñ Ù¥•ÝÌÉ•¹‘•È™É½´(€€€½¹”‘•É¥Ù•É•½ÉÑ¡É½Õ ½¹”•¹ÑÉäÉ•¹‘•É•È°Í¼Ñ¡”Á…¹•°…¹Ñ¡”…É…¹¹½Ð‘•ÍÉ¥‰”Ñ¡”(€€€Í…µ”±¥‰•ÉÑä‘¥™™•É•¹Ñ±ä°…¹Ñ¡”Íµ½­”…ÍÍ•ÉÑÌÑ¡”‘¥ÍÉ¥µ¥¹…Ñ¥¹œ…Í”ƒŠP„Í•½¹‰Õ¥±‘¥¹œ(€€€•ÑÌ¥ÑÌ½Ý¸Í•Ð°¹½ÐÑ¡”Ý¡½±”±¥ÍÐ°…¹„Í•¹”µÝ¥‘”±¥‰•ÉÑä¥Ì¹½ÐÁ¥¹¹•Ñ¼…¹ä‰Õ¥±‘¥¹œ¸(€€€€¨©½µÁ±•Ñ•¹•ÍÌ¥Ì¹½Ü•¹™½É•™½È½¹”±…ÍÌ½˜¥¹Ù•¹Ñ¥½¸°…¹½¹±ä½¹”¸¨¨Ù…±¥‘…Ñ”¹Áå€(€€€ÉÕ¹ÌÑ¡”¥¹Ù•ÉÍ”¡•¬è•Ù•ÉäÁ¡…Í”Ý¡½Í”™½½ÑÁÉ¥¹Ñ€½ÈÁ½Í¥Ñ¥½¹€¥Ì½¹©•ÑÕÉ…±€µÕÍÐ‰”(€€€±…¥µ•‰ä„±¥‰•ÉÑäÌ½Ù•ÉÌé€™¥•±ƒŠPÍÑÉÕÑÕÉ•}¥‘l¹Á¡…Í•}¥‘t¹…ÍÁ•Ñ€°‘•±…É•‰äÑ¡”(€€€‘½Õµ•¹ÐÉ…Ñ¡•ÈÑ¡…¸¥¹™•ÉÉ•™É½´¥ÑÌÝ½É‘¥¹œ¸M¥àÍÕ ¥¹Ù•¹Ñ¥½¹Ì•á¥ÍÐ¥¸Ñ¡”½µµ¥ÑÑ•(€€€‘…Ñ„€¡™¥Ù”™½½ÑÁÉ¥¹ÑÌ°Á±ÕÌ]…±­•ÈÌÁ½Í¥Ñ¥½¸¤ìÍ¥à‘•±…É…Ñ¥½¹Ì½Ù•ÈÑ¡•´¸Q¡”Í•±˜µÑ•ÍÐ(€€€…ÍÍ•ÉÑÌÑ¡”‘¥ÍÉ¥µ¥¹…Ñ¥¹œ…Í”°…¹Ñ¡…Ð…Í”½ÐÍÑÉ¥Ñ•Èè…¸•¹ÑÉäÝ¡½Í”ÁÉ½Í”¥Ì€©…‰½ÕÐ¨(€€€™½½ÑÁÉ¥¹ÑÌ…¹Á±…•µ•¹Ð°…¹Ý¡¥ ¹…µ•ÌÑ¡”‰Õ¥±‘¥¹œ°¹¼±½¹•È½Ù•ÉÌ…¹åÑ¡¥¹œ…Ð…±°¸(€€€Q¡”±…¥µÌ…É”¡•­•Ñ¡”½Ñ¡•ÈÝ…äÑ½¼ƒŠP„Ñ½­•¸¹…µ¥¹œ¹¼ÍÕ ÍÑÉÕÑÕÉ”°¹¼ÍÕ Á¡…Í”°(€€€½È…¸…ÑÑÉ¥‰ÕÑ”Ñ¡…Ð¥Ì¹½Ð½¹©•ÑÕÉ…°™…¥±ÌÑ¡”…Ñ”°Í¼…¸½Ù•Èµ±…¥´¥Ì…Ì±½Õ…Ì„…À¸(€€€¹ÑÉ¥•ÌÕ¹‘•È€¨©I•Í½±Ù•¨¨…É”•á•µÁÐ™É½´Ñ¡…Ð±…ÍÐÉÕ±”°Ý¡¥ ¥ÌÝ¡…Ð±•ÑÌ…¸…ÁÁ•¹µ½¹±ä(€€€‘½Õµ•¹ÐÍÕÉÙ¥Ù”¥ÑÌ½Ý¸‘…Ñ„‰•¥¹œ½ÉÉ•Ñ•¸€¨©Q¡”ÉÕ±”¹½Ü½Ù•ÉÌÍÑ…Ñ•™½É´…ÌÝ•±°…Ì(€€€‘É…Ý¸•½µ•ÑÉä¨¨€ ÈÀÈØ´Àà´ÄÀ¤èÑ¡”…ÍÁ•ÐÙ½…‰Õ±…Éä¥Ì•Ù•Éä…ÑÑ•ÍÑ•Ù…±Õ”¥¸„É•½ÉƒŠP(€€€™½½ÑÁÉ¥¹Ñ€°Á½Í¥Ñ¥½¹€°‘½Õµ•¹Ñ•‘}É…¹•€°Ñ¡”ÍÑÉÕÑÕÉ”µ±•Ù•°™Õ¹Ñ¥½¹€½½ÕÁ…¹ÑÍ€°…¹(€€€™½É´¸ñ…ÑÑÈù€•¹Õµ•É…Ñ•™É½´Ñ¡”‘…Ñ„É…Ñ¡•ÈÑ¡…¸™É½´„±¥ÍÐ°Í¼„¹•Ü…É¡•ÑåÁ”…ÑÑÉ¥‰ÕÑ”(€€€¥Ì¥¹Í¥‘”Ñ¡”ÉÕ±”Ñ¡”‘…ä¥Ð…ÁÁ•…ÉÌ¸]¥‘•¹¥¹œ¥Ð™½Õ¹™½ÕÈ¥¹Ù•¹Ñ¥½¹ÌÝ¥Ñ ¹¼…‘µ¥ÍÍ¥½¸ƒŠP(€€€Ñ¡”M…Õ…¹…Í €ÄàÈä…‰¥¸ÌÝ…±°¡•¥¡Ð…¹É½½˜ÑåÁ”°‰½Ñ A1!=1H¥¸Ñ¡•¥È½Ý¸¹½Ñ•Ì°(€€€…¹…±±•Éäè™…±Í•€½¸Ñ¡”É••¸QÉ•”…¹Ñ¡”]•ÍÑ•É¸°Ý¡•É”™…±Í”¥ÌÑ¡”…É¡•ÑåÁ”Ì(€€€‘•™…Õ±ÐÉ…Ñ¡•ÈÑ¡…¸„™¥¹‘¥¹œ¸Q•¸½¹©•ÑÕÉ…°Ù…±Õ•Ì°Ñ•¸‘•±…É…Ñ¥½¹Ì¸€¨©]¡…Ð¥ÌÍÑ¥±°(€€€Õ¹•¹™½É•¥Ì½µ¥ÍÍ¥½¹Ì…¹Í¥µÁ±¥™¥…Ñ¥½¹Ì¨¨°…¹Ñ¡…Ð¥ÌÑ¡”¡…É¡…±˜è…¸¥¹Ù•¹Ñ¥½¸¡…Ì„(€€€É•½ÉÑ¼Á½¥¹Ð…Ð…¹…¸½µ¥ÍÍ¥½¸‘½•Ì¹½Ð°Í¼Ñ¡”]•ÍÑ•É¸ÌÕ¹µ½‘•±±•ÍÑ…‰±”å…É€¡0ÄÀ¤(€€€…¹Ñ¡”É••¸QÉ•”ÌÍ¥‘”…‘‘¥Ñ¥½¹Ì€¡0ä¤…É”½Ù•É•‰äÁÉ½Í”…±½¹”¸9¼µ•¡…¹¥Í´…¸…Ñ „(€€€±¥‰•ÉÑäÑ…­•¸Ñ¡…Ð¹½‰½‘ä¹½Ñ¥•Ñ…­¥¹œ¸M¥à½˜Í¥àÍÑÉÕÑÕÉ•Ì…ÉÉä…Ð±•…ÍÐ½¹”±¥‰•ÉÑä°(€€€Í¼Ñ¡”Á½ÁÕÀÌ•µÁÑäÍÑ…Ñ”É•µ…¥¹ÌÕ¹•á•É¥Í•‰äÉ•…°‘…Ñ„¸(ÄÈ¸€¨©Q¡”½µ¥ÍÍ¥½¸¡…±˜¥Ì•¹™½É•¹½ÜÑ½¼°…¹ÍÝ¥Ñ¡¥¹œ¥Ð½¸™½Õ¹„‘½Õµ•¹Ñ•™•…ÑÕÉ”(€€€Ñ¡…ÐÝ…Ì¹•Ù•È‰Õ¥±Ð¸¨¨Q¡”¥¹Ù•¹Ñ¥½¸ÉÕ±”É•…‘Ì„½¹©•ÑÕÉ…±€Ñ…œ…¹‘•µ…¹‘Ì…¸(€€€…‘µ¥ÍÍ¥½¸¸¸½µ¥ÍÍ¥½¸±•…Ù•Ì¹¼Ñ…œè•Ù¥‘•¹”Ý¥Ñ ¹¼•½µ•ÑÉä¥¸™É½¹Ð½˜¥Ð±½½­Ì•á…Ñ±ä(€€€±¥­”•Ù¥‘•¹”Ý¥Ñ •½µ•ÑÉä¥¸™É½¹Ð½˜¥Ð°Ý¡¥ ¥ÌÝ¡äÁÉ½Í”Ý…ÌÑ¡”½¹±äÑ¡¥¹œ¡½±‘¥¹œ¥Ð(€€€Õ¹Ñ¥°¹½Ü¸Q¡”±…¥´Ñ¡•É•™½É”½µ•Ì™É½´Ñ¡”•¹•É…Ñ½ÈƒŠP•… €©}Á…É…µÌ¹Áå€‘•±…É•ÌÑ¡”(€€€™½É´…ÑÑÉ¥‰ÕÑ•Ì¥ÑÌ™É½µ}Á¡…Í•€…ÑÕ…±±äÉ•…‘Ì€¡=9MU5€¤°…¹•Ù•Éä…ÑÑÉ¥‰ÕÑ”½ÕÑÍ¥‘”(€€€Ñ¡…ÐÍ•ÐµÕÍÐÍ…ä½¸Ñ¡”É•½ÉÝ¡…ÐÑ¡”µ•Í ‘½•Ì¥¹ÍÑ•…è…‰Í•¹Ñ€°Í¥µÁ±¥™¥•‘€°½È(€€€É•½É‘}½¹±å€™½ÈÍ½µ•Ñ¡¥¹œÑ¡…ÐÝ…Ì¹•Ù•È„‰Õ¥±¥¹ÍÑÉÕÑ¥½¸¸Q¡”™¥ÉÍÐÑÝ¼½Ý”(€€€‘½Ì½1%	IQ%L¹µ‘€„½Ù•ÉÌé€Ñ½­•¸•á…Ñ±ä…Ì…¸¥¹Ù•¹Ñ¥½¸‘½•Ì°…¹Ñ¡”Á½ÁÕÀµ…É­Ì(€€€Ñ¡½Í”É½ÝÌÍ¼„Ù¥Í¥Ñ½ÈÍ••Ì¥Ð…¹¹½Ð½¹±äÑ¡”É•Á½Í¥Ñ½Éä¸€¨©QÝ•¹Ñäµ½¹”…ÑÑÉ¥‰ÕÑ•Ì…É½ÍÌ(€€€Í¥à‰Õ¥±‘¥¹ÌÑÕÉ¹•½ÕÐÑ¼É•… ¹¼Ù•ÉÑ•à¸¨¨5½ÍÐ…É”‰•¹¥¸µ‰ÕÐµÉ•…°Í¥µÁ±¥™¥…Ñ¥½¹ÌƒŠP„(€€€¡¥µ¹•ä½Õ¹Ð¹¼…É¡•ÑåÁ”É•…‘Ì°½¹”Ý¥¹‘½ÜÉ¡åÑ¡´½¸…±°Ñ¡É•”™É…µ”Ñ…Ù•É¹Ì°Ý…±°ÍÕÉ™…•Ì(€€€™¥á•‰äÑ¡”…É¡•ÑåÁ”É…Ñ¡•ÈÑ¡…¸Ñ¡”É•½É¸=¹”¥Ì¹½Ð¸€¨©Q¡”]½±˜A½¥¹ÐQ…Ù•É¸Ì™É…µ”(€€€•áÑ•¹Í¥½¸…¹¥ÑÌÁ…¥¹Ñ•Ý½±˜Í¥¸…É”‰½Ñ ‘½Õµ•¹Ñ•‘€…¹‰½Ñ …‰Í•¹Ð™É½´Ñ¡”µ½‘•°¨¨è(€€€Ñ¡”É•½ÉÍÁ•±±ÌÑ¡•´™É…µ•}•áÑ•¹Í¥½¹€…¹Í¥¹…•€°Ñ¡”±½}‘Ý•±±¥¹€…É¡•ÑåÁ”É•…‘Ì(€€€™É…µ•}…‘‘¥Ñ¥½¹€…¹Í¥¹€°…¹™É½µ}Á¡…Í•€™¥±±Ì…¸…‰Í•¹Ð…ÑÑÉ¥‰ÕÑ”Ý¥Ñ „‘•™…Õ±Ð°Í¼(€€€Ñ¡”ÑÝ¼‰•ÍÐµ…ÑÑ•ÍÑ•™•…ÑÕÉ•Ì½˜Ñ¡”¡½ÕÍ”Ý•É”‘É½ÁÁ•¥¸Í¥±•¹”…¹Ñ¡”Á½ÁÕÀÍ¡½Ý•Ñ¡”(€€€ÁÉ½©•ÐÌÍÑÉ½¹•ÍÐ½¹™¥‘•¹”¡¥À½Ù•È‰½Ñ ¸Q¡…Ð¥ÌÑ¡”½¹™¥‘•¹”µ½‘•°Ý½É­¥¹œ…Ì(€€€‘•Í¥¹•…¹ÍÑ¥±°µ¥Í±•…‘¥¹œ°Ý¡¥ µ…­•Ì¥ÐÑ¡”Í¡…ÉÁ•ÍÐ…ÉÕµ•¹Ð™½ÈÑ¡¥ÌÉÕ±”Ñ¡…ÐÑ¡”(€€€ÁÉ½©•Ð¡…ÌÁÉ½‘Õ•¸€¨©I•Á…¥É•€ÈÀÈØ´Àà´ÄÀ°¥¸½¹”Í±¥”Ý¥Ñ ¥ÑÌ‰…­”¨¨€¡Í•”€Äà‰•±½Ü¤¸(€€€5¥±±•ÈÌ¡½ÕÍ”Ý…ÌÑ¡”Í…µ”Í¡…Á”¥¸µ¥¹¥…ÑÕÉ”ƒŠP¥ÑÌÉ•½ÉÍ…åÌÑÝ¼¡¥µ¹•åÌ…¹(€€€±½}‘Ý•±±¥¹€‰Õ¥±Ð½¹”ƒŠP…¹¥Ì€¨©É•Á…¥É•€ÈÀÈØ´Àà´ÄÀ°¥¸½¹”Í±¥”Ý¥Ñ ¥ÑÌ‰…­”¨¨(€€€€¡Í•”€Ää‰•±½Ü¤¸]¡…Ð¥ÌÍÑ¥±°Õ¹•¹™½É•¥ÌÝ¡…Ð¹¼É•½Éµ•¹Ñ¥½¹Ì…Ð…±°ƒŠP(€€€Ñ¡”]•ÍÑ•É¸ÌÕ¹µ½‘•±±•ÍÑ…‰±”å…É¥Ì¹½Ü±…¥µ•°‰ÕÐ„±¥‰•ÉÑä¹½‰½‘ä¹½Ñ¥•Ñ…­¥¹œ(€€€É•µ…¥¹ÌÕ¹…Ñ¡…‰±”‰ä…¹äµ•¡…¹¥Í´¸(ÄÌ¸€¨©Q¡”‘½Õµ•¹Ð…¹Ñ¡”‘…Ñ„¡…‘É¥™Ñ•°…¹ÝÉ¥Ñ¥¹œÑ¡”±…¥´‘½Ý¸™½Õ¹¥Ð¸¨¨0ÄÈÍÑ¥±°(€€€É•…€‰Á½Í¥Ñ¥½¸Ñ…•¥¹™•ÉÉ•‘€ˆ™½ÈÑ¡”]…±­•Èµ••Ñ¥¹œ¡½ÕÍ”ìÑ¡”É•½ÉÝ…Ì‘½Ý¹É…‘•Ñ¼(€€€½¹©•ÑÕÉ…±€½¸€ÈÀÈØ´Àà´Àä…¹¹½Ñ¡¥¹œ…ÉÉ¥•Ñ¡”¡…¹”‰…¬¸Q¡”­•åÝ½ÉÉÕ±”Ý…Ì(€€€¥¹‘¥™™•É•¹ÐÑ¼Ñ¡”‘¥Í…É••µ•¹ÐƒŠPÑ¡”•¹ÑÉäÍ…åÌ€‰Á±…•ˆ°Ñ¡”Ù…±Õ”Ý…Ì½¹©•ÑÕÉ…°°…¹Ñ¡”(€€€µ…Ñ ¡•±™½È„É•…Í½¸Ñ¡…Ð¡…¹½Ñ¡¥¹œÑ¼‘¼Ý¥Ñ Ý¡•Ñ¡•ÈÑ¡”ÑÝ¼…É••¸•±…É¥¹œÑ¡”(€€€±…¥´™½É•Ñ¡”½µÁ…É¥Í½¸¸0ÄÈ¹½Ü…ÉÉ¥•Ì„I•Ù¥Í•±¥¹”Í…å¥¹œÍ¼°…¹Ñ¡”ÍÑ…±”Í•¹Ñ•¹”(€€€ÍÑ…åÌèÑ¡”™¥±”¥Ì…ÁÁ•¹µ½¹±ä°…¹„Í¥±•¹Ñ±ä½ÉÉ•Ñ•…‘µ¥ÍÍ¥½¸¥Ì¹½Ð½¹”¸(ÄÔ¸€¨©%aƒŠPÑ¡”ÍÑ…±•¹•ÍÌ…Ñ”•á¥ÍÑ•¥¸Ñ¡”‘½Õµ•¹Ñ…Ñ¥½¸…¹¹½Ý¡•É”•±Í”¸¨¨9QL¹µ‘€(€€€¡…ÌÍ…¥Í¥¹”Ñ¡”Í…™™½±Ñ¡…Ð€‰„ÍÑ…±”½µµ¥ÑÑ•1¥Ì„¡•¬™…¥±ÕÉ”°¹½Ð„Ý…É¹¥¹œˆ°(€€€…¹…ÍÍ•ÑÌ½µ…¹¥™•ÍÐ¹©Í½¹€¡…Ì…ÉÉ¥•…¸¥¹ÁÕÑÍ}Í¡„ÈÔÙ€Á•È…ÍÍ•ÐÍ¥¹”Ñ¡”™¥ÉÍÐ‰…­”¸(€€€9½Ñ¡¥¹œ•Ù•ÈÉ•½µÁÕÑ•¥Ð¸ÉÕ¹}ÍÑ…±•}¡•­€…Í­•½¹±äÝ¡•Ñ¡•È•… 1…ÁÁ•…É•¥¸Ñ¡”(€€€µ…¹¥™•ÍÐ°Í¼„É•½É½Õ±‰”•‘¥Ñ•¥¹Ñ¼„‘¥™™•É•¹Ð‰Õ¥±‘¥¹œ…¹Ñ¡”Ñ½Ý¸Ý½Õ±­••À(€€€É•¹‘•É¥¹œÑ¡”½±½¹”Ý¥Ñ Ñ¡”…Ñ”É••¸ƒŠPÑ¡”•á…Ð™…¥±ÕÉ”µ½‘”Ñ¡”LÔÉ•Á…¥ÉÌ…É”ÅÕ•Õ•(€€€™½È°Õ¹Õ…É‘•¸Q¡”¡•¬¹½ÜÉ•½µÁÕÑ•Ì•Ù•Éä½µµ¥ÑÑ•…ÍÍ•ÐÌ¥¹ÁÕÑÌ…¹™…¥±Ì½¸(€€€‘¥Í…É••µ•¹Ð°…¹Ñ¡”É•¥Á”±¥Ù•ÌÝ¥Ñ Ñ¡”•¹•É…Ñ½ÉÌ€¡•¹•É…Ñ½ÉÌ½µ•Í¡}¥¹ÁÕÑÌ¹Áå€°(€€€Ñ•ÉÉ…¥¹}•¸¹Ñ•ÉÉ…¥¹}¥¹ÁÕÑÍ}Í¡…€¤Í¼Ñ¡”Í¥‘”Ñ¡…ÐÝÉ¥Ñ•ÌÑ¡”¡…Í …¹Ñ¡”Í¥‘”Ñ¡…Ð¡•­Ì(€€€¥Ð…¹¹½Ð‘É¥™Ð¸(€€€€¨©MÝ¥Ñ¡¥¹œ¥Ð½¸É•ÅÕ¥É•É•‘•™¥¹¥¹œÑ¡”¡…Í °‰•…ÕÍ”Ñ¡”½±½¹”Ý…ÌÕ¹ÕÍ…‰±”¸¨¨%Ð¡…Í¡•(€€€Ñ¡”Ý¡½±”Á¡…Í”É•½ÉÁ±ÕÌ•Ù•Éä€¹Áå€Õ¹‘•È•¹•É…Ñ½ÉÌ½€°Ý¡¥ µ•…¹Ð…±°Í¥à‰Õ¥±‘¥¹Ì(€€€É•…ÍÑ…±”™½ÈÉ•…Í½¹ÌÑ¡…Ð…¹¹½Ðµ½Ù”„Ù•ÉÑ•àèÑ¡”•½µ•ÑÉäé€‘•±…É…Ñ¥½¹Ì…‘‘•½¸(€€€€ÈÀÈØ´Àà´ÄÀ°…¹„=9MU5€½¹ÍÑ…¹Ð…‘‘•Ñ¼½¹”…É¡•ÑåÁ”ÌÁ…É…µ•Ñ•Èµ½‘Õ±”¥¹Ù…±¥‘…Ñ¥¹œ(€€€Ñ¡”½Ñ¡•ÉÌœ‰Õ¥±‘¥¹Ì¸¡…Í Ñ¡…ÐÉ¥•ÌÍÑ…±”½Ù•È„É•ÝÉ¥ÑÑ•¸¹½Ñ”•ÑÌ‘¥Í‰•±¥•Ù•°…¹„(€€€‘¥Í‰•±¥•Ù•…Ñ”¥ÌÝ½ÉÍ”Ñ¡…¸¹½¹”¸%Ð¹½Ü¡…Í¡•ÌÝ¡…ÐÑ¡”‰Õ¥±‘•È…¸Í•”ƒŠPÑ¡”€©É•Í½±Ù•¨(€€€Á…É…µ•Ñ•ÉÌ°Ñ¡”±…ÍÌÌ‘•É¥Ù•ÁÉ½Á•ÉÑ¥•Ì°Ñ¡”½¹™¥‘•¹”™±½…ÑÌ°…¹Ñ¡”‰åÑ•Ì½˜Ñ¡”(€€€‰Õ¥±‘•È°½µµ½¸½€°‰Õ¥±¹Áå€…¹Ñ¡”	±•¹‘•ÈÁ¥¸¸A…É…µ•Ñ•Èµµ½‘Õ±”‰åÑ•Ì…É”‘•±¥‰•É…Ñ•±ä(€€€½ÕÐèÑ¡…Ðµ½‘Õ±”ÌÝ¡½±”•™™•Ð½¸Ñ¡”µ•Í ¥ÌÑ¡”½‰©•Ð¥ÐÉ•ÑÕÉ¹Ì°…¹Ñ¡”½‰©•Ð¥Ì(€€€¡…Í¡•¥¸µ½É”‘•Ñ…¥°Ñ¡…¸¥ÑÌÍ½ÕÉ”Ý½Õ±¥Ù”¸(€€€€¨©Q¡”•¥¡Ð½µµ¥ÑÑ•¡…Í¡•ÌÝ•É”É”µÍÑ…µÁ•Ý¥Ñ¡½ÕÐ„‰…­”°…¹Ñ¡…Ð¥Ì„±…¥´°Í¼¡•É”¥Ì(€€€Ñ¡”ÁÉ½½˜¸¨¨U¹‘•ÈÑ¡”¹•ÜÉ•¥Á”°•Ù•Éä¥¹ÁÕÐÑ¼…±°Í¥à‰Õ¥±‘¥¹Ì¥Ì‰åÑ”µ¥‘•¹Ñ¥…°Ñ¼Ý¡…Ð(€€€¥ÐÝ…Ì…ÐÑ¡”±…ÍÐ‰…­”€¡ŒÌäÔÍÉ€¤ƒŠP¡•­•‰äÉÕ¹¹¥¹œÑ¡”¹•ÜÉ•¥Á”¥¹Í¥‘”„Ý½É­ÑÉ•”½˜(€€€Ñ¡…Ð½µµ¥Ð…¹‘¥™™¥¹œÑ¡”¥¹ÁÕÐ‘½Õµ•¹ÑÌ°¹½Ð‰ä¥¹ÍÁ•Ñ¥½¸¸Q¡”Í¥¹±”‘¥™™•É•¹”¥Ì(€€€‰Õ¥±¹Áå€°Ý¡½Í”½¹±ä¡…¹”¥¸Ñ¡¥ÌÍ±¥”¥Ì‘•±•…Ñ¥¹œÑ¡”¡…Í Ñ¼Ñ¡”¹•Üµ½‘Õ±”¸Q•ÉÉ…¥¸(€€€É”µÍÑ…µÁ•™½ÈÑ¡”Í…µ”É•…Í½¸èÑ•ÉÉ…¥¹}•¸¹Áå€¡…Í¡•Ì¥ÑÌ½Ý¸‰åÑ•Ì…¹…¥¹•…¸•áÑÉ…Ñ•(€€€™Õ¹Ñ¥½¸¸9¼µ•Í Ý…ÌÉ••¹•É…Ñ•…¹¹½¹”¹••‘•Ñ¼‰”¸µ…¹¥™•ÍÐ¹©Í½¹€¹½ÜÉ•½É‘Ì(€€€¥¹ÁÕÑÍ}Í¡•µ•€°…¹Ñ¡”…Ñ”É•™ÕÍ•Ì„µ…¹¥™•ÍÐÍÑ…µÁ•Õ¹‘•È„Í¡•µ”¥Ð‘½•Ì¹½Ð½µÁÕÑ”(€€€É…Ñ¡•ÈÑ¡…¸½µÁ…É¥¹œÑÝ¼¡…Í¡•ÌÑ¡…Ðµ•…¸‘¥™™•É•¹ÐÑ¡¥¹Ì¸(€€€]¡…ÐÑ¡¥ÌÍÑ¥±°‘½•Ì¹½Ð…Ñ ¥ÌÍÑ…Ñ•¥¸µ•Í¡}¥¹ÁÕÑÌ¹Áå€è¥Ð½µÁ…É•Ì¥¹ÁÕÑÌ°¹½Ð½ÕÑÁÕÐ¸(€€€å±•Ì<¥Ì¹½Ð‰¥ÐµÉ•ÁÉ½‘Õ¥‰±”…É½ÍÌ¡…É‘Ý…É”°Ý¡¥ ¥ÌÝ¡ä™É•Í¡¹•ÍÌ¥Ì‘•™¥¹•½¸¥¹ÁÕÑÌ(€€€…Ð…±°ƒŠP„¡…¹µ•‘¥Ñ•1‰•¡¥¹…¸Õ¹Ñ½Õ¡•É•½ÉÁ…ÍÍ•Ì°…¹¹½Ñ¡¥¹œ¡•É”…¸Í•”¥Ð¸(ÄØ¸€¨©Q¡”¹¥¡Ñ±ä‰…­”ÁÕÍ¡•Ì¥ÑÌ‰É…¹ …¹…¹¹½Ð½Á•¸¥ÑÌAH¸¨¨¡¥…¼´Ñµ‰…­”¹åµ±€•¹‘Ì(€€€‰äÉ•…Ñ¥¹œ„ÁÕ±°É•ÅÕ•ÍÐ…¹Ñ¡…ÐÍÑ•À¡…Ì‰••¸™…¥±¥¹œ½¸„É•Á½Í¥Ñ½ÉäÍ•ÑÑ¥¹œƒŠP(€€€€‰¥Ñ!ÕˆÑ¥½¹Ì¥Ì¹½ÐÁ•Éµ¥ÑÑ•Ñ¼É•…Ñ”½È…ÁÁÉ½Ù”ÁÕ±°É•ÅÕ•ÍÑÌˆƒŠPÍ¼•Ù•Éä‰…­”Í¥¹”(€€€Ñ¡”Ý½É­™±½ÜÝ…ÌÝÉ¥ÑÑ•¸¡…Ì±•™Ð¥ÑÌ•½µ•ÑÉä½¸…¸½ÉÁ¡…¸ÍÑ•Ý…É½‰…­”´©€‰É…¹ Ñ¡…Ð(€€€¹½Ñ¡¥¹œµ•É•Ì¸¥¡ÐÍÕ ‰É…¹¡•Ì•á¥ÍÐ¸Q¡¥ÌÍ±¥”Ý½É­•…É½Õ¹¥Ð‰ä™•Ñ¡¥¹œÑ¡”‰…­”(€€€‰É…¹ …¹™…ÍÐµ™½ÉÝ…É‘¥¹œ½¹Ñ¼¥Ð°Ý¡¥ ¥Ì™¥¹”™½È…¸…•¹ÐÑ¡…Ð¥ÌÝ…Ñ¡¥¹œ°…¹¹¼ÕÍ”(€€€…Ð…±°™½ÈÑ¡”¹¥¡Ñ±ä¸Q¡”™¥à¥Ì½¹”¡•­‰½à¥¸Ñ¡”É•Á½Í¥Ñ½ÉäÌÑ¥½¹ÌÍ•ÑÑ¥¹Ì°½È„(€€€AP½¸Ñ¡…ÐÍÑ•ÀìÑ¡”Ý½É­™±½Ü±¥Ù•Ì½ÕÑÍ¥‘”¡¥…¼¼Ñ½€…¹¥ÌÑ¡•É•™½É”½ÕÑÍ¥‘”Ñ¡¥Ì(€€€±…¹”ÌÍ½Á”Ñ¼•‘¥Ð°Í¼¥Ð¥ÌÉ•½É‘•¡•É”É…Ñ¡•ÈÑ¡…¸™¥á•¸(ÄÜ¸€¨©É…µ”É…Ñ”™¥ÕÉ•Ì…É”µ•…¹¥¹±•ÍÌ¡•É”¸¨¨€ËŠLä™ÁÌÕ¹‘•È¡•…‘±•ÍÌMÝ¥™ÑM¡…‘•È¥ÌÍ½™ÑÝ…É”(€€€É…ÍÑ•É¥Í…Ñ¥½¸°¹½Ð„ATµ•…ÍÕÉ•µ•¹Ð¸É…Ü…±±Ì€ ÄÈ¤…¹ÑÉ¥…¹±•Ì€ Ä°ÀÀØ¤…É”É•…°¸((Äà¸€¨©%aƒŠPÑ¡”]½±˜A½¥¹ÐQ…Ù•É¸¡…Ì¥ÑÌ™É…µ”¡…±˜…¹¥ÑÌÝ½±˜Í¥¸¸¨¨Q¡”‘•™•ÐÑ¡”(€€€½µ¥ÍÍ¥½¸…Ñ”™½Õ¹½¸€ÈÀÈØ´Àà´ÄÀ¥ÌÉ•Á…¥É•Ñ¡”Í…µ”‘…ä°É•½É…¹µ•Í ¥¸½¹”½µµ¥Ðè(€€€™É…µ•}•áÑ•¹Í¥½¹€ƒŠH™É…µ•}…‘‘¥Ñ¥½¹€°Í¥¹…•€ƒŠHÍ¥¹€°Ñ¡”ÑÝ¼¹…µ•Ì±½}‘Ý•±±¥¹€(€€€…ÑÕ…±±äÉ•…‘Ì¸Q¡”‰Õ¥±‘¥¹œÑ¡…Ð¹…µ•]½±˜A½¥¹Ð¹½Ü¡…Ì„‰½…É¡…¹¥¹œ½ÕÑÍ¥‘”¥Ð¸(€€€€¨©Q¡”É•¹…µ”Ý…ÌÑ¡”Íµ…±±•È¡…±˜¸¨¨™É…µ•}…‘‘¥Ñ¥½¸èÑÉÕ•€…¹¹½Ñ¡¥¹œ•±Í”Ý½Õ±¡…Ù”±•Ð(€€€Ñ¡”…É¡•ÑåÁ”Á¥¬Ñ¡”‰…äÌÍ¥‘”°Ý¥‘Ñ °‘•ÁÑ …¹ÍÑ½É•ä½Õ¹Ð™É½´¥ÑÌ‘•™…Õ±ÑÌƒŠP„(€€€ÑÝ¼µÍÑ½É•ä™É…µ”‰±½¬…É½ÍÌÑ¡”É¥Ù•È™É½¹Ð½˜„Ñ…Ù•É¸Ñ¡”Í½ÕÉ•Ì‘•ÍÉ¥‰”…Ì±½ÜƒŠPÍ¼„(€€€‘½Õµ•¹Ñ•™•…ÑÕÉ”Ý½Õ±¡…Ù”…ÉÉ¥Ù•…Ð…¸¥¹Ù•¹Ñ•Í¥é”Ý¥Ñ ¹½Ñ¡¥¹œ…‘µ¥ÑÑ¥¹œ¥Ð°Ý¡¥ ¥Ì(€€€Ñ¡”Í…µ”™…¥±ÕÉ”Ñ¡¥ÌÉ•Á…¥È•á¥ÍÑÌÑ¼•¹°½¹”±•Ù•°‘½Ý¸¸Q¡”É•½ÉÑ¡•É•™½É”ÍÑ…Ñ•Ì…±°(€€€™½ÕÈèÍ¥‘”•¹‘€…¹Ý¥‘Ñ €Ð´½˜Ñ¡”€ÄÈ´™É½¹Ñ…”…¹‘•ÁÑ €Ü´…±°€¨©½¹©•ÑÕÉ…°¨¨°ÍÑ½É•ä(€€€½Õ¹Ð€Ä€¨©¥¹™•ÉÉ•¨¨‰äÑ¡”Í…µ”…ÉÕµ•¹ÐÑ¡”ÍÑ½É•ä½Õ¹Ð…‰½Ù”¥ÐÕÍ•Ì¸0ÈÐ…‘µ¥ÑÌÑ¡”Ñ¡É•”(€€€½¹©•ÑÕÉ…°½¹•Ìì0ÈÀµ½Ù•ÌÑ¼I•Í½±Ù•…ÉÉå¥¹œ‰½Ñ ÍÁ•±±¥¹ÌÑ¡…Ð¹¼±½¹•ÈÉ•Í½±Ù”°(€€€‰•…ÕÍ”„Í¥±•¹Ñ±ä½ÉÉ•Ñ•…‘µ¥ÍÍ¥½¸¥Ì¹½Ð½¹”¸(€€€€¨©]¡…ÐÑ¡”Í¥¸¥Ìè„‰±…¹¬‰½…É¸¨¨Q¡”‰É…­•Ð°Ñ¡”…É´°Ñ¡”‰½…É…¹¥ÑÌÁÉ½Á½ÉÑ¥½¹Ì…É”(€€€Ñ¡”…É¡•ÑåÁ”Ì¥¹Ù•¹Ñ¥½¸°…¹Ñ¡”Á…¥¹Ñ•Ý½±˜¥Ì¹½Ð‘É…Ý¸ƒŠP¹¼‘•ÍÉ¥ÁÑ¥½¸½˜¥ÐÍÕÉÙ¥Ù•Ì°(€€€…¹„Ý½±˜Á…¥¹Ñ•™É½´¥µ…¥¹…Ñ¥½¸Ý½Õ±‰”Ñ¡”µ½ÍÐ½¹ÍÁ¥Õ½ÕÌ¥¹Ù•¹Ñ¥½¸¥¸Ñ¡”Í•¹”½¸(€€€Ñ¡”½¹”½‰©•Ð•Ù•ÉäÙ¥Í¥Ñ½ÈÝ¥±°Ý…±¬ÕÀÑ¼¸0ÈÔÍ…åÌÍ¼¸(€€€€¨©QÝ¼±¥µ¥ÑÌÝ½ÉÑ ÍÑ…Ñ¥¹œ¸¨¨Q¡”½¹™¥‘•¹”Ñ¥¹Ð½¸Ñ¡”‰…ä™½±±½ÝÌÝ¡…ÐÑ¡”‰…ä%L(€€€€¡‘½Õµ•¹Ñ•Ñ¡…Ð¥Ð•á¥ÍÑ•°¥¹™•ÉÉ•Ñ¡…Ð¥ÐÝ…Ì±½Ü¤°¹½Ð¥ÑÌÕ¹­¹½Ý¸Í¥é”ƒŠPÑ¡”ÉÕ±”Í•Ð(€€€™½ÈÑ¡”M…Õ…¹…Í °Ý¡¥ µ•…¹ÌÑ¡”Ñ¥¹Ð…±½¹”Ý¥±°¹½ÐÑ•±°„Ù¥Í¥Ñ½ÈÑ¡”Ý¥‘Ñ ¥Ì„Õ•ÍÌ…¹(€€€½¹±äÑ¡”Á½ÁÕÀÌ±¥‰•ÉÑä¡¥ÀÝ¥±°¸¹Ñ¡”Ý¡½±”É•Á…¥ÈÉ•ÍÑÌ½¸„™½½ÑÁÉ¥¹ÐÑ¡…Ð¥Ì¥ÑÍ•±˜„(€€€Á±…•¡½±‘•Èè€Ð´½˜…¸¥¹Ù•¹Ñ•€ÄÈ´¥Ì„™É…Ñ¥½¸½˜„Õ•ÍÌ¸((Ää¸€¨©%aƒŠPÑ¡”¡¥µ¹•ä½Õ¹Ð¥Ì„¹Õµ‰•ÈÑ¡”…É¡•ÑåÁ•ÌÉ•…°…¹Ñ¡”Ñ¡¥Éµ¥ÍÍÁ•±±¥¹œ¥Ì¹½Ü(€€€„Ñ•ÍÐ¸¨¨Ù•ÉäÉ•½ÉÍÑ…Ñ•Ì¡¥µ¹•åÍ€ì¹•¥Ñ¡•È…É¡•ÑåÁ”É•…Ñ¡”Ù…±Õ”¸™É…µ•}Ñ…Ù•É¹€(€€€‰Õ¥±ÐÑÝ¼ÍÑ…­ÌÝ¡…Ñ•Ù•ÈÑ¡”É•½ÉÍ…¥…¹±½}‘Ý•±±¥¹€‰Õ¥±Ð½¹”°Í¼M…µÕ•°5¥±±•ÈÌ(€€€¡½ÕÍ”ƒŠPÉ•½ÉÑÝ¼°µ½‘•°½¹”ƒŠPÍÑ½½„ÍÑ…¬Í¡½ÉÐ™É½´¥ÑÌ™¥ÉÍÐ‰…­”¸	½Ñ …É¡•ÑåÁ•ÌÑ…­”(€€€Ñ¡”½Õ¹Ð¹½Ü¸Q¡”Á…¥È½¸„™É…µ”‰±½¬­••ÁÌ¥ÑÌ•á…ÐÁ½Í¥Ñ¥½¹Ì€ À¸ÈÈ…¹€À¸Üà½˜Ñ¡”(€€€™É½¹Ñ…”°É•…½™˜Ñ¡”M…Õ…¹…Í ‘•Á¥Ñ¥½¹Ì¤Í¼Ñ¡…ÐÁ…É…µ•Ñ•É¥Í¥¹œÑ¡”¹Õµ‰•È‘¥¹½ÐÅÕ¥•Ñ±ä(€€€µ½Ù”„‰Õ¥±‘¥¹œÝ¡½Í”½Õ¹ÐÝ…Ì…±É•…‘äÉ¥¡Ðì„±½œ‰Õ¥±‘¥¹œÌÍ•½¹ÍÑ…¬½•Ì½¸Ñ¡”™É…µ”(€€€…‘‘¥Ñ¥½¸É…Ñ¡•ÈÑ¡…¸Ñ¡”™…È…‰±”°‰•…ÕÍ”€©Ñ¡”É•½ÉÌ½Ý¸É•…Í½¸¨™½È½Õ¹Ñ¥¹œÑÝ¼¥Ì€‰„(€€€ÍÑ…¬¥¸•… •±•µ•¹Ðˆ°…¹¡½¹½ÕÉ¥¹œÑ¡”¹Õµ‰•ÈÝ¡¥±”½¹ÑÉ…‘¥Ñ¥¹œ¥ÑÌ…ÉÕµ•¹Ð¥Ì¹½Ð(€€€¡½¹½ÕÉ¥¹œ¥Ð¸0ÈÄµ½Ù•ÌÑ¼I•Í½±Ù•…¹Ñ¡”Í¥àÉ•½É‘Ì‘É½ÀÑ¡”•½µ•ÑÉäè€Í¥µÁ±¥™¥•€(€€€‘•±…É…Ñ¥½¸Ñ¡…ÐÝ…ÌÑÉÕ”Õ¹Ñ¥°Ñ¡¥Ì±…¹‘•¸(€€€€¨©Q¡”±½}‘Ý•±±¥¹€¡…±˜Ý…ÌÑ¡”]½±˜A½¥¹Ð‘•™•Ð„Ñ¡¥ÉÑ¥µ”¸¨¨Q¡”Á…É…µ•Ñ•ÈÝ…Ì(€€€¡¥µ¹•å€°„‰½½±•…¸ì¹¼É•½É¥¸Ñ¡¥Ì‘…Ñ…Í•Ð¡…Ì•Ù•È½¹Ñ…¥¹•Ñ¡…ÐÝ½É°Í¼™É½µ}Á¡…Í•€(€€€Ñ½½¬¥ÑÌ‘•™…Õ±Ð½¸•Ù•Éä±½œ‰Õ¥±‘¥¹œ…¹¹½Ñ¡¥¹œ½µÁ±…¥¹•¸Q¡É•”½ÕÉÉ•¹•Ì½˜½¹”(€€€™…¥±ÕÉ”¥Ì„Á…ÑÑ•É¸É…Ñ¡•ÈÑ¡…¸‰…±Õ¬°Í¼¥Ð¹½Ü¡…Ì„¡•¬¥¹ÍÑ•…½˜…¹½Ñ¡•È(€€€‘¥Í½Ù•É•ÈèÑ•ÍÑ}½¹ÍÕµ•‘}…ÑÑÉ¥‰ÕÑ•Í}…ÑÕ…±±å}É•…¡}Ñ¡•}Á…É…µ•Ñ•ÉÍ€Á•ÉÑÕÉ‰Ì•Ù•ÉäÍÑ…Ñ•(€€€Ù…±Õ”¥ÑÌ…É¡•ÑåÁ”‘•±…É•Ì¥Ð=9MU5L…¹É•ÅÕ¥É•ÌÑ¡”É•Í½±Ù•Á…É…µ•Ñ•ÉÌÑ¼¡…¹”ƒŠP€ÔÔ(€€€…ÑÑÉ¥‰ÕÑ•Ì•á•É¥Í•…É½ÍÌÑ¡”Í¥àÉ•½É‘Ì°Ý¥Ñ „A…É…µÉÉ½É€½Õ¹Ñ•…ÌÉ•…°Í¥¹”(€€€É•™ÕÍ¥¹œ„Ù…±Õ”¥ÌÑ¡”±½Õ‘•ÍÐÁ½ÍÍ¥‰±”ÁÉ½½˜½˜¡…Ù¥¹œÍ••¸¥Ð¸Q¡”½ÁÁ½Í¥Ñ”‘¥É•Ñ¥½¸€¡…¸(€€€…ÑÑÉ¥‰ÕÑ”ÍÑ…Ñ•…¹€©¹½Ð¨‘•±…É•¤Ý…Ì…±É•…‘äÑ¡”½µ¥ÍÍ¥½¸…Ñ”ìÑ¡¥Ì±½Í•ÌÑ¡”‘¥É•Ñ¥½¸(€€€Ý¡•É”Ñ¡”‘•±…É…Ñ¥½¸¥ÑÍ•±˜¥ÌÑ¡”™…±Í”½¹”°Ý¡¥ ¥ÌÑ¡”Ý½ÉÍ”½˜Ñ¡”ÑÝ¼°‰•…ÕÍ”…¸(€€€…ÑÑÉ¥‰ÕÑ”¥¹Í¥‘”=9MU5¥Ì•áÕÍ•™É½´…‘µ¥ÑÑ¥¹œ…¹åÑ¡¥¹œ¸(€€€€¨©]¡…Ð¥Ð‘½•Ì¹½Ð™¥à°…¹Ñ¡…Ð¥ÌÑ¡”µ½É”¥¹Ñ•É•ÍÑ¥¹œ¡…±˜¸¨¨Q¡”½Õ¹Ð¥Ì¥¹™•ÉÉ•‘€½¸(€€€•Ù•Éä‰Õ¥±‘¥¹œ…¹¹½Ñ¡¥¹œ•±Í”…‰½ÕÐ„ÍÑ…¬¥ÌÉ•½É‘•…¹åÝ¡•É”ƒŠP¹½Ð½¹”Í½ÕÉ”‘•ÍÉ¥‰•Ì(€€€„¡¥µ¹•ä½¸…¹ä½˜Ñ¡•Í”Í¥à¸A½Í¥Ñ¥½¸°¥ÉÑ °¡•¥¡Ð…‰½Ù”Ñ¡”É¥‘”…¹µ…Ñ•É¥…°…É”…±°(€€€Ñ¡”…É¡•ÑåÁ”Ì°Í¼Ñ¡”½¹™¥‘•¹”¡¥À„Ù¥Í¥Ñ½ÈÉ•…‘Ì½¸Ñ¡…ÐÉ½ÜÉ…‘•Ì½¹±ä€©¡½Üµ…¹ä¨¸(€€€0ÈØ¥Ì¹•Ü…¹¥ÌÑ¡”½¹±äÁ±…”Ñ¡…Ð‘¥ÍÑ¥¹Ñ¥½¸¥Ì±•¥‰±”¸((ÈÀ¸€¨©%aƒŠP5¥±±•ÈÌ™É…µ”É…¹”¥Ì‘¥µ•¹Í¥½¹•‰äÑ¡”É•½É°…¹™¥á¥¹œ¥Ð™½Õ¹Ñ¡”ÍÑ½É•åÌ(€€€½¸Ñ¡”ÝÉ½¹œ¡…±˜½˜Ñ¡”¡½ÕÍ”¸¨¨Q¡”ÅÕ•Õ•‘•™•ÐÝ…Ì0ÈÐÌ½¹”‰Õ¥±‘¥¹œ½Ù•Èè(€€€™É…µ•}…‘‘¥Ñ¥½¹€¥Ì‘½Õµ•¹Ñ•‘€½¸µ¥±±•É}¡½ÕÍ•€ƒŠP€‰„ÑÝ¼µÍÑ½Éä¡½ÕÍ”…‘‘•Ñ¼Ñ¡”…‰¥¸°(€€€™É½¹Ñ¥¹œÑ¡”É¥Ù•ÈˆƒŠP…¹Ñ¡”É•½ÉÍÑ…Ñ•¹¼Í¥‘”°¹¼Ý¥‘Ñ °¹¼‘•ÁÑ …¹¹¼ÍÑ½É•ä½Õ¹Ð°(€€€Í¼±½}‘Ý•±±¥¹€ÍÕÁÁ±¥•…±°™½ÕÈ™É½´¥ÑÌ‘•™…Õ±ÑÌ¸I•Á…¥É•€ÈÀÈØ´Àà´ÄÀ°É•½É…¹µ•Í ¥¸(€€€½¹”½µµ¥Ð¸QÝ¼½˜Ñ¡”™½ÕÈÑÕÉ¸½ÕÐÑ¼‰”€¨©…ÑÑ•ÍÑ•¨¨°Ý¡¥ ¥ÌÑ¡”‘¥™™•É•¹”‰•ÑÝ••¸Ñ¡¥Ì(€€€‰Õ¥±‘¥¹œ…¹Ñ¡”]½±˜A½¥¹Ð‰…äèÑ¡”Í¥‘”¥Ì™É½¹Ñ€‰•…ÕÍ”Ñ¡”Í½ÕÉ”Í…åÌ€©™É½¹Ñ¥¹œÑ¡”(€€€É¥Ù•È¨°…¹Ñ¡”É…¹”¥ÌÑÝ¼ÍÑ½É•åÌ‰•…ÕÍ”Ñ¡”Í½ÕÉ”Í…åÌ€©„ÑÝ¼µÍÑ½Éä¡½ÕÍ”¨¸=¹±äÑ¡”(€€€Ý¥‘Ñ …¹‘•ÁÑ …É”¥¹Ù•¹Ñ•°…¹Ñ¡•ä…É”É•…½™˜Ñ¡¥ÌÉ•½ÉÌ½Ý¸™½½ÑÁÉ¥¹ÐÁ½±å½¸ƒŠPÑ¡”(€€€É¥Ù•Èµ™É½¹Ñ¥¹œ±¥µˆ¥Ì€äƒ\€Ø´ƒŠPÉ…Ñ¡•ÈÑ¡…¸Á¥­•…™É•Í °Í¼Ñ¡”µ•Í …É••ÌÝ¥Ñ Ñ¡”Á±…¸(€€€Ñ¡”É•½É…±É•…‘ä‘É…ÝÌ¸0ÈÜ…‘µ¥ÑÌÑ¡•´ìÑ¡•ä¥¹¡•É¥ÐÑ¡”Á½±å½¸Ì¥¹Ù•¹Ñ¥½¸°Ý¡¥ ¥Ì(€€€Ñ½Ñ…°¸(€€€€¨©Q¡”ÍÑ½É•ä½Õ¹ÐÝ…ÌÑ¡”É•…°‘•™•Ð…¹¥ÐÝ…Ì¹½Ð½¸Ñ¡”ÅÕ•Õ”¸¨¨ÍÑ½É¥•Í€Ý…Ì€È°(€€€‘½Õµ•¹Ñ•‘€°Ý¥Ñ ¥ÑÌ½Ý¸¹½Ñ”Í…å¥¹œ¥¸…Ìµ…¹äÝ½É‘ÌÑ¡…ÐÑ¡”ÑÝ¼ÍÑ½É•åÌ‘•ÍÉ¥‰•Ñ¡”(€€€É¥Ù•Èµ™É½¹Ñ¥¹œÉ…¹”…¹¹½ÐÑ¡”Ý¡½±”‰Õ¥±‘¥¹œƒŠP‰ÕÐ±½}‘Ý•±±¥¹€É•…‘ÌÍÑ½É¥•Í€…ÌÑ¡”(€€€1==IÌ½Õ¹Ð¸M¼Ñ¡”‘½Õµ•¹Ñ•±…¥´Ý…ÌÍÁ•¹Ð½¸Ñ¡”…‰¥¸°Ñ¡”É…¹”™•±°‰…¬Ñ¼„(€€€€Ð¸Ü´‘•™…Õ±Ð°…¹Ñ¡”µ½‘•°ÍÑ½½„ÑÝ¼µÍÑ½É•ä±½œ…‰¥¸€¨©‰•¡¥¹„Í¡½ÉÑ•È™É…µ”‰±½¬¨¨è(€€€Ñ¡”½µÁ½Í¥Ñ¥½¸¥¹Ù•ÉÑ•°Í••¸™É½´Ñ¡”•á…ÐÍÁ½Ð…É½ÍÌÑ¡”Ý…Ñ•ÈÝ¡•É”Ñ¡”€ÄàÌÌ‘•ÍÉ¥ÁÑ¥½¸(€€€½˜¥ÐÝ…ÌÝÉ¥ÑÑ•¸¸Q¡…Ð¥ÌÑ¡”™É…µ•}•áÑ•¹Í¥½¹€½Í¥¹…•€½¡¥µ¹•å€™…¥±ÕÉ”¥¸¥ÑÌÍÕ‰Ñ±•È(€€€™½É´ƒŠP¹½Ð„¹…µ”Ñ¡”…É¡•ÑåÁ”½Õ±¹½Ð™¥¹°‰ÕÐ„¹…µ”¥Ð™½Õ¹…¹É•……Ì‰•¥¹œ…‰½ÕÐ„(€€€‘¥™™•É•¹Ð¡…±˜½˜Ñ¡”‰Õ¥±‘¥¹œ¸9¼ÍÁ•±±¥¹œ¡•¬…Ñ¡•ÌÑ¡…Ð°…¹¹•¥Ñ¡•È‘½•Ì(€€€Ñ•ÍÑ}½¹ÍÕµ•‘}…ÑÑÉ¥‰ÕÑ•Í}…ÑÕ…±±å}É•…¡}Ñ¡•}Á…É…µ•Ñ•ÉÍ€°Ý¡¥ ÁÉ½Ù•Ì½¹±äÑ¡…Ð„Ù…±Õ”µ½Ù•Ì(€€€€©Í½µ•Ñ¡¥¹œ¨¸Q¡”ÑÝ¼µÍÑ½É•ä±…¥´¹½ÜÍ¥ÑÌ½¸™É…µ•}…‘‘¥Ñ¥½¹}ÍÑ½É¥•Í€°Ñ¡”…‰¥¸ÌÍÑ½É¥•Í€(€€€¥Ì€Ä¥¹™•ÉÉ•‘€€¡¹¼Í½ÕÉ”¥Ù•ÌÑ¡”±½œÁ…ÉÐ„¡•¥¡ÐìÑ¡”€ÄàÌÌÙ¥•ÜÌ€‰„ÑÝ¼µÍÑ½Éä‰Õ¥±‘¥¹œ(€€€…¹…‘©½¥¹¥¹œ±½œ…‰¥¸ˆ½¹±äÉ•…‘Ì…Ì„½¹ÑÉ…ÍÐ¥˜Ñ¡”…‰¥¸Ý…Ì±½Ý•È¤°Ñ¡”€Ô¸È´µ½Ù•ÌÑ¼(€€€™É…µ•}…‘‘¥Ñ¥½¹}¡•¥¡Ñ}µ€°…¹Ý…±±}¡•¥¡Ñ}µ€‰•½µ•ÌÑ¡”…‰¥¸Ì€È¸Ø´ƒŠPÑ¡”¹Õµ‰•ÈÑ¡¥Ì(€€€É•½É¡…Ì¹…µ•™½È¥ÐÍ¥¹”¥ÐÝ…ÌÝÉ¥ÑÑ•¸°Í¥ÑÑ¥¹œ¥¸„¹½Ñ”É…Ñ¡•ÈÑ¡…¸¥¸„™¥•±¸(€€€0ÄÌµ½Ù•ÌÑ¼I•Í½±Ù•è¹•¥Ñ¡•È½µÁ½Í¥Ñ”‰Õ¥±‘¥¹œ¥Ì„Í¥¹±”•áÑÉÕÍ¥½¸…¹äµ½É”¸(€€€€¨©]¡…Ð‘¥¹½Ð•Ð‰•ÑÑ•È¸¨¨Q¡”…É¡•ÑåÁ”µ…ÍÍ•ÌÑ¡”™½½ÑÁÉ¥¹ÐÌ‰½Õ¹‘¥¹œ‰½à°Í¼Ñ¡”±½œ(€€€½É”½µ•Ì½ÕÐÑ¡”™Õ±°€ä´Ý¥‘”É…Ñ¡•ÈÑ¡…¸Ñ¡”Á½±å½¸Ì€Ø´…¹Ñ¡”€Ìƒ\€Ô´É”µ•¹ÑÉ…¹Ð(€€€½É¹•È‰•¡¥¹Ñ¡”É…¹”¥Ì™¥±±•¥¸¸MÑ…Ñ¥¹œÑ¡”É…¹”Ì½Ý¸¹Õµ‰•ÉÌ¥ÌÝ¡…Ðµ…­•ÌÑ¡…Ð(€€€Ù¥Í¥‰±”ƒŠPÑ¡”‘•™…Õ±ÑÌÁÉ½‘Õ•…¸¥¹Ù•ÉÑ•µPµ…Ñ¡¥¹œ¹•¥Ñ¡•ÈÑ¡”Á½±å½¸¹½ÈÑ¡”Í½ÕÉ•ÌƒŠP(€€€…¹0ÈÜÉ•½É‘Ì¥Ð¸¹Ñ¡”Ý¡½±”É•Á…¥ÈÍÑ¥±°É•ÍÑÌ½¸„Á±…•¡½±‘•Èè€äƒ\€Ø½˜…¸¥¹Ù•¹Ñ•(€€€€äƒ\€ÄÄ¸((ÈÄ¸€¨©Q¡”™¥ÉÍÐ‰É¥‘”°…¹Ñ¡”™¥ÉÍÐÉ•½ÉÝ¡½Í”Í¥é”¥Ì¹½Ð„Á±…•¡½±‘•È¸¨¨Q¡”9½ÉÑ 	É…¹ (€€€É½ÍÍ¥¹œ…Ð-¥¹é¥”MÑÉ••ÐƒŠP¡¥…¼Ì™¥ÉÍÐ‰É¥‘”°‰Õ¥±Ð€ÄàÌÈ°É•Á±…•€ÄàÌäƒŠP¥Ì¹½Ü„(€€€É•½É°„‰…­”…¹„ÁÕ‰±¥Í¡•µ•Í °½¸Ñ¡”‰É¥‘•}Ñ¥µ‰•É€…É¡•ÑåÁ”Ñ¡…Ð¡…‰••¸ÝÉ¥ÑÑ•¸(€€€…¹¹•Ù•ÈÕÍ•¸QÝ¼½˜¥ÑÌ¹Õµ‰•ÉÌ…É”•Ù¥‘•¹”É…Ñ¡•ÈÑ¡…¸¥¹Ù•¹Ñ¥½¸°Ý¡¥ ¥Ì¹•Ü¡•É”è(€€€€¨©Ñ•¸™••ÐÝ¥‘”¨¨¥Ì¡…É±•Ì±•…Ù•ÈÌ°É•…±±•¥¸Ñ¡”€©¡¥…¼QÉ¥‰Õ¹”¨½˜€Èä=Ð€ÄàäÌ‰ä„(€€€µ…¸Ý¡¼¡…‘É¥Ù•¸„Ñ•…´…É½ÍÌ¥Ð°…¹Ñ¡”€¨¨ÜÄ¸àÌ´ÍÁ…¸¨¨¥Ìµ•…ÍÕÉ•‰•ÑÝ••¸Ñ¡”ÑÝ¼(€€€ÑÉ…•€ÄàÌÐÝ…Ñ•É±¥¹•Ì…±½¹œÑ¡”-¥¹é¥”…±¥¹µ•¹ÐÉ…Ñ¡•ÈÑ¡…¸¡½Í•¸ƒŠP¥Ð…É••ÌÝ¥Ñ Ñ¡”(€€€É•… Ì‘É…™Ñ•µ•…¸Ý¥‘Ñ Ñ¼…‰½ÕÐ„µ•ÑÉ”°Ý¡¥ ¥ÌÑ¡”¡•¬Ñ¡…Ð¥ÐÉ•…‘ÌÑ¡”µ…À…ÐÑ¡¥Ì(€€€ÍÑ…Ñ¥½¸¥¹ÍÑ•…½˜…Ù•É…¥¹œ¥Ð¸Q¡É•”Í½ÕÉ”É•½É‘ÌÝ•É”…‘‘•°…±°Ñ¡É•”Ý¥Ñ ]…å‰…¬(€€€Í¹…ÁÍ¡½ÑÌ¸(€€€€¨©]¡…Ð¥Ì¥¹Ù•¹Ñ•¥ÌÑ¡”µ¥‘‘±”½˜Ñ¡”‰É¥‘”°…¹¥Ð¥ÌÑ¡”µ½ÍÐ½¹ÍÁ¥Õ½ÕÌÑ¡¥¹œ¥¸¥Ð¸¨¨(€€€±•…Ù•È‘•ÍÉ¥‰•ÌÑ¡”•¹‘ÌƒŠP€‰Ñ¡”…‰ÕÑµ•¹ÑÌÝ•É”‰Õ¥±Ð½˜¡•…Ùä±½Ì¥¸Ñ¡”Í¡…±±½ÜÝ…Ñ•È¹•…È(€€€Ñ¡”‰…¹­ÌˆƒŠP…¹¹½‰½‘ä‘•ÍÉ¥‰•ÌÝ¡…ÐÍÑ½½‰•ÑÝ••¸Ñ¡•´¸M½µ•Ñ¡¥¹œ¡…Ñ¼…ÉÉä€ÜÄ¸àÌ´½˜(€€€±½œÍÑÉ¥¹•È°Í¼Ñ¡”…É¡•ÑåÁ”Ì‘•™…Õ±Ð€Ð¸Ô´ÍÁ…¥¹œÁÕÑÌ€¨©™¥™Ñ••¸É¥‰Ì¥¸Ñ¡”É¥Ù•È¨¨°„(€€€É•Õ±…È½±½¹¹…‘”„Ù¥Í¥Ñ½ÈÝ¥±°É•……Ì„™…Ð…‰½ÕÐÑ¡”‰É¥‘”¸%Ð¥Ì„™…Ð…‰½ÕÐÑ¡”(€€€…É¡•ÑåÁ”¸0Èä…‘µ¥ÑÌ¥Ð°…¹Ñ¡”½¹™¥‘•¹”Ñ¥¹Ð…¹¹½ÐèÑ¡”Ñ¥¹ÐÉ…‘•ÌÝ¡…Ð„É¥ˆ€©¥Ì¨°(€€€¹½Ð¡½Üµ…¹äÑ¡•É”Ý•É”¸Q¡”ÍÁ…¸¥Ð‘¥Ù¥‘•Ì¥Ì¥ÑÍ•±˜Ñ¡”‘É…Ý¸Ý…Ñ•É±¥¹”µÑ¼µÝ…Ñ•É±¥¹”(€€€‘¥ÍÑ…¹”°…¹Ñ¡”…‰ÕÑµ•¹ÑÌÍÑ½½¥¹Í¥‘”Ñ¡…Ð±¥¹”‰ä…¸Õ¹É•½É‘•…µ½Õ¹Ð¸(€€€€¨©QÝ¼Í½ÕÉ•Ì½¹ÑÉ…‘¥Ð•… ½Ñ¡•È…‰½ÕÐÑ¡”Ñ¡¥¹œ…¹‰½Ñ …É”­•ÁÐ¸¨¨¹‘É•…Ì¡…Ì¥Ð(€€€€‰™½Éµ•½˜ÍÑÉ¥¹•ÉÌ…¹½¹±ä™¥ÑÑ•™½È™½½ÐÁ…ÍÍ•¹•ÉÌˆ…¹€‰ÕÍ•±•ÍÌ™½ÈÑ•…µÌˆ…Ì±…Ñ”…Ì(€€€Ñ¡”ÍÕµµ•È½˜€ÄàÌÌì±•…Ù•ÈÉ•µ•µ‰•É•‘É¥Ù¥¹œ…É½ÍÌ¥Ð°…¹½¸€ÄàÕœ€ÄàÌÔ„ÁÉ½•ÍÍ¥½¸½˜(€€€¡Õ¹‘É•‘ÌÉ½ÍÍ•¥Ð¸%ÐÝ…ÌÉ•‰Õ¥±Ð½ÈÝ¥‘•¹•¥¸‰•ÑÝ••¸…¹¹½Ñ¡¥¹œÉ•…¡•Í…åÌÝ¡•¸½È(€€€¡½Ü¸Q¡”É•½ÉÑ…­•ÌÑ¡”€ÄàÌÔÉ•…‘¥¹œƒŠP™½ÕÈÍÑÉ¥¹•ÉÌ°„™Õ±°µÝ¥‘Ñ ‘•¬ƒŠP…¹Í…åÌ½¸¥ÑÌ(€€€½Ý¸™…”Ñ¡…Ð…¸€ÄàÌÌÍ•¹”Ý½Õ±Ý…¹ÐÑ¡”½Ñ¡•È½¹”¸(€€€€¨©½ÉÉ•Ñ¥½¸Ñ¼Ñ¡¥ÌÁÉ½©•ÐÌ½Ý¸‘½ÍÍ¥•È…µ”½ÕÐ½˜ÝÉ¥Ñ¥¹œ¥Ð¸¨¨(€€€‘½Ì½É•Í•…É ¼ÀÌµÍÑÉÕÑÕÉ•Ìµ¹½ÉÑ ¹µ‘€ƒ
œÔÑ…Ì‰½Ñ €‰…‰½ÕÐ€ÄÀ™ÐÝ¥‘”ˆ…¹€‰±•…É¥¹œÑ¡”Ý…Ñ•È(€€€‰ä…‰½ÕÐ€Ø™Ðˆ…Ì‘½Õµ•¹Ñ•¸=¹±äÑ¡”Ý¥‘Ñ ÍÕÉÙ¥Ù•ÌèÑ¡”Á…•Ì…ÉÉå¥¹œÑ¡”Ý¥‘Ñ °Ñ¡”(€€€…‰ÕÑµ•¹ÑÌ°Ñ¡”ÍÑÉ¥¹•ÉÌ°Ñ¡”€ÄàÌÈ‘…Ñ”…¹Ñ¡”€ÄàÌäÉ•Á±…•µ•¹ÐÍ…ä¹½Ñ¡¥¹œ…‰½ÕÐ„¡•¥¡Ð(€€€…‰½Ù”Ñ¡”Ý…Ñ•È°…¹„‘¥É•ÐÍ•…É ½˜Ñ¡”Í…µ”¡½ÍÐ™½ÈÑ¡”Á¡É…Í¥¹œÉ•ÑÕÉ¹Ì¹½Ñ¡¥¹œ¸Q¡”(€€€™¥ÕÉ”¥Ì­•ÁÐ°±•…É…¹•}µ€¥ÌÑ…•¥¹™•ÉÉ•‘€°…¹‰É¥‘•}Ñ¥µ‰•É}Á…É…µÌ¹Áå€Ì‘½ÍÑÉ¥¹œ(€€€¥Ì½ÉÉ•Ñ•Í¼Ñ¡”½¹ÍÑ…¹ÐÌ¹…µ”ÍÑ½ÁÌ…ÍÍ•ÉÑ¥¹œÝ¡…Ð¥Ð…¹¹½ÐÍ¡½Ü¸(€€€€¨©Q¡”½¹ÑÉ…ÐÌÝ…Ñ•Èµ…¹¡½ÈÉÕ±”¥ÌÝ¥É•É…Ñ¡•ÈÑ¡…¸ÝÉ¥ÑÑ•¸¸¨¨‘½Ì½1µ=9QIP¹µ‘€¡…Ì(€€€Í…¥Í¥¹”Ñ¡”…É¡•ÑåÁ”Ý…Ì‘É…™Ñ•Ñ¡…Ð„ÍÑÉÕÑÕÉ”½Ù•ÈÝ…Ñ•È…¹¡½ÉÌä€ô€Á€…ÐÑ¡”‘•Í¥¸(€€€Ý…Ñ•ÈÍÕÉ™…”…¹Ñ¡…ÐÑ¡”É•¹‘•É•ÈµÕÍÐÁ±…”¥Ð……¥¹ÍÐÑ¡”Ý…Ñ•ÈÁ±…¹”ì¹½Ñ¡¥¹œ¥µÁ±•µ•¹Ñ•(€€€¥Ð°…¹¹½Ñ¡¥¹œ¹••‘•Ñ¼Õ¹Ñ¥°Ñ¡•É”Ý…Ì„‰É¥‘”¸Q¡”…É¡•ÑåÁ”‘•±…É•ÌYIQ%1}9!=I€°(€€€½µÁ¥±•}Í•¹”¹Áå€½Á¥•Ì¥ÐÑ¼Á±…•µ•¹Ð¹Ù•ÉÑ¥…±}…¹¡½É€°…¹Ñ¡”É•¹‘•É•ÈÁ±…•ÌÝ…Ñ•É€(€€€…Ð„±¥Ñ•É…°é•É¼ƒŠPÑ¡…ÐÁ±…¹”¥Ìé•É¼‰äÑ¡”‘•™¥¹¥Ñ¥½¸½˜Ñ¡”Ù•ÉÑ¥…°‘…ÑÕ´¸Q¡”Íµ½­”(€€€…ÍÍ•ÉÑÌÑ¡”€¨©‘¥™™•É•¹”¨¨‰•ÑÝ••¸Ñ¡”ÑÝ¼…¹¡½ÉÌ°¹½Ðä€ôôô€Á€è½Ù•È‘Éä±…¹Ñ¡•ä…É•”°(€€€Í¼„Ñ•ÍÐÑ¡…ÐÁ…ÍÍ•Ñ¡•É”Ý½Õ±ÁÉ½Ù”¹½Ñ¡¥¹œ¸(€€€€¨©]É¥Ñ¥¹œÑ¡…Ð…ÍÍ•ÉÑ¥½¸™½Õ¹ÑÝ¼Ñ¡¥¹ÌÑ¡”½‘”Ý…ÌÉ¥¡Ð…‰½ÕÐ…¹Ñ¡”‘•ÍÉ¥ÁÑ¥½¸Ý…Ì(€€€¹½Ð¸¨¨¥ÉÍÐ°Í…µÁ±¥¹œ…ÐÑ¡”É•½ÉÌÁ±…•µ•¹Ð½É¥¥¸ÁÉ½Ù•Ì¹½Ñ¡¥¹œ•¥Ñ¡•ÈèÑ¡…Ð½É¥¥¸¥Ì(€€€Ñ¡”Á½±å½¸Ì€ À°€À¤°™½ÈÑ¡¥Ì‰É¥‘”Ñ¡”Ý•ÍÐ•¹°Ý¡¥ Í¥ÑÌ•á…Ñ±ä½¸Ñ¡”ÑÉ…•Ý…Ñ•É±¥¹”(€€€Ý¡•É”Ñ¡”É½Õ¹É½ÍÍ•Ìé•É¼ƒŠPé•É¼……¥¹ÍÐé•É¼°…¹Ñ¡”¡•¬Á…ÍÍ•ÌÝ¡…Ñ•Ù•ÈÑ¡”É•¹‘•É•È(€€€‘½•Ì¸%ÐÍ…µÁ±•ÌÑ¡”‘•¬Ìµ¥‘Á½¥¹Ð¹½Ü¸M•½¹°Ñ¡”™…¥±ÕÉ”µ½‘”¥ÌÑ¡”½ÁÁ½Í¥Ñ”½˜Ñ¡”(€€€½‰Ù¥½ÕÌ½¹”¸Ñ•ÉÉ…¥¸¹¡•¥¡Ð ¥€‘½•Ì¹½ÐÉ•Á½ÉÐÑ¡”¡…¹¹•°‰•½Ù•ÈÝ…Ñ•Èì¥ÐÉ•Á½ÉÑÌ„(€€€€¨©Ý…‘¥¹œ‰…ÉÉ¥•È…Ð€¬Ð´¨¨°ÁÕÐÑ¡•É”Ñ¼ÍÑ½ÀÑ¡”Ý…±­•ÈÍÑÉ½±±¥¹œ¥¹Ñ¼Ñ¡”É¥Ù•È¸‰É¥‘”(€€€±•™Ð½¸Ñ¡”Ñ•ÉÉ…¥¸…¹¡½ÈÑ¡•É•™½É”‘½•Ì¹½ÐÍ¥¹¬½ÕÐ½˜Í¥¡ÐƒŠP¥Ð¡…¹Ì™½ÕÈµ•ÑÉ•Ì…‰½Ù”(€€€Ñ¡”Ý…Ñ•È°Ý¡¥ ¥ÌÑ¡”¡…É‘•È™…¥±ÕÉ”Ñ¼É•…°…¹¥Ð¥ÌÝ¡…ÐÑ¡”Íµ½­”¹½ÜÁ¥¹Ì¸(€€€€¨©e½Ô…¹¹½ÐÝ…±¬…É½ÍÌ¥Ð°…¹Ñ¡…Ð¥ÌÍÑ…Ñ•É…Ñ¡•ÈÑ¡…¸™…­•¸¨¨Q¡”Ý…±­•È™½±±½ÝÌÑ¡”(€€€Ñ•ÉÉ…¥¸°Í¼Ñ¡”‘•¬¥ÌÍ•¹•Éäå½ÔÁ…ÍÌÕ¹‘•ÈÉ…Ñ¡•ÈÑ¡…¸„É½ÕÑ”ì¥ÑÌ™½½ÑÁÉ¥¹Ð¥Ì•á±Õ‘•(€€€™É½´Ñ¡”½±±¥Í¥½¸Á½±å½¹Ì°‰•…ÕÍ”ÑÉ•…Ñ¥¹œ„‘•¬…Ì„Ý…±°Ý½Õ±ÁÕÐ…¸¥¹Ù¥Í¥‰±”‰…ÉÉ¥•È(€€€…É½ÍÌÑ¡”É¥Ù•ÈÝ¥Ñ ¹½Ñ¡¥¹œÙ¥Í¥‰±”…Ð¡•…¡•¥¡ÐÑ¼•áÁ±…¥¸¥Ð¸Ý…±­…‰±”‘•¬¹••‘ÌÑ¡”(€€€Ý…±­•ÈÑ¼±•…É¸…‰½ÕÐÍÕÉ™…•Ì…‰½Ù”Ñ¡”É½Õ¹°Ý¡¥ ¥Ì¥ÑÌ½Ý¸Õ¹¥Ð½˜Ý½É¬¸((ÈÈ¸€¨©Q¡”‰É¥‘”…ÉÉ¥Ù•Ì¹½Ý¡•É”°…¹Ñ¡”…Ñ”Ñ¡…ÐÍ…åÌÍ¼¥Ì¹•Ü¸¨¨Q¡É•”ÉÕ±•Ì¹½Ü…Í¬(€€€Ý¡•Ñ¡•È„É•½É¥Ì¡½¹•ÍÐèÑ¡”½¹™¥‘•¹”µ½‘•°É…‘•ÌÝ¡…Ð„Ù…±Õ”±…¥µÌ°Ñ¡”±¥‰•ÉÑ¥•Ì(€€€½Ù•É…”¡•¬‘•µ…¹‘Ì…¸…‘µ¥ÍÍ¥½¸™½È…¹åÑ¡¥¹œ¥¹Ù•¹Ñ•°…¹Ñ¡”•½µ•ÑÉä‘•±…É…Ñ¥½¹Ì(€€€‘•µ…¹½¹”™½È…¹åÑ¡¥¹œÍÑ…Ñ•…¹¹½Ð‰Õ¥±Ð¸9½¹”½˜Ñ¡•´…¸Í•”„ÍÑÉÕÑÕÉ”Ñ¡…ÐÝ…Ì(€€€‰Õ¥±Ð™…¥Ñ¡™Õ±±ä½¹Ñ¼É½Õ¹Ñ¡…Ð¥Ì¹½ÐÕ¹‘•É¹•…Ñ ¥Ð°‰•…ÕÍ”€¨©¹½Ñ¡¥¹œ¥¸Ñ¡”É•½É¥Ì(€€€ÝÉ½¹œ¨¨¸Ù•Éä¹…µ”É•Í½±Ù•Ì°•Ù•ÉäÙ…±Õ”É•…¡•Ì„Ù•ÉÑ•à°•Ù•Éä½¹™¥‘•¹”¡¥À¥Ì•…É¹•°(€€€…¹Ñ¡”9½ÉÑ 	É…¹ ‰É¥‘”ÍÑ¥±°ÍÑ…¹‘Ì€È¸ÐÈ´±•…È½˜Ñ¡”Ñ•ÉÉ…¥¸…Ð‰½Ñ ±…¹‘¥¹Ì¸(€€€¡•­}É½Õ¹‘}½¹Ñ…Ñ€±½Í•ÌÑ¡…Ð‘¥É•Ñ¥½¸¸… …É¡•ÑåÁ”‘•±…É•ÌÝ¡•É”¥ÐÑ½Õ¡•ÌÑ¡”(€€€É½Õ¹ƒŠPÁ•É¥µ•Ñ•É€™½È„‰Õ¥±‘¥¹œ€¡Ñ¡”™½½ÑÁÉ¥¹Ð½ÕÑ±¥¹”°…ÐÑ¡”‰…Í”½˜Ñ¡”Ý…±±Ì¤…¹(€€€•¹‘Í€™½È„É½ÍÍ¥¹œ€¡Ñ¡”ÑÝ¼•¹•‘•Ì°…Ð‘•¬¡•¥¡Ð¤ƒŠP…¹Ù…±¥‘…Ñ”¹Áå€µ•…ÍÕÉ•ÌÑ¡…Ð(€€€½ÕÑ±¥¹”……¥¹ÍÐÑ¡”½µµ¥ÑÑ•¡•¥¡Ñ™¥•±Ñ¡É½Õ Ñ½½±Ì½¡•¥¡Ñ™¥•±¹Áå€¸€¨©Q¡”Ñ½±•É…¹”¥Ì(€€€¹½Ð„¹•Ü¹Õµ‰•Èè¥Ð¥ÌÑ¡”Ý…±­•ÈÌ€À¸ÌÔ´ÍÑ•ÀµÕÀÉÕ±”¨¨°‰•…ÕÍ”Ñ¡”ÅÕ•ÍÑ¥½¸Ñ¡”…Ñ”(€€€…Í­Ì¥Ì±¥Ñ•É…±±äÑ¡”Ý…±­•ÈÌÅÕ•ÍÑ¥½¸°…¹„ÍÑÉÕÑÕÉ”„Ù¥Í¥Ñ½È½Õ±¹½ÐÍÑ•À½¹Ñ¼¡…Ì(€€€¹½Ðµ•ÐÑ¡”É½Õ¹¸(€€€€¨©]¡…Ð¥Ð™½Õ¹¥ÌÑ¡”½¹±äÑ¡¥¹œ¥Ð™½Õ¹°…¹Ñ¡…Ð¥ÌÝ½ÉÑ ÍÑ…Ñ¥¹œÑ½¼¸¨¨Q¡”Í¥à(€€€‰Õ¥±‘¥¹Ì±…¹èÑ¡•¥ÈÝ½ÉÍÐ½É¹•ÈÍ¥ÑÌ€À¸ÄØ´½™˜€¡Ñ¡”]½±˜A½¥¹ÐQ…Ù•É¸°½Ù•ÈÑ¡”‰…¹¬(€€€™…±°¤°Ý•±°¥¹Í¥‘”„ÍÑ•À¸Q¡”‰É¥‘”‘½•Ì¹½Ð°…¹…¹¹½ÐÝ¥Ñ Ñ¡”‘…Ñ„…Ì¥ÐÍÑ…¹‘ÌƒŠPÑ¡”(€€€‘•¬Í¥ÑÌ…Ð€È¸ÈÈ´€¡±•…Ù•ÈÌ¥¹™•ÉÉ•Í¥àµ™½½Ð±•…É…¹”Á±ÕÌÑ¡”ÍÑÉ¥¹•È…¹Á±…¹¬‘•ÁÑ (€€€Õ¹‘•È¥Ð¤…¹Ñ¡”¡¥¡•ÍÐ±…¹…¹åÝ¡•É”¥¸Ñ¡”€ØÐÀ´‰½à¥Ì€Ä¸ÌÄ´°Í¼Ñ¡•É”¥Ì¹¼É½Õ¹¥¸(€€€Ñ¡¥Ì•Á½ ™½È¥ÐÑ¼…ÉÉ¥Ù”…Ð¸Q¡”É•½É‘•±…É•ÌÉ½Õ¹‘}½¹Ñ…Ðè…ÁÁÉ½…¡}¹½Ñ}µ½‘•±±•‘€(€€€…¹0ÌÀ…‘µ¥ÑÌ¥ÐìÑ¡”Á½ÁÕÀÍ¡½ÝÌÑ¡”¡¥À½¸Ñ¡”‰Õ¥±‘¥¹œ‰•¥¹œ¥¹ÍÁ•Ñ•°Í¼Ñ¡”(€€€…‘µ¥ÍÍ¥½¸É•…¡•Ì„Ù¥Í¥Ñ½È…¹¹½Ð½¹±ä„É•Ù¥•Ý•È¸(€€€€¨©Q¡”…ÁÁÉ½… ¥Ì¹½Ðµ½‘•±±•‰•…ÕÍ”¹½Ñ¡¥¹œ‘•ÍÉ¥‰•Ì½¹”¸¨¨¹‘É•…Ì¥Ù•ÌÑ¡”ÍÑÉ¥¹•ÉÌ°(€€€±•…Ù•È¥Ù•ÌÑ¡”Ý¥‘Ñ …¹Ñ¡”±½œ…‰ÕÑµ•¹ÑÌ€‰¥¸Ñ¡”Í¡…±±½ÜÝ…Ñ•È¹•…ÈÑ¡”‰…¹­Ìˆ°…¹¹¼(€€€Í½ÕÉ”É•…¡•Í…åÌ¡½Ü„Á•ÉÍ½¸½È„Ñ•…´½Ð™É½´Ñ¡”‰…¹¬½¹Ñ¼Ñ¡”‘•¬¸¸•µ‰…¹­µ•¹Ð(€€€Ý½Õ±‰”„Í•½¹¥¹Ù•¹Ñ¥½¸ÍÑ…­•½¸Ñ¡”±•…É…¹”™¥ÕÉ”ƒŠPÝ¡¥ ¥Ì¥ÑÍ•±˜½¹±ä(€€€¥¹™•ÉÉ•‘€…¹Õ¹Í½ÕÉ•¥¸Ñ¡”‘½ÍÍ¥•ÈÑ¡…ÐÍÕÁÁ±¥•¥ÐƒŠP…¹Õ¹±¥­”0ÈäÌ™¥™Ñ••¸É¥‰Ì¥Ð(€€€¥ÌÑ¡”¥¹Ù•¹Ñ¥½¸„Ù¥Í¥Ñ½ÈÝ½Õ±Ý…±¬½Ù•ÈÉ…Ñ¡•ÈÑ¡…¸±½½¬…Ð¸(€€€€¨©Íµ…±±•ÈÑ¡¥¹œ…µ”½ÕÐ½˜ÝÉ¥Ñ¥¹œ¥Ð°…¹¥Ð¥Ì„Ý…É¹¥¹œ…‰½ÕÐÑ¡”ÍÑ…±•¹•ÍÌ¡…Í ¸¨¨(€€€Q¡”½¹Ñ…Ð¡•¥¡ÐÝ…Ì™¥ÉÍÐÝÉ¥ÑÑ•¸…Ì„ÁÉ½Á•ÉÑå€½¸	É¥‘•Q¥µ‰•ÉA…É…µÍ€°…¹(€€€µ•Í¡}¥¹ÁÕÑÌ¹Áå€¡…Í¡•Ì•Ù•ÉäÁÉ½Á•ÉÑä„Á…É…µ•Ñ•È±…ÍÌ‘•É¥Ù•ÌƒŠPÍ¼„¹Õµ‰•È¹¼‰Õ¥±‘•È(€€€É•…‘Ì¥µµ•‘¥…Ñ•±äÉ”µÍÑ…±•Ñ¡”‰É¥‘”¸Q¡…Ð¥Ì•á…Ñ±äÑ¡”™…±Í”Á½Í¥Ñ¥Ù”ƒ
œ€ÄÔÉ•ÝÉ½Ñ”Ñ¡”(€€€¡…Í Ñ¼•¹°…ÉÉ¥Ù¥¹œ™É½´„¹•Ü‘¥É•Ñ¥½¸èÑ¡”ÉÕ±”€‰„‘•É¥Ù•ÁÉ½Á•ÉÑä¥Ì„µ•Í ¥¹ÁÕÐˆ¥Ì(€€€É¥¡Ð…‰½ÕÐ½¹ÍÑ…¹ÑÌ…¹ÝÉ½¹œ…‰½ÕÐ…•ÍÍ½ÉÌ¸%Ð¥Ì„µ½‘Õ±”µ±•Ù•°(€€€É½Õ¹‘}½¹Ñ…Ñ}è¡Á…É…µÌ¥€¥¹ÍÑ•…°…¹Ñ¡”‘½ÍÑÉ¥¹œÍ…åÌÝ¡äÍ¼Ñ¡”¹•áÐ½¹”‘½•Ì¹½Ð(€€€É•‘¥Í½Ù•È¥Ð¸(€€€€¨©]¡…Ð¥ÐÍÑ¥±°…¹¹½ÐÍ•”¨¨¥Ì„ÍÑÉÕÑÕÉ”ÍÑ…¹‘¥¹œ½¸É½Õ¹Ñ¡…Ð•á¥ÍÑÌ…¹¥ÌÝÉ½¹œƒŠP(€€€Ñ¡”¡•¬½µÁ…É•Ì„µ•Í ……¥¹ÍÐÑ¡”¡•¥¡Ñ™¥•±°…¹‰½Ñ …¸…É•”½¸„ÍÕÉ™…”¹¼(€€€Í½ÕÉ”ÍÕÁÁ½ÉÑÌ¸((ÈÌ¸€¨©½ÕÈ…ÑÑÉ¥‰ÕÑ•Ì½˜Ñ¡”‰É¥‘”…É”¹½Ü‰•¡¥¹Ñ¡•¥È•Ù¥‘•¹”°…¹Ñ¡”•Ù¥‘•¹”Ý…Ì„(€€€™½½Ñ¹½Ñ”Õ¹‘•È„Á…É…É…Á Ñ¡¥ÌÁÉ½©•Ð¡…ÌÅÕ½Ñ•™½ÈÝ••­Ì¸¨¨Q¡”É•½ÉÌ½Ý¸µ•µ¼±¥ÍÑ•(€€€™½ÕÈ½Á•¸Ñ¡É•…‘Ì½¸€ÈÀÈØ´Àà´ÄÀìÑÝ¼Ý•É”ÁÕ±±•Ñ¡”Í…µ”‘…ä…¹½¹”½˜Ñ¡•´Á…¥™½È(€€€•Ù•ÉåÑ¡¥¹œ¸€¨©¹‘É•…ÌÁÉ¥¹ÑÌ°…ÐÑ¡”™½½Ð½˜ÁÀ¸€ØÌÄ´ØÌÈ°„ÍÑ…Ñ•µ•¹ÐÍ¥¹•‰ä™½ÕÈµ•¸Ý¡¼(€€€ÕÍ•Ñ¡”‰É…¹ ‰É¥‘•Ì¨¨ƒŠP(¸¸…Ñ½¸°)½¡¸	…Ñ•Ì°¡…É±•Ì±•…Ù•È…¹)½¡¸9½‰±”°…É••(€€€…Ð„µ••Ñ¥¹œ½˜½±Í•ÑÑ±•ÉÌ±…Ñ”¥¸Ñ¡”™…±°½˜€ÄààÌ…¹¡…¹‘•Ñ¼Ñ¡”•‘¥Ñ½ÉÌ‰ä	…Ñ•Ì¸(€€€%Ð¥ÌÑ¡”½¹±ä‘•ÍÉ¥ÁÑ¥½¸…¹å‰½‘äÝÉ½Ñ”½˜¡½ÜÑ¡•Í”É½ÍÍ¥¹ÌÝ•É”ÁÕÐÑ½•Ñ¡•Èè(€€€…‰ÕÑµ•¹ÑÌ½˜±½Ì¥¸Ñ¡”Í¡…±±½ÜÝ…Ñ•È¹•…ÈÑ¡”‰…¹­Ì°€¨©ÑÝ¼€‰‰•¹ÑÌˆ½˜™½ÕÈ¡•…Ùä±½Ì(€€€É•ÍÑ¥¹œ½¸Ñ¡”‰½ÑÑ½´¥¸‘••Á•ÈÝ…Ñ•È¨¨°ÍÑÉ¥¹•ÉÌ½˜¡•…Ùä±½Ì™É½´Ñ¡”…‰ÕÑµ•¹ÑÌÑ¼Ñ¡”(€€€‰•¹ÑÌ…¹‰•ÑÝ••¸Ñ¡•´°€¨©ÁÕ¹¡•½¹Ì½ÈÍÁ±¥Ð±½Ì™½È„™±½½È¨¨°…‰½ÕÐÑ•¸™••ÐÝ¥‘”°(€€€€¨©Ý¥Ñ¡½ÕÐÉ…¥±¥¹Ì™½ÈÑ¡”™¥ÉÍÐ™•Üå•…ÉÌ°…™Ñ•ÈÝ¡¥ Õ…É‘Ì½ÈÉ…¥±¥¹ÌÝ•É”…‘‘•¨¨°…¹(€€€€¨©…‰½ÕÐÍ¥à™••Ð…‰½Ù”Ñ¡”Ý…Ñ•È°€‰Í¼Ñ¡…ÐÑ•…µÌÁ…ÍÍ•Õ¹‘•ÈÑ¡•´½¸Ñ¡”¥”™É••±ä¸ˆ¨¨(€€€M½ÕÉ”É•½Éè½±‘}Í•ÑÑ±•ÉÍ}‰É¥‘•Í|ÄààÍ€°Ñ¥•È€È¸(€€€€¨©]¡…Ð¥Ð½ÉÉ•ÑÌ°…¹¹½¹”½˜¥Ð¥Ì½ÉÉ•Ñ•å•Ð¸¨¨Á¥•É}ÍÁ…¥¹}µ€ÁÕÑÌ™¥™Ñ••¸É¥‰Ì¥¸(€€€Ñ¡”É¥Ù•È½¸Ñ¡”…É¡•ÑåÁ”Ì‘•™…Õ±ÐìÑ¡”±•ÑÑ•ÈÍ…åÌÑÝ¼‰•¹ÑÌ¸Á¥•É}­¥¹‘€¥ÌÉ¥‰€°…¹(€€€Ñ¡¥ÌÉ•½É…ÉÕ•¥ÑÌÝ…äÑ¡•É”‰äÑÉ•…Ñ¥¹œÑ¡”-¥¹é¥”MÑÉ••ÐÁ…”ÌÑåÁ”µÝ½É€‰	•¹Ðˆ…Ì(€€€µ½‘•É¸•‘¥Ñ½É¥…°±…ÍÍ¥™¥…Ñ¥½¸ƒŠP¥Ð¥ÌÑ¡”Í•ÑÑ±•ÉÌœ½Ý¸Ý½É°…¹±•…Ù•È°Ñ¡”•å•Ý¥Ñ¹•ÍÌ(€€€Ñ¡…Ð…ÉÕµ•¹Ð±•…¹•½¸°Í¥¹•¥Ð¸±•…É…¹•}µ€Ý…Ì‘•µ½Ñ•Ñ¼¥¹™•ÉÉ•‘€¡•É”™½ÈÝ…¹Ð½˜(€€€„Á…”ìÑ¡”Á…”•á¥ÍÑÌ°…¹Ñ¡”‘½ÍÍ¥•ÈÌm=u€Ñ…œÝ…ÌÉ¥¡Ð¸Q¡”‘•¬¥ÌÑ¡”…É¡•ÑåÁ”Ì(€€€…¹Ñ¡”±•ÑÑ•ÈÍÑ…Ñ•Ì¥Ð¸€¨©Ù•Éä½¹”½˜Ñ¡½Í”¥Ì„µ•Í ¥¹ÁÕÐ¨¨°Í¼Ñ¡”É•½É…¹¹½Ðµ½Ù”(€€€Ý¥Ñ¡½ÕÐÑ¡”1µ½Ù¥¹œÝ¥Ñ ¥Ð°…¹Ñ¡¥Ì½µµ¥Ð‘•±¥‰•É…Ñ•±ä¡…¹•Ì¹¼Ù…±Õ”…¹¹¼(€€€½¹™¥‘•¹”Ñ…œè¥Ð±…¹‘ÌÑ¡”Í½ÕÉ”°Ñ¡”µ•µ¼°Ñ¡”±¥‰•ÉÑ¥•ÌÕÁ‘…Ñ•Ì…¹Ñ¡”¹½Ñ•ÌÑ¡…ÐÍ…ä(€€€½¸•… …ÑÑÉ¥‰ÕÑ”Ì½Ý¸™…”Ñ¡…Ð¥Ð¥Ì‰•¡¥¹¥ÑÌ•Ù¥‘•¹”¸€¨©Q¡”É•Á…¥È…¹¥ÑÌ‰…­”…É”(€€€½¹”Í±¥”…¹¥Ð¥ÌÑ¡”¹•áÐ½¹”¸¨¨€¡%ÐÝ…Ì°…¹¥Ð±…¹‘•Ñ¡”Í…µ”‘…äƒŠPƒ
œ€ÈÐ¸¤(€€€€¨©Q¡”Ý½É¬½É‘•È¨¨°Í¼Ñ¡”¹•áÐÍ±¥”‘½•Ì¹½Ð¡…Ù”Ñ¼É”µ‘•É¥Ù”¥Ðè‰É¥‘•}Ñ¥µ‰•É€‰Õ¥±‘Ì(€€€¥¹Ñ•Éµ•‘¥…Ñ”ÍÕÁÁ½ÉÑÌ™É½´„ÍÁ…¥¹œ°…¹Ñ¡”•Ù¥‘•¹”¥Ì„½Õ¹Ð…¹„™½É´°¹½Ð„ÍÁ…¥¹œƒŠP(€€€ÑÝ¼‰•¹ÑÌ…ÐÑ¡”Ñ¡¥É‘Ì½˜„€ÜÄ¸àÌ´ÍÁ…¸¥Ì„‘¥™™•É•¹ÐÁ…É…µ•Ñ•É¥Í…Ñ¥½¸°¹½Ð„‘¥™™•É•¹Ð(€€€¹Õµ‰•È°Í¼Ñ¡”…É¡•ÑåÁ”¡…¹•Ì‰•™½É”Ñ¡”É•½É‘½•Ì¸Á¥•É}­¥¹‘€Ý…¹ÑÌ„‰•¹Ñ€Ù…±Õ”(€€€€¡™½ÕÈ¡•…Ùä±½ÌÍÑ…¹‘¥¹œ½¸Ñ¡”‰½ÑÑ½´¤‰•Í¥‘”É¥‰€¸±•…É…¹•}µ€µ½Ù•ÌÑ¼‘½Õµ•¹Ñ•‘€(€€€Ý¥Ñ Ñ¡¥ÌÍ½ÕÉ”¸É…¥±¥¹€ÍÑ…åÌ™…±Í•€…¹¥ÑÌ¹½Ñ”¡…¹•Ì™É½´…¸…ÉÕµ•¹Ð™É½´Í¥±•¹”(€€€Ñ¼„É•…‘¥¹œ½˜€‰Ñ¡”™¥ÉÍÐ™•Üå•…ÉÌˆ¸0Èäµ½Ù•ÌÑ¼€¨©I•Í½±Ù•¨¨Ý¡•¸Ñ¡”µ•Í Í¡½ÝÌÑÝ¼(€€€ÍÕÁÁ½ÉÑÌ°…¹¹½Ð‰•™½É”¸(€€€€¨©QÝ¼¹•…Ñ¥Ù”™¥¹‘¥¹Ì…µ”Ý¥Ñ ¥Ð°…¹Ñ¡•ä½ÍÐ…ÌµÕ Ñ¼•ÍÑ…‰±¥Í …ÌÑ¡”Á½Í¥Ñ¥Ù”(€€€½¹”¸¨¨9•¥Ñ¡•È€ÄàÌÐÍ¡••Ð‘É…ÝÌÑ¡¥Ì‰É¥‘”¸	½Ñ Ý•É”¥¹ÍÁ•Ñ•…ÐÑ¡”É½ÍÍ¥¹œÌ½Ý¸™¥ÑÑ•(€€€Á¥á•°É…Ñ¡•ÈÑ¡…¸‰ä•å”ƒŠP¥¹Ù•ÉÐ•… Í¡••ÐÌ½µµ¥ÑÑ•@…™™¥¹”…ÐÑ¡”É•½ÉÌ‘•¬±¥¹”°(€€€™•Ñ Ñ¡…Ð%%%É•¥½¸ƒŠP…¹½¸‰½Ñ °Ñ¡”ÍÑÉ••ÐÍÑ½ÁÌ…ÐÑ¡”Ý…Ñ•É±¥¹”è„Á±…ÑÑ•ÍÑÉ••Ð¥Ì„(€€€‘•‘¥…Ñ¥½¸°¹½Ð„ÍÑÉÕÑÕÉ”¸Q¡”Ñ¡É•…Ñ¡”µ•µ¼É…Ñ•µ½ÍÐÁÉ½µ¥Í¥¹œ°€‰Ñ¡”€ÄàÌÐ¼ÄàÌÔ]…‰…¹Í¥„(€€€…¹-¥¹é¥”Ì‘‘¥Ñ¥½¸Á±…Ðˆ°ÑÕÉ¹Ì½ÕÐÑ¼‰”¡…Ñ¡…Ý…å|ÄàÌÑ€°„Í¡••Ð…±É•…‘ä¥¸Ñ¡¥Ì‘…Ñ…Í•Ð(€€€…¹…±É•…‘ä•½É•™•É•¹•°Ý¡¥ ¥Ì¥ÑÌ½Ý¸Íµ…±°±•ÍÍ½¸…‰½ÕÐ½Á•¸µÑ¡É•…±¥ÍÑÌ¸¹½¸(€€€!…Ñ¡…Ý…ä„¡…Ñ¡•°±…‘‘•Èµ±¥­”µ…É¬Í¥ÑÌ¥¸Ñ¡”¡…¹¹•°Ý¥Ñ¡¥¸€ÌÔ´½˜Ñ¡”É½ÍÍ¥¹œ…¹É•…‘Ì(€€€½¹Ù¥¹¥¹±ä…Ì„Á±…¹¬µ…¹µÍÑÉ¥¹•È‰É¥‘”Íåµ‰½°…Ðµ½‘•É…Ñ”é½½´ì…Ð™Õ±°É•Í½±ÕÑ¥½¸¥Ð¥Ì(€€€Ñ¡”±•ÑÑ•È€¨© ¨¨½˜€‰	I9 ˆ°±•ÑÑ•É•‘½Ý¸Ñ¡”Ý…Ñ•È¸%Ð¥ÌÝÉ¥ÑÑ•¸‘½Ý¸¡•É”Í¼Ñ¡…Ð¥Ð¥Ì(€€€™½Õ¹½¹”É…Ñ¡•ÈÑ¡…¸‘¥Í½Ù•É•ÑÝ¥”¸((ÈÐ¸€¨©%aƒŠPÑÝ¼‰•¹ÑÌ°¹½Ð™¥™Ñ••¸É¥‰Ì°…¹Ñ¡”É•Á…¥È¡…¹•„Á…É…µ•Ñ•ÈÉ…Ñ¡•ÈÑ¡…¸„(€€€¹Õµ‰•È¸¨¨ƒ
œ€ÈÌÌÝ½É¬½É‘•È±…¹‘•Ñ¡”Í…µ”‘…ä¥ÐÝ…ÌÝÉ¥ÑÑ•¸°É•½É…¹…É¡•ÑåÁ”…¹‰…­”(€€€¥¸½¹”½µµ¥Ð¸Á¥•É}ÍÁ…¥¹}µ€¥Ì½¹”™É½´‰É¥‘•}Ñ¥µ‰•É€…¹™É½´Ñ¡”É•½Éì(€€€Á¥•É}½Õ¹Ðè€É€€¡‘½Õµ•¹Ñ•‘€¤É•Á±…•Ì¥Ð°Á¥•É}­¥¹‘€¥Ì‰•¹Ñ€°±•…É…¹•}µ€¥ÌÁÉ½µ½Ñ•(€€€Ñ¼‘½Õµ•¹Ñ•‘€½¸Ñ¡”€ÄààÌÍÑ…Ñ•µ•¹Ð°…¹Ñ¡”™±½½ÈÑ¡”…É¡•ÑåÁ”¡…‰••¸ÍÕÁÁ±å¥¹œ¥¸(€€€Í¥±•¹”¥ÌÍÑ…Ñ•…Ì‘•­}­¥¹èÁÕ¹¡•½¹€¸Q¡”É¥Ù•È…ÉÉ¥•ÌÑ¡É•”ÍÁ…¹ÌÝ¡•É”¥Ð…ÉÉ¥•(€€€Í¥áÑ••¸¸(€€€€¨©Q¡”Á…É…µ•Ñ•ÈÝ…ÌÑ¡”™…Õ±Ð°¹½ÐÑ¡”Ù…±Õ”¸¨¨¸…É¡•ÑåÁ”Ñ¡…Ð‘¥Ù¥‘•Ì„ÍÁ…¸‰ä„ÍÁ…¥¹œ(€€€…¸½¹±ä•Ù•ÈÁÉ½‘Õ”„½±½¹¹…‘”°…¹„ÍÁ…¥¹œ¥Ì„‰Õ¥±‘•ÈÌ½¹Ù•¹¥•¹”Ñ¡…Ð¹¼Ý¥Ñ¹•ÍÌ(€€€Ý½Õ±•Ù•ÈÉ•½É¸]¡…Ð„µ…¸Ý¡¼‘É½Ù”„Ñ•…´…É½ÍÌ„‰É¥‘”É•µ•µ‰•ÉÌ¥Ì€©¡½Üµ…¹ä¨ÍÑ½½(€€€¥¸Ñ¡”Ý…Ñ•È…¹€©Ý¡…ÐÑ¡•äÝ•É”µ…‘”½˜¨ƒŠPÍ¼Ñ¡”¥¹ÁÕÐ¥Ì¹½Ü„½Õ¹Ð…¹„™½É´°…¹Ñ¡”(€€€ÍÁ…¥¹œÍÕÉÙ¥Ù•Ì½¹±ä…ÌA%I}MA%9}11	-}5€°Ñ¡”Ñ¡¥¹œ„‰É¥‘”™…±±Ì‰…¬Ñ¼Ý¡•¸(€€€¹½‰½‘ä‘•ÍÉ¥‰•¥ÑÌµ¥‘‘±”¸¡…¹¥¹œ€Ð¸ÔÑ¼€ÈÌ¸äÐÝ½Õ±¡…Ù”™¥á•Ñ¡¥Ì‰É¥‘”…¹±•™ÐÑ¡”(€€€¹•áÐ½¹”Ñ¼‰”™½Õ¹‰äÑ¡”Í…µ”…¥‘•¹Ð¸(€€€€¨©]¡…ÐÑ¡”½¹™¥‘•¹”Ù¥•Ü¹½ÜÍ…åÌ°…¹¥ÐÍ…åÌµ½É”Ñ¡…¸¥Ð‘¥¸¨¨±•…É…¹•}µ€¥Ì½¹”½˜(€€€Ñ¡”…ÑÑÉ¥‰ÕÑ•ÌÑ¡…ÐÍ…åÌÝ¡…ÐÑ¡¥ÌÍÑÉÕÑÕÉ”]L€¡„‰É¥‘”Ì‘½Õµ•¹Ñ•‘•ÍÉ¥ÁÑ¥½¸€©¥Ì¨(€€€‘¥µ•¹Í¥½¹…°ƒŠPÍ•”‰É¥‘•}Ñ¥µ‰•É}Á…É…µÍ€¤°Í¼ÁÉ½µ½Ñ¥¹œ¥ÐÑ…­•ÌÑ¡”‘•¬…¹Ñ¡”ÍÑÉ¥¹•ÉÌ(€€€½ÕÐ½˜Ñ¡”¡…±˜µ‘¥Ñ¡•É•ÍÑ…Ñ”Ñ¡”¥¹™•ÉÉ•‘€Ñ…œÁÕÐÑ¡•´¥¸°…¹Ñ¡”‰•¹ÑÌ½µ”½ÕÐÍ½±¥(€€€‰•…ÕÍ”‰½Ñ Ñ¡•¥È½Õ¹Ð…¹Ñ¡•¥È™½É´…É”…ÑÑ•ÍÑ•¸Q¡…Ð¥ÌÑ¡”™¥ÉÍÐÑ¥µ”¥¸Ñ¡¥Ì‘…Ñ…Í•Ð(€€€Ñ¡…Ð•Ù¥‘•¹”¡…Ìµ…‘”Í½µ•Ñ¡¥¹œ€©±•ÍÌ¨‘¥Ñ¡•É•¸(€€€€¨©¹Ý¡…Ð¥ÐÍÑ¥±°…¹¹½ÐÍ…ä¥ÌÝ¡•É”Ñ¡•äÍÑ½½¸¨¨Q¡”±•ÑÑ•È±½…Ñ•ÌÑ¡”‰•¹ÑÌ‰ä‘•ÁÑ ƒŠP(€€€€‰É•ÍÑ¥¹œ½¸Ñ¡”‰½ÑÑ½´°¥¸‘••Á•ÈÝ…Ñ•ÈˆƒŠPÝ¡¥ ¥Ì„±½…Ñ½ÈÑ¡¥ÌÁÉ½©•Ð…¹¹½ÐÕÍ”è¹¼(€€€Í½ÕÉ”¥Ù•ÌÑ¡”¡…¹¹•°Ì‰•ÁÉ½™¥±”…¹¹½Ñ¡¥¹œ‰•±½ÜÑ¡”Ý…Ñ•É±¥¹”¥Ìµ½‘•±±•¸Q¡•ä…É”(€€€‰Õ¥±Ð…ÐÑ¡”Ñ¡¥ÉÁ½¥¹ÑÌ‰•…ÕÍ”Ñ¡…Ð¥ÌÝ¡…Ð„‰Õ¥±‘•ÈÝ½Õ±‘¼Ý¥Ñ Ñ¡É•”É½Õ¡±ä•ÅÕ…°(€€€ÉÕ¹Ì¸M¼Ñ¡”¡¥À½¸Á¥•É}½Õ¹Ñ€É…‘•Ì¡½Üµ…¹ä…¹„Ù¥Í¥Ñ½ÈÍ••Ì•á…Ñ±äÝ¡•É”°Ý¡¥ ¥Ì(€€€Ñ¡”¡¥µ¹•åÍ€Í¥ÑÕ…Ñ¥½¸½˜ƒ
œ€Ää…ÉÉ¥Ù¥¹œ…Ð„‘¥™™•É•¹ÐÍÑÉÕÑÕÉ”¸€¨©0ÌÄ¨¨¥ÌÝ¡•É”¥Ð¥Ì(€€€…‘µ¥ÑÑ•°…¹¥Ð…ÉÉ¥•Ì„Í•½¹½µ¥ÍÍ¥½¸Ñ¡”É•Á…¥ÈÉ•…Ñ•èÑ¡É•”ÍÁ…¹Ìµ…­”•… ÍÑÉ¥¹•È(€€€ÉÕ¸€ÈÌ¸ä´°±½¹•ÈÑ¡…¸…¹äÑ¥µ‰•È…¹å‰½‘äÝ…Ìµ½Ù¥¹œ°Í¼Ñ¡½Í”ÉÕ¹ÌÝ•É”ÍÁ±¥•Í½µ•Ý¡•É”(€€€…¹¹½Ñ¡¥¹œÍ…åÌÝ¡•É”¸Q¡”µ•Í Í¡½ÝÌ½¹”±½œÁ•È‰…ä¸€¨©0Èäµ½Ù•ÌÑ¼I•Í½±Ù•¨¨ƒŠP…¹½¹±ä(€€€¹½Ü°‰•…ÕÍ”Ñ¡”•¹ÑÉä¥ÑÍ•±˜Í…¥¥ÐÝ½Õ±ÍÑ…äÕ¹Ñ¥°Ñ¡”µ•Í Í¡½Ý•ÑÝ¼ÍÕÁÁ½ÉÑÌ¸(€€€€¨©=¹”±¥µ¥Ð½˜Ñ¡”µ•Í ¥ÌÝ½ÉÑ ÍÑ…Ñ¥¹œ½¸¥ÑÌ½Ý¸¨¨°‰•…ÕÍ”¥Ð¥ÌÑ¡”µ½ÍÐÍÁ•¥™¥ŒÁ¡É…Í”(€€€¥¸Ñ¡”Í½ÕÉ”¸€©I•ÍÑ¥¹œ½¸Ñ¡”‰½ÑÑ½´¨¥ÌÝ¡…Ð‘¥ÍÑ¥¹Õ¥Í¡•Ì„‰•¹Ð™É½´„‘É¥Ù•¸Á¥±”‰•¹Ð°(€€€…¹…‰½Ù”Ñ¡”Ý…Ñ•É±¥¹”Ñ¡”ÑÝ¼…É”Ñ¡”Í…µ”Á¥ÑÕÉ”ì}±½}‰•¹Ñ€‘¥™™•ÉÌ™É½´}Á¥±•}‰•¹Ñ€‰ä(€€€™½ÕÈ¡•…Ùä±½Ì……¥¹ÍÐÑ¡É•”±¥¡Ð½¹•Ì°Ý¡¥ ¥ÌÝ¡…Ð„Ù¥Í¥Ñ½È…¸…ÑÕ…±±äÍ•”¸Q¡”É•ÍÐ(€€€½˜Ñ¡”‘¥ÍÑ¥¹Ñ¥½¸±¥Ù•Ì¥¸Ñ¡”É•½É…¹¥¸Ñ¡¥Ì™¥±”¸((ÈÔ¸€¨©Q¡”™¥ÉÍÐ‰Õ¥±‘¥¹œÝ¡½Í”™½½ÑÁÉ¥¹Ð¥Ì•Ù¥‘•¹”°…¹„½ÉÉ•Ñ¥½¸Ñ¼½ÕÈ½Ý¸‘½ÍÍ¥•ÈÑ¡…Ð(€€€¡…¹•ÌÝ¡…Ð¥Ð¥Ì¸¨¨¡½…¹}ÍÑ½É•€ƒŠPÑ¡”±½œÍÑ½É”…ÐÑ¡”Ý•ÍÐ•¹½˜Ñ¡”1…­”MÑÉ••Ð‰±½¬(€€€¥¸Ý¡¥ Ñ¡”U¹¥Ñ•MÑ…Ñ•Ì½Á•¹•„Á½ÍÐ½™™¥”…Ð¡¥…¼½¸€ÌÄ5…É €ÄàÌÄƒŠP¥ÌÑ¡”•¥¡Ñ (€€€ÍÑÉÕÑÕÉ”…¹Ñ¡”™¥ÉÍÐ	U%1%9¡•É”Ý¡½Í”½ÕÑ±¥¹”¥Ì¹½Ð„Á±…•¡½±‘•È¸¹‘É•…Ì¥Ù•Ì¥ÑÌ(€€€Í¥é”ÑÝ¥”°¥¸ÑÝ¼¥¹‘•Á•¹‘•¹Ñ±äÝÉ¥ÑÑ•¸Á…ÍÍ…•Ìè€‰Q¡”‰Õ¥±‘¥¹œÝ…ÌÑÝ•¹Ñä‰ä™½ÉÑäµ™¥Ù”™••Ð(€€€¥¸Í¥é”°Ý…ÌÁ…ÉÑ¥Ñ¥½¹•½™˜Í¼…ÌÑ¼Í•ÉÙ”…Ì„Á½ÍÐµ½™™¥”½¸½¹”Í¥‘”°…¹…ÌÑ¡”ÍÑ½É”½˜(€€€	É•ÝÍÑ•È°!½…¸€˜¼¸°½¸Ñ¡”½Ñ¡•Èˆ°…¹€‰Ñ¡”ÍÑ½É”½¹±ä½ÕÁ¥•…¸…É•„½˜™½ÉÑäµ™¥Ù”‰ä(€€€ÑÝ•¹Ñä™••Ðˆ¸€ÐÔƒ\€ÈÀ™Ð¥Ì€ÄÌ¸ÜÄØƒ\€Ø¸ÀäØ´…¹Ñ¡”™½½ÑÁÉ¥¹Ð¥ÌÑ…•‘½Õµ•¹Ñ•‘€°Ý¡¥ (€€€¹¼‰Õ¥±‘¥¹œ™½½ÑÁÉ¥¹Ð¥¸Ñ¡¥Ì‘…Ñ…Í•Ð¡…Ì‰••¸‰•™½É”¸€¨©]¡…Ð¥Ì‘½Õµ•¹Ñ•¥ÌÑ¡”M%i…¹(€€€¹½ÐÑ¡”Á±…¸¨¨èÝ¡¥ …á¥ÌÉÕ¹Ì…±½¹œÑ¡”ÍÑÉ••Ð¥Ì¹½‰½‘äÌ•Ù¥‘•¹”°Í¼Ñ¡…Ð…ÍÍ¥¹µ•¹ÐÍ¥ÑÌ(€€€½¸Ñ¡”™……‘”‰•…É¥¹œ¥¸Ñ¡”Á½Í¥Ñ¥½¸¹½Ñ”°Ý¡•É”É½Ñ…Ñ¥¹œÑ¡”‰Õ¥±‘¥¹œ¥ÌÝ¡…Ð¡…¹•Ì¥Ð¸(€€€€¨©Q¡¥Ì¥Ì…±Í¼Ñ¡”™¥ÉÍÐÉ•½É¡•É”Ý¥Ñ ¹½Ñ¡¥¹œ½¹©•ÑÕÉ…°¥¸¥Ð¨¨°Ý¡¥ ¥Ì¹½Ð„‰½…ÍÐƒŠP(€€€¥Ðµ•…¹Ì¥ÑÌ…ÁÌ…É”…ÁÌ¥¸Ñ¡”Í½ÕÉ•ÌœÁÉ•¥Í¥½¸É…Ñ¡•ÈÑ¡…¸¡½±•Ì™¥±±•‰ä¥¹Ù•¹Ñ¥½¸¸(€€€%Ð‘½•Ìµ•…¸Ñ¡”Á½ÁÕÀÌ•µÁÑä€‰]¡…ÐÝ”µ…‘”ÕÀ¡•É”ˆÍÑ…Ñ”¥Ì™¥¹…±±ä•á•É¥Í•‰äÉ•…°‘…Ñ„°(€€€Ý¡¥ ƒ
œ€ÄÄÉ•½É‘•…ÌÕ¹•á•É¥Í•¸(€€€€¨©Q¡”½ÉÉ•Ñ¥½¸¥ÌÑ¡”µ½É”ÕÍ•™Õ°¡…±˜¸¨¨‘½Ì½É•Í•…É ¼ÀÌµÍÑÉÕÑÕÉ•Ìµ¹½ÉÑ ¹µ‘€ƒ
œ€Ð‘…Ñ•Ì(€€€Ñ¡”Á½ÍÐ½™™¥”Ìµ½Ù”Ñ¼Ñ¡”É…¹­±¥¸…¹M½ÕÑ ]…Ñ•È…‘‘É•ÍÌ™É½´€È9½Ù•µ‰•È€ÄàÌÈ°Ñ¡”‘…ä(€€€!½…¸ÍÕ••‘•	…¥±•ä…ÌÁ½ÍÑµ…ÍÑ•È°…¹…±±ÌÑ¡…ÐÑ¡”€ÄàÌÔ½™™¥”¸¹‘É•…ÌÍ…åÌÑÝ¥”Ñ¡…Ð(€€€Ñ¡”½™™¥”Ý…ÌÍÑ¥±°…Ð1…­”…¹M½ÕÑ ]…Ñ•ÈÑ¡É½Õ €ÄàÌÌ…¹µ½Ù•€¨©…‰½ÕÐ)Õ±ä€ÄàÌÐ¨¨¸Q¡”(€€€‘½ÍÍ¥•ÈÌ½¹±ÕÍ¥½¸ÍÕÉÙ¥Ù•Ì…¹¥ÑÌ¡É½¹½±½ä‘½•Ì¹½ÐèÑ¡”€ÄàÌÈ‘…Ñ”¥ÌÑ¡”Á½ÍÑµ…ÍÑ•ÈÌ°(€€€¹½ÐÑ¡”‰Õ¥±‘¥¹œÌ¸Q¡”½¹™±…Ñ¥½¸¥ÌÑÉ…•…‰±”Ñ¼Ñ¡”ÕÉÉ•äÁ…”Ñ¡”‘½ÍÍ¥•ÈÕÍ•°Ý¡¥ (€€€µ…­•ÌÑ¡”…ÁÁ½¥¹Ñµ•¹Ð…¹Ñ¡”µ½Ù”½¹”Í•¹Ñ•¹”ƒŠP…¹Ý¡¥ …±Í¼ÍÕÁÁ±¥•ÌÑ¡”€‰Í½ÕÑ Ý•ÍÐ(€€€½É¹•ÈˆÑ¡…Ð¹‘É•…Ì¹•Ù•È¥Ù•Ì¸M½ÕÉ”É•½É¡¥…½±½å}™¥ÉÍÑ}Á½ÍÑ}½™™¥•€Í…åÌ½¸¥ÑÌ(€€€½Ý¸™…”Ý¡•É”¥Ð¥Ì™½±±½Ý•…¹Ý¡•É”¥Ð¥Ì¹½Ð¸€¨©Q¡”½¹Í•ÅÕ•¹”™½ÈÑ¡”Í•¹”¨¨è½¸(€€€€ÄàÌÔ´ÀÜ´ÀÄÑ¡¥Ì‰Õ¥±‘¥¹œ¥Ì„ÍÑ½É”Ñ¡…ÐÕÍ•Ñ¼‰”Ñ¡”Á½ÍÐ½™™¥”°…¹Ñ¡”Ñ½Ý¸Ì…ÑÕ…°(€€€Á½ÍÐ½™™¥”¥Ì„‘¥™™•É•¹Ð°Õ¹µ½‘•±±•‰Õ¥±‘¥¹œ…‰½ÕÐ€ÄÀÀ´•…ÍÐ°½˜Ý¡¥ ¹½Ñ¡¥¹œÍÕÉÙ¥Ù•Ì(€€€‰ÕÐ„ÍÑÉ••Ð©Õ¹Ñ¥½¸ƒŠP¥ÐÝ½Õ±‰”Ñ¡”µ½ÍÐ¥¹Ù•¹Ñ•‰Õ¥±‘¥¹œ¥¸Ñ¡”‘…Ñ…Í•Ð…¹¥Ð¥Ì(€€€ÝÉ¥ÑÑ•¸‘½Ý¸É…Ñ¡•ÈÑ¡…¸‰Õ¥±Ð€¡‘½Ì½IMI ½¡½…¹}ÍÑ½É”¹µ‘€ƒ
œ€Ð¤¸(€€€€¨©Q¡”Ý•…¬Á½¥¹Ð¥ÌÍÕÉÙ¥Ù…°°¹½Ð•½µ•ÑÉä°…¹¥Ð¥ÌÍÑ…Ñ•½¸Ñ¡”É•½É¸¨¨Q¡”‰Õ¥±‘¥¹œ¥Ì(€€€…ÑÑ•ÍÑ•ÍÑ…¹‘¥¹œÑ¼…‰½ÕÐ)Õ±ä€ÄàÌÐ…¹¹¼Í½ÕÉ”É•…¡•™½±±½ÝÌ¥ÐÁ…ÍÐÑ¡…Ðì¥Ð¥ÌÁ±…•(€€€¥¸„Í•¹”Í•Ð•±•Ù•¸µ½¹Ñ¡Ì±…Ñ•È½¸Ñ¡”½¹Ñ¥¹Õ¥Ñä…ÉÕµ•¹Ð°Ý¥Ñ Ñ¡”½Õ¹Ñ•Èµ…ÉÕµ•¹ÐƒŠP(€€€1…­”…¹M½ÕÑ ]…Ñ•ÈÝ…ÌÑ¡”½É¹•Èµ½ÍÐ•áÁ½Í•Ñ¼Ñ¡”€ÄàÌÔ‰½½´ƒŠP¥¸Ñ¡”Í…µ”¹½Ñ”¸%˜(€€€•Ù¥‘•¹”ÑÕÉ¹ÌÕÀÑ¡…Ð¥Ð…µ”‘½Ý¸™¥ÉÍÐ°¥Ð‰•±½¹Ì¥¸•á±ÕÍ¥½¹Ì¹©Í½¹€…¹Ñ¡¥ÌÉ•½É(€€€±•…Ù•ÌÑ¡”Í•¹”¸(€€€€¨©=¹”Íµ…±±•ÈÑ¡¥¹œ…µ”½ÕÐ½˜Ñ¡”Í…µ”Á…”…¹¥ÌÉ•½É‘•É…Ñ¡•ÈÑ¡…¸…Ñ•½¸¸¨¨ÕÉÉ•ä(€€€¡…ÌQ¡½µÁÍ½¸Ì€ÄàÌÀÁ±…Ð±…å¥¹œ½ÕÐÍÑÉ••ÑÌ€‰Õ¹¥™½Éµ±ä€ØØ™••ÐÝ¥‘”ˆì•Ù•ÉäÁ½Í¥Ñ¥½¸¥¸Ñ¡¥Ì(€€€‘…Ñ…Í•Ð½™™Í•ÑÌ‰ä¡…±˜½˜…¸€¨¨àÀ™Ð¨¨ÍÑÉ••Ð°™É½´Ñ¡”Ý¥‘Ñ¡Ì…¹¹½Ñ…Ñ•½¸!…Ñ¡…Ý…ä€ÄàÌÐ¸(€€€Q¡”‘¥™™•É•¹”¥Ì€È¸Ä´°…¸½É‘•È½˜µ…¹¥ÑÕ‘”¥¹Í¥‘”Ñ¡”•½É•™•É•¹”Ì½Ý¸•ÉÉ½È°Í¼¹½Ñ¡¥¹œ(€€€µ½Ù•ÌƒŠP‰ÕÐÑ¡”ÑÝ¼…¹¹½Ð‰½Ñ ‰”É¥¡Ð…‰½ÕÐÑ¡”Í…µ”ÍÑÉ••Ð°…¹Ñ¡”É•½¹¥±¥…Ñ¥½¸Ý½ÉÑ (€€€Ñ•ÍÑ¥¹œ¥ÌÑ¡…ÐÑ¡•ä…É”¹½Ð…‰½ÕÐÑ¡”Í…µ”ÍÑÉ••Ð¸M•”‘½Ì½IMI ½¡½…¹}ÍÑ½É”¹µ‘€ƒ
œ€Ô¸((ÈØ¸€¨©]¡…ÐÝ…Ì±•™Ð½ÕÐ¥ÌÉ•…‘…‰±”¥¸Ñ¡”Ý…±­Ñ¡É½Õ °…¹•¹™½É¥¹œ¥Ð™½Õ¹Ñ¡”½¹”™¥±”(€€€Ý¡•É”ÉÕ±”½¹”Ý…Ì¹•Ù•È¡•­•¸¨¨‘…Ñ„½•á±ÕÍ¥½¹Ì¹©Í½¹€ƒŠP™½ÕÉÑ••¸É•Í•…É¡•(€€€ÍÑÉÕÑÕÉ•ÌÝ¥Ñ Ñ¡”•Ù¥‘•¹”Ñ¡…Ð‘…Ñ•ÌÑ¡•´°Á±ÕÌ„™½ÕÈµ¥Ñ•´Ý…Ñ ±¥ÍÐƒŠP¡…Ì•á¥ÍÑ•(€€€Í¥¹”Ñ¡”Í…™™½±…¹¡…Ì‰••¸É•…‰ä…•¹ÑÌ½¹±ä¸Ù¥Í¥Ñ½ÈÍÑ…¹‘¥¹œ¥¸…¸•µÁÑä±½Ð(€€€…¹¹½Ð‘¥ÍÑ¥¹Õ¥Í Ñ¡É•”‘¥™™•É•¹ÐÍÑ…Ñ•µ•¹ÑÌè¹½‰½‘äÉ•Í•…É¡•Ñ¡¥Ì°Ñ¡”•Ù¥‘•¹”(€€€‘…Ñ•Ì¥Ð…™Ñ•ÈÑ¡”Í•¹”°½È¥Ð¡……±É•…‘ä½µ”‘½Ý¸¸Q¡”™¥ÉÍÐ¥Ì„…À¥¸Ñ¡”Ý½É¬(€€€…¹Ñ¡”½Ñ¡•ÈÑÝ¼…É”™¥¹‘¥¹ÌÑ¡…Ð½ÍÐÉ•Í•…É Ñ¼•ÍÑ…‰±¥Í ¸Q¡”Ù¥‘•¹”Á…¹•°¹½Ü(€€€…ÉÉ¥•ÌÑ¡•´Õ¹‘•È€¨©]¡…Ð¥Ì¹½Ð¡•É”¨¨°‘•É¥Ù•Á•ÈÍ•¹”‰ä½µÁ¥±•}Í•¹”¹Áå€Ý¥Ñ (€€€Ñ¡”¥Ñ…Ñ¥½¹Ì©½¥¹•°‰•±½ÜÑ¡”±¥‰•ÉÑ¥•Ì…¹¥¸Ñ¡”Í…µ”€ñ‘•Ñ…¥±Ìù€•¹ÑÉä°‰•…ÕÍ”(€€€Ñ¡•ä…É”Ñ¡”Í…µ”­¥¹½˜‘¥Í±½ÍÕÉ”¸(€€€€¨©Q¡”¡¥À¥ÌÑ¡”É•½ÉÌ™¥•±°¹•Ù•È„Á¡É…Í”‘•É¥Ù•™É½´…¸…‰Í•¹”¸¨¨Q•¸•¹ÑÉ¥•Ì(€€€…ÉÉä•…É±¥•ÍÑ}Í•¹•€…¹Í¡½Ü€‰¹½ÐÕ¹Ñ¥°€ÄàÌÜˆì­¥¹é¥•}¡½ÕÍ•€…¹½Õ¥±µ•ÑÑ•}…‰¥¹€(€€€Ý•É”•á±Õ‘•‰•…ÕÍ”Ñ¡•äÝ•É”=9°…ÉÉä¹¼ÍÕ ™¥•±°…¹•Ð¹¼¡¥ÀƒŠPÍÑ…µÁ¥¹œ(€€€½¹”½¸Ñ¡•´Ý½Õ±‰”…¸¥¹Ù•¹Ñ¥½¸½¸Ñ¡”Á…¹•°Ñ¡…Ð•á¥ÍÑÌÑ¼…‘µ¥Ð¥¹Ù•¹Ñ¥½¹Ì¸Q¡”(€€€Íµ½­”…ÍÍ•ÉÑÌÑ¡…Ð‘¥ÍÉ¥µ¥¹…Ñ¥¹œÁ…¥ÈÉ…Ñ¡•ÈÑ¡…¸„½Õ¹Ð°…¹…ÍÍ•ÉÑÌÑ¡…Ð„‰Õ¥±‘¥¹œ(€€€Ñ¡”Ù¥Í¥Ñ½È…¸Ý…±¬ÕÀÑ¼¥Ì€©¹½Ð¨½¸Ñ¡”±¥ÍÐ°Ý¡¥ „Í•Ñ¥½¸‘ÕµÁ¥¹œÑ¡”Ý¡½±”(€€€‘…Ñ…Í•ÐÝ½Õ±ÍÑ¥±°¡…Ù”Á…ÍÍ•¸(€€€€¨©Q¡”±¥ÍÐÍÑ…Ñ•ÌÝ¡…Ð¥Ð¥Ì¹½Ð¨¨°…¹Ñ¡…ÐÍ•¹Ñ•¹”¥Ì„Íµ½­”…ÍÍ•ÉÑ¥½¸Ñ½¼è•¥¡Ð½˜(€€€É½Õ¡±ä™½ÉÑäÉ•Í•…É¡•ÍÑÉÕÑÕÉ•ÌÍÑ…¹°Í¼„™½ÕÉÑ••¸µ¥Ñ•´±¥ÍÐ½˜…‰Í•¹•ÌÝ¥Ñ ¹¼(€€€ÍÕ ¹½Ñ”É•…‘Ì…Ì€‰Ñ¡¥Ì¥ÌÝ¡…Ð¥Ìµ¥ÍÍ¥¹œˆ°Ý¡¥ Ý½Õ±‰”Ñ¡”±…É•ÍÐ™…±Í”±…¥´Ñ¡”(€€€Á…¹•°½Õ±µ…­”¸(€€€€¨©QÝ¼ÉÕ±•Ì…ÉÉ¥Ù•Ý¥Ñ ¥Ð°…¹Ñ¡”™¥ÉÍÐ¥Ì•µ‰…ÉÉ…ÍÍ¥¹œ¥¸Ñ¡”ÕÍ•™Õ°Ý…ä¸¨¨9QL¹µ(€€€ÉÕ±”€Ä¥ÌÑ¡…Ð•Ù•ÉäÍ½ÕÉ•}¥‘€É•Í½±Ù•Ì¥¸‘…Ñ„½Í½ÕÉ•Ì½€ì•á±ÕÍ¥½¹Ì¹©Í½¹€Ý…ÌÑ¡”(€€€½¹”™¥±”Ý¡•É”¹½Ñ¡¥¹œ•¹™½É•¥Ð°‰•…ÕÍ”Õ¹Ñ¥°¹½Ü¹½Ñ¡¥¹œÉ•…¥ÐƒŠP„¥Ñ…Ñ¥½¸Ñ¡•É”(€€€½Õ±¡…Ù”¹…µ•„Í½ÕÉ”Ñ¡…Ð¹•Ù•È•á¥ÍÑ•…¹Ñ¡”…Ñ”Ý½Õ±¡…Ù”ÍÑ…å•É••¸¸(€€€¡•­}•á±ÕÍ¥½¹Í€¡½±‘Ì¥ÐÑ¼Ñ¡”Í…µ”ÍÑ…¹‘…É…Ì„ÍÑÉÕÑÕÉ”É•½Éè„Í±Õœ¥°„(€€€¹…µ”°„ÍÑ…Ñ•É•…Í½¸€¡…¸•á±ÕÍ¥½¸Ý¥Ñ¡½ÕÐ½¹”¥Ì„‘•±•Ñ¥½¸Ý¥Ñ „™¥±•¹…µ”¤°…¹…Ð(€€€±•…ÍÐ½¹”¥Ñ…Ñ¥½¸Ñ¡…ÐÉ•Í½±Ù•Ì¸Q¡”½µµ¥ÑÑ•™¥±”Á…ÍÍ•ÌÕ¹¡…¹•ìÑ¡”Ù…±Õ”¥ÌÑ¡…Ð(€€€Ñ¡”¹•áÐ•¹ÑÉä…¹¹½Ð¸Q¡”Í•½¹¥ÌÑ¡”‘…Ñ”…Ñ”É•…‰…­Ý…É‘Ìè…¸•¹ÑÉä‘…Ñ¥¹œ„(€€€‰Õ¥±‘¥¹œÑ¼€ÄàÌÜ¥Ì„½ÉÉ•Ð•á±ÕÍ¥½¸™É½´€ÄàÌÔ…¹„]I=9½¹”™É½´€ÄàÌÜ°…¹¹¼(€€€½µÁ…É¥Í½¸……¥¹ÍÐÑ¡”É•½É‘Ì…¸…Ñ ¥Ð‰•…ÕÍ”…¸•á±Õ‘•ÍÑÉÕÑÕÉ”¡…Ì¹¼É•½É(€€€Ñ¼½µÁ…É”Ý¥Ñ ¸%¸„å•…ÈµÁ…É…µ•Ñ•É¥é•ÁÉ½©•ÐÑ¡…Ð¥Ì•á…Ñ±äÑ¡”¡•¬Ý½ÉÑ ¡…Ù¥¹œ(€€€‰•™½É”Ñ¡”Í•½¹Í•¹”•á¥ÍÑÌÉ…Ñ¡•ÈÑ¡…¸…™Ñ•È¸(€€€€¨©Q¡”Ý…Ñ ±¥ÍÐ¥Ì‘•±¥‰•É…Ñ•±ä¹½ÐÍ¡½Ý¸¸¨¨%ÑÌ™½ÕÈ¥Ñ•µÌ…É”ÍÑÉÕÑÕÉ•ÌÝ¡½Í”€ÄàÌÔ(€€€ÍÑ…ÑÕÌ¥ÌÕ¹•ÉÑ…¥¸É…Ñ¡•ÈÑ¡…¸Í•ÑÑ±•°…¹½¹”½˜Ñ¡•´€¡Ý•ÍÑ•É¹}¡½Ñ•±€¤¥ÌÍÑ…¹‘¥¹œ¥¸(€€€Ñ¡”Í•¹”ƒŠPÁÕÑÑ¥¹œÑ¡•´Õ¹‘•È€‰Ý¡…Ð¥Ì¹½Ð¡•É”ˆÝ½Õ±‰”™…±Í”…‰½ÕÐÑ¡”½¹”Ñ¡¥¹œÑ¡”(€€€Í•Ñ¥½¸¥Ì™½È¸Q¡•¥ÈÕ¹•ÉÑ…¥¹Ñä‰•±½¹Ì½¸Ñ¡”É•½É‘Ì…¹¥¸Ñ¡”ÁÉ½Ù•¹…¹”Á½ÁÕÀ°(€€€Ý¡¥ ¥Ì„‘¥™™•É•¹ÐÍ±¥”…¹¥Ì¹½ÐÅÕ•Õ•¸(ÈÜ¸€¨©Q¡”Í¥‘•…ÉÌ…É”É”µ‘•É¥Ù•‰äÑ¡”…Ñ”¹½Ü°Ý¡¥ Ñ¡•äÝ•É”¹½Ð¸¨¨½µÁ¥±•}Í•¹”¹Áå€(€€€ÝÉ¥Ñ•ÌÝ¡…ÐÑ¡”É•¹‘•É•ÈÉ•…‘Ì…¹Ñ¡”½ÕÑÁÕÑÌ…É”½µµ¥ÑÑ•Í¼Ñ¡”Í¥Ñ”¹••‘Ì¹¼‰Õ¥±(€€€ÍÑ•ÀƒŠP…¸…ÉÉ…¹•µ•¹ÐÑ¡…Ð½¹±ä¡½±‘Ì¥˜‘É¥™Ð¥Ì„™…¥±ÕÉ”¸9½Ñ¡¥¹œÉ•½µÁÕÑ•Ñ¡•´°Í¼(€€€„É•½É•‘¥Ñ•Ý¥Ñ¡½ÕÐ„É•½µÁ¥±”Í¡¥ÁÁ•„Ý…±­Ñ¡É½Õ ÅÕ½Ñ¥¹œÑ¡”ÁÉ•Ù¥½ÕÌ‘…Ñ…Í•Ð(€€€Ý¥Ñ •Ù•Éä¥Ñ…Ñ¥½¸ÍÑ¥±°±½½­¥¹œ…ÕÑ¡½É¥Ñ…Ñ¥Ù”¸€´µ¡•­€É”µ‘•É¥Ù•ÌÑ¼µ•µ½Éä…¹(€€€½µÁ…É•Ìì¡•¬¹Í¡€ÉÕ¹Ì¥Ð°Ñ¡”Í…µ”Ý…ä¥Ð…±É•…‘äÉ”µ‘•É¥Ù•±¥‰•ÉÑ¥•Ì¹©Í½¹€¸Q¡”(€€€•¥¡Ð½µµ¥ÑÑ•Í¥‘•…ÉÌ…¹Ñ¡”¥¹‘•àÝ•É”‰åÑ”µ¥‘•¹Ñ¥…°½¸Ñ¡”™¥ÉÍÐÉÕ¸°Í¼Ñ¡¥Ì(€€€ÍÝ¥Ñ¡•½¸Ý¥Ñ ¹¼É•Á…¥È‰•¡¥¹¥Ð¸]¡…Ð¥Ð‘½•Ì9=P¡•¬¥ÌÑ¡”‘¥É•Ñ¥½¸Ñ¡”(€€€ÍÑ…±•¹•ÍÌ…Ñ”½Ù•ÉÌƒŠPÑ¡…ÐÑ¡”1µ…Ñ¡•ÌÑ¡”É•½ÉƒŠP…¹¹•¥Ñ¡•È½˜Ñ¡•´…¸Í•”„(€€€É•½ÉÑ¡…Ð¥ÌÝÉ½¹œ…‰½ÕÐÑ¡”Ñ½Ý¸¸((ŒŒ9•áÐ((¨©LÔƒŠPµ½É”ÍÑÉÕÑÕÉ”É•½É‘Ì¨¨°Ý¡¥ ¥Ì¹½ÜÑ¡”‰¥¹‘¥¹œ½¹ÍÑÉ…¥¹ÐèÍ•Ù•¸ÍÑÉÕÑÕÉ•ÌÍÑ…¹)Ý¡•É”Ñ¡”Í½ÕÉ•Ì‘•ÍÉ¥‰”É½Õ¡±ä™½ÉÑä°…¹½¹”½˜Ñ¡”Í•Ù•¸¥Ì„‰É¥‘”¸9½Ñ”Ñ¡”½ÕÁ±¥¹œ‘¥Í½Ù•É•½¸€ÈÀÈØ´Àà´ÄÀ°‰•…ÕÍ”¥ÐÍ•ÑÌ)Ñ¡”Í¡…Á”½˜Ñ¡”Ý½É¬èÑ½½±Ì½½µÁ¥±•}Í•¹”¹Áå€ÝÉ¥Ñ•Ì…¸…ÍÍ•Ñ€Á…Ñ ™½È•Ù•ÉäÍÑÉÕÑÕÉ”Ñ¡…Ð)É•Í½±Ù•Ì¥¹Ñ¼Ñ¡”Í•¹”°Í¼„É•½É½µµ¥ÑÑ•Ý¥Ñ¡½ÕÐ¥ÑÌ1µ…­•ÌÑ¡”É•¹‘•É•È™•Ñ „™¥±”)Ñ¡…Ð¥Ì¹½ÐÑ¡•É”ƒŠP„€ÐÀÐÑ¡”Íµ½­”½ÉÉ•Ñ±ä™…¥±Ì½¸¸€¨©ÍÑÉÕÑÕÉ”É•½É…¹¥ÑÌ‰…­”…É”½¹”)Õ¹¥Ð¸¨¨¸…•¹ÐÝ¥Ñ¡½ÕÐ	±•¹‘•È…¸ÁÉ•Á…É”Ñ¡”É•½É…¹Ñ¡”É•Í•…É µ•µ¼°‰ÕÐÑ¡”Á…¥È¡…Ì)Ñ¼±…¹Ñ½•Ñ¡•È°Í¼Ñ¡”‰…­”Ý½É­™±½ÜÌAH¥ÌÁ…ÉÐ½˜Ñ¡”Í…µ”Í±¥”É…Ñ¡•ÈÑ¡…¸„™½±±½ÜµÕÀ¸(¨©Q¡…Ð½ÕÁ±¥¹œ¥Ì¹½Ü•¹™½É•É…Ñ¡•ÈÑ¡…¸É•µ•µ‰•É•¨¨€ ÈÀÈØ´Àà´ÄÀ¤è•‘¥Ñ¥¹œ„Ù…±Õ”„)•¹•É…Ñ½ÈÉ•…‘Ìµ…­•ÌÑ¡”½µµ¥ÑÑ•1ÍÑ…±”…¹¡•¬¹Í¡€™…¥±ÌÕ¹Ñ¥°Ñ¡”É”µ‰…­”±…¹‘ÌÝ¥Ñ )¥Ð¸%ÐÝ…ÌÑ¡•¸•á•É¥Í•™½ÈÉ•…°‰äÑ¡”]½±˜A½¥¹ÐÉ•Á…¥ÈÑ¡”Í…µ”‘…äƒŠPÑ¡”É•¹…µ”ÑÕÉ¹•Ñ¡”)Ñ…Ù•É¸Ì…ÍÍ•ÐÍÑ…±”½¸Ñ¡”ÍÁ½Ð…¹Ñ¡”‰É…¹ ½Õ±¹½Ð¼É••¸Õ¹Ñ¥°Ñ¡”‰…­”±…¹‘•½¸¥Ð°)Ý¡¥ ¥ÌÑ¡”Ý¡½±”Á½¥¹Ð½˜ÝÉ¥Ñ¥¹œÑ¡”¡•¬°…¹……¥¸Ñ¡”Í…µ”‘…ä‰ä5¥±±•ÈÌÍ•½¹¡¥µ¹•ä°)…¹„Ñ¡¥ÉÑ¥µ”‰ä¡¥Ì™É…µ”É…¹”¸(¨©Q¡”É•Á…¥È±¥ÍÐÉ•™¥±±•¥ÑÍ•±˜™É½´Ñ¡”…É¡¥Ù”É…Ñ¡•ÈÑ¡…¸™É½´Ñ¡”…Ñ•Ì°…¹•µÁÑ¥•……¥¸)Ñ¡”Í…µ”‘…ä¨¨€ ÈÀÈØ´Àà´ÄÀ°ƒ
œ€ÈÌƒŠHƒ
œ€ÈÐ¤¸Ù•ÉäÁÉ•Ù¥½ÕÌ•¹ÑÉä½¸¥ÐÝ…Ì™½Õ¹‰ä„¡•¬è„)µ¥ÍÍÁ•±±•…ÑÑÉ¥‰ÕÑ”°„¹…µ”É•……Ì‰•¥¹œ…‰½ÕÐÑ¡”ÝÉ½¹œ¡…±˜½˜„‰Õ¥±‘¥¹œ¸Q¡…Ð½¹”Ý…Ì™½Õ¹)‰äÉ•…‘¥¹œ„Á…”°…¹¥Ð¥Ì¹½Ü€¨©=9¨¨ƒŠPÑ¡”É•½É°Ñ¡”…É¡•ÑåÁ”…¹Ñ¡”‰…­”±…¹‘•)Ñ½•Ñ¡•È°Á¥•É}½Õ¹Ðè€É€É•Á±…•Á¥•É}ÍÁ…¥¹}µ€°…¹Ñ¡”ÅÕ•Õ”¥Ì•µÁÑä……¥¸¸]¡…Ð¥Ð±•…Ù•Ì)‰•¡¥¹¥Ì„Í¡…Á”Ý½ÉÑ É•ÕÍ¥¹œÉ…Ñ¡•ÈÑ¡…¸„Ñ…Í¬èÝ¡•¸•Ù¥‘•¹”…¹…¸…É¡•ÑåÁ”‘¥Í…É•”°¡•¬)Ý¡•Ñ¡•ÈÑ¡”…É¡•ÑåÁ”¥Ì…Í­¥¹œ™½ÈÑ¡”ÝÉ½¹œ€©­¥¹¨½˜¹Õµ‰•È‰•™½É”¡…¹¥¹œÑ¡”¹Õµ‰•È¥Ð¡…Ì¸)Q¡”½±‘•È…½Õ¹Ð½˜Ñ¡”ÅÕ•Õ”°ÍÑ¥±°ÑÉÕ”½˜•Ù•ÉåÑ¡¥¹œ‰•™½É”Ñ¡¥Ì•¹ÑÉäèQ¡”±…ÍÐ•¹ÑÉäƒŠP)µ¥±±•É}¡½ÕÍ•€É•½É‘¥¹œ„‘½Õµ•¹Ñ•‘€™É…µ”É…¹”Ý¥Ñ ¹¼Í¥‘”°Ý¥‘Ñ °‘•ÁÑ ½ÈÍÑ½É•ä½Õ¹ÐƒŠP)±…¹‘•€ÈÀÈØ´Àà´ÄÀÝ¥Ñ ¥ÑÌ‰…­”€£
œ€ÈÀ¤°…¹¥ÐÝ…ÌÑ¡”™½ÕÉÑ …¹±…ÍÐ½˜Ñ¡”™…Õ±ÑÌÑ¡”½µ¥ÍÍ¥½¸)…Ñ”½Á•¹•¸Q¡É•”½˜Ñ¡”™½ÕÈÝ•É”ÍÁ•±±¥¹œìÑ¡”™½ÕÉÑ Ý…Ì„¹…µ”É•……Ì‰•¥¹œ…‰½ÕÐÑ¡”ÝÉ½¹œ)¡…±˜½˜„ÑÝ¼µÁ…ÉÐ‰Õ¥±‘¥¹œ°Ý¡¥ ¹¼ÍÁ•±±¥¹œ¡•¬Ý½Õ±¡…Ù”…Õ¡Ð¸9½Ñ¡¥¹œ¹•Ü¥ÌÅÕ•Õ•)‰•¡¥¹¥Ð°Í¼€¨©LÔ¥Ì…‘‘¥Ñ¥½¹Ì……¥¸¨¨è•¥¡Ð…É¡•ÑåÁ•Ì…¹…‰½ÕÐ™½ÉÑäÉ•Í•…É¡•ÍÑÉÕÑÕÉ•Ì)……¥¹ÍÐÑ¡”Í¥àÑ¡…ÐÍÑ…¹¸((¨©LäƒŠPÍÑÉ••ÑÌ°É½…‘Ì…¹Á…Ñ¡Ì¨¨°€¨©%IMPY%M%	1M1%=9€ÈÀÈØ´Àà´ÄÄ¸¨¨M•Ù•¹Ñ••¸‘…Ñ•)•…ÉÑ ÑÉ…Ù•±Ý…åÌ…É”½µÁ¥±•™É½´‘…Ñ„½ÍÑÉ••ÑÌ¼ÄàÌÔ¹©Í½¹€°‘É…Á•É…Ñ¡•ÈÑ¡…¸™±…ÑÑ•¹•°…¹)¥‘•¹Ñ¥™¥•±¥Ù”Ý¥Ñ Ñ¡•¥È€ÄàÌÔ…¹€ÈÀÈØ¹…µ•Ì¸Q¡”•…É±¥•ÈÍ•¹Ñ•¹”¡•É”Í…å¥¹œ€‰¹½Ñ¡¥¹œÝ…Ì)É…‘•Õ¹Ñ¥°€ÄàÔÔ´Ôàˆ½¹™ÕÍ•Ñ¡”±…Ñ•ÈI…¥Í¥¹œ½˜¡¥…¼Ý¥Ñ •…É±äÍÑÉ••ÐÝ½É¬…¹Ý…Ì)ÝÉ½¹œèM½ÕÑ ]…Ñ•ÈÝ…Ì½É‘•É•Á¥Ñ¡•‰äÁÉ¥°€ÄàÌÐ…¹É…‘•™½È‘É…¥¹…”Ñ¡…Ð)Õ±äìM½ÕÑ )]…Ñ•È…¹1…­”Ý•É”Ñ¡”ÑÝ¼•…É±äÁÉ¥¹¥Á…°¥µÁÉ½Ù•É½ÕÑ•Ì¸]¡…ÐÉ•µ…¥¹Ì¥ÌÑ¡”¹½ÉÑ µÍ¥‘”)½¹ÑÉ½°½•áÑ•¹ÐÉ•Í•…É °…¹äÍ•Á…É…Ñ•±ä…ÑÑ•ÍÑ•Á±…¹¬™½½ÑÝ…±­Ì°…¹•Ù¥‘•¹”Ñ¡…Ð½Õ±É•Á±…”)Ñ¡”½¹©•ÑÕÉ…°ÑÉ…Ù•±±•Ý¥‘Ñ¡Ì…¹ÉÕÐÁ…ÑÑ•É¹ÌÉ•½É‘•¥¸0Üä¸M•”I=5@ƒ
œLä¸((¨©LÕ„ƒŠP½ÉÐ•…É‰½É¸¨¨ƒŠP€¨©=9€ÈÀÈØ´Àà´ÄÄ¨¨°‰½Ñ …Ñ•Ì±•…É•‰•™½É”…¹ä•½µ•ÑÉä¸(¨©Q¡”™½½ÑÁÉ¥¹Ð¡…Ì„Í½ÕÉ”¸¨¨¸!…ÉÉ¥Í½¸)È¸ÌÍÕÉÙ•ä½˜Ñ¡”µ½ÕÑ ½˜Ñ¡”¡¥…¼I¥Ù•È™½È)Ñ¡”¡…É‰½ÕÈÝ½É­Ì°€ÈÐ•‰ÉÕ…Éä€ÄàÌÀ°…ÁÁÉ½Ù•‰ä]¥±±¥…´!½Ý…É°T¹L¸¥Ù¥°¹¥¹••È°É•ÁÉ½‘Õ•)¥¸¹‘É•…ÌÙ½°¸€ÄÀ¸€ÄÄÌ…¹±¥ÍÑ•¥¸Ñ¡…ÐÙ½±Õµ”Ì½Ý¸Ñ…‰±”½˜µ…ÁÌ…Ì€‰½ÉÐ•…É‰½É¸¥¸(ÄàÌÀ´ÌÈˆ¸%Ð‘É…ÝÌÑ¡”™½ÉÐ%8A18ƒŠPÍÅÕ…É”•¹±½ÍÕÉ”°Ý½É­Ì…ÐÑ¡É•”…¹±•Ì°™½ÕÈÉ…¹•Ì°ÑÝ¼)…Ñ•Ì°ÑÝ¼‰Õ¥±‘¥¹Ì™±…¹­¥¹œÑ¡”Í½ÕÑ …Ñ”ƒŠP…¹¥ÑÌ…ÉÉ…¹•µ•¹Ð¥Ì½ÉÉ½‰½É…Ñ•‰Õ¥±‘¥¹œ‰ä)‰Õ¥±‘¥¹œ‰äÕÉ‘½¸!Õ‰‰…ÉÌ€ÄàÈÜÝ…±¬É½Õ¹Ñ¡”¥¹Í¥‘”€¡¹‘É•…ÌÀ¸€ÈØÐ¤¸I•½É‘•…Ì)¡…ÉÉ¥Í½¹|ÄàÌÁ}É¥Ù•É}µ½ÕÑ¡€¸€¨©Q¡”Á±…Ñ”¡…Ì¹¼Í…±”‰…È¨¨°Í¼Ñ¡”Í…±”¥Ì‘•É¥Ù•™É½´Ñ¡”½¹”)ÍÑ…Ñ•‘¥µ•¹Í¥½¸¥¸Ñ¡”Ý¡½±”½µÁ±•àƒŠPÑ¡”½µµ…¹‘…¹ÐÌÅÕ…ÉÑ•ÉÌ…Ð€‰…‰½ÕÐ€ÈÔà€ÔÀ™Ðˆ¥¸Ñ¡”(ÄàÔÔÁ¡½Ñ½É…Á ­•äƒŠP¥Ù¥¹œ€Ä¸ÄÀ™Ð½Áà…¹„ÍÑ½­…‘”…‰½ÕÐ€ÔÌ´€ ÄÜÐ™Ð¤ÍÅÕ…É”…Ð€¨«
ÄÈÀ€”¨¨¸)QÝ¼¡•­Ì½¸Ñ¡”Í…µ”Á±…Ñ”…É•”Ñ¼€Ô€”…¹€ÄÄ€”¸€¨©Q¡”…ÉÉ¥Í½¸¥ÌÍ•ÑÑ±•¨¨è¡•±)½¹Ñ¥¹Õ½ÕÍ±ä™É½´)Õ¹”€ÄàÌÈÑ¼€Èä••µ‰•È€ÄàÌØ°5…¨¸)½¡¸É••¹”€ÕÑ %¹™…¹ÑÉäµ½ÍÐ±¥­•±ä)½µµ…¹‘¥¹œ½¸Ñ¡”Í•¹”‘…Ñ”°ÍÑÉ•¹Ñ …™Ñ•È€ÄàÌÌÕ¹…ÑÑ•ÍÑ•¸½ÕÉÑ••¸É•½É‘Ì°ÑÝ¼¹•Ü)…É¡•ÑåÁ•Ì€¡Á…±¥Í…‘•€°™½ÉÑ}ÍÑÉÕÑÕÉ•€¤°™½ÕÉÑ••¸‰…­•Ì°øÄÜ°ÀÀÀÑÉ¥…¹±•Ì¸¥Ù”•á±ÕÍ¥½¹Ì)Ý•¹Ð¥¸Ý¥Ñ ¥Ð°™½ÕÈ½˜Ñ¡•´ÝÉ½¹œµ™½ÉÐ™¥¹‘¥¹Ì¸M•”‘½Ì½IMI ½™½ÉÑ}‘•…É‰½É¸¹µ‘€¸(¨©]¡…Ð¥Ð‘¥9=PÍ•ÑÑ±”…¹Ý¡…Ð¥Ì¹½ÜÑ¡”‰¥¹‘¥¹œ½¹ÍÑÉ…¥¹ÐèÑ¡•É”¥Ì¹¼É½Õ¹Õ¹‘•È¥Ð¸¨¨((¨©LÉ”ƒŠP•áÑ•¹Ñ¡”É½Õ¹•…ÍÐÑ¼Ñ¡”±…­”¸¨¨I…¥Í•Ñ¼Ñ¡”Ñ½À½˜Ñ¡”Ñ•ÉÉ…¥¸Ý½É¬½¸(ÈÀÈØ´Àà´ÄÀ…Ð-•Ù¥¸Ì‘¥É•Ñ¥½¸°…™Ñ•È™É•”µ™±äµ…‘”¥ÐÙ¥Í¥‰±”™É½´Ñ¡”…¥ÈèÑ¡”µ½‘•±±•)‰½àÍÑ½ÁÌ…Ð±½…°€¬ÌÈÀ°Ý¡¥±”Ñ¡”½ÉÐ•…É‰½É¸Í¥Ñ”¥Ì…Ð€¬ÄÄÈÜ…¹Ñ¡”€ÄàÌÔÍ¡½É”¥Ì)…‰½ÕÐ„­¥±½µ•ÑÉ”™ÕÉÑ¡•ÈÍÑ¥±°¸½ÉÐ•…É‰½É¸…¹Ñ¡”¡…É‰½ÕÈÝ½É­Ì…¹¹½Ð‰”Á±…•Õ¹Ñ¥°)Ñ¡”É½Õ¹Õ¹‘•ÈÑ¡•´•á¥ÍÑÌ¸Q¡”Í¡½É•±¥¹”¥ÑÍ•±˜¥Ì„ÁÉ½Ù•¹…¹”ÁÉ½‰±•´‰•™½É”¥Ð¥Ì„)µ½‘•±±¥¹œ½¹”ƒŠP•Ù•ÉåÑ¡¥¹œ•…ÍÐ½˜É½Õ¡±ä5¥¡¥…¸Ù•¹Õ”¥Ì±…Ñ•È±…¹‘™¥±°°Í¼Ñ¡”•‘”)µÕÍÐ½µ”½™˜]É¥¡Ð€ÄàÌÐ°¹½Ð½™˜„µ½‘•É¸½…ÍÐ¸M•”I=5@ƒ
œLÉ”¸((¨©A…É•°€¡„¤¥Ì‘½¹”…¹Á…É•°€¡ˆ¤¥ÌÑ¡”¹•áÐÍ±¥”¸¨¨Q¡”Í¡½É”¥Ì¹½ÜÑÉ…•(¡Ñ½½±Ì½ÑÉ…•}Í¡½É•±¥¹”¹Áå€ƒŠHÍ¡½É•±¥¹”¹•½©Í½¹€°µ•µ¼)‘½Ì½IMI ½Í¡½É•±¥¹•}¡…É‰½É|ÄàÌÐ¹µ‘€¤…¹¥Ðµ½Ù•ÑÝ¼¹Õµ‰•ÉÌ½™˜•ÍÑ¥µ…Ñ”…¹½¹Ñ¼)µ•…ÍÕÉ•µ•¹ÐèÑ¡”µ…¥¹±…¹Í¡½É”É•…¡•Ì±½…°€¨©€¬ÄÈÔÜ¨¨…¹Ñ¡”Í…¹‰…ÈÌ•…ÍÐ•‘”(¨©€¬ÄÐäÜ¨¨°Í¼Ñ¡”É½…‘µ…ÀÌÁÉ½Á½Í•€¬ÄÔÀÀ‰½àÝ½Õ±¡…Ù”±¥ÁÁ•Ñ¡”‰…È‰ä€Ì´…¹Ñ¡”)‰½àÍ¡½Õ±‰”€¨¨¬ÄÔØÀ¨¨¸QÝ¼¥¹‘•Á•¹‘•¹ÐÍ•µ•¹Ñ…Ñ¥½¹Ì½˜Ñ¡”Í…µ”Í¡••Ð°¥¸‘¥™™•É•¹ÐÝ¥¹‘½ÝÌ)Ý¥Ñ ‘¥™™•É•¹Ð‰…­É½Õ¹ÍÑ…Ñ¥ÍÑ¥Ì°…É•”¥¸Ñ¡•¥È€àÀ´½Ù•É±…ÀÑ¼€¨¨À¸ÇŠLÔ¸Ü´¨¨½¸Ñ¡”Í½ÕÑ )‰…¹¬…¹€¨¨À¸×ŠLÄ¸Ì´¨¨½¸Ñ¡”¹½ÉÑ ƒŠPÝ½ÉÑ ÍÑ…Ñ¥¹œ‰•…ÕÍ”¥Ð¥Ì•Ù¥‘•¹”Ñ¡…ÐÑ¡”ÑÉ…”É•…‘Ì)Ñ¡”‘É…Õ¡ÑÍµ…¸Ì±¥¹”…¹¹½Ð¥ÑÌ½Ý¸Ñ¡É•Í¡½±‘Ì¸]¡…Ð¥ÌÍÑ¥±°…‰Í•¹Ðè€¨©¹¼•±•Ù…Ñ¥½¸•á¥ÍÑÌ)…¹åÝ¡•É”•…ÍÐ½˜€¬ÌÈÀ¨¨°Ñ¡”‰…È¥¹±Õ‘•¸‰…È¥Ì„ÍÕÉ™…”„½ÕÁ±”½˜™••Ð½˜±…­”ÍÑ…”)µ½Ù•Ì…¹¹¼Í½ÕÉ”¥Ù•Ì¥ÑÌ¡•¥¡Ð°Í¼Ñ¡”¹Õµ‰•ÈÝ¥±°¡…Ù”Ñ¼‰”…ÉÕ•¥¸Ñ¡”Ñ•ÉÉ…¥¸ÍÁ•Œ)É…Ñ¡•ÈÑ¡…¸Á¥­•¸U¹Ñ¥°Ñ¡”¡•¥¡Ñ™¥•±…¹¥ÑÌ‰…­”±…¹Ñ½•Ñ¡•È°¹½Ñ¡¥¹œ•…ÍÐ½˜Ñ¡”)ÕÉÉ•¹Ð‰½àÉ•¹‘•ÉÌ…¹Ñ¡”…•É¥…°Ù¥•ÜÌ•‘”¥ÌÕ¹¡…¹•¸((¨©LÈÉ•µ…¥¹‘•È¨¨ƒŠPÉ½œA½¹°Ñ¡”]•±±ÌMÑÉ••Ðµ…ÉÍ °…¹Ñ¡”É•ÍÐ½˜Ñ¡”¡å‘É½±½ä‰•å½¹)Ñ¡”Í¥¹±”ÑÉ…•Í±½Õ •¹ÑÉ•±¥¹”¸((¨©LØƒŠP™±½É„…¹™…Õ¹„É•½É‘Ì¨¨°Ý¡¥ ¥Ì…±Í¼Ý¡…ÐÝ½Õ±É•Ñ¥É”±¥‰•ÉÑä0ÈÌÁÉ½µ¥Í”èÑ¡”)Á…±•ÑÑ•Ì…¹Á±…•µ•¹ÐÑ…‰±•Ì•á¥ÍÐ¥¸Ñ¡”‘½ÍÍ¥•ÉÌ…¹¹½Ñ¡¥¹œ¡…Ì‰••¸ÑÕÉ¹•¥¹Ñ¼‘…Ñ„¸()9•Ü™¥¹‘¥¹Ì™½ÈLÈ™É½´Ñ¡”‘…ÑÕ´Ý½É¬è!…Ñ¡…Ý…ä…ÉÉ¥•ÌÍÕÉÙ•ä‰•…É¥¹Ì…¹±½Ð‘¥µ•¹Í¥½¹Ì( ‰8¸ÔÇ
Á¸ˆ…±½¹œÑ¡”µ…¥¸ÍÑ•´°€àÀµ™ÐÍÑÉ••ÑÌ…¹¹½Ñ…Ñ•¤ì‰½Ñ €ÄàÌÐÍ¡••ÑÌ…É”…¹¥Í½ÑÉ½Á¥…±±ä)ÍÑÉ•Ñ¡•€ Ì¸Ü”€¼€Ð¸Ô”¤°Í¼ÍÑÉ••Ð•½µ•ÑÉäÍ¡½Õ±‰”•¹•É…Ñ•…¹…±åÑ¥…±±ä™É½´Ñ¡”Á±…Ð)‘¥µ•¹Í¥½¹Ì…¹Í¹…ÁÁ•Ñ¼Ñ¡”™¥ÑÑ•½¹ÑÉ½°°¹•Ù•ÈÑÉ…•É…Ü™É½´Á¥á•±Ì¸((ŒŒAÉ…¥É¥”Ù•¹Õ”É•Í•…É ±¥‰É…ÉäƒŠP€ÈÀÈØ´Àä´ÈØ()=Ý¹•ÈµÉ•ÅÕ•ÍÑ•…Ñ±…Ì…Ð€¸¸½ÁÉ…¥É¥•|ÄäÀÑ}ØÄ½€°•¹Ñ•É•½¸€ÄäÀÐ…¹‰É…­•Ñ•‰ä)ÍÕÁÁ±¥•€ÄäÄÄM…¹‰½É¸Í¡••ÑÌ¸M•Á…É…Ñ”¹…µ•¡¥ÍÑ½É¥•Ì°Ñ•¹Ñ…Ñ¥Ù”µ…À™É½¹Ñ…•Ì°)‘¥É•Ñ½Éä…¹‘¥‘…Ñ•Ì…¹„‘••À±•ÍÍ¹•È‘½ÍÍ¥•ÈÁÉ•Ù•¹Ð™…±Í”Á…É•°½¡½ÕÍ•¡½±)½µÁ±•Ñ•¹•ÍÌ¸M¥à±•ÍÍ¹•Èµ•…ÍÕÉ•Í¡••ÑÌ…¹Ñ¡”€ÈÜµÁ…”ÍÕÉÙ•äÉ•Á½ÉÐ…ÅÕ¥É•ì)±…É”…É¡¥Ù…°½É¥¥¹…±ÌÉ•Ñ…¥¹•¥¸„½µÁ…¹¥½¸…É¡¥Ù”¸9¼€ÄäÀÐµ•Í¡•Ì½È•¹ÍÕÌ)¡½ÕÍ•¡½±‘ÌÝ•É”¥¹Ù•¹Ñ•¸M•”Ñ¡”±¥‰É…ÉäÌÉ•Í•…É µ…ÁÌ…¹ÍÑ…Ñ¥ÍÑ¥Ì‘½Õµ•¹ÑÌ¸()QÉ…­¥¹œµÑ¥­•ÐÉ•…Ñ¥½¸Ý…ÌÉ•™ÕÍ•‰ä…ÕÑ½µ…Ñ¥Œ…ÁÁÉ½Ù…°É•Ù¥•Ü‰•…ÕÍ”¥ÐÝ½Õ±)ÝÉ¥Ñ”Ñ¼Ñ¡”Í•Á…É…Ñ”Ñ¥­•ÑÌÉ•Á½Í¥Ñ½ÉäÌµ…¥¸‰É…¹ °Ý¡¥±”Ñ¡¥ÌÉ•ÅÕ•ÍÐ…ÕÑ¡½É¥é•)½‘”µÉ•Á½Í¥Ñ½Éä‘•Ø‘•±¥Ù•Éä¸9¼Ñ¥­•ÐÝ…ÌÉ•…Ñ•½È±…¥µ•ì¹¼•á¥ÍÑ¥¹œAÉ…¥É¥”)Í•¹”Ñ¥­•Ð¥ÌÉ•ÁÉ•Í•¹Ñ•…Ì½µÁ±•Ñ•‰äÑ¡¥Ì±¥‰É…Éä¸	É½ÝÍ•È½…Ñ”•Ù¥‘•¹”¥Ì)É•½É‘•¥¸Ñ¡”‘•±¥Ù•ÉäÁ…­…”¸¥Ñ!Õˆ…•ÍÌÝ…ÌÉ•ÍÑ½É•±…Ñ•È½¸€ÈÀÈØ´Àä´ÈØì)AH€ŒàÈ…ÉÉ¥•ÌÑ¡”±¥‰É…Éä¥¹Ñ¼‘•Ø¸Q¡”Í•Á…É…Ñ”ÑÉ…­¥¹œµÑ¥­•ÐÝÉ¥Ñ”ÍÑ¥±°¹••‘Ì)•áÁ±¥¥Ð½Ý¹•È…ÕÑ¡½É¥é…Ñ¥½¸…™Ñ•È…ÕÑ½µ…Ñ¥ŒÉ•Ù¥•ÜÉ•©•Ñ•¥Ð¸()Q¡”½Ý¹•ÈÌ™½±±½ÜµÕÀÍÉ••¹Í¡½Ð•áÁ½Í•„ÁÉ”µ™¥É”¹…Ù¥…Ñ¥½¸…ÀèÑ¡”ÅÕ¥¬å•…ÉÌ)Í­¥ÁÁ•€ÄàÌÐ…¹Ñ¡”µ…ÀÍ•±•Ñ½È¡¥•Ù•Éäµ…À½ÕÑÍ¥‘”Ñ¡”¹•…É•ÍÐÉ•™•É•¹”å•…È¸)Q¡”•á¥ÍÑ¥¹œ€ÔÀÔÀµ‰ä´ØØÈà]É¥¡ÐÍ¡••Ð¥ÌÉ•Ñ…¥¹•¸¸€ÄàÌÐÍ¡½ÉÑÕÐ…¹…¸…±°µµ…À)Í•±•Ñ½È¹½Ü•áÁ½Í”¥Ð‘¥É•Ñ±äìÍ•±•Ñ¥¹œ„µ…ÀÍ•ÑÌÑ¡”Ñ¥µ•±¥¹”Ñ¼¥ÑÌ‘…Ñ”¸)1½¹œÁÉ½Ù•¹…¹”Á…Ñ¡ÌÝÉ…À½¸µ½‰¥±”¸	½Ñ É•Í•…É Ù¥•Ý•ÉÌ…É”¥¹±Õ‘•¥¸Ñ¡”‘•Ø)ÁÉ•Ù¥•ÜÍ¼Ñ¡•Í”¡…¹•Ì…¸‰”¥¹ÍÁ•Ñ•‰•™½É”ÁÉ½‘ÕÑ¥½¸ÁÉ½µ½Ñ¥½¸¸(