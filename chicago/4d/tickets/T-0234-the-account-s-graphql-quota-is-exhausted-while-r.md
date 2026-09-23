---
id: T-0234
title: The account's GraphQL quota is exhausted while REST sits untouched, and a slice loses its PR to it
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-16
pr: 1372
claimed_by: run 9/16/2026, 11:38:27 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T01:49:35.668Z
claimed_run: null
---

GitHub meters **GraphQL and REST as two separate hourly buckets**, and the fleet
is spending one of them to nothing while the other is barely touched. Read by
slice 3 of 3 mid-run, 2026-08-27 at **15:54:32Z**:

    graphql   limit 5000   remaining 0      used 6690    reset 16:35:45Z
    core      limit 5000   remaining 4969   used 31      reset 16:08:28Z

**Zero of five thousand on one side; 4,969 of five thousand still available on
the other.** The account is not out of GitHub API — it is out of *one kind* of
it, and the kind `gh` reaches for by default.

## What it cost, in one run

Slice 3 of the 15:18 batch (steward-improve run 1140, T-0216) hit it three
separate times:

1. **`gh pr create` failed outright** — `GraphQL: API rate limit already
   exceeded for user ID 4193586`. The unit of work was finished, gated and
   pushed; the only thing standing between it and a PR was the wrong bucket.
2. **`dev-smoke-state.mjs ci <run id>`** — `failed to get jobs: HTTP 403: API
   rate limit exceeded`. The tool the run had just built could not read the CI
   half of its own data source, which is written up in that ticket as "the CI
   half is unread".
3. **`journal.sh` skipped the run's journal entry** — *"steward-journal lookup
   failed (rate limit or API error) — skipping journal entry, not creating a
   duplicate issue"*. The run happened and the ledger does not know.

**That run only got a PR because the agent thought of the workaround itself.**
It read `gh api rate_limit`, saw core was almost untouched, and posted the PR
straight to the REST endpoint (`POST /repos/kevinrhaas/custom/pulls`) with
Python instead. #402 exists because of an improvisation, not because the
pipeline can do this.

That is the shape of the defect. **A slice that does not improvise loses its
PR** — and a finished, gated, pushed unit of work with no PR is exactly the
failure `tickets/README.md` § *"A claim is only real once its PR merges"*
describes, and the one #395 was a salvage of.

## Why GraphQL specifically

`gh` uses GraphQL for most of the commands the fleet leans on — `gh pr create`,
`gh pr list`, `gh pr view`, `gh pr merge`, `gh pr comment`, `gh issue create`,
`gh search`. Nearly every step of the loop touches at least one. Counted across
polecat-platform's steward surface: `steward-janitor.yml` alone uses `pr list`,
`pr view` twice, `pr merge` and `pr comment`; `sync-shell.yml` uses `pr create`
three times and `pr list`; both sweeps use `issue create`. The improve agents
then use them again, per slice.

And GraphQL is not metered per call — it is metered in **points**, by query
complexity, so one `gh pr list` over a repo with hundreds of PRs is worth many
REST calls. `used: 6690` against a 5,000 limit is not 6,690 commands.

**Manager is not the drain**, checked rather than assumed: its `js/github.js`
contains no GraphQL at all — the console is REST end to end, which is why it
kept working while the loop did not.

## Why it is worse now, and will get worse again

The batch is the multiplier. One slice used to run at a time; the lane is now
**5** and the cap was raised to 10 the same day. Five concurrent agents each
running `gh pr create`/`view`/`list`, on top of the janitor and the bake, share
one 5,000-point hourly bucket. **The quota is per ACCOUNT, not per run**, so
slices do not each get their own — they compete, and the loser gets a 403 at
the last step of a 46-minute run.

This also hit a human operator the same afternoon: an interactive session was
locked out for a full **27 minutes** at ~14:35Z on the same account.

## The plan, in order of value

1. **Stop using GraphQL for the things REST does.** PR create, list, view,
   merge, comment all have REST equivalents on the core bucket that is sitting
   at 99 % free. Either call `gh api` with the REST path directly, or set the
   documented `gh` escape hatch where one exists. This is the whole fix for the
   symptom and it costs nothing — it is the same request against a different
   meter.
2. **Make the failure loud and recoverable where it still can happen.** A 403
   on the last step of a 46-minute run must not end with the work unpushed and
   unclaimed. The `salvage.sh` step already exists for unpushed work; it needs a
   sibling for *unPR'd* work — a branch that is pushed, gated and has no PR is
   recoverable, and today only a human notices.
3. **Read the meter before the batch, not after the failure.** `gh api
   rate_limit` is one cheap core call. A slice that starts with graphql
   remaining at 0 should know, and say so in its summary, rather than
   discovering it at the PR.
4. **Then reconsider the slice count against the measured burn.** Five may be
   fine once (1) lands, because REST has the headroom. It is not fine while
   every slice is drawing on an already-empty bucket. **Do not lower the count
   as the fix** — that trades throughput for a defect that has a real repair.

## What NOT to conclude

**This is not an argument that the loop is running too hard.** The account has
4,969 REST calls of headroom at the moment it fails. The work is not too big for
GitHub; it is aimed at the wrong meter. A run that reads the numbers and
concludes "back off to 3 slices" has misread them, the same way a red gate that
is red for everyone gets misread as a fact about the branch under test.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every PR the loop opens, lists, views, merges or comments on goes through the
  REST bucket, and `gh api rate_limit` is read at the end of a batch to show the
  graphql bucket is no longer being drained. **Measured across a real 5-slice
  batch, not a single run** — one slice never exhausted it either.
- A slice whose PR creation fails leaves a recoverable artefact and says so in
  its summary. Demonstrated against an injected 403, not asserted — a run that
  succeeds proves nothing about the path that only opens when it fails.
- The graphql/core split is written where a run will read it, so the next agent
  meeting a 403 does not have to rediscover that the other bucket is empty.
- If any call genuinely has no REST equivalent, it is **named**, with what it
  costs, rather than left as a silent exception.

**Links:** T-0232 (the promotion's checkout lottery — the other pipeline defect
that only shows under load) · #402 (the PR that only exists because of the
workaround) · #395 and `tickets/README.md` § *"A claim is only real once its PR
merges"* (what a lost PR costs) · steward-improve run 1140 · polecat-platform
`.github/workflows/steward-janitor.yml`, `sync-shell.yml`, `.github/steward/`.
