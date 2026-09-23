---
id: T-0674
title: A bot-opened PR never runs the dev gate before merge, and two of them broke dev
state: withdrawn
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: #792 landed and chicago-4d-check.yml runs on every pull_request unfiltered
needs_bake: false
closed_at: 2026-09-10T04:20:11.419Z
claimed_run: null
---

A bot-opened PR never runs the dev gate before merge, and two of them broke dev.

**Owner ruling, 2026-09-04: yes — gate bot-opened PRs before merge.** Asked directly during
the open-PR sweep, he chose it over the alternative of leaving the deploy ungated and
relying on auto-revert.

## Where the question came from

PR #743 raised it and then sat on `hold` for fifteen hours. Reviewing all seven held PRs on
2026-09-04, **this was the only genuinely open question in the entire backlog** — every other
hold was waiting on something already decided days earlier. #743 stated it plainly:

> a bot-opened PR never runs the gate before merge — **which is the root cause and is the
> owner's call to change.**

The evidence is specific, not hypothetical: **#740 and #741 merged and left `dev` red**, about
an hour before #743 was parked. Both were bot-opened. The breakage was two research-spend
ceiling breaches that a pre-merge gate would have caught, and it cost every branch open at the
time an unreadable gate — a run cannot tell its own failure from an inherited one.

## THE DISTINCTION THIS TICKET MUST NOT BLUR

This project has a hard-won rule that **deploy is never gated**: a `needs: test` gate once
froze the live site for about 21 hours, and `auto-revert.yml` ("Guard main") is the self-heal
instead. That rule stands and this ticket does not touch it.

**Gating a bot PR before it merges into `dev` is a different thing from gating the deploy.**
The first stops a red branch entering the integration branch; the second stops a published
site from updating. The analytics repo's pipeline doc already draws exactly this line — its
stage gate "is fine because it gates an integration branch, never the deploy." If a future
run reads this ticket as licence to gate deploy, it has misread it.

## What to work out

1. **Which PRs count as bot-opened.** The steward loop's own PRs, the `claude/*` session
   branches, anything opened by the app rather than by a person. Say it as a rule the
   workflow can evaluate, not a list that will drift.
2. **Which gate.** `tools/check.sh` is the obvious one and takes ~5 minutes. The renderer
   smoke is far longer and is advisory today — decide whether it is in or out, and say why.
   Do not put a 78-minute leg in front of every merge without measuring what that does to
   loop throughput.
3. **What happens on red.** The PR stays open and the janitor leaves it — which is already
   the janitor's behaviour — rather than anything that could wedge the loop.
4. **The cost, measured.** State how many merges per day this delays and by how long. The
   owner chose this knowing it costs throughput; the ticket should say how much it actually
   costs once built.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. A bot-opened PR into `dev` cannot merge without a green `check.sh` on its own head, and
   the rule for "bot-opened" is written where a workflow evaluates it.
2. `deploy.yml` is untouched. Assert it — the diff shows no change to any deploy path.
3. The #740/#741 failure is replayed against the new rule and shown to be caught: take those
   two heads, run the gate, and show it goes red. A rule that would not have caught the
   incident that motivated it is not done.
4. Throughput cost stated in numbers, not adjectives.
5. `docs/PIPELINE.md` (or the fleet guide it defers to) records the rule and the
   deploy-vs-integration distinction above, so the next reader does not undo it.
