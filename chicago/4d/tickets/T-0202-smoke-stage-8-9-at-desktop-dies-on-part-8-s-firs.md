---
id: T-0202
title: SMOKE_STAGE=8-9 at desktop dies on PART 8's first click, on dev as well as on a branch
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-08-27
pr: null
claimed_by: null
blocked_on: Fixed and shipped as T-0215 in PR #394: clickChrome() is on dev and part 8 runs its 28 staged checks in 6 m 10 s. The failure was machine load, not the panel — the part died on its first click having run zero staged checks, and was named for its last section.
needs_bake: false
---

`SMOKE_STAGE=8-9 SMOKE_VIEWPORT=desktop node tools/smoke_renderer.mjs --published` cannot
run. It dies on PART 8's first statement, and it dies the same way on an unmodified `dev`.

## Measured 2026-08-24 (found while working T-0026)

Three runs, all `--published`, all on the same host:

| tree | result |
|---|---|
| `steward/t-0026-southern-ground` | **8 passed, 1 failed** — 6 m 12 s, **0 staged-section check(s)** |
| the same branch, second attempt | **8 passed, 1 failed** — 6 m 12 s, 0 staged-section check(s) |
| **a clean `origin/dev` worktree, no changes at all** | **8 passed, 1 failed** — 6 m 00 s, 0 staged-section check(s) |

The failure is byte-for-byte the same in all three:

    FAIL  desktop 1280x800: the suite body ran to completion — TimeoutError: page.click: Timeout 90000ms exceeded.
      - waiting for locator('.panel-tab[data-tab="settings"]')
        - locator resolved to <button role="tab" class="panel-tab" data-tab="settings">Settings</button>
      - attempting click action
        - waiting for element to be visible, enabled and stable

**`zero page errors` passes in every run**, and `0 staged-section check(s)` means the run
never reached a single staged assertion: it died on the first line of PART 8's body, so
stages 8 and 9 contribute nothing at desktop today.

## The code already knows about this failure mode

`tools/smoke_renderer.mjs` ~8446, the comment immediately above the guard:

> …and the PANEL, which part 7 leaves open at its last line and this part reaches straight
> into: its first statement clicks a tab inside it, **and a click on a tab that has no
> layout waits ninety seconds and dies.** Guarded on the panel's own hidden state rather
> than toggling…

The guard clicks `#btn-help` when `#panel` carries `hidden` and then goes straight to
`page.click('.panel-tab[data-tab="settings"]')`. Playwright's click waits for the element to
be *visible, enabled and stable* — a bounding box unchanged across two frames — and the
locator resolves, so the element exists and something about its layout never settles. The
guard proves the hazard was known; what it does not do is wait for the panel to finish
opening.

**Mobile is not affected the same way**: `SMOKE_STAGE=8-9` at mobile reaches 22 staged
checks before its own (different) timeout, and `SMOKE_STAGE=8` alone at mobile runs through
the same click without complaint.

## What this costs

The desktop half of parts 8 and 9 — eye height, the settings, the Go-to tab, What's-new,
the Evidence panel, the liberties, the exclusions, the ground card and inspecting from the
air — is **not being run by any steward on a split**. `docs/ROADMAP.md` § THE RUN BUDGET
sizes the desktop parts from a measured profile (T-0167, T-0170, T-0173, T-0181) on the
assumption they run; parts 8 and 9 at desktop have not been executing at all.

**Not settled here:** whether the root cause is the guard or the host. All three runs above
were taken on a machine at load average 50–65 (ten parallel agents), and a slow first frame
would produce the same symptom. The comparison IS clean — the control had no changes and
failed identically — so this is not a branch's fault; whether it reproduces on an idle host
is the first thing the fix should establish.

## Acceptance

- The desktop `SMOKE_STAGE=8-9` run reaches its staged checks — a non-zero
  `staged-section check(s)` count — rather than dying on the first click.
- Whatever the cause turns out to be, it is written next to the guard, replacing the comment
  that predicted this failure and did not prevent it.
- **The 90 s timeout is not raised to make the red go away**, and no assertion is weakened:
  if the host is genuinely the cause, that is recorded as a finding about the runner and the
  guard is made to wait on the panel's layout rather than on its `hidden` attribute.
- Check whether PARTS 1–7 carry the same shape of cross-part assumption at desktop, since
  this one was introduced by the T-0060 → T-0121 → T-0167 re-cuts and nothing tested a split
  at desktop end to end.
