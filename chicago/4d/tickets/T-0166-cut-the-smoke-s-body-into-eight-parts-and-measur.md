---
id: T-0166
title: Cut the smoke's body into eight parts, and measure the mobile fit
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-0121
opened: 2026-08-23
closed: 2026-08-23
pr: 344
claimed_by: run 8/23/2026, 8:07:49 PM CT
blocked_on: null
needs_bake: false
---

Cut the smoke's body into eight parts, and measure the mobile fit.

Piece 1 of 2 of **T-0121 — The desktop smoke's fourth stage has outgrown the ten-minute command ceiling**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** `SMOKE_STAGE` takes eight parts and contiguous ranges of them; part
2k-1 plus part 2k is exactly T-0060's stage k, so the parts still audit to an
unfiltered pass; every part runs green **at mobile** on its own from a fresh boot, with
its wall clock measured and written where T-0060's fit was (docs/ROADMAP.md § THE RUN
BUDGET); and every invocation prints its own elapsed time, so the next margin to go is
visible without a run re-measuring by hand.

This piece deliberately does NOT claim the desktop fit — that is T-0167, and the reason
they are two tickets is written there.
