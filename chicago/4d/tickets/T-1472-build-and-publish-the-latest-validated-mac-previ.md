---
id: T-1472
title: Build and publish the latest validated Mac preview on demand
state: blocked-tech
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-1356
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: Qualified Apple Silicon Mac with licensed Unreal 5.8.2, Xcode, GPU test access and scoped GitHub release access; no eligible remote web runner exists
needs_bake: false
closed_at: null
claimed_run: null
---

Owner request, 2026-09-20: after a round of updates, kick off a build using the latest best source and make it downloadable. Parent: T-1356. [Current manual process](../docs/unreal/BUILD-AND-RELEASE.md).

**Executor: QUALIFIED MAC / UNREAL ONLY.** Remote web workers may prepare code/docs but cannot close this ticket. Keep blocked-tech until a coordinator verifies engine 5.8.2, Xcode, arm64 host, disk/cache capacity, render test access and scoped GitHub release credentials, then immediately claims it on that runner. No owner attendance should be needed for routine runs after provisioning. New hosts, paid services or credentials require their actual prerequisites; do not assume a generic runner can render.

## Acceptance — one on-demand update through downloadable prerelease

1. Add an on-demand entry point around the existing fresh build script (local command first; manual GitHub dispatch only on a qualified runner). Select the newest successful dev push gate, pin its full SHA, prove it belongs to dev, and show when newer dev commits were skipped. Permit an explicit validated SHA. Refuse missing/pending/failed validation and stale required assets. Record source, engine, SDK, scene date, coverage, hashes and build id; never combine assets from different revisions. Source selection is not proof of web feature parity.
2. Use fresh isolated output directories, preserve the previous working app, and fail before publication on import errors, failed rotation/placement checks, cook/package failure, or failed play test. Retain logs and make a retry of the same SHA unambiguous. Builds must not reset the owner's checkout or take keyboard/mouse focus.
3. Run the packaged background movement check plus the current named placement/road/feature checks. Provide a visual-review checkpoint for newly changed layers and an explicit receipt for anything not tested. Engine/cook success alone cannot mark parity complete.
4. Produce a ZIP, checksum, build receipt, coverage/release notes, platform and signing status. Upload as a new prerelease; verify a fresh download against its checksum and extraction/signature checks before advancing a latest-tested-Mac pointer. Failed builds leave the prior release available. Do not overwrite a tag with different bits or move main/production.
5. Demonstrate the command/dispatch against one newer dev snapshot and a failing-input case. Document exact runner setup, invocation, output/release discovery, retention, rollback and who can trigger it. Existing GitHub Releases is the destination; no new paid host is implied. Keep T-1357 source bundles and T-1361 streaming deployment separate. Public Mac notarization remains explicit work, not a claim made by uploading locally signed builds.

**Budget exception:** Owner explicitly requested these four independently verifiable follow-ups in the existing programme; reuse T-1360 for roads rather than duplicate it.
