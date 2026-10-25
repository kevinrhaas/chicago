#!/usr/bin/env bash
set -uo pipefail
_check_tools="$(cd "$(dirname "$0")" && pwd)"
cd "$_check_tools/.."

STRICT=""
[ "${1:-}" = "--strict" ] && STRICT="--strict"

# The step harness — `step`, `selftest` and the end-of-run roll-up — lives in its own
# file so that tools/test_check_harness.sh can source and exercise it (T-0763).
source "$_check_tools/check_harness.sh"
step "pictured frame taverns preserve defaults and build their opt-in details" \
  python3 tools/test_frame_tavern_picture_features.py

# T-3105: gallery supports must clear the declared pictured front.
step "first-fort explicit fronts preserve positional defaults and keep supports off apertures" \
  python3 tools/test_fort_picture_fronts.py

# Roof cloth uses a phase-local staff, never an entire building box.
step "explicit flag anchors preserve fort defaults and reject stale roof mounts" \
  node tools/test_flag_anchors.mjs

# Compiler/validator recognize real runtime consumption and honest card labels.
step "flag form values have an actual renderer and honest geometry labels" \
  python3 tools/test_flag_form_contract.py

# W1's forge stack, and the reason it is gated here rather than only on the baked
# master: `measure_stack_ordinance` reads the by-law's eighteen inches off the GLB, so
# a stack authored under the floor is caught a bake later by a gate that cannot say
# which archetype did it. This holds both ends of the bracket — the by-law's floor and
# Andreas's four feet — on the parameters, across every plan W1's own band admits, and
# with them the end wall the flue rises on and the three refusals the archetype makes.
step "W1's forge stack clears the by-law on every plan its family band admits" \
  python3 tools/test_outbuilding_forge.py

selftest "…and that bracket still fires when the head drops under the by-law" \
  python3 tools/test_outbuilding_forge.py --self-test

# The warehouse families' cargo-door rhythm, one storey up from the freight shed's.
# Same reason as above and two more of its own: an upper freight door stands over a
# cargo opening, so the doors on the two storeys have to read ONE set-out or they
# drift apart in a mesh that stays perfectly valid; and a single-bay record's set-out
# has to be the very float the archetype drew before the rhythm existed, or 43
# storefronts churn a bake for a change about warehouses. It also holds the beam's
# gable test at an OFF-CENTRE bay, which no committed record reaches — both of the
# town's F2 gables are deep enough to carry every bay — so it is held here or nowhere.
step "the warehouse's cargo doors and the freight doors over them set out once" \
  python3 tools/test_storefront_cargo_rhythm.py

selftest "…and that still fires when a single-door store moves by a nanometre" \
  python3 tools/test_storefront_cargo_rhythm.py --self-test

# T-2104: every shopfront's header board was built with no street face and a face
# lying ON the wall behind it (add_box's "back" is the y1 face, which on a +y facade
# is the one the street sees), and the two fought for depth as a visitor turned. The
# house stoops had the same skip. This builds the frame town without Blender and
# refuses a trim face lying on a wall that is not the hidden side of a board.
step "no trim board in the frame town lies flat on its own wall" \
  python3 tools/test_facade_board_faces.py

selftest "…and that still fires when a board's street face goes missing" \
  python3 tools/test_facade_board_faces.py --self-test

step "the street edge's cross-street faces enumerate as the plat says" \
  python3 tools/test_frontage_faces.py

selftest "…and those assertions still fire when the enumeration is broken" \
  python3 tools/test_frontage_faces.py --self-test

# T-1665, and it is a READING of the specification rather than a measurement of the
# town: the crosswalk's "2-3 shop bays" counts the door and `shopfront_bays` does not,
# so C3 looked short of its own band by one on every store and looked unsatisfiable at
# the top of it. The argument for the door-inclusive reading is D4's "3/5 bays; center
# or side door" and H1's "5 bays; center hall" — a centre door is centred in an odd
# count — and it is re-derived from the crosswalk here rather than remembered, because
# a reading whose evidence has been edited out of the file is a reading nobody is
# keeping. The same step holds the storefronts to their families' authored bands and
# holds `default_shopfront_bays`'s floor to fronts the frontage forced: on 20 of 26
# floors the one remaining window takes 50.0-66.7% of the front against a stated
# maximum of 45%, and until this step existed the floor overruled the ceiling in
# silence. docs/FACADE-BAYS.md is the settlement.
step "the shop-bay counts read as the specification's own words" \
  python3 tools/test_shopfront_bay_count.py

selftest "…and that reading's assertions still fire when each input is bent" \
  python3 tools/test_shopfront_bay_count.py --self-test

# The 665-roof programme's remainder is a function of what has been built, and the town
# grows most nights. Left as an authored number it goes stale silently — the crosswalk
# called 617 roofs remaining while 232 were standing — and the next block parcel schedules
# against a figure that is wrong by a third of the programme.
step "the 665-roof programme reconciles with the town that stands" \
  python3 tools/reconcile_665.py --check

# T-1196. The 668-roof schedule is a production decision from the owner's 2026
# specification, taken before the population layer existed, and the order book carries five
# `programme_deltas` rows stamped for this ticket so the comparison would be made
# deliberately. It is made here, once per gate, and it is the re-derivation rather than the
# spec that is asserted: every group says what it was compared WITH, three of the five
# deltas turn out to be unit mismatches or tautologies rather than disagreements about
# roofs, and the 308-household one resolves as an occupancy rate the November census
# brackets. The step also holds the two files that deal the same 668 roofs to each other:
# the crosswalk's counts had drifted to 662 and nine of its priority ranks were one place
# out, which is what an authored count field does when nothing re-derives it.
step "the roof programme re-derives against the order book, and the crosswalk deals its 668" \
  python3 tools/reprogramme_roofs_1835.py --check

selftest "…and its own refusals still fire when the programme is bent" \
  python3 tools/reprogramme_roofs_1835.py --self-test

# T-1445, and it reads the step above. Once the programme is re-derived, the 285 roofs
# the 2026-08 block recipes dealt anonymously can be asked whether the town still wants a
# roof of their kind in their place — against the order book's district/group head and
# the placement policy's clauses. 32 do not: trade roofs stranded sixteen to forty-seven
# metres back inside a block, and yard buildings fronting a principal street. The verdict
# is a SUBSTITUTION and the gate asserts it as one: a refamily moves the roof between
# order-book buckets and moves the roof COUNT by nothing, a seated roof is never re-dealt
# behind its household's back, and the whole audit re-derives from committed files or
# this step fails. T-1451 carries the verdicts into the recipe files and the bake, and
# the step below gates that execution; the 26 whose record id carries the family are
# T-1452's, and until it runs this remains a decision published and not yet executed.
step "the anonymous roofs re-audit against the programme the step above re-derived" \
  python3 tools/redeal_anonymous_roofs.py --check

selftest "…and the redeal's own refusals still fire on a bent order book" \
  python3 tools/redeal_anonymous_roofs.py --self-test

# T-1451, and it asks the question the step above cannot. The adjudication is DERIVED
# over the town as it stands, so carrying a verdict out deletes it: the roof conforms,
# the next re-derivation returns `keep`, and the evidence that anything happened is gone
# from the ledger. The permanent record is the recipe's own `redealt` block, and this
# step holds the recipe, the placements and the live adjudication to each other —
# including the one assertion that makes an execution worth anything, which is that
# every roof re-dealt now reads `keep`. A refamily that left the roof still breaching
# its policy would move a building for nothing, and would otherwise look identical.
step "the redeal's carried-out verdicts hold, and every re-dealt roof now conforms" \
  python3 tools/execute_roof_redeal.py --check

selftest "…and the executor's own refusals still fire on an unbuildable deal" \
  python3 tools/execute_roof_redeal.py --self-test

# T-1480, and the half of the redeal the step above CANNOT ask about. Nine North
# Division roofs carry their family in their id, so carrying their verdicts out
# renamed them — and the id was named by the sidecars, the liberties, the signage
# and trade goods, the lodging model, two lodger households, the reconstructed
# seating, the business layer, the hay limits, the Newberry leads, the land-sale
# ground index and both asset manifests. The failure this step exists to catch is
# not "the recipe says D4": it is a committed file still pointing at a roof that
# no longer exists, which reads as a merged migration and renders as a gap. So it
# sweeps the whole tree for the ids the nine left behind, and it says which dated
# receipts and transcripts are PINNED rather than quietly skipping them.
step "the redeal's migrated ids left nothing behind, and every migrated roof conforms" \
  python3 tools/execute_roof_redeal.py --check-migration

# T-1611, and the LAST of the 32 refamily verdicts. Six yard buildings on three platted
# blocks were re-dealt into dwelling families: the slot's family moved, its class was
# ASKED of `reconcile_665.inventory_class` rather than typed over, the record ids moved
# with the family and every committed file that named one was carried across. This step
# asks four things the step above cannot, because a block is dealt more than once and its
# schedule counts its own slots: that each re-dealt id still derives at its own sequence
# in its own programme phase; that the class it stands as is still the class the
# rear-cottage clause DERIVES for it, so losing that clause is red here rather than
# quietly making six second principal roofs again; that the live adjudication now returns
# `keep` for every one, which is the only thing a refamily is for; and that no committed
# file — outside the dated receipts and the two sweeps' own fixtures, which it names — is
# left pointing at one of the six ids that no longer exists.
step "the platted blocks' six are re-dealt, still derive their class, and left nothing behind" \
  python3 tools/execute_roof_redeal.py --check-blocks

# T-1483, and the step that had to exist before the 26 outstanding verdicts could be
# carried out at all. Their record ids encode the family, so executing them RENAMES a
# roof some seventy files name — and a scripted rename over those files would pass every
# gate here while printing a cooper employed at a cottage and a hitching post refused to
# a dwelling for a reason about a smithy. This measures, for every reference, whether the
# migration renames it, re-derives it, leaves it frozen as a record of a dated run, or
# has to adjudicate it; the report is the surface T-1481, T-1482 and T-1484 each stand
# on, and this step refuses it drifting away from the tree it describes.
step "the 26 moving roof ids' migration surface still describes the tree" \
  python3 tools/measure_roof_id_migration.py --check

selftest "…and it still tells a pointer from an assertion about what a roof is" \
  python3 tools/measure_roof_id_migration.py --self-test

# T-1494, and it is the OTHER half of the same execution. The step above covers the six
# verdicts whose id stayed put; these eleven changed name, and a renamed roof is a
# different kind of risk — a file that still says `recon_1835_south_c1_003` points at
# nothing, and nothing else here would notice, because a dangling id in an enclosure or
# a signage run reads as a record about a building this scene simply does not draw.
# So the step asks two things: that the recipe still derives each migrated id at the
# sequence it was migrated at, and that NO committed file names an old one. The
# handful that deliberately keep the old name — the Unreal receipts of an import that
# really did load it, the executor's own fixture — are listed in the tool with the
# reason, not skipped silently.
step "the migrated roof ids re-derive, and nothing still names an old one" \
  python3 tools/migrate_roof_ids.py --check

selftest "…and the migration's own refusals still fire on a moved recipe" \
  python3 tools/migrate_roof_ids.py --self-test

# T-1482, and the step that holds the last six of the 32 refamily verdicts to what was
# ruled about them. The two migrations above carried 20 out; these six are yard buildings
# standing off a block alley behind the principal roof on their own lot, and the
# adjudication moves every one into a dwelling family. The inventory class was read off
# the GROUP alone, so that promotion made each one a SECOND principal roof on an occupied
# lot — refused by the parcel gate, over `lot_ceiling_principal`, and not fixable inside
# the verdict, because all 36 offered families are ordinary dwellings. This tool measured
# that and the owner ruled on 2026-09-23 (option (a)): a rear cottage is ANCILLARY, so a
# lot may carry a main house plus a rear dwelling.
#
# T-1610 carried the ruling into `reconcile_665.inventory_class`, which now reads the
# position as well as the group, and into the placement policy as
# `rear_dwelling_behind_its_own_roof`. T-1611 then carried the six OUT, so this step's
# ordinary reading is now ZERO outstanding verdicts — which is what a carried-out
# adjudication looks like from here, because the ledger is re-derived over the town as
# it stands and a roof that conforms returns `keep`. What the step still holds is the
# re-derivation itself: the report must re-derive from the ledger, the block recipe and
# the placement policy, and it carries the ruling, the three remedies as each was costed,
# and the clause's own evidence — three of whose four documented stables stand exactly
# where the six were refused for standing. The record of the MOVE is the block recipe's
# `redealt` block, gated by the step below.
step "the platted blocks' remedies report still re-derives, and the rear-cottage ruling is still on the record" \
  python3 tools/measure_block_redeal_remedies.py --check

selftest "…and the derivation, both gates and the ruling's own record still fire when broken" \
  python3 tools/measure_block_redeal_remedies.py --self-test

# T-1499, and the silence it closes. Two tools sweep that same surface — the
# migrator above and `execute_roof_redeal.py --check-migration` — and until now each
# kept its OWN list of the files that legitimately keep an old name, with the same
# reasoning written out twice. They could disagree, and a disagreement was silent in
# the direction that hurts: a file pinned in one and not the other is red on whichever
# gate happens to run, and a file that should be stale but is pinned in both is a
# dangling id nothing catches. `tools/roof_id_pins.py` is the one list; this step asks
# BOTH sweeps their own verdict for every file in the tree and refuses a disagreement,
# so a future run that re-introduces a private list fails here instead of quietly
# diverging. It also refuses a dead pin and a pin that reaches outside the kind of
# name it claims to be.
step "the two roof-id sweeps read one list of pinned names, and agree on all of it" \
  python3 tools/roof_id_pins.py --check

selftest "…and the pin list's own refusals fire on a mutated list" \
  python3 tools/roof_id_pins.py --self-test

# T-0233, and the question the recipes cannot answer by being read: does a party-line
# run stand on the lots it was dealt? It does not — 8 of the 19 dealt lots carry none of
# their own run's roofs — and the ticket ruled that a RESERVATION rather than a defect,
# because `reconcile_665`'s free-lot arithmetic is derived from committed footprints and
# has never read a recipe's deal, so nothing is withheld from the programme by it. What
# was wrong was only that nobody could see it, which is why the measurement is wired in
# here instead of left as a command somebody remembers. The gate itself is the ceiling
# T-0079 established — `ROW_UNITS_PER_LOT` units per dealt lot, every roof already
# standing on those lots counted against it — and it passes today, so it is cheap.
step "no party-line run carries more roofs than the frontage it was dealt" \
  python3 tools/measure_frontage_entitlement.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_frontage_entitlement.py --self-test

# T-0163. The plat grid is the cartesian product of its east-west rows and north-south
# columns, so it proposes blocks that never existed, and it reports every refusal the same
# way — as a distance. A distance cannot tell "the centreline has not been carried there
# yet" from "these two streets never met", and both were being scheduled as headroom
# waiting on the same owed trace. This carries each refused block's named street toward it
# and samples the run against the committed heightfield: a run that crosses water is two
# banks, not a gap. It is what keeps the classification in the programme honest, so a block
# cannot quietly go back to promising roofs that no street control can deliver.
step "a refused block is short of control, or was never a block" \
  python3 tools/measure_block_gating.py --check

# T-0026, and the same fault one district wide. The programme's South balance — 120 roofs,
# the largest of the three gated ones — named STREET CONTROL as its blocker and sent the
# next parcel to go and carry a centreline. Measured, the blocker is the ground: the box
# ends at local N -400 m, INSIDE Washington Street's platted corridor, every north-south
# column of the south plat has its committed line cut at that same edge, and Madison — the
# plat's south boundary — is 125 m further south. The plat's last tier, six blocks and 48
# lots, is 100 % unmodelled. Two assertions: no committed platted block stands off the
# modelled ground (absolute, and it is what fires the day control is carried south without
# the terrain following), and the programme's stated southern coverage is the measured one.
step "no platted block stands off the modelled ground, and the south's blocker is the measured one" \
  python3 tools/measure_southern_ground.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_southern_ground.py --self-test

# T-1722, the same fault at the other end of the box. The North balance said "terrain,
# hydrology, flora and map coverage stop short of local N +760 m" for as long as it took
# somebody to measure it — by then the field carried to N +1120, the branch and its banks
# were traced to N +1079.21 and the lake margin to N +1117.30, and only the FLORA was
# short: z06's timber ring was still the 19 vertices cut to the old box wall, so the whole
# division north of Michigan Street drew as open prairie over ground Andreas documents as
# timbered. Two assertions: the committed timber ring (and the exclusion mirror z01 and z02
# carry, and the manifest's denormalised copies) is the one the committed waterline
# derives, and the division's ground reaches the line its own memo asks for.
step "the North Division's timber stands on the waterline, and its ground reaches the memo's line" \
  python3 tools/measure_northern_ground.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_northern_ground.py --self-test

# The two numbers on the FRONT screen (T-0036): buildings standing and people housed.
# Both are reads of the roof programme and the residents layer, and the most visible
# possible place to carry a stale number is the panel a visitor sees before anything
# else. Re-derived here so a run that builds ten roofs and forgets to regenerate the
# census fails at the commit rather than shipping a town that says it is smaller than
# it is. Also refuses a household whose `lives_at` names a structure the scene does not
# carry, which would silently drop people out of the count.
step "the gate's town census re-derives from the roofs and the residents" \
  python3 tools/town_census.py --check

# How far the town is from complete (T-1964, piece 1 of T-1215): the four joins the
# closeout names — every household housed, every working person at a workplace, every
# business roofed or its limit stated, every standing roof occupied or its use stated —
# counted by tier into data/render/town_completion_1835.json. The GAPS are the work the
# rest of T-1215 owes and do not fail this step; a DANGLING id (a lives_at, a seat, a
# workplace or a premises naming something that does not exist) does, and so does a
# ledger a run forgot to regenerate.
step "the town's completion audit re-derives, and no join names a missing record" \
  python3 tools/audit_town_completion_1835.py --check

selftest "…and it still refuses each kind of broken link" \
  python3 tools/audit_town_completion_1835.py --self-test

# Ground the town held in common is not building ground, and every gate this project
# had asked whether a building CLEARED the roadway, stood inside its own lot lines and
# missed its neighbours — never whether the ground it stood on was for sale. Two
# documented rental cottages spent five days standing on the public square for exactly
# that reason (ROADMAP T-A16). The reservation is authored data; this runs it.
step "nothing unpermitted stands on reserved ground" \
  python3 tools/measure_reserved_ground.py --gate

# The same question outside the plat, where it is bigger: 26.5 % of the modelled land
# above the water surface is the United States Reservation or the sand bar across the
# river mouth, neither was ever open to a private builder, and neither was refused by
# anything (ROADMAP T-E2). This also carries the under-coverage assertion — the polygons
# are resolved from the traces, so a terrain extension that outruns them fails here.
step "nothing unpermitted stands on refused ground, and the refusal still reaches it" \
  python3 tools/measure_no_build_ground.py --gate

# T-0891. The gate above now resolves a third KIND of ring: one read off a plate, rebuilt
# from the corner pixels and the transform a committed trace records rather than authored
# as vertices. Its worth is what it refuses — a ground corner edited without its pixel, a
# transform swapped under a reading taken before it — and not one of those is reachable
# from the committed data, so nothing would ever run them. This does, against fabricated
# copies of the real reading, so the refusals cannot rot into passes unnoticed.
selftest "…and the plate-reading resolver’s refusals still fire when broken" \
  python3 tools/measure_no_build_ground.py --self-test

# T-0436. The other kind of line over the same ground: not who could build on it, but
# whose by-laws reached it. The Trustees walked the corporate boundary on 7 November 1833
# and printed it three weeks later (chicago_democrat_1833_11_26#c024, tier 1); the legs
# are authored and the ring is RESOLVED from the committed streets and the committed
# shoreline, so a re-traced shore or a moved street must re-derive it or fail here. This
# never fails because a building stands outside the limits — twenty-four do, and that is
# a fact about 1835. It fails when the boundary stops being readable, or when a leg
# carried past the end of its own committed centreline comes near enough to a drawn
# building that the EXTENSION, rather than the ordinance, decides its side of the line.
step "the corporate boundary of 7 November 1833 still re-derives, and decides nobody by extrapolation" \
  python3 tools/measure_corporation_limits.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_corporation_limits.py --self-test

# T-1544, and it is the west leg's last 288.3 m read rather than only declared. That leg
# walks "north along said last mentioned street and its continuation to Ohio street", and
# the continuation is arithmetic: modern Jefferson does not survive north of Hubbard
# Street, so there is no third node to carry the line on. A NODE is not the only control.
# The ground the extension crosses is Wabansia, drawn whole on Wright's 1834 survey and
# already read into this repository, and this asks that reading whether Wright draws the
# continuation. He does not — the nearest drawn corridor is 73-80 m west, four times the
# sheet's own 16.02 m RMS — and the one line that could be mistaken for it, the tract's
# east rule against the North Branch, DIVERGES from the extension by 7.07 m over its
# length, so the identification is refused on bearing rather than on an offset that the
# registration's error could have argued away. This never fails because the leg is
# extrapolated; it fails when that refusal stops holding.
step "the west leg's continuation to Ohio is still bounded by Wright's sheet and not drawn on it" \
  python3 tools/measure_jefferson_continuation.py --gate --quiet

step "…and its committed reading re-derives from the committed geometry" \
  python3 tools/measure_jefferson_continuation.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_jefferson_continuation.py --self-test

# T-0134. The plate the Dearborn reach was built from draws warehouses on BOTH banks and
# only the north one stands. The south side was refused on a single spot reading taken by
# hand — "the corridor reaches to within about 1.7 m of the waterline" — and the whole bank
# was left empty on it. This is that refusal as a command, at every relief tolerance it
# could turn on: beside the platted street not one position takes the smallest footprint
# family F1 allows. It fails if a fit ever APPEARS, because a fit is the question re-opening
# and not a number to bank — which is the assertion that fires the day the terrain is
# extended, the plat is re-derived or the waterline is re-traced.
step "the south bank at the Dearborn reach still carries no ground outside its own street" \
  python3 tools/measure_south_bank_ground.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_south_bank_ground.py --self-test

# The terrain spec defers four in-town water features — the slough, the public-square
# pond, the Frog Pond and the Wells Street marsh — under one shared phrase, "existence
# documented, geometry conjectural". Existence is a claim about a PLACE and the scene is
# a date, and not one of the four had ever been asked where it stands on 1835-07-01
# (ROADMAP T-E5(a)). They do not answer alike: the slough is dated by the bridge this
# project already stands over it, the Frog Pond by a newspaper one year late, and the
# pond is argued in both directions by the same document. This holds the correspondence
# in both directions, so a fifth feature cannot be deferred undated and a dating entry
# cannot outlive the deferral it grades.
step "every deferred in-town water feature is dated against the scene" \
  python3 tools/measure_intown_water.py --gate

# The fifth of those features is no longer deferred, and the thing that most obviously
# depends on it had nobody watching it. The Slough Log Bridge is the only built thing in
# this dataset that exists to answer the terrain, and for two months it stood over dry
# prairie because zone 14 was not carved (T-0109). T-0005 carved it and T-0118 put its
# last reach square under this deck — both aimed elsewhere, neither gated here, and a
# swale line nudged a metre west would put the crossing back over solid ground with every
# other check still green. This joins the bridge's placement to the ground beneath it.
step "the slough crossing spans open water, and nothing else stands in the cut" \
  python3 tools/measure_slough_crossing.py --gate

# And the other side of the same coin: a road that meets this drain where NO crossing is
# recorded. T-1637. `fort_road` is the largest invention on the United States Reservation
# and its own record promised the water mask would make "honest gaps rather than fords" —
# written when no water was near it. T-1629 then moved the drain's mouth east of State
# Street, its new reach crossed the road, streets.js dutifully clipped the wet panels, and
# the way to the fort came out cut in two with every step in this gate still green. The
# line moved to leave the town over the crossing the town is DOCUMENTED to have built;
# this holds it there, and fires again if the drain is re-carved across it.
step "the way to the fort runs dry and crosses no water the town never bridged (T-1637)" \
  python3 tools/measure_fort_road_way.py --gate

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_fort_road_way.py --self-test

# And the water the town DRANK, which is a different argument about the same surfaces.
# `data/yard/town_water_cart.json` stands one cart where Andreas says the watermen drove
# into the lake, and the committed field says that water is the old southward channel with
# the sand bar and a quarter of a kilometre of open lake beyond it. T-0886 ruled the
# contradiction — the phrase names a stretch of bank, and 167 m south along that bank the
# traced bar ends and the water IS the lake — and the ruling is a set of distances read off
# a derived surface, written out in two documents. Nothing but this joins the prose to the
# field; a re-carve that drowns the bar or moves the waterline would leave both standing
# over a shore that is no longer there.
step "the watering place's ruling still matches the committed surfaces" \
  python3 tools/measure_watering_place.py --gate --quiet

selftest "…and the run classifier that reading rests on still fires" \
  python3 tools/measure_watering_place.py --self-test

# T-1765: reconstructed stock at the four branch-bridge ends. Validate the
# chosen offsets against committed deck centerlines and dry terrain corners.
step "the bridge-head timber still stands where the decks and the ground put it" \
  python3 tools/measure_bridge_head_timber.py --gate --quiet

selftest "…and every assertion that set-out rests on still fires" \
  python3 tools/measure_bridge_head_timber.py --self-test

# And the feature that crossing's own drain runs OUT of. "How much of the public
# square was wet" (T-0027) presumes a fraction can be read off the block, and it
# cannot: the terrain draws the square at the South Division plain's +2.9 ft with
# an inch and a half of relief — inside the spec's own declared micro-relief
# noise — so there is no basin there and a wet fraction read off it would be a
# read of the noise seed. The answer is a DEPTH: the dossier's own bed for zone 15
# is +1.0 to +2.0 ft, which the committed ground stands 0.84 to 1.96 ft above. So
# the square is planted as the flora dossier names it — ZONE 3, by name, the
# heading of the section that authors sedge meadow — and NO WATER IS DRAWN. This
# holds all of that: zero water, absolutely; no landform, so the zero stays a
# statement about the model; the sedge polygon still the committed plat's ring;
# and the drain still heading at the block it is named for.
step "no water stands on the public square, and its sward is the one the dossier names" \
  python3 tools/measure_public_square.py --gate

# Every generator asks whether the roof it is about to place stands in a platted street,
# and no invented roof has ever been allowed to. Nothing had ever asked it of the records
# a PERSON placed, so the answer arrived as anecdotes — three buildings in T-A9, two more
# in T-A12 — and the distribution behind them was never measured (ROADMAP K30). It is 29
# records, all of them documented and none of them generated. This holds that: a ratchet
# on the 29, and an ABSOLUTE assertion that no generated roof laps a corridor, which the
# placement gate already guarantees and which is therefore enforceable at zero.
step "no building has newly been drawn standing in a platted street" \
  python3 tools/measure_corridor_intrusion.py --gate --quiet

# The absolute half of that gate rests on ONE reading: which evidence layer a record
# belongs to. It used to be read off the record's ID PREFIX, and `physicians_office`
# carries no prefix while being a product of the inferred-household programme — so a
# generated record was scored against the ratchet, which may be re-baselined, instead of
# against the absolute, which may not (T-0221). The reading moved onto the record itself
# in plat_occupancy.layer_of_record; this puts a generated roof in a roadway, in memory,
# under both readings and checks which one the gate catches.
selftest "…and its absolute assertion still fires when a generated roof is put in a street" \
  python3 tools/measure_corridor_intrusion.py --self-test

# That gate and every generator ask the PLATTED corridors only, and the reservation had no
# plat — so T-1712 placed two Beaubien buildings on the centreline of `fort_road` and
# nothing asked (T-1743). This asks every street in data/streets/1835.json, at its own
# declared width, of every phase standing on the layer's date: a ratchet on the 48 laps
# banked on 2026-10-03, refusing a new one, a deeper one, or a cleared one left banked.
step "no building is newly drawn standing in any street corridor, the fort road included (T-1743)" \
  python3 tools/check_structure_corridors.py --gate

selftest "…and it refuses the trading post put back on the fort road (T-1743)" \
  python3 tools/check_structure_corridors.py --self-test

# The platted corridor above is an Original Town and West Division question: not one of the
# eleven corridors street_control.json measures is north of the river, and plat_corridors
# gives no north-bank street a ring at all. So nothing re-derived a north-bank frontage, and
# on 2026-09-06 two reconciliations of one ruling (PRs #974 and #975) put the Steamboat Hotel
# 36.79 m apart with both of them green. This is the missing half: the north bank's own rule
# — the drawn track's kerb plus a 2.00 m clearance — re-derived from the committed street on
# every commit, with every frontage that is not on it named and held to its own figure.
step "north-bank frontages still stand on the rule the north bank is placed by" \
  python3 tools/measure_north_bank_frontage.py --gate --quiet

selftest "…and that assertion fires when a roof leaves the frontage line" \
  python3 tools/measure_north_bank_frontage.py --self-test

# T-0421. Canal is the one street whose control does not agree with itself — three points
# spreading 2.33 m, so `disagree`, so its corridor stays on the drawn line. That figure was
# read for a year as an open question about where Canal ran. It is not: two of the five
# OpenStreetMap nodes averaged into `kinzie_canal` are the Kinzie Street Bikeway, and on the
# three road nodes the same three control points spread 0.09 m. The road-only reading is now
# committed data (`control.kinzie_canal.road_only_reading`) rather than three paragraphs of
# prose, and this re-derives BOTH spreads, the per-point offsets, and the 2.93 m variance the
# North Branch bridge declares against that same field. Nothing moves on either reading — the
# gate exists to keep that true, not to argue for the correction.
step "canal's corridor still reads the same on both readings of Kinzie x Canal" \
  python3 tools/measure_canal_control_spread.py --check

selftest "…and its assertions fire when either reading, the line or the bridge drifts" \
  python3 tools/measure_canal_control_spread.py --self-test

# Two generators build party-line rows onto the committed block faces and each asserts
# that ITS OWN run stands on one line; neither could see the other. The Lake face of
# blk_lake_clark is built by both and carried two lines 0.70 m apart, ten metres apart
# along the face and so not yet reading as a step (T-0104). This is the gate beside the
# two: it takes the face line out of the committed plat, projects every front wall onto
# it, and refuses a face carrying more than one — absolutely, with no ratchet, because
# after T-0104 the number is zero. It also closes party walls from BOTH sides, which is
# the case neither run-local gate can reach when the other half belongs to another
# generator.
# T-0226. North Water Street's line was a hand-drawn schematic that ran 477.4 m of its
# 843.3 m inside the water mask, so the renderer drew no roadway at all across that
# reach — and NOTHING SAW IT, because the panel-accounting gate asks whether every panel
# with a DRY centreline reached the ribbon and every one of them did. A street whose
# centreline is wet is invisible to that question by construction. The line is now
# derived from the committed north bank, and this is the gate that keeps it derived: it
# re-runs the derivation and refuses a committed line that is not the one it produces,
# so a bank that moves under the street is a red build rather than a silent hole.
step "north water street is still the line its own derivation produces, and still dry" \
  python3 tools/derive_north_water.py --gate

# T-0372. "Still dry" was a weaker question than it sounded: the gate above asks whether
# any BEND stands in water, and a street can hug a bank for a hundred metres without
# putting a vertex in it. The derivation now carries a clearance rule with two tiers —
# the open reach owes the half module less the fit's own give, and the two ends, where
# the street meets the water on purpose (it stops at the fork and crosses on a deck),
# owe five metres. This is the proof the rule refuses each tier, and that the two
# exemptions are load-bearing rather than a way of saying nothing.
selftest "…and its own assertions still fire when broken" \
  python3 tools/derive_north_water.py --self-test

step "a block face carries one street line, across every generator that builds on it" \
  python3 tools/measure_street_line.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_street_line.py --self-test

# T-0444. The West Division's module is derived from committed files and the owner's
# shift report is answered by a ceiling the river imposes, so both can rot silently
# if the bank trace or either committed west line moves. The self-test is the alarm:
# it asserts the ceiling still BINDS, which is the only thing that keeps
# docs/RESEARCH/west_division_module.md's answer true.
selftest "the West Division module, and the ceiling that answers the owner's shift report" \
  python3 tools/measure_west_division_module.py --self-test

# T-0446. Carroll and Fulton are the two West Division tiers the plat carries and no
# committed file held. Fulton is fitted to four surviving intersections; Carroll does
# not survive inside the plat and is the MIDPOINT of its two neighbours, so it is the
# one line here that a move of kinzie or fulton would silently falsify. The self-test
# holds that midpoint inside the bracket its neighbours put it in, and holds the band
# comparison docs/RESEARCH/west_division_tiers.md reports.
selftest "the West Division's tiers, and Carroll's midpoint still inside its own bracket" \
  python3 tools/measure_west_division_tiers.py --self-test

# T-0445. West Water is the West Division's riverfront street and it is not fitted to
# anything modern — nothing modern survives on its line. It is the committed 1834 west
# bank offset one half-corridor west, so the moment that bank trace moves, the street is
# in the water or off it and no other gate would notice. This holds the offset to the
# centimetre against the bank as committed, holds the two refusals against the modelled
# ground's own west edge, and holds the module the seating measures.
selftest "West Water still stands one half-corridor off the bank, and the two refusals still hold" \
  python3 tools/measure_west_division_streets.py --self-test

# T-0451, the same shape on the other side of the river. Six North Division lines are seated
# as the committed South Division streets continued north, and everything that entitles them
# to be there is arithmetic on two committed files — the pixel reading of the plat in
# data/traces/thompson_north_division_streets.json and the street lines themselves. So it all
# goes stale silently: move a South Division centreline and its northern half no longer lies
# on it, re-grade one and the North Division line keeps an attestation the parent lost. This
# holds the collinearity to 2 cm, holds each line's ends on North Water and Kinzie, holds the
# residual T-0827 left on the one line that still reads worst, and holds the sheet reading
# that says the plat letters no name in any North Division corridor. It needs no image library; the reading
# is committed data and `--reread` is what goes back to the 7 MB sheet.
selftest "the North Division lines still lie on the streets they continue, and say what names them" \
  python3 tools/measure_north_division_streets.py --self-test

# T-1457, the same sheet read DOWN instead of across. T-0451 gave the tier a width and no
# depth, and T-1436 could not cut lots into it because nothing committed said where the
# blocks stop. They stop on a line the plat draws, and the tier is a WEDGE: the lower lot
# row is the 180 ft the sheet letters in every block, and the upper row takes up the whole
# difference, 178.6 ft at Franklin to 232.7 at Wolcott. This holds that reading against the
# sheet's own lettered figures, holds the px-to-northing fit against T-0451's independent
# px-to-easting fit on the other axis, and — the assertion that matters most — holds the
# REFUSAL: committed Kinzie is held out of the fit and missed by 16.8 m at its worst, which
# is a shear, so depths may be published from this sheet up there and northings may not.
# Everything is arithmetic on two committed files; `--reread` is what goes back to the sheet.
selftest "the North Division tier is still the wedge the plat letters, and still refuses to publish a northing" \
  python3 tools/measure_north_division_tier_depth.py --self-test

# T-1458, the cut the reading above paid for. `generate_plat_lots.py` can cut a block only
# between two committed street lines and the tier has one, so the seven blocks Thompson
# draws between Kinzie and the river went uncut for as long as the sheet had no depth. They
# are cut here instead, off committed Kinzie and DOWN by the read depth — never off the
# sheet's own southern line, which is the northing T-1457 refuses to publish. The two steps
# are the pair every derived file in this repo carries: the file re-derives from its inputs,
# and the derivation holds its own assertions. The ones worth naming: the committed columns
# give four 80 ft lots to a face in all seven blocks, which is the sheet's module arrived at
# from the other side; the tier line predicts block 6's read north face to a fifth of a pixel,
# which is what its carried depth rests on; and the ONE block the terrain calls wet is the one
# the plat draws its watercourse across, two records with no arithmetic in common agreeing.
step "the North Division tier's blocks and lots re-derive from the reading and the committed lines" \
  python3 tools/cut_north_division_tier.py --check

selftest "the North Division tier's cut is still four to a face, still a wedge, and still seated on committed Kinzie" \
  python3 tools/cut_north_division_tier.py --self-test

# T-1477. The School Section's northernmost tier — the thirteen blocks between Madison and
# Monroe, the row Section 16 turns toward the town — cut into lots. The block grid has been
# committed since T-0797 and stopped at blocks, because Wright rules the section into blocks
# and letters their numbers without ruling a single lot line inside one. The lot COUNT is
# therefore not a module here: it is read, block by block, out of the Illinois State
# Archives' register of the state's own October 1833 sale, which prints the plat's language
# (`LOT3BL71`, `BL106`) and so says how many pieces each block was cut into. Nine blocks
# sold eight lots, two sold four, and the two the sheet letters `Reserved` sold nothing and
# are left whole. The assertions worth naming: the blocks the sale never names are EXACTLY
# the blocks the sheet reserves — two records, neither consulted about the other; the two
# four-lot blocks are the two at the South Branch end, and the one block the committed
# heightfield calls wet is one of them; and every block boundary is the committed grid's
# own vertex for vertex, which is what keeps this a cut and not a second survey.
step "the School Section tier's lots re-derive from the committed grid and the 1833 register" \
  python3 tools/cut_school_section_tier.py --check

selftest "the School Section tier is still cut into the lots the sale witnesses, and no others" \
  python3 tools/cut_school_section_tier.py --self-test

# T-2252, piece 1 of 3 of T-2247, on the owner's ruling of 2026-10-09: cross Monroe. The
# School Section's SECOND tier — the thirteen blocks between Monroe and Adams — cut by the
# first tier's own derive() on the grid's row 1, so the two tiers cannot be cut two ways.
# The register names all thirteen: eleven sold eight lots, and the two that sold four (71,
# 79) sit directly under the first tier's four-lot pair at the South Branch, with 79 the
# row's one wet block. Six blocks stand east of the river by T-2144's own test — 82 to 141,
# 48 lots — and those are where T-2253 and T-2254 deal and raise the South's six gated roofs.
step "the School Section's Monroe-Adams tier re-derives from the committed grid and the 1833 register" \
  python3 tools/cut_school_section_second_tier.py --check

selftest "the Monroe-Adams tier is cut into the lots the sale witnesses, under the first tier's columns" \
  python3 tools/cut_school_section_second_tier.py --self-test

# T-0827, the ticket the reading above could only name. `market` is the one street on this
# grid no sheet fixes directly — its west side is the river bank its whole length — and until
# this it was ONE modern junction on N Wacker Drive, which is 1926 made ground, plus a
# bearing. It is now Franklin stepped one module west, and the whole case is a pitch that
# two independently measured sheets bracket and the superseded line missed. That makes it
# exactly the kind of derivation that rots: the committed vertices are arithmetic on
# `franklin`, so moving Franklin, or the module, or re-fitting either sheet, silently leaves
# Market standing on a sum nobody made. This holds the re-fit to the centimetre against
# `franklin`, holds the line this replaced against the junction it was fitted to, holds the
# Wright ladder at five lines with no alley-width gap among them, and holds the bracket the
# argument rests on.
selftest "Market still stands one module west of Franklin, and the sheets still bracket it" \
  python3 tools/measure_market_line.py --self-test

# One line per face says nothing about what the wall on it is MADE of. L99 and L100 both
# worried that the schedule "will keep dealing cabins to commercial frontage", and the
# block recipes quietly acted on it: every log dwelling the five South Water blocks were
# dealt was put on the Lake face, leaving 15 invented buildings on South Water's line and
# not one of them log — against a documented record for the same line that carries Hogan's
# log store, and against the only picture of that row, which draws it as log AND frame
# shoulder to shoulder. T-0022 measured that, refused the re-apportionment K29 proposed,
# and moved the arrangement instead. This holds it: a principal street's INVENTED frontage
# may not be more uniform in construction than the documented record of the same street.
# A floor of one, absolute — the plate gives no ratio, so a share would be a number
# somebody chose.
step "no principal frontage is more uniform than the record it reconstructs" \
  python3 tools/measure_frontage_fabric.py --gate --quiet

selftest "…and its own assertion still fires when broken" \
  python3 tools/measure_frontage_fabric.py --self-test

# What a frontage is MADE OF was T-0022; what a non-dwelling standing on it is FOR is
# T-0024, legacy K32. The face rule ranks dwellings — best to the better street, meanest
# to the back one — and T-A15, dealt the first store any block parcel had had to place,
# extended the ranking to cover it rather than leaving the placement unreasoned. That
# extension was an agent's invention about 1835 commerce and was opened for the next
# commercial family to follow or refute. It is refused as a RULE and replaced by one that
# can be read off the committed record instead of argued: not one of the 31 documented
# stores, warehouses and workshops in this town stands on a light street, and every
# documented store standing on a platted street stands on its line. Two absolute
# assertions over the roofs the block parcels place, no ratchet, both green the day they
# were written — which is the only kind of absolute worth adding.
step "no block parcel stands a non-dwelling where the documented record puts none" \
  python3 tools/measure_face_rule.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_face_rule.py --self-test

# The face rule, the end rule and the frontage fabric were three modules each holding a
# piece of one policy and each re-typing its numbers — five of them, under seven names,
# across four files. T-1195 wrote the policy down: twelve clauses saying who lived and
# worked where, each with its tier and the documented records behind it, and the five
# numbers in one place that the four modules now import. The clause text is authored in
# the module; every count, street class and setback printed beside a clause is re-read
# from the committed tree on every run, which is what --check compares. THIRTEEN clauses
# since T-1610, the thirteenth being `rear_dwelling_behind_its_own_roof` — the owner's
# rear-cottage ruling of 2026-09-23, tier `inferred` and citing no record, because this
# town holds no documented roof standing as a dwelling in another roof's yard. It removes
# no outlier: all seven documented D roofs conformed already. Five assertions:
# no clause cites a record this tree does not hold; a `documented` clause has evidence
# and an inferred one has its reasoning; every outlier is explained AND every explanation
# still has its outlier; no family letter is left without a seat rule; and no module has
# taken its own copy of a shared constant back. No roof moves — this reads.
step "the placement policy still re-derives, and nothing re-typed its constants" \
  python3 tools/placement_policy_1835.py --check --quiet

selftest "…and its five assertions still fire when broken" \
  python3 tools/placement_policy_1835.py --self-test

# T-1613, the first piece of T-1199. The policy above says which GROUND a household of a
# kind belongs on; this says which LOT, and it could not be written until the lots were
# enumerated. `1835_lot_ledger.json` is that enumeration — 226 committed lots, each with
# the street its face fronts, that street's traffic class, whether it turns a corner, what
# stands on it and how many principal roofs the policy's multi-building rule lets it
# carry — every field a join over a record this project already committed.
# `1835_platted_seats.json` is the adjudication on top of it: every household the address
# book leaves at a band, offered the plat in the policy's own clause order, adopting a
# standing anonymous roof before ever asking for a new one, and handed to T-1614 in
# writing where the plat has nothing for it. Six assertions: no seat on a lot the ledger
# does not draw; no roof adopted twice; no household seated across a division line; no
# adopted roof also drawn off the order book (that would spend one roof twice); no row in
# scope left unanswered; and no owed row with a blank where its reason should be. Nothing
# is raised and nothing is baked — an adoption points at a roof that already stands and a
# slot is a request the 5C build tickets fulfil.
step "the lot ledger and the platted seats still re-derive" \
  python3 tools/seat_platted_ground_1835.py --check

selftest "…and the deal's six refusals still fire when broken" \
  python3 tools/seat_platted_ground_1835.py --self-test

# T-1638, piece 1 of 4 of T-1200. The deal above puts a household under a roof; until this
# step the ROOF said nothing back. The link ran one way — the address book's row naming its
# structure — so a visitor opening one of these South Water buildings read "Anonymous
# count-unit toward the July 1835 665-roof programme" while a file two directories away said
# which household the policy had seated in it. `1835_roof_keepers.json` is that publication,
# and its refusals are the load-bearing half: 60 of the deal's 108 adopted seats are
# households minted from the post office's letter lists, whom the owner's ruling of
# 2026-08-30 (T-0379) refuses a roof, so they are listed with the ruling rather than written
# onto a card. Nothing is raised, nothing is baked and no keeper is a reading — L276 carries
# the publication and L270 the invention underneath it.
# T-1685 ran the same pass for the Randolph–Washington tier, so the ledger is plural: the
# district rides in `DISTRICTS` with the ticket that carried it, `--check` holds every
# district the pass has been run for at once, and every seat outside them is still owed by
# name. It also added the third refusal — seven household cards are still NAMED a
# letter-list name while their person's flag has been correctly cleared, and one of them is
# seated on a Randolph roof, so the two statements are published on neither (T-1689).
step "the platted deal's roofs still name the keepers it seated there" \
  python3 tools/name_the_keepers_1835.py --check

selftest "…and the keeper ledger's assertions still fire when broken" \
  python3 tools/name_the_keepers_1835.py --self-test

# T-1614, the second piece of T-1199. The pass above enumerated the plat and handed 1,374
# of the 1,480 banded households on with a written reason; this is the file that answers
# them, on the ground the committed plat does not draw. `1835_off_plat_ledger.json`
# enumerates it — 136 tier lots the Thompson grid was closed before either tier file was
# written, the 2 School Section blocks left whole, Kinzie's Addition's 27 blocks with a
# boundary and no lot rule, the 7 placed survey chips and the 5 camp grounds carried by
# name because their own file authors no vertex. `1835_off_plat_seats.json` deals it in
# the placement policy's own clause order. EVERY SEAT IS AN ADOPTION and no slot is
# raised anywhere, because 150 of those 177 parcels have no row in the 665-roof
# programme's schedule at all and the 27 that do are marked `unsubdivided` with no
# headroom — which is the finding, not an omission. Seven assertions: no seat on a parcel
# the ledger does not draw; no roof adopted twice; no household seated across a division
# line, tested against the roof's own `reconstruction.district`; no roof adopted here that
# T-1613 already adopted, which would seat two households in one roof across two files;
# no order-book draw on ground the schedule does not open; no handed-on row left
# unanswered; and no owed row with a blank where its reason should be.
step "the off-plat ledger and its seats still re-derive" \
  python3 tools/seat_off_plat_ground_1835.py --check

selftest "…and the off-plat deal's seven refusals still fire when broken" \
  python3 tools/seat_off_plat_ground_1835.py --self-test

# T-1793, the first piece of T-1784. The off-plat deal above owes 44 households to
# `west/farms_and_country_seats`; this measures the ground they could farm before anyone
# raises a roof for them. The West is read west of the committed river on a 10 m lattice,
# cut by the corporation's 1833 bounds and by the survey tracts, and the unsubdivided
# ground outside the limits is counted in forties — the smallest holding the register and
# the 1835 press name here. It also reads the roofs already standing on that ground and the
# West's programme headroom for a D1 cabin and an A2 barn. It moves nothing; it fails when
# any of those inputs moves and the record was not rebuilt, or when its sums stop closing.
step "the West farm ground still re-derives from the seats, the tracts and the programme" \
  python3 tools/measure_west_farm_ground_1835.py --check

selftest "…and its sums and ceilings still refuse when broken" \
  python3 tools/measure_west_farm_ground_1835.py --self-test

# A dwelling nobody named is a count-unit toward a documented aggregate; a PUBLIC
# building nobody named is the claim that an institution stood here and left no record
# at all. ROADMAP T-I3 enumerated them: on 1835-07-01 the town's public buildings with a
# roof are three, all three are committed named records, and every other public function
# in Chicago was carried on inside a private building. generate_block_infill.py has
# refused the institutional families by name since L93, but only for the blocks — the
# North, West and phase-one parcels ran before it existed and nothing had ever asked the
# committed records. This asks all of them: absolute zero for I1 and I3, a ratchet at the
# one anonymous I2 that L93 records rather than deletes.
#
# T-0032 CLOSED THE OTHER HALF, which had been open since T-I3: the I3 target was SIX and
# the town's civic roofs are three, so three slots counted nothing and the schedule went on
# dealing them to blocks where every generator refused them. The step now settles every
# civic candidate against the committed dataset — a roof that stood, a building that came
# later, a function that never had a building of its own — and holds the target and the
# institutional district row to that ledger. It is the shape of fault this project has been
# bitten by twice: the court-house stood in the scene for four days while another file
# already credited it no roof, because nothing read the two together.
step "no anonymous roof claims to be a public building, and the civic target is the ledger" \
  python3 tools/measure_institutional_claims.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_institutional_claims.py --self-test

# THE OTHER NINE ROWS, which T-0032 found were cross-checked against nothing (T-0211).
# The matrix carries the same aggregate two ways that were authored independently — ten
# group rows and four division columns — and reconcile_665.py asserted only that the
# families sum to their group and the districts to the total. Nothing read a group's split
# BY DIVISION, which is precisely the pair T-0032 found disagreeing.
#
# The I3 repair does not generalise and this does not attempt it: a row above what stands
# is the ordinary, correct case for nine of these ten rows, because an anonymous dwelling
# is a legitimate count-unit toward a documented aggregate. What is asserted is the weaker
# pair that still catches the fault — the matrix must add up in BOTH directions, and a
# division standing OVER one of its group rows must say so. The second is a ratchet on a
# real residual: the North Division stands seven roofs above its rows (six freight, one
# the L93 school), reconcile_665.py clamped the negative away, and the seven slots it
# sheds to pay for them come out of the North's ordinary dwellings where nobody could see
# the transfer. Both figures are now in the programme document.
step "the group rows add up by division too, and every division over one declares it" \
  python3 tools/measure_group_district_rows.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_group_district_rows.py --self-test

# Uniformity is a claim, and no source makes it. 138 of the 218 anonymous records say
# in their own footprint note that the rectangle was sampled inside the family's
# authored band; this holds them to it, and prints the census of what still is not —
# 36 stamped massings and 40 eaves outside the band their own note cites, all of them
# on parcels whose meshes are canonical bakes (ROADMAP T-V1(b), K25). Read the census;
# a pass here is not "the town is a distribution".
step "the anonymous massings that claim a sampled band have one" \
  python3 tools/measure_massing_variety.py --gate

# The same sentence, asked of every reconstructed record and every value the crosswalk
# authors a testable band for. "Type-level choice within the D3 band" is the entire
# defence for inventing a building, so a value outside the band it cites is a note that
# is wrong about its own source — 98 of them, on 80 of 249 records (ROADMAP K25). The
# strict assertion FAILS today and is meant to: --strict runs it. What runs here is the
# ratchet, because the repair needs a bake and a permanently red dev gate would block
# every unrelated parcel behind it. A new offender, or a committed one whose value
# moved, fails. The fault may shrink and may not grow.
step "no reconstructed value is newly outside the band its own note cites" \
  python3 tools/measure_band_claims.py --gate --quiet

# The value NO record states and every visitor sees: the RIDGE the sampled pitch and
# the sampled footprint make together (T-0145). The crosswalk authors a `ridge_ft` band
# beside every eave band and nothing had ever read that column, so a parcel could repair
# its pitches into their band and push its roofs out of theirs — the fault moved one
# field over. This models the ridge from the archetype's own roof arithmetic, checks
# that model against the ridge the committed GLB actually carries, and ratchets the
# residual the same way the band-claims gate does. The residual is real and mostly
# structural: for several families no pitch inside the authored pitch band reaches the
# authored ridge band at the footprint the family authors.
step "no reconstructed roof's ridge is newly outside its family band" \
  python3 tools/measure_ridge_band.py

# ...and the same question asked of the SPECIFICATION rather than of a roof (T-0148).
# The gate above holds the eave a record happens to carry fixed, which made its residual
# read as a conflict between two committed bands — "no pitch reaches the ridge band at
# the footprint the family authors". The eave is not fixed: it is the second value the
# crosswalk authors as a band and the samplers draw from, so a ridge band is reachable
# from a (footprint, eave) PAIR. Swept that way, every family's four claims — footprint,
# eave, pitch, ridge — are satisfiable at every footprint in its own band, so nothing in
# the specification has to give way and the residual above is all repair. This holds that
# true: a crosswalk edit that authors a family which cannot be built to its own ridge band
# fails here, at the specification, instead of four runs later as a roof nobody can raise.
step "every family's footprint, eave, pitch and ridge bands are satisfiable at once" \
  python3 tools/measure_ridge_reach.py --quiet

# ...and the residual THAT gate printed as three NOTE lines, joined to what the
# generators actually deal (T-0179). Nine families are offered a SHED by their roof line
# and four cannot reach their own ridge band as one, because a shed's plane climbs the
# whole span where a gable climbs half. Nothing was broken, because no parcel dealt those
# four a shed — but which families get a shed was decided FIVE times, once inside each
# parcel, and the five had already drifted over A5. The rule now lives in
# tools/roof_form.py alone, the refusal is written on the card a visitor opens, and the
# step above holds the two together: a family dealt a form its own bands cannot carry, a
# record that does not carry its family's refusal, or a parcel that grows its own copy of
# the shed set all fail here.
selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_ridge_reach.py --self-test

# The same question asked of the crosswalk's OTHER two columns for the store families —
# `required_variant` and `variants` — which name forms rather than bands (T-1659). Three
# of those lines named forms `frame_storefront` could not draw, and two of the three were
# invisible rather than refused: C2's `levels: "1.5"` was read with `int()`, so eight
# records that state a story-and-a-half were built as one-storey shops with the shop
# opening cut through the attic floor; and C4's "side gable or hip" met a roof rule that
# gave a FRONT gable to every family whose id begins with C. The third — C3's and F2's
# hoist door — is correctly BUILDABLE AND UNBUILT, because those entries' own assumption
# notes forbid inferring one, and a capability no record exercises is exactly what a gate
# has to hold up.
step "the store families' crosswalk variants are the ones the archetype draws" \
  python3 tools/test_store_variants.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/test_store_variants.py --self-test

# The same question one attribute over, and the same answer (T-1686). `plan` decides
# where a house's front door goes, and five anonymous parcels each decided it beside
# their own form values — so all five gave H1 the three-bay hall-parlour front of a
# cottage, while H1's own entry requires `center_hall_one_and_half`, states a bare
# "5 bays" and is the ONLY family of the thirty-five that names a centre hall. Seven
# roofs stood on it. This holds the reading, the roofs, the five parcels asking one
# rule, and H2's two refused variants against the records that refuse them.
step "H1's centre hall is the crosswalk entry's, and H2's hip and Greek doorway are refused" \
  python3 tools/test_house_front.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/test_house_front.py --self-test

# And the question the two gates above cannot ask, because they read what LANDED: is
# every family the 665-roof schedule may deal to a platted block buildable at every
# size its own band allows? A family comes up rarely — there are two H1s and two H2s in
# the whole parcel — so a band whose tail the archetype refuses looks fine until the
# schedule deals into the tail and the run dies. This deals each family four hundred
# instances through the generator's own sampling and asks the archetype to build each
# one. It found H2 unbuildable over the top third of its authored eave band, D6 over
# the bottom of its own, a rounding step that put a pitch outside the band it was drawn
# from, and W2 fatal to the generator on the day it is first dealt (T-0142).
# T-0172 took the sweep off the block generator alone and onto all FOUR anonymous
# parcels — west, South Division infill and the inferred households deal the same
# families through the same archetypes and had never been asked. None of them refuses a
# deal; every one of them authors form values as per-family CONSTANTS whose note cites
# the family band, and 31 of those constants sit outside the band they cite. The gate is
# therefore a RATCHET from here: a refusal never passes, and an off-band claim passes
# only while tools/family_deal_baseline.json names it with the reason it stands.
step "every family every parcel may deal builds, and every band claim is named" \
  python3 tools/measure_family_deal.py --gate

# AGENTS.md puts one constraint above the work — the final removal of the Potawatomi
# from Chicago is August 1835, inside this project's first target year — and gives it
# one mechanism: review_required on any record blocks a scene from being marked
# released. Nothing had ever measured what that sentence covers (ROADMAP K34). It
# covered the buildings: the seven flagged households blocked nothing, and were safe
# only by the coincidence that each lives or works in a building that is flagged too.
# One record said in its own prose that it carried the flag and never had. Four
# absolute assertions and no ratchet, because this is a commitment rather than a fault
# being paid down.
step "the standing constraint reaches every record that claims it" \
  python3 tools/measure_review_constraint.py --gate

# The same shape of question asked of AGENTS.md rule 6 — a check_required source
# "may be cited in text but must not have assets derived from it", and
# docs/PROVENANCE.md says the validator enforces it. What the validator compares
# is two fields of the same source record: rights_status against the source's own
# asset_use label, so it can only fire once an author has written the violation
# down, and no source in this dataset ever has (ROADMAP K41). This asks the town
# instead, using the read-sets the archetypes and the terrain generator already
# declare. The population is banked by name: it may shrink and may not grow, and
# a repair has to be recorded with --update in the commit that made it.
step "no unresolved source is newly built into the town" \
  python3 tools/measure_rights_derivation.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_rights_derivation.py --self-test

# K41's residual, and the question one layer out: the buildings and the ground
# declare which of their figures reaches a vertex, and data/flora and data/fauna
# never had. 100 figures across the two layers, 38 of them read by the renderer
# and 58 by nothing at all — including the whole of data/fauna, which no file
# under renderers/ opens and publish.sh does not copy to the site (ROADMAP K42).
# The map is Python and the reader is JavaScript, so every declaration is scanned
# against the renderer sources with the comments stripped, in both directions.
step "every flora and fauna figure is declared read or banked unread" \
  python3 tools/measure_layer_reads.py --gate

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_layer_reads.py --self-test

# The same question one level in, and it is a different question: the read-set
# above says a FIGURE is read if any renderer source reads it, and no reader in
# this project receives every record. flora.js takes five roles and fifteen
# forms; trees.js takes two roles, five forms and FOUR of the manifest's ten
# zones. So 339 of the 1,880 (record, figure) pairs the map calls read reach
# nothing, six records reach no reader at all — four of them the lakeshore's
# woody scrub, which its own zone prose describes to a visitor — and three
# recorded July inflorescences draw no flower (ROADMAP K44). Every cohort is
# scanned out of the renderer rather than restated here, and all three
# populations are banked exactly: they may not grow, and a repair has to be
# recorded with --update in the commit that made it.
step "every flora record reaches the reader its figures are read by" \
  python3 tools/measure_flora_reach.py --gate

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_flora_reach.py --self-test

# The step after that one, and it is a different question again. K44 measured
# ROUTING — which reader is handed the record — and named the repair its finding
# implies: "add z08_lakeshore to TIMBER_ZONES and the four dune records are
# drawn". Measured, that repair draws nothing (ROADMAP K45(a)). TIMBER_ZONES is a
# SPECIES table: trees.js takes height, crown, foliage and density out of those
# files and then places from a hand-written COMMUNITIES mix, never from a zone's
# extent — z07_bur_oak_savanna's declared box is 4.4 km outside the modelled
# field and its oaks are drawn regardless. So a routed record whose species is in
# no mix is drawn nowhere, which the American sycamore has been all along, and
# the woody planter is a fixed 632 m square inside a field it reaches 27 % of.
# Both populations are banked and neither may worsen.
step "every routed woody record can be selected by something that places it" \
  python3 tools/measure_planting_reach.py --gate

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_planting_reach.py --self-test

# The population BOTH woody gates were blind to. smoke_renderer.mjs asserts that
# "woody vegetation never occupies the river mask" off trees.group.userData.stations
# — written only inside the near-field planter's 632 m square — and the flora half
# walks instance matrices on a lattice centred on the camera. FAR_TIMBER is neither:
# five bodies of timber authored as polylines and drawn as a horizon silhouette, and
# nothing had ever asked those polylines where they stand. One of them, the belt whose
# own note says it follows South Water Street, was 39 of 39 samples over the main stem
# and 3.347 m under its surface — the line of trees across the channel in the owner's
# screenshot (ROADMAP R-BUG5). T-0031 put it back on land (0 of 136) and the step below
# keeps it there. The renderer refuses water absolutely now; this holds the table, and
# scans the clip so it cannot quietly come back out.
step "no body of far timber stands in the river" \
  python3 tools/measure_far_timber.py --gate

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_far_timber.py --self-test

# T-0031 / R-BUG5(b). The belt that stood in the channel is back on land, on a line
# DERIVED from the committed `south_water` centreline rather than authored beside
# it — the owner's route 1, with the side of the street recorded as L191. The stub
# it replaced was drawn on a Wells Street 66.7 m east of the committed centreline,
# and that error is half of why it ended up in the river, so the belt is re-derived
# here on every commit. Move South Water Street and this fails until the belt moves
# with it.
step "the South Water timber belt re-derives from the street it is cut from" \
  python3 tools/derive_timber_belt.py --check

# T-0094 was filed saying the fort's pickets are flat-topped. They are not, and
# have not been since the archetype was written: the committed master carries
# 0.312 m of sharpened head on every one of its 768 posts, 8.4 % of the picket,
# and a visitor at the north wall sees the sawtooth. The claim had never been
# measured, which is how it reached a ticket. This holds the property so it cannot
# be re-filed off a screenshot, and so a flattened archetype or a decimation pass
# that ate the apexes would be named here rather than found by eye.
#
# THE PLATE HALF OF THAT FILE DOES NOT GATE, deliberately. p4_0 is a tier-5
# retrospective lithograph; it may inform a value and it may refute a claim made
# about itself, and it may not hold a build red. Run the file without --gate for
# the plate reading, which also needs Pillow and skips without it.
step "the fort's stockade is still pointed" \
  python3 tools/measure_picket_plate.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_picket_plate.py --self-test

# NOTE ON THE TWO FORT STEPS THAT FOLLOW, because they look inconsistent and are
# not. T-0094's plate half deliberately does NOT gate: it asks whether a tier-5
# retrospective lithograph supports a claim about the MODEL, and a lithograph may
# not hold a build red. T-0095's does gate, and its live assertion is a different
# question — the third one, which reads the RECORD and fires the day someone gives
# a corner work a height, a roof or a lantern on that plate's authority. Its other
# two assertions read a committed image that cannot change, so the only thing they
# can catch is the detector moving under them, which is what its baseline is for.
# One asks the plate about the town; the other asks the town about the plate.

# FOUR CROPS, FOUR PANELS OF ONE SHEET. Three of the fort layers' plates reached
# this repository as owner-supplied crops with a README and were cited by committed
# path for a month; T-0055 joined the Kinzie one to kurz_allison_1893 by hand and
# left the rest unconfirmed, and T-1107 measured them. The gate is not there to
# re-prove the identification — that is settled and written into the source record.
# It is there because a citation can rot silently: re-crop, re-scan or re-compress
# either image and four source_ids quietly stop pointing at what they claim, with
# nothing else in this repository able to notice. Six seconds to hold the join.
step "the four crops are still the panels their citations name" \
  python3 tools/measure_plate_join.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_plate_join.py --self-test

# Fort Dearborn's gates are built SHUT on purpose — the archetype's own words: a
# fort with its gates standing open makes a claim about the hour of the day, and
# the garrison is attested for the scene date. Both of them stood a quarter open.
# One leaf of each pair was placed from a midpoint that collapsed onto its own
# jamb, so 0.90 m of a 3.6 m gateway was daylight straight through the wall and
# 0.90 m of leaf lay across the pickets outside the frame — in the committed GLB,
# so in the bytes a visitor downloaded. This reads the shipped mesh rather than
# re-deriving the placement, because the derivation was the fault (T-0095).
step "Fort Dearborn's documented gates are shut" \
  python3 tools/measure_fort_gates.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_fort_gates.py --self-test

# T-0095 was filed saying p4_0 "draws the corner works RISING ABOVE the curtain
# with their own pyramidal roofs and small lanterns". It does not. It raises two
# such works and both stand over the MIDDLE of the wall, at 0.435 and 0.521 of the
# drawn run; the one angle the plate shows unoccluded is drawn plain, and the other
# is behind a tree. This is the second Fort Dearborn parcel in two days seeded by a
# plate read with the eye (T-0094 was the first), so the refutation is held by a
# measurement rather than by a paragraph — and its third assertion fires the day
# the record is built to the misreading anyway.
step "p4_0 raises no work at either angle of the fort it draws" \
  python3 tools/measure_fort_works_plate.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_fort_works_plate.py --self-test

# T-0197 audited the rest of that table, because three of its eight rows had been
# struck as wrong in a week and rows 1, 2 and 6 had never been measured at all —
# while already carrying TWO built ways on the reservation. Row 2 is the first row
# of that table to survive measurement: p4_0 draws one bare corridor, it meets the
# wall at the gate, it runs west, and it reaches the shore. Row 1's "both plates"
# is struck (p4_1 draws no way at the fort, on a detector that finds the way it
# draws elsewhere on the same bank). Row 6's flagstaff stands at 0.495 of the wall
# — over the gate, not in the parade where exclusions.json puts the FIRST fort's.
# Two of the three assertions here ask the TOWN about the plates, which is why this
# one gates where T-0094's plate half does not: they fire the day fort_bank_track
# is swung back east, or either way's geometry_confidence is promoted on the
# strength of a tier-5 lithograph.
step "the ways the fort plates draw are still the ways the town was built to" \
  python3 tools/measure_fort_ways_plate.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_fort_ways_plate.py --self-test

# T-0617. The same rule, applied to the owner's four Sauganash views: a row of
# docs/RESEARCH/sauganash_image_accuracy.md states a measurement, names the tool
# that made it, and prints the number. This gates on the four claims the note
# rests on — five bays over five with the door in the middle, and an annex whose
# courses are coarser than the block's siding — and on drift in the banked
# reading, which is how a detector edit that quietly moves a number gets caught.
step "Braunhold's Sauganash still says what the research note says it says" \
  python3 tools/measure_sauganash_plate.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_sauganash_plate.py --self-test

# T-0649. The fifth image the owner deposited beside those four, read against the
# 1838 harbour-light plate. The reading's whole point is a NEGATIVE — the sheet is
# composed rather than constructed, so nothing on it can be inverted to a station —
# and a negative is exactly the kind of finding that rots in silence. This gates on
# the ten claims docs/RESEARCH/chappel_shore_lighthouse.md rests on, and on drift in
# the banked reading of both sheets.
step "the Chappel shore drawing still refuses to place its own station" \
  python3 tools/measure_chappel_shore_lighthouse.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_chappel_shore_lighthouse.py --self-test

# T-0626. The plan the record now carries rests on ONE arithmetic result taken off
# that banked reading: both lines out of the drawn apex are world-horizontals, so
# they are two RIDGES meeting at a point, and two ridges of one wall height and one
# pitch meet only when they span the same width. That is what forces the cross
# wing's span in generators/archetypes/frame_tavern.py, so it is gated rather than
# quoted — if the finding ever flips, the record's derivation is stale.
step "both lines out of the Sauganash's drawn apex are still ridges, not rakes" \
  python3 tools/sauganash_apex_lines.py --gate --quiet

# The datum must remain the output of its committed ground control, never a
# hand-edited number. Skips (exit 0) when pyproj is not installed.
step "datum re-derivation" \
  python3 tools/rederive_datum.py

# T-0878. The verdict on the NA Wright sheet's registration is a MEASUREMENT — four
# models scored on eleven control points, a leave-one-out for each, and a table of how
# far every committed reading off that sheet would move under each. A verdict of that
# shape rots the moment its inputs move, and three of its inputs are files other
# tickets edit: the eight control points, the three section corners, and T-0797's
# measured line table. So it is re-derived here rather than quoted. Pure Python by
# design — numpy is not installed in the agent sandbox and a step that needs it SKIPS
# (T-1083), which is not a gate.
step "the NA Wright registration's adjudication still matches its own measurement" \
  python3 tools/adjudicate_wright_na_fit.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/adjudicate_wright_na_fit.py --self-test

# The liberties the walkthrough shows must still be the ones the markdown
# states. LIBERTIES.md is append-only and is the source of truth; data/
# liberties.json is derived and committed so the site needs no build step, which
# only holds up if drift is a gate failure rather than a discovery.
#
# Since T-0054 it also asks WHICH SECTION each entry is in, from two independent
# statements — the heading it sits under and the `**Resolved:**` line in its own
# text — because `resolved` is the section validate.py stops checking. It used to
# be the last section in a document whose one rule is that liberties are
# APPENDED, so 23 entries landed in the exemption by doing what they were told,
# and the drift check above could not see it: the markdown and the JSON agreed,
# both reading the fault the same way (the T-0207 shape).
step "liberties derived from docs/LIBERTIES.md" \
  python3 tools/compile_liberties.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/compile_liberties.py --self-test

# The renderer reads the sidecars and never the dataset, which only keeps the
# walkthrough and the archive together if a record edited without a recompile is
# a failure here rather than a discovery on the deployed site.
step "sidecars derived from data/" \
  python3 tools/compile_scene.py --all --check

# T-2747: the 1904 built-so-far walk is written from the building records, so a building
# that gains detail without the walk being rewritten is red here, and the walk stays current.
step "1904 built-so-far walk matches the building records (T-2747)" \
  python3 tools/jaunt_built_so_far.py --check

step "Jaunt schema, destinations and reachable state graph (T-1253)" \
  python3 tools/compile_jaunts.py --check

step "Jaunt refusal and data-only expansion fixtures (T-1253)" \
  python3 tools/test_compile_jaunts.py

# T-2039 (of T-1271): the LIBRARY, not one story — the 25 named premises, the six
# priority jaunts featured, 4-8 stops, quiet outings, keepsake families and ranks
# reachable without replay, and the owner's subjects each carried by a jaunt.
step "Jaunt library shape: roster, featured six, families, ranks, subjects (T-2039)" \
  python3 tools/audit_jaunts.py
selftest "…and each of its assertions still fires when the library is broken" \
  python3 tools/audit_jaunts.py --self-test

# compile_jaunts proves a jaunt is well-formed; this reads what it SAYS: no Indigenous
# encounter staged, no figure or asset carried, no quotation the claims do not hold
# verbatim, no restricted source cited (T-2040).
step "Jaunt content refusals across the library (T-2040)" \
  python3 tools/audit_jaunt_refusals.py

selftest "…and each refusal still fires when broken (T-2040)" \
  python3 tools/audit_jaunt_refusals.py --self-test

step "Source-use backlinks match authored claims (T-1248)" \
  python3 tools/compile_source_use.py --check

# The Glessner street/stable opening schedule is generated from the record, so a
# record change that is not re-scheduled is caught here (T-2211).
step "Glessner street and stable opening schedule matches its record (T-2211)" \
  python3 tools/glessner_opening_schedule.py --check

# The stable-roof reading re-solves two committed cameras and reads the roof
# through them, so a camera, pick or record height that moves without the report
# being re-written and re-read is caught here (T-2758).
step "Glessner stable-roof reading re-derives from its cameras (T-2758)" \
  python3 tools/glessner_stable_roof_read.py --check

# The cupola reading fits the stable cupola's height, size and place to both
# northwest prints through T-2758's re-solved cameras, so a pick, camera or record
# number that moves without the report being re-written and re-read is caught here
# (T-3031).
step "Glessner stable-cupola reading re-derives from both prints (T-3031)" \
  python3 tools/glessner_cupola_read.py --check

# HABS 15's camera is the stable_level fit on measured controls at the stable, and
# the hoist stone is read through it and through T-2758's HABS 01 doorway fit, so a
# pick, camera or record number that moves without the report and the camera being
# re-written and re-read is caught here (T-3147).
step "Glessner stable-end reading and HABS 15's camera re-derive (T-3147)" \
  python3 tools/glessner_stable_end_read.py --check

# Both north cameras are re-solved with the gable pairs' sill and head left free, so
# a pick, camera or record height that moves without the reading being re-written,
# or a record that builds the pairs outside it, is caught here (T-2850).
step "Glessner north gable pairs stand where HABS 13 and 14 read them (T-2850)" \
  python3 tools/glessner_north_pairs.py --check

# Taylor 2135 is refitted on the Prairie front's first-floor jambs with the stacks withheld,
# and the front's lights stand at HABS sheet 6's places and widths, so a pick, camera or
# opening that moves without the reading being re-written is caught here (T-2858).
step "Glessner's Prairie lights stand on HABS sheet 6, Taylor 2135 refitted on them (T-2858)" \
  python3 tools/glessner_prairie_front.py --check

# The north tower's finial is read through both north cameras, and the cone's size off
# its silhouette, so a plan moved to HABS 14's tip alone (which that camera cannot hold
# off the wall's plane) or a camera that moves without the reading is caught (T-2872).
step "Glessner north tower stands where HABS 01's tip and silhouette read it (T-2872)" \
  python3 tools/glessner_north_finial_read.py --check

step "Source-use fixtures preserve joins, counts and public boundaries (T-1248)" \
  python3 tools/test_compile_source_use.py

step "source browser counts and filters" \
  node tools/test_sources_view.mjs

# The home page's destination clips (T-2685): every clip a card names ships in both
# formats, nothing ships unnamed, and the weight stays capped. `--browser` drives the
# page itself; no smoke part loads the Observatory.
step "home page destination clips: named, in both formats, inside the cap (T-2685)" \
  node tools/test_portal_clips.mjs

step "shared destinations and safe stand-offs (T-1277)" \
  node tools/test_destinations.mjs

# Every building card offers a link to the write-up behind the building, and on
# the deployed site all 332 of them were a 404: publish.sh leaves docs/ out of
# the payload by design, so the link resolved in the source tree and nowhere a
# visitor stands (ROADMAP K26). The link is now absolute and this asserts both
# halves of it — that every linked dossier is a file here, and that the base the
# renderer composes with still points at this app inside its repository.
step "every dossier link a card offers resolves" \
  python3 tools/check_dossier_links.py

# Renderer JS must at least parse. The repo's deploy workflow does the same thing
# for site/, and a syntax error there is a blank page for everyone.
check_js() {
  local n=0 bad=0
  while IFS= read -r -d '' f; do
    n=$((n + 1))
    node --input-type=module --check < "$f" 2>/dev/null || {
      echo "   parse error: $f"; bad=1
    }
  done < <(find renderers -name '*.js' -not -path '*/vendor/*' -print0 2>/dev/null)
  echo "   $n module(s) parsed"
  return $bad
}
step "renderer modules parse" check_js

# T-1055. The ground mesh paints the two flora zones with box extents their own
# recorded `ground.rgb`, by multiplying the July tile's luminance through the
# record after dividing it by the tile's own mean. That construction is what
# makes the mean albedo inside a zone the recorded triple EXACTLY rather than
# approximately, and it is quiet when it breaks: retune the tile, or record a
# brighter triple that clips against the albedo ceiling, and the ground drifts
# off the record with nothing to say so. This runs the shader's arithmetic over
# the same deterministic pixels and holds all four triples to one sRGB unit.
step "the ground averages the colour each flora zone records" \
  node tools/measure_ground_albedo.mjs --gate

# The ground the town is ANCHORED to and the ground it is DRAWN as, compared on
# the committed bytes. `generators/terrain_gen.py` refuses to export a mesh more
# than 30 mm from the heightfield — inside a Blender run this gate cannot make,
# so nothing re-checked the committed master afterwards, and R-BUG3c was a 306 mm
# disagreement nobody could see. This asserts the master and REPORTS the shipped
# derivative, which is quantised by the publish step and conformed at load; the
# surface actually drawn is asserted by tools/smoke_renderer.mjs.
step "the ground mesh still meets the heightfield the walker samples" \
  node tools/measure_terrain_fit.mjs --gate

# …and the 1904 ground's (T-1738), which terrain_gen_graded.py bakes through the
# same mesher and the same 30 mm refusal.
step "the 1904 ground mesh meets its heightfield too (T-1738)" \
  node tools/measure_terrain_fit.mjs --epoch e1871_postfire --gate

# …and the 1812 ground's (T-2003), which terrain_gen_e1830.py bakes through the same mesher
# on the 1834 grid. Its heightfield is NOT re-derived here: the field is the 1834 one's
# arithmetic over a 2.4-million-cell box and takes about 76 s, which this pool cannot spend
# (rule 9). `validate.py --stale` holds its input hash instead, and
# `python3 generators/terrain_gen_e1830.py --check` is the byte-for-byte re-derivation.
step "the 1812 ground mesh meets its heightfield (T-2003)" \
  node tools/measure_terrain_fit.mjs --epoch e1830_natural --gate

# The OTHER two axes, which conformGroundToField() cannot repair — it reads a
# height back off the field at a vertex's shipped (E, N), so a vertex the
# quantiser moved in plan holds the right height for the wrong place, and on the
# east banks' 60-90 % slopes that cost 77 mm where the road ribbon has 22.
# generators/terrain_gen.py now derives the skirt margin so the publish step's
# POSITION rung divides the terrain grid exactly, which puts every ground vertex
# on a rung and takes the displacement to zero. This asserts the zero on the
# bytes rather than the arithmetic on the generator's side of the bake (T-0152).
step "the shipped ground stands where the master does, and inside the road lift" \
  node tools/measure_terrain_horizontal.mjs --gate

step "the shipped 1904 ground stands where its master does (T-1738)" \
  node tools/measure_terrain_horizontal.mjs --epoch e1871_postfire --gate

step "the shipped 1812 ground stands where its master does (T-2003)" \
  node tools/measure_terrain_horizontal.mjs --epoch e1830_natural --gate

# T-1067. The two gates above measure the ground against the mesh drawn FROM it,
# which cannot see the town standing where there is no ground at all. The box
# stops at n +400 and Kinzie's Addition was committed running to n +1029.71, so
# Wolcott Street's ribbon leaves the modelled ground and is draped on the
# renderer's fallback constant for 629.72 m, and 79.5 % of the north wall is a
# one-way door under the walker's 0.35 m step-up rule. None of that is asserted
# to be SMALL — no setting of this repo makes it small today, and a gate that
# demanded one would only ever be red. What is asserted is that the committed
# reading still matches a re-derivation, so the number cannot drift while the
# box or the street layer moves and nobody notices.
step "the town off the modelled ground is still the town the reading measured" \
  node tools/measure_north_of_box.mjs --gate

# T-1415, of T-1193. The sibling above measures a CONSEQUENCE — what the renderer
# does with a town that stands off the box. The west side asks a decision
# instead: the West Division recipe holds 35 of its 55 placements for want of
# ground and names E -700 m as the box it needs, and until this step nothing had
# derived that number. It is derived here from the westernmost held FOOTPRINT
# edge (not its centre) less the Wright georeference's worst residual, rounded
# west onto the 2.5 m lattice — which lands at E -705, five metres west of the
# round figure the recipe asked for, because -700 clears the sheet's RMS and
# stands 4.24 m short of its maximum. The gate holds the reading, so the wall
# moves when a placement moves rather than when somebody remembers. It moves no
# ground: the grid is a mesh input and T-1416 is what spends the bake.
step "the west wall the held slots need is still the wall the reading derives" \
  node tools/measure_west_of_box.mjs --gate

selftest "…and its own assertions still fire when the wall or a street moves" \
  node tools/measure_west_of_box.mjs --self-test

# T-0467. The other half of the same question, asked of the places a visitor is
# OFFERED rather than of the streets. `data/scenes/*.json` § anchors is the list
# the Go-to menu paints and the smoke harness drives, and until this step nothing
# asked whether an anchor stands on modelled ground at all. That was cheap to
# ignore while every viewpoint sat inside the 1834 plat; T-0467 put six of them
# up to 3.8 km down the southern field, where the pre-fill shore crosses 390 m of
# easting between Twelfth Street and the box floor, so a coordinate that is dry
# at one row is in the lake at another and the diff looks identical either way.
# The rule is written on the walk surface rather than made an exception for one
# id: `north_branch_bridge_deck` stands mid-span over a channel 2.38 m under the
# water plane and is CORRECT, because the bridge record declares walk_surface_m.
step "every viewpoint the app offers stands on modelled, dry, unbuilt ground" \
  node tools/measure_anchors.mjs --gate

selftest "…and the anchor-ground rules still hold on synthetic ground" \
  node tools/measure_anchors.mjs --self-test

# T-0466. The ground's culling grid used to be the literals 12 x 3, and those two
# numbers were a measurement of a 2,020 x 800 m box with its long axis east-west.
# The southern field turned the box's long axis north-south and the literals could
# not see it: three rows over the mesh's 10,240 m is a tile 3,413 m deep, a strip
# that is in the frustum from anywhere on it and can therefore never be culled.
# The grid is a function of the box now, and these two hold it there — the rule
# still reproduces the 12 x 3 the budget was measured at, tileGround() still ASKS
# it rather than carrying literals again, and the committed reading is still a
# reading of this rule on the field it names.
step "the ground's culling grid is still derived from its box" \
  node tools/measure_ground_tiling.mjs --check

selftest "…and its own assertions still fire when broken" \
  node tools/measure_ground_tiling.mjs --self-test

# The shrub archetype's own bounds, which are the only two numbers in it the
# RESEARCH owns: the clump keeps the half-width its record states, and a leaf
# spray stays a mass of leaves rather than shrinking towards a single leaf it
# cannot draw at two triangles. K57 measured that "hold the total plate area and
# refine the grain" trades the first for coverage, so the bound is a gate rather
# than a paragraph. The third assertion is a ratchet on the coverage itself.
step "the shrub keeps its recorded width and its shell is not see-through" \
  node tools/measure_spray_grain.mjs --gate --quiet

# The changelog contract, on every run rather than only when somebody remembers
# it. AGENTS.md has always told an agent to run this by hand before merging, and
# on 2026-08-13 the file was corrupted BY A MERGE — `.gitattributes` merges it
# with `merge=union`, so both parents were green and the union of them was not.
# A hand-run check cannot cover a file that a merge rewrites; this one can.
step "changelog contract" \
  node tools/check-changelog.mjs

# T-1380. The contract step above now also holds the tree to its merge base, so a
# merge that drops, re-stamps or renumbers a shipped entry is refused. That is the
# half that read "contract OK" on 25 dev merges; prove its refusals still fire.
selftest "…and a shipped release note cannot leave or change its number" \
  node tools/changelog-history.mjs --self-test

# THE ENTRY AS A FILE OF ITS OWN (owner, 2026-10-10). A PR writes its What's-New
# entry to changelog.d/<name>.json instead of the top line of changelog.js, because
# that one line made every open PR conflict with every landing (#607, #608, #610 and
# #613 each lost three merges to it). The fold on dev turns the file into an entry
# after the merge. Hold the pending files to the contract and budget now, while the
# PR is open, so the fold never meets a file it must refuse.
step "pending changelog entry files are well formed and inside the What's-New budget" \
  node tools/changelog-entries.mjs --check

selftest "…and the fold numbers, orders and deletes them, and refuses a bad one" \
  node tools/changelog-entries.mjs --self-test

# The ticket queue: the operational "what next" the owner ordered on 2026-08-17
# after his own requests went untraceable in the ROADMAP. Duplicate ids, queue
# drift, a stale BOARD, a block with no stated question — all merge-refusing.
#
# `--inherited-warn` IS WHOSE RED IT IS (T-1593). The tickets are a separate
# repository since 2026-09-23, so nothing this step reads is in the diff under
# review — and on 2026-09-25 that turned into a red nobody could clear: two
# tickets were filed as effort L at 23:07Z and the gate on #51, a pull request of
# AGENTS.md and three files under tools/, went red on THIS step 37 minutes later.
# It merged with GH_REST_MERGE_BLIND=1 after its author had proved the red was
# not his. So the step now says which faults are the branch's own — those fail —
# and reports the rest as a WARN naming the filing and the command that clears it
# for every open PR at once. `node tools/ticket.mjs check` run bare is still
# strict, which is where the rule keeps its teeth: by hand, and in the tickets
# repository's own CI. The flag does NOT soften a dirty or unpushed clone —
# state this run put there is state this run owns.
step "ticket queue (faults in the tickets repo are reported, not charged to this diff)" \
  node tools/ticket.mjs check --inherited-warn

# …AND BOTH HALVES OF T-1593, ON A REAL CLONE OF A REAL BARE TICKETS REPOSITORY,
# because the whole distinction is which repository a file lives in and a fixture
# folder cannot tell the two apart. The filing refusal (`new --effort L`, and an
# effort the gate cannot read) and the WARN, against the exact queue state that
# failed at 23:07Z — plus the three things the flag must NOT let through: a fault
# in this repo's own files, a tickets clone this run dirtied, and embedded mode.
step "a filing fault is refused at the prompt, and a queue fault no diff carries is not charged to it" \
  node tools/test_ticket_filing_effort.mjs

# T-3153. The owner's photo-ticket stopping rule (2026-10-25): a run files no ticket on a
# photo-gated house (the gap goes into its match record), any house past 25 tickets since
# the image gate takes new ones only from the owner, and `split` refuses a sign-off or a
# gated house past the cap unless `--owner-asked`. Proved on a fixture tickets folder.
step "photo follow-ups stop: no run-filed tickets on a photo-gated house, no split sign-off" \
  node tools/test_ticket_photo_stop.mjs

# T-1548. `done` refuses to close a ticket a committed file still records as live work
# — the shape that turned dev red three times running (T-1507 as #7, T-1540 as #25,
# T-1299 as #26), each found hours later by a different run from a red gate. The
# scanner is a gate, so it is proved by breaking it, on fixtures rather than on the
# data, and it asserts BOTH directions: the two shapes are caught, and the three ways
# a ticket id appears innocently are not.
selftest "…and the tripwire scanner behind \`done\` still fires, and still ignores prose" \
  node tools/ticket.mjs tripwire-self-test

# T-1581, AND THE HALF T-1548 COULD NOT SEE. That scanner matches the closing ticket's
# OWN id; all three of the closes that turned dev red on 2026-09-25 stranded an
# ANCESTOR instead — a pointer named a `split` parent, and the close took its last live
# descendant. #40 (T-1448) left twelve cohort units on T-1189 two levels up, red for
# 2.5h; #43 (T-1560) ended the re-family programme on T-1556 while T-1564 stood open
# under the split T-1559; #49 (T-1523) would have left 272 landholding units on T-1198.
#
# THE WALK IS ONE DEFINITION NOW (tools/ticket_liveness.py): the research ledger's
# `split_live`, the order book's `live_pieces_of` and ticket.mjs all read it, and the
# self-test holds the three shapes above plus the one that must NOT fire — a split with
# a live descendant two levels down.
selftest "…and the split walk all three of them read still holds, on all four shapes" \
  python3 tools/ticket_liveness.py --selftest

# AND THE QUESTION ASKED OF THIS BRANCH, NOT OF THE WORLD. `done --pr` sets `review`,
# and the tickets repo settles it to `done` when the PR MERGES — so the state that
# breaks dev arrives after this gate has already passed it. This step asks it early:
# the ledger's and the order book's ownership gates, re-run against a queue in which
# the tickets THIS BRANCH NAMES are already `done`.
#
# SCOPED TO THE BRANCH, and the scope is the point. Reading every `review` ticket in
# the shared queue would turn this PR red for a close somebody else is making, which
# is precisely the fault T-1593 is filed about; on `dev` and `main` it says so and
# does nothing. An ancestor that is ALREADY dead is not this branch's either — the
# step reports only what is NEW with the close.
step "closing this branch's tickets strands nobody above them" \
  python3 tools/ticket_liveness.py

# The link between the two: the shipped derivative against the master it was
# compressed from. `--stale` gates data -> master and check_published.mjs gates
# assets/web -> the mirror, and NOTHING gated the step in between, which is the one
# with the moving parts — two gltf-transform passes whose own comments in bake.sh
# record a bug that "collapsed every building to a two-metre box shipped past a fully
# green gate — twice" (ROADMAP K36). Triangles, node identity, the contract's
# attributes and the world bounding box are all answerable from the glTF JSON chunk,
# so this costs a second and no decoder. The material half is a ratchet, and K36(b)
# emptied it: 334 of 334 now, so the next offender is the first entry.
#
# K38 added assertion 8, which is the one that covers the OTHER writers. `assets/web/`
# is written by three scripts and four of their branches copy a master through, and a
# master copied over its own derivative satisfies assertions 1-7 by construction —
# measured, two of them passed the whole of this file. The 93 legitimate passthroughs
# are banked by name and both directions fail. A new placeholder therefore needs
# `--write-baseline` in the commit that adds it: the decision is recorded, not found.
step "the shipped derivative still describes the master's building" \
  python3 tools/measure_web_derivatives.py --gate --quiet

# The gate above has eight assertions and, until K37, nothing had ever watched one
# of them fail — its --self-test breaks each in memory against the real tree and
# was reporting SELF-TEST FAIL on a clean tree because a mutation it could no
# longer apply read as a miss. It costs a second, so run it here rather than
# trusting that someone runs it by hand.
selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_web_derivatives.py --self-test

# T-0158, and it is the SECOND fault of this exact shape. `build.py --ao` baked
# occlusion that read min 0.000 / max 1.000 in Blender's own buffer and reached the
# GLB as min 0 / max 0 — every one of 262,144 texels — while the run exited 0, the
# GLB grew 4 KB and assets/manifest.json recorded `baked_ao: true`. Under glTF an
# occlusion of 0 means FULLY occluded, so the manifest was asserting good AO on an
# asset whose ambient light was extinguished. Nothing at all read the texture. This
# does, off the exported bytes, with no Blender and no numpy: an asset that carries
# an occlusion texture must carry occlusion, and the manifest must agree with the
# file in both directions. Costs a quarter-second on a town whose 348 masters all
# carry `baked_ao: false` — the moment one does not, it has a reader.
step "a shipped occlusion texture carries occlusion, and the manifest agrees" \
  python3 generators/ao_export.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 generators/ao_export.py --self-test

# Does the site ship what the repository says it ships? R-BUG3c-b (#145) cost
# three parcels because the ground a browser loads was quantised by a publish
# step AFTER the only gate that measured it, and every gate passed because every
# gate compared a render to another render. #145 fixed that instance and left
# the general case open in as many words: "Nothing else in this project measures
# a published artefact against its own source." This is that gate. publish.sh is
# almost entirely `cp`, so the invariant is total — every published file is
# byte-identical to its source unless it is on a declared list that has to name
# what transforms it and which gate measures the SHIPPED form. It found two
# unchecked files on its first run, one of them a build.json two days stale.
# Skipped rather than failed when the mirror is absent, so a fresh checkout that
# has not published yet still gates cleanly.
# NO LONGER GUARDED BY `[ -d ]` (T-0938). The guard existed because a fresh checkout
# might not have published yet, and it meant exactly that checkout skipped this gate
# without saying so. The mirror is untracked now and the step at the top of this file
# publishes it, so the mirror always exists here and the question is always asked.
selftest "deferred household notes: the card's fields stay, the reasoning leaves (T-2151)" \
  node tools/defer_household_notes.mjs --self-test

step "the shipped sidecars carry their households, notes beside them (T-2151)" \
  node tools/defer_household_notes.mjs --check

selftest "packed boot sidecars: repeated values ship once, every record comes back whole (T-2315)" \
  node tools/pack_boot_sidecars.mjs --self-test

step "the boot sidecars rehydrate to the records at their own URLs (T-2315)" \
  node tools/pack_boot_sidecars.mjs --check

step "publish.sh produces a mirror that matches its source" \
  node tools/check_published.mjs

# The frontage's timber ships prebuilt (T-2677): publish.sh builds it in Node with the
# page's own createFrontage and the page uploads it. This refuses a prebuild whose
# inputs — the records, the heightfield, every module the build loaded — have moved
# since it was written, or a buffer its index did not hash. check_published.mjs asks
# the same of the mirror; this is the tool's own --check, run where the mirror is.
# T-2693: and the ground's tiles, which the page uploads in the ground GLB's place.
# T-2709: and the distant base, which createTerrain batches in place of its own cut.
# T-2710: and the streets' two layouts, which the page batches instead of laying.
# T-2711: and the yards' five surfaces, which the page uploads in place of laying them.
step "the published prebuilt frontage, ground, distant base, streets and yards are current against every file they were built from (T-2677, T-2693, T-2709, T-2710, T-2711)" \
  node tools/prebuild_layers.mjs --check ../../site/4d/data/prebuilt --layer frontage,ground,base,streets,yards

# T-2561: a kept year is served from the device, so its pack has to list exactly
# what ships — every entry the file at its hash — or an offline visitor gets a
# file the site no longer has. The self-test holds who is in which year's pack,
# the update diff the page fetches by, and the one-line kill switch.
selftest "year packs: membership, the update diff and the kill switch (T-2561)" \
  node tools/write_year_packs.mjs --self-test

step "year packs: every file a pack lists ships at the hash it lists (T-2561)" \
  node tools/write_year_packs.mjs --check

# The front doors on chicago.polecat.live (/4d/, /4d/<year>/) are walk/index.html with
# a <base href> into walk/. Their self-test holds the one thing that can go wrong with
# that shape: a <base> that is not the first child of <head>, or a planned year with
# no door.
selftest "front doors: /4d/ and /4d/<year>/ carry a <base> into walk/" \
  node tools/write_entry_pages.mjs --self-test

# …and the page those doors copy ships without the source's developer notes, which is
# what keeps five identical copies of it under validate.py's 64 KB duplicate floor
# (T-0722) without moving the floor. The self-test holds the rules (placeholders,
# conditional comments, raw elements and attribute values untouched); --check holds
# the shipped page to the source byte for byte, less exactly its comments and stamp.
selftest "the shipped walk page: developer comments out, placeholders and raw text untouched" \
  node tools/strip_page_comments.mjs --self-test

step "the published walk page and its doors are the source less its comments (T-0722)" \
  node tools/strip_page_comments.mjs --check ../../site/4d

# The reference browsers' asset directories leave the mirror only when the site root
# already ships every byte of them (T-1828) — never a directory with new work in it.
selftest "reference browsers: only what the root already ships is served from it" \
  python3 tools/serve_from_root.py --self-test

# …and the one layer in it publish.sh transforms rather than copies. The residents
# records ship minified for the size budget, so the byte comparison above cannot see
# them; this asserts the stronger-reading claim on the SHIPPED form — same value, same
# files, nothing dropped. It is also the ONLY owner of that claim now: until T-0938 the
# two writers of the residents layer each wrote the mirror themselves and
# `apply_census_1840_bridges.py --check` asserted its own copy was fresh, which is how
# two owners came to disagree about whitespace and turn this gate red on any run that
# published (T-0933).
selftest "letter-list roster: the cohort packs and reads back exactly (T-0438)" \
  python3 tools/pack_letter_list.py --self-test

step "the published residents layer carries its source's value" \
  node tools/check_published_residents.mjs

# …and the one file in that mirror whose SOURCE is rewritten after publish.sh has
# already run. `ticket.mjs done` needs the PR number that only exists once the PR
# is open, which is after the publish, so the documented order left the gate above
# red every single time and a remembered extra publish.sh was what actually held
# it together (T-0154; it broke on T-0153/PR #318). ticket.mjs now carries the file
# to the mirror itself. This asserts BOTH halves in a sandbox — that closing a
# ticket ends green, AND that a mirror somebody else made stale still fails, which
# is the half a fix like this one could quietly destroy.
step "closing a ticket leaves the mirror fresh, and a stale one still fails" \
  node tools/test_ticket_mirror.mjs

# The same trap, one file over (T-0155). changelog.js is published to TWO paths
# check_published compares byte for byte, and stamp-changelog.mjs rewrites the
# source — so a run that stamps AFTER publish.sh was red for following the rules.
# The stamper now carries both mirrors itself. Both halves again: that stamping
# late ends green, AND that a mirror somebody else made stale still fails.
step "stamping the changelog leaves both mirrors fresh, and a stale one still fails" \
  node tools/test_changelog_mirror.mjs

# T-0180. The nightly bake decides whether it produced anything by asking this
# script, so the script's own assertions are the gate on that decision. The two
# it exists to hold are the two that would silently break it: publish.sh stamping
# a THIRD path, and the exclusion widening from "the stamp moved" to "those two
# files moved" — after which a real change to build.json or to the gate page
# would stop opening a PR, which is the same dead signal in the other direction.
selftest "the bake's content test refuses the stamp and nothing else" \
  python3 tools/bake_content_changed.py --self-test

# T-0454, and the sibling of the check above: that one asks whether the bake
# produced anything, this one asks WHICH TREE it was asked about. The workflow
# used to check out `origin/dev` unconditionally, so a bake dispatched against a
# branch silently rebuilt dev — and dev was fresh, so the honest answer to the
# question above was "no content" while the branch's asset stayed stale and this
# gate went on calling it stale. Two tools right about two different trees, and
# the remedy this file's own error message prints ("re-bake it — tools/bake.sh,
# or the chicago-4d-bake workflow") true of the first and false of the second.
# The decision is a script so it can be asserted, and the last four assertions
# are drift guards on the workflow itself: a rule nothing calls any more is the
# same bug wearing a different hat.
selftest "the bake builds the ref it was given, and the nightly still builds dev" \
  python3 tools/bake_ref.py --self-test

# T-1668, and the third question about one bake: that one asks WHICH TREE, the
# one above it asks whether it PRODUCED anything, and this asks whether it was
# WORTH STARTING. A full-town bake is twenty-five minutes and two
# `pr-automerge` laps are eighteen, so until this existed every pull request
# touching `generators/` became a `resume` PR by arithmetic, however green —
# measured on T-1652/PR #104, whose three files could not move a vertex and
# whose own staleness gate said so (422 assets matching, no rebake). The path
# filter cannot tell "could have staled a mesh" from "did", so the decision now
# asks the freshness register that `run_stale_check` above already refuses the
# tree with. Every case that cannot be established bakes, and the assertions
# here are what keep that true: the four fail-open paths a green tree can never
# demonstrate, the carve-out for a workflow edit confined to the gate job, and
# drift guards that the workflow still asks at all.
selftest "the bake is skipped only when the freshness register says nothing staled" \
  python3 tools/bake_warranted.py --self-test

# T-2314. A whole-town bake derives only the masters the record says moved; deriving
# all ~714 pushed the content-build job past its thirty-minute ceiling.
selftest "a whole-town bake derives exactly the masters whose bytes moved (T-2314)" \
  python3 tools/stale_derivatives.py --self-test

# The duplicate-id remedy, tested in the only state it ever runs in. `restamp`
# used to find the ticket by FILE (its own comment explains that with two files
# sharing an id, nothing else can tell them apart) and then edit the queue by ID,
# so it rewrote whichever of the two lines the owner had ranked higher — a coin
# toss, and on 2026-08-27 it clobbered a real ticket's line and left a stale one
# behind with every gate green (T-0217). This runs the repair on BOTH orderings of
# the same fixture, because the old code passed one of them by luck.
step "restamp moves the queue line it was handed, not the other one" \
  node tools/test_ticket_restamp.mjs

# `new --after T-NNNN` is how a run files what it finds BESIDE the work it serves
# instead of at the foot of the queue (owner, 2026-09-10: the file had reached 195
# lines with the bottom third never worked). A placement flag can fail four quiet
# ways — land at a fixed index, move a neighbour, fall back without saying so, or
# leak the anchor id into the title — and this runs the same call against two
# orderings of one fixture so the line is shown to follow the ANCHOR.
# Since 2026-09-27 the same test holds the owner's band-9 rule: a follow-up that is not
# the owner's lands at the foot of band 9 unless `--blocks "<why>"` says what it blocks.
step "new --after places directly under the named ticket and moves nothing else" \
  node tools/test_ticket_after.mjs

# THE CLAIM IS A LOCK, and this is what holds it shut. On 2026-09-11 six open PRs
# turned out to be six runs working tickets another run had already finished —
# T-0990, T-1008, T-0867/T-0868, T-1026, T-0424, T-1011, every one closed on `dev`
# by somebody else. The cause was visibility, not merging: `claim` writes a ticket
# FILE that reaches `dev` only when its PR merges, and the branch scan can only see
# a branch that has been PUSHED, which happens about an hour later. T-1026's loser
# claimed 24 minutes after its winner and 77 minutes before the winner pushed.
#
# So the claim takes a marker ref on the remote first, and the SERVER decides who
# gets it. A lock is worth nothing asserted in the abstract, so every case here
# runs ticket.mjs twice against a real bare repository: two runs contend, an
# unreachable remote never stops a run, a dead claim is stolen and a live one is
# not, two stealers of one dead claim produce one winner, `done` lets go, and a
# runner with no git identity still takes it (the `fatal: empty ident name` that
# silently broke every PR lap until 2026-09-10). It found two real faults while
# being written: `??` passing an EMPTY identity through, and — the one that
# mattered — two runs claiming in the same second building the identical commit
# object, so git answered the loser `Everything up-to-date`, exit 0, and told it
# that it had won. That is the exact case the lock exists to decide.
step "a claim is a lock on the remote, and two runs cannot hold one ticket" \
  node tools/test_ticket_claim_lock.mjs

# AND THE LAP THAT CARRIES ALL OF IT MUST NEVER BE QUIETLY USELESS. On
# 2026-09-14 `gh pr list` hit a rate limit, pr-lap.sh's `PRS=$(...)` took the
# failure without `-e` to stop it, and the run printed
# `PR lap: pushed=0 already-current=0 left-alone=0 red=0` — what a healthy idle
# lap prints — and exited GREEN having lapped nothing. Every lap in that window
# read clean while sweeping nothing, which is what a stuck PR queue looks like
# from outside. This runs the REAL script against a faked `gh`.
step "a lap that could not ask never reports that it found nothing" \
  node tools/test_pr_lap_list.mjs

# AND THE LAP MUST BE ABLE TO FINISH A REBUILD IT STARTS (T-1521). `site/4d/` is
# generated and untracked (T-0938), so the lap's checkout has no mirror — and step
# 156 of 156, `rebuild_closing_set.py --build`, reads the published residents and
# REFUSES rather than write a count it did not take. The lap ran `rederive.mjs`
# without publishing, so every lap over such a PR failed at the same step and left
# it alone FOR EVER, which from outside looks exactly like a queue the lap has not
# got to. Measured 2026-09-21, lap run 35624254338: #1629, #1630 and #1631 sat
# unmergeable with GREEN gates while the lap reported success. This gate publishes
# first for the same reason (its step 1); the lap now does too. The suite runs the
# REAL script over a REAL bare remote with stub tools, and then runs it AGAIN with
# the publish neutered and requires that to fail — a regression test that cannot
# see the regression is decoration.
step "the lap publishes the mirror before the rebuild that reads it" \
  node tools/test_pr_lap_publish.mjs

# ...AND WHEN IT CAN ASK BUT CANNOT CHECK OUT, IT HAS TO SAY WHY (T-1565). The
# lap's two entry guards said four near-identical words each — `fetch failed`,
# `checkout failed` — with git's stderr sent to /dev/null, so #1629's failure on
# 2026-09-21 left a run summary with no reason in it at all: not which of the two
# failed, not git's message, not the ref it could not resolve. Every other refusal
# in the lap names its step and tails its log, which is how T-1521 was found.
# This one runs the REAL script against a REAL bare remote with REAL git — the
# faults live in git's own refusal messages, so a fake git would test the fake.
step "a lap that cannot check out a branch says which step failed, and why" \
  node tools/test_pr_lap_checkout.mjs

# ...AND A BRANCH LEVEL WITH dev IS NOT THEREFORE CURRENT WITH dev'S GATES (T-1362).
# The lap rebuilt the derived layer only inside a merge, so a branch with nothing to
# merge never reached it: #1487 sat red on four stale manifest-owned files while the
# lap printed `already current — nothing to lap`, and #1518 for two hours the same
# way. The lap now reads the head's own `gate` verdict (one REST call) and re-derives
# a current branch only when that reads red; a rebuild that moves nothing pushes
# nothing and says so on the PR once per head. REAL script, REAL bare remote, stub
# tools — and run again with the old exit restored, which must fail.
step "a branch level with dev but red is re-derived, not called current" \
  node tools/test_pr_lap_current.mjs

# ...AND TWO BAKES OF DIFFERENT STRUCTURES ARE NOT A CONFLICT (T-2892, owner 2026-10-19).
# assets/manifest.json and assets/manifest.web.json are one object each for the whole
# town, rewritten whole by every bake, so two PRs that baked different houses conflicted
# there and the lap left them alone as a REAL CONFLICT — #1104 on 2026-10-19, conflicting
# on manifest.json and nothing else, until a steward run paid a whole lap. The merger
# takes each entry from the side that changed it, re-emits on the merged tree any
# pure-emitter asset whose recipe moved on both sides (byte-identical or refused), and
# refuses a master both sides rebuilt. Its self-test merges in scratch repositories; the
# lap test runs the REAL lap over a REAL bare remote, then again with the step cut out,
# which must leave the PR alone.
selftest "the asset registries merge entry by entry, and refuse a master both sides rebuilt" \
  python3 tools/merge_asset_registry.py --self-test
step "the lap clears a registry-only conflict, and still leaves a real one alone" \
  node tools/test_pr_lap_registry.mjs

# ...AND THE LAP UNPACKS THE GLESSNER PACKAGE AGAIN AFTER MERGING (T-2907). Its clone laps
# every PR in turn and the unpacked v4 GLBs are IGNORED files, so after dev repacks the
# archive the copy on disk is the old one and publish.sh refuses it — #1114 was left alone
# for exactly that on 2026-10-19, right after its registries merged. REAL lap, REAL bare
# remote, a stub publish that refuses a stale output as the real one does; and again with
# the refresh cut out, which must leave the PR alone.
step "the lap unpacks the Glessner package from the merged tree before it publishes" \
  node tools/test_pr_lap_package.mjs

# ...AND NEITHER THE LAP NOR THE MERGER TOUCHES A PR A LIVE RUN IS LAPPING (T-2929). A run
# takes `lap/pr-<N>` before it laps a `resume` PR (T-1721), and every RUN honoured it; the two
# server sweeps never read it. #1132's lock was taken at 13:00Z on 2026-10-20, the lap pushed
# df6ae544a over it at 13:19Z and merge-ready merged that at 13:37Z — the holding run's merge,
# re-derive, check.sh and smoke all thrown away. Both now ask `ticket.mjs lap <N> --status`,
# the same reading `lap` steals by. REAL scripts, REAL ticket.mjs, REAL bare remotes: held is
# left alone, stale is not, unreadable is reported and not acted on, a lock taken mid-lap stops
# the push; and each script again with its read cut out, which must touch the held PR.
step "the lap and the merger leave a PR whose lap lock a live run holds" \
  node tools/test_pr_lap_lock.mjs

# AND THE THING THAT ACTUALLY MERGES A FINISHED PULL REQUEST, which for most of
# this repository's life was NOBODY. The lap's header said auto-merge did it; the
# fleet janitor said the lap plus auto-merge did it, while excluding `custom`
# from its own roster; the only `gh pr merge --auto` in the repo is in
# chicago-4d-bake.yml and fires on bakes. Checked 2026-09-14: #1327 and #1312
# both merged with `auto_merge: off` — by hand. So the lap made pull requests
# clean, CI made them green, and the queue still did not drain.
# merge-ready.sh closes that, and the state it merges on is the one thing that
# must never drift: `clean` is GitHub's own verdict that the branch merges AND
# every required check passed, while `blocked` — which every PR reads while its
# gate runs, i.e. all of them at once after a lap — must never merge. This runs
# the REAL script against a faked `gh` and asserts exactly that.
step "the merger merges what GitHub calls clean, and nothing else" \
  node tools/test_merge_ready.mjs

# AND THE PULL REQUEST NOTHING CAN MOVE, WHICH IS THE HOLE BETWEEN THOSE TWO
# (T-1368). A `dirty` PR has no merge ref; the gate runs on `pull_request`, which
# needs one, so it never starts and the PR carries ZERO check runs; `gate` is a
# required check, so GitHub never calls the PR `clean`; merge-ready merges only on
# `clean`; and the lap correctly refuses a conflict no tool owns. Nothing in that
# loop advances. Six pull requests hit it in two days — #1495 and #1497 on
# 2026-09-19, #1587, #1585, #1584 and #1590 on 2026-09-20 — and every one needed a
# person. Both of the first two merged THEMSELVES within minutes of a human
# pushing the merge, which is the proof that the rest of the automation is sound:
# the only missing piece was anyone being told.
#
# .github/steward/pr-stuck.sh is the telling, and the hard part is not finding the
# shape but REFUSING the three things that wear it — a `hold` PR (#1533, #1576,
# both mistaken for this on 2026-09-20), a PR whose own run is still going (#1499,
# which cleared itself), and a PR that is merely `unknown` (#1518, which merged
# fine when asked). This runs the REAL script against a faked `gh` and holds it to
# all three, and it found a live fault while being written: GNU `date -d ""`
# answers midnight today rather than failing, so an unreadable timestamp read as
# hours old and would have had the reporter declaring PRs stuck on no evidence.
step "a pull request nothing can move is reported, and nothing else is touched" \
  node tools/test_pr_stuck.mjs

# AND THE OTHER LABEL — the one a RUN applies to its own unfinished work (T-1573).
# `hold` is the owner's park switch and every pass above skips it on purpose,
# which is right; what was wrong is that the steward prompt told a run to apply
# that same label whenever it merely could not FINISH, so work needing nobody's
# decision had nothing coming for it either. Owner, 2026-09-25, on the three PRs
# parked that way: "that seems like a bad move because i am not aware of why they
# are held" — and he was right twice over, because #39's stated reason was already
# stale (CI had passed all 620 steps) while #41 and #42 were simply COMPLETE.
# `pr-rest.sh resume` is the replacement, and its whole value is one machine-
# readable line — `resume: <reason> · waits on: <T-NNNN|nothing>` — that pr-stuck
# reads back into every sweep. A reason lost to a stray newline, or a label applied
# before the reason is written, rebuilds the silence exactly. This runs the REAL
# script against a faked `gh` and holds it to the order as well as the content.
step "a run that cannot finish hands its PR on, and says why in a line a script can read" \
  node tools/test_pr_resume.mjs

# AND THE QUESTION THE LOCK CANNOT ANSWER: has this ticket's PR already MERGED?
# Everything here squash-merges, so a merged branch never becomes an ancestor of
# `dev`; `inflight` is honest about that and falls back on branch AGE, which makes a
# finished ticket read as litter rather than as done. T-0429 sat `claimed` behind a
# cold branch for five days as the topmost queue line carrying no PR — the exact
# shape of available work — and a run rebuilt the whole block, 116 files and 5,827
# insertions, onto records already on `dev` under the same ids.
#
# `ticket.mjs landed` asks the one question that settles it, against the closed PRs.
# THE GATE DOES NOT CALL THE NETWORK: this step runs the tool on a CONSTRUCTED PR
# list, which is the only honest demonstration of a check whose correct answer
# against the real `dev` changes hourly. What it holds is the three refusals that
# make the report trustworthy — a queue-keeping title ("File T-0968: …", "Pull
# T-0802 up…", "Rank T-0727 under…", three real merged PRs that touched none of the
# work they name) is not a claim of authorship, a `done` or `blocked-owner` ticket is
# not a finding, and an unreachable API degrades to silence rather than to an
# accusation — plus the one that makes it safe: it exits 0 whatever it finds, because
# a gate that hard-fails on a naming convention blocks a run that did nothing wrong.
step "a merged PR naming an unfinished ticket is REPORTED, and nothing else is" \
  node tools/test_ticket_landed.mjs

# AND THE OTHER HALF OF THE SAME BLIND SPOT (T-0852). `inflight` read branch AGE and
# nothing else, so a run that claims and then READS sources for four hours dropped out
# of the hot list at three — into a list headed "finished tickets, or branches older
# than a run", which is false about it twice over. Cohort 14 (T-0509) was read twice on
# 2026-09-05 by two runs that could not see each other; the ledgers disagreed on 36 of
# the 76 people and T-0816 had to adjudicate every one.
#
# The reading now takes TWO witnesses, and the second is what keeps the fix honest. The
# ticket file saying `claimed` is necessary and not sufficient — T-0987 is worked one
# stretch per run and sits `claimed` on `dev` permanently, so the file alone reported
# seven of its long-merged branches as in flight. The CLAIM LOCK is the other: it is
# taken with the claim and released by `done`, so it lives exactly as long as the run.
# Held is reported as in flight and SAID to be a long read or a dead one, because
# T-0429's fault runs the opposite way and must stay visible.
#
# The gate runs it on a CONSTRUCTED branch list for the reason `landed` does: the right
# answer against the real remote changes hourly. Both wrong readings are held — age
# alone fails the fault, the file alone fails T-0987 and T-0429.
# AND THE READING THAT WAS DEAD IN PRODUCTION WHILE THIS STEP RAN GREEN (T-1427). The
# `recoverable` reading guards itself with "a branch that ever HAD a pull request was
# never invisible", which reads `pr.head.ref` — and `restGet` projected that field away,
# so against the live API the guard was an empty set that could never fire, while the
# fixture below supplied `head.ref` by hand and this step passed. The fetch asked for
# `state=closed` besides, so an OPEN pull request was not in the collection at all. On
# 2026-09-20 `inflight` printed five branches as carrying work NOBODY CAN SEE and every
# one of the five had a pull request; `steward/t-1191-north-corridors` was one, and #1533
# on it was open, labelled `hold`, and parked for the owner on purpose. The one reading
# that exists to stop a duplicate rebuild was inviting one. The fixture and the API now
# arrive through one projection, so a fixture can no longer be richer than production.
step "a claim that outlived the window is work, a merged branch is litter, and a branch under review is neither" \
  node tools/test_ticket_inflight.mjs

# A SPLIT KEEPS ITS CLAIM, so the parent it leaves on `dev` cannot be claimed twice.
# T-1145 on 2026-09-17: one run claimed it at 03:38:16, split it, and the release
# handed claim/t-1145 back while its own PR was unopened; a second run read `dev`,
# where the split had not landed and the parent was still `open` at the top of the
# queue, and claimed it at 03:57:43. Both split it into different children and built
# plural dated roles twice, with colliding ids. A split is not finished work — the run
# carries on for another hour on a child, which is the widest window any terminal state
# has. The litter that made `split` release is collected by age instead.
step "a split keeps its claim, and the queue drops only finished work and regains what a merge lost" \
  node tools/test_ticket_claim_split.mjs

# THE TICKETS REPOSITORY (2026-09-23). Since the move to kevinrhaas/chicago-tickets a
# claim is a pushed commit, `done` is `review` until `settle` sees the PR merge, new ids
# are renumbered when another writer took them first, and `ask` keeps a decision in the
# queue. Every one of those is run for real here: two clones of one bare repository.
step "the tickets repo: claim is a pushed lock, done waits on the merge, ask stays in the queue" \
  node tools/test_ticket_repo_mode.mjs

# A PARKED PULL REQUEST IS THE ONE KIND NOTHING IS COMING BACK FOR (T-1576). The lap,
# `merge-ready.sh` and `pr-stuck.sh` all read labels before state and all skip `hold` on
# purpose, so a held PR is invisible by design — and the only place its reason was
# written was the PR body. The owner, 2026-09-25, finding three at once: "that seems
# like a bad move because i am not aware of why they are held". `board --parked` puts
# every open `hold`/`resume` PR on the board with its reason and its age.
#
# THE READING THIS STEP EXISTS FOR IS THE BLIND ONE. An empty section and a section
# whose PR list could not be read print identically unless something makes them differ,
# and the second dressed as the first is the same silence one level up. The fixture is
# a constructed PR list for the reason `landed --pr-json` takes one: against the live
# repository the right answer changes by the hour, so what a gate can hold is the
# READING. It reaches no network.
step "every held or resumable pull request reaches the board with its reason, and an unread list says so" \
  node tools/test_ticket_parked.mjs

# ONE RUN PER HOUSE AT A TIME (owner, 2026-10-19). Three slices held Glessner at once
# (#1090, #1091, #1094): each rebaked the house, each conflicted with the others' bakes,
# and their full smokes queued three hours and were cancelled. `claim` refuses a ticket
# whose house has a live claim, a ticket in review, or an open PR titled with a ticket of
# the same house, and `list --workable` marks the row HOUSE BUSY. Run for real against a
# tickets repository of its own; it reaches no network.
step "claim and list hold a 1904 house to one run at a time" \
  node tools/test_ticket_house_serial.mjs

# A RUN MAY TAKE A GROUP (T-2938, owner 2026-10-20: "when claiming a ticket, it can and
# should evaluate if it can claim multiple and handle them as a group in a single PR").
# `claim A B C` asks every member the single claim's questions, claims what passes in ONE
# pushed commit, reports each refusal and exits non-zero only when none was claimed; a
# member taken mid-push is reported and the rest re-claimed. `done A B --pr N` is all or
# nothing; `--with T-A` grows a held group (never inferred from a shared run URL);
# `release` gives back a claim the run will not finish; `list --group` is the shortlist.
# T-2940 rides the same sandbox: `new` files a follow-up into the band of its KIND (perf to
# band 1's foot, a building beside its own lines, ops to band 9's foot found by header).
# Run for real against a tickets repository of its own; it reaches no network.
step "a run claims, closes and releases a group of tickets as one unit" \
  node tools/test_ticket_group.mjs

# A GATED WRITER BELONGS IN THE MANIFEST (T-1282, owner 2026-09-18). A tool this gate runs
# with --check, and that can also write, produces DERIVED content by definition — so if
# derived_manifest.json has never heard of it, rederive.mjs never runs it, the lap leaves
# every open PR stale and this gate goes red with no automated remedy. That cost four
# separate hand-fixes on the night of 2026-09-17. The rule was already written in the
# manifest's preamble and did not hold, so it is a step now.
step "every gated writer is in the derived manifest, or exempted in writing" \
  node tools/audit_manifest_coverage.mjs

# T-1339, and it sits beside the writer coverage above because it is the same argument one
# question over. That gate asks WHICH TOOLS WRITE; this one asks WHICH OF THEM WRITE WHILE
# THE GATE IS RUNNING, which is a different failure with a worse signature.
#
# check.sh runs its steps in a job pool over ONE working tree (T-1289). A step that mutates
# that tree is read by whatever runs beside it, so the gate reports red on a tree that is
# green — four PRs went red that way on 2026-09-18 before the cause was found, and every one
# of them looked like a defect in the branch. T-1336 fixed the six self-tests responsible and
# put a retry behind them, which keeps the VERDICT correct; it does not stop the seventh
# being written, and TWO OF THE SIX carried comments claiming they already worked on a copy.
#
# So the answer is a measurement and not a convention, exactly as T-1302 answered "which
# tools write?" with a measured inventory rather than a pattern over the source. The slow
# half is tools/measure_step_isolation.mjs --build (one instrumented gate run); this reads
# what it wrote and costs milliseconds. An unmeasured step fails here, because an empty file
# would otherwise read as proof.
step "no gate step writes the live tree, and every one of them has been measured" \
  node tools/audit_step_isolation.mjs --check --quiet

selftest "…and it refuses an unmeasured step as well as a mutating one" \
  node tools/audit_step_isolation.mjs --self-test

selftest "…and the measurement's own readers still parse what check.sh declares" \
  node tools/measure_step_isolation.mjs --self-test

# A QUEUE LINE THAT STILL NAMES A FINISHED BLOCKER. T-0464 closed on 2026-09-14
# (#1257) and the three lines that LEAD South Through Time — T-0465, T-0466,
# T-0467 — all went on reading `blocked_on: T-0464` the next day. Nothing had to
# consume the field for it to cost a run: a steward picking work opens the top
# line, sees another ticket's id in `blocked_on`, and steps over it. On
# 2026-09-15 the band's lead sat unclaimed while the line below it was taken, and
# the owner is the one who noticed. The blocker's own state is the receipt, so
# `check` asks it rather than trusting the field to be swept by hand.
#
# SCOPED TO TICKETS STILL IN THE QUEUE, and the harness asserts the scope as hard
# as the fault: 16 tickets on dev named a finished blocker and only THREE were
# workable. The other 13 are themselves done or withdrawn, where the field is
# honest history nobody chooses work from — failing on those would be noise
# guarding nothing, and noise is what gets a check weakened later.
step "a queue line blocked on a finished ticket is refused, and a closed one's is not" \
  node tools/test_ticket_stale_block.mjs

# And band 8b, which T-1518 made the home of every blocked ticket, is now WRITTEN BY
# THE TOOL (T-1541). `block` used to drop the queue line and write nothing, so the
# line T-1518's gate demands was hand-written: T-1479 stood in no band until a run's
# gate caught it, and T-1532 and T-1536 each stood twice because two branches wrote
# the same block. `block` writes the line once (a re-block replaces it), `unblock`,
# `withdraw` and `done` take it out, and `check` refuses a band line standing twice.
step "band 8b: block writes a blocked ticket's line once, unblock takes it out, a twice is refused" \
  node tools/test_ticket_blocked_band.mjs

# And the collision the lane's parallelism makes inevitable. `nextIdNum` scans
# every origin ref before it mints, so a duplicate id is not a missing guard but
# the window between minting and pushing — on 2026-09-10 PRs #1048 and #1049 each
# filed T-0988 ten minutes apart. The merge is clean and this gate then goes red
# twice: on the duplicate, and on the survivor's queue line, which merge-queue.mjs
# ate because it reconciles QUEUE.md by id. pr-lap.sh heals both, so what it heals
# with has to be held: the side on the base never moves, references follow only
# when they were written where the moving ticket already existed, and both sides
# already on the base is a refusal rather than a coin toss.
selftest "…and a duplicate id renumbers the branch's side, carrying only its own references" \
  node tools/resolve_id_collisions.mjs --self-test

# And the tool asked of THIS tree, not only of its fixture. Green whenever every id
# is unique, which needs no base ref at all — the base is only consulted once there
# is a collision to attribute, so this cannot go red for want of a fetch.
step "no two tickets in this tree carry the same id" \
  node tools/resolve_id_collisions.mjs --check

# THE MANIFEST THE PR LAP RESOLVES RESEARCH CONFLICTS BY. It names, file by file,
# which parts of the derived research layer a tool rewrites from source — so a
# merge conflict in one of them is cleared by taking either side and rebuilding,
# the same rule pr-lap.sh has always applied to the five generated files. Held
# here because the manifest is the safety property: a path that drifts out of the
# tree, a file claimed by two steps, or a hand_authored file listed as derivable
# would each let the lap overwrite something nobody derives. The REBUILD itself is
# proved by the ordinary --check steps throughout this file; this holds the list.
#
# AND SINCE T-1363 it also holds the manifest's SECOND PASS — the short list of steps
# re-run after the sequence because they read a file the sequence rebuilds under them.
# The arrival stage is the one that needs it: it draws from the town model, and the
# town model is rebuilt further down from a profile of the cards it writes, so a single
# pass ends with ~1,400 cards drawn from a model that no longer exists. No ordering
# fixes a cycle; the pass walks it once more from a settled model. What this step holds
# is that the pass stays honest — every entry re-runs a command the sequence already
# gates and proves, the lagging reader leads it, and the file it lags on is genuinely
# rebuilt below it. That the pass SETTLES is proved elsewhere in this file, by the
# resident, tier, profile and town-model --check steps all being green after it.
step "the derived-layer manifest names real files, one owner each, none hand-authored, and its second pass is a real lag" \
  node tools/rederive.mjs --check

selftest "…and its own assertions fire when the manifest is made unsafe" \
  node tools/rederive.mjs --self-test

# AND THE ONE WAY THE MANIFEST'S ORDER IS REOPENED FROM OUTSIDE IT (T-1661). The lap
# has to re-run compile_scene AFTER `rederive.mjs --run`, because the second pass
# rewrites the resident cards the scene is compiled from. For a year it re-ran that step
# and nothing else — and the manifest places 37 steps below it, the first of which
# exports "current-scene membership" out of the two files compile_scene writes. So the
# lap pushed trees whose source-use had been derived against the PRE-merge scene:
# measured on PR #105's lap commit 4455713, owner_chicago_1835_reconstruction_spec_2026
# written with 3582 claims where a correct derivation gives 3620. 38 claims gone, nothing
# in the tree announcing it, three of this file's steps red — and the branch reported by
# GitHub as merged and up to date. A lap that merges green PRs cannot be the thing that
# hands the next pass a red gate it did not cause.
#
# `--tail` is the fix and this step is what keeps it: a manifest step re-run bare by any
# caller is out of sequence unless the manifest puts nothing below it. Held HERE rather
# than left to review because the reopening is one line of shell in a file nobody reads
# on a normal day, and its damage is invisible without the gate.
step "no caller of the derived manifest re-runs one of its steps out of sequence" \
  node tools/rederive.mjs --callers .github/steward/pr-lap.sh

# AND THE FIVE FILES THAT CLOSE THE RESIDENT LAYER, AS ONE SET (T-1333). index.json with
# its `merged` redirect table, the 1835 sidecars, the town census, the published residents
# and the final resident audit are each derived and each already gated above — and until
# this step nothing said they were a SET or what order they rebuild in. That is not a
# tidiness complaint: every `--check` above asks whether a file still follows from its
# inputs, and a file nobody rebuilt at all follows from its inputs perfectly well until
# somebody else's rebuild moves them. So a run could move the town, rebuild three of the
# five, and leave a green gate behind. This holds the membership (a member the derived
# manifest does not run, or an exemption that states no reason, is red), the gating (a
# member this file never asks `--check` of is red) and the REPORT, which states every
# number as a delta against the tree T-1333 opened on — so a branch that moves the town
# and leaves docs/RESEARCH/closing-convergence-2026-09.md alone goes red rather than
# shipping a page that still reads clean. T-1144 banked its acceptances 3, 5 and 9 here to
# be stated as measured deltas rather than re-asserted from a spot reading; they are rows
# in that report now, and a refused name coming back moves one.
step "the closing set is owned, gated and reported as deltas" \
  python3 tools/rebuild_closing_set.py --check --quiet

selftest "…and its own assertions fire when a member loses its owner, its gate or its reason" \
  python3 tools/rebuild_closing_set.py --self-test

# The other restamp, and the more dangerous one: `tools/restamp_inputs.py` rewrites
# `assets/manifest.json`'s input hashes without a bake, which is the only honest
# answer to a change in the input-hash RECIPE (T-0164) and would be a silent way to
# bless a stale mesh at any other moment. Its guard is that a SCHEME constant must
# have moved, and a committed tree — where the schemes agree by construction — is
# exactly the negative fixture that proves the guard still holds.
step "restamping the input hashes is refused when no recipe changed" \
  python3 tools/test_restamp_inputs.py

# The integration preview's assembler. It lives at the repo root because the
# deploy workflow does, but nothing else tests it, and it is the only thing that
# marks the preview as a preview — the noindex, the banner, the build stamp. A
# preview that quietly stops saying "DEV PREVIEW" is one screenshot away from
# being reported as a production bug. Skipped rather than failed when the script
# is absent, so a checkout of chicago/4d alone still gates cleanly.
if [ -f ../../.github/chicago-4d-dev-preview.mjs ]; then
  step "dev preview assembles, marked and stamped" \
    node tools/test_dev_preview.mjs
fi

# Every JSON in data/ must be loadable — a stray comma here breaks the whole build
# in a place far from the edit that caused it.
check_json() {
  python3 - <<'PY'
import json, sys
from pathlib import Path
bad = 0
n = 0
for p in sorted(Path("data").rglob("*.json")):
    n += 1
    try:
        json.loads(p.read_text())
    except json.JSONDecodeError as e:
        print(f"   invalid JSON: {p}: {e}")
        bad = 1
print(f"   {n} data file(s) parsed")
sys.exit(bad)
PY
}
# Attested must cite a source, an inference must record what it reasoned from,
# and NOTHING on an invented structure may outrank the invention that put it
# there. That last rule is the one that mattered: without it, 158 buildings that
# never existed graded their wall heights as evidence and rendered solid.
# THE ONE THING THIS COMMAND PROVES, RUN ONCE (T-0662). `--check` re-derives the
# resident synthesis over the committed cards and prints the population it writes:
# "OK: 1281 people; 404 attested, 877 inferred, 0 reconstructed; 730 projected".
# That is one fact, and it is this pass's.
#
# Until 2026-09-17 check.sh ran this IDENTICAL command five times under five labels,
# and four of those labels named a pass it does not run — so the gate read as though
# five derivations were held when one was, and it was the only command in this file
# that appeared more than once. Each of the four passes those labels named carries a
# `--check` of its own; on that day every one of them was RED and carried as ungated,
# with its reason and its owner, in data/research/check_gate_baseline.json:
#
#   tools/generate_inferred_households.py  (was the K1 households step)
#   tools/generate_inferred_names.py       (was this step's old label)
#   tools/replace_invented_residents.py    (was the T-0264 roof-deal step)
#   tools/mint_letter_list_residents.py    T-1222  --check: 798 file(s) differ
#
# T-1228 gated the first three on 2026-09-17, each at its own slot above, on a
# field-level ownership contract rather than byte-identity — the same shape T-0662
# found the letter-list mint wants. T-2070 gave the mint that contract on 2026-10-04,
# and its `--check` runs at the mint's own slot below.
#
# `mint_documented_residents.py` was on that list until T-1220 read its 10 files, fixed
# the two faults under them and committed the rest; it is a step of its own below.
#
# The invented names the old label spoke of are re-derived by
# `generate_inferred_names.py --check`, not here. `audit_check_gates.py --gate` now
# refuses a check.sh in which any one command runs under more than one label, so a
# step cannot borrow another pass's command again.
# T-1144 acceptance 8, and the gate the reconstruction bands are about to need.
# `grade` says whether the sources name a person at all: `attested`, `inferred`, or
# the reserved `reconstructed` — someone the sources do NOT name, drawn from the
# population model. The owner retired that population on 2026-09-02 and ruled it
# returns only under an explicit programme file; T-1167 is where it does. Until
# 2026-09-18 the boundary held only because all three mints happen to hardcode
# `"grade": "attested"` and the synthesis happens to retire anything else. Nothing
# asserted it, and T-1228's finding two slots below is what an unasserted invariant
# is worth. Each of the four writers now refuses on the way out, in EVERY mode, so
# `--check` is red on the same rule the write is; this step proves the committed
# layer holds none and that all four calls are still there. It is the CALL that is
# checked, not the import: a refusal imported and not called is the shape this
# guards. Per-attribute `confidence: reconstructed` — "Not attested", on one field
# of a real person — is untouched and must stay that way.
step "no research writer can mint a reconstructed resident" \
  python3 tools/refuse_reconstructed_grade.py --check

selftest "...and the refusal fires, while leaving per-attribute confidence alone" \
  python3 tools/refuse_reconstructed_grade.py --self-test

# T-1167, the other side of that boundary. One tool MAY mint the grade, and this is it:
# it does not call the refusal above, and in exchange every person it writes has to show
# which model row or rule drew them, the seed that redraws them, what evidence would
# retire them, and which stage of the programme wrote them. `--check` re-derives every
# implemented stage and holds the committed layer to that contract, so a reconstructed
# resident nobody can audit cannot reach dev. The 2026-09-02 retirement had to remove a
# whole population because no record answered those four questions.
step "the reconstruction programme answers for every reconstructed resident" \
  python3 tools/reconstruct_residents_1835.py --check

selftest "...and each rule of the record contract refuses its own mutation" \
  python3 tools/reconstruct_residents_1835.py --self-test

# T-1169. Two kinds of writer now touch data/residents/households/*.json: four mints
# that re-derive the whole record from their registers, and the reconstruction
# programme's stages, which write attribute blocks onto records the mints own. Each
# mint's --check compares the file it derives byte for byte, so the first stage to
# write anything put three of them into drift on 1,247 files. Ownership is PER
# ATTRIBUTE — the grain T-1158 already cut — and this asserts the wiring that makes it
# so: a mint that stops carrying would delete a stage's work on its next --build, and
# nothing else here would notice until the values were gone.
step "every mint that re-derives a household carries the blocks it does not own" \
  python3 tools/carry_stage_blocks.py --check

selftest "...and its own assertions still fire when broken" \
  python3 tools/carry_stage_blocks.py --self-test

# T-1523, the first thing to use that slot for anything but an arrival. T-1522 dealt a
# division to the 1,305 households no source places anywhere and wrote it in the address
# book ALONE, so the card and the manifest both still read `unplaced` and the People
# view's division filter was short of 1,526 people. This carries the dealt value onto the
# card as `division_reconstructed` — marked `reconstructed`, carrying the digest that
# placed it — and holds the two halves against each other in both directions: a dealt row
# whose card does not carry it is the invisibility T-1522 left, and a carried card the
# book deals nothing for is a block nothing re-derives. It also holds the scalar
# `division` at `unplaced`, which is the whole point of the block: rung 5 IS the
# households whose record places them nowhere, and `a_stated_division` would otherwise
# turn every one of them into a house.
step "the policy-only rung's dealt division is on the card the town shows" \
  python3 tools/carry_policy_only_division.py --check

selftest "...and every limit on that carry fires when broken" \
  python3 tools/carry_policy_only_division.py --self-test

# T-1350, the other half of that ownership and the opposite failure. A mint derives
# `arrival` as a not_later_than BOUND off its register, which is right until a reading
# says more than the register can — Moses and Kirkland's list of the spring of 1833
# names men the town's paper does not print for another year. Such a reading used to
# be written onto the card by hand and then REVERTED by the next --build without a
# word; T-1340 watched six of its rulings go that way and wrote the failure down. The
# ledger below is how one reaches a card the mints own, and the gate is what keeps it
# from becoming a way to write any date anywhere: no identity is made there, no reading
# is invented there, a supersession must be EARLIER than the bound it replaces, and the
# grade ceiling is the source's.
step "every ruled reading that supersedes a derived arrival bound is joined and earlier" \
  python3 tools/supersede_arrival.py --check

selftest "...and each of its four refusals still fires on its own case" \
  python3 tools/supersede_arrival.py --self-test

# T-1171, stage `modelled_families` of that programme, and the first one to write a
# PERSON rather than an attribute block. 94 heads the sources leave standing alone get
# the wife and children the household model says they kept, drawn at the head's own size
# band off the 1840 city's histogram, seeded on the household id, and counted into the
# order book — which refuses a draw rather than overfill a bucket. The stage's own
# --check strips its people out of the committed layer, draws them again and refuses a
# differing byte; `reconstruct_residents_1835.py --check` above holds each of them to the
# record contract, which is the other half.
step "the modelled families re-derive from the household model and the order book" \
  python3 tools/reconstruct_modelled_families.py --check

selftest "...and every rule that decides who gets a family refuses its own case" \
  python3 tools/reconstruct_modelled_families.py --self-test

# T-1172, stage `readmissions` of that programme. The borderline roster (T-1159) holds
# every name the corpus PRINTED and the research WITHHELD; this stage spends four of its
# seven classes, and it overturns no refusal. What the gate below holds: that all 898
# re-admissions re-derive from the roster, the layer and the three persistence crosswalks
# they are priced against; that every minted card still answers to the record contract;
# and - the one that matters most - that every card an R1 ruling stands beside STILL reads
# `uncertain` in the research layer, so a reconstruction cannot outlive the refusal it was
# written against. A hand-edited card or a persistence rate nudged toward a nicer figure
# fails here.
step "every re-admission re-derives, and no refusal it stands beside has moved" \
  python3 tools/readmit_borderline_roster.py --check

selftest "...and a guessed date, a borrowed name and a rising persistence curve are refused" \
  python3 tools/readmit_borderline_roster.py --self-test

# T-1174, stage `women_and_children` of the same programme, and the first one to write a
# HOUSEHOLD rather than to draw into one. The rolls that name this town print men, so the
# house with no man in it is the record the sources never made and the stage above — which
# is keyed to a male head and says so in its own refusals — cannot create. This one writes
# 124 female-headed households and the 556 people in them, drawing each head's band and
# each other person's sex and band against the shortfall the order book still carries in
# that division, so the draw converges on the population model's pyramid rather than near
# it. Its --check rebuilds the whole set from the model files and refuses a differing byte
# on the keys it owns; the keys another stage wrote are that stage's to prove, which is
# why it compares an owned view rather than the card.
step "the women and children re-derive from the pyramid the order book still wants" \
  python3 tools/reconstruct_women_children.py --check

selftest "...and every rule that decides who is drawn refuses its own case" \
  python3 tools/reconstruct_women_children.py --self-test

# T-1347 (of T-1173), stage `trade_households` of the same programme. The order book's
# twenty-four `family/trade` buckets ordered 308 adults at a trade that nobody printed;
# this stage draws them as heads of their own households, deals each a trade from the
# Fergus 1839 table's shares (T-1346), caps a trade at the December 1835 State census
# where that census counts a class one person keeps, and puts the refusals and the
# rounding remainder into the residual — day labour and domestic service, the work the
# record cannot see. What the gate below holds: that all 308 re-derive from their seeds,
# that every bucket is filled to its order and no further, that no trade outside the
# controlled vocabulary reaches a person, and that no kin is seated here — the family each
# head is owed is written as `household_owed` and seated by T-1174, whose quota it is.
# `reconstruct_residents_1835.py --check` above holds each drawn person to the record
# contract, which is the other half. A hand-edited card fails here.
step "every trade household re-derives, and every bucket the book ordered is filled" \
  python3 tools/reconstruct_trade_households.py --check

selftest "...and a seniority rule, an over-ceiling trade and a borrowed name are refused" \
  python3 tools/reconstruct_trade_households.py --self-test

# T-1531, stage `institutional_households`. The household quota apportions the town's
# houses across the roof groups by ROOF COUNT, which is right for a group whose roofs are
# houses and wrong for the one group whose roofs are a church, a jail, a council house and
# a light tower: the nine standing `institutional_public` roofs drew TWELVE households.
# `data/reconstruction/1835_institutional_lodging.json` asks each of the nine the question
# nobody had asked — does this project's own record of it put a household under it? — and
# two answer yes: the Watkins house, whose function is domestic, and the light, whose
# keepership is recorded at $350 a year WITH QUARTERS. `build_order_book_1835.py` weights
# the institutional cells on that file, so the book orders two, and this stage mints two.
# What the gate holds: that both cards re-derive from their seeds, that the order never
# exceeds what the adjudication admits, that both cells are discharged, and that no
# occupation outside the controlled vocabulary reaches a person.
step "the institutional households re-derive, and the book orders no more than the nine roofs admit" \
  python3 tools/reconstruct_institutional_households.py --check

selftest "...and an admitted roof with no card rule, a drifted tally and an invented age are refused" \
  python3 tools/reconstruct_institutional_households.py --self-test

# T-1353, stage `transients` of the same programme, and the only stage of it that writes
# people who are NOT residents. T-1352 bounded the summer crowd of 1 July 1835 at 192 to
# 900 and adopted no point; this stage spends 384 ("twice the 1843 rate"), reserves 77 for
# the land-sale purchasers the register names, and mints the remaining 307 as visitors in
# `data/residents/transients/`, dealt equally across the six sleeping-place classes the
# sources name and do not rank. What the gate below holds: that all 307 re-derive from
# their seeds, that the classes dealt to are still the ones the committed cohort model
# prints, that no card claims a residence — the town census counts a person as housed
# through `lives_at`, and a visitor moving that figure is the one failure this cohort
# exists to prevent — that the camps name only the one documented ground, that no roofed
# party names a house whose beds T-1371 is about to deal, and that no invented name is a
# name the rest of the layer already bears. `reconstruct_residents_1835.py --check` above
# holds each drawn person to the record contract, which is the other half.
step "every transient re-derives, and none of them claims a residence" \
  python3 tools/reconstruct_transients_1835.py --check

selftest "...and a moved sleeping class, a named house and a seated visitor are refused" \
  python3 tools/reconstruct_transients_1835.py --self-test

# T-1376, the `native_and_metis` half of stage `underdocumented` (T-1177) — the ONLY stage
# of the programme licensed to write a Native or Metis person. The Illinois State Archives
# roll of Black Hawk War enrollments at Chicago prints 134 men in two companies, forty
# under G KERCHEVAL and ninety-four under a company it heads INDIAN; T-1172 was licensed to
# spend the first and not the second, and the town carried twenty of Kercheval's and none
# of the others. This stage cards them under the same licence and the same persistence
# draw. The gate holds four things the record itself cannot: that every card re-derives
# from its roster row, that every one carries review_required AND touches_removal AND says
# in its own prose which subject it is held for (AGENTS.md's Indigenous-history rule, which
# refuses a bare boolean), that every withheld row names a stated reason rather than being
# silently dropped, and that the counted-but-unnamed remainder is still REFUSED in writing
# — a later pass that quietly drew a population where no source holds a count would have to
# delete that refusal to do it.
step "every Native and Metis card re-derives, each held for review in its own words" \
  python3 tools/reconstruct_underdocumented.py --check

selftest "...and a written nation, an English initial and a shared syllable are refused" \
  python3 tools/reconstruct_underdocumented.py --self-test

# T-1377, the `free_black` sub-stage of the same stage, and the answer to the emptiest row
# T-1375 printed: of 2,626 people the layer could give a community, the ones reading
# `free_black` were NOBODY. The corpus counts the free Black town of Chicago twice and
# names it never — Caton's six or seven free coloured men before the Court of County
# Commissioners in August 1833, and the 1840 census's fifty-three free coloured persons —
# so this stage writes the FLOOR of that bracket and says on every card that it is a
# reconstruction. The gate holds what the record cannot vouch for itself: that the floor is
# parsed out of the Caton card rather than typed into the tool, that the cohort stands at
# or above it and below the ceiling the 1840 share carries back, that the name pool's
# surnames are still exactly the ones the roster's R6 `black` rows print, that no drawn
# name reproduces a printed reading OR its surname-and-initial key (which is how a draw
# would quietly back-project one of the six people those surnames come from), and that
# every card carries review_required with its own sentence. The recapitulation leaf is
# excluded by name: fifteen of its lines carry free-coloured cells and not one is a
# household, and a reader who counted them would read this town as holding five times the
# free Black households it does.
step "the free Black cohort re-derives, at or above the floor of its bracket" \
  python3 tools/reconstruct_free_black.py --check

selftest "...and a back-projected name, a drifted pool and the recapitulation leaf are refused" \
  python3 tools/reconstruct_free_black.py --self-test

# T-1504, the `church_register` sub-stage of the same stage, and the reader a refusal in
# T-1376's own report had been waiting on: "the only book it reads is the 1832 muster roll,
# and this reading is a baptismal register entry. The row is owed a stage that reads the
# register." St Mary's baptismal register is the ONE source this project holds in which a
# contemporary states an Indigenous identity for a named person at Chicago — the priest's
# parenthesis on the page — and the two women he wrote it onto were the only adults on
# their own entries the town did not carry: it held both husbands and all three children.
# The gate holds five things the record cannot vouch for itself: that both cards re-derive
# from their roster rows, that each carries review_required AND touches_removal AND says in
# its own prose which subject it is held for (AGENTS.md's Indigenous-history rule, which
# refuses a bare boolean), that NO SURNAME IS INVENTED for a woman the book gives a
# forename and a parenthesis and nothing else, that the kinship the entry states is handed
# to T-1335 by name rather than joined here, and that the four printings collapse to the
# two women the page actually holds rather than to four cards.
step "the register's two women re-derive, mononyms intact and the kinship handed on" \
  python3 tools/reconstruct_church_register.py --check

selftest "...and an invented surname, a read nation and a doubled printing are refused" \
  python3 tools/reconstruct_church_register.py --self-test

# T-1349, stage `garrison` of the same programme, and the only one that is not a share of a
# town model at all. The order book refuses to apportion the fort — "NOT APPORTIONED. The
# garrison of 1 July 1835 is a return to be read" — so this stage reads it: the Act of 2
# March 1821 § 2 for what a company of infantry consisted of, Andreas for how many companies
# stood at the post, and the Army's own General Regulations of 1835 for the recruiting window
# every age is drawn inside. It writes 125 people in 11 households and SEATS them, which the
# civilian stages cannot: the fort's roofs are in the record already and the barracks card
# carried these men in the abstract before it carried them by name.
#
# The four refusals are asserted rather than trusted, and the fourth is the one this stage
# learned the hard way: a hundred men over thirty-six surnames made the town's one real
# Tuttle ambiguous to the civic mint's resolver, which minted a person it had always refused.
# An invention that changes how a source is READ has become evidence, so a drawn soldier may
# bear no family name a named resident bears. --check rebuilds every card and the return
# beside them and refuses a differing byte on the keys this stage owns.
step "the garrison re-derives from the establishment, and the return matches the cards" \
  python3 tools/reconstruct_garrison_1835.py --check

selftest "...and the establishment, the enlistment window and all four refusals still fire" \
  python3 tools/reconstruct_garrison_1835.py --self-test
# T-1304, stage `attribute_fill_sex_age` of that programme, and the first one to draw at
# scale. 593 people carried no sex after T-1303 had read every title and forename the
# evidence licenses, and 1,218 carried no age at all. This stage draws the rest: a sex at
# the male rate MEASURED on the roll the person was named off, and an age BAND from the
# 1840 schedule's sex x age columns, each seeded by the person's own id and each carrying
# what would retire it. The gate below is what keeps that honest rather than decorative -
# the rates re-derive from the layer, every drawn block re-derives from its seed, no birth
# year is written out of a decadal band, and the six collective descriptions that name
# nobody stay refused. `--check` proves the whole draw reproduces; a hand-edited card or a
# rate nudged toward a nicer figure fails here.
step "every drawn sex and age band re-derives from its seed, and the rates from the layer" \
  python3 tools/reconstruct_sex_age.py --check

selftest "...and a draw with no seed, a band turned into a year and a sexed group are refused" \
  python3 tools/reconstruct_sex_age.py --self-test

step "the resident synthesis re-derives the population it writes" \
  python3 tools/synthesize_resident_research.py --check

# `none_recorded` was carrying two facts at once (T-0693): "no trade anywhere" and
# "no trade for 1835, and a dated one for 1839". The owner opened one card and found
# the man's trade printed three times on it while the field a reader consults said he
# had none. The pointer that separates them is DERIVED from the `directories` block on
# the same record, so it is checkable rather than asserted — and gated here, because a
# later pass that stopped writing it would otherwise put every one of those cards back
# to asserting an absence its own file contradicts.
step "no person asserts a bare 'none_recorded' while the same record dates a trade" \
  python3 tools/qualify_later_trades.py --check

# ...and the four rules that derivation rests on, held over a record built to trip
# each: only an absence is qualified, the 1835 claim never moves, and the year travels
# with the trade. Nothing here is back-projection; T-0633 is where an address is.
selftest "the later-trade pointer obeys its own four rules" \
  python3 tools/qualify_later_trades.py --self-test

# THE OTHER HALF OF T-0837's RULE, AND THE HALF ITS OWN TOOL CANNOT SEE (T-0872).
# T-0837 gated the SYNTHESIZER: a trade only enters the 1835 `occupation` field out of a
# source whose `describes_date` covers 1835. That stops the next promotion. It says
# nothing about what earlier passes already committed — and worse, its refusal is
# SUPPRESSED on exactly those cards, because the synthesizer declines to overwrite a
# filled field before it ever reaches the date test. So the population the rule forbids
# was invisible from inside the tool that owns the rule, and sat a month unmeasured: the
# eight in T-0872's table were already nine four days after it was written.
#
# This is the read side. It measures what is STANDING, and its ledger may only fall: a
# row that disappears is a repair, a row that appears is a regression this refuses.
step "no standing 1835 trade is cited only to a volume about another year" \
  python3 tools/audit_scene_window_trades.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/audit_scene_window_trades.py --self-test

# T-1229 (of T-1145). THE SINGULAR FIELD THE TWO STEPS ABOVE ARE ARGUING OVER IS NOW A
# VIEW. `persons[].roles[]` is canonical — a controlled role, the kind of role it is, the
# bound its evidence permits, how it was dated, a confidence and its sources — and
# `persons[].occupation` is derived from the roles that actually cover 1 July 1835. That
# is what lets a card say a man was a candle manufacturer in 1833 AND a school inspector
# in 1839 without either erasing the other, and it is what took T-0991's six pre-scene
# trades off the 1835 field: the audit above now stands at zero because the roles carry
# them with their dates instead. This step is the re-derivation; validate.py holds the
# shape and refuses an undated or non-covering role standing in the 1835 field, which is
# the half a generator cannot cover because a hand edit never runs it.
step "resident roles re-derive, and the 1835 view is the roles that reach it" \
  python3 tools/derive_resident_roles.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/derive_resident_roles.py --self-test

# T-1375, from T-1177. A `community` on every person, derived off what the layer already
# says — a household's origin block, or a reconstructed person's own name-pool community
# — and graded no higher than the field it was read from. The step that matters here is
# the COVERAGE one inside the tool: every distinct `origin.value` in data/residents/ must
# be accounted for exactly once in data/residents/community_rules.json, as a stated
# community, as a region, or as explicitly unreadable. A new origin string that nobody has
# decided the meaning of would otherwise fall silently to `unknown`, which is the one
# failure this pass exists to make impossible — so it makes the gate red instead.
step "every person's community re-derives, and every origin string is accounted for" \
  python3 tools/derive_person_community.py --check

selftest "…and its refusals still fire (no tier above inferred off a place, no cohort it may not write)" \
  python3 tools/derive_person_community.py --self-test

# Re-deriving is not the same as being STABLE. The allocator dealt each pool by
# index, so a name was a function of how many people sorted ahead of you and one
# new household rewrote up to 73 of the 113 invented names — a diff in which the
# parcel's real additions could not be found, and in which a name that drifted
# because something was wrong would have been invisible (ROADMAP K20). Nothing
# caught it because --check re-derives the town as it stands and never asks what
# happens when it grows. This asks: it inserts a synthetic household in memory
# and counts who gets renamed.
step "one new household renames only the people it collides with" \
  python3 tools/measure_name_churn.py --gate --probes 8 --quiet

# And the pass that RETIRES an invented name (T-0264): where the newspaper
# register found a documented person for a trade the town had invented a
# household for, the documented man takes the roof. Re-derived here because the
# deal is a derivation and not a list — six refusals shape it, and a candidate
# that quietly stopped being refused would otherwise plant a real man on a roof
# his own record contradicts. `--report` prints the deal and every refusal.
# GATED (T-1228), on what the deal still owns: WHO IS ON THE ROOF. T-0489 left the
# four men it seated unplaced and tools/synthesize_resident_research.py then took
# their households into the resident research layer, so division, name,
# research_note and the head's grade, sources and note are no longer this pass's —
# but the head's id and name are, and they are the register's own finding. The
# withdrawal is asserted, not skipped: a man who quietly becomes placed again fails.
# T-1502: the deal's name pool reads a capitalised word only under a key path
# data/reconstruction/name_pool_keys.json declares, so a pass that writes a proper
# name into a card under a NEW key goes red here, naming the key, instead of
# silently retiring a documented man; and a lost seat says which refusal took him.
step "the register's four documented men still head the roofs the deal gives them" \
  python3 tools/replace_invented_residents.py --check
selftest "…and the name pool's declared keys, and a refusal naming its source, still fire when broken" \
  python3 tools/replace_invented_residents.py --self-test

# And the pass that ADDS one (T-0376). The register's `new_resident` people are
# the ones this reconstruction does not hold at all; where it can also read a
# trade, that trade is by construction one the occupation census never invented a
# roof for, so the only thing the town can do with the man is mint him. Gated for
# the same reason as the deal above: eight refusals shape the set, and one of
# them quietly ceasing to fire would put a firm, a man at the mouth of the
# St. Joseph, or a second copy of a real resident into the town's people.
# `--report` prints the mint and every refusal with its reason.
# GATED (T-1220, which is what T-0662 left here). The command this slot used to run does
# not touch the mint; this one does. The 10 files it reported differing were read, and
# two of them were not the name splitter's doing at all — they were faults in this pass,
# and both had quietly taken a documented man out of the town:
#
#   - `register_1835.json` ADJUDICATES: two printings it resolves onto one person carry
#     the same `action_target`. The mint iterated the printings, so 'Grant, J., Jr.'
#     (militia officer, 1834) and 'James Grant' (attorney, La Salle Street, 1835) — one
#     man by the register's own ruling — competed for the one Grant household refusal 8
#     allows, and the loser was refused as a duplicate of himself. Whichever printing
#     sorted first took the card. `fold_adjudicated()` mints one household per
#     adjudicated person now; fifteen of the pool's people are read from more than one
#     printing and every one of them carries all of it.
#   - Refusal 6 read 'P. Cohen's store' as somewhere else, and retired L. W. Montgomery,
#     a shoemaker the papers print seven times on South Water Street. The rule the
#     refusal is meant to be is written in the place vocabulary (T-1048, B2): a reading
#     that names ONLY such places is not a Chicago appearance. It is a test on a reading
#     now, and a person is refused only when every one of his readings fails it.
#
# 39 minted, was 38; the other 7 files were the corpus growing under a pass nothing
# re-ran. The letter-list mint's 798 stay ungated and carry their own ticket: 648 of them
# differ in nothing but the five keys `synthesize_resident_research.py` rewrites AFTER
# this pass, so a re-derive-and-diff there is red against a correct tree.
step "the minted documented residents re-derive from the register" \
  python3 tools/mint_documented_residents.py --check

# And the pass that adds the rest of that half (T-0373): the `new_resident` people
# the papers name with NO trade at all. There is no trade to anchor them, so the
# whole pass is a residency test — the corpus must place them inside the town and
# nowhere outside it, a bare "Chicago" must be corroborated by an address, a second
# issue or the committed company they are printed beside, and the name itself must be
# printed clear of the transcription's uncertainty marks. Gated because a refusal
# that quietly stopped firing would mint 'The Blanshard household' out of the letters
# `fG. BL NSHARD`, or seat a steamboat passenger from Green Bay in the town.
# `--report` prints the 4 minted and all 382 refusals with their reasons.
step "the residency-tested residents re-derive from the register" \
  python3 tools/mint_placed_residents.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/mint_placed_residents.py --self-test

# T-1137. A resident card becomes shared state after a mint writes it: research,
# directory, census, civic, church, land and old-settler passes append findings to
# the same household and person.  The civic mint used to call its entire derived
# note the boundary, so changing one character of that prefix silently cut roughly
# 6,000 characters from Alexander Wolcott's card.  Every appending pass already
# owns a stable marker for its once-each gate; this proves all four mints use that
# marker boundary, and changes the derived prose in memory to prove the foreign
# suffix, citation, blocks, rung and later-trade pointer survive.
selftest "all four resident mints preserve findings across a derived-note change" \
  python3 tools/resident_mint_carry.py --self-test

# And the pass beside it, on the other half of `new_resident` (T-0378, T-0379). A person
# the register reads ONLY from the post office's lists of uncalled-for letters has no
# trade, so the pass above cannot reach him. It used to take only the names held in more
# than one return and leave the rest to a decision the owner had not made; he made it on
# 2026-08-30 — HOLD ALL OF THEM — and this pass now mints every name its refusals admit,
# which is most of the people in the town. Gated for the same reason and more of it: the
# refusals are the only thing between a post-office list and the town's population, and
# one of them quietly ceasing to fire would now be worth hundreds of records rather than
# one. `--report` prints the mint and every refusal with its reason; `--scale` counts
# what the ruling did to the town on whatever tree it is run against.
# GATED ON WHAT IT OWNS (T-2070, out of T-1222; T-0662 found the contract). A byte-for-
# byte `--check` was the wrong one for this pass, and was carried ungated for it: the
# mint is NOT the last writer of the files it derives. The synthesis and the ladder
# rewrite the `letter_list_only` cohort's grade and note after it — the PROJECTED
# RESIDENT downgrade — and the research passes and the T-1169 fill stage append to the
# same cards, so re-deriving byte for byte was red on ~800 files of OTHER passes' work,
# and a re-run would have reverted it (grades back up to `attested`, a confidence
# upgrade this project forbids). `--check` now compares only what the mint owns: which
# households it holds, under which ids, and the keys its KEY_OWNERS table rules its
# own; a key on no row of that table is drift, never a default. What stood on the day
# it was gated — 43 people a re-run would add, 7 it would lose, 10 it would re-mint
# under a new id, 27 cards whose returns, bounds or names moved — is written row by
# row in data/research/letter_list_mint_ledger.json, each row naming the ticket that
# reads it (T-2071, T-2072, T-2073). The ledger only shrinks: red on drift that is on
# no row, red on a row that no longer stands. `tools/letter_list_mint_drift.py` prints
# the whole difference, later passes' keys included, off the same table.
step "the letter-list mint re-derives what it owns, and only the ledgered drift differs" \
  python3 tools/mint_letter_list_residents.py --check

# T-0491. The 1840 identity bridges — three adjudicated links from a canonical 1835
# resident to a named head of household in the federal census five years later. The
# contract is that 1840 is LATER EVIDENCE: the 210 census rows are retained whole, a
# canonical link needs an explicit adjudicated person_id and is graded `validated` or
# `provisional`, and no 1840 spouse, child or boarder is minted into an 1835 household
# from a count. `--check` re-derives all of that, and it ran nowhere but its own
# workflow, so PR #670 could add a bridge, leave the manifest counts and the published
# mirror behind it, and merge on a gate that never looked. It looks here now, beside the
# synthesis it shares the ledger with.
step "the 1840 identity bridges re-derive and back-project nothing" \
  python3 tools/apply_census_1840_bridges.py --check

# T-0714, and the owner asked for it directly. The bridges gate above proves the eleven
# links this project HAS made. The crosswalk below is the adjudication those links come
# out of — every named 1840 head given an outcome against the 1835 pools — and it was the
# one crosswalk in this repo that nothing gated. `crosswalk_norris_1844`,
# `crosswalk_fergus_1843`, the three Fergus 1839 crosswalks and the death notices all fail
# the moment their committed file stops re-deriving; this one drifted 290 heads without a
# red build, because the sheets kept being read and the adjudication was never re-run.
# Gated here in the same commit that re-derived it, so it never lands red.
step "every named 1840 head still adjudicates as the pages and the pools say" \
  python3 tools/crosswalk_census_1840_heads.py --check

# THE WRITE HOP OF THE SAME CROSSWALK, and the half T-0698 was actually still owed. The
# gate above proves the adjudication re-derives; it says nothing about whether the ruling
# ever reached the person it names. Measured on dev before this pass: 27 heads ruled
# `matched` or `candidate`, and 12 of the 27 cards carried the source at all — Philo
# Carpenter, John Calhoun, Ira Couch and George W. Dole among the twelve MATCHES whose
# cards had never been told. `measure_research_spend.py` read census_1840 as fully spent
# throughout — 27 reached, 27 written — while that was true of twelve of them.
#
# WHY it read green is corrected here (T-0962), because the reason recorded above it was
# wrong and a wrong reason is worse than none: it retires the question. The hop did NOT
# fail to look at resident_crosswalk.json — `is_crosswalk()` is a substring test and that
# file has always satisfied it, and re-running 577c2f6f5's tool over 577c2f6f5's tree
# reproduces the 27 out of its `heads`, 12 matched + 15 candidate. What passed them is the
# FILE-LEVEL SOURCE FALLBACK: a head stating no discriminators of its own is judged against
# the one source id at the top of the file, and the cards already cited it from the earlier
# bridge pass. A meter that cannot see a hop reports it green; so does one that asks too
# little.
#
# T-0989 closed that fallback rather than merely holding it. A ruling stating no source of
# its own is still judged against its file's, and that still makes it JUDGEABLE — but to
# count written the card must now also NAME what the ruling adjudicated: the read unit it
# cites, or the sheet a sheet-and-line ruling sits on. The old test asked only whether the
# card cited the file's one source id, which every ruling in the file shares, so a citation
# put there by any other pass passed all of them at once. Closing it moved one figure and
# it was not tuned back: directories fell from 914 of 914 written to 659, and the 255 is in
# the write ceiling with the reason beside it.
#
# T-0670 met the same wall from the other side, hit the ceiling on ONE ruling and reverted
# rather than rule. `spend_census_1840_heads.py` is that ruling taken generally: whatever
# the crosswalk reaches, the card is told — a MATCH as a match, and a CANDIDATE in a
# paragraph that says in its own words that nothing independent of the name was found and
# that nothing is asserted from it. Two fields, no grade, and the ladder limit quoted
# rather than paraphrased.
step "…and the 1840 heads are on the 27 cards they name, once each and still true" \
  python3 tools/spend_census_1840_heads.py --check

# The third direction, and it is T-0700's lesson taken rather than relearned: it is not
# enough to ask whether a card carries a paragraph. A paragraph that is PRESENT and no
# longer says what the crosswalk says — a card still calling somebody a candidate after
# the ruling became a match — is wrong in the one way that looks exactly like being right.
selftest "…and that pass writes two fields, moves no grade and repeats without drift" \
  python3 tools/spend_census_1840_heads.py --self-test

# …and the class of fault, not just this instance of it. An ungated derivation is a
# research output that can silently stop existing, and until T-0714 nothing could answer
# "which tools can re-derive themselves and are never asked to?" without a hand audit.
# This is a RATCHET: the ungated set may shrink, and may not grow. A new tool arrives
# gated, or with a deliberate line in data/research/check_gate_baseline.json.
step "no new tool carries a --check mode the gate never runs" \
  python3 tools/audit_check_gates.py --gate --quiet

selftest "…and the audit's own assertions still fire when broken" \
  python3 tools/audit_check_gates.py --self-test

# THE OTHER HALF OF THE SAME QUESTION, and the owner asked it on 2026-09-03: "i see
# lots of research being done ... but there are not outputs or updates to the household
# and resident data". The bridges gate above proves the links the project HAS made are
# honest. It cannot notice the links it never made. On that day census_1840 held 562
# names read off the sheets and a crosswalk of `passes: [], merges: [], refusals: []` —
# every reading ticket green, every output filed, and nothing across. coverage.json
# makes an unread image fail rather than pass quietly; this makes an unruled NAME do
# the same. It is a ratchet, not a target: reading ahead of the bridge is the method,
# so the gap may sit where it sits and may not silently widen.
#
# T-0962 widened the second hop by one word. `MATCH_CONTAINERS` was written from the
# containers dev happened to hold, so the hop read `matches` and not `matched` — and
# church/second_presbyterian_crosswalk.json files its 82 adjudicated roll members under
# `matched`, every one naming a household this town holds a card for. The hop did not call
# them unwritten; it left church out of the table altogether, and a domain that is absent
# reads as a domain with nothing to answer for. With the container read, church arrives at
# 82 reached and 0 on a card — confirmed independently, no resident record in the town
# cites `second_presbyterian_chicago_1892` at all. The ceiling below records that true 82
# rather than hiding it; T-0992 pays it down.
step "research stays inside its historical ratchet and closed unit ledger" \
  python3 tools/measure_research_spend.py --check --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_research_spend.py --self-test

selftest "…and closed-ledger mutations cannot pass silently" \
  python3 tools/measure_research_spend.py --ledger-self-test

# T-1241. The ledger above is the SOURCE side of the research: every reading unit gets one
# durable disposition and an unclassified one fails. It is silent on the town side, and the
# two are not the same book — a ledger at zero unclassified is perfectly compatible with
# firms that name no keeper and roofs that hold nobody. The closing audit reads the same
# ledger onto the resident, household, business and structure layers, reads those layers
# directly, and prints the gaps it finds with the ticket that carries each one. It is
# checked rather than merely written because a report nobody re-derives is a report that
# quietly stops being true, and this one is the evidence section T-1157 signs over.
step "the closing research audit still re-derives from the ledger and the four layers" \
  python3 tools/report_research_closing_audit.py --check --quiet

selftest "…and a moved measurement cannot pass as an unchanged report" \
  python3 tools/report_research_closing_audit.py --self-test

# T-1157. And the signature over the two books above. The owner asked, on 2026-09-17, to
# confirm that the research had been SPENT — on residents, households, trades and offices,
# on the businesses and who works in them, and on where everyone lived, worked and was
# otherwise significantly involved. The sign-off answers that on five axes and reduces it
# to ten CONDITIONS, each a measurement over committed files, and derives a GO or a NO-GO
# for the reconstruction bands from them. It is gated for the reason the report states
# about itself: a sign-off that cannot be revoked is not a measurement. If a condition
# breaks after the signature is given, this step goes red and the next run has to
# re-derive the verdict rather than inherit it.
check_summary
