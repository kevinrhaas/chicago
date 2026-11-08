#!/usr/bin/env bash
# The content build. Minutes, not seconds — runs on demand and nightly, NOT on
# every commit. tools/check.sh is the per-commit gate and needs no Blender.
#
#   tools/bake.sh                 build everything (derives only the masters
#                                 whose bytes moved — T-2314; BAKE_DERIVE_ALL=1
#                                 derives every one)
#   tools/bake.sh --only <id>     build one structure
#   tools/bake.sh --only a,b,c    build several, in one Blender start-up
#                                 (either form derives only the masters it built)
#   tools/bake.sh --no-bake       skip the UV unwrap (fast iteration)
#   SKIP_GATE=1 tools/bake.sh     leave check.sh to the caller (CI runs it in parts)
#
# AO is NOT baked here and never has been in the nightly: `--ao` is opt-in on
# generators/build.py and nothing passes it (T-0015). This line used to say
# `--no-bake` skips "AO baking", which read as though AO were on by default.
#
# Blender is pinned by exact version + sha256 in generators/blender.pin. Version
# pinning is what buys back determinism from a stateful tool; determinism itself
# is defined on INPUTS (see assets/manifest.json), because Cycles AO is not
# bit-reproducible across hardware. (Glessner's granite occlusion, the one Cycles bake
# in the build, reuses its committed atlas in assets/bakes/ when the mesh matches — T-2431.)
set -euo pipefail
cd "$(dirname "$0")/.."

# shellcheck disable=SC1091
source generators/blender.pin

CACHE="${BLENDER_CACHE:-/opt/blender-dl}"
BIN="$CACHE/$BLENDER_DIR/blender"
TARBALL="$CACHE/$(basename "$BLENDER_URL")"

fetch_blender() {
  mkdir -p "$CACHE"
  if [ ! -x "$BIN" ]; then
    if [ ! -f "$TARBALL" ]; then
      echo "fetching Blender $BLENDER_VERSION ..."
      curl -fL --retry 3 -o "$TARBALL" "$BLENDER_URL"
    fi
    echo "$BLENDER_SHA256  $TARBALL" | sha256sum -c - || {
      echo "SHA256 MISMATCH on the Blender tarball — refusing to run."
      echo "Either the download is corrupt or blender.pin is wrong. Do not 'fix'"
      echo "this by updating the hash without knowing why it changed."
      exit 1
    }
    tar -xf "$TARBALL" -C "$CACHE"
  fi
  "$BIN" --version | head -1
}

echo "== Blender"
fetch_blender

# T-1653. A `--only` bake derives the masters its build wrote and no others. Until
# this, the step below ran over every master in the tree whatever was selected — ~570
# of them, two npx start-ups each, about eighteen minutes — so re-baking one roof cost
# a run more of its 600-second foreground ceiling than the bake itself did. build.py
# writes the list (`--wrote`), because only it knows which phases and versions a
# selection resolved to; this passes it on unread. A bake with no selection still runs
# the whole step, which is also what rewrites assets/manifest.web.json whole.
SELECTED=0
for arg in "$@"; do
  case "$arg" in --only|--only=*) SELECTED=1 ;; esac
done
WROTE="$(mktemp -t bakewrote.XXXXXX)"
trap 'rm -f "$WROTE"' EXIT

echo
echo "== generate + bake"
# T-2492. A selection naming only pure-Python archetypes (below) is one Blender builds
# nothing for, and build.py says so with its own status, NOTHING_FOR_BLENDER
# (generators/common/selection.py) — under `set -e` its old `1` ended the bake here,
# before the emitters that build those ids ever ran. That status goes on to them, and
# only for a selection; every other non-zero still stops the bake. If nothing below
# writes a master either, the empty-list guard under "web derivatives" refuses.
NOTHING_FOR_BLENDER=3
BUILT=0
"$BIN" -b -noaudio --factory-startup --python generators/build.py -- "$@" --wrote "$WROTE" || BUILT=$?
if [ "$BUILT" != "0" ]; then
  if [ "$SELECTED" = "1" ] && [ "$BUILT" = "$NOTHING_FOR_BLENDER" ]; then
    echo "   Blender built nothing for this selection; the pure-Python emitters run next (T-2492)"
  else
    echo "   generators/build.py exited $BUILT — stopping the bake." >&2
    exit "$BUILT"
  fi
fi
# T-2266: the K01 assemblies write their glTF in pure Python (no Blender, seconds), and
# hand what they wrote to the same list, so a bake derives and publishes them too.
python3 generators/k01_emit.py "$@" --wrote "$WROTE"
# T-2306: and the K13 conservatories a structure record names, the same way.
python3 generators/k13_emit.py "$@" --wrote "$WROTE"
# T-2323: and the K16 timber fronts a structure record names, the same way.
python3 generators/k16_emit.py "$@" --wrote "$WROTE"
# T-2321: and the K12 coach houses a structure record names, the same way.
python3 generators/k12_emit.py "$@" --wrote "$WROTE"
# T-2329: and the Prairie district draft's houses, the same way.
python3 generators/draft_emit.py "$@" --wrote "$WROTE"
# T-2510: and the haystacks, the same way (one stack to a record, at Lee's Place in 1812).
python3 generators/haystack_emit.py "$@" --wrote "$WROTE"
# T-3342: and the Potawatomi camp's groups of 1812, the same way.
python3 generators/lodge_camp_emit.py "$@" --wrote "$WROTE"

echo
echo "== web derivatives"
# Lifted out whole by K36(b) into `tools/web_derivatives.sh`, so a
# Blender-free runner can regenerate the derivatives from the committed
# masters and MEASURE the result. The flags, the bit depths and the reasons
# all live over there, and this is their only caller.
if [ "$SELECTED" = "1" ]; then
  if [ ! -s "$WROTE" ]; then
    echo "   the selection built no master, so there is nothing to derive — see the" >&2
    echo "   skip lines above. Refusing to go on to publish a tree this bake did not touch." >&2
    exit 1
  fi
  echo "   $(wc -l < "$WROTE" | tr -d ' ') master(s) built by this selection; deriving those alone (T-1653)"
  tools/web_derivatives.sh --only "$(paste -sd, "$WROTE")"
elif [ "${BAKE_DERIVE_ALL:-0}" = "1" ]; then
  echo "   BAKE_DERIVE_ALL=1 — deriving every master"
  tools/web_derivatives.sh
else
  # T-2314. The whole town rebuilt, but a master whose bytes match the record of
  # what its derivative was made from needs nothing: deriving all ~714 took about
  # twenty minutes and pushed the content-build job past its thirty-minute ceiling.
  # The rule and its self-test live in tools/stale_derivatives.py.
  #
  # T-3503. Glessner's v4 derivatives are untracked (a verified package, materialized
  # at publish), so on a fresh checkout its master always read "underived" and every
  # whole-town bake re-encoded both tiers: 18 of the derivative step's 20.6 minutes,
  # for bytes publish then verified identical to the package. Restore them first when
  # the master just built IS the packaged one; a moved master is still derived below.
  python3 tools/stale_derivatives.py --reuse-packaged
  MOVED="$(python3 tools/stale_derivatives.py)"
  if [ -z "$MOVED" ]; then
    echo "   every master matches assets/manifest.web.json; nothing to derive (T-2314)"
  else
    echo "   $(printf '%s' "$MOVED" | tr ',' '\n' | wc -l | tr -d ' ') master(s) moved, unrecorded or underived; deriving those alone (T-2314)"
    tools/web_derivatives.sh --only "$MOVED"
  fi
fi

echo
echo "== sidecars"
python3 tools/compile_scene.py --all

# T-3503. Read off the models this bake just built, so it is the bake's to rewrite.
# derive_doors_1812.py keys each building on its model's sha256 and `--check` refuses
# a file whose models moved: the first whole-town bake to reach its gate (content
# build 42491116435, 2026-11-08) was red on that alone, because the 26.04 drift had
# re-hashed the 1812 masters and nothing in the bake re-read their doors.
echo
echo "== derived from the built models"
python3 tools/derive_doors_1812.py

echo
echo "== publish"
tools/publish.sh

# T-3503 — AND IN CI THE GATE RUNS SOMEWHERE ELSE TOO, for the smoke's reason below.
# Whole, `check.sh` outgrew one job: about thirty minutes on four cores by 2026-11-08
# (CI's own gate runs it as eight parts summing 38-42 minutes), after a twenty-minute
# derivative step, so the content build's bake job hit its fifty-minute cap inside
# this step on every whole-town bake of 11-07/08. `chicago-4d-bake.yml` sets
# SKIP_GATE=1 and runs the gate as eight parallel `--part k/8` jobs on the tree this
# bake pushed; no bake PR opens and no scene bundle publishes unless all eight pass.
# Run without it (the default) and the gate runs here, whole, as it always has.
if [ "${SKIP_GATE:-0}" = "1" ]; then
  echo
  echo "== gate (skipped: SKIP_GATE=1 — the content build runs it in parts, T-3503)"
else
  echo
  echo "== gate"
  tools/check.sh
fi

# The smoke runs against the PUBLISHED mirror, not the source tree, and it runs
# here because this is the step that just produced the compressed derivatives.
#
# The two trees do not load the same geometry: a sidecar's `gltf/<name>.glb`
# resolves to the uncompressed masters in the source tree and to the meshopt +
# quantised derivatives on the site. For as long as the smoke only ran against
# the source tree it never loaded a compressed asset, and a bug that collapsed
# every building to a two-metre box shipped past a fully green gate — twice.
# Whatever else is true, the bytes a visitor downloads have to be the bytes
# something tested.
#
# T-0165 — AND IN CI THAT PROPERTY IS NOW KEPT SOMEWHERE ELSE, so read the next
# paragraph before concluding the nightly stopped testing itself.
# `chicago-4d-bake.yml` sets SKIP_SMOKE=1 and runs the smoke as its own JOB,
# which takes the published mirror from this run as an ARTIFACT and drives it at
# both viewports in parallel. The reason is a ceiling, not a change of mind: run
# #261 was cancelled at 43m51s of a 45-minute job, inside the desktop half, and
# ~12 minutes of baking plus ~13 a viewport never fitted. Splitting it gives each
# part its own budget and still refuses to open a bake PR until both viewports
# are green. The bytes a visitor downloads are still the bytes something tested —
# tested one job later, by a job that cannot run unless this one succeeded.
#
# Run WITHOUT SKIP_SMOKE (the default, below) and the smoke happens here, inline,
# which is what you want locally: there is no artifact to hand anything to.
if [ "${SKIP_SMOKE:-0}" = "1" ]; then
  echo
  echo "== smoke (skipped: SKIP_SMOKE=1)"
else
  echo
  echo "== smoke (published mirror)"
  node tools/smoke_renderer.mjs --published
fi
