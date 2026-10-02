# T-1999 recovery checkpoint

This is an INTERIM, UNVALIDATED checkpoint requested by the owner on 2026-10-02.
Do not merge this branch as a completed repair. No completed bake or visual approval is claimed.

## Locations

- Ticket: https://github.com/kevinrhaas/chicago-tickets/blob/main/T-1750-1999/T-1999-rebuild-glessner-west-elevation-and-correct-nort.md
- Active integration branch: `steward/t-1999-glessner-elevation-rebuild`
- Recovery branch: `checkpoint/t-1999-glessner-20261002`
- Snapshot base: `10bd9c07e7bf1e02dd0344315aaa435a980167d0`
- North working tree: `north-work`, branch `steward/t-1999-north`.
- Roof working tree: `roof-work`, branch `steward/t-1999-roof`; no source edits existed there at this checkpoint.

## Owner's requested outcome

Correct north windows protruding above the eave, rebuild the full west elevation to the supplied straight-on elevation and archival northwest image, and assess the north entrance, stone appendage, carriage and loft doors. Match roof joins, stone courses, window positions, gutter/downpipe detail, squared dormer hood and finial. The tower should move toward the rear (left in the true west view) to align with the high gable peak. Preserve the lower rear continuous gable roof and solid south face. No center dormer post or added rear chimney. See the ticket for full acceptance.

## Saved work

The canonical source paths in this recovery branch include the north working tree's uncommitted edits at capture time: corrected upper window heads, porch/coping parameters, stable north entrance detailing, and the new `masonry_house_v4_north.py` helper. These files are a recovery snapshot, not a claim that implementation or validation is complete. The main and roof worktrees had no uncommitted source changes at capture.

`references/` contains review copies of all five owner reference images, with original filenames, pixel dimensions and SHA-256 hashes in `index.json`. Owner-generated elevation studies bound reconstruction; use HABS and archival evidence for historical claims. Do not trace source pixels into materials.

`qa/` preserves the early GLB inspection, meshopt decoding and Blender render scripts. They were copied from scratch and may contain absolute paths that a future session must update. Baseline full/light assets are already recoverable from the base commit; regenerated assets have NOT been produced by this snapshot.

## Resume safely

1. Read `chicago/4d/AGENTS.md`, `docs/PIPELINE.md`, and the current ticket. Check the active branch and open PRs first: another worker may have advanced after this checkpoint. Do not overwrite newer changes.
2. Compare this branch against its recorded base and the active integration branch. Recover only missing edits, retaining their working status.
3. Finish and review the north implementation. Complete the west/roof/tower reconstruction from the owner's images, with evidence and reconstruction notes.
4. Regenerate canonical full/light Glessner assets, sidecars and web derivatives. Check exact published derivatives at desktop and mobile sizes from west, north, northwest and south/courtyard.
5. Run required source, preflight and applicable browser gates before a PR into `dev` can merge. Keep checkpoints on GitHub after each substantive stage, and update this note with exact commands, results, remaining work and next action.

## Validation at this checkpoint

Pending. No full source gate, bake, or published browser gate was run for this recovery snapshot. The owner explicitly requested intermediate branch commits to prevent session loss; that is why this work is preserved before completion.

## Second snapshot: all three working trees

`checkpoints/manifest.json` indexes complete binary-capable patches for the integration, north and roof worktrees. These were captured after the first north-only checkpoint and include newer west fabric/drainage, source/provenance notes, and west-roof implementation work. Each patch includes tracked edits and untracked files and has passed `git apply --cached --check` against its recorded base. That proves recoverability only; it is not a build/test result.

The integration patch (`chicago.patch`) and roof patch (`roof-work.patch`) are separate unfinished workstreams. Do not stack them blindly: both change the structure and parameter files. Recover in separate worktrees, compare the diffs and integrate deliberately. The `north-work.patch` snapshot preserves the north task independently.

Example, from a checkout of this checkpoint branch:

```sh
git worktree add -b recovery/t-1999-integration ../t1999-integration 10bd9c07e7bf1e02dd0344315aaa435a980167d0
git -C ../t1999-integration apply --binary /absolute/path/to/this-checkpoint/chicago/4d/docs/RESEARCH/glessner-elevation-rebuild/checkpoints/chicago.patch
```

Use the same pattern for each patch with a separate branch/worktree. Read `work.md` recovered by the integration patch for the current architecture plan. A live worker may have advanced since capture: inspect the active branch and ticket before using any snapshot.
