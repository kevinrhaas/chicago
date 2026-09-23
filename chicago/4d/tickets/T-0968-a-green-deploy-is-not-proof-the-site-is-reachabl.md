---
id: T-0968
title: A green deploy is not proof the site is reachable: /chicago/4d/dev/ served a 404 for hours while every deploy reported success, and nothing checks a URL after publishing
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-16
pr: 1372
claimed_by: run 9/16/2026, 11:38:21 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T01:49:31.671Z
claimed_run: null
---

**OWNER-REPORTED, 2026-09-07.** `https://custom.polecat.live/chicago/4d/dev/` served a
**404** while every deploy in the run list reported success. Production was fine throughout,
so nothing in the repository, the workflow log or the Actions UI said anything was wrong.
It was found by a person opening the page.

## How it went silent

The preview is assembled from `site/chicago/4d/` in a worktree of `dev`. T-0937/T-0938 made
that tree generated and untracked — correctly; it was the file every branch conflicted on —
and `.github/chicago-4d-dev-preview.mjs` had this:

    if (!existsSync(SRC)) {
      console.log(`dev-preview: ${SRC} does not exist on the dev ref — skipping`);
      process.exit(0);
    }

so the assembler reported success on an empty source and the deploy went green. Fixed by
#1030/#1031, which publish the worktree before mirroring it.

**But the class of fault is not fixed, and that is what this ticket is for.** Nothing
anywhere asserts that a deployed URL returns a page. Every check in this pipeline stops at
"the workflow exited 0":

- `tools/check.sh` gates the SOURCE tree, before the artifact exists;
- the smoke suite drives `--published`, i.e. the LOCAL `site/` directory, not the origin;
- `deploy-pages` reports success when GitHub accepts the artifact, which says nothing about
  what a request returns.

So any fault between "artifact uploaded" and "browser gets HTML" is invisible by
construction: an empty directory, a path that moved, a `robots`/Pages routing change, a
tenant that stopped being copied. **The 404 lasted as long as it did because the only
detector was a human loading the page.**

## Why the obvious fix is wrong, and this needs care

The tempting version is to fail the deploy when a URL check fails. **Do not**, and the repo
already says why — `chicago/4d/CLAUDE.md`: *"Never hard-gate deploy on CI — a hard
`needs: test` gate once froze the live site ~21 hours."* T-0938 made the same call for the
4D publish, deliberately: *"A publish that fails must cost the 4D app, not every other
tenant in this monorepo."* #1030 got this wrong in the other direction — it made the publish
fatal — and #1031 reverted it. A URL smoke that can freeze the monorepo's deploy is a worse
bug than the one it detects.

So the requirement is **loud, not blocking**: an annotation a person sees, on a step that
does not gate the deploy.

## Acceptance

1. After the artifact deploys, the live origin is requested and the status recorded for at
   minimum: `/`, `/chicago/4d/`, `/chicago/4d/walk/`, `/chicago/4d/dev/`,
   `/chicago/4d/dev/walk/`. The list is data, not code, so a new tenant is one line.
2. **A non-200 raises a `::error::` annotation naming the URL and the status, and does NOT
   fail the deploy job.** State that reasoning in the step, with the 21-hour freeze named,
   so the next person does not "improve" it into a gate.
3. It tolerates propagation: Pages serves the new artifact some seconds after the API
   reports success, so the check retries over a bounded window before it reports anything.
   A flapping check that cries wolf will be ignored and is worse than none.
4. It checks a BODY signal, not only a status — a Pages 404 page is served with a 404, but a
   stale or empty preview can return 200 with nothing in it. Assert something the page must
   contain (the gate's build stamp is the obvious candidate, and the preview's own
   `PREVIEW`/noindex marking distinguishes the tier).
5. A self-test or a documented dry run proves the check FIRES — point it at a URL known to
   404 and show the annotation. An unproven detector is not a detector.

## Worth deciding while doing it

Whether the same check belongs on production promotion. `promote-to-prod.yml` moves
stage→main and tags a release; a URL check there would catch a promotion that shipped a hole
before anyone opened the site. Same non-blocking rule. Out of scope here unless it is free.

**Found by:** the owner, opening the page. Diagnosis and repair in #1030 and #1031; the
repair closed this instance, and this ticket is the reason it was invisible.