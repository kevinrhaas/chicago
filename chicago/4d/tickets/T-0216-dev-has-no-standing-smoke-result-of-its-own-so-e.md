---
id: T-0216
title: dev has no standing smoke result of its own, so every branch re-derives dev's reds by hand
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 402
claimed_by: run 8/27/2026, 10:23:32 AM CT
blocked_on: null
needs_bake: false
---

dev has no standing smoke result of its own, so every branch re-derives dev's reds by hand.

**From T-0215, which is what this cost.** `chicago-4d-check.yml` runs `check.sh` and nothing
else, and `chicago-4d-smoke.yml` is dispatch-plus-one-path. So the smoke state of `dev` is
whatever the last agent happened to run in a worktree, and the question every branch asks —
*"is this red mine, or did I inherit it?"* — is answered by cutting a clean `origin/dev`
worktree and paying for the stage again. On 2026-08-27 **three separate agents each paid that
price on the same red**, and the red turned out to be neither branch's nor dev's: it was the
machine (T-0215 has the frame timings). A fourth agent was simultaneously re-deriving the
desktop 3-4 triangle-ceiling red the same way.

**Acceptance:** a run that sees a red stage can find out, WITHOUT running anything, whether
`dev` was already red on that stage and when it last passed. Demonstrated by a steward run
answering it from the record alone.

**The obvious shape, not the only one.** A scheduled dispatch of `chicago-4d-smoke.yml` on
`dev` — it already has `workflow_dispatch` with `viewport` and `stage` inputs and a runner
without the ten-minute per-command ceiling — writing its per-stage result somewhere a run
reads early (`docs/STATUS.md` has no machine-readable slot for it; a committed
`tools/dev-smoke-state.json`, or the workflow's own run history queried by `gh`, both would).
Note the trap this ticket must not fall into: a result taken on a quiet CI runner does not
predict a steward run on a box carrying a dozen agents, so whatever it records has to carry
the conditions it was taken under — T-0215's readings differ by a factor of twenty on the same
tree.

**Why it is not built in T-0215's PR:** it edits `.github/workflows/`, which AGENTS.md
§ How work ships puts outside a steward run's scope — *"changing one needs an interactive,
owner-visible PR."*

**Related, and an operator decision rather than a repo one:** `SMOKE_PORT` defaults to 4187
for every agent, so two concurrent runs on the shared box collide with `EADDRINUSE` (T-0215's
first command did). The deeper version of the same problem is that a dozen simultaneous
SwiftShader browsers ARE the load T-0215 measured — 71-115 Chromium processes, load average
38-52, browsers killed mid-run. Scheduling the heavy gates rather than running them shoulder
to shoulder is worth more than any timeout.
