---
id: T-0813
title: Six generated artifacts conflict on every branch: merge them by regenerating, and make a drain lap a tool
state: split
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T19:46:19.386Z
claimed_run: null
---

Every one of the 21 PRs open against `dev` conflicts with it, and **all 21 conflict on
the same six files** — none of which a human should ever merge, because a tool builds
all six:

| file | built by | conflicts on |
|---|---|---|
| `site/chicago/4d/walk/index.html` | `tools/publish.sh` | 21 of 21 |
| `site/chicago/4d/tickets.json` | `ticket.mjs` (T-0154 mirror) | 21 of 21 |
| `site/chicago/4d/build.json` | `tools/publish.sh` | 21 of 21 |
| `chicago/4d/tickets/tickets.json` | `ticket.mjs board` | 21 of 21 |
| `chicago/4d/tickets/BOARD.md` | `ticket.mjs board` | 21 of 21 |
| `chicago/4d/tools/dev-smoke-state.json` | `dev-smoke-state.mjs record` | 15 of 21 |

Below those six the tail is short and mostly real: `identity_master.json` (7),
`register_1835.json` (5), `source_coverage.json` (4), the 665-roof programme (4).

**The two files that already have drivers do not appear at all.** `changelog.js`
conflicts on **0 of 21** and `QUEUE.md` on **3 of 21**, against 21 for every generated
artifact beside them. That is the measurement this ticket rests on: the driver treatment
`.gitattributes` gave those two on 2026-09-04 works, and the six files above never got it.

**So give them the same treatment, in the shape each one's content asks for:**

1. **The four build products** (`BOARD.md`, both `tickets.json`, `build.json`,
   `walk/index.html`) — a `regenerate` merge driver that ignores both sides entirely and
   re-runs the tool that owns the file. There is no such thing as a semantic conflict in
   a file whose whole content is a function of other tracked files. Register it in
   `tools/setup-merge-drivers.sh` beside `queue` and `changelog`.
2. **`dev-smoke-state.json`** is a LEDGER OF READINGS, not a source — #880 said so in as
   many words and `check.sh` does not gate it. Union the entries by (tree hash, viewport,
   stage), newest wins on a tie. It must never block a merge again.

**Then make a drain lap a tool, not a memory.** #880 did the whole procedure by hand and
wrote it down in its commit message; #891 did it again. It is the same six steps every
time, so `tools/drain.mjs <pr> [<pr>...]` should do them: merge `dev` into a batch
branch, regenerate every build product from its own source, restamp ticket-id collisions
with `ticket.mjs restamp` keeping queue places, union true appends with
`tools/resolve_append.py`, run `check.sh`, and **refuse** — leaving ordinary conflict
markers — on any conflict outside that set. Refusing is the point: a research claim
(#876 against #888 in `newberry_index/coverage.json`) is not a merge, and the tool must
say so rather than pick.

**Acceptance:** the six files above carry merge treatment registered by
`setup-merge-drivers.sh`, with a self-test per driver on a specimen that would conflict
without it (the drivers already here set the pattern — `merge-queue-selftest.mjs`,
`merge-changelog-selftest.mjs`). `tools/drain.mjs` performs a lap end to end on at least
two of the open PRs and refuses on a seeded non-build conflict, asserted in its own
self-test. `check.sh` runs both. Measured before and after on the same branches: the
conflicting-file count per PR drops from 6+ to 0 where nothing but build products differ.

Blocks T-0805, T-0806 and T-0807 — every lap after the first is cheap only if this lands.
