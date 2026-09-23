# Polecat fleet conventions and integration path

> **Research dossier — committed verbatim as a citable input.**
> Produced by a research agent on 2026-08-09 for the 4D Chicago project.
> Claims carry their own confidence tags and sources; nothing here is authoritative
> until promoted into `data/` with a resolving `source_id`. Where a source could not
> be retrieved, the gap is stated rather than filled.

---

# Polecat fleet — how ships happen, and what a "Chicago 1835 walkthrough" would need

## 0. Environment check (Playwright) — answered first

**Yes, Playwright is available**, Chromium only.

| Thing | Value |
|---|---|
| `playwright` CLI | `/opt/node22/bin/playwright`, **v1.56.1** |
| Global npm root | `/opt/node22/lib/node_modules` (contains `playwright`, plus `chromedriver`, `http-server`, `serve`, `typescript`, `eslint`, `prettier`) |
| `/opt/pw-browsers` | `chromium`, `chromium-1194`, `chromium_headless_shell-1194`, `ffmpeg-1011` — `INSTALLATION_COMPLETE` + `DEPENDENCIES_VALIDATED` markers present |
| Chromium binary | `/opt/pw-browsers/chromium-1194/chrome-linux/chrome` |
| **WebKit** | **NOT installed** — no `/opt/pw-browsers/webkit*` |

The fleet's local-run convention is an env var override, seen in `/home/user/manager.polecat.live/.github/smoke-test.mjs:38` and `.github/gen-shots.mjs:102`:

```js
const browser = await chromium.launch({ executablePath: process.env.PW_EXECUTABLE || undefined });
```

So locally: `PW_EXECUTABLE=/opt/pw-browsers/chromium-1194/chrome-linux/chrome node .github/smoke-test.mjs` (or set `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers`).

**Caveat for a new project:** JobTracker's smoke (`/home/user/jobtracker.polecat.live/.github/smoke-test.mjs:17`) imports **both** `chromium` and `webkit`. Copying that file verbatim will fail in this environment. A new project should be **Chromium-only locally**, and only add WebKit in CI (`npx playwright install --with-deps chromium webkit`, per `/home/user/jobtracker.polecat.live/.github/workflows/ci.yml`).

---

## 1. Fleet-wide automation orchestration — who fires what, where prompts live

**Everything is GitHub Actions.** Claude Code Remote routines were tried and abandoned — see the post-mortem in `/home/user/polecat-platform/docs/AUTOMATION.md:71-82` (trigger→execution path was unreliable; the prompts remain the portable source of truth if routines are revisited).

**The hub is `kevinrhaas/polecat-platform`.** Workflows in `/home/user/polecat-platform/.github/workflows/`, prompts in `/home/user/polecat-platform/.github/steward/*.md`.

### The scheduler is one data file

`/home/user/polecat-platform/.github/steward/focus.json` is the **single fleet scheduler**. All standalone crons for sweeps/janitor were retired 2026-07-16. Only one real cron exists:

- **`steward-focus.yml`** — heartbeat `*/10` UTC, Claude-free. Each tick reads `focus.json` through `.github/steward/schedule.mjs` (the canonical evaluator) and dispatches one improve run per lane that is **due AND idle**.

Lane fields (identical for `apps.*` and `jobs.*`): `enabled`, `everyHours`, `offset`, `window` (UTC hour range, wraps midnight), `startAt`, `until`, `slices` (1–5, **chained sequentially** — each `steward-improve` run dispatches the next on completion via its "Chain next slice" step; firing all at once overflows the per-app concurrency queue and GitHub cancels the surplus), and optional per-lane `model` (default `claude-opus-5`).

The `jobs` section schedules platform-level work with the same fields: `fleet-improve`, `sweep-ux`, `sweep-tech`, `janitor`. **Current state: every app lane is `enabled: false` except `analytics.polecat.live` (hourly, opus-5), and every job lane is disabled.** Cost posture is documented at `AUTOMATION.md:107-117`.

### The workflow roster

| Workflow | Prompt | What it does |
|---|---|---|
| `steward-improve.yml` | `.github/steward/improve.md` | ONE unit of work. `app=<repo>` input = focus mode; empty = fleet-wide pick |
| `steward-focus.yml` | (Claude-free) | The `*/10` heartbeat dispatcher |
| `steward-sweep-ux.yml` | `.github/steward/sweep-ux.md` | Read-only user walk of every live site → one findings issue per app |
| `steward-sweep-tech.yml` | `.github/steward/sweep-tech.md` | Audit: pageerrors, changelog contract, vendor sha256 drift, SW caches, CI health, secrets |
| `steward-janitor.yml` | (Claude-free) | Sweeps all fleet repos for open `steward/*` / `chore/polecat-shell-*` PRs, re-runs each app's smoke against the branch, merges green, comments on red. **Never touches drafts or `hold`-labeled PRs** |
| `steward-shell-release.yml` | `.github/steward/shell-release.md` | Bump `lib/VERSION` + manifest + tag, vendoring PRs to every app |
| `sync-shell.yml` | — | Copies `lib/` → each app's `vendor/polecat-shell/`, opens PRs |

### Secrets (on the hub repo)

Required: `CLAUDE_CODE_OAUTH_TOKEN`, `STEWARD_PAT` (classic PAT, repo scope on `kevinrhaas/*` — powers cross-repo clone/push and `gh`). Optional per-app: `MANAGER_ADMIN_TOKEN`, `ANALYTICS_ADMIN_TOKEN`, `JOBTRACKER_ADMIN_TOKEN`, `RELAY_ADMIN_TOKEN`, `MODELSERVER_ADMIN_TOKEN` — unlock each app's `lib/access.js` UX gate so sweeps exercise the real UI. Prompts forbid echoing token values anywhere.

### The Steward journal

Every run posts its summary as a comment on an always-open issue labeled `steward-journal`, tagged `<!-- steward-run:ID -->`, via `.github/steward/journal.sh`. Manager's Fleet Ops matches the tag to show each run's narrative (`/home/user/manager.polecat.live/js/github.js:161-173`, `journalFor()`).

### The shipping loop (the core doctrine)

From `/home/user/polecat-platform/docs/FLEET-GUIDE.md:8-17` and `AUTOMATION.md:60-65`:

> `steward/<topic>` branch → stamp changelog with the repo's own tool → run the repo's smoke gate → open PR → **merge it yourself when green**. Kevin does not manually merge automation output. Merge is ship. Genuinely risky/architectural work is the one exception: leave the PR open with the **`hold`** label.

Also: **parallel sweep subagents must each get their own working directory** (fresh `git worktree` or `mktemp -d` clone) — a shared checkout on 2026-07-28 produced a false credential-harvesting alarm (issue #101), documented at `AUTOMATION.md:98-104`.

---

## 2. The promotion pipeline (dev → stage → main)

Source: `/home/user/jobtracker.polecat.live/docs/PIPELINE.md`. JobTracker is the **pilot**; **analytics has since adopted it** — those are the only two repos with `.github/pipeline.json` today.

### Stages

| Stage | Branch | URL | Gate |
|---|---|---|---|
| Integration | `dev` | `/dev/` | **Dev gate** (`ci.yml`): `validate.mjs` + smoke, on PRs into dev and pushes to dev |
| Candidate | `stage` | `/stage/` | **Full gate** (`promote-to-stage.yml`): whole smoke suite against the *staged* build |
| Production | `main` | `/` | **None at deploy** — Guard main (`auto-revert.yml`) self-heals after the fact |

One Pages artifact carries all three: `deploy.yml` assembles `main` at root, then `stage-preview.mjs` folds `stage` and `dev` in at `/stage/` and `/dev/` — paths rewritten, SW replaced with a self-unregistering stub, `noindex` + robots exclusions, fixed banner (amber = dev, violet = stage). Previews share the production origin and its localStorage; they are search-hidden, **not** access-controlled.

### Mechanics

1. **Feature work**: branch `steward/<topic>` off `dev`, PR **into dev**, squash-merge on green dev gate. Merge-to-dev is *stage*, not ship.
2. **dev → stage** (`promote-to-stage.yml`): on dispatch or the `.github/pipeline.json` schedule. Back-merges `main` into `dev` (hotfixes never lost) → merges `dev` into `stage` (`--no-ff`) → assembles `/stage/` → runs the **full suite against it**. Red → `stage` force-rolled back to its pre-promotion commit (the only force-push in the pipeline, and only of the machine-owned `stage` pointer) + issue filed. Green → `/stage/` publishes. **This run's green/red IS the stage status record.**
3. **stage → prod** (`promote-to-prod.yml`): **dispatch-only, never scheduled.** Refuses while latest stage promotion is red (`requireGreenStageForProd`; `force` overrides). Merges `stage`→`main` (`--no-ff`), tags `release-vNNN`, freezes `/v/<n>/` via `archive-release.mjs`, dispatches deploy.
4. **Rollback** (`rollback-prod.yml`): `git revert -m 1` — main history stays append-only, never force-pushed.

**Hotfix bypass (deliberately unchanged):** branch off `main`, PR into `main`, merge. A red stage cannot block it — the prod path never consults stage. Next promotion's back-merge folds it into `dev`.

> **Doctrine:** *promotion is gated; deploy is not.* The "never hard-gate deploy on CI" rule came from a flaky test freezing analytics for ~21 hours. Dev/stage gates may be hard because they gate integration branches.

### What a repo needs to join

Files (all under `.github/`, per `PIPELINE.md:78-90`):

```
pipeline.json                  Pausable schedule + gate config (data file)
pipeline-schedule.mjs          "Is a scheduled promotion due?" evaluator
stage-preview.mjs              Assembles /stage/ + /dev/ inside the Pages artifact
validate.mjs                   Shared syntax gate (Guard main + dev gate + stage)
workflows/pipeline-setup.yml   One-button branch creation
workflows/ci.yml               Dev gate
workflows/promote-to-stage.yml Full gate + auto-rollback of stage
workflows/promote-to-prod.yml  Dispatch-only release + tag + snapshot
workflows/rollback-prod.yml    Revert the latest promotion merge
workflows/deploy.yml           Three-stage Pages artifact
workflows/auto-revert.yml      Guard main (merge-commit-aware)
```

Plus `archive-release.mjs` for the `/v/<n>/` snapshots + `releases.json`.

**`pipeline.json` shape** (verbatim from `/home/user/jobtracker.polecat.live/.github/pipeline.json`):

```json
{
  "_doc": "…DATA file, like polecat-platform's .github/steward/focus.json — editing it is a sanctioned direct commit to main…",
  "promoteToStage": { "enabled": true, "paused": false, "everyHours": 24,
                      "offset": 7, "window": [0, 24], "catchUpHours": 4 },
  "gates": {
    "devGate": "node .github/validate.mjs + node .github/smoke-test.mjs (ci.yml on PRs into dev and pushes to dev)",
    "stageSuite": "node .github/smoke-test.mjs against the STAGED /stage/ form (promote-to-stage.yml)",
    "stageSuiteTimeoutMinutes": 30
  },
  "requireGreenStageForProd": true
}
```

**Activation is idempotent and one-button** — merging the pipeline PR activates nothing (`deploy.yml`'s stage steps no-op until the branches exist). Then: dispatch `pipeline-setup.yml` → verify `/`, `/stage/`, `/dev/` → dispatch `promote-to-stage.yml` once → optional broken-commit drill → dispatch `promote-to-prod.yml`.

**Manager auto-discovers pipeline repos**: `/home/user/manager.polecat.live/js/views/pipeline.js:12-14` probes every fleet repo for `.github/pipeline.json`. Adopting the pipeline lights up the Pipeline view **with zero Manager changes**.

---

## 3. The changelog contract and smoke gate — exact formats and commands

### The changelog contract

Canonical definition: `/home/user/polecat-platform/docs/SHELL-API.md:192-206`. Every app publishes `https://<app>.polecat.live/js/changelog.js`:

```js
export const CHANGELOG = [ // newest first
  { v: 42, title: 'Short human title', kind: 'feature'|'polish'|'fix',
    ts: '2026-07-01T18:20:00Z', items: ['sentence', ...] },
];
export const LATEST_VERSION = CHANGELOG[0].v;
```

Hard rules:
- **Literal JS** — unquoted keys, single-quoted strings, escaped apostrophes.
- **No `//` inside item text.**
- **`ts` left EMPTY (`ts: ''`) by authors** and stamped by the repo's own tool.
- **`date` is derived, never hand-edited** — a US-Central alias regenerated from `ts`.
- Real entries also carry `date` and use `kind` values beyond the three documented (e.g. `'infra'` in JobTracker v61).

**Stamp tools are per-repo** (`FLEET-GUIDE.md:24-31`, `AUTOMATION.md:90-92`):

| Repo | Command |
|---|---|
| games | `node tools/stamp-changelog.mjs` |
| jobtracker / relay / autoselector / manager | `node .github/stamp-changelog.mjs` |
| analytics | `node tools/changelog-normalize.js` |
| polecat-app | its own generator |
| polecat-platform | `node scripts/stamp-changelog.mjs` (for `site/js/changelog.js`) |

`/home/user/jobtracker.polecat.live/.github/stamp-changelog.mjs` is the reference implementation — ~30 lines, no deps. It fills the **first** empty `ts` with `new Date().toISOString()` and regenerates every `date:` via `toLocaleString('en-US', { timeZone: 'America/Chicago', … }) + ' CT'`.

**Why it's sacred:** Manager's `js/ingest.js` parses the file **without executing it** — it extracts the `[…]` array literal with a bracket/string-aware walker (`extractArrayLiteral`), then converts JS-literal → strict JSON (`jsLiteralToJSON`) keeping string literals and structural runs strictly apart. Two documented past corruptions (`ingest.js:52-64`) came from regexes running inside string values. The launcher on polecat.live parses it live too.

### The smoke gate

**Bar** (`SHELL-API.md:208-217`, `FLEET-GUIDE.md:48-53`): Playwright at **390×780 AND desktop (1280×800)**, **zero pageerrors**, **both themes always**, all palettes, dashboard tiles/KPIs link to their detail, bump `sw.js` cache name when precached files change, one coherent unit of work per run, **no model identifiers in repo artifacts**.

**Commands by repo:**

| Repo | Command |
|---|---|
| jobtracker / manager / relay / autoselector | `node .github/smoke-test.mjs` |
| polecat-platform | `node scripts/smoke-test.mjs` |
| analytics | `node tests/run.js` |

`/home/user/jobtracker.polecat.live/.github/smoke-test.mjs` is the reference: spins a `node:http` static server on port 4178, opens marketing + gated app with a hardcoded valid team token, fails on console errors or missing key UI. It honors **`SMOKE_PREFIX`** (e.g. `SMOKE_PREFIX=/stage`) so `promote-to-stage.yml` runs the exact same suite against the staged preview and catches path-rewrite bugs.

**Smoke is ADVISORY in CI on non-pipeline repos — never a deploy gate.** `auto-revert.yml` ("Guard main") heals instead.

---

## 4. What Manager needs to "see" a project

Manager is a **local-first browser app** — `/home/user/manager.polecat.live/js/store.js` is a SQLite-shaped relational layer over one localStorage blob (`manager.workspace.v1`).

### Tables

```
projects     the fleet — one row per managed repo/site
releases     per-project "what's new" entries (a project's changelog)
credentials  shared (scope 'global') or per-project config/secrets
runs         the self-improvement cadence log (feature / sweep / …)
fieldDefs    fleet-wide schema for custom project metadata fields
savedViews   user-defined library filter+sort combos
dismissals   local per-browser notification state (excluded from merge-import)
```

### The `projects` row (from `Store.addProject`, `store.js:401-410`)

```js
{ id, slug, name, repo, site, sessionUrl, description, assessment, cadence,
  status:'idea', tags:[], icon:'grid', pinned:false, fields:{},
  autoSync:false, lastAutoSyncAt:0, autoSyncFailCount:0, autoSyncLastError:'',
  statusLocked:false, statusAuto:false, notes:'', notesHistory:[],
  changelogUrl, lastSyncAt, private, createdAt, updatedAt }
```

`id === slug` (slugified from `name`). Statuses: `live · active · building · paused · idea · archived` — **editorial signals a human sets**, not changed by syncing (except auto-status below).

### How a project gets registered

Three ways, all human/agent-initiated — **there is no auto-discovery of repos**:

1. **Seed** (`store.js:1140-1174`) — the built-in fleet, e.g. `{ id:'manager', name:'Manager', repo:'kevinrhaas/manager.polecat.live', site:'https://manager.polecat.live', status:'live', icon:'gauge', cadence:'GitHub Action · hourly', tags, description, assessment }`. Note `solution-engineering` is seeded with `site:''`, `status:'active'`, `private:true` — the precedent for a **multi-project workspace repo with no single deployed site**.
2. **`Store.addProject()`** via the Projects UI.
3. **Workspace JSON import** (`importJSON` / `mergeImport`).

**`kevinrhaas/custom` is NOT in the seed today.**

### What it ingests

- **`changelogUrl`** — defaults to `site + '/js/changelog.js'` (`ingest.js:19-22`, `guessChangelogUrl`). `syncReleases()` reconciles fetched entries into `releases` rows keyed by `v` (adds new, overwrites changed); `forceSyncReleases()` does a full reconcile where upstream wins and orphaned synced rows are deleted (hand-added rows, `source !== 'sync'`, are never touched). **CORS is expected to fail** on GitHub Pages — there's a paste-to-import fallback.
- **Auto-status derivation** (`deriveSyncStatus`): newest release ≤45 days → `live` (has `site`) or `active` (no site); >180 days → `paused`; in between → unchanged. Skips `statusLocked` and `archived`.
- **Health score** 0–100 from `recency 40 / velocity 40 / status 20` (renormalized), banded Thriving/Healthy/Steady/Slowing/Stale.

### What Fleet Ops needs from `repo`

`/home/user/manager.polecat.live/js/github.js` — a GitHub REST client whose token comes from the Credentials vault (only the vault row id is stored in `settings.fleetOps.credId`). `fleetRepos()` = every project with a `repo`, plus `kevinrhaas/polecat-platform`. Per-repo it fetches:

- `stewardPRs(repo)` — open PRs whose head ref matches `/^(steward|chore)\//` or whose title matches `/^chore: polecat-shell/`
- `sweepIssues(repo)` — open non-PR issues with `/sweep/i` in the title
- `checkState(repo, sha)` — check-runs reduced to one status dot
- `getBranch` / `compareRefs` / `listTags` / `workflowRuns` / `dispatchRepoWorkflow` — the pipeline primitives
- `getRepoJson` / `putRepoJson` — contents-API read/write with **sha compare-and-swap** (a concurrent edit 409s instead of clobbering)

A project row flagged `private: true` short-circuits to a synthetic 404 without a network round trip when no token is present, sparing the ~60/hr anonymous budget.

**So the minimum for Manager to see a project meaningfully:** a `projects` row with `name`, `repo` (`owner/name`), and either a `site` publishing `/js/changelog.js` or manual paste-import of releases.

---

## 5. Recommendation — minimal conventions for a "Chicago 1835 walkthrough"

### Important context you should know before deciding

**`kevinrhaas/custom` already hosts Chicago work.** `/home/user/custom/chicago/` contains `pre_fire_v1` and `postfire_1870s_v1` (CSV data, schema, docs, maps, research, viewer, xlsx). `/home/user/custom/site/chicago/` publishes them at `site/chicago/{pre-fire,rebuilding-1870s}/viewer/app.js` with a shared `index.html`. A **"Chicago 1835 walkthrough" is a natural third sibling**, not a new repo.

Also relevant: `custom` is **already partly fleet-shaped**. Its `README.md` says *"Not part of the Polecat app fleet, but it follows the platform's static-first / aurora-backdrop / light-dark conventions."* Two of its subfolder projects — `site/compass/` and `site/hosta/` — **already vendor `polecat-shell`** (`vendor/polecat-shell/{shell,ui,icons,theme,catalog,views}.js`). Its `.github/workflows/deploy.yml` already mirrors the fleet's single-deploy-authority pattern (`upload-pages-artifact` with `path: site`, publishing only the curated `site/` folder so ~2 GB of CAD source stays out) and already runs a **JS syntax sanity check** that is a de-facto proto-`validate.mjs`.

### Recommendation: build it as a subfolder in `kevinrhaas/custom`

A new standalone repo buys nothing here and costs a Pages site, a CNAME, a deploy workflow, and a Manager row. The Chicago material is already there, the deploy already works, and the shell is already vendored twice over.

### Adopt NOW (cheap, and expensive to retrofit)

1. **The changelog contract — this is the one non-negotiable.** Ship `site/chicago/1835/js/changelog.js` in fleet format from commit one: literal JS, newest-first, `ts: ''` on new entries, no `//` inside item text, `export const LATEST_VERSION = CHANGELOG[0].v`. Copy `/home/user/jobtracker.polecat.live/.github/stamp-changelog.mjs` (~30 lines, zero deps) and point `FILE` at the new path. Retrofitting version history you never recorded is impossible; everything else here is mechanical later.
2. **Vendor `polecat-shell` and use its tokens/theme/icons** — follow the `site/compass/` and `site/hosta/` precedent. Keeps `vendor/` read-only from day one so a future sha256 drift check passes, and means the aurora backdrop / light-dark / icon conventions come free.
3. **A Chromium-only smoke script** at `site/chicago/1835/smoke.mjs` (or repo-level `.github/smoke-test.mjs`): static server + Playwright, **390×780 AND 1280×800, zero pageerrors, both themes**, honoring `PW_EXECUTABLE` and `SMOKE_PREFIX`. Add WebKit only in CI. The 390×780 mobile gate is the one that's genuinely painful to retrofit into a 3D/map walkthrough — design for it now.
4. **Branch + PR discipline**: `steward/<topic>` branches, PR, self-merge on green, never push to main, `hold` label for anything architectural. Costs nothing, and it's what makes the janitor and the improve loop safe to point at the repo later.
5. **`docs/` with a stated playbook** — a `ROADMAP.md` (or `BUILD_LOOP.md`/`STATUS.md`). The steward's picking logic in `improve.md` explicitly reads these; without one, a focus lane has nothing to work from.
6. **Register a Manager `projects` row** — `{ name: 'Chicago 1835', repo: 'kevinrhaas/custom', site: 'https://kevinrhaas.github.io/custom/chicago/1835/', status: 'building', cadence: 'manual' }`. One row, and Manager starts tracking health, releases, steward PRs, and sweep issues.

### Can WAIT

- **The promotion pipeline** (dev/stage/main, 11 files). It's a two-repo pilot. Adopting it is purely additive and Manager auto-discovers it the moment `.github/pipeline.json` exists — genuinely zero-cost to defer.
- **`archive-release.mjs` / `/v/<n>/` snapshots.** Only matters once there's history worth freezing.
- **A `focus.json` lane.** Every app lane is disabled today anyway. Adding `"custom": { "enabled": false, "everyHours": 3 }` is a one-line flip whenever you want it.
- **`catalog.js` FLEET entry / a `*.polecat.live` subdomain.** That's the decision to make it a *suite app*, which this probably isn't — it's a project on a project site.
- **`sw.js` / PWA**, service worker cache-name discipline, `site-chrome.js` header/footer, the `access.js` gate, `auto-revert.yml` Guard main. All bolt on cleanly later.

**One structural caveat:** a subfolder project in `custom` cannot get its own `dev`/`stage` branches independently — the pipeline is per-repo, and `custom`'s single `deploy.yml` publishes all of `site/`. If staged delivery for this specific walkthrough ever matters, *that* is the argument for a standalone repo. Nothing else is.
