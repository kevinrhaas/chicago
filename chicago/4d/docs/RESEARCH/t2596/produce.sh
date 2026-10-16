#!/usr/bin/env bash
# T-2596 — ONE-SHOT PRODUCER, the machinery. The workflow file
# .github/workflows/t2596-glessner-ktx2.yml is only the trigger and the runner
# setup; everything else lives in this directory so the steward's text-only push
# channel could deliver it as ordinary files. Fires on a push to the ticket
# branch that touches docs/RESEARCH/t2596-run.txt. Every artifact commit is
# pushed the moment it exists, so a dead run loses nothing: re-add the sentinel
# (any content change) and it starts over from a clean tree — each step is
# idempotent. The final commit deletes this directory and the sentinel, so the
# pull request diff carries neither; deleting the workflow file itself is best
# effort (GITHUB_TOKEN holds no workflows permission).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)/chicago/4d"

pip install --quiet jsonschema pyproj openpyxl pypdf numpy scipy Pillow

# photo_match.mjs resolves playwright by createRequire from tools/, so the
# package must sit under chicago/4d/node_modules — not the global root.
npm install --no-save --no-package-lock playwright@1.56.1
node node_modules/playwright/cli.js install --with-deps chromium

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

push_branch() {
  local i
  for i in 1 2 3 4 5; do
    if git push origin "HEAD:$BRANCH"; then return 0; fi
    echo "push refused (attempt $i) — rebasing on the moved branch"
    git pull --rebase origin "$BRANCH"
  done
  echo "FATAL: five pushes refused" >&2
  return 1
}

# --- The steward's text edits, applied by exact anchor. ----------------------
# Every anchor must match exactly once, and the RESULT must be the byte pair the
# steward's fixture run passed on (the git blob hashes below). Anything else —
# a dev that moved under the branch, a re-typed character — stops the run here,
# before a single derivative is produced.
python3 docs/RESEARCH/t2596/apply_edits.py
bash -n tools/web_derivatives.sh
python3 -m py_compile tools/measure_web_derivatives.py
# The exact bytes the steward's fixture run passed on:
[ "$(git hash-object tools/web_derivatives.sh)" = "a25f11fa4f50bd1fa46ac400efec875c0a2f63ae" ] || { echo "FATAL: web_derivatives.sh is not the fixture-tested byte stream" >&2; exit 1; }
[ "$(git hash-object tools/measure_web_derivatives.py)" = "807d39a2c0fd16ded869e067e3806b3d8ecbddf7" ] || { echo "FATAL: measure_web_derivatives.py is not the fixture-tested byte stream" >&2; exit 1; }
python3 tools/test_glessner_v4_package_producer.py

# --- W1: commit the producer and gate edits. ---------------------------------
git add tools/web_derivatives.sh tools/measure_web_derivatives.py
if git diff --cached --quiet; then echo "edits already committed (refire)"; else
git commit -m "T-2596: encode the Glessner v4 set in KTX2 (producer + gate)" \
           -m "web_derivatives.sh: the v4 master joins the T-2595 KTX2 path (full cap 2048), and produce_light_version gains the same encode at cap 1024 between optimize and meshopt, with --texture-compress false for the main loop's own reason. The older Glessner versions (pre-v4, v2, v3) keep the path they had. measure_web_derivatives.py: assertion 10's RASTER_EXEMPT is deleted — the Glessner v4 set was the last named exception, and there is no exception now. Anchors and resulting bytes verified by the one-shot workflow against the steward's fixture run." \
           -m "Changelog: chicago/4d/changelog.d/T-2596.json"
fi
push_branch

# --- Bank the current state: materialize the package, stash the old bytes. ---
rm -f assets/gltf/glessner_house__as_built_1887.glb \
      assets/web/glessner_house__as_built_1887.glb \
      assets/web/glessner_house__as_built_1887.light.glb
python3 tools/recover_glessner_v4.py --materialize
mkdir -p "$RUNNER_TEMP/old"
cp assets/gltf/glessner_house__as_built_1887.glb "$RUNNER_TEMP/old/master.glb"
cp assets/web/glessner_house__as_built_1887.glb "$RUNNER_TEMP/old/full.glb"
cp assets/web/glessner_house__as_built_1887.light.glb "$RUNNER_TEMP/old/light.glb"
sha256sum "$RUNNER_TEMP/old/"*.glb
python3 tools/recover_glessner_v4.py --check
python3 docs/RESEARCH/t2596/package_old.py

# --- Render the CURRENT derivatives from every reference camera. -------------
# Old first: the renders the current files make. The side-by-sides go to the
# runner's temp dir — the committed photo-match side-by-sides are T-2228's
# review surface (PR #851), not this ticket's.
mkdir -p "$RUNNER_TEMP/renders/old" "$RUNNER_TEMP/sbs/old"
for v in $VIEWS; do
  echo "== current full: $v"
  node tools/photo_match.mjs "data/reference_views/glessner_house/$v.json" \
    --glb assets/web/glessner_house__as_built_1887.glb --out "$RUNNER_TEMP/sbs/old" | tee "$RUNNER_TEMP/pm.log"
  cp "$(grep -oE '/[^ ]+-render\.png' "$RUNNER_TEMP/pm.log" | head -1)" "$RUNNER_TEMP/renders/old/$v.png"
done
echo "== current light: $LIGHT_VIEW"
node tools/photo_match.mjs "data/reference_views/glessner_house/$LIGHT_VIEW.json" \
  --glb assets/web/glessner_house__as_built_1887.light.glb --out "$RUNNER_TEMP/sbs/old" | tee "$RUNNER_TEMP/pm.log"
cp "$(grep -oE '/[^ ]+-render\.png' "$RUNNER_TEMP/pm.log" | head -1)" "$RUNNER_TEMP/renders/old/$LIGHT_VIEW.light.png"

# --- THE PRODUCER. -------------------------------------------------------------
# optimize -> KTX2 (cap 2048) -> meshopt 16-bit for the full file;
# build-light -> optimize -> KTX2 (cap 1024) -> meshopt 16-bit for the light one;
# then record-web and the recovery repack, all inside the canonical script.
./tools/web_derivatives.sh --only glessner_house__as_built_1887.glb
ls -l assets/web/glessner_house__as_built_1887*.glb
ls -l docs/RESEARCH/glessner-v4-recovery/

# --- Render the NEW derivatives from every reference camera. -----------------
mkdir -p "$RUNNER_TEMP/renders/new" "$RUNNER_TEMP/sbs/new"
for v in $VIEWS; do
  echo "== new full: $v"
  node tools/photo_match.mjs "data/reference_views/glessner_house/$v.json" \
    --glb assets/web/glessner_house__as_built_1887.glb --out "$RUNNER_TEMP/sbs/new" | tee "$RUNNER_TEMP/pm.log"
  cp "$(grep -oE '/[^ ]+-render\.png' "$RUNNER_TEMP/pm.log" | head -1)" "$RUNNER_TEMP/renders/new/$v.png"
done
echo "== new light: $LIGHT_VIEW"
node tools/photo_match.mjs "data/reference_views/glessner_house/$LIGHT_VIEW.json" \
  --glb assets/web/glessner_house__as_built_1887.light.glb --out "$RUNNER_TEMP/sbs/new" | tee "$RUNNER_TEMP/pm.log"
cp "$(grep -oE '/[^ ]+-render\.png' "$RUNNER_TEMP/pm.log" | head -1)" "$RUNNER_TEMP/renders/new/$LIGHT_VIEW.light.png"

# --- Restore the human match records. ------------------------------------------
# The match records are HUMAN REVIEW STATE (verdicts, differences, T-2228's
# open review in PR #851). photo_match rewrites them on every run; the renders
# here are evidence, not a re-review, so the committed records are restored
# byte-for-byte and NOTHING under data/reference_views or docs/RESEARCH/
# photo-match is committed.
git checkout -- data/reference_views/glessner_house
if [ -n "$(git status --porcelain -- data/reference_views docs/RESEARCH/photo-match)" ]; then
  echo "FATAL: a match record or committed side-by-side moved" >&2
  git status --porcelain -- data/reference_views docs/RESEARCH/photo-match >&2
  exit 1
fi
echo "match records restored; human review state untouched"

# --- Evidence + verification. --------------------------------------------------
python3 docs/RESEARCH/t2596/evidence.py
python3 tools/recover_glessner_v4.py --check
python3 docs/RESEARCH/t2596/manifest_check.py

# --- W2: commit the derivatives package and evidence. --------------------------
git add docs/RESEARCH/glessner-v4-recovery \
        docs/RESEARCH/ktx2-v4 \
        assets/manifest.json \
        assets/manifest.web.json
if git diff --cached --quiet; then echo "artifacts already committed (refire)"; else
git commit -m "T-2596: Glessner v4 derivatives in KTX2, package repacked, evidence" \
           -m "Full and light web derivatives re-encoded by the canonical producer (KTX2: ETC1S colour, UASTC+RDO data, light tier capped at 1024), the three-file recovery package repacked with its new hashes, assets/manifest.json re-recorded by record-web, and the old-vs-new render evidence (per-camera PSNR) under docs/RESEARCH/ktx2-v4/." \
           -m "Changelog: chicago/4d/changelog.d/T-2596.json"
fi
push_branch

# --- The audit must name the NEW bytes. ----------------------------------------
# The baseline page verifies the loaded model against the audit's assets block.
# Regenerated by its own tool; the diff is printed in full so the review sees
# exactly what moved (expected: the assets block and the candidate hash; anything
# more is pre-existing master drift between the audit-era master and the recovery
# package's, and the PR says so, not hides it).
python3 tools/glessner_proportion_audit.py
python3 tools/glessner_proportion_audit.py --check
git --no-pager diff --stat -- data/comparisons/glessner/audit-report.json
git --no-pager diff -- data/comparisons/glessner/audit-report.json | head -80 || true

# --- W3: audit + budget note + retire the sentinel and this machinery. ---------
# The commit's content is fully regenerable (the audit from the GLBs on disk —
# untracked, they survive a reset — the budget sentence from the evidence file,
# the deletions by git rm), so the push loop can drop and redo it. Deleting the
# running script is safe on the runner: bash keeps reading the unlinked file
# through its open descriptor.
commit_w3() {
  python3 tools/glessner_proportion_audit.py
  python3 docs/RESEARCH/t2596/budget_edit.py
  git add data/comparisons/glessner/audit-report.json docs/SITE-BUDGET.md
  git rm -q --ignore-unmatch docs/RESEARCH/t2596-run.txt
  git rm -q -r --ignore-unmatch docs/RESEARCH/t2596
  if git diff --cached --quiet; then echo "final commit already landed (refire)"; return 0; fi
  git commit -m "T-2596: audit reads the new files; budget note measured; one-shot removed" \
             -m "data/comparisons/glessner/audit-report.json regenerated by its own tool so the baseline page's current-audit verification names the shipped bytes; docs/SITE-BUDGET.md §9's expected-not-measured sentence replaced with the measured sizes and PSNR. The sentinel and the one-shot machinery leave the branch so the producer cannot refire on a later push; the workflow file is retired by the next step where the token holds the workflows permission." \
             -m "Changelog: chicago/4d/changelog.d/T-2596.json"
}
commit_w3
for i in 1 2 3 4 5; do
  if git push origin "HEAD:$BRANCH"; then break; fi
  echo "push refused (attempt $i) — taking the moved branch and redoing the regenerable commit"
  git fetch origin "$BRANCH"
  git reset --hard "origin/$BRANCH"
  commit_w3
  [ "$i" = 5 ] && exit 1
done

# --- W4: retire the workflow file (best effort). -------------------------------
# GITHUB_TOKEN may not create, update or delete files under .github/workflows/
# (the platform's workflows-permission rule), so this is its own commit, AFTER
# the sentinel's, and green either way. A refusal leaves the file on the branch,
# owner-visible in the pull request; the owner deletes it in the web UI before
# merging, or merges with it — either way it can never fire again, because its
# push trigger names only this branch and the sentinel is gone.
cd "$(git rev-parse --show-toplevel)"
set +e
if [ ! -f .github/workflows/t2596-glessner-ktx2.yml ]; then
  echo 'workflow file already absent — nothing to do'
else
  git rm -q .github/workflows/t2596-glessner-ktx2.yml
  if git commit -m "T-2596: retire the one-shot producer workflow" \
       -m "Added to run the binary-producing half of the ticket on a runner. Its work is committed, and it cannot refire (the sentinel is gone), so it leaves the branch before the pull request."; then
    if git push origin "HEAD:$BRANCH"; then
      echo 'one-shot workflow removed from the branch'
    else
      echo '::warning::push refused — GITHUB_TOKEN holds no workflows permission, so the workflow file stays on the branch.'
      echo '::warning::Owner: delete .github/workflows/t2596-glessner-ktx2.yml on this branch in the web UI before merging, or merge with it — it cannot fire again (the push trigger names only this branch, and the sentinel is gone).'
      git fetch origin "$BRANCH"
      git reset --hard "origin/$BRANCH"
    fi
  else
    echo 'nothing to commit'
  fi
fi
set -e

# --- Run summary. ----------------------------------------------------------------
cd chicago/4d
EV=docs/RESEARCH/ktx2-v4/glessner-v4-ktx2.json
if [ -f "$EV" ]; then
  {
    echo "### T-2596 evidence"
    echo '```json'
    python3 -c "import json;d=json.load(open('$EV'));print(json.dumps({'files':d['files'],'textures':d['textures'],'package':d['package'],'renders':d['renders']},indent=1))"
    echo '```'
  } >> "$GITHUB_STEP_SUMMARY"
fi
echo "T-2596 one-shot producer: done"
