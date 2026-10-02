#!/usr/bin/env bash
# Copy the publishable tree into site/. The repo's Pages workflow publishes ONLY
# site/, so anything not copied here does not ship — which is deliberate: the
# uncompressed GLB masters, the research dossiers and the raw dataset all stay
# in the repo and out of the payload.
#
# THIS SCRIPT IS THE ONE WRITER OF site/4d/. The mirror is generated and
# untracked (T-0938), and the residents layer is shipped MINIFIED here and nowhere
# else, so no other tool may write those paths. When synthesize_resident_research.py
# wrote them too — pretty-printed — whichever ran last decided whether the gate was
# green, and `bash tools/publish.sh` on an untouched dev turned tools/check.sh red on
# four files whose parsed values were identical (T-0933).
set -euo pipefail
cd "$(dirname "$0")/.."

# The three v4 GLBs (master, full web, light web) are losslessly packed in committed archive parts.
# Restore only missing ignored outputs; divergent existing bytes fail with repack
# guidance. This never derives a mesh or replaces a derivative with its master.
python3 tools/recover_glessner_v4.py --materialize

# ---------------------------------------------------------------------------
# THIS SCRIPT DOES NOT DERIVE OR REPLACE assets/web/ — ROADMAP K38.
# The explicit three-file package materialization above writes only absent,
# ignored outputs whose exact source bytes and hashes are already committed.
#
# It used to be. Any master newer by mtime than its derivative was copied
# through, here, into the TRACKED source tree and then into the mirror. The
# intent was right — run `generators/build.py` alone and `assets/web/` goes
# stale, which once cost a debugging round when a rebuilt building kept
# rendering with its old confidence values — but the response was wrong twice:
#
#   * it SHIPPED THE UNCOMPRESSED MASTER, silently. Measured: two assets copied
#     through this way added 1,212,760 bytes to the payload, and the entire dev
#     gate printed CHECK PASS. A master copied over its own derivative has that
#     master's triangles, node identity, attributes, bounding box and materials,
#     and a byte count that is equal rather than larger, so every assertion in
#     tools/measure_web_derivatives.py passed it. Assertion 8 exists now and
#     catches exactly this, from ANY writer.
#   * and it made a publish step mutate the repository, which is the one thing
#     the mirror contract says publish does not do.
#
# So the detection stays and the writing goes. This refuses BEFORE it writes
# anything, names the files and names the command that fixes them.
#
# AND THE DETECTION IS NO LONGER AN mtime SCAN — ROADMAP K39. It was one, and K38
# recorded its own residual in as many words: mtime is a conservative trigger, not a
# complete one, because on a fresh clone `git checkout`'s write order makes every
# master older than its derivative (measured: 334 of 334). So the scan was silent on
# exactly the tree a steward run starts from, and the stale derivative it was written
# to catch — a master rebuilt with the same geometry and different _CONFIDENCE values —
# went past it and past assertions 1-8 alike.
#
# tools/web_derivatives.sh records the sha256 of the master it compressed as it writes
# each derivative, and assertion 9 in tools/measure_web_derivatives.py compares that
# hash to the master in the tree. So staleness is answered from CONTENT here now, and
# this simply runs the gate: it is the same question, asked by the thing that already
# knows how to ask it, and running the whole gate also means a publish cannot ship a
# tree whose derivatives fail any of the other eight.
# ---------------------------------------------------------------------------
mkdir -p assets/web
if ! python3 tools/measure_web_derivatives.py --gate --quiet; then
  echo "" >&2
  echo "REFUSING TO PUBLISH — the derivatives this would mirror do not answer for" >&2
  echo "themselves against the masters in the tree (see the failures above). The site" >&2
  echo "would carry a building the repository no longer describes, and publishing it" >&2
  echo "is how that becomes invisible." >&2
  echo "" >&2
  echo "Each failure names its own remedy; both of the common ones are regenerations:" >&2
  echo "   tools/web_derivatives.sh --only <name>       # a stale or unrecorded file" >&2
  echo "   python3 tools/measure_web_derivatives.py --write-baseline   # only if the" >&2
  echo "     # passthrough set moved — a master that compresses bigger stays a copy" >&2
  exit 1
fi

SITE="../../site/4d"
# Owner-requested Prairie research browser also travels with the dev preview.
python3 ../prairie_1904_v1/tools/publish.py "../../site/4d/prairie-1904"
# Keep the pre-fire reference UI available for review before production promotion.
bash ../pre_fire_v1/tools/publish.sh
mkdir -p "$SITE/pre-fire"
cp -R ../../site/pre-fire/viewer ../../site/pre-fire/maps ../../site/pre-fire/media "$SITE/pre-fire/"
# The site root already publishes both browsers' production copies, so any asset
# directory that is byte-identical there is read from there instead of shipped a
# second time (T-1828: 91.7 MB of a 287 MB tree, the 31 MB it was over budget).
python3 tools/serve_from_root.py "$SITE" ../../site
mkdir -p "$SITE/data/gltf" "$SITE/data/sidecars"

# renderer
if [ -d renderers/web ]; then
  rm -rf "$SITE/walk"
  cp -a renderers/web "$SITE/walk"
fi

# The changelog is authored inside the app (the What's-new tab imports it, and
# a page under walk/ cannot import from this publish mirror). Manager and the
# polecat.live launcher fetch it from <site>/js/changelog.js, though, so mirror
# it to that URL — it is a fleet-parsed contract path and must not move.
#
# AND IT IS MIRRORED ONCE, NOT TWICE — T-0722. The line above used to be the
# SECOND copy: `cp -a renderers/web "$SITE/walk"` had already carried the
# authored file to walk/js/changelog.js, so the mirror shipped the same 1.31 MB
# under two URLs. That is 4.1 % of the whole 32 MB budget spent on a byte-for-byte
# duplicate, and it grows twice as fast as the record does — every entry costs the
# payload double. It is what put dev at 31.999 MB with nothing left for a PR.
#
# So the real file goes to the fleet-parsed path, and walk/js/changelog.js becomes
# a re-export of it. `whatsnew.js` imports `./changelog.js` and cares only that
# CHANGELOG and LATEST_VERSION come back; ../../js/changelog.js resolves inside the
# mirror, where the fleet path is guaranteed to exist. Nothing under renderers/web
# changes: the dev tree still holds the authored file at the path the app imports,
# which is the whole reason the changelog is authored inside the app (a page under
# walk/ cannot import from a mirror that does not exist yet in the dev tree).
if [ -f renderers/web/js/changelog.js ]; then
  mkdir -p "$SITE/js"
  cp -f renderers/web/js/changelog.js "$SITE/js/changelog.js"
  # …and the SECOND published path takes a re-export of it rather than a second
  # copy. tools/stamp-changelog.mjs owns both forms (it is the writer of this
  # file), so the shim's text lives in exactly one place; calling it here is what
  # keeps publish.sh from being a second hand-kept copy of the same fact.
  # tools/check_published.mjs carries the TRANSFORMED row that says why the walk
  # copy is allowed to differ from its source, and tools/validate.py refuses any
  # two published files over 64 KB that hold identical bytes, so the duplicate
  # cannot come back the way it arrived.
  node tools/stamp-changelog.mjs --write-mirrors
fi

# The ticket board, for Manager and any fleet reader (T-0030): tickets.json is
# generated by tools/ticket.mjs and mirrored verbatim here.
#
# BUILT FIRST, NOT ASSUMED PRESENT (T-0937). Neither `tickets/tickets.json` nor the
# mirror is committed any more — they conflicted on every branch, because a run's
# first act is `ticket.mjs claim` and that rewrites both before any work is done, and
# GitHub's merge runs no driver to reconcile them (T-0857). So a fresh clone has
# neither file, and the old `[ -f ]` guard would have published nothing at all and
# said nothing about it. `board` is a pure function of tickets/*.md and costs
# milliseconds; running it here is what keeps /4d/tickets.json a real URL.
[ -f tickets/QUEUE.md ] || bash tools/tickets.sh || true   # the tickets are their own repo (2026-09-23)
node tools/ticket.mjs board >/dev/null
cp -f tickets/tickets.json "$SITE/tickets.json"

# Web-derivative assets only — never the masters. assets/web/ is produced by
# tools/web_derivatives.sh (which tools/bake.sh calls and nothing else does);
# the staleness of that directory against assets/gltf/ is settled at the top of
# this script, and this copies what is there rather than deciding it.
#
# The mirror is a MIRROR, not an accumulator. Copying in without clearing out
# means a retired asset ships forever: the 108 __recommended_1835.glb placeholders
# were deleted from the source tree and kept being published for as long as anyone
# ran this script. Clear the directory so a deletion propagates the way an edit does.
rm -rf "$SITE/data/gltf"
mkdir -p "$SITE/data/gltf"
if compgen -G "assets/web/*.glb" > /dev/null; then
  cp -f assets/web/*.glb "$SITE/data/gltf/"
fi
# The structure VERSIONS' derivatives (T-1727), under their own subtree so a sidecar's
# `gltf/versions/<id>/<label>/…` resolves here exactly as `gltf/<name>` does. Copied
# whole; the renderer fetches one only when an address asks for that version, so they
# cost the boot nothing. Their freshness is `validate.py --stale`'s version check.
if [ -d assets/web/versions ]; then
  cp -a assets/web/versions "$SITE/data/gltf/versions"
fi

# EVERY MAP BELOW SHIPS AS ITS LOSSLESS WEBP (T-1973), not its PNG master: the same
# pixels in about a third fewer bytes, held pixel-identical to the master by
# `tools/web_textures.py --check` in the gate. These are boot bytes — every visitor
# downloads them before standing in the street (docs/SITE-BUDGET.md § 4). The ground
# strip's two basecolors further down stay PNG: they load only under ?proof=ground.
#
# The two roof coverings' relief maps (T-1488). `renderers/web/js/roof-relief.js`
# resolves them against the ASSET base — ../../assets/ in the dev tree, ../data/
# in the published one — so they land here under data/textures/ and the same
# relative URL answers in both. FOUR FILES AND NOT SIXTEEN: the module binds
# `normal_gl` plus the packed `orm`, so the basecolor, height16, metallic,
# roughness, ao and normal_dx of each covering stay in the repository and out of
# the payload. material.json travels with them because the renderer reads the
# tile rate (`span_m`) off it rather than holding a constant of its own —
# leaving it behind is roofs with no relief on the deployed site while the dev
# tree shingles every one of them, which is the scenes/, fauna/ and residents/
# failure again.
for covering in wood_shingles_weathered roof_boards_weathered; do
  src="assets/textures/chicago_1835_pbr/roofs/$covering"
  dst="$SITE/data/textures/chicago_1835_pbr/roofs/$covering"
  mkdir -p "$dst"
  cp -f "$src/material.json" \
        "$src/${covering}_normal_gl.webp" \
        "$src/${covering}_orm.webp" \
        "$dst/"
done

# The street edge's board face (T-1815) — `renderers/web/js/frontage.js` binds
# its grain to every plank, stoop and post the layer lays. Same asset-base
# rename and the same reason as the roof relief above. FOUR FILES: the relief
# pair, material.json for the tile and the mean roughness, and the basecolor,
# which the layer reads only for its luminance ratio (the albedo modulation) —
# the timber's own colour stays on the vertex.
#
# The walls' relief (T-1963) — `renderers/web/js/wall-relief.js` binds the same
# board face to every clapboarded wall, and the hewn log face to every laid-log
# wall, and packs each one's albedo ratio from the basecolor at load. The same
# four files of each sheet, so the board face above already serves both layers.
for face in clapboard_board_face hewn_log_face; do
  src="assets/textures/chicago_1835_pbr/walls/$face"
  dst="$SITE/data/textures/chicago_1835_pbr/walls/$face"
  mkdir -p "$dst"
  cp -f "$src/material.json" \
        "$src/${face}_normal_gl.webp" \
        "$src/${face}_orm.webp" \
        "$src/${face}_basecolor.webp" \
        "$dst/"
done

# The T-1797 ground strip's two library substrates — `renderers/web/js/ground-strip.js`,
# drawn only under `?proof=ground`. Same asset-base rename and the same reason as
# the roof relief above: material.json carries the metric tile the strip reads.
# TWO FILES AND NOT TEN: the strip binds the basecolor only (the library's
# ground normals are flat — the strip's relief is its own grit tile), and the
# height, ORM and loose channels stay in the repository.
for ground in wet_prairie_muck lake_michigan_dune_sand; do
  src="assets/textures/chicago_1835_pbr/ground/$ground"
  dst="$SITE/data/textures/chicago_1835_pbr/ground/$ground"
  mkdir -p "$dst"
  cp -f "$src/material.json" \
        "$src/${ground}_basecolor.png" \
        "$dst/"
done

# The signboards' wood (T-1836). `renderers/web/js/signage.js` lays the grain of
# these two library sheets under the lettering atlas and builds its relief and
# roughness atlases from their normals, resolving them against the same asset
# base as the roof relief above. THREE FILES OF EACH SHEET: basecolor (read for its
# grain only, never its tone) and normal_gl, plus material.json for the metric
# span. Missing on the deployed site, the boards fall back to flat paint with a
# recorded problem — a loss nobody would see as an error, which is why it is here.
for sheet in props/signboard_weathered timber/heavy_timber_weathered; do
  name="${sheet#*/}"
  src="assets/textures/chicago_1835_pbr/$sheet"
  dst="$SITE/data/textures/chicago_1835_pbr/$sheet"
  mkdir -p "$dst"
  cp -f "$src/material.json" \
        "$src/${name}_basecolor.webp" \
        "$src/${name}_normal_gl.webp" \
        "$dst/"
done

# scenes, sidecars, datum (the renderer needs the origin for sun position).
# Keep the scenes/ subdirectory — the renderer fetches data/scenes/<year>.json,
# and flattening it here 404s the published build while the source tree works.
mkdir -p "$SITE/data/scenes"
cp -f data/scenes/*.json "$SITE/data/scenes/" 2>/dev/null || true
rm -f "$SITE"/data/[0-9]*.json
cp -f data/datum.json "$SITE/data/"
# The liberties list the Evidence panel reads. Derived from docs/LIBERTIES.md,
# which itself stays out of the payload.
cp -f data/liberties.json "$SITE/data/"
# The town census the gate screen shows — buildings standing and people housed
# (T-0036). Derived by tools/town_census.py and re-derived by tools/check.sh; the
# gate fetches it, so leaving it out of the mirror is a 404 on the deployed site
# while the dev tree counts the town perfectly — the scenes/, fauna/ and
# residents/ failure, a fourth time.
cp -f data/town_census.json "$SITE/data/"

# The derived town-ordinance limits the building card reads (T-0334). Derived by
# tools/derive_hay_limits.py and re-derived by tools/check.sh; renderers/web/js/
# ordinances.js fetches it at data/reconstruction/1835_hay_limits.json, so leaving
# it behind here is a 404 on the deployed site and a card missing a row while the
# dev tree shows it — the scenes/, fauna/ and residents/ failure again.
mkdir -p "$SITE/data/reconstruction"
cp -f data/reconstruction/1835_hay_limits.json "$SITE/data/reconstruction/"

# And the compiled agency relation the same card reads (T-1041). Derived by
# tools/compile_agencies.py and re-derived by tools/check.sh; agencies.js fetches it
# at data/reconstruction/1835_agencies.json from BOTH the building card and the person
# card, so leaving it behind is one 404 and two cards silently missing a relation the
# register has held since T-0410.
cp -f data/reconstruction/1835_agencies.json "$SITE/data/reconstruction/"

# And the profile of the known population (T-1160). Derived by
# tools/profile_population_1835.py and re-derived by tools/check.sh; population.js
# fetches it at data/reconstruction/1835_population_profile.json to render the
# Evidence hub's "The town's people" topic, so leaving it behind is a 404 and an
# Evidence tile that counts zero on the deployed site while the dev tree shows ten.
cp -f data/reconstruction/1835_population_profile.json "$SITE/data/reconstruction/"

# And the reconstruction order book (T-1166). Derived by
# tools/build_order_book_1835.py and re-derived by tools/check.sh; orderbook.js
# fetches it at data/reconstruction/1835_reconstruction_order_book.json to render the
# Evidence hub's "Reconstructing the town" topic — the progress view the three
# reconstruction bands fill — so leaving it behind is a 404 and a tile that counts
# zero on the deployed site while the dev tree shows seven.
cp -f data/reconstruction/1835_reconstruction_order_book.json "$SITE/data/reconstruction/"

# And the address book (T-1491). Derived by tools/seat_known_1835.py and re-derived by
# tools/check.sh; people.js fetches it at data/reconstruction/1835_address_book.json so
# that a household card can say where its household stood and at which rung. Leaving it
# behind is a 404 and 1,186 cards reading "No known address" with nothing after it —
# which is the sentence this file exists to replace.
cp -f data/reconstruction/1835_address_book.json "$SITE/data/reconstruction/"

# Terrain: the epoch registry, the traced river vectors, and the heightfield the
# renderer samples. The .bin is a plain binary and must travel with its meta —
# publishing heightfield.json without heightfield.bin gives a flat world and a
# 404 that only appears on the deployed site, never in the dev tree.
mkdir -p "$SITE/data/terrain"
cp -f data/terrain/epochs.json \
      data/terrain/shoreline_states.json \
      data/terrain/shoreline_disagreement_bands.geojson \
      "$SITE/data/terrain/"
if [ -d data/terrain/epochs ]; then
  rm -rf "$SITE/data/terrain/epochs"
  cp -a data/terrain/epochs "$SITE/data/terrain/epochs"
fi

if [ -d data/sidecars ]; then
  rm -rf "$SITE/data/sidecars"
  cp -a data/sidecars "$SITE/data/sidecars"
fi

# Vegetation: the flora manifest plus every zone and palette file it names. The
# renderer fetches exactly what index.json names and never probes, so a zone file
# left behind here is an HTTP 404 on the deployed walkthrough while the dev tree
# renders perfectly — the same failure the scenes/ subdirectory once caused.
# tools/validate.py --site checks the manifest against what actually landed here.
# The population layer. `data/residents/` carries no geometry by design (L1: no
# human figures), so nothing here is drawn — but the building card now names the
# households attached to a structure, and the Evidence panel and any future "who
# lived here" view read the manifest and the household records straight off the
# site. Until this line existed the whole layer stopped at the repo: ninety-six
# researched people that a visitor had no way to reach, which reads exactly like
# work that was never done.
# PUBLISHED MINIFIED, AND ONLY HERE. The residents layer is 1,380 hand-annotated
# household records whose notes run to paragraphs, and at indent=1 it was 8.8 MB of
# the 32 MB the published tree is allowed — the tree measured 31.999 MB on 2026-09-05
# and the next resident pass of any size could not land. Whitespace is the one thing
# in it a visitor never reads: the renderer fetches these with response.json(). The
# authored files under data/residents/ are untouched and stay diff-readable.
if [ -d data/residents ]; then
  rm -rf "$SITE/data/residents"
  cp -a data/residents "$SITE/data/residents"
  python3 - "$SITE/data/residents" <<'MINIFY'
import json, sys
from pathlib import Path
for q in Path(sys.argv[1]).rglob("*.json"):
    q.write_text(json.dumps(json.loads(q.read_text(encoding="utf-8")),
                            ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
MINIFY
fi

# The business layer. 196 firms compiled from the register — and 166 of them
# have no roof in this town, so a card in the Businesses directory is the ONLY
# place a visitor can reach them. `businesses/index.json` is what the directory
# lists; each `biz_*.json` is fetched when its card opens. Leave this out and the
# section is empty on the deployed site while the dev tree fills it — the
# scenes/, fauna/, residents/ and frontage/ failure, a sixth time. Copied
# verbatim, not minified as the residents are: 1.2 MB is nothing against the
# budget, and a byte-identical mirror is one the publish gate can check by
# comparison rather than one that needs a transform rule and a gate of its own.
if [ -d data/businesses ]; then
  rm -rf "$SITE/data/businesses"
  cp -a data/businesses "$SITE/data/businesses"
fi

# The enclosure layer — fence lines, yards and pens, drawn by
# renderers/web/js/enclosures.js straight from these numbers. It carries no GLB
# by design (an enclosure is a perimeter, not a footprint), so this copy is the
# whole of the layer's payload: leave it out and the fences are a 404 on the
# deployed site while the dev tree draws them perfectly — the same failure the
# scenes/ subdirectory and the fauna directory each caused once already.
if [ -d data/enclosures ]; then
  rm -rf "$SITE/data/enclosures"
  cp -a data/enclosures "$SITE/data/enclosures"
fi

# The signage layer — the boards on the town's business frontages, drawn by
# renderers/web/js/signage.js straight from these numbers. Same argument as the
# enclosures above and the same failure if it is left out: no GLB carries any of
# it, so an unmirrored directory is a 404 on the deployed site while the dev tree
# hangs every board perfectly.
if [ -d data/signage ]; then
  rm -rf "$SITE/data/signage"
  cp -a data/signage "$SITE/data/signage"
fi

# The yard layer — the barrels, cases and the one wagon standing on the town's
# own ground, drawn by renderers/web/js/yard.js straight from these numbers.
# Same argument as the enclosures and the signage above and the same failure if
# it is left out: no GLB carries any of it, so an unmirrored directory is a 404
# on the deployed site while the dev tree stands every barrel perfectly.
if [ -d data/yard ]; then
  rm -rf "$SITE/data/yard"
  cp -a data/yard "$SITE/data/yard"
fi

# The wharf layer — the river docks at the two forwarding warehouses whose own
# records state one, drawn by renderers/web/js/wharves.js straight from these
# numbers. Same argument as the enclosures, the signage and the yard above and
# the same failure if it is left out: no GLB carries any of it, so an unmirrored
# directory is a 404 on the deployed site while the dev tree draws both docks
# perfectly.
if [ -d data/wharves ]; then
  rm -rf "$SITE/data/wharves"
  cp -a data/wharves "$SITE/data/wharves"
fi

# The boat layer — the era-correct watercraft on the river (T-0063), drawn by
# renderers/web/js/boats.js straight from these numbers. Same argument as the
# wharves above and the same failure if it is left out: no GLB carries any of
# it, so an unmirrored directory is a 404 on the deployed site while the dev
# tree floats every hull perfectly.
if [ -d data/boats ]; then
  rm -rf "$SITE/data/boats"
  cp -a data/boats "$SITE/data/boats"
fi

# The well layer — the well heads placed to a coordinate (T-0887), drawn by
# renderers/web/js/wells.js straight from these numbers. Same argument as the
# boats above and the same failure if it is left out: no GLB carries any of it,
# so an unmirrored directory is a 404 on the deployed site while the dev tree
# stands the fort's well perfectly.
if [ -d data/wells ]; then
  rm -rf "$SITE/data/wells"
  cp -a data/wells "$SITE/data/wells"
fi

# The 1904 street grid (T-0474) — carriageways, block faces, alleys and parcels,
# generated by tools/trace_prairie_1904_grid.py and drawn by
# renderers/web/js/street-grid.js straight from these numbers. No GLB carries any
# of it, so an unmirrored directory is a 404 on the deployed /1904/ door.
if [ -d data/street_grid ]; then
  rm -rf "$SITE/data/street_grid"
  cp -a data/street_grid "$SITE/data/street_grid"
fi

# ...and the surfaces it is paved with (T-1728): the authored materials file, and
# for each material the three web maps its material.json names (colour, normal,
# packed ORM) plus the material.json itself, which carries the metric tile the
# renderer reads. FOUR FILES PER MATERIAL AND NOT TWELVE: the PNG masters, the
# DirectX normal, the 16-bit height and the loose AO/roughness/metallic stay in the
# repository, as the roof relief's do. Same asset-base rename as that block:
# textures/ resolves under data/ here and under assets/ in the dev tree.
if [ -d data/street_surfaces ]; then
  rm -rf "$SITE/data/street_surfaces"
  cp -a data/street_surfaces "$SITE/data/street_surfaces"
fi
for sheet in assets/textures/prairie_1904_pbr/*/*/material.json; do
  [ -f "$sheet" ] || continue
  src="$(dirname "$sheet")"
  rel="${src#assets/}"
  id="$(basename "$src")"
  mkdir -p "$SITE/data/$rel"
  cp -f "$sheet" "$src/${id}_basecolor_web.jpg" "$src/${id}_normal_gl_web.jpg" "$src/${id}_orm_web.jpg" \
        "$SITE/data/$rel/"
done

# The frontage layer — the plank walks, the board crossing and the named board
# on its post that stand between a building and the street it fronts on, drawn by
# renderers/web/js/frontage.js straight from these numbers. Same argument as the
# enclosures, the signage, the yard and the wharves above and the same failure if
# it is left out: no GLB carries any of it, so an unmirrored directory is a 404 on
# the deployed site while the dev tree lays every board perfectly.
if [ -d data/frontage ]; then
  rm -rf "$SITE/data/frontage"
  cp -a data/frontage "$SITE/data/frontage"
fi

# T-1275: compact optional loading library, never research assets.
mkdir -p "$SITE/data/loading"
cp data/loading/statuses.json "$SITE/data/loading/statuses.json"

if [ -d data/flora ]; then
  rm -rf "$SITE/data/flora"
  cp -a data/flora "$SITE/data/flora"
fi

# The animal layer (ROADMAP K51). Same argument as the residents above, and it
# was open longer: 139 records across ten habitat zones, every one graded to
# 1 July 1835 and cited, and until this line no browser had ever been offered
# the directory — while data/scenes/1835.json listed `fauna` among the scene's
# layers and two other documents implied a reader existed. Nothing here is
# drawn; the Evidence panel's wildlife section reads it as text.
if [ -d data/fauna ]; then
  rm -rf "$SITE/data/fauna"
  cp -a data/fauna "$SITE/data/fauna"
fi

# The build stamp the gate shows. Written here because publish IS the build: the
# one moment that knows which commit became which deployed tree. Central Time,
# because that is the clock the project's dates are quoted in everywhere else.
BUILD_VERSION=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)
BUILD_ISO=$(date -u +%Y-%m-%dT%H:%M:%SZ)
BUILD_CT=$(TZ=America/Chicago date +"%b %-d, %Y, %-I:%M %p CT")
# Injected as TEXT into the published gate, not fetched. A stamp that needs a
# request is a stamp that 404s in the dev tree and disappears exactly when the
# build is broken enough to matter; this one renders with no JS at all.
STAMP="build $BUILD_VERSION · $BUILD_CT"
# …and the release numbers the What's-new dot counts against (T-1973). The dot asks
# one question at boot — how many releases are newer than the one you last read — and
# answering it by importing js/changelog.js cost every first visit 1.03 MB on the wire,
# 7 % of the boot payload, for a number. The numbers go into the page as ranges
# ("1-1303"); whatsnew.js imports the changelog itself only when the tab is opened.
# Read from the file this same publish mirrors, so the page and the feed cannot
# disagree about which releases exist.
if [ -f "$SITE/walk/index.html" ]; then
  python3 - "$SITE/walk/index.html" "$STAMP" renderers/web/js/changelog.js <<'PYEOF'
import re, sys, pathlib
p, stamp = pathlib.Path(sys.argv[1]), sys.argv[2]
log = pathlib.Path(sys.argv[3]).read_text()
s = p.read_text()
s = s.replace('<p class="gate-build" id="gate-build" hidden><!--BUILD_STAMP--></p>',
              '<p class="gate-build" id="gate-build">' + stamp + '</p>')
entries = re.findall(r'^\s*\{\s*v:\s*(\d+|null)\s*,', log, re.M)
vs = sorted({int(v) for v in entries if v != 'null'})
runs = []
for v in vs:
    if runs and v == runs[-1][1] + 1:
        runs[-1][1] = v
    else:
        runs.append([v, v])
releases = ','.join(f'{a}-{b}' if a != b else f'{a}' for a, b in runs)
meta = '<meta name="c4d-releases" content="">'
if meta not in s or not vs:
    sys.exit(f'publish: cannot write the release numbers ({len(entries)} entries read, '
             f'placeholder {"present" if meta in s else "missing"})')
s = s.replace(meta, f'<meta name="c4d-releases" content="{releases}">')
p.write_text(s)
PYEOF
fi
# THE FRONT DOORS (chicago.polecat.live). The renderer lives at walk/, but nobody is
# sent there: /4d/ and /4d/<year>/ are copies of the STAMPED walk/index.html carrying a
# <base href> into walk/, so the address bar keeps the short path and every relative
# URL still resolves from walk/. This replaces the old opener page that bounced /4d/
# to walk/?year=1835. It runs after the stamp so every door shows the same build.
# Each door keeps walk/index.html's <head> and </body>, which is what
# .github/chicago-4d-dev-preview.mjs marks (robots meta, DEV PREVIEW banner).
rm -f "$SITE/index.html"
node tools/write_entry_pages.mjs "$SITE"

# build.json — the machine-readable twin of the stamp above. It was written ONCE,
# by hand, and then never again: the gate added in R-BUG3c-b's wake found it
# claiming version 8909332 built 2026-08-13 while the mirror beside it was two
# days newer. Anything reading it — tools/test_dev_preview.mjs, docs/PIPELINE.md —
# was reading a stale claim about what shipped. It is regenerated every publish
# now, from the same two variables the visible stamp uses, so the two cannot
# disagree.
cat > "$SITE/build.json" <<JSON
{
  "version": "$BUILD_VERSION",
  "built_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "built_ct": "$BUILD_CT"
}
JSON

echo "   build $BUILD_VERSION  $BUILD_CT"

# PORTABLE SIZE (T-0727): `du -sb` is GNU-only and dies on the macOS stewards
# (exit 64, whole publish marked failed after every byte landed). wc -c over
# the same files is the exact byte count on both flavors.
BYTES=$(find "$SITE" -type f -exec wc -c {} + | tail -1 | awk '{print $1}')
printf 'published %s  (%.2f MB)\n' "$SITE" "$(echo "scale=4; $BYTES/1048576" | bc)"
