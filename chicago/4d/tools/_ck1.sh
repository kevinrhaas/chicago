#!/usr/bin/env bash
set -uo pipefail
_check_tools="$(cd "$(dirname "$0")" && pwd)"
cd "$_check_tools/.."

STRICT=""
[ "${1:-}" = "--strict" ] && STRICT="--strict"

# The step harness — `step`, `selftest` and the end-of-run roll-up — lives in its own
# file so that tools/test_check_harness.sh can source and exercise it (T-0763).
source "$_check_tools/check_harness.sh"
# T-1548. Before anything else: are this clone's merge drivers registered? They live
# in .git/config, so they cannot be committed and a fresh clone starts without them.
# Unregistered they cost a hand-resolved changelog conflict per branch — four of them
# in one session on 2026-09-24 — and nothing anywhere says so. This says so.
step "the merge drivers this clone needs are registered (T-1548)" \
  bash tools/check-merge-drivers.sh

step "the tickets are here (kevinrhaas/chicago-tickets, cloned at tickets/)" \
  bash tools/tickets.sh
check_flush   # the publish below reads the clone; never race it under CHECK_JOBS>1

step "publish the mirror the gate measures (site/4d/ is generated, T-0938)" \
  bash tools/publish.sh

# THE ONE ORDERING THIS GATE HAS, and under CHECK_JOBS>1 it has to be said out loud.
# Everything below reads the mirror the step above writes, so the pool may not start
# any of it until that publish has finished. `check_flush` is the barrier: it drains
# what is queued and returns, and it is a no-op on the serial path.
check_flush

step "Glessner v4 packaged GLBs match both generated outputs (T-1730)" \
  python3 tools/recover_glessner_v4.py --check
selftest "…materialization refuses corruption and never overwrites a new bake" \
  python3 tools/test_glessner_v4_package.py --self-test
selftest "…only the canonical v4 derivative producer refreshes the package" \
  python3 tools/test_glessner_v4_package_producer.py --self-test
selftest "…arched apertures preserve whole-stone relief without false joints" \
  python3 tools/test_glessner_block_clipping.py --self-test
selftest "Scene bundle: one commit packed reproducibly; tampered, missing, extra, forged refused (T-2067)" \
  python3 tools/scene_bundle.py --self-test
step "Glessner's west roof has one continuous envelope and a lower rear eave (T-1830)" \
  python3 tools/test_glessner_roof_envelope.py
step "Glessner copper follows the low hood and both adjoining roof planes (T-2220)" \
  python3 tools/test_glessner_copper.py
step "Glessner rainwater reaches its collectors and grade without crossing openings (T-2221)" \
  python3 tools/test_glessner_rainwater.py
step "Glessner court surfaces are disjoint and approaches meet their thresholds (T-2224)" \
  python3 tools/test_glessner_courtyard_ground.py
step "Glessner plain brick and member grain preserve geometry and contacts (T-2226)" \
  python3 tools/test_glessner_finish.py
step "Glessner original plain-brick surface maps reproduce (T-2226)" \
  python3 tools/generate_glessner_finish.py --check
step "Glessner vines attach to masonry, clear openings and share their Light layout (T-2225)" \
  python3 tools/test_glessner_vines.py
step "Glessner foliage atlas rederives from its declared planting (T-2225)" \
  python3 tools/generate_glessner_vines.py --check
step "Glessner service posts seat on stone and gate hinges connect to masonry (T-2223)" \
  python3 tools/test_glessner_service_access.py
step "Glessner stacks meet both roof pitches and retain deep open flues (T-2222)" \
  python3 tools/test_glessner_chimneys.py
step "Glessner's curved stone staggers, its eave clears the gable and its pipe meets the roof (T-2470)" \
  python3 tools/test_glessner_north_tower.py
step "Glessner's service openings stay whole and the stable roof meets the north range (T-2219)" \
  python3 tools/test_glessner_service_junction.py
step "Glessner carriage leaves: relief, swing and grain" \
  python3 tools/test_glessner_porte.py
step "Glessner courtyard treads, landing and rounded terminal stay solid" \
  python3 tools/test_glessner_terrace.py
step "Glessner entry retains its cutback, single threshold and recessed carving" \
  python3 tools/test_glessner_entry.py
step "Prairie 1904 K01 component contract holds, and the Glessner baseline is the package it measured (T-2265)" \
  node tools/k01_contract.mjs --check
selftest "…coincident faces, hidden origin offsets and tier scale drift are caught on synthetic GLBs" \
  node tools/k01_contract.mjs --self-test
step "every Glessner tier's stone occlusion was baked from its committed atlas, so a bake on any CPU reproduces it (T-2431)" \
  python3 tools/check_stone_occlusion_atlas.py --check
selftest "…a model rebaked without its atlas, an atlas holding another key and an orphan atlas are refused" \
  python3 tools/check_stone_occlusion_atlas.py --self-test
step "Glessner's canonical UV caches are complete and reject stale or corrupt layouts (T-2494)" \
  python3 tools/test_stone_occlusion_uv.py
step "the K01 assemblies are the bytes their records build (T-2266)" \
  python3 generators/k01_emit.py --check
step "the K13 conservatories in the scene are the bytes their records build (T-2306)" \
  python3 generators/k13_emit.py --check
step "the K16 timber fronts in the scene are the bytes their records build (T-2323)" \
  python3 generators/k16_emit.py --check
step "the K12 coach houses in the scene are the bytes their records build (T-2321)" \
  python3 generators/k12_emit.py --check
step "the Prairie district draft's records are what its rules build from the traced sheets (T-2329)" \
  python3 tools/draft_prairie_1904.py --check
selftest "…and the draft builder still fits rectangles inside a part, reads the notation and refuses a hand edit" \
  python3 tools/draft_prairie_1904.py --self-test
step "the Prairie district draft's houses are the bytes their records build (T-2329)" \
  python3 generators/draft_emit.py --check
step "the haystacks are the bytes their records build (T-2510)" \
  python3 generators/haystack_emit.py --check

# T-0763. The gate's own OUTPUT is a gate. 114 of the steps below prove a derivation by
# breaking it and require its assertions to fire, so a green run prints dozens of lines
# that read exactly like a broken gate — and three tickets (T-0745, and the misreports in
# T-0522/T-0612/T-0683) were filed against those lines rather than against a fault. The
# harness answers that with `selftest`, which tags every line of such a transcript, and
# with the roll-up `check_summary` prints at the end. This holds both to it, and scans
# check.sh for a self-test that has drifted back onto plain `step`, where it would print
# untagged again.
# T-1083. WHAT THIS RUN CAN ACTUALLY ASK, declared before it asks anything.
#
# Thirteen steps below re-read a committed raster, and each degrades politely to a
# banked reading when the image and array libraries are absent — prints its skip and
# exits 0. Right for a tool; wrong for a gate, which then counts the skip as a pass.
# The dev gate installed jsonschema/pyproj/openpyxl/pypdf and had therefore never
# re-read a sheet, which is how `sauganash_range_m` sat 65.1 m out against a 1.0 m
# tolerance and green. CI now installs the readers and sets
# C4D_GATE_REQUIRE_READERS=1, which makes their absence RED here rather than silent.
# A sandbox without them gets the same enumeration as a warning and carries on.
step "the gate can ask what it claims to ask (raster readers present)" \
  python3 tools/check_gate_readers.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/check_gate_readers.py --self-test

step "the gate's own output tells a fired assertion from a failure" \
  bash tools/test_check_harness.sh

selftest "…and its own assertions still fire when broken" \
  bash tools/test_check_harness.sh --self-test

selftest "…and the post-deploy URL smoke still fires on a 404 (T-0968)" \
  node ../../.github/chicago-4d-url-check.mjs --self-test

selftest "…and the bounded clone abandons a bad draw and re-rolls (T-0232)" \
  bash ../../.github/chicago-4d-clone.sh --self-test

step "the steward surfaces spend the REST bucket, not GraphQL (T-0234)" \
  node tools/check_gh_rest.mjs

selftest "…and a reintroduced gh pr draw is refused (T-0234)" \
  node tools/check_gh_rest.mjs --self-test

# T-1652. `tools/bake.sh` documents `--only a,b,c` and passes its arguments straight
# through, so its usage is a promise about generators/build.py — which compared the id
# for EQUALITY, matched none of 422 records, printed `0 asset(s) built` and exited 1.
# The documented way to bake several buildings in one Blender start-up therefore baked
# nothing, and said nothing about why; a re-family lap on 2026-09-26 paid for ten
# separate start-ups instead. This is the gate beside the fix, in the shape
# check_haze_reach.mjs uses: read both texts and refuse them drifting apart again.
step "the --only form bake.sh documents is the form build.py implements (T-1652)" \
  python3 tools/check_only_selection.py --gate

selftest "…and the equality comparison and the falsy-empty test are both refused (T-1652)" \
  python3 tools/check_only_selection.py --self-test

selftest "…and the selection rule itself still fires on each of its assertions (T-1652)" \
  python3 generators/common/selection.py --self-test

# T-0135. The three scene-detail ceilings are a LADDER and nothing made them one.
# `sealLadder()` in main.js takes the running minimum down the tier order, so a rung
# typed too high cannot take effect; this is the gate beside that construction. It
# is here and not only in the renderer smoke because the dev gate is check.sh and
# nothing else (docs/PIPELINE.md) — a fault only a six-minute smoke part can see is
# a fault that reaches the dev preview. It reads the committed source, sliced.
step "the scene-detail ceilings are a ladder, and each rung says what it protects (T-0135)" \
  node tools/check_detail_ladder.mjs

selftest "…and the seal still clamps, marks and shouts a rung typed too high (T-0135)" \
  node tools/check_detail_ladder.mjs --self-test

# The other renderer constant that a DATA change can silently invalidate. L17's apron
# is re-derived from the terrain box by generators/terrain_gen.py, so extending the box
# moves the distance the haze has to close over — and the haze is a literal in two
# renderer files. This holds the one against the other, both ways. See T-1635.
step "the haze closes before L17's ground apron ends, and both its literals agree (T-1635)" \
  node tools/check_haze_reach.mjs

selftest "…and it refuses a thinned air, a shrunk apron and the two literals drifting apart (T-1635)" \
  node tools/check_haze_reach.mjs --self-test

step "dataset (schema, provenance, date gates, licenses, staleness, publish)" \
  python3 tools/validate.py --all $STRICT

# The validator's own suite re-validates the committed dataset as one of its tests;
# the step above already did, and more strictly, so the suite is told so (T-2117).
step "validator self-tests" \
  env CHECK_VALIDATE_ALL_IS_A_STEP=1 python3 tools/test_validate.py

# T-1727. STRUCTURE VERSIONS — `?structure=<id>&version=<label>` swaps one building for a
# committed alternate so competing builds can be compared side by side. validate.py above
# already holds every version to the structure rules and its mesh to --stale; these prove
# those reds actually fire (no mesh, a stale mesh, a model identifier as a label…), that
# the address bar falls back to the default out loud on every miss, and that the
# one-command promotion moves records, meshes and books together. docs/STRUCTURE-VERSIONS.md.
selftest "structure versions: no mesh, a stale mesh and a refused label are each red (T-1727)" \
  python3 tools/test_structure_versions.py --self-test

selftest "…the address bar swaps one committed version and falls back ALOUD on every miss (T-1727)" \
  node tools/test_structure_versions.mjs --self-test

step "Buildings share an image they carry identically: one decode, closed by its last holder (T-2464)" \
  node tools/test_shared_images.mjs

selftest "…and promote_version.mjs makes a version the default in one diff, reversibly (T-1727)" \
  node tools/promote_version.mjs --self-test

step "reconciled PRs preserve resident identities and refuse back-projected trades" \
  python3 tools/test_pr_reconciliation.py

# A book's page numbers are its locators, and for Hubbard's autobiography they are DERIVED:
# the committed text is the Internet Archive's djvu OCR, which carries no page breaks at all,
# so the leaf boundaries are carried onto it from the deposited scan. A derivation that is not
# gated drifts, and this one is cheap — it reads committed files only and needs no poppler.
step "book page indexes still match the text they index" \
  python3 tools/build_book_page_index.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/build_book_page_index.py --self-test

# T-1397. WHICH BYTES THE TRACES ARE MADE OF, held to a pin.
#
# The half-gate below compares the committed GeoJSON to the constants its generator
# writes. It cannot see the other half of the question: WHAT THE GENERATOR READ. That
# was an unpinned network fetch — `fetch_region` took whatever the cache held or the
# server returned, hashed it, and wrote the hash into provenance without checking it
# against anything. On 2026-09-19 the library re-encoded one region of the Wright
# sheet (263,865 bytes of JPEG became 231,112) and the lap, which runs
# `rederive.mjs --run` on every merge with numpy installed, re-traced the Chicago
# River from the new bytes and committed it onto two unrelated branches. #1518 and
# #1521 each failed the same four terrain gates over a ticket neither was about.
#
# Offline on purpose, like tools/refetch_control.py: it holds the register to the
# shas the committed readings record in their own PROVENANCE, and holds every
# manifest step that can reach the network either to fetching through
# tools/pinned_sources.py or to an enumerated offline command. Asking the server
# what it serves today needs the network and is `--verify-upstream`, by hand.
step "the traces' remote sources are pinned, and the readings record those pins" \
  python3 tools/pinned_sources.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/pinned_sources.py --self-test

# The river and the slough at the forks declare themselves "Generated by
# tools/trace_river.py — do not hand-edit", and until T-0687 nothing held them to
# it: the real reproduction (`--check`) re-traces a BPL scan and needs numpy,
# scipy, Pillow and the network, so it cannot be a per-commit gate and is not one.
# `hydrology.geojson` drifted from the generator on two PROVENANCE GRADES and sat
# that way for a month. This is the offline half — every literal those files
# carry, compared against the constants the generator writes them from, in
# milliseconds. Coordinates still need the deliberate `--check` re-run.
step "the traced forks still carry what their generator writes" \
  python3 tools/trace_river.py --check-properties

# The same half-gate for the South Branch south of the forks window (T-1071).
step "the traced South Branch still carries what its generator writes" \
  python3 tools/trace_south_branch.py --check-properties

# ...and for the South Branch BELOW TWELFTH STREET, which is the only trace in
# the corpus not taken from Wright (T-1150). It has the same offline half and one
# assertion the others cannot make: that both banks still meet the Wright window
# at the declared splice row and still cross the box floor, because the banks are
# a perpendicular offset and a re-trace moves both ends.
step "the South Branch below Twelfth still carries what its generator writes" \
  python3 tools/trace_south_branch_rees_1849.py --check-properties

# ...and the pre-fill lake shore beside it, off the same sheet (T-1151). This
# one's literals are a run's two ENDS and its two disagreements: it has to meet
# the Wright shore run on the declared row N -2159.9 and CROSS the box floor,
# because a run that stops on the floor leaves the floor row with no lake edge
# and 355 m of Lake Michigan comes out as dry prairie; and the seam step and the
# overlap offset have to stay negative and stay the size of the documented
# erosion, because a re-trace that lost the erosion signal would be reading
# something other than this shore.
step "the pre-fill lake shore below Twelfth still carries what its generator writes" \
  python3 tools/trace_lake_shore_rees_1849.py --check-properties

# T-1152. A late observation can bound an earlier shore; it cannot quietly
# become that shore, and a pair of fitted lines that disagree stays a polygonal
# band rather than an invented midpoint. The same contract keeps the planned
# 1880s state from aliasing the active 1835 terrain while its own scene ticket
# fills it — and, since T-1242, holds the 1812 state to the same rule from the
# other side: it HAS a line now, so the check is that the line is its own, that
# it re-derives from its readings, and that no drafted pier vertex rode in on it.
step "dated shorelines stay separate and source disagreement stays a band" \
  python3 tools/check_shoreline_states.py

selftest "…and shoreline-state assertions still fire when collapsed" \
  python3 tools/check_shoreline_states.py --self-test

# The 1812 shore is DERIVED, not traced — no survey of the pre-cut mouth exists —
# so the file has to fall out of data/terrain/1812_mouth_readings.json and the
# Wright 1834 trace byte for byte. The step above re-derives it semantically; this
# one catches the whitespace-and-ordering drift a semantic compare forgives.
step "the 1812 pre-cut shore still re-derives from its readings (T-1242)" \
  python3 tools/derive_shore_1812.py --check

# T-1286. The one pre-cut sheet held, Harrison 1830, read as a second line and
# measured against the derived one. Wright carries the state by the owner's ruling;
# this keeps the measurement of how far the only pre-cut reading disagrees with it
# true to the lines it was taken from, and the sentence the 1812 file's
# evidence_limit quotes from it true to the measurement.
step "the Harrison 1830 cross-check still measures what the 1812 shore quotes (T-1286)" \
  python3 tools/measure_shore_1812_harrison.py --check

# T-0470. The 15 August 1812 route and battle zone are DERIVED, not drawn: the
# readings (Heald's mile and a half, the Eighteenth Street tradition, the ridge
# line) laid along the 1812 shore the step above checks. The zone spans the
# readings' disagreement and claims no point; this holds the file to its readings
# byte for byte, and refuses it if the shore moves out from under the stations.
step "the 1812 evacuation route and battle zone re-derive from their readings (T-0470)" \
  python3 tools/derive_evacuation_1812.py --check

# T-2501. The South Branch below the box floor, down to the forks and the canal at
# Bridgeport, off the same Rees 1849 sheet: a MEASURING line, not yet a layer of any
# epoch. Its offline half holds the committed file to the trace's own literals and
# to the Bridgeport pick, the same way the reach above it is held.
step "the South Branch to Bridgeport still carries what its tracer writes (T-2501)" \
  python3 tools/trace_south_branch_bridgeport_rees_1849.py --check-properties

# T-2501. Lee's Place (Hardscrabble) is PLACED, not pinned: five printed placings
# measured along the river above, the adopted station and its reach of the
# north-west bank derived from them, and each disagreement printed. This holds the
# site file to its readings byte for byte, and refuses it if the river moves.
step "the 1812 Hardscrabble site re-derives from its readings (T-2501)" \
  python3 tools/derive_hardscrabble_1812.py --check

# T-2502. ...and the 1812 ground carried down to it: an apron field beside the box (the box
# itself is untouched), its land the floor row carried, its channel and banks T-2501's
# trace at the 1834 cross-section, every sample conjectural. Held byte for byte, and its
# rules (the north row IS the floor row, the side columns the carried land, the site's
# bank at or above the water) asserted. measure_anchors.mjs --gate holds the anchor on it.
step "the 1812 South Branch apron re-derives from the box floor and T-2501's trace (T-2502)" \
  python3 tools/derive_apron_south_branch_1812.py --check
selftest "…and its seams still hold when the apron is re-derived (T-2502)" \
  python3 tools/derive_apron_south_branch_1812.py --self-test

# T-2048. The first fort's one plan, Whistler's draught of 25 January 1808, read into a
# register the first fort will be built from (T-2049). The raster is not committed, so
# this holds what can be held without it: the scale is the 75 ft staff's arithmetic,
# every foot in the file is what its pixel box gives, and all 34 of the drafter's index
# numbers are accounted for. `--remeasure` re-finds the staff on the fetched sheet.
step "the Whistler 1808 reading of the first fort still adds up (T-2048)" \
  python3 tools/read_whistler_1808.py --check

# T-1249. A scene date is a claim about WHEN this reconstruction stands, and until
# now the 1880s one was the only claim in the terrain layer that nothing derived and
# nothing checked: the step above carried a bare `date(1885, 7, 1)` that T-1152 wrote
# in as scaffolding. It read like a settled figure. It is three and a half years
# before the Glessner House was finished, so the Prairie Avenue the 1880s epoch
# exists to carry could not have stood on it. The date is now the arithmetic of the
# committed readings — the latest documented lower bound, carried to the 1835 scene's
# own day-of-year, held inside the decade the parent ticket asked for — and the epoch,
# the shoreline state and check_shoreline_states.py all read the one file.
step "the 1880s scene date re-derives from its readings, and nothing has drifted off it" \
  python3 tools/check_1880s_scene_date.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/check_1880s_scene_date.py --self-test

# T-1250. The Prairie Avenue sheets -- Sanborn 1911 vol. 3 sheets 20, 28 and 35 and
# Robinson 1886 plate 10 -- georeferenced once, for every ticket that reads a line
# off them (the lake edge here; the streets, T-0474; the Glessner House, T-1729).
# The four GCP files in data/traces/gcp/ are generated from picks written in the
# tool and the modern control in data/traces/prairie_1904_control.json, and the
# rasters' sha256 are checked before any pick is trusted. The fit is a similarity
# at each sheet's PRINTED scale, and the tool's docstring says why the free affine
# is fitted and printed and not adopted; its contract fails if the street bands
# stop agreeing with the bar, or if the Glessner sheet's three standing houses stop
# landing within 5 m of their OpenStreetMap outlines.
step "the five Prairie Avenue sheets still re-derive their georeference (T-1250, T-3150)" \
  python3 tools/georef_prairie_1904.py --check

selftest "…and a moved control, a misread bar or a mislaid house still fails it" \
  python3 tools/georef_prairie_1904.py --self-test

# ...and the lake edge read off three of them. Both sheets are the wrong date for
# 1904, so both are bounds; the scene line between them is reconstructed (L287).
# --check re-reads the sheets, which needs Pillow and numpy
# (tools/check_gate_readers.py); without them it holds the committed file together
# and says it did not re-read.
step "the 1904 Illinois Central lake edge still re-traces from its sheets (T-1250)" \
  python3 tools/trace_ic_edge_1904.py --check

# T-0474. ...and the street grid read off the same three Sanborn sheets through that
# georeference: carriageways, every block face's margin / walk / parkway / curb, the
# alleys, and the lots on both faces of Prairie from 16th to 22nd, each with its 1911
# address. data/street_grid/1904.json is generated from picks written in the tool;
# its contract holds the Glessner lot's frontage inside what sheet 28 allows (T-1731
# left 74 or 77 ft for this ticket), refuses an address label that falls on no lot,
# and holds every band of the street section to the 1905 code's sidewalk space.
step "the 1904 Prairie Avenue street and parcel grid re-derives from its sheets (T-0474)" \
  python3 tools/trace_prairie_1904_grid.py --check

selftest "…and a misread lot line, a stray label or a broken section still fails it" \
  python3 tools/trace_prairie_1904_grid.py --self-test

# T-2474. ...the street section and the carriage walks laid on that grid's lots and faces,
# generated the same way; and (T-2473) the parkway elms planted on its parkway bands, clear
# of those carriage walks: the committed files are what the tools write, walk for walk and
# tree for tree.
step "the 1904 street section and carriage walks re-lay from the street grid (T-2474)" \
  python3 tools/lay_prairie_1904_street_section.py --check

step "the 1904 parkway elms re-plant from the street grid (T-2473)" \
  python3 tools/plant_prairie_1904_street_trees.py --check

# T-1840. ...and what stands on that grid's sheet 20 lots in 1904: the sheet census
# (prairie_1904_v1/data/sheet_census/sheet-20.json) assigns every 1911 frontage row and
# every named record on the sheet's ground exactly once, owns every traced parcel, keeps
# the printed number the library and the trace carry in step, and never lets a 1911 GARAGE
# stand for 1904 without a note (the study's ruling 11).
step "the 1904 sheet census assigns every Prairie frontage and named record once (T-1840)" \
  python3 ../prairie_1904_v1/tools/sheet_census.py --check

selftest "…and a dropped row, a doubled record or a kept misreading still fails it" \
  python3 ../prairie_1904_v1/tools/sheet_census.py --self-test

# T-2327. ...and the ground each of those sheet 28 buildings stands on. The census names every
# building and says of itself "Footprints are not digitized"; this reads them off the same
# raster through the same fit, as outlines on the drawn walls (colour-classed fabric, joined
# across its own lines, split into parts at solid walls) and gives every census polygon its
# outline, data/traces/prairie_1904_footprints_s28.json. The contract holds every outline
# inside its lot, counter-clockwise, assigned once and to a polygon the census names.
# T-2328 adds sheet 20 (16th-18th, the T-1840 census, for T-2160) as one more SHEETS entry:
# data/traces/prairie_1904_footprints_s20.json, the same reading, the same contract.
# T-2340 adds sheet 35 (20th-22nd, the T-1842 census, for T-2161), read off a coarser copy
# with the pixel rules scaled to it: data/traces/prairie_1904_footprints_s35.json.
step "sheets 28, 20 and 35's 1904 building footprints re-derive from the raster and cover every census polygon (T-2327, T-2328, T-2340)" \
  python3 tools/trace_prairie_1904_footprints.py --check

selftest "…and a broken trace, a clockwise or out-of-lot outline, an unnamed or twice-named building still fails it" \
  python3 tools/trace_prairie_1904_footprints.py --self-test

# T-3008: the visibility census of the background behind Prairie Avenue — which Indiana,
# Calumet, end-street and unlotted ground the avenue's walks see past the traced fabric —
# re-derives from the street grid, the sheet censuses and the traces it reads.
step "the background behind Prairie Avenue: what its walks see re-derives (T-3008)" \
  python3 tools/census_prairie_1904_background.py --check
selftest "…and its sight-line and storey-height rules hold (T-3008)" \
  python3 tools/census_prairie_1904_background.py --self-test

step "the 1904 outer lakefront joins every through track, keeps rails dry and reproduces its mapped apron (T-2495)" \
  python3 tools/extend_ic_lakefront_1904.py --check

step "the outer 1904 apron GLB and runtime heights agree at both joins (T-2495)" \
  node tools/check_coast_extension.mjs

# T-2477. ...and the faded context city around them: every building those three sheets draw off
# Prairie Avenue as a sheet-coloured rectangle, and a projected city past the sheets' edges, with
# trees (data/context/1904.json). The contract keeps every stand-in off Prairie Avenue's lots and
# roadway and out of the water, and every sheet it reads a resolving source. T-2491 carried it to
# the haze's reach with faded streets, which the contract keeps off every traced carriageway and lot.
step "the 1904 context city and its streets re-derive and keep off Prairie Avenue and the lake (T-2477, T-2491)" \
  python3 tools/build_context_1904.py --check

selftest "…and a stand-in put on a Prairie Avenue lot or in the lake, or a street across Prairie, still fails it" \
  python3 tools/build_context_1904.py --self-test

# T-2741. Today's streets under every year: the City of Chicago's centrelines clipped to the
# scenes' ground (data/modern/streets.json), each with its block's address ranges, so the compass
# says the street and house number you stand at today. The check holds the clip's shape, its
# source record, and three corners this project already holds OSM control for.
step "today's streets clip holds its shape and lands on the OSM control corners (T-2741)" \
  python3 tools/build_modern_streets.py --check

step "today's street and house number read off the City's block ranges, both sides' parity (T-2741)" \
  node tools/test_modern_streets.mjs

# T-1728. ...and what that grid is paved with. data/street_surfaces/1904.json is AUTHORED:
# every carriageway, alley and sidewalk band names a material, a tier, its sources and a
# range that bounds 1 July 1904. The contract holds it to the grid (nothing drawn without
# a surface, nothing surfaced that is not drawn), to data/sources/ (rule 1), to
# LIBERTIES.md (a reconstruction names its liberty), to the texture library the renderer
# binds, and refuses an ATTESTED block that rests only on the 1904 paving report or the
# 1905 code, which bound what a block could have been and never say what one was.
step "the 1904 street surfaces cover the grid, cite real sources and bound the scene date (T-1728)" \
  python3 tools/check_street_surfaces.py --check

selftest "…and a bare surface, an invented source, a report made to attest or a range that misses still fails it" \
  python3 tools/check_street_surfaces.py --self-test

# T-2296. ...and the relief those surfaces are lit with points the right way. The library's
# generator wrote green as -dh/drow, the DirectX sign, into every `normal_gl` map, and
# street-grid.js binds `normal_gl_web.jpg` into three.js, which reads OpenGL (+V up the
# image): every pothole, rut and joint was lit as a bump across the street. This
# correlates each map's red and green with its own height16's slopes, so a flipped
# channel is red whatever its strength.
step "the 1904 street normals are OpenGL-handed, as the renderer binds them (T-2296)" \
  python3 tools/check_street_surfaces.py --handedness

# T-2478. ...and the railway between those streets and the lake: the Illinois Central
# tracks sheets 20 and 28 draw, traced in a frame along the scene's waterline, joined
# across the sheets' gap and closed on their neighbours where no sheet draws them, each
# stretch recording how it was got. --check re-reads both sheets (Pillow and numpy,
# tools/check_gate_readers.py) and holds data/railway/1904.json to what a re-trace
# writes; without them it holds the committed file's properties together.
step "the 1904 Illinois Central tracks still re-trace from sheets 20 and 28 (T-2478)" \
  python3 tools/trace_ic_tracks_1904.py --check

# T-2292. ...and what the 1904 roofs are covered in. The K04 library's slates, tiles, pans
# and sheets are sized in data/components/prairie_1904/k04_roofs.json and drawn by the
# generator in assets/textures/prairie_1904_roofs/; a K01 roof maps TEXCOORD_0 = metres /
# tile_m, so a tile that is not a whole number of its own slates scales every slate on
# every roof that wears it. This holds the maps to the data, the double-lap rule, the
# reconstruction rules' slate range, a seamless wrap, and tile to the roofs a source shows.
step "the K04 roof library registers to its data, wraps seamlessly and cites what it rests on (T-2292)" \
  python3 tools/check_roof_library.py --check

selftest "…and a scaled tile, a broken lap, an odd bond, an oversized slate or a tile built from a barred source still fails it" \
  python3 tools/check_roof_library.py --self-test

# T-2297. ...and what the 1904 windows are. The K06 kit's parts are sized in
# data/components/prairie_1904/k06_windows.json and built by
# generators/archetypes/k06_windows.py. This rebuilds every variant and measures the
# geometry: each stage of the window strictly deeper than the last, every hole edge
# closed by a reveal, a dark room behind every pane, glass the only transparency and one
# layer of it per line of sight, no doubled face, even muntins, true arches, the
# triangle budget, and the specimen GLB the generator's bytes.
step "the K06 window kit builds every window as a closed recess over an enclosed room, one glass layer deep (T-2297)" \
  python3 tools/check_window_kit.py --check

selftest "…and a blind before the glass, a missing jamb, a holed backing, a doubled pane or a leaded street sash still fails it" \
  python3 tools/check_window_kit.py --self-test

# T-2301. ...and how the 1904 roofs are built. The K05 kit's parts are sized in
# data/components/prairie_1904/k05_roofs.json and built by generators/archetypes/k05_roofs.py
# as closed solids joined by a boolean union. This rebuilds every variant and measures the
# built surface: watertight, one shell, no doubled face, no face through another (no
# plane across a gable, parapet or cheek), parapets clear of their roofs, the roof graph
# as declared, the budget, and the specimen GLB the generator's bytes.
step "the K05 roof kit builds every roof as one closed, uncrossed solid with its declared ridges, hips and valleys (T-2301)" \
  python3 tools/check_roof_kit.py --check

selftest "…and a hole, an inward face, a doubled face, a roof through its gable, a floating return or a low parapet still fails it" \
  python3 tools/check_roof_kit.py --self-test

# T-2305. ...and what the 1904 conservatories are. The K13 kit's houses are sized in
# data/components/prairie_1904/k13_conservatories.json and built by
# generators/archetypes/k13_conservatories.py. This rebuilds every house and measures
# the geometry: every primary prouder and wider than every plate and every plate than
# every glazing bar, panes inside the glass range with the bars dividing each run evenly,
# the glass one convex single-sided envelope (one transparency per line of sight), no
# glass below the plinth's coping, every eave to a K04 gutter and every pipe to grade
# clear of the coping, the planting opaque, clear of the glass and below the eave, the
# curvilinear roof on its curve, no doubled face, the triangle budget, and the specimen
# GLB the generator's bytes.
step "the K13 conservatory kit builds every glasshouse as a three-tier frame over one convex single-sided envelope, every eave to grade (T-2305)" \
  python3 tools/check_conservatory_kit.py --check

selftest "…and bars as heavy as plates, a transparent lantern, an inward pane, a gutterless eave, a short pipe or a plant scene still fails it" \
  python3 tools/check_conservatory_kit.py --self-test

# T-2322. ...and what the 1904 frame houses' timber is. The K16 kit's cladding, trim,
# Gothic woodwork and porch are sized in data/components/prairie_1904/k16_timber.json and
# built by generators/archetypes/k16_timber.py, its cased window's sash from K06. This
# rebuilds every sample and measures the geometry: clapboard and shingle exposure inside
# the reconstruction rules' range and the wall inside the K01 frame range (never a
# masonry wall's thickness), every course's butt one exposure above the last with a
# shadow line and resting on the course below, joints staggered course to course, a
# batten bearing on both boards over every gap, trim proud of the cladding it stops,
# every bargeboard piercing open and cut through, an end-grain face at every joint,
# every timber part on a painted, stained or end-grain material, restrained per-board
# wear, no doubled face, the triangle budget, metric UVs, and the specimen GLB the
# generator's bytes.
step "the K16 timber kit builds every frame wall board by board: lapped courses, staggered joints, battens over joints, piercings cut through, a frame wall's thickness (T-2322)" \
  python3 tools/check_timber_kit.py --check

selftest "…and an 8 in exposure, a masonry-thick wall, sunken corner boards, lined-up joints, an open batten joint, a floating course or a covered piercing still fails it" \
  python3 tools/check_timber_kit.py --self-test

# T-2307. ...and what the 1904 bays, oriels and towers are. The K08 kit's plans, supports,
# bands, eaves and roofs are sized in data/components/prairie_1904/k08_bays.json and built
# by generators/archetypes/k08_bays.py, its windows from K06. This rebuilds every variant at
# both tiers and measures the geometry: keyed to its wall and never behind it, closed (rays
# from inside meet the bay), every pane over its own recess one glass layer deep, recesses
# inside the bay and clear of each other, no doubled face, curves cut fine with true
# normals, a plinth or corbels within their oversail, the light tier on the full tier's
# silhouette, the triangle budgets, and the specimen GLB the generator's bytes.
step "the K08 bay kit builds every bay, oriel and tower closed against its wall, its curves unfaceted (T-2307)" \
  python3 tools/check_bay_kit.py --check

selftest "…and a window off its run, a recess through the wall, a faceted curve, an oriel on one deep course or a roof with a hole still fails it" \
  python3 tools/check_bay_kit.py --self-test

# T-2787. ...and a K01 frontage carries a K08 tower past its eave (the kit piece 1801
# Prairie's move needs). Built on two committed records with a tower added, a hip and a
# mansard: the cap over the main roof, the ring closed above the wall head in the wall's
# plane, the wall head's brackets and bed moulding stopped at its junctions, the lights
# behind it dropped; a tower under the eave, out of its size range or in front of a door
# refused.
step "a K01 frontage carries a K08 tower past its eave, closed above the wall head and the wall head stopped at it (T-2787)" \
  python3 tools/test_k01_tower.py

# T-2841. ...and a K01 rear wing takes a hipped or gabled roof in K04's slate, where it was
# decked flat in tin (the kit piece 1801 Prairie's gabled section and east range need).
# Built on 1604's two wings and on 1811 as all-stone with its range raised over the main
# eave: the slate's eave and ridge, the ridge across the wing into the host wall or along
# it, the gable's walling, the junction closed above the host's top and the host wall
# drawn from the wing's wall top; a slate cut short for its pitch, a hip in tin, a gable
# facing no side and two slates on one house refused; every committed wing still flat.
step "a K01 rear wing takes a slated hip or gable, its junction with the host closed above the host's top (T-2841)" \
  python3 tools/test_k01_wing_roof.py

# T-3063. ...and a K01 gable roof's rear slope falls steeply to a flat deck under a level
# coped wall head (1811 Prairie's south wall behind its tall stack, level in both its
# pictures): the deck under the coping, the line level to the fall's foot and clear of the
# covering everywhere, 1811 built so, the plain coped line unchanged, and a fall over
# stepped ends, out of its pitch range, over the ridge or with too long a head refused.
step "a K01 gable roof's rear slope falls to a deck under a level coped wall head (T-3063)" \
  python3 tools/test_k01_rear_fall.py

# T-3144. A K07 swept stoop's cheek drawn in to its newel (a negative flare) and a cheek pierced
# by a row of openings under its top, as Levy's print shows 1812 Prairie's: built so, each
# opening open through the cheek, the plain stair back without them, and the misfits refused.
step "a swept stoop's cheek drawn in to its newel and pierced under its top (T-3144)" \
  python3 tools/test_k07_stair_foot.py

# T-2842. ...and a K08 tower stands on a K01 rear wing's wall, past the wing's own eave (the
# kit piece 1801 Prairie's north-east turret on its east range needs). Built on 1604's
# brick range under its flat deck and on 1811 as all-stone with its rear section hipped in
# slate: the cap over the wing's roof, the ring closed over the wing's wall top in its
# wall's plane, the wing's wall open behind it and its lights there dropped; a tower under
# the wing's eave, a bay or an oriel on a wing, a gable end, a later wing's junction, a
# corner and a wall no wing has refused.
step "a K08 tower stands on a K01 rear wing's wall past the wing's eave, closed over its wall top (T-2842)" \
  python3 tools/test_k01_wing_tower.py

# T-2843. ...and what 1801 Prairie's move onto K01 needed, held on its record: a mansard face
# holding two storeys rises 4.5-7.5 m (one stays the attic's 2.0-4.5 m), a K08 projection
# carried past the main eave is closed on the wall plane behind it and at its cap's end (one
# at the eave, 1812's, gains nothing), and a wing slated in the main roof's slate keeps its
# own material, so the publish path's dedup cannot merge its name away.
step "a mansard face holds two storeys; a K08 pavilion past the eave is closed behind it (T-2843)" \
  python3 tools/test_k01_pavilion_past_eave.py

# T-3002. ...and 1801 Prairie's carved stone: K10's moulded stone cornice under a mansard, run
# round the walls the record names and dying into the bays on them; a K08 storey's head
# frieze with its roundel; and a K08 gable's carved panel, its relief dropped on the light tier.
step "a stone cornice runs under a mansard; a K08 head frieze and gable panel (T-3002)" \
  python3 tools/test_k10_mansard_cornice.py

# T-3097. ...and its second-storey lights: K01's side_bays take windows read off a picture, as
# north_bays do, each laid once at its own sill; a read round head on an all-stone side face
# stands in the coursing under no flat arch, its spandrels in the wall's stone.
step "side_bays take read windows; a read round head on a stone side face has no flat arch (T-3097)" \
  python3 tools/test_k01_side_read_windows.py

# T-2900. ...and what 1801 Prairie's east range needed, held on its record: a K01 wing may run
# past its host wall's ends when it says `past_host` (still standing on 1.0 m of that wall),
# with a front wall of its own drawn only past the host and its roof cut only along it; and a
# K08 corner turret on a rear wing's wall (`corner`), its ring 0-0.3 m inside the end wall's
# plane, its eaves the wing's own and its cone whole over the wing's roof, closed behind by
# nothing. Each refusal round both says why.
step "a K01 wing runs past its host wall; a K08 corner turret stands at a wing's end (T-2900)" \
  python3 tools/test_k01_wing_past_host.py

# T-3006. A K01 front block may round a corner (`round_corner`, 1811's south corner off the
# 1888 plate): a quarter round in the front's stone, coursed on its beds and corbelled to the
# square in its last course, the front and side wall stopped at its tangents; a front pipe may
# stand behind the front's plane only on the round, clear of it. Each refusal says why.
step "a K01 front block rounds a corner in its own stone (T-3006)" \
  python3 tools/test_k01_round_corner.py

# T-3064. A wall gable's pinnacle shaft may stop under its block (1811's north pinnacle off the
# 1888 plate): a band below the face's eave, a scaled stone leaning in from it to the block's
# plinth, and the eave's end dying into that stone. Each refusal says why.
step "a K01 wall gable's pinnacle stops under its block in scaled stone (T-3064)" \
  python3 tools/test_k01_pinnacle_under_block.py

# T-2998. ...and 1801 Prairie's south pavilion's coped stone gable, from the Taylor photograph:
# a K08 projection's roof may be a `gable`, its front carried up between kneelers under raking
# stone copings, a slope from each kneeler to a ridge on its middle run back to the wall, a
# pinnacle on each kneeler and a stone finial on the apex; the front has no eaves and the
# returns' stop on its plane inside the kneelers. Every other roof builds as before, and each
# refusal round it says why.
step "a K08 projection takes a coped stone gable (T-2998)" \
  python3 tools/test_k08_gable.py

# T-2788. ...and what an all-stone house is. A K01 record naming `construction: "stone"`
# lays its K02 stone_front round every face, not a stone front on a brick box. No record
# names it yet (1801 Prairie, T-2789, is the first), so this builds four houses that carry
# a K02 front as all-stone, in memory, and measures them: every wall coursed in the
# record's stone, no brick under the eave, every course on the front's beds (level round
# each corner), a stone flat arch over every opening off the front, no coincident face;
# a quoin bond, a brick bay or a missing stone_front refused; every record as committed
# still brick on its flanks.
step "the K01 kit lays an all-stone house in its K02 stone round every face (T-2788)" \
  python3 tools/check_stone_house_kit.py --check

selftest "…and flanks left in brick, a corner off the front's beds, a headless opening, a doubled face or a refused record built anyway still fails it" \
  python3 tools/check_stone_house_kit.py --self-test

# T-2303. ...and what the 1904 entrances are. The K07 kit's parts are sized in
# data/components/prairie_1904/k07_entrances.json and built by
# generators/archetypes/k07_entrances.py. This rebuilds every variant and measures the
# geometry: the landing level with the threshold, the stair's foot on grade, equal
# risers and goings inside the reconstruction rules' ranges, every step closed, the walk
# clear, a carriage opening through its wall under a bearing lintel, a closed reveal,
# leaves clear of the floor, a hall behind every light, no doubled face, the triangle
# budget, and the specimen GLB the generator's bytes.
step "the K07 entrance kit lands every stair on its threshold and on grade, risers equal, the walk clear (T-2303)" \
  python3 tools/check_entrance_kit.py --check

selftest "…and an unequal riser, an open step, a stoop on the walk, an unbearing lintel or a floating leaf still fails it" \
  python3 tools/check_entrance_kit.py --self-test

# T-2309. ...and what the 1904 trim is. The K09 kit's parts are sized in
# data/components/prairie_1904/k09_trim.json and built by generators/archetypes/k09_trim.py.
# This rebuilds every variant and measures the geometry: every open edge of a piece lying on
# another surface (nothing floats, nothing hangs, nothing over a hole), every closed leaf,
# crocket and finial passing through its host, no doubled face, each piece's relief as the
# data says and never under the floor, radial joints and a centred crown stone, colonnettes in
# order, the panel's leaves inside their field, the hero entrance beyond the rowhouse, the
# triangle budgets, and the specimen GLB the generator's bytes.
step "the K09 carved-trim kit builds every ring, hood, capital, tracery and leaf as seated relief (T-2309)" \
  python3 tools/check_trim_kit.py --check

selftest "…and an even ring, a painted-thin stone, a floating block, a loose leaf, a back face on the wall or a skewed joint still fails it" \
  python3 tools/check_trim_kit.py --self-test

# T-2316. ...and how the 1904 wall heads end. The K10 kit's parts are sized in
# data/components/prairie_1904/k10_cornices.json and built by generators/archetypes/k10_cornices.py.
# This rebuilds every variant and measures the geometry: every open edge of a piece lying on
# another surface (no hanging end, no floating bracket), every closed kneeler, finial, ridge cap
# and iron bar passing through its host, no doubled face, every run turning both corners of its
# face by its own projection, brackets evenly spaced with one at every corner on both faces,
# baluster gaps, no dormer below its roof, cresting posts, budgets, and the specimen GLB.
step "the K10 cornice kit turns every corner and seats every bracket, rail, coping, dormer and bar (T-2316)" \
  python3 tools/check_cornice_kit.py --check

selftest "…and a dropped bracket, a lifted finial, a doubled dentil, a short crown, a sunk dormer or a missing post still fails it" \
  python3 tools/check_cornice_kit.py --self-test

# T-2312. ...and how a 1904 chimney meets its roof. The K15 kit's parts are sized in
# data/components/prairie_1904/k15_chimneys.json and built by
# generators/archetypes/k15_chimneys.py: each stack joined to a K05 roof by the boolean
# union, its flues cut out by the difference. This rebuilds every variant and both tiers
# and measures the built surface: watertight, one shell with its roof, no doubled face,
# no face through another, nothing below the covering, every flue a dark recess of its
# depth, the draught clearance, cricket or back flashing as the width asks, stepped
# flashing on every side, a light tier on the same centre and top, the budget, and the
# specimen GLB the generator's bytes.
step "the K15 chimney kit seats every stack in its roof as one closed solid, flues recessed and flashed on every side (T-2312)" \
  python3 tools/check_chimney_kit.py --check

selftest "…and a hole, a floating or sunken shaft, an uncut or grey flue, a short stack, a missing cricket or flashing, or a light tier off its stack still fails it" \
  python3 tools/check_chimney_kit.py --self-test

# T-2318. ...and what bounds the 1904 lots. The K11 kit's parts are sized in
# data/components/prairie_1904/k11_ironwork.json and built by generators/archetypes/k11_ironwork.py.
# This rebuilds every variant and measures the geometry: every member a closed solid let into
# what carries it (a picket through its rail, a rail into its post, a post, pier, curb or wall
# past grade), no doubled face, no iron member under the walking-distance shimmer floor, even
# panels inside the clear-gap range, a gate on two hinges that swings into the yard clear of its
# pier with nothing else in its opening, wall piers and coping drip, canopy fall, budgets, the GLB.
step "the K11 ironwork kit lets every member into its carrier, keeps runs out of entrances and nothing under the shimmer floor (T-2318)" \
  python3 tools/check_ironwork_kit.py --check

selftest "…and a lifted picket, a 6 mm rail, a curb across the gate, a one-hinge gate, a flat canopy or a missing pier still fails it" \
  python3 tools/check_ironwork_kit.py --self-test

# T-2320. ...and what stands at the back of the lot. The K12 kit's parts are sized in
# data/components/prairie_1904/k12_coach_house.json and built by
# generators/archetypes/k12_coach_house.py. This rebuilds the coach house and measures the
# geometry: every open edge lying on another surface (a wall's foot on the ground, its end on
# the wall it meets, a rake on the roof, a leaf on its reveal, the wing on the coach house and
# the house), every strap, beam, coping and cleat passing through its host, no doubled face,
# every elevation closed, every opening cut through its wall, the ramp and the stair at grade,
# no ventilator without a source, budgets, and the specimen GLB.
step "the K12 coach-house kit closes every elevation, cuts every opening through and sets its ramp and stair on grade (T-2320)" \
  python3 tools/check_coach_house_kit.py --check

selftest "…and a wing off its wall, a loose hoist beam, a doubled sill, an open elevation, a painted-on door or a sourceless ventilator still fails it" \
  python3 tools/check_coach_house_kit.py --self-test

# T-2324. ...and how old each of them looks. The K14 condition kit's layers (ground damp, eave
# soot, water trails, chimney plume, mortar, paint, grass edge, path wear) are data in
# data/components/prairie_1904/k14_condition.json, evaluated by generators/archetypes/k14_condition.py.
# This evaluates every layer over every fabric, age and height and holds it to 1904: every tone in
# [floor, 1], nothing cleaner with age but repainted wood, new work clean, a 38-year wall visibly
# older and still its own material, the full-age damp and soot equal to K03's, and the study's
# costs re-derived.
step "the K14 condition kit weathers each building to its own age in 1904, new work clean and nothing a ruin (T-2324)" \
  python3 tools/check_condition_kit.py --check

selftest "…and a black facade, a moss layer, a plume into the wind, a widening trail or a 40-year repaint still fails it" \
  python3 tools/check_condition_kit.py --self-test

# T-1963. The walls' relief is bound by reading the RECORD (route 2 of the photographic
# fabric preparation, docs/GLB-CONTRACT.md § Wall substrates, PROPOSED): which wall is
# clapboard, and how much of the wood's grain its finish lets through. That route's
# stated price is a renderer rule that must stay in step with materials.py, so this runs
# renderers/web/js/wall-grain.js itself over every record and holds it to
# wall_substrate() / wall_finish(), and to the `wall` materials the GLBs actually carry.
step "the walls' relief rule matches the substrate and finish the generators build (T-1963)" \
  python3 tools/check_wall_relief.py --check

selftest "…and a coat read as bare, a vertical board bound as clapboard or a finish_key outranking a coating still fails it" \
  python3 tools/check_wall_relief.py --self-test

# T-1973. The relief maps the walls, roofs, street edge and signboards bind ship as
# lossless WebP beside their PNG masters — boot bytes every visitor downloads, a third
# smaller on the wire. "Lossless" is a claim about pixels, so the gate reads them back:
# every derivative decodes to exactly its master, and none is an orphan.
step "the WebP maps the renderer binds decode pixel-identical to their PNG masters (T-1973)" \
  python3 tools/web_textures.py --check

selftest "…and a missing, lossy, resized, mislabelled or orphaned derivative still fails it" \
  python3 tools/web_textures.py --self-test

# T-2582. The KTX2 beside each drop-in sheet (roof relief, 1904 streets, the ground strip's
# muck), which js/ktx2.js loads in place of the image where the GPU takes a block format.
# KTX2 is lossy by design, so this reads what the renderer relies on, not pixels: the file
# is there and is a KTX2, it is its web map's size, it carries the full mip chain the
# light tier drops the top of, and no .ktx2 sits in the library that no sheet names.
step "every drop-in library sheet carries its KTX2: its web map's size, a full mip chain, no orphans (T-2582)" \
  python3 tools/ktx2_sheets.py --check

# T-2299. ...and the relief in them points the way its name says. The 1835 library's
# generator wrote green as -dh/drow, the DirectX sign, into every `normal_gl` and filed
# the OpenGL map as `normal_dx`, as the 1904 street library did until T-2296. Every
# board, log, shingle and signboard binds `normal_gl` through a flipY'd texture, so all
# of it was lit upside down along +V. This correlates both files of all 27 materials,
# and the WebPs the renderer binds, with their own height16's slopes.
step "the 1835 library's normal maps are handed as named, OpenGL and DirectX (T-2299)" \
  python3 tools/check_1835_normals.py --check

selftest "…and a DirectX map filed as OpenGL, the reverse, or a mirrored red still fails it" \
  python3 tools/check_1835_normals.py --self-test

# T-2300. ...and the maps the page derives beside them lie the same way up.
# wall-relief.js's `orl` and frontage.js's board grain are packed from canvas pixels
# (top row first) into a DataTexture, which three uploads unflipped, and are sampled
# on the uv of a normal_gl uploaded with flipY — so until T-2300 every wall's and
# walk's AO, roughness and grain was its relief's mirror along v.
step "the derived wall and board-face maps lie the way their normal_gl does (T-2300)" \
  node tools/check_relief_rows.mjs --check

selftest "…and a packer that writes them in canvas order still fails it" \
  node tools/check_relief_rows.mjs --self-test

# T-1251. The ground's zone table for the same scene. Its street crowns are READINGS
# (data/terrain/e1871_grade_readings.json) put through the spec's own datum
# conversion, its fill is the difference to the committed 1835 heightfield and
# must not come out constant (the ticket's claim that the two epochs are not
# offsets of one another), and its evidence limit is derived here rather than
# carried over from 1835. Every elevation cites a zone the research doc has.
step "the e1871_postfire zone table re-derives from its readings (T-1251)" \
  python3 tools/check_terrain_e1871.py --check

selftest "…and a hand-edited crown, a constant fill or an inherited limit still fails it" \
  python3 tools/check_terrain_e1871.py --self-test

# T-2002. The 1812 ground's zone table, written as an OVERLAY on the 1834 one: every
# 1834 block is carried, excepted, replaced or dropped with a reason, so a block added
# to 1834 later cannot reach the 1812 ground by default. The blocks it authors (the
# lake stage, the spit, the isthmus L240 left open, the live outlet channel, the shore
# north of the spit root, the west-bank ruling T-1286 asked for) cite dossier zones and
# stay inside their ranges, and the effective table resolve() builds carries no work.
step "the e1830_natural zone table accounts for every 1834 block (T-2002)" \
  python3 tools/check_terrain_e1830.py --check

selftest "…and an undecided block, a harbour work carried back or a breached isthmus still fails it" \
  python3 tools/check_terrain_e1830.py --self-test

# T-1738. …and the heightfield that zone table and the scene line generate. The
# field is numpy arithmetic and re-derives byte for byte; the meshes are Blender's
# and are held by their input hash (validate.py --stale) and the fit gates below.
step "the 1904 heightfield re-derives from its zone table and scene line (T-1738)" \
  python3 generators/terrain_gen_graded.py --check

# ...and for the North Branch north of it (T-1072). Two tools write one
# branches.geojson through tools/branches_file.py, and each of these two steps
# also holds the collection's shared fields and its declared feature order, so
# a writer that dropped the other's reach is caught by BOTH of them.
step "the traced North Branch still carries what its generator writes" \
  python3 tools/trace_north_branch.py --check-properties

# T-1078. The North Branch's east bank was short of Wright's inked bank by up to
# 32.7 m at the splice row, because a dry seam cut 402 px of bank wash off the
# channel and the speckle floor threw it away. `tr.seam_wash` puts it back, and
# the repair is only safe in one direction: it must not have bought back the 93 m
# leak into Wabansia's platted lots that `hue_tol` 7 exists to prevent. This holds
# the committed measurement to that — 0 rows west of the inked west bank — and to
# the two trace windows agreeing on the channel's drafted width across the line
# they are spliced on, which is what independently says the repair is right.
step "the North Branch's repaired east bank has not leaked the west one" \
  python3 tools/measure_north_branch_banks.py --check-properties

# T-0862. The NARA/Historic Urban Plans registration is the enabler the whole Wright
# band stands on — at 600 dpi it resolves the Original Town's block numerals where the
# BPL scan does not — and until now `grep -i nara` over this gate returned nothing but
# unrelated Playwright comments. A hand edit to a coefficient, a residual or the
# checksum would have passed every gate this project has, silently moving every reading
# taken through the fit. This is the offline half, the same split trace_river.py makes:
# each control point's residual, the RMS, the axis scales, the rotation, the scan-to-scan
# departures, the scale bar's px-per-foot and each lacuna's ground extent, all re-derived
# from the coefficients and the eight picked points. It re-picks nothing; re-locating the
# correspondences off the raster stays the deliberate second tier.
step "the Wright NARA registration still re-derives from its own control points" \
  python3 tools/check_wright_nara_registration.py --check-properties

selftest "…and its own assertions still fire when broken" \
  python3 tools/check_wright_nara_registration.py --self-test

# T-0792 piece 1. The nine coloured chips of Wright's legend are the only place any
# sheet in this project says who surveyed what ground and when, and three open tickets
# ask to read a wash "against the legend's swatches". This holds the reading offline:
# every pairwise chip distance re-derives from the committed medians, the grouping into
# separable colours re-derives at the committed threshold, each band's local metres
# re-derive through the committed affine, and the one chip-to-ground claim — that every
# committed side of section 16 falls inside chip 5's band — re-derives from the blocks
# file's own anchor. The REFUSAL is gated too: if a future edit ever made the nine chips
# look separable, the step says so, because the two ambiguous swatches are refused on
# exactly that arithmetic.
step "Wright's legend chips still refuse what they cannot separate" \
  python3 tools/read_wright_legend_swatches.py --check-properties

selftest "…and that reading's assertions still fire when broken" \
  python3 tools/read_wright_legend_swatches.py --self-test

# T-0795. The whole-sheet watercourse count, and what it costs to be wrong about it:
# the audit's headline is that Wright draws ONE watercourse that is not the river, so
# every number it rests on has to stay re-derivable or the count becomes an assertion.
# Offline half — the two bank re-entrant picks carried through the committed affine and
# checked against the E-ranges the traced 1834 waterline gives for the La Salle and
# State Street mouths, the station count against the committed centreline, the scale
# against the fit's axes, and every id the audit names against the terrain that holds
# it. The raster half is `--check-sheet` and needs Pillow and numpy, which this gate
# does not have.
step "Wright's whole sheet still counts one watercourse that is not the river" \
  python3 tools/audit_wright_watercourses.py --check-properties

selftest "…and that audit's assertions still fire when broken" \
  python3 tools/audit_wright_watercourses.py --self-test

# T-1080. The second, INDEPENDENT read of that one watercourse — off the 600 dpi NA/HUP
# sheet under its own registration, where `north_side_slough` was traced off the BPL
# master scan. It began life as a road record and the road was withdrawn: the two
# readings are one feature, and this is the only cross-check that record has. `--check`
# re-derives every metre, and the identity figure with it, from the committed pixels
# without opening the raster, so the gate can ask it. The raster half is `--check-sheet`
# and needs Pillow and numpy, which this gate does not have.
step "the NA re-read of the north-side slough still lands on the committed centreline" \
  python3 tools/read_north_side_slough_na.py --check
# T-1630. The same instrument on the South Division bank: the committed waterline from the
# bend to past the La Salle mouth, measured against the bank Wright INKED on the NA/HUP
# sheet, and the swell the owner reported measured inside each 1834 sheet separately so no
# registration enters it. The master scan cannot be re-fetched (its pin refuses the bytes
# BPL now serves), so this is the only check that record has. `--check` re-derives every
# metre offline from the committed pixel stations; the raster half is `--build`. The step
# also holds the reading's own VERDICT — if a later edit moves the committed bank off
# Wright's ink, the prose here would still read correctly and only this would notice.
step "the South Division bank still stands on Wright's inked bank" \
  python3 tools/read_south_bank_swell_1834.py --check
selftest "…and that reading’s gate still fires when its figures are broken" \
  python3 tools/read_south_bank_swell_1834.py --self-test
# T-1101. The nine chips, put on the ground. Seven of the nine tracts are polygons now —
# every one of them re-derived here from geometry this project already committed, never
# traced off a wash — and the two that name no tract are REFUSED, with the number that
# would change the refusal attached. This step rebuilds all seven rings from their own
# inputs and re-takes all 116 band verdicts from the band centroids the record carries,
# so a street line that moves, a section corner that drifts, a seating that is re-fitted
# or a grade quietly upgraded is a failure here rather than a claim nobody re-checked.
# The REFUSALS are gated too, for the same reason the swatch step gates its own: if a
# later edit gave Wabansia colour evidence it does not have, or handed one of the unnamed
# chips a polygon, the prose would still read correctly and only this would notice.
step "the nine survey tracts still stand where their committed ground puts them" \
  python3 tools/build_survey_tracts.py --check-properties

selftest "…and the tract layer's assertions still fire when broken" \
  python3 tools/build_survey_tracts.py --self-test

# T-1104. The tract layer names who surveyed the ground; the register names who bought it,
# and since T-0609 it has been on the ground. This joins them, and the join is where two
# committed files can quietly stop agreeing: a section corner that drifts, a seating that is
# re-fitted or a school-section block that moves changes which polygon a parcel falls in
# WITHOUT changing either file's own gate. So every share is re-clipped here from the
# committed rings and compared to the last decimal. The prose claims are gated as numbers
# too — that none of the seven 1830 canal entries touches the Original Town, that no row
# refused for being off the modelled ground names one of the four carried sections, and
# that the town-plat lots are still refused rather than sorted on a guess at their code.
step "the register's parcels still fall on the same survey tracts" \
  python3 tools/sort_land_sales_onto_tracts.py --check

selftest "…and the clip, the precedence clause and both refusals still fire when broken" \
  python3 tools/sort_land_sales_onto_tracts.py --self-test

# T-1082. The swatch reading above is of the NA/HUP facsimile; the North Branch's
# disputed bank wash is on the BPL master, and the same nine chips are not the same
# nine colours on the two sheets. This holds the master-side reading offline: the
# chips' pairwise separations and their grouping re-derive from the committed
# medians, each stretch's dilution rays re-derive from its band and paper colours,
# each verdict re-derives from the stated rule, and the stretches themselves are
# read from the bank baseline rather than re-declared. BOTH REFUSALS ARE GATED —
# if a future edit ever made the two sheets' chips agree, or put a facsimile band
# on this reach, or identified the east stretch's colour, the step says so, because
# those are exactly the three things docs/RESEARCH/north_branch_wabansia.md § 5
# refuses on.
step "the North Branch's bank wash is still a colour the legend cannot name" \
  python3 tools/read_north_branch_bank_wash.py --check-properties

selftest "…and that reading's assertions still fire when broken" \
  python3 tools/read_north_branch_bank_wash.py --self-test

# Runs early and costs milliseconds, because the fault it catches is cheap to
# make and expensive to ship: on 2026-08-24 three conflict-marker lines rode a
# merge into docs/LIBERTIES.md, compiled into data/liberties.json, published to
# the mirror and PROMOTED TO PRODUCTION, where a visitor opening L180 or L181
# read `# the liberties gate asks whether the markdown and the compiled JSON agree, and
# they agreed perfectly — both carried the same garbage.
step "no committed file carries a conflict marker" \
  python3 tools/test_no_conflict_markers.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/test_no_conflict_markers.py --self-test

# T-0820, and it sits here because it is the same fault as the line above: a
# merge that kept both sides. `dev` went red TWICE on 2026-09-05 on a duplicated
# id — two branches minting ticket T-0739, then a second byte-identical
# `west_water` in data/streets/1835.json from a branch cut before the first one
# landed — and a third came the same evening from an agent staging a `UU` with
# `git add -A`. None was caught on the branch that wrote it; all three were found
# by this script running against dev AFTER the merge, which is the expensive
# place to find anything, because the dev gate is the base every open PR
# inherits. One duplicate parked nineteen PRs behind a red they had not caused.
# It is worse now than it was then: dev carries a ruleset requiring `gate`, so a
# red dev no longer discourages merging, it forbids it.
#
# The rule is DISCOVERED, not listed — it applies wherever the shape appears (a
# list of two or more objects that all carry an `id`), so a list added tomorrow
# is covered without anybody remembering to register it. 2,835 files, 0.6 s.
# T-0829 extended it to lists of STRINGS — provenance, coverage, citations — which
# carry no `id` for the rule above to read: every one is held as a set unless the
# tool's MULTISETS table names it (one element per row, rows allowed to agree).
step "no committed list carries the same id, or the same string in a set, twice" \
  python3 tools/check_unique_ids.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/check_unique_ids.py --self-test

# NO DERIVED FIGURE HAS ITS LAST DIGIT DECIDED BY ACCUMULATION ORDER (T-1486). `sum()`
# adds left to right and drifts a few parts in 10^15 — nothing on a height or an easting
# until the true value sits exactly on the rounding boundary, at which point the drift,
# and not the measurement, prints the last digit. Two gated writers flapped their
# committed output between this loop's machine and CI's for that reason (T-1477): a
# ground reading that printed a mean OUTSIDE its own min and max, which rounding being
# monotonic says is impossible, and twenty block centroids sitting precisely on the 2 dp
# boundary because Kinzie's Addition is platted in feet. Measuring it found the cause the
# fix had only guessed at: CPython 3.12 compensates `sum()` for floats and 3.11 does not,
# and chicago-4d-check.yml pins 3.11 — so the same code on the same data genuinely
# printed a different digit in CI than on the machine that committed it. This step keeps
# the sweep swept (an AST census, because four of the sites put `round(` and `sum(` on
# different lines and no grep can see them), re-adds the committed aggregates whose
# components are committed beside them and reports any figure sitting within a part in
# 10^12 of its boundary, and mutation-tests the min-max-mean refusal by restoring the
# uncompensated sum and watching it fire.
step "no derived figure is rounded by accumulation drift" \
  python3 tools/check_exact_sums.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/check_exact_sums.py --self-test

# THE STRUCTURE FUNCTION VOCABULARY IS CLOSED (T-1311). `function.value` was a free
# string and 384 records had spelled it 109 ways — three of them the same word twice
# (`blacksmith_shop` and `blacksmith shop`, `store_residence` and `store-residence`,
# two spellings of the cooper/wheelwright shop). The signage rule, the yard goods,
# the street-edge furniture and the register's occupation crosswalk all match this
# value EXACTLY, so a second spelling is a trade those rules cannot see: closing the
# vocabulary gave nine anonymous roofs a WRITTEN refusal apiece in three derived
# layers that had simply not noticed them. `data/structures.schema.json` carries the
# vocabulary and validate.py refuses a value outside it; this asks the two questions
# the schema cannot — that every committed value is its own canonical form under the
# folding rule, and that no OTHER copy of the vocabulary has gone stale against it
# (the signage rule's trade names, the card's FUNCTION_WORDS, where `store-residence`
# sat as an unreachable branch for as long as the free string existed).
step "every structure function is a term of the closed vocabulary" \
  python3 tools/normalise_structure_function.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/normalise_structure_function.py --self-test

# THE QUEUE'S MERGE DRIVER. QUEUE.md is reconciled by tools/merge-queue.mjs —
# ours' order, theirs' closes and theirs' new tickets — because a text merge of
# a re-ranked queue against a branch that closed tickets conflicts on every hunk,
# and `union` would hand back both orderings with every ticket twice. Landing one
# re-rank on 2026-09-04 cost four merges of dev and four hand reconciliations.
selftest "the QUEUE.md merge driver still does what .gitattributes promises" \
  node tools/merge-queue-selftest.mjs

# T-0817, AND IT IS A GATE BECAUSE A DRIVER CANNOT REACH FAR ENOUGH. The ranking
# has been lost three times: 2026-09-04 ("the queue got massively reordered"),
# again on 2026-09-05 via PR #801 — a branch cut long before the re-rank, which
# took dev from the restored 415-line file back to the 2026-08-30 revision — and a
# third time to the drain band (#909). The driver above REFUSED the #801 merge and
# it made no difference, for the reason T-0817 names exactly: GitHub does not run
# this repository's merge drivers, so a squash-merge on the server never loads one.
# The driver protects a local `git merge` and cannot protect the thing that lands.
#
# check.sh is the required `gate` on dev's ruleset, so this refuses the merge
# BUTTON, which is the only place the regression actually arrives. What it asserts
# is not a judgement about ranking — it is that every re-rank the base already
# records is still present in the compact tickets/QUEUE_ORDER.md ledger. A branch
# missing one predates it, and merging it would put the old order back.
step "the owner's queue ranking has not gone backwards" \
  node tools/check_queue_order.mjs

# THE CHANGELOG-ENTRY GATE ANSWERS THE RIGHT QUESTION ABOUT THE RIGHT FILES, and
# until 2026-09-13 nothing tested that it did. `check-changelog-entry.mjs` runs
# only from the PR workflow (its own header says why: the nightly bake regenerates
# data/ and a gate inside check.sh would fail every bake), so its behaviour was
# never exercised anywhere — and it was the commonest cause of a red PR that day.
# Not for being strict about the town: `tools/dev-smoke-state.json` is T-0216's
# register of smoke RESULTS and sits under the watched `tools/` prefix, so a run
# that filed its readings — which AGENTS.md REQUIRES — drew a red gate for obeying
# the contract. #1264 and #1269 were red with that file as the only watched path
# they touched, and the same hand-written `Changelog: none` trailer had been added
# to #1090, #1108, #1126 and #1247 two days earlier. #1255 is NOT that shape and
# stays red correctly — it changed smoke_renderer.mjs too — which is the case the
# test's last two assertions pin.
#
# The exemption fixes it once; this keeps it fixed, and holds the gate's other
# answers while it is there — an exemption list is exactly the kind of edit that
# quietly widens. It asserts the gate STILL BITES on a real change with no entry,
# that the opt-out still needs a reason, and that a moved BASELINE beside the smoke
# register is NOT exempt, because a baseline is a claim about the town.
step "the changelog-entry gate exempts a smoke reading and still bites on a change" \
  node tools/test_changelog_entry_gate.mjs

selftest "…and its own assertions still fire when broken" \
  node tools/check_queue_order-selftest.mjs

# THE CHANGELOG'S MERGE DRIVER. Same reasoning, higher stakes: this file's history
# is seven repairs long, five of them in one day when `union` spliced one entry
# into another and left valid JavaScript nobody noticed. The driver never works
# below entry granularity, and REFUSES if both sides edited one shipped entry.
selftest "the changelog merge driver still does what .gitattributes promises" \
  node tools/merge-changelog-selftest.mjs

# T-0831. THE BUILD PRODUCTS' DRIVER, AND THE LEDGER'S. The measurement that
# bought these: PR #906 was open seventy minutes, `dev` moved FIVE times under it,
# and all five merges conflicted — always in generated files, never once in the
# substantive diff. #894 and #850 record the same, #850 pricing a lap at ~19
# minutes of verification during which dev took three more merges. Keeping ours is
# safe on those five because the gate ALREADY refuses each of them stale
# (ticket.mjs check, test_ticket_mirror.mjs, check_published.mjs), so the conflict
# was never what protected them.
#
# The half worth testing hardest is the file that is NOT one of them:
# tools/dev-smoke-state.json sits in the same conflict set and is an append-only
# ledger whose rows carry no id and which no step here reads — "keep ours" would
# have dropped the other side's readings silently. The suite proves no reading is
# ever lost, and ends with a REAL git merge, because a driver that works perfectly
# and is never invoked looks exactly like no driver at all.
selftest "the build-product and smoke-ledger merge drivers do what .gitattributes promises" \
  node tools/merge-generated-selftest.mjs

# T-0833. THE LAP THAT USES THEM. Every driver above only ever protects a LOCAL
# merge — git keeps a driver's command out of tracked content, so GitHub loads
# none of them and reports a conflict a clone does not have (measured on PR #940).
# Six PRs stood open against dev on 2026-09-13, all six called conflicting by
# `git merge-tree`, and on only four files: changelog.js (6), QUEUE.md (6),
# dev-smoke-state.json (5) — all three driver-covered — and assets/manifest.json
# (1), which is a real one. tools/drain.mjs is the clone that can apply the first
# three and hand back the fourth, and what is tested hardest is the handing back:
# a batching tool that quietly picks between two research claims looks exactly
# like one that works. The suite asserts the refusal exits non-zero and LEAVES THE
# MARKERS, which is the property a person actually uses.
selftest "the drain lap still refuses every conflict its drivers do not cover" \
  node tools/drain-selftest.mjs

# ADVISORY, NEVER A FAILURE. .gitattributes can declare `merge=queue` but cannot
# say what `queue` runs — git keeps a driver command out of tracked content on
# purpose. So each clone registers it once, and a clone that has not is NOT
# broken: git falls back to the ordinary text merge, which is what this repo did
# before the driver existed. Say so and move on.
MISSING_DRIVERS=""
for d in queue changelog generated smokestate; do
  [ -z "$(git config "merge.$d.driver" || true)" ] && MISSING_DRIVERS="$MISSING_DRIVERS $d"
done
if [ -n "$MISSING_DRIVERS" ]; then
  printf '\033[33m   note: this clone has not registered the custom merge driver(s):%s\033[0m\n' "$MISSING_DRIVERS"
  printf '\033[33m         those paths will conflict the old way until you run:\033[0m\n'
  printf '\033[33m           bash chicago/4d/tools/setup-merge-drivers.sh\033[0m\n'
  # Worth saying once rather than leaving to be rediscovered: registering
  # `generated` is what stops BOARD.md, tickets.json x2, build.json and
  # walk/index.html conflicting on EVERY merge (T-0831 — five for five on #906).
fi

# Anonymous reconstruction infill is authored as a compact parcel recipe, then
# expanded to ordinary one-file-per-structure records and visibly flagged GLBs.
# Both derivations must stay reproducible without Blender.
step "inferred infill records match the 665-roof programme" \
  python3 tools/generate_inferred_infill.py --check

step "North Division initial parcel matches its reviewed recipe" \
  python3 tools/generate_north_infill.py --check

step "West Division approaches parcel matches its recipe" \
  python3 tools/generate_west_infill.py --check

# T-1773: the West Division's second freight roof, at Lake and West Water. Its own
# generator because the West grid is unscheduled (reconcile_665.py, T-1455) and the
# block parcels cannot deal onto it; the record re-derives from its recipe and the
# validator is proved by breaking it. T-2150 adds the second recipe: the F2 the schedule
# dealt to plat block 50, seated on block 51's West Water corner at Washington Street on
# the policy's `bank_landing` clause, and the validator refuses it beyond that reach.
step "West freight roofs on West Water match their recipes" \
  python3 tools/generate_west_freight.py --check
selftest "…and its validator refuses bad ground" \
  python3 tools/generate_west_freight.py --self-test

# T-2022: the North Division's seventh freight roof, on the North Water bank at LaSalle.
# Its own generator because North Water is graded `light` and the block parcels refuse a
# warehouse there; it stands on the policy's `bank_landing` clause, the record re-derives from
# it, and the validator is proved by breaking it.
step "North freight roof on the North Water bank matches its recipe" \
  python3 tools/generate_north_freight.py --check
selftest "…and its validator refuses bad ground" \
  python3 tools/generate_north_freight.py --self-test

# T-2269: the South street line's owed lumber shed, on the South Branch's east bank south of
# Washington. Off the plat, on the placement policy's `lumber_landing` clause; the record
# re-derives from the recipe, and the validator is proved by breaking it.
step "South Branch lumber shed matches its recipe" \
  python3 tools/generate_south_lumber.py --check
selftest "…and its validator refuses bad ground" \
  python3 tools/generate_south_lumber.py --self-test
# T-2268: two of the South street line's owed freight roofs, on the South Branch's east bank
# between Madison and Washington. Off the plat, because no South Water lot is free and the
# Dearborn reach takes no more; they stand on `bank_landing`, the records re-derive from the
# recipe, and the validator is proved by breaking it.
step "South freight roofs on the South Branch bank match their recipe" \
  python3 tools/generate_south_freight.py --check
selftest "…and its validator refuses bad ground" \
  python3 tools/generate_south_freight.py --self-test

step "Canal approach trade roofs match their bounded recipe" \
  python3 tools/generate_canal_approach_trade.py --check
selftest "Canal trade placement refuses collisions and missing ground" \
  python3 tools/generate_canal_approach_trade.py --self-test
step "Canal trade roofs have existing keepers without invented homes" \
  python3 tools/canal_approach_occupancy.py --check
selftest "Canal trade occupancy preserves identities and lodging constraints" \
  python3 tools/canal_approach_occupancy.py --self-test

# T-1816: the anonymous-roof generators above deal every anonymous roof's finish, paint, roof
# condition and age through ONE rule — whose house it is — and each record says so in
# `reconstruction.fabric_basis`. The rule re-reads every record against itself, and its
# self-test proves no class can deal the Sauganash's white paint or a finish off the sheet.
step "every anonymous roof's finish is the fabric-by-household rule's" \
  python3 tools/fabric_rule_1835.py --check
selftest "…and the rule refuses white paint, off-sheet finishes and drift" \
  python3 tools/fabric_rule_1835.py --self-test

# KINZIE'S ADDITION'S STREET GRID, in two halves for the reason tools/trace_river.py
# is in two halves: the reading's own re-read opens a 5050 x 6628 raster and costs
# about half a minute, which a per-commit gate may not spend. What runs here is the
# cheap half — every metre committed in the trace re-derives from the pixels
# committed beside it, through the committed affine, and the eleven street lines
# re-derive from the module that trace measures. The raster half is
# `--check-sheet` and the PR runs it.
step "Kinzie's Addition's street reading re-derives from its own pixels" \
  python3 tools/read_kinzie_addition_streets.py --check

step "Kinzie's Addition's street lines re-derive from the module they are seated on" \
  python3 tools/seat_kinzie_addition_streets.py --check

# And the numbers in the cells those streets leave. The reading is a table of 52
# figures and a table is a list somebody typed, so this re-derives it twice over: the
# cell boxes come from the street trace above rather than from numbers of their own,
# and the run itself is re-derived from the boustrophedon rule, written independently
# of the table it checks. The raster half is `--check-sheet` and the PR runs it (T-1061).
step "Kinzie's Addition's block numerals re-derive from the reading and the run" \
  python3 tools/read_kinzie_addition_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_kinzie_addition_numerals.py --self-test

# AND THE LOT LINES INSIDE THOSE CELLS (T-1741). Same raster, same registration, same
# cell boxes — what is added is which cells Wright rules into lots and which he leaves
# whole. The reading is what lifted the Addition's blanket `lot_subdivision_withheld`,
# so it is gated at the same strength: every cell re-derives from the committed pixels
# or the cut standing on it is not the cut the sheet draws.
step "Kinzie's Addition's lot lines re-derive from the committed pixels" \
  python3 tools/read_kinzie_addition_lots.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_kinzie_addition_lots.py --self-test

# THE NORTH DIVISION'S SEVEN BLOCK NUMERALS (T-1088). The reading lives in
# data/traces/thompson_block_numbering.json; what is gated here is the CITATION — every
# crop region it cites is re-cut from the committed street lines by the same rule, so a
# street that moves invalidates the crop rather than silently outliving it.
step "the North Division numeral crops re-cut from the committed street lines" \
  python3 tools/read_north_division_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_north_division_numerals.py --self-test

# THE WASHINGTON-MADISON TIER'S SEVEN BLOCK NUMERALS (T-1094), gated for the same reason.
# Three of each box's four sides are a committed line; the fourth pair is the flanking
# north-south lines continued south along their own bearing, because they stop at y = -400.
# The gate re-cuts every box and also checks that each read window still lies inside the box
# it is cited under — block 52's declared overhang included.
step "the Washington-Madison numeral crops re-cut from the committed street lines" \
  python3 tools/read_washington_madison_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_washington_madison_numerals.py --self-test

# THE WEST DIVISION'S EIGHTEEN BLOCK NUMERALS (T-1098, out of T-1095), the last eighteen
# of the fifty-eight and the ones that had no control at all. Four boxes are flanked by
# two committed lines; the six tier lines are committed but clipped at east -320 m and are
# continued WEST along their own bearings; and the two flanks Jefferson and Des Plaines
# would give are `clinton` stepped one and two modules west, because when these eighteen
# numerals were READ both streets stood refused for want of modelled ground. T-1430 has
# since seated them, 8.70 m and 8.22 m from where the step puts them, and the crops still
# come off the step: they are citations of a reading already taken, and re-cutting them
# would re-read eighteen numerals to no purpose. What the seating changes is what the
# agreement MEANS — two instruments agreeing, rather than one licensing the other. The gate re-cuts every box,
# checks every read window still lies inside the box it is cited under, re-measures the
# three agreements that licence the step, and asserts the boustrophedon ACROSS the blocks
# other tickets already read — so a numeral misread here breaks against T-0788's 28 29 and
# T-1094's 52 rather than quietly standing alone.
step "the West Division numeral crops re-cut from the committed street lines" \
  python3 tools/read_west_division_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_west_division_numerals.py --self-test

# AND THE FIGURES INSIDE THOSE BLOCKS, read off the Thompson plat itself (T-0689). T-0444's
# acceptance point 1 asked for the West Division's lot dimensions and lot-counts to be read
# off the sheet rather than carried west from the South Division; #681 answered the rest of
# T-0444, said point 1 was still owed, and the ticket closed without it. The reading is
# `data/traces/thompson_west_division_lots.json` — 22 blocks, 203 lots, every figure citing
# the pixel region of the committed PNG it was read on. The gate holds the reading to that
# sheet's sha256 (a re-scan invalidates all 22 blocks' citations at once), refuses any West
# Division frontage of 80 ft — the South Division's figure, and the exact inference the
# ticket exists to keep out — and asserts THE CLOSURE: 180 + 18 + 180 off the block faces
# and the legend, and 5 x 75 3/5 off a margin, are 378 ft apiece from inputs that share
# nothing, so the block is square and the 458 ft module comes back from figures.
step "the West Division's lot figures still answer for the sheet they were read on" \
  python3 tools/read_west_division_lots.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_west_division_lots.py --self-test

# BLOCKS 14 AND 15, THE LAST TWO OF THE FIFTY-EIGHT (T-1099). They were refused for want of a
# street, and the street was there: Market Street flanks both, and the fourth side is Carroll
# continued east along the bearing of its own committed path. The same correction settles the
# collision T-1098 found — block 7's box took Market's own southern endpoint for its south,
# because block 7 is the one block in its tier with a single flank, and so reached 89 m past
# itself and cited a crop with TWO block numerals in it. The gate re-cuts both boxes, checks
# each read window lies inside the box it is cited under, and asserts directly that neither
# block's numeral lies inside the other's crop.
step "blocks 14 and 15 re-cut from Market Street and Carroll continued east" \
  python3 tools/read_wolf_point_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_wolf_point_numerals.py --self-test

# WABANSIA'S EAST-WEST STREETS, split the same way and for the same reason (T-1068).
# The cheap half re-derives every metre of the seven corridors from the pixels committed
# beside them, through the same NA affine, and re-derives the module and the Kinzie
# cross-check from those metres — so a hand-typed corridor width, a street moved out of
# Wright's north-to-south order, or a corridor centre that has wandered outside the crop
# its name was read in fails here. The raster half is `--check-sheet` and the PR runs it.
step "Wabansia's street reading re-derives from its own pixels" \
  python3 tools/read_wabansia_streets.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_wabansia_streets.py --self-test

# AND THE FIGURES IN THE CELLS THOSE CORRIDORS LEAVE (T-1074). Wabansia's tiers come
# from the street trace above and its COLUMNS are measured by the numeral reading itself,
# because Wright letters no north-south street here. So this re-derives the reading twice
# over, as T-1061 does for the Addition: every cell box is built from the committed
# corridors and column rules rather than typed, and the run 59-79 is re-derived from the
# boustrophedon rule written independently of the table it checks. A hand-typed figure, a
# crop that has left its own cell, a lot divider that has drifted far enough off a block's
# midpoint to be a street, or a closed gap where blocks 55-58 are unaccounted for all fail
# here. The raster half is `--check-sheet` and the PR runs it.
step "Wabansia's block numerals re-derive from the reading and the run" \
  python3 tools/read_wabansia_block_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_wabansia_block_numerals.py --self-test

# AND THE STRIP BETWEEN THAT GRID AND THE WATER (T-1077). The water-lot tract is a wedge,
# not a grid: its lot rules run with the river and its west boundary runs north-south, so
# a rank exists only south of the y where the two have drawn far enough apart for one.
# This re-derives that — every rank's north tip is solved for from the committed rules
# rather than typed — along with the run 1-22 the sheet closes, the two-figure gap it does
# NOT close, the lot module measured independently in three ranks, and the two named
# corridors that cross the strip rather than front the river. A figure guessed into the
# obliterated corner, a rank rule taken off a lot line, a refused figure quietly placed or
# a pinched figure upgraded to `documented` all fail here. The raster half is
# `--check-sheet` and the PR runs it.
step "Wabansia's water-lot strip re-derives from its rules and the run" \
  python3 tools/read_wabansia_water_lots.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_wabansia_water_lots.py --self-test

# AND THE SEATING OF ALL THREE (T-1070). The three readings above are pixel statements
# and each says in its own words that it authors no ground; this is the step that does.
# It re-derives every committed Wabansia street line, and the block grid's outline, from
# those pixels and the committed `kinzie` line — so a hand-nudged endpoint, a corridor
# moved off its rule, a changed corridor width or a street quietly carried east into the
# committed water all fail here. The seating is a translation north and not a fit: no
# control point stands within 900 m of this tract and none is invented.
step "Wabansia's streets re-derive from the readings and the committed Kinzie line" \
  python3 tools/seat_wabansia_streets.py --check

# T-1085, and it is the seam that step above hangs from. `kinzie` is committed off the
# Thompson plat and stops at the town's west line; Wright rules and letters the same
# street across the whole of Wabansia, so the reach west of local east -320 is carried as
# its own record — a different claim about wear, about traffic and about what attests the
# geometry, on the same line. This holds the reach to its two readings AND to the two
# things that would quietly invalidate the seating above: that it still meets `kinzie` at
# the seam, and that it adds no bend to the plat line. A bend there moves platted lot
# lines the whole length of the street and re-scores the corridor-intrusion count, which
# is why the carry is a record beside the line and never a vertex inside it.
step "Kinzie Street's Wabansia reach re-derives, meets the committed line and bends nothing" \
  python3 tools/carry_kinzie_west.py --check

# T-1443, and it is the same argument turned through ninety degrees. `carroll`, `fulton`,
# `lake`, `randolph` and `washington` all stopped at local east -320 — a clip that was
# this reconstruction's own extent and never a claim about the street, as `fulton`'s own
# note said. T-1416 built the field out to east -705 and T-1430 seated `des_plaines`, so
# both reasons are gone and the five are carried to that street. This holds the carry to
# the two things that would quietly invalidate it: that each reach is the committed line
# EXTENDED and not re-fitted — the old west vertex stays on the new line, so no platted
# lot line moves and no corridor is re-cut — and that every metre of it stands on dry
# modelled ground. `fulton`'s two surviving intersections west of the clip are the
# corroboration and they are re-measured here, not quoted.
step "the West Division's five tiers re-derive to Des Plaines, bend nothing and stand on dry ground" \
  python3 tools/carry_west_tiers_west.py --check

# THE KINZIE BLOCK, split the same way and for the same reason. The cheap half
# re-derives the block's ground from the four committed streets, the lot-rule
# counts from the peaks committed beside them, the answer about the modelled
# ground from the committed heightfield meta, and the phrase search over the
# committed research corpus — so a hand-edited count or a page that starts
# saying "Kinzie Block" fails here. The raster half is `--check-sheet`.
step "the Kinzie Block's reading re-derives from its own pixels and the corpus" \
  python3 tools/read_kinzie_block_name.py --check

# THE MICHIGAN ST TRACT north of Kinzie Street, split the same way for the same reason
# (T-0796). The cheap half re-derives every metre, every corridor, both identifications
# and the section arithmetic from the pixels and RGB triples committed beside them,
# through the committed affine — so a hand-edited number, a moved border or a retouched
# swatch fails here. The raster half is `--check-sheet` and the PR runs it.
step "the Michigan St tract's reading re-derives from its own pixels" \
  python3 tools/read_michigan_st_tract.py --check

# ...and the SEATING of that reading (T-1075). The reading is in the sheet's own fit; the
# four street lines and the polygon this project committed are that ladder hung on
# `michigan_north` and `market_north`. Two files hold one statement again, and this one has
# a standing temptation behind it: the seating stands 38.5 m north of where the sheet draws
# the tract, so a later pass that "corrects" a line back toward the drawn position, or
# nudges either datum street for an unrelated reason, would silently detach the tract from
# the argument its own notes go on making. The gate recomputes all of it every run.
step "the Michigan St tract is still seated on the two committed lines it was hung from" \
  python3 tools/seat_michigan_st_tract.py --check

# THE WATER LOTS (T-1063) take BOTH halves here, unlike the street reading above, for
# one measured reason: the re-read costs 2.1 s rather than half a minute. It walks one
# 930-pixel line and scans a twenty-pixel band beside it, where the street reading
# profiles five windows of a million pixels each. A gate that can afford the raster
# should spend it — the cheap half only proves the file is self-consistent, and the
# expensive half is what proves it is still what the sheet says.
step "the water-lot strip's metres re-derive from the pixels committed beside them" \
  python3 tools/read_kinzie_addition_water_lots.py --check

step "…and the strip still reads the same off the sheet" \
  python3 tools/read_kinzie_addition_water_lots.py --check-sheet

# The block parcels are the same shape of derivation with one difference worth the
# extra step: they author no coordinates at all. Every metre comes from the committed
# lot polygons, so a hand-nudged building would show up here as drift rather than as a
# plausible-looking number sitting beside a derived grid.
step "platted block parcels match their recipe and the committed lots" \
  python3 tools/generate_block_infill.py --check

# T-2133 (of T-1684). The cross-street term — a roof fronting its corner lot's SIDE
# street — is dealt by no recipe slot yet, so `--check` above never reaches it. This
# stands synthetic roofs on Dearborn and State and holds them to the lot, corridor and
# bearing gates, then breaks it five ways: an interior lot, a workshop on light State,
# a workshop where Lake outranks Dearborn, a yard building, a street that bounds no face.
selftest "…and a roof can front its corner lot's side street, and every refusal fires" \
  python3 tools/generate_block_infill.py --self-test

# A frontage entry declares the lots its party-line run stands across, and until T-0429
# nothing measured whether it did. That entry's run was anchored on the east end of its
# own strip and packed back west until the roofs ran out, which happened two lots short
# of the west end it had declared — and the declaration is read by three different files
# for three different purposes, so an untrue one is not inert. This re-derives the reach
# of every run in the town off the committed footprints and the committed plat, and the
# three South Water entries it cannot correct without moving a roof are conceded BY NAME
# in the tool with the measurement that found them (T-0449).
step "every frontage run stands across the lots its recipe declares" \
  python3 tools/measure_frontage_declaration.py --check
selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_frontage_declaration.py --self-test

# The note on every unit of a party-line row makes geometric claims — which street, how
# far back, which wall the anchor fixes and where — and the regeneration gate above
# cannot catch a wrong one: it re-derives each record FROM the same template, so a
# template that names the wrong wall re-derives the wrong wall perfectly. T-0189 and
# T-0208 were both found by a person reading the file. This reads the prose and holds
# each claim to the committed footprint and the committed plat (T-0239).
step "every party-line note says what its placement did" \
  python3 tools/check_frontage_notes.py --check
selftest "…and a note naming the wrong wall still fails" \
  python3 tools/check_frontage_notes.py --self-test

# The residents manifest is DERIVED, and now it is gated like one (T-0715). Four
# minting passes and four rewriting passes each rebuilt the SLICE of
# data/residents/index.json they owned and left the rest verbatim, so a household no
# pass owned could be regraded elsewhere and keep a row saying something else for
# ever - and the counts, summed from the rows, inherited the error. Landing #797
# found 18 such households by hand. This re-derives every row and every derived
# count from data/residents/households/*.json and fails if the committed file is not
# what the derivation produces.
#
# T-1144 acceptance 6 put the REDIRECT TABLE under the same rule. `merged` is one
# row per card folded onto another, it is the only way a retired id resolves, and
# it was the one list here nobody re-derived - so it had drifted both ways:
# `hh_vanderbogart_h` (T-0842) had a record and no row, so the id resolved to
# nothing while its own note said the table redirected it, and
# `hh_blanchard_gantry` was carried under `C7` after T-0993 minted `C8` for that
# fold, naming a reader the compound-surname rule for a middle-name argument. Both
# are now derived from data/residents/merged/*.json, and on top of the tally this
# refuses a redirect that does not ARRIVE - a target that is not a live card, a
# person in no card, a redirect onto another retired card, a retired id shadowing a
# live one - because a table can re-derive perfectly and still be a dead end.
step "the residents manifest re-derives from the household cards and the retired records" \
  python3 tools/rebuild_resident_index.py --check

# T-0871. It was the only re-derivation gate in this tree whose own assertions had
# never been shown to fire, and its argument list was read as `"--write" in argv` and
# nothing else - so `--wrtie` typed for `--write` fell through to the compare path,
# printed that the manifest re-derives, wrote nothing and exited 0. The parser refuses
# an unrecognised flag now, and this proves both: every refusal above broken on
# purpose, and the typo answered with a non-zero exit rather than a green check.
selftest "…and its own assertions still fire when broken" \
  python3 tools/rebuild_resident_index.py --self-test

# T-1386. 827 of the 2,269 people this layer carries sat outside the town's population on
# `present_on_scene_date: uncertain` — 276 of them graded `attested` — while 983 of the 984
# the project RECONSTRUCTED were ruled `present`, because the reconstruction stages rule a
# presence as they mint one. The layer believed in the people it made up and was undecided
# about the people it read, and `uncertain` there never meant disputed: it meant nobody had
# adjudicated. Exactly two cards are out on evidence of absence. The ruling puts all 827
# in, one at a time, at the tier each card's OWN dated readings reach — attested where a
# reading covers 1 July 1835, inferred where a source span or a pair of readings brackets
# it, reconstructed where the corpus stops before the day and the standing rule carries it.
# A tier is the whole safety property here (a blanket flip would put an undeclared claim on
# 276 cards), and a tier derived from a card's evidence is only as good as its
# re-derivation, so this is a gate and not a report: the town census, the population
# profile, the order book and the gate screen all count off this file.
step "the presence rulings re-derive from the cards' own dated readings" \
  python3 tools/rule_presence_1835.py --check

selftest "…and every ruling still passes the project's tier contract" \
  python3 tools/rule_presence_1835.py --self-test

# The kinship the corpus already states (T-0734). The audit that opened that ticket
# found 14 of 1,404 people related to anybody at all, and the reason was never that
# the sources were silent: the register marries couples this town holds both halves
# of, and nothing read it. The survey is DERIVED from the corpus, so it grows when a
# reading lands, and this step is what makes that growth impossible to ignore - a
# newly stated kinship whose two ends the town holds is a proposal, and a proposal
# nobody has ruled on is a red build rather than a thing to notice one day.
step "every stated kinship the corpus offers has been ruled on" \
  python3 tools/survey_stated_kin.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/survey_stated_kin.py --self-test

# T-2191. The survey above reads households/ only, so the register's parent ties whose
# other end is a card a BUILD writes whole (a readmission, the register's own
# underdocumented cards) are derived here instead: the generator writes its own row, and
# --land writes the mirror on households/. Both ends from one entry, or neither.
step "the register's parent ties onto generated cards stand on both ends (T-2191)" \
  python3 tools/generated_card_kin.py --check

selftest "…and a duplicate, a two-card far end and a two-word entry still write no tie" \
  python3 tools/generated_card_kin.py --self-test

# The inferred-household layer (K1 phase two) is the same shape of thing: an
# authored recipe — an occupation census, a roof-adoption table and a placement
# list — expanded into households, occupancy blocks and structure records. It also
# re-runs its own placement gates, so a centre that drifts onto another building,
# onto water or off the modelled ground fails here rather than in a bake.
# AND IT IS GATED HERE AT LAST (T-1228), on the part of it the owner kept.
# This slot read as though it were gated until T-0662 found it running a different
# pass under this label, and the programme's own `--check` was then red for a reason
# no run could fix by fixing code: the owner's T-0489 ruling of 2026-09-02 retired
# the reconstructed resident population and kept the geometry, and nothing told the
# generator. It still derives all 101 households — 96 of which the ruling removed —
# so demanding its whole output back was demanding the ruling be reversed once per
# commit. Byte-identity is the wrong contract for a pass that is not the last writer
# of the files it derives, which is what T-0662 found for the letter-list mint too.
# So the contract is FIELD-LEVEL and has two halves, both checked: every field this
# pass still owns re-derives exactly, and every field a ruling or a later ticket took
# off it is asserted to still say what that ruling left — a retired household that
# reappears, or an `occupants` block that stops saying anonymous stock, is red. The
# settlement is authored at
# data/reconstruction/1835_inferred_household_pass_ownership.json.
step "the inferred-household programme re-derives the 38 roofs it still owns" \
  python3 tools/generate_inferred_households.py --check

selftest "…and both halves of that ownership contract fire when broken" \
  python3 tools/inferred_household_ownership.py --self-test

# The naming pass (K18) owns NOTHING in the tree and that is the finding: every
# person it ever named was graded `reconstructed`, so T-0489 took all of them, and
# not one household carries a name_basis block today. Its `--check` used to CRASH
# rather than report — an unhandled FileNotFoundError on one of the 96 removed
# households. It now proves the two properties that are still load-bearing, because
# the other two passes overlay it to derive their own comparisons: the allocation is
# deterministic, and every invented name carries a name_basis graded `reconstructed`
# and may claim nothing better. Then it asserts the retirement itself.
step "the invented names re-deal identically and not one of them stands in the tree" \
  python3 tools/generate_inferred_names.py --check

# T-0838 (of T-0814). The step above re-derives the population IN MEMORY and checks its invariants;
# it never asks whether that derivation matches the cards on disk, and on 2026-09-05 it
# reported `OK: 1404 people` while the writer stood 132 household files from the tree,
# with T-0509's eight corroborations sitting in the gap. This is the missing half — the
# same re-derivation contract datum.json and the baked GLBs are held to, run against a
# throwaway copy of the tree so it cannot touch the real one. It is a RATCHET over the
# drift standing on 2026-09-05: undeclared drift fails, and drift that heals has to
# shrink the baseline in the commit that heals it. T-0837 owns spending what is standing.
step "the resident synthesizer has not drifted further from the cards it writes" \
  python3 tools/synthesize_resident_research.py --drift

selftest "…and that ratchet fires in both directions" \
  python3 tools/synthesize_resident_research.py --drift-self-test

# T-1232. The 94 research blocks whose identity this project asserted held dated arrivals,
# origins, marriages, deaths and expansions of initials in PROSE, beside structured fields
# that read "Not attested." `tools/spend_person_facts.py` turns every candidate in every
# research block into an adjudicated row and writes only the asserted ones onto the records.
# `--check` holds the table against the readings AND the records against the table, in both
# directions, so a hand-edited card and a lost row are the same red line.
step "the person-fact table and the facts it spent agree with the records" \
  python3 tools/spend_person_facts.py --check

# The adjudication rules, each mutated into the failure it exists to catch: a later volume
# promoted, an out-of-town fact asserted as a Chicago arrival, a reading graded
# `reconstructed`, a value the record already holds asserted twice.
selftest "…and every one of those rules bites when it is broken" \
  python3 tools/spend_person_facts.py --self-test

step "inferred placeholder GLBs match their records" \
  python3 generators/inferred_placeholder.py --check

# The renderer-track fixture. It is the only asset in the tree whose job is to be
# the thing the confidence view is TESTED against, so it has to carry all three
# levels on real vertices — and it stopped doing that when the record grew a mass
# the placeholder did not model. T-1112 owns the repair; this is the gate that
# keeps it repaired, and it also re-checks the sidecar against the record.
step "the confidence fixture carries all three levels, and agrees with its record" \
  python3 generators/placeholder.py --check

# The clapboard stock, both halves of it. The named deal re-derives its own 24 records
# (T-0049) — that half was never gated, so a hand-edited board width would have sat in
# the tree looking exactly like a dealt one. The recipes deal the other 131 and their
# own --check above holds those values byte for byte, but a recipe that stopped dealing
# ALTOGETHER would pass every one of those checks: a record with no siding_exposure_m is
# a perfectly well-formed record. It just puts 131 walls back on one course, invisibly,
# which is the defect T-0112 closed. So this asks the town-wide question instead.
step "every clapboard wall's stock re-derives from its deal" \
  python3 tools/deal_siding_stock.py --check

# The platted block and lot grid is generated from the Thompson module and the
# committed street lines, never traced off the 1834 sheets. Re-deriving it here is
# what keeps it a derivation: a hand-nudged block face would otherwise sit in the
# repo looking exactly like a surveyed one.
step "the platted block and lot grid re-derives from the module" \
  python3 tools/generate_plat_lots.py --check

# And the grid's own refusals still fire. The one that matters is the youngest: four
# crossings can be found and still describe no block, because two committed centrelines
# can converge to less than a corridor apart before they get there. Measured 2026-08-29
# by T-0183 on the closure the owner ruled for at Market x South Water, which emitted a
# 4,411 m2 bowtie with a plausible depth rather than refusing.
selftest "…and a block whose rows have crossed is refused rather than emitted" \
  python3 tools/generate_plat_lots.py --self-test

# T-1479. Two cells stand in both plat grids — blk_lake_clinton (plat block 28) and
# blk_randolph_clinton (block 45), between Clinton and Canal, which is West Division
# ground already emitted by the Original Town's grid on the SOUTH Division module. The
# sheet counts TEN lot numerals in each, two columns by five rows; the layer cuts EIGHT,
# four to a face. That gap is a ticket, and what this pair gates is the REFUSAL that
# keeps it open, so the refusal cannot quietly stop being true. Nothing moves: the tool
# writes numbers, exactly as measure_west_division_module.py did for T-0444.
# The assertions worth naming: both halves of the module refusal must BIND — the two
# 180 ft lot columns alone must not fit the committed face, and the depth must not
# divide into five whole lots of the printed frontage — because if either stopped
# holding, the re-cut would be derivable and this gate would be guarding a stale no.
# The seating is gated too (17 structures and 46 rows across 13 lots), since a withheld
# re-cut strands exactly that and a count which fell to nothing would make the move
# cheap. And the last one is the sharpest: NO withheld block anywhere in town may carry
# a seating. That is what makes the ticket's own first question — what a structure on a
# withdrawn lot is seated on — genuinely unanswered rather than answered somewhere this
# ticket failed to look.
step "the West Division re-cut of blocks 28 and 45 is still refused by the committed lines" \
  python3 tools/measure_west_grid_migration.py --check

selftest "…and both halves of that refusal, the seating it would strand and the unanswered first question still fire" \
  python3 tools/measure_west_grid_migration.py --self-test

# T-1540. The precondition BEHIND that refusal, which for three days pointed a reader at
# a ticket already done: Clinton to Canal stands at 367.9 ft against the plat's 458 ft,
# T-0444 reported it and T-0445 closed without moving a centreline. The owner ruled on
# 2026-09-21 that the successor must own the whole question rather than the one number —
# so this pair gates the WHOLE question. What is worth naming: the gap is on every
# interval of the West Division grid, not on Clinton to Canal alone, and the assertion
# that carries the finding is a COUNT rather than a metric — three intervals are short
# and a centreline moved reaches two, so no single street move closes it, and that
# holds whatever the datum residual is. The residual is gated both ways on purpose: at
# least one interval must be short by more than 17.5 m (or the whole gap is inside the
# georeferencing and there is nothing to repair) and at least one must sit inside it (or
# the measurement is not discriminating and any interval could be called a defect). And
# the sharpest one is the quotation: the sheet reading must still say `documented` "does
# not grade any position", because that sentence is the only reason the plat cannot be a
# position control — the day it changes, "the plat wins" becomes a move this project
# could actually make, and the ruling in this file has to be rewritten rather than reused.
step "the West Division's north-south lines are still seated on the survey, not on the plat's module" \
  python3 tools/measure_west_division_spacing.py --check

selftest "…and the gap on every interval, the datum test cutting both ways, the count no residual touches and both anchors' price still fire" \
  python3 tools/measure_west_division_spacing.py --self-test

# The band the two halves of that plat leave between them (T-0419). Since the owner ruled
# on 2026-08-29 that a corridor is derived from the street CONTROL, south_water's corridor
# stands 8.58 m north of block faces still offset from the DRAWN line, and 6,132 m2 of
# ground belongs to neither. Which of the two is wrong is the owner's question; this gate
# does not answer it. It pins the figures the question is asked ABOUT, so the fork cannot
# drift under him while it waits — and it has already caught that drift once: between the
# 2026-08-30 measurement and 2026-09-13 the shore work moved the claimed band's dry share
# 47.6 -> 46.0 %, and ordinary building took branch A's price from 43 roofs to 53.
step "the band between the re-centred corridor and its block faces is what T-0419 measured" \
  python3 tools/measure_corridor_strip.py --gate

selftest "…and that measurement's own assertions still fire when broken" \
  python3 tools/measure_corridor_strip.py --self-test

# AND THE RULING THAT CLOSED IT (T-0419, the owner, 2026-09-21): the block grid is NOT
# re-cut onto the control, the two lines are answers to two different questions, and EVERY
# READER SAYS WHICH IT TOOK. That is the substance of the ruling and the only part of it
# that is enforceable — the fault the ticket found was not a wrong line but a reader that
# never said, so nobody could tell whether its number was about the plat or about the town.
# The check reads the SYNTAX TREE and not the text, because every one of these modules
# discusses both lines at length in its prose and a grep for `from_control` reports almost
# all of them as control readers. `docs/CORRIDOR-LINES.md` is the ruling, the disagreement
# the owner declined to resolve, and the price branch A was refused at.
step "every reader of the platted grid says which of its two lines its answer stands on" \
  python3 tools/check_corridor_line.py --gate

selftest "…and the declaration is checked against the calls, in the tree and not in the prose" \
  python3 tools/check_corridor_line.py --self-test

# T-1812. The graded street section: the 1835 ground lowers every opened street's worked
# roadway below the shelf its walks and doors stand on. The painted width (streets.js
# WORKED_SHARE) and the graded width (the spec's worked_share) are one number in two
# files, and the committed heightfield has to carry the cut — both read here.
step "every opened street's bed lies below its walks, as wide as the road is painted (T-1812)" \
  python3 tools/check_street_section.py --gate

# T-0875. The School Section's 142 block numerals, read off the 600-dpi NA sheet.
# It sits beside the Thompson grid because it is the same question answered the
# other way round: there, two legible numerals could not say how a run passes from
# one tier to the next and the numbering is refused past one tier; here the whole
# grid is legible and the boustrophedon is observed, not argued. The trace is
# GENERATED from the reading table and the committed registration, so `--check` is
# what keeps a hand-edited numeral out — and the assertion that earns its keep is
# the one that re-derives 120 of the 142 from the scheme alone, written
# independently of the table it checks.
step "the School Section's block numerals re-derive from the reading and the scheme" \
  python3 tools/read_school_section_numerals.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_school_section_numerals.py --self-test

# The grid those numerals sit on had no gate at all, which is how its writer came to be
# silently destructive for weeks: `splice()` rewrote each target file from its own first
# record to the end, so re-running it deleted the twenty-two streets appended after its own.
# T-0877 and T-0959 found that independently the same morning and T-0877's fix is the one in
# force. Nothing NOTICED it because nothing re-ran the generator. This does (T-0959).
step "the School Section's block grid, streets and reservations re-derive" \
  python3 tools/generate_school_section_grid.py --check

# The dooryard garden pickets are the first record on the enclosure layer whose evidence
# is a TREATMENT and not a place — the Kinzie-view plate shows picket-fenced garden plots
# and no source puts a garden on any lot in this town. So the answer to "why this lot" is
# a RULE, and a rule that is not re-derived is a list somebody typed: this re-runs it
# against the committed lots, footprints, functions and households (ROADMAP K5 (a), T-0052).
step "the dooryard garden pickets re-derive from the rule that chose their lots" \
  python3 tools/generate_dooryard_pickets.py --check

# The lot-line yard fences are the same shape of claim at town scale: the owner asked for
# more fences, image 12 of his brief shows an 1830s town where every property is enclosed,
# and no source names a fence on any lot in Chicago. So WHICH lots and WHICH fence is a
# rule again — the committed plat for the lines, the committed footprints for where the
# yard begins, and the street records' own traffic classes for the type — re-derived here
# so kilometres of fence stay auditable rather than several hundred typed numbers (T-0068).
step "the lot-line yard fences re-derive from the rule that chose their lots and types" \
  python3 tools/generate_lot_line_fences.py --check

# And every one of those runs can now say WHOSE ground it stands on (T-0637). The join is a
# derivation off the committed lots, the committed footprints and the committed household
# index, so it is worth nothing unless it stays derivable and stays truthful about what it
# could not answer: this asks that every run on the whole layer names an owner or records a
# refusal, that no belongs_to names a structure or a household this repository does not
# hold, and that the two hand-authored yards keep the owners somebody read out of a source.
step "every enclosure run says whose ground it stands on, or records why it cannot" \
  python3 tools/check_enclosure_owners.py

# The dooryard plantings are the same shape one layer greener: the owner's brief and its
# image 12 attest a TREATMENT — trees and bushes kept close around the houses — and no
# source counts or places any particular house's stems. So which house keeps what is a
# RULE over the committed dwellings, streets, fences and ground, re-derived here so the
# 125 stems stay auditable rather than 125 numbers somebody typed (T-0074).
step "the dooryard plantings re-derive from the rule that dealt their stems" \
  python3 tools/generate_dooryard_plantings.py --check

# The settled town's ground is DERIVED, not drawn (T-2084): every plat block, every
# standing footprint and the forks seed, grown by the dossier's 50 m grazed halo, with
# the beach and the public square's slough held out. A hand edit of the polygon, or a
# district built without re-running the tool, leaves its houses standing in prairie —
# which is what the owner walked through on 2026-10-04 — and this refuses both.
step "the settled town's ground re-derives from the plat and every standing roof (T-2084)" \
  python3 tools/derive_settled_town_extent.py --check

# And the planted rows are the same shape again, on the one flora treatment this project
# has in WORDS rather than in pictures: Wau-Bun states "a broad green space was inclosed
# between it and the river, and shaded by a row of Lombardy poplars", at a house that is
# excluded from this scene. Seven committed plates draw that row and five agree on four
# stems at 0.195 of their own height apart; not one of them shows a poplar anywhere else
# in Chicago. So the treatment is the source's, the count and the rhythm are measured,
# and WHICH GROUND GETS ONE is a rule over the committed dwellings — re-derived here so
# the twelve stems and the refusal beside them stay auditable (T-0117).
step "the planted poplar rows re-derive from the rule that chose their greens" \
  python3 tools/generate_planted_rows.py --check

# Robert G. Clarke's 1835 shore grove, "perhaps fifty to seventy-five large cottonwoods"
# from a little north of Sixteenth to a little south of Eighteenth Street, with its
# clump of eight or nine on Wirt Dexter's lot end. The count, the strip's depth and every
# stem's place but the clump's are a rule's, re-derived here (T-2766,
# L-shore-grove-1835-2766).
step "the 1835 shore cottonwood grove re-derives from the rule that dealt it" \
  python3 tools/generate_shore_grove_1835.py --check

# The same grove in 1812, twenty-three years younger: the 1835 record's positions at
# half its heights as z08's dune cottonwood (T-2745, L-woods-1812-2745).
step "the 1812 shore cottonwoods re-derive from the 1835 grove" \
  python3 tools/generate_shore_grove_1812.py --check

# The fort's company gardens and Dr. Harmon's orchard (Wau-Bun, 1831): which fruit,
# how many and where are a rule's, re-derived here (T-2809, L-fruit-trees-1835-2809).
step "the 1835 company-garden and Harmon orchard plantings re-derive from their rule" \
  python3 tools/generate_fruit_plantings_1835.py --check

# The business signboards are the same shape of claim one layer over: exactly one record
# in this dataset ATTESTS a sign, and the boards on the other two dozen frontages are a
# reconstruction chosen by a rule about trades rather than a list of shops somebody liked.
# Re-derived here against the committed sidecars, so the rule stays the answer to "why
# this frontage" (ROADMAP K5 (b), T-0039).
step "the business signboards re-derive from the rule that chose their frontages" \
  python3 tools/generate_business_signboards.py --check

# ...AND THE RULE IS LOCAL (T-0405). "Re-derives" only says the committed file matches the
# rule; it says nothing about how far one frontage reaches. Until T-0405 the mounting was
# dealt from a counter walked down the town in id order, so admitting one frontage in the
# middle of the alphabet re-dealt every frontage after it — 103 of 109 consequences landed
# outside the 40 m the rule is about, the furthest 1,163 m off, and because the mounting
# decides how many lines a board has room for, some of them changed what the board SAID.
# This withholds each board in turn, re-derives the town without it, and holds every
# consequence against the distance from the board withheld. ~4 s.
step "admitting one signboard reaches no board further off than the rule's own 40 m" \
  python3 tools/generate_business_signboards.py --prove-locality

# ...AND AN INVENTED FIRM'S BOARD NEVER MOVES AN EVIDENCED ONE (T-1834). Reconstructed
# firms the business layer records IN a reconstructed roof now take a board, dealt after
# every named frontage; this re-derives the town without them and holds every evidenced
# board byte-identical. ~2 s.
step "a reconstructed firm's signboard moves no board the evidence carries" \
  python3 tools/generate_business_signboards.py --prove-recon-yields
# ...AND A REGISTER FIRM THE STREET-FACE ADOPTION HOUSES MOVES NO BOARD ALREADY HUNG
# (T-1835). Those boards are dealt last; this re-derives without them and holds the rest
# byte-identical. ~2 s.
step "an adopted register firm's signboard moves no board already hung" \
  python3 tools/generate_business_signboards.py --prove-adopted-yields

# The yard goods are the third record of this shape and the first whose evidence is an
# ORDINANCE: the village corporation legislated in November 1833 about timber, stone,
# brick, boxes and barrels stacked in the streets, which attests the treatment and not one
# location. So "which frontage gets goods" is a rule again, re-derived here against the
# committed sidecars and the wagon-yard perimeter (ROADMAP K5 (c), T-0040).
step "the yard goods re-derive from the rule that chose their frontages" \
  python3 tools/generate_yard_goods.py --check
# T-1984. EVERY DOOR, ONCE, AND NOTHING IN FRONT OF IT. The owner, walking Lake Street on
# 2026-10-02, found goods in front of doors, a sign on a door leaf, a window run into a door
# and prairie up to every threshold. `generate_entrances` reads each door off the front
# elevation its mesh is built from, re-derives the trodden apron in front of it, and
# refuses any front whose holes run together; `measure_doorways` holds every placed object
# in the town — goods, carts, posts, fittings, fences, sign posts, wells, planted stems —
# out of every doorway.
step "every door is read once, its apron re-derives, and no two holes on a front run together (T-1984)" \
  python3 tools/generate_entrances.py --check
step "nothing placed in the town stands in a doorway (T-1984)" \
  python3 tools/measure_doorways.py --gate
# T-2095. THE ALLEYS ARE LANES. The plat model's mid-block alley strip, on every block a
# structure stands on, laid in the road's dirt and carried to the cross street's track —
# re-derived here, and refused if a ring winds clockwise (yards.js culls it unseen).
step "the alley lanes re-derive from the plat's strips and the blocks built on (T-2095)" \
  python3 tools/generate_alley_lanes.py --check
# The yard outbuildings (T-1960) are the same shape again: a privy in a rear corner of every
# dwelling lot the plat reaches and a stable for the horse-keeping households, dealt from the
# lot survey the fences read and the house's own class and age — a rule, so re-derived here.
step "the yard outbuildings re-derive from the rule that dealt them by household" \
  python3 tools/generate_yard_outbuildings.py --check
# The kept ground (T-2086) reads those outbuildings: per improved lot, the kept ring where the
# forb layer stands back, the refuges at the foot of each outbuilding and the worn paths to
# them — which ground is kept is a rule, so it is re-derived here.
step "the kept yards, their refuges and their worn paths re-derive from the lot survey (T-2086)" \
  python3 tools/generate_kept_ground.py --check
# And the lots with no building on them (T-2101): grazed prairie remnant, a flora community
# whose extent is every vacant platted lot and whose species are the prairie's and the town's
# own under a stated crop — derived, so a district built later takes its lots out by re-running.
step "the vacant lots' grazed prairie remnant re-derives from the plat and the lot survey (T-2101)" \
  python3 tools/derive_lot_remnant.py --check

# And the OTHER HALF of that ordinance, which the goods record refused in writing:
# timber, stone and brick are building material on a lot that is going up, not a
# trader's stock on his own frontage. The rule's load-bearing clause is that the
# structure record has to STATE the construction state itself — a date test would read
# a first-attestation year as a groundbreaking and deal stacks of brick to buildings
# that had stood for a year — so exactly one lot in this scene qualifies, and this
# re-derives which one and where the piles stand (T-0057).
step "the building material re-derives from the rule that chose the lots" \
  python3 tools/generate_lot_building_material.py --check

# The working trades' yards (T-1961, piece 4 of T-1212): casks at the cooperages and
# packers, boards at the joiners', hides at the tannery, hay ricks at the stables outside
# the 1835 hay limits, wagons at the forwarders and the teamster's yard. Re-derived from
# the sidecars, the committed ground and the other yard records, so where each stands
# stays a rule.
step "the trade yards re-derive from the rule that dealt them" \
  python3 tools/generate_trade_yards.py --check

# A woodpile at every dwelling, by whose house it is (T-1959): the yard-by-household rule
# in tools/yard_rule_1835.py (printed in the placement policy under `yard`) says what
# each household kept — a slab heap, a log heap, stove ricks, bought cords — and where
# it stands is arithmetic on the house's own back wall. Re-derived here byte for byte,
# and the rule's own guarantees proved by breaking them.
step "the woodpiles re-derive from the yard-by-household rule" \
  python3 tools/generate_woodpiles.py --check
selftest "…and the yard-by-household rule's guarantees fire when broken" \
  python3 tools/yard_rule_1835.py --self-test

# Nothing stands inside a building (T-3078). The owner, 2026-10-23, of two shops grown
# into one another at Lake and Canal with a rail fence running into them: "make sure this
# does not happen again". Every tool above tests what it places against what IT knows
# about; this asks once, across layers and scenes, of the shapes the renderer draws — no
# building inside another past a party wall, no fence, walk or palisade through a
# building, no yard prop with its middle in a room, in 1812, 1835 and 1904. The four
# ways it was found broken are its self-test, the counter-clockwise footprint included.
step "no building, fence, walk or yard prop stands inside a building, in any scene (T-3078)" \
  python3 tools/check_structure_clearance.py
selftest "…and two shops on one corner, a fence through a turned house, a woodpile in a room and a stale ruling are each refused" \
  python3 tools/check_structure_clearance.py --self-test

# The fort apron is the same shape of claim about GROUND rather than about things standing
# on it: both committed Fort Dearborn plates draw the ground round the stockade as bare
# trodden earth, no source states a foot of it, and the render grew prairie to the pickets.
# So "how far out is it bare" is a rule, derived from the palisade's own committed footprint
# and placement, and re-derived here — along with the four assertions the rule has to be true
# for, which fail this gate rather than a reviewer's attention (T-0097).
step "the fort apron re-derives from the palisade it is measured off" \
  python3 tools/generate_fort_apron.py --check

# And the layer above that ground: the wood p4_0 draws outside the same walls (T-0098). Same
# shape again — the plate attests a tree mass and places nothing, so which ground carries a
# stem is a rule off the palisade's own footprint and its apron's own width, re-derived here.
# The rule also picks the SPECIES rather than a preference: of the zone's three recorded
# trees only one is banded low enough to carry the crown height measured off the plate, and
# a re-banded zone record must therefore fail this gate rather than quietly plant a
# cottonwood that would tower over the fort the plate draws it level with.
step "the fort wood re-derives from the palisade and the apron it stands off" \
  python3 tools/generate_fort_trees.py --check

# T-0008 took every chimney in the town off the ROOF material — R-W2a finding 1, a stack
# painted whatever weathering condition its own roof was dealt — and nothing measured the
# result, so it left ten stacks behind for four months: `fort_structure` was excluded
# deliberately (1816, before the town had a brick-yard) and the exclusion outlived the
# reason for it, which T-0137 answered off the fort's own attested brick. This gate is what
# stops that class of miss recurring, and it is stated on the BYTES rather than on any
# generator: a stack has to clear the roof to draw at all, so a building whose record counts
# a chimney and whose highest geometry IS the roof material has its stack inside the roof's
# own primitive. It reads the committed masters' accessor bounds and decodes no mesh.
step "no stack in the town is painted the colour of the roof it passes through" \
  python3 tools/measure_stack_fabric.py --gate --quiet

# Its neighbour, on the same accessor bounds and the same principle (T-0333). The Town of
# Chicago's by-law of 5 August 1835 section 18 — chicago_democrat_1835_08_19#c005 — carries
# every stove pipe or chimney "at least eighteen inches above the roof" under a five-dollar
# penalty, which is the first documented DIMENSIONAL constraint this project holds on
# anything above a roof line. Every stack in the town already clears it; this is the ratchet
# that stops one dropping back under. It does NOT decide which buildings the by-law reaches:
# section 22's corporation limits are T-0334's and are not drawn yet, and nothing here is
# conformed to a rule that may not bind it, because nothing has to move. SINCE T-0436 it
# also REPORTS the reach: the corporate boundary is committed, eight of the chimneyed
# buildings stand outside it, and section 18 never bound one of them. (The line is the
# Trustees' own of 7 November 1833 — NOT section 22, which draws the narrower
# hay-stacking boundary and is T-0334's.)
step "every stack is carried eighteen inches above its roof, as the by-law of 5 August 1835 requires" \
  python3 tools/measure_stack_ordinance.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_stack_ordinance.py --self-test

# The river wharves are the fourth record of this shape and the first whose rule
# reads a record's OWN attribute rather than a trade table: a sidecar standing on
# the scene date whose `dock` is true and graded attested or inferred. Two
# records in this town qualify and both state their dock in the same sentence of
# the same dossier; every other river frontage is refused by the same clause. The
# outline is derived from the traced bank, the committed footprint and the
# committed heightfield, so a re-traced bank or a moved warehouse must move the
# wharf with it or fail here (ROADMAP K5 (e), T-0041).
step "the river wharves re-derive from the records that state a dock" \
  python3 tools/generate_river_wharves.py --check

# The landing-place camps (T-1803) are placed against the drawn South Water line, the
# traced bank, the heightfield and every committed obstacle on the bank, so a moved
# deck, walk, boat or footprint must move a camp with it or fail here.
step "the landing-place camps re-derive from the bank they stand on" \
  python3 tools/place_landing_camps_1835.py --check

# The camps of the two conjectural grounds (T-1804) — the land-sale crowd on the
# reservation shore and a wagon party at the west approach — are placed against every
# drawn roadway, fence run, footprint, refused region and the heightfield, so anything
# built or drawn into their ground must move a camp with it or fail here.
step "the shore and west-approach camps re-derive from the ground they stand on" \
  python3 tools/place_camp_grounds_1835.py --check

# ROADMAP K5 (e) also asked for "a river-wharf mode of pier_crib", so that a town
# assembled from GLBs alone would carry its docks; T-0059 was that clause and was
# WITHDRAWN on 2026-08-27 on the three readings this holds. Not on an opinion about
# wharves: on the count of renderers that could read such a GLB (one, and it draws
# the wharves already), on the count of drawn-at-load layers that owe a generator
# half (nine of nine, so the debt is general and the wharf is not special), and on
# what each route into the bake re-stales. The last of those cuts BOTH ways and the
# gate states it either way — a mode inside pier_crib.py costs two meshes, which is
# cheap, while a new archetype edits build.py's registry and costs the town. The
# reading is gated rather than remembered because every figure in it is a thing the
# tree can change underneath the decision: a second renderer, a tenth layer, or the
# first drawn layer to grow a generator each fail here and send somebody back to the
# ticket.
step "the case T-0059 was withdrawn on still holds" \
  python3 tools/measure_generator_half.py --gate --quiet

# T-1654, and the sentence directly above is what pays for it: "a new archetype edits
# build.py's registry and costs the town". So did an argparse fix — 422 of 422 assets,
# for a change that could not move a vertex, because mesh_inputs.py hashed build.py
# WHOLE. The pipeline now lives in generators/emit.py, which the recipe hashes, and
# build.py kept the command line, which it does not. That split is an allowlist by
# construction, and code_inputs.py is the standing argument that an allowlist silently
# drops the next thing somebody adds — so it is asserted here on every run rather than
# trusted: an archetype import, a shared builder import, or any reach into bpy beyond
# bpy.app puts geometry back where the staleness gate cannot see it.
step "the bake's command-line half still makes no geometry" \
  python3 tools/test_build_cli_has_no_geometry.py

selftest "…and each way of breaking that split is still refused" \
  python3 tools/test_build_cli_has_no_geometry.py --self-test

# The frontage works are the fifth record of this shape and the first derived from
# a building AND a street at once: where a plank walk may lie is decided by the
# travelled track's own half-width out of data/streets/1835.json, not by the wall
# alone. Re-derived here for the same reason as the four above — "which wall gets a
# walk" is a rule, and a rule that is not re-run is a rule nobody is keeping (T-0082).
step "the frontage works re-derive from the rule that chose their walls" \
  python3 tools/generate_frontage_works.py --check

# AND THE HALF OF THAT RULE NO RECORD EXERCISES. A cross street bounds a block on
# its EAST and WEST faces; every street this record carries today bounds one on the
# north and south. T-0192 enumerated all four and made every ordering in that
# generator axis-aware, then measured the seven cross streets over all three
# scene-detail ceilings and left them out — so the east/west path ships with an
# empty covered tuple and the re-derivation above cannot touch it. This drives it
# over all seven, in hundredths of a second, so it is code somebody is keeping
# rather than code waiting to rot until the frame budget is won back.
# The freight shed's cargo openings, and specifically the thing no other gate can
# see: THREE callers have to agree about where they are. The builder frames them,
# `openings()` cuts them out of the boarding and tells the signboard generator where
# a board may not hang, and the validator refuses a count the wall cannot carry. They
# agree by all reading one set-out; if any of them ever computes its own, the frames
# land on solid board beside rectangular holes and the mesh is still perfectly valid.
# It also holds the reading the family was re-doored on: a wagon door clamped F1's
# eave FLOOR 32 mm above the bottom of the 10-13 ft band its own crosswalk authors.
step "the freight shed's cargo openings set out once and are read three times" \
  python3 tools/test_outbuilding_cargo.py

selftest "…and that agreement still fires when the frames drift off the holes" \
  python3 tools/test_outbuilding_cargo.py --self-test

# T-2376/T-2383/T-2385: pictured frame controls on the real accumulator.
check_summary
