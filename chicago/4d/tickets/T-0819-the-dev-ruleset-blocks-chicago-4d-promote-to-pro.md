---
id: T-0819
title: The dev ruleset blocks chicago-4d-promote-to-prod's back-merge: it pushes to dev as github-actions[bot] and the bypass list is empty, so production cannot be promoted
state: withdrawn
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: #903 opens the back-merge PR and main carries "Promote chicago/4d dev→prod: 476 commit(s)" — production promotes
needs_bake: false
closed_at: 2026-09-10T04:20:10.585Z
claimed_run: null
---

The dev ruleset blocks chicago-4d-promote-to-prod's back-merge: it pushes to dev as github-actions[bot] and the bypass list is empty, so production cannot be promoted.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

## The measurement

`.github/workflows/chicago-4d-promote-to-prod.yml` line 126:

```
    # 1. main → dev, so a hotfix is never lost by the forward merge.
    git checkout -B dev origin/dev
    git merge --no-edit main -m "Back-merge main into dev before promotion"
    git push origin dev          ← DIRECT PUSH TO dev
```

It runs on `actions/checkout@v4` with no explicit token and `permissions:
contents: write`, so it pushes as **`github-actions[bot]`** on the default
`GITHUB_TOKEN`.

A ruleset on `dev` that requires a status check — and more so one that also
requires a pull request — applies to direct pushes as well as to merges. With an
**empty bypass list** that push is rejected, the promotion step fails, and
**production cannot be promoted at all**: this workflow is the only route main
moves (`AGENTS.md`: *"Production moves ONLY when the owner dispatches
chicago-4d-promote-to-prod.yml. No schedule, no agent."*).

## Two ways to fix it, and they are not equivalent

1. **Add `GitHub Actions` to the ruleset's bypass list.** One setting, no code.
   Humans and the steward still go through PRs; only the promotion workflow's
   own back-merge is exempt. This is the smaller change and the recommended one.
2. **Make the back-merge open a PR** instead of pushing. More correct — the
   back-merge would then be gated like everything else — but it turns a
   synchronous step into one that waits on a check, inside the one workflow that
   must not half-finish. Worth doing only deliberately.

## Acceptance

- A dry-run promotion (`dry_run: true`) is unaffected either way — it skips the
  push, so it cannot prove this.
- A real promotion completes with the ruleset Active.
- Whichever fix is taken, the reason is written where the next person changing
  the ruleset will read it.
