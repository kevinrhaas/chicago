---
id: T-0271
title: The balanced ceiling is breached at the forks by 5,290 triangles on an unmodified dev, and both open tickets name a different stand
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded by #765, which raised all three scene-detail ceilings on the owner's ruling — its "never by raising it" was overridden by that ruling; every tier is inside its ceiling on dev
needs_bake: false
closed_at: 2026-09-10T04:20:10.411Z
claimed_run: null
---

The balanced ceiling is breached at the forks by 5,290 triangles on an unmodified dev, and both open tickets name a different stand.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by **T-0209**, which measured its own branch against a clean `origin/dev` worktree
with `tools/measure_detail_ceilings.mjs` in the same hour, on the same runner:

| viewport | tier | ceiling | clean `dev` worst | stand |
|---|---|---:|---:|---|
| desktop | `balanced` | 1,210,000 | **1,215,290 — OVER by 5,290** | the forks, from Wolf Point |
| desktop | `full` | 1,400,000 | 1,378,215 — PASS | the forks, from Wolf Point |
| desktop | `light` | 785,000 | 756,144 — PASS | Lake Street at Canal |
| mobile | all three | — | PASS, 75,190 to 113,179 clear | — |

**Nobody's branch put it there.** It is desktop only, it is `balanced` only, and it is at
**the forks, from Wolf Point** — which matters, because the two tickets already open on a
breached `balanced` ceiling, **T-0203** and **T-0218**, both name *Lake and Canal* and
both sit in the queue's `PROBABLY ALREADY ANSWERED` band. Lake and Canal now reads
1,198,860 and PASSES by 11,140. So the breach moved stand and neither open ticket
describes the one there is.

The last measured `balanced` figure on the record is T-0241's, 2026-08-27: 1,195,188 at
the worst of the same five stands, 14,812 clear, after the 800 m furniture reach paid for
Washington Street. Whatever has landed on `dev` since has spent that 14,812 and 5,290
more.

**Acceptance:** the current desktop `balanced` breach at the forks is attributed to what
landed, and either bought back inside the ceiling by a measured lever (T-0241's own note
leaves 700 m furniture reach on the table, worth ~57,000 at that tier) or recorded as a
tier that no longer fits its ceiling — **never by raising it**, which T-0237's acceptance
refuses in as many words and the re-basing count written into `main.js` beside `DETAIL`
is the argument for.

**Links:** T-0209 (the measurement) · T-0203 · T-0218 · T-0241 (the 800 m lever and the
700 m still on the table) · T-0237 · T-0248.
