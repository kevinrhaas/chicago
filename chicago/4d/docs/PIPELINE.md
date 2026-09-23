# PIPELINE — how 4D Chicago ships

**Two tiers: `dev` → `main`. Production moves only when the owner dispatches it.**

Adapted from the fleet pilot, `kevinrhaas/jobtracker.polecat.live` → `docs/PIPELINE.md`,
which is the canonical runbook and worth reading for the reasoning behind the shape. This
document records what is different here and why, so nobody has to diff two repos to find out.

Activated 2026-08-14 on the owner's instruction: *overnight work must not ship straight to
production.*

---

## The two tiers

| tier | branch | URL | who moves it |
|---|---|---|---|
| production | `main` | `/custom/chicago/4d/walk/?year=1835` | the owner, by dispatch |
| integration | `dev` | `/custom/chicago/4d/dev/walk/?year=1835` | any green PR into `dev` |

There is **no stage tier and no scheduled promotion**. The pilot has three tiers because it
promotes on a nightly cron; this app promotes on a human asking, so the middle tier would be
a queue with nobody in it.

**Merging into `dev` is stage, not ship.** It publishes the preview and nothing else.

---

## What each piece does

| file | job |
|---|---|
| `.github/workflows/chicago-4d-pipeline-setup.yml` | one-button: creates `dev` from `main` if absent, then dispatches a deploy. Idempotent. |
| `.github/workflows/deploy.yml` | the single deploy authority. Assembles ONE Pages artifact: `main` at the root, plus the `dev` branch's `site/chicago/4d/` folded in at `site/chicago/4d/dev/`. Since T-0938 it PUBLISHES both trees first — `site/chicago/4d/` is generated, not committed — and it triggers on `chicago/4d/**` rather than only `site/**`, because a 4D change no longer touches `site/`. |
| `.github/chicago-4d-dev-preview.mjs` | assembles that preview — copy, `noindex`, banner, dev build stamp, `build.json`, robots disallow. |
| `.github/workflows/chicago-4d-check.yml` | **the dev gate.** Runs on PRs into `dev` and pushes to `dev` (no branch filter, deliberately). |
| `.github/workflows/chicago-4d-promote-to-prod.yml` | **dispatch-only.** Back-merges `main`→`dev`, merges `dev`→`main` `--no-ff`, tags `release-vNNN`, then dispatches the deploy. |
| `.github/workflows/chicago-4d-bake.yml` | the content bake. **Builds the ref it was started on, and PRs into that same ref** — `tools/bake_ref.py` decides, and `check.sh` asserts it. The nightly and any run whose ref is `main` build `dev` and PR into `dev`, because the schedule has no tree of its own to speak for and nothing may PR into production. A bake dispatched against a branch builds THAT branch: until T-0454 it silently rebuilt `dev` instead, which is how the staleness gate and the bake came to disagree about one asset while both were right. |
| `.github/pipeline.json` | the manifest. Declares the shape — tiers, publish paths, workflow names — to anything that reads it. A **data file**: editing it is a sanctioned direct commit to `main`, same as the pilot's. |

`pipeline.json` earns its keep on the fleet console. Manager's Pipeline view
(`manager.polecat.live/app/#pipeline`) probes every fleet repo for that file and
draws a release card for each one it finds, so **adopting the pipeline is what
lights up the tile** — there is no per-repo entry to add on the Manager side.
The card then reads its shape from the manifest instead of assuming the pilot's:
two tiers rather than three, a publish path under `/chicago/4d/` rather than a
domain root, `chicago-4d-`-prefixed workflow names (this monorepo's
`.github/workflows/` is shared with every other tenant, so the bare
`promote-to-prod.yml` name was never available), and a `null` for each verb this
repo does not have, which draws no button rather than one that 404s.
It is `main` that gets probed, so a manifest that only ever exists on `dev` shows
nothing.

---

## dev's standing smoke result (T-0216)

**The dev gate is `check.sh` and nothing else.** `chicago-4d-check.yml` runs the fast half
of the two-speed build; `chicago-4d-smoke.yml` is dispatch-plus-one-path on purpose (a
~25-minute-per-viewport Playwright crawl on every push would be a queue, not a gate). So
`dev` has had **no standing smoke result of its own**, and the question every branch asks —
*"is this red mine, or did I inherit it?"* — was answered by cutting a clean `origin/dev`
worktree and paying ten minutes for the stage again.

On **2026-08-27 four separate runs paid that price on two reds**, and one of the two belonged
to neither branch nor `dev`: it was the machine. T-0215 has the frame timings — the same tree
drew twenty times slower on a loaded box than a quiet one, and `page.click` starved into a
90-second timeout that reads exactly like a broken control.

**`tools/dev-smoke-state.json` is the record, and `tools/dev-smoke-state.mjs` reads it.**

```
node tools/dev-smoke-state.mjs ask --viewport desktop --stage 8   # answer, running nothing
node tools/dev-smoke-state.mjs record run.log                     # file a smoke you ran anyway
node tools/dev-smoke-state.mjs ci 32689397335                     # fold a chicago-4d-smoke.yml run in
node tools/dev-smoke-state.mjs hash                               # the smoke-relevant tree hash
```

Three things about it are the whole design:

- **It is fed by the two routes a run already has**, because `.github/workflows/` is outside a
  steward run's scope (§ How work ships in `AGENTS.md`) and this could not be a new scheduled
  job. A local smoke log and a `chicago-4d-smoke.yml` run's log go through **one parser**. If
  the owner later schedules that workflow on `dev`, `ci <id>` is what folds its result in and
  nothing in the tool changes.
- **Every reading carries its conditions** — host, CPU count, load average, wall clock, and any
  animation-frame cost the smoke reported. A CI pass on a quiet runner **dates** a
  steward-runner red; it does not overrule it. A verdict without its conditions is what sent
  three runs chasing a machine.
- **Every reading carries a tree hash**, digesting exactly what the smoke exercises. Match it
  and the reading is a reading *of your tree* — the red is inherited, provably, with nothing
  re-run. The three files every branch changes by construction are handled rather than
  ignored: `tickets.json` is dropped (nothing reads it), the changelog is hashed **apart**
  (only part 8 reads it), and `publish.sh`'s build stamp is **normalised out** of the gate page.

**It is a record, never a bar.** Nothing in it fails a gate, refuses a merge or excuses a red.

---

## Five things that are easy to get wrong

**1. A Pages deploy job on a dev ref is REJECTED, silently.** The `github-pages` environment
carries a deployment-branch policy, so a `deploy` job running on `dev` fails in about a second
with no steps and no logs. It reads as "nothing ran" while the preview stays frozen at the last
main deploy. The fix, inherited verbatim from the pilot: a push to `dev` does not deploy
itself — the `refresh-previews` job re-dispatches `deploy.yml` **on main**, which rebuilds the
whole artifact from both refs.

**2. The preview needs no path rewriting, and that is a measured fact.** The pilot rewrites
every root-absolute `/x` URL because its app is served from the domain root. This app has
**zero** root-absolute URLs: `walk/index.html` uses `./css/…` and `./js/…`, and `scene-loader.js`
resolves data by page path (`walk/` → `../data/`). Mirroring the whole published
`site/chicago/4d/` tree under `dev/` therefore preserves every path by construction — which is
exactly why the whole tree is mirrored and not just `walk/`. If a root-absolute URL is ever
introduced, this stops being true and the preview script needs the pilot's rewriting.

**3. There is no service worker to neutralise.** The pilot replaces `sw.js` with a
self-unregistering stub so a preview never installs offline caching. This app has no service
worker, so there is nothing to stub and no cache to bump.

**4. Scope is `chicago/4d` alone.** `kevinrhaas/custom` is a monorepo of unrelated tenants —
CAD, print models, the Joliet game, a landing site. The dev tier covers the 4D app and nothing
else; every other tenant stays main-only. The artifact path stays `site`, so the ~2 GB of CAD
source can never enter it.

**5. Promotion is gated; deploy is not.** `deploy.yml` has no `needs: test` and must never get
one — a hard test gate on deploy once froze a fleet site for about 21 hours. The gate lives on
the *promotion*. The **hotfix exception** stands: a production emergency PRs straight into
`main`, and the next promotion's back-merge folds it into `dev` (which is why the promotion
back-merges main into dev *first* — otherwise it would silently revert the hotfix).

---

## The changelog, which the pipeline does not stamp for you

**Stamp before merging to `dev`. Nothing stamps later.** Prepend one entry to
`renderers/web/js/changelog.js` with all three authored fields blank — `v: null, ts: '',
date: ''` — then run `node tools/stamp-changelog.mjs`.

`date: ''` must be *present*: the stamper fills an empty `ts` but only *regenerates* a `date`
that already exists. `v: null` because the number is not yours to guess — two branches that
each compute "top + 1" both ship the same number.

**Re-run `node tools/check-changelog.mjs` AFTER any merge that touches this file, not only
before.** `.gitattributes` sets `merge=union`, which runs during the merge, so both parents can
be green and the result broken. That is exactly how `main` once shipped an unparseable
changelog and killed the What's-new tab and this project's release feed to Manager and the
launcher. The promotion workflow runs the contract check after both of its merges for this
reason.

---

## Where the releases are

**A release is a promotion, and nothing else makes one.** The loop merging into `dev` writes
changelog entries, but those entries are not released — they are queued. Everything that
displays this project's releases (the walkthrough's What's-new tab, Manager's ingest, the
polecat.live launcher) reads the **deployed** copy, which is `main`. So while `dev` runs
ahead, the release feed sits still at whatever was last promoted, and that is the design
working, not a fault: *overnight work must not ship straight to production.*

The cost is worth stating plainly, because it surprised the owner once already: **a day of
green, productive loop output looks like a dead release feed** until the promotion is
dispatched. `dev` ahead of `main` by N commits is the number to watch — Manager's Pipeline
card shows it, and `git rev-list --count origin/main..origin/dev` is the same answer.

Each promotion tags **`release-vNNN`**, where `NNN` is the changelog's top version — the same
number the What's-new tab shows, deliberately, so a tag names something a reader can find. A
promotion that carries no new changelog entry reuses the existing number and is left untagged
with a notice rather than inventing a second sequence. Tagging failures never fail the
promotion: by then the ship has already landed, and a missing label is not a bad deploy.

## Running it

```bash
# once, to create the branch and light up the preview
gh workflow run chicago-4d-pipeline-setup.yml

# ordinary work
git switch dev && git pull
git switch -c steward/<topic>
#   … one coherent unit of work …
./tools/check.sh && node tools/smoke_renderer.mjs      # both, foreground
./tools/preflight.sh                                   # the questions CI asks only on the PR
gh pr create --base dev
#   merge when the dev gate is green → /chicago/4d/dev/ updates

# production, owner only
gh workflow run chicago-4d-promote-to-prod.yml -f dry_run=true   # what would move
gh workflow run chicago-4d-promote-to-prod.yml                   # move it
```

---

## Proof of life

**2026-08-14** — this line was added on `dev` and nowhere else, as the pipeline's first
end-to-end proof: it must appear at `/custom/chicago/4d/dev/` while production at
`/custom/chicago/4d/walk/` is byte-for-byte unchanged. If you are reading it in a file that
also exists on `main`, the first promotion has since carried it across, which is the other
half of the proof.
