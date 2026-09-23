---
id: T-0235
title: The unfiltered renderer smoke takes 55 minutes on the steward runner, and three tickets reason against a 30-minute cap
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: 588
claimed_by: run 8/29/2026, 11:10:00 PM CT
blocked_on: null
needs_bake: false
---

The unfiltered renderer smoke takes 55 minutes on the steward runner, and three tickets reason against a 30-minute cap.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

## Measured

2026-08-27, steward run for T-0186, on an unmodified tree plus a changelog entry:

    node tools/smoke_renderer.mjs      851 passed, 0 failed
    55 m 10 s unfiltered

The runner has no GPU — chromium launches with `--enable-unsafe-swiftshader` and
rasterises on the CPU, which is where the time goes.

## Why it matters

T-0170, T-0173 and T-0181 all reason about the desktop legs' margin against a
**30-minute** cap. On this runner the whole gate is nearly twice that, so those
three margin figures do not describe the machine the gate actually runs on.

It also does not fit a steward run's foreground: the ceiling on a single
foreground command is 10 m 00 s, and the smoke's own summary line now says so.
This run had to block on the process across six windows to stay synchronous, and
an earlier attempt was killed at 41 minutes — one minute from the finish, as the
flushed fragment showed afterwards — because the run had no way to see progress:
node block-buffers stdout to a pipe, so the log stayed at **zero bytes for the
whole 41 minutes**. Redirecting to a real file instead made it observable.

## Worth considering

- Whether the per-part timings in T-0170/T-0173/T-0181 should be re-measured on a
  software rasteriser rather than on whatever produced the 30-minute figure.
- `SMOKE_STAGE` already splits the run; a documented steward recipe (which stages
  cover which change) would let a run verify what it touched inside its budget.
- The zero-byte-log problem is worth a line in the runbook on its own: a gate you
  cannot watch is a gate that gets killed.

## What shipped (PR pending)

`tools/smoke_budget.mjs` and `docs/SMOKE-BUDGET.md`. The gate's cost is **read**
out of `tools/dev-smoke-state.json` — steward-runner readings against the
published mirror, median per part, nothing asserted — and printed with the parts
that have no reading at all NAMED rather than filled in. Today: desktop 18 m 02 s
over the five parts that have one, mobile 28 m 33 s over all four legs, **46 m 35 s**
for both viewports, against the 30 minutes T-0170, T-0173 and T-0181 reason
against and the 55 m 10 s unfiltered figure this ticket opened with. Those three
tickets now carry the correction.

Readings filed before the T-0346 cut are RENUMBERED rather than discarded (old 5
is new 7; old 4 is new 4+5+6 and is reported as the group), so the record built
before 2026-08-30 still counts.

`--for <path>…` and `--for-diff` answer the question the ticket asked for: which
parts cover the change in hand, and the exact commands, packed under the 600 s
foreground ceiling with the measured margin beside each. The map can only ever
ADD parts — an unmapped path means the whole gate, a `NO PART` row says so
explicitly and still earns one cheap staged pass per viewport for the always-on
scaffolding — and `--self-test` runs in `check.sh`, so a renamed module fails the
gate instead of silently dropping a part from the recipe. One limitation is
stated rather than worked around: `publish.sh` restamps `walk/index.html`, so a
published change is always told "the whole gate"; read the diff.

The zero-byte-log problem has its own section in `docs/SMOKE-BUDGET.md` and a
line in `AGENTS.md`: node block-buffers stdout to a pipe, so redirect a smoke to
a real file or a green run gets killed one minute from its finish, as one did.

**Left open, as its own ticket.** T-0433: T-0346 measured the new desktop parts
4, 5 and 6 and filed none of the three, which is why six desktop parts still have
no reading — and the two places those figures are written down disagree by 1 m 18 s
on part 6.

**Verification.** `./tools/check.sh` PASS, including the new self-test step. Smoke
against `--published`, five legs, both viewports, zero page errors, every one
filed into the record: mobile 10 `1 m 38 s` 37/0, desktop 10 `2 m 55 s` 37/0,
mobile 1-2 `4 m 47 s` 151/0, desktop 11 `4 m 43 s` 104/0, desktop 1 `4 m 36 s` 77/0.
