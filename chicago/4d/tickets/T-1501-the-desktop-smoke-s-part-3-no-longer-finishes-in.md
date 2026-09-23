---
id: T-1501
title: The desktop smoke's part 3 no longer finishes inside the 600 s foreground ceiling: it stalls in the reconstruction-contract block and reports the body-completion sentinel, so no steward run can measure it
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

The desktop smoke's part 3 no longer finishes inside the 600 s foreground ceiling: it stalls in the reconstruction-contract block and reports the body-completion sentinel, so no steward run can measure it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`SMOKE_VIEWPORT=desktop SMOKE_STAGE=3 node tools/smoke_renderer.mjs --published` runs to
completion inside the 600 s a steward run's foreground command may take, on a steward
runner, and its verdict is about the town rather than about the clock. Either part 3 is cut
(the T-0166/T-0170 precedent: halve it and re-measure both halves), or the block below is
made to cost what it used to.

**Measured here, twice, 2026-09-21, on dev at 2d4ea3d05 (T-1369's run).**

    timeout 560 … → exit 124, 592 s wall → exit 124
    last check to print: "the ground was conformed to the field, with nothing left over"
    FAIL desktop 1280x800: the suite body ran to completion
         — Error: page.evaluate: Target page, context or browser has been closed

Both attempts died in the same place: the block immediately after that check, the
evidence-only households / reconstruction contract block (T-1327, `smoke_renderer.mjs`
~L6287). That block does one `page.evaluate` that fetches, **sequentially and in-page**,
every household carrying a reconstructed person. That set is **221 households on today's
dev** and it grows with every stage from T-1171 to T-1178 — by design, the count is read
off the manifest so it cannot go stale. The cost of the block grows with it, and nothing
re-measures the part when it does.

`smoke_budget.mjs` still prices desktop part 3 at **≈ 1m 40s measured, 8m 20s of margin**,
from the last reading that completed: **2026-09-18T01:35**, before T-1171's expansion
landed. So the budget tool actively tells runs this leg is cheap, and it is not.

**Why this is worth its own row.** Part 3 is one of the assertions QUEUE.md § 0 counts as
"standing red on dev", which makes `smoke_budget` report every leg covering it as "already
red on dev" so runs skip it. But dev is not red *there* on any claim about the town — the
only failing check is the **body-completion sentinel**, which fires when the process is
killed. The content assertions in that block have not been evaluated by anybody since
2026-09-18. A part nobody can finish is not a measurement, and it reads identically to a
real regression.

**Two facts that are easy to conflate, and one reader that does.**
`dev-smoke-state.mjs` already knows `killed` and `fail` are different facts (its own
comment at L468: "`killed` and `fail` are DIFFERENT FACTS and only one of them is about
this tree"). It decides between them on whether the log reached the page-error check
(L309-314) — but that check prints during teardown even when the body was killed, so a
killed run that got that far is filed as `fail`. The reading filed by this run says `fail`
for that reason; the failure it names is the sentinel, so the record is honest, but the
one-word verdict is not the one the header's own rule intends. Worth fixing beside the
part, not before it.

**Found by** T-1369's closing run, 2026-09-21, which needed this leg to demonstrate its
own acceptance and could not run it. See that ticket and PR.
