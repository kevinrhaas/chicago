---
id: T-0037
title: The liberties gate reads the whole Evidence panel, so a liberty saying 'Three of these' fails it
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-17
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: the smoke scans uncertainBlockText (smoke_renderer.mjs L12313), which is the open-questions node
needs_bake: false
closed_at: 2026-09-10T04:20:11.924Z
claimed_run: null
---

`tools/smoke_renderer.mjs` § `the panel states that once too — and counts nothing by
hand` guards against a hand-typed count of the open questions creeping back into the
Evidence panel. It does that with `!/Three of these/i.test(open.heading)`, and
`open.heading` is the textContent of the WHOLE panel — which includes every rendered
liberty. K53 (#221) shipped a liberty whose reasoning opens *"Why invent it rather than
leave the wand. Three of these records describe multi-stemmed plants in their own
committed text"*, so the guard now fires on a sentence about shrubs.

**Measured 2026-08-17**, `origin/dev` at `3114e061`, mobile 390×780 on the published
mirror: the assertion FAILS, `occurrences: 1` (the half it actually checks is correct)
and `hasHandCount: true` (the liberty). The desktop half has never fitted this runner's
per-command ceiling, which is why a gate red since #221 was only seen today.

The guard is not wrong to exist — it is aimed at the wrong element. The paraphrase it
bans lived in the open-questions heading, and `#uncertain-note` / the heading node is
what it should scan; the same fault is one line up in the `the panel states it once —
the hand-written paraphrase is gone` sibling, which divides over the whole panel too and
survives only because nothing has yet written its recorded note twice.

**Acceptance:** the assertion scans the element that carries the claim rather than the
whole panel; a liberty may contain any phrase without failing a gate about the open
questions; and the guard still fires when a hand-typed count IS put back in the heading
(prove it, the way this suite proves its other assertions fire when broken).

Found by T-0001's run (PR #231), which measured the same failure on `origin/dev` before merging.
