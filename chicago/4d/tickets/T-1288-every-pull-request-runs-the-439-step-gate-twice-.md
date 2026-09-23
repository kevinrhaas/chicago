---
id: T-1288
title: Every pull request runs the 439-step gate TWICE, because the check fires on push and on pull_request for the same commit
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: 1414
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T19:48:56.356Z
claimed_run: null
---

`.github/workflows/chicago-4d-check.yml` fires on **both** `push` and `pull_request`:

```yaml
on:
  push:
    paths: ['chicago/4d/**', '.github/workflows/chicago-4d-check.yml']
  pull_request:
    paths: ['chicago/4d/**']
```

A steward branch with an open pull request satisfies both. So every push to such a branch
starts the 439-step suite TWICE on the same commit, and the two runs are identical.

Observed on 2026-09-17 on every open pull request in the queue at once — #1411, #1410, #1409,
#1407, #1405 and #1392 each showed two `gate` check runs on the same head sha. One gate is
roughly ten minutes. The lap pushes to every open PR on every merge into `dev`, so the waste
is not once per PR: it is once per PR **per lap**, and there were four laps in the hour this
was found.

**This matters because CI time is what makes the queue slow to converge.** Every merge into
`dev` dirties every other pull request, each needs a lap, and each lapped head needs a gate
before it can be called clean. Paying twice for that doubles the wall-clock of the whole
drain.

**The fix is one line**, and it is the standard shape:

```yaml
on:
  push:
    branches: [dev, main]
    paths: [...]
  pull_request:
    paths: [...]
```

A branch push is then gated through the pull-request event only, and `dev` and `main` keep
their own push gate. **Check the other workflows for the same shape before assuming this one
is alone** — and check that nothing downstream keys off the push-event check run by name,
because `merge-ready` merges on GitHub's `clean`, which is computed from the REQUIRED checks
and would change if a required check stops being produced on push.

**Acceptance:** one pushed commit on a branch with an open pull request produces exactly ONE
`gate` check run; `dev` still gates on its own pushes; `merge-ready` still reports `clean` for
a green PR afterwards, verified on a real PR rather than reasoned about.


## WHAT THE FIX ACTUALLY WAS, AND THE COST THAT WAS NOT IN THE FILING

**Owner, 2026-09-17: "fix the double gate now."** `push` is now filtered to
`branches: [dev, main]`. `pull_request` is untouched.

**The file said not to do this**, and that comment is answered rather than deleted. It read:
"Neither trigger carries a branch filter, which is deliberate and worth stating so nobody
'tidies' it into `branches: [main]`: … an unfiltered trigger covers steward branches too."
The reason is real, and it is already served by the `pull_request` trigger. What the
unfiltered push bought on top of that was a second, identical run.

**The cost was worse than the filing said.** The filing called it waste. It is also LATENCY: a
pull request is not `clean` until every required check passes, so the PR waited on the SLOWER
of the two identical runs. Observed directly while draining the queue — four PRs sat
`blocked` with one `gate` green and its twin still in progress, and the merge driver's stall
alarm fired on them. The lap re-pushes every open PR on every merge into `dev`, so this was
paid once per PR **per lap**, four laps in that hour.

**What is given up, stated rather than glossed:** a steward branch pushed BEFORE its pull
request exists is not gated by that push. The gap closes when the PR opens, which in this repo
is the same run, and a run that dies before opening one now gets a DRAFT pull request from the
steward's salvage step (T-1155) — a draft still fires `pull_request`. Nothing that was covered
stops being covered.

**Checked, not assumed:** `chicago-4d-check.yml` was the only workflow in the repository with
an unfiltered `push` beside a `pull_request`.
