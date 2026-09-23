# Rebuild Chicago 1835 after an update

The working path today is a **manual local Mac build** using the committed
`renderers/unreal/build_mac.py`. T-1472 owns a single on-demand command/qualified-runner
dispatch and automatic tested-release discovery; neither exists yet. A web worker
cannot package this project just by checking out the repository.

## What “latest best” means

Use the newest successful **dev push** run of `chicago-4d-check.yml`, pin its full
commit, and build all source/assets from that revision. A newer dev commit whose
gate is pending or failing is not selected. A green repository gate is necessary,
but it does not replace Unreal build, placement, rendering or packaged-play tests.
Do not describe missing web layers as present just because their data is newer.

A source update requiring newly baked assets must pass the existing staleness/bake
contract first. Do not mix fresh JSON with GLBs copied from another build. The
current native adapter imports only the coverage stated in its README; consult
[PARITY.md](PARITY.md) for unfinished layers.

## 1. Prepare and pin the source

Use an Apple Silicon Mac with licensed Unreal **5.8.2**, full Xcode selected as its
developer directory (qualified with Xcode 27.0), Python 3, Git, GitHub CLI with repo
read access, and adequate free space. Use local storage outside iCloud/synced
Desktop or Documents. Routine background builds do not need the owner to operate
the keyboard; provisioning, access prompts and new-feature visual review may.

Run these commands from an existing clone of `kevinrhaas/custom`. They create a
separate checkout and do not reset or overwrite the current working tree:

```sh
git fetch origin dev
build_sha=$(gh run list --repo kevinrhaas/custom \
  --workflow chicago-4d-check.yml --branch dev --event push --status success \
  --limit 1 --json headSha --jq '.[0].headSha')
test -n "$build_sha" && test "$build_sha" != null || exit 1
git merge-base --is-ancestor "$build_sha" origin/dev || exit 1
printf 'Building validated dev commit: %s\nCurrent dev tip: ' "$build_sha"
git rev-parse origin/dev
build_root="$HOME/Chicago4D/releases/$(date -u +%Y%m%dT%H%M%SZ)-$build_sha"
mkdir -p "$build_root"
git worktree add --detach "$build_root/source" "$build_sha"
```

If no successful run is available, stop and investigate; do not silently build an
unvalidated tip. For an explicitly selected revision, obtain its successful gate
receipt and use its full SHA. Save the gate URL with the release notes. Do not
promote `main` as part of building a dev preview.

## 2. Build a fresh app

Continue in the same shell, retaining the variables above:

```sh
python3 "$build_root/source/chicago/4d/renderers/unreal/build_mac.py" \
  --engine '/Users/Shared/Epic Games/UE_5.8' \
  --project-dir "$build_root/project" \
  --archive-dir "$build_root/package"
```

Both output directories must be new. The script builds the editor module, imports
the pinned GLBs/sidecars, verifies the scene, and cooks/packages the app. It writes
step logs and `verification.json` in `project/Scripts`, plus `build-receipt.json`
in `package`. On failure retain those logs and the previous working app/release;
use fresh directories for a retry. This avoids the prototype's stale cached imports
and does not yet implement T-1358 incremental asset updates/retirement.

## 3. Test before replacing or publishing

```sh
app="$build_root/package/Mac/Chicago4D.app"
"$app/Contents/MacOS/Chicago4D" -ChicagoWalkTest -RenderOffScreen \
  -unattended -nosound > "$build_root/walk.log" 2>&1
python3 -c 'import pathlib,sys; s=pathlib.Path(sys.argv[1]).read_text(); assert "CHICAGO_WALK_TEST_RESULT PASS" in s' "$build_root/walk.log"
codesign --verify --deep --strict "$app"
```

Inspect the per-second movement readings as well as PASS. This is a short
spawn-route test, not a complete town test. Compare newly changed locations against
the web app at the **same source revision, date and quality preset**: building
bases/doors, fence orientation, street/bridge grades, flora and relevant UI flows.
Record screenshots and normal-walking routes. Do not use ghost/fly/teleport movement
as collision evidence. Do not interrupt an owner's running app or grab their input
for background tests. Replace an installed app only after it is closed, preserving
a backup until the new build has passed.

## 4. Package and publish a downloadable preview

```sh
zip_path="$build_root/Chicago1835-Mac-$build_sha.zip"
ditto -c -k --sequesterRsrc --keepParent "$app" "$zip_path"
ditto -x -k "$zip_path" "$build_root/extraction-check"
codesign --verify --deep --strict "$build_root/extraction-check/Chicago4D.app"
(cd "$build_root" && shasum -a 256 "$(basename "$zip_path")" > SHA256SUMS.txt)
```

Write `release-notes.md` inside `build_root` with the full source SHA/gate URL,
engine/SDK/architecture, changed features, exact coverage and omissions, test
results, controls, signing status and known issues. Retain the scene verification,
walk log and receipt. Sanitize local paths or other sensitive values before attaching
logs. The current app is locally signed, **not Developer ID signed/notarized**;
a download may be blocked by macOS. Do not tell users to disable Gatekeeper.
Broad public distribution still needs signing/notarization and a second-Mac test.

When the release notes and checks are complete, use GitHub Releases (already in use):

```sh
release_tag="chicago1835-mac-$build_sha"
gh release create "$release_tag" "$zip_path" "$build_root/SHA256SUMS.txt" \
  "$build_root/package/build-receipt.json" \
  --repo kevinrhaas/custom --target "$build_sha" --draft --prerelease \
  --title "Chicago 1835 Mac preview — $build_sha" \
  --notes-file "$build_root/release-notes.md"
```

Check the draft's assets and notes. Download its ZIP/checksum into a new directory
with `gh release download`, verify `shasum -a 256 -c SHA256SUMS.txt`, and repeat the
extraction/signature check. Then publish the reviewed draft:

```sh
gh release edit "$release_tag" --repo kevinrhaas/custom --draft=false
```

Use a new tag for different bits; never overwrite an existing published release.
Keep at least the previous tested release available. Rollback means downloading
that known-good ZIP, not moving an immutable tag. GitHub prereleases are separate
from the website's dev/main promotion and from server streaming deployment.
A stable latest-tested-Mac pointer and automated retention are pending T-1472.

## Execution and future work

T-1472 makes this sequence a repeatable on-demand operation. T-1357 provides regular
portable source bundles; T-1358 consumes them with safe incremental updates. Those
are separate contracts. Adding a schedule or build runner is not already done by
writing this document. Workflow changes go through an owner-visible PR, and an
engine-equipped runner must prove its capabilities before a held ticket is opened.
See [the queue programme](../../tickets/T-1356-epic-chicago-4d-unreal-asset-delivery-renderer-p.md)
by ticket id if its generated filename changes; [PARITY.md](PARITY.md) maps feature work.
