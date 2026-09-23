---
id: T-0215
title: Desktop smoke stage 8 (What's-new) is red on dev and every branch inherits it
state: done
epic: RENDERING
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: 394
claimed_by: run 8/27/2026, 12:44:46 AM CT
blocked_on: null
needs_bake: false
---

Desktop smoke stage 8 (What's-new) is red on dev and every branch inherits it.

Two branches independently reported `SMOKE_VIEWPORT=desktop SMOKE_STAGE=8` dying on a
single `page.click` timeout, and one of them re-ran it in a clean `origin/dev` worktree at
`29eebdef` to prove it was not its own change. That means the What's-new panel has been
unverified on every branch cut from dev for an unknown span, and nobody owns it because it
reads as each branch's own problem.

**The confound, stated up front.** Both reports were taken on a box carrying a dozen
parallel agents — load average 38-50, ~71 concurrent Chromium processes. A `page.click`
timeout is exactly what an overloaded software renderer produces, and a third agent had a
browser killed outright mid-stage on unmodified dev. So "stage 8 is broken" and "stage 8
cannot survive this machine" both predict the observation, and telling them apart is the
work.

**Acceptance:**

1. Every smoke reading in this ticket is recorded with the load average and the Chromium
   process count taken beside it. A reading at load 40 is not comparable to one at load 4
   and is not reported as though it were.
2. The What's-new panel is driven **by hand** — the page opened, the tab clicked from
   inside the page, the rendered feed read out — separately from the Playwright path, so
   "the panel works and the click cannot land" is distinguishable from "the panel is
   broken".
3. The verdict names one of: (a) a commit that broke the panel, with the panel fixed and
   the visitor-visible symptom described; (b) a stale assertion, with what it now waits on
   and evidence the panel genuinely works; (c) machine load, said plainly, with the
   reading that shows it.
4. Whatever the verdict, `SMOKE_VIEWPORT=desktop SMOKE_STAGE=8` reaches its summary line
   with zero failures on this branch, at a stated load, without any assertion being
   loosened, retried-until-green, or deleted.

---

## THE VERDICT: (c) MACHINE LOAD. Nothing broke, and no commit is guilty.

**Reproduced first, exactly.** On this branch off `origin/dev@29eebdef`, at load average
**38.7 rising to 51.7** with **71-115** concurrent Chromium processes:

```
8 passed, 1 failed · 0 staged-section check(s) (stage 8 of 9) · 4 m 23 s
FAIL desktop 1280x800: the suite body ran to completion
     — TimeoutError: page.click: Timeout 90000ms exceeded.
       waiting for locator('.panel-tab[data-tab="settings"]')
       locator resolved to <button role="tab" class="panel-tab" data-tab="settings">
       element is visible, enabled and stable
       scrolling into view if needed
```

**Read the count: ZERO staged checks.** The eight passes are the five boot checks, the page-error
check and the two vendor checks that every invocation takes. **Stage 8 was not failing at
What's-new — it was dying on the Settings tab, its very first action, before a single one of its
28 assertions had run.** The ticket title (and both branch reports) named the wrong subject
because the part is *called* What's-new; nothing in it had been reached, including everything in
it that has nothing to do with What's-new.

### 1. The panel is not broken. It was driven by hand while the gate was dying.

Same tree, same machine, load ~45. The page opened, the world entered, the panel opened and the
tab clicked **from inside the page**, then read back:

| reading | value |
|---|---|
| gate dismissed / panel open | `true` / `true` |
| `elementFromPoint` at the tab's own centre | `BUTTON.panel-tab` — **the tab itself** |
| pointer lock | none |
| entries painted | **272** |
| items painted | **1,569** |
| newest title | "Two evidence cards were showing their own merge scars" |
| its meta line | `Fixed · Aug 26, 2026, 11:18 PM CT` |
| unread chip after opening | cleared |
| `chicago4d.whatsnew.seen` | `272` |

Every assertion stage 8's What's-new section makes would have passed: ≥5 entries, items ≥ entries,
a title longer than four characters, a meta ending in `CT`, the dot cleared and `seen > 0`.

### 2. What actually moved is the cost of one animation frame.

Ten consecutive frames, measured on the loaded runner:

**17,036 · 29 · 333 · 21,451 · 20,211 · 119 · 4,420 · 22,280 · 12,242 · 26,580 ms**

against the **0.46-1.10 s** this project measured on 2026-08-13 and wrote its 90-second action
budget around. **The 29 ms and 119 ms frames in that same sample are the proof it is the machine
and not the scene**: the renderer draws this town fast when it is given the CPU, and for tens of
seconds at a stretch it was not being given it. Playwright's click will not hit-test a target
until it has held still across consecutive animation frames, so at 17-27 s a frame the 90 s budget
buys three or four of them.

### 3. It is FLAKY, not broken — the same click lands, and lands, and lands, and then does not.

`page.click('.panel-tab[data-tab="settings"]')`, the exact call that killed the gate, timed at the
same load:

| when | result |
|---|---|
| cold, fresh boot, the smoke's PART 8 prologue verbatim | **ok, 10.9 s** |
| on a settled page | **ok, 28.4 s** |
| `.panel-tab[data-tab="whatsnew"]`, settled | ok, 20.6 s |
| `#gate-btn` after a reload | ok, 53.8 s |
| in the gate | **timed out past 90 s** |

**This also refutes the obvious mechanism.** The tidy story — "a filtered run clicks seconds after
the world is revealed, during the most expensive frames of the run, where an unfiltered run has
seven parts of walking in between" — predicts the cold click is the slow one. It was the fastest
of the five. There is no deterministic trigger; there is a distribution whose tail crosses 90 s.

### 4. And the box kills browsers.

Two runs ended `Target page, context or browser has been closed` mid-measurement, `pgrep -c chrome`
went **115 → 0** in one interval, and a `page.goto` to `domcontentloaded` against a **local static
file server** timed out at 30 s once. Boot to `__chicago4d.ready` measured **29 s, 106.8 s and
127.4 s** on the same tree within twenty minutes — against the 30 s the smoke gives it.

### 5. No commit broke it, and here is the proof rather than the assertion.

T-0167 measured desktop part 8 **green at 6 m 10 s, twice**, on 2026-08-24 (ROADMAP § THE RUN
BUDGET). Since then **nothing the panel is made of has changed**: `renderers/web/index.html`,
`js/hud.js`, `js/whatsnew.js` and `css/walk.css` were all last touched at `d7e09dcb` (T-0076),
well before that measurement. What has changed under `renderers/web/` since 2026-08-23 is
`flora.js`, `frontage.js`, `trees.js`, `streets.js`, `main.js` and `changelog.js` — every one of
them a contribution to the cost of a frame, not one of them a panel.

## What was fixed, and why it is not a workaround

The project predicted this precisely. STATUS, 2026-08-13, on the last time this happened:

> **This is a standing hazard, not a fixed one**: the same starvation will return as the town
> grows, and the next symptom will again look like a UI bug rather than a budget.

It did, and it took three agents' runs with it. The budget is **not** raised a second time — a number
measured in frames is the wrong instrument for a scene whose frame cost is set by what else the
machine is doing, and 180 s would buy one town-sized month and spend it against a ten-minute
per-command ceiling this gate has already been re-cut for twice.

**`clickChrome()`** (in `tools/smoke_renderer.mjs`, beside `enterTown`) is the answer instead: for
the fourteen panel-chrome clicks in PART 8, it asserts in ONE page round trip everything
`page.click` asserts across many frame-bound ones — the element exists, is enabled, has a real
box, and is **the topmost thing at its own centre** — and then clicks it. Nothing is skipped and
nothing is softened:

- The `elementFromPoint` test is T-0108's assertion verbatim. A control the HUD's
  `pointer-events: none` swallows returns the **canvas** and fails here exactly as it fails a
  visitor's mouse.
- A control that is renamed, moved, zero-size or covered still fails — in one round trip, naming
  what covered it, instead of in ninety seconds with a call log that reads like a broken control.
- The four clicks where the trusted event is the **subject** rather than the means — part 4's
  confidence menu, T-0108 — stay `page.click`, and now say so where they stand.

The smoke also now **prints what a frame costs whenever an action times out**, so the next agent
to see this gets the answer in the same log instead of spending a run on it. It is a report, never
a bar: the failure still fails.

### The one thing the helper got wrong, kept on the record because it is the lesson

Its first run went from **0 staged checks to 19 of 28** and then failed two — *"G opens the Go to
tab"* reading `{"open":false,"tab":"goto"}`, and the result row after it reading
`clickChrome: [data-jump-id="randolph_canal"] has no box (0x0)`. Both were one fault:
**a real mouse press focuses a focusable control and an untrusted `.click()` does not.** Part 8
closes the panel and then presses `g`, and `g` only reaches the window shortcut once focus has
left the Go-to search box — `isTyping(e.target)` swallows it otherwise, which is exactly what that
guard is for and exactly the bug that section was written to catch. So the panel stayed shut and
the row underneath it had no box. `clickChrome` now focuses before it clicks, which is fidelity to
the click being replaced rather than a convenience.

Worth keeping for two reasons. It is the **precise** hazard in swapping a trusted event for an
untrusted one, so anyone extending `clickChrome` past part 8 knows what to look for. And the
helper's failure message named the fault in one line — `has no box (0x0)` — where the old path
would have spent ninety seconds and printed a call log about a stable, visible, enabled button.

## The controlled A/B, which settles it

The box drained around 06:00 CT (every agent's browser was killed at once), and that gave the
reading the whole ticket wanted: **`origin/dev`'s own unmodified `smoke_renderer.mjs`, run against
this same tree at a quiet load.**

| run | harness | load avg / Chromium | outcome | wall |
|---|---|---|---|---|
| desktop 8 | dev's, unmodified | 38.7 → 51.7 / 71-115 | **1 failed · 0 staged checks** | 4 m 23 s |
| desktop 8 | dev's, unmodified | **10.4 → 13.7 / 20-24** | **37 passed, 0 failed · 28 staged · SMOKE PASS** | **14 m 33 s** |
| desktop 8 | `clickChrome`, first cut | 15.8 → 15.7 / 21-30 | 26 passed, 2 failed · 19 staged | 3 m 14 s |
| desktop 8 | `clickChrome` + focus | 15.8 → 21.2 / 21-35 | **37 passed, 0 failed · 28 staged · SMOKE PASS** | **6 m 10 s** |
| mobile 8 | `clickChrome` + focus | 14.4 → 12.0 / 20-27 | **37 passed, 0 failed · 28 staged · SMOKE PASS** | 2 m 52 s |
| desktop 8 | after, **on the final merged tree** | 12.4 → 13.5 / 30 | **37 passed, 0 failed · 28 staged · SMOKE PASS** | 4 m 49 s |

**Row two is the verdict.** Same tree, same commit, same harness that had failed three agents —
green, every one of the 28 assertions reached and passed, on nothing but a quieter machine.
**Stage 8 was never broken.** It is (c), machine load, without qualification.

**And row two is also the argument for changing anything at all.** It passed in **14 m 33 s**,
four and a half minutes PAST the ten-minute per-command ceiling that a steward run's single
foreground command is killed at — so on this box the old part 8 does not fit even when it does
not flake. `clickChrome` does the same 28 checks at a comparable load in **6 m 10 s**, which is
T-0167's 2026-08-24 figure to the second. **It buys back 8 m 23 s of margin on the ceiling this
gate has already been re-cut for twice, and it does it by not paying for frames rather than by
checking less.**

Is it desktop-only? Yes, and the mechanism is the obvious one: at 390×780 a frame covers a quarter
the pixels, and the same part costs 2 m 52 s there against 6 m 10 s at 1280×800. Mobile was never
reported red by anyone, and every reading here is consistent with it having the headroom desktop
does not.

The green rows were taken as the box drained, so **none of them proves the fix survives load 50 —
nothing measurable here could.** They prove the 28 assertions exist, pass and are reached, and
that the part now fits its ceiling with margin. The claim about load rests on row two and on the
frame timings.

## The sibling ticket, already filed by someone else

**T-0210 — "The desktop smoke's stage 9 times out clicking the panel close, on an unmodified
tree"** arrived on dev while this was being measured. That is the same fault one part along:
`page.click('#panel-close')`, part 9, unmodified tree. `clickChrome` is the ready-made answer for
it and part 9's chrome clicks are the obvious next adoption — deliberately NOT done here, because
part 9 is that ticket's and because a helper that has been through exactly one part's worth of
surprises (see the focus fidelity above) should be extended by someone who reads that paragraph
first.

## The process fault, which is the part worth arguing about

A red stage that every branch inherits and nobody owns is not a code fault. Three separate agents
paid for this diagnosis on the same day. Two things would have stopped it, and neither is built
here:

1. **The staged gate has no owner and no baseline.** `chicago-4d-check.yml` runs `check.sh` and
   nothing else; the full smoke is dispatch-only. So dev's own smoke state is whatever the last
   agent happened to run, and "is this mine or dev's?" costs a fresh worktree and a re-run every
   time. A nightly dispatch of `chicago-4d-smoke.yml` on `dev`, posting its result somewhere the
   next run reads, would make that a lookup. **Filed as its own ticket** — it changes a workflow
   file, which AGENTS.md § How work ships puts outside a steward run's scope.
2. **Parallel agents share one runner and one port.** `SMOKE_PORT` defaults to 4187 for everyone,
   so two concurrent runs collide with `EADDRINUSE` (this run hit it on its first command) — and
   more to the point, a dozen simultaneous SwiftShader browsers ARE the load measured above. The
   readings above are the argument for scheduling the heavy gates rather than running them
   shoulder to shoulder; that is an operator decision, not a repo change, so it is written here
   rather than built.

