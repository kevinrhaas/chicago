---
id: T-0809
title: The janitor gates the branch un-merged and drops a conflict in silence, and the lane outruns its own merge lap
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-13
pr: 1269
claimed_by: run 9/13/2026, 2:02:56 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T19:41:54.733Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34776174481
---

The queue drain (T-0803 → T-0807) empties the pile. This ticket is why it filled, and
without it the pile is back inside a day. **Two causes, both measured, and both live in
`kevinrhaas/polecat-platform` — outside `chicago/4d`'s scope, so this ticket is the
record and the work is a PR there.**

**1. The janitor gates the branch UN-MERGED, then loses the conflict in silence.**
`.github/workflows/steward-janitor.yml` does `git clone --depth 1 -b "$BR"` and runs
`check.sh && smoke_renderer.mjs` on the branch **as it stands** — never merged with the
base it is about to be merged into. So:

- a green branch is merged **without the merge ever having been gated**, which is the
  exact hole T-0674 already filed against bot-opened PRs;
- when the merge then fails on conflict, the code path is
  `echo "merge failed (conflict?)"; SKIPPED=$((SKIPPED+1))` — **no comment on the PR, no
  label, nothing.** The red path comments; the conflict path does not.

That is why 21 PRs accumulated with nobody noticing: each one was swept, silently
skipped, and swept again the next hour. The fix is to merge the base into a scratch
branch first, gate THAT, and on conflict leave one comment naming the conflicting files
— reusing the existing "leave one comment, don't repeat it" guard that the red path
already has.

**2. The lane outruns its own merge lap.** `.github/steward/focus.json` had `custom` at
`slices: 5`, `everyHours: 1` — five PRs an hour into a branch where a merge lap costs
more wall-clock than the interval between merges. #880 wrote it down: *"the lane runs ten
slices an hour, every PR touches the same generated files, and a merge lap costs more
wall-clock than the interval between merges. Landing them one at a time loses ground."*

**Owner's call, 2026-09-05: drop `custom` to `slices: 2`.** That change is made in
polecat-platform and takes effect on the next `steward-focus.yml` tick once it is on
`main`.

**The standing rule the two together imply**, and the thing to write into AGENTS.md:
a `steward/*` PR that cannot merge is not "open", it is ROTTING — its ticket reads
`open` at the top of the queue and the next slice rebuilds the same work. So the janitor
must make an un-mergeable PR VISIBLE within one sweep, and the queue must carry a drain
lap whenever the count goes past what one lap can hold.

**Acceptance:** a PR against `kevinrhaas/polecat-platform` that (1) merges the PR's base
into the clone and gates the merge result, not the bare branch, and (2) comments once,
naming the conflicting paths, on any PR it cannot merge — with the existing
duplicate-comment guard extended to cover it. `focus.json` carries `custom` at
`slices: 2`. A sweep is observed doing both against this repo. AGENTS.md § How work ships
gains the rotting-PR rule with the count that bought it: 21 open, 21 conflicting, 6 build
products between them, five of them past saving.

Filed by the 2026-09-05 open-PR queue pass. T-0234 (the GraphQL quota) touches the same
workflow and should be read alongside it.

## Done, 2026-09-13 — the work is polecat-platform#161; this file is the record

**Acceptance item 1 — gate the merge, not the bare branch.** `steward-janitor.yml` no
longer does `git clone --depth 1 -b "$BR"`. `.github/steward/janitor-mergeability.sh
prepare <url> <dir> <base> <head>` puts base+head **merged** on disk and the gate runs on
that. Shallow on purpose: this repo is a 3.2 GB monorepo and seven bake legs have already
died on a full checkout of it (T-0437), so both tips arrive at depth 200 with **one**
deepen when that failed to reach a common ancestor — the case that makes a naive local
merge look unusable, and the one this ticket would otherwise have foundered on. The base
is read from the PR, never assumed `main`: `gh-rest.sh pr-sweepable` returns it as a third
column, because this repo, jobtracker and analytics are all dev-first.

**Acceptance item 2 — comment once, naming the conflicting paths.** `prepare` exits 1 and
prints the paths; the sweep comments once behind the marker `Steward janitor: cannot
merge`, on the same duplicate-comment guard the red-gate path already had. A server-side
merge that fails *after* a green gate — the base moved in between — is no longer silent
either, and `UNKNOWN` mergeability is skipped-and-retried with a journal line rather than
guessed at.

**The measurement that made the case.** Run read-only against this repo on 2026-09-13,
before the fix: **all five** open steward PRs conflicted with `dev`.

| PR | conflicting paths |
|---|---|
| #1210 | 16, incl. `heightfield.bin`, `assets/manifest.json`, `changelog.js`, `QUEUE.md` |
| #1231 | `changelog.js`, `tickets/QUEUE.md` |
| #1239 | those two plus `tools/dev-smoke-state.json` |
| #1242 | those three plus `assets/manifest.json` |
| #1252 | `changelog.js`, `tickets/QUEUE.md`, `tools/dev-smoke-state.json` |

Every one of them collides on files the root `.gitattributes` **deliberately** refuses to
union-merge — its own note records five silent changelog corruptions in one day as the
reason. So the conflicts are correct and expected; the silence about them was the defect.
Not one of the five had been told, and each ticket still read `open` at the top of the
queue, where the next slice picks the same row.

**Acceptance item 3 — the rotting-PR rule.** Written into `AGENTS.md` § How work ships
with the count that bought it, and into `docs/AUTOMATION.md`'s janitor row in
polecat-platform.

**Gated, not asserted.** `janitor-mergeability.sh --self-test` builds real git repos with
a real conflict and a base that moved after both branched (11 checks).
`test-janitor-sweep.sh` does not copy the sweep logic — it `yaml.safe_load`s
`steward-janitor.yml` and runs the **shipped** step body against fakes (20 checks), so a
later edit to the workflow that breaks this contract fails in CI. Both, plus the existing
`test-gh-rest.sh`, now run in that repo's `ci.yml`.

**NOT done, deliberately: `focus.json` at `slices: 2`.** That was the owner's 2026-09-05
call and it is honoured-then-superseded — he has moved the number twice since, to 1 on
2026-09-07 ("1 continuous lane") and to 3 today. The file is his to set and a stale
acceptance line is no licence to revert it, so `focus.json` is untouched.

**And the sweep was not observed live.** A full sweep cannot be observed inside one run:
this repo's janitor gate is `check.sh && node tools/smoke_renderer.mjs` bare, ~25 min per
viewport, against five open PRs, inside a workflow with `timeout-minutes: 55`. That is
T-0437's problem and this ticket does not fix it. What was done instead is stronger than
one dispatch: the shipped sweep body is executed by a self-test on every CI run, and the
mergeability helper was run read-only against all five live PRs (the table above).
