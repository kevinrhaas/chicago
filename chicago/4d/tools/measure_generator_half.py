#!/usr/bin/env python3
"""What a generator half for a renderer-drawn layer would cost, measured.

    tools/measure_generator_half.py            print the three readings
    tools/measure_generator_half.py --gate     exit 1 if a stated figure has moved

WHY THIS EXISTS. Ticket T-0059 asked for *"a river-wharf mode of `pier_crib`"*, so
that a town assembled from GLBs alone would carry its docks. `docs/ROADMAP.md` K5
makes the same request of three other clauses in almost the same words — *"the
generator half, so a baked town carries its own yards"*. Before building one, three
things wanted a number rather than an opinion:

  1. **How many committed meshes does adding it re-stale?** `generators/
     mesh_inputs.py` hashes an archetype's builder, `generators/emit.py` and
     the geometry-making half of `generators/common/` into every structure asset's
     `inputs_sha256`, and `generators/terrain_inputs.py` hashes `terrain_gen.py`
     and the same modules into every terrain asset's. Which half that is, is
     declared in `generators/code_inputs.py` (T-0164) rather than globbed. `tools/validate.py --stale` fails on
     any asset whose recomputed hash has moved. So the cost of adding a mode is not
     the mode: it is the rebake of everything the edited file's bytes reach. This
     measures that reach per candidate edit site.

  2. **Is a wharf the only layer that owes one?** The wharf is one of the data
     layers drawn at load out of committed JSON rather than loaded as a GLB. If the
     debt is general, paying it one layer at a time — by a route that re-stales the
     town each time — is the wrong shape of work, and the ticket is a fragment of a
     decision nobody has made rather than a unit anybody can ship.

  3. **Who would read the GLBs the mode would produce?** The ticket's motivation is
     *"a scene assembled from GLBs alone has no docks in it"*. That sentence has a
     consumer in it, and whether the consumer exists is checkable: it is the count
     of renderers under `renderers/`. A cost paid for a reader that does not exist
     is a different decision from one paid for a reader that does.

All three are printed. `--gate` holds them against the figures written into this
file's own `STATED` block, which is what makes them a measurement rather than a
number somebody remembers: the two are meant to be edited together, and a reading
that moves without the sentence beside it moving is the drift.

The drawn-layer denominator is derived from the tree — every `data/*/index.json` —
AND held against a named list. Deriving alone would silently absorb the next layer
somebody adds; naming alone would silently miss it. Held against each other, a new
layer fails this gate and gets read by a person, which is the only outcome worth
having.

THE DECISION, 2026-10-03 (T-0252). The three readings above were taken to put one
question in front of the owner, and it has been answered: `docs/GLB-CONTRACT.md` §
"Layers drawn at load" decides that the baked town carries NONE of these layers, and that
their portable form is an export made by the renderer module that draws them. So the
reading is kept as the gate, and two of its figures changed meaning without changing value:

  * `layers_with_a_generator: 0` is no longer a debt being counted. It is the rule. A
    layer that grows an archetype turns this red, and the fix is to change the contract
    first, not the number.
  * every layer this file names must have a row in the contract's layer table (between its
    `T-0252 layer export table` markers). A new layer therefore cannot arrive without
    somebody saying how it leaves the repository, which is how the nine-at-once question
    started.

NO BLENDER, NO NETWORK. It reads `assets/manifest.json`, the generator modules' own
hashing recipes and the committed layer manifests, all of which are in the tree —
the same standing this tool's neighbours in `tools/measure_*.py` have.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "generators"
DATA = ROOT / "data"
MANIFEST = ROOT / "assets" / "manifest.json"
RENDERERS = ROOT / "renderers"
RENDERER_JS = RENDERERS / "web" / "js"
CONTRACT = ROOT / "docs" / "GLB-CONTRACT.md"
TABLE_OPEN = "<!-- T-0252 layer export table"
TABLE_CLOSE = "<!-- end T-0252 layer export table -->"

# The reading this file was written against, re-taken on 2026-08-27 on `dev`
# @ a638614c (T-0059). `--gate` holds the live measurement to it. Moving a figure
# here is a claim that the reach changed, and it belongs in the same commit as
# whatever changed it.
#
# The two zero rows are T-0164's, added 2026-08-28. `common/phases.py` decides
# whether a mesh is built at all and builds none, and while it was globbed into
# both recipes one comment line in it re-staled 349 of 349. It is out of the hash
# now, `generators/code_inputs.py` says why, and a zero here is what keeps it out:
# put it back and this row reads 349.
#
# 349 -> 350 and 347 -> 348 on 2026-08-28: T-0254 added one structure to the town,
# north_water_slough_crossing. One more committed asset, one more mesh that a change to
# the shared generator modules or to build.py would re-stale; the terrain and pier_crib
# reaches are untouched because the crossing is neither.
#
# 350 -> 353 and 348 -> 351 on 2026-08-28 (T-0028): `blk_lake_franklin` was opened and
# carries three roofs. This is the ordinary movement of the reading, not a change in
# reach — a structure asset is in `build.py`'s reach by construction — and the terrain
# and pier_crib reaches stay at 2 each, which is the point of stating them separately.
#
# 353 -> 354 and 351 -> 352 on 2026-08-28 (T-0096): `fort_dearborn_flagstaff__staff_1833_37.glb`,
# the garrison flagstaff Andreas attests. One new fort_structure record, so one more committed
# asset and one more mesh a change to the shared generator modules or to build.py would re-stale.
#
# 354 -> 358 and 352 -> 356 on 2026-08-29 (T-0317): `blk_randolph_market` took its second
# deal — a party-line run of three on the block's free corner lot and the stable in its yard.
# Four new structure assets, so four more meshes a change to the shared generator modules or
# to build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
#
# 358 -> 359 and 356 -> 357 on 2026-08-29 (T-0380): `new_york_house__frame_1834.glb`, the
# frame hotel on Lake Street near Wells this project had wrongly excluded. One new
# frame_tavern record, so one more committed asset and one more mesh a change to the shared
# generator modules or to build.py would re-stale; terrain and pier_crib stay at 2 each.
#
# 359 -> 360 and 357 -> 358 on 2026-08-30 (T-0384): `john_holbrook_store__frame_1835.glb`,
# the clothing store two papers place one door from Dearborn on South Water Street. One new
# frame_storefront record, so one more committed asset and one more mesh a change to the
# shared generator modules or to build.py would re-stale; terrain and pier_crib stay at 2.
#
# 359 -> 367 and 357 -> 365 on 2026-08-30 (T-0429): `blk_south_water_lasalle` took its second
# deal — a party-line run of six along the west half of the block's South Water frontage and the
# two yard buildings on the lots it stands on. Eight new structure assets, so eight more meshes a
# change to the shared generator modules or to build.py would re-stale; the terrain and pier_crib
# reaches stay at 2 each.
#
# 368 -> 372 and 366 -> 370 on 2026-09-03 (T-0430): `blk_south_water_franklin` took its
# second deal — a party-line run of three on the block's one free lot of South Water
# frontage and the privy in the yard behind them. Four new structure assets, so four more
# meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each.
#
# 372 -> 374 and 370 -> 372 on 2026-09-05 (T-0431): `blk_south_water_clark` took its second
# deal — one C2 store-residence on the block's one free lot of South Water frontage, party-
# walled to Pruyne & Kimball's drug store, and the privy in the yard behind it. Two new
# structure assets, so two more meshes a change to the shared generator modules or to
# build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
#
# 375 -> 378 and 373 -> 376 on 2026-09-06 (T-0883): the Big Barn with Cupola, the Wash house
# and the Shop — three of the six things the 1830 Harrison plan names on Fort Dearborn's outer
# ground and nothing drew. Three new `outbuilding` records, so three more committed assets and
# three more meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each.
#
# 378 -> 380 and 376 -> 378 on 2026-09-06 (T-0881): the fort's Out Buildings, which the same
# plate letters in the PLURAL and draws as TWO blocks rather than the one every earlier reading
# of the sheet took them for. Two new `outbuilding` records, so two more committed assets and
# two more meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each. The Well is the sixth thing on that plate and
# adds nothing here: it is measured to a coordinate and deliberately not built, because this
# project has no well archetype (docs/RESEARCH/wells.md section 5, T-0887).
#
# 380 -> 383 and 378 -> 381 on 2026-09-11 (T-0432): the second deal on
# `blk_south_water_dearborn`, the last of the four South Water blocks T-0420 held in one
# ticket — two frame cottages on the South Water frontage of lot 2, one party-walled to each
# side wall of Frederick Thomas's shop, and the stable in the yard behind them. Three new
# structure assets, so three more meshes a change to the shared generator modules or to
# build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
#
# 383 -> 384 and 381 -> 382 on 2026-09-11 (T-1036): `fort_dearborn_us_factors_house`, the
# United States factory on the fort reservation — block A of the three the 1830 Harrison plate
# letters `U.S. Factor's House`, built as a `log_dwelling` where T-0894 read all three and
# built none. One new structure asset, so one more mesh a change to the shared generator
# modules or to build.py would re-stale; the terrain and pier_crib reaches stay at 2 each.
# Blocks B and C are drawn, unlettered and refused, and add nothing here: measured and
# deliberately not built.
#
# 9 -> 10 drawn-at-load layers on 2026-09-11 (T-0887): `data/wells/`, read by
# renderers/web/js/wells.js. The fort's well was the Well this block used to name as measured
# and not built — the plate letters it, Hubbard corroborates it and T-0881 measured it to a
# coordinate, and it stayed invisible because data/structures.schema.json has no well among its
# twelve archetypes and a structure record with no buildable form does not validate. The curb is
# derived at load from committed numbers, so THE ASSET COUNT DOES NOT MOVE and nothing re-stales:
# this layer, like the other nine, owes a generator half and has none.
#
# 384 -> 414 and 382 -> 412 on 2026-09-20 (T-1444): the West Division parcel's terrain hold
# is retired and thirty of its thirty-five held slots are built — `recon_1835_west_004`,
# `_013`, `_017`, `_020` and `_025`..`_055` less the five the corporate boundary's
# extrapolated west leg cannot decide (T-1490). Thirty new structure assets, so thirty more
# meshes a change to the shared generator modules or to build.py would re-stale; the terrain
# and pier_crib reaches stay at 2 each. The five held slots add nothing here for the same
# reason blocks B and C above add nothing: measured, dealt, and deliberately not built.
#
# 414 -> 417 and 412 -> 415 on 2026-09-24 (T-1490): Jefferson Street is carried north on its
# own surviving control and the corporate boundary's west leg walks it instead of being
# extrapolated 1,188.8 m across the West Division, so three of those five — `recon_1835_west_029`,
# `_032` and `_035` — are decided by the ordinance and are built. Three new structure assets.
# The remaining two are still not built and still add nothing: they stand inside the platted
# Jefferson corridor, which is a different refusal and is stated in the parcel's own recipe.
#
# 417 -> 419 and 415 -> 417 on 2026-09-25 (T-1545): the last two — `recon_1835_west_027` and
# `_037` — are re-dealt off that Jefferson corridor by the same frozen-setback table thirteen
# other slots of the parcel already stand on, 12.25 m and 10.00 m east, and are built. Two new
# structure assets, so two more meshes a change to the shared generator modules or to build.py
# would re-stale; the terrain and pier_crib reaches stay at 2 each. Nothing is held back in this
# parcel now, so this line is the last one it will move for a release.
#
# 419 -> 421 and 417 -> 419 on 2026-09-26 (T-1622): the third deal on
# blk_south_water_franklin raises the D4 two-room cottage and the D3 one-room cottage the
# platted seating asked that block for by name — `recon_1835_blk_south_water_franklin_d4_12`
# and `_d3_13` — on lot 4, its last free business-front lot. Two new structure assets, so two
# more meshes a change to the shared generator modules or to build.py would re-stale; the
# terrain and pier_crib reaches stay at 2 each. This is the first release on this row that a
# HOUSEHOLD asked for rather than the schedule's district remainder, and the reach moves for
# the same reason it always does: two more committed meshes, nothing about the debt itself.
#
# 421 -> 422 and 419 -> 420 on 2026-09-26 (T-1636): `south_bank_shed_dearborn_e1`, the
# south-bank half of the plate T-0133 built the north bank of, on ground T-1629's fill of the
# old slough mouth opened. One new structure asset, so one more mesh a change to the shared
# generator modules or to build.py would re-stale; the terrain and pier_crib reaches stay at 2
# each. It is the first roof this row has taken for a REFUSAL being re-read rather than for a
# slot being dealt: T-0134 refused this bank on a measurement, and the measurement moved.
#
# 422 -> 423 and 420 -> 421 on 2026-09-27 (T-1640): `south_bank_shed_dearborn_e2`, the second
# shed of that same row, on e1's own two wall lines with a wagon yard between them. One new
# structure asset, so one more mesh the shared generator modules would re-stale; the terrain
# and pier_crib reaches stay at 2 each. Nothing about the debt itself moved.
#
# 423 -> 434 and 421 -> 432 on 2026-09-28: THREE changes landed together, and this
# reading is the merged one. T-1712 built `beaubien_new_residence` and
# `beaubien_trading_post`, the two buildings Andreas records at the Beaubien homestead on
# the Fort Dearborn reservation that this project had not built; T-1709 built the six works
# buildings the four documented noxious trades imply - the packing house, salt house and
# stock shed of the South Branch plant, the bark and drying sheds of Miller and Hall's
# tanyard, and Elston's ash house; T-1714 built `mckee_log_house`,
# `caldwell_agency_log_house` and `agency_striker_log_house`, the ring of agency log
# buildings Wau-Bun and Andreas group round Cobweb Castle at the foot of State Street.
# Eleven new structure assets between them, so eleven more meshes a change to the shared
# generator modules or to build.py would re-stale; the terrain and pier_crib reaches stay at
# 2 each. Nothing about the debt itself moved.
# 434 -> 435 and 432 -> 433 on 2026-09-28 (T-1715): `fort_dearborn_root_house_b`, the
# second of the root-houses Kinzie puts on the river bank west of the fort. One new
# structure asset, so one more mesh the shared generator modules or emit.py would
# re-stale; the terrain and pier_crib reaches stay at 2 each. Nothing about the debt
# itself moved.
#
# 435 -> 436 and 433 -> 434 on 2026-09-28 (T-1716): `chicago_lighthouse_keepers_quarters`,
# the quarters the Chicago light's keepership was paid 'with quarters' for, raised beside the
# 1832 tower on the reservation. One more structure asset, so one more mesh a change to the
# shared generator modules or to build.py would re-stale; the terrain and pier_crib reaches
# stay at 2 each. Nothing about the debt itself moved.
# 436 -> 438 and 434 -> 436 on 2026-09-28 (T-1717): `kimberly_residence` and
# `kelsey_boarding_house`, the two houses Bonnell's walk of an August morning in 1835
# puts east of the Lake House building site on the north bank. Two new structure assets,
# so two more meshes a change to the shared generator modules or to emit.py would
# re-stale; the terrain and pier_crib reaches stay at 2 each. Nothing about the debt
# itself moved.
#
# 436 -> 438, and the terrain reach 2 -> 4, on 2026-09-28 (T-1738): the 1904 ground and
# water, `terrain__e1871_postfire.glb` and `water__e1871_postfire.glb`, baked by
# generators/terrain_gen_graded.py, which reuses terrain_gen.py's mesher and so is re-staled
# by it. Two more committed assets the shared generator modules reach; emit.py and pier_crib
# are untouched, and nothing about the debt itself moved.
#
# 438 -> 440 on 2026-09-28 (T-1738, merged in): the 1904 scene's terrain and water
# meshes, baked out of the e1871_postfire heightfield. Two more committed assets, and
# both of them the ground's, so `generators/terrain_gen.py` was already at 4 and
# `generators/emit.py` does not move. Nothing about the debt itself moved.
#
# 440 -> 444 and 436 -> 440 on 2026-09-28 (T-1736): the four roofs of the first deal on
# `blk_washington_clark`, the plat's last tier — two frame cottages and the privy and
# woodshed in their yards. Four new structure assets, so four more meshes the shared
# generator modules or emit.py would re-stale; the terrain reach stays at 4 and pier_crib
# at 2. Nothing about the debt itself moved.
#
# 444 -> 448 and 440 -> 444 on 2026-09-29 (T-1742): the four roofs of the first deal on
# `blk_indiana_north_wolcott`, Kinzie's Addition — two one-room frame cottages and the
# woodshed and privy off the alley behind them. Four new structure assets on the same
# terms as the four above: four more meshes the shared generator modules or emit.py
# would re-stale, the terrain reach still 4 and pier_crib still 2. Nothing about the
# debt itself moved.
#
# 448 -> 449 and 444 -> 445 on 2026-09-29 (T-1732): `glessner_house__as_built_1887.glb`,
# the Glessner House at 1800 Prairie, the first 1904 structure and the first record of the
# new `masonry_house` archetype. One new structure asset, so one more mesh the shared
# generator modules or emit.py would re-stale; the terrain reach stays at 4 and pier_crib
# at 2. Nothing about the debt itself moved.
#
# 449 -> 460 and 445 -> 456 on 2026-09-29 (T-1708): the eleven roofs of the deal on
# `blk_washington_wells`, the plat's last tier again — seven principal roofs (two D7
# houses, two H1 houses, two D3 cottages and an H2) with two privies, a woodshed and a
# stable behind them. Eleven new structure assets, so eleven more meshes the shared
# generator modules or emit.py would re-stale; the terrain reach stays at 4 and
# pier_crib at 2. Nothing about the debt itself moved.
#
# 460 -> 464 and 456 -> 460 on 2026-09-29 (T-1756): the four roofs of the SECOND deal on
# `blk_indiana_north_wolcott` — two more one-room frame cottages on lots 4 and 5 with a
# woodshed and a privy off the alley behind them, which completes the alternation the
# north-division memo describes on both faces of that block. Four new structure assets on
# the same terms as every entry above: four more meshes the shared generator modules or
# emit.py would re-stale, the terrain reach still 4 and pier_crib still 2. Nothing about
# the debt itself moved.
#
# 464 -> 475 and 460 -> 471 on 2026-09-29 (T-1735): the eleven roofs of the deal on
# `blk_washington_lasalle`, the south-west block of the same last tier, raised on top of the
# Wells eleven and the Wolcott four above. Seven principal dwellings (an H2, two H1, two D7
# and two D3) with a stable, two privies and a woodshed behind them. Eleven new structure
# assets, so eleven more meshes a change to the shared generator modules or to emit.py would
# re-stale; the terrain reach stays at 4 and pier_crib at 2. Nothing about the debt itself
# moved. The from-numbers are the ones this branch found on `dev` at its NINTH lap, and the
# three numbers are read off the committed tree by `--gate` rather than carried over.
#
# 475 -> 479 and 471 -> 475 on 2026-09-29 (T-1753): the four roofs of the first deal on
# `blk_indiana_north_cass`, the next cell east in Kinzie's Addition — two one-room frame
# cottages and the privy and woodshed off the alley behind them. Four new structure
# assets on the same terms as every entry above: four more meshes the shared generator
# modules or emit.py would re-stale, the terrain reach still 4 and pier_crib still 2.
# Nothing about the debt itself moved. The from-numbers are the ones this branch found
# on `dev` at its TENTH lap, not the 449/445 it was written off: the debt is cumulative,
# so T-1708's eleven, T-1756's four, the Glessner versions and T-1735's eleven are all
# counted first and these four go on top of them.
# 479 -> 492 and 475 -> 488 on 2026-09-29 (T-1751): the thirteen roofs of the deal on
# `blk_washington_franklin`, the plat's last tier dealt out to its lot ceiling — seven
# dwellings and the six yard buildings behind them. Thirteen new structure assets on the
# same terms as every entry above: thirteen more meshes the shared generator modules or
# emit.py would re-stale, the terrain reach still 4 and pier_crib still 2. Nothing about
# the debt itself moved. The from-numbers are the ones this branch found on `dev` at its
# FOURTH lap, not the 475/471 it was written off: the debt is cumulative, so T-1753's four
# are counted first and these thirteen go on top of them. IT IS ALSO THE LARGEST SINGLE
# MOVE THIS ROW HAS TAKEN, which is the measurement working as intended rather than a
# surprise — the debt is per-ASSET, so a block dealt out to its ceiling enlarges it by a
# whole block.
# THIS ROW HAS NOW MOVED SIX TIMES IN TWO DAYS — five block deals and the Glessner
# House — which is the measurement working as intended and also the shape of what it
# measures: the debt is per-ASSET, so every roof this project raises enlarges it, and it
# will keep being restated a parcel at a time for as long as the town is built a block
# at a time.
#
# 492 -> 496 and 488 -> 492 on 2026-09-29 (T-1757): the four roofs of the SECOND deal on
# `blk_indiana_north_cass` — two two-room frame cottages four lots west of the first pair,
# with a woodshed and the Addition's first stable off the alley behind them. Four new
# structure assets on the same terms as every entry above: four more meshes the shared
# generator modules or emit.py would re-stale, the terrain reach still 4 and pier_crib still
# 2. Nothing about the debt itself moved. The from-numbers were 479 -> 483 when this branch
# was written; T-1751's thirteen landed on `dev` first, so its 492/488 are the base these
# four go on top of. SEVENTH move in two days, and the note above already said why: the
# debt is per-ASSET.
#
# 496 -> 499 and 492 -> 495 on 2026-09-30 (T-1760): the three roofs of the first deal on
# `blk_lake_clinton` — a two-room cottage on Canal Street, a one-room cottage on Clinton
# Street, and a stable off the alley behind the Canal house. Three new structure assets
# mean three more meshes a shared generator or emit.py change would re-stale; the terrain
# reach stays at 4 and pier_crib at 2. Nothing about the debt itself moved.
#
# 499 -> 500 and 495 -> 496 on 2026-10-01 (T-1773): one roof, the West Division's second
# freight roof — an F2 warehouse at Lake and West Water. One more mesh the shared generator
# modules or emit.py would re-stale, on the same terms as every entry above.
#
# 500 -> 504 and 496 -> 500 on 2026-10-01 (T-1761): the four roofs of the SECOND deal on
# `blk_randolph_clinton` — a two-storey frame house and a two-room cottage on the Canal
# face, with a privy and a woodshed off the alley behind them. Four new structure assets on
# the same terms as every entry above, on top of T-1760's three and T-1773's one; terrain reach still 4 and
# pier_crib still 2.
#
# 504 -> 506 and 500 -> 502 on 2026-10-01 (T-1785): the doctor's house and barn in
# Wabansia, two named records rather than recipe roofs, and two more meshes the same
# shared-generator or emit.py change would re-stale. Nothing about the debt itself moved.
#
# 506 -> 512 and 502 -> 508 on 2026-10-01 (T-1776): six stables behind six of the town's
# public houses (the Tremont, the Exchange, the New York House, the Mansion House, the
# Sauganash and the Steamboat Hotel). Six new structure assets on the same terms as every
# entry above; terrain reach still 4 and pier_crib still 2.
#
# 512 -> 516 and 508 -> 512 on 2026-10-01 (T-1783): the four roofs on
# `blk_west_randolph_des_plaines`, the first deal on the West Division's outer platted
# blocks — three frame cottages and a carpenter's shop. Four new structure assets on the
# same terms; the terrain reach still 4 and pier_crib still 2.
#
# 516 -> 517 and 512 -> 513 on 2026-10-01 (T-1778): one roof, the town's first H3
# boarding house on `blk_washington_clark` — one more mesh on the same terms as every
# entry above; terrain reach still 4 and pier_crib still 2.
#
# 517 -> 519 and 513 -> 515 on 2026-10-01 (T-1803): the two emigrants' camps on the
# South Water bank, the first records of the new `camp` archetype. Registering it in
# emit.py's ARCHETYPES re-staled every structure asset once, and the whole town was
# rebaked in the same PR (the GLB bytes came back identical; only the manifests' input
# hashes moved). Terrain reach still 4 and pier_crib still 2.
#
# 519 -> 523 and 515 -> 519 on 2026-10-01 (T-1766): the Canal approach trade roofs — two
# stores and two workshops on the Canal Street approach (built as five; the W3 shop was
# withdrawn for the West workshops row). Four new structure assets on the same terms as
# every entry above; terrain reach still 4 and pier_crib still 2.
#
# 523 -> 528 and 519 -> 524 on 2026-10-01 (T-1809): the second H3 boarding house on
# `blk_washington_clark` and a stable and a privy behind each of the two — five more
# meshes on the same terms; terrain reach still 4 and pier_crib still 2.
#
# 528 -> 531 and 524 -> 527 on 2026-10-02 (T-1952): the North Division's H3 boarding house
# on `blk_indiana_north_cass` and a stable and a privy behind it — three more meshes on
# the same terms; terrain reach still 4 and pier_crib still 2.
#
# 531 -> 534 and 527 -> 530 on 2026-10-02 (T-1950, of T-1810): the third H3 boarding house on
# `blk_washington_clark`, on the Washington-and-Clark corner, and its stable and privy —
# three more meshes on the same terms; terrain reach still 4 and pier_crib still 2.
#
# 534 -> 543 and 530 -> 539 on 2026-10-02 (T-1951, of T-1810): the South's last three planned
# H3 boarding houses, two on `blk_washington_market` and one on `blk_washington_dearborn`,
# each with its stable and privy — nine more meshes on the same terms; terrain reach still 4
# and pier_crib still 2.
#
# 543 -> 545 and 539 -> 541 on 2026-10-02 (T-1804): the two camps on conjectural ground,
# the land-sale crowd's on the reservation shore and a wagon party's at the west
# approach — two more `camp` meshes on the same terms; terrain reach still 4 and
# pier_crib still 2.
#
# 545 -> 544 and 541 -> 540 on 2026-10-03 (T-2012): `south_bank_shed_dearborn_e1` is
# withdrawn, because South Water Street now runs on to State Street through where it stood.
# One structure asset fewer, so one mesh fewer the shared generator modules or emit.py would
# re-stale; terrain reach still 4 and pier_crib still 2.
#
# 544 -> 550 and 540 -> 546 on 2026-10-03 (T-1205): six trade roofs on the north face of
# Kinzie Street from the North Division recipe, the same `generate_north_infill` meshes as
# its sixty; terrain reach still 4 and pier_crib still 2.
# 550 -> 549 and 546 -> 545 on 2026-10-03 (T-1743): `beaubien_new_residence` is withdrawn
# and folded into `jb_beaubien_homestead` on the owner's ruling that Col. Beaubien's group
# shows one dwelling. One structure asset fewer; terrain reach still 4 and pier_crib still 2.
# 552 -> 551 with T-2003's two meshes below, merged.
#
# 550 -> 552 on 2026-10-03 (T-2003): the 1812 ground and water meshes,
# `terrain__e1830_natural.glb` and `water__e1830_natural.glb`. Both are built through
# terrain_gen.py's mesher and the common modules, so terrain reach goes 4 -> 6 and the
# common reach with it; emit.py builds no terrain, so 546 stands, and pier_crib still 2.
#
# 551 -> 565 and 545 -> 559 on 2026-10-04 (T-2050): the first Fort Dearborn's fourteen
# meshes, baked for the first time once the 1812 scene resolved them — eleven
# `fort_structure`, two `palisade`, one `outbuilding`, all through emit.py and the common
# modules. Terrain reach still 6 and pier_crib still 2.
#
# 565 -> 568 and 559 -> 562 on 2026-10-05 (T-1829): blk_west_lake_canal's three
# dwellings, a D5 and a D4 frame cottage and a D2 shanty, all through emit.py and the
# common modules. Terrain reach still 6 and pier_crib still 2.
#
# 568 -> 578 and 562 -> 572 on 2026-10-05 (T-2129): blk_washington_market's five
# dwellings (an H1, two D4s, a D7 and a D3) and their five yard buildings, all through
# emit.py and the common modules. Terrain reach still 6 and pier_crib still 2.
#
# 578 -> 587 and 572 -> 581 on 2026-10-05 (T-2130): the nine roofs the platted deal
# requests on blk_washington_dearborn and blk_washington_clark, all through emit.py and the
# common modules. Terrain reach still 6 and pier_crib still 2.
#
# 587 -> 613 and 581 -> 607 on 2026-10-05 (T-1746): the North Division's 26 ordinary
# dwellings carried off Kinzie's Addition into the clusters south of Michigan Street
# (generate_north_infill rows 68-93), all through emit.py and the common modules.
# Terrain reach still 6 and pier_crib still 2.
#
STATED = {
    "assets": 613,
    "restales": {
        "generators/common/*.py": 613,
        "generators/common/__init__.py": 0,
        "generators/common/phases.py": 0,
        "generators/emit.py": 607,
        "generators/build.py": 0,
        "generators/terrain_gen.py": 6,
        "generators/archetypes/pier_crib.py": 2,
    },
    "layers_drawn_at_load": 10,
    # T-0252 (2026-10-03): this zero is the decision in docs/GLB-CONTRACT.md § "Layers
    # drawn at load", not a count of debt. None is baked; each is exported by the module
    # that draws it. Raise it only after the contract says so.
    "layers_with_a_generator": 0,
    # T-1464 (2026-09-20): the owner-requested standalone Unreal adapter now
    # consumes the committed GLBs. The missing-layer debt has a second reader;
    # T-0252/T-1360 own the export/parity work, not a reopened wharf-only ticket.
    "renderers": 2,
}

# The data layers a renderer draws at load out of committed JSON, rather than
# loading a baked GLB for. Each is a directory under `data/` carrying its own
# `index.json` manifest — a static host cannot be globbed, which is why every one
# of them has one — plus the renderer module that consumes it.
DRAWN_AT_LOAD = {
    "boats": "boats.js",
    "enclosures": "enclosures.js",
    "fauna": "fauna.js",
    "flora": "flora.js",
    "frontage": "frontage.js",
    "residents": "residents.js",
    "signage": "signage.js",
    "wells": "wells.js",
    "wharves": "wharves.js",
    "yard": "yard.js",
}

# AND THE LAYERS THAT CARRY AN INDEX AND ARE NOT DRAWN AT ALL (T-1310). The test above
# reads `data/*/index.json` and was right that a manifest means a layer; it was not
# right that a layer means the renderer draws it. A directory under `data/` needs an
# index for the reason every one of them does — a static host cannot be globbed — and
# that says nothing about whether anything on screen consumes it. `data/businesses/` is
# the first of these: 196 compiled records of who traded where, read by the research
# tools and by tools/validate.py, and drawn by nothing. It owes no generator half
# because there is no geometry it could generate.
#
# This is a third class and not a loophole: a layer must still be NAMED in one of the
# two tables before the gate goes green, so a renderer-drawn layer that arrives without
# a module still fails here. What changed is that "not drawn" became a thing a layer is
# allowed to be, with its reason written next to it, which is what the refusal's own
# sentence asked for.
NOT_DRAWN_AT_LOAD = {
    "businesses": "compiled business records (T-1310); read by the research tools and "
                  "tools/validate.py, drawn by no renderer module and baked into no asset",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def restale_reach() -> tuple[dict, int, list]:
    """Per candidate edit site, how many committed assets its bytes are hashed into.

    The reach is not read off the files — it is read off the two hashing recipes,
    which is the only reading that cannot go stale behind them:

      * `mesh_inputs._code_shas(archetype)` names what a STRUCTURE asset's hash
        covers: `emit.py`, that archetype's builder, and `common/*.py`.
      * `terrain_inputs._code_shas()` names what a TERRAIN asset's covers:
        `terrain_gen.py` and `common/*.py`.

    So a site's reach is the count of assets whose recipe names it.
    """
    problems: list[str] = []
    if not MANIFEST.exists():
        return {}, 0, ["assets/manifest.json is missing, so no reach can be measured"]
    sys.path.insert(0, str(GEN))
    try:
        import code_inputs                      # noqa: PLC0415
        import mesh_inputs                      # noqa: PLC0415
        import terrain_inputs                   # noqa: PLC0415
    except Exception as e:                      # noqa: BLE001
        return {}, 0, [f"cannot import the generators' hashing recipes: {e}"]

    assets = load(MANIFEST).get("assets", {})
    reach: dict[str, int] = {}
    for entry in assets.values():
        if entry.get("structure_id"):
            arch = entry.get("archetype")
            if not arch:
                problems.append("a structure asset in the manifest names no archetype")
                continue
            try:
                names = mesh_inputs._code_shas(arch)      # noqa: SLF001
            except Exception as e:                        # noqa: BLE001
                problems.append(f"archetype {arch}: {e}")
                continue
        elif entry.get("terrain_epoch"):
            names = terrain_inputs._code_shas()           # noqa: SLF001
        else:
            continue
        for rel in names:
            key = "generators/common/*.py" if rel.startswith("common/") \
                else f"generators/{rel}"
            reach[key] = reach.get(key, 0) + 1
    # `common/*.py` is counted once per FILE above; collapse it to once per asset.
    # The divisor is the RECIPE's own module list and not the directory listing,
    # because since T-0164 the two differ: dividing 349 assets x 3 hashed modules
    # by the 5 files in the folder reads 209, a reach nothing has.
    commons = len(code_inputs.geometry_modules()) or 1
    if "generators/common/*.py" in reach:
        reach["generators/common/*.py"] //= commons
    # The modules T-0164 took OUT of the recipe are reported at their reach, which
    # is zero, rather than omitted. That is the standing gate on the property the
    # ticket bought: drop an exclusion and this row goes straight back to 349, and
    # `--gate` says so with the sentence beside it instead of a rebake nobody
    # ordered turning up in the next bake's diff.
    for name in code_inputs.excluded():
        reach[f"generators/common/{name}"] = 0
    # And `build.py`, which T-1654 took out of the structure recipe exactly as T-0164
    # took `common/phases.py` out of it — the pipeline moved to `generators/emit.py`
    # and the command line stayed behind. Reported at its reach, which is 0, for the
    # reason directly above: a row reading zero is the standing gate on that split.
    # Write a builder call back into the CLI and this row returns to 420 here, in a
    # diff somebody is reading, instead of arriving as a full-town rebake nobody
    # ordered. `tools/test_build_cli_has_no_geometry.py` refuses the edit outright;
    # this is the figure that would move if the refusal were ever removed.
    reach.setdefault("generators/build.py", 0)
    return reach, len(assets), problems


def layer_debt() -> tuple[list, list]:
    """Per drawn-at-load layer: is there anything under `generators/` that builds it?

    The test is deliberately blunt, because the answer is: an archetype module named
    for the layer, or a manifest asset whose archetype is. A layer with neither is
    drawn by the renderer and by nothing else, which is what "owes a generator half"
    means.
    """
    problems: list[str] = []
    assets = load(MANIFEST).get("assets", {}) if MANIFEST.exists() else {}
    baked = {e.get("archetype") for e in assets.values() if e.get("archetype")}

    # Derived and named, held against each other. See the module docstring.
    found = {p.parent.name for p in sorted(DATA.glob("*/index.json"))}
    named = set(DRAWN_AT_LOAD) | set(NOT_DRAWN_AT_LOAD)
    for extra in sorted(found - named):
        problems.append(f"data/{extra}/index.json is a manifested layer this file "
                        f"does not name; it is a drawn layer — in which case the reading "
                        f"below is out of date — or it is baked, or nothing draws it at "
                        f"all, and this file has to say which")
    for gone in sorted(named - found):
        problems.append(f"data/{gone}/index.json is named here and is not in the "
                        f"tree, so this reading counts a layer that no longer exists")

    rows = []
    for layer, module in sorted(DRAWN_AT_LOAD.items()):
        index = DATA / layer / "index.json"
        js = RENDERER_JS / module
        if not js.exists():
            problems.append(f"{layer}: renderers/web/js/{module} is missing, so "
                            f"nothing draws it and this reading is out of date")
        arch = GEN / "archetypes" / f"{layer}.py"
        records = 0
        if index.exists():
            doc = load(index)
            # The manifests do not agree on a key — `wharves`, `zones`,
            # `households`, and `flora` carries three lists at once — so the count
            # is not "the first list": it is every entry in the document that names
            # a record FILE, which is the one thing every one of these manifests agrees on
            # and the only thing this column is claiming.
            records = sum(1 for v in doc.values() if isinstance(v, list)
                          for e in v if isinstance(e, dict) and e.get("file"))
        rows.append({
            "layer": layer,
            "module": module,
            "records": records,
            "generator": arch.exists() or layer in baked,
        })
    return rows, problems


def contract_rows() -> tuple[list, list]:
    """The rows of the contract's layer table, as lists of cells (T-0252)."""
    if not CONTRACT.exists():
        return [], [f"{CONTRACT.relative_to(ROOT)} is missing, so no layer's export is decided"]
    text = CONTRACT.read_text(encoding="utf-8")
    start, end = text.find(TABLE_OPEN), text.find(TABLE_CLOSE)
    if start < 0 or end < start:
        return [], [f"{CONTRACT.relative_to(ROOT)} has no T-0252 layer export table "
                    f"between its markers, so no layer's export is decided"]
    rows = []
    for line in text[start:end].splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and cells and cells[0].startswith("`data/"):
            rows.append(cells)
    return rows, []


def contract_coverage() -> list:
    """Every layer this file names has a row in the contract's table, naming its module."""
    rows, problems = contract_rows()
    if problems:
        return problems
    for layer in sorted(set(DRAWN_AT_LOAD) | set(NOT_DRAWN_AT_LOAD)):
        mine = [r for r in rows if r[0].startswith(f"`data/{layer}/`")]
        if not mine:
            problems.append(f"data/{layer}/ has no row in docs/GLB-CONTRACT.md's layer "
                            f"export table: say how it leaves the repository (T-0252)")
            continue
        module = DRAWN_AT_LOAD.get(layer)
        if module and not any(module in r[0] for r in mine):
            problems.append(f"data/{layer}/'s row in docs/GLB-CONTRACT.md does not name "
                            f"{module}, the module that draws it")
    return problems


def renderers() -> list:
    """The things that could read a GLB. One directory under `renderers/` each."""
    return sorted(p.name for p in RENDERERS.iterdir()
                  if p.is_dir() and not p.name.startswith("."))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if a measured figure has moved off the stated one")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    reach, total, problems = restale_reach()
    rows, more = layer_debt()
    problems += more
    problems += contract_coverage()
    rend = renderers()
    drawn = len(rows)
    owed = sum(1 for r in rows if not r["generator"])

    if not args.quiet:
        print(f"COMMITTED, INPUT-TRACKED ASSETS: {total}\n")
        print(f"{'edit site':<42} {'re-stales':>9}   what a rebake would have to reach")
        for site, n in sorted(reach.items(), key=lambda kv: -kv[1]):
            share = ("nothing — outside both recipes (T-0164)" if n == 0
                     else "every committed mesh" if n >= total
                     else "every structure in the town" if n >= total - 2
                     else "the ground" if site.endswith("terrain_gen.py")
                     else "the meshes of that archetype alone")
            print(f"{site:<42} {n:>9}   {share}")
        print(f"\nLAYERS DRAWN AT LOAD FROM COMMITTED JSON: {drawn}, "
              f"{drawn - owed} with a generator, {owed} without — and none is owed one: "
              f"docs/GLB-CONTRACT.md (T-0252) exports them instead\n")
        print(f"{'layer':<12} {'renderer module':<18} {'record files':>13}  "
              f"generator")
        for r in rows:
            print(f"{r['layer']:<12} {r['module']:<18} {r['records']:>13}  "
                  f"{'yes' if r['generator'] else 'NONE'}")
        print(f"\nRENDERERS THAT COULD READ A GLB: {len(rend)} — {', '.join(rend)}")

    for key, want in STATED["restales"].items():
        got = reach.get(key)
        if got != want:
            problems.append(f"{key} re-stales {got} asset(s); this file states {want}")
    if total != STATED["assets"]:
        problems.append(f"{total} committed asset(s); this file states {STATED['assets']}")
    if drawn != STATED["layers_drawn_at_load"]:
        problems.append(f"{drawn} layer(s) drawn at load; this file states "
                        f"{STATED['layers_drawn_at_load']}")
    if drawn - owed != STATED["layers_with_a_generator"]:
        problems.append(f"{drawn - owed} drawn layer(s) have a generator; this file "
                        f"states {STATED['layers_with_a_generator']}, which is the rule in "
                        f"docs/GLB-CONTRACT.md § Layers drawn at load (T-0252): change "
                        f"the contract before the number")
    if len(rend) != STATED["renderers"]:
        problems.append(f"{len(rend)} renderer(s) under renderers/; this file states "
                        f"{STATED['renderers']}. A second one is exactly the reader "
                        f"T-0059 was withdrawn for not having — re-read that ticket")

    for p in problems:
        print(f"FAIL  {p}", file=sys.stderr)
    if problems:
        return 1
    if args.gate:
        print(f"generator half: none of {drawn} drawn layers is baked, as "
              f"docs/GLB-CONTRACT.md decides (T-0252), and each has a row there; "
              f"{len(rend)} renderers; the cheapest route into the bake re-stales "
              f"{min(reach.values()) if reach else 0} committed mesh(es), the shared "
              f"ones {max(reach.values()) if reach else 0}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
