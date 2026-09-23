#!/usr/bin/env bash
# The per-commit gate. Seconds, no Blender, runs in every agent sandbox.
#
# A gate that takes four minutes gets skipped, so this one deliberately does not
# build geometry. Content builds live in tools/bake.sh and run on demand.
#
#   tools/check.sh            the gate
#   tools/check.sh --strict   warnings are errors (used before a release)
set -uo pipefail
_check_tools="$(cd "$(dirname "$0")" && pwd)"
cd "$_check_tools/.."

STRICT=""
[ "${1:-}" = "--strict" ] && STRICT="--strict"

# The step harness — `step`, `selftest` and the end-of-run roll-up — lives in its own
# file so that tools/test_check_harness.sh can source and exercise it (T-0763).
source "$_check_tools/check_harness.sh"

step "Boot phase readiness, failure and history contract (T-1246)" \
  node tools/test_boot_phases.mjs

# THE MIRROR IS BUILT FIRST, BECAUSE IT IS NOT IN THE REPOSITORY ANY MORE (T-0938).
#
# `site/chicago/4d/` used to be committed, so every step below could assume it was
# simply there — and `check_published.mjs` ran under an `if [ -d ]` guard that made a
# fresh checkout skip the gate silently. It is untracked and .gitignored now (see
# /.gitignore for the measurement), which turns that assumption into an absence: a
# clone has no mirror at all until something publishes one.
#
# So the gate publishes one, here, before anything reads it. That is not a workaround;
# it is the honest reading of what check_published.mjs asserts. The claim was never
# "the mirror somebody committed matches its source" — it was "what publish.sh produces
# matches its source", and with the mirror off the PR surface that is the only reading
# left. Everything downstream now measures a mirror this run made, so a stale one is
# not a state that can exist.
#
# It costs about a second (measured: 1.0 s on a warm tree), and it is a REAL publish
# rather than a `--dry-run`, so publish.sh's own refusals — a derivative that no longer
# answers for its master — fail the gate here rather than at deploy time.
step "publish the mirror the gate measures (site/chicago/4d/ is generated, T-0938)" \
  bash tools/publish.sh

# THE ONE ORDERING THIS GATE HAS, and under CHECK_JOBS>1 it has to be said out loud.
# Everything below reads the mirror the step above writes, so the pool may not start
# any of it until that publish has finished. `check_flush` is the barrier: it drains
# what is queued and returns, and it is a no-op on the serial path.
check_flush

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

step "dataset (schema, provenance, date gates, licenses, staleness, publish)" \
  python3 tools/validate.py --all $STRICT

step "validator self-tests" \
  python3 tools/test_validate.py

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
step "no committed list carries the same id twice" \
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

# The yard goods are the third record of this shape and the first whose evidence is an
# ORDINANCE: the village corporation legislated in November 1833 about timber, stone,
# brick, boxes and barrels stacked in the streets, which attests the treatment and not one
# location. So "which frontage gets goods" is a rule again, re-derived here against the
# committed sidecars and the wagon-yard perimeter (ROADMAP K5 (c), T-0040).
step "the yard goods re-derive from the rule that chose their frontages" \
  python3 tools/generate_yard_goods.py --check

# And the OTHER HALF of that ordinance, which the goods record refused in writing:
# timber, stone and brick are building material on a lot that is going up, not a
# trader's stock on his own frontage. The rule's load-bearing clause is that the
# structure record has to STATE the construction state itself — a date test would read
# a first-attestation year as a groundbreaking and deal stacks of brick to buildings
# that had stood for a year — so exactly one lot in this scene qualifies, and this
# re-derives which one and where the piles stand (T-0057).
step "the building material re-derives from the rule that chose the lots" \
  python3 tools/generate_lot_building_material.py --check

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
step "the street edge's cross-street faces enumerate as the plat says" \
  python3 tools/test_frontage_faces.py

selftest "…and those assertions still fire when the enumeration is broken" \
  python3 tools/test_frontage_faces.py --self-test

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

# T-1482, and the step that says why the last six of the 32 refamily verdicts are still
# outstanding. The two migrations above carried 20 of them out; these six are yard
# buildings standing off a block alley behind the principal roof on their own lot, and
# the adjudication moves every one into a dwelling family. `generate_block_infill` reads
# a roof's inventory class from its group, so that promotion makes each one a SECOND
# principal roof on an occupied lot, which the parcel gate refuses and the committed
# `multi_building_lot` rule admits only on a principal-street lot in a party-line run.
# A report that could be read as "somebody forgot" is the failure this guards against:
# it holds the refusal, the 36 offered families that all land in the same class, the two
# open lots the three blocks have between them, and the clause's own evidence — three of
# whose four documented stables stand exactly where the six were refused for standing.
step "the platted blocks' six outstanding verdicts still have nowhere to be carried to" \
  python3 tools/measure_block_redeal_remedies.py --check

selftest "…and it would say so the moment a re-deal had somewhere to go" \
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

# The two numbers on the FRONT screen (T-0036): buildings standing and people housed.
# Both are reads of the roof programme and the residents layer, and the most visible
# possible place to carry a stale number is the panel a visitor sees before anything
# else. Re-derived here so a run that builds ten roofs and forgets to regenerate the
# census fails at the commit rather than shipping a town that says it is smaller than
# it is. Also refuses a household whose `lives_at` names a structure the scene does not
# carry, which would silently drop people out of the count.
step "the gate's town census re-derives from the roofs and the residents" \
  python3 tools/town_census.py --check

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
# from the committed tree on every run, which is what --check compares. Five assertions:
# no clause cites a record this tree does not hold; a `documented` clause has evidence
# and an inferred one has its reasoning; every outlier is explained AND every explanation
# still has its outlier; no family letter is left without a seat rule; and no module has
# taken its own copy of a shared constant back. No roof moves — this reads.
step "the placement policy still re-derives, and nothing re-typed its constants" \
  python3 tools/placement_policy_1835.py --check --quiet

selftest "…and its five assertions still fire when broken" \
  python3 tools/placement_policy_1835.py --self-test

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

# The ticket queue: the operational "what next" the owner ordered on 2026-08-17
# after his own requests went untraceable in the ROADMAP. Duplicate ids, queue
# drift, a stale BOARD, a block with no stated question — all merge-refusing.
step "ticket queue" \
  node tools/ticket.mjs check

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
step "publish.sh produces a mirror that matches its source" \
  node tools/check_published.mjs

# …and the one layer in it publish.sh transforms rather than copies. The residents
# records ship minified for the size budget, so the byte comparison above cannot see
# them; this asserts the stronger-reading claim on the SHIPPED form — same value, same
# files, nothing dropped. It is also the ONLY owner of that claim now: until T-0938 the
# two writers of the residents layer each wrote the mirror themselves and
# `apply_census_1840_bridges.py --check` asserted its own copy was fresh, which is how
# two owners came to disagree about whitespace and turn this gate red on any run that
# published (T-0933).
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
# found the letter-list mint wants and has not got yet. Only the mint is still
# carried as ungated in data/research/check_gate_baseline.json.
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
step "the register's four documented men still head the roofs the deal gives them" \
  python3 tools/replace_invented_residents.py --check

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
# NOT GATED (T-0662; the drift itself is T-1222's. It was T-0691's until 2026-09-18,
# when the owner's ruling landed and T-0691 shrank to the card gate below — the 798
# files are a pipeline-ordering question and were never the collisions).
# This slot ran `synthesize_resident_research.py --check`, which is not the mint.
# `tools/mint_letter_list_residents.py --check` is, and it reports 798 file(s)
# differing — but a byte-identity check is the wrong contract for this pass, because
# it is NOT the last writer of the files it derives: the synthesis above rewrites the
# `letter_list_only` cohort's grade, subtype and note, and retires households outright.
# Re-running the mint over the committed tree therefore REVERTS that work — it puts
# grades back from `inferred` to `attested` and strips the PROJECTED RESIDENT
# qualifier off post-office-only names, which is a confidence upgrade this project
# forbids — and it re-mints 54 households under changed ids (hh_adains_will_si becomes
# hh_adains_willisi) out of the same name-splitting fault as above. The pass is gated
# below by `--gate` and `--self-test`, which prove what they can. `--report` and
# `--scale` print the mint and its refusals.

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
step "the research sign-off re-derives, and its GO still follows from the tree" \
  python3 tools/report_research_signoff.py --check --quiet

selftest "…and every condition under that verdict fires when it is broken" \
  python3 tools/report_research_signoff.py --self-test

# T-1296. The land-sale ruling register is DERIVED — 1,572 notes nobody typed — so the
# claim it makes is not "somebody wrote these down" but "these re-derive from the register
# as read and the crosswalk as adjudicated". That claim is only worth anything if it is
# checked, and a drifted derived register is worse than an absent one: it reads as
# judgement and is not.
step "the land-sale rulings re-derive from the register and the crosswalk (T-1296)" \
  python3 tools/spend_land_sales_rulings.py --check --quiet

selftest "…and each of its rules still fires on the row it is for" \
  python3 tools/spend_land_sales_rulings.py --self-test

# T-1144 ACCEPTANCE 9. 820 households stand `present_on_scene_date: uncertain`, and what
# makes that a finding rather than a gap is a DATE: the last day the corpus can still see
# the person. T-1159 classifies those presences by it and T-1172 re-admits them against
# it, so the date is load-bearing for two tickets — and until 2026-09-18 it lived only in
# the prose of the presence note, where the roster below reached for it with a regular
# expression. A second representation of the same fact is the thing that drifts, and that
# one found a date on the handful of notes that happened to print one.
#
# It is derived from the card's own evidence blocks now, written onto the card, and read
# from there. The gate holds both halves of the contract: a leg under every uncertain
# presence, and NO leg on a presence that has since been settled — the field is the
# evidence under a verdict and may not outlive it. The mints rebuild the presence block
# whole, so `tools/resident_mint_carry.py` carries the leg through them and its own
# self-test asserts both the slot and the removal.
step "every uncertain presence carries the dated evidence leg under it (T-1144)" \
  python3 tools/derive_presence_evidence_leg.py --check

selftest "…and the leg's tier, window and removal rules fire over their fixtures" \
  python3 tools/derive_presence_evidence_leg.py --self-test

# T-1159. The borderline roster is the OFFER reconstruction reads before it invents a
# name: every name the research read and withheld from 1835, with the reason it was
# withheld and what may be done with it. It is derived from the ledger and the resident
# layer and it mints nobody, which is exactly why it has to be re-derived rather than
# trusted — a roster that has silently drifted from the ledger would send the
# reconstruction bands after people the research has since ruled on. The check also
# asserts the accounting rule: every non-asserted ledger unit is either carried as a row
# or listed as naming no person, and never neither.
step "the borderline roster re-derives from the ledger and the resident layer (T-1159)" \
  python3 tools/export_borderline_roster.py --check --quiet

selftest "…and its class, accounting and community assertions still fire when broken" \
  python3 tools/export_borderline_roster.py --self-test

# T-1298. The remainder of T-1236 — the resident-pass reservations, the newspaper person,
# notice, event, shipping and price units, the church register entries, the non-person book
# readings and the one Genealogy Trails reading — ruled across five derived registers on the
# same terms. The corpus they cover is fixed by `natural_disposition`, the derivation that
# reads no ruling register at all, so writing them cannot change what they must cover; this
# gate is the proof that they still re-derive from the readings as committed.
step "the remainder rulings re-derive from their five corpora (T-1298)" \
  python3 tools/spend_remainder_rulings.py --check --quiet

selftest "…and each of its rules still fires, and hands on only to live work" \
  python3 tools/spend_remainder_rulings.py --self-test

# T-1330. THE SPEND ITSELF, where the two steps above only ROUTE. Thirty of T-1301's
# `corroborated_enrichment` findings named an arrival, an origin, a departure or a dated
# appearance, and they had been handed from arrival ticket to arrival ticket without being
# read against the cards they name. Nine of them retire a value the arrival stage DREW —
# an origin region taken from the Old Settlers birthplace sample, an arrival year drawn
# from a distribution truncated at the household's bound — and the block that replaces one
# carries no `written_by_stage` mark, which is how reconstruct_residents_1835.py's
# `writable()` yields the field. So two gates have to agree here and this is the first of
# them: the blocks re-derive from the adjudication, and the adjudication still covers every
# unit the ruling register hands this pass, in both directions.
step "the enrichment arrival and origin spend re-derives onto its nine cards (T-1330)" \
  python3 tools/spend_enrichment_arrivals.py --check

selftest "…and its citation, naming and retirement rules still fire when broken" \
  python3 tools/spend_enrichment_arrivals.py --self-test

# T-1469. THE SAME INSTRUMENT OVER THE TRADE AND PREMISES HALF. Thirty-seven of T-1301's
# `corroborated_enrichment` findings named a trade, a firm, a shop, a tavern, a store or
# the premises one was kept at, and they were handed from business ticket to business
# ticket — T-1182, its five children, T-1190, its three, T-1468 — without being read
# against the cards they name. They are read now, against fields that did not exist when
# the hand-off was written: the converged business layer (T-1310, T-1440..T-1442), the
# dated plural roles with their `covers_scene_date` flag and their written withdrawal
# (T-0837, T-0991), and the committed candidate-fact table (T-1232). Nothing here writes a
# card, so what this gate proves is that every field the register NAMES still stands on the
# card, graded and cited: a carrier that has moved is a note that no longer says what the
# card says, which is the only way a read-only register can go wrong.
step "the trade and premises spend re-derives from the cards it names (T-1469)" \
  python3 tools/spend_trade_premises.py --check

selftest "…and its carrier, outcome and coverage rules still fire when broken" \
  python3 tools/spend_trade_premises.py --self-test

# T-1354. THE OTHER HALF OF T-1330's SPEND. Six of its thirty enrichments name a DEPARTURE
# from Chicago and no field on a resident card carries one — the only thing a removal bears
# on is `present_on_scene_date`. They were handed to T-1144, then to whichever child of its
# split happened to be open, and a hand-off is not a spend. These six are now ruled one at
# a time, each with the removal read BESIDE the other sources on its card rather than out
# of the one late compiler that carries it, because a departure read alone is the one way
# this dataset can delete a documented person on a single say-so. Five do not reach the
# scene date and the sixth was already written onto its card by T-0478, so nothing moves —
# and the gate is here precisely so that stays true: --check re-reads all six cards, and a
# presence that moves out from under one of these rulings turns it red.
step "the six departure rulings re-derive from the register and the cards (T-1354)" \
  python3 tools/spend_departure_rulings.py --check --quiet

selftest "…and its corpus, outcome and read-beside rules still fire when broken" \
  python3 tools/spend_departure_rulings.py --self-test

# T-1297. The same instrument over the name-on-a-roll body: the 1833-1835 poll and tax
# lists, the 1832 Black Hawk War enrollments, the 1830 heads of family, and the town
# findings of Andreas, Norris and Fergus that describe a year at or before the scene. 718
# notes nobody typed, derived from the rolls as read and the crosswalks as adjudicated, so
# the same claim needs the same check: a drifted derived register reads as judgement and
# is not.
step "the name-on-a-roll rulings re-derive from the rolls and the crosswalks (T-1297)" \
  python3 tools/spend_name_on_a_roll_rulings.py --check --quiet

selftest "…and each of its rules still fires on the row it is for" \
  python3 tools/spend_name_on_a_roll_rulings.py --self-test

# T-0764. What the eight gates below assert, and what they do not: a cohort manifest is a
# RESERVATION — these ids, in this order, each still a real named person — plus a SNAPSHOT
# of the tree at the moment the cohort was fixed. The reservation is re-derived and must
# match. The snapshot is not: research landing on a member is what the cohort is FOR, and
# gating it made a finished pass fail its own build (dev went red on 2026-09-05 that way).
# The other half of the same contract is on the write path — `freeze.write()` carries the
# committed snapshot forward, so regenerating a manifest can no longer overwrite the freeze
# with today's tree, which is how "this person came in at `inferred` on one source" was
# being lost silently, without a diff anybody read.
selftest "the cohort freeze's own assertions still fire when broken" \
  python3 tools/resident_cohort_freeze.py --self-test

# T-0442, T-0462, T-0463, T-0478, and T-0479. These reviews sit beside household facts on purpose: a plausible
# biography must stay a candidate until something more than the name bridges it
# to the 1835 record. Re-derive the fixed cohort and its public review payload.
step "the 75-person real-resident research cohort is fixed" \
  python3 tools/select_resident_research_pilot.py --gate

step "the second non-overlapping 75-person research cohort is fixed" \
  python3 tools/select_resident_research_pass_2.py --gate

step "the third non-overlapping 75-person research cohort is fixed" \
  python3 tools/select_resident_research_pass_3.py --gate

step "the fourth non-overlapping 75-person research cohort is fixed" \
  python3 tools/select_resident_research_pass_4.py --gate

step "the fifth non-overlapping 75-person research cohort is fixed" \
  python3 tools/select_resident_research_pass_5.py --gate

# T-0870. The five gates above used to DIE when a member's `letter_list_only` flag, or
# the presence value its stratum is named for, moved in the tree — the same event
# T-0764 had just settled is the research landing rather than staleness, arriving
# through a different door. The assertions are kept and their direction is scoped the
# way pass 13 scopes its own (T-0492): minting a cohort still refuses a member the
# stratum no longer describes, and once frozen the gate counts and names it and stays
# green. These prove BOTH halves per selector, because a scope nobody tests is a
# deletion nobody noticed.
selftest "…and each selector's stratum tests still refuse a mint and report a gate" \
  sh -c 'python3 tools/select_resident_research_pilot.py --self-test \
      && python3 tools/select_resident_research_pass_2.py --self-test \
      && python3 tools/select_resident_research_pass_3.py --self-test \
      && python3 tools/select_resident_research_pass_4.py --self-test \
      && python3 tools/select_resident_research_pass_5.py --self-test'

# T-0492 fixes cohorts 13, 14 and 15 in one selector, BEFORE their three tickets run,
# so T-0508, T-0509 and T-0510 do not edit this file and the same population frame at
# the same moment in three parallel runs. The frame is 228 named residents carrying no
# research row — measured, not the ticket's estimated 237 — chunked 76/76/76. 225 of
# them are the pilot, pass 2 and pass 3 cohorts, reserved and never researched (T-0511),
# which is why the gate refuses overlap with a completed RESEARCH ROW and not with a
# reservation. docs/RESEARCH/resident-research-pass-13.md carries the arithmetic.
step "the thirteenth research cohort is fixed" \
  python3 tools/select_resident_research_pass_13.py --gate

step "the fourteenth research cohort is fixed" \
  python3 tools/select_resident_research_pass_14.py --gate

step "the fifteenth research cohort is fixed" \
  python3 tools/select_resident_research_pass_15.py --gate

step "all 375 reviewed residents have reproducible research outcomes" \
  python3 tools/compile_resident_research_pilot.py --gate

# T-1109. Cohort 14's ledger is the one a SECOND reading had to adjudicate: T-0816 ruled
# the 36 people the two readings disagreed on, and fourteen of those rulings go against
# what the mechanical rule derives. Until this gate the ruled outcomes lived only as an
# edit of the output file, so the pass could not be re-derived at all — and nothing asked
# it to, while all thirteen crosswalks it reads were rebuilt underneath it between
# 2026-09-05 and 2026-09-14. The tool now reads pass_14_reconciliation.json as the
# evidence it is, which is what makes --check possible; this step is what stops the two
# from parting again. A failure here means either a crosswalk moved and the ledger has
# not been regenerated, or somebody edited the findings by hand.
step "cohort 14's ruled ledger still follows from its crosswalks and T-0816's rulings" \
  python3 tools/complete_resident_research_pass_14.py --check

# T-0511. The reference README's completion rule says a cohort ticket is not complete
# "while its XLSX/CSV/README package exists only locally", and on 2026-09-04 the folders
# existed for T-0478..T-0486 only: the first three slices — 225 people — had findings JSON
# and a dossier and nothing a reader could open. The packages are now DERIVED from the
# frozen manifests and the committed review payload, so this step is what keeps them from
# quietly stopping being true, and the index in the README with them.
step "every completed research cohort has a durable package, and it still matches its records" \
  python3 tools/export_resident_research_package.py --check

selftest "…and that gate's own assertions still fire when broken" \
  python3 tools/export_resident_research_package.py --self-test

# …and the ruling's own conditions, which --check cannot see. --check proves the records
# are what the pass derives; this proves the DERIVATION is what the owner permitted —
# every minted person carrying `letter_list_only` and the dated return behind it, and not
# one of them holding a roof, a trade, a second member or a building that names them. The
# failure mode it guards is silent: a later generator that deals roofs by household would
# put seven hundred invented dwellings in the town off a post-office list, and nothing
# about any single record would look wrong.
# T-0424. The 1 January 1834 return was read at the page image, and the roster of all 170
# printed lines is what the crops' 78 names are now measured against. Two things can rot
# here and neither is visible in a record: the tie between a crop fragment and its printed
# line is by ORDER, so a line inserted into or dropped from the roster silently re-points
# every entity below it at its neighbour; and the twelve readings the image OVERTURNED are
# the ones a later concordance pass would helpfully "repair" back to the impression they
# came from. --check holds the order, the count and the overturns; the gate is what makes
# re-reading the image unnecessary rather than optional.
step "the 1834 letter list's crop entities still point at the printed lines the image read" \
  python3 tools/read_letter_list_1834_image.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_letter_list_1834_image.py --self-test

# T-1138. And the three lines of the 1 APRIL 1834 return that two transcriptions of one
# return read differently, settled at three impressions of the page. What rots here is
# specific and would be invisible: `normalized` is what the town mints from, so a later
# concordance pass that "repairs" one of these three back to the impression it came from
# silently resurrects a card the image withdrew — a Raymore, or a Square with an e the
# type never set. --check holds the reading onto the three entities, refuses to let the
# other seventy-nine of the claim borrow their `scan_verified`, and asserts the withdrawal
# on disk: the two cards the image overturned are gone and the two it sets are committed.
step "the 1 April 1834 return's three contested lines still carry the reading the page made" \
  python3 tools/read_letter_list_1834_04_01_image.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_letter_list_1834_04_01_image.py --self-test

step "the letter-list cohort is what the owner's ruling permits" \
  python3 tools/mint_letter_list_residents.py --gate

selftest "…and that gate's own assertions still fire when broken" \
  python3 tools/mint_letter_list_residents.py --self-test

# T-0660. The pass reads a printed name one way now and read it another way before
# T-0638, and the difference collides nine committed records onto a family name some
# other record already holds. Retiring them is the owner's ruling and has not been made,
# so what is gated here is the MEASUREMENT: the derived list of collisions, what each
# would strand, and how far the committed cohort has drifted from what its own tool
# derives. The report is generated, never hand-written, and --check re-derives it — the
# failure mode it closes is a decision paper that quietly stops describing the tree it
# was measured on while the ruling it is waiting for has not happened yet.
step "the letter-list collision report still describes the tree" \
  python3 tools/report_letter_list_collisions.py --check

selftest "…and its two readings of a printed name are still two" \
  python3 tools/report_letter_list_collisions.py --self-test

# T-0691. The ruling was made on 2026-09-18 — option (c), refusals 7 and 8 are MINT-TIME
# rules and un-mint nobody — and its whole content is that the collision is SAID rather
# than acted on. So the thing to gate is no longer the measurement but the saying: every
# standing card a mint-time refusal lands on carries the block, and a card that stops
# saying its collision is red. T-0660 shipped eight of the seventy-five and left the rest
# to the cohort's next full re-derive; that re-derive is T-1222's and its byte-identity
# contract is the wrong one for this pass (see the note above the mint), so waiting for it
# meant sixty-seven readers meeting a card whose awkwardness was invisible. The block is
# composed by `mint_letter_list_residents.record()` and written by --write-records, which
# touches nothing else on the card; --check-records re-derives and compares.
step "every card a mint-time refusal lands on still says its collision" \
  python3 tools/report_letter_list_collisions.py --check-records

# T-1290. The 1840 census is CLOSED for the 1835 reconstruction and what closed it is a
# residue table: eight leaf-by-leaf tickets folded into one statement of what did not
# settle, on which leaf, against which competing reading, and why. A stated gap is a
# finished answer — but only while it still describes the tree. Every figure in that
# table is resolved out of the committed page files at render time, so a leaf re-read
# afterwards either moves the report or turns this red. The rot it closes is the one
# T-0926 already suffered: an argument resting on 15 of 29 figures reading `inferred`,
# on a tree that carries 17.
step "the 1840 residue table still describes the leaves it closed" \
  python3 tools/report_census_1840_residue.py --check

selftest "…and its figures still come off the page files, not out of the prose" \
  python3 tools/report_census_1840_residue.py --self-test

# T-1008. And the ledger that puts T-0424's 170 printed lines beside T-0310's cohort,
# line by line. It is DERIVED — from the roster, from the extractions of the return's
# impressions, and from `mint_letter_list_residents.mint()` itself — so it has three
# masters and any of them can move under it: a name added to a crop, a household the
# mint newly refuses on a surname some other pass just took, a line re-read at the
# scan. Each of those changes what a printed line reaches while leaving the ledger's
# own text untouched and plausible, which is exactly the rot --check exists for. The
# figure it defends is the one the cohort's floor is stated in: 54 of the 170 lines
# reach nothing at all.
step "the 1834 letter list's 170 lines still reach what the concordance says they reach" \
  python3 tools/concord_letter_list_1834_01_01.py --check

# T-1011. And the lift that closed the 54 the ledger above found reaching nothing. The
# claim it writes is DERIVED — the set of lines is every one the other five claims leave
# untied, computed through the concordance's own tie rules — so the failure mode is a
# line carried twice: a later pass re-reads one of the crops, that reading takes a line
# this claim also lifts, and the town holds the same addressee under two names with
# nothing looking wrong in either record. --check re-derives the set against the
# committed claim and fails on drift in EITHER direction.
step "the lines the 1834 crops lost are still exactly the ones the roster lift carries" \
  python3 tools/lift_letter_list_1834_unread.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/lift_letter_list_1834_unread.py --self-test

selftest "…and its tie rules still refuse the ambiguities they are meant to" \
  python3 tools/concord_letter_list_1834_01_01.py --self-test

# T-1141. And the SAME ledger for the 1 April 1834 return, whose 193 printed lines were
# counted off the 8 April impression after T-1138's three-line read found five things
# wrong in the twenty lines it happened to look at. It has the same three masters as the
# January one and one more that is specific to it: the tie is an ORDER-PRESERVING
# alignment of each claim onto its sub-column, so a name added to, removed from or
# re-read in any of the six claims re-shuffles which printed line every later entity of
# that claim lands on, silently and plausibly. The two figures this defends are the ones
# the ticket exists for — thirty lines dropped by the transcription the cohort was minted
# from, and two of them dropped by every claim the corpus holds — plus the return's own
# length, which is what the printed total at the foot of the column agrees with.
step "the 1 April 1834 return's 193 lines still reach what the concordance says they reach" \
  python3 tools/concord_letter_list_1834_04_01.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/concord_letter_list_1834_04_01.py --self-test

# And the fourth pass, BESIDE the letter-list one rather than above it (T-0514). The
# owner ratified a grading ladder for resident evidence on 2026-09-03 and T-0513 spent it
# into a proposal; nothing in that proposal had ever been written onto a card, and only 37
# of the 85 men on the 1835 poll list had even a surname in the residents layer. This pass
# writes the people the ladder reaches out of the civic lists, the parish register, the
# contemporary papers, the printed directories and the 1840 census — everything except the
# post office's letter lists, which the pass above owns and whose pool refusal 5 keeps this
# one out of. Gated three ways because the failure modes are all silent: a derivation that
# stopped re-deriving would let a hand-edit stand as a reading, a refusal that stopped
# firing would mint a Potawatomi enrollee of 1832 as an 1835 householder with an invented
# surname order, and a gate that stopped looking would let one of these 532 quietly gain a
# roof, a trade or a family that no source gives it. `--report` prints all 6,148 refusals
# with their reasons; docs/LIBERTIES.md L218 carries the scale.
step "the civic, church, press and book residents re-derive from the ladder" \
  python3 tools/mint_civic_residents.py --check

# T-0515, the second mode of the same pass. `--build` above mints the identities
# the town does NOT hold; this applies the ladder to the 162 it proposes for people
# already on a card, and its whole value is that the decision is DERIVED — the
# regrade, the eight it refuses on the forename the volume prints, and the forty-five
# downgrades it declines because the card rests on Andreas or on an adjudicated
# research outcome the ladder never read. A hand-edit to any one of those grades
# would otherwise stand as a reading.
step "the regraded residents re-derive from the ladder too" \
  python3 tools/mint_civic_residents.py --regrade --check

step "…and none of them claims more than a person and a reading" \
  python3 tools/mint_civic_residents.py --gate

selftest "…and that pass's own refusals still fire when broken" \
  python3 tools/mint_civic_residents.py --self-test

# T-1117. The 1833 tax list is a PROPERTY ROLL: the town assessed ground, so its 115
# names are owners and estates rather than people at the place, and it draws no line
# between a resident payer and a non-resident one — the published transcription has no
# column that could. Thirteen households rested their whole claim of presence on 1 July
# 1835 on that list's at-or-before leg, and the refutation is the list's own entry 110.
# The refusal lives in the pass above; this holds the two readings it stands on, so a
# transcription that moves reopens the ruling instead of leaving it citing a page that
# no longer says it. docs/RESEARCH/tax_list_1833_not_a_residence_check.md is the reading.
step "the 1833 tax roll still admits the man who proves it is not a residence check" \
  python3 tools/assert_tax_roll_ruling.py

# T-0720, the third spend of the same proposal. The two modes above own the 531 cards
# that carry a `ladder_rule`; nothing owned the other 873, and T-0692's --coverage
# measured 864 of them carrying a rung the ladder HAD ruled and no pass had ever
# written down. This pass writes it — one scalar, only where the ladder AGREES with the
# grade the card already carries, never a downgrade — and puts every disagreement on the
# owner's conflict list instead. Gated because the whole value of a rung on a card is
# that it is DERIVED: a hand-written one would be a grade's reason invented rather than
# ruled, and `--check` is what says so.
step "the ladder's ruled rungs re-derive on the cards no mint owns" \
  python3 tools/spend_ladder_rungs.py --check

step "…and none of them moves a grade to close the gap" \
  python3 tools/spend_ladder_rungs.py --gate

selftest "…and that pass's own refusals still fire when broken" \
  python3 tools/spend_ladder_rungs.py --self-test

# T-0839. THE MINTS' TEST FOR "the town already carries this person" IS THE NAME AS THE
# SOURCE PRINTED IT, so a man his sources spell six ways was minted six times: Gurdon
# Saltonstall Hubbard stood on six cards and Lieut. James Allen on four, and only the one
# card the ladder never reached knew Allen was an army officer. The merges landed on
# 2026-09-05 under written rulings. This gate is the half that stops it recurring — it
# re-derives the candidate clusters from the committed cards and FAILS while any card in
# one carries no written ruling, so a pass that re-splits an identity says so here rather
# than in the town's population count. It also holds the promise the merge made: every
# folded record still in the tree, every folded person_id still resolving, and every
# source a folded card brought still cited by the survivor.
step "one person, one card — every duplicate cluster carries a written ruling" \
  python3 tools/consolidate_town_cards.py --check

selftest "…and that pass's own assertions still fire when broken" \
  python3 tools/consolidate_town_cards.py --self-test

# T-1002. The candidate test above folds the surname AND the forename exactly, and three
# duplicate pairs one letter apart were therefore never proposed to it — not refused, not
# deferred, never seen. The measurement is the only thing that says how large that blind
# spot is, and its answer (71 pairs one letter of slack would add, against the 21 the exact
# test proposes) is the reason the remaining ones are ruled on pages and not on a distance.
# The counts move whenever the residents layer grows, so they are not gated for equality;
# what is gated is that the test still runs at all and still sees its own three pairs. A
# measurement that quietly stopped firing would report "the class is only the three".
selftest "the one-letter candidate test still measures the blind spot it was written for" \
  python3 tools/measure_card_fuzzy_candidates.py --self-test

# T-1291, which folded T-1027's 68-row epic and four satellites into one ticket on the
# owner's instruction that the research spend is a CHECK before reconstruction, not a
# programme. The measurement above says how many pairs the one-letter slack proposes; this
# gate says every one of them has been ANSWERED, and it is stricter than the pool it
# replaced: T-1027 counted a pair as ruled when EITHER card stood in some ruled cluster and
# admitted in its own table that "it does not mean the PAIR is ruled". A ruling weighing
# `wright_j` against two Wrights says nothing about `wight_j_f`. So this asks for a ruling
# that names BOTH cards, which is the only thing that answers the question the pair asks —
# and it fires the moment the resident layer grows a new one-letter neighbour, which is how
# the pool silted up to 68 rows the first time.
step "every one-letter card pair carries a ruling naming both its cards" \
  python3 tools/rule_fuzzy_card_pairs.py --check

selftest "…and pair-level coverage still refuses a ruling that names only one card" \
  python3 tools/rule_fuzzy_card_pairs.py --self-test

step "the three levels mean what they say" \
  python3 tools/audit_confidence.py --strict

step "data JSON parses" check_json

# Almost every Playwright tool here is a MEASURING instrument, and the rule is
# that a change is measured before it is claimed. Twelve of the sixteen could
# not be pointed at a browser, so on a runner without Playwright's own build
# they died before their first frame — which turns "measured" into "asserted"
# without anyone deciding to (T-0153).
step "every browser-launching tool honours PW_EXECUTABLE" \
  node tools/check_tool_browser.mjs

# The road-legibility gate fires once per STATION while the measurement is per
# BAND, so a band could collapse 55 points inside a passing station and the
# suite would print the same totals before and after. The movement report is
# what makes that visible; this is the report's own self-test, which replays
# R-W1's merge and requires it to name south_water 250-600 m unprompted (T-0016).
selftest "the road-band movement report names a band that moved" \
  node tools/road_band_movement.mjs --self-test

# T-0100. The street layer graded a ribbon by its surface and its wear and never
# by `geometry_confidence`, so an INVENTED ROUTE under an attested surface would
# have drawn at full confidence. It is degenerate in today's data — every street
# is pinned at `reconstructed` wear already — which is exactly why it needed a
# test rather than an eyeball: nothing on screen can show it either way. The
# test slices the expression out of streets.js instead of copying it, so the
# shipped grade and the tested grade cannot drift apart, and it carries a
# tripwire that fires the day the data makes the fix matter.
step "a street's invented line reaches the picture" \
  node tools/test_street_confidence.mjs

# K49(d) warned for a week that a spatial filter running after the stratified
# deal selects a BIASED set of ranks, and told every later parcel not to use
# `stratum` in a filtered layer on the strength of it. T-0018 refuted that: the
# position-to-rank map is re-keyed per block, so a rule that reads only position
# cannot lean. This runs the refutation's own control pair every time — a filter
# written to read the rank must be caught, a rank-blind one at the same rate must
# not — so the day someone makes the deal rank-correlated, the claim stops being
# refuted here rather than in a census six weeks later. It reads the deal out of
# flora.js rather than keeping a copy, so it fails by name if that file moves.
selftest "a spatial filter still cannot bias the sward's rank deal" \
  node tools/measure_rank_bias.mjs --self-test

# The smoke's parts get re-cut whenever the town outgrows the ten-minute foreground
# ceiling — four of them in 2026 alone — and docs/SMOKE-BUDGET.md's map of "which
# parts cover which change" is the kind of table that goes quietly wrong the first
# time a renderer module is renamed under it. So the map is not prose: it is a
# structure in tools/smoke_budget.mjs, and this holds it against the tree. It fails
# if a mapped path no longer exists, if a part of the body is covered by no row, if
# `PARTS` in smoke_renderer.mjs has moved out from under it, or if an unmapped path
# ever stops meaning THE WHOLE GATE — which is the property that makes the recipe
# safe to follow (T-0235).
selftest "the smoke's change-to-parts map still matches the tree" \
  node tools/smoke_budget.mjs --self-test

# The 1833-1835 newspaper corpus is the PAPERS epic's foundation: eighty-six issues
# that the project could not cite until they had a register to resolve against. The
# register is only worth something if it is true, so this asserts the count rather
# than observing it (a silently dropped issue is otherwise invisible), requires dates
# to increase strictly per publication, and re-hashes every derived text file. The
# deposit itself is on `main` and not on `dev` (T-0275), which is why the check knows
# three deposit states and not two: present, absent, and PARTIAL — and partial is
# always red, because that is the state that means damage.
step "the newspaper corpus resolves, and nothing under data/research/ is published" \
  python3 tools/newspaper_corpus.py --check

# T-0492. The newspapers' pipeline is the one that works, and six more domains are about
# to be read in parallel by runs that cannot see each other — the civic lists, the 1830
# and 1840 census, a church register, books and directories. If each invents its own file
# shape, the consolidation re-reads ten dialects and the refusals nobody wrote down have
# to be made again. So the shape is fixed before the sweep starts: a CLOSED kind
# vocabulary, a required reading grade, a coverage declaration where a declared item
# nothing reaches is a hole, an identity crosswalk that declares its refusals as carefully
# as its merges, and — for the two domains whose text this repo commits — the same
# verbatim gate the papers carry, which rebuilds every quote out of the committed lines
# and refuses one that differs by a character. The scaffold is EMPTY on purpose.
step "the research domains hold one shape" \
  python3 tools/research_domains.py --check

# T-0493, T-1029. THE FOUR VOTER LISTS, re-derived — 345 printed rows out of one
# committed text, and the crosswalk that proposes which of them meet the people of
# 1835. The tool had a `--check` from the day it was written and nothing ran it, so
# the two files it owns outright drifted as the residents layer grew underneath them:
# 849 cards were on the tree when voter_crosswalk.json was last built and 1,308 are
# now, which is 201 entries that had reached nobody and do reach somebody, reported
# by a committed file as unmatched. The third file is the domain's identity
# crosswalk, whose T-0493 pass DECLARED 82 refusals while the rules derived 26 — the
# shape of drift that is worst here, because a refusal is a judgement and a stale one
# reads as a judgement somebody made.
step "the four voter lists, their crosswalk and their refusals re-derive" \
  python3 tools/read_voter_lists.py --check

# T-0856. THE 1830 SCHEDULE, for the same reason and with a second fault underneath.
# `read_census_1830.py` had a `--check` from the day it was written and check.sh never
# called it, so the 200-head reading's crosswalk drifted off the town tree exactly as
# the voter lists above had: T-0839 and its siblings FOLDED `hh_clybourn_archibald`
# onto `hh_clybourne_archibald`, retired `hh_mann_john`, `hh_reed_george`,
# `hh_smith_d_a` and `hh_smith_james`, and raised `hh_harkness_j_p` — and the committed
# crosswalk went on printing sixteen matches and sixty-two refusals against cards that
# no longer exist. It re-derives at fourteen and sixty-three, with Clybourn demoted from
# a merge to a spelling CANDIDATE, which is the conservative direction and the whole
# argument for gating it: nobody chose those numbers, and nobody saw them move.
#
# The drift was invisible from below AND from above. `research_domains.py --check` is
# green because it does not re-derive this file, and `consolidate_resident_evidence.py
# --check` — which copies these refusal strings verbatim into identity_master.json —
# was consistent with the stale copy and went red only once the crosswalk beneath it
# was rebuilt. Both are re-derived elsewhere in this gate; neither could reach this.
step "the 1830 schedule's reading and its crosswalk re-derive off today's town tree" \
  python3 tools/read_census_1830.py --check

# And the fault underneath: `--check` used to re-derive IN PLACE — snapshot, `build()`
# over the committed files, diff. That reads as a check and behaves as a REPAIR, so the
# first run printed FAIL and mended the file, the second printed pass, and the drift was
# gone before anyone could look at it. As a gate it would have been worse than none:
# green on the second commit of every day, and every step below it reading a working
# tree this one had dirtied. It builds into a scratch tree now, and this holds it there.
selftest "…and that check stays non-destructive, and still fires on a real drift" \
  python3 tools/read_census_1830.py --self-test

# T-0856 ask 2, which was "say what ELSE under data/research/ derives from the household
# tree and is likewise unchecked — this cannot be the only one." Answered in a PR body
# that is true for a day: the tree is folded and renamed most weeks and a new domain
# reader lands most weeks, so the only answer that stays true is the enumeration. This
# walks every generated file under data/research/, keeps the ones whose generator reads
# data/residents/households/, and requires each to be re-derived by a step above. The
# answer on the day it was written was "read_census_1830.py, and nothing else" — 25
# generators, 39 files, one hole — and this goes red on the next one rather than waiting
# for the next T-0757 to trip over it.
step "every household-derived file under data/research/ is re-derived by this gate" \
  python3 tools/check_household_derivations.py --check

selftest "…and that enumeration's own assertions still fire when broken" \
  python3 tools/check_household_derivations.py --self-test

# T-1135. The Pruyne/Pryne ruling is a COUNT over that 1833 tax roll and not a reading of
# a page, and every figure it turns on can move underneath it: the roll is re-derived by
# the step above, the ground it stands on is re-derived by the corporation-limits tool,
# and the corpus it searches grows every week. Gated for the same reason T-1017's three
# figures are — a ruling that stands on a measurement should go RED OUT LOUD when the
# measurement moves, rather than quietly keeping a verdict the arithmetic no longer gives.
step "the 1833 tax roll still leaves Peter Pruyne one entry, and it is Pryne" \
  python3 tools/exhaust_tax_1833.py --check --quiet

selftest "…and each of that count's own assertions still fires when broken" \
  python3 tools/exhaust_tax_1833.py --self-test

# T-0566, T-0569. Norris's 1844 directory arrived as three generated files that no
# gate re-derived: the 2,073 entries, the crosswalk that proposes which of them meet
# the people of 1835, and the layer the panel renders those meetings from. A hand-edit
# to any of them — a match nudged out of "ambiguous", a refusal quietly dropped, a
# trade written into a card — would have shipped unopposed. All three rebuild and diff.
# T-0670, T-0696. THE TWO RULE MODULES the directory crosswalks import rather than
# restate: the forename agreement that refuses `Abbott, Thomas L.` onto Titus H. Abbott,
# and the tie discriminator that may NARROW a contested or ambiguous tie on a trade and
# may never make it a match. Both carry their own self-test and NEITHER was gated, so a
# loosened rule — one more contraction, a premises allowed to break a tie after all —
# would have re-derived both crosswalks quietly and passed every check below. The
# crosswalks are re-derived here; the rules they are re-derived BY were not.
selftest "the directory forename rule's own assertions still fire when broken" \
  python3 tools/name_agreement.py --self-test

# T-0987 stretch 9. And the OTHER rule module the same paragraph describes, which was
# left ungated and went red: stretch 8 put `doctor` into the title vocabulary and two of
# printed_twice's cases had been asserting the defect that vocabulary removed. Nothing
# noticed for a day. A rule that decides which printings are one man belongs in the gate
# beside the rule that decides which printing is which person.
selftest "the printed-twice fold's own assertions still fire when broken" \
  python3 tools/printed_twice.py --self-test

selftest "…and the tie discriminator's do too" \
  python3 tools/tiebreak.py --self-test

# T-0987 stretch 14. THE FOURTH RULE MODULE, and the one that reads the part of the
# name the other three stop before: the crosswalks key on surname plus FIRST INITIAL,
# so everything the compositor set after that letter was committed and never weighed.
# It is gated here for the same reason its three siblings are — the whole of its
# authority is the ranking (a spelling outranks an initial, or `Heacock, jr., R. E.`
# takes his father's entry), the word-count test (fire on what a reading says, never on
# what it omits), and three refusals that each cost more than they gave: a wife is not
# her husband, a son is not his father, and a page setting fewer words than a reading
# separates no two readings. Loosen any one of them and all four crosswalks re-derive
# quietly, with a match on the face of them and a wrong man underneath.
selftest "the whole-printed-name rule's own assertions still fire when broken" \
  python3 tools/named_by_the_page.py --self-test

# T-0987 stretch 15. THE FOURTH RULE MODULE, and the only one whose whole output is a
# REFUSAL — it promotes nothing, so what this gate protects is the discipline rather
# than a match. Two things would rot quietly without it: the five-letter floor, which
# is `name_agreement.agrees`'s own number and is what keeps `Cook`/`Cool` and `Hall`/
# `Ball` from becoming spelling variants of each other; and the thirteen second-hand
# lines, quoted verbatim off the printed volume's OCR with its damage left in, which
# are the whole evidence that the sixteen one-letter candidates are the volume's own
# distinction and not this transcription's. A quote that stops being findable at its
# line means the second hand moved under the ruling, and the ruling has to be re-read.
selftest "…and the one-letter surname clause's, whose only outcome is a refusal" \
  python3 tools/surname_one_letter_away.py --self-test

# T-1038. THE THIRD RULE MODULE, and the one that answers a question the other two
# cannot ask: is the 1835 person a PERSON at all, or the one card the letter-list
# mint pass was allowed to seat over a surname the post office printed twice? An
# initial standing against a full forename is a match under T-0670 — deliberately —
# so a card reading `S. Sherwood` took `Sherwood, Smith J., watchmaker and jeweller,
# 144 Lake st` and the reading it was seated over, `Stephen Sherwood`, would have
# refused it. Loosening this module widens what five crosswalks may carry to a card
# the letter list gave a name and nothing else, so it is gated like its two siblings.
selftest "…and the letter-list bucket refusal's, which all five directory crosswalks import" \
  python3 tools/letter_list_bucket.py --self-test

# T-0867. And the one-line predicate BOTH of those rules stand on: "does the 1835
# layer already hold a trade for this person?" It was written four times, once per
# directory crosswalk, and two of the four wrote the truthiness test — which reads
# the layer's `none_recorded` sentinel as a trade, so the crosswalk asking whose
# trade a directory could supply answered nobody. Fergus 1843 reported
# `could_carry_occupation: 0` for two thousand entries on it. It is one module now
# and this is its alarm: widening the sentinel list widens what every directory is
# allowed to carry to a card.
selftest "…and the trade-sentinel predicate all four crosswalks import" \
  python3 tools/trade_recorded.py --self-test

step "Norris's 1844 directory entries re-derive from the committed page text" \
  python3 tools/read_norris_1844.py --check

# T-0695. The eleven forenames archive.org's OCR set in characters no compositor had are
# repaired in the READING against Kim Torp's independent transcription, and the quote
# keeps the damage. The table that does it is the thing that rots: an entry re-read, a
# leaf re-committed, and a row stops matching — or a new garble arrives with no row. The
# self-test fails on either, and on a repair that tidied a quote.
selftest "…and every garbled forename in them is repaired, cited, and none is left unnamed" \
  python3 tools/read_norris_1844.py --self-test

step "…and the 1835 crosswalk re-derives from those entries" \
  python3 tools/crosswalk_norris_1844.py --check

# T-0896. The advertising directory's READING, which its crosswalk above stands on and
# which nothing re-derived. 38 pages of display cards, sliced out of the committed page
# text at each card's own line range, so the failure this catches is a quote that has
# stopped coming from the page it cites — the one fault the crosswalk gate cannot see,
# because the crosswalk re-derives from the reading and would follow it wherever it went.
step "…and the advertising directory's cards re-derive from the committed page text" \
  python3 tools/read_norris_1844_advertiser.py --check

# T-0896. AND THE SECOND READING OF THE SAME VOLUME. T-0566 read the Internet Archive
# scan; Kim Torp read the printed book independently onto genealogytrails.com. The
# committed file is the MATCH between the two hands, and it is the only thing in this
# project that says where our reading of Norris disagrees with somebody else's. It ran
# once, in 2026-09-03, and was never asked again: a re-read entry on either side, or a
# blocking rule changed under the matcher, moves the disagreements and nothing noticed.
step "…and our reading of Norris still disagrees with Torp's in exactly the places recorded" \
  python3 tools/compare_norris_1844_readings.py --check

# T-0867. The ADVERTISING directory's crosswalk beside it, which was the only one of
# the four with a committed output and no gate — so it sat at the residents layer of
# 4 September while the layer moved under it, and a regeneration on this ticket moved
# eleven refusals, five ambiguities and a match that nothing had asked for. Gated now
# for the same reason as its three siblings: a proposal nobody re-derives is a
# proposal that stops describing the town it proposes about.
step "…and the advertising directory's crosswalk re-derives too" \
  python3 tools/crosswalk_norris_1844_advertiser.py --check

# T-0632. And the pass that spends ALL FOUR directory crosswalks — Fergus 1839, Fergus
# 1843, Norris 1844 and Norris's advertising cards — onto the town: the layer the panel
# renders, the ledger that records what each volume was allowed to carry to a card and
# what it was refused, and the `directories` block on the household records those
# rulings name. It replaces the 1844-only pass. Gated byte for byte in all three places,
# because the failure it guards is the one this whole ticket was filed for: a trade or a
# street from 1844 quietly becoming a fact of 1835.
step "…and all four directories' findings re-derive onto the cards they reach" \
  python3 tools/spend_directories.py --check

selftest "…and that pass's four carry rules hold over everything it derives" \
  python3 tools/spend_directories.py --self-test

# T-0633. And what is DONE with the 87 later addresses that pass leaves on the record:
# the fourth address grammar, docs/ADDRESS-BACK-PROJECTION.md, which reads a street
# printed four to nine years after the scene backwards and carries it as the business's
# street FACE. All 87 are adjudicated and the refusals are committed beside the
# placements, so the gate re-derives the whole ledger and every `back_projection` block
# byte for byte. The failure it guards is the same one, one step further on: a face read
# back out of an 1844 directory quietly becoming a position of 1835, or — worse, because
# nothing else would catch it — a refusal disappearing from the record and reading to the
# next run as an address nobody had looked at.
step "…and the later addresses re-derive through the back-projection clauses" \
  python3 tools/back_project_addresses.py --check

selftest "…and no back-projected face has grown a grade, a roof or an 1835 link" \
  python3 tools/back_project_addresses.py --self-test

# T-0669, the residence half of the same grammar: docs/RESIDENCE-BACK-PROJECTION.md, which
# reads a street the volume prints as a HOME — its own `res` or `bds`, or Norris's `house`,
# `h` and `r` — and carries it as the household's street FACE and never as a point. All 61
# residence addresses are adjudicated and the 47 refusals are committed beside the 14
# placements, for the same
# reason the business pass's are: a refusal that disappears from the record reads to the
# next run as an address nobody looked at. The self-test additionally holds the invariant
# the two policies share — no printed address is PLACED by both of them.
step "…and the later HOME addresses re-derive through the residence clauses" \
  python3 tools/back_project_residences.py --check

selftest "…and no back-projected home has grown a point, a roof or an 1835 link" \
  python3 tools/back_project_residences.py --self-test

# T-0846, THE ONCE-EACH RULE, shared. Every pass below finds its own work by a MARKER
# sentence and asks two questions about it — is it PRESENT on the cards a ruling names, and
# does any UNRULED card carry it. A card carrying it TWICE answers both correctly, which is
# how T-0677's measurement went green with all thirty-one land-sales cards doubled. That
# ticket closed the hole in one tool; T-0846 found six passes write a paragraph and three
# still had no such rule, and the three copies that existed had already drifted — two of them
# counted the marker and never looked for a superseded wording. One implementation now, and
# this step is what keeps it wired: it re-reads the tools, so a seventh pass that grows an
# add-only paragraph applier and no `doubles()` fails here on the commit that adds it.
selftest "…and every pass that writes a paragraph onto a card holds the once-each rule" \
  python3 tools/spend_write_once.py --self-test

step "…and no card in the town carries any pass's paragraph twice" \
  python3 tools/spend_write_once.py --sweep

# T-0634, consolidation pass 1. The other half of the same defect, and the older half: the
# four early Chicago lists — the 1833 trustees' poll, the 1833 tax list, the 1834 poll and
# the 1835 poll — had matched 99 entries to people this town holds, and not one of the 99
# had put a source on the record it named. This pass writes them. It is gated in the same
# two directions as the directories pass because the failures are the same two: a ruling
# that stops reaching its card, and a card that carries the paragraph for a ruling the
# crosswalk never made.
step "…and the 1833-1835 rolls' matched rulings are on the cards they name" \
  python3 tools/spend_civic_voter_lists.py --check

selftest "…and that pass writes two fields, moves no grade and repeats without drift" \
  python3 tools/spend_civic_voter_lists.py --self-test

# T-1326. THE PASS ABOVE PUT THOSE RULINGS ON A CARD AND NOTHING COULD COUNT THEM. It writes
# a paragraph into `persons[].note`, and `tools/research_spend_ledger.py` reads a unit as
# SPENT only where a structured node carrying `attested`/`inferred` and a source names it —
# a person node carries `grade`, not `confidence` — so all 292 matched roll entries went on
# reading `unresolved` while the evidence sat on the cards. This pass writes the same
# rulings as `persons[].dated_bounds[]`: one row per entry, `inferred` because every
# identity in that crosswalk is a name agreement, `covers_scene_date: false` because an
# earlier source never promotes, and `bound_kind: "property"` with `here_by: null` on a tax
# row, which is T-1117's standing ruling held in a field instead of in prose.
step "…and each of those rulings is a bound on the card, not only a paragraph" \
  python3 tools/spend_civic_roll_bounds.py --check

selftest "…and a roll bounds a presence, a tax roll bounds property, and neither reaches the scene" \
  python3 tools/spend_civic_roll_bounds.py --self-test

# T-1337. THE SAME HOP FOR TWO MORE CORPORA, AND THIS TIME NOT A LEGIBILITY PASS. T-1329
# held 238 units — the 1830 Peoria & Putnam schedule, St Mary's and St Cyr's registers, and
# the town's press — and only ten of them sat on a card in any form, so an identification
# had to already stand before a bound could be written. Two did: the resident crosswalk's
# 14 matched 1830 lines and the baptismal crosswalk's 13 merged register appearances. This
# pass writes those 27 as `persons[].appearance_bounds[]`; an 1830 row bounds presence in a
# DISTRICT and not at Chicago (`here_by: null` — the division never writes the word
# Chicago), and three register appearances are dated after 1 July 1835, so they date an
# appearance and bound nothing at the scene. The other 83 are refused by name in the ruling
# registers, and the 128 press units went to T-1338 with the id collision that blocks them.
step "…and the 1830 schedule and St Mary's register are bounds on the 21 cards they name" \
  python3 tools/spend_appearance_bounds.py --check

selftest "…and a district is not the town, a later appearance bounds nothing, and no kin tie is taken" \
  python3 tools/spend_appearance_bounds.py --self-test

# T-1343. AND THE THIRD CORPUS OF T-1329, WHICH WAITED ON A NAME RATHER THAN AN IDENTITY.
# The press units could not be spent while a newspaper claim's ledger id was its bare
# `c004` — 55 held issues each print one, so a bound naming it would have closed 937 other
# units of this corpus as `asserted`. T-1342 gave a claim a file-qualified key and this
# pass spends what that unblocked: 111 of the 147 units whose only content is a named
# person on a dated day, written as `persons[].dated_bounds[]` through the shared block,
# two owners for the two papers. The identification is the committed register's
# (`register_1835.json`, `action: enrich`) and is never re-made here; `here_by` is null on
# every row, because a name in the town's print is not a body in the town. The other 36 are
# refused by name in the ruling register, and the ledger's own `ruling_coverage_faults`
# fails a ruling on one of the 111 as work that reads done and is not.
step "…and the 111 identified press appearances are bounds on the 148 cards they name (T-1343)" \
  python3 tools/spend_press_bounds.py --check --quiet

selftest "…and a name in print is never a presence, and no card the register did not enrich is touched" \
  python3 tools/spend_press_bounds.py --self-test

# T-1332. THE SAME HOP, FOR THE LAND REGISTER, INTO THE SAME BLOCK. T-1296 ruled all 1,572
# land-sale purchaser units and could not close 313 of them: the tract was entered on or
# before 1 July 1835 and the T-0700 / T-0850 adjudication UPHELD the purchaser against a
# card this town holds. It handed them to this ticket and said of itself that a hand-off is
# not a spend. This pass is the spend, and it writes into `persons[].dated_bounds[]` rather
# than inventing a second shape for a dated appearance — so the block now has two owners and
# `tools/dated_bounds_block.py` is the rule that keeps them from wiping each other. It is
# gated in four directions: a bound that stops reaching its card, a card carrying a bound off
# a purchase the crosswalk never upheld, a drifted ledger, and — the one that is not about
# this pass at all — the ruling register STILL ruling the 313, which
# `research_spend_ledger.ruling_coverage_faults` fails as work that reads done and is not.
step "…and the 313 upheld land-sale purchases are bounds on the cards they name (T-1332)" \
  python3 tools/spend_land_sale_bounds.py --check

selftest "…and a purchase is a dated appearance, never a residence, and never a Chicago presence" \
  python3 tools/spend_land_sale_bounds.py --self-test

selftest "…and two owners of one block replace their own rows and nobody else's" \
  python3 tools/dated_bounds_block.py --self-test

# T-0635, consolidation pass 2. The same defect again, in the volume the window opened on:
# Fergus 1839's two LATER lists — the 1837 city-election poll and the 1839 city register —
# had matched 101 entries to people this town holds, and the second hop could not even see
# them, because both crosswalks group their rulings under the pool each was matched against
# rather than at the top of the file. This pass writes them, and it is gated in the same two
# directions as its predecessors: a ruling that stops reaching its card, and a card that
# carries the paragraph for a ruling the crosswalk never made.
step "…and Fergus 1839's later lists are on the 97 cards they name" \
  python3 tools/spend_fergus_1839_later_lists.py --check

selftest "…and that pass writes two fields, moves no grade and repeats without drift" \
  python3 tools/spend_fergus_1839_later_lists.py --self-test

# T-0636, consolidation pass 3. The Illinois State Archives' land tract sales matched 35
# purchasers to people this town holds a card for, and not one of those cards cited the
# register — the largest unwritten block the second hop could see. This pass writes them,
# and it is gated in the same two directions as its three predecessors: a ruling that stops
# reaching its card, and a card that carries the paragraph for a ruling the crosswalk never
# made. The paragraph says PURCHASE and never residence, because the register's own
# Residence column reads COOK, ILLINOIS or UNKNOWN on every one of these rows.
#
# T-0677 added a THIRD direction, because two was not enough to keep the cards right. This
# tool was rewritten between passes 2 and 3 and the earlier version is still pushed on a
# branch; running it against dev gives every one of the 31 cards a second paragraph about
# the same register, and this step was GREEN on exactly that tree. A card says the register
# once — once written twice, and once by a superseded pass left standing beside this one.
step "…and the land tract sales are on the 31 cards they name, once each" \
  python3 tools/spend_land_sales.py --check

selftest "…and that pass writes two fields, moves no grade and repeats without drift" \
  python3 tools/spend_land_sales.py --self-test

# T-0681. The third list in the same volume as the two above: the Fort Dearborn Addition lot
# sale of 10-24 June 1839, printed pages 47-49. T-0666 crosswalked its 100 bidders and 11 of
# them are people this town holds a card for; not one of those cards had been told what the
# sale says, and three cited nothing the ruling rests on at all — the ceiling T-0635 recorded
# as "T-0666's to pay". This pass writes the eleven, and it is gated in the same two
# directions as its predecessors: a ruling that stops reaching its card, and a card that
# carries the paragraph for a ruling the crosswalk never made. The paragraph says BID and
# never residence, and it says so twice — the Addition was the garrison's reservation in
# 1835 and was not platted into lots at all, so a block and lot from this sale place nobody.
step "…and the Fort Dearborn Addition lot sale is on every card it names" \
  python3 tools/spend_fergus_1839_lot_sale.py --check

selftest "…and that pass writes two fields, moves no grade and repeats without drift" \
  python3 tools/spend_fergus_1839_lot_sale.py --self-test

# T-0554. The Calumet Club's old-settlers receptions are a source SERIES read out of the
# Tribune's reprints, and the thing that goes wrong with a source like this is silent
# drift: a name hand-tidied, a quote paraphrased, a merge asserted in a file and never
# written onto the record it names. So the rolls are REBUILT from the committed
# transcription and compared, every quote is rebuilt out of the same lines, and every
# merge has to be present on the resident record it claims.
step "the old-settlers rolls rebuild from their committed transcription" \
  python3 tools/old_settlers.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/old_settlers.py --self-test

# T-0678, consolidation pass 4. The rolls above are spent onto their cards by the tool
# that builds them; Fergus's 1843 old-settler death notices were not spent by anybody, and
# 38 rulings that named a town person had never reached that person's card. The pass that
# closes that gap is checked the same way passes 1-3 are: the ledger and every card
# re-derive from the crosswalk, no card carries the block without a ruling behind it, and
# the group this pass declares ALREADY spent by tools/old_settlers.py is verified rather
# than believed.
step "Fergus's death notices are on the cards the crosswalk names" \
  python3 tools/spend_old_settlers.py --check

selftest "…and that pass writes one block, moves no grade and repeats without drift" \
  python3 tools/spend_old_settlers.py --self-test

# T-1303 (from T-1168). The two rolls above carry an age at death and an age given at the
# Calumet Club, and neither had ever reached a person's `birth_year`; 1,183 of 1,282 people
# carried no sex at all. This pass spends both, and reads a sex off a gendered title or off
# a forename that stands in one sex's naming only — never off an initial, never off a rank,
# and never off a name its own evidence splits. The forename table is DERIVED from the
# people whose sex a source records plus the period pools, so `--check` holds that it has
# not been hand-widened, and holds every card against what the pass derives from the layer
# WITHOUT its own fills — which is what stops the table reading its guesses back in as
# evidence. The tier the model owes the rest is T-1304's.
step "sex and age stand on the evidence, and the forename table re-derives" \
  python3 tools/spend_person_sex_age.py --check

selftest "…and an initial, a rank and an ambiguous forename still fire nothing" \
  python3 tools/spend_person_sex_age.py --self-test

# T-1170. The kin survey lands a tie only where BOTH ends are people this town holds, and
# its own count says what that leaves: twelve relatives OF A HEAD THIS LAYER CARRIES who
# are nobody in the dataset. A second reading is needed to see the rest, because the period
# prints a wife as a marriage — 'married Welthyan Loomis 30 October 1808' — and the survey's
# `<relation> of <Name>` pattern cannot see one. This pass reads both, and every statement
# it reads is answered in data/residents/stated_family_rulings.json by somebody who has read
# the source. It writes the members a source NAMES and refuses to reconstruct: the ones a
# source merely COUNTS are the programme's, on the other side of the refusal gate above.
step "every family member the sources name is ruled on, and the ruled writes are on the cards" \
  python3 tools/spend_stated_families.py --check

selftest "…and an unruled statement, a lost write and a stale report all still fire" \
  python3 tools/spend_stated_families.py --self-test

# T-1320. Both passes above read the CARDS. Neither has ever read data/research/books/ —
# nine committed books, 267 adjudicated claims — for the kinship the books state, so a
# book sentence only reached a card when somebody happened to quote it onto one. This
# pass reads them, resolves both ends through the books' own crosswalk and by nothing
# else, and answers every claim that states kinship in
# data/research/books/kin_rulings.json. It mints nobody: a relative who was never in this
# scene is EVIDENCE and not structure, which is validate.py's own rule for a kin row.
step "every kinship the book corpus states is ruled on, and the ruled ties are on the cards" \
  python3 tools/spend_book_kin.py --check

selftest "…and a half brother flattened to a brother, a one-sided tie and a lost claim all still fire" \
  python3 tools/spend_book_kin.py --self-test

# T-0992. T-0962 widened the second hop to read the `matched` container and church entered
# that report for the first time: 83 rulings reached a person this town holds a card for and
# NOT ONE card cited the roll. The pass that closes that gap is checked the way every other
# spend is — the ledger and every card re-derive from the crosswalk, no card carries the
# paragraph without a matched ruling behind it — plus the line this source needs most: the
# 37 ambiguous and 330 refused rows are rivals still standing, and a card one of them names
# may never carry this pass's words.
step "the Second Presbyterian roll is on the cards its crosswalk matches" \
  python3 tools/spend_second_presbyterian_roll.py --check

selftest "…and that pass spends no refusal, moves no grade and repeats without drift" \
  python3 tools/spend_second_presbyterian_roll.py --self-test

selftest "…and its own assertions still fire when broken" \
  python3 tools/research_domains.py --self-test

# T-0557. The Illinois State Archives' land tract sales are the first source this project
# reads that is not about people at all — it is a register of TRANSACTIONS, and the way it
# goes wrong is by being read as a census. A purchase says a man bought ground; only the
# register's own Residence column says where he lived, and it names a county. So the
# reading is rebuilt from the committed deposit and diffed, the grade a row carries has to
# follow from that column rather than from the buying, and the three sections the
# database truncated at its own 150-row ceiling must never appear in the coverage
# declaration — a ceiling recorded as a completed read is the one error here nothing
# downstream could catch.
# T-0697. THE RULE THE RESIDENT CROSSWALK IMPORTS RATHER THAN RESTATES, gated for the
# same reason T-0696 gated the directories' two: the crosswalk below is re-derived here
# and the rule it is re-derived BY was not, so a loosened namesake rule — one more name
# folded onto another, M3's guard dropped, a suffix read as decoration — would re-derive
# the crosswalk quietly and pass every check after it.
selftest "the namesake rule's own assertions still fire when broken" \
  python3 tools/namesake.py --self-test

step "the land tract sales re-derive from their committed deposit" \
  python3 tools/read_land_sales.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_land_sales.py --self-test

# T-1124. …AND THE ONE QUESTION EVERY STEP ABOVE IS STRUCTURALLY UNABLE TO ASK: is a
# judgement simply GONE? `--check` above asks whether each surviving ruling is WELL
# FORMED, and on #1055 they all were — the eight that were left after a merge lap ate
# forty re-derived perfectly into a crosswalk perfectly consistent with them, and this
# gate was green on that commit and on every commit after it. A smaller rulings file is
# a legal rulings file. Twelve resident cards silently got back a federal land purchase
# each had been ruled it could not have, and the only witness was prose.
#
# So this compares the tree against the MERGE BASE rather than against anything the tree
# carries, by identity and by count, with `ruled[]` and `retired[]` counted together so a
# retirement is a move rather than a loss. A deliberate removal is still possible and
# states itself: the entry moves into `withdrawn[]` carrying its reason and its ticket.
step "no land-sale ruling has left the file without saying so" \
  python3 tools/check_rulings_not_lost.py

selftest "…and its own assertions still fire when broken" \
  python3 tools/check_rulings_not_lost.py --self-test

# T-1017. A ruling about a KIND OF ARGUMENT, and the only one in this domain that rests on a
# measurement rather than on a page. T-0990 refused RUSSELL SAMUEL and SKINNER JOSEPH while
# recording that the rows are at the town's own school-section sale — an argument it filed
# rather than used. T-1017 answers it by counting, and the answer is no: the sale is enriched
# in town-side names and cannot separate two bearers of one, so it is a prior over a
# population and not a check on a row. The figures behind that move whenever a ruling is made
# or the residents layer grows, which is exactly why they are asserted here and not merely
# printed. If the sale ever ceases to be non-exclusive, ceases to be minority-upheld, or
# ceases to print a surname twice, this step goes red naming the arm that failed and the
# question reopens — rather than the ruling standing on a measurement that moved under it.
step "the school-section sale still reads the way T-1017 ruled it" \
  python3 tools/school_section_sale.py --check

selftest "…and all three arms of that ruling still fail when broken" \
  python3 tools/school_section_sale.py --self-test

# T-1001. The surname fold is EXACT, and the measurement that says it should stay exact
# is the only thing standing between this domain and a fold that looks kinder and costs
# 24 correct matches. The counts move whenever the residents layer grows, so they are not
# gated for equality — what is gated is the distance function they rest on and the fact
# that the measurement still runs at all. A one_letter_apart() that quietly stopped
# firing would report "no cost" and read as a licence.
selftest "the surname-fold measurement still measures something, on a distance that holds" \
  python3 tools/measure_surname_fold.py --self-test

# T-0609. The register describes a tract; the structures carry a footprint; the join
# between them is a CONSTRUCTION, not a trace — the PLSS grid is carried from the single
# committed corner at State & Madison on the plat's own bearing (L219). Two things can go
# wrong silently and both are held here. A hand-edited `land_owner` block would be a
# statement about who owned ground that no longer follows from the register, and a
# structure that MOVES would keep an owner it no longer stands under; --check re-derives
# every block from the entries and the committed positions and refuses either. The
# self-test holds the grid itself: that the four sections still meet at G1, that a
# quarter still measures 160 acres, that a void entry confers nothing, and that the 150
# school-section rows still refuse for the plat this repo does not hold.
step "the land tracts still resolve to the same ground, and the same roofs stand on them" \
  python3 tools/resolve_land_tracts.py --check

selftest "…and the section grid's own assertions still fire when broken" \
  python3 tools/resolve_land_tracts.py --self-test

# T-0571. Fergus's 1843 directory is the earliest complete Chicago directory this project
# can reach, and its two halves are segmented by two different rules — the shouted head of
# a trade card on page 1, the current letter section on pages 2-4 — because the printer set
# them differently and the web transcription this repo holds does not indent a turned line.
# A segmenter that quietly loses forty entries is invisible to every other gate here, so the
# reading is REBUILT from the committed text and compared, and the per-page counts are held
# to what coverage.json declares. The crosswalk is rebuilt the same way: it is a proposal
# that changes no resident record, and a hand-edit of a proposal is how one becomes a fact
# nobody decided.
step "Fergus's 1843 directory rebuilds from its committed text, at the declared counts" \
  python3 tools/read_fergus_1843.py --check

# T-0987 stretch 12. The compositor set a POINT where the format sets the comma that
# closes a surname, and the crosswalk reaches an 1835 person through the surname and
# nothing else — so `Cook. George` made no match AND no refusal, and left no trace in
# any pool. Twenty-five are repaired in the READING against the Internet Archive's OCR
# of the printed volume, which this repository already held; the quote keeps the damage.
# The table is what rots: a re-committed page, a moved segmenter, or a new run-on with
# no row. The self-test fails on any of those, and on a repair that tidied a quote.
selftest "…and every run-on surname in it is repaired against the printed volume, or said" \
  python3 tools/read_fergus_1843.py --self-test

step "…and its crosswalk to the 1835 residents rebuilds too" \
  python3 tools/crosswalk_fergus_1843.py --check

# T-0589. The CIVIC ACCOUNT above that directory, on the same page: the officers and
# courts, the churches and societies with their memberships, the newspapers, the mails,
# the fire and military companies, the schools, the ward population count of 1 August
# 1843 and the port's trade. Three shapes on one range — a wrapped line, a heading that
# is not a claim, and three tables the transcription runs down the page one cell to a
# line — so the same guard as the directory's: the reading is REBUILT from the committed
# text and compared, and the count is held to what coverage.json declares. A segmenter
# that quietly rejoins the population table's rows off by one would be invisible to
# every other gate here.
step "Fergus's 1843 civic account rebuilds from its committed text, at the declared count" \
  python3 tools/read_fergus_1843_civic.py --check

# T-0506. Fergus's 1839 directory — the closest address list to 1835 this project can
# reach, and until now cited only through somebody else's web transcription. Same three
# gates as 1843's, for the same reason: a segmenter that quietly loses forty entries is
# invisible to every other check here, a hand-edited proposal is how a proposal becomes a
# fact nobody decided, and the street face compiled off it is what the street tickets will
# read. The third one also guards the compiler's own warning — that every address number
# in the volume off Lake street is an 1876 number — which is carried per row and would
# otherwise be a sentence in a README that nothing enforces.
step "Fergus's 1839 directory rebuilds from its committed text" \
  python3 tools/read_fergus_1839.py --check

# T-0987 stretch 13. Seven surnames the scan broke in two or the printer's comma left
# out are repaired against a committed witness, and this is the ratchet on the table:
# a row that stops firing, a repair that tidies its own quote, or an EIGHTH broken
# surname arriving with no row is invisible to every reader until this fails.
selftest "…and the seven repaired surnames in it still read off their witnesses" \
  python3 tools/read_fergus_1839.py --self-test

step "…and the trade table counted off it rebuilds too" \
  python3 tools/build_trade_table_1839.py --check

# T-1346. The table is a PRIOR the reconstruction will draw a head's trade from, so
# the rules that build it are load-bearing in a way a share never looks. Its own
# assertions pin the four that would be invisible if they broke: the slot is cut at
# the first comma so an employer never becomes a trade, the scan's five broken
# trades are repaired by name, a bare house-word is the trade while a house carrying
# a proper name is not, and mapped + refused still equals the entries with a printed
# trade — a normaliser that silently drops what it cannot read is how a share becomes
# a fiction.
selftest "…and the trade table's own reading rules still fire" \
  python3 tools/build_trade_table_1839.py --self-test

step "…and its crosswalk to the four pools of 1835 names rebuilds too" \
  python3 tools/crosswalk_fergus_1839.py --check

step "…and the 1839 street face compiled off it rebuilds too" \
  python3 tools/fergus_1839_street_faces.py --check

# T-0664. The next seven pages of the same volume, printed 40-46: the charter election of
# 2 May 1837 and its list of voters for mayor. A poll list is the easiest source in this
# repository to lose a column of — the page is set in four columns, the OCR does not read
# them in printed order, and a segmenter that drops one loses forty men without changing
# any other number here. So the reading is rebuilt from the committed text AND held to the
# per-leaf counts coverage.json declares, which is the guard T-0571 put on the 1843
# directory for the same reason. The crosswalk is rebuilt the same way: it is a proposal
# that changes no resident record, and a hand-edit of a proposal is how one becomes a fact
# nobody decided.
step "the 1837 charter election rebuilds from its committed text, at the declared counts" \
  python3 tools/read_fergus_1839_election.py --check

step "…and its crosswalk to the four pools of 1835 names rebuilds too" \
  python3 tools/crosswalk_fergus_1839_election.py --check

# T-0667. That poll's first ward reads 167 names against Fergus's own table of 170, and the
# claims file could only say the page images would have to settle it. They did:
# verify_fergus_1839_first_ward.py counts LINES OF TYPE on printed pages 41-42 — a name the
# OCR lost leaves no trace in the text and a double gap in the row grid — and found 167 set on
# a leading that never doubles. The measurement needs Pillow and archive.org, so what runs
# here is the leg that needs neither: the committed record and the committed claims file must
# still agree on 167, per leaf. They are two files that drift apart silently otherwise.
step "…and the first ward's 167 names still agree with what the page images were counted at" \
  python3 tools/verify_fergus_1839_first_ward.py --offline

# T-0665. The two leaves BETWEEN the directory and the poll, printed 38-39: the city
# register of 1839 and the printed tables of mayors and sheriffs. Three things need
# holding here that the poll pages did not need. The SEGMENTING, because the register
# sets all six wards of an office in one semicolon-separated run wrapped over three
# printed lines and breaks a surname across a line end, so a rule that loses a ward
# loses a man and changes no other number in this repository — the per-leaf counts
# coverage.json declares are the second opinion. The YEAR COLUMN, because seven of its
# rows are OCR damage repaired from an explicit map, and a year quietly guessed would
# move a man's office by a term; the tables' own ascending order is what checks the
# repairs, and the ex-officio coroners are held to the gap they are printed in. And the
# DERIVATIONS, because the only two statements these pages make about 1 July 1835 are
# not printed on them — who the sheriff was, and that the town had no mayor at all —
# and a derivation that lost its refusal would be this project's inference wearing a
# citation. The crosswalk is rebuilt the same way, for the reason the poll's is: it is
# a proposal that changes no resident record, and a hand-edited proposal is how one
# becomes a fact nobody decided.
step "the 1839 city register and the mayor and sheriff tables rebuild from their committed text" \
  python3 tools/read_fergus_1839_register.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_fergus_1839_register.py --self-test

step "…and its crosswalk to the four pools of 1835 names rebuilds too" \
  python3 tools/crosswalk_fergus_1839_register.py --check
# T-0666. The last four pages of the same volume, printed 47-50: the Fort Dearborn
# Addition sale of 10-24 June 1839, and the volume's own population table. Both are set
# in columns and the OCR does not read a columned page in printed order — its flat text
# puts one man's price against another man's lot, and sets 1863 under 1849 — so the rows
# are put back from the scan's word coordinates by a committed row map, and every cell in
# it names the spans of committed page text it is made of. That map is the thing worth
# gating: a span shifted by one line hands two hundred lots to the wrong bidders and looks
# exactly like a reading. Two checks catch it, and they are independent. This one rebuilds
# both claims files offline out of the committed text and the map and diffs them;
# research_domains.py --check, already run above, rebuilds every quote in them THROUGH
# those same spans, so a map that points at the wrong ink cannot produce a quote that
# matches. The self-test asserts the three rules that do the reading's judging — that a
# mark in the bidder column is a ditto only where a price is printed, so the printer's
# brace over a block of reserved lots is not read as the man above; that a block number is
# carried only while the lot numbers keep rising; and that a numeral the scan destroyed is
# null and never recovered from its neighbours.
step "Fergus 1839's Fort Dearborn lot sale and population table rebuild from the committed text and row map" \
  python3 tools/read_fergus_1839_lots.py --check

selftest "…and the three rules that judge that reading still fire when broken" \
  python3 tools/read_fergus_1839_lots.py --self-test

step "…and the bidders' crosswalk to the pools of 1835 names rebuilds too" \
  python3 tools/crosswalk_fergus_1839_lots.py --check

# T-0588. The dating pass over Norris's 1844 firms is a measurement whose ANSWER IS NO —
# no printing this project holds dates any of the 207 firms at or before 1835, so nothing
# was written to the businesses layer. A negative result is the easiest artefact in the
# repository to corrupt: nobody re-reads it, and a hand-edit that promotes one firm to
# "dated 1834" would put a business in the town on nobody's authority. So the whole file
# rebuilds from its four committed inputs and diffs, and the rules it rests on — that the
# sketch route reads the printed quote and never this project's own gloss, that a
# one-surname firm needs an agreeing initial, that a founding year has to be carried by
# founding language — are asserted with cases that fire.
step "Norris's 1844 firms re-derive their dating against 1835" \
  python3 tools/date_norris_1844_businesses.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/date_norris_1844_businesses.py --self-test

# T-0556. An INVENTORY of a website is the one research artefact that rots silently: it
# is a set of judgements about pages nobody will open again, and the only way to notice
# that a section was quietly dropped from it is to go and re-walk the site. So the county
# index page is committed RAW beside the readable cache, and this re-extracts its links
# and refuses an inventory that has no row for one of them — the ticket's acceptance
# ("covers every section the index links, none skipped silently") as an assertion rather
# than as a hope. It also rebuilds every quote the assessment filed in passing out of the
# committed text, because a quote from a website is a quote from something that can change
# under you.
# T-0574. Fergus's list of the deaths of Chicago's old settlers, and the one source this
# project holds that carries AGES AT DEATH — which are birth years, by subtraction this
# project does and the page does not. Two things need holding. The segmenting, because the
# transcription wraps a long entry without indenting the turn and the rule that tells a turn
# from a man is delicate: "Oct. 12, 1877" under O is the tail of Daniel O'Hara's entry, and a
# rule reading the section letter alone made a new man of the month. And the GRADE, because
# an arithmetic birth window that quietly became `documented` would be this project's own
# invention wearing a citation. The gate rebuilds both files out of the committed text, holds
# the count to what coverage.json declares, and refuses a record that claims the scene year
# or grades a derived birth above `inferred`.
step "Fergus's old-settler death notices rebuild from their committed text" \
  python3 tools/read_fergus_obits.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_fergus_obits.py --self-test

step "the Genealogy Trails inventory covers every section the county index links" \
  python3 tools/read_genealogytrails.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_genealogytrails.py --self-test
# T-0562. The seventh domain, and the one that needs a gate of its own. The Newberry
# Library's genealogical index is a FINDING AID: a card heads a family surname and names
# the book that treats it, and it never places a person anywhere. Its whole failure mode
# is that a surname in it looks like evidence, so the assertion that matters here is the
# last one — the source id may not appear behind a resident, a household or a building.
# The rest holds the reading honest: every `as_read` is rebuilt out of the committed
# card text, the committed text is held to the sha256 the extraction recorded, no record
# may be graded above `transcription_mediated`, and the hand-adjudicated precision sample
# must still be adjudicating cards that are actually in the records.
step "the Newberry index stays a finding aid, and its reading rebuilds from the cards" \
  python3 tools/read_newberry_index.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_newberry_index.py --self-test
# T-0590. The reading above is worth nothing until somebody rules on what it offered.
# Volume 1 put up 319 leads and made 0 merges, and a lead nobody has answered reads
# exactly like a lead nobody has looked at. The rulings are derived, not authored, so
# the gate that matters is that the file still re-derives: a hand-edited outcome, a
# lead that stopped being ruled on, or a merge appearing in a finding aid's crosswalk
# all fail here rather than in a spend measure three weeks later.
step "every Newberry lead is ruled on, anchored, and re-derives from the cards" \
  python3 tools/rule_newberry_leads.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/rule_newberry_leads.py --self-test
# T-0572. The 134 Black Hawk War veterans who enrolled AT CHICAGO in 1832. Two
# assertions carry this one. First, the reading is taken from the CACHED PAGE and not
# from the flattened text, because the flattening drops an empty cell and 94 of the 134
# rows leave the Rank cell empty — read from the text alone, `INDIAN` could be the rank
# or the company and nothing on the page would say which. Second, 83 of the 134 names
# carry no surname comma (the French and Potawatomi forms), so the parse anchors on the
# table row and the gate fails if that count moves: a comma filter would silently drop
# exactly the part of this town the reconstruction is least able to lose.
step "the Black Hawk War enrollments read 134 rows and keep the 83 without a surname" \
  python3 tools/read_blackhawk_war.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_blackhawk_war.py --self-test

# T-0573. Father St. Cyr's marriage register and his death page, the first Chicago
# church record. The assertion that carries this one is the page's OWN ARITHMETIC: the
# article prints its tally by priest — St. Cyr 22 marriages, Schaeffer 18, O'Meara 87,
# Plunkett 1 — and the parse of the entries returns exactly those four numbers
# independently. Nobody here has seen the register or the Review, so that agreement is
# the only check this reading can have, and it fails if any of the four moves. The other
# one is the trap the ticket named: footnote 5 puts three of the first four entries at
# Bear Creek, Sangamon County, not Chicago, and those rows carry it themselves.
step "St. Cyr's register reads 128 marriages against the article's own 22+18+87+1" \
  python3 tools/read_st_cyr_register.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_st_cyr_register.py --self-test

# T-0503, gated by T-1110. The same priest's BAPTISMAL register, read off the eleven
# deposited page images — the only primary record this project holds that names a family
# together. Three assertions ride on this one `--check`: the book's own pencil tally for
# each year (19 + 24 + 14) against the entries read, so a lost or invented entry shows;
# every declared image reached and no image reached that the deposit does not hold; and
# the three emitted JSONs still being exactly what the table in the tool says.
#
# WHY IT WAS NOT GATED UNTIL NOW, because the answer is the point. The crosswalk has a
# SECOND input — data/residents/ — and that layer grew from 849 people to 1,308 after the
# pass was written, so the committed file stopped matching a rebuild without anybody
# touching either it or the tool. T-1110 read the diff, named the cause as staleness
# rather than a hand edit, and rebuilt. This step is what stops it happening silently
# again: the town gaining a resident now fails HERE, in the commit that adds them, and
# the answer is `--build` in that same commit.
step "the St Mary's baptismal register still rebuilds, tallies and all" \
  python3 tools/read_st_marys_baptisms.py --check

# T-0583. The 1842-1892 roll of the Second Presbyterian Church of Chicago — the work
# fifty-four Newberry index cards cite and this project did not hold. Two things are
# gated. First, the COLUMNS: archive.org reads a four-column table in the order the
# scanner met the ink, so the reading is rebuilt from the committed row map's spans into
# the committed text, and a span that points at the wrong ink fails here. Second, the
# LADDER: the roll opens in June 1842, seven years after the scene date, so no line on it
# can be an 1835 fact — the self-test asserts every record says so and that nothing dated
# on or before 1835-07-01 has reached one.
step "the Second Presbyterian roll rebuilds, and no line of it is an 1835 fact" \
  python3 tools/read_second_presbyterian.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/read_second_presbyterian.py --self-test

selftest "…and its own assertions still fire when broken" \
  python3 tools/newspaper_corpus.py --self-test

selftest "the .docx extractor is deterministic and keeps its uncertainty brackets" \
  python3 tools/docx_text.py --self-test

# T-0257. The corpus made the papers citable; this is what a READING out of them looks
# like once it has been made, and the gate that keeps one honest. The assertion worth
# knowing about: a claim names the exact transcription lines its quote is built from,
# and this reassembles the quote out of the transcription and refuses any that differs
# by a character. "Never silently smoothed" is otherwise a hope — a tidied quote is
# invisible to every other check here, and the smoothed reading has a field of its own
# (`normalized`) to live in. gazetteer.json is GENERATED, so this also refuses a
# hand-edit to it, the same way the board and the published mirror are refused stale.
step "every newspaper claim resolves, quotes verbatim, and the gazetteer is compiled" \
  python3 tools/compile_gazetteer.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/compile_gazetteer.py --self-test

# T-0901. THE OCR'S TURKISH ALPHABET. Seven readings in the corpus carried ı, İ or Ğ
# — letters Turkish has and the Latin alphabet this project transcribes does not, and the
# signature of an OCR run whose language model was Turkish rather than of anything a
# compositor set in 1835. They repair to their base letter, demonstrated three ways: the
# repair turns `KİNZIE` into the name every other impression sets, `WRİĞHT` into the
# WRIGHT that claim's own notes already called a spurious breve, and `Benjamın Swena` into
# the `Benjamin Swena` T-0299 had ALREADY ruled the same entry of the same list. The gate is
# here rather than in the repair because the defect ARRIVES with a reading: a card carrying a
# character no hand wrote was refused against its own directory entry for three weeks before
# anyone read the card. A `quote` and a claim's `notes` keep the letter — the quote because
# it is the transcription character for character, the notes because they quote the artefact
# to explain a correction.
step "no reading carries a letter of the OCR's Turkish alphabet" \
  python3 tools/repair_ocr_turkish_alphabet.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/repair_ocr_turkish_alphabet.py --self-test

# T-1006 (of T-0988). The December 1835 State census counted the town BY CLASS — forty-four
# stores, eight taverns, twenty-two lawyers — and the register's `trade` is free prose off
# the printed notice, 152 distinct strings for 206 businesses. There was no class to count
# against, so the denominator this project had held since T-0581 read `bk_mose1_006` could
# not be set against anything. The class is ruled once per printed string in
# data/research/newspapers/trade_class_rulings.json; this re-derives the comparison from
# the register and the rulings, and it fails on the one thing that must never pass quietly:
# A BUSINESS NO RULING COVERS. A new notice extracted next week brings a trade string with
# it, and an unruled string would leave that house out of the count with nothing said.
step "every business carries a census class, and the December 1835 count re-derives" \
  python3 tools/trade_census_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/trade_census_1835.py --self-test

# T-1048 (of T-1047, of T-1040). `in_town_places()` resolves a place string against the bare
# town, the committed 1835 streets and the committed structure names — and 193 of the
# gazetteer's 2,665 persons carry nothing that resolves. The list is NOT 193 out-of-town men:
# `Fort Dearborn`, `Water Street`, `the Mansion House` and `the corner of Water and Franklin
# streets, Chicago` are all in the town and all fail it. So the vocabulary is resolved once
# per printed string in data/research/newspapers/place_vocabulary.json — derived against the
# committed dataset where it can be, ruled with its reasoning where it cannot — and this holds
# that resolution to both ends: A STRING THE PAPERS PRINT AND NOBODY HAS RESOLVED, which is
# what a newly extracted notice brings next week, and A DERIVATION THE DATASET NO LONGER
# MAKES, which is what renaming a street or a building does to it. It also restates every
# count in the file, so the measurement T-1049 argues from cannot go stale unnoticed.
step "every place the newspapers print is resolved inside the town, outside it, or undecided" \
  python3 tools/resolve_place_vocabulary.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/resolve_place_vocabulary.py --self-test

# T-1007 (of T-0988). The other half: SPENDING the gap T-1006 measured. The business
# register is compiled from printed NOTICES, so its four physician records were four
# physician advertisements — and five more doctors sat on resident cards off Andreas and
# the Democrat with no business record at all, because a physician need not advertise.
# This joins the two layers, records the Lyceum and the Reading Room as institutions with
# no building, and holds the bank and the lottery office as documented absences. It fails
# on the two omissions that would quietly shrink the town: a register record on a spent
# class that no ruling claims, and a resident card whose trade the count cannot see. It
# also refuses a roof for the Lyceum, which is the one thing T-1007 forbids outright.
step "the trade-census gap is spent from the layers that hold it, and nobody is invented" \
  python3 tools/trade_census_spend_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/trade_census_spend_1835.py --self-test

# T-1293, WHICH FOLDS T-1161 THROUGH T-1165. The step above compares the town to ONE
# count of the trades. This is the whole model the reconstruction bands spend: population,
# occupations, households, lodging and arrival, each figure a RANGE with its method and a
# named comparandum, derived from files this gate already holds — the town census, the
# authored roof programme, the T-1006 crosswalk, the 1840 composition and the Old Settlers
# roll. It reads no page and it names nobody; `--self-test` refuses a build that does.
#
# WHY A GATE AND NOT A DOCUMENT. Every figure is a function of a file that MOVES: the
# arrival distribution is recomputed whenever the resident layer is, and the population
# floor is derived from it. Left ungated, the model would go quietly stale against its own
# inputs while reading as a finished decision, which is the failure the order book (T-1166)
# can least afford — it is the quota bands 3-5 build to.
#
# The refusals worth knowing: an inverted range, a figure with no method or no file behind
# it, a point reading outside its own bounds, a section that takes more than one sentence
# to say what it is not claiming, and an EMPTY arrival distribution — which would otherwise
# return the November ceiling at both ends and stop being a range while still looking like
# one.
step "the 1835 town model re-derives, and every figure is bounded and says what it rests on" \
  python3 tools/model_town_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/model_town_1835.py --self-test

# T-0440. A house is minted from whichever printing the corpus carries first, and it took
# `placement` and `street` from it — so a standing advertisement that ran without an
# address in its first week and with one afterwards stood at `{"class": "none"}` for good
# and read `unplaceable` in the register while three of its own printings said otherwise.
# Fourteen houses of 206 were in that position, Clark, Filer & Co. among them. The repair
# is in `compile_gazetteer` and its self-test above; this is the standing count, and it
# fails only on the one thing the repair must never allow back: a live placement that
# places nothing while a printing of the same house, on or before the scene date, places
# it. The other two populations the report prints are NOT failures — a printed address
# outranked by another printed address is `anchor_changes`' judgement to make, and a
# house placed only after the scene date is the bound working.
step "no house is placed by a printing that gave no address" \
  python3 tools/measure_placement_silence.py --check

# T-0305. Four times in its thirteen issues the Chicago American contradicts ITSELF about
# a street, or prints one and loses the cross street that would locate it — the tailor's
# Franklin-or-Lake, which Water street Wm. Sabine and John Dave[s] stood in, and the corner
# of S. B. Cobb's saddlery. None of the four is closeable from the material this repository
# holds: the page images are held outside it, and three of the four subjects appear nowhere
# in the Democrat but a post-office letter list. So the four are DECLARED — each printing
# by claim, page, column and the exact substring it has to carry — and re-derived here,
# along with the negative half over all 73 Democrat issues. The day one of them is answered,
# by an image or by an extraction pass reaching a card nobody has read, this says so instead
# of docs/RESEARCH/american_self_contradictions.md going quietly out of date.
step "the American's four self-contradictions still read as declared" \
  python3 tools/measure_american_contradictions.py --gate

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_american_contradictions.py --self-test

# T-0262. The gazetteer says what was PRINTED; the register says what the town has to
# do about it — for every business an action and, where the action needs one, a
# committed target; for every person whether the town already holds them, invented a
# stand-in for them, or has never heard of them. It is DERIVED from the gazetteer and
# the committed dataset, so this refuses a hand-edit for the same reason the gazetteer
# gate does: a hand-edited register is a place to promote a business into the town
# without an argument, and the seeding tickets read it as if it were derived.
step "the scene-date register re-derives, and every action names its target" \
  python3 tools/compile_register.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/compile_register.py --self-test

# T-1310, of T-1180. AND WHERE A BUSINESS IS ACTUALLY WRITTEN DOWN. The register is a
# reading of the newspapers; data/businesses/ is the layer that reading compiles into,
# where a house of trade carries a tier on every field, the people it names carry a link
# to a town card or a stated reason there is none, and the 61 street-only and 62
# unplaceable businesses carry their LIMIT as a location kind rather than as prose in an
# action note. Compiled, never authored, for the same reason as the two files above: a
# hand-edited record is a place to promote a business — or a proprietor, or a premises —
# without an argument.
step "the business layer re-derives, and every register row has a record" \
  python3 tools/compile_businesses.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/compile_businesses.py --self-test

# T-1402, of T-1182. AND WHETHER THE DERIVATION SAYS WHAT THE RESEARCH SAYS. The step
# above asserts one thing — that a rebuild reproduces what is committed — and it is
# silent on whether the layer honours the rulings it was built out of. identity.json
# rules that two printed spellings are one house or one man, trade_class_rulings.json
# rules the December 1835 census class of every trade, and the register brackets four
# houses that moved. This reads all 196 records back against those, field by field, and
# refuses the report it derives if anyone hand-edits it or a ruling stops being honoured.
step "the business audit re-derives, and every identity ruling still holds" \
  python3 tools/audit_businesses.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/audit_businesses.py --self-test

# T-1404, of T-1182 clause 3. AND WHETHER EVERY IN-WINDOW TRADESMAN HAS SOMEWHERE TO WORK.
# 47 dated roles reach 1 July 1835 on people the business layer held no workplace for — a
# blacksmith with no smithy, five physicians against three offices. This raises an
# `inferred` house for each trade the premises rulings say implies one, folds two keepers
# of one household's trade into one house, HOLDS a candidate the register may already have
# printed under a name it could not match, and says `no_fixed_premises` on the role where
# the trade never had premises of its own. It reconstructs nothing: what the December
# census still counts short stays short, in the order book, for T-1186.
step "every in-window trade has a workplace or a stated reason it has none" \
  python3 tools/complete_inwindow_trades.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/complete_inwindow_trades.py --self-test

# T-1184, the first group of the business reconstruction band. The December 1835 State
# census counts classes the newspaper register does not hold — four druggists against two
# — and the order book turns each of those gaps into a quota with the ticket that owes it.
# This writes the houses that fill them: a period firm style dealt from the forms the
# register itself prints, a `street_only` face that claims no lot and no roof, and a
# proprietor ADOPTED from the resident band's reconstructed trade heads rather than minted,
# so the two bands fill one quota instead of ordering the same druggist twice. What the
# gate holds: that every record re-derives from its seed string, that the order book's
# `filled` counter carries this build's fill, that no invented style collides with one the
# register prints, and that no reconstructed house cites a source. A hand-edited record
# fails here; docs/LIBERTIES.md § L254 carries the invention.
step "every reconstructed business re-derives, and no invented style is a printed one" \
  python3 tools/reconstruct_businesses_1835.py --check

selftest "…and an unmapped class, a quota past its heads and a borrowed style are refused" \
  python3 tools/reconstruct_businesses_1835.py --self-test

# T-1441, of T-1190 clause 2 and clause 3. AND WHETHER THE SUBSTITUTION PROMISE IS KEPT.
# Every reconstructed record says what would retire it, and until now nothing could answer
# that question with the parts of a retirement the record does NOT carry: the order-book row
# that re-opens, the roof that is carried rather than demolished, the liberty whose count
# moves. `--dry-run` reads that plan for a candidate source and writes nothing ever; this
# holds the population it reads. Two assertions: every reconstructed firm and trade head
# still states its own retirement, and each liberty entry's share of the 32 houses agrees
# with the firms on disk. compile_liberties re-derives the POPULATION and cannot re-derive
# the SHARE — a firm carries the ticket that built it and a liberty carries no ticket — so
# a group rebuilt one house larger used to leave a word like FIFTEEN standing over sixteen.
# docs/PROVENANCE.md § Substitution is the rule.
step "every reconstruction says what retires it, and each liberty's share of the firms re-counts" \
  python3 tools/substitute_reconstruction.py --check

selftest "…and the match, the retirement plan and the share re-count each fire when broken" \
  python3 tools/substitute_reconstruction.py --self-test

# And what the town DOES with the register's `street_only` businesses (T-0354). The owner
# ruled on 2026-08-29 that a business the paper places on a platted street and nothing
# narrower adopts a reconstructed roof already standing on that street face;
# docs/STREET-FACE-ADOPTION.md is the policy and this re-derives the allocation. Gated
# rather than committed once because all four of the ruling's limits are assertions about
# a moving town: a roof that gets promoted, a roof that becomes a household's dwelling, a
# second business landing on one roof, or a record that quietly grows a lot field are each
# a silent breach of the ruling, and each one fails here. `--report` prints the deal, every
# refusal with its reason, and both readings of what "standing on that face" means.
step "the street-face adoptions re-derive, and no adopted business claims a lot" \
  python3 tools/adopt_street_faces.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/adopt_street_faces.py --self-test

# T-1237, the first piece of T-1147. The two steps above each answer one half of "where
# is this business", and the household layer answers "where does this family live" in a
# third place again — so a run that wanted the address book had to re-adjudicate all
# three. These rows are that join, derived: one row per home, workplace and
# business-location claim, carrying the street, face and anchor its evidence reached and
# the `limit_clause` that stopped it. T-1198's seating pass starts from the rows rather
# than from the evidence, which is why the clause is a FIELD and not prose.
#
# Gated rather than committed once, for the same reason the two steps above are: the
# counts it publishes are the location axis T-1157 reads at the research sign-off — 56
# businesses on a roof, 61 on a street face, 62 unplaceable; 20 households on a roof, 52
# in a division and 1,185 nowhere — and each of those is an assertion about a moving
# town. A business that quietly acquires a roof, a refused later address that acquires a
# street, or a row that loses the clause limiting it are each a silent breach, and each
# one fails here. `--report` prints both axes.
step "the location reconciliation rows re-derive, and no row resolves past its evidence" \
  python3 tools/location_reconciliation.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/location_reconciliation.py --self-test

# T-1239, the third piece of T-1147, and the ADJUDICATION of the rows above rather than a
# second reading of the evidence. It owns two of the parent's clauses.
#
# CLAUSE 3 — placement proportional to evidence — had two facts wearing one field. Forty of
# the 61 street-only businesses stand under a roof, because the owner's street-face adoption
# ruling of 2026-08-29 seats them there; clause 3 says a street-only business claims no roof.
# Both are true, of different things: the PAPER reached the street, the TOWN chose the roof.
# This step holds them apart — `evidence_reach` never climbs to the seat, every adopted seat
# is `seat_is_substitutable`, and an adopted roof that hardens into a claim fails here.
#
# AND IT SPLITS A NUMBER THAT WAS OVERSTATING ITSELF. The published axis says 56 businesses
# reach a structure; 11 of those reach a structure the town has not built (the register's
# `new_building` action, whose `action_target` is another business or a corner and not a
# structure id). 56 is right as an evidence metric and wrong as a completion metric, so both
# are published — 45 committed, 11 pending — and the gate refuses a pending roof that
# acquires a seat. NOTHING moves between the three published limits: clause 4 says they fall
# only on a new source, and this pass reads none. That is asserted, not merely reported.
#
# CLAUSE 4 — the four standing questions T-0251, T-0305, T-0386 and T-1087 — is why this is
# a gate at all. All four are RETAINED, none is the loop's to resolve, and a retention
# written as prose goes quietly out of date the day its subject changes. So each carries a
# guard measured from the committed data: the church's refusal note, the saddlery's watch
# entry, the Montgomery entries and the absence of a Carver building, the two undecided B4
# places and their person buckets. The day the owner rules, the guard stops holding and this
# step SAYS SO instead of the file lying. That is T-0305's own clause 5, applied to all four.
step "the location spend re-derives: no placement past its evidence, four retentions still true" \
  python3 tools/location_spend.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/location_spend.py --self-test

# T-1491. THE ADDRESS BOOK IS THE SPEND'S OTHER HALF, and it is gated for the same reason:
# it says where every known household and firm stands, and the whole of its value is that it
# never says more than the evidence does. Three limits carry the weight. A row at the `owed`
# rung MAY NOT CARRY A SEAT — that is the rung, and a seat appearing on one is exactly how a
# reconstructed band would come to be read as a reading. The business half is a strict
# restatement of the adjudication gated above, so a firm whose rung stops agreeing with its
# grade fails here rather than drifting into a second opinion. And rung 2 stands empty by
# MEASUREMENT, not assumption: the step re-reads the committed lot-address ledger, so the day
# a second lot address arrives naming somebody the gate fails rather than the rung quietly
# staying empty.
#
# T-1512 ADDED THE TWO RUNGS THE EVIDENCE STILL BOUNDS, and three more limits with them.
# A BAND MAY NOT MOVE A HOUSEHOLD OUT OF THE DIVISION ITS OWN CARD NAMES — the division is
# the reading and the band is the reconstruction, and a pass that could change the first
# while dealing the second is a pass that can rewrite evidence. A BAND MAY ONLY CITE A
# CLAUSE THE COMMITTED PLACEMENT POLICY HOLDS, and a head whose trade no clause reaches is
# banded to the division's own ground rather than dealt a class its record never carried.
# AND NO RECONSTRUCTED SEAT MAY GROW A LOT, A ROOF OR A COORDINATE: the step refuses the
# field by name, because that is the shape the drift would take.
step "the address book re-derives: every household and firm at the rung its evidence reaches, no band out of its division, no seat invented" \
  python3 tools/seat_known_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/seat_known_1835.py --self-test

# T-1144 acceptance 7, and the owner asked for it in those words on 2026-09-17: the
# convergence report must NAME, per person, which of the plural roles[] and which home,
# work and other locations reach 1 July 1835, so the sign-off reads coverage per axis off
# one table instead of re-deriving it. The two axes were both already counted in aggregate
# and neither could be asked about a PERSON without walking 1,258 household files and
# joining 1,705 reconciliation rows by hand.
#
# Gated here rather than higher up because every input it copies is gated ABOVE it — the
# roles at the roles step, the home/work/later rows at the reconciliation and spend steps
# just above, the premises on the business register's own present_at_scene_date. This table
# re-decides none of them: it copies each reach flag from the derivation that owns it, which
# is why a drift here means one of those layers moved and this join was not rebuilt with it.
# The self-test holds each rule over a fixture and proves it moves when its input moves,
# including the one that is easy to get wrong in the safe-looking direction: a `no_claim`
# home row is a STATED ABSENCE, not a failed placement, and reading the 1,186 of them as
# `limited` would turn the reconciliation's honesty into a manufactured gap.
step "every person says which roles and which places reach the scene date" \
  python3 tools/report_convergence_coverage.py --check --quiet

selftest "…and each of those rules moves when its input moves" \
  python3 tools/report_convergence_coverage.py --self-test

# T-1160. THE PROFILE OF THE KNOWN POPULATION, held to the layer it is read from.
#
# The owner asked for a population analysis of the known people before anything is
# reconstructed, and a profile is exactly the kind of document that rots quietly: the
# resident layer moves under it every time a mint runs, and a markdown table of
# percentages cannot say that it has. So the numbers live in
# `data/reconstruction/1835_population_profile.json`, the markdown is rendered FROM that
# json, and this step re-derives both from `data/residents/` and refuses a mismatch —
# which means a resident pass that changes the layer and does not re-run `--build` is
# red here rather than published wrong.
#
# It also holds the two judgements the profile makes. `REASON_RULES` buckets a stated
# reason for coming under a controlled term, and an unmatched reason is REFUSED rather
# than swept into an `other` row, so a new reason cannot fall silently through the axis.
# And the closing section — "what the town should have held" — is asserted to carry NO
# NUMBERS: the quantities belong to T-1293's model and T-1166's order book, and a figure
# typed into the profile would be a second, unsourced answer to the same question.
step "the 1835 population profile re-derives from the resident layer, on every axis" \
  python3 tools/profile_population_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/profile_population_1835.py --self-test

# T-1166. THE RECONSTRUCTION ORDER BOOK, held to every file it subtracts.
#
# The book is the quota the three reconstruction bands are built against: known
# minus model, per bucket, with the ticket that owes each one. It rots in exactly
# the way the profile does and in one worse way — a filler that writes more records
# than its bucket allows has silently overrun the town, and nothing else in this
# gate would notice. So `--check` re-derives every bucket from the town model, the
# profile's own layer, the roster, the roof programme, the inventory, the trade
# census and the 1840 composition, CARRIES the committed `filled` counters across
# unchanged, and refuses both drift and an overfilled bucket.
#
# The three judgements it makes are asserted rather than trusted. A range becomes a
# point by MIDPOINT and says so; a known person the layer cannot place is subtracted
# pro rata rather than dropped, so nobody is ordered twice; and only a household
# recorded `present` counts as known, because an `uncertain` one is already on the
# roster being offered to T-1172. The self-test also holds the one place the 1840
# age pyramid could silently disagree with the 1835 model — the child share — inside
# the model's own bracket.
#
# AND EVERY WORK ORDER IN IT NAMES A TICKET A RUN CAN STILL CLAIM (T-1420, 2026-09-21).
# `ticket.mjs done` already prints a NOTE when a close leaves a split parent with no
# live child — "any research unit that defers to it by id is now stranded (T-1237).
# That fails the re-derivation, in a tool this PR does not run" — and until now no tool
# ran it against the order book, so the note was advice a closing run could walk past.
# Thirteen of the twenty-four ids the book's owner tables named had closed or split
# under it by 2026-09-21. `--check` now re-reads the queue and REFUSES a bucket that
# still has work left whose `owning_ticket`, `owning_tickets` or `ground_waits_on`
# names a `done`, `split` or `withdrawn` ticket. Forward-looking ids only: `fills`,
# `recut_refusals`, `programme_deltas` and `roster_offered` record who DID the work and
# never move, and a discharged bucket keeps the id of whoever discharged it.
step "the 1835 reconstruction order book re-derives, no bucket is overfilled, and every work order names a live ticket" \
  python3 tools/build_order_book_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/build_order_book_1835.py --self-test

# T-1370, piece 1 of T-1175. HOW MANY BEDS EACH LODGING PLACE HELD. The town model
# states a bed bracket for the whole town and says in as many words that it "seats
# nobody in any lodging place and gives no boarding house a capacity of its own";
# T-1175 cannot seat a boarder without the per-place half, and T-1164 — the ticket
# that was to have written it — was withdrawn as folded into the town model, which
# is where the per-place half was lost.
#
# WHY A GATE, and it is the same argument as the order book's above. The model is an
# APPORTIONMENT of figures the town model already owns: each class's total is its
# place count times the model's own per-place figure, split by enclosed floor area.
# That construction is the entire claim to honesty here — the model redistributes a
# number rather than inventing one — and it holds only while the arithmetic does. So
# `--check` re-derives every row from the town model, the building inventory and the
# committed structure records, and REFUSES a total that has fallen outside the town
# model's own bracket, a place that sleeps nobody, or a place given more beds than
# the largest household the 1840 enumerator recorded.
#
# The classification is the other thing worth holding. A lodging place is read off
# each record's own `function` field and never off the roof programme's family code,
# because those two disagree: the programme schedules 42 roofs under the group name
# `larger_boarding_houses`, and 32 of them are families the archetype crosswalk calls
# houses. Reading the group name instead would quietly put boarders into six south-
# division dwellings, and the self-test holds that distinction directly.
step "the 1835 lodging model re-derives, and no house sleeps more than 1840 saw" \
  python3 tools/build_lodging_model_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/build_lodging_model_1835.py --self-test

# T-1183. THE RULE EVERY BUSINESS IS STAFFED BY, before anybody is staffed. Zero of
# the 197 business records carried a hand and the relationship vocabulary had held
# `clerk`, `apprentice`, `journeyman` and `servant` all along with nobody in them.
# This model prices the ESTABLISHMENT KINDS — a dry-goods store's clerk, a printing
# office's journeyman and apprentice, a tavern's bar-keeper, hostler, cook and
# chambermaid — so that the people T-1189 writes are a claim about a kind of house.
#
# WHY A GATE, and it is not the usual re-derivation argument alone. The model rests
# on one computed quotient — the 1839 directory's 152 clerks over the principals of
# the trades this model gives a clerk to — and on a reconciliation against the town
# model's own employment bracket. Both denominators move: the business layer gains
# records, the 1839 table is itself derived, and the town model re-cuts. `--check`
# re-derives the model and its report byte for byte and then REFUSES the failure
# that matters — a staffing table whose high end puts more people to work in the
# business layer alone than the town model employs in the whole town, which would
# be workers invented here. It refuses, too, any person id in the output: this file
# writes nobody, and that is the single line of its acceptance.
step "the 1835 business staffing model re-derives, and staffs nobody the town cannot employ" \
  python3 tools/build_staffing_model_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/build_staffing_model_1835.py --self-test

# T-1432, piece 1 of T-1189. THE STAFFING JOIN, ATTESTED AND INFERRED HALF. The model
# above says what a KIND of house employed and names nobody. This says where the people
# the sources DO name worked: 144 rows of the business layer carry a person_id, 110 town
# cards between them, and until now those cards said nothing about work at all. The join
# is written onto the person as `workplaces` — not `works_at`, which is the BUILDING and
# is singular and undated and policed as a structure link — and it is carried across at
# the business row's own tier, basis, source and claim ids. Nothing is minted here.
#
# WHY A GATE, AND WHY IT ASSERTS BOTH WAYS. The two ends move independently: the register
# recompiles, the identity work re-matches a printed name to a card, a household record is
# merged. A card carrying a workplace no business record names back is a fossil, and a
# named row whose card has lost its entry is a person who has quietly lost their trade.
# Either one is silent without this, and neither is a warning.
step "the 1835 staffing join re-derives, and holds from both ends" \
  python3 tools/staff_businesses_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/staff_businesses_1835.py --self-test

# T-1433, piece 2 of T-1189. THE STAFFING JOIN, RECONSTRUCTED HALF. The join above
# carried across every workplace a SOURCE names and said so: 144 rows, 110 cards, and
# the rest left standing. The rest is 524 people — the residents this project drew,
# each given a trade by the town model and not one of them given anywhere to follow it.
# This seats the ones the model can seat and states, for every one it cannot, the reason
# in the words of the ruling that decided it: a house of the trade with no room in its
# band, a keeper owed premises of their own, a soldier at a post the layer holds no
# establishment record for, a trade `premises_rulings.json` has never ruled on.
#
# WHY A GATE. Every block is a draw over two derived files that move — the staffing
# model re-cuts whenever a business record changes its occupation, and the business
# layer recompiles from the register — so a card written once would go on reading as
# this pass's output long after the pass stopped producing it. `--check` re-derives
# every block and the report byte for byte, refuses a card carrying a seat it is not
# owed and a seated card that has lost one, and refuses the failure that matters: a
# house holding more reconstructed hands in a role than the staffing model's own high
# end for it, which would be people invented here by a pass that invents nobody.
step "the 1835 reconstructed seating re-derives, and staffs no house past its band" \
  python3 tools/seat_reconstructed_trades_1835.py --check

selftest "…and each of its five assertions still fires when broken" \
  python3 tools/seat_reconstructed_trades_1835.py --self-test

# T-1462, piece 2 of 2 of T-1449, of T-1434, of T-1189. THE BUSINESS SIDE OF THAT SEATING.
# The pass above seated 124 reconstructed hands in 84 houses and wrote every seat in a
# join BESIDE the layer, keyed on the person. So the town knew where those people worked
# and the HOUSES did not: open any one of the 84 business cards and `staff` was empty,
# "Who kept it" printed the keeper alone, and a house standing at half the hands its
# class wants read exactly like a house standing at all of them. This lays the seats onto
# the records as an overlay — the compiler rewrites a compiled record whole, so a hand
# can only be laid over one — and puts each house's shortfall against the staffing model
# beside them, measured at the model's typical band and never its high end.
#
# WHY A GATE. It is an overlay over two derived files that both move: the seating re-draws
# whenever the business layer recompiles or the staffing model re-cuts, and the compiler
# refuses a committed record a rebuild would not produce. `--check` re-derives the overlay
# byte for byte, and the two failures that matter are refusals rather than warnings — a
# seat past every band the model gives the class, which would be a person invented by a
# pass that invents nobody, and an entry that would drop a row T-1422's RULING put on a
# record, because a derived pass may add to a judgement and may not overwrite one.
step "the reconstructed hands re-derive onto their houses, and each house states its shortfall" \
  python3 tools/staff_the_houses_1835.py --check

selftest "…and each of its seven assertions still fires when broken" \
  python3 tools/staff_the_houses_1835.py --self-test

# T-1461, piece 1 of T-1449, of T-1434, of T-1189. THE EMPLOYMENT COVERAGE ANSWER. The
# two joins above are both true and neither covers the town: 112 cards a source names in
# a house, 524 reconstructed trade-holders seated or told why not — 636 people of 3,243.
# The other 2,607 held no workplace, no seat and no reason, and a card that had never
# been asked the question looked exactly like a card that had been asked and answered
# no. This gives every person one answer from a closed set of five, in the words of the
# rule that decided it, so a silence is a statement that can be counted and argued with.
#
# IT SUPPLIES NO TRADE AND SEATS NOBODY. 2,536 people carry `occupation: none_recorded`
# and leave this pass carrying none — reading a trade in from the household is exactly
# the inference the reconstruction stages do under a quota and this pass has none.
# `at_a_trade_with_no_house_to_join` is counted as neither placed nor unemployed for the
# same reason: the soldier at the post and the laundress over her tub are at work, and
# what is missing is a house in the business layer to join them to.
#
# WHY A GATE. The cover is the claim, and it is made of four files that move
# independently — a card merged away leaves its answer behind as a fossil, a new
# household arrives with no answer at all, a premises ruling re-cut moves a man from his
# own account to somebody else's. `--check` re-derives every row and the report byte for
# byte and refuses the four ways the cover can be wrong: a person with no answer, a
# person with two, an answer in a word the vocabulary does not hold, and a child below
# the staffing model's own working-age floor placed in a shop.
step "every person in the resident layer carries one employment answer, and none carries none" \
  python3 tools/employment_coverage_1835.py --check

selftest "…and each of its seven assertions still fires when broken" \
  python3 tools/employment_coverage_1835.py --self-test

# T-1448, of T-1434, of T-1189. THE MINT ORDER FOR THE SHOP HANDS — and the collision
# that stopped the mint. The two passes above joined the houses to the people the
# sources name and the people this programme had already drawn; what was left was to
# MINT the rest, and the first question a mint has to answer is how many people it is
# allowed to invent. This project has one answer to that — the reconstruction order
# book — and set beside the staffing model it does not agree: the shops want 129 hands,
# the book has 109 slots left, every hand wanted is a man where two fifths of those
# slots are women's, and a fifth of the hands are boys of twelve to eighteen in a band
# where the book has nothing outstanding at all.
#
# WHY A GATE. The order is arithmetic over two derived files that both move — the
# staffing model re-cuts whenever a business record changes its occupation, and the
# book re-cuts whenever the known layer does — so the numbers the owner is being asked
# to rule on would go on reading as today's long after they stopped being true.
# `--check` re-derives the whole order byte for byte.
step "the 1835 staffing mint order re-derives, and spends no bucket it cannot reach" \
  python3 tools/staffing_mint_order_1835.py --check

selftest "…and each of its seven assertions still fires when broken" \
  python3 tools/staffing_mint_order_1835.py --self-test

# T-1371, piece 2 of T-1175 and stage `lodgers` of the resident reconstruction programme.
# THE BEDS THE MODEL ABOVE COUNTED, SLEPT IN. T-1370 gave fifteen built lodging places an
# ordinary-night capacity of 135 between them and seated nobody; thirty people stood on
# their cards, eight keepers and their families. This stage fills the ordinary-night
# figure: the solitary heads T-1171 and T-1173 already drew are seated first, the short
# beds are drawn against the order book's own `lodging` buckets, and a roof THIS programme
# raised as a lodging place is given a keeper at the trade its own `function` states.
#
# WHY A GATE. Every person here is a draw over a quota two other derived files own, and
# both of them move: the lodging model re-apportions whenever a structure record changes
# its floor area, and the order book re-cuts whenever the known layer does. Left ungated,
# a card written once would go on reading as this stage's output long after the stage
# stopped producing it. `--check` re-derives every card and the ledger byte for byte,
# holds the order book's fills to the ledger's own, and refuses a house sleeping more
# people than the 1840 enumerator ever saw or a person seated in two houses at once.
#
# The refusal worth knowing is the one that leaves beds empty. A person drawn into a
# lodging house has to be ordered out of the book's bucket for a DIVISION, and
# `data/structures/*.json` carries no division field at all — the residents layer's own
# households are where a named house's division comes from. The New York House and the
# Sauganash Hotel have none attached, so this stage mints nobody into them and says so
# rather than guessing a division to spend a bucket on. Thirteen ordinary-night beds
# stand empty at the end of it and the ledger names every one.
step "the boarders re-derive, and no house sleeps more than the 1840 enumerator saw" \
  python3 tools/seat_lodgers_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/seat_lodgers_1835.py --self-test

# T-1352, piece 1 of T-1178. THE ROW THE ORDER BOOK CANNOT APPORTION. `persons/transient/
# town` sits in the book above with no target and no quota, because the town model bounds
# the town's RESIDENTS and the land-sale crowd, the immigrants awaiting lots, the harbour
# gang and the crews ashore were in the town on 1 July 1835 and not of it. This bounds that
# cohort — 192 to 900 — and says where it slept; T-1353 mints it and T-1214 places the camps.
#
# WHY A GATE. Every figure is a quoted sentence or a count of a file that moves: the floor is
# a rate off the 1843 census applied to the town model's own resident point, and the measured
# land-sale floor is a join between the tract register and the resident crosswalk, which the
# resident layer changes under. Left ungated it would go stale while reading as a decision.
#
# The refusals worth knowing: a quoted sentence the corpus no longer carries (the American's
# "some hundreds more" is the whole ceiling, and a re-extraction that drops it must fail
# rather than leave the band standing on nothing), a land-sale crosswalk that can place
# nobody — which would make every purchaser in the register read as a stranger and turn a
# measurement into a fiction — a camp-ground candidate that types a polygon of its own
# instead of naming the committed geometry it resolves from, and a headline figure that has
# acquired a point reading, which this model refused to pick and no later hand may adopt for it.
step "the 1835 transient cohort re-derives, and its bracket still stands on the sentences it quotes" \
  python3 tools/model_transients_1835.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/model_transients_1835.py --self-test

# THE OTHER HALF OF THE SAME PROBLEM (T-0384, the owner's ruling of 2026-08-30). Where the
# adoptions answer "the paper names a face and no position", this answers "the paper names
# a position and no lot": a count of doors off a named corner — "on South-Water st. one
# door from Dearborn street" — places a store along the face, and AN ORDINAL IS STILL NOT A
# LOT. The limit is written in a field rather than in prose (`lot_claim` on the record) and
# this proves the chain: that the reading and the declaration name the same records, that
# the declaration is well formed and the record has grown no lot field under another name,
# that the plat's barred-lot map is IDENTICAL with the declaring records in the town and
# out of it — the transparency PR #514 lacked, which switched off the business-front clause
# and cost a dealt roof — and that the metres between a door and a corner, which are this
# project's arithmetic and not the paper's, are admitted at a liberty. `--report` prints
# the sweep of every `n doors` phrase the corpus holds. docs/CORNER-ORDINAL.md is the policy.
step "an ordinal off a corner places a position and claims no lot" \
  python3 tools/measure_corner_ordinals.py --gate --quiet

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_corner_ordinals.py --self-test

# SPENDING that allocation is a second gate, because the table and the structure records
# are two files and a policy that only reaches one of them is a policy the visitor never
# sees (T-0417). tools/inferred_occupancy.py is the ledger both the household programme
# and the adoptions hand their `occupants` block to; the generators' own `--check` above
# already refuses a record that has drifted from it, so what is left to prove here is that
# the ledger refuses a malformed adoption rather than passing it through — and that the
# two programmes never both claim one roof.
selftest "…and the ledger that spends them into the roofs refuses every way one could lie" \
  python3 tools/inferred_occupancy.py --self-test

# AND THE THIRD WAY A PAPER PLACES A BUILDING (T-0423): it prints a LOT AND A BLOCK. Where
# an adoption claims a face and an ordinal claims neither, this claims the plat's own unit,
# and there is exactly one of it in the corpus — G. Spring's For-Sale notice, six printings,
# "LOT No. 7, in block No. 16 … on Lake street". The address is authored in
# data/research/newspapers/lot_addresses.json and NOTHING ELSE about it is: the block number
# resolves through the committed numbering, the lot number through the committed lot grid,
# and which roof stands at the address is derived from its footprint. Gated rather than
# committed once for the same reason the adoptions are — every step of that chain moves when
# the town does. A block renumbered, a lot line redrawn, a second roof built onto the lot or
# a phase promoted because a documented address landed on it all fail here.
step "the lot-and-block address re-derives, and seating it promotes no roof" \
  python3 tools/lot_addresses.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/lot_addresses.py --self-test

# AND THE FOURTH THING A RECORD CAN SAY ABOUT A LOT, WHICH IS THE ONE NOBODY SAID (T-1478).
# The three above are all CLAIMS — a face adopted, an ordinal off a corner, a printed lot and
# block. This is a MEASUREMENT: until T-1194 the only lot layer stopped at the main stem, so a
# documented building north or west of the river stood on a bare coordinate; there are now
# five more grids out there and `stands_on_lot` records which lot of them each documented
# footprint turned out to fall on. It is gated rather than committed once because every step
# of it moves when the town does — a lot line redrawn, a block renumbered, a footprint
# corrected, a numeral re-read. The assertions worth naming: the seat is plat_occupancy's own
# rule IMPORTED rather than a second copy of it; only `research`-layer records carry one, so
# this project's reconstruction can never read back as evidence about the town; the grade is
# the WEAKER of the lot lines and the numeral, which is why the West Division's documented
# numerals still give inferred seats; and a grid that numbers nothing — Wabansia, the Michigan
# Street tract — seats the block and withholds the numeral rather than counting one off the
# polygon list.
step "every documented north-or-west record's lot re-derives from the committed grid" \
  python3 tools/record_lot_seating.py --check

selftest "…and a seat still may not claim a lot, outrank its lot lines, or invent a numeral" \
  python3 tools/record_lot_seating.py --self-test

# THE 1840 CENSUS LINE -> IPUMS SERIAL JOIN (T-0504). IPUMS holds 964 Chicago households as
# age-band counts with no names; every one of them is also a ruled line on a page image that
# carries the head's name, and the twenty-six free-white age-band columns are the only thing
# the two share. The join is DERIVED from the committed page readings rather than kept by
# hand — which is what the owner's lost v3/v4 workbooks were — so the thing worth gating is
# that it still re-derives: a page reading that changes and a crosswalk that does not is
# exactly the drift a workbook cannot report and this can. --check also holds the refusals:
# an ambiguous fingerprint attaches no serial, a serial is attached to at most one line, and
# a column the page does not close against the enumerator's own foot total is not compared.
step "the 1840 census line-to-serial crosswalk re-derives from the page readings" \
  python3 tools/census_1840_fingerprint.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/census_1840_fingerprint.py --self-test

# T-0507. The 1840 composition summary, and it is gated for a reason that is not staleness.
# The figures are cheap to re-derive and would matter little if they drifted a person or two;
# what matters is the LINE the file stands on. It is built from an extract that carries 55
# transcribed head-of-household names and 964 household serials, and the whole value of the
# summary is that it is counts and nothing else — 1840 household members are never minted
# into 1835 from census counts, which is the owner's own rule. --self-test refuses the build
# if a single one of those names or serials reaches the output, and --check refuses a
# committed file that no longer re-derives from the extract and from T-0504's column_map. A
# hand-edited count in there would be a fact about this town that nobody counted.
step "the 1840 household composition re-derives, and no name or serial reaches it" \
  python3 tools/census_1840_composition.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/census_1840_composition.py --self-test
# T-0513. The consolidation, and the reason it is gated rather than reported: it is the
# only file that says, for one identity, everything the project knows — and it is DERIVED
# from seven domains that each move on their own ticket. A source read on Tuesday that
# never reaches the master is the exact failure the owner named ("there are not outputs or
# updates to the household and resident data"), and it looks like nothing at all until
# somebody rebuilds by hand. --check rebuilds from the domains and fails if the committed
# files have drifted; the invariants it holds are the acceptance's own — one row per
# identity, no record claimed by two identities, every refusal carrying a rule that exists,
# and no row graded above what its rung of the ratified ladder allows.
step "the cross-domain identity master re-derives, and no grade stands above its rung" \
  python3 tools/consolidate_resident_evidence.py --check

# T-0638 fault C. The two READING RULES that ticket fixed are mechanical and were
# applied; the dozen names whose LETTERS look wrong are not, and this project does not
# invent readings. So they are written down instead — the printing, the column it was
# printed in, and a suspicion that is graded nothing and acted on nowhere. Gated
# because a worklist is only worth anything while it still cites the corpus it came
# from, and because the one way this file could do harm is by quietly acquiring a
# grade and becoming evidence for a name nobody ever read.
step "the letter lists' suspected misreadings stay a worklist and not evidence" \
  python3 tools/register_letter_list_suspicions.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/register_letter_list_suspicions.py --self-test

selftest "…and its own assertions still fire when broken" \
  python3 tools/consolidate_resident_evidence.py --self-test

# T-0843, the OTHER half of T-0839. `consolidate_town_cards.py --check` above gates that
# every duplicate cluster the town already holds carries a written ruling; that is ruling
# coverage, and it says nothing about the next duplicate. Three of the four minting passes
# test "does the town already carry this person?" by SURNAME, and that proxy is partial by
# design — each skips the households minted by itself and by the passes below it, so a card
# one of those wrote is invisible to it. `identity_master_guard.py` is the precise
# instrument for that blind spot: it hands a candidate name to the master's own `cluster()`,
# inside its own surname bucket, with every identity of that surname standing as an anchor
# whether it holds a card or not, and refuses only where the master itself merges. Gated
# because the whole value of it is that it is the master's answer and not a hand copy — a
# first draft written out by hand reported 19 committed cards as duplicates where the master
# reports 2, because a copy of M2 cannot see the rivals that HOLD a merge apart.
selftest "the mints' consultation of the identity master is the master's own rules" \
  python3 tools/identity_master_guard.py --self-test

# T-0512, the second half of the owner's publish ask. The final audit is the one file that
# says, for every person in the town, what they rest on — which ticket reviewed them, which
# source ids stand behind them by category, and what is still open. It is DERIVED from the
# residents layer, so it is exactly the kind of artifact that reads as current long after
# it has stopped being true: a cohort lands, the layer moves, and a stale CSV keeps telling
# the owner the programme reached 611 people. Gated in both directions — the committed
# package must re-derive, and a hand edit to it is refused.
step "the final resident audit still re-derives from the residents layer" \
  python3 tools/export_resident_audit.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/export_resident_audit.py --self-test

# T-1065. The lighthouse's coordinate is a reading of one glyph on Wright's 1834 sheet, and
# the pixel it was picked at lives in a different file from the metres it produced. Two files
# hold one statement, so the gate recomputes the metres from the pixel every run: a later pass
# that nudges the record for an unrelated reason would otherwise detach the number from the
# evidence its own note goes on citing. The PICK cannot be gated — it is an eyeball reading of
# a raster — which is exactly why the pixel is committed rather than only the result.
step "the lighthouse still stands on the glyph Wright drew for it" \
  python3 tools/measure_wright_lighthouse.py --check

selftest "…and its own assertions still fire when broken" \
  python3 tools/measure_wright_lighthouse.py --self-test

# T-0334. The 5 August 1835 hay-stacking ordinance walks a six-vertex boundary round the
# built town, and it is the only DOCUMENTED statement this project holds about where the
# built-up town ended in the scene year — every other judgement about density here comes
# from the plat, the land deal and measured frontage. The limit is DERIVED from committed
# street centrelines, the committed reservation ring and the traced 1834 shore, the way
# the datum is derived, so it is gated in both directions: the committed file must
# re-derive exactly, and a hand edit to it is refused. That matters more here than usual
# because the card now shows a visitor which side of the line a building stood on, and a
# hand-nudged ring would move that verdict for 383 buildings with nothing to catch it.
step "the 1835 hay-stacking limit still re-derives from committed street lines" \
  python3 tools/derive_hay_limits.py --check

selftest "…and its own refusals still fire when broken" \
  python3 tools/derive_hay_limits.py --self-test

# The agency relation the SAME card reads (T-1041), and gated the same way for the same
# reason. This one is a relation between two records rather than a measurement, so what
# a hand edit could do here is worse than a wrong number: it could hand a house a trade
# it never had, or quietly drop the standing caveat that says a holding is only a
# holding. Both are refusals in the tool, and the re-derivation is what keeps the card
# showing the register rather than somebody's improvement on it.
step "the agency relation still re-derives from the committed register" \
  python3 tools/compile_agencies.py --check

selftest "…and its own refusals still fire when broken" \
  python3 tools/compile_agencies.py --self-test

# T-1238. `associated_with[]` is the plural, dated form of `lives_at`/`works_at`, and
# its coverage file is how the migration's remaining distance stays a number rather than
# an impression: both shapes stand until the last record moves, and a half-migrated layer
# is exactly the state in which two fields quietly say two different things about one man.
# The row rules are broken one at a time by the module's own self-test; validate.py wires
# them into the gate and refuses a singular link that has drifted from its plural rows.
step "the association coverage still re-derives from the committed records" \
  python3 tools/associations.py --check

selftest "…and its own refusals still fire when broken" \
  python3 tools/associations.py --self-test

# T-1405. The OTHER places a person was — a civic seat, a parish act, an agency, ground
# bought, a school taught in — derived onto the cards from the committed evidence rather
# than hand-authored one at a time. Two things this step holds. The first is the usual
# one: the report re-derives, so a hand-edit loses. The second is the one that matters
# here — `--check` also asserts that every derived row is still ON ITS CARD, because the
# resident cards are byte-owned by writers that re-derive them and a field written into
# one can be dropped by the next pass and go quietly stale. A row that has been dropped
# is a claim about a man that the layer no longer makes, and the gate says so.
step "the person associations still re-derive, and are still on their cards" \
  python3 tools/person_associations.py --check

selftest "…and its own refusals still fire when broken" \
  python3 tools/person_associations.py --self-test

# T-1158. The per-attribute tier, and the three things that can go wrong with it.
#
# The first is DRIFT. The tier of an existing value is DERIVED from the confidence and the
# value the card already carries — the cards themselves are byte-owned by nine writers that
# each re-derive them, so a field written into one would be dropped by the next pass and
# quietly go stale. `--check` re-derives the table and refuses a hand-edit or a card that
# has moved under it. Rebuild with `--build`.
#
# The second is PROMOTION. A tier that could be set independently of the evidence would be
# a second, softer grade, and the whole point of the fourth tier — `unknown`, for the 7,314
# blocks that assert nothing — is that a reconstruction band cannot quietly reuse it for
# something it invented. So a tier may not disagree with its derivation, an invented value
# owes a basis and a replacement rule, and a value DRAWN from a model owes the seed that
# redraws it. `validate.py` enforces that on any record carrying the shape, through the
# module's own `check_tier_block`; the self-test below breaks each rule in turn.
step "every attribute's tier still re-derives from the card it sits on" \
  python3 tools/migrate_attribute_tiers.py --check

selftest "…and its own refusals still fire when broken" \
  python3 tools/migrate_attribute_tiers.py --self-test

# T-1398. THE REBUILD ORDER OF THE RESIDENT LAYER, gated rather than remembered.
#
# Every step above re-derives ONE artifact and says so when it is stale. None of them can
# say whether the SET of them adds up to a fixed point, and that is the thing the layer
# keeps getting wrong: the town model is a count of the layer, the programme's stages draw
# from the model, and the stages write back into the layer the model counts. Rebuilding
# "the stale piece the check named" therefore never converges — the check names the stage
# that is stale and the cycle runs through a stage it does not name. Measured three times
# in one evening clearing #1497 and #1502 (T-1179's findings): five gate steps red, then a
# 2-cycle running three passes, then two readers nobody had in the set at all.
#
# So the order is data now — data/reconstruction/1835_resident_layer_rebuild_order.json —
# `converge_resident_layer.py --run` executes it and iterates to the fixed point, and this
# holds the file honest: every step gated by THIS file, every declared path named by the
# tool that claims it, every back edge declared, and every gated re-derivation standing
# beside the layer classified either into the order or out of it. It re-derives nothing
# itself; the steps above already do that, and doing it twice would double the gate.
step "the resident layer's rebuild order still holds, and its set has not grown in silence" \
  python3 tools/converge_resident_layer.py --check

selftest "…and each of its four assertions still fires when broken" \
  python3 tools/converge_resident_layer.py --self-test

# The third is the two derivations parting company. The gate derives the tier in Python and
# the walkthrough derives it in JavaScript, because a card a visitor opens may not fetch a
# table of ten thousand rows to learn its own tiers. That failure would not crash: the card
# would draw the hatched `reconstructed` chip over a field nobody invented — the exact
# defect this ticket removes — while the published table went on reporting the right
# number. So both readers are run over the same 1,258 cards and required to agree.
step "the walkthrough's tier reader agrees with the published table" \
  node tools/check_attribute_tiers.mjs

selftest "…and its own derivation still answers each case" \
  node tools/check_attribute_tiers.mjs --self-test

check_summary
exit $CHECK_FAILED
