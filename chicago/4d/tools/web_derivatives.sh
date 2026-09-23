#!/usr/bin/env bash
# The web-derivative step, on its own: assets/gltf/*.glb -> assets/web/*.glb by
# `gltf-transform` alone. NO BLENDER, which is the whole point of it living here.
#
#   tools/web_derivatives.sh              regenerate every derivative
#   tools/web_derivatives.sh --out DIR    write somewhere else (measuring)
#   tools/web_derivatives.sh --only NAME  one file, by basename
#
# It was lifted out of `tools/bake.sh` by K36(b) unchanged — bake.sh calls this
# and nothing else does the work, so the bytes a nightly ships and the bytes a
# steward run can regenerate on a Blender-free runner are produced by ONE
# implementation. That mattered before it was possible: K36(a) found the
# data -> master -> derivative -> mirror chain gated at links 1 and 3 and not at
# link 2, and a repair to link 2 that could only be exercised inside a nightly
# is a repair nothing can measure.
#
# Verified byte-for-byte at the extraction: running this over the committed
# masters reproduces all 334 committed derivatives exactly, md5 for md5, on
# gltf-transform 4.4.2 — the release current at the extraction. The pin this
# sentence holds under NOW is fixed below (T-0537); it has read 4.5.0 since
# 2026-09-16, and the sentence is only true under the pinned version, whichever
# one a given commit carries.
#
# PINNED 2026-09-16 (T-0537) AT 4.5.0 — the toolchain is fixed in this file, not
# resolved from the calendar. `npx --yes @gltf-transform/cli` used to mean
# "whatever npm calls latest today", and that was measured twice, not theorised:
# on 2026-09-03 (T-0430) and again on 2026-09-13 (T-0332's branch) an upstream
# release moved the resolved version 4.4.2 -> 4.5.0 and every derivative the step
# touched came back with a TWO-BYTE diff — `{"generator":"glTF-Transform v4.5.0"}`
# — and nothing else: 196 of 384 files in one PR, pure stamp noise burying
# whatever it carried. And the caret is transitive: `@gltf-transform/cli@4.4.2`
# depends on `@gltf-transform/core@^4.4.2`, so pinning the CLI alone still stamps
# whatever the caret resolves to — which is how the 2026-09-03 reading was
# confirmed rather than guessed.
#
# THE FORK THE TICKET OFFERED, AS FOUND, NOT CHOSEN IN THE ABSTRACT: pin at 4.4.2
# and restamp the tree, or move to the current release deliberately and pin there.
# The move had ALREADY happened — 381 of 384 committed derivatives carry the
# v4.5.0 stamp tonight, landed bake by bake as a side effect, which is the whole
# disease — so pinning at 4.4.2 would have churned all 381 the other way. The pin
# therefore reads 4.5.0: the churn the ticket feared is bought back by making the
# state that already exists undeletable-by-calendar, not by moving 381 files to
# make a point. A future release (4.6.x) now CANNOT restamp the tree as a side
# effect; moving to it is a deliberate one-commit decision that regenerates all
# 384 derivatives and nothing else.
#
# Hence the pin names cli, core, functions AND extensions — every @gltf-transform
# package this step can reach — each at an exact version, installed together in
# one npx invocation so npm's dedupe cannot mix releases (functions/extensions
# carry the same transitive caret as core). The step then proves the resolution
# before it touches a byte: it fails if the resolved CLI version differs from the
# pin, and every transformed derivative is checked for the pinned stamp before it
# is accepted.
#
# THAT SENTENCE WAS NOT TRUE WHEN IT WAS WRITTEN — K36(b)'s own control measured
# 243 of 334, and the 91 it did not reproduce are the two findings it deferred:
# the 90 placeholder passthroughs (K37, decided below — the passthrough is right
# and the step now produces it) and the terrain derivative (R-W6(b), still open).
# With the size rule below in place, and K37's three repairs applied, it
# reproduces 331 of 334. The three it does not are named, not rounded off:
# `terrain__e1834_harbor_cut.glb` (committed at 14 bits, asked for at 16 —
# R-W6(b) owns it) and the two placeholders that compress SMALLER, which stay
# master copies because `generators/inferred_placeholder.py` rewrites the web
# tree from the master on every run and would undo them. See K37's open end.
#
# AND THAT SENTENCE IS NOT TRUE EITHER — measured 2026-08-16 by K39, which needed a
# reproduction control to verify its own record and could not get one. On a 20-asset
# spread sample of the compressed derivatives, **6 reproduced and 14 did not**, and
# every one of the 14 reproduces BYTE FOR BYTE under `BAKE_PALETTE=1`. The palette pass
# K36(b) turned off (for measured draw-call reasons that stand) was also WELDING these
# files, and K36(b) regenerated only the 38 that carried the material fault. So
# `assets/web/` is a mixture of two transformations: **195 of the 241 compressed
# derivatives carry fewer vertices than their masters**, which only the palette-era step
# produces, and 10,513 vertices in total. Nothing is wrong with the bytes on the site —
# a weld is lossless and assertions 1-9 are green on all of them — but this script does
# not produce them, and the next nightly bake will rewrite all 195 as unwelded files.
# ROADMAP K40 owns the count, the payload delta and the decision. Do not quote "331 of
# 334": it is the claim K40 exists to correct.
#
# COUNTED EXACTLY 2026-08-16 BY K40, with the control this script had never had —
# `tools/measure_web_reproduction.py`, which runs THIS script over all 334 masters into a
# scratch tree, chunked to fit the ten-minute per-command ceiling, and compares md5s.
# The number is **142 of 334**, and the 192 failures decompose with nothing left over:
# **189 reproduce byte-for-byte under `BAKE_PALETTE=1`** (the palette-era set, +48,836
# bytes to regenerate, mean +258 each, 10,491 vertices merged) plus the three already
# owned above — the two K37 placeholders and R-W6(b)'s terrain. Do not quote 195 either:
# it is a VERTEX signature and K40 measured it against the exact set, where SIX welded
# files reproduce here exactly (`optimize` dedups without the palette pass) and three
# failures carry no weld. The signature is not the set and no gate is built on it.
#
# AND THE SENTENCE AT THE TOP IS TRUE AFTER ALL, WHICH IS THE POINT OF THE CONTROL:
# on all 189, the bytes this script produces on a Blender-free runner are md5-identical
# to the bytes the nightly bake put in PR #175. What was wrong was never the extraction —
# it was that a step change had not been carried through the whole tree. Hence:
#
#   A CHANGE HERE THAT MOVES ANY DERIVATIVE'S BYTES REGENERATES ALL 334, NOT THE ONES
#   THAT VISIBLY BROKE.
#
# K36(b) turned the palette pass off and regenerated the 38 assets whose material
# identity it had broken; the other 195 kept bytes no step in this tree could produce,
# and it cost three days and two parcels to find out. K40 decided against recording the
# STEP beside the master for the same reason a hash of this file would be wrong: the
# four commits that have changed this script since it was extracted moved 38, 3, 0 and 0
# derivatives, so a script hash would have invalidated all 334 entries four times, twice
# on a commit that moved no byte. See docs/RESEARCH/web-reproduction.md.
set -euo pipefail
cd "$(dirname "$0")/.."

OUT=assets/web
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --out) OUT="$2"; shift 2 ;;
    --only) ONLY="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

# WHAT THIS STEP KNOWS AND NOTHING ELSE DOES — ROADMAP K39.
#
# It knows which master it just compressed. Until K39 it wrote that down nowhere, so
# "is this derivative stale?" was answered by a TIMESTAMP: publish.sh compared mtimes,
# and K38 measured that on a fresh clone `git checkout`'s write order makes 334 of 334
# masters older than their derivatives — silent on exactly the tree a steward run
# starts from. Assertions 1-8 in tools/measure_web_derivatives.py compare a derivative
# to whatever master sits beside it TODAY and never ask whether that is the one it came
# from, so a master rebuilt with the same geometry and different _CONFIDENCE values
# passed all of them. That is the failure publish.sh's own comment was written about.
#
# So the step records `name -> sha256(master)` into assets/manifest.web.json as it
# produces each file, and assertion 9 turns staleness into a hash comparison. It sits
# beside assets/manifest.json because the two are the two links of one chain: that one
# records data -> master and is written by the Blender build, this one records
# master -> derivative and is written by the step after it.
#
# THE COUPLING, DECIDED (K39 asked for the decision before the file): the STEP writes
# it, on every run, and a bake carries the diff. The record's lifecycle is the
# derivative's — same producer, same run, same commit — so a nightly that regenerates
# geometry rewrites the record in the same breath and cannot leave the dev gate red for
# everyone else. tools/bake.sh's only web-derivative call is this script, and the bake
# workflow commits `chicago/4d` whole, so this needs no workflow change. Banking it by
# hand was the alternative and it is the failure this project has now measured twice: a
# record a person maintains describes the tree as it was when they last remembered.
# It is NOT in tools/web_derivative_baseline.json for the same reason — that file is a
# record of FAULTS a person banks deliberately, and a map that changes on every bake
# would train everyone to run --write-baseline without reading it.
#
# It is written by this script and read by the gate. There is no flag anywhere that
# rewrites it without regenerating the bytes it describes: the remedy for a stale
# derivative is `tools/web_derivatives.sh --only NAME`, never an edit of the record.
RECORD="assets/manifest.web.json"
PRODUCED="$(mktemp -t webderiv.XXXXXX)"
trap 'rm -f "$PRODUCED"' EXIT

record_masters() {
  # Only ever for the canonical tree — a --out run is a MEASUREMENT and must not
  # author a claim about what the repository ships.
  [ "$OUT" = "assets/web" ] || return 0
  [ -s "$PRODUCED" ] || return 0
  python3 - "$RECORD" "$PRODUCED" "${ONLY:-}" <<'PY'
import hashlib, json, pathlib, sys

record, produced, only = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), sys.argv[3]
names = [n for n in produced.read_text().split() if n]

# A full run rewrites the map whole, so a deleted asset's entry goes with it. A
# --only run merges, because it has nothing to say about the other 333.
masters = {}
if only and record.exists():
    masters = json.loads(record.read_text()).get("masters", {})
for name in names:
    src = pathlib.Path("assets/gltf") / name
    masters[name] = hashlib.sha256(src.read_bytes()).hexdigest()

record.write_text(json.dumps({
    "$note": "ROADMAP K39. sha256 of the MASTER each derivative in assets/web/ was "
             "produced from, written by tools/web_derivatives.sh in the "
             "same run that produced the bytes, and read by "
             "tools/measure_web_derivatives.py assertion 9. It answers 'has the master "
             "been rebuilt since?' from CONTENT rather than from a timestamp — mtime "
             "cannot, because on a fresh clone every master is older than its "
             "derivative by checkout order (K38, measured 334 of 334). DERIVED, and "
             "not bankable: the remedy for a mismatch is "
             "`tools/web_derivatives.sh --only <name>`, never an edit of this file. It "
             "names the MASTER, not the STEP — a derivative made by an older flag set "
             "from this same master is recorded correctly here and reproduces nothing "
             "(ROADMAP K40).",
    "written_by": "tools/web_derivatives.sh",
    "masters": dict(sorted(masters.items())),
}, indent=2) + "\n", encoding="utf-8")
print(f"   recorded {len(names)} master hash(es) in {record}")
PY
}

echo "== web derivatives"

# THE PIN (T-0537) — exact versions, all four packages, one npx invocation.
# Pinned at 4.5.0 because that is the release the committed tree already carries
# (381 of 384 derivatives stamp v4.5.0, landed bake by bake — see the header).
# npx installs every --package into one throwaway env and caches by spec, so this
# resolution is a function of this file and not of the date. Do not "just" pin
# the CLI: it depends on core/functions/extensions by caret, and a bare CLI pin
# still stamps whatever those carets resolve to (measured 2026-09-03, T-0430).
GT_CLI_VERSION="4.5.0"
GT_CORE_VERSION="4.5.0"
GT_FUNCTIONS_VERSION="4.5.0"
GT_EXTENSIONS_VERSION="4.5.0"
GT_NPX=(npx --yes
  --package "@gltf-transform/cli@$GT_CLI_VERSION"
  --package "@gltf-transform/core@$GT_CORE_VERSION"
  --package "@gltf-transform/functions@$GT_FUNCTIONS_VERSION"
  --package "@gltf-transform/extensions@$GT_EXTENSIONS_VERSION")

# Prove the resolution before any derivative is touched. A mismatch means the
# pin variables and the invocation below disagree — a bug in THIS file, not bad
# luck — and stamping 384 files with an unpinned version is the exact failure
# this block exists to stop.
resolved_cli="$("${GT_NPX[@]}" gltf-transform --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 || true)"
if [ -n "$resolved_cli" ] && [ "$resolved_cli" != "$GT_CLI_VERSION" ]; then
  echo "   FATAL: npx resolved gltf-transform $resolved_cli but this script pins $GT_CLI_VERSION." >&2
  echo "   The pin and the invocation disagree (T-0537). Fix the script; do not run unpinned." >&2
  exit 1
fi

if [ -n "$resolved_cli" ]; then
  mkdir -p "$OUT"
  # `--texture-compress ktx2` shells out to the KTX-Software `ktx` binary, and
  # gltf-transform aborts the WHOLE optimize when it is absent — meshopt included.
  # ubuntu-latest does not ship `ktx` and neither does the dev container, so that
  # flag silently turned every derivative into an uncompressed copy of its master,
  # in every environment, since this step was written. Nothing has a texture yet,
  # so ask for KTX2 only where it can actually run.
  # KTX2 IS OFF, AND THE `ktx` BINARY BEING PRESENT IS NOT ENOUGH TO TURN IT ON.
  #
  # This used to read `if command -v ktx; then --texture-compress ktx2`, which
  # asks the wrong question. Whether the TOOL can write KTX2 says nothing about
  # whether the RENDERER can read it — and it cannot: the vendored GLTFLoader
  # only handles KHR_texture_basisu after `setKTX2Loader()` is called, nothing
  # calls it, and no Basis transcoder is vendored (it would need to be, since
  # renderers/web/ takes no CDN).
  #
  # Observed the moment `ktx` was installed on the runner (bake run
  # 31773216178): three derivatives came back with KTX2 textures, and the smoke
  # got `THREE.GLTFLoader: setKTX2Loader must be called before loading KTX2
  # textures` for each of them. An asset that throws in the loader is an asset
  # that is not in the scene, so it also took out the raycast, inspection and
  # ground-contact checks downstream. The bake never reached its push step, so
  # none of it left the runner.
  #
  # Turning this on is part of W2 (docs/RENDERING.md), and the order is: wire
  # KTX2Loader + a vendored transcoder into the renderer FIRST, prove it loads a
  # textured asset, and only then set BAKE_KTX2=1 here.
  # POSITION PRECISION IS PER-MESH, AND ONE MESH IN THIS TOWN IS 5 KM WIDE.
  #
  # `gltf-transform` quantises POSITION to a bit depth under ONE UNIFORM node
  # scale set by the mesh's own bounding box, so the rung spacing an asset lands
  # on is its own widest axis over 2^bits — nothing to do with how big its
  # details are. Measured on the 244 derivatives that ship quantised
  # (tools/measure_terrain_horizontal.mjs, and the per-asset scan in R-W6):
  #
  #   water__e1834_harbor_cut   330.8 mm  ) the two epoch-scale meshes: a 2,020 m
  #   terrain__e1834_harbor_cut 306.4 mm  ) box plus 1.5 km of skirt on each side
  #                                       ) (the skirt is 1,549.921875 m now, and
  #                                       )  that number is derived — see below)
  #   north_pier                 16.8 mm
  #   every other asset          ≤ 4.8 mm, median 0.5 mm
  #
  # At 14 bits the ground therefore ships on a 306 mm lattice, which R-BUG3c
  # found buries the road, and the town's OTHER 242 assets ship at half a
  # millimetre, which is precision nobody asked for and nothing can see. So the
  # bit depth is raised where it is needed and left alone where it is not:
  # 16 bits on the epoch meshes costs 1,116 bytes and takes the ground's lattice
  # to 76.6 mm and its worst drawn-surface error from 46.3 mm to 12.9 mm — under
  # the 22 mm road lift at every one of the field's 259,689 sample points. Asking
  # for 16 bits EVERYWHERE was measured too: +105.7 KB on a 4.47 MB payload
  # (+2.4 %) to buy nothing measurable, so it is not done. See R-W6.
  #
  # AND THE BIT DEPTH IS NO LONGER WHAT HOLDS THE GROUND — T-0152, 2026-08-23.
  # 12.9 mm became 77.1 mm without this step changing at all: the ground was
  # extended east onto bank faces at 60-90 %, and the cost of this quantiser is
  # (slope x plan displacement), so steeper ground is a tighter consumer of the
  # same rung. 16 bits is the format's maximum and the master is 5.8 MB too fat
  # to pass through, so neither of the two obvious answers was available.
  # `generators/terrain_gen.py` now DERIVES the skirt margin instead, so that the
  # uniform scale this step takes from the mesh's widest axis makes the rung an
  # exact submultiple of the 2.5 m terrain grid — the cell over 32, 78.125 mm.
  # Every ground vertex then stands on a rung and quantising rounds it to itself:
  # plan displacement 0.0 mm, drawn surface 6.7 mm worst, which is the master's
  # own decimation and nothing of this step's. `k` is a power of two on purpose,
  # so lowering EPOCH_QUANT_BITS multiplies the rung by a power of two and leaves
  # it commensurate — this step and that generator are not coupled through the
  # number below. `tools/measure_terrain_horizontal.mjs --gate` holds it.
  #
  # `optimize` has no --quantize-position, so compression moves to the `meshopt`
  # command in a second pass. Verified byte-for-byte: `optimize --compress false`
  # followed by a default `meshopt` reproduces the file this step shipped before,
  # exactly — the ONLY thing that changes below is the bit depth.
  EPOCH_QUANT_BITS="${EPOCH_QUANT_BITS:-16}"
  ASSET_QUANT_BITS="${ASSET_QUANT_BITS:-14}"
  compress=(--compress false)
  if [ "${BAKE_KTX2:-0}" = "1" ]; then
    if command -v ktx >/dev/null 2>&1; then
      echo "   BAKE_KTX2=1 — asking for KTX2 textures (the renderer MUST have setKTX2Loader wired)"
      compress+=(--texture-compress ktx2)
    else
      echo "   BAKE_KTX2=1 but no ktx binary on PATH; meshopt only"
    fi
  fi

  # NEVER SIMPLIFY. `optimize` runs mesh simplification BY DEFAULT, and on this
  # dataset that is not an optimisation, it is damage:
  #
  #   • The terrain is already decimated, deliberately, by generators/terrain_gen.py
  #     at a tolerance it MEASURES — it ray-casts the decimated mesh against the
  #     heightfield and refuses to export past 30 mm of drift. That number is the
  #     promise that the ground you stand on is the ground you see. A second,
  #     blind simplification pass with its own error budget breaks the promise
  #     silently and leaves nothing to measure it against.
  #   • Observed, not theorised: the ground went from 56,463 vertices per tile to
  #     about 100, and 33 of one tile's 99 remaining vertices came back with
  #     normals pointing DOWNWARD (normal.y = -1) — a hard-edged black polygon
  #     across the south-east of the town, visible from the air. The terrain had
  #     never been through this step before (it was the one asset gltf-transform
  #     had never run over), so nobody had seen what it does to a large, low-relief
  #     surface.
  #   • The buildings are authored low-poly from archetype parameters. There is no
  #     fat here for a simplifier to find, and the same class of normal damage on a
  #     clapboard wall would be far harder to spot.
  #
  # meshopt still does the compression work; simplification was never what made
  # the payload small.
  compress+=(--simplify false)

  # NEVER PALETTE, EITHER — K36(b), and the reason is the opposite of the one
  # the flag advertises.
  #
  # `optimize`'s palette pass folds a file's named materials into one
  # `PaletteMaterial` plus two generated PNGs whenever the file carries five or
  # more of them. It is sold as a draw-call saving, and inside one glTF file it
  # is. In THIS renderer it is a draw-call COST, measured on the mirror a
  # visitor is served rather than argued from the flag's documentation:
  #
  #   • `materialKey()` in renderers/web/js/buildings.js batches by material,
  #     and a texture is part of the key — a GLTFLoader mints a fresh uuid per
  #     loaded texture, so an asset arriving with its own generated palette map
  #     cannot join ANY batch, not even another palette asset's.
  #   • So the 38 faulted assets shipped as 40 single-building batches on top of
  #     the town's 16, and the published town drew 56 batches where R-W5a's
  #     number — taken against the SOURCE tree — was 16. Turning the pass off
  #     merges all 40 back in: 56 -> 16 batches, measured on the mirror.
  #   • A batch holding one building is culled with that building, so the cost
  #     is paid per POSE and it is worst where the town is densest. Measured at
  #     the eight scene anchors, 1280x800, before -> after:
  #
  #       green_tree 102 -> 70   forks  96 -> 68   from_above 84 -> 63
  #       south_water 82 -> 69   lake_market 71 -> 63   sauganash_wing 68 -> 61
  #       first_post_office 66 -> 60   sauganash 62 -> 59
  #
  #     FOUR OF THE EIGHT WERE OVER THE 80 BUDGET on the site. None is now, and
  #     the worst anchor falls 102 -> 70.
  #   • The payload it "saves" is a cost too: dropping the pass takes the 38
  #     from 318,540 to 505,932 bytes (+187,392, +58.8 % of those files, +4.1 %
  #     of the 4.5 MB tree against a 25 MB budget). The generated PNGs are
  #     cheaper on disk than 197 named materials and dearer in every other
  #     currency the renderer counts.
  #
  # It also silently deleted the names those assets were baked with — `log`,
  # `chinking`, `board`, `roof`, `dark`, `interior` — which is what K36(a) found
  # and what R-W2b needs back before it can wire an atlas onto them.
  #
  # `BAKE_PALETTE=1` restores the old behaviour for anyone who wants to
  # re-measure. Nothing in the pipeline sets it.
  if [ "${BAKE_PALETTE:-0}" = "1" ]; then
    echo "   BAKE_PALETTE=1 — palette pass ON (it costs draw calls here; see K36(b))"
  else
    compress+=(--palette false)
  fi

  # KEEP THE SMALLER FILE — K37, and the rule is a MEASUREMENT, not a class.
  #
  # `meshopt` writes an EXT_meshopt_compression header, a buffer-view table and
  # an index buffer. On a big mesh those are free; on a 30-triangle shed they
  # are most of the file, and the derivative comes out LARGER than the master it
  # was compressed from. Measured 2026-08-16 over the whole tree:
  #
  #   • the 90 flagged placeholders, compressed here for the first time:
  #     520,700 -> 628,028 bytes, +107,328 (+20.6 %). 88 of the 90 grow.
  #   • and it is not a placeholder property, in EITHER direction. THREE assets
  #     that have always been through this step ship bigger than their master
  #     today — fort_dearborn_root_house (+324), lake_house_construction (+240),
  #     fort_dearborn_magazine (+224) — while fort_dearborn_parade, 30 triangles
  #     and 5,504 bytes, compresses to -24.5 %. And two of the ninety
  #     placeholders go the other way (-808 and -816 bytes, both -9.3 %).
  #     Nothing about the asset's KIND predicts the sign; only measuring it does.
  #
  # K36(a) reported the 90 as an anomaly and K36(b)'s control found that this
  # step does not reproduce them. Both readings were right and neither was the
  # rule: the passthrough is CORRECT for those files, it was just arrived at by
  # the accident of `generators/inferred_placeholder.py` writing the same bytes
  # into both trees rather than by anything deciding it. So decide it here,
  # per file, from the bytes — a derivative that is not smaller than its master
  # has no reason to exist, and `tools/measure_web_derivatives.py` asserts the
  # outcome so the 91st cannot appear silently.
  #
  # A passthrough is not a degraded derivative. It is the master, so it carries
  # exact float positions instead of a quantised lattice, and it satisfies every
  # assertion that gate makes about identity, triangles and bounds by construction.
  # 90 assets have shipped this way to visitors since 2026-08-11.
  #
  # THE TWO EPOCH MESHES ARE EXCLUDED, DELIBERATELY AND BY NAME. `water__` is
  # +744 bytes (+55.0 %) under this rule and would be passed through by it — but
  # the epoch derivatives' bit depth is a GEOMETRIC decision (R-W6 set
  # EPOCH_QUANT_BITS against measured drawn-surface error, and the ground and the
  # waterline are what R-BUG3c, R-BUG4 and R-M1a all measure against), and
  # a payload rule does not get to move that. The exclusion is recorded in the
  # gate too, with its number.
  #
  # R-W6(b) used to be the second half of this sentence — it held both files
  # pending the owner's word on regenerating geometry outside a bake. It is
  # CLOSED (T-0151, 2026-08-23): a nightly bake shipped the 16-bit ground, the
  # committed derivative reproduces md5-for-md5 at 16 bits and not at 14, and
  # `tools/measure_terrain_fit.mjs --gate` now ASSERTS the shipped depth instead
  # of printing it. The surface error left on the ground as extended east (77.1 mm
  # worst, 56 samples past the road lift, on 60-90 % slopes) is CLOSED too —
  # T-0152, and it was a generator question rather than a bit-depth one: see the
  # derived skirt margin above.
  fellback=0
  passthrough=0
  for f in assets/gltf/*.glb; do
    [ -e "$f" ] || continue
    [ -z "$ONLY" ] || [ "$(basename "$f")" = "$ONLY" ] || continue
    out="$OUT/$(basename "$f")"
    case "$(basename "$f")" in
      terrain__*|water__*) bits="$EPOCH_QUANT_BITS"; epoch=1 ;;
      *) bits="$ASSET_QUANT_BITS"; epoch=0 ;;
    esac
    tmp="$(mktemp -t gltfopt.XXXXXX.glb)"
    if "${GT_NPX[@]}" gltf-transform optimize "$f" "$tmp" "${compress[@]}" 2>&1 | tail -2 \
      && "${GT_NPX[@]}" gltf-transform meshopt "$tmp" "$out" \
        --quantize-position "$bits" 2>&1 | tail -2; then
      # The stamp is the pin's receipt: a transformed derivative must say it was
      # made by the pinned core. Anything else means the toolchain moved under
      # an exact version, and banking 384 calendar-stamped files is the failure
      # T-0537 exists to stop — refuse before the bytes reach the tree.
      stamp="$(strings "$out" 2>/dev/null | grep -o 'glTF-Transform v[0-9][0-9.]*' | head -1 || true)"
      if [ "$stamp" != "glTF-Transform v$GT_CORE_VERSION" ]; then
        echo "   FATAL: $(basename "$f") is stamped '$stamp' but this step pins" >&2
        echo "   glTF-Transform v$GT_CORE_VERSION (T-0537). The toolchain moved" >&2
        echo "   under an exact version; refusing to write bytes no pin can describe." >&2
        rm -f "$tmp"
        exit 1
      fi
    else
      echo "   optimize failed for $(basename "$f"); copying the master through"
      cp "$f" "$out"; fellback=$((fellback + 1))
    fi
    rm -f "$tmp"
    note=""
    # PORTABLE SIZE, T-0537: `stat -c%s` is GNU-only and fails on the macOS
    # steward runners, which silently disabled the passthrough rule below
    # (the comparison read empty sizes and never fired, so the three K37
    # assets came back compressed BIGGER than their masters). `wc -c <` is
    # the same answer on both flavors.
    if [ "$epoch" = "0" ] && [ "$(wc -c < "$out" | tr -d ' ')" -ge "$(wc -c < "$f" | tr -d ' ')" ]; then
      cp -f "$f" "$out"
      passthrough=$((passthrough + 1))
      note="  (compression grew it; master passed through)"
    fi
    echo "$(basename "$f")" >> "$PRODUCED"
    printf '   %s  %s -> %s bytes%s\n' "$(basename "$f")" \
      "$(wc -c < "$f" | tr -d ' ')" "$(wc -c < "$out" | tr -d ' ')" "$note"
  done
  # Say it once, at the end, where it cannot scroll past unnoticed. A fallback
  # copy is CORRECT but fat, and a fat payload is what fails the 25 MB gate —
  # so the reason has to be visible next to the number.
  if [ "$fellback" -gt 0 ]; then
    echo "   WARNING: $fellback derivative(s) fell back to an uncompressed master copy"
  fi
  if [ "$passthrough" -gt 0 ]; then
    echo "   $passthrough derivative(s) kept as a master passthrough — compressing them"
    echo "   makes them bigger, which is a decision now and not an accident (K37)"
  fi
  # Every branch above that copies a master through — the deliberate size rule, the
  # optimize fallback, and the no-tool fallback below — produces a derivative that is
  # byte-identical to its master, and assertion 8 (K38) fails on any such file that is
  # not banked by name. That is the point: the two fallbacks are ACCIDENTS wearing the
  # deliberate rule's clothes, and until K38 nothing could tell them apart. So say what
  # closes the loop, here, rather than leaving it to be discovered on the dev gate.
  if [ "$OUT" = "assets/web" ] && [ -z "$ONLY" ]; then
    echo "   if the passthrough set moved, bank it in the same commit:"
    echo "     python3 tools/measure_web_derivatives.py --write-baseline"
  fi
else
  # A FOURTH passthrough path, and the widest: no tool means every one of the 334
  # derivatives becomes an uncompressed master copy — a ~4.6x payload against a 25 MB
  # budget. It warned and nothing gated it. Assertion 8 does now.
  echo "   gltf-transform unavailable; copying masters to assets/web unoptimised"
  echo "   WARNING: every derivative is now a master copy. tools/check.sh will fail"
  echo "   assertion 8 (K38) on all of them, which is correct — do not bank it."
  mkdir -p "$OUT" && cp -f assets/gltf/*.glb "$OUT/" 2>/dev/null || true
  # This branch is a writer too, and the record says what was written rather than what
  # was intended — a copy IS what came out of this step here. Assertion 8 is what says
  # it should not have.
  for f in assets/gltf/*.glb; do
    [ -e "$f" ] || continue
    [ -z "$ONLY" ] || [ "$(basename "$f")" = "$ONLY" ] || continue
    echo "$(basename "$f")" >> "$PRODUCED"
  done
fi

record_masters

