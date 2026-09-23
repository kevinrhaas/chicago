---
id: T-0210
title: The desktop smoke's stage 9 times out clicking the panel close, on an unmodified tree
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-28
pr: 470
claimed_by: run 8/28/2026, 10:43:08 AM CT
blocked_on: null
needs_bake: false
---

The desktop smoke's stage 9 times out clicking the panel close, on an unmodified tree.

Found while gating T-0054. `SMOKE_VIEWPORT=desktop SMOKE_STAGE=9 node tools/smoke_renderer.mjs
--published` ends **75 passed, 1 failed** with

    FAIL desktop 1280x800: the suite body ran to completion —
    TimeoutError: page.click: Timeout 90000ms exceeded.
      waiting for locator('#panel-close') … element is visible, enabled and stable
      … scrolling into view if needed

at `smoke_renderer.mjs:9629`, the close after the ground-claims block. Every check before it
passes and `zero page errors` passes after it, so nothing is broken on the page — the click
is issued, the element is actionable, and the action never resolves.

**It is not the branch.** The same stage was run on the stashed, unmodified tree as a control:
identical 75 pass / 1 fail, the same assertion, the same locator, the same 90 s. The two runs'
check lists diff clean. Timings on this runner: 8 m 21 s and 6 m 43 s with the branch, 9 m 49 s
for the control, against the 10 m ceiling on a single foreground command — so the box is close
to its limit and the failing action is the one that waits on a rendered frame.

The mobile half of the same stage passes 88/88, and stage 3 (the building cards, including the
popup's liberties) passes 74/74 at mobile.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The cause is named with a measurement rather than guessed at: either the click genuinely
  cannot complete on a software renderer at this frame cost, or the runner is over its budget
  and the stage needs re-cutting (T-0167's shape) — and whichever it is, it is measured on
  both a fast and a slow run rather than asserted.
- The desktop half of stage 9 runs to completion on the steward runner, without the assertion
  being weakened or the click being replaced by something that cannot fail.
