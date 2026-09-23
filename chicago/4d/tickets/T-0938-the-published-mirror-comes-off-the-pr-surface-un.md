---
id: T-0938
title: The published mirror comes off the PR surface: untrack site/chicago/4d/ and have deploy.yml publish it
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: T-0857
opened: 2026-09-06
closed: 2026-09-06
pr: 1023
claimed_by: run 9/6/2026, 11:25:53 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T04:45:58.975Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34082709036
---

The published mirror comes off the PR surface: untrack site/chicago/4d/ and have deploy.yml publish it.

Piece 2 of 2 of **T-0857 — GitHub's merge never runs this repo's merge drivers, so every PR reads as conflicting and auto-merge can never fire**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**THE OPEN QUESTION IN THE PARENT IS ANSWERED — traced 2026-09-06, and it does not block.**
The parent ends "the one thing to check first, because it decides the shape: whether
`/v/release-vNNN/` snapshots and `chicago-4d-promote-to-prod.yml` read the COMMITTED mirror."

  * **There are no `/v/` snapshots.** `site/chicago/4d/` holds `build.json`, `data`,
    `index.html`, `js`, `tickets.json`, `walk` and nothing else; no workflow, tool or doc in
    this repo writes a `/v/` path. The releases that exist are git TAGS (`release-vNNN`),
    written by the promotion job, and a tag needs no materialised tree.
  * **`chicago-4d-promote-to-prod.yml` never reads the mirror.** It merges refs — back-merge
    `main` into `dev`, `dev` into `main` `--no-ff`, tag, then `gh workflow run deploy.yml`.
    Its only file reads are `check-changelog.mjs` and the changelog's `v:`.

So the shape is the one the parent designed. What DOES have to be carried:

  * `deploy.yml` uploads `path: site` from the runner, so it must run `tools/publish.sh` on the
    main checkout before the upload — and the dev-preview step copies `_dev-src/site/chicago/4d`
    out of a worktree, so that worktree needs a publish too.
  * `deploy.yml`'s JS syntax step enumerates with `git ls-files 'site/**/*.js'`; an untracked
    mirror drops out of it. It has to walk the tree instead, after the publish.
  * `tools/validate.py run_site_check` already rglobs the working tree, so the byte budget is
    unaffected by tracking — that number does not change and must not be claimed as a win.
  * ~40 tools resolve `../../../site/chicago/4d` for their `--published` mode, and
    `tools/smoke_budget.mjs --for-diff` and `tools/bake_content_changed.py` read git state over
    those paths. Each needs a pass: a mirror that is absent until published is a different
    precondition from one that is always there.
  * `tools/dev-smoke-state.json` STAYS TRACKED (parent, point 5).

**Acceptance:** `site/chicago/4d/**` untracked and ignored; `deploy.yml` publishes before it
uploads, on both the production tree and the dev worktree; `check_published.mjs` reads as
"publish.sh PRODUCES a mirror that matches" and is run that way in the gate; the remaining
`merge=generated` lines gone; a deploy proved to still serve `walk/`, `js/changelog.js` and
`tickets.json`.
